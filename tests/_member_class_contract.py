"""Executable reading of the shipment-reconcile Member-Class Status Contract (161-F / 169-S).

Shared by ``test_shipment_reconcile_member_class_contract.py`` (U4, 161.001-T)
and ``test_shipment_reconcile_member_class_regression.py`` (U5, 161.002-T).

The contract under test is prose: a marker-bounded block in
``shipment-reconcile`` (resolved ``.github/skills/shipment-reconcile/SKILL.md``
and its template ``templates/skills/shipment-reconcile/SKILL.md.tmpl``). This
module does not restate the contract's status sets. It *parses* them from the
skill's own member-class table, so the gate-behaviour scenarios fail the moment
the table and the expected outcomes disagree, and pass only when the published
text itself yields the expected outcome.

What lives here, and why it is not a second source of truth:

* ``parse_member_class_table`` reads the status sets (``matched``, tolerated
  labels, halting values) from the skill text. Nothing in this module lists
  which statuses a member class may carry.
* ``evaluate_premode`` encodes only the *row-selection* rule (which member uses
  which row), which the skill states in prose and which the doc-contract tests
  pin separately: the ``qualifying-feature`` row applies only to the
  pre-close invocation (``expected_status: done``) under a step 2b ``CASCADE``
  verdict, and only to IDs in the classifier's qualifying set; every other
  member, and every member of every other invocation, uses the
  ``strict-scalar`` row.
* Close-path verdicts come from the real, unmodified
  ``classify_shipment_close_path`` run against an in-repo fixture backlog.

``unittest`` only (097-S canonical gate). Fixture backlogs live under the
git-ignored ``.autoharness/staging/tmp/`` root inside the repository
(Constitution IV) and are removed by the creating test.
"""

from __future__ import annotations

import os
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from autoharness.gates.shipment_closure import ClosePath, ClosePathDecision

REPO_ROOT = Path(__file__).resolve().parents[1]
RESOLVED_RELATIVE = ".github/skills/shipment-reconcile/SKILL.md"
TEMPLATE_RELATIVE = "templates/skills/shipment-reconcile/SKILL.md.tmpl"
RESOLVED_PATH = REPO_ROOT / RESOLVED_RELATIVE
TEMPLATE_PATH = REPO_ROOT / TEMPLATE_RELATIVE

BLOCK_BEGIN = "<!-- member-class-status-contract:BEGIN -->"
BLOCK_END = "<!-- member-class-status-contract:END -->"

CLASS_QUALIFYING_FEATURE = "qualifying-feature"
CLASS_STRICT_SCALAR = "strict-scalar"

MATCHED = "matched"
PRE_ARCHIVED = "pre-archived"
ANOMALY = "qualifying-feature-pre-archived-anomaly"
STATUS_MISMATCH = "status-mismatch"
MISSING = "missing"
CLASSIFIER_CONTRACT_HALT = "RECONCILE_FAIL_PREMODE_CLASSIFIER_CONTRACT"

PROCEED = "PROCEED"
HALT = "HALT"

_PROCEEDING_CLASSIFICATIONS = frozenset({MATCHED, PRE_ARCHIVED, ANOMALY})
_EXPECTED_STATUS_SENTINEL = "expected_status"
_ANY_OTHER_VALUE = "any other value"

_rendered_template_cache: str | None = None


def resolved_text() -> str:
    return RESOLVED_PATH.read_text(encoding="utf-8")


def template_text() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def rendered_template_text() -> str:
    """The template rendered with this workspace's own variable table.

    Uses the verifier's own renderer through ``tests/_assertion_render.py``
    (H2: no parallel substitution path), so the rendered template and the
    resolved copy are compared on equal terms.
    """
    global _rendered_template_cache
    if _rendered_template_cache is None:
        from _assertion_render import VARIANT_BACKLOGIT, RenderedCorpus

        corpus = RenderedCorpus(VARIANT_BACKLOGIT)
        _rendered_template_cache = corpus.render(TEMPLATE_PATH, RESOLVED_RELATIVE)
    return _rendered_template_cache


def sources() -> tuple[tuple[str, str], ...]:
    """(label, text) for both copies, each in resolved (placeholder-free) form."""
    return (("resolved", resolved_text()), ("rendered-template", rendered_template_text()))


def flatten(text: str) -> str:
    """Collapse all whitespace runs so prose re-wrapping never breaks a needle."""
    return re.sub(r"\s+", " ", text)


def extract_contract_block(text: str) -> str:
    begin = text.find(BLOCK_BEGIN)
    end = text.find(BLOCK_END)
    if begin == -1 or end == -1 or end < begin:
        raise LookupError(
            "Member-Class Status Contract block not found: expected "
            f"{BLOCK_BEGIN!r} ... {BLOCK_END!r}"
        )
    return text[begin + len(BLOCK_BEGIN) : end]


