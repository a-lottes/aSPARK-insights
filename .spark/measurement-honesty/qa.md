# QA Report: measurement-honesty

| | |
|---|---|
| **Phase** | Review (hands-on) |
| **Owner** | QA Tester (`/demo-day`) |
| **Input** | Three served `insights render` pages (8940/8941/8942) + a self-built hostile fixture; `.spark/measurement-honesty/spec.md` (approved), `review.md` (passed) |
| **Status** | `passed` |
| **Date** | 2026-08-09 |

## 1. Test Environment

- **App URL:**
  - `http://127.0.0.1:8940/report.html` — real dogfood snapshot (this repo, stale graph, `--as-of 2026-08-09`)
  - `http://127.0.0.1:8941/report.html` — empty-graph snapshot (fresh-repo first run)
  - `http://127.0.0.1:8942/report.html` — orchestrator's hostile fixture (`<script>` in `subject_id`/`reason`/`graph_staleness.changed`, stale=true, inconclusive probe)
  - `http://127.0.0.1:8943/my_hostile.html` — **my own** hand-built hostile fixture (attribute-breaking / `<img onerror>` / `<svg onload>` vector, plus a novel top-level provenance field), rendered via the real `render_html`, served on my own port and torn down after.
- **Browser / viewport(s):** Chromium (Browser pane). Desktop (1280x800), mobile 375x812, exploratory 320x700.
- **Test data / accounts used:** No accounts. Real CLI spot-checks (`insights build/query/render/verify/diff`) against this repo's real `.aspark-graph/graph.json`, plus a mutated pre-release-style snapshot I constructed to exercise `verify`/`diff`.
- **Tooling note:** All contrast, byte-offset, focusable-count, and horizontal-scroll assertions were measured via `getComputedStyle`/`outerHTML`/`scrollWidth` in the live page (this project's "measure, don't eyeball" precedent), not read from source.

## 2. Acceptance Criteria Verification

<!-- US-1/US-2/US-3/US-5 are build-time/JSON-shape guarantees; the primary browser surface is US-4 + NFR-4.
     US-1/US-2/US-5 rows below rest on CLI steps I performed; US-3/AC-3.* filesystem-safety and US-6 README are
     verified by /peer-review (254 green tests) and are not browser-observable — noted, not claimed as browser-tested. -->

| Spec ID | Steps performed | Expected | Observed | Result |
|---|---|---|---|---|
| AC-4.1(i) trigger | Loaded 8940, 8942, 8941; counted `NOT COMPUTED` blocks via DOM | Caveat on 8940 & 8942, absent on 8941 | 8940: 1 caveat; 8942: 1 caveat; 8941: `notComputedCaveatCount=0` | ✅ pass |
| AC-4.1(ii) placement | On 8940/8942: caveat after summary, before Provenance section | Top band, after `<h1>`+summary, before `#provenance` | Caveat's parent is `<body>`, sits after summary + stale cue, before Provenance | ✅ pass |
| AC-4.1(iii) content | Read caveat text on 8940/8942 | Count-first ("N of M"), then affected ids, then pointer; no full reason in band | "NOT COMPUTED — 2 of 8 metrics could not be computed … Affected: TRC-002, TRC-004-unverified-acs. See the Metrics table below." (8942: "2 of 3") | ✅ pass |
| AC-4.1(iv) stacking | On 8940 & 8942 (both stale): checked order + first words | STALE cue first, NOT COMPUTED second; distinguishable by first word | First words `STALE` vs `NOT`; both stale pages render stale cue first | ✅ pass |
| AC-4.1(v) byte-offset check | `outerHTML.indexOf()` on top stale-cue / caveat / provenance | topStale < caveat < provenance | 8940: 1292 < 1384 < 1594 (`order_ok=true`); 8942 order confirmed too | ✅ pass |
| AC-4.2 row-level reason | Read Metrics table rows for TRC-002 & TRC-004-unverified-acs on 8940 | Full `Not computed: <reason>` still shown per row | Both rows show full reason with both counts + filenames; top-band notice is additive | ✅ pass |
| AC-4.3 empty page | Loaded 8941; queried DOM for caveat + empty-notice | No evidence-caveat; `.empty-notice` "No facts recorded" still renders | `notComputedCaveatCount=0`, `staleCueCount=0`, `emptyNoticePresent=true` (class `empty-notice`) | ✅ pass |
| AC-4.4 label + escaping | 8942 + my own 8943 fixture; DOM script/img/svg element count, console | Textual label (not color-only); `<script>`/payloads escaped, page renders, exit 0 | Label word `NOT COMPUTED`; 8942: 0 script els, 3 escaped `&lt;script&gt;`; 8943: 0 script/img/svg els, all payloads escaped; console clean | ✅ pass |
| AC-4.5 static/self-contained | Network tab across all pages; script count; section order | No JS, no external fetch, fixed section order | 0 `<script>` elements everywhere; only same-origin `report.html` GET, no external hosts | ✅ pass |
| AC-4.6 probe provenance renders | Provenance tables on 8940 (present), 8941 (absent), 8942 (inconclusive) | Probe record renders on every report, field/value rows | 8940 outcome=present (10 files, qa.md/review.md); 8941 outcome=absent (0); 8942 outcome=inconclusive + detail curated string — all rendered | ✅ pass |
| AC-1.5 (CLI spot-check) | `insights build`+`query` on this repo | TRC-002 & TRC-004-unverified null+reason; others computed | TRC-002/004-unverified `value=null`; TRC-001=1.0, TRC-003=0.875, TRC-004-orphan=0, TRC-005-* computed | ✅ pass |
| AC-2.1 / D7 (CLI) | Inspected reason strings | Both counts + filenames; word-first (`reason[0].isdigit()==False`) | "no verifies-from-passing-QACheck edges found in the graph (0 of 41); 10 matching artifact file(s) found under .spark/ (qa.md, review.md)"; leading_digit=False | ✅ pass |
| AC-2.3 inconclusive reason | 8942 TRC-004-unverified-acs row + provenance | Reason names evidence absent AND on-disk check inconclusive w/ cause | "…; on-disk check inconclusive (could not list .spark/: permission denied)"; probe outcome=inconclusive, detail curated | ✅ pass |
| AC-2.5 (CLI) | Queried provenance on this repo | Probe sealed in provenance on every build, counts/flags only | `artifact_probe` present: outcome/feature_dir_count/matched_file_count/matched_filenames/detail — no paths/usernames | ✅ pass |
| AC-5.1 (CLI) | Inspected metric_versions | 5 metrics at 2.0.0, TRC-005-* at 1.0.0 | Exactly that | ✅ pass |
| AC-5.2 (CLI) | Scanned for duplicate metric_ids | Exactly one entry per id | No duplicates found | ✅ pass |
| AC-5.3 (CLI) | `insights diff` old(mutated) vs new | Shows version + value change together | TRC-002: v1.0.0/value 0.0 (a) → v2.0.0/value null+reason (b) | ✅ pass |
| AC-5.4 (CLI) | `insights verify` against mutated pre-release snapshot | `verify_mismatch` named error, exit 1, no traceback | Clean JSON `{"error":"verify_mismatch",...}`, exit=1, no traceback | ✅ pass |
| NFR-1 performance | `time insights build` on this repo | Probe adds <1s; build stays fast | Build ~0.31s total wall-clock | ✅ pass |
| NFR-4(a) heading structure | DOM heading scan + caveat siblings on 8940 | Block-level, no new heading, no skipped level, not between h2 & its content | h1→h2→h2→h2 no skip; caveat parent `<body>`, prev sibling is stale-cue `<p>` (in band 1) | ✅ pass |
| NFR-4(b) textual label | Read caveat opening token | Textual label, never color alone | Opens `NOT COMPUTED —`, distinct from `STALE —` | ✅ pass |
| NFR-4(c) contrast | `getComputedStyle` on caveat (8940) | text/bg ≥4.5:1, border/page ≥3:1 | text #7a4a00 on #fff6e5 = **6.97:1**; border #7a4a00 vs page #fff = **7.48:1**; no new hue introduced | ✅ pass |
| NFR-4(d) 375px wrap | Resized to 375 (and 320) on 8940 | id list wraps, no horizontal scroll, not inside `.table-wrap` | 375: scrollWidth==clientWidth==375, caveat 134px tall (wrapped), `insideTableWrap=false`; 320: no h-scroll | ✅ pass |
| NFR-4(e) no interactive els | `querySelectorAll('a,button,input,select,textarea,[tabindex]')` on all pages | length == 0 | 0 on 8940, 8941, 8942, 8943 | ✅ pass |
| NFR-5 determinism | Built + rendered twice to separate outputs; hashed | Byte-identical snapshot & report | Identical snapshot hash and identical report hash; report hash matches served 8940 page | ✅ pass |
| NFR-6 (cli lens) | `insights build --help` | Documents that build also *reads* `<repo>/.spark/` (a read, never a write) | Help text documents the `.spark/*/{qa.md,review.md}` presence read explicitly | ✅ pass |

## 3. Exploratory Findings

<!-- Beyond the ACs: reloads, mobile mid-flow, deep links, own-built hostile inputs. -->

| # | Severity | Steps to reproduce | Expected vs. observed | Status |
|---|---|---|---|---|
| B1 | — (no defect) | Built my own hostile snapshot with attribute-breaking `"><img src=x onerror=alert(101)>`, `<svg/onload=alert(102)>`, quote-breaking `'"><script>alert(103)</script>`, a payload nested in a fact `value` dict, and a **novel** top-level provenance field `future_field`; rendered via real `render_html`; served on 8943; loaded in browser | Expected: all escaped, nothing executes, key-driven provenance tail escapes the new field too. Observed: 0 script/img/svg elements created, all payloads present only as escaped entities (7×`&lt;img`, 5×`&lt;svg`, 4×`&lt;script&gt;`), no `onerror` fetch in network tab, console clean, `future_field.evil` rendered escaped. The `_esc` choke-point holds against a different vector than the prepared fixture. | not a bug — escaping confirmed by independent re-derivation |
| B2 | Minor (accepted) | Observe caveat count vs spec §1 illustrative "4 qa.md files" | Spec §1's success-signal wording ("4 `qa.md` files") is illustrative and predates later feature dirs; the live count is 10 matching files across 6 feature dirs (qa.md + review.md). Reason string and provenance agree (`matched_file_count=10`), so the number is internally consistent and truthful — just larger than the spec's example. No reader-facing defect. | accepted — spec text was explicitly "illustrative, not prescriptive" (AC-2.1) |
| B3 | — (no defect) | Reloaded each page multiple times; hashed served bytes twice via curl | Identical every time (static, no server-side state); 320px & browser-resize exploration never produced page-level horizontal scroll | not a bug |
| B4 | — (no defect) | On mobile 375px, the Provenance/Metrics/Facts **data tables** scroll inside their own `.table-wrap` container (Value column clipped at 375) | This is the pre-existing `snapshot-report` behavior (accepted B2 there), NOT this feature's caveat. The caveat itself is confirmed outside any `.table-wrap` and wraps correctly. Out of scope for measurement-honesty. | pre-existing, out of scope |

## 4. Console & Network

- **Console:** Clean on all four pages. No errors, no warnings, and critically **no `alert` dialogs** fired on either hostile fixture (8942 or my own 8943) — verified via `read_console_messages` and the absence of any dialog interruption.
- **Network:** Each page issues exactly one same-origin `GET report.html → 200`. No external hosts, no CDN, no fonts, no fetch/XHR. The `<img src=x onerror=...>` payload on my 8943 fixture produced **no** request for `x` — confirming no `<img>` element was ever created (escaped to text). Fully self-contained (AC-4.5).

## 5. Verdict

**PASS — I would demo any of these three pages to a stakeholder right now.**

The feature does exactly what it promises and nothing more. On the real dogfood page (8940) the two previously-fabricated numbers (`TRC-002`, `TRC-004-unverified-acs`) now read `Not computed:` with a word-first reason naming both what was observed in the graph (0 of 41) and on disk (10 matching qa.md/review.md files) — the "here is your actual bug" diagnosis the spec set out to deliver. The top-band `NOT COMPUTED` caveat stacks correctly under the `STALE` cue (verified by byte offset, distinguished by first word, not hue), reaches the skimming reader, and is backed by the full row-level reason for screen-reader navigation (AC-4.2). The empty page (8941) correctly renders **no** caveat while keeping its empty-facts notice, so the fresh-repo first screen is unchanged. The probe record renders in Provenance on all three disk outcomes (present / absent / inconclusive), closing the invisible-disclosure gap C7/D5 identified.

The one verification `/peer-review` explicitly deferred to me — NFR-4's live contrast and 375px measurements — passes with margin: 6.97:1 text and 7.48:1 border contrast, clean wrapping with no horizontal scroll at 375px or even 320px, zero interactive elements, no skipped heading levels. The security fix survives independent adversarial re-derivation: I built my own hostile fixture from scratch with an attribute-breaking / `onerror` / `onload` vector and a novel provenance field the prepared fixture never used, and the single `_esc` choke-point escaped every one — no script, no image load, no alert, no external request. Determinism holds byte-for-byte across independent builds and renders.

No Blocker, Major, or Minor defects. B2 (live count 10 vs the spec's illustrative "4") is a truthful, internally-consistent number, not a bug.

---

## ✅ QA GATE

*All boxes checked → `/go-live` may start. Any box open → back to `/increment`, then re-run `/demo-day`.*

- [x] Every Must-story acceptance criterion verified in the real browser and passed (US-4/NFR-4 browser-verified; US-1/US-2/US-5 build-time ACs spot-checked via real CLI; US-3 filesystem-safety and US-6 README are non-browser, covered by `/peer-review`'s 254 green tests)
- [x] Every browser-observable NFR verified and passed (NFR-1 timing, NFR-4 a–e, NFR-5 determinism, NFR-6 help text)
- [x] No open Blocker or Major bugs (Minor B2 listed and accepted; spec itself marks the count illustrative)
- [x] Browser console free of errors on the tested flows
- [x] Tested on all agreed viewports (desktop 1280, mobile 375, exploratory 320)
- [x] Status set to `passed`
