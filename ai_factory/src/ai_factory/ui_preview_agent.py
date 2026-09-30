"""UI Designer agent — generates a unique mobile HTML preview per factory run."""

from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from ai_factory.fast_path import run_basic_agent
from ai_factory.models import AIFactoryState
from ai_factory.web_images import (
    apply_images_to_html,
    build_image_prompt_block,
    resolve_images_for_labels,
    labels_from_state,
)

# Layout archetypes — each run picks one so product UIs don't all look the same.
_LAYOUT_ARCHETYPES: list[dict[str, str]] = [
    {
        "id": "boutique_light",
        "label": "Light boutique",
        "guide": (
            "Light background, serif display font for the brand name, 2-column product grid, "
            "soft rounded cards, rose or earth-tone accent, hero banner with seasonal copy."
        ),
    },
    {
        "id": "dark_luxury",
        "label": "Dark luxury",
        "guide": (
            "Dark ink background, champagne/gold accent, uppercase letter-spaced headings, "
            "full-bleed product photos, thin borders, editorial spacing — like a premium brand app."
        ),
    },
    {
        "id": "modern_minimal",
        "label": "Modern minimal",
        "guide": (
            "White/neutral background, sans-serif typography, single accent color, "
            "horizontal category chips, list-style catalog with large left-aligned images."
        ),
    },
    {
        "id": "vibrant_market",
        "label": "Vibrant marketplace",
        "guide": (
            "Bold saturated accent, playful rounded buttons, horizontal scroll carousels on home, "
            "emoji-free but energetic micro-copy, pill-shaped category filters."
        ),
    },
    {
        "id": "organic_natural",
        "label": "Organic / natural",
        "guide": (
            "Warm cream background, green or terracotta accent, hand-crafted feel, "
            "single-column cards with tall images, soft shadows, nature-inspired product names."
        ),
    },
]

_PREVIEW_BOOTSTRAP = """
<script id="ai-factory-preview-bootstrap">
(function () {
  function mainScriptAlive() {
    return (
      typeof window.enterApp === "function" ||
      typeof window.showTab === "function" ||
      document.getElementById("btn-login") ||
      document.getElementById("btn-demo")
    );
  }
  function resolveScreen(id) {
    var candidates = [id, "scr-" + id, "screen-" + id, id + "-screen"];
    for (var i = 0; i < candidates.length; i++) {
      var el = document.getElementById(candidates[i]);
      if (el) return el;
    }
    return null;
  }
  function activateScreen(id) {
    document.querySelectorAll(".screen").forEach(function (s) {
      s.classList.remove("active");
    });
    var el = resolveScreen(id);
    if (el) {
      el.classList.add("active");
      return true;
    }
    return false;
  }
  function showNav() {
    var nav =
      document.getElementById("bottom-nav") ||
      document.getElementById("bottomNav") ||
      document.querySelector("nav.nav, nav.tabbar, .tabbar, .nav");
    if (nav) {
      nav.style.display = "flex";
      nav.classList.add("show");
    }
  }
  function enterShell(user) {
    user = user || { name: "Demo Guest", email: "demo@example.com" };
    if (typeof window.enterApp === "function") {
      window.enterApp(user);
      return;
    }
    var demo = document.getElementById("btn-demo");
    if (demo) {
      demo.click();
      return;
    }
    if (!activateScreen("app")) activateScreen("home");
    showNav();
    if (typeof window.showTab === "function") window.showTab("home");
    else if (typeof window.goTab === "function") window.goTab("home");
    if (typeof window.renderHome === "function") window.renderHome();
    if (typeof window.renderAll === "function") window.renderAll();
  }
  function ensure(name, fn) {
    if (typeof window[name] !== "function") window[name] = fn;
  }
  ensure("show", function (id) {
    if (activateScreen(id)) return;
    if (id === "signup" || id === "login") return;
    if (id === "app") enterShell();
  });
  ensure("doAuth", function (mode) {
    var loginEmail = document.getElementById("loginEmail") || document.getElementById("login-email");
    var loginPass = document.getElementById("loginPass") || document.getElementById("login-pass");
    var suName = document.getElementById("suName") || document.getElementById("su-name");
    var suEmail = document.getElementById("suEmail") || document.getElementById("su-email");
    var suPass = document.getElementById("suPass") || document.getElementById("su-pass");
    if (mode === "login") {
      if (!loginEmail || !loginPass || !String(loginEmail.value || "").trim() || !String(loginPass.value || "").trim()) return;
    } else {
      if (!suName || !suEmail || !suPass || !String(suName.value || "").trim()) return;
    }
    var user =
      mode === "login"
        ? {
            name: String(loginEmail.value).split("@")[0],
            email: loginEmail.value,
          }
        : {
            name: suName.value,
            email: suEmail.value,
          };
    enterShell(user);
  });
  function bindClick(id, handler) {
    var el = document.getElementById(id);
    if (!el || el.dataset.afBound) return;
    el.dataset.afBound = "1";
    el.addEventListener("click", handler);
  }
  function wireAuthClicks() {
    bindClick("loginBtn", function () { doAuth("login"); });
    bindClick("btn-login", function () { doAuth("login"); });
    bindClick("signupBtn", function () { doAuth("signup"); });
    bindClick("btn-signup", function () { doAuth("signup"); });
    bindClick("demoBtn", function () { enterShell(); });
    bindClick("btn-demo", function () { enterShell(); });
    bindClick("toSignup", function () { show("signup"); });
    bindClick("to-signup", function () { show("signup"); });
    bindClick("toLogin", function () { show("login"); });
    bindClick("to-login", function () { show("login"); });
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
      } else if (label.indexOf("try demo") >= 0) {
        btn.dataset.afBound = "1";
        btn.addEventListener("click", function () {
          enterShell();
        });
      }
    });
  }
  function addDemoSkip() {
    var login = document.getElementById("login");
    if (!login || document.getElementById("af-demo-skip") || document.getElementById("demoBtn")) {
      return;
    }
    var skip = document.createElement("button");
    skip.id = "af-demo-skip";
    skip.type = "button";
    skip.className = "link";
    skip.textContent = "Try demo (skip login)";
    skip.style.marginTop = "8px";
    skip.addEventListener("click", function () {
      enterShell();
    });
    var anchor = login.querySelector(".link") || login.querySelector(".btn");
    if (anchor && anchor.parentNode) anchor.parentNode.appendChild(skip);
  }
  function ensureInitialScreen() {
    var active = document.querySelector(".screen.active");
    if (active) return;
    if (!activateScreen("login")) activateScreen("signup");
  }
  function boot() {
    ensureInitialScreen();
    wireAuthClicks();
    addDemoSkip();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
</script>
""".strip()


