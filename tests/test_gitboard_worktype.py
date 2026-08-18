"""GB-T5: work-type breakdown (AC-1.12, NFR-3/NFR-5).

`classify`/`breakdown` are pure — tested here in isolation from git and CLI
orchestration. The absent-vs-null distinction (AC-1.12(c)/(d) vs (a)) is
tested at the `build_board` level in test_gitboard_cli.py and below.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.board import build_board
from aspark_insights.gitboard.worktype import RECOGNIZED_TYPES, breakdown, classify


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


# --- classify(): the fixed 10-token set --------------------------------------


@pytest.mark.parametrize("token", RECOGNIZED_TYPES)
def test_classify_recognizes_every_token_in_the_fixed_set(token: str):
    assert classify(f"{token}: something") == token


def test_classify_is_case_insensitive_and_normalizes():
    assert classify("FEAT: something") == "feat"
    assert classify("Fix: something") == "fix"


def test_classify_tolerates_scope_and_breaking_marker():
    assert classify("feat(cli): add flag") == "feat"
    assert classify("feat!: breaking change") == "feat"
    assert classify("feat(cli)!: both") == "feat"


def test_classify_returns_none_for_unrecognized_subject():
    assert classify("bumped the version") is None
    assert classify("Merge branch 'main'") is None
    assert classify("wip") is None


def test_classify_never_infers_from_anything_but_the_leading_token():
    """§6: no keyword heuristics on subject text — "fixes a bug" must not be
    classified as `fix` just because the word appears."""
    assert classify("this commit fixes a bug in feat X") is None


# --- breakdown(): five distinct states ---------------------------------------


def test_breakdown_state_1_below_20_percent_is_null_with_reason():
    subjects = ["feat: a"] + [f"random subject {i}" for i in range(9)]  # 1/10 = 10%
    result = breakdown(subjects)
    assert result["value"] is None
    assert "1 of 10" in result["reason"]


def test_breakdown_state_2_at_or_above_20_percent_shows_unclassified_share():
    subjects = ["feat: a", "feat: b", "random c", "random d", "random e"]  # 2/5 = 40%
    result = breakdown(subjects)
    assert result["value"] is not None
    assert result["value"]["feat"] == 40
    assert result["value"]["unclassified"] == 60


def test_breakdown_state_5_all_classified_has_no_unclassified_key():
    subjects = ["feat: a", "fix: b"]
    result = breakdown(subjects)
    assert "unclassified" not in result["value"]
    assert result["value"] == {"feat": 50, "fix": 50}


def test_breakdown_exactly_at_20_percent_threshold_is_inclusive():
    subjects = ["feat: a"] + [f"random {i}" for i in range(4)]  # 1/5 = 20% exactly
    result = breakdown(subjects)
    assert result["value"] is not None  # >= 20%, not < 20%


def test_breakdown_zero_count_types_are_omitted_from_the_distribution():
    subjects = ["feat: a", "feat: b"]
    result = breakdown(subjects)
    assert set(result["value"].keys()) == {"feat"}


def test_breakdown_never_redistributes_unclassified_across_recognized_types():
    subjects = ["feat: a"] * 5 + ["random"] * 5  # 50/50
    result = breakdown(subjects)
    assert result["value"]["feat"] == 50
    assert result["value"]["unclassified"] == 50
    assert sum(result["value"].values()) == 100


# --- state 3 & 4: absent (not null) on tagless / zero-commits-since-tag ----


def test_breakdown_absent_state_3_no_tag(tmp_path: Path):
    repo = tmp_path / "notag"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: only")
    board = build_board(str(repo), "2026-08-13")
    assert "work_types" not in board


def test_breakdown_absent_state_4_zero_commits_since_tag(tmp_path: Path):
    repo = tmp_path / "clean"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")  # HEAD is the tag itself, 0 commits since
    board = build_board(str(repo), "2026-08-13")
    assert board["commits"]["value"] == 0
    assert "work_types" not in board  # 0/0 undefined, never a fabricated 0%


def test_breakdown_real_state_1_via_build_board_with_recognizable_repo(tmp_path: Path):
    """An integration check that state 1 (< 20%) is reachable end to end,
    not just at the pure-function level."""
    repo = tmp_path / "unconventional"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "chore: base")
    _git(repo, "tag", "v1.0.0")
    for i in range(6):
        _git(repo, "commit", "--allow-empty", "-q", "-m", f"unconventional message {i}")
    board = build_board(str(repo), "2026-08-13")
    assert board["work_types"]["value"] is None
    assert board["work_types"]["reason"]
