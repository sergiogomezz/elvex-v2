from config import config as cfg
from config.loader import load_keys, get_api_key, load_json
from tools.utils import landing_intro, loading_animation

from clients.openai_client import OpenAIClient
from clients.ollama_client import LocalLLMClient

from agents.task_specifier import TaskSpecifierAgent
from agents.task_divider import TaskDividerAgent
from agents.task_evaluator import TaskEvaluatorAgent
from agents.orchestrator import OrchestratorAgent
from agents.base_working_agent import BaseWorkingAgent
from agents.subtasks_gatherer import SubtasksGatherer

import os

def main():

    if cfg.USE_LOCAL_MODEL:
        client = LocalLLMClient(model=cfg.LOCAL_MODEL_NAME)

    else:
        keys = load_keys()
        api_key = get_api_key(keys)
        client = OpenAIClient(api_key=api_key, model=cfg.OPENAI_MODEL_NAME)

    landing_intro()

    first_user_input = input('What do you want to do? ')

    stop = loading_animation()

    try:
        # Invoke (1) Specifier Agent
        specifier_agent = TaskSpecifierAgent(client=client)
        specifier_agent_result = specifier_agent.specify_task(first_user_input)
        # Invoke (2) Divider Agent
        divider_agent = TaskDividerAgent(client=client)
        divider_agent_result = divider_agent.divide_tasks(specifier_agent_result)

        # Invoke (3) Evaluator Agent
        evaluator_agent = TaskEvaluatorAgent(client=client)
        subtasks_path = evaluator_agent.evaluate_tasks(divider_agent_result)

        # Get Each Subtask and Invoke (4) an Agent Orchestrator for each one
        # Improvement: add context and memory -- subtasks dependencies
        subtasks = load_json(subtasks_path)

        task_id = subtasks["task_desc"]
        subtasks = subtasks["subtasks"]

        for subtask in subtasks:
            orchestrator = OrchestratorAgent(client=client, task_id=task_id)
            orchestrator_path = orchestrator.design_agents(subtask)


        # Creating the dependencies & context for working agents (5)
        agent_outputs = {}
        pending_subtasks = subtasks[:]
        completed_subtasks = set()

        while pending_subtasks:
            for subtask in pending_subtasks[:]:
                subtask_id = subtask['id']
                depends_on = subtask['depends_on']

                if all(dep in completed_subtasks for dep in depends_on):
                    agents_file_path = os.path.join(orchestrator_path, f"{subtask_id}_output.json")

                    agents = load_json(agents_file_path)

                    for agent in agents:
                        context=""
                        for dep_id in depends_on:
                            dep_path = agent_outputs.get(dep_id)
                            if dep_path and os.path.exists(dep_path):
                                with open(dep_path) as f:
                                    context += f"\n--- Output from {dep_id} ---\n" + f.read()

                        working_agent = BaseWorkingAgent(
                            client = client,
                            task_id = task_id,
                            agent_id = agent['agent_id'],
                            subtask_id = agent['subtask_id'],
                            agent_type = agent['agent_type'],
                            objective = agent['objective'],
                            prompt = agent['prompt'],
                            context = context
                        )

                        agent_path = working_agent.work()
                        agent_outputs[agent['agent_id']] = agent_path
                        completed_subtasks.add(subtask_id)

                    pending_subtasks.remove(subtask)

                else:
                    missing = [dep for dep in depends_on if dep not in completed_subtasks]
                    print(f"Subtask {subtask_id} waiting on: {missing}")
        
        
        # Invoke (6) Agent Subtasks Gatherer
        subtask_gatherer_agent = SubtasksGatherer(client=client)
        final_user_output = subtask_gatherer_agent.gather_subtasks(task_id)

        print(f"AI's final answer: {final_user_output}")
    
    except Exception as e:
        print(f"\nAgents were not too accurate this time 😔\nError: {e}")

    finally:
        stop()


if __name__ == "__main__":
    main()