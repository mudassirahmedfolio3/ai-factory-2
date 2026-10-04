"""User-facing agent and phase labels (backend keys unchanged)."""

from __future__ import annotations

AGENT_DISPLAY: dict[str, str] = {
    "customer": "Customer",
    "spec_writer": "Business Developer",
    "requirements_editor": "Business Developer",
    "architect": "Solution Architect",
    "ui_ux_designer": "UI/UX Designer",
    "designer": "UI/UX Designer",
    "project_manager": "Project Manager",
    "pm": "Project Manager",
    "backend_developer": "Backend Developer",
    "frontend_developer": "Frontend Developer",
    "deployment_engineer": "Deployment Engineer",
    "release_engineer": "Release Engineer",
    "qa_engineer": "QA Engineer",
    "qa": "QA Engineer",
    "tester": "QA Engineer",
    "smoke_tester": "Smoke Tester",
    "security_engineer": "Security Engineer",
    "integration_pass": "Integration Engineer",
    "console": "Factory Console",
}


def agent_display_name(agent: str) -> str:
    key = (agent or "").strip().lower().replace(" ", "_")
    if key in AGENT_DISPLAY:
        return AGENT_DISPLAY[key]
    if not agent:
        return "Agent"
    return agent.replace("_", " ").title()


def phase_display_name(phase: str) -> str:
    labels = {
        "discovery": "Discovery",
        "planning": "Planning",
        "design": "Design",
        "build": "Build",
        "release": "Release",
        "complete": "Complete",
    }
    return labels.get((phase or "").lower(), (phase or "Unknown").title())
