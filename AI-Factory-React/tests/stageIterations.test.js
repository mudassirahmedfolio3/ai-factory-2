import test from 'node:test';
import assert from 'node:assert/strict';
import { buildStageIterations } from '../src/stageIterations.js';

test('single pass shows Iteration 1 first pass', () => {
  const iterations = buildStageIterations(
    [
      {
        timestamp: '2026-10-01T10:00:00+00:00',
        event: 'build',
        decision: 'completed',
        details: { summary: 'APIs delivered.' },
      },
    ],
    5,
    { progress: 100, complete: false },
  );

  assert.equal(iterations.length, 1);
  assert.equal(iterations[0].n, 1);
  assert.equal(iterations[0].reason, 'first pass');
  assert.match(iterations[0].summary, /APIs delivered/);
});

test('QA then developer_fix creates revisit after QA on build stage', () => {
  const iterations = buildStageIterations(
    [
      {
        timestamp: '2026-10-01T10:00:00+00:00',
        event: 'build',
        decision: 'completed',
        details: { summary: 'First build.' },
      },
      {
        timestamp: '2026-10-01T10:05:00+00:00',
        event: 'qa',
        decision: 'fail',
        details: { note: 'Broken flow.' },
      },
      {
        timestamp: '2026-10-01T10:10:00+00:00',
        event: 'developer_fix',
        decision: 'applied',
        details: { summary: 'Fixed defects.' },
      },
    ],
    5,
    { progress: 100 },
  );

  assert.equal(iterations.length, 2);
  assert.equal(iterations[0].reason, 'first pass');
  assert.equal(iterations[1].n, 2);
  assert.equal(iterations[1].reason, 'revisit after QA');
  assert.match(iterations[1].summary, /Fixed defects/);
});

test('future stage returns muted Not started', () => {
  const iterations = buildStageIterations([], 9, { future: true, progress: 0 });
  assert.equal(iterations.length, 1);
  assert.equal(iterations[0].reason, 'Not started');
  assert.equal(iterations[0].muted, true);
});

test('live mid-pass marks latest iteration In progress', () => {
  const iterations = buildStageIterations(
    [
      {
        timestamp: '2026-10-01T10:00:00+00:00',
        event: 'build',
        decision: 'completed',
        details: { summary: 'Working…' },
      },
    ],
    5,
    { isLiveStage: true, progress: 40 },
  );

  assert.equal(iterations[0].status, 'In progress');
});

test('no audit but stage progress still yields Iteration 1', () => {
  const iterations = buildStageIterations([], 2, { progress: 100 });
  assert.equal(iterations.length, 1);
  assert.equal(iterations[0].n, 1);
  assert.equal(iterations[0].reason, 'first pass');
});
