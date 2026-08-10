"""metrics/evidence.py (US-1/US-2): the registry-wide null-on-absent-evidence
gate, plus the reason-composition/version-bump guarantees (T3).
"""

from __future__ import annotations

from aspark_insights.artifact_probe import ArtifactProbeResult
from aspark_insights.metrics.evidence import (
    IMPLEMENTS_EVIDENCE,
    MAPS_TO_EVIDENCE,
    QA_EVIDENCE,
    gate,
)
from aspark_insights.metrics.registry import registry
from aspark_insights.model.fact import Fact, SubjectKind
from aspark_insights.model.value import MetricValue

_ABSENT_PROBE = ArtifactProbeResult("absent", 0, (), 0)
_PRESENT_PROBE = ArtifactProbeResult("present", 4, ("qa.md", "review.md"), 3)
_INCONCLUSIVE_PROBE = ArtifactProbeResult(
    "inconclusive", 0, (), 0, detail="could not list .spark/: permission denied",
)


def _task_fact(mapped: bool, implements: bool) -> Fact:
    return Fact(SubjectKind.CODE_ARTIFACT, "task:f:T1", "task", {"mapped": mapped, "implements": implements})


def _ac_fact(verified_pass: bool) -> Fact:
    return Fact(SubjectKind.CODE_ARTIFACT, "ac:f:AC-1", "acceptance_criterion", {"verified_pass": verified_pass})


# --- AC-1.4: a metric that already nulled for its own reason is a no-op ----


def test_gate_is_a_no_op_when_result_already_null_denominator_absent():
    already_null = MetricValue(metric_id="TRC-001", metric_version="2.0.0", value=None, reason="no Story nodes found in graph", n=0)
    result = gate(already_null, MAPS_TO_EVIDENCE, (), _ABSENT_PROBE)
    assert result is already_null  # untouched, not even reconstructed


def test_gate_is_a_no_op_when_kind_is_none():
    computed = MetricValue(metric_id="TRC-005-declared", metric_version="1.0.0", value=0.5, n=4)
    result = gate(computed, None, (), _ABSENT_PROBE)
    assert result is computed


# --- AC-1.2: overrides a non-null result when the evidence kind is absent --


def test_gate_overrides_to_null_when_evidence_absent():
    computed = MetricValue(metric_id="TRC-002", metric_version="2.0.0", value=0.0, n=41)
    facts = (_ac_fact(verified_pass=False),) * 41  # no verified_pass=True anywhere
    result = gate(computed, QA_EVIDENCE, facts, _ABSENT_PROBE)
    assert result.value is None
    assert result.n == 41  # n is preserved, never dropped
    assert result.reason
    assert not result.reason[0].isdigit()  # AC-2.1/D7: word-first


def test_gate_preserves_metric_id_and_version_on_override():
    computed = MetricValue(metric_id="TRC-004-unverified-acs", metric_version="2.0.0", value=41, n=41)
    facts = (_ac_fact(verified_pass=False),) * 41
    result = gate(computed, QA_EVIDENCE, facts, _ABSENT_PROBE)
    assert result.metric_id == "TRC-004-unverified-acs"
    assert result.metric_version == "2.0.0"


# --- AC-1.3: byte-identical passthrough when evidence is present -----------


def test_gate_passes_through_unchanged_when_evidence_present():
    computed = MetricValue(metric_id="TRC-002", metric_version="2.0.0", value=0.5, n=2)
    facts = (_ac_fact(verified_pass=True), _ac_fact(verified_pass=False))
    result = gate(computed, QA_EVIDENCE, facts, _PRESENT_PROBE)
    assert result is computed


# --- AC-2.1/2.2/2.3: three materially different reason strings -------------


def test_reason_present_probe_names_both_counts():
    computed = MetricValue(metric_id="TRC-002", metric_version="2.0.0", value=0.0, n=41)
    facts = (_ac_fact(verified_pass=False),) * 41
    result = gate(computed, QA_EVIDENCE, facts, _PRESENT_PROBE)
    assert "0 of 41" in result.reason
    assert "qa.md" in result.reason and "review.md" in result.reason


