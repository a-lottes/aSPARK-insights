"""report — self-contained HTML rendering of a `build_board()` dict (US-4).

Imports `_esc`/`_STYLE` from `render.py` so the escaping choke-point and the
just-verified palette are the *literal* same code, never a copy (AC-4.7) —
but builds its own markup rather than reusing the metric-shaped card/table
builders, which assume `metric_id`/`n`/`reason` fields a board entry doesn't
honestly have.
"""

from __future__ import annotations

from pathlib import Path

from aspark_insights.errors import BoardUnreadableError
from aspark_insights.gitboard.worktype import RECOGNIZED_TYPES, classify
from aspark_insights.render import _esc, _STYLE
from aspark_insights.store import STORE_DIRNAME

REPORT_FILENAME = "board.html"

# Reuses only colors already verified elsewhere in this project's own
# rendered output (render.py's `.stale-cue`/`.null-value`/`.metric-*`
# palette) — no new color pair this module introduces needs a fresh
# /demo-day contrast measurement.
_BOARD_STYLE = """
  .interim-marker { border: 1px solid #999; background: #f7f7f7; padding: 0.4rem 0.6rem; font-weight: 700; font-size: 0.85rem; margin: 0 0 0.75rem; }
  .answer-sentence { font-size: 1rem; margin: 0 0 1rem; }
  .badge { display: inline-block; font-size: 0.75rem; font-weight: 700; color: #1a1a1a; background: #f0f0f0; padding: 0.1rem 0.4rem; border-radius: 3px; }
  .badge--unclassified { background: #fff; border: 1px dashed #999; color: #444; }
  .commit-list { list-style: none; padding: 0; margin: 0.75rem 0; }
  .commit-item { border: 1px solid #ccc; border-radius: 6px; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem; }
  .commit-item dl { display: grid; grid-template-columns: auto 1fr; gap: 0.2rem 0.6rem; margin: 0; }
  .commit-item dt { font-size: 0.75rem; color: #666; font-weight: 600; }
  .commit-item dd { margin: 0; font-size: 0.9rem; }
  .truncation-note { font-size: 0.82rem; color: #444; font-style: italic; margin: 0.4rem 0 0; }
  #provenance dl { display: grid; grid-template-columns: auto 1fr; gap: 0.3rem 1rem; }
  #provenance dt { color: #666; font-size: 0.85rem; }
  #provenance dd { margin: 0; font-size: 0.9rem; }
"""


def _render_interim_marker() -> str:
    """AC-4.5(b): legible near the top, unscrolled, as a labelled line.
    Neutral provenance styling — never `.stale-cue`'s alarm geometry — this
    is a status fact ("this is the ADR-2 fallback"), not a warning."""
    return (
        '<p class="interim-marker">INTERIM (git-native) &mdash; measured from '
        "local git only; superseded once the graph reports release data.</p>\n"
    )


