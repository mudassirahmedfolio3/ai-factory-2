"""Fetch a random e-commerce app brief from the public web."""

from __future__ import annotations

import json
import random
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class EcommerceBrief:
    project_name: str
    client_brief: str
    niche: str
    source: str


_USER_AGENT = "AIFactory/1.0 (ecommerce brief generator)"
_TIMEOUT = 12

# Seeds when live APIs are unreachable — still e-commerce niches.
_FALLBACK_NICHES: list[tuple[str, str]] = [
    ("artisan-coffee-shop", "Specialty coffee beans, brewing gear, and subscription boxes for home baristas."),
    ("vintage-vinyl-market", "Second-hand vinyl records, turntables, and collector-grade album listings."),
    ("pet-supplies-hub", "Organic pet food, toys, grooming kits, and vet-recommended accessories."),
    ("outdoor-camping-gear", "Tents, backpacks, portable stoves, and trail-ready apparel for weekend campers."),
    ("handmade-jewelry-boutique", "Artisan rings, necklaces, and custom engraving for gift buyers."),
    ("plant-parent-shop", "Indoor plants, ceramic pots, grow lights, and care guides for urban gardeners."),
    ("sneaker-resale-store", "Limited-edition sneakers, size filters, and authenticity badges for collectors."),
    ("zero-waste-grocery", "Refillable pantry staples, reusable containers, and local delivery slots."),
    ("board-game-paradise", "Strategy board games, expansions, and family party game bundles."),
    ("fitness-protein-market", "Protein powders, resistance bands, and meal-prep containers for athletes."),
]


def _http_get_json(url: str) -> object | None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:48] or "ecommerce-app"


def _fetch_dummyjson_seed() -> tuple[str, str, str] | None:
    """Return (niche_label, sample_product, category_slug) from DummyJSON."""
    categories = _http_get_json("https://dummyjson.com/products/categories")
    if not isinstance(categories, list) or not categories:
        return None

    cat = random.choice(categories)
    if not isinstance(cat, dict):
        return None
    slug = str(cat.get("slug", "")).strip()
    label = str(cat.get("name", slug)).strip().title()
    if not slug:
        return None

    products_payload = _http_get_json(f"https://dummyjson.com/products/category/{slug}?limit=20")
    sample = ""
    if isinstance(products_payload, dict):
        products = products_payload.get("products")
        if isinstance(products, list) and products:
            item = random.choice(products)
            if isinstance(item, dict):
                title = str(item.get("title", "")).strip()
                price = item.get("price")
                if title:
                    sample = title
                    if isinstance(price, (int, float)):
                        sample += f" (${price:.2f})"

    return label, sample, _slugify(slug or label)


def _fetch_wikipedia_blurb(search_term: str) -> str:
    """One-sentence context from Wikipedia search + summary."""
    query = urllib.parse.quote(search_term)
    search = _http_get_json(
        f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=1&namespace=0&format=json"
    )
    if not isinstance(search, list) or len(search) < 2:
        return ""
    titles = search[1]
    if not titles or not isinstance(titles[0], str):
        return ""
    title = titles[0]
    summary = _http_get_json(
        "https://en.wikipedia.org/api/rest_v1/page/summary/"
        + urllib.parse.quote(title.replace(" ", "_"))
    )
    if isinstance(summary, dict):
        extract = str(summary.get("extract", "")).strip()
        if extract:
            first = extract.split(". ")[0].strip()
            if first and not first.endswith("."):
                first += "."
            return first
    return ""


def fetch_random_ecommerce_brief() -> EcommerceBrief:
    """Build a unique e-commerce MVP brief using live web sources."""
    niche_label = ""
    sample_product = ""
    project_name = ""
    sources: list[str] = []

    seed = _fetch_dummyjson_seed()
    if seed:
        niche_label, sample_product, project_name = seed
        sources.append("dummyjson.com")

    if not niche_label:
        project_name, desc = random.choice(_FALLBACK_NICHES)
        niche_label = project_name.replace("-", " ").title()
        sample_product = desc.split(".")[0]
        sources.append("local-fallback")

    wiki = _fetch_wikipedia_blurb(f"{niche_label} online retail ecommerce")
    if wiki:
        sources.append("wikipedia.org")

    feature_pool = [
        "product catalog with search and filters",
        "shopping cart with quantity updates",
        "guest checkout and registered accounts",
        "order confirmation email",
        "wishlist or favorites",
        "product reviews and star ratings",
        "promo codes at checkout",
        "order history",
    ]
    features = random.sample(feature_pool, k=4)

    brief_parts = [
        f"Build a Flutter e-commerce MVP for **{niche_label}**.",
        f"Target shoppers interested in this vertical.",
    ]
    if wiki:
        brief_parts.append(f"Market context: {wiki}")
    if sample_product:
        brief_parts.append(f"Example listing style: {sample_product}.")
    brief_parts.append(
        "MVP must include: " + ", ".join(features) + "."
    )
    brief_parts.append(
        "Mobile-first UX, small releasable increment, demo-ready in one sprint."
    )

    return EcommerceBrief(
        project_name=project_name,
        client_brief=" ".join(brief_parts),
        niche=niche_label,
        source="+".join(sources),
    )
