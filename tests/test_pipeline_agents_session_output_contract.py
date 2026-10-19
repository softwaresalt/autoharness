"""Pipeline agents report normative operator-visible events in the session output.

209-F U11-U13 (plan D-4): the Orchestrator, Ship and Stage agents no longer
depend on a remote broadcast channel. Normative events stay as unconditional
session-output reports and the Operator Choice Presentation Rule replaces the
combined remote-broadcast rule.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

_ORCHESTRATOR = (
    "templates/agents/_orchestrator.agent.md.tmpl",
    ".github/agents/_orchestrator.agent.md",
)
_SHIP = (
    "templates/agents/_ship.agent.md.tmpl",
    ".github/agents/_ship.agent.md",
)
_STAGE = (
    "templates/agents/_stage.agent.md.tmpl",
    ".github/agents/_stage.agent.md",
)


def _read(rel: str) -> str:
    return (_REPO_ROOT / rel).read_text(encoding="utf-8")


class PipelineAgentsSessionOutputContractTests(unittest.TestCase):
    def test_orchestrator_dark_mode_events_are_session_output_summaries(self) -> None:
        for rel in _ORCHESTRATOR:
            with self.subTest(path=rel):
                text = _read(rel)
                self.assertIn("emit `DARK_MODE_START` and `DARK_MODE_SCOPE` as operator-visible", text)
                self.assertIn("session-output summaries", text)
                self.assertIn("resolved scope, approval authority, admin", text)
                self.assertIn("degraded-visibility behavior defined in P-017", text)
                self.assertIn("emit `DARK_MODE_COMPLETE` or `DARK_MODE_HALTED`", text)

    def test_ship_template_reports_wait_notices_and_closure_warning_in_session_output(self) -> None:
        text = _read(_SHIP[0])
        self.assertIn("Report `[WAIT] Awaiting user merge approval` in the session output", text)
        self.assertIn("STOP until the operator replies", text)
        self.assertIn("On halt, also report `[WAIT] Merge not confirmed for PR #{pr_number}: {state}`", text)
        self.assertIn("log `CLOSURE_INDEX_SYNC_WARN` and write the warning to the session output", text)
        self.assertIn("claim-verify result in the session output.", text)

    def test_ship_agents_report_violations_and_gates_in_session_output(self) -> None:
        for rel in _SHIP:
            with self.subTest(path=rel):
                text = _read(rel)
                self.assertIn("P-009 violation in the session output", text)

    def test_stage_agents_carry_operator_choice_presentation_rule(self) -> None:
        for rel in _STAGE:
            with self.subTest(path=rel):
                text = _read(rel)
                self.assertIn("Operator Choice Presentation Rule", text)
                self.assertIn("self-contained", text)
                self.assertIn("operator selection or confirmation is awaited", text)
                self.assertIn("native approval path", text)
                self.assertIn("`strict-safety`", text)
                self.assertIn("report a P-005 violation in the session output", text)

    def test_stage_step_sequence_checklist_keeps_all_steps_in_order(self) -> None:
        for rel in _STAGE:
            with self.subTest(path=rel):
                text = _read(rel)
                block = text.split("```text", 1)[1].split("```", 1)[0]
                steps = [line.split("—")[0].strip() for line in block.splitlines() if line.startswith("[ ]")]
                self.assertEqual(steps[0], "[ ] Step 0.0")
                self.assertEqual(steps[1], "[ ] Step 0.1")
                self.assertEqual(steps[2], "[ ] Step 0")
                self.assertEqual(steps[-1], "[ ] Step 6")
                self.assertNotIn("0.1c", "".join(steps))


if __name__ == "__main__":
    unittest.main()
