"""US-7: the determinism canary (AC-7.1, AC-7.2).

Two halves: (1) building the frozen fixture twice, independently, must be
byte-identical — the canary CI runs on every commit; (2) the canary is itself
proven to catch the regression class it exists for, by showing a clock-reading
metric function produces different output for identical inputs.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from aspark_insights.metrics.registry import MetricRegistry
from aspark_insights.model.provenance import GraphSource, Provenance, ScopeFilterResult
from aspark_insights.model.snapshot import Snapshot
from aspark_insights.model.value import MetricValue
from aspark_insights.serialization import canonical_json
from aspark_insights.store import snapshot_path

FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "graph.json"
TRACE_FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "trace_graph.json"
FIXED_AS_OF = "2026-07-29"  # frozen, never derived from the wall clock


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True,
        text=True,
        cwd=repo,
    )


def test_double_build_against_frozen_fixture_is_byte_identical(tmp_path: Path):
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(FIXTURE_GRAPH, graph_dir / "graph.json")

    run_1 = _run_cli(tmp_path, "build", "--as-of", FIXED_AS_OF)
    bytes_1 = snapshot_path(tmp_path, FIXED_AS_OF).read_bytes()

    run_2 = _run_cli(tmp_path, "build", "--as-of", FIXED_AS_OF)
    bytes_2 = snapshot_path(tmp_path, FIXED_AS_OF).read_bytes()

    assert run_1.returncode == 0, run_1.stderr
    assert run_2.returncode == 0, run_2.stderr
    assert bytes_1 == bytes_2, "double build of the frozen fixture must be byte-identical"


def test_double_build_against_trace_fixture_is_byte_identical_with_real_metrics(tmp_path: Path):
    """AC-7.3: extends the canary past the empty-catalog case — a fixture with real
    Story/AC/Task/File nodes must still double-build byte-identical now that the
    metrics array is genuinely populated, not empty."""
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(TRACE_FIXTURE_GRAPH, graph_dir / "graph.json")

    run_1 = _run_cli(tmp_path, "build", "--as-of", FIXED_AS_OF)
    bytes_1 = snapshot_path(tmp_path, FIXED_AS_OF).read_bytes()

    run_2 = _run_cli(tmp_path, "build", "--as-of", FIXED_AS_OF)
    bytes_2 = snapshot_path(tmp_path, FIXED_AS_OF).read_bytes()

    assert run_1.returncode == 0, run_1.stderr
    assert run_2.returncode == 0, run_2.stderr

    import json

    metrics = json.loads(bytes_1)["metrics"]
    assert len(metrics) >= 6  # TRC-001..003, both TRC-004 entries, three TRC-005 tiers
    assert any(m["metric_id"] == "TRC-001" and m["value"] is not None for m in metrics)
    assert bytes_1 == bytes_2, "double build with a non-empty metrics catalog must be byte-identical"


def test_canary_would_detect_an_ambient_clock_violation(monkeypatch):
    """Proves the byte-compare technique itself catches the regression class ADR-4 forbids.

    Builds two real Snapshots — through Snapshot.seal and canonical_json, the exact
    substrate `insights build` and the positive canary above exercise — whose only
    difference is a MetricValue produced by a clock-reading registry function, and
    shows the serialized bytes differ. That is precisely what CI's byte-compare
    would flag if such a metric were ever wired into a real build.
    """
    reg = MetricRegistry()

    def _clock_reading_metric(facts, *, as_of: str | None = None) -> MetricValue:
        return MetricValue(metric_id="BAD-001", metric_version="1.0.0", value=time.time())

    reg.register("BAD-001", "1.0.0", _clock_reading_metric)
    fn = reg.get("BAD-001", "1.0.0")

    clock_readings = iter([1_000.0, 2_000.0])
    monkeypatch.setattr(time, "time", lambda: next(clock_readings))

    provenance = Provenance(
        as_of=FIXED_AS_OF,
        insights_version="0.1.0",
        metric_registry_version="0.1.0",
        graph_source=GraphSource(access="library-interim", sealed=True),
        policy_versions=None,
        scope_filter=ScopeFilterResult(patterns=(), excluded_count=0),
        graph_staleness=None,
    )

    snapshot_1 = Snapshot.seal(facts=[], metrics=[fn((), as_of=FIXED_AS_OF)], provenance=provenance)
    snapshot_2 = Snapshot.seal(facts=[], metrics=[fn((), as_of=FIXED_AS_OF)], provenance=provenance)

    bytes_1 = canonical_json(snapshot_1.to_dict())
    bytes_2 = canonical_json(snapshot_2.to_dict())

    assert bytes_1 != bytes_2, (
        "same inputs (facts, as_of, provenance) produced different serialized bytes — "
        "this is exactly what the CI canary's byte-compare would catch"
    )
