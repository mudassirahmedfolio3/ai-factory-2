"""Build the pass/fail report, per-agent confidence levels, and a written analysis from one DeepEval session.

Every judge score is between 0 and 1 and passes at PASS_THRESHOLD (0.6). An agent's confidence is the average
of its judge scores (its own test file plus its step in the end-to-end flow). It is labelled:

    HIGH    0.80 - 1.00   the work meets the criteria with little or no gap
    MEDIUM  0.60 - 0.79   passing, but the judge found real gaps
    LOW     0.00 - 0.59   failing

The verdict is separate from the average: an agent is FAIL as soon as one of its tests fails.
For each agent the report adds the judge's own reasons and a written analysis (why the score, why that level,
strengths, gaps, what to improve). The analysis is one extra LLM call per agent; set DEEPEVAL_REPORT_ANALYSIS=0
to skip it and keep only the judge's reasons.
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from common import PASS_THRESHOLD, RESULTS, ask_llm
from eval_report_html import STATUS_END, STATUS_PLACEHOLDER_HTML, STATUS_START, to_html  # noqa: F401

STATUS_PLACEHOLDER_MD = (
    f"{STATUS_START}\nRemediation not started. Set DEEPEVAL_REMEDIATE=1 to start it after the report.\n{STATUS_END}"
)

AGENTS = [
    "customer", "spec_writer", "project_manager", "architect", "ui_ux_designer",
    "backend_developer", "frontend_developer", "qa_engineer", "deployment_engineer",
    "integration_pass", "smoke_tester",
]
HIGH = 0.8

LEVEL_MEANING = {
    "HIGH": f"{HIGH:.2f} to 1.00. The output meets the criteria with little or no gap.",
    "MEDIUM": f"{PASS_THRESHOLD:.2f} to {HIGH - 0.01:.2f}. The output passes, but the judge found real gaps that should be fixed.",
    "LOW": f"0.00 to {PASS_THRESHOLD - 0.01:.2f}. The output does not meet the criteria; the test fails.",
}


def label(score: float | None) -> str:
    if score is None:
        return "-"
    return "HIGH" if score >= HIGH else "MEDIUM" if score >= PASS_THRESHOLD else "LOW"


def agent_of(file_name: str, test_name: str) -> str | None:
    """Which agent a test belongs to: test_<agent>.py, or the agent named in a flow test's function name."""
    stem = file_name.removesuffix(".py").removeprefix("test_")
    if stem in AGENTS:
        return stem
    for agent in sorted(AGENTS, key=len, reverse=True):
        if agent in test_name:
            return agent
    return None


def level_justification(agent: dict) -> str:
    """Rule-based sentence that states exactly why the agent got its level (no LLM involved)."""
    c, low = agent["confidence"], agent["lowest_score"]
    if c is None:
        return "No judged tests ran for this agent, so there is no score."
    lvl = agent["confidence_level"]
    text = f"The average judge score is {c:.2f}, which is {lvl} ({LEVEL_MEANING[lvl]})"
    if agent["failed"]:
        text += f" {agent['failed']} test(s) scored below {PASS_THRESHOLD}, so the verdict is FAIL even though the average may look acceptable."
    elif low is not None and low - PASS_THRESHOLD < 0.05:
        text += f" The weakest test scored {low:.2f}, right on the pass mark, so a small regression would turn it into a FAIL."
    elif lvl == "MEDIUM":
        text += f" The weakest test scored {low:.2f}; every test passes but none of the gaps below were serious enough to fail."
    return text


def _analysis_prompt(agent: str, data: dict) -> str:
    tests = "\n\n".join(
        f"Test: {t['file']}::{t['test']}\nResult: {t['outcome']}, score {t['score']}\n"
        f"Criteria: {t['criteria']}\nJudge's reason: {t['reason']}"
        for t in data["tests"] if t["score"] is not None
    )
    return (
        f"You are writing the analysis section of a QA report for the '{agent}' agent of an AI software pipeline. "
        f"An LLM judge scored its output between 0 and 1 (pass mark {PASS_THRESHOLD}). "
        f"The agent's confidence is {data['confidence']:.2f}, level {data['confidence_level']} "
        f"(HIGH >= {HIGH}, MEDIUM >= {PASS_THRESHOLD}, LOW below).\n\n"
        f"Here are the judged tests with the judge's own reasons:\n\n{tests}\n\n"
        "Using ONLY what the reasons say (do not invent problems), answer as JSON with these keys:\n"
        '{"why_score": "2-4 sentences explaining why the agent got this score",\n'
        ' "level_justification": "1-3 sentences justifying why the level is HIGH, MEDIUM or LOW and not the next one up",\n'
        ' "strengths": ["short bullet", ...],\n'
        ' "gaps": ["short bullet naming a concrete missing or wrong thing", ...],\n'
        ' "improvements": ["short, concrete action that would raise the score, tied to a gap", ...]}\n'
        "Use empty lists when there is nothing to say. Return only the JSON."
    )


