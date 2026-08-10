"""US-5: metric registry mechanism (foundation). Real TRC-*/MTA-* entries land

via `metrics/traceability.py` (traceability-metrics, I2) — see test_traceability.py
for those. This file tests the bare `MetricRegistry` mechanism in isolation.
"""

from __future__ import annotations

import pytest

from aspark_insights.metrics.registry import MetricRegistry, registry
from aspark_insights.model.fact import Fact, SubjectKind
from aspark_insights.model.value import MetricValue


def _test_only_metric(facts: tuple[Fact, ...], *, as_of: str | None = None) -> MetricValue:
    """A pure test-only function — exercises the mechanism, never a shipped KPI."""
    count = sum(1 for f in facts if f.predicate == "loc")
    return MetricValue(metric_id="TEST-001", metric_version="1.0.0", value=count)


def test_register_lookup_and_ordered_list():
    reg = MetricRegistry()
    reg.register("TEST-001", "1.0.0", _test_only_metric)
    reg.register("TEST-002", "1.0.0", _test_only_metric)

    fn = reg.get("TEST-001", "1.0.0")
    assert fn is _test_only_metric

    listing = reg.list()
    assert listing == [
        {"metric_id": "TEST-001", "metric_version": "1.0.0"},
        {"metric_id": "TEST-002", "metric_version": "1.0.0"},
    ]


def test_registering_the_same_id_and_version_twice_fails():
    reg = MetricRegistry()
    reg.register("TEST-001", "1.0.0", _test_only_metric)
    with pytest.raises(ValueError):
        reg.register("TEST-001", "1.0.0", _test_only_metric)


def test_registered_function_is_pure_and_invocable():
    reg = MetricRegistry()
    reg.register("TEST-001", "1.0.0", _test_only_metric)
    facts = (Fact(SubjectKind.CODE_ARTIFACT, "file:a.py", "loc", 10),)
    result = reg.get("TEST-001", "1.0.0")(facts, as_of="2026-07-29")
    assert result.value == 1


def test_shared_registry_registers_traceability_metrics_on_import():
    """The module-level `registry` singleton is populated by importing
    `metrics.traceability` — an explicit, grep-able `register()` call at import
    time (see that module's docstring), not decorator magic."""
    from aspark_insights.metrics import traceability  # noqa: F401

    listing = registry.list()
    assert {"metric_id": "TRC-001", "metric_version": "2.0.0"} in listing


# --- measurement-honesty: evidence_kind storage/lookup ----------------------


def test_register_without_evidence_kind_defaults_to_none():
    reg = MetricRegistry()
    reg.register("TEST-001", "1.0.0", _test_only_metric)
    assert reg.evidence_kind("TEST-001", "1.0.0") is None


def test_register_stores_and_exposes_its_evidence_kind():
    from aspark_insights.metrics.evidence import MAPS_TO_EVIDENCE

    reg = MetricRegistry()
    reg.register("TEST-001", "1.0.0", _test_only_metric, evidence_kind=MAPS_TO_EVIDENCE)
    assert reg.evidence_kind("TEST-001", "1.0.0") is MAPS_TO_EVIDENCE


def test_evidence_kind_for_unregistered_pair_is_none_not_a_crash():
    reg = MetricRegistry()
    assert reg.evidence_kind("NOPE", "9.9.9") is None
