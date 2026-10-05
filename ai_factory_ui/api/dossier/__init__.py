"""Run dossier export (read-only; safe during active factory runs)."""

from __future__ import annotations

from dossier.build_context import build_dossier_context
from dossier.pdf import html_to_pdf
from dossier.render_html import render_dossier_html


def generate_dossier_pdf(run_id: str) -> bytes:
    ctx = build_dossier_context(run_id)
    html = render_dossier_html(ctx)
    return html_to_pdf(html)


def generate_dossier_html(run_id: str) -> str:
    ctx = build_dossier_context(run_id)
    return render_dossier_html(ctx)


def generate_combined_dossier_pdf(run_ids: list[str]) -> bytes:
    from dossier.render_html import render_combined_dossier_html

    ids = [r.strip() for r in run_ids if r and r.strip()]
    if not ids:
        raise ValueError("run_ids must not be empty")
    contexts = [build_dossier_context(rid) for rid in ids]
    html = render_combined_dossier_html(contexts)
    return html_to_pdf(html)


def generate_combined_dossier_html(run_ids: list[str]) -> str:
    from dossier.render_html import render_combined_dossier_html

    ids = [r.strip() for r in run_ids if r and r.strip()]
    contexts = [build_dossier_context(rid) for rid in ids]
    return render_combined_dossier_html(contexts)
