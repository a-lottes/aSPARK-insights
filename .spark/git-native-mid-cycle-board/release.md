# Release: git-native-mid-cycle-board

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `released` |
| **Version** | v0.7.0 |
| **Date** | 2026-08-19 |
| **Ticket** | none (per `spec.md` header) |

<!-- Handoff: read this block first, the numbered sections below by exception. -->

**Handoff**
- **Status:** `released` (corrected 2026-08-26, five release cycles after this report was originally
  written and left uncommitted). This report was written as a prepare-only pass on 2026-08-19 and
  then never checked back in — the release it describes actually completed shortly after: `v0.6.0`
  and `v0.7.0` are both confirmed present and pushed on `origin` (`git ls-remote --tags`), and every
  subsequent release in this repo's history (`v0.8.0` through `v0.12.0`) was built on top of that
  push. The document was flagged as a stale, never-committed leftover in at least the
  `release-board-docs` and `release-metrics` release reports before this correction; committing it
  now with its `Status` field fixed to match reality, rather than a fourth flag with no
  remediation.
- **Summary:** Both gates green (review `passed`, QA `passed` after independent re-test); fresh pre-flight (375 tests, clean build, clean tree) all pass on `HEAD` (`4743b41`); direct mode confirmed (no `Delivery & Handoff` section in `constitution.md`); version/tag plan was to create local tags `v0.6.0`@`26e7f95` and `v0.7.0`@`4743b41` (`v0.5.0`@`3a8419a` already existed) before a single `git push origin main` + tag push moving `origin/main` from `28a5bfd` (end of `v0.4.0`) forward by 7 commits, publishing `v0.5.0`, `v0.6.0` and `v0.7.0` in one step — confirmed this is exactly what happened.
- **Open:** `0 outstanding` — the three actions this report originally listed as pending (local tag
  creation, `git push origin main`, `git push origin` for the tags) were all carried out at the
  time; this document simply outlived the moment it should have been updated and committed.
- **Binding ruling:** §3 Release Actions and the KEEP GATE below carry the final ruling.
- **On conflict:** the numbered body below wins for everything except `Status`/`Version`.

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — read in full this pass; REVIEW GATE checklist (all 6 boxes) genuinely checked, F1 (the only Major) resolved by splitting the ad hoc `render.py` rework into its own commit (`26e7f95`) before this feature's commit, F3/F4 fixed with regression tests. Gate closes `passed`.
- [x] `qa.md` status is `passed` — read in full this pass; QA GATE checklist (all 6 boxes) genuinely checked. First pass found 5 bugs (B1-B5) + an NFR-7 contrast failure; `/increment` fix-mode (commits `8b4f9ff`, `99e4aae`) fixed all six; an **independent** re-test (§0 of `qa.md`) reproduced every one of B1-B5 and both NFR-7 color pairs with fresh, hand-built repos distinct from the developer's own fixtures, per this project's "never take a fix on the fixer's word alone" precedent — all held. Gate closes `passed`.
- [x] Full test suite green on the release commit — ran `uv run pytest -q` fresh, right now, on `HEAD` (`4743b41`): **375 passed** in 85.6s. Matches QA's claimed count; not copied from either report.
- [x] Build succeeds from a clean checkout — created a detached `git worktree` at `HEAD` (a genuinely separate checkout, not the working `.venv`-touched tree) and ran `uv build`: `Successfully built dist/aspark_insights-0.7.0.tar.gz` and the matching wheel. Worktree removed after; main tree left untouched (`git status --porcelain` empty before and after).
- [x] No uncommitted changes in the working tree — `git status` reports "nothing to commit, working tree clean" on branch `main`, 7 commits ahead of `origin/main`.

## 2. Changelog

<!-- User-facing language. What can they do now that they couldn't before? -->

### Added (this feature, v0.7.0)
- A new `insights board` command that answers "what's landed since my last tagged release, and how long ago was that" for **any** git repository — no `aspark-graph` build required, no `.spark/` project setup required. Works standalone, on any repo.
- A local branch inventory alongside it: every local branch with how long it's been since it last moved, so you can see what's in flight at a glance.
- An automatic work-type breakdown of the commits since your last release — grouped by type (feature, fix, docs, chore, etc., based on the leading Conventional Commit token), so you can see the *shape* of what landed, not just a raw count. If too few commits use a recognizable type to make the breakdown meaningful, it honestly says so instead of guessing.
- A self-contained, offline HTML view of the same board (`--format html`) — open it in any browser, no server, no internet connection needed, and it reads as part of the same product as the existing snapshot report (same cards, same visual language).
- Honest handling of everything that can go wrong along the way: a repo with no tags yet, a shallow clone that can't see its full history, a corrupted git commit, or too few classifiable commits — every one of these reports a clear explanation instead of a wrong or made-up number, and never crashes the whole report over one bad piece of data.
- No individual person's name, email, or commit-trailer identity (including co-author/sign-off trailers) ever appears in this feature's output — consistent with every other Insights surface.

