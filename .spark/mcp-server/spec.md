# Spec: mcp-server

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-03 |

## 1. Problem & Goal

- **Problem:** Since `traceability-metrics` (I2) shipped, `insights build` produces a real
  snapshot (facts/metrics/provenance), but the only way an agent already talking to an MCP
  host in a conversation can read it is to shell out to `insights query` as a subprocess and
  parse raw stdout — an extra hop the family already removed for graph facts, where
  `aspark-graph`'s own MCP server (`server.py`) exposes `get_node`/`story_trace`/`gate_health`/…
  as native tool calls. This isn't hypothetical friction: this project's own `/peer-review` and
  `/go-live` sessions (see `traceability-metrics/release.md` §1) already hand-invoke `insights`
  as a subprocess to read metric values mid-conversation.
- **Goal:** An MCP-capable agent host reads the latest snapshot's facts/metrics/provenance as a
  native tool call — no filesystem path argument to supply or get wrong — with the same clean,
  never-a-traceback error behavior the CLI already guarantees (constitution §6).
- **Success signal:** An MCP client (e.g. Claude Code) calling the `query` tool against a repo
  with a real built snapshot gets back JSON value-identical to what `insights query --repo
  <that repo>` prints to stdout, with **zero** path arguments passed at call time; calling it
  against a repo with no snapshot yet returns a clean `{"found": false, "reason": "no_snapshot",
  ...}`-shaped result, never a raw traceback.
- **Why now:** Backlog-sequenced directly after I2, which just shipped (`.spark/BACKLOG.md`
  §3, I7). The user picked this via `/next-steps`. The family's CLI↔MCP name-matching idiom
  (`aspark-graph` v0.5.0+) is currently only half-adopted across the family — insights has none.

## 2. Target Users

- **An MCP-capable agent host** (Claude Code or similar) already running SPARK ceremonies
  (`/peer-review`, `/demo-day`, ad hoc project Q&A) in a repo with a built insights snapshot —
  wants the same numbers `insights query` prints, without shelling out and parsing stdout by
  hand.
- **The operator wiring up the MCP server** (a human, or an agent-host config file) — picks
  which one repo's snapshot the server serves, the same way they already configure
  `aspark-graph`'s MCP server today (cwd or an explicit path at launch).

**Not a target:** an agent wanting freshly computed (not-yet-built) metrics — that still
requires running `insights build` via the CLI directly, deliberately outside this MCP surface
(see US-1). Multi-repo/fleet consumers are explicitly out of scope (I9, `.spark/BACKLOG.md`
§3, "Blockiert durch Entscheidung," still undecided).

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | The CLI verb to launch the server is `insights serve`. | Decided — mirrors `aspark-graph`'s own `serve` subcommand exactly (`cli.py:32`), the established family idiom the backlog invokes by name ("namensgleich zur CLI"), not invented here. |
| A2 | The server process serves exactly one repo/snapshot-output location, fixed once at launch via `--repo`/`--output` (the same two flags `insights build`/`query` already accept). | Decided. Multi-repo aggregation is I9, explicitly still blocked/undecided in the backlog — building it here would be scope creep ahead of that decision. |
| A3 | "Read-only" is enforced by *omission* (the MCP module never calls the snapshot-computation path), not by a runtime permission check. | Must be stated plainly as a real non-guarantee in `SECURITY.md` (US-2), not oversold as a boundary — same honesty framing `aspark-graph`'s own `SECURITY.md` Non-guarantee #1 uses for its confinement check. |
| A4 | Unlike `aspark-graph`'s G3, this feature adds **no** repo-confinement/marker check (`.git`/`.spark` shape check). | Decided. The backlog explicitly scopes this smaller ("kleiner") than G3. Removing the per-call path parameter entirely (A2) was judged a stronger, simpler mitigation than replicating a marker check for a target the operator already fixed once at launch — there is no untrusted per-call path left to confine. |
| A5 | `SECURITY.md` ships as an AC/DoD of this feature's own Must story (US-2), not a separate ceremony/gate before `/sprint-plan`. | **PO recommendation, not yet user-confirmed.** Justified by size: the entire surface being documented is one read-only tool with a fixed repo — small enough that splitting "write the tool" and "write its three-paragraph trust doc" into two `/story-time` passes is overhead the backlog's own phrasing ("Vorher SECURITY.md") doesn't obviously demand. Open to the user overriding toward a harder prerequisite gate. |
| A6 | `diff` and `verify` are excluded from the MCP surface in v1. | Decided (see §6, §7 C7) — `verify` internally recomputes via `GraphPort` even though it writes nothing, which the "never triggers a fresh build" rule (NFR-2) treats the same as `build`; `diff` would need a non-path snapshot-identifier design not yet worked out. Both deferred, not rejected. |

