"""Generate a mobile-style web preview and open it in the browser — no Flutter needed."""

from __future__ import annotations

import hashlib
import re
import socket
import threading
import webbrowser
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

PREVIEWS_DIR = Path("apps")

_SERVERS: dict[str, ThreadingHTTPServer] = {}


@dataclass
class BrowserRunResult:
    success: bool
    message: str
    preview_dir: Path | None = None
    url: str | None = None
    log: str = ""
    preview_qa: dict | None = None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _theme_for_project(project_name: str) -> tuple[str, str, str]:
    """Deterministic accent + gradient per project so previews look distinct."""
    digest = hashlib.sha256(project_name.encode()).hexdigest()
    palettes = [
        ("#06b6d4", "#0f172a", "#134e4a"),
        ("#f97316", "#1c1917", "#7c2d12"),
        ("#a855f7", "#1e1b4b", "#581c87"),
        ("#22c55e", "#052e16", "#14532d"),
        ("#ec4899", "#500724", "#831843"),
        ("#eab308", "#422006", "#713f12"),
        ("#3b82f6", "#0c1929", "#1e3a8a"),
        ("#14b8a6", "#042f2e", "#115e59"),
    ]
    idx = int(digest[:2], 16) % len(palettes)
    return palettes[idx]


def _extract_products(*sources: str) -> list[tuple[str, float]]:
    """Pull product-like names from PRD/build artifacts, else use defaults."""
    combined = "\n".join(s for s in sources if s)
    priced: list[tuple[str, float]] = []

    for match in re.finditer(
        r"([A-Z][A-Za-z0-9' /&-]{2,45})\s*(?:[-–—:]\s*)?\$(\d+(?:\.\d{2})?)",
        combined,
    ):
        priced.append((match.group(1).strip(), float(match.group(2))))

    names: list[str] = []
    for pattern in (
        r"Product\(['\"]([^'\"]+)['\"]",
        r"(?:product|item|listing|sku)[:\s]+([A-Z][^\n,.]{2,45})",
        r"Example listing[^:]*:\s*([^\n($]{3,45})",
        r"^\s*[-*]\s+(?:\*\*)?([A-Z][^:\n*$]{3,45})(?:\*\*)?(?:\s*[-–—]|\s*\$|\s*:|\s*$)",
    ):
        names.extend(re.findall(pattern, combined, re.MULTILINE | re.IGNORECASE))

    skip = {
        "architecture", "sprint scope", "mvp", "goal", "catalog", "cart", "checkout",
        "flutter", "release", "user story", "acceptance", "market context",
    }
    seen: set[str] = set()
    products: list[tuple[str, float]] = []

    for name, price in priced:
        key = name.lower()
        if len(key) < 3 or key in skip or key in seen:
            continue
        seen.add(key)
        products.append((name, price))

    for name in names:
        key = name.strip().lower()
        if len(key) < 3 or key in skip or key in seen:
            continue
        seen.add(key)
        products.append((name.strip(), round(12.99 + len(products) * 17.25, 2)))

    if products:
        return products[:6]

    # Niche-flavored defaults from brief keywords
    lower = combined.lower()
    if any(w in lower for w in ("coffee", "espresso", "bean")):
        defaults = [("Ethiopian Single Origin", 18.50), ("Ceramic Pour-Over", 34.00), ("Cold Brew Kit", 29.99)]
    elif any(w in lower for w in ("pet", "dog", "cat")):
        defaults = [("Organic Kibble 5kg", 42.00), ("Chew Toy Bundle", 15.99), ("Grooming Brush", 12.50)]
    elif any(w in lower for w in ("vinyl", "record", "music")):
        defaults = [("Jazz Classics LP", 24.99), ("Turntable Mat", 19.00), ("Record Cleaner", 14.50)]
    elif any(w in lower for w in ("plant", "garden", "succulent")):
        defaults = [("Monstera Deliciosa", 38.00), ("Terracotta Planter", 16.00), ("Grow Light Bulb", 22.99)]
    elif any(w in lower for w in ("sneaker", "shoe", "footwear")):
        defaults = [("Retro Runner", 129.00), ("Canvas Low-Top", 59.99), ("Performance Socks 3pk", 18.00)]
    elif any(w in lower for w in ("wallet", "wallets", "leather")):
        defaults = [
            ("Classic Bifold Wallet", 49.99),
            ("Slim Card Holder", 34.00),
            ("Travel Zip Wallet", 62.00),
            ("Minimalist Money Clip", 28.50),
        ]
    else:
        defaults = [
            ("Featured Item A", 79.99),
            ("Featured Item B", 24.50),
            ("Featured Item C", 18.00),
            ("Featured Item D", 89.00),
        ]
    return defaults[:4]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "item"


