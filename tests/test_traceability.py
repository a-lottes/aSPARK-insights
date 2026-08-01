"""TRC-*/MTA-* metric definitions (metrics/traceability.py)."""

from __future__ import annotations

import pytest

from aspark_insights.metrics.registry import registry
from aspark_insights.model.fact import Fact, SubjectKind


def _story_fact(subject_id: str, *, mapped: bool) -> Fact:
    return Fact(SubjectKind.CODE_ARTIFACT, subject_id, "story", {"mapped": mapped})


def _ac_fact(subject_id: str, *, verified_pass: bool) -> Fact:
    return Fact(SubjectKind.CODE_ARTIFACT, subject_id, "acceptance_criterion", {"verified_pass": verified_pass})


def _task_fact(subject_id: str, *, mapped: bool, implements: bool) -> Fact:
    return Fact(SubjectKind.CODE_ARTIFACT, subject_id, "task", {"mapped": mapped, "implements": implements})


def test_trc_001_share_of_mapped_stories():
    from aspark_insights.metrics import traceability  # noqa: F401

    fn = registry.get("TRC-001", "1.0.0")
    facts = (
        _story_fact("story:f:US-1", mapped=True),
        _story_fact("story:f:US-2", mapped=True),
        _story_fact("story:f:US-3", mapped=False),
    )
    result = fn(facts, as_of="2026-07-29")
    assert result.value == 2 / 3
    assert result.n == 3
    assert result.reason is None


def test_trc_001_zero_stories_is_null_with_reason_not_zero_division():
    from aspark_insights.metrics import traceability  # noqa: F401

    fn = registry.get("TRC-001", "1.0.0")
    result = fn((), as_of="2026-07-29")
    assert result.value is None
    assert result.n == 0
    assert "no Story nodes found" in result.reason


def test_trc_001_ignores_non_story_facts():
    from aspark_insights.metrics import traceability  # noqa: F401

    fn = registry.get("TRC-001", "1.0.0")
    facts = (
        _story_fact("story:f:US-1", mapped=True),
        Fact(SubjectKind.CODE_ARTIFACT, "task:f:T1", "task", {"mapped": True, "implements": False}),
    )
    result = fn(facts, as_of="2026-07-29")
    assert result.value == 1.0
    assert result.n == 1


def test_trc_002_share_of_verified_pass_acs():
    from aspark_insights.metrics import traceability  # noqa: F401

    fn = registry.get("TRC-002", "1.0.0")
    facts = (
        _ac_fact("ac:f:AC-1.1", verified_pass=True),
        _ac_fact("ac:f:AC-1.2", verified_pass=False),
    )
    result = fn(facts, as_of="2026-07-29")
    assert result.value == 0.5
    assert result.n == 2


def test_trc_002_zero_acs_is_null_with_reason():
    from aspark_insights.metrics import traceability  # noqa: F401

    fn = registry.get("TRC-002", "1.0.0")
    result = fn((), as_of="2026-07-29")
    assert result.value is None
    assert result.n == 0
    assert "no AcceptanceCriterion nodes found" in result.reason


def test_trc_003_share_of_implementing_tasks():
    from aspark_insights.metrics import traceability  # noqa: F401

    fn = registry.get("TRC-003", "1.0.0")
    facts = (
        _task_fact("task:f:T1", mapped=True, implements=True),
        _task_fact("task:f:T2", mapped=True, implements=False),
        _task_fact("task:f:T3", mapped=False, implements=False),
    )
    result = fn(facts, as_of="2026-07-29")
    assert result.value == 1 / 3
    assert result.n == 3


def test_trc_003_zero_tasks_is_null_with_reason():
    from aspark_insights.metrics import traceability  # noqa: F401

    fn = registry.get("TRC-003", "1.0.0")
    result = fn((), as_of="2026-07-29")
    assert result.value is None
    assert result.n == 0
    assert "no Task nodes found" in result.reason


def test_trc_004_orphan_tasks_matches_gate_healths_definition():
    """Orphan = a Task with no outgoing maps_to — mirrors gate_health, never reads
    open_findings (A3's Finding-node filename mismatch is sidestepped entirely)."""
    from aspark_insights.metrics import traceability  # noqa: F401

    fn = registry.get("TRC-004-orphan-tasks", "1.0.0")
    facts = (
        _task_fact("task:f:T1", mapped=True, implements=True),
        _task_fact("task:f:T2", mapped=False, implements=True),  # orphan: not mapped
    )
    result = fn(facts, as_of="2026-07-29")
    assert result.value == 1
    assert result.n == 2


