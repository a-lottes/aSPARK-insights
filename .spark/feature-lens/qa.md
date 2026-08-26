# QA Report: feature-lens

| | |
|---|---|
| **Phase** | Review (hands-on) |
| **Owner** | QA Tester (`/demo-day`) |
| **Input** | Running app (`http://localhost:8801/feature-lens.html`), `.spark/feature-lens/spec.md`, `plan.md`, `review.md` |
| **Status** | `passed` |
| **Date** | 2026-08-26 (re-test) |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report updates it in the same edit that closes or re-rules a bug:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `passed` — B1 re-tested adversarially in `/demo-day` re-run, 2026-08-26, with fresh
  independent measurements against the freshly-regenerated page at
  `http://localhost:8801/feature-lens.html`. Confirmed genuinely fixed, no new regression
  introduced. See B1's row for the full re-test evidence.
- **Verdict (original pass):** One Major, first-hand-observed bug at the agreed mobile viewport
  (375×812); everything else (desktop layout, all 11 real features' data correctness, the
  gate/pipeline anti-verdict construction, security, offline/determinism/performance) passed
  cleanly, on real data, hands-on.
- **Fix applied:** `featurelens_report.py`'s `_LENS_STYLE` gained a `min-width` floor on
  `.lens-table` (62rem) and on every cell (9ch/12ch), so columns can no longer be crushed below a
  readable width by `overflow-wrap: anywhere` alone.
- **Re-test evidence (this pass, own measurements, not the developer's numbers):** at 375×812,
  `getBoundingClientRect()` on every header/body cell in the first row measured 92.5–141.6px (was
  33–53px) — real words, confirmed visually via screenshot (feature names, dates, and status badges
  all read as legible text, not vertical single-letter columns). `.table-wrap` genuinely scrolls:
  `scrollWidth 992 > clientWidth 327`. The page itself still shows zero page-level scroll:
  `window.innerWidth === document.documentElement.scrollWidth === document.documentElement.clientWidth
  === 375`. Scrolled `.table-wrap` fully right (`scrollLeft = scrollWidth`) and screenshotted: the
  Gate and Delivered In columns are fully revealed and legible — the scroll container genuinely
  exposes hidden content, not a broken/invisible scrollbar. Desktop (1280×800) re-verified
  unaffected in this session: table renders at its natural 1200px width, `.table-wrap` needs no
  scroll (`scrollWidth === clientWidth === 1200`), page-level scroll clean. CSS source inspected
  live and confirms the described fix is actually present: `min-width: 62rem` on `.lens-table`,
  `min-width: 9ch`/`12ch` on cells. Regression spot-check (not a full AC re-run): gate badge
  contrast 8.06:1 and `<h1>` contrast 17.42:1 (both match the original pass exactly), heading order
  still `H1→H2→H2→H3×5` with no skip, 0 interactive elements, pipeline section structurally intact
  (11/11 `<li>`s in the `Released` bucket, 4 empty buckets rendering `.empty-notice` with identical
  `<h3>` styling, `git-native-mid-cycle-board`/`measurement-honesty` still showing gate `Released`
  with evidence `release: preparing`). Console: 0 messages. Network: only the page's own two
  `GET /feature-lens.html → 200 OK` requests, zero external calls.
- **Open:** `0 open`.
- **Binding ruling:** §5 Verdict and the QA GATE below.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch
  as a finding at the next `/demo-day` and proceed — don't stop on it.

## 1. Test Environment

- **App URL:** `http://localhost:8801/feature-lens.html` (static file, Python `http.server`,
  already running — not started/stopped by me), this repo's own `insights features --format html`
  output, `as_of=2026-08-26`, generated after `/peer-review`'s fix rounds (`review.md` status
  `passed`). **Re-test (this pass):** page freshly regenerated after the B1 fix landed
  (`insights features --as-of 2026-08-26 --format html`); same server, same port, not
  restarted by me.
- **Browser / viewport(s):** in-app Browser pane (`mcp__Claude_Browser__*`). Tested at desktop
  1280×800 and mobile 375×812 (the two viewports NFR-4 itself names).
- **Test data / accounts used:** none — read-only page, no auth, no forms. Cross-checked the
  page's own real data against `uv run insights releases --as-of 2026-08-26 --format json` and
  `uv run insights features --as-of 2026-08-26 --format json` run directly via shell against this
  repo (11/11 features, 11/11 `delivered_in` tags byte-matched the rendered page).
