# 1) Wait for 20261003-044724 to complete (auto-resume if worker dies)
# 2) Merge Release 2 expansion brief + POST resume (another release, same run_id)
# 3) Wait for second completion (auto-resume)
# 4) Start lighting-retail-mvp as a new run
param(
    [string]$RunId = "20261003-044724",
    [string]$ApiBase = "http://127.0.0.1:8001",
    [int]$PollSec = 60
)

$ExpansionPath = "e:\aifactory\ai_factory_fz\briefs\release2-shopease-expansion.md"
$LightingBriefPath = "e:\aifactory\ai_factory_fz\briefs\lighting-retail-mvp.md"
$StatePath = "e:\aifactory\ai_factory_fz\runs\$RunId\state.json"

function Test-WorkerLive([string]$Id) {
    $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'fz_worker' -and $_.CommandLine -match [regex]::Escape($Id) }
    return [bool]$procs
}

function Wait-RunCompleted([string]$Id, [string]$Label) {
    Write-Host "=== $Label : waiting for $Id to complete ==="
    while ($true) {
        try {
            $snap = Invoke-RestMethod -Uri "$ApiBase/runs/$Id" -TimeoutSec 90
            $st = $snap.status
            Write-Host ("[{0}] {1} status={2} phase={3}" -f (Get-Date -Format "HH:mm:ss"), $Id, $st, $snap.phase)
            if ($st -eq "completed") { return }
            # Do not auto-resume `failed` (build/QA stop); that causes resume loops. Only stale/running with no worker.
            if (-not (Test-WorkerLive $Id) -and $st -in @("running", "stale")) {
                Write-Host "Auto-resume $Id (worker missing, status=$st)..."
                Invoke-RestMethod -Method Post -Uri "$ApiBase/runs/$Id/resume" -TimeoutSec 300 | Out-Null
            }
        } catch {
            Write-Warning $_.Exception.Message
        }
        Start-Sleep -Seconds $PollSec
    }
}

function Merge-Release2Brief {
    if (-not (Test-Path $StatePath)) { throw "Missing $StatePath" }
    if (-not (Test-Path $ExpansionPath)) { throw "Missing $ExpansionPath" }
    $py = "e:\aifactory\ai_factory_fz\.venv\Scripts\python.exe"
    $script = "e:\aifactory\ai_factory_ui\scripts\merge_release2_brief.py"
    & $py $script $StatePath $ExpansionPath
    if ($LASTEXITCODE -ne 0) { throw "merge_release2_brief failed" }
}

# Stop the old single-step lighting waiter if it was started (best-effort)
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'start-lighting-after-run.ps1' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Wait-RunCompleted -Id $RunId -Label "Pass 1"

Write-Host "=== Starting Release 2 on same run_id (Generate another release) ==="
Merge-Release2Brief
Invoke-RestMethod -Method Post -Uri "$ApiBase/runs/$RunId/resume" -TimeoutSec 120 | Out-Null

Wait-RunCompleted -Id $RunId -Label "Pass 2 (Release 2)"

Write-Host "=== Starting lighting-retail-mvp as new run ==="
$brief = Get-Content $LightingBriefPath -Raw -Encoding UTF8
$body = @{
    project_name = "lighting-retail-mvp"
    client_brief = $brief
    complexity   = "standard"
} | ConvertTo-Json -Depth 3
$resp = Invoke-RestMethod -Method Post -Uri "$ApiBase/runs" -Body $body -ContentType "application/json; charset=utf-8" -TimeoutSec 120
$newId = $resp.run_id
Write-Host "Lighting run started: $newId"
Write-Host "Monitor: .\monitor-and-resume-run.ps1 -RunId $newId"
