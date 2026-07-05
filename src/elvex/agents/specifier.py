from typing import Optional

from elvex.agents.contracts import TaskSpecifierOutput
from elvex.agents.retry import call_json_agent_with_retry
from elvex.llms.types import AgentConfig
from elvex.utils.loader import load_prompt, parse_json

SPECIFIER_PROMPT_PATH = "task_specifier_prompt.md"


class TaskSpecifierAgent:
    def __init__(self, client, agent_config: Optional[AgentConfig] = None):
        self.client = client
        self.agent_config = self._build_agent_config(agent_config)

    def specify_task(self, user_prompt: str, lf_parent=None) -> str:
        messages = [
            {"role": "user", "content": user_prompt}
        ]

        def _parse_and_validate(response_text: str):
            response_parsed = parse_json(response_text)
            TaskSpecifierOutput.model_validate(response_parsed)
            return response_parsed

        _, response_text = call_json_agent_with_retry(
            client=self.client,
            messages=messages,
            parse_and_validate=_parse_and_validate,
            error_context="TaskSpecifierAgent",
            chat_kwargs={
                "config": self.agent_config,
                "lf_parent": lf_parent,
                "observation_name": "TaskSpecifierAgent.chat",
            },
            observation_metadata={
                "agent": "TaskSpecifierAgent",
                "workflow_stage": "specifier",
            },
        )
        return response_text

    def _build_agent_config(self, agent_config: Optional[AgentConfig]) -> AgentConfig:
        base_config = AgentConfig(system_prompt=load_prompt(SPECIFIER_PROMPT_PATH))
        if agent_config is None:
            return base_config
        overrides = agent_config.model_dump(exclude_none=True)
        return base_config.model_copy(update=overrides)
