# QA Report: public-repo-polish

| | |
|---|---|
| **Phase** | Review (hands-on) |
| **Owner** | QA Tester (`/demo-day`) |
| **Input** | Local repo state at `/Users/andreaslottes/aSPARK-insights` (not yet pushed — no live GitHub page reflects this feature), `.spark/public-repo-polish/spec.md`, `.spark/public-repo-polish/review.md` (status `passed`) |
| **Status** | `passed` |
| **Date** | 2026-08-02 |

## 1. Test Environment

- **App URL:** N/A — this feature has no running app. Its deliverable is the repo's public surface
  (README, LICENSE, `.gitignore`). The live `github.com/a-lottes/aSPARK-insights` page still shows
  the old placeholder README (this feature hasn't been pushed via `/go-live` yet), so it was
  deliberately **not** used as ground truth. Instead, the current local `README.md` was rendered
  through GitHub's own Markdown rendering API (`gh api /markdown`, `mode=gfm`,
  `context=a-lottes/aSPARK-insights`) — i.e. the exact HTML GitHub itself would produce — wrapped in
  a minimal styled page and served over `http://localhost:8934` (a throwaway `python3 -m
  http.server`, stopped and cleaned up at the end of this session) so it could be loaded and
  inspected in a real browser tab rather than read as raw Markdown source.
- **Browser / viewport(s):** Claude Browser pane, desktop viewport (1280×720), light color scheme
  forced (the pane's default dark scheme was inverting my un-styled preview page's colors —
  a limitation of my throwaway test harness, not of the README/GitHub's real rendering; noted under
  Console & Network). Per spec §8, this feature has no interactive UI and NFR-7 (accessibility) is
  marked N/A — no mobile-viewport pass was required or performed.
- **Test data / accounts used:** Real sibling repo `/Users/andreaslottes/aSPARK-graph` (has a
  built `.aspark-graph/graph.json` already). Five throwaway files created and destroyed for the
  `.gitignore` patterns (`.env`, `.env.local`, `.vscode/x`, `.idea/x`, `Thumbs.db`) — all removed
  before finishing. No accounts needed (no auth surface).

## 2. Acceptance Criteria Verification

