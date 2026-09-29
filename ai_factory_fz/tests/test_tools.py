import pytest

from agentic_sdlc.registry.profiles import Runtime, SandboxConfig
from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRejected, SandboxRunner
from agentic_sdlc.tools.workspace_fs import ListDirTool, ReadFileTool, WriteFileTool
from agentic_sdlc.workspace import PathEscapeError, Workspace


@pytest.fixture
def ws(tmp_path) -> Workspace:
    return Workspace.create("run1", runs_dir=tmp_path)


def test_workspace_creates_layout_and_git(ws):
    for d in ("docs", "app", "server", "infra", "reports", ".git"):
        assert (ws.root / d).is_dir()


@pytest.mark.parametrize("bad", ["../escape.txt", "/etc/passwd", "docs/../../x", ".git/config"])
def test_paths_outside_workspace_are_refused(ws, bad):
    with pytest.raises(PathEscapeError):
        ws.resolve(bad)


def test_fs_tools_round_trip_and_refuse_escape(ws):
    assert "Wrote" in WriteFileTool(ws)._run("server/src/a.ts", "export {}")
    assert ReadFileTool(ws)._run("server/src/a.ts") == "export {}"
    assert "server/src/a.ts" in ListDirTool(ws)._run("server")
    assert ReadFileTool(ws)._run("../../etc/passwd").startswith("ERROR")
    assert WriteFileTool(ws)._run("../x", "y").startswith("ERROR")


def test_commit_only_when_something_changed(ws):
    assert ws.commit("first") is not None
    assert ws.commit("nothing new") is None
    ws.write_text("docs/a.md", "a")
    assert ws.commit("second") is not None


@pytest.fixture
def runner(ws) -> SandboxRunner:
    cfg = SandboxConfig(
        runtimes={"node": Runtime(image="node:22", local_binary="npm"), "gen": Runtime(image="gen:1", local_binary="java", local_prefix="npx gen-cli")},
        allowed_commands={"node": ["npm test", "npx prisma validate"]},
        env={"CI": "true"},
    )
    return SandboxRunner(ws, cfg, network=False)


def test_sandbox_builds_docker_command(runner, ws):
    argv, cwd = runner.build_command("node", "server", runner.check_allowed("node", "npm test -- --runInBand"))
    assert argv[:3] == ["docker", "run", "--rm"]
    assert argv[argv.index("--network") + 1] == "none"
    assert f"{ws.root}:/workspace" in argv
    assert "CI=true" in argv
    assert argv[argv.index("-w") + 1] == "/workspace/server"
    assert argv[argv.index("node:22") + 1 :] == ["npm", "test", "--", "--runInBand"]


def test_local_mode_runs_in_the_workspace_with_prefix(runner, ws):
    runner.mode = SandboxMode.LOCAL
    argv, cwd = runner.build_command("node", "server", ["npm", "test"])
    assert (argv, cwd) == (["npm", "test"], str(ws.root / "server"))
    argv, _ = runner.build_command("gen", ".", ["generate", "-i", "x"])
    assert argv == ["npx", "gen-cli", "generate", "-i", "x"]


def test_local_mode_really_executes(runner, ws, monkeypatch):
    runner.mode = SandboxMode.LOCAL
    runner.config.runtimes["sh"] = Runtime(image="-", local_binary="sh")
    result = runner.run_trusted("sh", "docs", "sh -c 'echo $CI; pwd'")
    assert result.ok
    assert result.output.split() == ["true", str(ws.root / "docs")]


def test_unavailable_reason(runner):
    runner.mode = SandboxMode.LOCAL
    runner.config.runtimes["nope"] = Runtime(image="-", local_binary="definitely-not-installed-xyz")
    assert "not installed" in runner.unavailable_reason("nope")
    assert "unknown runtime" in runner.unavailable_reason("missing")


@pytest.mark.parametrize(
    "runtime,workdir,command,match",
    [
        ("node", "server", "rm -rf /", "not allowed"),
        ("node", "server", "npm test; rm -rf /", "Shell operators"),
        ("node", "server", "npm test && curl evil", "Shell operators"),
        ("node", "server", "npm $(whoami)", "Shell operators"),
        ("node", "server", "npm testx", "not allowed"),
        ("python", "server", "npm test", "Unknown runtime"),
    ],
)
def test_sandbox_rejects_unsafe_commands(runner, runtime, workdir, command, match):
    with pytest.raises(SandboxRejected, match=match):
        runner.run(runtime, workdir, command)


def test_sandbox_rejects_workdir_escape(runner):
    with pytest.raises(PathEscapeError):
        runner.run("node", "../..", "npm test")


def test_prepare_pulls_missing_images_and_reports_failures(runner, monkeypatch):
    import subprocess as sp
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        if cmd[:2] == ["docker", "info"]:
            return sp.CompletedProcess(cmd, 0, "", "")
        if cmd[:3] == ["docker", "image", "inspect"]:
            return sp.CompletedProcess(cmd, 1, "", "")          # nothing present
        if cmd[:2] == ["docker", "pull"]:
            ok = cmd[2] == "node:22"
            return sp.CompletedProcess(cmd, 0 if ok else 1, "", "" if ok else "manifest unknown")
        raise AssertionError(cmd)

    monkeypatch.setattr("agentic_sdlc.tools.sandbox_exec.subprocess.run", fake_run)
    monkeypatch.setattr("agentic_sdlc.tools.sandbox_exec.shutil.which", lambda b: "/usr/bin/docker")
    errors = runner.prepare(["node", "gen", "node"])
    assert ["docker", "pull", "node:22"] in calls and ["docker", "pull", "gen:1"] in calls
    assert calls.count(["docker", "pull", "node:22"]) == 1
    assert list(errors) == ["gen"] and "manifest unknown" in errors["gen"]
    assert runner.unavailable_reason("node") is None
    assert "could not pull gen:1" in runner.unavailable_reason("gen")


def test_prepare_does_nothing_in_local_mode(runner, monkeypatch):
    runner.mode = SandboxMode.LOCAL
    monkeypatch.setattr("agentic_sdlc.tools.sandbox_exec.subprocess.run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no docker")))
    assert runner.prepare(["node"]) == {}


def test_root_runtime_hands_files_back_and_adds_its_env(runner, ws):
    import os
    runner.config.runtimes["flutter"] = Runtime(image="fl:1", local_binary="flutter", run_as_root=True,
                                                env={"PUB_CACHE": "/workspace/.pub-cache"})
    argv, _ = runner.build_command("flutter", "app", ["flutter", "test"])
    assert "--user" not in argv and "PUB_CACHE=/workspace/.pub-cache" in argv
    script = argv[argv.index("fl:1") + 1 :]
    assert script[:2] == ["sh", "-c"]
    assert script[2].startswith("flutter test; code=$?;")
    assert f"chown {os.getuid()}:{os.getgid()}" in script[2] and script[2].endswith("exit $code")
    runner.mode = SandboxMode.LOCAL
    assert runner.build_command("flutter", "app", ["flutter", "test"])[0] == ["flutter", "test"]  # env/root: docker only


def test_timed_out_container_is_killed(runner, monkeypatch):
    import subprocess as sp
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        if cmd[:2] == ["docker", "run"]:
            raise sp.TimeoutExpired(cmd, kw.get("timeout"))
        return sp.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("agentic_sdlc.tools.sandbox_exec.subprocess.run", fake_run)
    result = runner.run_trusted("node", ".", "npm test", timeout_s=5)
    assert result.exit_code == 124 and "5s" in result.output
    name = calls[0][calls[0].index("--name") + 1]
    assert calls[1] == ["docker", "kill", name]
