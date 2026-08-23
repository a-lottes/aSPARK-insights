# Spec: release-board-docs

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-23 |
| **Ticket** | none |

<!-- Handoff: read this block first, the numbered sections below by exception. -->

**Handoff**
- **Status:** `approved` (2026-08-23) — `/look-and-feel` design review complete (8 findings, no
  blockers, verdict "safe to proceed to `/sprint-plan`"), and the user gave explicit approval
  ("Approve, proceed") in conversation. Both remaining SPEC GATE boxes are now checked; the gate is
  closed.
- **Summary:** Two additive, directly-user-requested improvements to the shipped
  `release-board-html` (v0.9.0): (1) reorder its index newest-first; (2) let the maintainer read
  a selected artifact's actual full document content, not just its extracted status/date/reason,
  from the release board itself. Both render already-computed/already-on-disk data; nothing new
  is derived (ADR-0).
- **Open:** `2 open, both non-blocking` — A4 (single-file vs multi-file vs collapse-in-place
  architecture) and A5 (the resulting page/file-weight numeric ceiling), both explicitly accepted
  as risk and deferred to `/sprint-plan`'s technical judgment call, not resolved here per this
  project's "the spec contains no solutions" rule. The user explicitly confirmed they want the
  Engineering Manager to make the A4/A5 call at `/sprint-plan` rather than stating a preference
  now — A4/A5 stay exactly as written: open, parked, non-blocking. No Must-level acceptance
  criterion depends on either resolving a particular way.
- **Binding ruling:** §4 User Stories for what's committed; §3 for what isn't yet; §7 for what the
  PO resolved without escalating; §8 for the Designer's findings (none blocking).
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch
  at the next `/peer-review` and proceed.

## 1. Problem & Goal

- **Problem:** `release-board-html` (v0.9.0, shipped this session) already turns `insights
  releases`' JSON into one glanceable, offline HTML page — an index, per-release drill-down, and
  a 5-artifact status matrix (`spec`/`plan`/`review`/`qa`/`release`). The maintainer who just used
  it against this repo's real history names two concrete gaps, not hypothetical ones: (1) the
  index lists releases oldest-first, the opposite of how every changelog or Releases page (GitHub
  included) orders entries, so "what just happened" is at the bottom, not the top; (2) the status
  matrix answers *"is this artifact done"* but not *"what does it actually say"* — by
  `release-board-html`'s own deliberate design (its AC-2.1/AC-2.6, and `artifactstatus.py`'s own
  scope, AC-2.4 there: "only the header table... no other section of the free-form Markdown body
  is parsed, at all") a spec's problem statement, a review's findings table, a QA verdict's
  reasoning are still one editor or GitHub trip away — exactly the trip the release board was
  built to end for status, but explicitly not yet for content.
- **Goal:** Two independent, additive changes to the already-shipped release board: reorder its
  index newest-first, and let the maintainer read any existing artifact's real document content
  from the page itself. Neither recomputes anything the graph, git, or `build_release_map()`
  already answer — the reorder is a rendering-order flip over the same JSON; the content view is
  a new *read* of files this feature's own status matrix already opens today (just further than
  the header table).
