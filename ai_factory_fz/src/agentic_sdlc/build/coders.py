"""Agents that work on code in the run workspace.

Two implementations behind one interface, picked per agent from its configured model:

- ClaudeCodeWorker: the agent's model is claude-code/... (CLAUDE_CODE_ENABLE=true).
  The job is handed to headless Claude Code with its own file tools, confined to the
  component directory, plus only the allow-listed build/test commands (local sandbox mode).
- CrewAIWorker: any other model. A CrewAI agent with the fs_* and sandbox_exec tools.

Both return the job's structured output model and a usage record.
"""

import json
import logging
import os
import shlex
import subprocess
import sys
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel

from agentic_sdlc.crews.base import (PhaseError, TaskResult, TaskRunner, UsageLimitError, feedback_text,
                                     fill_template, is_usage_limit)
from agentic_sdlc.llms.backend import CLAUDE_CODE_PREFIX
from agentic_sdlc.registry.agents import AgentRegistry
from agentic_sdlc.state import UsageRecord
from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRunner
from agentic_sdlc.workspace import Workspace

T = TypeVar("T", bound=BaseModel)
log = logging.getLogger(__name__)


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


class ClaudeCodeWorker:
    def __init__(self, agents: AgentRegistry, tasks: dict[str, dict[str, Any]], workspace: Workspace,
                 sandbox: SandboxRunner, timeout_s: int = 3600, cli_path: str = "claude"):
        self.profile_name = agents.profile.name
        self.agents = agents
        self.tasks = tasks
        self.workspace = workspace
        self.sandbox = sandbox
        self.timeout_s = timeout_s
        self.cli_path = cli_path

    def _runtimes(self, job: Job) -> list[str]:
        """Runtimes whose allow-listed commands the agent may run. Local mode: on this machine.
        Docker mode: through wrapper commands that run them in the runtime's container."""
        rts = [r for r in [job.runtime, *job.extra_runtimes] if r]
        return [r for r in rts if self.sandbox.unavailable_reason(r) is None]

    def _install_wrappers(self, runtimes: list[str]) -> str | None:
        """Docker mode: write .sdlc/bin/<tool> wrappers for the allow-listed tools and return the
        directory to put first on PATH. The wrappers enforce the same allow-list."""
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

    def tooling_text(self, job: Job) -> str:
        cmds = allowed_commands(self.sandbox, self._runtimes(job))
        cwd = self.workspace.resolve(job.workdir)
        text = (
            f"Your working directory is {cwd}. Use your Read, Glob, Grep, Edit and Write tools. "
            f"Project documents are read-only in {self.workspace.root / 'docs'}."
        )
        if cmds:
            text += (" Run these commands with Bash, from your working directory, one command per Bash call "
                     "(no cd, &&, pipes or redirects): " + "; ".join(cmds) + ".")
        else:
            text += " You cannot run commands; the build and tests are run for you after you finish."
        return text

    def build_command(self, job: Job, model: str, system: str) -> list[str]:
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

    def run(self, job: Job[T]) -> TaskResult[T]:
        d = self.agents.definition(job.agent_key)
        system = f"You are the {d['role']}. {d['goal'].strip()}\n\n{d['backstory'].strip()}"
        tdef = self.tasks[job.task_key]
        prompt = fill_template(tdef["description"], {**job.inputs, "tooling": self.tooling_text(job)}) \
            + feedback_text(job.feedback)
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        env.update(self.sandbox.config.env)
        wrappers = self._install_wrappers(self._runtimes(job))
        if wrappers:
            env["PATH"] = f"{wrappers}{os.pathsep}{env.get('PATH', '')}"
        cwd = self.workspace.resolve(job.workdir)
        last_error = ""
        for candidate in self.agents.models.spec_for(job.agent_key).candidates():
            model = candidate.removeprefix(CLAUDE_CODE_PREFIX)
            try:
                proc = subprocess.run(self.build_command(job, model, system), input=prompt, capture_output=True,
                                      text=True, timeout=self.timeout_s, env=env, cwd=cwd)
            except subprocess.TimeoutExpired:
                last_error = f"{model}: timed out after {self.timeout_s}s"
                log.warning("Claude Code job %s (%s) %s", job.task_key, job.agent_key, last_error)
                continue
            try:
                data = json.loads(proc.stdout)
            except json.JSONDecodeError:
                data = None
            if not isinstance(data, dict) or data.get("is_error") or data.get("structured_output") is None:
                if isinstance(data, dict):
                    detail = f"{data.get('subtype')}: {(data.get('result') or '')[:400]}"
                    if data.get("structured_output") is None and not data.get("is_error"):
                        detail = f"finished without the required structured report ({detail})"
                else:
                    detail = f"exit {proc.returncode}: {(proc.stderr or proc.stdout)[-400:]}"
                last_error = f"{model}: {detail}"
                if is_usage_limit(detail):
                    # Same account for every candidate model: stop instead of trying the next one.
                    raise UsageLimitError(f"Usage limit reached: {(data or {}).get('result') or detail}")
                log.warning("Claude Code job %s (%s) failed on %s", job.task_key, job.agent_key, last_error)
                self._save_failure(job, model, proc)
                continue
            return TaskResult(
                artifact=job.output_model.model_validate(data["structured_output"]),
                usage=self._usage(job, candidate, data),
            )
        raise PhaseError(f"Claude Code job '{job.task_key}' for '{job.agent_key}' failed: {last_error}")

    def _save_failure(self, job: Job, model: str, proc: subprocess.CompletedProcess) -> None:
        """Keep the raw result of a failed job for diagnosis (reports/agent_failures/)."""
        name = f"reports/agent_failures/{datetime.now():%H%M%S}-{job.task_key}-{model}.json"
        try:
            self.workspace.write_text(name, json.dumps({"exit_code": proc.returncode, "stdout": proc.stdout[-20000:],
                                                        "stderr": proc.stderr[-5000:]}, indent=2))
        except OSError:
            pass

    @staticmethod
    def _usage(job: Job, model: str, data: dict[str, Any]) -> UsageRecord:
        per_model = (data.get("modelUsage") or {}).values()
        inp = sum(m.get("inputTokens", 0) for m in per_model)
        cache_read = sum(m.get("cacheReadInputTokens", 0) for m in per_model)
        cache_write = sum(m.get("cacheCreationInputTokens", 0) for m in per_model)
        out = sum(m.get("outputTokens", 0) for m in per_model)
        prompt = inp + cache_read + cache_write
        return UsageRecord(phase=job.phase, agent=job.agent_key, model=model, prompt_tokens=prompt,
                           cached_prompt_tokens=cache_read, completion_tokens=out, total_tokens=prompt + out)


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
    return CrewAIWorker(TaskRunner(agents, tasks), sandbox)
