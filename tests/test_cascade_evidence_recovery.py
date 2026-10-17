"""Validator and record-builder tests for the additive ``recovery`` block (211-F, plan unit T9; hardening H4)."""

from __future__ import annotations

import copy
import unittest

from autoharness.gates import cascade_evidence
from autoharness.gates.cascade_evidence import (
    build_recovery_block,
    unavailable_capture,
    validate_evidence_record,
    validate_evidence_structure,
)
from test_cascade_evidence_contract import _FEATURE, _SHIPMENT, cascade_record

_ORIGINAL_RUN = "0123456789abcdef0123456789abcdef"
_RECOVERY_RUN = "fedcba9876543210fedcba9876543210"
_SHIPPED_AT = "2026-10-02T00:00:02+00:00"

_COMPLETE_FACTS = {
    "exit_code": "observed_journal",
    "timed_out": "observed_journal",
    "finished_at": "observed_journal",
    "stdout": "observed_journal",
    "stderr": "observed_journal",
    "archived_ids": "observed_journal",
    "returned_ids": "observed_journal",
    "commit_sha": "observed_journal",
    "mutation_state": "derived_live_state",
}
_ATTRIBUTED_FACTS = {
    "exit_code": "unknown",
    "timed_out": "unknown",
    "finished_at": "engine_event_log",
    "stdout": "unknown",
    "stderr": "unknown",
    "archived_ids": "engine_event_log",
    "returned_ids": "derived_live_state",
    "commit_sha": "unknown",
    "mutation_state": "derived_live_state",
}


def _attribution() -> dict:
    return {"basis": "engine_event_log", "shipped_event_at": _SHIPPED_AT, "operation": _SHIPMENT}


def _recovered(mode: str = "journal_complete") -> dict:
    record = cascade_record()
    record["run_id"] = _RECOVERY_RUN
    if mode == "journal_complete":
        facts, attribution = dict(_COMPLETE_FACTS), None
    else:
        facts, attribution = dict(_ATTRIBUTED_FACTS), _attribution()
        invocation = record["invocation"]
        invocation["exit_code"] = None
        invocation["timed_out"] = None
        invocation["finished_at"] = _SHIPPED_AT
        invocation["stdout"] = unavailable_capture("the journal was not retained")
        invocation["stderr"] = unavailable_capture("the journal was not retained")
        record["post_close"]["parsed_result"]["commit_sha"] = None
    record["recovery"] = build_recovery_block(
        mode=mode,
        recovered_at="2026-10-02T01:00:00Z",
        recovery_run_id=_RECOVERY_RUN,
        supersedes_run_id=_ORIGINAL_RUN,
        lock_disposition={
            "action": "tombstoned",
            "owner_pid": 4242,
            "owner_host": "ci-host",
            "basis": "pid_absent",
        },
        engine_attribution=attribution,
        facts=facts,
    )
    return record


def _strict(record: dict) -> list[str]:
    return validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="cascade")


def _structure(record: dict) -> list[str]:
    return validate_evidence_structure(record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="cascade")


def _mutate(mode: str, mutation) -> dict:
    record = _recovered(mode)
    mutation(record)
    return record


def _facts(record: dict) -> dict:
    return record["recovery"]["facts"]


class RecoveredRecordAcceptanceTests(unittest.TestCase):
    def test_journal_complete_record_validates(self) -> None:
        self.assertEqual(_strict(_recovered("journal_complete")), [])

    def test_attributed_records_with_unknown_facts_validate(self) -> None:
        for mode in ("journal_partial", "postconditions_only"):
            with self.subTest(mode=mode):
                self.assertEqual(_strict(_recovered(mode)), [])

    def test_null_finished_at_is_tolerated_only_under_a_recovery_block(self) -> None:
        def unknown_finish(record: dict) -> None:
            record["invocation"]["finished_at"] = None
            _facts(record)["finished_at"] = "unknown"

        self.assertEqual(_strict(_mutate("journal_partial", unknown_finish)), [])
        record = _mutate("journal_partial", unknown_finish)
        del record["recovery"]
        self.assertTrue(any("finished_at" in problem for problem in _strict(record)))

    def test_builder_output_is_json_shaped(self) -> None:
        block = _recovered("journal_complete")["recovery"]
        self.assertIs(block["recovered"], True)
        self.assertEqual(block["supersedes_run_id"], _ORIGINAL_RUN)
        self.assertEqual(set(block["facts"]), set(cascade_evidence.RECOVERY_FACT_KEYS))


