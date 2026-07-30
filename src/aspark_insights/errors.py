"""Named errors — every CLI failure exits 1 with one of these, never a raw traceback."""

from __future__ import annotations


class InsightsError(Exception):
    """Base for every named error the CLI can surface. Carries a machine-readable reason."""

    reason: str = "error"

    def __init__(self, message: str, *, reason: str | None = None) -> None:
        super().__init__(message)
        if reason is not None:
            self.reason = reason

    def to_dict(self) -> dict:
        return {"error": self.reason, "message": str(self)}


class GraphNotBuiltError(InsightsError):
    reason = "graph_not_built"


class GraphVersionMismatchError(InsightsError):
    reason = "graph_version_mismatch"


class PolicyUnavailable(InsightsError):
    """Not raised as a failure — used as a well-formed result value (AC-3.1)."""

    reason = "policy_unavailable"


class NotImplementedStub(InsightsError):
    reason = "not_implemented"


class VerifyMismatchError(InsightsError):
    reason = "verify_mismatch"


class SnapshotUnreadableError(InsightsError):
    """A snapshot path is missing, unreadable, or not valid JSON."""

    reason = "snapshot_unreadable"


class InvalidAsOfError(InsightsError):
    """`--as-of` is not a well-formed ISO-8601 date.

    Rejected here, before any filesystem path is built from it — `as_of` becomes
    the snapshot's filename (`store.snapshot_path`), so an unvalidated value is a
    path-traversal / arbitrary-write primitive, not just a cosmetic input check.
    """

    reason = "invalid_as_of"


class GraphUnreadableError(InsightsError):
    """The graph's own store exists but is malformed (bad JSON or bad shape)."""

    reason = "graph_unreadable"
