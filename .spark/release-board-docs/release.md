# Release: release-board-docs

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `released` |
| **Version** | v0.10.0 (released — pushed to `origin/main`, tag `v0.10.0` pushed) |
| **Date** | 2026-08-23 |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report updates it in the same edit that changes status or actions:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `released`. The user gave explicit publish authorization in this conversation
  ("yes"); the orchestrator executed the push directly (holding that first-hand authorization
  plus direct tool access), the same division of labor established as correct across every
  prior `release-board*` cycle.
- **Summary:** Release board's HTML view now orders newest-first and lets the maintainer read
  any feature's actual spec/plan/review/qa/release document content in place, structured via a
  new bounded Markdown renderer — plus a mid-cycle symlink-escape security fix and a mobile
  CSS wrap fix. Shipped as v0.10.0 (minor, additive, backward-compatible). Release commit
  `6201553` + docs commit `c72259a` + annotated tag `v0.10.0` pushed to `origin`
  (`385c1ea..c72259a` on `main`). **Post-release smoke check run and green** (§3): a fresh
  `git clone` of `origin` at the pushed tag, `uv sync`, confirms `aspark_insights.__version__ ==
  "0.10.0"`, `insights releases --format html` produces a valid page (doctype, inline logo,
  "newest first" lead sentence, 50 `<details class="doc-content">` blocks), and
  `--format json` still exits 0 with `v0.1.0` first (order genuinely untouched).
- **Open:** none for this feature. Unrelated: the pre-existing untracked
  `.spark/git-native-mid-cycle-board/release.md` remains untouched, flagged again in §4 as a
  cleanup item now spanning three release cycles unaddressed.
- **Binding ruling:** §3 Release Actions and the KEEP GATE below carry the final ruling.
- **On conflict:** the numbered body below wins for everything except `Status`/`Version`; log
  the mismatch as a finding at the next `/go-live` and proceed — don't stop on it.

## 1. Pre-Flight Checks

<!-- Verified immediately before releasing — not copied from earlier reports. -->

- [x] `review.md` status is `passed` — round 2 (adversarial re-review), 18 fixed / 1 open Nit
  (F19, non-blocking, explicitly recorded as such in the REVIEW GATE), REVIEW GATE fully checked
