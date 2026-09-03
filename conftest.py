"""Put `src/` and `tests/` on the path so the suite runs from a bare checkout.

No editable install, no venv step. `vocabulary.py` lives in `tests/` because
it is shared by the tests and by `tools/parity_report.py`, and neither
should have to reach into the other's directory by relative path.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for path in (ROOT / "src", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
