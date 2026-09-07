"""The twin-parity vocabulary, ported into the package that replaced the twins.

`fsg-tender-review/tests/test_resolver_twin_parity.py` compared its resolver
against the Bluebeam toolkit's copy on a shared vocabulary and failed on any
disagreement. That test exists because the two copies were found, on 26 Aug
2026, to disagree on seven notations, one of them a different mass.

Once both repos import this package there are no twins left to compare, so
the vocabulary changes job rather than retiring. Here it does two things:

1. Every notation in it resolves, under BOTH rounding policies, without
   raising. The vocabulary is the set of notations known to exercise a
   grammar branch, so it is the cheapest broad regression net there is.
2. The one notation the twins genuinely disagree about still produces the
   two different answers, on purpose. If that ever collapses to one, either
   an estimator answered the question and the policy should be deleted, or
   the package silently settled it -- and those must not look alike.

The live three-way comparison against both source repos is
`tools/parity_report.py`, which reads them at a pinned git ref. It is not a
test: it needs both sibling checkouts, which CI does not have.
"""
from __future__ import annotations

import pytest
from vocabulary import KNOWN_OPEN_QUESTION, VOCABULARY, build, library_sweep

from fsg_common import sections

VERDICTS = {"exact", "canonical", "nearest", "cold-formed",
            "cold-formed-lysaght-assumed", "cold-formed-vendor-equivalent",
            "material-mismatch", "shape-modifier", "substitution",
            "unresolved"}


@pytest.fixture(scope="module")
def corpus():
    return build(sections.PACKAGED_SNAPSHOT)


@pytest.mark.parametrize("policy", sections.ALL_POLICIES, ids=lambda p: p.name)
@pytest.mark.parametrize("raw", VOCABULARY)
def test_the_vocabulary_resolves_under_both_policies(raw, policy):
    section, how = sections.resolve(raw, policy)
    assert how in VERDICTS, raw
    if how in ("unresolved", "material-mismatch", "shape-modifier", "cold-formed"):
        assert section is None, raw
    else:
        assert section is not None, raw


@pytest.mark.parametrize("raw", VOCABULARY)
def test_the_grammar_functions_never_raise(raw):
    sections.loose_key(raw)
    sections.canonical_candidates(raw)
    sections.cold_formed(raw)
    sections.shape_modifier(raw)
    sections.ambiguous_candidates(raw)
    sections.shape_modifier_candidates(raw)


def test_the_corpus_covers_more_than_its_authors_chose(corpus):
    """Rule 15: a corpus only catches what it exercises. The hand-picked
    cases are paired with every section id in the library, so a change that
    breaks a family nobody listed still goes red."""
    sweep = library_sweep(sections.PACKAGED_SNAPSHOT)
    assert len(sweep) > 700
    assert set(sweep) <= set(corpus)
    assert len(corpus) >= len(sweep) + 50


def test_every_library_section_resolves_to_itself(corpus):
    """The structural check behind the sweep. A section written exactly as
    the library files it must come back as itself, exactly -- any other
    answer means the index and the grammar disagree about the same string."""
    misses = []
    for section_id in library_sweep(sections.PACKAGED_SNAPSHOT):
        section, how = sections.resolve(section_id)
        if section is None or section.section_id != section_id or how != "exact":
            misses.append((section_id, section.section_id if section else None, how))
    assert not misses, f"{len(misses)} section(s) did not round-trip: {misses[:10]}"


# --- the open question ----------------------------------------------------

@pytest.mark.parametrize("raw", KNOWN_OPEN_QUESTION)
def test_open_question_is_not_settled(raw):
    """`273 CHS 6.4` is the one notation the two source resolvers disagree
    about, and it is an open question for FSG's estimators
    (Rostov-au/fsg-tender-review#184 item 1), not a defect.

    Both policies find the same section at the same mass. What differs is the
    verdict, and the verdict decides whether an estimator is asked to look.

    DELETE THIS TEST when the question is answered. It exists to stop the
    consolidation quietly picking a side, and it should not outlive the
    question it guards.
    """
    tr_section, tr_how = sections.resolve(raw, sections.TENDER_REVIEW)
    bb_section, bb_how = sections.resolve(raw, sections.BLUEBEAM)
    assert tr_section == bb_section, "the section must not move, only the verdict"
    assert tr_how == "canonical"
    assert bb_how == "nearest"


