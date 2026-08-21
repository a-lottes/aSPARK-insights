"""releaseboard_report — self-contained, dark-theme HTML rendering of a
`build_release_map()` dict (release-board-html, US-1/US-2/US-3).

Imports `_esc` from `render.py` (the one canonical escape choke-point,
NFR-2) but not `_STYLE` — A1's ruling (match the live aSPARK brand site,
not the shipped light scorecard theme) means this module ships its own
`:root`-token-based dark stylesheet rather than layering onto the light
one `report.py` reuses. Nothing here is recomputed: every figure comes
from `build_release_map()`'s own dict, verbatim (ADR-0).
"""

from __future__ import annotations

import re
from pathlib import Path

from aspark_insights.errors import ReleaseMapUnreadableError, ReportUnwritableError
from aspark_insights.gitboard.releaseboard_logo import LOGO_DATA_URI
from aspark_insights.gitboard.worktype import RECOGNIZED_TYPES
from aspark_insights.render import _esc
from aspark_insights.store import STORE_DIRNAME

REPORT_FILENAME = "release-board.html"

_ARTIFACT_NAMES = ("spec", "plan", "review", "qa", "release")

# NFR-4: a member/unattributed list beyond this bound is disclosed as
# truncated, mirroring `report.py`'s own `MAX_COMMITS_SHOWN` precedent —
# never silently grown without limit. Real data today: 3 members, 1
# unattributed at most.
_MAX_MEMBERS_SHOWN = 50
_MAX_UNATTRIBUTED_SHOWN = 50

# A3/NFR-5: hue keyed to artifact TYPE only, never to the artifact's own
# status VALUE — the identical hue renders for a `failed` and a `passed`
# qa.md (plan.md §1 Q5's fixed assignment). Five real, non-judgment hues
# from the live aSPARK site's own token set (spec §3 A1). Badges use a
# solid neutral background (`--bg-secondary`) rather than the live site's
# translucent per-hue tint: an opaque neutral background gives every hue a
# verifiable >=4.5:1 text contrast independent of its container, while the
# orange hue's own translucent tint measured a hair under 4.5:1 in the
# hand-computed check that informed this choice (T6).
_ARTIFACT_HUES: dict[str, str] = {
    "spec": "#3abdb0",     # teal
    "plan": "#a29bfe",     # violet
    "review": "#fdcb6e",   # amber
    "qa": "#00b894",       # green
    "release": "#e8623a",  # orange
}

_STYLE = """
  :root {
    --bg-primary: #0a0a0f;
    --bg-secondary: #12121a;
    --bg-card: #16162a;
    --text-primary: #f0f0f8;
    --text-secondary: #a0a0c0;
    /* --text-muted measures 3.90:1 on --bg-primary and 3.51:1 on --bg-card:
       it clears the 3:1 large-text/non-text floor but FAILS the 4.5:1
       small-text floor. Per spec A1 / plan T6 it may only be applied to
       >=24px-regular / >=19px-bold text or to non-text decoration — never to
       a status value, reason, commit subject/hash, date or count. */
    --text-muted: #6c6c8a;
    --accent-teal: #3abdb0;
    --border-subtle: rgba(58, 189, 176, 0.15);
    --border-line: rgba(255, 255, 255, 0.09);
    --radius-sm: 8px;
    --radius-lg: 24px;
    --maxw: 1200px;
  }
  * { box-sizing: border-box; }
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-primary);
    background: var(--bg-primary);
    margin: 0;
    padding: 2rem 1.5rem 4rem;
  }
  .page { max-width: var(--maxw); margin: 0 auto; }
  .masthead { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem; }
  .masthead img { height: 40px; width: auto; display: block; }
  h1 { font-size: 2.4rem; font-weight: 900; margin: 0 0 0.25rem; }
  h2 { font-size: 1.6rem; font-weight: 800; margin: 2.5rem 0 1rem; border-bottom: 1px solid var(--border-line); padding-bottom: 0.5rem; }
  h3 { font-size: 1.05rem; font-weight: 700; margin: 1.25rem 0 0.5rem; color: var(--text-primary); }
  a { color: var(--accent-teal); }
  .lead { color: var(--text-secondary); font-size: 1rem; margin: 0 0 0.5rem; }
  .index-list { list-style: none; padding: 0; margin: 1rem 0; display: grid; gap: 0.75rem; }
  .index-row { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem;
    background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);
    padding: 0.9rem 1.2rem; text-decoration: none; }
  .index-row:hover { border-color: var(--accent-teal); }
  .index-tag { font-weight: 700; font-size: 1.05rem; color: var(--text-primary); }
  .index-meta { font-size: 0.85rem; color: var(--text-secondary); white-space: nowrap; }
  .release-card { background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg);
    padding: 1.75rem; margin-bottom: 1.5rem; scroll-margin-top: 1rem; }
  .back-link { font-size: 0.85rem; display: inline-block; margin-bottom: 0.75rem; }
  .member-block { margin: 1rem 0; }
  .member-name { font-weight: 700; font-size: 1rem; color: var(--text-primary); }
  table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; }
  th, td { border: 1px solid var(--border-line); padding: 0.5rem 0.7rem; text-align: left; vertical-align: top;
    font-size: 0.88rem; color: var(--text-secondary); }
  th { background: var(--bg-secondary); color: var(--text-primary); }
  caption { text-align: left; font-weight: 600; margin-bottom: 0.25rem; color: var(--text-primary); }
  .table-wrap { overflow-x: auto; }
  .badge { display: inline-block; font-size: 0.75rem; font-weight: 700; padding: 0.15rem 0.55rem;
    border-radius: 100px; background: var(--bg-secondary); border: 1px solid currentColor; }
  .badge-reason { color: var(--text-secondary); font-size: 0.82rem; margin-left: 0.5rem; }
  .stats-line { color: var(--text-secondary); font-size: 0.95rem; margin: 0.25rem 0 1rem; }
  .commit-list { list-style: none; padding: 0; margin: 0.5rem 0; }
  .commit-item { font-size: 0.85rem; color: var(--text-secondary); padding: 0.4rem 0; border-bottom: 1px solid var(--border-line); }
  .commit-item .hash { color: var(--text-primary); font-family: 'JetBrains Mono', 'Fira Code', monospace; }
  .empty-notice { border: 1px solid var(--border-line); background: var(--bg-secondary); padding: 0.9rem;
    font-style: italic; color: var(--text-secondary); border-radius: var(--radius-sm); }
  .truncation-note { font-size: 0.82rem; color: var(--text-secondary); font-style: italic; margin: 0.4rem 0 0; }
  .pseudo-marker { display: inline-block; font-size: 0.7rem; color: var(--text-secondary);
    text-transform: uppercase; letter-spacing: 0.05em; margin-left: 0.5rem; }
"""


