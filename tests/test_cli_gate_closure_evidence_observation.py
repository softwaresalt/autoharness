"""CLI tests for the closure-evidence gate's SAFE_CLOSE observation-set re-check (192.016-T, plan unit A4b).

For a ``safe_close`` record, the gate re-checks every ``pre_close.observation_set``
entry at write time: a located entry must still be at exactly its recorded path
and location with its recorded SHA-256, and a ``location: missing`` entry must
still be missing. Paths are containment-checked before any byte is read, and
the first segment must be the detected backlog root. An empty set passes with a
vacuous-check warning. Every failure is ``failed_check: close_evidence``.

Fixture observation sets come from the real A2b ``compute_observation_set`` over
a scratch ``.backlogit`` tree, so the tests pin the producer and the gate together.
"""

from __future__ import annotations

import hashlib
import os
import unittest
from pathlib import Path
from unittest import mock

from test_cascade_evidence_contract import _disposition, _engine_record
from test_cli_gate_closure_evidence import (
    _MERGE_SHA,
    _READY,
    _ClosureWorkspaceMixin,
    _make_dir_link,
    _run_json,
    evidence_record,
    evidence_relpath,
    with_close_keys,
)

from autoharness.gates.cascade_evidence import (
    build_evidence_path,
    observation_entry_to_record,
    serialize_evidence_record,
)
from autoharness.gates.closure_contract import build_closure_path
from autoharness.shipment_close.observation import compute_observation_set

_SHIPMENT = "175-S"
_FEATURE = "167-F"
_UNVERIFIED = "1.10.1"


def _write_record(
    root: Path,
    folder: str,
    artifact_id: str,
    *,
    artifact_type: str = "task",
    status: str = "queued",
    parent_id: str | None = None,
    note: str = "",
) -> Path:
    """Write one ``.backlogit/{folder}/{id}.md`` record (both folders always exist)."""

    for name in ("queue", "archive"):
        (root / ".backlogit" / name).mkdir(parents=True, exist_ok=True)
    parent = f"parent_id: {parent_id}\n" if parent_id else ""
    path = root / ".backlogit" / folder / f"{artifact_id}.md"
    path.write_text(
        f"---\nid: {artifact_id}\nartifact_type: {artifact_type}\nstatus: {status}\n{parent}---\n# {artifact_id}\n{note}",
        encoding="utf-8",
    )
    return path


def _move(root: Path, artifact_id: str, source: str, target: str) -> None:
    (root / ".backlogit" / source / f"{artifact_id}.md").rename(root / ".backlogit" / target / f"{artifact_id}.md")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class _ObservationGateMixin(_ClosureWorkspaceMixin):
    def _partial_feature_fixture(self) -> list[dict]:
        """Task-only, partial-feature manifest [167.001-T]; returns the A2b observation set."""

        _write_record(self.root, "queue", _FEATURE, artifact_type="feature", status="active")
        _write_record(self.root, "queue", "167.001-T", status="done", parent_id=_FEATURE)
        _write_record(self.root, "queue", "167.002-T", status="queued", parent_id=_FEATURE)
        _write_record(self.root, "archive", "167.003-T", status="done", parent_id=_FEATURE)
        entries = compute_observation_set(
            ["167.001-T"], _SHIPMENT, self.root / ".backlogit", excluded_ids=()
        )
        observed = [observation_entry_to_record(entry) for entry in entries]
        self.assertEqual(
            [(entry["id"], entry["location"]) for entry in observed],
            [("167-F", "queue"), ("167.002-T", "queue"), ("167.003-T", "archive")],
        )
        return observed

    def _gate_with(
        self,
        observation_set: list[dict],
        *,
        classifier: str = "SAFE_CLOSE",
        engine: dict | None = None,
        dispositions: list[dict] | None = None,
    ) -> tuple[dict, int]:
        record = evidence_record("safe_close", _SHIPMENT, _FEATURE, classifier=classifier, engine=engine)
        record["pre_close"]["observation_set"] = observation_set
        if dispositions is not None:
            record["pre_close"]["linked_deliberation_disposition"]["dispositions"] = dispositions
        evidence = build_evidence_path(self.root, _SHIPMENT, _FEATURE)
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(serialize_evidence_record(record), encoding="utf-8")
        for existing in self.closure_dir.glob("*.md"):
            existing.unlink()
        body = with_close_keys(_READY, "safe_close", evidence_relpath(_SHIPMENT, _FEATURE), merge_commit=_MERGE_SHA)
        artifact = build_closure_path("docs/closure", _SHIPMENT, _FEATURE, workspace_root=self.root)
        artifact.write_text(body, encoding="utf-8")
        payload, code = _run_json(
            "gate", "closure-evidence", "--path", str(artifact), "--workspace", str(self.root)
        )
        return payload, code if code is not None else 0


