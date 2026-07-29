"""Tests for the JSONL epoch sink — emit-only (U4, task 051.006)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.telemetry import jsonl_sink
from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
    WorkSizingSnapshot,
)
from autoharness.telemetry.jsonl_sink import (
    TelemetryConflictError,
    append_epoch,
    find_epoch_digest,
)


def _epoch(task_id: str) -> ExecutionEpoch:
    return ExecutionEpoch(
        task_id=task_id,
        route=RouteConfiguration(models=("gpt-5.4",)),
        economics=EconomicPayload(input_tokens=10, output_tokens=5),
        operations=OperationalReality(cli_tools=("git",)),
        outcome=AbsoluteOutcome(gate_exit_codes=(0,)),
    )


def _sized_epoch(epoch_id: str = "cccccccccccccccccccccccccccccccc") -> ExecutionEpoch:
    return ExecutionEpoch(
        epoch_id=epoch_id,
        task_id="079.003-T",
        route=RouteConfiguration(models=("gpt-5.4",), route_kinds=("structural_graph",)),
        economics=EconomicPayload(
            input_tokens=10,
            output_tokens=5,
            cached_input_tokens=2,
            cumulative_input_tokens=100,
            cumulative_output_tokens=50,
            context_area_tokens=200,
            avoided_read_estimated_tokens=80,
            tool_output_estimated_tokens=12,
        ),
        operations=OperationalReality(
            cli_tools=("git",),
            tool_surfaces=("mcp",),
            retrieval_packs=("agent-engram",),
            route_kind_counts={"structural_graph": 1},
            routed_lookup_count=1,
            expected_tool_count=1,
            observed_expected_tool_count=0,
            missing_expected_tool_count=1,
            expected_tool_counts={"engram.map_code": 1},
            observed_tool_counts={"engram.map_code": 0},
            missing_expected_tool_counts={"engram.map_code": 1},
        ),
        outcome=AbsoluteOutcome(gate_exit_codes=(0,), tool_gap_count=1),
        sizing=WorkSizingSnapshot(
            snapshot_at="2026-07-24T03:07:22Z",
            task_size_label="M",
            feature_planned_child_task_count=1,
            feature_planned_child_size_histogram={"M": 1},
            feature_child_membership_hash=WorkSizingSnapshot.membership_hash(["079.003-T"]),
        ),
    )


class JsonlSinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.jsonl_path = Path(self._tmp.name) / ".autoharness" / "metrics" / "execution_epochs.jsonl"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_each_line_is_well_formed_json_with_contract_fields(self) -> None:
        epoch = _epoch("051.006-T")
        append_epoch(epoch, self.jsonl_path)

        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        for key in ("epoch_id", "schema_version", "task_id", "timestamp", "route", "economics", "operations", "outcome"):
            self.assertIn(key, parsed)
        self.assertEqual(parsed["task_id"], "051.006-T")

    def test_append_semantics_preserve_existing_lines(self) -> None:
        append_epoch(_epoch("a"), self.jsonl_path)
        append_epoch(_epoch("b"), self.jsonl_path)

        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["task_id"], "a")
        self.assertEqual(json.loads(lines[1])["task_id"], "b")

    def test_parent_directory_is_created(self) -> None:
        self.assertFalse(self.jsonl_path.parent.exists())
        append_epoch(_epoch("x"), self.jsonl_path)
        self.assertTrue(self.jsonl_path.exists())

    def test_concurrent_appends_produce_intact_lines(self) -> None:
        # Each append must land as exactly one atomic, complete line even under
        # many concurrent writers — no interleaving or split lines.
        import threading

        n_threads = 12
        m_records = 120

        def worker(tid: int) -> None:
            for i in range(m_records):
                append_epoch(_epoch(f"t{tid}-{i}"), self.jsonl_path)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), n_threads * m_records)
        for line in lines:
            json.loads(line)  # every line must be valid, complete JSON

    def test_v11_record_is_written_exactly_with_sizing_and_no_event_body(self) -> None:
        epoch = _sized_epoch()
        append_epoch(epoch, self.jsonl_path)

        payload = json.loads(self.jsonl_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(payload, epoch.to_record())
        self.assertEqual(payload["sizing"]["task_size_label"], "M")
        self.assertEqual(payload["operations"]["expected_tool_counts"], {"engram.map_code": 1})
        self.assertNotIn("raw_tool_output", payload)
        self.assertNotIn("tool_events", payload)

    def test_identical_replay_is_not_appended_and_conflict_is_diagnosed(self) -> None:
        first = _sized_epoch("dddddddddddddddddddddddddddddddd")
        append_epoch(first, self.jsonl_path)
        idempotent = append_epoch(first, self.jsonl_path)
        conflict = ExecutionEpoch(
            epoch_id=first.epoch_id,
            task_id="079.003-T",
            route=first.route,
            economics=EconomicPayload(input_tokens=999),
            operations=first.operations,
            outcome=first.outcome,
        )

        with self.assertRaises(TelemetryConflictError):
            append_epoch(conflict, self.jsonl_path)

        lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(idempotent.status, "idempotent_replay")
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["economics"]["input_tokens"], 10)

    def test_preflight_tail_scan_detects_concurrent_identical_replay(self) -> None:
        epoch = _sized_epoch("abababababababababababababababab")
        append_epoch(_epoch("history"), self.jsonl_path)
        preflight = jsonl_sink.scan_epoch_digest(self.jsonl_path, epoch.epoch_id)
        append_epoch(epoch, self.jsonl_path)

        with mock.patch.object(
            jsonl_sink,
            "scan_epoch_digest",
            wraps=jsonl_sink.scan_epoch_digest,
        ) as scan:
            result = append_epoch(epoch, self.jsonl_path, preflight=preflight)

        self.assertEqual(result.status, "idempotent_replay")
        self.assertEqual(len(self.jsonl_path.read_text(encoding="utf-8").splitlines()), 2)
        self.assertEqual(scan.call_count, 1)
        self.assertEqual(scan.call_args.kwargs["start_offset"], preflight.scanned_offset)

    def test_preflight_tail_scan_detects_concurrent_conflicting_replay(self) -> None:
        first = _sized_epoch("babababababababababababababababa")
        conflict = ExecutionEpoch(
            epoch_id=first.epoch_id,
            task_id="079.003-T",
            route=first.route,
            economics=EconomicPayload(input_tokens=999),
            operations=first.operations,
            outcome=first.outcome,
        )
        append_epoch(_epoch("history"), self.jsonl_path)
        preflight = jsonl_sink.scan_epoch_digest(self.jsonl_path, first.epoch_id)
        append_epoch(first, self.jsonl_path)

        with mock.patch.object(
            jsonl_sink,
            "scan_epoch_digest",
            wraps=jsonl_sink.scan_epoch_digest,
        ) as scan:
            with self.assertRaises(TelemetryConflictError):
                append_epoch(conflict, self.jsonl_path, preflight=preflight)

        self.assertEqual(len(self.jsonl_path.read_text(encoding="utf-8").splitlines()), 2)
        self.assertEqual(scan.call_count, 1)
        self.assertEqual(scan.call_args.kwargs["start_offset"], preflight.scanned_offset)

    def test_corrupt_historical_line_does_not_disable_emission(self) -> None:
        """Regression (Copilot review r3 B5): every append preflights the whole
        file via find_epoch_digest. A single corrupt historical line must not
        raise JSONDecodeError and permanently disable future JSONL emission — the
        scan skips malformed lines and keeps going, and appends still succeed."""
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        valid_line = json.dumps({"epoch_id": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "x": 1})
        self.jsonl_path.write_text(
            "{ this is not valid json\n" + valid_line + "\n", encoding="utf-8"
        )

        # The scan must find the well-formed record past the corrupt line.
        self.assertIsNotNone(
            find_epoch_digest(self.jsonl_path, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        )

        # A new append must still succeed despite the corrupt historical line.
        result = append_epoch(_epoch("051.099-T"), self.jsonl_path)
        self.assertEqual(result.status, "created")


def _encode_line(epoch: ExecutionEpoch) -> str:
    return json.dumps(epoch.to_record(), separators=(",", ":")) + "\n"


def _conflicting_epoch(epoch_id: str, input_tokens: int = 999) -> ExecutionEpoch:
    base = _sized_epoch(epoch_id)
    return ExecutionEpoch(
        epoch_id=base.epoch_id,
        task_id="079.003-T",
        route=base.route,
        economics=EconomicPayload(input_tokens=input_tokens),
        operations=base.operations,
        outcome=base.outcome,
    )


class CrossSegmentReplayTests(unittest.TestCase):
    """095.001-T — replay/preflight scan spans active + sealed segments."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.jsonl_path = Path(self._tmp.name) / ".autoharness" / "metrics" / "execution_epochs.jsonl"
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_sealed(self, generation: int, *epochs: ExecutionEpoch) -> Path:
        sealed = jsonl_sink.sealed_segment_path(self.jsonl_path, generation)
        sealed.write_text("".join(_encode_line(e) for e in epochs), encoding="utf-8")
        return sealed

    def test_idempotent_replay_when_epoch_lives_in_sealed_segment(self) -> None:
        epoch = _sized_epoch("11111111111111111111111111111111")
        self._write_sealed(1, epoch)

        result = append_epoch(epoch, self.jsonl_path)

        self.assertEqual(result.status, "idempotent_replay")
        # No line is written to the (still absent) active segment on replay.
        self.assertFalse(self.jsonl_path.exists())

    def test_conflict_detected_across_sealed_segment(self) -> None:
        original = _sized_epoch("22222222222222222222222222222222")
        self._write_sealed(1, original)

        with self.assertRaises(TelemetryConflictError):
            append_epoch(_conflicting_epoch(original.epoch_id), self.jsonl_path)

    def test_active_replacement_between_preflight_and_append_invalidates_offset(self) -> None:
        # A rollover between preflight and append replaces the active segment with
        # a LARGER file whose early bytes hold the epoch. A naive resume from the
        # stale offset would skip the replay; the generation identity forces a full
        # cross-segment rescan that still detects it.
        epoch = _sized_epoch("33333333333333333333333333333333")
        append_epoch(_epoch("history-a"), self.jsonl_path)
        append_epoch(_epoch("history-b"), self.jsonl_path)
        preflight = jsonl_sink.scan_epoch_digest(self.jsonl_path, epoch.epoch_id)
        self.assertIsNone(preflight.existing_digest)
        self.assertEqual(preflight.active_generation, 1)

        # Simulate rollover: seal the old active to generation 1, then create a
        # fresh, larger active whose first line is the replayed epoch.
        self.jsonl_path.replace(jsonl_sink.sealed_segment_path(self.jsonl_path, 1))
        fresh = _encode_line(epoch) + "".join(_encode_line(_epoch(f"filler-{i}")) for i in range(5))
        self.jsonl_path.write_text(fresh, encoding="utf-8")
        self.assertGreater(self.jsonl_path.stat().st_size, preflight.scanned_offset)

        result = append_epoch(epoch, self.jsonl_path, preflight=preflight)
        self.assertEqual(result.status, "idempotent_replay")

    def test_single_segment_offset_optimization_preserved_with_generation_identity(self) -> None:
        epoch = _sized_epoch("44444444444444444444444444444444")
        append_epoch(_epoch("history"), self.jsonl_path)
        preflight = jsonl_sink.scan_epoch_digest(self.jsonl_path, epoch.epoch_id)
        self.assertEqual(preflight.active_generation, 1)
        self.assertGreater(preflight.active_size, 0)
        append_epoch(epoch, self.jsonl_path)

        with mock.patch.object(
            jsonl_sink, "scan_epoch_digest", wraps=jsonl_sink.scan_epoch_digest
        ) as scan:
            result = append_epoch(epoch, self.jsonl_path, preflight=preflight)

        self.assertEqual(result.status, "idempotent_replay")
        self.assertEqual(scan.call_count, 1)
        self.assertEqual(scan.call_args.kwargs["start_offset"], preflight.scanned_offset)


