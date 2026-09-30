"""Bottom-up estimation review (Wideband-Delphi style).

The Project manager drafts the work breakdown and initial estimates. Then each developer agent
re-estimates only the items of its own component (one call per agent, no tools). Small gaps: the
builder's estimate is adopted. Big gaps (see EstimationConfig): the Project manager reconciles them
with both rationales in front of it, and must land between the two numbers.
"""

from dataclasses import dataclass
from typing import Any

from agentic_sdlc.artifacts.architecture import ArchitectureDoc
from agentic_sdlc.artifacts.backlog import Backlog, WorkItem
from agentic_sdlc.artifacts.estimates import EstimateReview, Reconciliation
from agentic_sdlc.crews.base import TaskResult, TaskRunner, artifact_guardrail
from agentic_sdlc.registry.profiles import Profile

PHASE = "planning"
_LEVEL = {"low": 0, "medium": 1, "high": 2}


@dataclass
class EstimationConfig:
    enabled: bool = True
    big_gap_points: int = 3      # |PM - dev| at least this many points ...
    big_gap_ratio: float = 2.0   # ... or one estimate at least this multiple of the other

    @classmethod
    def from_pipeline(cls, pipeline: dict[str, Any]) -> "EstimationConfig":
        p = pipeline.get("planning", {}) or {}
        return cls(enabled=p.get("estimation_review", True), big_gap_points=p.get("big_gap_points", 3),
                   big_gap_ratio=p.get("big_gap_ratio", 2.0))

    def is_big_gap(self, pm: int, dev: int) -> bool:
        return abs(pm - dev) >= self.big_gap_points or max(pm, dev) >= self.big_gap_ratio * min(pm, dev)


def item_text(w: WorkItem) -> str:
    links = "; ".join(f"{label}: {', '.join(v)}" for label, v in (
        ("operations", w.api_operations), ("models", w.data_models), ("screens", w.screens), ("modules", w.modules)) if v)
    return (f"- {w.id} [{w.component}] {w.title}: {w.description}\n"
            f"  Builds: {links or '-'}\n  Depends on: {', '.join(w.depends_on) or '-'}\n"
            f"  PM estimate: {w.estimate_points} pts ({w.complexity} complexity, {w.risk} risk, "
            f"{w.confidence} confidence) because: {w.estimate_rationale or '-'}")


def estimator_groups(backlog: Backlog, profile: Profile) -> dict[str, list[WorkItem]]:
    """agent key -> the work items it will build (and so estimates)."""
    groups: dict[str, list[WorkItem]] = {}
    for w in backlog.work_items:
        comp = profile.components.get(w.component)
        if comp:
            groups.setdefault(comp.agent, []).append(w)
    return groups


def review_estimates(runner: TaskRunner, backlog: Backlog, architecture: ArchitectureDoc, profile: Profile,
                     cfg: EstimationConfig) -> list[TaskResult]:
    """Run the review on `backlog` in place. Returns the task results (for usage accounting)."""
    results: list[TaskResult] = []
    items = {w.id: w for w in backlog.work_items}
    for agent, group in estimator_groups(backlog, profile).items():
        ids = [w.id for w in group]

        def covers(review: EstimateReview, ids=ids) -> list[str]:
            got = [e.item_id for e in review.estimates]
            errors = [f"Estimate {i}, which is not one of your items" for i in got if i not in ids]
            errors += [f"Missing an estimate for {i}" for i in ids if i not in got]
            return errors + [f"More than one estimate for {i}" for i in set(got) if got.count(i) > 1]

        res = runner.run(PHASE, "review_estimates", {
            "items": "\n".join(item_text(w) for w in group),
            "solution": architecture.solution_summary(),
            "stack": profile.stack_summary(),
        }, EstimateReview, guardrail=artifact_guardrail(EstimateReview, covers), agent_key=agent, with_tools=False)
        results.append(res)
        for e in res.artifact.estimates:
            w = items[e.item_id]
            w.pm_points = w.estimate_points if w.pm_points is None else w.pm_points
            w.dev_points, w.estimated_by = e.points, agent
            w.risk = max(w.risk, e.risk, key=_LEVEL.get)                  # the more cautious view wins
            w.confidence = min(w.confidence, e.confidence, key=_LEVEL.get)
            w.complexity = e.complexity
            if e.concerns:
                w.estimate_rationale = f"{w.estimate_rationale} | {agent}: {e.rationale}; concerns: {e.concerns}"
            elif e.rationale:
                w.estimate_rationale = f"{w.estimate_rationale} | {agent}: {e.rationale}"
            if not cfg.is_big_gap(w.pm_points, e.points):
                w.estimate_points = e.points
                w.estimate_notes = "builder's estimate adopted" if e.points != w.pm_points else "PM and builder agree"

    disputed = [w for w in backlog.work_items
                if w.dev_points is not None and cfg.is_big_gap(w.pm_points, w.dev_points)]
    if disputed:
        bounds = {w.id: (min(w.pm_points, w.dev_points), max(w.pm_points, w.dev_points)) for w in disputed}

        def within(r: Reconciliation) -> list[str]:
            got = {d.item_id: d.final_points for d in r.decisions}
            errors = [f"Missing a decision for {i}" for i in bounds if i not in got]
            return errors + [f"{i}: {p} is outside the two estimates {bounds[i][0]}-{bounds[i][1]}"
                             for i, p in got.items() if i in bounds and not bounds[i][0] <= p <= bounds[i][1]]

        res = runner.run(PHASE, "reconcile_estimates", {
            "disagreements": "\n".join(
                f"- {w.id} {w.title}: PM {w.pm_points} pts vs {w.estimated_by} {w.dev_points} pts. "
                f"Reasons: {w.estimate_rationale}" for w in disputed),
        }, Reconciliation, guardrail=artifact_guardrail(Reconciliation, within))
        results.append(res)
        for d in res.artifact.decisions:
            if d.item_id in items:
                items[d.item_id].estimate_points = d.final_points
                items[d.item_id].estimate_notes = f"reconciled by the PM: {d.reason}"
    backlog.estimation_reviewed = True
    return results
