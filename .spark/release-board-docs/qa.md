# QA Report: release-board-docs

| | |
|---|---|
| **Phase** | Review (hands-on) |
| **Owner** | QA Tester (`/demo-day`) |
| **Input** | Running app (`http://localhost:8797/release-board.html`), `.spark/release-board-docs/spec.md` |
| **Status** | `passed` |
| **Date** | 2026-08-23 (round 2 re-verification) |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report updates it in the same edit that closes or re-rules a bug:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `passed` (round 2) — B1 independently re-verified fixed in the browser; no
  regressions found.
- **Verdict:** Round 1: both Must stories (US-1, US-2) genuinely, hands-on verified and pass
  every one of their ACs, including the two hardest ones (F1's hostile-script escaping
  re-verified with a fresh self-authored `<script>`/`onerror` fixture, and the mcp-server
  dedup-link target verified to resolve to the *correct* anchor, not just *a* link). US-3
  (Should) also passes in full. The single reason round 1 failed the gate was B1: a real,
  reproducible mobile horizontal-scroll bug in the page's own real content — long inline
  `<code>` spans inside embedded document prose don't wrap at 375px.
- **B1 fix, round 2 independent re-verification (this round):** did **not** trust the developer's
  fix annotation — reproduced live against a freshly re-served, freshly regenerated page
  (`/tmp/rbd-demo2/.aspark-insights/release-board.html`, port 8798). Resized to 375×812, opened
  the exact `release-board/plan.md` `<details>` (`#doc-f1-plan`, confirmed via DOM to be owned by
  member `member-8-0`, the same artifact named in the original repro), located the same
  `test_a_deleted_feature_directory_still_appears_in_the_release_it_shipped_in` code span via
  fresh `getBoundingClientRect()`: `right: 299.8px` (viewport 375px, no protrusion), width
  187.8×72px, `overflow-wrap: anywhere` / `word-break: break-word` both computed. Page-level
  `document.documentElement.scrollWidth === clientWidth === 375` — matches the fix claim exactly.
  **Systemic spot-check (not just the one named element):** expanded all 45 documents on the page
  simultaneously at 375px and re-measured — page-level `scrollWidth` stayed `375` (no horizontal
  overflow anywhere on the whole page, all documents, all features). Isolated all 4,462 inline
  `<code>` spans inside `.doc-content p`/`li` across every expanded document: **0 protrude** past
  the viewport, including the 5 longest spans found (152–361 characters each), spanning 5
  different documents/features (`doc-f4-release`/member-4-1, `doc-f5-plan`/member-3-0,
  `doc-f7-plan`/member-2-2, `doc-f0-release`/member-9-0, `doc-f2-plan`/member-6-0) — confirms the
  fix is the systemic `.doc-content`-wide CSS rule it claims to be, not a one-off patch for the
  single element named in the original bug report.
- **Regression check:** index still newest-first at mobile width (screenshot + DOM `h2` order:
  Since v0.9.0 → v0.9.0 → … → v0.1.0, unchanged). Desktop 1280×800 re-checked separately: zero
  horizontal scroll (`scrollWidth === clientWidth === 1280`), and `doc-f4-release` (a different
  document than the one used for the mobile check, for variety) expands normally with real
  structured content — genuine `<table>`/`<caption>`/`<th>` markup, not a status badge or raw
  text. Console clean throughout (`read_console_messages`: no logs). Full first-pass sweep (F1
  hostile-script fixture, dedup-link resolution, checklist color-independence, contrast, keyboard
  operability) was not re-run in full per the task scope — this CSS-only fix touches none of
  those code paths and none of them were re-broken by anything observed this round.
- **Open:** `0 open`. B1 closed on independent re-verification.
- **Binding ruling:** §2 (AC table) for the full pass/fail trace; §3 B1 for the fix record.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch
  at the next `/demo-day` and proceed.

## 1. Test Environment

- **App URL (round 1):** `http://localhost:8797/release-board.html` (static, offline, zero-JS HTML;
  `python3 -m http.server 8797` serving `/tmp/rbd-demo/.aspark-insights/release-board.html`,
  1,314,196 bytes — matches the stated real measured weight).
