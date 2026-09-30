"""Unit tests for fz_emulator project resolution."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fz_emulator import resolve_flutter_project  # noqa: E402


def test_resolve_flutter_project_from_run_state(tmp_path, monkeypatch):
    import config

    runs = tmp_path / "runs"
    run_id = "20260101-120000"
    app_dir = runs / run_id / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "pubspec.yaml").write_text("name: demo\n", encoding="utf-8")
    monkeypatch.setattr(config, "FZ_RUNS_DIR", runs)

    resolved = resolve_flutter_project(
        run_id,
        {"flutter_project_dir": str(app_dir)},
    )
    assert resolved == app_dir


def test_resolve_flutter_project_falls_back_to_runs_dir(tmp_path, monkeypatch):
    import config

    runs = tmp_path / "runs"
    run_id = "20260101-120000"
    app_dir = runs / run_id / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "pubspec.yaml").write_text("name: demo\n", encoding="utf-8")
    monkeypatch.setattr(config, "FZ_RUNS_DIR", runs)

    assert resolve_flutter_project(run_id) == app_dir


def test_resolve_flutter_project_missing_pubspec(tmp_path, monkeypatch):
    import config

    runs = tmp_path / "runs"
    run_id = "20260101-120000"
    app_dir = runs / run_id / "app"
    app_dir.mkdir(parents=True)
    monkeypatch.setattr(config, "FZ_RUNS_DIR", runs)

    assert resolve_flutter_project(run_id) is None