- **Success signal:** Rendered against this repo today (9 real tags `v0.1.0`-`v0.9.0` plus the
  open pseudo-release window — 10 entries, confirmed from this repo's own `.git/refs/tags/`), the
  index's first row is the open pseudo-release window and its last row is `v0.1.0` — the exact
  reverse of today's shipped order. Selecting `release-board-html`'s own `review.md` from whichever
  release it lands under surfaces that file's real written content — its actual "Overall
  impression" prose and its 5 numbered findings — not merely the `Status: `approved``/`Date:
  2026-08-20` cells the shipped matrix already shows for it today.
- **Why now:** Both asks are direct, concrete reaction to a feature that shipped this same
  session — the cheapest, most trustworthy signal a PO gets: a real user reacting to real running
  software, not a hypothetical. If this never ships, nothing breaks — the shipped page and its
  JSON source are both complete and useful today, and the reordering gap is cosmetic, not a
  correctness bug. What weighs *for* building it now: the reorder is nearly free (no new data, a
  display-order flip); the content-view gap directly blocks this feature family's own stated goal
  — ending the "open a second tool" cycle — which v0.9.0 achieved for status but, by its own
  explicit scoping choice, not for content. What it displaces: the next cycle's worth of time that
  could instead go toward `release-board`'s own still-open, still-deferred A3 ("why" extraction
  from Clarifications/ADR prose) — a related, real alternative, not a false one.

## 2. Target Users

- **The maintainer, reading project history (concrete: Andreas)** — the same audience every prior
  release-board surface names, now reacting to the real page they just opened rather than a
  hypothetical one.
- **A future second maintainer onboarding (hypothesized, not yet observed)** — inherited unchanged
  from `release-board-html`'s own framing.

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | **Newest-first semantics — RESOLVED by the PO.** "Newest first" needs a precise, checkable definition, not just a direction. | The pseudo-release row (the open window since the latest tag) renders first, if present; every real tag follows in reverse tag-topology order (newest tag next, oldest tag last). This is a **rendering-order flip only** — `insights releases`' own JSON/`build_release_map()` list order is untouched (still oldest-tag-first, pseudo-release last), preserving ADR-0: no data is re-derived, only re-displayed. |
| A2 | **Full-document scope — RESOLVED by the PO.** Does "the contents of the individual documents" mean the same 5 files the status matrix already reads, or something broader? | Exactly the same 5 named artifacts already covered by the existing status matrix (`spec.md`/`plan.md`/`review.md`/`qa.md`/`release.md`) for each member feature. No new artifact type enters scope — not `constitution.md`, not `BACKLOG.md`, not source code, not commit diffs. |
| A3 | **Markdown construct coverage — RESOLVED by the PO, bounded deliberately.** Full CommonMark compliance is a materially larger, open-ended surface than this project's own artifacts need. | Bounded to constructs actually observed across this repo's real, shipped artifacts (confirmed by this pass's own read of `release-board-html/spec.md`, `release-board/spec.md`, and the constitution): ATX headings (`#`-`####`), pipe tables, bullet/numbered/checklist lists, bold/italic, inline code spans, fenced code blocks, HTML comments (`<!-- -->`, this project's own convention for internal notes — every observed `spec.md` opens with one), horizontal rules, links. An unrecognized construct degrades to visible plain text (AC-3.4), never dropped, never a crash. Not a claim of general-purpose Markdown-parser correctness. |
| A4 | **Single-file vs. multi-file vs. collapse-in-place architecture — OPEN, deliberately not resolved here.** This reopens a decision two prior specs made deliberately: `release-board`'s own A2 ("an index page with drill-down, not one file per release") and `release-board-html`'s inherited Out-of-Scope line, both explicitly ruling against per-release/per-feature files. | **Not resolved in this spec — parked for `/sprint-plan`'s Engineering Manager**, per this project's own rule that a spec contains no solutions. The PO's own independent read of the real tradeoff, grounded in this pass's own line-count survey (not an estimate — a direct `Grep` count across this repo's 9 shipped features' `.spark/*/{spec,plan,review,qa,release}.md`): **7,404 total lines** of raw artifact source across all 9 features combined (spec avg 262 lines, plan avg 123, review avg 108, qa avg 100 across the 8 features that have one, release avg 241); the single largest feature is `measurement-honesty` at **1,111 combined lines** across its 5 artifacts, and the single largest file is `measurement-honesty/spec.md` at **538 lines** — some individual table cells in this repo's own specs run into the thousands of characters on one unwrapped line (e.g. `release-board-html/spec.md`'s own A1 row). Three real candidate shapes, honestly weighed: **(a)** one giant single file embedding every document's full rendered body for every feature — the orchestrator's page-weight concern is real and grounded in these numbers, though a precise KB/MB verdict needs a rendered prototype, not a line count alone; **(b)** a `<details>`/native-HTML collapse-in-place single file — genuinely solves the *visual* glanceability concern (nothing shows until expanded, zero JS, one file, satisfies ADR-5 unchanged) but does **not** by itself reduce the file's on-disk size or DOM parse cost, since the collapsed content's bytes still ship inside the file — worth stating plainly, since it's not a full substitute for (c) on the weight axis, only on the initial-visual-overwhelm axis; **(c)** a genuine multi-file site (`index.html` + one file per feature or per artifact, still fully offline, relative `file://` links, no server) — does reduce per-view weight and DOM size, but is the literal reversal both prior specs ruled against, and a narrower middle ground exists worth naming: leave the already-shipped, already-Designer-reviewed index+drill-down page's *existing* content (tags, members, status matrix) architecturally untouched, and let only the *new* full-document-content capability spawn additional file(s) — smaller a reversal than a full multi-page site. `/sprint-plan` picks among these with the real numbers above as input. |
| A5 | **Page/file-weight numeric ceiling — OPEN, downstream of A4.** NFR-4 needs a concrete bound, but the right number depends on which shape A4 resolves to (one file's total weight vs. one file's weight when content is spawned elsewhere). | Not set in this spec. NFR-4 states the qualitative bar (bounded reads, disclosed truncation, no unbounded growth); the numeric ceiling is set at `/sprint-plan` once A4 is decided, and confirmed at `/demo-day` — not invented here without that context. |
| A6 | *(Accepted, inherited — not reopened.)* The aSPARK dark-theme visual language, the badge-hue-by-artifact-type rule (never by status), and the zero-JS static-anchor drill-down principle are already Designer-reviewed and shipped in `release-board-html` (v0.9.0). | Carries over unchanged for everything this spec doesn't itself touch. This spec's new asks (order, content-viewing) are additive; nothing here re-litigates A1/A3/A4/A5 from `release-board-html`'s own spec. |

