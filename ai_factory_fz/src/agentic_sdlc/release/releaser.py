"""Release phase: staging deployment, integration pass, smoke test, then production.

verify():
  1. Deployment engineer writes the Dockerfile, staging compose file, staging env (test values)
     and CI workflow.                                                    (once)
  2. Smoke tester writes the smoke suite for the journeys that are built. (once)
  3. Round: start staging -> contract check (served OpenAPI vs docs/openapi.yaml) ->
     Integration pass reviews wiring/config and reports bugs -> smoke suite runs against
     staging -> stop staging. Problems go to the developer, then the next round.
     Rounds are limited; if problems remain the run stops for a human.
production(): package the release (build, notes, git tag) and, if a production command is
  configured, run it.
"""

import logging
import os
import shlex
import subprocess
import time
from datetime import datetime
from typing import Any, Callable

from agentic_sdlc.artifacts.reports import QAReport, WorkItemResult
from agentic_sdlc.build.coders import Job, Worker
from agentic_sdlc.crews.base import PhaseError, TaskResult, UsageLimitError
from agentic_sdlc.guardrails import agents as agent_guardrails
from agentic_sdlc.guardrails import code as code_guardrails
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.release.device import DeviceError, Emulator
from agentic_sdlc.release.contract import contract_diff
from agentic_sdlc.release.staging import Staging, StagingError, http_get
from agentic_sdlc.state import ProjectState
from agentic_sdlc.tools.sandbox_exec import SandboxRunner
from agentic_sdlc.workspace import Workspace

log = logging.getLogger(__name__)
PHASE = "release"


