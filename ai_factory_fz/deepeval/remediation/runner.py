"""The only module that touches the pipeline: builds a TaskRunner for the Project Manager.

Needs the ai_factory_fz environment (CrewAI + agentic_sdlc). Run from ai_factory_fz: `uv run python deepeval/remediate.py ...`.
The two remediation prompts live in remediation/prompts/tasks.yaml and are merged in memory, so the pipeline's own
config/tasks.yaml is never modified."""

import json
from pathlib import Path

import yaml

DEFAULT_PROFILE = "flutter_nestjs_ecommerce"
DEFAULT_PIPELINE = "pipeline"
PROMPTS = Path(__file__).resolve().parent / "prompts" / "tasks.yaml"


def load_prompts() -> dict:
    return yaml.safe_load(PROMPTS.read_text(encoding="utf-8"))


def build_runner(run_dir: Path):
    """Uses the run's own profile and pipeline when it has a state.json, else the defaults."""
    try:
        from agentic_sdlc.crews.base import TaskRunner
        from agentic_sdlc.registry.agents import AgentRegistry
        from agentic_sdlc.registry.profiles import Profile
        from agentic_sdlc.settings import load_config
    except ImportError as e:   # run from the deepeval environment instead of the pipeline's
        raise SystemExit("The Project Manager needs the pipeline environment: run this from ai_factory_fz with "
                         f"`uv run python deepeval/remediate.py ...` ({e})")

    profile, pipeline = DEFAULT_PROFILE, DEFAULT_PIPELINE
    state = Path(run_dir) / "state.json"
    if state.is_file():
        data = json.loads(state.read_text(encoding="utf-8"))
        profile, pipeline = data.get("profile") or profile, data.get("pipeline") or pipeline
    agents = AgentRegistry.from_config(Profile.load(profile), None, load_config(pipeline).get("models"))
    return TaskRunner(agents, tasks={**load_config("tasks"), **load_prompts()})
