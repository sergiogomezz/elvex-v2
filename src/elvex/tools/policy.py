from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from elvex.tools.registry import ToolRegistry

ALLOW_ALL = "*"

# Optional agent-specific restrictions.
# - Keep ALLOW_ALL to permit every registered tool.
# - Set lists to restrict access.
DEFAULT_TOOL_ALLOWLIST: str | List[str] = ALLOW_ALL
AGENT_TYPE_TOOL_ALLOWLIST: Dict[str, str | List[str]] = {}
AGENT_ID_TOOL_ALLOWLIST: Dict[str, str | List[str]] = {}


def resolve_allowed_tool_names(
    registry: ToolRegistry,
    *,
    agent_type: str,
    agent_id: str,
    explicit_allowlist: Optional[Iterable[str]] = None,
) -> List[str]:
    all_tools = registry.list_names()

    if explicit_allowlist is not None:
        allowed = [name for name in explicit_allowlist if name in all_tools]
        return allowed

    policy_value: str | List[str] = DEFAULT_TOOL_ALLOWLIST
    if agent_type in AGENT_TYPE_TOOL_ALLOWLIST:
        policy_value = AGENT_TYPE_TOOL_ALLOWLIST[agent_type]
    if agent_id in AGENT_ID_TOOL_ALLOWLIST:
        policy_value = AGENT_ID_TOOL_ALLOWLIST[agent_id]

    if policy_value == ALLOW_ALL:
        return all_tools

    return [name for name in policy_value if name in all_tools]