## 4. User Stories

### US-1 (Must): An agent reads the latest snapshot over MCP, read-only, no path parameters

> As an agent already talking to an MCP host, I want to call a tool named the same as the CLI
> command I'd otherwise shell out to, so that I get the same facts/metrics/provenance natively,
> without supplying (or mistyping) a filesystem path myself.

**Acceptance criteria:**

- [ ] AC-1.1: Given the package installed, when someone runs `insights serve --repo <path>
      --output <path>` (mirroring the existing `build`/`query` flag names and defaults), then a
      local stdio MCP server starts, configured to that one fixed repo/output location for its
      entire process lifetime.
- [ ] AC-1.2: Given the running server, when an MCP client calls the `query` tool, then it
      accepts **no** parameter of any kind — not a `repo`, `path`, `output`, or any other
      string that could become or contribute to a filesystem path. The repo/output location is
      never renegotiable per call.
- [ ] AC-1.3: Given a repo with a real built snapshot, when `query` is called, then it returns
      the same `facts`/`metrics`/`provenance` fields `insights query --repo <that repo>` prints
      to stdout for that same on-disk snapshot — value-identical, not a re-derived or
      re-filtered subset. Whatever TRC-*/MTA-* entries are currently registered and present in
      the snapshot's `metrics` array are returned as-is; no metric is enumerated by name in the
      tool itself, so a future newly registered metric appears automatically with no MCP-side
      change.
- [ ] AC-1.4: Given a repo with no snapshot built yet, when `query` is called, then it returns
      `{"found": false, "reason": "no_snapshot", "message": ...}` — never an unhandled
      exception or raw traceback through the stdio transport. Same shape and reasoning for a
      present-but-corrupt/malformed snapshot file (`reason: "snapshot_unreadable"`), reusing
      the CLI's own existing named-error reasons (`errors.py`), not a second, invented
      vocabulary.
- [ ] AC-1.5: Given the running server, when `query` is called any number of times in a row,
      then it never writes to `.aspark-insights/` and never invokes the computation path
      `insights build`/`insights verify` use (both reach `GraphPort`) — every call only reads a
      snapshot file already on disk at call time.
- [ ] AC-1.6: Given the running server, then the transport is stdio only — no HTTP listener, no
      bound network port, no authentication surface exists anywhere in this feature.

### US-2 (Must): `SECURITY.md` documents the trust boundary before this ships

> As the maintainer, I want a `SECURITY.md` that states this server's trust boundary and
> explicit non-guarantees, so a reviewer (or future contributor) can check it against the code
> and find no overclaim — matching the family's own established practice on `aspark-graph`.

**Acceptance criteria:**

- [ ] AC-2.1: Given the repository root, then `SECURITY.md` exists before/alongside this
      feature's release, and states the trust boundary: a local **stdio child process** of the
      calling agent host, running with the invoking user's own file permissions; **no auth, no
      HTTP, no network, no remote transport**; exactly **one** fixed repo/output target per
      process, set once at launch by whoever starts it (A2) — never chosen or changed by the
      calling agent mid-conversation.
