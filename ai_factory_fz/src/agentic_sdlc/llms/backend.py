"""Chooses how Anthropic models are called, from environment variables.

  CLAUDE_CODE_ENABLE=true   anthropic/<model> runs through Claude Code (`claude -p`),
                            authenticated with CLAUDE_CODE_OAUTH_TOKEN (required).
  CLAUDE_CODE_ENABLE=false  anthropic/<model> calls the Claude API with ANTHROPIC_API_KEY
  (or unset)                (required).

Models of other providers (openai/..., gemini/...) are not affected. A model written as
claude-code/<model> in models.yaml always uses Claude Code.
"""

import os
from enum import Enum

ANTHROPIC_PREFIX = "anthropic/"
CLAUDE_CODE_PREFIX = "claude-code/"

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"", "0", "false", "no", "off"}


class Backend(str, Enum):
    CLAUDE_CODE = "claude_code"
    API = "api"


class CredentialsError(RuntimeError):
    """The selected backend is missing its credential."""


def selected_backend(env: dict[str, str] | None = None) -> Backend:
    env = os.environ if env is None else env
    raw = env.get("CLAUDE_CODE_ENABLE", "").strip().lower()
    if raw in _TRUE:
        return Backend.CLAUDE_CODE
    if raw in _FALSE:
        return Backend.API
    raise CredentialsError(f"CLAUDE_CODE_ENABLE must be true or false, got '{raw}'")


def route_model(model: str, backend: Backend) -> str:
    """Map anthropic/<model> onto Claude Code when that backend is selected."""
    if backend is Backend.CLAUDE_CODE and model.startswith(ANTHROPIC_PREFIX):
        return CLAUDE_CODE_PREFIX + model.removeprefix(ANTHROPIC_PREFIX)
    return model


def check_credentials(models: list[str], env: dict[str, str] | None = None) -> None:
    """Fail before any agent runs if a model's path has no credential."""
    env = os.environ if env is None else env
    if any(m.startswith(CLAUDE_CODE_PREFIX) for m in models) and not env.get("CLAUDE_CODE_OAUTH_TOKEN"):
        raise CredentialsError(
            "Claude Code path selected (CLAUDE_CODE_ENABLE=true) but CLAUDE_CODE_OAUTH_TOKEN is not set. "
            "Create one with `claude setup-token` and add it to .env, or set CLAUDE_CODE_ENABLE=false "
            "to use ANTHROPIC_API_KEY."
        )
    if any(m.startswith(ANTHROPIC_PREFIX) for m in models) and not env.get("ANTHROPIC_API_KEY"):
        raise CredentialsError(
            "Claude API path selected (CLAUDE_CODE_ENABLE is false or unset) but ANTHROPIC_API_KEY is not set. "
            "Add it to .env, or set CLAUDE_CODE_ENABLE=true with CLAUDE_CODE_OAUTH_TOKEN."
        )
