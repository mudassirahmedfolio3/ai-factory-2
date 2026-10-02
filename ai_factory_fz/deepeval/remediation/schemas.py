"""Schemas for the DeepEval remediation loop."""

from typing import Literal

from pydantic import BaseModel, Field

AGENT_KEYS = (
    "customer", "spec_writer", "project_manager", "architect", "ui_ux_designer", "backend_developer",
    "frontend_developer", "qa_engineer", "deployment_engineer", "integration_pass", "smoke_tester",
)

Classification = Literal["verified_defect", "specification_gap", "unverified", "false_positive_or_exception"]
Priority = Literal["P0", "P1", "P2", "P3"]
TaskStatus = Literal["proposed", "approved", "rejected", "in_progress", "done", "failed", "blocked"]


class Finding(BaseModel):
    """One normalized item from the DeepEval report, kept verbatim so results trace back to it."""

    id: str = Field(description="F-001, F-002, ...")
    kind: Literal["failed_test", "gap"]
    source_test: str
    agent: str | None = None
    score: float | None = None
    level: str | None = None
    original_text: str
    evidence: str
    suggestions: list[str] = Field(default_factory=list, description="Improvements the report proposed")


class ValidatedFinding(BaseModel):
    finding_id: str
    classification: Classification
    classification_reason: str
    evidence_checked: list[str] = Field(default_factory=list, description="Run files actually inspected")
    root_cause: str
    root_cause_status: Literal["confirmed", "hypothesis"]
    severity: Literal["critical", "high", "medium", "low"]
    evidence_confidence: Literal["low", "medium", "high"]
    verification_method: str


class TriageResult(BaseModel):
    findings: list[ValidatedFinding]


class RemediationTask(BaseModel):
    id: str = Field(description="R-001, R-002, ...")
    title: str
    problem: str
    finding_ids: list[str]
    validation_status: Classification
    root_cause: str
    root_cause_status: Literal["confirmed", "hypothesis"]
    affected_requirements: list[str] = Field(default_factory=list)
    affected_components: list[str] = Field(default_factory=list)
    owners: list[str] = Field(description="Existing agent keys")
    inputs: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    steps: list[str]
    acceptance_criteria: list[str]
    verification: str
    priority: Priority
    priority_rationale: str
    status: TaskStatus = "proposed"
    needs_human_approval: bool
    approval_reason: str = ""


class Disposition(BaseModel):
    """A finding that gets no task, with the reason."""

    finding_id: str
    disposition: Literal["no_action_false_positive", "needs_evidence", "accepted_exception_pending_approval"]
    reason: str


class RemediationBacklog(BaseModel):
    summary: str
    tasks: list[RemediationTask]
    dispositions: list[Disposition] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        lines = ["# Remediation backlog", "", self.summary, ""]
        if self.limitations:
            lines += ["## Limitations", *[f"- {x}" for x in self.limitations], ""]
        lines += ["## Tasks", ""]
        for t in sorted(self.tasks, key=lambda t: (t.priority, t.id)):
            lines += [
                f"### {t.id} [{t.priority}] {t.title}", "",
                f"- Status: {t.status}. Owners: {', '.join(t.owners)}. Depends on: {', '.join(t.depends_on) or 'none'}",
                f"- Findings: {', '.join(t.finding_ids)}. Validation: {t.validation_status}",
                f"- Problem: {t.problem}",
                f"- Root cause ({t.root_cause_status}): {t.root_cause}",
                f"- Priority rationale: {t.priority_rationale}",
                f"- Human approval needed: {'yes, ' + t.approval_reason if t.needs_human_approval else 'no'}",
                "- Steps:", *[f"  - {s}" for s in t.steps],
                "- Acceptance criteria:", *[f"  - {a}" for a in t.acceptance_criteria],
                f"- Verification: {t.verification}", "",
            ]
        if self.dispositions:
            lines += ["## Findings without a task", ""]
            lines += [f"- {d.finding_id}: {d.disposition}. {d.reason}" for d in self.dispositions]
        return "\n".join(lines) + "\n"
