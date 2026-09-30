"""Flow routing tests with a fake task runner (no LLM calls)."""

import json

import pytest

from agentic_sdlc.crews.base import TaskResult
from agentic_sdlc.flow import Deps, SDLCFlow
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.state import UsageRecord
from agentic_sdlc.workspace import Workspace

PIPELINE = {
    "phases": {"discovery": True, "planning": True, "design": True, "build": False, "release": False},
    "gates": {"prd": True, "architecture": True, "release": True},
    "gate_mode": "console",
    "limits": {"clarification_rounds": 2, "gate_rejections": 2},
    "budget": {"max_total_tokens": 1_000_000},
}


class FakeRunner:
    def __init__(self, canned):
        self.canned = canned
        self.calls: list[tuple[str, dict]] = []

    def run(self, phase, task_key, inputs, output_model, guardrail=None, agent_key=None, with_tools=True):
        self.calls.append((task_key, inputs))
        if task_key == "review_estimates":
            # Each developer agrees with the PM's draft (disagreements are tested in test_estimation.py).
            import re
            from agentic_sdlc.artifacts.estimates import EstimateReview, ItemEstimate
            estimates = [ItemEstimate(item_id=i, points=int(p), complexity="medium", risk="medium",
                                      confidence="medium", rationale="ok")
                         for i, p in re.findall(r"- (WI-\d+) .*?PM estimate: (\d+) pts", inputs["items"], re.S)]
            artifact = EstimateReview(estimates=estimates)
        else:
            artifact = self.canned[task_key].model_copy(deep=True)
        assert isinstance(artifact, output_model)
        return TaskResult(artifact=artifact, usage=UsageRecord(phase=phase, agent=agent_key or task_key, model="fake", total_tokens=10))

    def keys(self):
        return [k for k, _ in self.calls]


def make_flow(tmp_path, runner, answers, pipeline=PIPELINE, restore_json=None):
    answers = iter(answers)

    def deps_factory(state):
        return Deps(
            workspace=Workspace.create(state.run_id, runs_dir=tmp_path),
            profile=Profile.load("flutter_nestjs_ecommerce"),
            runner=runner,
            pipeline=pipeline,
            input_fn=lambda _prompt: next(answers),
        )

    return SDLCFlow(deps_factory=deps_factory, restore_json=restore_json)


@pytest.fixture(autouse=True)
def console_gates(monkeypatch):
    monkeypatch.delenv("SDLC_GATE_MODE", raising=False)


def test_happy_path_runs_all_built_phases(tmp_path, canned):
    runner = FakeRunner(canned)
    flow = make_flow(tmp_path, runner, ["y", "", "y", ""])
    flow.kickoff(inputs={"run_id": "r1", "brief": "shop"})

    s = flow.state
    assert s.status == "completed", s.stop_reason
    assert runner.keys() == [
        "customer_brief", "spec_questions", "customer_answers", "spec_questions",
        "customer_answers", "write_prd", "design_architecture", "design_ui", "plan_backlog",
        "review_estimates", "review_estimates",
    ]
    assert [(g.gate, g.approved) for g in s.gate_history] == [("prd", True), ("architecture", True)]
    root = tmp_path / "r1"
    for f in ("prd.md", "backlog.md", "architecture.md", "openapi.yaml", "schema.prisma", "design_system.md"):
        assert (root / "docs" / f).exists(), f
    assert json.loads((root / "state.json").read_text())["status"] == "completed"
    assert "Total tokens: 110" in (root / "reports" / "run_summary.md").read_text()  # 11 agent calls


def test_rejected_prd_is_rewritten_with_feedback(tmp_path, canned):
    runner = FakeRunner(canned)
    flow = make_flow(tmp_path, runner, ["n", "Add guest checkout", "y", "", "y", ""])
    flow.kickoff(inputs={"run_id": "r2", "brief": "shop"})

    assert flow.state.status == "completed", flow.state.stop_reason
    prd_calls = [inputs for key, inputs in runner.calls if key == "write_prd"]
    assert len(prd_calls) == 2
    assert prd_calls[0]["revision_notes"] == "(none)"
    assert prd_calls[1]["revision_notes"] == "Add guest checkout"


def test_rejected_solution_rewrites_architecture_design_and_plan_with_feedback(tmp_path, canned):
    runner = FakeRunner(canned)
    flow = make_flow(tmp_path, runner, ["y", "", "n", "Use Redis for carts", "y", ""])
    flow.kickoff(inputs={"run_id": "r3", "brief": "shop"})

    assert flow.state.status == "completed", flow.state.stop_reason
    for key in ("design_architecture", "design_ui", "plan_backlog"):
        assert runner.keys().count(key) == 2, key
        assert [i for k, i in runner.calls if k == key][1]["revision_notes"] == "Use Redis for carts", key


