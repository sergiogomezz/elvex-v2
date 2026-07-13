from fastapi.testclient import TestClient

from elvex.api.app import create_app
from elvex.core.errors import WorkflowReliabilityError
from elvex.core.workflow import WorkflowRunResult
from elvex.llms.errors import LLMQuotaError
from elvex.services.workflow_service import get_workflow_service


class FakeWorkflowService:
    def __init__(self, result: WorkflowRunResult | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.prompts: list[str] = []

    def run(self, prompt: str) -> WorkflowRunResult:
        self.prompts.append(prompt)
        if self.error is not None:
            raise self.error
        return self.result or WorkflowRunResult(
            status="completed",
            result="fake workflow result",
            run_id="run_20260709_120000_deadbeef",
            output_dir="/tmp/elvex/outputs/runs/run_20260709_120000_deadbeef",
            trace_id=None,
        )


def _client_with_service(service: FakeWorkflowService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_workflow_service] = lambda: service
    return TestClient(app)


def test_health_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_returns_welcome_message():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Elvex API", "docs": "/docs"}


def test_create_run_returns_service_result_without_calling_llm():
    service = FakeWorkflowService(
        result=WorkflowRunResult(
            status="completed",
            result="fake answer",
            run_id="run_20260709_120000_deadbeef",
            output_dir="/tmp/elvex/outputs/runs/run_20260709_120000_deadbeef",
            trace_id="trace_123",
        )
    )
    client = _client_with_service(service)

    response = client.post("/runs", json={"prompt": "Build a demo plan"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "result": "fake answer",
        "run_id": "run_20260709_120000_deadbeef",
        "output_dir": "/tmp/elvex/outputs/runs/run_20260709_120000_deadbeef",
        "trace_id": "trace_123",
    }
    assert service.prompts == ["Build a demo plan"]


def test_create_run_omits_trace_id_when_unavailable():
    service = FakeWorkflowService(
        result=WorkflowRunResult(
            status="completed",
            result="fake answer",
            run_id="run_20260709_120000_deadbeef",
            output_dir="/tmp/elvex/outputs/runs/run_20260709_120000_deadbeef",
            trace_id=None,
        )
    )
    client = _client_with_service(service)

    response = client.post("/runs", json={"prompt": "Build a demo plan"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "result": "fake answer",
        "run_id": "run_20260709_120000_deadbeef",
        "output_dir": "/tmp/elvex/outputs/runs/run_20260709_120000_deadbeef",
    }


def test_create_run_rejects_empty_prompt():
    service = FakeWorkflowService()
    client = _client_with_service(service)

    response = client.post("/runs", json={"prompt": ""})

    assert response.status_code == 422
    assert service.prompts == []


def test_create_run_maps_llm_provider_errors_to_502():
    service = FakeWorkflowService(error=LLMQuotaError("Insufficient quota on OpenAI API."))
    client = _client_with_service(service)

    response = client.post("/runs", json={"prompt": "Run the workflow"})

    assert response.status_code == 502
    assert response.json() == {"detail": "Insufficient quota on OpenAI API."}


def test_create_run_maps_workflow_errors_to_500():
    service = FakeWorkflowService(error=WorkflowReliabilityError("Worker failed cleanly."))
    client = _client_with_service(service)

    response = client.post("/runs", json={"prompt": "Run the workflow"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Worker failed cleanly."}


def test_create_run_hides_unexpected_error_details():
    service = FakeWorkflowService(error=RuntimeError("database password leaked in stack"))
    client = _client_with_service(service)

    response = client.post("/runs", json={"prompt": "Run the workflow"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Workflow execution failed"}
