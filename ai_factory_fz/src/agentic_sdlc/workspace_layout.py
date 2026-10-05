"""Resolve component directories when architect output differs from profile defaults."""

from __future__ import annotations

from agentic_sdlc.registry.profiles import Component, Profile
from agentic_sdlc.workspace import Workspace


def component_workdir(ws: Workspace, comp: Component) -> str:
    """Profile backend uses ``server/``; many monorepos place NestJS at ``apps/api/``."""
    wd = comp.workdir
    if wd != "server":
        return wd
    api_pkg = ws.root / "apps/api/package.json"
    if not api_pkg.is_file():
        return wd
    srv_pkg = ws.root / "server/package.json"
    if not srv_pkg.is_file():
        return "apps/api"
    try:
        if api_pkg.resolve() == srv_pkg.resolve():
            return "apps/api"
    except OSError:
        pass
    if (ws.root / "apps/api/src/main.ts").is_file():
        return "apps/api"
    return wd


def component_scope_prefixes(ws: Workspace, comp: Component, profile: Profile) -> list[str]:
    """Path prefixes allowed for DV3 scope (primary workdir plus monorepo aliases)."""
    prefixes: list[str] = []
    eff = component_workdir(ws, comp)
    if eff not in (".", ""):
        prefixes.append(eff.rstrip("/") + "/")
    if comp.workdir not in (".", "") and comp.workdir.rstrip("/") + "/" not in prefixes:
        prefixes.append(comp.workdir.rstrip("/") + "/")
    for extra in profile.guardrails.get("scope_also_allowed") or []:
        if not extra.endswith("/"):
            extra = extra.rstrip("/") + "/"
        if extra not in prefixes:
            prefixes.append(extra)
    return prefixes
