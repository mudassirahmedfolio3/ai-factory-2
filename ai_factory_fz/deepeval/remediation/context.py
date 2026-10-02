"""Collect the run artifacts the Project Manager needs as evidence (read-only, bounded)."""

import os
from pathlib import Path

ARTIFACTS = {
    "prd": "docs/prd.md",
    "architecture": "docs/architecture.md",
    "openapi": "docs/openapi.yaml",
    "design": "docs/design_system.md",
    "product_brief": "docs/product_brief.md",
}
CODE_ROOTS = ("server/src", "app/lib", "app/test", "app/integration_test", "server/smoke", "infra")
SKIP_DIRS = frozenset({"node_modules", ".dart_tool", "build", "dist", ".git"})
MAX_EXCERPTS = 40
NOT_AVAILABLE = "(not available)"
UNREADABLE = "(unreadable)"


def _is_within_run(path: Path, run_dir: Path) -> bool:
    """Check if resolved path is within run_dir."""
    try:
        path.resolve().relative_to(run_dir.resolve())
        return True
    except (ValueError, OSError, RuntimeError):   # outside, broken or looping symlink
        return False


def _walk_code(root: Path, run_dir: Path, skipped: list[str]) -> list[Path]:
    """Sorted files under root, pruning dependency/build directories during the walk."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in filenames:
            p = Path(dirpath) / name
            if not _is_within_run(p, run_dir):
                skipped.append(p.relative_to(run_dir).as_posix())
            elif p.is_file():
                found.append(p)
    return sorted(found)


def _read(path: Path, limit: int) -> tuple[str | None, str | None]:
    """Read file safely; return (content, error_type) where error_type is None, 'outside', or 'unreadable'."""
    try:
        return (path.read_text(encoding="utf-8", errors="replace")[:limit], None)
    except OSError:
        return (None, "unreadable")


def gather_context(run_dir: Path, max_chars: int = 12000) -> dict[str, str]:
    run_dir = Path(run_dir)
    ctx: dict[str, str] = {}
    missing: list[str] = []
    unreadable: list[str] = []
    skipped: list[str] = []

    for key, rel in ARTIFACTS.items():
        p = run_dir / rel
        if not p.is_file():
            ctx[key] = NOT_AVAILABLE
            missing.append(rel)
        elif not _is_within_run(p, run_dir):
            ctx[key] = NOT_AVAILABLE
            skipped.append(rel)
        else:
            content, error = _read(p, max_chars)
            if error == "unreadable":
                ctx[key] = UNREADABLE
                unreadable.append(rel)
            else:
                ctx[key] = content

    per_root = [_walk_code(run_dir / root, run_dir, skipped) for root in CODE_ROOTS if (run_dir / root).is_dir()]
    files = sorted(p for group in per_root for p in group)
    ctx["file_listing"] = "\n".join(p.relative_to(run_dir).as_posix() for p in files[:300]) or "(no source files)"

    # Round-robin over the code roots so one large root cannot crowd out the others.
    selected: list[Path] = []
    queues = [list(group) for group in per_root]
    while len(selected) < MAX_EXCERPTS and any(queues):
        for q in queues:
            if q and len(selected) < MAX_EXCERPTS:
                selected.append(q.pop(0))
    code_parts = []
    for p in selected:
        content, error = _read(p, 3000)
        if error is None:
            code_parts.append(f"### {p.relative_to(run_dir).as_posix()}\n{content}")
        elif error == "unreadable":
            unreadable.append(p.relative_to(run_dir).as_posix())
    ctx["code"] = "\n\n".join(code_parts)[: max_chars * 2] or "(no source files)"

    reports = sorted((run_dir / "reports").glob("*.md")) if (run_dir / "reports").is_dir() else []
    reports = [r for r in reports if _is_within_run(r, run_dir)]

    report_parts = []
    unreadable_reports = []
    for p in reports:
        content, error = _read(p, max_chars)
        if error is None:
            report_parts.append(f"### {p.name}\n{content}")
        elif error == "unreadable":
            unreadable_reports.append(p.relative_to(run_dir).as_posix())
            unreadable.append(p.relative_to(run_dir).as_posix())

    if report_parts:
        ctx["reports"] = "\n\n".join(report_parts)[: max_chars * 2]
    elif unreadable_reports:
        ctx["reports"] = UNREADABLE
    else:
        ctx["reports"] = "(no reports)"

    # Build limitations list
    limitations = []
    limitations.extend(f"- missing: {m}" for m in missing)
    limitations.extend(f"- skipped (outside run folder): {s}" for s in skipped)
    limitations.extend(f"- unreadable: {u}" for u in unreadable)
    if len(selected) < len(files):
        limitations.append(f"- truncated: {len(selected)} of {len(files)} code files shown in the excerpts")
    ctx["limitations"] = "\n".join(limitations) or "none"
    return ctx
