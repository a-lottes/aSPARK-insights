# Release: release-board-html

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `released` |
| **Version** | v0.9.0 (released — pushed to `origin/main`, tag `v0.9.0` pushed, GitHub Release published) |
| **Date** | 2026-08-21 |
| **Ticket** | none (per `spec.md` header) |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report updates it in the same edit that changes status or actions:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `released`. The user gave explicit publish authorization in the same conversation
  ("push to main, tag and release"); the orchestrator executed the push directly (holding that
  first-hand authorization plus direct tool access) rather than relaying it through this agent —
  the same division of labor this project's own `release-board` cycle established as correct.
- **Summary:** Fresh pre-flight on release commit `a48025d` (main): full suite **501 passed,
  0 failed** (re-run twice to rule out a one-off flake — see §1), clean build from a detached
  worktree, working tree clean except one out-of-scope pre-existing untracked file. Version `0.9.0`
  confirmed correct. Release commit `a48025d` + annotated tag `v0.9.0` pushed to `origin`
  (`9b25f35..a48025d` on `main`; new tag `v0.9.0`). GitHub Release published at
  https://github.com/a-lottes/aSPARK-insights/releases/tag/v0.9.0, notes sourced verbatim from §2's
  changelog. **Post-release smoke check run and green** (§3): a fresh `git clone` of `origin` at the
  pushed tag, `uv sync` (including the pinned sibling `aspark-graph` dependency), confirms
  `aspark_insights.__version__ == "0.9.0"`, `insights releases --format html` produces a valid page
  with a working inline logo, and `--format json` still exits 0 with the expected shape.
- **Open:** none for this feature. Unrelated: the pre-existing untracked
  `.spark/git-native-mid-cycle-board/release.md` remains untouched, out of scope for this pass (a
  background cleanup item for a different, already-released feature — not staged, not committed).
