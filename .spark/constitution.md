# Constitution: aspark-insights

| | |
|---|---|
| **Scope** | Project-wide — binds every SPARK phase and every feature |
| **Owner** | The user (amended via `/charter`) |
| **Status** | `active` |
| **Date** | 2026-07-31 |

<!-- First draft, written after the `foundation` (I1) increment shipped (v0.1.0, commit 86b2beb).
     Grounded in: CLAUDE.md, .spark/BACKLOG.md, .spark/foundation/{spec,review,qa,release}.md,
     pyproject.toml, docs/ARCHITECTURE-PROPOSAL.md, docs/CROSS-REPO-PLAN.md. Entries marked
     "OPEN QUESTION" are flagged for the user rather than decided by the Facilitator. -->

## 1. Product Principles

- **Evidence over completeness.** An honest `value: null` with a mandatory, non-empty
  `reason` beats a fabricated or approximated number — this is the product's central trust
  guarantee, not an edge case. Structurally enforced: `MetricValue` cannot construct a null
  without a reason (foundation AC-4.2); precedent is MTTR staying `null` rather than invented
  (BACKLOG.md §1, "G2").
- **Don't recompute what the graph already answers.** `aspark-graph` is the fact-query source
  of truth (`dora`, `gate_health`, `staleness`, …); Insights' job is versioned metric
  definitions, time series over snapshots, joins and dashboards on top of those facts — never
  a second implementation of the same query (ADR-0). This is the scoping tie-breaker whenever
  a new metric idea looks like "just recompute X locally": wrap and add provenance, don't
  duplicate (`docs/ARCHITECTURE-PROPOSAL.md` line 220).
- **Reproducibility over convenience.** Given identical inputs (including `as_of`), a snapshot
  build is byte-identical, every time. No feature ships that reads the wall clock or any other
  ambient state from inside the derivation path (ADR-4) — checked automatically by a CI
  determinism canary, not just asserted.

## 2. Project Profile & Active Lenses

