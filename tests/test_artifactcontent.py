"""RBD-T2/T3/T4: bounded, honest artifact document reads."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from aspark_insights.gitboard.artifactcontent import (
    collect_release_documents,
    read_artifact_document,
)


# --- T3: honest states (AC-2.2/2.3) ------------------------------------------


def test_missing_file_reports_named_reason(tmp_path: Path):
    result = read_artifact_document(tmp_path / "nope.md")
    assert result["reason"] == "file not found"
    assert result["text"] == ""
    assert not result["empty"]


def test_unreadable_file_reports_named_reason(tmp_path: Path):
    path = tmp_path / "locked.md"
    path.write_text("secret", encoding="utf-8")
    path.chmod(0o000)
    try:
        result = read_artifact_document(path)
        if os.geteuid() == 0:  # root ignores chmod; skip assertion in that environment
            pytest.skip("running as root, chmod 000 has no effect")
        assert result["reason"] is not None
        assert "could not read" in result["reason"] or "could not stat" in result["reason"]
    finally:
        path.chmod(0o644)


def test_undecodable_file_reports_named_reason(tmp_path: Path):
    path = tmp_path / "binary.md"
    path.write_bytes(b"\xff\xfe\x00\x01not valid utf-8 \xff")
    result = read_artifact_document(path)
    assert result["reason"] is not None
    assert "decode" in result["reason"]


def test_empty_file_is_distinct_from_missing_or_unreadable(tmp_path: Path):
    path = tmp_path / "empty.md"
    path.write_text("", encoding="utf-8")
    result = read_artifact_document(path)
    assert result["empty"] is True
    assert result["reason"] is None
    assert result["text"] == ""


def test_normal_file_reads_cleanly(tmp_path: Path):
    path = tmp_path / "spec.md"
    path.write_text("# Spec\n\nSome content.\n", encoding="utf-8")
    result = read_artifact_document(path)
    assert result["reason"] is None
    assert result["empty"] is False
    assert result["truncated"] is False
    assert result["text"] == "# Spec\n\nSome content.\n"
    assert result["total_lines"] == result["shown_lines"]


# --- T4: bounds and disclosure (AC-2.5) --------------------------------------


def test_line_bound_truncates_and_discloses_true_total(tmp_path: Path):
    path = tmp_path / "big.md"
    path.write_text("\n".join(f"line {i}" for i in range(3000)), encoding="utf-8")
    result = read_artifact_document(path, max_lines=1200, max_bytes=1_000_000)
    assert result["truncated"] is True
    assert result["shown_lines"] == 1200
    assert result["total_lines"] == 3000
    assert result["text"].count("\n") == 1199  # 1200 lines joined by 1199 newlines


def test_byte_bound_trips_on_a_single_giant_line(tmp_path: Path):
    """T4's own DoD case: a single-line 1MB fixture has only 1 real line,
    so the line bound never fires, but the byte bound must."""
    path = tmp_path / "giant.md"
    path.write_text("x" * 1_000_000, encoding="utf-8")
    result = read_artifact_document(path, max_lines=1200, max_bytes=200_000)
    assert result["truncated"] is True
    assert result["total_bytes"] == 1_000_000
    assert len(result["text"].encode("utf-8")) <= 200_000
    assert result["total_lines"] == 1


def test_within_both_bounds_is_not_truncated(tmp_path: Path):
    path = tmp_path / "small.md"
    path.write_text("a small document\n", encoding="utf-8")
    result = read_artifact_document(path, max_lines=1200, max_bytes=200_000)
    assert result["truncated"] is False


def test_byte_truncation_does_not_crash_on_a_multibyte_boundary(tmp_path: Path):
    """A UTF-8 multi-byte character straddling the exact byte cut must
    degrade cleanly (dropped), never raise."""
    path = tmp_path / "unicode.md"
    # Build content whose byte-200000 boundary likely lands inside a
    # multi-byte emoji sequence.
    text = "🎉" * 100_000  # 4 bytes each = 400,000 bytes
    path.write_text(text, encoding="utf-8")
    result = read_artifact_document(path, max_lines=1200, max_bytes=200_000)
    assert result["truncated"] is True
    assert result["reason"] is None  # never a hard failure from a truncation boundary


# --- collect_release_documents (T2) ------------------------------------------


def _git(repo: Path, *args: str):
    import subprocess

    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )


def test_collect_reads_every_distinct_feature_once(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".spark" / "feature-a").mkdir(parents=True)
    (repo / ".spark" / "feature-a" / "spec.md").write_text("spec content", encoding="utf-8")
    data = {
        "releases": [
            {"tag": "v1.0.0", "members": [{"name": "feature-a"}], "unattributed": []},
            {"tag": "v2.0.0", "members": [{"name": "feature-a"}], "unattributed": []},
        ]
    }
    docs = collect_release_documents(str(repo), data)
    assert list(docs.keys()) == ["feature-a"]  # present once, not per-release
    assert docs["feature-a"]["spec"]["text"] == "spec content"
    assert docs["feature-a"]["plan"]["reason"] == "file not found"


def test_collect_skips_hostile_feature_names(tmp_path: Path):
    """T6: a feature name is re-validated at this module's own boundary,
    independent of releasemap's own upstream check."""
    repo = tmp_path / "repo"
    repo.mkdir()
    data = {
        "releases": [
            {"tag": "v1.0.0", "members": [
                {"name": "../../../etc/passwd"},
                {"name": "-rf"},
                {"name": "legit-feature"},
            ], "unattributed": []},
        ]
    }
    (repo / ".spark" / "legit-feature").mkdir(parents=True)
    (repo / ".spark" / "legit-feature" / "spec.md").write_text("ok", encoding="utf-8")
    docs = collect_release_documents(str(repo), data)
    assert list(docs.keys()) == ["legit-feature"]


