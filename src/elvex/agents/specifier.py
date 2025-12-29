from config.settings import AGENT_SPECIFIER_PROMPT
from src.elvex.utils.loader import load_prompt, parse_json

class TaskSpecifierAgent:
    def __init__(self, client):
        self.client = client
        self.system_prompt = load_prompt(AGENT_SPECIFIER_PROMPT)

    def specify_task(self, user_prompt):
        messages = [
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, system_prompt=self.system_prompt)
        response_text = response.text if hasattr(response, "text") else response
        parse_json(response_text)

        return response_text
