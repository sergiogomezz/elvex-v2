import json

from config.settings import AGENT_ORCHESTRATOR_PROMPT
from elvex.agents.contracts import OrchestratorPlan
from src.elvex.utils.loader import load_prompt, save_output_json_orchestrator, parse_json


class OrchestratorAgent:
    def __init__(self, client, task_id):
        self.client = client
        self.system_prompt = load_prompt(AGENT_ORCHESTRATOR_PROMPT)
        self.task_id = task_id

    def design_agents(self, subtask: dict):
        prompt = json.dumps({
            "task_desc": self.task_id,
            "subtask_id": subtask["id"],
            "title": subtask["title"],
            "description": subtask["description"]
        }, indent=2)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(messages)
        response_text = response.text if hasattr(response, "text") else response
        response_parsed = parse_json(response_text)
        OrchestratorPlan.model_validate(response_parsed)

        orchestrator_path = save_output_json_orchestrator(response_parsed)

        return orchestrator_path