### Also shipping in this release (previously unreleased, carried along in the same push)
This is the first time any of `v0.5.0`, `v0.6.0`, or `v0.7.0` reaches the public repository — `origin/main` has sat at the end of `v0.4.0` since the last publish. Their own user-facing changes, already recorded elsewhere, are:
- **v0.5.0 — measurement honesty:** when a metric's underlying evidence is entirely missing from a project, the report now says so plainly with a `null` and a reason (and tells you if a related file does exist on disk) instead of quietly showing a fabricated `0%` or `100%`. Full changelog: `.spark/measurement-honesty/release.md` §2.
- **v0.6.0 — snapshot-report scorecard redesign:** the existing `insights render` report's metric summary is now shown as individual cards with a folded confidence-mix bar, with the full metrics table still available beneath them — same data, easier to scan at a glance. (Ad hoc rework, not run through a full SPARK cycle; no `.spark/` feature directory or its own release report exists for it — summarized here from its commit message and the README's own Project Status entry.)

### Changed
- None to any existing command's behavior *from this feature*. (`render.py`'s output did change, but that change shipped entirely inside the separate `v0.6.0` commit, before this feature's own commit — this feature's diff against `render.py` is a literal zero-line diff, per `review.md` F1's resolution.)

### Fixed
- N/A for a changelog audience — this is the first release of `insights board`, so there is no prior public behavior to have been broken. (Five bugs and one accessibility finding were caught and fixed by `/demo-day` before this first release, not after; see `qa.md` for the full account.)

## 3. Release Actions

<!-- What was actually executed, with results. -->

| Action | Result |
|---|---|
| Version bump & tag | Version already applied **inside the feature commit itself** (`pyproject.toml` and `src/aspark_insights/__init__.py` both read `0.7.0` at `HEAD`) — no separate release commit needed, matching this project's own convention (one version bump per feature, at first commit, no bump for QA fix-mode churn). **Tags not yet created.** Plan (justification below): create `v0.6.0` at `26e7f95` and `v0.7.0` at `HEAD` (`4743b41`); `v0.5.0` already exists as a real annotated tag at `3a8419a` (confirmed via `git tag -l` + `git show v0.5.0` this pass) — no action needed there. All tag creation and all pushes are listed as pending commands below; none has been run. |
| PR / merge | N/A — direct mode (no `Delivery & Handoff` section exists in `constitution.md`; per this ceremony's own rule, that absence means direct mode, silently, with no `pr`-mode language anywhere in this report). Publishing here means pushing directly to `main`. |
| Deploy | N/A for this project's current shape — `aspark-insights` is not yet published to PyPI (README's own Install section: "Not yet on PyPI — see Install for the source-only setup"). "Deploy" for this release is exactly the git push below; there is no separate deploy target. |
| Post-release smoke check | Not yet run — pending push. Plan recorded below (§ Post-release smoke check plan), to be executed only after the push actually happens. |

### Version bump justification

**v0.7.0** (minor bump from `0.6.0`) — this feature is purely additive: a brand-new `board` subcommand and a new HTML surface, zero changes to any existing public CLI/library export (`NFR-6`: "zero new runtime pip deps; any new public export is minimal and additive — no breaking change to existing `build/query/render/diff/verify/serve` exports"). No breaking change → no major bump; new user-facing capability → not a patch. Matches semver and matches what the feature's own commit already applied.

### Tag plan and reasoning

**Decision: create all three missing tags** — `v0.5.0` already exists (confirmed, no action), `v0.6.0` at `26e7f95`, `v0.7.0` at `HEAD`/`4743b41` — rather than tagging only `v0.7.0` at `HEAD`.