def _release_anchor(index: int) -> str:
    """Position-based id (`rel-0`, `rel-1`, ...) — never the tag text itself:
    a git tag is not guaranteed to be a valid, unique HTML `id` token, and
    position in `releases[]` is already the stable, order-preserving key
    every other AC in this module keys off of."""
    return f"rel-{index}"


def _release_label(release: dict) -> str:
    """A real release shows its tag; the pseudo-release (AC-1.3's `tag: null`
    discriminator — never inferred from row position) shows the open window
    it measures since its own `previous_tag`."""
    if release["tag"] is not None:
        return release["tag"]
    return f"Since {release['previous_tag']}" if release["previous_tag"] else "Open window"


_LEADING_BACKTICK_SPAN = re.compile(r"^`([^`]+)`")


def _strip_status_backticks(value: str) -> str:
    """AC-2.6: this project's own header tables wrap `Status` in Markdown
    code-span backticks (e.g. `` `approved` ``); stripped here as a
    presentation-only cleanup — the value itself is otherwise shown exactly
    as extracted, never re-interpreted.

    QA B1: a compound narrative status (e.g. this repo's own real
    `` `passed` — independent re-test... `` cell) only wraps its *leading*
    word in backticks, not the whole value — the original whole-value-wrap
    check never matched it, leaving a literal backtick visible. Matches and
    strips a leading backtick-delimited span specifically, leaving any
    trailing free text untouched and verbatim; a plain single-word wrapped
    value (the common case) still strips exactly as before."""
    match = _LEADING_BACKTICK_SPAN.match(value)
    if match:
        return match.group(1) + value[match.end():]
    return value


def _render_artifact_table(member: dict) -> str:
    """T4/AC-2.1: a real `<table>`/`<th scope="col">` matrix — never a
    div-badge-list standing in for tabular data (constitution §4). Every
    artifact's literal `status`, its `date` if present, and its `reason`
    when `status` is null — exactly as `build_release_map` returned it."""
    rows = []
    for artifact in _ARTIFACT_NAMES:
        entry = member["status"][artifact]
        status = entry.get("status")
        date = entry.get("date")
        reason = entry.get("reason")
        status_cell = (
            _esc(_strip_status_backticks(status)) if status is not None
            else f'<span class="badge-reason">{_esc(reason or "status unavailable")}</span>'
        )
        rows.append(
            "<tr>"
            f'<td><span class="badge" style="color:{_ARTIFACT_HUES[artifact]}">{_esc(artifact)}</span></td>'
            f"<td>{status_cell}</td>"
            f"<td>{_esc(date) if date is not None else ''}</td>"
            "</tr>"
        )
    body = "\n".join(rows)
    return (
        '<div class="table-wrap">\n<table>\n'
        # QA B2: the caption used to repeat the member's name
        # ("<name> — artifact status"), which the `<h4>` directly above
        # already states — at 375px, a long name made the caption's own
        # text wide enough to clip inside `.table-wrap`'s scroll container.
        # Dropped the redundant name: shorter, always fits, and avoids a
        # screen reader announcing the same name twice back to back.
        "<caption>Artifact status</caption>\n"
        '<thead><tr><th scope="col">Artifact</th><th scope="col">Status</th><th scope="col">Date</th></tr></thead>\n'
        f"<tbody>\n{body}\n</tbody>\n"
        "</table>\n</div>\n"
    )