- **Project type(s):** `cli` + `library`.
  - `cli` — evidence: `[project.scripts] insights = "aspark_insights.cli:main"`
    (`pyproject.toml`), stdlib `argparse`, five subcommands (`build|query|render|diff|verify`)
    in the family's C2 idiom (JSON on stdout, `sort_keys=True`, exit 1 + named error). No web
    surface exists (foundation spec NFR-7/NFR-8 explicitly marked N/A — "no UI surface").
  - `library` — evidence: installable package under `src/aspark_insights` with `hatchling` as
    the wheel build backend, no server/bind port; the *pattern* it exists to serve is
    consumed-as-a-dependency (mirrors how `aspark-graph` is itself consumed here as a
    version-pinned library dependency, and how a future `aspark-ci` is expected to consume
    Insights' JSON per BACKLOG.md §4). No external importer exists yet today, but the user
    confirmed (2026-07-31) including it now rather than waiting — the package is already built
    to be imported, and the family consumption pattern is clear enough to plan for.
- **Characteristics:** none of `handles-auth`, `is-public`, `handles-payments`, or
  `has-database` apply — no auth/network surface exists (local CLI only, foundation NFR-8),
  and derived state is JSON snapshot files under `.aspark-insights/`, not a database.
  `is-multilingual` does not apply (no locale surface).
  - **`handles-pii` — confirmed off (2026-07-31).** The project's own non-negotiable ("never
    person-level metrics — measure systems/features/code, never individuals," BACKLOG.md §4)
    is a *stronger* commitment than generic PII handling: it's not "handle PII carefully," it's
    "structurally cannot ingest person-level data at all" (enforced by the Fact model's
    subject-kind enum, AC-4.1). The user decided the Non-Negotiable already covers this more
    precisely than the generic PII checklist would.
- **Active lenses:**

| Lens | Why it's active (or off) | Enforced in |
|---|---|---|
| `cli` | active — type `cli`; help/discoverability, stdout/stderr hygiene, exit codes are already load-bearing conventions here (C2 idiom, NFR-3) | `/story-time`, `/peer-review`, `/demo-day` |
| `library` | active — type `library`, confirmed by the user (2026-07-31) despite no external importer yet; public API surface, semver/deprecation discipline matter once any package (family or external) depends on `aspark_insights` directly | `/story-time`, `/peer-review` |
| `security` | active — confirmed by the user (2026-07-31), proposed rather than mechanically derived. No characteristic in the standard trigger list (`handles-auth`/`is-public`/`handles-payments`/`handles-pii`) formally fires this for a local, no-network CLI. Grounded in real evidence: foundation's QA found a genuine Blocker path-traversal/arbitrary-file-write bug via an unvalidated `--as-of` (B5), plus two raw-traceback-leak bugs (B2, F1/F5) on malformed input. "Validate any input that becomes a filesystem path" and "never a raw traceback" are now proven-necessary disciplines, not speculative ones, even absent a network surface. | `/story-time`, `/peer-review`, `/demo-day` |
| `ux` | active — confirmed 2026-08-03, proposed rather than mechanically derived (same pattern as `security` above). Trigger: `/story-time` is about to open for a scoped-down version of I5 `dashboards` (BACKLOG.md §3) — a single-audience static HTML report (whoever runs `insights render`, no role-switching) rendering the current snapshot (facts/metrics/provenance), built to ADR-5 (offline-first, air-gap, no second toolchain), with no server and at most expand/collapse interactivity. The original backlog's three-persona framing (Developer/Architect/Engineering Manager role-differentiated views) is explicitly deferred to a future I5b, pending evidence a second consumer actually exists — out of scope for this feature. Evaluated against the `web-app` type signal (SPA framework, routes, auth, app-like tool UI) and it doesn't match — no framework, no routing, no auth surface — so the project type stays `cli` + `library`, unchanged; `ux` activates on its own narrower grounds instead of relabeling the project. The concern is real regardless: a data-dense report, even for one audience, has genuine information-hierarchy, legibility and (for any interactive element) keyboard-operability requirements from the day this page ships. | `/story-time`, `/peer-review`, `/demo-day` |
| `seo` / `api` / `i18n` / `data` | off — no website/web-app/api surface, no locale surface, no database (JSON snapshot files, not a DB) | — |

- **Active-lens load:** 4 lenses active (`cli`, `library`, `security`, `ux`) — crossed the 4+
  threshold as of the `ux` activation (2026-08-03). **Elevated-load flag: set.** Every phase
  should scrutinize this stack rather than skim it — the flag is visibility, not a cap.

## 3. Technical Constraints

- **Stack / runtime:** Python ≥3.11, `uv` + `hatchling`, stdlib `argparse`, `pytest`. A
  version-**pinned-exact** (not ranged) `uv` path dependency on the sibling `aspark-graph`
  (currently `==0.7.0`) — the interim library adapter imports its internals directly, so even
  a patch bump could change shape underneath it (pyproject.toml comment, ADR-1). No new
  language or build backend without an amendment.
- **Patterns to follow:**
  - **Named-error taxonomy + one canonical serializer.** Every CLI failure raises an
    `InsightsError` subclass carrying a machine-readable `reason` (`errors.py`); every
    stdout/stderr JSON payload goes through `canonical_json()` (`serialization.py`,
    `sort_keys=True`). No ad hoc `print()`/`raise`.
  - **C2 idiom on every subcommand:** JSON on stdout (`sort_keys=True`), exit 1 with a named
    error on failure, never a raw traceback — this exact guarantee was the subject of three
    real bugs in `foundation` (B2, F1, F5) and must not regress.
  - **`GraphPort` is the only seam to `aspark-graph`.** Nothing outside `ports/graph.py` reads
    `.aspark-graph/graph.json` or imports `aspark_graph` internals directly (AC-2.4, checked
    in CI and at `/peer-review`). The interim library adapter has a documented sunset
    condition — it retires once graph's `G6 export` ships (ADR-1); `graph_source.access`
    stays visible in every snapshot's provenance until then.
  - **No second git parser.** Time is the graph's fact to state (Release/Commit nodes via
    G1/G2); only the documented interim git-adapter fallback is permitted if `touches` is
    rejected upstream (ADR-2).
  - **`--output` from day one.** Any CLI subcommand that reads from `--repo X` and also writes
    derived state ships a separate `--output` flag, and documents the write-location behavior
    directly in `--help` text — defaulting to writing under `--repo` is fine, but must be an
    explicit, escapable, documented default (per B1's resolution).
  - **Never mock the sibling `aspark-graph` dependency in integration tests.** Require a real,
    pinned, installed sibling repo (this is what let QA find B2/B5 — a mock would have hidden
    both).
- **Off-limits:**
  - No `datetime.now()` (or any other ambient-clock/non-deterministic read) anywhere in the
    derivation path; `as_of` is always an explicit input, recorded in provenance (ADR-4).
  - No shared `aspark-common` coupling-smuggling library across the family — already decided
    against by the family (BACKLOG.md §4, P5); the export contract (graph's G6) replaces the
    need.
  - No LLM in the derivation path — metrics are pure functions; agents read results via a
    future read-only MCP server, but no KPI is ever model-generated (BACKLOG.md §4, "P1").
  - No threshold enforcement in this repo — Insights measures, `aspark-ci` (consuming
    Insights' JSON) enforces gates (BACKLOG.md §4).

## 4. Quality Bars (Definition of Done defaults)

- **Testing:** every Must story has an automated test; additionally, per the `foundation`
  retro, every finding a reviewer/QA closes is **re-verified by re-running the exact original
  repro**, not just by a new passing test — a green suite alone was not treated as sufficient
  evidence in this project's own precedent (`release.md` §6).
- **Accessibility:** activated 2026-08-03 alongside the `ux` lens, grounded in what I5's actual
  deliverable is (BACKLOG.md §3: one self-contained static HTML page, ADR-5 offline-first/
  air-gap, no server, at most expand/collapse interactivity) — not a generic "WCAG 2.1 AA"
  copy-paste sized for a full interactive web app:
  - Semantic HTML: a single `<h1>`, a coherent nested heading hierarchy, tabular metric data
    marked up with real `<table>`/`<th>` elements (not `<div>` grids) — checkable by inspecting
    the rendered HTML, not just the generator source.
  - Color contrast: all text and any status/health indicator meet WCAG 2.1 AA contrast (4.5:1
    normal text, 3:1 large text/graphics); any color-coded status (e.g. red/green health) also
    carries a non-color cue (icon or text label) — color is never the only signal.
  - Keyboard-operable: any interactive element the page ships (e.g. expand/collapse sections) is
    reachable and operable via keyboard alone (Tab/Enter/Space); no mouse-only interaction.
  - Deliberately out of scope: ARIA live regions and other dynamic-update affordances — the page
    renders once from a snapshot and never updates in place, so there is nothing to announce.
  - Self-contained per ADR-5: no external font/CDN/script fetch — the page renders fully offline,
    so assistive-tech behavior never depends on a network call succeeding.
- **Performance:** N/A for now — no real metric computation exists yet to set a meaningful
  latency budget (mirrors foundation's own NFR-6, marked N/A for the same reason). **OPEN
  QUESTION:** once I2 (`traceability-metrics`) ships real computation, a number should be set
  here rather than left N/A indefinitely — flagging so it isn't silently forgotten, not
  inventing one now.
- **Security:** grounded directly in foundation's QA findings —
  - Any value that becomes a filesystem path or gets parsed into another system's data
    structure (`--as-of`, snapshot filenames, `--repo`/`--output`) is validated against a
    hostile-input checklist before use: empty string, path-traversal sequences (`../`), an
    absolute path, a wrong-but-valid-JSON shape (list/string/null/number instead of the
    expected dict), and a dict missing expected keys (per B5, and the CLAUDE.md nudge it
    produced).
  - No raw traceback ever reaches stdout/stderr on any input — every failure path is caught
    and wrapped in a named error (per B2/F1/F5; this is also NFR-3).
  - No PII/person-level data is ever collected, computed on, or logged (see §6
    Non-Negotiables) — this is the project's strongest privacy guarantee, stronger than
    generic "PII handled carefully."

## 5. Conventions

- **Naming / structure:** `src/aspark_insights` package layout with `ports/` (GraphPort,
  PolicyPort), `model/` (Fact, Snapshot, Provenance, MetricValue), `metrics/` (versioned
  registry) and `cli.py` submodules; CLI entrypoint is `insights` via `project.scripts`.
- **Commits / branches:** Conventional-Commits-style subject lines (e.g. `feat: foundation —
  …`), as used in the one commit so far. No branch-naming convention is established yet beyond
  the initial `main`-only history — **OPEN, not yet decided**; not blocking, since nothing has
  branched yet.
- **Language:** all artifacts — code, specs, `.spark/*`, commit messages, comments — in
  English regardless of chat language.
- **Git identity before `/go-live`.** For a from-scratch, not-yet-`git init`-ed repo (or any
  new clone without local identity configured), confirm `user.name`/`user.email` *before* the
  first `/go-live` pass, not at the release ceremony itself — learned from `foundation`'s
  workaround via env-var-scoped `GIT_AUTHOR_*`/`GIT_COMMITTER_*` variables.

## 6. Non-Negotiables

- **Never person-level metrics.** Only systems, features, and code-artifacts are measured;
  no `Fact`/`MetricValue` subject kind ever identifies an individual person (e.g. commit
  author, assignee). This is a structural design constraint (enforced by the Fact model's
  subject-kind enum, AC-4.1/NFR-4), not a setting — it "destroys the trust the evidence rests
  on" if violated (BACKLOG.md §4, near-verbatim).
- **Never invent a number.** When a metric cannot be honestly computed, the model represents
  it as `value: null` together with a mandatory, non-empty `reason` — a null without a reason
  is not constructible (AC-4.2). An honest `null` with a reason **is** the product, not the
  gap (BACKLOG.md §4, "G2" precedent, near-verbatim).
- **Never a raw traceback.** Every CLI failure exits 1 with a machine-readable named error on
  stderr; three real bugs (B2, F1, F5) already regressed this once in `foundation` and it must
  never regress again silently.

---

## Amendments

| Date | Change | Why |
|---|---|---|
| 2026-07-31 | Initial constitution | First `/charter` pass, run after the `foundation` (I1) increment released (v0.1.0). Grounds every section in what the shipped code, `.spark/BACKLOG.md`'s ADRs, and `foundation`'s spec/review/QA/release reports already demonstrate — no aspirational entries invented ahead of evidence. User confirmed all three flagged open questions in the same session: `security` lens active despite no network surface (grounded in real B5/B2/F1/F5 findings); `handles-pii` left off (the "never person-level metrics" Non-Negotiable already covers this more precisely); `library` type included now despite no external importer yet. |
| 2026-08-03 | Activated `ux` lens (§2); replaced the Accessibility quality bar's `N/A` with a real, falsifiable bar (§4) | Triggered by `/story-time` about to open for a scoped-down version of I5 `dashboards` (BACKLOG.md §3: a single-audience static HTML report — whoever runs `insights render`, no role-switching — rendering the current snapshot, built to ADR-5 offline-first/air-gap, no server, no second toolchain; the backlog's original three-persona Developer/Architect/Engineering-Manager framing is deferred to a future I5b pending evidence a second consumer exists) — the constitution's own §4 had already flagged this exact moment as "revisit explicitly once I5 ships." Evaluated whether this deliverable meets the `web-app` type signal (SPA framework, routes, auth, app-like tool UI) and decided it doesn't — no framework, no routing, no auth surface — so the project type stays `cli` + `library`, unchanged; `ux` instead activates on its own narrower grounds, mirroring the `security` lens's precedent (proposed rather than mechanically derived, grounded in concrete evidence rather than a formally-firing type/characteristic trigger). Active-lens load crosses to 4 (`cli`, `library`, `security`, `ux`) — elevated-load flag now set. No other section touched: the standing performance-budget open question in §4 is untouched by this amendment. |
