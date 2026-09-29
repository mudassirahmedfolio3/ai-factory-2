import type { AuditEvent, RunState } from "./types";

const BASE = "/api";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  return res.json() as Promise<T>;
}

export function listRuns(): Promise<RunState[]> {
  return fetchJson("/runs");
}

export function getRun(runId: string): Promise<RunState> {
  return fetchJson(`/runs/${runId}`);
}

export function getCurrentRun(): Promise<RunState> {
  return fetchJson("/runs/current");
}

export function fetchRandomBrief(): Promise<{
  project_name: string;
  client_brief: string;
  niche: string;
  source: string;
}> {
  return fetchJson("/briefs/random");
}

export function startRun(body: {
  project_name: string;
  client_brief: string;
  complexity: "basic" | "basic_plus" | "standard" | "full";
  max_releases?: number;
}): Promise<{
  run_id: string;
  status: string;
  complexity?: string;
  estimated_minutes?: number;
}> {
  return fetchJson("/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function fetchArtifact(path: string, runId?: string): Promise<{ content: string }> {
  const url = runId
    ? `/runs/${runId}/artifacts/${path}`
    : `/artifacts/${path}`;
  return fetchJson(url);
}

export function subscribeEvents(
  runId: string | null,
  onState: (state: RunState) => void,
  onAudit: (event: AuditEvent) => void,
): () => void {
  const url = runId
    ? `${BASE}/runs/${runId}/events`
    : `${BASE}/runs/current/events`;

  const source = new EventSource(url);

  source.addEventListener("state", (e) => {
    onState(JSON.parse(e.data) as RunState);
  });

  source.addEventListener("audit", (e) => {
    onAudit(JSON.parse(e.data) as AuditEvent);
  });

  return () => source.close();
}