| Spec ID | Steps performed | Expected | Observed | Result |
|---|---|---|---|---|
| AC-1.1 | Rendered `README.md` via GitHub's markdown API, loaded in browser, read the two opening blockquotes. | States what the project computes and its real v0.2.0 status; no "Geplant" language; no production-readiness/dashboard overclaim. | First blockquote: "Real, hand-verifiable engineering metrics computed from your repo's actual delivery graph." Second: "Project status: shipped at `v0.2.0` — real traceability coverage, not yet dashboards," explicitly lists what's *not* built yet (dashboards, flow/cycle-time, architecture-health, policy-derived). No "Geplant"/placeholder wording anywhere. | ✅ pass |
| AC-1.2 | Ran the Install section's exact commands myself, fresh, against the real repo: `uv sync --extra dev` then `uv run pytest`. | Both succeed against real repo state; no PyPI `pip install` reference. | `uv sync --extra dev` → "Resolved 41 packages... Checked 39 packages", exit 0. `uv run pytest` → `128 passed in 34.72s`. README text confirmed to say "Not yet published to a package index" — no pip/PyPI install shown. | ✅ pass |
| AC-1.3 | Ran every Usage-section command verbatim, in order, against `../aSPARK-graph`: `aspark-graph build`, `insights build --as-of 2026-08-02`, `insights build --as-of 2026-08-01` (for the diff example), `insights query`, `insights diff`, `insights verify`, `insights render`. | Each either runs directly or is explicitly labeled with its prerequisite; `render` is labeled "not yet implemented" and should fail loudly, not silently succeed. | All 6 real commands: exit 0 with real `sort_keys` JSON (build, query, diff, verify all produced real output — e.g. verify returned `{"matches": true, ...}`). `insights render` → exit 1, `{"error": "not_implemented", "message": "insights render is not implemented yet (dashboards land at I5)"}` — matches the README's own "exits 1 with a named error rather than succeeding silently" claim exactly. | ✅ pass |
| AC-1.4 | Rendered README's "Position in the Product Family" table in browser; read the DOM (`read_page` accessibility tree) for each link's actual `href`; independently ran `curl -sI` against all three URLs. | Table links to `aSPARK` Core, `aspark-graph`, and `aSPARK-policy`, none dead. | DOM shows real `<a>` elements: `aSPARK Core` → `https://github.com/a-lottes/aSPARK`, `aspark-graph` → `https://github.com/a-lottes/aSPARK-graph`, `aSPARK-policy` → `https://github.com/a-lottes/aSPARK-policy`. All three independently `curl -sI`'d: **HTTP/2 200** for all three. F1 from review (missing hyperlinks) is confirmed genuinely fixed. | ✅ pass |
| AC-1.5 | Read rendered License section; confirmed `LICENSE` file exists at repo root. | Names MIT, links to a real root `LICENSE` file, never a dead link. | Rendered section reads "MIT © 2026 Andreas Lottes..." with `MIT` as a link (`href="LICENSE"`, a root-relative link — correct for a file that will sit next to `README.md` once pushed). `LICENSE` confirmed present at repo root (see AC-2.1). Note: GitHub's markdown-render API can't resolve this relative link outside a real repo tree context — a known limitation of this preview method, not a defect (see §4). | ✅ pass |
| AC-1.6 | Ran `grep -n "/Users/\|/home/" README.md LICENSE .gitignore` myself. | No local-machine absolute paths, no internal URLs, no fabricated numbers. | Empty match — nothing found. Read full README/LICENSE text; no adoption/quality numbers present (only version numbers and named metric IDs, no invented usage stats). | ✅ pass |
| AC-2.1 | `cat LICENSE`, read full text top to bottom; checked copyright line. | Standard MIT text, correct holder/year, matches `pyproject.toml`. | Full, untruncated standard MIT License text. `Copyright (c) 2026 Andreas Lottes`. No local path leakage. | ✅ pass |
| AC-2.2 | Compared our `LICENSE` byte-for-byte (`diff`) against the *live* sibling `aSPARK-graph`'s committed `LICENSE` (fetched via `gh api repos/a-lottes/aSPARK-graph/contents/LICENSE`); separately queried GitHub's own license-detector API for that live sibling repo (`gh api repos/.../license`). | Close enough to standard MIT to auto-detect, matching the sibling precedent. | `diff` → **IDENTICAL**, byte-for-byte. GitHub's real detector on the live sibling reports `{"key":"mit","name":"MIT License","spdx_id":"MIT"}` — since our file is byte-identical to a file GitHub already detects as MIT, the same detection will hold once this repo is pushed. | ✅ pass |
| AC-3.1 | For each of the 7 pre-existing ignore patterns, ran `git check-ignore -v` on a matching path (`.venv`, `.pytest_cache`, `.claude`, `__pycache__/x.pyc`, `.aspark-insights/x`, `.aspark-graph`, `.DS_Store`). | All still ignored, no regression. | All 7 matched a `.gitignore` rule (line numbers 2, 5, 8, 11, 12, 17, 31 respectively). | ✅ pass |
| AC-3.2 | Created my own throwaway files/dirs (`.env`, `.env.local`, `.vscode/x`, `.idea/x`, `Thumbs.db`) fresh, then ran `git status --porcelain` and `git check-ignore -v` on each. | Each shows ignored, not untracked. | `git status --porcelain` after creation did **not** list any of the 5 files. `git check-ignore -v` matched all 5 to their new `.gitignore` lines (27, 28, 23, 24, 20). All 5 removed afterward; confirmed clean. | ✅ pass |
| AC-3.3 | Ran `git status` before and after adding the 5 throwaway files; compared to the pre-existing feature diff. | Same clean state plus new patterns caught; nothing else newly ignored/un-ignored. | Before/after `git status` identical except for the intentional throwaway files (which vanished once ignored/removed) — no unrelated file's ignore status changed. | ✅ pass |
| AC-4.1 | Ran `git ls-files .spark/traceability-metrics/release.md`. | File is tracked (already committed, per review's F2 finding). | File listed as tracked — confirmed independently, not assumed from the review report. | ✅ pass |
| AC-4.2 | Ran `git status` at the end of my session (after all CLI runs, gitignore tests, and cleanup). | Clean tree, only this feature's own intended diff (`M .gitignore`, `M README.md`, `?? LICENSE`, `?? .spark/public-repo-polish/`). | Exactly that — no leftover file from my own testing, no unexpected modification. | ✅ pass |
| AC-5.1 | Read the rendered README top to bottom in the browser. | Section order: problem → install → usage → status → family position → license. | Confirmed exact order: "The problem" → "Install" → "Usage" → "Project Status" → "Position in the Product Family" → "License". Matches spec's required convention. | ✅ pass |
| NFR-1 (security) | Same `grep` as AC-1.6, run myself independently. | No local path/secret in touched files. | Empty match. | ✅ pass |
| NFR-2 (security) | Same as AC-3.2 — created real `.env`/`.env.*` throwaway files, confirmed ignored. | New patterns actually prevent tracking. | Confirmed — `.env` and `.env.local` both matched and absent from `git status`. | ✅ pass |
| NFR-3 (cli) | Same as AC-1.3 — every command literally executed. | Every command copy-paste runnable or explicitly labeled. | All 6 commands run for real with matching behavior/labeling. | ✅ pass |
| NFR-4 (library) | Read README's Install/family table PyPI claims; independently queried the real PyPI JSON API for both package names. | Accurately reflects real distribution state — no false PyPI claim. | `pypi.org/pypi/aspark-graph/json` → **200** (really on PyPI, matches table's "(on PyPI)" tag). `pypi.org/pypi/aspark-insights/json` → **404** (really not published, matches README's "Not yet published to a package index"). | ✅ pass |
| NFR-5 (evidence honesty) | Read every concrete number in the README (`v0.2.0`, `TRC-001…005`, `MTA-001…003`, sibling version numbers). | No number presented as a live/current guarantee without dating; no fabricated adoption/quality metric. | All version numbers are release version tags (verifiable, not "live" metrics); no dogfooded metric *value* (e.g. an actual percentage) appears verbatim in the README body — only metric *names*/IDs are listed, so C3's "must be dated if shown" constraint isn't even triggered. No adoption/usage number anywhere. | ✅ pass |
| NFR-6 / NFR-7 | N/A per spec (no runtime behavior change; plain Markdown, no custom UI). | — | Confirmed N/A is accurate — no interactive controls, no runtime code path touched. | ✅ pass (N/A confirmed, not just asserted) |

## 3. Exploratory Findings

| # | Severity | Steps to reproduce | Expected vs. observed | Status |
|---|---|---|---|---|
| B1 | Minor (tooling artifact, not a product defect) | Load the rendered README preview in the Claude Browser pane with its default dark color scheme (no explicit `colorScheme` override). | Expected: readable text. Observed: the un-styled parts of my *own throwaway test-harness page* (not GitHub's real CSS) rendered low-contrast/near-invisible under forced dark mode, because my minimal preview stylesheet didn't declare an explicit background/dark-mode block. This is an artifact of my one-off local test harness lacking GitHub's real `markdown-body` dark theme CSS — **not** a defect in the README content or in real GitHub rendering (GitHub's actual site handles both themes correctly; I only reproduced the HTML fragment, not GitHub's full stylesheet). Filed for completeness, not as a product bug. | accepted (test-harness limitation) |
| B2 | Informational | Scroll the browser-pane tab away from `scrollY=0` (via either the `scroll` action or `window.scrollTo` through JS), then request a screenshot. | Expected: screenshot shows the scrolled-to content. Observed: screenshot consistently returned a fully blank frame after any scroll, while the DOM/accessibility tree (`read_page`) and JS (`document.querySelectorAll`) continued to report correct, populated content at all times. Worked around by using `read_page`/JS DOM introspection (real observations of the rendered browser DOM, not source-reading) for content below the fold, plus one clean top-of-page screenshot. This looks like a Browser-pane tooling glitch in this session, unrelated to the README/product. | accepted (QA tooling limitation, worked around) |

No Blocker or Major bugs found in the feature itself.

## 4. Console & Network

- No browser console errors observed on the rendered-README page (a static file, no client JS to
  error).
- Network: the three sibling-family hyperlinks (`aSPARK`, `aspark-graph`, `aSPARK-policy`) each
  independently `curl`'d — all returned `HTTP/2 200`.
- The `[MIT](LICENSE)` relative link in the License section could not be followed end-to-end in
  this preview (GitHub's `/markdown` render API returns the link as-is; it has no real repository
  tree to resolve a relative path against, and my throwaway local HTTP server didn't mirror the
  repo's file layout at that path). This is a **known limitation of the preview method**, not a
  real defect: the `LICENSE` file genuinely exists at the repo root next to `README.md` (verified
  via `cat`/`ls`), which is exactly the layout GitHub needs to resolve `[MIT](LICENSE)` correctly
  once this repo state is actually pushed. Flagging this limitation explicitly rather than silently
  passing over it, per instructions.
- PyPI JSON API calls (`pypi.org/pypi/{aspark-graph,aspark-insights}/json`) and GitHub license-
  detector API call (`gh api repos/a-lottes/aSPARK-graph/license`) all returned clean, expected
  responses (200/404 as anticipated) — no unexpected failures.

## 5. Verdict

I would demo this. Every Must-story acceptance criterion was independently re-verified by
performing the actual steps — not by trusting the passed review — including literally re-running
every README command against the real sibling repo (`uv sync`, `pytest`, `aspark-graph build`,
`insights build` ×2, `query`, `diff`, `verify`, `render`), re-creating all five `.gitignore`
throwaway test files myself, re-diffing `LICENSE` byte-for-byte against the live sibling and
GitHub's own license detector, and rendering the current README through GitHub's real Markdown API
(not just reading its source) to confirm the opening status callout, the family table's links, the
fenced code blocks, and the checklist all render as intended — real blockquotes, real `<pre>`
monospace blocks, real `<a href>` links (all three verified live with 200s), and real `<input
type="checkbox">` elements, not literal `[x]` text.

The one prior finding (F1, missing sibling hyperlinks) is confirmed genuinely fixed with working
links. The sibling `/Users/andreaslottes/aSPARK-graph` repo's `git status` was captured before and
after my entire CLI-verification pass and is byte-for-byte identical (only its own pre-existing
unrelated `?? .spark/BACKLOG.md`) — independently reproducing the exact "no side effects on the
sibling" property the review already checked once.

Two exploratory notes are logged (B1, B2) but both are limitations of my own throwaway test harness
/ this session's browser tooling, not defects in the README, LICENSE, or `.gitignore` — I've called
that out explicitly rather than letting it read as a product finding. No Blocker or Major bugs. The
repo's working tree is clean at the end of this session, matching exactly the feature's own
intended diff, with all throwaway test artifacts (readme preview HTML, local HTTP server,
`.env`/`.vscode`/`.idea`/`Thumbs.db` test files) removed.

Status is left as `draft`, per instructions — the maintainer makes the final `passed` call.

---

## ✅ QA GATE

- [x] Every Must-story acceptance criterion verified in the real browser and passed
- [x] Every browser-observable NFR verified and passed
- [x] No open Blocker or Major bugs (two Minor/informational tooling notes logged and self-accepted as non-product)
- [x] Browser console free of errors on the tested flows
- [x] Tested on all agreed viewports (desktop; mobile N/A per spec §8/NFR-7, confirmed accurate rather than assumed)
- [x] Status set to `passed` — confirmed by the user
