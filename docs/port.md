# How the resolver was ported, and how to check it

The point of this file is that you should not have to trust the port. The
body of `src/fsg_common/sections/_resolver.py` is a copy of
`fsg-tender-review/src/fsg_tender_review/resolve.py`, and the difference
between them is twelve edits plus a rewritten module docstring. You can see
that for yourself:

```
git -C ../fsg-tender-review show origin/main:src/fsg_tender_review/resolve.py > /tmp/resolve.py
diff -u /tmp/resolve.py src/fsg_common/sections/_resolver.py
```

Measured 3 Sep 2026: 13 hunks, 81 lines added, 56 removed. Hunk 1 is the
module docstring. The other 12 are below.

Nothing was reformatted, renamed or tidied. That was the whole discipline of
the move: a port you can diff is a port you can review, and every guard
clause in this file exists because a first version got a real number wrong on
a real tender.

## The twelve edits

| # | What | Why |
|---|---|---|
| 1 | `from .classification import Section` becomes `from ._section import Section` | The dataclass moved into the package. Same six fields, same two properties. |
| 2 | `_is_rounding` takes a `policy` argument | See `_policy.py`. The one open question. |
| 3 | The hardcoded `0.051` one-decimal clause becomes `policy.decimal_tolerance`, with `None` meaning the clause does not apply | Same. |
| 4 | `SectionLibrary.__init__` takes `rounding=` and stores it | Same. |
| 5 | `SectionLibrary.resolve` passes `self.rounding` into `_is_rounding` | Same. |
| 6 | `library()` reads `_snapshot.sections()` instead of `classification.sections()` | The snapshot ships inside the package now. |
| 7 | `_policy` imported, `__all__` declared | New public surface. |
| 8 | `library()` cache widened from `maxsize=1` to `maxsize=4`, takes `rounding` | One cached library per policy, not one overall. |
| 9 | `resolve()` takes and forwards `rounding` | Convenience wrapper. |
| 10 | `ambiguous_candidates()` takes `rounding` and passes it to `library()` | So a Bluebeam-policy caller is not silently handed tender-review answers. |
| 11 | `shape_modifier_candidates()` takes `rounding` and passes it to `library()` | Same. It resolves the plain form, so the policy can reach it. |
| 12 | `mass_of()` takes `rounding` and forwards it to `resolve()` | Same. |

Edits 2 to 5 and 8 to 12 are all one change: threading the rounding policy
through, so the package can answer as either source repo does. Edits 1, 6 and
7 are the packaging.

Every edit was applied as an exact-string replacement that asserted it matched
exactly once, so a silent no-op was not possible.

## What did not come across

`fsg-tender-review`'s `classification.py` also holds weight classes, the
grading bands, the labour rates and `classify()`. None of it moved. Those are
classification, not section resolution, and the audit named only
`classification.Section`. The file stays where it is and keeps reading the
same JSON.

## What came from the other side

The Bluebeam toolkit's `sections.py` had three things `resolve.py` did not,
and they are in `_snapshot.py`:

- `load_section_library(workbook_path)`, the only function here that opens an
  Excel workbook. `openpyxl` is imported inside it, so the package still
  installs with no third-party dependency.
- `load_section_library_from_snapshot`, `default_snapshot_path`,
  `snapshot_vintage`, `snapshot_staleness_warning` and the `90_Lists` sheet
  and column constants.
- `SNAPSHOT_STALE_AFTER_DAYS`.

Both repos' names for the provenance helpers are kept as aliases
(`provenance_line` and `check_provenance` from tender-review,
`snapshot_vintage` and `snapshot_staleness_warning` from the toolkit) so a
consumer shim is an import rather than a rewrite.

## Verifying a change to the resolver

Run all three. They answer different questions and the first two are not
substitutes for the third.

```
python -m pytest -q              # the rules, and the vocabulary
python tools/parity_report.py    # still identical to both source repos?
python -m ruff check .
```

If you change resolver behaviour deliberately, `parity_report.py` will go red
against whichever source repo you moved away from. That is it working. Update
the source repo in the same round, or record why the two now differ, the way
`_policy.py` does for the CHS wall.
