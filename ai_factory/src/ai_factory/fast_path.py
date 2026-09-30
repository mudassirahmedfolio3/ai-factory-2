"""Fast-track pipeline for basic complexity (~10 min target)."""

from __future__ import annotations

from ai_factory.llm_config import get_llm
from ai_factory.llm_invoke import invoke_llm
from ai_factory.models import AIFactoryState, ClientApproval

def basic_discovery_prompt(state: AIFactoryState) -> str:
    return f"""
Create a MINIMAL one-page PRD for {state.project_name}.

Client brief:
{state.client_brief}

Rules:
- Bullet points only, maximum 12 bullets total
- Tailor every feature and product example to the specific niche in the client brief — NOT a generic store
- Name 4-6 example products that fit this niche (realistic titles and price ranges)
- Require login/signup, bottom navigation, product images, and cart in MVP scope
- Include 3 user stories with one acceptance criterion each
- Under 400 words total
- Do NOT ask questions — output the PRD only
""".strip()


def plus_design_prompt(state: AIFactoryState) -> str:
    return f"""
Design the mobile app architecture for {state.project_name} based on this PRD.

PRD:
{state.requirements_doc}

Client feedback (if any):
{chr(10).join(state.client_feedback) or "None"}

Output sections:
## Architecture (component diagram in prose, max 15 lines)
## Key screens (list 5-7 screens with one-line purpose each)
## Data model (3-5 core entities with key fields)
## API endpoints (5-8 REST endpoints)

Tailor everything to the PRD and client brief — do NOT use generic placeholder names.
Under 700 words. Output only the design document.
""".strip()


def plus_sprint_prompt(state: AIFactoryState) -> str:
    return f"""
Create a sprint plan for release 1 of {state.project_name}.

PRD excerpt:
{state.requirements_doc[:2000]}

Architecture:
{state.architecture_doc[:2000]}

Output:
## Sprint goal (1 sentence)
## User stories (5 items with acceptance criteria)
## Out of scope for this release (3 bullets)

Under 400 words. Match the PRD scope exactly.
""".strip()


def plus_build_prompt(state: AIFactoryState) -> str:
    return f"""
Produce a Flutter implementation sketch for {state.project_name} release 1.

Sprint plan:
{state.current_sprint}

Architecture:
{state.architecture_doc[:2500]}

Output:
## File structure (lib/ tree)
## Sample Dart (2-3 widgets: catalog + cart, max 120 lines total)
## State management approach (short paragraph)

Use realistic names from the PRD. Under 800 words. No clarifying questions.
""".strip()


def plus_qa_prompt(state: AIFactoryState) -> str:
    return f"""
Write a QA smoke-test plan for {state.project_name} release 1.

PRD:
{state.requirements_doc[:1500]}

Build summary:
{state.code_artifacts[:1500]}

Output markdown with:
## Test cases (8-10 numbered cases covering catalog, cart, checkout, auth)
## Verdict line containing PASS or FAIL
## Blocking issues (if any)

End with a clear PASS or FAIL verdict for release readiness.
""".strip()


def basic_build_prompt(state: AIFactoryState) -> str:
    return f"""
Build a MINIMAL Flutter MVP plan and code sketch for {state.project_name}.

PRD:
{state.requirements_doc}

Output exactly these sections:
## Architecture (max 8 lines)
## Sprint scope (5 bullets)
## Sample Dart (one small screen widget + one model class, under 60 lines total)

Rules:
- Under 500 words total
- Use product and screen names from the PRD niche — no generic "Product 1" placeholders
- No placeholder "TODO" menus or clarifying questions
- Output the artifact only
""".strip()


def run_basic_agent(prompt: str, role: str, goal: str) -> str:
    """Single-shot LLM call — avoids CrewAI Agent.kickoff() multi-step executor."""
    llm = get_llm("strong")
    wrapped = (
        f"You are {role}. {goal}\n"
        "Produce the complete final deliverable now. "
        "Do NOT ask clarifying questions or offer menus.\n\n"
        f"{prompt}"
    )
    output = invoke_llm(llm, wrapped, agent_role=role, task_name=goal)
    if not output:
        raise RuntimeError(f"Empty LLM response for {role} (basic path)")
    return output

def auto_approval() -> ClientApproval:
    return ClientApproval(decision="approved", feedback=[], priority_changes=[])


def stub_gate_report(title: str, token: str) -> str:
    return (
        f"# {title}\n\n"
        f"{token}\n\n"
        "Auto-passed at basic complexity — full worker crew skipped for speed.\n"
    )
