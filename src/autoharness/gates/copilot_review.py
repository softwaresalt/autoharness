"""Deterministic Copilot-review merge gate (task 068.001-T / feature 068-F).

When GitHub Copilot review is enabled for a pull request, this gate deterministically
holds an (admin) merge until (1) Copilot has completed a review for the **current**
``headRefOid`` and (2) all Copilot-authored review threads are resolved -- iterating
across multiple review rounds by construction, because the gate only passes when the
*latest* HEAD has a completed Copilot review with zero open bot threads.

Design constraints (decision + hardened plan, 2026-07-09):

* The classifier :func:`classify` is a **pure** function of the parsed PR review
  state and the enforcement mode -- given the same inputs it always yields the same
  verdict, so behaviour is reproducible and unit-testable without a network call.
* The default GitHub query invokes ``gh api graphql`` as an argv array with
  ``shell=False`` and a bounded timeout. The array is built with a fixed number of
  elements (:func:`build_query_argv`), so an interpolated value (a PR number or a
  ``owner/name`` slug) always lands inside exactly one argv element and can never
  change argv arity or spawn a second command. Values are additionally validated
  against strict patterns before use.
* **Fail-closed inversion vs. the sizing gate.** The sizing gate fails *open*
  (advisory). This gate is the opposite where it matters: when Copilot review **is
  enabled** and the wait/resolution is incomplete or unverifiable, it fails
  **closed** (BLOCK). "Green but unverifiable" must never resolve to "merge".
* A bounded ``--max-wait`` window governs how long the harness waits for an engaged
  reviewer to submit a review for the current HEAD. On expiry the gate emits a
  distinct :attr:`Verdict.REVIEW_TIMEOUT` outcome that is logged and **still blocks**;
  only an audited ``--force`` overrides it.

Boundary: this module depends only on the Python standard library. It must not reach
into install/tune surfaces or other gate modules, so the gate can evolve independently.
"""

from __future__ import annotations

import enum
import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# GraphQL exposes the Copilot reviewer bot login WITHOUT the ``[bot]`` suffix
# (REST uses ``copilot-pull-request-reviewer[bot]``). The gate reads GraphQL, so it
# matches the no-suffix form. Centralised so a login drift is a one-line change.
COPILOT_LOGIN = "copilot-pull-request-reviewer"

# A submitted GitHub review can be in any of these states; PENDING means the review
# has not actually been submitted yet, so it never counts as "completed".
_PENDING_STATE = "PENDING"

# States that represent a genuinely completed, submitted review. A DISMISSED review
# was withdrawn and must NOT satisfy the gate; PENDING was never submitted. Any state
# outside _KNOWN_STATES on a Copilot review is treated as a malformed response and
# fails the gate closed (DETECTION_AMBIGUOUS) rather than being guessed as complete.
_COMPLETED_STATES = frozenset({"APPROVED", "CHANGES_REQUESTED", "COMMENTED"})
_KNOWN_STATES = _COMPLETED_STATES | {_PENDING_STATE, "DISMISSED"}

ENFORCEMENT_MODES = ("auto", "required", "disabled")
DEFAULT_ENFORCEMENT = "auto"

DEFAULT_GH = "gh"

# Bound every external gh call so a hung binary can never wedge the merge gate.
_COMMAND_TIMEOUT_SECONDS = 30

# Strict validation patterns for interpolated values (defence in depth on top of the
# argv-array / shell=False guarantee). A repo is ``owner/name``; a PR is a positive int.
_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")

_GRAPHQL_QUERY = """\
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      headRefOid
      reviewRequests(first:100){ nodes{ requestedReviewer{
        __typename ... on Bot{ login } ... on User{ login } } }
        pageInfo{ hasNextPage } }
      reviews(last:100){ nodes{ author{ login } state commit{ oid } }
        pageInfo{ hasPreviousPage } }
      reviewThreads(first:100){ nodes{ id isResolved
        comments(first:1){ nodes{ author{ login } } } }
        pageInfo{ hasNextPage } }
    }
  }
}"""


class Verdict(enum.Enum):
    """The classified outcome of the Copilot-review gate for one PR at one HEAD."""

    SATISFIED = "SATISFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
    UNRESOLVED_THREADS = "UNRESOLVED_THREADS"
    REVIEW_TIMEOUT = "REVIEW_TIMEOUT"
    DETECTION_AMBIGUOUS = "DETECTION_AMBIGUOUS"
    VERIFY_FAILED = "VERIFY_FAILED"


