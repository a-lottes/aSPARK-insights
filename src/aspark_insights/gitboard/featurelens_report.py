"""featurelens_report — self-contained HTML rendering of a
`build_feature_lens()` dict (feature-lens US-1/US-2/US-3).

Imports `_STYLE`/`_ARTIFACT_HUES`/`_strip_status_backticks`/`_render_masthead`
from `releaseboard_report.py` and `_esc` from `render.py` rather than forking
them — the same cross-module private-choke-point import the release board
itself already makes for `_esc`. Page CSS is the shipped `_STYLE` plus an
additive `_LENS_STYLE`: the release board's own bytes, and its determinism/
contrast tests, are untouched by this module's existence (NFR-2/R3).
"""

from __future__ import annotations

from pathlib import Path

from aspark_insights.errors import ReleaseMapUnreadableError, ReportUnwritableError
from aspark_insights.gitboard.featurelens import group_by_gate
from aspark_insights.gitboard.releaseboard_report import (
    _ARTIFACT_HUES,
    _ARTIFACT_NAMES,
    _STYLE,
    _render_masthead,
    _strip_status_backticks,
)
from aspark_insights.render import _esc
from aspark_insights.store import STORE_DIRNAME

REPORT_FILENAME = "feature-lens.html"

_COLUMN_HEADERS = (
    "Feature",
    "spec.md's own Date (last updated)",
    "Spec",
    "Plan",
    "Review",
    "QA",
    "Release",
    "Gate",
    "Delivered In",
)

# AC-2.1/2.5/3.1: one uniform, non-artifact hue for the gate badge and the
# pipeline section — never a per-gate-value color, extending
# `_ARTIFACT_HUES`'s hue-keyed-to-type-never-status rule to this field.
_LENS_STYLE = """
  /* QA B1: `overflow-wrap: anywhere` alone gives the browser's table-layout
     algorithm license to shrink every column arbitrarily far below its
     `max-width` — at 375px this crushed all nine columns to 33-53px,
     wrapping every header and most values one character per line. A
     `min-width` floor keeps each column at a genuinely readable width,
     forcing the table's natural width past the viewport so the shipped
     `.table-wrap { overflow-x: auto }` container actually engages and
     scrolls horizontally — the page itself still never scrolls (NFR-4's
     literal bar), and `overflow-wrap: anywhere` remains as a safety net
     for one truly long unbroken token (a hostile fixture's payload)
     rather than the mechanism ordinary column widths depend on. Per
     plan.md's own R4: the fallback is a readable, scrollable table
     container, never a wider page. */
  .lens-table { min-width: 62rem; }
  .lens-table th, .lens-table td { overflow-wrap: anywhere; max-width: 22ch; min-width: 9ch; }
  .lens-table th:first-child, .lens-table td:first-child { max-width: 28ch; min-width: 12ch; }
  .gate-badge { display: inline-block; font-size: 0.75rem; font-weight: 700; padding: 0.15rem 0.55rem;
    border-radius: 100px; background: var(--bg-secondary); border: 1px solid var(--accent-teal);
    color: var(--accent-teal); }
  .gate-evidence { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem; }
  .pipeline-section h3 { font-size: 0.95rem; margin: 1.5rem 0 0.5rem; }
  .pipeline-list { list-style: none; padding: 0; margin: 0.5rem 0; display: grid; gap: 0.4rem; }
  .pipeline-list li { background: var(--bg-card); border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm); padding: 0.5rem 0.8rem; font-size: 0.9rem; }
"""


def _status_badge(artifact: str, entry: dict) -> str:
    """Compact type+status badge, reusing `_ARTIFACT_HUES` (color by
    artifact type, never by status value) — the same visual vocabulary
    `_render_artifact_table` uses, without its own surrounding `<table>`.
    The reason renders only when `status` is `null` (AC-1.5) — never
    duplicated alongside a plain-word status like `approved`."""
    status = entry["status"]
    hue = _ARTIFACT_HUES[artifact]
    if status is None:
        reason = entry["reason"] or "status unavailable"
        return (
            f'<span class="badge" style="color:{hue}">{_esc(artifact)}</span>'
            f'<span class="badge-reason">{_esc(reason)}</span>'
        )
    return f'<span class="badge" style="color:{hue}">{_esc(artifact)}</span> {_esc(_strip_status_backticks(status))}'


def _gate_evidence_text(evidence: list[dict]) -> str:
    parts = []
    for e in evidence:
        artifact = e["artifact"]
        if e["reason"] is not None:
            parts.append(f"{artifact}: {e['reason']}")
        else:
            parts.append(f"{artifact}: {_strip_status_backticks(e['status'])}")
    return ", ".join(parts)


