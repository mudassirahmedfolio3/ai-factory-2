"""Device support: toolchain readiness, emulator command wiring, release device round (fakes only)."""

import pytest

from agentic_sdlc.artifacts.reports import QAReport
from agentic_sdlc.registry.profiles import DeviceConfig, Profile
from agentic_sdlc.release.device import AndroidToolchain, Emulator
from agentic_sdlc.state import ItemProgress
from agentic_sdlc.tools.sandbox_exec import SandboxResult
from test_build_loop import ScriptedWorker
from test_release import FakeSandbox, FakeStaging, releaser


def test_toolchain_not_ready_until_everything_is_installed(tmp_path, monkeypatch):
    monkeypatch.setattr("agentic_sdlc.release.device.os.access", lambda p, m: True)
    real_exists = type(tmp_path).exists
    monkeypatch.setattr("agentic_sdlc.release.device.Path.exists", lambda self: True if str(self) == "/dev/kvm" else real_exists(self))
    reason = AndroidToolchain(DeviceConfig(), sdk_root=tmp_path / "sdk").not_ready_reason()
    assert "the emulator" in reason and "run `uv run setup-android` once" in reason


def test_toolchain_ready_when_sdk_parts_exist(tmp_path, monkeypatch):
    monkeypatch.setattr("agentic_sdlc.release.device.os.access", lambda p, m: True)
    cfg = DeviceConfig()
    tc = AndroidToolchain(cfg, sdk_root=tmp_path)
    for p in (tc.sdkmanager, tc.emulator, tc._system_image_dir(), tc.avd_home / f"{cfg.avd_name}.avd"):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.mkdir() if p.suffix == ".avd" or p == tc._system_image_dir() else p.write_text("")
    real_exists = type(tmp_path).exists
    monkeypatch.setattr("agentic_sdlc.release.device.Path.exists", lambda self: True if str(self) == "/dev/kvm" else real_exists(self))
    assert tc.not_ready_reason() is None


class RecordingSandbox:
    def __init__(self):
        self.calls = []

    def run_trusted(self, runtime, workdir, command, env=None, host_network=False, timeout_s=None):
        self.calls.append((runtime, workdir, command, host_network))
        return SandboxResult(exit_code=0, output="1")


def test_emulator_device_commands_run_in_the_container_after_adb_finds_the_device(tmp_path):
    from agentic_sdlc.workspace import Workspace
    sb = RecordingSandbox()
    em = Emulator(AndroidToolchain(DeviceConfig()), sb, Workspace.create("r", runs_dir=tmp_path))
    em.run("flutter test integration_test -d emulator-5554", "app")
    runtime, workdir, command, host = sb.calls[-1]
    assert (runtime, workdir, host) == ("flutter", "app", True)
    assert command.startswith("sh -c ") and "adb -s emulator-5554 wait-for-device; flutter test" in command
    em.launch("com.x.app")
    assert "monkey -p com.x.app" in sb.calls[-1][2]


# ---------- release device round ----------

class FakeToolchain:
    def __init__(self, reason=None):
        self.reason = reason

    def not_ready_reason(self):
        return self.reason


class FakeEmulator:
    serial = "emulator-5554"

    def __init__(self, reason=None, build_ok=True, test_ok=True):
        self.tc = FakeToolchain(reason)
        self.build_ok, self.test_ok = build_ok, test_ok
        self.commands, self.started, self.stopped = [], 0, 0

    def start(self, window=False):
        self.started += 1

    def run(self, command, workdir, timeout_s=None):
        self.commands.append(command)
        ok = self.build_ok if command.startswith("flutter build") else self.test_ok
        return SandboxResult(exit_code=0 if ok else 1, output="ok" if ok else "SocketException: Cleartext HTTP traffic to 10.0.2.2 not permitted")

    def install(self, apk, workdir, app_id=""):
        return SandboxResult(exit_code=0, output="Success")

    def launch(self, app_id):
        return SandboxResult(exit_code=0, output="")

    def screenshot(self, rel):
        return rel

    def stop(self):
        self.stopped += 1


def device_releaser(tmp_path, prd, backlog, worker, emulator, test_dir=True):
    r, s, ws = releaser(tmp_path, prd, backlog, worker, cfg={"fix_rounds": 1, "device": {"enabled": True}})
    r.emulator = emulator
    s.build.items["WI-002"] = ItemProgress(status="done", summary="screen")  # WI-002 is the frontend item
    if test_dir:
        (ws.root / "app" / "integration_test").mkdir(parents=True, exist_ok=True)
    return r, s, ws


def test_device_round_builds_installs_tests_and_reports(tmp_path, prd, backlog, monkeypatch):
    monkeypatch.setattr("agentic_sdlc.release.releaser.time.sleep", lambda s: None)
    worker = ScriptedWorker({"integration_review": [QAReport(milestone_id="integration", passed=True, summary="ok")]})
    em = FakeEmulator()
    r, s, ws = device_releaser(tmp_path, prd, backlog, worker, em)
    r.verify()
    assert s.release.verified and s.release.device_passed
    assert "write_device_tests" in [j.task_key for j in worker.jobs]
    assert em.commands[0] == "flutter build apk --debug --dart-define=API_BASE_URL=http://10.0.2.2:3999/api/v1"
    assert em.commands[1].startswith("flutter test integration_test -d emulator-5554")
    assert s.release.device_screenshots == ["reports/device/round1/launch.png", "reports/device/round1/after_tests.png"]
    assert em.stopped == 1
    report = (ws.root / "reports" / "release_round1.md").read_text()
    assert "## On-device (Android emulator)" in report and "launch.png" in report


