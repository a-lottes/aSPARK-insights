"""MetricValue — a metric result that structurally cannot lie about being honest.

A null value with no reason is not constructible (AC-4.2). This is the model-level
enforcement of the family's "MTTR stays null with a documented reason" precedent
(sibling repo's G2 decision) — the shape itself refuses a silent, unexplained gap.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricValue:
    metric_id: str
    metric_version: str
    value: float | int | None
    reason: str | None = None
    n: int | None = None  # MTA-001: the denominator this value was computed over

    def __post_init__(self) -> None:
        if self.value is None and not self.reason:
            raise ValueError(
                "MetricValue with value=None requires a non-empty reason "
                f"(metric_id={self.metric_id!r})"
            )
        if self.value is not None and self.reason is not None:
            raise ValueError(
                "MetricValue with a computed value must not also carry a reason "
                f"(metric_id={self.metric_id!r})"
            )

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "metric_version": self.metric_version,
            "value": self.value,
            "reason": self.reason,
            "n": self.n,
        }