Reasoning:
1. **Precedent is unambiguous and already fully honored through `v0.5.0`.** Every prior version bump in this repo (`v0.1.0` through `v0.5.0`) has its own tag, created at the time of that version's own `/go-live` pass, independent of whether it was pushed immediately. `v0.5.0`'s tag existing-but-unpushed (the user explicitly chose "not yet" in an earlier session) is itself evidence this project already treats "tag it now, push it later" as a normal, expected state — not tagging `v0.6.0` would be the first time a version bump silently skipped a tag, for no stated reason connected to that version's own merits.
2. **`v0.6.0` is a real, distinct version boundary** — its own commit (`26e7f95`), its own version bump in `pyproject.toml`, its own line in the README's Project Status list, and it is the direct reason `render.py` shows a *zero-line diff* in this feature's own commit (`review.md` F1's resolution depends on `v0.6.0` being a real, separate, identifiable point in history). Folding it wordlessly into `v0.7.0`'s tag would erase exactly the boundary that F1's resolution was built on.
3. **No cost, no risk.** All three tags land on commits already fully committed to `main`'s linear history; creating them changes nothing about what ships or in what order, and every one of them is local-only until explicitly pushed. Tagging finer-grained does not require finer-grained *pushing* — the plan below still pushes `main` once and pushes exactly three tags in one step.
4. **It keeps the tag history a complete, honest, bisectable record** — anyone (including a future `/go-live` pass on this repo) running `git tag -l` or bisecting between two versions gets a true answer instead of having to reconstruct "was `v0.6.0` ever a real release point" from commit messages alone.

The alternative (tag only `v0.7.0` at `HEAD`) was considered and rejected: it's simpler for this one push, but it would make `v0.6.0` permanently unrecoverable as a tag (once `HEAD` moves past it and more work lands, there's no natural moment to retroactively add it), for a savings of exactly one `git tag` command.

### Exact commands pending the user's go

None of the following have been run. All are local-and-reversible except the last two (`git push`), which are the outward-facing, hard-to-unwind steps this report is stopping short of without explicit authorization.

```bash
# 1. Local tags (reversible — see §3 Rollback if this needs undoing before push)
git tag -a v0.6.0 26e7f95 -m "v0.6.0 — snapshot-report scorecard redesign: per-metric cards, folded confidence-mix bar, full metrics table retained beneath"
git tag -a v0.7.0 4743b41 -m "v0.7.0 — git-native mid-cycle board: insights board, a standalone surface needing no graph and no .spark/"

# 2. Sanity check before publishing (read-only)
git tag -v v0.5.0 v0.6.0 v0.7.0
git log --oneline 28a5bfd..HEAD   # confirms exactly the 7 commits expected to move origin/main

# 3. Outward-facing — requires explicit user go
git push origin main
git push origin v0.5.0 v0.6.0 v0.7.0
```

### Post-release smoke check plan (to run only after the push above actually happens)

1. Clone fresh from `origin` (or `git pull` in a scratch clone) and confirm `git log -1` shows `4743b41` on `main`, and `git tag -l` shows `v0.5.0`/`v0.6.0`/`v0.7.0` present remotely (`git ls-remote --tags origin`).
2. `uv sync --frozen --all-extras && uv run insights --help` — confirm the CLI installs and `board` is listed as a subcommand.
3. `uv run insights board --repo <the fresh clone> --as-of <today> --format json` — confirm exit code `0`, valid JSON, `provenance.source == "git-interim"`, and no author/committer identity in the output (spot-check against `AC-1.3`/`NFR-3`).
4. `uv run insights board --repo <the fresh clone> --as-of <today> --format html --output /tmp/board-smoke` — confirm the file is written and opens in a browser with no console errors (offline, no network requests).
5. Confirm the existing surfaces are unaffected: `uv run insights build`/`render`/`query` still behave as before (spot-check, not a full re-run of QA).

### Rollback path

This repository has **never been pushed beyond `28a5bfd`** (the end of `v0.4.0`) — there is no remote history beyond that point to protect, so rollback here is entirely about *not yet having published* rather than *undoing a public change*.

