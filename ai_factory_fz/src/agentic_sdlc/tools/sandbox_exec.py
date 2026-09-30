"""Run build/test commands for a run workspace, in Docker or directly on the host.

Modes (SDLC_SANDBOX env var, else pipeline.yaml build.sandbox):
  docker  each command runs in a throwaway container of the runtime's image, with only the
          run workspace mounted. Recommended.
  local   commands run on this machine, inside the run workspace. Use only when Docker is not
          available. Agent-written code (e.g. `npm test`) then runs with your user's rights.

Agent commands must match the profile's allow-list; scaffolding uses run_trusted().
"""

import logging
import os
import shlex
import sys
import uuid
import shutil
import subprocess
from enum import Enum

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from agentic_sdlc.registry.profiles import SandboxConfig
from agentic_sdlc.workspace import Workspace

log = logging.getLogger(__name__)
CONTAINER_ROOT = "/workspace"
_FORBIDDEN_CHARS = set(";&|<>`$\n\r")


class SandboxMode(str, Enum):
    DOCKER = "docker"
    LOCAL = "local"


class SandboxRejected(ValueError):
    """The command is not allowed to run."""


class SandboxResult(BaseModel):
    exit_code: int
    output: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    def summary(self) -> str:
        return f"exit_code={self.exit_code}\n{self.output}"


def sandbox_mode(configured: str = "docker") -> SandboxMode:
    return SandboxMode(os.environ.get("SDLC_SANDBOX", configured))


