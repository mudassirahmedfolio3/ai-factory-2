/** Group audit events into per-UI-stage visit iterations. */

/** Audit event name → UI stage indices (0–10). */
export const EVENT_UI_STAGES = {
  project_kickoff: [0],
  prd_review: [1],
  build: [5, 6],
  developer_fix: [5, 6],
  code_review: [8],
  security: [8],
  qa: [8],
  preview_qa: [9],
  flutter_artifacts: [7],
  browser_preview: [10],
  release_review: [10],
};

const REVISIT_REASONS = {
  qa: 'revisit after QA',
  preview_qa: 'revisit after QA',
  code_review: 'revisit after code review',
  security: 'revisit after security',
};

function formatTime(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function eventUiStages(eventName) {
  return EVENT_UI_STAGES[eventName] || [];
}

function shortSummary(event) {
  const d = event.details || {};
  const decision = event.decision || '';
  if (d.summary) return d.summary;
  if (d.note) return d.note;
  if (decision) return `${event.event}: ${decision}`;
  return event.event || 'Activity';
}

function iterationStatus(events, { isLiveStage, progress, complete, failed, isLast }) {
  if (failed && isLast) return 'Failed';
  if (complete && isLast) return 'Complete';
  if (isLiveStage && isLast && progress > 0 && progress < 100) return 'In progress';
  const last = events[events.length - 1];
  const decision = String(last?.decision || '').toLowerCase();
  if (['fail', 'rejected', 'skipped'].includes(decision)) return 'Needs work';
  if (events.length) return 'Complete';
  if (progress >= 100) return 'Complete';
  if (progress > 0) return 'In progress';
  return 'Pending';
}

function leaveReason(leaveEventName) {
  return REVISIT_REASONS[leaveEventName] || 'revisit';
}

/**
 * Build oldest→newest iteration blocks for one UI stage.
 *
 * @param {Array} auditEvents
 * @param {number} stageIndex
 * @param {{ isLiveStage?: boolean, progress?: number, complete?: boolean, failed?: boolean, future?: boolean }} opts
 */
export function buildStageIterations(auditEvents, stageIndex, opts = {}) {
  const {
    isLiveStage = false,
    progress = 0,
    complete = false,
    failed = false,
    future = false,
  } = opts;

  if (future) {
    return [
      {
        n: 1,
        reason: 'Not started',
        status: 'Pending',
        timeLabel: '',
        summary: 'This stage has not started yet.',
        muted: true,
      },
    ];
  }

  const events = [...(auditEvents || [])].sort((a, b) =>
    (a.timestamp || '').localeCompare(b.timestamp || ''),
  );

  const visits = [];
  let inStage = false;
  let open = null;
  let lastLeaveEvent = null;

  for (const event of events) {
    const mapped = eventUiStages(event.event);
    if (!mapped.length) continue;

    const matches = mapped.includes(stageIndex);
    if (matches) {
      if (!inStage) {
        const n = visits.length + 1;
        open = {
          n,
          reason: n === 1 ? 'first pass' : leaveReason(lastLeaveEvent),
          events: [],
        };
        visits.push(open);
        inStage = true;
      }
      open.events.push(event);
    } else if (inStage) {
      lastLeaveEvent = event.event;
      inStage = false;
      open = null;
    }
  }

  if (!visits.length) {
    if (progress <= 0 && !isLiveStage && !complete) {
      return [
        {
          n: 1,
          reason: 'Not started',
          status: 'Pending',
          timeLabel: '',
          summary: 'This stage has not started yet.',
          muted: true,
        },
      ];
    }
    return [
      {
        n: 1,
        reason: 'first pass',
        status: iterationStatus([], {
          isLiveStage,
          progress,
          complete,
          failed,
          isLast: true,
        }),
        timeLabel: '',
        summary: isLiveStage
          ? 'Live pass in progress.'
          : complete || progress >= 100
            ? 'Stage completed.'
            : 'Stage activity recorded.',
        muted: false,
      },
    ];
  }

  return visits.map((visit, i) => {
    const isLast = i === visits.length - 1;
    const first = visit.events[0];
    const last = visit.events[visit.events.length - 1];
    return {
      n: visit.n,
      reason: visit.reason,
      status: iterationStatus(visit.events, {
        isLiveStage,
        progress,
        complete,
        failed,
        isLast,
      }),
      timeLabel: formatTime(first?.timestamp || last?.timestamp),
      summary: shortSummary(last || first),
      muted: false,
    };
  });
}
