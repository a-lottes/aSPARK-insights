"""Canonical JSON — the byte-stability contract every snapshot and CLI output relies on."""

from __future__ import annotations

import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """Sorted keys, stable indent, no ascii-escaping, trailing newline.

    Same input must always produce the same bytes — this is the determinism
    canary's substrate (ADR-4), not merely a formatting preference.
    """
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
