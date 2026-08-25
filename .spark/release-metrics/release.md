# Release: release-metrics

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `released` |
| **Version** | v0.11.0 (released — pushed to `origin/main`, tag `v0.11.0` pushed) |
| **Date** | 2026-08-25 |
| **Ticket** | none (spec.md header states none) |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report updates it in the same edit that changes status or actions:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `released`. The user gave explicit publish authorization in this conversation for
  both the local commit/tag and the push; both were executed and verified. Release commit
  `023f23a8023aa565ecc1e406bbd9c87809055c47` + docs checkpoint commit
  `ce4bc8c86a09bed05643f42aafc0499c54aa5e23` + annotated tag `v0.11.0` (target `023f23a8`) all
  pushed to `origin` (`1af5b5a..ce4bc8c` on `main`). `git ls-remote origin` confirms
  `refs/heads/main` at `ce4bc8c8` and `refs/tags/v0.11.0` at `71490ff7` (tag object) resolving to
  `023f23a8`. **Post-release smoke check run and green** (§3): `insights releases --as-of
  2026-08-25 --format html` produces a valid page (doctype present; top-level figures band with
  all 8 figures — tagged releases, first/last release, median gap, gap range, features delivered,
  delivered scope, commits since last release; cadence strip present as `cadence-bar` rows,
  correctly including the new `v0.10.0 → v0.11.0` gap; 11 per-card `<dl class="figures-band
  release-figures">` headers present, including the new v0.11.0/release-metrics card itself); and
  `--format json` exits 0 with valid, parseable JSON (12 releases, including the untagged
  in-progress entry).
- **Summary:** v0.11.0 adds measured time-and-size figures to the release board — a date, commit
  count and work-type mix on every real release; a stated delivered-vs-trailing attribution rule so
  a feature's scope is no longer double-counted across its bookkeeping commits; a project-wide
  figures band and cadence strip; and (Should, US-4) a per-release figures header on each detail
  card. One disclosed known limitation carries into this release unresolved by design: the 5-second
  performance bar (NFR-8) is not met (see §2).
- **Open:** none for this feature. Unrelated: the pre-existing untracked
  `.spark/git-native-mid-cycle-board/release.md` remains untouched, flagged again in §4 as a
  cleanup item now spanning at least four release cycles unaddressed.
- **Binding ruling:** §3 Release Actions and the KEEP GATE below carry the final ruling.
- **On conflict:** the numbered body below wins for everything except `Status`/`Version`; log the
  mismatch as a finding at the next `/go-live` and proceed — don't stop on it.

## 0. Gate Check (done before anything else)

- **`review.md`** — Status `passed` (header table + Handoff block). REVIEW GATE (foot of file)
  fully checked: no open Blocker, no open Major (F1-F3 fixed and independently re-verified by the
  reviewer's own fresh fixtures across two rounds; **F4 waived by the user**, reason recorded in
  its §3 row — a spec-wording-vs-measured-reality mismatch on NFR-8/AC-1.1/AC-3.1, not a code
  defect, with a spec-amendment follow-up tracked separately), every Must AC traces to code, all
  plan deviations documented, suite green at 679, Status `passed`.
- **`qa.md`** — Status `passed` (header table + Handoff block). QA GATE fully checked: every
  Must-story AC verified live in the browser and passed (AC-1.4 the one named, legitimate exception
  — not forceable live without monkeypatching git internals, relies on review.md's own
  mutation-tested fixture), every browser-observable NFR verified, 0 open Blockers/Majors (1 Minor,
  B1, a stale illustrative number in `spec.md`'s own AC-1.2 prose — already fixed directly in
  `spec.md` by the user, not a code defect), console clean, both viewports tested, Status `passed`.
