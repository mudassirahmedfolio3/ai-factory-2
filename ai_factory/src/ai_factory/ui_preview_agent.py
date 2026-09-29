"""UI Designer agent — generates a unique mobile HTML preview per factory run."""

from __future__ import annotations

import re

from ai_factory.fast_path import run_basic_agent
from ai_factory.models import AIFactoryState


def ui_preview_prompt(state: AIFactoryState) -> str:
    arch = (state.architecture_doc or "")[:2500]
    code = (state.code_artifacts or "")[:2500]
    prd = (state.requirements_doc or "")[:3500]
    brief = (state.client_brief or "")[:1200]
    sprint = (state.current_sprint or state.sprint_backlog or "")[:1500]

    return f"""
Design and build a COMPLETE mobile shopping app preview for "{state.project_name}".

CLIENT BRIEF:
{brief}

PRD:
{prd}

ARCHITECTURE / SCREENS:
{arch or "Infer from PRD."}

SPRINT / BUILD NOTES:
{sprint or code or "MVP catalog + auth + cart."}

You are the UI Designer. Output ONE self-contained HTML file for a phone-sized demo.

MANDATORY SCREENS (all must exist and be reachable via navigation):
1. Login — email, password, button, link to Sign Up
2. Sign Up — name, email, password, button, link to Login
3. Home / Catalog — hero + product grid with images
4. Cart — list items, quantities, checkout button
5. Profile — user info, order history placeholder

MANDATORY FEATURES:
- Bottom tab bar navigation (Home, Browse, Cart, Profile) using vanilla JavaScript
- After login/signup (any non-empty submit), show the main app shell
- Product cards MUST use real images: https://picsum.photos/seed/{{unique-per-product}}/400/300
  Use product-name slugs as seeds (e.g. seed=ethiopian-blend). Never use letter-only placeholders.
- Product names and prices from the PRD niche — not "Product 1" or "Featured Item A"
- Working "Add to cart" with a visible cart badge count
- Mobile-first layout: max-width 390px, centered, touch-friendly tap targets
- Unique visual identity: colors, typography, and layout tailored to this niche (not the same theme every run)

TECHNICAL RULES:
- Single HTML document: <!DOCTYPE html> through </html>
- All CSS inside <style>, all JS inside <script> — no external files except picsum.photos images
- Must run inside an iframe with sandbox="allow-scripts allow-forms"
- No markdown fences, no commentary before or after the HTML
- Maximum ~450 lines of HTML/CSS/JS total

Output ONLY the HTML document.
""".strip()


def extract_html_from_response(text: str) -> str:
    """Pull a complete HTML document from an LLM response."""
    raw = (text or "").strip()
    if not raw:
        return ""

    fence = re.search(r"```(?:html)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()

    lower = raw.lower()
    start = lower.find("<!doctype")
    if start == -1:
        start = lower.find("<html")
    if start == -1:
        return ""

    end = lower.rfind("</html>")
    if end == -1:
        return raw[start:].strip()
    return raw[start : end + len("</html>")].strip()


def validate_preview_html(html: str) -> bool:
    if not html or len(html) < 400:
        return False
    lower = html.lower()
    if not all(token in lower for token in ("<html", "<body", "<style", "<script")):
        return False
    has_login = "login" in lower or "log in" in lower
    has_signup = "sign up" in lower or "signup" in lower or "register" in lower
    if not (has_login and has_signup):
        return False
    has_nav = "nav" in lower or "tab" in lower or "bottom" in lower
    if not has_nav:
        return False
    if "picsum.photos" not in lower and "<img" not in lower:
        return False
    return True


def generate_ui_preview_html(state: AIFactoryState) -> str:
    """Run the UI Designer agent and return HTML for the browser preview."""
    raw = run_basic_agent(
        ui_preview_prompt(state),
        role="Senior UI Designer",
        goal=(
            "Produce a unique, production-quality mobile HTML prototype with auth, "
            "navigation, product images, and cart — tailored to the client brief."
        ),
    )
    html = extract_html_from_response(raw)
    if not validate_preview_html(html):
        raise ValueError(
            "UI preview HTML failed validation (missing screens, images, or structure)."
        )
    return html
