# Spec: feature-lens

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-25 |
| **Ticket** | none |

<!-- Handoff: read this block first, the numbered sections below by exception. -->

**Handoff**
- **Status:** `approved` (2026-08-25, user approval in conversation, after `/look-and-feel`'s design
  check with no Blocker — findings folded into ACs, see C9) — header table authoritative for
  `Status`.
- **Summary:** The release board (`insights releases`, v0.11.0) is release-centric — one card per
  git tag. A feature that spans releases (nearly all of them do, structurally: see §1) is scattered
  across cards by design. This feature adds a second, equally-weighted view: one row per feature
  (spec date → 5-artifact status → delivered-in tag), plus a derived, honestly-labelled current-gate
  position, grouped into a Should-level pipeline section. No new git/`.spark/` read: every field
  already exists in `build_release_map()`'s per-member output (A1).
- **Open:** none — every clarification below was resolved by the PO in this pass (§7); nothing
  parked to §3 as blocking.
- **Binding ruling:** §4 User Stories for what's committed; §6 for what was cut; §7 for what changed
  and why.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch at
  the next `/peer-review` and proceed.

## 1. Problem & Goal

- **Problem:** Asking "where does feature X stand, end to end?" today means opening the release
  board and manually reconciling **two or more cards**, because it is the *structural default*, not
  a rare edge case, for a feature to appear on more than one release's card. Measured on this repo
  today: `release-board-docs` delivered in `v0.10.0` (its own `spec.md` reads `2026-08-23`) but its
  bookkeeping commit also lands inside `v0.11.0`'s range, where it shows as a **trailing** member
  next to `release-metrics`'s own delivering entry. The same shape repeats at essentially every
  release boundary — `release-board` (delivered `v0.8.0`) trails again into `v0.9.0`; `v0.3.0` alone
  delivered **two** features (`mcp-server`, `public-repo-polish`) while `v0.6.0` delivered **zero**.
  A reader has to already know the release board's own oldest-occurrence delivery rule and newest-
  occurrence document rule (two different, both-correct, already-shipped anchors — `release-metrics`
  A3/A4) just to avoid misreading a trailing appearance as a second delivery.
- **Goal:** One row per feature — its own spec date, its own 5-artifact gate status, and the single
  release it actually delivered in (or an honest "not yet delivered") — so a feature's whole story
  reads without cross-referencing release cards. A Should-level pipeline grouping surfaces where an
  in-flight feature currently sits, the moment one exists.
- **Success signal:** Rendered against this repo today, `release-board-docs`'s row reads exactly:
  spec date `2026-08-23`, gate `Released` (its `release.md` literally reads `released`), delivered
  in `v0.10.0` — with no second row, no `v0.11.0` entry, and no need to open `v0.11.0`'s card to
  confirm it isn't double-delivered there. Second signal: this repo's 11 real features produce 11
  rows, all reading gate `Released`, delivered across `v0.1.0`–`v0.11.0` exactly matching
  `release-metrics` A3's already-measured mapping — a reader can confirm the new view agrees with
  the already-trusted one, not a second, divergent bookkeeping system.
