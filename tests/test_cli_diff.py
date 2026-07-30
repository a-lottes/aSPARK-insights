"""US-6: CLI `diff <a> <b>` (AC-6.3)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.store import snapshot_path

FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "graph.json"


@pytest.fixture
def built_repo(tmp_path: Path) -> Path:
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(FIXTURE_GRAPH, graph_dir / "graph.json")
    return tmp_path


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True,
        text=True,
        cwd=repo,
    )


def test_diff_of_snapshot_against_itself_is_empty(built_repo: Path):
    build = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert build.returncode == 0, build.stderr
    path = str(snapshot_path(built_repo, "2026-07-29"))

    result = _run_cli(built_repo, "diff", path, path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {}


def test_diff_between_different_as_of_snapshots_shows_provenance_change(built_repo: Path):
    _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    _run_cli(built_repo, "build", "--as-of", "2026-07-30")
    path_a = str(snapshot_path(built_repo, "2026-07-29"))
    path_b = str(snapshot_path(built_repo, "2026-07-30"))

    result = _run_cli(built_repo, "diff", path_a, path_b)
    assert result.returncode == 0, result.stderr
    diff = json.loads(result.stdout)
    assert diff["provenance"]["as_of"] == {"a": "2026-07-29", "b": "2026-07-30"}


def test_diff_missing_file_exits_1_with_named_error_not_a_traceback(tmp_path: Path):
    result = _run_cli(tmp_path, "diff", "does-not-exist-a.json", "does-not-exist-b.json")
    assert result.returncode == 1
    assert "snapshot_unreadable" in result.stderr
    assert "Traceback" not in result.stderr
