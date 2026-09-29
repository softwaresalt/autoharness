"""P-002.7 canonical post-claim member-status contract — conformance suite.

177-S / 169-F. Created by RED task 169.009-T at this exact path and extended in
place by 169.010-T, 169.012-T, 169.013-T and 169.014-T. No other module in this
unit holds an assertion.

Every assertion is a ``check_*`` function that raises ``AssertionError`` whose
text starts with the assertion's own declared marker. Each assertion is
observed three ways, one test method per observation, named
``test_<ID>_<slug>__<observation>``:

* ``live_surfaces``      — the assertion against the four declared surfaces as
  they exist in the working tree. Before ACTIVATE (169.015-T) this is the
  ABSENCE RED observation: it fails individually with its own marker.
* ``near_miss_fixture``  — the DISCRIMINATING RED observation: the assertion is
  executed against its named near-miss fixture (tests/p002_7_near_miss_fixtures.py)
  and must FAIL there with its own marker and a MISMATCH (not ABSENT) reason;
  the test method passes only when that failure is observed.
* ``inert_candidate``    — the INERT GREEN observation: the assertion executed
  against the canonical candidate definition (tests/p002_7_candidate_definition.py)
  applied in memory as test-owned data, and observed passing.

Import safety (binding): this module reads no file and runs no process at import
time; every surface read happens inside a test body through a helper.

Plan: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md (rev 8).
"""

from __future__ import annotations

import re
import unittest
from typing import Callable, Mapping

import p002_7_candidate_definition as candidate
import p002_7_near_miss_fixtures as near_miss

ABSENT = "ABSENT"
MISMATCH = "MISMATCH"


def _fail(marker: str, reason: str, detail: str) -> None:
    raise AssertionError("%s: %s: %s" % (marker, reason, detail))


def _single_block(surfaces: Mapping[str, str], path: str, marker: str) -> str:
    block = candidate.extract_single_block(surfaces.get(path, ""))
    if block is None:
        _fail(marker, ABSENT, "%s carries no single P-002.7 block" % path)
    return block


def _assert_discriminates(testcase: unittest.TestCase, check: Callable[[], None], marker: str) -> None:
    """Discriminating RED: ``check`` must fail against its near-miss, for its own marker, on a MISMATCH."""

    try:
        check()
    except AssertionError as exc:
        text = str(exc)
        # Recorded so the observation harness can report the discriminating failure text itself.
        testcase.observed_near_miss_failure = text
        testcase.assertTrue(text.startswith(marker + ":"), "failure carried a foreign marker: %s" % text)
        testcase.assertIn(MISMATCH, text, "near-miss failed on absence, not on the contract: %s" % text)
        return
    testcase.fail("%s: assertion did not fail against its near-miss fixture" % marker)


# ---------------------------------------------------------------------------
# Family A (169.009-T): the three claim-to-admission transition rows
# ---------------------------------------------------------------------------

MARKER_A = {
    "T1": "P002_7_A1_ROW_T1",
    "T2": "P002_7_A2_ROW_T2",
    "T3": "P002_7_A3_ROW_T3",
}


def check_a_transition_row(surfaces: Mapping[str, str], row_id: str) -> None:
    marker = MARKER_A[row_id]
    expected = [row for row in candidate.TRANSITION_ROWS if row[0] == row_id]
    for path in candidate.POLICY_SURFACES:
        block = _single_block(surfaces, path, marker)
        found = [row for row in candidate.parse_transition_rows(block) if row and row[0] == row_id]
        if found != expected:
            _fail(marker, MISMATCH, "%s row %s is %r, expected %r" % (path, row_id, found, expected))