class StrippedRecoveryBlockTests(unittest.TestCase):
    """H4 mutation test: remove the block and the original failures return."""

    def test_every_relaxed_field_fails_again_without_the_block(self) -> None:
        expected = {
            "journal_partial": ("exit_code", "timed_out", "stdout", "stderr"),
            "postconditions_only": ("exit_code", "timed_out", "stdout", "stderr"),
        }
        for mode, fields in expected.items():
            record = _recovered(mode)
            del record["recovery"]
            problems = _strict(record)
            for name in fields:
                with self.subTest(mode=mode, field=name):
                    self.assertTrue(any(f"invocation.{name}" in problem for problem in problems), problems)

    def test_returned_ids_unknown_fails_without_the_block(self) -> None:
        def unknown_returned(record: dict) -> None:
            record["post_close"]["parsed_result"]["returned_ids"] = None
            _facts(record)["returned_ids"] = "unknown"

        self.assertEqual(_strict(_mutate("journal_partial", unknown_returned)), [])
        record = _mutate("journal_partial", unknown_returned)
        del record["recovery"]
        self.assertTrue(any("returned_ids" in problem for problem in _strict(record)))

    def test_commit_sha_unknown_requires_null(self) -> None:
        record = _recovered("journal_partial")
        record["post_close"]["parsed_result"]["commit_sha"] = "a" * 40
        self.assertTrue(any("commit_sha" in problem for problem in _strict(record)))

    def test_mutation_state_indeterminate_fails_without_the_block(self) -> None:
        record = _recovered("journal_partial")
        record["invocation"]["mutation_state"] = "indeterminate"
        self.assertTrue(any("mutation_state" in problem for problem in _strict(record)))


class RecoveryBlockStructureTests(unittest.TestCase):
    def _problems(self, mutation, mode: str = "journal_complete") -> list[str]:
        return _strict(_mutate(mode, mutation))

    def test_missing_extra_and_malformed_block_keys(self) -> None:
        self.assertTrue(self._problems(lambda r: r["recovery"].pop("mode")))
        self.assertTrue(self._problems(lambda r: r["recovery"].update(extra=1)))
        self.assertTrue(self._problems(lambda r: r["recovery"].update(recovered=False)))
        self.assertTrue(self._problems(lambda r: r["recovery"].update(mode="guessed")))
        self.assertTrue(self._problems(lambda r: r.update(recovery="yes")))

    def test_facts_map_must_cover_exactly_the_enumerated_fields(self) -> None:
        self.assertTrue(any("facts" in p for p in self._problems(lambda r: _facts(r).pop("exit_code"))))
        self.assertTrue(any("facts" in p for p in self._problems(lambda r: _facts(r).update(bogus="unknown"))))
        self.assertTrue(any("facts" in p for p in self._problems(lambda r: _facts(r).update(exit_code="guessed"))))

    def test_run_identifiers_are_bound(self) -> None:
        self.assertTrue(any("recovery_run_id" in p for p in self._problems(lambda r: r["recovery"].update(recovery_run_id=_ORIGINAL_RUN))))
        self.assertTrue(any("supersedes_run_id" in p for p in self._problems(lambda r: r["recovery"].update(supersedes_run_id=_RECOVERY_RUN))))
        self.assertTrue(any("recovered_at" in p for p in self._problems(lambda r: r["recovery"].update(recovered_at="not a time"))))
        self.assertTrue(any("recovered_at" in p for p in self._problems(lambda r: r["recovery"].update(recovered_at="2026-10-02T00:00:00Z"))))

    def test_lock_disposition_is_validated_and_consistent(self) -> None:
        def basis(value: str):
            return lambda r: r["recovery"]["lock_disposition"].update(basis=value)

        self.assertTrue(any("lock_disposition" in p for p in self._problems(basis("operator_confirmed"))))
        self.assertTrue(any("lock_disposition" in p for p in self._problems(basis("guessed"))))
        self.assertTrue(any("lock_disposition" in p for p in self._problems(lambda r: r["recovery"].update(lock_disposition=None))))
        self.assertEqual(
            self._problems(
                lambda r: r["recovery"].update(
                    lock_disposition={"action": "absent", "owner_pid": None, "owner_host": None, "basis": "lock_absent"}
                )
            ),
            [],
        )

    def test_recovery_block_is_refused_on_a_safe_close_record(self) -> None:
        record = cascade_evidence_safe_close()
        record["recovery"] = _recovered()["recovery"]
        problems = validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="safe_close")
        self.assertTrue(any("recovery" in p for p in problems))


