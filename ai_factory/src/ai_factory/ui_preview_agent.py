"""UI Designer agent — generates a unique mobile HTML preview per factory run."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from ai_factory.fast_path import run_basic_agent
from ai_factory.models import AIFactoryState

_PREVIEW_BOOTSTRAP = """
<script id="ai-factory-preview-bootstrap">
(function () {
  function ensure(name, fn) {
    if (typeof window[name] !== "function") window[name] = fn;
  }
  ensure("show", function (id) {
    document.querySelectorAll(".screen").forEach(function (s) {
      s.classList.remove("active");
    });
    var el = document.getElementById(id);
    if (el) el.classList.add("active");
  });
  ensure("doAuth", function (mode) {
    var fields =
      mode === "login"
        ? ["loginEmail", "loginPass"]
        : ["suName", "suEmail", "suPass"];
    for (var i = 0; i < fields.length; i++) {
      var input = document.getElementById(fields[i]);
      if (!input || !String(input.value || "").trim()) return;
    }
    show("app");
    if (typeof nav === "function") nav("home");
    if (typeof renderAll === "function") renderAll();
  });
  function wireAuthClicks() {
    document.querySelectorAll("button.link, button.btn").forEach(function (btn) {
      if (btn.dataset.afBound) return;
      var label = (btn.textContent || "").trim().toLowerCase();
      if (label.indexOf("already have") >= 0) {
        btn.dataset.afBound = "1";
        btn.addEventListener("click", function () {
          show("login");
        });
      } else if (label.indexOf("create an account") >= 0) {
        btn.dataset.afBound = "1";
        btn.addEventListener("click", function () {
          show("signup");
        });
      } else if (label.indexOf("create account") >= 0) {
        btn.dataset.afBound = "1";
        btn.addEventListener("click", function () {
          doAuth("signup");
        });
      } else if (label === "sign in") {
        btn.dataset.afBound = "1";
        btn.addEventListener("click", function () {
          doAuth("login");
        });
      }
    });
  }
  function addDemoSkip() {
    var login = document.getElementById("login");
    if (!login || document.getElementById("af-demo-skip")) return;
    var skip = document.createElement("button");
    skip.id = "af-demo-skip";
    skip.type = "button";
    skip.className = "link";
    skip.textContent = "Try demo (skip login)";
    skip.style.marginTop = "8px";
    skip.addEventListener("click", function () {
      ["loginEmail", "loginPass", "suName", "suEmail", "suPass"].forEach(function (id) {
        var el = document.getElementById(id);
        if (el && !el.value) el.value = "demo";
      });
      doAuth("login");
    });
    var anchor = login.querySelector(".link") || login.querySelector(".btn");
    if (anchor && anchor.parentNode) anchor.parentNode.appendChild(skip);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      wireAuthClicks();
      addDemoSkip();
    });
  } else {
    wireAuthClicks();
    addDemoSkip();
  }
})();
</script>
""".strip()


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
- All CSS inside <style>, all JS inside one <script> block — no external files except picsum.photos images
- Must run inside an iframe with sandbox="allow-scripts allow-forms allow-same-origin"
- Use addEventListener for button clicks — avoid inline onclick attributes
- JavaScript MUST parse without syntax errors (no stray braces after template-return functions)
- Do not nest template literals that embed onclick="..." strings — build DOM with createElement instead
- Login screen must include a visible "Try demo (skip login)" button that enters the app without credentials
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


def extract_script_blocks(html: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(
            r"<script\b[^>]*>(.*?)</script>",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if "ai-factory-preview-bootstrap" not in match.group(0)
    ]


def javascript_syntax_ok(script: str) -> bool:
    """Return True when Node can parse the script (or Node is unavailable)."""
    if not script.strip():
        return False
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".js",
        encoding="utf-8",
        delete=False,
    ) as handle:
        handle.write(script)
        path = Path(handle.name)
    try:
        result = subprocess.run(
            ["node", "--check", str(path)],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return True
    finally:
        path.unlink(missing_ok=True)


def repair_common_script_errors(script: str) -> str:
    """Fix frequent LLM mistakes that break the whole preview script."""
    repaired = script
    patterns = (
        r"(`\}\n)\}(\nfunction )",
        r"(`;\n)\}(\nfunction )",
    )
    for _ in range(8):
        if javascript_syntax_ok(repaired):
            break
        changed = False
        for pattern in patterns:
            next_repaired = re.sub(pattern, r"\1\2", repaired, count=1)
            if next_repaired != repaired:
                repaired = next_repaired
                changed = True
                break
        if not changed:
            break
    return repaired


def inject_preview_bootstrap(html: str) -> str:
    if "ai-factory-preview-bootstrap" in html:
        return html
    if re.search(r"</body>", html, re.IGNORECASE):
        return re.sub(
            r"</body>",
            _PREVIEW_BOOTSTRAP + "\n</body>",
            html,
            count=1,
            flags=re.IGNORECASE,
        )
    return html + "\n" + _PREVIEW_BOOTSTRAP


def finalize_preview_html(html: str) -> str:
    """Repair JS when possible and always attach iframe-safe auth bootstrap."""
    scripts = extract_script_blocks(html)
    if scripts:
        main_script = scripts[0]
        repaired = repair_common_script_errors(main_script)
        if repaired != main_script and javascript_syntax_ok(repaired):
            html = html.replace(main_script, repaired, 1)
            main_script = repaired
        if not javascript_syntax_ok(main_script):
            html = inject_preview_bootstrap(html)
            return html
    return inject_preview_bootstrap(html)


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
    return finalize_preview_html(html)
