"""RM-T4: delivery attribution — a feature is "delivering" in exactly its
oldest release appearance (A3), and per-release `delivered_scope` sums
`scope` over delivering members only (US-2, AC-2.1-2.4, AC-3.4)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.releasemap import build_release_map

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


def _commit(repo: Path, path: str, subject: str, content: str | None = None) -> None:
    full = repo / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content if content is not None else subject, encoding="utf-8")
    _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", subject)


def _spec(us_count: int, ac_per_us: int) -> str:
    body = "# spec\n\n"
    for u in range(1, us_count + 1):
        body += f"### US-{u} a story\n\n"
        for a in range(1, ac_per_us + 1):
            body += f"- [ ] AC-{u}.{a} an ac\n"
        body += "\n"
    return body


def _member(release: dict, name: str) -> dict:
    return next(m for m in release["members"] if m["name"] == name)


@pytest.fixture
def two_release_repo(tmp_path: Path) -> Path:
    """feature-x ships in v1.0.0 (US=2/AC=4) fully; feature-y ships across
    both v1.0.0 (partial) and v2.0.0 (trailing docs commit) — mirrors this
    repo's own v0.6.0/measurement-honesty shape."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _commit(repo, ".spark/feature-x/spec.md", "feat: feature-x spec", _spec(2, 2))
    _commit(repo, ".spark/feature-y/spec.md", "feat: feature-y spec", _spec(3, 5))
    _git(repo, "tag", "v1.0.0")
    _commit(repo, ".spark/feature-y/release.md", "docs: record feature-y release report")
    _git(repo, "tag", "v2.0.0")
    return repo


def test_feature_delivers_in_its_oldest_appearance(two_release_repo: Path):
    result = build_release_map(str(two_release_repo), "2026-08-10")
    v1 = result["releases"][0]
    fy = _member(v1, "feature-y")
    assert fy["delivery"] == {"delivering": True, "delivered_in": None, "reason": None}


def test_later_appearance_is_trailing_not_delivering(two_release_repo: Path):
    result = build_release_map(str(two_release_repo), "2026-08-10")
    v2 = result["releases"][1]
    fy = _member(v2, "feature-y")
    assert fy["delivery"] == {"delivering": False, "delivered_in": "v1.0.0", "reason": None}


def test_delivered_scope_sums_only_delivering_members(two_release_repo: Path):
    result = build_release_map(str(two_release_repo), "2026-08-10")
    v1 = result["releases"][0]
    # feature-x: 2 US / 4 AC; feature-y: 3 US / 15 AC -> 5 / 19 total
    assert v1["delivered_scope"] == {
        "us": 5, "acs": 19, "n": 2, "unreadable": [], "reason": None,
    }


def test_trailing_only_release_has_honest_zero_scope_not_null(two_release_repo: Path):
    result = build_release_map(str(two_release_repo), "2026-08-10")
    v2 = result["releases"][1]
    assert v2["delivered_scope"] == {
        "us": 0, "acs": 0, "n": 0, "unreadable": [], "reason": None,
    }


def test_feature_only_in_open_window_is_not_delivering(two_release_repo: Path):
    _commit(two_release_repo, ".spark/feature-z/spec.md", "feat: feature-z spec", _spec(1, 1))
    result = build_release_map(str(two_release_repo), "2026-08-10")
    pseudo = result["releases"][-1]
    assert pseudo["tag"] is None
    fz = _member(pseudo, "feature-z")
    assert fz["delivery"] == {
        "delivering": False, "delivered_in": None,
        "reason": "not yet delivered in a tagged release",
    }
    # and it contributes to no real release's delivered_scope
    for r in result["releases"]:
        if r["tag"] is not None:
            assert "feature-z" not in [m["name"] for m in r["members"] if m["delivery"]["delivering"]]


