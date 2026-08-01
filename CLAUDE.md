# aspark-insights — project conventions

Patterns and process nudges kept from the `foundation` (I1) cycle. Read
`.spark/foundation/release.md` §6 for the full story behind each of these.

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
  "never touch git config" rule — avoidable with an earlier heads-up.

- **Never mock the sibling `aspark-graph` dependency in integration tests.**
  The decision to require a real, pinned, installed sibling repo for
  `tests/test_graph_integration.py` (rather than a fake) is exactly what let
  QA later surface a real malformed-`graph.json` traceback bug — a mock
  would have hidden it. Keep this precedent for any future family-repo
  integration.