- **aspark-graph:** per the caller's own pre-check, `query staleness` returned `stale: true`; per
  the tool's own rule I treated the graph as absent and cited no result from it, and did not
  invoke it myself.

## 2. Acceptance Criteria Verification

| Spec ID | Steps performed | Expected | Observed | Result |
|---|---|---|---|---|
| AC-1.1 | Loaded the page; extracted full table text and markup via `get_page_text`/`read_page`/`outerHTML`; cross-ran `insights features --as-of 2026-08-26 --format json` via Bash and diffed the 11 names/dates/gates/`delivered_in` values against the rendered table. | All 11 named features, each exactly once, own spec date / 5-artifact map / delivered-in; every cell wrap-disciplined, no page overflow. | All 11 present exactly once; every field byte-matched the CLI JSON. Wrap CSS (`overflow-wrap`, `max-width`, and now `min-width`) confirmed present via `getComputedStyle` on `td`. Re-tested at 375px this pass: no page-level overflow (`innerWidth===scrollWidth===375`), and the table is now genuinely readable within its own scrolling container — see B1/NFR-4. | ✅ pass (desktop and mobile) |
| AC-1.2 | Located the `release-board-docs` row; read its `Delivered In` cell; confirmed via the CLI JSON (`delivery` object per release) that `v0.10.0` carries `delivering: true` and `v0.11.0` carries `delivered_in: "v0.10.0", delivering: false`. | `release-board-docs` delivered-in reads `v0.10.0`; exactly one row; no `v0.11.0` second entry. | Exactly one `release-board-docs` row, `Delivered In` = `v0.10.0`. No second row for it anywhere in the table. Matches the CLI cross-check exactly. | ✅ pass |
| AC-1.3 | Searched the real-data table/pipeline for any feature whose only occurrence is the open pseudo-release. | A `null`/"not yet delivered" case should exist only if this repo has one (A3 says it doesn't). | No real feature in this repo is in that state today — confirmed (all 11 show a concrete `vX.Y.Z`). This is the spec's own disclosed A3 limitation, not a defect. No fixture-repo URL was provided to this session to browser-test the pseudo-release case directly. | N/A — not independently browser-verifiable against real data (A3, disclosed); relies on `review.md`'s own fixture-based verification, not re-tested here |
| AC-1.4 | Inspected every 5-artifact cell across all 11 rows for a null/degraded status. Found one **in real data, unplanned**: `mcp-server`'s `qa` cell. Confirmed via `ls .spark/mcp-server/` that no `qa.md` file exists there. | A failed/missing field renders with a specific named reason, never silently dropped, never a raw traceback. | `mcp-server`'s QA cell renders **only** `file not found` (no `qa` type badge, since AC-1.5's own rule is "reason only when status is null, never duplicated alongside a status word") — no traceback, page renders cleanly, row otherwise complete. This is a genuine real-data confirmation of the honest-degrade path, better evidence than a fixture. | ✅ pass |
| AC-1.5 | Viewed the page at 1280×800: confirmed a real `<table class="lens-table">` (not a `<div>` grid) with 9 `<th>` header cells, verified `scope="col"` present, checked row order (date-desc, name-asc tie-break — reproduced: `release-metrics` 2026-08-24 first, `foundation` 2026-07-29 last), checked 5-artifact cells render as type+status badges with reason shown only when null. **Re-test:** re-measured mobile columns independently (see B1). | Real `<table>`/`<th>`, correct order, compact badges, wrap discipline on every cell, holding at both viewports. | Desktop: all correct, clean, readable (re-confirmed this pass: natural width 1200px, no scroll needed). **Mobile (375×812), re-tested:** columns now measure 92.5–141.6px each (own fresh measurement, not the developer's) — real legible words, confirmed by screenshot. Page-level scroll still zero (`innerWidth===scrollWidth===clientWidth===375`); `.table-wrap` now genuinely scrolls (`scrollWidth 992 > clientWidth 327`) and reveals the later columns when scrolled (see B1-flow). | ✅ pass (desktop and mobile both re-verified) |
| AC-2.1 | Inspected the `<style>` block (`fetch`+text) for `.gate-badge` rule count; ran `getComputedStyle` on all 11 `.gate-badge` elements; searched the CSS and DOM for `progress`/`meter`/`track`/`dot`/`role="progressbar"`. | Gate is plain text/badge, one uniform treatment for all 6 possible values, always paired with the literal deciding artifact's status, no shape/color device implying sequence. | Exactly **one** `.gate-badge` CSS rule in the whole stylesheet (single line, no per-value selector exists in the CSS at all — structural, not just today's data). All 11 badges' computed `background-color`/`color`/`border-color`/`padding`/`border-radius` are **identical** (`uniqueStyleCount: 1`). Zero `<progress>`, `<meter>`, `[role="progressbar"]`, and zero occurrences of `progress`/`meter`/`track`/`dot` anywhere in the CSS. Every gate paired with `gate-evidence` text (e.g. `release: released`). | ✅ pass |
| AC-2.2 | Read every row's Gate + evidence text; specifically checked `git-native-mid-cycle-board` and `measurement-honesty` (known pre-existing stale `release.md: preparing`). | All 11 real features show gate `Released`; each shows its own literal `release.md` status, even the two `preparing` ones. | All 11 rows: Gate = `Released`. `git-native-mid-cycle-board` and `measurement-honesty` both show `release: preparing` as evidence while still reading gate `Released` — the exact accepted nuance (gate reflects "an artifact exists," not "value equals a specific string"). Confirmed live, not assumed. | ✅ pass |
| AC-2.3 | Searched for an `Increment`-gate feature in real data / any fixture reachable from the given URL. | Approved `plan.md`, no `review.md` → gate `Increment`. | No such state exists in this repo's real data (A3, disclosed) and no fixture app URL was provided to this session. | N/A — not independently browser-verifiable here; relies on `review.md`'s fixture-based verification |
| AC-2.4 | Same search, for an `Unknown`-gate feature (no readable `spec.md` header). | Gate `Unknown`, own reason surfaced, never guessed as `Spec`. | No such state exists in real data; no fixture URL provided. | N/A — not independently browser-verifiable here; relies on `review.md`'s fixture-based verification |
| AC-2.5 | Compared gate rendering across all 11 features (all currently `Released`, so no cross-value comparison is possible in real data) and inspected the CSS/DOM structurally for any device that could rank features. | No color/icon/order implies one feature is "better"; no progress-bar/step-tracker/dot-track device anywhere. | Same evidence as AC-2.1: one CSS rule, identical computed style across all badges, zero track/progress/meter markup anywhere on the page. Table row order is by date, not by gate — no gate-based sort exists to imply ranking. | ✅ pass |
| AC-3.1 | Scrolled to the Pipeline section; read its DOM structure (`h3` + sibling `p.empty-notice` or `ul.pipeline-list`, all under `div.pipeline-section`). | Every feature in exactly one of Spec/Increment/Review/QA/Released/Unknown; plain headed groups, no bar/track/dot device. | 5 buckets rendered (`Unknown` correctly absent — 0 features hold it). Programmatically counted: table has 11 rows, pipeline `Released` bucket has 11 `<li>`s, no feature appears in more than one bucket (`Released` is the only non-empty one). Rendered purely as `<h3>` + `<ul>`/`<p>` — no bar/track/dot markup. | ✅ pass |
| AC-3.2 | Compared the populated `Released` bucket against the 4 empty buckets: `getComputedStyle` on each bucket's `<h3>` (font-size, font-weight) and inspected each `.pipeline-section`'s parent class/chrome. | `Released` lists all 11; every other bucket states plainly it holds none, with the **same structural weight** as `Released` — same heading tag, same section chrome, not dimmed/collapsed. | All 5 buckets share `parentClass: pipeline-section`, identical `<h3>` (`15.2px`, weight `700`) regardless of populated/empty. Empty buckets use the existing `.empty-notice` idiom (confirmed visually and in markup) — same card/border chrome as neighboring populated content, not visually smaller. Screenshot at 375px confirms this reads well at mobile too (unlike the table — see B1). | ✅ pass |
| AC-3.3 | Searched for the six-stage fixture case. | Each of 6 buckets shows exactly its one expected feature. | No fixture app URL was provided to this session; this repo's real data cannot exercise 5 of 6 gate values (A3, disclosed). | N/A — not independently browser-verifiable here; relies on `review.md`'s fixture-based verification |
| AC-3.4 | Confirmed the pipeline section is a structurally separate, appended section after the Features table (DOM byte-offset check, see NFR-4 row) and that removing it would not touch the table markup (single call site, per plan/review). | US-1/US-2 hold unchanged whether or not US-3 ships. | Table and Pipeline are structurally independent sections (byte offsets: `Features` h2 @ 41658, `<table` @ 41698, `Pipeline` h2 @ 48163 — sequential, non-overlapping). This is largely a code-structure claim (confirmed at review) rather than a runtime-observable one; the DOM separation is consistent with severability. | ✅ pass (structural evidence only; not independently re-provable by removing code from the browser) |

### Browser-observable NFRs

| Spec ID | Steps performed | Expected | Observed | Result |
|---|---|---|---|---|
| NFR-3 (Security) | Watched console + network tab through every interaction; inspected rendered HTML for `<script>`, `on*` attributes, unescaped payloads on real feature/tag names; grepped the raw served HTML for email addresses / person names. | Every rendered string escaped at one choke point; no raw traceback; no person-level data. | Console: 0 errors/warnings throughout. Network: only the page's own `GET /feature-lens.html` requests, nothing else. `document.querySelectorAll('script,svg,iframe,form').length` shape check (via full-page scan) found none; no `on\w+=` attribute anywhere. `grep -oE` for email pattern and `andreas` (case-insensitive) over the served HTML: zero matches — no person-level/git-identity data leaked (constitution §6). I did not build a fresh hostile `<script>`-fixture myself (no fixture repo URL given this session) — this exact adversarial case was already covered exhaustively in `review.md` (F2/NFR-3, 25 malformed shapes + a hand-built XSS fixture, both re-broken at re-review). | ✅ pass (real-data surface); adversarial-fixture coverage relied on from `/peer-review`, not re-run here |
| NFR-4 (Accessibility, measured) | `getComputedStyle`-based contrast ratios on gate badge, all 5 artifact-type badges, table cell text, `.empty-notice`, `.gate-evidence`, `.badge-reason`, `<h1>`; heading list via `querySelectorAll('h1..h6')`; interactive-element count; `window.innerWidth`/`document.documentElement.scrollWidth`/`clientWidth` at 375px; visual + DOM inspection of the 9-column table at 375px. **Re-test:** re-ran the contrast/heading/interactive-count spot checks and the 375px table measurement fresh this pass. | WCAG AA (4.5:1 text / 3:1 non-text) everywhere; single `<h1>`, coherent `h1→h2→h2→h3` nesting, no skipped level; 0 interactive elements; no page-level horizontal scroll at 375px; every table cell wrap-disciplined and **usably readable**. | **Contrast (re-confirmed this pass):** gate badge 8.06:1, `<h1>` 17.42:1 — both exact matches to the original pass, no regression. **Headings (re-confirmed):** exactly one `<h1>`; order `H1 → H2 → H2 → H3×5` — no skipped level. **Interactive elements (re-confirmed):** `document.querySelectorAll('a,button,input,select,textarea,[tabindex]').length === 0`. **No page-level horizontal scroll at 375px (re-confirmed):** `innerWidth === scrollWidth === clientWidth === 375`. **Table readability at 375px, re-tested with fresh measurements:** the `min-width` floor added to `.lens-table`/cells (62rem / 9ch / 12ch) now forces the table to its natural 992px width; columns measure 92.5–141.6px each, confirmed genuinely readable by screenshot (real words, not single-letter columns). `.table-wrap` now does the scrolling work its `overflow-x:auto` was always meant to do (`scrollWidth 992 > clientWidth 327`), and scrolling it reveals the remaining columns cleanly (see B1-flow). Pipeline section at 375px re-confirmed fine (4 empty buckets + 1 populated bucket, same `<h3>` styling, `.empty-notice` chrome unchanged). | ✅ pass — B1 fix closes the previous mobile-table failure; everything else re-confirmed unchanged |
| NFR-5 (Measurement honesty) | Compared the 11 pipeline `<li>` gate-evidence strings against their own table row's gate-evidence string programmatically (`.gate-evidence` text extraction + exact-match diff, not eyeballed). Checked `mcp-server`'s real null-QA case for a specific reason (see AC-1.4). Grepped page for email/person data. | Gate never shown without literal evidence; no estimate/silent-zero; no person-level field. | **11/11 byte-identical matches**, 0 mismatches, between table and pipeline evidence text. `mcp-server`'s real null case names `file not found`, not a bare null. Zero person-level data found in the served HTML. | ✅ pass |
| NFR-6 (Reproducibility) | Ran `insights features --as-of 2026-08-26 --format html` twice to two separate `--output` directories via Bash, `diff`'d the two generated `feature-lens.html` files byte-for-byte. | Byte-identical output for a fixed `HEAD`/`as_of`. | `diff` reported no differences — **byte-identical**. | ✅ pass |
| NFR-7 (Offline/reliability) | Inspected every `<link>`/`<script>`/`<img>`/`<iframe>` element's `src`/`href` on the live page. | Fully self-contained, no external fetch, handles edge-repo shapes without error (structural — this repo isn't a zero-feature case). | The only such element is one `<img>` with a `data:image/png;base64,...` URI (the aSPARK masthead logo) — zero `http://`/`https://`/protocol-relative references. Zero `<script>` tags. Page rendered without error against this repo's real 11-feature, ~15s-git-walk history. | ✅ pass |
| NFR-8 (Performance) | Timed `insights features --format json` vs `insights releases --format json` via `/usr/bin/time -p` against this repo, same `as_of`. | Feature-lens adds ~0 additional cost beyond the release board's own inherited git-walk. | `features`: 15.45s real. `releases`: 14.97s real. The ~0.5s delta is well within run-to-run noise for a ~15s git-subprocess-heavy command and consistent with `review.md`'s measured "0.1ms of added in-memory work" claim — feature-lens is not adding a second git walk. | ✅ pass |

## 3. Exploratory Findings

| # | Severity | Steps to reproduce | Expected vs. observed | Status |
|---|---|---|---|---|
| B1 | Major | 1. Open `http://localhost:8801/feature-lens.html`. 2. Resize the viewport to 375×812 (the same mobile width NFR-4 itself specifies). 3. Scroll to the Features table. 4. Read the header row and the first few data rows. | **Original observation (fixed):** every 9-column header and most feature-name/status cells wrapped one character per line — measured column widths were 33–53px each — because `overflow-wrap: anywhere` on every cell lowered each cell's minimum content width to a single character, so the browser's table-layout algorithm squeezed all 9 columns into the 375px viewport instead of growing to natural width and scrolling. This was exactly the failure mode `plan.md`'s own **R4** named as a possibility. **Re-test (this pass, own fresh measurements, not the developer's):** at 375×812, `getBoundingClientRect()` on the header row and first data row measured 92.5–141.6px per column (header: Feature 141.6, Date 125.1, Spec 102.0, Plan 101.1, Review 101.0, QA 120.0, Release 107.1, Gate 100.4, Delivered In 92.6) — a genuinely readable range, confirmed visually via screenshot: feature names, dates, and status text all render as real horizontal words, not vertical single-letter columns. `.table-wrap` genuinely scrolls (`scrollWidth: 992` vs `clientWidth: 327`, `canScroll: true`), and the table's natural width is confirmed at 992px via `getBoundingClientRect()`. The page itself still shows zero page-level horizontal scroll: `window.innerWidth === document.documentElement.scrollWidth === document.documentElement.clientWidth === 375`. CSS source inspected live confirms the fix is actually present (`min-width: 62rem` on `.lens-table`, `min-width: 9ch`/`12ch` on cells), not just claimed. | **fixed, verified** — re-broken adversarially with independent measurements in this session; genuinely resolved, no regression. See B1-flow below and the Handoff block. |
| B1-flow | — (surrounding-flow check, not a new bug) | 1. At 375×812 with the table now wider than viewport, scrolled `.table-wrap` fully right via `scrollLeft = scrollWidth`. 2. Screenshotted the result. | **Expected:** horizontal scroll within `.table-wrap` should reveal the later columns (Gate, Delivered In) as real, legible content — not hide them behind a broken or invisible scrollbar. **Observed:** scrolling fully right cleanly reveals the `Release`, `Gate`, and `Delivered In` columns, all fully legible (e.g. `Released` badges, `release: released`/`release: preparing` evidence text, `v0.11.0`-style version strings) — confirmed via screenshot. The fix does not trade "crushed columns" for "content hidden behind broken scroll." | ✅ pass — no new bug introduced by the fix |

