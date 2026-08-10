from elvex.core.workflow import (
    WorkflowEventCallback,
    WorkflowRunResult,
    create_workflow_run,
)
from elvex.llms.registry import Provider


class WorkflowService:
    def run(
        self,
        prompt: str,
        *,
        provider: Provider | None = None,
        run_id: str | None = None,
        event_callback: WorkflowEventCallback | None = None,
    ) -> WorkflowRunResult:
        return create_workflow_run(
            prompt,
            provider=provider,
            run_id=run_id,
            event_callback=event_callback,
        )


def get_workflow_service() -> WorkflowService:
    return WorkflowService()
