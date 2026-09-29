#!/usr/bin/env python
"""Entry points.

  uv run kickoff [--brief briefs/ecommerce_mvp.md] [--pipeline pipeline] [--profile ...] [--run-id ID]
  uv run resume <run_id> [--milestones M1,M2]
  uv run plot
  crewai run            (same as kickoff with defaults)
"""

import argparse
import json
import os
import sys
from pathlib import Path

from agentic_sdlc.flow import SDLCFlow
from agentic_sdlc.settings import CONFIG_DIR, PROJECT_ROOT, RUNS_DIR
from agentic_sdlc.workspace import Workspace, new_run_id

DEFAULT_BRIEF = PROJECT_ROOT / "briefs" / "ecommerce_mvp.md"
DEFAULT_PROFILE = "flutter_nestjs_ecommerce"


def _print_result(flow: SDLCFlow) -> None:
    s = flow.state
    print(f"\nRun {s.run_id}: {s.status}" + (f" ({s.stop_reason})" if s.stop_reason else ""))
    print(f"Artifacts: {RUNS_DIR / s.run_id / 'docs'}")
    print(f"Summary:   {RUNS_DIR / s.run_id / 'reports' / 'run_summary.md'}")


def start_run(brief_path: Path, profile: str, run_id: str | None = None, pipeline: str = "pipeline") -> SDLCFlow:
    brief = brief_path.read_text(encoding="utf-8")
    if not (CONFIG_DIR / f"{pipeline}.yaml").exists():
        raise SystemExit(f"No pipeline config at {CONFIG_DIR / (pipeline + '.yaml')}")
    run_id = run_id or new_run_id(brief_path.stem)
    flow = SDLCFlow()
    flow.kickoff(inputs={"run_id": run_id, "profile": profile, "brief": brief, "pipeline": pipeline})
    _print_result(flow)
    return flow


def resume_run(run_id: str) -> SDLCFlow:
    ws = Workspace.open(run_id)
    flow = SDLCFlow(restore_json=ws.load_state_json())
    flow.kickoff(inputs={"run_id": run_id})
    _print_result(flow)
    return flow


def kickoff() -> None:
    parser = argparse.ArgumentParser(description="Start a new SDLC run")
    parser.add_argument("--brief", type=Path, default=DEFAULT_BRIEF)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--run-id")
    parser.add_argument("--pipeline", default="pipeline", help="Pipeline config name in config/, e.g. pipeline.demo")
    parser.add_argument("--milestones", help="Build only these milestones, e.g. M1,M2")
    args, _ = parser.parse_known_args()
    _apply_milestones(args.milestones)
    start_run(args.brief, args.profile, args.run_id, args.pipeline)


def resume() -> None:
    parser = argparse.ArgumentParser(description="Resume a stopped or interrupted SDLC run")
    parser.add_argument("run_id")
    parser.add_argument("--milestones", help="Build only these milestones, e.g. M1,M2")
    args = parser.parse_args()
    _apply_milestones(args.milestones)
    resume_run(args.run_id)


def _apply_milestones(milestones: str | None) -> None:
    if milestones:
        os.environ["SDLC_BUILD_MILESTONES"] = milestones


def setup_android() -> None:
    """One-time: install the Android SDK + emulator for this system (you accept the licence)."""
    from agentic_sdlc.registry.profiles import Profile
    from agentic_sdlc.release.device import AndroidToolchain

    parser = argparse.ArgumentParser(description="Install the Android emulator used for device tests")
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    profile = Profile.load(parser.parse_args().profile)
    if profile.device is None:
        raise SystemExit(f"Profile '{profile.name}' has no device section")
    AndroidToolchain(profile.device).install()


def showcase() -> None:
    """Start staging and open the app in an Android emulator window, for a demo.

      uv run showcase <run_id>          start (staging + emulator + app)
      uv run showcase <run_id> --stop   stop both
    """
    from agentic_sdlc.registry.profiles import Profile
    from agentic_sdlc.release.device import AndroidToolchain, DeviceError, Emulator
    from agentic_sdlc.release.staging import Staging, StagingError
    from agentic_sdlc.settings import load_config
    from agentic_sdlc.state import ProjectState
    from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRunner, sandbox_mode

    parser = argparse.ArgumentParser(description="Show a run's app in the Android emulator")
    parser.add_argument("run_id")
    parser.add_argument("--stop", action="store_true")
    args = parser.parse_args()

    ws = Workspace.open(args.run_id)
    state = ProjectState.model_validate_json(ws.load_state_json())
    profile = Profile.load(state.profile)
    pipeline = load_config(state.pipeline)
    if profile.device is None:
        raise SystemExit(f"Profile '{profile.name}' has no device section")
    mode = sandbox_mode((pipeline.get("build") or {}).get("sandbox", "docker"))
    if mode is not SandboxMode.DOCKER:
        raise SystemExit("showcase needs Docker (staging runs with docker compose)")
    sandbox = SandboxRunner(ws, profile.sandbox, mode)
    port = (pipeline.get("release") or {}).get("staging_port", 3100)
    staging = Staging(ws, profile, sandbox, port=port, startup_timeout_s=180)
    dev = profile.device
    app = profile.components[dev.app_component]
    emulator = Emulator(AndroidToolchain(dev), sandbox, ws, runtime=app.runtime, boot_timeout_s=420)
    staging.extra_env = {k: v.format(host=dev.host_alias, port=port) for k, v in dev.asset_env.items()}

    if args.stop:
        emulator.stop()
        staging.stop()
        print("Stopped the emulator and staging.")
        return

    api_base = f"http://{dev.host_alias}:{port}{profile.release.api_prefix}"
    try:
        print(f"Starting staging on http://localhost:{port} ...", flush=True)
        staging.start()
        print("Starting the Android emulator (a window will open) ...", flush=True)
        emulator.start(window=True)
    except (StagingError, DeviceError) as e:
        raise SystemExit(str(e))
    print(f"Building the app for the device (API {api_base}) ...", flush=True)
    build = emulator.run(dev.build_command.format(api_base=api_base, serial=emulator.serial), app.workdir,
                         timeout_s=dev.build_timeout_s)
    if not build.ok:
        raise SystemExit(f"App build failed:\n{build.output[-3000:]}")
    if not emulator.install(dev.apk_path, app.workdir, dev.app_id).ok:
        raise SystemExit("Installing the app on the emulator failed")
    emulator.launch(dev.app_id)
    print(f"\nThe app is running in the emulator window, against staging at http://localhost:{port}.")
    print(f"Stop everything with:  uv run showcase {args.run_id} --stop")


def plot() -> None:
    SDLCFlow().plot("sdlc_flow")


def run_with_trigger() -> None:
    """Start a run from a JSON payload: {"brief": "...", "profile": "...", "run_id": "..."}."""
    if len(sys.argv) < 2:
        raise SystemExit("Provide a JSON payload as the first argument")
    payload = json.loads(sys.argv[1])
    run_id = payload.get("run_id") or new_run_id("trigger")
    flow = SDLCFlow()
    flow.kickoff(inputs={"run_id": run_id, "profile": payload.get("profile", DEFAULT_PROFILE), "brief": payload["brief"]})
    _print_result(flow)


if __name__ == "__main__":
    kickoff()