No other exploratory bugs found. B1 (re-tested this pass, confirmed fixed) and B1-flow (surrounding-flow check, passed) are the only entries. Nothing new found in this re-test session; the original pass's checks (double-navigating, refresh, zero-JS so no double-submit/race conditions, no forms/links for deep-linking, `mcp-server`'s honest QA-cell degrade) were spot-checked, not re-run exhaustively, per the re-test's own reduced scope.

## 4. Console & Network

Checked at both desktop (1280×800) and mobile (375×812) viewports on the freshly-regenerated page, before and after all interactions (re-test, this pass):
- **Console:** zero messages of any kind (no errors, warnings, logs) throughout the session.
- **Network:** only `GET /feature-lens.html → 200 OK` (twice, once per navigation); zero other requests — no fonts, no scripts, no analytics, no third-party calls. Matches the original pass exactly; no regression. Confirms NFR-7's offline/self-contained claim and NFR-3's "no external leak" concern from the browser's own vantage point.

## 5. Verdict

Desktop is genuinely demo-ready: all 11 real features render correctly and exactly once, every value cross-checked byte-for-byte against the CLI's own JSON output, the gate/pipeline anti-verdict construction (this feature's central constitutional risk) holds up under direct `getComputedStyle` and CSS-source inspection — one gate-badge rule, identical computed style across all 11 badges, zero progress/meter/track markup anywhere on the page, structurally, not just in today's all-`Released` data — and the honesty discipline (NFR-5) proved itself on real, unplanned data (`mcp-server`'s missing `qa.md`) exactly as designed, not just on a rehearsed fixture. Determinism, offline self-containment, zero-interactive-element keyboard parity, and the NFR-8 performance-isolation claim all measured out true.

