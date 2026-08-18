# Plan: git-native-mid-cycle-board

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/git-native-mid-cycle-board/spec.md` (status `approved`) |
| **Status** | `approved` |
| **Date** | 2026-08-13 |

## 1. Architecture Decision

- **Context:** A standalone, read-only surface that answers "what landed since the last
  release marker, what's in flight" from local git plumbing only — no `GraphPort`, no `.spark/`,
  no `Snapshot` (C1/A5: `build_snapshot` raises `GraphNotBuiltError` with no graph, so folding
  git-facts into the Snapshot makes them unreachable in the exact no-graph case this feature
  exists to prove). Every output self-discloses `source: git-interim` (AC-1.9, the ADR-2
  fallback made enforceable). The spec left six implementation calls to this plan.

- **Decision (the six open calls):**
  1. **Shape = a plain `gitboard/` package of pure + subprocess-wrapping modules, *not* a
     `ports/` member.** `ports/` holds seams to *sibling systems* (`GraphPort`, `PolicyPort`)
     that carry a version pin and a "not yet built" null-adapter state; git is always-local,
     has no version to pin and no null-adapter state to degrade through — it is either runnable
     or it is not. This is exactly `measurement-honesty`'s ruling that its filesystem probe was
     not a `ports/` member (plan §1.2). Modules: `gitread.py` (the subprocess seam), `worktype.py`
     (pure classification), `board.py` (`build_board(repo, as_of)` → dict, the shared core),
     `report.py` (HTML).
  2. **Subprocess contract:** fixed argument vectors with `git -C <path>` (never `cwd`, never a
     shell string — the `CLIGraphPort` rigor NFR-2 demands), `subprocess.run(capture_output=True,
     text=True, timeout=…)`. An explicit `ensure_git_repo()` probe (`git -C <p> rev-parse
     --git-dir`) runs first so every later nonzero exit is disambiguated: `FileNotFoundError` →
     `GitUnavailableError` (git absent, AC-1.5); `ensure_git_repo` nonzero → `NotAGitRepoError`
     (empty/traversal/absolute/non-git/corrupt `.git`, AC-1.4/AC-2.3); `describe --tags` nonzero
     *after* the repo is proven valid → **no tag → `None`**, the honest null (AC-1.2), never an
     error; `TimeoutExpired` → `GitUnavailableError` (git produced no usable result in budget).
     Reads use `%x1f`-delimited `--format` (`%h`/`%s`/`%cI` only) with newline record separators.
  3. **Type-parsing lives in `worktype.py` as two pure functions:** `classify(subject) -> str|None`
     (a fixed compiled regex against the 10-token set, optional `(scope)`/`!`, case-insensitive,
     normalized — never a regex built from repo content, NFR-2) and `breakdown(subjects) ->
     dict|null` (the 20% threshold + explicit `unclassified` share). The **absent** cases
     (AC-1.12(c) no tag, (d) 0/0) are decided in `board.py` *before* `breakdown` is called,
     since they depend on tag/count, not on the subjects.
  4. **HTML seam = a new `report.py` that imports `_esc` and `_STYLE` from `render.py` and
     builds its own markup.** `_esc` must be the *literal* same choke-point (AC-1.7/NFR-2);
     `_STYLE` is imported and a small board-only block appended, so the just-verified palette
     (`.metric-card`, `.metric-bar`, `.confidence-*`) cannot drift. The card/table *builders*
     (`_render_metric_card`, `_render_metrics_full_table`) are **not** reused — they assume
     Snapshot-shaped metric dicts (`metric_id`/`n`/`reason`) this feature has no honest analogue
     for. Genuinely-new primitives: the commit-row type badge and the interim marker (AC-4.7
     confirms `render.py` ships no badge precedent).
  5. **CLI = one subcommand `board` with `--repo`, `--as-of` (required), `--output`,
     `--format {json,html}` (default `json`).** Both formats consume one `build_board()` result,
     so JSON↔HTML parity is structural (the "shared core, two thin adapters" house pattern,
     `mcp-server` precedent). `json` → stdout, writes nothing, `--output` irrelevant (AC-4.4);
     `html` → writes `<output|repo>/.aspark-insights/board.html`, prints its path as JSON.
  6. **Accessibility markup (A8 divergence, concrete):** branch listing = real `<table>` +
     `<caption>` + `<th scope="col">`, age cell = `.metric-bar` **plus numeric age text**
     (AC-4.12(a)(d)); commit listing = `<ul>` of `<li>` each a `<dl>` with `<dt>/<dd>` for
     **Type, Subject, Hash, Date**, type badge inside the labelled Type `<dd>` (AC-4.12(b) — type
     not dropped); provenance = `<dl>` of `<dt>/<dd>` pairs (AC-4.6); each block a programmatic
     `<h2>`/`<caption>` (AC-4.12(c)); work-type bar = `.confidence-*` single-fill + adjacent
     legend, fixed order, `unclassified` last (AC-4.11).

- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | A `GitPort` under `ports/` mirroring `PolicyPort` | `ports/` = sibling-system seams with a version pin + null-adapter state; git has neither — it is runnable or not. Same reasoning that kept `measurement-honesty`'s probe out of `ports/`. |
  | git via shell string / `cwd=` built from repo content | Injection surface NFR-2 forbids; `-C <path>` fixed vector is the `CLIGraphPort` discipline the constitution names. |
  | Hand-parse every hostile `--repo` form before invoking git | Reimplements git's own repo-detection; instead we reject only empty-string early and let `rev-parse --git-dir`'s nonzero exit be the authority → one `NotAGitRepoError`. |
  | Inline type-parsing in command orchestration | The threshold/absent/unclassified logic is fiddly; a pure `worktype` module is unit-testable in isolation against subject lists. |
  | Reuse `render.py`'s card/table *builders* by faking metric dicts | They assume `metric_id`/`n`/`reason`; contorting board data into fake metric shapes is dishonest coupling. Reuse `_esc`+`_STYLE`, build board markup fresh. |
  | Copy the CSS vocabulary by paste | Drifts from the palette just re-verified this session; import `_STYLE`, append only new primitives. |
  | Two subcommands (`board` + `board-html`) | Duplicates flag wiring; one `build_board()` + a `--format` switch gives parity structurally. |
  | HTML to stdout | Offline self-contained file surface needs a write location and the `--output` discipline (AC-4.1/AC-4.4). |
  | One null treatment for every empty figure | AC-4.9 requires three distinct shapes: **absent** (no card), **null** (dashed card), **true zero** (real `0` card). |

- **Consequences:** *Easier* — US-2's standalone proof is structural (the package imports no
  `GraphPort`/`aspark_graph`, testable by an import assertion); JSON↔HTML parity from one core;
  `worktype` is a small pure seam. *Harder* — a second subprocess seam (git) with its own full
  hostile-input matrix; four new HTML color pairs (badge, interim marker, age bar, work-type
  segments) become a `/demo-day` `getComputedStyle` burden; the absent/null/true-zero trichotomy
  must thread consistently through JSON and four HTML surfaces.

## 2. Affected Components

<!-- Hand-scoped. `aspark-graph query staleness --repo .` was reported stale: true earlier this
     session, so per the tool's own "stale ⇒ absent" rule (and the last two plans' house standard)
     no impact result is cited as evidence; I have requested `aspark-graph query impact
     src/aspark_insights/errors.py src/aspark_insights/cli.py src/aspark_insights/render.py
     src/aspark_insights/__init__.py --repo .` on the union of the *existing* files these tasks
     touch, and will fold in a fresh result if staleness clears. The new gitboard/* files have no
     graph node yet, so impact could only speak to the four existing files above. Scoped by reading
     the code directly below, not from the graph. -->

- **New:** `src/aspark_insights/gitboard/__init__.py`, `gitboard/gitread.py`, `gitboard/worktype.py`,
  `gitboard/board.py`, `gitboard/report.py`; test modules named per task.
- **Changed:** `src/aspark_insights/errors.py` (+`GitUnavailableError`, +`NotAGitRepoError`),
  `src/aspark_insights/cli.py` (`board` subcommand + `_cmd_board`),
  `src/aspark_insights/__init__.py` (version bump), `README.md`.
- **Imported, not changed:** `src/aspark_insights/render.py` (`_esc`, `_STYLE`),
  `src/aspark_insights/serialization.py` (`canonical_json`).
- **Dependencies:** zero new runtime pip deps (NFR-6) — `git` is a subprocess, `subprocess`/`re`/
  `datetime` are stdlib. New error subclasses are the house named-error taxonomy, not a dependency.

## 3. Task Breakdown

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Walking skeleton: git seam + minimal board + `board --format json` | US-1, US-2 | AC-1.2, AC-1.5, AC-1.6, AC-1.8, AC-1.9, AC-2.1, AC-2.2, AC-2.3, NFR-1, NFR-6, NFR-8 | – | `done` | `gitread.ensure_git_repo`/`resolve_tag`/`count_commits_since`/`is_shallow` invoke `git -C <path>` fixed vectors; `board.build_board(repo, as_of)` returns a dict carrying `source:"git-interim"`, a provenance block (`as_of`, `insights_version`, `git_available`, resolved tag or null+reason, `shallow`), and `commits_since_tag.value`; no-tag → `value:null`+reason exit 0 (AC-1.2), git-absent → `GitUnavailableError` exit 1 (AC-1.5), non-git/corrupt/empty `--repo` → `NotAGitRepoError` exit 1 (AC-2.3); `insights board --repo <no-graph-no-.spark repo>` exits 0; a test asserts the `gitboard` package imports no `GraphPort`/`aspark_graph` and never constructs one (AC-2.2); two runs at fixed HEAD+`as_of` are byte-identical via `canonical_json` (AC-1.6) — files: src/aspark_insights/errors.py, src/aspark_insights/gitboard/__init__.py, src/aspark_insights/gitboard/gitread.py, src/aspark_insights/gitboard/board.py, src/aspark_insights/cli.py, tests/test_gitboard_cli.py |
| T2 | Hostile `--repo` + git-invocation rigor | US-1 | AC-1.4, NFR-2 | T1 | `done` | Empty string is rejected before any git call; `../` traversal, an absolute path, a non-git directory and a corrupt `.git` each reach git as a fixed `-C` vector and map to `NotAGitRepoError` exit 1 with the git stderr folded into a named-error sentence — never a raw traceback, never a shell; `TimeoutExpired` maps to `GitUnavailableError`; a table-driven test runs all five hostile forms and asserts exit 1 + a named `error` reason on stderr and no traceback — files: src/aspark_insights/gitboard/gitread.py, tests/test_gitboard_security.py |
| T3 | Commit list, N=50 bound, privacy | US-1 | AC-1.1, AC-1.3, AC-1.7, NFR-3, NFR-4 | T1 | `done` | `gitread.list_commits_since` runs `git -C <p> log <tag>..HEAD --format=%h%x1f%s%x1f%cI --max-count=50`, splitting records on newline and fields on `\x1f`; `build_board` carries each commit's short hash, first-line subject (opaque string) and date, the **exact** total from `rev-list --count`, and a `truncated`/`total` disclosure when total > 50 (NFR-4); the `--format` string contains no identity placeholder (`%an`/`%ae`/`%cn`/`%ce`/`%b`/trailers) and a test scans the whole JSON for author/email/`Co-Authored-By`/`Signed-off-by` and finds none (AC-1.3, NFR-3); subjects are carried verbatim in JSON, parsed only for the AC-1.12 token (AC-1.7) — files: src/aspark_insights/gitboard/gitread.py, src/aspark_insights/gitboard/board.py, tests/test_gitboard_commits.py |
| T4 | Days-since-tag | US-1 | AC-1.10, NFR-5 | T1 | `done` | `gitread.tag_commit_date` reads the resolved tag's commit date; `build_board` computes whole days from that date to `as_of` (UTC-normalized, never `now()`, NFR-5); **no tag → the field is absent entirely** (AC-1.10(a), not a second null); a resolved tag whose commit date is unreadable → `value:null`+reason naming that cause (AC-1.10(b)); `--as-of` validated identically to `build` (reuse `InvalidAsOfError`, strptime `YYYY-MM-DD`); unit tests fix `as_of` and the tag date and assert the exact day count and both degradation states — files: src/aspark_insights/gitboard/gitread.py, src/aspark_insights/gitboard/board.py, tests/test_gitboard_days.py |
| T5 | Work-type breakdown | US-1 | AC-1.12, NFR-3, NFR-5 | T3 | `done` | `worktype.classify` matches the fixed 10-token set (optional `(scope)`/`!`, case-insensitive, normalized lowercase) via one compiled literal regex, returning the token or `None`; `worktype.breakdown` returns `value:null`+reason naming the counts when < 20% classify (no distribution), else a distribution with an always-present explicit `unclassified` share in the declared order (`feat`…`style`, `unclassified` last, zero counts omitted — NFR-5 visual comparability); `board.build_board` emits the breakdown **absent** on no tag and on zero-commits-since-tag (AC-1.12(c)/(d)) before calling `breakdown`; the five distinct states each have a test (< 20%, ≥ 20% with unclassified, no-tag-absent, 0-commit-absent, all-classified) — files: src/aspark_insights/gitboard/worktype.py, src/aspark_insights/gitboard/board.py, tests/test_gitboard_worktype.py |
| T6 | Local branch inventory | US-3 | AC-3.1, AC-3.2, AC-3.3 | T1 | `done` | `gitread.list_branches` runs `git -C <p> for-each-ref --format=%(refname:short)%x1f%(objectname:short)%x1f%(committerdate:iso-strict) refs/heads/`; `build_board` lists each branch with tip short-hash, tip date and an age in whole days = `as_of − tip-date` (never `now()`), no author identity; a single-branch checkout reports exactly the branches present (AC-3.2); an unreadable tip date → age `null`+reason (AC-3.3); tests cover multi-branch, single-branch, and unreadable-date — files: src/aspark_insights/gitboard/gitread.py, src/aspark_insights/gitboard/board.py, tests/test_gitboard_branches.py |
| T7 | HTML skeleton: block order, provenance, interim marker, answer sentence, stat cards | US-4 | AC-4.1, AC-4.2, AC-4.4, AC-4.5, AC-4.6, AC-4.8, AC-4.9, AC-4.13, NFR-8 | T4, T5, T6 | `done` | `report.render_board_html(board)` imports `_esc`/`_STYLE` from `render.py`, appends a board-only CSS block, and emits `<html lang="en">` + viewport meta + descriptive `<title>` + `<h1>`, then the fixed block order checkable by byte offset (AC-4.13): interim marker (`<p class="interim-marker">`, neutral, distinct from `.stale-cue`, AC-4.5) → answer sentence (AC-4.8: plain-language, the three degenerate states in words, `at least` shallow qualifier inline) → `.metric-card` stat row (AC-4.9: absent figure → no card, null → `.metric-card--null`+`.null-value`/AC-4.2, true zero → real `0` card) → `<h2>` Work types → `<h2>` Commits → `<h2>` Branches → `<h2>` Provenance (`<dl>` field/value pairs incl. `source: git-interim`, tag or null+reason, `shallow`, git-availability, active bound disclosures — AC-4.6); no network/JS (AC-4.1); an absent work-type block omits its `<h2>` (AC-4.13); `board --format html` honors `--output`, documented in `--help` (AC-4.4); a byte-offset test asserts the order and that absent blocks are omitted — files: src/aspark_insights/gitboard/report.py, src/aspark_insights/cli.py, tests/test_gitboard_render.py |
| T8 | HTML listings + named accessibility mechanisms | US-4, US-3 | AC-4.2, AC-4.3, AC-4.7, AC-4.10, AC-4.11, AC-4.12, NFR-7 | T7 | `done` | Commit listing = `<ul>`/`<li>` each a `<dl>` with `<dt>/<dd>` for Type, Subject, Hash, Date (AC-4.12(b), type never dropped), a `<span class="badge">` inside the labelled Type `<dd>` (the one new primitive, justified against AC-4.3/NFR-7 on its own); branch listing = real `<table>` + `<caption>` + `<th scope="col">`, age cell = `.metric-bar` **plus numeric age text** (AC-4.12(a)(d)); work-type breakdown follows `.confidence-mix` (single fill, hairline separators, adjacent legend, fixed order, `unclassified` equal weight) and renders neither bar nor null-card when absent (AC-4.11); no red/green judgment hue anywhere, status as text (AC-4.3); every dynamic string flows through `_esc` incl. commit subjects (AC-1.7); a test asserts the branch `<table>`/`<th scope>`/`<caption>`, the four commit `<dt>` labels, the badge label, the fixed legend order, and that a `<script>`-bearing subject renders escaped — files: src/aspark_insights/gitboard/report.py, tests/test_gitboard_render.py |
| T9 | Determinism canary, real-git integration, version, README, `--help` | US-1, US-2, US-4 | AC-1.6, NFR-3, NFR-5, NFR-6 | T7, T8 | `done` | A determinism canary double-builds a `tmp_path` real git repo (`git init`/commit/tag via subprocess) and asserts byte-identical JSON **and** `board.html`; an integration test builds a repo whose commits carry a `Co-Authored-By` trailer and asserts no author/email/trailer reaches JSON or HTML (NFR-3, live constraint), plus a shallow-clone repo disclosing `shallow:true` and the `at least` HTML qualifier; `__version__` bumped (behavior changed, NFR-6); README gains a `board` section documenting the standalone/`source: git-interim` guarantee, the 10-token set, the 20% rule and the write location — files: tests/test_gitboard_determinism.py, tests/test_gitboard_integration.py, src/aspark_insights/__init__.py, README.md |

## 4. Test Strategy

- **US-1 (commits/derivations) — unit + integration.** `test_gitboard_commits.py`: AC-1.1 count
  equals `rev-list --count` and the list carries hash/subject/date; N=50 bound with exact total
  and disclosure (NFR-4). `test_gitboard_days.py`: AC-1.10(a) absent vs (b) null, fixed `as_of`.
  `test_gitboard_worktype.py`: the **five distinct states** as separate cases (< 20% null,
  ≥ 20% with `unclassified`, no-tag absent, zero-commit absent, all-classified) + fixed order.
  `test_gitboard_cli.py`: AC-1.2 no-tag null exit 0 vs AC-1.5 git-absent exit 1 (distinct
  reasons, NFR-1); byte-identical repeat (AC-1.6).
- **US-2 (standalone proof) — unit.** `test_gitboard_cli.py`: runs against a `tmp_path` with
  neither `.aspark-graph/` nor `.spark/` and exits 0 (AC-2.1); an import-level assertion that the
  `gitboard` package references no `GraphPort`/`aspark_graph` (AC-2.2); a non-git dir → named
  result, never a fabricated zero (AC-2.3).
- **US-3 (branches) — unit.** `test_gitboard_branches.py`: multi-branch ages, single-branch truth
  (AC-3.2), unreadable-tip null age (AC-3.3), no identity field present.
- **US-4 (HTML) — unit for structure, `/demo-day` for pixels.** `test_gitboard_render.py`: block
  order by byte offset (AC-4.13), absent-block `<h2>` omission, null vs true-zero vs absent card
  shapes (AC-4.9/4.2), provenance `<dl>` pairing (AC-4.6), branch `<table>`/`<th scope>`/`<caption>`
  + commit `<dl>` four labels + badge label (AC-4.12), fixed legend order (AC-4.11), `_esc` on a
  `<script>` subject, no external ref / no JS (AC-4.1).
- **Security — unit.** `test_gitboard_security.py`: the full §4 hostile-`--repo` checklist (empty,
  `../`, absolute, non-git, corrupt `.git`) each → exit 1 named error, no traceback; fixed-vector
  assertion (NFR-2).
- **Privacy — unit + integration.** `test_gitboard_commits.py` scans JSON, `test_gitboard_integration.py`
  builds a real `Co-Authored-By` commit and scans JSON **and** HTML for any author/email/trailer
  token (NFR-3 — a live check, this repo's own commits carry such trailers).
- **Determinism — `test_gitboard_determinism.py`:** double-build a real temp git repo → byte-identical
  JSON and `board.html`; no wall-clock read in the derivation path (all elapsed figures `as_of`-relative,
  NFR-5).
- **Deferred to `/demo-day` (per "measure, don't eyeball"):** `getComputedStyle` contrast on the four
  new color pairs (interim marker, badge, work-type segments + hairline separators, per-branch age
  bar) against NFR-7's 4.5:1/3:1 bars; 375px `innerWidth`/`scrollWidth`/`clientWidth` on the commit
  list, branch table and provenance grid; the viewport meta; the rendered block order by byte offset
  in `outerHTML`. Real git repos are used throughout — git is not mocked (the sibling-integration
  precedent, applied to the git seam that is the whole point of this feature).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Four new HTML color pairs (badge, interim marker, age-bar fill, work-type segments/hairlines) unverified for contrast | Medium (NFR-7 fail at `/demo-day`) | Reuse `.metric-bar-fill`/`.confidence-seg` (`#1a1a1a`, pre-verified high-contrast) for the bars; badge + marker are the only genuinely new pairs → measured at `/demo-day`; every figure also carries numeric/text so no channel is color- or length-only (AC-4.12(d)). |
