from __future__ import annotations

import asyncio
import json
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
from pydantic import BaseModel, Field
from config import AI_FACTORY_ROOT
from dotenv import load_dotenv
from run_manager import is_running, start_run
from sse_starlette.sse import EventSourceResponse

load_dotenv(AI_FACTORY_ROOT / ".env", override=True)

app = FastAPI(title="AI Factory Console API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
    import sys

    sys.path.insert(0, str(AI_FACTORY_ROOT / "src"))
    from ai_factory.complexity import list_profiles

    return list_profiles()


@app.get("/health")
def health() -> dict[str, str | bool]:
    import os

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    return {
        "status": "ok",
        "llm_provider": provider,
        "cursor_key_loaded": bool(os.getenv("CURSOR_API_KEY", "").strip()),
        "groq_key_loaded": bool(os.getenv("GROQ_API_KEY", "").strip()),
    }


@app.get("/runs")
def runs() -> list[dict[str, Any]]:
    return list_runs()


@app.get("/runs/current")
def current_run() -> dict[str, Any]:
    state = get_current_run_state()
    if not state:
        raise HTTPException(status_code=404, detail="No active or recent run state")
    return {**state, "is_live": state.get("status") == "running"}


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
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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


@app.get("/status")
def status() -> dict[str, Any]:
    state = get_current_run_state()
    return {
        "factory_running": is_running(),
        "current_run": state,
    }


async def _event_stream(run_id: str | None = None):
    last_state_ts = ""
    event_count = 0
    while True:
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