**Re-test verdict (this pass):** I would now demo the mobile view. `plan.md`'s own R4 named the risk that a nine-column table might survive the letter of "no page-level horizontal scroll" while failing the reading experience it exists to protect — B1 confirmed that risk had materialized in the original pass. This session re-broke B1 adversarially with independent measurements rather than trusting the developer's fix description: at 375×812, columns now measure 92.5–141.6px (real legible words, confirmed by fresh screenshot), `.table-wrap` genuinely scrolls (`scrollWidth 992 > clientWidth 327`), scrolling it fully reveals the Gate and Delivered In columns cleanly (no broken/invisible scrollbar — a distinct failure mode I specifically checked for and did not find), and the page itself still shows zero page-level horizontal scroll. Desktop was re-confirmed unaffected at its natural 1200px width. The regression spot-check (gate badge and `<h1>` contrast, heading order, interactive-element count, pipeline section structure, console/network) found no new problem and exactly matches the original pass's numbers. B1 is closed; no new bug was introduced by the fix.

Four Must/Should ACs (AC-1.3, AC-2.3, AC-2.4, AC-3.3) remain not independently browser-verifiable in this repo's real, all-`Released` data (A3, disclosed honestly in `spec.md`/`plan.md`/`review.md` from the start, and unchanged by this fix) — this is a pre-existing, three-times-disclosed, review-covered limitation, not a new gap, and not something this re-test session could or should attempt to force a fixture for.

I would demo this application, including the mobile view, to a stakeholder right now.

---

## ✅ QA GATE

*All boxes checked → `/go-live` may start. Any box open → back to `/increment`, then re-run `/demo-day`.*

- [x] Every Must-story acceptance criterion verified in the real browser and passed — AC-1.5 re-tested and passes at both 375px and 1280px (B1 fixed); AC-1.3/AC-2.3/AC-2.4/AC-3.3 remain not independently browser-verifiable (fixture-only states, disclosed, unchanged by this fix, not a gate blocker per the original ruling)
- [x] Every browser-observable NFR verified and passed — NFR-4 re-tested and passes at 375px (B1 fixed); all others re-confirmed passing
- [x] No open Blocker or Major bugs (Minor bugs listed and accepted by the user) — B1 closed, verified fixed; no new bug found
- [x] Browser console free of errors on the tested flows
- [x] Tested on all agreed viewports (1280×800 and 375×812)
- [x] Status set to `passed`
