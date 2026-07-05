class LLMProviderError(RuntimeError):
    """Base error for provider failures that should be safe to show to users."""


class LLMQuotaError(LLMProviderError):
    """Raised when a provider rejects a request because quota or credits are exhausted."""
