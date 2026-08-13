"""Tests for autoharness.supervise.events -- the in-process event bus (119.004-T).

Covers redaction-on-emit, the no-raw-emit-API surface contract,
subscribe/unsubscribe/fan-out, and the mandatory H7 anti-drift no-listen
guard: a behavioral (sys.addaudithook-based) enforcement mechanism proven
via a POSITIVE CONTROL that deliberately opens listening sockets through
four different stdlib APIs and asserts the guard fires for each.
"""

from __future__ import annotations

import asyncio
import contextlib
import gc
import http.server
import inspect
import socket
import socketserver
import sys
import unittest

from autoharness.supervise.contracts import ChildOutput, ChildSpawned, SidecarProbed
from autoharness.supervise.events import (
    EventBus,
    ListeningSocketDetected,
    check_import_denylist,
    install_no_listen_guard,
)
from autoharness.supervise.redact import PLACEHOLDER, Redactor


class RedactionOnEmitTests(unittest.TestCase):
    def test_registered_secret_never_reaches_subscriber(self) -> None:
        redactor = Redactor()
        redactor.register_secret("super-secret-token-1234567890")
        bus = EventBus(redactor=redactor)
        received: list[SidecarProbed] = []
        bus.subscribe(SidecarProbed, received.append)

        bus.emit(
            SidecarProbed(
                name="gh",
                available=True,
                detail="auth token=super-secret-token-1234567890 accepted",
            )
        )

        self.assertEqual(len(received), 1)
        self.assertNotIn("super-secret-token-1234567890", received[0].detail)
        self.assertIn(PLACEHOLDER, received[0].detail)

    def test_pattern_matched_secret_in_string_field_is_redacted(self) -> None:
        redactor = Redactor()
        bus = EventBus(redactor=redactor)
        received: list[ChildOutput] = []
        bus.subscribe(ChildOutput, received.append)

        bus.emit(ChildOutput(stream="stdout", line="token=ghp_" + "a" * 36))

        self.assertEqual(len(received), 1)
        self.assertNotIn("ghp_", received[0].line)
        self.assertIn(PLACEHOLDER, received[0].line)

    def test_event_with_no_secret_passes_through_unchanged_in_content(self) -> None:
        redactor = Redactor()
        bus = EventBus(redactor=redactor)
        received: list[ChildOutput] = []
        bus.subscribe(ChildOutput, received.append)

        bus.emit(ChildOutput(stream="stdout", line="hello world"))

        self.assertEqual(received[0].line, "hello world")


class NoRawEmitApiTests(unittest.TestCase):
    def test_public_api_surface_has_no_bypass_method(self) -> None:
        public_methods = {
            name
            for name, _member in inspect.getmembers(EventBus, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        self.assertEqual(public_methods, {"emit", "subscribe", "unsubscribe"})

    def test_emit_is_the_sole_delivery_path(self) -> None:
        # There is exactly one way to get an event to a subscriber: emit().
        # No emit_raw / publish_unredacted / bypass_redaction style method.
        for forbidden_name in ("emit_raw", "publish_unredacted", "emit_unsafe", "bypass_redaction"):
            self.assertFalse(hasattr(EventBus, forbidden_name))


class SubscribeUnsubscribeFanOutTests(unittest.TestCase):
    def test_multiple_subscribers_all_receive_matching_events(self) -> None:
        bus = EventBus()
        received_a: list[object] = []
        received_b: list[object] = []
        bus.subscribe(ChildSpawned, received_a.append)
        bus.subscribe(ChildSpawned, received_b.append)

        bus.emit(ChildSpawned(argv=("echo", "hi"), pid=123))

        self.assertEqual(len(received_a), 1)
        self.assertEqual(len(received_b), 1)

    def test_subscriber_only_receives_matching_event_type(self) -> None:
        bus = EventBus()
        received: list[object] = []
        bus.subscribe(ChildSpawned, received.append)

        bus.emit(ChildOutput(stream="stdout", line="not spawned"))

        self.assertEqual(received, [])

    def test_predicate_subscription_supported(self) -> None:
        bus = EventBus()
        received: list[object] = []
        bus.subscribe(lambda event: isinstance(event, ChildOutput) and event.stream == "stderr", received.append)

        bus.emit(ChildOutput(stream="stdout", line="ignored"))
        bus.emit(ChildOutput(stream="stderr", line="captured"))

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].line, "captured")

    def test_unsubscribe_stops_delivery(self) -> None:
        bus = EventBus()
        received: list[object] = []
        token = bus.subscribe(ChildSpawned, received.append)
        bus.unsubscribe(token)

        bus.emit(ChildSpawned(argv=("echo",), pid=1))

        self.assertEqual(received, [])

    def test_unsubscribe_unknown_token_is_a_safe_no_op(self) -> None:
        bus = EventBus()
        bus.unsubscribe("not-a-real-token")  # must not raise