def _extract_articles(*sources: str) -> list[tuple[str, str]]:
    """Article titles + short excerpts for blog-style fallbacks."""
    combined = "\n".join(s for s in sources if s)
    titles: list[str] = []
    for pattern in (
        r"^\s*[-*#]\s+(?:\*\*)?([A-Z][^:\n*$]{8,70})(?:\*\*)?(?:\s*$|\s*[-–—])",
        r"(?:article|post|topic)[:\s]+([A-Z][^\n,.]{8,70})",
    ):
        titles.extend(re.findall(pattern, combined, re.MULTILINE | re.IGNORECASE))
    seen: set[str] = set()
    articles: list[tuple[str, str]] = []
    for title in titles:
        key = title.strip().lower()
        if len(key) < 8 or key in seen:
            continue
        seen.add(key)
        excerpt = f"Notes on {title.strip().lower()} — from your brief."
        articles.append((title.strip(), excerpt))
    if articles:
        return articles[:6]
    lower = combined.lower()
    if any(w in lower for w in ("blog", "article", "writer", "publish")):
        return [
            ("Morning pages for busy founders", "How a 15-minute writing ritual unlocks clarity."),
            ("Publishing without perfectionism", "Ship drafts, gather feedback, iterate in public."),
            ("Building a niche readership", "Find your angle and stay consistent."),
            ("Editorial workflow on mobile", "Draft, edit, and schedule from your phone."),
        ]
    slug = (combined[:40] or "Project").strip().title()
    return [
        (f"{slug} — getting started", "Overview of the core workflow from your brief."),
        (f"{slug} — deep dive", "Key features and how users accomplish their goals."),
        (f"{slug} — best practices", "Tips for getting the most from the app."),
    ]


