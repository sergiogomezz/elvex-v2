from typing import Any, Literal

from pydantic import BaseModel, Field

ProviderName = Literal["openai", "claude", "ollama"]


class HealthResponse(BaseModel):
    status: str


class RootResponse(BaseModel):
    message: str
    docs: str


class WorkflowRequest(BaseModel):
    prompt: str = Field(min_length=1)


class WorkflowResponse(BaseModel):
    status: str
    result: str
    run_id: str
    output_dir: str
    trace_id: str | None = None


class StudioWorkflowRequest(BaseModel):
    prompt: str = Field(min_length=1)
    provider: ProviderName = "openai"


class StudioEvent(BaseModel):
    type: str
    entity_id: str
    entity_type: str
    title: str
    status: str
    data: dict[str, Any] = Field(default_factory=dict)
    sequence: int
    timestamp: str


class StudioRunResponse(BaseModel):
    run_id: str
    prompt: str
    provider: ProviderName
    status: str
    result: str | None = None
    trace_id: str | None = None
    error: str | None = None
    created_at: str
    updated_at: str
    events: list[StudioEvent] = Field(default_factory=list)
