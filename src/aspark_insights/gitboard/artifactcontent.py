"""artifactcontent — bounded, honest reads of a feature's own 5 artifact
document bodies (release-board-docs, US-2).

Kept separate from `artifactstatus.py` deliberately: that module's
docstring makes "no other section of the body is parsed, at all" a
load-bearing promise for `artifactstatus.py`'s own header-table-only
extraction, and `build_release_map` must keep that exact behavior
unchanged (CLAUDE.md's "don't over-generalize a fix onto callers that
never asked for it"). This module (the *full* 5-artifact document body)
only ever runs on the `--format html` branch, never on the JSON path —
`build_release_map()` never imports it. Review F9: as of release-metrics,
`build_release_map()`'s JSON path does read one narrow slice of one body
— `gitboard/scopecount.py` counts `spec.md`'s own `### US-N`/`- [ ] AC-`
lines for the delivered-scope figures — a separate, deliberate, plan-
recorded exception to the header-table-only promise above, not this
module's own reuse of it.
"""

from __future__ import annotations

from pathlib import Path

_SPARK_DIRNAME = ".spark"
_ARTIFACT_NAMES = ("spec", "plan", "review", "qa", "release")

# T4/A5: per-document bound — 1,200 lines or 200 KB, whichever trips first
# (2x today's largest real document, `measurement-honesty/spec.md` at 597
# lines, per plan.md §1's own measured survey).
_MAX_DOCUMENT_LINES = 1200
_MAX_DOCUMENT_BYTES = 200_000

# Defense against a truly pathological file (not a realistic project
# artifact): above this, don't even attempt to read/decode the whole file
# just to report an honest total line count — disclose size only. Well
# above `_MAX_DOCUMENT_BYTES` so every real artifact in this repo (largest
# today: 597 lines, ~20 KB) is read in full for an honest total-line count.
_SANITY_READ_CEILING_BYTES = 10_000_000


def _failure(reason: str) -> dict:
    return {
        "text": "", "total_lines": 0, "shown_lines": 0, "total_bytes": 0,
        "truncated": False, "byte_truncated": False, "line_truncated": False,
        "empty": False, "reason": reason,
    }


def _is_valid_feature_name(name: str) -> bool:
    """T6/NFR-2: independently re-validated here, even though
    `releasemap._is_valid_feature_name` already validated every name that
    reaches this collector — a deliberate second check at this module's own
    I/O boundary (defense in depth for a new path-building surface), not a
    shared function reused across modules, so a bug in one validator can't
    silently disable the other."""
    return bool(name) and "/" not in name and ".." not in name and not name.startswith("-")