# The only verdicts that permit a merge. Everything else BLOCKS (fail-closed).
PASS_VERDICTS = frozenset({Verdict.SATISFIED, Verdict.NOT_APPLICABLE})

_VERDICT_MESSAGES = {
    Verdict.SATISFIED: (
        "Copilot review is complete for the current HEAD and all Copilot-authored "
        "threads are resolved. Merge may proceed with respect to this gate."
    ),
    Verdict.NOT_APPLICABLE: (
        "Copilot review is not in play for this PR (no engagement signal and "
        "enforcement is not 'required'). Gate is not-applicable; merge is not held."
    ),
    Verdict.WAITING_FOR_REVIEW: (
        "Copilot review is enabled but has not completed for the current HEAD. "
        "BLOCK: wait for Copilot to submit a review for this HEAD before merging."
    ),
    Verdict.UNRESOLVED_THREADS: (
        "Copilot has completed a review for the current HEAD but one or more "
        "Copilot-authored review threads are unresolved. BLOCK: address and resolve "
        "every Copilot thread (reply + resolve) before merging."
    ),
    Verdict.REVIEW_TIMEOUT: (
        "Copilot review is enabled but did not complete for the current HEAD within "
        "the bounded --max-wait window. BLOCK (timeout never equals silent merge). "
        "Re-run after review completes, or override with an audited --force."
    ),
    Verdict.DETECTION_AMBIGUOUS: (
        "The PR review state could not be interpreted unambiguously (missing HEAD or "
        "malformed GraphQL response). BLOCK (fail-safe) until the state is verifiable."
    ),
    Verdict.VERIFY_FAILED: (
        "Could not verify Copilot-review state (gh missing, API unreachable, or the "
        "query failed) and enablement is unknown. BLOCK (fail-safe)."
    ),
}


# ---------------------------------------------------------------------------
# Parsed review state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReviewRecord:
    """One submitted Copilot review: its state and the commit it reviewed."""

    state: str
    commit_oid: str | None


@dataclass(frozen=True)
class ReviewState:
    """The Copilot-relevant slice of a pull request's review surface."""

    head_ref_oid: str | None
    copilot_requested: bool
    copilot_reviews: tuple[ReviewRecord, ...]
    copilot_unresolved_thread_ids: tuple[str, ...]
    parse_ok: bool = True

    @property
    def copilot_engaged(self) -> bool:
        """True when Copilot is a requested reviewer or has already reviewed."""
        return self.copilot_requested or bool(self.copilot_reviews)

    def completed_for_head(self) -> bool:
        """True when a completed (submitted, non-dismissed) Copilot review targets HEAD."""
        if not self.head_ref_oid:
            return False
        return any(
            r.commit_oid == self.head_ref_oid and r.state in _COMPLETED_STATES
            for r in self.copilot_reviews
        )


def _login(node: Any) -> str | None:
    if isinstance(node, Mapping):
        login = node.get("login")
        if isinstance(login, str):
            return login
    return None


