"""Preflight: check the machine before a run spends any tokens.

Checks only what the enabled phases need: Claude/model credentials; Docker access and the toolchain
images (pulled here if missing) for build/release in docker mode; installed toolchains in local
mode; a staging database in local mode; the Android emulator when device checks are enabled.
Returns the problems that would stop the run, each with its fix; empty means ready.
"""

import os
from typing import Any

from agentic_sdlc.build.scaffold import required_runtimes
from agentic_sdlc.llms.backend import CredentialsError
from agentic_sdlc.registry.models import ModelRegistry
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.release.device import AndroidToolchain
from agentic_sdlc.tools import docker_access
from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRunner


def check(pipeline: dict[str, Any], profile: Profile, sandbox: SandboxRunner, models: ModelRegistry) -> list[str]:
    phases = pipeline.get("phases", {}) or {}
    build, release = phases.get("build", False), phases.get("release", False)
    release_cfg = pipeline.get("release", {}) or {}
    problems: list[str] = []

    try:
        models.check_credentials()
    except CredentialsError as e:
        problems.append(str(e))

    if build or release:
        runtimes = sorted({rt for c in profile.components.values() for rt in required_runtimes(c)})
        if sandbox.mode is SandboxMode.DOCKER:
            docker_problem = docker_access.problem()
            if docker_problem:
                problems.append(docker_problem)
            else:
                problems += [f"Toolchain image for '{rt}' is not available: {err}"
                             for rt, err in sandbox.prepare(runtimes).items()]
        else:
            problems += [f"Toolchain '{rt}': {reason}" for rt in runtimes
                         if (reason := sandbox.unavailable_reason(rt))]
            if release and not os.environ.get("SDLC_STAGING_DATABASE_URL"):
                problems.append("Local staging needs SDLC_STAGING_DATABASE_URL in .env (an empty PostgreSQL "
                                "database), or use build.sandbox: docker")

    if release and (release_cfg.get("device") or {}).get("enabled") and profile.device:
        reason = AndroidToolchain(profile.device).not_ready_reason()
        if reason:
            problems.append(reason.replace("`uv run setup-android` once", "`uv run setup` once"))
    return problems


def report(problems: list[str]) -> str:
    if not problems:
        return "Preflight: ready."
    return "Preflight found problems to fix before this run can work:\n" + "\n".join(f"- {p}" for p in problems)
