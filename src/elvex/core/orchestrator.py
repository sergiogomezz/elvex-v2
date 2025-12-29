# coordina el trabajo, va llamando a cada agente de manera secuencial

from src.elvex.agents.specifier import TaskSpecifierAgent
from src.elvex.llms.registry import get_llm_client

def create_workflow(user_prompt):
    client = get_llm_client()
    specifier_agent = TaskSpecifierAgent(client)
    return specifier_agent.specify_task(user_prompt)
