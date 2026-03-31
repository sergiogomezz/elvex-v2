import json
import os

from elvex.llms.types import AgentConfig
from elvex.agents.base_worker_agent import BaseWorkingAgent
from elvex.agents.gatherer_subagents import GathererSubagents
from elvex.agents.gatherer_subtasks import GathererSubtasks
from elvex.agents.specifier import TaskSpecifierAgent
from elvex.agents.divider import TaskDividerAgent
from elvex.agents.evaluator import TaskEvaluatorAgent
from elvex.agents.orchestrator import OrchestratorAgent
from elvex.llms.registry import get_llm_client
from elvex.core.task_graph import build_task_graph, get_ready_subtasks, subtasks_from_divider_output


def _build_dependency_context(dependency_output_paths: list[str]) -> str:
    if not dependency_output_paths:
        return ""

    context_chunks: list[str] = []
    for output_path in dependency_output_paths:
        if not os.path.exists(output_path):
            continue
        with open(output_path, "r") as f:
            context_chunks.append(f.read())

    return "\n\n".join(context_chunks)


def create_workflow(user_prompt: str) -> str:
    # getting client. It may be possible to get a different client for each agent
    default_client = get_llm_client()

    # Invoke specifier agent
    specifier_agent_config = AgentConfig(temperature=0.3)
    
    specifier_agent = TaskSpecifierAgent(client=default_client, agent_config=specifier_agent_config)
    specifier_result = specifier_agent.specify_task(user_prompt)

    # Invoke divider agent
    divider_agent_config = AgentConfig(temperature=0.7)

    divider_agent = TaskDividerAgent(client=default_client, agent_config=divider_agent_config)
    
    evaluator_agent_config = AgentConfig(temperature=0.1)
    evaluator_agent = TaskEvaluatorAgent(client=default_client, agent_config=evaluator_agent_config)

    max_rounds = 3
    evaluator_feedback = None
    divider_result = None

    for _ in range(max_rounds):
        divider_result = divider_agent.divide_tasks(specifier_result, evaluator_feedback=evaluator_feedback)
        evaluation, _ = evaluator_agent.evaluate_tasks(divider_result)

        if evaluation.get("is_valid", False):
            break

        evaluator_feedback = {
            "is_valid": evaluation.get("is_valid", False),
            "correction_explanation": evaluation.get("correction_explanation", ""),
        }

    if divider_result is None:
        raise ValueError("Divider did not produce a result.")

    # Build/validate task graph
    subtasks = subtasks_from_divider_output(divider_result)
    build_task_graph(subtasks)

    task_desc = divider_result.get("task_desc", "unnamed_task")

    # Invoke orchestrator for each subtask in dependency order
    orchestrator_agent_config = AgentConfig(temperature=0.2)
    orchestrator_agent = OrchestratorAgent(client=default_client, agent_config=orchestrator_agent_config)

    # Generate worker plans for every subtask.
    subtask_specs: dict[str, list[dict]] = {}
    orchestrated_subtasks: set[str] = set()

    while len(orchestrated_subtasks) < len(subtasks):
        ready_subtasks = get_ready_subtasks(subtasks, orchestrated_subtasks)
        if not ready_subtasks:
            raise ValueError("No ready subtasks found while orchestrating; possible dependency issue.")

        for st in ready_subtasks:
            orchestrator_dir = orchestrator_agent.design_agents(
                task_desc,
                {
                    "id": st.id,
                    "title": st.title,
                    "description": st.description,
                    "depends_on": list(st.depends_on),
                },
            )
            agents_file_path = os.path.join(orchestrator_dir, f"{st.id}_output.json")
            with open(agents_file_path, "r") as f:
                subtask_specs[st.id] = json.load(f)
            orchestrated_subtasks.add(st.id)

    # Execute worker agents with dependency-aware context.
    subagents_gatherer = GathererSubagents(client=default_client)
    subtask_agent_outputs: dict[str, list[str]] = {}
    executed_subtasks: set[str] = set()

    while len(executed_subtasks) < len(subtasks):
        ready_subtasks = get_ready_subtasks(subtasks, executed_subtasks)
        if not ready_subtasks:
            raise ValueError("No ready subtasks found while executing workers; possible dependency issue.")

        for st in ready_subtasks:
            dependency_paths: list[str] = []
            for dep_id in st.depends_on:
                dependency_paths.extend(subtask_agent_outputs.get(dep_id, []))

            context = _build_dependency_context(dependency_paths)

            worker_specs = subtask_specs.get(st.id, [])
            if not worker_specs:
                raise ValueError(f"No orchestrator output found for subtask '{st.id}'.")

            subtask_outputs: list[str] = []
            for agent_spec in worker_specs:
                worker = BaseWorkingAgent(
                    client=default_client,
                    task_id=task_desc,
                    agent_id=agent_spec["agent_id"],
                    subtask_id=agent_spec["subtask_id"],
                    agent_type=agent_spec["agent_type"],
                    objective=agent_spec["objective"],
                    prompt=agent_spec["prompt"],
                    context=context,
                )
                output_path = worker.work()
                if output_path is None:
                    raise ValueError(
                        f"Worker agent '{agent_spec['agent_id']}' failed to produce valid JSON output."
                    )
                subtask_outputs.append(output_path)

            subtask_agent_outputs[st.id] = subtask_outputs
            subagents_gatherer.gather_subtask(task_desc, st.id)
            executed_subtasks.add(st.id)

    subtasks_gatherer = GathererSubtasks(client=default_client)
    final_answer = subtasks_gatherer.gather_subtasks(task_desc)

    return final_answer
