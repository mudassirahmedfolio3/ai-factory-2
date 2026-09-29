import React, { useEffect, useRef, useState } from 'react';
import { stages, examples } from './data';
import { validateFiles } from './engine';
import { MobileFrame, StageSkeleton, ReadyApp } from './Phone';
import {
  ApiError,
  fetchRandomBrief,
  fetchArtifact,
  fetchAuditEvents,
  getCurrentRun,
  listComplexityOptions,
  previewUrl as buildPreviewUrl,
  startRun,
} from './api.js';
import {
  buildClientBrief,
  deliveryStageCopy,
  runStateToDashboard,
  slugProjectName,
} from './phaseMap.js';
import { buildProjectJourney } from './journeyMap.js';
import { connectRun } from './runSync.js';

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
    complexity: state.complexity || 'basic_plus',
    estimatedMinutes: state.estimated_minutes,
    projectName: state.project_name || 'Project',
  };
}

function Intake({ onStart }) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState([]);
  const [menu, setMenu] = useState(false);
  const [error, setError] = useState('');
  const [drag, setDrag] = useState(false);
  const [complexity, setComplexity] = useState('basic_plus');
  const [complexityOptions, setComplexityOptions] = useState([]);
  const [starting, setStarting] = useState(false);
  const [loadingBrief, setLoadingBrief] = useState(false);
  const [liveRun, setLiveRun] = useState(null);
  const input = useRef();
  const menuRef = useRef();

  useEffect(() => {
    getCurrentRun()
      .then((state) => {
        if (!state?.run_id) return;
        if (state.status === 'running' && state.is_live) setLiveRun(state);
        if (state.status === 'completed') setLiveRun({ ...state, completed: true });
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    listComplexityOptions()
      .then(setComplexityOptions)
      .catch(() =>
        setComplexityOptions([
          { id: 'basic', label: 'Basic', estimated_minutes: 10 },
          { id: 'basic_plus', label: 'Basic+', estimated_minutes: 25 },
          { id: 'standard', label: 'Standard', estimated_minutes: 60 },
          { id: 'full', label: 'Full', estimated_minutes: 120 },
        ]),
      );
  }, []);

  useEffect(() => {
    const close = (e) => {
      if (!menuRef.current?.contains(e.target)) setMenu(false);
    };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  }, []);

  const selectedProfile = complexityOptions.find((o) => o.id === complexity);

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
      const result = await startRun({ project_name, client_brief, complexity });
      onStart({
        runId: result.run_id,
        text: text.trim(),
        files,
        complexity: result.complexity || complexity,
        estimatedMinutes: result.estimated_minutes || selectedProfile?.estimated_minutes,
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
    <>
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
        <span className="eyebrow">NEW PROJECT</span>
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
          <div className="complexity-picker">
            <label htmlFor="complexity">Run complexity</label>
            <select
              id="complexity"
              value={complexity}
              onChange={(e) => setComplexity(e.target.value)}
            >
              {complexityOptions.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label} (~{o.estimated_minutes} min)
                </option>
              ))}
            </select>
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
        <p className="demo-note">
          Live run
          {selectedProfile ? ` · ~${selectedProfile.estimated_minutes} min` : ''} · Powered by CrewAI
        </p>
      </main>
    </>
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

function Dashboard({ project, onReset }) {
  const [runState, setRunState] = useState(null);
  const [view, setView] = useState(null);
  const [modal, setModal] = useState(null);
  const [prdContent, setPrdContent] = useState('');
  const [prdLoading, setPrdLoading] = useState(false);
  const [auditEvents, setAuditEvents] = useState([]);
  const [journeyLoading, setJourneyLoading] = useState(false);
  const navRef = useRef();

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
  const done = run.complete && stageIndex === 8;
  const preview = run.browserReady && project.runId ? buildPreviewUrl(project.runId) : null;
  const showPreview = Boolean(preview && (run.browserReady || run.complete));
  const displayName = runState?.project_name || project.projectName || 'Project';
  const deliveryCopy =
    stageIndex === 8 ? deliveryStageCopy(runState, displayName) : null;
  const journey = buildProjectJourney(auditEvents, runState);

  useEffect(() => {
    stages.forEach((s) => {
      const img = new Image();
      img.src = s.image;
    });
  }, []);

  useEffect(() => {
    const disconnect = connectRun(project.runId, setRunState, (event) => {
      setAuditEvents((prev) => {
        if (prev.some((e) => e.timestamp === event.timestamp && e.event === event.event)) {
          return prev;
        }
        return [...prev, event].sort((a, b) =>
          (a.timestamp || '').localeCompare(b.timestamp || ''),
        );
      });
    });
    return disconnect;
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
    if (modal !== 'brief' || !project.runId) return;
    setPrdLoading(true);
    const artifactPath =
      stageIndex === 8 ? 'releases/release_1_notes.md' : 'requirements/prd.md';
    fetchArtifact(artifactPath, project.runId)
      .then((res) => setPrdContent(res.content || ''))
      .catch(() => setPrdContent(''))
      .finally(() => setPrdLoading(false));
  }, [modal, project.runId, stageIndex]);

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

  return (
    <>
      {run.failed && (
        <div className="error-banner" role="alert">
          Run failed: {run.error || 'Unknown error'}. Start a new project to retry.
        </div>
      )}
      <header className="header dashboard-header">
        <Brand />
        <nav className="stepper" aria-label="AI Factory stages" ref={navRef}>
          {stages.map((s, i) => (
            <button
              key={s.key}
              className={`step ${i === stageIndex ? 'selected' : ''} ${i < run.active || run.complete ? 'completed' : ''}`}
              aria-current={i === stageIndex ? 'step' : undefined}
              onClick={() => review(i)}
            >
              <span className="step-circle">
                {i < run.active || run.complete ? '✓' : <img src={s.icon} alt="" />}
              </span>
              <span>
                {String(i + 1).padStart(2, '0')} {s.key}
              </span>
            </button>
          ))}
        </nav>
        <div className="project-progress">
          <div>
            <span>Project progress</span>
            <b>{run.overall}%</b>
          </div>
          <Progress value={run.overall} label="Overall project progress" />
        </div>
      </header>
      <main className="dashboard">
        <section className="factory-floor">
          <div className="stage-hero" key={stage.key}>
            <span className="eyebrow">
              STEP {stageIndex + 1} OF 9&nbsp; / &nbsp;{stage.key.toUpperCase()}
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
          <div className="agent-context">
            <div className="agent-line">
              <b>{stage.agent}</b>
              <span className={done ? 'success' : run.failed ? 'error' : ''}>● {status}</span>
            </div>
            <div className="context-grid">
              <div>
                <small>{done ? 'Latest milestone' : 'Currently working on'}</small>
                <p>{stage.check[Math.min(4, Math.floor(progress / 20))]}</p>
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
          </div>
        </section>
        <section className="application-studio">
          <div className="studio-heading">
            <div>
              <h2>{displayName}</h2>
              <p>
                {stage.key} ·{' '}
                {stageIndex === 8 && !done
                  ? 'Packaging the application for delivery'
                  : stage.right}
              </p>
            </div>
            <span className={`status ${done ? 'success' : run.failed ? 'error' : ''}`}>● {status}</span>
          </div>
          <div className="device-area">
            <MobileFrame previewUrl={showPreview ? preview : null}>
              {showPreview ? null : done ? (
                <ReadyApp />
              ) : (
                <StageSkeleton stage={stageIndex} progress={progress} />
              )}
            </MobileFrame>
            {stageIndex === 7 && !viewing && !run.complete && (
              <div className="stage-actions">
                <span className="approval-status">
                  Release approval: {run.approval || 'pending'}
                </span>
                <small>Approval is handled by the simulated client in the pipeline.</small>
              </div>
            )}
            {stageIndex === 8 && showPreview && !done && (
              <div className="stage-actions">
                <button className="primary" onClick={() => setModal('app')}>
                  View application
                </button>
                <small>Live preview ready · finalizing handover package</small>
              </div>
            )}
            {done && (
              <div className="stage-actions">
                <button className="primary" onClick={() => setModal('app')}>
                  View application
                </button>
                <button className="secondary" onClick={() => setModal('journey')}>
                  Project journey
                </button>
              </div>
            )}
          </div>
          <div className="stage-progress">
            <div>
              <span>
                {done
                  ? 'Production release complete'
                  : stageIndex === 8
                    ? 'Preparing production release'
                    : stage.progress}
              </span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} label={`${stage.key} progress`} />
          </div>
          <div className="info-cards">
            <article>
              <h3>{deliveryCopy?.card1Title || stage.card1[0]}</h3>
              <button className="document-card" onClick={() => setModal('brief')}>
                <img src="/assets/11e0d.svg" alt="" />
                <span>
                  <b>
                    {stageIndex === 0 && project.files.length
                      ? project.files[0].name
                      : deliveryCopy?.card1Name || stage.card1[1]}
                  </b>
                  <small>{deliveryCopy?.card1Sub || stage.card1[2]}</small>
                </span>
              </button>
              <p>
                {deliveryCopy?.card1Foot ||
                  (done
                    ? 'Handover package ready'
                    : stageIndex === 8
                      ? 'Packaging source, build and documentation'
                      : stage.card1[3])}
              </p>
            </article>
            <article>
              <h3>{stage.card2[0]}</h3>
              {(deliveryCopy?.deployLines || stage.card2.slice(1)).map((x, i) => (
                <p className="feature" key={x}>
                  <span>
                    {deliveryCopy
                      ? run.complete || (i === 0 && run.browserReady) || (i === 1 && run.checks?.qa_passed) || (i === 2 && run.complete)
                        ? '✓'
                        : ''
                      : progress >= (i + 1) * 30
                        ? '✓'
                        : ''}
                  </span>
                  {deliveryCopy
                    ? x
                    : stageIndex === 8 && !done
                      ? x
                          .replace('Complete', 'Preparing')
                          .replace('Passed', 'Checking')
                          .replace('Ready', 'Preparing')
                      : x}
                </p>
              ))}
            </article>
          </div>
        </section>
      </main>
      <footer className="demo-controls">
        <span>
          <i className={run.complete ? 'complete-dot' : 'live-dot'} />
          {run.failed ? 'Run failed' : run.complete ? 'Run complete' : 'Live run'}
          {project.estimatedMinutes ? ` · ~${project.estimatedMinutes} min` : ''}
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
          ? 'All nine stages complete. Your application is ready.'
          : `Current stage: ${stages[run.active].key}`}
      </div>
      {modal === 'brief' && (
        <Modal
          title={stageIndex === 8 ? 'Release notes' : 'Project brief'}
          onClose={() => setModal(null)}
        >
          {prdLoading ? (
            <p>{stageIndex === 8 ? 'Loading release notes…' : 'Loading PRD…'}</p>
          ) : prdContent ? (
            <pre className="brief-text artifact-content">{prdContent}</pre>
          ) : (
            <p className="brief-text">{project.text || 'Requirements provided in the attached documents.'}</p>
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
      {modal === 'app' && (
        <Modal title={`${displayName} · Preview`} onClose={() => setModal(null)}>
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
    </>
  );
}

export default function App() {
  const [project, setProject] = useState(null);
  return project ? (
    <Dashboard project={project} onReset={() => setProject(null)} />
  ) : (
    <Intake onStart={setProject} />
  );
}