def cascade_evidence_safe_close() -> dict:
    from test_cascade_evidence_contract import safe_close_record

    return safe_close_record()


class AntiFabricationTests(unittest.TestCase):
    def test_observed_exit_code_requires_an_integer(self) -> None:
        record = _mutate("journal_complete", lambda r: r["invocation"].update(exit_code=None))
        self.assertTrue(any("exit_code" in p for p in _strict(record)))

    def test_unknown_exit_code_may_not_carry_a_value(self) -> None:
        record = _mutate("journal_partial", lambda r: r["invocation"].update(exit_code=0))
        self.assertTrue(any("exit_code" in p for p in _strict(record)))

    def test_unknown_timed_out_may_not_carry_a_value(self) -> None:
        record = _mutate("journal_partial", lambda r: r["invocation"].update(timed_out=False))
        self.assertTrue(any("timed_out" in p for p in _strict(record)))

    def test_forged_observed_stdout_without_capture_data_is_rejected(self) -> None:
        for stream in ("stdout", "stderr"):
            with self.subTest(stream=stream):
                record = _mutate(
                    "journal_complete", lambda r: r["invocation"].update({stream: unavailable_capture("lost")})
                )
                self.assertTrue(any(stream in p for p in _strict(record)))

    def test_unknown_stdout_must_be_the_explicit_unavailable_marker(self) -> None:
        record = _mutate("journal_partial", lambda r: r["invocation"].update(stdout=copy.deepcopy(cascade_record()["invocation"]["stdout"])))
        self.assertTrue(any("stdout" in p for p in _strict(record)))
        record = _mutate("journal_partial", lambda r: r["invocation"].update(stdout={"availability": "unavailable"}))
        self.assertTrue(any("stdout" in p for p in _strict(record)))

    def test_unknown_finished_at_requires_null_and_other_values_a_timestamp(self) -> None:
        record = _mutate("journal_partial", lambda r: _facts(r).update(finished_at="unknown"))
        self.assertTrue(any("finished_at" in p for p in _strict(record)))
        record = _mutate("journal_complete", lambda r: r["invocation"].update(finished_at=None))
        self.assertTrue(any("finished_at" in p for p in _strict(record)))

    def test_engine_finished_at_must_equal_the_attributed_shipped_event(self) -> None:
        record = _mutate("journal_partial", lambda r: r["invocation"].update(finished_at="2026-10-02T00:00:05Z"))
        self.assertTrue(any("finished_at" in p for p in _strict(record)))

    def test_mutation_state_none_is_rejected_for_recovered_cascades(self) -> None:
        for mode in ("journal_complete", "journal_partial"):
            with self.subTest(mode=mode):
                record = _mutate(mode, lambda r: r["invocation"].update(mutation_state="none"))
                self.assertTrue(any("mutation_state" in p for p in _strict(record)))
                self.assertTrue(any("mutation_state" in p for p in _structure(record)))

    def test_journal_complete_cannot_claim_unobserved_facts(self) -> None:
        for key in ("stdout", "exit_code", "archived_ids", "returned_ids"):
            with self.subTest(key=key):
                record = _mutate("journal_complete", lambda r: _facts(r).update({key: "unknown"}))
                self.assertTrue(_strict(record))

    def test_engine_derived_facts_need_attribution(self) -> None:
        record = _mutate("journal_partial", lambda r: r["recovery"].update(engine_attribution=None))
        self.assertTrue(any("engine_attribution" in p for p in _strict(record)))
        record = _mutate("postconditions_only", lambda r: r["recovery"].update(engine_attribution=None))
        self.assertTrue(any("engine_attribution" in p for p in _strict(record)))

    def test_postconditions_only_cannot_claim_journal_observations(self) -> None:
        record = _mutate("postconditions_only", lambda r: _facts(r).update(archived_ids="observed_journal"))
        self.assertTrue(_strict(record))
        record = _mutate("postconditions_only", lambda r: _facts(r).update(exit_code="observed_journal"))
        self.assertTrue(_strict(record))

    def test_attribution_shape_operation_and_time(self) -> None:
        def set_attr(**changes):
            return lambda r: r["recovery"]["engine_attribution"].update(changes)

        for changes in (
            {"operation": "999-S"},
            {"shipped_event_at": "2026-10-01T23:59:59Z"},
            {"shipped_event_at": "garbage"},
            {"basis": "journal"},
        ):
            with self.subTest(changes=changes):
                self.assertTrue(any("engine_attribution" in p or "finished_at" in p for p in _strict(_mutate("journal_partial", set_attr(**changes)))))

    def test_returned_ids_unknown_requires_null_and_derived_requires_empty(self) -> None:
        record = _mutate("journal_partial", lambda r: _facts(r).update(returned_ids="unknown"))
        self.assertTrue(any("returned_ids" in p for p in _strict(record)))
        record = _mutate("journal_partial", lambda r: r["post_close"]["parsed_result"].update(returned_ids=["x"]))
        self.assertTrue(any("returned_ids" in p for p in _strict(record)))

    def test_partial_journal_observed_capture_must_be_marked_truncated(self) -> None:
        def observe_stdout(record: dict) -> None:
            _facts(record)["stdout"] = "observed_journal"
            record["invocation"]["stdout"] = copy.deepcopy(cascade_record()["invocation"]["stdout"])

        record = _mutate("journal_partial", observe_stdout)
        self.assertTrue(any("capture_truncated" in p for p in _strict(record)))
        record["invocation"]["stdout"]["capture_truncated"] = True
        self.assertEqual(_strict(record), [])

    def test_recomputations_still_apply_to_recovered_records(self) -> None:
        record = _mutate("journal_complete", lambda r: r["post_close"]["parsed_result"]["archived_ids"].pop())
        self.assertTrue(_strict(record))
        record = _mutate("journal_complete", lambda r: r["post_close"].update(shipment_archived_shipped=False))
        self.assertTrue(_strict(record))


