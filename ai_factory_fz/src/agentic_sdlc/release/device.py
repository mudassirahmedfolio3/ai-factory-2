"""Android device support: SDK toolchain on this machine, emulator lifecycle, app install/launch.

Split of responsibilities:
- This machine runs only the Android *emulator* (needs KVM for speed) from a system-managed SDK in
  ~/.local/share/agentic-sdlc/android-sdk (no sudo). Installed by `uv run setup-android`, which is
  also where the human accepts the Android SDK licence; pipeline runs never accept it.
- Everything that talks to the device (adb, flutter build/test) runs in the Flutter container with
  host networking. The container's adb server finds the emulator on its standard local ports, so
  there is only ever one adb version in play.
"""

import os
import re
import shlex
import shutil
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

from agentic_sdlc.registry.profiles import DeviceConfig
from agentic_sdlc.tools.sandbox_exec import SandboxResult, SandboxRunner
from agentic_sdlc.workspace import Workspace

SDK_ROOT = Path(os.environ.get("SDLC_ANDROID_SDK", Path.home() / ".local/share/agentic-sdlc/android-sdk"))
REPOSITORY_XML = "https://dl.google.com/android/repository/repository2-3.xml"
DOWNLOAD_BASE = "https://dl.google.com/android/repository/"
FALLBACK_CMDLINE_TOOLS = "commandlinetools-linux-16111833_latest.zip"


class DeviceError(RuntimeError):
    pass


class AndroidToolchain:
    def __init__(self, config: DeviceConfig, sdk_root: Path | None = None):
        self.cfg = config
        self.root = sdk_root or SDK_ROOT

    # ---------- paths ----------

    @property
    def sdkmanager(self) -> Path:
        return self.root / "cmdline-tools" / "latest" / "bin" / "sdkmanager"

    @property
    def avdmanager(self) -> Path:
        return self.root / "cmdline-tools" / "latest" / "bin" / "avdmanager"

    @property
    def emulator(self) -> Path:
        return self.root / "emulator" / "emulator"

    @property
    def avd_home(self) -> Path:
        return self.root / "avd"

    def _system_image_dir(self) -> Path:
        return self.root.joinpath(*self.cfg.system_image.split(";"))

    def env(self) -> dict[str, str]:
        return {**os.environ, "ANDROID_SDK_ROOT": str(self.root), "ANDROID_HOME": str(self.root),
                "ANDROID_AVD_HOME": str(self.avd_home)}

    # ---------- readiness ----------

    def not_ready_reason(self) -> str | None:
        if not Path("/dev/kvm").exists() or not os.access("/dev/kvm", os.R_OK | os.W_OK):
            return "No usable /dev/kvm: the Android emulator needs hardware virtualisation (KVM) for this user"
        missing = [what for what, path in (
            ("the Android command-line tools", self.sdkmanager), ("the emulator", self.emulator),
            (f"the system image {self.cfg.system_image}", self._system_image_dir()),
            (f"the virtual device '{self.cfg.avd_name}'", self.avd_home / f"{self.cfg.avd_name}.avd"),
        ) if not path.exists()]
        if missing:
            return "Android emulator not set up (missing " + ", ".join(missing) + "): run `uv run setup-android` once"
        return None

    # ---------- install (interactive; run by a human) ----------

    def install(self) -> None:
        """Download the SDK pieces and create the virtual device. Shows the licence prompt."""
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.sdkmanager.exists():
            self._install_cmdline_tools()
        print("\nThe Android SDK licence must be accepted by you. Review it and answer the prompts:\n", flush=True)
        # Interactive on purpose: the person running setup reads and accepts the licence.
        subprocess.run([str(self.sdkmanager), f"--sdk_root={self.root}", "--licenses"], env=self.env(), check=True)
        packages = ["platform-tools", "emulator", self.cfg.system_image]
        print(f"\nInstalling {', '.join(packages)} (a few GB, one time)...", flush=True)
        subprocess.run([str(self.sdkmanager), f"--sdk_root={self.root}", *packages], env=self.env(), check=True)
        self.avd_home.mkdir(parents=True, exist_ok=True)
        if not (self.avd_home / f"{self.cfg.avd_name}.avd").exists():
            subprocess.run(
                [str(self.avdmanager), "create", "avd", "-n", self.cfg.avd_name, "-k", self.cfg.system_image,
                 "-d", self.cfg.device_profile, "--force"],
                input="no\n", text=True, env=self.env(), check=True,
            )
        reason = self.not_ready_reason()
        if reason:
            raise DeviceError(reason)
        print(f"\nAndroid emulator ready: AVD '{self.cfg.avd_name}' in {self.root}", flush=True)

    def _install_cmdline_tools(self) -> None:
        name = latest_cmdline_tools()
        print(f"Downloading {name}...", flush=True)
        archive = self.root / name
        urllib.request.urlretrieve(DOWNLOAD_BASE + name, archive)
        tmp = self.root / "cmdline-tools" / "_unpack"
        shutil.rmtree(tmp, ignore_errors=True)
        with zipfile.ZipFile(archive) as z:
            z.extractall(tmp)
        for f in tmp.rglob("*"):
            if f.is_file() and f.parent.name == "bin":
                f.chmod(0o755)
        dest = self.root / "cmdline-tools" / "latest"
        shutil.rmtree(dest, ignore_errors=True)
        (tmp / "cmdline-tools").rename(dest)
        shutil.rmtree(tmp, ignore_errors=True)
        archive.unlink()


