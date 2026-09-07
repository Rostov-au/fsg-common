"""The section library's PROVENANCE guard: the right workbook, not just a clean one.

Why this file exists
--------------------
`tests/test_refresh_write_guard.py` pins the guard against a workbook that did
not READ cleanly -- formulas returned as text, every mass `None`. That is one
half of the 1 Sep 2026 accident. This file pins the other half, which that
guard does not catch: a workbook that read **perfectly** and was simply the
**wrong one**.

Measured by construction, 2 Sep 2026, against the library committed at
`bd85cc2` (21 Aug) -- stale, and structurally flawless:

    validation_failures(stale)  ->  []          <- it would have been written
    75PFC        6.65   (the corrected library carries 5.92)
    125x75RHS6  17.92   (the corrected library carries 16.70)

Both controls passed in that run -- a mass-stripped payload was refused and the
current committed library was accepted -- so the clean result on the stale
payload is the guard's answer, not a broken probe.

The two signals the accident left, and each has a test below:

  1. `_provenance.source` differed between the committed copy and the workbook
     read, and **nothing compared them** -- `--check` least of all, since
     `content_sha256` is computed over the body only and the source is not in
     the hash it compares.
  2. The workbook read was **older** than the committed copy's `taken` date.

**ADR 14 is the reason `same_workbook` exists at all**, and the reason it is
tested on both hosts' worth of input: `_provenance.source` is a path that lives
in *data*, so it is compared on Windows here and on Linux in CI, and a
comparison built on `os.path.normcase` / `os.sep` answers differently on the
two for the same two strings without raising.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import refresh_from_workbook as R  # noqa: E402

LIVE = r"S:\Estimating\Reference\FSG_Estimating_Template.xlsx"
OTHER = r"S:\Estimating\Reference\FSG_Estimating_Template.bak-20260820.xlsx"


def _committed(source=LIVE, generated="2026-09-01"):
    return {"_provenance": {"source": source, "generated": generated},
            "sections": []}


# --------------------------------------------------------------------------
# same_workbook -- ADR 14. These are the cases that make a `normcase`-based
# comparison answer differently on Windows and on Linux.

def test_the_same_path_is_the_same_workbook():
    assert R.same_workbook(LIVE, LIVE)


def test_separator_style_does_not_make_it_a_different_workbook():
    """A hand-typed or JSON-round-tripped path may carry forward slashes. It is
    the same file, and on Linux `os.sep` would not even see the backslash form
    as having separators at all."""
    assert R.same_workbook(LIVE, LIVE.replace("\\", "/"))


def test_case_does_not_make_it_a_different_workbook():
    """Windows is case-insensitive and the share is a Windows share, so these
    are one file. `os.path.normcase` is the IDENTITY on Linux, so a comparison
    built on it calls them different in CI and the same on David's machine --
    the same input, two verdicts, no exception."""
    assert R.same_workbook(LIVE, LIVE.upper())


def test_a_genuinely_different_workbook_is_different():
    assert not R.same_workbook(LIVE, OTHER)


def test_a_missing_source_is_NOT_a_match():
    """The strict direction on purpose. An unrecorded source is the state the
    guard exists to stop being written, so it must not read as agreement."""
    assert not R.same_workbook(LIVE, None)
    assert not R.same_workbook(LIVE, "")
    assert not R.same_workbook(None, None)


# --------------------------------------------------------------------------
# provenance_refusals

def test_the_right_workbook_at_the_right_age_is_allowed():
    """The control this whole file needs: the ordinary correct regeneration
    must pass, or every test below proves only that the guard refuses."""
    assert R.provenance_refusals(
        workbook=LIVE, workbook_date=dt.date(2026, 9, 1),
        committed=_committed()) == []


def test_a_first_generation_with_no_committed_copy_is_allowed():
    assert R.provenance_refusals(
        workbook=LIVE, workbook_date=dt.date(2026, 9, 1), committed=None) == []


def test_a_DIFFERENT_workbook_is_refused():
    """Signal 1 of the accident. The committed copy named one workbook and the
    regeneration read another."""
    problems = R.provenance_refusals(
        workbook=OTHER, workbook_date=dt.date(2026, 9, 1),
        committed=_committed(source=LIVE))
    assert problems
    assert any("DIFFERENT workbook" in p for p in problems)
    assert any(OTHER in p and LIVE in p for p in problems), (
        "the refusal must NAME both paths -- an operator cannot act on "
        "'provenance mismatch' alone")


def test_an_OLDER_workbook_is_refused():
    """Signal 2. The 20 Aug copy cannot carry the 29 Aug corrections."""
    problems = R.provenance_refusals(
        workbook=LIVE, workbook_date=dt.date(2026, 8, 20),
        committed=_committed(generated="2026-09-01"))
    assert any("OLDER" in p for p in problems), problems


def test_a_NEWER_workbook_is_allowed_and_the_asymmetry_is_deliberate():
    """The rule is one-directional and says so. An mtime later than the
    committed copy proves nothing -- a copy onto the share stamps today's date
    whatever is inside -- so it must not be treated as a freshness certificate,
    only as the absence of provable staleness."""
    assert R.provenance_refusals(
        workbook=LIVE, workbook_date=dt.date(2026, 9, 30),
        committed=_committed(generated="2026-09-01")) == []


def test_the_same_DAY_is_allowed():
    """Regenerating twice in one day is the normal correction loop."""
    assert R.provenance_refusals(
        workbook=LIVE, workbook_date=dt.date(2026, 9, 1),
        committed=_committed(generated="2026-09-01")) == []


def test_an_unreadable_workbook_date_does_not_silently_pass_the_source_rule():
    """`workbook_date` returns None when it cannot stat the file. The age rule
    then cannot run -- but the SOURCE rule still must, or an unstattable file
    would buy a free pass on both."""
    problems = R.provenance_refusals(
        workbook=OTHER, workbook_date=None, committed=_committed(source=LIVE))
    assert any("DIFFERENT workbook" in p for p in problems), problems


def test_an_unreadable_committed_DATE_is_refused_rather_than_ignored():
    """A `generated` value that will not parse means the age comparison cannot
    be made. Skipping it quietly is the fail-open shape this repo keeps
    finding, so it is a refusal carrying its own reason."""
    problems = R.provenance_refusals(
        workbook=LIVE, workbook_date=dt.date(2026, 9, 1),
        committed=_committed(generated="1 Sep 2026"))
    assert any("unreadable" in p for p in problems), problems


def test_a_committed_copy_with_no_source_recorded_is_refused_and_says_so():
    problems = R.provenance_refusals(
        workbook=LIVE, workbook_date=dt.date(2026, 9, 1),
        committed={"_provenance": {"generated": "2026-09-01"}, "sections": []})
    assert any("no source recorded" in p for p in problems), problems


# --------------------------------------------------------------------------
# The two guards are independent, which is the point of adding this one.

def test_the_CONTENT_guard_does_not_catch_a_stale_workbook():
    """The measurement this card turns on, kept as a test so it cannot quietly
    stop being true. A stale library is structurally perfect -- every mass a
    real number, every anchor right -- so `validation_failures` returns nothing
    and only the provenance rule stands between it and the committed copy."""
    stale = {"sections": [
        {"section_id": "310UB40", "category": "TYP", "mass_kg_per_m": 40.4,
         "plate_thickness_mm": None, "plate_kg_per_m2": None},
        {"section_id": "200PFC", "category": "TYP", "mass_kg_per_m": 22.9,
         "plate_thickness_mm": None, "plate_kg_per_m2": None},
        # The value that actually moved: 6.65 in the 21 Aug library, 5.92 in
        # the corrected one. Nothing in the content guard knows which is right.
        {"section_id": "75PFC", "category": "TYP", "mass_kg_per_m": 6.65,
         "plate_thickness_mm": None, "plate_kg_per_m2": None},
    ]}
    assert R.validation_failures(stale) == [], (
        "if this ever fails the content guard has grown a rule about VALUES, "
        "and this file's premise needs re-measuring")
    assert R.provenance_refusals(
        workbook=OTHER, workbook_date=dt.date(2026, 8, 21),
        committed=_committed(source=LIVE, generated="2026-09-01"))


def test_the_PROVENANCE_guard_does_not_catch_a_bad_read():
    """And the converse, so neither is ever mistaken for the other: the right
    workbook read badly passes every provenance rule."""
    assert R.provenance_refusals(
        workbook=LIVE, workbook_date=dt.date(2026, 9, 1),
        committed=_committed()) == []
    assert R.validation_failures({"sections": []})


# --------------------------------------------------------------------------
# 4 Sep 2026: the source moved from S: to the sibling repo's tracked template
# (David's decision). That turned `_provenance.source` from a share path --
# host-independent wherever the share is mapped -- into a path under whichever
# checkout generated it. ADR 14's rule is about parsing such a path; this is
# the other half, WRITING one that another host can still compare.
# --------------------------------------------------------------------------

def test_the_sibling_template_is_recorded_in_a_form_every_host_can_compare():
    r"""An absolute path here would refuse everywhere but the generating machine.

    `C:\Users\<someone>\fsg-estimating-tools\...` names nothing in CI and
    nothing on a second workstation, so `same_workbook` would answer False and
    `provenance_refusals` would report PROVENANCE MISMATCH -- indistinguishable
    from the real accident this file exists to catch. Collapsing the sibling
    template to one agreed spelling is what keeps the two apart.
    """
    absolute = R._SIBLING_TEMPLATE
    assert R.portable_source(absolute) == R.PORTABLE_SIBLING
    assert not R.PORTABLE_SIBLING.startswith(("C:", "/", "\\")), (
        "the recorded form must not be rooted on any one host's filesystem")


def test_portable_source_leaves_every_other_workbook_alone():
    """There is no portable name for an arbitrary path, and inventing one
    would make two different workbooks compare equal -- the exact failure the
    guard exists to prevent, introduced by the fix for a different one."""
    assert R.portable_source(LIVE) == LIVE
    assert R.portable_source(OTHER) == OTHER
    assert R.portable_source(None) is None
    assert R.portable_source("") == ""


def test_a_different_workbook_is_still_refused_after_the_move():
    """The falsification. If `portable_source` collapsed too much, this would
    pass silently and the guard would be gone rather than relocated."""
    assert R.provenance_refusals(
        workbook=LIVE, workbook_date=dt.date(2026, 9, 4),
        committed=_committed(source=R.PORTABLE_SIBLING,
                             generated="2026-09-04")), (
        "the S: copy must not be accepted against a library taken from the "
        "sibling template -- S: still carries the four fictional CHS sizes")


def test_the_absolute_and_relative_spellings_of_the_sibling_are_one_workbook():
    """A library generated before this change recorded the absolute path. It
    must keep verifying rather than demanding a regeneration -- both sides of
    the comparison go through `portable_source` for that reason."""
    assert R.provenance_refusals(
        workbook=R._SIBLING_TEMPLATE, workbook_date=dt.date(2026, 9, 4),
        committed=_committed(source=R._SIBLING_TEMPLATE,
                             generated="2026-09-04")) == []
    assert R.provenance_refusals(
        workbook=R._SIBLING_TEMPLATE, workbook_date=dt.date(2026, 9, 4),
        committed=_committed(source=R.PORTABLE_SIBLING,
                             generated="2026-09-04")) == []
