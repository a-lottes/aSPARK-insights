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


class GitUnavailableError(InsightsError):
    """`git` itself is unusable — not installed, not on PATH, timed out, or an
    unexpected nonzero exit at a call site that assumed a valid repo. Distinct
    from `NotAGitRepoError`: this is about the tool, not the target directory.
    """

    reason = "git_unavailable"


class NotAGitRepoError(InsightsError):
    """`--repo` is not a git working tree or bare repo — empty string, `../`
    traversal, an absolute path to a non-repo, or a directory with a corrupt
    `.git`. `git rev-parse --git-dir`'s own nonzero exit is the sole authority
    for this; never hand-parsed."""

    reason = "not_a_git_repo"


class BoardUnreadableError(InsightsError):
    """A board dict passed to the git-board HTML renderer has an unexpected
    shape — mirrors `SnapshotUnreadableError`'s "never a raw traceback on
    malformed input" guarantee for this feature's own data shape."""

    reason = "board_unreadable"


class SparkDirUnreadableError(InsightsError):
    """`.spark/` exists but could not be listed or read — e.g. a filesystem
    permission error (review F1). Distinct from a missing `.spark/`, which
    is not an error at all (`releasemap._list_feature_dirs` returns an
    empty list), and distinct from `GitUnavailableError` — this is a
    filesystem access failure, not a git one."""

    reason = "spark_dir_unreadable"


class ReleaseMapUnreadableError(InsightsError):
    """A `build_release_map()` dict passed to the release-board HTML
    renderer has an unexpected shape — the exact mirror of
    `BoardUnreadableError`, itself introduced for `report.py`'s identical
    render-shape guard (release-board-html plan.md §2)."""

    reason = "release_map_unreadable"


class ReportUnwritableError(InsightsError):
    """`--output`'s resolved report path could not be created or written —
    e.g. a path component that is already a regular file, or a permission
    error. Distinct from `ReleaseMapUnreadableError`/`BoardUnreadableError`
    (a data-shape problem): this is a filesystem write failure on an
    otherwise-valid render (review F1)."""

    reason = "report_unwritable"
