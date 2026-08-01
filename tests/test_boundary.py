"""NFR-2/AC-2.4: only ports/graph.py may reach into aspark_graph or its graph.json."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src" / "aspark_insights"
ALLOWED = {SRC_DIR / "ports" / "graph.py"}

_PATTERNS = [
    re.compile(r"\baspark_graph\b"),
    re.compile(r"\.aspark-graph[/\\]graph\.json"),
    # The CLI's own package/executable name, hyphen form — catches a stray
    # subprocess.run(["aspark-graph", ...]) bypassing CLIGraphPort.
    re.compile(r"aspark-graph"),
]


def _find_offenders(src_dir: Path, allowed: set[Path]) -> list[str]:
    offenders = []
    for path in sorted(src_dir.rglob("*.py")):
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if any(p.search(text) for p in _PATTERNS):
            offenders.append(str(path.relative_to(src_dir.parent.parent)))
    return offenders


def test_no_code_outside_graph_port_touches_aspark_graph_directly():
    offenders = _find_offenders(SRC_DIR, ALLOWED)
    assert not offenders, (
        f"only ports/graph.py may reference aspark_graph or .aspark-graph/graph.json: {offenders}"
    )


def test_guard_catches_a_hyphen_form_bypass(tmp_path: Path):
    """Proves the pattern would flag a violation, not just that none exists today."""
    src_dir = tmp_path / "src" / "pkg"
    src_dir.mkdir(parents=True)
    (src_dir / "sneaky.py").write_text(
        'import subprocess\nsubprocess.run(["aspark-graph", "query", "staleness"])\n',
        encoding="utf-8",
    )
    offenders = _find_offenders(src_dir, allowed=set())
    assert offenders == [str(Path("src") / "pkg" / "sneaky.py")]


def test_new_metrics_files_are_within_the_guards_scan_scope():
    """metrics/collectors.py, scope.py and traceability.py (traceability-metrics,
    I2) must be files the guard actually scans, not silently excluded — proves
    T7's boundary check covers this feature's new files, not just I1's."""
    scanned = {p for p in SRC_DIR.rglob("*.py")}
    for name in ("collectors.py", "scope.py", "traceability.py"):
        path = SRC_DIR / "metrics" / name
        assert path in scanned
        assert path not in ALLOWED


def test_a_planted_violation_in_a_new_metrics_file_is_caught(tmp_path: Path):
    """Copies collectors.py's real content into a same-named tmp file and
    injects a direct aspark_graph import — proves the guard would fail the
    build if this specific file ever regressed, not just a synthetic stand-in."""
    src_dir = tmp_path / "src" / "aspark_insights" / "metrics"
    src_dir.mkdir(parents=True)
    real = (SRC_DIR / "metrics" / "collectors.py").read_text(encoding="utf-8")
    (src_dir / "collectors.py").write_text(
        real + "\nimport aspark_graph  # a planted regression\n", encoding="utf-8"
    )
    offenders = _find_offenders(src_dir.parent, allowed=set())
    assert offenders == [str(Path("src") / "aspark_insights" / "metrics" / "collectors.py")]
