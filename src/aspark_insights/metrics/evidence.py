"""EvidenceKind / gate — the registry-wide null-on-absent-evidence rule (US-1).

A metric may compute a value from Facts whose underlying graph evidence kind
(a specific edge/node predicate) never actually got extracted — e.g. this
repo's own graph has zero `verifies` edges because the pinned graph tool's
artifact parser never recognizes this convention's `qa.md`/`review.md`
filenames (A1). `gate()` runs once per metric, after its function returns, and turns a
value computed from zero evidence into an honest null — never touching a
result the function already nulled for its own reason (AC-1.4: the
denominator-absent reason always wins).

A metric declares its evidence kind at `registry.register(...)`, not by
restating the check inside its own body (AC-1.6): a future metric inherits
the rule by declaring a kind, nothing more.

Known limitation, accepted rather than solved here: `QA_EVIDENCE`'s count is
"AC has an incoming `verifies` edge from a *passing* QACheck" (AC-1.1's own
literal definition), not "AC has any `verifies` edge regardless of result" —
so a graph with real QAChecks that all genuinely failed would also read as
"evidence absent" here. Distinguishing the two needs a Fact-level signal this
project's collector doesn't carry today (whether QA was *attempted*, not
just whether it *passed*). Not reachable by this repo's own dogfood graph
(zero `verifies` edges of any kind, A1) or by any current fixture; worth a
future spec question if a repo with genuinely all-failing QA is ever the
target, not a defect in this feature's own success signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from aspark_insights.artifact_probe import ArtifactProbeResult
from aspark_insights.model.fact import Fact
from aspark_insights.model.value import MetricValue


@dataclass(frozen=True, slots=True)
class EvidenceKind:
    """Declares which Fact-derived signal a metric's non-null value depends on."""

    graph_noun: str  # what's being counted, for the reason text
    graph_count: Callable[[tuple[Fact, ...]], int]  # count of the evidence kind across facts
    uses_disk_probe: bool = False  # whether the reason should also compose the probe's on-disk half


def _count_maps_to_evidence(facts: tuple[Fact, ...]) -> int:
    return sum(1 for f in facts if f.predicate == "task" and f.value.get("mapped"))


def _count_implements_evidence(facts: tuple[Fact, ...]) -> int:
    return sum(1 for f in facts if f.predicate == "task" and f.value.get("implements"))


def _count_qa_evidence(facts: tuple[Fact, ...]) -> int:
    return sum(
        1 for f in facts
        if f.predicate == "acceptance_criterion" and f.value.get("verified_pass")
    )


MAPS_TO_EVIDENCE = EvidenceKind(
    graph_noun="Task→Story maps_to edges", graph_count=_count_maps_to_evidence,
)
IMPLEMENTS_EVIDENCE = EvidenceKind(
    graph_noun="Task→File implements edges", graph_count=_count_implements_evidence,
)
QA_EVIDENCE = EvidenceKind(
    graph_noun="verifies-from-passing-QACheck edges", graph_count=_count_qa_evidence,
    uses_disk_probe=True,
)


def _compose_reason(kind: EvidenceKind, result: MetricValue, probe: ArtifactProbeResult | None) -> str:
    # Word-first (AC-2.1/D7): never starts with a digit — rendered into a
    # metrics-table Value column, where a leading "0" would read as the
    # metric's own value, the exact confusion this feature removes.
    graph_phrase = f"no {kind.graph_noun} found in the graph (0 of {result.n})"
    if not kind.uses_disk_probe:
        return graph_phrase
    if probe is None:
        # AC-2.3: the on-disk check was inconclusive because it never ran at
        # all — distinct from a probe that ran and returned "inconclusive".
        return f"{graph_phrase}; on-disk check inconclusive (probe did not run)"
    return f"{graph_phrase}; {probe.disk_phrase()}"


def gate(
    result: MetricValue,
    kind: EvidenceKind | None,
    facts: tuple[Fact, ...],
    probe: ArtifactProbeResult | None,
) -> MetricValue:
    """Overrides `result` to null+reason iff it's non-null but `kind`'s
    declared evidence has a repo-wide count of zero. A no-op when `kind` is
    None (the metric declares no evidence kind), when `result` is already
    null (AC-1.4: the denominator-absent reason always wins — this gate never
    competes with it), or when the evidence kind's count is nonzero
    (AC-1.3: byte-identical passthrough)."""
    if kind is None or result.value is None:
        return result
    if kind.graph_count(facts) > 0:
        return result
    return MetricValue(
        metric_id=result.metric_id,
        metric_version=result.metric_version,
        value=None,
        reason=_compose_reason(kind, result, probe),
        n=result.n,
    )
