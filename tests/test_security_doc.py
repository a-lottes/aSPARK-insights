"""T5: SECURITY.md says what it means and means what it says (AC-2.1..2.4).

Doc-introspection testing (same technique as aspark-graph's own
tests/test_security_doc.py): section extraction + substring/count assertions,
so the document cannot rot silently.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECURITY_PATH = ROOT / "SECURITY.md"
README_PATH = ROOT / "README.md"

_DENYLIST = ("sandbox", "isolat", "contain", "prevent", "protect")


def _security_text() -> str:
    assert SECURITY_PATH.exists(), "SECURITY.md does not exist at the repo root"
    return SECURITY_PATH.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Text from `## <heading>` to the next `## ` heading (or EOF)."""
    m = re.search(rf"^## {re.escape(heading)}\b(.*?)(?=\n## |\Z)", text, re.DOTALL | re.MULTILINE)
    assert m, f"SECURITY.md missing '## {heading}' section"
    return m.group(1)


# --- AC-2.1: the file exists and states the trust boundary ------------------


def test_ac_2_1_security_md_exists():
    assert SECURITY_PATH.exists()


def test_ac_2_1_trust_boundary_stated():
    section = _section(_security_text(), "Trust boundary")
    lowered = section.lower()
    assert "stdio" in lowered
    assert "no authentication" in lowered or "no auth" in lowered
    assert "no http" in lowered
    assert "no network" in lowered or "network access" in lowered
    assert "remote transport" in lowered
    assert "one" in lowered and "repo" in lowered  # exactly one fixed repo/output target
    assert "mid-conversation" in lowered


# --- AC-2.2: at least four named non-guarantees ------------------------------

_NON_GUARANTEE_MARKERS = [
    "not a runtime permission",   # 1: read-only is enforced by omission
    "no repo-confinement",        # 2: no marker/confinement check
    "no privilege",               # 3: removes no privilege the operator lacked
    "adversarial",                # 4: identifiers originate from analyzed repo content
]


def test_ac_2_2_non_guarantees_present():
    section = _section(_security_text(), "Non-guarantees")
    items = re.findall(r"^\d+\.\s", section, re.MULTILINE)
    assert len(items) >= 4, f"expected at least four numbered non-guarantees, found {len(items)}"
    lowered = section.lower()
    for marker in _NON_GUARANTEE_MARKERS:
        assert marker in lowered, f"non-guarantee marker {marker!r} not found in the section"


# --- AC-2.3: reporting channel + response window -----------------------------


def test_ac_2_3_reporting_channel_and_response_window():
    section = _section(_security_text(), "Reporting a vulnerability")
    lowered = section.lower()
    assert "private security advisor" in lowered or "private security" in lowered
    assert "never a public issue" in lowered or "not a public issue" in lowered
    assert "5 working days" in section
    assert "in scope" in lowered


# --- AC-2.4: the keyword denylist, outside Non-guarantees only --------------


def test_ac_2_4_denylist_words_appear_only_in_non_guarantees():
    text = _security_text()
    non_guarantees = _section(text, "Non-guarantees")
    rest = text.replace(non_guarantees, "")
    for word in _DENYLIST:
        offenders = [line for line in rest.splitlines() if re.search(word, line, re.IGNORECASE)]
        assert offenders == [], f"{word!r} appears outside Non-guarantees: {offenders}"


# --- README links SECURITY.md and documents the MCP surface -----------------


def test_readme_links_security_doc():
    assert "SECURITY.md" in README_PATH.read_text(encoding="utf-8")


def test_readme_mcp_section_documents_the_query_tool():
    readme = README_PATH.read_text(encoding="utf-8")
    m = re.search(r"^### MCP\b(.*?)(?=\n## |\Z)", readme, re.DOTALL | re.MULTILINE)
    assert m, "README.md missing '### MCP' section"
    section = m.group(1)
    lowered = section.lower()
    assert "read-only" in lowered
    assert "query" in section
    assert "no arguments" in lowered or "zero" in lowered