class FamilyATransitionRowsTests(unittest.TestCase):
    """Positive presence of each canonical claim-to-admission row, in both policy copies."""

    def test_A1_row_t1__live_surfaces(self) -> None:
        check_a_transition_row(candidate.load_live_surfaces(), "T1")

    def test_A1_row_t1__near_miss_fixture(self) -> None:
        _assert_discriminates(
            self, lambda: check_a_transition_row(near_miss.row_target_altered("T1"), "T1"), MARKER_A["T1"]
        )

    def test_A1_row_t1__inert_candidate(self) -> None:
        check_a_transition_row(candidate.load_candidate_surfaces(), "T1")

    def test_A2_row_t2__live_surfaces(self) -> None:
        check_a_transition_row(candidate.load_live_surfaces(), "T2")

    def test_A2_row_t2__near_miss_fixture(self) -> None:
        _assert_discriminates(
            self, lambda: check_a_transition_row(near_miss.row_target_altered("T2"), "T2"), MARKER_A["T2"]
        )

    def test_A2_row_t2__inert_candidate(self) -> None:
        check_a_transition_row(candidate.load_candidate_surfaces(), "T2")

    def test_A3_row_t3__live_surfaces(self) -> None:
        check_a_transition_row(candidate.load_live_surfaces(), "T3")

    def test_A3_row_t3__near_miss_fixture(self) -> None:
        _assert_discriminates(
            self, lambda: check_a_transition_row(near_miss.row_target_altered("T3"), "T3"), MARKER_A["T3"]
        )

    def test_A3_row_t3__inert_candidate(self) -> None:
        check_a_transition_row(candidate.load_candidate_surfaces(), "T3")


# ---------------------------------------------------------------------------
# Family B (169.010-T): bidirectional cross-reference, resolving in both copies
# ---------------------------------------------------------------------------

MARKER_B_FORWARD = "P002_7_B1_XREF_FORWARD"
MARKER_B_REVERSE = "P002_7_B2_XREF_REVERSE"


def check_b_forward_cross_reference(surfaces: Mapping[str, str]) -> None:
    """The policy clause names the Ship intake-reconciliation note, and that note resolves, in both copies."""

    marker = MARKER_B_FORWARD
    sentence = candidate.normalize_whitespace(candidate.FORWARD_CROSS_REFERENCE)
    for copy, (policy_path, agent_path) in candidate.CROSS_REFERENCE_COPIES.items():
        block = _single_block(surfaces, policy_path, marker)
        if sentence not in candidate.normalize_whitespace(block):
            _fail(marker, MISMATCH, "%s copy: %s does not name the Ship intake-reconciliation note" % (copy, policy_path))
        agent_text = surfaces.get(agent_path, "")
        note_at = agent_text.find(candidate.SHIP_NOTE_TITLE)
        agent_block = candidate.extract_single_block(agent_text)
        if note_at < 0 or agent_block is None or agent_text.find(agent_block) < note_at:
            _fail(marker, MISMATCH, "%s copy: named Ship note does not resolve in %s" % (copy, agent_path))


def check_b_reverse_cross_reference(surfaces: Mapping[str, str]) -> None:
    """The Ship intake-reconciliation note names the policy clause, and that clause resolves, in both copies."""

    marker = MARKER_B_REVERSE
    sentence = candidate.normalize_whitespace(candidate.REVERSE_CROSS_REFERENCE)
    for copy, (policy_path, agent_path) in candidate.CROSS_REFERENCE_COPIES.items():
        block = _single_block(surfaces, agent_path, marker)
        if sentence not in candidate.normalize_whitespace(block):
            _fail(marker, MISMATCH, "%s copy: %s does not name the P-002.7 clause" % (copy, agent_path))
        if candidate.VOCABULARY_HEADING not in surfaces.get(policy_path, ""):
            _fail(marker, MISMATCH, "%s copy: named P-002.7 clause does not resolve in %s" % (copy, policy_path))


class FamilyBCrossReferenceTests(unittest.TestCase):
    """The two prose sites name each other bidirectionally; one-directional is a failure."""

    def test_B1_xref_forward__live_surfaces(self) -> None:
        check_b_forward_cross_reference(candidate.load_live_surfaces())

    def test_B1_xref_forward__near_miss_fixture(self) -> None:
        _assert_discriminates(
            self,
            lambda: check_b_forward_cross_reference(near_miss.cross_reference_reverse_only()),
            MARKER_B_FORWARD,
        )

    def test_B1_xref_forward__inert_candidate(self) -> None:
        check_b_forward_cross_reference(candidate.load_candidate_surfaces())

    def test_B2_xref_reverse__live_surfaces(self) -> None:
        check_b_reverse_cross_reference(candidate.load_live_surfaces())

    def test_B2_xref_reverse__near_miss_fixture(self) -> None:
        _assert_discriminates(
            self,
            lambda: check_b_reverse_cross_reference(near_miss.cross_reference_forward_only()),
            MARKER_B_REVERSE,
        )

    def test_B2_xref_reverse__inert_candidate(self) -> None:
        check_b_reverse_cross_reference(candidate.load_candidate_surfaces())


