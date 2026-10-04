"""Model registry: maps each agent to an LLM (plus fallbacks) from config/models.yaml."""

import os
from typing import Any

from crewai import LLM
from crewai.llms.base_llm import BaseLLM
from pydantic import BaseModel, Field

from agentic_sdlc.llms.backend import (
    CLAUDE_CODE_PREFIX,
    Backend,
    Provider,
    check_credentials,
    route_model,
    selected_backend,
    selected_provider,
)
from agentic_sdlc.llms.claude_code import ClaudeCodeLLM
from agentic_sdlc.llms.cursor_agent import CursorAgentLLM
from agentic_sdlc.settings import load_config


class ModelSpec(BaseModel):
    model: str
    fallbacks: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)

    def candidates(self) -> list[str]:
        """Primary model first, then fallbacks, without duplicates."""
        seen: list[str] = []
        for m in [self.model, *self.fallbacks]:
            if m not in seen:
                seen.append(m)
        return seen


class ModelRegistry:
    def __init__(self, config: dict[str, Any], backend: Backend | None = None):
        """`backend` defaults to the one chosen by CLAUDE_CODE_ENABLE."""
        self.backend = backend or selected_backend()
        self._defaults: dict[str, Any] = config.get("defaults", {})
        self._tiers: dict[str, dict[str, Any]] = config.get("tiers", {})
        self._agents: dict[str, Any] = config.get("agents", {})

    @classmethod
    def from_config(cls, agent_overrides: dict[str, Any] | None = None) -> "ModelRegistry":
        """`agent_overrides` (e.g. a pipeline's `models:` section) replace entries of models.yaml."""
        config = load_config("models")
        if agent_overrides:
            unknown = set(agent_overrides) - set(config.get("agents", {}))
            if unknown:
                raise KeyError(f"Model overrides for unknown agents: {sorted(unknown)}")
            config["agents"] = {**config.get("agents", {}), **agent_overrides}
        return cls(config)

    def spec_for(self, agent_key: str) -> ModelSpec:
        entry = self._agents.get(agent_key)
        if entry is None:
            raise KeyError(f"No model configured for agent '{agent_key}' in models.yaml")
        if isinstance(entry, str):
            if entry not in self._tiers:
                raise KeyError(f"Agent '{agent_key}' uses unknown tier '{entry}'")
            entry = self._tiers[entry]
        entry = dict(entry)
        model = entry.pop("model")
        fallbacks = entry.pop("fallbacks", [])
        return ModelSpec(
            model=route_model(model, self.backend),
            fallbacks=[route_model(m, self.backend) for m in fallbacks],
            params={**self._defaults, **entry},
        )

    def check_credentials(self) -> None:
        """Raise CredentialsError if any configured model's path has no credential."""
        check_credentials([m for key in self._agents for m in self.spec_for(key).candidates()])

    def build_llm(self, agent_key: str, model: str | None = None) -> BaseLLM:
        """Build the LLM for an agent. `model` picks one of its candidates (default: primary)."""
        spec = self.spec_for(agent_key)
        provider = selected_provider()
        timeout = int(spec.params.get("timeout", 600))

        if provider is Provider.CURSOR_CLI:
            per_agent = os.getenv(f"CURSOR_MODEL_{agent_key.upper()}", "").strip()
            model = per_agent or os.getenv("CURSOR_PROXY_MODEL", "auto")
            return CursorAgentLLM(
                model=model,
                api_key=os.getenv("CURSOR_API_KEY", "").strip() or None,
                working_dir=os.getenv("CURSOR_AGENT_CWD", os.getcwd()),
                timeout_seconds=int(os.getenv("CURSOR_AGENT_TIMEOUT", str(timeout))),
            )
        if provider is Provider.CURSOR_PROXY:
            return LLM(
                model=os.getenv("CURSOR_PROXY_MODEL", "auto"),
                custom_openai=True,
                base_url=os.getenv("CURSOR_PROXY_BASE_URL", "http://localhost:4646/v1"),
                api_key=os.getenv("CURSOR_API_KEY", "").strip(),
                timeout=timeout,
            )

        model = model or spec.model
        if model.startswith(CLAUDE_CODE_PREFIX):
            # Claude Code picks its own output limit; only timeout and effort apply.
            params = {k: v for k, v in spec.params.items() if k in ("timeout", "effort")}
            return ClaudeCodeLLM(model=model.removeprefix(CLAUDE_CODE_PREFIX), **params)
        params = {k: v for k, v in spec.params.items() if k != "effort"}
        return LLM(model=model, **params)
