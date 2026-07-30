# Spec: foundation

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-07-29 |

## 1. Problem & Goal

- **Problem:** aSPARK-insights is an empty, not-yet-`git init`-ed repo. Every non-negotiable
  already fixed for this product — the graph/insights boundary (ADR-0), no ambient clock in
  derivation (ADR-4), never person-level metrics, never invent a number — is cheapest to bake
  into the model and CLI *today*, before any real computation exists to grandfather exceptions
  around later (e.g. a "just this one metric needs a committer field" creeping in during I2).
- **Goal:** A working, deterministic package skeleton that the next feature
  (I2 `traceability-metrics`) can add real metric definitions to without redesigning ports,
  the core model, the CLI subcommand shape, or the determinism guarantee.
- **Success signal:** `insights build` runs end-to-end — reads a real graph via the interim
  GraphPort adapter, produces a sealed, provenance-complete snapshot under
  `.aspark-insights/` with an *empty* metric catalog — and the CI determinism canary (double
  build, byte-compare) is green. I2 can then start by adding functions to the registry and
  wiring Collectors, touching nothing in `ports/`, the model's core shape, or `cli.py`'s
  subcommand wiring.
- **Why now:** Nothing on the I1–I9 roadmap can start without this. The sibling graph backlog
  has already reserved cross-repo vocabulary "für insights" (G1 `release-nodes`, G2
  `dora-query`) that only makes sense once a consumer exists. Each guardrail (determinism,
  no person-level subjects) is structurally cheap to enforce now and expensive to retrofit
  once real metrics assume a looser model.

## 2. Target Users

No external end user yet — Insights has shipped nothing consumer-facing, and per the family's
own positioning guardrail it stays "Geplant" until I2 produces real numbers. This feature
serves two internal roles instead of inventing a premature "dashboard user":

- **The Insights maintainer** who builds I2 next (traceability metrics) — the immediate
  beneficiary of a scaffold they don't have to redesign.
- **CI, acting as an always-on auditor** of the determinism guarantee (ADR-4) — every commit
  after this one is checked against it automatically, not just at code review time.

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | `aspark-graph` can be installed as a version-pinned dependency (path/git/registry) so the interim library adapter has something real to import. | Assumed yes (sibling repo lives locally under the family stack); exact pin mechanism is a technical "how" — parked for `/sprint-plan`. |
| A2 | The determinism canary needs a **fixed fixture input** (not a live, moving repo) so CI results stay stable over time. | Assumed yes; fixture design (what graph state, what `as_of`) parked for `/sprint-plan`. |
| A3 | `aspark-policy` has no resolver/CLI yet — `PolicyPort`'s null adapter is intentionally inert until policy P1–P3 ship. | Confirmed by the neighbor-repo brief; not reopened here. |
| Q1 | Is this repo's `.spark/` tracked publicly or kept local (CROSS-REPO-PLAN §6, item 3)? | **Resolved 2026-07-29 by the user:** `.spark/` is git-tracked and public, matching the `aspark-graph` / `aSPARK` Core precedent (not `aspark-policy`'s local precedent). No longer open. |

## 4. User Stories

### US-1 (Must): Family-stack package scaffold

> As the Insights maintainer, I want a package that follows the family's Python stack
> conventions, so that I can start writing Insights code without re-deciding tooling.

**Acceptance criteria:**

- [ ] AC-1.1: Given a fresh clone, when running `uv sync`, then dependencies resolve from the
      committed `uv.lock` with no drift (`uv lock --check` exits 0).
- [ ] AC-1.2: Given the installed package, when importing `aspark_insights`, then `ports`,
      `model`, `metrics` and `cli` submodules import without error.
- [ ] AC-1.3: Given `pyproject.toml`, when inspected, then `requires-python >= 3.11` and the
      build backend is `hatchling`.

### US-2 (Must): GraphPort — the only seam to aspark-graph

> As the Insights maintainer, I want every graph read routed through one GraphPort with a
> CLI adapter and a version-pinned interim library adapter, so that Insights never depends
> on `.aspark-graph/graph.json`'s file format directly, and the interim coupling's expiry
> stays visible.

**Acceptance criteria:**

- [ ] AC-2.1: Given a built aspark-graph repo, when the CLI adapter issues a supported query,
      then it returns the parsed JSON the graph's own C2 contract promises; against an
      unbuilt graph it raises a named error, never a raw crash.
- [ ] AC-2.2: Given the interim library adapter, when it reads the whole graph document via
      the pinned `aspark_graph` import, then the result matches the canonical `nodes`/`edges`
      content the graph itself would persist; if the installed version doesn't match the pin,
      it refuses with a named error rather than reading a possibly-wrong shape.