class ObservationSetRecheckTests(_ObservationGateMixin, unittest.TestCase):
    """Scenario 1: the observation-set table."""

    def test_observation_set_table(self) -> None:
        def archive_parent() -> None:
            _move(self.root, _FEATURE, "queue", "archive")

        def modify_sibling() -> None:
            path = self.root / ".backlogit" / "queue" / "167.002-T.md"
            path.write_text(path.read_text(encoding="utf-8").replace("queued", "done"), encoding="utf-8")

        def archive_sibling() -> None:
            _move(self.root, "167.002-T", "queue", "archive")

        def modify_archived_sibling() -> None:
            path = self.root / ".backlogit" / "archive" / "167.003-T.md"
            path.write_text(path.read_text(encoding="utf-8") + "touched\n", encoding="utf-8")

        def safe_close_manifest_task() -> None:
            _move(self.root, "167.001-T", "queue", "archive")

        rows = [
            ("unchanged, sibling already archived at baseline", None, None),
            ("safe-close archived the manifest task", safe_close_manifest_task, None),
            ("parent feature now archived", archive_parent, "167-F"),
            ("sibling now modified", modify_sibling, "167.002-T"),
            ("sibling now archived", archive_sibling, "167.002-T"),
            ("baseline-archived sibling now modified", modify_archived_sibling, "167.003-T"),
        ]
        for label, mutate, culprit in rows:
            with self.subTest(row=label):
                observed = self._partial_feature_fixture()
                if mutate is not None:
                    mutate()
                payload, code = self._gate_with(observed)
                if culprit is None:
                    self.assertEqual((code, payload["failed_check"]), (0, None), payload["message"])
                    self.assertFalse([w for w in payload["warnings"] if "vacuous" in w], payload["warnings"])
                else:
                    self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"), payload["message"])
                    self.assertIn(culprit, payload["message"])
                for name in ("queue", "archive"):
                    for leftover in (self.root / ".backlogit" / name).glob("*.md"):
                        leftover.unlink()

    def test_empty_observation_set_passes_with_vacuous_warning(self) -> None:
        payload, code = self._gate_with([])
        self.assertEqual((code, payload["failed_check"]), (0, None), payload["message"])
        self.assertTrue([w for w in payload["warnings"] if "vacuous" in w], payload["warnings"])

    def test_whole_feature_cascade_classifier_unverified_engine_passes_after_safe_close(self) -> None:
        # Re-plan cycle-1 R11: the manifest feature is inside closure_scope(S), never observed.
        _write_record(self.root, "queue", _FEATURE, artifact_type="feature", status="active")
        _write_record(self.root, "queue", "167.001-T", status="done", parent_id=_FEATURE)
        _write_record(self.root, "queue", "167.002-T", status="done", parent_id=_FEATURE)
        _write_record(self.root, "queue", "168-F", artifact_type="feature", status="active")
        entries = compute_observation_set(
            [_FEATURE, "167.001-T", "167.002-T"], _SHIPMENT, self.root / ".backlogit", excluded_ids=()
        )
        observed = [observation_entry_to_record(entry) for entry in entries]
        self.assertNotIn(_FEATURE, [entry["id"] for entry in observed])
        for artifact_id in (_FEATURE, "167.001-T", "167.002-T"):
            _move(self.root, artifact_id, "queue", "archive")
        payload, code = self._gate_with(observed, classifier="CASCADE", engine=_engine_record(_UNVERIFIED))
        self.assertEqual((code, payload["failed_check"]), (0, None), payload["message"])

    def test_missing_entry_must_stay_missing(self) -> None:
        _write_record(self.root, "queue", _FEATURE, artifact_type="feature", status="active")
        missing = {"id": "167.099-T", "path": None, "location": "missing", "sha256": None, "declared_status": None}
        with self.subTest(row="still missing"):
            payload, code = self._gate_with([dict(missing)])
            self.assertEqual((code, payload["failed_check"]), (0, None), payload["message"])
        with self.subTest(row="now resolves to a record"):
            _write_record(self.root, "archive", "167.099-T", status="done", parent_id=_FEATURE)
            payload, code = self._gate_with([dict(missing)])
            self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"), payload["message"])
            self.assertIn("167.099-T", payload["message"])
        with self.subTest(row="torn resolution"):
            _write_record(self.root, "queue", "167.099-T", status="done", parent_id=_FEATURE)
            payload, code = self._gate_with([dict(missing)])
            self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"), payload["message"])

    def test_path_containment_before_any_read(self) -> None:
        opened: list[str] = []
        real_open = os.open

        def spy(path, *args, **kwargs):
            opened.append(os.path.abspath(os.fspath(path)))
            return real_open(path, *args, **kwargs)

        with self.subTest(row="first segment is not the detected backlog root"):
            target = _write_record(self.root, "queue", "167.002-T", status="queued", parent_id=_FEATURE)
            entry = {
                "id": "167.002-T",
                "path": ".backlog/queue/167.002-T.md",
                "location": "queue",
                "sha256": _sha(target),
                "declared_status": "queued",
            }
            opened.clear()
            with mock.patch("os.open", side_effect=spy):
                payload, code = self._gate_with([entry])
            self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"), payload["message"])
            self.assertIn("backlog root", payload["message"])
            self.assertFalse([p for p in opened if p.endswith("167.002-T.md")], opened)

        with self.subTest(row="junctioned or symlinked component"):
            outside_archive = self.outside / "archive"
            outside_archive.mkdir()
            planted = outside_archive / "167.003-T.md"
            planted.write_text("---\nid: 167.003-T\nartifact_type: task\nstatus: done\n---\n", encoding="utf-8")
            archive_dir = self.root / ".backlogit" / "archive"
            for leftover in archive_dir.glob("*.md"):
                leftover.unlink()
            archive_dir.rmdir()
            reason = _make_dir_link(archive_dir, outside_archive)
            if reason:
                self.skipTest(reason)
            entry = {
                "id": "167.003-T",
                "path": ".backlogit/archive/167.003-T.md",
                "location": "archive",
                "sha256": _sha(planted),
                "declared_status": "done",
            }
            opened.clear()
            with mock.patch("os.open", side_effect=spy):
                payload, code = self._gate_with([entry])
            self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"), payload["message"])
            self.assertIn("symlink_or_reparse_point", payload["message"])
            self.assertFalse([p for p in opened if p.startswith(str(self.outside))], "read outside the backlog")

    def test_recorded_location_must_match_the_path(self) -> None:
        target = _write_record(self.root, "queue", "167.002-T", status="queued", parent_id=_FEATURE)
        entry = {
            "id": "167.002-T",
            "path": ".backlogit/queue/167.002-T.md",
            "location": "archive",
            "sha256": _sha(target),
            "declared_status": "queued",
        }
        payload, code = self._gate_with([entry])
        self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"), payload["message"])


