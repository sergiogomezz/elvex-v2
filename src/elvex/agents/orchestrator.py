import json
from typing import Optional

from elvex.agents.contracts import OrchestratorPlan
from elvex.llms.types import AgentConfig
from elvex.utils.loader import load_prompt, parse_json, save_output_json_orchestrator

ORCHESTRATOR_PROMPT_PATH = "agent_orchestrator.md"


class OrchestratorAgent:
    def __init__(self, client, agent_config: Optional[AgentConfig] = None):
        self.client = client
        self.agent_config = self._build_agent_config(agent_config)

    def design_agents(self, task_desc: str, subtask: dict, lf_parent=None):
        prompt = json.dumps(
            {
                "task_desc": task_desc,
                "subtask_id": subtask["id"],
                "title": subtask["title"],
                "description": subtask["description"],
            },
            indent=2,
        )

        messages = [
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat(
            messages=messages,
            config=self.agent_config,
            lf_parent=lf_parent,
            observation_name="OrchestratorAgent.chat",
            observation_metadata={
                "agent": "OrchestratorAgent",
                "subtask_id": subtask["id"],
            },
        )
        response_text = response.text if hasattr(response, "text") else response
        response_parsed = parse_json(response_text)
        OrchestratorPlan.model_validate(response_parsed)

        orchestrator_path = save_output_json_orchestrator(response_parsed)

        return orchestrator_path

    def _build_agent_config(self, agent_config: Optional[AgentConfig]) -> AgentConfig:
        base_config = AgentConfig(system_prompt=load_prompt(ORCHESTRATOR_PROMPT_PATH))
        if agent_config is None:
            return base_config
        overrides = agent_config.model_dump(exclude_none=True)
        return base_config.model_copy(update=overrides)
