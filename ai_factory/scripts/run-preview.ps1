# Open the latest factory browser preview (or re-serve an existing one).
# Usage: .\scripts\run-preview.ps1 [run_id]

param([string]$RunId = "")

$Root = Split-Path -Parent $PSScriptRoot
$Apps = Join-Path $Root "apps"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

& $Python -c @"
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r'$Root') / 'src'))
from ai_factory.browser_runner import run_browser_preview

apps = Path(r'$Apps')
run_id = r'$RunId'
if not run_id:
    dirs = sorted([d for d in apps.iterdir() if d.is_dir()], key=lambda p: p.name, reverse=True)
    if not dirs:
        raise SystemExit('No previews in apps/ — run the factory first.')
    run_id = dirs[0].name

index = apps / run_id / 'index.html'
if index.exists():
    result = run_browser_preview(
        run_id=run_id,
        project_name=run_id,
        client_brief='',
        code_artifacts=index.read_text(encoding='utf-8'),
        open_browser=True,
    )
else:
    result = run_browser_preview(
        run_id=run_id,
        project_name='preview',
        client_brief='Demo',
        code_artifacts='',
        open_browser=True,
    )
print(result.url or result.message)
"@