def test_the_policies_differ_on_that_and_nothing_else(corpus):
    """The policy is a scalpel or it is a second resolver. This measures
    which: exactly one notation in the whole corpus may answer differently
    under the two policies."""
    moved = []
    for raw in corpus:
        a = sections.resolve(raw, sections.TENDER_REVIEW)
        b = sections.resolve(raw, sections.BLUEBEAM)
        if a != b:
            moved.append(raw)
    assert moved == KNOWN_OPEN_QUESTION, moved


def test_both_policies_apply_whole_number_rounding(corpus):
    """Only the one-decimal clause differs. `250 UB 25.7` against the
    library's `250UB26` is `canonical` under both."""
    for policy in sections.ALL_POLICIES:
        section, how = sections.resolve("250UB25.7", policy)
        assert (section.section_id, how) == ("250UB26", "canonical"), policy.name


# --- the shape of the record ----------------------------------------------

def test_the_snapshot_threshold_is_the_one_both_repos_agreed_on():
    """The toolkit read 30 with a comment claiming it matched the other
    repo's 90, so the repo that does not refresh the snapshot warned three
    times sooner than the one that does. Aligned 28 Aug 2026."""
    assert sections.STALE_AFTER_DAYS == 90
    assert sections.SNAPSHOT_STALE_AFTER_DAYS == sections.STALE_AFTER_DAYS


def test_absent_provenance_is_not_reported_as_fresh(tmp_path):
    """Absent is a third state, never the same answer as 'checked and fine'
    (rule 27). A snapshot with no generated date gets its own words."""
    import json

    p = tmp_path / "no-provenance.json"
    p.write_text(json.dumps({"sections": [], "_provenance": {}}), encoding="utf-8")
    warning = sections.staleness_warning(str(p))
    assert warning is not None
    assert "cannot be checked" in warning


def test_an_unreadable_snapshot_says_so_rather_than_printing_a_blank(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    assert "UNREADABLE" in sections.vintage_line(str(p))


# --- the surface a consumer shim needs ------------------------------------

def test_the_names_the_bluebeam_toolkit_imports_are_all_present():
    """`fsg-bluebeam-steel-standards/tools/fsg_mto/cli.py` and its
    `tools/tests/test_offline.py` import these by name from the module this
    package replaces. A shim can only be a re-export if every one of them is
    reachable from `fsg_common.sections`.

    Three are private. That is deliberate and explained in the package
    docstring; the point of this test is that dropping one silently breaks a
    consumer's test suite rather than this one's.
    """
    needed = [
        # cli.py
        "default_snapshot_path", "load_section_library",
        "load_section_library_from_snapshot", "snapshot_staleness_warning",
        "snapshot_vintage",
        # columns.py, schedule.py, takeoff.py
        "Section", "SectionLibrary",
        # test_offline.py, including the private three
        "canonical_candidates", "cold_formed", "loose_key",
        "_NON_STEEL", "_SHAPE_MODIFIER", "_looks_like_mark",
        "COLD_FORMED", "SNAPSHOT_STALE_AFTER_DAYS",
    ]
    missing = [n for n in needed if not hasattr(sections, n)]
    assert not missing, f"a consumer shim would fail on: {missing}"


def test_the_names_fsg_tender_review_imports_are_all_present():
    """The other consumer's surface: `resolve.py`'s public API plus the
    `Section` its `classification.py` exports."""
    needed = [
        "resolve", "library", "SectionLibrary", "Section", "loose_key",
        "canonical_candidates", "cold_formed", "shape_modifier",
        "ambiguous_candidates", "shape_modifier_candidates", "mass_of",
        "substitutions", "COLD_FORMED", "NEAREST_TOLERANCE", "NEAREST_MARGIN",
        "HEAD_TOLERANCE",
    ]
    missing = [n for n in needed if not hasattr(sections, n)]
    assert not missing, f"a consumer shim would fail on: {missing}"
