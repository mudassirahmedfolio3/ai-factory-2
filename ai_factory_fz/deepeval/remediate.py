"""Entry point: python deepeval/remediate.py run|approve|resume|status ...  (run from ai_factory_fz)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from remediation.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
