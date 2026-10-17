"""``cascade-close --recover`` reconstruction (211.011-T, plan unit T11; hardening H1, H4, H8, H9).

The orphaned ``invoking`` state comes from really running the attached command against the fake backlogit and killing
the finalizer, so the journal (``exit.json`` with its quiescence verdict, the raw streams) is genuine. Engine event
logs are synthesized to the shape the spike characterized, with and without the operation correlation real logs lack.
"""

from __future__ import annotations

import copy
import datetime
import hashlib
import json
import os
import shutil
import unittest
from pathlib import Path

from test_shipment_cascade_close_invoke import (
    _ARCHIVED,
    _FEATURE,
    _SHA,
    _SHIPMENT,
    _TASK,
    _envelope,
)
from test_shipment_close_recover_eligibility import (
    _Orphan,
    _options,
    _quiet_env,
)

from autoharness.gates.cascade_evidence import validate_evidence_record, validate_evidence_structure
from autoharness.shipment_close import EXIT_INPUT, EXIT_INVOCATION_INDETERMINATE, EXIT_OK, EXIT_POSTCONDITION_FAILED
from autoharness.shipment_close import EXIT_RECOVERY_REFUSED
from autoharness.shipment_close.journal import write_json
from autoharness.shipment_close.recover import recover_cascade_close

_RECOVERY_RUN = "b" * 32


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _local(started: str, plus_seconds: float, *, offset_hours: int = 2) -> str:
    """An offset-bearing timestamp ``plus_seconds`` after ``started`` (an instant), as the engine writes them."""

    instant = datetime.datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    zone = datetime.timezone(datetime.timedelta(hours=offset_hours))
    return (instant + datetime.timedelta(seconds=plus_seconds)).astimezone(zone).isoformat()


def _event(item: str, timestamp: str, event_type: str, delta: dict, actor: str = "backlogit") -> str:
    return json.dumps(
        {"timestamp": timestamp, "actor": actor, "item_id": item, "event_type": event_type, "delta": delta}
    )


class _Recovery(_Orphan):
    def write_logs(
        self,
        *,
        correlated: bool = True,
        shipped: bool = True,
        archived: tuple[str, ...] = tuple(_ARCHIVED),
        foreign_on: str | None = None,
    ) -> None:
        started = self.record()["invocation"]["started_at"]
        logs = self.backlog / "logs"
        logs.mkdir(exist_ok=True)
        operation = {"_shipment_operation": _SHIPMENT} if correlated else {}
        shipment_events = [
            _event(_SHIPMENT, _local(started, -3600), "shipment_created", {"items": [_FEATURE, _TASK]}),
        ]
        if shipped:
            shipment_events.append(
                _event(
                    _SHIPMENT,
                    _local(started, 2),
                    "shipment_status_changed",
                    {"status": "shipped", "_shipment_operation": _SHIPMENT},
                )
            )
        per_item: dict[str, list[str]] = {_FEATURE: [], _TASK: []}
        for index, item in enumerate(archived):
            line = _event(item, _local(started, 3 + index), "archived", {"archive_path": f".backlogit/archive/{item}.md", **operation})
            (shipment_events if item == _SHIPMENT else per_item.setdefault(item, [])).append(line)
        if foreign_on is not None:
            line = _event(foreign_on, _local(started, 4), "status_changed", {"to": "done"}, actor="a-human")
            (shipment_events if foreign_on == _SHIPMENT else per_item.setdefault(foreign_on, [])).append(line)
        (logs / f"{_SHIPMENT}.jsonl").write_text("\n".join(shipment_events) + "\n", encoding="utf-8")
        for item, lines in per_item.items():
            (logs / f"{item}.jsonl").write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")

    def mark_unproven(self) -> None:
        journal = self.journal()
        exit_record = json.loads((self.journal_dir / "exit.json").read_text(encoding="utf-8"))
        exit_record["quiescence"]["stdout"]["proven"] = False
        write_json(journal, "exit.json", exit_record)

    def run_recovery(self, **options: object):
        return recover_cascade_close(
            self.root, _SHIPMENT, _FEATURE, options=_options(**options), env=_quiet_env(), run_id=_RECOVERY_RUN
        )

    def validate(self, record: dict, *, strict: bool = True) -> list[str]:
        check = validate_evidence_record if strict else validate_evidence_structure
        return check(record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="cascade")


