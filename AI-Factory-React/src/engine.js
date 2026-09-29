export const initialRun = { active: 0, progress: 0, paused: false, complete: false, approval: 'pending', revision: 0 };
export function advance(state, amount) {
  if (state.paused || state.complete) return state;
  const progress = state.progress + amount;
  if (progress < 100) return { ...state, progress };
  if (state.active === 8) return { ...state, progress: 100, complete: true, paused: true };
  return { ...state, active: state.active + 1, progress: 0, approval: state.active === 7 ? 'auto-approved' : state.approval };
}
export function runReducer(state, action) {
  switch (action.type) {
    case 'tick': return advance(state, action.amount);
    case 'pause': return { ...state, paused: !state.paused };
    case 'approve': return state.active === 7 ? { ...state, active: 8, progress: 0, approval: 'approved', paused: false } : state;
    case 'revise': return state.active === 7 ? { ...initialRun, active: 5, revision: state.revision + 1 } : state;
    case 'reset': return { ...initialRun };
    default: return state;
  }
}
export const overallProgress = state => state.complete ? 100 : Math.min(99, Math.floor((state.active * 100 + state.progress) / 9));
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
