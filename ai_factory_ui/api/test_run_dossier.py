"""SDLC dossier export (read-only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from config import FZ_RUNS_DIR
from dossier import generate_dossier_html, generate_dossier_pdf


@pytest.fixture
def sample_run_id() -> str | None:
    if not FZ_RUNS_DIR.is_dir():
        return None
    for run_dir in sorted(FZ_RUNS_DIR.iterdir(), reverse=True):
        if (run_dir / "state.json").is_file():
            return run_dir.name
    return None


def test_dossier_html_contains_core_sections(sample_run_id: str | None) -> None:
    if not sample_run_id:
        pytest.skip("No fz runs on disk")
    html = generate_dossier_html(sample_run_id)
    assert "SDLC Dossier" in html
    assert "Executive summary" in html
    assert "Scope traceability matrix" in html
    assert "Business Developer" in html
    assert "Release passes" in html
    assert "Agent activity log" in html
    assert "Agent transcripts" in html


def test_dossier_pdf_non_empty(sample_run_id: str | None) -> None:
    if not sample_run_id:
        pytest.skip("No fz runs on disk")
    pdf = generate_dossier_pdf(sample_run_id)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 5000
