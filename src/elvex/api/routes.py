from fastapi import APIRouter, Depends, HTTPException

from elvex.api.schemas import HealthResponse, WorkflowRequest, WorkflowResponse
from elvex.core.errors import WorkflowReliabilityError
from elvex.llms.errors import LLMProviderError
from elvex.services.workflow_service import WorkflowService, get_workflow_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/workflow", response_model=WorkflowResponse)
def run_workflow(
    request: WorkflowRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    try:
        result = workflow_service.run(prompt=request.prompt)
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except WorkflowReliabilityError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Workflow execution failed") from exc

    return WorkflowResponse(result=result)
