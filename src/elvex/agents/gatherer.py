# This agent serves to gather the results of the different agents
from config.settings import AGENT_SUBTASK_GATHERER
from src.elvex.utils.loader import load_prompt, parse_json, load_root_path

import os
import json


class SubtasksGatherer():
    def __init__(self, client):
        self.client = client
        self.system_prompt = load_prompt(AGENT_SUBTASK_GATHERER)

    def gather_subtasks(self, task_id):
        user_message = self.get_user_subtasks(task_id)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]
        response = self.client.chat(messages)
        response_text = response.text if hasattr(response, "text") else response
        return response_text


    def get_user_subtasks(self, task_id):
        def json_to_text(data, indent=0):
            lines = []
            prefix = "  " * indent + "- "
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        lines.append("  " * indent + f"{key}:")
                        lines.extend(json_to_text(value, indent + 1))
                    else:
                        lines.append(prefix + f"{key}: {value}")
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, (dict, list)):
                        lines.append(prefix.rstrip() + ":")
                        lines.extend(json_to_text(item, indent + 1))
                    else:
                        lines.append(prefix + str(item))
            else:
                lines.append(prefix + str(data))
            return lines

        root_path = load_root_path()
        base_path = f"{root_path}/outputs/{task_id}/work_agents"
        messages = []
        for agent_folder in sorted(os.listdir(base_path)):
            agent_path = os.path.join(base_path, agent_folder)
            if os.path.isdir(agent_path):
                json_files = [f for f in os.listdir(agent_path) if f.endswith(".json")]
                if json_files:
                    with open(os.path.join(agent_path, json_files[0]), "r") as f:
                        data = json.load(f)
                        answer = data.get("answer", "")
                        if isinstance(answer, dict) or isinstance(answer, list):
                            formatted_answer = "\n".join(json_to_text(answer))
                        else:
                            formatted_answer = str(answer)
                        messages.append(f"Subtask {agent_folder}:\n{formatted_answer}")

        return "\n\n".join(messages)
