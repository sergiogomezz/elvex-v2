from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import shutil
from ollama import chat
from pydantic import Field
from pydantic_settings import BaseSettings

from elvex.llms.types import AgentConfig, ChatResponse, Message
from elvex.observability import get_observer

class OllamaSettings(BaseSettings):
    model: str = Field(default="llama3", alias="OLLAMA_MODEL")

    class Config:
        env_file = ".env"
        extra = "ignore"
        populate_by_name = True


class OllamaClient:
    """Local Ollama-backed LLM client."""

    def __init__(self):
        if not shutil.which("ollama"):
            raise RuntimeError("Ollama is not installed or is not in PATH")
        self.settings = OllamaSettings()

    def chat(
        self,
        messages: List[Message] | List[Dict[str, Any]] | List[Any],
        *,
        config: Optional[AgentConfig] = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,  # unused, kept for API parity
        max_output_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        observer = get_observer()
        cfg = config or AgentConfig()

        prompt = system_prompt if system_prompt is not None else cfg.system_prompt
        selected_model = model if model is not None else cfg.model or self.settings.model
        temperature = temperature if temperature is not None else cfg.temperature
        max_tokens = max_output_tokens if max_output_tokens is not None else cfg.max_output_tokens
        lf_parent = kwargs.get("lf_parent")
        observation_name = kwargs.get("observation_name", "ollama.chat")
        observation_metadata = kwargs.get("observation_metadata") or {}

        request_messages = [_normalize_message(m) for m in messages]
        if prompt:
            request_messages = [{"role": "system", "content": prompt}, *request_messages]

        options: Dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        generation = observer.start_generation(
            parent=lf_parent,
            name=observation_name,
            model=selected_model,
            input_payload=request_messages,
            metadata={
                "provider": "ollama",
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                **observation_metadata,
            },
        )
        started_at = time.perf_counter()

        try:
            response = chat(model=selected_model, messages=request_messages, options=options or None)
            content = (
                response["message"]["content"]
                if isinstance(response, dict)
                else response.message.content
            )

            usage = _extract_usage_dict(response)
            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            observer.end(
                generation,
                output=content,
                usage=usage,
                metadata={"latency_ms": elapsed_ms},
            )

            return ChatResponse(text=content, usage=getattr(response, "eval_count", None), raw=response)
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
    if isinstance(msg, dict):
        return {"role": msg["role"], "content": msg["content"]}
    if hasattr(msg, "role") and hasattr(msg, "content"):
        return {"role": getattr(msg, "role"), "content": getattr(msg, "content")}
    raise TypeError(f"Unsupported message type: {type(msg)}")


def _extract_usage_dict(response: Any) -> Optional[Dict[str, Any]]:
    if isinstance(response, dict):
        prompt_tokens = response.get("prompt_eval_count")
        output_tokens = response.get("eval_count")
        if prompt_tokens is None and output_tokens is None:
            return None
        usage: Dict[str, Any] = {}
        if prompt_tokens is not None:
            usage["input"] = prompt_tokens
        if output_tokens is not None:
            usage["output"] = output_tokens
        usage["total"] = (prompt_tokens or 0) + (output_tokens or 0)
        return usage

    prompt_tokens = getattr(response, "prompt_eval_count", None)
    output_tokens = getattr(response, "eval_count", None)
    if prompt_tokens is None and output_tokens is None:
        return None

    usage = {}
    if prompt_tokens is not None:
        usage["input"] = prompt_tokens
    if output_tokens is not None:
        usage["output"] = output_tokens
    usage["total"] = (prompt_tokens or 0) + (output_tokens or 0)
    return usage
