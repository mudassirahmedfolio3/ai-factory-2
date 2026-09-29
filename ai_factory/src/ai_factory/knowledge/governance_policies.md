# Governance & Risk-Based Autonomy

## Autonomy levels (Harness-style)

| Level | Name | Behavior |
|-------|------|----------|
| **L1** | Supervised | Agents prepare artifacts only; no runtime deploy decisions |
| **L2** | Human-in-the-loop | Agents recommend; deploy/merge requires explicit approval |
| **L3** | Policy-bound autonomous | Agents deploy automatically when all policy checks pass |

## Default policies for AI Factory

- Production deploys: **L2** minimum (simulated client or ops approval)
- Staging deploys: **L3** allowed after security + QA pass
- Critical security findings: always block regardless of level
- All agent actions logged to artifacts/audit/

## Approval gates

1. PRD approval (simulated client)
2. Code review pass (worker agent)
3. Security scan pass (worker agent)
4. QA pass
5. Deploy approval (governance gate — L2/L3 logic)
6. Release demo approval (simulated client)

## Audit trail

Every gate writes JSON to `artifacts/audit/` with timestamp, decision, agent, and policy version.
