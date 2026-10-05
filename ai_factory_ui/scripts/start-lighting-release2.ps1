# Pass 2 on lighting run 20261004-043044: merge Release 2 brief + resume (Generate another release).
param(
    [string]$RunId = "20261004-043044",
    [string]$ApiBase = "http://127.0.0.1:8001",
    [switch]$MergeOnly
)

$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$StatePath = Join-Path $Root "ai_factory_fz\runs\$RunId\state.json"
$ExpansionPath = Join-Path $Root "ai_factory_fz\briefs\release2-lighting-retail-expansion.md"
$Py = Join-Path $Root "ai_factory_fz\.venv\Scripts\python.exe"
$MergeScript = Join-Path $PSScriptRoot "merge_release2_brief.py"

if (-not (Test-Path $StatePath)) { throw "Missing $StatePath" }
if (-not (Test-Path $ExpansionPath)) { throw "Missing $ExpansionPath" }

& $Py $MergeScript $StatePath $ExpansionPath `
    --pass1-before 13 `
    --pipeline pipeline.client.release2.lighting `
    --marker "Release 2 — lighting-retail MVP expansion"
if ($LASTEXITCODE -ne 0) { throw "merge_release2_brief failed" }

Write-Host "Merged Release 2 brief into $StatePath (pipeline.client.release2.lighting, WI-013+)."
if ($MergeOnly) {
    Write-Host "MergeOnly: open History and click 'Generate another release', or run without -MergeOnly."
    exit 0
}

$snap = Invoke-RestMethod -Uri "$ApiBase/runs/$RunId" -TimeoutSec 30
if ($snap.is_live -and $snap.status -eq "running") {
    throw "Run $RunId is already live. Wait for it to finish before Pass 2."
}

Write-Host "Resuming $RunId (Pass 2)..."
Invoke-RestMethod -Method Post -Uri "$ApiBase/runs/$RunId/resume" -TimeoutSec 120 | Out-Null
Write-Host "Pass 2 started. Monitor in the console or: fz_worker log under ai_factory_ui/api/artifacts/logs/"
