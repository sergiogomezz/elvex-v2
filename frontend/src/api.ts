import type { Provider, StudioRun } from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function parseResponse(response: Response): Promise<StudioRun> {
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? "Elvex API is not available");
  }
  return response.json();
}

export async function createStudioRun(
  prompt: string,
  provider: Provider,
): Promise<StudioRun> {
  const response = await fetch(`${API_BASE}/studio/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, provider }),
  });
  return parseResponse(response);
}

export async function getStudioRun(runId: string): Promise<StudioRun> {
  const response = await fetch(`${API_BASE}/studio/runs/${runId}`);
  return parseResponse(response);
}