class JournalCompleteTests(unittest.TestCase):
    def test_a_complete_journal_is_recovered_and_the_record_passes_the_gate_validator(self) -> None:
        orphan = _Recovery(self)
        original_run = orphan.record()["run_id"]
        ship_calls = len([a for a in orphan.argv_log() if "ship" in a])
        before_tree = _tree_digest(orphan.backlog)
        outcome = orphan.run_recovery()
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        self.assertTrue(outcome.recovered)
        self.assertEqual(outcome.recovery_mode, "journal_complete")
        record = orphan.record()
        self.assertEqual(record["phase"], "post_close")
        self.assertEqual(record["run_id"], _RECOVERY_RUN)
        self.assertEqual(orphan.validate(record), [])
        block = record["recovery"]
        self.assertEqual((block["mode"], block["supersedes_run_id"], block["recovery_run_id"]), ("journal_complete", original_run, _RECOVERY_RUN))
        self.assertEqual(set(block["facts"].values()) - {"observed_journal"}, set())
        self.assertEqual(record["invocation"]["exit_code"], 0)
        self.assertEqual(record["post_close"]["parsed_result"]["commit_sha"], _SHA)
        self.assertEqual(sorted(record["post_close"]["parsed_result"]["archived_ids"]), sorted(_ARCHIVED))
        self.assertEqual(block["lock_disposition"]["action"], "absent")
        self.assertEqual(
            len([a for a in orphan.argv_log() if "ship" in a]), ship_calls, "recovery never re-runs backlogit shipment ship"
        )
        self.assertEqual(_tree_digest(orphan.backlog), before_tree, "recovery never edits the backlog")
        self.assertFalse(orphan.lock_path.exists())

    def test_recovery_is_idempotent(self) -> None:
        orphan = _Recovery(self)
        self.assertEqual(orphan.run_recovery().exit_code, EXIT_OK)
        before = orphan.evidence.read_bytes()
        again = orphan.run_recovery()
        self.assertEqual(again.exit_code, EXIT_INPUT, again.message)
        self.assertIn("already finalized", again.message)
        self.assertEqual(orphan.evidence.read_bytes(), before)

    def test_a_dead_owner_lock_is_tombstoned(self) -> None:
        orphan = _Recovery(self)
        orphan.write_lock()
        outcome = orphan.run_recovery()
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        block = orphan.record()["recovery"]["lock_disposition"]
        self.assertEqual((block["action"], block["basis"]), ("tombstoned", "pid_absent"))
        self.assertEqual(len([n for n in os.listdir(orphan.lock_path.parent) if ".stale-" in n]), 1)
        self.assertFalse(orphan.lock_path.exists())

    def test_an_operator_confirmed_takeover_is_recorded_as_such(self) -> None:
        orphan = _Recovery(self)
        orphan.write_lock(host="some-other-host")
        outcome = orphan.run_recovery(confirm_owner_dead=True)
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        block = orphan.record()["recovery"]["lock_disposition"]
        self.assertEqual((block["action"], block["basis"]), ("operator_confirmed", "operator_confirmed"))
        self.assertEqual(block["owner_host"], "some-other-host")
        self.assertEqual(orphan.validate(orphan.record()), [])

    def test_uncorrelated_item_events_do_not_block_a_complete_journal(self) -> None:
        orphan = _Recovery(self)
        orphan.write_logs(correlated=False, foreign_on=_TASK)
        self.assertEqual(orphan.run_recovery().exit_code, EXIT_OK)
        self.assertEqual(orphan.validate(orphan.record()), [])

    def test_the_recovered_record_survives_the_gate_validator_with_a_missing_event_log(self) -> None:
        orphan = _Recovery(self)
        self.assertFalse((orphan.backlog / "logs").exists())
        self.assertEqual(orphan.run_recovery().exit_code, EXIT_OK)

    def test_dry_run_reports_the_mode_without_writing(self) -> None:
        orphan = _Recovery(self)
        before = orphan.evidence.read_bytes()
        outcome = orphan.run_recovery(dry_run=True)
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        self.assertEqual(outcome.recovery_mode, "journal_complete")
        self.assertFalse(outcome.recovered)
        self.assertEqual(orphan.evidence.read_bytes(), before)


class DeterminatePartialRecordTests(unittest.TestCase):
    def test_a_partial_footprint_is_persisted_as_exit_5_and_the_gate_still_refuses_it(self) -> None:
        ship = {"archive": [_TASK], "envelope": _envelope([_TASK])}
        orphan = _Recovery(self, ship=ship)
        outcome = orphan.run_recovery()
        self.assertEqual(outcome.exit_code, EXIT_POSTCONDITION_FAILED, outcome.message)
        self.assertTrue(outcome.recovered)
        record = orphan.record()
        self.assertEqual(record["post_close"]["postcondition_verdict"], "fail")
        self.assertTrue(record["post_close"]["missing_required"])
        self.assertEqual(orphan.validate(record, strict=False), [])
        self.assertTrue(orphan.validate(record, strict=True), "the closure-evidence gate keeps refusing a failure record")

    def test_unparsed_stdout_is_a_recorded_exit_6_with_unknown_engine_facts(self) -> None:
        ship = {"archive": [], "envelope": {"jsonrpc": "2.0", "id": 1, "error": {"code": -1, "message": "boom"}}, "exit": 1}
        orphan = _Recovery(self, ship=ship)
        outcome = orphan.run_recovery()
        self.assertEqual(outcome.exit_code, EXIT_INVOCATION_INDETERMINATE, outcome.message)
        record = orphan.record()
        self.assertIsNone(record["post_close"]["parsed_result"])
        self.assertEqual(record["recovery"]["facts"]["archived_ids"], "unknown")
        self.assertEqual(record["invocation"]["mutation_state"], "indeterminate")
        self.assertEqual(orphan.validate(record, strict=False), [])
        self.assertTrue(orphan.validate(record))