def _render_member_block(member: dict) -> str:
    return (
        '<div class="member-block">\n'
        f'<h4 class="member-name">{_esc(member["name"])}</h4>\n'
        f"{_render_artifact_table(member)}"
        "</div>\n"
    )


def _render_members_section(release: dict) -> str:
    """NFR-4: bounded at `_MAX_MEMBERS_SHOWN`, disclosed as truncated —
    mirrors `report.py`'s own `.truncation-note` idiom rather than growing
    the page without limit (review F2)."""
    members = release["members"]
    if not members:
        return '<p class="empty-notice">No member features attributed to this release.</p>\n'
    shown = members[:_MAX_MEMBERS_SHOWN]
    body = "".join(_render_member_block(m) for m in shown)
    if len(members) > len(shown):
        body += (
            f'<p class="truncation-note">Showing the first {len(shown)} of {len(members)}.</p>\n'
        )
    return body


def _render_unattributed_section(release: dict) -> str:
    """AC-2.4/2.5: every entry's hash and subject verbatim, never re-
    attributed by matching text against a directory name; an empty list
    states "none" explicitly. NFR-4: bounded at `_MAX_UNATTRIBUTED_SHOWN`,
    disclosed as truncated (review F2)."""
    unattributed = release["unattributed"]
    if not unattributed:
        return '<p class="empty-notice">none</p>\n'
    shown = unattributed[:_MAX_UNATTRIBUTED_SHOWN]
    items = "".join(
        '<li class="commit-item">'
        f'<span class="hash">{_esc(c["hash"])}</span> — {_esc(c["subject"])}'
        "</li>\n"
        for c in shown
    )
    body = f'<ul class="commit-list">\n{items}</ul>\n'
    if len(unattributed) > len(shown):
        body += (
            f'<p class="truncation-note">Showing the first {len(shown)} of {len(unattributed)}.</p>\n'
        )
    return body


def _work_types_clause(release: dict) -> str:
    """AC-1.3: `work_types` is present on the pseudo-release exactly when
    `build_board()` itself includes it (conditional, same as
    `days_since_tag` — absent on too few classified commits or a
    zero-commit window, per `board.py`'s own `_build_work_types`), and
    review F5 caught that this renderer previously dropped it silently even
    when present. Fixed declared order (`RECOGNIZED_TYPES`, then
    `unclassified`) — the same order `report.py`'s own confidence-mix
    legend uses — never raw dict iteration order (NFR-6)."""
    wt = release.get("work_types")
    if wt is None or wt["value"] is None:
        return ""
    order = (*RECOGNIZED_TYPES, "unclassified")
    present = [(t, wt["value"][t]) for t in order if t in wt["value"]]
    if not present:
        return ""
    legend = ", ".join(f"{t} {pct}%" for t, pct in present)
    return f" Work types: {legend}."


def _pseudo_stats_line(release: dict) -> str:
    """AC-1.3/AC-3.2: the pseudo-release's own `commits`/`branches`/
    `days_since_tag`/`work_types` figures, copied through
    `build_release_map` from `build_board()` verbatim — formatted into one
    sentence here, never recomputed a second way. A zero-commit window
    states a true zero in words (AC-3.2), never a null card or an omitted
    line."""
    commits = release["commits"]
    tag = release["previous_tag"]
    if commits["value"] is None:
        return _esc(commits["reason"])
    if commits["value"] == 0:
        return _esc(f"Nothing has landed since {tag}." if tag else "Nothing has landed yet.")
    days = release.get("days_since_tag", {}).get("value")
    days_clause = f", {days} day{'s' if days != 1 else ''} ago" if days is not None else ""
    branch_count = len(release["branches"])
    branches_clause = f" {branch_count} local branch{'es' if branch_count != 1 else ''}."
    commit_word = "commit" if commits["value"] == 1 else "commits"
    work_types_clause = _work_types_clause(release)
    # One `_esc` over the whole sentence — never a partly-escaped string
    # concatenated with an unescaped tail, so a future edit that interpolates
    # a branch *name* here cannot silently bypass the choke-point (NFR-2).
    return _esc(
        f"{commits['value']} {commit_word} since {tag}{days_clause}.{branches_clause}{work_types_clause}"
    )


