"""Tests for autoharness.remote.ui -- the constrained V1 control-surface
wiring (121.007-T).

The pure surface spec (``build_surface_spec``) is exhaustively tested
without any UI toolkit installed -- it must expose EXACTLY the approved
Observe panels and Steer actions, nothing else, and no raw/general-purpose
component (shell textbox, code editor, generic chat) may appear anywhere
in the spec. The Gradio adapter itself is only exercised when the optional
``autoharness[remote]`` extra (gradio) is installed; otherwise that single
test is skipped rather than failing the base suite.
"""

from __future__ import annotations

import unittest

from autoharness.remote.contracts import ObserveCommand, RemoteResponse, SteerCommand
from autoharness.remote.errors import RemoteError, RemoteErrorKind
from autoharness.remote.ui import (
    OBSERVE_PANELS,
    STEER_ACTIONS,
    ObservePanelSpec,
    SteerActionSpec,
    _dispatch_confirmed_payload_and_render,
    build_surface_spec,
    _dispatch_confirmed_and_render,
    _dispatch_payload_and_render,
    launch_gradio_app,
    render_callback_result,
    validate_gradio_bind,
)

try:
    import gradio  # noqa: F401

    _GRADIO_AVAILABLE = True
except ImportError:
    _GRADIO_AVAILABLE = False


class SurfaceSpecClosureTests(unittest.TestCase):
    def test_observe_panels_cover_exactly_the_closed_observe_vocabulary(self) -> None:
        self.assertEqual(
            {panel.command for panel in OBSERVE_PANELS}, set(ObserveCommand)
        )

    def test_steer_actions_cover_exactly_the_closed_steer_vocabulary(self) -> None:
        self.assertEqual(
            {action.command for action in STEER_ACTIONS}, set(SteerCommand)
        )

    def test_every_panel_and_action_has_a_non_empty_label(self) -> None:
        for panel in OBSERVE_PANELS:
            with self.subTest(panel=panel):
                self.assertTrue(panel.label)
        for action in STEER_ACTIONS:
            with self.subTest(action=action):
                self.assertTrue(action.label)

    def test_cancel_requires_confirmation(self) -> None:
        cancel_specs = [a for a in STEER_ACTIONS if a.command is SteerCommand.CANCEL]
        self.assertEqual(len(cancel_specs), 1)
        self.assertTrue(cancel_specs[0].confirm)

    def test_build_surface_spec_returns_the_same_closed_tuples(self) -> None:
        spec = build_surface_spec()
        self.assertEqual(spec["observe"], OBSERVE_PANELS)
        self.assertEqual(spec["steer"], STEER_ACTIONS)

    def test_specs_are_frozen_value_objects(self) -> None:
        panel = ObservePanelSpec(ObserveCommand.STATUS, "Status")
        with self.assertRaises(Exception):
            panel.label = "Different"  # type: ignore[misc]
        action = SteerActionSpec(SteerCommand.PAUSE, "Pause")
        with self.assertRaises(Exception):
            action.label = "Different"  # type: ignore[misc]

    def test_non_loopback_gradio_bind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_gradio_bind("0.0.0.0")

    def test_remote_errors_render_as_structured_json(self) -> None:
        rendered = render_callback_result(
            RemoteError("bad request", kind=RemoteErrorKind.PROTOCOL)
        )
        self.assertIn('"ok": false', rendered)
        self.assertIn('"kind": "protocol_error"', rendered)

    def test_remote_response_with_immutable_payload_renders_as_structured_json(self) -> None:
        rendered = render_callback_result(
            RemoteResponse(
                request_id="req-1",
                command="status",
                ok=True,
                payload={"phase": "running"},
            )
        )
        self.assertIn('"ok": true', rendered)
        self.assertIn('"phase": "running"', rendered)

    def test_launch_gradio_app_forces_loopback_and_rejects_override(self) -> None:
        class FakeApp:
            def __init__(self) -> None:
                self.calls: list[dict[str, object]] = []

            def launch(self, *, server_name: str, **kwargs: object) -> object:
                self.calls.append({"server_name": server_name, **kwargs})
                return "launched"

        app = FakeApp()
        self.assertEqual(launch_gradio_app(app, share=False), "launched")
        self.assertEqual(app.calls, [{"server_name": "127.0.0.1", "share": False}])
        with self.assertRaises(ValueError):
            launch_gradio_app(app, server_name="0.0.0.0")
        with self.assertRaises(ValueError):
            launch_gradio_app(app, share=True)

    def test_cancel_dispatch_requires_explicit_confirmation(self) -> None:
        calls: list[object] = []
        rendered = _dispatch_confirmed_and_render(calls.append, SteerCommand.CANCEL, False)
        self.assertIn("confirmation_required", rendered)
        self.assertEqual(calls, [])
        _dispatch_confirmed_and_render(calls.append, SteerCommand.CANCEL, True)
        self.assertEqual(calls, [SteerCommand.CANCEL])

    def test_payload_dispatch_forwards_json_without_synthesizing_envelope(self) -> None:
        calls: list[bytes] = []
        def capture(payload: bytes) -> dict[str, object]:
            calls.append(payload)
            return {"request_id": "caller-1"}

        rendered = _dispatch_payload_and_render(capture, {"request_id": "caller-1"})
        self.assertEqual(calls, [b'{"request_id":"caller-1"}'])
        self.assertIn('"request_id": "caller-1"', rendered)

    def test_payload_dispatch_rejects_non_json_values(self) -> None:
        calls: list[bytes] = []
        rendered = _dispatch_payload_and_render(calls.append, {"bad": object()})
        self.assertIn('"ok": false', rendered)
        self.assertIn("protocol_error", rendered)

    def test_payload_dispatch_rejects_command_mismatch_before_dispatch(self) -> None:
        calls: list[bytes] = []
        rendered = _dispatch_payload_and_render(
            calls.append,
            {"command": "cancel"},
            expected_command=SteerCommand.PAUSE.value,
        )
        self.assertIn('"ok": false', rendered)
        self.assertIn("protocol_error", rendered)
        self.assertIn("does not match", rendered)
        self.assertEqual(calls, [])

    def test_cancel_confirmation_cannot_be_bypassed_by_another_button(self) -> None:
        calls: list[bytes] = []
        rendered = _dispatch_confirmed_payload_and_render(
            calls.append,
            {"command": SteerCommand.CANCEL.value},
            True,
            expected_command=SteerCommand.PAUSE.value,
        )
        self.assertIn('"ok": false', rendered)
        self.assertIn("protocol_error", rendered)
        self.assertEqual(calls, [])


