"""CLI wiring of ``cascade-close --recover`` and exit 10, ``recovery_available``, and the gate advisory (211.015-T, plan unit T12)."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from test_cascade_evidence_recovery import _recovered
from test_cli_gate_closure_evidence import (
    _MERGE_SHA,
    _READY,
    evidence_record,
    evidence_relpath,
    with_close_keys,
    write_evidence,
)
from test_cli_shipment_cascade_close import _BASE, _EVIDENCE, _JSON_KEYS, _MUTATING, _json, _run, _Stubs

from autoharness import cli
from autoharness.cli import SHIPMENT_USAGE, main
from autoharness.gates.closure_contract import build_closure_path
from autoharness.shipment_close import recover
from autoharness.shipment_close.command import CascadeCloseOutcome
from autoharness.shipment_close.recover import RecoverOptions, RecoverOutcome

_JOURNAL = Path("ws/.autoharness/gates/cascade-close/900-S-600-F.journal")
_RECOVER = ("shipment", "cascade-close", "--shipment", "900-S", "--feature", "600-F", "--recover")


def _recover_json(*argv: str, outcome: RecoverOutcome):
    with _Stubs() as stubs, mock.patch.object(recover, "recover_cascade_close", return_value=outcome) as called:
        out, _err, code = _run(*argv, "--json")
    return json.loads(out), code, stubs, called


class RecoverCliTests(unittest.TestCase):
    def test_recover_routes_to_the_recovery_entry_point_and_resolves_no_binary(self) -> None:
        outcome = RecoverOutcome(
            0,
            "recovered",
            evidence_path=_EVIDENCE,
            journal_path=_JOURNAL,
            recovered=True,
            recovery_mode="journal_complete",
            action="reconstruct",
            phase_written="post_close",
            postcondition_verdict="pass",
        )
        payload, code, stubs, called = _recover_json(*_RECOVER, outcome=outcome)
        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"], "recover")
        self.assertIs(payload["recovered"], True)
        self.assertEqual(payload["recovery_mode"], "journal_complete")
        self.assertEqual(payload["journal_path"], str(_JOURNAL))
        self.assertEqual(payload["phase_written"], "post_close")
        self.assertEqual(payload["mutation_possible"], "yes")
        self.assertEqual(payload["operator_action"], "none")
        self.assertIs(payload["dry_run"], False)
        self.assertTrue(set(payload) >= _JSON_KEYS)
        stubs.resolve.assert_not_called()
        stubs.mutating.assert_not_called()
        stubs.classify.assert_not_called()
        called.assert_called_once()
        self.assertEqual(called.call_args.args[1:3], ("900-S", "600-F"))
        self.assertEqual(called.call_args.kwargs["options"], RecoverOptions())

    def test_flags_reach_the_options(self) -> None:
        outcome = RecoverOutcome(0, "dry", dry_run=True)
        payload, _code, _stubs, called = _recover_json(
            *_RECOVER, "--dry-run", "--confirm-owner-dead", "--confirm-engine-stopped", outcome=outcome
        )
        self.assertIs(payload["dry_run"], True)
        self.assertEqual(
            called.call_args.kwargs["options"],
            RecoverOptions(dry_run=True, confirm_owner_dead=True, confirm_engine_stopped=True),
        )
        self.assertEqual(payload["mutation_possible"], "unknown")

    def test_exit_10_is_a_review_required_refusal(self) -> None:
        outcome = RecoverOutcome(10, "refused: the lock owner is not provably dead", evidence_path=_EVIDENCE)
        payload, code, _stubs, _called = _recover_json(*_RECOVER, outcome=outcome)
        self.assertEqual(code, 10)
        self.assertEqual(payload["operator_action"], "review_required")
        self.assertEqual(payload["mutation_possible"], "unknown")
        self.assertIs(payload["recovered"], False)
        self.assertIn("refused: the lock owner is not provably dead", payload["failures"])

    def test_a_rollback_is_mutation_free_exit_2(self) -> None:
        outcome = RecoverOutcome(2, "rolled back", evidence_path=_EVIDENCE, action="rollback", phase_written="pre_close")
        payload, code, _stubs, _called = _recover_json(*_RECOVER, outcome=outcome)
        self.assertEqual(code, 2)
        self.assertEqual(payload["mutation_possible"], "no")
        self.assertEqual(payload["phase_written"], "pre_close")
        self.assertEqual(payload["recovery_action"], "rollback")

    def test_failure_records_are_review_required_exit_5(self) -> None:
        outcome = RecoverOutcome(5, "failed", recovered=True, recovery_mode="journal_complete", failures=("missing_required: x",))
        payload, code, _stubs, _called = _recover_json(*_RECOVER, outcome=outcome)
        self.assertEqual((code, payload["operator_action"], payload["mutation_possible"]), (5, "review_required", "yes"))
        self.assertIn("missing_required: x", payload["failures"])

    def test_text_output_goes_to_stderr_for_refusals(self) -> None:
        outcome = RecoverOutcome(10, "refused", evidence_path=_EVIDENCE)
        with _Stubs(), mock.patch.object(recover, "recover_cascade_close", return_value=outcome):
            out, err, code = _run(*_RECOVER)
        self.assertEqual((out, code), ("", 10))
        self.assertIn("cascade-close (recover) — exit 10: refused", err)

    def test_argument_rules(self) -> None:
        for label, argv in (
            ("dry-run alone", (*_BASE, "--dry-run")),
            ("confirm-owner-dead alone", (*_MUTATING, "--confirm-owner-dead")),
            ("confirm-engine-stopped alone", (*_BASE, "--classify-only", "--confirm-engine-stopped")),
            ("recover with message", (*_RECOVER, "--message", "x")),
            ("recover with sha", (*_RECOVER, "--sha", "a" * 40)),
            ("recover with timeout", (*_RECOVER, "--timeout", "60")),
            ("recover with detach", (*_RECOVER, "--detach")),
            ("recover with poll", (*_RECOVER, "--poll")),
            ("recover with wait", (*_RECOVER, "--wait", "5")),
            ("recover with classify-only", (*_RECOVER, "--classify-only")),
            ("recover with caller-wait", (*_RECOVER, "--caller-wait", "9")),
            ("recover without shipment", ("shipment", "cascade-close", "--feature", "600-F", "--recover")),
        ):
            with self.subTest(label):
                with _Stubs() as stubs, mock.patch.object(recover, "recover_cascade_close") as called:
                    _out, _err, code = _run(*argv)
                self.assertEqual(code, 2)
                called.assert_not_called()
                stubs.mutating.assert_not_called()

    def test_usage_documents_recovery_and_exit_10(self) -> None:
        for text in ("--recover", "--dry-run", "--confirm-owner-dead", "--confirm-engine-stopped", "  10  --recover"):
            self.assertIn(text, SHIPMENT_USAGE)


class RecoveryAvailableCliTests(unittest.TestCase):
    def test_exit_7_with_a_recoverable_run_names_the_recovery_command_and_sets_the_flag(self) -> None:
        outcome = CascadeCloseOutcome(exit_code=7, message="an invoking record exists", evidence_path=_EVIDENCE, recovery_available=True)
        payload, code, _stubs = _json(*_MUTATING, mutating=outcome)
        self.assertEqual(code, 7)
        self.assertIs(payload["recovery_available"], True)
        self.assertTrue(any("--recover --dry-run" in failure for failure in payload["failures"]), payload["failures"])
        with _Stubs(mutating=outcome):
            _out, err, _code = _run(*_MUTATING)
        self.assertIn("--recover --dry-run", err)

    def test_exit_7_that_is_not_recoverable_says_so_and_never_suggests_recovery(self) -> None:
        outcome = CascadeCloseOutcome(exit_code=7, message="lock held", evidence_path=_EVIDENCE, recovery_available=False)
        payload, _code, _stubs = _json(*_MUTATING, mutating=outcome)
        self.assertIs(payload["recovery_available"], False)
        self.assertFalse(any("--recover" in failure for failure in payload["failures"]))

    def test_the_key_set_of_every_other_outcome_is_unchanged(self) -> None:
        for exit_code in (0, 2, 5, 6, 8):
            with self.subTest(exit_code=exit_code):
                outcome = CascadeCloseOutcome(exit_code=exit_code, message="m", evidence_path=_EVIDENCE, recovery_available=True)
                payload, _code, _stubs = _json(*_MUTATING, mutating=outcome)
                self.assertEqual(set(payload), _JSON_KEYS)
        payload, _code, _stubs = _json(*_MUTATING, mutating=CascadeCloseOutcome(exit_code=7, message="m"))
        self.assertEqual(set(payload), _JSON_KEYS)


class GateAdvisoryTests(unittest.TestCase):
    """The closure-evidence gate keeps its exact output for ordinary records and adds an advisory for recovered ones."""

    _SHIP, _FEAT = "175-S", "167-F"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve() / "workspace"
        (self.root / "docs" / "closure").mkdir(parents=True)

    def _gate(self, record: dict, *, text: bool = False):
        write_evidence(self.root, self._SHIP, self._FEAT, record)
        logs = self.root / ".backlogit" / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        for item in [self._SHIP, *[m["id"] for m in record["pre_close"]["manifest_members"]]]:
            (logs / f"{item}.jsonl").write_text("", encoding="utf-8")
        body = with_close_keys(_READY, "cascade", evidence_relpath(self._SHIP, self._FEAT), merge_commit=_MERGE_SHA)
        path = build_closure_path("docs/closure", self._SHIP, self._FEAT, workspace_root=self.root)
        path.write_text(body, encoding="utf-8")
        from datetime import datetime, timezone

        argv = ["gate", "closure-evidence", "--path", str(path), "--workspace", str(self.root)]
        if not text:
            argv.append("--json")
        out, err = io.StringIO(), io.StringIO()
        code: int | None = 0
        with mock.patch.object(cli, "_merge_committer_time", return_value=datetime(2026, 10, 1, 23, 0, tzinfo=timezone.utc)):
            try:
                with redirect_stdout(out), redirect_stderr(err):
                    main(argv)
            except SystemExit as exc:
                code = exc.code
        return out.getvalue(), code

    def _recovered_record(self) -> dict:
        record = evidence_record("cascade", self._SHIP, self._FEAT)
        facts = {
            "exit_code": "observed_journal",
            "timed_out": "observed_journal",
            "finished_at": "observed_journal",
            "stdout": "observed_journal",
            "stderr": "observed_journal",
            "archived_ids": "observed_journal",
            "returned_ids": "observed_journal",
            "commit_sha": "observed_journal",
            "mutation_state": "observed_journal",
        }
        template = _recovered("journal_complete")["recovery"]
        record["run_id"] = template["recovery_run_id"]
        record["recovery"] = {**template, "facts": facts}
        return record

    def test_an_ordinary_record_keeps_the_exact_gate_output(self) -> None:
        out, code = self._gate(evidence_record("cascade", self._SHIP, self._FEAT))
        payload = json.loads(out)
        self.assertIn(code, (0, None), payload)
        self.assertNotIn("evidence_recovered", payload)
        self.assertNotIn("recovery_mode", payload)

    def test_a_recovered_record_passes_with_an_advisory(self) -> None:
        out, code = self._gate(self._recovered_record())
        payload = json.loads(out)
        self.assertIn(code, (0, None), payload)
        self.assertIs(payload["evidence_recovered"], True)
        self.assertEqual(payload["recovery_mode"], "journal_complete")
        self.assertTrue(any("RECOVERED" in warning for warning in payload["warnings"]), payload["warnings"])

    def test_text_output_prints_the_advisory(self) -> None:
        out, _code = self._gate(self._recovered_record(), text=True)
        self.assertIn("PASS", out)
        self.assertIn("Advisory", out)
        self.assertIn("journal_complete", out)

    def test_a_structurally_valid_failure_record_is_still_refused(self) -> None:
        record = self._recovered_record()
        record["post_close"]["postcondition_verdict"] = "fail"
        record["post_close"]["failures"] = ["missing_required: x"]
        out, code = self._gate(record)
        payload = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(payload["failed_check"], "close_evidence")


class RecoverMutationFlagTests(unittest.TestCase):
    def test_a_recover_input_error_never_reports_possible_mutation(self) -> None:
        payload = cli._cascade_close_payload("recover", 2, "evidence already finalized", RecoverOutcome(2, "x"))
        self.assertEqual(payload["mutation_possible"], "no")

    def test_a_refused_recover_stays_unknown_and_a_recovered_one_is_yes(self) -> None:
        refused = cli._cascade_close_payload("recover", 10, "refused", RecoverOutcome(10, "x"))
        self.assertEqual(refused["mutation_possible"], "unknown")
        recovered = cli._cascade_close_payload("recover", 0, "ok", RecoverOutcome(0, "x", recovered=True))
        self.assertEqual(recovered["mutation_possible"], "yes")


if __name__ == "__main__":
    unittest.main()
