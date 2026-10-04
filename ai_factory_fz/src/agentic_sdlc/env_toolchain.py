"""Prepend repo-local and common toolchain directories to PATH (Windows-friendly).

API-spawned workers and Cursor/Claude headless CLIs often inherit a minimal PATH without
Flutter, Node, Git, or Java even when they are installed for the interactive user.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from agentic_sdlc.settings import PROJECT_ROOT


def _repo_root() -> Path:
    return PROJECT_ROOT.parent


def toolchain_path_prepend() -> list[str]:
    """Directories to prepend to PATH, in order."""
    parts: list[str] = []
    repo = _repo_root()
    flutter_bin = repo / ".tools" / "flutter" / "bin"
    if flutter_bin.is_dir():
        parts.append(str(flutter_bin))

    for candidate in (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "nodejs",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "node",
        Path(r"C:\Program Files\Git\cmd"),
        Path(r"C:\Program Files\Git\bin"),
    ):
        if candidate.is_dir():
            parts.append(str(candidate))

    if not os.environ.get("JAVA_HOME"):
        for base in (
            Path(r"C:\Program Files\Microsoft"),
            Path(r"C:\Program Files\Eclipse Adoptium"),
            Path(r"C:\Program Files\Java"),
        ):
            if not base.is_dir():
                continue
            jdks = sorted(base.glob("jdk-*"), reverse=True)
            if jdks:
                parts.append(str(jdks[0] / "bin"))
                break
    elif sys.platform == "win32":
        java_bin = Path(os.environ["JAVA_HOME"]) / "bin"
        if java_bin.is_dir():
            parts.append(str(java_bin))

    return parts


def enrich_path(environ: dict[str, str]) -> None:
    """Mutate *environ* by prepending toolchain_path_prepend() to PATH."""
    prepend = toolchain_path_prepend()
    if not prepend:
        return
    existing = environ.get("PATH", "")
    environ["PATH"] = os.pathsep.join(prepend) + (os.pathsep + existing if existing else "")


def apply_toolchain_path() -> None:
    """Prepend toolchains to the current process environment."""
    enrich_path(os.environ)
