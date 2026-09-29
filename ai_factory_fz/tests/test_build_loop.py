"""Build loop tests with a fake sandbox and scripted workers (no agents, no toolchains)."""

import pytest

from agentic_sdlc.artifacts.backlog import Backlog, Epic, Milestone, WorkItem
from agentic_sdlc.artifacts.reports import Bug, QAReport, WorkItemResult
from agentic_sdlc.build.loop import BuildConfig, Builder
from agentic_sdlc.crews.base import PhaseError, TaskResult
from agentic_sdlc.registry.profiles import Component, Profile, ScaffoldStep
from agentic_sdlc.state import ProjectState, UsageRecord
from agentic_sdlc.tools.sandbox_exec import SandboxResult
from agentic_sdlc.workspace import Workspace


class FakeSandbox:
    def __init__(self, unavailable=None, check_results=None):
        self.unavailable = unavailable or {}
        self.check_results = list(check_results or [])  # consumed by checks; default ok
        self.commands: list[tuple[str, str, str]] = []

    def unavailable_reason(self, runtime):
        return self.unavailable.get(runtime)

    def prepare(self, runtimes):
        self.prepared = list(runtimes)
        return {}

    def run_trusted(self, runtime, workdir, command, env=None, host_network=False, timeout_s=None):
        self.commands.append((runtime, workdir, command))
        if command.startswith("check") and self.check_results:
            return self.check_results.pop(0)
        return SandboxResult(exit_code=0, output="ok")


class ScriptedWorker:
    """Returns queued results per task key; defaults to success / passing QA."""

    def __init__(self, script=None):
        self.script = {k: list(v) for k, v in (script or {}).items()}
        self.jobs = []

    def run(self, job):
        self.jobs.append(job)
        queued = self.script.get(job.task_key)
        out = queued.pop(0) if queued else None
        if isinstance(out, Exception):
            raise out
        if out is None:
            out = (QAReport(milestone_id=job.inputs["milestone_id"], passed=True, summary="ok")
                   if job.task_key == "qa_milestone" else WorkItemResult(summary=f"did {job.inputs.get('item_id', job.task_key)}", checks_passed=True))
        return TaskResult(artifact=out, usage=UsageRecord(phase="build", agent=job.agent_key, model="fake", total_tokens=5))


def item(wid, component="backend", deps=(), stories=("US-001",)):
    return WorkItem(id=wid, title=f"title {wid}", description="d", epic_id="E-01", component=component,
                    story_ids=list(stories), depends_on=list(deps), estimate_points=2)


@pytest.fixture
def profile(tmp_path):
    base = Profile.load("flutter_nestjs_ecommerce")
    return base.model_copy(update={"components": {
        "backend": Component(agent="backend_developer", workdir="server", runtime="node", checks=["check build", "check test"],
                             scaffold=[ScaffoldStep(run="scaffold server", creates="server/package.json")]),
        "frontend": Component(agent="frontend_developer", workdir="app", runtime="flutter", checks=["check analyze"]),
        "infra": Component(agent="deployment_engineer", workdir=".", runtime=None),
    }})


def make_builder(tmp_path, prd, profile, items, milestones, sandbox=None, worker=None, cfg=None):
    state = ProjectState(run_id="r", prd=prd, backlog=Backlog(
        epics=[Epic(id="E-01", title="e", story_ids=["US-001"])], work_items=items, milestones=milestones))
    ws = Workspace.create("r", runs_dir=tmp_path)
    sandbox = sandbox or FakeSandbox()
    worker = worker or ScriptedWorker()
    stops: list[str] = []

    def stop(reason):
        state.status, state.stop_reason = "stopped", reason
        stops.append(reason)

    b = Builder(state, ws, profile, sandbox, lambda agent: worker, cfg or BuildConfig(milestones=[]),
                record=lambda r: r.artifact, checkpoint=lambda msg: None,
                can_continue=lambda: state.status == "running", stop=stop)
    return b, state, sandbox, worker


