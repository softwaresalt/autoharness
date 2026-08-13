"""Tests for autoharness.supervise.journal -- the append-only session journal
(119.005-T).

Covers append-only behavior, seq monotonicity, crash-mid-write recovery,
cursor resume across a fresh instance, redaction (no secret substring of
length >= 8 survives to disk), git-ignore containment (H6, reusing
locking.ensure_ignored), and path containment against an escaping
session_id.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from autoharness.supervise.contracts import ChildOutputUnavailable
from autoharness.supervise.errors import LockError
from autoharness.supervise.journal import SessionJournal, read_cursor
from autoharness.supervise.redact import Redactor


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )


class AppendOnlyAndMonotonicityTests(unittest.TestCase):
    def test_writes_only_append_never_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="s1")
            journal.append_event(ChildOutputUnavailable(reason="one"))
            first_content = journal.journal_path.read_text(encoding="utf-8")
            journal.append_event(ChildOutputUnavailable(reason="two"))
            second_content = journal.journal_path.read_text(encoding="utf-8")

            self.assertTrue(second_content.startswith(first_content))
            self.assertGreater(len(second_content), len(first_content))

    def test_seq_is_monotonically_increasing(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="s1")
            seqs = [
                journal.append_event(ChildOutputUnavailable(reason=str(i)))
                for i in range(5)
            ]
            self.assertEqual(seqs, sorted(seqs))
            self.assertEqual(len(seqs), len(set(seqs)))

    def test_header_is_written_as_first_line(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="s1")
            journal.append_event(ChildOutputUnavailable(reason="x"))
            lines = journal.journal_path.read_text(encoding="utf-8").splitlines()
            header = json.loads(lines[0])
            self.assertEqual(header["kind"], "header")
            self.assertEqual(header["schema_version"], 1)
            self.assertEqual(header["session_id"], "s1")


class CrashMidWriteRecoveryTests(unittest.TestCase):
    def test_read_cursor_tolerates_truncated_final_line(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="s1")
            journal.append_event(ChildOutputUnavailable(reason="a"))
            journal.append_event(ChildOutputUnavailable(reason="b"))
            good_cursor = read_cursor(journal.journal_path)

            # Simulate a crash mid-write: append a truncated/corrupt line.
            with journal.journal_path.open("a", encoding="utf-8") as handle:
                handle.write('{"seq": 99, "kind": "event", "incompl')

            recovered_cursor = read_cursor(journal.journal_path)
            self.assertEqual(recovered_cursor, good_cursor)

    def test_read_cursor_on_missing_file_returns_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            missing_path = Path(workspace) / "does-not-exist.jsonl"
            self.assertEqual(read_cursor(missing_path), -1)


class CursorResumeTests(unittest.TestCase):
    def test_fresh_instance_continues_seq_after_simulated_crash(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            first = SessionJournal(workspace, session_id="s1")
            seq_a = first.append_event(ChildOutputUnavailable(reason="a"))
            seq_b = first.append_event(ChildOutputUnavailable(reason="b"))
            del first  # simulate the process crashing / instance going away

            second = SessionJournal(workspace, session_id="s1")
            seq_c = second.append_event(ChildOutputUnavailable(reason="c"))

            self.assertEqual([seq_a, seq_b, seq_c], sorted([seq_a, seq_b, seq_c]))
            self.assertGreater(seq_c, seq_b)


class RedactionChokePointTests(unittest.TestCase):
    def test_no_secret_substring_of_length_8_or_more_survives_to_disk(self) -> None:
        secret = "SUPER-SECRET-VALUE-abcdefgh"
        redactor = Redactor()
        redactor.register_secret(secret)
        with tempfile.TemporaryDirectory() as workspace:
            journal = SessionJournal(workspace, session_id="s1", redactor=redactor)
            journal.append_event(ChildOutputUnavailable(reason=f"leaked={secret}"))

            content = journal.journal_path.read_text(encoding="utf-8")
            # No 8+-character substring of the secret should appear verbatim.
            for start in range(0, len(secret) - 8 + 1):
                chunk = secret[start : start + 8]
                self.assertNotIn(chunk, content)


class GitIgnoreContainmentTests(unittest.TestCase):
    def test_session_directory_is_git_ignored(self) -> None:
        if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
            self.skipTest("git is not available in this environment")

        with tempfile.TemporaryDirectory() as workspace:
            # Resolve consistently with SessionJournal's own internal
            # resolution (Path(workspace_root).resolve()) -- on Windows,
            # tempfile.TemporaryDirectory() can otherwise hand back an
            # 8.3-short-name form that doesn't match the long-form path
            # SessionJournal resolves internally, breaking relative_to().
            workspace_path = Path(workspace).resolve()
            init = _run_git(["init", "-q"], cwd=workspace_path)
            if init.returncode != 0:
                self.skipTest(f"git init failed: {init.stderr}")

            journal = SessionJournal(workspace_path, session_id="s1")
            journal.append_event(ChildOutputUnavailable(reason="x"))

            check = _run_git(
                ["check-ignore", str(journal.session_dir.relative_to(workspace_path))],
                cwd=workspace_path,
            )
            self.assertEqual(
                check.returncode,
                0,
                f"expected session dir to be git-ignored; stdout={check.stdout!r} stderr={check.stderr!r}",
            )


class PathContainmentTests(unittest.TestCase):
    def test_escaping_session_id_raises_rather_than_writing_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            # Three ".." segments are required to actually escape here: two
            # cancel the fixed ".autoharness/sessions" prefix, and the third
            # then climbs above the workspace root itself. Two ".." segments
            # would merely land back at the (still-contained) workspace root.
            with self.assertRaises(LockError):
                SessionJournal(workspace, session_id="../../../evil")

    def test_escaping_session_id_with_windows_separators_raises(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            with self.assertRaises(LockError):
                SessionJournal(workspace, session_id="..\\..\\..\\evil")


if __name__ == "__main__":
    unittest.main()
