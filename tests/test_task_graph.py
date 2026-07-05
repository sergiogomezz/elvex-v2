import pytest

from elvex.core.task_graph import (
    Subtask,
    TaskGraphError,
    build_task_graph,
    get_ready_subtasks,
    subtasks_from_divider_output,
    topological_sort,
)


def test_topological_sort_orders_dependencies_before_dependents():
    subtasks = [
        Subtask(id="T3", title="final", description="", depends_on=["T1", "T2"]),
        Subtask(id="T2", title="middle", description="", depends_on=["T1"]),
        Subtask(id="T1", title="first", description="", depends_on=[]),
    ]

    assert [subtask.id for subtask in topological_sort(subtasks)] == ["T1", "T2", "T3"]


def test_build_task_graph_rejects_duplicate_ids():
    subtasks = [
        Subtask(id="T1", title="one", description="", depends_on=[]),
        Subtask(id="T1", title="again", description="", depends_on=[]),
    ]

    with pytest.raises(TaskGraphError, match="Duplicate subtask id"):
        build_task_graph(subtasks)


def test_build_task_graph_rejects_unknown_dependency():
    subtasks = [Subtask(id="T1", title="one", description="", depends_on=["missing"])]

    with pytest.raises(TaskGraphError, match="depends on unknown id"):
        build_task_graph(subtasks)


def test_topological_sort_rejects_cycles():
    subtasks = [
        Subtask(id="T1", title="one", description="", depends_on=["T2"]),
        Subtask(id="T2", title="two", description="", depends_on=["T1"]),
    ]

    with pytest.raises(TaskGraphError, match="Cycle detected"):
        topological_sort(subtasks)


def test_get_ready_subtasks_returns_only_unblocked_tasks():
    subtasks = [
        Subtask(id="T1", title="one", description="", depends_on=[]),
        Subtask(id="T2", title="two", description="", depends_on=["T1"]),
        Subtask(id="T3", title="three", description="", depends_on=[]),
    ]

    assert [subtask.id for subtask in get_ready_subtasks(subtasks, completed_ids=set())] == ["T1", "T3"]
    assert [subtask.id for subtask in get_ready_subtasks(subtasks, completed_ids={"T1"})] == ["T2", "T3"]


def test_subtasks_from_divider_output_handles_missing_optional_fields():
    divider_output = {
        "subtasks": [
            {"id": "T1", "title": "one"},
            {"id": "T2", "description": "two", "depends_on": ["T1"]},
        ]
    }

    subtasks = subtasks_from_divider_output(divider_output)

    assert subtasks == [
        Subtask(id="T1", title="one", description="", depends_on=[]),
        Subtask(id="T2", title="", description="two", depends_on=["T1"]),
    ]
