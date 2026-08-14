"""Integration tests for autoharness.supervise.app.run_session (120.004-T).

Uses FakeChildProcess (never a real subprocess for the supervised child), a
real SessionStateMachine, a real EventBus, and a real tmp-dir SessionJournal
throughout. bootstrap.py's/sidecar.py's own subprocess calls are neutralized
by pointing gh_executable/backlogit_executable/engram_executable at
nonexistent binary names so shutil.which resolves nothing and every
sidecar/token step degrades non-fatally (already independently tested in
their own unit suites) -- no real subprocess is ever spawned by this
module's own integration tests.
"""

from __future__ import annotations

import inspect
import io
import json
import sys
import tempfile
import threading
import time
import unittest
import unittest.mock as mock
from pathlib import Path
from typing import Optional

from autoharness.supervise.app import (
    _ActiveChildRef,
    _pump_child_output,
    _pump_operator_input,
    _start_output_pump,
    run_session,
)
from autoharness.supervise.contracts import (
    GATED_ACTION_CATALOG,
    ApprovalRequested,
    ApprovalResolved,
    ChildOutput,
    SessionPhaseChanged,
)
from autoharness.supervise.errors import EXIT_CODE_BY_KIND, ErrorKind
from autoharness.supervise.events import EventBus
from autoharness.supervise.locking import RECORD_RELATIVE_PATH, SessionLockRefused, SessionRecord
from autoharness.supervise.process import FakeChildProcess
from autoharness.supervise.result import SupervisorResult
from autoharness.supervise.session import Phase

_NONEXISTENT_TOOL = "autoharness-test-nonexistent-tool-xyz"

#: A deterministic, never-actually-executed Copilot CLI "path" used to make
#: resolve_copilot() succeed hermetically regardless of whether a real
#: `copilot` CLI happens to be installed/on PATH in the executing
#: environment. This repo's own CI runner (.github/workflows/ci.yml `test`
#: job) installs NO `copilot` binary, so any test that calls run_session()
#: without either (a) injecting its own child_process_factory AND patching
#: resolution, or (b) exercising the resolution-failure path on purpose,
#: must not depend on ambient PATH/COPILOT_EXE_PATH state to determine
#: whether resolve_copilot() succeeds.
_FAKE_COPILOT_EXE_PATH = "/nonexistent/autoharness-test-copilot-double"


def _sidecar_kwargs() -> dict:
    return {
        "gh_executable": _NONEXISTENT_TOOL,
        "backlogit_executable": _NONEXISTENT_TOOL,
        "engram_executable": _NONEXISTENT_TOOL,
    }


class _DeterministicCopilotResolutionMixin:
    """Mix in to make ``resolve_copilot()`` succeed deterministically.

    Every test using this mixin also injects its own
    ``child_process_factory`` (a :class:`FakeChildProcess`), so the fake
    exe path this mixin sets is composed into ``argv`` but never actually
    executed -- this is purely a resolution-hermeticity fix, not a change
    to what is spawned.
    """

    def setUp(self) -> None:
        super().setUp()  # type: ignore[misc]
        patcher = mock.patch.dict("os.environ", {"COPILOT_EXE_PATH": _FAKE_COPILOT_EXE_PATH})
        patcher.start()
        self.addCleanup(patcher.stop)  # type: ignore[attr-defined]


class AlwaysApproveApprovalService:
    """Test double that approves every gated action with its "yes" option."""

    def __init__(self) -> None:
        self.requested: list[str] = []

    def request_approval(self, identifier: str, *, interactive: bool = True, **_kw) -> ApprovalResolved:
        self.requested.append(identifier)
        spec = GATED_ACTION_CATALOG[identifier]
        # The "approve" option is always the first declared option for both
        # catalog entries today ("restart" for session_restart, "force_unlock"
        # for force_unlock).
        return ApprovalResolved(kind=identifier, resolution=spec.options[0], resolved_by="test-spy")


class AlwaysDenyApprovalService:
    """Test double that denies every gated action (second declared option)."""

    def __init__(self) -> None:
        self.requested: list[str] = []

    def request_approval(self, identifier: str, *, interactive: bool = True, **_kw) -> ApprovalResolved:
        self.requested.append(identifier)
        spec = GATED_ACTION_CATALOG[identifier]
        return ApprovalResolved(kind=identifier, resolution=spec.options[1], resolved_by="test-spy")


class RaisingApprovalService:
    """Test double whose request_approval always raises."""

    def request_approval(self, identifier: str, *, interactive: bool = True, **_kw):
        raise RuntimeError(f"approval channel unavailable for {identifier}")


class StubLock:
    """Deterministic, injectable lock double simulating contention.

    The FIRST ``acquire()`` call raises :class:`SessionLockRefused`
    unconditionally. Every subsequent call succeeds. ``record_path`` points
    at a real file the test pre-populates with a genuinely-stale
    :class:`SessionRecord` so ``locking.diagnose_liveness``/
    ``force_unlock`` behave exactly as they would against a real workspace,
    without depending on real OS-level file-lock contention (which is
    racy/platform-dependent to simulate in-process).
    """

    def __init__(self, workspace_root: Path, session_id: Optional[str], record_path: Path) -> None:
        self.workspace_root = workspace_root
        self.session_id = session_id or "stub-session"
        self.record_path = record_path
        self.acquire_calls = 0
        self.released = False

    def acquire(self) -> "StubLock":
        self.acquire_calls += 1
        if self.acquire_calls == 1:
            raise SessionLockRefused("stub contention")
        return self

    def release(self) -> None:
        self.released = True


def _make_lock_factory(record_path: Path):
    def factory(workspace_root: Path, session_id: Optional[str]) -> StubLock:
        return StubLock(workspace_root, session_id, record_path)

    return factory


def _write_stale_record(record_path: Path) -> SessionRecord:
    record_path.parent.mkdir(parents=True, exist_ok=True)
    # A PID astronomically unlikely to be alive, with a start_time of 0.0 --
    # diagnose_liveness() treats an absent/dead PID as STALE.
    record = SessionRecord(pid=2**30 - 1, start_time=0.0, session_id="stale-session")
    record_path.write_text(json.dumps(record.to_dict()), encoding="utf-8")
    return record


class SignatureContractTests(unittest.TestCase):
    def test_approval_service_parameter_has_no_default(self) -> None:
        sig = inspect.signature(run_session)
        self.assertIs(sig.parameters["approval_service"].default, inspect.Parameter.empty)

    def test_omitting_approval_service_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            run_session(workspace_root=Path("."), argv=[])  # type: ignore[call-arg]


class HappyPathTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    def test_clean_exit_propagates_verbatim_and_drains_to_exited(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            fake_child = FakeChildProcess(argv=(), exit_code=0)
            bus = EventBus()
            phases: list[str] = []
            bus.subscribe(SessionPhaseChanged, lambda e: phases.append(e.phase))

            result = run_session(
                workspace_root=workspace_root,
                argv=["--some-flag"],
                approval_service=AlwaysApproveApprovalService(),
                event_bus=bus,
                child_process_factory=lambda argv: fake_child,
                **_sidecar_kwargs(),
            )

            self.assertIsInstance(result, SupervisorResult)
            self.assertEqual(result.status, "ok")
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(fake_child.spawned)
            self.assertTrue(fake_child.waited)
            self.assertIn(Phase.RUNNING.value, phases)
            self.assertIn(Phase.DRAINING.value, phases)
            self.assertIn(Phase.EXITED.value, phases)

    def test_non_zero_clean_exit_with_no_restart_budget_is_still_ok_status(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            fake_child = FakeChildProcess(argv=(), exit_code=17)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                max_restarts=0,
                child_process_factory=lambda argv: fake_child,
                **_sidecar_kwargs(),
            )

            # H3: the child's real exit code propagates verbatim even
            # though it is non-zero -- SupervisorResult.status describes
            # the SUPERVISOR's own clean completion, not the child's exit
            # code.
            self.assertEqual(result.status, "ok")
            self.assertEqual(result.exit_code, 17)

    def test_remote_cancel_uses_recovery_and_returns_cancelled(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            fake_child = FakeChildProcess(argv=(), exit_code=0)
            remote_instances: list[object] = []

            class FakeRemoteControlPlane:
                def __init__(self, **kwargs) -> None:
                    self.kwargs = kwargs
                    self.started = False
                    self.stopped = False
                    remote_instances.append(self)

                def start(self) -> None:
                    self.started = True
                    self.kwargs["on_cancel"]()

                def stop(self) -> None:
                    self.stopped = True

            result = run_session(
                workspace_root=Path(workspace),
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                child_process_factory=lambda argv: fake_child,
                remote_enabled=True,
                remote_control_plane_factory=FakeRemoteControlPlane,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "cancelled")
            self.assertTrue(fake_child.closed)
            self.assertTrue(remote_instances[0].started)
            self.assertTrue(remote_instances[0].stopped)

    def test_remote_shutdown_failure_does_not_skip_child_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            fake_child = FakeChildProcess(argv=(), exit_code=0)

            class FailingRemoteControlPlane:
                def start(self) -> None:
                    pass

                def stop(self) -> None:
                    raise RuntimeError("simulated tunnel teardown failure")

            result = run_session(
                workspace_root=Path(workspace),
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                child_process_factory=lambda argv: fake_child,
                remote_enabled=True,
                remote_control_plane_factory=lambda **_kwargs: FailingRemoteControlPlane(),
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            self.assertTrue(fake_child.closed)
            self.assertTrue(
                any("remote control-plane shutdown failed" in warning for warning in result.warnings)
            )

    def test_sidecar_degradation_is_non_fatal_and_session_still_completes(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            fake_child = FakeChildProcess(argv=(), exit_code=0)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                child_process_factory=lambda argv: fake_child,
                **_sidecar_kwargs(),  # all three tools unresolvable -> degraded/unavailable
            )

            self.assertEqual(result.status, "ok")
            self.assertEqual(result.exit_code, 0)


class DefaultChildProcessFactoryCwdTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    """120-F runtime-defect remediation (real symptom: Engram/graphtor-docs
    MCP servers, both spawned BY Copilot as local stdio children, never
    became live during a real launch). Root cause was `.mcp.json`'s use of
    an unresolved `${workspaceFolder}` placeholder (fixed separately); this
    is the reinforcing half of the fix -- when no explicit
    ``child_process_factory`` is injected, the DEFAULT factory MUST anchor
    the spawned Copilot child's own ``cwd`` to the resolved
    ``workspace_root`` (never left to inherit whatever directory the
    operator's shell happened to be in), so that any local stdio MCP server
    Copilot itself spawns -- which inherits Copilot's cwd -- resolves its
    own CWD-relative defaults (e.g. Engram's `--workspace`, graphtor-docs's
    `--config`/`--db-path`) against the real workspace.
    """

    def test_default_factory_anchors_child_cwd_to_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            captured: dict[str, object] = {}

            def fake_ctor(argv, cwd=None):
                captured["cwd"] = cwd
                return FakeChildProcess(argv=tuple(argv), exit_code=0)

            with mock.patch(
                "autoharness.supervise.app.InheritStdioChildProcess", side_effect=fake_ctor
            ):
                result = run_session(
                    workspace_root=workspace_root,
                    argv=[],
                    approval_service=AlwaysApproveApprovalService(),
                    use_pty=False,
                    **_sidecar_kwargs(),
                )

            self.assertEqual(result.status, "ok")
            self.assertEqual(captured["cwd"], str(workspace_root))

    def test_default_factory_forwards_cwd_to_pty_construction_too(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            captured: dict[str, object] = {}

            def fake_pty_factory(argv, cwd=None):
                captured["cwd"] = cwd
                return FakeChildProcess(argv=tuple(argv), exit_code=0), None

            with mock.patch(
                "autoharness.supervise.app.create_pty_or_inherited_child_process",
                side_effect=fake_pty_factory,
            ):
                result = run_session(
                    workspace_root=workspace_root,
                    argv=[],
                    approval_service=AlwaysApproveApprovalService(),
                    use_pty=True,
                    **_sidecar_kwargs(),
                )

            self.assertEqual(result.status, "ok")
            self.assertEqual(captured["cwd"], str(workspace_root))


class ResolutionFailureTests(unittest.TestCase):
    def test_unresolvable_copilot_fails_closed_before_spawn(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            spawned = {"called": False}

            def factory(argv):
                spawned["called"] = True
                return FakeChildProcess(argv=tuple(argv), exit_code=0)

            with mock.patch("autoharness.supervise.resolve.shutil.which", return_value=None):
                with mock.patch.dict("os.environ", {}, clear=False):
                    import os as os_mod

                    os_mod.environ.pop("COPILOT_EXE_PATH", None)
                    os_mod.environ.pop("COPILOT_EXE", None)

                    result = run_session(
                        workspace_root=workspace_root,
                        argv=[],
                        approval_service=AlwaysApproveApprovalService(),
                        child_process_factory=factory,
                        **_sidecar_kwargs(),
                    )

            self.assertEqual(result.status, "failed")
            self.assertEqual(result.exit_code, EXIT_CODE_BY_KIND[ErrorKind.RESOLUTION])
            self.assertFalse(spawned["called"], "child must never be spawned when resolution fails")


class LockContentionTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    def test_contention_without_force_unlock_resolves_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            record_path = workspace_root / RECORD_RELATIVE_PATH
            _write_stale_record(record_path)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                force_unlock=False,
                lock_factory=_make_lock_factory(record_path),
                child_process_factory=lambda argv: FakeChildProcess(argv=tuple(argv), exit_code=0),
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "blocked")
            self.assertEqual(result.exit_code, EXIT_CODE_BY_KIND[ErrorKind.LOCK])

    def test_contention_with_force_unlock_approved_recovers_and_completes(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            record_path = workspace_root / RECORD_RELATIVE_PATH
            _write_stale_record(record_path)
            approval_service = AlwaysApproveApprovalService()
            fake_child = FakeChildProcess(argv=(), exit_code=0)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=approval_service,
                force_unlock=True,
                non_interactive=True,
                lock_factory=_make_lock_factory(record_path),
                child_process_factory=lambda argv: fake_child,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            self.assertEqual(result.exit_code, 0)
            self.assertIn("force_unlock", approval_service.requested)

    def test_contention_with_force_unlock_denied_resolves_blocked_and_no_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            record_path = workspace_root / RECORD_RELATIVE_PATH
            _write_stale_record(record_path)
            approval_service = AlwaysDenyApprovalService()

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=approval_service,
                force_unlock=True,
                non_interactive=True,
                lock_factory=_make_lock_factory(record_path),
                child_process_factory=lambda argv: FakeChildProcess(argv=tuple(argv), exit_code=0),
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "blocked")
            self.assertEqual(result.exit_code, EXIT_CODE_BY_KIND[ErrorKind.LOCK])
            # The record must NOT have been removed (side effect skipped).
            self.assertTrue(record_path.exists())


class RestartTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    def test_approved_restart_spawns_replacement_child_and_completes(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            children = [
                FakeChildProcess(argv=(), exit_code=3),
                FakeChildProcess(argv=(), exit_code=0),
            ]
            approval_service = AlwaysApproveApprovalService()

            def factory(argv):
                return children.pop(0)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=approval_service,
                max_restarts=1,
                non_interactive=True,
                child_process_factory=factory,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            self.assertEqual(result.exit_code, 0)
            self.assertIn("session_restart", approval_service.requested)

    def test_approved_restart_does_not_signal_the_already_exited_old_child(self) -> None:
        """P-018 Copilot review finding, PR #331, comment 3778730421.

        By the time ``RestartController.attempt()`` is invoked, the OLD
        child has ALREADY exited/been reaped (its ``exit_code`` was
        obtained via ``child.wait()`` immediately above in the same loop
        iteration). Signaling an already-reaped PID risks hitting a PID
        the OS has since reused for an unrelated process. ``child=None``
        is passed to ``attempt()`` for exactly this reason; the OLD
        child's file descriptor is instead closed directly by this call
        site, without ever calling ``signal()`` on it again.
        """

        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            old_child = FakeChildProcess(argv=(), exit_code=3)
            new_child = FakeChildProcess(argv=(), exit_code=0)
            children = [old_child, new_child]
            approval_service = AlwaysApproveApprovalService()

            def factory(argv):
                return children.pop(0)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=approval_service,
                max_restarts=1,
                non_interactive=True,
                child_process_factory=factory,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            # The OLD child was never signaled (no risk of hitting a
            # reused PID) but its file descriptor was still closed.
            self.assertEqual(old_child.signals_received, [])
            self.assertTrue(old_child.closed)

    def test_declined_restart_drains_to_failed(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            fake_child = FakeChildProcess(argv=(), exit_code=9)
            approval_service = AlwaysDenyApprovalService()

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=approval_service,
                max_restarts=1,
                non_interactive=True,
                child_process_factory=lambda argv: fake_child,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "failed")
            self.assertEqual(result.exit_code, EXIT_CODE_BY_KIND[ErrorKind.RESTART])


class RestartAndCancelEventsVisibleOnBusTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    """P-018 Copilot review finding (PR #331, comment 3778121169):
    ``cancel_session``/``RestartController.attempt`` previously wrote
    cancellation/restart events directly to the journal, bypassing
    ``run_session``'s own ``_emit`` closure entirely -- so ``EventBus``
    subscribers never observed a ``RestartScheduled``/``RestartExhausted``/
    ``CancelRequested`` event during a real end-to-end session, even though
    the journal file itself did contain them. These integration tests
    subscribe to a REAL ``EventBus`` (not a spy in place of recovery.py's
    internals) and drive a real ``run_session`` restart/cancellation flow,
    proving the fix end-to-end rather than only at the recovery.py-unit
    level.
    """

    def test_approved_restart_scheduled_event_is_observed_on_the_bus(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            bus = EventBus()
            observed: list = []
            bus.subscribe(lambda _event: True, observed.append)
            children = [
                FakeChildProcess(argv=(), exit_code=3),
                FakeChildProcess(argv=(), exit_code=0),
            ]

            def factory(argv):
                return children.pop(0)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                event_bus=bus,
                max_restarts=1,
                non_interactive=True,
                child_process_factory=factory,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            event_types = [type(event).__name__ for event in observed]
            self.assertIn(
                "RestartScheduled",
                event_types,
                "RestartController.attempt() must route RestartScheduled through "
                "run_session's _emit so EventBus subscribers observe it",
            )

    def test_restart_exhaustion_event_is_observed_on_the_bus(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            bus = EventBus()
            observed: list = []
            bus.subscribe(lambda _event: True, observed.append)
            fake_child = FakeChildProcess(argv=(), exit_code=9)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysDenyApprovalService(),
                event_bus=bus,
                max_restarts=1,
                non_interactive=True,
                child_process_factory=lambda argv: fake_child,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "failed")
            event_types = [type(event).__name__ for event in observed]
            self.assertIn(
                "RestartExhausted",
                event_types,
                "RestartController.attempt()'s exhaustion branch must route "
                "RestartExhausted through run_session's _emit so EventBus "
                "subscribers observe it",
            )


class NegativeControlTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    def test_raising_approval_service_never_performs_force_unlock_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            record_path = workspace_root / RECORD_RELATIVE_PATH
            _write_stale_record(record_path)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=RaisingApprovalService(),
                force_unlock=True,
                non_interactive=True,
                lock_factory=_make_lock_factory(record_path),
                child_process_factory=lambda argv: FakeChildProcess(argv=tuple(argv), exit_code=0),
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "blocked")
            self.assertTrue(record_path.exists(), "the raising approval service must never allow force_unlock's side effect")

    def test_raising_approval_service_never_performs_restart_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            fake_child = FakeChildProcess(argv=(), exit_code=9)
            spawn_count = {"n": 0}

            def factory(argv):
                spawn_count["n"] += 1
                return fake_child

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=RaisingApprovalService(),
                max_restarts=1,
                non_interactive=True,
                child_process_factory=factory,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "failed")
            self.assertEqual(spawn_count["n"], 1, "a replacement child must never be spawned")

    def test_deliberately_unwired_fixture_is_caught_by_exact_set_equality_check(self) -> None:
        """Meta-test: proves the exact-set-equality assertion style used in
        MandatoryDispatchTests below is capable of detecting a defect where
        an orchestrator forgets to dispatch one catalog action."""

        def deliberately_unwired_orchestrator(approval_service) -> list[str]:
            # Intentionally dispatches ONLY "force_unlock", never
            # "session_restart" -- simulating the exact defect class this
            # test proves is detectable.
            approval_service.request_approval("force_unlock", interactive=False)
            return list(getattr(approval_service, "requested", []))

        spy = AlwaysApproveApprovalService()
        dispatched = deliberately_unwired_orchestrator(spy)
        with self.assertRaises(AssertionError):
            self.assertEqual(set(dispatched), set(GATED_ACTION_CATALOG.keys()))


class MandatoryDispatchTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    def test_both_catalog_actions_dispatched_in_one_scenario(self) -> None:
        """Exercises BOTH gated actions in a single run_session call and
        asserts exact-set equality against GATED_ACTION_CATALOG's keys, in
        both directions."""

        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            record_path = workspace_root / RECORD_RELATIVE_PATH
            _write_stale_record(record_path)
            approval_service = AlwaysApproveApprovalService()
            children = [
                FakeChildProcess(argv=(), exit_code=5),
                FakeChildProcess(argv=(), exit_code=0),
            ]

            def factory(argv):
                return children.pop(0)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=approval_service,
                force_unlock=True,
                max_restarts=1,
                non_interactive=True,
                lock_factory=_make_lock_factory(record_path),
                child_process_factory=factory,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(set(approval_service.requested), set(GATED_ACTION_CATALOG.keys()))
            self.assertEqual(sorted(approval_service.requested), sorted(GATED_ACTION_CATALOG.keys()))


class ApprovalRequestedEventEmissionTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    """P-018 Copilot review finding, PR #331: run_session previously
    dispatched straight from catalog lookup to
    ``approval_service.request_approval(...)`` and journaled only the
    ``ApprovalResolved`` response, leaving the EventBus/journal without the
    request metadata (``summary``, ``options``, ``default``, ``timeout``)
    documented in the event catalog. Both gated-action call sites must now
    emit an ``ApprovalRequested`` event (on both the bus AND the journal)
    immediately before blocking for input."""

    def test_force_unlock_emits_approval_requested_before_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            record_path = workspace_root / RECORD_RELATIVE_PATH
            _write_stale_record(record_path)
            bus = EventBus()
            kinds: list[type] = []
            bus.subscribe(ApprovalRequested, lambda e: kinds.append(type(e)))
            bus.subscribe(ApprovalResolved, lambda e: kinds.append(type(e)))

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                force_unlock=True,
                non_interactive=True,
                event_bus=bus,
                lock_factory=_make_lock_factory(record_path),
                child_process_factory=lambda argv: FakeChildProcess(argv=tuple(argv), exit_code=0),
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            self.assertEqual(kinds, [ApprovalRequested, ApprovalResolved])

    def test_session_restart_emits_approval_requested_before_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            children = [
                FakeChildProcess(argv=(), exit_code=3),
                FakeChildProcess(argv=(), exit_code=0),
            ]
            bus = EventBus()
            kinds: list[type] = []
            bus.subscribe(ApprovalRequested, lambda e: kinds.append(type(e)))
            bus.subscribe(ApprovalResolved, lambda e: kinds.append(type(e)))

            def factory(argv):
                return children.pop(0)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                max_restarts=1,
                non_interactive=True,
                event_bus=bus,
                child_process_factory=factory,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            self.assertEqual(kinds, [ApprovalRequested, ApprovalResolved])


class BootstrapEnvironRestorationTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    """P-018 Copilot review finding, PR #331: applying bootstrap-resolved
    additions (which may include a real GitHub token) to this process's own
    ``os.environ`` must never outlive a single ``run_session()`` call -- the
    prior implementation mutated ``os.environ`` permanently with no
    restoration, leaking one workspace's secrets/bootstrap paths into later
    sessions or unrelated library callers sharing the same process."""

    def test_bootstrap_env_addition_is_restored_after_run_session_returns(self) -> None:
        import os as os_mod

        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            sentinel_var = "AUTOHARNESS_TEST_BOOTSTRAP_ENV_LEAK_SENTINEL"
            self.assertNotIn(sentinel_var, os_mod.environ)
            (workspace_root / ".env.local").write_text(
                f"{sentinel_var}=leaked-value\n", encoding="utf-8"
            )

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                child_process_factory=lambda argv: FakeChildProcess(argv=tuple(argv), exit_code=0),
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            self.assertNotIn(
                sentinel_var,
                os_mod.environ,
                "a .env.local-resolved addition must not outlive run_session()",
            )


class EnvironMutationSerializationTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    """P-018 Copilot review finding (PR #331, comment 3778273440):
    snapshotting and restoring ``os.environ`` around a single
    ``run_session`` call does not by itself make that mutation
    concurrency-safe -- workspace locks are per-workspace, so TWO
    ``run_session`` calls for TWO DIFFERENT workspaces can legitimately run
    concurrently in the same process. Proves ``_ENVIRON_MUTATION_LOCK``
    actually serializes their environment-mutation windows: while one call
    is still "running" (its child hasn't exited yet), a concurrent call for
    a different workspace must not have applied its own bootstrap-resolved
    environment yet, and once both complete neither leaves a trace in
    ``os.environ``.
    """

    def test_two_concurrent_run_session_calls_never_interleave_environ_mutation(
        self,
    ) -> None:
        import os as os_mod

        spawned_event = threading.Event()
        proceed_event = threading.Event()

        class _BlockingChildProcess:
            """Stays 'running' until the test explicitly releases it,
            simulating a long-lived Copilot child so the test can observe
            _ENVIRON_MUTATION_LOCK actually being held for the mutation's
            full lifetime, not just around the brief `os.environ.update`
            call itself."""

            supports_output_capture = False
            pid = 4242

            def spawn(self) -> None:
                spawned_event.set()

            def wait(self, timeout: Optional[float] = None) -> int:
                proceed_event.wait(timeout=10.0)
                return 0

            def close(self) -> None:
                pass

            def signal(self, sig: int) -> None:
                pass

        sentinel_a = "AUTOHARNESS_TEST_ENV_LOCK_SENTINEL_A"
        sentinel_b = "AUTOHARNESS_TEST_ENV_LOCK_SENTINEL_B"
        self.assertNotIn(sentinel_a, os_mod.environ)
        self.assertNotIn(sentinel_b, os_mod.environ)

        with tempfile.TemporaryDirectory() as workspace_a, tempfile.TemporaryDirectory() as workspace_b:
            root_a = Path(workspace_a)
            root_b = Path(workspace_b)
            (root_a / ".env.local").write_text(f"{sentinel_a}=a-value\n", encoding="utf-8")
            (root_b / ".env.local").write_text(f"{sentinel_b}=b-value\n", encoding="utf-8")

            results: dict[str, Any] = {}

            def _run_a() -> None:
                results["a"] = run_session(
                    workspace_root=root_a,
                    argv=[],
                    approval_service=AlwaysApproveApprovalService(),
                    child_process_factory=lambda argv: _BlockingChildProcess(),
                    **_sidecar_kwargs(),
                )

            def _run_b() -> None:
                results["b"] = run_session(
                    workspace_root=root_b,
                    argv=[],
                    approval_service=AlwaysApproveApprovalService(),
                    child_process_factory=lambda argv: FakeChildProcess(
                        argv=tuple(argv), exit_code=0, supports_output_capture=False
                    ),
                    **_sidecar_kwargs(),
                )

            thread_a = threading.Thread(target=_run_a, daemon=True)
            thread_a.start()

            # Wait until A has definitely applied its own environ mutation
            # and spawned its (indefinitely-blocking) child.
            self.assertTrue(spawned_event.wait(timeout=5.0), "thread A never reached spawn()")
            self.assertIn(sentinel_a, os_mod.environ)

            thread_b = threading.Thread(target=_run_b, daemon=True)
            thread_b.start()

            # Give B ample opportunity to race ahead if the lock did NOT
            # serialize these two calls -- B's own bootstrap/env-mutation
            # phase has nothing else to block on for a different workspace.
            time.sleep(0.3)
            self.assertNotIn(
                sentinel_b,
                os_mod.environ,
                "B must not have applied its own environ mutation while A "
                "still holds _ENVIRON_MUTATION_LOCK -- the two calls raced "
                "instead of serializing",
            )

            # Release A -- its child now exits, A restores its snapshot and
            # releases the lock, letting B proceed and complete quickly.
            proceed_event.set()
            thread_a.join(timeout=5.0)
            thread_b.join(timeout=5.0)

            self.assertFalse(thread_a.is_alive())
            self.assertFalse(thread_b.is_alive())
            self.assertEqual(results["a"].status, "ok")
            self.assertEqual(results["b"].status, "ok")
            self.assertNotIn(sentinel_a, os_mod.environ)
            self.assertNotIn(sentinel_b, os_mod.environ)


class EnvironLockCoversBootstrapReadTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    """P-018 Copilot review finding, PR #331, comment 3778730372.

    ``_ENVIRON_MUTATION_LOCK`` was previously acquired only around the
    ``os.environ.update()`` APPLY step, but ``bootstrap_workspace()``
    (called with no explicit ``env=``) reads its OWN baseline via an
    internal ``dict(os.environ)`` snapshot -- an unsynchronized read that
    could observe a concurrent call's still-applied mutation and
    misinterpret it as this call's own NO-CLOBBER preset. Proves the lock
    is now held for the ENTIRE ``bootstrap_workspace()`` call, not just the
    later apply step.
    """

    def test_bootstrap_workspace_is_called_while_environ_lock_already_held(self) -> None:
        from autoharness.supervise import app as app_mod

        observed_locked: list[bool] = []
        real_bootstrap_workspace = app_mod.bootstrap_mod.bootstrap_workspace

        def _spy(*args, **kwargs):
            observed_locked.append(app_mod._ENVIRON_MUTATION_LOCK.locked())
            return real_bootstrap_workspace(*args, **kwargs)

        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            with mock.patch.object(
                app_mod.bootstrap_mod, "bootstrap_workspace", side_effect=_spy
            ):
                result = run_session(
                    workspace_root=workspace_root,
                    argv=[],
                    approval_service=AlwaysApproveApprovalService(),
                    child_process_factory=lambda argv: FakeChildProcess(
                        argv=tuple(argv), exit_code=0, supports_output_capture=False
                    ),
                    **_sidecar_kwargs(),
                )

        self.assertEqual(result.status, "ok")
        self.assertEqual(observed_locked, [True])
        # The lock must not leak held past this run_session() call.
        self.assertFalse(app_mod._ENVIRON_MUTATION_LOCK.locked())


class H2FailClosedNonInteractiveTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    def test_session_restart_falls_back_to_declared_fallback_when_non_interactive(self) -> None:
        """Integration-level (not approvals.py-unit-level) H2 check: a REAL
        ConsoleApprovalService, run non-interactively end-to-end, must
        resolve the session_restart gated action to the catalog's declared
        UseSafeDefault fallback ("decline"), which recovery.py then treats
        as a declined restart -- draining to FAILED."""

        from autoharness.supervise.approvals import ConsoleApprovalService

        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            fake_child = FakeChildProcess(argv=(), exit_code=9)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=ConsoleApprovalService(),
                max_restarts=1,
                non_interactive=True,
                child_process_factory=lambda argv: fake_child,
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "failed")
            self.assertEqual(result.exit_code, EXIT_CODE_BY_KIND[ErrorKind.RESTART])

            # Confirm the auto-resolution was journaled (auto-resolved, not
            # "operator").
            sessions_root = workspace_root / ".autoharness" / "sessions"
            self.assertTrue(sessions_root.exists())
            session_dirs = list(sessions_root.iterdir())
            self.assertEqual(len(session_dirs), 1)
            journal_path = session_dirs[0] / "journal.jsonl"
            lines = journal_path.read_text(encoding="utf-8").splitlines()
            records = [json.loads(line) for line in lines if line.strip()]
            approval_resolved_records = [r for r in records if r.get("kind") == "ApprovalResolved"]
            self.assertTrue(any(r.get("resolved_by") == "fallback_policy" for r in approval_resolved_records))

    def test_force_unlock_falls_back_to_refused_when_non_interactive(self) -> None:
        from autoharness.supervise.approvals import ConsoleApprovalService

        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            record_path = workspace_root / RECORD_RELATIVE_PATH
            _write_stale_record(record_path)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=ConsoleApprovalService(),
                force_unlock=True,
                non_interactive=True,
                lock_factory=_make_lock_factory(record_path),
                child_process_factory=lambda argv: FakeChildProcess(argv=tuple(argv), exit_code=0),
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "blocked")
            self.assertEqual(result.exit_code, EXIT_CODE_BY_KIND[ErrorKind.LOCK])
            self.assertTrue(record_path.exists(), "REFUSED resolution must never remove the record")


class H8PureCompositionTests(unittest.TestCase):
    def test_module_does_not_import_forbidden_low_level_primitives_directly(self) -> None:
        """Sanity check that app.py composes existing modules rather than
        reimplementing subprocess spawning itself (H8: pure composition)."""

        import autoharness.supervise.app as app_mod

        source = inspect.getsource(app_mod)
        self.assertNotIn("subprocess.Popen(", source)
        self.assertNotIn("shell=True", source)


@unittest.skipUnless(sys.platform != "win32", "real-executable fake sidecars use POSIX shebang scripts")
class SidecarPreflightBeforeCopilotLaunchSmokeTests(unittest.TestCase):
    """Controlled end-to-end smoke test (120-F runtime-defect remediation,
    item 7): proves ALL THREE preflight sidecars (backlogit, Engram,
    graphtor-docs) are actually invoked via REAL subprocess execution of
    fake executables -- not merely mocked -- and reach an "ok" readiness
    outcome BEFORE the (still-faked, per this module's own test
    convention) Copilot child ever spawns. Each fake executable is a real,
    independently executable script (never network-dependent, never
    touching any real external installation) that appends its own name to
    a shared, workspace-local order-log file the moment it runs.
    """

    def test_all_three_sidecars_invoked_and_ok_before_copilot_spawn(self) -> None:
        import os
        import stat

        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)
            bin_dir = workspace_root / "fake-bin"
            bin_dir.mkdir()
            order_log = workspace_root / "order.log"

            def _install_fake(name: str) -> Path:
                script = bin_dir / name
                script.write_text(
                    "#!/bin/sh\n"
                    f'echo "{name}" >> "{order_log}"\n'
                    "exit 0\n",
                    encoding="utf-8",
                )
                script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                return script

            _install_fake("backlogit")
            _install_fake("engram")
            _install_fake("graphtor-docs")
            # A fake `copilot` on PATH too: this repo's own CI runner
            # installs no real `copilot` CLI, so resolve_copilot()'s
            # shutil.which("copilot") must not depend on one being
            # ambiently present. The actual spawn below is still faked via
            # `copilot_factory`, so this script is composed into argv but
            # never executed.
            _install_fake("copilot")

            original_path = os.environ.get("PATH", "")
            spawn_marker: dict[str, object] = {}

            def copilot_factory(argv):
                order_log.write_text(
                    (order_log.read_text(encoding="utf-8") if order_log.exists() else "")
                    + "copilot\n",
                    encoding="utf-8",
                )
                spawn_marker["spawned"] = True
                return FakeChildProcess(argv=tuple(argv), exit_code=0)

            with mock.patch.dict(os.environ, {"PATH": f"{bin_dir}{os.pathsep}{original_path}"}):
                result = run_session(
                    workspace_root=workspace_root,
                    argv=[],
                    approval_service=AlwaysApproveApprovalService(),
                    child_process_factory=copilot_factory,
                    gh_executable=_NONEXISTENT_TOOL,
                    backlogit_executable="backlogit",
                    engram_executable="engram",
                    graphtor_docs_executable="graphtor-docs",
                )

            self.assertEqual(result.status, "ok")
            self.assertTrue(spawn_marker.get("spawned"))
            self.assertTrue(order_log.exists())
            lines = order_log.read_text(encoding="utf-8").splitlines()
            self.assertIn("copilot", lines)
            self.assertLess(
                lines.index("backlogit"),
                lines.index("copilot"),
                "backlogit preflight must complete before the Copilot child spawns",
            )
            self.assertLess(
                lines.index("engram"),
                lines.index("copilot"),
                "Engram preflight must complete before the Copilot child spawns",
            )
            # P-018 Copilot review finding, PR #331: the prior version of
            # this smoke test never actually asserted graphtor-docs was
            # invoked at all -- only backlogit/Engram were checked, so a
            # regression that stopped graphtor-docs from resolving/running
            # (sidecar failures are always non-fatal, so `result.status`
            # alone would never catch this) would still pass silently.
            self.assertIn(
                "graphtor-docs",
                lines,
                "graphtor-docs preflight must actually run (not silently skipped)",
            )
            self.assertLess(
                lines.index("graphtor-docs"),
                lines.index("copilot"),
                "graphtor-docs preflight must complete before the Copilot child spawns",
            )


class PtyPumpDirectUnitTests(unittest.TestCase):
    """Direct, synchronous (non-threaded) unit tests for the bidirectional
    PTY I/O pump helpers introduced to fix a P-018 Copilot review finding
    (PR #331, comment 3777840441): the supervisor previously blocked in
    ``child.wait()`` without ever draining ``child.read()`` or forwarding
    operator input via ``child.write()``, so a PTY-backed interactive
    Copilot session's output was invisible and its prompts could never
    receive input. Calling the pump functions directly (not through the
    daemon-thread wiring in :func:`_start_output_pump`) keeps these
    assertions deterministic and free of timing races.
    """

    def test_pump_child_output_drains_every_chunk_writes_to_stream_and_emits_events(
        self,
    ) -> None:
        child = FakeChildProcess(argv=(), scripted_stdout=["first\n", "second\n"])
        child.spawn()
        captured_events: list[ChildOutput] = []
        out = io.StringIO()

        with mock.patch.object(sys, "stdout", out):
            _pump_child_output(child, captured_events.append)

        self.assertEqual(out.getvalue(), "first\nsecond\n")
        self.assertEqual([e.line for e in captured_events], ["first\n", "second\n"])
        self.assertTrue(all(e.stream == "stdout" for e in captured_events))

    def test_pump_child_output_returns_on_read_exception_without_propagating(self) -> None:
        class _RaisingReadChild:
            supports_output_capture = True

            def read(self) -> Optional[str]:
                raise OSError("pty gone")

        captured: list = []

        # Must return quietly rather than raising into the caller (a
        # background daemon thread has no caller to propagate into).
        _pump_child_output(_RaisingReadChild(), captured.append)

        self.assertEqual(captured, [])

    def test_pump_child_output_survives_emit_failure_and_keeps_draining(self) -> None:
        # P-018 Copilot review finding (PR #331, comment 3778273465): a
        # raising `emit` (journal I/O error, raising EventBus subscriber)
        # previously terminated the WHOLE pump thread -- the exact
        # PTY-buffer-fills-and-the-child-deadlocks failure mode this pump
        # exists to prevent, just moved one layer down. Proves draining
        # continues across an emit failure, and the failure is reported
        # through `report_emit_failure` rather than silently discarded.
        child = FakeChildProcess(argv=(), scripted_stdout=["first\n", "second\n", "third\n"])
        child.spawn()
        out = io.StringIO()
        reported: list[str] = []

        def _raising_emit(event: ChildOutput) -> None:
            if event.line == "second\n":
                raise OSError("disk full")

        with mock.patch.object(sys, "stdout", out):
            _pump_child_output(child, _raising_emit, reported.append)

        # All three chunks still reached the real console -- the emit
        # failure on the middle chunk did not stop draining the child.
        self.assertEqual(out.getvalue(), "first\nsecond\nthird\n")
        self.assertEqual(len(reported), 1)
        self.assertIn("disk full", reported[0])

    def test_pump_child_output_swallows_a_raising_report_emit_failure_callback(self) -> None:
        # The failure-reporting channel itself must never propagate either
        # -- a buggy/raising `report_emit_failure` must not resurrect the
        # exact "pump thread dies silently" failure mode this fix exists to
        # close.
        child = FakeChildProcess(argv=(), scripted_stdout=["only\n"])
        child.spawn()
        out = io.StringIO()

        def _raising_emit(event: ChildOutput) -> None:
            raise OSError("emit boom")

        def _raising_report(message: str) -> None:
            raise RuntimeError("reporting channel boom")

        with mock.patch.object(sys, "stdout", out):
            # Must not raise.
            _pump_child_output(child, _raising_emit, _raising_report)

        self.assertEqual(out.getvalue(), "only\n")

    def test_pump_child_output_redacts_registered_secret_before_console_write(self) -> None:
        # P-018 Copilot review finding (PR #331, comment 3778627856): the
        # console write previously ran BEFORE either redaction choke point
        # (EventBus/SessionJournal only redact the copy they deliver/
        # persist, strictly AFTER the raw chunk had already reached the
        # real console). A registered secret echoed by the child must now
        # be redacted in what actually reaches stdout.
        from autoharness.supervise.redact import register_secret

        marker = "unique-console-redaction-marker-qqq789"
        register_secret(marker)

        child = FakeChildProcess(
            argv=(), scripted_stdout=[f"before {marker} after\n", "plain line\n"]
        )
        child.spawn()
        captured_events: list[ChildOutput] = []
        out = io.StringIO()

        with mock.patch.object(sys, "stdout", out):
            _pump_child_output(child, captured_events.append)

        console_output = out.getvalue()
        self.assertNotIn(marker, console_output)
        self.assertIn("before ***REDACTED*** after\n", console_output)
        self.assertIn("plain line\n", console_output)
        # The emitted event itself still carries the RAW value: EventBus/
        # SessionJournal apply their own independent redaction to the
        # delivered/persisted copy -- this fix only closes the direct,
        # pre-redaction console-write gap, it does not change the existing
        # emit-path contract.
        self.assertEqual(captured_events[0].line, f"before {marker} after\n")

    def test_pump_operator_input_forwards_every_line_to_the_active_child(self) -> None:
        child = FakeChildProcess(argv=())
        child.spawn()
        active_ref = _ActiveChildRef(child)
        fake_stdin = io.StringIO("hello\nworld\n")

        with mock.patch.object(sys, "stdin", fake_stdin):
            _pump_operator_input(active_ref)

        self.assertEqual(child.written, [b"hello\n", b"world\n"])

    def test_pump_operator_input_survives_a_write_exception_and_keeps_reading(self) -> None:
        # P-018 Copilot review finding (PR #331, comment 3778121130): a
        # transient write failure against the CURRENT active child (e.g.
        # exactly the moment it is being replaced by a restart) must not
        # kill this session-wide persistent pump thread -- a later line
        # must still reach whatever child is active by then.
        class _RaisingWriteChild:
            def write(self, data: bytes) -> None:
                raise OSError("pty closed")

        raising_child = _RaisingWriteChild()
        active_ref = _ActiveChildRef(raising_child)
        fake_stdin = io.StringIO("dropped-line\n")

        with mock.patch.object(sys, "stdin", fake_stdin):
            # Must not raise, and must not return early -- reaches EOF and
            # returns only because the StringIO is exhausted, not because
            # the write failed.
            _pump_operator_input(active_ref)

    def test_pump_operator_input_forwards_to_repointed_child_after_restart_handoff(self) -> None:
        # P-018 Copilot review finding (PR #331, comment 3778121130): after
        # `active_ref.set(new_child)` (what a restart handoff does), the
        # SAME persistent pump thread/call must forward subsequent input to
        # the NEW child, not the old one -- proving there is exactly one
        # input reader routed to whichever child is currently active.
        old_child = FakeChildProcess(argv=())
        old_child.spawn()
        new_child = FakeChildProcess(argv=())
        new_child.spawn()
        active_ref = _ActiveChildRef(old_child)

        class _RepointingStdin:
            """Repoints active_ref to new_child after the first line, then EOFs."""

            def __init__(self) -> None:
                self._lines = iter(["first-to-old\n", "second-to-new\n", ""])

            def readline(self) -> str:
                line = next(self._lines)
                if line == "second-to-new\n":
                    active_ref.set(new_child)
                return line

        with mock.patch.object(sys, "stdin", _RepointingStdin()):
            _pump_operator_input(active_ref)

        self.assertEqual(old_child.written, [b"first-to-old\n"])
        self.assertEqual(new_child.written, [b"second-to-new\n"])


class StartOutputPumpTests(unittest.TestCase):
    """Integration-level tests for :func:`_start_output_pump`'s daemon-thread
    wiring, exercised through real (but short-lived, deterministic)
    background threads rather than direct synchronous calls.
    """

    def test_no_op_when_output_capture_unsupported(self) -> None:
        child = FakeChildProcess(argv=(), supports_output_capture=False)
        child.spawn()
        before = threading.active_count()

        thread = _start_output_pump(child, lambda event: None)
        time.sleep(0.05)

        self.assertIsNone(thread)
        self.assertEqual(
            threading.active_count(),
            before,
            "no pump thread should be started for a backend that cannot capture output",
        )

    def test_starts_daemon_thread_and_pumps_scripted_output_end_to_end(self) -> None:
        child = FakeChildProcess(argv=(), scripted_stdout=["hi\n"])
        child.spawn()
        captured_events: list[ChildOutput] = []
        out = io.StringIO()

        with mock.patch.object(sys, "stdout", out):
            thread = _start_output_pump(child, captured_events.append)
            self.assertIsNotNone(thread)
            thread.join(timeout=2.0)

        self.assertEqual([e.line for e in captured_events], ["hi\n"])
        self.assertEqual(out.getvalue(), "hi\n")


class ChildTerminationOrderingTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    """P-018 Copilot review finding (PR #331, comment 3777958619): a
    supervisor failure occurring after ``child.spawn()`` previously
    released the workspace lock in the ``except`` block BEFORE the
    module-level ``finally`` terminated the child -- letting another
    supervisor invocation acquire the lock while the old Copilot child was
    still alive. Proves the child is now closed BEFORE the lock is
    released on a post-spawn failure path.
    """

    def test_child_is_closed_before_lock_is_released_on_post_spawn_failure(self) -> None:
        order: list[str] = []

        class _OrderRecordingChild:
            supports_output_capture = False
            pid = 4321

            def spawn(self) -> None:
                pass

            def read(self) -> Optional[str]:
                return None

            def write(self, data: bytes) -> None:
                pass

            def signal(self, sig: int) -> None:
                pass

            def wait(self, timeout: Optional[float] = None) -> int:
                # Simulates a failure occurring after the child has spawned
                # (e.g. journaling/bookkeeping raising), which the
                # module-level `except Exception` boundary must catch.
                raise RuntimeError("simulated post-spawn failure")

            def close(self) -> None:
                order.append("child_close")

        class _OrderRecordingLock:
            def __init__(self) -> None:
                self.session_id = "order-test-session"

            def acquire(self) -> "_OrderRecordingLock":
                return self

            def release(self) -> None:
                order.append("lock_release")

        with tempfile.TemporaryDirectory() as workspace:
            workspace_root = Path(workspace)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                lock_factory=lambda root, session_id: _OrderRecordingLock(),
                child_process_factory=lambda argv: _OrderRecordingChild(),
                **_sidecar_kwargs(),
            )

        self.assertEqual(result.status, "failed")
        # The child must be closed (terminated) strictly BEFORE the lock is
        # released -- never the reverse -- on every failure path.
        self.assertGreaterEqual(len(order), 2)
        self.assertEqual(order[0], "child_close")
        self.assertEqual(order[1], "lock_release")


