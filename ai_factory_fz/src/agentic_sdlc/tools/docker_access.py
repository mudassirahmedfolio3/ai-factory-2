"""How this process can reach Docker, found once and reused for every docker command.

- direct: `docker` works as is.
- sg:     the user is in the `docker` group, but this login session started before they were
          added (the group only applies to new logins). Commands then run through
          `sg docker -c ...`, which needs no password for group members, so nobody has to log
          out and back in.
- none:   Docker is not installed or the user is not in the `docker` group. That needs admin
          rights, so a person has to run `uv run setup` once.
"""

import getpass
import shlex
import shutil
import subprocess
import sys
from functools import lru_cache

# Unix-only; missing on Windows — Docker Desktop does not use the `docker` group.
try:
    import grp
except ImportError:  # pragma: no cover - Windows
    grp = None  # type: ignore[assignment]


def _ok(cmd: list[str]) -> bool:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def in_docker_group(user: str | None = None) -> bool:
    if grp is None or sys.platform == "win32":
        return False
    user = user or getpass.getuser()
    try:
        return user in grp.getgrnam("docker").gr_mem
    except KeyError:
        return False


@lru_cache(maxsize=1)
def access_mode() -> str:
    if not shutil.which("docker"):
        return "none"
    if _ok(["docker", "info"]):
        return "direct"
    if in_docker_group() and shutil.which("sg") and _ok(["sg", "docker", "-c", "docker info"]):
        return "sg"
    return "none"


def problem() -> str | None:
    """None if Docker is usable, else what is wrong and how to fix it."""
    if access_mode() != "none":
        return None
    if not shutil.which("docker"):
        return "Docker is not installed: run `uv run setup` once (it installs Docker with your sudo password)"
    if not in_docker_group():
        return "Your user is not in the 'docker' group: run `uv run setup` once (asks for your sudo password)"
    return "Docker is installed but not responding (is the Docker service running? `sudo systemctl start docker`)"


def argv(cmd: list[str]) -> list[str]:
    """The command to execute for a docker command line, given how Docker can be reached."""
    if cmd and cmd[0] == "docker" and access_mode() == "sg":
        return ["sg", "docker", "-c", shlex.join(cmd)]
    return cmd


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(argv(cmd), **kwargs)
