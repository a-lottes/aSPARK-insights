# Spec: traceability-metrics

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-07-31 |

## 1. Problem & Goal

- **Problem:** `foundation` (I1) shipped a package that builds a snapshot with an *empty*
  metric catalog. No one — not the Insights maintainer, not the two dogfood repos this
  product exists to prove itself on — can see a single real number about their delivery
  process yet. Meanwhile a verified, real data-quality trap already sits in the graph's own
  repo (49 of 98 File nodes are `.claude/worktrees/**` duplicates — ARCHITECTURE-PROPOSAL.md
  §2.1) that would silently double-count coverage if a naive metric read the graph as-is.
- **Goal:** `insights build` against a real, built `aspark-graph` v0.5.0/v0.7.0 repo returns
  real Story→Task, AC→QA and Task→Code coverage (TRC-001…003), an orphan/unverified count
  (TRC-004), each with its own sample size and an honest `null`+reason wherever the graph has
  nothing to count — computed with a documented scope filter, not a raw unfiltered read.
- **Success signal:** `insights build --as-of <date> --repo <path-to-aSPARK-graph checkout>`
  returns a TRC-002 (AC→QA coverage) value with `n` equal to the real AcceptanceCriterion
  count the graph indexes for that repo (not a placeholder, not `null` without cause);
  building the same inputs twice produces byte-identical snapshot files.
- **Why now:** the backlog sequences every later increment (I3 flow, I4 architecture, I5
  dashboards, I7 MCP) as "after I2" — none of them has real data to render, join or serve
  until this ships. The family's own positioning guardrail ("Insights stays *Geplant* until
  it produces real numbers," ARCHITECTURE-PROPOSAL.md §1) is blocked on exactly this.

## 2. Target Users

- **The aSPARK-graph and aSPARK-policy maintainers, today** — the two named dogfood targets;
  the first people who will actually read a number this feature produces.
- **The Insights maintainer building I3+ next** — the same internal role foundation served;
  needs TRC-*/MTA-* proven end-to-end (registry entry → Collector → sealed snapshot) before
  adding flow/architecture/debt metrics on the same scaffold.

