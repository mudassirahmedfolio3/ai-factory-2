"""Maps tool names used in config/agents.yaml to tool instances bound to one run."""

from typing import Callable

from crewai.tools import BaseTool

from agentic_sdlc.tools.sandbox_exec import SandboxExecTool, SandboxRunner
from agentic_sdlc.tools.workspace_fs import ListDirTool, ReadFileTool, WriteFileTool
from agentic_sdlc.workspace import Workspace


def build_tool_resolver(workspace: Workspace, runner: SandboxRunner) -> Callable[[str], BaseTool]:
    factories: dict[str, Callable[[], BaseTool]] = {
        "fs_read": lambda: ReadFileTool(workspace),
        "fs_write": lambda: WriteFileTool(workspace),
        "fs_list": lambda: ListDirTool(workspace),
        "sandbox_exec": lambda: SandboxExecTool(runner),
    }

    def resolve(name: str) -> BaseTool:
        if name not in factories:
            raise KeyError(f"Unknown tool '{name}'. Known tools: {sorted(factories)}")
        return factories[name]()

    return resolve
