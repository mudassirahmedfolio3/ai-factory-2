"""Central LLM configuration — switch providers via .env without editing crews."""

from __future__ import annotations

import os

from crewai import LLM

from ai_factory.cursor_agent_llm import CursorAgentLLM

_groq_patch_applied = False


def _ensure_groq_compat() -> None:
    """CrewAI injects cache_breakpoint into messages; Groq rejects it (crewAI #5886)."""
    global _groq_patch_applied
    if _groq_patch_applied:
        return
    import crewai.llms.cache as _crewai_cache

    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
    _groq_patch_applied = True


def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "openai").strip().lower()


def get_llm(tier: str = "strong") -> LLM | str:
    """
    Return an LLM for CrewAI agents.

    Tiers:
      - strong: PM, architect, code review, security (default gpt-4o / auto)
      - fast: QA, release, DevOps (default gpt-4o-mini / auto)

    Providers (LLM_PROVIDER in .env):
      - openai   — default; set OPENAI_API_KEY
      - anthropic — Claude; set ANTHROPIC_API_KEY (Opus 5 strong / Sonnet 5 fast)
      - groq     — free interim; set GROQ_API_KEY
      - cursor_cli   — Cursor via CLI + CURSOR_API_KEY (recommended temporary)
      - cursor_proxy — Cursor via local proxy (requires agent login + proxy running)
    """
    provider = _provider()
    strong_model = os.getenv("LLM_STRONG_MODEL", "gpt-4o")
    fast_model = os.getenv("LLM_FAST_MODEL", "gpt-4o-mini")
    model = strong_model if tier == "strong" else fast_model

    if provider == "openai":
        return f"openai/{model}"

    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic. "
                "Create one at https://console.anthropic.com/settings/keys"
            )
        claude_model = os.getenv(
            "ANTHROPIC_STRONG_MODEL" if tier == "strong" else "ANTHROPIC_FAST_MODEL",
            "claude-sonnet-4-6" if tier == "strong" else "claude-haiku-4-5",
        )
        # Keep max_tokens modest by default — saves Claude spend on long outputs.
        max_tokens = int(
            os.getenv(
                "ANTHROPIC_MAX_TOKENS" if tier == "strong" else "ANTHROPIC_FAST_MAX_TOKENS",
                "8192" if tier == "strong" else "2048",
            )
        )
        return LLM(
            model=f"anthropic/{claude_model}",
            api_key=api_key,
            max_tokens=max_tokens,
            timeout=int(os.getenv("ANTHROPIC_TIMEOUT", "600")),
        )

    if provider == "groq":
        _ensure_groq_compat()
        groq_model = os.getenv(
            "GROQ_MODEL" if tier == "strong" else "GROQ_FAST_MODEL",
            "llama-3.3-70b-versatile" if tier == "strong" else "llama-3.1-8b-instant",
        )
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is required when LLM_PROVIDER=groq. "
                "Get a free key at https://console.groq.com"
            )
        max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "2048"))
        # LiteLLM groq/ prefix keeps full model IDs (e.g. openai/gpt-oss-20b).
        return LLM(
            model=f"groq/{groq_model}",
            api_key=api_key,
            max_tokens=max_tokens,
            timeout=int(os.getenv("GROQ_TIMEOUT", "120")),
        )

    if provider in ("cursor_cli", "cursor_proxy"):
        api_key = os.getenv("CURSOR_API_KEY", "").strip()
        if provider == "cursor_proxy" and not api_key:
            raise ValueError(
                "CURSOR_API_KEY is required when LLM_PROVIDER=cursor_proxy. "
                "Generate one at https://cursor.com/dashboard/integrations"
            )
        if provider == "cursor_proxy":
            base_url = os.getenv("CURSOR_PROXY_BASE_URL", "http://localhost:4646/v1")
            return LLM(
                model=os.getenv("CURSOR_PROXY_MODEL", "auto"),
                custom_openai=True,
                base_url=base_url,
                api_key=api_key,
            )
        return CursorAgentLLM(
            model=os.getenv("CURSOR_PROXY_MODEL", "auto"),
            api_key=api_key,
            working_dir=os.getenv("CURSOR_AGENT_CWD", os.getcwd()),
            timeout_seconds=int(os.getenv("CURSOR_AGENT_TIMEOUT", "600")),
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER={provider!r}. Use openai, anthropic, groq, cursor_cli, or cursor_proxy."
    )
