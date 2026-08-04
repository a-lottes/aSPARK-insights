# Spec: snapshot-report

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-04 |

<!-- Deliberately named `snapshot-report`, not "dashboards" — this is the scoped-down slice of
     BACKLOG.md's I5. The full three-persona concept stays reserved under that name for a future
     I5b, pending evidence a second real consumer exists (see §6). -->

## 1. Problem & Goal

- **Problem:** `insights render` has been a loud stub since `foundation` (I1) — it raises
  `NotImplementedStub("insights render is not implemented yet (dashboards land at I5)")`
  (`cli.py:133`). Since `traceability-metrics` (I2) shipped, every `insights build` now produces
  a real snapshot (TRC-001…005/MTA-001…003, honest values or `null`+reason) — but the only way
  to read it is `insights query`'s raw JSON, hand-parsed. `render` is the last of the five
  original C2-idiom subcommands (`build|query|render|diff|verify`) still fake.
- **Goal:** `insights render` writes a real, self-contained, offline-viewable HTML page
  presenting the latest snapshot's facts, metrics (with `n` and honest nulls) and provenance in
  a form a human can skim in a browser — no JSON hand-parsing.
- **Success signal:** `insights render --repo <path>` against a repo with a real built snapshot
  (e.g. aSPARK-graph or aSPARK-policy — I2's own dogfood targets) writes
  `.aspark-insights/report.html`; opened offline in a browser it shows every fact/metric with its
  `n`/reason visible, and no `not_implemented` error remains anywhere in the CLI.
- **Why now:** Backlog-sequenced right after I2, the first feature with anything real to render.
  The user confirmed via `/next-steps` that finishing this stub — scoped down, not the full I5
  three-persona/time-series vision — is the right next slice.

## 2. Target Users

- **Whoever runs `insights render` today** — currently the Insights maintainer, dogfooding this
  tool against aSPARK-graph and aSPARK-policy (I2's own two named dogfood targets). Single
  audience, no role-switching.
- **Not a target:** a second, differentiated Developer/Architect/Engineering-Manager audience
  (I5b, deferred pending evidence it's needed); a CI system assembling multi-snapshot history
  (deferred, §6); any external consumer (none confirmed, mirrors I2's own framing).

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | Snapshot lookup and error taxonomy should reuse what `query` already does. | Confirmed against `store.py`/`query.py`: `render` resolves "the snapshot" exactly the way `query` does (`latest_snapshot_path`, `no_snapshot`/`snapshot_unreadable` reasons) — no second lookup path invented. |
| A2 | Facts today only ever describe Story/AcceptanceCriterion/Task nodes (`metrics/collectors.py:collect_facts`), so the Facts table will often be sparse or empty against a repo without much Story-graph population — exactly what this project's own dogfood fixture (`tests/fixtures/graph.json`) already shows (`facts == []`, every metric `null`+reason). | Inherited from what I2 already computes, not a defect of this feature — reflected in US-3's honest-empty-state requirement, not treated as a bug to fix here. |
| A3 | Should the page ship any interactivity (e.g. expand/collapse), which the constitution's Accessibility bar allows for ("at most")? | No — v1 ships fully static markup, zero interactive elements. Smallest slice that still satisfies "human-skimmable" at current dogfood scale (tens of rows, per I2's own ~132 ACs/16 `verifies` numbers); revisit only if a real legibility problem is observed. |
| A4 | Any open questions left blocking the gate? | No — every ambiguity found in the Clarify pass (§7) was resolved into a story, an NFR, or an Out-of-Scope line. None parked here. |

## 4. User Stories

### US-1 (Must): Render the latest snapshot as one self-contained HTML report

> As whoever runs `insights render`, I want the current snapshot's facts, metrics and
> provenance rendered into one human-skimmable HTML page, so I can review the system's state
> without hand-parsing raw JSON.

**Acceptance criteria:**

- [ ] AC-1.1: Given a repo with at least one snapshot under `.aspark-insights/snapshots/` (found
      the same way `insights query` finds it — latest by filename), when `insights render
      --repo <path>` runs, then it writes one self-contained HTML file to
      `<output-or-repo>/.aspark-insights/report.html`, overwriting any file already there, prints
      `{"report": "<absolute path>"}` (`canonical_json`) to stdout, and exits 0.
- [ ] AC-1.2: Given the same snapshot, the rendered page includes a single `<h1>`, a `<table>`
      of every entry in `facts` (subject_kind, subject_id, predicate, value) and a `<table>` of
      every entry in `metrics` (metric_id, metric_version, value, reason, n) — every row present
      in the snapshot's JSON appears in the rendered tables; none dropped, paginated, or
      truncated away. Rows render in a canonical, deterministic order, never the incidental order
      of the underlying list: facts sorted ascending by `(subject_kind, subject_id, predicate)`;
      metrics sorted ascending by `(metric_id, metric_version)`. All four sort fields are plain
      strings on the model (`SubjectKind.value`/`subject_id`/`predicate` in `model/fact.py`;
      `metric_id`/`metric_version` in `model/value.py`), so this is an ordinary, deterministic
      lexicographic sort — no locale-dependent or custom collation is introduced. This closes
      NFR-5's latent risk directly: byte-identical output requires a provably stable row order,
      not just stable JSON content, and this sort key is that stability guarantee.
- [ ] AC-1.3: Given the same snapshot, the page also presents provenance verbatim: `as_of`,
      `insights_version`, `metric_registry_version`, `graph_source` (access/sealed),
      `scope_filter` (patterns/excluded_count), and `graph_staleness` — never summarized away.
- [ ] AC-1.4: Given `graph_staleness.stale` is `true`, the page marks the report as based on a
      stale graph using **text**, not color alone (e.g. a "STALE" word/label next to the
      staleness data) — a colorblind reader must not need color to see the caveat. This same
      textual stale cue *also* surfaces near the top of the page — after the `<h1>` and the US-5
      summary, before the reader reaches the metrics or facts tables — so the caveat does not
      require scrolling past two full data tables to find (e.g. illustrative only, not
      prescriptive markup: "Report based on a stale graph — see Provenance for details"). The
      top-of-page cue is required *in addition to*, never *instead of*, the provenance-section
      detail already required above; when `graph_staleness.stale == true`, both must be present,
      and both must satisfy the same non-color-only requirement.
- [ ] AC-1.5: Given the rendered file, opening it in a browser with no network connection
      available renders identically to opening it with one — no external font, stylesheet,
      script or image is fetched (ADR-5); all styling is inline or embedded in the one file.
- [ ] AC-1.6: Given a rendered report, its sections appear in this fixed top-to-bottom order in
      the rendered HTML: (1) the `<h1>` and, directly under it, the US-5 summary and — when
      applicable — the AC-1.4 top-of-page stale cue; (2) the staleness/provenance section
      (AC-1.3); (3) the metrics table (AC-1.2); (4) the facts table (AC-1.2). This is checkable
      mechanically: each section's opening tag (or heading, see NFR-4's `<h2>` guidance) appears
      strictly earlier in the file's byte offset than the next section's opening tag — provenance
      before metrics, metrics before facts — so a reader never has to scroll past both data
      tables to reach the report's central trust question ("is this data even current?").

### US-2 (Must): No snapshot yet — a clean named error, not a crash

> As whoever runs `insights render` before ever running `insights build`, I want a clear,
> honest error, so I know what to do next instead of getting a Python traceback.

**Acceptance criteria:**

- [ ] AC-2.1: Given a repo with no `.aspark-insights/snapshots/` directory (or an empty one),
      when `insights render --repo <path>` runs, then it exits 1, prints nothing to stdout, and
      prints a `canonical_json` error on stderr with `"error": "no_snapshot"` — the exact reason
      `insights query` already uses for this case, not a second invented vocabulary.
- [ ] AC-2.2: Given a present-but-corrupt or wrong-shape snapshot file (malformed JSON, or valid
      JSON missing `facts`/`metrics`/`provenance`), when `insights render` runs, then it exits 1
      with `"error": "snapshot_unreadable"` — reusing `query`'s existing validation, never a raw
      traceback.

### US-3 (Must): Every value is presented honestly — `n` beside the value, `null` shows its reason

> As a reader of the report, I want a metric's sample size next to its value and a
> plain-language reason wherever a value is honestly null, so I never mistake a small sample for
> a solid one, or a missing value for a silent gap.

**Acceptance criteria:**

- [ ] AC-3.1: Given a metric with a non-null `value`, the rendered row shows the value together
      with its `n` (e.g. "62% (n=8)") — never the bare value with `n` omitted or relegated
      somewhere a reader could miss it.
- [ ] AC-3.2: Given a metric with `value: null`, the rendered row shows its `reason` text in
      place of the value — never a blank cell, an unexplained dash, or a fabricated placeholder.
- [ ] AC-3.3: Given this project's own dogfood fixture (zero Story/AC/Task nodes — the exact
      case `foundation`'s determinism fixture already exercises, where every metric is `null`
      with a reason), when rendered, every metric row shows its real reason text and the facts
      table shows an explicit "no facts recorded for this snapshot" message rather than an
      empty, unexplained table.

### US-4 (Must): No string from the snapshot can inject markup

> As whoever opens the rendered report in a browser, I want any text drawn from the analyzed
> repo's own content (e.g. a Story's `subject_id`) to appear as literal text, so a repo with
> unusual — even adversarial — `.spark/` content can never execute script or break the page.

