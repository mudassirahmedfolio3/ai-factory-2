import React, { useCallback, useEffect, useState } from 'react';
import { listRuns, startEmulatorRun } from './api.js';

function Brand() {
  return (
    <div className="brand">
      <img src="/assets/df624.svg" alt="" />
      <div>
        <b>AI FACTORY</b>
        <small>From Requirement to Reality</small>
      </div>
    </div>
  );
}

function formatWhen(run) {
  const raw = run.archived_at || run.updated_at;
  if (!raw) return '—';
  try {
    return new Date(raw).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return raw;
  }
}

function statusLabel(run) {
  if (run.is_live && run.status === 'running') return 'Live';
  const s = (run.status || 'unknown').toLowerCase();
  if (s === 'completed') return 'Completed';
  if (s === 'failed') return 'Failed';
  if (s === 'stale') return 'Stale';
  if (s === 'running') return 'Running';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function statusClass(run) {
  if (run.is_live && run.status === 'running') return 'live';
  const s = (run.status || '').toLowerCase();
  if (s === 'completed') return 'completed';
  if (s === 'failed') return 'failed';
  if (s === 'stale') return 'stale';
  if (s === 'running') return 'running';
  return 'unknown';
}

export default function History({ onOpenRun, onNewProject }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [emulatorBusyId, setEmulatorBusyId] = useState(null);
  const [emulatorMsg, setEmulatorMsg] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    setError('');
    listRuns()
      .then((data) => setRuns(Array.isArray(data) ? data : []))
      .catch((err) => {
        setRuns([]);
        setError(err.message || 'Could not load run history.');
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const onFocus = () => load();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [load]);

  async function handleRunEmulator(run) {
    if (!run?.run_id || emulatorBusyId) return;
    setEmulatorBusyId(run.run_id);
    setEmulatorMsg('');
    try {
      const status = await startEmulatorRun(run.run_id);
      setEmulatorMsg(
        status.message ||
          `Emulator ${status.status || 'starting'} for ${run.project_name || run.run_id}` +
            (status.device_id ? ` · ${status.device_id}` : '') +
            (status.note ? ` · ${status.note}` : ''),
      );
    } catch (err) {
      setEmulatorMsg(err.message || 'Failed to start emulator');
    } finally {
      setEmulatorBusyId(null);
    }
  }

  return (
    <>
      <header className="header history-header">
        <Brand />
        <div className="header-actions">
          <button type="button" className="secondary header-btn" onClick={onNewProject}>
            New project
          </button>
        </div>
      </header>
      <main className="history">
        <div className="history-intro">
          <h1>Run history</h1>
          <p>
            Recent factory runs and their status. Open any run for full details, or launch a
            Flutter app on your local emulator when sources are available under{' '}
            <code>ai_factory/apps</code>.
          </p>
        </div>

        {emulatorMsg && (
          <p className="history-emulator-msg" role="status">
            {emulatorMsg}
          </p>
        )}

        {loading && (
          <p className="history-status" role="status">
            Loading runs…
          </p>
        )}

        {!loading && error && (
          <div className="history-empty" role="alert">
            <p className="error">{error}</p>
            <button type="button" className="secondary" onClick={load}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && runs.length === 0 && (
          <div className="history-empty">
            <p>No archived runs yet.</p>
            <button type="button" className="primary" onClick={onNewProject}>
              Start a project
            </button>
          </div>
        )}

        {!loading && !error && runs.length > 0 && (
          <ul className="history-list">
            {runs.map((run) => (
              <li key={run.run_id} className="history-row">
                <div className="history-row-main">
                  <div className="history-row-title">
                    <b>{run.project_name || 'Untitled project'}</b>
                    <span className={`run-status run-status-${statusClass(run)}`}>
                      {statusLabel(run)}
                    </span>
                    {run.flutter_ready ? (
                      <span className="run-status run-status-flutter">Flutter</span>
                    ) : null}
                  </div>
                  <div className="history-row-meta">
                    <span title="Run ID">{run.run_id}</span>
                    {run.phase ? <span>{run.phase}</span> : null}
                    {run.complexity ? <span>{run.complexity}</span> : null}
                    {run.usage?.total_tokens ? (
                      <span title="LLM tokens">
                        {(run.usage.uncached_tokens ?? run.usage.total_tokens).toLocaleString()} tokens
                        {run.usage.llm_calls ? ` · ${run.usage.llm_calls} calls` : ''}
                      </span>
                    ) : null}
                    <span>{formatWhen(run)}</span>
                  </div>
                </div>
                <div className="history-row-actions">
                  {run.flutter_ready ? (
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => handleRunEmulator(run)}
                      disabled={Boolean(emulatorBusyId)}
                    >
                      {emulatorBusyId === run.run_id ? 'Starting…' : 'Run on emulator'}
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="primary"
                    onClick={() => onOpenRun(run)}
                    disabled={!run.run_id}
                  >
                    View details
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
