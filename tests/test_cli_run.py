"""Tests for the `autoharness run` CLI adapter (120.006-T).

The adapter is pure plumbing: it parses argv, constructs a real
``ConsoleApprovalService``, calls :func:`autoharness.supervise.app.run_session`
with every option forwarded 1:1, renders the returned
:class:`~autoharness.supervise.result.SupervisorResult` (human or ``--json``),
and exits with ``result.exit_code`` verbatim.

``autoharness.supervise.app.run_session`` is monkeypatched to a spy/stub in
every test here so no real subprocess, lock, or approval flow ever runs.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from autoharness.cli import main
from autoharness.supervise.result import SupervisorResult


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - test harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


class _SpyRunSession:
    """Records the kwargs it was called with and returns a canned result."""

    def __init__(self, result: SupervisorResult) -> None:
        self.result = result
        self.calls: list[dict] = []

    def __call__(self, **kwargs) -> SupervisorResult:
        self.calls.append(kwargs)
        return self.result


class RunHelpTests(unittest.TestCase):
    def test_run_help_lists_options(self) -> None:
        out, _, code = _run("run", "--help")
        self.assertEqual(code, 0)
        self.assertIn("--json", out)
        self.assertIn("--force-unlock", out)
        self.assertIn("--max-restarts", out)
        self.assertIn("--pty", out)
        self.assertIn("--no-pty", out)
        self.assertIn("--session-id", out)
        self.assertIn("--workspace", out)

    def test_top_level_usage_lists_run(self) -> None:
        out, _, _ = _run("--help")
        self.assertIn("autoharness run", out)


class RunHelpTokenAfterSeparatorForwardingTests(unittest.TestCase):
    """Regression guard (129-S review gate P1 finding): a forwarded child
    argv token of ``help``/``--help``/``-h`` placed AFTER the ``--``
    separator belongs to the operator's own command (e.g. an operator
    running ``./start.sh --help`` intending to see Copilot CLI's own
    help) and MUST be forwarded to ``run_session`` verbatim -- never
    intercepted by this adapter's own help-usage short-circuit, which is
    scoped exclusively to the adapter's OWN pre-``--`` args."""

    def test_help_token_after_separator_is_forwarded_not_intercepted(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            out, _, code = _run("run", "--", "--help")
        self.assertEqual(len(spy.calls), 1)
        self.assertEqual(tuple(spy.calls[0]["argv"]), ("--help",))
        self.assertNotIn("Usage:", out)

    def test_bare_help_token_after_separator_is_forwarded(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--", "help")
        self.assertEqual(tuple(spy.calls[0]["argv"]), ("help",))

    def test_short_h_token_after_separator_is_forwarded(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--", "-h")
        self.assertEqual(tuple(spy.calls[0]["argv"]), ("-h",))

    def test_own_help_flag_before_separator_still_short_circuits(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            out, _, code = _run("run", "--help", "--", "some-child-arg")
        self.assertEqual(len(spy.calls), 0)
        self.assertIn("Usage:", out)


class RunArgErrorTests(unittest.TestCase):
    def test_unknown_flag_exits_2(self) -> None:
        _, _, code = _run("run", "--bogus")
        self.assertEqual(code, 2)

    def test_pty_and_no_pty_mutually_exclusive_exits_2(self) -> None:
        _, _, code = _run("run", "--pty", "--no-pty")
        self.assertEqual(code, 2)

    def test_max_restarts_missing_value_exits_2(self) -> None:
        _, _, code = _run("run", "--max-restarts")
        self.assertEqual(code, 2)

    def test_max_restarts_non_integer_exits_2(self) -> None:
        _, _, code = _run("run", "--max-restarts", "nope")
        self.assertEqual(code, 2)

    def test_session_id_missing_value_exits_2(self) -> None:
        _, _, code = _run("run", "--session-id")
        self.assertEqual(code, 2)

    def test_workspace_missing_value_exits_2(self) -> None:
        _, _, code = _run("run", "--workspace")
        self.assertEqual(code, 2)


class RunRenderingTests(unittest.TestCase):
    def test_human_rendering_ok(self) -> None:
        spy = _SpyRunSession(
            SupervisorResult(status="ok", exit_code=0, messages=("done",), warnings=("careful",))
        )
        with mock.patch("autoharness.supervise.app.run_session", spy):
            out, _, code = _run("run", "--", "status")
        self.assertEqual(code, 0)
        self.assertIn("ok", out)
        self.assertIn("done", out)
        self.assertIn("careful", out)

    def test_json_rendering(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            out, _, code = _run("run", "--json", "--", "status")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["exit_code"], 0)

    def test_exit_code_propagates_for_failed(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="failed", exit_code=7))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _, _, code = _run("run")
        self.assertEqual(code, 7)

    def test_exit_code_propagates_for_blocked_refusal(self) -> None:
        # A REFUSED force-unlock resolves to a distinctive non-zero exit
        # code; the adapter must propagate it verbatim, never remap to 0
        # or any other code.
        spy = _SpyRunSession(SupervisorResult(status="blocked", exit_code=13))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _, _, code = _run("run", "--force-unlock")
        self.assertEqual(code, 13)

    def test_exit_code_propagates_for_cancelled(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="cancelled", exit_code=130))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _, _, code = _run("run")
        self.assertEqual(code, 130)


class RunForwardingTests(unittest.TestCase):
    """Every option must be BOTH parsed AND actually forwarded into the
    ``run_session`` call kwargs -- parsing success alone is not sufficient
    evidence."""

    def test_default_forwarding(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run")
        self.assertEqual(len(spy.calls), 1)
        kwargs = spy.calls[0]
        self.assertEqual(kwargs["workspace_root"], Path("."))
        self.assertEqual(tuple(kwargs["argv"]), ())
        self.assertFalse(kwargs["force_unlock"])
        self.assertEqual(kwargs["max_restarts"], 0)
        self.assertIsNone(kwargs["use_pty"])
        self.assertIsNone(kwargs["session_id"])
        # A real, concrete approval service must be constructed for the CLI
        # path -- never omitted, never a permissive stand-in.
        from autoharness.supervise.approvals import ConsoleApprovalService

        self.assertIsInstance(kwargs["approval_service"], ConsoleApprovalService)

    def test_json_flag_forwarded_to_rendering_only(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--json")
        # --json is a CLI-local rendering switch; run_session itself has no
        # such parameter, so it must not appear in the forwarded kwargs.
        self.assertNotIn("json", spy.calls[0])
        self.assertNotIn("emit_json", spy.calls[0])

    def test_force_unlock_forwarded(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--force-unlock")
        self.assertTrue(spy.calls[0]["force_unlock"])

    def test_max_restarts_forwarded(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--max-restarts", "3")
        self.assertEqual(spy.calls[0]["max_restarts"], 3)

    def test_pty_forwarded(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--pty")
        self.assertIs(spy.calls[0]["use_pty"], True)

    def test_no_pty_forwarded(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--no-pty")
        self.assertIs(spy.calls[0]["use_pty"], False)

    def test_session_id_forwarded(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--session-id", "abc-123")
        self.assertEqual(spy.calls[0]["session_id"], "abc-123")

    def test_workspace_forwarded(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--workspace", r"C:\some\workspace")
        self.assertEqual(spy.calls[0]["workspace_root"], Path(r"C:\some\workspace"))

    def test_trailing_argv_forwarded_verbatim(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run("run", "--max-restarts", "2", "--", "-x", "--weird flag", "value with spaces")
        self.assertEqual(spy.calls[0]["max_restarts"], 2)
        self.assertEqual(
            tuple(spy.calls[0]["argv"]),
            ("-x", "--weird flag", "value with spaces"),
        )

    def test_all_options_combined(self) -> None:
        spy = _SpyRunSession(SupervisorResult(status="ok", exit_code=0))
        with mock.patch("autoharness.supervise.app.run_session", spy):
            _run(
                "run",
                "--json",
                "--force-unlock",
                "--max-restarts",
                "5",
                "--pty",
                "--session-id",
                "sess-1",
                "--",
                "some",
                "args",
            )
        kwargs = spy.calls[0]
        self.assertTrue(kwargs["force_unlock"])
        self.assertEqual(kwargs["max_restarts"], 5)
        self.assertIs(kwargs["use_pty"], True)
        self.assertEqual(kwargs["session_id"], "sess-1")
        self.assertEqual(tuple(kwargs["argv"]), ("some", "args"))


if __name__ == "__main__":
    unittest.main()
