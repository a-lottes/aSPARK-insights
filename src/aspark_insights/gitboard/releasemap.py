"""releasemap — shared core: every git tag (topology-ordered) plus one
trailing open-window pseudo-release, mapped to the `.spark/<feature>/`
directories and unattributed commits in range, plus each feature's own
artifact status (US-1/US-2/US-3). Since release-metrics, each real
release also carries its own `date`/`commit_count`/`work_types`/
`gap_days`/`delivered_scope`, each member its own `delivery`/`scope`, and
the map a top-level `figures` band — all computed once here and only ever
read, never re-derived, by both `--format json` and the HTML renderer
(ADR-0; review F9).

The pseudo-release's own git-derived figures are never a second
implementation of "commits since the latest tag" (AC-1.8/ADR-0) — they are
`gitboard.board.build_board()`'s own result, reused verbatim. Imports no
sibling graph tool's port or library — standalone the same way
`gitboard/board.py` already is (US-1's own no-graph proof extends here).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from aspark_insights import __version__ as INSIGHTS_VERSION
from aspark_insights.errors import GitUnavailableError, InvalidAsOfError, SparkDirUnreadableError
from aspark_insights.gitboard import gitread, worktype
from aspark_insights.gitboard.artifactstatus import read_artifact_status
from aspark_insights.gitboard.board import build_board
from aspark_insights.gitboard.scopecount import read_scope_counts

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
) -> tuple[list[str], list[dict], list[dict]]:
    """A7: membership is decided **only** by changed paths in `range_spec`,
    never by matching a commit's subject text against a directory name —
    this repo's own `26e7f95` ("snapshot-report scorecard redesign") names
    a directory in prose while touching zero files under it, which is
    exactly the trap path-only attribution avoids. `unattributed` is every
    commit in range that touched no validated feature directory (A7) — never
    dropped, never guessed onto the nearest feature.

    release-metrics T1/T2: also returns the full `all_commits` list — the
    same range population AC-1.2's commit count and AC-1.3's work-type mix
    are measured over, so a caller gets both figures at **zero extra git
    calls** rather than a second, separately-derived range (ADR-0)."""
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
    return members, unattributed, all_commits


def _member_entries(repo_root: str, member_names: list[str]) -> list[dict]:
    """Each member's own `spec`/`plan`/`review`/`qa`/`release` status map
    (US-2), read via `.spark/<feature-name>/<artifact>.md` paths built from
    an already-validated name (`_list_feature_dirs` rejected any hostile
    name before it could reach here — NFR-2, no second validation needed).

    release-metrics US-2/A1: also reads `scope` — the feature's own US/AC
    counts via the local `scopecount` parser, from the same `spec.md`
    `status["spec"]` already opens for a different cell. `delivery` is
    NOT stamped here — it depends on cross-release ordering, so
    `_attribute_delivery` fills it in afterward as its own pass over the
    assembled `releases[]` (§1's "delivery is data, not rendering")."""
    entries = []
    for name in member_names:
        feature_dir = Path(repo_root) / _SPARK_DIRNAME / name
        status = {
            artifact: read_artifact_status(feature_dir / f"{artifact}.md")
            for artifact in _ARTIFACT_NAMES
        }
        scope = read_scope_counts(feature_dir / "spec.md")
        entries.append({"name": name, "status": status, "scope": scope})
    return entries


def _attribute_delivery(releases: list[dict]) -> None:
    """A3/A6/US-2: a feature is **delivering** in exactly the oldest release
    it appears as a member of; every later appearance (including in the
    open pseudo-release) is **trailing**. Mutates each member dict in
    place with `delivery: {"delivering", "delivered_in", "reason"}` —
    never re-decides membership itself (ADR-0), only labels who was first.

    Must run over `releases` in the exact order `build_release_map`
    assembles it — real tags oldest-first, pseudo-release (if any) last —
    so a feature whose first appearance is the open window is never
    marked delivering (A6): it is `delivering: False, delivered_in: None`
    with a named reason, distinct from "delivering: False in a real
    release with a real `delivered_in` tag"."""
    delivered_in: dict[str, str] = {}
    for release in releases:
        tag = release["tag"]
        for member in release["members"]:
            name = member["name"]
            if name in delivered_in:
                member["delivery"] = {
                    "delivering": False, "delivered_in": delivered_in[name], "reason": None,
                }
            elif tag is not None:
                delivered_in[name] = tag
                member["delivery"] = {"delivering": True, "delivered_in": None, "reason": None}
            else:
                member["delivery"] = {
                    "delivering": False, "delivered_in": None,
                    "reason": "not yet delivered in a tagged release",
                }


def _delivered_scope(release: dict) -> dict:
    """US-2/AC-2.3/AC-3.6: sums `scope` over **delivering** members only —
    trailing members contribute zero by construction (the loop below never
    visits them), not by filtering a pre-summed total. An unreadable
    delivering member's scope is named and excluded, never folded in as a
    silent zero (constitution: never invent a number); if delivering
    members exist but *none* of their scopes are readable, the total is
    `null` with a reason, distinct from a release that genuinely delivers
    nothing (AC-2.2's v0.6.0 case), which reports a real `0`."""
    delivering = [m for m in release["members"] if m["delivery"]["delivering"]]
    us_total = 0
    ac_total = 0
    unreadable: list[str] = []
    counted = 0
    for member in delivering:
        scope = member["scope"]
        if scope["us"] is None or scope["acs"] is None:
            unreadable.append(member["name"])
            continue
        us_total += scope["us"]
        ac_total += scope["acs"]
        counted += 1
    if delivering and counted == 0:
        return {
            "us": None, "acs": None, "n": 0, "unreadable": unreadable,
            "reason": "no delivering member's scope could be read",
        }
    return {"us": us_total, "acs": ac_total, "n": counted, "unreadable": unreadable, "reason": None}


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
    members, unattributed, _all_commits = _members_and_unattributed(repo_root, range_spec, feature_dirs)

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


def _release_date(repo_root: str, tag: str) -> tuple[str | None, str | None]:
    """AC-1.1/AC-1.4: a real release's own tag commit date, UTC-normalized
    to a plain calendar date — the same normalization `board._whole_days`
    already uses for "age" figures, so a gap between two release dates is
    the difference of two dates derived identically (plan §1's named
    sub-decision). `None` + a reason when unreadable — `tag_commit_date`
    already filters git's own unexpanded-`%cI`-placeholder quirk; the
    `ValueError` guard here is QA-B1-style local wrapping for any other
    truthy-but-unparseable value, never a raw traceback."""
    raw = gitread.tag_commit_date(repo_root, tag)
    if raw is None:
        return None, "tag commit date could not be read"
    try:
        return datetime.fromisoformat(raw).astimezone(timezone.utc).date().isoformat(), None
    except ValueError:
        return None, "tag commit date could not be parsed"


def _release_work_types(all_commits: list[dict]) -> dict | None:
    """AC-1.3: mirrors `board._build_work_types`'s own conditional
    presence exactly — the key is **absent** (not even `null`) on a
    genuinely empty range (no referent to classify), and present with
    `{"value": None, "reason": ...}` when commits exist but too few are
    classifiable (`worktype.breakdown`'s own honest-null, never a second
    classifier)."""
    if not all_commits:
        return None
    subjects = [c["subject"] for c in all_commits]
    return worktype.breakdown(subjects)


def _attach_gap_days(releases: list[dict]) -> None:
    """A5/A7/AC-4.2: a real release's gap to its immediate predecessor —
    a distinct quantity and a distinct key from the pseudo-release's own
    `days_since_tag` (age relative to `as_of`), never overloaded. The
    earliest release has no predecessor: `null` with that reason, never a
    `0`, which would misread as "shipped the same day" (AC-4.2). Gap is
    always measured against the *immediately preceding* release's own
    date — if that date is itself unreadable, the gap is `null` with its
    own reason rather than silently reaching further back (no look-behind
    heuristic invented beyond what AC-1.4/A5 asked for)."""
    prev_date: str | None = None
    is_first = True
    for release in releases:
        if release["tag"] is None:
            continue  # pseudo-release keeps days_since_tag untouched (A7)
        this_date = release.get("date")
        if is_first:
            release["gap_days"], release["gap_days_reason"] = None, "no predecessor release"
        elif prev_date is None or this_date is None:
            release["gap_days"], release["gap_days_reason"] = (
                None, "a needed release date could not be read",
            )
        else:
            release["gap_days"] = (date.fromisoformat(this_date) - date.fromisoformat(prev_date)).days
            release["gap_days_reason"] = None
        prev_date = this_date
        is_first = False


def _median(values: list[int]) -> float:
    """A plain, documented median — even-`n` is the exact two-middle mean,
    never rounded (plan §1's named sub-decision, so a re-derivation always
    reproduces the same figure)."""
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2


def _build_figures(releases: list[dict]) -> dict:
    """US-3: the global figures band — every entry a measured number with
    its own denominator, or `null` with a named reason (MTA-001/NFR-5).
    **No trend line, projection or forecast is computed here or anywhere**
    — the qualitative rule is satisfied by never writing the code that
    would draw one, not by a threshold this project has never set."""
    real = [r for r in releases if r["tag"] is not None]
    pseudo = next((r for r in releases if r["tag"] is None), None)

    gaps = [r["gap_days"] for r in real if r.get("gap_days") is not None]
    dates = [r["date"] for r in real if r.get("date") is not None]
    scope_unreadable = sorted({name for r in real for name in r["delivered_scope"]["unreadable"]})
    features_delivered = sum(1 for r in real for m in r["members"] if m["delivery"]["delivering"])
    # review F1: how many of `features_delivered`'s own scopes actually
    # went into `delivered_us`/`delivered_acs` — a partial `n` (<
    # features_delivered) is real even when the total itself isn't null,
    # and must be visible next to the total rather than only inferable
    # from `scope_unreadable`'s name list.
    delivered_scope_n = sum(r["delivered_scope"]["n"] for r in real)

    # AC-3.6: a release whose *entire* delivering set was unreadable
    # reports `delivered_scope["us"] is None` (see `_delivered_scope`) —
    # summing `or 0` over that would silently fold a null into the band's
    # total, exactly what AC-3.6 forbids ("never a silent zero folded into
    # ... the band's total"). `scope_unreadable` already names the affected
    # feature(s) for the reason text.
    if any(r["delivered_scope"]["us"] is None for r in real):
        delivered_us = None
        delivered_acs = None
    else:
        delivered_us = sum(r["delivered_scope"]["us"] for r in real)
        delivered_acs = sum(r["delivered_scope"]["acs"] for r in real)

    return {
        "release_count": len(real),
        "first_date": min(dates) if dates else None,
        "last_date": max(dates) if dates else None,
        "gap_median": _median(gaps) if gaps else None,
        "gap_min": min(gaps) if gaps else None,
        "gap_max": max(gaps) if gaps else None,
        "gap_n": len(gaps),
        "features_delivered": features_delivered,
        "delivered_us": delivered_us,
        "delivered_acs": delivered_acs,
        "delivered_scope_n": delivered_scope_n,
        "scope_unreadable": scope_unreadable,
        "open_window_commit_count": (
            pseudo["commits"]["value"] if pseudo and pseudo["commits"]["value"] is not None else None
        ),
    }


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
            members, unattributed, all_commits = _members_and_unattributed(
                repo_root, range_spec, feature_dirs
            )
            date_value, date_reason = _release_date(repo_root, tag)
            entry = {
                "tag": tag,
                "date": date_value,
                "date_reason": date_reason,
                "commit_count": len(all_commits),
                "members": _member_entries(repo_root, members),
                "unattributed": unattributed,
            }
            work_types = _release_work_types(all_commits)
            if work_types is not None:
                entry["work_types"] = work_types
            releases.append(entry)
            previous_tag = tag

        # AC-3.1: previous_tag/next_tag chain real releases only (null at
        # either end); the pseudo-release is never chained through a real
        # release's next_tag — its existence is discoverable only via
        # AC-1.10's tag:null.
        for i, r in enumerate(releases):
            r["previous_tag"] = releases[i - 1]["tag"] if i > 0 else None
            r["next_tag"] = releases[i + 1]["tag"] if i + 1 < len(releases) else None

        # release-metrics T4/T6: gap_days over real releases only, before
        # the pseudo-release (no tag, no gap) is appended.
        _attach_gap_days(releases)

        pseudo = _pseudo_release(repo_root, as_of, feature_dirs) if releases else None
        if pseudo is not None:
            releases.append(pseudo)

        # release-metrics US-2: delivery attribution runs over the FULL
        # list (real releases oldest-first, then the pseudo-release last)
        # so a feature whose first appearance is the open window is never
        # marked delivering (A6) — see _attribute_delivery's own docstring.
        _attribute_delivery(releases)
        for r in releases:
            if r["tag"] is not None:
                r["delivered_scope"] = _delivered_scope(r)

        figures = _build_figures(releases) if releases else None
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
        "figures": figures,
    }
