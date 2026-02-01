# Coordinates the workflow and call the agents as needed

from elvex.llms.types import AgentConfig
from elvex.agents.specifier import TaskSpecifierAgent
from elvex.agents.divider import TaskDividerAgent
from elvex.agents.evaluator import TaskEvaluatorAgent
from elvex.agents.orchestrator import OrchestratorAgent
from elvex.llms.registry import get_llm_client
from elvex.core.task_graph import build_task_graph, get_ready_subtasks, subtasks_from_divider_output


def create_workflow(user_prompt: str) -> dict:
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
    
    completed_subtasks: set[str] = set()

    while len(completed_subtasks) < len(subtasks):
        ready_subtasks = get_ready_subtasks(subtasks, completed_subtasks)
        if not ready_subtasks:
            raise ValueError("No ready subtasks found; possible dependency issue.")

        for st in ready_subtasks:
            orchestrator_agent.design_agents(
                task_desc,
                {
                    "id": st.id,
                    "title": st.title,
                    "description": st.description,
                    "depends_on": list(st.depends_on),
                },
            )
            completed_subtasks.add(st.id)

    return divider_result