def test_device_failures_go_to_the_frontend_developer(tmp_path, prd, backlog, monkeypatch):
    monkeypatch.setattr("agentic_sdlc.release.releaser.time.sleep", lambda s: None)
    ok = QAReport(milestone_id="integration", passed=True, summary="ok")
    worker = ScriptedWorker({"integration_review": [ok, ok]})
    em = FakeEmulator(test_ok=False)
    r, s, _ = device_releaser(tmp_path, prd, backlog, worker, em)
    r.verify()
    fixes = [j for j in worker.jobs if j.task_key == "fix_work_item"]
    assert fixes and fixes[0].agent_key == "frontend_developer" and fixes[0].workdir == "app"
    assert "Cleartext HTTP traffic" in fixes[0].inputs["problems"]


def test_device_not_ready_is_noted_not_failed(tmp_path, prd, backlog):
    worker = ScriptedWorker({"integration_review": [QAReport(milestone_id="integration", passed=True, summary="ok")]})
    em = FakeEmulator(reason="Android emulator not set up: run `uv run setup-android` once")
    r, s, _ = device_releaser(tmp_path, prd, backlog, worker, em)
    r.verify()
    assert s.release.verified and s.release.device_passed is None
    assert "setup-android" in s.release.device_note
    assert "not run: Android emulator not set up" in r.gate_summary()


def test_staging_writes_a_compose_override_for_device_env(tmp_path):
    from agentic_sdlc.release.staging import Staging
    from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRunner
    from agentic_sdlc.workspace import Workspace
    profile = Profile.load("flutter_nestjs_ecommerce")
    ws = Workspace.create("r", runs_dir=tmp_path)
    st = Staging(ws, profile, SandboxRunner(ws, profile.sandbox, SandboxMode.DOCKER), port=3100)
    st.extra_env = {"PUBLIC_ASSET_BASE_URL": "http://10.0.2.2:3100/assets"}
    import agentic_sdlc.release.staging as mod
    seen = {}
    mod_run = mod.subprocess.run
    mod.subprocess.run = lambda cmd, **kw: seen.setdefault("cmd", cmd) and mod_run(["true"])
    try:
        st._compose("ps")
    finally:
        mod.subprocess.run = mod_run
    assert str(ws.root / ".sdlc/compose.override.yml") in seen["cmd"]
    assert 'PUBLIC_ASSET_BASE_URL: "http://10.0.2.2:3100/assets"' in (ws.root / ".sdlc/compose.override.yml").read_text()


def test_enabling_device_checks_reopens_a_verified_and_approved_release(tmp_path, prd, backlog, monkeypatch):
    from agentic_sdlc.state import GateDecision
    monkeypatch.setattr("agentic_sdlc.release.releaser.time.sleep", lambda s: None)
    worker = ScriptedWorker({"integration_review": [QAReport(milestone_id="integration", passed=True, summary="ok")]})
    r, s, _ = device_releaser(tmp_path, prd, backlog, worker, FakeEmulator())
    s.release.verified, s.release.production = True, "packaged"
    s.gate_history.append(GateDecision(gate="release", approved=True))
    r.verify()
    assert s.release.verified and s.release.device_passed          # verified again, on device
    assert not s.gate_approved("release")                          # the human must approve again
    assert s.release.production == "todo"
    assert s.rejections("release") == []                           # a reopen is not a rejection


def test_install_and_launch_wait_for_the_device(tmp_path):
    from agentic_sdlc.workspace import Workspace
    sb = RecordingSandbox()
    em = Emulator(AndroidToolchain(DeviceConfig()), sb, Workspace.create("r", runs_dir=tmp_path))
    em.install("build/app.apk", "app")
    em.launch("com.x.app")
    for _, _, command, host in sb.calls:
        assert host and "wait-for-device;" in command
    assert "install -r build/app.apk" in sb.calls[0][2]


def test_install_replaces_an_app_signed_with_another_debug_key(tmp_path):
    from agentic_sdlc.workspace import Workspace

    class Sb(RecordingSandbox):
        def run_trusted(self, runtime, workdir, command, env=None, host_network=False, timeout_s=None):
            self.calls.append(command)
            if "install -r" in command:
                return SandboxResult(exit_code=1, output="Failure [INSTALL_FAILED_UPDATE_INCOMPATIBLE: signatures do not match]")
            return SandboxResult(exit_code=0, output="Success")

    sb = Sb()
    em = Emulator(AndroidToolchain(DeviceConfig()), sb, Workspace.create("r", runs_dir=tmp_path))
    assert em.install("app.apk", "app", "com.x.app").ok
    assert any("uninstall com.x.app" in c for c in sb.calls)
