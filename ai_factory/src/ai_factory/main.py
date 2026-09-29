#!/usr/bin/env python
from __future__ import annotations

import json
import re
from pathlib import Path

from crewai import Agent, CheckpointConfig
from crewai.flow import Flow, listen, router, start

from ai_factory.crews.build_crew.build_crew import BuildCrew
from ai_factory.crews.change_request_crew.change_request_crew import ChangeRequestCrew
from ai_factory.crews.code_review_crew.code_review_crew import CodeReviewCrew
from ai_factory.crews.design_crew.design_crew import DesignCrew
from ai_factory.crews.discovery_crew.discovery_crew import DiscoveryCrew
from ai_factory.crews.qa_crew.qa_crew import QACrew
from ai_factory.crews.release_crew.release_crew import ReleaseCrew
from ai_factory.crews.security_crew.security_crew import SecurityCrew
from ai_factory.crews.sprint_planning_crew.sprint_planning_crew import SprintPlanningCrew
from ai_factory.complexity import get_profile
from ai_factory.brief_generator import fetch_random_ecommerce_brief
from ai_factory.browser_runner import run_browser_preview
from ai_factory.fast_path import (
    auto_approval,
    basic_build_prompt,
    basic_discovery_prompt,
    plus_build_prompt,
    plus_design_prompt,
    plus_qa_prompt,
    plus_sprint_prompt,
    run_basic_agent,
    stub_gate_report,
)
from ai_factory.governance import GovernanceGate, GovernancePolicy
from ai_factory.llm_config import get_llm
from ai_factory.models import AIFactoryState, ChangeImpact, ClientApproval
from ai_factory.utils import (
    archive_run,
    crew_inputs,
    log_audit,
    new_run_id,
    publish_run_state,
    save_artifact,
    sync_graph_from_state,
    verdict_passed,
)

DEFAULT_CLIENT_BRIEF = """
We need an e-commerce mobile app built with Flutter for a small retail business.
MVP must include: product catalog with search, shopping cart, checkout with address
and payment, order confirmation, and basic user accounts. We want small releasable
increments with client approval after each demo. Post-MVP: order tracking, wishlists,
and promotions.
""".strip()

CHECKPOINT = CheckpointConfig(
    location="./.checkpoints",
    on_events=["method_execution_finished"],
    max_checkpoints=50,
)


