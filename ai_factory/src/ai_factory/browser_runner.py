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
    else:
        defaults = [
            ("Featured Item A", 79.99),
            ("Featured Item B", 24.50),
            ("Featured Item C", 18.00),
            ("Featured Item D", 89.00),
        ]
    return defaults[:4]


def build_preview_html(
    project_name: str,
    client_brief: str,
    code_artifacts: str,
    requirements_doc: str = "",
) -> str:
    products = _extract_products(requirements_doc, code_artifacts, client_brief)
    accent, bg, grad_end = _theme_for_project(project_name)
    display_name = project_name.replace("-", " ").title()
    product_cards = "\n".join(
        f"""
        <article class="product" data-name="{quote(name)}" data-price="{price}">
          <div class="thumb">{name[0]}</div>
          <h3>{name}</h3>
          <p class="price">${price:.2f}</p>
          <button type="button" class="add">Add to cart</button>
        </article>"""
        for name, price in products
    )
    brief = (client_brief or "E-commerce MVP preview")[:220].replace("<", "&lt;")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{display_name} — AI Factory Preview</title>
  <style>
    :root {{
      --bg: {bg}; --card: #1e293b; --accent: {accent}; --text: #f1f5f9; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; min-height: 100vh; font-family: system-ui, sans-serif;
      background: linear-gradient(160deg, var(--bg) 0%, {grad_end} 100%); color: var(--text);
      display: flex; justify-content: center; padding: 24px 12px;
    }}
    .phone {{
      width: min(390px, 100%); background: var(--bg); border-radius: 28px;
      box-shadow: 0 24px 80px rgba(0,0,0,.45); overflow: hidden; border: 1px solid #334155;
    }}
    header {{
      padding: 16px 20px; display: flex; justify-content: space-between; align-items: center;
      background: rgba(15,23,42,.9); border-bottom: 1px solid #334155;
    }}
    header h1 {{ font-size: 1rem; margin: 0; }}
    .badge {{
      background: var(--accent); color: #042f2e; font-weight: 700; font-size: .75rem;
      padding: 4px 10px; border-radius: 999px;
    }}
    .brief {{ padding: 12px 20px; font-size: .8rem; color: var(--muted); border-bottom: 1px solid #1e293b; }}
    .grid {{ padding: 16px; display: grid; gap: 12px; }}
    .product {{
      background: var(--card); border-radius: 16px; padding: 14px; border: 1px solid #334155;
    }}
    .thumb {{
      width: 48px; height: 48px; border-radius: 12px; background: var(--accent); color: #042f2e;
      display: grid; place-items: center; font-weight: 800; font-size: 1.2rem; margin-bottom: 8px;
    }}
    .product h3 {{ margin: 0 0 4px; font-size: .95rem; }}
    .price {{ margin: 0 0 10px; color: var(--accent); font-weight: 600; }}
    .add {{
      width: 100%; border: 0; border-radius: 10px; padding: 10px; cursor: pointer;
      background: var(--accent); color: #042f2e; font-weight: 600;
    }}
    .toast {{
      position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
      background: #042f2e; color: var(--accent); padding: 10px 18px; border-radius: 999px;
      font-size: .85rem; opacity: 0; transition: opacity .2s; pointer-events: none;
    }}
    .toast.show {{ opacity: 1; }}
  </style>
</head>
<body>
  <div class="phone">
    <header>
      <h1>{display_name}</h1>
      <span class="badge" id="cart">Cart: 0</span>
    </header>
    <p class="brief">{brief}</p>
    <div class="grid">{product_cards}</div>
  </div>
  <div class="toast" id="toast">Added to cart</div>
  <script>
    let count = 0;
    const cart = document.getElementById('cart');
    const toast = document.getElementById('toast');
    document.querySelectorAll('.add').forEach(btn => {{
      btn.addEventListener('click', () => {{
        count++;
        cart.textContent = 'Cart: ' + count;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 1200);
      }});
    }});
  </script>
</body>
</html>"""


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

    from ai_factory.ui_preview_agent import validate_preview_html

    if ui_html and validate_preview_html(ui_html):
        html = ui_html
    else:
        html = build_preview_html(project_name, client_brief, code_artifacts, requirements_doc)
    index = preview_dir / "index.html"
    index.write_text(html, encoding="utf-8")

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
    )
