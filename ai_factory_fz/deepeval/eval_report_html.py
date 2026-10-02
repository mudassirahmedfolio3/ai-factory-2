"""Self-contained HTML version of the DeepEval report (same data as eval_report.json). All text is escaped."""

from html import escape as e

STATUS_START = "<!-- remediation-status:start -->"
STATUS_END = "<!-- remediation-status:end -->"
STATUS_PLACEHOLDER_HTML = f"{STATUS_START}<p class=\"remediation-status\">Remediation not started.</p>{STATUS_END}"

CSS = """
body{font-family:system-ui,sans-serif;margin:2rem auto;max-width:960px;padding:0 1rem;color:#1f2328;background:#fff}
table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border:1px solid #d0d7de;padding:.4rem .6rem;text-align:left}
th{background:#f6f8fa}.HIGH{color:#1a7f37;font-weight:600}.MEDIUM{color:#9a6700;font-weight:600}.LOW,.FAIL{color:#cf222e;font-weight:600}
.PASS{color:#1a7f37;font-weight:600}details{margin:1rem 0;border:1px solid #d0d7de;border-radius:6px;padding:.5rem 1rem}
.remediation-status{background:#f6f8fa;padding:.75rem 1.5rem;border-radius:6px}
@media(prefers-color-scheme:dark){body{background:#0d1117;color:#e6edf3}th{background:#161b22}th,td,details{border-color:#30363d}
.remediation-status{background:#161b22}.HIGH,.PASS{color:#3fb950}.MEDIUM{color:#d29922}.LOW,.FAIL{color:#ff7b72}}
"""


def _fmt(v) -> str:
    return "-" if v is None else f"{v:.2f}"


def _ul(items) -> str:
    return "<ul>" + "".join(f"<li>{e(str(i))}</li>" for i in items) + "</ul>" if items else "<p>None noted.</p>"


def _agent(a: dict) -> str:
    an = a.get("analysis") or {}
    parts = [f"<details><summary><b>{e(a['agent'])}</b>: <span class=\"{e(a['verdict'].replace(' ', ''))}\">{e(a['verdict'])}</span>, "
             f"confidence {_fmt(a.get('confidence'))} (<span class=\"{e(a['confidence_level'])}\">{e(a['confidence_level'])}</span>)</summary>"]
    if a.get("level_reasoning"):
        parts.append(f"<p><b>Why this level:</b> {e(a['level_reasoning'])}</p>")
    if an and not an.get("error"):
        parts += [f"<p><b>Why this score:</b> {e(an.get('why_score', ''))}</p>",
                  f"<p><b>Level justification:</b> {e(an.get('level_justification', ''))}</p>",
                  "<p><b>Strengths</b></p>" + _ul(an.get("strengths")),
                  "<p><b>Gaps</b></p>" + _ul(an.get("gaps")),
                  "<p><b>What can be improved</b></p>" + _ul(an.get("improvements"))]
    parts.append("<p><b>Judge's reasons per test</b></p><ul>")
    for t in a.get("tests", []):
        parts.append(f"<li><code>{e(t['file'])}::{e(t['test'])}</code>: {e(t['outcome'].upper())}, score {_fmt(t.get('score'))} "
                     f"({e(str(t.get('level')))})<br><i>Criteria:</i> {e(t.get('criteria', ''))}<br>"
                     f"<i>Judge's reason:</i> {e(t.get('reason', ''))}</li>")
    parts.append("</ul></details>")
    return "".join(parts)


def to_html(r: dict) -> str:
    o = r["overall"]
    rows = "".join(
        f"<tr><td>{e(a['agent'])}</td><td class=\"{e(a['verdict'].replace(' ', ''))}\">{e(a['verdict'])}</td>"
        f"<td>{_fmt(a.get('confidence'))}</td><td class=\"{e(a['confidence_level'])}\">{e(a['confidence_level'])}</td>"
        f"<td>{_fmt(a.get('lowest_score'))}</td><td>{a['passed']}/{a['failed']}/{a['skipped']}</td></tr>"
        for a in r["agents"]
    )
    levels = "".join(f"<li><b>{e(k)}</b>: {e(str(v))}</li>" for k, v in r.get("level_meaning", {}).items())
    return (
        f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>DeepEval report {e(r['run'])}</title><style>{CSS}</style></head><body>"
        f"<h1>DeepEval report: {e(r['run'])}</h1><p>Generated {e(r['generated'])}. Judge scores run from 0 to 1; "
        f"a test passes at {r['pass_threshold']} or above.</p>"
        f"<p><b>Overall: <span class=\"{e(o['verdict'].replace(' ', ''))}\">{e(o['verdict'])}</span></b> | confidence {_fmt(o.get('confidence'))} "
        f"({e(o['confidence_level'])}) | {o['passed']} passed, {o['failed']} failed, {o['skipped']} skipped</p>"
        f"{STATUS_PLACEHOLDER_HTML}<h2>Confidence levels</h2><ul>{levels}</ul>"
        f"<h2>Summary</h2><table><tr><th>Agent</th><th>Verdict</th><th>Confidence</th><th>Level</th><th>Lowest</th>"
        f"<th>Pass/Fail/Skip</th></tr>{rows}</table><h2>Details per agent</h2>{''.join(_agent(a) for a in r['agents'])}"
        f"</body></html>"
    )
