"""CLI-side engine-log window check: containment-checked log reads and the merge-time seam (171-S U2b)."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from autoharness import cli
from test_cascade_evidence_contract import _SHIPMENT, cascade_record

_MEMBER = "192.001-T"
_FEATURE_MEMBER = "192-F"
_MERGE = datetime(2026, 10, 2, 0, 0, 0, tzinfo=timezone.utc)


class EngineWindowProblemsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve() / "workspace"
        self.logs = self.root / ".backlogit" / "logs"
        self.logs.mkdir(parents=True)
        (self.root / ".backlogit" / "queue").mkdir()
        (self.root / ".backlogit" / "archive").mkdir()
        self.record = copy.deepcopy(cascade_record())
        self.record["pre_close"]["captured_at"] = "2026-10-02T01:00:00Z"
        self.record["invocation"]["started_at"] = "2026-10-02T01:00:05Z"
        self.record["invocation"]["finished_at"] = "2026-10-02T01:10:00Z"
        for item_id in (_SHIPMENT, _MEMBER, _FEATURE_MEMBER):
            (self.logs / f"{item_id}.jsonl").write_text("", encoding="utf-8")

    def _problems(self, merge=_MERGE) -> tuple[list[str], list[str]]:
        warnings: list[str] = []
        with mock.patch.object(cli, "_merge_committer_time", return_value=merge):
            return cli._engine_window_problems(self.record, self.root, warnings), warnings

    def test_clean_logs_pass(self) -> None:
        self.assertEqual(self._problems(), ([], []))

    def test_archive_in_window_in_real_log_file_fails(self) -> None:
        event = {"timestamp": "2026-10-01T17:30:00-07:00", "item_id": _MEMBER, "event_type": "archived", "delta": {}}
        (self.logs / f"{_MEMBER}.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
        problems, _ = self._problems()
        self.assertEqual(len(problems), 1, problems)
        self.assertIn(_MEMBER, problems[0])

    def test_unresolvable_merge_time_fails(self) -> None:
        problems, _ = self._problems(merge=None)
        self.assertEqual(len(problems), 1, problems)

    def test_missing_log_for_unarchived_member_fails(self) -> None:
        (self.logs / f"{_MEMBER}.jsonl").unlink()
        problems, _ = self._problems()
        self.assertTrue(any(_MEMBER in p for p in problems), problems)

    def test_log_symlink_escaping_the_backlog_is_refused(self) -> None:
        target = self.root.parent / "outside.jsonl"
        target.write_text("", encoding="utf-8")
        link = self.logs / f"{_MEMBER}.jsonl"
        link.unlink()
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("symlinks unavailable")
        problems, _ = self._problems()
        self.assertTrue(any(_MEMBER in p for p in problems), problems)

    def test_unsafe_member_id_is_refused_without_a_read(self) -> None:
        self.record["pre_close"]["manifest_members"][0]["id"] = "..\\evil"
        problems, _ = self._problems()
        self.assertTrue(any("safe artifact ID" in p for p in problems), problems)

    def test_backlog_root_undetectable_fails(self) -> None:
        for child in (self.root / ".backlogit").iterdir():
            if child.is_dir():
                for entry in child.iterdir():
                    entry.unlink()
                child.rmdir()
        (self.root / ".backlogit").rmdir()
        problems, _ = self._problems()
        self.assertEqual(len(problems), 1, problems)


class MergeCommitterTimeTests(unittest.TestCase):
    def test_non_hex_or_non_string_sha_is_unresolvable_without_running_git(self) -> None:
        with mock.patch.object(cli.subprocess, "run") as run:
            for sha in ("--output=x", "", None, 123, "zzzzzzz"):
                self.assertIsNone(cli._merge_committer_time(Path("."), sha))
            run.assert_not_called()

    def test_git_output_is_parsed_as_a_utc_instant(self) -> None:
        completed = mock.Mock(returncode=0, stdout="2026-10-01T21:48:32-07:00\n")
        with mock.patch.object(cli.subprocess, "run", return_value=completed):
            result = cli._merge_committer_time(Path("."), "bd824b97999832aa38122f2f70d300ebbb5d2e09")
        self.assertEqual(result, datetime(2026, 10, 2, 4, 48, 32, tzinfo=timezone.utc))

    def test_git_failure_is_unresolvable(self) -> None:
        completed = mock.Mock(returncode=128, stdout="")
        with mock.patch.object(cli.subprocess, "run", return_value=completed):
            self.assertIsNone(cli._merge_committer_time(Path("."), "bd824b9"))


if __name__ == "__main__":
    unittest.main()
