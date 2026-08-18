"""GB-T6: local branch inventory (AC-3.1/3.2/3.3)."""

from __future__ import annotations

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
