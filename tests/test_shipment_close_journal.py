"""Durable journal tests (211.001-T, plan unit T2; hardening H5)."""

from __future__ import annotations

import copy
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.shipment_close import journal as journal_module
from autoharness.shipment_close.journal import (
    MAX_JSON_BYTES,
    TRUNCATION_MARKER,
    JournalError,
    cleanup_raw_files,
    create_journal,
    discard_journal,
    enforce_stream_cap,
    journal_path,
    open_stream_file,
    read_json,
    read_stream,
    write_json,
)
from cascade_close_test_support import make_dir_link

_RUN = "a" * 32
_OTHER_RUN = "b" * 32


def _meta(run_id: str = _RUN) -> dict:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "shipment_id": "218-S",
        "feature_id": "211-F",
        "argv_redacted": ["backlogit", "shipment", "ship", "218-S"],
        "argv_sha256": "0" * 64,
        "timeout_seconds": 600,
        "caller_wait_seconds": None,
        "host": "host-a",
        "wrapper_pid": 4242,
        "created_at": "2026-10-17T00:00:00Z",
        "finalizer": None,
    }


def _exit(run_id: str = _RUN) -> dict:
    stream = {"proven": True, "method": "job_object", "survivors_killed": 0, "total_bytes": 12}
    return {
        "schema_version": 1,
        "run_id": run_id,
        "state": "exited",
        "child_pid": 99,
        "started_at": "2026-10-17T00:00:01Z",
        "finished_at": "2026-10-17T00:00:05Z",
        "exit_code": 0,
        "timed_out": False,
        "quiescence": {"stdout": dict(stream), "stderr": dict(stream)},
    }


def _never_started(run_id: str = _RUN) -> dict:
    record = _exit(run_id)
    record.update(state="never_started", child_pid=None, exit_code=None, finished_at=None, quiescence=None)
    return record


def _outcome(run_id: str = _RUN) -> dict:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "exit_code": 0,
        "outcome": "completed",
        "finalizer": "foreground",
        "written_at": "2026-10-17T00:00:06Z",
    }


