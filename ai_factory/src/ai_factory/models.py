from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ai_factory.complexity import ComplexityLevel
from ai_factory.governance import AutonomyLevel, DeployEnvironment, GovernancePolicy


class ClientApproval(BaseModel):
    decision: Literal["approved", "changes_requested", "rejected"]
    feedback: list[str] = Field(default_factory=list)
    priority_changes: list[str] = Field(default_factory=list)


class QAReport(BaseModel):
    passed: bool
    blocking_issues: list[str] = Field(default_factory=list)
    test_summary: str = ""


class ChangeImpact(BaseModel):
    severity: Literal["minor", "major"]
    summary: str
    affected_stories: list[str] = Field(default_factory=list)
    updated_backlog: str = ""


class AIFactoryState(BaseModel):
    run_id: str = ""
    run_status: str = "pending"
    project_name: str = "ecommerce-flutter-app"
    client_brief: str = ""
    backend_recommendation: str = ""
    requirements_doc: str = ""
    architecture_doc: str = ""
    sprint_backlog: str = ""
    current_sprint: str = ""
    code_artifacts: str = ""
    ui_preview_html: str = ""
    code_review_report: str = ""
    security_report: str = ""
    deployment_report: str = ""
    post_deploy_report: str = ""
    test_report: str = ""
    release_notes: str = ""
    client_feedback: list[str] = Field(default_factory=list)
    approval_status: str = ""
    change_requests: list[str] = Field(default_factory=list)
    release_number: int = 0
    phase: str = "kickoff"
    qa_passed: bool = False
    code_review_passed: bool = False
    security_passed: bool = False
    post_deploy_passed: bool = False
    deploy_approved: bool = False
    prd_approval: ClientApproval | None = None
    release_approval: ClientApproval | None = None
    deploy_approval: ClientApproval | None = None
    change_impact: ChangeImpact | None = None
    governance: GovernancePolicy = Field(default_factory=GovernancePolicy)
    autonomy_level: AutonomyLevel = "L2"
    deploy_environment: DeployEnvironment = "staging"
    max_releases: int = 3
    complexity: ComplexityLevel = "standard"
    build_retry_count: int = 0
    max_build_retries: int = 2
    remaining_backlog: bool = True
    knowledge_graph_context: str = ""
