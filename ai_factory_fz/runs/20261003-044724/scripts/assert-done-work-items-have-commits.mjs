/**
 * BUG-003 guard: a work item may only be status=done when commit is a non-null hash.
 * Prevents silently losing deliverables when later reverts reset an uncommitted tree.
 */
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const statePath = join(root, 'state.json');

// state.json is run-local / gitignored in this factory layout; skip when absent.
if (!existsSync(statePath)) {
  console.log('OK: state.json not present; skipping done/commit invariant.');
  process.exit(0);
}

const state = JSON.parse(readFileSync(statePath, 'utf8'));
const workItems = state?.build?.work_items ?? {};

const violations = Object.entries(workItems).filter(([, item]) => {
  return item?.status === 'done' && (item.commit === null || item.commit === undefined || item.commit === '');
});

if (violations.length > 0) {
  const details = violations
    .map(([id, item]) => `${id}: status=${item.status}, commit=${JSON.stringify(item.commit)}`)
    .join('\n');
  console.error(
    'BUG-003: work items marked done without a commit hash:\n' + details,
  );
  process.exit(1);
}

console.log('OK: every done work item has a non-null commit hash.');