- **App URL (round 2, this pass):** `http://localhost:8798/release-board.html`, serving a freshly
  regenerated `/tmp/rbd-demo2/.aspark-insights/release-board.html` (post-B1-fix), verified reachable
  (`200 OK`) before testing.
- **Browser / viewport(s):** `mcp__Claude_Browser__*` (Chromium-based). Desktop (1280×800,
  default) and mobile (375×812, `resize_window` preset `mobile`), both reloaded after resize.
- **Test data / accounts used:** This repo's own real `.spark/` history as of `--as-of
  2026-08-23` (9 real tags `v0.1.0`–`v0.9.0` + 1 open pseudo-release, 10 entries total, 16
  feature-artifact members). For AC-2.2/AC-2.3/AC-2.4/AC-2.5/AC-3.4 (empty file, hostile
  `<script>`/`onerror` payload, 5,003-line oversized document, unrecognized Markdown constructs)
  I constructed a minimal isolated throwaway git repo (`/private/tmp/.../scratchpad/empty-doc-test`,
  never touching this project's real repo) with a single tag and a single feature carrying
  hand-crafted fixture files, generated via the real `insights releases --format html` CLI, and
  served on a separate port (8798, stopped after use) — per this project's own adversarial-
  reproduction precedent (build your own hostile input, don't just trust the description of one).
  The real-repo checks (AC-1.*, AC-2.1, AC-3.1, AC-3.2, AC-3.3, NFR-2 spot-check, NFR-4, NFR-5,
  NFR-6) were run against the actual served page with no fixtures.

## 2. Acceptance Criteria Verification

| Spec ID | Steps performed | Expected | Observed | Result |
|---|---|---|---|---|
| AC-1.1 | Loaded the real page, screenshotted the index, and read `h2`/index-row order via DOM query on the served real page. | Pseudo-release "Since v0.9.0" first, `v0.1.0` last, reverse of JSON order. | Screenshot + DOM both show: Since v0.9.0, v0.9.0, v0.8.0 … v0.2.0, v0.1.0 (10 rows, confirmed to the bottom via JS query, not just visible viewport). Lead sentence reads "10 releases, newest first." (design finding 1 fixed). | ✅ pass |
| AC-1.2 | Extracted the document-order sequence of all `<h2>` detail-card headings and compared to the index-row sequence. | Detail-card order identical to index order, no mismatch. | Both sequences: `Since v0.9.0, v0.9.0, v0.8.0, v0.7.0, v0.6.0, v0.5.0, v0.4.0, v0.3.0, v0.2.0, v0.1.0` — byte-identical. | ✅ pass |
| AC-1.3 | Ran `insights releases --as-of 2026-08-23 --format json` directly and parsed the release-tag order. | Oldest-first, pseudo-release last — completely unaffected by the HTML reorder. | `['v0.1.0', 'v0.2.0', ..., 'v0.9.0', None]` — oldest-first, pseudo-release (`None` tag) last. Unchanged from pre-feature behavior. | ✅ pass |
| AC-1.4 | Compared v0.3.0's member order (`mcp-server`, `public-repo-polish`, `traceability-metrics`) and a member's artifact-status row order (`spec/plan/review/qa/release`) in the rendered HTML against the underlying JSON's member order. | Member list and artifact-row ordering untouched by the top-level release reversal. | Both match exactly; only the top-level release sequence reversed. | ✅ pass |
| AC-2.1 | Expanded `release-board-html/review.md`, `release-board-html/spec.md`, and `snapshot-report`'s docs (3+ artifacts across 2+ releases) via real mouse clicks on `<summary>`; separately traced every "Documents shown under `<release>`" link on the page (7 occurrences) by precisely mapping each link's *owning* member (via `closest('[id^="member-"]')`, not text-proximity) to its `href` target, including `mcp-server` (member of both v0.3.0 and v0.4.0). | Full document content appears (not just status badges); a multi-release member's docs show once, under the newest occurrence, with an honest link at the older occurrence that lands on the real content. | All 3 expanded docs showed real prose/headings/tables (e.g. `release-board-html/review.md`'s actual "Overall impression" text and 5 numbered findings — not a status badge). All 7 dedup links resolve to the correct target member (verified `mcp-server` under v0.3.0 → href `#member-3-0` → target is genuinely `mcp-server` under v0.4.0, not a neighboring member — an early text-proximity-based check produced a false positive of a wrong-target bug here; the precise DOM-ancestor check showed it was correct). | ✅ pass |
| AC-2.2 | Constructed a fixture feature with `release.md` deliberately not created (file does not exist) alongside real sibling files; expanded its `<details>`. | Board states plainly a file wasn't found — no raw traceback, no blank/broken page, no stale cache. | `<p class="empty-notice">file not found</p>` shown under a correct `.doc-provenance` line naming the missing path; siblings with real content rendered normally alongside it. | ✅ pass |
| AC-2.3 | Constructed a genuinely 0-byte `qa.md` in the same fixture feature (exists, readable, empty) alongside the missing `release.md` and real-content siblings; expanded its `<details>`. | States plainly the doc is empty; visually/textually distinguishable from both the "file not found" case and from real content. | `<p class="empty-notice">This document is empty.</p>` — distinct wording from "file not found", same fixture repo, directly comparable side-by-side; both trivially distinguishable from the multi-hundred-character real-content blocks next to them. | ✅ pass |
| AC-2.4 | Built a hand-authored hostile `spec.md` embedding `<script>window.__qaXssFired = true; document.title = 'XSS-FIRED';</script>`, an `<img src=x onerror="window.__qaXssFired2 = true">`, and a backtick-quoted `<script>alert(1)</script>` fixture string; rendered and expanded it; checked `window.__qaXssFired`/`__qaXssFired2`, `document.title`, and `querySelectorAll('script'|'img').length` after render. | Every character escaped through one canonical choke-point; hostile markup renders as inert visible text, never executes. | `xssFired: false`, `xssFired2: false`, page title unchanged, 0 `<script>`/`<img>` elements in the rendered DOM; raw HTML shows `&lt;script&gt;...&lt;/script&gt;` as literal escaped text. | ✅ pass |
| AC-2.5 | Constructed a 5,003-line / 638,912-byte `plan.md` (well beyond the real largest artifact, 538 lines) and expanded it. | Excess disclosed as truncated with a stated line/byte count, never silently dropped. | `<p class="truncation-note">Showing the first 1200 of 5003 lines (152255 of 638912 bytes) of this document.</p>` — reuses the existing `.truncation-note` idiom per design finding 5. | ✅ pass |
| AC-3.1 | Traversed every heading/`[role=heading]` element on the whole page (index + all 10 release detail cards + all 45 expanded documents) computing effective level (`aria-level` when present, else tag number); checked h1 count and consecutive-level gaps. Separately confirmed a document with real h3-level (`###`) source content (`release-board-html/spec.md`'s `US-1`/`US-2`/`US-3`) renders via `role="heading" aria-level="7"` (design finding 2's option (a)), not a flattened, ambiguous h6. | Exactly one page-level `<h1>`; zero skipped levels anywhere, including inside embedded documents; depths beyond h6 use `aria-level`, not silent flattening. | 497 total heading nodes page-wide; `h1Count: 1`; `skipsCount: 0`; `maxLevel: 7` (via `aria-level="7"` on the `US-1/US-2/US-3` div headings, confirmed `role="heading"`). | ✅ pass |
| AC-3.2 | Inspected `release-board-html/spec.md`'s 4 embedded pipe-tables (Assumptions, NFRs, Clarifications, plus the Handoff-block table) via DOM `querySelectorAll('table')`/`<caption>`. Cross-checked with the hostile-fixture repo's table too. | Real `<table>`/`<th>` markup, not raw pipe text; captions distinct per table (design finding 7). | 4 real `<table>` elements with `<caption>`/`<th scope="col">`; captions: `"Spec: release-board-html"` (first table, before any numbered heading — falls back to doc title), `"3. Assumptions & Open Questions"`, `"5. Non-Functional Requirements"`, `"7. Clarifications"` — all 4 distinct, sourced from nearest preceding heading. | ✅ pass |
| AC-3.3 | Queried all `- [x]`/`- [ ]` list items page-wide (611 total: 434 checked, 177 unchecked); compared `getComputedStyle(...).color` between checked and unchecked glyph spans and their sr-only text labels; confirmed the visually-hidden label technique. | Checked/unchecked distinguishable by text/glyph, never color alone. | Both use identical color `rgb(240, 240, 248)` — no hue difference at all. Rendering: `<span aria-hidden="true">☑/☐</span> <span class="sr-only">checked:/unchecked:</span>` (clip-rect(0,0,0,0) sr-only pattern) — matches design finding 6's named fallback option exactly. Glyph codepoints confirmed correct (U+2610/U+2611) via `codePointAt`. | ✅ pass |
| AC-3.4 | Built a fixture `review.md` with a nested blockquote (`>`), a reference-style link (`[see here][1]`), and a raw HTML `<table>` (none in A3's bounded construct set); rendered and expanded it. | Degrades to plain, visible, readable text; never dropped, never a crash, rest of document still renders. | All three appear as literal escaped text (`&gt; This is a nested blockquote...`, `[see here][1]`, `&lt;table&gt;...`); the trailing "End of unusual constructs." paragraph after them rendered fine — no crash, no truncation of the rest. | ✅ pass |
| NFR-2 (security spot-check) | Read `release-board-html/review.md` and `qa.md` (both quote code/hostile-fixture text describing security findings) in their expanded form; separately ran the dedicated hostile-fixture test under AC-2.4. | Any code-like/HTML-like prose in real documents renders as inert visible text. | No live markup found executing in either real document; the dedicated hostile-fixture test (AC-2.4) is the stronger, adversarial confirmation and passed. | ✅ pass |
| NFR-4 (offline / page weight) | Checked served file size on disk; watched `read_network_requests` across the entire session (initial load, hash navigations, `<details>` toggles). | Self-contained, offline, no external fetch; bounded page weight, well under budget. | File size 1,314,196 bytes (~1.25MB) — matches the stated measurement, well under the 2.5MB/page and 5MB ceiling. Network log shows only `GET .../release-board.html` requests (repeated navigations to the same file, all 200 OK) — zero other requests (no fonts/scripts/images/CSS from any external host) across the whole test session. | ✅ pass |
| NFR-5 (accessibility, measured) | `getComputedStyle` contrast (WCAG relative-luminance formula) on `.doc-content` and `.doc-provenance` against their resolved background; whole-page heading-order scan (see AC-3.1); real keyboard `Tab` navigation (not `.focus()`, which gave a false negative — see §3 note) onto an index link and a `<summary>`, checking `:focus-visible` and `outlineStyle`; native `<details>` `Enter`-key toggle; 375px viewport `scrollWidth` vs `clientWidth` check, drilling into which elements protrude past the viewport and whether they're contained by their own `overflow-x:auto` wrapper. | WCAG AA contrast (≥4.5:1 body text); zero skipped heading levels; visible keyboard focus; keyboard-operable `<details>`; no unwanted page-level horizontal scroll, including around wide tables. | `.doc-content` contrast 16.43:1, `.doc-provenance` 7.35:1 (both far above AA). Heading order: see AC-3.1 (pass). Real `Tab` press → `outlineStyle: "auto"`, `:focus-visible` true, on both an index link and a `<summary>` — visible focus confirmed. `Enter` on a focused `<summary>` correctly toggled `details.open` (and 3× rapid `.click()` toggled correctly on the 3rd, odd-numbered click — no double-fire bug). Wide tables (`.table-wrap`, `overflow-x:auto`) are correctly self-contained — they do **not** cause page-level scroll. Round 1 found `document.documentElement.scrollWidth` (391px) exceeding `clientWidth` (375px) at mobile width, traced to long inline `<code>` spans lacking `overflow-wrap`/`word-break` — see B1. **Round 2 re-verification:** with the fix applied, re-checked the identical repro (`scrollWidth === clientWidth === 375`) plus a systemic check with all 45 documents expanded simultaneously (`scrollWidth` still 375; 0 of 4,462 inline `<code>` spans protrude, across 5+ different documents/features). | ✅ pass (round 2) |
| NFR-6 (reproducibility, bonus check) | Ran `insights releases --format html --output <dir>` twice to separate output directories from the same repo state and `diff`'d the two files. | Byte-identical render for a fixed input. | `diff -q` reported no difference — byte-identical. | ✅ pass |

## 3. Exploratory Findings

| # | Severity | Steps to reproduce | Expected vs. observed | Status |
|---|---|---|---|---|
| B1 | Major | 1) Serve `release-board.html` and resize the browser to 375×812 (mobile). 2) Navigate to the real page (no fixture needed — this is real, currently-shipping content). 3) Expand `release-board` feature's `plan.md` (`#doc-f1-plan`, under member `release-board`). 4) Locate the inline `<code>test_a_deleted_feature_directory_still_appears_in_the_release_it_shipped_in</code>` span (a real test-name reference in that plan's own text) and inspect its `getBoundingClientRect()`, or simply observe `document.documentElement.scrollWidth` (391px) vs `clientWidth` (375px) on the page as a whole with that `<details>` open. | Expected: no page-level horizontal scroll at 375px, per this project's own "no horizontal scroll" mobile bar (extended by this feature to cover text now embedded from real documents). Observed: the inline `<code>` span (587–757px wide in some samples, `right: 699`–`868.5`px against a 375px viewport) is not wrapped and is not inside any `overflow-x` container, so it pushes the whole `<body>`/page out sideways. Root cause: the embedded-CSS `.doc-content p, .doc-content li { max-width: 74ch; }` rule (design finding 4's reading-width fix) constrains the *box*, but nothing sets `overflow-wrap`/`word-break` on inline content inside that box — only `.doc-content pre` got `word-break: break-word`, not `.doc-content code`/`p`/`li`. This is systemic, not a one-off: multiple real long test-name/file-path `<code>` spans across at least `release-board`'s and `mcp-server`'s embedded plan/review docs trigger it (found 15 protruding elements past the viewport edge on a single scan of the real page). Wide *tables* are correctly handled (contained by `.table-wrap { overflow-x: auto }`) — this is specifically the inline-`<code>`-in-prose case that was missed. **Fixed, independently re-verified round 2:** `overflow-wrap: anywhere` added to `.doc-content p`/`li`/`code` (mirroring `.doc-content pre`'s existing wrap rule). Round 2 re-verified live against a freshly regenerated page and fresh browser session (not the developer's own account): same `<details>` (`#doc-f1-plan`, confirmed via DOM to be owned by member `member-8-0`), same code span, `scrollWidth === clientWidth === 375` (was 391 vs 375), span wraps to 187.8px wide with `right: 299.8px` (well inside the 375px viewport) instead of protruding. Went beyond the single named element per this project's multi-element spot-check precedent: expanded all 45 documents on the page simultaneously and confirmed page-level `scrollWidth` stayed 375 with all of them open, and that 0 of 4,462 inline `<code>` spans inside `.doc-content p`/`li` protrude past the viewport anywhere on the page — checked the 5 longest spans found (152–361 chars) across 5 different documents/features (`doc-f4-release`, `doc-f5-plan`, `doc-f7-plan`, `doc-f0-release`, `doc-f2-plan`), confirming the fix is the systemic `.doc-content`-wide rule it claims to be, not a one-off patch for the originally-named span. A CSS-rule regression test was added by the fix so this can't silently regress the way the F2 `.sr-only` gap did. | fixed (verified) |

