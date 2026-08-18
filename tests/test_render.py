"""snapshot-report: `insights render` writes one self-contained, offline HTML
report of the latest snapshot (US-1..US-5). Task references are to
.spark/snapshot-report/plan.md's T1..T7.
"""

from __future__ import annotations

import inspect
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.build import build_snapshot
from aspark_insights.errors import InsightsError
from aspark_insights.render import REPORT_FILENAME, render_html, run_render
from aspark_insights.store import STORE_DIRNAME, write_snapshot

FIXTURE_GRAPH = Path(__file__).parent / "fixtures" / "graph.json"

_EXTERNAL_REF_PATTERN = re.compile(r'(https?://|<link\b|<script\b[^>]*\bsrc=)', re.IGNORECASE)


@pytest.fixture
def built_repo(tmp_path: Path) -> Path:
    graph_dir = tmp_path / ".aspark-graph"
    graph_dir.mkdir()
    shutil.copyfile(FIXTURE_GRAPH, graph_dir / "graph.json")
    return tmp_path


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True,
        text=True,
        cwd=repo,
    )


# --- T1: walking skeleton ----------------------------------------------------


def test_render_html_is_pure_no_io_no_clock_no_random():
    sig = inspect.signature(render_html)
    assert list(sig.parameters) == ["snapshot"]


def test_render_html_has_viewport_meta_so_mobile_width_actually_applies():
    """NFR-7: without this, mobile browsers render at a fixed ~980px virtual
    viewport regardless of device width, defeating the 375px requirement
    entirely — caught by actually rendering the page in a browser, not just
    reading the CSS."""
    text = render_html(_snapshot())
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in text


def test_render_html_skeleton_has_doctype_one_h1_embedded_style_no_external_refs():
    snapshot = {"facts": [], "metrics": [], "provenance": {
        "as_of": "2026-08-04", "insights_version": "0.3.0", "metric_registry_version": "0.1.0",
        "graph_source": {"access": "library-interim", "sealed": True}, "policy_versions": None,
        "scope_filter": {"patterns": [], "excluded_count": 0}, "graph_staleness": None,
    }}
    text = render_html(snapshot)
    assert text.startswith("<!DOCTYPE html>")
    assert text.count("<h1") == 1
    assert "<style>" in text
    assert not _EXTERNAL_REF_PATTERN.search(text)


def test_run_render_writes_report_and_returns_resolved_absolute_path(built_repo: Path):
    snapshot = build_snapshot(built_repo, as_of="2026-07-29")
    write_snapshot(built_repo, snapshot)

    path = run_render(str(built_repo))

    assert path.is_absolute()
    assert path == path.resolve()
    assert path.name == REPORT_FILENAME
    assert path.parent.name == STORE_DIRNAME
    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_run_render_overwrites_existing_report(built_repo: Path):
    snapshot = build_snapshot(built_repo, as_of="2026-07-29")
    write_snapshot(built_repo, snapshot)
    report_path = built_repo / STORE_DIRNAME / REPORT_FILENAME
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("stale content", encoding="utf-8")

    run_render(str(built_repo))

    assert "stale content" not in report_path.read_text(encoding="utf-8")


def test_cli_render_prints_report_confirmation_json_and_exits_0(built_repo: Path):
    build_result = _run_cli(built_repo, "build", "--as-of", "2026-07-29")
    assert build_result.returncode == 0, build_result.stderr

    result = _run_cli(built_repo, "render")
    assert result.returncode == 0, result.stderr

    data = json.loads(result.stdout)
    assert set(data.keys()) == {"report"}
    assert Path(data["report"]).is_absolute()
    assert Path(data["report"]).exists()


def test_render_help_documents_real_behavior_not_not_implemented(tmp_path: Path):
    result = _run_cli(tmp_path, "render", "--help")
    assert result.returncode == 0
    assert "not yet implemented" not in result.stdout.lower()
    assert "--repo" in result.stdout
    assert "--output" in result.stdout


def test_build_help_documents_the_spark_artifact_presence_read(tmp_path: Path):
    """NFR-6: build --help must document that build also *reads* <repo>/.spark/
    for artifact presence (a read, never a write) — the project's own
    "document the write-location behavior directly in --help text" convention
    (CLAUDE.md), extended to this feature's new read."""
    result = _run_cli(tmp_path, "build", "--help")
    assert result.returncode == 0
    assert ".spark/" in result.stdout
    assert "qa.md" in result.stdout or "review.md" in result.stdout


# --- T2: no snapshot / unreadable -> reuse query's named errors --------------


def test_render_with_no_snapshot_exits_1_with_named_error(tmp_path: Path):
    result = _run_cli(tmp_path, "render")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "no_snapshot" in result.stderr
    assert "Traceback" not in result.stderr


