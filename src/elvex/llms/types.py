from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

Role = Literal["system", "user", "assistant"]


class Message(BaseModel):
    role: Role
    content: str


class ChatResponse(BaseModel):
    text: str
    usage: Optional[dict] = None
    raw: Optional[Any] = None


class AgentConfig(BaseModel):
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    tools: Optional[List[Dict[str, Any]]] = None
    max_output_tokens: Optional[int] = None
