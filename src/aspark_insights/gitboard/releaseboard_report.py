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
from aspark_insights.gitboard.markdownlite import render_markdown
from aspark_insights.gitboard.releaseboard_logo import LOGO_DATA_URI
from aspark_insights.gitboard.worktype import RECOGNIZED_TYPES
from aspark_insights.render import _esc
from aspark_insights.store import STORE_DIRNAME

REPORT_FILENAME = "release-board.html"

_ARTIFACT_NAMES = ("spec", "plan", "review", "qa", "release")
_SPARK_DIRNAME = ".spark"

# NFR-4: a member/unattributed list beyond this bound is disclosed as
# truncated, mirroring `report.py`'s own `MAX_COMMITS_SHOWN` precedent —
# never silently grown without limit. Real data today: 3 members, 1
# unattributed at most.
_MAX_MEMBERS_SHOWN = 50
_MAX_UNATTRIBUTED_SHOWN = 50

# T4/A5: total raw document bytes consumed, in display order, before this
# page stops embedding further feature documents — the hard ceiling that
# turns the single-file decision (plan.md §1) into a bound, not a hope. A
# document beyond this budget is disclosed by name and path, never embedded
# and never silently dropped.
_PAGE_DOCUMENT_BUDGET_BYTES = 2_500_000

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
  /* T5 (design findings 3/4/8): a document's own raw prose must never look
     like the board's own live status UI (.release-card/.badge) — flat
     background, a left accent rule instead of a card radius, its own
     provenance label always visible even before expanding. */
  .doc-content { background: var(--bg-secondary); border-left: 3px solid var(--accent-teal);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0; padding: 0.75rem 1rem; margin: 0.6rem 0; }
  .doc-content summary { cursor: pointer; font-weight: 700; color: var(--text-primary); }
  .doc-provenance { font-size: 0.78rem; color: var(--text-secondary); margin: 0.5rem 0; }
  /* QA B1: a long inline `<code>` span (a real test-name/file-path
     reference in this project's own document prose) was not wrapped and
     pushed the whole page out sideways at 375px — `.doc-content pre`
     already had `word-break`, prose and list items never did. */
  .doc-content p, .doc-content li { max-width: 74ch; overflow-wrap: anywhere; }
  .doc-content code { overflow-wrap: anywhere; word-break: break-word; }
  .doc-content pre { white-space: pre-wrap; word-break: break-word; font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.82rem; color: var(--text-secondary); background: var(--bg-primary); border-radius: var(--radius-sm);
    padding: 0.75rem; overflow-x: auto; margin: 0.5rem 0; }
  .doc-content table { max-width: none; }
  /* T9/AC-3.3 (design finding 6): `markdownlite` emits a `.sr-only`
     "checked:"/"unchecked:" prefix on every checklist item so the state
     reaches assistive tech as text, never as color or glyph alone. Without
     this rule the prefix rendered as visible body copy next to every
     checkbox glyph (review F2). */
  .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
    overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
  .doc-back-link { font-size: 0.8rem; display: inline-block; margin-top: 0.5rem; }
  .doc-content-link { color: var(--text-secondary); font-size: 0.88rem; margin: 0.4rem 0; }
  /* T7/AC-3.1, T10/AC-4.1: real <dl> label/value pairs — reuses the
     shipped .index-list auto-fit grid idiom so the band wraps to
     multiple rows at narrow widths instead of one unbreakable row
     (design finding 4, this page's own prior 375px defect). */
  .figures-band { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.9rem 1.5rem; margin: 1rem 0 1.5rem; padding: 1.1rem 1.3rem; background: var(--bg-card);
    border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); }
  .figures-band dt { font-size: 0.78rem; color: var(--text-secondary); text-transform: uppercase;
    letter-spacing: 0.04em; margin: 0; }
  .figures-band dd { font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin: 0.15rem 0 0; }
  .release-figures dd { font-size: 0.95rem; }
  /* T8/AC-3.2/NFR-5: exactly one class, one hue, for every bar regardless
     of value — a value-dependent color here would read as an undisclosed
     pass/fail verdict (constitution §3/§6). The longest gap is marked by
     rank only (bold text + the word "longest"), never by this bar's
     color or width alone — every gap is also a plain number in the
     preceding cell. */
  .cadence-bar { display: block; height: 0.6rem; min-width: 2px; background: var(--accent-teal);
    border-radius: 100px; }
