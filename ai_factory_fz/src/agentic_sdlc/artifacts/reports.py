"""Build artifacts: what a coding agent reports back, and QA reports with bugs."""

from typing import Literal

from pydantic import BaseModel, Field


class WorkItemResult(BaseModel):
    summary: str = Field(description="What was implemented, in a few sentences")
    files_changed: list[str] = Field(default_factory=list, description="Paths relative to the workspace")
    tests_added: list[str] = Field(default_factory=list)
    checks_passed: bool = Field(description="True if the build/test commands you ran passed")
    blocked: bool = Field(default=False, description="True if the item cannot be done; explain in blocked_reason")
    blocked_reason: str = ""
    notes: str = Field(default="", description="Follow-ups, assumptions, known gaps")


class Bug(BaseModel):
    id: str = Field(description="BUG-001, ...")
    work_item_id: str = Field(description="The work item the bug belongs to")
    title: str
    severity: Literal["blocker", "major", "minor"]
    story_id: str = ""
    steps: str = Field(description="How to reproduce, or where in the code")
    expected: str
    actual: str


class QAReport(BaseModel):
    milestone_id: str
    passed: bool = Field(description="True only if there are no blocker or major bugs")
    criteria_checked: list[str] = Field(default_factory=list, description="Acceptance criteria verified, with how")
    tests_added: list[str] = Field(default_factory=list)
    bugs: list[Bug] = Field(default_factory=list)
    summary: str

    def blocking_bugs(self) -> list[Bug]:
        return [b for b in self.bugs if b.severity in ("blocker", "major")]

    def to_markdown(self) -> str:
        lines = [f"# QA report: {self.milestone_id}", "", f"Result: **{'passed' if self.passed else 'failed'}**", "", self.summary, "", "## Criteria checked"]
        lines += [f"- {c}" for c in self.criteria_checked] or ["- (none)"]
        lines += ["", "## Bugs"]
        for b in self.bugs:
            lines += [f"### {b.id} [{b.severity}] {b.title} ({b.work_item_id})", f"Steps: {b.steps}", f"Expected: {b.expected}", f"Actual: {b.actual}", ""]
        if not self.bugs:
            lines.append("None.")
        return "\n".join(lines)
