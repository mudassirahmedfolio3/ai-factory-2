"""Flow state for one SDLC run. Checkpointed to runs/<run_id>/state.json after every phase."""

from datetime import datetime, timezone
from typing import Literal

from crewai.flow.flow import FlowState
from pydantic import BaseModel, Field

from agentic_sdlc.artifacts.architecture import ArchitectureDoc
from agentic_sdlc.artifacts.backlog import Backlog
from agentic_sdlc.artifacts.design import DesignSystem
from agentic_sdlc.artifacts.prd import PRD, ProductBrief, QAPair
from agentic_sdlc.artifacts.reports import QAReport, WorkItemResult


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class GateDecision(BaseModel):
    gate: str
    approved: bool
    feedback: str = ""
    decided_by: str = "human"
    decided_at: str = Field(default_factory=utcnow)


class UsageRecord(BaseModel):
    phase: str
    agent: str
    model: str
    prompt_tokens: int = 0
    cached_prompt_tokens: int = 0  # included in prompt_tokens; cheap cache reads
    completion_tokens: int = 0
    total_tokens: int = 0
    task_key: str = ""
    duration_ms: int = 0
    started_at: str = ""
    ended_at: str = ""

    @property
    def uncached_tokens(self) -> int:
        return self.total_tokens - self.cached_prompt_tokens


class ItemProgress(BaseModel):
    status: Literal["todo", "done", "blocked", "failed"] = "todo"
    attempts: int = 0
    summary: str = ""
    reason: str = ""  # why blocked or failed
    commit: str | None = None


class MilestoneProgress(BaseModel):
    status: Literal["todo", "done", "partial", "failed"] = "todo"
    qa_rounds: int = 0
    qa_reports: list[QAReport] = Field(default_factory=list)


class BuildState(BaseModel):
    scaffolded: list[str] = Field(default_factory=list)  # components whose project exists
    items: dict[str, ItemProgress] = Field(default_factory=dict)
    milestones: dict[str, MilestoneProgress] = Field(default_factory=dict)

    def item(self, wid: str) -> ItemProgress:
        return self.items.setdefault(wid, ItemProgress())

    def milestone(self, mid: str) -> MilestoneProgress:
        return self.milestones.setdefault(mid, MilestoneProgress())


class ReleaseState(BaseModel):
    deployment: WorkItemResult | None = None      # Deployment engineer: Dockerfile, compose, CI, staging env
    smoke_suite: WorkItemResult | None = None     # Smoke tester: the smoke test suite
    rounds: int = 0                               # staging verification rounds, all runs
    contract_issues: list[str] = Field(default_factory=list)
    integration: QAReport | None = None
    smoke_passed: bool | None = None
    smoke_output: str = ""
    device_suite: WorkItemResult | None = None    # Smoke tester: on-device journey tests
    device_passed: bool | None = None             # None: not run (see device_note)
    device_output: str = ""
    device_note: str = ""                         # why device checks were skipped, if they were
    device_screenshots: list[str] = Field(default_factory=list)
    verified: bool = False                        # staging, integration, smoke (and device) passed
    production: Literal["todo", "packaged", "deployed", "failed"] = "todo"
    production_notes: str = ""

    def reset_verification(self) -> None:
        self.contract_issues, self.integration = [], None
        self.smoke_passed, self.smoke_output, self.verified = None, "", False
        self.device_passed, self.device_output, self.device_note, self.device_screenshots = None, "", "", []


class ProjectState(FlowState):
    run_id: str = ""
    profile: str = "flutter_nestjs_ecommerce"
    pipeline: str = "pipeline"          # config/<pipeline>.yaml, fixed for the run
    brief: str = ""

    product_brief: ProductBrief | None = None
    clarifications: list[QAPair] = Field(default_factory=list)
    prd: PRD | None = None
    backlog: Backlog | None = None
    architecture: ArchitectureDoc | None = None
    design: DesignSystem | None = None
    build: BuildState = Field(default_factory=BuildState)
    release: ReleaseState = Field(default_factory=ReleaseState)

    gate_history: list[GateDecision] = Field(default_factory=list)
    usage: list[UsageRecord] = Field(default_factory=list)

    status: Literal["running", "completed", "stopped"] = "running"
    stop_reason: str = ""

    def gate_approved(self, gate: str) -> bool:
        """True if the latest decision for this gate is an approval."""
        latest = [d for d in self.gate_history if d.gate == gate]
        return bool(latest) and latest[-1].approved

    def rejections(self, gate: str) -> list[GateDecision]:
        """Human rejections (a system reopen is not a rejection)."""
        return [d for d in self.gate_history if d.gate == gate and not d.approved and d.decided_by != "system"]

    def reopen_release(self, reason: str) -> None:
        """Something changed after release verification/approval: verify again and ask again."""
        self.release.reset_verification()
        self.release.production, self.release.production_notes = "todo", ""
        if self.gate_approved("release"):
            self.gate_history.append(GateDecision(gate="release", approved=False, decided_by="system", feedback=reason))

    def revision_notes(self, gate: str) -> str:
        """Feedback from the latest human rejection of this gate, if it came after the last approval."""
        for d in reversed(self.gate_history):
            if d.gate == gate and d.decided_by != "system":
                return "" if d.approved else d.feedback
        return ""

    def total_tokens(self) -> int:
        return sum(u.total_tokens for u in self.usage)

    def uncached_tokens(self) -> int:
        """Tokens that count against the budget: cache reads are excluded, since agentic
        coding sessions re-read the same context many times at a small fraction of the cost."""
        return sum(u.uncached_tokens for u in self.usage)
