from __future__ import annotations

from typing import Any, Callable, Dict, List, Literal, Optional, Protocol

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from elvex.llms.types import AgentConfig, ChatResponse, Message

Provider = Literal["openai", "ollama", "claude"]


class RegistrySettings(BaseSettings):
    """Defaults for the registry (read from .env)."""

    provider_used: Provider = Field(default="openai", alias="PROVIDER_USED")

    class Config:
        env_file = ".env"
        extra = "ignore"
        populate_by_name = True

 
class LLMConfig(BaseModel):
    """Optional overrides when asking the registry for a client."""

    provider: Optional[Provider] = None


class LLMClient(Protocol):
    """Common interface used by the rest of the codebase.

    We keep it minimal on purpose. It matches your OpenAIClient.chat signature
    (config + per-call overrides), but other providers can ignore fields they
    don't support.
    """

    def chat(
        self,
        messages: List[Message] | List[Dict[str, Any]] | List[Any],
        *,
        config: Optional[AgentConfig] = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_output_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        ...


def _resolve_provider(cfg: Optional[LLMConfig]) -> Provider:
    settings = RegistrySettings()
    if cfg and cfg.provider is not None:
        return cfg.provider
    return settings.provider_used


def _build_openai_client() -> LLMClient:
    from elvex.llms.clients.openai_client import OpenAIClient

    return OpenAIClient()


def _build_ollama_client() -> LLMClient:
    from elvex.llms.clients.ollama_client import OllamaClient

    return OllamaClient()


def _build_claude_client() -> LLMClient:
    from elvex.llms.clients.claude_client import ClaudeClient

    return ClaudeClient()


CLIENT_BUILDERS: Dict[Provider, Callable[[], LLMClient]] = {
    "openai": _build_openai_client,
    "ollama": _build_ollama_client,
    "claude": _build_claude_client,
}


def get_llm_client(cfg: Optional[LLMConfig] = None) -> LLMClient:
    """Return an instantiated provider client.

    - Default: uses PROVIDER_USED from .env
    - Override: pass LLMConfig(provider="claude") (or "ollama" / "openai")

    Example:
        client = get_llm_client()  # uses PROVIDER_USED
        claude = get_llm_client(LLMConfig(provider="claude"))
    """

    provider = _resolve_provider(cfg)

    builder = CLIENT_BUILDERS.get(provider)
    if builder is None:
        raise ValueError(f"Unsupported provider: {provider}")

    return builder()
