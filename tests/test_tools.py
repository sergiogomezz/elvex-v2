from pydantic import BaseModel

from elvex.tools.interfaces import ToolSpec
from elvex.tools.local_tools import (
    execute_local_tool,
    get_agent_tool_definitions,
    get_agent_tool_names,
)
from elvex.tools.registry import ToolRegistry


class EchoInput(BaseModel):
    text: str


class EchoTool(ToolSpec):
    name = "echo"
    description = "Echo input text."
    input_model = EchoInput

    def _run(self, payload: EchoInput) -> str:
        return payload.text


def test_tool_registry_executes_registered_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())

    assert registry.execute("echo", {"text": "hello"}) == "hello"


def test_tool_registry_blocks_disallowed_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())

    assert registry.execute("echo", {"text": "hello"}, allowed_names=[]) == (
        "Error: Tool 'echo' is not allowed for this agent."
    )


def test_tool_registry_reports_unknown_tool():
    registry = ToolRegistry()

    assert registry.execute("missing", {}) == "Error: Unknown tool 'missing'."


def test_local_calculate_tool_executes_safe_expression():
    assert execute_local_tool("calculate", {"expression": "sqrt(16) + 2"}) == "6.0"


def test_local_calculate_tool_rejects_unsafe_expression():
    result = execute_local_tool("calculate", {"expression": "__import__('os')"})

    assert result.startswith("Error:")


def test_agent_tool_allowlist_filters_registered_tools():
    assert get_agent_tool_names(
        agent_type="researcher",
        agent_id="A1",
        explicit_allowlist=["calculate", "missing"],
    ) == ["calculate"]


def test_agent_tool_definitions_have_openai_function_shape():
    definitions = get_agent_tool_definitions(agent_type="researcher", agent_id="A1")

    assert {definition["name"] for definition in definitions} >= {"calculate", "get_exchange_rate"}
    assert all(definition["type"] == "function" for definition in definitions)
