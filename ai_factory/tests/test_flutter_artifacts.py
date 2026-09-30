"""Tests for Flutter artifact materialization helpers."""

from __future__ import annotations

from ai_factory.flutter_artifacts import (
    _class_name,
    _extract_dart_blocks,
    _fallback_files,
    _parse_project_json,
    _safe_relative_path,
    _slug,
    artifacts_enabled,
)
from ai_factory.models import AIFactoryState


def test_slug_and_class_name():
    assert _slug("Atelier Verde!") == "atelier_verde"
    assert _class_name("furniture_shop") == "FurnitureShop"
    assert _class_name("123_app").startswith("App")


def test_extract_dart_blocks():
    md = "## Sample\n\n```dart\nclass Foo {}\n```\n"
    assert _extract_dart_blocks(md) == ["class Foo {}"]


def test_parse_project_json_with_surrounding_text():
    raw = 'Here is JSON:\n{"package_name": "demo_app", "files": []}\nDone.'
    parsed = _parse_project_json(raw)
    assert parsed["package_name"] == "demo_app"


def test_safe_relative_path_blocks_traversal():
    assert _safe_relative_path("lib/main.dart") == "lib/main.dart"
    assert _safe_relative_path("../secret.txt") is None
    assert _safe_relative_path("android/app/build.gradle") is None


def test_fallback_files_from_build_sketch():
    state = AIFactoryState(
        project_name="Furniture Shop",
        code_artifacts="```dart\nclass SearchScreen extends StatelessWidget {\n  @override\n  Widget build(BuildContext c) => SizedBox();\n}\n```",
    )
    files = _fallback_files(state, "furniture_shop")
    paths = {f["path"] for f in files}
    assert "lib/main.dart" in paths
    assert any(p.startswith("lib/screens/") for p in paths)
    assert "pubspec.yaml" in paths


def test_artifacts_enabled_default():
    assert artifacts_enabled() is True
