"""Optional Flutter emulator launch — wraps the HTML preview in a real mobile app shell."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

PREVIEWS_DIR = Path("apps")


@dataclass
class EmulatorRunResult:
    success: bool
    message: str
    device_id: str | None = None
    project_dir: Path | None = None
    log: str = ""


def emulator_enabled() -> bool:
    return os.getenv("FLUTTER_EMULATOR", "").strip().lower() in ("1", "true", "yes")


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9_]+", "_", name.lower()).strip("_")
    return slug[:30] or "ai_factory_app"


def _android_preview_url(preview_url: str) -> str:
    """Map localhost preview server to Android emulator host."""
    parsed = urlparse(preview_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 80
    path = parsed.path or "/index.html"
    if host in ("127.0.0.1", "localhost"):
        host = "10.0.2.2"
    return f"http://{host}:{port}{path}"


def _pick_device(flutter: str) -> str | None:
    result = subprocess.run(
        [flutter, "devices"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return None
    for line in (result.stdout or "").splitlines():
        lower = line.lower()
        if "•" not in line or "chrome" in lower or "windows" in lower:
            continue
        if "emulator" in lower or "(mobile)" in lower or "android" in lower:
            parts = [p.strip() for p in line.split("•")]
            if len(parts) >= 2:
                return parts[1]
    return None


def _write_main_dart(path: Path, project_title: str, preview_url: str) -> None:
    safe_title = project_title.replace('"', "'")
    path.write_text(
        f'''import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

void main() {{
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const FactoryPreviewApp());
}}

class FactoryPreviewApp extends StatelessWidget {{
  const FactoryPreviewApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: {safe_title!r},
      theme: ThemeData(colorSchemeSeed: const Color(0xFF635BFF), useMaterial3: true),
      home: PreviewScreen(title: {safe_title!r}, url: {preview_url!r}),
    );
  }}
}}

class PreviewScreen extends StatefulWidget {{
  const PreviewScreen({{super.key, required this.title, required this.url}});
  final String title;
  final String url;

  @override
  State<PreviewScreen> createState() => _PreviewScreenState();
}}

class _PreviewScreenState extends State<PreviewScreen> {{
  late final WebViewController _controller;

  @override
  void initState() {{
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(Uri.parse(widget.url));
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: WebViewWidget(controller: _controller),
    );
  }}
}}
''',
        encoding="utf-8",
    )


def _ensure_pubspec_webview(pubspec: Path) -> None:
    text = pubspec.read_text(encoding="utf-8")
    if "webview_flutter" in text:
        return
    if "dependencies:" not in text:
        return
    text = text.replace(
        "dependencies:",
        "dependencies:\n  webview_flutter: ^4.10.0",
        1,
    )
    pubspec.write_text(text, encoding="utf-8")


def run_flutter_emulator(
    *,
    run_id: str,
    project_name: str,
    preview_url: str | None,
) -> EmulatorRunResult:
    """Launch a Flutter shell on an emulator that loads the HTML preview in a WebView."""
    if not emulator_enabled():
        return EmulatorRunResult(
            success=False,
            message="Flutter emulator disabled (set FLUTTER_EMULATOR=1 in ai_factory/.env)",
        )
    if not preview_url:
        return EmulatorRunResult(success=False, message="No preview URL to load in emulator")

    flutter = shutil.which("flutter")
    if not flutter:
        return EmulatorRunResult(
            success=False,
            message="Flutter SDK not found on PATH — install Flutter + Android Studio emulator",
        )

    device = _pick_device(flutter)
    if not device:
        return EmulatorRunResult(
            success=False,
            message="No Flutter device/emulator found — start an Android emulator first",
        )

    slug = _slug(project_name)
    project_dir = (PREVIEWS_DIR / run_id / "flutter_app").resolve()
    android_url = _android_preview_url(preview_url)

    if not (project_dir / "pubspec.yaml").exists():
        project_dir.parent.mkdir(parents=True, exist_ok=True)
        create = subprocess.run(
            [
                flutter,
                "create",
                "--org",
                "com.aifactory",
                "--project-name",
                slug,
                str(project_dir),
            ],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if create.returncode != 0:
            return EmulatorRunResult(
                success=False,
                message="flutter create failed",
                log=(create.stderr or create.stdout or "")[:2000],
            )

    _ensure_pubspec_webview(project_dir / "pubspec.yaml")
    _write_main_dart(project_dir / "lib" / "main.dart", project_name, android_url)

    pub_get = subprocess.run(
        [flutter, "pub", "get"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if pub_get.returncode != 0:
        return EmulatorRunResult(
            success=False,
            message="flutter pub get failed",
            log=(pub_get.stderr or pub_get.stdout or "")[:2000],
        )

    def _run() -> None:
        subprocess.run(
            [flutter, "run", "-d", device],
            cwd=project_dir,
            timeout=None,
            check=False,
        )

    threading.Thread(
        target=_run,
        name=f"flutter-emulator-{run_id}",
        daemon=True,
    ).start()

    return EmulatorRunResult(
        success=True,
        message=f"Flutter emulator launch started on {device}",
        device_id=device,
        project_dir=project_dir,
        log=f"WebView URL: {android_url}",
    )
