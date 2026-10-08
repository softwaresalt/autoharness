"""U6 (161.004-T): single-source contract guard and dogfood-parity guard for the
shipment-reconcile Member-Class Status Contract (161-F / 169-S).

The defect this shipment fixes had a generative cause: one status rule stated
independently in two places, which then drifted apart. These guards keep the fix
from re-creating that condition:

* **Single source.** The member-class status rules — the declared-status rule
  (R-1) and the member-class table — are stated in exactly one place, the
  marker-bounded Member-Class Status Contract block. The Output classification
  table, Pre-Mode step 3, Safe-Close Step 0(b) and the Cascade Close
  Sub-Procedure *reference* the block by name instead of restating it.
  (The 147-F-pinned consequence sentence — an archive-resident ``done`` record
  is not truly archived — is an application of the rule to the two-set gate and
  is deliberately left where 147-F pins it.)
* **Two-sided placeholder parity (H-3).** The resolved skill carries zero
  unresolved ``{{...}}`` placeholders, and the template carries zero literal
  ``.backlogit`` directory references.
* **Section parity, and the edit-mechanism arbiter (P2-5).** Every section this
  shipment touches renders from the template to exactly the resolved copy's
  text. The pair is hand-edited in parallel; if a regeneration step is ever
  introduced, or a hand-edit lands on one side only, this fails loudly rather
  than letting one copy silently discard the other's edit. Whole-file parity is
  intentionally not asserted: the template generalises some workspace-specific
  evidence (commit SHAs, stash IDs) that the resolved copy cites verbatim.

``unittest`` only (097-S canonical gate).
"""

from __future__ import annotations

import re
import unittest

import _member_class_contract as mcc

_RULE_SENTENCE = "never inferred from, nor substituted by"
_LOCATION_ALONE = "location alone is never sufficient"
_TABLE_HEADER = "| Member class |"
_CONTRACT_REFERENCE = "Member-Class Status Contract"

#: (label, start anchor, end anchor) for every region this shipment edits.
_TOUCHED_SECTIONS = (
    ("when-to-use", "## When to Use", "## Inputs"),
    ("inputs", "## Inputs", "## Output"),
    ("output-and-contract", "## Output", "### Shipment-Record-Status Classification"),
    ("recommendation-list", "The report ends with a `recommendation`:", "### Mixed-Role Detection Classification"),
    ("pre-mode", "### Pre-Mode", "### Post-Mode"),
    ("safe-close-step-0b", "b. **Snapshot pre-close", "c. **Classify the close path**"),
    ("safe-close-step-0c-agreement", "**Pre-Mode step 2b agreement check.**", "* **CASCADE selected**"),
    (
        "cascade-pre-archived-preamble",
        "**Pre-archived manifest members",
        "**`archived_ids` is a transition log",
    ),
    (
        "cascade-step-3",
        "3. **Verify `archived_ids` against",
        "4. **Verify no `parent_id` was cleared**",
    ),
    ("scenario-matrix", "## Deterministic Safe-Close Scenario Matrix", "## Quality Criteria"),
    ("quality-criteria", "## Quality Criteria", "## Related Artifacts"),
    ("related-artifacts", "## Related Artifacts", "## Model Routing"),
)

_ALLOWED_PLACEHOLDER = re.compile(r"^\{\{(STATUS|OP|BACKLOG_DIRECTORY|SUFFIX)[A-Z_]*\}\}$")


def _outside_block(text: str) -> str:
    begin = text.index(mcc.BLOCK_BEGIN)
    end = text.index(mcc.BLOCK_END) + len(mcc.BLOCK_END)
    return text[:begin] + text[end:]


