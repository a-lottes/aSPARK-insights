"""releasemap — shared core: every git tag (topology-ordered) plus one
trailing open-window pseudo-release, mapped to the `.spark/<feature>/`
directories and unattributed commits in range, plus each feature's own
artifact status (US-1/US-2/US-3).

The pseudo-release's own git-derived figures are never a second
implementation of "commits since the latest tag" (AC-1.8/ADR-0) — they are
`gitboard.board.build_board()`'s own result, reused verbatim. Imports no
sibling graph tool's port or library — standalone the same way
`gitboard/board.py` already is (US-1's own no-graph proof extends here).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aspark_insights import __version__ as INSIGHTS_VERSION
from aspark_insights.errors import GitUnavailableError, InvalidAsOfError, SparkDirUnreadableError
from aspark_insights.gitboard import gitread
from aspark_insights.gitboard.artifactstatus import read_artifact_status
from aspark_insights.gitboard.board import build_board

_SPARK_DIRNAME = ".spark"
_ARTIFACT_NAMES = ("spec", "plan", "review", "qa", "release")


def _validate_as_of(as_of: str) -> None:
    """A parse of a caller-supplied string, not a clock read (ADR-4) — the
    same validation `board.build_board` applies to its own `--as-of`."""
    try:
        datetime.strptime(as_of, "%Y-%m-%d")
    except ValueError as exc:
        raise InvalidAsOfError(
            f"--as-of must be an ISO-8601 date (YYYY-MM-DD), got {as_of!r}"
        ) from exc


def _is_valid_feature_name(name: str) -> bool:
    """NFR-2: every `.spark/` entry name is an untrusted path component —
    rejects anything that could be misread as a git pathspec flag or a
    traversal segment, whether the name came from the filesystem or from
    git's own tracked-path history."""
    return not ("/" in name or ".." in name or name.startswith("-"))


def _list_feature_dirs(repo_root: str) -> list[str]:
    """Every valid `.spark/<feature-name>/` directory name **currently on
    disk**, sorted for determinism (NFR-7) — never the raw `iterdir()`
    order, which is filesystem-dependent. An entry is silently excluded,
    never erred on, if its name fails `_is_valid_feature_name`, if it is
    not a real directory, or if its resolved path escapes `<repo>/.spark/`
    (a symlink pointing outside the repo). This is only ever a *subset* of
    the full candidate set `_all_feature_names` builds — a directory
    renamed, deleted, or absent from the current checkout is invisible
    here by construction (QA B1), which is exactly why `_all_feature_names`
    also consults git history rather than using this alone."""
    spark_dir = Path(repo_root) / _SPARK_DIRNAME
    if not spark_dir.is_dir():
        return []
    spark_root = spark_dir.resolve()

    names = []
    for entry in spark_dir.iterdir():
        name = entry.name
        if not _is_valid_feature_name(name):
            continue
        if not entry.is_dir():
            continue
        try:
            resolved = entry.resolve()
        except OSError:
            continue
        if resolved.parent != spark_root:
            continue
        names.append(name)
    return sorted(names)


def _all_feature_names(repo_root: str) -> list[str]:
    """QA B1's fix: the exhaustive candidate feature-name set — the union
    of every name currently on disk (`_list_feature_dirs`) and every name
    ever touched by a commit reachable from any ref
    (`gitread.list_ever_touched_spark_feature_names`), each individually
    name-validated (NFR-2). `git log <range> -- .spark/<name>/` (already
    used for membership, A7) scores historical existence correctly on its
    own; the only thing that was working-tree-scoped was this candidate
    list. A history-only name simply has no artifact files to read on disk
    right now — `_member_entries`/`read_artifact_status` already degrade
    that honestly to `"file not found"` per artifact, the same shape any
    missing artifact file already reports (AC-2.2), not a new failure
    mode."""
    from_disk = set(_list_feature_dirs(repo_root))
    from_history = {
        name for name in gitread.list_ever_touched_spark_feature_names(repo_root)
        if _is_valid_feature_name(name)
    }
    return sorted(from_disk | from_history)


def _members_and_unattributed(
    repo_root: str, range_spec: str, feature_dirs: list[str]
) -> tuple[list[str], list[dict]]:
    """A7: membership is decided **only** by changed paths in `range_spec`,
    never by matching a commit's subject text against a directory name —
    this repo's own `26e7f95` ("snapshot-report scorecard redesign") names
    a directory in prose while touching zero files under it, which is
    exactly the trap path-only attribution avoids. `unattributed` is every
    commit in range that touched no validated feature directory (A7) — never
    dropped, never guessed onto the nearest feature."""
    all_commits = gitread.list_commits_in_range(repo_root, range_spec)
    touched_by_any: set[str] = set()
    members = []
    for name in feature_dirs:
        pathspec = f"{_SPARK_DIRNAME}/{name}/"
        hashes = gitread.commits_touching_path(repo_root, range_spec, pathspec)
        if hashes:
            members.append(name)
            touched_by_any |= hashes
    unattributed = [
        {"hash": c["hash"], "subject": c["subject"]}
        for c in all_commits
        if c["hash"] not in touched_by_any
    ]
    return members, unattributed


