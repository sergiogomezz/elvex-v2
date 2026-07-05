import json

import pytest

from elvex.agents.specifier import TaskSpecifierAgent
from elvex.agents.base_worker_agent import BaseWorkingAgent
from elvex.core.errors import MalformedAgentResponseError, OrchestratorOutputError
from elvex.core.workflow import _load_orchestrator_specs


class FakeResponse:
    def __init__(self, text):
        self.text = text


class SequenceClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, **kwargs):
        self.calls.append({"messages": messages, **kwargs})
        return FakeResponse(self.responses.pop(0))


def test_json_agent_retries_once_after_malformed_json():
    client = SequenceClient(
        [
            "not json",
            json.dumps({"task_type": "demo", "details": "ok"}),
        ]
    )
    agent = TaskSpecifierAgent(client=client)

    result = agent.specify_task("demo")

    assert json.loads(result) == {"task_type": "demo", "details": "ok"}
    assert len(client.calls) == 2
    assert client.calls[0]["observation_metadata"]["retry_number"] == 0
    assert client.calls[1]["observation_metadata"]["retry_number"] == 1
    assert client.calls[1]["observation_metadata"]["is_retry"] is True
    assert "previous response was not valid JSON" in client.calls[1]["messages"][-1]["content"]


def test_json_agent_raises_clear_error_after_retry_exhausted():
    client = SequenceClient(["not json", "still not json"])
    agent = TaskSpecifierAgent(client=client)

    with pytest.raises(MalformedAgentResponseError, match="TaskSpecifierAgent returned malformed JSON"):
        agent.specify_task("demo")

    assert len(client.calls) == 2


def test_worker_raises_clear_error_after_retry_exhausted():
    client = SequenceClient(["not json", "still not json"])
    worker = BaseWorkingAgent(
        client=client,
        task_id="demo_task",
        agent_id="A1",
        subtask_id="T1",
        agent_type="Researcher",
        objective="Research",
        prompt="Return JSON",
        context="",
    )

    with pytest.raises(MalformedAgentResponseError, match="Worker 'A1' for subtask 'T1'"):
        worker.work()

    assert len(client.calls) == 2
    assert client.calls[0]["observation_metadata"]["retry_number"] == 0
    assert client.calls[1]["observation_metadata"]["retry_number"] == 1


def test_load_orchestrator_specs_rejects_missing_file(tmp_path):
    with pytest.raises(OrchestratorOutputError, match="Missing orchestrator output"):
        _load_orchestrator_specs(str(tmp_path), "T1")


def test_load_orchestrator_specs_rejects_invalid_json(tmp_path):
    (tmp_path / "T1_output.json").write_text("not json")

    with pytest.raises(OrchestratorOutputError, match="Invalid orchestrator JSON"):
        _load_orchestrator_specs(str(tmp_path), "T1")


def test_load_orchestrator_specs_rejects_missing_worker_keys(tmp_path):
    (tmp_path / "T1_output.json").write_text(json.dumps([{"agent_id": "A1"}]))

    with pytest.raises(OrchestratorOutputError, match="missing keys"):
        _load_orchestrator_specs(str(tmp_path), "T1")


def test_load_orchestrator_specs_accepts_valid_worker_specs(tmp_path):
    payload = [
        {
            "task_desc": "demo_task",
            "subtask_id": "T1",
            "agent_id": "A1",
            "agent_type": "Researcher",
            "objective": "Research",
            "prompt": "Return JSON",
        }
    ]
    (tmp_path / "T1_output.json").write_text(json.dumps(payload))

    assert _load_orchestrator_specs(str(tmp_path), "T1") == payload
