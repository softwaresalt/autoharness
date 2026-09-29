"""P-002.7 near-miss fixtures (177-S / 169-F, task 169.011-T, PREPARE, inert).

The discriminating RED rule: every assertion in the conformance suite must be
observed failing not only against the current (absent) surfaces but also
against a synthetic near-miss -- a copy of the canonical candidate mutated in
EXACTLY the way that assertion exists to catch. A failure against the near-miss
proves the assertion tests the CONTRACT rather than a file's existence.

Every fixture starts from ``load_candidate_surfaces()`` (the canonical content
applied in memory to the live surfaces) and changes one thing. The module is
not collected by ``unittest discover`` (no ``test`` prefix) and contains no
assertion. Nothing runs at import time.
"""

from __future__ import annotations

from typing import Dict

import p002_7_candidate_definition as candidate


def _replace_in_blocks(surfaces: Dict[str, str], paths, old: str, new: str) -> Dict[str, str]:
    mutated = dict(surfaces)
    for path in paths:
        text = mutated[path]
        block = candidate.extract_single_block(text)
        if block is None or old not in block:
            raise ValueError("near-miss mutation anchor not found in %s" % path)
        mutated[path] = text.replace(block, block.replace(old, new, 1), 1)
    return mutated


def row_target_altered(row_id: str) -> Dict[str, str]:
    """Family A: one transition row's target (admission outcome) altered."""

    rows = []
    for row in candidate.TRANSITION_ROWS:
        if row[0] == row_id:
            outcome = row[3]
            altered = outcome.replace("**admit**", "**halt**", 1) if "**admit**" in outcome else outcome.replace(
                "**halt**", "**admit**", 1
            )
            row = (row[0], row[1], row[2], altered)
        rows.append(row)
    old_block = candidate.POLICY_BLOCK
    new_block = candidate.render_policy_block(rows=tuple(rows))
    surfaces = candidate.load_candidate_surfaces()
    for path in candidate.POLICY_SURFACES:
        surfaces[path] = surfaces[path].replace(old_block, new_block, 1)
    return surfaces


def cross_reference_forward_only() -> Dict[str, str]:
    """Family B (reverse direction): the policy names the Ship note, the Ship note does not name the policy."""

    note = candidate.SHIP_NOTE_PARAGRAPH.replace(
        candidate.REVERSE_CROSS_REFERENCE, "is the expected post-claim state", 1
    ).replace("; P-002.7 names this intake-reconciliation note in return", "", 1)
    old_block = candidate.AGENT_BLOCK
    new_block = candidate.render_agent_block(note=note)
    surfaces = candidate.load_candidate_surfaces()
    for path in candidate.AGENT_SURFACES:
        surfaces[path] = surfaces[path].replace(old_block, new_block, 1)
    return surfaces


def cross_reference_reverse_only() -> Dict[str, str]:
    """Family B (forward direction): the Ship note names the policy, the policy does not name the Ship note."""

    old_block = candidate.POLICY_BLOCK
    new_block = candidate.render_policy_block(
        cross_reference="**Cross-reference**: this contract applies at shipment intake."
    )
    surfaces = candidate.load_candidate_surfaces()
    for path in candidate.POLICY_SURFACES:
        surfaces[path] = surfaces[path].replace(old_block, new_block, 1)
    return surfaces


def mirror_diverged(pair: str) -> Dict[str, str]:
    """Family C: the installed mirror's P-002.7 block diverged from its template by one word."""

    _template, mirror = candidate.MIRROR_PAIRS[pair]
    surfaces = candidate.load_candidate_surfaces()
    word = "legitimately" if pair == "policy" else "canonical"
    replacement = "normally" if pair == "policy" else "expected"
    return _replace_in_blocks(surfaces, [mirror], word, replacement)


def attribution_removed() -> Dict[str, str]:
    """Family D: the observed-version attribution paragraph removed."""

    old_block = candidate.POLICY_BLOCK
    new_block = candidate.render_policy_block(attribution=None)
    surfaces = candidate.load_candidate_surfaces()
    for path in candidate.POLICY_SURFACES:
        surfaces[path] = surfaces[path].replace(old_block, new_block, 1)
    return surfaces


FOURTH_ROW = (
    "T4",
    "`active`",
    "all `active`, resumed session",
    "**halt** `WAVE_NO_PROGRESS`",
)


def fourth_row_added() -> Dict[str, str]:
    """Family E1: a fourth transition row added to the table."""

    old_block = candidate.POLICY_BLOCK
    new_block = candidate.render_policy_block(rows=candidate.TRANSITION_ROWS + (FOURTH_ROW,))
    surfaces = candidate.load_candidate_surfaces()
    for path in candidate.POLICY_SURFACES:
        surfaces[path] = surfaces[path].replace(old_block, new_block, 1)
    return surfaces


FIFTH_SURFACE_PATH = "templates/agents/_stage.agent.md.tmpl"


def fifth_surface_introduced() -> Dict[str, str]:
    """Family E2: a fifth declaring surface introduced inside the search scope."""

    files = candidate.load_candidate_scope_files()
    existing = files.get(FIFTH_SURFACE_PATH, "")
    files[FIFTH_SURFACE_PATH] = existing + "\n" + candidate.AGENT_BLOCK
    return files
