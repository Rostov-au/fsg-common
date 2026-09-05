"""The shared notation corpus. Used by the tests and by `tools/parity_report.py`.

Three layers, deliberately.

**1. VOCABULARY** is the twin-parity vocabulary, copied verbatim from
`fsg-tender-review/tests/test_resolver_twin_parity.py` at `origin/main`
(3 Sep 2026). Every entry earned its place by being a notation the two
resolvers were once found to disagree about, or one that a change to either
side was about to move. The comments are kept because they are the record of
why each was added.

**2. ANCHORS** are the load-bearing behaviours `fsg-tender-review/CLAUDE.md`
names in prose, paired with the rule each one pins. The vocabulary proves the
two implementations agree; the anchors prove the answer is the RIGHT one.
That distinction is not academic here. `10 SQ ROD` and `M30 THREADED ROD`
were both wrong in BOTH resolvers for months, agreeing the whole time,
because neither token had ever appeared in the vocabulary.

**3. `library_sweep()`** feeds every section id in the snapshot back in as a
notation. Rule 15 of `fsg-estimating-crm/docs/multi-session-working.md`: a
corpus only catches what it exercises, so hand-picked cases are paired with a
structural sweep nobody chose case by case. It is the layer that would catch
a change breaking a family no author thought to list.
"""
from __future__ import annotations

import json

# --- layer 1: the twin-parity vocabulary, verbatim -------------------------
VOCABULARY = [
    # the seven that diverged (26 Aug 2026 audit)
    "6 mm FLOOR PLATE", "10 THK CHEQUER PLATE", "200x200x6 TREAD PLATE",
    "BASEPLATE 20", "8FP;", "FLT10*90", "PLT10*80",
    # the shared baseline
    "200 PFC", "250 UB 25", "310 UB 40", "125 x 125 x 9 SHS", "300 x 90 PFC",
    "76.1 OD 3.2 Pipe", "12 mm PLATE", "200 x 200 x 10 PL",
    "PLATE 10 THK 250 x 250", "125 x 125 x 8 L", "150 x 90 x 10 L",
    "C1 100 x 100 x 5 SHS", "BASE PLATE 20", "TEMPLATE 20", "NAMEPLATE 2",
    "LINERPL13*206.5", "Z20015", "LYS-C15024", "6061-T6 100 x 50 RHS",
    "21.3 CHS 2", "12 BPL", "BISALLOY 12", "16 ROD", "20 SQ", "",
    "60.3 OD 3.91 PIPE", "60.3 CHS 3.91", "273 CHS 6.35",
    # The SQ/ROD precedence family (31 Aug 2026). Both twins had ROD
    # outranking SQ, so `10 SQ ROD` came back as the round rod -- 21.6% under
    # the estimator, labelled `canonical`. They agreed while both were wrong,
    # which is what a vocabulary gap looks like from here: the two tokens
    # never appeared together in this list.
    "10 SQ ROD", "12 SQ ROD", "16 SQ ROD", "20 SQ ROD", "25 SQ ROD", "40 SQ ROD",
    "10 SQUARE ROD", "ROD 10 SQ", "10SQ ROD", "24 SQ ROD", "10 SQ BAR",
    "10 ROD", "24 ROUND BAR", "DIA 24 RND BAR", "400 SQ. x 20 PLATE",
    # The shape-modifier family (1 Sep 2026) -- the same lesson one step on.
    # THREADED and HEX name cross-sections 90_Lists carries no family for, so
    # both twins dropped the word and returned the plain ROD section as
    # `canonical`: 7-14% heavy on 189 detailer lines, asserted rather than
    # flagged. The finish and material modifiers sit beside them deliberately
    # -- the whole rule is that the three kinds stay three.
    "M12 THREADED ROD", "M30 THREADED ROD", "M36 THREADED ROD",
    "M16 THREADED STUD", "M12/4.6_THREADED_ROD", "ALL THREAD 16",
    "10 HEX ROD", "16 HEX BAR", "20 HEXAGONAL BAR",
    "GALV 10 ROD", "10 ROD (BLACK)", "STAINLESS 10 ROD",
    # The six the 3 Sep 2026 code review found missing: thickness taken as the
    # smallest dimension rather than the last, an asterisk join, an
    # underscore-joined member mark, an unequal angle read as an EA (27% over,
    # labelled canonical), and a flat bar that resolved written one way round
    # and not the other.
    "10 x 200 x 200 PL", "200*200*10 PL", "BIS250LK_250LR",
    "FL 100 X 10", "150 x 90 x 10 ANGLE",
    "M24 ROD", "200 UB 25 x 6061 LG", "100 x 75 x 6 EA",
]

