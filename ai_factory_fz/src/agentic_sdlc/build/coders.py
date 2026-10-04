"""Agents that work on code in the run workspace.

Three implementations behind one interface:

- ClaudeCodeWorker: claude-code/... models (CLAUDE_CODE_ENABLE=true).
- CursorCodeWorker: LLM_PROVIDER=cursor_cli — headless Cursor `agent` with shell and file tools.
- CrewAIWorker: Anthropic API / proxy — CrewAI agent with fs_* and sandbox_exec tools.
"""

import json
import logging
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from agentic_sdlc.crews.base import (PhaseError, TaskResult, TaskRunner, UsageLimitError, feedback_text,
                                     fill_template, is_usage_limit)
from agentic_sdlc.env_toolchain import enrich_path
from agentic_sdlc.llms.backend import CLAUDE_CODE_PREFIX, Provider, selected_provider
from agentic_sdlc.llms.cursor_agent import _resolve_agent_cli
from agentic_sdlc.registry.agents import AgentRegistry
from agentic_sdlc.state import UsageRecord
from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRunner
from agentic_sdlc.artifacts.reports import WorkItemResult
from agentic_sdlc.build.transcript_log import append_transcript
from agentic_sdlc.workspace import Workspace

T = TypeVar("T", bound=BaseModel)
log = logging.getLogger(__name__)

_CODING_AGENT_KEYS = frozenset({
    "backend_developer", "frontend_developer", "qa_engineer", "deployment_engineer",
})


@dataclass
class Job(Generic[T]):
    phase: str
    agent_key: str
    task_key: str                 # prompt template in config/tasks.yaml
    inputs: dict[str, Any]
    output_model: type[T]
    workdir: str                  # component directory, relative to the workspace
    runtime: str | None           # toolchain the agent may run commands with
    extra_runtimes: list[str] = field(default_factory=list)
    feedback: str = ""            # guardrail problems from a rejected previous attempt


class Worker(Protocol):
    def run(self, job: Job[T]) -> TaskResult[T]: ...


def allowed_commands(sandbox: SandboxRunner, runtimes: list[str]) -> list[str]:
    return [c for rt in runtimes for c in sandbox.config.allowed_commands.get(rt, [])]


def _extract_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty output")
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in output")
    return json.loads(text[start : end + 1])


def _artifact_from_cli_json(data: dict[str, Any], model: type[T]) -> T:
    structured = data.get("structured_output")
    if structured is not None:
        return model.model_validate(structured)
    for key in ("result", "text", "output", "message"):
        raw = data.get(key)
        if isinstance(raw, str) and raw.strip():
            try:
                return model.model_validate(_extract_json_object(raw))
            except (ValidationError, ValueError, json.JSONDecodeError):
                continue
    # Cursor CLI often finishes with subtype=success and a narrative result (no JSON envelope).
    if model is WorkItemResult and not data.get("is_error"):
        raw = data.get("result") or data.get("text") or data.get("output") or ""
        if isinstance(raw, str) and raw.strip():
            return WorkItemResult(
                summary=raw.strip()[:4000],
                checks_passed=False,
            )
    raise ValueError("CLI JSON did not contain structured_output or parseable result JSON")


