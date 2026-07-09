from fastapi.testclient import TestClient

from elvex.api.app import create_app
from elvex.core.errors import WorkflowReliabilityError
from elvex.llms.errors import LLMQuotaError
from elvex.services.workflow_service import get_workflow_service


class FakeWorkflowService:
    def __init__(self, result: str | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.prompts: list[str] = []

    def run(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self.error is not None:
            raise self.error
        return self.result or "fake workflow result"


def _client_with_service(service: FakeWorkflowService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_workflow_service] = lambda: service
    return TestClient(app)


def test_health_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_workflow_returns_service_result_without_calling_llm():
    service = FakeWorkflowService(result="fake answer")
    client = _client_with_service(service)

    response = client.post("/workflow", json={"prompt": "Build a demo plan"})

    assert response.status_code == 200
    assert response.json() == {"result": "fake answer"}
    assert service.prompts == ["Build a demo plan"]


def test_run_workflow_rejects_empty_prompt():
    service = FakeWorkflowService(result="should not run")
    client = _client_with_service(service)

    response = client.post("/workflow", json={"prompt": ""})

    assert response.status_code == 422
    assert service.prompts == []


def test_run_workflow_maps_llm_provider_errors_to_502():
    service = FakeWorkflowService(error=LLMQuotaError("Insufficient quota on OpenAI API."))
    client = _client_with_service(service)

    response = client.post("/workflow", json={"prompt": "Run the workflow"})

    assert response.status_code == 502
    assert response.json() == {"detail": "Insufficient quota on OpenAI API."}


def test_run_workflow_maps_workflow_errors_to_500():
    service = FakeWorkflowService(error=WorkflowReliabilityError("Worker failed cleanly."))
    client = _client_with_service(service)

    response = client.post("/workflow", json={"prompt": "Run the workflow"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Worker failed cleanly."}


def test_run_workflow_hides_unexpected_error_details():
    service = FakeWorkflowService(error=RuntimeError("database password leaked in stack"))
    client = _client_with_service(service)

    response = client.post("/workflow", json={"prompt": "Run the workflow"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Workflow execution failed"}