class _Workspace(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace = Path(self._tmp.name).resolve()
        self.journal = create_journal(self.workspace, "218-S", "211-F", _RUN)


class DirectoryTest(_Workspace):
    def test_directory_is_created_under_the_gitignored_gates_tree(self) -> None:
        expected = self.workspace / ".autoharness" / "gates" / "cascade-close" / "218-S-211-F.journal"
        self.assertEqual(self.journal.path, expected)
        self.assertTrue(expected.is_dir())
        self.assertEqual(journal_path(self.workspace, "218-S", "211-F"), expected)

    def test_reopening_is_idempotent(self) -> None:
        again = create_journal(self.workspace, "218-S", "211-F", _OTHER_RUN)
        self.assertEqual(again.path, self.journal.path)

    def test_invalid_run_id_and_pair_ids_are_refused(self) -> None:
        with self.assertRaises(JournalError):
            create_journal(self.workspace, "218-S", "211-F", "XYZ")
        with self.assertRaises(JournalError):
            journal_path(self.workspace, "../x", "211-F")

    def test_linked_component_is_refused(self) -> None:
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        for relative in (".autoharness", ".autoharness/gates/cascade-close/218-S-211-F.journal"):
            with self.subTest(relative):
                workspace = Path(tempfile.mkdtemp(dir=self._tmp.name))
                target = Path(other.name) / "t"
                target.mkdir(exist_ok=True)
                link = workspace / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                reason = make_dir_link(link, target)
                if reason:
                    self.skipTest(reason)
                with self.assertRaises(Exception) as caught:
                    create_journal(workspace, "218-S", "211-F", _RUN)
                self.assertIn("untrusted", str(caught.exception) + getattr(caught.exception, "reason", ""))

    def test_a_journal_swapped_for_a_link_after_creation_is_refused(self) -> None:
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        write_json(self.journal, "meta.json", _meta())
        (self.journal.path / "meta.json").unlink()
        self.journal.path.rmdir()
        reason = make_dir_link(self.journal.path, Path(other.name))
        if reason:
            self.skipTest(reason)
        with self.assertRaises(JournalError) as caught:
            read_json(self.journal, "meta.json")
        self.assertEqual(caught.exception.reason, "untrusted")
        with self.assertRaises(JournalError):
            write_json(self.journal, "meta.json", _meta())
        with self.assertRaises(JournalError):
            open_stream_file(self.journal, "stdout.raw")
        self.assertEqual(os.listdir(other.name), [])


class JsonFilesTest(_Workspace):
    def test_round_trip_for_each_schema(self) -> None:
        for name, record in (("meta.json", _meta()), ("exit.json", _exit()), ("outcome.json", _outcome())):
            with self.subTest(name):
                write_json(self.journal, name, record)
                self.assertEqual(read_json(self.journal, name), record)

    def test_never_started_sentinel_round_trips(self) -> None:
        write_json(self.journal, "exit.json", _never_started())
        self.assertEqual(read_json(self.journal, "exit.json")["state"], "never_started")

    def test_overwrite_is_atomic_and_leaves_no_temp_files(self) -> None:
        write_json(self.journal, "outcome.json", _outcome())
        changed = _outcome()
        changed["exit_code"] = 5
        changed["outcome"] = "postcondition_failed"
        write_json(self.journal, "outcome.json", changed)
        self.assertEqual(read_json(self.journal, "outcome.json")["exit_code"], 5)
        self.assertEqual(sorted(os.listdir(self.journal.path)), ["outcome.json"])

    def test_failed_replace_leaves_the_prior_file_and_no_temp(self) -> None:
        write_json(self.journal, "outcome.json", _outcome())
        before = (self.journal.path / "outcome.json").read_bytes()
        changed = _outcome()
        changed["exit_code"] = 6
        with mock.patch.object(journal_module, "_replace_with_retry", side_effect=PermissionError("locked")):
            with self.assertRaises(JournalError):
                write_json(self.journal, "outcome.json", changed)
        self.assertEqual((self.journal.path / "outcome.json").read_bytes(), before)
        self.assertEqual(sorted(os.listdir(self.journal.path)), ["outcome.json"])

    @unittest.skipIf(os.name == "nt", "POSIX mode bits")
    def test_files_are_owner_only(self) -> None:
        write_json(self.journal, "meta.json", _meta())
        fd = open_stream_file(self.journal, "stdout.raw")
        os.close(fd)
        for name in ("meta.json", "stdout.raw"):
            self.assertEqual(stat.S_IMODE((self.journal.path / name).stat().st_mode), 0o600)

    def test_missing_torn_and_oversized_reads_are_distinct_refusals(self) -> None:
        with self.assertRaises(JournalError) as caught:
            read_json(self.journal, "meta.json")
        self.assertEqual(caught.exception.reason, "missing")
        write_json(self.journal, "meta.json", _meta())
        path = self.journal.path / "meta.json"
        path.write_bytes(path.read_bytes()[:40])
        with self.assertRaises(JournalError) as caught:
            read_json(self.journal, "meta.json")
        self.assertEqual(caught.exception.reason, "torn")
        path.write_bytes(b"x" * (MAX_JSON_BYTES + 1))
        with self.assertRaises(JournalError) as caught:
            read_json(self.journal, "meta.json")
        self.assertEqual(caught.exception.reason, "oversize")
        path.write_bytes(b"\xff\xfe")
        with self.assertRaises(JournalError) as caught:
            read_json(self.journal, "meta.json")
        self.assertEqual(caught.exception.reason, "torn")

    def test_non_object_foreign_run_and_version_are_refused_on_read(self) -> None:
        path = self.journal.path / "outcome.json"
        cases = {
            "array": b"[]",
            "foreign run": json.dumps(_outcome(_OTHER_RUN)).encode(),
            "bad version": json.dumps({**_outcome(), "schema_version": 2}).encode(),
            "bad run id": json.dumps({**_outcome(), "run_id": "short"}).encode(),
        }
        for name, payload in cases.items():
            with self.subTest(name):
                path.write_bytes(payload)
                with self.assertRaises(JournalError):
                    read_json(self.journal, "outcome.json")

    def test_a_legitimate_other_run_can_be_read_when_named(self) -> None:
        (self.journal.path / "outcome.json").write_bytes(json.dumps(_outcome(_OTHER_RUN)).encode())
        self.assertEqual(
            read_json(self.journal, "outcome.json", expected_run_id=_OTHER_RUN)["run_id"], _OTHER_RUN
        )

    def test_schema_violations_are_refused_on_read_and_write(self) -> None:
        def mutate(base: dict, **changes: object) -> dict:
            record = copy.deepcopy(base)
            record.update(changes)
            return record

        def drop(base: dict, key: str) -> dict:
            record = copy.deepcopy(base)
            del record[key]
            return record

        bad_quiescence = _exit()
        bad_quiescence["quiescence"]["stdout"]["proven"] = "yes"
        cases = [
            ("meta.json", mutate(_meta(), argv_redacted=[])),
            ("meta.json", mutate(_meta(), argv_redacted=["a", 1])),
            ("meta.json", mutate(_meta(), argv_sha256="abc")),
            ("meta.json", mutate(_meta(), timeout_seconds=0)),
            ("meta.json", mutate(_meta(), timeout_seconds=True)),
            ("meta.json", mutate(_meta(), caller_wait_seconds=-1)),
            ("meta.json", mutate(_meta(), wrapper_pid=0)),
            ("meta.json", mutate(_meta(), extra="x")),
            ("meta.json", drop(_meta(), "host")),
            ("exit.json", mutate(_exit(), state="done")),
            ("exit.json", mutate(_exit(), timed_out="no")),
            ("exit.json", mutate(_exit(), exit_code=None)),
            ("exit.json", mutate(_exit(), quiescence=None)),
            ("exit.json", mutate(_exit(), quiescence={"stdout": _exit()["quiescence"]["stdout"]})),
            ("exit.json", bad_quiescence),
            ("exit.json", mutate(_never_started(), child_pid=7)),
            ("exit.json", mutate(_never_started(), quiescence=_exit()["quiescence"])),
            ("outcome.json", mutate(_outcome(), exit_code=300)),
            ("outcome.json", mutate(_outcome(), outcome="whatever")),
            ("outcome.json", mutate(_outcome(), finalizer="")),
            ("outcome.json", drop(_outcome(), "written_at")),
        ]
        for name, record in cases:
            with self.subTest(name=name, record=record):
                with self.assertRaises(JournalError):
                    write_json(self.journal, name, record)
                (self.journal.path / name).write_bytes(json.dumps(record).encode())
                with self.assertRaises(JournalError):
                    read_json(self.journal, name)
                (self.journal.path / name).unlink()

    def test_hostile_json_values_are_refusals_never_a_traceback(self) -> None:
        launch = journal_module.build_launch(
            run_id=_RUN,
            workspace=str(self.workspace),
            shipment_id="218-S",
            feature_id="211-F",
            merge_commit_sha="a" * 40,
            mode="attached",
            argv=["bin", "ship"],
            binary_path="bin",
            binary_sha256="0" * 64,
            argv_prefix=["bin"],
            cwd=str(self.workspace),
            timeout_seconds=30,
        )
        started = {"schema_version": 1, "run_id": _RUN, "written_at": "2026-10-17T00:00:00Z", "pid": None}
        cases = [
            ("exit.json", {**_exit(), "state": ["exited"]}),
            ("exit.json", {**_exit(), "state": {"a": 1}}),
            ("outcome.json", {**_outcome(), "outcome": ["completed"]}),
            ("launch.json", {**launch, "mode": ["attached"]}),
            ("launch.json", {**launch, "quiescence_grace_seconds": float("inf")}),
            ("launch.json", {**launch, "quiescence_grace_seconds": float("nan")}),
            ("child_started.json", {**started, "state": ["spawned"]}),
            ("child_started.json", {**started, "state": {"x": 1}}),
            ("outcome.json", {**_outcome(), "schema_version": True}),
            ("outcome.json", {**_outcome(), "schema_version": 1.0}),
        ]
        for name, record in cases:
            with self.subTest(name=name, record=record):
                with self.assertRaises(JournalError):
                    write_json(self.journal, name, record)
                (self.journal.path / name).write_bytes(json.dumps(record).encode())
                with self.assertRaises(JournalError):
                    read_json(self.journal, name)
                (self.journal.path / name).unlink()

    def test_deeply_nested_json_is_a_refusal_not_a_recursion_error(self) -> None:
        (self.journal.path / "meta.json").write_bytes(b"[" * 20000 + b"]" * 20000)
        with self.assertRaises(JournalError) as caught:
            read_json(self.journal, "meta.json")
        self.assertIn(caught.exception.reason, ("torn", "invalid"))
        with (
            mock.patch.object(journal_module.json, "loads", side_effect=RecursionError),
            self.assertRaises(JournalError) as caught,
        ):
            read_json(self.journal, "meta.json")
        self.assertEqual(caught.exception.reason, "torn")

    def test_unknown_names_and_foreign_run_writes_are_refused(self) -> None:
        with self.assertRaises(JournalError):
            write_json(self.journal, "evil.json", _meta())
        with self.assertRaises(JournalError):
            read_json(self.journal, "../meta.json")
        with self.assertRaises(JournalError):
            write_json(self.journal, "meta.json", _meta(_OTHER_RUN))

    def test_a_file_replaced_by_a_directory_is_refused(self) -> None:
        (self.journal.path / "meta.json").mkdir()
        with self.assertRaises(JournalError):
            read_json(self.journal, "meta.json")


class StreamTest(_Workspace):
    def test_streams_are_created_exclusively_and_appendable(self) -> None:
        fd = open_stream_file(self.journal, "stdout.raw")
        os.write(fd, b"one\n")
        os.close(fd)
        with self.assertRaises(JournalError) as caught:
            open_stream_file(self.journal, "stdout.raw")
        self.assertEqual(caught.exception.reason, "exists")
        self.assertEqual(read_stream(self.journal, "stdout.raw"), (b"one\n", False))

    def test_unknown_stream_names_are_refused(self) -> None:
        for call in (open_stream_file, read_stream, enforce_stream_cap):
            with self.subTest(call.__name__), self.assertRaises(JournalError):
                call(self.journal, "meta.json")

    def test_read_is_capped_and_flags_truncation(self) -> None:
        fd = open_stream_file(self.journal, "stderr.raw")
        os.write(fd, b"x" * 100)
        os.close(fd)
        self.assertEqual(read_stream(self.journal, "stderr.raw", cap=100), (b"x" * 100, False))
        self.assertEqual(read_stream(self.journal, "stderr.raw", cap=10), (b"x" * 10, True))

    def test_oversize_stream_is_truncated_with_an_explicit_marker(self) -> None:
        fd = open_stream_file(self.journal, "stdout.raw")
        os.write(fd, b"y" * 50)
        os.close(fd)
        self.assertFalse(enforce_stream_cap(self.journal, "stdout.raw", cap=50))
        self.assertTrue(enforce_stream_cap(self.journal, "stdout.raw", cap=20))
        data, truncated = read_stream(self.journal, "stdout.raw", cap=1000)
        self.assertFalse(truncated)
        self.assertEqual(data, b"y" * 20 + TRUNCATION_MARKER)

    def test_cap_on_a_missing_stream_is_refused(self) -> None:
        with self.assertRaises(JournalError) as caught:
            enforce_stream_cap(self.journal, "stdout.raw")
        self.assertEqual(caught.exception.reason, "missing")


class CleanupTest(_Workspace):
    def _populate(self) -> None:
        for name in ("stdout.raw", "stderr.raw"):
            os.close(open_stream_file(self.journal, name))
        (self.journal.path / "launch.json").write_text("{}", encoding="utf-8")
        for name, record in (("meta.json", _meta()), ("exit.json", _exit()), ("outcome.json", _outcome())):
            write_json(self.journal, name, record)

    def test_cleanup_removes_only_the_raw_files(self) -> None:
        self._populate()
        cleanup_raw_files(self.journal)
        self.assertEqual(sorted(os.listdir(self.journal.path)), ["exit.json", "meta.json", "outcome.json"])
        self.assertEqual(read_json(self.journal, "outcome.json")["exit_code"], 0)
        cleanup_raw_files(self.journal)

    def test_discard_removes_owned_files_and_an_empty_directory_only(self) -> None:
        self._populate()
        discard_journal(self.journal)
        self.assertFalse(self.journal.path.exists())

    def test_discard_keeps_a_directory_that_holds_foreign_files(self) -> None:
        self._populate()
        (self.journal.path / "keep.txt").write_text("x", encoding="utf-8")
        discard_journal(self.journal)
        self.assertEqual(os.listdir(self.journal.path), ["keep.txt"])


if __name__ == "__main__":
    unittest.main()
