"""The build loop: for each milestone, implement its work items, verify them, then QA.

Per work item: scaffold the component if needed -> the developer agent implements it ->
the component's checks run (build, tests) -> on failure the agent gets the output and fixes
it (limited attempts) -> commit. Items whose toolchain is missing, or whose dependencies are
blocked, are marked blocked with a reason instead of failing the run.

Per milestone: the QA agent verifies the acceptance criteria and reports bugs -> developers
fix blocking bugs -> checks -> QA again, up to qa_fix_rounds. If bugs remain, the run stops
for a human to look.

All progress lives in ProjectState.build and is checkpointed after every step, so a resumed
run continues where it stopped.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Callable

from agentic_sdlc.artifacts.backlog import Milestone, WorkItem
from agentic_sdlc.artifacts.reports import Bug, QAReport, WorkItemResult
from agentic_sdlc.build.coders import Job, Worker
from agentic_sdlc.build.scaffold import ScaffoldError, required_runtimes, scaffold
from agentic_sdlc.crews.base import PhaseError, TaskResult, UsageLimitError
from agentic_sdlc.registry.profiles import Component, Profile
from agentic_sdlc.state import ProjectState
from agentic_sdlc.tools.sandbox_exec import SandboxRunner
from agentic_sdlc.workspace import Workspace

log = logging.getLogger(__name__)
PHASE = "build"


@dataclass
class BuildConfig:
    milestones: list[str]          # empty = all, in backlog order
    check_fix_attempts: int = 2
    qa_fix_rounds: int = 3

    @classmethod
    def from_pipeline(cls, pipeline: dict[str, Any]) -> "BuildConfig":
        b = pipeline.get("build", {}) or {}
        override = os.environ.get("SDLC_BUILD_MILESTONES")
        milestones = [m.strip() for m in override.split(",") if m.strip()] if override else list(b.get("milestones") or [])
        return cls(
            milestones=milestones,
            check_fix_attempts=b.get("check_fix_attempts", 2),
            qa_fix_rounds=pipeline.get("limits", {}).get("qa_fix_rounds", 3),
        )


class Builder:
    def __init__(
        self,
        state: ProjectState,
        workspace: Workspace,
        profile: Profile,
        sandbox: SandboxRunner,
        worker_for: Callable[[str], Worker],
        config: BuildConfig,
        record: Callable[[TaskResult], Any],
        checkpoint: Callable[[str], None],
        can_continue: Callable[[], bool],
        stop: Callable[[str], None],
    ):
        self.s = state
        self.ws = workspace
        self.profile = profile
        self.sandbox = sandbox
        self.worker_for = worker_for
        self.cfg = config
        self.record = record
        self.checkpoint = checkpoint
        self.can_continue = can_continue
        self.stop = stop
        self.items: dict[str, WorkItem] = {w.id: w for w in state.backlog.work_items}
        self._unavailable: dict[str, str] = {}  # component -> reason

    # ---------- selection ----------

    def selected_milestones(self) -> list[Milestone]:
        ms = self.s.backlog.milestones
        if not self.cfg.milestones:
            return ms
        unknown = set(self.cfg.milestones) - {m.id for m in ms}
        if unknown:
            raise ValueError(f"build.milestones lists unknown milestones: {sorted(unknown)}")
        return [m for m in ms if m.id in self.cfg.milestones]

    def ordered_items(self, m: Milestone) -> list[WorkItem]:
        """Milestone items in dependency order (dependencies inside the milestone first)."""
        ids = [wid for wid in m.work_item_ids if wid in self.items]
        done: list[str] = []
        pending = list(ids)
        while pending:
            ready = [w for w in pending if all(d not in pending or d in done for d in self.items[w].depends_on)]
            nxt = ready[0] if ready else pending[0]  # cycles are rejected at planning; be safe anyway
            done.append(nxt)
            pending.remove(nxt)
        return [self.items[w] for w in done]

    # ---------- run ----------

    def run(self) -> None:
        milestones = self.selected_milestones()
        self.prepare_toolchains(milestones)
        for m in milestones:
            mp = self.s.build.milestone(m.id)
            if mp.status == "done":
                continue
            # A partial milestone is retried: blocked/failed items get another go, since the
            # cause (a missing toolchain, a setup error) may have been fixed since.
            newly_done = False
            for item in self.ordered_items(m):
                if not self.can_continue():
                    return
                was_done = self.s.build.item(item.id).status == "done"
                self.build_item(m, item)
                newly_done |= not was_done and self.s.build.item(item.id).status == "done"
            if not self.can_continue():
                return
            if mp.status == "todo" or newly_done or mp.status == "failed":
                self.qa_milestone(m)
            if self.s.status != "running":
                return

    def prepare_toolchains(self, milestones: list[Milestone]) -> None:
        """Make the toolchains for the components still to build ready (e.g. pull Docker images)."""
        components = {self.items[w].component for m in milestones for w in m.work_item_ids
                      if w in self.items and self.s.build.item(w).status != "done"}
        runtimes = [rt for c in sorted(components) if c in self.profile.components
                    for rt in required_runtimes(self.profile.components[c])]
        for runtime, error in self.sandbox.prepare(runtimes).items():
            log.warning("Toolchain %s unavailable: %s", runtime, error)

    # ---------- work items ----------

    def component(self, item: WorkItem) -> Component:
        comp = self.profile.components.get(item.component)
        if comp is None:
            raise ValueError(f"Profile has no component '{item.component}' (needed by {item.id})")
        return comp

    def block_reason(self, item: WorkItem) -> str | None:
        for dep in item.depends_on:
            dp = self.s.build.items.get(dep)
            if dp is None or dp.status != "done":
                state = dp.status if dp else "not built (outside the selected milestones)"
                return f"depends on {dep}, which is {state}"
        comp = self.component(item)
        if item.component in self._unavailable:
            return self._unavailable[item.component]
        for rt in required_runtimes(comp):
            reason = self.sandbox.unavailable_reason(rt)
            if reason:
                self._unavailable[item.component] = reason
                return reason
        return None

    def ensure_scaffold(self, name: str, comp: Component) -> str | None:
        if name in self.s.build.scaffolded or not comp.scaffold:
            return None
        try:
            steps = scaffold(name, comp, self.ws, self.sandbox)
        except ScaffoldError as e:
            self._unavailable[name] = f"project setup failed: {str(e)[:500]}"
            return self._unavailable[name]
        self.s.build.scaffolded.append(name)
        self.ws.write_text(f"reports/scaffold_{name}.log", "\n".join(steps) + "\n")
        self.checkpoint(f"Build: scaffold {name}")
        return None

    def run_checks(self, comp: Component) -> tuple[bool, str]:
        if not comp.runtime:
            return True, ""
        for cmd in comp.checks:
            result = self.sandbox.run_trusted(comp.runtime, comp.workdir, cmd)
            if not result.ok:
                return False, f"`{cmd}` failed (exit {result.exit_code}):\n{result.output[-6000:]}"
        return True, ""

    def stories_text(self, story_ids: list[str]) -> str:
        stories = {s.id: s for s in self.s.prd.user_stories}
        out = []
        for sid in story_ids:
            s = stories.get(sid)
            if s:
                out.append(f"{s.id} {s.title}: As a {s.as_a}, I want {s.i_want}, so that {s.so_that}.")
                out += [f"  - Given {c.given} when {c.when} then {c.then}" for c in s.acceptance_criteria]
        return "\n".join(out) or "(no user stories: technical item)"

    @staticmethod
    def links_text(item: WorkItem) -> str:
        """What the plan says this item builds, so the developer knows exactly what it owns."""
        parts = [(label, values) for label, values in (
            ("API operations", item.api_operations), ("data models", item.data_models),
            ("screens", item.screens), ("modules", item.modules)) if values]
        return ("\nPlanned scope: " + "; ".join(f"{label}: {', '.join(v)}" for label, v in parts)) if parts else ""

    def done_summary(self) -> str:
        lines = [f"- {wid} {self.items[wid].title}: {p.summary[:200]}" for wid, p in self.s.build.items.items()
                 if p.status == "done" and wid in self.items]
        return "\n".join(lines) or "(none yet)"

    def item_inputs(self, m: Milestone, item: WorkItem, comp: Component, problems: str) -> dict[str, Any]:
        return {
            "item_id": item.id,
            "item_title": item.title,
            "item_description": item.description + self.links_text(item),
            "component": item.component,
            "milestone": f"{m.id} {m.name}: {m.goal}",
            "stories": self.stories_text(item.story_ids),
            "done_items": self.done_summary(),
            "docs_dir": str(self.ws.root / "docs"),
            "checks": "; ".join(comp.checks) or "(none)",
            "problems": problems or "(none)",
        }

    def build_item(self, m: Milestone, item: WorkItem) -> None:
        p = self.s.build.item(item.id)
        if p.status == "done":
            return
        comp = self.component(item)
        reason = self.block_reason(item) or self.ensure_scaffold(item.component, comp)
        if reason:
            p.status, p.reason = "blocked", reason
            self.checkpoint(f"Build: {item.id} blocked")
            return

        outcome, result, detail = self._work_until_green(m, item, comp, "implement_work_item", "")
        if outcome == "done":
            p.status, p.summary, p.reason = "done", result.summary, ""
            p.commit = self.ws.commit(f"{item.id}: {item.title} ({comp.agent})")
        elif outcome == "blocked":
            p.status, p.reason, p.summary = "blocked", detail, result.summary if result else ""
        else:
            p.status, p.reason = "failed", detail
        self.checkpoint(f"Build: {item.id} {p.status}")

    def _work_until_green(self, m: Milestone, item: WorkItem, comp: Component, first_task: str,
                          problems: str) -> tuple[str, WorkItemResult | None, str]:
        """Run the agent, then the checks; feed failing check output back to the agent until the
        checks pass or attempts run out. Returns (outcome, last result, reason): outcome is
        done, blocked or failed. Used for new work items and for QA bug fixes alike."""
        p = self.s.build.item(item.id)
        task_key = first_task
        result = None
        for attempt in range(1, self.cfg.check_fix_attempts + 2):
            p.attempts += 1
            result = self._work(comp, task_key, self.item_inputs(m, item, comp, problems))
            if result is None:
                return "failed", None, "the developer agent failed (see reports/agent_failures and logs)"
            if result.blocked:
                return "blocked", result, result.blocked_reason or "agent reported blocked"
            ok, output = self.run_checks(comp)
            if ok:
                return "done", result, ""
            problems = f"The checks failed after your change. Fix the cause.\n{output}"
            task_key = "fix_work_item"
        return "failed", result, f"checks still failing after {attempt} attempt(s). Last output:\n{output[-1500:]}"

    def _work(self, comp: Component, task_key: str, inputs: dict[str, Any]) -> WorkItemResult | None:
        job = Job(PHASE, comp.agent, task_key, inputs, WorkItemResult, comp.workdir, comp.runtime)
        try:
            return self.record(self.worker_for(comp.agent).run(job))
        except UsageLimitError as e:
            self.stop(f"{e}. Resume the run after the limit resets (uv run resume <run_id>).")
            return None
        except PhaseError as e:
            log.error("%s", e)
            return None

    # ---------- QA ----------

    def qa_milestone(self, m: Milestone) -> None:
        mp = self.s.build.milestone(m.id)
        items = [self.items[w] for w in m.work_item_ids if w in self.items]
        done = [i for i in items if self.s.build.item(i.id).status == "done"]
        not_done = [i for i in items if i not in done]
        if not done:
            mp.status = "partial"
            self.checkpoint(f"Build: {m.id} nothing buildable, QA skipped")
            return

        session_rounds = 0  # the fix-round limit applies per run, so a resume gets fresh rounds
        while True:
            mp.qa_rounds += 1
            session_rounds += 1
            report = self._qa(m, done, not_done)
            if report is None:
                self.stop(f"QA agent failed on {m.id}")
                break
            mp.qa_reports.append(report)
            self.ws.write_text(f"reports/qa_{m.id}_round{mp.qa_rounds}.md", report.to_markdown())
            self.ws.commit(f"QA {m.id} round {mp.qa_rounds}: {'passed' if report.passed else 'failed'}")
            bugs = report.blocking_bugs()
            if not bugs:
                mp.status = "done" if not not_done else "partial"
                break
            if session_rounds > self.cfg.qa_fix_rounds:
                mp.status = "failed"
                self.stop(f"{m.id}: {len(bugs)} blocking bug(s) remain after {self.cfg.qa_fix_rounds} fix rounds; "
                          f"see reports/qa_{m.id}_round{mp.qa_rounds}.md")
                break
            self.fix_bugs(m, bugs)
            if not self.can_continue():
                break
        self.checkpoint(f"Build: {m.id} {mp.status}")

    def _qa(self, m: Milestone, done: list[WorkItem], not_done: list[WorkItem]) -> QAReport | None:
        runtimes = sorted({self.component(i).runtime for i in done if self.component(i).runtime})
        inputs = {
            "milestone": f"{m.id} {m.name}: {m.goal}",
            "milestone_id": m.id,
            "items": "\n".join(f"- {i.id} [{i.component}] {i.title}: {self.s.build.item(i.id).summary[:300]}" for i in done),
            "not_built": "\n".join(f"- {i.id} {i.title}: {self.s.build.item(i.id).reason}" for i in not_done) or "(none)",
            "stories": self.stories_text(sorted({sid for i in done for sid in i.story_ids})),
            "docs_dir": str(self.ws.root / "docs"),
        }
        job = Job(PHASE, "qa_engineer", "qa_milestone", inputs, QAReport, ".", runtimes[0] if runtimes else None, runtimes[1:])
        try:
            return self.record(self.worker_for("qa_engineer").run(job))
        except UsageLimitError as e:
            self.stop(f"{e}. Resume the run after the limit resets (uv run resume <run_id>).")
            return None
        except PhaseError as e:
            log.error("%s", e)
            return None

    def fix_bugs(self, m: Milestone, bugs: list[Bug]) -> None:
        by_item: dict[str, list[Bug]] = {}
        for b in bugs:
            by_item.setdefault(b.work_item_id if b.work_item_id in self.items else m.work_item_ids[0], []).append(b)
        for wid, item_bugs in by_item.items():
            if not self.can_continue():
                return
            item = self.items[wid]
            comp = self.component(item)
            text = "QA found these bugs. Fix them and add or update tests that prove the fix:\n" + "\n".join(
                f"- {b.id} [{b.severity}] {b.title}\n  Steps: {b.steps}\n  Expected: {b.expected}\n  Actual: {b.actual}"
                for b in item_bugs
            )
            outcome, _, detail = self._work_until_green(m, item, comp, "fix_work_item", text)
            if outcome == "done":
                self.ws.commit(f"{wid}: fix {', '.join(b.id for b in item_bugs)}")
            else:
                log.warning("Bug fix on %s did not complete: %s", wid, detail[:300])
            self.checkpoint(f"Build: {wid} bug fixes")