def test_reason_absent_probe_says_no_matching_files():
    computed = MetricValue(metric_id="TRC-002", metric_version="2.0.0", value=0.0, n=41)
    facts = (_ac_fact(verified_pass=False),) * 41
    result = gate(computed, QA_EVIDENCE, facts, _ABSENT_PROBE)
    assert "no matching artifact files found under .spark/" in result.reason


def test_reason_inconclusive_probe_says_so_and_names_the_cause():
    computed = MetricValue(metric_id="TRC-002", metric_version="2.0.0", value=0.0, n=41)
    facts = (_ac_fact(verified_pass=False),) * 41
    result = gate(computed, QA_EVIDENCE, facts, _INCONCLUSIVE_PROBE)
    assert "inconclusive" in result.reason
    assert "permission denied" in result.reason


def test_three_reason_strings_are_materially_different():
    computed = MetricValue(metric_id="TRC-002", metric_version="2.0.0", value=0.0, n=41)
    facts = (_ac_fact(verified_pass=False),) * 41
    reasons = {
        gate(computed, QA_EVIDENCE, facts, probe).reason
        for probe in (_ABSENT_PROBE, _PRESENT_PROBE, _INCONCLUSIVE_PROBE)
    }
    assert len(reasons) == 3


def test_non_disk_backed_kind_never_mentions_the_probe():
    computed = MetricValue(metric_id="TRC-003", metric_version="2.0.0", value=0.0, n=8)
    facts = (_task_fact(mapped=True, implements=False),) * 8
    result = gate(computed, IMPLEMENTS_EVIDENCE, facts, _PRESENT_PROBE)
    assert "qa.md" not in result.reason
    assert ".spark" not in result.reason


# --- AC-2.4: never asserts the sibling's parser internals as fact ----------


def test_reason_never_names_a_sibling_version_or_unprobed_filename():
    computed = MetricValue(metric_id="TRC-002", metric_version="2.0.0", value=0.0, n=41)
    facts = (_ac_fact(verified_pass=False),) * 41
    for probe in (_ABSENT_PROBE, _PRESENT_PROBE, _INCONCLUSIVE_PROBE):
        reason = gate(computed, QA_EVIDENCE, facts, probe).reason
        assert "aspark-graph" not in reason
        assert "0.7.0" not in reason
        assert "review-report.md" not in reason  # the legacy filename the probe never looks for


# --- Invariant the caveat trigger depends on (build.py's own guard) --------


def test_gate_is_the_only_producer_of_null_with_truthy_n_among_these_cases():
    """Documents the invariant `build.py` enforces separately: a metric
    function's own return must never be null-with-truthy-n — only gate()
    may produce that shape (render's caveat trigger is exactly `value is
    None and n`)."""
    computed = MetricValue(metric_id="TRC-001", metric_version="2.0.0", value=0.5, n=4)
    facts = (_task_fact(mapped=False, implements=False),) * 4  # zero maps_to evidence
    result = gate(computed, MAPS_TO_EVIDENCE, facts, _ABSENT_PROBE)
    assert result.value is None and result.n


# --- AC-1.6: a new metric inherits the rule by declaring a kind, no restate -


def test_a_throwaway_metric_inherits_the_rule_via_evidence_kind():
    def _decoy_fn(facts, *, as_of=None):
        return MetricValue(metric_id="ZZZ-001", metric_version="1.0.0", value=1, n=5)

    reg_backup = dict(registry._entries)
    kind_backup = dict(registry._evidence_kinds)
    try:
        registry.register("ZZZ-001", "1.0.0", _decoy_fn, evidence_kind=MAPS_TO_EVIDENCE)
        fn = registry.get("ZZZ-001", "1.0.0")
        kind = registry.evidence_kind("ZZZ-001", "1.0.0")
        raw = fn((), as_of="2026-07-29")
        result = gate(raw, kind, (), _ABSENT_PROBE)
        assert result.value is None
        assert "Task→Story maps_to edges" in result.reason
    finally:
        registry._entries = reg_backup
        registry._evidence_kinds = kind_backup
