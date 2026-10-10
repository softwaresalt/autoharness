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
      reviews(last:100){ nodes{ databaseId author{ login } state commit{ oid } body }
        pageInfo{ hasPreviousPage } }
      reviewThreads(first:100){ nodes{ id isResolved
        comments(first:1){ nodes{ author{ login } } } }
        pageInfo{ hasNextPage } }
      comments(last:100){ nodes{ author{ login } authorAssociation body }
        pageInfo{ hasPreviousPage } }
    }
  }
}"""


class Verdict(enum.Enum):
    """The classified outcome of the Copilot-review gate for one PR at one HEAD."""

    SATISFIED = "SATISFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
    UNRESOLVED_THREADS = "UNRESOLVED_THREADS"
    UNDISPOSITIONED_BODY_FINDINGS = "UNDISPOSITIONED_BODY_FINDINGS"
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
    Verdict.UNDISPOSITIONED_BODY_FINDINGS: (
        "A completed Copilot review body carries findings with no review thread, and "
        "no trusted PR comment has dispositioned them. BLOCK: fix each finding, or "
        "capture it (P-021 C2), or decline it with a rationale; then post a PR comment "
        "quoting the findings with the line 'Copilot-Review-Body-Disposition: <review "
        "id>' and re-run."
    ),
    Verdict.REVIEW_TIMEOUT: (
        "Copilot review is enabled but did not complete for the current HEAD within "
        "the bounded --max-wait window. BLOCK (timeout never equals silent merge). "
        "Re-run after review completes, or override with an audited --force."
    ),
    Verdict.DETECTION_AMBIGUOUS: (
        "The PR review state could not be interpreted unambiguously (missing HEAD, a "
        "malformed GraphQL response, or review-body disposition that cannot be confirmed). "
        "BLOCK (fail-safe) until the state is verifiable."
    ),
    Verdict.VERIFY_FAILED: (
        "Could not verify Copilot-review state (gh missing, API unreachable, or the "
        "query failed) and enablement is unknown. BLOCK (fail-safe)."
    ),
}


# ---------------------------------------------------------------------------
# Review-body findings (201-F U1)
# ---------------------------------------------------------------------------

# Literal marker a trusted PR comment carries to disposition one Copilot review body.
DISPOSITION_MARKER = "Copilot-Review-Body-Disposition:"

# The Copilot overview-format version this detector understands. Other versions are
# still counted best-effort and surfaced as an advisory (OQ-1).
KNOWN_OVERVIEW_VERSION = 2


@dataclass(frozen=True)
class BodyFindings:
    """Threadless findings counted in one Copilot review body."""

    count: int
    markers: tuple[str, ...]
    overview_version: int | None


_BODY_PREVIOUSLY_MISSED_RE = re.compile(r"Previously\s+missed\s*\((\d+)\)", re.IGNORECASE)
_BODY_SUPPRESSED_RE = re.compile(r"Suppressed\s+comments\s*\((\d+)\)", re.IGNORECASE)
_BODY_OPEN_FINDINGS_RE = re.compile(r"(?<!\d)(\d+)\s+open\s+findings?", re.IGNORECASE)
_BODY_ANCHOR_RE = re.compile(r"#discussion_r\d+")
_BODY_SECTION_HEADER_RE = re.compile(r"<summary>\s*<strong>|^### ", re.IGNORECASE | re.MULTILINE)
_BODY_OVERVIEW_RE = re.compile(r"<!--\s*ccr-overview-v(\d+)\s*-->", re.IGNORECASE)


def detect_body_findings(body: str) -> BodyFindings:
    """Count threadless findings in one Copilot review body (pure, stdlib ``re``).

    ``count = max(S, PM) + U``:

    * ``PM`` is the largest ``Previously missed (N)`` count in the body;
    * ``S`` is the largest ``Suppressed comments (N)`` count in the body (the maximum
      over occurrences keeps the detector on the fail-closed side);
    * ``U = max(0, N_open - A)`` where ``N_open`` is the count of each ``N open findings``
      headline, and ``A`` is the number of ``#discussion_r`` anchors inside that headline's
      span. ``U`` is the largest such value over all open-findings headlines. Each span
      ends at the next section header (``<summary><strong>`` or a
      ``### `` line) or at the end of the body. Nested ``<summary><picture>`` per-finding
      blocks are not section headers, so they cannot truncate the span.

    The ``resolved since last review``, ``What changed in this PR``, and overview risk
    lines are never counted.
    """
    text = body or ""

    previously_missed = max(
        (int(m.group(1)) for m in _BODY_PREVIOUSLY_MISSED_RE.finditer(text)), default=0
    )
    suppressed = max((int(m.group(1)) for m in _BODY_SUPPRESSED_RE.finditer(text)), default=0)

    unanchored = 0
    # Each open-findings headline is checked against its own span; the largest
    # unanchored count wins, which keeps the detector on the fail-closed side.
    for open_match in _BODY_OPEN_FINDINGS_RE.finditer(text):
        n_open = int(open_match.group(1))
        header = _BODY_SECTION_HEADER_RE.search(text, open_match.end())
        span_end = header.start() if header is not None else len(text)
        anchors = len(_BODY_ANCHOR_RE.findall(text[open_match.end() : span_end]))
        unanchored = max(unanchored, n_open - anchors)

    markers: list[str] = []
    if previously_missed > 0:
        markers.append("previously_missed")
    if suppressed > 0:
        markers.append("suppressed")
    if unanchored > 0:
        markers.append("unanchored_open")

    overview = _BODY_OVERVIEW_RE.search(text)
    return BodyFindings(
        count=max(suppressed, previously_missed) + unanchored,
        markers=tuple(markers),
        overview_version=int(overview.group(1)) if overview is not None else None,
    )



# ---------------------------------------------------------------------------
# Parsed review state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReviewRecord:
    """One submitted Copilot review: its state and the commit it reviewed."""

    state: str
    commit_oid: str | None
    database_id: int | None = None
    body_findings: int = 0
    overview_version: int | None = None


@dataclass(frozen=True)
class ReviewState:
    """The Copilot-relevant slice of a pull request's review surface."""

    head_ref_oid: str | None
    copilot_requested: bool
    copilot_reviews: tuple[ReviewRecord, ...]
    copilot_unresolved_thread_ids: tuple[str, ...]
    parse_ok: bool = True
    dispositioned_review_ids: frozenset[int] = frozenset()
    comments_complete: bool = True

    @property
    def undispositioned_body_finding_review_ids(self) -> tuple[int, ...]:
        """Completed Copilot reviews (any round) with threadless body findings that no
        trusted PR comment has dispositioned, in review order."""
        return tuple(
            review.database_id
            for review in self.copilot_reviews
            if review.state in _COMPLETED_STATES
            and review.body_findings > 0
            and review.database_id is not None
            and review.database_id not in self.dispositioned_review_ids
        )

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


# Non-Copilot comment authors whose association may clear a body-finding disposition.
TRUSTED_DISPOSITION_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})

