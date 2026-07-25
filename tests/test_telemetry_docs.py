"""Documentation coverage for telemetry ownership and adapter boundaries."""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


class TelemetryDocsTests(unittest.TestCase):
    def test_architecture_and_reference_describe_ownership_boundaries(self) -> None:
        for rel in ("docs/ARCHITECTURE.md", "docs/telemetry-reference.md"):
            text = (_ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("autoharness owns", text)
            self.assertIn("local epoch time-series", text)
            self.assertIn("backlogit", text)
            self.assertIn("traceability", text)
            self.assertIn("agent-engram", text)
            self.assertIn("structural/graph ingestion consumer", text)

    def test_reference_lists_final_contract_fields_and_lifecycle(self) -> None:
        text = (_ROOT / "docs" / "telemetry-reference.md").read_text(encoding="utf-8")
        for phrase in (
            "ExecutionEpoch v1.1",
            "ToolTelemetryEvent v1.0",
            "forward-only",
            "WorkSizingSnapshot",
            "autoharness telemetry begin",
            "autoharness telemetry record --context-ref",
            "first-write immutable",
            "payload_digest",
            "metric_sources",
            "metric_quality",
            "nullable",
            "zero counts",
            "unsized",
            "There is no `unavailable` histogram bucket",
            "cost-per-size-point",
            "unavailable",
        ):
            self.assertIn(phrase, text)

    def test_reference_documents_cross_pack_sequencing_and_deferrals(self) -> None:
        text = (_ROOT / "docs" / "telemetry-reference.md").read_text(encoding="utf-8")
        for phrase in (
            "092-S",
            "079.013-T",
            "079.014-T",
            "079.016-T",
            "079.015-T",
            "082-F",
            "084-F",
            "085-F",
            "live event model/sink/emission",
            "deferred to 084-F",
            "autoharness gate size",
            "metadata complexity/scope bucket",
            "2-hour rule",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
