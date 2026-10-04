/**
 * Shared GET /health (getHealth) response checks for docker-compose staging smoke.
 * No secrets; base URL from HEALTH_SMOKE_URL (default http://127.0.0.1:3000/health).
 */

/** @param {unknown} body */
export function validateGetHealthBody(body) {
  if (body === null || typeof body !== 'object' || Array.isArray(body)) {
    return { ok: false, reason: 'body is not a JSON object' };
  }
  const record = /** @type {Record<string, unknown>} */ (body);
  if (record.status !== 'ok') {
    return { ok: false, reason: `status must be "ok", got ${JSON.stringify(record.status)}` };
  }
  if (record.database !== 'up') {
    return {
      ok: false,
      reason: `database must be "up", got ${JSON.stringify(record.database)}`,
    };
  }
  if (typeof record.timestamp !== 'string' || Number.isNaN(Date.parse(record.timestamp))) {
    return { ok: false, reason: 'timestamp must be an ISO-8601 date-time string' };
  }
  return { ok: true };
}

/**
 * @param {string} baseUrl full URL to GET /health (unprefixed infra probe)
 * @param {{ fetchFn?: typeof fetch; timeoutMs?: number }} [options]
 */
export async function probeGetHealth(baseUrl, options = {}) {
  const fetchFn = options.fetchFn ?? fetch;
  const timeoutMs = options.timeoutMs ?? 15_000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetchFn(baseUrl, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    const text = await res.text();
    let json;
    try {
      json = JSON.parse(text);
    } catch {
      return {
        ok: false,
        status: res.status,
        reason: `non-JSON response: ${text.slice(0, 200)}`,
      };
    }
    if (res.status !== 200) {
      return {
        ok: false,
        status: res.status,
        reason: `expected HTTP 200, got ${res.status}`,
        body: json,
      };
    }
    const validation = validateGetHealthBody(json);
    if (!validation.ok) {
      return { ok: false, status: res.status, reason: validation.reason, body: json };
    }
    return { ok: true, status: res.status, body: json };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, reason: message };
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Poll until getHealth succeeds or attempts exhausted.
 * @param {string} baseUrl
 * @param {{ attempts?: number; intervalMs?: number; fetchFn?: typeof fetch }} [options]
 */
export async function waitForGetHealth(baseUrl, options = {}) {
  const attempts = options.attempts ?? 30;
  const intervalMs = options.intervalMs ?? 2_000;
  let last = /** @type {Awaited<ReturnType<typeof probeGetHealth>> | null} */ (null);
  for (let i = 0; i < attempts; i += 1) {
    last = await probeGetHealth(baseUrl, { fetchFn: options.fetchFn });
    if (last.ok) {
      return last;
    }
    if (i < attempts - 1) {
      await new Promise((r) => setTimeout(r, intervalMs));
    }
  }
  return last ?? { ok: false, reason: 'no attempts made' };
}
