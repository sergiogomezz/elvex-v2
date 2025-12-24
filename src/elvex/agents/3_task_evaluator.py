import json
import os
from config.settings import AGENT_EVALUATOR_PROMPT
from src.elvex.utils.loader import load_prompt, save_output_json, load_root_path

# este tiene que poder volver atrás si devuelve un false y devolver contexto.

class TaskEvaluatorAgent:
    def __init__(self, client):
        self.client = client
        self.system_prompt = load_prompt(AGENT_EVALUATOR_PROMPT)

    def evaluate_tasks(self, divider_agent_result):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(divider_agent_result, indent=2)}        
        ]

        response = self.client.chat(messages)

        response_parsed = save_output_json(response, "evaluator")

        final_output_path = self.manage_final_tasks(response_parsed, divider_agent_result)
        
        return final_output_path


    def manage_final_tasks(self, response_parsed, divider_agent_result):
        is_valid = response_parsed.get("is_valid", False)
        task_desc = response_parsed.get("task_desc", "unnamed_task")
        root_path = load_root_path()
        output_dir = os.path.join(root_path, "outputs", task_desc)
        os.makedirs(output_dir, exist_ok=True)

        final_output_path = os.path.join(output_dir, "final_subtasks.json")

        if is_valid:
            with open(final_output_path, "w") as f:
                json.dump(divider_agent_result, f, indent=2)
        else:
            corrected_subtasks = response_parsed.get("corrected_subtasks")
            if corrected_subtasks:
                final_result = {
                    "task_desc": task_desc,
                    "subtasks": corrected_subtasks
                }
                with open(final_output_path, "w") as f:
                    json.dump(final_result, f, indent=2)

        return final_output_path