- [x] `qa.md` status is `passed` — round 2 (independent re-verification of B1's fix), 0 open,
  QA GATE fully checked
- [x] Full test suite green on the release commit — re-ran fresh, right before committing, on
  this exact tree content: `uv run python -m pytest -q` → **586 passed**, 0 failed (matches the
  count both `review.md` and `qa.md` independently claim; not copied from either report). The
  commit itself changed no tracked file content beyond moving these exact files into history
  (`git diff --stat HEAD` on the resulting commit is empty), so this result stands for `6201553`
  unchanged.
- [x] Build succeeds from a clean checkout — `uv build` → `aspark_insights-0.10.0.tar.gz` and
  `aspark_insights-0.10.0-py3-none-any.whl` both built successfully to a scratch output dir
- [x] No uncommitted changes in the working tree — after the release commit, `git status
  --short` shows only two untracked files: this report (`.spark/release-board-docs/release.md`,
  written and committed separately per §3) and `.spark/git-native-mid-cycle-board/release.md`.
  The latter is a stale, never-committed leftover from an already-released prior feature
  (`git-native-mid-cycle-board`, shipped in `v0.7.0`), flagged separately as its own background
  cleanup task and explicitly out of scope here — left untracked and untouched, deliberately
  excluded from every `git add` this pass.

**Additional pre-flight verification performed (not copied from earlier reports):**
- Re-derived the version bump myself: confirmed `pyproject.toml`, `src/aspark_insights/__init__.py`
  and `uv.lock`'s own `aspark-insights` entry all already read `0.10.0` (from `0.9.0`), consistent
  across all three files, before committing.
- Re-verified `--format json`'s byte-for-byte order claim directly: ran `insights releases --as-of
  2026-08-23 --format json` on the feature working tree, then `git stash`-ed to the pre-feature
  tree and ran the identical command again. The only difference between the two outputs is the
  `insights_version` field (`0.10.0` vs `0.9.0`, expected) — release order and every other field
  are identical. Working tree was restored via `git stash pop` immediately after (verified via
  `git status --short` matching the pre-stash state exactly, before proceeding to commit).
- Read `--help` and `insights releases --help` live: both name the document read and scope it to
  `--format html`, matching `review.md`'s F9 finding and `NFR-1`.
- Read the full `git diff` for `README.md` and `src/aspark_insights/cli.py` myself, not just the
  reports' summary of them — confirms the stated behavior (help text, README wording, the
  `documents = collect_release_documents(...)` wiring gated to the html branch only).

## 2. Changelog

<!-- User-facing language. What can they do now that they couldn't before? -->

### Added
- The release board's HTML page now lets you open any feature's actual spec, plan, review, QA,
  or release document and read its real written content — headings, tables, checklists — right
  there on the page, instead of needing a separate trip to an editor or GitHub. A feature that
  shipped as part of more than one release shows its documents once, with a link at every other
  release that takes you straight to them.
- If a document is missing, unreadable, or empty, the page now says so plainly instead of showing
  a blank or broken section. A very large document is shown up to a generous limit with a clear
  note about how much was left out — nothing is silently cut off without telling you.

### Changed
- The release board's index and per-release list now show your most recent work first (today's
  open in-progress window at the top, your very first release at the bottom) — matching how any
  changelog or "Releases" page you're used to already reads, instead of oldest-first.
- Document content on the page (headings, tables, checked/unchecked items) now renders as real,
  legible formatting rather than showing raw `#`/`|`/`[ ]` markup symbols.

### Fixed
- Closed a security gap where a document file that had been symlinked to point outside the
  project could have had its contents leaked onto the generated page; such a document now shows
  a clear "outside the project" notice instead.
- Fixed a mobile display bug where long inline code references inside a document's text could
  push the whole page sideways, forcing unwanted horizontal scrolling on a phone-sized screen.

## 3. Release Actions

<!-- What was actually executed, with results. -->

| Action | Result |
|---|---|
| Version bump & tag | Version bump already present in-tree and verified correct before committing (`0.9.0` → `0.10.0` in `pyproject.toml`, `__init__.py`, and `uv.lock`'s own entry). **Justification (semver, minor bump):** three additive, backward-compatible behavior changes (index reorder, new document-viewing capability, structured Markdown rendering) plus a security fix and a CSS wrap fix bundled into the same release — no breaking change to any existing CLI flag, subcommand behavior (`--format json` stdout proven byte-identical in order), or public API signature. Release commit `6201553` + docs commit `c72259a`; annotated tag `v0.10.0` on `6201553`. **Pushed** to `origin` (`git push origin main` moved `origin/main` `385c1ea..c72259a`; `git push origin v0.10.0` published the tag). |
| PR / merge | N/A — direct mode (no `Delivery & Handoff` section in `.spark/constitution.md`; matches both prior `release-board*` cycles, which also released direct-to-`main`). |
| Deploy | This project's "deploy" is the git push itself (no PyPI target). **Done** — see above. |
| Post-release smoke check | **Run, green.** Fresh `git clone` of `origin` at the pushed tag `v0.10.0`, `uv sync` succeeded, `uv run python -c "import aspark_insights; print(aspark_insights.__version__)"` → `0.10.0`. `uv run insights releases --as-of 2026-08-24 --format html` produced a 1,420,633-byte valid page: doctype present, inline logo present, lead sentence reads "newest first," 50 `<details class="doc-content">` blocks (document-viewing capability live). `uv run insights releases --as-of 2026-08-24 --format json` exits 0, 11 releases (grew by one — this release's own tag now counts), first entry `v0.1.0` confirming the underlying list order is still oldest-first/untouched by the HTML reorder. Temporary clone removed after verification. |

**Commands executed, on the user's explicit go ("yes"):**
```bash
git push origin main
# 385c1ea..c72259a  main -> main

git push origin v0.10.0
# * [new tag]         v0.10.0 -> v0.10.0
```
Both ran successfully; no errors, no force flags, no history rewrite.

## 4. Learnings (Keep!)

<!-- The K in SPARK: what does the team keep from this cycle? -->

- **What went well:**
  - The review's own re-review round (F16–F19) is the strongest evidence yet in this project that
    "re-verify by execution, not by reading the fix" catches real residual defects: F8's fix was
    incomplete for a truthy non-list `releases` value, a NUL byte, and an over-length name; F11's
    and F7's fixes shipped with zero regression tests and both survived the full suite when
    reverted. All three were caught only because the reviewer refused to take the fix-mode
    annotation's word for it — the exact discipline CLAUDE.md's "snapshot-report" nudge already
    named, now proven again in a second feature.
  - QA's B1 re-verification went well beyond "the one repro from the bug report": it expanded all
    45 documents simultaneously at 375px and checked all 4,462 inline `<code>` spans, not just the
    single span named in the original finding — confirming the fix was the systemic CSS rule it
    claimed to be, not a one-off patch. This is the adversarial-reproduction bar in action for a
    UI bug, not just a security one.
  - Version-sync discipline (`pyproject.toml` + `__init__.py` + `uv.lock`'s own entry, all three
    kept in lockstep) held cleanly again, exactly as the prior `release-board-html` cycle
    established — worth keeping as a standing release checklist item.
- **What we'd do differently:**
  - F19 (the `allowed_root` containment control defaulting to opt-in rather than required) was
    correctly left open as a non-blocking Nit, but it is a real design trap for the next caller of
    `read_artifact_document`. Worth surfacing this explicitly to `/sprint-plan` for the next
    feature that touches `artifactcontent.py`, rather than letting it sit silently until a second
    caller reopens the hole it guards against.
  - The stray, never-committed `.spark/git-native-mid-cycle-board/release.md` file has now sat
    untracked in the working tree across at least this release cycle too (it predates this
    feature and is already flagged elsewhere as its own cleanup task). This is exactly the kind
    of repeated-flag-with-no-remediation pattern this project's own CLAUDE.md already calls out
    for git identity ("a repeated note in a release report doesn't self-enforce"). Recommend
    actually resolving it (commit it, or delete it if its content is truly stale/incorrect)
    before it survives a third release cycle unaddressed.
- **Patterns worth reusing:**
  - Re-running `--format json` before *and* after `git stash`-ing the feature diff, on the exact
    same `--as-of` date, is a cheap, high-confidence way for a release manager to independently
    verify an "unchanged sibling output" claim (like AC-1.3 here) without having to trust the
    review/QA report's account of it — worth keeping as a standard `/go-live` pre-flight technique
    for any feature that claims "format X is untouched" alongside a change to format Y.
  - Candidate for this project's `CLAUDE.md`: explicitly document the "exclude unrelated stray
    working-tree files from the release commit by naming them, not by `git add -A`" discipline
    used in this pass — staging files by exact name (never a broad `git add -A`/`.`) is what made
    it safe to leave `git-native-mid-cycle-board/release.md` untouched while still catching every
    real feature file, including the two brand-new modules and their tests.
  - This project's own established two-commit release pattern (a code/docs release commit first,
    then a separate `docs: record release report` commit added after local tag creation — see
    `a5f43be`) was followed again here, since this release.md necessarily describes the very
    commit and tag it reports on and can't be authored before they exist. Worth keeping as the
    default `/go-live` mechanic rather than trying to fold the report into the release commit.

---

## ✅ KEEP GATE

*All boxes checked → the loop is closed. The feature is done-done.*

- [x] All pre-flight checks passed at release time — re-run fresh on this exact commit, not
  copied from `review.md`/`qa.md` (586 passed, clean build, version consistent, JSON order
  independently re-verified unchanged)
- [x] Changelog written in user-facing language — §2, no commit hashes/ticket IDs/internal jargon
- [x] Release actions executed and verified — push to `origin main`, tag `v0.10.0` pushed,
  post-release smoke check run green from a fresh clone at the pushed tag (§3)
- [x] Learnings recorded — §4
- [x] Status set to `released` — the user gave explicit publish authorization in this
  conversation ("yes"); all outward-facing actions completed and verified

**Rollback path:**
This feature is entirely additive/confined to the `releases --format html` code path plus two new
modules (`gitboard/artifactcontent.py`, `gitboard/markdownlite.py`); `--format json` is untouched
(independently re-verified in §1). It writes only one output file at render time
(`release-board.html`, same as `v0.9.0`) and reads existing `.spark/` files — no data migration,
no schema change, no persisted state beyond that one rendered file.

**Current, live state: pushed and released.** `main` and tag `v0.10.0` are both public on
`origin`. If a problem surfaces: `git revert 6201553` on `main` (never a force-push/history-
rewrite) restores `0.9.0`'s behavior forward; delete and re-push the tag pointer only if genuinely
necessary. Because the feature only ever writes one regenerated `release-board.html` file, there
is no "stale data left behind" case: the very next render (pre- or post-revert) fully regenerates
that one file from source, with no migration or backfill step required either direction.
