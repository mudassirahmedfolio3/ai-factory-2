import os
import time

import common


def make(runs, *names):
    for n in names:
        (runs / n).mkdir(parents=True)


def test_picks_the_newest_run_id_not_the_most_recently_edited_folder(tmp_path):
    make(tmp_path, "20261003-044724", "20261004-043044", "20261002-120919")
    time.sleep(0.05)
    make(tmp_path, "sample-manual", "thread-test")        # scratch folders touched last
    os.utime(tmp_path / "20261003-044724", None)           # an old run edited just now must not win either
    assert common.latest_run_dir(tmp_path).name == "20261004-043044"


def test_a_run_id_with_a_slug_counts_and_sorts_by_time(tmp_path):
    make(tmp_path, "20261004-043044-lighting-retail", "20261004-051500-shoes", "20261003-235959-zzz")
    assert common.latest_run_dir(tmp_path).name == "20261004-051500-shoes"


def test_without_any_run_id_it_falls_back_to_the_most_recent_folder(tmp_path):
    make(tmp_path, "sample-manual")
    time.sleep(0.05)
    make(tmp_path, "debug-test")
    assert common.latest_run_dir(tmp_path).name == "debug-test"


def test_no_runs_folder_or_an_empty_one_gives_none(tmp_path):
    assert common.latest_run_dir(tmp_path / "missing") is None
    assert common.latest_run_dir(tmp_path) is None


def test_files_in_the_runs_folder_are_ignored(tmp_path):
    make(tmp_path, "20261002-120919")
    (tmp_path / "20261009-000000.txt").write_text("x", encoding="utf-8")
    assert common.latest_run_dir(tmp_path).name == "20261002-120919"


def test_find_run_dir_uses_the_env_override_first_then_the_latest_build(tmp_path, monkeypatch):
    make(tmp_path, "20261004-043044", "sample-manual")
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    monkeypatch.delenv("DEEPEVAL_RUN_DIR", raising=False)
    assert common.find_run_dir().name == "20261004-043044"
    monkeypatch.setenv("DEEPEVAL_RUN_DIR", str(tmp_path / "sample-manual"))
    assert common.find_run_dir().name == "sample-manual"
    monkeypatch.setenv("DEEPEVAL_RUN_DIR", str(tmp_path / "does-not-exist"))
    assert common.find_run_dir() is None