"""


def _scope_text(us: int, acs: int) -> str:
    """Review F12: `acs` singularizes like the existing `commit`/`commits`
    idiom (`_pseudo_stats_line`) — `"1 AC"`, never `"1 ACs"`. `us` stays
    the fixed abbreviation `US` regardless of count, matching this
    project's own spec/plan usage (`"1 US"`, not `"1 USs"`)."""
    ac_word = "AC" if acs == 1 else "ACs"
    return f"{us} US / {acs} {ac_word}"


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


def _document_plan(display_order: list[tuple[int, dict]], documents: dict, budget_bytes: int) -> dict[str, dict]:
    """T2 dedup + T4 page budget, computed together in one pass over
    `display_order` (A5: budget consumed in display order, never reordered
    for convenience). Maps feature name -> `{"home_index", "embedded",
    "k"}`: `home_index` is the original `releases[]` index of the release
    under which this feature's documents actually render inline (its first
    occurrence in display order); `embedded` is False when the page budget
    was exhausted before reaching it (T4's disclosed-not-dropped case,
    never a silent omission); `k` is a stable, position-derived integer
    (0-based, first-occurrence order) used to build anchor ids that never
    encode the feature's own name text.

    Review F3 (Major): iterates only `release["members"][:_MAX_MEMBERS_SHOWN]`
    — the exact same slice `_render_members_section` actually renders — so
    a feature past that bound can never become the "home" of a member
    block that is never rendered. Without this, a feature's documents
    could be homed to a release whose member list is truncated before
    reaching it, vanishing from the page entirely while every other
    occurrence still links to it."""
    plan: dict[str, dict] = {}
    remaining = budget_bytes
    for original_index, release in display_order:
        for slot, member in enumerate(release["members"][:_MAX_MEMBERS_SHOWN]):
            name = member["name"]
            if name in plan:
                continue
            docs = documents.get(name, {})
            feature_bytes = sum(len(d.get("text", "").encode("utf-8")) for d in docs.values())
            embedded = feature_bytes <= remaining
            if embedded:
                remaining -= feature_bytes
            plan[name] = {
                "home_index": original_index,
                # Review F13: the anchor the non-home link actually
                # targets — the member block itself, not just the release
                # card (`#rel-N` could land the reader far above the
                # content on a release with many members).
                "home_anchor": f"member-{original_index}-{slot}",
                "embedded": embedded,
                "k": len(plan),
            }
    return plan


def _truncation_message(doc: dict) -> str:
    """T4/AC-2.5: line-bounded and byte-bounded documents need different
    honest wording — a single giant line (the byte cap trips, the line
    count never does) has nothing meaningful to say about "lines shown".

    Review F6: when BOTH caps tripped (a huge first line pushes the byte
    cap while also forcing the partial trailing line to be dropped, so
    `shown_lines < total_lines` by exactly one), the line-only wording
    wrongly implied the shown line(s) were complete. State both when both
    are true, never just the line count in that case."""
    byte_truncated = doc.get("byte_truncated", False)
    line_truncated = doc.get("line_truncated", False)
    shown_bytes = len(doc["text"].encode("utf-8"))
    if byte_truncated and line_truncated:
        return (
            f"Showing the first {doc['shown_lines']} of {doc['total_lines']} lines "
            f"({shown_bytes} of {doc['total_bytes']} bytes) of this document."
        )
    if line_truncated:
        return f"Showing the first {doc['shown_lines']} of {doc['total_lines']} lines of this document."
    return f"Showing the first {shown_bytes} of {doc['total_bytes']} bytes of this document."


