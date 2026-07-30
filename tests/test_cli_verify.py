"""US-6: CLI `verify <snapshot>` (AC-6.4)."""

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


def test_verify_matching_snapshot_reports_match(built_repo: Path):
    build = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert build.returncode == 0, build.stderr
    path = str(snapshot_path(built_repo, "2026-07-29"))

    result = _run_cli(built_repo, "verify", path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"snapshot": path, "matches": True}


def test_verify_tampered_snapshot_exits_1_with_named_mismatch(built_repo: Path):
    build = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert build.returncode == 0, build.stderr
    path = Path(snapshot_path(built_repo, "2026-07-29"))

    data = json.loads(path.read_text())
    data["provenance"]["insights_version"] = "9.9.9-tampered"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = _run_cli(built_repo, "verify", str(path))
    assert result.returncode == 1
    assert "verify_mismatch" in result.stderr


def test_verify_missing_file_exits_1_with_named_error_not_a_traceback(tmp_path: Path):
    result = _run_cli(tmp_path, "verify", "does-not-exist.json")
    assert result.returncode == 1
    assert "snapshot_unreadable" in result.stderr
    assert "Traceback" not in result.stderr


def test_verify_wrong_shape_json_exits_1_with_named_error_not_a_traceback(tmp_path: Path):
    """F5: a valid JSON file that isn't snapshot-shaped (e.g. package.json) must not crash."""
    not_a_snapshot = tmp_path / "package.json"
    not_a_snapshot.write_text('{"name": "not-a-snapshot", "version": "1.0.0"}\n', encoding="utf-8")

    result = _run_cli(tmp_path, "verify", str(not_a_snapshot))
    assert result.returncode == 1
    assert "snapshot_unreadable" in result.stderr
    assert "Traceback" not in result.stderr


def test_verify_without_matching_repo_hints_at_repo_flag(built_repo: Path, tmp_path: Path):
    """B4: omitting/mis-setting --repo must not read as 'you never ran build'."""
    build = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert build.returncode == 0, build.stderr
    path = str(snapshot_path(built_repo, "2026-07-29"))

    unbuilt_cwd = tmp_path / "somewhere-else"
    unbuilt_cwd.mkdir()
    result = _run_cli(unbuilt_cwd, "verify", path)  # no --repo, cwd has no graph
    assert result.returncode == 1
    assert "graph_not_built" in result.stderr
    assert "--repo" in result.stderr
