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


def _machine(profile_name: str, pipeline_name: str):
    from agentic_sdlc.registry.models import ModelRegistry
    from agentic_sdlc.registry.profiles import Profile
    from agentic_sdlc.settings import load_config
    from agentic_sdlc.tools.sandbox_exec import SandboxRunner, sandbox_mode

    profile = Profile.load(profile_name)
    pipeline = load_config(pipeline_name)
    probe = Workspace.create(".preflight")   # scratch workspace, only used to run image checks
    sandbox = SandboxRunner(probe, profile.sandbox, sandbox_mode((pipeline.get("build") or {}).get("sandbox", "docker")))
    return profile, pipeline, sandbox, ModelRegistry.from_config(pipeline.get("models"))


def preflight_cmd() -> None:
    """Check this machine for a pipeline without starting a run."""
    from agentic_sdlc import preflight

    parser = argparse.ArgumentParser(description="Check the machine is ready for a pipeline")
    parser.add_argument("--pipeline", default="pipeline")
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    args = parser.parse_args()
    profile, pipeline, sandbox, models = _machine(args.profile, args.pipeline)
    problems = preflight.check(pipeline=pipeline, profile=profile, sandbox=sandbox, models=models)
    print(preflight.report(problems))
    raise SystemExit(1 if problems else 0)


def setup() -> None:
    """One-time machine setup. Everything is automatic except what needs you: your sudo password
    (Docker install / docker group) and accepting the Android SDK licence."""
    import getpass
    import shutil
    import subprocess

    from agentic_sdlc import preflight
    from agentic_sdlc.build.scaffold import required_runtimes
    from agentic_sdlc.release.device import AndroidToolchain
    from agentic_sdlc.tools import docker_access

    parser = argparse.ArgumentParser(description="Prepare this machine for the SDLC pipeline")
    parser.add_argument("--pipeline", default="pipeline.demo")
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    args = parser.parse_args()
    user = getpass.getuser()

    def sudo(cmd: list[str], why: str) -> None:
        print(f"\n{why}\n  sudo {' '.join(cmd)}\n(you will be asked for your password)", flush=True)
        subprocess.run(["sudo", *cmd], check=True)

    print("1/4 Docker", flush=True)
    if not shutil.which("docker"):
        if not shutil.which("apt-get"):
            raise SystemExit("Docker is not installed and this is not an apt-based system: "
                             "install Docker (https://docs.docker.com/engine/install/), then run setup again.")
        sudo(["apt-get", "install", "-y", "docker.io", "docker-compose-v2"], "Installing Docker:")
        sudo(["systemctl", "enable", "--now", "docker"], "Starting the Docker service:")
    if not docker_access.in_docker_group(user):
        sudo(["usermod", "-aG", "docker", user], f"Adding '{user}' to the docker group:")
    docker_access.access_mode.cache_clear()
    mode = docker_access.access_mode()
    print(f"   Docker access: {mode}" + (" (no need to log out: the pipeline uses sg docker)" if mode == "sg" else ""))

    profile, pipeline, sandbox, models = _machine(args.profile, args.pipeline)
    print("\n2/4 Toolchain images", flush=True)
    runtimes = sorted({rt for c in profile.components.values() for rt in required_runtimes(c)})
    for rt, err in sandbox.prepare(runtimes).items():
        print(f"   {rt}: {err}")

    print("\n3/4 Android emulator", flush=True)
    if profile.device and ((pipeline.get("release") or {}).get("device") or {}).get("enabled"):
        tc = AndroidToolchain(profile.device)
        if tc.not_ready_reason():
            tc.install()
        else:
            print("   ready")
    else:
        print("   not needed by this pipeline")

    print("\n4/4 Claude access", flush=True)
    problems = preflight.check(profile=profile, pipeline=pipeline, sandbox=sandbox, models=models)
    if any("CLAUDE_CODE_OAUTH_TOKEN" in p or "ANTHROPIC_API_KEY" in p for p in problems):
        print("   Create a token with `claude setup-token` and put it in .env as CLAUDE_CODE_OAUTH_TOKEN "
              "(with CLAUDE_CODE_ENABLE=true). This is your account's secret, so you add it yourself.")
    print("\n" + preflight.report(problems))


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