def test_symlink_escaping_spark_directory_is_rejected(tmp_path: Path):
    """Review F1 (Blocker): a `.spark/<feature>/spec.md` symlinked outside
    the repo must never be read and embedded — reproduced end-to-end
    against a real symlink to a real file outside `.spark/`."""
    repo = tmp_path / "repo"
    (repo / ".spark" / "pwned").mkdir(parents=True)
    secret = tmp_path / "secret_outside.txt"
    secret.write_text("TOP SECRET DATA", encoding="utf-8")
    (repo / ".spark" / "pwned" / "spec.md").symlink_to(secret)

    data = {"releases": [{"tag": "v1.0.0", "members": [{"name": "pwned"}], "unattributed": []}]}
    docs = collect_release_documents(str(repo), data)
    assert docs["pwned"]["spec"]["reason"] == "document path escapes .spark/"
    assert "TOP SECRET DATA" not in docs["pwned"]["spec"]["text"]


def test_symlink_within_spark_root_is_still_permitted(tmp_path: Path):
    """A symlink that stays *inside* `.spark/` (e.g. an internal alias) is
    not an escape and must still read normally — only escaping symlinks
    are rejected."""
    repo = tmp_path / "repo"
    (repo / ".spark" / "canonical-feature").mkdir(parents=True)
    (repo / ".spark" / "canonical-feature" / "spec.md").write_text("real content", encoding="utf-8")
    (repo / ".spark" / "aliased-feature").mkdir(parents=True)
    (repo / ".spark" / "aliased-feature" / "spec.md").symlink_to(
        repo / ".spark" / "canonical-feature" / "spec.md"
    )

    data = {"releases": [{"tag": "v1.0.0", "members": [{"name": "aliased-feature"}], "unattributed": []}]}
    docs = collect_release_documents(str(repo), data)
    assert docs["aliased-feature"]["spec"]["text"] == "real content"
    assert docs["aliased-feature"]["spec"]["reason"] is None


def test_collector_never_raises_on_malformed_data_shapes(tmp_path: Path):
    """Review F8: `collect_release_documents`'s own docstring claims "never
    raises" — this proves it against the exact shapes that broke it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    for malformed in (
        {"releases": None},
        {"releases": [None]},
        {"releases": [{"members": [{}]}]},
        {"releases": [{"members": None}]},
        {},
    ):
        collect_release_documents(str(repo), malformed)  # must not raise


def test_collector_never_raises_on_truthy_non_list_and_unstattable_names(tmp_path: Path):
    """Re-review of F8: the first fix used `data.get(...) or []`, which only
    catches a *falsy* wrong type — a truthy non-list still raised
    `TypeError`, and a feature name that no `stat()` can accept (embedded
    NUL, or longer than `NAME_MAX`) escaped `read_artifact_document`'s own
    "Never raises" contract as a `ValueError`/`ENAMETOOLONG OSError`. Not
    reachable from `build_release_map()` (no real directory can be named
    either way), but the constitution's "never a raw traceback" is the
    contract these two functions' docstrings both assert unconditionally."""
    repo = tmp_path / "repo"
    repo.mkdir()
    for malformed in (
        {"releases": 42},
        {"releases": "notalist"},
        {"releases": [{"members": "abc"}]},
        {"releases": [{"members": [{"name": "a\x00b"}]}]},
        {"releases": [{"members": [{"name": "a" * 5000}]}]},
    ):
        collect_release_documents(str(repo), malformed)  # must not raise

    # ...and each unstattable name degrades to an honest reason, not silence
    docs = collect_release_documents(
        str(repo), {"releases": [{"members": [{"name": "b" * 5000}]}]}
    )
    assert docs["b" * 5000]["spec"]["reason"] is not None
    assert docs["b" * 5000]["spec"]["text"] == ""


def test_collect_deterministic_order(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    for name in ("zeta", "alpha", "mid"):
        (repo / ".spark" / name).mkdir(parents=True)
    data = {
        "releases": [
            {"tag": "v1.0.0", "members": [{"name": "zeta"}, {"name": "alpha"}, {"name": "mid"}], "unattributed": []},
        ]
    }
    docs = collect_release_documents(str(repo), data)
    assert list(docs.keys()) == ["alpha", "mid", "zeta"]  # sorted, not insertion order