- **Why now:** Nothing breaks if this is never built — the release board is correct today, and the
  reconciliation cost only bites someone who actually tries to trace one feature across cards, which
  is exactly the act a Product Owner deciding what to build next performs. What weighs for it: every
  field this feature needs is already computed (A1, ADR-0) — this is a new *grouping/traversal* of
  existing data, not a new metric or a new read, so the cost is close to the floor a feature in this
  project can have. What it displaces: the still-open cycle-time/rework-rate work named in the
  originating `/next-steps` brief — deliberately not started here (§6), since both are blocked on
  aSPARK core issues (#24, #26) this project doesn't control.

## 2. Target Users

- **The maintainer deciding what to build next (concrete: Andreas)** — the same reader the release
  board already serves, in a different act: not "reconstruct what a release contained" (solved) but
  "check on one feature," which today costs a multi-card reconciliation.
- **A future `aspark-ci` consumer (named, not built)** — this feature's JSON is a shape a gate could
  read (e.g. "is anything sitting in Review right now"). It stays measurement only; no gate logic
  ships here (constitution §3).

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | Every field this feature needs (spec date, 5-artifact status, delivery tag) already exists in `build_release_map()`'s per-member output — confirmed by reading `releasemap.py`/`artifactstatus.py` directly, not assumed. | **Confirmed.** No new git call and no new `.spark/` read beyond what the release board already performs. Per-feature US/AC scope (`scopecount.py`) also already exists but is deliberately not surfaced here (§6) — its availability was checked, then declined, not overlooked. |
| A2 | The derived "current gate" (Spec/Increment/Review/QA/Released/Unknown) is a *label over already-known statuses*, not a new fact — does this risk becoming exactly the health/verdict language constitution §3/§6 forbids? | **No, by construction (AC-2.1/AC-2.5).** The label always renders paired with the literal status string of the artifact it was derived from (e.g. "Increment — plan: approved, review: not started"); no color, icon or ordering implies better/worse. It is a position, not a verdict — the same distinction the release board already draws for delivering/trailing. |
| A3 | This repo's real data has **zero** in-flight features today (all 11 are `released`) — can the Spec/Increment/Review/QA pipeline buckets be proven against real data at all this cycle? | **No, disclosed as a real limitation, not a defect.** AC-2.3/AC-2.4/AC-3.3 are verified against a purpose-built fixture directory; AC-2.2/AC-3.2 verify the `Released`-only real case. Both are named explicitly rather than one silently standing in for the other. |
| A4 | Does this feature re-decide the release board's own delivery-attribution (oldest occurrence) or document (newest occurrence) rules? | **No (§6).** Both are reused verbatim, unchanged, from the already-shipped `release-metrics`/`release-board-docs` rules. This feature adds a new *grouping* of the same underlying facts; it does not re-litigate either anchor. |
| A5 | Cycle time (spec date → delivery tag date) is trivially computable from fields this view already displays side by side — should it ship, even in an honestly-labelled coarse form? | **Omitted entirely, not a coarse honest version either (§6).** `spec.md`'s `Date` field is overwritten on every status change (aSPARK core issue #24, open, external) — it reflects "last updated," not "interrogation started." Even a carefully-worded coarse figure sitting directly next to a delivery-tag date on the same row is one glance away from being read as real phase duration; the risk of that misreading outweighs the value of a number this project cannot yet compute honestly. |

## 4. User Stories

### US-1 (Must): One row per feature — spec date, gate status, delivered-in tag

> As the maintainer, I want to see each feature's own spec date, 5-artifact status and the single
> release it actually delivered in, so I can check on one feature without opening every release
> card it happens to touch.

**Acceptance criteria:**

- [ ] AC-1.1: Given `insights features --as-of <date> --format json` run against this repo, when it
  completes, then the output lists all 11 real `.spark/` features (`foundation`,
  `traceability-metrics`, `mcp-server`, `public-repo-polish`, `snapshot-report`,
  `measurement-honesty`, `git-native-mid-cycle-board`, `release-board`, `release-board-html`,
  `release-board-docs`, `release-metrics`), each exactly once, each carrying its own `spec.md`
  `Date`, its 5-artifact status map (`spec`/`plan`/`review`/`qa`/`release`, each `{status, date,
  reason}`), and its delivery tag — every value read verbatim from `build_release_map()`'s existing
  per-member output, never a second, separately-derived computation (ADR-0). Every cell — including
  a full-sentence reason string — honors the same wrap/`max-width` discipline as NFR-4, never
  causing the row or page to overflow horizontally.
- [ ] AC-1.2: Given `release-board-docs` specifically, when rendered, then its delivered-in tag
  reads `v0.10.0` — the one release it actually delivered in — even though it also appears as a
  trailing member of `v0.11.0`'s window; it appears as exactly one row, never duplicated, and
  `v0.11.0` is never shown as a second delivery for it.
- [ ] AC-1.3: Given a feature whose only appearance so far is the open pseudo-release (a fixture —
  no real feature in this repo is in that state today, A3), when rendered, then its delivered-in tag
  is `null` with the reason "not yet delivered in a tagged release," reused verbatim from the
  existing delivery attribution, not re-derived.
- [ ] AC-1.4: Given a feature whose `spec.md` cannot be read (missing, unreadable, or no header
  table — the same degrade path `artifactstatus.py` already defines), when rendered, then its row
  still appears with the specific named reason for whichever field failed — never silently dropped,
  never a raw traceback. That reason text renders within the per-feature table's own wrap discipline
  (NFR-4) — long enough to be read in full, never the cause of horizontal overflow.
- [ ] AC-1.5: Given `--format html`, when the page renders, then the same per-feature data appears
  as one row per feature in a real `<table>` with `<th>` column headers (never a `<div>` grid
  standing in for tabular data), ordered by `spec.md` `Date` newest-first, tie-broken by feature name
  ascending — the same "newest first" convention the release board already established. The
  5-artifact status cells render as compact type+status badges (reusing `_ARTIFACT_HUES`), with the
  full reason text shown only when a status is `null` — never duplicated inline alongside a
  plain-word status such as `approved` — and every cell in the table honors NFR-4's wrap discipline.

### US-2 (Must): An honest, derived current-gate position per feature

> As the maintainer, I want each feature's current position in the pipeline stated as a plain named
> stage — never a health verdict — so I can tell where a feature sits without it being colored as
> "on track" or "behind."

**Acceptance criteria:**

- [ ] AC-2.1: Given a feature's own status map, when its current gate is computed, then it is
  exactly one of `Spec`, `Increment`, `Review`, `QA`, `Released`, `Unknown` — found by checking
  `release` → `qa` → `review` → `plan` → `spec` in that order and stopping at the first non-null
  status (`release` non-null → `Released`; `qa` non-null → `QA`; `review` non-null → `Review`;
  `plan` non-null → `Increment`; `spec` non-null → `Spec`; all null → `Unknown`) — and the result
  always renders paired with the literal status string of the artifact it was derived from (e.g.
  "Increment — plan: approved, review: not started"), never a bare label with no artifact evidence
  attached. The gate label renders as plain headed text only — never a progress bar, step-tracker,
  filled/unfilled dot-track, or any other shape-based device that encodes "further along = better"
  independent of color — and uses exactly one uniform badge/text treatment regardless of which of
  the six values it holds, with no distinct hue assigned per gate value (extending
  `_ARTIFACT_HUES`'s existing hue-keyed-to-artifact-type-never-status rule to this status-shaped
  field).
- [ ] AC-2.2: Given this repo's real, current data, when rendered, then all 11 features show gate
  `Released`, each displaying its own `release.md`'s literal status string (`released`) — verified
  against this repo's own `.spark/*/release.md` files, not a fixture, for this one AC.
- [ ] AC-2.3: Given a fixture feature directory carrying an approved `plan.md` and no `review.md`,
  when rendered, then its gate reads `Increment` — verified against a purpose-built fixture, since
  no real feature in this repo is in that state today (A3, a disclosed limitation, not a defect).
- [ ] AC-2.4: Given a fixture feature directory whose `spec.md` has no readable header-table
  `Status` row, when rendered, then its gate reads `Unknown` with that exact reason surfaced —
  never guessed as `Spec` just because the directory exists.
- [ ] AC-2.5: Given the current-gate field, when compared across any two features, then no color,
  icon, or sort order implies one feature's position is "better" or "worse" than another's — every
  gate is a plain named position with its evidence attached, never a pass/fail/health/staleness
  verdict (constitution §3/§6). This includes the rendering device itself: no progress bar,
  step-tracker, or filled/unfilled dot-track for the gate, since such a shape can encode sequence
  completion on its own, independent of any color choice or cross-feature comparison.

### US-3 (Should): A pipeline section grouping features by current gate

> As the maintainer, I want features grouped visually by their current gate, so an in-flight
> feature's position is visible at a glance without reading every row of the table.

**Acceptance criteria:**

- [ ] AC-3.1: Given the same `--format html` page, when it renders, then a second section groups
  every feature into exactly one bucket per US-2's rule (`Spec`/`Increment`/`Review`/`QA`/
  `Released`, plus `Unknown` only if it actually occurs) — every feature appears in exactly one
  bucket, never split across two, never omitted from all of them. The pipeline section itself
  renders as plain headed groups — never a progress bar, step-tracker, or filled/unfilled dot-track
  spanning the six buckets — since that shape alone would encode "further along = better"
  independent of any color used.
