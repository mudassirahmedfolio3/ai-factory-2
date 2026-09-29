# Start OpenAI-compatible proxy for Cursor API (required when LLM_PROVIDER=cursor_proxy)
# Usage: .\scripts\start-cursor-proxy.ps1
# Keep this terminal open while running crewai run

$ErrorActionPreference = "Stop"
$envFile = Join-Path $PSScriptRoot ".." ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"')
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

if (-not $env:CURSOR_API_KEY) {
    Write-Error "CURSOR_API_KEY not set in .env"
}

# Cursor CLI must be installed: irm 'https://cursor.com/install?win32=true' | iex
# One-time auth (pick one):
#   agent login
#   — or rely on CURSOR_API_KEY (set above from .env)
$agentCmd = Get-Command agent -ErrorAction SilentlyContinue
if (-not $agentCmd) {
    Write-Warning "Cursor CLI (agent) not found. Install: irm 'https://cursor.com/install?win32=true' | iex"
}

Write-Host "Starting cursor-agent-api-proxy on http://localhost:4646/v1 ..."
Write-Host "If health checks fail, run once: agent login"
Write-Host "Keep this terminal open while running crewai run."
npx --yes cursor-agent-api-proxy start
