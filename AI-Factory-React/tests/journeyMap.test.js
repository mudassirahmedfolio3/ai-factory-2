import test from 'node:test';
import assert from 'node:assert/strict';
import { buildProjectJourney } from '../src/journeyMap.js';

test('buildProjectJourney explains preview QA and developer fix', () => {
  const { activities, pipelineNote } = buildProjectJourney(
    [
      {
        timestamp: '2026-09-29T10:00:00+00:00',
        event: 'build',
        decision: 'completed',
        agent: 'software_engineer',
        details: { summary: 'Dart sketch delivered.' },
      },
      {
        timestamp: '2026-09-29T10:05:00+00:00',
        event: 'qa',
        decision: 'stub_pass',
        agent: 'qa_engineer',
        details: { note: 'Backend only.' },
      },
      {
        timestamp: '2026-09-29T10:06:00+00:00',
        event: 'preview_qa',
        decision: 'fail',
        agent: 'qa_engineer',
        details: {
          js_valid_before: false,
          js_valid_after: true,
          repairs: ['Auto-repaired JavaScript syntax'],
        },
      },
      {
        timestamp: '2026-09-29T10:06:01+00:00',
        event: 'developer_fix',
        decision: 'applied',
        agent: 'ui_designer',
        details: { fixes: ['Auto-repaired JavaScript syntax'] },
      },
    ],
    { complexity: 'basic' },
  );

  assert.match(pipelineNote, /Flutter project/i);
  assert.equal(activities.length, 4);
  assert.match(activities[2].detail, /invalid/i);
  assert.match(activities[3].detail, /Auto-repaired/i);
});
