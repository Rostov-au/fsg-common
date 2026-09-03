"""Code shared by the four FSG estimating repos.

Pure Python, standard library only. `openpyxl` is needed by the two paths
that open an Excel workbook (`sections.load_section_library` and
`scripts/refresh_from_workbook.py`) and is imported inside them, so
installing this package does not require it.

Modules planned by the audit of 2 Sep 2026 (Part 3.8): `sections`,
`leak_guard`, `constants`, `envfile`, `hosts`. Only `sections` is built --
it was the largest copy and the one with a live drift risk.
"""

__version__ = "0.1.0"
