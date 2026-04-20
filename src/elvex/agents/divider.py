import json
from typing import Optional, Union

from elvex.agents.contracts import TaskDividerOutput
from elvex.llms.types import AgentConfig
from elvex.utils.loader import load_prompt, save_output_json

DIVIDER_PROMPT_PATH = "task_divider_prompt.md"


class TaskDividerAgent:
    def __init__(self, client, agent_config: Optional[AgentConfig] = None):
        self.client = client
        self.agent_config = self._build_agent_config(agent_config)

    def divide_tasks(self, specifier_agent_result, evaluator_feedback: Optional[Union[str, dict]] = None, lf_parent=None):
        messages = [
            {"role": "user", "content": specifier_agent_result}
        ]
        
        if evaluator_feedback:
            feedback_text = (
                evaluator_feedback
                if isinstance(evaluator_feedback, str)
                else json.dumps(evaluator_feedback, indent=2)
            )
            messages.append({"role": "user", "content": f"Evaluator feedback:\n{feedback_text}"})
    
        response = self.client.chat(
            messages=messages,
            config=self.agent_config,
            lf_parent=lf_parent,
            observation_name="TaskDividerAgent.chat",
            observation_metadata={
                "agent": "TaskDividerAgent",
                "has_evaluator_feedback": bool(evaluator_feedback),
            },
        )
        response_text = response.text if hasattr(response, "text") else response

        response_parsed = save_output_json(response_text, "divider")
        TaskDividerOutput.model_validate(response_parsed)
        
        return response_parsed

    def _build_agent_config(self, agent_config: Optional[AgentConfig]) -> AgentConfig:
        base_config = AgentConfig(system_prompt=load_prompt(DIVIDER_PROMPT_PATH))
        if agent_config is None:
            return base_config
        overrides = agent_config.model_dump(exclude_none=True)
        return base_config.model_copy(update=overrides)
