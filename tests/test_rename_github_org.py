"""tr#669 / crm#655 gate line 7 prep: the GitHub-org rename script.

Proves the three things a dry-run-by-default, multi-repo rewriter has to get
right before it is trusted anywhere near the five real checkouts:

  1. The new org name is validated, not guessed -- empty, slash-containing,
     the literal no-op `Rostov-au`, and GitHub-invalid logins all refuse.
  2. A missing or non-git repo directory REFUSES the whole run rather than
     being silently skipped (the "absent must not answer" rule this estate
     applies everywhere else).
  3. `scan_repo` (dry run) never writes; `apply_repo` rewrites ONLY the
     literal `Rostov-au/` substring, byte-for-byte otherwise -- an untracked
     file is left alone, a binary/non-utf8 file is skipped and reported
     rather than corrupted, and a file's own CRLF/LF choice survives
     untouched (the `write_text`-normalises-line-endings trap).

These run against real, disposable git repos built in `tmp_path` -- never
against the five real checkouts, which this test suite must not assume are
even present on the machine running CI.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import rename_github_org as R  # noqa: E402


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
    )


def _init_repo(tmp_path: Path, name: str = "sample-repo") -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit",
         "--allow-empty", "--quiet", "-m", "init")
    return repo


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t",
         "commit", "--quiet", "-m", message)


# --------------------------------------------------------------- org name


def test_validate_org_name_accepts_a_plain_login():
    assert R.validate_org_name("FSG-Steel") == "FSG-Steel"


def test_validate_org_name_refuses_empty():
    with pytest.raises(SystemExit, match="empty"):
        R.validate_org_name("   ")


def test_validate_org_name_refuses_a_slash():
    with pytest.raises(SystemExit, match=r"'/'"):
        R.validate_org_name("some/org")


def test_validate_org_name_refuses_the_literal_no_op():
    """The one name that would make this script a very slow way to do
    nothing -- refused explicitly rather than silently succeeding at
    replacing 'Rostov-au/' with 'Rostov-au/'."""
    with pytest.raises(SystemExit, match="no-op"):
        R.validate_org_name("Rostov-au")


def test_validate_org_name_refuses_a_leading_hyphen():
    with pytest.raises(SystemExit):
        R.validate_org_name("-bad")


# ------------------------------------------------------------ resolve_repos


def test_resolve_repos_refuses_a_missing_directory(tmp_path):
    with pytest.raises(SystemExit, match="does not exist"):
        R.resolve_repos(tmp_path, only=["fsg-common"])


def test_resolve_repos_refuses_a_non_git_directory(tmp_path):
    (tmp_path / "fsg-common").mkdir()
    with pytest.raises(SystemExit, match="not a git working tree"):
        R.resolve_repos(tmp_path, only=["fsg-common"])


def test_resolve_repos_refuses_an_unknown_repo_name(tmp_path):
    with pytest.raises(SystemExit, match="not in the known five"):
        R.resolve_repos(tmp_path, only=["not-one-of-the-five"])


def test_resolve_repos_accepts_a_real_git_worktree(tmp_path):
    _init_repo(tmp_path, "fsg-common")
    resolved = R.resolve_repos(tmp_path, only=["fsg-common"])
    assert resolved == {"fsg-common": tmp_path / "fsg-common"}


# --------------------------------------------------------- scan_repo / apply


def test_scan_repo_finds_tracked_occurrences_and_writes_nothing(tmp_path):
    repo = _init_repo(tmp_path)
    target = repo / "README.md"
    target.write_text("see Rostov-au/fsg-common for details\n", encoding="utf-8")
    _commit_all(repo, "add readme")
    before = target.read_bytes()

    hits, skipped = R.scan_repo(repo, "FSG-Steel")

    assert skipped == []
    assert len(hits) == 1
    assert hits[0].rel_path == "README.md"
    assert hits[0].after == "see FSG-Steel/fsg-common for details"
    assert target.read_bytes() == before, "a dry-run scan must not write"


def test_scan_repo_ignores_an_untracked_file(tmp_path):
    """Tracked-only, matching this estate's own leak-guard convention: an
    untracked scratch file must never be touched by a multi-file rewrite."""
    repo = _init_repo(tmp_path)
    (repo / "scratch.txt").write_text("Rostov-au/not-tracked\n", encoding="utf-8")
    # deliberately not added or committed

    hits, skipped = R.scan_repo(repo, "FSG-Steel")

    assert hits == []
    assert skipped == []


def test_apply_repo_rewrites_only_the_tracked_hit(tmp_path):
    repo = _init_repo(tmp_path)
    tracked = repo / "docs.md"
    tracked.write_text("Rostov-au/fsg-common and Rostov-au/fsg-tender-review\n",
                        encoding="utf-8")
    _commit_all(repo, "add docs")
    untracked = repo / "scratch.txt"
    untracked.write_text("Rostov-au/leave-me-alone\n", encoding="utf-8")

    changed = R.apply_repo(repo, "FSG-Steel")

    assert changed == ["docs.md"]
    assert tracked.read_text(encoding="utf-8") == (
        "FSG-Steel/fsg-common and FSG-Steel/fsg-tender-review\n"
    )
    assert untracked.read_text(encoding="utf-8") == "Rostov-au/leave-me-alone\n"


def test_apply_repo_preserves_crlf_and_touches_only_the_matching_bytes(tmp_path):
    """The write_text-normalises-line-endings trap: this script must read and
    write bytes, never text, so a CRLF file comes back CRLF, unchanged apart
    from the one substituted substring."""
    repo = _init_repo(tmp_path)
    target = repo / "windows.md"
    content = b"line one\r\nsee Rostov-au/fsg-common here\r\nline three\r\n"
    target.write_bytes(content)
    _commit_all(repo, "add crlf file")

    R.apply_repo(repo, "FSG-Steel")

    after = target.read_bytes()
    assert after == content.replace(b"Rostov-au/", b"FSG-Steel/")
    assert after.count(b"\r\n") == content.count(b"\r\n"), "CRLF count must be unchanged"


def test_apply_repo_skips_a_non_utf8_file_and_leaves_it_untouched(tmp_path):
    repo = _init_repo(tmp_path)
    target = repo / "binary.dat"
    # Valid latin-1 bytes that are not valid utf-8, with the needle embedded.
    raw = "café Rostov-au/fsg-common".encode("latin-1")
    assert b"\xe9" in raw  # sanity: this really isn't valid utf-8
    target.write_bytes(raw)
    _commit_all(repo, "add non-utf8 file")

    hits, skipped = R.scan_repo(repo, "FSG-Steel")
    assert hits == []
    assert skipped == ["binary.dat"]

    changed = R.apply_repo(repo, "FSG-Steel")
    assert changed == []
    assert target.read_bytes() == raw, "a file that failed to decode must be left untouched"


def test_apply_repo_is_idempotent_once_nothing_matches(tmp_path):
    """Running twice (e.g. an operator re-running after checking the dry-run
    output) must not error and must not touch a file with no more hits."""
    repo = _init_repo(tmp_path)
    target = repo / "README.md"
    target.write_text("Rostov-au/fsg-common\n", encoding="utf-8")
    _commit_all(repo, "add readme")

    first = R.apply_repo(repo, "FSG-Steel")
    assert first == ["README.md"]
    second = R.apply_repo(repo, "FSG-Steel")
    assert second == [], "no 'Rostov-au/' left, so the second pass changes nothing"
