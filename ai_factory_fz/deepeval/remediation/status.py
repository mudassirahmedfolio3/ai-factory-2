"""The six-step status of a remediation cycle, saved to runs/<id>/remediation/status.json."""

import html
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

StepState = Literal["pending", "running", "awaiting_approval", "done", "failed", "blocked"]
STEP_DEFS = [
    ("report", "DeepEval report"),
    ("triage", "Project Manager triage and backlog"),
    ("fix", "Fix the source of the problem"),
    ("integration", "Integration Pass"),
    ("qa_smoke", "QA and smoke tests"),
    ("reevaluate", "Re-evaluate with DeepEval"),
]
STATUS_START = "<!-- remediation-status:start -->"
STATUS_END = "<!-- remediation-status:end -->"
_ALLOWED: dict[str, set[str]] = {
    "pending": {"running", "blocked"},
    "running": {"awaiting_approval", "done", "failed", "blocked"},
    "awaiting_approval": {"done", "blocked"},
    "failed": {"running"},
    "blocked": {"running"},
    "done": set(),
}


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


class InvalidTransition(RuntimeError):
    pass


class StepStatus(BaseModel):
    key: str
    title: str
    state: StepState = "pending"
    reason: str = ""
    updated: str = ""


def _default_steps() -> list[StepStatus]:
    return [StepStatus(key=k, title=t) for k, t in STEP_DEFS]


class RemediationStatus(BaseModel):
    steps: list[StepStatus] = Field(default_factory=_default_steps)
    round: int = 1
    note: str = ""

    @classmethod
    def load(cls, path: Path) -> "RemediationStatus":
        path = Path(path)
        return cls.model_validate_json(path.read_text(encoding="utf-8")) if path.is_file() else cls()

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(path)

    def step(self, key: str) -> StepStatus:
        for s in self.steps:
            if s.key == key:
                return s
        raise KeyError(f"Unknown remediation step '{key}'")

    def set(self, key: str, state: StepState, reason: str = "") -> None:
        s = self.step(key)
        if state not in _ALLOWED[s.state]:
            raise InvalidTransition(f"Step '{key}' cannot go from {s.state} to {state}")
        if state in ("running", "awaiting_approval", "done"):
            earlier = self.steps[: self.steps.index(s)]
            if any(e.state != "done" for e in earlier):
                raise InvalidTransition(f"Step '{key}' cannot be {state} before the earlier steps are done")
        s.state, s.reason, s.updated = state, reason, datetime.now().isoformat(timespec="seconds")

    def lines(self) -> list[str]:
        return [f"{i}. {s.title}: {s.state.upper().replace('_', ' ')}" + (f" ({s.reason})" if s.reason else "")
                for i, s in enumerate(self.steps, start=1)]

    def block_md(self) -> str:
        rows = [f"{STATUS_START}", f"**Remediation status** (round {self.round})", "",
                "| # | Step | State | Note |", "|---|---|---|---|"]
        rows += [f"| {i} | {s.title} | {s.state.upper().replace('_', ' ')} | {_cell(s.reason)} |"
                 for i, s in enumerate(self.steps, start=1)]
        rows.append(STATUS_END)
        return "\n".join(rows)

    def block_html(self) -> str:
        items = "".join(
            f'<li class="{html.escape(s.state)}"><b>{html.escape(s.title)}</b>: '
            f'{html.escape(s.state.upper().replace("_", " "))}'
            + (f" ({html.escape(s.reason)})" if s.reason else "") + "</li>"
            for s in self.steps
        )
        return f'{STATUS_START}<ol class="remediation-status">{items}</ol>{STATUS_END}'


def refresh_report_headers(run_dir: Path, status: RemediationStatus) -> list[Path]:
    """Rewrite the status block inside eval_report*.md / *.html that already contain the markers."""
    pattern = re.compile(re.escape(STATUS_START) + r".*?" + re.escape(STATUS_END), re.S)
    changed = []
    for path in sorted(Path(run_dir).glob("eval_report*")):
        if path.suffix not in (".md", ".html"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
            if not pattern.search(text):   # no markers, or a start without an end
                continue
            block = status.block_html() if path.suffix == ".html" else status.block_md()
            path.write_text(pattern.sub(lambda _m: block, text, count=1), encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue   # a cosmetic refresh must never fail the flow
        changed.append(path)
    return changed
