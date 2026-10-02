# Sample run export: 20261002-120919

Copied from a local `ai_factory_fz/runs/20261002-120919` for analysis / DeepEval.

Includes `state.json` and `docs/` only (no app/server build trees, no nested `.git`).

Point DeepEval at this folder:

```bash
cd ai_factory_fz/deepeval
set DEEPEVAL_RUN_DIR=../samples/20261002-120919
uv run deepeval test run agent_test_writeup/
```
