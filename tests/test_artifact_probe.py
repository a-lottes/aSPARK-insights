"""artifact_probe.py (US-3): bounded, safe, deterministic .spark/ presence check.

Each test below is one of the plan's T1 hostile/edge cases (AC-3.1..3.8).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from aspark_insights.artifact_probe import ArtifactProbeResult, probe_artifacts

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="symlink/permission tests assume a POSIX filesystem"
)


# --- AC-3.1: absent .spark/ is a valid answer, not an error -----------------


def test_absent_spark_dir_reports_absent(tmp_path: Path):
    result = probe_artifacts(tmp_path)
    assert result.outcome == "absent"
    assert result.matched_file_count == 0
    assert result.matched_filenames == ()
    assert result.feature_dir_count == 0
    assert result.detail is None


# --- AC-3.2: .spark as a file, broken symlink, or symlink — never followed --


def test_spark_as_a_regular_file_is_inconclusive_never_a_crash(tmp_path: Path):
    (tmp_path / ".spark").write_text("not a directory", encoding="utf-8")
    result = probe_artifacts(tmp_path)
    assert result.outcome == "inconclusive"
    assert result.detail is not None


def test_spark_as_a_broken_symlink_is_inconclusive_never_followed(tmp_path: Path):
    (tmp_path / ".spark").symlink_to(tmp_path / "nonexistent-target")
    result = probe_artifacts(tmp_path)
    assert result.outcome == "inconclusive"


def test_spark_as_a_symlink_to_a_real_directory_is_inconclusive_never_followed(tmp_path: Path):
    real_dir = tmp_path / "real-spark"
    (real_dir / "feature-a").mkdir(parents=True)
    (real_dir / "feature-a" / "qa.md").write_text("x", encoding="utf-8")
    (tmp_path / ".spark").symlink_to(real_dir)

    result = probe_artifacts(tmp_path)
    # Never followed, even though the target is a real, populated directory —
    # so the (real) qa.md inside it must never be counted.
    assert result.outcome == "inconclusive"
    assert result.matched_file_count == 0


def test_feature_dir_symlink_is_never_descended_into(tmp_path: Path):
    real_dir = tmp_path / "real-feature"
    real_dir.mkdir()
    (real_dir / "qa.md").write_text("x", encoding="utf-8")

    spark = tmp_path / ".spark"
    spark.mkdir()
    (spark / "linked-feature").symlink_to(real_dir)

    result = probe_artifacts(tmp_path)
    assert result.matched_file_count == 0
    assert result.feature_dir_count == 0


def test_artifact_file_symlink_is_never_followed(tmp_path: Path):
    real_file = tmp_path / "real-qa.md"
    real_file.write_text("x", encoding="utf-8")

    feature_dir = tmp_path / ".spark" / "feature-a"
    feature_dir.mkdir(parents=True)
    (feature_dir / "qa.md").symlink_to(real_file)

    result = probe_artifacts(tmp_path)
    assert result.matched_file_count == 0
    assert result.outcome == "absent"
    assert result.feature_dir_count == 1  # the directory itself is real, just its file is a link


# --- AC-3.3: unreadable .spark/ (or a feature dir inside it) never raises ---


def test_unreadable_spark_dir_is_inconclusive_with_sanitized_cause(tmp_path: Path):
    if os.geteuid() == 0:
        pytest.skip("root bypasses directory permission checks")
    spark = tmp_path / ".spark"
    spark.mkdir()
    spark.chmod(0o000)
    try:
        result = probe_artifacts(tmp_path)
        assert result.outcome == "inconclusive"
        assert result.detail is not None
        assert "permission" in result.detail.lower()
    finally:
        spark.chmod(0o755)


# --- AC-3.4: zero bytes of content read; matched regardless of content -----


def test_empty_matched_file_is_still_counted_zero_bytes_read(tmp_path: Path):
    feature_dir = tmp_path / ".spark" / "feature-a"
    feature_dir.mkdir(parents=True)
    (feature_dir / "qa.md").write_text("", encoding="utf-8")

    result = probe_artifacts(tmp_path)
    assert result.outcome == "present"
    assert result.matched_file_count == 1


def test_huge_matched_file_is_counted_without_being_read(tmp_path: Path):
    feature_dir = tmp_path / ".spark" / "feature-a"
    feature_dir.mkdir(parents=True)
    huge = feature_dir / "review.md"
    with huge.open("wb") as f:
        f.seek(10 * 1024 * 1024 - 1)
        f.write(b"\0")

    result = probe_artifacts(tmp_path)
    assert result.outcome == "present"
    assert "review.md" in result.matched_filenames


def test_invalid_utf8_matched_file_is_counted_without_a_decode_error(tmp_path: Path):
    feature_dir = tmp_path / ".spark" / "feature-a"
    feature_dir.mkdir(parents=True)
    (feature_dir / "qa.md").write_bytes(b"\xff\xfe\x00not-real-utf8")

    result = probe_artifacts(tmp_path)  # must not raise UnicodeDecodeError
    assert result.outcome == "present"


# --- AC-3.5: descends exactly one level; performance budget -----------------


def test_file_two_levels_deep_is_not_counted(tmp_path: Path):
    nested = tmp_path / ".spark" / "feature-a" / "nested" / "qa.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("x", encoding="utf-8")

    result = probe_artifacts(tmp_path)
    assert result.outcome == "absent"
    assert result.matched_file_count == 0


def test_thousand_feature_dirs_completes_within_budget(tmp_path: Path):
    spark = tmp_path / ".spark"
    spark.mkdir()
    for i in range(1000):
        d = spark / f"feature-{i:04d}"
        d.mkdir()
        if i == 500:
            (d / "qa.md").write_text("x", encoding="utf-8")

    start = time.monotonic()
    result = probe_artifacts(tmp_path)
    elapsed = time.monotonic() - start

    assert elapsed < 1.0
    assert result.feature_dir_count == 1000
    assert result.matched_file_count == 1


# --- AC-3.6: no absolute path / home dir / username / foreign filename -----


def test_result_never_contains_absolute_path_home_or_username(tmp_path: Path):
    feature_dir = tmp_path / ".spark" / "feature-a"
    feature_dir.mkdir(parents=True)
    (feature_dir / "qa.md").write_text("x", encoding="utf-8")

    result = probe_artifacts(tmp_path)
    blob = repr(result.to_dict())
    home = os.path.expanduser("~")
    username = os.environ.get("USER") or os.environ.get("USERNAME") or ""
    assert str(tmp_path) not in blob
    assert home not in blob
    if username:
        assert username not in blob


def test_matched_filenames_only_ever_the_built_in_set(tmp_path: Path):
    feature_dir = tmp_path / ".spark" / "feature-a"
    feature_dir.mkdir(parents=True)
    (feature_dir / "qa.md").write_text("x", encoding="utf-8")
    (feature_dir / "spec.md").write_text("x", encoding="utf-8")  # not in the built-in set
    (feature_dir / "plan.md").write_text("x", encoding="utf-8")

    result = probe_artifacts(tmp_path)
    assert set(result.matched_filenames) <= {"qa.md", "review.md"}
    assert result.matched_file_count == 1


# --- AC-3.7: paths composed only from repo_root + built-in set; hostile input


@pytest.mark.parametrize(
    "repo_root",
    ["", "../../../etc", "/etc", "/nonexistent-absolute-path-xyz", "relative/nonexistent"],
)
def test_hostile_repo_root_never_raises(repo_root: str):
    result = probe_artifacts(repo_root)  # must not raise
    assert isinstance(result, ArtifactProbeResult)


# --- AC-3.8: sorted, mtime-free, deterministic traversal --------------------


def test_result_is_deterministic_across_repeated_calls(tmp_path: Path):
    for name in ("zzz-feature", "aaa-feature", "mmm-feature"):
        d = tmp_path / ".spark" / name
        d.mkdir(parents=True)
        (d / "qa.md").write_text("x", encoding="utf-8")

    first = probe_artifacts(tmp_path)
    second = probe_artifacts(tmp_path)
    assert first == second
    assert first.matched_filenames == ("qa.md",)


def test_both_filenames_present_yields_sorted_tuple(tmp_path: Path):
    feature_dir = tmp_path / ".spark" / "feature-a"
    feature_dir.mkdir(parents=True)
    (feature_dir / "review.md").write_text("x", encoding="utf-8")
    (feature_dir / "qa.md").write_text("x", encoding="utf-8")

    result = probe_artifacts(tmp_path)
    assert result.matched_filenames == ("qa.md", "review.md")  # sorted, not insertion order


# --- disk_phrase(): three materially different strings ---------------------


def test_disk_phrase_present_names_count_and_filenames(tmp_path: Path):
    feature_dir = tmp_path / ".spark" / "feature-a"
    feature_dir.mkdir(parents=True)
    (feature_dir / "qa.md").write_text("x", encoding="utf-8")

    result = probe_artifacts(tmp_path)
    phrase = result.disk_phrase()
    assert "1" in phrase
    assert "qa.md" in phrase


def test_disk_phrase_absent_is_a_fixed_distinct_string(tmp_path: Path):
    result = probe_artifacts(tmp_path)
    assert result.disk_phrase() == "no matching artifact files found under .spark/"


def test_disk_phrase_inconclusive_names_the_cause_distinctly(tmp_path: Path):
    (tmp_path / ".spark").write_text("x", encoding="utf-8")
    result = probe_artifacts(tmp_path)
    phrase = result.disk_phrase()
    assert phrase.startswith("on-disk check inconclusive (")
    assert phrase != "no matching artifact files found under .spark/"


def test_the_three_disk_phrases_are_all_materially_different(tmp_path: Path):
    absent = probe_artifacts(tmp_path)

    present_root = tmp_path / "present-case"
    fd = present_root / ".spark" / "feature-a"
    fd.mkdir(parents=True)
    (fd / "qa.md").write_text("x", encoding="utf-8")
    present = probe_artifacts(present_root)

    inconclusive_root = tmp_path / "inconclusive-case"
    inconclusive_root.mkdir()
    (inconclusive_root / ".spark").write_text("x", encoding="utf-8")
    inconclusive = probe_artifacts(inconclusive_root)

    phrases = {absent.disk_phrase(), present.disk_phrase(), inconclusive.disk_phrase()}
    assert len(phrases) == 3