**Acceptance criteria:**

- [ ] AC-4.1: Given a snapshot fact whose `subject_id` (or any other string anywhere in
      `facts`/`metrics`/`provenance`) contains HTML-significant characters (e.g. `<`, `>`, `&`,
      `"`), when the page is rendered, then those characters appear HTML-escaped in the output
      file — the literal substring `<script>` never appears unescaped anywhere in the rendered
      HTML, regardless of where in the snapshot it originated.
- [ ] AC-4.2: Given the same hostile input, the page still renders successfully end-to-end (exit
      0) — an adversarial-looking string is escaped, never rejected as a hard error (a hard
      error there would let one repo's content silently disable someone else's report run).

### US-5 (Should): An at-a-glance summary at the top of the page

> As a reader skimming the report, I want a short summary count of facts/metrics right under
> the title, so I can tell the shape of what I'm looking at before reading every row.

**Acceptance criteria:**

- [ ] AC-5.1: Given a rendered report, directly under the `<h1>` a summary line states the count
      of facts and the count of metrics in this snapshot, including how many metrics are `null`
      (e.g. "0 facts, 8 metrics (0 with a computed value, 8 null)").
- [ ] AC-5.2: Given the same summary, its counts always match the actual number of rows rendered
      in the tables below — never out of sync with the facts/metrics tables.

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | Performance | Rendering a snapshot at current dogfood scale (tens of facts/metrics, matching I2's own ~132 ACs/16 `verifies` numbers) completes in well under 5s on a mid-range laptop. | `/demo-day` timing observation |
| NFR-2 | Security — XSS (`security` lens) | Every string value from `facts`/`metrics`/`provenance` is HTML-escaped before being written to the output file (AC-4.1) — this is the project's first HTML-generating feature, and `subject_id` values originate from the analyzed repo's own `.spark/` content via the graph (the same caveat `SECURITY.md`/`mcp-server` spec AC-2.2(4) already names), so this is a real, not theoretical, risk. | `/peer-review` + a targeted test embedding a hostile `subject_id` and asserting the raw tag never appears unescaped |
| NFR-3 | Security — write-path safety (`security` lens) | The HTML output path is fixed (`<output-or-repo>/.aspark-insights/report.html`), never derived from snapshot content or from any flag beyond the already-accepted `--repo`/`--output` — no new path-traversal surface is introduced (no new `--out`-style flag ships, §6). | `/peer-review` |
| NFR-4 | Accessibility (constitution §4, `ux` lens) | Semantic HTML: a single `<h1>`, tabular metric/fact data as real `<table>`/`<th>` (not `<div>` grids). WCAG 2.1 AA contrast (4.5:1 normal text, 3:1 large text/graphics); the stale-graph cue (AC-1.4) carries a non-color cue, never color alone. No ARIA live regions — the page renders once and never updates in place. Self-contained per ADR-5: no external font/CDN/script fetch (AC-1.5). | `/look-and-feel` + `/demo-day` |
| NFR-5 | Reliability / determinism | Rendering the same on-disk snapshot file twice (unchanged bytes in) produces byte-identical HTML output — no embedded wall-clock timestamp, no random id/nonce anywhere in the markup, and row order is the canonical sort defined in AC-1.2 (not incidental list/dict iteration order). | `/demo-day` + a determinism test alongside the existing canary |
| NFR-6 | Observability | N/A — a single, synchronous, file-writing CLI subcommand with no background process; every failure already surfaces via the existing C2 named-error/stderr contract (NFR-9), nothing further to observe. | — |
| NFR-7 | UX — state coverage & responsiveness (`ux` lens) | Empty/honest-null states orient the reader, never show a blank cell (US-3). At a 375px viewport width the page has no horizontal scroll and stays readable. A realistic dogfood-scale snapshot (tens of rows) renders every row without breaking page layout or silently truncating (AC-1.2). | `/look-and-feel` + `/demo-day` |
| NFR-8 | UX — forms & interactivity (`ux` lens) | N/A — the page ships zero interactive elements in this increment (A3): no forms, no expand/collapse, nothing to keyboard-operate, hover/focus, or animate; `prefers-reduced-motion` has nothing to apply to. | — |
| NFR-9 | CLI (`cli` lens) | `render --help` documents the real behavior (reads the latest snapshot via `--repo`/`--output`, writes `report.html`) — no longer "not yet implemented." Exit codes and error shape match `build`/`query`'s established C2 idiom exactly (named-error JSON on stderr, exit 1). | Golden `--help` test + `/demo-day` |
| NFR-10 | Library (`library` lens) | The new render module exposes a minimal, intentional public surface (mirrors `build_snapshot`/`run_query`'s shape) — no incidental helper function leaks as public API. | `/peer-review` (public-surface diff) |

## 6. Out of Scope

- **Multi-snapshot / time-series trend view** (sparklines, historical comparison across
  snapshot dates) — the original I5 backlog concept. Makes no sense for a single-point-in-time
  render and needs more than one real dogfood snapshot to justify honestly; deferred to a future
  increment once that evidence exists.
- **The MTA-001 "suppress trendlines under the n-threshold" idea, as originally phrased** —
  doesn't apply to a single-snapshot render, since there's no trend to suppress in the first
  place. Its honest single-snapshot equivalent is US-3: `n` always travels visibly next to its
  value; no trend/sparkline element is attempted anywhere on this page.
- **Three-persona role-switching** (Developer/Architect/Engineering-Manager views) — deferred to
  a future I5b, pending evidence a second real consumer exists.
- **CI workflow templates for multi-developer snapshot time-series assembly** (original I5's
  "Multi-Developer-Betrieb") — solves a problem this single-maintainer project doesn't have yet.
- **Any interactive JS** (expand/collapse, sort, filter, search) — fully static in this
  increment (A3); revisit only if a real legibility problem with static tables is observed.
- **A configurable `--out` path for the HTML file**, separate from `--repo`/`--output` — always
  writes to the fixed default path, mirroring the established `--repo`/`--output` convention
  rather than adding a third path flag.
- **Rendering an arbitrary/older snapshot by date** — always renders the latest, same as `query`.
- **Threshold enforcement / pass-fail gating** on any metric shown — `aspark-ci`'s job, never
  Insights' (constitution §3, repeated non-negotiable).
- **Person-level metrics** — permanently out (constitution §6).

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-04 | Single snapshot, or the original backlog's multi-snapshot time series? | Single-snapshot-only — renders whatever `latest_snapshot_path` resolves to, no history. A time-series view needs multiple real snapshots to be honest about, which doesn't exist yet for this single-maintainer project. See §6. |
| C2 | 2026-08-04 | Where does the HTML get written — stdout, `.aspark-insights/`, or a new `--out` flag? | `<output-or-repo>/.aspark-insights/report.html`, mirroring how `build` writes derived state under the existing `--repo`/`--output` convention (project CLAUDE.md's own "`--output` from day one" pattern) — no new flag invented (AC-1.1, §6). |
| C3 | 2026-08-04 | What happens with no snapshot built yet? | The same named errors `query` already raises (`no_snapshot`/`snapshot_unreadable`), never a crash (US-2) — no second error vocabulary. |
| C4 | 2026-08-04 | Does "renderer refuses trendlines under the n-threshold" (MTA-001) apply to a single-snapshot render? | No — resolved as out of scope; see the dedicated Out-of-Scope line above. Its honest equivalent here is always showing `n` beside the value (US-3). |
| C5 | 2026-08-04 | Should XSS/escaping be a concrete AC, not just a mention? | Yes — US-4/NFR-2. This is the project's first HTML-generating feature, and `subject_id` values are sourced from the analyzed repo's own content via the graph, so this is real risk, not a theoretical one. |
| C6 | 2026-08-04 | `/look-and-feel`'s design review flagged three testable structural gaps as needing a spec amendment rather than `/increment`'s judgment (findings 1, 2, 3 — see §8): no stated sort order for the facts/metrics tables, no stated page-section order, and an underspecified stale-cue prominence. Should these become concrete ACs? | Yes, per user approval. Finding 1 → AC-1.2 amended with a canonical sort (`(subject_kind, subject_id, predicate)` for facts, `(metric_id, metric_version)` for metrics; both confirmed as plain-string fields against `model/fact.py`/`model/value.py`), cross-referenced to NFR-5's determinism guarantee. Finding 2 → new AC-1.6 states the fixed top-to-bottom section order (summary/stale-cue → provenance → metrics → facts), checkable by section-tag byte offset in the rendered file. Finding 3 → AC-1.4 amended to require the textual stale cue to also surface near the top of the page (under `<h1>`/summary), in addition to — not instead of — the existing provenance-table detail; the example notice string is marked illustrative, not prescriptive markup, matching the pattern already used for AC-5.1. Findings 4–6 and the two accessibility notes were deliberately left out of this amendment — the design review itself judged them safe for `/increment` to apply directly inside existing AC/NFR wording, and that split is not reopened here. |

## 8. Design Review

<!-- Filled by /look-and-feel. Empty design review = gate stays red for UI-facing features. -->

- **Overall impression:** The scope is right-sized and the underlying instincts are sound —
  static/offline/no-JS (ADR-5), escaping every string (US-4), and reusing `query`'s error
  vocabulary (US-2) are all correct calls for a single-audience report, and none of the findings
  below reopen the already-settled scope cuts (interactivity, multi-snapshot, personas). But the
  spec currently under-specifies several concrete presentation decisions that its own success
  signal ("human-skimmable") and its own trust guarantee (honest nulls, staleness) depend on:
  no stated row order for the two data tables, no stated page-section order, no stated
  prominence for the stale-graph cue, no visual distinction between a real value and a null's
  reason, and thin design direction for the empty/near-empty state that is, in practice, the
  *first real screen* most runs of this tool will show (this project's own dogfood fixture is
  zero facts / all-null metrics). Genuinely greenfield: no existing HTML/CSS artifact exists
  anywhere in this repo (`docs/` is Markdown only) or in the sibling `aspark-graph` checkout on
  disk, so there is no established visual language to match or break — every finding below is
  argued from the spec's own stated goals, not from an inherited house style.

- **Heuristics findings:**

  1. **[Major] No stated sort order for the facts/metrics tables.** Location: AC-1.2, AC-1.3.
     Rule: Recognition over recall / minimalism — the spec's own success signal is
     "human-skimmable," but at dogfood scale (I2's own ~132 ACs / 16 `verifies` / tens of
     metrics) an *unsorted* flat table is not skimmable; a reader has to scan every row to find
     one. AC-1.2/1.3 only require "every entry... appears," leaving row order to whatever the
     underlying list's iteration order happens to be — which is also a latent risk to NFR-5's
     byte-identical-output guarantee if that order isn't already provably stable input-to-input.
     Fix: state a canonical sort directly in the AC text — e.g. facts sorted by
     `(subject_kind, subject_id, predicate)`, metrics sorted by `(metric_id, metric_version)`.
     This changes testable AC behavior, so it should go back through `/story-time` as an AC
     amendment rather than being left to `/increment`'s judgment.

  2. **[Major] No stated page-section order; stale/provenance risks landing below the fold.**
     Location: AC-1.2, AC-1.3, §1 Goal. Rule: Visibility of status — the spec never states
     whether facts, metrics, or provenance/staleness renders first. Given the report's central
     trust question is "is this data even current?" (`graph_staleness`, AC-1.4), a reader
     scrolling past two full tables before reaching that answer is backwards. Fix: state page
     order explicitly (e.g. summary → staleness/provenance → metrics → facts, or justify a
     different order), and treat the stale cue as part of that early block, not only a cell
     inside a provenance table further down. Ties directly to finding 3. Route to `/story-time`
     — this is a testable structural decision, not a rendering nuance.

  3. **[Major] AC-1.4's stale-graph cue is underspecified for prominence.** Location: AC-1.4.
     Rule: Visibility of status — "next to the staleness data" is satisfied by a single word
     buried in a provenance-table cell, which is easy to miss on a page whose visual bulk is two
     large data tables, even though staleness materially changes how much to trust everything
     else on the page. Fix: require the cue to also surface without scrolling into the
     provenance section when `graph_staleness.stale == true` — e.g. a labelled notice directly
     under the `<h1>`/summary ("Report based on a stale graph — see Provenance for details"),
     in addition to (not instead of) the provenance-table detail. Route to `/story-time` — this
     adds a testable placement requirement AC-1.4 doesn't currently state.

  4. **[Major] No visual distinction between a real value and a null's reason.** Location:
     AC-3.2 (compare AC-3.1). Rule: Recognition over recall / error prevention — AC-3.1 requires
     values to render as e.g. `62% (n=8)`; AC-3.2 requires nulls to render "reason text in place
     of the value," but nothing distinguishes the *shape* of those two cell contents from each
     other. A terse reason string can look enough like a value at a skim that a reader misreads
     it — the exact failure this product exists to prevent (constitution §1: an honest null is
     the product, not the gap). Fix: give null rows a fixed, non-color-only visual marker — e.g.
     italic text prefixed with a constant label, `Not computed: <reason>` — so the cell's shape,
     not just its color, signals "this is an explanation." This fits inside AC-3.2's existing
     wording ("shows its reason text") — `/increment` can apply it without a spec change, but it
     should not be left to arbitrary per-row styling, hence flagged explicitly here.

  5. **[Major] US-5's summary line is a dense sentence, not an at-a-glance shape.** Location:
     US-5, AC-5.1. Rule: Minimalism / hierarchy — US-5's stated purpose is "tell the shape of
     what I'm looking at before reading every row," but AC-5.1's example
     ("0 facts, 8 metrics (0 with a computed value, 8 null)") is one dense sentence with a
     nested parenthetical — the opposite of glanceable. Fix: present the same three counts
     (facts / metrics total / metrics null) as visually distinct figures — e.g. a short
     label:value list — not prose. This doesn't change what AC-5.1 requires (the counts
     themselves), only how they're presented, so `/increment` can apply it without new scope;
     recommend AC-5.1's example string be marked "illustrative content, not prescriptive
     markup" so it isn't read as mandating one literal sentence.

  6. **[Major] AC-3.3's empty/near-empty state is under-designed for what is, in practice, the
     primary first-run screen.** Location: AC-3.3 (see also A2). Rule: Visibility of status /
     error prevention — this project's own dogfood fixture produces zero facts and all-null
     metrics, so this is not a rare edge case, it is very likely the *first* screen anyone
     actually sees. "An explicit... message" is correct in principle but thin as design
     direction: a bare one-line caption sitting inside an otherwise visually empty table can
     read as "the tool is broken," not "the tool worked and confirmed there is nothing here yet"
     — exactly the distinction the constitution's central trust guarantee depends on. Fix: treat
     this as a primary state to design for, not an incidental AC — e.g. a clearly-styled notice
     block (not bare inline text) explaining what a zero-facts / all-null-metrics report means,
     using the same non-color textual-treatment principle already required for AC-1.4. Fits
     inside AC-3.3's existing wording; `/increment` can apply it as design guidance, but flag it
     as priority, not afterthought.

- **Accessibility notes:**

  - **[Major] NFR-4 promises a "coherent nested heading hierarchy" that no AC actually
    requires.** Location: NFR-4 vs. AC-1.2/AC-1.3/US-5. Rule: constitution §4 Accessibility bar
    (semantic HTML, heading hierarchy). No AC currently establishes section headings between
    the summary and the tables. Fix: require an `<h2>` before each of the Facts table, Metrics
    table, and Provenance section (e.g. "Facts", "Metrics", "Provenance") so NFR-4's promise is
    actually testable, and so a screen-reader user can navigate the page by heading rather than
    reading it linearly. This fills in NFR-4's existing intent rather than adding new scope —
    `/increment` can apply it directly.
  - **[Major] Table header semantics are unspecified beyond "real `<table>`/`<th>`."** Location:
    NFR-4. Rule: constitution §4 Accessibility bar. Without `<th scope="col">` (and a
    `<caption>` or `aria-labelledby` tying each table to its heading), a screen reader in
    table-navigation mode cannot reliably announce which column a cell belongs to across a
    many-row table — a real risk at "tens of rows" dogfood scale (NFR-1/NFR-7), not a
    theoretical one. Fix: `/increment` uses `<th scope="col">` on every header row and a
    `<caption>` (or equivalent `aria-labelledby`) per table; no AC change needed, this sits
     inside NFR-4's existing "real `<table>`/`<th>`" requirement.
  - Contrast requirements for the non-color cues (AC-1.4's stale label, the fix in finding 4
    above) are already covered generically by NFR-4's stated WCAG AA figures (4.5:1 / 3:1) —
    no additional finding needed there, just confirming it isn't a gap.

- **Design risks & required changes:**

  - **Route to `/story-time` before gate (testable-behavior gaps, not visual polish):**
    findings 1 (facts/metrics sort order), 2 (page-section order) and 3 (stale-cue prominence)
    all add or change testable AC behavior that the current spec is silent on. Leaving them
    unresolved means two different implementers of AC-1.2/1.3/1.4 could reasonably build
    differently-ordered, differently-prominent pages that both technically pass the letter of
    the current ACs — which is exactly the ambiguity the Clarify pass (§7) is supposed to have
    closed. Recommend one more `/story-time` pass adding: (a) an explicit sort order for both
    tables, (b) an explicit page-section order, (c) an explicit "stale cue visible above the
    provenance section when `graph_staleness.stale == true`" requirement.
  - **Safe for `/increment` to apply directly as design guidance, no spec change needed:**
    findings 4 (null-vs-value visual distinction), 5 (summary as distinct figures, not prose),
    6 (empty-state notice treatment), and both accessibility notes (heading hierarchy, table
    header semantics) — all fit inside existing AC/NFR wording and don't add new testable
    behavior beyond what's already promised.
  - No finding above requires new features or reopens the confirmed scope cuts (zero
    interactivity, single snapshot, single audience) — everything is a presentation/structure
    gap inside the already-agreed scope.

---

## ✅ SPEC GATE

*All boxes checked → `/sprint-plan` may start. Any box open → back to `/story-time` or `/look-and-feel`.*

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone")
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason)
- [x] Clarify pass done: no ambiguity left unresolved or unparked
- [x] Open questions are resolved or explicitly accepted as risk
- [x] Out-of-scope section is filled (something was consciously cut)
- [x] Constitution (`.spark/constitution.md`) respected, or conflicts recorded as open questions
- [x] Design review done for UI-facing features (or marked N/A with reason) — findings 1/2/3
      folded into AC-1.2/AC-1.4/AC-1.6 above (§7 C6); findings 4–6 and both accessibility notes
      remain `/increment` guidance per the design review's own routing.
- [x] Status set to `approved` by the user