def _member_entries(repo_root: str, member_names: list[str]) -> list[dict]:
    """Each member's own `spec`/`plan`/`review`/`qa`/`release` status map
    (US-2), read via `.spark/<feature-name>/<artifact>.md` paths built from
    an already-validated name (`_list_feature_dirs` rejected any hostile
    name before it could reach here — NFR-2, no second validation needed)."""
    entries = []
    for name in member_names:
        feature_dir = Path(repo_root) / _SPARK_DIRNAME / name
        status = {
            artifact: read_artifact_status(feature_dir / f"{artifact}.md")
            for artifact in _ARTIFACT_NAMES
        }
        entries.append({"name": name, "status": status})
    return entries


def _pseudo_release(repo_root: str, as_of: str, feature_dirs: list[str]) -> dict | None:
    """AC-1.8: the pseudo-release's own git-derived figures are never
    recomputed — they are `board.build_board()`'s own result, copied through
    unchanged (same conditional key presence `build_board` itself uses, so a
    byte-equality check against a live `build_board` call holds exactly).
    AC-1.9: absent entirely (`None`, no entry appended) when `build_board`
    resolves no tag at all — "since the latest tag" has no referent without
    one, and AC-1.4 already explains the whole no-tags case once. Present
    (possibly a real, honest zero — never a null card) whenever a tag *is*
    resolved, using the identical `<tag>..HEAD` range `build_board` itself
    counted over for `commits`/`days_since_tag`/`work_types`."""
    board = build_board(repo_root, as_of)
    latest_tag = board["provenance"]["resolved_tag"]
    if latest_tag is None:
        return None

    range_spec = f"{latest_tag}..HEAD"
    members, unattributed = _members_and_unattributed(repo_root, range_spec, feature_dirs)

    pseudo = {
        "tag": None,
        # F3 (review): sourced from `build_board`'s own resolved tag — the
        # exact tag the figures above were computed against — never from
        # `releasemap`'s separately topo-ordered tag list, which could name
        # a different (unreachable/non-linear) tag than the one `git
        # describe` actually resolved.
        "previous_tag": latest_tag,
        "next_tag": None,
        "members": _member_entries(repo_root, members),
        "unattributed": unattributed,
        "commits": board["commits"],
        "branches": board["branches"],
    }
    if "days_since_tag" in board:
        pseudo["days_since_tag"] = board["days_since_tag"]
    if "work_types" in board:
        pseudo["work_types"] = board["work_types"]
    return pseudo


def build_release_map(repo_root: str, as_of: str) -> dict:
    """The one read: validates `as_of`, confirms `repo_root` is a real git
    repo (raises `NotAGitRepoError` otherwise, mirroring `board.build_board`),
    then walks every tag oldest-first (AC-1.1), computing each one's
    `<previous-tag>..<tag>` range (bare `<tag>` for the earliest one — A6)
    and its member/unattributed split (A7/A8/A9: a release may span several
    feature directories, and a feature's own trailing commit may land inside
    the *next* release's range — both are real, disclosed as such, never
    filtered). Zero tags is an honest empty list with a reason, exit 0
    (AC-1.4), never a failure. Any *unexpected* failure past that point is
    the final safety net into a named error — never a raw traceback
    (constitution §6; review F1): an unexpected git failure (`ValueError`
    from a malformed exit-0 result, same discipline as `board.build_board`)
    becomes `GitUnavailableError`; an unreadable `.spark/` (e.g. a
    filesystem permission error) becomes `SparkDirUnreadableError` — a
    different failure class, named as such rather than folded into the
    git-specific error."""
    _validate_as_of(as_of)
    gitread.ensure_git_repo(repo_root)

    try:
        tags = gitread.list_tags_topo_order(repo_root)
        # QA B1: the *exhaustive* candidate set (current checkout + every
        # name ever touched by history on any ref), not just what's on disk
        # right now — see _all_feature_names.
        feature_dirs = _all_feature_names(repo_root)

        releases = []
        previous_tag: str | None = None
        for t in tags:
            tag = t["tag"]
            range_spec = f"{previous_tag}..{tag}" if previous_tag else tag
            members, unattributed = _members_and_unattributed(repo_root, range_spec, feature_dirs)
            releases.append({
                "tag": tag,
                "members": _member_entries(repo_root, members),
                "unattributed": unattributed,
            })
            previous_tag = tag

        # AC-3.1: previous_tag/next_tag chain real releases only (null at
        # either end); the pseudo-release is never chained through a real
        # release's next_tag — its existence is discoverable only via
        # AC-1.10's tag:null.
        for i, r in enumerate(releases):
            r["previous_tag"] = releases[i - 1]["tag"] if i > 0 else None
            r["next_tag"] = releases[i + 1]["tag"] if i + 1 < len(releases) else None

        pseudo = _pseudo_release(repo_root, as_of, feature_dirs) if releases else None
        if pseudo is not None:
            releases.append(pseudo)
    except (gitread.GitCommandFailed, ValueError) as exc:
        raise GitUnavailableError(f"git command failed unexpectedly: {exc}") from exc
    except OSError as exc:
        raise SparkDirUnreadableError(f".spark/ could not be read: {exc}") from exc

    return {
        "provenance": {
            "as_of": as_of,
            "insights_version": INSIGHTS_VERSION,
            "source": "git-interim",
            "git_available": True,
        },
        "releases": releases,
        "reason": None if releases else "repository has no tags",
    }