def test_items_are_built_in_dependency_order_then_qa(tmp_path, prd, profile):
    items = [item("WI-002", deps=["WI-001"]), item("WI-001")]
    b, s, sandbox, worker = make_builder(tmp_path, prd, profile, items, [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-002", "WI-001"])])
    b.run()
    assert [j.inputs.get("item_id") for j in worker.jobs if j.task_key == "implement_work_item"] == ["WI-001", "WI-002"]
    assert all(s.build.item(w).status == "done" for w in ("WI-001", "WI-002"))
    assert s.build.item("WI-001").commit is not None
    assert s.build.milestone("M1").status == "done"
    assert s.build.scaffolded == ["backend"]
    assert sandbox.commands.count(("node", ".", "scaffold server")) == 1
    implement = worker.jobs[0]
    assert (implement.agent_key, implement.workdir, implement.runtime) == ("backend_developer", "server", "node")
    assert "Given g when w then t" in implement.inputs["stories"]


def test_failing_checks_are_fed_back_until_they_pass(tmp_path, prd, profile):
    sandbox = FakeSandbox(check_results=[SandboxResult(exit_code=1, output="TS2345: bad type")])
    b, s, _, worker = make_builder(tmp_path, prd, profile, [item("WI-001")],
                                   [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])], sandbox=sandbox)
    b.run()
    assert s.build.item("WI-001").status == "done"
    assert s.build.item("WI-001").attempts == 2
    fix = [j for j in worker.jobs if j.task_key == "fix_work_item"][0]
    assert "TS2345: bad type" in fix.inputs["problems"]


def test_item_fails_after_attempts_and_dependents_are_blocked(tmp_path, prd, profile):
    fail = SandboxResult(exit_code=1, output="boom")
    sandbox = FakeSandbox(check_results=[fail] * 10)
    items = [item("WI-001"), item("WI-002", deps=["WI-001"])]
    b, s, _, _ = make_builder(tmp_path, prd, profile, items, [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001", "WI-002"])],
                              sandbox=sandbox, cfg=BuildConfig(milestones=[], check_fix_attempts=1))
    b.run()
    assert s.build.item("WI-001").status == "failed"
    assert s.build.item("WI-001").attempts == 2
    assert s.build.item("WI-002").status == "blocked"
    assert "depends on WI-001, which is failed" in s.build.item("WI-002").reason
    assert s.build.milestone("M1").status == "partial"


def test_missing_toolchain_blocks_items_but_not_the_run(tmp_path, prd, profile):
    sandbox = FakeSandbox(unavailable={"flutter": "'flutter' is not installed"})
    items = [item("WI-001"), item("WI-002", component="frontend")]
    b, s, _, _ = make_builder(tmp_path, prd, profile, items, [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001", "WI-002"])], sandbox=sandbox)
    b.run()
    assert s.build.item("WI-001").status == "done"
    assert s.build.item("WI-002").status == "blocked"
    assert "flutter" in s.build.item("WI-002").reason
    assert s.build.milestone("M1").status == "partial"
    assert s.status == "running"


def test_agent_reported_blocked(tmp_path, prd, profile):
    worker = ScriptedWorker({"implement_work_item": [WorkItemResult(summary="", checks_passed=False, blocked=True, blocked_reason="needs Postmark account")]})
    b, s, _, _ = make_builder(tmp_path, prd, profile, [item("WI-001")], [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])], worker=worker)
    b.run()
    assert (s.build.item("WI-001").status, s.build.item("WI-001").reason) == ("blocked", "needs Postmark account")


def test_qa_bugs_go_back_to_the_developer_then_pass(tmp_path, prd, profile):
    bug = Bug(id="BUG-001", work_item_id="WI-001", title="409 not returned", severity="major", steps="POST dup", expected="409", actual="500")
    worker = ScriptedWorker({"qa_milestone": [QAReport(milestone_id="M1", passed=False, bugs=[bug], summary="bug"), None]})
    b, s, _, _ = make_builder(tmp_path, prd, profile, [item("WI-001")], [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])], worker=worker)
    b.run()
    fix = [j for j in worker.jobs if j.task_key == "fix_work_item"]
    assert len(fix) == 1 and "BUG-001" in fix[0].inputs["problems"]
    mp = s.build.milestone("M1")
    assert (mp.status, mp.qa_rounds, len(mp.qa_reports)) == ("done", 2, 2)
    assert (tmp_path / "r" / "reports" / "qa_M1_round1.md").exists()


