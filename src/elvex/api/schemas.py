from pydantic import BaseModel, Field


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
