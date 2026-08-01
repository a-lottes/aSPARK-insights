"""US-6 walking skeleton: `insights build --as-of` end to end (AC-6.2, AC-4.4, NFR-1, NFR-5)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.build import build_snapshot
from aspark_insights.errors import GraphNotBuiltError, InvalidAsOfError
from aspark_insights.store import snapshot_path, snapshots_dir

FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "graph.json"


@pytest.fixture
def built_repo(tmp_path: Path) -> Path:
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(FIXTURE_GRAPH, graph_dir / "graph.json")
    return tmp_path


def test_build_snapshot_seals_honest_metrics_with_provenance(built_repo: Path):
    """The shared File/Function fixture has no Story/AC/Task nodes — every
    registered metric honestly reports null+reason rather than a fabricated
    number, per traceability-metrics' own zero-denominator rule."""
    snap = build_snapshot(built_repo, as_of="2026-07-29")
    assert len(snap.metrics) >= 1
    assert all(m.value is None and m.reason for m in snap.metrics)
    assert snap.provenance.as_of == "2026-07-29"
    assert snap.provenance.graph_source.access == "library-interim"
    assert snap.provenance.graph_source.sealed is True
    assert snap.provenance.policy_versions is None


def test_build_snapshot_raises_named_error_on_unbuilt_graph(tmp_path: Path):
    with pytest.raises(GraphNotBuiltError):
        build_snapshot(tmp_path, as_of="2026-07-29")


@pytest.mark.parametrize(
    "bad_as_of",
    [
        "../../../../../../../../tmp/insights-traversal-poc",
        "../../etc/evil",
        "not-a-date",
        "",
        "2026-13-45",  # not a real calendar date
        "2026/07/29",  # wrong separator
    ],
)
def test_build_snapshot_rejects_invalid_as_of(built_repo: Path, bad_as_of: str):
    """B5: an unvalidated --as-of is a path-traversal / arbitrary-write primitive."""
    with pytest.raises(InvalidAsOfError):
        build_snapshot(built_repo, as_of=bad_as_of)


def test_build_snapshot_rejecting_bad_as_of_never_touches_the_filesystem(built_repo: Path, tmp_path: Path):
    outside_target = tmp_path.parent / "insights-traversal-poc.json"
    outside_target.unlink(missing_ok=True)
    try:
        with pytest.raises(InvalidAsOfError):
            build_snapshot(built_repo, as_of=f"../{outside_target.stem}")
        assert not outside_target.exists()
    finally:
        outside_target.unlink(missing_ok=True)


def test_build_twice_is_byte_identical(built_repo: Path):
    snap1 = build_snapshot(built_repo, as_of="2026-07-29")
    snap2 = build_snapshot(built_repo, as_of="2026-07-29")
    from aspark_insights.serialization import canonical_json

    assert canonical_json(snap1.to_dict()) == canonical_json(snap2.to_dict())


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True,
        text=True,
        cwd=repo,
    )


def test_cli_build_writes_snapshot_and_prints_canonical_json(built_repo: Path):
    result = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert result.returncode == 0, result.stderr
    assert result.stdout.endswith("\n")
    out_path = snapshot_path(built_repo, "2026-07-29")
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8") == result.stdout


def test_cli_build_exits_1_with_named_error_on_unbuilt_graph(tmp_path: Path):
    result = _run_cli(tmp_path, "build", "--as-of", "2026-07-29")
    assert result.returncode == 1
    assert "graph_not_built" in result.stderr or "graph not built" in result.stderr
    assert result.stdout == ""


def test_cli_build_twice_on_disk_is_byte_identical(built_repo: Path):
    r1 = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    path = snapshot_path(built_repo, "2026-07-29")
    bytes1 = path.read_bytes()
    r2 = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    bytes2 = path.read_bytes()
    assert r1.returncode == r2.returncode == 0
    assert bytes1 == bytes2


def test_cli_build_rejects_path_traversal_as_of_with_no_write(built_repo: Path):
    """B5, reproduced exactly as QA found it: must not write outside .aspark-insights/."""
    canary = built_repo.parent / "insights-traversal-poc.json"
    canary.unlink(missing_ok=True)
    try:
        result = _run_cli(
            built_repo, "build", "--as-of",
            f"../../../../../../../../{canary.stem}",
        )
        assert result.returncode == 1
        assert "invalid_as_of" in result.stderr
        assert not canary.exists()
    finally:
        canary.unlink(missing_ok=True)


def test_cli_build_output_flag_redirects_write_location(built_repo: Path, tmp_path: Path):
    """B1: --output lets a caller avoid writing into the analyzed repo."""
    output_dir = tmp_path / "elsewhere"
    result = _run_cli(built_repo, "build", "--as-of", "2026-07-29", "--output", str(output_dir))
    assert result.returncode == 0, result.stderr
    assert snapshot_path(output_dir, "2026-07-29").exists()
    assert not snapshots_dir(built_repo).exists()


def test_cli_build_default_output_is_unchanged(built_repo: Path):
    """B1: omitting --output preserves the pre-fix default (writes under --repo)."""
    result = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert result.returncode == 0, result.stderr
    assert snapshot_path(built_repo, "2026-07-29").exists()
