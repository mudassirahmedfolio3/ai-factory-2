# Monitor an fz run; auto-resume on stale worker (does not kill a live worker).
param(
    [Parameter(Mandatory = $true)]
    [string]$RunId,
    [string]$ApiBase = "http://127.0.0.1:8001",
    [int]$IntervalSec = 45
)

function Get-RunSnapshot {
    try {
        $r = Invoke-RestMethod -Uri "$ApiBase/runs/$RunId" -TimeoutSec 60
        return $r
    } catch {
        return $null
    }
}

function Test-WorkerLive {
    $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'fz_worker' -and $_.CommandLine -match [regex]::Escape($RunId) }
    return [bool]$procs
}

Write-Host "Monitoring run $RunId (every ${IntervalSec}s). Ctrl+C to stop."
$deadPolls = 0
while ($true) {
    $live = Test-WorkerLive
    $snap = Get-RunSnapshot
    $status = if ($snap) { $snap.status } else { "?" }
    $phase = if ($snap) { $snap.phase } else { "?" }
    Write-Host ("[{0}] worker={1} ui_status={2} phase={3}" -f (Get-Date -Format "HH:mm:ss"), $(if ($live) { "live" } else { "off" }), $status, $phase)

    if ($snap -and $status -eq "completed") {
        Write-Host "Run completed."
        break
    }

    if ($live) {
        $deadPolls = 0
    } elseif ($snap -and ($status -in @("running", "stale"))) {
        $deadPolls++
        # Avoid resume storms (manual + scripts killing a worker that just started).
        if ($deadPolls -ge 2) {
            Write-Host "Worker not running for ${deadPolls}x polls; attempting resume..."
            try {
                Invoke-RestMethod -Method Post -Uri "$ApiBase/runs/$RunId/resume" -TimeoutSec 120 | Out-Null
                Write-Host "Resume requested."
                $deadPolls = 0
            } catch {
                Write-Warning $_.Exception.Message
            }
        }
    }

    Start-Sleep -Seconds $IntervalSec
}
