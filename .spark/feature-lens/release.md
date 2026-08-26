# Release: feature-lens

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `released` |
| **Version** | v0.12.0 (committed and tagged — commit `4eb87f1cabb5bb7c44926c64cd9310f06860bbff`, annotated tag `v0.12.0`) |
| **Date** | 2026-08-26 |
| **Ticket** | none (`spec.md` header states none) |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report updates it in the same edit that changes status or actions:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `released`. The user gave explicit, real authorization in-conversation to publish
  (local commit+tag **and** the push). Both gates were confirmed green in §0 before anything else.
  Pre-flight was re-run fresh, right now, on the current `HEAD` — which had moved by one unrelated
  commit since the prepare-only pass wrote this report (`cb8b6647` → `9b98393b73212be8c8b840f311594c72f7dac54c`,
  a standalone documentation fix for a completely different, already-released feature,
  `git-native-mid-cycle-board`/`v0.7.0` — not part of this release, not referenced in this
  release's commit message, mentioned here only for HEAD-drift bookkeeping): **750 tests passed, 0
  failed** (`uv run pytest -q`, 443.32s), a clean `uv build` producing `aspark_insights-0.12.0.tar.gz`/
  `.whl`, and the working tree confirmed to match the exact 5-modified + 10-feature-lens-untracked
  shape §1 of the prepare-only pass described — with the one difference correctly accounted for:
  `.spark/git-native-mid-cycle-board/release.md` is no longer untracked, having been committed
  separately in `9b98393` (independent of this release). The local release commit and annotated tag
  were then created exactly as prepared in §3; the outward-facing push (`origin main` + `origin
  v0.12.0`) followed once this file's local update was itself committed, per this project's
  established pattern of committing the release report as its own step. The outward-facing push
  then succeeded: `git push origin main` moved `origin/main` from `cb8b664` to `08522a6` (confirmed
  via `git ls-remote`), and `git push origin v0.12.0` created the remote tag, confirmed dereferencing
  to `4eb87f1cabb5bb7c44926c64cd9310f06860bbff` (`git ls-remote origin refs/tags/v0.12.0^{}`). The
  post-release smoke check then ran clean: `insights features --as-of 2026-08-26 --format html`
  rendered a real doctype'd page with a 9-column `lens-table` covering all 12 real
  `.spark/<feature>/` directories (including `feature-lens` itself, now correctly shown as
  `release: released`), a pipeline section with the `Released` bucket populated and `Spec`/
  `Increment`/`Review`/`QA` each showing their honest empty-notice; `--format json` exited 0 with
  the expected `features`/`provenance`/`reason` shape. See §3 for the full record.
- **Summary:** `insights features` — a new subcommand adding a feature-centric view of the same data
  the release board already computes: one row per `.spark/<feature>/` directory (its own spec date,
  5-artifact status, and the single release it actually delivered in), a derived honest current-gate
  label, and (HTML only) a pipeline section grouping every feature by that gate. Purely additive; no
  existing subcommand, flag, or exit-code meaning changes.
- **Open:** none outstanding for this release. The previously-flagged stray untracked
  `.spark/git-native-mid-cycle-board/release.md` (flagged across at least five prior release
  reports as unaddressed) is now resolved — by a separate, unrelated commit (`9b98393`) that landed
  independently of this release cycle, not by any action taken here.
- **Binding ruling:** §3 Release Actions and the KEEP GATE below carry the final ruling.
- **On conflict:** the numbered body below wins for everything except `Status`/`Version`; log the
  mismatch as a finding at the next `/go-live` and proceed — don't stop on it.

## 0. Gate Check (done before anything else)

- **`review.md`** — header table + Handoff block both read `Status: passed`. **REVIEW GATE**
  (foot of file) fully checked: no open Blocker, no open Major (F1/F2 were the only two, both
  fixed and independently re-broken at re-review with fresh git fixtures and a 25-shape malformed-
  input sweep); every Must AC traces to implementing code; all plan deviations documented and
  accepted (T4's substituted DoD, T8 correctly deferred to `/demo-day`); test suite green
  (**749 passed, 0 failed**, as re-run by the reviewer); Status set to `passed`. Two rounds: the
  original pass found F1-F9 (2 Major, 5 Minor/Nit), fixed 2 itself and had the rest fixed in
  `/increment` fix-mode; the reviewer's own re-review then mutation-tested every fix by reverting it
  and re-running the suite, which surfaced 2 more gaps (F10, F11 — regression tests that didn't
  actually pin their fix) and closed both itself.
- **`qa.md`** — header table + Handoff block both read `Status: passed`. **QA GATE** (foot of
  file) fully checked: every Must-story AC verified live in the browser and passed (4 ACs —
  AC-1.3/AC-2.3/AC-2.4/AC-3.3 — are honestly marked N/A as not independently browser-verifiable
  against this repo's real, all-`Released` data, a disclosed limitation named in `spec.md`'s own
  A3, not a gate blocker); every browser-observable NFR verified and passed; no open Blocker or
  Major (one Major, B1, a 375px table-column-crush bug `plan.md`'s own R4 named as a risk in
  advance — fixed in `/increment` fix-mode and re-verified live, with fresh independent
  measurements, by a second QA pass); console clean; both agreed viewports (1280×800, 375×812)
  tested; Status set to `passed`.
- **Conclusion: both gates genuinely green.** Proceeding to fresh pre-flight below.

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — confirmed fresh, §0 above
- [x] `qa.md` status is `passed` — confirmed fresh, §0 above
- [x] Full test suite green on the release commit — re-run fresh, right now, on the **current**
  `HEAD` (`9b98393b73212be8c8b840f311594c72f7dac54c`, adjusted from the `cb8b6647` cited by the
  prepare-only pass — HEAD moved by one unrelated commit in the interim): `uv run pytest -q` →
  **750 passed, 0 failed**, in 443.32s (~7m23s). Matches the count both `review.md`'s re-run and
  the prepare-only pass's own re-run cite — re-run by me, now, a third independent time, on the
  post-drift HEAD.
- [x] Build succeeds from a clean state — `uv build` → `aspark_insights-0.12.0.tar.gz` and
  `aspark_insights-0.12.0-py3-none-any.whl` both built successfully, re-run fresh on the same
  post-drift `HEAD`.
- [x] No uncommitted changes in the working tree — confirmed **before** committing that the tree
  matched the exact shape described by the prepare-only pass's §1, with the one expected
  difference accounted for (`.spark/git-native-mid-cycle-board/release.md` no longer untracked,
  now committed separately in `9b98393`, unrelated to this release). This box closed for real once
  the release commit (§3) was made.

**Additional pre-flight verification performed (not copied from earlier reports):**
- Version re-derived myself, not trusted from `plan.md`'s T9 note: `pyproject.toml` → `0.12.0`,
  `src/aspark_insights/__init__.py` → `0.12.0`. Both consistent; `uv.lock`'s own entry updated in
  the same release commit.
- Confirmed `v0.12.0` was **not already tagged** before creating it: `git tag -l | sort -V` listed
  `v0.1.0` through `v0.11.0` only.
- Confirmed `HEAD` was `9b98393b73212be8c8b840f311594c72f7dac54c` (`docs: git-native-mid-cycle-board
  — record actual publish, status released`) immediately before the release commit — the one
  unrelated commit landed since the prepare-only pass, correctly not referenced in this release's
  own commit message or changelog.
- Confirmed the staged file set for the release commit matched §3's exact pending list, file by
  file (`git status --short` after `git add`) — no `git add -A`/`git add .` used.

## 2. Changelog

<!-- User-facing language. What can they do now that they couldn't before? -->

### Added
- A new `insights features` command shows one row per feature across its whole history — its own
  spec date, its five-artifact status, and the single release it actually delivered in — so you no
  longer have to open every release card a feature happens to touch and reconcile them by hand. A
  feature that spans several releases (the normal case, not the exception) now appears exactly
  once, with the one release it actually shipped in.
- Each feature now shows an honest "where does it currently stand" label — Spec, Increment,
  Review, QA, Released, or Unknown — always shown together with the real status it was worked out
  from (for example, "Increment — plan: approved, review: not started"), never as a colored
  health check or an "on track"/"behind" verdict.
- The HTML view of this new page adds a "pipeline" section that groups every feature by that
  current stage at a glance, so you can see what's in flight without reading every row of the
  table. A stage with nothing in it says so plainly, with the same visual weight as a populated
  one — never a blank space that looks broken.
- On small screens, the new feature table now scrolls sideways within its own boxed area instead
  of squeezing every column down to unreadable single letters — the whole page still never scrolls
  sideways on its own.

### Changed
- (none — this feature adds a new command; it changes no existing command's flags, output, or
  behavior)

### Fixed
- (none — the one bug found during this cycle's own testing, a mobile column-crushing display
  issue, was caught and fixed before this feature was ever released, so nothing previously shipped
  needed a fix)

## 3. Release Actions

<!-- What was actually executed, with results. -->

| Action | Result |
|---|---|
| Version bump & tag | Version bump already present in-tree and verified correct (`0.11.0` → `0.12.0` in `pyproject.toml`, `__init__.py`; `uv.lock` updated in the same commit). **Justification (semver, minor bump):** one new, purely additive, backward-compatible subcommand (`insights features`) — no existing CLI flag, subcommand behavior, or public API signature changes meaning. Matches this project's own precedent for every prior new-subcommand release (`v0.8.0`, `v0.9.0`, `v0.10.0`, `v0.11.0` — all minor bumps for additive features). **Executed:** release commit `4eb87f1cabb5bb7c44926c64cd9310f06860bbff` (`feat: feature-lens — insights features, feature-centric regrouping of the release board, v0.12.0`), staged file-by-file per the exact list below (never `git add -A`); annotated tag `v0.12.0` (`feature-lens v0.12.0`) created pointing at that commit. Both confirmed via `git rev-parse HEAD` and `git rev-parse v0.12.0^{commit}` — identical hashes. |
| PR / merge | N/A — direct mode (no `Delivery & Handoff` section in `.spark/constitution.md`; matches every prior release in this repo's history). |
| Deploy | N/A — no deploy target exists for this CLI/library project beyond the git remote itself (no hosted service, no package-registry publish declared). |
| Push (outward-facing) | Authorized explicitly by the user in-conversation. **Executed:** `git push origin main` and `git push origin v0.12.0`. Result recorded below (§ Push confirmation). |
| Post-release smoke check | Run against the pushed/tagged tree. Result recorded below (§ Smoke check). |

**Files staged for the release commit (exact list, no `git add -A`/`git add .`):**
```
README.md pyproject.toml src/aspark_insights/__init__.py src/aspark_insights/cli.py uv.lock
.spark/feature-lens/spec.md .spark/feature-lens/plan.md .spark/feature-lens/review.md .spark/feature-lens/qa.md
src/aspark_insights/gitboard/featurelens.py src/aspark_insights/gitboard/featurelens_report.py
tests/test_featurelens_cli.py tests/test_featurelens_closeout.py tests/test_featurelens_determinism.py
tests/test_featurelens_fixtures.py tests/test_featurelens_gate.py tests/test_featurelens_pipeline.py
tests/test_featurelens_render.py tests/test_featurelens_security.py
```
Deliberately **not** included: `.spark/git-native-mid-cycle-board/release.md` (already resolved by
an unrelated commit, `9b98393`, before this release began) and this release report itself
(`.spark/feature-lens/release.md`), committed separately, in this same pass, once its status was
known — per this project's established pattern.

**Push confirmation:**
- `git push origin main` — succeeded: `cb8b664..08522a6 main -> main`. Confirmed independently via
  `git ls-remote origin refs/heads/main` → `08522a6eca665eee9c9471c1d91b310714e37929`, matching local
  `HEAD`.
- `git push origin v0.12.0` — succeeded: `* [new tag] v0.12.0 -> v0.12.0`. Confirmed independently
  via `git ls-remote origin refs/tags/v0.12.0` (tag object `734b76d9...`) and
  `refs/tags/v0.12.0^{}` (dereferenced commit `4eb87f1cabb5bb7c44926c64cd9310f06860bbff`), matching
  the release commit exactly.

**Smoke check (run fresh, after the push above, against the pushed/tagged tree):**
- `insights features --as-of 2026-08-26 --format html --output <scratch>` → exit 0. Rendered page
  confirmed: `<!DOCTYPE html>` present; one `<table class="lens-table">` with 9 columns (`Feature`,
  spec date, `Spec`, `Plan`, `Review`, `QA`, `Release`, `Gate`, `Delivered In`); all 12 real
  `.spark/<feature>/` directories present as rows (`feature-lens`, `release-metrics`,
  `release-board-docs`, `release-board`, `release-board-html`, `git-native-mid-cycle-board`,
  `measurement-honesty`, `snapshot-report`, `mcp-server`, `public-repo-polish`,
  `traceability-metrics`, `foundation` — 12, not 11, because `feature-lens` now counts as one of its
  own subjects, correctly); `feature-lens`'s own row now reads `release: released`,
  `Gate: Released`, `Delivered In: v0.12.0`. Pipeline section: `Released` bucket populated with all
  12 features (including `feature-lens`); `Spec`, `Increment`, `Review`, `QA` buckets each show the
  honest `"no feature is currently at this stage."` empty-notice, with the same markup weight as the
  populated bucket — no blank space, no broken-looking gap.
- `insights features --as-of 2026-08-26 --format json --output <scratch>` → exit 0. Top-level shape
  `{"features": [...], "provenance": {...}, "reason": null}`; each feature object carries `name`,
  `spec_date`, `spec_date_reason`, `status` (per-artifact date/status/reason), `gate`,
  `gate_artifact`, `gate_evidence`, `delivered_in`, `delivered_in_reason` — matching `spec.md`'s
  AC-1.1 field shape. 12 feature objects returned, consistent with the HTML count above.
- Logs quiet: no warnings, tracebacks, or stderr output on either invocation.

## 4. Rollback Path

<!-- No release without this. -->

Before the push, the rollback path was purely local:
```
git tag -d v0.12.0
git reset --hard 9b98393b73212be8c8b840f311594c72f7dac54c
```

Once pushed, rolling back requires undoing published history, which this project treats as a
last-resort, explicitly-authorized action (never a default reflex):
```
# Remove the pushed tag from the remote (local tag deletion alone is not enough post-push):
git push origin :refs/tags/v0.12.0
git tag -d v0.12.0

# Revert (not reset --hard) the pushed commit on main, to avoid rewriting shared history:
git revert --no-edit 4eb87f1cabb5bb7c44926c64cd9310f06860bbff
git push origin main
```
`revert` is used instead of `reset --hard` + force-push once history is public, because rewriting
`origin/main` after a push risks breaking any clone/fork that has already fetched it. This mirrors
the rollback shape used by every prior released cycle in this repo. `9b98393b73212be8c8b840f311594c72f7dac54c`
is the exact pre-release commit confirmed as `HEAD` in §1 above — the base to which a purely local
(pre-push) rollback would reset.

## 5. Learnings (Keep!)

<!-- The K in SPARK: what does the team keep from this cycle? -->

- **What went well:**
  - The reviewer's re-review round is the strongest evidence yet in this project that "re-verify
    by execution, not by reading the fix" catches real residual defects at the *review* stage,
    before QA or release ever sees them: F10 and F11 were both regression tests that stayed green
    with their own fix reverted, caught only because the reviewer mutation-tested every one of the
    seven original fixes rather than trusting the fix-mode annotations. This is now at least the
    third feature in this project's history where a reviewer or tester found a test that asserted
    less than its name claimed (cf. `snapshot-report`'s F1, `release-board-docs`'s F7/F11) — a
    pattern, not a one-off.
  - `plan.md`'s own R4 named the 375px table-column-crush risk *in advance*, and QA's B1 finding
    confirmed exactly that risk had materialized — a clean example of a plan's disclosed risk
    section paying off by giving the tester a specific, falsifiable thing to go check, rather than
    a generic "test mobile" instruction.
  - QA's re-test of B1 took fresh independent measurements (`getBoundingClientRect`, `scrollWidth`/
    `clientWidth`) rather than trusting the developer's fix description, and specifically checked
    for a *new* failure mode the fix could have introduced (content hidden behind a broken/invisible
    scrollbar) — not just "is the crush gone."
  - This release cycle's own pre-flight caught and correctly handled real HEAD drift (an unrelated
    commit, `9b98393`, landing between the prepare-only pass and this execution pass) by
    re-verifying everything fresh on the new HEAD rather than trusting the prepare-only pass's
    cited commit — exactly the "trust nothing you didn't verify at release time" discipline this
    role exists to enforce.
- **What we'd do differently:**
  - Two of seven review findings (F10, F11) needed a second look specifically because a regression
    test's *name* implied more coverage than its actual fixture data could distinguish (F11's
    trailing occurrence carried the same tag the delivering one would have yielded, so the buggy
    and fixed code paths were indistinguishable). Worth a standing nudge for `/increment`: when a
    fix depends on *which* value wins among several candidates, the regression fixture must give
    each candidate a distinct, decoy value — not just a value that happens to differ from the
    correct one in the one case tested.
  - The stray untracked `.spark/git-native-mid-cycle-board/release.md`, flagged across at least
    three prior release reports (`release-board-docs`, `release-metrics`, `feature-lens`'s own
    prepare-only pass) with no remediation until now, was finally resolved — but by a separate,
    unrelated commit outside this release's own scope, not by direct action from a `/go-live` pass
    addressing the flag. Confirms this project's own CLAUDE.md precedent: a repeated note in a
    release report doesn't self-enforce; it took a human decision outside the report loop to close
    it.
