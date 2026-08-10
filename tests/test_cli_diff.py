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


def test_diff_shows_metric_version_change_together_with_value_change(tmp_path: Path):
    """AC-5.3: a metric whose definition changed (measurement-honesty's version
    bump) shows both the version and the value change in one diff — never a
    version bump silently hidden behind an unexplained value change."""
    common_provenance = {
        "as_of": "2026-07-29", "insights_version": "0.4.0", "metric_registry_version": "0.1.0",
        "graph_source": {"access": "library-interim", "sealed": True}, "policy_versions": None,
        "scope_filter": {"patterns": [], "excluded_count": 0}, "graph_staleness": None,
        "artifact_probe": {"outcome": "absent", "matched_file_count": 0, "matched_filenames": [], "feature_dir_count": 0, "detail": None},
    }
    snapshot_a = {
        "facts": [], "provenance": common_provenance,
        "metrics": [{"metric_id": "TRC-002", "metric_version": "1.0.0", "value": 0.0, "reason": None, "n": 41}],
    }
    snapshot_b = {
        "facts": [], "provenance": common_provenance,
        "metrics": [{"metric_id": "TRC-002", "metric_version": "2.0.0", "value": None, "reason": "no evidence found", "n": 41}],
    }
    path_a = tmp_path / "a.json"
    path_b = tmp_path / "b.json"
    path_a.write_text(json.dumps(snapshot_a), encoding="utf-8")
    path_b.write_text(json.dumps(snapshot_b), encoding="utf-8")

    result = _run_cli(tmp_path, "diff", str(path_a), str(path_b))
    assert result.returncode == 0, result.stderr
    diff = json.loads(result.stdout)
    assert diff["metrics"]["a"] == snapshot_a["metrics"]
    assert diff["metrics"]["b"] == snapshot_b["metrics"]
    # both the version string and the value differ in the same shown diff
    assert diff["metrics"]["a"][0]["metric_version"] != diff["metrics"]["b"][0]["metric_version"]
    assert diff["metrics"]["a"][0]["value"] != diff["metrics"]["b"][0]["value"]
