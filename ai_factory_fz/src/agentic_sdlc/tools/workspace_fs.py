"""File tools for agents. Every path is resolved inside the run workspace only."""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from agentic_sdlc.workspace import PathEscapeError, Workspace

MAX_READ_CHARS = 60_000
MAX_LIST_ENTRIES = 500
_SKIP_DIRS = {".git", "node_modules", ".dart_tool", "build", ".gradle"}


class _WorkspaceTool(BaseTool):
    _ws: Workspace = PrivateAttr()

    def __init__(self, workspace: Workspace, **kwargs):
        super().__init__(**kwargs)
        self._ws = workspace


class PathArgs(BaseModel):
    path: str = Field(description="Path relative to the run workspace, e.g. server/src/main.ts")


class ReadArgs(PathArgs):
    start_line: int = Field(default=1, ge=1, description="First line to return (1-based)")
    max_lines: int | None = Field(default=None, ge=1, description="Number of lines to return; omit for the rest")


class WriteArgs(PathArgs):
    content: str = Field(description="Full new content of the file")


class ReadFileTool(_WorkspaceTool):
    name: str = "fs_read"
    description: str = (
        "Read a text file from the project workspace. For large files, read a window with "
        "start_line and max_lines; the reply says how many lines the file has."
    )
    args_schema: type[BaseModel] = ReadArgs

    def _run(self, path: str, start_line: int = 1, max_lines: int | None = None) -> str:
        try:
            p = self._ws.resolve(path)
        except PathEscapeError as e:
            return f"ERROR: {e}"
        if not p.is_file():
            return f"ERROR: {path} does not exist or is not a file"
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        window = lines[start_line - 1 : (start_line - 1 + max_lines) if max_lines else None]
        text = "".join(window)
        if len(text) > MAX_READ_CHARS:
            text = text[:MAX_READ_CHARS] + "\n... [truncated; read a smaller window with start_line/max_lines]"
        if start_line > 1 or max_lines or len(window) < len(lines):
            end = start_line - 1 + len(window)
            text = f"[lines {start_line}-{end} of {len(lines)}]\n" + text
        return text


class WriteFileTool(_WorkspaceTool):
    name: str = "fs_write"
    description: str = "Create or overwrite a text file in the project workspace."
    args_schema: type[BaseModel] = WriteArgs

    def _run(self, path: str, content: str) -> str:
        try:
            self._ws.write_text(path, content)
        except PathEscapeError as e:
            return f"ERROR: {e}"
        return f"Wrote {len(content)} chars to {path}"


class ListDirTool(_WorkspaceTool):
    name: str = "fs_list"
    description: str = "List files under a directory of the project workspace (recursive)."
    args_schema: type[BaseModel] = PathArgs

    def _run(self, path: str = ".") -> str:
        try:
            base = self._ws.resolve(path)
        except PathEscapeError as e:
            return f"ERROR: {e}"
        if not base.is_dir():
            return f"ERROR: {path} is not a directory"
        entries = []
        for p in sorted(base.rglob("*")):
            rel = p.relative_to(self._ws.root)
            if _SKIP_DIRS.intersection(rel.parts) or not p.is_file():
                continue
            entries.append(str(rel))
            if len(entries) >= MAX_LIST_ENTRIES:
                entries.append("... [more files not shown]")
                break
        return "\n".join(entries) or "(empty)"