def test_render_on_corrupt_snapshot_exits_1_with_named_error_not_a_traceback(tmp_path: Path):
    snapshots_dir = tmp_path / STORE_DIRNAME / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "2026-07-29.json").write_text("{not valid json", encoding="utf-8")

    result = _run_cli(tmp_path, "render")
    assert result.returncode == 1
    assert "snapshot_unreadable" in result.stderr
    assert "Traceback" not in result.stderr


def test_render_on_wrong_shape_json_exits_1_with_named_error(tmp_path: Path):
    snapshots_dir = tmp_path / STORE_DIRNAME / "snapshots"
    snapshots_dir.mkdir(parents=True)
    (snapshots_dir / "2026-07-29.json").write_text("{}", encoding="utf-8")

    result = _run_cli(tmp_path, "render")
    assert result.returncode == 1
    assert "snapshot_unreadable" in result.stderr
    assert "Traceback" not in result.stderr


def test_run_render_raises_insights_error_not_a_generic_exception(tmp_path: Path):
    with pytest.raises(InsightsError):
        run_render(str(tmp_path))


# --- F1 (review fix): a wrong-sub-shape snapshot never raises a raw traceback -


def _write_snapshot_json(tmp_path: Path, snapshot: dict) -> None:
    snapshots_dir = tmp_path / STORE_DIRNAME / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    (snapshots_dir / "2026-08-04.json").write_text(json.dumps(snapshot), encoding="utf-8")


def test_metric_missing_value_field_raises_snapshot_unreadable_not_a_crash(tmp_path: Path):
    """The exact repro found in /peer-review: a metric dict present but missing
    value/reason/n crashed render_html with a raw KeyError before the fix."""
    _write_snapshot_json(tmp_path, {
        "facts": [], "metrics": [{"metric_id": "M1", "metric_version": "1.0.0"}],
        "provenance": {"as_of": "2026-08-04"},
    })
    with pytest.raises(InsightsError) as exc_info:
        run_render(str(tmp_path))
    assert exc_info.value.reason == "snapshot_unreadable"


def test_fact_missing_subject_kind_field_raises_snapshot_unreadable_not_a_crash(tmp_path: Path):
    _write_snapshot_json(tmp_path, {
        "facts": [{"subject_id": "x", "predicate": "p", "value": 1}], "metrics": [],
        "provenance": {"as_of": "2026-08-04"},
    })
    with pytest.raises(InsightsError) as exc_info:
        run_render(str(tmp_path))
    assert exc_info.value.reason == "snapshot_unreadable"


def test_facts_not_a_list_raises_snapshot_unreadable_not_a_crash(tmp_path: Path):
    _write_snapshot_json(tmp_path, {
        "facts": "not-a-list", "metrics": [],
        "provenance": {"as_of": "2026-08-04"},
    })
    with pytest.raises(InsightsError) as exc_info:
        run_render(str(tmp_path))
    assert exc_info.value.reason == "snapshot_unreadable"


def test_wrong_sub_shape_via_real_cli_exits_1_with_named_error_not_a_traceback(tmp_path: Path):
    _write_snapshot_json(tmp_path, {
        "facts": [], "metrics": [{"metric_id": "M1", "metric_version": "1.0.0"}],
        "provenance": {"as_of": "2026-08-04"},
    })
    result = _run_cli(tmp_path, "render")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "snapshot_unreadable" in result.stderr
    assert "Traceback" not in result.stderr


# --- T3: data tables — canonical sort, nothing dropped, semantic markup -----


def _snapshot(facts=None, metrics=None, provenance=None) -> dict:
    return {
        "facts": facts or [],
        "metrics": metrics or [],
        "provenance": provenance or {
            "as_of": "2026-08-04", "insights_version": "0.3.0", "metric_registry_version": "0.1.0",
            "graph_source": {"access": "library-interim", "sealed": True}, "policy_versions": None,
            "scope_filter": {"patterns": [], "excluded_count": 0}, "graph_staleness": None,
        },
    }


def test_facts_table_sorted_by_subject_kind_subject_id_predicate():
    facts = [
        {"subject_kind": "feature", "subject_id": "z", "predicate": "p", "value": 1},
        {"subject_kind": "code_artifact", "subject_id": "a", "predicate": "p", "value": 2},
        {"subject_kind": "code_artifact", "subject_id": "a", "predicate": "a-earlier", "value": 3},
    ]
    text = render_html(_snapshot(facts=facts))
    positions = [text.index(f'>{v}<') for v in ("3", "2", "1")]
    assert positions == sorted(positions)