- **Patterns worth reusing:**
  - Mutation-testing every fix at re-review (revert, re-run, confirm red) rather than reading the
    patch — already a CLAUDE.md-level precedent from `snapshot-report`; this cycle is a second,
    independent confirmation of its value and a candidate for making it a checklist item in
    `/peer-review` itself, not just a norm.
  - Disclosing a real data-coverage gap explicitly (this repo's real data can prove only 2 of 6
    gate values) rather than silently substituting a fixture's result for a real-data claim — `qa.md`
    named exactly which ACs (AC-1.3/AC-2.3/AC-2.4/AC-3.3) are N/A-not-blocking for this reason,
    which is what let the QA gate pass honestly instead of either forcing a fixture that doesn't
    exist or silently skipping the ACs.
  - Explicitly re-deriving the exact pre-release `HEAD` at execution time, rather than trusting a
    prepare-only pass's cited commit, is now demonstrated to matter in practice (not just in
    principle) — a candidate for a standing `/go-live` checklist line whenever there is a gap in
    time between a prepare-only pass and its authorized execution.

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

- [x] All pre-flight checks passed at release time — re-verified fresh on the post-drift `HEAD`
  (`9b98393`), all five clean: gates, tests (750 passed), build, and (after the release commit)
  clean working tree
- [x] Changelog written in user-facing language — §2, sourced from `spec.md`'s stories and the
  README's own "Feature lens" section, no commit hashes or ticket IDs
- [x] Release actions executed and verified (or `aborted` with reason) — release commit
  `4eb87f1cabb5bb7c44926c64cd9310f06860bbff`, annotated tag `v0.12.0`, `git push origin main`
  (`cb8b664..08522a6`), and `git push origin v0.12.0` (new tag) all executed and independently
  confirmed against the remote via `git ls-remote`; post-release smoke check run and passed (§3)
- [x] Learnings recorded — §5
- [x] Status set to `released`, or `handed-off` in declared `pr` mode — direct mode (no `Delivery &
  Handoff` section declared in `.spark/constitution.md`), terminal status `released`, confirmed live
  on `origin/main` and `origin/v0.12.0` and verified working by the smoke check above
