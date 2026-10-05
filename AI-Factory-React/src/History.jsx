import React, { useCallback, useEffect, useState } from 'react';
import {
  ApiError,
  downloadRunDossier,
  getEmulatorStatus,
  listRuns,
  resumeRun,
  startEmulatorRun,
} from './api.js';

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

function canGenerateRelease(run, runs) {
  if (!run?.run_id) return false;
  // Only block when a worker is actually running this run (not orphaned "running" UI state).
  if (run.is_live && (run.status || '').toLowerCase() === 'running') return false;
  const liveOther = runs.find(
    (r) => r.is_live && (r.status || '').toLowerCase() === 'running' && r.run_id !== run.run_id,
  );
  if (liveOther) return false;
  const s = (run.status || '').toLowerCase();
  if (s === 'completed' || s === 'failed' || s === 'stopped' || s === 'stale') return true;
  // Worker gone but checkpoint still says running — resume is allowed.
  if (s === 'running' && !run.is_live) return true;
  return false;
}

export default function History({ onOpenRun, onNewProject, onGenerateRelease }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [emulatorBusyId, setEmulatorBusyId] = useState(null);
  const [releaseBusyId, setReleaseBusyId] = useState(null);
  const [emulatorMsg, setEmulatorMsg] = useState('');
  const [dossierBusy, setDossierBusy] = useState(null);

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

  async function handleGenerateRelease(run) {
    if (!run?.run_id || releaseBusyId) return;
    setReleaseBusyId(run.run_id);
    setEmulatorMsg('');
    try {
      await resumeRun(run.run_id);
      setEmulatorMsg(
        `Generating another release for ${run.project_name || run.run_id}… opening live view.`,
      );
      if (onGenerateRelease) {
        onGenerateRelease(run);
      } else {
        onOpenRun(run);
      }
      load();
    } catch (err) {
      if (err instanceof ApiError && err.code === 'RUN_IN_PROGRESS' && err.runId) {
        setEmulatorMsg(
          `Cannot start while run ${err.runId} is in progress. Wait for it to finish or open that run.`,
        );
      } else {
        setEmulatorMsg(err.message || 'Could not start another release');
      }
    } finally {
      setReleaseBusyId(null);
    }
  }

  async function handleDownloadDossier(run, format = 'pdf') {
    if (!run?.run_id || dossierBusy) return;
    setDossierBusy({ runId: run.run_id, format });
    setEmulatorMsg('');
    try {
      await downloadRunDossier(run.run_id, format);
      const label = format === 'html' ? 'HTML' : 'PDF';
      setEmulatorMsg(`Downloaded SDLC dossier (${label}) for ${run.run_id}.`);
    } catch (err) {
      setEmulatorMsg(err.message || 'Could not download dossier.');
    } finally {
      setDossierBusy(null);
    }
  }

  async function handleRunEmulator(run) {
    if (!run?.run_id || emulatorBusyId) return;
    const runId = run.run_id;
    setEmulatorBusyId(runId);
    setEmulatorMsg(
      `Starting emulator for ${run.project_name || runId}… (first launch can take several minutes; your live factory run is not stopped.)`,
    );
    try {
      const status = await startEmulatorRun(runId);
      const formatStatus = (s) => {
        const tail = (s.log_tail || '').split('\n').filter(Boolean).pop();
        return (
          (s.message ? `${s.message} · ` : '') +
          `Emulator ${s.status || 'starting'} for ${run.project_name || runId}` +
          (s.device_id ? ` · ${s.device_id}` : '') +
          (s.note ? ` · ${s.note}` : '') +
          (s.error ? ` · ${s.error}` : '') +
          (tail ? ` · ${tail.slice(0, 120)}` : '')
        );
      };
      setEmulatorMsg(formatStatus(status));

      for (let i = 0; i < 120; i += 1) {
        await new Promise((r) => window.setTimeout(r, 3000));
        const latest = await getEmulatorStatus(runId);
        setEmulatorMsg(formatStatus(latest));
        if (latest.status === 'failed' || latest.status === 'stopped' || latest.status === 'idle') {
          break;
        }
        if (latest.status === 'running' && (latest.log_tail || '').includes('Flutter run key commands')) {
          setEmulatorMsg(
            `${formatStatus(latest)} · Check your Android emulator window — the app should be open.`,
          );
          break;
        }
      }
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
            Flutter app on the local emulator when sources exist, or{' '}
            <strong>Generate another release</strong> to continue the same project (blocked while a
            different run is live).
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
                    <b>{run.product_name || run.project_name || 'Untitled project'}</b>
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
                  {canGenerateRelease(run, runs) ? (
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => handleGenerateRelease(run)}
                      disabled={Boolean(releaseBusyId)}
                    >
                      {releaseBusyId === run.run_id ? 'Starting…' : 'Generate another release'}
                    </button>
                  ) : null}
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
                    className="icon-btn secondary"
                    title="Download SDLC dossier (HTML)"
                    aria-label="Download SDLC dossier HTML"
                    onClick={() => handleDownloadDossier(run, 'html')}
                    disabled={
                      !run.run_id ||
                      (dossierBusy?.runId === run.run_id && Boolean(dossierBusy))
                    }
                  >
                    {dossierBusy?.runId === run.run_id && dossierBusy?.format === 'html'
                      ? '…'
                      : '↓ HTML'}
                  </button>
                  <button
                    type="button"
                    className="icon-btn secondary"
                    title="Download SDLC dossier (PDF)"
                    aria-label="Download SDLC dossier PDF"
                    onClick={() => handleDownloadDossier(run, 'pdf')}
                    disabled={
                      !run.run_id ||
                      (dossierBusy?.runId === run.run_id && Boolean(dossierBusy))
                    }
                  >
                    {dossierBusy?.runId === run.run_id && dossierBusy?.format === 'pdf'
                      ? '…'
                      : '↓ PDF'}
                  </button>
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
