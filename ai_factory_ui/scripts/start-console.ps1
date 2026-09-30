# Start AI Factory Console (API + AI-Factory-React frontend)
# Usage: .\scripts\start-console.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$FzVenv = Join-Path $Root "..\ai_factory_fz\.venv\Scripts\python.exe"
$LegacyVenv = Join-Path $Root "..\ai_factory\.venv\Scripts\python.exe"
$ApiDir = Join-Path $Root "api"
$ReactDir = [System.IO.Path]::GetFullPath((Join-Path $Root "..\AI-Factory-React"))

if (Test-Path $FzVenv) {
    $FactoryVenv = $FzVenv
    $env:FACTORY_ENGINE = "fz"
    Write-Host "Using ai_factory_fz venv (FACTORY_ENGINE=fz)."
} elseif (Test-Path $LegacyVenv) {
    $env:FACTORY_ENGINE = "legacy"
    $FactoryVenv = $LegacyVenv
    Write-Host "Using ai_factory venv (legacy engine)."
} else {
    Write-Error "No Python venv found. Run: cd ai_factory_fz && ..\ai_factory\.venv\Scripts\uv.exe sync"
}

function Stop-PortListener([int]$Port) {
    try {
        Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
            ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "  (Could not free port $Port - close old terminals manually if needed)"
    }
}

$ApiPort = 8001

Write-Host "Freeing ports 5173, 5174, 8000 and $ApiPort (stale dev servers)..."
Stop-PortListener 5173
Stop-PortListener 5174
Stop-PortListener 8000
Stop-PortListener $ApiPort

Write-Host "Starting API on http://127.0.0.1:$ApiPort (engine=$($env:FACTORY_ENGINE)) ..."
# Avoid --reload during fz runs: reload kills the background SDLC worker subprocess.
$uvicornArgs = @("-m", "uvicorn", "main:app", "--port", "$ApiPort")
if ($env:FACTORY_ENGINE -ne "fz") {
    $uvicornArgs += "--reload"
}
Start-Process cmd.exe -ArgumentList @(
    "/c",
    "set FACTORY_ENGINE=$($env:FACTORY_ENGINE)&& `"$FactoryVenv`" $($uvicornArgs -join ' ')"
) -WorkingDirectory $ApiDir

Write-Host "Waiting for API health..."
$healthy = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$ApiPort/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $healthy = $true; break }
    } catch { }
}
if (-not $healthy) {
    Write-Warning "API did not respond on /health - restart may still be in progress."
} else {
    Write-Host "API is ready."
}

$pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $pnpm -and -not $npm) {
    Write-Warning "Node.js not found. Install Node 18+ then run: cd AI-Factory-React && pnpm install && pnpm dev"
} else {
    Write-Host "Starting AI-Factory-React on http://127.0.0.1:5173 ..."
    Write-Host "  (NOT ai_factory_ui/web - that is the legacy console without API key / token UI)"
    if ($pnpm) {
        Start-Process -FilePath "pnpm" -ArgumentList "dev" -WorkingDirectory $ReactDir
    } else {
        Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $ReactDir
    }
}

Write-Host ""
Write-Host "Console starting. Open http://127.0.0.1:5173  (NOT 5174)"
Write-Host "Hard-refresh once (Ctrl+Shift+R) if the page looks stale."
Write-Host "If the page hangs: close all factory terminals and run this script again."
