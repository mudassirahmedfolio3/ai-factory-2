"""Guardrails on the changes a coding agent makes (checked before the change is committed).

  DV1 no weakening tests: no deleted test files, no fewer test cases, no newly skipped tests
  DV2 no secrets in changed files
  DV3 stay in scope: only the component's folder; contract copies stay equal to docs/

A violation goes back to the same agent as feedback (like a failing build), so it can undo it.
"""

import fnmatch
import re
from pathlib import Path
from typing import Any

from git import Repo

from agentic_sdlc.guardrails import secrets
from agentic_sdlc.registry.profiles import Component, Profile
from agentic_sdlc.workspace import Workspace

CODE_RULES = ["DV1", "DV2", "DV3"]

# Run-level artifacts (transcripts, QA reports, scaffold logs) — not owned by a single component.
SCOPE_INFRA_PREFIXES = ("reports/",)

# Test file patterns per toolchain; a profile can override them under guardrails.tests.
DEFAULT_TESTS: dict[str, dict[str, Any]] = {
    "node": {"files": ["*.spec.ts", "*.test.ts", "*.e2e-spec.ts", "*.spec.js", "*.test.js"],
             "case": r"\b(it|test)\s*\(",
             "skip": r"\b(it|test|describe)\.(skip|todo)\s*\(|\bx(it|describe|test)\s*\("},
    "flutter": {"files": ["*_test.dart"],
                "case": r"\b(test|testWidgets)\s*\(",
                "skip": r"\bskip\s*:\s*(true|['\"])"},
}


def changed_files(ws: Workspace) -> list[str]:
    """Paths changed since the last commit, including new files (ignored files excluded)."""
    repo = Repo(ws.root)
    paths = {d.a_path for d in repo.index.diff(None)} | {d.a_path for d in repo.head.commit.diff(None)} \
        if repo.head.is_valid() else set()
    paths |= set(repo.untracked_files)
    return sorted(paths)


def discard_changes(ws: Workspace, workdir: str) -> None:
    """Throw away uncommitted changes under a folder (e.g. a failed or rejected work item)."""
    repo = Repo(ws.root)
    target = "." if workdir in (".", "") else workdir
    if repo.head.is_valid():
        repo.git.checkout("HEAD", "--", target)
    repo.git.clean("-fdq", "--", target)


def _head_text(repo: Repo, path: str) -> str | None:
    try:
        return repo.git.show(f"HEAD:{path}")
    except Exception:
        return None


def _test_cfg(profile: Profile, runtime: str | None) -> dict[str, Any] | None:
    return (profile.guardrails.get("tests") or {}).get(runtime) or DEFAULT_TESTS.get(runtime or "")


def _is_test(path: str, cfg: dict[str, Any]) -> bool:
    return any(fnmatch.fnmatch(Path(path).name, pat) for pat in cfg["files"])


def dv1_tests(ws: Workspace, comp: Component, profile: Profile, files: list[str]) -> list[str]:
    cfg = _test_cfg(profile, comp.runtime)
    if not cfg:
        return []
    repo = Repo(ws.root)
    if not repo.head.is_valid():
        return []
    case, skip = re.compile(cfg["case"]), re.compile(cfg["skip"])
    prefix = "" if comp.workdir in (".", "") else comp.workdir.rstrip("/") + "/"
    head_tests = [p for p in repo.git.ls_files("--", comp.workdir).splitlines() if _is_test(p, cfg)] \
        if prefix else [p for p in repo.git.ls_files().splitlines() if _is_test(p, cfg)]
    errors = []
    before_cases = after_cases = before_skips = after_skips = 0
    for path in head_tests:
        old = _head_text(repo, path) or ""
        before_cases += len(case.findall(old))
        before_skips += len(skip.findall(old))
        disk = ws.root / path
        if not disk.exists():
            errors.append(f"DV1: test file {path} was deleted")
            continue
        new = disk.read_text(encoding="utf-8", errors="replace")
        after_cases += len(case.findall(new))
        after_skips += len(skip.findall(new))
    for path in files:  # new test files add cases (and can add skips)
        if path not in head_tests and path.startswith(prefix) and _is_test(path, cfg) and (ws.root / path).exists():
            new = (ws.root / path).read_text(encoding="utf-8", errors="replace")
            after_cases += len(case.findall(new))
            after_skips += len(skip.findall(new))
    if after_cases < before_cases:
        errors.append(f"DV1: the number of test cases dropped from {before_cases} to {after_cases}; "
                      "fix the code instead of removing tests")
    if after_skips > before_skips:
        errors.append(f"DV1: {after_skips - before_skips} test(s) were newly skipped; fix the code instead of skipping tests")
    return errors


def dv2_secrets(ws: Workspace, profile: Profile, files: list[str]) -> list[str]:
    ignore = profile.guardrails.get("secret_scan_ignore", [])
    errors = []
    for path in files:
        p = ws.root / path
        if any(fnmatch.fnmatch(path, pat) for pat in ignore) or not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        errors += [f"DV2: {path} contains what looks like {what}; use an environment variable or a placeholder"
                   for what in secrets.find(text)]
    return errors


def dv3_scope(ws: Workspace, comp: Component, profile: Profile, files: list[str]) -> list[str]:
    errors = []
    if comp.workdir not in (".", ""):
        prefix = comp.workdir.rstrip("/") + "/"
        allowed = [prefix, *(profile.guardrails.get("scope_also_allowed") or [])]
        outside = [
            f for f in files
            if not any(f.startswith(a) for a in allowed)
            and not any(f.startswith(p) for p in SCOPE_INFRA_PREFIXES)
        ]
        errors += [f"DV3: {f} is outside this work item's component ({comp.workdir}/); undo that change" for f in outside]
    for source, copies in (profile.guardrails.get("contract_copies") or {}).items():
        src = ws.root / source
        for copy in copies:
            dst = ws.root / copy
            if src.exists() and dst.exists() and copy in files and dst.read_bytes() != src.read_bytes():
                errors.append(f"DV3: {copy} must stay identical to the approved {source}; "
                              "contract changes go through the Architect and Gate 2")
    return errors


def check_changes(ws: Workspace, comp: Component, profile: Profile, rules: set[str]) -> list[str]:
    """Guardrail problems in the uncommitted changes of one work item (empty = ok to commit)."""
    files = changed_files(ws)
    errors = []
    if "DV1" in rules:
        errors += dv1_tests(ws, comp, profile, files)
    if "DV2" in rules:
        errors += dv2_secrets(ws, profile, files)
    if "DV3" in rules:
        errors += dv3_scope(ws, comp, profile, files)
    return errors
