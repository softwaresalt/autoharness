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

_EXECUTION_SKILLS_A = (
    "build-feature",
    "fix-ci",
    "compact-context",
    "pr-lifecycle",
    "review",
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


class ExecutionSkillsASessionOutputContractTests(unittest.TestCase):
    def test_execution_skills_a_carry_no_remote_channel_text(self) -> None:
        for skill in _EXECUTION_SKILLS_A:
            for rel in _paths(skill):
                with self.subTest(path=rel):
                    text = _read(rel).lower()
                    self.assertNotIn("intercom", text)
                    self.assertNotIn("heartbeat", text)
                    self.assertNotIn("| event | level | message prefix |", text)
                    self.assertNotIn("| event | trigger | broadcast format |", text)

    def test_review_skill_section_order_is_unchanged_minus_removed_section(self) -> None:
        for rel in _paths("review"):
            with self.subTest(path=rel):
                headings = [line for line in _read(rel).splitlines() if line.startswith("## ")]
                self.assertEqual(headings[0], "## Subagent Depth Constraint")
                self.assertEqual(headings[1], "## Mode Detection")
                text = _read(rel)
                self.assertIn("`.github/instructions/strict-safety.instructions.md`", text)
                self.assertIn("Report the readiness outcome and the P0-P3 finding counts in the session output", text)

    def test_fix_ci_keeps_normative_outcomes_as_session_output_reports(self) -> None:
        for rel in _paths("fix-ci"):
            with self.subTest(path=rel):
                text = _read(rel)
                self.assertIn("## Session-Output Reports", text)
                self.assertIn("Reply gate: PASS ({count} threads)", text)
                self.assertIn("### Step 6.5: Reply Gate (NON-NEGOTIABLE)", text)

    def test_pr_lifecycle_keeps_merge_approval_wait_in_session_output(self) -> None:
        for rel in _paths("pr-lifecycle"):
            with self.subTest(path=rel):
                text = _read(rel)
                self.assertIn("`PR ready — awaiting user approval`, then STOP until the operator replies", text)

    def test_compact_context_reports_summary_in_session_output(self) -> None:
        for rel in _paths("compact-context"):
            with self.subTest(path=rel):
                text = _read(rel)
                self.assertIn("Summarize in the session output:", text)
                self.assertIn("### Phase 4: Report", text)

    def test_build_feature_routes_destructive_actions_through_native_approval(self) -> None:
        text = _read("templates/skills/build-feature/SKILL.md.tmpl")
        self.assertIn("native approval path", text)
        self.assertIn("* One file change per tool call\n", text.replace("\r\n", "\n"))


if __name__ == "__main__":
    unittest.main()
