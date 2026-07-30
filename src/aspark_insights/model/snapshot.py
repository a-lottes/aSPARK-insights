"""Snapshot — a sealed, self-documenting build output (AC-4.3, AC-4.4)."""

from __future__ import annotations

from dataclasses import dataclass

from .fact import Fact
from .provenance import Provenance
from .value import MetricValue


@dataclass(frozen=True, slots=True)
class Snapshot:
    facts: tuple[Fact, ...]
    metrics: tuple[MetricValue, ...]
    provenance: Provenance

    @classmethod
    def seal(
        cls,
        *,
        facts: list[Fact] | tuple[Fact, ...],
        metrics: list[MetricValue] | tuple[MetricValue, ...],
        provenance: Provenance,
    ) -> "Snapshot":
        return cls(facts=tuple(facts), metrics=tuple(metrics), provenance=provenance)

    def to_dict(self) -> dict:
        return {
            "facts": [f.to_dict() for f in self.facts],
            "metrics": [m.to_dict() for m in self.metrics],
            "provenance": self.provenance.to_dict(),
        }