- [ ] AC-2.3: Given any successful GraphPort read, when a snapshot is built from it, then
      provenance records `graph_source.access` (`"library-interim"` or the CLI equivalent) so
      the sunset condition (retires at graph's G6) stays visible in every snapshot.
- [ ] AC-2.4: Given the codebase, when searching outside the GraphPort's own files, then no
      code reads `.aspark-graph/graph.json` or imports `aspark_graph` internals directly
      (checked in CI and at `/peer-review`).

### US-3 (Should): PolicyPort — null adapter for now

> As the Insights maintainer, I want a stable PolicyPort interface backed by a null adapter,
> so that future policy-consuming code has a real seam to compile against today, without
> pretending a resolver exists.

**Acceptance criteria:**

- [ ] AC-3.1: Given aspark-policy ships no resolver/CLI yet, when PolicyPort is called, then
      it returns a well-formed "unavailable" result — never an exception, never fabricated
      data — naming the missing resolver as the reason.
- [ ] AC-3.2: Given the null adapter, when a snapshot is built, then provenance's
      `policy_versions` field is explicitly `null` (present, not omitted).

### US-4 (Must): Fact / Snapshot / Provenance / MetricValue model with built-in guardrails

> As the Insights maintainer, I want the core data model to structurally forbid
> person-level subjects and to represent "no honest value" as a first-class case, so later
> metrics can't accidentally violate the family's non-negotiables.

**Acceptance criteria:**

- [ ] AC-4.1: Given the Fact model's subject/entity kinds, when reviewed, then only system-,
      feature-, and code-artifact-level kinds exist — none represents an individual person
      (e.g. commit author, assignee).
- [ ] AC-4.2: Given MetricValue, when a metric cannot honestly compute a number, then the
      model represents `value: null` together with a mandatory, non-empty `reason` — a null
      without a reason is not constructible.
- [ ] AC-4.3: Given Provenance, when a Snapshot is sealed, then it always carries `as_of`,
      `insights_version`, `metric_registry_version`, `graph_source` (`access`, `sealed`) and
      `policy_versions` — all supplied as inputs, never read from the wall clock at build time.
- [ ] AC-4.4: Given a Snapshot built twice with identical inputs (including the same
      `as_of`), when the two output files are compared byte-for-byte, then they are identical.

### US-5 (Must): Metric registry mechanism — no real metrics yet

> As the Insights maintainer, I want a versioned registry for pure metric functions, so that
> I2 can add real definitions (TRC-001 etc.) without redesigning how metrics are declared,
> versioned, or looked up.

**Acceptance criteria:**

- [ ] AC-5.1: Given the registry, when a pure function is registered under an id and a
      semantic version, then it can be retrieved by `(id, version)` and listed alongside all
      registered entries in stable (`sort_keys`) order.
- [ ] AC-5.2: Given a registered function, when invoked during a build, then its signature
      exposes only `Fact`s (and `as_of` where declared) — no ambient clock, I/O, or network
      call is reachable from inside it.
- [ ] AC-5.3: Given this feature ships zero real metric definitions, when `insights build`
      runs, then it produces a valid, empty-metrics snapshot; the registry mechanism itself is
      proven by one test-only registered function in the test suite — never shipped as a
      catalog entry or documented as a KPI.

### US-6 (Must): CLI skeleton in the family's C2 idiom

> As the Insights maintainer, I want all five subcommands wired with consistent
> JSON-on-stdout / exit-code behavior, so every future capability slots into an
> already-consistent interface instead of inventing its own conventions.

**Acceptance criteria:**

- [ ] AC-6.1: Given any of `build|query|render|diff|verify`, when invoked with `--help`, then
      usage prints and exit code is 0.
- [ ] AC-6.2: Given `insights build --as-of <date>` against a built graph, when it succeeds,
      then it prints `sort_keys=True` JSON to stdout and writes the sealed snapshot under
      `.aspark-insights/`; against a missing/unbuilt graph it writes a named error to stderr
      and exits 1 — never an unhandled traceback.
- [ ] AC-6.3: Given two stored snapshots, when running `insights diff <a> <b>`, then it
      prints a structural JSON diff of changed facts/provenance fields, exit 0; diffing a
      snapshot against itself yields an empty diff.
- [ ] AC-6.4: Given a stored snapshot, when running `insights verify <snapshot>`, then it
      recomputes the build from the snapshot's own recorded inputs and reports (JSON, exit 0)
      whether the recomputed output byte-matches the stored one, or exits 1 with a named
      mismatch error if it doesn't.
- [ ] AC-6.5: Given no metric catalog and no HTML templates exist in this feature, when
      `insights render` is invoked, then it exits 1 with a named `not_implemented` error
      rather than silently succeeding with empty output; `insights query` MAY instead read
      back raw stored Facts/Provenance from the last snapshot, since that data already exists.

### US-7 (Must): Determinism canary in CI

> As CI, acting on behalf of every future contributor and auditor, I want an automated check
> that building identical inputs twice produces byte-identical output, so a violation of
> "no ambient clock in the derivation path" is caught before it ships — not discovered later
> as a wrong dashboard number.

**Acceptance criteria:**

- [ ] AC-7.1: Given a pinned fixture input (fixed graph state + fixed `as_of`), when CI runs
      `insights build` twice in independent invocations, then the two output files are
      byte-identical; any difference fails the CI job.
- [ ] AC-7.2: Given a deliberately introduced ambient-clock read in a test double (e.g. a
      registered function calling `datetime.now()`), when the canary runs against it, then
      the build detectably fails — the canary itself is tested to catch this regression
      class, not merely proven to pass on a clean checkout.

## 5. Non-Functional Requirements

No `.spark/constitution.md` exists in this repo yet, so no lens profile is active. The NFRs
below are inherited from the family's own architecture conventions (C2 idiom, ADR-4) instead
of a constitution.

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | Reliability / correctness | Identical inputs (incl. `as_of`) ⇒ byte-identical snapshot output, always. | CI determinism canary (US-7) + ad hoc `insights verify` |
| NFR-2 | Architecture boundary | No code outside `ports/graph.py` reads `.aspark-graph/graph.json` or `aspark_graph` internals directly. | CI check + `/peer-review` (AC-2.4) |
| NFR-3 | Interface consistency | Every subcommand's stdout is valid JSON with `sort_keys=True`; every failure exits 1 with a machine-readable named error, never a raw traceback. | Golden-output tests + `/demo-day` |
| NFR-4 | Data-model guardrail | No field or enum value in Fact/MetricValue identifies an individual person as a metric subject. | Schema/type review at `/peer-review` (AC-4.1) |
| NFR-5 | Observability | Every sealed snapshot self-documents enough (`as_of`, versions, graph access mode, `sealed` flag) that a reader can explain a number without re-running the build. | `/demo-day` inspection of a real snapshot |
| NFR-6 | Performance | N/A — no real metric computation exists yet to have a meaningful latency budget; lands with I2+. | — |
| NFR-7 | Accessibility | N/A — no UI surface in this feature (CLI/JSON only); HTML dashboards are I5. | — |
| NFR-8 | Security & privacy | N/A beyond NFR-4 — no PII is ever collected (product non-goal), and no network/auth surface exists in a local CLI yet. | — |

## 6. Out of Scope

- **Real metric definitions** (TRC-\*, FLW-\*, ARC-\*, DBT-\*, MTA-\*) — that's I2 onward;
  this feature ships the registry mechanism with zero catalog entries.
- **Dashboards / HTML rendering** (ADR-5) — I5. `render` ships as a documented, loud stub only.
- **A real PolicyPort resolver adapter** — blocked on aspark-policy P1–P3; stays null.
- **Graph's bulk export contract (G6)** — this feature uses the interim library adapter;
  migrating to `query export` once G6 ships is a future change, not built here.
- **`touches` attribute / phase-duration / flow metrics** — blocked on graph G1/G2; entirely I3.
- **CI snapshot intake / shared team time-series** — I5's multi-developer operation.
- **MCP server** (I7), **fleet / multi-repo aggregation** (I9), **policy-derived compliance
  metrics** (I8) — all later increments, all blocked on named neighbor-repo work.
- **Person-level metrics** — permanently out, not just "later" (non-negotiable design
  constraint, not a scheduling choice).
- **The exact CI platform/workflow file** — a technical "how"; the *requirement* for a
  determinism canary is in scope, its concrete pipeline config is for `/sprint-plan`.

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-07-29 | Do `query`/`render` need real behavior in this feature? | `render` is a loud stub (`not_implemented`) — no templates exist until I5. `query` may serve raw stored Facts/Provenance (that data already exists), but not metric values (none exist). See AC-6.5. |
| C2 | 2026-07-29 | Should the metric registry ship with an example metric? | No catalog/real metric. Only a test-only registered function to exercise the mechanism end-to-end — explicitly not a KPI. See AC-5.3. |
| C3 | 2026-07-29 | Must vs Should for PolicyPort? | Should — cheap and low-risk, but not on I2's critical path (I2 needs GraphPort only). Kept in scope so I2/I3 code doesn't grow ad hoc policy branches before a real seam exists. |
| C4 | 2026-07-29 | Must the interim library adapter be validated against a real installed `aspark-graph`, or is a mock acceptable? | Real, pinned install required for at least one bulk-document read and one CLI query (AC-2.1/2.2) — mocking only would defer the riskiest coupling validation to I2, defeating the point of building the adapter now. |
| C5 | 2026-07-29 | Is `.spark/` visibility part of this feature's scope? | No — repo-governance decision independent of the code; tracked as Q1 (§3), resolved 2026-07-29 by the user: tracked & public. |

## 8. Design Review

N/A for this feature — no UI surface (CLI/JSON only). To be revisited at I5 (`dashboards`).

---

## ✅ SPEC GATE

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone")
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason)
- [x] Clarify pass done: no ambiguity left unresolved or unparked
- [x] Open questions are resolved or explicitly accepted as risk
- [x] Out-of-scope section is filled (something was consciously cut)
- [x] Constitution (`.spark/constitution.md`) respected, or conflicts recorded as open questions — none exists; N/A noted in §5
- [x] Design review done for UI-facing features (or marked N/A with reason)
- [x] Status set to `approved` by the user
