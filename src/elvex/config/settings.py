import os
from src.elvex.utils.loader import load_root_path

# General Info
PROJECT_NAME = "elvex-v2"

# Model Settings (ollama, claude, openai)
PROVIDER_USED = "openai"
MODEL_NAME = "gpt-4o-mini"

# Improvement: select a different model for each agent.

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