## 4. User Stories

### US-1 (Must): Newest-first release ordering

> As the maintainer, I want the release board's index ordered newest-first — the open window at
> the top, the oldest tag at the bottom — so I see what just happened without scrolling past the
> whole project history first, matching the convention every changelog or Releases page already
> uses.

**Acceptance criteria:**

- [ ] AC-1.1: Given the same release set `insights releases`/`build_release_map()` already returns
  (today: 9 real tags plus the open pseudo-release window — 10 entries), when the HTML page is
  rendered, then the index lists the pseudo-release row first (if present), followed by every real
  tag in reverse tag-topology order (newest tag first, oldest tag last) — A1's precise definition,
  the exact reverse of `insights releases`' own JSON list order.
- [ ] AC-1.2: Given the same release set, when the per-release detail cards render below the
  index, then they appear in the identical newest-first sequence as the index — no mismatch
  between an index row's visual position and its corresponding detail card's position.
- [ ] AC-1.3: Given `--format json`, when the command runs, then stdout order is completely
  unaffected by this reversal — byte-for-byte the same order as before (oldest tag first,
  pseudo-release last). This is a rendering-only, HTML-view concern, never a re-derivation of the
  underlying release list's own order (ADR-0).
- [ ] AC-1.4: Given a release's own member list or a member's own 5-artifact status row, when
  rendered, then their internal ordering is untouched by this story — only the top-level release
  sequence (index and detail-card order) reverses; nothing below that level is in scope here.

### US-2 (Must): View a feature's full artifact document content

> As the maintainer, I want to open any feature's spec/plan/review/qa/release document and read
> its actual written content — not just the extracted status/date/reason — from the release board
> itself, so a click gets me the real story instead of a second trip to an editor or GitHub.

**Acceptance criteria:**

- [ ] AC-2.1: Given a member's artifact whose file exists on disk, when I select that artifact
  from the release board, then I can reach its full document content — every section (problem
  statement, acceptance criteria, findings tables, learnings, whatever the file actually contains)
  — not merely the header-table `Status`/`Date`/`reason` cells the existing 5-artifact matrix
  already shows, and without leaving to a separate editor, terminal, or browser tab.