No dashboard consumer yet (I5) and no MCP-reading agent yet (I7) — both explicitly wait for
this feature's real values to exist before they have anything to render or serve.

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | Both dogfood repos have a graph built (`aspark-graph build .`) before `/demo-day`. Neither currently does (`.aspark-graph/graph.json` absent in both, verified). | Running the sibling's own already-shipped `build` command once is an operational step, not a "neighbor-repo change" — no code in either sibling changes. In scope for `/demo-day`, not this spec. |
| A2 | `aSPARK-policy` has no `.spark/` feature directories yet (verified — early-stage per BACKLOG.md §2). | Every TRC metric computed there legitimately reports `null` + `n=0` ("no Story/AC/Task nodes found") — this is the honest answer for an empty repo, not a defect to fix here (see AC-1.4, AC-7.2). |
| A3 (risk, verified) | `aspark-graph` v0.7.0's own artifact parser (`src/aspark_graph/artifacts.py`) hardcodes `review-report.md` / `qa-report.md` / `release-notes.md` — **not** aSPARK's current `review.md` / `qa.md` / `release.md` convention (confirmed: this repo's own `.spark/foundation/` uses the current names). `aSPARK-graph`'s **own** `.spark/aspark-graph/` happens to still use the old names, so `verifies`/`Finding` nodes populate correctly *there* — the stated dogfood target is unaffected. But any repo using the current convention (this repo included, once self-dogfooded) will silently show zero QA_CHECK/Finding nodes — not because no QA happened, but because the graph never found the file. | Accepted as a real, named risk — not fixed here. TRC-002/TRC-004 trust whatever the graph actually parsed (ADR-0: never build a second artifact parser to route around it — same "no second parser" precedent as ADR-2's git rule). Recorded in provenance via existing graph-source/staleness disclosure, not a new field invented to paper over it. **Recommended next step (not built here):** file this as a graph-backlog item (a `review-report.md`→`review.md` rename or alias, sibling to the already-proposed G7) — left for the user to decide whether to raise it. |
| A4 | The library-interim `GraphPort` adapter (bulk `read_graph`) has no named-query surface; only `CLIGraphPort` can run `query staleness`. | This feature's build path uses **both** adapters — bulk library read for Facts/TRC-*, one CLI query for MTA-002's staleness disclosure. Already anticipated by I1's two-adapter design; the exact call sequence is a `/sprint-plan` "how". |

## 4. User Stories

### US-1 (Must): Core coverage metrics — TRC-001, TRC-002, TRC-003

> As an aSPARK-graph/aSPARK-policy maintainer, I want story→task, AC→QA and task→code
> coverage computed from my repo's actual graph, so that I see real traceability numbers
> instead of an empty catalog.

**Acceptance criteria:**

- [ ] AC-1.1: Given a built graph, when `insights build --as-of <date>` runs, then the
      snapshot's metrics include TRC-001 (`value` = share of Story nodes with ≥1 incoming
      `maps_to` edge, `n` = total Story count).
- [ ] AC-1.2: Given the same build, then TRC-002's `value` = share of AcceptanceCriterion
      nodes with ≥1 incoming `verifies` edge whose QACheck `result` is `"pass"`, `n` = total
      AC count. (A failing or unresolved QA check does not count as coverage — kept
      consistent with TRC-004's explicit pass-only "unverified" definition, AC-2.1.)
- [ ] AC-1.3: Given the same build, then TRC-003's `value` = share of Task nodes with ≥1
      outgoing `implements` edge (any confidence tier), `n` = total Task count.
- [ ] AC-1.4: Given a graph with zero nodes of the relevant kind (e.g. no Story node exists),
      when the corresponding metric is computed, then its `MetricValue` is `value: null` with
      a reason naming the empty denominator (e.g. `"no Story nodes found in graph"`) and
      `n: 0` — never a fabricated `0.0` or `1.0` for a zero/zero division.
- [ ] AC-1.5: Given a stored snapshot with real metrics, when running `insights query`, then
      the printed JSON includes the snapshot's `metrics` array alongside `facts`/`provenance`
      (foundation's AC-6.5 deferred this only because no metric existed yet).

### US-2 (Must): Orphan / unverified rate — TRC-004

> As an aSPARK-graph maintainer, I want to see which tasks and acceptance criteria have no
> traceable link at all, so that I know where the trace breaks down without re-deriving the
> graph's own gate logic myself.

**Acceptance criteria:**

- [ ] AC-2.1: Given the graph's own orphan-task predicate (a Task with no outgoing `maps_to`)
      and unverified-AC predicate (an AC with no incoming `verifies` whose `result` is
      `"pass"`) — the exact predicates `aspark-graph`'s `gate_health` already defines — when a
      snapshot is built, then TRC-004 reports the orphan-task count (`n` = total Tasks) and the
      unverified-AC count (`n` = total ACs) as two distinct values, never blended into one
      ratio that would hide which predicate drove it.
- [ ] AC-2.2: Given `gate_health`'s `open_findings` field depends on Finding nodes that the
      graph's artifact parser only populates for the legacy `review-report.md`/`qa-report.md`
      filenames (A3), when TRC-004 is computed, then it never surfaces `open_findings` as
      evidence — only the two structurally sound predicates in AC-2.1.

### US-3 (Should): Evidence confidence-mix — TRC-005

> As an Insights maintainer, I want to know how much of the traceability picture rests on
> declared links versus best-effort inference, so that a high coverage number isn't mistaken
> for a strongly-evidenced one.

**Acceptance criteria:**

- [ ] AC-3.1: Given the graph's own confidence ranking on trace-path edges (`declared` >
      `extracted` > `inferred`, already computed by `impact`/`story_trace`'s weakest-link
      logic), when TRC-005 is computed, then it reports the declared/extracted/inferred share
      of the weakest link across every Story's full trace to its tasks' code links — reusing
      the graph's existing tagging, never a second independently-invented confidence scheme.
- [ ] AC-3.2: Given zero Story nodes, then TRC-005's value is `null` with a reason, `n: 0` —
      same zero-denominator rule as AC-1.4.

### US-4 (Must): Sample size travels with every metric — MTA-001

> As anyone reading a metric value, I want its sample size right next to it, so that a
> percentage over 2 items is never mistaken for one over 200.

**Acceptance criteria:**

- [ ] AC-4.1: Given any of TRC-001…005, when its value is computed, then the same result
      carries the exact denominator (`n`) used to compute it — not a separately looked-up
      metric id, since each TRC metric's denominator differs (Story count vs. AC count vs.
      Task count). No metric in this feature ships without its own `n`.
- [ ] AC-4.2: Given `n = 0` for any metric, the value is `null` with a reason naming the
      absent node kind — the same rule as AC-1.4/AC-3.2, stated once here as the general case.

### US-5 (Must): Scope exclusions disclosed — MTA-003 / ScopeFilter

> As anyone reading a coverage number, I want to know if worktree duplicates or other noise
> were filtered out before the number was computed, so I don't mistake a scoped result for
> the whole repo, or a filtered-out flaw for the true count.

**Acceptance criteria:**

- [ ] AC-5.1: Given the graph document read via GraphPort, when nodes under a built-in
      default exclusion set (at minimum `.claude/worktrees/**`) are present, then they are
      excluded from every TRC-* metric's numerator and denominator, and the snapshot's
      provenance records which patterns were applied and how many nodes were dropped.
- [ ] AC-5.2: Given a graph with none of the excluded paths present, then provenance still
      records the (empty) exclusion result explicitly — present, not omitted.

### US-6 (Must): Graph freshness disclosed — MTA-002

> As anyone reading a snapshot, I want to know whether the graph it was built from still
> matched the repo on disk, so a stale graph's numbers are never mistaken for current ones.

**Acceptance criteria:**

- [ ] AC-6.1: Given a built graph, when a snapshot is built, then provenance records the
      graph's own `staleness` result (`stale`, `files_checked`, `changed`, `missing`) captured
      at build time.
- [ ] AC-6.2: Given the graph reports `stale: true`, metrics are still computed from whatever
      was read (build never silently refuses), but provenance's staleness field makes the
      caveat visible — a stale snapshot's numbers are never presented as unconditionally fresh.

### US-7 (Must): Dogfooded and deterministic

> As the Insights maintainer, I want the whole pipeline proven end-to-end on both named
> repos with the existing determinism guarantee intact, so "real numbers, reproducibly" is
> demonstrated, not just asserted.

**Acceptance criteria:**

- [ ] AC-7.1: Given a real, built `aSPARK-graph` repo, `insights build --as-of <date> --repo
      <path>` produces TRC-001…004 (and TRC-005) with real, non-placeholder values or an
      honest `null`+reason, each with `n` populated.
- [ ] AC-7.2: Given a real, built `aSPARK-policy` repo (currently zero `.spark/` features),
      every TRC metric legitimately reports `null` + reason ("no Story/AC/Task nodes found")
      with `n: 0` — not a fabricated `0%` or `100%` for an empty repo.
- [ ] AC-7.3: Given the same repo and `as_of` built twice independently, the two output
      snapshot files — now containing a non-empty metrics catalog — are byte-identical,
      extending I1's determinism canary fixture/CI job past the empty-catalog case.

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | Reliability / determinism | Identical inputs ⇒ byte-identical snapshot, now with a non-empty metrics catalog (extends foundation's canary fixture). | CI determinism canary + `insights verify` |
| NFR-2 | Evidence honesty (Non-Negotiable) | No TRC/MTA metric ever reports a numeric value when its denominator is zero or the required node kind is entirely absent — always `null`+reason instead (AC-1.4, AC-3.2, AC-4.2, AC-7.2). | Unit tests against a zero-Story/zero-AC fixture + `/peer-review` |
| NFR-3 | Security (`security` lens) | Any new CLI-reachable input this feature adds (e.g. a scope-exclude pattern, if ever exposed as a flag) passes the hostile-input checklist (empty string, `../` traversal, absolute path, wrong-but-valid-JSON shape, missing keys) before being used to filter graph data; failure is a named error, never a raw traceback. | `/peer-review` + targeted hostile-input tests |
| NFR-4 | Architecture boundary | Every new Collector/metric file reads graph data exclusively through `GraphPort` — no new direct `aspark_graph` import site outside `ports/graph.py` (extends foundation's AC-2.4). | CI boundary grep + `/peer-review` |
| NFR-5 | Library (`library` lens) | Each TRC-*/MTA-* registry entry is registered under an immutable `(id, version)` pair; a shipped definition is never edited in place — a changed computation ships as a new version, so a historical snapshot stays interpretable against the version it names. | `/peer-review` + an append-only-registry test |
| NFR-6 | Performance | `insights build --as-of <date>` completes in under 60 seconds against the current aSPARK-graph and aSPARK-policy graphs (low tens of features/stories) on a mid-range laptop — resolves the constitution's flagged open question (§4) now that real computation exists. | `/demo-day` timing observation |
| NFR-7 | Accessibility | N/A — no UI surface in this feature (CLI/JSON only); dashboards are I5. | — |
| NFR-8 | CLI (`cli` lens) | No new subcommand is added; `build`/`query --help` text documents that `metrics` now carries real TRC-*/MTA-* entries (not an empty catalog), so a first-time reader isn't left guessing why the array used to be empty. | Golden-output `--help` test + `/demo-day` |

## 6. Out of Scope

- **FLW-\*** (I3, blocked on graph G1/G2), **ARC-\*** (I4, honest only after graph G7 scope
  hygiene), **DBT-\*** and **MTA-004** (I6/I8, blocked on policy P1–P3) — all later increments.
- **Dashboards / HTML rendering** (I5) — `render` stays the loud `not_implemented` stub from I1.
- **MCP server** (I7), **fleet / multi-repo aggregation** (I9).
- **A graph-side fix for the `review-report.md` vs. `review.md` artifact-filename mismatch**
  (A3) — a real, verified upstream gap, but a neighbor-repo change; this feature discloses
  the risk, it does not patch the sibling.
- **A second, Insights-side artifact parser** to route around that mismatch — explicitly
  rejected; would violate "don't recompute what the graph answers" (ADR-0) and the "no second
  parser" precedent already set for git (ADR-2).
- **CLI-configurable scope-exclude patterns** beyond the built-in default set (US-5) — a
  future refinement once a real second exclusion case is observed, not invented speculatively.
- **Per-feature drill-down** of TRC-004 as separately queryable slices — the repo-wide
  aggregate (US-2) is the Must; per-feature breakdown is a future nicety.
- **Threshold enforcement / gating** on any TRC/MTA value — always `aspark-ci`'s job,
  never Insights' (non-negotiable, repeated from the constitution).
- **Person-level metrics** — permanently out, not a scheduling choice.

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-07-31 | Is MTA-001 (`n`) its own registry metric, separate from TRC-*? | No — `n` is a structural field on every `MetricValue`, not an independently looked-up id, since each TRC metric's denominator differs. See US-4. |
| C2 | 2026-07-31 | Is TRC-005 (confidence-mix) premature for I2? | No — it wraps the graph's own existing `declared`/`extracted`/`inferred` tagging on trace-path edges (already computed by `impact`/`story_trace`), no new scheme invented. Kept Should, given lower dogfood urgency than the headline coverage numbers. |
| C3 | 2026-07-31 | Does TRC-004 need one CLI call to `gate_health` per feature? | No — its two sound predicates (orphan tasks, unverified ACs) are derivable directly from the bulk graph document already read via the library-interim `GraphPort`, mirroring `gate_health`'s own definition rather than reimplementing a different one, and without O(features) subprocess calls. |
| C4 | 2026-07-31 | What about `gate_health`'s `open_findings` and the artifact-filename mismatch (A3)? | TRC-004 never surfaces `open_findings`. The filename mismatch is recorded as a named, verified risk (A3), not fixed here — no second parser, no neighbor-repo change. |
| C5 | 2026-07-31 | Should ScopeFilter's exclusion patterns be CLI-configurable in v1? | No — ships with a built-in default set (≥ `.claude/worktrees/**`), always disclosed in provenance (US-5); configurability parked (§6). |
| C6 | 2026-07-31 | Should `insights query` surface metric values now that real ones exist? | Yes — extends foundation's AC-6.5, which deferred this only because no metric existed yet. See AC-1.5. |
| C7 | 2026-08-01 | AC-1.2 said "≥1 incoming `verifies` edge" (any result); `/increment` shipped it as pass-only, to stay consistent with TRC-004's explicit pass-only "unverified" definition (AC-2.1) — a failing QA check shouldn't count as "covered" under one metric and "not covered" under the sibling metric. `/peer-review` (F4) flagged the spec text as never reconciled to the shipped, reviewed behavior. | AC-1.2 amended to state the pass-only requirement explicitly (this row). No code change — the shipped behavior was already correct; only the spec text was out of date. |

## 8. Design Review

N/A for this feature — no UI surface (CLI/JSON only). To be revisited at I5 (`dashboards`).

---

## ✅ SPEC GATE

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone")
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason)
- [x] Clarify pass done: no ambiguity left unresolved or unparked
- [x] Open questions are resolved or explicitly accepted as risk (A3)
- [x] Out-of-scope section is filled (something was consciously cut)
- [x] Constitution (`.spark/constitution.md`) respected, or conflicts recorded as open questions
- [x] Design review done for UI-facing features (or marked N/A with reason) — N/A, see §8
- [x] Status set to `approved` by the user
