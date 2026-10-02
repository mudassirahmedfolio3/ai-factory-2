import os
import pytest
from remediation.context import gather_context


def make_run(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "prd.md").write_text("PRD text", encoding="utf-8")
    (tmp_path / "docs" / "openapi.yaml").write_text("openapi: 3.1.0", encoding="utf-8")
    (tmp_path / "server" / "src").mkdir(parents=True)
    (tmp_path / "server" / "src" / "main.ts").write_text("bootstrap()", encoding="utf-8")
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "qa_m1.md").write_text("QA report", encoding="utf-8")
    return tmp_path


def test_reads_present_artifacts_and_lists_files(tmp_path):
    ctx = gather_context(make_run(tmp_path))
    assert ctx["prd"] == "PRD text" and ctx["openapi"] == "openapi: 3.1.0"
    assert "server/src/main.ts" in ctx["file_listing"] and "bootstrap()" in ctx["code"]
    assert "QA report" in ctx["reports"]


def test_missing_artifacts_are_marked_and_listed_as_limitations(tmp_path):
    ctx = gather_context(make_run(tmp_path))
    assert ctx["architecture"] == "(not available)"
    assert "docs/architecture.md" in ctx["limitations"] and "docs/prd.md" not in ctx["limitations"]


def test_empty_run_does_not_crash(tmp_path):
    ctx = gather_context(tmp_path)
    assert ctx["file_listing"] == "(no source files)" and ctx["code"] == "(no source files)"
    assert ctx["reports"] == "(no reports)"


def test_long_files_are_truncated(tmp_path):
    run = make_run(tmp_path)
    (run / "docs" / "prd.md").write_text("x" * 50_000, encoding="utf-8")
    assert len(gather_context(run, max_chars=1000)["prd"]) <= 1000


def test_symlink_outside_run_folder_is_skipped(tmp_path):
    """Symlinks pointing outside run_dir must not be read; must be tracked in limitations."""
    run = make_run(tmp_path)
    outside_dir = tmp_path.parent / "outside"
    outside_dir.mkdir(exist_ok=True)
    outside_file = outside_dir / "secret.md"
    outside_file.write_text("secret content", encoding="utf-8")

    try:
        symlink_path = run / "docs" / "architecture.md"
        os.symlink(outside_file, symlink_path)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on this system")

    ctx = gather_context(run)
    assert ctx["architecture"] == "(not available)"
    assert "secret content" not in str(ctx)
    assert "- skipped (outside run folder): docs/architecture.md" in ctx["limitations"]


def test_unreadable_file_is_handled_gracefully(tmp_path, monkeypatch):
    """Files that raise OSError must not abort gather_context; must be marked unreadable."""
    run = make_run(tmp_path)

    original_read_text = __import__("pathlib").Path.read_text

    def mock_read_text(self, *args, **kwargs):
        if self.name == "qa_m1.md":
            raise PermissionError(f"Permission denied: {self}")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr("pathlib.Path.read_text", mock_read_text)

    ctx = gather_context(run)
    assert ctx["reports"] == "(unreadable)"
    assert "- unreadable: reports/qa_m1.md" in ctx["limitations"]


def test_large_app_does_not_crowd_out_the_backend(tmp_path):
    run = make_run(tmp_path)
    (run / "server" / "src" / "main.ts").write_text("SERVER-CODE", encoding="utf-8")
    (run / "app" / "lib").mkdir(parents=True)
    for i in range(60):
        (run / "app" / "lib" / f"w{i:02d}.dart").write_text("// app", encoding="utf-8")
    ctx = gather_context(run)
    assert "SERVER-CODE" in ctx["code"]
    assert "- truncated: 40 of 61 code files shown in the excerpts" in ctx["limitations"]


def test_dependency_and_build_dirs_are_never_listed(tmp_path):
    run = make_run(tmp_path)
    for name in ("node_modules", ".dart_tool", "build", "dist", ".git"):
        (run / "server" / "src" / name).mkdir()
        (run / "server" / "src" / name / "junk.js").write_text("JUNK", encoding="utf-8")
    ctx = gather_context(run)
    assert "junk.js" not in ctx["file_listing"] and "JUNK" not in ctx["code"]
    assert "truncated" not in ctx["limitations"]


def test_complete_small_run_has_no_truncation_limitation(tmp_path):
    assert "truncated" not in gather_context(make_run(tmp_path))["limitations"]


def test_broken_symlink_in_code_root_is_skipped_not_fatal(tmp_path):
    run = make_run(tmp_path)
    try:
        os.symlink(tmp_path / "nowhere", run / "server" / "src" / "dangling.ts")
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on this system")
    ctx = gather_context(run)
    assert "- skipped (outside run folder): server/src/dangling.ts" in ctx["limitations"]
    assert "bootstrap()" in ctx["code"]