class SandboxRunner:
    def __init__(
        self,
        workspace: Workspace,
        config: SandboxConfig,
        mode: SandboxMode = SandboxMode.DOCKER,
        network: bool = True,
        timeout_s: int = 900,
        max_output_chars: int = 12_000,
    ):
        self.workspace = workspace
        self.config = config
        self.mode = mode
        self.network = network
        self.timeout_s = timeout_s
        self.max_output_chars = max_output_chars
        self._image_errors: dict[str, str] = {}   # runtime -> why its image is not available

    # ---------- setup ----------

    def prepare(self, runtimes: list[str], pull_timeout_s: int = 1800) -> dict[str, str]:
        """Docker mode: pull the images these runtimes need, if they are not present yet.
        Returns {runtime: error} for images that could not be pulled (those runtimes then
        report as unavailable). Local mode: nothing to do."""
        if self.mode is not SandboxMode.DOCKER or self._docker_problem():
            return {}
        for runtime in dict.fromkeys(runtimes):
            rt = self.config.runtimes.get(runtime)
            if rt is None or runtime in self._image_errors:
                continue
            if subprocess.run(["docker", "image", "inspect", rt.image], capture_output=True).returncode == 0:
                continue
            log.warning("Pulling %s for the %s runtime (first use; this can take a few minutes)", rt.image, runtime)
            print(f"Pulling {rt.image} for the {runtime} runtime (first use; this can take a few minutes)...", flush=True)
            try:
                r = subprocess.run(["docker", "pull", rt.image], capture_output=True, text=True, timeout=pull_timeout_s)
                if r.returncode != 0:
                    self._image_errors[runtime] = f"could not pull {rt.image}: {(r.stderr or r.stdout).strip()[-300:]}"
            except subprocess.TimeoutExpired:
                self._image_errors[runtime] = f"pulling {rt.image} timed out after {pull_timeout_s}s"
        return dict(self._image_errors)

    # ---------- availability ----------

    @staticmethod
    def _docker_problem() -> str | None:
        probe = subprocess.run(["docker", "info"], capture_output=True, text=True) if shutil.which("docker") else None
        if probe is None or probe.returncode != 0:
            return "Docker is not usable by this user (install it, or add the user to the 'docker' group)"
        return None

    def unavailable_reason(self, runtime: str) -> str | None:
        """None if commands for this runtime can run, else a human-readable reason."""
        rt = self.config.runtimes.get(runtime)
        if rt is None:
            return f"unknown runtime '{runtime}'"
        if self.mode is SandboxMode.DOCKER:
            return self._docker_problem() or self._image_errors.get(runtime)
        if not shutil.which(rt.local_binary):
            return f"'{rt.local_binary}' is not installed on this machine (needed for the {runtime} runtime in local mode)"
        return None

    # ---------- command building ----------

    def check_allowed(self, runtime: str, command: str) -> list[str]:
        if runtime not in self.config.runtimes:
            raise SandboxRejected(f"Unknown runtime '{runtime}'. Use one of: {sorted(self.config.runtimes)}")
        if _FORBIDDEN_CHARS.intersection(command):
            raise SandboxRejected("Shell operators (; & | < > ` $ newlines) are not allowed; run one command at a time")
        argv = shlex.split(command)
        allowed = [shlex.split(a) for a in self.config.allowed_commands.get(runtime, [])]
        if not any(argv[: len(prefix)] == prefix for prefix in allowed):
            raise SandboxRejected(
                f"Command not allowed for runtime '{runtime}'. Allowed prefixes: "
                + ", ".join(" ".join(p) for p in allowed)
            )
        return argv

    def build_command(self, runtime: str, workdir: str, argv: list[str], env: dict[str, str] | None = None,
                      host_network: bool = False) -> tuple[list[str], str]:
        """Return (argv to execute, host cwd). Raises PathEscapeError for a bad workdir."""
        host_dir = self.workspace.resolve(workdir)
        rt = self.config.runtimes[runtime]
        if self.mode is SandboxMode.LOCAL:
            return [*shlex.split(rt.local_prefix), *argv], str(host_dir)
        rel = host_dir.relative_to(self.workspace.root).as_posix()
        container_dir = CONTAINER_ROOT if rel == "." else f"{CONTAINER_ROOT}/{rel}"
        env_args = [a for k, v in {**self.config.env, **rt.env, **(env or {})}.items() for a in ("-e", f"{k}={v}")]
        network = "host" if host_network else ("bridge" if self.network else "none")
        owner = f"{os.getuid()}:{os.getgid()}"
        if rt.run_as_root:
            # Root inside the container, then hand root-created files back to the host user so the
            # file tools and later non-root commands can still edit them.
            user_args: list[str] = []
            argv = ["sh", "-c", f"{shlex.join(argv)}; code=$?; "
                    f"find {CONTAINER_ROOT} -xdev -user 0 -exec chown {owner} {{}} + 2>/dev/null; exit $code"]
        else:
            # Run as the host user so generated files stay editable by the file tools.
            user_args = ["--user", owner, "-e", "HOME=/tmp"]
        return [
            "docker", "run", "--rm",
            "--network", network,
            *user_args,
            *env_args,
            "-v", f"{self.workspace.root}:{CONTAINER_ROOT}",
            "-w", container_dir,
            rt.image, *argv,
        ], str(self.workspace.root)

    # ---------- execution ----------

    def run(self, runtime: str, workdir: str, command: str) -> SandboxResult:
        """Run an agent-requested command; it must be on the allow-list."""
        return self._execute(runtime, workdir, self.check_allowed(runtime, command))

    def run_trusted(self, runtime: str, workdir: str, command: str, env: dict[str, str] | None = None,
                    host_network: bool = False, timeout_s: int | None = None) -> SandboxResult:
        """Run a command from our own config (scaffolding, checks, staging) without the allow-list.
        `env` is added last; `host_network` lets a container reach services on localhost."""
        if runtime not in self.config.runtimes:
            raise SandboxRejected(f"Unknown runtime '{runtime}'")
        return self._execute(runtime, workdir, shlex.split(command), env, host_network, timeout_s)

    def _execute(self, runtime: str, workdir: str, argv: list[str], extra_env: dict[str, str] | None = None,
                 host_network: bool = False, timeout_s: int | None = None) -> SandboxResult:
        cmd, cwd = self.build_command(runtime, workdir, argv, extra_env, host_network)
        name = None
        if cmd[:3] == ["docker", "run", "--rm"]:
            # Named, so a timed-out container can be killed instead of running on unattended.
            name = f"sdlc-{uuid.uuid4().hex[:12]}"
            cmd = [*cmd[:3], "--name", name, *cmd[3:]]
        env = {**os.environ, **self.config.env, **(extra_env or {})} if self.mode is SandboxMode.LOCAL else None
        limit = timeout_s or self.timeout_s
        # On Windows, CreateProcess cannot launch .bat/.cmd (flutter.bat, npm.cmd) without a shell.
        if self.mode is SandboxMode.LOCAL and sys.platform == "win32" and cmd:
            resolved = shutil.which(cmd[0])
            if resolved:
                cmd = [resolved, *cmd[1:]]
            cmd = ["cmd.exe", "/c", *cmd]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=limit, cwd=cwd, env=env)
        except subprocess.TimeoutExpired:
            if name:
                subprocess.run(["docker", "kill", name], capture_output=True)
            return SandboxResult(exit_code=124, output=f"Timed out after {limit}s")
        except FileNotFoundError as e:
            return SandboxResult(exit_code=127, output=str(e))
        output = (proc.stdout or "") + (proc.stderr or "")
        if len(output) > self.max_output_chars:
            output = "... [earlier output truncated]\n" + output[-self.max_output_chars :]
        return SandboxResult(exit_code=proc.returncode, output=output)


class SandboxArgs(BaseModel):
    runtime: str = Field(description="Which toolchain to use, e.g. 'flutter' or 'node'")
    workdir: str = Field(description="Directory relative to the workspace, e.g. 'server' or 'app'")
    command: str = Field(description="One allow-listed command, e.g. 'npm test' or 'flutter analyze'")


class SandboxExecTool(BaseTool):
    name: str = "sandbox_exec"
    description: str = (
        "Run one allow-listed build or test command for the project and "
        "return its exit code and output."
    )
    args_schema: type[BaseModel] = SandboxArgs
    _runner: SandboxRunner = PrivateAttr()

    def __init__(self, runner: SandboxRunner, **kwargs):
        super().__init__(**kwargs)
        self._runner = runner

    def _run(self, runtime: str, workdir: str, command: str) -> str:
        try:
            return self._runner.run(runtime, workdir, command).summary()
        except (SandboxRejected, ValueError) as e:
            return f"REJECTED: {e}"
