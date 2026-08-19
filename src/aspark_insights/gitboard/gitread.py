"""gitread — the one subprocess seam to `git`, fixed argument vectors only.

Every call uses `git -C <repo_root> ...` (never `cwd=`, never a shell string
built from repo content — NFR-2, the same discipline `CLIGraphPort` already
established for the sibling graph tool's subprocess boundary). `git`'s own
repo-detection (`rev-parse --git-dir`) is the sole authority for "is this a
git repo" — hand-parsing `--repo` first would just race git's own logic with
a second, weaker one.

No call here ever asks git for an identity field (`%an`/`%ae`/`%cn`/`%ce`/
`%b`/trailers) — NFR-3 holds at the source, not just at the render layer.
"""

from __future__ import annotations

import subprocess

from aspark_insights.errors import GitUnavailableError, NotAGitRepoError

_TIMEOUT_SECONDS = 10
_FIELD_SEP = "\x1f"

# Two divergent git quirks for the same underlying cause — a commit whose
# committer timestamp can't be parsed (QA B1/B2/B3, demo-day 2026-08-19):
# `log --format=%cI` leaves the placeholder literal, unexpanded, instead of
# substituting anything; `for-each-ref`'s `%(committerdate:iso-strict)`
# instead silently substitutes the Unix epoch. Both are non-empty, truthy
# strings that would otherwise slip past a plain `if raw:`/`is None` check.
_UNEXPANDED_DATE_TOKEN = "%cI"
_EPOCH_ISO_STRICT = "1970-01-01T00:00:00+00:00"


class GitCommandFailed(Exception):
    """Internal only: a nonzero git exit. Never escapes this module — each
    call site reclassifies it into what a failure means *there* (a missing
    repo, an absent tag, an unreadable date), and `board.build_board()` is
    the final safety net for any call site that doesn't."""

    def __init__(self, stderr: str) -> None:
        super().__init__(stderr)
        self.stderr = stderr


def _run(repo_root: str, *args: str) -> str:
    """`git -C <repo_root> <args>`, fixed vector, never a shell string.
    Returns stripped stdout on exit 0. `git` being absent or unresponsive is
    unambiguous regardless of call site, so it raises `GitUnavailableError`
    directly; any other nonzero exit raises `GitCommandFailed` for the
    caller to reclassify."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True, text=True, timeout=_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise GitUnavailableError("git is not installed or not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitUnavailableError(f"git did not respond within {_TIMEOUT_SECONDS}s") from exc
    if result.returncode != 0:
        raise GitCommandFailed(result.stderr.strip())
    return result.stdout.strip("\n")


def ensure_git_repo(repo_root: str) -> None:
    """Raises `NotAGitRepoError` unless `repo_root` is a real git working
    tree or bare repo. The only place `--repo`'s validity is decided — every
    later call in this module assumes it already passed. An empty string is
    rejected before any subprocess call: `-C ""` is not well-defined across
    platforms, so it is never handed to git at all."""
    if not repo_root:
        raise NotAGitRepoError("--repo must not be empty")
    try:
        _run(repo_root, "rev-parse", "--git-dir")
    except GitCommandFailed as exc:
        raise NotAGitRepoError(f"{repo_root!r} is not a git repository: {exc.stderr}") from exc


def is_shallow(repo_root: str) -> bool:
    return _run(repo_root, "rev-parse", "--is-shallow-repository") == "true"


def resolve_tag(repo_root: str) -> str | None:
    """The nearest tag reachable from HEAD by commit topology (`git describe`
    semantics — spec A3). `None` when the repo has no tags at all: this is
    not a failure, it is the honest input to AC-1.2's null."""
    try:
        return _run(repo_root, "describe", "--tags", "--abbrev=0")
    except GitCommandFailed:
        return None


