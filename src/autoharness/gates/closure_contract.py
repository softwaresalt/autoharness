"""Closure-evidence naming contract: the single authoritative definition (167-F).

This module is the ONE machine-readable place the post-merge closure-evidence
filename contract is stated. The producer documentation
(``operational-closure`` skill, Ship agent) quotes
``CANONICAL_CLOSURE_PATTERN_DOC`` verbatim, and the consumer
(``autoharness.gates.topology.FilesystemTopologyReaders``) discovers evidence
through ``classify_closure_candidates``. Neither side restates the pattern, so
the two cannot drift apart again (decision D1,
``docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md``).

Normative source: ``docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md``
(revision 5), section "Contract Specification":

* **C1** -- identifier grammars (write side, uppercase-only, case-sensitive).
* **C2** -- recognized read set: closed, exactly two fully-anchored patterns.
  R1 (canonical) is the read side of what the builder writes; R2 (legacy) is
  read-only over the closed, already-committed date-prefixed corpus and is the
  ONLY place lowercase tolerance exists.
* **C3** -- candidate attribution is a parse at a designated filename position,
  never a token search.
* **C4** -- path construction is anchored to an explicit, resolved workspace
  root and contained within it.
* **C5** -- the acceptance predicate is owned by the consumer
  (``topology._closure_artifact_complete``); this module only describes it.

Scope guard: this module performs NO frontmatter parsing and makes NO validity
judgement. It answers "which files are candidates for this shipment, and how
are they classified by name", and builds/contains canonical paths. It never
creates a directory, never writes a file, and never touches the committed
closure corpus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

__all__ = [
    "CANONICAL_CLOSURE_FILENAME_TEMPLATE",
    "CANONICAL_CLOSURE_PATTERN_DOC",
    "CLOSURE_DIR_PLACEHOLDER",
    "CLOSURE_FEATURE_ID_PATTERN",
    "CLOSURE_PREDICATE_REQUIREMENT_DOC",
    "CLOSURE_SHIPMENT_ID_PATTERN",
    "CONSUMER_SITES",
    "CONTRACT_DEFINITION_SITE",
    "DEFAULT_CLOSURE_DIR",
    "RECOGNIZED_CLOSURE_PATTERNS",
    "RUNTIME_SCAN_ROOTS",
    "ClosureContractError",
    "ClosureDiscovery",
    "ClosureDiscoveryOutcome",
    "attribute_closure_candidate",
    "classify_closure_candidates",
]


class ClosureContractError(ValueError):
    """Raised when a caller-supplied identifier or path violates the contract."""


# ---------------------------------------------------------------------------
# C1 -- identifier grammars (single definition; every other component consumes)
# ---------------------------------------------------------------------------

# ASCII alphanumeric ordinal with NO internal hyphen.
_ORDINAL_FRAGMENT = r"[A-Za-z0-9]+"
# Canonical (uppercase) kind letters.
_SHIPMENT_KIND = "S"
_FEATURE_KIND = "F"
# Non-capturing identifier fragments composed from the grammar pieces above.
# R1 embeds these so its identifier segments are the SAME grammar as C1.
_SHIPMENT_ID_FRAGMENT = f"{_ORDINAL_FRAGMENT}-{_SHIPMENT_KIND}"
_FEATURE_ID_FRAGMENT = f"{_ORDINAL_FRAGMENT}-{_FEATURE_KIND}"

CLOSURE_SHIPMENT_ID_PATTERN = re.compile(
    rf"\A(?P<ordinal>{_ORDINAL_FRAGMENT})-(?P<kind>{_SHIPMENT_KIND})\Z", re.ASCII
)
CLOSURE_FEATURE_ID_PATTERN = re.compile(
    rf"\A(?P<ordinal>{_ORDINAL_FRAGMENT})-(?P<kind>{_FEATURE_KIND})\Z", re.ASCII
)

# ---------------------------------------------------------------------------
# Canonical write pattern (D2) and its derived documentation form (R8)
# ---------------------------------------------------------------------------

CANONICAL_CLOSURE_FILENAME_TEMPLATE = "{shipment_id}-{feature_id}-post-merge-closure.md"
"""The single authoritative write pattern (D2). Placeholders are substituted
by ``build_closure_path``; every other form of the pattern is derived from it."""

CLOSURE_DIR_PLACEHOLDER = "{{DOCS_CLOSURE}}"
"""Template placeholder for the closure directory in producer documentation.
Installed (rendered) mirrors substitute it with the workspace's literal
closure directory (``docs/closure`` in this repository)."""

DEFAULT_CLOSURE_DIR = Path("docs") / "closure"
"""The workspace-relative closure directory the topology consumer reads."""

_PLACEHOLDER_SPLIT = re.compile(r"(\{shipment_id\}|\{feature_id\})")


def _render_pattern_doc(template: str) -> str:
    """Derive the human-readable documented pattern from the machine template.

    Pure function: the documented text producer skills quote verbatim is
    computed from ``CANONICAL_CLOSURE_FILENAME_TEMPLATE`` and can therefore
    never be edited independently of it.
    """
    return f"{CLOSURE_DIR_PLACEHOLDER}/{template}"


def _compile_canonical_pattern(template: str) -> re.Pattern[str]:
    """Compile R1 from the write template and the C1 identifier fragments.

    Each placeholder must appear exactly once; literal text is escaped. This
    makes R1 the read side of exactly what the builder writes.
    """
    parts = _PLACEHOLDER_SPLIT.split(template)
    placeholders = [part for part in parts if part in ("{shipment_id}", "{feature_id}")]
    if sorted(placeholders) != ["{feature_id}", "{shipment_id}"]:
        raise ClosureContractError(
            f"canonical closure template {template!r} must contain each identifier "
            "placeholder exactly once"
        )
    rendered: list[str] = []
    for part in parts:
        if part == "{shipment_id}":
            rendered.append(f"(?P<shipment_id>{_SHIPMENT_ID_FRAGMENT})")
        elif part == "{feature_id}":
            rendered.append(f"(?P<feature_id>{_FEATURE_ID_FRAGMENT})")
        else:
            rendered.append(re.escape(part))
    return re.compile(r"\A" + "".join(rendered) + r"\Z", re.ASCII)


CANONICAL_CLOSURE_PATTERN_DOC = _render_pattern_doc(CANONICAL_CLOSURE_FILENAME_TEMPLATE)
"""Derived, not authored: ``{{DOCS_CLOSURE}}/{shipment_id}-{feature_id}-post-merge-closure.md``."""

# ---------------------------------------------------------------------------
# C2 -- recognized read set (closed, exactly two, fully anchored)
# ---------------------------------------------------------------------------

_CANONICAL_CLOSURE_PATTERN = _compile_canonical_pattern(CANONICAL_CLOSURE_FILENAME_TEMPLATE)
# R2 legacy: read-only over the closed, already-committed date-prefixed corpus.
# Its free-form suffix is intentionally NOT bound to a grammar (binding it
# would silently de-recognize committed history). Lowercase tolerance for the
# shipment kind letter exists here and nowhere else.
_LEGACY_CLOSURE_PATTERN = re.compile(
    r"\A(?P<date>\d{4}-\d{2}-\d{2})-(?P<shipment_id>[A-Za-z0-9]+-[Ss])-(?P<suffix>.+)-closure\.md\Z",
    re.ASCII,
)

RECOGNIZED_CLOSURE_PATTERNS: tuple[re.Pattern[str], re.Pattern[str]] = (
    _CANONICAL_CLOSURE_PATTERN,
    _LEGACY_CLOSURE_PATTERN,
)
"""Ordered, CLOSED recognized read set: ``(R1 canonical, R2 legacy)``.

