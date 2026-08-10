"""artifact_probe — a bounded, read-only presence check under `<repo>/.spark/`.

Not a second artifact parser (ADR-0, spec §6 of measurement-honesty): reads
**zero bytes** of file content, descends exactly one level, and answers only
"does a file matching the built-in filename set exist" — the one question a
graph-derived Fact structurally cannot answer (a missing `verifies` edge
never says whether that's because no `qa.md` exists or because one exists
but the pinned graph tool's parser never recognized its filename).

Never raises. Every failure mode — a missing `.spark/`, a `.spark` that is a
regular file or a symlink, an unreadable directory — resolves to a well-formed
`ArtifactProbeResult`, never a traceback (constitution §6, AC-3.1..3.3).
"""

from __future__ import annotations

import errno
import os
from dataclasses import dataclass
from pathlib import Path

# The two current aSPARK-convention artifact filenames a feature directory may
# hold. Built-in and fixed — no CLI flag, no config (spec §6: "no requester").
ARTIFACT_FILENAMES: tuple[str, ...] = ("qa.md", "review.md")

_SPARK_DIRNAME = ".spark"


@dataclass(frozen=True, slots=True)
class ArtifactProbeResult:
    """Counts and flags only — never an absolute path, home dir, username, or
    a filename outside `ARTIFACT_FILENAMES` (AC-3.6). `detail` is a curated,
    path-free category string, only set when `outcome == "inconclusive"`."""

    outcome: str  # "present" | "absent" | "inconclusive"
    matched_file_count: int
    matched_filenames: tuple[str, ...]  # subset of ARTIFACT_FILENAMES, sorted
    feature_dir_count: int
    detail: str | None = None

    def to_dict(self) -> dict:
        return {
            "outcome": self.outcome,
            "matched_file_count": self.matched_file_count,
            "matched_filenames": list(self.matched_filenames),
            "feature_dir_count": self.feature_dir_count,
            "detail": self.detail,
        }

    def disk_phrase(self) -> str:
        """The reason's on-disk half (AC-2.1/2.2/2.3) — three materially
        different strings depending on outcome, so a reader (and a test) can
        tell the cases apart."""
        if self.outcome == "inconclusive":
            return f"on-disk check inconclusive ({self.detail})"
        if self.matched_file_count == 0:
            return "no matching artifact files found under .spark/"
        names = ", ".join(self.matched_filenames)
        return f"{self.matched_file_count} matching artifact file(s) found under .spark/ ({names})"


def _os_error_category(exc: OSError) -> str:
    """A curated, path-free cause — never `str(exc)`, which routinely embeds
    the absolute path (AC-3.6, NFR-3). Named by errno class, not by message."""
    if exc.errno in (errno.EACCES, errno.EPERM):
        return "permission denied"
    if exc.errno == errno.ENOTDIR:
        return "not a directory"
    if exc.errno == errno.ENOENT:
        return "vanished during scan"
    return type(exc).__name__


def probe_artifacts(repo_root: str | Path) -> ArtifactProbeResult:
    """Presence-only check under `<repo_root>/.spark/<feature>/<filename>`.

    Descends exactly one level (AC-3.5), follows no symlink at any level
    (AC-3.2), reads zero bytes of file content (AC-3.4), and composes every
    path from `repo_root` plus the built-in filename set only (AC-3.7) — so a
    hostile `repo_root` (empty string, `../` traversal, an absolute path, a
    nonexistent path) never raises; it simply finds nothing.
    """
    spark_dir = Path(repo_root) / _SPARK_DIRNAME

    if not os.path.lexists(spark_dir):
        return ArtifactProbeResult("absent", 0, (), 0)
    if os.path.islink(spark_dir) or not os.path.isdir(spark_dir):
        # A `.spark` that is a regular file, or any kind of symlink (even one
        # that resolves to a real directory) — never followed (AC-3.2).
        return ArtifactProbeResult(
            "inconclusive", 0, (), 0,
            detail=".spark exists but is not a plain directory",
        )

    try:
        entries = sorted(os.scandir(spark_dir), key=lambda e: e.name)
    except OSError as exc:
        return ArtifactProbeResult(
            "inconclusive", 0, (), 0,
            detail=f"could not list .spark/: {_os_error_category(exc)}",
        )

    matched_count = 0
    matched_types: set[str] = set()
    feature_dir_count = 0
    inconclusive_detail: str | None = None

    for entry in entries:
        try:
            if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                continue  # not a plain feature directory — never descended into
        except OSError as exc:
            inconclusive_detail = inconclusive_detail or (
                f"could not stat a .spark/ entry: {_os_error_category(exc)}"
            )
            continue

        feature_dir_count += 1
        for name in ARTIFACT_FILENAMES:
            candidate = Path(entry.path) / name
            try:
                if os.path.islink(candidate):
                    continue  # never followed (AC-3.2), even one level down
                if os.path.isfile(candidate):
                    matched_count += 1
                    matched_types.add(name)
            except OSError as exc:
                inconclusive_detail = inconclusive_detail or (
                    f"could not check a feature directory: {_os_error_category(exc)}"
                )

    if inconclusive_detail is not None and matched_count == 0:
        return ArtifactProbeResult(
            "inconclusive", 0, (), feature_dir_count, detail=inconclusive_detail
        )

    matched_filenames = tuple(sorted(matched_types))
    outcome = "present" if matched_filenames else "absent"
    return ArtifactProbeResult(outcome, matched_count, matched_filenames, feature_dir_count)
