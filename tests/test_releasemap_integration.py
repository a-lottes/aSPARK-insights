"""RB-T8: real-history smoke test + privacy integration (AC-1.2, AC-1.6,
NFR-3, NFR-4)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aspark_insights.gitboard.releasemap import build_release_map


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


# --- Real-history smoke test: this repo's own frozen v0.2.0..v0.3.0 --------


def test_frozen_v0_3_0_range_yields_the_real_three_members():
    """The `v0.2.0..v0.3.0` range is frozen, immutable past history — this
    pins that real fact directly, no synthetic fixture involved, no
    HEAD-dependent count (AC-1.2)."""
    repo_root = Path(__file__).resolve().parents[1]
    result = build_release_map(str(repo_root), "2026-08-19")
    v3 = next(r for r in result["releases"] if r["tag"] == "v0.3.0")
    names = sorted(m["name"] for m in v3["members"])
    assert names == ["mcp-server", "public-repo-polish", "traceability-metrics"]


def test_every_real_tag_appears_exactly_once():
    repo_root = Path(__file__).resolve().parents[1]
    result = build_release_map(str(repo_root), "2026-08-19")
    real_tags = [r["tag"] for r in result["releases"] if r["tag"] is not None]
    assert len(real_tags) == len(set(real_tags))
    known = {"v0.1.0", "v0.2.0", "v0.3.0", "v0.4.0", "v0.5.0"}
    assert known <= set(real_tags)


def test_exactly_one_pseudo_release_whose_previous_tag_is_the_latest_real_tag():
    repo_root = Path(__file__).resolve().parents[1]
    result = build_release_map(str(repo_root), "2026-08-19")
    real_tags = [r["tag"] for r in result["releases"] if r["tag"] is not None]
    pseudo_entries = [r for r in result["releases"] if r["tag"] is None]
    assert len(pseudo_entries) == 1
    assert pseudo_entries[0]["previous_tag"] == real_tags[-1]


# --- NFR-3/NFR-4: no identity/trailer field, live constraint ---------------


def test_co_authored_by_trailer_never_reaches_release_map_output(tmp_path: Path):
    repo = tmp_path / "trailered"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    message = "feat: paired work\n\nCo-Authored-By: Someone Else <someone@example.com>"
    _git(repo, "commit", "--allow-empty", "-q", "-m", message)

    result = build_release_map(str(repo), "2026-08-19")
    blob = json.dumps(result)
    for token in ("Co-Authored-By", "someone@example.com", "Someone Else", "Test", "t@example.com"):
        assert token not in blob


def test_signed_off_by_trailer_never_reaches_release_map_output(tmp_path: Path):
    repo = tmp_path / "signedoff"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    message = "fix: something\n\nSigned-off-by: Test <t@example.com>"
    _git(repo, "commit", "--allow-empty", "-q", "-m", message)

    result = build_release_map(str(repo), "2026-08-19")
    blob = json.dumps(result)
    assert "Signed-off-by" not in blob