def read_artifact_document(
    path: Path, *, max_lines: int = _MAX_DOCUMENT_LINES, max_bytes: int = _MAX_DOCUMENT_BYTES,
    allowed_root: Path | None = None,
) -> dict:
    """Never raises (T3/AC-2.2/2.3) — degrades to an honest `reason`,
    mirroring `artifactstatus.py`'s own contract. Bounded (T4/AC-2.5): the
    returned `text` never exceeds `max_lines`/`max_bytes`; `total_lines`/
    `total_bytes` report the file's real, full size so a truncation
    disclosure is honest about what was left out, not just what was kept.

    Review F1 (Blocker): `path.is_file()`/`read_bytes()` alone follow a
    symlink anywhere a filesystem grants read access — a `.spark/<feature>/
    spec.md` symlinked outside the repo would otherwise be read and
    embedded verbatim into a page this project's own README calls
    self-contained and shareable. When `allowed_root` is given, the
    resolved path must be contained within it (mirrors
    `releasemap._list_feature_dirs`'s own resolve-and-contain check for
    the *directory* — this is the same guard for the *file*, the gap T6
    named and had not actually implemented).

    Returns `{"text", "total_lines", "shown_lines", "total_bytes",
    "truncated", "empty", "reason"}`. `reason` is set only for a hard
    failure (not found / unreadable / undecodable / too large to attempt /
    escapes `allowed_root`); a truncated-but-successful read has
    `reason: None`.
    """
    if allowed_root is not None:
        try:
            resolved = path.resolve()
            resolved_root = allowed_root.resolve()
        # Re-review: `ValueError` too, not just `OSError` — `Path.resolve()`
        # raises `ValueError("embedded null character in path")`, not an
        # `OSError`, for a name containing NUL, which escaped the "Never
        # raises" contract entirely.
        except (OSError, ValueError) as exc:
            return _failure(f"could not resolve path: {exc}")
        if not resolved.is_relative_to(resolved_root):
            return _failure("document path escapes .spark/")

    # Re-review: `Path.is_file()` swallows most `OSError`s but *not*
    # `ENAMETOOLONG` (a >255-byte name) and not the NUL `ValueError` on the
    # `allowed_root=None` seam — both reached the caller as a raw traceback,
    # against this function's own "Never raises" contract.
    try:
        exists = path.is_file()
    except (OSError, ValueError) as exc:
        return _failure(f"could not stat file: {exc}")
    if not exists:
        return _failure("file not found")
    try:
        total_bytes = path.stat().st_size
    except OSError as exc:
        return _failure(f"could not stat file: {exc}")

    if total_bytes == 0:
        return {
            "text": "", "total_lines": 0, "shown_lines": 0, "total_bytes": 0,
            "truncated": False, "byte_truncated": False, "line_truncated": False,
            "empty": True, "reason": None,
        }
    if total_bytes > _SANITY_READ_CEILING_BYTES:
        return _failure(
            f"document too large to read ({total_bytes} bytes exceeds the "
            f"{_SANITY_READ_CEILING_BYTES}-byte safety ceiling)"
        )

    try:
        raw = path.read_bytes()
    except OSError as exc:
        return _failure(f"could not read file: {exc}")
    try:
        full_text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return _failure(f"could not decode file as UTF-8: {exc}")

    total_lines = len(full_text.split("\n"))

    byte_truncated = len(raw) > max_bytes
    if byte_truncated:
        # Re-decode only the kept prefix; a multi-byte UTF-8 character split
        # by the byte cut is dropped rather than raised on (`errors="ignore"`)
        # — a truncation boundary, not a real encoding failure.
        text = raw[:max_bytes].decode("utf-8", errors="ignore")
        lines = text.split("\n")
        if len(lines) > 1:
            lines = lines[:-1]  # drop a possibly-partial trailing line
    else:
        text = full_text
        lines = text.split("\n")

    line_truncated = len(lines) > max_lines
    if line_truncated:
        lines = lines[:max_lines]

    shown_text = "\n".join(lines)
    return {
        "text": shown_text,
        "total_lines": total_lines,
        "shown_lines": len(lines),
        "total_bytes": total_bytes,
        "truncated": byte_truncated or line_truncated,
        # Review F6: kept separate (not just OR'd into `truncated`) so the
        # rendering layer can state which cap(s) actually tripped — a
        # 300KB first line followed by short lines trips the byte cap
        # while `shown_lines < total_lines` only by 1 (the dropped partial
        # line), and "showing the first 1 of 12 lines" alone would wrongly
        # imply that one shown line is complete.
        "byte_truncated": byte_truncated,
        "line_truncated": line_truncated,
        "empty": False,
        "reason": None,
    }


def collect_release_documents(
    repo_root: str, data: dict, *, max_lines: int = _MAX_DOCUMENT_LINES, max_bytes: int = _MAX_DOCUMENT_BYTES,
) -> dict[str, dict[str, dict]]:
    """Reads every distinct member feature's 5 artifact documents exactly
    once — feature names are deduplicated naturally by dict key, since the
    same feature can be a member of more than one release (symmetric to
    `release-board`'s own AC-1.2: "a release can span more than one
    feature... real, not a bug"). *Which* release's card actually embeds a
    given feature's documents inline (display-order dedup, the page-weight
    budget) is the renderer's own decision — this collector only answers
    "what does the file say," bounded per document. Genuinely never raises
    (review F8): a malformed `data` shape (a non-list `releases`, a
    non-dict release/member, a missing `name`) is skipped rather than
    indexed into blindly — an unreadable `.spark/` degrades the same way
    each individual document read already does (AC-2.2), never a CLI
    failure."""
    feature_names: set[str] = set()
    # Re-review: `isinstance(..., list)`, not `or []` — a *truthy* non-list
    # (`{"releases": 42}`) sailed past the falsy-default and raised
    # `TypeError: 'int' object is not iterable`, which is exactly the
    # "non-list `releases`" case the docstring above already claimed to skip.
    releases = data.get("releases")
    for release in releases if isinstance(releases, list) else []:
        if not isinstance(release, dict):
            continue
        members = release.get("members")
        for member in members if isinstance(members, list) else []:
            if not isinstance(member, dict):
                continue
            name = member.get("name")
            if isinstance(name, str):
                feature_names.add(name)

    spark_root = Path(repo_root) / _SPARK_DIRNAME
    documents: dict[str, dict[str, dict]] = {}
    for name in sorted(feature_names):  # deterministic order (NFR-6)
        if not _is_valid_feature_name(name):
            continue  # T6: never build a path from an unvalidated name
        feature_dir = spark_root / name
        documents[name] = {
            artifact: read_artifact_document(
                feature_dir / f"{artifact}.md", max_lines=max_lines, max_bytes=max_bytes,
                allowed_root=spark_root,
            )
            for artifact in _ARTIFACT_NAMES
        }
    return documents
