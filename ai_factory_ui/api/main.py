from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from artifact_reader import (
    get_current_run_state,
    get_run,
    list_runs,
    read_artifact,
    read_audit_events,
)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from config import AI_FACTORY_FZ_ROOT, AI_FACTORY_ROOT, FACTORY_ENGINE
from dotenv import load_dotenv
from run_manager import is_running, start_run
from sse_starlette.sse import EventSourceResponse

if FACTORY_ENGINE == "fz":
    load_dotenv(AI_FACTORY_FZ_ROOT / ".env", override=True)
    load_dotenv(AI_FACTORY_ROOT / ".env", override=False)
else:
    load_dotenv(AI_FACTORY_ROOT / ".env", override=True)

app = FastAPI(title="AI Factory Console API", version="0.1.0")


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if raw.strip():
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartRunRequest(BaseModel):
    project_name: str = "ecommerce-flutter-app"
    client_brief: str = ""
    complexity: str = Field(default="standard", pattern="^(basic|basic_plus|standard|full)$")
    max_releases: int | None = Field(default=None, ge=1, le=10)
    autonomy_level: str = "L2"
    deploy_environment: str = "staging"


class EmulatorStartRequest(BaseModel):
    device_id: str | None = None


@app.get("/briefs/random")
def random_brief() -> dict[str, str]:
    import sys

    sys.path.insert(0, str(AI_FACTORY_ROOT / "src"))
    from ai_factory.brief_generator import fetch_random_ecommerce_brief

    brief = fetch_random_ecommerce_brief()
    return {
        "project_name": brief.project_name,
        "client_brief": brief.client_brief,
        "niche": brief.niche,
        "source": brief.source,
    }


@app.get("/complexity-options")
def complexity_options() -> list[dict[str, object]]:
    if FACTORY_ENGINE == "fz":
        from fz_bridge import COMPLEXITY_MINUTES

        return [
            {
                "id": key,
                "label": key.replace("_", " ").title(),
                "estimated_minutes": minutes,
                "max_releases": 1,
            }
            for key, minutes in COMPLEXITY_MINUTES.items()
        ]

    import sys

    sys.path.insert(0, str(AI_FACTORY_ROOT / "src"))
    from ai_factory.complexity import list_profiles

    return list_profiles()


@app.get("/health")
def health() -> dict[str, Any]:
    import os

    payload: dict[str, Any] = {
        "status": "ok",
        "factory_engine": FACTORY_ENGINE,
    }
    if FACTORY_ENGINE == "fz":
        from fz_docker import docker_status

        provider = os.getenv("LLM_PROVIDER", "cursor_cli").strip().lower() or "cursor_cli"
        claude_code = os.getenv("CLAUDE_CODE_ENABLE", "false").strip().lower() == "true"
        payload["llm_provider"] = provider
        payload["claude_code_enabled"] = claude_code
        payload["anthropic_key_loaded"] = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
        payload["claude_oauth_loaded"] = bool(os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "").strip())
        payload["cursor_key_loaded"] = bool(os.getenv("CURSOR_API_KEY", "").strip())
        payload["docker"] = docker_status()
    else:
        provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        payload["llm_provider"] = provider
        payload["cursor_key_loaded"] = bool(os.getenv("CURSOR_API_KEY", "").strip())
        payload["groq_key_loaded"] = bool(os.getenv("GROQ_API_KEY", "").strip())
    return payload


@app.get("/runs")
def runs() -> list[dict[str, Any]]:
    return list_runs()


@app.get("/runs/current")
def current_run() -> dict[str, Any]:
    from run_manager import is_running, reconcile_run_state

    reconcile_run_state()
    state = get_current_run_state()
    if not state:
        raise HTTPException(status_code=404, detail="No active or recent run state")
    return {**state, "is_live": state.get("status") == "running" and is_running()}


@app.get("/runs/{run_id}")
def run_detail(run_id: str) -> dict[str, Any]:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@app.post("/runs")
def create_run(body: StartRunRequest) -> dict[str, Any]:
    try:
        return start_run(
            project_name=body.project_name,
            client_brief=body.client_brief,
            complexity=body.complexity,
            max_releases=body.max_releases,
            autonomy_level=body.autonomy_level,
            deploy_environment=body.deploy_environment,
        )
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("RUN_IN_PROGRESS:"):
            run_id = message.split(":", 1)[1] or None
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "A factory run is already in progress",
                    "run_id": run_id,
                },
            ) from exc
        raise HTTPException(status_code=409, detail=message) from exc


