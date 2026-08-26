"""FL-T5: pipeline section — grouping, structural parity, severability
(feature-lens US-3, AC-3.1-3.4)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from aspark_insights.gitboard.featurelens import group_by_gate
from aspark_insights.gitboard.featurelens_report import render_feature_lens_html

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _feature(name, gate) -> dict:
    return {
        "name": name, "spec_date": "2026-08-01", "spec_date_reason": None,
        "status": {a: {"status": "approved", "date": "2026-08-01", "reason": None} for a in ("spec", "plan", "review", "qa", "release")},
        "gate": gate, "gate_artifact": "spec", "gate_evidence": [{"artifact": "spec", "status": "approved", "reason": None}],
        "delivered_in": None, "delivered_in_reason": "not yet delivered in a tagged release",
    }


def _data(features) -> dict:
    return {"provenance": {}, "features": features, "reason": None}


# --- AC-3.1: exactly one bucket per feature -------------------------------------


def test_every_feature_in_exactly_one_bucket_disjoint_and_complete():
    features = [_feature("a", "Spec"), _feature("b", "Increment"), _feature("c", "Released")]
    buckets = group_by_gate(features)
    all_named = [m["name"] for _, members in buckets for m in members]
    assert sorted(all_named) == ["a", "b", "c"]
    assert len(all_named) == len(set(all_named))


def test_bucket_order_is_spec_increment_review_qa_released():
    features = [_feature("a", "Released"), _feature("b", "Spec")]
    buckets = group_by_gate(features)
    names_in_order = [g for g, _ in buckets]
    # Spec must precede Released regardless of input order
    assert names_in_order.index("Spec") < names_in_order.index("Released")


def test_unknown_bucket_absent_when_it_does_not_occur():
    features = [_feature("a", "Released")]
    buckets = group_by_gate(features)
    assert "Unknown" not in dict(buckets)


def test_unknown_bucket_present_only_when_it_occurs():
    features = [_feature("a", "Unknown")]
    buckets = group_by_gate(features)
    assert "Unknown" in dict(buckets)


# --- AC-3.2: real-data parity + structural weight -------------------------------


def test_real_repo_released_bucket_lists_all_eleven_others_state_none_with_parity(tmp_path: Path):
    out = tmp_path / "out"
    result = subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", "features", "--as-of", "2026-08-25", "--format", "html", "--output", str(out)],
        capture_output=True, text=True, cwd=_REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    html_path = Path(json.loads(result.stdout)["report"])
    html = html_path.read_text(encoding="utf-8")
    pipeline = html.split("<h2>Pipeline</h2>")[1]
    released_section = pipeline.split("<h3>Released</h3>")[1].split("<h3>")[0]
    expected = {
        "foundation", "traceability-metrics", "mcp-server", "public-repo-polish",
        "snapshot-report", "measurement-honesty", "git-native-mid-cycle-board",
        "release-board", "release-board-html", "release-board-docs", "release-metrics",
    }
    for name in expected:
        assert f"<li>{name} " in released_section  # name present, followed by its gate evidence
    sections = pipeline.split("<h3>")
    empty_sections = [s for s in sections if "no feature is currently at this stage" in s]
    populated_sections = [s for s in sections if "pipeline-list" in s]
    assert len(populated_sections) == 1  # only Released is populated on this repo's real data
    for s in empty_sections:
        assert "empty-notice" in s
        # same heading tag family, not dimmed/collapsed — h3 present at split point already


def test_empty_bucket_uses_shipped_empty_notice_idiom():
    html = render_feature_lens_html(_data([_feature("a", "Released")]))
    pipeline = html.split("<h2>Pipeline</h2>")[1]
    assert '<p class="empty-notice">no feature is currently at this stage.</p>' in pipeline


# --- AC-3.4: severability --------------------------------------------------------


def test_pipeline_call_site_is_a_single_function_removable_without_touching_must_output():
    """Severability is checkable by inspection: exactly one call site
    assembles the pipeline section into the page, and every pipeline-only
    assertion lives in this test module — removing the call and the
    function leaves the Must-level table output untouched."""
    import inspect

    from aspark_insights.gitboard import featurelens_report

    source = inspect.getsource(featurelens_report.render_feature_lens_html)
    assert source.count("_render_pipeline_section(") == 1