class PartialJournalTests(unittest.TestCase):
    def test_an_unproven_quiescence_verdict_is_never_a_complete_journal(self) -> None:
        orphan = _Recovery(self)
        orphan.mark_unproven()
        before = orphan.evidence.read_bytes()
        outcome = orphan.run_recovery()
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)
        self.assertIn("event log", outcome.message)
        self.assertEqual(orphan.evidence.read_bytes(), before)
        self.assertFalse(orphan.lock_path.exists())

    def test_a_stream_that_grew_after_the_verdict_is_not_complete(self) -> None:
        orphan = _Recovery(self)
        with open(orphan.journal_dir / "stdout.raw", "ab") as handle:
            handle.write(b" late bytes")
        self.assertEqual(orphan.run_recovery().exit_code, EXIT_RECOVERY_REFUSED)

    def test_a_partial_journal_with_correlated_engine_events_records_unknowns_as_null(self) -> None:
        orphan = _Recovery(self)
        orphan.mark_unproven()
        orphan.write_logs(correlated=True)
        outcome = orphan.run_recovery()
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        self.assertEqual(outcome.recovery_mode, "journal_partial")
        record = orphan.record()
        self.assertEqual(orphan.validate(record), [])
        facts = record["recovery"]["facts"]
        self.assertEqual(facts["archived_ids"], "engine_event_log")
        self.assertEqual(facts["stdout"], "unknown")
        self.assertEqual(record["invocation"]["stdout"], {"availability": "unavailable", "reason": record["invocation"]["stdout"]["reason"]})
        self.assertIsNone(record["post_close"]["parsed_result"]["commit_sha"], "an unobserved fact is never invented")
        self.assertEqual(facts["exit_code"], "observed_journal")
        self.assertEqual(record["recovery"]["engine_attribution"]["operation"], _SHIPMENT)

    def test_a_timed_out_sentinel_without_an_exit_code_is_a_determinate_exit_6_record(self) -> None:
        orphan = _Recovery(self)
        orphan.mark_unproven()
        orphan.write_logs(correlated=True)
        exit_record = json.loads((orphan.journal_dir / "exit.json").read_text(encoding="utf-8"))
        exit_record.update(state="timed_out", exit_code=None, timed_out=True)
        write_json(orphan.journal(), "exit.json", exit_record)
        outcome = orphan.run_recovery()
        self.assertEqual(outcome.exit_code, EXIT_INVOCATION_INDETERMINATE, outcome.message)
        self.assertTrue(outcome.recovered)
        record = orphan.record()
        facts = record["recovery"]["facts"]
        self.assertEqual((facts["exit_code"], facts["timed_out"]), ("unknown", "observed_journal"))
        self.assertIsNone(record["invocation"]["exit_code"])
        self.assertIs(record["invocation"]["timed_out"], True)
        self.assertEqual(orphan.validate(record, strict=False), [])

    def test_a_sentinel_without_a_finish_time_falls_back_to_the_engine_log(self) -> None:
        orphan = _Recovery(self)
        orphan.mark_unproven()
        orphan.write_logs(correlated=True)
        exit_record = json.loads((orphan.journal_dir / "exit.json").read_text(encoding="utf-8"))
        exit_record["finished_at"] = None
        write_json(orphan.journal(), "exit.json", exit_record)
        outcome = orphan.run_recovery()
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        record = orphan.record()
        self.assertEqual(record["recovery"]["facts"]["finished_at"], "engine_event_log")
        self.assertTrue(record["invocation"]["finished_at"])

    def test_offset_bearing_engine_timestamps_are_compared_as_utc_instants(self) -> None:
        for offset in (-7, 0, 14):
            with self.subTest(offset=offset):
                orphan = _Recovery(self)
                orphan.mark_unproven()
                started = orphan.record()["invocation"]["started_at"]
                orphan.write_logs()
                logs = orphan.backlog / "logs"
                for path in logs.glob("*.jsonl"):
                    text = path.read_text(encoding="utf-8")
                    for line in text.splitlines():
                        event = json.loads(line)
                        instant = datetime.datetime.fromisoformat(event["timestamp"])
                        event["timestamp"] = instant.astimezone(datetime.timezone(datetime.timedelta(hours=offset))).isoformat()
                        text = text.replace(line, json.dumps(event))
                    path.write_text(text, encoding="utf-8")
                self.assertEqual(orphan.run_recovery().exit_code, EXIT_OK)
                self.assertTrue(started)


