# Security

## Trust boundary

`insights serve`'s MCP server is a **local stdio child process** of the calling agent host. It runs with the **invoking user's own file permissions** — it has no account, no elevated access, and no boundary of its own around what it can read on disk. There is **no authentication, no HTTP listener, no network access, and no remote transport**: the only way to reach it is the stdio pipe an agent host opens when it launches the process.

Exactly **one** repo/output target is served per process, fixed once at
launch by whoever runs `insights serve --repo <path> --output <path>` — it
is never chosen or changed by the calling agent mid-conversation. The
`query` tool takes no arguments of any kind.

The `mcp` SDK dependency is capped at `>=1.12,<1.20`. Versions `1.20+`
hard-pull `cryptography` to support server-side OAuth, a feature this server
does not use and has no code path for. The cap is a **packaging decision** —
it keeps the tool installable on platforms without a `cryptography` wheel —
not a security control.

## Non-guarantees

This project does not claim, and this document does not imply, any of the
following:

1. **Read-only is enforced by omission, not a runtime permission
   boundary.** The `query` tool never calls the snapshot-computation path
   because `server.py`/`query.py` never import it — checked structurally at
   `/peer-review` and in CI (`tests/test_boundary.py`). This is a code-shape
   guarantee, not a sandbox or process-level access-control mechanism
   enforcing it from outside the code.
2. **There is no repo-confinement or marker check.** Unlike `aspark-graph`,
   this server does not verify that the operator-chosen `--repo`/`--output`
   "looks like a repo" (a `.git`/`.spark` shape check) at all. Any directory
   the operator points it at is served as-is.
3. **This removes no privilege the operator did not already have.**
   Whoever can launch `insights serve --repo X` could already read `X`
   directly on the same machine — the server adds a query interface, not a
   new access boundary.
4. **Identifier strings in `facts`/`metrics` are not guaranteed free of
   adversarial content.** `subject_id` and similar identifiers originate
   from the analyzed repo's own `.spark/` content, by way of the graph. This
   is a narrower caveat than `aspark-graph`'s own — insights' `Fact` model
   carries only booleans, confidence tiers and ids, never free-text titles
   or prose — but a repo with adversarial `.spark/` content could still
   produce adversarial-looking identifier strings, and no sanitisation is
   applied before they reach a caller.

## Reporting a vulnerability

Report suspected vulnerabilities through **GitHub private security
advisories** on this repository — never a public issue. Use the "Report a
vulnerability" button under the repository's Security tab. You will get an
initial response within **5 working days**.

In scope: anything that makes this server's actual behaviour diverge from
what this document states — for example, a tool call that accepts a
path-like argument, a call that writes to `.aspark-insights/`, or a call
that triggers a fresh `insights build`/`verify`. The design limitations
already described in the *Non-guarantees* section above are known, and
reporting one of them back to us is not necessary; they are not bugs.
