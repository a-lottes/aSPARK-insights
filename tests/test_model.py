"""US-4: core model with structural guardrails (AC-4.1, AC-4.2, AC-4.3)."""

from __future__ import annotations

import pytest

from aspark_insights.model.fact import Fact, SubjectKind
from aspark_insights.model.provenance import GraphSource, Provenance, ScopeFilterResult
from aspark_insights.model.snapshot import Snapshot
from aspark_insights.model.value import MetricValue


def test_subject_kind_has_no_person_level_member():
    names = {member.name for member in SubjectKind}
    values = {member.value for member in SubjectKind}
    assert names == {"SYSTEM", "FEATURE", "CODE_ARTIFACT"}
    for forbidden in ("person", "author", "assignee", "developer", "committer", "user"):
        assert forbidden not in values


def test_fact_round_trips_to_dict():
    fact = Fact(SubjectKind.CODE_ARTIFACT, "file:src/foo.py", "loc", 42)
    assert fact.to_dict() == {
        "subject_kind": "code_artifact",
        "subject_id": "file:src/foo.py",
        "predicate": "loc",
        "value": 42,
    }


def test_metric_value_null_without_reason_is_not_constructible():
    with pytest.raises(ValueError):
        MetricValue(metric_id="MTTR-001", metric_version="1.0.0", value=None)


def test_metric_value_null_with_reason_is_fine():
    mv = MetricValue(metric_id="MTTR-001", metric_version="1.0.0", value=None, reason="no incident data")
    assert mv.value is None
    assert mv.reason == "no incident data"


def test_metric_value_present_forbids_a_reason():
    with pytest.raises(ValueError):
        MetricValue(metric_id="TRC-001", metric_version="1.0.0", value=0.5, reason="shouldn't be here")


def test_metric_value_present_without_reason_is_fine():
    mv = MetricValue(metric_id="TRC-001", metric_version="1.0.0", value=0.5)
    assert mv.value == 0.5
    assert mv.reason is None


def _provenance(**overrides) -> Provenance:
    defaults = dict(
        as_of="2026-07-29",
        insights_version="0.1.0",
        metric_registry_version="0.1.0",
        graph_source=GraphSource(access="library-interim", sealed=True),
        policy_versions=None,
        scope_filter=ScopeFilterResult(patterns=(), excluded_count=0),
        graph_staleness=None,
    )
    defaults.update(overrides)
    return Provenance(**defaults)


def test_provenance_requires_every_field_as_an_input():
    prov = _provenance()
    assert prov.as_of == "2026-07-29"
    assert prov.policy_versions is None
    assert prov.to_dict()["graph_source"] == {"access": "library-interim", "sealed": True}
    assert prov.to_dict()["scope_filter"] == {"patterns": [], "excluded_count": 0}
    assert prov.to_dict()["graph_staleness"] is None


def test_metric_value_carries_its_own_n():
    mv = MetricValue(metric_id="TRC-001", metric_version="1.0.0", value=0.5, n=4)
    assert mv.n == 4
    assert mv.to_dict()["n"] == 4


def test_snapshot_seal_composes_and_serializes():
    fact = Fact(SubjectKind.SYSTEM, "system:aspark-insights", "exists", True)
    metric = MetricValue(metric_id="TRC-001", metric_version="1.0.0", value=None, reason="no metrics yet")
    snap = Snapshot.seal(facts=[fact], metrics=[metric], provenance=_provenance())
    d = snap.to_dict()
    assert d["facts"] == [fact.to_dict()]
    assert d["metrics"] == [metric.to_dict()]
    assert d["provenance"]["as_of"] == "2026-07-29"
