# coordina el trabajo, va llamando a cada agente de manera secuencial

from src.elvex.agents.specifier import TaskSpecifierAgent

def create_workflow(input):
    TaskSpecifierAgent = TaskSpecifierAgent(input=input)