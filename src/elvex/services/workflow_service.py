from elvex.core.workflow import WorkflowRunResult, create_workflow_run


class WorkflowService:
    def run(self, prompt: str) -> WorkflowRunResult:
        return create_workflow_run(prompt)


def get_workflow_service() -> WorkflowService:
    return WorkflowService()