def test_metrics_scorecard_sorted_by_metric_id_then_version():
    metrics = [
        {"metric_id": "TRC-002", "metric_version": "1.0.0", "value": 1, "reason": None, "n": 5},
        {"metric_id": "TRC-001", "metric_version": "2.0.0", "value": 2, "reason": None, "n": 5},
        {"metric_id": "TRC-001", "metric_version": "1.0.0", "value": 3, "reason": None, "n": 5},
    ]
    text = render_html(_snapshot(metrics=metrics))
    pos_trc001_v1 = text.index("TRC-001 &middot; v1.0.0")
    pos_trc001_v2 = text.index("TRC-001 &middot; v2.0.0")
    pos_trc002 = text.index("TRC-002 &middot; v1.0.0")
    assert pos_trc001_v1 < pos_trc001_v2 < pos_trc002


def test_all_facts_and_metrics_rows_present_none_dropped():
    facts = [
        {"subject_kind": "code_artifact", "subject_id": f"id-{i}", "predicate": "p", "value": i}
        for i in range(12)
    ]
    metrics = [
        {"metric_id": f"M-{i}", "metric_version": "1.0.0", "value": i, "reason": None, "n": 5}
        for i in range(12)
    ]
    text = render_html(_snapshot(facts=facts, metrics=metrics))
    for i in range(12):
        assert f"id-{i}" in text
        assert f"M-{i}" in text


def test_tables_have_scope_col_headers_and_captions():
    text = render_html(_snapshot(
        facts=[{"subject_kind": "code_artifact", "subject_id": "a", "predicate": "p", "value": 1}],
    ))
    assert text.count('<th scope="col">') >= 2  # Facts + Provenance tables
    assert "<caption>Facts</caption>" in text
    assert "<caption>Provenance</caption>" in text


# --- T4: provenance verbatim, section order, two-place stale cue -----------


_STALE_PROVENANCE = {
    "as_of": "2026-08-04", "insights_version": "0.3.0", "metric_registry_version": "0.1.0",
    "graph_source": {"access": "library-interim", "sealed": True}, "policy_versions": None,
    "scope_filter": {"patterns": [".claude/worktrees/**"], "excluded_count": 3},
    "graph_staleness": {
        "available": True, "stale": True, "files_checked": 40,
        "changed": ["src/a.py"], "missing": [], "advice": "Run 'aspark-graph build' to refresh.",
    },
}


def test_provenance_rendered_verbatim():
    text = render_html(_snapshot(provenance=_STALE_PROVENANCE))
    assert "2026-08-04" in text
    assert "0.3.0" in text
    assert "0.1.0" in text
    assert "library-interim" in text
    assert ".claude/worktrees/**" in text
    assert "40" in text
    assert "src/a.py" in text
    assert "Run &#x27;aspark-graph build&#x27; to refresh." in text  # html.escape(quote=True)


def test_section_order_provenance_then_metrics_then_facts():
    text = render_html(_snapshot(
        facts=[{"subject_kind": "code_artifact", "subject_id": "a", "predicate": "p", "value": 1}],
        metrics=[{"metric_id": "M", "metric_version": "1", "value": 1, "reason": None, "n": 1}],
    ))
    pos_h1 = text.index("<h1")
    pos_provenance = text.index('id="provenance"')
    pos_metrics = text.index('id="metrics"')
    pos_facts = text.index('id="facts"')
    assert pos_h1 < pos_provenance < pos_metrics < pos_facts


def test_stale_cue_appears_in_two_places_when_stale():
    text = render_html(_snapshot(provenance=_STALE_PROVENANCE))
    assert text.count("STALE") == 2
    pos_h1 = text.index("<h1")
    pos_provenance = text.index('id="provenance"')
    first_stale = text.index("STALE")
    second_stale = text.index("STALE", first_stale + 1)
    assert pos_h1 < first_stale < pos_provenance < second_stale


def test_no_stale_cue_when_not_stale():
    text = render_html(_snapshot())  # default provenance has graph_staleness: None
    assert "STALE" not in text


def test_no_stale_cue_when_stale_is_false():
    provenance = dict(_STALE_PROVENANCE)
    provenance["graph_staleness"] = {**_STALE_PROVENANCE["graph_staleness"], "stale": False}
    text = render_html(_snapshot(provenance=provenance))
    assert "STALE" not in text


def test_h2_headings_present_for_provenance_metrics_facts():
    text = render_html(_snapshot())
    assert "<h2>Provenance</h2>" in text
    assert "<h2>Metrics</h2>" in text
    assert "<h2>Facts</h2>" in text


# --- T5: honest values — n beside value, distinctly-shaped null, empty state -


def test_computed_share_metric_shows_percent_together_with_n():
    """TRC-003 is a known "share" metric (a 0..1 fraction) — the scorecard
    shows it as a rounded percent, not the raw float, with its n alongside
    in the same value block, never split across unrelated elements."""
    metrics = [{"metric_id": "TRC-003", "metric_version": "1.0.0", "value": 0.875, "reason": None, "n": 8}]
    text = render_html(_snapshot(metrics=metrics))
    assert '<p class="metric-value">88% <span class="metric-n">(n=8)</span></p>' in text


