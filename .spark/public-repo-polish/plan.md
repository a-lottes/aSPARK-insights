# Plan: public-repo-polish

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/public-repo-polish/spec.md` (`approved`) |
| **Status** | `approved` |
| **Date** | 2026-08-02 |

## 1. Architecture Decision

This is a documentation/config/hygiene increment — no `src/` change. The real decisions
are about *content*, so the ADR is deliberately light, but each choice names its rejected
alternative.

- **Context:** The repo is public today with a 4-line placeholder README, no root `LICENSE`
  (despite `pyproject.toml`'s `license = {text = "MIT"}`), gaps in `.gitignore`, and one
  already-`released` artifact (`.spark/traceability-metrics/release.md`) sitting untracked.
  Two shipped siblings (`aSPARK-graph`, `aSPARK-policy`) already set the family's public
  standard — a single root README, a verbatim-MIT `LICENSE`, `MIT © Andreas Lottes`.
- **Decision:** Mirror the siblings, do not invent. **(1)** One root `README.md` (no `docs/`
  subsite), section order `problem → install → usage → status → family → license` per
  AC-5.1, with an honest v0.2.0 status callout in the first lines (the `aSPARK-policy`
  pattern — status blockquote up top, fuller Status section lower). **(2)** `LICENSE` copied
  **verbatim** from `aSPARK-graph`'s file (standard MIT, `Copyright (c) 2026 Andreas Lottes`)
  so GitHub's detector recognizes it and the holder matches `pyproject.toml`'s `authors`.
  **(3)** `.gitignore` gets **five specific** new patterns, not a broad "harden it".
  **(4)** The orphaned `release.md` ships as its **own housekeeping commit**, separate from
  this feature's README/LICENSE/`.gitignore` diff, matching the `00e9c02` precedent.
- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | A `docs/` mini-site or multi-file README | Out of proportion to a hygiene cycle; C4 explicitly keeps `docs/`/`BACKLOG.md` as internal drafts and requires the README to stand alone instead |
  | Hand-write / SPDX-stub the MIT text | GitHub's `licensee` detector wants the standard template; copying the sibling's proven-detected file is zero-risk and keeps the family byte-consistent |
  | Copyright to an org name, or omit the year | `pyproject.toml` `authors` and both siblings say `Andreas Lottes` / `2026` — an org would be a fabricated holder |
  | Broad globs (`.env*`, `*.local`, a big boilerplate `.gitignore`) | Risks silently ignoring a file the repo means to track (AC-3.3 regression); the spec names the exact gaps, so add exactly those |
  | Fold `release.md` into the feature commit | Breaks the "each commit's diff matches what its own gate reviewed" convention (release.md was never in this feature's reviewed diff); housekeeping stays separate per `00e9c02` |
- **Consequences:** Easier — a stranger reads one file; the family reads as one product line;
  license is machine-detectable; git history stops lagging shipped reality. Harder — the
  README now carries live CLI claims that must be re-run at every `/demo-day` (Risk 1); any
  metric number shown becomes a dated-example maintenance point (Risk 2).

## 2. Affected Components

Scoped **by hand** — no tool file was passed and no `aspark-graph` blast-radius query was
run (a docs/config change touches no source node, so a story-level blast radius would come
back empty and ground nothing). Files touched:

- `README.md` — full rewrite (T3, T4).
- `LICENSE` — new file (T1).
- `.gitignore` — five appended patterns (T2).
- `.spark/traceability-metrics/release.md` — committed, content unchanged (T5).

No new dependency, service, or pattern. Ground-truth inputs read for content: `pyproject.toml`
(v0.2.0, `license={text="MIT"}`, `aspark-graph==0.7.0`, `uv.sources` path `../aSPARK-graph`,
`insights` script), `src/aspark_insights/cli.py` (real subcommands `build|query|render|diff|
verify` and their flags), the two sibling READMEs/LICENSE, and the release report.

## 3. Task Breakdown

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Add root `LICENSE` | US-2 | AC-2.1, AC-2.2, NFR-1 | – | `done` | A root `LICENSE` file exists with the standard MIT text copied verbatim from `aSPARK-graph`'s, header `Copyright (c) 2026 Andreas Lottes`; text matches `pyproject.toml`'s `license = {text = "MIT"}`; `grep -n "/Users/\|/home/" LICENSE` returns nothing; the file is close enough to the standard template that GitHub/`licensee` detects it as MIT — files: LICENSE |
| T2 | Harden `.gitignore` | US-3 | AC-3.1, AC-3.2, AC-3.3, NFR-1, NFR-2 | – | `done` | Append exactly five patterns under labeled comment sections — IDE: `.vscode/`, `.idea/`; secrets: `.env`, `.env.*`; OS: `Thumbs.db` — leaving every existing pattern unchanged (AC-3.1 no regression); a throwaway file matching each new pattern shows ignored in `git status` (AC-3.2/NFR-2); `git status` on the real tree is otherwise unchanged and `git check-ignore` flags no currently-tracked file (AC-3.3); no local path in the file (NFR-1) — files: .gitignore |
| T3 | README: structure, status, install, family, license link | US-1, US-5 | AC-1.1, AC-1.2, AC-1.4, AC-1.5, AC-1.6, AC-5.1, NFR-1, NFR-4, NFR-5 | T1 | `done` | README rewritten in section order `problem → install → usage → status → family → license`; first lines state what it is (versioned metric definitions/coverage metrics computed from `aspark-graph`'s facts, never recomputed) and honest status (v0.2.0; real TRC-001..005/MTA-001..003 shipped; dashboards/flow/architecture-health not yet built; no "Geplant", no production/dashboard/PyPI claim); Install describes source-only setup (Python ≥3.11, `uv sync --extra dev`, sibling `aSPARK-graph` checkout at `../aSPARK-graph` per `uv.sources`), no `pip install` (AC-1.2/NFR-4); links `aSPARK` Core, `aspark-graph`, `aSPARK-policy` and states this repo's place, without requiring `docs/`/`BACKLOG.md` (AC-1.4); License section names MIT and links the real `./LICENSE` (AC-1.5); no `/Users/`/`/home/` path, no internal URL, no invented number — `grep -n "/Users/\|/home/" README.md` empty (AC-1.6/NFR-1); any metric number shown is labeled a dated point-in-time example (NFR-5) — files: README.md |
| T4 | README: Usage — real, runnable CLI examples | US-1 | AC-1.3, NFR-3, NFR-5 | T3 | `done` | Usage section shows only real shipped subcommands/flags — `build --as-of <date> [--repo] [--output]`, `query [--repo] [--output]`, `diff <a> <b>`, `verify <snapshot> [--repo]`, and `render` labeled explicitly as the not-yet-implemented (I5) stub; every example either runs as-is against a real checkout or is labeled with its prerequisite (e.g. "requires a graph built via `aspark-graph build`"); each command is literally run at `/demo-day` and succeeds/behaves as labeled (NFR-3); any concrete value shown carries a dated point-in-time label (NFR-5) — files: README.md |
| T5 | Commit orphaned `release.md` (own housekeeping commit) | US-4 | AC-4.1, AC-4.2 | – | `done` | `.spark/traceability-metrics/release.md` (status `released`, v0.2.0) is present and unchanged on disk; the plan-of-record is that it ships as its **own** housekeeping commit, separate from this feature's README/LICENSE/`.gitignore` commit, matching the `00e9c02` precedent (actual commit executed at `/go-live`); at that point `git status` reports a clean tree with no untracked/modified file beyond this feature's own intended diff (AC-4.2) — files: .spark/traceability-metrics/release.md |

## 4. Test Strategy

No unit/integration tests: there is no runtime code path to assert on — the meaningful
verification is running the documented commands and observing git behavior, which is higher
value than asserting on Markdown/`.gitignore` text. "Manual" here means concrete, repeatable
checks, not eyeballing.

- **US-1 (README) — Must.** `/demo-day`: literally run every command in Usage against a real
  checkout (`insights build --help`; `insights build --repo ../aSPARK-graph --as-of
  2026-08-01 --output <scratch>`; `query`; `render` → the honest `not_implemented` stub;
  `diff`; `verify`) and confirm each succeeds or matches its prerequisite label (NFR-3).
  `/peer-review`: `grep -n "/Users/\|/home/"` on `README.md` is empty (NFR-1); Install claims
  checked against `pyproject.toml`/`uv.lock` — source-only, pinned sibling, no PyPI (NFR-4);
  every metric number is a dated example (NFR-5); the License link resolves to `./LICENSE`.
- **US-2 (LICENSE) — Must.** `/demo-day`: GitHub's license widget / a `licensee`-style check
  recognizes MIT (AC-2.2). `/peer-review`: holder/year match `pyproject.toml` and the sibling
  (AC-2.1); no local path (NFR-1).
- **US-3 (`.gitignore`) — Must.** `/demo-day`: create a throwaway file per new pattern
  (`.env`, `.env.local`, `.vscode/x`, `.idea/x`, `Thumbs.db`) and confirm `git status` shows
  each ignored (AC-3.2/NFR-2); confirm the rest of `git status` is unchanged and no
  previously-tracked file is now ignored via `git check-ignore` (AC-3.3); confirm the AC-3.1
  set still ignored (no regression).
- **US-4 (`release.md`) — Must.** `/go-live` pre-flight: after the housekeeping commit,
  `git status` is clean (AC-4.2) and the committed blob byte-matches the on-disk file (AC-4.1).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| README CLI claims drift as future increments change flags/subcommands | A public example stops working — the exact dishonesty this feature fixes | NFR-3 re-runs every command at each `/demo-day`; examples carry explicit prerequisite labels rather than pretending zero setup |
| A shown metric number goes stale or reads as invented | Violates NFR-5 / "never invent a number" | C3/NFR-5: any number is labeled a dated point-in-time example; prefer showing the *command* over baking in a value — omit numbers if a clean dated label isn't possible |
| LICENSE copyright-holder ambiguity (person vs org) | Wrong/legally-muddy holder in a public file | Copy the sibling verbatim: `Copyright (c) 2026 Andreas Lottes`, matching `pyproject.toml` `authors` — no new holder invented |
| A `.gitignore` pattern accidentally ignores a file the repo tracks | AC-3.3 regression, silent data loss from `git add` | Use the five specific patterns only (no broad globs); verify with `git check-ignore` against the tracked set and diff `git status` before/after |
| Committing `release.md` now vs. the existing `v0.2.0` tag on `7ef4a43` | Confusion about history — the tag predates this commit | Expected and fine: release reports lag their release (same as `foundation`'s own report in `00e9c02`); the tag stays put, `release.md` lands as a later housekeeping commit; `/go-live` owns the actual commit |
| US-5 tempts editing sibling repos to match (e.g. policy's stale "insights v0.1.0" line) | Out-of-scope edits to other products | US-5 is a one-way, light check on **our** README's section order/tone only; sibling repos are never touched |

## 6. Deviations (recorded during /increment)

- **README's Usage examples were reordered to lead with `--output` by default**, not as
  a secondary aside. T4's own verification (actually running every command, per NFR-3)
  caught this for real: running the plan's originally-drafted first example (`insights
  build --repo ../aSPARK-graph`, no `--output`) left a real, untracked `.aspark-insights/`
  directory in the sibling `aSPARK-graph` repo — precisely the "writes into a repo you're
  just reading" trap `foundation`'s own B1 finding was about. Every subsequent example
  (`query`, `diff`, `verify`) was updated to use the `--output`-redirected snapshot path
  instead of the sibling's own tree. No architecture change — pure README wording,
  caught and fixed within T4's own verification step, not escalated back to `/sprint-plan`.

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft)
- [x] Architecture decision includes rejected alternatives (a decision without alternatives is a guess)
- [x] Architecture respects the constitution's technical constraints (or a conflict is recorded)
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies
- [x] Test strategy covers every Must story
- [x] Status set to `approved` by the user
