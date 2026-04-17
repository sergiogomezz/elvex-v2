from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

from elvex.tools.interfaces import ToolSpec


class ToolRegistry:
    """In-memory registry of available local tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def list_names(self) -> List[str]:
        return list(self._tools.keys())

    def get_openai_definitions(self, allowed_names: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
        names = set(allowed_names) if allowed_names is not None else set(self._tools.keys())
        return [tool.to_openai_definition() for name, tool in self._tools.items() if name in names]

    def execute(self, name: str, arguments: Dict[str, Any], allowed_names: Optional[Iterable[str]] = None) -> str:
        if allowed_names is not None and name not in set(allowed_names):
            return f"Error: Tool '{name}' is not allowed for this agent."

        tool = self._tools.get(name)
        if tool is None:
            return f"Error: Unknown tool '{name}'."

        try:
            return str(tool.run(arguments))
        except Exception as exc:
            return f"Error: {str(exc)}"

    def build_executor(self, allowed_names: Optional[Iterable[str]] = None) -> Callable[[str, Dict[str, Any]], str]:
        def _executor(name: str, arguments: Dict[str, Any]) -> str:
            return self.execute(name=name, arguments=arguments, allowed_names=allowed_names)

        return _executor