def _infer_app_profile(brief: str, prd: str) -> dict[str, str]:
    """Pick preview screens from the client brief — not always ecommerce."""
    text = f"{brief}\n{prd}".lower()
    blog_markers = (
        "blog",
        "article",
        "articles",
        "post ",
        "posts",
        "writer",
        "writing",
        "publish",
        "newsletter",
        "reading",
        "editor",
    )
    shop_markers = (
        "shop",
        "store",
        "cart",
        "checkout",
        "catalog",
        "product",
        "ecommerce",
        "e-commerce",
        "order",
        "retail",
        "netsuite",
        "suitecommerce",
        "sca",
    )
    if any(marker in text for marker in blog_markers) and not any(
        marker in text for marker in shop_markers
    ):
        return {
            "kind": "blog",
            "label": "mobile blog / reading app",
            "default_notes": "MVP feed + article detail + compose draft.",
            "screens": """
1. Login — email, password, button, link to Sign Up
2. Sign Up — name, email, password, button, link to Login
3. Feed / Home — list of article cards with title, excerpt, author, cover image
4. Article detail — full post body, author, date, share/bookmark actions
5. Compose — title field, body textarea, publish/save draft button
6. Profile — user info, my posts list
""".strip(),
            "features": """
- Bottom tab bar (Feed, Compose, Profile) using vanilla JavaScript
- After login/signup, show the main app shell
- Article cards use real web image URLs provided in WEB IMAGE URLS (Wikimedia / Flickr by topic)
- Article titles and excerpts must match the client brief niche — not generic placeholders
- Working navigation between feed, article detail, and compose
""".strip(),
        }
    if any(marker in text for marker in shop_markers):
        return {
            "kind": "ecommerce",
            "label": "mobile shopping app",
            "default_notes": "MVP catalog + auth + cart.",
            "screens": """
1. Login — email, password, button, link to Sign Up
2. Sign Up — name, email, password, button, link to Login
3. Home / Catalog — hero + product grid with images
4. Cart — list items, quantities, checkout button
5. Profile — user info, order history placeholder
""".strip(),
            "features": """
- Bottom tab bar navigation (Home, Browse, Cart, Profile) using vanilla JavaScript
- After login/signup (any non-empty submit), show the main app shell
- Product cards MUST use the real web image URLs provided in WEB IMAGE URLS
- Product names and prices from the PRD niche — not "Product 1" or "Featured Item A"
- Working "Add to cart" with a visible cart badge count
""".strip(),
        }
    return {
        "kind": "custom",
        "label": "mobile app described in the client brief",
        "default_notes": "Infer MVP screens directly from the client brief and PRD.",
        "screens": """
1. Login — email, password, button, link to Sign Up
2. Sign Up — name, email, password, button, link to Login
3. Home — primary dashboard for the product described in the brief
4. Core feature screen — the main workflow from the brief (not a generic shop unless the brief asks for one)
5. Profile / settings — user info and account actions
""".strip(),
        "features": """
- Bottom tab or primary navigation matching the brief's core workflows
- After login/signup, show the main app shell
- Use real web image URLs from WEB IMAGE URLS where appropriate
- Labels, copy, and data must reflect the client brief — never default to a generic ecommerce demo
""".strip(),
    }


