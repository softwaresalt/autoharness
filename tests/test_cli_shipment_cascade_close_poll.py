"""CLI wiring of ``--caller-wait`` / ``--poll`` / ``--wait`` (211.007-T, plan unit T8)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from test_cli_shipment_cascade_close import _BASE, _EVIDENCE, _MUTATING, _json, _run, _Stubs

from _env_patch import patched_environ
from autoharness.cli import SHIPMENT_USAGE
from autoharness.shipment_close import poll
from autoharness.shipment_close.command import CascadeCloseOutcome
from autoharness.shipment_close.poll import PollOutcome

_JOURNAL = Path("ws/.autoharness/gates/cascade-close/900-S-600-F.journal")
_POLL = ("shipment", "cascade-close", "--shipment", "900-S", "--feature", "600-F", "--poll")
_OK = CascadeCloseOutcome(exit_code=0, message="closed", evidence_path=_EVIDENCE)


def _poll_json(*argv: str, outcome: PollOutcome):
    with _Stubs() as stubs, mock.patch.object(poll, "poll_cascade_close", return_value=outcome) as polled:
        out, _err, code = _run(*argv, "--json")
    return json.loads(out), code, stubs, polled


class CallerWaitCliTests(unittest.TestCase):
    def test_the_flag_reaches_the_command(self) -> None:
        payload, _code, stubs = _json(*_MUTATING, "--caller-wait", "4000", mutating=_OK)
        self.assertEqual(payload["mode"], "mutating")
        self.assertEqual(stubs.mutating.call_args.kwargs["caller_wait_seconds"], 4000)

    def test_the_environment_variable_is_the_fallback_and_the_flag_wins(self) -> None:
        with patched_environ(AUTOHARNESS_CALLER_WAIT_SECONDS="7200"):
            _payload, _code, stubs = _json(*_MUTATING, mutating=_OK)
            self.assertEqual(stubs.mutating.call_args.kwargs["caller_wait_seconds"], 7200)
            _payload, _code, stubs = _json(*_MUTATING, "--caller-wait", "3000", mutating=_OK)
            self.assertEqual(stubs.mutating.call_args.kwargs["caller_wait_seconds"], 3000)

    def test_no_declared_wait_adds_no_argument(self) -> None:
        with patched_environ(AUTOHARNESS_CALLER_WAIT_SECONDS=None):
            _payload, _code, stubs = _json(*_MUTATING, mutating=_OK)
        self.assertNotIn("caller_wait_seconds", stubs.mutating.call_args.kwargs)

    def test_malformed_values_are_exit_2_and_nothing_runs(self) -> None:
        for label, argv, env in (
            ("non-integer flag", (*_MUTATING, "--caller-wait", "soon"), None),
            ("negative flag", (*_MUTATING, "--caller-wait", "-1"), None),
            ("float flag", (*_MUTATING, "--caller-wait", "1e3"), None),
            ("bad environment variable", _MUTATING, "forever"),
            ("classify-only", (*_BASE, "--classify-only", "--caller-wait", "10"), None),
        ):
            with self.subTest(label), patched_environ(AUTOHARNESS_CALLER_WAIT_SECONDS=env):
                payload, code, stubs = _json(*argv)
                self.assertEqual(code, 2)
                self.assertEqual(payload["mutation_possible"], "no")
                stubs.mutating.assert_not_called()
                stubs.classify.assert_not_called()


class PollCliTests(unittest.TestCase):
    def test_poll_routes_to_the_read_only_poll_without_resolving_the_binary(self) -> None:
        outcome = PollOutcome(
            exit_code=9,
            message="running",
            journal_path=_JOURNAL,
            evidence_path=_EVIDENCE,
            outcome_source=None,
            recovery_available=False,
        )
        payload, code, stubs, polled = _poll_json(*_POLL, "--wait", "30", "--workspace", "scratch-ws", outcome=outcome)
        self.assertEqual(code, 9)
        self.assertEqual(payload["mode"], "poll")
        self.assertEqual(payload["mutation_possible"], "yes")
        self.assertEqual(payload["operator_action"], "none")
        self.assertEqual(payload["journal_path"], str(_JOURNAL))
        self.assertIsNone(payload["outcome_source"])
        self.assertIs(payload["recovery_available"], False)
        polled.assert_called_once_with(Path("scratch-ws"), "900-S", "600-F", wait_seconds=30)
        stubs.resolve.assert_not_called()
        stubs.mutating.assert_not_called()
        stubs.classify.assert_not_called()

    def test_poll_defaults_to_no_wait_and_reports_the_final_code(self) -> None:
        outcome = PollOutcome(exit_code=0, message="done", journal_path=_JOURNAL, outcome_source="evidence_record")
        payload, code, _stubs, polled = _poll_json(*_POLL, outcome=outcome)
        self.assertEqual(code, 0)
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["outcome_source"], "evidence_record")
        polled.assert_called_once_with(Path("."), "900-S", "600-F", wait_seconds=0)

    def test_poll_exit_7_carries_recovery_available(self) -> None:
        outcome = PollOutcome(exit_code=7, message="owner dead", journal_path=_JOURNAL, recovery_available=True)
        payload, code, _stubs, _polled = _poll_json(*_POLL, outcome=outcome)
        self.assertEqual(code, 7)
        self.assertEqual(payload["operator_action"], "review_required")
        self.assertIs(payload["recovery_available"], True)

    def test_incompatible_arguments_are_exit_2(self) -> None:
        for label, extra in (
            ("--message", ("--message", "m")),
            ("--author", ("--author", "a")),
            ("--timeout", ("--timeout", "60")),
            ("--detach", ("--detach",)),
            ("--classify-only", ("--classify-only",)),
            ("--caller-wait", ("--caller-wait", "10")),
            ("a negative wait", ("--wait", "-1")),
            ("a non-integer wait", ("--wait", "soon")),
        ):
            with self.subTest(label):
                payload, code, _stubs, polled = _poll_json(
                    *_POLL, *extra, outcome=PollOutcome(exit_code=0, message="unused")
                )
                self.assertEqual(code, 2)
                polled.assert_not_called()

    def test_wait_requires_poll(self) -> None:
        payload, code, stubs = _json(*_MUTATING, "--wait", "5")
        self.assertEqual(code, 2)
        stubs.mutating.assert_not_called()

    def test_usage_documents_the_new_options(self) -> None:
        for token in ("--caller-wait", "AUTOHARNESS_CALLER_WAIT_SECONDS", "--poll", "--wait"):
            self.assertIn(token, SHIPMENT_USAGE)


if __name__ == "__main__":
    unittest.main()
