from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class WorkflowRequest(BaseModel):
    prompt: str = Field(min_length=1)


class WorkflowResponse(BaseModel):
    result: str
