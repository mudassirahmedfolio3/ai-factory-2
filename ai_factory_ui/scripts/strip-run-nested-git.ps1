# Remove nested .git dirs under ai_factory_fz/runs so the monorepo can track run files.
$runsRoot = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) 'ai_factory_fz\runs'
if (-not (Test-Path -LiteralPath $runsRoot)) {
    Write-Error "Runs root not found: $runsRoot"
    exit 1
}
Get-ChildItem -LiteralPath $runsRoot -Directory | ForEach-Object {
    $gitDir = Join-Path $_.FullName '.git'
    if (Test-Path -LiteralPath $gitDir) {
        Remove-Item -LiteralPath $gitDir -Recurse -Force
        Write-Output "Removed nested repo: $($_.Name)"
    }
}
