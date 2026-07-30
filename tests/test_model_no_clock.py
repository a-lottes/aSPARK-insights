"""ADR-4: no ambient clock in the derivation path — enforced at the model layer."""

from __future__ import annotations

import re
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent.parent / "src" / "aspark_insights" / "model"

_FORBIDDEN = re.compile(r"^\s*(import\s+(datetime|time)\b|from\s+(datetime|time)\s+import)", re.MULTILINE)


def test_model_files_never_import_datetime_or_time():
    offenders = []
    for path in sorted(MODEL_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if _FORBIDDEN.search(text):
            offenders.append(str(path.relative_to(MODEL_DIR.parent.parent.parent)))
    assert not offenders, f"model/ must never read an ambient clock: {offenders}"
