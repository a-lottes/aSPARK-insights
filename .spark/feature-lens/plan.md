# Plan: feature-lens

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/feature-lens/spec.md` (must be `approved`) |
| **Status** | `approved` |
| **Date** | 2026-08-25 |

**Handoff**
- **Status:** `approved` (2026-08-25, user approval in conversation) — header table authoritative
  for `Status`.
- **Summary:** Two new **pure** modules (`gitboard/featurelens.py`, `gitboard/featurelens_report.py`)
  and one new CLI subcommand. `build_feature_lens(release_map)` is a dict→dict regrouping pass over
  `build_release_map()`'s already-assembled `releases[]`/`members[]` — zero new git calls, zero new
  `.spark/` reads, zero lines changed in any shipped `gitboard` module (NFR-2 holds *structurally*,
  not by test). The HTML page appends its own `_LENS_STYLE` to the shipped `_STYLE` and imports
  `_ARTIFACT_HUES`/`_esc`/`_strip_status_backticks`/`_render_masthead` rather than forking them.
- **Open:** `1 task not done` (T8, `/demo-day`'s browser measurement harness — contrast, 375px
  scroll, DOM order, wall-clock timing; not a code task). T1-T7, T9 done. Full suite green at 745
  (up from 679; 66 new tests, all this feature's own).
- **Deviation, recorded during T4 (small, obvious correction per `/increment`'s own rule):** T4's
  DoD asked to assert the interactive-element count (`a,button,input,select,textarea,[tabindex]`)
  "equal to the release board page's own count" — but `feature-lens.html` is a brand-new page with
  no prior version of itself to diff against, so a literal count-equality check against
  `release-board.html` (which has many `<a>` navigation links) would be false and meaningless. The
  actual, stronger fact, verified: the page has **zero** interactive elements of any kind — keyboard
  operability holds trivially, by construction. Test:
  `test_zero_interactive_elements_keyboard_operability_by_construction`
  (`tests/test_featurelens_render.py`).
- **Binding ruling:** §3 Task Breakdown for current task status; a plan revision after review/QA
  findings updates §1/§3 in place, never a new section
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch as a
  finding at the next `/peer-review` and proceed — don't stop on it.

## 1. Architecture Decision

- **Context:** `build_release_map(repo_root, as_of)` already returns, per release, a `members[]` list
  whose every entry carries `name`, the 5-artifact `status` map (each `{status, date, reason}`),
  `delivery` (`{delivering, delivered_in, reason}`) and `scope` — verified by reading `releasemap.py`
  (A1). A feature appears once per release it has a commit in, so the *only* genuinely new work is a
  **regrouping**: collapse N occurrences into one row, read (never re-derive) the delivery anchor, and
  label a gate. Two shipped invariants make this cheap and safe: `_member_entries` reads each
  artifact's status from the **working tree** (`.spark/<name>/<artifact>.md`), so every occurrence of
  the same feature carries a byte-identical `status` map within one run; and `_attribute_delivery`
  has already stamped the oldest-occurrence rule onto each member. Membership itself comes from git
  ranges — so a `.spark/` directory with no commit under it is not in the release board's universe and
  will not be in this one either (see §5).
- **Decision:** **One pure transform module, one pure render module, one thin CLI adapter — nothing
  shipped is edited.**
  1. **`gitboard/featurelens.py`** (new, pure, no `subprocess`/`gitread`/`Path` import):
     `current_gate(status) -> (gate, gate_artifact, evidence)`, `group_by_gate(features)`, and
     `build_feature_lens(release_map: dict) -> dict`. It walks `release_map["releases"]` in the order
     given (oldest-first, pseudo last), takes each feature's payload from its **delivering** occurrence
     when one exists and otherwise its first (oldest) occurrence, and reads `delivered_in` as *the tag
     of the release whose occurrence has `delivering: True`* — never "the oldest release it appears
     in", which would be a second implementation of the shipped rule (A4/ADR-0).
  2. **`gitboard/featurelens_report.py`** (new, pure `dict -> str` plus one `run_*` writer):
     `render_feature_lens_html(data)` and `run_feature_lens_report(data, output)` writing
     `<output>/.aspark-insights/feature-lens.html`. Imports `_STYLE`, `_ARTIFACT_HUES`,
     `_strip_status_backticks`, `_render_masthead` from `releaseboard_report.py` and `_esc` from
     `render.py` — the same cross-module private-choke-point import the shipped release board already
     makes (`from aspark_insights.render import _esc`), so this is house style, not a new pattern.
     Page CSS is `f"<style>{_STYLE}{_LENS_STYLE}</style>"`: **additive only**, so the release board's
     own bytes and its determinism tests are untouched, and NFR-4's per-cell wrap rules are scoped to
     `.lens-table` instead of widening the shipped generic `th, td` rule.
  3. **`cli.py`**: one `p_features` subparser (`--as-of` required, `--repo`, `--output`, `--format
     {json,html}`) and `_cmd_features`, wired exactly like `_cmd_releases` — `build_release_map(...)`
     then `build_feature_lens(...)`, `canonical_json` to stdout for `json`, and the lazy-imported
     renderer plus `{"report": <path>}` for `html`. No new `InsightsError` subclass (NFR-1):
     `build_feature_lens` catches `(KeyError, TypeError, AttributeError)` at its own boundary and
     raises the existing `ReleaseMapUnreadableError`, mirroring `run_release_board_report`.
- **JSON payload (pinned here so `/increment` invents nothing):** `{"provenance": <release_map's own,
  verbatim>, "features": [{"name", "spec_date", "spec_date_reason", "status": <5-artifact map
  verbatim>, "gate", "gate_artifact", "gate_evidence": [{"artifact","status","reason"}, ...],
  "delivered_in", "delivered_in_reason"}], "reason": null | <string>}`. No `pipeline` key: US-3 is an
  HTML section (§6/C4) and a consumer can group by `gate` itself; `group_by_gate` stays a pure,
  unit-tested helper the renderer calls. No `scope` key either — checked, then declined (§6/C6).
- **Named sub-decisions (not left to `/increment`):**
  - **Row order (AC-1.5/C5):** dated features sorted by name ascending, then stable-sorted by the
    literal `spec_date` **string** descending (never parsed — a malformed date must not raise);
    undated features follow, name ascending. Undated is never treated as newest and never dropped.
  - **Gate evidence (AC-2.1/NFR-5):** the deciding artifact's own `"<artifact>: <status>"` plus, when
    the decider is not `release`, the next artifact in the sequence rendered from its **verbatim
    reason** — e.g. `Increment — plan: approved, review: file not found`. AC-2.1's illustrative
    "review: not started" is deliberately *not* copied as literal output: "not started" would assert
    more than the data knows (a file can be unreadable rather than absent), and NFR-5 binds over an
    `e.g.`. `Unknown` surfaces `spec`'s own reason verbatim (AC-2.4).
  - **Gate rendering (AC-2.1/AC-2.5/C9):** one `<span class="badge gate">` — a single class, a single
    non-artifact hue, for all six values; no per-gate palette, no bar/track/dot device anywhere on the
    page. Pipeline buckets are `<h3>` + `<ul>`; empty buckets get the same `<h3>` and the shipped
    `.empty-notice` idiom (AC-3.2 parity), never a dim or a collapse.
  - **Table shape (AC-1.5/NFR-4):** a real `<table class="lens-table">` inside the shipped
    `.table-wrap`, `<th scope="col">` on all nine columns, the date column headed exactly
    `spec.md's own Date (last updated)` (NFR-5). Each of the five status cells is a `_ARTIFACT_HUES`
    type badge plus the literal status, and the reason text **only** when `status is null`.
  - **Empty cases (NFR-7):** zero releases → `reason` is the map's own verbatim reason (e.g.
    `repository has no tags`); releases but no members anywhere → `no features found`. Either way the
    page renders one `.empty-notice`, no table and no pipeline section.
- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | Put `build_feature_lens` in `releasemap.py` | That module's docstring pins it as *the one read* — a git-dependent module whose tests need a real repo. A pure regrouping there inherits that setup for logic that needs none, and makes the six-state gate fixtures (AC-2.3/2.4/3.3) far more expensive to write than a dict-in/dict-out unit test. `scopecount.py` already set the precedent: a new sibling module with its own honesty contract. |
  | Add a `features` key to `build_release_map()`'s output | Changes `insights releases --format json` bytes and re-opens its determinism/render tests for a payload no `releases` consumer asked for, and makes every `releases` run pay for it. Purely-additive-elsewhere (NFR-2) is stronger when nothing shipped is touched at all. |
  | Compute the grouping inside the HTML renderer | AC-1.1 is a `--format json` criterion and §2 names a future `aspark-ci` JSON consumer, so the renderer would be a second implementation the moment JSON needs it — the exact CLI/MCP-parity mistake CLAUDE.md's "shared core, thin adapters" rule exists to prevent, and the same alternative `release-metrics` rejected. |
  | A new module that enumerates `.spark/` itself so never-committed feature dirs appear | A second membership source next to the shipped git-range rule (A4/ADR-0), producing rows the release board itself denies exist. The limitation is disclosed in `--help`/README instead (§5, R2). |
  | Render the feature lens as a third section of `release-board.html` | §6/C4 puts the pipeline in *this* feature's page, and NFR-1 asks for a sibling subcommand. Folding it into the release board would edit a reviewed, byte-pinned page and couple two commands' output. |
  | Refactor `_STYLE`/`_ARTIFACT_HUES` out into a shared `gitboard/boardstyle.py` first | A speculative refactor of a shipped, contrast-measured stylesheet whose only justification is tidiness; it would move bytes the release board's determinism tests depend on. Import the names and append `_LENS_STYLE` — reversible in one commit if a third page ever appears. |
  | Derive `delivered_in` as "the oldest release the feature appears in" | Structurally identical to the shipped `_attribute_delivery` rule and therefore a second copy of it (A4). Read `delivery["delivering"]` instead — one careless edit can then never desynchronise the two views. |
