# Lightweight Android emulator setup (no full Android Studio required).
# Downloads SDK command-line tools (~150 MB), creates an AVD, configures Flutter.

$ErrorActionPreference = "Stop"

# Java is required for sdkmanager/avdmanager.
$JdkRoot = Get-ChildItem "C:\Program Files\Microsoft\jdk-*" -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $JdkRoot) {
    Write-Host "Installing OpenJDK 17..."
    winget install Microsoft.OpenJDK.17 --accept-package-agreements --accept-source-agreements --disable-interactivity
    $JdkRoot = Get-ChildItem "C:\Program Files\Microsoft\jdk-*" -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
}
if ($JdkRoot) {
    $env:JAVA_HOME = $JdkRoot.FullName
    $env:Path = "$($JdkRoot.FullName)\bin;" + $env:Path
} else {
    throw "Java (JDK 17+) is required. Install Microsoft.OpenJDK.17 then re-run."
}

$SdkRoot = Join-Path $env:LOCALAPPDATA "Android\Sdk"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$FlutterBin = Join-Path $RepoRoot ".tools\flutter\bin"
$CmdlineZip = Join-Path $env:TEMP "commandlinetools-win.zip"
$CmdlineUrl = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"

function Find-SdkManager {
    @(
        (Join-Path $SdkRoot "cmdline-tools\latest\bin\sdkmanager.bat"),
        (Join-Path $SdkRoot "cmdline-tools\bin\sdkmanager.bat")
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
}

function Ensure-CommandLineTools {
    if (Find-SdkManager) { return }

    Write-Host "Downloading Android command-line tools (~150 MB)..."
    New-Item -ItemType Directory -Force -Path $SdkRoot | Out-Null
    Invoke-WebRequest -Uri $CmdlineUrl -OutFile $CmdlineZip -UseBasicParsing

    $extractDir = Join-Path $env:TEMP "android-cmdline-extract"
    if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
    Expand-Archive -Path $CmdlineZip -DestinationPath $extractDir -Force

    $target = Join-Path $SdkRoot "cmdline-tools\latest"
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    if (Test-Path $target) { Remove-Item $target -Recurse -Force }
    Move-Item (Join-Path $extractDir "cmdline-tools") $target
    Remove-Item $CmdlineZip -Force -ErrorAction SilentlyContinue
    Write-Host "Command-line tools installed."
}

Ensure-CommandLineTools
$sdkmanager = Find-SdkManager
if (-not $sdkmanager) { throw "sdkmanager not found after install" }

$env:ANDROID_HOME = $SdkRoot
$env:ANDROID_SDK_ROOT = $SdkRoot

Write-Host "Accepting SDK licenses..."
1..50 | ForEach-Object { "y" } | & $sdkmanager --licenses | Out-Null

Write-Host "Installing platform-tools, emulator, API 34 system image (may take several minutes)..."
& $sdkmanager "platform-tools" "emulator" "platforms;android-34" "system-images;android-34;google_apis;x86_64"

$avdmanager = Join-Path $SdkRoot "cmdline-tools\latest\bin\avdmanager.bat"
$avdName = "ai_factory_pixel"
$existing = & $avdmanager list avd 2>&1 | Out-String
if ($existing -notmatch $avdName) {
    Write-Host "Creating AVD $avdName ..."
    echo no | & $avdmanager create avd -n $avdName -k "system-images;android-34;google_apis;x86_64" -d pixel_7
} else {
    Write-Host "AVD $avdName already exists."
}

$flutter = Join-Path $FlutterBin "flutter.bat"
if (Test-Path $flutter) {
    & $flutter config --android-sdk $SdkRoot
    Write-Host ""
    & $flutter doctor
    Write-Host ""
    & $flutter emulators
}

Write-Host ""
Write-Host "Done. Use 'Run on emulator' in http://127.0.0.1:5173 after a build completes."
