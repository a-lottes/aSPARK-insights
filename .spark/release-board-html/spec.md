# Spec: release-board-html

| | |
|---|---|
| **Phase** | Specify |
| **Owner** | Product Owner (`/story-time`), Designer (`/look-and-feel`) |
| **Status** | `approved` |
| **Date** | 2026-08-19 |
| **Ticket** | none |

<!-- Handoff: read this block first, the numbered sections below by exception. -->

**Handoff**
- **Status:** `approved` (2026-08-19) — third `/story-time` pass (gate close): all open questions
  resolved (A1/A3/A4 in the prior pass; A5 sourced, its remaining logo-embedding step reclassified
  as `/increment`-time implementation work, not an open question); Design Review (§8) filled by a
  real `/look-and-feel` pass, verdict "sound, safe to proceed." User gave explicit approval
  ("ja, freigeben") in chat. Gate closed. Ready for `/sprint-plan`.
- **Summary:** A self-contained, offline HTML companion to `insights releases`' JSON (release-board,
  v0.8.0, shipped) — one index of every release, real and the open pseudo-release window, with
  drill-down into each release's members and their 5-artifact status, rendering that JSON verbatim
  and computing nothing new.
- **Open:** `0 open` — A1, A3, A4 resolved this cycle's second pass; A5 sourced (the 2182×721 PNG
  logo asset is downloaded into the repo), its inline-embedding step deferred to `/increment` as
  normal implementation work, not a remaining open question. A2 was always a named constitutional
  constraint, not a live question.
- **Binding ruling:** §4 User Stories for what's committed; §3 for what isn't yet; §7 for what the
  PO resolved without escalating.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch at
  the next `/peer-review` and proceed.

## 1. Problem & Goal

- **Problem:** `release-board` (v0.8.0, shipped) already collapsed the real reconstruction problem —
  reading 5-6 files across N feature directories plus raw `git log`/`git tag` by hand — into one
  JSON call. That pain is genuinely solved. What's left is smaller and more specific: reading that
  JSON to answer "what shipped, and what's each artifact's status" still means piping through `jq`
  or scrolling a moderately nested structure by eye; there is no way to glance at this project's
  release history the way `insights render`'s own HTML scorecard already lets you glance at a
  point-in-time metrics snapshot (I5, shipped). Concretely, this repo today has **8 real tags**
  (`v0.1.0`-`v0.8.0`, confirmed from this repo's own `.git/refs/tags/`) plus one open pseudo-release
  window — small enough to read as JSON today, but the exact "glanceable HTML view" gap release-
  board's own spec named and deferred (§6/§8, A2: "an index page with drill-down," resolved in
  shape but not built).
- **Goal:** One self-contained, offline HTML page — an index of every release (each real tag, plus
  the trailing pseudo-release for the open window since the latest tag) with drill-down into each
  release's member `.spark/<feature>/` directories, their 5-artifact status (`spec`/`plan`/`review`/
  `qa`/`release`), and unattributed commits — rendering `insights releases`' own JSON verbatim.
  Nothing is recomputed; this is a rendering layer only, the same "shared core, two thin adapters"
  discipline already used for `render.py` and the MCP server.
