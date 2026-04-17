from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from elvex.tools.builtin_tools import TOOL_REGISTRY
from elvex.tools.policy import resolve_allowed_tool_names


def get_agent_tool_names(
    *,
    agent_type: str,
    agent_id: str,
    explicit_allowlist: Optional[Iterable[str]] = None,
) -> List[str]:
    return resolve_allowed_tool_names(
        registry=TOOL_REGISTRY,
        agent_type=agent_type,
        agent_id=agent_id,
        explicit_allowlist=explicit_allowlist,
    )


def get_agent_tool_definitions(
    *,
    agent_type: str,
    agent_id: str,
    explicit_allowlist: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    allowed = get_agent_tool_names(
        agent_type=agent_type,
        agent_id=agent_id,
        explicit_allowlist=explicit_allowlist,
    )
    return TOOL_REGISTRY.get_openai_definitions(allowed_names=allowed)


def get_agent_tool_executor(
    *,
    agent_type: str,
    agent_id: str,
    explicit_allowlist: Optional[Iterable[str]] = None,
):
    allowed = get_agent_tool_names(
        agent_type=agent_type,
        agent_id=agent_id,
        explicit_allowlist=explicit_allowlist,
    )
    return TOOL_REGISTRY.build_executor(allowed_names=allowed)


# Backward-compatible exports for existing call sites.
OPENAI_LOCAL_TOOLS = TOOL_REGISTRY.get_openai_definitions()


def execute_local_tool(name: str, arguments: Dict[str, Any]) -> str:
    return TOOL_REGISTRY.execute(name=name, arguments=arguments)

