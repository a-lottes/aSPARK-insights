# Release: release-board-docs

| | |
|---|---|
| **Phase** | Keep |
| **Owner** | Release Manager (`/go-live`) |
| **Input** | `review.md` (`passed`), `qa.md` (`passed`) |
| **Status** | `preparing` |
| **Version** | v0.10.0 (release commit + local tag created — see §3; not yet pushed) |
| **Date** | 2026-08-23 |

<!-- Handoff: read this block first, the numbered sections below by exception. Whoever
     writes to this report updates it in the same edit that changes status or actions:
     overwrite in place, never append. The block holds one current state, never a
     per-round log; a stale block is a defect, not a cosmetic issue. -->

**Handoff**
- **Status:** `preparing` — release commit made (`6201553`), local annotated tag `v0.10.0`
  created and verified (`git tag -v` resolves, tagger `Andreas Lottes <andreas@lottes.dev>`,
  target `6201553`, no GPG signature — matches this repo's existing tag norm on every prior tag,
  not a new gap). **Push deliberately not executed.** Both gates are green (`review.md`
  `passed`, `qa.md` `passed`) and fresh pre-flight (586 tests, clean build, byte-identical JSON
  order) passed on this exact commit. Direct mode (no `Delivery & Handoff` section in
  `.spark/constitution.md`), matching both prior `release-board*` cycles.
- **Summary:** Release board's HTML view now orders newest-first and lets the maintainer read
  any feature's actual spec/plan/review/qa/release document content in place, structured via a
  new bounded Markdown renderer — plus a mid-cycle symlink-escape security fix and a mobile
  CSS wrap fix. Shipped as v0.10.0 (minor, additive, backward-compatible). Local commit and tag
  prepared; push held for the user's explicit go, per this role's mandate that outward-facing
  actions require authorization relayed by the caller, not inferred from a task instruction to
  "prepare."
- **Open:** `1 outstanding` — the user's explicit go to run the four pending publish commands
  in §3 (`git push origin main`, `git push origin v0.10.0`, plus the post-push smoke check).
  Nothing else is outstanding; there is no `handed-off` mode here (direct mode).
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
| Version bump & tag | Version bump already present in-tree and verified correct before committing (`0.9.0` → `0.10.0` in `pyproject.toml`, `__init__.py`, and `uv.lock`'s own entry). **Justification (semver, minor bump):** three additive, backward-compatible behavior changes (index reorder, new document-viewing capability, structured Markdown rendering) plus a security fix and a CSS wrap fix bundled into the same release — no breaking change to any existing CLI flag, subcommand behavior (`--format json` stdout proven byte-identical in order), or public API signature; `library`-lens NFR-3 explicitly requires additive-only exports, which held. Per this project's own precedent (`public-repo-polish` shipped with *no* bump because it changed no behavior; both prior `release-board` cycles bumped minor for the same class of additive change), a minor bump is correct here too. **Executed this pass:** release commit `6201553` created (all feature files, `.spark/git-native-mid-cycle-board/release.md` explicitly excluded); local annotated tag `v0.10.0` created and verified against `6201553` via `git tag -v`. **Not executed:** `git push origin main`, `git push origin v0.10.0` — held pending the user's explicit go. |
| PR / merge | N/A — direct mode (no `Delivery & Handoff` section in `.spark/constitution.md`; matches both prior `release-board*` cycles, which also released direct-to-`main`). |
| Deploy | **Not yet run — awaiting explicit user go.** Pending outward-facing commands: `git push origin main` and `git push origin v0.10.0`. No deploy target beyond the git remote exists for this CLI/library project (no hosted service, no package registry publish declared for this project). |
| Post-release smoke check | **Not yet run** — this step only makes sense after the tag is pushed. Planned smoke check once authorized: (1) `uv run insights releases --as-of <today> --format html --output <scratch-dir>` from a fresh clone/checkout of the pushed tag, confirm exit 0 and a `release-board.html` file is written; (2) open the file and confirm the index reads newest-first, at least one feature's document expands with real structured content (not raw markdown), and a deliberately-broken/missing artifact case (if any exists in the real repo) shows an honest notice rather than a blank section; (3) confirm `uv run insights releases --as-of <today> --format json` still exits 0 with unchanged field shape; (4) confirm no console/log noise from the CLI itself (exit code and stdout only, per the C2 idiom). |

**Exact pending commands (none executed yet — held for explicit user authorization):**
```
git push origin main
git push origin v0.10.0
```
(Local, reversible commands already executed this pass, for the record: `git commit` producing
`6201553`, and `git tag -a v0.10.0 -m "release-board-docs v0.10.0"` — see the block above.)

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
- [ ] Release actions executed and verified (or `aborted` with reason) — **partially executed,
  deliberately**: the local, reversible half (release commit `6201553`, local tag `v0.10.0`) is
  done and verified; the outward-facing half (push to `origin`) is correctly held pending the
  user's explicit go — a reportable, non-failure state per this role's own mandate, not an
  oversight. This box stays unchecked until push + the post-release smoke check in §3 actually
  run.
- [x] Learnings recorded — §4
- [ ] Status set to `released` — **not yet**; status is `preparing` pending the user's go. (Direct
  mode: no `handed-off` status applies here — no `Delivery & Handoff` section exists in
  `.spark/constitution.md`.)

**Rollback path (documented before any publish, per this role's Hard Rules):**
This feature is entirely additive/confined to the `releases --format html` code path plus two new
modules (`gitboard/artifactcontent.py`, `gitboard/markdownlite.py`); `--format json` is untouched
(independently re-verified in §1). It writes only one output file at render time
(`release-board.html`, same as `v0.9.0`) and reads existing `.spark/` files — no data migration,
no schema change, no persisted state beyond that one rendered file.
- **Right now (commit + tag local, nothing pushed):** `git tag -d v0.10.0` then `git reset --hard
  <the commit before 6201553>` cleanly discards both and restores `0.9.0`'s tree and behavior
  exactly — nothing external has seen either artifact yet, so this is a zero-cost, fully clean
  undo.
- **After push (only relevant once the user's go is given and §3's pending commands run):**
  `git revert 6201553` on `main` (not a force-push/history-rewrite) restores `0.9.0`'s behavior
  forward, then delete and re-push the tag pointer only if genuinely necessary (`git tag -d
  v0.10.0 && git push origin :refs/tags/v0.10.0`) — but since `main` is a shared branch, a
  forward revert is strongly preferred over any rewrite. Because the feature only ever writes one
  regenerated `release-board.html` file, there is no "stale data left behind" case: the very next
  render (pre- or post-revert) fully regenerates that one file from source, with no migration or
  backfill step required either direction.
