"""FL-T6: hardening — a fresh hostile fixture (not copied from any prior
feature's), both formats, real CLI (feature-lens NFR-3)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.errors import ReleaseMapUnreadableError
from aspark_insights.gitboard.featurelens_report import run_feature_lens_report

_SCRIPT_TAG = "<script>evil()</script>"
# No `/` here (unlike the tag above): a feature name becomes a real
# filesystem directory (.spark/<name>/), where `/` would create nested
# directories instead of one hostile directory name — a different failure
# mode than a git ref, which tolerates embedded `/` as hierarchical
# namespacing without corrupting the logical tag name.
_SCRIPT_FEATURE = "<img src=x onerror=evil()>"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aspark_insights.cli", *args],
        capture_output=True, text=True, cwd=repo,
    )


def _commit(repo: Path, path: str, subject: str, content: str) -> None:
    full = repo / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", subject)


@pytest.fixture
def hostile_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    hostile_spec = (
        "# Doc\n\n| | |\n|---|---|\n"
        f"| **Status** | `{_SCRIPT_FEATURE}` |\n"
        "| **Date** | 2026-08-01 |\n"
    )
    _commit(repo, f".spark/{_SCRIPT_FEATURE}/spec.md", "feat: hostile spec", hostile_spec)
    _git(repo, "tag", _SCRIPT_TAG)
    return repo


def test_hostile_feature_directory_name_and_tag_json_exits_0(hostile_repo: Path):
    result = _run_cli(hostile_repo, "features", "--as-of", "2026-08-10", "--format", "json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["features"][0]["name"] == _SCRIPT_FEATURE  # verbatim, not sanitized in the data layer
    assert payload["features"][0]["delivered_in"] == _SCRIPT_TAG


def test_hostile_feature_directory_name_and_tag_html_is_inert(hostile_repo: Path, tmp_path: Path):
    out = tmp_path / "out"
    result = _run_cli(hostile_repo, "features", "--as-of", "2026-08-10", "--format", "html", "--output", str(out))
    assert result.returncode == 0, result.stderr
    html_path = json.loads(result.stdout)["report"]
    html = Path(html_path).read_text(encoding="utf-8")
    assert "<script>evil()</script>" not in html
    assert "&lt;script&gt;evil()&lt;/script&gt;" in html
    assert html.count("<script") == 0  # no real <script> tag anywhere on the page


def test_unreadable_spec_no_artifacts_zero_feature_repo_never_raise(tmp_path: Path):
    # unreadable spec.md
    bad = tmp_path / "bad"
    bad.mkdir()
    _git(bad, "init", "-q")
    _commit(bad, ".spark/broken/spec.md", "feat: broken", "# no header table at all\n")
    _git(bad, "tag", "v1.0.0")
    result = _run_cli(bad, "features", "--as-of", "2026-08-10", "--format", "json")
    assert result.returncode == 0
    assert "Traceback" not in result.stderr

    # feature directory with no artifacts at all (empty dir)
    none_ = tmp_path / "none"
    none_.mkdir()
    _git(none_, "init", "-q")
    (none_ / ".spark" / "empty-feature").mkdir(parents=True)
    _git(none_, "commit", "--allow-empty", "-q", "-m", "feat: no artifacts")
    result = _run_cli(none_, "features", "--as-of", "2026-08-10", "--format", "json")
    assert result.returncode == 0
    assert "Traceback" not in result.stderr

    # zero-feature .spark/
    zero = tmp_path / "zero"
    zero.mkdir()
    _git(zero, "init", "-q")
    _git(zero, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(zero, "tag", "v1.0.0")
    result = _run_cli(zero, "features", "--as-of", "2026-08-10", "--format", "json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["features"] == []


def test_malformed_release_map_raises_named_error_not_traceback():
    """review F2: the plan pinned a `ReleaseMapUnreadableError` boundary in
    `build_feature_lens` itself — this must assert the named error, not the
    raw exception classes it wraps."""
    from aspark_insights.gitboard.featurelens import build_feature_lens

    with pytest.raises(ReleaseMapUnreadableError):
        build_feature_lens({})
    with pytest.raises(ReleaseMapUnreadableError):
        build_feature_lens(None)


def test_malformed_feature_lens_data_raises_named_error_via_report_writer(tmp_path: Path):
    malformed = {"features": [{"name": "x"}]}  # missing every other required key
    with pytest.raises(ReleaseMapUnreadableError):
        run_feature_lens_report(malformed, str(tmp_path))
