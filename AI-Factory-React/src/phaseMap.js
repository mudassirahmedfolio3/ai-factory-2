/** Maps 9 Figma UI stages to backend pipeline step IDs. */
export const UI_STAGE_BACKEND_IDS = [
  ['discovery'],
  ['discovery'],
  ['design'],
  ['design'],
  ['sprint'],
  ['build'],
  ['code_review', 'security', 'qa'],
  ['release', 'client_review'],
  ['browser'],
];

export const UI_STAGE_COUNT = UI_STAGE_BACKEND_IDS.length;

function stepStatusMap(pipelineSteps) {
  const map = new Map();
  for (const step of pipelineSteps || []) {
    map.set(step.id, step.status);
  }
  return map;
}

function idsForUiStage(uiIndex) {
  return UI_STAGE_BACKEND_IDS[uiIndex] || [];
}

/** Aggregate status for one UI stage from its backend step IDs. */
export function stageAggregateStatus(statusMap, uiIndex) {
  const ids = idsForUiStage(uiIndex);
  if (!ids.length) return 'pending';

  const statuses = ids.map((id) => statusMap.get(id) || 'pending');
  if (statuses.some((s) => s === 'failed')) return 'failed';
  if (statuses.every((s) => s === 'completed')) return 'completed';
  if (statuses.some((s) => s === 'active')) return 'active';
  return 'pending';
}

/** Progress 0–100 within a UI stage. */
export function stageProgress(statusMap, uiIndex) {
  const ids = idsForUiStage(uiIndex);
  if (!ids.length) return 0;

  const statuses = ids.map((id) => statusMap.get(id) || 'pending');
  const completed = statuses.filter((s) => s === 'completed').length;
  const hasActive = statuses.some((s) => s === 'active');

  if (completed === ids.length) return 100;
  if (hasActive) return Math.round(((completed + 0.6) / ids.length) * 100);
  if (completed > 0) return Math.round((completed / ids.length) * 100);
  return 0;
}

/** Active UI stage index from pipeline state. */
export function activeUiStage(runState) {
  const statusMap = stepStatusMap(runState?.pipeline_steps);

  for (let i = 0; i < UI_STAGE_COUNT; i++) {
    if (stageAggregateStatus(statusMap, i) === 'active') return i;
  }

  if (runState?.status === 'completed') return UI_STAGE_COUNT - 1;

  let lastCompleted = -1;
  for (let i = 0; i < UI_STAGE_COUNT; i++) {
    if (stageAggregateStatus(statusMap, i) === 'completed') lastCompleted = i;
  }
  if (lastCompleted >= 0 && lastCompleted < UI_STAGE_COUNT - 1) {
    return lastCompleted + 1;
  }
  return Math.max(0, lastCompleted);
}

/** Overall progress across all 9 UI stages. */
export function overallProgressFromState(runState) {
  if (runState?.status === 'completed') return 100;
  if (runState?.status === 'failed') {
    const statusMap = stepStatusMap(runState.pipeline_steps);
    let sum = 0;
    for (let i = 0; i < UI_STAGE_COUNT; i++) sum += stageProgress(statusMap, i);
    return Math.min(99, Math.floor(sum / UI_STAGE_COUNT));
  }

  const statusMap = stepStatusMap(runState?.pipeline_steps);
  let sum = 0;
  for (let i = 0; i < UI_STAGE_COUNT; i++) sum += stageProgress(statusMap, i);
  return Math.min(99, Math.floor(sum / UI_STAGE_COUNT));
}

/** Derive dashboard run object from backend RunState. */
export function runStateToDashboard(runState) {
  const statusMap = stepStatusMap(runState?.pipeline_steps);
  const active = activeUiStage(runState);
  const progress = stageProgress(statusMap, active);
  const complete = runState?.status === 'completed';
  const failed = runState?.status === 'failed';

  const browserDone = (statusMap.get('browser') || 'pending') === 'completed';

  return {
    active,
    progress,
    complete,
    failed,
    error: runState?.error || null,
    approval: runState?.approvals?.release || runState?.approvals?.prd || 'pending',
    browserReady: browserDone,
    projectName: runState?.project_name || 'Project',
    runId: runState?.run_id || null,
    phase: runState?.phase || '',
    overall: overallProgressFromState(runState),
  };
}

export function slugProjectName(text) {
  const line = (text || '').split('\n')[0].trim();
  if (!line) return 'ecommerce-app';
  const slug = line
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 48);
  return slug || 'ecommerce-app';
}

export function buildClientBrief(text, files) {
  let brief = (text || '').trim();
  if (files?.length) {
    const names = files.map((f) => f.name).join(', ');
    brief = brief
      ? `${brief}\n\nAttached files (reference only): ${names}`
      : `Requirements provided in attached files: ${names}`;
  }
  return brief;
}