def _render_one_document(feature_name: str, artifact: str, k: int, doc: dict) -> str:
    """T2/T3/T5: one artifact's document as a closed `<details>` — honest
    per-state body (T3), truncation disclosure (T4), a persistent
    provenance label naming the real repo-relative path so a reader never
    mistakes raw document prose for the board's own live status (finding
    3)."""
    anchor = f"doc-f{k}-{artifact}"
    reason = doc.get("reason")
    if reason is not None:
        body = f'<p class="empty-notice">{_esc(reason)}</p>\n'
    elif doc.get("empty"):
        body = '<p class="empty-notice">This document is empty.</p>\n'
    else:
        # T10/US-3: structured rendering (markdownlite) — real headings,
        # tables, lists, no raw #/|/[ ] syntax. Base level 5: the page's
        # own shipped hierarchy already runs h1(page)-h2(release)-
        # h3(section)-h4(member); `<summary>` is a label, not a heading, so
        # it costs no level (design finding 2, plan §1).
        body = f"{render_markdown(doc['text'], base_level=5)}\n"
        if doc.get("truncated"):
            body += f'<p class="truncation-note">{_esc(_truncation_message(doc))}</p>\n'
    path = f"{_SPARK_DIRNAME}/{feature_name}/{artifact}.md"
    return (
        f'<details class="doc-content" id="{_esc(anchor)}">\n'
        f'<summary>{_esc(artifact)}.md</summary>\n'
        f'<p class="doc-provenance">Document content &mdash; read-only, as extracted from '
        f'<code>{_esc(path)}</code></p>\n'
        f"{body}"
        "</details>\n"
    )


def _render_document_details(feature_name: str, k: int, documents: dict) -> str:
    docs = documents.get(feature_name, {})
    # Review F14: a real, specific reason — not the bare, unexplained
    # "not read" — for the case where this feature has no entry in
    # `documents` at all (e.g. `documents={}`, or a name that failed the
    # collector's own validation).
    empty_doc = {
        "reason": "document not collected for this render", "text": "", "empty": False, "truncated": False,
        "total_lines": 0, "shown_lines": 0, "total_bytes": 0,
    }
    return "".join(
        _render_one_document(feature_name, artifact, k, docs.get(artifact) or empty_doc)
        for artifact in _ARTIFACT_NAMES
    )


def _render_documents_for_member(
    member: dict, original_index: int, plan: dict, documents: dict,
    releases: list[dict], member_anchor: str,
) -> str:
    """US-2: the document-viewing capability for one member, in whichever
    of three states its feature's dedup/budget plan puts it in — home and
    embedded (full content), non-home (an explicit link to where it lives,
    never a silent gap — finding per T2's dedup rule), or home but over the
    page budget (disclosed by path, never embedded and never dropped
    silently — T4/A5)."""
    name = member["name"]
    entry = plan.get(name)
    if entry is None:
        return ""
    note = _trailing_note(member)
    if entry["home_index"] != original_index:
        home_label = _esc(_release_label(releases[entry["home_index"]]))
        # Review F13: links directly to the member block itself, not just
        # the release card — a card can hold up to 50 members.
        home_anchor = _esc(entry["home_anchor"])
        return note + (
            f'<p class="doc-content-link">Documents shown under '
            f'<a href="#{home_anchor}">{home_label}</a>.</p>\n'
        )
    if not entry["embedded"]:
        return note + (
            '<p class="empty-notice">Not embedded in this page &mdash; the page-weight budget '
            f'was reached before reaching this feature\'s documents. Read each one directly at '
            f'<code>{_SPARK_DIRNAME}/{_esc(name)}/{{spec,plan,review,qa,release}}.md</code>.</p>\n'
        )
    return note + (
        _render_document_details(name, entry["k"], documents)
        + f'<a class="doc-back-link" href="#{_esc(member_anchor)}">&uarr; Back to {_esc(name)}</a>\n'
    )


def _render_member_block(
    member: dict, *, original_index: int, member_slot: int,
    plan: dict | None, documents: dict | None, releases: list[dict] | None,
) -> str:
    member_anchor = f"member-{original_index}-{member_slot}"
    doc_section = ""
    if plan is not None:
        doc_section = _render_documents_for_member(member, original_index, plan, documents, releases, member_anchor)
    return (
        f'<div class="member-block" id="{_esc(member_anchor)}">\n'
        f'<h4 class="member-name">{_esc(member["name"])}</h4>\n'
        f"{_delivery_clause(member)}"
        f"{_render_artifact_table(member)}"
        f"{doc_section}"
        "</div>\n"
    )


