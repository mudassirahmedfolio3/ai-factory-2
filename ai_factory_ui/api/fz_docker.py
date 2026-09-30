"""Docker readiness checks for ai_factory_fz build sandbox."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

# Images used by profiles/flutter_nestjs_ecommerce sandbox (pipeline.ui build phase).
FZ_DOCKER_IMAGES = [
    "node:24-bookworm",
    "ghcr.io/cirruslabs/flutter:stable",
    "openapitools/openapi-generator-cli:v7.10.0",
]


def docker_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def docker_status() -> dict[str, Any]:
    path = shutil.which("docker")
    if not path:
        return {
            "installed": False,
            "running": False,
            "message": "Docker CLI not found. Install Docker Desktop for Windows.",
        }
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            version = (result.stdout or "").strip()
            return {
                "installed": True,
                "running": True,
                "version": version,
                "message": "Docker is ready.",
            }
        err = (result.stderr or result.stdout or "").strip()
        return {
            "installed": True,
            "running": False,
            "message": err or "Docker is installed but not running. Start Docker Desktop.",
        }
    except subprocess.TimeoutExpired:
        return {
            "installed": True,
            "running": False,
            "message": "Docker did not respond in time. Start Docker Desktop.",
        }
    except OSError as exc:
        return {"installed": True, "running": False, "message": str(exc)}


def pull_fz_images() -> list[dict[str, str]]:
    """Pull sandbox images. Returns per-image status rows."""
    rows: list[dict[str, str]] = []
    if not docker_available():
        return [{"image": "*", "status": "skipped", "detail": "Docker not available"}]
    for image in FZ_DOCKER_IMAGES:
        try:
            result = subprocess.run(
                ["docker", "pull", image],
                capture_output=True,
                text=True,
                timeout=1800,
            )
            if result.returncode == 0:
                rows.append({"image": image, "status": "ok", "detail": "pulled"})
            else:
                detail = (result.stderr or result.stdout or "").strip()[-300:]
                rows.append({"image": image, "status": "failed", "detail": detail})
        except subprocess.TimeoutExpired:
            rows.append({"image": image, "status": "failed", "detail": "pull timed out"})
    return rows