def _shared_fallback_shell(
    *,
    project_name: str,
    client_brief: str,
    run_id: str,
    main_grid_html: str,
    home_heading: str,
    home_sub: str,
    tabs: list[tuple[str, str, str]],
    third_screen_id: str,
    third_screen_title: str,
    third_screen_body: str,
) -> str:
    accent, bg, grad_end = _theme_for_project(f"{run_id}:{project_name}")
    display_name = project_name.replace("-", " ").title()
    variant = int(hashlib.sha256(f"{run_id}:{project_name}".encode()).hexdigest()[:2], 16) % 3
    font_stack = (
        "Georgia, serif",
        "system-ui, sans-serif",
        "'Segoe UI', Tahoma, sans-serif",
    )[variant]
    card_cols = "1fr 1fr" if variant != 2 else "1fr"
    brief = (client_brief or "Mobile MVP preview")[:180].replace("<", "&lt;")
    tab_buttons = "\n".join(
        f'<button class="tab{" on" if i == 0 else ""}" data-tab="{tab_id}" type="button">{label}</button>'
        for i, (tab_id, label, _) in enumerate(tabs)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{display_name}</title>
<style>
:root{{--accent:{accent};--bg:{bg};--grad:{grad_end};--text:#f8fafc;--muted:#94a3b8;--card:#1e293b}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:{font_stack};background:linear-gradient(165deg,var(--bg),var(--grad));color:var(--text);display:flex;justify-content:center;min-height:100vh}}
.app{{width:100%;max-width:390px;min-height:100vh;background:var(--bg);position:relative;padding-bottom:64px}}
.screen{{display:none;flex-direction:column;min-height:calc(100vh - 64px)}}
.screen.active{{display:flex}}
.auth{{padding:40px 24px;justify-content:center}}
.auth h1{{font-size:1.6rem;color:var(--accent);text-align:center;margin-bottom:6px}}
.auth p{{text-align:center;color:var(--muted);font-size:.85rem;margin-bottom:24px}}
.field{{margin-bottom:12px}}
.field label{{display:block;font-size:.72rem;color:var(--muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.06em}}
.field input{{width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0f172a;color:var(--text)}}
.btn{{width:100%;padding:13px;border:none;border-radius:10px;font-weight:600;cursor:pointer;margin-top:8px}}
.btn-primary{{background:var(--accent);color:#0f172a}}
.btn-link{{background:none;color:var(--accent);font-size:.9rem;margin-top:14px}}
.top{{padding:14px 16px;border-bottom:1px solid #334155}}
.top h2{{font-size:1.1rem}}
.top small{{color:var(--muted);font-size:.75rem}}
.hero{{margin:12px 16px;padding:18px;border-radius:14px;background:linear-gradient(135deg,var(--accent),var(--grad))}}
.hero b{{display:block;font-size:1rem;margin-bottom:4px}}
.hero span{{font-size:.8rem;opacity:.9}}
.grid{{display:grid;grid-template-columns:{card_cols};gap:10px;padding:12px 16px 20px}}
.card{{background:var(--card);border-radius:12px;overflow:hidden;border:1px solid #334155}}
.card img{{width:100%;height:120px;object-fit:cover;display:block}}
.card-body{{padding:10px}}
.card-body h3{{font-size:.85rem;line-height:1.3;margin-bottom:4px}}
.card-body p{{font-size:.72rem;color:var(--muted);line-height:1.4}}
.price{{color:var(--accent);font-weight:700;font-size:.9rem;margin-bottom:8px}}
.add-btn{{width:100%;padding:8px;border:none;border-radius:8px;background:var(--accent);color:#0f172a;font-weight:600;cursor:pointer;font-size:.75rem}}
.profile{{padding:24px 16px;text-align:center}}
.avatar{{width:56px;height:56px;border-radius:50%;background:var(--accent);color:#0f172a;display:grid;place-items:center;margin:0 auto 10px;font-weight:700}}
.bottom-nav{{position:fixed;bottom:0;width:100%;max-width:390px;display:flex;background:#0f172a;border-top:1px solid #334155}}
.tab{{flex:1;padding:10px 4px;text-align:center;background:none;border:none;color:var(--muted);font-size:.65rem;cursor:pointer}}
.tab.on{{color:var(--accent)}}
</style>
</head>
<body>
<div class="app">
  <section class="screen active" id="login">
    <div class="auth"><h1>{display_name}</h1><p>{brief}</p>
    <div class="field"><label>Email</label><input id="loginEmail" type="email" placeholder="you@example.com"/></div>
    <div class="field"><label>Password</label><input id="loginPass" type="password" placeholder="••••••••"/></div>
    <button class="btn btn-primary" id="loginBtn" type="button">Log in</button>
    <button class="btn btn-link" id="toSignup" type="button">Sign up</button></div>
  </section>
  <section class="screen" id="signup">
    <div class="auth"><h1>Create account</h1><p>Join {display_name}</p>
    <div class="field"><label>Name</label><input id="suName" type="text"/></div>
    <div class="field"><label>Email</label><input id="suEmail" type="email"/></div>
    <div class="field"><label>Password</label><input id="suPass" type="password"/></div>
    <button class="btn btn-primary" id="signupBtn" type="button">Register</button>
    <button class="btn btn-link" id="toLogin" type="button">Back to login</button></div>
  </section>
  <section class="screen" id="home">
    <div class="top"><h2>{home_heading}</h2><small>{home_sub}</small></div>
    <div class="hero"><b>{display_name}</b><span>{brief[:80]}</span></div>
    <div class="grid" id="catalog">{main_grid_html}</div>
  </section>
  <section class="screen" id="{third_screen_id}">
    <div class="top"><h2>{third_screen_title}</h2></div>
    <div class="profile"><p style="padding:16px;color:var(--muted);font-size:.85rem;line-height:1.5">{third_screen_body}</p></div>
  </section>
  <section class="screen" id="profile">
    <div class="profile"><div class="avatar" id="avatar">U</div><h3 id="userName">Guest</h3><p id="userEmail" style="color:var(--muted);font-size:.85rem">demo@example.com</p></div>
  </section>
  <nav class="bottom-nav" id="bottomNav" style="display:none">
    {tab_buttons}
  </nav>
</div>
<script>
function show(id){{document.querySelectorAll('.screen').forEach(function(s){{s.classList.remove('active')}});var el=document.getElementById(id);if(el)el.classList.add('active')}}
function enterApp(u){{document.getElementById('bottomNav').style.display='flex';document.getElementById('userName').textContent=u.name;document.getElementById('userEmail').textContent=u.email;document.getElementById('avatar').textContent=(u.name||'U')[0].toUpperCase();show('home')}}
document.getElementById('toSignup').addEventListener('click',function(){{show('signup')}});
document.getElementById('toLogin').addEventListener('click',function(){{show('login')}});
document.getElementById('loginBtn').addEventListener('click',function(){{if(document.getElementById('loginEmail').value&&document.getElementById('loginPass').value)enterApp({{name:'Guest',email:document.getElementById('loginEmail').value}})}});
document.getElementById('signupBtn').addEventListener('click',function(){{if(document.getElementById('suName').value)enterApp({{name:document.getElementById('suName').value,email:document.getElementById('suEmail').value||'demo@example.com'}})}});
document.querySelectorAll('.tab').forEach(function(tab){{tab.addEventListener('click',function(){{document.querySelectorAll('.tab').forEach(function(t){{t.classList.remove('on')}});tab.classList.add('on');show(tab.dataset.tab)}})}});
</script>
</body>
</html>"""


def build_preview_html(
    project_name: str,
    client_brief: str,
    code_artifacts: str,
    requirements_doc: str = "",
    run_id: str = "",
) -> str:
    """Rich fallback when the UI Designer agent fails — brief-aware, not one static shop."""
    from ai_factory.ui_preview_agent import _infer_app_profile

    profile = _infer_app_profile(client_brief, requirements_doc)
    if profile["kind"] == "blog":
        return _build_blog_fallback_html(
            project_name, client_brief, code_artifacts, requirements_doc, run_id
        )
    if profile["kind"] == "custom":
        return _build_custom_fallback_html(
            project_name, client_brief, code_artifacts, requirements_doc, run_id
        )
    return _build_shop_fallback_html(
        project_name, client_brief, code_artifacts, requirements_doc, run_id
    )


def _build_shop_fallback_html(
    project_name: str,
    client_brief: str,
    code_artifacts: str,
    requirements_doc: str = "",
    run_id: str = "",
) -> str:
    from ai_factory.web_images import resolve_images_for_labels

    products = _extract_products(requirements_doc, code_artifacts, client_brief)
    image_map = resolve_images_for_labels(
        [name for name, _ in products],
        run_id=run_id,
        client_brief=client_brief,
        requirements_doc=requirements_doc,
        code_artifacts=code_artifacts,
        project_name=project_name,
    )
    product_cards = "\n".join(
        f"""<article class="card" data-name="{name}" data-price="{price}">
          <img src="{image_map.get(name, f'https://loremflickr.com/400/280/{_slug(name)}')}" alt="{name}" loading="lazy"/>
          <div class="card-body"><h3>{name}</h3><p class="price">${price:.2f}</p>
          <button type="button" class="add-btn">Add to cart</button></div></article>"""
        for name, price in products
    )
    return _shared_fallback_shell(
        project_name=project_name,
        client_brief=client_brief,
        run_id=run_id,
        main_grid_html=product_cards,
        home_heading=project_name.replace("-", " ").title(),
        home_sub="Curated for you",
        tabs=[("home", "Shop", "home"), ("cart", "Cart", "cart"), ("profile", "Profile", "profile")],
        third_screen_id="cart",
        third_screen_title="Cart",
        third_screen_body="Your cart is empty — browse the catalog and add items.",
    )


def _build_blog_fallback_html(
    project_name: str,
    client_brief: str,
    code_artifacts: str,
    requirements_doc: str = "",
    run_id: str = "",
) -> str:
    from ai_factory.web_images import resolve_images_for_labels

    articles = _extract_articles(requirements_doc, code_artifacts, client_brief)
    labels = [title for title, _ in articles]
    image_map = resolve_images_for_labels(
        labels,
        run_id=run_id,
        client_brief=client_brief,
        requirements_doc=requirements_doc,
        code_artifacts=code_artifacts,
        project_name=project_name,
    )
    article_cards = "\n".join(
        f"""<article class="card">
          <img src="{image_map.get(title, f'https://loremflickr.com/400/280/{_slug(title)}')}" alt="{title}" loading="lazy"/>
          <div class="card-body"><h3>{title}</h3><p>{excerpt}</p></div></article>"""
        for title, excerpt in articles
    )
    return _shared_fallback_shell(
        project_name=project_name,
        client_brief=client_brief,
        run_id=run_id,
        main_grid_html=article_cards,
        home_heading="Feed",
        home_sub="Latest from your brief",
        tabs=[("home", "Feed", "home"), ("compose", "Compose", "compose"), ("profile", "Profile", "profile")],
        third_screen_id="compose",
        third_screen_title="Compose",
        third_screen_body="Draft your next article here — title, body, and publish when ready.",
    )


def _build_custom_fallback_html(
    project_name: str,
    client_brief: str,
    code_artifacts: str,
    requirements_doc: str = "",
    run_id: str = "",
) -> str:
    from ai_factory.web_images import resolve_images_for_labels

    combined = f"{client_brief}\n{requirements_doc}\n{code_artifacts}"
    features: list[str] = []
    for match in re.finditer(r"^\s*[-*]\s+([A-Z][^\n]{4,50})", combined, re.MULTILINE):
        features.append(match.group(1).strip())
    if not features:
        features = [
            "Core workflow",
            "Dashboard overview",
            "Saved items",
            "Settings & profile",
        ]
    labels = features[:4]
    image_map = resolve_images_for_labels(
        labels,
        run_id=run_id,
        client_brief=client_brief,
        requirements_doc=requirements_doc,
        code_artifacts=code_artifacts,
        project_name=project_name,
    )
    feature_cards = "\n".join(
        f"""<article class="card">
          <img src="{image_map.get(label, f'https://loremflickr.com/400/280/{_slug(label)}')}" alt="{label}" loading="lazy"/>
          <div class="card-body"><h3>{label}</h3><p>Tap to open this workflow from your brief.</p></div></article>"""
        for label in labels
    )
    return _shared_fallback_shell(
        project_name=project_name,
        client_brief=client_brief,
        run_id=run_id,
        main_grid_html=feature_cards,
        home_heading="Home",
        home_sub="Built from your brief",
        tabs=[("home", "Home", "home"), ("workspace", "Workspace", "workspace"), ("profile", "Profile", "profile")],
        third_screen_id="workspace",
        third_screen_title="Workspace",
        third_screen_body="Primary tools and workflows inferred from your project brief.",
    )


def _start_server(preview_dir: Path, port: int, run_id: str) -> ThreadingHTTPServer:
    """Serve only preview_dir — class-level directory is ignored by http.server on Windows."""
    base_dir = str(preview_dir.resolve())

    class PreviewHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=base_dir, **kwargs)

        def log_message(self, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), PreviewHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name=f"preview-{run_id}")
    thread.start()
    _SERVERS[run_id] = server
    return server


def run_browser_preview(
    *,
    run_id: str,
    project_name: str,
    client_brief: str,
    code_artifacts: str,
    requirements_doc: str = "",
    ui_html: str | None = None,
    open_browser: bool = True,
) -> BrowserRunResult:
    preview_dir = PREVIEWS_DIR / run_id
    preview_dir.mkdir(parents=True, exist_ok=True)

    from ai_factory.ui_preview_agent import finalize_preview_html, validate_preview_html

    if ui_html and validate_preview_html(ui_html):
        finalized = finalize_preview_html(ui_html)
    else:
        finalized = finalize_preview_html(
            build_preview_html(
                project_name,
                client_brief,
                code_artifacts,
                requirements_doc,
                run_id=run_id,
            )
        )
    index = preview_dir / "index.html"
    index.write_text(finalized.html, encoding="utf-8")
    preview_qa = {
        "js_valid_before": finalized.js_valid_before,
        "js_valid_after": finalized.js_valid_after,
        "repairs": finalized.repairs,
        "bootstrap_injected": finalized.bootstrap_injected,
    }

    port = _free_port()
    try:
        _start_server(preview_dir, port, run_id)
    except OSError as exc:
        return BrowserRunResult(
            success=False,
            message=f"Could not start preview server: {exc}",
            preview_dir=preview_dir,
            log=str(exc),
        )

    url = f"http://127.0.0.1:{port}/index.html"
    if open_browser:
        webbrowser.open(url)

    return BrowserRunResult(
        success=True,
        message="Preview opened in browser",
        preview_dir=preview_dir,
        url=url,
        log=f"Serving {index.as_posix()} at {url}",
        preview_qa=preview_qa,
    )
