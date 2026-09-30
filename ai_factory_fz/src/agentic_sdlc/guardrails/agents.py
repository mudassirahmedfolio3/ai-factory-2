"""Guardrails for the other agents' outputs (all code checks).

  QA1 consistent verdict: passed <=> no blocker/major bugs          (QA engineer, Integration pass)
  QA2 bugs point to real work items and have steps/expected/actual   (QA engineer, Integration pass)
  DE1 container hygiene: non-root image, toolchain's runtime major    (Deployment engineer)
  ST1 real smoke/device suites: enough journeys, real HTTP, no mocks  (Smoke tester)
  CU1 the Customer answers every question it was asked                (Customer)
  UX1 valid design tokens: hex colours, unique routes, WCAG AA contrast (UI/UX designer)
"""

import json
import re
from pathlib import Path
from typing import Any

from agentic_sdlc.artifacts.design import DesignSystem
from agentic_sdlc.artifacts.prd import CustomerAnswers
from agentic_sdlc.artifacts.reports import QAReport
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.workspace import Workspace

AGENT_RULES = ["DV1", "DV2", "DV3", "QA1", "QA2", "DE1", "ST1", "CU1", "UX1"]


def enabled(pipeline: dict[str, Any]) -> set[str]:
    """Agent guardrails switched on (`guardrails.agents`: a list, or 'all'). Default: all."""
    setting = (pipeline.get("guardrails") or {}).get("agents", "all")
    if setting == "all":
        return set(AGENT_RULES)
    unknown = [r for r in setting if r not in AGENT_RULES]
    if unknown:
        raise ValueError(f"Unknown agent guardrails in pipeline config: {unknown} (known: {AGENT_RULES})")
    return set(setting)


# ---------- QA engineer / Integration pass ----------

def report_errors(report: QAReport, item_ids: list[str], rules: set[str], extra_ids: tuple[str, ...] = ()) -> list[str]:
    errors = []
    if "QA1" in rules and report.passed != (not report.blocking_bugs()):
        errors.append(f"QA1: passed is {report.passed} but there are {len(report.blocking_bugs())} blocker/major bugs; "
                      "passed must be true exactly when there are none")
    if "QA2" in rules:
        valid = set(item_ids) | set(extra_ids)
        for b in report.bugs:
            if b.work_item_id not in valid:
                errors.append(f"QA2: {b.id} names work item '{b.work_item_id}', which is not one of {sorted(valid)}")
            missing = [f for f in ("steps", "expected", "actual") if not getattr(b, f).strip()]
            if missing:
                errors.append(f"QA2: {b.id} has no {', '.join(missing)}")
    return errors


# ---------- Deployment engineer ----------

def _major(image: str) -> str | None:
    m = re.search(r":(\d+)", image)
    return m.group(1) if m else None


def de1_container(ws: Workspace, profile: Profile) -> list[str]:
    api = profile.components.get(profile.release.api_component)
    dockerfile = ws.root / (api.workdir if api else ".") / "Dockerfile"
    if not dockerfile.exists():
        return [f"DE1: {dockerfile.relative_to(ws.root)} is missing"]
    text = dockerfile.read_text(encoding="utf-8", errors="replace")
    stages = re.split(r"(?im)^\s*FROM\s+", text)[1:]
    if not stages:
        return ["DE1: the Dockerfile has no FROM instruction"]
    errors = []
    final = stages[-1]
    users = re.findall(r"(?im)^\s*USER\s+(\S+)", final)
    if not users or users[-1] in ("root", "0", "0:0"):
        errors.append("DE1: the final image runs as root; add a non-root USER (e.g. USER node) in the last stage")
    want = _major(profile.sandbox.runtimes[api.runtime].image) if api and api.runtime in profile.sandbox.runtimes else None
    if want:
        for stage in dict.fromkeys(s.split()[0] for s in stages):   # each base image once
            image = stage
            got = _major(image)
            if image.startswith(("node:", "node@")) and got and got != want:
                errors.append(f"DE1: base image {image} uses Node {got}, but the build toolchain uses Node {want} "
                              "(the lockfile was made with it); use node:" + want + "-slim or similar")
    return errors


# ---------- Smoke tester ----------

