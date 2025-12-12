import json
import os

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
    

def save_output_json(response, agent_type):
    root_dir = load_root_path()
    outputs_dir = os.path.join(root_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    response_parsed = parse_json(response)
    task_desc = response_parsed.get("task_desc", "unnamed_task")
    task_dir = os.path.join(outputs_dir, task_desc)
    os.makedirs(task_dir, exist_ok=True)

    output_path = os.path.join(task_dir, f"{agent_type}_output.json")

    with open(output_path, "w") as f:
        json.dump(response_parsed, f, indent=2)

    return response_parsed



def save_output_json_orchestrator(response):
    root_dir = load_root_path()
    outputs_dir = os.path.join(root_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    response_parsed = parse_json(response)
    first_item = response_parsed[0]
    task_desc = first_item.get("task_desc", "unnamed_task")
    dir_orchestrator = os.path.join(outputs_dir, task_desc, "orchestrator")
    os.makedirs(dir_orchestrator, exist_ok=True)
    
    subtask_id = first_item.get("subtask_id", "unknown_subtask")
    output_path = os.path.join(dir_orchestrator, f"{subtask_id}_output.json")

    with open(output_path, "w") as f:
        json.dump(response_parsed, f, indent=2)

    return dir_orchestrator


def save_output_json_agents(response):
    root_dir = load_root_path()
    outputs_dir = os.path.join(root_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    response_parsed = parse_json(response)
    task_desc = response_parsed.get("task_desc", "unnamed_task")
    dir_work_agents = os.path.join(outputs_dir, task_desc, "work_agents")
    os.makedirs(dir_work_agents, exist_ok=True)
    
    subtask_id = response_parsed.get("subtask_id", "unknown_subtask")
    subtask_path = os.path.join(dir_work_agents, subtask_id)
    os.makedirs(subtask_path, exist_ok=True)

    agent_id = response_parsed.get("agent_id", "unknown_agent")
    output_path = os.path.join(subtask_path, f"{agent_id}_output.json")

    with open(output_path, "w") as f:
        json.dump(response_parsed, f, indent=2)

    return output_path