def _render_members_section(
    release: dict, *, original_index: int,
    plan: dict | None, documents: dict | None, releases: list[dict] | None,
) -> str:
    """NFR-4: bounded at `_MAX_MEMBERS_SHOWN`, disclosed as truncated —
    mirrors `report.py`'s own `.truncation-note` idiom rather than growing
    the page without limit (review F2)."""
    members = release["members"]
    if not members:
        return '<p class="empty-notice">No member features attributed to this release.</p>\n'
    shown = members[:_MAX_MEMBERS_SHOWN]
    body = "".join(
        _render_member_block(
            m, original_index=original_index, member_slot=i,
            plan=plan, documents=documents, releases=releases,
        )
        for i, m in enumerate(shown)
    )
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


def _work_types_value(release: dict) -> str:
    """Shared with `_work_types_clause` below (review F8: `_render_release_
    figures` used to re-derive this by string-slicing `_work_types_clause`'s
    own sentence and collapsing every "nothing to show" case — key absent,
    or `worktype.breakdown` itself returning an honest null — into one
    generic message, discarding `breakdown`'s own specific reason). Returns
    the bare legend text, or the most specific reason available; never a
    guess, never generic when a real reason exists. Fixed declared order
    (`RECOGNIZED_TYPES`, then `unclassified`) — the same order `report.py`'s
    own confidence-mix legend uses — never raw dict iteration order
    (NFR-6)."""
    wt = release.get("work_types")
    if wt is None:
        return "not classifiable for this range"
    if wt["value"] is None:
        return wt["reason"] or "not classifiable for this range"
    order = (*RECOGNIZED_TYPES, "unclassified")
    present = [(t, wt["value"][t]) for t in order if t in wt["value"]]
    if not present:
        return "not classifiable for this range"
    return ", ".join(f"{t} {pct}%" for t, pct in present)


def _work_types_clause(release: dict) -> str:
    """AC-1.3: `work_types` is present on the pseudo-release exactly when
    `build_board()` itself includes it (conditional, same as
    `days_since_tag` — absent on too few classified commits or a
    zero-commit window, per `board.py`'s own `_build_work_types`), and
    review F5 caught that this renderer previously dropped it silently even
    when present. Empty (no clause at all) when there is genuinely nothing
    to say — the `<dl>` header (`_render_release_figures`) always shows a
    row instead, via `_work_types_value` directly."""
    wt = release.get("work_types")
    if wt is None or wt["value"] is None:
        return ""
    return f" Work types: {_work_types_value(release)}."


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


def _real_stats_line(release: dict) -> str:
    """AC-1.1/1.2 (T1) + AC-1.3 (T2): a real release's own tag date and
    commit count — the Must-level counterpart to `_pseudo_stats_line`,
    reading `build_release_map`'s own `date`/`commit_count`/`work_types`
    figures verbatim, never recomputed a second way. One `_esc` over the
    whole sentence, same NFR-2 discipline as `_pseudo_stats_line`."""
    date = release.get("date")
    date_reason = release.get("date_reason") or "date unavailable"
    # Review F6: the null branch must terminate its own sentence too, or the
    # reason runs straight into the commit count ("...could not be read 1 commit.").
    date_clause = f"Tagged {date}." if date is not None else f"{date_reason}."
    commit_count = release["commit_count"]
    commit_word = "commit" if commit_count == 1 else "commits"
    work_types_clause = _work_types_clause(release)
    return _esc(f"{date_clause} {commit_count} {commit_word}.{work_types_clause}")


def _delivery_clause(member: dict) -> str:
    """US-2/AC-2.1: `delivery` is a machine-readable field on `member`
    (`build_release_map`'s own attribution, never re-derived here),
    rendered as a plain-text label — "Delivering"/"Trailing" — never a
    color- or icon-only cue. Carries the member's own `scope` (AC-3.6) so
    a reader sees the number this member itself contributes, or its
    honest null, next to the label."""
    delivery = member["delivery"]
    scope = member["scope"]
    scope_text = (
        _scope_text(scope["us"], scope["acs"]) if scope["us"] is not None
        else _esc(scope["reason"] or "scope unavailable")
    )
    if delivery["delivering"]:
        return f'<p class="stats-line">Delivering &mdash; {scope_text}.</p>\n'
    if delivery["delivered_in"] is not None:
        return (
            '<p class="stats-line">Trailing &mdash; delivered in '
            f'<code>{_esc(delivery["delivered_in"])}</code>.</p>\n'
        )
    return f'<p class="stats-line">{_esc(delivery["reason"])}</p>\n'


