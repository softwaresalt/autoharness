"""Pin tests for the verified engine line and the engine-line runbook drift guard (215.002-T)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from autoharness.gates.shipment_closure import (
    VERIFIED_CASCADE_ENGINE_MINOR_LINES,
    EngineSemanticsVerdict,
    assess_cascade_engine_semantics,
)

_ROOT = Path(__file__).resolve().parents[1]
_RUNBOOK = _ROOT / "docs" / "engine-line-verification.md"
_ORCHESTRATOR = _ROOT / "templates" / "agents" / "_orchestrator.agent.md.tmpl"
_TOKEN_RE = re.compile(r"Verified engine-semantics lines:\s*`([^`]+)`")


def _assess(version: object):
    return assess_cascade_engine_semantics(
        version, probe_surface="cli", invocation_surface="cli"
    )


class EngineLinePinTests(unittest.TestCase):
    def test_verified_set_is_exactly_1_11(self) -> None:
        self.assertEqual(VERIFIED_CASCADE_ENGINE_MINOR_LINES, frozenset({(1, 11)}))

    def test_candidate_versions_assess_unverified(self) -> None:
        for version in ("1.12.0", "1.12.0-rc1", "1.11.0-829-ga623b0af", None):
            with self.subTest(version=version):
                self.assertIs(_assess(version).verdict, EngineSemanticsVerdict.UNVERIFIED)

    def test_released_1_11_is_verified(self) -> None:
        self.assertIs(_assess("1.11.0").verdict, EngineSemanticsVerdict.VERIFIED)


class RunbookDriftGuardTests(unittest.TestCase):
    def test_runbook_names_same_verified_set_as_constant(self) -> None:
        text = _RUNBOOK.read_text(encoding="utf-8")
        matches = _TOKEN_RE.findall(text)
        self.assertEqual(len(matches), 1, matches)
        lines = frozenset(
            (int(a), int(b))
            for a, b in (part.strip().split(".") for part in matches[0].split(","))
        )
        self.assertEqual(lines, VERIFIED_CASCADE_ENGINE_MINOR_LINES)

    def test_runbook_names_constant_and_gate_files(self) -> None:
        text = _RUNBOOK.read_text(encoding="utf-8")
        for needle in (
            "VERIFIED_CASCADE_ENGINE_MINOR_LINES",
            "src/autoharness/gates/shipment_closure.py",
            "templates/policies/workflow-policies.md.tmpl",
            "templates/skills/shipment-reconcile/SKILL.md.tmpl",
        ):
            self.assertIn(needle, text)

    def test_orchestrator_queue_listing_is_not_sole_eligibility_authority(self) -> None:
        text = _ORCHESTRATOR.read_text(encoding="utf-8")
        self.assertIn("not** the sole eligibility authority", text)


if __name__ == "__main__":
    unittest.main()
