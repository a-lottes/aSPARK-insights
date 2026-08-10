"""US-2: integration test against a real, pinned aspark-graph install (AC-2.1, AC-2.2, C4).

Mocking only would defer validation of the riskiest coupling — the interim library
adapter's direct import of aspark_graph internals — to I2. This test runs against
the actual sibling repo (a uv path dependency, checked out alongside this one),
not a fixture, so that coupling is proven now.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aspark_insights.build import build_snapshot
from aspark_insights.errors import GraphNotBuiltError
from aspark_insights.ports.graph import CLIGraphPort, LibraryInterimGraphPort

REPO_ROOT = Path(__file__).resolve().parent.parent
SIBLING_GRAPH_REPO = REPO_ROOT.parent / "aSPARK-graph"
SIBLING_GRAPH_JSON = SIBLING_GRAPH_REPO / ".aspark-graph" / "graph.json"
SELF_GRAPH_JSON = REPO_ROOT / ".aspark-graph" / "graph.json"

pytestmark = pytest.mark.skipif(
    not SIBLING_GRAPH_JSON.exists(),
    reason=(
        f"no built graph at {SIBLING_GRAPH_JSON} — run `aspark-graph build .` in "
        "the sibling repo first (CI does this explicitly; see .github/workflows/ci.yml)"
    ),
)


def test_library_adapter_matches_the_graphs_own_canonical_document():
    port = LibraryInterimGraphPort()
    result = port.read_graph(SIBLING_GRAPH_REPO)

    expected = json.loads(SIBLING_GRAPH_JSON.read_text(encoding="utf-8"))
    assert result == expected
    assert result["nodes"], "expected at least one real node from the family's own graph"


def test_cli_adapter_returns_the_graphs_contract_json():
    port = CLIGraphPort()
    result = port.query("staleness", repo_root=str(SIBLING_GRAPH_REPO))
    assert "files_checked" in result
    assert "stale" in result


def test_library_adapter_raises_named_error_against_a_truly_unbuilt_graph(tmp_path: Path):
    port = LibraryInterimGraphPort()
    with pytest.raises(GraphNotBuiltError):
        port.read_graph(tmp_path)


# --- traceability-metrics (I2): TRC-*/MTA-* against real, unmocked graphs ---


def test_trc_metrics_against_the_sibling_repo_are_real_values_or_honest_null():
    """Every TRC-* entry either computes a real value or reports null+reason —
    never a fabricated number — and every entry carries its own n (AC-7.1)."""
    snap = build_snapshot(SIBLING_GRAPH_REPO, as_of="2026-07-31")
    trc_entries = [m for m in snap.metrics if m.metric_id.startswith("TRC-")]
    assert len(trc_entries) >= 6  # TRC-001..003, both TRC-004 entries, three TRC-005 tiers
    for m in trc_entries:
        assert m.n is not None
        assert (m.value is not None) or (m.value is None and m.reason)

    trc_001 = next(m for m in trc_entries if m.metric_id == "TRC-001")
    assert trc_001.n > 0, "the family's own repo has real Story nodes to measure"


@pytest.mark.skipif(
    not SELF_GRAPH_JSON.exists(),
    reason=f"no built graph at {SELF_GRAPH_JSON} — run `aspark-graph build .` in this repo first",
)
def test_trc_002_against_this_repos_own_graph_demonstrates_the_measurement_honesty_fix():
    """A3 (spec.md §3) → measurement-honesty: this repo uses the *current*
    review.md/qa.md naming, which the installed graph tool's artifact parser
    doesn't recognize (it looks for the legacy review-report.md/qa-report.md).
    Story/AC/Task nodes parse fine (from spec.md/plan.md, which the parser
    *does* recognize), but zero QACheck nodes ever populate here — before this
    feature, TRC-002 read a confident, fabricated 0.0/n=41 (a real bug, not a
    real measurement — see `.spark/traceability-metrics/spec.md` A3 and
    `.spark/measurement-honesty/spec.md` §1). This test proves the fix against
    the real, unmocked dogfood target: the evidence-absent gate now nulls both
    QA metrics with a reason naming the real observed counts, while every
    other TRC metric — whose evidence layer genuinely exists on this repo —
    still carries a real computed value, not also nulled by an over-broad
    fix."""
    snap = build_snapshot(REPO_ROOT, as_of="2026-07-31")

    ac_facts = [f for f in snap.facts if f.predicate == "acceptance_criterion"]
    assert ac_facts, "this repo's own spec.md files have real ACs to measure"
    assert not any(f.value.get("verified_pass") for f in ac_facts), (
        "A3: no verifies edge should be reachable via the legacy-filename-only "
        "artifact parser on a current-convention repo"
    )

    by_id = {m.metric_id: m for m in snap.metrics}

    trc_002 = by_id["TRC-002"]
    assert trc_002.value is None
    assert trc_002.n == len(ac_facts)  # n preserved, never dropped or zeroed
    assert trc_002.reason and not trc_002.reason[0].isdigit()  # word-first (AC-2.1/D7)
    assert "0 of" in trc_002.reason  # the real graph count is named, not hidden

    trc_004_unverified = by_id["TRC-004-unverified-acs"]
    assert trc_004_unverified.value is None
    assert trc_004_unverified.n == len(ac_facts)

    # The probe found this repo's own real .spark/*/qa.md files on disk —
    # the reason names that, turning "we can't measure this" into "here's
    # the file we failed to parse" (spec §1's own success signal).
    assert "matching artifact file" in trc_002.reason

    # The fix is scoped to the evidence-absent metrics only — every other
    # TRC entry, whose maps_to/implements evidence genuinely exists on this
    # repo's graph, still carries a real computed value.
    for metric_id in ("TRC-001", "TRC-003", "TRC-004-orphan-tasks"):
        metric = by_id[metric_id]
        assert metric.value is not None, f"{metric_id} should not be gated on this repo's real graph"

    artifact_probe = snap.provenance.artifact_probe
    assert artifact_probe["outcome"] == "present"
    assert artifact_probe["matched_file_count"] > 0


def test_zero_node_repo_reports_honest_null_not_a_fabricated_value(tmp_path: Path):
    """AC-7.2: a repo with a built-but-empty graph reports null+reason for every
    TRC-*, never a fabricated 0% or 100%."""
    from aspark_graph.graph import Graph

    Graph().save(tmp_path / ".aspark-graph" / "graph.json")

    snap = build_snapshot(tmp_path, as_of="2026-07-31")
    trc_entries = [m for m in snap.metrics if m.metric_id.startswith("TRC-")]
    assert trc_entries
    for m in trc_entries:
        assert m.value is None
        assert m.reason
        assert m.n == 0