class Releaser:
    def __init__(
        self,
        state: ProjectState,
        workspace: Workspace,
        profile: Profile,
        sandbox: SandboxRunner,
        worker_for: Callable[[str], Worker],
        staging: Staging,
        config: dict[str, Any],
        record: Callable[[TaskResult], Any],
        checkpoint: Callable[[str], None],
        can_continue: Callable[[], bool],
        stop: Callable[[str], None],
        emulator: Emulator | None = None,
        guard_rules: set[str] | None = None,
    ):
        self.emulator = emulator
        self.guard_rules = guard_rules or set()
        self.s = state
        self.r = state.release
        self.ws = workspace
        self.profile = profile
        self.api = profile.components[profile.release.api_component]
        self.sandbox = sandbox
        self.worker_for = worker_for
        self.staging = staging
        self.cfg = config
        self.record = record
        self.checkpoint = checkpoint
        self.can_continue = can_continue
        self.stop = stop

    # ---------- helpers ----------

    @property
    def api_base_url(self) -> str:
        """Base URL clients use, including the API prefix, e.g. http://localhost:3100/api/v1."""
        return self.staging.base_url + self.profile.release.api_prefix

    def built_summary(self) -> str:
        items = {w.id: w for w in self.s.backlog.work_items}
        lines = [f"- {wid} [{items[wid].component}] {items[wid].title}" for wid, p in self.s.build.items.items()
                 if p.status == "done" and wid in items]
        return "\n".join(lines) or "(nothing built)"

    def not_built_summary(self) -> str:
        items = {w.id: w for w in self.s.backlog.work_items}
        lines = [f"- {wid} {items[wid].title}: {p.status} ({p.reason[:120]})" for wid, p in self.s.build.items.items()
                 if p.status != "done" and wid in items]
        return "\n".join(lines) or "(none)"

    def _job(self, agent: str, task_key: str, inputs: dict[str, Any], model, workdir: str,
             runtime: str | None = "api", feedback: str = "") -> Any:
        rt = self.api.runtime if runtime == "api" else runtime
        job = Job(PHASE, agent, task_key, {**self._common(), **inputs}, model, workdir, rt, feedback=feedback)
        try:
            return self.record(self.worker_for(agent).run(job))
        except UsageLimitError as e:
            self.stop(f"{e}. Resume the run after the limit resets (uv run resume <run_id>).")
            return None
        except PhaseError as e:
            log.error("%s", e)
            return None

    def _common(self) -> dict[str, Any]:
        rel = self.profile.release
        return {
            "docs_dir": str(self.ws.root / "docs"),
            "built": self.built_summary(),
            "not_built": self.not_built_summary(),
            "api_dir": self.api.workdir,
            "health_path": rel.health_path,
            "openapi_json_path": rel.openapi_json_path or "(not required)",
            "compose_file": rel.compose_file,
            "env_file": rel.env_file,
            "smoke_command": rel.smoke_command,
            "port": self.staging.port,
            "api_base_example": f"http://localhost:{self.staging.port}{self.profile.release.api_prefix}",
            "toolchain_image": self.profile.sandbox.runtimes[self.api.runtime].image if self.api.runtime else "(none)",
        }

    # ---------- guardrails ----------

    def _guarded(self, agent: str, task_key: str, inputs: dict[str, Any], model, workdir: str,
                 runtime: str | None, check: Callable[[Any], list[str]], what: str) -> Any:
        """Run a job; if its guardrail check fails, re-run it once with the reasons. If it still
        fails, discard its uncommitted changes and stop the run. Returns the result or None."""
        result = self._job(agent, task_key, inputs, model, workdir, runtime)
        if result is None or result.blocked:
            return result
        problems = check(result)
        if problems:
            result = self._job(agent, task_key, inputs, model, workdir, runtime, feedback="\n".join(problems))
            problems = check(result) if result is not None and not result.blocked else problems
        if problems:
            code_guardrails.discard_changes(self.ws, workdir)
            self.stop(f"{what} was rejected by guardrails:\n- " + "\n- ".join(problems))
            return None
        return result

    def _code_rules(self) -> set[str]:
        return self.guard_rules & set(code_guardrails.CODE_RULES)

    def _deployment_problems(self, _result: Any) -> list[str]:
        problems = agent_guardrails.de1_container(self.ws, self.profile) if "DE1" in self.guard_rules else []
        if "DV2" in self.guard_rules:
            problems += code_guardrails.dv2_secrets(self.ws, self.profile, code_guardrails.changed_files(self.ws))
        return problems

    def _smoke_problems(self, _result: Any) -> list[str]:
        if "ST1" not in self.guard_rules:
            return []
        return agent_guardrails.st1_smoke_suite(self.ws, self.profile, self.cfg.get("min_smoke_tests", 3))

    def _device_suite_problems(self, _result: Any) -> list[str]:
        return agent_guardrails.st1_device_suite(self.ws, self.profile) if "ST1" in self.guard_rules else []

    # ---------- device ----------

    @property
    def device_enabled(self) -> bool:
        return bool(self.profile.device and self.emulator and (self.cfg.get("device") or {}).get("enabled"))

    @property
    def app(self):
        return self.profile.components[self.profile.device.app_component]

    def app_built(self) -> bool:
        items = {w.id: w for w in self.s.backlog.work_items}
        return any(p.status == "done" and wid in items and items[wid].component == self.profile.device.app_component
                   for wid, p in self.s.build.items.items())

    @property
    def device_api_base(self) -> str:
        return f"http://{self.profile.device.host_alias}:{self.staging.port}{self.profile.release.api_prefix}"

    def device_env(self) -> dict[str, str]:
        dev = self.profile.device
        return {k: v.format(host=dev.host_alias, port=self.staging.port) for k, v in dev.asset_env.items()}

    def _device_round(self) -> list[tuple[str, str]]:
        """Build, install and launch the app on the emulator against the running staging; run the
        on-device journey tests. Returns problems for the app component."""
        dev, app, r = self.profile.device, self.app, self.r
        if not self.app_built():
            r.device_note = "no app work items are built yet"
            return []
        reason = self.emulator.tc.not_ready_reason()
        if reason:
            r.device_note = reason
            return []
        try:
            self.emulator.start(window=not (self.cfg.get("device") or {}).get("headless", True))
        except DeviceError as e:
            r.device_note = f"emulator did not start: {str(e)[:500]}"
            return []
        fmt = {"api_base": self.device_api_base, "serial": self.emulator.serial}
        build = self.emulator.run(dev.build_command.format(**fmt), app.workdir, timeout_s=dev.build_timeout_s)
        if not build.ok:
            r.device_passed, r.device_output = False, build.output[-6000:]
            return [(dev.app_component, f"Building the app for the device failed:\n{build.output[-3000:]}")]
        installed = self.emulator.install(dev.apk_path, app.workdir, dev.app_id)
        if not installed.ok:
            r.device_passed, r.device_output = False, installed.output[-3000:]
            return [(dev.app_component, f"Installing the app on the emulator failed:\n{installed.output[-2000:]}")]
        self.emulator.launch(dev.app_id)
        time.sleep(8)  # first frame and first API calls
        shot = self.emulator.screenshot(f"reports/device/round{r.rounds}/launch.png")
        if shot:
            r.device_screenshots.append(shot)
        if r.device_suite is None or not self.ws.resolve(f"{app.workdir}/{dev.test_dir}").exists():
            r.device_note = "no on-device test suite yet; only launched the app"
            r.device_passed = True
            return []
        test = self.emulator.run(dev.test_command.format(**fmt), app.workdir, timeout_s=dev.build_timeout_s)
        r.device_passed, r.device_output = test.ok, test.output[-6000:]
        after = self.emulator.screenshot(f"reports/device/round{r.rounds}/after_tests.png")
        if after:
            r.device_screenshots.append(after)
        if not test.ok:
            return [(dev.app_component, f"On-device journey tests failed against staging "
                                        f"({self.device_api_base}):\n{test.output[-3000:]}")]
        return []

    def _write_device_suite(self) -> bool:
        dev, app = self.profile.device, self.app
        result = self._guarded("smoke_tester", "write_device_tests", {
            "app_dir": app.workdir, "test_dir": dev.test_dir, "device_api_base": self.device_api_base,
            "test_command": dev.test_command.format(api_base=self.device_api_base, serial=self.emulator.serial),
            "host_alias": dev.host_alias,
        }, WorkItemResult, app.workdir, app.runtime, self._device_suite_problems, "The on-device test suite")
        if result is None or result.blocked:
            self.stop(f"Smoke tester could not write the device tests: {result.blocked_reason if result else 'agent failed'}")
            return False
        self.r.device_suite = result
        self.ws.commit("Release: on-device journey tests (smoke_tester)")
        self.checkpoint("Release: device test suite")
        return True

    # ---------- verification ----------

    def verify(self) -> None:
        try:
            self._verify()
        finally:
            if self.device_enabled:
                self.emulator.stop()

    def _verify(self) -> None:
        if self.r.verified and self.device_enabled and self.app_built() and self.r.device_passed is None \
                and not self.r.device_note:
            # Device checks were enabled after this release was verified: verify it again.
            self.s.reopen_release("On-device checks enabled since the last verification")
            self.checkpoint("Release: reopened for on-device checks")
        if self.r.verified:
            return
        if self.r.deployment is None:
            result = self._guarded(self.profile.components.get("infra", self.api).agent, "deploy_staging", {},
                                   WorkItemResult, ".", "api", self._deployment_problems, "The staging deployment")
            if result is None or result.blocked:
                self.stop(f"Deployment engineer could not prepare staging: {result.blocked_reason if result else 'agent failed'}")
                return
            self.r.deployment = result
            self.ws.commit("Release: staging deployment files (deployment_engineer)")
            self.checkpoint("Release: deployment files")
        if self.r.smoke_suite is None and self.profile.release.smoke_command:
            result = self._guarded("smoke_tester", "write_smoke_tests", {}, WorkItemResult, self.api.workdir, "api",
                                   self._smoke_problems, "The smoke test suite")
            if result is None or result.blocked:
                self.stop(f"Smoke tester could not write the smoke suite: {result.blocked_reason if result else 'agent failed'}")
                return
            self.r.smoke_suite = result
            self.ws.commit("Release: smoke test suite (smoke_tester)")
            self.checkpoint("Release: smoke suite")
        if self.device_enabled and self.app_built() and self.r.device_suite is None:
            if not self._write_device_suite():
                return

        max_rounds = self.cfg.get("fix_rounds", 2) + 1
        for session_round in range(1, max_rounds + 1):
            if not self.can_continue():
                return
            self.r.rounds += 1
            self.r.reset_verification()
            problems = self._verify_round(first_in_session=session_round == 1)
            self.ws.write_text(f"reports/release_round{self.r.rounds}.md", self.verification_markdown(problems))
            outcome = "staging did not start" if problems is None else ("passed" if not problems else "failed")
            self.ws.commit(f"Release verification round {self.r.rounds}: {outcome}")
            if problems is None:  # staging could not start; reason already recorded
                return
            if not problems:
                self.r.verified = True
                self.checkpoint("Release: staging verified")
                return
            if session_round == max_rounds:
                self.stop(f"Release verification still failing after {max_rounds} round(s); "
                          f"see reports/release_round{self.r.rounds}.md")
                return
            for component in dict.fromkeys(c for c, _ in problems):
                texts = [t for c, t in problems if c == component]
                self.fix("Staging verification found these problems. Fix them:\n" + "\n".join(texts), component)

    def _verify_round(self, first_in_session: bool = True) -> list[tuple[str, str]] | None:
        """One staging round. Returns (component, problem) pairs, or None if staging could not start."""
        api_c = self.profile.release.api_component
        if self.device_enabled:
            self.staging.extra_env = self.device_env()
        try:
            self.staging.start()
        except StagingError as e:
            logs = str(e)
            self.checkpoint("Release: staging failed to start")
            # A start failure may be a code/config problem the developer can fix; hand it over once.
            if first_in_session and "SDLC_STAGING_DATABASE_URL" not in logs and "Docker is not usable" not in logs:
                return [(api_c, f"Staging failed to start:\n{logs[-3000:]}")]
            self.stop(f"Staging could not start: {logs[:600]}")
            return None
        try:
            rel = self.profile.release
            if rel.openapi_json_path:
                status, body = http_get(self.staging.base_url + rel.openapi_json_path)
                self.r.contract_issues = (
                    contract_diff(self.ws.read_text("docs/openapi.yaml"), body, rel.api_prefix,
                                  ignore_paths=[rel.health_path, rel.openapi_json_path])
                    if status == 200 else [f"GET {rel.openapi_json_path} returned {status or 'no response'}"]
                )
                self.r.contract_issues = self._built_scope(self.r.contract_issues)
            inputs = {
                "base_url": self.api_base_url,
                "contract_issues": "\n".join(self.r.contract_issues) or "(none)",
                "staging_logs": self.staging.logs(3000),
            }
            item_ids = [w.id for w in self.s.backlog.work_items]
            report = self._job("integration_pass", "integration_review", inputs, QAReport, ".")
            errors = agent_guardrails.report_errors(report, item_ids, self.guard_rules, ("RELEASE",)) if report else []
            if errors:  # one retry with the reasons, then derive the verdict from the bugs
                report = self._job("integration_pass", "integration_review", inputs, QAReport, ".", feedback="\n".join(errors))
                if report and agent_guardrails.report_errors(report, item_ids, self.guard_rules, ("RELEASE",)):
                    report.passed = not report.blocking_bugs()
            self.r.integration = report
            if self.profile.release.smoke_command:
                res = self.sandbox.run_trusted(self.api.runtime, self.api.workdir, rel.smoke_command,
                                               env={"SMOKE_BASE_URL": self.api_base_url}, host_network=True)
                self.r.smoke_passed, self.r.smoke_output = res.ok, res.output[-6000:]
            device_problems = self._device_round() if self.device_enabled else []
        finally:
            self.staging.stop()
        problems: list[tuple[str, str]] = []
        if self.r.integration is None:
            problems.append((api_c, "The integration pass agent failed to produce a report"))
        else:
            problems += [(api_c, f"[{b.severity}] {b.title}: {b.actual} (expected: {b.expected})")
                         for b in self.r.integration.blocking_bugs()]
        if self.r.smoke_passed is False:
            problems.append((api_c, f"Smoke tests failed against staging:\n{self.r.smoke_output[-3000:]}"))
        return problems + device_problems

    def _built_scope(self, issues: list[str]) -> list[str]:
        """Endpoints of unbuilt work are expected to be missing; only report extra endpoints and
        missing ones when everything was built."""
        if any(p.status != "done" for p in self.s.build.items.values()):
            return [i for i in issues if not i.startswith("Missing in the API")]
        return issues

    def fix(self, problems: str, component: str | None = None) -> None:
        """Send problems to the developer of the component they belong to (default: the API)."""
        component = component or self.profile.release.api_component
        comp = self.profile.components[component]
        inputs = {
            "item_id": "RELEASE", "item_title": "Release verification fixes", "component": component,
            "item_description": "Fix problems found while running the system on staging.",
            "milestone": "Release", "stories": "(see the problems)", "checks": "; ".join(comp.checks) or "(none)",
            "problems": problems, "done_items": self.built_summary(),
        }
        code_rules = self._code_rules()
        result = self._guarded(comp.agent, "fix_work_item", inputs, WorkItemResult, comp.workdir, comp.runtime,
                               lambda _r: code_guardrails.check_changes(self.ws, comp, self.profile, code_rules)
                               if code_rules else [], f"The {component} fix")
        if result is not None:
            self.ws.commit(f"Release: fixes from staging verification ({comp.agent})")
        self.checkpoint("Release: fixes applied")

    def verification_markdown(self, problems: list[str] | None) -> str:
        r = self.r
        lines = [f"# Release verification, round {r.rounds}", "",
                 f"Staging: {self.staging.mode} at {self.staging.base_url}", "", "## Contract check"]
        lines += [f"- {i}" for i in r.contract_issues] or ["- matches the contract for the built scope"]
        lines += ["", "## Integration pass", r.integration.to_markdown() if r.integration else "(no report)",
                  "", "## Smoke tests", f"Result: {'passed' if r.smoke_passed else 'failed' if r.smoke_passed is False else 'not run'}",
                  "", "```", r.smoke_output[-3000:], "```", "", "## On-device (Android emulator)"]
        if r.device_passed is None:
            lines.append(f"Not run: {r.device_note or 'device checks disabled'}")
        else:
            lines.append(f"Result: {'passed' if r.device_passed else 'failed'}" + (f" ({r.device_note})" if r.device_note else ""))
            lines += [f"![{p.rsplit('/', 1)[-1]}](../{p.removeprefix('reports/')})" for p in r.device_screenshots]
            if r.device_output:
                lines += ["", "```", r.device_output[-3000:], "```"]
        lines += ["", "## Problems"]
        if problems is None:
            lines.append(f"- Staging could not start: {self.s.stop_reason[:1500]}")
        else:
            lines += [f"- [{c}] {p}" for c, p in problems] or ["- none"]
        return "\n".join(lines)

    def gate_summary(self) -> str:
        r = self.r
        return (f"Staging verified in round {r.rounds}: contract ok, integration "
                f"{'passed' if r.integration and r.integration.passed else 'n/a'}, smoke "
                f"{'passed' if r.smoke_passed else 'n/a'}, on device "
                f"{'passed' if r.device_passed else ('not run: ' + r.device_note if r.device_passed is None else 'failed')}"
                f"{' (screenshots: ' + ', '.join(r.device_screenshots) + ')' if r.device_screenshots else ''}. Built: "
                f"{sum(p.status == 'done' for p in self.s.build.items.values())} work items; not built: "
                f"{sum(p.status != 'done' for p in self.s.build.items.values())}.")

    # ---------- production ----------

    def production(self) -> None:
        if self.r.production in ("packaged", "deployed"):
            return
        notes = []
        for cmd in self.profile.release.package_commands:
            res = self.sandbox.run_trusted(self.api.runtime, self.api.workdir, cmd)
            if not res.ok:
                self.r.production, self.r.production_notes = "failed", f"`{cmd}` failed:\n{res.output[-3000:]}"
                self.stop(f"Packaging failed: `{cmd}`")
                return
            notes.append(f"ran `{cmd}`")
        tag = "release-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        self.ws.write_text("reports/release_notes.md", self.release_notes(tag))
        self.ws.commit(f"Release notes for {tag}")
        self.ws.tag(tag)
        self.r.production, self.r.production_notes = "packaged", f"Tagged {tag}. " + "; ".join(notes)

        command = (self.cfg.get("production_command") or "").strip()
        if command:
            proc = subprocess.run(shlex.split(command), cwd=self.ws.root, capture_output=True, text=True,
                                  timeout=self.cfg.get("production_timeout_s", 1800), env=dict(os.environ))
            output = (proc.stdout + proc.stderr)[-4000:]
            self.ws.write_text("reports/production_deploy.log", output)
            if proc.returncode != 0:
                self.r.production = "failed"
                self.r.production_notes += f"\nProduction command failed (exit {proc.returncode})."
                self.stop(f"Production deployment failed; see reports/production_deploy.log")
                return
            self.r.production = "deployed"
            self.r.production_notes += "\nProduction command succeeded."
        self.checkpoint(f"Release: {self.r.production}")

    def release_notes(self, tag: str) -> str:
        r = self.r
        return "\n".join([
            f"# Release {tag}", "", f"Product: {self.s.prd.title}", "",
            "## Included", self.built_summary(), "",
            "## Not included", self.not_built_summary(), "",
            "## Verification", f"Staging rounds: {r.rounds}. Smoke: {'passed' if r.smoke_passed else 'n/a'}.",
            f"Integration: {r.integration.summary if r.integration else 'n/a'}", "",
            "## Deployment", r.deployment.summary if r.deployment else "", "",
        ])
