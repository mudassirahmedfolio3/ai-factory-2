import React, { useCallback, useEffect, useState } from 'react';
import { listRuns } from './api.js';

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
          <p>Recent factory runs and their status. Open any run for full details.</p>
        </div>

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
                  </div>
                  <div className="history-row-meta">
                    <span title="Run ID">{run.run_id}</span>
                    {run.phase ? <span>{run.phase}</span> : null}
                    {run.complexity ? <span>{run.complexity}</span> : null}
                    <span>{formatWhen(run)}</span>
                  </div>
                </div>
                <button
                  type="button"
                  className="primary"
                  onClick={() => onOpenRun(run)}
                  disabled={!run.run_id}
                >
                  View details
                </button>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
