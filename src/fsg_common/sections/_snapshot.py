"""Where the section rows come from: the packaged snapshot, or the workbook.

`90_Lists` in FSG's estimating workbook is the source of truth. It lives on
S: and is not always reachable, so `scripts/refresh_from_workbook.py`
duplicates it into `data/fsg_sections.json`, tracked in git with a
`_provenance` block naming the sheet, the generation date and a content
hash. Everything at runtime reads the snapshot; only the refresh script and
`load_section_library()` open a workbook.

## The snapshot moved inside the package, and that is a behaviour change

The Bluebeam toolkit's `default_snapshot_path()` pointed at the
`fsg-tender-review` checkout sitting next to it on disk, so every answer it
gave depended on the vintage of a sibling repo's WORKING TREE. On 2 Sep 2026
two sessions disagreed about whether `Z20024` resolves: one was reading a
733-section snapshot while `origin/main` held 750. Nothing was wrong with
either machine and nothing reported a difference.

The snapshot now ships inside this package, so a consumer gets the rows the
package version pins and a checkout it does not control cannot move them.
`FSG_SECTIONS_SNAPSHOT` still overrides, which is how the parity harness
points both resolvers at one file.

## Age is not currency

`check_provenance()` answers "has anyone re-checked the copy lately", never
"does the copy still match `90_Lists`". A copy regenerated yesterday from a
workbook that has since changed passes; the 733-row snapshot above passed a
90-day check while being 17 rows short. The real check is
`scripts/refresh_from_workbook.py --check`, which compares the content hash
against a fresh read and therefore needs the workbook. So `vintage_line()`
prints rows, date and hash on EVERY run, including a clean one: a line only
printed on failure is not there when you need to ask whether there is a
failure.
"""
from __future__ import annotations

import datetime as dt
import functools
import json
import os

from ._policy import TENDER_REVIEW, RoundingPolicy
from ._section import Section

# --- the live workbook -----------------------------------------------------
SHEET = "90_Lists"
FIRST_ROW = 6
LAST_ROW = 1005  # matches 20_MTO's own live MATCH range, 90_Lists!$A$6:$A$1005

COL_SECTION_ID = 1
COL_CATEGORY = 2
COL_BUILD_DEFAULT = 4
COL_MASS_FINAL = 7  # "Mass/m (kg/m) - FINAL"
COL_PLATE_THK = 8
COL_PLATE_KG_M2 = 9

#: Both source repos used 90. The toolkit read 30 with a comment claiming it
#: matched, so the repo that does NOT refresh the snapshot warned three times
#: sooner than the one that does; aligned 28 Aug 2026 and pinned by a test.
STALE_AFTER_DAYS = 90
SNAPSHOT_STALE_AFTER_DAYS = STALE_AFTER_DAYS  # the toolkit's name for it

PACKAGED_SNAPSHOT = os.path.join(os.path.dirname(__file__), "data",
                                 "fsg_sections.json")


def default_snapshot_path() -> str:
    """The packaged snapshot, or whatever `FSG_SECTIONS_SNAPSHOT` names."""
    return os.environ.get("FSG_SECTIONS_SNAPSHOT", PACKAGED_SNAPSHOT)


def _num(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@functools.lru_cache(maxsize=4)
def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def sections(path: str | None = None) -> dict[str, Section]:
    """Every section in the snapshot, keyed by upper-case id."""
    data = _load(path or default_snapshot_path())
    return {s["section_id"].upper(): Section(**s) for s in data["sections"]}


def provenance(path: str | None = None) -> dict:
    return _load(path or default_snapshot_path()).get("_provenance", {})


def vintage_line(path: str | None = None) -> str:
    """Rows, date and hash, on one line. Print it on every run.

    Absent fields are named `ABSENT` rather than left blank: a line reading
    `generated ` looks like provenance and answers no question.
    """
    path = path or default_snapshot_path()
    try:
        data = _load(path)
    except (OSError, ValueError) as exc:
        return f"{path} -- UNREADABLE ({type(exc).__name__}: {exc})"
    prov = data.get("_provenance", {})
    return (f"{len(data.get('sections', []))} sections, generated "
            f"{prov.get('generated') or 'ABSENT'}, sha "
            f"{prov.get('content_sha256') or 'ABSENT'} ({path})")


def staleness_warning(path: str | None = None) -> str | None:
    """A warning if the snapshot is old enough to mention, else None.

    A snapshot with no `generated` field gets its own words, not None:
    "cannot be checked" is not the same answer as "checked and fine".
    """
    prov = provenance(path)
    generated = prov.get("generated")
    if not generated:
        return (
            "section snapshot carries no `_provenance.generated`, so its age "
            "cannot be checked at all -- this is not the same as it being "
            "current. Regenerate it with scripts/refresh_from_workbook.py"
        )
    age = (dt.date.today() - dt.date.fromisoformat(generated)).days
    if age >= STALE_AFTER_DAYS:
        return (
            f"section snapshot is {age} days old (generated {generated}) -- "
            f"run scripts/refresh_from_workbook.py to refresh it, or pass "
            f"--workbook for a live read"
        )
    return None


# --- the names the two source repos called these ---------------------------
# Kept so a consumer shim is an import rather than a rewrite.

def snapshot_vintage(json_path: str) -> str:
    """The Bluebeam toolkit's name for `vintage_line`."""
    return vintage_line(json_path)


def snapshot_staleness_warning(json_path: str) -> str | None:
    """The Bluebeam toolkit's name for `staleness_warning`."""
    return staleness_warning(json_path)


def provenance_line(path: str | None = None) -> str:
    """fsg-tender-review's name for `vintage_line`, without the path."""
    return vintage_line(path).rsplit(" (", 1)[0]


def check_provenance(path: str | None = None) -> str | None:
    """fsg-tender-review's name for `staleness_warning`."""
    return staleness_warning(path)


def load_section_library_from_snapshot(json_path: str,
                                       rounding: RoundingPolicy = TENDER_REVIEW):
    """A `SectionLibrary` over the snapshot at `json_path`."""
    from ._resolver import SectionLibrary
    return SectionLibrary(sections(json_path).values(), rounding=rounding)


def load_section_library(workbook_path: str,
                         rounding: RoundingPolicy = TENDER_REVIEW):
    """Read `90_Lists` from a copy of the estimating workbook, read-only.

    The one path here that opens a workbook. `data_only=True` is not
    optional: the mass columns are formulas, and reading them as text turns
    every mass into None silently.
    """
    import openpyxl

    from ._resolver import SectionLibrary

    wb = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
    try:
        ws = wb[SHEET]
        rows: list[Section] = []
        for row in ws.iter_rows(min_row=FIRST_ROW, max_row=LAST_ROW,
                                min_col=1, max_col=9, values_only=True):
            section_id = row[COL_SECTION_ID - 1]
            if not section_id:
                continue
            rows.append(Section(
                section_id=str(section_id).strip(),
                category=str(row[COL_CATEGORY - 1] or "").strip(),
                build_default=str(row[COL_BUILD_DEFAULT - 1] or "Stick").strip(),
                mass_kg_per_m=_num(row[COL_MASS_FINAL - 1]),
                plate_thickness_mm=_num(row[COL_PLATE_THK - 1]),
                plate_kg_per_m2=_num(row[COL_PLATE_KG_M2 - 1]),
            ))
    finally:
        wb.close()
    return SectionLibrary(rows, rounding=rounding)