def _connection(container: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    """Return the connection mapping for ``key``, or None if absent/malformed."""
    val = container.get(key)
    return val if isinstance(val, Mapping) else None


def _truncated(conn: Mapping[str, Any], field: str) -> bool:
    """True when a connection's pageInfo reports more pages in ``field``."""
    page_info = conn.get("pageInfo")
    return isinstance(page_info, Mapping) and page_info.get(field) is True


def parse_graphql_response(raw: Mapping[str, Any]) -> ReviewState:
    """Parse a ``gh api graphql`` response into a :class:`ReviewState`.

    Tolerant of the ``{"data": ...}`` envelope but strict about structure: this is a
    fail-closed gate, so any missing HEAD, structurally invalid connection, truncated
    (paginated) connection, or unknown review state yields ``parse_ok=False`` and the
    classifier BLOCKS with DETECTION_AMBIGUOUS rather than guessing SATISFIED /
    NOT_APPLICABLE.
    """

    def _ambiguous() -> ReviewState:
        return ReviewState(None, False, (), (), parse_ok=False)

    data = raw.get("data") if isinstance(raw.get("data"), Mapping) else raw
    repo = data.get("repository") if isinstance(data, Mapping) else None
    pr = repo.get("pullRequest") if isinstance(repo, Mapping) else None
    if not isinstance(pr, Mapping):
        return _ambiguous()

    head = pr.get("headRefOid")
    head = head if isinstance(head, str) and head else None
    if head is None:
        return _ambiguous()

    # reviewRequests — a structurally invalid or truncated connection means we cannot
    # prove Copilot's enablement state, so fail closed rather than assume "not asked".
    req = _connection(pr, "reviewRequests")
    if req is None or _truncated(req, "hasNextPage"):
        return _ambiguous()
    copilot_requested = any(
        _login(node.get("requestedReviewer")) == COPILOT_LOGIN for node in _nodes(req)
    )

    # reviews — must be structurally valid and not truncated; every Copilot review must
    # carry a known state (a missing/unknown state must not be read as "completed").
    rv = _connection(pr, "reviews")
    if rv is None or _truncated(rv, "hasPreviousPage"):
        return _ambiguous()
    reviews: list[ReviewRecord] = []
    for node in _nodes(rv):
        if _login(node.get("author")) != COPILOT_LOGIN:
            continue
        state = node.get("state")
        if not isinstance(state, str) or state not in _KNOWN_STATES:
            return _ambiguous()
        commit = node.get("commit")
        oid = commit.get("oid") if isinstance(commit, Mapping) else None
        reviews.append(
            ReviewRecord(state=state, commit_oid=oid if isinstance(oid, str) else None)
        )

    # reviewThreads — must be structurally valid and not truncated; a truncated thread
    # list could hide an unresolved Copilot thread and yield a false SATISFIED.
    threads = _connection(pr, "reviewThreads")
    if threads is None or _truncated(threads, "hasNextPage"):
        return _ambiguous()
    unresolved: list[str] = []
    for node in _nodes(threads):
        resolved = node.get("isResolved")
        if resolved is True:
            continue
        if resolved is not False:
            # A non-boolean isResolved is a malformed thread; fail closed.
            return _ambiguous()
        comments = node.get("comments")
        comment_nodes = _nodes(comments) if isinstance(comments, Mapping) else []
        first = comment_nodes[0] if comment_nodes else None
        if first is not None and _login(first.get("author")) == COPILOT_LOGIN:
            tid = node.get("id")
            if isinstance(tid, str):
                unresolved.append(tid)

    return ReviewState(
        head_ref_oid=head,
        copilot_requested=copilot_requested,
        copilot_reviews=tuple(reviews),
        copilot_unresolved_thread_ids=tuple(unresolved),
    )


def _nodes(container: Any) -> list[Any]:
    if isinstance(container, Mapping):
        nodes = container.get("nodes")
        if isinstance(nodes, Sequence) and not isinstance(nodes, (str, bytes)):
            return [n for n in nodes if isinstance(n, Mapping)]
    return []


# ---------------------------------------------------------------------------
# Pure classifier
# ---------------------------------------------------------------------------


def classify(
    state: ReviewState | None,
    enforcement: str = DEFAULT_ENFORCEMENT,
    *,
    timed_out: bool = False,
    verify_failed: bool = False,
) -> Verdict:
    """Classify a PR's Copilot-review posture into a :class:`Verdict`. Pure.

    Fail-closed: any enabled-but-incomplete/unverifiable posture BLOCKS. The only
    passing verdicts are :attr:`Verdict.SATISFIED` and :attr:`Verdict.NOT_APPLICABLE`.
    """
    if enforcement not in ENFORCEMENT_MODES:
        raise ValueError(
            f"enforcement must be one of {ENFORCEMENT_MODES}, got {enforcement!r}"
        )

    if enforcement == "disabled":
        return Verdict.NOT_APPLICABLE

    if verify_failed:
        # Unknown enablement + could not verify -> fail safe (BLOCK) in all modes.
        return Verdict.VERIFY_FAILED

    if state is None or not state.parse_ok:
        return Verdict.DETECTION_AMBIGUOUS
    if not state.head_ref_oid:
        return Verdict.DETECTION_AMBIGUOUS

    engaged = enforcement == "required" or state.copilot_engaged
    if not engaged:
        # auto mode, no per-PR engagement signal -> do not wedge waiting for a
        # reviewer that will never come.
        return Verdict.NOT_APPLICABLE

    if not state.completed_for_head():
        return Verdict.REVIEW_TIMEOUT if timed_out else Verdict.WAITING_FOR_REVIEW

    if state.copilot_unresolved_thread_ids:
        return Verdict.UNRESOLVED_THREADS

    return Verdict.SATISFIED


# ---------------------------------------------------------------------------
# Gate result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CopilotReviewResult:
    """The outcome of running the Copilot-review gate against one PR."""

    verdict: Verdict
    enforcement: str
    head_ref_oid: str | None = None
    unresolved_thread_ids: tuple[str, ...] = ()
    rounds: int = 1
    forced: bool = False
    detail: str = ""

    @property
    def message(self) -> str:
        base = _VERDICT_MESSAGES[self.verdict]
        return f"{base} ({self.detail})" if self.detail else base

    @property
    def is_pass(self) -> bool:
        """True when the verdict itself permits merge (ignoring --force)."""
        return self.verdict in PASS_VERDICTS

    @property
    def blocked(self) -> bool:
        """True when the gate holds the merge (unless overridden by --force)."""
        return not self.is_pass and not self.forced

    @property
    def exit_code(self) -> int:
        return 0 if not self.blocked else 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "enforcement": self.enforcement,
            "head_ref_oid": self.head_ref_oid,
            "unresolved_thread_ids": list(self.unresolved_thread_ids),
            "rounds": self.rounds,
            "forced": self.forced,
            "blocked": self.blocked,
            "exit_code": self.exit_code,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Safe GitHub query
# ---------------------------------------------------------------------------


def build_query_argv(pr: int, repo: str, gh_bin: str = DEFAULT_GH) -> list[str]:
    """Build the fixed-arity ``gh api graphql`` argv for a PR review-state query.

    ``pr`` and ``repo`` are each interpolated into exactly one argv element, so a
    hostile value can never change argv arity or spawn a second command. Callers
    should still validate inputs via :func:`_validate_repo` / ``int(pr)``.
    """
    owner, name = repo.split("/", 1)
    return [
        gh_bin,
        "api",
        "graphql",
        "-f",
        f"owner={owner}",
        "-f",
        f"repo={name}",
        "-F",
        f"pr={int(pr)}",
        "-f",
        f"query={_GRAPHQL_QUERY}",
    ]


def _validate_repo(repo: str) -> str:
    if not isinstance(repo, str) or not _REPO_RE.match(repo):
        raise ValueError(
            f"repo must be 'owner/name' with no shell metacharacters, got {repo!r}"
        )
    return repo


def _validate_pr(pr: Any) -> int:
    try:
        value = int(pr)
    except (TypeError, ValueError):
        raise ValueError(f"pr must be a positive integer, got {pr!r}") from None
    if value <= 0:
        raise ValueError(f"pr must be a positive integer, got {pr!r}")
    return value


def query_pr_review_state(
    pr: int,
    repo: str,
    *,
    run_fn: "Callable[..., Any] | None" = None,
    gh_bin: str = DEFAULT_GH,
) -> ReviewState:
    """Query GitHub for a PR's Copilot-review state via ``gh api graphql``.

    Raises on any failure (missing binary, timeout, non-zero exit, unparseable
    output) so the caller can classify it as VERIFY_FAILED (fail-safe).
    """
    pr = _validate_pr(pr)
    repo = _validate_repo(repo)
    argv = build_query_argv(pr, repo, gh_bin=gh_bin)
    run = run_fn or subprocess.run
    proc = run(
        argv,
        capture_output=True,
        text=True,
        shell=False,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    )
    if getattr(proc, "returncode", 1) != 0:
        stderr = (getattr(proc, "stderr", "") or "").strip()
        raise RuntimeError(stderr or f"gh api graphql failed for {repo}#{pr}")
    stdout = getattr(proc, "stdout", "") or ""
    try:
        raw = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"could not parse gh output: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise RuntimeError("gh output was not a JSON object")
    # gh api graphql can exit 0 while returning a top-level GraphQL errors array with
    # only partial data. Passing that to the parser could yield a false SATISFIED, so
    # treat any non-empty errors array as a verification failure (fail-closed BLOCK).
    errors = raw.get("errors")
    if isinstance(errors, Sequence) and not isinstance(errors, (str, bytes)) and errors:
        raise RuntimeError(f"gh api graphql returned errors for {repo}#{pr}: {errors}")
    return parse_graphql_response(raw)


# ---------------------------------------------------------------------------
# Bounded poll loop
# ---------------------------------------------------------------------------


def evaluate(
    pr: int,
    repo: str,
    *,
    enforcement: str = DEFAULT_ENFORCEMENT,
    max_wait: float = 0.0,
    poll_interval: float = 15.0,
    query_fn: "Callable[[], ReviewState] | None" = None,
    run_fn: "Callable[..., Any] | None" = None,
    gh_bin: str = DEFAULT_GH,
    sleep_fn: "Callable[[float], None] | None" = None,
    clock_fn: "Callable[[], float] | None" = None,
    forced: bool = False,
) -> CopilotReviewResult:
    """Evaluate the gate for ``pr``, polling up to ``max_wait`` seconds.

    Polls ``query_fn`` (default: :func:`query_pr_review_state`) and classifies each
    result. While the verdict is WAITING_FOR_REVIEW and the elapsed time is within
    ``max_wait``, it sleeps ``poll_interval`` and re-queries. On expiry the pending
    verdict is escalated to REVIEW_TIMEOUT (still a BLOCK). All I/O is injectable so
    the loop is fully deterministic under test.

    ``forced`` records an audited operator override: the verdict is unchanged but the
    result reports ``blocked=False`` so ``--force`` can let an otherwise-blocking
    outcome through with an audit trail.
    """
    if enforcement not in ENFORCEMENT_MODES:
        raise ValueError(
            f"enforcement must be one of {ENFORCEMENT_MODES}, got {enforcement!r}"
        )

    if enforcement == "disabled":
        return CopilotReviewResult(Verdict.NOT_APPLICABLE, enforcement, forced=forced)

    import math
    import time as _time

    # Validate inputs BEFORE the poll loop so a malformed repo/PR raises ValueError to
    # the caller (CLI exit 2) instead of being swallowed as VERIFY_FAILED — and so a
    # newline-bearing value can never reach the --force audit log. Skipped when a
    # query_fn is injected (tests supply their own state without touching gh).
    if query_fn is None:
        pr = _validate_pr(pr)
        repo = _validate_repo(repo)

    # A bounded window requires a finite, positive budget. nan/inf are rejected so the
    # loop can never spin forever; anything else degrades to a single-shot check.
    has_budget = isinstance(max_wait, (int, float)) and math.isfinite(max_wait) and max_wait > 0

    sleep = sleep_fn or _time.sleep
    clock = clock_fn or _time.monotonic
    if query_fn is None:
        def query_fn() -> ReviewState:  # type: ignore[misc]
            return query_pr_review_state(pr, repo, run_fn=run_fn, gh_bin=gh_bin)

    start = clock()
    rounds = 0
    while True:
        rounds += 1
        try:
            state = query_fn()
        except Exception:  # noqa: BLE001 - any query failure is a fail-safe BLOCK
            verdict = classify(None, enforcement, verify_failed=True)
            return CopilotReviewResult(
                verdict, enforcement, rounds=rounds, forced=forced,
                detail=f"round {rounds}",
            )

        verdict = classify(state, enforcement)
        if verdict is not Verdict.WAITING_FOR_REVIEW:
            return CopilotReviewResult(
                verdict,
                enforcement,
                head_ref_oid=state.head_ref_oid,
                unresolved_thread_ids=state.copilot_unresolved_thread_ids,
                rounds=rounds,
                forced=forced,
            )

        # Review is enabled but not yet complete for HEAD. With no wait budget this
        # is a single-shot check (WAITING); with a budget we poll until the window
        # expires, then escalate to REVIEW_TIMEOUT. Both outcomes BLOCK.
        if not has_budget:
            return CopilotReviewResult(
                Verdict.WAITING_FOR_REVIEW,
                enforcement,
                head_ref_oid=state.head_ref_oid,
                unresolved_thread_ids=state.copilot_unresolved_thread_ids,
                rounds=rounds,
                forced=forced,
            )
        elapsed = clock() - start
        if elapsed >= max_wait:
            verdict = classify(state, enforcement, timed_out=True)
            return CopilotReviewResult(
                verdict,
                enforcement,
                head_ref_oid=state.head_ref_oid,
                unresolved_thread_ids=state.copilot_unresolved_thread_ids,
                rounds=rounds,
                forced=forced,
                detail=f"waited {elapsed:.0f}s of {max_wait:.0f}s",
            )
        sleep(poll_interval)
