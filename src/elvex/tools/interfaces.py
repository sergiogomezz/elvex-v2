from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Type

from pydantic import BaseModel


class ToolSpec(ABC):
    """Common interface for local tools used by worker agents."""

    name: str
    description: str
    input_model: Type[BaseModel]

    def to_openai_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.input_model.model_json_schema(),
        }

    def run(self, arguments: Dict[str, Any]) -> str:
        payload = self.input_model.model_validate(arguments)
        return self._run(payload)

    @abstractmethod
    def _run(self, payload: BaseModel) -> str:
        """Execute tool logic from validated payload."""

