from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AutonomyLevel = Literal["L1", "L2", "L3"]
DeployEnvironment = Literal["staging", "production"]


class GovernancePolicy(BaseModel):
    """Risk-based autonomy (Harness-style levels)."""

    autonomy_level: AutonomyLevel = "L2"
    environment: DeployEnvironment = "staging"
    require_security_pass: bool = True
    require_qa_pass: bool = True
    require_code_review_pass: bool = True
    block_on_critical_findings: bool = True
    allowed_deploy_hours: str = "any"  # e.g. "business_hours" for production


class DeployApproval(BaseModel):
    decision: Literal["approved", "denied", "pending"]
    approver: str = "governance_gate"
    reason: str = ""
    policy_violations: list[str] = Field(default_factory=list)


class GovernanceGate:
    """Enforces delivery policies before autonomous actions."""

    def __init__(self, policy: GovernancePolicy):
        self.policy = policy

    def can_auto_deploy(
        self,
        *,
        security_passed: bool,
        qa_passed: bool,
        code_review_passed: bool,
        critical_findings: list[str],
    ) -> DeployApproval:
        violations: list[str] = []

        if self.policy.require_security_pass and not security_passed:
            violations.append("Security scan did not pass")
        if self.policy.require_qa_pass and not qa_passed:
            violations.append("QA did not pass")
        if self.policy.require_code_review_pass and not code_review_passed:
            violations.append("Code review did not pass")
        if self.policy.block_on_critical_findings and critical_findings:
            violations.append(f"Critical findings: {', '.join(critical_findings[:3])}")

        if violations:
            return DeployApproval(
                decision="denied",
                reason="Policy violations block deployment",
                policy_violations=violations,
            )

        if self.policy.autonomy_level == "L1":
            return DeployApproval(
                decision="pending",
                reason="L1: No autonomous deploy — explicit approval required",
            )

        if self.policy.autonomy_level == "L2":
            return DeployApproval(
                decision="pending",
                reason="L2: Agent recommends deploy — human/simulated approval required",
            )

        # L3: autonomous within policy
        return DeployApproval(
            decision="approved",
            approver="autonomous_policy",
            reason="L3: All policy checks passed — autonomous deploy permitted",
        )
