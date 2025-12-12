import json
import os
from config.settings import AGENT_SPECIFIER_PROMPT
from src.elvex.utils.loader import load_prompt, parse_json

class TaskSpecifierAgent:
    def __init__(self, client):
        self.client = client
        self.system_prompt = load_prompt(AGENT_SPECIFIER_PROMPT)

    def specify_task(self, user_prompt):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat(messages)
        
        response_parsed = parse_json(response)


        return response