def section(text: str, start_heading: str, end_heading: str) -> str:
    """Text from ``start_heading`` up to (not including) the next ``end_heading``.

    ``start_heading`` must occur exactly once, so a moved, removed or duplicated
    anchor fails loudly instead of silently binding to the wrong region.
    """
    occurrences = text.count(start_heading)
    if occurrences != 1:
        raise LookupError(f"start anchor {start_heading!r} occurs {occurrences} times; expected exactly 1")
    start = text.index(start_heading)
    end = text.find(end_heading, start + len(start_heading))
    if end == -1:
        raise LookupError(f"end anchor {end_heading!r} not found after {start_heading!r}")
    return text[start:end]


@dataclass(frozen=True)
class MemberClassRow:
    matched: frozenset[str]
    matched_is_expected_status: bool
    tolerated: Mapping[str, str]
    halting: frozenset[str]
    halts_on_any_other_value: bool


def _cells(row_line: str) -> list[str]:
    return [cell.strip() for cell in row_line.strip().strip("|").split("|")]


def _ticked(cell: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cell)


def parse_member_class_table(block: str) -> dict[str, MemberClassRow]:
    """Parse the four-column member-class table out of the contract block.

    Expected shape (status values back-ticked; tolerated cell pairs a declared
    status with the label it is reported under)::

        | Member class | `matched` | Tolerated ... | HALT (`status-mismatch`) |
        |---|---|---|---|
        | `qualifying-feature` | `active`, `done` | `archived` -> `<label>` | `queued`; any other value (R-5) |
        | `strict-scalar` | the invocation's `expected_status` | `archived` -> `pre-archived` | any other value (R-5) |
    """
    rows: dict[str, MemberClassRow] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| `"):
            continue
        cells = _cells(stripped)
        if len(cells) != 4:
            raise ValueError(f"member-class row must have 4 cells, got {len(cells)}: {line!r}")
        class_tokens = _ticked(cells[0])
        if len(class_tokens) != 1:
            raise ValueError(f"member-class cell must name exactly one class: {cells[0]!r}")
        matched_tokens = _ticked(cells[1])
        tolerated_tokens = _ticked(cells[2])
        if len(tolerated_tokens) % 2:
            raise ValueError(f"tolerated cell must pair status -> label: {cells[2]!r}")
        tolerated = {
            tolerated_tokens[index]: tolerated_tokens[index + 1]
            for index in range(0, len(tolerated_tokens), 2)
        }
        halt_cell = cells[3]
        rows[class_tokens[0]] = MemberClassRow(
            matched=frozenset(t for t in matched_tokens if t != _EXPECTED_STATUS_SENTINEL),
            matched_is_expected_status=_EXPECTED_STATUS_SENTINEL in matched_tokens,
            tolerated=tolerated,
            halting=frozenset(t for t in _ticked(halt_cell) if t != STATUS_MISMATCH),
            halts_on_any_other_value=_ANY_OTHER_VALUE in halt_cell.lower(),
        )
    if not rows:
        raise LookupError("no member-class rows found in the contract block")
    return rows


def load_contract(text: str) -> dict[str, MemberClassRow]:
    return parse_member_class_table(extract_contract_block(text))


@dataclass(frozen=True)
class Member:
    """One manifest member as Pre-Mode step 3 sees it."""

    artifact_id: str
    artifact_type: str
    status: object
    location: str | None  # "queue", "archive", "both", "unreadable", or None when missing


@dataclass(frozen=True)
class PreModeOutcome:
    recommendation: str
    classifications: Mapping[str, str]
    halt_token: str | None = None


def _classify_status(row: MemberClassRow, status: object, expected_status: str) -> str:
    # R-5: a missing, empty or non-string status is never a recognised value.
    if not isinstance(status, str) or status == "":
        return STATUS_MISMATCH
    matched = set(row.matched)
    if row.matched_is_expected_status:
        matched.add(expected_status)
    if status in matched:
        return MATCHED
    if status in row.tolerated:
        return row.tolerated[status]
    if status in row.halting or row.halts_on_any_other_value:
        return STATUS_MISMATCH
    # The table itself leaves this value unspecified: a contract defect, not a pass.
    raise AssertionError(f"member-class row leaves status {status!r} unspecified (R-5)")


def evaluate_premode(
    contract: Mapping[str, MemberClassRow],
    members: Iterable[Member],
    *,
    expected_status: str,
    decision: ClosePathDecision | None,
) -> PreModeOutcome:
    """Apply the parsed contract to one Pre-Mode invocation.

    ``decision`` is step 2b's recorded verdict; ``None`` models a classifier
    error, which the skill records as ``SAFE_CLOSE``.
    """
    members = list(members)
    cascade_scope = (
        expected_status == "done"
        and decision is not None
        and decision.close_path is ClosePath.CASCADE
    )
    qualifying = frozenset(decision.qualifying_feature_ids) if cascade_scope else frozenset()
    if cascade_scope and not qualifying:
        # I-2: CASCADE with an empty qualifying set is a classifier contract violation.
        return PreModeOutcome(HALT, {}, CLASSIFIER_CONTRACT_HALT)

    classifications: dict[str, str] = {}
    for member in members:
        if member.location is None:
            classifications[member.artifact_id] = MISSING
            continue
        if member.location in ("both", "unreadable"):
            # Step 3: an ambiguous or unreadable record is never resolved by guessing.
            classifications[member.artifact_id] = STATUS_MISMATCH
            continue
        if cascade_scope and member.artifact_type == "feature" and member.artifact_id not in qualifying:
            # I-1: a feature member outside the qualifying set under CASCADE.
            return PreModeOutcome(HALT, classifications, CLASSIFIER_CONTRACT_HALT)
        member_class = (
            CLASS_QUALIFYING_FEATURE
            if cascade_scope and member.artifact_id in qualifying
            else CLASS_STRICT_SCALAR
        )
        classifications[member.artifact_id] = _classify_status(
            contract[member_class], member.status, expected_status
        )

    proceed = all(value in _PROCEEDING_CLASSIFICATIONS for value in classifications.values())
    return PreModeOutcome(PROCEED if proceed else HALT, classifications)


class FixtureBacklog:
    """An in-repo, git-ignored fixture backlog (Constitution IV containment)."""

    _PREFIX = "member-class-"

    def __init__(self) -> None:
        self.staging_root = (REPO_ROOT / ".autoharness" / "staging" / "tmp").resolve()
        self.root = (self.staging_root / f"{self._PREFIX}{uuid.uuid4().hex}").resolve()
        self._assert_owned()
        self.backlog_dir = self.root / ".backlogit"
        (self.backlog_dir / "queue").mkdir(parents=True, exist_ok=True)
        (self.backlog_dir / "archive").mkdir(parents=True, exist_ok=True)
        self._members: dict[str, Member] = {}

    def _assert_owned(self) -> None:
        """The root must be a ``member-class-*`` child of the staging root, nothing wider."""
        if self.root.parent != self.staging_root or not self.root.name.startswith(self._PREFIX):
            raise AssertionError(f"containment violation: {self.root} is not a fixture under {self.staging_root}")
        if os.path.commonpath([str(REPO_ROOT), str(self.root)]) != str(REPO_ROOT):
            raise AssertionError(f"containment violation: {self.root} escapes {REPO_ROOT}")

    def add(
        self,
        artifact_id: str,
        artifact_type: str,
        *,
        status: str,
        location: str = "queue",
        parent_id: str | None = None,
        archive_status: str | None = None,
    ) -> None:
        """Write one record.

        ``location="both"`` writes a torn queue + archive pair; ``archive_status``
        makes the archive copy declare a different status (a conflicting duplicate).
        """
        def render(declared: str) -> str:
            lines = ["---", f"id: {artifact_id}", f"artifact_type: {artifact_type}"]
            if parent_id is not None:
                lines.append(f"parent_id: {parent_id}")
            lines.append(f"status: {declared}")
            lines.extend(["---", f"# {artifact_id}", ""])
            return "\n".join(lines)

        if location == "both":
            (self.backlog_dir / "queue" / f"{artifact_id}.md").write_text(render(status), encoding="utf-8")
            (self.backlog_dir / "archive" / f"{artifact_id}.md").write_text(
                render(archive_status or status), encoding="utf-8"
            )
        else:
            (self.backlog_dir / location / f"{artifact_id}.md").write_text(render(status), encoding="utf-8")
        self._members[artifact_id] = Member(artifact_id, artifact_type, status, location)

    def add_unreadable(self, artifact_id: str, *, location: str = "queue") -> None:
        """Write a record whose frontmatter never closes, so it cannot be parsed."""
        (self.backlog_dir / location / f"{artifact_id}.md").write_text(
            f"---\nid: {artifact_id}\nstatus: [unterminated\n", encoding="utf-8"
        )
        self._members[artifact_id] = Member(artifact_id, "unknown", None, "unreadable")

    def members(self, manifest: Iterable[str]) -> list[Member]:
        return [self._members[item] for item in manifest]

    def cleanup(self) -> None:
        self._assert_owned()
        if self.root.exists():
            shutil.rmtree(self.root)