class _CodeShellWorker:
    """Shared run loop for headless coding CLIs with file tools and allow-listed shell commands."""

    def __init__(self, agents: AgentRegistry, tasks: dict[str, dict[str, Any]], workspace: Workspace,
                 sandbox: SandboxRunner, timeout_s: int = 3600):
        self.profile_name = agents.profile.name
        self.agents = agents
        self.tasks = tasks
        self.workspace = workspace
        self.sandbox = sandbox
        self.timeout_s = timeout_s

    def _runtimes(self, job: Job) -> list[str]:
        rts = [r for r in [job.runtime, *job.extra_runtimes] if r]
        return [r for r in rts if self.sandbox.unavailable_reason(r) is None]

    def _install_wrappers(self, runtimes: list[str]) -> str | None:
        if self.sandbox.mode is not SandboxMode.DOCKER or not runtimes:
            return None
        bin_dir = self.workspace.root / ".sdlc" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        for rt in runtimes:
            for tool in {shlex.split(c)[0] for c in self.sandbox.config.allowed_commands.get(rt, [])}:
                script = bin_dir / tool
                script.write_text(
                    "#!/bin/sh\n"
                    f"exec {shlex.quote(sys.executable)} -m agentic_sdlc.tools.sandbox_cli "
                    f"--workspace {shlex.quote(str(self.workspace.root))} --profile {shlex.quote(self.profile_name)} "
                    f"--runtime {shlex.quote(rt)} -- {shlex.quote(tool)} \"$@\"\n",
                    encoding="utf-8",
                )
                script.chmod(0o755)
        return str(bin_dir)

    def tooling_text(self, job: Job, shell_hint: str) -> str:
        cmds = allowed_commands(self.sandbox, self._runtimes(job))
        cwd = self.workspace.resolve(job.workdir)
        text = (
            f"Your working directory is {cwd}. Use your Read, Glob, Grep, Edit and Write tools. "
            f"Project documents are read-only in {self.workspace.root / 'docs'}."
        )
        if cmds:
            text += (
                f" Run these commands {shell_hint}, from your working directory, one command at a time "
                f"(no cd, &&, pipes or redirects): " + "; ".join(cmds) + "."
            )
        else:
            text += " You cannot run commands; the build and tests are run for you after you finish."
        return text

    def models_for(self, job: Job) -> list[str]:
        raise NotImplementedError

    def build_command(self, job: Job, model: str, system: str, prompt: str) -> list[str]:
        raise NotImplementedError

    def stdin_prompt(self, system: str, prompt: str) -> str:
        return prompt

    def _save_failure(
        self,
        job: Job,
        model: str,
        proc: subprocess.CompletedProcess,
        *,
        started_at: str,
        ended_at: str,
        duration_ms: int,
        prompt: str,
        data: dict[str, Any] | None,
    ) -> None:
        name = f"reports/agent_failures/{datetime.now():%H%M%S}-{job.task_key}-{model}.json"
        try:
            self.workspace.write_text(name, json.dumps({"exit_code": proc.returncode, "stdout": proc.stdout[-20000:],
                                                        "stderr": proc.stderr[-5000:]}, indent=2))
        except OSError:
            pass
        try:
            append_transcript(
                self.workspace.root,
                started_at=started_at,
                ended_at=ended_at,
                duration_ms=duration_ms,
                phase=job.phase,
                agent_key=job.agent_key,
                task_key=job.task_key,
                model=model,
                workdir=job.workdir,
                success=False,
                exit_code=proc.returncode,
                prompt=prompt,
                data=data,
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
            )
        except OSError:
            pass

    @staticmethod
    def _usage(
        job: Job,
        model: str,
        data: dict[str, Any],
        *,
        started_at: str,
        ended_at: str,
        duration_ms: int,
    ) -> UsageRecord:
        per_model = (data.get("modelUsage") or {}).values()
        inp = sum(m.get("inputTokens", 0) for m in per_model)
        cache_read = sum(m.get("cacheReadInputTokens", 0) for m in per_model)
        cache_write = sum(m.get("cacheCreationInputTokens", 0) for m in per_model)
        out = sum(m.get("outputTokens", 0) for m in per_model)
        prompt = inp + cache_read + cache_write
        return UsageRecord(
            phase=job.phase,
            agent=job.agent_key,
            model=model,
            prompt_tokens=prompt,
            cached_prompt_tokens=cache_read,
            completion_tokens=out,
            total_tokens=prompt + out,
            task_key=job.task_key,
            duration_ms=duration_ms,
            started_at=started_at,
            ended_at=ended_at,
        )

    def run(self, job: Job[T]) -> TaskResult[T]:
        d = self.agents.definition(job.agent_key)
        system = f"You are the {d['role']}. {d['goal'].strip()}\n\n{d['backstory'].strip()}"
        tdef = self.tasks[job.task_key]
        prompt = fill_template(tdef["description"], {**job.inputs, "tooling": self.tooling_text(job, self._shell_hint())}) \
            + feedback_text(job.feedback)
        prompt += (
            "\n\nWhen you finish, respond with valid JSON only (no markdown fences) matching this schema:\n"
            + json.dumps(job.output_model.model_json_schema())
        )
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        enrich_path(env)
        env.update(self.sandbox.config.env)
        wrappers = self._install_wrappers(self._runtimes(job))
        if wrappers:
            env["PATH"] = f"{wrappers}{os.pathsep}{env.get('PATH', '')}"
        cwd = self.workspace.resolve(job.workdir)
        last_error = ""
        for candidate in self.models_for(job):
            model = candidate.removeprefix(CLAUDE_CODE_PREFIX)
            started = datetime.now(timezone.utc)
            t0 = time.perf_counter()
            try:
                stdin = self.stdin_prompt(system, prompt)
                proc = subprocess.run(self.build_command(job, model, system, prompt), input=stdin, capture_output=True,
                                      text=True, timeout=self.timeout_s, env=env, cwd=cwd)
            except subprocess.TimeoutExpired:
                ended = datetime.now(timezone.utc)
                duration_ms = int((time.perf_counter() - t0) * 1000)
                last_error = f"{model}: timed out after {self.timeout_s}s"
                log.warning("Code-shell job %s (%s) %s", job.task_key, job.agent_key, last_error)
                try:
                    append_transcript(
                        self.workspace.root,
                        started_at=started.isoformat(),
                        ended_at=ended.isoformat(),
                        duration_ms=duration_ms,
                        phase=job.phase,
                        agent_key=job.agent_key,
                        task_key=job.task_key,
                        model=model,
                        workdir=job.workdir,
                        success=False,
                        exit_code=None,
                        prompt=self.stdin_prompt(system, prompt),
                        data=None,
                        stdout="",
                        stderr=last_error,
                    )
                except OSError:
                    pass
                continue
            try:
                data = json.loads(proc.stdout)
            except json.JSONDecodeError:
                data = None
            try:
                if not isinstance(data, dict) or data.get("is_error"):
                    raise ValueError("error or non-JSON stdout")
                artifact = _artifact_from_cli_json(data, job.output_model)
            except (ValueError, ValidationError, json.JSONDecodeError) as e:
                if isinstance(data, dict):
                    detail = f"{data.get('subtype')}: {(data.get('result') or '')[:400]}"
                    if not data.get("is_error"):
                        detail = f"finished without the required structured report ({detail}; {e})"
                else:
                    detail = f"exit {proc.returncode}: {(proc.stderr or proc.stdout)[-400:]}"
                last_error = f"{model}: {detail}"
                if is_usage_limit(detail):
                    raise UsageLimitError(f"Usage limit reached: {(data or {}).get('result') or detail}")
                log.warning("Code-shell job %s (%s) failed on %s", job.task_key, job.agent_key, last_error)
                ended = datetime.now(timezone.utc)
                duration_ms = int((time.perf_counter() - t0) * 1000)
                self._save_failure(
                    job,
                    model,
                    proc,
                    started_at=started.isoformat(),
                    ended_at=ended.isoformat(),
                    duration_ms=duration_ms,
                    prompt=self.stdin_prompt(system, prompt),
                    data=data if isinstance(data, dict) else None,
                )
                continue
            ended = datetime.now(timezone.utc)
            duration_ms = int((time.perf_counter() - t0) * 1000)
            try:
                append_transcript(
                    self.workspace.root,
                    started_at=started.isoformat(),
                    ended_at=ended.isoformat(),
                    duration_ms=duration_ms,
                    phase=job.phase,
                    agent_key=job.agent_key,
                    task_key=job.task_key,
                    model=model,
                    workdir=job.workdir,
                    success=True,
                    exit_code=proc.returncode,
                    prompt=self.stdin_prompt(system, prompt),
                    data=data,
                    stdout=proc.stdout or "",
                    stderr=proc.stderr or "",
                )
            except OSError:
                pass
            return TaskResult(
                artifact=artifact,
                usage=self._usage(
                    job,
                    candidate,
                    data,
                    started_at=started.isoformat(),
                    ended_at=ended.isoformat(),
                    duration_ms=duration_ms,
                ),
            )
        raise PhaseError(f"Code-shell job '{job.task_key}' for '{job.agent_key}' failed: {last_error}")

    def _shell_hint(self) -> str:
        return "with Bash"


