"""GB-T9: determinism canary — a real git repo, built twice, byte-identical
JSON and HTML (AC-1.6, NFR-5)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.board import build_board
from aspark_insights.gitboard.report import render_board_html
from aspark_insights.serialization import canonical_json


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


@pytest.fixture
def real_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "canary"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "fix: second")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "docs: third")
    _git(repo, "branch", "feature/x")
    return repo


def test_double_build_json_is_byte_identical(real_repo: Path):
    first = canonical_json(build_board(str(real_repo), "2026-08-13"))
    second = canonical_json(build_board(str(real_repo), "2026-08-13"))
    assert first == second


def test_double_render_html_is_byte_identical(real_repo: Path):
    board = build_board(str(real_repo), "2026-08-13")
    first = render_board_html(board)
    second = render_board_html(board)
    assert first == second


def test_double_build_and_render_end_to_end_is_byte_identical(real_repo: Path):
    """Rebuilds the board dict fresh each time too — not just re-rendering
    the same dict — to prove the whole pipeline is deterministic, not only
    the pure render function."""
    board_1 = build_board(str(real_repo), "2026-08-13")
    html_1 = render_board_html(board_1)
    board_2 = build_board(str(real_repo), "2026-08-13")
    html_2 = render_board_html(board_2)
    assert canonical_json(board_1) == canonical_json(board_2)
    assert html_1 == html_2