class SingleSourceContractTests(unittest.TestCase):
    def test_exactly_one_contract_block(self) -> None:
        for label, text in mcc.sources():
            with self.subTest(source=label):
                self.assertEqual(text.count(mcc.BLOCK_BEGIN), 1)
                self.assertEqual(text.count(mcc.BLOCK_END), 1)
                self.assertLess(text.index(mcc.BLOCK_BEGIN), text.index(mcc.BLOCK_END))

    def test_declared_status_rule_is_stated_only_inside_the_block(self) -> None:
        for label, text in mcc.sources():
            flat = mcc.flatten(text)
            with self.subTest(source=label):
                self.assertEqual(flat.count(_RULE_SENTENCE), 1)
                self.assertEqual(flat.lower().count(_LOCATION_ALONE), 1)
                block = mcc.flatten(mcc.extract_contract_block(text))
                self.assertIn(_RULE_SENTENCE, block)
                self.assertIn(_LOCATION_ALONE, block.lower())

    def test_member_class_table_is_stated_only_inside_the_block(self) -> None:
        for label, text in mcc.sources():
            with self.subTest(source=label):
                self.assertEqual(text.count(_TABLE_HEADER), 1)
                self.assertIn(_TABLE_HEADER, mcc.extract_contract_block(text))
                outside = _outside_block(text)
                self.assertNotIn("| `qualifying-feature` |", outside)
                self.assertNotIn("| `strict-scalar` |", outside)

    def test_dependent_sites_reference_the_block_by_name(self) -> None:
        for label, text in mcc.sources():
            for site, start, end in (
                ("output-table", "Every item in the manifest is classified as one of:", "> Classification semantics"),
                ("pre-mode-step-3", "3. **Check each manifest item**", "4. **Orphan scan**"),
                ("safe-close-step-0b", "b. **Snapshot pre-close", "c. **Classify the close path**"),
                (
                    "cascade-pre-archived-preamble",
                    "**Pre-archived manifest members",
                    "**`archived_ids` is a transition log",
                ),
                ("cascade-step-3", "3. **Verify `archived_ids` against", "4. **Verify no `parent_id` was cleared**"),
            ):
                with self.subTest(source=label, site=site):
                    region = mcc.flatten(mcc.section(text, start, end))
                    self.assertIn(_CONTRACT_REFERENCE, region)

    def test_output_table_lists_the_anomaly_label_and_counts_agree(self) -> None:
        for label, text in mcc.sources():
            table = mcc.section(text, "Every item in the manifest is classified as one of:", "> Classification semantics")
            rows = [line for line in table.splitlines() if line.startswith("| `")]
            with self.subTest(source=label):
                self.assertIn(f"| `{mcc.ANOMALY}` |", table)
                self.assertEqual(len(rows), 6)
                self.assertNotIn("five per-item classifications", text)
                quality = mcc.section(text, "## Quality Criteria", "## Related Artifacts")
                self.assertIn("All six item classifications", quality)


class DogfoodParityTests(unittest.TestCase):
    def test_resolved_copy_has_no_unresolved_placeholders(self) -> None:
        self.assertNotIn("{{", mcc.resolved_text())

    def test_template_has_no_literal_backlog_directory(self) -> None:
        offending = [
            index + 1
            for index, line in enumerate(mcc.template_text().splitlines())
            if ".backlogit" in line
        ]
        self.assertEqual(offending, [], "template must use {{BACKLOG_DIRECTORY}}")

    def test_template_placeholders_in_touched_sections_are_known_tokens(self) -> None:
        template = mcc.template_text()
        for label, start, end in _TOUCHED_SECTIONS:
            for token in re.findall(r"\{\{[^}]+\}\}", mcc.section(template, start, end)):
                with self.subTest(section=label, token=token):
                    self.assertRegex(token, _ALLOWED_PLACEHOLDER)

    def test_touched_sections_render_to_the_resolved_copy(self) -> None:
        resolved = mcc.resolved_text()
        rendered = mcc.rendered_template_text()
        for label, start, end in _TOUCHED_SECTIONS:
            with self.subTest(section=label):
                self.assertEqual(
                    mcc.section(rendered, start, end),
                    mcc.section(resolved, start, end),
                    f"{label}: template and resolved copy diverge; edit both in the same commit",
                )

    def test_contract_block_renders_to_the_resolved_block(self) -> None:
        self.assertEqual(
            mcc.extract_contract_block(mcc.rendered_template_text()),
            mcc.extract_contract_block(mcc.resolved_text()),
        )


if __name__ == "__main__":
    unittest.main()
