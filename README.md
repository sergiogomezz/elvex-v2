# Elvex v2

## Project Summary
Elvex v2 is a multi-agent orchestration pipeline that turns a user prompt into a final natural-language answer through staged planning, decomposition, execution, and aggregation. The system first specifies the task, divides it into subtasks, validates the split, and then orchestrates specialized worker agents per subtask. Each stage is persisted under `src/elvex/outputs/` so the workflow remains inspectable and reproducible.

The execution model uses a double-funnel architecture: worker outputs are first consolidated per subtask (`gatherer_subagents`), then those subtask-level outputs are combined into a final user-facing response (`gatherer_subtasks`). This keeps decomposition and execution granular while preserving a coherent final output.

```mermaid
flowchart TD
    A[User Prompt] --> B[TaskSpecifierAgent]
    B --> C[TaskDividerAgent]
    C --> D[TaskEvaluatorAgent]
    D -->|valid| E[OrchestratorAgent per Subtask]
    D -->|invalid feedback loop| C
    E --> F[Worker Agents per Subtask]
    F --> G[GathererSubagents<br/>first funnel]
    G --> H[GathererSubtasks<br/>second funnel]
    H --> I[Final Answer]
```

## Run (Short Path)
1. Create and activate a virtual environment with `uv`:
```bash
uv venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
uv pip install -e .
```

3. Configure environment variables (copy example and edit values):
```bash
cp .env.example .env
```
Required keys:
- `PROVIDER_USED` (`openai`, `ollama`, or `claude`)
- `OPENAI_API_KEY` (if using OpenAI)
- `OPENAI_MODEL` (for OpenAI runs)

4. Run the local workflow:
```bash
python scripts/main_local.py
```
or
```bash
python scripts/main_local.py --prompt "Plan a 7-day trip to Malaysia"
```
