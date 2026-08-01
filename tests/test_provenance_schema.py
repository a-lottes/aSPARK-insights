"""Provenance's new fields (scope_filter, graph_staleness) are always present."""

from __future__ import annotations

from aspark_insights.model.provenance import GraphSource, Provenance, ScopeFilterResult


def test_scope_filter_result_round_trips_even_when_empty():
    result = ScopeFilterResult(patterns=(), excluded_count=0)
    assert result.to_dict() == {"patterns": [], "excluded_count": 0}


def test_scope_filter_result_round_trips_with_exclusions():
    result = ScopeFilterResult(patterns=(".claude/worktrees/**",), excluded_count=7)
    assert result.to_dict() == {"patterns": [".claude/worktrees/**"], "excluded_count": 7}


def test_provenance_scope_filter_and_staleness_always_present_in_dict():
    prov = Provenance(
        as_of="2026-07-29",
        insights_version="0.2.0",
        metric_registry_version="0.2.0",
        graph_source=GraphSource(access="library-interim", sealed=True),
        policy_versions=None,
        scope_filter=ScopeFilterResult(patterns=(), excluded_count=0),
        graph_staleness=None,
    )
    d = prov.to_dict()
    assert "scope_filter" in d
    assert "graph_staleness" in d
    assert d["graph_staleness"] is None
