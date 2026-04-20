from __future__ import annotations

import json
import os
from typing import Any

from elvex.utils.loader import get_latest_task_output_dir, load_prompt, parse_json

SUBAGENTS_GATHERER_PROMPT_PATH = "subagents_gatherer_prompt.md"


class GathererSubagents:
    """First funnel: gathers multiple worker-agent outputs for a single subtask."""

    def __init__(self, client):
        self.client = client
        self.system_prompt = load_prompt(SUBAGENTS_GATHERER_PROMPT_PATH)

    def gather_subtask(self, task_desc: str, subtask_id: str, lf_parent=None) -> str:
        task_dir = get_latest_task_output_dir(task_desc)
        if not task_dir:
            raise ValueError(f"No output directory found for task '{task_desc}'.")

        subtask_dir = os.path.join(task_dir, "work_agents", subtask_id)
        if not os.path.isdir(subtask_dir):
            raise ValueError(f"No worker outputs found for subtask '{subtask_id}'.")

        worker_payloads: list[dict[str, Any]] = []
        for filename in sorted(os.listdir(subtask_dir)):
            if not filename.endswith(".json"):
                continue
            with open(os.path.join(subtask_dir, filename), "r") as f:
                worker_payloads.append(json.load(f))

        if not worker_payloads:
            raise ValueError(f"No worker JSON outputs found for subtask '{subtask_id}'.")

        user_message = json.dumps(
            {
                "task_desc": task_desc,
                "subtask_id": subtask_id,
                "worker_outputs": worker_payloads,
            },
            indent=2,
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = self.client.chat(
            messages=messages,
            lf_parent=lf_parent,
            observation_name="GathererSubagents.chat",
            observation_metadata={
                "agent": "GathererSubagents",
                "subtask_id": subtask_id,
            },
        )
        response_text = response.text if hasattr(response, "text") else response
        response_parsed = parse_json(response_text)

        normalized = {
            "task_desc": response_parsed.get("task_desc", task_desc),
            "subtask_id": response_parsed.get("subtask_id", subtask_id),
            "answer": response_parsed.get("answer", ""),
        }

        output_dir = os.path.join(task_dir, "gatherer_subagents")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{subtask_id}_output.json")
        with open(output_path, "w") as f:
            json.dump(normalized, f, indent=2)

        return output_path
