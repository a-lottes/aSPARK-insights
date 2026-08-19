"""RB-T5: ordered prev/next tag pointers (AC-3.1, AC-3.2)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.releasemap import build_release_map


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


@pytest.fixture
def three_tag_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: one")
    _git(repo, "tag", "v0.1.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: two")
    _git(repo, "tag", "v0.2.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: three")
    _git(repo, "tag", "v0.3.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: open")
    return repo


def test_chain_endpoints_are_null(three_tag_repo: Path):
    result = build_release_map(str(three_tag_repo), "2026-08-19")
    real = [r for r in result["releases"] if r["tag"] is not None]
    assert real[0]["previous_tag"] is None
    assert real[-1]["tag"] == "v0.3.0"
    assert real[-1]["next_tag"] is None


def test_middle_release_points_at_real_neighbors(three_tag_repo: Path):
    result = build_release_map(str(three_tag_repo), "2026-08-19")
    v2 = next(r for r in result["releases"] if r["tag"] == "v0.2.0")
    assert v2["previous_tag"] == "v0.1.0"
    assert v2["next_tag"] == "v0.3.0"


def test_last_real_release_next_tag_is_null_never_the_pseudo_release(three_tag_repo: Path):
    """A real release's next_tag never names the pseudo-release — its
    existence is discoverable only via tag:null, never by chaining."""
    result = build_release_map(str(three_tag_repo), "2026-08-19")
    v3 = next(r for r in result["releases"] if r["tag"] == "v0.3.0")
    assert v3["next_tag"] is None


def test_pseudo_release_previous_tag_is_latest_real_tag_next_tag_is_null(three_tag_repo: Path):
    result = build_release_map(str(three_tag_repo), "2026-08-19")
    pseudo = result["releases"][-1]
    assert pseudo["tag"] is None
    assert pseudo["previous_tag"] == "v0.3.0"
    assert pseudo["next_tag"] is None


def test_single_tag_repo_has_null_previous_and_next(tmp_path: Path):
    repo = tmp_path / "single"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: only")
    _git(repo, "tag", "v1.0.0")
    result = build_release_map(str(repo), "2026-08-19")
    real = [r for r in result["releases"] if r["tag"] is not None]
    assert len(real) == 1
    assert real[0]["previous_tag"] is None
    assert real[0]["next_tag"] is None
