"""GB-T3: commit list, N=50 bound, privacy (AC-1.1/1.3/1.7, NFR-3/NFR-4)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard import gitread
from aspark_insights.gitboard.board import MAX_COMMITS_SHOWN, build_board


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


@pytest.fixture
def repo_with_n_commits(tmp_path: Path):
    def _make(n: int, tag: str = "v1.0.0") -> Path:
        repo = tmp_path / f"repo-{n}"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "commit", "--allow-empty", "-q", "-m", "chore: base")
        _git(repo, "tag", tag)
        for i in range(n):
            _git(repo, "commit", "--allow-empty", "-q", "-m", f"feat: commit {i}")
        return repo
    return _make


# --- AC-1.1: exact count, hash/subject/date ----------------------------------


def test_commit_count_matches_rev_list_count(repo_with_n_commits):
    repo = repo_with_n_commits(5)
    board = build_board(str(repo), "2026-08-13")
    real_count = int(_git(repo, "rev-list", "--count", "v1.0.0..HEAD").stdout.strip())
    assert board["commits"]["value"] == real_count == 5


def test_each_shown_commit_carries_hash_subject_date(repo_with_n_commits):
    repo = repo_with_n_commits(3)
    board = build_board(str(repo), "2026-08-13")
    for c in board["commits"]["shown"]:
        assert set(c.keys()) == {"hash", "subject", "date"}
        assert c["subject"].startswith("feat: commit")
        assert len(c["hash"]) > 0


# --- NFR-4: N=50 bound, exact total, explicit disclosure --------------------


def test_more_than_fifty_commits_bounds_shown_but_keeps_exact_total(repo_with_n_commits):
    repo = repo_with_n_commits(65)
    board = build_board(str(repo), "2026-08-13")
    assert board["commits"]["value"] == 65  # exact, never truncated
    assert board["commits"]["shown_count"] == MAX_COMMITS_SHOWN == 50
    assert len(board["commits"]["shown"]) == 50
    assert board["commits"]["truncated"] is True


def test_fewer_than_fifty_commits_is_not_flagged_truncated(repo_with_n_commits):
    repo = repo_with_n_commits(5)
    board = build_board(str(repo), "2026-08-13")
    assert board["commits"]["truncated"] is False
    assert board["commits"]["shown_count"] == 5


# --- AC-1.3 / NFR-3: no identity field ever reaches the output --------------

_IDENTITY_TOKENS = ("author", "committer", "email", "Co-Authored-By", "Signed-off-by", "t@example.com", "Test")


def test_output_json_carries_no_identity_field(repo_with_n_commits):
    repo = repo_with_n_commits(3)
    board = build_board(str(repo), "2026-08-13")
    blob = json.dumps(board)
    for token in _IDENTITY_TOKENS:
        assert token not in blob, f"identity token {token!r} leaked into board output"


def test_git_format_strings_never_request_an_identity_placeholder():
    """A future edit that silently adds %an/%ae/%cn/%ce/%b would be an NFR-3
    breach — checked against the actual `fmt = ...` assignments the code
    hands to git, not the whole file text (which legitimately *documents*
    the forbidden tokens in prose, e.g. this module's own docstring)."""
    import re

    src = Path(gitread.__file__).read_text(encoding="utf-8")
    fmt_lines = [line for line in src.splitlines() if re.match(r"\s*fmt\s*=", line)]
    assert fmt_lines, "expected at least one `fmt = ...` assignment to check"
    for placeholder in ("%an", "%ae", "%cn", "%ce", "%b", "%(authorname)", "%(authoremail)"):
        for line in fmt_lines:
            assert placeholder not in line, f"identity placeholder {placeholder!r} found in: {line}"


# --- AC-1.7: subjects carried verbatim as opaque strings in JSON ------------


def test_hostile_commit_subject_carried_verbatim_in_json_never_parsed_for_identity(tmp_path: Path):
    repo = tmp_path / "hostile"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: <script>alert(1)</script>")
    board = build_board(str(repo), "2026-08-13")
    subjects = [c["subject"] for c in board["commits"]["shown"]]
    assert "feat: <script>alert(1)</script>" in subjects  # verbatim in JSON, not escaped here


# --- F4 (review): an embedded 0x1f byte in a subject must not misalign the
#     hash/subject/date fields the %x1f-delimited --format splits on --------


def test_subject_containing_the_field_separator_byte_does_not_misalign_fields(tmp_path: Path):
    repo = tmp_path / "field-sep-in-subject"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    hostile_subject = "feat: do X\x1fY"
    _git(repo, "commit", "--allow-empty", "-q", "-m", hostile_subject)
    board = build_board(str(repo), "2026-08-13")
    commit = board["commits"]["shown"][0]
    assert commit["subject"] == hostile_subject
    assert commit["date"].count("-") >= 2  # still a real ISO-strict date, not subject overflow