#: Held OUT of the vocabulary upstream, and carried here on purpose.
#: The two source resolvers genuinely disagree on this one and the parity
#: gate would go red on every commit for a question no session may settle.
#: Excluding it from a gate is right; excluding it from a MEASUREMENT hides
#: the only real difference there is. See `fsg_common.sections._policy`.
KNOWN_OPEN_QUESTION = ["273 CHS 6.4"]

# --- layer 2: the anchors CLAUDE.md names, and the rule each pins ----------
ANCHORS = [
    ("200 PFC", "resolves, 22.9 kg/m"),
    ("200PFC", "the library's own spelling gives the same answer"),
    ("250UB", "unresolved, with its candidates named"),
    ("250 UB", "same, spaced"),
    ("BASEPLATE 12", "resolves to PL, never BPL"),
    ("BASE PLATE 12", "same, spaced"),
    ("12 PL", "the plain plate row"),
    ("12 BPL", "Bisalloy stays Bisalloy"),
    ("STAINLESS 10 ROD", "material modifier refuses as material-mismatch"),
    ("STAINLESS 12 PL", "material modifier refuses"),
    ("SS 10 ROD", "the abbreviation refuses too, added 5 Sep 2026"),
    ("SS 12 PL", "same shape"),
    ("S/S 10 ROD", "the slashed spelling refuses the same way"),
    ("GALV 10 ROD", "finish modifier drops: same steel, same mass"),
    ("GALVANISED 10 ROD", "finish modifier drops"),
    ("HDG 200 PFC", "finish modifier drops"),
    ("10 SQ ROD", "shape modifier drops to 10SQ, a real library row"),
    ("40 SQ ROD", "40SQ is a real row"),
    ("24 SQ ROD", "no 24SQ row, so an honest miss and not a guess"),
    ("THREADED ROD 16", "shape-modifier refusal, not the plain section"),
    ("M20 THREADED ROD", "shape-modifier refusal"),
    ("16 HEX ROD", "shape-modifier refusal"),
    ("HEX BAR 24", "shape-modifier refusal"),
    ("250UB25.7", "FSG rounds the mass, so this is the stored 250UB26"),
    ("250UB26", "the stored id resolves exactly"),
    ("6 mm FLOOR PLATE", "6FP, priced by area"),
]

#: Behaviour both source resolvers share that MAY be wrong. Carried in the
#: corpus so parity covers it, and listed here so it is not mistaken for an
#: endorsed answer.
#:
#: The `SS`/`S/S` gap this list used to carry was closed 5 Sep 2026: both
#: source resolvers already added them to `_NON_STEEL` on 3 Sep, in step with
#: each other, and this package's port simply predated that same-day change.
#: See `ANCHORS` above and `_resolver.py`'s own comment. Moved rather than
#: deleted outright as a reminder of the shape: a gap this list carries is
#: presumed live until a parity run against the current sources says
#: otherwise, not until someone remembers to check.
OBSERVED_GAPS = [
    ("BASEPLATE", "bare, no size: unresolved"),
]


# --- layer 3: the structural sweep ----------------------------------------
def library_sweep(snapshot_path: str) -> list[str]:
    """Every section id in the snapshot, fed back in as a notation."""
    with open(snapshot_path, encoding="utf-8") as fh:
        return [s["section_id"] for s in json.load(fh)["sections"]]


def build(snapshot_path: str) -> list[str]:
    """The merged corpus. Order-stable, duplicates removed."""
    out: list[str] = []
    seen: set[str] = set()
    for group in (VOCABULARY, KNOWN_OPEN_QUESTION,
                  [a for a, _ in ANCHORS], [g for g, _ in OBSERVED_GAPS],
                  library_sweep(snapshot_path)):
        for raw in group:
            if raw not in seen:
                seen.add(raw)
                out.append(raw)
    return out
