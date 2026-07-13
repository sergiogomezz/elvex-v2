import json

from elvex.core import workflow
from elvex.utils import loader


class RecordingObserver:
    def __init__(self):
        self.traces = []
        self.spans = []
        self.ends = []
        self.flushed = False

    def start_trace(self, **kwargs):
        trace = {"type": "trace", "id": "trace_test_123", **kwargs}
        self.traces.append(trace)
        return trace

    def start_span(self, **kwargs):
        span = {"type": "span", **kwargs}
        self.spans.append(span)
        return span

    def end(self, *args, **kwargs):
        self.ends.append({"args": args, **kwargs})
        return None

    def flush(self):
        self.flushed = True
        return None


class FakeSpecifierAgent:
    def __init__(self, client, agent_config=None):
        pass

    def specify_task(self, user_prompt, lf_parent=None):
        return json.dumps({"task_type": "demo", "details": user_prompt})


class FakeDividerAgent:
    def __init__(self, client, agent_config=None):
        pass

    def divide_tasks(self, specifier_agent_result, evaluator_feedback=None, lf_parent=None):
        return {
            "task_desc": "demo_task",
            "subtasks": [
                {
                    "id": "T1",
                    "title": "Collect facts",
                    "description": "Collect source material.",
                    "depends_on": [],
                },
                {
                    "id": "T2",
                    "title": "Write answer",
                    "description": "Use collected facts to write the answer.",
                    "depends_on": ["T1"],
                },
            ],
        }


class FakeEvaluatorAgent:
    def __init__(self, client, agent_config=None):
        pass

    def evaluate_tasks(self, divider_agent_result, lf_parent=None):
        return (
            {
                "task_desc": divider_agent_result["task_desc"],
                "is_valid": True,
                "correction_explanation": "",
            },
            None,
        )


def test_create_workflow_runs_dependency_order_and_returns_final_answer(tmp_path, monkeypatch):
    observer = RecordingObserver()
    records = {
        "orchestrated": [],
        "worker_contexts": {},
        "gathered_subtasks": [],
        "final_task_desc": None,
    }

    class FakeOrchestratorAgent:
        def __init__(self, client, agent_config=None):
            pass

        def design_agents(self, task_desc, subtask, lf_parent=None):
            records["orchestrated"].append(subtask["id"])
            orchestrator_dir = tmp_path / "orchestrator"
            orchestrator_dir.mkdir(exist_ok=True)
            payload = [
                {
                    "task_desc": task_desc,
                    "subtask_id": subtask["id"],
                    "agent_id": f"{subtask['id']}_A1",
                    "agent_type": "worker",
                    "objective": f"Do {subtask['id']}",
                    "prompt": "Return JSON.",
                }
            ]
            (orchestrator_dir / f"{subtask['id']}_output.json").write_text(json.dumps(payload))
            return str(orchestrator_dir)

    class FakeWorkerAgent:
        def __init__(
            self,
            client,
            task_id,
            agent_id,
            subtask_id,
            agent_type,
            objective,
            prompt,
            context,
            allowed_tools=None,
        ):
            self.task_id = task_id
            self.agent_id = agent_id
            self.subtask_id = subtask_id
            self.context = context

        def work(self, lf_parent=None):
            records["worker_contexts"][self.subtask_id] = self.context
            output_dir = tmp_path / "workers" / self.subtask_id
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{self.agent_id}_output.json"
            output_path.write_text(
                json.dumps(
                    {
                        "task_desc": self.task_id,
                        "subtask_id": self.subtask_id,
                        "agent_id": self.agent_id,
                        "answer": f"answer from {self.subtask_id}",
                    }
                )
            )
            return str(output_path)

    class FakeGathererSubagents:
        def __init__(self, client):
            pass

        def gather_subtask(self, task_desc, subtask_id, lf_parent=None):
            records["gathered_subtasks"].append(subtask_id)
            return str(tmp_path / f"{subtask_id}_gathered.json")

    class FakeGathererSubtasks:
        def __init__(self, client):
            pass

        def gather_subtasks(self, task_desc, lf_parent=None):
            records["final_task_desc"] = task_desc
            return "final answer"

    monkeypatch.setenv("PROVIDER_USED", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setattr(loader, "load_project_root_path", lambda: str(tmp_path))
    monkeypatch.setattr(workflow, "get_observer", lambda: observer)
    monkeypatch.setattr(workflow, "get_llm_client", lambda: object())
    monkeypatch.setattr(workflow, "TaskSpecifierAgent", FakeSpecifierAgent)
    monkeypatch.setattr(workflow, "TaskDividerAgent", FakeDividerAgent)
    monkeypatch.setattr(workflow, "TaskEvaluatorAgent", FakeEvaluatorAgent)
    monkeypatch.setattr(workflow, "OrchestratorAgent", FakeOrchestratorAgent)
    monkeypatch.setattr(workflow, "BaseWorkingAgent", FakeWorkerAgent)
    monkeypatch.setattr(workflow, "GathererSubagents", FakeGathererSubagents)
    monkeypatch.setattr(workflow, "GathererSubtasks", FakeGathererSubtasks)

    run = workflow.create_workflow_run("Build a demo answer", run_id="run_20260709_120000_deadbeef")

    assert run.status == "completed"
    assert run.result == "final answer"
    assert run.run_id == "run_20260709_120000_deadbeef"
    assert run.output_dir == str(tmp_path / "outputs" / "runs" / "run_20260709_120000_deadbeef")
    assert run.trace_id == "trace_test_123"
    assert (tmp_path / "outputs" / "runs" / "run_20260709_120000_deadbeef").is_dir()
    assert records["orchestrated"] == ["T1", "T2"]
    assert records["gathered_subtasks"] == ["T1", "T2"]
    assert records["final_task_desc"] == "demo_task"
    assert records["worker_contexts"]["T1"] == ""
    assert "answer from T1" in records["worker_contexts"]["T2"]
    assert '"subtask_id": "T1"' in records["worker_contexts"]["T2"]
    assert observer.traces[0]["name"] == "create_workflow"
    assert observer.traces[0]["metadata"] == {
        "workflow_stage": "workflow",
        "workflow_version": "v1",
        "original_user_prompt": "Build a demo answer",
        "run_id": "run_20260709_120000_deadbeef",
        "output_dir": str(tmp_path / "outputs" / "runs" / "run_20260709_120000_deadbeef"),
        "provider": "openai",
        "model": "gpt-test",
    }
    assert [span["name"] for span in observer.spans] == [
        "Specify Task",
        "Divide and Evaluate Round 1",
        "Orchestrate Subtask T1",
        "Orchestrate Subtask T2",
        "Execute Subtask T1",
        "Worker T1/T1_A1 (worker)",
        "Execute Subtask T2",
        "Worker T2/T2_A1 (worker)",
        "Final Gather demo_task",
    ]
    assert observer.spans[4]["metadata"]["workflow_stage"] == "execute_subtask"
    assert observer.spans[4]["metadata"]["subtask_id"] == "T1"
    assert observer.spans[5]["metadata"]["workflow_stage"] == "execute_worker"
    assert observer.spans[5]["metadata"]["agent_id"] == "T1_A1"
    assert observer.spans[5]["metadata"]["agent_type"] == "worker"
    assert observer.ends[-1]["metadata"]["task_desc"] == "demo_task"
    assert observer.ends[-1]["metadata"]["number_of_subtasks"] == 2
