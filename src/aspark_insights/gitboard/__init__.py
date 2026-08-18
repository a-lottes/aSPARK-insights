"""gitboard — the git-native standalone mid-cycle board.

Reads only local git plumbing (never the sibling graph port, never `.spark/`) to answer
"what landed since the last release marker, what's in flight" — the ADR-2
documented interim fallback (BACKLOG.md §4 "Eigener Git-Parser") activated
for real, proving Insights can serve any git repo, not only the aSPARK
family (spec.md US-2). Every output self-discloses `source: "git-interim"`
so it is never mistaken for a graph-sourced (future G1/G2) fact.
"""

from __future__ import annotations