# An exact disposition line: the literal marker, one canonical ASCII integer review
# databaseId (no leading zero, no non-ASCII digits), and nothing else on the line.
# Trailing text (for example "101 later") never clears a review.
_DISPOSITION_LINE_RE = re.compile(
    rf"^{re.escape(DISPOSITION_MARKER)}[ \t]*(0|[1-9][0-9]*)[ \t]*\r?$", re.MULTILINE
)


def _login(node: Any) -> str | None:
    if isinstance(node, Mapping):
        login = node.get("login")
        if isinstance(login, str):
            return login
    return None


def _requested_is_copilot(node: Mapping[str, Any]) -> bool | None:
    """Whether a ``reviewRequests`` node requests the Copilot bot.

    Returns ``True``/``False`` when the reviewer identity is readable, or ``None``
    when the reviewer object is malformed or its bot identity cannot be read. A
    determinable non-bot reviewer (User/Team/Mannequin/...) is not the Copilot bot;
    only a genuinely unreadable identity fails closed, so a pending human or team
    review request never blocks the gate.
    """
    reviewer = node.get("requestedReviewer")
    if not isinstance(reviewer, Mapping):
        return None
    typename = reviewer.get("__typename")
    if not isinstance(typename, str):
        return None
    if typename == "Bot":
        login = reviewer.get("login")
        if not isinstance(login, str):
            return None
        return login == COPILOT_LOGIN
    return False


