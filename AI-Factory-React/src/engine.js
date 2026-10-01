import { GATE_HOLD, gateIndexes } from './gates.js';

const STAGE_COUNT = 11;
const GATE = STAGE_COUNT - 2;
const LAST = STAGE_COUNT - 1;

const ISSUES = [
  {
    id: 'spec-gap',
    at: 1,
    atProgress: 42,
    reopen: [0],
    paces: { 0: 1.75, 1: 0.55 },
    note: 'Customer clarification · Customer and Spec Writer are both working',
  },
  {
    id: 'backend-block',
    at: 5,
    atProgress: 36,
    reopen: [2, 3],
    paces: { 2: 0.6, 3: 1.65, 5: 1.05 },
    note: 'Build issue · Architect, UI/UX Designer and Backend Developer are working at different speeds',
  },
  {
    id: 'qa-build',
    at: 8,
    atProgress: 28,
    reopen: [5, 6],
    paces: { 5: 1.4, 6: 0.9, 8: 0.5 },
    note: 'QA failed · Backend and Frontend started rework; they will not finish together',
  },
  {
    id: 'qa-design',
    at: 8,
    atProgress: 62,
    reopen: [3],
    paces: { 3: 1.55, 8: 0.45 },
    note: 'QA found a design defect while other fixes are still open',
  },
];

function createInitialRun() {
  return {
    active: 0,
    progress: 0,
    progresses: Array(STAGE_COUNT).fill(0),
    statuses: ['active', ...Array(STAGE_COUNT - 1).fill('pending')],
    paces: Array(STAGE_COUNT).fill(1),
    paused: false,
    complete: false,
    approval: 'pending',
    revision: 0,
    fired: [],
    note: '',
    revisited: Array(STAGE_COUNT).fill(false),
    holds: Array(STAGE_COUNT).fill(0),
    decisions: {},
    reviewing: false,
  };
}

export const initialRun = createInitialRun();

function cloneStatuses(state) {
  if (state.statuses?.length === STAGE_COUNT) return state.statuses.slice();
  return Array.from({ length: STAGE_COUNT }, (_, i) => (state.complete || i < state.active ? 'done' : i === state.active ? 'active' : 'pending'));
}

function cloneProgresses(state) {
  if (state.progresses?.length === STAGE_COUNT) return state.progresses.slice();
  return Array.from({ length: STAGE_COUNT }, (_, i) => (i === state.active ? state.progress : i < state.active || state.complete ? 100 : 0));
}

function clonePaces(state) {
  if (state.paces?.length === STAGE_COUNT) return state.paces.slice();
  return Array(STAGE_COUNT).fill(1);
}

function cloneHolds(state) {
  return state.holds?.length === STAGE_COUNT ? state.holds.slice() : Array(STAGE_COUNT).fill(0);
}

function focusIndex(statuses) {
  const active = statuses.findIndex((status) => status === 'active');
  if (active !== -1) return active;
  const awaiting = statuses.findIndex((status) => status === 'awaiting');
  return awaiting === -1 ? LAST : awaiting;
}

function releaseReadyStages(statuses, progresses, paces) {
  const firstOpen = statuses.findIndex((status) => status !== 'done');
  if (firstOpen === -1) return true;
  if (statuses[firstOpen] === 'pending') {
    statuses[firstOpen] = 'active';
    progresses[firstOpen] = 0;
    paces[firstOpen] = 1;
  }
  return false;
}

export function advance(state, amount) {
  if (state.paused || state.complete) return state;
  const statuses = cloneStatuses(state);
  const progresses = cloneProgresses(state);
  const paces = clonePaces(state);
  const fired = state.fired ? state.fired.slice() : [];
  const revisited = state.revisited?.length === STAGE_COUNT ? state.revisited.slice() : Array(STAGE_COUNT).fill(false);
  const holds = cloneHolds(state);
  const decisions = { ...(state.decisions || {}) };
  let note = state.note || '';
  let approval = state.approval;
  const activeIndexes = statuses.flatMap((status, index) => (status === 'active' ? [index] : []));
  if (!activeIndexes.length && !statuses.includes('awaiting')) return state;

  for (const index of activeIndexes) {
    progresses[index] = Math.min(100, progresses[index] + amount * (paces[index] || 1));
  }

  for (const issue of ISSUES) {
    if (fired.includes(issue.id)) continue;
    if (statuses[issue.at] !== 'active' || progresses[issue.at] < issue.atProgress) continue;
    fired.push(issue.id);
    note = issue.note;
    for (const index of issue.reopen) {
      statuses[index] = 'active';
      progresses[index] = 0;
      holds[index] = 0;
    }
    for (const [index, pace] of Object.entries(issue.paces)) paces[Number(index)] = pace;
  }

  for (const index of activeIndexes) {
    if (progresses[index] < 100) continue;
    progresses[index] = 100;
    if (gateIndexes.includes(index)) {
      statuses[index] = 'awaiting';
      holds[index] = 0;
      continue;
    }
    statuses[index] = 'done';
    revisited[index] = true;
  }

  if (!state.reviewing) {
    statuses.forEach((status, index) => {
      if (status !== 'awaiting') return;
      holds[index] += amount;
      if (holds[index] < GATE_HOLD) return;
      statuses[index] = 'done';
      revisited[index] = true;
      holds[index] = 0;
      decisions[index] = { decision: 'auto-approved', comment: '' };
      if (index === GATE) approval = 'auto-approved';
    });
  }

  if (releaseReadyStages(statuses, progresses, paces)) {
    return { ...state, statuses, progresses, paces, fired, revisited, holds, decisions, note: '', progress: 100, active: LAST, complete: true, paused: true, approval };
  }

  const stillParallel = statuses.filter((status) => status === 'active').length > 1;
  const active = focusIndex(statuses);
  return {
    ...state,
    active,
    progress: progresses[active] ?? 0,
    progresses,
    statuses,
    paces,
    fired,
    revisited,
    holds,
    decisions,
    note: stillParallel ? note : '',
    approval,
    complete: false,
    paused: state.paused,
  };
}

