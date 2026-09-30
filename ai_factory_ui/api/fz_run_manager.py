"""Run ai_factory_fz (agentic_sdlc) from the FastAPI console with UI-compatible state."""

from __future__ import annotations

import os
import sys
import threading
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

from config import AI_FACTORY_FZ_ROOT, RUN_STATE_PATH
from fz_bridge import (
    COMPLEXITY_MINUTES,
    archive_fz_run,
    log_fz_audit,
    publish_fz_run_state,
)


def _make_ui_flow(publish_ctx: dict[str, str]):
    """SDLCFlow subclass that publishes run state after every checkpoint."""
    from agentic_sdlc.flow import SDLCFlow

    class ConsoleSDLCFlow(SDLCFlow):
        def __init__(self, **data: Any):
            super().__init__(**data)
            self._publish_ctx = publish_ctx

        def _checkpoint(self, message: str) -> None:
            super()._checkpoint(message)
            publish_fz_run_state(
                self.state,
                project_name=self._publish_ctx["project_name"],
                complexity=self._publish_ctx["complexity"],
                checkpoint_msg=message,
            )

    return ConsoleSDLCFlow


def _ensure_fz_env() -> None:
    load_dotenv(AI_FACTORY_FZ_ROOT / ".env", override=True)
    os.environ["SDLC_HOME"] = str(AI_FACTORY_FZ_ROOT)
    os.environ.setdefault("SDLC_GATE_MODE", "auto")

    claude_code = os.getenv("CLAUDE_CODE_ENABLE", "false").strip().lower() == "true"
    if claude_code:
        if not os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "").strip():
            raise RuntimeError(
                "CLAUDE_CODE_OAUTH_TOKEN is missing in ai_factory_fz/.env — run `claude setup-token`."
            )
    elif not os.getenv("ANTHROPIC_API_KEY", "").strip():
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing in ai_factory_fz/.env — add your Claude API key."
        )


def _resolve_brief(client_brief: str, project_name: str) -> str:
    if client_brief.strip():
        title = project_name.strip() or "App"
        return f"# {title}\n\n{client_brief.strip()}"
    default = AI_FACTORY_FZ_ROOT / "briefs" / "ecommerce_mvp.md"
    if default.is_file():
        return default.read_text(encoding="utf-8")
    return f"Build a Flutter + NestJS ecommerce mobile app named {project_name}."


def _resolve_milestones(complexity: str) -> str | None:
    if complexity == "basic":
        return "M1"
    if complexity == "basic_plus":
        return "M1,M2"
    return None


def _run_fz_flow(
    *,
    run_id: str,
    project_name: str,
    client_brief: str,
    complexity: str,
) -> None:
    original_cwd = os.getcwd()
    publish_ctx = {"project_name": project_name, "complexity": complexity}
    try:
        os.chdir(AI_FACTORY_FZ_ROOT)
        fz_src = AI_FACTORY_FZ_ROOT / "src"
        if str(fz_src) not in sys.path:
            sys.path.insert(0, str(fz_src))

        for mod in list(sys.modules):
            if mod == "agentic_sdlc" or mod.startswith("agentic_sdlc."):
                del sys.modules[mod]

        _ensure_fz_env()

        milestones = _resolve_milestones(complexity)
        if milestones:
            os.environ["SDLC_BUILD_MILESTONES"] = milestones
        else:
            os.environ.pop("SDLC_BUILD_MILESTONES", None)

        brief = _resolve_brief(client_brief, project_name)
        profile = "flutter_nestjs_ecommerce"
        pipeline = "pipeline.ui"

        from agentic_sdlc.state import ProjectState

        seed = ProjectState(
            run_id=run_id,
            profile=profile,
            pipeline=pipeline,
            brief=brief,
            status="running",
        )
        publish_fz_run_state(seed, project_name=project_name, complexity=complexity, checkpoint_msg="Queued")
        log_fz_audit(run_id, "run_started", "started", "console", {"complexity": complexity, "pipeline": pipeline})

        FlowClass = _make_ui_flow(publish_ctx)
        flow = FlowClass()
        flow.kickoff(inputs={"run_id": run_id, "profile": profile, "brief": brief, "pipeline": pipeline})

        publish_fz_run_state(flow.state, project_name=project_name, complexity=complexity, checkpoint_msg="Finished")
        archive_fz_run(flow.state, project_name, complexity)
        log_fz_audit(
            run_id,
            "run_finished",
            flow.state.status,
            "console",
            {"stop_reason": flow.state.stop_reason or None},
        )
    except Exception as exc:
        import run_manager as rm

        rm._write_failed_state(str(exc))
        log_fz_audit(run_id, "run_failed", "failed", "console", {"error": str(exc)})
        raise
    finally:
        os.chdir(original_cwd)


def start_fz_run(
    project_name: str = "ecommerce-flutter-app",
    client_brief: str = "",
    complexity: str = "standard",
    max_releases: int | None = None,  # noqa: ARG001 — kept for API parity
    autonomy_level: str = "L2",  # noqa: ARG001
    deploy_environment: str = "staging",  # noqa: ARG001
) -> dict[str, Any]:
    import run_manager as rm

    with rm._lock:
        rm._reconcile_stale_run()
        if rm.is_running():
            run_id = (rm._read_run_state() or {}).get("run_id", "")
            raise RuntimeError(f"RUN_IN_PROGRESS:{run_id}")

        _ensure_fz_env()

        run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        rm._active_thread = threading.Thread(
            target=_run_fz_flow,
            kwargs={
                "run_id": run_id,
                "project_name": project_name,
                "client_brief": client_brief,
                "complexity": complexity,
            },
            name=f"ai-factory-fz-{run_id}",
            daemon=True,
        )
        rm._active_thread.start()

        return {
            "run_id": run_id,
            "status": "started",
            "project_name": project_name,
            "complexity": complexity,
            "estimated_minutes": COMPLEXITY_MINUTES.get(complexity, 90),
            "factory_engine": "fz",
        }
