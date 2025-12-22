from __future__ import annotations

from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from pydantic import Field
from pydantic_settings import BaseSettings

from elvex.llms.types import AgentConfig, ChatResponse, Message


class ClaudeSettings(BaseSettings):
    api_key: str = Field(alias="ANTHROPIC_API_KEY")
    model: str = Field(default="claude-3-haiku-20240307", alias="CLAUDE_MODEL")

    class Config:
        env_file = ".env"
        extra = "ignore"
        populate_by_name = True


class ClaudeClient:
    """Claude client with a chat interface compatible with the registry protocol."""

    def __init__(self):
        self.settings = ClaudeSettings()
        self.client = Anthropic(api_key=self.settings.api_key)
        self.default_model = self.settings.model

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
        cfg = config or AgentConfig()

        system_prompt = system_prompt if system_prompt is not None else cfg.system_prompt
        model = model if model is not None else cfg.model or self.default_model
        temperature = temperature if temperature is not None else cfg.temperature
        max_tokens = max_output_tokens if max_output_tokens is not None else cfg.max_output_tokens

        # Claude API takes system separately and messages without system role.
        system_parts: List[str] = [system_prompt] if system_prompt else []
        converted_messages = []
        for msg in messages:
            role = getattr(msg, "role", None) if not isinstance(msg, dict) else msg.get("role")
            content = getattr(msg, "content", None) if not isinstance(msg, dict) else msg.get("content")
            if role == "system":
                if content:
                    system_parts.append(content)
                continue
            if role is None or content is None:
                continue
            converted_messages.append(
                {"role": role, "content": [{"type": "text", "text": str(content)}]}
            )

        system = "\n\n".join([part for part in system_parts if part]) or None

        response = self.client.messages.create(
            model=model,
            system=system,
            messages=converted_messages,
            temperature=temperature,
            max_tokens=max_tokens or 1024,
        )

        text = "".join([block.text for block in response.content if hasattr(block, "text")])
        return ChatResponse(
            text=text,
            usage=getattr(response, "usage", None),
        )
