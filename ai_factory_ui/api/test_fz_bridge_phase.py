"""UI phase and stage inference for FZ runs."""

from __future__ import annotations

from types import SimpleNamespace

from fz_bridge import (
    build_progress_summary,
    infer_product_display_name,
    infer_ui_phase,
    infer_ui_stage_index,
)


def _state(**kwargs):
    defaults = dict(
        status="running",
        product_brief=None,
        prd=None,
        architecture=None,
        design=None,
        backlog=None,
        build=SimpleNamespace(items={}, milestones={}),
        release=SimpleNamespace(verified=False),
        gate_history=[],
    )
    defaults.update(kwargs)
    s = SimpleNamespace(**defaults)

    def gate_approved(gate: str) -> bool:
        for d in reversed(s.gate_history):
            if d.gate == gate:
                return d.approved
        return False

    s.gate_approved = gate_approved
    return s


def test_build_not_qa_when_m2_wis_todo() -> None:
    """M1 QA history must not label M2 coding as QA."""
    backlog = SimpleNamespace(
        milestones=[SimpleNamespace(id="M1", work_item_ids=["WI-001"]), SimpleNamespace(id="M2", work_item_ids=["WI-006"])],
        work_items=[
            SimpleNamespace(id="WI-001", component="frontend"),
            SimpleNamespace(id="WI-006", component="backend"),
        ],
    )
    build = SimpleNamespace(
        items={
            "WI-001": {"status": "done"},
            "WI-006": {"status": "todo"},
        },
        milestones={"M1": {"status": "done", "qa_rounds": 3}, "M2": {"status": "todo", "qa_rounds": 0}},
    )
    state = _state(prd=object(), architecture=object(), design=object(), backlog=backlog, build=build)
    state.gate_history = [
        SimpleNamespace(gate="prd", approved=True),
        SimpleNamespace(gate="architecture", approved=True),
    ]
    assert infer_ui_phase(state) == "build"
    assert infer_ui_stage_index(state) == 5


def test_qa_when_milestone_wis_done_but_milestone_not() -> None:
    backlog = SimpleNamespace(
        milestones=[SimpleNamespace(id="M2", work_item_ids=["WI-006"])],
        work_items=[SimpleNamespace(id="WI-006", component="backend")],
    )
    build = SimpleNamespace(
        items={"WI-006": {"status": "done"}},
        milestones={"M2": {"status": "todo", "qa_rounds": 0}},
    )
    state = _state(prd=object(), architecture=object(), design=object(), backlog=backlog, build=build)
    state.gate_history = [
        SimpleNamespace(gate="prd", approved=True),
        SimpleNamespace(gate="architecture", approved=True),
    ]
    assert infer_ui_phase(state) == "qa"


def test_product_display_name_prefers_brief_over_slug() -> None:
    brief = SimpleNamespace(product_name="ShopEase — Release 2 (Mobile Shopping App)")
    state = _state(product_brief=brief)
    assert infer_product_display_name(state, "build-a-comprehensive-e-commerce-app") == "ShopEase"


def test_discovery_stages_customer_then_spec() -> None:
    state = _state()
    assert infer_ui_stage_index(state) == 0
    state.product_brief = object()
    assert infer_ui_stage_index(state) == 1


def test_pass2_replan_shows_architect_not_qa_when_pass1_build_done() -> None:
    """Release 2 replan clears backlog; all Pass 1 WIs done must not show QA Engineer."""
    build = SimpleNamespace(
        items={f"WI-{i:03d}": {"status": "done"} for i in range(1, 13)},
        milestones={"M1": {"status": "done", "qa_rounds": 1}, "M2": {"status": "done", "qa_rounds": 1}},
    )
    state = _state(prd=object(), architecture=None, design=None, backlog=None, build=build, status="running")
    state.gate_history = [SimpleNamespace(gate="prd", approved=True)]
    assert infer_ui_phase(state) == "planning"
    assert infer_ui_stage_index(state) == 2


def test_build_stage_not_architect_when_architecture_gate_pending() -> None:
    """Pass 2 build with open architecture gate must not highlight Architect (stage 2)."""
    backlog = SimpleNamespace(
        milestones=[SimpleNamespace(id="M3", work_item_ids=["WI-016"])],
        work_items=[
            SimpleNamespace(id="WI-010", component="backend"),
            SimpleNamespace(id="WI-016", component="frontend"),
        ],
    )
    build = SimpleNamespace(
        items={f"WI-0{i}": {"status": "done"} for i in range(10, 16)} | {"WI-016": {"status": "todo"}},
        milestones={"M3": {"status": "todo", "qa_rounds": 0}},
    )
    state = _state(
        prd=object(),
        architecture=object(),
        design=object(),
        backlog=backlog,
        build=build,
    )
    state.gate_history = [SimpleNamespace(gate="prd", approved=True)]
    assert infer_ui_phase(state) == "build"
    assert infer_ui_stage_index(state) == 6


def test_build_progress_summary_counts_work_items() -> None:
    backlog = SimpleNamespace(
        milestones=[SimpleNamespace(id="M1", work_item_ids=["WI-001", "WI-002"])],
        work_items=[
            SimpleNamespace(id="WI-001", title="Bootstrap", component="shared"),
            SimpleNamespace(id="WI-002", title="Catalog UI", component="frontend"),
        ],
    )
    build = SimpleNamespace(
        items={"WI-001": {"status": "done"}, "WI-002": {"status": "todo"}},
        milestones={"M1": {"status": "todo", "qa_rounds": 0}},
    )
    state = _state(backlog=backlog, build=build)
    summary = build_progress_summary(state)
    assert summary["total"] == 2
    assert summary["done"] == 1
    assert summary["remaining"] == 1
    assert summary["active_work_item_id"] == "WI-002"
    assert summary["active_work_item_title"] == "Catalog UI"