def test_unparseable_delivering_member_scope_excluded_but_named(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _commit(repo, ".spark/good/spec.md", "feat: good spec", _spec(2, 3))
    _commit(repo, ".spark/bad/spec.md", "feat: bad spec", "# no story heading at all\n")
    _git(repo, "tag", "v1.0.0")
    result = build_release_map(str(repo), "2026-08-10")
    v1 = result["releases"][0]
    assert v1["delivered_scope"]["us"] == 2
    assert v1["delivered_scope"]["acs"] == 6
    assert v1["delivered_scope"]["n"] == 1
    assert v1["delivered_scope"]["unreadable"] == ["bad"]
    assert v1["delivered_scope"]["reason"] is None


def test_all_delivering_members_unreadable_is_null_not_a_folded_zero(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _commit(repo, ".spark/bad/spec.md", "feat: bad spec", "# no story heading at all\n")
    _git(repo, "tag", "v1.0.0")
    result = build_release_map(str(repo), "2026-08-10")
    v1 = result["releases"][0]
    assert v1["delivered_scope"] == {
        "us": None, "acs": None, "n": 0, "unreadable": ["bad"],
        "reason": "no delivering member's scope could be read",
    }


def test_no_delivering_members_at_all_is_a_true_zero(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: no feature dirs")
    _git(repo, "tag", "v1.0.0")
    result = build_release_map(str(repo), "2026-08-10")
    v1 = result["releases"][0]
    assert v1["delivered_scope"] == {
        "us": 0, "acs": 0, "n": 0, "unreadable": [], "reason": None,
    }


# --- against this repo's own real, measured delivery mapping (T4 DoD) -------


def test_real_repo_v0_6_0_has_zero_delivering_and_trailing_measurement_honesty():
    result = build_release_map(str(_REPO_ROOT), "2026-08-24")
    v060 = next(r for r in result["releases"] if r["tag"] == "v0.6.0")
    assert v060["delivered_scope"] == {
        "us": 0, "acs": 0, "n": 0, "unreadable": [], "reason": None,
    }
    mh = _member(v060, "measurement-honesty")
    assert mh["delivery"] == {"delivering": False, "delivered_in": "v0.5.0", "reason": None}


def test_real_repo_delivered_scope_at_v0_3_0_v0_5_0_v0_9_0():
    result = build_release_map(str(_REPO_ROOT), "2026-08-24")
    by_tag = {r["tag"]: r for r in result["releases"] if r["tag"] is not None}
    assert (by_tag["v0.3.0"]["delivered_scope"]["us"], by_tag["v0.3.0"]["delivered_scope"]["acs"]) == (7, 24)
    assert (by_tag["v0.5.0"]["delivered_scope"]["us"], by_tag["v0.5.0"]["delivered_scope"]["acs"]) == (6, 33)
    assert (by_tag["v0.9.0"]["delivered_scope"]["us"], by_tag["v0.9.0"]["delivered_scope"]["acs"]) == (3, 13)


def test_real_repo_features_delivered_total_is_ten():
    result = build_release_map(str(_REPO_ROOT), "2026-08-24")
    assert result["figures"]["features_delivered"] == 10


def test_one_release_with_all_delivering_scope_unreadable_nulls_the_band_total_not_zero(tmp_path: Path):
    """AC-3.6: a per-release `us: None` (all delivering members unreadable)
    must never be silently folded as 0 into the global band total."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _commit(repo, ".spark/good/spec.md", "feat: good spec", _spec(2, 3))
    _git(repo, "tag", "v1.0.0")
    _commit(repo, ".spark/bad/spec.md", "feat: bad spec", "# no story heading at all\n")
    _git(repo, "tag", "v2.0.0")
    result = build_release_map(str(repo), "2026-08-10")
    v2 = next(r for r in result["releases"] if r["tag"] == "v2.0.0")
    assert v2["delivered_scope"]["us"] is None
    figures = result["figures"]
    assert figures["delivered_us"] is None
    assert figures["delivered_acs"] is None
    assert figures["scope_unreadable"] == ["bad"]
