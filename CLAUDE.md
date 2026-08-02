# aspark-insights — project conventions

Patterns and process nudges kept from the `foundation` (I1) and
`traceability-metrics` (I2) cycles. Read `.spark/foundation/release.md` §6 and
`.spark/traceability-metrics/release.md` §6 for the full story behind each.

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

- **For a from-scratch, not-yet-`git init`-ed repo, confirm the local git
  commit identity (`user.name`/`user.email`) is configured *before* the
  first `/go-live` pass**, not at the release ceremony itself. This project's
  first commit had to work around a completely unconfigured identity via
  env-var-scoped `GIT_AUTHOR_*`/`GIT_COMMITTER_*` variables, per the standing
  "never touch git config" rule — avoidable with an earlier heads-up. **Still
  unconfigured as of the I2 release** (the second cycle running) despite this
  same nudge — writing it down once isn't self-enforcing; treat it as a real
  action item, not a note to re-read.

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
