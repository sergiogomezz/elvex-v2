# Coordinates the workflow and call the agents as needed

from elvex.llms.types import AgentConfig
from elvex.agents.specifier import TaskSpecifierAgent
from elvex.llms.registry import get_llm_client


def create_workflow(user_prompt: str) -> str:
    # getting client. It may be possible to get a different client for each agent
    default_client = get_llm_client()

    # Invoke specifier agent
    specifier_agent_config = AgentConfig(
        temperature=0.3)

    specifier_agent = TaskSpecifierAgent(client=default_client, agent_config=specifier_agent_config)

    return specifier_agent.specify_task(user_prompt)
