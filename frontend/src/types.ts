export type Provider = "openai" | "claude" | "ollama";
export type RunStatus = "queued" | "running" | "completed" | "failed";
export type EntityStatus = "idle" | "running" | "completed" | "failed";

export interface StudioEvent {
  type: string;
  entity_id: string;
  entity_type: string;
  title: string;
  status: EntityStatus;
  data: Record<string, unknown>;
  sequence: number;
  timestamp: string;
}

export interface StudioRun {
  run_id: string;
  prompt: string;
  provider: Provider;
  status: RunStatus;
  result?: string;
  trace_id?: string;
  error?: string;
  created_at: string;
  updated_at: string;
  events: StudioEvent[];
}

export interface Subtask {
  id: string;
  title: string;
  description: string;
  depends_on: string[];
}

export interface AgentSpec {
  task_desc?: string;
  subtask_id: string;
  agent_id: string;
  agent_type: string;
  objective: string;
  prompt: string;
}
