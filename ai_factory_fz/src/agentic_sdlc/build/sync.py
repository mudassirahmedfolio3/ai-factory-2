"""Keep build progress aligned with the current backlog (e.g. Pass 2 adds WIs under a done milestone)."""

from __future__ import annotations

import logging

from agentic_sdlc.state import ProjectState

log = logging.getLogger(__name__)


def sync_build_with_backlog(state: ProjectState) -> None:
    """Ensure every backlog WI has build progress; reopen milestones that gained incomplete work."""
    backlog = state.backlog
    if backlog is None:
        return
    item_ids = {w.id for w in backlog.work_items}
    for wid in item_ids:
        state.build.item(wid)
    for m in backlog.milestones:
        mp = state.build.milestone(m.id)
        pending = any(
            state.build.item(wid).status != "done"
            for wid in m.work_item_ids
            if wid in item_ids
        )
        if pending and mp.status == "done":
            mp.status = "todo"
            log.info("Reopened milestone %s: backlog has incomplete work items", m.id)
