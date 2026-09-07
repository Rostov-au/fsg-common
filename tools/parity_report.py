#!/usr/bin/env python3
"""Prove `fsg_common.sections` answers what both source resolvers answer.

    python tools/parity_report.py

Reads three implementations, runs one notation corpus through all of them,
and prints a count:

    A  fsg_common.sections                        (this package)
    B  fsg-tender-review  src/.../resolve.py      at a pinned git ref
    C  fsg-bluebeam-steel-standards  .../sections.py   at a pinned git ref

A is compared against B and against C on the one shared library behaviour --
the `RoundingPolicy` split that used to make this a policy-per-repo
comparison (`tender-review` vs `bluebeam`) was answered and deleted 7 Sep
2026 (fsg-tender-review#184 Q25); both source repos converge on the same
verdicts now. B and C are also compared against each other, which is what
`fsg-tender-review/scripts/check_twin_parity.py` used to do and is reported
here so the package's verdict can be read next to the twins' own.

WHAT IT READS. Both siblings are read out of their git object stores at a
pinned ref (`git show <ref>:<path>`), never from whatever branch the clone
happens to have checked out. That rule is inherited from
`check_twin_parity.py`, which learned it the hard way: on 31 Aug 2026 it
reported all 23 baselined disagreements resolved because the sibling was
parked on a feature branch 8 commits ahead of `main`.

WHAT IT PRINTS EVERY TIME, including a clean run: the repo, ref, commit and
subject of each side, and the section snapshot's rows, generated date and
content hash. Both resolvers answer FROM that snapshot, so a difference in
section count reads as a resolver difference unless the count is on the
page. Two sessions lost a day to exactly that on 2 Sep 2026, one reading 733
sections while the other read 750.

Exit 0 when the package matches both sides on every notation. Exit 1 when it
does not, or when a comparison could not be established at all -- a gate that
compared nothing must say so rather than pass quietly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_SRC = REPO_ROOT / "src"
TESTS = REPO_ROOT / "tests"

TR_NAME = "fsg-tender-review"
BB_NAME = "fsg-bluebeam-steel-standards"
TR_FILES = {
    "fsg_tender_review/__init__.py": "src/fsg_tender_review/__init__.py",
    "fsg_tender_review/resolve.py": "src/fsg_tender_review/resolve.py",
    "fsg_tender_review/classification.py": "src/fsg_tender_review/classification.py",
    "fsg_tender_review/substitutions.py": "src/fsg_tender_review/substitutions.py",
    "fsg_tender_review/data/fsg_sections.json":
        "src/fsg_tender_review/data/fsg_sections.json",
    "fsg_tender_review/data/substitutions.json":
        "src/fsg_tender_review/data/substitutions.json",
}
BB_FILES = {
    "fsg_mto/__init__.py": "tools/fsg_mto/__init__.py",
    "fsg_mto/sections.py": "tools/fsg_mto/sections.py",
}

FIELDS = ["loose_key", "canonical_candidates", "cold_formed",
          "shape_modifier", "resolve"]


class Unavailable(RuntimeError):
    """A comparison could not be established. Never reported as agreement."""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """git in `repo`, with every GIT_* variable stripped.

    `git -C <path>` sets the working directory but GIT_DIR wins over it, so
    under a pre-commit hook this would resolve refs against the WRONG repo.
    `check_twin_parity.py` hit that on 31 Aug 2026.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, env=env)


