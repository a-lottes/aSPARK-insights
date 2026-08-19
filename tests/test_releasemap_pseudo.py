"""RB-T4: pseudo-release via verbatim `build_board()` reuse
(AC-1.8, AC-1.9, AC-1.10, NFR-3, NFR-7)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.board import build_board
from aspark_insights.gitboard.releasemap import build_release_map


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


@pytest.fixture
def tagged_repo_with_open_window(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: open work")
    return repo


# --- AC-1.10: sole discriminator ---------------------------------------------


def test_pseudo_release_has_tag_null(tagged_repo_with_open_window: Path):
    result = build_release_map(str(tagged_repo_with_open_window), "2026-08-19")
    assert result["releases"][-1]["tag"] is None
    assert all(r["tag"] is not None for r in result["releases"][:-1])


def test_exactly_one_pseudo_release_entry(tagged_repo_with_open_window: Path):
    result = build_release_map(str(tagged_repo_with_open_window), "2026-08-19")
    null_tags = [r for r in result["releases"] if r["tag"] is None]
    assert len(null_tags) == 1


# --- AC-1.8: verbatim reuse, byte-equal to a live build_board() call --------


def test_pseudo_release_figures_are_byte_equal_to_live_build_board(tagged_repo_with_open_window: Path):
    result = build_release_map(str(tagged_repo_with_open_window), "2026-08-19")
    pseudo = result["releases"][-1]
    live = build_board(str(tagged_repo_with_open_window), "2026-08-19")

    assert pseudo["commits"] == live["commits"]
    assert pseudo["branches"] == live["branches"]
    assert ("days_since_tag" in pseudo) == ("days_since_tag" in live)
    if "days_since_tag" in live:
        assert pseudo["days_since_tag"] == live["days_since_tag"]
    assert ("work_types" in pseudo) == ("work_types" in live)
    if "work_types" in live:
        assert pseudo["work_types"] == live["work_types"]


# --- AC-1.9: true zero (present, empty) vs no-tag-at-all (absent) ----------


def test_zero_commits_since_latest_tag_is_present_not_omitted(tmp_path: Path):
    repo = tmp_path / "zerosince"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    result = build_release_map(str(repo), "2026-08-19")
    pseudo = result["releases"][-1]
    assert pseudo["tag"] is None
    assert pseudo["commits"]["value"] == 0
    assert pseudo["members"] == []
    assert pseudo["unattributed"] == []


def test_no_tags_at_all_means_no_pseudo_release_entry(tmp_path: Path):
    repo = tmp_path / "notags"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: only")
    result = build_release_map(str(repo), "2026-08-19")
    assert result["releases"] == []


# --- Members/unattributed computed over the pseudo-release's own range -----


def test_pseudo_release_membership_reflects_feature_dirs_touched_since_tag(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    (repo / ".spark" / "new-feature").mkdir(parents=True)
    (repo / ".spark" / "new-feature" / "spec.md").write_text("...", encoding="utf-8")
    _git(repo, "add", ".spark/new-feature/spec.md")
    _git(repo, "commit", "-q", "-m", "feat: new-feature spec")

    result = build_release_map(str(repo), "2026-08-19")
    pseudo = result["releases"][-1]
    assert [m["name"] for m in pseudo["members"]] == ["new-feature"]


# --- NFR-7: determinism (no wall-clock, fixed HEAD/as_of) -------------------


def test_pseudo_release_is_deterministic_at_fixed_head_and_as_of(tagged_repo_with_open_window: Path):
    a = build_release_map(str(tagged_repo_with_open_window), "2026-08-19")
    b = build_release_map(str(tagged_repo_with_open_window), "2026-08-19")
    from aspark_insights.serialization import canonical_json

    assert canonical_json(a) == canonical_json(b)


# --- F3 (review, Minor): previous_tag must come from build_board's own
#     resolved tag, never from releasemap's separately topo-ordered list --


@pytest.fixture
def two_tag_repo_with_open_window(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: one")
    _git(repo, "tag", "v1.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: two")
    _git(repo, "tag", "v2.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: open")
    return repo


def test_pseudo_release_previous_tag_sourced_from_build_board_not_recomputed(
    two_tag_repo_with_open_window: Path, monkeypatch,
):
    """F3 (review, Minor): `previous_tag` must be `build_board`'s own
    resolved tag — never a value `releasemap` derives separately from its
    own topo-ordered tag list (the old bug sourced it from
    `releases[-1]["tag"]`, which could disagree with `build_board`'s
    `git describe` pick on an unreachable or tied tag). Proven by forcing a
    deliberate disagreement: `build_board` is monkeypatched to report the
    *older* real tag (`v1.0.0`) as resolved, even though the natural nearest
    tag is `v2.0.0` — the pseudo-release must reflect the injected value,
    proving it reads `build_board`'s own field rather than re-deriving it."""
    from aspark_insights.gitboard import releasemap

    real_build_board = releasemap.build_board

    def _resolved_to_older_tag(repo_root, as_of):
        board = real_build_board(repo_root, as_of)
        board["provenance"]["resolved_tag"] = "v1.0.0"  # deliberately not v2.0.0
        return board

    monkeypatch.setattr(releasemap, "build_board", _resolved_to_older_tag)
    result = releasemap._pseudo_release(str(two_tag_repo_with_open_window), "2026-08-19", [])
    assert result["previous_tag"] == "v1.0.0"
