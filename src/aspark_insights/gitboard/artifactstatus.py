"""artifactstatus — a strict, honestly-degrading reader of one
`.spark/<feature>/*.md` artifact's header-table `Status`/`Date` fields
(US-2).

Deliberately not tolerant across formats (AC-2.3): only the first maximal
run of consecutive `|`-leading lines is read as the header table (AC-2.4 —
no other section of the free-form Markdown body is parsed, at all), and
only a row whose first cell is exactly `**Status**` (resp. `**Date**`) is
matched. Anything that doesn't match this fixed shape degrades to an
honest `null` + a reason naming the specific cause — never a guess, never
a best-effort format-agnostic parse. This project's own header tables have
held steady across 7 real cycles; the body sections beneath them have not
(spec §3 A3) — that drift is exactly what AC-2.4's narrow scope avoids
ever having to parse.
"""

from __future__ import annotations

from pathlib import Path

# NFR-5: bounded even when no pipe-table is ever found — real header tables
# in this project sit within the first ~10 lines, so this is a generous cap,
# not a tight fit.
_MAX_LINES_SCANNED = 200


def read_artifact_status(path: Path) -> dict:
    """`{"status": str|None, "date": str|None, "reason": str|None}` —
    `reason` is set exactly when `status` is `None`. `date` is reported
    independently: a missing Date row never blocks a found Status."""
    if not path.is_file():
        return {"status": None, "date": None, "reason": "file not found"}

    try:
        table_lines = _read_header_table(path)
    except (OSError, UnicodeDecodeError) as exc:
        return {"status": None, "date": None, "reason": f"could not read file: {exc}"}

    if not table_lines:
        return {"status": None, "date": None, "reason": "no header table found"}

    status = _cell_value(table_lines, "**Status**")
    date = _cell_value(table_lines, "**Date**")
    reason = None if status is not None else "no Status row found in header table"
    return {"status": status, "date": date, "reason": reason}


def _read_header_table(path: Path) -> list[str]:
    """The first maximal run of consecutive `|`-leading lines, bounded to
    `_MAX_LINES_SCANNED` lines read regardless of whether a table is ever
    found (NFR-5)."""
    table_lines: list[str] = []
    in_table = False
    with path.open("r", encoding="utf-8") as f:
        for _ in range(_MAX_LINES_SCANNED):
            line = f.readline()
            if not line:
                break
            stripped = line.rstrip("\n")
            if stripped.startswith("|"):
                in_table = True
                table_lines.append(stripped)
            elif in_table:
                break  # the first non-| line after the table block ends it
    return table_lines


def _cell_value(table_lines: list[str], label: str) -> str | None:
    """The trimmed second cell of the first row whose first cell is exactly
    `label` — e.g. `| **Status** | \\`approved\\` |` yields `` `approved` ``
    verbatim (AC-2.1), including any trailing prose a cell carries beyond a
    clean token (a real, observed shape in this project's own artifacts).
    A value containing a literal `|` splits into more than the expected
    four raw cells (leading empty, label, value, trailing empty) — review
    F2: rejoined from the *unstripped* cells rather than truncated at the
    first embedded pipe, so whitespace immediately around it survives
    exactly as written, not just the value itself."""
    for line in table_lines:
        raw_cells = line.split("|")
        if len(raw_cells) >= 4 and raw_cells[1].strip() == label:
            return "|".join(raw_cells[2:-1]).strip()
    return None
