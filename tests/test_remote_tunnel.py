"""Tests for autoharness.remote.tunnel -- loopback-only binding and the
devtunnel lifecycle boundary (121.005-T).

Covers: non-loopback bind hosts are always rejected (T7 non-negotiable),
devtunnel-unavailable produces a clear, actionable failure, and tunnel
teardown is mandatory + idempotent across normal shutdown and
crash/exception paths.
"""

from __future__ import annotations

import unittest

from autoharness.remote.errors import DevtunnelUnavailableError
from autoharness.remote.tunnel import (
    FakeTunnelProcess,
    NonLoopbackBindError,
    TunnelLifecycle,
    resolve_devtunnel_executable,
    validate_loopback_bind,
)


class LoopbackBindValidationTests(unittest.TestCase):
    def test_127_0_0_1_is_accepted(self) -> None:
        validate_loopback_bind("127.0.0.1")  # must not raise

    def test_localhost_is_accepted(self) -> None:
        validate_loopback_bind("localhost")  # must not raise

    def test_ipv6_loopback_is_accepted(self) -> None:
        validate_loopback_bind("::1")  # must not raise

    def test_all_interfaces_is_rejected(self) -> None:
        with self.assertRaises(NonLoopbackBindError):
            validate_loopback_bind("0.0.0.0")

    def test_ipv6_all_interfaces_is_rejected(self) -> None:
        with self.assertRaises(NonLoopbackBindError):
            validate_loopback_bind("::")

    def test_arbitrary_lan_address_is_rejected(self) -> None:
        with self.assertRaises(NonLoopbackBindError):
            validate_loopback_bind("192.168.1.5")

    def test_empty_host_is_rejected(self) -> None:
        with self.assertRaises(NonLoopbackBindError):
            validate_loopback_bind("")


class DevtunnelResolutionTests(unittest.TestCase):
    def test_missing_devtunnel_raises_clear_actionable_error(self) -> None:
        with self.assertRaises(DevtunnelUnavailableError) as ctx:
            resolve_devtunnel_executable(which_fn=lambda name: None)
        self.assertIn("devtunnel", str(ctx.exception).lower())

    def test_present_devtunnel_returns_its_path(self) -> None:
        path = resolve_devtunnel_executable(which_fn=lambda name: r"C:\tools\devtunnel.exe")
        self.assertEqual(path, r"C:\tools\devtunnel.exe")


class TunnelLifecycleTests(unittest.TestCase):
    def test_construction_validates_loopback_bind(self) -> None:
        with self.assertRaises(NonLoopbackBindError):
            TunnelLifecycle(bind_host="0.0.0.0", process_factory=lambda: FakeTunnelProcess(argv=("devtunnel",)))

    def test_start_spawns_the_underlying_process(self) -> None:
        fake = FakeTunnelProcess(argv=("devtunnel", "host"))
        lifecycle = TunnelLifecycle(bind_host="127.0.0.1", process_factory=lambda: fake)
        lifecycle.start()
        self.assertTrue(fake.spawned)
        self.assertTrue(lifecycle.active)

    def test_start_is_idempotent(self) -> None:
        created = []

        def factory() -> FakeTunnelProcess:
            proc = FakeTunnelProcess(argv=("devtunnel",))
            created.append(proc)
            return proc

        lifecycle = TunnelLifecycle(bind_host="127.0.0.1", process_factory=factory)
        lifecycle.start()
        lifecycle.start()
        self.assertEqual(len(created), 1)

    def test_teardown_terminates_and_is_idempotent(self) -> None:
        fake = FakeTunnelProcess(argv=("devtunnel",))
        lifecycle = TunnelLifecycle(bind_host="127.0.0.1", process_factory=lambda: fake)
        lifecycle.start()
        lifecycle.teardown()
        self.assertTrue(fake.terminated)
        self.assertFalse(lifecycle.active)
        lifecycle.teardown()  # must not raise -- idempotent

    def test_teardown_before_start_is_a_safe_no_op(self) -> None:
        lifecycle = TunnelLifecycle(
            bind_host="127.0.0.1", process_factory=lambda: FakeTunnelProcess(argv=("devtunnel",))
        )
        lifecycle.teardown()  # must not raise
        self.assertFalse(lifecycle.active)

    def test_teardown_runs_on_crash_path_via_try_finally(self) -> None:
        """Mandatory-teardown-on-crash contract: a lifecycle used inside a
        try/finally must still be torn down even when the guarded body
        raises."""

        fake = FakeTunnelProcess(argv=("devtunnel",))
        lifecycle = TunnelLifecycle(bind_host="127.0.0.1", process_factory=lambda: fake)
        lifecycle.start()
        with self.assertRaises(RuntimeError):
            try:
                raise RuntimeError("simulated crash")
            finally:
                lifecycle.teardown()
        self.assertTrue(fake.terminated)
        self.assertFalse(lifecycle.active)


if __name__ == "__main__":
    unittest.main()
