"""Tests for web image resolution."""

from __future__ import annotations

from ai_factory.web_images import (
    apply_images_to_html,
    fetch_image_url,
    niche_keywords,
    resolve_images_for_labels,
)


def test_niche_keywords_blog():
    kw = niche_keywords("Build a blog app for writers", item="Morning writing routine")
    assert "blog" in kw or "writing" in kw or "morning" in kw


def test_niche_keywords_bags():
    kw = niche_keywords("Women's handbags ecommerce MVP", item="Leather tote bag")
    assert "handbag" in kw or "leather" in kw or "tote" in kw


def test_fetch_image_url_returns_https():
    asset = fetch_image_url("women handbag fashion")
    assert asset.url.startswith("https://")
    assert asset.source in ("wikimedia", "loremflickr")


def test_apply_images_to_html_by_alt():
    mapping = {"Green Oval Earring": "https://upload.wikimedia.org/example.jpg"}
    html = '<img alt="Green Oval Earring" src="https://picsum.photos/seed/x/400/300"/>'
    out = apply_images_to_html(html, mapping)
    assert "upload.wikimedia.org/example.jpg" in out
    assert "picsum.photos" not in out


def test_resolve_images_caches(monkeypatch, tmp_path):
    from ai_factory import web_images as wi

    monkeypatch.setattr(wi, "CACHE_DIR", tmp_path)
    calls = {"n": 0}

    def fake_fetch(keyword, **kwargs):
        calls["n"] += 1
        from ai_factory.web_images import ImageAsset

        return ImageAsset(label=keyword, keyword=keyword, url=f"https://example.com/{calls['n']}", source="test")

    monkeypatch.setattr(wi, "fetch_image_url", fake_fetch)
    first = resolve_images_for_labels(["Rose Gold Hoop"], run_id="run-test")
    second = resolve_images_for_labels(["Rose Gold Hoop"], run_id="run-test")
    assert first == second
    assert calls["n"] == 1