def _render_gate_cell(feature: dict) -> str:
    """AC-2.1/2.5: one uniform badge class regardless of gate value — never
    a progress bar, step-tracker, or dot-track, and never a per-value hue —
    always paired with the literal artifact evidence it was derived from."""
    gate = feature["gate"]
    evidence = _gate_evidence_text(feature["gate_evidence"])
    return (
        f'<span class="gate-badge">{_esc(gate)}</span>'
        f'<span class="gate-evidence">{_esc(evidence)}</span>'
    )


def _render_feature_row(feature: dict) -> str:
    date_display = feature["spec_date"] if feature["spec_date"] is not None else (feature["spec_date_reason"] or "unavailable")
    delivered_display = feature["delivered_in"] if feature["delivered_in"] is not None else (feature["delivered_in_reason"] or "unavailable")
    cells = [
        f"<td>{_esc(feature['name'])}</td>",
        f"<td>{_esc(date_display)}</td>",
    ]
    cells.extend(f"<td>{_status_badge(a, feature['status'][a])}</td>" for a in _ARTIFACT_NAMES)
    cells.append(f"<td>{_render_gate_cell(feature)}</td>")
    cells.append(f"<td>{_esc(delivered_display)}</td>")
    return "<tr>" + "".join(cells) + "</tr>\n"


def _render_features_table(features: list[dict]) -> str:
    header_cells = "".join(f'<th scope="col">{_esc(h)}</th>' for h in _COLUMN_HEADERS)
    rows = "".join(_render_feature_row(f) for f in features)
    return (
        '<div class="table-wrap">\n<table class="lens-table">\n'
        f"<thead><tr>{header_cells}</tr></thead>\n"
        f"<tbody>\n{rows}</tbody>\n"
        "</table>\n</div>\n"
    )


def _render_pipeline_section(features: list[dict]) -> str:
    """AC-3.1/3.2: plain headed groups, never a progress/step device. Every
    bucket — empty or populated — gets the same `<h3>` + section chrome; an
    empty bucket uses the shipped `.empty-notice` idiom with the same
    structural weight as a populated one, never dimmed or collapsed.

    Review F7: each list item also carries its own gate evidence (the same
    text the table's gate cell shows) — NFR-5's "never shown without the
    literal status string it was derived from" applies here too, not only
    in the table; a bare feature name under a `<h3>Increment</h3>` heading
    would otherwise be the one place a gate appears without evidence."""
    buckets = group_by_gate(features)
    parts = ['<div class="pipeline-section">\n<h2>Pipeline</h2>\n']
    for gate, members in buckets:
        parts.append(f"<h3>{_esc(gate)}</h3>\n")
        if not members:
            parts.append('<p class="empty-notice">no feature is currently at this stage.</p>\n')
        else:
            items = "".join(
                f'<li>{_esc(m["name"])} '
                f'<span class="gate-evidence">{_esc(_gate_evidence_text(m["gate_evidence"]))}</span></li>\n'
                for m in members
            )
            parts.append(f'<ul class="pipeline-list">\n{items}</ul>\n')
    parts.append("</div>\n")
    return "".join(parts)


def render_feature_lens_html(data: dict) -> str:
    """Pure — `build_feature_lens()` dict in, HTML string out, no I/O/clock/
    randomness of its own (NFR-6). Zero JavaScript."""
    features = data["features"]

    if not features:
        body = f'<p class="empty-notice">{_esc(data.get("reason") or "no features found")}</p>\n'
    else:
        body = (
            "<h2>Features</h2>\n"
            f"{_render_features_table(features)}"
            f"{_render_pipeline_section(features)}"
        )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Feature Lens</title>\n"
        f"<style>{_STYLE}{_LENS_STYLE}</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="page">\n'
        + _render_masthead()
        + "<h1>Feature Lens</h1>\n"
        + body
        + "</div>\n"
        "</body>\n"
        "</html>\n"
    )


def run_feature_lens_report(data: dict, output: str) -> Path:
    """Same F1-class safety net `releaseboard_report.py`/`report.py` both
    apply: a malformed data dict must never escape as a raw traceback."""
    try:
        text = render_feature_lens_html(data)
    except (AttributeError, KeyError, TypeError) as exc:
        raise ReleaseMapUnreadableError(
            f"feature lens data has an unexpected shape: {exc}"
        ) from exc

    out_path = Path(output) / STORE_DIRNAME / REPORT_FILENAME
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise ReportUnwritableError(
            f"could not write feature-lens.html to {out_path}: {exc}"
        ) from exc
    return out_path.resolve()
