"""Agent registry: builds crewai Agents from config/agents.yaml + profile + model registry."""

from typing import Any, Callable

from crewai import Agent
from crewai.tools import BaseTool

from agentic_sdlc.registry.models import ModelRegistry
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.settings import load_config

# Given a tool name from agents.yaml, return a tool instance bound to the current run.
ToolResolver = Callable[[str], BaseTool]


class AgentRegistry:
    def __init__(
        self,
        definitions: dict[str, dict[str, Any]],
        models: ModelRegistry,
        profile: Profile,
        tool_resolver: ToolResolver | None = None,
    ):
        self._definitions = definitions
        self.models = models
        self.profile = profile
        self._tool_resolver = tool_resolver

    @classmethod
    def from_config(
        cls, profile: Profile, tool_resolver: ToolResolver | None = None,
        model_overrides: dict[str, Any] | None = None,
    ) -> "AgentRegistry":
        return cls(load_config("agents"), ModelRegistry.from_config(model_overrides), profile, tool_resolver)

    def keys(self) -> list[str]:
        return list(self._definitions)

    def definition(self, agent_key: str) -> dict[str, Any]:
        if agent_key not in self._definitions:
            raise KeyError(f"Unknown agent '{agent_key}'")
        merged = {**self._definitions[agent_key], **self.profile.agent_overrides.get(agent_key, {})}
        context = self.profile.context_for(agent_key)
        if context:
            merged["backstory"] = f"{merged['backstory'].strip()}\n\nProject conventions:\n{context}"
        return merged

    def build(self, agent_key: str, model: str | None = None) -> Agent:
        d = self.definition(agent_key)
        tool_names: list[str] = d.get("tools", [])
        if tool_names and self._tool_resolver is None:
            raise RuntimeError(f"Agent '{agent_key}' needs tools but no tool resolver was given")
        tools = [self._tool_resolver(n) for n in tool_names] if tool_names else []
        return Agent(
            role=d["role"],
            goal=d["goal"].strip(),
            backstory=d["backstory"].strip(),
            llm=self.models.build_llm(agent_key, model),
            tools=tools,
            allow_delegation=d.get("allow_delegation", False),
            max_iter=d.get("max_iter", 25),
            respect_context_window=True,
            inject_date=True,
            verbose=d.get("verbose", False),
        )
