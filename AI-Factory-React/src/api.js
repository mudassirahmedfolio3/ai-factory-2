const BASE = import.meta.env.VITE_API_URL || '/api';

export class ApiError extends Error {
  constructor(message, { status, runId, code } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.runId = runId;
    this.code = code;
  }
}

async function fetchJson(path, init = {}) {
  const defaultTimeoutMs = init.method === 'POST' && path === '/runs' ? 60000 : 15000;
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    signal: init.signal ?? AbortSignal.timeout(defaultTimeoutMs),
  });
  if (!res.ok) {
    const raw = await res.text();
    let message = raw || res.statusText;
    let runId;
    try {
      const parsed = JSON.parse(raw);
      const detail = parsed.detail;
      if (typeof detail === 'object' && detail !== null) {
        message = detail.message || message;
        runId = detail.run_id;
      } else if (typeof detail === 'string') {
        message = detail;
      }
    } catch {
      /* plain text error body */
    }
    if (res.status === 409 && runId) {
      throw new ApiError(message, { status: 409, runId, code: 'RUN_IN_PROGRESS' });
    }
    throw new ApiError(message, { status: res.status });
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

export function fetchAuditEvents(runId) {
  return fetchJson(`/runs/${runId}/audit`);
}

export function previewUrl(runId) {
  return `${BASE}/runs/${runId}/preview/index.html`;
}

export function listEmulatorDevices(runId) {
  return fetchJson(`/runs/${runId}/emulator/devices`);
}

export function getEmulatorStatus(runId) {
  return fetchJson(`/runs/${runId}/emulator/status`);
}

export function startEmulatorRun(runId, deviceId) {
  return fetchJson(`/runs/${runId}/emulator/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(deviceId ? { device_id: deviceId } : {}),
  });
}

export function stopEmulatorRun(runId) {
  return fetchJson(`/runs/${runId}/emulator/stop`, { method: 'POST' });
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