class AIFactoryFlow(Flow[AIFactoryState]):
    """Full SDLC + Harness-style delivery orchestration for e-commerce Flutter apps."""

    @start()
    def project_kickoff(self, crewai_trigger_payload: dict | None = None):
        if crewai_trigger_payload:
            self.state.project_name = crewai_trigger_payload.get(
                "project_name", self.state.project_name
            )
            self.state.client_brief = crewai_trigger_payload.get(
                "client_brief", self.state.client_brief
            )
            self.state.max_releases = crewai_trigger_payload.get(
                "max_releases", self.state.max_releases
            )
            self.state.autonomy_level = crewai_trigger_payload.get(
                "autonomy_level", self.state.autonomy_level
            )
            self.state.deploy_environment = crewai_trigger_payload.get(
                "deploy_environment", self.state.deploy_environment
            )
            self.state.complexity = crewai_trigger_payload.get(
                "complexity", self.state.complexity
            )
            if "max_releases" in crewai_trigger_payload:
                self.state.max_releases = crewai_trigger_payload["max_releases"]
        profile = get_profile(self.state.complexity)
        if self.state.max_releases <= 0:
            self.state.max_releases = profile.max_releases
        if not self.state.client_brief.strip():
            self.state.client_brief = DEFAULT_CLIENT_BRIEF
        self.state.governance = GovernancePolicy(
            autonomy_level=self.state.autonomy_level,
            environment=self.state.deploy_environment,
        )
        self.state.phase = "kickoff"
        self.state.release_number = 1
        if crewai_trigger_payload:
            self.state.run_id = crewai_trigger_payload.get("run_id", self.state.run_id)
        if not self.state.run_id:
            self.state.run_id = new_run_id()
        if self.state.complexity == "basic":
            brief = fetch_random_ecommerce_brief()
            self.state.project_name = brief.project_name
            self.state.client_brief = brief.client_brief
            save_artifact(
                "requirements/client_brief.json",
                json.dumps(
                    {
                        "niche": brief.niche,
                        "source": brief.source,
                        "project_name": brief.project_name,
                        "client_brief": brief.client_brief,
                    },
                    indent=2,
                ),
            )
            print(f"Basic track: random e-commerce brief ({brief.niche}) via {brief.source}")
        self.state.run_status = "running"
        publish_run_state(self.state)
        sync_graph_from_state(self.state)
        log_audit(
            "project_kickoff",
            "started",
            "flow",
            {
                "project": self.state.project_name,
                "complexity": self.state.complexity,
                "estimated_minutes": profile.estimated_minutes,
            },
            state=self.state,
        )
        print(
            f"AI Factory kickoff: {self.state.project_name} "
            f"({self.state.complexity}, ~{profile.estimated_minutes} min)"
        )
        return self.state.complexity

    @router(project_kickoff)
    def route_by_complexity(self, complexity):
        if complexity == "basic":
            return "basic_path"
        if complexity == "basic_plus":
            return "basic_plus_path"
        return "standard_path"

    @listen("basic_path")
    def run_basic_discovery(self, _previous=None):
        self.state.phase = "discovery"
        print("Basic track: mini PRD...")
        self.state.requirements_doc = run_basic_agent(
            basic_discovery_prompt(self.state),
            role="Product Manager",
            goal="Write a minimal MVP PRD quickly.",
        )
        save_artifact("requirements/prd.md", self.state.requirements_doc)
        self.state.prd_approval = auto_approval()
        self.state.approval_status = "approved"
        save_artifact(
            "approvals/prd_review.json",
            self.state.prd_approval.model_dump_json(indent=2),
        )
        sync_graph_from_state(self.state)
        log_audit("prd_review", "approved", "auto_basic", state=self.state)
        return "basic_discovery_done"

    @listen(run_basic_discovery)
    def run_basic_build(self, _previous=None):
        self.state.phase = "build"
        publish_run_state(self.state)
        print("Basic track: architecture + code sketch...")
        combined = run_basic_agent(
            basic_build_prompt(self.state),
            role="Flutter Engineer",
            goal="Produce a minimal architecture and Dart sketch.",
        )
        self.state.architecture_doc = combined
        self.state.current_sprint = "MVP: core catalog + cart flow"
        self.state.sprint_backlog = self.state.current_sprint
        self.state.code_artifacts = combined
        save_artifact("design/architecture.md", combined)
        save_artifact("sprints/release_1_plan.md", self.state.current_sprint)
        save_artifact("build/release_1_code.md", combined)
        sync_graph_from_state(self.state)
        return "basic_build_done"

    @listen(run_basic_build)
    def run_basic_auto_gates(self, _previous=None):
        print("Basic track: auto-passing delivery gates...")
        self.state.code_review_report = stub_gate_report("Code Review", "REVIEW_PASS")
        self.state.code_review_passed = True
        self.state.phase = "code_review"
        publish_run_state(self.state)

        self.state.security_report = stub_gate_report("Security Scan", "SECURITY_PASS")
        self.state.security_passed = True
        self.state.phase = "security"
        publish_run_state(self.state)

        self.state.test_report = "# QA\n\nPASS\n\nSmoke tests assumed for basic MVP.\n"
        self.state.qa_passed = True
        self.state.phase = "qa"
        publish_run_state(self.state)

        self.state.release_notes = (
            f"# Release 1 — {self.state.project_name}\n\n"
            "Basic complexity run: MVP PRD, architecture sketch, and sample Dart delivered.\n"
        )
        save_artifact("releases/release_1_notes.md", self.state.release_notes)
        self.state.phase = "release"
        publish_run_state(self.state)

        self._launch_browser_preview_and_report()
        self.state.deploy_approved = True
        save_artifact("review/release_1_review.md", self.state.code_review_report)
        save_artifact("security/release_1_scan.md", self.state.security_report)
        save_artifact("qa/release_1_report.md", self.state.test_report)
        self.state.phase = "deployment"
        sync_graph_from_state(self.state)

        self.state.release_approval = auto_approval()
        save_artifact(
            "approvals/release_1_review.json",
            self.state.release_approval.model_dump_json(indent=2),
        )
        log_audit("release_review", "approved", "auto_basic", state=self.state)
        self.state.remaining_backlog = False
        return "project_complete"

    @listen("basic_plus_path")
    def run_plus_discovery(self, _previous=None):
        self.state.phase = "discovery"
        print("Basic+ track: Discovery Crew...")
        result = DiscoveryCrew().crew().kickoff(inputs=crew_inputs(self.state))
        self.state.requirements_doc = result.raw
        save_artifact("requirements/prd.md", self.state.requirements_doc)
        sync_graph_from_state(self.state)
        return "plus_discovery_done"

    @listen(run_plus_discovery)
    def run_plus_prd_review(self, _previous=None):
        self.state.phase = "prd_review"
        print("Basic+ track: simulated client PRD review...")
        raw = run_basic_agent(
            f"""
Review this Product Requirements Document for {self.state.project_name}.

PRD:
{self.state.requirements_doc}

Respond with JSON only (no markdown fences):
{{"decision": "approved" or "changes_requested" or "rejected", "feedback": ["..."], "priority_changes": ["..."]}}

Approve if MVP scope is clear; otherwise request specific changes.
""".strip(),
            role="Simulated Client Stakeholder",
            goal="Review PRD from a business and UX perspective.",
        )
        approval = self._parse_client_approval(raw)
        self.state.prd_approval = approval
        self.state.client_feedback = list(approval.feedback)
        self.state.approval_status = approval.decision
        save_artifact("approvals/prd_review.json", approval.model_dump_json(indent=2))
        log_audit("prd_review", approval.decision, "simulated_client", state=self.state)
        return approval.decision

    @router(run_plus_prd_review)
    def route_plus_prd(self, decision):
        if decision == "rejected":
            print("Basic+ track: PRD rejected — continuing with feedback noted.")
        elif decision == "changes_requested" and self.state.prd_approval:
            self.state.change_requests = list(
                self.state.prd_approval.priority_changes or self.state.prd_approval.feedback
            )
        return "plus_prd_ok"

    @listen("plus_prd_ok")
    def run_plus_design(self, _previous=None):
        self.state.phase = "design"
        print("Basic+ track: architecture & screens...")
        self.state.architecture_doc = run_basic_agent(
            plus_design_prompt(self.state),
            role="Technical Architect",
            goal="Produce tailored mobile architecture from the PRD.",
        )
        save_artifact("design/architecture.md", self.state.architecture_doc)
        sync_graph_from_state(self.state)
        return "plus_design_done"

    @listen(run_plus_design)
    def run_plus_sprint(self, _previous=None):
        self.state.phase = "sprint_planning"
        print("Basic+ track: sprint planning...")
        sprint = run_basic_agent(
            plus_sprint_prompt(self.state),
            role="Product Manager",
            goal="Define release 1 sprint scope from PRD and architecture.",
        )
        self.state.current_sprint = sprint
        self.state.sprint_backlog = sprint
        save_artifact("sprints/release_1_plan.md", sprint)
        sync_graph_from_state(self.state)
        return "plus_sprint_done"

    @listen(run_plus_sprint)
    def run_plus_build(self, _previous=None):
        self.state.phase = "build"
        print("Basic+ track: Flutter build sketch...")
        build = run_basic_agent(
            plus_build_prompt(self.state),
            role="Flutter Engineer",
            goal="Produce implementation sketch aligned with sprint and PRD.",
        )
        self.state.code_artifacts = build
        save_artifact("build/release_1_code.md", build)
        sync_graph_from_state(self.state)
        return "plus_build_done"

    @listen(run_plus_build)
    def run_plus_qa(self, _previous=None):
        self.state.phase = "qa"
        print("Basic+ track: QA smoke plan...")
        qa = run_basic_agent(
            plus_qa_prompt(self.state),
            role="QA Engineer",
            goal="Validate release readiness against PRD and build output.",
        )
        self.state.test_report = qa
        save_artifact("qa/release_1_report.md", qa)
        passed = bool(re.search(r"\bPASS\b", qa, re.IGNORECASE)) and not bool(
            re.search(r"\bFAIL\b", qa, re.IGNORECASE)
        )
        self.state.qa_passed = passed
        sync_graph_from_state(self.state)
        log_audit("qa", "pass" if passed else "fail", "qa_engineer", state=self.state)
        return "plus_qa_done"

    @listen(run_plus_qa)
    def run_plus_finish(self, _previous=None):
        print("Basic+ track: lightweight gates + browser preview...")
        self.state.code_review_report = stub_gate_report(
            "Code Review", "REVIEW_PASS"
        ) + "\n(Full code review crew skipped at Basic+ complexity.)\n"
        self.state.code_review_passed = True
        self.state.phase = "code_review"
        publish_run_state(self.state)

        self.state.security_report = stub_gate_report(
            "Security Scan", "SECURITY_PASS"
        ) + "\n(Full security crew skipped at Basic+ complexity.)\n"
        self.state.security_passed = True
        self.state.phase = "security"
        publish_run_state(self.state)

        self.state.release_notes = (
            f"# Release 1 — {self.state.project_name}\n\n"
            f"Basic+ run: discovery crew, design, build, QA, browser preview.\n\n"
            f"QA verdict: {'PASS' if self.state.qa_passed else 'FAIL'}\n"
        )
        save_artifact("releases/release_1_notes.md", self.state.release_notes)
        self.state.phase = "release"
        publish_run_state(self.state)

        self._launch_browser_preview_and_report()
        self.state.deploy_approved = True
        save_artifact("review/release_1_review.md", self.state.code_review_report)
        save_artifact("security/release_1_scan.md", self.state.security_report)

        self.state.release_approval = auto_approval()
        save_artifact(
            "approvals/release_1_review.json",
            self.state.release_approval.model_dump_json(indent=2),
        )
        log_audit("release_review", "approved", "auto_basic_plus", state=self.state)
        self.state.remaining_backlog = False
        return "project_complete"

    @staticmethod
    def _parse_client_approval(raw: str) -> ClientApproval:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return ClientApproval.model_validate_json(raw[start : end + 1])
            except Exception:
                pass
        return ClientApproval(decision="approved", feedback=[], priority_changes=[])

    def _launch_browser_preview_and_report(self) -> None:
        """Open a mobile-style web preview in the browser (replaces deploy/emulator)."""
        self.state.phase = "browser"
        publish_run_state(self.state)
        print("Opening browser preview...")
        result = run_browser_preview(
            run_id=self.state.run_id,
            project_name=self.state.project_name,
            client_brief=self.state.client_brief,
            code_artifacts=self.state.code_artifacts,
            requirements_doc=self.state.requirements_doc,
        )
        status = "BROWSER_PASS" if result.success else "BROWSER_SKIPPED"
        report = (
            f"# Browser Preview — {self.state.project_name}\n\n"
            f"**Status:** {status}\n"
            f"**Message:** {result.message}\n"
        )
        if result.url:
            report += f"**URL:** {result.url}\n"
        if result.preview_dir:
            report += f"**Files:** `{result.preview_dir.as_posix()}/index.html`\n"
        if result.log:
            report += f"\n## Log\n\n```\n{result.log}\n```\n"

        self.state.deployment_report = report
        self.state.post_deploy_report = report
        self.state.post_deploy_passed = result.success
        rel = self.state.release_number
        save_artifact(f"browser/release_{rel}_preview.md", report)
        sync_graph_from_state(self.state)
        log_audit(
            "browser_preview",
            "pass" if result.success else "skipped",
            "browser_runner",
            {"url": result.url, "preview_dir": str(result.preview_dir or "")},
            state=self.state,
        )

    @listen("standard_path")
    def run_discovery(self, _previous=None):
        self.state.phase = "discovery"
        print("Running Discovery Crew...")
        result = DiscoveryCrew().crew().kickoff(inputs=crew_inputs(self.state))
        self.state.requirements_doc = result.raw
        save_artifact("requirements/prd.md", self.state.requirements_doc)
        sync_graph_from_state(self.state)
        return "discovery_complete"

    @listen(run_discovery)
    def prd_client_review(self, _previous):
        self.state.phase = "prd_review"
        print("Simulated Client reviewing PRD...")
        client = Agent(
            role="Simulated Client Stakeholder",
            goal="Review the PRD from a business and UX perspective and approve or request changes.",
            backstory=(
                "You represent a non-technical retail business owner. You care about "
                "user experience, clear checkout, and realistic MVP scope—not implementation details."
            ),
            llm=get_llm("strong"),
        )
        prompt = f"""
Review this Product Requirements Document for {self.state.project_name}.

PRD:
{self.state.requirements_doc}

Evaluate business value, UX clarity, and MVP scope. Approve if ready for design,
or request specific changes.
"""
        result = client.kickoff(prompt, response_format=ClientApproval)
        self.state.prd_approval = result.pydantic
        self.state.client_feedback = list(result.pydantic.feedback)
        self.state.approval_status = result.pydantic.decision
        save_artifact("approvals/prd_review.json", result.pydantic.model_dump_json(indent=2))
        log_audit("prd_review", result.pydantic.decision, "simulated_client", state=self.state)
        return result.pydantic.decision

    @router(prd_client_review)
    def route_prd_approval(self, decision):
        if decision == "approved":
            return "prd_approved"
        if decision == "changes_requested":
            self.state.change_requests = list(
                self.state.prd_approval.priority_changes  # type: ignore[union-attr]
                or self.state.prd_approval.feedback  # type: ignore[union-attr]
            )
            return "prd_changes"
        return "prd_rejected"

    @listen("prd_approved")
    def run_design(self, _previous=None):
        self.state.phase = "design"
        print("Running Design Crew...")
        result = DesignCrew().crew().kickoff(inputs=crew_inputs(self.state))
        self.state.architecture_doc = result.raw
        if "backend" in result.raw.lower():
            self.state.backend_recommendation = result.raw[:2000]
        save_artifact("design/architecture.md", self.state.architecture_doc)
        sync_graph_from_state(self.state)
        return "design_complete"

    @listen("prd_changes")
    def run_change_request_from_prd(self, _previous=None):
        return self._run_change_request()

    @listen("release_changes")
    def run_change_request_from_release(self, _previous=None):
        return self._run_change_request()

    def _run_change_request(self):
        self.state.phase = "change_request"
        print("Running Change Request Crew...")
        result = ChangeRequestCrew().crew().kickoff(inputs=crew_inputs(self.state))
        raw = result.raw
        self.state.requirements_doc = raw
        save_artifact("requirements/prd_updated.md", raw)
        severity = "minor"
        if "major" in raw.lower()[:500]:
            severity = "major"
        self.state.change_impact = ChangeImpact(
            severity=severity,  # type: ignore[arg-type]
            summary=raw[:500],
            updated_backlog=raw,
        )
        return severity

    @router(run_change_request_from_prd)
    def route_change_from_prd(self, severity):
        return self._route_change_severity(severity)

    @router(run_change_request_from_release)
    def route_change_from_release(self, severity):
        return self._route_change_severity(severity)

    def _route_change_severity(self, severity):
        if severity == "major":
            return "change_to_discovery"
        return "change_to_sprint"

    @listen("change_to_discovery")
    @listen("prd_rejected")
    def rerun_discovery_after_change(self, _previous=None):
        approval = self.state.prd_approval
        if approval and approval.feedback:
            self.state.change_requests = list(approval.feedback)
        print("Re-running Discovery with client feedback...")
        return self.run_discovery("from_change")

    @listen("change_to_sprint")
    def sprint_after_minor_change(self, _previous=None):
        return self._run_sprint_planning()

    @listen(run_design)
    def run_sprint_planning(self, _previous):
        return self._run_sprint_planning()

    @listen("next_sprint")
    def start_next_sprint(self, _previous=None):
        self.state.release_number += 1
        self.state.build_retry_count = 0
        self.state.qa_passed = False
        self.state.code_review_passed = False
        self.state.security_passed = False
        self.state.post_deploy_passed = False
        self.state.deploy_approved = False
        return self._run_sprint_planning()

    def _run_sprint_planning(self):
        self.state.phase = "sprint_planning"
        print(f"Running Sprint Planning (release #{self.state.release_number})...")
        result = SprintPlanningCrew().crew().kickoff(inputs=crew_inputs(self.state))
        self.state.current_sprint = result.raw
        self.state.sprint_backlog = result.raw
        save_artifact(f"sprints/release_{self.state.release_number}_plan.md", result.raw)
        sync_graph_from_state(self.state)
        return "sprint_planned"

    @listen(run_sprint_planning)
    @listen(sprint_after_minor_change)
    @listen(start_next_sprint)
    def run_build(self, _previous):
        self.state.phase = "build"
        print(f"Running Build Crew (attempt {self.state.build_retry_count + 1})...")
        result = BuildCrew().crew().kickoff(inputs=crew_inputs(self.state))
        self.state.code_artifacts = result.raw
        save_artifact(f"build/release_{self.state.release_number}_code.md", result.raw)
        sync_graph_from_state(self.state)
        return "build_complete"

    @listen("delivery_retry")
    def run_build_retry(self, _previous=None):
        self.state.build_retry_count += 1
        return self.run_build("retry")

    @listen(run_build)
    def run_code_review(self, _previous):
        """Harness-style Code Review Worker Agent."""
        self.state.phase = "code_review"
        print("Running Code Review Worker Agent...")
        result = CodeReviewCrew().crew().kickoff(inputs=crew_inputs(self.state))
        self.state.code_review_report = result.raw
        save_artifact(f"review/release_{self.state.release_number}_review.md", result.raw)
        self.state.code_review_passed = verdict_passed(result.raw, "REVIEW_PASS", "REVIEW_FAIL")
        sync_graph_from_state(self.state)
        log_audit(
            "code_review",
            "pass" if self.state.code_review_passed else "fail",
            "code_reviewer",
            state=self.state,
        )
        return "review_pass" if self.state.code_review_passed else "review_fail"

    @router(run_code_review)
    def route_code_review(self, verdict):
        if verdict == "review_pass":
            return "review_pass"
        if self.state.build_retry_count < self.state.max_build_retries:
            return "delivery_retry"
        print("Max retries reached; continuing with review failures noted.")
        return "review_pass"

    @listen("review_pass")
    def run_security_scan(self, _previous=None):
        """Harness-style Security Testing Worker Agent."""
        self.state.phase = "security"
        print("Running AppSec Worker Agent...")
        result = SecurityCrew().crew().kickoff(inputs=crew_inputs(self.state))
        self.state.security_report = result.raw
        save_artifact(f"security/release_{self.state.release_number}_scan.md", result.raw)
        self.state.security_passed = verdict_passed(result.raw, "SECURITY_PASS", "SECURITY_FAIL")
        sync_graph_from_state(self.state)
        log_audit(
            "security_scan",
            "pass" if self.state.security_passed else "fail",
            "security_engineer",
            state=self.state,
        )
        return "security_pass" if self.state.security_passed else "security_fail"

    @router(run_security_scan)
    def route_security(self, verdict):
        if verdict == "security_pass":
            return "security_pass"
        if self.state.build_retry_count < self.state.max_build_retries:
            return "delivery_retry"
        print("Max retries reached; continuing with security failures noted.")
        return "security_pass"

    @listen("security_pass")
    def run_qa(self, _previous=None):
        self.state.phase = "qa"
        print("Running QA Crew...")
        result = QACrew().crew().kickoff(inputs=crew_inputs(self.state))
        self.state.test_report = result.raw
        save_artifact(f"qa/release_{self.state.release_number}_report.md", result.raw)
        passed = bool(re.search(r"\bPASS\b", result.raw, re.IGNORECASE))
        failed = bool(re.search(r"\bFAIL\b", result.raw, re.IGNORECASE))
        self.state.qa_passed = passed and not failed
        sync_graph_from_state(self.state)
        log_audit("qa", "pass" if self.state.qa_passed else "fail", "qa_engineer", state=self.state)
        return "qa_pass" if self.state.qa_passed else "qa_fail"

    @router(run_qa)
    def route_qa(self, verdict):
        if verdict == "qa_pass":
            return "qa_pass"
        if self.state.build_retry_count < self.state.max_build_retries:
            return "delivery_retry"
        print("Max QA retries reached; proceeding with failures noted.")
        return "qa_pass"

    @listen("qa_pass")
    def run_release(self, _previous=None):
        self.state.phase = "release"
        print("Running Release Crew...")
        result = ReleaseCrew().crew().kickoff(inputs=crew_inputs(self.state))
        self.state.release_notes = result.raw
        save_artifact(f"releases/release_{self.state.release_number}_notes.md", result.raw)
        sync_graph_from_state(self.state)
        return "release_complete"

    @listen(run_release)
    def governance_deploy_gate(self, _previous):
        """Risk-based autonomy gate before deployment (Harness L1/L2/L3)."""
        self.state.phase = "governance"
        gate = GovernanceGate(self.state.governance)
        critical = []
        if "CRITICAL" in self.state.security_report.upper():
            critical.append("critical_security")
        approval = gate.can_auto_deploy(
            security_passed=self.state.security_passed,
            qa_passed=self.state.qa_passed,
            code_review_passed=self.state.code_review_passed,
            critical_findings=critical,
        )
        save_artifact(
            f"governance/release_{self.state.release_number}_policy.json",
            approval.model_dump_json(indent=2),
        )
        log_audit(
            "governance_gate",
            approval.decision,
            "governance_gate",
            {"reason": approval.reason},
            state=self.state,
        )

        if approval.decision == "denied":
            print(f"Deploy blocked: {approval.policy_violations}")
            return "deploy_denied"

        if approval.decision == "pending":
            return self._request_deploy_approval(approval.reason)

        self.state.deploy_approved = True
        return "deploy_approved"

    def _request_deploy_approval(self, reason: str):
        """L2 human-in-the-loop — simulated ops approver."""
        self.state.phase = "deploy_approval"
        print(f"Deploy approval required ({reason})...")
        approver = Agent(
            role="Simulated Ops Approver",
            goal="Approve or deny production/staging deployments based on policy and reports.",
            backstory=(
                "You are the on-call release manager. You approve deploys when security, "
                "QA, and code review evidence is satisfactory for the target environment."
            ),
            llm=get_llm("strong"),
        )
        prompt = f"""
Deployment approval request for {self.state.project_name} release #{self.state.release_number}.
Environment: {self.state.deploy_environment}
Autonomy level: {self.state.autonomy_level}

Code review passed: {self.state.code_review_passed}
Security passed: {self.state.security_passed}
QA passed: {self.state.qa_passed}

Release notes excerpt:
{self.state.release_notes[:1200]}

Approve or deny this deployment.
"""
        result = approver.kickoff(prompt, response_format=ClientApproval)
        self.state.deploy_approval = result.pydantic
        save_artifact(
            f"approvals/deploy_{self.state.release_number}_review.json",
            result.pydantic.model_dump_json(indent=2),
        )
        log_audit("deploy_approval", result.pydantic.decision, "simulated_ops", state=self.state)
        if result.pydantic.decision == "approved":
            self.state.deploy_approved = True
            return "deploy_approved"
        return "deploy_denied"

    @router(governance_deploy_gate)
    def route_governance(self, outcome):
        if outcome == "deploy_approved":
            return "deploy_approved"
        return "deploy_denied"

    @listen("deploy_denied")
    def handle_deploy_denied(self, _previous=None):
        print("Deployment denied — returning to build for remediation.")
        return "delivery_retry"

    @listen("deploy_approved")
    def run_browser_preview(self, _previous=None):
        """Open web preview in the browser instead of cloud deploy."""
        self._launch_browser_preview_and_report()
        return "post_deploy_pass"

    @router(run_browser_preview)
    def route_post_deploy(self, verdict):
        if verdict == "post_deploy_pass":
            return "post_deploy_pass"
        if self.state.build_retry_count < self.state.max_build_retries:
            return "delivery_retry"
        return "post_deploy_pass"

    @listen("post_deploy_pass")
    def release_client_review(self, _previous=None):
        self.state.phase = "release_review"
        print("Simulated Client reviewing release...")
        client = Agent(
            role="Simulated Client Stakeholder",
            goal="Review the release demo and notes; approve or request changes.",
            backstory=(
                "You are the business owner reviewing a sprint demo. You approve releases "
                "that deliver promised user-facing value with acceptable quality."
            ),
            llm=get_llm("strong"),
        )
        prompt = f"""
Review release #{self.state.release_number} for {self.state.project_name}.

Release notes:
{self.state.release_notes}

Deployed to: {self.state.deploy_environment}
Post-deploy verification: {"PASS" if self.state.post_deploy_passed else "FAIL"}

Sprint scope delivered:
{self.state.current_sprint}

QA summary:
{self.state.test_report[:1000]}

Approve the release, request changes, or reject.
"""
        result = client.kickoff(prompt, response_format=ClientApproval)
        self.state.release_approval = result.pydantic
        self.state.client_feedback = list(result.pydantic.feedback)
        save_artifact(
            f"approvals/release_{self.state.release_number}_review.json",
            result.pydantic.model_dump_json(indent=2),
        )
        log_audit("release_review", result.pydantic.decision, "simulated_client", state=self.state)
        backlog_markers = ("deferred", "remaining", "post-mvp", "backlog", "future")
        combined = (self.state.requirements_doc + self.state.sprint_backlog).lower()
        self.state.remaining_backlog = any(m in combined for m in backlog_markers)
        return result.pydantic.decision

    @router(release_client_review)
    def route_release(self, decision):
        if decision == "changes_requested":
            approval = self.state.release_approval
            self.state.change_requests = list(
                approval.priority_changes if approval else []
            ) or list(approval.feedback if approval else [])
            return "release_changes"
        if decision == "rejected":
            self.state.change_requests = list(
                self.state.release_approval.feedback  # type: ignore[union-attr]
            )
            return "release_changes"
        if self.state.remaining_backlog and self.state.release_number < self.state.max_releases:
            return "next_sprint"
        return "project_complete"

    @listen("project_complete")
    def finalize_project(self, _previous=None):
        self.state.phase = "complete"
        self.state.run_status = "completed"
        publish_run_state(self.state)
        sync_graph_from_state(self.state)
        archive_run(self.state)
        summary = {
            "project_name": self.state.project_name,
            "releases_completed": self.state.release_number,
            "backend_recommendation": self.state.backend_recommendation[:500],
            "autonomy_level": self.state.autonomy_level,
            "phase": "complete",
            "knowledge_graph": "artifacts/knowledge_graph.json",
            "audit_trail": "artifacts/audit/",
        }
        save_artifact("summary.json", json.dumps(summary, indent=2))
        print("AI Factory SDLC + delivery complete.")
        print(json.dumps(summary, indent=2))
        return summary


def kickoff():
    from dotenv import load_dotenv

    load_dotenv(Path(".env"), override=True)
    flow = AIFactoryFlow(checkpoint=CHECKPOINT)
    flow.kickoff(
        inputs={
            "project_name": "ecommerce-flutter-app",
            "client_brief": "",
            "max_releases": 2,
            "autonomy_level": "L2",
            "deploy_environment": "staging",
        }
    )


def plot():
    flow = AIFactoryFlow()
    flow.plot()


def run_with_trigger():
    import sys

    if len(sys.argv) < 2:
        raise RuntimeError("No trigger payload provided. Pass JSON as the first argument.")

    trigger_payload = json.loads(sys.argv[1])
    flow = AIFactoryFlow(checkpoint=CHECKPOINT)
    flow.kickoff({"crewai_trigger_payload": trigger_payload})


if __name__ == "__main__":
    kickoff()