class ClaudeCodeWorker(_CodeShellWorker):
    def __init__(self, agents: AgentRegistry, tasks: dict[str, dict[str, Any]], workspace: Workspace,
                 sandbox: SandboxRunner, timeout_s: int = 3600, cli_path: str = "claude"):
        super().__init__(agents, tasks, workspace, sandbox, timeout_s)
        self.cli_path = cli_path

    def models_for(self, job: Job) -> list[str]:
        return self.agents.models.spec_for(job.agent_key).candidates()

    def build_command(self, job: Job, model: str, system: str, prompt: str) -> list[str]:
        docs = str(self.workspace.root / "docs")
        allowed = ["Read", "Glob", "Grep", "Edit", "Write", *self.agents.web_rules(job.agent_key)]
        for c in allowed_commands(self.sandbox, self._runtimes(job)):
            allowed += [f"Bash({c})", f"Bash({c} *)"]
        return [
            self.cli_path, "-p",
            "--output-format", "json",
            "--model", model,
            "--permission-mode", "dontAsk",
            "--allowedTools", *allowed,
            "--disallowedTools", f"Edit(/{docs}/**)", f"Write(/{docs}/**)",
            "--add-dir", docs,
            "--append-system-prompt", system,
            "--json-schema", json.dumps(job.output_model.model_json_schema()),
            "--no-session-persistence",
            "--setting-sources", "",
            "--strict-mcp-config",
        ]


