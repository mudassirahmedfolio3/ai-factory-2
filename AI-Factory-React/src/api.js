const BASE = '/api';

async function fetchJson(path, init) {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  return res.json();
}

export function listRuns() {
  return fetchJson('/runs');
}

export function getRun(runId) {
  return fetchJson(`/runs/${runId}`);
}

export function getCurrentRun() {
  return fetchJson('/runs/current');
}

export function fetchRandomBrief() {
  return fetchJson('/briefs/random');
}

export function listComplexityOptions() {
  return fetchJson('/complexity-options');
}

export function startRun(body) {
  return fetchJson('/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function fetchArtifact(path, runId) {
  const url = runId
    ? `/runs/${runId}/artifacts/${path}`
    : `/artifacts/${path}`;
  return fetchJson(url);
}

export function previewUrl(runId) {
  return `${BASE}/runs/${runId}/preview/index.html`;
}

export function subscribeEvents(runId, onState, onAudit) {
  const url = runId
    ? `${BASE}/runs/${runId}/events`
    : `${BASE}/runs/current/events`;

  const source = new EventSource(url);

  source.addEventListener('state', (e) => {
    onState(JSON.parse(e.data));
  });

  source.addEventListener('audit', (e) => {
    onAudit(JSON.parse(e.data));
  });

  return () => source.close();
}