class LexicalDenylistSecondaryCheckTests(unittest.TestCase):
    def test_known_denylisted_module_names_are_flagged(self) -> None:
        violations = check_import_denylist(["gradio", "fastapi", "flask", "uvicorn", "aiohttp", "os", "json"])
        self.assertEqual(set(violations), {"gradio", "fastapi", "flask", "uvicorn", "aiohttp"})

    def test_devtunnel_shaped_names_are_flagged(self) -> None:
        violations = check_import_denylist(["ms_devtunnel_client", "devtunnels", "requests"])
        self.assertEqual(set(violations), {"ms_devtunnel_client", "devtunnels"})

    def test_clean_module_list_has_no_violations(self) -> None:
        self.assertEqual(check_import_denylist(["json", "re", "dataclasses"]), [])


class NoListenGuardScopingTests(unittest.TestCase):
    def test_guard_does_not_fire_for_non_socket_work(self) -> None:
        with install_no_listen_guard():
            result = 1 + 1
        self.assertEqual(result, 2)

    def test_guard_is_inactive_outside_its_context(self) -> None:
        with install_no_listen_guard():
            pass
        # Outside the guard's scope, binding a socket must NOT raise.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", 0))
        finally:
            sock.close()


class NoListenGuardPositiveControlTests(unittest.TestCase):
    """Mandatory positive control: prove the guard actually fires."""

    def test_socket_create_server_is_detected(self) -> None:
        srv = None
        try:
            with self.assertRaises(ListeningSocketDetected):
                with install_no_listen_guard():
                    srv = socket.create_server(("127.0.0.1", 0))
        finally:
            if srv is not None:
                srv.close()
            gc.collect()

    def test_socketserver_tcpserver_is_detected(self) -> None:
        server = socketserver.TCPServer.__new__(socketserver.TCPServer)
        try:
            with self.assertRaises(ListeningSocketDetected):
                with install_no_listen_guard():
                    server.__init__(("127.0.0.1", 0), socketserver.BaseRequestHandler)
        finally:
            with contextlib.suppress(Exception):
                if getattr(server, "socket", None) is not None:
                    server.socket.close()

    def test_http_server_httpserver_is_detected(self) -> None:
        server = http.server.HTTPServer.__new__(http.server.HTTPServer)
        try:
            with self.assertRaises(ListeningSocketDetected):
                with install_no_listen_guard():
                    server.__init__(("127.0.0.1", 0), http.server.BaseHTTPRequestHandler)
        finally:
            with contextlib.suppress(Exception):
                if getattr(server, "socket", None) is not None:
                    server.socket.close()

    def test_asyncio_start_server_is_detected(self) -> None:
        # Create the event loop OUTSIDE the guard: on Windows, event-loop
        # construction itself performs a socket.bind as part of emulating
        # socketpair() for the loop's self-pipe wakeup mechanism, which
        # would make the guard fire for an unrelated reason. Only the
        # start_server() call itself runs inside the guard's scope, so the
        # detected bind is unambiguously the one start_server() performs.
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        try:
            async def _handler(reader, writer):  # pragma: no cover - never runs
                pass

            async def _attempt() -> None:
                server = await asyncio.start_server(_handler, host="127.0.0.1", port=0)
                server.close()
                await server.wait_closed()

            with self.assertRaises(ListeningSocketDetected):
                with install_no_listen_guard():
                    loop.run_until_complete(_attempt())
        finally:
            loop.close()
            asyncio.set_event_loop_policy(None)
        gc.collect()


class NoListenGuardCrossThreadTests(unittest.TestCase):
    """128-S review remediation: the guard's depth counter must be visible
    to EVERY thread, not just the one that entered the ``with`` block --
    otherwise a background thread started while the guard is active could
    bind a listening socket undetected (a genuine H7/F28 bypass, since a
    ``contextvars.ContextVar`` is NOT inherited by a newly created OS
    thread).
    """

    def test_guard_fires_for_bind_performed_on_a_background_thread(self) -> None:
        import threading

        detected: list[BaseException] = []
        srv_holder: list[socket.socket] = []

        def _bind_on_thread() -> None:
            try:
                srv_holder.append(socket.create_server(("127.0.0.1", 0)))
            except ListeningSocketDetected as exc:
                detected.append(exc)

        with install_no_listen_guard():
            thread = threading.Thread(target=_bind_on_thread)
            thread.start()
            thread.join(timeout=10)

        try:
            self.assertEqual(
                len(detected),
                1,
                "the no-listen guard must fire for a socket bind performed by a "
                "background thread while the guard's context is active on the "
                "thread that entered it",
            )
        finally:
            for srv in srv_holder:
                with contextlib.suppress(Exception):
                    srv.close()
            gc.collect()


if __name__ == "__main__":
    unittest.main()
