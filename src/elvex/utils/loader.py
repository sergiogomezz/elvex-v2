import json
import os
import re
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Generator

SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_CURRENT_RUN_OUTPUT_DIR: ContextVar[str | None] = ContextVar("current_run_output_dir", default=None)


def _validate_identifier(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string, got: {type(value)}")
    if not SAFE_IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"Invalid {field_name}: '{value}'. Allowed pattern: {SAFE_IDENTIFIER_PATTERN.pattern}"
        )
    return value


def _safe_join(base_dir: str, *parts: str) -> str:
    base_real = os.path.realpath(base_dir)
    candidate = os.path.realpath(os.path.join(base_dir, *parts))
    if not (candidate == base_real or candidate.startswith(base_real + os.sep)):
        raise ValueError(f"Unsafe path resolution detected: {candidate}")
    return candidate


def load_json(path: str) -> Any:
    with open(path, "r") as f:
        result = json.load(f)
    return result


def load_keys(path: str = "keys.json") -> dict:
    with open(path, "r") as f:
        return json.load(f)


def get_api_key(keys: dict) -> str:
    api_key = keys.get("openai", {}).get("api_key")

    if not api_key:
        raise ValueError("API key not found in keys.json")

    return api_key


def load_root_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    return root_dir


def load_project_root_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_dir, "..", "..", ".."))


def load_prompt(prompt_name: str) -> str:
    root_dir = load_root_path()
    prompts_dir = os.path.join(root_dir, "prompts")
    prompt_path = os.path.join(prompts_dir, prompt_name)
    with open(prompt_path, "r") as f:
        return f.read()


def parse_json(response: str) -> Any:
    if not isinstance(response, str):
        raise TypeError(f"Expected string response, got: {type(response)}")

    text = response.strip()
    if not text:
        raise ValueError("Could not parse the response as JSON. Error: empty response from model.")

    try:
        parsed_output = json.loads(text)
        return parsed_output
    except json.JSONDecodeError as e:
        # Common case: the model wraps JSON in markdown fences.
        fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced_match:
            fenced_text = fenced_match.group(1).strip()
            if fenced_text:
                try:
                    return json.loads(fenced_text)
                except json.JSONDecodeError:
                    pass

        # Fallback: extract first object/array from surrounding text.
        first_obj = text.find("{")
        first_arr = text.find("[")
        starts = [idx for idx in (first_obj, first_arr) if idx != -1]
        if starts:
            start = min(starts)
            candidate = text[start:]
            try:
                parsed_output, _ = json.JSONDecoder().raw_decode(candidate)
                return parsed_output
            except json.JSONDecodeError:
                pass

        preview = text[:200].replace("\n", "\\n")
        raise ValueError(f"Could not parse the response as JSON. Error: {e}. Response preview: {preview}")


def coerce_json(response: Any) -> dict | list:
    if isinstance(response, (dict, list)):
        return response
    if isinstance(response, str):
        return parse_json(response)
    raise TypeError(f"Unsupported JSON payload type: {type(response)}")


def coerce_json_object(response: Any) -> dict:
    response_parsed = coerce_json(response)
    if not isinstance(response_parsed, dict):
        raise TypeError(f"Expected JSON object, got: {type(response_parsed)}")
    return response_parsed


def coerce_json_list(response: Any) -> list:
    response_parsed = coerce_json(response)
    if not isinstance(response_parsed, list):
        raise TypeError(f"Expected JSON list, got: {type(response_parsed)}")
    return response_parsed


def _runs_outputs_base_dir() -> str:
    return os.path.join(load_project_root_path(), "outputs", "runs")


def get_run_output_dir(run_id: str) -> str:
    run_id = _validate_identifier(run_id, "run_id")
    return _safe_join(_runs_outputs_base_dir(), run_id)


@contextmanager
def workflow_output_context(run_id: str) -> Generator[str, None, None]:
    output_dir = get_run_output_dir(run_id)
    os.makedirs(output_dir, exist_ok=True)
    token = _CURRENT_RUN_OUTPUT_DIR.set(output_dir)
    try:
        yield output_dir
    finally:
        _CURRENT_RUN_OUTPUT_DIR.reset(token)