class SegmentRolloverTests(unittest.TestCase):
    """095.002-T — size-based rollover with a no-replace generation claim."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.jsonl_path = Path(self._tmp.name) / ".autoharness" / "metrics" / "execution_epochs.jsonl"
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_rollover_seals_active_and_starts_fresh_at_low_threshold(self) -> None:
        first = _sized_epoch("a" * 32)
        second = _sized_epoch("b" * 32)
        with mock.patch.object(jsonl_sink, "_MAX_SEGMENT_BYTES", 200):
            # Active is empty (< threshold) so the first record is written; the
            # second append observes size >= threshold, seals gen 1, and writes to
            # a fresh active.
            self.assertEqual(append_epoch(first, self.jsonl_path).status, "created")
            self.assertEqual(append_epoch(second, self.jsonl_path).status, "created")

        sealed = jsonl_sink.sealed_segment_path(self.jsonl_path, 1)
        self.assertTrue(sealed.exists())
        self.assertEqual([g for g, _ in jsonl_sink.sealed_segments(self.jsonl_path)], [1])
        sealed_lines = sealed.read_text(encoding="utf-8").splitlines()
        active_lines = self.jsonl_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual([json.loads(sealed_lines[0])["epoch_id"]], [first.epoch_id])
        self.assertEqual([json.loads(active_lines[0])["epoch_id"]], [second.epoch_id])
        # Cross-segment replay still holds after rollover: the sealed record is
        # detected as an idempotent replay, not re-appended.
        self.assertEqual(append_epoch(first, self.jsonl_path).status, "idempotent_replay")
        self.assertEqual(len(self.jsonl_path.read_text(encoding="utf-8").splitlines()), 1)

    def test_seal_collision_retries_next_generation_without_clobber(self) -> None:
        active_bytes = _encode_line(_sized_epoch("b" * 32)).encode("utf-8")
        self.jsonl_path.write_bytes(active_bytes)
        # Generation 1 is already sealed with distinct content that MUST survive.
        gen1 = jsonl_sink.sealed_segment_path(self.jsonl_path, 1)
        gen1.write_text("SEALED-GEN-1\n", encoding="utf-8")
        gen1_bytes = gen1.read_bytes()

        # Force the sealer to first pick generation 1 (already taken, as a
        # concurrent writer would), then re-read the true max on retry. The
        # no-replace claim must refuse to clobber gen 1 and land on gen 2.
        with mock.patch.object(jsonl_sink, "_max_sealed_generation", side_effect=[0, 1]):
            generation = jsonl_sink._seal_active_segment(self.jsonl_path)

        self.assertEqual(generation, 2)
        self.assertEqual(gen1.read_bytes(), gen1_bytes)  # zero whole-segment loss
        self.assertEqual(
            jsonl_sink.sealed_segment_path(self.jsonl_path, 2).read_bytes(), active_bytes
        )
        self.assertFalse(self.jsonl_path.exists())  # active consumed by the seal

    def test_default_threshold_keeps_small_writes_single_segment(self) -> None:
        for i in range(6):
            append_epoch(_sized_epoch(f"{i:032d}"), self.jsonl_path)
        self.assertEqual(jsonl_sink.sealed_segments(self.jsonl_path), [])
        self.assertEqual(len(self.jsonl_path.read_text(encoding="utf-8").splitlines()), 6)

    def test_oversized_single_record_written_intact_to_own_segment(self) -> None:
        oversized = _sized_epoch("c" * 32)
        oversized_line = _encode_line(oversized)
        with mock.patch.object(jsonl_sink, "_MAX_SEGMENT_BYTES", 200):
            # The oversized record (> threshold) is written intact to the active
            # segment; the next append seals it — intact — into its own segment.
            append_epoch(oversized, self.jsonl_path)
            append_epoch(_sized_epoch("d" * 32), self.jsonl_path)

        sealed = jsonl_sink.sealed_segment_path(self.jsonl_path, 1)
        sealed_text = sealed.read_text(encoding="utf-8")
        self.assertEqual(sealed_text, oversized_line)  # single intact line, not split
        self.assertGreater(len(oversized_line.encode("utf-8")), 200)


if __name__ == "__main__":
    unittest.main()
