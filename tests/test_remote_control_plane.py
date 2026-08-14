"""Tests for production Plan 2 control-plane composition."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from autoharness.remote.control_plane import RemoteControlPlane
from autoharness.remote.contracts import ObserveCommand, SteerCommand
from autoharness.remote.tunnel import FakeTunnelProcess, TunnelLifecycle
from autoharness.supervise.approvals import ConsoleApprovalService
from autoharness.supervise.events import EventBus
from autoharness.supervise.session import Phase, SessionStateMachine


class _Journal:
    def __init__(self) -> None:
        self.events: list[object] = []

    def append_event(self, event: object) -> int:
        self.events.append(event)
        return len(self.events)

    def read_own_cursor(self) -> int:
        return len(self.events)

    def read_own_tail(self, limit: int = 50) -> list[dict[str, object]]:
        return []


def _running_machine() -> SessionStateMachine:
    machine = SessionStateMachine()
    for phase in (
        Phase.LOCKING,
        Phase.BOOTSTRAPPING,
        Phase.PREFLIGHT,
        Phase.RESOLVING,
        Phase.LAUNCHING,
        Phase.RUNNING,
    ):
        machine.transition(phase)
    return machine


class RemoteControlPlaneTests(unittest.TestCase):
    def _create(self, machine: SessionStateMachine | None = None) -> RemoteControlPlane:
        return RemoteControlPlane.create(
            workspace_root=Path("/workspace"),
            session_id="session-1",
            state_machine=machine or _running_machine(),
            journal=_Journal(),
            event_bus=EventBus(),
            local_channel=ConsoleApprovalService(),
            on_pause=lambda: "paused-by-child",
            on_resume=lambda: "resumed-by-child",
            on_cancel=lambda: "cancelled-by-child",
            emit=lambda event: 1,
            secret=b"s" * 32,
        )

    @mock.patch(
        "autoharness.remote.control_plane.resolve_devtunnel_executable",
        return_value="devtunnel",
    )
    def test_callbacks_construct_bound_authenticated_requests(self, _resolve: mock.Mock) -> None:
        plane = self._create()
        response = plane.dispatch_observe(ObserveCommand.STATUS)
        self.assertTrue(response.ok)
        self.assertEqual(response.payload["phase"], Phase.RUNNING.value)
        steer_response = plane.dispatch_steer(SteerCommand.PAUSE)
        self.assertTrue(steer_response.ok)
        self.assertEqual(steer_response.payload["acknowledgement"], "paused-by-child")

    @mock.patch(
        "autoharness.remote.control_plane.resolve_devtunnel_executable",
        return_value="devtunnel",
    )
    def test_start_launches_loopback_ui_and_tunnel_then_stop_tears_down(
        self, _resolve: mock.Mock
    ) -> None:
        plane = self._create()
        fake = FakeTunnelProcess(("devtunnel", "host"))
        plane.tunnel = TunnelLifecycle(
            bind_host="127.0.0.1",
            process_factory=lambda: fake,
        )
        with (
            mock.patch(
                "autoharness.remote.control_plane.build_gradio_app",
                return_value=object(),
            ) as build,
            mock.patch("autoharness.remote.control_plane.launch_gradio_app") as launch,
        ):
            plane.start()
            self.assertTrue(plane.started)
            build.assert_called_once()
            launch.assert_called_once()
            self.assertEqual(launch.call_args.kwargs["bind_host"], "127.0.0.1")
            self.assertFalse(launch.call_args.kwargs["share"])
            plane.stop()
        self.assertTrue(fake.terminated)
        self.assertFalse(plane.started)


if __name__ == "__main__":
    unittest.main()
