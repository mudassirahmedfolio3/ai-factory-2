import { useCallback, useEffect, useState } from "react";
import {
  getCurrentRun,
  getRun,
  listRuns,
  startRun,
  subscribeEvents,
} from "./api";
import ActivityFeed from "./components/ActivityFeed";
import ArtifactPanel from "./components/ArtifactPanel";
import NewRunModal from "./components/NewRunModal";
import PipelineBoard from "./components/PipelineBoard";
import type { AuditEvent, RunState } from "./types";

function activeStepId(state: RunState | null): string | undefined {
  if (!state?.pipeline_steps) return undefined;
  return state.pipeline_steps.find((s) => s.status === "active")?.id;
}

export default function App() {
  const [runs, setRuns] = useState<RunState[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runState, setRunState] = useState<RunState | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRuns = useCallback(async () => {
    try {
      const data = await listRuns();
      setRuns(data);
    } catch {
      setRuns([]);
    }
  }, []);

  const loadRun = useCallback(async (runId: string | null) => {
    try {
      if (!runId) {
        const current = await getCurrentRun();
        setRunState(current);
        setSelectedRunId(current.run_id);
        return;
      }
      const run = await getRun(runId);
      setRunState(run);
    } catch {
      setRunState(null);
    }
  }, []);

  useEffect(() => {
    loadRuns();
    getCurrentRun()
      .then((r) => {
        if (r.status === "idle" || !r.run_id) {
          setRunState(null);
          return;
        }
        setSelectedRunId(r.run_id);
        setRunState(r);
      })
      .catch(() => setRunState(null));
  }, [loadRuns]);

  useEffect(() => {
    if (selectedRunId) loadRun(selectedRunId);
  }, [selectedRunId, loadRun]);

  useEffect(() => {
    const unsub = subscribeEvents(
      selectedRunId,
      (state) => {
        setRunState(state);
        loadRuns();
      },
      (ev) => setEvents((prev) => [...prev, ev]),
    );
    return unsub;
  }, [selectedRunId, loadRuns]);

  const handleStartRun = async (data: {
    project_name: string;
    client_brief: string;
    complexity: "basic" | "basic_plus" | "standard" | "full";
    max_releases?: number;
  }) => {
    setStarting(true);
    setError(null);
    setEvents([]);
    try {
      const result = await startRun(data);
      setSelectedRunId(result.run_id);
      setModalOpen(false);
      await loadRuns();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start run");
    } finally {
      setStarting(false);
    }
  };

  const isLive = runState?.status === "running";
  const isStale = runState?.status === "stale";

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-900/80 px-6 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">AI Factory Console</h1>
            <p className="text-sm text-slate-400">
              Live SDLC pipeline · code review · QA · security · browser preview
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              value={selectedRunId ?? ""}
              onChange={(e) => setSelectedRunId(e.target.value || null)}
            >
              <option value="">Current / latest</option>
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.project_name} — {r.run_id} ({r.status})
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500"
            >
              + New Run
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-4 p-6">
        {error && (
          <div className="rounded-lg border border-red-800 bg-red-950/50 px-4 py-2 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3">
          {isLive && (
            <span className="flex items-center gap-2 text-sm text-cyan-300">
              <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
              Live
            </span>
          )}
          {isStale && (
            <span className="text-sm text-amber-400">
              Stale — no updates in 30+ min. Start a new run.
            </span>
          )}
          {runState?.status === "failed" && runState.error && (
            <span className="text-sm text-red-400">{runState.error}</span>
          )}
          <span className="text-sm text-slate-300">
            {runState?.project_name ?? "No run selected"}
          </span>
          {runState && (
            <>
              {runState.complexity && (
                <span className="text-xs capitalize text-slate-500">
                  {runState.complexity}
                  {runState.estimated_minutes != null && ` · ~${runState.estimated_minutes} min`}
                </span>
              )}
              <span className="text-xs text-slate-500">Release {runState.release_number}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  runState.status === "completed"
                    ? "bg-emerald-900 text-emerald-300"
                    : runState.status === "failed"
                      ? "bg-red-900 text-red-300"
                      : runState.status === "running"
                        ? "bg-cyan-900 text-cyan-300"
                        : "bg-slate-800 text-slate-400"
                }`}
              >
                {runState.status}
              </span>
            </>
          )}
          {runState?.approvals && (
            <div className="ml-auto flex gap-2 text-xs text-slate-400">
              <span>PRD: {runState.approvals.prd ?? "—"}</span>
              <span>Release: {runState.approvals.release ?? "—"}</span>
              <span>Deploy: {runState.approvals.deploy ?? "—"}</span>
            </div>
          )}
        </div>

        {runState && (
          <PipelineBoard steps={runState.pipeline_steps ?? []} phase={runState.phase} />
        )}

        <div className="grid min-h-[28rem] grid-cols-1 gap-4 lg:grid-cols-2">
          <ActivityFeed events={events} />
          <ArtifactPanel
            artifacts={runState?.artifacts_index ?? []}
            runId={runState?.is_live === false ? runState.run_id : selectedRunId ?? undefined}
            activePhase={activeStepId(runState)}
          />
        </div>
      </main>

      <NewRunModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleStartRun}
        loading={starting}
      />
    </div>
  );
}