- [ ] AC-2.2: Given an artifact file that does not exist (the existing "file not found" case) or
  exists but cannot be read (encoding error, permission error), when I try to view its content,
  then the release board states that plainly — the specific reason, never a raw traceback, never a
  blank or broken page, never a stale cached copy standing in for the real answer.
- [ ] AC-2.3: Given an artifact file that exists, is readable, and is empty (0 bytes), when I try
  to view its content, then the release board states that plainly (e.g. "this document is empty")
  — visually distinguishable from a read failure (AC-2.2) and from a genuinely large document,
  never an indistinguishable blank section.
- [ ] AC-2.4: Given any document's raw content, when rendered, then every character reaches the
  page only after passing through one canonical escape choke-point — mirrors the existing `_esc`
  discipline already proven for commit subjects and status strings, now extended to whole document
  bodies — so a hostile `<script>`- or event-handler-bearing string anywhere in a document's text
  renders as inert, visible text, never executes.
- [ ] AC-2.5: Given an artifact file larger than a stated bound (comfortably above today's largest
  real artifact, `measurement-honesty/spec.md` at 538 lines — see A4), when its content is read,
  then the excess is disclosed as truncated (a stated line/byte count shown) — never silently
  dropped, never causing an unbounded read.

### US-3 (Should): Structured, legible rendering of document content

> As the maintainer, I want a document's headings, tables, and checklists to render as real
> structured HTML rather than a raw dump of `#`/`|`/`[ ]` syntax, so a spec's acceptance-criteria
> table or a review's findings table is actually scannable, not just technically present.

**Acceptance criteria:**

- [ ] AC-3.1: Given a document's ATX-style headings, when rendered, then they appear as real
  heading elements, correctly nested underneath the page's own existing heading hierarchy — never
  introducing a second page-level `<h1>`, never skipping a level (constitution §4's "single
  `<h1>`, coherent nested hierarchy" bar — this is the new risk full-document embedding
  introduces, since a document's own top-level heading, e.g. `# Spec: <feature-name>`, must be
  demoted to fit rather than compete with the page's own `<h1>`).
- [ ] AC-3.2: Given a document's pipe-table blocks (e.g. a spec's Acceptance Criteria table, a
  review's findings table, a QA report's bug table), when rendered, then they appear as real
  `<table>`/`<th>` markup — never raw pipe-delimited text — mirroring this project's own "no
  `<div>` grids standing in for tabular data" bar, extended to embedded document content.
- [ ] AC-3.3: Given a document's checklist items (`- [ ]` / `- [x]`), when rendered, then checked
  and unchecked items are visually distinguishable from each other and from a plain bullet using a
  text-based cue, never color alone — matches the existing "no pass/fail judgment conveyed by
  color" bar (A3/NFR-5's precedent from `release-board-html`), so a checked item never reads as a
  green "good" verdict and an unchecked item never reads as a red "bad" one.
