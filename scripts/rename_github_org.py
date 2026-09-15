"""Prep tool for the GitHub-org rename: catalogue and (optionally) replace every
literal `Rostov-au/` across all five FSG repos' tracked files.

    python scripts/rename_github_org.py <new-org>                    # dry run (default)
    python scripts/rename_github_org.py <new-org> --apply            # write for real
    python scripts/rename_github_org.py <new-org> --repos-root DIR   # non-default layout
    python scripts/rename_github_org.py <new-org> --only REPO [...]  # restrict to some repos

WHY THIS EXISTS
---------------
crm#655 gate line 7 (David, 15 Sep 2026): moving the five repos into an
FSG-owned GitHub organisation, with secrets and self-hosted runners
re-attached, is one of the stated conditions for calling the work server
ready. crm#655's own transfer checklist names the mechanical half of that
move by hand: once each repo is transferred, "a lane replaces every literal
`Rostov-au/` in CLAUDE.md, ci.yml, health.yml, validate.yml, docs/ and
scripts/ across the five repos." tr#669 is that prep, as a **dry run** --
the org has not been created yet (crm#655's own checklist still has
"create the company git and n8n accounts" ahead of it), so this script's
job today is to prove the replacement is correct and mechanical, not to
run it against any of the five real checkouts.

DRY RUN BY DEFAULT -- the same gate every other multi-file writer in this
estate uses (`fsg-estimating-tools/scripts/deploy_workbook.py`'s `--apply`
is the pattern this follows). Default mode reads and prints; nothing on
disk changes until `--apply` is passed explicitly. There is no `--force`
and no implicit confirmation.

WHAT IT TOUCHES
----------------
Git-TRACKED files only, read via `git -C <repo> ls-files` -- never a
filesystem walk, so a build artefact, a `.venv`, or an untracked scratch
file is never touched. A file that fails a strict utf-8 decode (a binary,
or something in another encoding) is SKIPPED and reported, never
corrupted by a lossy rewrite.

The five repos are addressed by name and are expected as sibling
directories of `--repos-root` (default: this script's own repo's parent
directory -- the layout this estate's machines actually use, since this
script lives at `<repos-root>/fsg-common/scripts/rename_github_org.py`).
A repo directory that is missing, or exists but is not a git working
tree, REFUSES the whole run rather than being silently skipped -- an
absent repo must not read as "nothing to rename there." `--only` narrows
the *scope* deliberately (and is how the throwaway-clone test below
targets a single repo without the other four existing); a repo outside
`--only` is never even checked for existence.

THE NEW ORG NAME IS NEVER GUESSED. It is a required positional argument,
with no default and no environment-variable fallback -- crm#655 states
plainly that the org does not exist yet, so a tool that invented a
plausible-looking name would be worse than one that refuses to run
without it. It is validated against GitHub's own login rules (alphanumeric
and single internal hyphens) so a typo fails before anything is written,
not after.

WHAT IT REPLACES
------------------
Only the literal substring `Rostov-au/` -- including the trailing slash --
becomes `<new-org>/`. A bare `Rostov-au` with no trailing slash never
appears in the catalogue this script was written from (tr#669, all five
repos' tracked trees, 15 Sep 2026): every real occurrence is a repo
reference (`Rostov-au/fsg-common`), a URL segment
(`github.com/Rostov-au/...`), a `gh -R Rostov-au/<repo>` flag, or a
placeholder (`Rostov-au/repo#123`), always slash-terminated. Restricting
to the slash-terminated form is deliberate: it is the one substring that
is unambiguously "an org reference" wherever it appears, and it leaves a
future ambiguous case (a bare `Rostov-au` with no slash, if one is ever
added) untouched rather than silently rewritten.

WHAT IT DOES NOT DO
--------------------
It never commits, stages or pushes. Each of the five repos needs its own
commit and its own PR -- they are five separate remotes -- and that
judgement (message, review, when to open each PR) belongs to the person
running this after the real transfer, not to this script.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

OLD = "Rostov-au/"

REPO_NAMES = (
    "fsg-common",
    "fsg-estimating-crm",
    "fsg-tender-review",
    "fsg-estimating-tools",
    "fsg-bluebeam-steel-standards",
)

# GitHub's own organisation-login shape: alphanumeric, single internal
# hyphens, cannot start or end with one. Checked before anything is written
# so a typo'd org name fails loud rather than landing mid-catalogue.
_ORG_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")


class RefusedError(SystemExit):
    """A refusal, not a crash -- always exits non-zero with a printed reason."""

    def __init__(self, message: str):
        super().__init__(f"REFUSED: {message}")


def validate_org_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise RefusedError("the new org name is empty")
    if "/" in name:
        raise RefusedError(f"{name!r} contains a '/' -- pass the org login only")
    if name == "Rostov-au":
        raise RefusedError(
            "the new org name is 'Rostov-au' -- that is a no-op rename, refusing"
        )
    if not _ORG_NAME_RE.match(name):
        raise RefusedError(
            f"{name!r} is not a valid GitHub organisation login "
            "(alphanumeric, single internal hyphens, 1-39 chars)"
        )
    return name


def is_git_worktree(path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def resolve_repos(repos_root: Path, only: list[str] | None) -> dict[str, Path]:
    """name -> path for every repo in scope. Refuses (all at once) if any
    in-scope repo is missing or not a git working tree -- ABSENT IS NOT PASS,
    matching the rest of this estate's gates: a partial catalogue that
    silently drops a whole repo is a wrong answer dressed as a report."""
    scope = REPO_NAMES if only is None else tuple(only)
    unknown = [name for name in scope if name not in REPO_NAMES]
    if unknown:
        raise RefusedError(
            f"--only names repo(s) not in the known five: {', '.join(unknown)}"
        )
    problems: list[str] = []
    paths: dict[str, Path] = {}
    for name in scope:
        path = repos_root / name
        if not path.is_dir():
            problems.append(f"{path} does not exist")
            continue
        if not is_git_worktree(path):
            problems.append(f"{path} exists but is not a git working tree")
            continue
        paths[name] = path
    if problems:
        detail = "\n  ".join(problems)
        raise RefusedError(
            f"{len(problems)} repo(s) in scope could not be used:\n  {detail}"
        )
    return paths


def tracked_files(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.splitlines()


class FileHit:
    __slots__ = ("rel_path", "line_no", "before", "after")

    def __init__(self, rel_path: str, line_no: int, before: str, after: str):
        self.rel_path = rel_path
        self.line_no = line_no
        self.before = before
        self.after = after


def scan_repo(repo: Path, new_org: str) -> tuple[list[FileHit], list[str]]:
    """(hits, skipped_binary_paths) for every tracked file under `repo`."""
    replacement = f"{new_org}/"
    hits: list[FileHit] = []
    skipped: list[str] = []
    for rel in tracked_files(repo):
        path = repo / rel
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if OLD.encode("utf-8") not in raw:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append(rel)
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if OLD in line:
                hits.append(FileHit(rel, line_no, line, line.replace(OLD, replacement)))
    return hits, skipped


def apply_repo(repo: Path, new_org: str) -> list[str]:
    """Rewrite every tracked file containing OLD, byte-for-byte apart from the
    substitution -- read_bytes/write_bytes, never write_text, so an existing
    CRLF file is not silently normalised to LF (or vice versa) as a side
    effect of the rename. Returns the list of changed relative paths."""
    replacement = f"{new_org}/"
    changed: list[str] = []
    for rel in tracked_files(repo):
        path = repo / rel
        if not path.is_file():
            continue
        raw = path.read_bytes()
        needle = OLD.encode("utf-8")
        if needle not in raw:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue  # reported separately by scan_repo; apply must not guess
        new_text = text.replace(OLD, replacement)
        path.write_bytes(new_text.encode("utf-8"))
        changed.append(rel)
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Catalogue, or (with --apply) replace, every literal "
                     "'Rostov-au/' across the five FSG repos' tracked files."
    )
    ap.add_argument("new_org", help="the new GitHub org login -- never guessed, "
                                     "always required")
    ap.add_argument("--repos-root", type=Path, default=None,
                     help="directory containing the five repos as siblings "
                          "(default: this script's own repo's parent dir)")
    ap.add_argument("--only", nargs="+", default=None, metavar="REPO",
                     help="restrict to these repo names instead of all five "
                          "(e.g. for testing against one throwaway clone)")
    ap.add_argument("--apply", action="store_true",
                     help="write the replacement for real. Without this flag "
                          "the run is read-only and only prints what it would "
                          "change.")
    args = ap.parse_args()

    new_org = validate_org_name(args.new_org)
    repos_root = args.repos_root or Path(__file__).resolve().parents[2]
    if not repos_root.is_dir():
        raise RefusedError(f"--repos-root {repos_root} does not exist")

    repos = resolve_repos(repos_root, args.only)

    print(f"{'APPLY' if args.apply else 'DRY RUN'}: Rostov-au/ -> {new_org}/")
    print(f"repos-root: {repos_root}")
    print(f"scope: {', '.join(repos)}")
    print()

    grand_files = 0
    grand_hits = 0
    grand_skipped: list[str] = []

    for name, repo in repos.items():
        hits, skipped = scan_repo(repo, new_org)
        grand_skipped.extend(f"{name}/{rel}" for rel in skipped)
        if not hits:
            print(f"== {name}: 0 occurrences ==")
            print()
            continue

        by_file: dict[str, list[FileHit]] = {}
        for hit in hits:
            by_file.setdefault(hit.rel_path, []).append(hit)

        print(f"== {name}: {len(hits)} occurrence(s) in {len(by_file)} file(s) ==")
        for rel, file_hits in sorted(by_file.items()):
            for hit in file_hits:
                print(f"  {rel}:{hit.line_no}")
                print(f"    - {hit.before}")
                print(f"    + {hit.after}")
        print()

        grand_files += len(by_file)
        grand_hits += len(hits)

        if args.apply:
            changed = apply_repo(repo, new_org)
            assert set(changed) == set(by_file), (
                "apply_repo touched a different file set than scan_repo found "
                "-- refusing to trust the report, this is a bug"
            )
            print(f"  APPLIED: {len(changed)} file(s) rewritten in {name}")
            print()

    if grand_skipped:
        print(f"SKIPPED (not valid utf-8, left untouched): {len(grand_skipped)}")
        for rel in grand_skipped:
            print(f"  {rel}")
        print()

    print(f"TOTAL: {grand_hits} occurrence(s) across {grand_files} file(s) "
          f"in {sum(1 for r in repos)} repo(s) scanned")

    if not args.apply:
        print()
        print("DRY RUN -- nothing was written. Re-run with --apply to write.")
        print("Nothing is committed or pushed by this script, in either mode -- "
              "each repo needs its own commit.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