Adding a third member is a deliberate contract change (D3), pinned by a
cardinality test."""

# ---------------------------------------------------------------------------
# C3 -- designated-position attribution
# ---------------------------------------------------------------------------

# The position R2 reserves for the identifier (immediately after the date).
_LEGACY_SHIPMENT_POSITION = re.compile(
    r"\A\d{4}-\d{2}-\d{2}-(?P<shipment_id>[A-Za-z0-9]+-[Ss])(?:-|\Z)", re.ASCII
)
# The leading position R1 reserves for the identifier.
_CANONICAL_SHIPMENT_POSITION = re.compile(
    r"\A(?P<shipment_id>[A-Za-z0-9]+-[Ss])(?:-|\Z)", re.ASCII
)


def attribute_closure_candidate(filename: str, shipment_id: str) -> bool:
    """Return whether ``filename`` is a closure candidate for ``shipment_id``.

    Parses the shipment identifier from its designated position (legacy
    position first, then canonical) and compares that single parsed group
    using the matched position's own rule: exact, case-sensitive equality for
    the canonical position; ``str.casefold()`` equality for the legacy
    position. The requested token is never searched for anywhere else in the
    filename -- in particular never inside an R2 free-form suffix.
    """
    legacy = _LEGACY_SHIPMENT_POSITION.match(filename)
    if legacy is not None:
        return legacy.group("shipment_id").casefold() == shipment_id.casefold()
    canonical = _CANONICAL_SHIPMENT_POSITION.match(filename)
    if canonical is not None:
        return canonical.group("shipment_id") == shipment_id
    return False


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

ClosureDiscoveryOutcome = Literal["absent", "unrecognized", "recognized"]


@dataclass(frozen=True)
class ClosureDiscovery:
    """Name-level classification of the closure candidates for one shipment.

    ``outcome`` is ``recognized`` when at least one attributed candidate
    matches a recognized pattern, ``unrecognized`` when attributed candidates
    exist but none matches, and ``absent`` when nothing is attributed.
    Recognition never implies acceptance: validity is decided by the
    consumer's predicate over the file content.
    """

    shipment_id: str
    closure_dir: Path
    canonical_matches: tuple[Path, ...]
    legacy_matches: tuple[Path, ...]
    unrecognized_candidates: tuple[Path, ...]
    outcome: ClosureDiscoveryOutcome

    @property
    def evaluation_order(self) -> tuple[Path, ...]:
        """Recognized candidates in D5 order: the canonical partition wins
        outright when non-empty; otherwise the legacy partition."""
        return self.canonical_matches or self.legacy_matches

    @property
    def candidate_paths(self) -> tuple[Path, ...]:
        """Every attributed candidate, in deterministic sorted order."""
        return tuple(
            sorted(
                self.canonical_matches + self.legacy_matches + self.unrecognized_candidates,
                key=lambda path: path.name,
            )
        )


def _matches_canonical(filename: str, shipment_id: str) -> bool:
    match = _CANONICAL_CLOSURE_PATTERN.match(filename)
    return match is not None and match.group("shipment_id") == shipment_id


def _matches_legacy(filename: str, shipment_id: str) -> bool:
    match = _LEGACY_CLOSURE_PATTERN.match(filename)
    return match is not None and match.group("shipment_id").casefold() == shipment_id.casefold()


def classify_closure_candidates(closure_dir: Path | str, shipment_id: str) -> ClosureDiscovery:
    """Classify the entries of ``closure_dir`` attributed to ``shipment_id``.

    A missing directory yields ``absent``. Listing errors (``OSError``) are
    propagated to the caller, which owns fail-closed handling. Candidates are
    returned in deterministic, name-sorted order within each partition.
    """
    directory = Path(closure_dir)
    canonical: list[Path] = []
    legacy: list[Path] = []
    unrecognized: list[Path] = []
    if directory.is_dir():
        for entry in sorted(directory.iterdir(), key=lambda path: path.name):
            name = entry.name
            if not attribute_closure_candidate(name, shipment_id):
                continue
            if _matches_canonical(name, shipment_id):
                canonical.append(entry)
            elif _matches_legacy(name, shipment_id):
                legacy.append(entry)
            else:
                unrecognized.append(entry)
    if canonical or legacy:
        outcome: ClosureDiscoveryOutcome = "recognized"
    elif unrecognized:
        outcome = "unrecognized"
    else:
        outcome = "absent"
    return ClosureDiscovery(
        shipment_id=shipment_id,
        closure_dir=directory,
        canonical_matches=tuple(canonical),
        legacy_matches=tuple(legacy),
        unrecognized_candidates=tuple(unrecognized),
        outcome=outcome,
    )


# ---------------------------------------------------------------------------
# C5 -- descriptive summary of the consumer-owned acceptance predicate
# ---------------------------------------------------------------------------

CLOSURE_PREDICATE_REQUIREMENT_DOC = (
    "a closure artifact is accepted only when its frontmatter carries a "
    "compaction_status (or legacy compaction) of done or degraded AND a "
    "closure_status of READY, or of READY_WITH_CONDITIONS with a non-empty "
    "conditions list in which every entry is a mapping with satisfied: true "
    "(the literal boolean) and a non-empty evidence reference"
)
"""Descriptive text only -- makes NO validity judgement. The deciding
authority is ``autoharness.gates.topology._closure_artifact_complete``."""

# ---------------------------------------------------------------------------
# Contract-owned runtime surface registry (non-drift guard scope)
# ---------------------------------------------------------------------------

CONTRACT_DEFINITION_SITE = "src/autoharness/gates/closure_contract.py"
"""This module's own repository-relative path (the authoritative definition)."""

CONSUMER_SITES: tuple[str, ...] = (
    "src/autoharness/gates/topology.py",
    "src/autoharness/cli.py",
    "templates/skills/operational-closure/SKILL.md.tmpl",
    ".github/skills/operational-closure/SKILL.md",
    "templates/agents/_ship.agent.md.tmpl",
    ".github/agents/_ship.agent.md",
)
"""Runtime and producer sites that derive from this contract."""

RUNTIME_SCAN_ROOTS: tuple[str, ...] = (
    "src/autoharness/",
    "templates/skills/operational-closure/",
    "templates/agents/",
    ".github/skills/operational-closure/",
    ".github/agents/",
)
"""Declared scan scope for the non-drift guard. Narrative ``docs/`` and test
code are outside the scope by construction."""