# ---------------------------------------------------------------------------
# Family C (169.012-T): template and installed mirror identical in the P-002.7 block
# ---------------------------------------------------------------------------

MARKER_C = {
    "policy": "P002_7_C1_MIRROR_POLICY",
    "agent": "P002_7_C2_MIRROR_AGENT",
}


def check_c_mirror_identity(surfaces: Mapping[str, str], pair: str) -> None:
    marker = MARKER_C[pair]
    template_path, mirror_path = candidate.MIRROR_PAIRS[pair]
    template_block = _single_block(surfaces, template_path, marker)
    mirror_block = _single_block(surfaces, mirror_path, marker)
    if template_block != mirror_block:
        template_words = template_block.split()
        mirror_words = mirror_block.split()
        first = next(
            (i for i, (a, b) in enumerate(zip(template_words, mirror_words)) if a != b),
            min(len(template_words), len(mirror_words)),
        )
        _fail(
            marker,
            MISMATCH,
            "%s P-002.7 block diverges from %s at word %d" % (mirror_path, template_path, first),
        )


class FamilyCMirrorIdentityTests(unittest.TestCase):
    """Each authoritative template and its installed mirror carry a byte-identical P-002.7 block."""

    def test_C1_mirror_policy__live_surfaces(self) -> None:
        check_c_mirror_identity(candidate.load_live_surfaces(), "policy")

    def test_C1_mirror_policy__near_miss_fixture(self) -> None:
        _assert_discriminates(
            self, lambda: check_c_mirror_identity(near_miss.mirror_diverged("policy"), "policy"), MARKER_C["policy"]
        )

    def test_C1_mirror_policy__inert_candidate(self) -> None:
        check_c_mirror_identity(candidate.load_candidate_surfaces(), "policy")

    def test_C2_mirror_agent__live_surfaces(self) -> None:
        check_c_mirror_identity(candidate.load_live_surfaces(), "agent")

    def test_C2_mirror_agent__near_miss_fixture(self) -> None:
        _assert_discriminates(
            self, lambda: check_c_mirror_identity(near_miss.mirror_diverged("agent"), "agent"), MARKER_C["agent"]
        )

    def test_C2_mirror_agent__inert_candidate(self) -> None:
        check_c_mirror_identity(candidate.load_candidate_surfaces(), "agent")


# ---------------------------------------------------------------------------
# Family D (169.013-T): observed-version attribution paragraph present
# ---------------------------------------------------------------------------

MARKER_D = "P002_7_D1_ATTRIBUTION"
_VERSION_RE = re.compile(r"backlogit \d+\.\d+\.\d+")


def check_d_attribution(surfaces: Mapping[str, str]) -> None:
    """The clause records the backlogit version it was observed against (recorded, not executed)."""

    marker = MARKER_D
    for path in candidate.POLICY_SURFACES:
        block = _single_block(surfaces, path, marker)
        paragraphs = [line for line in block.split("\n") if line.startswith(candidate.ATTRIBUTION_LABEL)]
        if len(paragraphs) != 1:
            _fail(marker, MISMATCH, "%s carries %d observed-version attribution paragraphs" % (path, len(paragraphs)))
        if not _VERSION_RE.search(paragraphs[0]):
            _fail(marker, MISMATCH, "%s attribution paragraph names no backlogit version" % path)


class FamilyDAttributionTests(unittest.TestCase):
    """The externally-observed clause carries its observed-version attribution in both policy copies."""

    def test_D1_attribution__live_surfaces(self) -> None:
        check_d_attribution(candidate.load_live_surfaces())

    def test_D1_attribution__near_miss_fixture(self) -> None:
        _assert_discriminates(self, lambda: check_d_attribution(near_miss.attribution_removed()), MARKER_D)

    def test_D1_attribution__inert_candidate(self) -> None:
        check_d_attribution(candidate.load_candidate_surfaces())


if __name__ == "__main__":
    unittest.main()
