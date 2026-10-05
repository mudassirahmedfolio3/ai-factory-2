from agentic_sdlc.artifacts.backlog import Backlog, Milestone, WorkItem
from agentic_sdlc.build.sync import sync_build_with_backlog
from agentic_sdlc.state import BuildState, ItemProgress, MilestoneProgress, ProjectState


def _wi(wid: str) -> WorkItem:
    return WorkItem(
        id=wid,
        title=wid,
        description="d",
        epic_id="E",
        feature="f",
        component="backend",
        story_ids=["US-001"],
        estimate_points=2,
    )


def test_sync_reopens_done_milestone_when_backlog_has_todo():
    s = ProjectState(
        run_id="r",
        backlog=Backlog(
            epics=[],
            work_items=[_wi("WI-010")],
            milestones=[Milestone(id="M3", name="R2", goal="g", work_item_ids=["WI-010"])],
        ),
        build=BuildState(
            items={"WI-001": ItemProgress(status="done")},
            milestones={"M2": MilestoneProgress(status="done", qa_rounds=2)},
        ),
    )
    sync_build_with_backlog(s)
    assert s.build.item("WI-010").status == "todo"
    assert "M3" not in s.build.milestones or s.build.milestone("M3").status == "todo"
