import test from 'node:test';
import assert from 'node:assert/strict';
import {
  activeUiStage,
  buildCompleteFromState,
  deliveryStageCopy,
  filterUsageForStage,
  flutterRunReadyFromState,
  overallProgressFromState,
  previewReadyFromState,
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

test('previewReadyFromState is true when post_deploy_passed', () => {
  assert.equal(
    previewReadyFromState({
      status: 'running',
      checks: { post_deploy_passed: true },
      pipeline_steps: [{ id: 'browser', status: 'active' }],
    }),
    true,
  );
});

test('buildCompleteFromState is true when build step completed', () => {
  const steps = discoveryActive.pipeline_steps.map((step) =>
    step.id === 'build' ? { ...step, status: 'completed' } : step,
  );
  assert.equal(buildCompleteFromState({ status: 'running', pipeline_steps: steps }), true);
  assert.equal(buildCompleteFromState(discoveryActive), false);
});

test('flutterRunReadyFromState waits for build completion on fz runs', () => {
  const buildDone = discoveryActive.pipeline_steps.map((step) =>
    step.id === 'build' ? { ...step, status: 'completed' } : step,
  );
  assert.equal(
    flutterRunReadyFromState({
      factory_engine: 'fz',
      status: 'running',
      pipeline_steps: buildDone,
      checks: { flutter_artifacts_ready: true },
    }),
    true,
  );
  assert.equal(
    flutterRunReadyFromState({
      factory_engine: 'fz',
      status: 'running',
      pipeline_steps: discoveryActive.pipeline_steps,
      checks: { flutter_artifacts_ready: true },
    }),
    false,
  );
});

test('runStateToDashboard exposes browserReady from post_deploy checks', () => {
  const dash = runStateToDashboard({
    status: 'running',
    checks: { post_deploy_passed: true, qa_passed: true },
    pipeline_steps: discoveryActive.pipeline_steps,
  });
  assert.equal(dash.browserReady, true);
});

test('deliveryStageCopy uses project name and release number', () => {
  const copy = deliveryStageCopy(
    {
      status: 'running',
      release_number: 1,
      checks: { post_deploy_passed: true, flutter_artifacts_ready: true },
    },
    'womens-jewellery',
  );
  assert.match(copy.card1Name, /womens-jewellery/);
  assert.match(copy.deployLines[0], /Flutter project/);
  assert.match(copy.deployLines[1], /HTML preview/);
});

test('filterUsageForStage keeps only that stage agents', () => {
  const usage = {
    provider: 'agentic_sdlc',
    token_budget: 0,
    activities: [
      { id: '1', agent: 'customer', task: 'customer_brief', total_tokens: 10 },
      { id: '2', agent: 'spec_writer', task: 'write_prd', total_tokens: 20 },
      { id: '3', agent: 'architect', task: 'architecture', total_tokens: 30 },
    ],
  };
  const spec = filterUsageForStage(usage, 1);
  assert.equal(spec.activities.length, 1);
  assert.equal(spec.activities[0].agent, 'spec_writer');
  assert.equal(spec.llm_calls, 1);
  assert.equal(spec.total_tokens, 20);

  const arch = filterUsageForStage(usage, 2);
  assert.equal(arch.activities.length, 1);
  assert.equal(arch.activities[0].agent, 'architect');
});