def _parse_json(text: str) -> dict | None:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    try:
        return json.loads(text[start:end + 1]) if start != -1 and end > start else None
    except json.JSONDecodeError:
        return None


def analyze(agent: str, data: dict) -> dict | None:
    try:
        return _parse_json(ask_llm(_analysis_prompt(agent, data)))
    except Exception as exc:  # the report must still be written when the extra call fails
        return {"error": f"{type(exc).__name__}: {exc}"}


def build(outcomes: dict[tuple[str, str], str], run_name: str) -> dict:
    """outcomes: (file, test) -> passed | failed | skipped, collected by conftest.py."""
    tests, structure = [], []
    per_agent = {a: {"scores": [], "failed": 0, "passed": 0, "skipped": 0, "tests": []} for a in AGENTS}
    for (file, name), outcome in sorted(outcomes.items()):
        agent = agent_of(file, name)
        judged = RESULTS.get((file, name), [])
        scores = [j["score"] for j in judged if j["score"] is not None]
        score = sum(scores) / len(scores) if scores else None
        row = {
            "agent": agent, "scope": "flow" if file == "test_end_to_end_flow.py" else "agent",
            "file": file, "test": name, "outcome": outcome,
            "score": None if score is None else round(score, 3),
            "level": label(score),
            "criteria": " | ".join(j.get("criteria") or "" for j in judged),
            "reason": " | ".join(j["reason"] or "" for j in judged),
        }
        tests.append(row)
        if agent is None:
            structure.append(row)
            continue
        per_agent[agent][outcome if outcome in ("passed", "failed", "skipped") else "failed"] += 1
        per_agent[agent]["scores"].extend(scores)
        per_agent[agent]["tests"].append(row)

    agents = []
    for a in AGENTS:
        d = per_agent[a]
        ran = d["passed"] + d["failed"]
        confidence = sum(d["scores"]) / len(d["scores"]) if d["scores"] else None
        entry = {
            "agent": a,
            "verdict": "NOT RUN" if not ran else "FAIL" if d["failed"] else "PASS",
            "confidence": None if confidence is None else round(confidence, 3),
            "confidence_level": label(confidence),
            "lowest_score": round(min(d["scores"]), 3) if d["scores"] else None,
            "passed": d["passed"], "failed": d["failed"], "skipped": d["skipped"],
            "tests": d["tests"],
        }
        entry["level_reasoning"] = level_justification(entry)
        agents.append(entry)

    if os.environ.get("DEEPEVAL_REPORT_ANALYSIS", "1") != "0":
        scored = [a for a in agents if a["confidence"] is not None]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for a, result in zip(scored, pool.map(lambda a: analyze(a["agent"], a), scored)):
                a["analysis"] = result

    all_scores = [s for d in per_agent.values() for s in d["scores"]]
    overall = sum(all_scores) / len(all_scores) if all_scores else None
    counts = {k: sum(1 for t in tests if t["outcome"] == k) for k in ("passed", "failed", "skipped")}
    return {
        "run": run_name,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "pass_threshold": PASS_THRESHOLD,
        "level_meaning": LEVEL_MEANING,
        "overall": {
            "verdict": "FAIL" if counts["failed"] else "PASS" if counts["passed"] else "NOT RUN",
            "confidence": None if overall is None else round(overall, 3),
            "confidence_level": label(overall), **counts,
        },
        "agents": agents,
        "structure_checks": structure,
        "tests": tests,
    }