PREVIEWS_ROOT = AI_FACTORY_ROOT / "apps"


@app.get("/runs/{run_id}/preview/{path:path}")
def run_preview(run_id: str, path: str):
    """Serve browser preview HTML (legacy ai_factory) or fz design docs when available."""
    preview_dir = (PREVIEWS_ROOT / run_id).resolve()
    if not preview_dir.is_dir() and FACTORY_ENGINE == "fz":
        from config import FZ_RUNS_DIR

        fz_docs = (FZ_RUNS_DIR / run_id / "docs").resolve()
        if fz_docs.is_dir():
            preview_dir = fz_docs
    if not preview_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Preview for run {run_id} not found")
    file_path = (preview_dir / path).resolve()
    try:
        file_path.relative_to(preview_dir)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Invalid preview path") from exc
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Preview file {path} not found")
    return FileResponse(file_path)


@app.get("/runs/{run_id}/audit")
def run_audit(run_id: str) -> list[dict[str, Any]]:
    """Governance audit trail for project journey (developer, QA, fixes)."""
    events = read_audit_events(run_id=run_id)
    return events


@app.get("/runs/{run_id}/artifacts/{path:path}")
def artifact(run_id: str, path: str) -> dict[str, str]:
    content = read_artifact(path, run_id=run_id)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Artifact {path} not found")
    return {"path": path, "content": content}


@app.get("/artifacts/{path:path}")
def live_artifact(path: str) -> dict[str, str]:
    content = read_artifact(path)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Artifact {path} not found")
    return {"path": path, "content": content}


@app.get("/runs/{run_id}/emulator/devices")
def emulator_devices(run_id: str) -> dict[str, Any]:
    _ = run_id
    from fz_emulator import list_devices, list_emulators

    return {"devices": list_devices(), "emulators": list_emulators()}


@app.get("/runs/{run_id}/emulator/status")
def emulator_status(run_id: str) -> dict[str, Any]:
    from fz_emulator import get_status

    return get_status(run_id)


@app.post("/runs/{run_id}/emulator/start")
def emulator_start(run_id: str, body: EmulatorStartRequest | None = None) -> dict[str, Any]:
    from fz_emulator import flutter_project_ready, start as start_emulator

    run = get_run(run_id)
    # Allow launching when Flutter sources exist under apps/{id}/flutter even if
    # the run is not in the archived snapshot index.
    if not run and not flutter_project_ready(run_id):
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    try:
        return start_emulator(run_id, device_id=body.device_id if body else None, run_state=run)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/runs/{run_id}/emulator/stop")
def emulator_stop(run_id: str) -> dict[str, Any]:
    from fz_emulator import stop as stop_emulator

    return stop_emulator(run_id)


@app.get("/status")
def status() -> dict[str, Any]:
    state = get_current_run_state()
    return {
        "factory_running": is_running(),
        "current_run": state,
    }


async def _event_stream(run_id: str | None = None):
    from run_manager import reconcile_run_state

    last_state_ts = ""
    event_count = 0
    while True:
        reconcile_run_state()
        state = get_current_run_state()
        if run_id and state and state.get("run_id") != run_id:
            archived = get_run(run_id)
            if archived:
                state = archived

        if state:
            ts = state.get("updated_at", "")
            if ts != last_state_ts:
                last_state_ts = ts
                yield {"event": "state", "data": json.dumps(state)}

        events = read_audit_events(run_id=run_id, since=event_count)
        for entry in events:
            event_count += 1
            yield {"event": "audit", "data": json.dumps(entry)}

        live = state and state.get("status") == "running"
        if not live and event_count > 0:
            yield {"event": "done", "data": json.dumps({"status": "idle"})}
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)


@app.get("/runs/current/events")
async def current_events():
    state = get_current_run_state()
    run_id = state.get("run_id") if state else None
    return EventSourceResponse(_event_stream(run_id))


@app.get("/runs/{run_id}/events")
async def run_events(run_id: str):
    return EventSourceResponse(_event_stream(run_id))
