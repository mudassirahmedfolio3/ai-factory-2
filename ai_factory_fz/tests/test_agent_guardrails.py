"""Guardrails for the non-Architect agents: DV1-3, QA1-2, DE1, ST1, CU1, UX1."""

import json

import pytest

from agentic_sdlc.artifacts.design import ColorToken, DesignSystem, NavigationLink, ScreenSpec, SharedWidget, TypeStyle
from agentic_sdlc.artifacts.prd import CustomerAnswers, QAPair
from agentic_sdlc.artifacts.reports import Bug, QAReport
from agentic_sdlc.guardrails import agents as ag
from agentic_sdlc.guardrails import code as cg
from agentic_sdlc.guardrails import secrets
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.workspace import Workspace

ALL = set(ag.AGENT_RULES)


@pytest.fixture
def profile():
    return Profile.load("flutter_nestjs_ecommerce")


@pytest.fixture
def ws(tmp_path):
    w = Workspace.create("r", runs_dir=tmp_path)
    w.write_text("server/src/cart.spec.ts", "it('adds', () => {});\nit('removes', () => {});\n")
    w.write_text("app/test/cart_test.dart", "testWidgets('shows cart', (t) async {});\n")
    w.write_text("docs/openapi.yaml", "openapi: 3.1.0\n")
    w.write_text("server/openapi.yaml", "openapi: 3.1.0\n")
    w.commit("baseline")
    return w


# ---------- DV1 ----------

def test_dv1_passes_when_tests_are_added(ws, profile):
    ws.write_text("server/src/cart.spec.ts", "it('adds', () => {});\nit('removes', () => {});\nit('totals', () => {});\n")
    assert cg.check_changes(ws, profile.components["backend"], profile, {"DV1"}) == []


def test_dv1_catches_deleted_fewer_and_skipped_tests(ws, profile):
    ws.write_text("server/src/cart.spec.ts", "it.skip('adds', () => {});\n")
    hits = cg.check_changes(ws, profile.components["backend"], profile, {"DV1"})
    assert any("dropped from 2 to 0" in h for h in hits) and any("newly skipped" in h for h in hits)  # skipped = not a live case
    (ws.root / "app/test/cart_test.dart").unlink()
    assert any("app/test/cart_test.dart was deleted" in h for h in cg.check_changes(ws, profile.components["frontend"], profile, {"DV1"}))


def test_dv1_flutter_skip(ws, profile):
    ws.write_text("app/test/cart_test.dart", "testWidgets('shows cart', (t) async {}, skip: true);\n")
    assert any("newly skipped" in h for h in cg.check_changes(ws, profile.components["frontend"], profile, {"DV1"}))


# ---------- DV2 ----------

def test_dv2_finds_real_secrets_but_allows_placeholders(ws, profile):
    ws.write_text("server/src/stripe.ts", "const key = 'sk_live_51Habcdefghijklmnop';\n")
    ws.write_text("infra/staging.env", "STRIPE_SECRET_KEY=sk_test_placeholder\nDATABASE_URL=postgresql://shop:staging_test_password@db/shop\n")
    hits = cg.check_changes(ws, profile.components["backend"], profile, {"DV2"})
    assert hits == ["DV2: server/src/stripe.ts contains what looks like a Stripe secret key; use an environment variable or a placeholder"]


def test_secret_patterns():
    assert secrets.find("postgres://admin:hunter2@db:5432/x") == ["a connection string with a password"]
    assert secrets.find("postgres://admin:${DB_PASSWORD}@db/x") == []
    assert secrets.find("-----BEGIN RSA PRIVATE KEY-----") == ["a private key"]


# ---------- DV3 ----------

def test_dv3_scope_and_contract_copies(ws, profile):
    ws.write_text("app/lib/main.dart", "void main() {}\n")
    ws.write_text("server/openapi.yaml", "openapi: 3.1.0\n# drifted\n")
    hits = cg.check_changes(ws, profile.components["backend"], profile, {"DV3"})
    assert "DV3: app/lib/main.dart is outside this work item's component (server/); undo that change" in hits
    assert any("server/openapi.yaml must stay identical to the approved docs/openapi.yaml" in h for h in hits)


def test_dv3_allows_reports_infra(ws, profile):
    ws.write_text("reports/agent_transcript.jsonl", '{"agent":"backend_developer"}\n')
    ws.write_text("reports/scaffold_backend.log", "ok\n")
    hits = cg.check_changes(ws, profile.components["backend"], profile, {"DV3"})
    assert hits == []


def test_discard_changes_restores_the_component(ws):
    ws.write_text("server/src/cart.spec.ts", "gone\n")
    ws.write_text("server/src/new.ts", "x\n")
    ws.write_text("app/lib/keep.dart", "y\n")
    cg.discard_changes(ws, "server")
    assert "it('adds'" in (ws.root / "server/src/cart.spec.ts").read_text()
    assert not (ws.root / "server/src/new.ts").exists() and (ws.root / "app/lib/keep.dart").exists()


# ---------- QA1 / QA2 ----------

def bug(item="WI-001", sev="major", steps="s"):
    return Bug(id="BUG-1", work_item_id=item, title="t", severity=sev, steps=steps, expected="e", actual="a")