def test_pm_plans_from_the_architecture_and_screens(tmp_path, canned):
    runner = FakeRunner(canned)
    flow = make_flow(tmp_path, runner, ["y", "", "y", ""])
    flow.kickoff(inputs={"run_id": "r9", "brief": "shop"})
    inputs = next(i for k, i in runner.calls if k == "plan_backlog")
    assert "listProducts: GET /api/v1/products" in inputs["solution"]
    assert "Data models: Product" in inputs["solution"]
    assert "SCR-01 Products (/products)" in inputs["screens"]


def test_too_many_rejections_stop_the_run(tmp_path, canned):
    runner = FakeRunner(canned)
    flow = make_flow(tmp_path, runner, ["n", "no", "n", "still no"])
    flow.kickoff(inputs={"run_id": "r4", "brief": "shop"})

    assert flow.state.status == "stopped"
    assert "rejected 2 times" in flow.state.stop_reason
    assert "plan_backlog" not in runner.keys()


def test_disabled_gates_auto_approve(tmp_path, canned):
    pipeline = {**PIPELINE, "gates": {"prd": False, "architecture": False}}
    flow = make_flow(tmp_path, FakeRunner(canned), [], pipeline=pipeline)
    flow.kickoff(inputs={"run_id": "r5", "brief": "shop"})
    assert flow.state.status == "completed"
    assert {g.decided_by for g in flow.state.gate_history} == {"config"}


def test_budget_stops_before_next_phase(tmp_path, canned):
    pipeline = {**PIPELINE, "budget": {"max_total_tokens": 25}}
    runner = FakeRunner(canned)
    flow = make_flow(tmp_path, runner, [], pipeline=pipeline)
    flow.kickoff(inputs={"run_id": "r6", "brief": "shop"})
    assert flow.state.status == "stopped"
    assert "budget" in flow.state.stop_reason
    assert "write_prd" not in runner.keys()


def test_release_without_a_build_stops_clearly(tmp_path, canned):
    pipeline = {**PIPELINE, "phases": {**PIPELINE["phases"], "release": True}}
    flow = make_flow(tmp_path, FakeRunner(canned), ["y", "", "y", ""], pipeline=pipeline)
    flow.kickoff(inputs={"run_id": "r7", "brief": "shop"})
    assert flow.state.status == "stopped"
    assert "needs built work items" in flow.state.stop_reason


def test_resume_skips_finished_work(tmp_path, canned):
    # First run stops at the PRD gate after too many rejections.
    first = make_flow(tmp_path, FakeRunner(canned), ["n", "a", "n", "b"])
    first.kickoff(inputs={"run_id": "r8", "brief": "shop"})
    assert first.state.status == "stopped"

    saved = Workspace.open("r8", runs_dir=tmp_path).load_state_json()
    runner = FakeRunner(canned)
    resumed = make_flow(tmp_path, runner, ["y", "", "y", ""], restore_json=saved)
    resumed.kickoff(inputs={"run_id": "r8"})

    assert resumed.state.status == "completed", resumed.state.stop_reason
    # Brief and clarifications were kept; the rejected PRD is rewritten with the last feedback.
    assert runner.keys()[:1] == ["write_prd"]
    assert runner.calls[0][1]["revision_notes"] == "b"


def test_build_phase_runs_after_design(tmp_path, canned):
    from test_build_loop import FakeSandbox, ScriptedWorker

    worker = ScriptedWorker()
    pipeline = {**PIPELINE, "phases": {**PIPELINE["phases"], "build": True}, "build": {"milestones": ["M1"]}}

    def deps_factory(state):
        return Deps(
            workspace=Workspace.create(state.run_id, runs_dir=tmp_path),
            profile=Profile.load("flutter_nestjs_ecommerce"),
            runner=FakeRunner(canned), pipeline=pipeline, input_fn=lambda _p: "y",
            sandbox=FakeSandbox(unavailable={"flutter": "no flutter here"}), worker_for=lambda agent: worker,
        )

    flow = SDLCFlow(deps_factory=deps_factory)
    flow.kickoff(inputs={"run_id": "rb", "brief": "shop"})
    s = flow.state
    assert s.status == "completed", s.stop_reason
    assert s.build.item("WI-001").status == "done"
    assert s.build.item("WI-002").status == "blocked"  # frontend: no flutter
    assert s.build.milestone("M1").status == "partial"
    summary = (tmp_path / "rb" / "reports" / "run_summary.md").read_text()
    assert "## Build" in summary and "| WI-002 | blocked |" in summary


