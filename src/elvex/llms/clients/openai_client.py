from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from elvex.llms.types import AgentConfig, ChatResponse, Message
from elvex.observability import get_observer


class OpenAISettings(BaseSettings):

    api_key: str = Field(alias="OPENAI_API_KEY")
    model: Optional[str] = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    class Config:
        env_file = ".env"
        extra = "ignore"
        populate_by_name = True


class OpenAIClient:
    
    def __init__(self):
        self.settings = OpenAISettings()
        self.client = OpenAI(api_key=self.settings.api_key)
        self.default_model = self.settings.model

    def chat(
        self,
        messages: List[Message] | List[Dict[str, Any]],
        *,
        config: Optional[AgentConfig] = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_output_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Given messages as input, returns the LLM output."""

        input_messages = [_normalize_message(m) for m in messages]
        observer = get_observer()

        cfg = config or AgentConfig()

        system_prompt = system_prompt if system_prompt is not None else cfg.system_prompt
        model = model if model is not None else cfg.model
        temperature = temperature if temperature is not None else cfg.temperature
        tools = tools if tools is not None else cfg.tools
        max_tokens = max_output_tokens if max_output_tokens is not None else cfg.max_output_tokens
        tool_executor: Optional[Callable[[str, Dict[str, Any]], str]] = kwargs.get("tool_executor")
        lf_parent = kwargs.get("lf_parent")
        observation_name = kwargs.get("observation_name", "openai.chat")
        observation_metadata = kwargs.get("observation_metadata") or {}

        if system_prompt:
            input_messages = [
                {"role": "system", "content": system_prompt},
                *input_messages,
            ]
        selected_model = model or self.default_model or "unknown_model"
        generation = observer.start_generation(
            parent=lf_parent,
            name=observation_name,
            model=selected_model,
            input_payload=input_messages,
            metadata={
                "provider": "openai",
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "tool_count": len(tools or []),
                **observation_metadata,
            },
        )
        started_at = time.perf_counter()

        try:
            resp = self.client.responses.create(
                model=selected_model,
                input=input_messages,
                temperature=temperature,
                tools=tools,
                max_output_tokens=max_tokens,
            )

            # Handle function tools in-loop for providers/models that emit function_call output items.
            if tools and tool_executor:
                max_tool_rounds = 8
                rounds = 0
                while rounds < max_tool_rounds:
                    rounds += 1
                    function_calls = _extract_function_calls(resp)
                    if not function_calls:
                        break

                    tool_outputs: List[Dict[str, Any]] = []
                    for function_call in function_calls:
                        call_id = function_call.get("call_id")
                        name = function_call.get("name")
                        raw_arguments = function_call.get("arguments", "{}")
                        try:
                            parsed_arguments = (
                                json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
                            )
                        except json.JSONDecodeError:
                            parsed_arguments = {}

                        tool_span = observer.start_span(
                            parent=generation or lf_parent,
                            name=f"tool.{name}",
                            input_payload=parsed_arguments,
                            metadata={
                                "tool_name": name,
                                "tool_call_id": call_id,
                                "provider": "openai",
                            },
                        )

                        tool_started = time.perf_counter()
                        tool_result = tool_executor(name, parsed_arguments)
                        tool_elapsed_ms = round((time.perf_counter() - tool_started) * 1000, 2)

                        observer.end(
                            tool_span,
                            output=str(tool_result),
                            metadata={"latency_ms": tool_elapsed_ms},
                        )
                        tool_outputs.append(
                            {
                                "type": "function_call_output",
                                "call_id": call_id,
                                "output": str(tool_result),
                            }
                        )

                    resp = self.client.responses.create(
                        model=selected_model,
                        previous_response_id=getattr(resp, "id", None),
                        input=tool_outputs,
                        temperature=temperature,
                        tools=tools,
                        max_output_tokens=max_tokens,
                    )

            usage = getattr(resp, "usage", None)
            usage_data = usage.model_dump() if hasattr(usage, "model_dump") else usage
            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            observer.end(
                generation,
                output=resp.output_text,
                usage=_extract_usage_dict(usage_data),
                metadata={
                    "latency_ms": elapsed_ms,
                    "raw_usage": usage_data,
                },
            )
            return ChatResponse(
                text=resp.output_text,
                usage=usage_data,
            )
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            observer.end(
                generation,
                output={"error": str(exc)},
                level="ERROR",
                status_message=str(exc),
                metadata={"latency_ms": elapsed_ms},
            )
            raise


def _normalize_message(msg: Any) -> Dict[str, Any]:
    if isinstance(msg, Message):
        return msg.model_dump()
    if isinstance(msg, BaseModel):
        data = msg.model_dump()
        return {"role": data["role"], "content": data["content"]}
    if isinstance(msg, dict):
        return {"role": msg["role"], "content": msg["content"]}
    raise TypeError(f"Unsupported message type: {type(msg)}")


def _extract_function_calls(response: Any) -> List[Dict[str, Any]]:
    output_items = getattr(response, "output", []) or []
    function_calls: List[Dict[str, Any]] = []

    for item in output_items:
        item_type = item.get("type") if isinstance(item, dict) else getattr(item, "type", None)
        if item_type != "function_call":
            continue

        function_calls.append(
            {
                "call_id": item.get("call_id") if isinstance(item, dict) else getattr(item, "call_id", None),
                "name": item.get("name") if isinstance(item, dict) else getattr(item, "name", None),
                "arguments": (
                    item.get("arguments") if isinstance(item, dict) else getattr(item, "arguments", "{}")
                ),
            }
        )

    return function_calls


def _extract_usage_dict(usage: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(usage, dict):
        return None

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")

    usage_dict: Dict[str, Any] = {}
    if input_tokens is not None:
        usage_dict["input"] = input_tokens
    if output_tokens is not None:
        usage_dict["output"] = output_tokens
    if total_tokens is not None:
        usage_dict["total"] = total_tokens
    return usage_dict or None
