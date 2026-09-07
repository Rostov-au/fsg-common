"""The 6 Sep 2026 code review, Part 1 item 1: three notations that resolved
to a wrong number labelled `canonical`, and the cases beside each of them.

Each of the three was a rule fixed once for the case named on 3 Sep and not
tested for the case next to it -- the re-run's own finding was that six
such fixes broke their neighbours. So every fix here ships with the
neighbouring spellings pinned in the same file: the ones that must keep
resolving exactly as they did, so the guard that stops the wrong number
cannot also stop the right one.

    6 x 100 x 10 FL     was 100FL6 (40% under)   -> an honest miss
    100 x 50 x 3 SHS    was 100SHS3 (36% over)   -> unresolved, RHS named
    10 PL 100 x 6000    was 100PL (10x to 20x)   -> 10PL
"""
from __future__ import annotations

import pytest

from fsg_common import sections


def _id(raw: str) -> str | None:
    section, _how = sections.resolve(raw)
    return section.section_id if section else None


def _how(raw: str) -> str:
    return sections.resolve(raw)[1]


# --- flat bar: the sorted candidate needs exactly two numbers ---------------

def test_a_count_before_a_flat_bar_is_not_read_as_its_thickness():
    """`6 x 100 x 10 FL` is six pieces of 100 x 10 flat. Sorting the first
    two numbers made the count the thickness: 100FL6, 40% under."""
    assert _id("6 x 100 x 10 FL") != "100FL6"
    assert _how("6 x 100 x 10 FL") == "unresolved"


def test_the_written_order_candidate_still_carries_a_trailing_length():
    """The count-first spelling loses the sorted candidate; the written-order
    one is untouched, so a flat with its length appended still resolves."""
    assert _id("100 x 10 FL x 6000") == "100FL10"


@pytest.mark.parametrize("raw", ["100 X 10 FL", "FL 100 X 10", "10 X 100 FL", "100x10 FLAT"])
def test_a_two_number_flat_bar_resolves_either_way_round(raw):
    """The rule the sorted candidate exists for: both dimension orders reach
    the library's width-first id."""
    assert _id(raw) == "100FL10"
    assert _how(raw) in ("exact", "canonical")


# --- square hollow: three numbers with unequal sides are not an SHS ---------

def test_unequal_sides_written_as_shs_stay_unresolved():
    """`100 x 50 x 3 SHS` is a rectangular section with the wrong word. The
    old branch dropped the 50 and asserted 100SHS3 at 36% over."""
    assert _how("100 x 50 x 3 SHS") == "unresolved"
    assert _id("100 x 50 x 3 SHS") is None


def test_the_rhs_row_for_those_sides_exists_and_is_what_the_estimator_would_pick():
    """The row the notation was probably reaching for. Named here so the test
    fails if the library stops carrying it, which would turn the refusal
    above from a choice into a gap."""
    section, how = sections.resolve("100 x 50 x 3 RHS")
    assert section is not None and section.section_id == "100x50RHS3"
    assert how in ("exact", "canonical")


@pytest.mark.parametrize("raw, expected", [
    ("100 x 100 x 5 SHS", "100SHS5"),
    ("C1 100 x 100 x 5 SHS", "100SHS5"),
    ("100 SHS 5", "100SHS5"),
    ("125 x 125 x 9 SHS", "125SHS9"),
    ("100x100x5 SHS", "100SHS5"),
])
def test_equal_sided_and_two_number_shs_spellings_still_resolve(raw, expected):
    assert _id(raw) == expected


def test_a_bare_shs_head_with_no_wall_still_names_its_candidates():
    """`100 x 100 SHS` gives no wall. It never resolved; what it must keep
    doing is name the family so an estimator can choose."""
    assert _how("100 x 100 SHS") == "unresolved"
    named = {s.section_id for s in sections.ambiguous_candidates("100 x 100 SHS")}
    assert "100SHS5" in named


# --- plate: a number against the PL token beats the dimension group --------

def test_a_thickness_written_against_the_plate_word_wins_over_the_group_minimum():
    """`10 PL 100 x 6000` is 10 mm plate, 100 wide, 6000 long. The group
    minimum read the 100 as the thickness: ten to twenty times the mass."""
    assert _id("10 PL 100 x 6000") == "10PL"


@pytest.mark.parametrize("raw", ["12 PL x 150 x 3000", "PLATE 12 250 x 250", "12 PL 150 x 3000"])
def test_the_adjacent_number_wins_on_either_side_of_the_word(raw):
    assert _id(raw) == "12PL"


@pytest.mark.parametrize("raw, expected", [
    ("200 x 200 x 10 PL", "10PL"),        # the adjacent 10 is inside the group: minimum
    ("250 x 250 x 12 PLATE", "12PL"),
    ("400 SQ. x 20 PLATE", "20PL"),
    ("PLATE 10 THK 250 x 250", "10PL"),   # THK still beats everything
    ("16 THK PL 300 x 300", "16PL"),
    ("12 mm PLATE", "12PL"),
    ("25 PL 2 No.", "25PL"),
    ("BASEPLATE 20", "20PL"),
    ("20 BASEPLATE", "20PL"),
    ("PL 10 x 100", "10PL"),
    ("GUSSET PLATE 10 x 200 x 200", "10PL"),
    ("2 x PL 10 x 100", "10PL"),          # a count before the word is not adjacent to it
])
def test_every_plate_spelling_the_group_rule_already_answered_is_unchanged(raw, expected):
    assert _id(raw) == expected


def test_a_number_inside_the_dimension_group_is_not_promoted_by_sitting_next_to_the_word():
    """`250 x 250 x 12 PLATE` and `PLATE 250 x 250 x 12` both put a number
    against the word, and both numbers are group members. The group minimum
    must keep answering; the adjacency rule is for a number OUTSIDE it."""
    assert _id("250 x 250 x 12 PLATE") == "12PL"
    assert _id("PLATE 250 x 250 x 12") == "12PL"