- [ ] AC-3.2: Given this repo's real data, when rendered, then the `Released` bucket lists all 11
  features and every other bucket states plainly that it currently holds none (e.g. "no feature is
  currently at this stage") — never blank, never absent, never a bare `0` indistinguishable from an
  unreadable value. Every bucket — empty or populated — renders with the same structural weight (its
  own heading, the same section chrome, the same type scale), using this page's existing
  `.empty-notice` idiom for the empty case — never dimmed, collapsed, or visually de-emphasized
  relative to the populated `Released` bucket.
- [ ] AC-3.3: Given a fixture repo with one feature manually placed at each of the six stages, when
  rendered, then each bucket shows exactly the one feature expected for it — the AC that actually
  proves the grouping logic end-to-end, since this repo's own real data cannot (A3).
- [ ] AC-3.4: Given US-3 is not built, when US-1/US-2 ship, then every Must-level acceptance
  criterion above still passes unchanged — this story is cleanly severable, the same pattern
  `release-metrics`' own Should (AC-4.4) used.

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | CLI (lens) | A new subcommand, `insights features`, mirrors `board`/`releases`: `--as-of` (required), `--repo` (default `.`), `--output` (default `--repo`, documented in `--help`), `--format {json,html}` (default `json`). Reuses the existing error taxonomy — no new error class for a failure that already has a name (`InvalidAsOfError`, `NotAGitRepoError`, `GitUnavailableError`, `SparkDirUnreadableError`). Results on stdout only; nothing on stdout in `--format html` mode beyond the `{"report": <path>}` JSON `insights releases`/`board` already use for their own HTML branch. | /peer-review |
| NFR-2 | Library (lens) | Purely additive: no existing `insights build\|query\|render\|diff\|verify\|board\|releases` key, flag, or exit code changes meaning. Zero new runtime pip dependency. This feature's own JSON (`insights features --format json`) is new surface with no prior consumer to break. | /peer-review |
| NFR-3 | Security (lens) | Every rendered string — feature name, tag name, status string, reason text — passes through the same single HTML-escaping choke point the release board already uses before reaching the page; feature-directory names and tag names are attacker-influenceable content. Verified adversarially with a hand-crafted fixture carrying a `<script>`-bearing feature-directory name and a `<script>`-bearing tag name, per this project's adversarial-reproduction bar (CLAUDE.md) — a fresh hostile fixture, not a reused one. No raw traceback on any input, including an unreadable `spec.md`, a feature with no artifacts at all, and a zero-feature `.spark/`. | /peer-review + /demo-day |
| NFR-4 | Accessibility (constitution §4 bar) | Semantic HTML: single `<h1>`, coherent heading nesting, the per-feature table as a real `<table>`/`<th>` (AC-1.5), the pipeline buckets (US-3) as headed groups, not unlabeled `<div>`s. WCAG 2.1 AA contrast (4.5:1 text, 3:1 non-text), measured via `getComputedStyle`, never eyeballed. No new interactive element beyond the existing page's pattern (e.g. `<details>`), so keyboard operability holds by construction — verified by confirming the count of `a,button,input,select,textarea,[tabindex]` matches the existing page's own count, per `snapshot-report`'s established technique. No horizontal scroll at 375px (`innerWidth`/`scrollWidth`/`clientWidth`), extending `release-board-docs` B1's own mobile precedent to this page's new table and pipeline sections. Specifically, every cell of the new per-feature table — not only prose — carries the same `overflow-wrap`/`max-width` treatment already scoped to `.doc-content p, li, code`, since up to five artifact-status cells (each potentially holding a null-reason sentence) plus a spec date and delivery tag share one row; the 5-artifact status cells render as compact type+status badges with the reason text shown only when status is `null`, never duplicated alongside a plain-word status. | /look-and-feel + /demo-day |
| NFR-5 | Measurement honesty (constitution §1/§6) | Every field is either a value read verbatim from existing artifact/scope data with its own denominator, or `null` + a specific, non-empty reason — never an estimate, never a silent zero. The current-gate label (US-2) is never shown without the literal status string of the artifact it was derived from. `spec.md`'s `Date` field is labelled exactly as "spec.md's own Date (last updated)," never as "spec started on" or any phrasing implying phase-start precision it does not have (A5, aSPARK core issue #24). No git-identity/person-level field is ever read or shown (constitution §6) — `gitread.py`'s existing identity refusal is relied on unchanged. | /peer-review + /demo-day |
| NFR-6 | Reproducibility (ADR-4) | For a fixed `HEAD`, `.spark/` tree and `as_of`, both `--format json` and `--format html` output are byte-identical across repeated runs. No `datetime.now()` or other ambient read enters the derivation path. | /peer-review + increment test |
| NFR-7 | Reliability / offline (ADR-5) | The rendered page stays one self-contained file, no external font/script/stylesheet fetch. Handles a zero-feature `.spark/`, a single-feature repo, and this repo's 11-feature history without error — a zero-feature `.spark/` states that plainly ("no features found") rather than rendering an empty table with no explanation. | /demo-day |
| NFR-8 | Performance | This feature adds **zero additional git subprocess calls** beyond a single already-computed release-map-equivalent pass — its own per-feature grouping/labelling cost is O(features) in-memory work, sub-second, independent of and never compounding the pre-existing, separately-disclosed git-walk cost the release board already carries (`release-metrics` NFR-8's known, unrelated limitation is not repeated or re-measured here). | /demo-day |

## 6. Out of Scope

- **Cycle time / rework rate / findings-severity density in any form**, including an honestly-
  labelled coarse "spec-date-to-tag-date" figure — deliberately omitted, not merely deferred (A5).
  Blocked on aSPARK core issues #24 (single overwritten `Date` field) and #26 (no machine-readable
  severity); revisit only once either lands upstream.
- **AI token/cost usage** — out of scope entirely, pending its own spec (unresolved reproducibility
  and person-level-data questions), unrelated to this feature's data.
- **Any health, RAG/traffic-light, pass/fail, "on track"/"blocked," or velocity verdict** —
  constitution §3/§6 forbids it; the current-gate label is a position with evidence attached, never
  a judgment (AC-2.5).
- **Re-deriving membership, commit ranges, delivery attribution, or the document newest-occurrence
  rule** — all reused verbatim from the already-shipped release board (A4, ADR-0); this feature adds
  a new grouping of existing facts, not a second set of rules.
- **Per-feature US/AC scope counts on this view** — already available on the release board
  (`scopecount.py`); deliberately not duplicated here to keep this page about status/position, not
  size. A conscious cut, not an oversight (A1).
- **A separate CLI `--format` value for the pipeline grouping (US-3)** — it ships as a second
  section of the same `--format html` page, not a new flag value, so there is exactly one page to
  keep self-contained and offline (ADR-5).
- **MCP exposure of this data this cycle** — the existing MCP server exposes only the snapshot-based
  `query` tool; no current consumer asked for feature-lens or release-board-shaped data over MCP,
  mirroring `release-metrics`' own precedent of not extending MCP for its own new figures.
- **Any write/edit affordance** — this view is read-only, same as the release board; no action a
  reader takes here changes any artifact's status.
- **Cross-repo/fleet aggregation, CSV/spreadsheet export, client-side sorting/filtering, a
  configurable theme** — inherited cuts from every prior board in this project; no story here
  reopens any of them.

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-25 | Does this view re-decide the release board's oldest-occurrence delivery rule or newest-occurrence document rule? | **No (A4).** Both reused verbatim from `release-metrics`/`release-board-docs`; this feature only adds a new grouping of the same facts. |
| C2 | 2026-08-25 | How is the current gate computed when even `spec.md`'s own status can't be read? | **`Unknown`, with that exact reason surfaced (AC-2.4)** — never guessed as `Spec` merely because the directory exists. |
| C3 | 2026-08-25 | Should cycle time (spec date → delivery tag date) ship, since both dates already sit on the same row? | **No, omitted entirely, not even a labelled coarse version (A5).** The risk of a single-overwritten-Date-field figure being read as real phase duration outweighs the value, per aSPARK core issue #24. |
| C4 | 2026-08-25 | Is the pipeline grouping (US-3) a new CLI `--format` value or a section of the existing page? | **A section of the same `--format html` page.** No new flag value; one self-contained page stays the unit (ADR-5). |
| C5 | 2026-08-25 | What order are feature rows shown in? | **Newest `spec.md` `Date` first, tie-broken by feature name ascending** — mirrors the release board's own newest-first convention. |
| C6 | 2026-08-25 | Should per-feature US/AC scope be duplicated onto this view since it's already computed? | **No (§6).** Deliberately cut to keep this page about status/position; already shown on the release board. Checked, not overlooked (A1). |
| C7 | 2026-08-25 | Does the current-gate label risk reading as a health verdict? | **No, by construction (A2, AC-2.1/AC-2.5).** It always renders with the literal artifact status string it was derived from; no color/icon/order implies better or worse. |
| C8 | 2026-08-25 | Can this feature's real ACs prove the in-flight pipeline stages (Increment/Review/QA), given this repo has zero in-flight features today? | **No — disclosed honestly (A3).** AC-2.3/AC-2.4/AC-3.3 verify against a purpose-built fixture; AC-2.2/AC-3.2 verify the real `Released`-only case. Neither substitutes for the other. |
| C9 | 2026-08-25 | `/look-and-feel`'s design-check surfaced three findings (the gate/pipeline concept risks a progress-bar/step-tracker/hue-per-value device even with zero verdict language; AC-3.2's empty-bucket wording is honest but not designed for the 5-of-6-empty real case; the new per-feature table's 5-artifact-status-plus-date-plus-tag row has no stated wrap discipline) — fold as a scope change or as AC/NFR wording additions? | **Folded as AC/NFR wording additions, no scope change** — matches the non-reopening precedent `release-metrics`' own finding 3 set (Designer via `/look-and-feel`). AC-2.1/AC-2.5/AC-3.1 gained an anti-metaphor clause (no progress-bar/step-tracker/dot-track; no hue-per-gate-value, one uniform badge/text treatment). AC-3.2 gained an empty-bucket structural-parity clause reusing the existing `.empty-notice` idiom. AC-1.1/AC-1.4/AC-1.5/NFR-4 gained explicit per-cell wrap/`max-width` discipline plus a compact-badge-with-conditional-reason treatment for the 5-artifact status cells. §8 Design Review is unchanged — it is the Designer's own record. |

## 8. Design Review

<!-- Filled by /look-and-feel, Specify-phase pass against the spec. No running page exists yet.
     Read first, so nothing already-decided is re-litigated: `release-board-html/spec.md` §8 and
     `release-board-docs/spec.md` §8 (this visual system's two prior reviews), `release-metrics/
     spec.md` §8 (the sibling that hit this exact class of constitutional risk on its cadence
     strip), and `src/aspark_insights/gitboard/releaseboard_report.py`'s live `_STYLE`/
     `_ARTIFACT_HUES`/`_render_cadence_strip` for the conventions already in production. -->

- **Overall impression:** The spec's own honesty discipline (null+reason, AC-2.5's explicit
  anti-verdict clause, A2/A3/C7/C8 all naming the risk directly) is at the same bar the project's
  two prior boards were held to, and every user-facing wording choice is already carefully hedged.
  The gap is not in the *words* the spec commits to — it's that nothing yet constrains the
  **visual mechanism** used to render a derived, six-valued, sequence-shaped concept (the gate)
  and a per-stage grouping of it (the pipeline section), and that mechanism is exactly where this
  project's own precedent (`release-metrics` finding 3) shows the constitutional risk actually
  lands: not in copy, in shape and color. Nothing below reopens US-1/US-2/US-3's scope, AC-3.4's
  severability, or any §6 cut — every finding is a wording addition to an existing AC/NFR, safe to
  fold before `/sprint-plan`.

- **Heuristics findings:**

  1. **[Major] The gate concept (AC-2.1) and the pipeline grouping (AC-3.1) are both six-valued and
     inherently sequence-shaped, but no AC or NFR yet bans the visual metaphors that would turn
     "a position" back into "a maturity ladder" even with zero verdict language and zero
     comparative color.** Location: US-2/AC-2.1, AC-2.5; US-3/AC-3.1; constitution §3/§6. Rule:
     Color/shape used with meaning, never as an implied verdict — this is the same tripwire
     `release-metrics` finding 3 flagged on its cadence strip ("one highlight-color choice away
     from becoming the RAG verdict §6 forbids"), and it recurs here in a sharper form because the
     underlying value is *itself* an ordered stage name, not a magnitude. AC-2.5 correctly bans
     color/icon/sort order that implies one **feature** is better or worse than another — but it
     is silent on two adjacent, equally real risks: (a) a **progress bar, filled/unfilled
     step-tracker, or dot-track** rendering of the gate or the pipeline section reads as "further
     along = more done/better" from its shape alone, independent of any color or feature-to-feature
     comparison — the device itself encodes rank; (b) a **distinct hue per gate value**
     (e.g. muted grey for `Spec`, vivid green for `Released`) would contradict this project's own
     already-shipped, already-reviewed precedent that hue is keyed to artifact **type**, never to
     artifact **status** (`releaseboard_report.py` `_ARTIFACT_HUES` comment, "the identical hue
     renders for a `failed` and a `passed` qa.md") — a gate is a status-shaped value, so the same
     rule applies with more force, not less. Fix: add one clause each to AC-2.1 and AC-3.1: (a) the
     gate label and the pipeline section render as plain headed text/lists — never a progress bar,
     step-tracker, filled-circle track, or any other device whose shape alone encodes sequence
     completion; (b) the gate label uses exactly one uniform badge/text treatment regardless of
     which of the six values it holds, mirroring the cadence-bar's "one class, one hue, for every
     bar regardless of value" rule (`_STYLE` `.cadence-bar` comment) and the artifact-hue-by-type
     precedent — if the five per-artifact status cells in the US-1 table reuse the existing
     `_ARTIFACT_HUES` (keyed to artifact type, already reviewed and shipped), that is fine and
     encouraged (see finding 6); the *gate* label specifically must not adopt a parallel six-hue
     palette of its own.

  2. **[Major] AC-3.2's wording ("no feature is currently at this stage") is sufficient honesty
     but not sufficient design guidance for the state every real reader will actually see: 5 of 6
     pipeline buckets empty on every render against this repo's real data today (A3/C8), with only
     `Released` populated.** Location: AC-3.2; US-3 (ux lens, state coverage — "empty state is
     designed, not a blank void"). Rule: Minimalism / visibility of status — a page where 83% of a
     section's buckets are empty-with-a-sentence risks reading as broken or half-implemented on
     first real render, precisely because A3 discloses this as the expected (not exceptional) real
     case for the entire remaining life of this feature until a second in-flight feature exists.
     The spec's own wording only prevents a *dishonest* empty state (blank/absent/bare `0`); it
     doesn't prevent a *visually alarming* honest one. Fix: add a sentence to AC-3.2 or NFR-4
     stating that an empty bucket renders with the **same structural weight** as a populated one —
     its own heading, same card/section chrome, same type scale — reusing this page's own existing
     `.empty-notice` idiom (already shipped for "no releases found," "none," and other honest-zero
     cases in `releaseboard_report.py`) rather than a dimmed, collapsed-by-default, or visually
     de-emphasized treatment that would make five real, correctly-computed buckets look like five
     rendering failures.

  3. **[Major] US-1's "one row per feature" table (AC-1.1/AC-1.5) has to fit a spec date, five
     artifact statuses (each with its own optional date and reason), and a delivered-in tag on one
     row — but no AC/NFR states how the 5-artifact status fits into cells narrow enough to survive
     NFR-4's own 375px no-horizontal-scroll bar, especially for the one case where a status cell's
     text is a full sentence, not a word.** Location: AC-1.1, AC-1.4, AC-1.5; NFR-4. Rule:
     Responsive layout / recognition over recall — this is the *exact* failure mode this project
     has already shipped and already fixed once: `release-board-docs qa.md` B1 found an unwrapped
     inline `<code>` span pushing the whole page sideways at 375px, fixed by adding
     `overflow-wrap`/`word-break`/`max-width` rules scoped specifically to the prose-bearing cells
     (`.doc-content p, .doc-content li` in `_STYLE`). AC-1.4's own "specific named reason" text for
     an unreadable `spec.md`, and the existing artifact-status reason strings this project already
     renders (e.g. the real `` `passed` — independent re-test... `` narrative status seen in
     `_strip_status_backticks`'s own docstring), are exactly the kind of longer free-text this new
     table will have to hold in five columns simultaneously, on one row, for every feature that hit
     a degrade path. Fix: add to NFR-4 that every cell in the new per-feature table — not just the
     already-covered `.doc-content` prose — gets the same wrap/`max-width` discipline before
     `/increment`, and recommend (not mandate, since this is a layout choice, not a new fact) that
     the 5-artifact status render as compact type+status badges with the reason surfaced only when
     status is null (which AC-1.4's own real data shows is the uncommon case), rather than reason
     text being shown unconditionally alongside a healthy status.

- **Accessibility notes:** NFR-4 already sets a real, falsifiable bar (single `<h1>`, real
  `<table>`/`<th>`, headed pipeline groups, WCAG AA contrast via `getComputedStyle`, keyboard
  parity by construction since no new interactive element is introduced, no horizontal scroll at
  375px) and needs no new AC to reach the constitution's §4 floor — it already matches or exceeds
  it. Two small, non-blocking additions worth folding alongside the findings above: (a) the new
  table's `<th>` elements should carry `scope="col"` explicitly, matching the convention already
  established in `_render_artifact_table`'s own header row, so a future implementer doesn't have to
  guess whether that attribute is this project's house style (it is); (b) the pipeline section's
  per-bucket headings (US-3) should sit at a heading level that nests correctly under this page's
  own `<h1>`/`<h2>` structure (mirroring `release-board-html`'s already-reviewed base-level
  discipline for embedded document headings), not left implicit until `/increment`.

- **Design risks & required changes:**
  1. Add an explicit anti-metaphor clause to AC-2.1/AC-3.1: no progress bar, step-tracker, or
     filled/unfilled dot-track for the gate label or the pipeline section; plain headed text/lists
     only (finding 1).
  2. Add a uniform-treatment clause to AC-2.1: the gate label uses one badge/text style regardless
     of value — no hue-per-gate palette — extending the shipped artifact-hue-by-type-never-status
     and cadence-bar-one-hue precedents to this new, sequence-shaped value (finding 1).
  3. Add an empty-bucket parity clause to AC-3.2: an empty pipeline bucket renders with the same
     structural weight (heading, chrome, type scale) as a populated one, via the existing
     `.empty-notice` idiom — never dimmed or de-emphasized relative to `Released` (finding 2).
  4. Extend NFR-4's wrap/`overflow-wrap` requirement, currently scoped to `.doc-content` prose, to
     every cell of the new per-feature table; recommend compact type+status badges with reason
     shown only when status is null (finding 3).
  5. Minor, non-blocking: `scope="col"` on the new table's `<th>`s, and a stated heading level for
     pipeline-bucket headings that nests under the page's existing hierarchy (accessibility notes).
  6. Minor, non-blocking, consistency win rather than a defect: the five per-artifact status cells
     in the new table should reuse the existing `_ARTIFACT_HUES` badge-by-type palette
     (`releaseboard_report.py`) rather than a new one — same action, same look, already reviewed
     and shipped.

  None of the above force a return to `/story-time` — every fix is a wording addition to an
  already-committed AC/NFR, not a new story or a scope change, matching exactly how
  `release-metrics`' own equivalent findings (its finding 3, the cadence-strip color risk this
  review's finding 1 generalizes) were folded without reopening its Design phase.

---

## ✅ SPEC GATE

*All boxes checked → `/sprint-plan` may start. Any box open → back to `/story-time` or `/look-and-feel`.*

- [x] Problem, goal and success signal are concrete — grounded in this repo's own real data (11
  features, `v0.1.0`–`v0.11.0`, the `release-board-docs`/`v0.10.0`/`v0.11.0` trailing case), not
  estimated
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must — US-1/US-2 Must, US-3 Should,
  with AC-3.4 pinning its severability
- [x] Non-functional requirements are stated and measurable, including a targeted NFR per each
  active lens (`cli` NFR-1, `library` NFR-2, `security` NFR-3, `ux`/accessibility NFR-4)
- [x] Clarify pass done: no ambiguity left unresolved or unparked — C1-C8 resolved by the PO
- [x] Open questions are resolved or explicitly accepted as risk — §3's A1-A5 are all resolved, none
  blocking
- [x] Out-of-scope section is filled — cycle time, AI cost, health verdicts, re-derived delivery
  rules, duplicated scope counts, a second `--format` value, and MCP exposure are all named,
  conscious cuts
- [x] Constitution respected, or conflicts recorded as open questions — §3/§6 (no verdict, no
  person-level data), ADR-0 (no re-derivation), ADR-4 (reproducibility), ADR-5 (offline) all honored
  by construction; no conflict found
- [x] Design review done for UI-facing features — run 2026-08-25 (§8): no Blocker; 3 Major findings,
  all folded into AC-1.1/1.4/1.5, AC-2.1/2.5, AC-3.1/3.2 and NFR-4 as wording additions (C9), no
  scope reopened
- [x] Status set to `approved` by the user — 2026-08-25, in conversation