**Note on methodology:** this pass repeatedly hit the documented "black screenshot after JS-driven scroll / hash navigation" tooling quirk (confirmed here across JS `scrollIntoView`, hash-link clicks, and even plain mouse-wheel scroll — the quirk is broader than the task description anticipated, but consistent with it). Every finding above was cross-checked via `get_page_text`, `read_page`, and `javascript_tool` DOM/style/geometry queries rather than trusting or dismissing a black frame either way; B1 in particular is confirmed by direct pixel geometry (`getBoundingClientRect`), not a screenshot. Two full-page screenshots did succeed (immediately after a fresh `navigate`, before any scroll/interaction) and both visually confirm the newest-first index ordering at desktop and mobile width.

**Note on a false-positive I ruled out myself:** an early, less careful check (matching a dedup link's *parent* `textContent` prefix to guess which member it belonged to) appeared to show `mcp-server`'s "Documents shown under v0.4.0" link pointing at `snapshot-report`'s content instead — a suspicious near-miss. Re-derived properly via `closest('[id^="member-"]')` to find the link's true owning member (rather than trusting the DOM-order proximity of a preceding "← Back to index" link), all 7 dedup links on the page, including this one, resolve correctly. Recorded here per this project's own precedent of re-deriving a suspected bug from scratch before either confirming or ruling it out, rather than acting on the first signal.

## 4. Console & Network

- **Console:** checked repeatedly across the whole session (index load, every `<details>` expansion, hostile-fixture render, mobile resize, keyboard navigation) via `read_console_messages` — zero log/warn/error entries at any point.
- **Network:** checked via `read_network_requests` across the whole session — only `GET .../release-board.html` requests appear (the initial load plus repeated navigations during testing, all `200 OK`). No font, script, image, stylesheet, or any other request fired at any point, including while expanding documents or toggling `<details>` — confirms zero runtime dependencies (ADR-5), even though document content is read from disk at *render* time, not view time.

## 5. Verdict

**Round 2 (this pass):** Would I demo this to a stakeholder right now? **Yes.** Round 1 established
that both Must stories (US-1 newest-first ordering, US-2 full-document viewing with honest empty/
missing/truncated states and safe escaping) pass every one of their acceptance criteria, verified
hands-on, including deliberately adversarial re-derivation of the two riskiest claims (the
hostile-script escaping, and the multi-release dedup link actually landing on the right content
rather than just "a" link). US-3's structured rendering (headings via `aria-level`, real tables
with distinct captions, color-independent checklists) is also fully verified and demo-ready.