- [ ] AC-2.2: Given `SECURITY.md`, then it contains a *Non-guarantees* section naming at least:
      (1) read-only is enforced by **omission** (the MCP module never calls the
      snapshot-computation path), not a runtime permission boundary (A3); (2) there is **no**
      repo-confinement/marker check — unlike `aspark-graph`, this feature does not verify the
      operator-chosen `--repo`/`--output` "looks like a repo" at all (A4); (3) this removes no
      privilege the operator did not already have — whoever can launch `insights serve --repo
      X` could already read `X` directly; (4) node identifiers returned in `facts`/`metrics`
      (e.g. `subject_id`) originate from the analyzed repo's own `.spark/` content via the
      graph, so a repo with adversarial `.spark/` content could produce adversarial-looking
      identifier strings — smaller than `aspark-graph`'s data-not-instruction caveat (insights
      Facts carry only booleans/tiers/ids, never free-text titles or prose), but the same
      caution applies to any string a caller displays verbatim.
- [ ] AC-2.3: Given `SECURITY.md`, then it names a vulnerability-reporting channel and initial
      response time, consistent with the family's existing practice (`aspark-graph/SECURITY.md`
      §"Reporting a vulnerability": GitHub private security advisories).
- [ ] AC-2.4: Given `SECURITY.md`, then no sentence outside the *Non-guarantees* section uses
      "sandbox", "isolat-", "contain", "prevent" or "protect" — the same anti-overclaim
      discipline `aspark-graph`'s own `SECURITY.md` enforces (its AC-2.4 precedent).

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | Security (`security` lens) | No MCP tool accepts any parameter that becomes or contributes to a filesystem path (AC-1.2); the server's repo/output target is fixed once at process launch and cannot change per call. | `/peer-review` (tool signature review) + a test enumerating each tool's parameters |
| NFR-2 | Security (`security` lens) | No MCP tool ever triggers the computation path `insights build`/`insights verify` use (both reach `GraphPort`); every tool response reads only a snapshot file already written to disk before the call (AC-1.5). | `/peer-review` (the MCP module never imports the snapshot-build function) + `/demo-day` (observe no `.aspark-insights/` write during a tool call) |
| NFR-3 | Reliability / clean errors | No MCP tool call ever raises an unhandled exception or leaks a raw Python traceback through the stdio transport; every failure returns a named, machine-readable error shape reusing the CLI's existing error reasons (AC-1.4) — never a second, invented vocabulary. | `/peer-review` + tests against no-snapshot and malformed-snapshot fixtures |
| NFR-4 | CLI (`cli` lens) | Every exposed MCP tool's name matches an existing `insights` CLI subcommand name exactly, and the server launches via an `insights serve` subcommand (A1) — the same CLI↔MCP naming idiom `aspark-graph` already established. No tool name is invented with no CLI counterpart. | `/peer-review` |
| NFR-5 | Library (`library` lens) | This feature adds exactly one new public entry point (the `serve` subcommand and its underlying module) — no new public class/function surface beyond what's needed to run the one tool and read an existing snapshot. | `/peer-review` (public-surface diff) |
| NFR-6 | Security / transport | Transport is stdio only: no HTTP listener, no bound network port, no authentication surface (AC-1.6). | `/peer-review` (dependency & code check) |
| NFR-7 | Performance | A `query` tool call returns in well under 1s on a mid-range laptop for current dogfood snapshot sizes (tens of facts/metrics) — it only reads a small, already-built JSON file. | `/demo-day` timing observation |
| NFR-8 | Consistency | For the same on-disk snapshot, the `query` tool's output is value-identical to `insights query --repo <same repo>`'s stdout (AC-1.3) — the MCP surface never computes or presents a different answer than the CLI. | `/peer-review` + a parity test (same style as `aspark-graph`'s own CLI↔MCP parity test) |
| NFR-9 | Accessibility | N/A — no UI surface; stdio JSON only. | — |

## 6. Out of Scope

- **Multi-repo / fleet aggregation** — I9, explicitly still blocked on an undecided
  architecture question per the backlog. This feature serves exactly one repo per process (A2).
- **`diff` and `verify` as MCP tools** — deferred (A6, §7 C7): `verify` internally recomputes
  via `GraphPort`, which NFR-2 treats the same as `build`; `diff` needs a non-path
  snapshot-identifier scheme not designed here.
- **A repo-confinement/marker check** (`.git`/`.spark` shape check, mirroring `aspark-graph`'s
  G3) — deliberately not built (A4); removing the per-call path parameter was judged sufficient
  for a fixed, operator-chosen target.
- **HTTP, remote, or authenticated transport** — stdio only (NFR-6); no evidence of a need for
  anything else, and the security lens's rationale (no network surface today) argues against it.
- **A "list snapshots" / historical-snapshot enumeration tool** — not asked for; would also
  reopen the "path parameter" question for identifying which snapshot. Revisit if `diff` is
  ever built.
- **`render`/dashboard exposure over MCP** — `render` is still an unimplemented CLI stub (I5).
- **Any new metric computation** — this feature only serves whatever I2 already computed;
  it never adds a TRC-*/MTA-* entry.
- **Threshold enforcement / gating over MCP** — repeated non-negotiable, same as the CLI
  (`aspark-ci` consumes the JSON; insights never enforces).
- **Person-level metrics** — permanently out, not a scheduling choice (constitution §6).

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-03 | Is "read-only" structurally enforced, or just documented intent? | Enforced by omission and checked, not just asserted: NFR-2 requires the MCP module never import/call the snapshot-computation path, verified at `/peer-review` and observed at `/demo-day` (no `.aspark-insights/` write during a call) — same enforcement spirit as the existing `GraphPort`-boundary check (AC-2.4 in `foundation`), though here it's "never call" rather than "only call through one seam." |
| C2 | 2026-08-03 | What happens when no snapshot exists yet? | A clean, named error shape (`{"found": false, "reason": "no_snapshot", ...}`), never a raw traceback — AC-1.4, reusing the CLI's own existing error taxonomy rather than inventing a second one. |
| C3 | 2026-08-03 | Multi-repo support? | No — exactly one repo per server process, fixed at launch (A2). I9 (fleet) is explicitly still blocked on an undecided architecture question; building multi-repo here would preempt that decision without evidence of need. |
| C4 | 2026-08-03 | Expose all of TRC-001…005/MTA-001…003, or a curated subset? | All of whatever the snapshot currently contains — AC-1.3 returns the same `metrics` array `insights query` already returns, with no metric enumerated by name in the tool. No new exposure surface invented; this mirrors exactly what I2 shipped. |
| C5 | 2026-08-03 | Transport: stdio only, or should HTTP/remote be considered? | stdio only (NFR-6) — matches the family idiom and the constitution's security-lens rationale (no network surface today, grounded in real `foundation` QA findings, not speculative). No case was made for remote access, so none is built. |
| C6 | 2026-08-03 | Should `SECURITY.md` be an AC of this feature's Must story, or a prerequisite gate before `/sprint-plan`? | PO recommends: an AC/DoD of US-2, part of this same spec (A5) — the surface is small enough (one read-only tool, one fixed repo) that a second `/story-time` pass for a three-paragraph doc is overhead the backlog phrasing doesn't clearly demand. Not yet user-confirmed; flagged as an explicit judgment call, not silently decided. |
| C7 | 2026-08-03 | Should `diff`/`verify` be exposed over MCP now, since the CLI already has them? | No (A6). `verify` reaches `GraphPort` to recompute (even though it writes nothing) — NFR-2's "never triggers a fresh build" treats that the same as `build`. `diff` takes two filesystem paths on the CLI today; exposing it over MCP would need a non-path snapshot-identifier design (e.g. by `as_of` date, resolved server-side against the one fixed snapshot directory) that isn't designed here. Both parked, not rejected — natural candidates for a follow-up increment once `query` alone is proven useful. |

## 8. Design Review

N/A — no UI surface (stdio MCP + JSON only), same framing as `traceability-metrics` §8. To be
revisited only if a future increment adds a rendered surface (I5, `dashboards`, remains
unrelated to this feature).

---

## ✅ SPEC GATE

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone")
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason)
- [x] Clarify pass done: no ambiguity left unresolved or unparked
- [x] Open questions are resolved or explicitly accepted as risk (A5 flagged as PO recommendation pending user confirmation)
- [x] Out-of-scope section is filled (something was consciously cut)
- [x] Constitution (`.spark/constitution.md`) respected, or conflicts recorded as open questions
- [x] Design review done for UI-facing features (or marked N/A with reason) — N/A, see §8
- [x] Status set to `approved` by the user
