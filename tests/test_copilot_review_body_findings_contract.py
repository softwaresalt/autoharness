"""Cross-surface contract pin for the Copilot review-body findings gate (201-F U9).

The verdict name and the disposition marker must not drift between the gate code, the
gate reference doc, the PR-automation instruction (template and mirror), the P-018
policy (template and mirror), and Ship step 7c (template and mirror). Each assertion
runs on whitespace-collapsed text, so line wrapping in a surface cannot hide a token.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from autoharness.gates.copilot_review import DISPOSITION_MARKER, PASS_VERDICTS, Verdict

_ROOT = Path(__file__).resolve().parents[1]
_VERDICT = Verdict.UNDISPOSITIONED_BODY_FINDINGS.value
_BLOCK_PEER = "UNRESOLVED_THREADS"
_INSTRUCTION_TEMPLATE = _ROOT / "templates" / "instructions" / "github-pr-automation.instructions.md.tmpl"
_INSTRUCTION_MIRROR = _ROOT / ".github" / "instructions" / "github-pr-automation.instructions.md"
_POLICY_TEMPLATE = _ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
_POLICY_MIRROR = _ROOT / ".github" / "policies" / "workflow-policies.md"
_SHIP_TEMPLATE = _ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_SHIP_MIRROR = _ROOT / ".github" / "agents" / "_ship.agent.md"
_GATE_DOC = _ROOT / "docs" / "copilot-review-gate.md"

# The seven surfaces that must carry the verdict and the marker (plan U9, scenario 1).
_SURFACES = (
    _INSTRUCTION_TEMPLATE,
    _INSTRUCTION_MIRROR,
    _POLICY_TEMPLATE,
    _POLICY_MIRROR,
    _SHIP_TEMPLATE,
    _SHIP_MIRROR,
    _GATE_DOC,
)


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _paragraphs(text: str) -> list[str]:
    """Blank-line-separated blocks, collapsed. A Markdown table or list is one block."""
    return [_collapse(block) for block in re.split(r"\n\s*\n", text) if block.strip()]


class CopilotReviewBodyFindingsContractTests(unittest.TestCase):
    def test_verdict_and_marker_appear_on_every_surface(self) -> None:
        for path in _SURFACES:
            with self.subTest(surface=path.relative_to(_ROOT).as_posix()):
                text = _collapse(_read(path))
                self.assertIn(_VERDICT, text)
                self.assertIn(DISPOSITION_MARKER, text)

    def test_verdict_is_block_and_co_occurs_with_unresolved_threads(self) -> None:
        self.assertNotIn(Verdict.UNDISPOSITIONED_BODY_FINDINGS, PASS_VERDICTS)
        for path in _SURFACES:
            with self.subTest(surface=path.relative_to(_ROOT).as_posix()):
                paragraphs = _paragraphs(_read(path))
                self.assertTrue(
                    any(_VERDICT in block and _BLOCK_PEER in block for block in paragraphs),
                    "no block enumerates the new BLOCK verdict beside UNRESOLVED_THREADS",
                )

    def test_instruction_has_threadless_section_and_readiness_token(self) -> None:
        for path in (_INSTRUCTION_TEMPLATE, _INSTRUCTION_MIRROR):
            with self.subTest(surface=path.relative_to(_ROOT).as_posix()):
                text = _collapse(_read(path))
                self.assertIn("Threadless Review-Body Findings", text)
                self.assertIn("Review-body findings:", text)


if __name__ == "__main__":
    unittest.main()
