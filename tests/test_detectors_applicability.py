"""Applicability tests for pre-review detectors (149.004-T / 149.009-T)."""

from __future__ import annotations

import unittest
from pathlib import Path

from autoharness.backlog_root import BacklogUnavailableError

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

        def discover(base: str, head: str, *, cwd=None, raise_on_failure=False):
            calls["discover"] += 1
            self.assertEqual(base, "a" * 40)
            self.assertEqual(head, "b" * 40)
            self.assertTrue(raise_on_failure)
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

        class _UnavailableReaders:
            def list_shipments(self):
                raise BacklogUnavailableError(Path(".backlogit"), "required backlog directory is unavailable")

            def current_branch(self):
                return "feat/157-s-s1-detector-sdk-evidence-node-contract-and-gate-pre-review-reader"

        with self.assertRaises(ApplicabilityContextError):
            build_applicability_context(
                base="a" * 40,
                head="b" * 40,
                resolve_ref=lambda ref, **_kwargs: ref,
                discover=lambda *args, **kwargs: [],
                profile_loader=lambda _path: {"runtime_surfaces": {"cli": True}},
                readers_factory=lambda _workspace: _UnavailableReaders(),
            )
        result = context_failure_results((node,), "required backlog directory is unavailable")[0]
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

    def test_missing_manifest_artifact_fails_closed_instead_of_silently_skipping(self) -> None:
        shipment = ShipmentState(
            "157-S", title="S1", live_status="active", manifest_item_ids=("149.001-T", "149.999-T")
        )
        artifacts = {"149.001-T": ArtifactState("149.001-T", artifact_type="task", live_status="active")}
        with self.assertRaises(ApplicabilityContextError):
            build_applicability_context(
                base="main",
                head="HEAD",
                resolve_ref=lambda ref, **_kwargs: {"main": "a" * 40, "HEAD": "b" * 40}[ref],
                discover=lambda *args, **kwargs: [],
                profile_loader=lambda _path: {"runtime_surfaces": {"cli": True}},
                readers_factory=lambda _workspace: _FakeReaders((shipment,), artifacts),
            )

    def test_real_load_workspace_profile_raises_on_malformed_yaml(self) -> None:
        import tempfile

        from autoharness.detectors.applicability import _load_workspace_profile

        repo_root = Path(__file__).resolve().parents[1]
        temp_root = repo_root / ".test-output"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as tmp:
            profile_path = Path(tmp) / "workspace-profile.yaml"
            profile_path.write_text("runtime_surfaces: [unterminated\n", encoding="utf-8")
            with self.assertRaises(ApplicabilityContextError):
                _load_workspace_profile(profile_path)

    def test_context_threads_resolved_workspace_to_produce_callers(self) -> None:
        shipment = ShipmentState("157-S", title="S1", live_status="active", manifest_item_ids=("149.001-T",))
        artifacts = {"149.001-T": ArtifactState("149.001-T", artifact_type="task", live_status="active")}
        context = build_applicability_context(
            base="main",
            head="HEAD",
            cwd=Path("/some/resolved/workspace"),
            resolve_ref=lambda ref, **_kwargs: {"main": "a" * 40, "HEAD": "b" * 40}[ref],
            discover=lambda *args, **kwargs: [],
            profile_loader=lambda _path: {"runtime_surfaces": {"cli": True}},
            readers_factory=lambda _workspace: _FakeReaders((shipment,), artifacts),
        )
        self.assertEqual(context.workspace, str(Path("/some/resolved/workspace")))

    def test_diff_discovery_failure_fails_closed_instead_of_silent_empty_list(self) -> None:
        # A successful rev-parse for both refs does not guarantee the
        # triple-dot diff between them can succeed (e.g. unrelated histories
        # with no merge-base). `discover_modified_files` degrades that to an
        # empty list by default; `build_applicability_context` must opt into
        # `raise_on_failure=True` so this case fails closed to
        # `ApplicabilityContextError` rather than silently becoming
        # `modified_paths=()` (which would otherwise misreport as a false
        # `not_applicable` downstream).
        from autoharness.gates.discovery import GitDiffDiscoveryError

        shipment = ShipmentState("157-S", title="S1", live_status="active", manifest_item_ids=("149.001-T",))
        artifacts = {"149.001-T": ArtifactState("149.001-T", artifact_type="task", live_status="active")}

        def failing_discover(base: str, head: str, *, cwd=None, raise_on_failure=False):
            self.assertTrue(raise_on_failure)
            raise GitDiffDiscoveryError("git diff --name-only exited 128: unrelated histories")

        with self.assertRaises(ApplicabilityContextError):
            build_applicability_context(
                base="main",
                head="HEAD",
                resolve_ref=lambda ref, **_kwargs: {"main": "a" * 40, "HEAD": "b" * 40}[ref],
                discover=failing_discover,
                profile_loader=lambda _path: {"runtime_surfaces": {"cli": True}},
                readers_factory=lambda _workspace: _FakeReaders((shipment,), artifacts),
            )

    def test_real_discover_modified_files_raises_git_diff_discovery_error_when_opted_in(self) -> None:
        from autoharness.gates.discovery import GitDiffDiscoveryError, discover_modified_files

        sha_a = "a" * 40
        sha_b = "b" * 40

        def failing_runner(_argv, _cwd):
            return 128, "", "fatal: unrelated histories"

        with self.assertRaises(GitDiffDiscoveryError):
            discover_modified_files(sha_a, sha_b, runner=failing_runner, raise_on_failure=True)

        # Default (opt-out) behavior is unchanged: existing callers such as
        # `gates/gate.py`'s `check()` keep degrading to an empty list.
        self.assertEqual(discover_modified_files(sha_a, sha_b, runner=failing_runner), [])


if __name__ == "__main__":
    unittest.main()
