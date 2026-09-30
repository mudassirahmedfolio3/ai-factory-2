"""Launch generated Flutter apps on a local emulator from the console API."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import AI_FACTORY_FZ_ROOT, AI_FACTORY_ROOT, ARTIFACTS_DIR, FZ_RUNS_DIR

EMULATOR_DIR = ARTIFACTS_DIR / "emulator"
_lock = threading.Lock()
_active: dict[str, subprocess.Popen[Any]] = {}


def _flutter_executable() -> str:
    repo_root = AI_FACTORY_FZ_ROOT.parent
    name = "flutter.bat" if sys.platform == "win32" else "flutter"
    local = repo_root / ".tools" / "flutter" / "bin" / name
    if local.is_file():
        return str(local)
    return "flutter"


def _android_sdk_root() -> Path | None:
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        raw = os.getenv(key, "").strip()
        if raw:
            sdk = Path(raw)
            if sdk.is_dir():
                return sdk
    localappdata = os.getenv("LOCALAPPDATA", "").strip()
    if localappdata:
        default = Path(localappdata) / "Android" / "Sdk"
        if default.is_dir():
            return default
    return None


def _git_bin_dirs() -> list[str]:
    candidates: list[Path] = []
    for key in ("ProgramFiles", "ProgramFiles(x86)"):
        root = os.getenv(key, "").strip()
        if root:
            candidates.append(Path(root) / "Git" / "cmd")
            candidates.append(Path(root) / "Git" / "bin")
    return [str(path) for path in candidates if path.is_dir()]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    path_parts: list[str] = []
    path_parts.extend(_git_bin_dirs())
    flutter_bin = AI_FACTORY_FZ_ROOT.parent / ".tools" / "flutter" / "bin"
    if flutter_bin.is_dir():
        path_parts.append(str(flutter_bin))
    sdk = _android_sdk_root()
    if sdk:
        env["ANDROID_HOME"] = str(sdk)
        env["ANDROID_SDK_ROOT"] = str(sdk)
        for sub in (sdk / "platform-tools", sdk / "emulator"):
            if sub.is_dir():
                path_parts.append(str(sub))
    if not env.get("JAVA_HOME"):
        for base in (
            Path(r"C:\Program Files\Microsoft"),
            Path(r"C:\Program Files\Eclipse Adoptium"),
            Path(r"C:\Program Files\Java"),
        ):
            if not base.is_dir():
                continue
            jdks = sorted(base.glob("jdk-*"), reverse=True)
            if jdks:
                env["JAVA_HOME"] = str(jdks[0])
                path_parts.insert(0, str(jdks[0] / "bin"))
                break
    if path_parts:
        env["PATH"] = os.pathsep.join(path_parts) + os.pathsep + env.get("PATH", "")
    return env


def _state_path(run_id: str) -> Path:
    return EMULATOR_DIR / f"{run_id}.json"


def _log_path(run_id: str) -> Path:
    return EMULATOR_DIR / f"{run_id}.log"


def _write_state(run_id: str, payload: dict[str, Any]) -> None:
    EMULATOR_DIR.mkdir(parents=True, exist_ok=True)
    _state_path(run_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def resolve_flutter_project(run_id: str, run_state: dict[str, Any] | None = None) -> Path | None:
    """Locate a runnable Flutter project for a run id.

    Order: explicit flutter_project_dir → fz runs/{id}/app → legacy ai_factory/apps/{id}/flutter.
    """
    if run_state:
        raw = run_state.get("flutter_project_dir")
        if raw:
            project = Path(str(raw))
            if (project / "pubspec.yaml").is_file():
                return project
    app_dir = FZ_RUNS_DIR / run_id / "app"
    if (app_dir / "pubspec.yaml").is_file():
        return app_dir
    legacy = AI_FACTORY_ROOT / "apps" / run_id / "flutter"
    if (legacy / "pubspec.yaml").is_file():
        return legacy
    return None


def flutter_project_ready(run_id: str, run_state: dict[str, Any] | None = None) -> bool:
    return resolve_flutter_project(run_id, run_state) is not None


def _run_flutter(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_flutter_executable(), *args],
        cwd=str(cwd) if cwd else None,
        env=_env(),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def list_devices() -> dict[str, Any]:
    try:
        result = _run_flutter(["devices", "--machine"], timeout=60)
    except subprocess.TimeoutExpired:
        return {"devices": [], "error": "flutter devices timed out"}
    except FileNotFoundError:
        return {"devices": [], "error": "Flutter SDK not found. Install Flutter or use .tools/flutter."}

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "flutter devices failed").strip()
        return {"devices": [], "error": err}

    try:
        raw = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return {"devices": [], "error": "Invalid JSON from flutter devices"}

    devices: list[dict[str, Any]] = []
    for entry in raw if isinstance(raw, list) else []:
        platform = entry.get("targetPlatform") or entry.get("platform")
        devices.append(
            {
                "id": entry.get("id"),
                "name": entry.get("name"),
                "platform": platform,
                "emulator": bool(entry.get("emulator")),
            }
        )
    return {"devices": devices}


def list_emulators() -> dict[str, Any]:
    try:
        result = _run_flutter(["emulators"], timeout=60)
    except subprocess.TimeoutExpired:
        return {"emulators": [], "error": "flutter emulators timed out"}
    except FileNotFoundError:
        return {"emulators": [], "error": "Flutter SDK not found"}

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "flutter emulators failed").strip()
        return {"emulators": [], "error": err}

    emulators: list[dict[str, Any]] = []
    for line in (result.stdout or "").splitlines():
        stripped = line.strip()
        if "•" not in stripped or stripped.lower().startswith("id"):
            continue
        parts = [part.strip() for part in stripped.split("•")]
        if not parts or not parts[0]:
            continue
        emulators.append(
            {
                "id": parts[0],
                "name": parts[1] if len(parts) > 1 else parts[0],
                "platform": parts[3] if len(parts) > 3 else "android",
            }
        )
    return {"emulators": emulators}


def _pick_device(preferred_id: str | None) -> tuple[str | None, str | None]:
    devices = list_devices().get("devices", [])
    if preferred_id and any(d.get("id") == preferred_id for d in devices):
        return preferred_id, None

    for device in devices:
        platform = str(device.get("platform") or "")
        if device.get("emulator") and "android" in platform and device.get("id"):
            return str(device["id"]), None

    for device in devices:
        if device.get("emulator") and device.get("id"):
            return str(device["id"]), None

    for device in devices:
        platform = str(device.get("platform") or "")
        if "android" in platform and device.get("id"):
            return str(device["id"]), None

    for device in devices:
        if device.get("id") == "windows":
            return "windows", "No Android emulator detected; launching on Windows desktop instead."

    if devices and devices[0].get("id"):
        return str(devices[0]["id"]), "No Android emulator detected; using the first available Flutter device."

    return None, None


def _launch_emulator_if_needed() -> tuple[str | None, str | None]:
    device_id, note = _pick_device(None)
    if device_id:
        return device_id, note

    emulators = list_emulators().get("emulators", [])
    if not emulators:
        return None, None

    emu_id = emulators[0].get("id")
    if not emu_id:
        return None, None

    try:
        _run_flutter(["emulators", "--launch", str(emu_id)], timeout=180)
    except subprocess.TimeoutExpired:
        return None, "Timed out while starting the Android emulator."

    for _ in range(90):
        time.sleep(2)
        device_id, note = _pick_device(None)
        if device_id:
            return device_id, note
    return None, "Android emulator did not become ready in time."


def _log_tail(run_id: str, lines: int = 40) -> str:
    path = _log_path(run_id)
    if not path.is_file():
        return ""
    content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:])


def get_status(run_id: str) -> dict[str, Any]:
    path = _state_path(run_id)
    if not path.is_file():
        return {"run_id": run_id, "status": "idle"}

    state = json.loads(path.read_text(encoding="utf-8"))
    pid = int(state.get("pid") or 0)
    if state.get("status") == "running" and pid and not _pid_alive(pid):
        state["status"] = "stopped"
        state["stopped_at"] = datetime.now(timezone.utc).isoformat()
        _write_state(run_id, state)

    state["log_tail"] = _log_tail(run_id)
    return state


def _run_emulator_worker(run_id: str, project: Path, device_id: str | None) -> None:
    log_path = _log_path(run_id)

    def update(**fields: Any) -> None:
        current = json.loads(_state_path(run_id).read_text(encoding="utf-8"))
        current.update(fields)
        _write_state(run_id, current)

    try:
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n--- flutter pub get ({datetime.now(timezone.utc).isoformat()}) ---\n")
            pub = _run_flutter(["pub", "get"], cwd=project, timeout=300)
            log.write(pub.stdout or "")
            log.write(pub.stderr or "")
            if pub.returncode != 0:
                update(status="failed", error="flutter pub get failed")
                return

            log.write("\n--- resolving device ---\n")
            resolved, note = _pick_device(device_id)
            if not resolved:
                resolved, launch_note = _launch_emulator_if_needed()
                note = note or launch_note
            if not resolved:
                update(
                    status="failed",
                    error=(
                        "No emulator or device found. Install Android Studio, create an AVD "
                        "(Tools → Device Manager), then retry."
                    ),
                )
                return

            update(device_id=resolved, status="starting", note=note)
            log.write(f"\n--- flutter run -d {resolved} ---\n")

            proc = subprocess.Popen(
                [_flutter_executable(), "run", "-d", resolved],
                cwd=str(project),
                env=_env(),
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
            with _lock:
                _active[run_id] = proc
            update(status="running", pid=proc.pid, device_id=resolved)
            proc.wait()
            with _lock:
                _active.pop(run_id, None)

            if proc.returncode == 0:
                update(status="stopped", stopped_at=datetime.now(timezone.utc).isoformat())
            else:
                update(
                    status="failed",
                    error=f"flutter run exited with code {proc.returncode}",
                    stopped_at=datetime.now(timezone.utc).isoformat(),
                )
    except Exception as exc:
        update(status="failed", error=str(exc))


def start(run_id: str, device_id: str | None = None, run_state: dict[str, Any] | None = None) -> dict[str, Any]:
    project = resolve_flutter_project(run_id, run_state)
    if not project:
        raise ValueError(
            "Flutter project not found for this run. Expected "
            f"ai_factory_fz/runs/{run_id}/app or ai_factory/apps/{run_id}/flutter with a pubspec.yaml."
        )

    with _lock:
        existing = get_status(run_id)
        if existing.get("status") in ("starting", "running"):
            pid = int(existing.get("pid") or 0)
            if pid and _pid_alive(pid):
                return {**existing, "message": "Emulator session already active"}

        EMULATOR_DIR.mkdir(parents=True, exist_ok=True)
        log_path = _log_path(run_id)
        if log_path.is_file():
            log_path.write_text("", encoding="utf-8")

        state: dict[str, Any] = {
            "run_id": run_id,
            "status": "starting",
            "project_dir": str(project),
            "device_id": device_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "pid": None,
            "error": None,
            "log_path": str(log_path),
        }
        _write_state(run_id, state)

    thread = threading.Thread(
        target=_run_emulator_worker,
        args=(run_id, project, device_id),
        daemon=True,
        name=f"emulator-{run_id}",
    )
    thread.start()
    return get_status(run_id)


def stop(run_id: str) -> dict[str, Any]:
    with _lock:
        proc = _active.get(run_id)
        if proc and proc.poll() is None:
            proc.terminate()
        state = get_status(run_id)
        if state.get("status") in ("starting", "running"):
            state["status"] = "stopped"
            state["stopped_at"] = datetime.now(timezone.utc).isoformat()
            _write_state(run_id, state)
        return get_status(run_id)
