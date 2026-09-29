import { subscribeEvents, getCurrentRun } from './api.js';
import { runStateToDashboard } from './phaseMap.js';

export { runStateToDashboard };

/** Poll + SSE hook helper — returns unsubscribe function. */
export function connectRun(runId, onRunState, onAudit) {
  let stopped = false;

  getCurrentRun()
    .then((state) => {
      if (!stopped && state?.run_id === runId) onRunState(state);
    })
    .catch(() => {});

  const unsubscribe = subscribeEvents(
    runId,
    (state) => {
      if (!stopped) onRunState(state);
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