def _connection(container: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    """Return the connection mapping for ``key``, or None if absent/malformed."""
    val = container.get(key)
    return val if isinstance(val, Mapping) else None


def _page_complete(conn: Mapping[str, Any], field: str) -> bool:
    """True ONLY when ``pageInfo`` explicitly proves the connection is not truncated.

    Fail-closed: a missing ``pageInfo``, a non-mapping ``pageInfo``, or a non-boolean
    (or ``True``) ``field`` is unverifiable and returns False, so the parser can never
    mistake an unprovable connection for a complete one.
    """
    page_info = conn.get("pageInfo")
    if not isinstance(page_info, Mapping):
        return False
    return page_info.get(field) is False


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

    # reviewRequests — a structurally invalid, unprovably-complete, or truncated
    # connection means we cannot prove Copilot's enablement state, so fail closed
    # rather than assume "not asked".
    req = _connection(pr, "reviewRequests")
    if req is None or not _page_complete(req, "hasNextPage"):
        return _ambiguous()
    req_nodes = _strict_nodes(req)
    if req_nodes is None:
        return _ambiguous()
    copilot_requested = False
    for node in req_nodes:
        is_copilot = _requested_is_copilot(node)
        if is_copilot is None:
            # A request node whose reviewer identity/type cannot be read is
            # unverifiable: we cannot prove it is NOT the Copilot bot, so fail closed
            # instead of silently treating it as "not Copilot".
            return _ambiguous()
        if is_copilot:
            copilot_requested = True

    # reviews — must be structurally valid and provably complete; every Copilot review
    # must carry a known state (a missing/unknown state must not be read as "completed").
    rv = _connection(pr, "reviews")
    if rv is None or not _page_complete(rv, "hasPreviousPage"):
        return _ambiguous()
    review_nodes = _strict_nodes(rv)
    if review_nodes is None:
        return _ambiguous()
    reviews: list[ReviewRecord] = []
    for node in review_nodes:
        author = _login(node.get("author"))
        if author is None:
            # An unidentifiable review author is unverifiable: it could be the Copilot
            # bot with a transiently-null identity, so fail closed before filtering
            # rather than silently skipping it as "not Copilot".
            return _ambiguous()
        if author != COPILOT_LOGIN:
            continue
        state = node.get("state")
        if not isinstance(state, str) or state not in _KNOWN_STATES:
            return _ambiguous()
        commit = node.get("commit")
        oid = commit.get("oid") if isinstance(commit, Mapping) else None
        # Review body (201-F U2): GitHub's body is non-null, so an absent, null, or
        # non-string body is unverifiable and fails closed.
        body = node.get("body")
        if not isinstance(body, str):
            # GitHub's review body is non-null, so an absent or null body is
            # unverifiable and fails closed rather than counting as "no findings".
            return _ambiguous()
        try:
            findings = detect_body_findings(body)
        except ValueError:
            # A digit run beyond CPython's int-conversion limit cannot be counted.
            return _ambiguous()
        database_id = node.get("databaseId")
        if isinstance(database_id, bool) or not isinstance(database_id, int):
            database_id = None
        if findings.count > 0 and database_id is None:
            # A body finding that cannot be dispositioned by review ID is unverifiable.
            return _ambiguous()
        reviews.append(
            ReviewRecord(
                state=state,
                commit_oid=oid if isinstance(oid, str) else None,
                database_id=database_id,
                body_findings=findings.count,
                overview_version=findings.overview_version,
            )
        )

    # reviewThreads — must be structurally valid and provably complete; a truncated or
    # malformed thread list could hide an unresolved Copilot thread and yield a false
    # SATISFIED.
    threads = _connection(pr, "reviewThreads")
    if threads is None or not _page_complete(threads, "hasNextPage"):
        return _ambiguous()
    thread_nodes = _strict_nodes(threads)
    if thread_nodes is None:
        return _ambiguous()
    unresolved: list[str] = []
    for node in thread_nodes:
        resolved = node.get("isResolved")
        if resolved is True:
            continue
        if resolved is not False:
            # A non-boolean isResolved is a malformed thread; fail closed.
            return _ambiguous()
        # An unresolved thread with a malformed/absent comment list or an
        # undeterminable author is unverifiable: we cannot prove it is NOT an open
        # Copilot thread, so fail closed instead of silently dropping it.
        comment_nodes = _strict_nodes(node.get("comments"))
        if comment_nodes is None:
            return _ambiguous()
        first = comment_nodes[0] if comment_nodes else None
        author = _login(first.get("author")) if first is not None else None
        if author is None:
            return _ambiguous()
        if author == COPILOT_LOGIN:
            tid = node.get("id")
            if not isinstance(tid, str):
                # A malformed id on an open Copilot thread cannot be resolved/tracked.
                return _ambiguous()
            unresolved.append(tid)

    # PR conversation comments (201-F U2). A missing or malformed connection is
    # unverifiable and fails closed. A comment with an unattributable author (a deleted
    # account) is skipped, and so is any comment that is not a trusted disposition: only
    # a non-bot comment with authorAssociation OWNER, MEMBER, or COLLABORATOR can clear a
    # review-body disposition. Skipping is the fail-closed direction for clearance.
    comments = _connection(pr, "comments")
    if comments is None:
        return _ambiguous()
    comment_nodes = _strict_nodes(comments)
    if comment_nodes is None:
        return _ambiguous()
    dispositioned: set[int] = set()
    for node in comment_nodes:
        author = _login(node.get("author"))
        if author is None:
            # An unattributable comment (a deleted account) can never be a trusted
            # disposition, so it is skipped. It does not make the gate ambiguous, which
            # would wedge every PR on a comment that cannot clear anything.
            continue
        association = node.get("authorAssociation")
        if author == COPILOT_LOGIN:
            continue
        if not isinstance(association, str) or association not in TRUSTED_DISPOSITION_ASSOCIATIONS:
            continue
        text = node.get("body")
        if not isinstance(text, str):
            continue
        try:
            dispositioned.update(int(match.group(1)) for match in _DISPOSITION_LINE_RE.finditer(text))
        except ValueError:
            return _ambiguous()

    return ReviewState(
        head_ref_oid=head,
        copilot_requested=copilot_requested,
        copilot_reviews=tuple(reviews),
        copilot_unresolved_thread_ids=tuple(unresolved),
        dispositioned_review_ids=frozenset(dispositioned),
        comments_complete=_page_complete(comments, "hasPreviousPage"),
    )


def _strict_nodes(container: Any) -> list[Mapping[str, Any]] | None:
    """Return a connection's ``nodes`` as mappings, or None if unverifiable.

    Fail-closed: a non-mapping container, an absent/non-array ``nodes`` field, or any
    non-object entry yields None so the caller BLOCKS rather than treating malformed
    data as an empty (and therefore "clean") node list.
    """
    if not isinstance(container, Mapping):
        return None
    nodes = container.get("nodes")
    if not isinstance(nodes, Sequence) or isinstance(nodes, (str, bytes)):
        return None
    result: list[Mapping[str, Any]] = []
    for node in nodes:
        if not isinstance(node, Mapping):
            return None
        result.append(node)
    return result


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

    if state.undispositioned_body_finding_review_ids:
        # Threadless review-body findings with no trusted disposition (201-F U3).
        # Truncated comments could hide the disposition marker on an unfetched page,
        # so the verdict is ambiguous rather than a definite block.
        if not state.comments_complete:
            return Verdict.DETECTION_AMBIGUOUS
        return Verdict.UNDISPOSITIONED_BODY_FINDINGS

    return Verdict.SATISFIED


def _overview_advisory(state: ReviewState) -> tuple[str, ...]:
    """OQ-1 advisory: a Copilot review body with an unrecognized overview version.

    The verdict is unaffected; the advisory tells an operator that body detection may
    be incomplete and the review bodies should be read manually.
    """
    messages: list[str] = []
    for review in state.copilot_reviews:
        version = review.overview_version
        if version is None or version == KNOWN_OVERVIEW_VERSION:
            continue
        message = (
            f"unrecognized ccr-overview version v{version}: review-body detection may be "
            "incomplete; read review bodies manually"
        )
        if message not in messages:
            messages.append(message)
    return tuple(messages)


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
    undispositioned_body_finding_review_ids: tuple[int, ...] = ()
    advisory: tuple[str, ...] = ()

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
            "undispositioned_body_finding_review_ids": list(
                self.undispositioned_body_finding_review_ids
            ),
            "advisory": list(self.advisory),
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


def _ambiguity_detail(state: ReviewState, verdict: Verdict) -> str:
    """Operator-facing cause for DETECTION_AMBIGUOUS that a truncated comments page causes."""
    if verdict is Verdict.DETECTION_AMBIGUOUS and state.parse_ok and not state.comments_complete:
        return "PR comments page truncated; disposition markers cannot be confirmed"
    return ""


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
) -> CopilotReviewResult:
    """Evaluate the gate for ``pr``, polling up to ``max_wait`` seconds.

    Polls ``query_fn`` (default: :func:`query_pr_review_state`) and classifies each
    result. While the verdict is WAITING_FOR_REVIEW and the elapsed time is within
    ``max_wait``, it sleeps ``poll_interval`` and re-queries. On expiry the pending
    verdict is escalated to REVIEW_TIMEOUT (still a BLOCK). All I/O is injectable so
    the loop is fully deterministic under test.

    Evaluation is **purely blocking**: it never returns a passed-through override. An
    audited operator ``--force`` bypass is applied by the CLI *after* the audit record
    is written (see :func:`autoharness.cli._audit_copilot_review_force`), so a direct
    caller can never obtain an unaudited non-blocking result from this function.
    """
    if enforcement not in ENFORCEMENT_MODES:
        raise ValueError(
            f"enforcement must be one of {ENFORCEMENT_MODES}, got {enforcement!r}"
        )

    if enforcement == "disabled":
        return CopilotReviewResult(Verdict.NOT_APPLICABLE, enforcement)

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
                verdict, enforcement, rounds=rounds,
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
                undispositioned_body_finding_review_ids=state.undispositioned_body_finding_review_ids,
                advisory=_overview_advisory(state),
                detail=_ambiguity_detail(state, verdict),
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
                undispositioned_body_finding_review_ids=state.undispositioned_body_finding_review_ids,
                advisory=_overview_advisory(state),
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
                detail=f"waited {elapsed:.0f}s of {max_wait:.0f}s",
                undispositioned_body_finding_review_ids=state.undispositioned_body_finding_review_ids,
                advisory=_overview_advisory(state),
            )
        # Sleep only for the remaining budget so the advertised bounded wait is
        # honoured: a full poll_interval could otherwise overshoot the window by up to
        # one interval (e.g. --max-wait 1 must not sleep a full 15s before rechecking).
        sleep(min(poll_interval, max_wait - elapsed))
