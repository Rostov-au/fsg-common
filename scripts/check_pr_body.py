#!/usr/bin/env python3
"""No pull request body or first comment carries an AI attribution line.

David's rule, all five FSG repos, 16 Sep 2026: no commit carries a
Co-Authored-By trailer and no pull request or document carries a
Generated-with-Claude-Code line. `fsg-estimating-crm` went first
(`scripts/check_pr_body.py` there, which also enforces a closing-keyword and
a word-count rule this repo has never had -- this script is deliberately
narrower and checks only the one rule David asked all five repos for).

Absent input does not answer: an unreadable comments file exits 2 (cannot
evaluate), never 0. Run locally with `--body-file` and optionally
`--comment-file`; CI passes `--event "$GITHUB_EVENT_PATH"` and the first
comment fetched with `gh api`. Exit 0 when the rule holds, 1 when it fails,
2 when the input could not be evaluated.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

EXEMPT_AUTHORS = frozenset({"dependabot[bot]", "github-actions[bot]"})

# David's rule, all five repos, 16 Sep 2026: no commit carries a
# Co-Authored-By trailer and no pull request or document carries a
# Generated-with-Claude-Code line. Case-insensitive -- a person capitalises
# either phrase however they type it, and the rule is not meant to be
# dodged by case.
FORBIDDEN_ATTRIBUTION = (
    ("Co-Authored-By", re.compile(r"Co-Authored-By", re.IGNORECASE)),
    ("Generated with", re.compile(r"Generated with", re.IGNORECASE)),
)


def word_count(text: str | None) -> int:
    return len(re.findall(r"\S+", text or ""))


def check(body: str | None, first_comment: str | None, author: str | None) -> list[str]:
    """The problems with this PR, in order; an empty list is a pass."""
    if author in EXEMPT_AUTHORS:
        return []
    problems: list[str] = []
    for phrase, pattern in FORBIDDEN_ATTRIBUTION:
        found_in = [name for name, text in
                    (("the body", body), ("the first comment", first_comment))
                    if text and pattern.search(text)]
        if found_in:
            problems.append(
                f"{' and '.join(found_in)} carries a \"{phrase}\" line; no commit, pull "
                f"request or document carries an attribution line")
    return problems


def first_comment_body(comments_json: str) -> str | None:
    """The body of the earliest issue comment in a `gh api .../comments`
    listing, or None when the listing is empty. Raises on anything else."""
    data = json.loads(comments_json)
    if not isinstance(data, list):
        raise ValueError(f"expected a JSON list of comments, got {type(data).__name__}")
    if not data:
        return None
    return data[0].get("body") or ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--event", help="GITHUB_EVENT_PATH: a pull_request event JSON")
    ap.add_argument("--comments", help="JSON list from `gh api repos/O/R/issues/N/comments`")
    ap.add_argument("--body-file", help="local use: a file holding the PR body")
    ap.add_argument("--comment-file", help="local use: a file holding the first comment")
    ap.add_argument("--author", default=None, help="local use: the PR author's login")
    args = ap.parse_args(argv)

    author = args.author
    first_comment: str | None = None
    comment_state = "first comment: not supplied (counted as 0 words)"
    try:
        if args.event:
            with open(args.event, encoding="utf-8") as fh:
                event = json.load(fh)
            pr = event.get("pull_request") or {}
            body = pr.get("body")
            author = (pr.get("user") or {}).get("login") or author
        elif args.body_file:
            with open(args.body_file, encoding="utf-8") as fh:
                body = fh.read()
        else:
            print("check_pr_body: give --event or --body-file", file=sys.stderr)
            return 2
        if args.comments:
            with open(args.comments, encoding="utf-8") as fh:
                first_comment = first_comment_body(fh.read())
            comment_state = ("first comment: none yet" if first_comment is None
                             else f"first comment: {word_count(first_comment)} words")
        elif args.comment_file:
            with open(args.comment_file, encoding="utf-8") as fh:
                first_comment = fh.read()
            comment_state = f"first comment: {word_count(first_comment)} words"
    except (OSError, ValueError) as exc:
        print(f"check_pr_body: CANNOT EVALUATE -- {exc}", file=sys.stderr)
        return 2

    problems = check(body, first_comment, author)
    print(f"check_pr_body: author {author or '?'}; body {word_count(body)} words; "
          f"{comment_state}")
    if author in EXEMPT_AUTHORS:
        print(f"check_pr_body: {author} is exempt (a bot's body is not ours to shape)")
        return 0
    if problems:
        for p in problems:
            print(f"::error::{p}")
        return 1
    print("check_pr_body: ok -- no attribution line in the body or first comment")
    return 0


if __name__ == "__main__":
    sys.exit(main())
