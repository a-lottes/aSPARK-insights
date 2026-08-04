# Plan: snapshot-report

| | |
|---|---|
| **Phase** | Plan |
| **Owner** | Engineering Manager (`/sprint-plan`) |
| **Input** | `.spark/snapshot-report/spec.md` (`approved`) |
| **Status** | `approved` |
| **Date** | 2026-08-04 |

## 1. Architecture Decision

- **Context:** `insights render` is the last fake C2 subcommand — `_cmd_render`
  (`cli.py:132`) raises `NotImplementedStub`. Since I2 every `insights build` writes a real
  snapshot; the read path is already solved by `query` (`store.latest_snapshot_path` →
  `read_snapshot_dict` → `require_snapshot_shape`, then `{"facts","metrics","provenance"}`).
  This feature adds an HTML view of that same on-disk snapshot. It touches **no graph** —
  `GraphPort` is never reached (identical to `query`/`run_query`), so no graph-integration test
  is warranted; the only sibling contact is fixture *setup* that builds a real snapshot (never a
  mock, per constitution). It is the project's **first HTML-generating** surface: no existing
  HTML/CSS artifact exists here or in the sibling checkout (spec §8), so there is no house visual
  language to match — but there *is* a real XSS surface (`subject_id` etc. come from the analyzed
  repo's `.spark/`, NFR-2) and a hard determinism bar (NFR-5, byte-identical re-render).

- **Decision:** New `render.py` module, mirroring the `query.py`/`build.py` "logic in a module,
  thin CLI adapter" house shape (one adapter — there is no MCP-equivalent surface for render).
  Two public functions: a **pure** `render_html(snapshot: dict) -> str` (dict→HTML, zero IO, no
  clock, no randomness — the NFR-5 determinism substrate and the unit-test seam for every content
  AC) and an orchestrator `run_render(location: str) -> Path` that resolves/validates the latest
  snapshot **via the exact `query` path** (so US-2's errors come by reuse, not reinvention),
  calls `render_html`, writes `<location>/.aspark-insights/report.html` (fixed path, `STORE_DIRNAME`,
  overwrite), and returns the **resolved absolute** path. `_cmd_render` wires `--repo`/`--output`
  → `run_render` and prints `canonical_json({"report": str(path)})`. HTML is built from **stdlib
  hand-rolled string templates with `html.escape` at a single choke-point** — every dynamic value
  from facts/metrics/provenance flows through one `_esc()` helper; no snapshot data is ever
  f-string-interpolated raw. Styling is one embedded `<style>` block, no external refs (AC-1.5).

- **Alternatives considered:**
  | Alternative | Why rejected |
  |---|---|
  | **Jinja2** (or any templating engine) for autoescaping | A new runtime dep (+MarkupSafe transitive) — a supply-chain/size liability the `library` lens flags — bought for a **fixed single-page layout** with no inheritance, macros or user templates. Autoescape's safety is matched by funnelling every value through one stdlib `html.escape` choke-point, and that choke-point is *test-provable* (AC-4.1 plants `<script>`). "We write those ~60 lines ourselves" wins; the dep doesn't earn its keep. |
  | Raw f-string interpolation of snapshot values (no central helper) | The exact "easy to miss a spot" trap the `security` lens warns of — one forgotten escape is stored XSS. Rejected for a single `_esc()` choke-point that dynamic content structurally cannot bypass, guarded by a hostile-input test. |
  | `xml.etree.ElementTree` / DOM builder (stdlib, auto-escapes text) | No dep, but XML-escapes `<style>`/`<!DOCTYPE>` content and yields awkward, hard-to-diff markup; heavier and less legible than string templates for a fixed layout, and fights the inline-CSS requirement. |
  | Extend `query.py` / put HTML in `cli.py` | Bloats the CLI adapter and couples read-core to a presentation concern; the house pattern is a dedicated module with a minimal public surface (NFR-10). |

- **Consequences:** Easier — zero new dependencies; determinism is structural (pure function, no
  clock/nonce); every content AC is a fast in-process unit test on `render_html`; a future new
  TRC-*/MTA-* metric renders with no render change (nothing is metric-named). Harder — escaping
  correctness now rides on the discipline that *all* dynamic content goes through `_esc()` (bought
  back by the AC-4.1 planted-input test and a code choke-point, not convention); hand-rolled CSS
  must hit WCAG AA contrast without a framework (NFR-4, verified at `/look-and-feel`/`/demo-day`).

## 2. Affected Components

**Blast radius scoped by hand — not by an `impact` query.** Same situation as the
`traceability-metrics`/`mcp-server` precedents: the change is dominated by a *new* file
(`render.py`) no graph indexes yet, and the only pre-indexed edited source file is `cli.py`,
whose downstream is confined to this package's own CLI dispatch. A confirming call is named
below; it will not change scope.

- **New:** `src/aspark_insights/render.py` (`render_html` pure generator + `run_render`
  orchestrator + private `_esc`/table/section helpers); `tests/test_render.py` (all content ACs
  on `render_html`; end-to-end `run_render`/CLI on `built_repo`).
- **Edited:** `src/aspark_insights/cli.py` (`_cmd_render` real body; `sub.add_parser("render", …)`
  gains `--repo`/`--output` + real `--help` text, replacing "not yet implemented");
  `tests/test_cli_stubs.py` (the `test_render_exits_1_with_named_not_implemented_error` test
  asserts behavior being **removed** — rewrite/relocate it).
- **No new dependency, no new service, no new pattern.** Reuses `store` (lookup/validation),
  `errors` (`no_snapshot`/`snapshot_unreadable` already exist — no new error class),
  `serialization.canonical_json` (stdout confirmation), and `html.escape` (stdlib). `GraphPort`
  untouched. `README.md` may gain a one-line `render` mention (not load-bearing; omitted from
  task `files:` notes until confirmed).
- **Available confirming call (optional):**
  `aspark-graph query impact src/aspark_insights/cli.py --repo .`

## 3. Task Breakdown

<!-- Escaping (US-4) is baked into every task from T3 on via the single `_esc()` choke-point
     introduced with the first dynamic content; T7 is its dedicated hostile-input + determinism
     proof. Design-review findings 4/5/6 and both accessibility notes are applied inside the
     tasks named below, per §8's routing, and their DoDs say so explicitly. -->

| # | Task | Story | Covers (AC / NFR) | Depends on | Status | Definition of Done |
|---|---|---|---|---|---|---|
| T1 | Walking skeleton: `render` boots, reads the snapshot, writes a structurally-correct self-contained `report.html` | US-1 | AC-1.1, AC-1.5, NFR-9, NFR-10 | – | `done` | New `render.py` exposes `render_html(snapshot: dict) -> str` (pure, no IO/clock/random) and `run_render(location: str) -> Path`; `run_render` resolves the latest snapshot the exact way `query` does (`latest_snapshot_path`→`read_snapshot_dict`→`require_snapshot_shape`), calls `render_html`, writes `<location>/.aspark-insights/report.html` (via `STORE_DIRNAME`, overwriting), returns the **resolved absolute** path. `render` subparser gains `--repo` (default `.`) + `--output` (default `None`→repo) with real `--help` text; `_cmd_render` calls `run_render(args.output or args.repo)` and prints `canonical_json({"report": str(path)})` on stdout, exit 0. Skeleton HTML has `<!DOCTYPE html>`, one `<h1>`, one embedded `<style>`, and **no external font/CDN/script/image ref** (asserted by a test scanning for `http`/`src=`/`link rel`). Public surface is exactly `render_html`+`run_render` (helpers `_`-prefixed). The old stub test in `test_cli_stubs.py` is removed/rewritten — files: src/aspark_insights/render.py, src/aspark_insights/cli.py, tests/test_render.py, tests/test_cli_stubs.py |
| T2 | No snapshot / unreadable → reuse `query`'s named errors | US-2 | AC-2.1, AC-2.2, NFR-3 | T1 | `done` | Because `run_render` reuses the `query` lookup+validation path and `main`'s `except InsightsError` wraps it, `render` on a repo with no `.aspark-insights/snapshots/` (or empty) exits 1, prints **nothing to stdout**, and emits `canonical_json` with `"error": "no_snapshot"` on stderr; a present-but-corrupt / wrong-shape snapshot (bad JSON, or valid JSON missing `facts`/`metrics`/`provenance`) exits 1 with `"error": "snapshot_unreadable"` — same reason strings as `query`, **no new vocabulary**, never a traceback. Tests mirror `test_cli_stubs.py`'s existing `query` no-snapshot/corrupt/wrong-shape cases against `render` — files: src/aspark_insights/render.py, tests/test_render.py |
| T3 | The two data tables: canonical sort, nothing dropped, semantic markup + `_esc` choke-point | US-1 | AC-1.2, NFR-4, NFR-5, NFR-7 | T1 | `done` | `render_html` emits a `<table>` of every `facts` entry (subject_kind, subject_id, predicate, value) sorted ascending by `(subject_kind, subject_id, predicate)`, and a `<table>` of every `metrics` entry (metric_id, metric_version, value, reason, n) sorted ascending by `(metric_id, metric_version)` — every snapshot row appears, none dropped/paginated/truncated; a test with a multi-row unsorted input asserts rendered row order is the canonical sort, not input order. Each table uses `<th scope="col">` and a `<caption>` (or `aria-labelledby`) tying it to its heading (§8 accessibility note). The single `_esc()` = `html.escape(str(v), quote=True)` choke-point is introduced here and **all** cell content flows through it — files: src/aspark_insights/render.py, tests/test_render.py |
| T4 | Provenance verbatim, fixed section order, stale cue in two places, heading hierarchy | US-1 | AC-1.3, AC-1.4, AC-1.6, NFR-4 | T3 | `done` | Page renders provenance verbatim (`as_of`, `insights_version`, `metric_registry_version`, `graph_source` access/sealed, `scope_filter` patterns/excluded_count, `graph_staleness`) — never summarized. Sections appear in fixed byte order: (1) `<h1>`+summary+top stale cue → (2) provenance → (3) metrics → (4) facts, each behind an `<h2>` (Provenance/Metrics/Facts, §8 accessibility note); a test asserts the section headings' byte offsets are strictly increasing. When `graph_staleness.stale == true`, a **textual** (non-color-only) stale cue appears **both** near the top (after `<h1>`/summary, before provenance) **and** in the provenance section; a test with `stale: true` asserts two distinct textual cues, and `stale: false` asserts none — files: src/aspark_insights/render.py, tests/test_render.py |
| T5 | Honest values: `n` beside value, null shows a distinctly-shaped reason, real empty-state notice | US-3 | AC-3.1, AC-3.2, AC-3.3, NFR-7 | T3 | `done` | A non-null metric renders value **with** its `n` (e.g. `62% (n=8)`); a `value: null` row renders its `reason` with a fixed, non-color-only marker giving it a different **shape** from a value (§8 finding 4 — e.g. italic `Not computed: <reason>`), never a blank cell/bare dash/placeholder. Against the project's dogfood `built_repo` fixture (zero facts, every metric null+reason — built via the existing `build_snapshot`/`write_snapshot` fixture pattern, no new fixture invented) every metric row shows its real reason and the facts table shows an explicit **styled notice block** (not bare inline text) explaining a zero-facts report (§8 finding 6 — treated as the primary first-run state, not an afterthought) — files: src/aspark_insights/render.py, tests/test_render.py |
| T6 | At-a-glance summary as distinct figures under `<h1>` | US-5 | AC-5.1, AC-5.2 | T3 | `done` | Directly under `<h1>`, a summary presents facts count, metrics total, and metrics-null count as **visually distinct figures** (a label:value list, not one dense sentence — §8 finding 5; AC-5.1's example string treated as illustrative); a test asserts the summary's fact/metric/null counts exactly match the number of rows `render_html` produced in the tables below (AC-5.2) — files: src/aspark_insights/render.py, tests/test_render.py |
| T7 | XSS hardening + byte-identical determinism | US-4 | AC-4.1, AC-4.2, NFR-2, NFR-5 | T3, T4, T5, T6 | `done` | A snapshot carrying HTML-significant chars (`<`, `>`, `&`, `"`) in `subject_id` and in a metric `reason`/provenance string renders with those chars escaped — the literal `<script>` never appears unescaped anywhere in the output, wherever in the snapshot it originated (AC-4.1) — and the render still completes end-to-end at exit 0, never a hard error (AC-4.2); a coverage-style test confirms every string field path (facts/metrics/provenance) passes through `_esc`. A determinism test renders the same on-disk snapshot twice and asserts **byte-identical** output (no wall-clock, no random id/nonce), reusing the canonical sort from AC-1.2 — files: src/aspark_insights/render.py, tests/test_render.py |

## 4. Test Strategy

- **US-1 (render the snapshot):** unit tests on the pure `render_html(dict)` for the single
  `<h1>`, both tables and every row present (T1/T3), canonical sort order (T3), verbatim
  provenance, fixed section byte-order and the two-place stale cue (T4). End-to-end: `run_render`
  and the real `insights render` subprocess against `built_repo` write `report.html` to the fixed
  absolute path and print `{"report": …}` at exit 0 (T1). Self-containment (AC-1.5) is a string
  scan for external refs (T1). *Deliberately `/demo-day`*: NFR-1 sub-5s timing, NFR-4 WCAG-AA
  contrast, NFR-7 375px no-horizontal-scroll, and real offline browser rendering — visual/rendered
  properties a source read can't prove; per this project's own house technique, render the HTML
  and inspect it in a browser (and, if useful, via GitHub's markdown API precedent) at QA.
- **US-2 (named errors):** subprocess tests mirroring the existing `query` no-snapshot / corrupt /
  wrong-shape cases in `test_cli_stubs.py` — exit 1, empty stdout, correct `reason`, no traceback
  (T2). No graph fixture needed for these; render never reaches the graph.
- **US-3 (honest values / empty state):** unit tests on `render_html` for `n`-beside-value, the
  distinctly-shaped null reason, and the styled zero-facts notice, driven by the real all-null
  dogfood fixture built with `build_snapshot`/`write_snapshot` — the actual first-run screen (T5).
- **US-4 (no injection):** a targeted hostile-input test embedding `<script>` in a `subject_id`
  and a provenance string, asserting the raw tag never appears unescaped and render still exits 0
  (T7). This is the `security` lens's proof that the `_esc` choke-point holds.
- **US-5 (summary):** unit test asserting summary counts equal rendered table row counts (T6).
- **Determinism (NFR-5):** a byte-identical double-render test alongside the existing determinism
  canary (T7).
- **No graph-integration test for render** — render reads only an on-disk snapshot; the sibling
  `aspark-graph` is used solely (unmocked) to *build* fixtures, matching the constitution.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| A dynamic value bypasses `_esc` (raw f-string), reintroducing stored XSS | AC-4.1/NFR-2 regress silently — one repo's `.spark/` content injects markup into another's report | Single `_esc()` choke-point all cell content must flow through (code review-visible); T7 plants `<script>` in `subject_id` and provenance and a coverage test asserts every string path is escaped |
| Hand-rolled CSS misses WCAG-AA contrast or the stale/null cues rely on color | NFR-4 accessibility fails; a colorblind reader misses the staleness caveat (AC-1.4) or misreads a null as a value | Non-color textual cues required by AC-1.4/finding 4 are tested structurally (T4/T5); contrast is verified visually at `/look-and-feel`/`/demo-day` against the stated 4.5:1/3:1 figures |
| A hidden non-determinism (dict iteration, a stray timestamp) breaks byte-identical re-render | NFR-5 fails; a `verify`-style trust guarantee erodes | `render_html` is pure with no clock/random; canonical sort (AC-1.2) fixes row order; T7's double-render byte-compare is the canary |
| AC-1.1 requires an **absolute** path but `_cmd_verify` echoes a relative `str(path)` — copying that idiom would ship the wrong form | Confirmation JSON prints a relative path; AC-1.1 fails | T1 DoD fixes the printed value as the **resolved** absolute path (`str(path.resolve())`), a deliberate, tested divergence from verify's relative echo |
| The dogfood empty state (zero facts / all-null) reads as "the tool is broken" | Undermines the product's central trust guarantee (an honest null *is* the product) | Finding 6 applied in T5 as a **styled notice block** explaining a zero-facts report, tested against the real all-null fixture — treated as the primary first-run screen, not an edge case |
| Sort keys assumed to be plain strings but a model field isn't | Sort raises or is non-deterministic, breaking AC-1.2/NFR-5 | Confirmed against source: `SubjectKind` serializes via `.value` (a str) and `subject_id`/`predicate`/`metric_id`/`metric_version` are plain `str` on `model/fact.py`/`model/value.py`; sort operates on the serialized dict's string fields |

## Deviations

- **Added a `<meta name="viewport">` tag and per-table `.table-wrap` (`overflow-x: auto`)
  scroll containers, not named in any task's DoD.** Caught by actually rendering the page
  in a browser at 375px width (NFR-7's own verification method) rather than trusting the
  CSS alone: without the viewport meta tag, a mobile/narrow browser renders the page at a
  fixed ~980px virtual viewport regardless of the real device width, so `innerWidth` never
  became `375` and the "no horizontal scroll at 375px" requirement was untestable, let
  alone met. Fixed in `render.py` (`render_html`'s `<head>`, and each of the metrics/facts/
  provenance table renderers), with a new regression test
  (`test_render_html_has_viewport_meta_so_mobile_width_actually_applies`) and confirmed
  live: page-level `scrollWidth == clientWidth == 375` after the fix, with each `.table-wrap`
  scrolling internally instead. Small, obvious, within-scope correction — no architecture,
  story or AC change.

---

## ✅ PLAN GATE

*All boxes checked → `/increment` may start. Any box open → back to `/sprint-plan`.*

- [x] Spec status is `approved` (never plan against a draft)
- [x] Architecture decision includes rejected alternatives (a decision without alternatives is a guess)
- [x] Architecture respects the constitution's technical constraints (named-error taxonomy + `canonical_json` reused; no new error class; `GraphPort` untouched — render reaches no graph; no ambient clock/random in `render_html`; `--output` from day one; sibling `aspark-graph` never mocked — used only to build fixtures; no new runtime dependency)
- [x] Every task maps to a user story — no orphan tasks, no story without tasks
- [x] Every Must AC and every applicable NFR is covered by at least one task
- [x] Every task has a checkable definition of done
- [x] Task order respects dependencies
- [x] Test strategy covers every Must story
- [x] Status set to `approved` by the user