def sibling(name: str, override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return (REPO_ROOT.parent / name).resolve()


def describe(repo: Path, ref: str) -> tuple[str, str]:
    """(short sha, "<date> <subject>") for `ref`, or raise."""
    if not repo.is_dir():
        raise Unavailable(f"sibling repo not found at {repo}")
    rev = git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if rev.returncode != 0 or not rev.stdout.strip():
        raise Unavailable(f"ref {ref!r} does not exist in {repo}")
    show = git(repo, "show", "-s", "--format=%h %cs %s", rev.stdout.strip())
    short, _, rest = show.stdout.strip().partition(" ")
    return short, rest


def materialise(repo: Path, ref: str, files: dict[str, str], dest: Path) -> Path:
    """Extract `files` from `repo` at `ref` into `dest`; return the sys.path root."""
    for rel, path_in_repo in files.items():
        blob = git(repo, "show", f"{ref}:{path_in_repo}")
        if blob.returncode != 0:
            raise Unavailable(
                f"{path_in_repo} does not exist in {repo} at {ref} -- nothing "
                "can be compared, so this fails rather than reporting agreement")
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(blob.stdout, encoding="utf-8")
    return dest


def snapshot_facts(path: str) -> dict:
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    prov = data.get("_provenance") or {}
    return {"path": path, "rows": len(data.get("sections") or []),
            "generated": prov.get("generated"),
            "content_sha256": prov.get("content_sha256"),
            "file_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()}


def call(fn, raw):
    """Record the answer, or the exception as the answer.

    A resolver that raises where its twin returns is a divergence, and a
    harness that dies on it reports nothing at all.
    """
    try:
        return {"ok": True, "value": fn(raw)}
    except Exception as exc:  # noqa: BLE001 - the exception IS the observation
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def fields_of(sec):
    if sec is None:
        return None
    return {"section_id": sec.section_id, "category": sec.category,
            "build_default": sec.build_default,
            "mass_kg_per_m": sec.mass_kg_per_m,
            "plate_thickness_mm": sec.plate_thickness_mm,
            "plate_kg_per_m2": sec.plate_kg_per_m2,
            "is_plate": sec.is_plate, "kg_per_m2": sec.kg_per_m2}


def probe(grammar, lib, corpus: list[str]) -> dict[str, dict]:
    out = {}
    for raw in corpus:
        rec = {
            "loose_key": call(grammar.loose_key, raw),
            "canonical_candidates": call(grammar.canonical_candidates, raw),
            "cold_formed": call(grammar.cold_formed, raw),
            "shape_modifier": call(grammar.shape_modifier, raw),
        }
        res = call(lib.resolve, raw)
        if res["ok"]:
            sec, how = res["value"]
            rec["resolve"] = {"ok": True, "section": fields_of(sec), "how": how}
        else:
            rec["resolve"] = res
        out[raw] = rec
    return out


def diff(a: dict, b: dict) -> list[tuple[str, str, object, object]]:
    found = []
    for raw in a:
        for f in FIELDS:
            if a[raw][f] != b[raw][f]:
                found.append((raw, f, a[raw][f], b[raw][f]))
    return found


def report(title: str, a: dict, b: dict, total: int) -> int:
    d = diff(a, b)
    differing = len({x[0] for x in d})
    print(f"{title}")
    print(f"    compared {total} notations x {len(FIELDS)} fields")
    print(f"    agree    {total - differing}")
    print(f"    differ   {differing}")
    for raw, f, va, vb in d:
        print(f"      {raw!r}  [{f}]")
        print(f"        A: {json.dumps(va, sort_keys=True, default=str)}")
        print(f"        B: {json.dumps(vb, sort_keys=True, default=str)}")
    return differing


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tender-review-repo", default=os.environ.get("FSG_TR_REPO"))
    ap.add_argument("--bluebeam-repo", default=os.environ.get("FSG_TWIN_REPO"))
    ap.add_argument("--ref", default=os.environ.get("FSG_TWIN_REF", "origin/main"),
                    help="git ref to read BOTH siblings at (default: origin/main)")
    args = ap.parse_args(argv)

    tr_repo = sibling(TR_NAME, args.tender_review_repo)
    bb_repo = sibling(BB_NAME, args.bluebeam_repo)

    sys.path.insert(0, str(PKG_SRC))
    sys.path.insert(0, str(TESTS))
    import vocabulary  # noqa: E402

    from fsg_common import sections as common  # noqa: E402

    snapshot = common.PACKAGED_SNAPSHOT
    # Every side must answer from ONE library file, or this measures the
    # snapshot instead of the resolver.
    os.environ["FSG_SECTIONS_SNAPSHOT"] = snapshot
    facts = snapshot_facts(snapshot)
    corpus = vocabulary.build(snapshot)

    with tempfile.TemporaryDirectory(prefix="fsg-common-parity-") as tmp:
        tmpd = Path(tmp)
        try:
            tr_sha, tr_subject = describe(tr_repo, args.ref)
            bb_sha, bb_subject = describe(bb_repo, args.ref)
            tr_root = materialise(tr_repo, args.ref, TR_FILES, tmpd / "tr")
            bb_root = materialise(bb_repo, args.ref, BB_FILES, tmpd / "bb")
        except Unavailable as exc:
            print(f"parity_report.py: CANNOT ESTABLISH THE COMPARISON -- {exc}")
            print("  Nothing was compared. That is a failure, not agreement.")
            return 1

        print("fsg-common section resolver parity")
        print(f"  package  {REPO_ROOT}")
        print("  A        fsg_common.sections")
        print(f"  B        {tr_repo}")
        print(f"           {args.ref} -> {tr_sha}  {tr_subject}")
        print(f"  C        {bb_repo}")
        print(f"           {args.ref} -> {bb_sha}  {bb_subject}")
        print(f"  library  {facts['rows']} sections, generated "
              f"{facts['generated']}, sha {facts['content_sha256']}")
        print(f"           file sha256 {facts['file_sha256'][:16]}  {facts['path']}")
        print(f"  corpus   {len(corpus)} notations "
              f"({len(vocabulary.VOCABULARY)} twin-parity vocabulary, "
              f"{len(vocabulary.ANCHORS)} CLAUDE.md anchors, "
              f"{len(vocabulary.library_sweep(snapshot))} library sweep, "
              f"deduplicated)")
        print(f"  python   {sys.version.split()[0]}")
        print()

        sys.path.insert(0, str(tr_root))
        sys.path.insert(0, str(bb_root))
        from fsg_mto import sections as bb  # noqa: E402
        from fsg_tender_review import resolve as tr  # noqa: E402

        a = probe(common, common.library(), corpus)
        b = probe(tr, tr.library(), corpus)
        c = probe(bb, bb.load_section_library_from_snapshot(
            bb.default_snapshot_path()), corpus)

    n = len(corpus)
    bad = 0
    bad += report(f"A vs B   fsg_common vs {TR_NAME}", a, b, n)
    print()
    bad += report(f"A vs C   fsg_common vs {BB_NAME}", a, c, n)
    print()
    twins = report(f"B vs C   {TR_NAME} vs {BB_NAME}  (the twins' own gate)",
                   b, c, n)
    print()
    if bad:
        print(f"VERDICT: FAIL -- the package differs from a source resolver on "
              f"{bad} notation(s)")
        return 1
    print(f"VERDICT: PASS -- fsg_common matches both source resolvers on all "
          f"{n} notations")
    if twins:
        print(f"         The two source resolvers still differ from each other on "
              f"{twins} notation(s) -- unexpected now the rounding-policy split "
              f"is deleted; worth checking why rather than assuming it's benign.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
