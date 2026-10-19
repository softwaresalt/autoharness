"""Skills no longer depend on a remote broadcast channel.

209-F U14-U16 (plan D-4): the planning- and execution-phase skills drop their
per-step broadcast tables and protocol paragraphs. Normative operator-visible
outcomes (gate verdicts, handoff events) stay as session-output reports, and the
literal markers other contracts pin stay untouched.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

_PLANNING_SKILLS = (
    "brainstorm",
    "deliberate",
    "doc-review",
    "harvest",
    "impl-plan",
    "plan-harden",
    "plan-review",
)


def _paths(skill: str) -> list[str]:
    candidates = (
        f"templates/skills/{skill}/SKILL.md.tmpl",
        f".github/skills/{skill}/SKILL.md",
    )
    return [rel for rel in candidates if (_REPO_ROOT / rel).exists()]


def _read(rel: str) -> str:
    return (_REPO_ROOT / rel).read_text(encoding="utf-8")


class PlanningSkillsSessionOutputContractTests(unittest.TestCase):
    def test_planning_skills_carry_no_remote_channel_text(self) -> None:
        for skill in _PLANNING_SKILLS:
            for rel in _paths(skill):
                with self.subTest(path=rel):
                    text = _read(rel).lower()
                    self.assertNotIn("intercom", text)
                    self.assertNotIn("heartbeat", text)
                    self.assertNotIn("| event | level | message prefix |", text)

    def test_brainstorm_handoff_event_is_reported_in_session_output(self) -> None:
        for rel in _paths("brainstorm"):
            with self.subTest(path=rel):
                text = _read(rel)
                self.assertIn("`BRAINSTORM_HANDOFF_READY`", text)
                self.assertIn("Report it in the session output", text)
                self.assertIn("requirements artifact itself", text)
                self.assertIn("Brainstorm does not author pull request", text)

    def test_plan_review_markers_and_persona_rules_are_unchanged(self) -> None:
        for rel in _paths("plan-review"):
            with self.subTest(path=rel):
                text = _read(rel)
                self.assertIn("dispatch_mode: multi-agent | single-agent-declared-degradation | same-model-declared-degradation", text)
                self.assertIn("decision: PASS | ADVISORY | FAIL", text)
                self.assertIn("reviewer subagent dispatch, model-specific reviewer routing, indexed", text)
                self.assertIn("knowledge retrieval are capabilities that must be surfaced", text)

    def test_harvest_marker_checks_are_unchanged(self) -> None:
        for rel in _paths("harvest"):
            with self.subTest(path=rel):
                text = _read(rel)
                self.assertIn("require literal machine-readable", text)
                self.assertIn("`dispatch_mode:` and `decision:`", text)

    def test_doc_review_gated_auto_uses_operator_approval(self) -> None:
        for rel in _paths("doc-review"):
            with self.subTest(path=rel):
                self.assertIn("| `gated_auto` | Operator approval |", _read(rel))


if __name__ == "__main__":
    unittest.main()