def test_bugs_remaining_after_fix_rounds_stop_the_run(tmp_path, prd, profile):
    bug = Bug(id="BUG-001", work_item_id="WI-001", title="t", severity="blocker", steps="s", expected="e", actual="a")
    worker = ScriptedWorker({"qa_milestone": [QAReport(milestone_id="M1", passed=False, bugs=[bug], summary="bad")] * 5})
    b, s, _, _ = make_builder(tmp_path, prd, profile, [item("WI-001")], [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])],
                              worker=worker, cfg=BuildConfig(milestones=[], qa_fix_rounds=1))
    b.run()
    assert s.status == "stopped"
    assert "blocking bug(s) remain" in s.stop_reason
    assert s.build.milestone("M1").status == "failed"


def test_minor_bugs_do_not_block(tmp_path, prd, profile):
    bug = Bug(id="BUG-001", work_item_id="WI-001", title="typo", severity="minor", steps="s", expected="e", actual="a")
    worker = ScriptedWorker({"qa_milestone": [QAReport(milestone_id="M1", passed=True, bugs=[bug], summary="ok")]})
    b, s, _, _ = make_builder(tmp_path, prd, profile, [item("WI-001")], [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])], worker=worker)
    b.run()
    assert s.build.milestone("M1").status == "done"


def test_only_selected_milestones_and_resume_skips_done(tmp_path, prd, profile):
    items = [item("WI-001"), item("WI-002", deps=["WI-001"])]
    ms = [Milestone(id="M1", name="a", goal="g", work_item_ids=["WI-001"]), Milestone(id="M2", name="b", goal="g", work_item_ids=["WI-002"])]
    b, s, _, worker = make_builder(tmp_path, prd, profile, items, ms, cfg=BuildConfig(milestones=["M1"]))
    b.run()
    assert "WI-002" not in s.build.items
    b.cfg = BuildConfig(milestones=["M1", "M2"])
    b.run()
    implemented = [j.inputs["item_id"] for j in worker.jobs if j.task_key == "implement_work_item"]
    assert implemented == ["WI-001", "WI-002"]  # WI-001 not rebuilt


def test_unknown_milestone_is_a_config_error(tmp_path, prd, profile):
    b, *_ = make_builder(tmp_path, prd, profile, [item("WI-001")], [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])],
                         cfg=BuildConfig(milestones=["M9"]))
    with pytest.raises(ValueError, match="M9"):
        b.run()


def test_worker_failure_marks_item_failed(tmp_path, prd, profile):
    worker = ScriptedWorker({"implement_work_item": [PhaseError("claude down")]})
    b, s, _, _ = make_builder(tmp_path, prd, profile, [item("WI-001")], [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])], worker=worker)
    b.run()
    assert s.build.item("WI-001").status == "failed"


def test_resume_retries_blocked_items_and_reruns_qa(tmp_path, prd, profile):
    sandbox = FakeSandbox(unavailable={"node": "npm missing"})
    b, s, _, worker = make_builder(tmp_path, prd, profile, [item("WI-001")],
                                   [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])], sandbox=sandbox)
    b.run()
    assert s.build.item("WI-001").status == "blocked"
    assert s.build.milestone("M1").status == "partial"

    sandbox.unavailable = {}          # toolchain installed
    b._unavailable.clear()            # a new run starts with a fresh Builder
    b.run()
    assert s.build.item("WI-001").status == "done"
    assert s.build.milestone("M1").status == "done"
    assert [j.task_key for j in worker.jobs].count("qa_milestone") == 1

    b.run()                           # nothing new: no extra QA
    assert [j.task_key for j in worker.jobs].count("qa_milestone") == 1