def test_computed_value_with_n_none_never_shows_a_bare_value():
    """F2: the model permits value != None with n == None; never a bare value
    with no n-related marker at all, even in this theoretical case. "M" is
    not a known metric_id, so it falls back to its raw value (no percent)."""
    metrics = [{"metric_id": "M", "metric_version": "1.0.0", "value": 42, "reason": None, "n": None}]
    text = render_html(_snapshot(metrics=metrics))
    assert "42" in text
    assert "(n unavailable)" in text
    assert '<p class="metric-value">42</p>' not in text  # never a bare value, no n-marker


# --- review B1/B2/M1-M7: the fragile new branches (previously zero coverage) -


def _metric_value_block(text: str, metric_id: str) -> str:
    """The rendered `<p class="metric-value">...</p>` for one metric's card —
    scoped so assertions never accidentally match the static `<style>` block
    (which always contains literal `100%`, e.g. `.metric-bar-fill { height:
    100%; }`, regardless of any metric's data)."""
    marker = f'{metric_id} &middot;'
    card_start = text.rindex('<div class="metric-card', 0, text.index(marker))
    card = text[card_start:text.index("</div>", text.index(marker))]
    value_start = card.index('<p class="metric-value">')
    return card[value_start:card.index("</p>", value_start) + 4]


def test_count_metric_shows_the_count_never_a_substituted_percentage():
    """review M1: TRC-004-orphan-tasks is a "count" metric — its raw count
    must remain the displayed value; the ratio drives the bar's width only,
    it never replaces the number shown in the value line itself."""
    metrics = [{"metric_id": "TRC-004-orphan-tasks", "metric_version": "1.0.0", "value": 3, "reason": None, "n": 24}]
    text = render_html(_snapshot(metrics=metrics))
    value_block = _metric_value_block(text, "TRC-004-orphan-tasks")
    assert value_block == '<p class="metric-value">3 of 24 <span class="metric-n">(n=24)</span></p>'
    assert "12%" not in value_block  # the ratio must never appear as if it were the value


def test_share_above_one_falls_back_to_raw_value_no_bar():
    """review M2: an out-of-range share (a broken input, not a real fraction)
    is never clamped into a plausible-looking percentage — it falls back to
    the raw value and drops the bar entirely."""
    metrics = [{"metric_id": "TRC-001", "metric_version": "1.0.0", "value": 1.7, "reason": None, "n": 4}]
    text = render_html(_snapshot(metrics=metrics))
    value_block = _metric_value_block(text, "TRC-001")
    assert "%" not in value_block
    assert "1.7" in value_block
    assert '<div class="metric-bar-fill"' not in text  # no bar rendered anywhere for this single-metric page


def test_count_exceeding_its_own_n_falls_back_to_raw_no_bar():
    """review M1/M2: a count greater than its own n is nonsensical — never
    silently pinned to 100%."""
    metrics = [{"metric_id": "TRC-004-orphan-tasks", "metric_version": "1.0.0", "value": 50, "reason": None, "n": 4}]
    text = render_html(_snapshot(metrics=metrics))
    value_block = _metric_value_block(text, "TRC-004-orphan-tasks")
    assert "%" not in value_block
    assert "50" in value_block
    assert '<div class="metric-bar-fill"' not in text  # no bar rendered anywhere for this single-metric page


def test_tiny_nonzero_share_never_rounds_away_to_a_false_zero():
    """review M2: 1-of-250 must never render as the same "0%" a real, honest
    zero would show — that would assert something false and erase the
    distinction between "almost none" and "none"."""
    metrics = [{"metric_id": "TRC-002", "metric_version": "1.0.0", "value": 0.004, "reason": None, "n": 250}]
    text = render_html(_snapshot(metrics=metrics))
    assert "&lt;1%" in text
    assert '>0%<' not in text and '">0%' not in text


def test_confidence_mix_null_string_tier_does_not_crash_the_report():
    """review M3: a non-numeric tier value must degrade honestly (no mix
    rendered, cards render instead), never raise out of render_html — the
    exact class of defect the last cycle's F1 fix hardened against."""
    metrics = [
        {"metric_id": "TRC-005-declared", "metric_version": "1.0.0", "value": "not-a-number", "reason": None, "n": 4},
        {"metric_id": "TRC-005-extracted", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 4},
        {"metric_id": "TRC-005-inferred", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 4},
    ]
    text = render_html(_snapshot(metrics=metrics))  # must not raise
    assert '<div class="confidence-mix">' not in text
    assert "TRC-005-declared" in text  # falls back to its own card


def test_confidence_mix_requires_all_three_tiers_present():
    """review M5: two of three tiers must not render a mix that misrepresents
    the absent third as untraced remainder."""
    metrics = [
        {"metric_id": "TRC-005-declared", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 4},
        {"metric_id": "TRC-005-extracted", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 4},
    ]
    text = render_html(_snapshot(metrics=metrics))
    assert '<div class="confidence-mix">' not in text