def _design_identity(state: AIFactoryState, attempt: int = 0) -> tuple[str, str, dict[str, str]]:
    brief = (state.client_brief or "")[:200]
    digest = hashlib.sha256(f"{state.run_id}:{state.project_name}:{brief}".encode()).hexdigest()
    design_seed = digest[:8]
    accent = f"#{digest[8:14]}"
    archetype = _LAYOUT_ARCHETYPES[(int(digest[14:18], 16) + attempt) % len(_LAYOUT_ARCHETYPES)]
    return design_seed, accent, archetype


def ui_preview_prompt(state: AIFactoryState, *, attempt: int = 0, retry_note: str = "") -> str:
    arch = (state.architecture_doc or "")[:2500]
    code = (state.code_artifacts or "")[:2500]
    prd = (state.requirements_doc or "")[:3500]
    brief = (state.client_brief or "")[:1200]
    sprint = (state.current_sprint or state.sprint_backlog or "")[:1500]
    design_seed, accent, archetype = _design_identity(state, attempt)
    profile = _infer_app_profile(brief, prd)
    image_block = build_image_prompt_block(
        run_id=state.run_id,
        client_brief=state.client_brief,
        requirements_doc=state.requirements_doc,
        code_artifacts=state.code_artifacts,
        project_name=state.project_name,
    )

    retry_block = f"\nRETRY NOTE: {retry_note}\n" if retry_note else ""

    return f"""
Design and build a COMPLETE {profile["label"]} preview for "{state.project_name}".
App kind detected from brief: {profile["kind"]} — follow the client brief, NOT a generic ecommerce template unless the brief asks for shopping.

DESIGN IDENTITY FOR THIS RUN — you MUST follow this exact creative direction:
- Run design seed: {design_seed}
- Primary accent color: {accent} (derive secondary + background colors from this — do NOT default to generic purple/indigo/teal)
- Layout archetype: {archetype["label"]} — {archetype["guide"]}
- This app must look like a different brand from any generic "AI Factory" or dark-slate ecommerce demo
{retry_block}

CLIENT BRIEF:
{brief}

PRD:
{prd}

ARCHITECTURE / SCREENS:
{arch or "Infer from PRD."}

SPRINT / BUILD NOTES:
{sprint or code or profile["default_notes"]}

{image_block}

You are the UI Designer. Output ONE self-contained HTML file for a phone-sized demo.

MANDATORY SCREENS (all must exist and be reachable via navigation):
{profile["screens"]}

MANDATORY FEATURES:
{profile["features"]}
- Mobile-first layout: max-width 390px, centered, touch-friendly tap targets
- Unique visual identity: colors, typography, and layout tailored to this niche (not the same theme every run)

TECHNICAL RULES:
- Single HTML document: <!DOCTYPE html> through </html>
- All CSS inside <style>, all JS inside one <script> block — no external files except https image URLs
- Must run inside an iframe with sandbox="allow-scripts allow-forms allow-same-origin"
- Use addEventListener for button clicks — avoid inline onclick attributes
- If you wrap JS in an IIFE, assign handlers to window before closing: window.enterApp=enterApp; window.showTab=showTab;
- Prefer screen ids like scr-login, scr-home OR login/home — bootstrap resolves both
- Include id="btn-demo" on the skip-login / demo button
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


_IFRAME_EXPORT = """
  try {
    if (typeof enterApp === "function") window.enterApp = enterApp;
    if (typeof showTab === "function") window.showTab = showTab;
    if (typeof showAuth === "function") window.showAuth = showAuth;
    if (typeof goTab === "function") window.goTab = goTab;
    if (typeof renderHome === "function") window.renderHome = renderHome;
    if (typeof renderAll === "function") window.renderAll = renderAll;
  } catch (e) {}
