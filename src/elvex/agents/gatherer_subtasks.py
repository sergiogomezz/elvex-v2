from __future__ import annotations

import json
import os
from typing import Any

from elvex.utils.loader import get_latest_task_output_dir, load_prompt

SUBTASKS_GATHERER_PROMPT_PATH = "subtasks_gatherer_prompt.md"


class GathererSubtasks:
    """Second funnel: gathers each subtask-level result into final user output."""

    def __init__(self, client):
        self.client = client
        self.system_prompt = load_prompt(SUBTASKS_GATHERER_PROMPT_PATH)

    def gather_subtasks(self, task_desc: str, lf_parent=None) -> str:
        task_dir = get_latest_task_output_dir(task_desc)
        if not task_dir:
            raise ValueError(f"No output directory found for task '{task_desc}'.")

        gathered_dir = os.path.join(task_dir, "gatherer_subagents")
        if not os.path.isdir(gathered_dir):
            raise ValueError("No subtask-level gathered outputs found in 'gatherer_subagents'.")

        gathered_payloads: list[dict[str, Any]] = []
        for filename in sorted(os.listdir(gathered_dir)):
            if not filename.endswith(".json"):
                continue
            with open(os.path.join(gathered_dir, filename), "r") as f:
                gathered_payloads.append(json.load(f))

        if not gathered_payloads:
            raise ValueError("No valid subtask gatherer outputs found.")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(gathered_payloads, indent=2)},
        ]
        response = self.client.chat(
            messages=messages,
            lf_parent=lf_parent,
            observation_name="GathererSubtasks.chat",
            observation_metadata={"agent": "GathererSubtasks"},
        )
        response_text = response.text if hasattr(response, "text") else response

        final_output_path = os.path.join(task_dir, "final_answer.txt")
        with open(final_output_path, "w") as f:
            f.write(str(response_text).strip())

        return str(response_text).strip()
