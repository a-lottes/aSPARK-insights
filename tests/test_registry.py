"""US-5: metric registry mechanism, shipping zero real metric definitions."""

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


def test_shipped_registry_is_empty():
    """No real metric definitions ship with this feature — that's I2's job."""
    assert registry.list() == []
