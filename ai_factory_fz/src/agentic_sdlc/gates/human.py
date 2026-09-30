"""Human approval gates. The flow pauses here until a person approves or rejects."""

import os
from pathlib import Path
from typing import Callable, Literal

from agentic_sdlc.state import GateDecision

GateMode = Literal["console", "auto"]
InputFn = Callable[[str], str]


def gate_mode(configured: str) -> GateMode:
    mode = os.environ.get("SDLC_GATE_MODE", configured)
    if mode not in ("console", "auto"):
        raise ValueError(f"Unknown gate mode '{mode}' (use console or auto)")
    return mode  # type: ignore[return-value]


def request_approval(
    gate: str,
    summary: str,
    documents: list[Path],
    mode: GateMode,
    input_fn: InputFn = input,
) -> GateDecision:
    if mode == "auto":
        return GateDecision(gate=gate, approved=True, decided_by="auto")

    print("\n" + "=" * 72)
    print(f"APPROVAL NEEDED: {gate}")
    print(summary)
    print("Review these documents:")
    for d in documents:
        print(f"  - {d}")
    print("=" * 72)
    while True:
        answer = input_fn("Approve? [y]es / [n]o: ").strip().lower()
        if answer in ("y", "yes"):
            notes = input_fn("Optional notes (Enter to skip): ").strip()
            return GateDecision(gate=gate, approved=True, feedback=notes)
        if answer in ("n", "no"):
            feedback = ""
            while not feedback:
                feedback = input_fn("What should change? ").strip()
            return GateDecision(gate=gate, approved=False, feedback=feedback)
