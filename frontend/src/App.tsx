import { FormEvent, useEffect, useMemo, useState } from "react";
import { createStudioRun, getStudioRun } from "./api";
import type {
  AgentSpec,
  EntityStatus,
  Provider,
  StudioEvent,
  StudioRun,
  Subtask,
} from "./types";

const PIPELINE = [
  { id: "specifier", type: "specifier", title: "Specifier" },
  { id: "divider", type: "divider", title: "Divider" },
  { id: "evaluator", type: "evaluator", title: "Evaluator" },
  { id: "final_gatherer", type: "final_gatherer", title: "Final gatherer" },
];

const AVATARS: Record<string, string> = {
  workflow: "⚡",
  specifier: "🧭",
  divider: "🧩",
  evaluator: "🛡️",
  task_graph: "🗺️",
  orchestrator: "🎛️",
  gatherer: "🧵",
  final_gatherer: "✨",
  researcher: "🔎",
  research: "🔎",
  writer: "✍️",
  analyst: "📊",
  developer: "💻",
  coder: "💻",
  planner: "🗓️",
  worker: "🤖",
};

function avatarFor(type: string) {
  const key = type.toLowerCase();
  return (
    AVATARS[key] ??
    Object.entries(AVATARS).find(([name]) => key.includes(name))?.[1] ??
    "🤖"
  );
}

function pretty(value: unknown) {
  if (typeof value === "string") {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }
  return JSON.stringify(value, null, 2);
}

function latestEvent(events: StudioEvent[], entityId: string) {
  return [...events].reverse().find((event) => event.entity_id === entityId);
}

