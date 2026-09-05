"""The behaviours `fsg-tender-review/CLAUDE.md` names, pinned as assertions.

`test_sections_parity.py` proves this package answers what the two source
resolvers answer. That is agreement, not correctness, and the two come
apart: `10 SQ ROD` and `M30 THREADED ROD` were wrong in BOTH resolvers for
months while every parity check passed, because neither token was in the
vocabulary being compared.

So these tests do the other half. Each one states the rule from CLAUDE.md
and checks the answer against it, so a change that moves both copies the
same wrong way still goes red here.
"""
from __future__ import annotations

import pytest
from vocabulary import ANCHORS, OBSERVED_GAPS

from fsg_common import sections


def test_the_library_loaded_at_all():
    """A resolver over an empty library resolves nothing and reports it as an
    honest miss, so every test below would pass green against no data."""
    lib = sections.library()
    assert len(lib) > 700, f"only {len(lib)} sections -- is the snapshot right?"


def test_provenance_is_stated():
    """Rows, date and hash, on every run. A result nobody can attribute to a
    library version is not reproducible."""
    line = sections.vintage_line()
    assert "ABSENT" not in line, line
    assert "sections, generated" in line


# --- the resolver's own rules ---------------------------------------------

def test_200_pfc_is_22_9_kg_per_m():
    section, how = sections.resolve("200 PFC")
    assert section.section_id == "200PFC"
    assert section.mass_kg_per_m == 22.9
    assert how == "exact"


def test_the_spaced_and_library_spellings_agree():
    assert sections.resolve("200 PFC")[0] == sections.resolve("200PFC")[0]


def test_a_bare_depth_is_unresolved_with_its_candidates_named():
    """`250UB` is genuinely three commercial sizes. The drawing has not
    chosen, so the resolver must not either -- but it names them, or the
    estimator gets a flat 'unresolved' and no way to raise a useful RFI."""
    section, how = sections.resolve("250UB")
    assert section is None
    assert how == "unresolved"
    named = [s.section_id for s in sections.ambiguous_candidates("250UB")]
    assert named == ["250UB26", "250UB31", "250UB37"]


def test_baseplate_is_pl_and_never_bpl():
    """BPL is Bisalloy. Reading a base plate as Bisalloy prices the wrong
    steel."""
    for raw in ("BASEPLATE 12", "BASE PLATE 12"):
        section, _how = sections.resolve(raw)
        assert section.section_id == "12PL", raw
    assert sections.resolve("12 BPL")[0].section_id == "12BPL"


def test_fsg_ids_round_the_mass_so_matching_is_on_mass_not_digits():
    """`250UB25.7` is stored `250UB26`."""
    section, how = sections.resolve("250UB25.7")
    assert section.section_id == "250UB26"
    assert section.mass_kg_per_m == 25.7
    assert how == "canonical"


# --- the three kinds of modifier, which must not blur ---------------------

def test_a_material_modifier_refuses():
    """90_Lists is entirely steel. Matching aluminium or stainless against it
    prices a different metal as steel."""
    for raw in ("STAINLESS 10 ROD", "STAINLESS 12 PL", "6061-T6 100 x 50 RHS"):
        section, how = sections.resolve(raw)
        assert section is None, raw
        assert how == "material-mismatch", raw


def test_a_finish_modifier_drops_because_the_mass_is_unchanged():
    """GALV is the same steel at the same mass."""
    plain = sections.resolve("10 ROD")[0]
    for raw in ("GALV 10 ROD", "GALVANISED 10 ROD", "10 ROD (BLACK)"):
        section, _how = sections.resolve(raw)
        assert section == plain, raw
        assert section.mass_kg_per_m == plain.mass_kg_per_m, raw
    assert sections.resolve("HDG 200 PFC")[0].section_id == "200PFC"


def test_a_shape_modifier_drops_only_where_the_library_has_that_shape():
    """`10SQ` through `40SQ` are real rows, so square evidence has somewhere
    real to go and the answer is the square bar, not the round one."""
    section, how = sections.resolve("10 SQ ROD")
    assert section.section_id == "10SQ"
    assert how == "canonical"
    assert sections.resolve("40 SQ ROD")[0].section_id == "40SQ"


def test_a_shape_the_library_lacks_is_an_honest_miss_not_a_guess():
    """There is no 24SQ row. The answer is a miss, never the round bar."""
    section, how = sections.resolve("24 SQ ROD")
    assert section is None
    assert how == "unresolved"


