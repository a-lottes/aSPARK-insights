"""render — turn the latest snapshot into one self-contained, offline HTML report.

Two public functions: `render_html` (pure — snapshot dict in, HTML string out, no
IO/clock/randomness; the NFR-5 determinism substrate and the unit-test seam for
every content AC) and `run_render` (the CLI orchestrator — resolves/validates the
latest snapshot via the exact `query` path, so US-2's named errors come by reuse,
never a second vocabulary).
"""

from __future__ import annotations

import html as _html
from pathlib import Path

from aspark_insights.errors import SnapshotUnreadableError
from aspark_insights.query import run_query
from aspark_insights.store import STORE_DIRNAME

REPORT_FILENAME = "report.html"

_STYLE = """
  body { font-family: system-ui, -apple-system, sans-serif; color: #1a1a1a; background: #fff; margin: 2rem; max-width: 60rem; }
  h1 { font-size: 1.5rem; }
  h2 { font-size: 1.15rem; margin-top: 2rem; border-bottom: 1px solid #ccc; padding-bottom: 0.25rem; }
  .table-wrap { overflow-x: auto; margin-top: 0.5rem; }
  table { border-collapse: collapse; width: 100%; }
  caption { text-align: left; font-weight: 600; margin-bottom: 0.25rem; }
  th, td { border: 1px solid #999; padding: 0.4rem 0.6rem; text-align: left; vertical-align: top; }
  th { background: #f0f0f0; }
  .summary { font-size: 1rem; }
  .null-value { font-style: italic; color: #444; }
  .stale-cue { border: 2px solid #7a4a00; color: #7a4a00; background: #fff6e5; padding: 0.5rem 0.75rem; font-weight: 700; margin: 0.5rem 0; }
  .empty-notice { border: 1px solid #999; background: #f7f7f7; padding: 0.75rem; font-style: italic; }
  .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; margin-top: 0.75rem; }
  .metric-card { border: 1px solid #ccc; border-radius: 6px; padding: 0.75rem 0.9rem; background: #fafafa; }
  .metric-card--null { border-style: dashed; background: #fff; }
  .metric-label { font-size: 0.85rem; color: #444; margin: 0 0 0.25rem; }
  .metric-value { font-size: 1.35rem; font-weight: 600; margin: 0 0 0.4rem; }
  .metric-value--null { font-size: 1rem; font-weight: 600; font-style: italic; color: #444; }
  .metric-n { font-size: 0.85rem; font-weight: 400; color: #666; }
  .metric-bar { height: 6px; background: #e2e2e2; border-radius: 3px; overflow: hidden; }
  .metric-bar-fill { height: 100%; background: #1a1a1a; }
  .metric-reason { font-size: 0.82rem; color: #444; margin: 0.4rem 0 0; }
  .metric-id { font-size: 0.75rem; color: #666; margin: 0.5rem 0 0; }
  .confidence-mix { border: 1px solid #ccc; border-radius: 6px; padding: 0.75rem 0.9rem; margin-top: 1rem; background: #fafafa; }
  .confidence-bar { display: flex; height: 10px; border-radius: 5px; overflow: hidden; margin: 0.5rem 0; }
  .confidence-seg { height: 100%; background: #1a1a1a; }
  .confidence-seg + .confidence-seg { border-left: 1px solid #fafafa; }
  .confidence-legend { font-size: 0.82rem; color: #444; margin: 0; }
"""

# Plain-language presentation metadata per metric_id, deliberately kept in the
# render layer only (never in the registry/model — this is display framing,
# not computation, so it carries no version and needs no bump when reworded).
# An unmapped metric_id (any future one) falls back to its raw id as label
# and no bar — never crashes, never invents a share/count shape it wasn't
# told about.
_METRIC_META: dict[str, dict[str, str]] = {
    "TRC-001": {"label": "Stories linked to tasks", "kind": "share"},
    "TRC-002": {"label": "ACs with QA evidence", "kind": "share"},
    "TRC-003": {"label": "Tasks linked to code", "kind": "share"},
    "TRC-004-orphan-tasks": {"label": "Tasks with no story link", "kind": "count"},
    "TRC-004-unverified-acs": {"label": "ACs with no QA evidence", "kind": "count"},
    "TRC-005-declared": {"label": "Trace confidence: declared", "kind": "share"},
    "TRC-005-extracted": {"label": "Trace confidence: extracted", "kind": "share"},
    "TRC-005-inferred": {"label": "Trace confidence: inferred", "kind": "share"},
}
_CONFIDENCE_TIER_IDS = ("TRC-005-declared", "TRC-005-extracted", "TRC-005-inferred")