function AgentAvatar({
  type,
  status,
  size = "large",
}: {
  type: string;
  status: EntityStatus;
  size?: "small" | "large";
}) {
  return (
    <span className={`agent-avatar avatar-${size} status-${status}`} aria-hidden="true">
      <span>{avatarFor(type)}</span>
      <i />
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const labels: Record<string, string> = {
    queued: "Queued",
    running: "Working",
    completed: "Complete",
    failed: "Needs attention",
    idle: "Waiting",
  };
  return (
    <span className={`status-badge status-${status}`}>
      <i />
      {labels[status] ?? status}
    </span>
  );
}

function StageCard({
  item,
  event,
  onClick,
}: {
  item: { id: string; type: string; title: string };
  event?: StudioEvent;
  onClick: () => void;
}) {
  const status = event?.status ?? "idle";
  return (
    <button
      className={`stage-card status-${status}`}
      onClick={onClick}
      disabled={!event}
      aria-label={`Inspect ${item.title}`}
    >
      <AgentAvatar type={item.type} status={status} />
      <span className="stage-copy">
        <strong>{item.title}</strong>
        <small>{status === "running" ? "Thinking now…" : status}</small>
      </span>
    </button>
  );
}

export default function App() {
  const [prompt, setPrompt] = useState(
    "Create a practical three-day launch plan for an independent AI product.",
  );
  const [provider, setProvider] = useState<Provider>("openai");
  const [run, setRun] = useState<StudioRun | null>(null);
  const [selected, setSelected] = useState<StudioEvent | null>(null);
  const [requestError, setRequestError] = useState("");

  useEffect(() => {
    if (!run || !["queued", "running"].includes(run.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const nextRun = await getStudioRun(run.run_id);
        setRun(nextRun);
      } catch (error) {
        setRequestError(error instanceof Error ? error.message : "Could not refresh run");
      }
    }, 800);
    return () => window.clearInterval(timer);
  }, [run?.run_id, run?.status]);

  const subtasks = useMemo<Subtask[]>(() => {
    const event = run?.events.find((item) => item.type === "subtasks_created");
    return (event?.data.subtasks as Subtask[] | undefined) ?? [];
  }, [run?.events]);

  const agentsBySubtask = useMemo(() => {
    const groups: Record<string, AgentSpec[]> = {};
    for (const event of run?.events ?? []) {
      if (event.type !== "agents_created") continue;
      const subtaskId = event.data.subtask_id as string;
      groups[subtaskId] = (event.data.agents as AgentSpec[]) ?? [];
    }
    return groups;
  }, [run?.events]);

  async function startRun(event: FormEvent) {
    event.preventDefault();
    if (!prompt.trim()) return;
    setRequestError("");
    setSelected(null);
    try {
      setRun(await createStudioRun(prompt.trim(), provider));
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : "Could not start Elvex");
    }
  }

  function selectEntity(entityId: string) {
    const event = latestEvent(run?.events ?? [], entityId);
    if (event) setSelected(event);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Elvex Studio home">
          <span className="brand-mark">E</span>
          <span>
            <strong>Elvex</strong>
            <small>STUDIO</small>
          </span>
        </a>
        <div className="run-meta">
          {run ? (
            <>
              <span className="run-id">{run.run_id.split("_").slice(-1)}</span>
              <StatusBadge status={run.status} />
            </>
          ) : (
            <span className="ready-label"><i /> System ready</span>
          )}
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="eyebrow"><span>●</span> MULTI-AGENT WORKBENCH</div>
          <h1>Watch ideas become<br /><em>coordinated work.</em></h1>
          <p>
            Give Elvex a goal. Follow every decision, subtask and specialist as the
            team builds your answer.
          </p>

          <form className="composer" onSubmit={startRun}>
            <label htmlFor="task-prompt">What should the team work on?</label>
            <textarea
              id="task-prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={3}
              disabled={run?.status === "running" || run?.status === "queued"}
            />
            <div className="composer-footer">
              <label className="provider-control">
                <span>Provider</span>
                <select
                  value={provider}
                  onChange={(event) => setProvider(event.target.value as Provider)}
                  disabled={run?.status === "running" || run?.status === "queued"}
                >
                  <option value="openai">OpenAI</option>
                  <option value="claude">Anthropic</option>
                  <option value="ollama">Ollama · local</option>
                </select>
              </label>
              <button
                className="run-button"
                type="submit"
                disabled={run?.status === "running" || run?.status === "queued"}
              >
                <span>{run?.status === "running" ? "Team working" : "Run Elvex"}</span>
                <b>→</b>
              </button>
            </div>
          </form>
          {requestError && <p className="error-banner">{requestError}</p>}
        </section>

        <section className="workspace">
          <div className="section-heading">
            <div>
              <span className="section-number">01</span>
              <h2>Workflow pulse</h2>
            </div>
            <p>Click any active teammate to inspect its work.</p>
          </div>

          <div className="pipeline">
            {PIPELINE.slice(0, 3).map((item, index) => (
              <div className="pipeline-step" key={item.id}>
                <StageCard
                  item={item}
                  event={latestEvent(run?.events ?? [], item.id)}
                  onClick={() => selectEntity(item.id)}
                />
                {index < 2 && <span className="connector">→</span>}
              </div>
            ))}
          </div>

          <div className="section-heading task-heading">
            <div>
              <span className="section-number">02</span>
              <h2>Specialist teams</h2>
            </div>
            <p>{subtasks.length ? `${subtasks.length} subtasks generated` : "Waiting for a plan"}</p>
          </div>

          {subtasks.length ? (
            <div className="subtask-grid">
              {subtasks.map((subtask, index) => {
                const agents = agentsBySubtask[subtask.id] ?? [];
                return (
                  <article className="subtask-card" key={subtask.id}>
                    <div className="subtask-topline">
                      <span>{String(index + 1).padStart(2, "0")}</span>
                      <small>{subtask.depends_on.length ? `After ${subtask.depends_on.join(", ")}` : "Starts first"}</small>
                    </div>
                    <h3>{subtask.title}</h3>
                    <p>{subtask.description}</p>
                    <div className="agent-row">
                      {agents.length ? agents.map((agent) => {
                        const entityId = `worker:${subtask.id}:${agent.agent_id}`;
                        const event = latestEvent(run?.events ?? [], entityId);
                        const status = event?.status ?? "idle";
                        return (
                          <button
                            className="mini-agent"
                            key={agent.agent_id}
                            onClick={() => selectEntity(entityId)}
                            disabled={!event}
                            title={`Inspect ${agent.agent_type}`}
                          >
                            <AgentAvatar type={agent.agent_type} status={status} size="small" />
                            <span>{agent.agent_type}</span>
                          </button>
                        );
                      }) : (
                        <span className="agents-pending">Orchestrator is assembling the team…</span>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-avatars">
                <AgentAvatar type="researcher" status="idle" />
                <AgentAvatar type="writer" status="idle" />
                <AgentAvatar type="analyst" status="idle" />
              </div>
              <h3>Your team will gather here</h3>
              <p>Start a run and Elvex will create the right specialists for each subtask.</p>
            </div>
          )}

          {(run?.result || run?.error) && (
            <section className={`final-answer ${run.error ? "has-error" : ""}`}>
              <span className="section-number">03</span>
              <div>
                <small>{run.error ? "RUN STOPPED" : "FINAL DELIVERY"}</small>
                <h2>{run.error ? "Elvex needs attention" : "The team has delivered."}</h2>
                <p>{run.error ?? run.result}</p>
              </div>
            </section>
          )}
        </section>
      </main>

      {selected && (
        <div className="drawer-backdrop" onClick={() => setSelected(null)}>
          <aside
            className="detail-drawer"
            onClick={(event) => event.stopPropagation()}
            aria-label="Agent output detail"
          >
            <button className="drawer-close" onClick={() => setSelected(null)} aria-label="Close">
              ×
            </button>
            <AgentAvatar type={selected.entity_type} status={selected.status} />
            <span className="drawer-kicker">{selected.entity_type.replaceAll("_", " ")}</span>
            <h2>{selected.title}</h2>
            <StatusBadge status={selected.status} />
            <div className="drawer-content">
              {Object.keys(selected.data).length ? Object.entries(selected.data).map(([key, value]) => (
                <section key={key}>
                  <h3>{key.replaceAll("_", " ")}</h3>
                  <pre>{pretty(value)}</pre>
                </section>
              )) : (
                <p>This teammate is preparing its work.</p>
              )}
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