class RuntimeBindingEnvReachesChildTests(_DeterministicCopilotResolutionMixin, unittest.TestCase):
    """120-F post-closure correction (2026-08-13): the ENGRAM_WORKSPACE /
    GRAPHTOR_DB_PATH / GRAPHTOR_SOURCES additions bootstrap.py now always
    resolves must actually reach ``os.environ`` for the FULL lifetime of
    the spawned child (not just momentarily around
    ``bootstrap_workspace()``'s own call), and must be restored afterward --
    reusing the SAME serialized read-apply-restore critical section 129-S's
    own P-018 remediation already proved for every other bootstrap-resolved
    addition. This is the reinforcing half of 129-S's original fix
    (`.mcp.json` cleanup + child ``cwd`` anchoring): a real launch verified
    live (2026-08-13) that CWD-anchoring alone is insufficient when the
    Copilot child inherits an ALREADY-SET ``ENGRAM_WORKSPACE`` from its own
    ambient process environment, because an explicit env var always wins
    over a CWD-relative default in Engram's/graphtor-docs's own documented
    precedence.
    """

    def test_binding_env_is_present_in_os_environ_at_child_spawn_time_and_restored_after(
        self,
    ) -> None:
        import os as os_mod

        stale_var = "ENGRAM_WORKSPACE"
        stale_value = r"C:\Source\GitHub\engram"
        observed_at_spawn: dict[str, Optional[str]] = {}

        class _ObservingChild:
            supports_output_capture = False
            pid = 9001

            def spawn(self) -> None:
                # Captures os.environ exactly as the real Popen-based
                # backends would see it at spawn time (they inherit
                # os.environ verbatim with no per-call override).
                observed_at_spawn["ENGRAM_WORKSPACE"] = os_mod.environ.get("ENGRAM_WORKSPACE")
                observed_at_spawn["GRAPHTOR_DB_PATH"] = os_mod.environ.get("GRAPHTOR_DB_PATH")
                observed_at_spawn["GRAPHTOR_SOURCES"] = os_mod.environ.get("GRAPHTOR_SOURCES")

            def read(self) -> Optional[str]:
                return None

            def write(self, data: bytes) -> None:
                pass

            def signal(self, sig: int) -> None:
                pass

            def wait(self, timeout: Optional[float] = None) -> int:
                return 0

            def close(self) -> None:
                pass

        with tempfile.TemporaryDirectory() as workspace, mock.patch.dict(
            "os.environ", {stale_var: stale_value}
        ):
            workspace_root = Path(workspace)
            self.assertEqual(os_mod.environ.get(stale_var), stale_value)

            result = run_session(
                workspace_root=workspace_root,
                argv=[],
                approval_service=AlwaysApproveApprovalService(),
                child_process_factory=lambda argv: _ObservingChild(),
                **_sidecar_kwargs(),
            )

            self.assertEqual(result.status, "ok")
            resolved_root = str(workspace_root.resolve())
            self.assertEqual(observed_at_spawn["ENGRAM_WORKSPACE"], resolved_root)
            self.assertNotEqual(observed_at_spawn["ENGRAM_WORKSPACE"], stale_value)
            self.assertEqual(
                observed_at_spawn["GRAPHTOR_DB_PATH"],
                str(workspace_root.resolve() / ".graphtor" / "graph.db"),
            )
            self.assertEqual(
                observed_at_spawn["GRAPHTOR_SOURCES"],
                str(workspace_root.resolve() / ".graphtor" / "config" / "sources.yaml"),
            )

            # Restored to the stale/ambient value the mock.patch.dict
            # context manager set up, exactly as every other
            # bootstrap-resolved addition is restored (P-018 remediation) --
            # this call must never permanently overwrite the caller's own
            # process environment.
            self.assertEqual(os_mod.environ.get(stale_var), stale_value)


if __name__ == "__main__":
    unittest.main()
