import os
from src.elvex.utils.loader import load_root_path

# General Info
PROJECT_NAME = "TFM_Agentic_AI"

# Model Settings
USE_LOCAL_MODEL = True

# For ollama client
LOCAL_MODEL_NAME = "gpt-oss:20b"

# Improvement: select a different model for each agent.
    # Mistral 32k context but smaller model size.
    # Ollama3 8k context but larger model size.

# For OpenAI
OPENAI_MODEL_NAME = "gpt-4o-mini"

# Agents settings
ENABLE_DYNAMIC_AGENT_GENERATOR = True
MAX_AGENTS = 10

# Paths
ROOT_DIR = load_root_path()
AGENTS_DIR = os.path.join(ROOT_DIR, "agents")
PROMPTS_DIR = os.path.join(ROOT_DIR, "prompts")

# Prompts
AGENT_SPECIFIER_PROMPT = "task_specifier_prompt.txt"
AGENT_DIVIDER_PROMPT = "task_divider_prompt.txt"
AGENT_EVALUATOR_PROMPT = "task_evaluator_prompt.txt"
AGENT_ORCHESTRATOR_PROMPT = "agent_orchestrator.txt"
AGENT_SUBTASK_GATHERER = "subtasks_gatherer_prompt.txt"