class CursorCodeWorker(_CodeShellWorker):
    """Headless Cursor agent for build tasks (shell + files; sandbox disabled for allow-listed commands)."""

    def models_for(self, job: Job) -> list[str]:
        per_agent = os.getenv(f"CURSOR_MODEL_{job.agent_key.upper()}", "").strip()
        model = per_agent or os.getenv("CURSOR_PROXY_MODEL", "auto")
        return [model]

    def _shell_hint(self) -> str:
        return "in the terminal/shell"

    def build_command(self, job: Job, model: str, system: str, prompt: str) -> list[str]:
        node_exe, index_js = _resolve_agent_cli()
        docs = str(self.workspace.root / "docs")
        cwd = self.workspace.resolve(job.workdir)
        cmd = [node_exe, index_js] if index_js else [node_exe]
        cmd += [
            "-p",
            "--trust",
            "--force",
            "--sandbox", "disabled",
            "--output-format", "json",
            "--model", model,
            "--workspace", str(cwd),
            "--add-dir", docs,
        ]
        return cmd

    def stdin_prompt(self, system: str, prompt: str) -> str:
        return f"{system.strip()}\n\n{prompt}"


class CrewAIWorker:
    def __init__(self, runner: TaskRunner, sandbox: SandboxRunner):
        self.runner = runner
        self.sandbox = sandbox

    def run(self, job: Job[T]) -> TaskResult[T]:
        runtimes = [r for r in [job.runtime, *job.extra_runtimes] if r and self.sandbox.unavailable_reason(r) is None]
        cmds = allowed_commands(self.sandbox, runtimes)
        tooling = (
            f"Work in the '{job.workdir}' directory of the workspace. Use fs_list, fs_read (with start_line and "
            "max_lines for large files) and fs_write (full file content). Project documents are in 'docs/' (read-only). "
        )
        tooling += (
            f"Run commands with sandbox_exec (runtime one of {runtimes}, workdir '{job.workdir}'). Allowed: " + "; ".join(cmds) + "."
            if cmds else "You cannot run commands; the build and tests are run for you after you finish."
        )
        return self.runner.run(job.phase, job.task_key, {**job.inputs, "tooling": tooling}, job.output_model,
                               agent_key=job.agent_key, feedback=job.feedback)


def make_worker(agent_key: str, agents: AgentRegistry, tasks: dict[str, dict[str, Any]], workspace: Workspace,
                sandbox: SandboxRunner, timeout_s: int = 3600) -> Worker:
    if agents.models.spec_for(agent_key).model.startswith(CLAUDE_CODE_PREFIX):
        return ClaudeCodeWorker(agents, tasks, workspace, sandbox, timeout_s)
    if selected_provider() is Provider.CURSOR_CLI and agent_key in _CODING_AGENT_KEYS:
        return CursorCodeWorker(agents, tasks, workspace, sandbox, timeout_s)
    return CrewAIWorker(TaskRunner(agents, tasks), sandbox)
