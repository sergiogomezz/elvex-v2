from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from elvex.core.workflow import generate_run_id
from elvex.llms.errors import LLMProviderError
from elvex.llms.registry import Provider
from elvex.services.workflow_service import WorkflowService


def _now() -> str:
    return datetime.now(UTC).isoformat()


class StudioRunStore:
    """Small in-memory run registry for the first Elvex Studio iteration."""

    def __init__(self, workflow_service: WorkflowService | None = None) -> None:
        self.workflow_service = workflow_service or WorkflowService()
        self._runs: dict[str, dict[str, Any]] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="elvex-studio")

    def start(self, prompt: str, provider: Provider) -> dict[str, Any]:
        run_id = generate_run_id()
        run = {
            "run_id": run_id,
            "prompt": prompt,
            "provider": provider,
            "status": "queued",
            "result": None,
            "trace_id": None,
            "error": None,
            "created_at": _now(),
            "updated_at": _now(),
            "events": [],
        }
        with self._lock:
            self._runs[run_id] = run
        self._executor.submit(self._execute, run_id, prompt, provider)
        return deepcopy(run)

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            run = self._runs.get(run_id)
            return deepcopy(run) if run else None

    def _append_event(self, run_id: str, event: dict[str, Any]) -> None:
        with self._lock:
            run = self._runs[run_id]
            run["events"].append(
                {
                    **event,
                    "sequence": len(run["events"]) + 1,
                    "timestamp": _now(),
                }
            )
            run["status"] = "running"
            run["updated_at"] = _now()

    def _execute(self, run_id: str, prompt: str, provider: Provider) -> None:
        self._append_event(
            run_id,
            {
                "type": "run_started",
                "entity_id": "workflow",
                "entity_type": "workflow",
                "title": "Elvex workflow",
                "status": "running",
                "data": {"provider": provider},
            },
        )
        try:
            result = self.workflow_service.run(
                prompt,
                provider=provider,
                run_id=run_id,
                event_callback=lambda event: self._append_event(run_id, event),
            )
        except LLMProviderError as exc:
            self._finish_with_error(run_id, str(exc))
            return
        except Exception:
            self._finish_with_error(run_id, "Workflow execution failed")
            return

        with self._lock:
            run = self._runs[run_id]
            run["status"] = "completed"
            run["result"] = result.result
            run["trace_id"] = result.trace_id
            run["updated_at"] = _now()
            run["events"].append(
                {
                    "type": "run_completed",
                    "entity_id": "workflow",
                    "entity_type": "workflow",
                    "title": "Elvex workflow",
                    "status": "completed",
                    "data": {"output": result.result},
                    "sequence": len(run["events"]) + 1,
                    "timestamp": _now(),
                }
            )

    def _finish_with_error(self, run_id: str, message: str) -> None:
        with self._lock:
            run = self._runs[run_id]
            run["status"] = "failed"
            run["error"] = message
            run["updated_at"] = _now()
            run["events"].append(
                {
                    "type": "run_failed",
                    "entity_id": "workflow",
                    "entity_type": "workflow",
                    "title": "Elvex workflow",
                    "status": "failed",
                    "data": {"error": message},
                    "sequence": len(run["events"]) + 1,
                    "timestamp": _now(),
                }
            )


_studio_store = StudioRunStore()


def get_studio_store() -> StudioRunStore:
    return _studio_store