class PostconditionsOnlyTests(unittest.TestCase):
    def _legacy(self, **kwargs: object) -> _Recovery:
        orphan = _Recovery(self, **kwargs)
        shutil.rmtree(orphan.journal_dir)
        return orphan

    def test_real_engine_logs_cannot_attribute_the_footprint_so_recovery_is_refused(self) -> None:
        orphan = self._legacy()
        orphan.write_logs(correlated=False)
        before = orphan.evidence.read_bytes()
        outcome = orphan.run_recovery(confirm_engine_stopped=True)
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)
        self.assertIn("correlat", outcome.message)
        self.assertEqual(orphan.evidence.read_bytes(), before)
        self.assertFalse(orphan.lock_path.exists())

    def test_identical_live_state_with_no_engine_event_is_refused(self) -> None:
        orphan = self._legacy()
        orphan.write_logs(correlated=True, shipped=False)
        self.assertEqual(orphan.run_recovery(confirm_engine_stopped=True).exit_code, EXIT_RECOVERY_REFUSED)

    def test_a_missing_event_log_is_refused_not_treated_as_empty(self) -> None:
        orphan = self._legacy()
        self.assertEqual(orphan.run_recovery(confirm_engine_stopped=True).exit_code, EXIT_RECOVERY_REFUSED)

    def test_an_engine_that_stopped_partially_and_a_human_who_finished_the_archival_is_refused(self) -> None:
        orphan = self._legacy()
        orphan.write_logs(correlated=True, archived=(_FEATURE, _SHIPMENT), foreign_on=_TASK)
        outcome = orphan.run_recovery(confirm_engine_stopped=True)
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)

    def test_a_foreign_actor_event_in_the_window_is_refused_even_when_every_archive_is_correlated(self) -> None:
        orphan = self._legacy()
        orphan.write_logs(correlated=True, foreign_on=_TASK)
        self.assertEqual(orphan.run_recovery(confirm_engine_stopped=True).exit_code, EXIT_RECOVERY_REFUSED)

    def test_a_correlated_footprint_yields_a_postconditions_only_record_with_every_unknown_null(self) -> None:
        orphan = self._legacy()
        orphan.write_logs(correlated=True)
        outcome = orphan.run_recovery(confirm_engine_stopped=True)
        self.assertEqual(outcome.exit_code, EXIT_OK, outcome.message)
        self.assertEqual(outcome.recovery_mode, "postconditions_only")
        record = orphan.record()
        self.assertEqual(orphan.validate(record), [])
        invocation = record["invocation"]
        self.assertEqual((invocation["exit_code"], invocation["timed_out"]), (None, None))
        self.assertEqual(invocation["stdout"]["availability"], "unavailable")
        facts = record["recovery"]["facts"]
        self.assertEqual(
            {key: facts[key] for key in ("exit_code", "timed_out", "stdout", "stderr", "commit_sha")},
            {key: "unknown" for key in ("exit_code", "timed_out", "stdout", "stderr", "commit_sha")},
        )
        self.assertEqual(facts["archived_ids"], "engine_event_log")
        self.assertEqual(facts["finished_at"], "engine_event_log")
        self.assertEqual(record["recovery"]["lock_disposition"]["action"], "absent")
        self.assertEqual(invocation["finished_at"], record["recovery"]["engine_attribution"]["shipped_event_at"])

    def test_stripping_the_recovery_block_returns_the_original_failures(self) -> None:
        orphan = self._legacy()
        orphan.write_logs(correlated=True)
        self.assertEqual(orphan.run_recovery(confirm_engine_stopped=True).exit_code, EXIT_OK)
        record = orphan.record()
        stripped = copy.deepcopy(record)
        del stripped["recovery"]
        problems = orphan.validate(stripped)
        self.assertTrue(any("exit_code" in p for p in problems) and any("stdout" in p for p in problems), problems)

    def test_a_footprint_not_matching_the_pre_close_baseline_is_refused_or_failed(self) -> None:
        orphan = self._legacy()
        orphan.write_logs(correlated=True, archived=(_FEATURE, _SHIPMENT))
        outcome = orphan.run_recovery(confirm_engine_stopped=True)
        self.assertEqual(outcome.exit_code, EXIT_RECOVERY_REFUSED, outcome.message)


if __name__ == "__main__":
    unittest.main()
