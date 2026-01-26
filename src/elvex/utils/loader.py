import json
import os
from datetime import datetime

def load_json(path):
    with open(path, "r") as f:
        result = json.load(f)
    return result

def load_keys(path='keys.json'):
    with open(path, 'r') as f:
        return json.load(f)
    

def get_api_key(keys):
    api_key = keys.get('openai', {}).get('api_key')

    if not api_key:
        raise ValueError("API key not found in keys.json")
    
    return api_key


def load_root_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    return root_dir


def load_prompt(prompt_name):
    root_dir = load_root_path()
    prompts_dir = os.path.join(root_dir, "prompts")
    prompt_path = os.path.join(prompts_dir, prompt_name)
    with open(prompt_path, 'r') as f:
        return f.read()
    

def parse_json(response):
    try:
        parsed_output = json.loads(response.strip())
        return parsed_output
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse the response as JSON. Error: {e}")


def coerce_json(response):
    if isinstance(response, (dict, list)):
        return response
    if isinstance(response, str):
        return parse_json(response)
    raise TypeError(f"Unsupported JSON payload type: {type(response)}")
    

def _task_outputs_base_dir(task_desc):
    root_dir = load_root_path()
    return os.path.join(root_dir, "outputs")


def _timestamp_dir_name():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_task_output_dir(task_desc):
    base_dir = _task_outputs_base_dir(task_desc)
    os.makedirs(base_dir, exist_ok=True)

    task_dir = os.path.join(base_dir, f"{_timestamp_dir_name()}_{task_desc}")
    os.makedirs(task_dir, exist_ok=True)
    return task_dir


def get_latest_task_output_dir(task_desc):
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


def save_output_json(response, agent_type, use_latest_dir: bool = False):
    response_parsed = coerce_json(response)
    task_desc = response_parsed.get("task_desc", "unnamed_task")
    if use_latest_dir:
        task_dir = get_latest_task_output_dir(task_desc) or create_task_output_dir(task_desc)
    else:
        task_dir = create_task_output_dir(task_desc)

    output_path = os.path.join(task_dir, f"{agent_type}_output.json")

    with open(output_path, "w") as f:
        json.dump(response_parsed, f, indent=2)

    return response_parsed


def save_output_json_orchestrator(response):
    response_parsed = coerce_json(response)
    first_item = response_parsed[0]
    task_desc = first_item.get("task_desc", "unnamed_task")
    task_dir = get_latest_task_output_dir(task_desc) or create_task_output_dir(task_desc)
    dir_orchestrator = os.path.join(task_dir, "orchestrator")
    os.makedirs(dir_orchestrator, exist_ok=True)
    
    subtask_id = first_item.get("subtask_id", "unknown_subtask")
    output_path = os.path.join(dir_orchestrator, f"{subtask_id}_output.json")

    with open(output_path, "w") as f:
        json.dump(response_parsed, f, indent=2)

    return dir_orchestrator


def save_output_json_agents(response):
    response_parsed = coerce_json(response)
    task_desc = response_parsed.get("task_desc", "unnamed_task")
    task_dir = get_latest_task_output_dir(task_desc) or create_task_output_dir(task_desc)
    dir_work_agents = os.path.join(task_dir, "work_agents")
    os.makedirs(dir_work_agents, exist_ok=True)
    
    subtask_id = response_parsed.get("subtask_id", "unknown_subtask")
    subtask_path = os.path.join(dir_work_agents, subtask_id)
    os.makedirs(subtask_path, exist_ok=True)

    agent_id = response_parsed.get("agent_id", "unknown_agent")
    output_path = os.path.join(subtask_path, f"{agent_id}_output.json")

    with open(output_path, "w") as f:
        json.dump(response_parsed, f, indent=2)

    return output_path
