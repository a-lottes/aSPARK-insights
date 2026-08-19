"""RB-T2: validated `.spark/` feature-dir enumeration (NFR-2)."""

from __future__ import annotations

from pathlib import Path

from aspark_insights.gitboard.releasemap import _list_feature_dirs


def test_lists_ordinary_feature_directories(tmp_path: Path):
    (tmp_path / ".spark" / "foundation").mkdir(parents=True)
    (tmp_path / ".spark" / "release-board").mkdir(parents=True)
    names = _list_feature_dirs(str(tmp_path))
    assert names == ["foundation", "release-board"]  # sorted, deterministic


def test_no_spark_directory_at_all_is_empty(tmp_path: Path):
    assert _list_feature_dirs(str(tmp_path)) == []


def test_files_directly_under_spark_are_excluded(tmp_path: Path):
    (tmp_path / ".spark").mkdir()
    (tmp_path / ".spark" / "BACKLOG.md").write_text("...", encoding="utf-8")
    (tmp_path / ".spark" / "constitution.md").write_text("...", encoding="utf-8")
    (tmp_path / ".spark" / "real-feature").mkdir()
    assert _list_feature_dirs(str(tmp_path)) == ["real-feature"]


def test_traversal_shaped_name_is_excluded(tmp_path: Path):
    # A literal ".." entry can't be created via mkdir (the filesystem itself
    # rejects it) — a name merely *containing* ".." is the realistic hostile,
    # creatable case the guard must catch.
    spark = tmp_path / ".spark"
    spark.mkdir()
    (spark / "..evil").mkdir()
    names = _list_feature_dirs(str(tmp_path))
    assert "..evil" not in names


def test_leading_dash_name_is_excluded(tmp_path: Path):
    spark = tmp_path / ".spark"
    spark.mkdir()
    (spark / "-rf").mkdir()
    (spark / "real-feature").mkdir()
    names = _list_feature_dirs(str(tmp_path))
    assert "-rf" not in names
    assert "real-feature" in names


def test_symlink_escaping_the_spark_root_is_excluded(tmp_path: Path):
    spark = tmp_path / ".spark"
    spark.mkdir()
    outside = tmp_path / "outside-secret"
    outside.mkdir()
    (outside / "sensitive.md").write_text("do not read", encoding="utf-8")
    (spark / "escape-link").symlink_to(outside, target_is_directory=True)
    (spark / "real-feature").mkdir()
    names = _list_feature_dirs(str(tmp_path))
    assert "escape-link" not in names
    assert "real-feature" in names


def test_symlink_whose_resolved_path_stays_under_spark_root_is_permitted(tmp_path: Path):
    """The exclusion rule is "resolved path escapes `.spark/`" (NFR-2), not
    "any symlink" — a symlink to another entry that itself resolves to
    somewhere under `.spark/` is not an escape and is a valid name."""
    spark = tmp_path / ".spark"
    spark.mkdir()
    real = spark / "real-feature"
    real.mkdir()
    (spark / "alias-link").symlink_to(real, target_is_directory=True)
    names = _list_feature_dirs(str(tmp_path))
    assert names == ["alias-link", "real-feature"]


def test_a_plain_file_named_like_a_feature_is_excluded(tmp_path: Path):
    spark = tmp_path / ".spark"
    spark.mkdir()
    (spark / "not-a-dir.md").write_text("...", encoding="utf-8")
    (spark / "real-feature").mkdir()
    assert _list_feature_dirs(str(tmp_path)) == ["real-feature"]