Round 1's single blocker, B1 (real embedded document prose breaking the page's "no horizontal
scroll" mobile bar because inline `<code>` spans never got the `word-break` treatment that `<pre>`
blocks already have), was fixed and is now independently re-verified in this round — not on the
fixer's word, but by reproducing the exact original repro fresh (freshly regenerated page, fresh
browser session) and then going further: expanding all 45 documents simultaneously at 375px and
confirming zero of 4,462 inline `<code>` spans protrude anywhere on the page, spread across 5
different documents/features, not just the one span named in the original bug report. This
confirms the fix is the systemic `.doc-content`-wide CSS rule it claims to be. No regressions were
found in the flows that sit next to this fix (newest-first index order, structured document
rendering at desktop, console cleanliness) — each spot-checked live this round per this project's
"fixes love breaking their neighbors" precedent.

---

## ✅ QA GATE

*All boxes checked → `/go-live` may start. Any box open → back to `/increment`, then re-run `/demo-day`.*

- [x] Every Must-story acceptance criterion verified in the real browser and passed
- [x] Every browser-observable NFR verified and passed — NFR-5 re-verified round 2: B1's fix
  confirmed live (`scrollWidth === clientWidth === 375` at the original repro and with all 45
  documents expanded; 0/4,462 inline `<code>` spans protrude)
- [x] No open Blocker or Major bugs (Minor bugs listed and accepted by the user) — B1 closed,
  independently re-verified fixed
- [x] Browser console free of errors on the tested flows
- [x] Tested on all agreed viewports (desktop 1280×800, mobile 375×812)
- [x] Status set to `passed`