- **Success signal:** Rendered against *this* repo today, the page lists all **9 entries** — the 8
  real tags plus the pseudo-release — in `insights releases`' own order. `v0.3.0`'s row drills down
  to its real **3 members** (`traceability-metrics`, `public-repo-polish`, `mcp-server` —
  independently hand-verified in release-board's own spec, AC-1.2); `v0.7.0`'s row drills down to
  its real **1 member** (`git-native-mid-cycle-board`). Commit `26e7f95`'s real subject ("feat: snapshot-
  report scorecard redesign — cards, confidence mix, full table, v0.6.0") appears in its release's
  `unattributed` list, never mis-attributed to `snapshot-report` by matching that text against a
  directory name — release-board's own adversarial AC-1.3 guarantee, which this rendering layer must
  not silently lose. The pseudo-release row shows the honest, live commit count since `v0.8.0` —
  **2, as of this spec's drafting** (`a5f43be`, `9b25f35`, both `.spark/release-board/` bookkeeping)
  — matching `insights releases`' own JSON byte-for-byte, expected to differ on a later run whose
  `HEAD` has moved, exactly as release-board's own NFR-7 already scopes.
- **Why now — argued honestly:** If this is never built, nothing breaks: the JSON is complete,
  scriptable, and already solves the harder problem (release-board's own). This is explicitly the
  smaller, "last mile of glanceability" feature release-board's own spec named and deferred, not an
  urgent one — the PO states that plainly rather than inflating the case. What weighs *for* building
  it now: (a) release-board's own A2 already resolved the shape informationally, naming this as the
  next step rather than an open design question; (b) nothing else in the backlog is currently
  unblocked and ready — I3/I4/I6/I8/I9 each wait on a graph feature or an external decision this
  repo doesn't control, and I5's offline-HTML pattern already exists and is shipped, so this is a
  direct, low-risk extension of proven infrastructure rather than a new pattern. What it displaces:
  the next cycle's worth of time that could instead go toward finishing release-board's own deferred
  A3 (the "why" extraction, still open, still non-blocking) — a real but not more urgent alternative.

## 2. Target Users

- **The maintainer, skimming project history (concrete: Andreas)** — the same audience release-
  board itself names, in the same modality shift `insights render` already made for metrics: from
  "run a command and parse JSON" to "open a file and look."
- **A future second maintainer onboarding (hypothesized, not yet observed)** — named as a hypothesis
  only, exactly as `git-native-mid-cycle-board` and `release-board` both named their own.

## 3. Assumptions & Open Questions

| # | Assumption / Question | Resolution |
|---|---|---|
| A1 | **Visual-language choice — RESOLVED.** The PO's original framing offered a binary choice: reuse the shipped report's `.metric-card`/`.metric-bar`/`.confidence-mix`/`.table-wrap` vocabulary, or adopt a "retro newsroom CMS dashboard" language from a reference mockup (dark masthead, serif headings, black/cream/red accent). The user rejected both options, verbatim: *"Moderner look der zu dem logo und https://aspark.lottes.dev (wewbseite) passt"* — a modern look matching the logo and the real, live aSPARK marketing website. That site is now the actual design reference; the retro-newsroom mockup is superseded and no longer a candidate direction. | **Resolved — match the real, live aSPARK brand site's current visual language**, verified by direct computed-style inspection of https://aspark.lottes.dev (a real, concrete reference, not a guess or a recreation from memory). Full token set extracted and recorded here (completes the gap `/look-and-feel` flagged in §8 finding 1): **Backgrounds** — `--bg-primary #0a0a0f`, `--bg-secondary #12121a`, `--bg-tertiary #1a1a2e`, `--bg-card #16162a`. **Accents** — `--accent-teal #3abdb0` (primary), `--accent-teal-light #5cd6ca`, `--accent-orange #e8623a`, `--accent-orange-light #f07a56`, `--accent-green #00b894`, `--accent-amber #fdcb6e`, `--accent-violet #a29bfe`. **Text** — `--text-primary #f0f0f8`, `--text-secondary #a0a0c0`, `--text-muted #6c6c8a`, `--text-light #dde0ed`. **Borders** — `--border-subtle rgba(58,189,176,0.15)`, `--border-active rgba(58,189,176,0.4)`, `--border-line rgba(255,255,255,0.09)`. **Radii** — `--radius-sm 8px`, `--radius-md 16px`, `--radius-lg 24px` (pill controls use 100px). **Typography** — Inter for all UI text (900-weight H1 / ~66.56px, 800-weight H2 / ~46.08px, 700-weight buttons/badges); `JetBrains Mono` reserved for mono/metadata strings (code/hash/technical values), never body prose. **Badge-hue availability for A3:** beyond `--accent-teal`, the extracted palette names exactly 4 further non-neutral accent hues (`--accent-orange`, `--accent-green`, `--accent-amber`, `--accent-violet`) — 5 distinct hues total, enough to key each of A3's 5 artifact types (`spec`/`plan`/`review`/`qa`/`release`) to its own consistent color. Which hue goes to which artifact type is an `/increment`/`/sprint-plan`-time assignment, not a spec-level decision — this row only confirms 5 real, non-judgment-color hues exist and are named to draw from. **Binding contrast-scoping rule** (a concretization of NFR-5's existing 4.5:1-normal-text/3:1-large-text-or-non-text bar for this specific token pair, not a new requirement): `--text-muted` (#6c6c8a) measures ≈3.90:1 on `--bg-primary` and ≈3.51:1 on `--bg-card` — it clears the 3:1 large-text/non-text floor but fails the 4.5:1 normal-text floor. `--text-muted` may therefore only be used for large text (≥24px regular, or ≥19px bold) or non-text decorative elements (e.g. a metric bar, a border) — never for small body text, artifact `reason` strings, commit subjects/hashes, or any other string that must clear the 4.5:1 floor. `--text-secondary` (#a0a0c0, ≈7.8:1 on `--bg-primary`) is the floor color for any small/body text needing full AA compliance; `--text-primary` and `--text-light` clear it by a wider margin still. Translating these tokens into this page's concrete CSS remains `/look-and-feel`'s/`/increment`'s job, not this spec's — this row records the reference and the binding constraint, not the stylesheet. |
| A2 | **Liveness boundary.** The reference image's whole premise is a *live* operations dashboard — a scrolling ticker, a "readers right now" figure, writer-presence indicators, a live countdown clock. ADR-4 forbids any `datetime.now()`/ambient-clock read anywhere in the derivation path, and every HTML surface shipped so far in this repo renders once from a snapshot and never updates in place (the exact reasoning `git-native-mid-cycle-board`'s own spec used to scope ARIA live regions out: "the page renders once... so there is nothing to announce"). | **Accepted — a constitutional constraint, not a live open question, named explicitly since the brief's premise conflicts with it.** The visual language (typography, palette, density, card/badge styling) may be borrowed from the reference (now the real aSPARK site, per A1); its *liveness* (motion, presence, a self-updating clock) may not. Neither the PO nor the user can waive this without amending the constitution. |
| A3 | **Badge color vs. the no-judgment-color rule — RESOLVED.** Newsroom/CMS-style badge systems typically color-code by urgency precisely to signal "this needs attention" — but constitution §3's off-limits ("no pass/fail, staleness, or health judgment... Insights measures, `aspark-ci` enforces") and `git-native-mid-cycle-board`'s own already-shipped AC-4.3 ("no red/green pass-fail coloring that implies a judgment... status is conveyed as text, not a verdict hue") together forbid exactly that instinct — a `qa.md` status of `failed` may never render in a color that reads as "bad," a `passed` never in one that reads as "good." | **Resolved — "Farbe nur nach Artefakt-Typ, nie nach Status"** (color only by artifact type, never by status), the user's explicit ruling. The 5 artifact-type badges (`spec`/`plan`/`review`/`qa`/`release`) may each carry a distinct, consistent hue keyed to *which artifact type they are* — e.g. `spec` always one color, `qa` always another — but the *status value* inside a given artifact (`approved` vs `draft` vs `failed`, or null) never changes that badge's hue. Note, for the record: the real aSPARK site's own product-status badges (Live/Frühphase/Geplant/Zukunft — found during A1's token extraction) *do* vary color by state, but that precedent is about product lifecycle stage, a different axis from this feature's artifact status, and the user's ruling here is intentionally stricter. NFR-5's existing "no judgment hue" language already covers this and is unchanged by this ruling — it is a specific instance of that rule, not a new one. |
| A4 | **Drill-down mechanism — RESOLVED.** Release-board's own A2 resolved the *shape* ("an index page with drill-down") but not the *mechanism*. | **Resolved — "Statische Anker, kein JS (Empfohlen von PO)"**, confirming the PO's own original default recommendation. Static, same-document `#`-anchor navigation, zero JavaScript: the index links to each release's detail rendered below it on the same page, matching `git-native-mid-cycle-board`'s own "no executable JS at all" precedent (AC-4.1) rather than reopening the keyboard-operability/motion questions that precedent already settled. An interactive expand/collapse widget is confirmed cut (§6), not merely a PO default. |
| A5 | **Logo asset — RESOLVED (sourced; embedding deferred to `/increment`).** No aSPARK logo (teal 'a' + white 'SPARK' wordmark, orange triangle accent) previously existed as a file anywhere in this repo. | **Resolved.** `assets/aspark-logo-dark.png` (2182×721 PNG, 126KB) has been downloaded into the repo, sourced from `https://github.com/a-lottes/aSPARK/blob/main/assets/aspark-logo-dark.png?raw=true` per the user's own reference. Embedding it inline (AC-1.4, ADR-5) — including the resize/re-compress step Design Review finding 5 (§8) flags — is `/increment`-time implementation work, not a remaining spec-level open question; the asset itself is no longer missing. |
| A6 | *(Accepted, inherited — not reopened.)* No independent `BACKLOG.md` entry names this feature either, the same structural question release-board's own A1 asked. Inherits that ruling ("yes, in `aspark-insights`") rather than re-litigating it (C3). |

## 4. User Stories

### US-1 (Must): Self-contained index of every release

> As the maintainer, I want one HTML page listing every release — tagged and the open pseudo-
> release window — at a glance, so I can see the shape of this project's history without parsing
> JSON by hand.

**Acceptance criteria:**

- [ ] AC-1.1: Given this repo's real `insights releases` output (today: 8 real tags, `v0.1.0`-
  `v0.8.0`, plus the trailing pseudo-release — 9 entries), when the page is rendered, then the index
  lists exactly one row per entry, in the same order `insights releases` returns them (oldest real
  tag first, pseudo-release last) — no row computed, reordered, or filtered independently of that
  order.