def _trailing_note(member: dict) -> str:
    """AC-2.7: a release card must never juxtapose a trailing member's
    full, current document with a `0`-delivered figure and no
    explanation. This note names the actual delivery release explicitly,
    and is prepended in every one of the three document-viewing states
    (embedded, linked-elsewhere, over-budget — T5 DoD), never only one of
    them. Absent for a delivering member and for the pseudo-release's own
    "not yet delivered" members (`delivered_in is None`) — there is no
    delivery release to name in either case."""
    delivery = member["delivery"]
    if delivery["delivering"] or delivery["delivered_in"] is None:
        return ""
    return (
        '<p class="doc-provenance">Trailing member &mdash; delivered in '
        f'<code>{_esc(delivery["delivered_in"])}</code>; document shown as currently written.</p>\n'
    )


def _delivering_summary_line(release: dict) -> str:
    """AC-2.6: a real release's delivering-member count, stated in words,
    distinct from the member list itself (a trailing member still gets
    its own block below — AC-2.1/AC-2.7) so an empty delivering set is
    never conflated with the list being empty or a `null`+reason state.
    Wording matches AC-2.6's own quoted text exactly."""
    delivering = [m for m in release["members"] if m["delivery"]["delivering"]]
    if not delivering:
        return '<p class="stats-line">no feature was delivered in this release.</p>\n'
    names = ", ".join(_esc(m["name"]) for m in delivering)
    count_word = "feature" if len(delivering) == 1 else "features"
    return f'<p class="stats-line">{len(delivering)} {count_word} delivered: {names}.</p>\n'


def _render_release_figures(release: dict) -> str:
    """US-4/AC-4.1: a real release's own per-card figures header — date,
    gap to its predecessor (or its `null` reason, never a `0` — AC-4.2),
    delivering vs. trailing features, delivered scope, commit count,
    unattributed count, and work-type mix. One `<dl>` pass over
    `build_release_map`'s own figures, nothing recomputed. Its own render
    unit, called from exactly one line of `_render_release_detail` (plan
    §1's severability decision — AC-4.4)."""
    date = release.get("date")
    date_display = date if date is not None else (release.get("date_reason") or "unavailable")

    gap = release.get("gap_days")
    gap_display = f"{gap} d" if gap is not None else (release.get("gap_days_reason") or "unavailable")

    members = release["members"]
    delivering = [m for m in members if m["delivery"]["delivering"]]
    trailing = [
        m for m in members
        if not m["delivery"]["delivering"] and m["delivery"]["delivered_in"] is not None
    ]
    delivering_display = ", ".join(m["name"] for m in delivering) if delivering else "none"
    trailing_display = ", ".join(m["name"] for m in trailing) if trailing else "none"

    scope = release["delivered_scope"]
    # review F1: `n`/`unreadable` were computed by `_delivered_scope` and
    # then discarded here — a partially-unreadable scope rendered as a
    # complete-looking number with no disclosure (AC-3.6). Now always
    # visible, mirroring the band's own `scope_unreadable` note.
    if scope["us"] is not None:
        scope_display = f"{_scope_text(scope['us'], scope['acs'])} (n={scope['n']} of {len(delivering)} delivering)"
    else:
        scope_display = scope["reason"] or "unavailable"
    if scope["unreadable"]:
        scope_display += f"; unreadable: {', '.join(scope['unreadable'])}"

    wt_display = _work_types_value(release)

    rows = "".join(
        f"<dt>{_esc(label)}</dt>\n<dd>{_esc(str(value))}</dd>\n"
        for label, value in (
            ("Date", date_display),
            ("Gap to predecessor", gap_display),
            ("Delivering", delivering_display),
            ("Trailing", trailing_display),
            ("Delivered scope", scope_display),
            ("Commits", release["commit_count"]),
            ("Unattributed commits", len(release["unattributed"])),
            ("Work types", wt_display),
        )
    )
    return f'<dl class="figures-band release-figures">\n{rows}</dl>\n'