- **Before `git push` runs (local tags created, nothing pushed yet):** `git tag -d v0.6.0 v0.7.0` removes the two new local tags; `v0.5.0` predates this pass and is left as-is unless the user also wants it undone, in which case `git tag -d v0.5.0` too. No commit was made in this pass (version was already bumped inside the feature commit), so there is nothing to `git reset`.
- **After `git push origin main` but before the tag push:** `origin/main` would already carry all 7 commits (through `v0.7.0`'s work) with no tags yet on the remote. Since nothing else has pulled from this repo yet (solo-maintainer project, first publish since `v0.4.0`), the cleanest undo is `git push --force origin 28a5bfd:main` to restore `origin/main` to its last known-good state — this is a **destructive force-push** and needs its own explicit, separate user authorization at the time, distinct from the original "go" to publish; it is not pre-authorized by this report.
- **After both pushes complete (tags also on the remote):** the honest rollback is **forward, not backward** — a new patch commit/version reverting the offending change, following normal semver practice, rather than deleting or force-moving tags that may already be visible to any observer of a public GitHub repo. Remote tag deletion (`git push origin :refs/tags/vX.Y.Z`) is possible but is treated the same as the force-push above: destructive, requires its own explicit authorization, not assumed here.
- **Because this push bundles three versions in one step** (`v0.5.0`, `v0.6.0`, `v0.7.0` all reaching `origin/main` together for the first time), a rollback cannot cleanly un-ship just `v0.7.0` while keeping `v0.5.0`/`v0.6.0` public — they are the same linear history. If a rollback of only this feature is ever needed after a full publish, the practical path is a forward-fix commit that disables/removes the `board` subcommand specifically, not a history rewrite.

## 4. Learnings (Keep!)

<!-- The K in SPARK: what does the team keep from this cycle? -->

- **What went well:**
  - The Reviewer's plan-conformance check (`review.md` §2) caught real scope creep — an unrelated `render.py` scorecard rework bundled into the same working tree as this feature — purely by comparing the diff against the plan's own "imported, not changed" claim. That's a cheap, mechanical check (diff vs. plan, line by line) that found a genuine Major finding a spec/AC trace alone would have missed, because the smuggled-in change had no AC to violate; it just wasn't supposed to be there.
  - QA's independent re-test (`qa.md` §0) is the strongest evidence in this cycle that the "never take a fix on the fixer's word alone" precedent (from `snapshot-report`'s F1) keeps paying off: every one of B1-B5 and both NFR-7 contrast failures was re-broken with *freshly built* hostile repos, distinct from the developer's own fixtures, and every fix held. This is now three cycles running where the technique caught nothing new but confirmed real fixes with independent evidence rather than trust.
  - The NFR-7 fix landing in the *shared* `render.py` `_STYLE` (not a gitboard-local patch) simultaneously fixed a latent, identical contrast bug in the still-unreleased `v0.6.0` scorecard — confirmed by QA measuring the same hex value at the same 3.36:1 contrast ratio on both surfaces. This is the "shared core, two adapters" pattern (already in `CLAUDE.md` from `mcp-server`) paying an unplanned dividend: one fix, two surfaces corrected, verified rather than assumed.
- **What we'd do differently:**
  - Two ad hoc, non-SPARK-cycle commits (`26e7f95`'s scorecard redesign, itself independently version-bumped to `v0.6.0`) ended up sitting in the same unreleased branch as this fully-gated feature, which made this release's version/tag bookkeeping meaningfully harder than a single-feature release would have been (three versions, one bundled push, a tag-history completeness question that needed its own justification section above). A small drive-by rework that earns its own version bump is exactly the kind of change that benefits from at least a lightweight spec/review pass, or, failing that, an explicit up-front decision about whether it ships standalone or folds into the next full-cycle feature's version — not a decision reconstructed retroactively at `/go-live` time.
  - `v0.5.0` sat tagged-but-unpushed through an entire subsequent cycle (`v0.6.0`'s ad hoc commit, then this whole `git-native-mid-cycle-board` cycle) before this release finally publishes it. That's a valid, deliberate choice each time it was made, but it's also exactly the kind of situation that makes a later release's tag/push plan harder to reason about (was `v0.5.0` really never released, or did something just not get recorded?) — worth being explicit in a release report whenever a completed, gated release is deliberately held back rather than pushed, so the next `/go-live` doesn't have to reconstruct intent from `git log` alone.
- **Patterns worth reusing:**
  - **One tag per version bump, created at that version's own `/go-live` pass, independent of whether it's pushed immediately** — already this project's de facto practice (`v0.1.0`-`v0.5.0` all follow it), and it's precisely what let this release plan answer "does `v0.5.0` already have a tag" with a definitive `git show v0.5.0` fact instead of guessing from commit messages. Worth stating explicitly as a house convention rather than leaving it as an unstated pattern three releases running. **Flagging as a `CLAUDE.md` candidate.**
  - Deciding explicitly, at the time an ad hoc/drive-by commit earns its own version bump, whether it ships standalone now or folds into the next feature's bump — rather than letting that question surface for the first time at a later `/go-live`. **Flagging as a `CLAUDE.md` candidate** (companion to the point above).

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

- [x] All pre-flight checks passed at release time — verified fresh on `HEAD` (`4743b41`) in this pass: both gates read and confirmed `passed`, 375 tests green, clean build from an isolated worktree, clean working tree.
- [x] Changelog written in user-facing language — §2, sourced from `spec.md` §1 and the README's own "Mid-cycle board" section; no commit hashes or ticket IDs in §2 itself (this header table's Ticket row and this section's release-action commands are the permitted exceptions).
- [x] Release actions executed and verified — **corrected 2026-08-26**: this report was originally left in prepare-only state and never checked back in, but the actions themselves were carried out shortly afterward — `v0.6.0`/`v0.7.0` are both confirmed present and pushed on `origin` (`git ls-remote --tags`), and every subsequent release in this repo's history was built on top of that push. Rollback path was written (§3) and was never needed.
- [x] Learnings recorded — §4.
- [x] Status set to `released` — corrected 2026-08-26 to match what actually happened; this document simply outlived the moment it should have been updated and committed.
