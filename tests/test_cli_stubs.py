"""US-6: CLI help, `render` stub, `query` readback (AC-6.1, AC-6.5, NFR-3)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

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


@pytest.mark.parametrize("command", ["build", "query", "render", "diff", "verify"])
def test_help_prints_usage_and_exits_0(tmp_path: Path, command: str):
    result = _run_cli(tmp_path, command, "--help")
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_render_exits_1_with_named_not_implemented_error(tmp_path: Path):
    result = _run_cli(tmp_path, "render")
    assert result.returncode == 1
    assert "not_implemented" in result.stderr
    assert result.stdout == ""


def test_query_reads_back_raw_facts_and_provenance_from_last_snapshot(built_repo: Path):
    build_result = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert build_result.returncode == 0, build_result.stderr

    query_result = _run_cli(built_repo, "query")
    assert query_result.returncode == 0, query_result.stderr

    import json

    data = json.loads(query_result.stdout)
    assert set(data.keys()) == {"facts", "metrics", "provenance"}
    assert data["provenance"]["as_of"] == "2026-07-29"
    assert data["facts"] == []  # fixture has no Story/AC/Task nodes to collect


def test_query_with_no_snapshot_exits_1_with_named_error(tmp_path: Path):
    result = _run_cli(tmp_path, "query")
    assert result.returncode == 1
    assert "no_snapshot" in result.stderr


def test_query_on_corrupt_snapshot_exits_1_with_named_error_not_a_traceback(tmp_path: Path):
    snapshots_dir = tmp_path / ".aspark-insights" / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "2026-07-29.json").write_text("{not valid json", encoding="utf-8")

    result = _run_cli(tmp_path, "query")
    assert result.returncode == 1
    assert "snapshot_unreadable" in result.stderr
    assert "Traceback" not in result.stderr


def test_query_on_wrong_shape_json_exits_1_with_named_error_not_a_traceback(tmp_path: Path):
    """F5: valid JSON that isn't snapshot-shaped (e.g. an empty {}) must not crash."""
    snapshots_dir = tmp_path / ".aspark-insights" / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "2026-07-29.json").write_text("{}", encoding="utf-8")

    result = _run_cli(tmp_path, "query")
    assert result.returncode == 1
    assert "snapshot_unreadable" in result.stderr
    assert "Traceback" not in result.stderr