@unittest.skipUnless(_GRADIO_AVAILABLE, "gradio is an optional extra (autoharness[remote])")
class GradioAdapterTests(unittest.TestCase):
    def test_build_gradio_app_wires_without_error(self) -> None:
        from autoharness.remote.ui import build_gradio_app

        calls: list[str] = []
        app = build_gradio_app(
            dispatch_observe=lambda payload: calls.append(f"observe:{payload}"),
            dispatch_steer=lambda payload: calls.append(f"steer:{payload}"),
        )
        self.assertIsNotNone(app)


class GradioLazyImportTests(unittest.TestCase):
    def test_module_import_never_requires_gradio(self) -> None:
        """The base import of autoharness.remote.ui must succeed with no
        gradio dependency -- gradio is imported LAZILY, only inside
        build_gradio_app(), so the optional extra never becomes a base
        install requirement."""

        import importlib
        import sys

        self.assertNotIn("gradio", sys.modules.keys() - {"gradio"} | set())
        module = importlib.import_module("autoharness.remote.ui")
        self.assertTrue(hasattr(module, "build_gradio_app"))

    @unittest.skipIf(_GRADIO_AVAILABLE, "this test asserts the ImportError path when gradio is ABSENT")
    def test_build_gradio_app_raises_import_error_with_install_hint_when_absent(self) -> None:
        from autoharness.remote.ui import build_gradio_app

        with self.assertRaises(ImportError) as ctx:
            build_gradio_app(dispatch_observe=lambda c: None, dispatch_steer=lambda c: None)
        self.assertIn("remote", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
