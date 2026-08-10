from fastapi import APIRouter, Depends, HTTPException

from elvex.api.schemas import (
    HealthResponse,
    RootResponse,
    StudioRunResponse,
    StudioWorkflowRequest,
    WorkflowRequest,
    WorkflowResponse,
)
from elvex.core.errors import WorkflowReliabilityError
from elvex.llms.errors import LLMProviderError
from elvex.services.workflow_service import WorkflowService, get_workflow_service
from elvex.services.studio_service import StudioRunStore, get_studio_store

router = APIRouter()


@router.get("/", response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(message="Welcome to Elvex API", docs="/docs")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/runs", response_model=WorkflowResponse, response_model_exclude_none=True)
def create_run(
    request: WorkflowRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    try:
        run = workflow_service.run(prompt=request.prompt)
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except WorkflowReliabilityError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Workflow execution failed") from exc

    return WorkflowResponse(
        status=run.status,
        result=run.result,
        run_id=run.run_id,
        output_dir=run.output_dir,
        trace_id=run.trace_id,
    )


@router.post(
    "/studio/runs",
    response_model=StudioRunResponse,
    response_model_exclude_none=True,
    status_code=202,
)
def create_studio_run(
    request: StudioWorkflowRequest,
    studio_store: StudioRunStore = Depends(get_studio_store),
) -> StudioRunResponse:
    return StudioRunResponse.model_validate(
        studio_store.start(prompt=request.prompt, provider=request.provider)
    )


@router.get(
    "/studio/runs/{run_id}",
    response_model=StudioRunResponse,
    response_model_exclude_none=True,
)
def get_studio_run(
    run_id: str,
    studio_store: StudioRunStore = Depends(get_studio_store),
) -> StudioRunResponse:
    run = studio_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Studio run not found")
    return StudioRunResponse.model_validate(run)