- **Consequences:** *Easier* — the gate algorithm and the grouping are testable at unit speed with
  hand-built dicts, so the six gate states get real coverage despite this repo having only `Released`
  data (A3); NFR-2 needs no regression test because no shipped file is edited; both views are provably
  one computation (ADR-0). *Harder* — the lens inherits the release board's whole per-release git walk
  (~12 s on this repo, `release-metrics` NFR-8's disclosed pre-existing cost) even though its own work
  is O(features) in memory; the page is coupled to `_STYLE` by import, so a future edit there changes
  two pages at once; and a nine-column table is the widest thing this visual system has shipped.

## 2. Affected Components

- **New:** `src/aspark_insights/gitboard/featurelens.py` (pure transform),
  `src/aspark_insights/gitboard/featurelens_report.py` (pure renderer + writer), seven new test
  modules (§4).
- **Modified:** `src/aspark_insights/cli.py` (one subparser + one `_cmd_features`),
  `src/aspark_insights/__init__.py` + `pyproject.toml` (version `0.11.0` → `0.12.0` — a new
  subcommand is a behavior change, so the bump is earned, not ceremonial), `README.md`.
- **Read-only imports, not modified:** `releasemap.py`, `releaseboard_report.py`, `render.py`,
  `errors.py`, `serialization.py`, `store.py`.
- **New dependencies:** none — stdlib only, zero new runtime pip dependency (NFR-2).
- **Blast radius:** the `aspark-graph` `impact` query for the union of the `files:` notes below
  (`src/aspark_insights/cli.py`, `src/aspark_insights/__init__.py` — the only two indexed source
  files that already exist) **was requested but has not been run**: this planning pass had no shell.
  §2 above is therefore **scoped by hand**, from reading `cli.py`, `releasemap.py` and
  `releaseboard_report.py` directly. If the query is relayed later, fold its `affected_stories`/
  `affected_acs` in here and say so; an empty result would mean *the analysed plans declare no file
  links*, never *nothing is at risk*.

## 3. Task Breakdown

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Walking skeleton: `featurelens.py` (`current_gate` + `build_feature_lens`) and the `insights features` json branch, end to end | US-1, US-2 | AC-1.1 (json), AC-1.2, AC-2.1 (computation), AC-2.2, NFR-1 (shape), NFR-2, NFR-8 | – | `done` | `insights features --as-of 2026-08-25 --format json` exits 0 against this repo and lists each of the 11 named features exactly once, each with its own 5-artifact `status` map verbatim, `gate: "Released"` and its own `release.md` literal status; `release-board-docs` reads `spec_date: "2026-08-23"`, `delivered_in: "v0.10.0"` and appears exactly once despite its `v0.11.0` trailing occurrence; a test pins that two occurrences of one feature carry equal `status` maps (the invariant dedup rests on); a test asserts `featurelens.py`'s source imports neither `subprocess` nor `gitread` nor `pathlib` (NFR-8's zero-extra-git-call claim, structural); stdout goes through `canonical_json` — files: src/aspark_insights/gitboard/featurelens.py, src/aspark_insights/cli.py, tests/test_featurelens_gate.py, tests/test_featurelens_cli.py |
| T2 | Honest degrade + gate evidence + ordering | US-1, US-2 | AC-1.3, AC-1.4, AC-2.1 (evidence pairing), AC-2.4, NFR-5 | T1 | `done` | A feature whose only occurrence is the pseudo-release reports `delivered_in: null` with the reason string `not yet delivered in a tagged release` **copied byte-for-byte** from `member["delivery"]["reason"]` (asserted by comparing against the release map's own value, not a literal); an unreadable/absent/header-tableless `spec.md` still yields a row with the specific per-field reason and never raises; `gate_evidence` always carries the deciding artifact's literal status, plus the next artifact's verbatim reason when the decider is not `release`; row order is date-descending, name-ascending, undated last, proven with a malformed date string that must not raise — files: src/aspark_insights/gitboard/featurelens.py, tests/test_featurelens_gate.py |
| T3 | Six-stage fixture repo (real git, no mocks) | US-2 | AC-2.3, AC-2.4 | T2 | `done` | One pytest fixture builds a real git repo with seven feature directories — one each at `Spec`, `Increment` (approved `plan.md`, no `review.md`), `Review`, `QA`, `Released`, `Unknown` (a `spec.md` with no header table), plus one committed after the only tag so it is pseudo-release-only — and `build_feature_lens(build_release_map(...))` returns exactly the expected gate for each, `Unknown` surfacing its own reason and never guessed as `Spec` — files: tests/test_featurelens_fixtures.py |
| T4 | HTML page: table, badges, wrap discipline, writer, `--format html` branch | US-1, US-2 | AC-1.1 (wrap), AC-1.5, AC-2.5, NFR-1, NFR-4 (structural) | T2 | `done` | `insights features --as-of <d> --format html` writes `<output>/.aspark-insights/feature-lens.html` and prints only `{"report": <path>}`; the page has exactly one `<h1>`, a real `<table class="lens-table">` inside `.table-wrap` with nine `<th scope="col">` cells including the literal header `spec.md's own Date (last updated)`, rows in T2's order, each status cell an `_ARTIFACT_HUES` type badge with the reason present only when the status is null; `_LENS_STYLE` gives every `.lens-table th, .lens-table td` an `overflow-wrap`/`max-width` rule and the shipped `_STYLE` string is embedded unmodified; the gate uses one badge class with no per-value hue and the page source contains no bar/track/meter/progress element; the interactive-element count (`a,button,input,select,textarea,[tabindex]`) is asserted equal to the release board page's own count — files: src/aspark_insights/gitboard/featurelens_report.py, src/aspark_insights/cli.py, tests/test_featurelens_render.py |
| T5 | Pipeline section (`group_by_gate` + rendering) | US-3 | AC-3.1, AC-3.2, AC-3.3, AC-3.4 | T3, T4 | `done` | Every feature lands in exactly one bucket (a test sums bucket sizes against the feature count and asserts disjointness); buckets render in `Spec`/`Increment`/`Review`/`QA`/`Released` order, `Unknown` present only when non-empty, each as `<h3>` + `<ul>` nested under the page `<h2>`; against this repo's real data `Released` lists all 11 named features and each other bucket carries its own `<h3>` plus an `.empty-notice` sentence with the same classes/type scale as a populated bucket (asserted on the markup, not eyeballed); against T3's fixture each bucket shows exactly its one expected feature; severability is checkable by inspection — every pipeline assertion lives only in this task's test module and the section is one call site in the page assembly — files: src/aspark_insights/gitboard/featurelens.py, src/aspark_insights/gitboard/featurelens_report.py, tests/test_featurelens_pipeline.py |
| T6 | Security: fresh hostile fixture, both formats | US-1 | NFR-3 | T4 | `done` | A newly hand-built fixture (not a copy of `test_releaseboard_security.py`'s) with a `<script>alert(1)</script>` feature-directory name **and** a `<script>`-named git tag runs end to end through the real CLI in both formats: no unescaped `<script` in the HTML, the payload present only in escaped form, exit 0, and no raw traceback; separately, an unreadable `spec.md`, a feature directory with no artifacts at all, a zero-feature `.spark/`, and a malformed release-map dict each produce either a clean result or a named `InsightsError` on stderr — files: tests/test_featurelens_security.py |
| T7 | Determinism, offline, edge-repo shapes | US-1 | NFR-6, NFR-7 | T4 | `done` | Two consecutive runs at a fixed `HEAD`/`as_of` are byte-identical in both formats; the rendered page contains no `http://`/`https://`/`//` external font, script or stylesheet reference and no `<script>` tag of its own; `datetime.now` appears nowhere in either new module (source assertion); a 0-tag repo, a 0-feature repo, a 1-feature repo and this repo's full history each render without error, the empty cases stating their own reason in words — files: tests/test_featurelens_determinism.py |
| T8 | `/demo-day` verification harness notes | US-1, US-3 | NFR-4 (measured), NFR-8 (measured) | T5 | `todo` | The page is opened in a real browser and recorded: WCAG contrast for gate badge, status badges, `.empty-notice` and table text via `getComputedStyle` (4.5:1 text / 3:1 non-text); `window.innerWidth`/`document.documentElement.scrollWidth`/`clientWidth` at 375px showing no page-level horizontal scroll; DOM order of the table and pipeline sections by byte offset in `outerHTML`; and wall-clock time of `insights features --format json` versus `insights releases --format json` recorded so this feature's own O(features) cost is separated from the inherited git-walk cost, disclosed rather than claimed |
| T9 | Close-out: version, `--help`, README | US-1 | NFR-1, NFR-2 | T6, T7 | `done` | Version `0.11.0` → `0.12.0` in both places; `insights features --help` documents the `--output` write location and states exactly what `--repo` is read for (git plumbing, `.spark/` directory names and each feature's five artifact header tables — no document bodies) and that a feature directory with no commit under it is not listed; README gains a feature-lens section and a Project Status entry; `git diff --stat` shows no change to any file under `src/aspark_insights/gitboard/` other than the two new modules, and the pre-existing suite passes unchanged (NFR-2, structural) — files: src/aspark_insights/__init__.py, pyproject.toml, src/aspark_insights/cli.py, README.md |

## 4. Test Strategy

- **Unit (pure, no git — the bulk).** `current_gate`, `group_by_gate` and `build_feature_lens` take
  hand-built dicts, so all six gate values, the dedup, the delivery read, the ordering rule and every
  degrade path are covered at unit speed (`tests/test_featurelens_gate.py`). This is the payoff of
  keeping the transform out of `releasemap.py`.
- **Integration, real git, never mocked (house rule).** `tests/test_featurelens_fixtures.py` builds
  real repos with `git init`/`commit`/`tag` using the existing `_git`/`_commit` helper shape, and
  `tests/test_featurelens_cli.py` shells out to the real CLI (`python -m aspark_insights.cli`) both
  against a fixture repo and against **this** repo.
- **Per Must story.** US-1: AC-1.1/AC-1.2 against this repo's real data (T1), AC-1.3/AC-1.4 against
  fixtures (T2/T3), AC-1.5 against rendered markup (T4). US-2: AC-2.1 unit + markup, AC-2.2 real data,
  AC-2.3/AC-2.4 fixtures (T3), AC-2.5 asserted on markup (no per-value hue, no bar/track element).
  US-3 (Should): AC-3.1/AC-3.2 real data + markup, AC-3.3 the six-stage fixture — the only AC that
  proves the grouping end to end (A3/C8).
- **Real-data limitation, honored explicitly (A3/C8).** No fixture assertion is ever described as
  covering the real case and no real-data assertion stands in for a gate state this repo doesn't have.
  Assertions over this repo are written as *"each of these 11 named features appears exactly once and
  reads `Released`"* — **never** as an exact row count, because this feature's own
  `.spark/feature-lens/` directory becomes a 12th, genuinely in-flight feature the moment its
  artifacts are committed during `/increment` (see §5 R1).
- **Left to `/demo-day` in the browser, with a reason (T8).** Contrast ratios, 375px scroll behavior
  and section ordering are measurable only against a rendered page, per this project's established
  technique (`snapshot-report`); the NFR-8 timing split needs a real machine, not a test assertion.
  Everything structurally checkable (semantic markup, `scope="col"`, single `<h1>`, interactive-element
  count parity, no external fetch) is asserted in the suite, not deferred.
- **Regression.** No existing test is modified. NFR-2 is proven by the diff (no shipped module
  touched) plus the full pre-existing suite passing unchanged (T9).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **R1** This increment's own `.spark/feature-lens/` artifacts get committed mid-cycle, so the repo grows a 12th feature sitting at `Increment`/`Review` — an exact-count assertion for AC-1.1/AC-2.2 would go red mid-`/increment` | Medium — a spurious test failure that looks like a defect | Write every real-data assertion as containment + exactly-once over the 11 **named** features (§4). Treat the accidental real in-flight row as a bonus signal, never as a substitute for T3's fixtures (A3 stands) |
| **R2** A `.spark/<feature>/` directory with no commit under it is invisible (membership is a git-range fact) — e.g. this very feature before its first commit | Medium — a first-time user reads a missing row as a bug | Deliberate: the alternative is a second membership source (§1). Disclosed in `--help` and README (T9), and it matches the release board exactly, so the two views never disagree |
| **R3** `_STYLE` is imported, not copied: a future edit to the release board's stylesheet silently restyles this page | Medium — contrast/wrap regressions on a page nobody was editing | `_LENS_STYLE` owns every lens-specific rule; a test asserts the shipped `_STYLE` is embedded verbatim, so a change is at least visible as a failing byte comparison, and contrast is re-measured at each `/demo-day` |
| **R4** Nine columns is the widest table this visual system has shipped; per-cell wrap may still leave the `.table-wrap` container scrolling at 375px | Medium — NFR-4's bar is page-level, not container-level, but the reading experience can still be poor | Per-cell `max-width`/`overflow-wrap` (T4) plus the measured 375px check (T8). If the container proves unusable, the fallback is fewer visible columns, not a wider page — a layout call for `/demo-day`, recorded here so it isn't improvised |
| **R5** Gate evidence prints the artifact's verbatim reason (`review: file not found`) where AC-2.1's example says `review: not started` | Low — a reviewer may read it as non-compliance | Recorded as a named sub-decision in §1 with its NFR-5 justification; the AC's own `e.g.` makes the wording illustrative |
| **R6** `insights features` inherits the release board's ~12 s per-release git walk (`release-metrics` NFR-8's disclosed pre-existing cost) | Low — a slow command, not a wrong one | NFR-8 already carves this out; T8 measures and reports the two commands side by side so this feature's own cost is separated rather than absorbed into a claim |
| **R7** `spec.md`'s `Date` is the "last updated" field (aSPARK core issue #24) and sits next to a delivery tag | Low, but it is the exact misreading A5/C3 cut cycle time to avoid | The column header is pinned verbatim to `spec.md's own Date (last updated)` (T4) and no derived duration is computed anywhere on the page or in the JSON |

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft) — `approved` 2026-08-25, header table read directly
- [x] Architecture decision includes rejected alternatives — seven, each with its reason
- [x] Architecture respects the constitution's technical constraints — ADR-0 (no re-derivation: delivery and membership are read, never recomputed), ADR-4 (no clock; `as_of` stays an input), ADR-5 (one self-contained offline page), §3 no-second-git-parser (zero new git calls), §3 named-error taxonomy + `canonical_json`, §6 no verdict / no person-level data; no conflict found
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task — AC-1.1…1.5, AC-2.1…2.5 and NFR-1…8 all appear in §3's Covers column
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies — T1 is the runnable end-to-end skeleton; the Should (T5) sits after both Musts
- [x] Test strategy covers every Must story — §4, with the A3 fixture-vs-real-data split named explicitly
- [x] Status set to `approved` by the user — 2026-08-25, in conversation
