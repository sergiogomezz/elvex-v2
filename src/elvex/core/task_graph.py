from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set


class TaskGraphError(ValueError):
    pass


@dataclass(frozen=True)
class Subtask:
    id: str
    title: str
    description: str
    depends_on: List[str]


def subtasks_from_divider_output(divider_output: dict) -> List[Subtask]:
    subtasks = divider_output.get("subtasks", [])
    return [
        Subtask(
            id=st.get("id", ""),
            title=st.get("title", ""),
            description=st.get("description", ""),
            depends_on=list(st.get("depends_on", [])),
        )
        for st in subtasks
    ]


def build_task_graph(
    subtasks: Iterable[Subtask],
) -> tuple[Dict[str, Subtask], Dict[str, Set[str]], Dict[str, Set[str]]]:
    """
    Returns:
      - nodes: id -> Subtask
      - outgoing: id -> set(of nodes that depend on id)
      - incoming: id -> set(of prerequisites for id)
    """
    nodes: Dict[str, Subtask] = {}
    for st in subtasks:
        if st.id in nodes:
            raise TaskGraphError(f"Duplicate subtask id: {st.id}")
        nodes[st.id] = st
    
    outgoing: Dict[str, Set[str]] = {sid: set() for sid in nodes}
    incoming: Dict[str, Set[str]] = {sid: set() for sid in nodes}

    # Validate dependencies exist + no self dependency
    for st in nodes.values():
        for dep in st.depends_on:
            if dep == st.id:
                raise TaskGraphError(f"Subtask '{st.id}' depends on itself.")
            if dep not in nodes:
                raise TaskGraphError(f"Subtask '{st.id}' depends on unknown id '{dep}'.")
            incoming[st.id].add(dep)
            outgoing[dep].add(st.id)

    return nodes, outgoing, incoming


def topological_sort(subtasks: Iterable[Subtask]) -> List[Subtask]:
    """
    Kahn's algorithm. Works for linear and non-linear dependency structures.
    Raises TaskGraphError on cycles or invalid deps.
    """
    nodes, outgoing, incoming = build_task_graph(subtasks)

    # Start with nodes that have no prerequisites
    ready = sorted([sid for sid, deps in incoming.items() if not deps])  # sorted for determinism
    ordered_ids: List[str] = []

    while ready:
        current = ready.pop(0)
        ordered_ids.append(current)

        # For each node that depends on 'current', remove the prerequisite edge
        for nxt in sorted(outgoing[current]):
            incoming[nxt].remove(current)
            if not incoming[nxt]:
                ready.append(nxt)
                ready.sort()

    if len(ordered_ids) != len(nodes):
        # Cycle exists. Provide helpful info.
        remaining = [sid for sid, deps in incoming.items() if deps]
        sample = {sid: sorted(list(incoming[sid])) for sid in remaining}
        raise TaskGraphError(f"Cycle detected or unresolved deps. Remaining: {sample}")

    return [nodes[sid] for sid in ordered_ids]


def get_ready_subtasks(subtasks: Iterable[Subtask], completed_ids: Set[str]) -> List[Subtask]:
    """
    Useful for an orchestrator that executes in 'waves' (parallel-ready tasks).
    Returns tasks whose dependencies are all satisfied and not completed yet.
    """
    nodes, _, incoming = build_task_graph(subtasks)

    ready: List[Subtask] = []
    for sid, st in nodes.items():
        if sid in completed_ids:
            continue
        if incoming[sid].issubset(completed_ids):
            ready.append(st)

    # deterministic ordering
    return sorted(ready, key=lambda x: x.id)
