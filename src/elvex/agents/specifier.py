from typing import Optional

from elvex.config.settings import AGENT_SPECIFIER_PROMPT
from elvex.llms.types import AgentConfig
from elvex.utils.loader import load_prompt, parse_json


class TaskSpecifierAgent:
    def __init__(self, client, agent_config: Optional[AgentConfig] = None):
        self.client = client
        self.agent_config = self._build_agent_config(agent_config)

    def specify_task(self, user_prompt: str) -> str:
        messages = [
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat(messages=messages, config=self.agent_config)
        response_text = response.text if hasattr(response, "text") else response
        parse_json(response_text)

        return response_text

    def _build_agent_config(self, agent_config: Optional[AgentConfig]) -> AgentConfig:
        base_config = AgentConfig(system_prompt=load_prompt(AGENT_SPECIFIER_PROMPT))
        if agent_config is None:
            return base_config
        overrides = agent_config.model_dump(exclude_none=True)
        return base_config.model_copy(update=overrides)
