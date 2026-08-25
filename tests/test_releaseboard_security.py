"""RM-T9: hardening — hand-crafted hostile fixtures built fresh for this
pass, run through both `--format json` and `--format html` (the JSON path
now reads each feature's own `spec.md` body for the first time — T4's
disclosed new attack surface)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from aspark_insights.errors import ReleaseMapUnreadableError
from aspark_insights.gitboard.releaseboard_report import render_release_board_html, run_release_board_report

_SCRIPT_TAG = "<script>alert(1)</script>"


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


def _commit(repo: Path, path: str, subject: str, content: str | None = None) -> None:
    full = repo / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content if content is not None else subject, encoding="utf-8")
    _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", subject)


@pytest.fixture
def hostile_tag_repo(tmp_path: Path) -> Path:
    """A real git tag literally named with a `<script>` payload — git's own
    ref-name rules permit `<`/`>`/`(`/`)`; only whitespace, `~^:?*[\\`,
    leading `-`, and a handful of other forms are actually forbidden."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _commit(repo, ".spark/feature-x/spec.md", "feat: spec", "### US-1 a story\n\n- [ ] AC-1.1 an ac\n")
    _git(repo, "tag", _SCRIPT_TAG)
    return repo


@pytest.fixture
def hostile_spec_repo(tmp_path: Path) -> Path:
    """A `spec.md` whose US heading and AC checkbox lines carry raw markup
    and control characters — the JSON path's new read surface (T4)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    hostile_spec = (
        "### US-1 <img src=x onerror=alert(1)> a story\x00\x07\n\n"
        "- [ ] AC-1.1 <script>alert(2)</script>\n"
        "- [x] AC-1.2 normal\n"
    )
    _commit(repo, ".spark/feature-x/spec.md", "feat: spec", hostile_spec)
    _git(repo, "tag", "v1.0.0")
    return repo


# --- hostile tag name: end to end, every surface, exit 0 -----------------------


def test_hostile_tag_json_path_exits_0_and_is_valid_json(hostile_tag_repo: Path):
    result = _run_cli(hostile_tag_repo, "releases", "--as-of", "2026-08-10", "--format", "json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["releases"][0]["tag"] == _SCRIPT_TAG  # verbatim, not sanitized in the data layer


def test_hostile_tag_html_path_exits_0_and_script_is_inert_everywhere(hostile_tag_repo: Path, tmp_path: Path):
    out = tmp_path / "out"
    result = _run_cli(hostile_tag_repo, "releases", "--as-of", "2026-08-10", "--format", "html", "--output", str(out))
    assert result.returncode == 0
    html_path = json.loads(result.stdout)["report"]
    html = Path(html_path).read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    # band, index, card heading, and cadence "from -> to" cells are all
    # inert — a raw `<script>` substring anywhere would already have
    # failed the assertion above across the whole page.


# --- hostile spec.md body: JSON path (new surface) and HTML path --------------


def test_hostile_spec_json_path_never_raises_and_counts_or_nulls_honestly(hostile_spec_repo: Path):
    result = _run_cli(hostile_spec_repo, "releases", "--as-of", "2026-08-10", "--format", "json")
    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stdout)
    scope = payload["releases"][0]["members"][0]["scope"]
    # the heading itself is malformed prose but still matches `### US-\d+`
    # at the line start, so a real (not estimated) count is honest here.
    assert scope["us"] == 1
    assert scope["acs"] == 2


def test_hostile_spec_html_path_renders_hostile_content_inert(hostile_spec_repo: Path, tmp_path: Path):
    out = tmp_path / "out"
    result = _run_cli(hostile_spec_repo, "releases", "--as-of", "2026-08-10", "--format", "html", "--output", str(out))
    assert result.returncode == 0
    html_path = json.loads(result.stdout)["report"]
    html = Path(html_path).read_text(encoding="utf-8")
    assert "<script>alert(2)</script>" not in html
    assert "<img src=x onerror=alert(1)>" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html  # inert text, angle brackets escaped


# --- malformed release-map dict never a raw traceback --------------------------


def test_malformed_release_map_missing_new_keys_raises_named_error_not_a_traceback(tmp_path: Path):
    malformed = {
        "provenance": {}, "reason": None, "figures": None,
        "releases": [{"tag": "v1.0.0", "members": [{"name": "x", "status": {}}], "unattributed": []}],
        # commit_count/date/delivered_scope/delivery/scope all missing
    }
    with pytest.raises(ReleaseMapUnreadableError):
        run_release_board_report(malformed, str(tmp_path))


def test_malformed_release_map_pure_render_raises_key_or_attribute_error_not_something_worse():
    malformed = {"releases": [{"tag": "v1.0.0", "members": [], "unattributed": []}], "reason": None, "figures": None}
    with pytest.raises((KeyError, AttributeError, TypeError)):
        render_release_board_html(malformed)


# --- 0-, 1-, 2-tag repos each render without error, end to end ----------------


@pytest.mark.parametrize("tag_count", [0, 1, 2])
def test_n_tag_repo_renders_html_without_error(tmp_path: Path, tag_count: int):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    for i in range(tag_count):
        _git(repo, "tag", f"v{i + 1}.0.0")
        _git(repo, "commit", "--allow-empty", "-q", "-m", f"feat: {i}")
    out = tmp_path / "out"
    result = _run_cli(repo, "releases", "--as-of", "2026-08-10", "--format", "html", "--output", str(out))
    assert result.returncode == 0, result.stderr
    html_path = json.loads(result.stdout)["report"]
    html = Path(html_path).read_text(encoding="utf-8")
    assert "Traceback" not in html
    assert html.count("<h1") == 1


def test_unreadable_tag_date_html_renders_the_reason_not_a_traceback(monkeypatch, tmp_path: Path):
    from aspark_insights.gitboard import gitread
    from aspark_insights.gitboard.releasemap import build_release_map

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    monkeypatch.setattr(gitread, "tag_commit_date", lambda repo_root, tag: None)
    data = build_release_map(str(repo), "2026-08-10")
    html = render_release_board_html(data)
    assert "Traceback" not in html
    assert "tag commit date could not be read" in html
