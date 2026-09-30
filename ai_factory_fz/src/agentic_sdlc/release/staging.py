"""Staging environment: start the built API, wait until healthy, stop it afterwards.

Two ways, chosen automatically:
  compose  Docker usable -> `docker compose up` with the compose file the Deployment engineer wrote.
  local    no Docker -> run the API as a local process against SDLC_STAGING_DATABASE_URL.
"""

import json
import os
import shlex
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRunner
from agentic_sdlc.workspace import Workspace


class StagingError(RuntimeError):
    pass


_PROGRESS = ("Downloading", "Extracting", "Pulling fs layer", "Waiting", "Verifying Checksum",
             "Download complete", "Pull complete", "Already exists")


def _without_progress(output: str) -> str:
    """Drop image download progress so the actual error is what remains at the end."""
    return "\n".join(line for line in output.splitlines() if not any(p in line for p in _PROGRESS))


def http_get(url: str, timeout: float = 5.0) -> tuple[int, str]:
    """GET a URL; returns (status, body). Status 0 means no connection."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError):
        return 0, ""


def read_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


class Staging:
    def __init__(self, workspace: Workspace, profile: Profile, sandbox: SandboxRunner, port: int = 3100,
                 startup_timeout_s: int = 90):
        self.ws = workspace
        self.rel = profile.release
        self.comp = profile.components[profile.release.api_component]
        self.sandbox = sandbox
        self.port = port
        self.startup_timeout_s = startup_timeout_s
        self.base_url = f"http://localhost:{port}"
        self._proc: subprocess.Popen | None = None
        self._log_file = None
        self.extra_env: dict[str, str] = {}   # e.g. device-reachable asset URLs, set before start()

    @property
    def mode(self) -> str:
        return "compose" if self.sandbox.mode is SandboxMode.DOCKER else "local"

    def unavailable_reason(self) -> str | None:
        if self.mode == "compose":
            return self.sandbox.unavailable_reason(self.comp.runtime)
        if not os.environ.get("SDLC_STAGING_DATABASE_URL"):
            return ("Local staging needs a PostgreSQL database: set SDLC_STAGING_DATABASE_URL in .env "
                    "(an empty database it may reset), or use Docker (build.sandbox: docker)")
        return self.sandbox.unavailable_reason(self.comp.runtime)

    def _env(self) -> dict[str, str]:
        env = read_env_file(self.ws.resolve(self.rel.env_file))
        env.update({"PORT": str(self.port), "NODE_ENV": env.get("NODE_ENV", "production")})
        if self.mode == "local":
            env["DATABASE_URL"] = os.environ["SDLC_STAGING_DATABASE_URL"]
        env.update(self.extra_env)
        return env

    def start(self) -> None:
        reason = self.unavailable_reason()
        if reason:
            raise StagingError(reason)
        (self._start_compose if self.mode == "compose" else self._start_local)()
        self._wait_healthy()

    def _compose(self, *args: str) -> subprocess.CompletedProcess:
        files = ["-f", self.rel.compose_file]
        if self.extra_env:
            # Overrides for the API service (environment beats env_file), kept out of the repo.
            override = self.ws.resolve(".sdlc/compose.override.yml")
            override.parent.mkdir(parents=True, exist_ok=True)
            lines = ["services:", f"  {self.rel.compose_api_service}:", "    environment:"]
            lines += [f"      {k}: {json.dumps(v)}" for k, v in self.extra_env.items()]
            override.write_text("\n".join(lines) + "\n", encoding="utf-8")
            files += ["-f", str(override)]
        cmd = ["docker", "compose", "--progress", "plain", *files, "--env-file", self.rel.env_file, *args]
        env = {**os.environ, "STAGING_PORT": str(self.port)}
        return subprocess.run(cmd, cwd=self.ws.root, capture_output=True, text=True, timeout=1800, env=env)

    def _start_compose(self) -> None:
        for f in (self.rel.compose_file, self.rel.env_file):
            if not self.ws.resolve(f).exists():
                raise StagingError(f"{f} is missing; the Deployment engineer must create it")
        r = self._compose("up", "-d", "--build", "--quiet-pull")
        if r.returncode != 0:
            raise StagingError(f"docker compose up failed:\n{_without_progress(r.stdout + r.stderr)[-4000:]}")

    def _start_local(self) -> None:
        env = self._env()
        for cmd in self.rel.local_prepare:
            r = self.sandbox.run_trusted(self.comp.runtime, self.comp.workdir, cmd, env=env)
            if not r.ok:
                raise StagingError(f"`{cmd}` failed:\n{r.output[-4000:]}")
        log_path = self.ws.resolve("reports/staging.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_file = open(log_path, "w", encoding="utf-8")
        self._proc = subprocess.Popen(
            shlex.split(self.rel.local_start), cwd=self.ws.resolve(self.comp.workdir),
            env={**os.environ, **self.sandbox.config.env, **env},
            stdout=self._log_file, stderr=subprocess.STDOUT, start_new_session=True,
        )

    def _wait_healthy(self) -> None:
        deadline = time.monotonic() + self.startup_timeout_s
        url = self.base_url + self.rel.health_path
        while time.monotonic() < deadline:
            if self._proc is not None and self._proc.poll() is not None:
                raise StagingError(f"The API exited during startup (code {self._proc.returncode}):\n{self.logs()}")
            status, _ = http_get(url)
            if status == 200:
                return
            time.sleep(1)
        raise StagingError(f"{url} did not return 200 within {self.startup_timeout_s}s:\n{self.logs()}")

    def logs(self, chars: int = 4000) -> str:
        if self.mode == "compose":
            r = self._compose("logs", "--no-color", "--tail", "200")
            return (r.stdout + r.stderr)[-chars:]
        p = self.ws.resolve("reports/staging.log")
        if self._log_file:
            self._log_file.flush()
        return p.read_text(encoding="utf-8", errors="replace")[-chars:] if p.exists() else ""

    def stop(self) -> None:
        if self.mode == "compose":
            self._compose("down", "-v")
            return
        if self._proc is not None and self._proc.poll() is None:
            os.killpg(self._proc.pid, signal.SIGTERM)
            try:
                self._proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(self._proc.pid, signal.SIGKILL)
        self._proc = None
        if self._log_file:
            self._log_file.close()
            self._log_file = None