def st1_smoke_suite(ws: Workspace, profile: Profile, min_tests: int) -> list[str]:
    api = profile.components.get(profile.release.api_component)
    if not api or not profile.release.smoke_command:
        return []
    root = ws.root / api.workdir
    pkg = root / "package.json"
    script = profile.release.smoke_command.removeprefix("npm run ").strip()
    try:
        scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})
    except (OSError, ValueError):
        scripts = {}
    if script not in scripts:
        return [f"ST1: package.json has no '{script}' script"]
    files = [p for p in root.rglob("*") if p.is_file() and "node_modules" not in p.parts and "smoke" in str(p.relative_to(root)).lower()
             and p.suffix in (".ts", ".js")]
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in files)
    errors = []
    cases = len(re.findall(r"\b(it|test)\s*\(", text))
    if cases < min_tests:
        errors.append(f"ST1: the smoke suite has {cases} test(s); write at least {min_tests} journeys")
    if "SMOKE_BASE_URL" not in text:
        errors.append("ST1: the smoke suite does not use SMOKE_BASE_URL to reach the running API")
    if re.search(r"from\s+['\"](\.\./)+src/|require\(['\"](\.\./)+src/", text):
        errors.append("ST1: the smoke suite imports application code; test the running API over HTTP only")
    if re.search(r"\bjest\.mock\(|\bnock\(|\bmsw\b|setupServer\(", text):
        errors.append("ST1: the smoke suite mocks the network; call the real API")
    return errors


def st1_device_suite(ws: Workspace, profile: Profile) -> list[str]:
    dev = profile.device
    if not dev:
        return []
    app = profile.components.get(dev.app_component)
    root = ws.root / (app.workdir if app else ".") / dev.test_dir
    files = list(root.rglob("*.dart")) if root.exists() else []
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in files)
    errors = []
    if not re.search(r"\btestWidgets\s*\(", text):
        errors.append(f"ST1: no on-device journey tests (testWidgets) in {dev.test_dir}/")
    if re.search(r"\bMock(Client|Dio|HttpClient)\b|package:mocktail|package:mockito|http_mock_adapter", text):
        errors.append("ST1: the device tests mock the network; they must use the real staging API")
    return errors


# ---------- Customer ----------

def cu1_answers(answers: CustomerAnswers, questions: list[str]) -> list[str]:
    """Every question gets a non-empty answer. Matched by question text; if the Customer rephrased
    the questions, one non-empty answer per question is enough."""
    given = [a for a in answers.answers if a.answer.strip()]
    answered = {_q(a.question) for a in given}
    missing = [q for q in questions if _q(q) not in answered]
    if not missing or len(given) >= len(questions):
        return []
    return [f"CU1: no answer for: {q}" for q in missing]


def _q(text: str) -> str:
    return re.sub(r"\W+", " ", text).strip().lower()


# ---------- UI/UX designer ----------

_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 8:
        h = h[2:]  # AARRGGBB (Flutter style): ignore alpha
    def channel(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def ux1_tokens(design: DesignSystem, min_contrast: float = 4.5) -> list[str]:
    errors = []
    for c in design.colors:
        for mode in ("light", "dark"):
            value = getattr(c, mode)
            if not _HEX.match(value.strip()):
                errors.append(f"UX1: colour {c.name} ({mode}) '{value}' is not a hex colour (#RRGGBB)")
    routes = [s.route for s in design.screens]
    errors += [f"UX1: route {r} is used by more than one screen" for r in sorted({r for r in routes if routes.count(r) > 1})]
    by_name = {c.name.lower(): c for c in design.colors}
    for c in design.colors:
        if c.name.lower().startswith("on") and len(c.name) > 2:
            base = by_name.get(c.name[2:].lower())
            if not base:
                continue
            for mode in ("light", "dark"):
                fg, bg = getattr(c, mode).strip(), getattr(base, mode).strip()
                if _HEX.match(fg) and _HEX.match(bg) and contrast(fg, bg) < min_contrast:
                    errors.append(f"UX1: {c.name} on {base.name} ({mode}) has contrast {contrast(fg, bg):.2f}:1; "
                                  f"WCAG AA needs {min_contrast}:1 for text")
    return errors