| Commit subject breaks `--format` parsing (embedded delimiter, non-UTF-8) | Medium (wrong list / crash) | `%x1f` field + newline record separators (a `%s` first line can contain neither); `text=True` with a replace-on-error decode; every subject re-escaped via `_esc` in HTML. |
| A future edit to a `--format` string silently adds an identity placeholder | High (NFR-3 / §6 breach) | A test asserts the format strings contain no `%an`/`%ae`/`%cn`/`%ce`/`%b`/trailer token, plus an output-scan test for author/email/`Co-Authored-By`/`Signed-off-by` (T3/T9). |
| AC-1.4 ("non-git dir → exit 1 named error") vs AC-2.3 ("honest named result, never a fabricated zero") read as conflicting | Low | Interpreted as one behavior: a `NotAGitRepoError` (exit 1) whose `to_dict()` on stderr *is* the honest named result and is never a `count:0` success. Recorded here, not raised as a blocker — AC-1.4 is explicit and AC-2.3's "never a fabricated zero" is satisfied. |
| Whole-days arithmetic off-by-one across timezones | Medium (wrong elapsed figure) | Normalize git's `%cI`/`iso-strict` dates to UTC before subtracting the `as_of` calendar date; unit tests pin `as_of` and the commit date and assert exact counts (T4/T6). |
| Shallow clone makes counts inexact | Low | AC-1.8 discloses `shallow:true` in provenance and AC-4.8 carries the inline `at least` qualifier on the answer sentence; asserted in T9. |
| Standalone surface pre-empts the "family-scoped vs standalone" fork (backlog I9) | Named risk (A6), not gate-blocking | Out of scope to decide here; the `source: git-interim` marker keeps this yielding to graph G1/G2 once they ship, so the lean is reversible. |

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft)
- [x] Architecture decision includes rejected alternatives (a decision without alternatives is a guess)
- [x] Architecture respects the constitution's technical constraints (or a conflict is recorded) — ADR-2 fallback authorized (A1/C5, `source: git-interim`); no `now()` (NFR-5); named errors, no raw traceback; never person-level (NFR-3); §4 accessibility divergence accepted as A8
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies
- [x] Test strategy covers every Must story
- [x] Status set to `approved` by the user (2026-08-13)
