"""LLM invoke helper tests."""

from __future__ import annotations

import pytest

from ai_factory.llm_invoke import invoke_llm


class _FakeLlm:
    def call(self, prompt: str) -> str:
        return f"ok:{len(prompt)}"


def test_invoke_llm_supports_callable_providers():
    assert invoke_llm(_FakeLlm(), "hello") == "ok:5"