- [ ] AC-1.2: Given a real release's row, when rendered, then it shows the tag string, its member
  count, and its unattributed-commit count, each read from `members`/`unattributed`'s list lengths
  as returned — never a separately recomputed count.
- [ ] AC-1.3: Given the pseudo-release's row (`tag: null`), when rendered, then it is distinguished
  from every real-tag row using the JSON's own `tag: null` discriminator (never inferred from row
  position), and its reused `commits`/`branches`/`days_since_tag`/`work_types` figures (from
  `build_board()`, per release-board's own AC-1.8) are shown as-is — e.g. today, exactly 2 commits
  since `v0.8.0` — never recomputed a second way.
- [ ] AC-1.4: Given the page, when opened offline with no network connection, then it renders fully
  — no external font, script, image, or stylesheet fetch (ADR-5, matching every prior HTML surface
  in this repo) — and, if the aSPARK wordmark is present per the design brief, it is embedded inline
  (e.g. inline SVG or a `data:` URI), never fetched from an external URL (A5).

### US-2 (Must): Per-release drill-down detail

> As the maintainer, I want to see a release's full member and artifact-status detail without
> leaving the page or re-running the CLI, so a skim can become a real answer without a second tool
> call.

**Acceptance criteria:**

- [ ] AC-2.1: Given any release row on the index, when I follow its link, then I reach that
  release's full detail on the same self-contained page (a same-document navigation, never a second
  file or a network request), listing every member's name and its 5-artifact status map (`spec`/
  `plan`/`review`/`qa`/`release`) — each artifact's literal extracted `status` string exactly as
  release-board returned it, its `date` if present, and its `reason` when `status` is null.
