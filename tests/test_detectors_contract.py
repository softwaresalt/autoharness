"""Contract tests for pre-review detector node results (149.001-T / 149.009-T)."""

from __future__ import annotations

import dataclasses
import unittest

from autoharness.detectors.contract import (
    ApplicabilitySpec,
    DETECTOR_STATUS_VALUES,
    NodeResult,
    NodeSpec,
    ProducerSpec,
    RemediationSpec,
    ValidatorSpec,
    status_exit_code,
)


def _node_spec(*, mode: str = "report_only") -> NodeSpec:
    return NodeSpec(
        node_id="det:D-ART/ART-01@1",
        domain="D-ART",
        detector_id="ART-01",
        version="1",
        applies_when=ApplicabilitySpec(changed_paths_any=(".backlogit/**",)),
        producer=ProducerSpec(kind="pure", ref="autoharness.detectors.art.section_markers:produce"),
        validator=ValidatorSpec(ref="autoharness.detectors.art.section_markers:validate"),
        severity="medium",
        mode=mode,
        remediation=RemediationSpec(class_name="guided_fix", authority="stage"),
    )


class DetectorContractTests(unittest.TestCase):
    def test_node_result_uses_one_canonical_status_field(self) -> None:
        result = NodeResult(name="det:D-ART/ART-01@1", status="passed", details={"ok": True})
        field_names = {field.name for field in dataclasses.fields(NodeResult)}
        self.assertNotIn("verdict", field_names)
        self.assertEqual(result.verdict, "passed")
        self.assertNotIn("verdict", result.to_dict())

    def test_status_vocabulary_and_exit_mapping_are_closed(self) -> None:
        self.assertEqual(
            DETECTOR_STATUS_VALUES,
            (
                "passed",
                "failed",
                "insufficient_evidence",
                "blocked_upstream",
                "not_applicable",
                "skipped",
                "waived",
                "invalid",
            ),
        )
        for status in DETECTOR_STATUS_VALUES:
            expected = 2 if status == "invalid" else 0
            self.assertEqual(status_exit_code(status), expected)
        with self.assertRaises(ValueError):
            NodeResult(name="det:D-ART/ART-01@1", status="unexpected")

    def test_node_spec_rejects_non_report_only_mode(self) -> None:
        with self.assertRaises(ValueError):
            _node_spec(mode="blocking")


if __name__ == "__main__":
    unittest.main()
