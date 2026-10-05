import React, { useEffect, useRef, useState } from 'react';
import { stages, examples } from './data';
import { validateFiles } from './engine';
import { gates } from './gates.js';
import { GateReview, MockupReview } from './GateReview.jsx';
import { MobileFrame, StageSkeleton, ReadyApp } from './Phone';
import {
  ApiError,
  fetchRandomBrief,
  fetchArtifact,
  fetchAuditEvents,
  getCurrentRun,
  getRun,
  previewUrl as buildPreviewUrl,
  getEmulatorStatus,
  startEmulatorRun,
  stopEmulatorRun,
  startRun,
  downloadRunDossier,
} from './api.js';
import { displayAgentName } from './agentLabels.js';
import {
  buildClientBrief,
  buildProgressFooterLine,
  deliveryStageCopy,
  filterUsageForStage,
  flutterRunReadyFromState,
  fzCurrentWorkLabel,
  fzStudioSubtitle,
  runStateToDashboard,
  slugProjectName,
} from './phaseMap.js';
import { buildProjectJourney } from './journeyMap.js';
import { buildStageIterations } from './stageIterations.js';
import { stageDocumentCandidates } from './stageDocuments.js';
import { connectRun } from './runSync.js';
import History from './History.jsx';

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

function Progress({ value, label }) {
  return (
    <div
      className="progress"
      role="progressbar"
      aria-label={label}
      aria-valuenow={Math.round(value)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <span style={{ width: `${value}%` }} />
    </div>
  );
}

function projectFromRunState(state, fallbackText = '') {
  return {
    runId: state.run_id,
    text: fallbackText,
    files: [],
    complexity: state.complexity || 'standard',
    estimatedMinutes: state.estimated_minutes,
    projectName: state.project_name || 'Project',
  };
}

const UI_SESSION_KEY = 'ai_factory_ui_session';

function loadUiSession() {
  try {
    const raw = sessionStorage.getItem(UI_SESSION_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (data?.view === 'dashboard' && data?.project?.runId) return data;
  } catch {
    /* ignore corrupt session */
  }
  return null;
}

function saveUiSession(view, project) {
  try {
    if (view === 'dashboard' && project?.runId) {
      sessionStorage.setItem(
        UI_SESSION_KEY,
        JSON.stringify({
          view: 'dashboard',
          project: {
            runId: project.runId,
            text: project.text || '',
            files: [],
            complexity: project.complexity || 'standard',
            estimatedMinutes: project.estimatedMinutes,
            projectName: project.projectName || 'Project',
          },
        }),
      );
    } else if (view === 'intake') {
      sessionStorage.removeItem(UI_SESSION_KEY);
    }
  } catch {
    /* storage disabled */
  }
}

function Intake({ onStart, onOpenHistory }) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState([]);
  const [menu, setMenu] = useState(false);
  const [error, setError] = useState('');
  const [drag, setDrag] = useState(false);
  const [starting, setStarting] = useState(false);
  const [loadingBrief, setLoadingBrief] = useState(false);
  const [liveRun, setLiveRun] = useState(null);
  const input = useRef();
  const menuRef = useRef();

  useEffect(() => {
    getCurrentRun()
      .then((state) => {
        if (!state?.run_id) return;
        if (state.status === 'running' || state.status === 'stale') {
          setLiveRun({ ...state, is_live: Boolean(state.is_live) });
        }
        if (state.status === 'completed') setLiveRun({ ...state, completed: true });
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const close = (e) => {
      if (!menuRef.current?.contains(e.target)) setMenu(false);
    };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  }, []);

  function addFiles(list) {
    const { accepted, errors } = validateFiles([...list]);
    setFiles((old) =>
      [...old, ...accepted.filter((f) => !old.some((o) => o.name === f.name && o.size === f.size))].slice(0, 8),
    );
    setError(
      errors.join(' ') ||
        (files.length + accepted.length > 8 ? 'You can attach up to 8 files.' : ''),
    );
    setMenu(false);
  }

  function pick(accept) {
    input.current.accept = accept;
    input.current.click();
    setMenu(false);
  }

  async function handleRandomBrief() {
    setLoadingBrief(true);
    setError('');
    try {
      const brief = await fetchRandomBrief();
      setText(brief.client_brief);
    } catch (err) {
      setError(err.message || 'Could not load random brief.');
    } finally {
      setLoadingBrief(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim() && !files.length) return;
    setStarting(true);
    setError('');
    const project_name = slugProjectName(text);
    try {
      const client_brief = buildClientBrief(text, files);
      const result = await startRun({
        project_name,
        client_brief,
        complexity: 'standard',
      });
      onStart({
        runId: result.run_id,
        text: text.trim(),
        files,
        complexity: result.complexity || 'standard',
        estimatedMinutes: result.estimated_minutes,
        projectName: project_name,
      });
    } catch (err) {
      if (err instanceof ApiError && err.code === 'RUN_IN_PROGRESS' && err.runId) {
        setLiveRun({ run_id: err.runId, project_name: project_name, status: 'running', is_live: true });
        setError('A factory run is already in progress. View it below or wait for it to finish.');
        return;
      }
      setError(err.message || 'Failed to start factory run.');
    } finally {
      setStarting(false);
    }
  }

  function viewLiveRun() {
    if (!liveRun) return;
    onStart(projectFromRunState(liveRun, text.trim()));
  }

  return (
    <div className="app-shell">
      {liveRun && (
        <div className="live-run-banner" role="status">
          <span>
            {liveRun.completed ? 'Run complete' : 'Run in progress'}:{' '}
            <b>{liveRun.project_name}</b> ({liveRun.run_id})
          </span>
          <button type="button" className="primary" onClick={viewLiveRun}>
            {liveRun.completed ? 'View delivery' : 'View live run'}
          </button>
        </div>
      )}
      <header className="header intake-header">
        <Brand />
        <div className="header-actions">
          <button type="button" className="secondary header-btn" onClick={onOpenHistory}>
            History
          </button>
          <span className="eyebrow">NEW PROJECT</span>
        </div>
      </header>
      <main className="intake">
        <div className="welcome">
          <span className="badge">YOUR IDEA. OUR AI SPECIALISTS.</span>
          <h1>What would you like to build?</h1>
          <p>Describe your idea or upload a requirement document. We&apos;ll take it from here.</p>
        </div>
        <form
          className={`composer ${drag ? 'dragging' : ''}`}
          onSubmit={handleSubmit}
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            addFiles(e.dataTransfer.files);
          }}
        >
          <label className="sr-only" htmlFor="requirements">
            Your requirements
          </label>
          <textarea
            id="requirements"
            placeholder="Describe the app you want to build…"
            value={text}
            maxLength={10000}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                e.currentTarget.form.requestSubmit();
              }
            }}
          />
          <div className="attachments">
            {files.map((f, i) => (
              <div className="attachment" key={f.name + i}>
                <img src="/assets/11e0d.svg" alt="" />
                <span title={f.name}>
                  {f.name}
                  <small>{f.size < 1024 ? `${f.size} B` : `${(f.size / 1024).toFixed(0)} KB`}</small>
                </span>
                <button
                  type="button"
                  aria-label={`Remove ${f.name}`}
                  onClick={() => setFiles(files.filter((_, x) => x !== i))}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          <div className="composer-actions">
            <div className="upload-wrap" ref={menuRef}>
              <button
                className="plus"
                type="button"
                aria-label="Add images or documents"
                aria-expanded={menu}
                onClick={() => setMenu(!menu)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') setMenu(false);
                }}
              >
                +
              </button>
              <span>Add images or documents</span>
              {menu && (
                <div className="upload-menu">
                  <button type="button" onClick={() => pick('.pdf,.doc,.docx,.txt,.md')}>
                    ▤ Upload requirement document
                  </button>
                  <button type="button" onClick={() => pick('image/png,image/jpeg,image/webp')}>
                    ▧ Upload images
                  </button>
                </div>
              )}
            </div>
            <input
              ref={input}
              type="file"
              multiple
              hidden
              onChange={(e) => {
                addFiles(e.target.files);
                e.target.value = '';
              }}
            />
            <button
              className="secondary"
              type="button"
              disabled={loadingBrief || starting}
              onClick={handleRandomBrief}
            >
              {loadingBrief ? 'Loading…' : 'Random brief'}
            </button>
            <button className="primary" disabled={(!text.trim() && !files.length) || starting}>
              {starting ? 'Starting…' : 'Start AI Factory'} <span>→</span>
            </button>
          </div>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </form>
        <div className="intake-hints">
          <p>Attach a document or image, write your requirements, or use both.</p>
          <small>PDF, DOCX, TXT, MD, PNG, JPG, WebP · Up to 20 MB each · 8 files</small>
          <div className="examples">
            {Object.keys(examples).map((x) => (
              <button key={x} type="button" onClick={() => setText(examples[x])}>
                {x}
              </button>
            ))}
          </div>
        </div>
        <p className="next">
          <b>NEXT</b> Your Requirement specialist will review your brief and shape the product vision.
        </p>
        <p className="demo-note">Live run · Powered by CrewAI</p>
      </main>
    </div>
  );
}

function Modal({ title, children, onClose }) {
  const ref = useRef();
  useEffect(() => {
    ref.current.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === ref.current) onClose();
      }}
    >
      <div className="modal-heading">
        <h2>{title}</h2>
        <button onClick={onClose} aria-label="Close dialog">
          ×
        </button>
      </div>
      {children}
    </dialog>
  );
}

