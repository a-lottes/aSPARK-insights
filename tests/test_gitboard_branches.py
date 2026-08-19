"""GB-T6: local branch inventory (AC-3.1/3.2/3.3)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard import gitread
from aspark_insights.gitboard.board import build_board


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


def _corrupt_committer_timestamp(repo: Path, branch: str) -> None:
    """Real git corruption, not a mock — see test_gitboard_days.py's twin
    helper for the same technique against a tag's commit (B1)."""
    raw = _git(repo, "cat-file", "-p", branch).stdout
    bad = re.sub(
        r"^committer (.*) <(.*)> \d+ [+-]\d+$",
        r"committer \1 <\2> NOTATIMESTAMP +0000",
        raw, flags=re.MULTILINE,
    )
    new_hash = subprocess.run(
        ["git", "hash-object", "-w", "-t", "commit", "--stdin"],
        cwd=repo, input=bad, capture_output=True, text=True, check=True,
    ).stdout.strip()
    _git(repo, "update-ref", f"refs/heads/{branch}", new_hash)


@pytest.fixture
def multi_branch_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "multi"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "branch", "feature-x")
    default_branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    _git(repo, "checkout", "-q", "-b", "feature-y")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: y work")
    _git(repo, "checkout", "-q", default_branch)
    return repo


# --- AC-3.1: tip hash, tip date, age in whole days, no identity -------------


def test_branches_carry_tip_hash_date_age_no_identity(multi_branch_repo: Path):
    board = build_board(str(multi_branch_repo), "2026-08-13")
    names = {b["name"] for b in board["branches"]}
    assert {"feature-x", "feature-y"} <= names
    for b in board["branches"]:
        assert set(b.keys()) == {"name", "tip_hash", "tip_date", "age_days", "age_reason"}
        assert isinstance(b["age_days"], int)
        assert "email" not in b and "author" not in b


def test_branch_ages_are_as_of_relative(multi_branch_repo: Path):
    import subprocess as sp

    tip_date = sp.run(
        ["git", "log", "-1", "--format=%cI", "feature-y"],
        cwd=multi_branch_repo, capture_output=True, text=True, check=True,
    ).stdout.strip()
    from aspark_insights.gitboard.board import _whole_days

    board = build_board(str(multi_branch_repo), "2026-08-20")
    branch = next(b for b in board["branches"] if b["name"] == "feature-y")
    assert branch["age_days"] == _whole_days(tip_date, "2026-08-20")


# --- AC-3.2: single-branch checkout reports exactly what's present ---------


def test_single_branch_checkout_reports_only_that_branch(tmp_path: Path):
    repo = tmp_path / "single"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: only branch")
    board = build_board(str(repo), "2026-08-13")
    assert len(board["branches"]) == 1


# --- AC-3.3: unreadable tip date -> age null+reason, never guessed --------


def test_unreadable_branch_tip_date_is_null_age_with_reason(monkeypatch, tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")

    real_list_branches = gitread.list_branches

    def _broken(repo_root):
        branches = real_list_branches(repo_root)
        for b in branches:
            b["tip_date"] = ""
        return branches

    monkeypatch.setattr(gitread, "list_branches", _broken)
    board = build_board(str(repo), "2026-08-13")
    assert board["branches"][0]["age_days"] is None
    assert "could not be read" in board["branches"][0]["age_reason"]


def test_real_corrupted_branch_tip_date_is_null_not_a_guessed_epoch_age(tmp_path: Path):
    """QA B2 (Major): `git for-each-ref`'s `%(committerdate:iso-strict)`
    silently substitutes the Unix epoch (`1970-01-01T00:00:00+00:00`) for a
    commit with an unparseable committer timestamp, rather than emitting
    empty output — unlike `log --format`'s literal-placeholder behavior
    (B1's twin bug). The old `if b["tip_date"]:` truthiness check treated
    that fabricated-but-truthy epoch string as a real date, silently
    displaying a ~56-year-old age with `age_reason: None`. Reproduced with a
    real corrupted git object, not the mocked empty-string short-circuit
    `test_unreadable_branch_tip_date_is_null_age_with_reason` already
    covers."""
    repo = tmp_path / "badbranchdate"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    branch = _git(repo, "symbolic-ref", "--short", "HEAD").stdout.strip()
    _corrupt_committer_timestamp(repo, branch)

    board = build_board(str(repo), "2026-08-13")
    assert len(board["branches"]) == 1
    assert board["branches"][0]["age_days"] is None
    assert board["branches"][0]["age_reason"] is not None
    assert "could not be read" in board["branches"][0]["age_reason"]