def tag_commit_date(repo_root: str, tag: str) -> str | None:
    """The tag's own commit date, ISO-8601. `None` if it cannot be read —
    AC-1.10(b)'s degradation, distinct from AC-1.10(a)'s no-tag-at-all case.
    A commit with an unparseable committer timestamp makes git itself leave
    `%cI` unexpanded (B1) — that literal token is `None`-worthy too, not a
    real date `datetime.fromisoformat` could ever parse."""
    try:
        raw = _run(repo_root, "log", "-1", "--format=%cI", tag)
    except GitCommandFailed:
        return None
    return None if raw == _UNEXPANDED_DATE_TOKEN else raw


def count_commits_since(repo_root: str, tag: str) -> int:
    """The exact count (AC-1.1) — never truncated, unlike the shown list."""
    return int(_run(repo_root, "rev-list", "--count", f"{tag}..HEAD"))


def _parse_records(raw: str, field_names: tuple[str, ...]) -> list[dict]:
    """Splits each line into exactly `len(field_names)` fields. The first and
    last fields are peeled off with a single split each — a git hash/ref name
    and an ISO-strict date can never themselves contain `\\x1f` — so any
    field_names[1:-1] value keeps any embedded `\\x1f` byte a hostile or
    unusual commit subject might carry, rather than misaligning every field
    after it."""
    if not raw:
        return []
    records = []
    for line in raw.split("\n"):
        first, rest = line.split(_FIELD_SEP, 1)
        middle, last = rest.rsplit(_FIELD_SEP, 1)
        records.append(dict(zip(field_names, (first, middle, last))))
    return records


def list_commit_subjects_since(repo_root: str, tag: str) -> list[str]:
    """Every commit subject since `tag` — unbounded, for `worktype.breakdown`
    (AC-1.12), which must classify the *whole* population, not just the
    NFR-4-bounded display list, or the 20% threshold would be computed over
    a biased sample on any repo with more than 50 commits since its tag."""
    out = _run(repo_root, "log", f"{tag}..HEAD", "--format=%s")
    return out.split("\n") if out else []


def list_commits_since(repo_root: str, tag: str, max_count: int) -> list[dict]:
    """Hash, subject (first line only — `%s` already stops there) and commit
    date, bounded to `max_count` (NFR-4). No identity field is ever asked of
    git (NFR-3). A commit's own unparseable committer timestamp hits the same
    unexpanded-`%cI` quirk `tag_commit_date` guards against (B3) — this field
    has no null state of its own to degrade into (no AC governs it), so the
    leaked literal git syntax is replaced with a plain, honest sentence
    instead of being carried through as if it were a real date."""
    fmt = f"%h{_FIELD_SEP}%s{_FIELD_SEP}%cI"
    out = _run(repo_root, "log", f"{tag}..HEAD", f"--format={fmt}", f"--max-count={max_count}")
    records = _parse_records(out, ("hash", "subject", "date"))
    for r in records:
        if r["date"] == _UNEXPANDED_DATE_TOKEN:
            r["date"] = "date could not be read"
    return records


def list_branches(repo_root: str) -> list[dict]:
    """Local `refs/heads/*` only (spec C4) — tip hash and tip date, no
    identity field. A tip whose committer timestamp is unparseable makes
    `for-each-ref` silently substitute the Unix epoch rather than emitting
    empty output (B2) — indistinguishable from a genuine epoch date at this
    level, but no real commit predates git's own 2005 creation, so it is
    normalized to `""` here, which `board._build_branches`'s existing
    `if b["tip_date"]:` check already treats as unreadable (AC-3.3)."""
    fmt = f"%(refname:short){_FIELD_SEP}%(objectname:short){_FIELD_SEP}%(committerdate:iso-strict)"
    out = _run(repo_root, "for-each-ref", f"--format={fmt}", "refs/heads/")
    records = _parse_records(out, ("name", "tip_hash", "tip_date"))
    for r in records:
        if r["tip_date"] == _EPOCH_ISO_STRICT:
            r["tip_date"] = ""
    return records