def _esc(value: object) -> str:
    """The single choke-point every dynamic value must flow through (NFR-2)."""
    return _html.escape(str(value), quote=True)


def _fact_sort_key(fact: dict) -> tuple[str, str, str]:
    return (fact["subject_kind"], fact["subject_id"], fact["predicate"])


def _metric_sort_key(metric: dict) -> tuple[str, str]:
    return (metric["metric_id"], metric["metric_version"])


def _metric_percent(value: object, n: object, kind: str | None) -> int | None:
    """A percentage for the magnitude bar, or `None` when one cannot be derived
    honestly. `kind="share"`: value is already a 0..1 fraction. `kind="count"`:
    value is a raw count over its own denominator `n`.

    Deliberately **not clamped** (review M2): a share outside 0..1 or a count
    exceeding its own `n` is a broken input, and silently pinning it to 0/100
    would render a plausible number over a nonsensical one. Returning `None`
    drops the bar and leaves the raw value showing instead — the honest
    degradation this project already applies to unknown metric shapes."""
    try:
        if kind == "share":
            share = float(value)
            if not 0.0 <= share <= 1.0:
                return None
            return round(share * 100)
        if kind == "count" and n:
            count, denom = float(value), float(n)
            if not 0.0 <= count <= denom:
                return None
            return round(count / denom * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    return None


def _format_share(share: float) -> str:
    """Never round a real, nonzero share away to `0%` (review M2): a displayed
    `0%` for 1-of-250 asserts something false and becomes indistinguishable
    from an honest zero. Sub-half-percent magnitudes render as `<1%`, and the
    symmetric near-100 case as `>99%`."""
    pct = share * 100
    if 0 < pct < 0.5:
        return "&lt;1%"
    if 99.5 < pct < 100:
        return "&gt;99%"
    return f"{round(pct)}%"


def _render_metric_card(m: dict) -> str:
    """A real value always carries its `n` (AC-3.1); a null carries its full
    `reason`, in the same `Not computed` wording the table uses — one
    reader-facing word for one state (`measurement-honesty` C14's explicit
    user ruling: reuse the existing phrasing, never a new synonym)."""
    meta = _METRIC_META.get(m["metric_id"], {})
    label = meta.get("label", m["metric_id"])
    id_line = f'<p class="metric-id">{_esc(m["metric_id"])} &middot; v{_esc(m["metric_version"])}</p>\n'

    if m["value"] is None:
        return (
            '<div class="metric-card metric-card--null">\n'
            f'<p class="metric-label">{_esc(label)}</p>\n'
            '<p class="metric-value metric-value--null null-value">Not computed</p>\n'
            f'<p class="metric-reason">{_esc(m["reason"])}</p>\n'
            f"{id_line}"
            "</div>\n"
        )

    kind = meta.get("kind")
    percent = _metric_percent(m["value"], m["n"], kind)
    # AC-3.1 (foundation precedent): never a bare value with n omitted.
    n_part = f' <span class="metric-n">(n={_esc(m["n"])})</span>' if m["n"] is not None \
        else ' <span class="metric-n">(n unavailable)</span>'
    # A count metric shows its count, never a percentage substituted for it
    # (review M1): the registry ships TRC-004 as counts, and rendering the
    # ratio in the value's place publishes a derived figure the registry never
    # computed. The ratio drives the bar only.
    if kind == "share" and percent is not None:
        value_text = _format_share(float(m["value"]))
    elif kind == "count" and percent is not None:
        value_text = f'{_esc(m["value"])} of {_esc(m["n"])}'
    else:
        value_text = _esc(m["value"])
    bar = (
        f'<div class="metric-bar"><div class="metric-bar-fill" style="width:{percent:d}%"></div></div>\n'
        if percent is not None else ""
    )
    return (
        '<div class="metric-card">\n'
        f'<p class="metric-label">{_esc(label)}</p>\n'
        f'<p class="metric-value">{value_text}{n_part}</p>\n'
        f"{bar}"
        f"{id_line}"
        "</div>\n"
    )


def _render_confidence_mix(metrics_by_id: dict[str, dict]) -> str:
    """TRC-005's three tiers as one stacked bar — a *visual addition* to the
    metrics table, never a replacement for it: every tier keeps its own row
    with its id, version and `n` below (AC-1.2).

    Renders only when all three tiers are present, all real, and all share one
    `n`. A partial set would read as "the remainder is untraced" when a tier is
    merely absent (review M5); differing `n`s would publish one denominator for
    three different populations (M4). Percentages route through
    `_metric_percent`, not a second copy of the arithmetic (M3)."""
    tiers = [metrics_by_id[tid] for tid in _CONFIDENCE_TIER_IDS if tid in metrics_by_id]
    if len(tiers) != len(_CONFIDENCE_TIER_IDS):
        return ""
    percents = [_metric_percent(t["value"], t["n"], "share") for t in tiers]
    if any(p is None for p in percents):
        return ""
    n = tiers[0]["n"]
    if not n or any(t["n"] != n for t in tiers):  # falsy n (None or 0): no real population to share
        return ""

    segments = "".join(
        f'<div class="confidence-seg" style="width:{p:d}%"></div>\n'
        for p in percents if p > 0
    )
    legend = " &middot; ".join(
        f'{_esc(_METRIC_META.get(t["metric_id"], {}).get("label", t["metric_id"]).rsplit(": ", 1)[-1])} '
        f'{_format_share(float(t["value"]))}'
        for t in tiers
    )
    return (
        '<div class="confidence-mix">\n'
        f'<p class="metric-label">Trace confidence (of {_esc(n)} fully-traced stories)</p>\n'
        f'<div class="confidence-bar">\n{segments}</div>\n'
        f'<p class="confidence-legend">{legend}</p>\n'
        "</div>\n"
    )


def _render_metric_value_cell(value: object, reason: str | None, n: int | None) -> str:
    """AC-3.1/3.2: a real value always carries its `n`; a null value shows its
    `reason` with a fixed, non-color-only shape distinguishing it from a value
    — never a blank cell or bare dash."""
    if value is not None:
        n_part = f" (n={_esc(n)})" if n is not None else " (n unavailable)"
        return f"{_esc(value)}{n_part}"
    return f'<span class="null-value">Not computed: {_esc(reason)}</span>'


def _render_metrics_full_table(metrics: list[dict]) -> str:
    """AC-1.2 / NFR-4 / constitution §4: **every** entry in `metrics` appears
    here with its own `metric_id` and `metric_version`, in a real `<table>`
    with `<th scope="col">` and a `<caption>` — not a `<div>` grid. The cards
    and the confidence bar above are a readability layer on top of this table,
    never a substitute for it: a metric folded into a visual summary must still
    be findable, versioned and countable here (review B1/B2)."""
    rows = []
    for m in metrics:
        value_cell = _render_metric_value_cell(m["value"], m["reason"], m["n"])
        rows.append(
            "<tr>"
            f"<td>{_esc(m['metric_id'])}</td>"
            f"<td>{_esc(m['metric_version'])}</td>"
            f"<td>{value_cell}</td>"
            "</tr>"
        )
    body = "\n".join(rows)
    return (
        '<div class="table-wrap">\n<table>\n<caption>Metrics</caption>\n'
        "<thead><tr>"
        '<th scope="col">Metric ID</th><th scope="col">Version</th><th scope="col">Value</th>'
        "</tr></thead>\n"
        f"<tbody>\n{body}\n</tbody>\n"
        "</table>\n</div>\n"
    )


def _render_metrics_scorecard(metrics: list[dict]) -> str:
    """Cards and the confidence bar as a plain-language reading layer, over the
    full metrics table that carries every id, version and `n` (AC-1.2). Cards
    cover the metrics not folded into the confidence bar; the table covers all
    of them, so nothing is reachable only through a visual summary."""
    by_id = {m["metric_id"]: m for m in metrics}
    confidence_html = _render_confidence_mix(by_id)
    # Identity-based, not id-based: two versions of one metric_id must not both
    # vanish because a single-version fold consumed the id (review M6).
    folded = {id(by_id[tid]) for tid in _CONFIDENCE_TIER_IDS if tid in by_id} if confidence_html else set()
    cards = "".join(_render_metric_card(m) for m in metrics if id(m) not in folded)
    return (
        '<section id="metrics">\n'
        "<h2>Metrics</h2>\n"
        f'<div class="metric-grid">\n{cards}</div>\n'
        f"{confidence_html}"
        f"{_render_metrics_full_table(metrics)}"
        "</section>\n"
    )


def _render_facts_table(facts: list[dict]) -> str:
    if not facts:
        # AC-3.3 / design review finding 6: this is the realistic first-run
        # screen (this project's own dogfood fixture hits it), not an edge
        # case — a styled notice block, not a bare empty table.
        return (
            '<section id="facts">\n'
            "<h2>Facts</h2>\n"
            '<p class="empty-notice">No facts recorded for this snapshot.</p>\n'
            "</section>\n"
        )
    rows = []
    for f in facts:
        rows.append(
            "<tr>"
            f"<td>{_esc(f['subject_kind'])}</td>"
            f"<td>{_esc(f['subject_id'])}</td>"
            f"<td>{_esc(f['predicate'])}</td>"
            f"<td>{_esc(f['value'])}</td>"
            "</tr>"
        )
    body = "\n".join(rows)
    return (
        '<section id="facts">\n'
        "<h2>Facts</h2>\n"
        '<div class="table-wrap">\n<table>\n<caption>Facts</caption>\n'
        "<thead><tr>"
        '<th scope="col">Subject kind</th><th scope="col">Subject ID</th>'
        '<th scope="col">Predicate</th><th scope="col">Value</th>'
        "</tr></thead>\n"
        f"<tbody>\n{body}\n</tbody>\n"
        "</table>\n</div>\n"
        "</section>\n"
    )


def _is_stale(graph_staleness: dict | None) -> bool:
    return bool(graph_staleness and graph_staleness.get("stale") is True)


def _flatten_list(values) -> str:
    if not values:
        return "(none)"
    return ", ".join(_esc(v) for v in values)


def _flatten_value(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return _flatten_list(value)
    return _esc(value)


def _render_summary(facts: list[dict], metrics: list[dict]) -> str:
    null_count = sum(1 for m in metrics if m["value"] is None)
    computed_count = len(metrics) - null_count
    return (
        '<ul class="summary">\n'
        f"<li><strong>Facts:</strong> {_esc(len(facts))}</li>\n"
        f"<li><strong>Metrics:</strong> {_esc(len(metrics))}</li>\n"
        f"<li><strong>Computed:</strong> {_esc(computed_count)}</li>\n"
        f"<li><strong>Null:</strong> {_esc(null_count)}</li>\n"
        "</ul>\n"
    )


def _render_top_stale_cue() -> str:
    return (
        '<p class="stale-cue">STALE &mdash; report based on a stale graph; '
        "see Provenance for details.</p>\n"
    )


def _evidence_absent_metrics(metrics: list[dict]) -> list[dict]:
    """AC-4.1(i): the caveat's trigger is exactly `value is None and n` — this
    is the shape only `metrics.evidence.gate()` produces (build.py enforces
    that invariant). A denominator-absent null always has `n` falsy (0 or
    None) and never raises this caveat (AC-1.4's precedence, AC-4.3's
    negative case) — no per-metric marker, no model change needed."""
    return [m for m in metrics if m["value"] is None and m["n"]]


def _render_evidence_caveat(metrics: list[dict]) -> str:
    """AC-4.1: reuses `.stale-cue`'s box geometry (same class, same
    pre-verified contrast) but opens with a constant label distinct from
    `STALE` — so the two cues are told apart by their first word, not by
    hue (AC-4.4: never color alone). `metrics` is already sorted by the
    caller, so `affected` preserves that order without re-sorting."""
    affected = _evidence_absent_metrics(metrics)
    if not affected:
        return ""  # AC-4.3: no notice, placeholder, or empty container
    ids = ", ".join(_esc(m["metric_id"]) for m in affected)
    return (
        '<p class="stale-cue">NOT COMPUTED &mdash; '
        f"{_esc(len(affected))} of {_esc(len(metrics))} metrics could not be computed "
        "&mdash; the evidence they count is absent from the graph. "
        f"Affected: {ids}. See the Metrics table below.</p>\n"
    )


# Top-level Provenance keys already given explicit row treatment below —
# never generated by the generic tail, so `policy_versions` (currently always
# None, deliberately unrendered — unchanged pre-existing behavior) doesn't
# suddenly appear, and existing snapshots' rendered bytes stay unchanged.
_KNOWN_PROVENANCE_KEYS = frozenset({
    "as_of", "insights_version", "metric_registry_version",
    "graph_source", "policy_versions", "scope_filter", "graph_staleness",
})


def _render_provenance(provenance: dict, stale: bool) -> str:
    graph_source = provenance.get("graph_source") or {}
    scope_filter = provenance.get("scope_filter") or {}
    graph_staleness = provenance.get("graph_staleness")

    rows: list[tuple[str, str]] = [
        ("as_of", _esc(provenance.get("as_of"))),
        ("insights_version", _esc(provenance.get("insights_version"))),
        ("metric_registry_version", _esc(provenance.get("metric_registry_version"))),
        ("graph_source.access", _esc(graph_source.get("access"))),
        ("graph_source.sealed", _esc(graph_source.get("sealed"))),
        ("scope_filter.patterns", _flatten_list(scope_filter.get("patterns"))),
        ("scope_filter.excluded_count", _esc(scope_filter.get("excluded_count"))),
    ]
    if graph_staleness is None:
        rows.append(("graph_staleness", "(not available)"))
    else:
        for key in sorted(graph_staleness):
            rows.append((f"graph_staleness.{key}", _flatten_value(graph_staleness[key])))

    # AC-4.6: any top-level provenance field beyond the known set above (e.g.
    # artifact_probe) renders here, key-driven — a hardcoded row list would
    # silently drop a future field the way it dropped artifact_probe before
    # this fix (D5/Blocker, spec §8).
    for top_key in sorted(provenance):
        if top_key in _KNOWN_PROVENANCE_KEYS:
            continue
        nested = provenance[top_key]
        if isinstance(nested, dict):
            for key in sorted(nested):
                rows.append((f"{top_key}.{key}", _flatten_value(nested[key])))
        else:
            rows.append((top_key, _flatten_value(nested)))

    body = "\n".join(f"<tr><td>{_esc(k)}</td><td>{v}</td></tr>" for k, v in rows)
    in_section_cue = (
        '<p class="stale-cue">STALE &mdash; graph_staleness.stale is true.</p>\n' if stale else ""
    )
    return (
        '<section id="provenance">\n'
        "<h2>Provenance</h2>\n"
        f"{in_section_cue}"
        '<div class="table-wrap">\n<table>\n<caption>Provenance</caption>\n'
        '<thead><tr><th scope="col">Field</th><th scope="col">Value</th></tr></thead>\n'
        f"<tbody>\n{body}\n</tbody>\n"
        "</table>\n</div>\n"
        "</section>\n"
    )


def render_html(snapshot: dict) -> str:
    facts = sorted(snapshot["facts"], key=_fact_sort_key)
    metrics = sorted(snapshot["metrics"], key=_metric_sort_key)
    provenance = snapshot["provenance"]
    stale = _is_stale(provenance.get("graph_staleness"))

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Insights Snapshot Report</title>\n"
        f"<style>{_STYLE}</style>\n"
        "</head>\n"
        "<body>\n"
        "<h1>Insights Snapshot Report</h1>\n"
        + _render_summary(facts, metrics)
        + (_render_top_stale_cue() if stale else "")
        + _render_evidence_caveat(metrics)
        + _render_provenance(provenance, stale)
        + _render_metrics_scorecard(metrics)
        + _render_facts_table(facts)
        + "</body>\n"
        "</html>\n"
    )


def run_render(location: str) -> Path:
    """Write `<location>/.aspark-insights/report.html`, return its resolved absolute path."""
    snapshot = run_query(location)
    try:
        text = render_html(snapshot)
    except (AttributeError, KeyError, TypeError) as exc:
        # `require_snapshot_shape` (via run_query) only checks top-level keys
        # — a fact/metric entry with the wrong sub-shape, or facts/metrics not
        # even a list, passes that check but crashes render's deeper indexing.
        # query/verify never index this deep, so this stays render-specific
        # rather than widening require_snapshot_shape for callers that never
        # asked for the extra strictness (F1).
        raise SnapshotUnreadableError(
            f"snapshot at {location!r} has an unexpected shape: {exc}"
        ) from exc
    out_path = Path(location) / STORE_DIRNAME / REPORT_FILENAME
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path.resolve()
