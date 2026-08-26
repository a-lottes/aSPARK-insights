"""FL-T7: determinism, offline, edge-repo shapes (feature-lens NFR-6, NFR-7)."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.featurelens import build_feature_lens
from aspark_insights.gitboard.featurelens_report import render_feature_lens_html
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
def real_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _commit(repo, ".spark/feature-a/spec.md", "feat: a spec", _artifact("approved"))
    _commit(repo, ".spark/feature-a/release.md", "feat: a release", _artifact("released"))
    _git(repo, "tag", "v1.0.0")
    return repo


def test_no_datetime_now_in_either_new_module():
    for path in ("src/aspark_insights/gitboard/featurelens.py", "src/aspark_insights/gitboard/featurelens_report.py"):
        source = Path(path).read_text(encoding="utf-8")
        assert "datetime.now" not in source
        assert "date.today" not in source


def test_two_json_builds_at_fixed_head_are_byte_identical(real_repo: Path):
    rm1 = build_release_map(str(real_repo), "2026-08-20")
    rm2 = build_release_map(str(real_repo), "2026-08-20")
    assert build_feature_lens(rm1) == build_feature_lens(rm2)


def test_two_html_renders_are_byte_identical(real_repo: Path):
    rm = build_release_map(str(real_repo), "2026-08-20")
    fl = build_feature_lens(rm)
    assert render_feature_lens_html(fl) == render_feature_lens_html(fl)


def test_page_has_no_external_reference_and_no_own_script_tag(real_repo: Path):
    rm = build_release_map(str(real_repo), "2026-08-20")
    fl = build_feature_lens(rm)
    html = render_feature_lens_html(fl)
    assert "http://" not in html
    assert "https://" not in html
    assert 'src="//' not in html  # protocol-relative external reference
    assert 'href="//' not in html
    assert "<script" not in html


@pytest.mark.parametrize("tag_count,feature_count", [(0, 0), (0, 1), (1, 1)])
def test_edge_repo_shapes_render_without_error(tmp_path: Path, tag_count: int, feature_count: int):
    repo = tmp_path / f"repo-{tag_count}-{feature_count}"
    repo.mkdir()
    _git(repo, "init", "-q")
    for i in range(feature_count):
        _commit(repo, f".spark/feature-{i}/spec.md", f"feat: {i}", _artifact("approved"))
    if not feature_count:
        _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    for i in range(tag_count):
        _git(repo, "tag", f"v{i + 1}.0.0")
    rm = build_release_map(str(repo), "2026-08-20")
    fl = build_feature_lens(rm)
    html = render_feature_lens_html(fl)
    # the real check is "it didn't raise" (a raise never reaches this line at
    # all) — assert the page is genuinely a complete, well-formed document,
    # not a vacuous substring that can never be false.
    assert html.startswith("<!DOCTYPE html>")
    assert html.rstrip().endswith("</html>")


def test_zero_tag_repo_states_its_own_reason_in_words(tmp_path: Path):
    repo = tmp_path / "notags"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    rm = build_release_map(str(repo), "2026-08-20")
    fl = build_feature_lens(rm)
    assert fl["features"] == []
    assert fl["reason"] == "repository has no tags"
    html = render_feature_lens_html(fl)
    assert "repository has no tags" in html


def test_full_history_of_this_repo_renders_end_to_end():
    """This repo's own 11-feature history — the third edge shape NFR-7
    names explicitly."""
    repo_root = Path(__file__).resolve().parent.parent
    rm = build_release_map(str(repo_root), "2026-08-25")
    fl = build_feature_lens(rm)
    html = render_feature_lens_html(fl)
    assert len(fl["features"]) >= 11
    assert "Traceback" not in html
