import subprocess

import remediation_trigger as t


def test_does_nothing_unless_enabled(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(t.subprocess, "Popen", lambda *a, **k: calls.append((a, k)))
    monkeypatch.delenv("DEEPEVAL_REMEDIATE", raising=False)
    assert t.maybe_start(tmp_path, tmp_path / "eval_report_flow.json") is None
    monkeypatch.setenv("DEEPEVAL_REMEDIATE", "0")
    assert t.maybe_start(tmp_path, tmp_path / "eval_report_flow.json") is None
    assert calls == []


def test_starts_remediate_with_absolute_paths_when_enabled(tmp_path, monkeypatch):
    calls = []

    class FakeProc:
        pass

    monkeypatch.setattr(t.subprocess, "Popen", lambda *a, **k: calls.append((a, k)) or FakeProc())
    monkeypatch.setenv("DEEPEVAL_REMEDIATE", "1")
    run = tmp_path / "my run"
    run.mkdir()
    log = t.maybe_start(run, run / "eval_report_flow.json")
    (cmd,), kwargs = calls[0]
    assert cmd[:3] == ["uv", "run", "python"] and cmd[3].endswith("remediate.py") and "run" in cmd[4:]
    assert str(run.resolve()) in cmd and str((run / "eval_report_flow.json").resolve()) in cmd
    assert kwargs["cwd"] == t.FZ_ROOT and log == run / "remediation" / "trigger.log" and log.parent.is_dir()


def test_a_failing_launch_never_raises(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise OSError("uv not found")

    monkeypatch.setattr(t.subprocess, "Popen", boom)
    monkeypatch.setenv("DEEPEVAL_REMEDIATE", "1")
    assert t.maybe_start(tmp_path, tmp_path / "x.json") is None


def test_any_exception_from_launch_never_raises(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(t.subprocess, "Popen", boom)
    monkeypatch.setenv("DEEPEVAL_REMEDIATE", "1")
    assert t.maybe_start(tmp_path, tmp_path / "x.json") is None


def test_path_resolution_failure_never_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPEVAL_REMEDIATE", "1")
    assert t.maybe_start("\0bad", tmp_path / "x.json") is None


def test_windows_flags_do_not_detach_console_window():
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        assert t.WINDOWS_FLAGS == subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        assert not t.WINDOWS_FLAGS & subprocess.DETACHED_PROCESS