def fmt(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def _bullets(items) -> list[str]:
    return [f"- {i}" for i in items] if items else ["- None noted."]


def to_markdown(r: dict) -> str:
    o = r["overall"]
    lines = [
        f"# DeepEval report: {r['run']}", "",
        f"Generated {r['generated']}.", "",
        f"**Overall: {o['verdict']}** | confidence {fmt(o['confidence'])} ({o['confidence_level']}) | "
        f"{o['passed']} passed, {o['failed']} failed, {o['skipped']} skipped", "",
        STATUS_PLACEHOLDER_MD, "",
        "## How to read this report", "",
        f"- Every test asks an LLM judge to score one agent's output against written criteria, from 0 to 1. "
        f"A test **passes at {r['pass_threshold']} or above**.",
        "- An agent's **confidence** is the average of its judge scores in this run (its own test file and/or its step in the end-to-end flow, "
        "whichever were run).",
    ]
    lines += [f"- **{k}** ({v})" for k, v in r["level_meaning"].items()]
    lines += [
        "- The **verdict** is separate: an agent is FAIL as soon as one of its tests fails.",
        "- Confidence is the judge's rating of the output, not a statistical probability. Scores can move a little between runs.",
        "", "## Summary", "",
        "| Agent | Verdict | Confidence | Level | Lowest score | Passed | Failed | Skipped |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for a in r["agents"]:
        lines.append(
            f"| {a['agent']} | {a['verdict']} | {fmt(a['confidence'])} | {a['confidence_level']} | "
            f"{fmt(a['lowest_score'])} | {a['passed']} | {a['failed']} | {a['skipped']} |"
        )

    focus = sorted((a for a in r["agents"] if a["confidence"] is not None), key=lambda a: a["confidence"])
    focus = [a for a in focus if a["confidence_level"] != "HIGH"]
    if focus:
        lines += ["", "## Where to improve first (lowest confidence first)", ""]
        for a in focus:
            imps = (a.get("analysis") or {}).get("improvements") or []
            lines.append(f"- **{a['agent']}** ({fmt(a['confidence'])}, {a['confidence_level']}): "
                         + ("; ".join(imps[:2]) if imps else "see the details below"))

    lines += ["", "## Details per agent"]
    for a in r["agents"]:
        lines += ["", f"### {a['agent']}: {a['verdict']}, confidence {fmt(a['confidence'])} ({a['confidence_level']})", ""]
        if a["confidence"] is None:
            lines.append("No judged tests ran for this agent: it was not selected in this run, or its tests were skipped because the files they need are missing.")
            continue
        an = a.get("analysis") or {}
        lines += [f"**Why this level:** {a['level_reasoning']}", ""]
        if an.get("error"):
            lines += [f"_The written analysis could not be generated ({an['error']}). The judge's reasons are below._", ""]
        elif an:
            lines += [f"**Why this score:** {an.get('why_score', '')}", "",
                      f"**Level justification:** {an.get('level_justification', '')}", "",
                      "**Strengths**", *_bullets(an.get("strengths")), "",
                      "**Gaps**", *_bullets(an.get("gaps")), "",
                      "**What can be improved**", *_bullets(an.get("improvements")), ""]
        lines += ["**Judge's reasons per test**", ""]
        for t in a["tests"]:
            if t["score"] is None:
                lines.append(f"- `{t['file']}::{t['test']}`: {t['outcome'].upper()} (no score)")
                continue
            lines += [f"- `{t['file']}::{t['test']}`: {t['outcome'].upper()}, score {fmt(t['score'])} ({t['level']})",
                      f"  - Criteria: {t['criteria']}",
                      f"  - Judge's reason: {t['reason']}"]

    if r["structure_checks"]:
        lines += ["", "## Run-level checks (no judge)", ""]
        lines += [f"- `{t['file']}::{t['test']}`: {t['outcome'].upper()}" for t in r["structure_checks"]]
    return "\n".join(lines) + "\n"


def to_terminal(r: dict) -> list[str]:
    o = r["overall"]
    lines = [f"Overall {o['verdict']}: confidence {fmt(o['confidence'])} ({o['confidence_level']}), "
             f"{o['passed']} passed, {o['failed']} failed, {o['skipped']} skipped (pass mark {r['pass_threshold']})", ""]
    lines.append(f"{'agent':<22}{'verdict':<9}{'confidence':<12}{'level':<8}{'lowest':<8}pass/fail/skip")
    for a in r["agents"]:
        lines.append(f"{a['agent']:<22}{a['verdict']:<9}{fmt(a['confidence']):<12}{a['confidence_level']:<8}"
                     f"{fmt(a['lowest_score']):<8}{a['passed']}/{a['failed']}/{a['skipped']}")
    return lines


def report_name(outcomes) -> str:
    """eval_report_agents / eval_report_flow when only one kind of test ran, else eval_report."""
    flow = {file == "test_end_to_end_flow.py" for file, _ in outcomes}
    return "eval_report" if len(flow) != 1 else "eval_report_flow" if flow == {True} else "eval_report_agents"


def write(r: dict, folder: Path, name: str = "eval_report") -> list[Path]:
    paths = [folder / f"{name}.json", folder / f"{name}.md", folder / f"{name}.html"]
    paths[0].write_text(json.dumps(r, indent=2), encoding="utf-8")
    paths[1].write_text(to_markdown(r), encoding="utf-8")
    paths[2].write_text(to_html(r), encoding="utf-8")
    return paths
