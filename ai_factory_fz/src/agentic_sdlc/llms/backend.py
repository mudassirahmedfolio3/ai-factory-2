"""Chooses how LLMs are called, from environment variables.

LLM_PROVIDER (development vs demo):
  cursor_cli    — Cursor subscription via local `agent` CLI + CURSOR_API_KEY (default for dev)
  cursor_proxy  — Cursor via local OpenAI-compatible proxy (CURSOR_PROXY_BASE_URL)
  anthropic     — Claude via CLAUDE_CODE_ENABLE switch (use on demo day)

When LLM_PROVIDER=anthropic:
  CLAUDE_CODE_ENABLE=true   anthropic/<model> runs through Claude Code (`claude -p`),
                            authenticated with CLAUDE_CODE_OAUTH_TOKEN (required).
  CLAUDE_CODE_ENABLE=false  anthropic/<model> calls the Claude API with ANTHROPIC_API_KEY
  (or unset)                (required).

Models of other providers (openai/..., gemini/...) are not affected by the Claude switch.
A model written as claude-code/<model> in models.yaml always uses Claude Code.
"""

import os
from enum import Enum

ANTHROPIC_PREFIX = "anthropic/"
CLAUDE_CODE_PREFIX = "claude-code/"

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"", "0", "false", "no", "off"}


class Provider(str, Enum):
    CURSOR_CLI = "cursor_cli"
    CURSOR_PROXY = "cursor_proxy"
    ANTHROPIC = "anthropic"


class Backend(str, Enum):
    CLAUDE_CODE = "claude_code"
    API = "api"


class CredentialsError(RuntimeError):
    """The selected backend is missing its credential."""


def selected_provider(env: dict[str, str] | None = None) -> Provider:
    env = os.environ if env is None else env
    raw = env.get("LLM_PROVIDER", "cursor_cli").strip().lower() or "cursor_cli"
    try:
        return Provider(raw)
    except ValueError as exc:
        raise CredentialsError(
            f"LLM_PROVIDER must be cursor_cli, cursor_proxy, or anthropic, got '{raw}'"
        ) from exc


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
    provider = selected_provider(env)

    if provider is Provider.CURSOR_CLI:
        # CURSOR_API_KEY is preferred; `agent login` alone can also work.
        return
    if provider is Provider.CURSOR_PROXY:
        if not env.get("CURSOR_API_KEY", "").strip():
            raise CredentialsError(
                "LLM_PROVIDER=cursor_proxy but CURSOR_API_KEY is not set. "
                "Add it to .env, or use LLM_PROVIDER=cursor_cli."
            )
        return

    if any(m.startswith(CLAUDE_CODE_PREFIX) for m in models) and not env.get("CLAUDE_CODE_OAUTH_TOKEN"):
        raise CredentialsError(
            "Claude Code path selected (CLAUDE_CODE_ENABLE=true) but CLAUDE_CODE_OAUTH_TOKEN is not set. "
            "Create one with `claude setup-token` and add it to .env, or set CLAUDE_CODE_ENABLE=false "
            "to use ANTHROPIC_API_KEY."
        )
    if any(m.startswith(ANTHROPIC_PREFIX) for m in models) and not env.get("ANTHROPIC_API_KEY"):
        raise CredentialsError(
            "Claude API path selected (CLAUDE_CODE_ENABLE is false or unset) but ANTHROPIC_API_KEY is not set. "
            "Add it to .env, or set CLAUDE_CODE_ENABLE=true with CLAUDE_CODE_OAUTH_TOKEN, "
            "or set LLM_PROVIDER=cursor_cli for development."
        )
