"""T2: run_query is the one read core both adapters share (AC-1.3, NFR-5, NFR-8).

A CLI-byte-unchanged regression test proves the cli._cmd_query refactor to
call run_query() didn't change stdout, which is what makes NFR-8's
"value-identical" claim a fact about a shared function, not a promise about
two independently maintained read paths.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.build import build_snapshot
from aspark_insights.errors import InsightsError
from aspark_insights.query import run_query
from aspark_insights.store import write_snapshot

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


def test_run_query_returns_facts_metrics_provenance(built_repo: Path):
    snapshot = build_snapshot(built_repo, as_of="2026-07-29")
    write_snapshot(built_repo, snapshot)

    result = run_query(str(built_repo))

    assert set(result.keys()) == {"facts", "metrics", "provenance"}
    assert result["provenance"]["as_of"] == "2026-07-29"
    assert result["facts"] == snapshot.to_dict()["facts"]
    assert result["metrics"] == snapshot.to_dict()["metrics"]
    assert result["provenance"] == snapshot.to_dict()["provenance"]


def test_run_query_no_metric_is_enumerated_by_name(built_repo: Path):
    """AC-1.3: whatever the snapshot's `metrics` array currently holds passes
    through as-is — the read core names no metric id, so a future newly
    registered metric would appear with zero code change here."""
    snapshot = build_snapshot(built_repo, as_of="2026-07-29")
    write_snapshot(built_repo, snapshot)

    result = run_query(str(built_repo))

    assert result["metrics"] == snapshot.to_dict()["metrics"]


def test_run_query_raises_no_snapshot(tmp_path: Path):
    with pytest.raises(InsightsError) as exc_info:
        run_query(str(tmp_path))
    assert exc_info.value.reason == "no_snapshot"


def test_run_query_raises_snapshot_unreadable_on_corrupt_snapshot(tmp_path: Path):
    snapshots_dir = tmp_path / ".aspark-insights" / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "2026-07-29.json").write_text("{not valid json", encoding="utf-8")

    with pytest.raises(InsightsError) as exc_info:
        run_query(str(tmp_path))
    assert exc_info.value.reason == "snapshot_unreadable"


@pytest.mark.parametrize("payload", ["5", "null", "3.14", '"a string"', "[]"])
def test_run_query_raises_snapshot_unreadable_on_non_object_json(tmp_path: Path, payload: str):
    """Constitution hostile-input checklist: a snapshot file that is valid JSON
    but a scalar/list (not an object) must raise the named `snapshot_unreadable`
    error, never a raw TypeError traceback (AC-1.4, NFR-3)."""
    snapshots_dir = tmp_path / ".aspark-insights" / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "2026-07-29.json").write_text(payload, encoding="utf-8")

    with pytest.raises(InsightsError) as exc_info:
        run_query(str(tmp_path))
    assert exc_info.value.reason == "snapshot_unreadable"


def test_cli_query_stdout_is_byte_unchanged_after_the_run_query_refactor(built_repo: Path):
    """Regression guard for the T2 refactor: cli._cmd_query now delegates to
    run_query(), but must print exactly what it printed before."""
    build_result = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert build_result.returncode == 0, build_result.stderr

    query_result = _run_cli(built_repo, "query")
    assert query_result.returncode == 0, query_result.stderr

    import json

    data = json.loads(query_result.stdout)
    assert set(data.keys()) == {"facts", "metrics", "provenance"}
    assert data["provenance"]["as_of"] == "2026-07-29"
    assert data["facts"] == []  # fixture has no Story/AC/Task nodes to collect
