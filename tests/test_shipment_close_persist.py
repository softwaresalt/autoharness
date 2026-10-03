"""Evidence persistence tests for the ``cascade-close`` command (192.002-T, plan unit A1b).

Four table-driven scenarios (plan ``### A1b``):

1. streaming capture and redaction (tail window, parse cap, redaction before
   the excerpt slice, quoted JSON keys, free-text fields);
2. the per-pair lock and directory trust (SL-F01, SL-F06);
3. the existing-record check (PR #460 review; re-plan cycle-1 R1);
4. owner transitions, the pre_close takeover compare-and-swap (Copilot PR #481
   T6), and the atomic write.

Every fixture workspace is a fresh temporary directory created by the test,
following the existing ``tests/`` convention; the command code never writes
outside the workspace it is given.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from autoharness.gates.cascade_evidence import CascadeEvidenceError, build_evidence_path
from autoharness.shipment_close import EXIT_INPUT, EXIT_LOCKED
from autoharness.shipment_close import persist
from autoharness.shipment_close.persist import (
    LEADING_MARGIN_BYTES,
    MODE_CLASSIFY_ONLY,
    MODE_MUTATING,
    MODE_REPLACE_PRE_CLOSE,
    PARSE_CAP_BYTES,
    PARSE_CAP_LINES,
    STDOUT_OVERFLOW_ERROR,
    TAIL_BYTES,
    TAIL_LINES,
    PersistError,
    StreamCapture,
    acquire_pair_lock,
    check_existing_record,
    redact_record_free_text,
    write_evidence_atomic,
)

from test_cascade_evidence_contract import cascade_record, safe_close_record

_SHIPMENT = "198-S"
_FEATURE = "192-F"
_RUN_A = "a" * 32
_RUN_B = "b" * 32
_RUN_C = "c" * 32


def _make_dir_link(link: Path, target: Path) -> str | None:
    """Create a directory symlink (or Windows junction). Return a skip reason on failure."""

    try:
        os.symlink(target, link, target_is_directory=True)
        return None
    except (OSError, NotImplementedError) as exc:
        symlink_error = exc
    if os.name == "nt":
        try:
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
            return None
        except (OSError, ImportError, AttributeError) as exc:  # pragma: no cover - platform
            return f"cannot create symlink ({symlink_error}) or junction ({exc})"
    return f"cannot create directory symlink: {symlink_error}"


def _capture(data: bytes, *, parse: bool = False, chunk: int = 65536):
    capture = StreamCapture(parse_buffer=parse)
    for start in range(0, len(data), chunk):
        capture.feed(data[start : start + chunk])
    return capture, capture.finish()


def _record(builder, *, phase: str, run_id: str) -> dict:
    record = builder()
    record["phase"] = phase
    record["run_id"] = run_id
    return record


def _cascade_pre_close(run_id: str) -> dict:
    record = cascade_record()
    for key in ("invocation", "post_close"):
        record.pop(key)
    record["phase"] = "pre_close"
    record["run_id"] = run_id
    return record


class _Workspace:
    """A fresh fixture workspace (and a sibling ``outside`` directory) per test."""

    def __init__(self, test: unittest.TestCase) -> None:
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        base = Path(tmp.name).resolve()
        self.root = base / "ws"
        self.outside = base / "outside"
        self.root.mkdir()
        self.outside.mkdir()
        self.evidence = build_evidence_path(self.root, _SHIPMENT, _FEATURE)

    def place(self, record: dict) -> bytes:
        self.evidence.parent.mkdir(parents=True, exist_ok=True)
        data = persist.serialize_evidence_record(record).encode("utf-8")
        self.evidence.write_bytes(data)
        return data


class CaptureAndRedactionTests(unittest.TestCase):
    """Scenario 1: bounded streaming capture and redaction before the slice."""

    def test_capture_and_redaction_table(self) -> None:
        def lines(count: int) -> bytes:
            return b"".join(b"line %d\n" % index for index in range(count))

        # (label, data, parse, expected excerpt length check, truncated)
        rows = [
            ("exactly 64 KiB", b"a" * TAIL_BYTES, False, TAIL_BYTES, False),
            ("64 KiB plus one", b"a" * (TAIL_BYTES + 1), False, TAIL_BYTES, True),
        ]
        for label, data, parse, excerpt_bytes, truncated in rows:
            with self.subTest(label):
                _, result = _capture(data, parse=parse)
                self.assertEqual(len(result.excerpt.encode("utf-8")), excerpt_bytes)
                self.assertIs(result.capture_truncated, truncated)
                self.assertEqual(result.total_bytes, len(data))
                self.assertEqual(result.sha256, hashlib.sha256(data).hexdigest())

        for count, truncated in ((TAIL_LINES, False), (TAIL_LINES + 1, True)):
            with self.subTest(lines=count):
                _, result = _capture(lines(count))
                self.assertEqual(len(result.excerpt.splitlines()), TAIL_LINES)
                self.assertEqual(result.total_lines, count)
                self.assertIs(result.capture_truncated, truncated)
                self.assertTrue(result.excerpt.endswith(f"line {count - 1}\n"))

        with self.subTest("2 MiB stream with bounded retained memory"):
            data = (b"0123456789abcdef" * 4096) * 32  # 2 MiB
            capture = StreamCapture(parse_buffer=True)
            peak = 0
            for start in range(0, len(data), 65536):
                capture.feed(data[start : start + 65536])
                peak = max(peak, capture.retained_bytes)
            result = capture.finish()
            self.assertLessEqual(peak, PARSE_CAP_BYTES + TAIL_BYTES + LEADING_MARGIN_BYTES + 65536)
            self.assertLessEqual(capture.retained_bytes, TAIL_BYTES + LEADING_MARGIN_BYTES)
            self.assertEqual(result.total_bytes, 2 * 1024 * 1024)
            self.assertEqual(result.sha256, hashlib.sha256(data).hexdigest())
            self.assertTrue(result.capture_truncated)

        for label, data in (
            ("stdout over the byte cap", b"x" * (PARSE_CAP_BYTES + 1)),
            ("stdout over the line cap", b"\n" * (PARSE_CAP_LINES + 1)),
        ):
            with self.subTest(label):
                _, result = _capture(data, parse=True)
                self.assertIsNone(result.parse_bytes)
                self.assertEqual(result.parse_error, STDOUT_OVERFLOW_ERROR)
                self.assertEqual(STDOUT_OVERFLOW_ERROR, "stdout exceeded capture cap")
                self.assertTrue(result.capture_truncated)

        with self.subTest("stdout within the cap is kept for parsing"):
            _, result = _capture(b'{"ok": true}\n', parse=True)
            self.assertEqual(result.parse_bytes, b'{"ok": true}\n')
            self.assertIsNone(result.parse_error)
        with self.subTest("stderr never keeps a parse buffer"):
            _, result = _capture(b'{"ok": true}\n', parse=False)
            self.assertIsNone(result.parse_bytes)
            self.assertIsNone(result.parse_error)

        with self.subTest("redaction"):
            _, result = _capture(b"backlogit: token=supersecret ok\n")
            self.assertNotIn("supersecret", result.excerpt)
            self.assertIn("token=[REDACTED]", result.excerpt)
            self.assertTrue(result.redaction_applied)
            self.assertEqual(result.to_record()["redaction_applied"], True)
            self.assertEqual(
                set(result.to_record()),
                {"total_bytes", "total_lines", "sha256", "capture_truncated", "excerpt", "redaction_applied"},
            )

        with self.subTest("secret split across the excerpt boundary"):
            secret = b"token=QZXSECRETQZX\n"
            suffix = b"B" * (TAIL_BYTES - 8)
            data = b"A" * 100 + b"\n" + secret + suffix
            self.assertIn(b"QZX", data[-TAIL_BYTES:])  # a slice-then-redact excerpt would leak
            _, result = _capture(data)
            self.assertNotIn("QZX", result.excerpt)
            self.assertTrue(result.redaction_applied)

        for text, kept in (
            ('{"token": "abc"}', '"token": "[REDACTED]"'),
            ('{"api_key":"abc"}', '"api_key":"[REDACTED]"'),
            ('{"Access_Token" : "abc"}', '"Access_Token" : "[REDACTED]"'),
        ):
            with self.subTest(quoted_json=text):
                _, result = _capture(text.encode("utf-8"))
                self.assertIn(kept, result.excerpt)
                self.assertNotIn('"abc"', result.excerpt)

        with self.subTest("free-text fields: failures[], parse_error, argv, version_excerpt"):
            record = cascade_record()
            record["tool"]["version_excerpt"] = "backlogit 1.11.0 token=abc"
            record["invocation"]["argv_redacted"] = ["backlogit", "--message", "password=hunter2"]
            record["post_close"]["failures"] = ["drift: secret=xyz"]
            record["post_close"]["parse_error"] = "bad body api_key=k1"
            engine_before = copy.deepcopy(record["pre_close"]["engine_semantics"])
            selection_before = copy.deepcopy(record["pre_close"]["close_path_selection"])
            redacted, applied = redact_record_free_text(record)
            self.assertTrue(applied)
            dumped = json.dumps(redacted)
            for leak in ("token=abc", "hunter2", "secret=xyz", "api_key=k1"):
                self.assertNotIn(leak, dumped)
            self.assertEqual(redacted["pre_close"]["engine_semantics"], engine_before)
            self.assertEqual(redacted["pre_close"]["close_path_selection"], selection_before)
            self.assertIn("hunter2", record["invocation"]["argv_redacted"][2])  # input untouched


class LockAndDirectoryTrustTests(unittest.TestCase):
    """Scenario 2: one winner per pair; untrusted directory components refused before any file."""

    def test_concurrent_acquirers(self) -> None:
        workspace = _Workspace(self)
        barrier = threading.Barrier(2)
        outcomes: list[object] = []

        def acquire(run_id: str) -> None:
            barrier.wait()
            try:
                outcomes.append(acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, run_id))
            except PersistError as exc:
                outcomes.append(exc)

        threads = [threading.Thread(target=acquire, args=(run_id,)) for run_id in (_RUN_A, _RUN_B)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(10)
        locks = [item for item in outcomes if isinstance(item, persist.PairLock)]
        errors = [item for item in outcomes if isinstance(item, PersistError)]
        self.assertEqual(len(locks), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].exit_code, EXIT_LOCKED)
        lock = locks[0]
        held = json.loads(lock.lock_path.read_text(encoding="utf-8"))
        self.assertEqual(held["run_id"], lock.run_id)
        self.assertEqual(held["pid"], os.getpid())
        self.assertIn("started_at", held)
        self.assertEqual(
            lock.lock_path,
            workspace.root / ".autoharness" / "gates" / "cascade-close" / f"{_SHIPMENT}-{_FEATURE}.lock",
        )
        # A held lock is never broken automatically.
        with self.assertRaises(PersistError) as caught:
            acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, _RUN_C)
        self.assertEqual(caught.exception.exit_code, EXIT_LOCKED)
        lock.release()
        self.assertFalse(lock.lock_path.exists())
        with acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, _RUN_C) as again:
            self.assertTrue(again.lock_path.exists())
        self.assertFalse(again.lock_path.exists())

    def test_untrusted_directory_components(self) -> None:
        for label, linked in (
            ("lock-directory component", Path(".autoharness")),
            ("lock-directory leaf parent", Path(".autoharness") / "gates"),
            ("evidence-directory component", Path("docs") / "closure"),
            ("evidence-directory leaf", Path("docs") / "closure" / "evidence"),
        ):
            with self.subTest(label):
                workspace = _Workspace(self)
                link = workspace.root / linked
                link.parent.mkdir(parents=True, exist_ok=True)
                skip = _make_dir_link(link, workspace.outside)
                if skip:
                    self.skipTest(skip)
                with self.assertRaises(PersistError) as caught:
                    acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, _RUN_A)
                self.assertEqual(caught.exception.exit_code, EXIT_INPUT)
                self.assertEqual(list(workspace.outside.iterdir()), [])
                self.assertEqual([p for p in workspace.root.rglob("*.lock")], [])

        with self.subTest("invalid run_id"):
            workspace = _Workspace(self)
            with self.assertRaises(PersistError):
                acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, "not-a-run-id")

    def test_lock_write_failure_is_persist_error_and_leaves_no_lock(self) -> None:
        # 198-S local review: os.write/os.fsync OSError must not escape raw or
        # leave a half-written O_EXCL lock behind.
        for target in ("write", "fsync"):
            with self.subTest(target):
                workspace = _Workspace(self)
                with mock.patch.object(persist.os, target, side_effect=OSError(28, "No space left on device")):
                    with self.assertRaises(PersistError) as caught:
                        acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, _RUN_A)
                self.assertEqual(caught.exception.exit_code, EXIT_INPUT)
                self.assertIn("cannot write lock", str(caught.exception))
                self.assertEqual([p for p in workspace.root.rglob("*.lock")], [])
                with acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, _RUN_B) as lock:
                    self.assertTrue(lock.lock_path.exists())

    def test_release_retries_unlink_and_never_raises(self) -> None:
        # 198-S local review: a Windows sharing violation on unlink must not
        # replace the real outcome from a ``finally`` release.
        with self.subTest("a transient PermissionError is retried"):
            workspace = _Workspace(self)
            lock = acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, _RUN_A)
            real_unlink = os.unlink
            calls = {"count": 0}

            def flaky_unlink(path, *args, **kwargs):
                calls["count"] += 1
                if calls["count"] == 1:
                    raise PermissionError(13, "sharing violation")
                return real_unlink(path, *args, **kwargs)

            with mock.patch.object(persist.os, "unlink", flaky_unlink), mock.patch.object(persist.time, "sleep"):
                lock.release()
            self.assertEqual(calls["count"], 2)
            self.assertFalse(lock.lock_path.exists())

        with self.subTest("a persistent failure warns on stderr and leaves the lock"):
            workspace = _Workspace(self)
            lock = acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, _RUN_A)
            stderr = io.StringIO()
            with (
                mock.patch.object(persist.os, "unlink", side_effect=PermissionError(13, "sharing violation")),
                mock.patch.object(persist.time, "sleep"),
                mock.patch.object(persist.sys, "stderr", stderr),
            ):
                lock.release()  # must not raise
            self.assertFalse(lock.held)
            self.assertTrue(lock.lock_path.exists())
            self.assertIn(str(lock.lock_path), stderr.getvalue())
            self.assertIn("operator", stderr.getvalue())


class ExistingRecordCheckTests(unittest.TestCase):
    """Scenario 3: the existing-record check under the lock."""

    def test_existing_record_table(self) -> None:
        safe_pre_close = _record(safe_close_record, phase="pre_close", run_id=_RUN_A)
        cascade_pre_close = _cascade_pre_close(_RUN_A)
        invoking = _cascade_pre_close(_RUN_A)
        invoking["phase"] = "invoking"
        post_close = _record(cascade_record, phase="post_close", run_id=_RUN_A)

        # (label, existing record or raw bytes, mode, expected exit or "returned" / None)
        rows = [
            ("no record", None, MODE_CLASSIFY_ONLY, None),
            ("no record, mutating", None, MODE_MUTATING, None),
            ("invoking record", invoking, MODE_MUTATING, EXIT_LOCKED),
            ("invoking record, classify-only", invoking, MODE_CLASSIFY_ONLY, EXIT_LOCKED),
            ("post_close record", post_close, MODE_MUTATING, EXIT_INPUT),
            ("post_close record, replace", post_close, MODE_REPLACE_PRE_CLOSE, EXIT_INPUT),
            ("plain classify-only over pre_close", safe_pre_close, MODE_CLASSIFY_ONLY, EXIT_INPUT),
            ("replace-pre-close over pre_close", safe_pre_close, MODE_REPLACE_PRE_CLOSE, "returned"),
            ("mutating over cascade-selected pre_close", cascade_pre_close, MODE_MUTATING, "returned"),
            ("mutating over safe_close-selected pre_close", safe_pre_close, MODE_MUTATING, "returned"),
            ("unparseable record", b"{not json", MODE_MUTATING, EXIT_LOCKED),
        ]
        for label, existing, mode, expected in rows:
            with self.subTest(label):
                workspace = _Workspace(self)
                before = None
                if isinstance(existing, bytes):
                    workspace.evidence.parent.mkdir(parents=True, exist_ok=True)
                    workspace.evidence.write_bytes(existing)
                    before = existing
                elif existing is not None:
                    before = workspace.place(existing)
                with acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, _RUN_B) as lock:
                    if expected in (None, "returned"):
                        returned = check_existing_record(lock, mode=mode)
                        if expected is None:
                            self.assertIsNone(returned)
                        else:
                            self.assertEqual(returned, json.loads(before.decode("utf-8")))
                    else:
                        with self.assertRaises(PersistError) as caught:
                            check_existing_record(lock, mode=mode)
                        self.assertEqual(caught.exception.exit_code, expected)
                if before is not None:
                    self.assertEqual(workspace.evidence.read_bytes(), before, f"{label} changed the record")

        with self.subTest("the check refuses to run without the lock"):
            workspace = _Workspace(self)
            lock = acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, _RUN_B)
            lock.release()
            with self.assertRaises(PersistError):
                check_existing_record(lock, mode=MODE_MUTATING)


class OwnerTransitionAndAtomicWriteTests(unittest.TestCase):
    """Scenario 4: owner transitions, the pre_close takeover, and the atomic write."""

    def _locked(self, run_id: str):
        workspace = _Workspace(self)
        lock = acquire_pair_lock(workspace.root, _SHIPMENT, _FEATURE, run_id)
        self.addCleanup(lock.release)
        return workspace, lock

    def test_owner_transitions(self) -> None:
        workspace, _ = self._locked(_RUN_A)
        pre_close = _cascade_pre_close(_RUN_A)
        write_evidence_atomic(workspace.evidence, pre_close, owner_run_id=_RUN_A)
        invoking = copy.deepcopy(pre_close)
        invoking["phase"] = "invoking"
        write_evidence_atomic(workspace.evidence, invoking, owner_run_id=_RUN_A)
        post_close = _record(cascade_record, phase="post_close", run_id=_RUN_A)
        write_evidence_atomic(workspace.evidence, post_close, owner_run_id=_RUN_A)
        written = workspace.evidence.read_text(encoding="utf-8")
        self.assertEqual(written, persist.serialize_evidence_record(post_close))
        self.assertTrue(written.endswith("}\n"))

        final = workspace.evidence.read_bytes()
        # Nothing moves out of post_close, not even for the owner.
        for label, record in (("post_close -> invoking", invoking), ("post_close -> post_close", post_close)):
            with self.subTest(label):
                with self.assertRaises(CascadeEvidenceError):
                    write_evidence_atomic(workspace.evidence, record, owner_run_id=_RUN_A)
                self.assertEqual(workspace.evidence.read_bytes(), final)

    def test_owner_transition_refusals(self) -> None:
        # (label, existing record, new record, owner_run_id, takeover_from_run_id, lock run_id)
        foreign_invoking = _cascade_pre_close(_RUN_A)
        foreign_invoking["phase"] = "invoking"
        mine_invoking = copy.deepcopy(foreign_invoking)
        mine_invoking["run_id"] = _RUN_B
        rows = [
            ("foreign writer over pre_close", _cascade_pre_close(_RUN_A), mine_invoking, _RUN_B, None, _RUN_B),
            ("record run_id differs from owner", None, _cascade_pre_close(_RUN_A), _RUN_B, None, _RUN_B),
            ("owner without the lock", None, _cascade_pre_close(_RUN_B), _RUN_B, None, _RUN_C),
            ("fresh record must start at pre_close", None, mine_invoking, _RUN_B, None, _RUN_B),
            ("pre_close skipping invoking", _cascade_pre_close(_RUN_B),
             _record(cascade_record, phase="post_close", run_id=_RUN_B), _RUN_B, None, _RUN_B),
            ("takeover with the wrong prior run_id", _cascade_pre_close(_RUN_A), _cascade_pre_close(_RUN_B),
             _RUN_B, _RUN_C, _RUN_B),
            ("takeover over an invoking record", foreign_invoking, _cascade_pre_close(_RUN_B), _RUN_B, _RUN_A, _RUN_B),
            ("takeover over a post_close record", _record(cascade_record, phase="post_close", run_id=_RUN_A),
             _cascade_pre_close(_RUN_B), _RUN_B, _RUN_A, _RUN_B),
            ("takeover writing a non-pre_close record", _cascade_pre_close(_RUN_A), mine_invoking,
             _RUN_B, _RUN_A, _RUN_B),
            ("takeover with no prior record", None, _cascade_pre_close(_RUN_B), _RUN_B, _RUN_A, _RUN_B),
        ]
        for label, existing, new, owner, takeover, lock_run in rows:
            with self.subTest(label):
                workspace, _ = self._locked(lock_run)
                before = workspace.place(existing) if existing is not None else None
                with self.assertRaises(CascadeEvidenceError):
                    write_evidence_atomic(
                        workspace.evidence, new, owner_run_id=owner, takeover_from_run_id=takeover
                    )
                if before is None:
                    self.assertFalse(workspace.evidence.exists())
                else:
                    self.assertEqual(workspace.evidence.read_bytes(), before)

    def test_pre_close_takeover(self) -> None:
        for label, existing in (
            ("cascade-selected", _cascade_pre_close(_RUN_A)),
            ("safe_close-selected", _record(safe_close_record, phase="pre_close", run_id=_RUN_A)),
        ):
            with self.subTest(label):
                workspace, lock = self._locked(_RUN_B)
                workspace.place(existing)
                handed_off = check_existing_record(lock, mode=MODE_MUTATING)
                restamped = copy.deepcopy(handed_off)
                restamped["run_id"] = _RUN_B
                restamped["pre_close"]["captured_at"] = "2026-10-02T01:00:00Z"
                write_evidence_atomic(
                    workspace.evidence,
                    restamped,
                    owner_run_id=_RUN_B,
                    takeover_from_run_id=handed_off["run_id"],
                )
                on_disk = json.loads(workspace.evidence.read_text(encoding="utf-8"))
                self.assertEqual(on_disk["run_id"], _RUN_B)
                # The record is now bound to the new run: ordinary owner transitions follow.
                invoking = copy.deepcopy(restamped)
                invoking["phase"] = "invoking"
                write_evidence_atomic(workspace.evidence, invoking, owner_run_id=_RUN_B)
                self.assertEqual(json.loads(workspace.evidence.read_text(encoding="utf-8"))["phase"], "invoking")

    def test_atomic_write_failure_and_symlink_target(self) -> None:
        with self.subTest("simulated replace failure leaves no partial file"):
            workspace, _ = self._locked(_RUN_A)
            before = workspace.place(_cascade_pre_close(_RUN_A))
            invoking = _cascade_pre_close(_RUN_A)
            invoking["phase"] = "invoking"
            with mock.patch.object(persist.os, "replace", side_effect=OSError("disk full")):
                with self.assertRaises(CascadeEvidenceError):
                    write_evidence_atomic(workspace.evidence, invoking, owner_run_id=_RUN_A)
            self.assertEqual(workspace.evidence.read_bytes(), before)
            self.assertEqual(sorted(p.name for p in workspace.evidence.parent.iterdir()), [workspace.evidence.name])

        with self.subTest("a sharing violation is retried at most 3 times"):
            workspace, _ = self._locked(_RUN_A)
            real_replace = os.replace
            calls = {"count": 0}

            def flaky(src, dst):
                calls["count"] += 1
                if calls["count"] < 3:
                    raise PermissionError("sharing violation")
                return real_replace(src, dst)

            with mock.patch.object(persist.os, "replace", side_effect=flaky), mock.patch.object(
                persist.time, "sleep"
            ):
                write_evidence_atomic(workspace.evidence, _cascade_pre_close(_RUN_A), owner_run_id=_RUN_A)
            self.assertEqual(calls["count"], 3)
            self.assertTrue(workspace.evidence.exists())

        with self.subTest("a symlinked target is refused"):
            workspace, _ = self._locked(_RUN_A)
            workspace.evidence.parent.mkdir(parents=True, exist_ok=True)
            target = workspace.outside / "elsewhere.json"
            target.write_text("{}\n", encoding="utf-8")
            try:
                os.symlink(target, workspace.evidence)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"cannot create file symlink: {exc}")
            with self.assertRaises(CascadeEvidenceError):
                write_evidence_atomic(workspace.evidence, _cascade_pre_close(_RUN_A), owner_run_id=_RUN_A)
            self.assertEqual(target.read_text(encoding="utf-8"), "{}\n")
            self.assertTrue(workspace.evidence.is_symlink())


if __name__ == "__main__":
    unittest.main()
