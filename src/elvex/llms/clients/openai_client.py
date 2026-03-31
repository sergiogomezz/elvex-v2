from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from elvex.llms.types import AgentConfig, ChatResponse, Message


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

        cfg = config or AgentConfig()

        system_prompt = system_prompt if system_prompt is not None else cfg.system_prompt
        model = model if model is not None else cfg.model
        temperature = temperature if temperature is not None else cfg.temperature
        tools = tools if tools is not None else cfg.tools
        max_tokens = max_output_tokens if max_output_tokens is not None else cfg.max_output_tokens
        tool_executor: Optional[Callable[[str, Dict[str, Any]], str]] = kwargs.get("tool_executor")

        if system_prompt:
            input_messages = [
                {"role": "system", "content": system_prompt},
                *input_messages,
            ]
    
        resp = self.client.responses.create(
            model=model or self.default_model,
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

                    tool_result = tool_executor(name, parsed_arguments)
                    tool_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": str(tool_result),
                        }
                    )

                resp = self.client.responses.create(
                    model=model or self.default_model,
                    previous_response_id=getattr(resp, "id", None),
                    input=tool_outputs,
                    temperature=temperature,
                    tools=tools,
                    max_output_tokens=max_tokens,
                )

        usage = getattr(resp, "usage", None)
        usage_data = usage.model_dump() if hasattr(usage, "model_dump") else usage
        return ChatResponse(
            text=resp.output_text,
            usage=usage_data,
        )


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
