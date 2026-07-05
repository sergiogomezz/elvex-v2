class WorkflowReliabilityError(RuntimeError):
    """Base error for workflow failures that should be safe to show to users."""


class MalformedAgentResponseError(WorkflowReliabilityError):
    """Raised when an agent fails to return valid structured output after bounded retries."""


class OrchestratorOutputError(WorkflowReliabilityError):
    """Raised when orchestrator output files are missing or invalid."""


class WorkerExecutionError(WorkflowReliabilityError):
    """Raised when a worker cannot complete its assigned subtask."""