def latest_cmdline_tools() -> str:
    try:
        with urllib.request.urlopen(REPOSITORY_XML, timeout=30) as r:
            names = re.findall(r"commandlinetools-linux-(\d+)_latest\.zip", r.read().decode())
        if names:
            return f"commandlinetools-linux-{max(map(int, names))}_latest.zip"
    except OSError:
        pass
    return FALLBACK_CMDLINE_TOOLS


class Emulator:
    """One emulator instance; device commands go through the Flutter container's adb."""

    def __init__(self, toolchain: AndroidToolchain, sandbox: SandboxRunner, workspace: Workspace,
                 runtime: str = "flutter", boot_timeout_s: int = 300):
        self.tc = toolchain
        self.cfg = toolchain.cfg
        self.sandbox = sandbox
        self.ws = workspace
        self.runtime = runtime
        self.boot_timeout_s = boot_timeout_s
        self._proc: subprocess.Popen | None = None

    @property
    def serial(self) -> str:
        return f"emulator-{self.cfg.console_port}"

    def run(self, command: str, workdir: str, timeout_s: int | None = None) -> SandboxResult:
        """Run a device command (e.g. flutter test -d <serial>) in the container, after the
        container's fresh adb server has found the emulator."""
        script = f"adb start-server >/dev/null 2>&1; adb -s {self.serial} wait-for-device; {command}"
        return self.sandbox.run_trusted(self.runtime, workdir, f"sh -c {shlex.quote(script)}", host_network=True,
                                        timeout_s=timeout_s)

    def adb(self, *args: str, workdir: str = ".") -> SandboxResult:
        """adb against the (booted) device, after the container's adb server has found it."""
        return self.run(" ".join(["adb", "-s", self.serial, *map(shlex.quote, args)]), workdir, timeout_s=300)

    def is_booted(self) -> bool:
        # No wait-for-device here: during boot the device may not be visible yet.
        script = (f"adb start-server >/dev/null 2>&1; sleep 2; "
                  f"adb -s {self.serial} shell getprop sys.boot_completed")
        r = self.sandbox.run_trusted(self.runtime, ".", f"sh -c {shlex.quote(script)}", host_network=True, timeout_s=60)
        return r.ok and r.output.strip().endswith("1")

    def start(self, window: bool = False) -> None:
        reason = self.tc.not_ready_reason()
        if reason:
            raise DeviceError(reason)
        if self.is_booted():
            return
        log = self.ws.resolve("reports/device/emulator.log")
        log.parent.mkdir(parents=True, exist_ok=True)
        args = [str(self.tc.emulator), "-avd", self.cfg.avd_name, "-port", str(self.cfg.console_port),
                "-no-snapshot-save", "-no-audio", "-no-boot-anim", "-gpu", "swiftshader_indirect"]
        if not window:
            args.append("-no-window")
        self._proc = subprocess.Popen(args, env=self.tc.env(), stdout=open(log, "w"), stderr=subprocess.STDOUT,
                                      start_new_session=True)
        deadline = time.monotonic() + self.boot_timeout_s
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                raise DeviceError(f"The emulator exited during boot (code {self._proc.returncode}):\n"
                                  + log.read_text(errors="replace")[-2000:])
            if self.is_booted():
                return
            time.sleep(5)
        raise DeviceError(f"The emulator did not finish booting within {self.boot_timeout_s}s")

    def install(self, apk_path: str, workdir: str, app_id: str = "") -> SandboxResult:
        r = self.adb("install", "-r", apk_path, workdir=workdir)
        if not r.ok and "INSTALL_FAILED_UPDATE_INCOMPATIBLE" in r.output and app_id:
            # Signed with a different debug key than the installed copy: replace it (test device).
            self.adb("uninstall", app_id)
            r = self.adb("install", apk_path, workdir=workdir)
        return r

    def launch(self, app_id: str) -> SandboxResult:
        return self.adb("shell", "monkey", "-p", app_id, "-c", "android.intent.category.LAUNCHER", "1")

    def screenshot(self, rel_path: str) -> str | None:
        """Save a PNG of the screen to a workspace path; returns the path or None."""
        tmp = "/sdcard/sdlc_screen.png"
        if not self.adb("shell", "screencap", "-p", tmp).ok:
            return None
        self.ws.resolve(rel_path).parent.mkdir(parents=True, exist_ok=True)
        r = self.adb("pull", tmp, f"/workspace/{rel_path}")
        return rel_path if r.ok else None

    def stop(self) -> None:
        """Power the device off (no console auth token needed), then make sure the emulator
        process on this machine is gone."""
        self.run(f"adb -s {self.serial} shell reboot -p", ".")
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and self._host_pids():
            time.sleep(2)
        for pid in self._host_pids():
            try:
                os.kill(pid, 15)
            except ProcessLookupError:
                pass
        self._proc = None

    def _host_pids(self) -> list[int]:
        """Emulator processes for this AVD and port, including ones started by an earlier run."""
        out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout
        return [int(line.split(None, 1)[0]) for line in out.splitlines()[1:]
                if f"-avd {self.cfg.avd_name}" in line and f"-port {self.cfg.console_port}" in line
                and ("qemu-system" in line or "emulator" in line)]
