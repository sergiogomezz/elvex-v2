from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, RootModel


class TaskSpecifierOutput(BaseModel):
    task_type: str
    details: str


class Subtask(BaseModel):
    id: str
    title: str
    description: str
    depends_on: List[str]


class TaskDividerOutput(BaseModel):
    task_desc: str
    subtasks: List[Subtask]


class TaskEvaluatorOutput(BaseModel):
    task_desc: str
    is_valid: bool
    correction_explanation: str


class OrchestratorAgentSpec(BaseModel):
    task_desc: str
    subtask_id: str
    agent_id: str
    agent_type: str
    objective: str
    prompt: str


class OrchestratorPlan(RootModel[List[OrchestratorAgentSpec]]):
    pass


class WorkerAgentOutput(BaseModel):
    task_desc: str
    subtask_id: str
    agent_id: str
    answer: Any
