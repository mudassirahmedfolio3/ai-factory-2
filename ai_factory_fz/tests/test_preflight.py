"""Preflight: stops a run before any tokens are spent when the machine is not ready."""

from agentic_sdlc import preflight
from agentic_sdlc.llms.backend import CredentialsError
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.tools import docker_access
from agentic_sdlc.tools.sandbox_exec import SandboxMode


class Models:
    def __init__(self, error=None):
        self.error = error

    def check_credentials(self):
        if self.error:
            raise CredentialsError(self.error)


class Sandbox:
    def __init__(self, mode=SandboxMode.DOCKER, pull_errors=None, unavailable=None):
        self.mode, self.pull_errors, self.unavailable = mode, pull_errors or {}, unavailable or {}
        self.prepared = None

    def prepare(self, runtimes):
        self.prepared = runtimes
        return self.pull_errors

    def unavailable_reason(self, rt):
        return self.unavailable.get(rt)


PIPE = {"phases": {"build": True, "release": False}}


def profile():
    return Profile.load("flutter_nestjs_ecommerce")


def test_ready_machine_pulls_images_and_passes():
    sb = Sandbox()
    assert preflight.check(PIPE, profile(), sb, Models()) == []
    assert sb.prepared == ["flutter", "node", "openapi"]


def test_missing_credentials_and_docker_are_reported_with_fixes(monkeypatch):
    monkeypatch.setattr(docker_access, "access_mode", lambda: "none")
    monkeypatch.setattr(docker_access.shutil, "which", lambda b: "/usr/bin/docker")
    monkeypatch.setattr(docker_access, "in_docker_group", lambda user=None: False)
    problems = preflight.check(PIPE, profile(), Sandbox(), Models("CLAUDE_CODE_OAUTH_TOKEN is not set"))
    assert any("CLAUDE_CODE_OAUTH_TOKEN" in p for p in problems)
    assert any("uv run setup" in p for p in problems)


def test_image_pull_failures_block():
    problems = preflight.check(PIPE, profile(), Sandbox(pull_errors={"flutter": "timed out"}), Models())
    assert problems == ["Toolchain image for 'flutter' is not available: timed out"]


def test_planning_only_runs_need_no_toolchains():
    sb = Sandbox()
    assert preflight.check({"phases": {"build": False, "release": False}}, profile(), sb, Models()) == []
    assert sb.prepared is None


def test_device_checks_need_the_emulator(monkeypatch):
    monkeypatch.setattr("agentic_sdlc.preflight.AndroidToolchain.not_ready_reason",
                        lambda self: "Android emulator not set up (...): run `uv run setup-android` once")
    pipe = {"phases": {"build": True, "release": True}, "release": {"device": {"enabled": True}}}
    problems = preflight.check(pipe, profile(), Sandbox(), Models())
    assert any("Android emulator not set up" in p and "uv run setup" in p for p in problems)


def test_local_mode_checks_installed_toolchains(monkeypatch):
    monkeypatch.delenv("SDLC_STAGING_DATABASE_URL", raising=False)
    sb = Sandbox(mode=SandboxMode.LOCAL, unavailable={"flutter": "'flutter' is not installed"})
    problems = preflight.check({"phases": {"build": True, "release": True}}, profile(), sb, Models())
    assert "Toolchain 'flutter': 'flutter' is not installed" in problems
    assert any("SDLC_STAGING_DATABASE_URL" in p for p in problems)
