"""RBH-T9: determinism canary — a real git repo, built and rendered twice,
byte-identical HTML (NFR-6), including the inlined base64 logo."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.releasemap import build_release_map
from aspark_insights.gitboard.releaseboard_report import render_release_board_html


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
    (repo / ".spark").mkdir()
    (repo / ".spark" / "feature-a").mkdir()
    (repo / ".spark" / "feature-a" / "spec.md").write_text(
        "# Spec\n\n| | |\n|---|---|\n| **Status** | `approved` |\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "fix: second")
    _git(repo, "branch", "feature/x")
    return repo


def test_double_render_html_is_byte_identical(real_repo: Path):
    data = build_release_map(str(real_repo), "2026-08-20")
    first = render_release_board_html(data)
    second = render_release_board_html(data)
    assert first == second


def test_double_build_and_render_end_to_end_is_byte_identical(real_repo: Path):
    data_1 = build_release_map(str(real_repo), "2026-08-20")
    html_1 = render_release_board_html(data_1)
    data_2 = build_release_map(str(real_repo), "2026-08-20")
    html_2 = render_release_board_html(data_2)
    assert html_1 == html_2
