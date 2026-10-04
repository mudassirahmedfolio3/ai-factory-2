# Staging smoke: GET /health (getHealth) against docker-compose API.
param(
  [switch]$Up,
  [string]$Url = $(if ($env:HEALTH_SMOKE_URL) { $env:HEALTH_SMOKE_URL } else { $port = if ($env:PORT) { $env:PORT } else { '3000' }; "http://127.0.0.1:$port/health" })
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

if ($Up) {
  Push-Location $Root
  try {
    docker compose up -d --build --wait
  } finally {
    Pop-Location
  }
}

Push-Location $Root
try {
  node (Join-Path $Root 'scripts/run-gethealth-smoke.mjs') $Url
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
  Pop-Location
}