def _render_release_detail(release: dict, index: int) -> str:
    anchor = _release_anchor(index)
    label = _release_label(release)
    is_pseudo = release["tag"] is None
    pseudo_marker = '<span class="pseudo-marker">open window</span>' if is_pseudo else ""
    stats_line = f'<p class="stats-line">{_pseudo_stats_line(release)}</p>\n' if is_pseudo else ""
    return (
        f'<article class="release-card" id="{_esc(anchor)}">\n'
        f'<a class="back-link" href="#index">&larr; Back to index</a>\n'
        f"<h2>{_esc(label)}{pseudo_marker}</h2>\n"
        f"{stats_line}"
        "<h3>Members</h3>\n"
        f"{_render_members_section(release)}"
        "<h3>Unattributed commits</h3>\n"
        f"{_render_unattributed_section(release)}"
        "</article>\n"
    )


def _render_index_row(release: dict, index: int) -> str:
    """AC-1.1/1.2: one row per entry, in `releases[]`'s own order; counts
    read from `members`/`unattributed`'s list lengths, never recomputed
    (T1). AC-1.3: the pseudo-release is distinguished by `tag: null`, never
    by its row position."""
    anchor = _release_anchor(index)
    label = _release_label(release)
    is_pseudo = release["tag"] is None
    pseudo_marker = '<span class="pseudo-marker">open window</span>' if is_pseudo else ""
    member_count = len(release["members"])
    unattributed_count = len(release["unattributed"])
    return (
        f'<li><a class="index-row" href="#{_esc(anchor)}">\n'
        f'<span class="index-tag">{_esc(label)}{pseudo_marker}</span>\n'
        f'<span class="index-meta">{member_count} member{"s" if member_count != 1 else ""} '
        f'&middot; {unattributed_count} unattributed</span>\n'
        "</a></li>\n"
    )


def _render_masthead() -> str:
    return (
        '<div class="masthead">\n'
        f'<img src="{LOGO_DATA_URI}" alt="aSPARK" width="121" height="40">\n'
        "</div>\n"
    )


def render_release_board_html(data: dict) -> str:
    """Pure — `build_release_map()` dict in, HTML string out, no
    I/O/clock/randomness (NFR-6's determinism substrate, the unit-test
    seam). Zero JavaScript, static same-document `#`-anchor drill-down
    (A4)."""
    releases = data["releases"]
    reason = data.get("reason")

    if not releases:
        # AC-3.1: zero tags — the reason in words, an empty index, never a
        # traceback, a blank page, or a placeholder row.
        body = (
            f'<p class="empty-notice">{_esc(reason or "no releases found")}</p>\n'
        )
    else:
        index_rows = "".join(_render_index_row(r, i) for i, r in enumerate(releases))
        details = "".join(_render_release_detail(r, i) for i, r in enumerate(releases))
        count_word = "release" if len(releases) == 1 else "releases"
        body = (
            f'<p class="lead">{len(releases)} {count_word}, oldest first.</p>\n'
            f'<ul class="index-list" id="index">\n{index_rows}</ul>\n'
            f"{details}"
        )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>aSPARK Release Board</title>\n"
        f"<style>{_STYLE}</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="page">\n'
        + _render_masthead()
        + "<h1>Release Board</h1>\n"
        + body
        + "</div>\n"
        "</body>\n"
        "</html>\n"
    )


def run_release_board_report(data: dict, output: str) -> Path:
    """Writes `<output>/.aspark-insights/release-board.html`, returns its
    resolved absolute path. Same F1-class safety net `render.py`/`report.py`
    both apply: a malformed data dict must never escape as a raw traceback
    (constitution §6). Review F1: the write itself is equally hostile-input-
    exposed (`--output` pointing at an existing file, or an unwritable
    path) — wrapped in its own guard so a bad *destination* fails exactly
    as cleanly as bad *data*, never a raw `OSError` traceback."""
    try:
        text = render_release_board_html(data)
    except (AttributeError, KeyError, TypeError) as exc:
        raise ReleaseMapUnreadableError(
            f"release map data has an unexpected shape: {exc}"
        ) from exc

    out_path = Path(output) / STORE_DIRNAME / REPORT_FILENAME
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise ReportUnwritableError(
            f"could not write release-board.html to {out_path}: {exc}"
        ) from exc
    return out_path.resolve()
