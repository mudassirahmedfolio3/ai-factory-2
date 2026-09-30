"""Deterministic project setup (no LLM): runs the profile's scaffold steps for a component."""

import shutil

from agentic_sdlc.registry.profiles import Component
from agentic_sdlc.tools.sandbox_exec import SandboxRunner
from agentic_sdlc.workspace import Workspace


class ScaffoldError(RuntimeError):
    pass


def required_runtimes(component: Component) -> list[str]:
    rts = [component.runtime] if component.runtime else []
    for step in component.scaffold:
        if step.run and (step.runtime or component.runtime) not in rts:
            rts.append(step.runtime or component.runtime)
    return [r for r in rts if r]


def scaffold(name: str, component: Component, workspace: Workspace, sandbox: SandboxRunner) -> list[str]:
    """Run each step unless its `creates` path exists. Returns a log of what ran."""
    log: list[str] = []
    for step in component.scaffold:
        if step.creates and workspace.resolve(step.creates).exists():
            log.append(f"skip (exists): {step.creates}")
            continue
        if step.copy_from and step.copy_to:
            dst = workspace.resolve(step.copy_to)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(workspace.resolve(step.copy_from), dst)
            log.append(f"copied {step.copy_from} -> {step.copy_to}")
            continue
        if not step.run:
            continue
        runtime = step.runtime or component.runtime
        if runtime is None:
            raise ScaffoldError(f"Scaffold step '{step.run}' for {name} has no runtime")
        result = sandbox.run_trusted(runtime, step.workdir, step.run)
        if not result.ok:
            raise ScaffoldError(f"Scaffold step failed for {name}: `{step.run}`\n{result.output[-3000:]}")
        log.append(f"ran: {step.run}")
    return log
