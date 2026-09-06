"""tr#359, 6 Sep 2026: a bare or glued-L equal-angle triple.

`fsg-tender-review`'s own detailer dialect (measured against a real Tier A
pack, FSG-25Q-319) writes an equal angle three ways that never carry a
spaced `L` or the word `ANGLE`: `90x90x8`, `L90x90x8`, `90x90x8L`. None of
those spellings reached `_resolver.py`'s existing dialect paths, so all
three were an honest `unresolved` miss.

These tests pin two separate things:

1. The eight real priced combinations resolve, in all three spellings.
2. The mechanism, not just the answer: a bad triple must refuse even where
   `nearest()` would have rounded it to a real section. `_bare_equal_angle`
   does an EXACT `self.get()` lookup and must never route through
   `canonical_candidates()`/`nearest()` -- the same discipline as the
   Lysaght cold-formed alias in the same module.
"""
from __future__ import annotations

from fsg_common import sections

# Eight real, priced 90_Lists rows, spanning several leg sizes.
_PRICED_COMBOS = [
    ("90", "6", "90EA6"),
    ("90", "8", "90EA8"),
    ("65", "6", "65EA6"),
    ("75", "6", "75EA6"),
    ("50", "5", "50EA5"),
    ("100", "8", "100EA8"),
    ("125", "8", "125EA8"),
    ("150", "10", "150EA10"),
]


def test_bare_triple_resolves_to_the_priced_equal_angle():
    for leg, thickness, expected_id in _PRICED_COMBOS:
        raw = f"{leg}x{leg}x{thickness}"
        section, how = sections.resolve(raw)
        assert section is not None, raw
        assert section.section_id == expected_id, raw
        assert how == "canonical", raw


def test_leading_glued_l_resolves_the_same_way():
    for leg, thickness, expected_id in _PRICED_COMBOS:
        raw = f"L{leg}x{leg}x{thickness}"
        section, how = sections.resolve(raw)
        assert section is not None, raw
        assert section.section_id == expected_id, raw
        assert how == "canonical", raw


def test_trailing_glued_l_resolves_the_same_way():
    for leg, thickness, expected_id in _PRICED_COMBOS:
        raw = f"{leg}x{leg}x{thickness}L"
        section, how = sections.resolve(raw)
        assert section is not None, raw
        assert section.section_id == expected_id, raw
        assert how == "canonical", raw


def test_the_separator_and_case_do_not_matter():
    for raw, expected_id in (
        ("90X90X8L", "90EA8"), ("90*90*8L", "90EA8"),
        ("L90X90X8", "90EA8"), ("l90x90x8", "90EA8"),
    ):
        section, how = sections.resolve(raw)
        assert section is not None and section.section_id == expected_id, raw
        assert how == "canonical", raw


def test_a_doubly_glued_l_refuses_rather_than_guessing_which_end_is_noise():
    """'L90x90x8L' is not a spelling this dialect is known to use. Refuse it
    honestly rather than silently picking a side."""
    section, how = sections.resolve("L90x90x8L")
    assert section is None
    assert how == "unresolved"


def test_an_unequal_leg_triple_is_not_an_equal_angle_and_does_not_resolve_here():
    """100x50x6 names a genuinely different shape (unequal angle territory),
    not a garbled equal angle. This path must not guess an EA for it."""
    section, how = sections.resolve("100x50x6")
    assert section is None
    assert how == "unresolved"


def test_a_garbled_thickness_refuses_even_though_it_names_a_real_leg_size():
    """56 has no EA family and 4mm is not one of its thicknesses -- an
    honest, uninteresting miss."""
    section, how = sections.resolve("56x56x4")
    assert section is None
    assert how == "unresolved"


def test_the_exact_lookup_refuses_a_triple_nearest_would_have_rounded():
    """The mechanism, not just the outcome. 90EA8.3 is not a real section id,
    but `nearest()` -- given the chance -- rounds an 8.3 thickness to the
    real 90EA8 row (within its own 5% tolerance). If this fix routed through
    `canonical_candidates()`/`nearest()` instead of `self.get()`, '90x90x8.3'
    would resolve to 90EA8 as a confident wrong mass. It must not.
    """
    # Prove nearest() really would round this, so the refusal below is the
    # new code's own exact-lookup discipline and not an accident of nearest
    # already being unable to find the family.
    assert sections.library().nearest("90EA8.3") is not None
    assert sections.library().nearest("90EA8.3").section_id == "90EA8"

    for raw in ("90x90x8.3", "L90x90x8.3", "90x90x8.3L"):
        section, how = sections.resolve(raw)
        assert section is None, raw
        assert how == "unresolved", raw


def test_a_type_word_already_present_is_not_double_handled_here():
    """'90 x 90 x 8 EA' already resolves through the existing canonical
    dialect path long before this check is ever reached -- confirming this
    fix adds a path rather than replacing one."""
    section, how = sections.resolve("90 x 90 x 8 EA")
    assert section is not None and section.section_id == "90EA8"
    assert how in ("exact", "canonical")


def test_a_nonstandard_thickness_stays_an_honest_miss():
    """90x90x7 names a real leg size but 7mm is not a 90EA thickness (6, 8,
    10 are). No family-adjacent guess -- an honest miss, same as the
    garbled-thickness case above."""
    section, how = sections.resolve("90x90x7")
    assert section is None
    assert how == "unresolved"
