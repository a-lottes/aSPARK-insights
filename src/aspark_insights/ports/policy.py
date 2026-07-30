"""PolicyPort — a stable seam for policy-consuming code, backed by a null adapter.

`aspark-policy` ships no resolver/CLI yet (P1-P3 unshipped). The null adapter
returns a well-formed "unavailable" result — never raises, never fabricates a
compliance number — naming the missing resolver as the reason (AC-3.1). Real
resolution lands in I8, once policy ships stable rule identifiers.
"""

from __future__ import annotations

from typing import Protocol

from aspark_insights.errors import PolicyUnavailable


class PolicyPort(Protocol):
    def resolve(self, repo_root: str) -> PolicyUnavailable | dict:
        """Return either policy version info, or a PolicyUnavailable naming why not."""
        ...


class NullPolicyPort:
    """The only adapter that exists today — inert until aspark-policy ships a resolver."""

    def resolve(self, repo_root: str) -> PolicyUnavailable:
        return PolicyUnavailable(
            "aspark-policy has no resolver/CLI yet (blocked on P1-P3)"
        )