def _release_flow(tmp_path, canned, answers, worker):
    from test_build_loop import FakeSandbox
    from test_release import FakeStaging

    pipeline = {**PIPELINE, "phases": {**PIPELINE["phases"], "build": True, "release": True},
                "build": {"milestones": ["M1"]}, "release": {"fix_rounds": 1},
                "guardrails": {"agents": []}}   # fakes write no real files; guardrails are tested separately
    answers = iter(answers)

    def deps_factory(state):
        return Deps(
            workspace=Workspace.create(state.run_id, runs_dir=tmp_path),
            profile=Profile.load("flutter_nestjs_ecommerce"),
            runner=FakeRunner(canned), pipeline=pipeline, input_fn=lambda _p: next(answers),
            sandbox=FakeSandbox(unavailable={"flutter": "no flutter"}), worker_for=lambda agent: worker,
            staging=FakeStaging(),
        )

    return SDLCFlow(deps_factory=deps_factory)


def test_full_flow_through_release_gate_to_production(tmp_path, canned):
    from test_build_loop import ScriptedWorker
    from test_release import passing_integration

    worker = ScriptedWorker({"integration_review": [passing_integration()]})
    flow = _release_flow(tmp_path, canned, ["y", "", "y", "", "y", ""], worker)
    flow.kickoff(inputs={"run_id": "rr", "brief": "shop"})
    s = flow.state
    assert s.status == "completed", s.stop_reason
    assert [(g.gate, g.approved) for g in s.gate_history] == [("prd", True), ("architecture", True), ("release", True)]
    assert s.release.verified and s.release.production == "packaged"
    assert "## Release" in (tmp_path / "rr" / "reports" / "run_summary.md").read_text()


def test_rejected_release_goes_to_developer_and_is_reverified(tmp_path, canned):
    from test_build_loop import ScriptedWorker
    from test_release import passing_integration

    worker = ScriptedWorker({"integration_review": [passing_integration(), passing_integration()]})
    flow = _release_flow(tmp_path, canned, ["y", "", "y", "", "n", "Checkout total ignores tax", "y", ""], worker)
    flow.kickoff(inputs={"run_id": "rj", "brief": "shop"})
    s = flow.state
    assert s.status == "completed", s.stop_reason
    fixes = [j for j in worker.jobs if j.task_key == "fix_work_item" and j.phase == "release"]
    assert len(fixes) == 1 and "Checkout total ignores tax" in fixes[0].inputs["problems"]
    assert s.release.rounds == 2 and s.release.production == "packaged"


def test_scope_rules_reach_the_planning_prompts(tmp_path, canned):
    runner = FakeRunner(canned)
    pipeline = {**PIPELINE, "scope": {"max_work_items": 5, "guidance": "Demo only."}}
    flow = make_flow(tmp_path, runner, ["y", "", "y", ""], pipeline=pipeline)
    flow.kickoff(inputs={"run_id": "rs", "brief": "shop", "pipeline": "pipeline.demo"})
    assert flow.state.pipeline == "pipeline.demo"
    for key in ("write_prd", "plan_backlog", "design_architecture", "design_ui"):
        inputs = next(i for k, i in runner.calls if k == key)
        assert "Demo only." in inputs["scope_rules"] and "at most 5 work items" in inputs["scope_rules"], key


def test_preflight_problems_stop_the_run_before_any_agent(tmp_path, canned):
    runner = FakeRunner(canned)

    def deps_factory(state):
        return Deps(workspace=Workspace.create(state.run_id, runs_dir=tmp_path), profile=Profile.load("flutter_nestjs_ecommerce"),
                    runner=runner, pipeline=PIPELINE, input_fn=lambda _p: "y",
                    preflight=lambda: ["Docker is not usable: run `uv run setup` once"])

    flow = SDLCFlow(deps_factory=deps_factory)
    flow.kickoff(inputs={"run_id": "rp", "brief": "shop"})
    assert flow.state.status == "stopped"
    assert "uv run setup" in flow.state.stop_reason and "uv run resume rp" in flow.state.stop_reason
    assert runner.calls == []


def test_estimation_review_can_be_switched_off(tmp_path, canned):
    runner = FakeRunner(canned)
    pipeline = {**PIPELINE, "planning": {"estimation_review": False}}
    flow = make_flow(tmp_path, runner, ["y", "", "y", ""], pipeline=pipeline)
    flow.kickoff(inputs={"run_id": "re", "brief": "shop"})
    assert flow.state.status == "completed" and "review_estimates" not in runner.keys()
    assert not flow.state.backlog.estimation_reviewed