def _render_release_detail(
    release: dict, index: int, *,
    plan: dict | None = None, documents: dict | None = None, releases: list[dict] | None = None,
) -> str:
    anchor = _release_anchor(index)
    label = _release_label(release)
    is_pseudo = release["tag"] is None
    pseudo_marker = '<span class="pseudo-marker">open window</span>' if is_pseudo else ""
    if is_pseudo:
        stats_line = f'<p class="stats-line">{_pseudo_stats_line(release)}</p>\n'
        figures_header = ""
        delivering_summary = ""
    else:
        stats_line = f'<p class="stats-line">{_real_stats_line(release)}</p>\n'
        figures_header = _render_release_figures(release)  # US-4, AC-4.4: single call site
        delivering_summary = _delivering_summary_line(release)
    return (
        f'<article class="release-card" id="{_esc(anchor)}">\n'
        f'<a class="back-link" href="#index">&larr; Back to index</a>\n'
        f"<h2>{_esc(label)}{pseudo_marker}</h2>\n"
        f"{stats_line}"
        f"{figures_header}"
        "<h3>Members</h3>\n"
        f"{delivering_summary}"
        f"{_render_members_section(release, original_index=index, plan=plan, documents=documents, releases=releases)}"
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


def _display_order(releases: list[dict]) -> list[tuple[int, dict]]:
    """US-1/AC-1.1: newest-first — every pseudo-release (`tag is None`)
    first, in its own original relative order, then every real tag reversed
    (newest tag first, oldest last). Partitioned by the `tag is None`
    discriminator, never by position — `releases[]` itself (and
    `--format json`'s stdout) keeps its own oldest-first/pseudo-last order
    completely untouched (AC-1.3, ADR-0: a display-order flip, never a
    re-derivation). Each entry's original `releases[]` index travels with
    it so anchors (`rel-N`) still identify the same underlying entry
    regardless of display order (AC-1.1/1.2)."""
    indexed = list(enumerate(releases))
    pseudo = [(i, r) for i, r in indexed if r["tag"] is None]
    real = [(i, r) for i, r in indexed if r["tag"] is not None]
    return pseudo + list(reversed(real))


def _render_masthead() -> str:
    return (
        '<div class="masthead">\n'
        f'<img src="{LOGO_DATA_URI}" alt="aSPARK" width="121" height="40">\n'
        "</div>\n"
    )


def _render_page_budget_notice(plan: dict | None) -> str:
    """Review F7: T4's DoD promised a page-level disclosure of how many
    documents the weight budget left out — the per-member notice alone
    (`_render_documents_for_member`) never summed to a page-wide count.
    Consumption stays best-fit (deterministic, still <= budget — a later,
    smaller feature can still fit after a larger one didn't), rather than
    a hard stop; this notice is what makes that behavior honestly
    disclosed rather than silently different from what the plan
    described."""
    if not plan:
        return ""
    skipped = [name for name, entry in plan.items() if not entry["embedded"]]
    if not skipped:
        return ""
    names = ", ".join(f"{_SPARK_DIRNAME}/{_esc(n)}/" for n in sorted(skipped))
    count_word = "feature's" if len(skipped) == 1 else "features'"
    return (
        f'<p class="truncation-note">{len(skipped)} {count_word} documents were not embedded '
        f"in this page &mdash; the page-weight budget was reached before reaching them. "
        f"Read them directly at: {names}.</p>\n"
    )


def _render_figures_band(data: dict) -> str:
    """US-3/AC-3.1: the global figures band, above the release index — one
    formatting pass over `build_release_map()`'s own top-level `figures`
    dict, nothing recomputed (ADR-0). AC-3.5: a zero-tag repo states its
    reason and shows no figures. AC-3.4: one unreadable figure shows
    `null`+reason while every other still renders. A `<dl>` — real
    programmatic label/value pairing, reusing the shipped `.index-list`
    auto-fit grid idiom for the 375px multi-row wrap (design finding 4)."""
    figures = data.get("figures")
    if figures is None:
        return f'<p class="empty-notice">{_esc(data.get("reason") or "no releases found")}</p>\n'

    def cell(label: str, value, reason: str | None = None) -> str:
        display = value if value is not None else (reason or "unavailable")
        return f"<dt>{_esc(label)}</dt>\n<dd>{_esc(str(display))}</dd>\n"

    gap_range = (
        f"{figures['gap_min']}–{figures['gap_max']} d"
        if figures["gap_min"] is not None else None
    )
    # review F11: `_median` always returns `float` (so an even-`n` fractional
    # median like `1.5` prints correctly) — but AC-3.1's own stated example
    # is the bare integer `2`, not `2.0`. Display-only: drops a whole
    # number's trailing `.0` without touching the JSON value or the
    # underlying float itself.
    gap_median = figures["gap_median"]
    gap_median_text = None
    if gap_median is not None:
        gap_median_text = str(int(gap_median)) if gap_median == int(gap_median) else str(gap_median)
    gap_median_display = f"{gap_median_text} d" if gap_median_text is not None else None
    scope_display = (
        _scope_text(figures['delivered_us'], figures['delivered_acs'])
        if figures["delivered_us"] is not None else None
    )
    # review F1: the `n` beside the label — how many of `features_delivered`
    # actually contributed to this total — so a partial count (some
    # delivering members unreadable, but not ALL of any single release's
    # own set) is visible next to the number, not only inferable from the
    # `scope_unreadable` note below.
    scope_label = f"Delivered scope (n={figures['delivered_scope_n']} of {figures['features_delivered']} delivering)"
    rows = "".join([
        cell("Tagged releases", figures["release_count"]),
        cell("First release", figures["first_date"], "date unavailable"),
        cell("Last release", figures["last_date"], "date unavailable"),
        cell(f"Median gap (n={figures['gap_n']})", gap_median_display, "not enough measured gaps"),
        cell("Gap range", gap_range, "not enough measured gaps"),
        cell("Features delivered", figures["features_delivered"]),
        cell(scope_label, scope_display, "scope unavailable"),
        cell("Commits since last release", figures["open_window_commit_count"], "unavailable"),
    ])
    unreadable_note = ""
    if figures["scope_unreadable"]:
        names = ", ".join(_esc(n) for n in figures["scope_unreadable"])
        unreadable_note = f'<p class="truncation-note">Scope unreadable for: {names}.</p>\n'
    return f'<dl class="figures-band">\n{rows}</dl>\n{unreadable_note}'


def _cadence_bar_width_pct(gap: int, gap_max: int) -> int:
    if gap_max <= 0:
        return 0
    return max(0, min(100, round((gap / gap_max) * 100)))


def _render_cadence_strip(releases: list[dict]) -> str:
    """US-3/AC-3.2/AC-3.3/AC-3.4/AC-3.7: real releases oldest-first, one row
    per gap SLOT — every real release except the earliest has one, whether
    or not its own gap turned out measurable. Never the pseudo-release's
    own age (A7). Exactly two states, never a third (AC-3.7): **present**
    shows every slot — a plain number plus a uniform-hue bar for a
    measured gap, or `null`+its own reason with no bar for an unmeasurable
    one (AC-3.4; review F2 — an unmeasurable gap used to be silently
    dropped from the table instead of shown as unmeasurable, which could
    also mislabel the wrong row "longest") — or **absent** entirely, with
    a reason naming `n` (AC-3.3, refuses itself below 2 gap slots — a
    single slot cannot depict a shape). The "longest" mark (review F7 —
    previously applied to every tied row, including an all-zero set) is
    shown only when every slot in the set is measured, there is exactly
    one maximum, and it is greater than zero — by rank/text weight only,
    never by color; no connecting line, curve or averaged value is ever
    drawn."""
    real = [r for r in releases if r["tag"] is not None]
    gap_slots = real[1:]  # the earliest real release has no predecessor gap
    if len(gap_slots) < 2:
        # Re-review F14: `n` here is the number of release-to-release gap
        # SLOTS, which since F2's rewrite is no longer the same quantity as
        # the number of *measured* gaps — with 2 tags and one unreadable tag
        # date this said "not enough measured gaps (n=1)" while zero were
        # actually measured, overstating measurement on the one surface
        # AC-3.3 governs. Named for what it counts.
        return (
            '<p class="empty-notice">Not enough release-to-release gaps to show a cadence '
            f"strip (n={len(gap_slots)}).</p>\n"
        )
    known_gaps = [r["gap_days"] for r in gap_slots if r["gap_days"] is not None]
    gap_max = max(known_gaps) if known_gaps else None
    all_known = len(known_gaps) == len(gap_slots)
    show_longest = all_known and gap_max is not None and gap_max > 0 and known_gaps.count(gap_max) == 1

    row_htmls = []
    for r in gap_slots:
        gap = r["gap_days"]
        if gap is None:
            gap_cell = _esc(r.get("gap_days_reason") or "unavailable")
            bar_cell = ""
        else:
            is_longest = show_longest and gap == gap_max
            gap_cell = f"<strong>{gap} d (longest)</strong>" if is_longest else f"{gap} d"
            width_pct = _cadence_bar_width_pct(gap, gap_max)
            bar_cell = f'<span class="cadence-bar" style="width:{width_pct}%"></span>'
        row_htmls.append(
            "<tr>"
            f"<td>{_esc(r['previous_tag'])} &rarr; {_esc(r['tag'])}</td>"
            f"<td>{gap_cell}</td>"
            f"<td>{bar_cell}</td>"
            "</tr>\n"
        )
    body = "".join(row_htmls)
    caption = "Cadence between releases"
    if not all_known:
        caption += f" ({len(known_gaps)} of {len(gap_slots)} measured)"
    return (
        '<div class="table-wrap">\n<table>\n'
        f"<caption>{_esc(caption)}</caption>\n"
        '<thead><tr><th scope="col">From &rarr; To</th><th scope="col">Gap (days)</th>'
        '<th scope="col">Relative</th></tr></thead>\n'
        f"<tbody>\n{body}</tbody>\n"
        "</table>\n</div>\n"
    )


def render_release_board_html(data: dict, documents: dict | None = None) -> str:
    """Pure — `build_release_map()` dict (and, optionally, an already-read
    `documents` dict from `artifactcontent.collect_release_documents`) in,
    HTML string out, no I/O/clock/randomness of its own (NFR-6's
    determinism substrate, the unit-test seam). Zero JavaScript, static
    same-document `#`-anchor drill-down (A4). `documents=None` (the
    default) renders byte-identically to before US-2 existed — no document
    section, no plan computed. `documents={}` is a *different* case (review
    F14, corrected here): a plan IS computed, so every member still gets
    its 5-artifact `<details>` section, each honestly stating "no document
    collected for this render" (`_render_document_details`'s own
    placeholder) rather than the capability silently vanishing.

    Review F10: `data`'s accepted shape narrowed at `0.11.0` — every real
    release now requires its own `figures`/`date`/`commit_count`/
    `delivered_scope`, and every member its own `delivery`/`scope`
    (`build_release_map()`'s own current output; see `releasemap.py`'s
    module docstring). A `0.10.0`-shaped dict missing these keys raises
    `KeyError`/`AttributeError` here — this function is pure and does not
    itself catch that; callers wanting a named error instead of a raw
    exception should go through `run_release_board_report`, which wraps
    exactly those classes into `ReleaseMapUnreadableError`."""
    releases = data["releases"]

    if not releases:
        # AC-3.1/AC-3.5: zero tags — the band states the reason in words,
        # an empty index, never a traceback, a blank page, or a
        # placeholder row.
        body = _render_figures_band(data)
    else:
        order = _display_order(releases)
        plan = _document_plan(order, documents, _PAGE_DOCUMENT_BUDGET_BYTES) if documents is not None else None
        index_rows = "".join(_render_index_row(r, i) for i, r in order)
        details = "".join(
            _render_release_detail(r, i, plan=plan, documents=documents, releases=releases)
            for i, r in order
        )
        count_word = "release" if len(releases) == 1 else "releases"
        body = (
            "<h2>Overview</h2>\n"
            f"{_render_figures_band(data)}"
            "<h2>Cadence</h2>\n"
            f"{_render_cadence_strip(releases)}"
            f'<p class="lead">{len(releases)} {count_word}, newest first.</p>\n'
            f'<ul class="index-list" id="index">\n{index_rows}</ul>\n'
            f"{_render_page_budget_notice(plan)}"
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


def run_release_board_report(data: dict, output: str, documents: dict | None = None) -> Path:
    """Writes `<output>/.aspark-insights/release-board.html`, returns its
    resolved absolute path. Same F1-class safety net `render.py`/`report.py`
    both apply: a malformed data dict must never escape as a raw traceback
    (constitution §6). Review F1: the write itself is equally hostile-input-
    exposed (`--output` pointing at an existing file, or an unwritable
    path) — wrapped in its own guard so a bad *destination* fails exactly
    as cleanly as bad *data*, never a raw `OSError` traceback."""
    try:
        text = render_release_board_html(data, documents)
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
