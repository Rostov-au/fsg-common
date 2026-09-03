# fsg-common

Code shared by the four FSG estimating repos. Pure Python, standard library
only.

Right now it contains one module, `fsg_common.sections`: FSG's steel section
library and the resolver that turns a drawing's own notation into a canonical
`Section_ID`, or into an honest miss.

```python
from fsg_common import sections

section, how = sections.resolve("200 PFC")
# ('200PFC', 22.9, 'exact')
```

## Why it exists

The resolver existed twice. `fsg-tender-review/src/fsg_tender_review/
resolve.py` was 848 lines, `fsg-bluebeam-steel-standards/tools/fsg_mto/
sections.py` was 878, and the two were kept in step by a git hook, a parity
test and a baseline script. The audit of 2 Sep 2026 (Part 3.8) called for one
package instead, and this is the first module of it.

The two copies had already drifted once. On 26 Aug 2026 they were found to
disagree on seven notations, one of them a different mass: `6 mm FLOOR PLATE`
was 49.1 kg/m2 in one and 47.1 in the other.

## The deliverable is the proof, not the move

```
python tools/parity_report.py
```

reads both source repos at a pinned git ref, runs one corpus of 836 notations
through all three implementations, and prints a count. As of 3 Sep 2026:

| Comparison | Agree | Differ |
|---|---|---|
| `fsg_common` (tender-review policy) vs `fsg-tender-review` | 836 | 0 |
| `fsg_common` (bluebeam policy) vs `fsg-bluebeam-steel-standards` | 836 | 0 |
| the two source resolvers against each other | 835 | 1 |

The corpus is three layers: the 70-entry twin-parity vocabulary ported from
`fsg-tender-review/tests/test_resolver_twin_parity.py`, 23 anchors naming the
rules `fsg-tender-review/CLAUDE.md` states in prose, and every one of the 750
section ids in the library fed back in as a notation. The third layer is there
because a corpus only catches what it exercises, and the two hardest defects
this resolver has had were both cases where the twins agreed with each other
and were both wrong.

## The one thing that differs, and why it is a parameter

`273 CHS 6.4` resolves to `273CHS6.35` at 41.77 kg/m in both repos.
`fsg-tender-review` labels it `canonical`; the Bluebeam toolkit labels it
`nearest`. Same section, same mass, different verdict, and the verdict is what
decides whether an estimator is asked to look at the line.

That is an open question for FSG's estimators, not a defect. It is item 1 of
Rostov-au/fsg-tender-review#184, and the standing instruction on #180 is that
both resolvers stay as they are until an estimator answers.

So the package carries it rather than settling it:

```python
sections.resolve("273 CHS 6.4", sections.TENDER_REVIEW)  # -> canonical
sections.resolve("273 CHS 6.4", sections.BLUEBEAM)       # -> nearest
```

`TENDER_REVIEW` is the default. Both policies agree on every other notation in
the corpus, and a test asserts that. When the estimators answer, delete
`_policy.py`, inline the winning branch, and delete the test that guards it.

## Layout

```
src/fsg_common/sections/
    _resolver.py    the grammar and SectionLibrary; a near-verbatim copy
    _section.py     the Section dataclass
    _snapshot.py    reading the library, from the packaged JSON or a workbook
    _policy.py      the one open question, carried
    substitutions.py  an estimator's recorded size swap
    data/           the generated section snapshot. Never hand-edit.
scripts/refresh_from_workbook.py   regenerates data/fsg_sections.json
tools/parity_report.py             the three-way comparison
tests/vocabulary.py                the corpus, shared by tests and tools
```

## The snapshot ships inside the package

`data/fsg_sections.json` is generated from `90_Lists` in the estimating
workbook and is byte-identical to the copy both source repos read today.
Never hand-edit it; change the workbook and run
`scripts/refresh_from_workbook.py`.

This is a behaviour change for the Bluebeam toolkit, and a deliberate one. Its
`default_snapshot_path()` pointed at whatever `fsg-tender-review` checkout sat
next to it on disk, so its answers depended on a working tree it did not
control. On 2 Sep 2026 two sessions disagreed about whether `Z20024` resolves,
one reading 733 sections and the other 750, and nothing reported a difference.
`FSG_SECTIONS_SNAPSHOT` still overrides the path when you need it to.

## Running the checks

```
python -m pytest -q          # 260 tests, no sibling repos needed
python -m ruff check .
python tools/parity_report.py   # needs both sibling checkouts
```

`parity_report.py` is not a test. It needs both sibling repos on disk, which
CI does not have, and it fails loudly rather than skipping when it cannot
establish the comparison, because a gate that compared nothing has not agreed
with anything.

## Not built yet

The audit named five modules. Only `sections` is built, because it was the
largest copy and the one with a live drift risk. Still duplicated across the
four repos: `check_no_client_data.py` (four copies, already drifted, 919 lines
in the CRM against 260 in tender-review), the sector enum, the revision
sequence, the `.env` readers and the `FSG_SSH_HOST` resolution.
