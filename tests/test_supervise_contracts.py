"""Tests for autoharness.supervise.contracts (118.003-T)."""

from __future__ import annotations

import unittest

from autoharness.supervise.contracts import (
    GATED_ACTION_CATALOG,
    ApprovalRequested,
    ApprovalResolved,
    CancelRequested,
    ChildExited,
    ChildOutput,
    ChildOutputUnavailable,
    ChildSpawned,
    CopilotResolved,
    FallbackPolicy,
    GatedActionSpec,
    JournalCheckpoint,
    Refuse,
    RestartExhausted,
    RestartScheduled,
    SessionPhaseChanged,
    SidecarProbed,
    UnknownGatedActionError,
    UseSafeDefault,
    get_gated_action,
)

EXPECTED_GATED_ACTION_IDS = frozenset({"session_restart", "force_unlock"})


class EventCatalogTests(unittest.TestCase):
    """Every event payload dataclass is constructible with its documented fields."""

    def test_session_phase_changed(self) -> None:
        event = SessionPhaseChanged(phase="running", previous_phase="starting")
        self.assertEqual(event.phase, "running")
        self.assertEqual(event.previous_phase, "starting")

    def test_sidecar_probed(self) -> None:
        event = SidecarProbed(name="backlogit", available=True, detail="found on PATH")
        self.assertTrue(event.available)

    def test_copilot_resolved(self) -> None:
        event = CopilotResolved(exe_path="/usr/bin/copilot", source="path_lookup")
        self.assertEqual(event.source, "path_lookup")

    def test_child_spawned(self) -> None:
        event = ChildSpawned(argv=("copilot", "--remote"), pid=1234)
        self.assertEqual(event.argv, ("copilot", "--remote"))

    def test_child_output(self) -> None:
        event = ChildOutput(stream="stdout", line="hello")
        self.assertEqual(event.stream, "stdout")

    def test_child_output_unavailable(self) -> None:
        event = ChildOutputUnavailable(reason="inherited stdio, not captured")
        self.assertIn("inherited", event.reason)

    def test_child_exited(self) -> None:
        event = ChildExited(exit_code=0)
        self.assertEqual(event.exit_code, 0)

    def test_approval_requested_and_resolved(self) -> None:
        request = ApprovalRequested(
            kind="force_unlock",
            summary="Force-remove a stale lock record",
            options=("force_unlock", "cancel"),
            default="cancel",
            timeout=30.0,
        )
        response = ApprovalResolved(
            kind="force_unlock", resolution="cancel", resolved_by="operator"
        )
        self.assertEqual(request.kind, response.kind)
        self.assertEqual(response.resolution, "cancel")

    def test_cancel_requested_default_reason(self) -> None:
        event = CancelRequested()
        self.assertEqual(event.reason, "")

    def test_restart_scheduled_and_exhausted(self) -> None:
        scheduled = RestartScheduled(attempt=1, max_attempts=3)
        exhausted = RestartExhausted(attempts=3)
        self.assertEqual(scheduled.max_attempts, 3)
        self.assertEqual(exhausted.attempts, 3)

    def test_journal_checkpoint(self) -> None:
        event = JournalCheckpoint(sequence=42, detail="checkpoint")
        self.assertEqual(event.sequence, 42)


class FallbackPolicyTests(unittest.TestCase):
    def test_use_safe_default_is_constructible(self) -> None:
        policy = UseSafeDefault("decline restart")
        self.assertIsInstance(policy, FallbackPolicy)
        self.assertIn("decline restart", policy.describe())

    def test_refuse_is_constructible(self) -> None:
        policy = Refuse()
        self.assertIsInstance(policy, FallbackPolicy)
        self.assertIn("refuse", policy.describe().lower())

    def test_exactly_two_variants_exist(self) -> None:
        # Every direct subclass of FallbackPolicy must be one of these two.
        subclasses = {cls.__name__ for cls in FallbackPolicy.__subclasses__()}
        self.assertEqual(subclasses, {"UseSafeDefault", "Refuse"})


class GatedActionCatalogTests(unittest.TestCase):
    def test_catalog_identifiers_are_exactly_the_expected_set(self) -> None:
        """Exact set equality: catches both an omission and an unannounced addition."""

        self.assertEqual(set(GATED_ACTION_CATALOG.keys()), EXPECTED_GATED_ACTION_IDS)

    def test_every_entry_has_complete_metadata(self) -> None:
        for identifier, spec in GATED_ACTION_CATALOG.items():
            self.assertEqual(spec.identifier, identifier)
            self.assertTrue(spec.summary, f"{identifier} must have a non-empty summary")
            self.assertTrue(spec.options, f"{identifier} must declare permitted options")
            self.assertGreater(spec.timeout, 0, f"{identifier} must declare a positive timeout")
            self.assertIsInstance(spec.fallback_policy, FallbackPolicy)

    def test_each_entry_has_exactly_one_fallback_policy_variant(self) -> None:
        for identifier, spec in GATED_ACTION_CATALOG.items():
            variants = [
                isinstance(spec.fallback_policy, UseSafeDefault),
                isinstance(spec.fallback_policy, Refuse),
            ]
            self.assertEqual(
                sum(variants), 1, f"{identifier} must select exactly one FallbackPolicy variant"
            )

    def test_session_restart_uses_safe_default(self) -> None:
        spec = GATED_ACTION_CATALOG["session_restart"]
        self.assertIsInstance(spec.fallback_policy, UseSafeDefault)
        self.assertIn("decline", spec.fallback_policy.reference_or_value.lower())

    def test_force_unlock_refuses(self) -> None:
        spec = GATED_ACTION_CATALOG["force_unlock"]
        self.assertIsInstance(spec.fallback_policy, Refuse)

    def test_unregistered_lookup_raises(self) -> None:
        with self.assertRaises(UnknownGatedActionError):
            get_gated_action("not_a_real_action")

    def test_get_gated_action_returns_registered_entries(self) -> None:
        for identifier in EXPECTED_GATED_ACTION_IDS:
            spec = get_gated_action(identifier)
            self.assertEqual(spec.identifier, identifier)

    def test_policy_less_entry_construction_raises(self) -> None:
        with self.assertRaises(ValueError):
            GatedActionSpec(
                identifier="unspecified_action",
                summary="An action with no fallback policy declared.",
                options=("a", "b"),
                timeout=10.0,
            )

    def test_catalog_is_immutable_mapping(self) -> None:
        with self.assertRaises(TypeError):
            GATED_ACTION_CATALOG["session_restart"] = None  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
