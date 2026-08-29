"""Applicability tests for pre-review detectors (149.004-T / 149.009-T)."""

from __future__ import annotations

import unittest
from pathlib import Path

from autoharness.detectors.applicability import (
    ApplicabilityContextError,
    build_applicability_context,
    context_failure_results,
    evaluate_node_applicability,
)
from autoharness.detectors.contract import (
    ApplicabilitySpec,
    NodeSpec,
    ProducerSpec,
    RemediationSpec,
    ValidatorSpec,
)
from autoharness.gates.topology import ArtifactState, ShipmentState


class _FakeReaders:
    def __init__(self, shipments, artifacts, branch="feat/157-s-s1-detector-sdk-evidence-node-contract-and-gate-pre-review-reader"):
        self._shipments = tuple(shipments)
        self._artifacts = dict(artifacts)
        self._branch = branch

    def list_shipments(self):
        return self._shipments

    def current_branch(self):
        return self._branch

    def read_artifact(self, artifact_id: str):
        return self._artifacts.get(artifact_id)


class ApplicabilityTests(unittest.TestCase):
    def _node(self, applies_when: ApplicabilitySpec) -> NodeSpec:
        return NodeSpec(
            node_id="det:D-ART/ART-01@1",
            domain="D-ART",
            detector_id="ART-01",
            version="1",
            applies_when=applies_when,
            producer=ProducerSpec(kind="pure", ref="autoharness.detectors.art.section_markers:produce"),
            validator=ValidatorSpec(ref="autoharness.detectors.art.section_markers:validate"),
            severity="medium",
            remediation=RemediationSpec(class_name="guided_fix", authority="stage"),
        )

    def test_builds_context_once_and_honors_changed_paths_matching(self) -> None:
        calls = {"resolve": 0, "discover": 0, "profile": 0, "readers": 0}
        shipment = ShipmentState("157-S", title="S1", live_status="active", manifest_item_ids=("149.001-T",))
        artifacts = {"149.001-T": ArtifactState("149.001-T", artifact_type="task", live_status="active")}

        def resolve(ref: str, *, cwd=None, runner=None):
            calls["resolve"] += 1
            return {"main": "a" * 40, "HEAD": "b" * 40}[ref]

        def discover(base: str, head: str, *, cwd=None):
            calls["discover"] += 1
            self.assertEqual(base, "a" * 40)
            self.assertEqual(head, "b" * 40)
            return [".backlogit/queue/149.001-T.md"]

        def profile_loader(path: Path):
            calls["profile"] += 1
            return {"runtime_surfaces": {"cli": True, "web_ui": False}}

        def readers_factory(_workspace: Path):
            calls["readers"] += 1
            return _FakeReaders((shipment,), artifacts)

        context = build_applicability_context(
            base="main",
            head="HEAD",
            cwd=Path("."),
            resolve_ref=resolve,
            discover=discover,
            profile_loader=profile_loader,
            readers_factory=readers_factory,
        )
        node = self._node(ApplicabilitySpec(changed_paths_any=(".backlogit/**",), workspace_surfaces_any=("cli",)))
        self.assertIsNone(evaluate_node_applicability(node, context))
        self.assertEqual(calls, {"resolve": 2, "discover": 1, "profile": 1, "readers": 1})

    def test_context_failure_results_are_insufficient_evidence(self) -> None:
        node = self._node(ApplicabilitySpec(changed_paths_any=(".backlogit/**",)))
        with self.assertRaises(ApplicabilityContextError):
            build_applicability_context(
                base="main",
                head="HEAD",
                resolve_ref=lambda ref, **_kwargs: None if ref == "main" else "b" * 40,
                discover=lambda *args, **kwargs: [],
                profile_loader=lambda _path: {"runtime_surfaces": {"cli": True}},
                readers_factory=lambda _workspace: _FakeReaders((), {}),
            )
        result = context_failure_results((node,), "base ref could not be resolved")[0]
        self.assertEqual(result.status, "insufficient_evidence")
        self.assertNotEqual(result.status, "not_applicable")

    def test_not_applicable_records_excluded_by_clause(self) -> None:
        shipment = ShipmentState("157-S", title="S1", live_status="active", manifest_item_ids=("149.001-T",))
        artifacts = {"149.001-T": ArtifactState("149.001-T", artifact_type="task", live_status="active")}
        context = build_applicability_context(
            base="main",
            head="HEAD",
            resolve_ref=lambda ref, **_kwargs: {"main": "a" * 40, "HEAD": "b" * 40}[ref],
            discover=lambda *args, **kwargs: ["docs/readme.md"],
            profile_loader=lambda _path: {"runtime_surfaces": {"cli": True}},
            readers_factory=lambda _workspace: _FakeReaders((shipment,), artifacts),
        )
        node = self._node(ApplicabilitySpec(changed_paths_any=(".backlogit/**",)))
        result = evaluate_node_applicability(node, context)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, "not_applicable")
        self.assertEqual(result.excluded_by, "changed_paths_any")


if __name__ == "__main__":
    unittest.main()
