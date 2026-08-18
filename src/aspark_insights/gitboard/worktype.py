"""worktype — classify a commit subject's leading Conventional-Commit token.

Two pure functions, no I/O, no git — unit-testable against plain subject
lists in isolation from the subprocess seam and the CLI orchestration.

Never infers a type from anything but the leading token (spec §6): no
keyword heuristics on subject text, no path-based classification, no LLM.
A commit that doesn't carry a recognized token is `unclassified` — never
guessed.
"""

from __future__ import annotations

import re

# Fixed, declared order — the same order the mix bar and legend render in
# (AC-4.11), so two runs of one repo are visually comparable, not just
# byte-stable (NFR-5). `unclassified` is not a member: it's the remainder,
# always appended last by `breakdown`, never a token to match.
RECOGNIZED_TYPES: tuple[str, ...] = (
    "feat", "fix", "docs", "chore", "refactor", "test", "build", "ci", "perf", "style",
)

_UNCLASSIFIED = "unclassified"

# One fixed, compiled pattern — never a regex built from repo content (NFR-2).
# `type(scope)!: subject` — scope and `!` (breaking-change marker) tolerated
# but not captured; only the leading type token is classified.
_TYPE_PATTERN = re.compile(
    r"^(" + "|".join(re.escape(t) for t in RECOGNIZED_TYPES) + r")(\([^)]*\))?!?:",
    re.IGNORECASE,
)

# AC-1.12(a): below this share of classifiable commits, the whole breakdown
# is too thin to characterize the work mix — an honest null, not a guess.
_MIN_CLASSIFIABLE_SHARE = 0.20


def classify(subject: str) -> str | None:
    """The recognized type token (lowercased), or `None` if the subject
    carries no Conventional-Commit prefix from the fixed set."""
    match = _TYPE_PATTERN.match(subject)
    return match.group(1).lower() if match else None


def breakdown(subjects: list[str]) -> dict:
    """A proportional work-type mix, or an honest null when too few subjects
    are classifiable to characterize the mix at all (AC-1.12(a)).

    Callers decide the *absent* cases (no tag; zero commits since tag) —
    this function only ever sees a real, nonempty population; `subjects`
    must be non-empty (board.py never calls it otherwise)."""
    types = [classify(s) for s in subjects]
    classified = [t for t in types if t is not None]
    share = len(classified) / len(subjects)

    if share < _MIN_CLASSIFIABLE_SHARE:
        return {
            "value": None,
            "reason": (
                f"{len(classified)} of {len(subjects)} commits carry a recognized "
                "Conventional Commit type; too few to characterize the work mix"
            ),
        }

    counts: dict[str, int] = {t: 0 for t in RECOGNIZED_TYPES}
    for t in classified:
        counts[t] += 1
    unclassified_count = len(subjects) - len(classified)

    distribution = {
        t: round(count / len(subjects) * 100)
        for t, count in counts.items()
        if count > 0
    }
    if unclassified_count > 0:
        distribution[_UNCLASSIFIED] = round(unclassified_count / len(subjects) * 100)

    return {"value": distribution, "reason": None}
