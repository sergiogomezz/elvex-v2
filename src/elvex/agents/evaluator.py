import json
import os
from typing import Optional

from elvex.agents.contracts import TaskEvaluatorOutput
from elvex.agents.retry import call_json_agent_with_retry
from elvex.llms.types import AgentConfig
from elvex.utils.loader import (
    coerce_json,
    get_latest_task_output_dir,
    load_prompt,
    save_output_json,
)

EVALUATOR_PROMPT_PATH = "task_evaluator_prompt.md"


class TaskEvaluatorAgent:
    def __init__(self, client, agent_config: Optional[AgentConfig] = None):
        self.client = client
        self.agent_config = self._build_agent_config(agent_config)

    def evaluate_tasks(self, divider_agent_result, lf_parent=None):
        messages = [
            {"role": "user", "content": json.dumps(divider_agent_result, indent=2)}
        ]

        def _parse_and_validate(response_text: str):
            response_parsed = coerce_json(response_text)
            minimal_response = {
                "task_desc": response_parsed.get("task_desc", "unnamed_task"),
                "is_valid": response_parsed.get("is_valid", False),
                "correction_explanation": response_parsed.get("correction_explanation", ""),
            }
            TaskEvaluatorOutput.model_validate(minimal_response)
            return response_parsed, minimal_response

        parsed_pair, _ = call_json_agent_with_retry(
            client=self.client,
            messages=messages,
            parse_and_validate=_parse_and_validate,
            error_context="TaskEvaluatorAgent",
            chat_kwargs={
                "config": self.agent_config,
                "lf_parent": lf_parent,
                "observation_name": "TaskEvaluatorAgent.chat",
            },
            observation_metadata={
                "agent": "TaskEvaluatorAgent",
                "workflow_stage": "evaluator",
                "task_desc": divider_agent_result.get("task_desc"),
            },
        )
        response_parsed, minimal_response = parsed_pair
        save_output_json(minimal_response, "evaluator", use_latest_dir=True)

        final_output_path = self.manage_final_tasks(minimal_response, divider_agent_result)
        
        return response_parsed, final_output_path


    def _build_agent_config(self, agent_config: Optional[AgentConfig]) -> AgentConfig:
        base_config = AgentConfig(system_prompt=load_prompt(EVALUATOR_PROMPT_PATH))
        if agent_config is None:
            return base_config
        overrides = agent_config.model_dump(exclude_none=True)
        return base_config.model_copy(update=overrides)


    def manage_final_tasks(self, minimal_response, divider_agent_result):
        is_valid = minimal_response.get("is_valid", False)
        if not is_valid:
            return None

        task_desc = minimal_response.get("task_desc", "unnamed_task")
        task_dir = get_latest_task_output_dir(task_desc) or ""
        if not task_dir:
            return None

        final_output_path = os.path.join(task_dir, "final_subtasks.json")

        with open(final_output_path, "w") as f:
            json.dump(divider_agent_result, f, indent=2)

        return final_output_path