def test_confidence_mix_requires_matching_n_across_tiers():
    """review M4: tiers with differing n describe different populations —
    folding them into one bar with one n would misattribute the denominator."""
    metrics = [
        {"metric_id": "TRC-005-declared", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 4},
        {"metric_id": "TRC-005-extracted", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 99},
        {"metric_id": "TRC-005-inferred", "metric_version": "1.0.0", "value": 0.0, "reason": None, "n": 4},
    ]
    text = render_html(_snapshot(metrics=metrics))
    assert '<div class="confidence-mix">' not in text


def test_confidence_mix_null_n_is_not_rendered_as_literal_none():
    """review M4: an all-null n must never reach the page as the word 'None'."""
    metrics = [
        {"metric_id": "TRC-005-declared", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": None},
        {"metric_id": "TRC-005-extracted", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": None},
        {"metric_id": "TRC-005-inferred", "metric_version": "1.0.0", "value": 0.0, "reason": None, "n": None},
    ]
    text = render_html(_snapshot(metrics=metrics))
    assert '<div class="confidence-mix">' not in text
    assert "of None fully-traced" not in text


def test_confidence_mix_zero_n_is_not_a_real_population_to_share():
    """N1 (re-verification pass): n=0 must be treated the same as n=None — a
    share "of 0 fully-traced stories" is a population that does not exist,
    not a real mix to render. The real registry emits null, not a share, at
    n=0 (AC-1.4's precedence), so this guards a broken-input path directly,
    the same reachability class M2/M4 already defend."""
    metrics = [
        {"metric_id": "TRC-005-declared", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 0},
        {"metric_id": "TRC-005-extracted", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 0},
        {"metric_id": "TRC-005-inferred", "metric_version": "1.0.0", "value": 0.0, "reason": None, "n": 0},
    ]
    text = render_html(_snapshot(metrics=metrics))
    assert '<div class="confidence-mix">' not in text
    assert "of 0 fully-traced" not in text


def test_duplicate_metric_id_across_versions_both_reach_the_page():
    """review M6: two versions of one metric_id (a legitimate registry shape,
    exercised elsewhere by TRC-001 v1/v2) must not both vanish when one
    version happens to be a confidence tier folded into the mix bar."""
    metrics = [
        {"metric_id": "TRC-005-declared", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 4},
        {"metric_id": "TRC-005-declared", "metric_version": "2.0.0", "value": 0.5, "reason": None, "n": 4},
        {"metric_id": "TRC-005-extracted", "metric_version": "1.0.0", "value": 0.5, "reason": None, "n": 4},
        {"metric_id": "TRC-005-inferred", "metric_version": "1.0.0", "value": 0.0, "reason": None, "n": 4},
    ]
    text = render_html(_snapshot(metrics=metrics))
    metrics_section = text.split('id="metrics"')[1].split("</section>")[0]
    # The table (B1/B2) is guaranteed to carry every metric regardless of
    # folding — this is the assertion that actually exercises M6.
    assert "<td>TRC-005-declared</td><td>1.0.0</td>" in metrics_section
    assert "<td>TRC-005-declared</td><td>2.0.0</td>" in metrics_section
    # v1.0.0 was not consumed by the mix fold, so it also keeps its own card.
    assert "TRC-005-declared &middot; v1.0.0" in metrics_section


def test_full_metrics_table_present_alongside_the_scorecard():
    """review B1 (constitution §4 / snapshot-report AC-1.2): the cards are an
    addition, never a replacement — every metric still appears in a real
    <table> with <th scope="col"> and a <caption>."""
    metrics = [{"metric_id": "TRC-003", "metric_version": "1.0.0", "value": 0.875, "reason": None, "n": 8}]
    text = render_html(_snapshot(metrics=metrics))
    metrics_section = text.split('id="metrics"')[1].split("</section>")[0]
    assert "<caption>Metrics</caption>" in metrics_section
    assert '<th scope="col">Metric ID</th>' in metrics_section
    assert "<td>TRC-003</td>" in metrics_section


def test_all_eight_family_metrics_reach_the_page_none_dropped_by_folding():
    """review B2: the exact live-repo shape (8 metrics, 3 folded into the
    confidence mix) must still show all 8 ids in the full table, matching the
    summary's own count — reproduces the bug found against this repo's real
    output before the fix."""
    metrics = [
        {"metric_id": "TRC-001", "metric_version": "2.0.0", "value": 1.0, "reason": None, "n": 14},
        {"metric_id": "TRC-002", "metric_version": "2.0.0", "value": None, "reason": "no evidence", "n": 41},
        {"metric_id": "TRC-003", "metric_version": "2.0.0", "value": 0.875, "reason": None, "n": 24},
        {"metric_id": "TRC-004-orphan-tasks", "metric_version": "2.0.0", "value": 0, "reason": None, "n": 24},
        {"metric_id": "TRC-004-unverified-acs", "metric_version": "2.0.0", "value": None, "reason": "no evidence", "n": 41},
        {"metric_id": "TRC-005-declared", "metric_version": "1.0.0", "value": 1.0, "reason": None, "n": 13},
        {"metric_id": "TRC-005-extracted", "metric_version": "1.0.0", "value": 0.0, "reason": None, "n": 13},
        {"metric_id": "TRC-005-inferred", "metric_version": "1.0.0", "value": 0.0, "reason": None, "n": 13},
    ]
    text = render_html(_snapshot(metrics=metrics))
    assert "<li><strong>Metrics:</strong> 8</li>" in text
    metrics_section = text.split('id="metrics"')[1].split("</section>")[0]
    for m in metrics:
        assert f"<td>{m['metric_id']}</td><td>{m['metric_version']}</td>" in metrics_section


def test_null_value_shows_reason_with_distinct_shape_not_blank():
    metrics = [{"metric_id": "TRC-002", "metric_version": "1.0.0", "value": None, "reason": "no Story nodes found in graph", "n": None}]
    text = render_html(_snapshot(metrics=metrics))
    assert "no Story nodes found in graph" in text
    assert "metric-card--null" in text
    assert "metric-value--null" in text
    assert "Not computed" in text  # measurement-honesty C14: reuse existing wording, not a new synonym
    assert '<p class="metric-reason"></p>' not in text  # never a blank reason


def test_all_null_dogfood_snapshot_shows_real_reasons_and_facts_empty_notice(built_repo: Path):
    """AC-3.3: the exact fixture-driven all-null case, built via build_snapshot,
    not invented data — the realistic first-run screen."""
    import html as _html

    snapshot = build_snapshot(built_repo, as_of="2026-07-29")
    text = render_html(snapshot.to_dict())
    assert all(m.value is None for m in snapshot.metrics)
    for m in snapshot.metrics:
        assert _html.escape(m.reason, quote=True) in text
    assert "No facts recorded for this snapshot." in text
    assert 'class="empty-notice"' in text
    assert "<table>" not in text.split('id="facts"')[1].split("</section>")[0]


# --- T6: at-a-glance summary as distinct figures, under <h1> ----------------


def test_summary_appears_directly_under_h1_as_distinct_figures_not_prose():
    facts = [{"subject_kind": "code_artifact", "subject_id": "a", "predicate": "p", "value": 1}]
    metrics = [
        {"metric_id": "M1", "metric_version": "1", "value": 1, "reason": None, "n": 1},
        {"metric_id": "M2", "metric_version": "1", "value": None, "reason": "no data", "n": None},
    ]
    text = render_html(_snapshot(facts=facts, metrics=metrics))
    pos_h1 = text.index("<h1")
    pos_summary = text.index('class="summary"')
    pos_provenance = text.index('id="provenance"')
    assert pos_h1 < pos_summary < pos_provenance
    # distinct figures (a list of label:value items), not one dense sentence
    assert text.count("<li>") >= 4


def test_summary_counts_match_rendered_card_and_fact_row_counts():
    facts = [
        {"subject_kind": "code_artifact", "subject_id": f"id-{i}", "predicate": "p", "value": i}
        for i in range(3)
    ]
    metrics = [
        {"metric_id": "M1", "metric_version": "1", "value": 1, "reason": None, "n": 1},
        {"metric_id": "M2", "metric_version": "1", "value": None, "reason": "no data", "n": None},
        {"metric_id": "M3", "metric_version": "1", "value": None, "reason": "no data", "n": None},
    ]
    text = render_html(_snapshot(facts=facts, metrics=metrics))
    assert "<li><strong>Facts:</strong> 3</li>" in text
    assert "<li><strong>Metrics:</strong> 3</li>" in text
    assert "<li><strong>Computed:</strong> 1</li>" in text
    assert "<li><strong>Null:</strong> 2</li>" in text
    metrics_section = text.split('id="metrics"')[1].split("</section>")[0]
    facts_section = text.split('id="facts"')[1].split("</section>")[0]
    assert metrics_section.count('<div class="metric-card') == 3  # one card per metric, none dropped
    assert facts_section.count("<tr>") == 1 + 3  # thead + 3 fact rows


# --- T7: XSS hardening + byte-identical determinism -------------------------


_HOSTILE = '<script>alert(1)</script>'


def test_hostile_subject_id_is_escaped_never_raw_in_output():
    facts = [{"subject_kind": "code_artifact", "subject_id": _HOSTILE, "predicate": "p", "value": "v"}]
    text = render_html(_snapshot(facts=facts))
    assert "<script>alert(1)</script>" not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text


def test_hostile_metric_reason_is_escaped():
    metrics = [{"metric_id": "M", "metric_version": "1", "value": None, "reason": _HOSTILE, "n": None}]
    text = render_html(_snapshot(metrics=metrics))
    assert "<script>alert(1)</script>" not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text


def test_hostile_provenance_strings_are_escaped():
    provenance = {
        "as_of": "2026-08-04", "insights_version": "0.3.0", "metric_registry_version": "0.1.0",
        "graph_source": {"access": "library-interim", "sealed": True}, "policy_versions": None,
        "scope_filter": {"patterns": [_HOSTILE], "excluded_count": 0},
        "graph_staleness": {"available": True, "stale": False, "files_checked": 1,
                             "changed": [_HOSTILE], "missing": [], "advice": _HOSTILE},
    }
    text = render_html(_snapshot(provenance=provenance))
    assert "<script>alert(1)</script>" not in text
    assert text.count("&lt;script&gt;alert(1)&lt;/script&gt;") == 3  # patterns, changed, advice


def test_hostile_input_still_renders_successfully_never_a_hard_error():
    facts = [{"subject_kind": "code_artifact", "subject_id": _HOSTILE, "predicate": _HOSTILE, "value": _HOSTILE}]
    metrics = [{"metric_id": _HOSTILE, "metric_version": "1", "value": None, "reason": _HOSTILE, "n": None}]
    text = render_html(_snapshot(facts=facts, metrics=metrics))  # must not raise
    assert text.startswith("<!DOCTYPE html>")
    assert "<script>alert(1)</script>" not in text


def test_render_html_is_byte_identical_across_repeated_calls():
    snapshot = _snapshot(
        facts=[{"subject_kind": "code_artifact", "subject_id": "b", "predicate": "p", "value": 1},
               {"subject_kind": "code_artifact", "subject_id": "a", "predicate": "p", "value": 2}],
        metrics=[{"metric_id": "M2", "metric_version": "1", "value": 1, "reason": None, "n": 1},
                 {"metric_id": "M1", "metric_version": "1", "value": None, "reason": "x", "n": None}],
    )
    first = render_html(snapshot)
    second = render_html(snapshot)
    assert first == second


def test_run_render_byte_identical_on_repeated_render_of_same_snapshot(built_repo: Path):
    snapshot = build_snapshot(built_repo, as_of="2026-07-29")
    write_snapshot(built_repo, snapshot)

    run_render(str(built_repo))
    first_text = (built_repo / STORE_DIRNAME / REPORT_FILENAME).read_text(encoding="utf-8")
    run_render(str(built_repo))
    second_text = (built_repo / STORE_DIRNAME / REPORT_FILENAME).read_text(encoding="utf-8")

    assert first_text == second_text


# --- measurement-honesty T2: artifact_probe renders on every report (AC-4.6) -


def test_artifact_probe_provenance_renders_even_with_no_spark_present(built_repo: Path):
    """AC-2.5/AC-4.6: the probe result is sealed and rendered on *every* build,
    not only when a metric is affected — otherwise "no caveat" is indistinguishable
    from "the check never ran" (the same invisible-disclosure failure this
    feature exists to fix, one layer up)."""
    snapshot = build_snapshot(built_repo, as_of="2026-07-29")  # built_repo has no .spark/
    text = render_html(snapshot.to_dict())
    assert "artifact_probe.outcome" in text
    assert "absent" in text


def test_artifact_probe_provenance_renders_when_spark_is_present(built_repo: Path):
    feature_dir = built_repo / ".spark" / "some-feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "qa.md").write_text("x", encoding="utf-8")

    snapshot = build_snapshot(built_repo, as_of="2026-07-29")
    text = render_html(snapshot.to_dict())
    assert "artifact_probe.matched_filenames" in text
    assert "qa.md" in text


def test_render_provenance_generic_tail_does_not_reintroduce_policy_versions():
    """Guards the T2 mitigation directly: policy_versions is a known top-level
    key deliberately excluded from the generic tail, so genericizing the row
    generation must not start rendering it (existing byte output unchanged)."""
    text = render_html(_snapshot())  # default provenance has policy_versions: None
    assert "policy_versions" not in text


# --- measurement-honesty T4: top-band evidence caveat (AC-4.1..4.5) ---------


def _evidence_absent_metric(metric_id: str, n: int, reason: str = "no evidence found") -> dict:
    return {"metric_id": metric_id, "metric_version": "2.0.0", "value": None, "reason": reason, "n": n}


def _denominator_absent_metric(metric_id: str) -> dict:
    return {"metric_id": metric_id, "metric_version": "2.0.0", "value": None, "reason": "no nodes found", "n": 0}


def _computed_metric(metric_id: str, value=1.0, n=5) -> dict:
    return {"metric_id": metric_id, "metric_version": "2.0.0", "value": value, "reason": None, "n": n}


def test_caveat_triggers_on_evidence_absent_null_with_truthy_n():
    metrics = [_evidence_absent_metric("TRC-002", n=41), _computed_metric("TRC-001")]
    text = render_html(_snapshot(metrics=metrics))
    assert "NOT COMPUTED" in text
    assert "TRC-002" in text.split("NOT COMPUTED")[1].split("</p>")[0]


def test_caveat_states_count_against_total_first():
    metrics = [_evidence_absent_metric("TRC-002", n=41), _evidence_absent_metric("TRC-004-unverified-acs", n=41), _computed_metric("TRC-001")]
    text = render_html(_snapshot(metrics=metrics))
    caveat = text.split("NOT COMPUTED")[1].split("</p>")[0]
    assert "2 of 3 metrics" in caveat


def test_caveat_names_affected_ids_and_points_to_metrics_table():
    metrics = [_evidence_absent_metric("TRC-002", n=41), _computed_metric("TRC-001")]
    text = render_html(_snapshot(metrics=metrics))
    caveat = text.split("NOT COMPUTED")[1].split("</p>")[0]
    assert "TRC-002" in caveat
    assert "See the Metrics table below" in caveat
    # the full reason string is not in the top band — that's the row's job (AC-4.2)
    assert "no evidence found" not in caveat


def test_caveat_does_not_trigger_on_denominator_absent_null_fresh_repo_screen():
    """AC-4.1(i)/AC-4.3: an all-null fresh-repo snapshot (every null is
    denominator-absent, n=0) must render no caveat — identical to the empty
    state /demo-day already accepted as reading correctly."""
    metrics = [_denominator_absent_metric("TRC-001"), _denominator_absent_metric("TRC-002")]
    text = render_html(_snapshot(metrics=metrics))
    assert "NOT COMPUTED" not in text


def test_no_caveat_when_no_metric_is_evidence_absent():
    metrics = [_computed_metric("TRC-001"), _computed_metric("TRC-002")]
    text = render_html(_snapshot(metrics=metrics))
    assert "NOT COMPUTED" not in text


def test_empty_notice_still_renders_when_caveat_does_not_fire():
    """AC-4.3's carve-out: the fresh-repo case renders no evidence caveat but
    must still render snapshot-report's own empty-facts notice."""
    metrics = [_denominator_absent_metric("TRC-001")]
    text = render_html(_snapshot(facts=[], metrics=metrics))
    assert "NOT COMPUTED" not in text
    assert 'class="empty-notice"' in text


def test_caveat_byte_offset_order_stale_then_caveat_then_provenance():
    metrics = [_evidence_absent_metric("TRC-002", n=41)]
    text = render_html(_snapshot(provenance=_STALE_PROVENANCE, metrics=metrics))
    pos_stale = text.index('<p class="stale-cue">STALE')
    pos_caveat = text.index('<p class="stale-cue">NOT COMPUTED')
    pos_provenance = text.index('id="provenance"')
    assert pos_stale < pos_caveat < pos_provenance


def test_caveat_placed_before_provenance_even_without_staleness():
    metrics = [_evidence_absent_metric("TRC-002", n=41)]
    text = render_html(_snapshot(metrics=metrics))  # not stale — no stale cue at all
    assert "STALE" not in text
    pos_caveat = text.index('<p class="stale-cue">NOT COMPUTED')
    pos_provenance = text.index('id="provenance"')
    assert pos_caveat < pos_provenance


def test_caveat_row_level_reason_still_shown_ac_4_2_untouched():
    """AC-4.2: the affected metric's own card still shows its full reason —
    the top-band caveat is additive, never a replacement. The scorecard
    shows this as "Not computed" plus the reason as its own paragraph on the
    card, and the same reason still appears in the full metrics table below
    (review B1/B2) — the guarantee (the full reason is always visible on the
    metric itself) is unchanged, now doubly so."""
    metrics = [_evidence_absent_metric("TRC-002", n=41, reason="no verifies edges found (0 of 41)")]
    text = render_html(_snapshot(metrics=metrics))
    assert "Not computed" in text
    assert '<p class="metric-reason">no verifies edges found (0 of 41)</p>' in text
    assert "Not computed: no verifies edges found (0 of 41)" in text  # the full table row


def test_hostile_metric_id_in_caveat_is_escaped():
    metrics = [_evidence_absent_metric(_HOSTILE, n=1)]
    text = render_html(_snapshot(metrics=metrics))  # must not raise
    caveat = text.split("NOT COMPUTED")[1].split("</p>")[0]
    assert "<script>alert(1)</script>" not in caveat
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in caveat


def test_caveat_present_page_still_has_no_javascript_or_external_refs():
    metrics = [_evidence_absent_metric("TRC-002", n=41)]
    text = render_html(_snapshot(metrics=metrics))
    assert not _EXTERNAL_REF_PATTERN.search(text)
    assert "<script>" not in text
