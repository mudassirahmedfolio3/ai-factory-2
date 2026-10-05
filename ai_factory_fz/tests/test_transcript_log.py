"""Agent transcript log for dossier export."""

from pathlib import Path

from agentic_sdlc.build.transcript_log import append_transcript, extract_transcript_payload


def test_append_and_extract(tmp_path: Path) -> None:
    data = {"result": "hello", "structured_output": {"summary": "ok"}}
    append_transcript(
        tmp_path,
        started_at="2026-01-01T00:00:00+00:00",
        ended_at="2026-01-01T00:01:00+00:00",
        duration_ms=60000,
        phase="build",
        agent_key="backend_developer",
        task_key="implement_work_item",
        model="auto",
        workdir="server",
        success=True,
        exit_code=0,
        prompt="Do the thing",
        data=data,
        stdout='{"result": "hello"}',
    )
    path = tmp_path / "reports" / "agent_transcript.jsonl"
    assert path.is_file()
    payload = extract_transcript_payload(data, '{"result": "hello"}')
    assert payload.get("assistant_result") == "hello"
