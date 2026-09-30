"""Bottom-up estimation review: builders re-estimate their own items; the PM reconciles big gaps."""

import pytest

from agentic_sdlc.artifacts.estimates import Decision, EstimateReview, ItemEstimate, Reconciliation
from agentic_sdlc.crews.base import TaskResult
from agentic_sdlc.crews.estimation import EstimationConfig, estimator_groups, review_estimates
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.state import UsageRecord


class Runner:
    """Answers review_estimates per agent from `dev_points`, and reconcile_estimates from `decisions`."""

    def __init__(self, dev_points, decisions=None, concerns=""):
        self.dev_points, self.decisions, self.concerns = dev_points, decisions or {}, concerns
        self.calls = []

    def run(self, phase, task_key, inputs, output_model, guardrail=None, agent_key=None, with_tools=True):
        self.calls.append((task_key, agent_key, with_tools, inputs))
        if task_key == "review_estimates":
            import re
            ids = re.findall(r"- (WI-\d+) ", inputs["items"])
            art = EstimateReview(estimates=[ItemEstimate(item_id=i, points=self.dev_points[i], complexity="high",
                                                         risk="high", confidence="low", rationale=f"{i} needs more",
                                                         concerns=self.concerns) for i in ids])
        else:
            art = Reconciliation(decisions=[Decision(item_id=i, final_points=p, reason="builder named hidden work")
                                            for i, p in self.decisions.items()])
        if guardrail:
            from crewai.tasks.task_output import TaskOutput
            ok, feedback = guardrail(TaskOutput(description="", raw=art.model_dump_json(), agent="x", pydantic=art))
            assert ok, feedback
        return TaskResult(artifact=art, usage=UsageRecord(phase=phase, agent=agent_key or "pm", model="fake"))


@pytest.fixture
def profile():
    return Profile.load("flutter_nestjs_ecommerce")


def test_each_developer_estimates_only_its_own_items_without_tools(backlog, architecture, profile):
    runner = Runner({"WI-001": 3, "WI-002": 3})
    review_estimates(runner, backlog, architecture, profile, EstimationConfig())
    reviews = [(agent, tools, inputs["items"]) for key, agent, tools, inputs in runner.calls if key == "review_estimates"]
    assert [(a, t) for a, t, _ in reviews] == [("backend_developer", False), ("frontend_developer", False)]
    assert "WI-001" in reviews[0][2] and "WI-002" not in reviews[0][2]
    assert "PM estimate: 3 pts" in reviews[0][2] and "operations: listProducts" in reviews[0][2]
    assert backlog.estimation_reviewed
    assert all(w.estimate_notes == "PM and builder agree" for w in backlog.work_items)
    assert "reconcile_estimates" not in [c[0] for c in runner.calls]


def test_small_gap_adopts_the_builders_estimate_and_the_cautious_risk(backlog, architecture, profile):
    runner = Runner({"WI-001": 5, "WI-002": 3}, concerns="seed data not in the plan")
    review_estimates(runner, backlog, architecture, profile, EstimationConfig())
    w = backlog.work_items[0]
    assert (w.pm_points, w.dev_points, w.estimate_points) == (3, 5, 5)
    assert w.estimate_notes == "builder's estimate adopted" and w.estimated_by == "backend_developer"
    assert (w.risk, w.confidence) == ("high", "low")
    assert "seed data not in the plan" in w.estimate_rationale


def test_big_gap_is_reconciled_by_the_pm_within_both_estimates(backlog, architecture, profile):
    runner = Runner({"WI-001": 8, "WI-002": 3}, decisions={"WI-001": 6})
    review_estimates(runner, backlog, architecture, profile, EstimationConfig())
    w = backlog.work_items[0]
    assert (w.pm_points, w.dev_points, w.estimate_points) == (3, 8, 6)
    assert w.disagreement and "builder named hidden work" in w.estimate_notes
    reconcile = [c for c in runner.calls if c[0] == "reconcile_estimates"][0]
    assert "WI-001 Products API: PM 3 pts vs backend_developer 8 pts" in reconcile[3]["disagreements"]
    md = backlog.to_markdown()
    assert "## Estimation review" in md and "1 big disagreements reconciled" in md and "6 (PM 3, dev 8)" in md


def test_reconciliation_must_land_between_the_estimates(backlog, architecture, profile):
    runner = Runner({"WI-001": 8, "WI-002": 3}, decisions={"WI-001": 2})
    with pytest.raises(AssertionError, match="outside the two estimates 3-8"):
        review_estimates(runner, backlog, architecture, profile, EstimationConfig())


def test_gap_rule():
    cfg = EstimationConfig(big_gap_points=3, big_gap_ratio=2.0)
    assert not cfg.is_big_gap(3, 5)
    assert cfg.is_big_gap(3, 6)        # 3 points apart
    assert cfg.is_big_gap(1, 2)        # 2x
    assert not cfg.is_big_gap(4, 4)


def test_items_group_by_the_components_agent(backlog, profile):
    groups = estimator_groups(backlog, profile)
    assert {k: [w.id for w in v] for k, v in groups.items()} == {"backend_developer": ["WI-001"], "frontend_developer": ["WI-002"]}
