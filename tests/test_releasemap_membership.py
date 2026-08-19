"""RB-T3: membership + unattributed for real releases (A6/A7/A8/A9)
(AC-1.2, AC-1.3, AC-1.6, NFR-2)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aspark_insights.gitboard.releasemap import build_release_map


def _member_names(release: dict) -> list[str]:
    return [m["name"] for m in release["members"]]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


def _commit(repo: Path, path: str, subject: str) -> None:
    full = repo / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(subject, encoding="utf-8")
    _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", subject)


@pytest.fixture
def multi_member_repo(tmp_path: Path) -> Path:
    """Reproduces this repo's own real v0.3.0 shape (A8: three members) and
    the A9 pattern (a feature's trailing docs commit landing in the *next*
    release's range), plus the AC-1.3 adversarial subject/unattributed cases."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")

    # feature-x ships fully before v1.0.0
    _commit(repo, ".spark/feature-x/spec.md", "feat: feature-x spec")
    _commit(repo, ".spark/feature-x/plan.md", "feat: feature-x plan")
    _git(repo, "tag", "v1.0.0")

    # A9: feature-x's own trailing "record release report" commit lands
    # AFTER v1.0.0, inside the *next* range — not the range it shipped under.
    _commit(repo, ".spark/feature-x/release.md", "docs: record feature-x release report")
    _commit(repo, ".spark/feature-y/spec.md", "feat: feature-y spec")
    _commit(repo, ".spark/feature-z/spec.md", "feat: feature-z spec")
    # unattributed: touches no .spark/<feature>/ path at all
    _commit(repo, ".spark/BACKLOG.md", "docs: update backlog")
    # AC-1.3 adversarial: subject names feature-x, touches CLAUDE.md only
    _commit(repo, "CLAUDE.md", "docs: fold feature-x's pattern into CLAUDE.md")
    _git(repo, "tag", "v2.0.0")

    return repo


def test_earliest_release_has_exactly_its_one_real_member(multi_member_repo: Path):
    result = build_release_map(str(multi_member_repo), "2026-08-19")
    v1 = next(r for r in result["releases"] if r["tag"] == "v1.0.0")
    assert _member_names(v1) == ["feature-x"]
    assert v1["unattributed"] == []


def test_second_release_has_three_members_a8_shape(multi_member_repo: Path):
    result = build_release_map(str(multi_member_repo), "2026-08-19")
    v2 = next(r for r in result["releases"] if r["tag"] == "v2.0.0")
    assert _member_names(v2) == ["feature-x", "feature-y", "feature-z"]


def test_a9_trailing_docs_commit_lands_in_next_release_not_its_own(multi_member_repo: Path):
    """feature-x's trailing 'docs: record release report' commit is why
    feature-x reappears in v2.0.0's members even though its own work shipped
    under v1.0.0 — asserted as correct (A9), not filtered."""
    result = build_release_map(str(multi_member_repo), "2026-08-19")
    v2 = next(r for r in result["releases"] if r["tag"] == "v2.0.0")
    assert "feature-x" in _member_names(v2)


def test_backlog_only_commit_is_unattributed_never_dropped(multi_member_repo: Path):
    result = build_release_map(str(multi_member_repo), "2026-08-19")
    v2 = next(r for r in result["releases"] if r["tag"] == "v2.0.0")
    subjects = [c["subject"] for c in v2["unattributed"]]
    assert "docs: update backlog" in subjects


def test_ac_1_3_subject_naming_a_dir_it_never_touched_is_unattributed_not_matched(multi_member_repo: Path):
    """A commit whose subject mentions 'feature-x' but touches only
    CLAUDE.md must never be attributed to feature-x by text matching."""
    result = build_release_map(str(multi_member_repo), "2026-08-19")
    v2 = next(r for r in result["releases"] if r["tag"] == "v2.0.0")
    unattributed_subjects = [c["subject"] for c in v2["unattributed"]]
    assert "docs: fold feature-x's pattern into CLAUDE.md" in unattributed_subjects
    # and it must not have inflated feature-x's membership beyond the one
    # real touching commit already covered by the trailing-docs test above


def test_unattributed_entries_carry_hash_and_subject_only(multi_member_repo: Path):
    result = build_release_map(str(multi_member_repo), "2026-08-19")
    v2 = next(r for r in result["releases"] if r["tag"] == "v2.0.0")
    for c in v2["unattributed"]:
        assert set(c.keys()) == {"hash", "subject"}


# --- AC-1.6: no author/committer identity anywhere in the output -----------


def test_no_identity_field_anywhere_in_release_map(multi_member_repo: Path):
    import json

    result = build_release_map(str(multi_member_repo), "2026-08-19")
    blob = json.dumps(result)
    for token in ("author", "committer", "email", "t@example.com", "Test"):
        assert token not in blob, f"identity token {token!r} leaked into release map"


# --- QA B1 (Major): a renamed/deleted feature directory, or one that only
#     ever existed on a non-current branch, must still be found — the
#     candidate feature-name set can't be scoped to the current checkout ---


def test_a_deleted_feature_directory_still_appears_in_the_release_it_shipped_in(tmp_path: Path):
    """B1's exact repro: `oldfeature` ships and is tagged, then the
    directory is deleted and replaced by `newfeature` before the next tag.
    `oldfeature`'s own commit unambiguously touches `.spark/oldfeature/`
    (confirmed independently via plain `git log v1.0.0 -- .spark/oldfeature/`
    outside this test too) — it must appear as v1.0.0's member, not be
    silently dumped into `unattributed` just because the directory no
    longer exists on disk."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / ".spark" / "oldfeature").mkdir(parents=True)
    (repo / ".spark" / "oldfeature" / "spec.md").write_text("spec", encoding="utf-8")
    _git(repo, "add", ".spark/oldfeature/spec.md")
    _git(repo, "commit", "-q", "-m", "feat: oldfeature spec")
    _git(repo, "tag", "v1.0.0")
    _git(repo, "rm", "-r", "-q", ".spark/oldfeature")
    (repo / ".spark" / "newfeature").mkdir(parents=True)
    (repo / ".spark" / "newfeature" / "spec.md").write_text("spec", encoding="utf-8")
    _git(repo, "add", ".spark/newfeature/spec.md")
    _git(repo, "commit", "-q", "-m", "feat: newfeature spec, retire oldfeature")
    _git(repo, "tag", "v2.0.0")

    result = build_release_map(str(repo), "2026-08-19")
    v1 = next(r for r in result["releases"] if r["tag"] == "v1.0.0")
    assert _member_names(v1) == ["oldfeature"]
    assert v1["unattributed"] == []


def test_a_feature_only_reachable_via_a_tag_on_another_branch_still_appears(tmp_path: Path):
    """B1's second repro: a tag sits on a branch that never got merged into
    the branch currently checked out. `feat_b`'s directory has never
    existed in `main`'s own checkout history, only on `side` — must still
    be found via `--all`, not just commits reachable from `main`/`HEAD`."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "commit", "--allow-empty", "-q", "-m", "feat: base")
    _git(repo, "tag", "v1.0.0")
    default_branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    _git(repo, "checkout", "-q", "-b", "side")
    (repo / ".spark" / "feat_b").mkdir(parents=True)
    (repo / ".spark" / "feat_b" / "spec.md").write_text("spec", encoding="utf-8")
    _git(repo, "add", ".spark/feat_b/spec.md")
    _git(repo, "commit", "-q", "-m", "feat: feat_b spec")
    _git(repo, "tag", "v2.0.0")
    _git(repo, "checkout", "-q", default_branch)

    result = build_release_map(str(repo), "2026-08-19")
    v2 = next(r for r in result["releases"] if r["tag"] == "v2.0.0")
    assert "feat_b" in _member_names(v2)
