import pytest

from elvex.llms.clients.openai_client import OpenAIClient
from elvex.llms.errors import LLMQuotaError


class NoopObserver:
    def start_generation(self, **kwargs):
        return object()

    def end(self, *args, **kwargs):
        return None


class FakeInsufficientQuotaError(Exception):
    code = "insufficient_quota"


class FakeResponses:
    def create(self, **kwargs):
        raise FakeInsufficientQuotaError("You exceeded your current quota.")


class FakeOpenAISDKClient:
    responses = FakeResponses()


def test_openai_client_maps_insufficient_quota_to_friendly_error(monkeypatch):
    monkeypatch.setattr("elvex.llms.clients.openai_client.get_observer", lambda: NoopObserver())

    client = OpenAIClient.__new__(OpenAIClient)
    client.client = FakeOpenAISDKClient()
    client.default_model = "test-model"

    with pytest.raises(LLMQuotaError, match="Insufficient quota on OpenAI API"):
        client.chat([{"role": "user", "content": "hello"}])
