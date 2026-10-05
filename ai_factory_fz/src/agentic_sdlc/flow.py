"""SDLCFlow: runs the SDLC phases in order, with human gates, revision loops and checkpoints.

Every phase is idempotent: it skips work whose artifact is already in the state.
That is what makes resume work: reload state.json and kick off the flow again.
Rejecting a gate clears that artifact, so the next pass rewrites it using the feedback.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import PrivateAttr

from agentic_sdlc.build.coders import Worker, make_worker
from agentic_sdlc.build.loop import BuildConfig, Builder
from agentic_sdlc.build.sync import sync_build_with_backlog
from agentic_sdlc import preflight
from agentic_sdlc.crews import design, discovery, estimation, planning
from agentic_sdlc.guardrails import agents as agent_guardrails
from agentic_sdlc.guardrails import architecture as architecture_guardrails
from agentic_sdlc.crews.base import TaskResult, TaskRunner
from agentic_sdlc.gates.human import InputFn, gate_mode, request_approval
from agentic_sdlc.registry.agents import AgentRegistry
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.release.device import AndroidToolchain, Emulator
from agentic_sdlc.release.releaser import Releaser
from agentic_sdlc.release.staging import Staging
from agentic_sdlc.scope import Scope
from agentic_sdlc.settings import load_config
from agentic_sdlc.state import GateDecision, ProjectState
from agentic_sdlc.tools.registry import build_tool_resolver
from agentic_sdlc.env_toolchain import apply_toolchain_path
from agentic_sdlc.tools.sandbox_exec import SandboxRunner, sandbox_mode
from agentic_sdlc.workspace import Workspace

log = logging.getLogger(__name__)


@dataclass
class Deps:
    workspace: Workspace
    profile: Profile
    runner: TaskRunner
    pipeline: dict[str, Any]
    input_fn: InputFn = input
    sandbox: SandboxRunner | None = None
    worker_for: Callable[[str], Worker] | None = None
    staging: Staging | None = None
    emulator: Emulator | None = None
    preflight: Callable[[], list[str]] | None = None   # machine checks; problems stop the run early
    extra: dict[str, Any] = field(default_factory=dict)


def default_deps(state: ProjectState) -> Deps:
    apply_toolchain_path()
    profile = Profile.load(state.profile)
    workspace = Workspace.create(state.run_id)
    pipeline = load_config(state.pipeline)
    build_cfg = pipeline.get("build", {}) or {}
    sandbox = SandboxRunner(workspace, profile.sandbox, sandbox_mode(build_cfg.get("sandbox", "docker")))
    agents = AgentRegistry.from_config(profile, build_tool_resolver(workspace, sandbox), pipeline.get("models"))
    runner = TaskRunner(agents, workspace=workspace)
    timeout = build_cfg.get("agent_timeout_s", 3600)
    release_cfg = pipeline.get("release", {}) or {}
    staging = Staging(workspace, profile, sandbox, port=release_cfg.get("staging_port", 3100),
                      startup_timeout_s=release_cfg.get("startup_timeout_s", 90))
    emulator = None
    if profile.device and (release_cfg.get("device") or {}).get("enabled"):
        device_rt = profile.components[profile.device.app_component].runtime
        emulator = Emulator(AndroidToolchain(profile.device), sandbox, workspace, runtime=device_rt,
                            boot_timeout_s=(release_cfg.get("device") or {}).get("boot_timeout_s", 300))
    return Deps(
        workspace=workspace, profile=profile, runner=runner, pipeline=pipeline, sandbox=sandbox, staging=staging,
        emulator=emulator,
        worker_for=lambda agent_key: make_worker(agent_key, agents, runner.tasks, workspace, sandbox, timeout),
        preflight=lambda: preflight.check(pipeline, profile, sandbox, agents.models),
    )


class SDLCFlow(Flow[ProjectState]):
    _deps_factory: Callable[[ProjectState], Deps] | None = PrivateAttr(default=None)
    _deps: Deps | None = PrivateAttr(default=None)
    _restore_json: str | None = PrivateAttr(default=None)

    def __init__(self, deps_factory: Callable[[ProjectState], Deps] | None = None, restore_json: str | None = None, **data: Any):
        super().__init__(**data)
        self._deps_factory = deps_factory
        self._restore_json = restore_json

    # ---------- helpers ----------

    @property
    def deps(self) -> Deps:
        assert self._deps is not None, "init_run has not run"
        return self._deps

    def _checkpoint(self, message: str) -> None:
        self.deps.workspace.save_state(self.state)
        self.deps.workspace.commit(message)

    def _record(self, result: TaskResult) -> Any:
        self.state.usage.append(result.usage)
        return result.artifact

    @property
    def _scope(self) -> Scope:
        from agentic_sdlc.release.contract import strip_prefix

        rel = self.deps.profile.release
        infra = tuple(strip_prefix(p, rel.api_prefix) for p in (rel.health_path, rel.openapi_json_path) if p)
        return Scope.from_pipeline(self.deps.pipeline, infra_paths=infra)

    def _phase_enabled(self, phase: str) -> bool:
        return bool(self.deps.pipeline.get("phases", {}).get(phase, False))

    def _stop(self, reason: str) -> None:
        if self.state.status == "stopped":
            log.warning("Also: %s", reason)  # keep the first (root-cause) reason
            return
        self.state.status = "stopped"
        self.state.stop_reason = reason
        log.warning("Run stopped: %s", reason)

    def _over_budget(self) -> bool:
        limit = self.deps.pipeline.get("budget", {}).get("max_total_tokens")
        if limit and self.state.uncached_tokens() > limit:
            self._stop(f"Token budget exceeded ({self.state.uncached_tokens()} uncached tokens > {limit})")
            return True
        return False

    def _can_continue(self) -> bool:
        return self.state.status == "running" and not self._over_budget()

    def _gate(self, gate: str, summary: str, docs: list[str], discard: Callable[[], None]) -> str:
        """Returns '<gate>_approved', '<gate>_rejected' or 'stopped'.

        On rejection, `discard` drops the rejected artifact before the checkpoint, so the
        next pass (or a resume) rewrites it with the feedback instead of re-asking about it.
        """
        if self.state.status != "running":
            return "stopped"
        if self.state.gate_approved(gate):
            return f"{gate}_approved"
        if not self.deps.pipeline.get("gates", {}).get(gate, True):
            decision = GateDecision(gate=gate, approved=True, decided_by="config")
        else:
            decision = request_approval(
                gate,
                summary,
                [self.deps.workspace.root / d for d in docs],
                gate_mode(self.deps.pipeline.get("gate_mode", "console")),
                self.deps.input_fn,
            )
        self.state.gate_history.append(decision)
        if decision.approved:
            self._checkpoint(f"Gate {gate}: approved")
            return f"{gate}_approved"
        discard()
        limit = self.deps.pipeline.get("limits", {}).get("gate_rejections", 3)
        if len(self.state.rejections(gate)) >= limit:
            self._stop(f"Gate '{gate}' rejected {limit} times")
            self._checkpoint(f"Gate {gate}: rejected, run stopped")
            return "stopped"
        self._checkpoint(f"Gate {gate}: rejected")
        return f"{gate}_rejected"

    # ---------- flow ----------

    @start()
    def init_run(self) -> None:
        if self._restore_json:
            restored = ProjectState.model_validate_json(self._restore_json)
            for name in ProjectState.model_fields:
                if name != "id":
                    setattr(self.state, name, getattr(restored, name))
            # Resuming continues from where the run stopped, or runs phases enabled since it completed.
            self.state.status, self.state.stop_reason = "running", ""
        if not self.state.run_id:
            raise ValueError("run_id is required")
        self._deps = (self._deps_factory or default_deps)(self.state)
        self._checkpoint("Run started")
        if self.deps.preflight:
            problems = self.deps.preflight()
            print(preflight.report(problems), flush=True)
            if problems:
                self._stop(preflight.report(problems) + f"\nThen run: uv run resume {self.state.run_id}")

    @listen(init_run)
    def discovery_phase(self) -> None:
        if not self._can_continue() or not self._phase_enabled("discovery"):
            return
        runner, ws = self.deps.runner, self.deps.workspace
        if self.state.product_brief is None:
            self.state.product_brief = self._record(discovery.expand_brief(runner, self.state.brief))
            ws.save_artifact("product_brief", self.state.product_brief)
            self._checkpoint("Discovery: product brief")
        if not self.state.clarifications:
            max_rounds = self.deps.pipeline.get("limits", {}).get("clarification_rounds", 3)
            history, results = discovery.clarify(runner, self.state.product_brief, [], max_rounds,
                                                 agent_guardrails.enabled(self.deps.pipeline))
            for r in results:
                self._record(r)
            self.state.clarifications = history
            ws.write_text("docs/clarifications.md", "# Clarifications\n\n" + discovery.format_qa(history) + "\n")
            self._checkpoint("Discovery: clarifications")
        self._write_prd()

    def _write_prd(self) -> None:
        if self.state.prd is not None or not self._can_continue():
            return
        self.state.prd = self._record(
            discovery.write_prd(
                self.deps.runner,
                self.state.product_brief,
                self.state.clarifications,
                self.deps.profile.stack_summary(),
                self.state.revision_notes("prd"),
                self._scope,
            )
        )
        self.deps.workspace.save_artifact("prd", self.state.prd)
        self._checkpoint("Discovery: PRD")

    @router(or_(discovery_phase, "revise_prd"))
    def prd_gate(self) -> Literal["prd_approved", "prd_rejected", "stopped"]:
        if self.state.prd is None:
            if self.state.status == "running":
                self._stop("No PRD was produced (is the discovery phase disabled?)")
            return "stopped"
        prd = self.state.prd
        summary = f"PRD '{prd.title}': {len(prd.user_stories)} user stories, {len(prd.must_have_ids())} must-have."
        return self._gate("prd", summary, ["docs/prd.md", "docs/clarifications.md"], lambda: setattr(self.state, "prd", None))

    @listen("prd_rejected")
    def revise_prd(self) -> None:
        self._write_prd()

    @listen("prd_approved")
    def solution_phase(self) -> None:
        """Architect designs the solution, UI/UX designs the screens, then the Project manager
        breaks the solution down into estimated, linked work items."""
        self._write_solution()

    def _write_solution(self) -> None:
        ws, notes = self.deps.workspace, self.state.revision_notes("architecture")
        if self._phase_enabled("planning") and self.state.architecture is None and self._can_continue():
            arch = self._record(planning.design_architecture(
                self.deps.runner, self.state.prd, self.deps.profile.stack_summary(),
                self.deps.profile.domain_entities, notes, self._scope,
                guardrails=architecture_guardrails.checker(self.deps.profile, self.deps.pipeline),
            ))
            self.state.architecture = arch
            ws.save_artifact("architecture", arch)
            ws.write_text("docs/openapi.yaml", arch.openapi_yaml)
            ws.write_text("docs/schema.prisma", arch.prisma_schema)
            self._checkpoint("Planning: architecture, OpenAPI contract, Prisma schema")
        if (self._phase_enabled("design") and self.state.design is None and self.state.architecture is not None
                and self._can_continue()):
            self.state.design = self._record(design.design_ui(
                self.deps.runner, self.state.prd, self.state.architecture, self._scope, notes,
                agent_guardrails.enabled(self.deps.pipeline)))
            ws.save_artifact("design_system", self.state.design)
            self._checkpoint("Design: design system and screen specs")
        if (self._phase_enabled("planning") and self.state.backlog is None and self.state.architecture is not None
                and self._can_continue()):
            self.state.backlog = self._record(planning.plan_work(
                self.deps.runner, self.state.prd, self.state.architecture, self.state.design,
                self.deps.profile.stack_summary(), notes, self._scope,
            ))
            ws.save_artifact("backlog", self.state.backlog)
            self._checkpoint("Planning: work breakdown and estimates")
        est = estimation.EstimationConfig.from_pipeline(self.deps.pipeline)
        # Only while Gate 2 is open: an approved plan is not re-estimated behind the reviewer's back.
        if est.enabled and self.state.backlog is not None and not self.state.backlog.estimation_reviewed \
                and not self.state.gate_approved("architecture") and self._can_continue():
            for result in estimation.review_estimates(self.deps.runner, self.state.backlog, self.state.architecture,
                                                      self.deps.profile, est):
                self._record(result)
            ws.save_artifact("backlog", self.state.backlog)
            self._checkpoint("Planning: developers' estimation review")

    @router(or_(solution_phase, "revise_solution"))
    def architecture_gate(self) -> Literal["architecture_approved", "architecture_rejected", "stopped"]:
        if self.state.architecture is None or self.state.backlog is None:
            if self.state.status == "running":
                self._stop("No architecture or plan was produced (is the planning phase disabled?)")
            return "stopped"
        a, b = self.state.architecture, self.state.backlog
        screens = f", {len(self.state.design.screens)} screens" if self.state.design else ""
        summary = (
            f"Solution: {len(a.backend_modules)} backend modules, {len(a.operations())} API operations, "
            f"{len(a.data_models())} data models{screens}, {len(a.adrs)} ADRs. Plan: {len(b.work_items)} work items, "
            f"{b.total_points()} points in {len(b.milestones)} milestones; critical path {' → '.join(b.critical_path())}."
        )
        if b.estimation_reviewed:
            changed = sum(1 for w in b.work_items if w.pm_points is not None and w.pm_points != w.estimate_points)
            disputed = sum(1 for w in b.work_items if w.disagreement)
            summary += (f" Estimates reviewed by the developers: {changed} changed from the PM's draft, "
                        f"{disputed} big disagreements reconciled (see docs/backlog.md).")
        docs = ["docs/architecture.md", "docs/openapi.yaml", "docs/schema.prisma", "docs/design_system.md", "docs/backlog.md"]

        def discard() -> None:
            # A change to the design changes the plan: rewrite all three with the feedback.
            self.state.architecture = self.state.design = self.state.backlog = None

        return self._gate("architecture", summary, docs, discard)

    @listen("architecture_rejected")
    def revise_solution(self) -> None:
        self._write_solution()

    @router("architecture_approved")
    def after_solution(self) -> Literal["build_requested", "release_requested", "run_finished", "stopped"]:
        if self.state.status != "running":
            return "stopped"
        if self._phase_enabled("build"):
            return "build_requested"
        return self._after_build()

    @router("build_requested")
    def build_phase(self) -> Literal["release_requested", "run_finished", "stopped"]:
        sync_build_with_backlog(self.state)
        done_before = {w for w, p in self.state.build.items.items() if p.status == "done"}
        if self._can_continue():
            Builder(
                state=self.state,
                workspace=self.deps.workspace,
                profile=self.deps.profile,
                sandbox=self.deps.sandbox,
                worker_for=self.deps.worker_for,
                config=BuildConfig.from_pipeline(self.deps.pipeline),
                record=self._record,
                checkpoint=self._checkpoint,
                can_continue=self._can_continue,
                stop=self._stop,
            ).run()
        done_now = {w for w, p in self.state.build.items.items() if p.status == "done"}
        if done_now - done_before and (self.state.release.deployment or self.state.release.rounds):
            # New features since the last release verification: verify again, with a smoke
            # suite that covers them.
            self.state.reopen_release("New build work since the last release verification")
            self.state.release.smoke_suite = None
            self.state.release.device_suite = None
            self._checkpoint("Release: re-verification needed after new build work")
        if self.state.status != "running":
            return "stopped"
        return self._after_build()

    def _after_build(self) -> Literal["release_requested", "run_finished", "stopped"]:
        if self._phase_enabled("release"):
            if not any(p.status == "done" for p in self.state.build.items.values()):
                if self.state.build.items:
                    self._stop("Nothing could be built, so there is nothing to release: every work item is "
                               "blocked or failed. See the Build table in reports/run_summary.md for the reasons, "
                               "fix the cause and resume.")
                else:
                    self._stop("The release phase needs built work items; enable the build phase and resume")
                return "stopped"
            return "release_requested"
        return "run_finished"

    def _releaser(self) -> Releaser:
        return Releaser(
            state=self.state,
            workspace=self.deps.workspace,
            profile=self.deps.profile,
            sandbox=self.deps.sandbox,
            worker_for=self.deps.worker_for,
            staging=self.deps.staging,
            config=self.deps.pipeline.get("release", {}) or {},
            record=self._record,
            checkpoint=self._checkpoint,
            can_continue=self._can_continue,
            stop=self._stop,
            emulator=self.deps.emulator,
            guard_rules=agent_guardrails.enabled(self.deps.pipeline),
        )

    @router(or_("release_requested", "revise_release"))
    def release_phase(self) -> Literal["release_ready", "stopped"]:
        if self._can_continue():
            self._releaser().verify()
        if self.state.status != "running" or not self.state.release.verified:
            return "stopped"
        return "release_ready"

    @router("release_ready")
    def release_gate(self) -> Literal["release_approved", "release_rejected", "stopped"]:
        n = self.state.release.rounds
        docs = [f"reports/release_round{n}.md", "infra/README.md"]
        return self._gate("release", self._releaser().gate_summary(), docs,
                          lambda: self.state.release.reset_verification())

    @listen("release_rejected")
    def revise_release(self) -> None:
        # The reviewer's feedback goes to the developer; then staging is verified again.
        if self._can_continue():
            self._releaser().fix("The release reviewer rejected this release:\n" + self.state.revision_notes("release"))

    @router("release_approved")
    def production_phase(self) -> Literal["run_finished", "stopped"]:
        if self._can_continue():
            self._releaser().production()
        return "run_finished" if self.state.status == "running" else "stopped"

    @listen(or_("run_finished", "stopped"))
    def finish(self) -> ProjectState:
        if self.state.status == "running":
            self.state.status = "completed"
        self.deps.workspace.write_text("reports/run_summary.md", self._summary_markdown())
        self._checkpoint(f"Run {self.state.status}")
        return self.state

    def _summary_markdown(self) -> str:
        s = self.state
        lines = [f"# Run {s.run_id}", "", f"Status: **{s.status}**"]
        lines.append("Architect guardrails enforced: "
                     + ", ".join(architecture_guardrails.enabled_rules(self.deps.pipeline)))
        if s.stop_reason:
            lines.append(f"Stop reason: {s.stop_reason}")
        lines += ["", "## Gates", "| Gate | Approved | By | Feedback | At |", "|---|---|---|---|---|"]
        lines += [f"| {g.gate} | {g.approved} | {g.decided_by} | {g.feedback or '-'} | {g.decided_at} |" for g in s.gate_history]
        r = s.release
        if r.rounds or r.deployment:
            lines += ["", "## Release", f"Staging rounds: {r.rounds}; verified: {r.verified}; "
                      f"smoke: {r.smoke_passed}; production: {r.production}"]
            if r.production_notes:
                lines.append(r.production_notes)
        if s.build.items or s.build.milestones:
            lines += ["", "## Build", "| Milestone | Status | QA rounds |", "|---|---|---|"]
            lines += [f"| {mid} | {mp.status} | {mp.qa_rounds} |" for mid, mp in s.build.milestones.items()]
            lines += ["", "| Work item | Status | Attempts | Notes |", "|---|---|---|---|"]
            for wid, ip in s.build.items.items():
                note = (ip.reason or ip.summary).replace("|", "/").replace("\n", " ")[:160]
                lines.append(f"| {wid} | {ip.status} | {ip.attempts} | {note} |")
        lines += ["", "## Token usage by agent", "| Agent | Model | Calls | Tokens | Uncached |", "|---|---|---|---|---|"]
        totals: dict[tuple[str, str], list[int]] = {}
        for u in s.usage:
            t = totals.setdefault((u.agent, u.model), [0, 0, 0])
            t[0] += 1
            t[1] += u.total_tokens
            t[2] += u.uncached_tokens
        lines += [f"| {a} | {m} | {c} | {n:,} | {un:,} |" for (a, m), (c, n, un) in totals.items()]
        lines += ["", f"Total tokens: {s.total_tokens():,} ({s.uncached_tokens():,} uncached; the budget counts uncached)", ""]
        return "\n".join(lines)