"""


def export_iframe_handlers(script: str) -> str:
    """Expose app functions on window when LLM wraps logic in an IIFE."""
    if "window.enterApp" in script:
        return script
    if re.search(r"\}\)\(\);\s*$", script.strip()):
        return re.sub(
            r"\}\)\(\);\s*$",
            _IFRAME_EXPORT + "\n})();",
            script.strip(),
            count=1,
        ) + "\n"
    return script.strip() + "\n" + _IFRAME_EXPORT


def repair_common_script_errors(script: str) -> str:
    """Fix frequent LLM mistakes that break the whole preview script."""
    repaired = script
    patterns = (
        r"(`\}\n)\}(\nfunction )",
        r"(`;\n)\}(\nfunction )",
        r"appendChild\(document\.createTextNode\(([^)]+)\);(\}\);)",
        r"createTextNode\(([^)]+)\);(\}\);)",
    )
    replacements = (
        r"\1\2",
        r"\1\2",
        r"appendChild(document.createTextNode(\1));\2",
        r"createTextNode(\1));\2",
    )
    for _ in range(12):
        if javascript_syntax_ok(repaired):
            break
        changed = False
        for pattern, replacement in zip(patterns, replacements, strict=True):
            next_repaired = re.sub(pattern, replacement, repaired, count=1)
            if next_repaired != repaired:
                repaired = next_repaired
                changed = True
                break
        if not changed:
            break
    return repaired


def inject_preview_bootstrap(html: str) -> str:
    if "ai-factory-preview-bootstrap" in html:
        html = re.sub(
            r'<script id="ai-factory-preview-bootstrap">.*?</script>\s*',
            "",
            html,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
    if re.search(r"</body>", html, re.IGNORECASE):
        return re.sub(
            r"</body>",
            _PREVIEW_BOOTSTRAP + "\n</body>",
            html,
            count=1,
            flags=re.IGNORECASE,
        )
    return html + "\n" + _PREVIEW_BOOTSTRAP


@dataclass
class PreviewFinalizeResult:
    html: str
    js_valid_before: bool = True
    js_valid_after: bool = True
    repairs: list[str] = field(default_factory=list)
    bootstrap_injected: bool = False


def finalize_preview_html(html: str) -> PreviewFinalizeResult:
    """Repair JS when possible and always attach iframe-safe auth bootstrap."""
    repairs: list[str] = []
    if "ai-factory-preview-bootstrap" in html:
        html = re.sub(
            r'<script id="ai-factory-preview-bootstrap">.*?</script>\s*',
            "",
            html,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
    scripts = extract_script_blocks(html)
    js_valid_before = True
    js_valid_after = True
    if scripts:
        main_script = scripts[0]
        js_valid_before = javascript_syntax_ok(main_script)
        if not js_valid_before:
            repairs.append("JavaScript syntax error in generated preview script")
        repaired = repair_common_script_errors(main_script)
        if repaired != main_script:
            if javascript_syntax_ok(repaired):
                repairs.append("Auto-repaired JavaScript syntax (stray brace / createTextNode paren)")
                html = html.replace(main_script, repaired, 1)
                main_script = repaired
            else:
                repairs.append("Attempted JavaScript repair — manual review still required")
        exported = export_iframe_handlers(main_script)
        if exported != main_script and javascript_syntax_ok(exported):
            html = html.replace(main_script, exported, 1)
            main_script = exported
            repairs.append("Exported enterApp/showTab to window for iframe preview")
        js_valid_after = javascript_syntax_ok(main_script)
    final_html = inject_preview_bootstrap(html)
    return PreviewFinalizeResult(
        html=final_html,
        js_valid_before=js_valid_before,
        js_valid_after=js_valid_after,
        repairs=repairs,
        bootstrap_injected=True,
    )


def _goal_for_profile(profile: dict[str, str]) -> str:
    kind = profile.get("kind", "custom")
    if kind == "blog":
        return (
            "Produce a unique mobile blog/reading HTML prototype with auth, article feed, "
            "article detail, and compose — tailored to the client brief. "
            "Never reuse a generic ecommerce or dark-slate shop template."
        )
    if kind == "ecommerce":
        return (
            "Produce a unique mobile shopping HTML prototype with auth, catalog, cart, "
            "and real product images — tailored to the client brief niche."
        )
    return (
        "Produce a unique mobile app HTML prototype whose screens and workflows match "
        "the client brief — not a generic ecommerce demo unless the brief asks for shopping."
    )


def _validation_feedback(html: str) -> str:
    if not html:
        return "empty HTML response"
    lower = html.lower()
    issues: list[str] = []
    if len(html) < 400:
        issues.append("HTML too short")
    if not all(token in lower for token in ("<html", "<body", "<style", "<script")):
        issues.append("missing html/body/style/script")
    if not any(t in lower for t in ("login", "log in", "sign in", "signin")):
        issues.append("missing login screen")
    if not any(t in lower for t in ("sign up", "signup", "register", "create account", "join")):
        issues.append("missing sign-up screen")
    if not any(t in lower for t in ("bottom-nav", "bottomnav", "tabbar", "tab-bar", "nav", "tab", "bottom")):
        issues.append("missing bottom navigation")
    has_images = "<img" in lower and any(
        token in lower
        for token in (
            "picsum.photos",
            "wikimedia",
            "upload.wikimedia.org",
            "loremflickr.com",
            'src="http',
            "src='http",
        )
    )
    if not has_images:
        issues.append("missing https image URLs")
    return "; ".join(issues) or "structure invalid"


def enrich_preview_html(html: str, state: AIFactoryState) -> str:
    """Inject niche images and finalize before validation."""
    labels = labels_from_state(
        client_brief=state.client_brief,
        requirements_doc=state.requirements_doc,
        code_artifacts=state.code_artifacts,
        project_name=state.project_name,
    )
    image_map = resolve_images_for_labels(
        labels,
        run_id=state.run_id,
        client_brief=state.client_brief,
        requirements_doc=state.requirements_doc,
        code_artifacts=state.code_artifacts,
        project_name=state.project_name,
    )
    html = apply_images_to_html(html, image_map)
    lower = html.lower()
    if image_map and (
        "<img" not in lower
        or not any(t in lower for t in ('src="http', "src='http", "wikimedia", "loremflickr"))
    ):
        hero_url = next(iter(image_map.values()))
        hero = f'<img src="{hero_url}" alt="{labels[0]}" style="display:none" aria-hidden="true"/>'
        html = re.sub(r"(<body[^>]*>)", rf"\1{hero}", html, count=1, flags=re.IGNORECASE)
    return finalize_preview_html(html).html


def validate_preview_html(html: str) -> bool:
    if not html or len(html) < 400:
        return False
    lower = html.lower()
    if not all(token in lower for token in ("<html", "<body", "<style", "<script")):
        return False
    has_login = any(
        token in lower for token in ("login", "log in", "sign in", "signin")
    )
    has_signup = any(
        token in lower
        for token in ("sign up", "signup", "register", "create account", "join")
    )
    if not (has_login and has_signup):
        return False
    has_nav = any(
        token in lower
        for token in ("bottom-nav", "bottomnav", "tabbar", "tab-bar", "nav", "tab", "bottom")
    )
    if not has_nav:
        return False
    has_images = "<img" in lower and any(
        token in lower
        for token in (
            "picsum.photos",
            "wikimedia",
            "upload.wikimedia.org",
            "loremflickr.com",
            "src=\"http",
        )
    )
    if not has_images:
        return False
    return True


def generate_ui_preview_html(state: AIFactoryState) -> str:
    """Run the UI Designer agent and return HTML for the browser preview."""
    brief = (state.client_brief or "")[:1200]
    prd = (state.requirements_doc or "")[:3500]
    profile = _infer_app_profile(brief, prd)
    goal = _goal_for_profile(profile)
    last_issue = ""
    for attempt in range(3):
        raw = run_basic_agent(
            ui_preview_prompt(
                state,
                attempt=attempt,
                retry_note=last_issue,
            ),
            role="Senior UI Designer",
            goal=goal,
        )
        html = extract_html_from_response(raw)
        if not html:
            last_issue = "Output must be a complete HTML document only (no markdown fences or commentary)."
            continue
        html = enrich_preview_html(html, state)
        if validate_preview_html(html):
            return html
        last_issue = _validation_feedback(html)
    raise ValueError(
        f"UI preview HTML failed validation after 3 attempts ({last_issue})."
    )
