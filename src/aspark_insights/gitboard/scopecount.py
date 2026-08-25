"""scopecount — count a feature's own delivered scope (US/AC) directly from
its `spec.md`, never the sibling graph (release-metrics US-2/A1).

Kept separate from `artifactstatus.py` deliberately, mirroring
`artifactcontent.py`'s own precedent: that module's docstring makes "no
other section of the free-form Markdown body is parsed, at all" a
load-bearing promise for the header-table-only status extraction two
shipped features already depend on (`build_release_map`'s own status map,
`release-board-html`'s AC-2.4). Counting `### US-N` headings and
`- [ ] AC-` lines is a second, independent scan over the same file for a
different purpose — folding it into `artifactstatus.py` would silently
widen a contract nothing asked it to carry (CLAUDE.md's "don't
over-generalize a fix onto callers that never asked for it").

`gitboard` stays fully graph-free (A1): no `GraphPort` import, consistent
with `releasemap.py`'s own docstring and this project's three-feature-old,
structurally tested principle.
"""

from __future__ import annotations

import re
from pathlib import Path

_US_HEADING = re.compile(r"^### US-\d+")
_AC_LINE = re.compile(r"^\s*-\s*\[[ xX]\]\s*AC-")

# Defense against a pathological file — a real spec.md is a few hundred
# lines (largest observed in this project: 597); well above that without
# reading the whole file just to count headings/checkboxes.
_MAX_LINES_SCANNED = 5000


def read_scope_counts(path: Path) -> dict:
    """Never raises (AC-3.6) — degrades to an honest `reason`, the same
    contract `artifactstatus.py`/`artifactcontent.py` already hold. Counts
    `### US-N` headings (US) and `- [ ] AC-`/`- [x] AC-` lines (ACs) —
    never a guess, never an estimate.

    Returns `{"us": int|None, "acs": int|None, "reason": str|None}`.
    `reason` is set only when scope genuinely cannot be counted (file
    missing, unreadable, or no `### US-N` heading found at all — a spec
    with zero stories is not a real shape this project's own template
    produces); a spec with stories but zero checked/unchecked AC lines
    still reports a real `acs: 0`, never a null.
    """
    # Review F5: `Path.is_file()` swallows most `OSError`s but not all of
    # them (an over-long path raises `ENAMETOOLONG` straight through, and a
    # NUL byte in the name raises `ValueError` on some Pythons) — the exact
    # escape hatch `artifactcontent.py` already documents. Unguarded, it
    # broke this function's own "never raises" contract (AC-3.6/NFR-1),
    # turning one unreadable spec into a whole-report `SparkDirUnreadableError`.
    try:
        exists = path.is_file()
    except (OSError, ValueError) as exc:
        return {"us": None, "acs": None, "reason": f"could not read file: {exc}"}
    if not exists:
        return {"us": None, "acs": None, "reason": "spec.md missing"}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    # `UnicodeDecodeError` is a `ValueError` subclass — it must be caught
    # first, or the broader clause below would swallow its own message.
    except UnicodeDecodeError as exc:
        return {"us": None, "acs": None, "reason": f"could not decode file as UTF-8: {exc}"}
    except (OSError, ValueError) as exc:
        return {"us": None, "acs": None, "reason": f"could not read file: {exc}"}

    # Review F3: silently scanning only `lines[:_MAX_LINES_SCANNED]` and
    # returning whatever partial count that produced was itself a fabricated
    # number with no reason the moment a file crossed the bound — exactly
    # what AC-3.6/constitution §6 ("never invent a number") forbid. A file
    # this large is not a real spec.md this project's own template
    # produces (largest observed: 597 lines), so refusing outright, named,
    # is the honest degradation, not a truncated guess.
    if len(lines) > _MAX_LINES_SCANNED:
        return {
            "us": None, "acs": None,
            "reason": f"spec.md exceeds {_MAX_LINES_SCANNED} lines; scope not counted",
        }

    us_count = 0
    ac_count = 0
    for line in lines:
        if _US_HEADING.match(line):
            us_count += 1
        elif _AC_LINE.match(line):
            ac_count += 1

    if us_count == 0:
        return {"us": None, "acs": None, "reason": "no US heading found"}
    return {"us": us_count, "acs": ac_count, "reason": None}
