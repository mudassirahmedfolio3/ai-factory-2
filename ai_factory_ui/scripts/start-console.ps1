# Start AI Factory Console (API + Web)
# Usage: .\scripts\start-console.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$FactoryVenv = Join-Path $Root "..\ai_factory\.venv\Scripts\python.exe"
$ApiDir = Join-Path $Root "api"
$WebDir = Join-Path $Root "web"

if (-not (Test-Path $FactoryVenv)) {
    Write-Error "ai_factory venv not found. Run: cd ai_factory && crewai install"
}

Write-Host "Starting API on http://127.0.0.1:8000 ..."
Start-Process -FilePath $FactoryVenv -ArgumentList "-m", "uvicorn", "main:app", "--reload", "--port", "8000" -WorkingDirectory $ApiDir

Write-Host "Starting Web on http://localhost:5173 ..."
Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $WebDir

Write-Host "Console starting. Open http://localhost:5173"
