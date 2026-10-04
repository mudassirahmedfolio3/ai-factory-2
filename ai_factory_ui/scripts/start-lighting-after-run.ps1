# Wait for a run to complete, then start the lighting MVP factory run.
param(
    [string]$WaitForRunId = "20261003-044724",
    [string]$ApiBase = "http://127.0.0.1:8001",
    [string]$BriefPath = "e:\aifactory\ai_factory_fz\briefs\lighting-retail-mvp.md",
    [int]$PollSec = 60,
    # When Pass 2 is already building, use -NoAutoResume so this script only waits + starts lighting.
    [switch]$NoAutoResume
)

# ReadAllText avoids PowerShell 5.x sending client_brief as a FileInfo-shaped object in JSON.
$brief = [System.IO.File]::ReadAllText($BriefPath)
$body = (@{
    project_name = "lighting-retail-mvp"
    client_brief = [string]$brief
    complexity   = "standard"
} | ConvertTo-Json -Depth 2 -Compress)

Write-Host "Waiting for $WaitForRunId to reach completed..."
while ($true) {
    try {
        $snap = Invoke-RestMethod -Uri "$ApiBase/runs/$WaitForRunId" -TimeoutSec 90
        $st = $snap.status
        Write-Host ("[{0}] {1} status={2} phase={3}" -f (Get-Date -Format "HH:mm:ss"), $WaitForRunId, $st, $snap.phase)
        if ($st -eq "completed") { break }
        $live = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -match 'fz_worker' -and $_.CommandLine -match [regex]::Escape($WaitForRunId) }
        if (-not $NoAutoResume -and -not $live -and $st -in @("running", "stale")) {
            Write-Host "Auto-resume $WaitForRunId..."
            Invoke-RestMethod -Method Post -Uri "$ApiBase/runs/$WaitForRunId/resume" -TimeoutSec 120 | Out-Null
        }
    } catch {
        Write-Warning $_.Exception.Message
    }
    Start-Sleep -Seconds $PollSec
}

Write-Host "Starting lighting retail MVP run..."
$resp = Invoke-RestMethod -Method Post -Uri "$ApiBase/runs" -Body $body -ContentType "application/json; charset=utf-8" -TimeoutSec 120
Write-Host "Started run $($resp.run_id). Monitor in History or: monitor-and-resume-run.ps1 -RunId $($resp.run_id)"