- [ ] AC-3.4: Given a Markdown construct this feature does not specially render (anything outside
  A3's bounded set — e.g. nested blockquotes, reference-style links, raw HTML tables), when
  encountered, then it degrades to plain, visible, readable text — never dropped silently, never a
  crash, never a broken render of the rest of the document.

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | CLI (lens) | No new CLI flag or subcommand for the reorder (still `insights releases --format html`). Whatever file(s) A4 resolves to, `--help` documents exactly what gets written under `--output` (names/count), per this project's day-one `--output` convention — the write-location contract stays explicit and escapable regardless of file count. `--format json` stdout is untouched by this feature entirely (AC-1.3). | /peer-review |
| NFR-2 | Security (lens) | Every character of every rendered document body — not just commit subjects and status/date/reason strings as before — flows through one canonical escape choke-point before reaching the page (AC-2.4). Verified with a hand-crafted hostile fixture embedding `<script>`/`onerror`-style content inside a document *body* (not just a status cell), per this project's adversarial-reproduction QA bar (CLAUDE.md). `--repo`/`--output` (and any additional output-path argument A4's resolution introduces) validated against the existing hostile-input checklist. | /peer-review + /demo-day |
| NFR-3 | Library (lens) | Any new export is additive only — no change to any existing export's signature or behavior. No new runtime pip dependency is added without being named and justified as an explicit, recorded deviation at `/sprint-plan` — matches this project's zero-new-dependency precedent across every prior HTML surface (`render.py`, `report.py`, `releaseboard_report.py`). | /peer-review |
| NFR-4 | Reliability / offline (ADR-5) | Every file this feature produces — whatever count A4 resolves to — is self-contained: no external font/script/image/stylesheet fetch, fully readable offline. Full-document reads are bounded (AC-2.5) so one pathologically large file cannot cause an unbounded read; content beyond the bound is disclosed as truncated, never silently dropped. The exact numeric page/file-weight ceiling is set once A4's shape is decided (A5) — not invented here without that context, but must be stated and verified before this feature ships. | /demo-day |
| NFR-5 | Accessibility / UX (lens) | Inherits the existing bar unchanged (single page-level `<h1>`, coherent nested heading hierarchy, real `<table>`/`<th>` for tabular data, WCAG 2.1 AA contrast, no status conveyed by color alone) — extended by AC-3.1/AC-3.3 to cover the new risk full-document embedding introduces (a document's own heading nesting into the page's hierarchy; checklist state never color-only). Verified via DOM heading-order inspection and `getComputedStyle`, the same techniques already established for this repo's prior HTML surfaces, never eyeballed. | /look-and-feel + /demo-day |
| NFR-6 | Reproducibility (§1) | Byte-identical render for a fixed set of on-disk artifact files and a fixed `HEAD`/tag set (inherits `release-board-html`'s own NFR-6 unchanged). Reading full document bodies from disk introduces no new source of non-determinism — file content is a fixed input the same way header-table extraction already was. | /peer-review + increment test |

## 6. Out of Scope

- **Rendering any file outside a feature's own 5 named artifacts** — not `constitution.md`, not
  `BACKLOG.md`, not source code, not commit diffs (A2).
- **General-purpose CommonMark/full Markdown-spec compliance** — bounded deliberately to the
  constructs this project's own artifacts actually use (A3); an unrecognized construct degrades to
  plain text (AC-3.4), never a crash.
- **Full-text search across document content** — a natural next ask the moment whole documents are
  embedded; consciously not built this cycle.
- **Syntax-highlighted code rendering** — this project's own artifacts are prose/tables, not source
  code blocks needing a highlighter.
- **Resolving the single-file vs. multi-file vs. collapse-in-place architecture question itself**
  — deliberately parked for `/sprint-plan` (A4), not decided in this spec.
- **Editing, annotating, or commenting on any `.spark/` artifact** — read-only, inherited from
  every prior release-board surface.
- **Any live-updating content, MCP exposure, cross-repo/fleet aggregation, or client-side
  sorting/filtering of the release list** — all inherited unchanged from `release-board-html`'s
  own Out-of-Scope section; none of this spec's asks reopen them.
- **A configurable or user-selectable visual theme/palette** — one shipped visual language,
  inherited unchanged (A6).

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-23 | Does "view the contents of the documents" mean the full document body, or just the Handoff block already summarized elsewhere? | **Resolved by the PO, not escalated.** Full document body (A2) — the user's phrasing contrasts explicitly with the current status-table-only view, and the Handoff block is already effectively summarized by the existing status/date/reason fields; a "read the top only" mode wouldn't add real new value over what's already shipped. |
| C2 | 2026-08-23 | Should full-document rendering ship with structured HTML (headings/tables/checklists) or plain escaped text on day one? | **Resolved by the PO, not escalated.** Split into a Must (US-2: minimum legible full-content access, even as plain escaped text) and a Should (US-3: structured rendering) — smallest-slice discipline; the Must alone delivers real value even if the Should is deferred to a later pass. |
| C3 | 2026-08-23 | Does the newest-first reversal change `insights releases`' JSON order, or only the HTML view's display order? | **Resolved by the PO, not escalated (A1/AC-1.3).** Display-order only; JSON output is untouched — no re-derivation of the underlying order (ADR-0). |
| C4 | 2026-08-23 | Which Markdown constructs must render specially, given full CommonMark compliance is a much larger surface than this project needs? | **Resolved by the PO, not escalated (A3).** Bounded to constructs actually observed across this repo's own shipped artifacts; everything else degrades to plain text (AC-3.4), never a crash. |

## 8. Design Review

<!-- Filled by /look-and-feel, Specify-phase pass against the spec. No running page exists yet;
     `releaseboard_report.py` (the shipped release-board-html v0.9.0 renderer) was read for
     concrete grounding on heading depth, existing CSS vocabulary, and the anchor/back-link
     mechanism this spec extends. A6 (visual language) is not reopened. -->

- **Overall impression:** The two Must stories are individually sound and additive — the reorder
  (US-1) is a pure display-order flip with no data re-derivation (ADR-0 respected), and the
  content-view story (US-2) correctly identifies its own hardest risk up front (AC-3.1's heading
  competition). The design gap isn't in what's committed, it's in what the spec leaves silent:
  reading several hundred lines of a document's own prose *inside* an already status-dense page
  needs its own wayfinding, its own visual identity distinct from the badge/table vocabulary, and
  a heading-depth budget that the page's own existing structure (already 4 levels deep before a
  byte of document content appears) makes tighter than AC-3.1 as written accounts for. None of
  this reopens A4/A5 or any SPEC GATE box — every finding below is either a small addition to an
  existing AC/NFR or an implementation note for `/increment`.

