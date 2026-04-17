from elvex.agents.contracts import WorkerAgentOutput
from elvex.tools.local_tools import get_agent_tool_definitions, get_agent_tool_executor
from elvex.utils.loader import parse_json, save_output_json_agents


class BaseWorkingAgent:
    def __init__(
        self,
        client,
        task_id,
        agent_id,
        subtask_id,
        agent_type,
        objective,
        prompt,
        context,
        allowed_tools=None,
    ):
        self.client = client
        self.task_id = task_id
        self.subtask_id = subtask_id
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.objective = objective
        self.prompt = prompt
        self.context = context
        self.allowed_tools = allowed_tools

    def work(self):
        sys_prompt = f"""You are a {self.agent_type} worker agent executing ONE subtask in a larger task graph.
Your job is to complete only this subtask's deliverable with high-quality, detailed output.

Subtask context (do not ignore):
{self.context}

System instructions for you:
{self.prompt}

Rules:
- Focus only on this subtask. Do NOT summarize other subtasks or produce the final user-facing response.
- Use the provided context if it is relevant to this subtask's objective.
- If assumptions are required, state them inside the "answer" field.
- Do NOT include any explanations or commentary outside the JSON.
- You must respond in strict valid JSON with the exact structure below.

Required JSON format:
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


        tool_definitions = get_agent_tool_definitions(
            agent_type=self.agent_type,
            agent_id=self.agent_id,
            explicit_allowlist=self.allowed_tools,
        )
        tool_executor = get_agent_tool_executor(
            agent_type=self.agent_type,
            agent_id=self.agent_id,
            explicit_allowlist=self.allowed_tools,
        )

        max_retries = 2
        for _ in range(max_retries + 1):
            response = self.client.chat(
                messages,
                tools=tool_definitions or None,
                tool_executor=tool_executor,
            )
            response_text = response.text if hasattr(response, "text") else response
            try:
                response_parsed = parse_json(response_text)
                WorkerAgentOutput.model_validate(response_parsed)
                agents_path = save_output_json_agents(response_parsed)
                return agents_path
            except ValueError:
                continue
        return None
