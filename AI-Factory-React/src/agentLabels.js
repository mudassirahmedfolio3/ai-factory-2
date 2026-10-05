/** User-facing agent names (backend keys unchanged). */

const AGENT_LABELS = {
  spec_writer: 'Business Developer',
  requirements_editor: 'Business Developer',
  customer: 'Customer',
  architect: 'Solution Architect',
  ui_ux_designer: 'UI/UX Designer',
  project_manager: 'Project Manager',
  backend_developer: 'Backend Developer',
  frontend_developer: 'Frontend Developer',
  qa_engineer: 'QA Engineer',
  smoke_tester: 'Smoke Tester',
  deployment_engineer: 'Deployment Engineer',
};

export function displayAgentName(agent) {
  if (!agent) return 'Agent';
  const key = String(agent).toLowerCase().replace(/\s+/g, '_');
  if (AGENT_LABELS[key]) return AGENT_LABELS[key];
  return String(agent)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
