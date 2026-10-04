"""Monorepo workdir resolution (server/ vs apps/api/)."""

from pathlib import Path

from agentic_sdlc.registry.profiles import Component, Profile
from agentic_sdlc.workspace import Workspace
from agentic_sdlc.workspace_layout import component_scope_prefixes, component_workdir


def test_component_workdir_prefers_apps_api_when_both_exist(tmp_path: Path) -> None:
    api = tmp_path / "apps" / "api"
    api.mkdir(parents=True)
    (api / "package.json").write_text("{}", encoding="utf-8")
    (api / "src").mkdir()
    (api / "src" / "main.ts").write_text("// api", encoding="utf-8")
    srv = tmp_path / "server"
    srv.mkdir()
    (srv / "package.json").write_text("{}", encoding="utf-8")

    ws = Workspace(tmp_path)
    comp = Component(agent="backend_developer", workdir="server", runtime="node")
    assert component_workdir(ws, comp) == "apps/api"
    prefixes = component_scope_prefixes(ws, comp, Profile.load("flutter_nestjs_ecommerce"))
    assert "apps/api/" in prefixes
    assert "server/" in prefixes