class DispositionRecheckTests(_ObservationGateMixin, unittest.TestCase):
    """Scenario 2: the disposition table (re-plan cycle-1 R2 regression pin; cycle-2 C2-1)."""

    def _deliberation(self) -> tuple[Path, dict]:
        path = _write_record(self.root, "queue", "035-DL", artifact_type="deliberation", status="accepted")
        disposition = _disposition("retained_engine_unverified")
        disposition["records"][0]["sha256"] = _sha(path)
        return path, disposition

    def test_verified_engine_disposition_archive_after_safe_close_passes(self) -> None:
        for outcome in ("archive", "retained_live_status", "retained_shared_reference"):
            with self.subTest(outcome=outcome):
                observed = self._partial_feature_fixture()
                _path, disposition = self._deliberation()
                disposition["outcome"] = outcome
                disposition["reason_code"] = outcome
                if outcome == "archive":
                    # The skill's disposition step is the sole archiver, after safe-close.
                    _move(self.root, "035-DL", "queue", "archive")
                payload, code = self._gate_with(observed, dispositions=[disposition])
                self.assertEqual((code, payload["failed_check"]), (0, None), payload["message"])
                self.assertFalse([w for w in payload["warnings"] if "stranded" in w], payload["warnings"])
                for name in ("queue", "archive"):
                    for leftover in (self.root / ".backlogit" / name).glob("*.md"):
                        leftover.unlink()

    def test_unverified_engine_deliberation_is_rechecked_byte_identical(self) -> None:
        def archive_it(path: Path) -> None:
            _move(self.root, "035-DL", "queue", "archive")

        def modify_it(path: Path) -> None:
            path.write_text(path.read_text(encoding="utf-8").replace("accepted", "archived"), encoding="utf-8")

        rows = [("unchanged", None), ("direct cascade archived it", archive_it), ("direct cascade modified it", modify_it)]
        for label, mutate in rows:
            with self.subTest(row=label):
                observed = self._partial_feature_fixture()
                path, disposition = self._deliberation()
                observed.append(
                    {
                        "id": "035-DL",
                        "path": ".backlogit/queue/035-DL.md",
                        "location": "queue",
                        "sha256": _sha(path),
                        "declared_status": "accepted",
                    }
                )
                if mutate is not None:
                    mutate(path)
                payload, code = self._gate_with(
                    observed, engine=_engine_record(_UNVERIFIED), dispositions=[disposition]
                )
                if mutate is None:
                    self.assertEqual((code, payload["failed_check"]), (0, None), payload["message"])
                else:
                    self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"), payload["message"])
                    self.assertIn("035-DL", payload["message"])
                self.assertFalse([w for w in payload["warnings"] if "stranded" in w], payload["warnings"])
                for name in ("queue", "archive"):
                    for leftover in (self.root / ".backlogit" / name).glob("*.md"):
                        leftover.unlink()


if __name__ == "__main__":
    unittest.main()
