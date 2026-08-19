# Review Report: release-board

| | |
|---|---|
| **Phase** | Review |
| **Owner** | Reviewer (`/peer-review`) |
| **Input** | The uncommitted working-tree diff of `/increment` (on top of `4743b41`), `.spark/release-board/plan.md` |
| **Status** | `passed` |
| **Date** | 2026-08-19 (re-reviewed 2026-08-19) |

**Handoff**
- **Status:** `passed` — F1/F2/F3 fixes independently re-verified adversarially; gate closed.
- **Verdict:** Passes. All three fixes hold under my own fresh hostile inputs (not the developer's fixtures) — see §3. Full suite 443 passed, re-run this session. No new issue introduced by the fixes; `InvalidAsOfError`/`NotAGitRepoError` still propagate unwrapped from before the new try block.
- **Open:** `0 open` blocking. Nit `F4` (no `--version`, pre-existing) and open item `F5` (version 0.8.0 ahead of newest tag — `/go-live` must create the tags) remain, both non-blocking, for the user/EM to route.
- **Binding ruling:** §3 Findings + §4 Traceability + REVIEW GATE below.
- **On conflict:** the numbered body below wins for everything except `Status`; log the mismatch as a finding at the next `/peer-review` and proceed.

## 1. Scope

Reviewed the entire release-board increment: new `gitboard/releasemap.py`, `gitboard/artifactstatus.py`, `gitread.py` additions (`list_tags_topo_order`, `list_commits_in_range`, `commits_touching_path`), the `releases` CLI subcommand, version bump 0.7.0→0.8.0 (`__init__.py`/`pyproject.toml`/`uv.lock`), README "Release board" section, and all nine new test modules. Read the full `gitread.py`/`cli.py` diffs to confirm nothing existing was disturbed (only additive). Ran the whole suite (437 passed, 5m39s). Independently re-derived the `v0.2.0..v0.3.0` three-member fact and the A9 trailing-docs pattern from real `git log`; built my own adversarial symlink/traversal `.spark/` fixture for NFR-2; probed the embedded-pipe artifact case and the `_MAX_LINES_SCANNED` bound; reproduced the raw-traceback edge (F1). **Not reviewed / noted:** untracked `.spark/git-native-mid-cycle-board/release.md` is the previous cycle's prepared-but-unpushed release report — not this increment's diff; left as-is, flagged so it isn't a surprise. The `aspark-graph` graph was stale this session (treated absent per its own rule); this feature imports no graph anyway, so no graph result was used as evidence.

## 2. Plan Conformance

| Task | Implemented as planned? | Note |
|---|---|---|
| T1 | ✅ | `list_tags_topo_order` orders by `rev-list --topo-order --reverse HEAD` position; skeleton + zero-tags + hostile-`--repo` as specified. |
| T2 | ✅ | `_list_feature_dirs` validates `/`, `..`, leading `-`, resolves under `.spark/`. Independently re-verified (my own fixture). |
| T3 | ✅ | Path-only membership; A8 three-member + A9 trailing-docs asserted as intended. |
| T4 | ✅ | Pseudo-release copies `build_board()` figure keys verbatim; byte-equality test genuinely asserts per-key equality (not a weaker check). |
| T5 | ✅ | prev/next chain real tags only; pseudo `previous_tag`=latest real tag / `next_tag`=null. (Latent edge on unreachable tags — F3.) |
| T6 | ✅ | First-pipe-table-only parser; `members` cleanly evolved string→`{name,status}` dict — no leftover flat-string assumption in code or tests. |
| T7 | ✅ | Hostile-`--repo` matrix + malicious `.spark/` entry + fixed-vector assertion. |
| T8 | ✅ | Determinism canary, frozen-`v0.3.0` smoke, no-identity scan, version bump, README, `--help` all present. |

## 3. Findings

| # | Severity | Location | Finding | Status |
|---|---|---|---|---|
| F1 | Blocker | `releasemap.py:54,80,85` (via `build_release_map`) | The new read path has no equivalent of `board.py:122-130`'s outer `except (GitCommandFailed, ValueError)` net. `_list_feature_dirs`'s `iterdir()` (OSError) and the unguarded `list_commits_in_range`/`commits_touching_path` git calls raise non-`InsightsError` exceptions that escape `cli.py:155`'s `except InsightsError`. **Reproduced:** `insights releases` against a repo with an unreadable `.spark/` prints a raw `PermissionError` traceback to stderr — violates constitution §6 "never a raw traceback" (the exact class of B2/F1/F5). **Fixed:** `build_release_map` now wraps its full body in `try`/`except (gitread.GitCommandFailed, ValueError) -> GitUnavailableError` (mirroring `board.py`'s own net) and a separate `except OSError -> SparkDirUnreadableError` (new named error, `errors.py`) for filesystem-specific failures — a distinct failure class from a git one, named as such rather than folded in. Reproduced the exact original repro (`os.chmod(.spark, 0o000)`) both at the CLI (`test_unreadable_spark_directory_is_a_named_error_not_a_traceback`) and at the Python level (`test_unreadable_spark_directory_raises_named_error_at_the_python_level`), `tests/test_releasemap_security.py`. **Re-review (independent, adversarial):** confirmed the outer `try` wraps the *entire* body (tags, `_list_feature_dirs`, membership git calls, `_member_entries`); `_validate_as_of`/`ensure_git_repo` are outside it, so `InvalidAsOfError`/`NotAGitRepoError` still propagate as themselves (verified behaviorally). `SparkDirUnreadableError` is a well-formed `InsightsError` subclass (`reason="spark_dir_unreadable"`, inherits `to_dict`). Broke it with two modes the developer never tested: (a) `.spark/` set `0o444` (read, no-execute — `iterdir` lists but `entry.is_dir()` stats → `PermissionError`) → `SparkDirUnreadableError`; (b) a `.spark/<feature>/` *sub*directory set `0o000` *after* commit (so it's a real git member) — `_member_entries`→`read_artifact_status`→`is_file()` re-raises `PermissionError` (EACCES not in `pathlib._ignore_error`), caught by the same net → `SparkDirUnreadableError`. Both a distinct code path from the original `0o000`-on-`.spark/` repro; both held. Both promoted to permanent regression tests post-review: `test_no_execute_spark_directory_is_also_a_named_error`, `test_unreadable_feature_subdirectory_is_also_a_named_error` (`tests/test_releasemap_security.py`) — previously only verified ad-hoc during the review session. | fixed |
| F2 | Minor | `artifactstatus.py:74-75` | A `Status`/`Date` cell whose value contains a literal `\|` is silently truncated at the pipe with `reason: None` (e.g. `` `approved` (see A|B) `` → `` `approved` (see A ``), not verbatim (AC-2.1) and not honest-null. No real artifact currently triggers it; latent. **Fixed:** `_cell_value` now rejoins the raw (unstripped) cells beyond the label match with `\|`, then strips only the final result — the whole value survives exactly, including whitespace immediately around the embedded pipe. New regression test: `test_status_cell_containing_a_literal_pipe_is_rejoined_verbatim_not_truncated`, `tests/test_artifactstatus.py`. **Re-review (independent):** the developer's own test uses a pipe mid-value; I broke it with three placements it didn't cover — pipe at the very *start* of the value (`|x`→`|x`), at the very *end* (`x|`→`x|`), and *two* embedded pipes (`a|b|c`→`a|b|c`), plus an only-pipes value (`||`→`||`). All reconstruct verbatim via `"|".join(raw_cells[2:-1]).strip()`. | fixed |
| F3 | Minor | `releasemap.py:184` | Pseudo-release `previous_tag = releases[-1]["tag"]` is the topo-last enumerated tag, but its membership range/figures come from `build_board`'s `git describe` (nearest *reachable* tag). With an unreachable/non-linear tag these disagree. Doesn't manifest on this linear repo. **Fixed:** `previous_tag`/`next_tag` are now set inside `_pseudo_release` itself, sourced directly from `board["provenance"]["resolved_tag"]` (the exact tag its figures were computed against) — `build_release_map`'s separate topo-ordered-list assignment removed entirely. New regression test forces a deliberate disagreement via a monkeypatched `build_board` and confirms the pseudo-release reflects the injected value, not the topo list: `test_pseudo_release_previous_tag_sourced_from_build_board_not_recomputed`, `tests/test_releasemap_pseudo.py`. **Re-review (independent):** confirmed structurally sound — `previous_tag`/`next_tag` are now set inside `_pseudo_release` from `board["provenance"]["resolved_tag"]`; the old `build_release_map`-level `previous_tag = releases[-1]["tag"]` is gone, and the real-release chaining loop (lines 194-196) runs *before* the pseudo is appended, so it never touches it (no double-assignment). The developer's test calls `_pseudo_release` directly; I went further and drove the *full* `build_release_map` with a monkeypatched `build_board` forcing a real disagreement (injected `resolved_tag="v1.0.0"` while the topo-last real tag is `v2.0.0`): the pseudo's `previous_tag` reflected the injected `v1.0.0` (proving it reads `build_board`'s field, not the topo list), while the real `v2.0.0` release chained independently (`previous=v1.0.0`, `next=None`) — a genuine disagreement, not a value correct either way. | fixed |
| F4 | Nit | `cli.py:_build_parser` | No top-level `--version` (CLI lens §1.2). Pre-existing across all subcommands, not introduced here; noted since this cycle bumps the version. | open |
| F5 | (open item) | `pyproject.toml`, `README.md` | Version is 0.8.0 but the newest git tag is `v0.5.0`: `v0.6.0`/`v0.7.0` (git-native board) and now `v0.8.0` are all untagged/unpushed. Coherent within the working tree's own sequence, but `/go-live` must create three tags — surface it so it isn't a surprise. Not a code defect; for the user/EM to route. | open |

## 4. Requirements Traceability

| Spec ID | Implemented at | Verdict |
|---|---|---|
| AC-1.1 | `releasemap.py:159-186`, `gitread.py:list_tags_topo_order` | ✅ met |
| AC-1.2 | `releasemap.py:_members_and_unattributed`; `test_releasemap_integration` | ✅ met — independently re-derived (mcp-server/public-repo-polish/traceability-metrics) |
| AC-1.3 | `releasemap.py:80-93` (path-only); `test_releasemap_membership` | ✅ met |
| AC-1.4 | `releasemap.py:196` (`reason:"repository has no tags"`) | ✅ met |
| AC-1.5 | `gitread.ensure_git_repo`; `test_releasemap_security` | ✅ met — F1 fixed & re-verified; unreadable `.spark/` (and unreadable feature subdir) now a named error |
| AC-1.6 | no identity field asked of git; `test_no_identity...` | ✅ met |
| AC-1.7 | `canonical_json`; `test_byte_identical_repeat_runs` | ✅ met |
| AC-1.8 | `releasemap.py:124-142`; `test_pseudo...byte_equal` | ✅ met — verbatim reuse, no second derivation |
| AC-1.9 | `releasemap.py:126-127,182` | ✅ met (present-zero vs absent-no-tag) |
| AC-1.10 | `releasemap.py:133` (`"tag": None`) | ✅ met |
| AC-2.1 | `artifactstatus.py:68-82` | ✅ met — F2 fixed & re-verified; embedded pipes (start/end/multiple) rejoined verbatim |
| AC-2.2 | `artifactstatus.py:31-32` | ✅ met |
| AC-2.3 | `artifactstatus.py:36-44` | ✅ met |
| AC-2.4 | `artifactstatus.py:48-65` (first block, 200-line bound enforced) | ✅ met — bound verified: loop is `range(_MAX_LINES_SCANNED)`, never exceeds 200 reads |
| AC-3.1 | `releasemap.py:139-140,194-196` | ✅ met — F3 fixed & re-verified; pseudo's `previous_tag` sourced from `build_board`'s own resolved tag |
| AC-3.2 | no HTML produced | ✅ met |
| NFR-1 (cli) | `cli.py`, `--help` documents flags + no-disk-write | ✅ (—version: F4) |
| NFR-2 (security) | `_list_feature_dirs`, fixed-vector git | ✅ met — independently re-verified with own fixture |
| NFR-3 (library) | zero new deps, in-process `build_board`, additive export | ✅ met |
| NFR-4 (privacy) | no identity/trailer reaches output; tests scan | ✅ met |
| NFR-5 | bounded artifact read (200 lines) | ✅ met |
| NFR-7 | no `now()`, byte-identical | ✅ met |

## 5. What Was Checked

- [x] Correctness: logic matches ACs; A8/A9 real-history facts independently re-derived from `git log`, not taken on trust
- [x] Non-functional: NFR-2 re-verified with a self-built adversarial symlink/traversal fixture; NFR-3/4/7 hold
- [x] Error handling: F1 fixed — `build_release_map` wraps its full body; unreadable `.spark/` (and unreadable feature subdir, and no-execute mode) → `SparkDirUnreadableError`, never a traceback; pre-try errors still propagate unwrapped. Independently re-verified.
- [x] Security: input validated, fixed-vector subprocess, no secret/PII leak (verified behaviorally)
- [x] Tests: exist, meaningful, all 441 pass (re-run this session, 313s); byte-equality test asserts what it claims; F1/F2/F3 regression tests genuinely fail the old behavior
- [x] Readability: clear, well-documented; naming and structure follow house patterns

## 6. Verdict

This passes. The original build earned most of its claims — byte-equal AC-1.8 reuse, independently re-derived A8/A9 facts, an NFR-2 feature-dir validation that survived a from-scratch adversarial fixture, a provable `_MAX_LINES_SCANNED` bound — and the one Blocker plus two Minors it shipped with are now genuinely fixed, verified by me with fresh hostile inputs rather than the developer's own fixtures. F1: `build_release_map` now wraps its full body, and I confirmed the net catches failure modes the developer never tested — a no-execute (`0o444`) `.spark/` and an unreadable `.spark/<feature>/` *sub*directory that reaches the net through a different code path (`_member_entries`→`is_file()` re-raising `PermissionError`) — while `InvalidAsOfError`/`NotAGitRepoError`, which fire before the try, still propagate as themselves. F2: embedded pipes at the start, end, and doubled within a cell all reconstruct verbatim. F3: driving the full `build_release_map` with a monkeypatched `build_board` that forces a real disagreement (injected `v1.0.0` vs. topo-last `v2.0.0`) proved the pseudo-release reads `build_board`'s own resolved tag while the real chain stays independent. Full suite re-run green (443 passed). The two remaining items — no `--version` (F4, pre-existing) and a package version ahead of the newest git tag (F5, for `/go-live` to tag) — are non-blocking and routed to the user/EM. Passed.

---

## ✅ REVIEW GATE

*All boxes checked → `/demo-day` may start. Any box open → back to `/increment`.*

- [x] No open Blocker findings — F1 fixed and independently re-verified adversarially (§3)
- [x] No open Major findings (or explicitly waived by the user, with reason recorded here)
- [x] Every Must AC traces to implementing code; no constitution non-negotiable violated — F1's §6 violation fixed and re-verified with fresh hostile inputs
- [x] All plan deviations documented and accepted — no deviations; all 8 tasks as planned
- [x] Test suite runs green — 443 passed (re-run this session; 4 regression tests for F1/F2/F3 confirmed to fail the old behavior)
- [x] Status set to `passed` — independent `/peer-review` re-review complete; each fix broken-again with inputs the fix-mode developer did not test, all held