function providerLabel(provider) {
  const labels = {
    anthropic: 'Claude',
    cursor_cli: 'Cursor',
    cursor_proxy: 'Cursor',
    openai: 'OpenAI',
    groq: 'Groq',
  };
  return labels[provider] || provider || 'LLM';
}

function formatUsage(usage, live = false) {
  if (!usage && !live) return null;
  const calls = usage?.llm_calls ?? 0;
  const total = usage?.uncached_tokens ?? usage?.total_tokens ?? 0;
  const budget = usage?.token_budget ?? 0;
  const pct = usage?.usage_percent ?? 0;
  const provider = providerLabel(usage?.provider);
  if (!calls && !live && !budget) return null;
  const totalLabel = total.toLocaleString();
  if (budget > 0) {
    const budgetLabel = budget.toLocaleString();
    return calls
      ? `${provider} · ${calls} calls · ${totalLabel} / ${budgetLabel} uncached (${pct}%)`
      : `${provider} · 0 / ${budgetLabel} tokens (0%)`;
  }
  const approx = usage?.estimated_calls ? '~' : '';
  const label = total >= 1000 ? `${approx}${Math.round(total / 1000)}k tokens` : `${approx}${total} tokens`;
  return calls ? `${provider} · ${calls} LLM calls · ${label}` : `${provider} · tracking usage…`;
}