def test_qa_report_rules():
    ok = QAReport(milestone_id="M1", passed=False, bugs=[bug()], summary="s")
    assert ag.report_errors(ok, ["WI-001"], ALL) == []
    contradictory = QAReport(milestone_id="M1", passed=True, bugs=[bug()], summary="s")
    assert any(e.startswith("QA1") for e in ag.report_errors(contradictory, ["WI-001"], ALL))
    unknown = QAReport(milestone_id="M1", passed=False, bugs=[bug(item="WI-999", steps=" ")], summary="s")
    errors = ag.report_errors(unknown, ["WI-001"], ALL)
    assert any("WI-999" in e for e in errors) and any("has no steps" in e for e in errors)
    assert ag.report_errors(QAReport(milestone_id="i", passed=False, bugs=[bug(item="RELEASE")], summary="s"),
                            ["WI-001"], ALL, ("RELEASE",)) == []


# ---------- DE1 ----------

def test_de1_container(ws, profile):
    assert ag.de1_container(ws, profile) == ["DE1: server/Dockerfile is missing"]
    ws.write_text("server/Dockerfile", "FROM node:22-slim AS build\nRUN npm ci\nFROM node:22-slim\nCMD node dist/main.js\n")
    hits = ag.de1_container(ws, profile)
    assert any("runs as root" in h for h in hits) and sum("Node 22" in h for h in hits) == 1
    ws.write_text("server/Dockerfile", "FROM node:24-slim AS build\nFROM node:24-slim\nUSER node\nCMD node dist/main.js\n")
    assert ag.de1_container(ws, profile) == []


# ---------- ST1 ----------

def test_st1_smoke_suite(ws, profile):
    ws.write_text("server/package.json", json.dumps({"scripts": {"test": "jest"}}))
    assert ag.st1_smoke_suite(ws, profile, 3) == ["ST1: package.json has no 'test:smoke' script"]
    ws.write_text("server/package.json", json.dumps({"scripts": {"test:smoke": "jest -c smoke"}}))
    ws.write_text("server/smoke-tests/journey.smoke.ts", "import { x } from '../src/cart';\njest.mock('x');\nit('a', () => {});\n")
    hits = ag.st1_smoke_suite(ws, profile, 3)
    assert len(hits) == 4 and any("1 test(s)" in h for h in hits) and any("SMOKE_BASE_URL" in h for h in hits)
    ws.write_text("server/smoke-tests/journey.smoke.ts",
                  "const b = process.env.SMOKE_BASE_URL;\nit('a', () => {});\nit('b', () => {});\nit('c', () => {});\n")
    assert ag.st1_smoke_suite(ws, profile, 3) == []


def test_st1_device_suite(ws, profile):
    assert any("no on-device journey tests" in h for h in ag.st1_device_suite(ws, profile))
    ws.write_text("app/integration_test/journey_test.dart", "import 'package:mocktail/mocktail.dart';\ntestWidgets('j', (t) async {});\n")
    assert ag.st1_device_suite(ws, profile) == ["ST1: the device tests mock the network; they must use the real staging API"]


# ---------- CU1 ----------

def test_cu1_every_question_answered():
    qs = ["Guest checkout?", "Which platforms?"]
    full = CustomerAnswers(answers=[QAPair(question="Guest checkout?", answer="No"), QAPair(question="Which platforms?", answer="Both")])
    assert ag.cu1_answers(full, qs) == []
    rephrased = CustomerAnswers(answers=[QAPair(question="Guest checkout", answer="No"), QAPair(question="Platforms", answer="Both")])
    assert ag.cu1_answers(rephrased, qs) == []
    partial = CustomerAnswers(answers=[QAPair(question="Guest checkout?", answer="No")])
    assert ag.cu1_answers(partial, qs) == ["CU1: no answer for: Which platforms?"]


# ---------- UX1 ----------

def design(colors, routes=("/a", "/b")):
    return DesignSystem(colors=colors, typography=[TypeStyle(name="b", size=14, weight=400, line_height=1.4)],
                        spacing=[4], corner_radii=[4], shared_widgets=[SharedWidget(name="w", description="d")],
                        screens=[ScreenSpec(id=f"SCR-0{i}", name="s", route=r, purpose="p", components=[], states=[], story_ids=[])
                                 for i, r in enumerate(routes)],
                        navigation=[NavigationLink(from_screen="a", to_screen="b", trigger="t")], accessibility=[])


def test_ux1_colours_routes_contrast():
    good = design([ColorToken(name="primary", light="#1A73E8", dark="#8AB4F8"),
                   ColorToken(name="onPrimary", light="#FFFFFF", dark="#000000")])
    assert ag.ux1_tokens(good) == []
    bad = design([ColorToken(name="primary", light="#FFEB3B", dark="red"),
                  ColorToken(name="onPrimary", light="#FFFFFF", dark="#000000")], routes=("/a", "/a"))
    hits = ag.ux1_tokens(bad)
    assert any("'red' is not a hex colour" in h for h in hits)
    assert "UX1: route /a is used by more than one screen" in hits
    assert any("onPrimary on primary (light) has contrast" in h for h in hits)
    assert round(ag.contrast("#000000", "#FFFFFF"), 1) == 21.0


def test_rules_are_chosen_per_pipeline():
    assert ag.enabled({}) == ALL
    assert ag.enabled({"guardrails": {"agents": ["DV1"]}}) == {"DV1"}
    with pytest.raises(ValueError, match="XX1"):
        ag.enabled({"guardrails": {"agents": ["XX1"]}})
