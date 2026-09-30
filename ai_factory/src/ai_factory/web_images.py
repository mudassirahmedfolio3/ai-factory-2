"""Resolve niche-relevant image URLs from the public web for previews and Flutter apps."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

CACHE_DIR = Path("artifacts/cache/web_images")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "item"
_USER_AGENT = "AIFactory/1.0 (preview image resolver)"
_WIKI_API = "https://commons.wikimedia.org/w/api.php"


@dataclass
class ImageAsset:
    label: str
    keyword: str
    url: str
    source: str


def _cache_path(run_id: str) -> Path:
    return CACHE_DIR / f"{run_id or 'default'}.json"


def _load_cache(run_id: str) -> dict[str, str]:
    path = _cache_path(run_id)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(run_id: str, mapping: dict[str, str]) -> None:
    path = _cache_path(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")


def _http_get_json(url: str, timeout: float = 8.0) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def niche_keywords(*texts: str, item: str = "") -> str:
    """Build a short image search phrase from brief, PRD, and item label."""
    combined = " ".join(t for t in texts if t).lower()
    item_words = re.sub(r"[^a-z0-9\s]", " ", item.lower()).split()
    stop = {
        "the",
        "and",
        "for",
        "with",
        "app",
        "mobile",
        "flutter",
        "mvp",
        "product",
        "item",
        "featured",
        "release",
        "screen",
        "view",
        "login",
        "signup",
    }
    topic_words: list[str] = []
    for word in re.sub(r"[^a-z0-9\s-]", " ", combined).split():
        if len(word) < 3 or word in stop:
            continue
        if word not in topic_words:
            topic_words.append(word)

    blog_markers = ("blog", "article", "post", "writer", "newsletter", "reading")
    shop_markers = ("shop", "store", "cart", "catalog", "ecommerce", "e-commerce", "retail")

    if any(m in combined for m in blog_markers) and not any(m in combined for m in shop_markers):
        base = ["blog", "writing", "article"]
    elif any(m in combined for m in ("jewell", "jewelry", "earring", "necklace", "bracelet")):
        base = ["jewellery", "accessory"]
    elif any(m in combined for m in ("bag", "handbag", "purse", "tote")):
        base = ["handbag", "women", "fashion"]
    elif any(m in combined for m in ("coffee", "espresso", "cafe")):
        base = ["coffee", "cafe"]
    elif any(m in combined for m in ("furniture", "sofa", "chair", "table")):
        base = ["furniture", "interior"]
    elif any(m in combined for m in shop_markers):
        base = ["product", "shopping"]
    else:
        base = topic_words[:2] or ["mobile", "app"]

    item_part = [w for w in item_words if w not in stop and len(w) > 2][:3]
    words = item_part + [w for w in base if w not in item_part]
    return " ".join(words[:5]).strip() or "product"


def _wikimedia_image_url(keyword: str, width: int = 400) -> str | None:
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "origin": "*",
            "generator": "search",
            "gsrsearch": keyword,
            "gsrnamespace": "6",
            "gsrlimit": "3",
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": str(width),
        }
    )
    payload = _http_get_json(f"{_WIKI_API}?{params}")
    if not payload:
        return None
    pages = (payload.get("query") or {}).get("pages") or {}
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        url = infos[0].get("thumburl") or infos[0].get("url")
        if url and url.startswith("https://"):
            return url
    return None


def _loremflickr_url(keyword: str, width: int, height: int) -> str:
    tags = ",".join(
        t
        for t in re.sub(r"[^a-z0-9\s,]", " ", keyword.lower()).split()
        if len(t) > 2
    )[:60] or "product"
    return f"https://loremflickr.com/{width}/{height}/{tags}"


def fetch_image_url(keyword: str, *, width: int = 400, height: int = 280) -> ImageAsset:
    wiki = _wikimedia_image_url(keyword, width=width)
    if wiki:
        return ImageAsset(label=keyword, keyword=keyword, url=wiki, source="wikimedia")
    flickr = _loremflickr_url(keyword, width, height)
    return ImageAsset(label=keyword, keyword=keyword, url=flickr, source="loremflickr")


def labels_from_state(
    *,
    client_brief: str = "",
    requirements_doc: str = "",
    code_artifacts: str = "",
    project_name: str = "",
    max_items: int = 8,
) -> list[str]:
    from ai_factory.browser_runner import _extract_products

    products = _extract_products(requirements_doc, code_artifacts, client_brief)
    labels = [name for name, _ in products]
    if labels:
        return labels[:max_items]

    combined = f"{client_brief}\n{requirements_doc}\n{project_name}"
    lower = combined.lower()
    if any(w in lower for w in ("blog", "article", "post", "writer")):
        return [
            "Morning writing routine",
            "Publishing your first post",
            "Building an audience",
            "Editorial workflow tips",
        ][:max_items]
    slug = project_name.replace("-", " ").title() or "Product"
    return [f"{slug} highlight {i + 1}" for i in range(min(4, max_items))]


def resolve_images_for_labels(
    labels: list[str],
    *,
    run_id: str = "",
    client_brief: str = "",
    requirements_doc: str = "",
    code_artifacts: str = "",
    project_name: str = "",
) -> dict[str, str]:
    cache = _load_cache(run_id)
    mapping: dict[str, str] = {}
    for label in labels:
        key = label.strip()
        if not key:
            continue
        if key in cache:
            mapping[key] = cache[key]
            continue
        keyword = niche_keywords(
            client_brief,
            requirements_doc,
            code_artifacts,
            project_name,
            item=key,
        )
        asset = fetch_image_url(keyword, width=400, height=280)
        mapping[key] = asset.url
        cache[key] = asset.url
    if run_id:
        _save_cache(run_id, cache)
    return mapping


def build_image_prompt_block(
    *,
    run_id: str = "",
    client_brief: str = "",
    requirements_doc: str = "",
    code_artifacts: str = "",
    project_name: str = "",
) -> str:
    labels = labels_from_state(
        client_brief=client_brief,
        requirements_doc=requirements_doc,
        code_artifacts=code_artifacts,
        project_name=project_name,
    )
    mapping = resolve_images_for_labels(
        labels,
        run_id=run_id,
        client_brief=client_brief,
        requirements_doc=requirements_doc,
        code_artifacts=code_artifacts,
        project_name=project_name,
    )
    if not mapping:
        return ""
    lines = [
        "WEB IMAGE URLS — use these exact https src values (real web photos relevant to the niche):"
    ]
    for label, url in mapping.items():
        lines.append(f'- "{label}": {url}')
    lines.append(
        "Do NOT use picsum.photos. Match each card/article img src to the closest label above."
    )
    return "\n".join(lines)


def apply_images_to_html(html: str, mapping: dict[str, str]) -> str:
    """Replace placeholder image URLs using img alt text or nearby product names."""
    if not html or not mapping:
        return html

    def _pick_url(alt: str, seed: str = "") -> str | None:
        alt_l = alt.lower().strip()
        if alt_l in mapping:
            return mapping[alt_l]
        for label, url in mapping.items():
            if label.lower() in alt_l or alt_l in label.lower():
                return url
        if seed:
            slug = _slug(seed)
            for label, url in mapping.items():
                if _slug(label) == slug:
                    return url
        return None

    def _replace_img(match: re.Match[str]) -> str:
        tag = match.group(0)
        alt_m = re.search(r'alt=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        alt = alt_m.group(1) if alt_m else ""
        seed_m = re.search(r"picsum\.photos/seed/([^/\"']+)", tag, re.IGNORECASE)
        seed = seed_m.group(1) if seed_m else ""
        url = _pick_url(alt, seed)
        if not url:
            return tag
        return re.sub(
            r'src=["\'][^"\']+["\']',
            f'src="{url}"',
            tag,
            count=1,
            flags=re.IGNORECASE,
        )

    updated = re.sub(r"<img\b[^>]*>", _replace_img, html, flags=re.IGNORECASE)

    for label, url in mapping.items():
        slug = _slug(label)
        updated = updated.replace(f"https://picsum.photos/seed/{slug}/", url + "/")
        updated = re.sub(
            rf"https://picsum\.photos/seed/{re.escape(slug)}/\d+/\d+",
            url,
            updated,
            flags=re.IGNORECASE,
        )
    return updated


def apply_images_to_dart(content: str, mapping: dict[str, str]) -> str:
    if not content or not mapping:
        return content
    updated = content
    for label, url in mapping.items():
        slug = _slug(label)
        updated = re.sub(
            rf"https://picsum\.photos/seed/{re.escape(slug)}/\d+",
            url,
            updated,
            flags=re.IGNORECASE,
        )
        updated = updated.replace(f"imageUrl: 'https://picsum.photos/seed/{slug}", f"imageUrl: '{url}")
    return updated