- [ ] AC-2.2: Given `v0.3.0`'s real 3 members (`traceability-metrics`, `public-repo-polish`,
  `mcp-server`), when I drill into `v0.3.0`, then all three appear, each with its own 5-artifact
  status row — never truncated or summarized away at this release's size.
- [ ] AC-2.3: Given `v0.7.0`'s real single member (`git-native-mid-cycle-board`), when I drill into
  `v0.7.0`, then exactly one member row appears — no phantom second row, no pluralization defect
  implying more than one.
- [ ] AC-2.4: Given a release's `unattributed` list, when I drill into it, then every entry's hash
  and subject are shown verbatim — e.g. commit `26e7f95`'s real subject appears in its release's
  unattributed list, never re-attributed to `snapshot-report` by matching that text against a
  directory name (release-board's own AC-1.3 guarantee must survive the rendering layer unchanged).
- [ ] AC-2.5: Given a release (real or pseudo) whose `unattributed` list is empty, when I drill into
  it, then the section states "none" explicitly — never silently absent, never conflated with an
  artifact's null-with-reason state.
- [ ] AC-2.6: Given a member's artifact status whose extracted value carries Markdown code-span
  backticks around it (this project's own convention: every observed header table wraps its
  `Status` cell in `` `…` ``, e.g. `` `approved` ``, confirmed from every shipped `spec.md`/`plan.md`
  in this repo, and from `artifactstatus.py`'s verbatim, unstripped extraction), when displayed,
  then the decorative backticks are stripped for legibility — a presentation-only cleanup, never a
  data change — while the underlying value is otherwise shown exactly as extracted, never re-
  interpreted or mapped onto a different vocabulary.

### US-3 (Must): Honest empty and degenerate states, never a crash

> As the maintainer, I want the page to degrade honestly on a repo with no tags or no commits since
> the last one, so it never crashes and never fabricates a release that doesn't exist.

**Acceptance criteria:**

- [ ] AC-3.1: Given a repo with zero tags (release-board's own `reason: "repository has no tags"`
  case), when the page is rendered, then it states that reason in words, shows an empty index (no
  rows, no pseudo-release — release-board itself never emits one without at least one real tag), and
  never shows a raw traceback, a blank page, or a placeholder row (constitution §6).
- [ ] AC-3.2: Given the pseudo-release with zero commits since the latest tag (release-board's own
  AC-1.9 honest-zero case), when rendered, then its row and detail state a true zero ("nothing has
  landed since `<tag>`") — never a null card, never an omitted row.
- [ ] AC-3.3: Given any artifact status that is `null` with a reason (a missing file, an unparseable
  header table — release-board AC-2.2/2.3), when rendered, then the reason is shown in words next to
  the artifact's badge — never a blank cell, never a guessed status.

## 5. Non-Functional Requirements

| # | Category | Requirement (measurable) | How it's verified |
|---|---|---|---|
| NFR-1 | CLI (lens) | `insights releases` gains `html` as a legal value for its existing `--format` flag (already reserved for exactly this in the shipped CLI: `choices=("json",)`, a single-value enum left open) and a new `--output` flag for the write location, documented in `--help`, following this project's day-one `--output` convention. `--format json`'s existing byte-for-byte stdout output is unchanged (no breaking change); exit codes and error classes (`GitUnavailableError`, `SparkDirUnreadableError`, `InvalidAsOfError`, …) are unchanged from release-board's own — no new failure taxonomy invented for the same underlying failures. | /peer-review |
| NFR-2 | Security (lens) | Every commit subject and every extracted artifact `status`/`date`/`reason` string is attacker-influenceable content (a commit message or a hand-edited header-table cell can carry arbitrary text) and must flow through one canonical HTML-escape choke-point before reaching the page — mirrors `render.py`'s existing `_esc()` precedent and this project's own adversarial-reproduction QA bar (CLAUDE.md); a hostile `<script>`-bearing commit subject or status cell renders as inert text, never executes. `--repo`/`--output` validated against the §4 hostile-input checklist before use. No new runtime dependency introduces a supply-chain surface. | /peer-review + /demo-day |
| NFR-3 | Library (lens) | Any new export (e.g. a `render_release_board()` function) is additive only — no change to any existing `build/query/render/diff/verify/serve/board/releases` export's signature or behavior. Zero new runtime pip dependencies. | /peer-review |
| NFR-4 | Reliability / offline (ADR-5) | The rendered page is a single, self-contained file — no external font, script, image, or stylesheet fetch, matching every prior HTML surface in this repo. Handles the current real dataset (9 entries, up to 3 members in one release) and a materially larger one without an unbounded read or a broken layout; a member or unattributed list beyond a stated bound is disclosed as truncated, mirroring `git-native-mid-cycle-board`'s NFR-4 fixed-N-with-disclosure precedent, rather than silently growing the page without limit. | /demo-day |
| NFR-5 | Accessibility / UX (lens) | Bar inherited, not restated, from `git-native-mid-cycle-board`'s already-shipped precedent: real `<table>`/`<th>` (or an equivalent named, programmatic field/value-pairing mechanism) for the 5-artifact status matrix (constitution §4); WCAG 2.1 AA contrast (4.5:1 text, 3:1 non-text) on every color pair the page ships, including any newly introduced per A1's resolution (the real aSPARK brand palette) — measured via `getComputedStyle`, never eyeballed; no status/badge is conveyed by color alone (a text label always accompanies it), and **no color implies a pass/fail or health judgment on any artifact's own recorded status** — extends `git-native-mid-cycle-board`'s AC-4.3 "no judgment hue" guarantee to the artifact-status badges this feature introduces, and is the exact rule A3's "color by type, never by status" ruling instantiates. At 375px viewport width, no horizontal page scroll (`innerWidth`/`scrollWidth`/`clientWidth`). State coverage per the `ux` lens: an honest empty state (AC-3.1), a true-zero state (AC-3.2), a null-with-reason state (AC-3.3) — loading/error/success/form states are N/A (a static, one-time render with no user input or async action). The drill-down mechanism (A4: static `#`-anchors, zero JS) carries no interactive control beyond native anchor links, so keyboard-operability is inherited from the browser's own link handling; this clause is satisfied by construction. | /look-and-feel + /demo-day |
| NFR-6 | Reproducibility (§1) | For a fixed repo `HEAD`, tag set, and `as_of`, the rendered HTML is byte-identical across runs (mirrors release-board's own NFR-7). The pseudo-release's own figures are expected, not a violation, to differ across runs whose `HEAD` has moved — identical scoping to release-board's own NFR-7. | /peer-review + increment test |

## 6. Out of Scope

- **Any live-updating content** — a ticker's motion/marquee, a "readers right now" or presence
  counter, a live countdown clock, client-side auto-refresh, or any `datetime.now()`/ambient-clock
  read (ADR-4). The visual *language* may be borrowed from the reference (the real aSPARK site, per
  A1); its *liveness* may not (A2). If a static "ticker strip" visual motif is built at all, it
  renders once from the same snapshot as the rest of the page and never animates or scrolls on its
  own (constitution's accessibility bar: "nothing moves... without the user initiating it").
- **A second, independent implementation of anything release-board's JSON already computes** — this
  feature only renders `insights releases`' own output; no commit range, membership, or status
  extraction is recomputed (ADR-0's spirit, the same boundary release-board drew around
  `build_board()`).
- **Separate per-release HTML files / a multi-page site** — release-board's own A2 already resolved
  the shape as one index page with drill-down, not one file per release.
- **An interactive expand/collapse drill-down widget** — A4 resolved the mechanism as static
  anchors, zero JavaScript; this is a confirmed cut, not a default pending override.
- **Any pass/fail, staleness, "release health," or completeness judgment on a release or a member's
  status** — Insights measures, `aspark-ci` enforces (constitution §3). No badge, color, or sort
  order may imply "this release/feature is behind." Artifact-status badges are colored only by
  artifact type, never by status value (A3).
- **Sorting, filtering, searching, or any client-side manipulation of the release list.**
- **A configurable or user-selectable visual theme/palette** — one shipped visual language, matching
  the real aSPARK brand site per A1's resolution; not a themeable product.
- **MCP exposure of this HTML surface** — no story asks for it, mirrors release-board's own
  out-of-scope line.
- **Cross-repo / fleet aggregation** (backlog I9) — same boundary every prior board has respected.
- **Writing to, editing, or annotating any `.spark/` artifact** — read/render only, same as
  release-board.

## 7. Clarifications

| # | Date | Question | Resolution |
|---|---|---|---|
| C1 | 2026-08-19 | Should this feature ship as a new subcommand, or extend `insights releases`'s existing `--format` flag? | **Resolved by the PO, not escalated.** Extend `--format` — the shipped CLI already reserves it (`choices=("json",)`, a single-value enum clearly left open for exactly this), so adding `html` is the minimal-surface move (library lens); a new subcommand would duplicate the same `--repo`/`--as-of` flags for no reason. |
| C2 | 2026-08-19 | Should the badge's displayed status string include the Markdown code-span backticks release-board's own header-table extraction returns verbatim (e.g. `` `approved` ``)? | **Resolved by the PO, not escalated (AC-2.6).** Strip the decorative backticks before display as a presentation-only cleanup; the underlying extracted value is otherwise shown exactly as-is. This doesn't touch what data is shown, only how a known, universal formatting artifact is displayed — not ambiguous enough to need the user's ruling. |
| C3 | 2026-08-19 | Does this feature belong in `aspark-insights` at all, absent its own `BACKLOG.md` entry? | **Resolved — inherits release-board's own A1/C4 ruling** ("yes, in `aspark-insights`"). This is release-board's own deferred HTML story (its §6/A2), not a new structural-boundary question. |
| C4 | 2026-08-19 | A1: reuse the shipped report vocabulary, or the retro-newsroom mockup? | **Resolved by the user, escalated per A1.** Neither — the real, live aSPARK brand site (https://aspark.lottes.dev) is the actual reference; verbatim: *"Moderner look der zu dem logo und https://aspark.lottes.dev (wewbseite) passt."* Tokens extracted via computed-style inspection, folded into A1. |
| C5 | 2026-08-19 | A3: does the artifact-status badge system vary color by status? | **Resolved by the user, escalated per A3.** No — verbatim: *"Farbe nur nach Artefakt-Typ, nie nach Status."* Color keys to artifact type only; the no-judgment-hue rule (NFR-5) is unaffected. |
| C6 | 2026-08-19 | A4: static anchors or an interactive widget for drill-down? | **Resolved by the user, escalated per A4.** Static anchors, zero JS — verbatim: *"Statische Anker, kein JS (Empfohlen von PO)"* — confirming the PO's original default. |
| C7 | 2026-08-20 | `/peer-review` finding F3 (Major): AC-2.3 and §1's success signal claimed `v0.5.0`'s real single member is `measurement-honesty` — independently verified (`git log --name-only v0.4.0..v0.5.0` and `build_release_map()`'s actual output) to be false; `v0.5.0` genuinely has 2 members (`measurement-honesty` and `snapshot-report`, whose trailing "record the release report" commit `28a5bfd` lands inside v0.5.0's range — a real, disclosed-not-filtered case per release-board's own A8). The rendering code is correct; only the spec's illustrative claim was stale. Which real tag has exactly one member and doesn't overlap an example already used elsewhere in the spec? | **Resolved by the PO, not escalated.** Re-pointed both AC-2.3 and §1's success signal at `v0.7.0`/`git-native-mid-cycle-board` — verified to have exactly one member and zero unattributed commits, and distinct from `v0.3.0` (the 3-member example, AC-2.2) and `v0.6.0` (the unattributed-commit example via commit `26e7f95`, AC-2.4). |

## 8. Design Review

<!-- Filled by /look-and-feel, Specify-phase pass against the spec (A1/A3/A4/A5 already resolved,
     not reopened here). No running page exists yet — quantitative contrast numbers below are
     computed from the spec's own stated hex values (WCAG relative-luminance formula), not
     eyeballed and not yet confirmed via getComputedStyle; that confirmation is /demo-day's job
     per NFR-5's own verification method. -->

- **Overall impression:** The design direction is sound and internally consistent — matching a
  real, live reference site via computed-style extraction (A1) rather than a mockup, keying badge
  color to artifact type rather than status (A3, a correctly-scoped instance of the already-shipped
  no-judgment-hue rule), and static zero-JS anchors (A4) are all defensible calls that don't fight
  the feature's own goal (a glanceable, offline, honest render of already-computed JSON). State
  coverage under the `ux` lens is genuinely complete for a static page: empty-repo (AC-3.1),
  true-zero pseudo-release (AC-3.2), and null-with-reason (AC-3.3) are all named; loading/error/
  form states are correctly N/A. The two real gaps are that **A1's token set, as written in the
  spec, is materially incomplete against what NFR-5 and A3 actually need it to cover** (a text-color
  triad and a 5-way badge-hue palette), and that **AC-1.4/A5's 126KB logo has no stated weight
  bound**. Neither requires reopening A1/A3/A4's rulings or a new story — both are "finish the same
  extraction, then verify it" items, routed below.

- **Findings:**

  1. **[Major] A1's resolved token list names exactly one accent color (teal `#3abdb0`) and zero
     text-color tokens, but A3 requires 5 visually distinct, consistently-keyed badge hues
     (`spec`/`plan`/`review`/`qa`/`release`) and NFR-5 requires AA contrast "on every color pair
     the page ships, including any newly introduced per A1's resolution" — and the page's actual
     content (status strings, dates, reasons, commit subjects) is text.**
     Location: §3 A1, A3; NFR-5. Rule: Color used with meaning, not decoration (visual craft) /
     consistency & standards. As literally written, A1 gives backgrounds, one accent, typography
     and shape tokens — not a palette a badge system or a text hierarchy can be built from without
     improvising mid-`/increment`, which is exactly the kind of undocumented decision this project's
     own precedent (A1 itself) was written to avoid. Fix: before `/increment`, extend A1's same
     live-site extraction technique (computed-style inspection of aspark.lottes.dev, not a guess)
     to produce (a) a primary/secondary/muted text-color triad on both `--bg-primary` and
     `--bg-card`, and (b) 5 named badge hues, each with its own on-tint text-contrast number. This
     doesn't reopen A1's *ruling* (match the live site) — it finishes applying it. Safe for
     `/increment` once those values are written down; not safe to leave implicit.

  2. **[Major] One specific text-color pairing that would plausibly be reached under this gap —
     a muted token around `#6c6c8a` — computes below NFR-5's 4.5:1 normal-text floor on both
     stated background tokens.** Location: §3 A1 (token gap), NFR-5. Rule: WCAG 2.1 AA contrast,
     never eyeballed. Using the WCAG relative-luminance formula on the hex values this session's
     own extraction context named (not present in the spec's committed text — see finding 1):
     `#6c6c8a` on `--bg-primary #0a0a0f` ≈ **3.9:1**, and on `--bg-card #16162a` ≈ **3.5:1** — both
     pass the 3:1 large-text/non-text bar but **fail** the 4.5:1 normal-text bar NFR-5 sets. By
     contrast, a secondary token around `#a0a0c0` clears both backgrounds comfortably (≈7.8:1 /
     ≈7.0:1), and the teal accent `#3abdb0` clears ≈8.5:1. If a `#6c6c8a`-class muted token ends up
     applied to any normal-size body text — a plausible candidate is AC-3.3's null-artifact
     `reason` text, or AC-2.4's commit hash/subject text — it will ship AA-failing. Fix: once
     finding 1's text triad is written down, either restrict any `#6c6c8a`-class token to large
     text/non-text uses only (≥19px bold / 24px regular, or icon-only), or pick a lighter muted
     value: name the choice explicitly, then confirm the shipped value via `getComputedStyle` at
     `/demo-day` per NFR-5's own method — this finding is a computed flag, not a substitute for
     that measurement.

  3. **[Major] No stated way back from a release/member detail block to the index.** Location:
     US-2, AC-2.1, A4. Rule: User control — can the user back out without losing their place. A4's
     static same-document anchors (correctly, zero JS) get you *down* the page from the index to a
     release's detail, but no AC names a return path; the only way back is the browser's own back
     button or manual scroll. §1's own success signal is glanceability, and the entry count only
     grows (9 today, one more per future tag) — this is exactly the flow that degrades quietest as
     the page grows. Fix: each release/member detail heading carries its own same-document anchor
     link back to the index (e.g. `#index` or `#top`), using the identical zero-JS mechanism A4
     already chose — doesn't reopen A4, doesn't need a new AC, safe for `/increment` inside AC-2.1's
     existing wording.

  4. **[Major] Heading hierarchy, `<html lang>`, `<title>`, and viewport meta are unstated in
     NFR-5**, despite the constitution's Accessibility bar explicitly requiring "a single `<h1>`,
     a coherent nested heading hierarchy" and despite this exact bug class (missing viewport meta)
     having shipped once already in this repo (`snapshot-report`, caught at `/demo-day`) and been
     flagged again, unresolved, in `git-native-mid-cycle-board`'s own design review (finding 19,
     routed "safe for `/increment`" both times — a repeat, per this project's own CLAUDE.md lesson
     about not letting a flagged gap recur silently a third time). Location: NFR-5. This page's
     structure is genuinely deep (index → per-release detail → per-member 5-artifact table), so an
     unstated heading scheme risks a skipped level or a duplicate `<h1>`. Fix: state explicitly —
     one `<h1>` for the page, `<h2>` per release detail, `<h3>` per member — plus `<html lang="en">`,
     a descriptive `<title>`, and a `<meta name="viewport">` tag. Safe for `/increment`, but naming
     it now is what breaks the repeat pattern.

  5. **[Major] AC-1.4/A5's 126KB PNG has no stated page-weight bound, and NFR-4's "without
     unbounded read" language is scoped to data (members/unattributed lists), not to the logo
     asset.** Location: AC-1.4, A5, NFR-4. Rule: Minimalism / every element earns its place — a
     hero-resolution asset (2182×721) inline-embedded as base64 (≈33% size inflation, so ≈168KB of
     HTML) for a page whose actual current data payload is 9 releases / ≤3 members each is
     disproportionate, and ADR-5's offline requirement (which correctly forbids fetching it
     externally) doesn't by itself excuse shipping it unoptimized. Fix: add an explicit bound —
     either to NFR-4 or a new NFR — e.g. "the embedded logo asset is resized/re-compressed to a
     stated ceiling (e.g. ≤30KB) before inlining, at whatever resolution the page's actual rendered
     logo size requires (a masthead-sized wordmark, not a 2182px-wide source)." This is an
     `/increment`-time image-optimization task, not a blocker, but it needs a stated number so it
     isn't done ad hoc and re-litigated later.

  - **Resolved by construction, confirmed, not a finding:** A3's "color by type, not status" plus
    NFR-5's "no status/badge conveyed by color alone" together already require every badge to carry
    a text label, and NFR-5's "real `<table>`/`<th>`" requirement for the 5-artifact matrix means
    the artifact-type name is already a programmatic, visible label (a `<th scope="col">`) distinct
    from the badge's color — this satisfies recognition-over-recall and the no-color-alone rule for
    artifact-type badges specifically, *provided* the matrix ships as a real table and not a
    div-based badge list per member (worth a one-line confirmation at `/peer-review`, not a new
    finding).

- **Routing:**
  - **Before `/increment` starts (token completion, not a `/story-time` reopening — A1's ruling to
    match the live site stands, this only finishes applying it):** findings 1 and 2 — write down
    the text-color triad and the 5 badge hues, resolve the muted-token contrast risk.
  - **Safe for `/increment` inside existing AC/NFR wording:** findings 3, 4, and 5.
  - **Deferred to `/demo-day` measurement (per NFR-5's own method, `getComputedStyle`, not
    eyeballed):** every color pair this feature ships, including whichever values resolve findings
    1 and 2; the 375px no-horizontal-scroll requirement; the rendered `<h1>`/`<h2>`/`<h3>` order by
    DOM inspection.
  - **No finding reopens A1, A3, or A4's rulings, or asks for new scope** — nothing above asks for
    JS, an expand/collapse widget, sorting/filtering, or a themeable palette (§6 stays intact).

---

## ✅ SPEC GATE

*All boxes checked → `/sprint-plan` may start. Any box open → back to `/story-time` or `/look-and-feel`.*

- [x] Problem, goal and success signal are concrete (no buzzwords, no "everyone") — grounded in this
  repo's real, current tag list and two independently-verified real examples inherited from
  release-board's own spec
- [x] Every story has testable Given/When/Then acceptance criteria
- [x] Stories are prioritized (MoSCoW) and at least one is a Must — all three committed stories are
  Must; this is a deliberately small slice with no Should/Could padding
- [x] Non-functional requirements are stated and measurable (or marked N/A with reason)
- [x] Clarify pass done: no ambiguity left unresolved or unparked — C1/C2 resolved by the PO; every
  remaining ambiguity found in the sweep is parked in §3, not silently absorbed
- [x] Open questions are resolved or explicitly accepted as risk — A1 (visual language), A3 (badge
  color by type only), and A4 (static anchors, zero JS) are resolved with the user's explicit
  rulings, recorded in §3 and §7 (C4/C5/C6); A2 is a named constitutional constraint, never a live
  question; A5 (logo) is sourced — `assets/aspark-logo-dark.png` is downloaded into the repo — with
  its remaining inline-embedding step correctly reclassified as `/increment`-time implementation
  work, not an open spec question. No real open question remains.
- [x] Out-of-scope section is filled (something was consciously cut) — an interactive drill-down
  widget and any live-updating content are both named cuts, not silent omissions
- [x] Constitution respected, or conflicts recorded as open questions — A2 names the liveness
  boundary explicitly; A3 names the badge-color tension explicitly; neither is silently overridden
- [x] Design review done for UI-facing features (or marked N/A with reason) — done: `/look-and-feel`
  ran a real pass against this spec (§8), 5 findings (2 already folded back into A1 — token
  completeness and the text-contrast scoping rule — the other 3 routed as `/increment`-time
  implementation notes, not spec blockers), overall verdict "sound, safe to proceed."
- [x] Status set to `approved` by the user — the user gave explicit approval ("ja, freigeben") in
  chat on 2026-08-19.
</content>