def test_resumed_failed_milestone_gets_fresh_fix_rounds(tmp_path, prd, profile):
    bug = Bug(id="BUG-001", work_item_id="WI-001", title="t", severity="major", steps="s", expected="e", actual="a")
    bad = QAReport(milestone_id="M1", passed=False, bugs=[bug], summary="bad")
    worker = ScriptedWorker({"qa_milestone": [bad, bad, None]})
    b, s, _, _ = make_builder(tmp_path, prd, profile, [item("WI-001")], [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])],
                              worker=worker, cfg=BuildConfig(milestones=[], qa_fix_rounds=1))
    b.run()
    assert s.status == "stopped"
    s.status, s.stop_reason = "running", ""   # what resume does
    b.run()
    mp = s.build.milestone("M1")
    assert (mp.status, mp.qa_rounds) == ("done", 3)
    assert (tmp_path / "r" / "reports" / "qa_M1_round3.md").exists()


def test_toolchains_are_prepared_for_components_still_to_build(tmp_path, prd, profile):
    items = [item("WI-001"), item("WI-002", component="frontend"), item("WI-003", component="infra")]
    b, s, sandbox, _ = make_builder(tmp_path, prd, profile, items, [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001", "WI-002", "WI-003"])])
    s.build.item("WI-002").status = "done"
    b.run()
    assert sandbox.prepared == ["node"]  # frontend already done; infra needs no toolchain


def test_bug_fix_with_failing_checks_gets_the_output_and_retries(tmp_path, prd, profile):
    bug = Bug(id="BUG-001", work_item_id="WI-001", title="t", severity="major", steps="s", expected="e", actual="a")
    worker = ScriptedWorker({"qa_milestone": [QAReport(milestone_id="M1", passed=False, bugs=[bug], summary="bug"), None]})
    ok, bad = SandboxResult(exit_code=0, output="ok"), SandboxResult(exit_code=1, output="1 test failed: svg")
    sandbox = FakeSandbox(check_results=[ok, ok, bad, ok, ok])  # build ok; first fix breaks tests; retry passes
    b, s, _, _ = make_builder(tmp_path, prd, profile, [item("WI-001")], [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])],
                              sandbox=sandbox, worker=worker)
    b.run()
    fixes = [j for j in worker.jobs if j.task_key == "fix_work_item"]
    assert len(fixes) == 2 and "1 test failed: svg" in fixes[1].inputs["problems"]
    assert s.build.milestone("M1").status == "done"


def test_failed_item_reason_keeps_the_check_output(tmp_path, prd, profile):
    sandbox = FakeSandbox(check_results=[SandboxResult(exit_code=1, output="Expected: 2 Actual: 1")] * 5)
    b, s, _, _ = make_builder(tmp_path, prd, profile, [item("WI-001")], [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001"])],
                              sandbox=sandbox, cfg=BuildConfig(milestones=[], check_fix_attempts=1))
    b.run()
    assert "Expected: 2 Actual: 1" in s.build.item("WI-001").reason


def test_usage_limit_stops_the_run_with_the_real_reason(tmp_path, prd, profile):
    from agentic_sdlc.crews.base import UsageLimitError
    worker = ScriptedWorker({"implement_work_item": [UsageLimitError("Usage limit reached: resets 8:10pm")]})
    b, s, _, _ = make_builder(tmp_path, prd, profile, [item("WI-001"), item("WI-002")],
                              [Milestone(id="M1", name="m", goal="g", work_item_ids=["WI-001", "WI-002"])], worker=worker)
    b.run()
    assert s.status == "stopped" and "resets 8:10pm" in s.stop_reason and "uv run resume" in s.stop_reason
    assert [j.inputs["item_id"] for j in worker.jobs] == ["WI-001"]  # nothing else attempted
