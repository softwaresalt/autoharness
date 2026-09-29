"""P-002.7 canonical candidate definition (177-S / 169-F, task 169.011-T, PREPARE, inert).

This module is TEST-OWNED DATA. It is the single canonical source of every word
the P-002.7 ACTIVATE commit (169.015-T) later transcribes into the four declared
surfaces, plus the executable surface-enumeration rule the conformance suite
applies. It is deliberately named so that ``unittest discover``'s default
``test*.py`` pattern does NOT collect it: it contributes no test and no
assertion. It is imported by ``tests/test_p002_7_member_status_contract.py``.

INERT: nothing in the live harness imports or references this module, no policy
clause points at it, and no declared surface is changed by authoring it.

Plan: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
(plan_id post-claim-member-status-contract-v2, revision 8). Stash 3EF5AAF2.

Nothing here reads a file or runs a process at import time; every filesystem
or git access happens inside a function called from a test body.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Clause identity
# ---------------------------------------------------------------------------

CLAUSE_ANCHOR = "P-002.7"
VOCABULARY_HEADING = "### P-002.7 — Post-Claim Member-Status Contract"

BLOCK_BEGIN_PREFIX = "<!-- P-002.7:BEGIN"
BLOCK_END_LINE_SUFFIX = "<!-- P-002.7:END -->"

# ---------------------------------------------------------------------------
# Declared surfaces and the surface-enumeration rule (plan: Declared surfaces)
# ---------------------------------------------------------------------------

POLICY_TEMPLATE = "templates/policies/workflow-policies.md.tmpl"
POLICY_INSTALLED = ".github/policies/workflow-policies.md"
AGENT_TEMPLATE = "templates/agents/_ship.agent.md.tmpl"
AGENT_INSTALLED = ".github/agents/_ship.agent.md"

# Enumeration order is load-bearing: it is the CCD/v1 input order.
DECLARED_SURFACES: Tuple[str, ...] = (
    POLICY_TEMPLATE,
    POLICY_INSTALLED,
    AGENT_TEMPLATE,
    AGENT_INSTALLED,
)
DECLARED_SURFACE_COUNT = 4

POLICY_SURFACES: Tuple[str, ...] = (POLICY_TEMPLATE, POLICY_INSTALLED)
AGENT_SURFACES: Tuple[str, ...] = (AGENT_TEMPLATE, AGENT_INSTALLED)

# Authoritative/mirror pairs: (template, installed mirror).
MIRROR_PAIRS: Dict[str, Tuple[str, str]] = {
    "policy": (POLICY_TEMPLATE, POLICY_INSTALLED),
    "agent": (AGENT_TEMPLATE, AGENT_INSTALLED),
}

# Copy pairs for the bidirectional cross-reference: (policy copy, agent copy).
CROSS_REFERENCE_COPIES: Dict[str, Tuple[str, str]] = {
    "template": (POLICY_TEMPLATE, AGENT_TEMPLATE),
    "installed": (POLICY_INSTALLED, AGENT_INSTALLED),
}

SEARCH_SCOPE: Tuple[str, ...] = (
    "templates/policies/",
    ".github/policies/",
    "templates/agents/",
    ".github/agents/",
)

# Excluded by rule, not by oversight. .autoharness/staging/ (.gitignore:6) is a
# generated verify-workspace artifact, not a mirror; .autoharness/gates/
# (.gitignore:7) holds this unit's generated verdict artifacts; docs/ narrates
# the contract and does not declare it.
EXCLUDED_PREFIXES: Tuple[str, ...] = (
    ".autoharness/staging/",
    ".autoharness/gates/",
    "docs/",
)

# ---------------------------------------------------------------------------
# Canonical vocabulary: exactly three claim-to-admission transition rows
# ---------------------------------------------------------------------------

TRANSITION_TABLE_HEADER = (
    "| Row | Shipment record | Manifest members | Admission outcome |",
    "|-----|-----------------|------------------|-------------------|",
)

# (row id, shipment record status, manifest member state, admission outcome)
TRANSITION_ROWS: Tuple[Tuple[str, str, str, str], ...] = (
    (
        "T1",
        "`active`",
        "all `active`, claim just issued",
        "**admit** — the post-claim cascade state, not a residual",
    ),
    (
        "T2",
        "`queued`",
        "at least one `active` or `done`",
        "**halt** `SHIPMENT_STATE_INCONSISTENT`",
    ),
    (
        "T3",
        "`active`",
        "mixed `done` / `active` / `queued`, mid-execution",
        "**admit** — not an intake-reconciliation case",
    ),
)
TRANSITION_ROW_COUNT = 3

# ---------------------------------------------------------------------------
# Clause prose
# ---------------------------------------------------------------------------

STATEMENT_PARAGRAPH = (
    "**Statement**: Immediately after a shipment claim, every queued manifest member legitimately "
    "reads `active`. That status is the claim operation's own cascade, not evidence of prior partial "
    "execution, so no derived or workspace-local admission rule may treat the post-claim all-active "
    "state as a blocking residual."
)

VOCABULARY_INTRO_PARAGRAPH = (
    "**Canonical post-claim member-status vocabulary**: the claim-to-admission transition is defined "
    "by exactly these three rows, and no other row belongs to this contract."
)

PRESERVED_DISTINCTION_PARAGRAPH = (
    "**Preserved distinction**: a mid-execution partial-active manifest (row T3) is a genuinely "
    "different state from the post-claim all-active manifest (row T1). Any active-residual gate a "
    "workspace authors for the mid-execution state remains valid and is not weakened; the "
    "discriminator is the claim boundary, not member status alone. This clause does not suppress, "
    "soften, or pre-empt the `SHIPMENT_STATE_INCONSISTENT` early-warning (row T2)."
)

ATTRIBUTION_LABEL = "**Observed-version attribution**:"
ATTRIBUTION_PARAGRAPH = (
    ATTRIBUTION_LABEL
    + " backlogit `ClaimShipment` activates the shipment record and every included queued member in "
    "one all-or-nothing operation. That behaviour was observed against backlogit 1.10.0 "
    "(`docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`, pinned "
    "upstream by `TestClaimShipment_ActivatesIncludedScope`) and re-observed against backlogit "
    "1.11.0 at the 177-S claim. This clause records that observed version range only; re-verify the "
    "cascade against the installed backlogit version rather than treating it as a claim about all "
    "versions."
)

# Forward half of the bidirectional cross-reference: the policy clause names
# the Ship intake-reconciliation note.
SHIP_NOTE_TITLE = "**Intake reconciliation check"
FORWARD_CROSS_REFERENCE = (
    "the Ship agent's intake-reconciliation note (the **Intake reconciliation check** item of "
    "Ship's shipment intake) applies this contract at intake and names P-002.7 in return"
)
FORWARD_CROSS_REFERENCE_PARAGRAPH = (
    "**Cross-reference**: " + FORWARD_CROSS_REFERENCE + "; the two must be changed together."
)

# Reverse half: the Ship note names the policy clause.
REVERSE_CROSS_REFERENCE = (
    "is the canonical post-claim state defined by P-002.7 (Post-Claim Member-Status Contract) in "
    "the workflow policy registry"
)
SHIP_NOTE_PARAGRAPH = (
    "**Post-claim member status (P-002.7)**: the all-`active` manifest this check expects "
    "immediately after this session's own claim in item 4 "
    + REVERSE_CROSS_REFERENCE
    + ", not a residual from prior partial execution; P-002.7 names this intake-reconciliation "
    "note in return, so the two must be changed together."
)

SHIP_NOTE_INDENT = "   "
SHIP_NOTE_WRAP_WIDTH = 116

# ---------------------------------------------------------------------------
# Block rendering
# ---------------------------------------------------------------------------


def _table_row(cells: Iterable[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _wrap(text: str, width: int, indent: str) -> List[str]:
    lines: List[str] = []
    current = ""
    for word in text.split(" "):
        candidate = word if not current else current + " " + word
        if current and len(indent) + len(candidate) > width:
            lines.append(indent + current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(indent + current)
    return lines


def render_policy_block(
    rows: Tuple[Tuple[str, str, str, str], ...] = TRANSITION_ROWS,
    attribution: Optional[str] = ATTRIBUTION_PARAGRAPH,
    cross_reference: Optional[str] = FORWARD_CROSS_REFERENCE_PARAGRAPH,
) -> str:
    """Return the canonical P-002.7 policy block (LF line endings, trailing LF).

    The keyword arguments exist only so the near-miss fixture module can derive
    a copy mutated in exactly one way; the defaults ARE the canonical clause.
    """

    lines: List[str] = [
        BLOCK_BEGIN_PREFIX + " canonical post-claim member-status contract -->",
        VOCABULARY_HEADING,
        "",
        STATEMENT_PARAGRAPH,
        "",
        VOCABULARY_INTRO_PARAGRAPH,
        "",
        *TRANSITION_TABLE_HEADER,
        *(_table_row(row) for row in rows),
        "",
        PRESERVED_DISTINCTION_PARAGRAPH,
    ]
    if attribution is not None:
        lines += ["", attribution]
    if cross_reference is not None:
        lines += ["", cross_reference]
    lines.append(BLOCK_END_LINE_SUFFIX)
    return "\n".join(lines) + "\n"


def render_agent_block(note: str = SHIP_NOTE_PARAGRAPH) -> str:
    """Return the canonical P-002.7 Ship-agent block (indented list continuation)."""

    lines = [SHIP_NOTE_INDENT + BLOCK_BEGIN_PREFIX + " post-claim member-status cross-reference -->"]
    lines += _wrap(note, SHIP_NOTE_WRAP_WIDTH, SHIP_NOTE_INDENT)
    lines.append(SHIP_NOTE_INDENT + BLOCK_END_LINE_SUFFIX)
    return "\n".join(lines) + "\n"


POLICY_BLOCK = render_policy_block()
AGENT_BLOCK = render_agent_block()

# ---------------------------------------------------------------------------
# Transcription placement (consumed verbatim by ACTIVATE, 169.015-T)
# ---------------------------------------------------------------------------

POLICY_INSERT_AFTER_LINE = "**Violation Action**: Halt and suggest running the harness-architect."
AGENT_INSERT_AFTER_FRAGMENT = "which is built for exactly that mixed state."

AMENDMENT_INSERT_AFTER_PREFIX = "| 1.26.0  |"
AMENDMENT_REASON = (
    "177-S (169-F, stash 3EF5AAF2): canonical post-claim member-status contract — immediately after "
    "a shipment claim every queued manifest member legitimately reads `active` (backlogit "
    "`ClaimShipment` cascade, observed 1.10.0 and re-observed 1.11.0); exactly three "
    "claim-to-admission rows (T1 admit the post-claim all-active state, T2 halt "
    "`SHIPMENT_STATE_INCONSISTENT`, T3 admit the mid-execution mixed state); bidirectional "
    "cross-reference with the Ship intake-reconciliation note. The mid-execution active-residual "
    "distinction and the `SHIPMENT_STATE_INCONSISTENT` early-warning are unchanged. Coverage: "
    "`tests/test_p002_7_member_status_contract.py`"
)
AMENDMENT_ROWS: Dict[str, str] = {
    POLICY_TEMPLATE: "| 1.27.0  | {{DATE}}     | Added P-002.7    | " + AMENDMENT_REASON + " |",
    POLICY_INSTALLED: "| 1.27.0  | 2026-09-29     | Added P-002.7    | " + AMENDMENT_REASON + " |",
}


def _insert_after_line(text: str, predicate, insertion: str) -> str:
    lines = text.split("\n")
    matches = [i for i, line in enumerate(lines) if predicate(line)]
    if len(matches) != 1:
        raise ValueError("insertion anchor must match exactly one line, matched %d" % len(matches))
    index = matches[0]
    insertion_lines = insertion.split("\n")
    return "\n".join(lines[: index + 1] + insertion_lines + lines[index + 1 :])


def strip_activation(path: str, text: str) -> str:
    """Remove exactly what :func:`apply_activation` inserts (idempotence helper)."""

    block = POLICY_BLOCK if path in POLICY_SURFACES else AGENT_BLOCK
    text = text.replace("\n" + block, "", 1) if ("\n" + block) in text else text
    row = AMENDMENT_ROWS.get(path)
    if row is not None:
        text = text.replace(row + "\n", "", 1)
    return text


def apply_activation(path: str, text: str) -> str:
    """Return ``text`` with the canonical P-002.7 content transcribed into it.

    Idempotent: any previously transcribed canonical content is stripped first.
    """

    base = strip_activation(path, text)
    if path in POLICY_SURFACES:
        activated = _insert_after_line(
            base,
            lambda line: line == POLICY_INSERT_AFTER_LINE,
            "\n" + POLICY_BLOCK.rstrip("\n"),
        )
        return _insert_after_line(
            activated,
            lambda line: line.startswith(AMENDMENT_INSERT_AFTER_PREFIX),
            AMENDMENT_ROWS[path],
        )
    if path in AGENT_SURFACES:
        return _insert_after_line(
            base,
            lambda line: AGENT_INSERT_AFTER_FRAGMENT in line,
            "\n" + AGENT_BLOCK.rstrip("\n"),
        )
    raise ValueError("not a declared surface: %s" % path)


# ---------------------------------------------------------------------------
# Readers (called only from test bodies, never at import time)
# ---------------------------------------------------------------------------


def read_surface(path: str) -> str:
    """Read one repository file as LF-normalized text; missing file reads as ''."""

    full = REPO_ROOT / path
    try:
        data = full.read_bytes()
    except FileNotFoundError:
        return ""
    return data.replace(b"\r\n", b"\n").decode("utf-8", errors="replace")


def load_live_surfaces() -> Dict[str, str]:
    return {path: read_surface(path) for path in DECLARED_SURFACES}


def load_candidate_surfaces() -> Dict[str, str]:
    """The inert candidate: the live surfaces with the canonical content applied in memory."""

    live = load_live_surfaces()
    return {path: apply_activation(path, text) for path, text in live.items()}


def tracked_scope_paths() -> List[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", *SEARCH_SCOPE],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=True,
    )
    return sorted(p for p in result.stdout.decode("utf-8").split("\0") if p)


def load_live_scope_files() -> Dict[str, str]:
    return {path: read_surface(path) for path in tracked_scope_paths()}


def load_candidate_scope_files() -> Dict[str, str]:
    files = load_live_scope_files()
    for path in DECLARED_SURFACES:
        files[path] = apply_activation(path, files.get(path, read_surface(path)))
    return files


# ---------------------------------------------------------------------------
# Surface-enumeration rule (executable form of the plan's marker set)
# ---------------------------------------------------------------------------


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def in_search_scope(path: str) -> bool:
    return path.startswith(SEARCH_SCOPE) and not path.startswith(EXCLUDED_PREFIXES)


def is_declaring_surface(text: str) -> bool:
    """Marker set: the clause anchor together with either the vocabulary block
    or a cross-reference sentence that names the clause."""

    if CLAUSE_ANCHOR not in text:
        return False
    flat = normalize_whitespace(text)
    return (
        VOCABULARY_HEADING in text
        or normalize_whitespace(FORWARD_CROSS_REFERENCE) in flat
        or normalize_whitespace(REVERSE_CROSS_REFERENCE) in flat
    )


def enumerate_declaring_surfaces(files: Mapping[str, str]) -> Tuple[str, ...]:
    return tuple(
        sorted(path for path, text in files.items() if in_search_scope(path) and is_declaring_surface(text))
    )


# ---------------------------------------------------------------------------
# Block extraction and table parsing
# ---------------------------------------------------------------------------


def extract_blocks(text: str) -> List[str]:
    """Return every P-002.7 block (BEGIN line through END line inclusive, LF-joined)."""

    blocks: List[str] = []
    current: Optional[List[str]] = None
    for line in text.split("\n"):
        if current is None:
            if line.lstrip().startswith(BLOCK_BEGIN_PREFIX):
                current = [line]
        else:
            current.append(line)
            if line.rstrip().endswith(BLOCK_END_LINE_SUFFIX):
                blocks.append("\n".join(current) + "\n")
                current = None
    return blocks


def extract_single_block(text: str) -> Optional[str]:
    blocks = extract_blocks(text)
    return blocks[0] if len(blocks) == 1 else None


def parse_transition_rows(block: str) -> List[Tuple[str, ...]]:
    rows: List[Tuple[str, ...]] = []
    for line in block.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("| T"):
            continue
        cells = tuple(cell.strip() for cell in stripped.strip("|").split("|"))
        rows.append(cells)
    return rows