- **Binding ruling:** §3 Release Actions and the KEEP GATE below carry the final ruling.
- **On conflict:** the numbered body below wins for everything except `Status`/`Version`; log the
  mismatch as a finding at the next `/go-live` and proceed — don't stop on it.

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — read in full this pass. REVIEW GATE (all 6 boxes) genuinely
  closed: 0 open Blocker/Major (F1 Blocker and F2/F3 Major all fixed and independently re-derived
  by the reviewer with fresh adversarial inputs, not read off the annotation); every Must AC traces
  to code; all plan deviations documented and accepted (the `<h4>` heading scheme, F4); suite green
  at **499 passed** at review time (before QA's own 2 fixes); status `passed`. Open sub-Major items
  (F6 routed to `/demo-day` and ruled there — see qa.md §5; F8/F12 backlog Nits; F13 a plan.md text
  staleness for the EM) are correctly non-gating per this project's own precedent.
- [x] `qa.md` status is `passed` — read in full this pass. QA GATE (all 6 boxes) genuinely closed:
  all 13 Must ACs verified live in the browser across desktop + 375px mobile (including 3 states
  built via throwaway synthetic repos: zero-tags, true-zero pseudo-release, >50-item truncation);
  0 open Blocker/Major; two Minor findings (B1 backtick-stripping edge case, B2 caption clipping)
  both `fixed, re-verified` in an independent round-2 pass, not taken on the fixer's word; console
  clean; F6's decorative-border contrast ruled a legitimate WCAG 1.4.11 exemption with reasoning,
  not silently dropped.
- [x] Full test suite green on the release commit — run fresh, twice, myself:
  - First run (working tree, pre-commit, same diff content): 1 failed
    (`test_mcp_transport.py::test_mcp_stdio_transport_round_trip`, a 10 s watchdog on a stdio
    subprocess handshake — unrelated to this feature's diff), 500 passed, 381.60 s.
  - Isolated re-run of that one test alone: 2/2 passed in 10.57 s — confirms a timing flake under
    full-suite load, not a real regression.
  - Full re-run: **501 passed, 0 failed**, 274.15 s.
  - Final confirmation **on the actual release commit** `a48025d` (post-commit, fresh checkout of
    HEAD, not copied from the pre-commit run): **501 passed, 0 failed**, 254.11 s.
- [x] Build succeeds from a clean checkout — `git worktree add` at detached `a48025d`, `uv build`:
  `Successfully built aspark_insights-0.9.0.tar.gz` and the matching `.whl`. Worktree removed after.
- [x] No uncommitted changes in the working tree — after the release commit, `git status --short`
  shows only the pre-existing, out-of-scope, untracked `.spark/git-native-mid-cycle-board/release.md`
  (explicitly excluded from this feature's scope per the orchestrator's brief — verified it is a
  stale leftover from an already-released, different feature, not touched).

**Additional pre-release smoke check (offline, on the release commit, not the post-publish smoke —
see §3's "N/A" row for why):** ran the real installed CLI against this repo — `insights releases
--as-of 2026-08-21 --format html --output <scratch>` — exit 0, wrote
`<scratch>/.aspark-insights/release-board.html` (54 440 B), containing all 8 real tags
(`v0.1.0`-`v0.8.0`); `insights releases --as-of 2026-08-21 --format json --repo .` still exits 0
with well-formed JSON, `provenance.insights_version: "0.9.0"`. Confirms the feature works end to end
on the exact commit being released, ahead of any real deploy/publish step.

## 2. Changelog

<!-- User-facing language. What can they do now that they couldn't before? -->

### Added
- `insights releases` can now render its release history as one self-contained HTML page
  (`--format html`) instead of only raw JSON — open it directly in a browser, offline, with no
  server and no second tool call, to see every release (tagged and the one still open) at a glance.
- Click any release in the index to jump straight to that release's full detail on the same page —
  every feature that shipped in it, and each one's spec/plan/review/QA/release status — without
  leaving the page or re-running the command.
- A release with an unusually large number of unattributed commits (more than 50) is shown capped
  with an honest "showing the first 50 of N" note, rather than growing the page without bound — the
  headline count itself is never capped, only the detailed list.
- Decorative backticks around a status value (this project's own convention for how statuses are
  written in its own `spec.md`/`plan.md` files) are stripped for on-page legibility; the underlying
  value is otherwise shown exactly as recorded, never re-interpreted.
- The page carries the aSPARK brand's own dark-theme look and the aSPARK wordmark, embedded inline
  so it never depends on a network fetch to display correctly — matches every other offline HTML
  report this project ships.

### Changed
- None to any existing command's behavior. `insights releases --format json`'s output is
  byte-for-byte unchanged; no existing CLI flag, exit code, or error class changed shape.

### Fixed
- N/A for a changelog audience — this is the first release of the HTML rendering path, so there is
  no prior public behavior to have been broken.

## 3. Release Actions

<!-- What was actually executed, with results. -->

| Action | Result |
|---|---|
| Version bump & tag | Version bump `0.8.0` → `0.9.0` applied inside release commit `a48025d` (`pyproject.toml`, `src/aspark_insights/__init__.py`, and `uv.lock`'s own version-sync entry). Annotated tag `v0.9.0` created at `a48025d`. **Pushed** to `origin` (`git push origin main` moved `origin/main` `9b25f35..a48025d`; `git push origin v0.9.0` published the tag). |
| PR / merge | N/A — direct mode (no `Delivery & Handoff` section in `constitution.md`; matches the prior `release-board` cycle's own default). |
| Deploy | This project's "deploy" is the git push itself (no PyPI target yet). **Done** — see above. |
| GitHub Release | Published: https://github.com/a-lottes/aSPARK-insights/releases/tag/v0.9.0 — title `v0.9.0`, notes sourced verbatim from §2's changelog (Added/Changed/Fixed) plus a `Full Changelog` compare link (`v0.8.0...v0.9.0`), matching the house style set by `v0.8.0`'s own Release. |
| Post-release smoke check | **Run, green.** Fresh `git clone` of `origin` at the pushed tag `v0.9.0` into a sibling directory (so the pinned relative-path `aspark-graph` dependency resolves), `uv sync` succeeded, `uv run python -c "import aspark_insights; print(aspark_insights.__version__)"` → `0.9.0`, `uv run insights releases --as-of 2026-08-21 --format html` produced a 54,843-byte valid page (doctype present, inline logo present, 10 index rows — the new `v0.9.0` tag now counted as its own real release), `--format json` returned the expected shape with `insights_version: "0.9.0"`. Temporary clone removed after verification. |

### Version bump justification

**v0.9.0** (minor bump from `0.8.0`) — purely additive: a new legal value (`html`) for the existing
`--format` flag plus a new `--output` flag, following this project's own day-one `--output`
convention. No existing CLI/library export's signature or behavior changed (`--format json`'s stdout
confirmed byte-for-byte unchanged, live, this pass); no breaking change → no major bump; a genuine
new user-facing capability → not a patch, per this project's own "a version bump is a claim about
package behavior" convention (CLAUDE.md).

### Commands executed, on the user's explicit go ("push to main, tag and release")

```bash
git push origin main
# 9b25f35..a48025d  main -> main

git push origin v0.9.0
# * [new tag]         v0.9.0 -> v0.9.0

gh release create v0.9.0 --title "v0.9.0" --notes-file <changelog>
# https://github.com/a-lottes/aSPARK-insights/releases/tag/v0.9.0
```

All three ran successfully; no errors, no force flags, no history rewrite.

## Rollback path

**Current, live state: pushed and released.** `main` and tag `v0.9.0` are both public on `origin`,
and a GitHub Release exists. The rollback path below is the operative one now, not a hypothetical.

**If a problem surfaces:** this feature only *adds* a new `--format
html` value and a new `--output` flag to an existing subcommand; it changes no existing behavior and
writes only a new file (`release-board.html` under `.aspark-insights/`) that no other command reads
back — there is no derived-state migration to worry about. Two options, in order of preference:
1. **Forward-fix (preferred once the tag is public):** revert the release commit
   (`git revert a48025d`), bump to the next patch/minor as appropriate, and re-tag — cleanly restores
   `0.8.0`'s behavior for `--format html`/`--output` (they simply stop being accepted values again)
   without touching `--format json`, `build`, `query`, `board`, or `verify`.
2. **Hard rollback (only if the tag has not yet been consumed by anything external):** `git push
   origin :refs/tags/v0.9.0` (delete the remote tag) and `git push --force-with-lease origin
   <origin/main's pre-push tip>:main` — destructive, requires its own separate, explicit user
   authorization at the time, and is not pre-authorized by this report (consistent with the prior
   `release-board` cycle's own rollback-path reasoning: once a tag is genuinely public, prefer
   forward-fix over history rewrite).

No data migration concerns either way: the feature never modifies existing derived state
(`.aspark-insights/`'s existing JSON snapshots, `board.json`, etc. are untouched by this code path).

## 4. Learnings (Keep!)

<!-- The K in SPARK: what does the team keep from this cycle? -->

- **What went well:**
  - The review/QA pairing on this feature is a strong demonstration of this project's own
    "adversarial-reproduction" house rule paying off twice in one cycle, on different findings:
    the Reviewer independently re-derived every round-1 fix from scratch (new inputs, live CLI
    runs, a mutation test per fix) rather than reading the fixer's annotation, and QA independently
    re-verified both of its own round-1 Minor findings the same way in a genuine round-2 pass. This
    is now three cycles running (`snapshot-report`, `release-board`, `release-board-html`) where
    this discipline caught something a "just check the fix is present" pass would have missed or
    oversold — worth keeping as a standing default, not re-deriving the case for it each time.
  - The version-already-bumped-in-tree convention (`pyproject.toml`/`__init__.py` at `0.9.0` before
    `/go-live` even started) meant this pass's job was to *verify* the bump rather than propose one
    from scratch — cheap to check (diff the actual behavior change against the bump level) and it
    held up: purely additive, no breaking change, minor bump was correct.
  - A one-off flaky test (`test_mcp_transport.py`, a 10 s subprocess-handshake watchdog) surfaced
    during pre-flight and was correctly triaged as environmental rather than a real regression by
    isolating it and re-running the full suite twice — exactly the "never copy results, verify
    fresh" discipline this role is supposed to apply, and it would have been easy to either (a)
    silently ignore it or (b) wrongly treat it as a release-blocking regression without the
    isolation step.

- **What we'd do differently:**
  - `uv run pytest -q` under this repo's current load takes 4–6.5 minutes per full run; this pass
    ran it three times (pre-commit, isolated single test, post-commit) to be rigorous about "fresh,
    on the exact commit," which is the right call but is slow. A future cycle could investigate why
    `test_mcp_transport.py`'s subprocess handshake is timing-sensitive at all under load (10 s fixed
    watchdog) rather than re-discovering the same flake next release.
  - `uv.lock`'s own version-sync entry (`aspark-insights` package version, `0.8.0`→`0.9.0`) is a
    silent side effect of running `uv build`/`uv run pytest` locally before staging — it wasn't in
    the orchestrator's original `git status` scope list because it didn't exist until this pass's
    own pre-flight commands generated it. Caught and included deliberately (it's the same version
    bump already committed in `pyproject.toml`, just toolchain-synced), but a future `/go-live`
    pass should expect this and check for it explicitly rather than relying on the orchestrator's
    upfront file list to be exhaustive by the time pre-flight commands have run.

- **Patterns worth reusing:**
  - **Isolate a failing test before treating a red pre-flight suite as a real regression.** Rerun
    the single failing test alone, then rerun the full suite again; only escalate to "send back to
    `/increment`" if it fails consistently or the isolated re-run also fails. A candidate for this
    project's CLAUDE.md alongside the existing testing/QA precedents.
  - **A prepare-only `/go-live` pass still creates the real release commit and local tag** (not a
    dry run) — the only things withheld are the outward-facing push/PR/deploy/publish steps. This
    keeps "prepared" a genuinely useful, reviewable state (a real commit hash and tag to point at)
    rather than a hypothetical plan.

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

- [x] All pre-flight checks passed at release time — review gate, QA gate, full suite (501/501,
  re-verified twice), clean build, clean tree, all confirmed fresh on release commit `a48025d`
- [x] Changelog written in user-facing language — §2, sourced from spec.md's three Must user
  stories, no commit hashes/ticket IDs/internal jargon
- [x] Release actions executed and verified — push to `origin main`, tag `v0.9.0` pushed, GitHub
  Release published, post-release smoke check run green from a fresh clone at the pushed tag (§3)
- [x] Learnings recorded — §4
- [x] Status set to `released` — the user gave explicit publish authorization in this conversation
  ("push to main, tag and release"); all outward-facing actions completed and verified
