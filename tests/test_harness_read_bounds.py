"""Unit C, task C3 (187.003-T): harness_read bounded reads and read budget.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "C3: Bounded reads and read budget".

Proof G cases G25 to G29 run on each host over a real temporary tree with a
64-byte file cap. Reads are unbuffered and binary and go only through the
private ``_read_chunk(fd, n)`` patch point; the open counter spies on
``os.open`` only. Every failure returns an explicit code and no bytes.

Roster (P-004, Marker Convention): every test in this module; each reached the
RED-phase stub with its own marker ``AHLC_C3_READ_BOUNDS:<t>`` at the C3 RED
commit.
"""

from __future__ import annotations

import errno
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness import harness_read
from autoharness.harness_read import ReadErrorCode, ReadLimits, TrustRoot, open_reader

W = TrustRoot.WORKSPACE
CAP = 64
CRLF_FIXTURE = b"\r\n\x1a" + bytes(range(256)) + b"\r\n\x1a\x00"


class BoundsFixture(unittest.TestCase):
    """The Proof G bounded-read files under ``ws/b``, ``ws/t`` and ``ws/n``."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.mkdtemp(prefix="ahlc-c3-")
        cls.addClassCleanup(shutil.rmtree, cls._tmp, True)
        ws = Path(cls._tmp) / "ws"
        cls.ws = ws
        files = {
            "b/cap.bin": b"A" * 64,
            "b/cap1.bin": b"B" * 65,
            "b/big.bin": b"C" * 4096,
            "t/t1.bin": b"D" * 64,
            "t/t2.bin": b"E" * 64,
            "t/t3.bin": b"F",
            "n/c1.txt": b"C1-01\n",
            "n/c2.txt": b"C2-02\n",
            "n/c3.txt": b"C3-03\n",
            "n/c4.txt": b"C4-04\n",
            "x/crlf.bin": CRLF_FIXTURE,
        }
        for relative, data in files.items():
            path = ws / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def reader(self, **limits: int):
        return open_reader(workspace_root=str(self.ws), limits=ReadLimits(**limits))

    def assert_ok(self, result, expected: bytes) -> None:
        self.assertIsNone(result.error)
        self.assertEqual(result.data, expected)

    def assert_error(self, result, code: ReadErrorCode) -> None:
        self.assertIs(result.error, code)
        self.assertIsNone(result.data)


class _ChunkRecorder:
    """Stands in for ``_read_chunk``: records each request and returns short reads."""

    def __init__(self, *, short: int | None = None, endless: bool = False) -> None:
        self.requests: list[int] = []
        self.returned: list[int] = []
        self.short = short
        self.endless = endless

    def __call__(self, fd: int, n: int) -> bytes:
        self.requests.append(n)
        if self.endless:
            data = b"Z" * n
        else:
            data = os.read(fd, min(n, self.short) if self.short else n)
        self.returned.append(len(data))
        return data


class BoundedReadCaseTests(BoundsFixture):
    def test_G25_exact_cap_accepted(self) -> None:
        self.assert_ok(self.reader(max_file_bytes=CAP).read_bytes(W, "b/cap.bin"), b"A" * 64)

    def test_G26_cap_plus_one_rejected(self) -> None:
        recorder = _ChunkRecorder()
        with mock.patch.object(harness_read, "_read_chunk", recorder):
            result = self.reader(max_file_bytes=CAP).read_bytes(W, "b/cap1.bin")
        self.assert_error(result, ReadErrorCode.FILE_SIZE_LIMIT)
        self.assertLessEqual(sum(recorder.requests), CAP + 1)
        # The fstat size check rejects it before any read request.
        self.assertEqual(recorder.requests, [])

    def test_G27_large_file_rejected_after_at_most_cap_plus_one(self) -> None:
        recorder = _ChunkRecorder()
        with mock.patch.object(harness_read, "_read_chunk", recorder):
            result = self.reader(max_file_bytes=CAP).read_bytes(W, "b/big.bin")
        self.assert_error(result, ReadErrorCode.FILE_SIZE_LIMIT)
        self.assertLessEqual(sum(recorder.requests), CAP + 1)
        self.assertEqual(recorder.requests, [])

    def _total_reader(self):
        return self.reader(max_file_bytes=CAP, max_total_bytes=2 * CAP)

    def test_G28a_total_first_accept(self) -> None:
        reader = self._total_reader()
        self.assert_ok(reader.read_bytes(W, "t/t1.bin"), b"D" * 64)
        self.assertEqual(reader.usage.bytes_reserved, 64)

    def test_G28b_total_second_accept(self) -> None:
        reader = self._total_reader()
        self.assert_ok(reader.read_bytes(W, "t/t1.bin"), b"D" * 64)
        self.assert_ok(reader.read_bytes(W, "t/t2.bin"), b"E" * 64)
        self.assertEqual(reader.usage.bytes_reserved, 128)

    def test_G28c_total_exhausted(self) -> None:
        reader = self._total_reader()
        self.assert_ok(reader.read_bytes(W, "t/t1.bin"), b"D" * 64)
        self.assert_ok(reader.read_bytes(W, "t/t2.bin"), b"E" * 64)
        recorder = _ChunkRecorder()
        with mock.patch.object(harness_read, "_read_chunk", recorder):
            result = reader.read_bytes(W, "t/t3.bin")
        self.assert_error(result, ReadErrorCode.TOTAL_SIZE_LIMIT)
        self.assertLessEqual(sum(recorder.requests), 1)
        self.assertEqual(recorder.requests, [])
        self.assertEqual(reader.usage.files_claimed, 3)

    def _count_sequence(self, accepts: int):
        reader = self.reader(max_files=3)
        expected = [b"C1-01\n", b"C2-02\n", b"C3-03\n"]
        for index in range(accepts):
            self.assert_ok(reader.read_bytes(W, f"n/c{index + 1}.txt"), expected[index])
        return reader

    def test_G29a_count_first_accept(self) -> None:
        self.assertEqual(self._count_sequence(1).usage.files_claimed, 1)

    def test_G29b_count_second_accept(self) -> None:
        self.assertEqual(self._count_sequence(2).usage.files_claimed, 2)

    def test_G29c_count_third_accept(self) -> None:
        self.assertEqual(self._count_sequence(3).usage.files_claimed, 3)

    def test_G29d_count_exhausted_before_any_open(self) -> None:
        reader = self._count_sequence(3)
        with mock.patch("os.open", wraps=os.open) as open_spy:
            result = reader.read_bytes(W, "n/c4.txt")
        self.assert_error(result, ReadErrorCode.FILE_COUNT_LIMIT)
        self.assertEqual(open_spy.call_count, 0)
        self.assertEqual(reader.usage.files_claimed, 3)


class ReadLoopTests(BoundsFixture):
    def test_reads_go_through_read_chunk_and_continue_through_short_reads(self) -> None:
        recorder = _ChunkRecorder(short=7)
        with mock.patch.object(harness_read, "_read_chunk", recorder):
            result = self.reader(max_file_bytes=CAP).read_bytes(W, "b/cap.bin")
        self.assert_ok(result, b"A" * 64)
        self.assertGreater(len(recorder.requests), 2)
        held = 0
        for request, returned in zip(recorder.requests, recorder.returned):
            self.assertGreaterEqual(request, 1)
            self.assertLessEqual(request, CAP + 1 - held)
            held += returned
        self.assertEqual(recorder.returned[-1], 0, "the loop must read to EOF")

    def test_growth_past_reservation_is_charged_and_capped(self) -> None:
        recorder = _ChunkRecorder(endless=True)
        reader = self.reader(max_file_bytes=CAP)
        with mock.patch.object(harness_read, "_read_chunk", recorder):
            result = reader.read_bytes(W, "t/t3.bin")
        self.assert_error(result, ReadErrorCode.FILE_SIZE_LIMIT)
        self.assertLessEqual(sum(recorder.requests), CAP + 1)
        self.assertEqual(reader.usage.bytes_reserved, CAP + 1)

    def test_growth_past_remaining_total_is_total_limit(self) -> None:
        recorder = _ChunkRecorder(endless=True)
        reader = self.reader(max_file_bytes=CAP, max_total_bytes=10)
        with mock.patch.object(harness_read, "_read_chunk", recorder):
            result = reader.read_bytes(W, "t/t3.bin")
        self.assert_error(result, ReadErrorCode.TOTAL_SIZE_LIMIT)
        self.assertLessEqual(sum(recorder.requests), 11)

    def test_binary_bytes_returned_exactly(self) -> None:
        self.assert_ok(open_reader(workspace_root=str(self.ws)).read_bytes(W, "x/crlf.bin"), CRLF_FIXTURE)

    def test_os_read_failure_is_io_with_no_bytes(self) -> None:
        def failing_chunk(fd: int, n: int) -> bytes:
            raise OSError(errno.EIO, "simulated read failure")

        reader = open_reader(workspace_root=str(self.ws))
        with mock.patch.object(harness_read, "_read_chunk", failing_chunk):
            result = reader.read_bytes(W, "b/cap.bin")
        self.assert_error(result, ReadErrorCode.IO)
        self.assertEqual(result.path, "b/cap.bin")

    def test_usage_never_decreases(self) -> None:
        reader = self.reader(max_file_bytes=CAP, max_total_bytes=200, max_files=6)
        requests = ["t/t1.bin", "..", "b/big.bin", "t/t2.bin", "b/cap1.bin", "t/t3.bin", "n/c1.txt"]
        previous = reader.usage
        for relative_path in requests:
            reader.read_bytes(W, relative_path)
            current = reader.usage
            self.assertGreaterEqual(current.files_claimed, previous.files_claimed)
            self.assertGreaterEqual(current.bytes_reserved, previous.bytes_reserved)
            previous = current
        self.assertEqual(previous.files_claimed, 6)


if __name__ == "__main__":
    unittest.main()