class StructureValidatorTests(unittest.TestCase):
    def _failing(self, mode: str = "journal_complete") -> dict:
        record = _recovered(mode)
        post = record["post_close"]
        post["parsed_result"]["archived_ids"] = ["192.001-T", _SHIPMENT]
        post["missing_required"] = ["192-F"]
        post["postcondition_verdict"] = "fail"
        post["failures"] = ["missing_required: ['192-F'] not archived"]
        return record

    def test_consistent_fail_record_validates_structurally_and_is_refused_by_the_gate_validator(self) -> None:
        record = self._failing()
        self.assertEqual(_structure(record), [])
        self.assertTrue(_strict(record))

    def test_pass_records_validate_under_both(self) -> None:
        for mode in ("journal_complete", "journal_partial", "postconditions_only"):
            with self.subTest(mode=mode):
                self.assertEqual(_structure(_recovered(mode)), [])

    def test_inconsistent_fail_records_are_rejected(self) -> None:
        record = self._failing()
        record["post_close"]["failures"] = []
        self.assertTrue(_structure(record))
        record = self._failing()
        record["post_close"]["missing_required"] = []
        self.assertTrue(_structure(record))
        record = self._failing()
        record["post_close"]["postcondition_verdict"] = "pass"
        self.assertTrue(_structure(record))
        record = _recovered()
        record["post_close"]["failures"] = ["x"]
        self.assertTrue(_structure(record))

    def test_structure_validation_still_checks_shape_pair_and_recovery_block(self) -> None:
        record = self._failing()
        record["shipment_id"] = "999-S"
        self.assertTrue(_structure(record))
        record = self._failing()
        _facts(record).pop("stdout")
        self.assertTrue(_structure(record))

    def test_partial_footprint_with_nonzero_exit_and_unparsed_stdout(self) -> None:
        record = _recovered("journal_complete")
        record["invocation"].update(exit_code=1, mutation_state="indeterminate")
        post = record["post_close"]
        post.update(parsed_result=None, parse_error="stdout is empty", postcondition_verdict="fail")
        post.update(failures=["parse_error: stdout is empty"])
        post["unexpected_archived"], post["missing_required"] = [], []
        facts = _facts(record)
        facts.update(archived_ids="unknown", returned_ids="unknown", commit_sha="unknown")
        self.assertEqual(_structure(record), [])
        self.assertTrue(_strict(record))


if __name__ == "__main__":
    unittest.main()
