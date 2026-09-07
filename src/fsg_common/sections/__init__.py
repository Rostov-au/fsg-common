"""FSG's section library and the resolver that reads a drawing's notation.

    >>> from fsg_common import sections
    >>> section, how = sections.resolve("200 PFC")
    >>> section.section_id, section.mass_kg_per_m, how
    ('200PFC', 22.9, 'exact')

`how` is never optional. A caller that reduces the result to a mass and
drops the verdict has thrown away the difference between the drawing's own
words and the resolver's best guess, which is the whole point of showing the
working.

## What is here

- `Section` -- one row of `90_Lists`.
- `resolve` / `library` / `SectionLibrary` -- notation in, `(Section, how)`
  out.
- `ambiguous_candidates` -- what `250UB` could have meant, when it resolves
  to nothing because the drawing never chose.
- `shape_modifier_candidates` -- for a `shape-modifier` refusal, the plain
  section that was ruled out. The anchor, never the answer.
- `substitutions` -- an estimator's recorded decision to price a size the
  library lacks as a different real one. Read by the resolver; never a
  resolver rule.
- `load_section_library` -- the one function that opens a workbook.
- `RoundingPolicy`, `TENDER_REVIEW`, `BLUEBEAM` -- the single behaviour the
  two source resolvers disagree about, carried rather than settled. See
  `_policy.py`.

## Verdicts

`exact`, `canonical`, `nearest`, `cold-formed`, `material-mismatch`,
`shape-modifier`, `substitution`, `unresolved`. `nearest` and every refusal
need an estimator's eye and callers must surface them.

## Three private names are re-exported on purpose

`_NON_STEEL`, `_SHAPE_MODIFIER` and `_looks_like_mark` are underscored and
still exported, because `fsg-bluebeam-steel-standards/tools/tests/
test_offline.py` imports all three by name from the module this package
replaces. A shim that offered only the public surface would break that suite,
and a consumer reaching into `fsg_common.sections._resolver` instead would be
worse: it would couple the consumer to this package's internal file layout.

They are not a public API and not in `__all__`. If the toolkit's tests stop
needing them, delete these three lines.
"""
from __future__ import annotations

from . import substitutions
from ._policy import ALL_POLICIES, BLUEBEAM, TENDER_REVIEW, RoundingPolicy
from ._resolver import (  # noqa: F401 - see the note below
    _NON_STEEL,
    _SHAPE_MODIFIER,
    COLD_FORMED,
    COLD_FORMED_VENDORS,
    HEAD_TOLERANCE,
    NEAREST_MARGIN,
    NEAREST_TOLERANCE,
    SectionLibrary,
    _looks_like_mark,
    ambiguous_candidates,
    canonical_candidates,
    cold_formed,
    library,
    loose_key,
    mass_of,
    resolve,
    shape_modifier,
    shape_modifier_candidates,
    vendor_cold_formed,
)
from ._section import Section
from ._snapshot import (
    COL_BUILD_DEFAULT,
    COL_CATEGORY,
    COL_MASS_FINAL,
    COL_PLATE_KG_M2,
    COL_PLATE_THK,
    COL_SECTION_ID,
    FIRST_ROW,
    LAST_ROW,
    PACKAGED_SNAPSHOT,
    SHEET,
    SNAPSHOT_STALE_AFTER_DAYS,
    STALE_AFTER_DAYS,
    check_provenance,
    default_snapshot_path,
    load_section_library,
    load_section_library_from_snapshot,
    provenance,
    provenance_line,
    snapshot_staleness_warning,
    snapshot_vintage,
    staleness_warning,
    vintage_line,
)

__all__ = [
    "ALL_POLICIES", "BLUEBEAM", "TENDER_REVIEW", "RoundingPolicy",
    "Section", "SectionLibrary",
    "ambiguous_candidates", "canonical_candidates", "cold_formed", "library",
    "loose_key", "mass_of", "resolve", "shape_modifier",
    "shape_modifier_candidates", "substitutions", "vendor_cold_formed",
    "COLD_FORMED", "COLD_FORMED_VENDORS", "HEAD_TOLERANCE", "NEAREST_MARGIN",
    "NEAREST_TOLERANCE",
    "SHEET", "FIRST_ROW", "LAST_ROW", "COL_SECTION_ID", "COL_CATEGORY",
    "COL_BUILD_DEFAULT", "COL_MASS_FINAL", "COL_PLATE_THK", "COL_PLATE_KG_M2",
    "STALE_AFTER_DAYS", "SNAPSHOT_STALE_AFTER_DAYS", "PACKAGED_SNAPSHOT",
    "check_provenance", "default_snapshot_path", "load_section_library",
    "load_section_library_from_snapshot", "provenance", "provenance_line",
    "snapshot_staleness_warning", "snapshot_vintage", "staleness_warning",
    "vintage_line",
]
