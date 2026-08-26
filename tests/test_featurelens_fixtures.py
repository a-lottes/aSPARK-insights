"""FL-T3: the six-stage fixture — real git, no mocks (feature-lens AC-2.3,
AC-2.4). This is the one test that proves the full six gate states end to
end, since this repo's own real data cannot (A3/C8: every real feature here
is `Released`)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.featurelens import build_feature_lens
from aspark_insights.gitboard.releasemap import build_release_map


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


def _commit(repo: Path, path: str, subject: str, content: str) -> None:
    full = repo / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", subject)


def _artifact(status: str, date: str = "2026-08-01") -> str:
    return f"# Doc\n\n| | |\n|---|---|\n| **Status** | `{status}` |\n| **Date** | {date} |\n"


@pytest.fixture
def six_stage_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")

    # at-spec: only spec.md
    _commit(repo, ".spark/at-spec/spec.md", "feat: at-spec spec", _artifact("draft"))

    # at-increment: spec approved, plan approved, no review.md
    _commit(repo, ".spark/at-increment/spec.md", "feat: at-increment spec", _artifact("approved"))
    _commit(repo, ".spark/at-increment/plan.md", "feat: at-increment plan", _artifact("approved"))

    # at-review: + review.md
    _commit(repo, ".spark/at-review/spec.md", "feat: at-review spec", _artifact("approved"))
    _commit(repo, ".spark/at-review/plan.md", "feat: at-review plan", _artifact("approved"))
    _commit(repo, ".spark/at-review/review.md", "feat: at-review review", _artifact("passed"))

    # at-qa: + qa.md
    _commit(repo, ".spark/at-qa/spec.md", "feat: at-qa spec", _artifact("approved"))
    _commit(repo, ".spark/at-qa/plan.md", "feat: at-qa plan", _artifact("approved"))
    _commit(repo, ".spark/at-qa/review.md", "feat: at-qa review", _artifact("passed"))
    _commit(repo, ".spark/at-qa/qa.md", "feat: at-qa qa", _artifact("passed"))

    # at-released: full 5-artifact set
    _commit(repo, ".spark/at-released/spec.md", "feat: at-released spec", _artifact("approved"))
    _commit(repo, ".spark/at-released/plan.md", "feat: at-released plan", _artifact("approved"))
    _commit(repo, ".spark/at-released/review.md", "feat: at-released review", _artifact("passed"))
    _commit(repo, ".spark/at-released/qa.md", "feat: at-released qa", _artifact("passed"))
    _commit(repo, ".spark/at-released/release.md", "feat: at-released release", _artifact("released"))
    _git(repo, "tag", "v1.0.0")

    # at-unknown: spec.md with no header table at all
    _commit(repo, ".spark/at-unknown/spec.md", "feat: at-unknown spec", "# Just prose\n\nno table here.\n")
    _git(repo, "tag", "v2.0.0")

    return repo


def test_six_stages_each_produce_exactly_their_own_expected_gate(six_stage_repo: Path):
    release_map = build_release_map(str(six_stage_repo), "2026-08-25")
    result = build_feature_lens(release_map)
    gates = {f["name"]: f["gate"] for f in result["features"]}
    assert gates["at-spec"] == "Spec"
    assert gates["at-increment"] == "Increment"
    assert gates["at-review"] == "Review"
    assert gates["at-qa"] == "QA"
    assert gates["at-released"] == "Released"
    assert gates["at-unknown"] == "Unknown"


def test_at_increment_gate_evidence_names_missing_review_not_started(six_stage_repo: Path):
    """AC-2.3."""
    release_map = build_release_map(str(six_stage_repo), "2026-08-25")
    result = build_feature_lens(release_map)
    row = next(f for f in result["features"] if f["name"] == "at-increment")
    assert row["gate_artifact"] == "plan"
    review_evidence = next(e for e in row["gate_evidence"] if e["artifact"] == "review")
    assert review_evidence["status"] is None
    assert review_evidence["reason"] is not None


def test_at_unknown_gate_surfaces_its_own_reason_not_guessed_as_spec(six_stage_repo: Path):
    """AC-2.4: never guessed as `Spec` just because the directory exists."""
    release_map = build_release_map(str(six_stage_repo), "2026-08-25")
    result = build_feature_lens(release_map)
    row = next(f for f in result["features"] if f["name"] == "at-unknown")
    assert row["gate"] == "Unknown"
    assert row["gate_artifact"] is None
    assert row["gate_evidence"][0]["reason"] is not None


def test_spec_with_status_row_but_no_date_row_names_its_own_date_reason(tmp_path: Path):
    """review F1/F10, end to end on real git (not a hand-built dict): a
    header table carrying `**Status**` but no `**Date**` row is an ordinary
    shape, and it must never ship `spec_date: null` with a null reason
    (AC-1.4/NFR-5). The prescribed fixture for F1's fix, added at re-review."""
    repo = tmp_path / "dateless"
    repo.mkdir()
    _git(repo, "init", "-q")
    _commit(
        repo, ".spark/no-date-row/spec.md", "feat: no-date-row spec",
        "# Doc\n\n| | |\n|---|---|\n| **Phase** | Spec |\n| **Status** | `in-review` |\n\n## Body\n",
    )
    _git(repo, "tag", "v1.0.0")

    result = build_feature_lens(build_release_map(str(repo), "2026-08-25"))
    row = next(f for f in result["features"] if f["name"] == "no-date-row")
    assert row["spec_date"] is None
    assert row["spec_date_reason"] == "no Date row found in header table"
    assert row["gate"] == "Spec"  # the Status row is still read; only the date degrades


def test_pipeline_buckets_each_show_exactly_their_one_expected_feature(six_stage_repo: Path):
    """AC-3.3."""
    from aspark_insights.gitboard.featurelens import group_by_gate

    release_map = build_release_map(str(six_stage_repo), "2026-08-25")
    result = build_feature_lens(release_map)
    buckets = dict(group_by_gate(result["features"]))
    assert [m["name"] for m in buckets["Spec"]] == ["at-spec"]
    assert [m["name"] for m in buckets["Increment"]] == ["at-increment"]
    assert [m["name"] for m in buckets["Review"]] == ["at-review"]
    assert [m["name"] for m in buckets["QA"]] == ["at-qa"]
    assert [m["name"] for m in buckets["Released"]] == ["at-released"]
    assert [m["name"] for m in buckets["Unknown"]] == ["at-unknown"]
