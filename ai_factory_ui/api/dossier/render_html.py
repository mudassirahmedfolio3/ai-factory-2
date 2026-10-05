"""Render dossier context to styled HTML for PDF export."""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from dossier.build_context import DossierContext
from dossier.transcripts import format_transcript_for_pdf

MAX_ARTIFACT_LINES = 120


def _img_data_uri(path: Path) -> str | None:
    if not path.is_file():
        return None
    suffix = path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix)
    if not mime:
        return None
    raw = path.read_bytes()
    if len(raw) > 2_500_000:
        return None
    b64 = base64.standard_b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _table(headers: list[str], rows: list[list[str]], css_class: str = "data-table") -> str:
    if not rows:
        return "<p><em>No entries yet.</em></p>"
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>"
    return f'<table class="{css_class}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def _section(title: str, body: str, anchor: str) -> str:
    return f'<section class="block" id="{escape(anchor)}"><h2>{escape(title)}</h2>{body}</section>'


def _bullets(items: list[str]) -> str:
    if not items:
        return "<p><em>None recorded.</em></p>"
    return "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in items) + "</ul>"


def render_dossier_html(ctx: DossierContext) -> str:
    m = ctx.meta
    draft_badge = (
        '<p class="draft-banner">DRAFT — Run in progress. This snapshot reflects work completed so far.</p>'
        if ctx.is_draft
        else ""
    )

    # Executive summary
    exec_lines = [
        f"<strong>Run ID:</strong> {escape(ctx.run_id)}",
        f"<strong>Product:</strong> {escape(ctx.product_name)}",
        f"<strong>Status:</strong> {escape(ctx.status)}",
        f"<strong>Profile:</strong> {escape(ctx.profile)}",
        f"<strong>Pipeline:</strong> {escape(ctx.pipeline)}",
        f"<strong>Generated:</strong> {escape(ctx.generated_at)}",
        f"<strong>LLM tokens (recorded):</strong> {m.get('total_tokens', 0):,}",
    ]
    if ctx.brief:
        exec_lines.append(f"<p class=\"lede\">{escape(ctx.brief[:1200])}</p>")
    exec_html = "<div class=\"exec-grid\">" + "".join(f"<p>{line}</p>" for line in exec_lines[:6]) + "</div>"

    # TOC anchors
    toc = """
    <ol class="toc">
      <li><a href="#sdlc">How this SDLC run works</a></li>
      <li><a href="#executive">Executive summary</a></li>
      <li><a href="#customer">Customer &amp; discovery</a></li>
      <li><a href="#business">Business Developer (specification)</a></li>
      <li><a href="#architect">Solution Architect</a></li>
      <li><a href="#design">UI/UX &amp; experience</a></li>
      <li><a href="#plan">Delivery plan &amp; milestones</a></li>
      <li><a href="#apis">API catalog</a></li>
      <li><a href="#implementation">Implementation &amp; commits</a></li>
      <li><a href="#screens">App screens &amp; features</a></li>
      <li><a href="#qa">Quality assurance</a></li>
      <li><a href="#fixes">QA fix progression</a></li>
      <li><a href="#release">Release, smoke &amp; device</a></li>
      <li><a href="#trace">Scope traceability</a></li>
      <li><a href="#decisions">Decision &amp; gate log</a></li>
      <li><a href="#passes">Release passes &amp; worker sessions</a></li>
      <li><a href="#timeline">Project timeline</a></li>
      <li><a href="#agent-activity">Agent activity log (to &amp; fro)</a></li>
      <li><a href="#transcripts">Agent transcripts (prompts &amp; responses)</a></li>
      <li><a href="#usage">Agent usage &amp; effort</a></li>
      <li><a href="#checks">Automated verification log</a></li>
      <li><a href="#tests">Test inventory</a></li>
      <li><a href="#issues">Known issues &amp; deferrals</a></li>
      <li><a href="#open">Open questions</a></li>
      <li><a href="#env">Environment &amp; reproducibility</a></li>
      <li><a href="#security">Security &amp; compliance notes</a></li>
      <li><a href="#screenshots">Screenshots</a></li>
      <li><a href="#artifacts">Artifact index</a></li>
      <li><a href="#appendix">Appendix — full QA reports</a></li>
      <li><a href="#worker-log">Appendix — worker log excerpt</a></li>
    </ol>
    """

    clar_rows = []
    for pair in ctx.meta.get("clarifications") or []:
        if isinstance(pair, dict):
            clar_rows.append([pair.get("question", ""), pair.get("answer", "")])
    clar_html = _table(["Question", "Answer"], clar_rows) if clar_rows else m["doc_html"].get("clarifications", "")

    customer_body = f"""
    {m['doc_html'].get('product_brief', '')}
    <h3>Clarifications with the customer</h3>
    {clar_html}
    """

    story_rows = m.get("user_story_rows") or []
    business_body = m["doc_html"].get("prd", "")
    if story_rows:
        business_body += "<h3>User stories (structured)</h3>" + _table(
            ["ID", "Title", "Priority", "Acceptance (sample)"], story_rows
        )

    arch = m.get("architecture") or {}
    arch_extra = ""
    if arch:
        comps = [c.get("name", "") for c in (arch.get("components") or []) if isinstance(c, dict)]
        if comps:
            arch_extra += "<h3>Components</h3>" + _bullets(comps)
        adrs = arch.get("adrs") or []
        if adrs:
            adr_items = [f"{a.get('title', '')}: {a.get('decision', '')[:200]}" for a in adrs if isinstance(a, dict)]
            arch_extra += "<h3>Architecture decisions (ADRs)</h3>" + _bullets(adr_items)
    architect_body = m["doc_html"].get("architecture", "") + arch_extra

    design_body = m["doc_html"].get("design", "")

    plan_body = m["doc_html"].get("backlog", "")
    ms_rows = []
    for mid, mp in sorted((m.get("milestones") or {}).items()):
        if isinstance(mp, dict):
            ms_rows.append([mid, mp.get("status", ""), str(mp.get("qa_rounds", 0))])
    plan_body += "<h3>Milestone progress</h3>" + _table(["Milestone", "Status", "QA rounds"], ms_rows)

    api_rows = [[r["method"], r["path"], r["operation_id"], r["summary"]] for r in m.get("openapi_rows") or []]
    apis_body = _table(["Method", "Path", "Operation ID", "Summary"], api_rows)
    arch = m.get("architecture") or {}
    mod_rows = []
    for mod in arch.get("backend_modules") or []:
        if isinstance(mod, dict):
            endpoints = ", ".join(mod.get("endpoints") or [])
            entities = ", ".join(mod.get("entities") or [])
            mod_rows.append([mod.get("name", ""), mod.get("responsibility", "")[:200], entities, endpoints])
    if mod_rows:
        apis_body += "<h3>Backend modules (architecture)</h3>" + _table(
            ["Module", "Responsibility", "Entities", "Endpoints"], mod_rows
        )
    dep_rows = []
    deps = m.get("work_item_dependencies") or []
    for row in deps:
        dep_rows.append([row.get("id", ""), row.get("title", ""), ", ".join(row.get("depends_on") or []), row.get("component", "")])
    if dep_rows:
        apis_body += "<h3>Work item dependencies</h3>" + _table(
            ["Work item", "Title", "Depends on", "Component"], dep_rows
        )

    impl_rows = []
    for wid, prog in sorted((m.get("build_items") or {}).items()):
        if isinstance(prog, dict):
            impl_rows.append(
                [
                    wid,
                    prog.get("status", ""),
                    str(prog.get("attempts", "")),
                    (prog.get("summary") or "")[:280],
                ]
            )
    impl_body = _table(["Work item", "Status", "Attempts", "Summary"], impl_rows)
    commit_rows = [
        [r["work_item"], r["commit"], r["status"], r["title"], r["summary"][:200]]
        for r in m.get("commit_log") or []
    ]
    impl_body += "<h3>Commit changelog (work items)</h3>" + _table(
        ["WI", "Commit", "Status", "Title", "Summary"], commit_rows
    )

    screen_rows = [[s["id"], s["name"], s["route"], s["purpose"]] for s in m.get("app_screens") or []]
    screens_body = _table(["Screen ID", "Name", "Route", "Purpose"], screen_rows)

    qa_body = ""
    for narr in m.get("qa_fix_narrative") or []:
        qa_body += f"<h3>Milestone {escape(narr['milestone_id'])}</h3>"
        for rnd in narr.get("rounds") or []:
            status = "PASSED" if rnd.get("passed") else "FAILED"
            qa_body += f"<h4>Round {rnd['round']} — {status}</h4>"
            qa_body += f"<p>{escape(rnd.get('summary') or '')}</p>"
            if rnd.get("tests_added"):
                qa_body += "<p><strong>Tests added</strong></p>" + _bullets(rnd["tests_added"])
            bugs = rnd.get("bugs") or []
            if bugs:
                bug_rows = [
                    [b.get("id", ""), b.get("severity", ""), b.get("title", ""), b.get("work_item_id", "")]
                    for b in bugs
                    if isinstance(b, dict)
                ]
                qa_body += _table(["Bug", "Severity", "Title", "WI"], bug_rows)

    fixes_body = ""
    for narr in m.get("qa_fix_narrative") or []:
        fixes_body += f"<h3>{escape(narr['milestone_id'])}</h3>"
        for rnd in narr.get("rounds") or []:
            fixed = rnd.get("fixed_bug_ids") or []
            if rnd["round"] == 1 and not fixed:
                fixes_body += f"<p>Round {rnd['round']}: initial QA baseline.</p>"
                continue
            if fixed:
                fixes_body += f"<p>Round {rnd['round']}: addressed prior findings — {escape(', '.join(fixed))}</p>"
            else:
                fixes_body += f"<p>Round {rnd['round']}: no resolved bug IDs detected vs previous round (may be copy or criteria changes).</p>"

    rel = m.get("release") or {}
    rel_parts = []
    if rel.get("smoke_suite") and isinstance(rel["smoke_suite"], dict):
        ss = rel["smoke_suite"]
        rel_parts.append(f"<p><strong>Smoke suite:</strong> {escape(ss.get('summary', ''))}</p>")
        if ss.get("tests_added"):
            rel_parts.append(_bullets(ss["tests_added"]))
    if rel.get("smoke_passed") is not None:
        rel_parts.append(f"<p>Smoke result: <strong>{'PASS' if rel['smoke_passed'] else 'FAIL'}</strong></p>")
    if rel.get("smoke_output"):
        rel_parts.append(f"<pre class=\"code\">{escape(str(rel['smoke_output'])[:4000])}</pre>")
    if rel.get("integration") and isinstance(rel["integration"], dict):
        ig = rel["integration"]
        rel_parts.append(f"<p><strong>Integration:</strong> {escape(ig.get('summary', ''))}</p>")
    if rel.get("device_passed") is not None:
        rel_parts.append(f"<p>Device verification: <strong>{'PASS' if rel['device_passed'] else 'FAIL'}</strong></p>")
    if rel.get("device_note"):
        rel_parts.append(f"<p>{escape(rel['device_note'])}</p>")
    if rel.get("contract_issues"):
        rel_parts.append("<h3>Contract issues</h3>" + _bullets([str(c) for c in rel["contract_issues"]]))
    release_body = "".join(rel_parts) or "<p><em>Release verification not run yet.</em></p>"

    trace_rows = [
        [r["work_item"], r["stories"], r["screens"], r["api_ops"], r["build_status"], r["commit"]]
        for r in m.get("traceability") or []
    ]
    trace_body = _table(["Work item", "User stories", "Screens", "API ops", "Build", "Commit"], trace_rows)

    gate_rows = []
    for g in m.get("gate_history") or []:
        if isinstance(g, dict):
            gate_rows.append(
                [
                    g.get("gate", ""),
                    "Approved" if g.get("approved") else "Rejected",
                    g.get("decided_by", ""),
                    g.get("decided_at", ""),
                    (g.get("feedback") or "")[:200],
                ]
            )
    decisions_body = _table(["Gate", "Outcome", "By", "When", "Feedback"], gate_rows)

    pass_rows = [
        [
            str(p.get("pass_number", "")),
            p.get("label") or "",
            p.get("started_at") or "",
            p.get("ended_at") or "—",
            str(p.get("activity_count", "")),
            (p.get("note") or "")[:120],
        ]
        for p in m.get("passes") or []
    ]
    passes_body = _table(
        ["Pass", "Label", "Started (UTC)", "Ended (UTC)", "Activity rows", "Notes"],
        pass_rows,
    )

    ts_stats = m.get("timeline_stats") or {}
    act_stats = m.get("activity_stats") or {}
    trunc_note = ""
    if ts_stats.get("timeline_truncated") or act_stats.get("activity_truncated"):
        trunc_note = (
            "<p class=\"lede\">Large run: showing "
            f"{len(m.get('timeline') or [])} timeline / {len(m.get('agent_activity') or [])} activity rows "
            f"(caps {ts_stats.get('timeline_cap', '—')} each). "
            "Full transcripts are in <code>reports/agent_transcript.jsonl</code> in the run workspace.</p>"
        )

    timeline_rows = [[e["when"], e["what"], e["detail"]] for e in m.get("timeline") or []]
    timeline_body = trunc_note + _table(["When", "Event", "Detail"], timeline_rows)

    activity_rows = [
        [
            str(a.get("pass") or "—"),
            a.get("when") or "—",
            a.get("when_inferred") or "",
            a.get("agent") or "",
            a.get("action") or "",
            (a.get("detail") or "")[:320],
            a.get("source") or "",
        ]
        for a in m.get("agent_activity") or []
    ]
    activity_body = _table(
        ["Pass", "When", "Time source", "Agent / role", "Action", "Detail", "Source"],
        activity_rows,
    )

    transcript_blocks = []
    for i, entry in enumerate(m.get("transcripts") or [], start=1):
        if not isinstance(entry, dict):
            continue
        transcript_blocks.append(
            f"<h4>Transcript {i}</h4><pre class=\"code\">{escape(format_transcript_for_pdf(entry))}</pre>"
        )
    if transcript_blocks:
        transcripts_body = (
            "<p>Prompt excerpts, assistant results, structured conversation (when returned by Cursor CLI), "
            "and stdout/stderr captures. Logged to <code>reports/agent_transcript.jsonl</code> on each coding-agent call.</p>"
            + "".join(transcript_blocks)
        )
    else:
        transcripts_body = (
            "<p><em>No transcript file yet. After the next worker session, coding agents append "
            "<code>reports/agent_transcript.jsonl</code>. Failures may appear under "
            "<code>reports/agent_failures/</code>.</em></p>"
        )

    usage_rows = [
        [u["agent"], str(u["calls"]), f"{u['duration_ms']:,} ms", f"{u['tokens']:,}", ", ".join(u["tasks"][:8])]
        for u in m.get("usage_by_agent") or []
    ]
    usage_body = _table(["Agent", "Calls", "Duration", "Tokens", "Tasks"], usage_rows)

    check_lines = []
    for wid, prog in sorted((m.get("build_items") or {}).items()):
        if not isinstance(prog, dict):
            continue
        summary = (prog.get("summary") or "").lower()
        if any(k in summary for k in ("flutter analyze", "flutter test", "jest", "e2e", "vitest", "npm test")):
            check_lines.append(f"{wid}: {(prog.get('summary') or '')[:360]}")
    checks_body = _bullets(check_lines) if check_lines else "<p><em>See implementation summaries and QA rounds for verification detail.</em></p>"

    tf = m.get("test_files") or {}
    tests_body = f"<h3>Flutter tests ({len(tf.get('app') or [])})</h3>"
    tests_body += _bullets((tf.get("app") or [])[:40])
    tests_body += f"<h3>Server tests ({len(tf.get('server') or [])})</h3>"
    tests_body += _bullets((tf.get("server") or [])[:40])

    issue_rows = [[i["source"], i["severity"], i["title"]] for i in m.get("known_issues") or []]
    issues_body = _table(["Source", "Severity", "Issue"], issue_rows)

    open_body = _bullets(m.get("open_questions") or [])

    env_body = f"""
    <ul>
      <li><strong>Factory engine:</strong> agentic_sdlc (FZ)</li>
      <li><strong>Profile:</strong> {escape(ctx.profile)}</li>
      <li><strong>Pipeline:</strong> {escape(ctx.pipeline)}</li>
      <li><strong>Workspace:</strong> runs/{escape(ctx.run_id)}/</li>
      <li><strong>Reproducibility:</strong> state.json checkpoint + docs/ + app/ + server/ in run workspace</li>
    </ul>
    """

    sec_criteria = []
    for mp in (m.get("milestones") or {}).values():
        if isinstance(mp, dict):
            for report in mp.get("qa_reports") or []:
                if isinstance(report, dict):
                    for line in report.get("criteria_checked") or []:
                        low = str(line).lower()
                        if any(k in low for k in ("security", "secret", "cleartext", "auth", "owasp")):
                            sec_criteria.append(str(line)[:300])
    security_body = _bullets(sec_criteria[:24]) if sec_criteria else "<p><em>See QA sections for security-related acceptance checks.</em></p>"

    shots_html = ""
    for label, path_str in m.get("screenshots") or []:
        uri = _img_data_uri(Path(path_str))
        if uri:
            shots_html += f'<figure class="shot"><img src="{uri}" alt="{escape(label)}"/><figcaption>{escape(label)}</figcaption></figure>'
    if not shots_html:
        shots_html = "<p><em>No device screenshots captured yet. Use release/device verification or add files under reports/screenshots/.</em></p>"

    art_list = m.get("artifacts") or []
    artifacts_body = _bullets(art_list[:MAX_ARTIFACT_LINES])

    appendix_body = m.get("qa_reports_html") or "<p><em>No QA markdown reports on disk.</em></p>"

    log_excerpt = m.get("worker_log_excerpt") or ""
    log_chars = m.get("worker_log_chars") or len(log_excerpt)
    worker_log_body = (
        f"<p>Excerpt ({len(log_excerpt):,} of {log_chars:,} chars). Full log: "
        f"<code>ai_factory/artifacts/logs/fz_worker_{escape(ctx.run_id)}.log</code></p>"
        f"<pre class=\"code\">{escape(log_excerpt)}</pre>"
        if log_excerpt
        else "<p><em>No fz_worker log found under artifacts/logs/ for this run.</em></p>"
    )

    sdlc_body = """
    <p>This dossier documents a full <strong>agentic SDLC</strong> run orchestrated by AI Factory:
    structured discovery, specification, architecture, design, planned delivery, implementation,
    multi-round QA, and release verification. Each phase produces reviewable artifacts under
    <code>docs/</code>, <code>reports/</code>, and generated <code>app/</code> / <code>server/</code> code,
    checkpointed in <code>state.json</code> after every step.</p>
    <p>Human-readable roles in this document use product names (e.g. Business Developer, Solution Architect).
    Automated agents execute tasks against the pipeline profile; gates record approvals; QA rounds capture
    defects and fixes until milestones pass acceptance.</p>
    """

    audit_rows = []
    for a in m.get("audit") or []:
        if isinstance(a, dict):
            audit_rows.append(
                [
                    a.get("timestamp") or a.get("created_at") or "",
                    a.get("event") or "",
                    a.get("decision") or "",
                    a.get("agent") or "",
                ]
            )
    governance_extra = ""
    if audit_rows:
        governance_extra = "<h3>Console audit trail</h3>" + _table(
            ["When", "Event", "Decision", "Agent"], audit_rows
        )

    sections_html = (
        _section("How this SDLC run works", sdlc_body + governance_extra, "sdlc")
        + _section("Executive summary", draft_badge + exec_html, "executive")
        + _section("Customer & discovery", customer_body, "customer")
        + _section("Business Developer (specification)", business_body, "business")
        + _section("Solution Architect", architect_body, "architect")
        + _section("UI/UX & experience design", design_body, "design")
        + _section("Delivery plan & milestones", plan_body, "plan")
        + _section("API catalog (OpenAPI)", apis_body, "apis")
        + _section("Implementation log", impl_body, "implementation")
        + _section("App screens & features", screens_body, "screens")
        + _section("Quality assurance", qa_body, "qa")
        + _section("Fixes after QA identification", fixes_body, "fixes")
        + _section("Release, smoke & device verification", release_body, "release")
        + _section("Scope traceability matrix", trace_body, "trace")
        + _section("Decision & gate log", decisions_body, "decisions")
        + _section(
            "Release passes & worker sessions",
            "<p>Passes are inferred from console audit <code>run_started</code> events and "
            "<code>fz_worker</code> session markers (resume / new worker). Same run id accumulates "
            "Pass 1, Pass 2, … in one dossier.</p>" + passes_body,
            "passes",
        )
        + _section("Project timeline", timeline_body, "timeline")
        + _section(
            "Agent activity log (to & fro)",
            "<p>Ordered record of gates, audit events, recorded LLM tasks, QA rounds, build attempts, "
            "transcript markers, and flow methods. Timestamps use recorded times, git commit times, QA report "
            "file mtimes, or pass-window interpolation (see Time source column).</p>" + activity_body,
            "agent-activity",
        )
        + _section("Agent transcripts (prompts & responses)", transcripts_body, "transcripts")
        + _section("Agent usage & effort", usage_body, "usage")
        + _section("Automated verification log", checks_body, "checks")
        + _section("Test inventory", tests_body, "tests")
        + _section("Known issues & deferrals", issues_body, "issues")
        + _section("Open questions", open_body, "open")
        + _section("Environment & reproducibility", env_body, "env")
        + _section("Security & compliance snapshot", security_body, "security")
        + _section("Screenshots", shots_html, "screenshots")
        + _section("Artifact index", artifacts_body, "artifacts")
        + _section("Appendix — full QA reports", appendix_body, "appendix")
        + _section("Appendix — worker log excerpt", worker_log_body, "worker-log")
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>SDLC Dossier — {escape(ctx.product_name)} ({escape(ctx.run_id)})</title>
<style>
@page {{
  size: A4;
  margin: 18mm 16mm 22mm 16mm;
  @frame footer {{
    -pdf-frame-content: footerContent;
    bottom: 8mm;
    margin-left: 16mm;
    margin-right: 16mm;
    height: 10mm;
  }}
}}
body {{
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.45;
  color: #1c2744;
}}
.cover {{
  page-break-after: always;
  padding-top: 48mm;
  text-align: center;
}}
.cover .brand {{
  font-size: 11pt;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #635bff;
  margin-bottom: 12mm;
}}
.cover h1 {{
  font-size: 26pt;
  font-weight: 700;
  margin: 0 0 8mm;
  color: #0f172a;
}}
.cover .subtitle {{
  font-size: 13pt;
  color: #475569;
  max-width: 140mm;
  margin: 0 auto 16mm;
}}
.cover .meta {{
  font-size: 10pt;
  color: #64748b;
}}
.toc {{
  page-break-after: always;
  line-height: 1.8;
}}
.toc a {{
  color: #635bff;
  text-decoration: none;
}}
h2 {{
  font-size: 16pt;
  color: #635bff;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 4px;
  margin-top: 18pt;
  page-break-after: avoid;
}}
h3 {{ font-size: 12pt; margin-top: 14pt; color: #334155; }}
h4 {{ font-size: 10.5pt; margin-top: 10pt; }}
.block {{ page-break-inside: avoid; margin-bottom: 14pt; }}
.draft-banner {{
  background: #fef3c7;
  border: 1px solid #f59e0b;
  padding: 8px 12px;
  border-radius: 6px;
  font-weight: 600;
}}
.data-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 8.5pt;
  margin: 8pt 0 12pt;
}}
.data-table th {{
  background: #635bff;
  color: #fff;
  text-align: left;
  padding: 6px 8px;
}}
.data-table td {{
  border: 1px solid #e2e8f0;
  padding: 5px 8px;
  vertical-align: top;
}}
.data-table tr:nth-child(even) td {{ background: #f8fafc; }}
ul {{ margin: 6pt 0 10pt 18pt; }}
li {{ margin-bottom: 4pt; }}
pre.code {{
  background: #f1f5f9;
  padding: 8px;
  font-size: 8pt;
  overflow: hidden;
  border-radius: 4px;
}}
.lede {{ font-size: 11pt; color: #334155; }}
.exec-grid p {{ margin: 4pt 0; }}
.shot {{
  text-align: center;
  margin: 12pt 0;
  page-break-inside: avoid;
}}
.shot img {{
  max-width: 100%;
  max-height: 220mm;
  border: 1px solid #e2e8f0;
}}
.shot figcaption {{ font-size: 9pt; color: #64748b; margin-top: 4pt; }}
#footerContent {{
  font-size: 8pt;
  color: #94a3b8;
  text-align: center;
}}
</style>
</head>
<body>
<div id="footerContent">AI Factory SDLC Dossier · {escape(ctx.run_id)} · {escape(ctx.generated_at)}</div>

<div class="cover">
  <div class="brand">AI Factory</div>
  <h1>{escape(ctx.product_name)}</h1>
  <p class="subtitle">End-to-end SDLC dossier — discovery through release</p>
  <p class="meta">Run {escape(ctx.run_id)} · Status {escape(ctx.status)} · {escape(ctx.generated_at)}</p>
  {('<p class="meta draft-banner">IN PROGRESS SNAPSHOT</p>' if ctx.is_draft else '')}
</div>

<h2>Contents</h2>
{toc}

{sections_html}

</body>
</html>"""


def render_combined_dossier_html(contexts: list[DossierContext]) -> str:
    """Single PDF spanning multiple run ids (e.g. ShopEase pass 1 + lighting MVP)."""
    if not contexts:
        raise ValueError("At least one run id is required for a combined dossier")
    if len(contexts) == 1:
        return render_dossier_html(contexts[0])

    program_rows = [[c.run_id, c.status, c.product_name, c.pipeline] for c in contexts]
    program_table = _table(["Run ID", "Status", "Product", "Pipeline"], program_rows)

    all_activity: list[list[str]] = []
    for ctx in contexts:
        for a in ctx.meta.get("agent_activity") or []:
            all_activity.append(
                [
                    ctx.run_id,
                    str(a.get("pass") or "—"),
                    a.get("when") or "—",
                    a.get("agent") or "",
                    a.get("action") or "",
                    (a.get("detail") or "")[:200],
                ]
            )
    all_activity.sort(key=lambda r: r[2])
    program_activity = _table(
        ["Run", "Pass", "When", "Agent", "Action", "Detail"],
        all_activity[:800],
    )
    program_section = _section(
        "Program overview (all runs in this export)",
        "<p>Combined export merges independent run workspaces into one PDF. "
        "Each run keeps its own pass markers and artifacts below.</p>"
        + program_table
        + "<h3>Cross-run agent activity (timestamped rows first)</h3>"
        + program_activity,
        "program",
    )

    first_html = render_dossier_html(contexts[0])
    first_html = first_html.replace(
        "<h2>Contents</h2>",
        program_section + "<h2>Contents</h2>",
        1,
    )
    first_html = first_html.replace(
        ".block {{ page-break-inside: avoid; margin-bottom: 14pt; }}",
        ".block {{ page-break-inside: avoid; margin-bottom: 14pt; }}\n"
        ".run-separator {{ page-break-before: always; margin-top: 24pt; }}",
        1,
    )
    out = first_html.rsplit("</body>", 1)[0]

    for ctx in contexts[1:]:
        html = render_dossier_html(ctx)
        body = html.split("<body>", 1)[1].rsplit("</body>", 1)[0]
        out += (
            f'<div class="run-separator"><h1>Run {escape(ctx.run_id)} — {escape(ctx.product_name)}</h1>'
            f"<p>Status: {escape(ctx.status)} · Pipeline: {escape(ctx.pipeline)}</p></div>"
            + body
        )
    return out + "</body></html>"
