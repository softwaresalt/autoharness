"""Gate-level engine-window tests: closure-evidence through the real window logic on both close paths (171-S)."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from test_cli_gate_closure_evidence import (
    _READY,
    evidence_record,
    evidence_relpath,
    with_close_keys,
    write_evidence,
    _MERGE_SHA,
    _run_json,
)

from autoharness import cli
from autoharness.gates.closure_contract import build_closure_path

_SHIP = "175-S"
_FEAT = "167-F"
_MERGE = datetime(2026, 10, 1, 23, 0, 0, tzinfo=timezone.utc)


class WindowGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve() / "workspace"
        (self.root / "docs" / "closure").mkdir(parents=True)

    def _prepare(self, close_path: str, events: dict[str, list[dict]] | None = None) -> Path:
        record = evidence_record(close_path, _SHIP, _FEAT)
        write_evidence(self.root, _SHIP, _FEAT, record)
        logs = self.root / ".backlogit" / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        ids = [_SHIP] + [m["id"] for m in record["pre_close"]["manifest_members"]]
        for item_id in ids:
            lines = [json.dumps(e) for e in (events or {}).get(item_id, [])]
            (logs / f"{item_id}.jsonl").write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        body = with_close_keys(_READY, close_path, evidence_relpath(_SHIP, _FEAT), merge_commit=_MERGE_SHA)
        path = build_closure_path("docs/closure", _SHIP, _FEAT, workspace_root=self.root)
        path.write_text(body, encoding="utf-8")
        self.member = record["pre_close"]["manifest_members"][0]["id"]
        return path

    def _gate(self, path: Path) -> tuple[dict, int | None]:
        with mock.patch.object(cli, "_merge_committer_time", return_value=_MERGE):
            return _run_json("gate", "closure-evidence", "--path", str(path), "--workspace", str(self.root))

    def _check(self, close_path: str, *, bad_event: bool, timestamp: str = "2026-10-01T23:30:00Z") -> None:
        path = self._prepare(close_path)
        if bad_event:
            event = {"timestamp": timestamp, "item_id": self.member, "event_type": "archived", "delta": {}}
            (self.root / ".backlogit" / "logs" / f"{self.member}.jsonl").write_text(
                json.dumps(event) + "\n", encoding="utf-8"
            )
        payload, code = self._gate(path)
        if bad_event:
            self.assertEqual(code, 1)
            self.assertEqual(payload["failed_check"], "close_evidence")
            self.assertIn("not provably pre-mutation", payload["message"])
        else:
            self.assertIn(code, (0, None), payload)

    def test_cascade_clean_passes(self) -> None:
        self._check("cascade", bad_event=False)

    def test_cascade_close_mutation_in_window_fails(self) -> None:
        self._check("cascade", bad_event=True)

    def test_safe_close_clean_passes(self) -> None:
        self._check("safe_close", bad_event=False)

    def test_safe_close_close_mutation_in_window_fails(self) -> None:
        self._check("safe_close", bad_event=True)

    def test_close_mutation_with_garbage_timestamp_fails_closed(self) -> None:
        for close_path in ("cascade", "safe_close"):
            with self.subTest(close_path=close_path):
                self._check(close_path, bad_event=True, timestamp="not-a-time")
        path = self._prepare("cascade")
        event = {"item_id": self.member, "event_type": "archived", "delta": {}}
        (self.root / ".backlogit" / "logs" / f"{self.member}.jsonl").write_text(
            json.dumps(event) + "\n", encoding="utf-8"
        )
        payload, code = self._gate(path)
        self.assertEqual(code, 1)
        self.assertEqual(payload["failed_check"], "close_evidence")
        self.assertIn("malformed timestamp", payload["message"])


if __name__ == "__main__":
    unittest.main()
