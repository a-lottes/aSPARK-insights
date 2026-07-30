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
