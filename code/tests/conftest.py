"""Pytest bootstrap: make repo-root packages (scripts/) importable.

Inserted because tests/ has no packaging of its own and test modules import
`scripts.*` by repo-relative name. No runtime effect outside pytest.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
