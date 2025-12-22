from __future__ import annotations

from typing import Any, Dict, List, Optional

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
    ) -> ChatResponse:
        """Given messages as input, returns the LLM output."""

        input_messages = [_normalize_message(m) for m in messages]

        cfg = config or AgentConfig()

        system_prompt = system_prompt if system_prompt is not None else cfg.system_prompt
        model = model if model is not None else cfg.model
        temperature = temperature if temperature is not None else cfg.temperature
        tools = tools if tools is not None else cfg.tools
        max_tokens = max_output_tokens if max_output_tokens is not None else cfg.max_output_tokens

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

        return ChatResponse(
            text=resp.output_text,
            usage=getattr(resp, "usage", None),
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
