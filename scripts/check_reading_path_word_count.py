#!/usr/bin/env python3
"""fsg-common's own copy of the estate-wide reading-path word gate.

The check itself -- the six-file list, the word cap, the credential
handling, the Dependabot exemption -- lives in `fsg_common.reading_path`.
This is a thin wrapper naming which repo it is running in, same as the
copy in each of the other four repos (fsg-estimating-crm, fsg-tender-review,
fsg-estimating-tools, fsg-bluebeam-steel-standards). See that module's
docstring for the full rationale, and crm#557/crm#635 for David's decision.

    python scripts/check_reading_path_word_count.py
    python scripts/check_reading_path_word_count.py --json
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from fsg_common.reading_path import main  # noqa: E402

THIS_REPO = "fsg-common"

if __name__ == "__main__":
    sys.exit(main(THIS_REPO, sys.argv[1:]))