def test_threaded_and_hex_refuse_rather_than_assert_the_plain_section():
    """A threaded rod runs 7-14% lighter than the plain bar of the same
    nominal diameter. Dropping the word and returning the plain section is a
    confidently wrong mass, not a near miss."""
    for raw in ("THREADED ROD 16", "M20 THREADED ROD", "M30 THREADED ROD",
                "16 HEX ROD", "HEX BAR 24"):
        section, how = sections.resolve(raw)
        assert section is None, raw
        assert how == "shape-modifier", raw


def test_a_shape_modifier_refusal_names_the_word_and_the_section_ruled_out():
    """A refusal an estimator cannot act on is only half the rule. The word
    says why; the anchor says what plain bar the rate is quoted off."""
    assert sections.shape_modifier("M30 THREADED ROD") == "THREADED"
    assert sections.shape_modifier("16 HEX ROD") == "HEX"
    anchor = sections.shape_modifier_candidates("M30 THREADED ROD")
    assert [s.section_id for s in anchor] == ["30ROD"]


def test_floor_plate_is_priced_by_area():
    section, _how = sections.resolve("6 mm FLOOR PLATE")
    assert section.section_id == "6FP"
    assert section.is_plate
    assert section.kg_per_m2 == 49.1


def test_mass_of_hands_back_an_AREA_mass_for_floor_plate():
    """A trap, pinned as behaviour because it is behaviour, not a wish.

    `mass_of()` is documented to return "None for a plate or anything else
    the library prices by area rather than by length". That holds for the
    `PL` family, whose `mass_kg_per_m` really is None. It does NOT hold for
    floor plate: `90_Lists` files an `FP` row's kg/m2 in the kg/m COLUMN, so
    `mass_kg_per_m` is 49.1 and `mass_of` returns it through an API named and
    documented per metre.

    A caller doing `qty * length_m * mass_of(...)` on a floor-plate line
    therefore multiplies kg/m2 by metres. That is precisely the arithmetic
    `Section.is_plate` was added to stop, reached through a different door,
    and `is_plate` is right here while `mass_of` is the one that forgets.

    Carried, not fixed. Changing `mass_of` changes what two callers in
    `fsg-tender-review` compute, and this package exists to consolidate the
    resolver without moving any answer. Raised for that repo; run
    `tools/known_issues.py` for the live reproducer.
    """
    assert sections.mass_of("6 mm FLOOR PLATE") == 49.1
    assert sections.resolve("6 mm FLOOR PLATE")[0].kg_per_m2 == 49.1
    # the PL family, where the documented contract does hold
    assert sections.mass_of("12 PL") is None
    assert sections.resolve("12 PL")[0].is_plate


# --- the anchor table, as a table -----------------------------------------

@pytest.mark.parametrize("raw,rule", ANCHORS)
def test_every_anchor_resolves_without_raising(raw, rule):
    """The rule text is in the id so a failure names the rule it broke."""
    section, how = sections.resolve(raw)
    assert how in ("exact", "canonical", "nearest", "cold-formed",
                   "material-mismatch", "shape-modifier", "substitution",
                   "unresolved"), f"{raw}: {rule}"
    if section is not None:
        assert section.section_id


@pytest.mark.parametrize("raw,note", OBSERVED_GAPS)
def test_observed_gaps_are_recorded_not_asserted(raw, note):
    """These do NOT pin desired behaviour. They exist so the corpus covers a
    case the resolvers may be getting wrong, and so a change to it is visible
    rather than silent. See `vocabulary.OBSERVED_GAPS`."""
    section, how = sections.resolve(raw)
    assert how in ("exact", "canonical", "nearest", "unresolved",
                   "material-mismatch", "shape-modifier"), f"{raw}: {note}"


def test_ss_is_recognised_as_stainless():
    """5 Sep 2026: the gap this test used to pin is closed, with the
    estimator's answer already in hand -- both source resolvers added `SS`/
    `S/S` to `_NON_STEEL` on 3 Sep 2026 in step with each other (a decision
    already made, not a fresh one for this package), and fsg-common's own
    port had simply been taken before that same-day change landed.
    """
    assert sections.resolve("SS 10 ROD") == (None, "material-mismatch")
    assert sections.resolve("S/S 10 ROD") == (None, "material-mismatch")
    assert sections.resolve("STAINLESS 10 ROD") == (None, "material-mismatch")
    # The `\b` boundary stays exact: `SHS`/`RHS` are untouched, `SS` inside a
    # longer word is a substring and not a word.
    section, how = sections.resolve("100SHS4")
    assert section is not None and how == "exact"
