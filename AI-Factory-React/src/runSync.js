import { subscribeEvents, getCurrentRun, getRun } from './api.js';
import { runStateToDashboard } from './phaseMap.js';

export { runStateToDashboard };

function loadRunState(runId) {
  return getRun(runId).catch(() => getCurrentRun());
}

/** Poll + SSE hook helper — returns unsubscribe function. */
export function connectRun(runId, onRunState, onAudit) {
  let stopped = false;

  loadRunState(runId)
    .then((state) => {
      if (!stopped && state?.run_id === runId) onRunState(state);
    })
    .catch(() => {});

  const unsubscribe = subscribeEvents(
    runId,
    (state) => {
      if (!stopped && state?.run_id === runId) onRunState(state);
    },
    (event) => {
      if (!stopped && onAudit) onAudit(event);
    },
  );

  return () => {
    stopped = true;
    unsubscribe();
  };
}
