"""RB-T1: walking skeleton — tag enumeration + `insights releases --format json`
(AC-1.1, AC-1.4, AC-1.5, AC-1.7, AC-1.10, NFR-1)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.errors import NotAGitRepoError
from aspark_insights.gitboard import gitread
from aspark_insights.gitboard.releasemap import build_release_map


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True, text=True, cwd=repo,
    )


@pytest.fixture
def two_tag_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: one")
    _git(repo, "tag", "v0.1.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: two")
    _git(repo, "tag", "v0.2.0")
    return repo


# --- AC-1.1: one entry per tag, topology-ordered oldest first ---------------


def test_release_list_has_one_entry_per_tag_oldest_first(two_tag_repo: Path):
    result = build_release_map(str(two_tag_repo), "2026-08-19")
    # A trailing tag:null pseudo-release is also present once a tag exists
    # (AC-1.9, added in T4) — filter to real tags for this real-tag-order check.
    real_tags = [r["tag"] for r in result["releases"] if r["tag"] is not None]
    assert real_tags == ["v0.1.0", "v0.2.0"]


def test_gitread_list_tags_topo_order_matches_git_tag_list(two_tag_repo: Path):
    real_tags = set(_git(two_tag_repo, "tag", "--list").stdout.split())
    entries = gitread.list_tags_topo_order(str(two_tag_repo))
    assert {e["tag"] for e in entries} == real_tags
    assert all(e["reachable"] for e in entries)


# --- AC-1.4: zero tags -> honest empty list + reason, exit 0 ----------------


def test_zero_tags_is_empty_list_with_reason(tmp_path: Path):
    repo = tmp_path / "notags"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: only")
    result = build_release_map(str(repo), "2026-08-19")
    assert result["releases"] == []
    assert result["reason"] == "repository has no tags"


def test_zero_tags_cli_exits_zero(tmp_path: Path):
    repo = tmp_path / "notags"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: only")
    result = _run_cli(repo, "releases", "--as-of", "2026-08-19")
    assert result.returncode == 0
    assert '"reason": "repository has no tags"' in result.stdout


# --- AC-1.5: hostile --repo -> named error, exit 1, never a traceback ------


def test_empty_repo_string_rejected_before_any_git_call():
    with pytest.raises(NotAGitRepoError):
        build_release_map("", "2026-08-19")


def test_non_git_directory_is_named_error_not_a_traceback(tmp_path: Path):
    result = _run_cli(tmp_path, "releases", "--as-of", "2026-08-19", "--repo", str(tmp_path))
    assert result.returncode == 1
    assert "not_a_git_repo" in result.stderr
    assert "Traceback" not in result.stderr


# --- AC-1.7: byte-identical repeat runs -------------------------------------


def test_byte_identical_repeat_runs(two_tag_repo: Path):
    a = build_release_map(str(two_tag_repo), "2026-08-19")
    b = build_release_map(str(two_tag_repo), "2026-08-19")
    from aspark_insights.serialization import canonical_json

    assert canonical_json(a) == canonical_json(b)


# --- AC-1.10: every entry carries a tag field; null is the pseudo-release --


def test_every_real_release_entry_carries_its_tag_string(two_tag_repo: Path):
    result = build_release_map(str(two_tag_repo), "2026-08-19")
    for r in result["releases"]:
        assert r["tag"] in {"v0.1.0", "v0.2.0", None}
        if r["tag"] is None:
            continue  # the pseudo-release (T4) — its null tag is AC-1.10's own point
        assert r["tag"] is not None


# --- NFR-1: JSON stdout, exit codes, --help ---------------------------------


def test_help_documents_flags(tmp_path: Path):
    result = _run_cli(tmp_path, "releases", "--help")
    assert result.returncode == 0
    assert "--as-of" in result.stdout
    assert "--repo" in result.stdout
