import test from 'node:test';
import assert from 'node:assert/strict';
import {
  activeUiStage,
  overallProgressFromState,
  runStateToDashboard,
  stageProgress,
  slugProjectName,
  buildClientBrief,
} from '../src/phaseMap.js';

const discoveryActive = {
  status: 'running',
  pipeline_steps: [
    { id: 'discovery', label: 'Discovery', status: 'active' },
    { id: 'design', label: 'Design', status: 'pending' },
    { id: 'sprint', label: 'Sprint', status: 'pending' },
    { id: 'build', label: 'Build', status: 'pending' },
    { id: 'code_review', label: 'Code Review', status: 'pending' },
    { id: 'security', label: 'Security', status: 'pending' },
    { id: 'qa', label: 'QA', status: 'pending' },
    { id: 'release', label: 'Release', status: 'pending' },
    { id: 'browser', label: 'Browser', status: 'pending' },
    { id: 'client_review', label: 'Client Review', status: 'pending' },
  ],
};

test('activeUiStage maps discovery to UI stage 0 or 1', () => {
  const idx = activeUiStage(discoveryActive);
  assert.ok(idx === 0 || idx === 1);
});

test('stageProgress returns partial progress for active QA substeps', () => {
  const statusMap = new Map([
    ['code_review', 'completed'],
    ['security', 'active'],
    ['qa', 'pending'],
  ]);
  const progress = stageProgress(statusMap, 6);
  assert.ok(progress > 0 && progress < 100);
});

test('runStateToDashboard marks complete when status completed', () => {
  const dash = runStateToDashboard({
    status: 'completed',
    project_name: 'test-app',
    pipeline_steps: discoveryActive.pipeline_steps.map((s) => ({
      ...s,
      status: 'completed',
    })),
  });
  assert.equal(dash.complete, true);
  assert.equal(dash.active, 8);
});

test('overallProgressFromState reaches 100 when completed', () => {
  assert.equal(
    overallProgressFromState({
      status: 'completed',
      pipeline_steps: [],
    }),
    100,
  );
});

test('slugProjectName creates kebab-case slug', () => {
  assert.equal(slugProjectName('Build An Online Store'), 'build-an-online-store');
});

test('buildClientBrief appends attachment names', () => {
  const brief = buildClientBrief('Hello', [{ name: 'req.pdf' }]);
  assert.match(brief, /req\.pdf/);
});
