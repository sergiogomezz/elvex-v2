from elvex.agents.contracts import WorkerAgentOutput
from src.elvex.utils.loader import parse_json, save_output_json_agents


class BaseWorkingAgent:
    def __init__(self, client, task_id, agent_id, subtask_id, agent_type, objective, prompt, context):
        self.client = client
        self.task_id = task_id
        self.subtask_id = subtask_id
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.objective = objective
        self.prompt = prompt
        self.context = context

    def work(self):
        sys_prompt = f"""You are a {self.agent_type} agent. Your goal is to {self.prompt}.
            The context from previous subtasks that you MUST take into account is {self.context}.
            DO NOT include any explanation or comments. Output ONLY the JSON object.
            You must respond ALWAYS in strict valid JSON format with the following structure:

            {{
                "task_desc": "{self.task_id}",
                "subtask_id": "{self.subtask_id}",
                "agent_id": "{self.agent_id}",
                "answer": <your detailed answer here as a string or structured object>
            }}"""

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": self.objective}
        ]

        # Gestiona la persistencia. Si falla el formato de salida, reejecuta el agente.

        max_retries = 2
        for _ in range(max_retries + 1):
            response = self.client.chat(messages)
            response_text = response.text if hasattr(response, "text") else response
            try:
                response_parsed = parse_json(response_text)
                WorkerAgentOutput.model_validate(response_parsed)
                agents_path = save_output_json_agents(response_parsed)
                return agents_path
            except ValueError:
                continue
        return None
