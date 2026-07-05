import json
from typing import Optional, Union

from elvex.agents.contracts import TaskDividerOutput
from elvex.agents.retry import call_json_agent_with_retry
from elvex.llms.types import AgentConfig
from elvex.utils.loader import load_prompt, parse_json, save_output_json

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
    
        def _parse_and_validate(response_text: str):
            response_parsed = parse_json(response_text)
            TaskDividerOutput.model_validate(response_parsed)
            save_output_json(response_parsed, "divider")
            return response_parsed

        response_parsed, _ = call_json_agent_with_retry(
            client=self.client,
            messages=messages,
            parse_and_validate=_parse_and_validate,
            error_context="TaskDividerAgent",
            chat_kwargs={
                "config": self.agent_config,
                "lf_parent": lf_parent,
                "observation_name": "TaskDividerAgent.chat",
            },
            observation_metadata={
                "agent": "TaskDividerAgent",
                "workflow_stage": "divider",
                "has_evaluator_feedback": bool(evaluator_feedback),
            },
        )
        
        return response_parsed

    def _build_agent_config(self, agent_config: Optional[AgentConfig]) -> AgentConfig:
        base_config = AgentConfig(system_prompt=load_prompt(DIVIDER_PROMPT_PATH))
        if agent_config is None:
            return base_config
        overrides = agent_config.model_dump(exclude_none=True)
        return base_config.model_copy(update=overrides)
