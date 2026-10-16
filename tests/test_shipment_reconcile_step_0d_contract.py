"""Section-scoped contract guard for shipment-reconcile Step 0(d) / ``pre_report_path`` (171-S U4).

Reads both the resolved skill and the rendered template (``_member_class_contract.sources``).
"""

from __future__ import annotations

import unittest

import _member_class_contract as mcc

_ROUTING_BEGIN = "<!-- cascade-close-routing:BEGIN step-0c -->"
_AGREEMENT_LABEL = "**Pre-Mode step 2b agreement check.**"


def _step_0(text: str) -> str:
    return mcc.section(text, "0. **Load manifest, snapshot pre-close state", "* **CASCADE selected**")


class Step0dContractTests(unittest.TestCase):
    def test_step_0c_names_the_192f_record_as_the_pre_mutation_evidence(self) -> None:
        for label, text in mcc.sources():
            step_0 = mcc.flatten(_step_0(text))
            with self.subTest(source=label):
                self.assertIn("the Step 0(c) pre-mutation evidence record", step_0)
                self.assertIn("closure-evidence", step_0)
                self.assertIn("not provably pre-mutation", step_0)

    def test_agreement_check_is_labelled_step_0d_and_keeps_its_label(self) -> None:
        for label, text in mcc.sources():
            with self.subTest(source=label):
                self.assertEqual(text.count("**Step 0(d).**"), 1)
                self.assertEqual(text.count(_AGREEMENT_LABEL), 1)
                self.assertLess(text.index("**Step 0(d).**"), text.index(_AGREEMENT_LABEL))
                self.assertLess(text.index(_AGREEMENT_LABEL), text.index(_ROUTING_BEGIN))

    def test_inputs_declare_pre_report_path_for_safe_close_only(self) -> None:
        for label, text in mcc.sources():
            inputs = mcc.section(text, "## Inputs", "## Output")
            rows = [line for line in inputs.splitlines() if line.startswith("| `pre_report_path` |")]
            with self.subTest(source=label):
                self.assertEqual(len(rows), 1)
                row = mcc.flatten(rows[0])
                self.assertIn("`safe-close`", row)
                self.assertIn("REQUIRED", row)
                self.assertIn("within this lock hold", row)

    def test_not_applicable_is_keyed_to_the_absent_parameter(self) -> None:
        for label, text in mcc.sources():
            agreement = mcc.flatten(mcc.section(text, _AGREEMENT_LABEL, _ROUTING_BEGIN))
            with self.subTest(source=label):
                self.assertIn("`pre_report_path` absent", agreement)
                self.assertIn("`pre_report_path` present but unreadable", agreement)
                self.assertIn("RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT", agreement)
                self.assertIn("agreement-check: not-applicable", agreement)

    def test_no_stale_ship_step_5_reference(self) -> None:
        for label, text in mcc.sources():
            with self.subTest(source=label):
                self.assertNotIn("(Ship Step 5)", mcc.flatten(text))
                self.assertIn("(Ship's post-merge closure)", mcc.flatten(_step_0(text)))

    def test_matrix_and_quality_criteria_cover_the_new_behaviour(self) -> None:
        for label, text in mcc.sources():
            matrix = mcc.flatten(mcc.section(text, "## Deterministic Safe-Close Scenario Matrix", "## Quality Criteria"))
            quality = mcc.flatten(mcc.section(text, "## Quality Criteria", "## Related Artifacts"))
            with self.subTest(source=label):
                self.assertIn("not provably pre-mutation", matrix)
                for needle in (
                    "`pre_report_path` absent",
                    "`pre_report_path` present and agreeing",
                    "`pre_report_path` present and differing",
                ):
                    self.assertIn(needle, matrix)
                self.assertIn("`pre_report_path`", quality)
                self.assertIn("not provably pre-mutation", quality)

    def test_ship_agent_copies_pass_pre_report_path_to_safe_close(self) -> None:
        for path in (
            mcc.REPO_ROOT / ".github" / "agents" / "_ship.agent.md",
            mcc.REPO_ROOT / "templates" / "agents" / "_ship.agent.md.tmpl",
        ):
            with self.subTest(path=path.name):
                flat = mcc.flatten(path.read_text(encoding="utf-8"))
                self.assertIn("`pre_report_path` set to the", flat)
                self.assertIn("Step 0(d) agreement-check outcome", flat)
                self.assertNotIn("Step 0(c) agreement-check outcome", flat)

    def test_matrix_classifier_disagreement_row_uses_step_0d_naming(self) -> None:
        for label, text in mcc.sources():
            with self.subTest(source=label):
                self.assertIn("step 2b / Step 0(d) classifier disagreement", text)
                self.assertNotIn("step 2b / Step 0(c) classifier disagreement", text)

    def test_template_and_resolved_copies_agree_on_the_edited_region(self) -> None:
        (_, resolved), (_, rendered) = mcc.sources()
        self.assertEqual(
            mcc.section(resolved, "**Step 0(d).**", _ROUTING_BEGIN), mcc.section(rendered, "**Step 0(d).**", _ROUTING_BEGIN)
        )
        self.assertEqual(
            mcc.section(resolved, "## Inputs", "## Output"), mcc.section(rendered, "## Inputs", "## Output")
        )


if __name__ == "__main__":
    unittest.main()
