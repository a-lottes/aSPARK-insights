# Spec: release-metrics

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-24 |
| **Ticket** | none |

<!-- Handoff: read this block first, the numbered sections below by exception. -->

**Handoff**
- **Status:** `approved` (2026-08-24, user approval in conversation). All clarify-pass and design
  findings folded into ACs/NFRs below; §8 is Designer-owned and left untouched. Ready for
  `/sprint-plan` (already run — see `plan.md`, `approved`) and `/increment`.
- **Summary:** The shipped release board (v0.10.0) is a complete *evidence* artifact but has no
  time axis: not one real tagged release shows **when** it happened, how long it took, or how much
  scope it actually delivered. This feature adds measured release figures (date, cadence gap,
  commits, work-type mix, scope) plus an attribution rule that stops double-counting a feature in
  every release its directory was touched in.
- **Resolved earlier passes:** A1 — the user chose the **local parser**: US/AC scope counts are read
  directly from each feature's own `spec.md` (the same file `artifactstatus.py` already opens for
  its status field), never the sibling graph; `gitboard` stays fully graph-free, and AC-3.6 states
  the missing/unparseable-spec failure mode. A2 — not a real discrepancy: the caller's original
  brief under-stated the active-lens set; `.spark/constitution.md` §2's four lenses
  (`cli`/`library`/`security`/`ux`) were already correctly targeted in this spec's §5
  (NFR-3/NFR-4) and need no change.