export function runReducer(state, action) {
  switch (action.type) {
    case 'tick': return advance(state, action.amount);
    case 'pause': return { ...state, paused: !state.paused };
    case 'review': return state.reviewing === !!action.open ? state : { ...state, reviewing: !!action.open };
    case 'approve': {
      const index = Number.isInteger(action.index) ? action.index : GATE;
      if (!gateIndexes.includes(index)) return state;
      const statuses = cloneStatuses(state);
      if (statuses[index] !== 'active' && statuses[index] !== 'awaiting') return state;
      const progresses = cloneProgresses(state);
      const paces = clonePaces(state);
      const revisited = state.revisited?.length === STAGE_COUNT ? state.revisited.slice() : Array(STAGE_COUNT).fill(false);
      const holds = cloneHolds(state);
      statuses[index] = 'done';
      progresses[index] = 100;
      revisited[index] = true;
      holds[index] = 0;
      const decisions = { ...(state.decisions || {}), [index]: { decision: 'approved', comment: action.comment || '' } };
      const approval = index === GATE ? 'approved' : state.approval;
      if (releaseReadyStages(statuses, progresses, paces)) {
        return { ...state, statuses, progresses, paces, revisited, holds, decisions, note: '', progress: 100, active: LAST, complete: true, paused: true, approval, reviewing: false };
      }
      const active = focusIndex(statuses);
      return { ...state, active, progress: progresses[active] ?? 0, statuses, progresses, paces, revisited, holds, decisions, approval, paused: false, note: '', reviewing: false };
    }
    case 'reject': {
      const index = action.index;
      if (!gateIndexes.includes(index)) return state;
      const statuses = cloneStatuses(state);
      if (statuses[index] !== 'active' && statuses[index] !== 'awaiting') return state;
      const progresses = cloneProgresses(state);
      const revisited = state.revisited?.length === STAGE_COUNT ? state.revisited.slice() : Array(STAGE_COUNT).fill(false);
      const holds = cloneHolds(state);
      statuses[index] = 'active';
      progresses[index] = 0;
      revisited[index] = true;
      holds[index] = 0;
      const decisions = { ...(state.decisions || {}), [index]: { decision: 'rejected', comment: action.comment || '' } };
      return { ...state, active: index, progress: 0, statuses, progresses, revisited, holds, decisions, paused: false, complete: false, reviewing: false, note: '' };
    }
    case 'revise': {
      if (state.active !== GATE) return state;
      const revisited = Array(STAGE_COUNT).fill(false);
      for (let index = 0; index < GATE; index += 1) revisited[index] = true;
      const statuses = Array(STAGE_COUNT).fill('done');
      const progresses = Array(STAGE_COUNT).fill(100);
      statuses[5] = 'active';
      progresses[5] = 0;
      for (let index = 6; index < STAGE_COUNT; index += 1) {
        statuses[index] = 'pending';
        progresses[index] = 0;
      }
      return {
        ...createInitialRun(),
        active: 5,
        progress: 0,
        statuses,
        progresses,
        revision: state.revision + 1,
        paused: false,
        fired: ISSUES.map((issue) => issue.id),
        revisited,
      };
    }
    case 'reset': return createInitialRun();
    default: return state;
  }
}

export const overallProgress = (state) => {
  if (state.complete) return 100;
  const progresses = state.progresses?.length === STAGE_COUNT ? state.progresses : cloneProgresses(state);
  const statuses = state.statuses?.length === STAGE_COUNT ? state.statuses : cloneStatuses(state);
  const total = statuses.reduce((sum, status, index) => sum + (status === 'done' ? 100 : status === 'active' ? progresses[index] : 0), 0);
  return Math.min(99, Math.floor(total / STAGE_COUNT));
};

export function validateFiles(files) {
  const accepted = [], errors = [];
  for (const file of files) {
    if (!/\.(pdf|docx?|txt|md|png|jpe?g|webp)$/i.test(file.name)) errors.push(`${file.name}: use PDF, DOC/DOCX, TXT, MD, PNG, JPG or WebP.`);
    else if (file.size > 20 * 1024 * 1024) errors.push(`${file.name}: maximum size is 20 MB.`);
    else if (file.size === 0) errors.push(`${file.name}: this file is empty.`);
    else accepted.push(file);
  }
  return { accepted, errors };
}