def get_current_run_output_dir() -> str | None:
    return _CURRENT_RUN_OUTPUT_DIR.get()


def _task_outputs_base_dir(_task_desc: str) -> str:
    current_run_output_dir = get_current_run_output_dir()
    if current_run_output_dir is not None:
        return current_run_output_dir
    return _runs_outputs_base_dir()


def _timestamp_dir_name() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_task_output_dir(task_desc: str) -> str:
    task_desc = _validate_identifier(task_desc, "task_desc")
    current_run_output_dir = get_current_run_output_dir()
    if current_run_output_dir is not None:
        os.makedirs(current_run_output_dir, exist_ok=True)
        return current_run_output_dir

    base_dir = _task_outputs_base_dir(task_desc)
    os.makedirs(base_dir, exist_ok=True)

    task_dir = _safe_join(base_dir, f"{_timestamp_dir_name()}_{task_desc}")
    os.makedirs(task_dir, exist_ok=True)
    return task_dir


def get_latest_task_output_dir(task_desc: str) -> str | None:
    task_desc = _validate_identifier(task_desc, "task_desc")
    current_run_output_dir = get_current_run_output_dir()
    if current_run_output_dir is not None:
        return current_run_output_dir if os.path.isdir(current_run_output_dir) else None

    base_dir = _task_outputs_base_dir(task_desc)
    if not os.path.isdir(base_dir):
        return None

    candidates = [
        entry for entry in os.listdir(base_dir)
        if entry.endswith(f"_{task_desc}") and os.path.isdir(os.path.join(base_dir, entry))
    ]
    if not candidates:
        return None

    latest = max(candidates)
    return os.path.join(base_dir, latest)


def save_output_json(response: Any, agent_type: str, use_latest_dir: bool = False) -> dict:
    response_parsed = coerce_json_object(response)
    task_desc = _validate_identifier(response_parsed.get("task_desc", "unnamed_task"), "task_desc")
    agent_type = _validate_identifier(agent_type, "agent_type")
    if use_latest_dir:
        task_dir = get_latest_task_output_dir(task_desc) or create_task_output_dir(task_desc)
    else:
        task_dir = create_task_output_dir(task_desc)

    output_path = _safe_join(task_dir, f"{agent_type}_output.json")

    with open(output_path, "w") as f:
        json.dump(response_parsed, f, indent=2)

    return response_parsed


def save_output_json_orchestrator(response: Any) -> str:
    response_parsed = coerce_json_list(response)
    first_item = response_parsed[0]
    if not isinstance(first_item, dict):
        raise TypeError(f"Expected orchestrator item to be a JSON object, got: {type(first_item)}")
    task_desc = _validate_identifier(first_item.get("task_desc", "unnamed_task"), "task_desc")
    task_dir = get_latest_task_output_dir(task_desc) or create_task_output_dir(task_desc)
    dir_orchestrator = _safe_join(task_dir, "orchestrator")
    os.makedirs(dir_orchestrator, exist_ok=True)

    subtask_id = _validate_identifier(first_item.get("subtask_id", "unknown_subtask"), "subtask_id")
    output_path = _safe_join(dir_orchestrator, f"{subtask_id}_output.json")

    with open(output_path, "w") as f:
        json.dump(response_parsed, f, indent=2)

    return dir_orchestrator


def save_output_json_agents(response: Any) -> str:
    response_parsed = coerce_json_object(response)
    task_desc = _validate_identifier(response_parsed.get("task_desc", "unnamed_task"), "task_desc")
    task_dir = get_latest_task_output_dir(task_desc) or create_task_output_dir(task_desc)
    dir_work_agents = _safe_join(task_dir, "work_agents")
    os.makedirs(dir_work_agents, exist_ok=True)

    subtask_id = _validate_identifier(response_parsed.get("subtask_id", "unknown_subtask"), "subtask_id")
    subtask_path = _safe_join(dir_work_agents, subtask_id)
    os.makedirs(subtask_path, exist_ok=True)

    agent_id = _validate_identifier(response_parsed.get("agent_id", "unknown_agent"), "agent_id")
    output_path = _safe_join(subtask_path, f"{agent_id}_output.json")

    with open(output_path, "w") as f:
        json.dump(response_parsed, f, indent=2)

    return output_path
