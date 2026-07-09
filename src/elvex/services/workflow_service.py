from elvex.core.workflow import create_workflow


class WorkflowService:
    def run(self, prompt: str) -> str:
        return create_workflow(prompt)


def get_workflow_service() -> WorkflowService:
    return WorkflowService()