- **Conclusion: both gates genuinely green.** `/go-live` may proceed. Re-confirmed fresh again
  immediately before the release commit above: both files' header tables and Handoff blocks still
  read `passed`, `git status --short` on the working tree exactly matched the file list this pass
  had already enumerated (no drift since the prepare-only pass), `HEAD` was still `1af5b5a` (the
  same commit `review.md`'s own **Input** row names as its diff base), and no `v0.11.0` tag existed
  yet before this pass created one.

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — confirmed fresh, §0 above
- [x] `qa.md` status is `passed` — confirmed fresh, §0 above
- [x] Full test suite green on the release commit — re-run fresh, right now, on this exact working
  tree (before the release commit was made): `uv run python -m pytest -q` → **679 passed**, 0
  failed, in 537.58s (~9 min — consistent with the disclosed NFR-8 cost recurring across the
  suite's many CLI-invoking integration tests). Matches the count both `review.md` and `qa.md`
  independently report; not copied from either — run by me, now, on this tree. The release commit
  itself changed no tracked file content beyond moving these exact files into history (`git diff
  --stat` against the parent is empty for the resulting commit), so this result stands unchanged
  for `023f23a8`.
- [x] Build succeeds from a clean checkout — `uv build --out-dir <scratch>` →
  `aspark_insights-0.11.0.tar.gz` and `aspark_insights-0.11.0-py3-none-any.whl` both built
  successfully.
- [x] No uncommitted changes in the working tree — after the release commit, `git status --short`
  showed only two untracked files: this report (`.spark/release-metrics/release.md`, written and
  committed separately per §3) and the pre-existing stray `.spark/git-native-mid-cycle-board/
  release.md` (a leftover from an already-released prior feature, flagged again below and in §4 —
  now unaddressed across at least four release cycles), explicitly excluded from the release commit
  by naming files, never `git add -A`.

**Additional pre-flight verification performed (not copied from earlier reports):**
- Version re-derived myself, not trusted from `plan.md`'s T11 note: `pyproject.toml` → `0.11.0`,
  `src/aspark_insights/__init__.py` → `0.11.0`, `uv.lock`'s own `aspark-insights` entry → `0.11.0`.
  All three consistent. Confirmed again post-release: `aspark_insights.__version__ == "0.11.0"` on
  the pushed tree.
- Confirmed `v0.11.0` was **not already tagged** before this pass: `git tag -l | sort -V` listed
  `v0.1.0` through `v0.10.0` only.
- Confirmed the release commit landed on top of `HEAD` (`1af5b5a`, `docs: release-board-docs —
  record actual publish, status released`) — the same commit `review.md`'s own **Input** row
  names as its diff base.
- Read README's "Release board" section (lines 187-260) directly — already updated this cycle with
  the figures-band/cadence-strip/delivery-attribution bullets; changelog below is sourced from this
  plus `spec.md` §4's stories, not re-derived from the diff.

## 2. Changelog

<!-- User-facing language. What can they do now that they couldn't before? -->

### Added
- Each tagged release's card now shows its own release date, how many commits shipped in it, and
  what kind of work they were (features, fixes, docs, and so on) — a release stops being just a
  list of who worked on it and becomes something with a position in time.
- A summary panel now sits above the release list showing, at a glance: how many releases have
  shipped, when the very first and most recent ones happened, how spaced out releases have been
  (with the longest gap called out), how many features have shipped in total, and how much scope
  has actually been delivered.
- Each release's own detail card now opens with its own quick-reference figures — its date, the
  gap since the release before it, which features it actually delivered versus which ones are just
  carrying leftover follow-up work, how much scope that represents, and its commit/work-type mix —
  so you can read one release's whole story without piecing it together from other parts of the
  page.

### Changed
- A feature now counts as "delivered" in exactly one release — the one where it actually shipped —
  instead of being counted again every time a later bookkeeping commit (like recording that
  release's own report) happens to land inside a different release's range. Previously this could
  roughly double a release's reported scope; some releases were showing 1.5x-2.2x more delivered
  work than they actually contained. Every later reappearance of a feature is now labelled clearly
  as carrying follow-up work, not hidden.
- A release that didn't deliver any features now says so in plain words ("no feature was delivered
  in this release") instead of leaving that unclear.
- The gap-between-releases strip and the new summary panel never use color to suggest "this one is
  bad" — every figure is a plain measured number with its own count shown alongside it, and the
  longest gap is called out by label only, never by a warning color.

### Known Limitations
- Generating the HTML release board is slower than the 5-second target this feature aimed for — it
  currently takes roughly 12-14 seconds against this project's own release history. The large
  majority of that time (about 11 seconds) is pre-existing cost from before this release and out of
  this feature's scope to fix; this feature's own added work accounts for well under one second of
  the total. This was found, measured, and disclosed during review rather than hidden, and a
  follow-up to revisit the underlying cost (and the spec's own wording) is tracked separately rather
  than fixed in this release.

## 3. Release Actions

<!-- What was actually executed, with results. -->

| Action | Result |
|---|---|
| Version bump & tag | **Executed.** Bump: `0.10.0` → `0.11.0`, already present in `pyproject.toml`/`__init__.py`/`uv.lock` from `/increment`'s T11 close-out; verified consistent (§1). **Bump-level justification (semver, minor):** a real, additive behavioral change — new measured per-release figures, a project-wide figures band and cadence strip, and delivery-vs-trailing attribution logic (US-1/US-2/US-3, plus Should US-4) — with zero breaking change to any existing CLI flag, subcommand exit code, or JSON key (NFR-2's additive-only claim independently re-verified by the reviewer via byte-comparison). Release commit `023f23a8023aa565ecc1e406bbd9c87809055c47` created (22 files changed, 3307 insertions, 50 deletions), staged by explicit filename list only. Annotated tag `v0.11.0` created, target `023f23a8`. |
| PR / merge | N/A — direct mode. `.spark/constitution.md` has no `Delivery & Handoff` section; this matches every prior release in this repo's history (`v0.1.0` through `v0.10.0`, all local-commit-and-tag with no PR). |
| Deploy | **Executed.** `git push origin main` → `1af5b5a..ce4bc8c main -> main`. `git push origin v0.11.0` → `* [new tag] v0.11.0 -> v0.11.0`. Confirmed on the remote via `git ls-remote origin refs/heads/main refs/tags/v0.11.0`: `refs/heads/main` at `ce4bc8c86a09bed05643f42aafc0499c54aa5e23`, `refs/tags/v0.11.0` at `71490ff7e2558e30fa26a4407629a013fd63df7c` (tag object, target `023f23a8`) — matches local exactly. |
| Post-release smoke check | **Executed, green.** `aspark_insights.__version__ == "0.11.0"` confirmed on the pushed tree. `uv run insights releases --as-of 2026-08-25 --format html` → exit 0, wrote `.aspark-insights/release-board.html`: doctype present (`<!DOCTYPE html>`); top-level `<dl class="figures-band">` present with all 8 figures (tagged releases: 11 → 12 with this release counted separately in the lead sentence "12 releases, newest first"; first release 2026-07-30; last release 2026-08-25; median gap n=10, 2 d; gap range 0-8 d; features delivered 11; delivered scope 49 US/208 ACs; commits since last release 1); cadence strip present as a `cadence-bar`-class table, 10 gap rows including the new `v0.10.0 → v0.11.0` (2 d) row, longest gap `v0.5.0 → v0.6.0` (8 d) still correctly labelled, no warning color used; 11 per-card `<dl class="figures-band release-figures">` headers found live in the rendered DOM (verified by literal-string count, not just quoted-in-docs occurrences), including the new v0.11.0 card itself (`Date 2026-08-25`, `Delivering release-metrics`, `Trailing release-board-docs`, `Delivered scope 4 US / 23 ACs`). `uv run insights releases --as-of 2026-08-25 --format json` → exit 0, valid JSON, top-level keys `figures`/`provenance`/`reason`/`releases`, 12 release entries. |

### Exact pending commands

**Group A — local, reversible (commit + tag). Executed.**

```bash
# Staged exactly the files this feature touched — never git add -A/. (excluded the stray,
# unrelated untracked .spark/git-native-mid-cycle-board/release.md)
git add README.md pyproject.toml uv.lock \
  src/aspark_insights/__init__.py \
  src/aspark_insights/cli.py \
  src/aspark_insights/gitboard/artifactcontent.py \
  src/aspark_insights/gitboard/releaseboard_report.py \
  src/aspark_insights/gitboard/releasemap.py \
  src/aspark_insights/gitboard/scopecount.py \
  tests/test_releaseboard_docs.py \
  tests/test_releaseboard_render.py \
  tests/test_releaseboard_anchors.py \
  tests/test_releaseboard_cadence.py \
  tests/test_releaseboard_figures.py \
  tests/test_releaseboard_security.py \
  tests/test_releasemap_delivery.py \
  tests/test_releasemap_figures.py \
  tests/test_scopecount.py \
  .spark/release-metrics/spec.md \
  .spark/release-metrics/plan.md \
  .spark/release-metrics/review.md \
  .spark/release-metrics/qa.md

git commit -m "feat: release-metrics — measured release figures, delivery-vs-trailing attribution, v0.11.0"
# -> 023f23a8023aa565ecc1e406bbd9c87809055c47

git tag -a v0.11.0 -m "v0.11.0 — release-metrics: per-release date/commits/work-types, delivered-vs-trailing scope attribution, global figures band and cadence strip"
# -> tag v0.11.0, target 023f23a8

# Second commit, this project's established pattern: the release report necessarily describes
# the commit/tag it reports on, so it's committed separately, after Group A above. Written as a
# checkpoint before the push below, per this project's own precedent (release-board-docs).
git add .spark/release-metrics/release.md
git commit -m "docs: release-metrics — record prepared release, tag created, push authorized"
# -> ce4bc8c86a09bed05643f42aafc0499c54aa5e23
```

**Group B — outward-facing (explicit go already given by the user in this conversation).
Executed.**

```bash
git push origin main
# -> 1af5b5a..ce4bc8c  main -> main
git push origin v0.11.0
# -> * [new tag]         v0.11.0 -> v0.11.0
```

This report's own third commit (recording the final `released` status, push confirmation and
smoke-check results below) is written after the above and pushed to `origin/main` as its own
follow-up commit, matching this project's established pattern (`release-board-docs`'s
`c72259a` → `1af5b5a` sequence).

## 4. Learnings (Keep!)

<!-- The K in SPARK: what does the team keep from this cycle? -->

- **What went well:**
  - The review's own round-2 (self-adversarial re-review) found and closed two new Nits (F14, F15)
    introduced by the fix round itself, using techniques the fix round didn't use — mutation-testing
    every fix by reverting it in `src/` and confirming its cited regression test actually goes red.
    This is the third feature in a row where "don't take the fix on its word" caught something a
    green suite alone would have missed (F15 in particular: a claimed-covered path that was, in
    fact, unpinned). Worth keeping as the standing bar for every future fix-mode round, not just
    security findings.
  - QA independently re-verified every honesty/null-disclosure mechanism (F1/F2/F3/F14) with its
    own fresh, from-scratch hostile fixtures — a script-bearing tag name, an unparseable spec, a
    0-tag repo, a not-yet-delivered feature — never reusing the developer's or reviewer's repros,
    per this project's own adversarial-reproduction bar. All held.
  - A genuine spec-wording gap (F4: NFR-8/AC-1.1/AC-3.1 don't match measured reality) was correctly
    escalated as a Major that only the user could waive, rather than downgraded by any agent — the
    constitution's rule that a Major cannot be waived by any agent held exactly as designed.
  - Version-sync discipline (`pyproject.toml` + `__init__.py` + `uv.lock`'s own entry, all three in
    lockstep) held cleanly again — independently re-verified here for a fourth consecutive release,
    and again post-push against the pushed tree.
  - The post-release smoke check caught the release-metrics feature correctly measuring *itself*:
    the newly pushed `v0.11.0` tag showed up live in its own release board's per-card figures
    (`Delivering release-metrics`, gap `2 d` since `v0.10.0`) within the same pass that published
    it — the most direct possible confirmation that the feature works against real, current repo
    state rather than only fixture data.
- **What we'd do differently:**
  - The stray, never-committed `.spark/git-native-mid-cycle-board/release.md` has now sat untracked
    across at least four release cycles despite being flagged in `release-board-html/release.md`
    and again in `release-board-docs/release.md`. This is precisely the "a repeated note in a
    release report doesn't self-enforce" pattern CLAUDE.md already names for git identity — worth
    resolving directly (commit it, or delete it if stale) rather than flagging it a fifth time.
  - NFR-8's 5-second performance bar is now disclosed-but-unmet across two features in a row
    (originally flagged as an open constitution question in 2026-07-31, now measurably missed by
    2.7x with a named, understood cause). The spec-amendment follow-up F4 tracks should actually be
    scheduled, not left as a standing waiver that recurs at every future `/peer-review` of this
    surface.
  - Unlike this repo's own established two-stage precedent (`release-board-docs` committed+tagged
    locally in one pass, withholding the push for a separate, later pass), this release's user gave
    full authorization for both the local commit/tag *and* the push in the same conversation up
    front. The intermediate checkpoint commit still documented the local state honestly before the
    push ran (Status stayed `preparing` there, not `released`, until the push and smoke check were
    actually confirmed) — worth keeping as the default: never write `released` ahead of the
    verified fact, even when the whole sequence is pre-authorized to run back-to-back.
- **Patterns worth reusing:**
  - Mutation-testing every review/QA fix (revert in `src/`, confirm the cited test goes red) is now
    proven across three features to catch real gaps a green suite hides — worth promoting from
    "good practice" to an explicit `/peer-review` checklist item in this project's own conventions.
  - Sourcing the changelog from both `spec.md`'s user stories *and* the already-updated README
    section (rather than the diff or commit messages) produced changelog language a maintainer
    could hand to a non-technical reader without translation — worth keeping as the default
    `/go-live` technique.
  - Verifying a push not just by "the command returned 0" but by a follow-up `git ls-remote`
    read-back of the actual remote ref — worth keeping as the default push-verification technique
    for every future `/go-live`, alongside the existing "smoke-check the running product" bar.

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

- [x] All pre-flight checks passed at release time — re-run fresh on this exact tree (§1)
- [x] Changelog written in user-facing language — §2, no commit hashes/ticket IDs/internal jargon;
  the one known limitation (NFR-8) stated plainly rather than omitted
- [x] Release actions executed and verified (or `aborted` with reason) — §3: release commit
  `023f23a8`, tag `v0.11.0`, docs checkpoint commit `ce4bc8c8`, push of `main` and the tag to
  `origin` (confirmed via `git ls-remote`), and a green post-release smoke check (HTML + JSON both
  verified against the live pushed tree)
- [x] Learnings recorded — §4
- [x] Status set to `released` — confirmed accurate: push verified on the remote, smoke check
  passed live against the pushed tree, no `handed-off` mode applies (direct mode, no `Delivery &
  Handoff` section in `.spark/constitution.md`)

---

**Rollback path (this project's own established pattern for a pushed release):**

The push has completed (`main` and tag `v0.11.0` are on `origin`). If a problem surfaces now:

```bash
git revert 023f23a8023aa565ecc1e406bbd9c87809055c47   # release commit
git revert ce4bc8c86a09bed05643f42aafc0499c54aa5e23   # docs checkpoint commit (if needed)
git push origin main
```

Never a force-push or history rewrite on `main`. If the tag itself needs to be moved or removed
(genuinely rare — only if `v0.11.0` must stop pointing at bad code), delete and re-push the tag
pointer only:

```bash
git push origin :refs/tags/v0.11.0
git tag -d v0.11.0
```

This feature is additive/confined to the `releases` code path (`releasemap.py`,
`releaseboard_report.py`, new `scopecount.py`) plus doc/test files; `--format json`'s pre-existing
key set is untouched (NFR-2, independently verified by the reviewer via byte-comparison and
re-confirmed here live: `figures`/`provenance`/`reason`/`releases` — no keys removed or renamed),
and it writes only one regenerated output file at render time (`release-board.html`), so there is
no data migration, schema change, or persisted-state backfill in either direction to undo.
