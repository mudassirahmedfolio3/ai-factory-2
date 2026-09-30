/** Map audit events to human-readable project journey activities. */

const EVENT_META = {
  project_kickoff: {
    stage: 'Requirement',
    role: 'Flow Orchestrator',
    title: 'Project kickoff',
  },
  prd_review: {
    stage: 'Business Analyst',
    role: 'Business Analyst',
    title: 'PRD review',
  },
  build: {
    stage: 'Developer',
    role: 'Software Engineer',
    title: 'Implementation',
  },
  code_review: {
    stage: 'QA',
    role: 'Code Reviewer',
    title: 'Code review',
  },
  security: {
    stage: 'QA',
    role: 'Security Engineer',
    title: 'Security scan',
  },
  qa: {
    stage: 'QA',
    role: 'QA Engineer',
    title: 'Quality assurance',
  },
  preview_qa: {
    stage: 'QA',
    role: 'QA Engineer',
    title: 'Browser preview validation',
  },
  developer_fix: {
    stage: 'Developer',
    role: 'UI Designer / Engineer',
    title: 'Defect remediation',
  },
  flutter_artifacts: {
    stage: 'Build',
    role: 'Flutter Engineer',
    title: 'Flutter project generated',
  },
  browser_preview: {
    stage: 'Delivery',
    role: 'Release Engineer',
    title: 'Browser preview deployed',
  },
  release_review: {
    stage: 'UAT',
    role: 'Product Reviewer',
    title: 'Release approval',
  },
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

function detailForEvent(event) {
  const d = event.details || {};
  const decision = event.decision || '';

  switch (event.event) {
    case 'project_kickoff':
      return `Started ${d.project || 'project'} (${d.complexity || 'standard'}, ~${d.estimated_minutes || '?'} min).`;
    case 'prd_review':
      return decision === 'approved'
        ? 'PRD approved — scope locked for build.'
        : `PRD review: ${decision}. ${(d.feedback || []).join(' ') || ''}`.trim();
    case 'build':
      return d.summary || `Delivered ${d.artifact || 'build artifacts'} (${d.lines || '?'} lines).`;
    case 'code_review':
      return d.note || `Code review ${decision}.`;
    case 'security':
      return d.note || `Security scan ${decision}.`;
    case 'qa':
      if (decision === 'stub_pass') {
        return (
          d.note ||
          'Backend smoke tests auto-passed at Basic complexity. HTML preview checked separately.'
        );
      }
      return `QA verdict: ${decision}. ${d.artifact ? `Report: ${d.artifact}` : ''}`.trim();
    case 'preview_qa': {
      const parts = [
        `Validated mobile HTML preview (${d.scope || 'browser_html'}).`,
        `JS syntax before repair: ${d.js_valid_before ? 'valid' : 'invalid'}.`,
        `JS syntax after repair: ${d.js_valid_after ? 'valid' : 'invalid'}.`,
      ];
      if (d.repairs?.length) {
        parts.push(`Issues found: ${d.repairs.join('; ')}.`);
      }
      return parts.join(' ');
    }
    case 'developer_fix':
      return `${d.summary || 'Applied fixes.'} ${(d.fixes || []).join('; ')}`;
    case 'flutter_artifacts':
      return (
        d.summary ||
        `Flutter project at ${d.project_dir || 'apps/{run_id}/flutter'} (${d.file_count || '?'} files). Manifest: ${d.manifest || 'build/flutter/manifest.json'}.`
      );
    case 'browser_preview':
      return `Preview served at ${d.url || 'local path'}. Files: ${d.preview_dir || 'apps/{run_id}/index.html'}.`;
    case 'release_review':
      return decision === 'approved'
        ? 'Stakeholder approved release for delivery.'
        : `Release review: ${decision}.`;
    default:
      return JSON.stringify(d) !== '{}' ? JSON.stringify(d) : decision;
  }
}

/** Build chronological journey activities from audit log entries. */
export function buildProjectJourney(auditEvents, runState) {
  const events = [...(auditEvents || [])].sort((a, b) =>
    (a.timestamp || '').localeCompare(b.timestamp || ''),
  );

  const activities = events.map((event) => {
    const meta = EVENT_META[event.event] || {
      stage: 'Pipeline',
      role: event.agent || 'Agent',
      title: event.event || 'Activity',
    };
    return {
      id: `${event.timestamp}-${event.event}`,
      timestamp: event.timestamp,
      timeLabel: formatTime(event.timestamp),
      stage: meta.stage,
      role: meta.role,
      title: meta.title,
      decision: event.decision,
      detail: detailForEvent(event),
      passed: !['fail', 'rejected', 'skipped'].includes(String(event.decision || '').toLowerCase()),
    };
  });

  const complexity = runState?.complexity || 'standard';
  const note =
    complexity === 'basic'
      ? 'Basic runs produce a Flutter project under apps/{run_id}/flutter plus a fast HTML preview in the phone frame. Backend QA is stubbed; preview QA runs at delivery.'
      : complexity === 'basic_plus'
        ? 'Basic+ runs add discovery and QA on backend artifacts, then materialize a Flutter project and HTML preview at delivery.'
        : 'Standard runs use full agent crews, then deliver a Flutter project, HTML preview, and handover package.';

  return { activities, pipelineNote: note, complexity };
}
