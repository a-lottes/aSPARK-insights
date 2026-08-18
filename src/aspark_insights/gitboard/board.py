"""board — the shared core: read git once, assemble one dict, JSON and HTML
both render from it (the house "shared core, two thin adapters" pattern).

Never imports the sibling graph tool's port or library and never touches
`.spark/` — that's the whole point (US-2, AC-2.2): this must run against a
repo with zero graph and zero `.spark/` present.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from aspark_insights import __version__ as INSIGHTS_VERSION
from aspark_insights.errors import GitUnavailableError, InvalidAsOfError
from aspark_insights.gitboard import gitread, worktype

MAX_COMMITS_SHOWN = 50


def _validate_as_of(as_of: str) -> None:
    """A parse of a caller-supplied string, not a clock read (ADR-4) — the
    same validation `build_snapshot` applies to its own `--as-of`."""
    try:
        datetime.strptime(as_of, "%Y-%m-%d")
    except ValueError as exc:
        raise InvalidAsOfError(
            f"--as-of must be an ISO-8601 date (YYYY-MM-DD), got {as_of!r}"
        ) from exc


def _whole_days(from_iso: str, as_of: str) -> int:
    """UTC-normalized whole days from an ISO-8601 git date to `as_of` (a
    plain YYYY-MM-DD) — never `now()` (NFR-5). Normalizing to UTC before
    taking the calendar date keeps the figure stable regardless of the
    committer's local offset or the machine running `insights board`."""
    from_date = datetime.fromisoformat(from_iso).astimezone(timezone.utc).date()
    as_of_date = date.fromisoformat(as_of)
    return (as_of_date - from_date).days


def _build_commits(repo_root: str, tag: str | None) -> dict:
    if tag is None:
        return {
            "value": None,
            "reason": "repository has no tags; commits-since-release is undefined without a release marker",
        }
    count = gitread.count_commits_since(repo_root, tag)
    shown = gitread.list_commits_since(repo_root, tag, MAX_COMMITS_SHOWN)
    return {
        "value": count,
        "reason": None,
        "shown": shown,
        "shown_count": len(shown),
        "truncated": count > len(shown),
    }


def _build_days_since_tag(repo_root: str, tag: str | None, as_of: str) -> dict | None:
    """`None` (the key is *absent* from the board, AC-1.10(a)) when there is
    no tag at all — a second null for the same cause AC-1.2 already explains
    would be two competing explanations, not one. A dict (present, possibly
    null-with-reason) whenever a tag exists."""
    if tag is None:
        return None
    tag_date = gitread.tag_commit_date(repo_root, tag)
    if tag_date is None:
        return {"value": None, "reason": f"commit date for tag {tag!r} could not be read"}
    return {"value": _whole_days(tag_date, as_of), "reason": None}


def _build_work_types(repo_root: str, tag: str | None, commit_count: int | None) -> dict | None:
    """`None` (absent) on a tagless repo or a real zero-commits-since-tag —
    AC-1.12(c)/(d): "commits since T" has no referent without T, and a 0/0
    classifiable ratio is undefined, not a real 0%. Both cases are decided
    here, before `worktype.breakdown` ever sees a (necessarily nonempty)
    subject list."""
    if tag is None or not commit_count:
        return None
    subjects = gitread.list_commit_subjects_since(repo_root, tag)
    return worktype.breakdown(subjects)


def _build_branches(repo_root: str, as_of: str) -> list[dict]:
    branches = []
    for b in gitread.list_branches(repo_root):
        if b["tip_date"]:
            branches.append({**b, "age_days": _whole_days(b["tip_date"], as_of), "age_reason": None})
        else:
            branches.append({**b, "age_days": None, "age_reason": "branch tip commit date could not be read"})
    return branches


def build_board(repo_root: str, as_of: str) -> dict:
    """The one read: validates `as_of`, confirms `repo_root` is a real git
    repo (raises `NotAGitRepoError` otherwise — AC-1.4/AC-2.3), then reads
    every git-derived figure this feature reports. Any *unexpected* git
    failure past that point (a call site with no bespoke degradation of its
    own) is the final safety net into `GitUnavailableError` — never a raw
    traceback (constitution §6). `ValueError` is caught alongside
    `GitCommandFailed`: an exit-0 git call whose output doesn't parse as
    expected (a malformed `rev-list --count` integer, an unparseable `%cI`
    date) is exactly as unexpected as a nonzero exit, and must not escape
    as a raw traceback either."""
    _validate_as_of(as_of)
    gitread.ensure_git_repo(repo_root)

    try:
        shallow = gitread.is_shallow(repo_root)
        tag = gitread.resolve_tag(repo_root)
        commits = _build_commits(repo_root, tag)
        days_since_tag = _build_days_since_tag(repo_root, tag, as_of)
        work_types = _build_work_types(repo_root, tag, commits["value"])
        branches = _build_branches(repo_root, as_of)
    except (gitread.GitCommandFailed, ValueError) as exc:
        raise GitUnavailableError(f"git command failed unexpectedly: {exc}") from exc

    board = {
        "provenance": {
            "as_of": as_of,
            "insights_version": INSIGHTS_VERSION,
            "source": "git-interim",
            "git_available": True,
            "resolved_tag": tag,
            "resolved_tag_reason": None if tag is not None else "repository has no tags",
            "shallow": shallow,
        },
        "commits": commits,
        "branches": branches,
    }
    if days_since_tag is not None:
        board["days_since_tag"] = days_since_tag
    if work_types is not None:
        board["work_types"] = work_types
    return board