def test_trc_004_unverified_acs_matches_gate_healths_definition():
    from aspark_insights.metrics import traceability  # noqa: F401

    fn = registry.get("TRC-004-unverified-acs", "1.0.0")
    facts = (
        _ac_fact("ac:f:AC-1.1", verified_pass=True),
        _ac_fact("ac:f:AC-1.2", verified_pass=False),  # unverified
    )
    result = fn(facts, as_of="2026-07-29")
    assert result.value == 1
    assert result.n == 2


def test_trc_004_zero_denominator_for_both_entries():
    from aspark_insights.metrics import traceability  # noqa: F401

    orphan_fn = registry.get("TRC-004-orphan-tasks", "1.0.0")
    unverified_fn = registry.get("TRC-004-unverified-acs", "1.0.0")

    orphan_result = orphan_fn((), as_of="2026-07-29")
    assert orphan_result.value is None
    assert orphan_result.n == 0

    unverified_result = unverified_fn((), as_of="2026-07-29")
    assert unverified_result.value is None
    assert unverified_result.n == 0


def test_trc_004_is_two_distinct_entries_never_blended():
    from aspark_insights.metrics import traceability  # noqa: F401

    listing = registry.list()
    assert {"metric_id": "TRC-004-orphan-tasks", "metric_version": "1.0.0"} in listing
    assert {"metric_id": "TRC-004-unverified-acs", "metric_version": "1.0.0"} in listing
    assert not any(entry["metric_id"] == "TRC-004" for entry in listing)


def _story_fact_with_trace(subject_id: str, *, mapped: bool, confidence_tier: str | None) -> Fact:
    return Fact(
        SubjectKind.CODE_ARTIFACT, subject_id, "story",
        {"mapped": mapped, "confidence_tier": confidence_tier},
    )


def test_trc_005_reports_declared_extracted_inferred_shares_as_three_entries():
    from aspark_insights.metrics import traceability  # noqa: F401

    facts = (
        _story_fact_with_trace("story:f:US-1", mapped=True, confidence_tier="declared"),
        _story_fact_with_trace("story:f:US-2", mapped=True, confidence_tier="declared"),
        _story_fact_with_trace("story:f:US-3", mapped=True, confidence_tier="inferred"),
        _story_fact_with_trace("story:f:US-4", mapped=False, confidence_tier=None),  # no trace
    )
    declared = registry.get("TRC-005-declared", "1.0.0")(facts, as_of="2026-07-29")
    extracted = registry.get("TRC-005-extracted", "1.0.0")(facts, as_of="2026-07-29")
    inferred = registry.get("TRC-005-inferred", "1.0.0")(facts, as_of="2026-07-29")

    assert declared.value == 2 / 3
    assert declared.n == 3  # only Stories with a trace count toward n
    assert extracted.value == 0.0
    assert extracted.n == 3
    assert inferred.value == 1 / 3
    assert inferred.n == 3


def test_trc_005_zero_traced_stories_is_null_with_reason():
    from aspark_insights.metrics import traceability  # noqa: F401

    facts = (_story_fact_with_trace("story:f:US-1", mapped=False, confidence_tier=None),)
    for tier in ("declared", "extracted", "inferred"):
        result = registry.get(f"TRC-005-{tier}", "1.0.0")(facts, as_of="2026-07-29")
        assert result.value is None
        assert result.n == 0
        assert "no Story has a full trace" in result.reason


# --- MTA-001: every metric carries n, and null <=> n==0 (cross-metric) -------


def test_every_registered_metric_carries_n_and_is_null_at_n_zero():
    """MTA-001: no TRC-*/MTA-* entry ships without its own n; with zero matching
    facts every one honestly reports null+reason rather than a fabricated number."""
    from aspark_insights.metrics import traceability  # noqa: F401

    listing = [e for e in registry.list() if e["metric_id"].startswith("TRC-")]
    assert len(listing) >= 6  # TRC-001..003, both TRC-004 entries, all three TRC-005 tiers

    for entry in listing:
        fn = registry.get(entry["metric_id"], entry["metric_version"])
        result = fn((), as_of="2026-07-29")
        assert result.n == 0, entry
        assert result.value is None, entry
        assert result.reason, entry


# --- NFR-5: the shared registry is append-only -------------------------------


def test_shared_registry_refuses_to_re_register_a_shipped_id_and_version():
    from aspark_insights.metrics import traceability  # noqa: F401

    def _decoy(facts, *, as_of=None):
        raise AssertionError("should never be called")

    with pytest.raises(ValueError):
        registry.register("TRC-001", "1.0.0", _decoy)
