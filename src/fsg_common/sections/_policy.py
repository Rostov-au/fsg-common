"""The one behaviour the two source resolvers do not share.

Measured 3 Sep 2026 over an 835-notation corpus (`tools/parity_report.py`):
`fsg-tender-review/src/fsg_tender_review/resolve.py` and
`fsg-bluebeam-steel-standards/tools/fsg_mto/sections.py` returned the same
answer for 834 of them. The exception is a CHS wall written one decimal
short:

    273 CHS 6.4   ->  273CHS6.35, 41.77 kg/m, "canonical"   tender-review
    273 CHS 6.4   ->  273CHS6.35, 41.77 kg/m, "nearest"     Bluebeam toolkit

Same section and same mass either way. What moves is the verdict, and the
verdict is what decides whether an estimator is asked to look at the line.

WHY THIS IS A PARAMETER AND NOT A FIX. The question underneath it is what a
drawing means by `CHS 6.4`: the library's imperial 6.35 wall, or the AS/NZS
metric 6.4 wall the library does not carry. That is an estimator's
knowledge, not a developer's decision. It is open as item 1 of
Rostov-au/fsg-tender-review#184, "Questions for the estimators", and the
standing instruction on Rostov-au/fsg-tender-review#180 is explicit: "Both
resolvers stay as they are -- the toolkit on `nearest`, this repo on
`canonical` -- until an estimator answers."

So consolidating the two copies must not settle it as a side effect. A
shared package that quietly picked one would change a live answer in one of
the two repos, on a question that was deliberately held open, and nothing
downstream would report that it had changed.

WHEN IT IS ANSWERED: delete this module, inline the winning branch in
`_is_rounding`, drop the `rounding=` parameters, and delete
`test_open_question_is_not_settled`. The policy is scaffolding around one
unanswered question and should not outlive it.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoundingPolicy:
    """Whether a library ID one decimal from the drawing's number counts as a
    rounding (`canonical`) or as a near-miss (`nearest`).

    `decimal_tolerance` is None for whole-number rounding only. Both
    policies apply the whole-number rule -- `250 UB 25.7` against the
    library's `250UB26` is `canonical` either way; only the one-decimal
    clause differs.
    """

    name: str
    decimal_tolerance: float | None


#: fsg-tender-review's behaviour: a wall within 0.051 of the library's is a
#: rounding. Derived from 85 of 85 `nearest` outcomes in the 28 Aug 2026
#: Tier A run, all within 1% on mass.
TENDER_REVIEW = RoundingPolicy(name="tender-review", decimal_tolerance=0.051)

#: fsg-bluebeam-steel-standards' behaviour: whole-number rounding only, so a
#: one-decimal difference stays `nearest` and reaches an estimator.
BLUEBEAM = RoundingPolicy(name="bluebeam", decimal_tolerance=None)

#: Every policy, for tests that must cover both rather than the default one.
ALL_POLICIES = (TENDER_REVIEW, BLUEBEAM)
