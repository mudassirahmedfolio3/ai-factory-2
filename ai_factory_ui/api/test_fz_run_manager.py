"""fz worker tracking and resume helpers."""

from fz_run_manager import _parse_run_id_from_cmdline


def test_parse_run_id_from_worker_cmdline():
    cmd = (
        'python fz_worker.py "{\\"run_id\\": \\"20261003-044724\\", \\"project_name\\": \\"x\\"}"'
    )
    assert _parse_run_id_from_cmdline(cmd) == "20261003-044724"
