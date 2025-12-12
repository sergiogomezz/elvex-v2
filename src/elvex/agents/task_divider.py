from config.settings import AGENT_DIVIDER_PROMPT
from src.elvex.utils.loader import load_prompt, save_output_json


class TaskDividerAgent:
    def __init__(self, client):
        self.client = client
        self.system_prompt = load_prompt(AGENT_DIVIDER_PROMPT)

    def divide_tasks(self, specifier_agent_result):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": specifier_agent_result}
        ]

        response = self.client.chat(messages)

        response_parsed = save_output_json(response, "divider")

        return response_parsed