def _pluralize(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def _answer_sentence_text(board: dict) -> str:
    """AC-4.8: one plain-language sentence, degenerate states stated in
    words — never a silently-omitted clause, never a `null`/`—` placeholder,
    and never a second explanation for a cause AC-1.2 already covers once."""
    tag = board["provenance"]["resolved_tag"]
    commits = board["commits"]
    branches = board["branches"]

    days = board.get("days_since_tag", {}).get("value")
    days_clause = f", {_pluralize(days, 'day')} ago" if days is not None else ""

    if tag is None:
        commit_clause = "This repository has no tags, so there is no release marker to measure against."
    elif commits["value"] == 0:
        tagged_suffix = days_clause.lstrip(", ")  # ", 6 days ago" -> "6 days ago"
        commit_clause = (
            f"Nothing has landed since {tag}, tagged {tagged_suffix}."
            if tagged_suffix else f"Nothing has landed since {tag}."
        )
    else:
        qualifier = "At least " if board["provenance"]["shallow"] else ""
        count_words = _pluralize(commits["value"], "commit")
        commit_clause = f"{qualifier}{count_words} landed since {tag}{days_clause}."

    if not branches:
        branch_clause = "No local branches found."
    else:
        oldest = max(branches, key=lambda b: b["age_days"] if b["age_days"] is not None else -1)
        branch_count_words = _pluralize(len(branches), "local branch")
        if oldest["age_days"] is None:
            branch_clause = f"{branch_count_words}, oldest age could not be read."
        else:
            branch_clause = f"{branch_count_words}, oldest moved {_pluralize(oldest['age_days'], 'day')} ago."

    return f"{commit_clause} {branch_clause}"


def _render_answer_sentence(board: dict) -> str:
    return f'<p class="answer-sentence">{_esc(_answer_sentence_text(board))}</p>\n'


def _render_stat_card(label: str, value: object, reason: str | None) -> str:
    """Reuses the scorecard's honest-null card shape (AC-4.2/AC-4.7) — the
    same `.metric-card--null`/`.null-value` treatment, not a fourth
    vocabulary for one state."""
    if value is None:
        return (
            '<div class="metric-card metric-card--null">\n'
            f'<p class="metric-label">{_esc(label)}</p>\n'
            '<p class="metric-value metric-value--null null-value">Not computed</p>\n'
            f'<p class="metric-reason">{_esc(reason)}</p>\n'
            "</div>\n"
        )
    return (
        '<div class="metric-card">\n'
        f'<p class="metric-label">{_esc(label)}</p>\n'
        f'<p class="metric-value">{_esc(value)}</p>\n'
        "</div>\n"
    )


def _render_stat_cards(board: dict) -> str:
    """AC-4.9: absent figure -> no card at all; null -> dashed card; true
    zero -> a real `0` value card. Four headline figures, in order."""
    cards = []
    commits = board["commits"]
    cards.append(_render_stat_card("Commits since tag", commits["value"], commits["reason"]))

    if "days_since_tag" in board:  # absent (AC-1.10(a)) -> no card, not a null card
        d = board["days_since_tag"]
        cards.append(_render_stat_card("Days since tag", d["value"], d["reason"]))

    branches = board["branches"]
    cards.append(_render_stat_card("Local branches", len(branches), None))  # always a real value, 0 included

    if branches:  # no branches -> no "oldest age" card: nothing to measure
        oldest = max(branches, key=lambda b: b["age_days"] if b["age_days"] is not None else -1)
        cards.append(_render_stat_card("Oldest branch age (days)", oldest["age_days"], oldest["age_reason"]))

    return '<div class="metric-grid">\n' + "".join(cards) + "</div>\n"


def _render_work_types_section(board: dict) -> str:
    """AC-4.13: an *absent* work-type figure (no tag, or 0 commits since tag)
    omits this whole block — heading included — never an empty labelled
    section."""
    if "work_types" not in board:
        return ""
    wt = board["work_types"]
    if wt["value"] is None:
        body = (
            '<div class="metric-card metric-card--null">\n'
            '<p class="metric-label">Work-type mix</p>\n'
            '<p class="metric-value metric-value--null null-value">Not computed</p>\n'
            f'<p class="metric-reason">{_esc(wt["reason"])}</p>\n'
            "</div>\n"
        )
    else:
        # AC-4.11: `.confidence-mix`'s shipped pattern (single fill, hairline
        # separators, adjacent legend) — per-segment inline labels are
        # unrenderable at this scale (spec §8 finding 14). Fixed declared
        # order, `unclassified` last; zero-count types already absent from
        # `breakdown()`'s own output.
        order = (*RECOGNIZED_TYPES, "unclassified")
        present = [(t, wt["value"][t]) for t in order if t in wt["value"]]
        segments = "".join(
            f'<div class="confidence-seg" style="width:{pct:d}%"></div>\n' for _, pct in present
        )
        legend = " &middot; ".join(f"{_esc(t)} {_esc(pct)}%" for t, pct in present)
        body = (
            '<div class="confidence-mix">\n'
            f'<div class="confidence-bar">\n{segments}</div>\n'
            f'<p class="confidence-legend">{legend}</p>\n'
            "</div>\n"
        )
    return '<section id="work-types">\n<h2>Work types</h2>\n' + body + "</section>\n"


def _render_commits_section(board: dict) -> str:
    """AC-4.12(b): a scannable list, each item a `<dl>` naming Type, Subject,
    Hash and Date explicitly — not visual order alone. The type badge is the
    one genuinely new primitive `render.py` has no precedent for (AC-4.7)."""
    commits = board["commits"]
    if commits["value"] is None:
        body = f'<p class="empty-notice">{_esc(commits["reason"])}</p>\n'
    elif commits["value"] == 0:
        body = '<p class="empty-notice">No commits since the resolved tag.</p>\n'
    else:
        items = []
        for c in commits["shown"]:
            wtype = classify(c["subject"])
            badge = (
                f'<span class="badge">{_esc(wtype)}</span>' if wtype
                else '<span class="badge badge--unclassified">unclassified</span>'
            )
            items.append(
                '<li class="commit-item">\n<dl>\n'
                f"<dt>Type</dt><dd>{badge}</dd>\n"
                f'<dt>Subject</dt><dd>{_esc(c["subject"])}</dd>\n'
                f'<dt>Hash</dt><dd>{_esc(c["hash"])}</dd>\n'
                f'<dt>Date</dt><dd>{_esc(c["date"])}</dd>\n'
                "</dl>\n</li>\n"
            )
        body = '<ul class="commit-list">\n' + "".join(items) + "</ul>\n"
        if commits["truncated"]:
            body += (
                f'<p class="truncation-note">Showing the most recent {_esc(commits["shown_count"])} '
                f'of {_esc(commits["value"])}.</p>\n'
            )
    return '<section id="commits">\n<h2>Commits</h2>\n' + body + "</section>\n"


def _render_branches_section(board: dict) -> str:
    """AC-4.12(a)(d): the branch listing stays a real `<table>` with
    `<th scope="col">` + `<caption>` — the age *cell* becomes a magnitude bar
    (`.metric-bar`, the shipped reference), but always carries its numeric
    age as text alongside, never bar length alone."""
    branches = board["branches"]
    if not branches:
        return '<section id="branches">\n<h2>Branches</h2>\n<p class="empty-notice">No local branches found.</p>\n</section>\n'

    known_ages = [b["age_days"] for b in branches if b["age_days"] is not None]
    max_age = max(known_ages) if known_ages else 0
    rows = []
    for b in branches:
        if b["age_days"] is None:
            age_cell = f'<span class="null-value">Not computed: {_esc(b["age_reason"])}</span>'
        else:
            pct = round(b["age_days"] / max_age * 100) if max_age > 0 else 0
            age_cell = (
                f'{_esc(_pluralize(b["age_days"], "day"))}'
                f'<div class="metric-bar"><div class="metric-bar-fill" style="width:{pct}%"></div></div>'
            )
        rows.append(
            "<tr>"
            f"<td>{_esc(b['name'])}</td>"
            f"<td>{_esc(b['tip_hash'])}</td>"
            f"<td>{_esc(b['tip_date'])}</td>"
            f"<td>{age_cell}</td>"
            "</tr>"
        )
    body = "\n".join(rows)
    return (
        '<section id="branches">\n<h2>Branches</h2>\n'
        '<div class="table-wrap">\n<table>\n<caption>Branches</caption>\n'
        "<thead><tr>"
        '<th scope="col">Branch</th><th scope="col">Tip</th>'
        '<th scope="col">Tip date</th><th scope="col">Age</th>'
        "</tr></thead>\n"
        f"<tbody>\n{body}\n</tbody>\n"
        "</table>\n</div>\n</section>\n"
    )


def _render_provenance_section(board: dict) -> str:
    """AC-4.6 (the Blocker's fix): every trust-bearing field renders here on
    *every* report — `<dl>` field/value pairing, programmatic, not visual
    adjacency alone."""
    prov = board["provenance"]
    resolved_tag_value = prov["resolved_tag"] if prov["resolved_tag"] is not None \
        else f"(none) — {prov['resolved_tag_reason']}"
    rows = [
        ("as_of", prov["as_of"]),
        ("insights_version", prov["insights_version"]),
        ("source", prov["source"]),
        ("git_available", prov["git_available"]),
        ("resolved_tag", resolved_tag_value),
        ("shallow", prov["shallow"]),
    ]
    commits = board["commits"]
    if commits.get("truncated"):
        rows.append(("commits.truncated", f"showing {commits['shown_count']} of {commits['value']}"))
    if "work_types" in board and board["work_types"]["value"] is None:
        rows.append(("work_types.reason", board["work_types"]["reason"]))

    items = "".join(f"<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>\n" for k, v in rows)
    return f'<section id="provenance">\n<h2>Provenance</h2>\n<dl>\n{items}</dl>\n</section>\n'


def render_board_html(board: dict) -> str:
    """Pure — board dict in, HTML string out, no I/O/clock/randomness. Block
    order is fixed and byte-offset-checkable (AC-4.13): `<h1>` -> interim
    marker -> answer sentence -> stat cards -> Work types -> Commits ->
    Branches -> Provenance. A block whose content is absent (Work types on a
    tagless/zero-commit repo) omits its own `<h2>` with it."""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Insights Mid-Cycle Board</title>\n"
        f"<style>{_STYLE}{_BOARD_STYLE}</style>\n"
        "</head>\n"
        "<body>\n"
        "<h1>Mid-Cycle Board</h1>\n"
        + _render_interim_marker()
        + _render_answer_sentence(board)
        + _render_stat_cards(board)
        + _render_work_types_section(board)
        + _render_commits_section(board)
        + _render_branches_section(board)
        + _render_provenance_section(board)
        + "</body>\n"
        "</html>\n"
    )


def run_board_report(board: dict, output: str) -> Path:
    """Writes `<output>/.aspark-insights/board.html`, returns its resolved
    absolute path (AC-4.4)."""
    try:
        text = render_board_html(board)
    except (AttributeError, KeyError, TypeError) as exc:
        # Same F1-class guard `render.py`'s own run_render applies: a
        # malformed board dict must never escape as a raw traceback.
        raise BoardUnreadableError(f"board data has an unexpected shape: {exc}") from exc
    out_path = Path(output) / STORE_DIRNAME / REPORT_FILENAME
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path.resolve()
