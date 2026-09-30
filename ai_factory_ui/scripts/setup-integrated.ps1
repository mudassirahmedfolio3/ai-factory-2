# Setup integrated_ai_factory: fz venv, Docker, sandbox images, env files.
# Usage: .\scripts\setup-integrated.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $Root
$FzRoot = Join-Path $RepoRoot "ai_factory_fz"
$LegacyVenvUv = Join-Path $RepoRoot "ai_factory\.venv\Scripts\uv.exe"
$FzVenv = Join-Path $FzRoot ".venv\Scripts\python.exe"
$ApiDir = Join-Path $Root "api"

Write-Host "=== AI Factory integrated setup ===" -ForegroundColor Cyan

# 1. fz Python environment
if (-not (Test-Path $FzVenv)) {
    if (-not (Test-Path $LegacyVenvUv)) {
        Write-Error "uv not found. Install ai_factory venv first: cd ai_factory && crewai install"
    }
    Write-Host "Creating ai_factory_fz venv (uv sync)..."
    Push-Location $FzRoot
    & $LegacyVenvUv sync
    & $LegacyVenvUv pip install -r (Join-Path $ApiDir "requirements.txt")
    Pop-Location
} else {
    Write-Host "ai_factory_fz venv OK."
}

# 2. env files
$FzEnv = Join-Path $FzRoot ".env"
if (-not (Test-Path $FzEnv)) {
    Copy-Item (Join-Path $FzRoot ".env.example") $FzEnv
    Write-Warning "Created ai_factory_fz/.env - add ANTHROPIC_API_KEY before running."
}
$ApiEnv = Join-Path $ApiDir ".env"
if (-not (Test-Path $ApiEnv)) {
    Set-Content -Path $ApiEnv -Value "FACTORY_ENGINE=fz`n" -Encoding UTF8
    Write-Host "Created ai_factory_ui/api/.env (FACTORY_ENGINE=fz)."
}

# 3. Docker Desktop
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Host "Docker not found. Installing Docker Desktop via winget..."
    winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    Write-Warning "Docker Desktop installed. Start it from the Start menu, wait until it says 'Running', then re-run this script to pull images."
} else {
    Write-Host "Docker CLI found: $($docker.Source)"
}

# 4. Pull sandbox images (when Docker daemon is up)
try {
    docker info *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Pulling fz sandbox images (first time may take several minutes)..."
        $images = @(
            "node:24-bookworm",
            "ghcr.io/cirruslabs/flutter:stable",
            "openapitools/openapi-generator-cli:v7.10.0"
        )
        foreach ($img in $images) {
            Write-Host "  docker pull $img"
            docker pull $img
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Failed to pull $img"
            }
        }
    } else {
        Write-Warning "Docker daemon not running. Start Docker Desktop, then run: docker pull node:24-bookworm"
    }
} catch {
    Write-Warning "Could not verify Docker: $_"
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next:"
Write-Host "  1. Ensure ANTHROPIC_API_KEY is set in ai_factory_fz/.env"
Write-Host "  2. Start Docker Desktop (if not running)"
Write-Host "  3. Run: .\scripts\start-console.ps1"
Write-Host "  4. Open http://127.0.0.1:5173"