function formatDuration(ms) {
  const n = Number(ms) || 0;
  if (n <= 0) return null;
  if (n < 1000) return `${n}ms`;
  const s = Math.round(n / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return rem ? `${m}m ${rem}s` : `${m}m`;
}

function formatActivityTokens(activity) {
  const total = activity?.total_tokens ?? 0;
  if (!total && activity?.status === 'running') return 'working…';
  const prefix = activity?.estimated ? '~' : '';
  const tokens =
    total >= 1000 ? `${prefix}${Math.round(total / 1000)}k tokens` : `${prefix}${total} tokens`;
  const dur = formatDuration(activity?.duration_ms);
  return dur ? `${tokens} · ${dur}` : tokens;
}

function groupActivitiesByPhase(activities = []) {
  const groups = [];
  const index = new Map();
  for (const item of activities) {
    const phase = item.phase || item.task || 'other';
    if (!index.has(phase)) {
      index.set(phase, groups.length);
      groups.push({ phase, items: [] });
    }
    groups[index.get(phase)].items.push(item);
  }
  return groups;
}

function UsageActivityFeed({ activities = [], live = false, onSelect }) {
  const all = [...activities];
  const items = live ? all.reverse().slice(0, 12) : all;
  if (!items.length && !live) return null;

  if (!live && items.length) {
    const groups = groupActivitiesByPhase(items);
    return (
      <div className="usage-activity-archive" aria-label="Model activity by stage">
        {groups.map((group) => (
          <div key={group.phase} className="usage-activity-group">
            <h4 className="usage-activity-phase">{group.phase}</h4>
            <ul className="usage-activity">
              {group.items.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`usage-activity-item usage-activity-${item.status || 'completed'} usage-activity-btn`}
                    onClick={() => onSelect?.(item)}
                  >
                    <div className="usage-activity-main">
                      <span className="usage-activity-dot" aria-hidden="true" />
                      <div className="usage-activity-copy">
                        <span className="usage-activity-who">{displayAgentName(item.agent)}</span>
                        <span className="usage-activity-model">{item.model || 'model'}</span>
                      </div>
                      <span className="usage-activity-tokens">{formatActivityTokens(item)}</span>
                    </div>
                    {item.task && <p className="usage-activity-task">{item.task}</p>}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    );
  }

  return (
    <ul className="usage-activity" aria-label="Model activity">
      {items.map((item) => (
        <li key={item.id}>
          <button
            type="button"
            className={`usage-activity-item usage-activity-${item.status || 'completed'} usage-activity-btn`}
            onClick={() => onSelect?.(item)}
          >
            <div className="usage-activity-main">
              <span className={`usage-activity-dot ${item.status === 'running' ? 'pulse' : ''}`} aria-hidden="true" />
              <div className="usage-activity-copy">
                <span className="usage-activity-who">{displayAgentName(item.agent)}</span>
                <span className="usage-activity-model">{item.model || 'model'}</span>
              </div>
              <span className="usage-activity-tokens">{formatActivityTokens(item)}</span>
            </div>
            {item.task && <p className="usage-activity-task">{item.task}</p>}
          </button>
        </li>
      ))}
      {live && !items.some((item) => item.status === 'running') && (
        <li className="usage-activity-item usage-activity-waiting">
          <div className="usage-activity-main">
            <span className="usage-activity-dot pulse" aria-hidden="true" />
            <div className="usage-activity-copy">
              <span className="usage-activity-who">Pipeline</span>
              <span className="usage-activity-model">waiting for next model call</span>
            </div>
          </div>
        </li>
      )}
    </ul>
  );
}

function UsageDetailModal({ activity, onClose }) {
  if (!activity) return null;
  const title = activity.detail_title || activity.label || activity.agent || 'Activity';
  const items = activity.detail_items || [];
  const paths = activity.detail_paths || [];
  return (
    <Modal title={title} onClose={onClose}>
      <div className="usage-detail">
        <p className="usage-detail-meta">
          {[displayAgentName(activity.agent), activity.model, activity.phase || activity.task, formatActivityTokens(activity)]
            .filter(Boolean)
            .join(' · ')}
        </p>
        {items.length ? (
          <ul className="usage-detail-list">
            {items.map((line, i) => (
              <li key={`${i}-${String(line).slice(0, 24)}`}>{line}</li>
            ))}
          </ul>
        ) : (
          <p>No detail recorded for this step yet.</p>
        )}
        {paths.length > 0 && (
          <>
            <h3 className="usage-detail-paths-heading">Artifacts</h3>
            <ul className="usage-detail-paths">
              {paths.map((p) => (
                <li key={p}>
                  <code>{p}</code>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
      <button type="button" className="primary" onClick={onClose}>
        Close
      </button>
    </Modal>
  );
}

function UsageBanner({ usage, live = false, stageLive = false }) {
  const [selected, setSelected] = useState(null);
  const budget = usage?.token_budget ?? 0;
  const provider = usage?.provider || 'llm';
  const activities = usage?.activities ?? [];
  const show =
    live ||
    stageLive ||
    budget > 0 ||
    (usage?.total_tokens ?? 0) > 0 ||
    activities.length > 0 ||
    provider === 'anthropic' ||
    provider === 'cursor_cli' ||
    provider === 'agentic_sdlc';
  if (!show) return null;

  const pct = Math.min(100, usage?.usage_percent ?? 0);
  const level = pct >= 90 ? 'critical' : pct >= 70 ? 'warn' : 'ok';
  const label =
    formatUsage(usage, live || stageLive) ||
    `${providerLabel(provider)} · token usage tracking…`;

  return (
    <div
      className={`usage-banner usage-${level}`}
      title={usage?.budget_warning || 'LLM token usage for this stage'}
    >
      <p className="usage-banner-text">{label}</p>
      {budget > 0 && (
        <div className="usage-meter-track" aria-hidden="true">
          <div className="usage-meter-fill" style={{ width: `${Math.max(pct, (live || stageLive) && !usage?.total_tokens ? 1 : 0)}%` }} />
        </div>
      )}
      <UsageActivityFeed
        activities={activities}
        live={stageLive}
        onSelect={setSelected}
      />
      {usage?.budget_warning && <small className="usage-warning">{usage.budget_warning}</small>}
      {selected && <UsageDetailModal activity={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function Dashboard({ project, onReset, onOpenHistory }) {
  const [runState, setRunState] = useState(null);
  const [runLoading, setRunLoading] = useState(true);
  const [view, setView] = useState(null);
  const [modal, setModal] = useState(null);
  const [prdContent, setPrdContent] = useState('');
  const [prdLoading, setPrdLoading] = useState(false);
  const [prdMeta, setPrdMeta] = useState({ title: 'Document', path: '' });
  const [flutterManifest, setFlutterManifest] = useState('');
  const [flutterLoading, setFlutterLoading] = useState(false);
  const [emulatorStatus, setEmulatorStatus] = useState(null);
  const [emulatorBusy, setEmulatorBusy] = useState(false);
  const [auditEvents, setAuditEvents] = useState([]);
  const [journeyLoading, setJourneyLoading] = useState(false);
  const [gateOpen, setGateOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [dossierBusy, setDossierBusy] = useState(null);
  const navRef = useRef();
  const detailScrollRef = useRef(null);

  const lastStage = stages.length - 1;
  const run = runState
    ? runStateToDashboard(runState)
    : {
        active: 0,
        progress: 0,
        complete: false,
        failed: false,
        overall: 0,
        browserReady: false,
        projectName: project.projectName,
        approval: 'pending',
        checks: {},
        releaseNumber: 1,
      };

  const stageIndex = view ?? run.active;
  const stage = stages[stageIndex];
  const viewing = view !== null && view !== run.active;
  const progress = viewing ? (stageIndex < run.active ? 100 : 0) : run.progress;
  const done = run.complete && stageIndex === lastStage;
  const isFutureStage = viewing && stageIndex > run.active;

  useEffect(() => {
    if (detailScrollRef.current) detailScrollRef.current.scrollTop = 0;
  }, [stageIndex]);

  const gateInfo = gates.find((g) => g.index === stageIndex);
  const isFzEngine = runState?.factory_engine === 'fz';
  const preview =
    !isFzEngine && run.browserReady && project.runId ? buildPreviewUrl(project.runId) : null;
  const showPreview = Boolean(preview && (run.browserReady || run.complete));
  const displayName =
    runState?.product_name || runState?.project_name || project.projectName || 'Project';
  const flutterDir =
    runState?.flutter_project_dir ||
    (project.runId ? `apps/${project.runId}/flutter` : null);
  const flutterReady =
    flutterRunReadyFromState(runState) ||
    (run.complete && isFzEngine) ||
    Boolean(runState?.flutter_ready);
  const isDeliveryStage = stageIndex === lastStage;
  const deliveryCopy = isDeliveryStage ? deliveryStageCopy(runState, displayName) : null;
  const journey = buildProjectJourney(auditEvents, runState);
  const stageIterations = buildStageIterations(auditEvents, stageIndex, {
    isLiveStage: !viewing,
    progress,
    complete: done || (stageIndex < run.active && run.active > 0),
    failed: run.failed && !viewing,
    future: isFutureStage,
  });
  const stageUsage = filterUsageForStage(runState?.usage, stageIndex);
  const featureLines = deliveryCopy?.deployLines || stage.card2.slice(1);
  const stageDoc = stageDocumentCandidates(stageIndex, runState?.artifacts_index || []);

  const card1Title = deliveryCopy?.card1Title || stage.card1[0];
  const card1Name =
    stageIndex === 0 && project.files.length
      ? project.files[0].name
      : deliveryCopy?.card1Name ||
        stage.card1[1].replace(/^NOVA\s*·\s*/i, `${displayName} · `);
  const card1Sub =
    deliveryCopy?.card1Sub ||
    (stageDoc.paths[0] ? stageDoc.paths[0] : stage.card1[2]);
  const card1Foot =
    deliveryCopy?.card1Foot ||
    (done
      ? 'Handover package ready'
      : stageDoc.paths.length
        ? `Open ${stageDoc.title}`
        : stage.card1[3]);

  useEffect(() => {
    stages.forEach((s) => {
      const img = new Image();
      img.src = s.image;
    });
  }, []);

  useEffect(() => {
    setRunLoading(true);
    const loadingTimeout = window.setTimeout(() => setRunLoading(false), 10000);
    const disconnect = connectRun(
      project.runId,
      (state) => {
        setRunState(state);
        setRunLoading(false);
      },
      (event) => {
        setAuditEvents((prev) => {
          if (prev.some((e) => e.timestamp === event.timestamp && e.event === event.event)) {
            return prev;
          }
          return [...prev, event].sort((a, b) =>
            (a.timestamp || '').localeCompare(b.timestamp || ''),
          );
        });
      },
    );
    return () => {
      window.clearTimeout(loadingTimeout);
      disconnect();
    };
  }, [project.runId]);

  useEffect(() => {
    if (modal !== 'journey' || !project.runId) return;
    setJourneyLoading(true);
    fetchAuditEvents(project.runId)
      .then(setAuditEvents)
      .catch(() => setAuditEvents([]))
      .finally(() => setJourneyLoading(false));
  }, [modal, project.runId]);

  useEffect(() => {
    navRef.current?.querySelector('[aria-current="step"]')?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'center',
    });
  }, [stageIndex]);

  useEffect(() => {
    if (modal !== 'flutter' || !project.runId) return;
    setFlutterLoading(true);
    fetchArtifact('build/flutter/manifest.json', project.runId)
      .then((res) => setFlutterManifest(res.content || ''))
      .catch(() => setFlutterManifest(''))
      .finally(() => setFlutterLoading(false));
  }, [modal, project.runId]);

  useEffect(() => {
    if (!flutterReady || !project.runId) return;
    let cancelled = false;
    const refresh = () => {
      getEmulatorStatus(project.runId)
        .then((status) => {
          if (!cancelled) setEmulatorStatus(status);
        })
        .catch(() => {
          if (!cancelled) setEmulatorStatus(null);
        });
    };
    refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [flutterReady, project.runId]);

  const handleStartEmulator = async () => {
    if (!project.runId || emulatorBusy) return;
    setEmulatorBusy(true);
    try {
      const status = await startEmulatorRun(project.runId);
      setEmulatorStatus(status);
    } catch (err) {
      setEmulatorStatus({
        status: 'failed',
        error: err instanceof Error ? err.message : 'Failed to start emulator',
      });
    } finally {
      setEmulatorBusy(false);
    }
  };

  const handleStopEmulator = async () => {
    if (!project.runId || emulatorBusy) return;
    setEmulatorBusy(true);
    try {
      const status = await stopEmulatorRun(project.runId);
      setEmulatorStatus(status);
    } catch (err) {
      setEmulatorStatus({
        status: 'failed',
        error: err instanceof Error ? err.message : 'Failed to stop emulator session',
      });
    } finally {
      setEmulatorBusy(false);
    }
  };

  const emulatorActive =
    emulatorStatus?.status === 'starting' || emulatorStatus?.status === 'running';

  useEffect(() => {
    if (modal !== 'brief' || !project.runId) return;
    let cancelled = false;
    setPrdLoading(true);
    setPrdContent('');
    setPrdMeta({ title: stageDoc.title, path: '' });

    const candidates = stageDoc.paths.length
      ? stageDoc.paths
      : stageDocumentCandidates(stageIndex, runState?.artifacts_index || []).paths;

    (async () => {
      for (const path of candidates) {
        try {
          const res = await fetchArtifact(path, project.runId);
          if (cancelled) return;
          if (res?.content) {
            setPrdContent(res.content);
            setPrdMeta({ title: stageDoc.title, path });
            setPrdLoading(false);
            return;
          }
        } catch {
          /* try next candidate */
        }
      }
      if (cancelled) return;
      // Fall back to the intake text for this run — never a shared leftover PRD.
      setPrdContent(project.text || '');
      setPrdMeta({
        title: stageDoc.title,
        path: project.text ? '(intake brief)' : '',
      });
      setPrdLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [modal, project.runId, project.text, stageIndex, stageDoc.title, stageDoc.paths.join('|'), runState?.artifacts_index]);

  const status = run.failed
    ? 'Failed'
    : done
      ? 'Delivered'
      : viewing
        ? stageIndex < run.active
          ? 'Completed'
          : 'Upcoming'
        : stageIndex === 7
          ? run.approval === 'approved'
            ? 'Approved'
            : 'Awaiting approval'
          : 'In progress';

  const fzWorkLabel = fzCurrentWorkLabel(runState);
  const footerProgress = buildProgressFooterLine(runState, project);
  const studioSubtitle = fzStudioSubtitle(runState, stage, stageIndex, lastStage, done);

  function review(i) {
    setView(i === run.active ? null : i);
  }

  function download() {
    const contents = JSON.stringify(
      {
        project: project.text,
        run_id: project.runId,
        attachments: project.files.map((f) => f.name),
        version: '1.0.0',
        approval: run.approval,
        pipeline: runState?.pipeline_steps,
        flutter_project_dir: runState?.flutter_project_dir || null,
        flutter_manifest: 'build/flutter/manifest.json',
      },
      null,
      2,
    );
    const url = URL.createObjectURL(new Blob([contents], { type: 'application/json' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `${displayName}-handover.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  if (runLoading && !runState) {
    return (
      <div className="app-shell">
        <header className="header dashboard-header">
          <Brand />
        </header>
        <main className="dashboard dashboard-loading">
          <p role="status">Connecting to factory run…</p>
        </main>
      </div>
    );
  }

  if (!runState) {
    return (
      <div className="app-shell">
        <header className="header dashboard-header">
          <Brand />
        </header>
        <main className="dashboard dashboard-loading">
          <p className="error" role="alert">
            Could not load run state. Check that the API is running on port 8001, then refresh.
          </p>
          <button type="button" className="secondary" onClick={onReset}>
            Back to intake
          </button>
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      {run.failed && (
        <div className="error-banner" role="alert">
          {runState?.status === 'stale'
            ? `Run interrupted: ${run.error || 'The factory worker is no longer running.'} You can resume from History (Generate another release) — no need to start over.`
            : `Run failed: ${run.error || 'The worker exited unexpectedly (see fz_worker log in artifacts/logs).'}. Try History → Generate another release, or start a new project.`}
        </div>
      )}
      <header className="header dashboard-header">
        <Brand />
        <nav className="stepper" aria-label="AI Factory stages" ref={navRef}>
          {stages.map((s, i) => {
            const completed = i < run.active || run.complete;
            const inProgress = !completed && i === run.active;
            return (
            <button
              key={s.key}
              className={`step ${i === stageIndex ? 'selected' : ''} ${completed ? 'completed' : ''} ${inProgress ? 'inprogress' : ''}`}
              aria-current={i === stageIndex ? 'step' : undefined}
              aria-label={`${s.key}, ${completed ? 'done' : inProgress ? 'in progress' : 'not started'}`}
              onClick={() => review(i)}
            >
              <span className="step-circle">
                {completed ? '✓' : <img src={s.icon} alt="" />}
              </span>
              <span className="step-label">
                {String(i + 1).padStart(2, '0')} {s.key}
              </span>
              {inProgress ? (
                <span className="agent-dock">
                  <i className="agent-arrow" aria-hidden="true" />
                  <span className="agent-row">
                    {(s.agents || [s.agent]).map((name, n) => (
                      <b
                        key={name}
                        className="agent-token"
                        style={{ animationDelay: `${n * 0.14}s` }}
                        title={name}
                      >
                        <i>
                          {String(name)
                            .split(' ')
                            .slice(0, 2)
                            .map((part) => part[0])
                            .join('')}
                        </i>
                      </b>
                    ))}
                  </span>
                </span>
              ) : null}
            </button>
            );
          })}
        </nav>
        <div className="header-actions dashboard-header-actions">
          <button type="button" className="secondary header-btn" onClick={onOpenHistory}>
            History
          </button>
          <div className="project-progress">
            <div>
              <span>Project progress</span>
              <b>{run.overall}%</b>
            </div>
            <Progress value={run.overall} label="Overall project progress" />
          </div>
        </div>
      </header>
      <main className="dashboard">
        <section className="factory-floor">
          <div className="stage-hero" key={stage.key}>
            <span className="eyebrow">
              STEP {stageIndex + 1} OF {stages.length}&nbsp; / &nbsp;{stage.key.toUpperCase()}
            </span>
            <h1>{stage.title}</h1>
            <p>{stage.description}</p>
            <div className="checklist">
              {stage.check.map((x, i) => (
                <span key={x}>
                  <i className={progress >= (i + 1) * 20 ? 'checked' : ''}>
                    {progress >= (i + 1) * 20 ? '✓' : '·'}
                  </i>
                  {x}
                </span>
              ))}
            </div>
          </div>
          <div className="agent-scene">
            {stages.map((s, i) => (
              <img
                key={s.key}
                src={s.image}
                alt={i === stageIndex ? `${s.key} specialist working in the AI Factory` : ''}
                aria-hidden={i !== stageIndex}
                className={i === stageIndex ? 'visible' : ''}
              />
            ))}
          </div>
          <div className={`agent-context${detailOpen ? ' open' : ''}`}>
            <div className="context-detail full-detail">
              <div className="context-detail-inner" ref={detailScrollRef}>
                <div className="context-detail-body">
                  <div className="detail-block detail-usage">
                    <small>Token usage · {stage.key}</small>
                    <UsageBanner
                      usage={stageUsage}
                      live={!run.complete && !run.failed}
                      stageLive={!viewing && !run.complete && !run.failed}
                    />
                  </div>
                  <div className="detail-block">
                    <small>{card1Title}</small>
                    <button
                      type="button"
                      className="detail-document"
                      onClick={() => setModal('brief')}
                    >
                      <img src="/assets/11e0d.svg" alt="" />
                      <span>
                        <b>{card1Name}</b>
                        <small>{card1Sub}</small>
                      </span>
                    </button>
                    <p>{card1Foot}</p>
                  </div>
                  <div className="detail-block">
                    <small>{stage.card2[0]}</small>
                    <div className="detail-features">
                      {featureLines.map((x, i) => (
                        <p className="detail-feature" key={x}>
                          <span>
                            {deliveryCopy
                              ? run.complete ||
                                (i === 0 && run.browserReady) ||
                                (i === 1 && run.checks?.qa_passed) ||
                                (i === 2 && run.complete)
                                ? '✓'
                                : ''
                              : progress >= (i + 1) * 30
                                ? '✓'
                                : ''}
                          </span>
                          {deliveryCopy
                            ? x
                            : stageIndex === lastStage && !done
                              ? x
                                  .replace('Complete', 'Preparing')
                                  .replace('Passed', 'Checking')
                                  .replace('Ready', 'Preparing')
                              : x}
                        </p>
                      ))}
                    </div>
                  </div>
                  <div className="detail-block">
                    <small>Iterations</small>
                    <div className="iteration-list">
                      {stageIterations.map((it) => (
                        <div
                          key={it.n}
                          className={`iteration-block${it.muted ? ' muted' : ''}${
                            it.status === 'In progress' ? ' live' : ''
                          }`}
                        >
                          <div className="iteration-head">
                            <b>
                              Iteration {it.n}
                              {it.reason ? ` · ${it.reason}` : ''}
                            </b>
                            <span>{it.status}</span>
                          </div>
                          {(it.timeLabel || it.summary) && (
                            <p>
                              {it.timeLabel ? `${it.timeLabel} · ` : ''}
                              {it.summary}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="agent-line">
              <b>{stage.agent}</b>
              <span className={done ? 'success' : run.failed ? 'error' : ''}>● {status}</span>
            </div>
            <div className="context-grid">
              <div>
                <small>{done ? 'Latest milestone' : 'Currently working on'}</small>
                <p>
                  {fzWorkLabel && !viewing && !done
                    ? fzWorkLabel
                    : stage.check[Math.min(4, Math.floor(progress / 20))]}
                </p>
              </div>
              <div>
                <small>Input</small>
                <p>{stageIndex === 0 && project.files.length ? project.files[0].name : stage.input}</p>
              </div>
              <div>
                <small>Output</small>
                <p>{stage.output}</p>
              </div>
            </div>
            <div className="detail-actions">
              {isFzEngine && project.runId ? (
                <>
                  <button
                    type="button"
                    className="icon-btn secondary"
                    title="Download SDLC dossier (HTML)"
                    aria-label="Download SDLC dossier HTML"
                    disabled={Boolean(dossierBusy)}
                    onClick={async () => {
                      if (!project.runId || dossierBusy) return;
                      setDossierBusy('html');
                      try {
                        await downloadRunDossier(project.runId, 'html');
                      } catch {
                        /* user can retry from History */
                      } finally {
                        setDossierBusy(null);
                      }
                    }}
                  >
                    {dossierBusy === 'html' ? '…' : '↓ HTML'}
                  </button>
                  <button
                    type="button"
                    className="icon-btn secondary"
                    title="Download SDLC dossier (PDF)"
                    aria-label="Download SDLC dossier PDF"
                    disabled={Boolean(dossierBusy)}
                    onClick={async () => {
                      if (!project.runId || dossierBusy) return;
                      setDossierBusy('pdf');
                      try {
                        await downloadRunDossier(project.runId, 'pdf');
                      } catch {
                        /* user can retry from History */
                      } finally {
                        setDossierBusy(null);
                      }
                    }}
                  >
                    {dossierBusy === 'pdf' ? '…' : '↓ PDF'}
                  </button>
                </>
              ) : null}
              <button
                type="button"
                className="detail-link"
                aria-expanded={detailOpen}
                onClick={() => setDetailOpen((open) => !open)}
              >
                {detailOpen ? 'Hide detail' : 'View detail'}
              </button>
            </div>
          </div>
        </section>
        <section className="application-studio">
          <div className="studio-heading">
            <div>
              <h2>{displayName}</h2>
              <p>{studioSubtitle}</p>
            </div>
            <span className={`status ${done ? 'success' : run.failed ? 'error' : ''}`}>● {status}</span>
          </div>
          <div className="device-area">
            <MobileFrame previewUrl={showPreview ? preview : null}>
              {showPreview ? null : done || (isFzEngine && flutterReady) ? (
                <ReadyApp />
              ) : (
                <StageSkeleton stage={stageIndex} progress={progress} />
              )}
            </MobileFrame>
            {gateInfo && (
              <div className="stage-actions">
                <button className="secondary" type="button" onClick={() => setGateOpen(true)}>
                  {gateInfo.label}
                </button>
                <small>Open the review pack for this stage.</small>
              </div>
            )}
            {stageIndex === 7 && !viewing && !run.complete && (
              <div className="stage-actions">
                <span className="approval-status">
                  Release approval: {run.approval || 'pending'}
                </span>
                <small>Approval is handled by the simulated client in the pipeline.</small>
              </div>
            )}
            {stageIndex === lastStage && showPreview && !done && (
              <div className="stage-actions">
                <button className="primary" onClick={() => setModal('app')}>
                  View application
                </button>
                <small>Live preview ready · finalizing handover package</small>
              </div>
            )}
           
            {done && (
              <div className="stage-actions">
                {!isFzEngine && (
                  <button className="primary" onClick={() => setModal('app')}>
                    View HTML preview
                  </button>
                )}
                {flutterReady && (
                  <button
                    className="primary"
                    onClick={handleStartEmulator}
                    disabled={emulatorBusy || emulatorActive}
                  >
                    {emulatorActive ? 'Launching on emulator…' : 'Run on emulator'}
                  </button>
                )}
                {flutterReady && (
                  <button
                    className="secondary"
                    onClick={() => setModal('flutter')}
                  >
                    View Flutter source
                  </button>
                )}
                <button className="secondary" onClick={() => setModal('journey')}>
                  Project journey
                </button>
              </div>
            )}
            {!done && flutterReady && (
              <div className="stage-actions">
                <button
                  className="primary"
                  onClick={handleStartEmulator}
                  disabled={emulatorBusy || emulatorActive}
                >
                  {emulatorActive ? 'Launching on emulator…' : 'Run on emulator'}
                </button>
                {emulatorActive && (
                  <button className="secondary" onClick={handleStopEmulator} disabled={emulatorBusy}>
                    Stop emulator
                  </button>
                )}
                <button className="secondary" onClick={() => setModal('flutter')}>
                  View Flutter source
                </button>
                {emulatorStatus?.status && emulatorStatus.status !== 'idle' && (
                  <small>
                    Emulator: {emulatorStatus.status}
                    {emulatorStatus.device_id ? ` · ${emulatorStatus.device_id}` : ''}
                    {emulatorStatus.error ? ` · ${emulatorStatus.error}` : ''}
                  </small>
                )}
              </div>
            )}
          </div>
          <div className="stage-progress">
            <div>
              <span>
                {done
                  ? 'Production release complete'
                  : stageIndex === lastStage
                    ? 'Preparing production release'
                    : stage.progress}
              </span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} label={`${stage.key} progress`} />
          </div>
        </section>
      </main>
      <footer className="demo-controls">
        <span>
          <i className={run.complete ? 'complete-dot' : 'live-dot'} />
          {run.failed ? 'Run failed' : run.complete ? 'Run complete' : 'Live run'}
          {footerProgress ? ` · ${footerProgress}` : ''}
        </span>
        <div>
          {viewing && (
            <button type="button" onClick={() => setView(null)}>
              Return to live stage
            </button>
          )}
          {run.complete && (
            <button type="button" onClick={download}>
              Download handover
            </button>
          )}
          <button type="button" onClick={() => setModal('restart')}>
            New project
          </button>
        </div>
      </footer>
      <div className="sr-only" aria-live="polite">
        {run.complete
          ? 'All stages complete. Your application is ready.'
          : `Current stage: ${stages[run.active].key}`}
      </div>
      {modal === 'brief' && (
        <Modal title={prdMeta.title || stageDoc.title} onClose={() => setModal(null)}>
          {prdMeta.path ? (
            <p className="usage-detail-meta" style={{ marginTop: 0 }}>
              {prdMeta.path}
            </p>
          ) : null}
          {prdLoading ? (
            <p>Loading {stageDoc.title}…</p>
          ) : prdContent ? (
            <pre className="brief-text artifact-content">{prdContent}</pre>
          ) : (
            <p className="brief-text">
              No {stageDoc.title.toLowerCase()} for this run yet. It will appear here when the
              agent writes it.
            </p>
          )}
          <h3>Attachments</h3>
          {project.files.length ? (
            project.files.map((f, i) => (
              <p key={i}>
                {f.name} · {f.size < 1024 ? `${f.size} B` : `${(f.size / 1024).toFixed(0)} KB`}
              </p>
            ))
          ) : (
            <p>No attachments</p>
          )}
        </Modal>
      )}
      {modal === 'flutter' && (
        <Modal title={`${displayName} · Flutter source`} onClose={() => setModal(null)}>
          <p className="brief-text">
            There is no live Flutter preview in the browser. The factory writes a Flutter
            project to disk — run it locally with the Flutter SDK or launch an emulator from here.
          </p>
          {flutterReady && (
            <div className="stage-actions">
              <button
                className="primary"
                onClick={handleStartEmulator}
                disabled={emulatorBusy || emulatorActive}
              >
                {emulatorActive ? 'Launching on emulator…' : 'Run on emulator'}
              </button>
              {emulatorActive && (
                <button className="secondary" onClick={handleStopEmulator} disabled={emulatorBusy}>
                  Stop
                </button>
              )}
            </div>
          )}
          {emulatorStatus?.status && emulatorStatus.status !== 'idle' && (
            <p className="brief-text">
              Emulator: <strong>{emulatorStatus.status}</strong>
              {emulatorStatus.device_id ? ` · ${emulatorStatus.device_id}` : ''}
              {emulatorStatus.note ? ` · ${emulatorStatus.note}` : ''}
              {emulatorStatus.error ? ` · ${emulatorStatus.error}` : ''}
            </p>
          )}
          {emulatorStatus?.log_tail && (
            <>
              <h3>Launch log</h3>
              <pre className="artifact-content">{emulatorStatus.log_tail}</pre>
            </>
          )}
          {flutterDir && (
            <p className="brief-text">
              Project folder: <code>{flutterDir}</code>
            </p>
          )}
          <pre className="brief-text">{`cd ${isFzEngine ? flutterDir || `ai_factory_fz/runs/${project.runId}/app` : `ai_factory/${flutterDir || `apps/${project.runId}/flutter`}`}
flutter pub get
flutter run`}</pre>
          {flutterLoading ? (
            <p>Loading manifest…</p>
          ) : flutterManifest ? (
            <>
              <h3>Manifest</h3>
              <pre className="artifact-content">{flutterManifest}</pre>
            </>
          ) : (
            <p>Manifest not ready yet — check again after the Delivery stage.</p>
          )}
        </Modal>
      )}
      {modal === 'app' && (
        <Modal title={`${displayName} · HTML preview`} onClose={() => setModal(null)}>
          <div className="app-modal">
            <MobileFrame previewUrl={preview} wide>
              {!preview && <ReadyApp />}
            </MobileFrame>
          </div>
        </Modal>
      )}
      {modal === 'journey' && (
        <Modal title="Project journey" onClose={() => setModal(null)}>
          <p className="journey-note">{journey.pipelineNote}</p>
          {journeyLoading ? (
            <p>Loading activity log…</p>
          ) : (
            <>
              <ol className="journey-stages">
                {stages.map((s, i) => (
                  <li key={s.key}>
                    <b>
                      {i <= run.active || run.complete ? '✓' : '○'} {s.key}
                    </b>
                    <span>{s.output}</span>
                  </li>
                ))}
              </ol>
              <h3 className="journey-activity-heading">Activity log</h3>
              <ol className="journey-activity">
                {journey.activities.length ? (
                  journey.activities.map((item) => (
                    <li key={item.id} className={item.passed ? 'pass' : 'warn'}>
                      <div className="journey-activity-head">
                        <b>{item.title}</b>
                        <span>{item.timeLabel}</span>
                      </div>
                      <small>
                        {item.stage} · {item.role} · {item.decision}
                      </small>
                      <p>{item.detail}</p>
                    </li>
                  ))
                ) : (
                  <li>
                    <p>No audit entries yet for this run.</p>
                  </li>
                )}
              </ol>
            </>
          )}
          <button className="primary" onClick={download}>
            Download handover
          </button>
        </Modal>
      )}
      {modal === 'restart' && (
        <Modal title="Start a new project?" onClose={() => setModal(null)}>
          <p>This clears the current session. The factory run continues in the background.</p>
          <div className="modal-actions">
            <button className="secondary" onClick={() => setModal(null)}>
              Keep this project
            </button>
            <button className="primary" onClick={onReset}>
              Start new project
            </button>
          </div>
        </Modal>
      )}
      {gateOpen && gateInfo?.kind === 'design' && (
        <MockupReview
          onClose={() => setGateOpen(false)}
          onApprove={() => setGateOpen(false)}
          onReject={() => setGateOpen(false)}
        />
      )}
      {gateOpen && gateInfo && gateInfo.kind !== 'design' && (
        <GateReview
          kind={gateInfo.kind}
          project={project}
          onClose={() => setGateOpen(false)}
          onApprove={() => setGateOpen(false)}
          onReject={() => setGateOpen(false)}
        />
      )}
    </div>
  );
}

export default function App() {
  const initialSession = typeof sessionStorage !== 'undefined' ? loadUiSession() : null;
  const [view, setView] = useState(initialSession ? 'dashboard' : 'intake');
  const [project, setProject] = useState(initialSession?.project ?? null);

  useEffect(() => {
    saveUiSession(view, project);
  }, [view, project]);

  function openHistory() {
    setView('history');
  }

  function openIntake() {
    setProject(null);
    setView('intake');
  }

  function startProject(next) {
    setProject(next);
    setView('dashboard');
  }

  async function openRun(run) {
    const runId = run?.run_id;
    if (!runId) return;
    try {
      const full = await getRun(runId);
      setProject(projectFromRunState(full || run));
    } catch {
      setProject(projectFromRunState(run));
    }
    setView('dashboard');
  }

  if (view === 'history') {
    return (
      <div className="app-shell app-shell-scroll">
        <History
          onOpenRun={openRun}
          onNewProject={openIntake}
          onGenerateRelease={openRun}
        />
      </div>
    );
  }

  if (view === 'dashboard' && project) {
    return (
      <Dashboard
        project={project}
        onReset={openIntake}
        onOpenHistory={openHistory}
      />
    );
  }

  return <Intake onStart={startProject} onOpenHistory={openHistory} />;
}
