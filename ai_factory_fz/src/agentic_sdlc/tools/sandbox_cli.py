"""Command-line entry used by the wrapper scripts that ClaudeCodeWorker installs in Docker mode.

A coding agent runs e.g. `flutter test` in its Bash tool. In Docker mode, `flutter` on its PATH is a
wrapper that calls this module, which runs the command in the runtime's container through the
same SandboxRunner (and allow-list) as everything else, from the agent's current directory.

  python -m agentic_sdlc.tools.sandbox_cli --workspace DIR --profile NAME --runtime RT -- CMD...
"""

import argparse
import os
import shlex
import sys
from pathlib import Path

from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRejected, SandboxRunner
from agentic_sdlc.workspace import PathEscapeError, Workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = [c for c in args.command if c != "--"] if args.command[:1] == ["--"] else args.command

    ws = Workspace(Path(args.workspace))
    runner = SandboxRunner(ws, Profile.load(args.profile).sandbox, SandboxMode.DOCKER)
    try:
        workdir = str(Path(os.getcwd()).resolve().relative_to(ws.root)) or "."
    except ValueError:
        print("Commands must run inside the project workspace", file=sys.stderr)
        return 2
    try:
        result = runner.run(args.runtime, workdir, shlex.join(command))
    except (SandboxRejected, PathEscapeError) as e:
        print(f"REJECTED: {e}", file=sys.stderr)
        return 126
    sys.stdout.write(result.output)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
