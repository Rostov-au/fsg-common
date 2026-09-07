"""The leak guard: refuse to commit a client document, customer PII, or a
credential. One engine, four repos -- `fsg-tender-review`, `fsg-estimating-
crm`, `fsg-bluebeam-steel-standards` and `fsg-estimating-tools` each carried
an independently-evolved copy of this script (26 Aug - 7 Sep 2026), and each
found and fixed a DIFFERENT real bug the others still carry. Consolidated
7 Sep 2026 (fsg-estimating-tools#116, David: "Yes -- one guard, all repos" --
"the strictest leak guard becomes the shared one... reading both and keeping
the better reasoning, not unioning the patterns").

## What came from where, and why

**File discovery and the zero-files refusal** (`range_files`, `range_ever_
added`, `range_deletions`, the `main()` population-selection and "examined
nothing is not the same as found nothing" refusal) -- `fsg-tender-review`'s
copy, the most complete: its own `range_files` already unions a commit-walk
so a file added then deleted mid-range is still scanned (git history keeps
the blob), and its `--files` handling distinguishes "given, but empty" from
"not given at all" (GNU `xargs` with no `-r` runs a command once on empty
input, which `nargs="*"`'s falsy `[]` could not tell apart from "no --files
flag" -- tr, 4 Sep 2026).

**The historical-content read is NEW here, not ported from anywhere.**
Every existing copy read a `--range`'s file list from git objects but a
file's CONTENT from the working tree with a plain `open()` -- correct only
when the tree already matches the range's own history, which is false for a
file the range's commit-walk finds (added then deleted before the tip, so
never on disk at any point the tree could be checked out to) and false from
inside a pre-commit hook checking a commit that has not been created yet
(`fsg-bluebeam-steel-standards#64`, 7 Sep 2026: this repo's own vendored-file
deletion was the first thing in four repos' history to trigger it -- the
hook's `--range <empty-tree>..HEAD` self-test failed on a file the commit
being made would delete, because HEAD had not moved yet and the working
tree already had). That PR's fix (fall back to `git show <range-target>:
<path>`) is not general enough for tender-review's own shape of the same
problem: a file added then deleted mid-range is absent from EVERY ref, not
just the working tree, so `_range_path_sources()` below finds the actual
commit within the range that most recently touched each such path and reads
the blob from THERE.

**Secret patterns** -- `fsg-estimating-crm`'s unified `password[=:]"value"`
form (measured against real false positives twice: the identifier-prefix
lookbehind it used to carry was tested and reversed by `fsg-tender-review`'s
own PR #92 on 1 Sep 2026 -- 25 real `workbook_password=`/`register_password=`
occurrences here, zero new false positives from removing it, because the
VALUE shape, a quoted 3+ character literal, was doing the discriminating
work all along; and the `/`-exclusion crm's own 29 Aug fix added was itself
measured wrong on 2 Sep -- `/` is in the base64 alphabet, so excluding it
missed five of six realistic generated secrets. crm's current pattern lets
`/` back in with three shape tests at the ACTUAL point of past confusion
instead: not path-shaped, not template-expression-shaped, no leading
whitespace). Plus `fsg-estimating-tools`' two ESCAPED-quote variants (`=`
and `:` forms where the quote characters are themselves backslash-escaped in
the source text, e.g. inside a JSON string or a Python string literal) --
tender-review's own PR #92 named this "gap 3, needs a different rule" and
left it open in both repos it touched; tools closed it independently on
3 Sep 2026 and crm's unified pattern does not cover it (it requires a real,
unescaped quote character). Kept as tools wrote them rather than merged into
crm's pattern, per the "read both, keep the better reasoning, do not union"
instruction -- each is proven in its own repo's tests and a hand-built
hybrid would be proven in neither.

**PII (email/phone) is `fsg-estimating-crm`'s alone** -- the only one of the
four repos with a leak guard that ever had it, added 26 Aug 2026 (this repo
holds real customer data) and put through a dedicated boundary-defect audit
27 Aug 2026 (every pattern opened with `\\b`, which is blind to a value
sitting behind a LITERAL escape sequence in source text -- "Name\\n0400 111
222" has the word-character `n` of `\\n` immediately before the digits, so
`\\b` finds no boundary -- fixed per-pattern, not with one blunt rule) and a
phone-format census against 8,445 real values on 27 Aug 2026 (the WA
bracketed-area-code landline format the patterns could not match until
then). `EMAIL_RE`, `AU_MOBILE_RE`, `AU_LANDLINE_RE` and their allowlist
machinery are ported near-verbatim, because this is the one part of the
sibling copies that already went through exactly the falsification rigor
this whole file exists to preserve.

**Deliberately NOT ported**: `RECORD_ID_RE`, `LITERAL_ID_NAME_RE`,
`NON_CONTACT_TYPE_RE`, the proximity co-occurrence check, and the JSON
`name`+id-literal / n8n `pinData` detectors. These protect against a
re-identification risk specific to EspoCRM record ids sitting next to a
real person's name in THIS repo's own one-off migration scripts
(`fix_blob_accounts.ps1`-shaped incidents) -- the other three repos have no
EspoCRM records and no such scripts, so porting this would add PROXIMITY-
BASED matching that fires on nothing real in three of four repos while
adding a live false-positive surface (a bare 17-hex-character string is not
uniquely an EspoCRM id -- a git SHA prefix is the same shape). David's
decision covers "phone/email detection reaches every repo"; this is a
narrower, repo-specific extension of it that stays in
`fsg-estimating-crm`'s own script.

## How a consumer uses this

A repo does not call `main()` directly with its own flags -- it builds a
`GuardConfig` naming what is actually different about it (the refusal
banner's wording, its own `ALLOWED` path exemptions, any extra secret
pattern, whether PII detection applies) and calls `run(argv, config)`.
Everything else -- the regex engine, the range machinery, the zero-files
refusal, the historical-blob fallback -- is this module's, not the
caller's, so a fix here reaches every repo the next time each bumps its
`fsg-common.pin`, the same mechanism `sections.py` already uses.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

# --- extensions and filenames -----------------------------------------------

#: The baseline every consumer repo already blocked identically. A repo may
#: add its own extras via `GuardConfig.extra_blocked_extensions`.
DEFAULT_BLOCKED_EXTENSIONS: dict[str, str] = {
    ".pdf": "client drawings and specifications",
    ".dwg": "CAD", ".dxf": "CAD", ".ifc": "models", ".rvt": "models",
    ".xls": "job workbooks (client and commercial data)",
    ".xlsx": "job workbooks (client and commercial data)",
    ".xlsm": "job workbooks (client and commercial data)",
    ".xlsb": "job workbooks (client and commercial data)",
    ".csv": "extracts -- usually client, project or commercial data",
    ".jsonl": "crawl indexes (client, project and job names)",
    ".db": "the history warehouse (client and commercial data)",
    ".sqlite": "the history warehouse",
    ".sqlite3": "the history warehouse",
    ".png": "rendered pages / screenshots that may show client data",
    ".jpg": "scans/photos", ".jpeg": "scans/photos",
    ".tif": "scans", ".tiff": "scans",
    ".zip": "packs",
    ".key": "credentials", ".pem": "credentials", ".pfx": "credentials",
}

#: Filenames that are always wrong regardless of extension, in every repo.
BLOCKED_NAMES: tuple[re.Pattern, ...] = (
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/)\.env\.[^/]*$(?<!\.example)"),
)

# --- secret patterns ---------------------------------------------------------

#: `FSG_WORKBOOK_PASSWORD=`/`FSG_REGISTER_PASSWORD=` -- identical in every
#: repo since this was first written, and narrow enough (a named variable, not
#: a generic word) that the value need not even be quoted.
FSG_CREDENTIAL_RE = re.compile(
    r"FSG_(?:WORKBOOK|REGISTER)_PASSWORD[ \t]*=[ \t]*['\"]?\S+", re.I)

#: The generic `password[=:]"value"` form, crm's current pattern (see module
#: docstring). Matches both `=` and `:` (JSON/YAML), an UNESCAPED quoted
#: value of 3+ non-space characters, and refuses a value that looks like a
#: path (`/p`, `./p`, `../p`, `~/p`, `C:\p`) or a template expression
#: (`{{ ... }}`, `${VAR}`) -- the two shapes that cost this pattern real
#: coverage before they were measured and fixed.
GENERIC_PASSWORD_RE = re.compile(
    r"password"
    r"['\"]?"                # the JSON key's own closing quote
    r"\s*[=:]\s*"            # `=` (python/env) or `:` (json/yaml)
    r"['\"]"
    r"(?!\s)"                # not the space after a CLOSING quote
    r"(?![~.]{0,2}/)"        # not /p, ./p, ../p, ~/p
    r"(?![A-Za-z]:[\\/])"    # not C:\p or C:/p
    r"(?![=$]\{?\{)"         # not ={{expr}} or ${VAR}
    r"(?!\{\{)"              # not {{ expr }}
    r"[^'\"\s]{3,}"          # a secret has no spaces in it
    r"['\"]", re.I)

#: The escaped-quote `=` form -- `password = \"secret\"`, where the quote
#: characters are themselves backslash-escaped in the source text (inside a
#: JSON string or a Python string literal). `fsg-estimating-tools`, 3 Sep
#: 2026. `GENERIC_PASSWORD_RE` cannot see this: it requires a real, unescaped
#: quote character immediately after the operator.
ESCAPED_PASSWORD_EQ_RE = re.compile(
    r"password[ \t]*=[ \t]*\\+['\"][^'\"\\]{3,}\\+['\"]", re.I)

#: The escaped-quote `:` form -- a credential inside a doubly-escaped JSON
#: document or a captured request body. `fsg-estimating-tools`, 3 Sep 2026,
#: with one fix made HERE, 7 Sep 2026, found by this consolidation's own
#: falsification rather than carried over unread: the source pattern
#: delimited the VALUE with `\\*` (zero or more backslashes), so it also
#: matched the plain, UNESCAPED case with none of `GENERIC_PASSWORD_RE`'s
#: template/path exclusions -- `"password": "={{$json.pw}}"`, a real n8n
#: expression shape, matched as a hardcoded password. Changed to `\\+`
#: (one or more) so this pattern only ever fires on a value that is
#: actually escaped, which is the one case `GENERIC_PASSWORD_RE` cannot
#: see; the KEY side stays `\\*`, since whether `"password"` itself is
#: escaped is independent of whether its value is.
ESCAPED_PASSWORD_COLON_RE = re.compile(
    r"\\*['\"]password\\*['\"][ \t]*:[ \t]*\\+['\"][^'\"\\]{3,}\\+['\"]", re.I)

#: The four secret patterns every repo gets. `GuardConfig.extra_secret_
#: patterns` is for something genuinely repo-specific, not a substitute for
#: widening one of these.
DEFAULT_SECRET_PATTERNS: tuple[tuple[re.Pattern, str], ...] = (
    (FSG_CREDENTIAL_RE, "a workbook/register password assigned in tracked source"),
    (GENERIC_PASSWORD_RE, "a hardcoded password"),
    (ESCAPED_PASSWORD_EQ_RE, "a hardcoded password"),
    (ESCAPED_PASSWORD_COLON_RE, "a hardcoded password"),
)

DEFAULT_SCAN_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".md", ".ps1", ".sh", ".toml", ".yaml", ".yml",
    ".json", ".txt", ".cfg", ".ini",
})

#: `.env.example` documents variable names with empty values on purpose, and
#: this module's own source necessarily contains every pattern it looks for.
DEFAULT_CONTENT_SCAN_SKIP: tuple[re.Pattern, ...] = (
    re.compile(r"(^|/)\.env\.example$"),
    re.compile(r"(^|/)check_no_client_data\.py$"),
    re.compile(r"(^|/)leak_guard\.py$"),
)

# --- PII (email/phone), optional per repo -----------------------------------
#
# See the module docstring for the boundary-defect and phone-census history
# behind these three. Ported from fsg-estimating-crm, the only source.

EMAIL_RE = re.compile(
    r"(?:(?<=\\[nrt])|(?<![A-Za-z0-9._%+\-\\]))"
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

AU_MOBILE_RE = re.compile(r"(?<![0-9])(?:\+61[ \-]?|0[ \-]?)4(?:[ \-]?\d){8}\b")

AU_LANDLINE_RE = re.compile(
    r"(?<![0-9])(?:"
    r"(?:\+61[ \-]?\(?0?\)?[ \-]?[2378]|\(0[2378]\)|0[2378])(?:[ \-]?\d){8}"
    r"|61[2378][ \-]\d{4}[ \-]\d{4}"
    r"|(?:\+61[ \-]?)?[69]\d{3} \d{4}"
    r")\b")

#: RFC 2606 reserves `.invalid` for exactly this: a synthetic address
#: guaranteed to never resolve to a real mailbox.
DEFAULT_ALLOWED_EMAIL_TLDS: frozenset[str] = frozenset({"invalid"})

#: A value that announces itself as synthetic -- a fixture testing the
#: parser itself, not a real credential/contact. Deliberately a VALUE-shape
#: allowance, never a per-file one: it travels with the string, so it cannot
#: exempt a file wholesale the way a path-based rule could.
PLACEHOLDER_VALUE_RE = re.compile(
    r"not-?a-?(?:real-?)?(?:credential|password|secret|key)"
    r"|fake|dummy|synthetic|placeholder|example|changeme|xxxxx",
    re.I,
)


@dataclass(frozen=True)
class GuardConfig:
    """What is actually different between repos. Everything not listed here
    is this module's, shared, and fixed once for all four consumers.

    `repo_holds` / `client_data_lives` fill the BLOCKED banner -- the two
    lines every repo's own script wrote by hand, in its own words, naming
    what it holds and where the real thing actually lives instead.
    """

    repo_holds: str
    client_data_lives: str
    extra_blocked_extensions: dict[str, str] = field(default_factory=dict)
    allowed_paths: tuple[re.Pattern, ...] = ()
    extra_secret_patterns: tuple[tuple[re.Pattern, str], ...] = ()
    extra_content_scan_skip: tuple[re.Pattern, ...] = ()
    extra_scan_extensions: frozenset[str] = frozenset()
    enable_pii: bool = False
    allowed_email_addresses: frozenset[str] = frozenset()
    allowed_email_domains: frozenset[str] = frozenset()
    allowed_email_tlds: frozenset[str] = DEFAULT_ALLOWED_EMAIL_TLDS
    role_account_local_parts: frozenset[str] = frozenset()

    @property
    def blocked_extensions(self) -> dict[str, str]:
        return {**DEFAULT_BLOCKED_EXTENSIONS, **self.extra_blocked_extensions}

    @property
    def secret_patterns(self) -> tuple[tuple[re.Pattern, str], ...]:
        return DEFAULT_SECRET_PATTERNS + self.extra_secret_patterns

    @property
    def content_scan_skip(self) -> tuple[re.Pattern, ...]:
        return DEFAULT_CONTENT_SCAN_SKIP + self.extra_content_scan_skip

    @property
    def scan_extensions(self) -> frozenset[str]:
        return DEFAULT_SCAN_EXTENSIONS | self.extra_scan_extensions


def _looks_like_text(path: str) -> bool:
    """Content sniff for files whose extension is not in `scan_extensions`.

    Extensionless files (`.githooks/pre-commit`, `.gitattributes`) and an
    unforeseen extension cannot be decided by an extension rule at all --
    found 27 Aug 2026 leaving 9-24 tracked files never opened by an
    extension-only version of this check, across two repos independently.
    So the decision is made on content instead: a NUL byte in the first
    8 KB, or bytes that are not valid UTF-8, means binary; anything else is
    treated as text and scanned.

    Deliberately crude, and biased towards scanning. A false "text" verdict
    costs a few wasted regex passes over a binary file; a false "binary"
    verdict is a silent hole, which is the failure being corrected here.
    """
    try:
        with open(path, "rb") as fh:
            chunk = fh.read(8192)
    except OSError:
        # NOT False -- that would be the silent hole this docstring names,
        # taken on a read error. True routes the file to the caller's own
        # read, which records an unreadable file as a problem, not a skip.
        return True
    if b"\x00" in chunk:
        return False
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _run(*args: str) -> list[str]:
    out = subprocess.run(args, capture_output=True, text=True, check=False)
    return [line for line in out.stdout.splitlines() if line.strip()]


def staged_files() -> list[str]:
    return _run("git", "diff", "--cached", "--name-only", "--diff-filter=ACMR")


def range_files(rev_range: str) -> list[str]:
    """Every path the range ever ADDED, not the paths it net-added.

    `git diff A..B` is the NET difference between two commits. A PDF
    committed in the middle of a branch and deleted before the tip does not
    appear in it -- and that is precisely the case this guard exists for,
    because git history keeps the blob whatever the tip looks like.

    `git log --diff-filter=AM` walks the commits instead of comparing the
    ends, so a file that came and went is listed. The union is scanned:
    the two-dot diff still contributes renames, which `log --name-only`
    reports under the new name only.
    """
    net = _run("git", "diff", "--name-only", "--diff-filter=ACMR", rev_range)
    ever = _run("git", "log", "--pretty=format:", "--name-only",
                "--diff-filter=AM", rev_range)
    return sorted({p for p in net + ever if p})


def range_deletions(rev_range: str) -> list[str]:
    """The paths the range net-DELETES. A range that only removes files has
    nothing to scan and is not the empty range the refusal in `run()` exists
    for: a PR that deletes one file and nothing else must not be refused for
    selecting "no files" when it could not have leaked anything."""
    return sorted(p for p in _run("git", "diff", "--name-only",
                                  "--diff-filter=D", rev_range) if p)


def _range_path_sources(rev_range: str) -> dict[str, str]:
    """For every path `range_files` can name via its commit-walk half, the
    MOST RECENT commit within the range that added or modified it -- not
    the range's own endpoint.

    This is what makes reading a range's file CONTENT correct, not just its
    file LIST. A path can be in `range_files` because some earlier commit in
    the range added or modified it and a later commit in the SAME range
    deleted it again before the tip -- that file is absent from the working
    tree, absent from the range's target ref, and absent from every
    currently-checked-out state; the only place its content still exists is
    the specific commit that last touched it. `git log` walks newest-first
    by default, so the first commit seen for a path in this walk is already
    the most recent one.
    """
    out = _run("git", "log", "--pretty=format:@@%H", "--name-only",
              "--diff-filter=AM", rev_range)
    sources: dict[str, str] = {}
    current: str | None = None
    for line in out:
        if line.startswith("@@"):
            current = line[2:]
            continue
        if current and line not in sources:
            sources[line] = current
    return sources


def _read_body(path: str, path_sources: dict[str, str] | None) -> str | None:
    """The content to scan for *path*: the working tree, or, for a `--range`
    check, the git blob at the specific commit `_range_path_sources` names
    for it, if the working-tree read fails.

    Reading the working tree assumes it already matches whatever the range's
    file list was computed from -- true in CI (the checked-out commit IS the
    range's own target) but false in at least two real, now-measured cases:
    a file added then deleted mid-range (never on disk at any reachable
    state), and a pre-commit hook checking `--range <empty-tree>..HEAD`
    where the commit that will make HEAD move has not been created yet, so
    a file the in-progress commit deletes is still in HEAD's tree (unmoved)
    but already gone from the working tree (fsg-bluebeam-steel-
    standards#64, 7 Sep 2026). `path_sources` is `None` for `--files`/staged
    checks, which have no range and no fallback -- a missing file there is
    exactly what it looks like.
    """
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        if not path_sources:
            return None
        commit = path_sources.get(path)
        if commit is None:
            return None
        out = subprocess.run(["git", "show", f"{commit}:{path}"],
                             capture_output=True, text=True, check=False)
        return out.stdout if out.returncode == 0 else None


def _allowed(path: str, config: GuardConfig) -> bool:
    return any(rx.match(path) for rx in config.allowed_paths)


def _find_email_hits(body: str, config: GuardConfig) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for m in EMAIL_RE.finditer(body):
        addr = m.group(0)
        local, _, domain = addr.partition("@")
        if addr.lower() in {a.lower() for a in config.allowed_email_addresses}:
            continue
        domain_l = domain.lower()
        if domain_l in {d.lower() for d in config.allowed_email_domains}:
            continue
        if domain_l.rsplit(".", 1)[-1] in config.allowed_email_tlds:
            continue
        if local.lower() in {p.lower() for p in config.role_account_local_parts}:
            continue
        line = body[:m.start()].count("\n") + 1
        hits.append((line, addr))
    return hits


def _find_phone_hits(body: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for rx in (AU_MOBILE_RE, AU_LANDLINE_RE):
        for m in rx.finditer(body):
            line = body[:m.start()].count("\n") + 1
            hits.append((line, m.group(0)))
    return hits


def check(paths: list[str], config: GuardConfig,
          path_sources: dict[str, str] | None = None,
          read_content: bool = True) -> list[str]:
    problems: list[str] = []
    for path in paths:
        norm = path.replace("\\", "/")

        for rx in BLOCKED_NAMES:
            if rx.search(norm):
                problems.append(f"{norm}: credentials file must never be committed")
                break

        ext = os.path.splitext(norm)[1].lower()
        blocked_extensions = config.blocked_extensions
        if ext in blocked_extensions and not _allowed(norm, config):
            problems.append(f"{norm}: {blocked_extensions[ext]} ({ext})")
            continue

        if not read_content:
            continue
        scan_extensions = config.scan_extensions
        if ext not in scan_extensions and not _looks_like_text(path):
            continue
        if any(rx.search(norm) for rx in config.content_scan_skip):
            continue

        body = _read_body(path, path_sources)
        if body is None:
            problems.append(
                f"{norm}: could not be read, so it was NOT scanned "
                f"(FileNotFoundError) -- this is a gap in the check, "
                f"not a pass")
            continue

        for rx, why in config.secret_patterns:
            for hit in rx.finditer(body):
                # `finditer`, not `search`: with `search` a single allowed
                # placeholder earlier in the file would end the scan of
                # that file for this pattern and hide a real credential
                # below it.
                if PLACEHOLDER_VALUE_RE.search(hit.group(0)):
                    continue
                line = body[:hit.start()].count("\n") + 1
                problems.append(f"{norm}:{line}: {why}")
                break
            else:
                continue
            break

        if config.enable_pii:
            for line, addr in _find_email_hits(body, config):
                problems.append(f"{norm}:{line}: customer email address ({addr})")
            for line, num in _find_phone_hits(body):
                problems.append(f"{norm}:{line}: Australian phone number ({num})")

    return problems


def run(argv: list[str] | None, config: GuardConfig) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", dest="rev_range",
                    help="check a commit range instead of the staged files")
    ap.add_argument("--files", nargs="*", help="check these paths explicitly")
    args = ap.parse_args(argv)

    path_sources: dict[str, str] | None = None
    if args.files:
        paths = args.files
        asked_for = f"--files ({len(args.files)} path(s) given)"
    elif args.files is not None:
        # `--files` GIVEN WITH NO PATHS -- the live CI shape, not a
        # hypothetical: `git ls-files -z | xargs -0 ... --files` runs the
        # command ONCE WITH NO ARGUMENTS on empty input unless xargs was
        # passed `-r`. `nargs="*"` makes that case `[]`, falsy, which used
        # to fall through to `staged_files()` (empty in CI) and report
        # clean. Distinguishing it from `None` is the whole fix.
        paths = []
        asked_for = "--files (given, but with no paths)"
    elif args.rev_range:
        paths = range_files(args.rev_range)
        asked_for = f"--range {args.rev_range}"
        path_sources = _range_path_sources(args.rev_range)
    else:
        paths = staged_files()
        asked_for = None            # nothing was requested; the index decides

    # ZERO FILES IS NOT A CLEAN RESULT WHEN A POPULATION WAS ASKED FOR.
    # CI runs `--range <empty-tree>..HEAD`, meant to list every file in
    # HEAD; if that ever came back empty (a shallow clone, a mistyped hash,
    # a rewritten history) the guard would scan nothing and report clean, in
    # green, in the one check whose whole job is to refuse. "Checked
    # everything, found nothing" and "checked nothing" must not look alike.
    #
    # No staged files stays a PASS: an empty index is the normal state of a
    # hook invocation with nothing to commit, nobody asked for a population,
    # and refusing there would make the hook unusable.
    if not paths:
        if asked_for is None:
            print("ok -- no staged files, so there was nothing to check "
                  "(this is not the same as 0 files being clean)")
            return 0
        deleted = range_deletions(args.rev_range) if args.rev_range else []
        if deleted:
            print(f"ok -- {asked_for} only deletes {len(deleted)} file(s) "
                  f"({', '.join(deleted)}); nothing was added or modified, "
                  "so there was nothing to scan (this is not the same as "
                  "0 files being clean)")
            return 0
        print(f"REFUSED. {asked_for} selected NO files, so this guard "
              "checked nothing.", file=sys.stderr)
        print("  A run that examined nothing is not a run that found "
              "nothing. Exiting non-zero", file=sys.stderr)
        print("  rather than reporting clean -- most likely a shallow "
              "clone (CI needs fetch-depth: 0),", file=sys.stderr)
        print("  a bad ref, or a range whose two ends are the same commit.",
              file=sys.stderr)
        return 2

    problems = check(paths, config, path_sources=path_sources)
    if not problems:
        print(f"ok -- {len(paths)} file(s) checked, nothing blocked")
        return 0

    print(f"BLOCKED. {config.repo_holds}", file=sys.stderr)
    print(f"{config.client_data_lives}\n", file=sys.stderr)
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    print("\nGit history keeps a file even after a later deletion, so this "
          "has to be fixed before the commit, not after.", file=sys.stderr)
    return 1
