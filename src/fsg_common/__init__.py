"""Code shared by the four FSG estimating repos.

Pure Python, standard library only. `openpyxl` is needed by the two paths
that open an Excel workbook (`sections.load_section_library` and
`scripts/refresh_from_workbook.py`) and is imported inside them, so
installing this package does not require it.

Modules planned by the audit of 2 Sep 2026 (Part 3.8): `sections`,
`leak_guard`, `constants`, `envfile`, `hosts`. `sections` (the largest copy,
the one with a live drift risk) and `leak_guard` (fsg-estimating-tools#116,
7 Sep 2026 -- "one guard, all repos") are built; `constants`, `envfile` and
`hosts` are not.
"""

__version__ = "0.1.0"