- **Folded this pass (§8 findings 1-4; finding 5 parked for `/sprint-plan` per §8, no spec change):**
  AC-2.7 states the explanatory note a trailing member's document must carry (finding 1); AC-3.7
  collapses the cadence strip's small-sample behavior to exactly two states — present-raw or
  absent-with-reason, never a partial state (finding 2); NFR-5 now states cadence-strip segments
  carry one uniform hue regardless of value, extending `release-board-html`'s
  badge-hue-never-by-status precedent (finding 3 — flagged constitutionally sharp because the
  feature's own originating mockup used a warning hue for this exact bar); NFR-4 now states the
  figures band wraps to a multi-row grid at 375px, matching `release-board-docs/qa.md` B1's mobile
  precedent (finding 4).
- **Binding ruling:** §4 User Stories for what's committed; §3 for what isn't; §7 for what the PO
  resolved without escalating; §6 for what was cut — including the health/RAG verdict this
  feature is repeatedly tempted toward and constitutionally may not ship.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch at
  the next `/peer-review` and proceed.

## 1. Problem & Goal

- **Problem:** `release-board-docs` (v0.10.0) closed the *evidence* gap — every release, its member
  features, their 5-artifact status, and now their full document bodies are one file away. It did
  not close the *steering* gap. Measured against this repo today: **no real tagged release carries
  a date at all.** `build_release_map()` emits `tag`/`previous_tag`/`next_tag`/`members`/
  `unattributed` per real tag and nothing else; only the open pseudo-release has any time figure
  (`days_since_tag`, `commits`, `work_types`, reused verbatim from `build_board()` per
  release-board's AC-1.8). The date is sitting in git, one command away and unread
  (`git log -1 --format=%cs v0.5.0` → `2026-08-10`). Second, measured: **naive per-release scope
  counting roughly doubles everything** — 8 of this repo's 10 features appear in exactly two
  releases, once via their `feat:` commit and once via the trailing `docs: record … release report`
  commit, so v0.3.0 reads as 14 US / 42 ACs against a real 7 US / 24 ACs (2.0×), v0.5.0 as 11/48
  against 6/33 (1.5×), v0.9.0 as 6/29 against 3/13 (2.2×).
- **Goal:** Give each release a measured time and size, and one stated attribution rule, so the
  board answers "when, how long, how much" — not just "what exists". Every figure is a measured
  number with its own denominator, or an honest `null` with a reason. No figure is a verdict.
- **Success signal:** Rendered against this repo today, `v0.6.0` reads as: **0 delivering features,
  1 trailing member (`measurement-honesty`, delivered in v0.5.0), an 8-day gap — the longest in the
  project against a 2-day median — and 1 unattributed commit** (`26e7f95 feat: snapshot-report
  scorecard redesign`, which touched `src/` but not `.spark/snapshot-report/`, so path attribution
  correctly declines to claim it). Today, the release that looks emptiest by member count is
  invisible; after this ships it is legible as the slowest window in the project's history, and
  only the *combination* of date, gap, delivering-vs-trailing scope and unattributed count makes it
  so. Second signal: v0.9.0's detail card states 3 US / 13 ACs (`release-board-html`'s real
  content), not 6 / 29.
- **Why now:** Nothing breaks if this is never built — the board is correct today, and the
  double-counting only misleads someone who counts by hand, which nobody currently does. What
  weighs for it: the underlying data is already read or one cheap git call away (ADR-0 respected —
  this reads what exists, it does not re-derive membership, status, or commit ranges), and the
  attribution defect is a *correctness* bug the moment anyone puts a scope number on the page, so
  it is cheaper to fix before US-3/US-4 print one than after. What it displaces: `release-board`'s
  still-open A3 ("why" extraction from Clarifications/ADR prose) — a real, still-deferred
  alternative, named honestly rather than pretended away.

## 2. Target Users

- **The maintainer steering the next cycle (concrete: Andreas)** — the same reader every prior
  release-board surface names, but in a different act: not "reconstruct what happened" (solved) but
  "decide what to do next", which needs a time axis the board has never had.
- **A future `aspark-ci` consumer (named, not built)** — this feature's JSON is the shape a gate
  would read. It stays measurement only; the gate lives there (constitution §3), never here.

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | **Scope-count source — RESOLVED by the user (was gating a Must).** US-3/US-4 print US and AC counts per release. Two candidate sources existed and conflicted on principle: (a) the sibling `aspark-graph`, the constitution's declared fact-query source of truth (ADR-0), vs. (b) a local parse, since the whole `gitboard` package is deliberately graph-free and standalone (`board.py`'s own docstring, `releasemap.py`'s "imports no sibling graph tool's port or library"). | **The local parser.** US/AC scope counts are read directly from each feature's own `spec.md` — `### US-N` headings counted for US, `- [ ] AC-`/`- [x] AC-` lines counted for ACs — the same file `artifactstatus.py` already opens for its status field, just a different extraction over the same source. `gitboard` stays fully graph-free: no `GraphPort` dependency is added, consistent with `releasemap.py`'s own docstring and this project's three-feature-old, structurally tested principle ("imports no sibling graph tool's port or library"). AC-3.6 states the missing/unparseable-spec failure mode: `null` with a named reason, never an estimate, never a silent zero. Whether the extraction lands as a new function in an existing `gitboard` module (e.g. beside `artifactstatus.py`) or a new sibling module is `/sprint-plan`'s call, not this spec's — this spec states the source and the failure behavior only, never the implementation shape. |
| A2 | **Active-lens set — RESOLVED; not a real discrepancy, an orchestrator briefing error.** The brief that opened this pass stated the active lenses are "only `cli` + `library` (no `ux`/`seo`/`security`/`i18n`)". `.spark/constitution.md` §2 declares **four** active lenses — `cli`, `library`, `security`, `ux` — with the elevated-load flag set since 2026-08-03. | **Confirmed closed.** The constitution's four lenses stand as declared and needed no amendment; this spec was already written to all four (§5 NFR-3 security, NFR-4 ux) before this discrepancy was even raised. The narrower set named in the original brief was the orchestrator's error, not the project's state — no change to §5. |
| A3 | **Delivery attribution — RESOLVED by the PO.** A feature must be counted as *delivered* exactly once, but its directory is legitimately touched across several releases. | **Delivery release = the oldest release in which the feature appears as a member.** Every later appearance is a **trailing** member: shown, never hidden, but contributing zero to that release's delivered-scope figures. Measured mapping today: `foundation`→v0.1.0, `traceability-metrics`→v0.2.0, `mcp-server`→v0.3.0, `public-repo-polish`→v0.3.0, `snapshot-report`→v0.4.0, `measurement-honesty`→v0.5.0, `git-native-mid-cycle-board`→v0.7.0, `release-board`→v0.8.0, `release-board-html`→v0.9.0, `release-board-docs`→v0.10.0. v0.6.0 delivers none. |
| A4 | **Opposite anchors — RESOLVED by the PO, and stated because it reads like a contradiction.** `release-board-docs` de-duplicates a feature's *documents* to its **newest** occurrence (correct: you want to read the current state of a spec). A3 anchors *scope* to the **oldest** occurrence (correct: that is where the work landed). | Both are right; they are different questions. This is recorded here and enforced by AC-2.5 precisely so a later change does not "unify" the two rules on the plausible-but-wrong assumption that one anchor should serve both purposes. |
| A5 | **Cadence denominator — RESOLVED by the PO, because the headline number depends on it.** Ten tagged releases produce **nine** inter-release gaps. The brief's "median 2 d" holds for n=9 (`[0,1,1,1,2,2,2,6,8]` → 2); computing over ten values by treating v0.1.0's own pre-history as a gap yields a median of 1.5. The brief's "10 releases in 24 days" is likewise an inclusive day count; the nine gaps sum to **23** days (2026-07-31 → 2026-08-23). | **Cadence is measured over inter-release gaps only: n = (number of tagged releases − 1) = 9 today.** The earliest tag has no predecessor and therefore no gap — `null` with that reason, never a zero. `n` is displayed beside the figure (MTA-001), so the denominator is never implicit. Span is stated as its two endpoint dates, never as a single ambiguous day count. |
| A6 | **The open window is not a delivery — RESOLVED by the PO.** A feature whose first member appearance is in the pseudo-release has not shipped in any tag. | It is reported as *not yet delivered in a tagged release*, with that reason — never counted as delivered, never silently omitted. The pseudo-release keeps its existing `days_since_tag`/`commits`/`work_types` figures untouched (release-board AC-1.8's verbatim reuse is not reopened). |
| A7 | **Key-naming trap — RESOLVED by the PO.** A real release's "gap to its predecessor" and the pseudo-release's existing `days_since_tag` ("age of the latest tag relative to `as_of`") are *different quantities*. | A real release's gap ships under its **own distinct key**, never by overloading `days_since_tag`, whose existing meaning and value stay byte-identical (NFR-2). Naming is `/sprint-plan`'s; distinctness is this spec's ruling. |
| A8 | *(Accepted, inherited — not reopened.)* The aSPARK dark-theme visual language, badge-hue-by-artifact-type-never-by-status, zero-JS static anchors, and newest-first ordering are shipped and Designer-reviewed (`release-board-html` A1/A3/A4, `release-board-docs` A1/A6). | Carries over unchanged. This spec adds figures to existing surfaces; it re-litigates none of them. |

## 4. User Stories

### US-1 (Must): Every real release carries its own measured figures

> As the maintainer, I want each tagged release to show when it happened, how many commits it
> contains and what kind of work they were, so a release stops being a bag of filenames with no
> position in time.

**Acceptance criteria:**

- [ ] AC-1.1: Given a repo with tags, when `insights releases --format json` runs, then every real
  release entry carries a **release date** read from its own tag commit, alongside the existing
  `tag`/`previous_tag`/`next_tag`/`members`/`unattributed` keys — e.g. `v0.5.0` reports
  `2026-08-10`. Verified against `git log -1 --format=%cs <tag>` for at least three distinct tags.
- [ ] AC-1.2: Given a real release, when it is rendered in JSON and HTML, then it carries a
  **commit count** for its own `<previous-tag>..<tag>` range — the same range `build_release_map()`
  already computes membership over, never a second, separately-derived range. Measured today:
  v0.1.0=1, v0.2.0=2, v0.3.0=4, v0.4.0=3, v0.5.0=2, v0.6.0=2, v0.7.0=4, v0.8.0=1, v0.9.0=3,
  v0.10.0=2. (QA B1: this row originally read `v0.6.0=1`; independently re-verified via
  `git rev-list --count v0.5.0..v0.6.0` during `/demo-day` and corrected — the shipped code and
  the rendered page always had the correct value, 2; only this illustrative spec number was stale.)
- [ ] AC-1.3: Given a real release with at least one commit, when rendered, then it carries a
  **work-type mix** produced by the same `worktype.breakdown()` the open window already uses — same
  shape, same declared type order, same `unclassified` bucket — never a second classifier, and it
  is absent (the key omitted, exactly as `board.py` already omits it) rather than shown as a false
  0% when the window has no classifiable commits.
- [ ] AC-1.4: Given a tag whose commit date cannot be read (git leaves `%cI` unexpanded, or the
  value does not parse), when rendered, then that release's date is `null` with a non-empty reason
  and the release is still listed with every other figure it *can* report — never dropped, never a
  guessed or substituted date, never a raw traceback.
- [ ] AC-1.5: Given the same figures, when the HTML page renders, then each real release's figures
  appear on that release's own surface — no real release shows a figure belonging to the open
  window, and the open window's existing `days_since_tag`/`commits`/`work_types` line renders
  byte-identically to v0.10.0 (AC-1.8's verbatim-reuse guarantee survives this feature unchanged).

### US-2 (Must): One stated attribution rule, delivered vs. trailing

> As the maintainer, I want each feature counted as delivered in exactly one release, with every
> later appearance labelled as trailing, so per-release scope stops being roughly doubled by
> release-report bookkeeping commits.

**Acceptance criteria:**

- [ ] AC-2.1: Given a feature appearing as a member of more than one release, when rendered in JSON
  and HTML, then exactly one of those releases marks it **delivering** — the oldest — and every
  other marks it **trailing**, using a machine-readable field, not a rendering-only visual cue.
- [ ] AC-2.2: Given this repo today, when rendered, then the delivering release of all ten features
  matches A3's measured mapping exactly, and **v0.6.0 reports zero delivering features** while
  still listing `measurement-honesty` as a trailing member with its delivery release named.
- [ ] AC-2.3: Given a release's delivered-scope figures, when computed, then only its delivering
  members contribute — v0.9.0 reports **3 US / 13 ACs** (`release-board-html`'s own real content),
  not the 6 / 29 a naive member-sum yields; v0.3.0 reports 7 / 24, not 14 / 42; v0.5.0 reports
  6 / 33, not 11 / 48.
- [ ] AC-2.4: Given a feature whose first member appearance is in the open pseudo-release, when
  rendered, then it is reported as not yet delivered in any tagged release, with that reason — and
  never counted into any real release's delivered scope (A6).
- [ ] AC-2.5: Given the same feature, when its documents are shown, then document de-duplication
  still resolves to its **newest** occurrence exactly as v0.10.0 ships it, while scope attribution
  resolves to its **oldest** — the two anchors are independent, and a test asserts both hold
  simultaneously for at least one feature that appears in two releases (A4).
- [ ] AC-2.6: Given a release whose delivering-member set is empty, when rendered in HTML, then it
  states that in words ("no feature was delivered in this release") — never a blank panel, never a
  `0` indistinguishable from an unreadable value, never conflated with a `null`+reason state.
- [ ] AC-2.7: Given a release's detail card renders a trailing member's document (A4/AC-2.5), when
  displayed, then the document's frame carries a one-line note naming the delivery release
  explicitly (e.g. "trailing member — delivered in `v0.5.0`; document shown as currently written")
  — never a silent juxtaposition of a `0`-delivered figure and that member's full, current document
  with no explanation. Verified on v0.6.0's card, which shows 0 delivering features (AC-2.2)
  alongside `measurement-honesty` displayed as a trailing member (`/look-and-feel` §8 finding 1).

### US-3 (Must): A global figures band and a cadence strip

> As the maintainer, I want the shape of the whole project's release history at the top of the
> page, so I see cadence and total delivered scope before drilling into any single release.

**Acceptance criteria:**

- [ ] AC-3.1: Given the rendered page, when it loads, then a figures band appears above the release
  index carrying, at minimum: number of tagged releases, the first and last release dates, median
  and range of inter-release gaps, number of features delivered, total delivered US and AC counts,
  and the open window's commit count — each a measured number, each with its denominator shown
  (MTA-001). Today: 10 releases, 2026-07-31 → 2026-08-23, median gap 2 d (n=9, range 0-8),
  10 features, 2 commits since v0.10.0.
- [ ] AC-3.2: Given the cadence strip, when rendered, then it depicts the nine measured
  inter-release gaps as discrete measured values, each individually readable as a number in text —
  never only as a length or a color — and the longest gap (8 days, v0.5.0→v0.6.0) is identifiable
  as such from the page alone.
- [ ] AC-3.3: Given fewer releases than the strip needs to be meaningful, when rendered, then the
  strip **refuses itself** — it states that the sample is too small and names `n`, rather than
  drawing a shape over one or two points. Verified against a fixture repo with exactly 1 tag and
  one with exactly 2.
- [ ] AC-3.4: Given any band figure that cannot be honestly computed (a scope count whose source is
  missing or unparseable, a gap whose endpoint date is unreadable), when rendered, then that one
  figure shows `null` with a non-empty reason while every other figure still renders — one
  unreadable input never blanks or crashes the band.
- [ ] AC-3.5: Given a repo with zero tags (the existing `reason: "repository has no tags"` case),
  when rendered, then the band states that reason and shows no figures — never zeros standing in
  for absent data, never a traceback (constitution §6).
- [ ] AC-3.6: Given a feature whose scope would contribute to a release's or the band's delivered
  US/AC counts, when its own `spec.md` is missing, unreadable, or contains no `### US-N` heading
  (unparseable), then that feature's scope contribution is `null` with a stated reason
  (`"spec.md missing"` / `"no US heading found"`) — never an estimated count, and never a silent
  zero folded into another release's or the band's total. This is the same honesty discipline
  `artifactstatus.py` already applies to the status field, reused here for scope counting rather
  than reinvented. Verified against a fixture feature directory with no `spec.md` and one whose
  `spec.md` contains no `### US-N` heading.
- [ ] AC-3.7: Given the cadence strip at any `n`, when rendered, then exactly two states exist and
  no third: (a) **present** — every gap shown as a discrete raw value, with no connecting line, no
  fitted curve, and no interpretive summary of any kind (NFR-5), or (b) **absent** entirely, with a
  stated reason naming `n` (AC-3.3). A partially-drawn state — bars with no line, or some gaps
  replaced by an averaged/summarized value — is never permitted at any `n`, so `/increment` and
  `/demo-day` cannot land on different readings of the boundary (`/look-and-feel` §8 finding 2).

### US-4 (Should): Per-release figures header on each detail card

> As the maintainer, I want each release's detail card to open with its own figures, so I can read
> one release's story without reassembling it from the band and the member list.

**Acceptance criteria:**

- [ ] AC-4.1: Given a real release's detail card, when rendered, then it opens with that release's
  own figures: date, gap to its predecessor, delivering features (and trailing ones, labelled),
  delivered scope (US / ACs), commit count, how many of those commits are unattributed, and the
  work-type mix.
- [ ] AC-4.2: Given the earliest release (v0.1.0), when its card renders, then its gap shows
  `null` with the reason that it has no predecessor — never `0`, which would read as "shipped the
  same day as the one before it" (A5).
- [ ] AC-4.3: Given v0.6.0's detail card, when rendered, then it simultaneously shows 0 delivering
  features, a trailing `measurement-honesty`, the project's longest gap (8 days), and 1
  unattributed commit whose subject appears verbatim — the combination this feature exists to make
  legible.
- [ ] AC-4.4: Given US-4 is not built, when US-1/US-2/US-3 ship, then every Must-level acceptance
  criterion above still passes unchanged — this story is cleanly severable (the same C2 pattern
  `release-board-docs` used for its own Should).

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | CLI (lens) | No new subcommand and no new flag: still `insights releases [--format json\|html] [--repo] [--output] [--as-of]`. Exit codes and the existing error taxonomy (`GitUnavailableError`, `SparkDirUnreadableError`, `InvalidAsOfError`, `NotAGitRepoError`) are unchanged — no new failure class is invented for a failure that already has a name. A1 resolved to a local parser (no graph dependency added); a missing or unparseable feature `spec.md` yields a `null`+reason scope contribution inside the payload (AC-3.6), never a nonzero exit and never a new failure class. | /peer-review |
| NFR-2 | Library (lens) | Every JSON change is **additive**: no existing key is renamed, removed, or has its value or meaning changed. Specifically, the pseudo-release's `commits`/`branches`/`days_since_tag`/`work_types` keep byte-identical values and semantics (A7), and `--format json`'s existing keys remain a superset-compatible read for any current consumer. Zero new runtime pip dependencies, per this project's standing precedent. Verified by a byte-comparison test of the pre-existing key subset against v0.10.0's output on this repo. | /peer-review + increment test |
| NFR-3 | Security (lens) | Every newly rendered string — tag names, dates, work-type labels, reasons, delivery-release names — passes through the existing single `_esc` choke-point before reaching the page; tag names are attacker-influenceable content (a tag may be named arbitrarily). Verified adversarially with a hand-crafted fixture repo carrying a `<script>`-bearing tag name, per this project's adversarial-reproduction bar (CLAUDE.md) — the reviewer/tester constructs their own hostile input rather than re-running the reported one. No raw traceback on any input, including an unreadable date, an unparseable spec (A1's new local parser reading arbitrary feature `spec.md` content), and a repo with one tag. | /peer-review + /demo-day |
| NFR-4 | Accessibility / UX (lens) | Bar inherited unchanged from the shipped board and extended to this feature's new surfaces: the figures band and any per-release figures header use real semantic markup with programmatic label/value pairing (never a `<div>` grid standing in for tabular data); WCAG 2.1 AA contrast (4.5:1 text, 3:1 non-text) on every pair including any bar/strip fill, measured via `getComputedStyle`, never eyeballed; **the cadence strip conveys no information by length or color alone** — every gap is also a number in text (AC-3.2); no horizontal page scroll at 375px measured via `innerWidth`/`scrollWidth`/`clientWidth`; single `<h1>` and coherent heading nesting preserved as the band is inserted above the existing index; nothing animates. Keyboard operability is satisfied by construction, not merely asserted: this feature ships no new interactive element — the figures band and cadence strip are static rendered text/markup, same as the existing board — so there is nothing new to Tab to; verified by confirming `document.querySelectorAll('a,button,input,select,textarea,[tabindex]')` count on the new surfaces matches the pre-existing count, per this project's own precedent (`snapshot-report` NFR-8/qa.md). The figures band (AC-3.1) wraps to a multi-row grid at narrow widths — reusing the existing member-list/status-matrix grid pattern rather than rendering as a single unbreakable row — so it does not reintroduce the 375px horizontal-scroll defect `release-board-docs/qa.md` B1 found on this same page; verified via the same `innerWidth`/`scrollWidth`/`clientWidth` measurement this NFR already requires (`/look-and-feel` §8 finding 4). | /look-and-feel + /demo-day |
| NFR-5 | Measurement honesty (constitution §1/§6, MTA-001) | Every figure this feature ships displays its own denominator `n`, or is `null` with a non-empty, specific reason — never `0` standing in for "unknown", never an interpolated or estimated value. **No fitted trend line, projection, forecast, or extrapolation is drawn over any measured series**, so MTA-001's below-threshold suppression rule is satisfied by construction rather than by a threshold number this project has never set; a series too small to depict refuses itself and says so (AC-3.3). No figure is person-attributed (constitution §6); no git identity field is read. The cadence strip's gap segments and any accompanying labels carry **one uniform hue regardless of value**; a standout gap (e.g. the project's current longest, 8 days) may be emphasized only by rank or text weight — a bolder label, a numeric callout beside the bar — never by a value-dependent color choice, which would read as an undisclosed pass/fail or health verdict (constitution §3/§6) indistinguishable in effect from a traffic light. This extends `release-board-html`'s badge-hue-by-artifact-type-never-by-status rule (A3) to this feature's new bar/strip element (`/look-and-feel` §8 finding 3). | /peer-review + /demo-day |
| NFR-6 | Reproducibility (ADR-4) | For a fixed `HEAD`, tag set and `as_of`, both JSON and HTML output are byte-identical across runs. No `datetime.now()` or other ambient read enters the derivation path: a release's date is a git fact, a gap is the difference between two git facts, and any "age" figure is measured relative to the explicit `as_of` input. Enforced by the existing determinism canary extended to cover the new figures. | /peer-review + increment test |
| NFR-7 | Reliability / offline (ADR-5) | The rendered page stays one self-contained file with no external font, script, image or stylesheet fetch. The band and per-release figures add a bounded, O(releases) amount of content — never O(releases × features) — and the existing page-budget notice and truncation disclosure mechanisms are reused, not replaced. Handles a 1-tag repo, a 2-tag repo, a 0-tag repo, and this repo's 10-tag history without error. | /demo-day |
| NFR-8 | Performance | Reading a date, a commit count and a subject list per release multiplies git subprocess calls by the release count. `insights releases --format html` on this repo (10 releases, 10 features) completes within **5 seconds** on the maintainer's machine, and the number of git invocations grows linearly with release count, not with releases × features — measured, not assumed. This also sets the first concrete number against the constitution §4 performance bar, which has stood at `N/A` with a standing open question since 2026-07-31. | /demo-day |

## 6. Out of Scope

- **Any health, RAG/traffic-light, pass/fail, "on track", "behind schedule", velocity-target or
  release-health score.** Constitution §3 is explicit — Insights measures, `aspark-ci` decides. This
  is the single most likely scope creep on this feature: a figures band is exactly where a product
  owner reaches for a green light. The page ships measured numbers with denominators, never a
  verdict, and no color on it may imply "good" or "bad".
- **Trend lines, forecasts, projections, moving averages, or a "next release expected" estimate** —
  n=9 gaps, and MTA-001 exists to stop precisely this (NFR-5).
- **Any person-level figure** — commits per author, review latency by reviewer, ownership. Not
  merely unbuilt: structurally forbidden (constitution §6), and `gitread` reads no identity field.
- **Re-deriving membership, commit ranges, or artifact status** — this feature reads what
  `build_release_map()` already computes and adds git facts one call away; it re-implements none of
  it (ADR-0).
- **Reordering, re-anchoring, or otherwise changing the shipped document view** — `release-board-docs`'
  newest-occurrence document anchor is deliberately left alone (A4/AC-2.5).
- **Changing what "member" means** — path-based attribution stays exactly as shipped, including the
  disclosed `26e7f95` unattributed case. This feature labels members delivering vs. trailing; it
  does not re-decide who is a member.
- **A graph-backed scope-count source** — decided against (A1); `gitboard` stays graph-free.
- **Cross-repo / fleet aggregation, CSV or spreadsheet export, MCP exposure of these figures,
  client-side sorting/filtering, a configurable theme** — all inherited cuts from prior boards; no
  story here reopens any of them.

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-24 | Does a feature count as delivered in every release its directory was touched in, or exactly one? | **Resolved by the PO (A3).** Exactly one — the oldest occurrence. Every later appearance is trailing, shown but contributing zero scope. Without this, 8 of 10 features double-count and the headline scope figures are wrong by 1.5×-2.2× on real data. |
| C2 | 2026-08-24 | Does the newest-occurrence document rule conflict with the oldest-occurrence scope rule? | **Resolved by the PO (A4, AC-2.5).** No — they answer different questions and both are correct. Recorded and test-pinned specifically so a later "unification" does not silently break one of them. |
| C3 | 2026-08-24 | Is the median inter-release gap 2 days or 1.5? | **Resolved by the PO (A5).** 2 days over n=9 inter-release gaps. 1.5 comes from counting ten values by treating the earliest tag as having a gap, which it does not. The denominator ships next to the number (MTA-001) so the question cannot recur silently. Related: the "24 days" span in the originating brief is an inclusive day count; the nine gaps sum to 23 days, so the spec states endpoint dates instead. |
| C4 | 2026-08-24 | Could US-3 (band + cadence strip) drop to Should, leaving only US-1/US-2 as Musts? | **Probed and rejected by the PO.** The cadence strip is the piece that makes the v0.6.0 case visible at all — a release with zero delivering members and the project's longest gap is only legible when both figures sit on the same surface. US-1/US-2 alone would ship correct numbers nobody compares. US-4 remains the severable Should (AC-4.4). |
| C5 | 2026-08-24 | Should a real release reuse the pseudo-release's `days_since_tag` key for its gap? | **Resolved by the PO (A7).** No — different quantities. Overloading the key would make an existing consumer read "age relative to `as_of`" where a tag-to-tag gap is meant. |
| C6 | 2026-08-24 | Where do the US/AC scope counts come from? | **Resolved by the user (A1).** A local parser over each feature's own `spec.md` — `gitboard` stays graph-free; a missing or unparseable spec yields `null`+reason (AC-3.6), never an estimate or a silent zero. |
| C7 | 2026-08-24 | Is the active-lens set really only `cli`+`library`, narrower than the constitution's four? | **Resolved — not a real discrepancy (A2).** The caller's original brief under-stated the set; `.spark/constitution.md` §2's four lenses (`cli`/`library`/`security`/`ux`) stand as declared, and this spec's §5 already targeted all four (NFR-3/NFR-4). No amendment, no change. |
| C8 | 2026-08-24 | Could the cadence strip highlight its longest gap with a distinct (e.g. warning) color? | **Resolved by the PO, per `/look-and-feel` §8 finding 3.** No — every gap segment carries one uniform hue regardless of value (NFR-5); a standout gap is emphasized only by rank or text weight, never color, per constitution §3/§6 and the existing badge-hue-never-by-status precedent. The feature's own originating mockup used a warning hue for this exact bar, which is precisely the risk this closes. |
| C9 | 2026-08-24 | Beyond the n=1/n=2 refusal, can the cadence strip ever show raw bars without the interpretive line as a partial, in-between state? | **Resolved by the PO, per `/look-and-feel` §8 finding 2 (AC-3.7).** No third state exists — the strip is either fully present (raw discrete values, no line, no summary) or fully absent with a stated reason naming `n`. |
| C10 | 2026-08-24 | When a release card shows a trailing member's document, does the reader see any explanation for "0 delivered" sitting beside a full current document? | **Resolved by the PO, per `/look-and-feel` §8 finding 1 (AC-2.7).** Yes — a one-line note names the actual delivery release explicitly; never a silent juxtaposition of the two figures. |
| C11 | 2026-08-24 | Does the new figures band risk the same 375px horizontal-scroll bug `release-board-docs` shipped once already? | **Resolved by the PO, per `/look-and-feel` §8 finding 4 (NFR-4).** The band wraps to a multi-row grid at narrow widths, reusing the existing grid pattern used elsewhere on the page. |

## 8. Design Review

<!-- Filled by /look-and-feel, Specify-phase pass against the spec. No running page exists yet;
     release-board-docs/spec.md §8 and release-board-html/spec.md §8 (the two prior reviews of
     this exact visual system) were read first so nothing already-decided (aSPARK dark theme,
     badge-hue-by-artifact-type-never-status, zero-JS static anchors, A8/A6) is re-litigated. -->

- **Overall impression:** The four stories add numbers to an already-decided visual system rather
  than opening a new one, and every AC that touches an honesty edge case (null+reason, small-n
  refusal, empty delivering-set wording) is written with the same discipline this project's prior
  two reviews praised. The real design risk here isn't craft, it's **legibility of two rules that
  are individually correct but collide on the same rendered surface**: US-2's oldest-anchor
  scope rule sitting next to the inherited newest-anchor document rule (A4), and US-3's figures
  band sitting directly above an index that a prior QA pass (`release-board-docs` B1) already
  proved is not free of 375px surprises. Nothing below reopens A1-A8, US-1-US-4's scope, or asks
  for new stories — every finding is a wording addition to an existing AC/NFR, safe for
  `/increment`.

- **Findings:**

  1. **[Major] AC-2.5 pins that the two anchors (scope: oldest, document: newest) hold
     simultaneously — but no AC states what a reader sees when a release detail card shows both
     at once, which is exactly the v0.6.0-shaped case this feature exists to make legible.**
     Location: US-2/AC-2.1, AC-2.5; `release-board-docs` A4/AC-2.5. Rule: Match the real world /
     recognition over recall — a reader who has not internalized "delivery anchor ≠ document
     anchor" will see a release card stating "0 delivering features" (US-4/AC-4.3's own v0.6.0
     example) directly beside a member row whose document view shows that same feature's *current,
     full* content, and will reasonably read this as a contradiction or a bug, not two correct
     answers to two different questions. Fix: wherever a trailing member's document is shown on a
     release that did not deliver it, the document's frame carries a one-line note naming the
     delivery release explicitly (e.g. "trailing member — delivered in `v0.5.0`; document shown as
     currently written") — this is a wording addition to AC-2.1/AC-2.2's existing trailing-label
     requirement, not a new AC.

  2. **[Major] AC-3.3's small-sample refusal is stated for the whole strip (1 or 2 tags) but not
     for the boundary the spec's own honesty rule (NFR-5, MTA-001) is actually protecting against:
     a strip that renders raw bars/values for n below some threshold and only omits the
     *interpretive* line.** Location: AC-3.2, AC-3.3, NFR-5. Rule: Visibility of status /
     consistency — an underspecified boundary here is exactly the kind of ambiguity CLAUDE.md
     flags as inviting `/increment` and QA to diverge. As written, AC-3.3 only names the "refuses
     itself entirely" behavior at n=1/n=2; it is silent on whether the strip *ever* ships bars with
     no line versus always being all-or-nothing. Since NFR-5 already bans any fitted line
     regardless of n, the honest simplification is to state it as one rule: the strip is either
     absent-with-stated-reason (small n) or present as discrete labeled values with no connecting
     line, ever — never a third, partially-drawn state. Fix: fold this single sentence into AC-3.2
     so it can't be read two ways at `/increment`.

  3. **[Minor, flagged because of the constitutional stakes, not craft] The cadence strip is one
     highlight-color choice away from becoming the RAG verdict §6/NFR-5 explicitly forbids, and
     neither AC-3.2 nor NFR-5 states the rule that would stop it.** Location: AC-3.2; §6 ("no color
     may imply good or bad"); NFR-5. Rule: Color used with meaning, not decoration, and never as a
     verdict — the badge-hue precedent (`release-board-html` A3, "never by status") is the directly
     applicable prior ruling. A single value singled out by a distinct hue *because* it is the
     longest gap (the 8-day v0.5.0→v0.6.0 case AC-3.2 itself names as the thing to make
     identifiable) reads as "this one is bad" the moment its color differs from its eight
     siblings for a reason other than category — indistinguishable in effect from a red traffic
     light, regardless of which specific hue is chosen. AC-3.2's own "identifiable as such from the
     page alone" is satisfiable without this risk: the number and the strip's own position/order
     already make the maximum findable without any value-dependent color. Fix: add one clause to
     AC-3.2 — every gap segment/label uses one uniform hue regardless of its value; "longest gap
     identifiable" is satisfied by the number and, if wanted, a neutral non-color cue (e.g. boldest
     label weight or a text marker) applied by *rank*, never by a distinct color tied to magnitude.
     This is a genuine tripwire given the constitution's explicit ban and this feature's own
     originating mockup reportedly using a warning hue for this exact bar — naming the rule now is
     cheaper than un-shipping a color choice later.

  4. **[Minor] The figures band (US-3) is inserted above the existing index with no stated
     collapse or compactness constraint, on a page a prior QA pass already found fragile at
     375px.** Location: AC-3.1; `release-board-docs/qa.md` B1 (embedded `<code>` wrap failure at
     375px, round 1). Rule: Minimalism / responsive layout — AC-3.1 lists seven distinct figures
     (release count, two dates, gap median+range, feature count, two scope totals, commit count)
     with no stated layout hint, which risks either a seven-cell single row that cannot fit 375px
     without wrapping oddly, or a tall stacked block that pushes the actual release list below the
     fold on mobile before the "ten-second" scan even reaches it. Fix: no new AC needed — add a
     sentence to AC-3.1 or NFR-4 stating the band wraps to a multi-row grid at narrow widths
     (reusing whatever grid/flex pattern the existing member-list or status-matrix already uses)
     rather than a single unbreakable row, so this doesn't get discovered as a second 375px bug at
     `/demo-day` the way B1 was.

  5. **[Minor, confirms severability, not a gap] US-4's AC-4.4 states severability as an outcome
     but the spec doesn't say US-4 renders through its own function/anchor** — worth naming so
     `/sprint-plan` treats it as a design constraint, not just a test assertion. Location: AC-4.4.
     Rule: Consistency / architecture-matches-claim. AC-4.4 is testable as written (Musts still
     pass if US-4 is "not built"), but the *design* claim of severability is stronger if the
     per-release figures header is understood from the start as its own render unit rather than
     interleaved into US-1's per-release loop — otherwise "not built" silently means "commented
     out" rather than "cleanly absent." Fix: no AC change required; this is a one-line note for
     `/sprint-plan`'s Engineering Manager to route into the module/function split, consistent with
     this project's own "shared core, thin adapters" pattern (CLAUDE.md) applied to severability
     rather than to CLI/MCP parity.

- **Accessibility notes:** NFR-4 correctly inherits the shipped bar unchanged and correctly states
  the strip conveys nothing by length/color alone (AC-3.2) — finding 3 above sharpens that same
  rule against a specific, named collision with the constitution's RAG ban rather than adding a
  new accessibility requirement. NFR-4's `<h1>`/heading-nesting and keyboard-operability language
  (zero new interactive elements) is sound as written and needs no addition. No new accessibility
  gap beyond findings 3 and 4 above.

- **Design risks & required changes:**
  - **Before `/increment` starts (needs a one-line answer, not new scope):** finding 3 — the
    cadence-strip color rule must be pinned to "uniform hue, rank/weight only" before a hostile
    reading of AC-3.2 (color by magnitude) gets built and has to be un-shipped as a constitution
    violation.
  - **Fold into existing AC/NFR wording, safe for `/increment`:** findings 1, 2, and 4.
  - **Note for `/sprint-plan`, not a finding against the spec:** finding 5.
  - **No blocker.** No finding reopens A1-A8, §6, or any SPEC GATE box; the design direction is
    sound enough to proceed to `/sprint-plan` once finding 3's one-line color rule is confirmed.

---

## ✅ SPEC GATE

*All boxes checked → `/sprint-plan` may start. Any box open → back to `/story-time` or `/look-and-feel`.*

- [x] Problem, goal and success signal are concrete — grounded in figures measured against this
  repo on 2026-08-24 (10 tags, the v0.6.0 case, the 1.5×-2.2× double-count), not estimated
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must — US-1/US-2/US-3 Must, US-4
  Should, with AC-4.4 pinning its severability
- [x] Non-functional requirements are stated and measurable — including the first concrete
  performance number in this project (NFR-8), against a constitution bar standing at `N/A`
- [x] Clarify pass done: no ambiguity left unresolved or unparked — C1-C11 resolved (C1-C5, C8-C11
  by the PO; C6/A1 and C7/A2 escalated and resolved by the user, not silently absorbed)
- [x] Open questions are resolved or explicitly accepted as risk — A1 resolved by the user (local
  parser over each feature's own `spec.md`, AC-3.6 states the failure mode); A2 confirmed as an
  orchestrator briefing error, not a real constitution conflict — no change needed to §5
- [x] Out-of-scope section is filled — the health/RAG verdict, trend lines, and person-level
  figures are named, conscious, constitutionally-required cuts
- [x] Constitution respected, or conflicts recorded as open questions — §3's no-judgment rule is
  enforced in §6 and NFR-5; ADR-0/4/5 and MTA-001 are honored; the two genuine tensions (A1's
  ADR-0-vs-standalone trade, A2's lens set) are recorded as open questions, not overridden
- [x] Design review done for UI-facing features — `/look-and-feel` ran; 5 findings, no
  Blocker, all folded back into ACs/NFRs (AC-2.7, AC-3.7, NFR-4, NFR-5)
- [x] Status set to `approved` by the user — given in this conversation
