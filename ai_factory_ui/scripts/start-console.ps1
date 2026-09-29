# Start AI Factory Console (API + AI-Factory-React frontend)
# Usage: .\scripts\start-console.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$FactoryVenv = Join-Path $Root "..\ai_factory\.venv\Scripts\python.exe"
$ApiDir = Join-Path $Root "api"
$ReactDir = Join-Path $Root "..\AI-Factory-React"

if (-not (Test-Path $FactoryVenv)) {
    Write-Error "ai_factory venv not found. Run: cd ai_factory && crewai install"
}

Write-Host "Starting API on http://127.0.0.1:8000 ..."
Start-Process -FilePath $FactoryVenv -ArgumentList "-m", "uvicorn", "main:app", "--reload", "--port", "8000" -WorkingDirectory $ApiDir

$pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $pnpm -and -not $npm) {
    Write-Warning "Node.js not found. Install Node 18+ then run: cd AI-Factory-React && pnpm install && pnpm dev"
} else {
    Write-Host "Starting AI-Factory-React on http://127.0.0.1:5173 ..."
    if ($pnpm) {
        Start-Process -FilePath "pnpm" -ArgumentList "dev" -WorkingDirectory $ReactDir
    } else {
        Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $ReactDir
    }
}

Write-Host "Console starting. Open http://127.0.0.1:5173"
