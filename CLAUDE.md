# aspark-insights — project conventions

Patterns and process nudges kept from the `foundation` (I1),
`traceability-metrics` (I2), `public-repo-polish`, and `mcp-server` (I7)
cycles. Read `.spark/foundation/release.md` §6,
`.spark/traceability-metrics/release.md` §6,
`.spark/public-repo-polish/release.md` §6, and `.spark/mcp-server/release.md`
§6 for the full story behind each.

## Code patterns

- **Named-error taxonomy + one canonical serializer.** Every CLI failure raises
  an `InsightsError` subclass carrying a machine-readable `reason`
  (`errors.py`); every stdout/stderr JSON payload goes through
  `canonical_json()` (`serialization.py`, `sort_keys=True`, stable). This pair
  is what makes "never a raw traceback, always sort_keys JSON" both
  enforceable and cheaply testable — keep using it for every new subcommand
  and every new error case, rather than ad hoc `print()`/`raise`.

- **Any CLI that reads from `--repo X` and also writes derived state should
  ship a separate `--output` flag from day one**, and document the
  write-location behavior directly in `--help` text — not just in a code
  comment. Defaulting to writing under `--repo` (mirroring how
  `aspark-graph` keeps `.aspark-graph/` inside the analyzed repo) is fine,
  but it must be an explicit, escapable, documented default, never a silent
  side effect a first-time user discovers by accident.

- **When closing a validation gap, check whether every caller of the affected
  code path actually wants the same strictness before centralizing the fix.**
  `require_snapshot_shape()` was deliberately kept as its own function rather
  than folded into `read_snapshot_dict()`, because `diff`'s `.get()`-based
  tolerance for partial/malformed input was a deliberate, different behavior
  from `query`/`verify`'s need to fail loudly. Don't over-generalize a fix
  onto callers that never asked for it.

- **A metric with more than one denominator ships as multiple immutable
  registry entries, never as one dict-valued `MetricValue.value`.** TRC-004
  (orphan-tasks vs. unverified-acs) and TRC-005 (declared/extracted/inferred
  shares) both hit this: `MetricValue.value` is deliberately a scalar
  (`float | int | None`), so a metric that's really "N related numbers" ships
  as N separately versioned `(id, version)` entries — e.g. `TRC-005-declared`,
  `TRC-005-extracted`, `TRC-005-inferred` — each with its own `n`. Keep this as
  the house style rather than re-litigating the shape per future multi-part
  metric.

- **When a second surface (MCP tool, future HTTP endpoint, …) needs to expose
  logic the CLI already has, factor a shared core function first and wire two
  thin adapters to it — never duplicate the logic or reimplement the read
  path.** `mcp-server` (I7) did this with `query.py:run_query()`: both
  `cli._cmd_query` and the MCP `query` tool call the same function, so
  CLI↔MCP parity became a structural property (provable by one regression
  test — `test_cli_query_stdout_is_byte_unchanged_after_the_run_query_refactor`)
  rather than something that has to be manually re-checked every time either
  surface changes. Keep this as the default design move for any future
  second adapter, rather than re-deriving parity by hand each time.

- **Prefer disclosing a new risk through an existing provenance field over
  inventing a bespoke new one.** The A3 risk (this family's current
  `review.md`/`qa.md` filenames aren't recognized by the installed
  `aspark-graph`'s artifact parser, which expects legacy names) is disclosed
  via the existing `graph_source`/staleness provenance rather than a new
  "parser coverage" flag — one more application of "don't recompute what the
  graph already answers," extended to disclosure, not just computation.

## Process nudges for future increments

- **Apply a hostile-input checklist at `/increment` time for any CLI argument
  that becomes part of a file path or gets parsed into another system's
  data structure.** At minimum: empty string, path-traversal sequences
  (`../`), an absolute path, a wrong-but-valid-JSON shape (list/string/null/
  number instead of the expected dict), and a dict missing expected keys.
  In `foundation`, an unvalidated `--as-of` turned out to be a real
  path-traversal/arbitrary-write vulnerability (found by QA, not by the
  original task DoDs) — cheaper to check for this class of bug during
  `/increment` than to find it during `/demo-day`.

- **Git identity is now configured** (`git config --global user.name`/
  `user.email`, set during `public-repo-polish`'s `/go-live`, with the user's
  explicit authorization) — this took two full release cycles of being
  flagged in a report before it was actually fixed. The lesson: a repeated
  note in a release report doesn't self-enforce; when something is flagged
  twice with no remediation, ask the question directly in the moment rather
  than writing it down a third time.

- **Never mock the sibling `aspark-graph` dependency in integration tests.**
  The decision to require a real, pinned, installed sibling repo for
  `tests/test_graph_integration.py` (rather than a fake) is exactly what let
  QA later surface a real malformed-`graph.json` traceback bug — a mock
  would have hidden it. Keep this precedent for any future family-repo
  integration.

- **When a plan names a specific external repo as a dogfood/integration
  target, verify that target is actually in the state the plan assumes
  (e.g. "has a built graph") at the *start* of the phase that depends on
  it — not as a reactive discovery mid-`/demo-day`.** I2's spec assumption
  A1 claimed both `aspark-graph` and `aspark-policy` had (or would trivially
  get) a built graph; in practice `aspark-policy`'s never built at all,
  and QA only found out by trying. The underlying cause (a real
  `TemplateDriftError` in that repo's own `.spark/format-json-schema/spec.md`
  — a heading shaped `### US-6 — dropped (...)`  the graph parser can't
  read) is out of scope to fix here, but the earlier the assumption is
  checked, the cheaper the surprise.

- **For any documentation-heavy feature (a README rewrite, family-facing
  docs), render the Markdown through GitHub's real `/markdown` API
  (`gh api /markdown`, `mode=gfm`) and inspect the resulting HTML in a
  browser before `/go-live`**, rather than trusting the raw source read.
  `public-repo-polish`'s QA pass did this and caught things a source read
  never would have proven (real checkbox rendering, real link resolution,
  real table formatting) — the first genuine visual-surface QA in this
  project. Keep this as the house technique for any future docs feature.

- **A version bump is a claim about package behavior, not a ceremony
  checkbox.** `public-repo-polish` was documentation/config-only (README,
  LICENSE, `.gitignore`) with zero `src/`/`tests/` change — it shipped with
  **no version bump**, deliberately, so "the version changed" keeps meaning
  "the package's behavior changed" for every future release. Don't bump a
  version by default just because a `/go-live` happened.

- **When a family of sibling repos shares a README convention (section
  order, status framing, family-position table), treat matching it as a
  checked acceptance criterion**, not an afterthought — `public-repo-polish`
  scoped this explicitly (US-5) rather than leaving family consistency to
  chance. Keep this precedent for any future family-repo public-facing doc.
