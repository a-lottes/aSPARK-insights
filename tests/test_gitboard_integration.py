"""GB-T9: real-git integration — privacy against a real Co-Authored-By
trailer, and a real shallow clone (NFR-3 live constraint; AC-1.8/AC-4.8).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.board import build_board
from aspark_insights.gitboard.report import render_board_html


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


# --- NFR-3: a real Co-Authored-By trailer never reaches any output --------


def test_co_authored_by_trailer_never_reaches_json_or_html(tmp_path: Path):
    repo = tmp_path / "trailered"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    message = "feat: paired work\n\nCo-Authored-By: Someone Else <someone@example.com>"
    _git(repo, "commit", "--allow-empty", "-q", "-m", message)

    board = build_board(str(repo), "2026-08-13")
    blob = json.dumps(board)
    html = render_board_html(board)

    for artifact in (blob, html):
        assert "Co-Authored-By" not in artifact
        assert "someone@example.com" not in artifact
        assert "Someone Else" not in artifact
        assert "Test" not in artifact  # the committer identity used to build the fixture
        assert "t@example.com" not in artifact


def test_signed_off_by_trailer_never_reaches_json_or_html(tmp_path: Path):
    repo = tmp_path / "signedoff"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    message = "fix: something\n\nSigned-off-by: Test <t@example.com>"
    _git(repo, "commit", "--allow-empty", "-q", "-m", message)

    board = build_board(str(repo), "2026-08-13")
    blob = json.dumps(board)
    assert "Signed-off-by" not in blob


# --- AC-1.8/AC-4.8: a genuinely shallow clone -------------------------------


@pytest.fixture
def shallow_clone(tmp_path: Path) -> Path:
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-q")
    _git(origin, "commit", "--allow-empty", "-q", "-m", "feat: one")
    _git(origin, "tag", "v1.0.0")
    _git(origin, "commit", "--allow-empty", "-q", "-m", "feat: two")
    _git(origin, "commit", "--allow-empty", "-q", "-m", "feat: three")

    shallow = tmp_path / "shallow"
    # `--depth` is silently ignored for local-path clones ("--depth is
    # ignored in local clones; use file:// instead" — git's own message);
    # the file:// scheme is required to produce a genuinely shallow clone.
    # depth=3 (== the origin's full history) still sets is-shallow-repository
    # true while keeping v1.0.0 reachable, so this exercises "shallow AND
    # tagged" rather than "shallow with no tag at all" (a different case,
    # already covered elsewhere).
    subprocess.run(
        ["git", "clone", "--depth", "3", f"file://{origin}", str(shallow)],
        capture_output=True, text=True, check=True,
    )
    return shallow


def test_shallow_clone_discloses_shallow_true(shallow_clone: Path):
    board = build_board(str(shallow_clone), "2026-08-13")
    assert board["provenance"]["shallow"] is True


def test_shallow_clone_html_carries_the_at_least_qualifier(shallow_clone: Path):
    board = build_board(str(shallow_clone), "2026-08-13")
    text = render_board_html(board)
    sentence = text.split('class="answer-sentence"')[1].split("</p>")[0]
    assert "At least" in sentence


def test_non_shallow_clone_never_carries_the_at_least_qualifier(tmp_path: Path):
    repo = tmp_path / "full"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: more")
    board = build_board(str(repo), "2026-08-13")
    text = render_board_html(board)
    sentence = text.split('class="answer-sentence"')[1].split("</p>")[0]
    assert "At least" not in sentence