- **Findings:**

  1. **[Major] The shipped page's lead sentence will become false the moment US-1 ships, and no
     AC names fixing it.** Location: `releaseboard_report.py:358`
     (`f'<p class="lead">{len(releases)} {count_word}, oldest first.</p>'`); AC-1.1-1.4. Rule:
     Match the real world — the very first line of body text on the page would openly contradict
     its own newly-reversed visual order. Fix: add a line to US-1 (or fold into AC-1.1) requiring
     that user-facing copy describing list order — this lead sentence, and any other future
     occurrence — is updated to match the new order. Cheap, but easy to miss precisely because it
     lives in prose text, not in the JSON data the ACs otherwise check.

  2. **[Major] Heading-depth budget: the page's existing structure already spends 4 levels
     (h1 page → h2 release → h3 "Members" → h4 member name) before any embedded document content
     begins, and A3 bounds embedded documents to 4 more ATX levels (`#`-`####`).** Location:
     AC-3.1, A3; `_render_release_detail`/`_render_member_block` in `releaseboard_report.py`. Rule:
     Accessibility — coherent nested heading hierarchy (constitution §4). If a document's own top
     heading demotes to h5/h6 per AC-3.1's instruction, native HTML has no level below h6 for the
     document's remaining `##`/`###`/`####` — three distinct source levels would collapse onto the
     same h6, which isn't a "skip" but *is* a flattening that defeats "coherent nesting" and would
     mislead a screen reader's heading-outline navigation (a document's H1/H2/H3/H4 all reading as
     identical h6s). Fix: name the concrete mapping before `/increment` — either (a) `role="heading"
     aria-level="7"`/`"8"`/`"9"` for the deeper levels (a standard, widely-supported technique for
     depths beyond native h6), or (b) explicitly demote the deepest embedded level to non-heading
     styled text once the native ceiling is hit, rather than forcing it to fake-flat h6. Leaving
     this unstated risks an ad hoc "everything is h6" choice at `/increment` that silently fails
     AC-3.1's own promise.

  3. **[Major] No visual framing distinguishes "the board's own extracted status" from "the
     artifact's own raw prose," and a document's own words can contain status-shaped text.**
     Location: US-2, AC-2.1. Rule: Match the real world / minimalism — a reader must be able to
     tell instantly whether they're looking at Insights' judgment or the document's own sentence.
     A QA report's prose can itself contain the string "Status: failed" mid-paragraph; without a
     distinct container, that risks being misread as another status-matrix verdict rather than
     historical document text. Fix: give embedded document content its own visually distinct
     frame — a differently-toned card plus a persistent label ("Document content — read-only, as
     extracted from `<path>`") at the top of every embedded block — reusing the page's existing
     card vocabulary but never visually identical to `.release-card`/the artifact-status table.

  4. **[Minor] No reading-width constraint for embedded prose.** Location: US-2/US-3; the existing
     `--maxw: 1200px` single-column container (`releaseboard_report.py` `_STYLE`). Rule:
     Typography — sane line length (visual craft). Tables and index rows read fine at full width;
     several hundred lines of prose paragraph at ~1200px in body-size Inter will run well past a
     comfortable ~60-90 character line length. Fix: constrain embedded document *paragraphs*
     specifically (not tables/code within the document) to a narrower column, e.g. `max-width:
     70ch`, inside the content frame from finding 3.

  5. **[Major] AC-2.5's truncation disclosure has no named UI treatment — the spec states this
     itself.** Location: AC-2.5. Rule: Visibility of status / consistency. Fix: reuse the existing
     `.truncation-note` idiom already shipped for members/unattributed lists ("Showing the first N
     of M") rather than inventing a new "read more"/expand affordance — cheapest, most consistent
     choice, and needs no JS regardless of which A4 shape wins. Worth stating explicitly so
     `/increment` doesn't reinvent it or leave it ambiguous.

  6. **[Major] AC-3.3's "no color alone" checklist rule is a constraint with no concrete design
     answer.** Location: AC-3.3. Rule: Accessibility / consistency with the existing "always a text
     label, never color alone" badge precedent (A3/NFR-5). Proposed fix: render `- [x]`/`- [ ]` as
     real, non-interactive `<input type="checkbox" checked disabled>` / `<input type="checkbox"
     disabled>` elements — native browser-drawn check semantics carry state without relying on
     color, match the maintainer's existing mental model (identical to GitHub's own checklist
     rendering), and extend this page's existing "text label, not color" precedent to native form
     controls rather than a bespoke glyph. If a `disabled` input reads as too close to "editable"
     for a read-only page, the fallback is a text-prefixed glyph pair (`☑`/`☐`, `aria-hidden`) with
     a visually-hidden "checked"/"unchecked" prefix — either is acceptable, but one should be named
     before `/increment` rather than left open.

  7. **[Minor] Table caption uniqueness at scale.** Location: AC-3.2, NFR-5. Once documents' own
     pipe-tables render as real `<table>`/`<caption>` markup, a single release/member section could
     carry several tables (the existing artifact-status matrix plus a spec's AC table, a review's
     findings table, a QA's bug table — potentially per member). Rule: Accessibility — screen-reader
     table-list navigation relies on distinct captions. Fix: source an embedded table's caption from
     its nearest preceding heading text (e.g. "Acceptance Criteria") rather than a generic label; if
     that's not feasible, state explicitly that embedded document tables omit `<caption>` (caption
     isn't mandatory) rather than leaving the choice ambiguous.

  8. **[Major] No stated "how do I get back" affordance from inside an embedded document,
     distinct from the release-level one already shipped.** Location: AC-2.1, US-2;
     `.back-link`/`&larr; Back to index` in `releaseboard_report.py`. Rule: User control. The
     shipped page already solves release→index; nothing yet solves "I'm 400 lines into a spec's
     content — how do I get back to the member's status row or the release I came from," which
     matters more now that US-1's reorder means a reader's position in a 10-and-growing list is
     easy to lose after a long embedded read. Fix: extend the identical zero-JS anchor pattern —
     each embedded document block carries its own back-link to its member/release anchor (not just
     to `#index`), reusing `.back-link`'s existing style and mechanism verbatim.

  - **Design-consequence note for A4 (not a ruling — the Engineering Manager's call):** among the
    three candidate shapes named in A4, only (b) `<details>` collapse-in-place avoids a navigation
    event entirely — no lost scroll position, no separate back-affordance needed at all, and best
    satisfies "not overwhelming by default" at today's real content volumes (538 lines for the
    largest single artifact). Shapes (a) single-giant-file and (c) multi-file both introduce a real
    page-load-then-jump or file-to-file navigation cost that findings 3, 5, and 8 above exist
    specifically to mitigate. Whichever shape wins, those three findings still apply.

- **Accessibility notes:** Contrast/palette are inherited unchanged from `release-board-html`'s own
  §8 (not reopened). The new accessibility surface this spec introduces is heading depth (finding
  2), checklist state without color (finding 6), and table-caption distinctness at higher table
  counts (finding 7) — all named above. Keyboard operability is satisfied by construction: the
  content-view mechanism, whatever A4 resolves to, is expected to stay within native anchor links
  or native `<details>`/`<summary>` (both natively keyboard-operable, no custom widget), consistent
  with `release-board-html`'s own "zero JS, native elements only" precedent — worth a one-line
  confirmation at `/peer-review` once A4 is decided, not a new finding here.

- **Design risks & required changes:**
  - **Before `/increment` starts (needs a named answer, not new scope):** findings 2 (heading-depth
    mapping), 6 (checklist treatment), and 5 (truncation UI) — each is a concrete design decision
    this spec currently leaves implicit; naming one of the proposed options is enough.
  - **Fold into existing AC/NFR wording, safe for `/increment`:** findings 1, 3, 4, and 8.
  - **Nice-to-have, non-blocking:** finding 7.
  - **No finding is a blocker and none reopens US-1/US-2/US-3, A1-A6, or the SPEC GATE.** Nothing
    above asks for new scope, JS, or a themeable palette; the design direction is sound enough to
    proceed to `/sprint-plan`.

---

## ✅ SPEC GATE

*All boxes checked → `/sprint-plan` may start. Any box open → back to `/story-time` or `/look-and-feel`.*

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone") — grounded in
  this repo's real, current tag list (9 tags + pseudo-release) and a real example
  (`release-board-html/review.md`'s own content)
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must — US-1/US-2 Must, US-3 Should
  (deliberately deferrable polish, per the smallest-slice discipline in C2)
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason)
- [x] Clarify pass done: no ambiguity left unresolved or unparked — C1-C4 resolved by the PO; A4/A5
  are the one genuine architecture ambiguity, explicitly parked in §3, not silently absorbed
- [x] Open questions are resolved or explicitly accepted as risk — A4 (architecture shape) and A5
  (weight ceiling) are explicitly accepted as risk, deferred to `/sprint-plan`'s technical
  judgment; no Must AC depends on either resolving a particular way
- [x] Out-of-scope section is filled (something was consciously cut) — full-text search, general
  CommonMark compliance, and the architecture decision itself are all named, conscious cuts
- [x] Constitution respected, or conflicts recorded as open questions — no conflict; ADR-0 (no
  re-derivation), ADR-5 (offline, whatever the file count), the zero-new-dependency library
  precedent, and the accessibility heading-hierarchy bar are all honored and, where a new risk is
  introduced (document heading nesting), named explicitly rather than assumed away
- [x] Design review done for UI-facing features (or marked N/A with reason) — done. `/look-and-feel`
  pass complete against this spec: 8 findings (5 Major, 3 Minor), no blockers, verdict "safe to
  proceed to `/sprint-plan`"
- [x] Status set to `approved` by the user — done. User approved in conversation ("Approve,
  proceed"), including A4/A5's explicit deferral to `/sprint-plan`'s Engineering Manager
</content>
</invoke>
