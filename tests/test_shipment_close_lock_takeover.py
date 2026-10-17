"""Lock payload, pid handoff, serialized stale-lock takeover, and recovery/rollback transitions.

Covers 211.003-T (plan unit T4; hardening H3, H7, H8): the pair lock carries
``host``/``pid_start``/``supervisor``; takeover happens only for a provably
dead owner (or an operator confirmation for an unprovable one), is serialized
by an ``O_EXCL`` guard with an identity recheck inside it, and tombstones the
stale lock; and the evidence writer gains the recovery (``invoking ->
post_close``) and never-spawned rollback (``invoking -> pre_close``)
transitions.
"""

from __future__ import annotations

import copy
import json
import os
import threading
import unittest
from unittest import mock

from autoharness.gates.cascade_evidence import CascadeEvidenceError
from autoharness.shipment_close import EXIT_INPUT, EXIT_LOCKED, liveness
from autoharness.shipment_close import persist
from autoharness.shipment_close.liveness import ProbeResult
from autoharness.shipment_close.persist import (
    PersistError,
    RollbackProof,
    acquire_pair_lock,
    handoff_lock,
    observe_lock,
    takeover_stale_lock,
    write_evidence_atomic,
)

from test_shipment_close_persist import _cascade_pre_close, _record, _Workspace
from test_cascade_evidence_contract import cascade_record

_S, _F = "198-S", "192-F"
_OLD = "a" * 32
_NEW = "b" * 32
_OTHER = "c" * 32
_HOST = "host-a"


def _prober(state: str, start: str | None = None):
    return lambda pid: ProbeResult(state, start=start, detail=state)  # type: ignore[arg-type]


def _stale_lock(workspace: _Workspace, **payload: object) -> bytes:
    base = {"run_id": _OLD, "pid": 4242, "started_at": "2026-10-16T00:00:00Z", "host": _HOST, "pid_start": "100"}
    base.update(payload)
    base = {k: v for k, v in base.items() if v is not ...}
    lock_dir = workspace.root / ".autoharness" / "gates" / "cascade-close"
    lock_dir.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(base, sort_keys=True) + "\n").encode("utf-8")
    (lock_dir / f"{_S}-{_F}.lock").write_bytes(data)
    return data


def _lock_path(workspace: _Workspace):
    return workspace.root / ".autoharness" / "gates" / "cascade-close" / f"{_S}-{_F}.lock"


def _takeover(workspace: _Workspace, observed, **kwargs):
    kwargs.setdefault("local_host", _HOST)
    return takeover_stale_lock(workspace.root, _S, _F, _NEW, observed, **kwargs)


class LockPayloadTest(unittest.TestCase):
    def test_payload_carries_host_pid_start_and_supervisor(self) -> None:
        workspace = _Workspace(self)
        with acquire_pair_lock(workspace.root, _S, _F, _OLD) as lock:
            payload = json.loads(lock.lock_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["pid"], os.getpid())
        self.assertEqual(payload["host"], liveness.current_host())
        self.assertEqual(payload["pid_start"], liveness.process_start_time(os.getpid()))
        self.assertIs(payload["supervisor"], False)
        self.assertEqual(set(payload), {"run_id", "pid", "started_at", "host", "pid_start", "supervisor"})

    def test_supervisor_flag_is_recorded(self) -> None:
        workspace = _Workspace(self)
        with acquire_pair_lock(workspace.root, _S, _F, _OLD, supervisor=True) as lock:
            self.assertIs(json.loads(lock.lock_path.read_text(encoding="utf-8"))["supervisor"], True)


class HandoffTest(unittest.TestCase):
    def test_handoff_rewrites_the_owner_pid_and_keeps_the_run(self) -> None:
        workspace = _Workspace(self)
        with acquire_pair_lock(workspace.root, _S, _F, _OLD) as lock:
            before = json.loads(lock.lock_path.read_text(encoding="utf-8"))
            handoff_lock(lock, pid=777, pid_start="555")
            after = json.loads(lock.lock_path.read_text(encoding="utf-8"))
            self.assertEqual((after["pid"], after["pid_start"], after["supervisor"]), (777, "555", True))
            self.assertEqual((after["run_id"], after["started_at"], after["host"]), (_OLD, before["started_at"], before["host"]))
            self.assertEqual(sorted(os.listdir(lock.lock_path.parent)), [lock.lock_path.name])
        self.assertFalse(lock.lock_path.exists())

    def test_handoff_refuses_a_lock_it_does_not_own(self) -> None:
        workspace = _Workspace(self)
        lock = acquire_pair_lock(workspace.root, _S, _F, _OLD)
        self.addCleanup(lock.release)
        raw = _stale_lock(workspace, run_id=_OTHER)
        with self.assertRaises(PersistError):
            handoff_lock(lock, pid=1, pid_start=None)
        self.assertEqual(lock.lock_path.read_bytes(), raw)

    def test_handoff_rejects_invalid_pid_and_failed_replace_keeps_the_old_lock(self) -> None:
        workspace = _Workspace(self)
        with acquire_pair_lock(workspace.root, _S, _F, _OLD) as lock:
            with self.assertRaises(PersistError):
                handoff_lock(lock, pid=0, pid_start=None)
            before = lock.lock_path.read_bytes()
            with mock.patch.object(persist, "_replace_with_retry", side_effect=PermissionError("busy")):
                with self.assertRaises(PersistError):
                    handoff_lock(lock, pid=5, pid_start=None)
            self.assertEqual(lock.lock_path.read_bytes(), before)
            self.assertEqual(sorted(os.listdir(lock.lock_path.parent)), [lock.lock_path.name])


class ObserveLockTest(unittest.TestCase):
    def test_absent_parsed_and_unparsable(self) -> None:
        workspace = _Workspace(self)
        self.assertIsNone(observe_lock(workspace.root, _S, _F))
        raw = _stale_lock(workspace)
        seen = observe_lock(workspace.root, _S, _F)
        self.assertEqual((seen.run_id, seen.pid, seen.pid_start, seen.host, seen.parsed), (_OLD, 4242, "100", _HOST, True))
        self.assertFalse(seen.supervisor)
        _lock_path(workspace).write_bytes(b"{torn")
        torn = observe_lock(workspace.root, _S, _F)
        self.assertFalse(torn.parsed)
        self.assertNotEqual(torn.raw_sha256, seen.raw_sha256)
        self.assertEqual(len(raw) > 0, True)

    def test_a_recursion_error_while_parsing_a_lock_is_an_unparsable_lock(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace)
        with mock.patch.object(persist.json, "loads", side_effect=RecursionError):
            seen = observe_lock(workspace.root, _S, _F)
            self.assertFalse(seen.parsed)
            self.assertEqual(persist._read_lock_run_id(_lock_path(workspace)), (None, False))

    def test_legacy_payload_is_parsed_with_missing_identity(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace, host=..., pid_start=...)
        seen = observe_lock(workspace.root, _S, _F)
        self.assertTrue(seen.parsed)
        self.assertIsNone(seen.host)
        self.assertIsNone(seen.pid_start)


class TakeoverTest(unittest.TestCase):
    def test_dead_owner_is_tombstoned_and_a_new_lock_is_created(self) -> None:
        for label, prober, basis in (
            ("pid absent", _prober("absent"), "pid_absent"),
            ("pid reused", _prober("alive", "999"), "pid_start_mismatch"),
        ):
            with self.subTest(label):
                workspace = _Workspace(self)
                raw = _stale_lock(workspace)
                observed = observe_lock(workspace.root, _S, _F)
                lock, disposition = _takeover(workspace, observed, prober=prober)
                self.addCleanup(lock.release)
                self.assertEqual((disposition.action, disposition.basis), ("tombstoned", basis))
                self.assertEqual((disposition.owner_pid, disposition.owner_host), (4242, _HOST))
                payload = json.loads(lock.lock_path.read_text(encoding="utf-8"))
                self.assertEqual((payload["run_id"], payload["pid"]), (_NEW, os.getpid()))
                tombstone = lock.lock_path.parent / f"{_S}-{_F}.lock.stale-{_OLD}-{_NEW}"
                self.assertEqual(tombstone.read_bytes(), raw)
                self.assertFalse((lock.lock_path.parent / f"{_S}-{_F}.lock.takeover").exists())
                self.assertEqual(lock.run_id, _NEW)
                self.assertTrue(lock.held)

    def test_a_live_owner_is_never_taken_over_even_with_confirmation(self) -> None:
        for confirm in (False, True):
            with self.subTest(confirm=confirm):
                workspace = _Workspace(self)
                raw = _stale_lock(workspace)
                observed = observe_lock(workspace.root, _S, _F)
                with self.assertRaises(PersistError) as caught:
                    _takeover(workspace, observed, prober=_prober("alive", "100"), confirm_owner_dead=confirm)
                self.assertEqual(caught.exception.exit_code, EXIT_LOCKED)
                self.assertEqual(_lock_path(workspace).read_bytes(), raw)
                self.assertEqual(sorted(os.listdir(_lock_path(workspace).parent)), [_lock_path(workspace).name])

    def test_unprovable_owners_need_operator_confirmation(self) -> None:
        cases = {
            "legacy lock": dict(host=..., pid_start=...),
            "foreign host": dict(host="elsewhere"),
            "invalid pid": dict(pid=0),
        }
        for label, payload in cases.items():
            with self.subTest(label):
                workspace = _Workspace(self)
                raw = _stale_lock(workspace, **payload)
                observed = observe_lock(workspace.root, _S, _F)
                with self.assertRaises(PersistError) as caught:
                    _takeover(workspace, observed, prober=_prober("absent"))
                self.assertEqual(caught.exception.exit_code, EXIT_LOCKED)
                self.assertEqual(_lock_path(workspace).read_bytes(), raw)
                lock, disposition = _takeover(workspace, observed, prober=_prober("absent"), confirm_owner_dead=True)
                self.addCleanup(lock.release)
                self.assertEqual((disposition.action, disposition.basis), ("operator_confirmed", "operator_confirmed"))

    def test_unparsable_lock_needs_confirmation(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace)
        _lock_path(workspace).write_bytes(b"{torn")
        observed = observe_lock(workspace.root, _S, _F)
        with self.assertRaises(PersistError):
            _takeover(workspace, observed, prober=_prober("absent"))
        lock, disposition = _takeover(workspace, observed, prober=_prober("absent"), confirm_owner_dead=True)
        self.addCleanup(lock.release)
        self.assertEqual(disposition.action, "operator_confirmed")
        tombstone = lock.lock_path.parent / f"{_S}-{_F}.lock.stale-unreadable-{_NEW}"
        self.assertEqual(tombstone.read_bytes(), b"{torn")

    def test_unknown_probe_is_not_dead_and_confirmation_does_not_override_it(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace)
        observed = observe_lock(workspace.root, _S, _F)
        for confirm in (False, True):
            with self.assertRaises(PersistError):
                _takeover(workspace, observed, prober=_prober("unknown"), confirm_owner_dead=confirm)

    def test_delayed_contender_with_a_stale_verdict_cannot_rename_a_live_lock(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace)
        stale_view_for_b = observe_lock(workspace.root, _S, _F)
        a_lock, _ = takeover_stale_lock(
            workspace.root, _S, _F, _NEW, stale_view_for_b, local_host=_HOST, prober=_prober("absent")
        )
        self.addCleanup(a_lock.release)
        a_bytes = a_lock.lock_path.read_bytes()
        with self.assertRaises(PersistError) as caught:
            takeover_stale_lock(
                workspace.root, _S, _F, _OTHER, stale_view_for_b, local_host=_HOST, prober=_prober("absent")
            )
        self.assertEqual(caught.exception.exit_code, EXIT_LOCKED)
        self.assertEqual(a_lock.lock_path.read_bytes(), a_bytes)
        names = sorted(os.listdir(a_lock.lock_path.parent))
        self.assertEqual(names, sorted([a_lock.lock_path.name, f"{_S}-{_F}.lock.stale-{_OLD}-{_NEW}"]))

    def test_identity_recheck_inside_the_guard_catches_a_swapped_lock(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace)
        observed = observe_lock(workspace.root, _S, _F)
        swapped = _stale_lock(workspace, run_id=_OTHER, pid=9)
        with self.assertRaises(PersistError) as caught:
            _takeover(workspace, observed, prober=_prober("absent"))
        self.assertEqual(caught.exception.exit_code, EXIT_LOCKED)
        self.assertEqual(_lock_path(workspace).read_bytes(), swapped)

    def _flaky_guard_unlink(self, failures: int):
        real = os.unlink
        remaining = [failures]

        def flaky(path, *args, **kwargs):
            if str(path).endswith(".takeover") and remaining[0] != 0:
                remaining[0] -= 1
                raise PermissionError("sharing violation")
            return real(path, *args, **kwargs)

        return flaky

    def test_a_transient_sharing_violation_removing_the_guard_is_retried(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace)
        observed = observe_lock(workspace.root, _S, _F)
        with (
            mock.patch.object(persist.os, "unlink", self._flaky_guard_unlink(2)),
            mock.patch.object(persist.time, "sleep"),
        ):
            lock, _ = _takeover(workspace, observed, prober=_prober("absent"))
        self.addCleanup(lock.release)
        self.assertFalse(_lock_path(workspace).with_name(f"{_S}-{_F}.lock.takeover").exists())

    def test_a_guard_that_cannot_be_removed_is_named_in_a_warning(self) -> None:
        import contextlib
        import io

        workspace = _Workspace(self)
        _stale_lock(workspace)
        observed = observe_lock(workspace.root, _S, _F)
        guard = _lock_path(workspace).with_name(f"{_S}-{_F}.lock.takeover")
        stderr = io.StringIO()
        with (
            mock.patch.object(persist.os, "unlink", self._flaky_guard_unlink(-1)),
            mock.patch.object(persist.time, "sleep"),
            contextlib.redirect_stderr(stderr),
        ):
            lock, _ = _takeover(workspace, observed, prober=_prober("absent"))
        self.addCleanup(lock.release)
        self.assertIn(str(guard), stderr.getvalue())
        self.assertTrue(guard.exists())
        guard.unlink()

    def test_a_stale_guard_is_never_auto_cleared(self) -> None:
        workspace = _Workspace(self)
        raw = _stale_lock(workspace)
        guard = _lock_path(workspace).with_name(f"{_S}-{_F}.lock.takeover")
        guard.write_text("crashed", encoding="utf-8")
        observed = observe_lock(workspace.root, _S, _F)
        with self.assertRaises(PersistError) as caught:
            _takeover(workspace, observed, prober=_prober("absent"))
        self.assertEqual(caught.exception.exit_code, EXIT_LOCKED)
        self.assertEqual(guard.read_text(encoding="utf-8"), "crashed")
        self.assertEqual(_lock_path(workspace).read_bytes(), raw)

    def test_concurrent_takeovers_have_exactly_one_winner(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace)
        observed = observe_lock(workspace.root, _S, _F)
        barrier = threading.Barrier(2)
        results: list[object] = []

        def run(run_id: str) -> None:
            barrier.wait()
            try:
                results.append(
                    takeover_stale_lock(
                        workspace.root, _S, _F, run_id, observed, local_host=_HOST, prober=_prober("absent")
                    )
                )
            except PersistError as exc:
                results.append(exc)

        threads = [threading.Thread(target=run, args=(r,)) for r in (_NEW, _OTHER)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(15)
        winners = [r for r in results if isinstance(r, tuple)]
        losers = [r for r in results if isinstance(r, PersistError)]
        self.assertEqual((len(winners), len(losers)), (1, 1))
        self.assertEqual(losers[0].exit_code, EXIT_LOCKED)
        winners[0][0].release()

    def test_absent_lock_creates_one_with_an_absent_disposition(self) -> None:
        workspace = _Workspace(self)
        lock, disposition = _takeover(workspace, None, prober=_prober("absent"))
        self.addCleanup(lock.release)
        self.assertEqual((disposition.action, disposition.basis), ("absent", "lock_absent"))
        self.assertTrue(lock.lock_path.exists())

    def test_a_lock_that_vanished_or_appeared_since_observation_is_refused(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace)
        observed = observe_lock(workspace.root, _S, _F)
        _lock_path(workspace).unlink()
        with self.assertRaises(PersistError):
            _takeover(workspace, observed, prober=_prober("absent"))
        raw = _stale_lock(workspace)
        with self.assertRaises(PersistError):
            _takeover(workspace, None, prober=_prober("absent"))
        self.assertEqual(_lock_path(workspace).read_bytes(), raw)

    def test_an_existing_tombstone_is_never_overwritten(self) -> None:
        workspace = _Workspace(self)
        _stale_lock(workspace)
        tombstone = _lock_path(workspace).with_name(f"{_S}-{_F}.lock.stale-{_OLD}-{_NEW}")
        tombstone.write_text("keep", encoding="utf-8")
        observed = observe_lock(workspace.root, _S, _F)
        with self.assertRaises(PersistError):
            _takeover(workspace, observed, prober=_prober("absent"))
        self.assertEqual(tombstone.read_text(encoding="utf-8"), "keep")

    def test_a_free_acquirer_winning_after_the_rename_keeps_its_lock_and_the_tombstone_stays(self) -> None:
        workspace = _Workspace(self)
        raw = _stale_lock(workspace)
        observed = observe_lock(workspace.root, _S, _F)
        real = persist._create_lock_file

        def racing(path, payload):
            if str(path).endswith(".lock"):
                real(path, {**payload, "run_id": _OTHER})
            return real(path, payload)

        with mock.patch.object(persist, "_create_lock_file", side_effect=racing):
            with self.assertRaises(PersistError) as caught:
                _takeover(workspace, observed, prober=_prober("absent"))
        self.assertEqual(caught.exception.exit_code, EXIT_LOCKED)
        self.assertEqual(json.loads(_lock_path(workspace).read_text(encoding="utf-8"))["run_id"], _OTHER)
        self.assertEqual(_lock_path(workspace).with_name(f"{_S}-{_F}.lock.stale-{_OLD}-{_NEW}").read_bytes(), raw)
        self.assertFalse(_lock_path(workspace).with_name(f"{_S}-{_F}.lock.takeover").exists())

    def test_invalid_recovery_run_id_is_refused_before_anything_is_touched(self) -> None:
        workspace = _Workspace(self)
        raw = _stale_lock(workspace)
        observed = observe_lock(workspace.root, _S, _F)
        with self.assertRaises(PersistError) as caught:
            takeover_stale_lock(workspace.root, _S, _F, "nope", observed, local_host=_HOST, prober=_prober("absent"))
        self.assertEqual(caught.exception.exit_code, EXIT_INPUT)
        self.assertEqual(_lock_path(workspace).read_bytes(), raw)


def _invoking(run_id: str) -> dict:
    record = _cascade_pre_close(run_id)
    record["phase"] = "invoking"
    return record


def _recovered(run_id: str, supersedes: str, **recovery: object) -> dict:
    record = _record(cascade_record, phase="post_close", run_id=run_id)
    record["recovery"] = {"recovered": True, "supersedes_run_id": supersedes, "recovery_run_id": run_id, **recovery}
    return record


class RecoveryTransitionTest(unittest.TestCase):
    def _setup(self, existing: dict | None, lock_run: str = _NEW):
        workspace = _Workspace(self)
        lock = acquire_pair_lock(workspace.root, _S, _F, lock_run)
        self.addCleanup(lock.release)
        before = workspace.place(existing) if existing is not None else None
        return workspace, before

    def test_recovery_run_may_finalize_an_invoking_record_of_a_dead_run(self) -> None:
        workspace, _ = self._setup(_invoking(_OLD))
        record = _recovered(_NEW, _OLD)
        write_evidence_atomic(workspace.evidence, record, owner_run_id=_NEW, recover_from_run_id=_OLD)
        on_disk = json.loads(workspace.evidence.read_text(encoding="utf-8"))
        self.assertEqual((on_disk["phase"], on_disk["run_id"]), ("post_close", _NEW))
        # Terminal: nothing moves out of post_close afterwards.
        with self.assertRaises(CascadeEvidenceError):
            write_evidence_atomic(workspace.evidence, record, owner_run_id=_NEW, recover_from_run_id=_OLD)

    def test_recovery_transition_refusals(self) -> None:
        no_block = _record(cascade_record, phase="post_close", run_id=_NEW)
        not_recovered = _recovered(_NEW, _OLD)
        not_recovered["recovery"]["recovered"] = False
        cases = [
            ("no recovery block", _invoking(_OLD), no_block, _NEW, _OLD),
            ("recovered is false", _invoking(_OLD), not_recovered, _NEW, _OLD),
            ("supersedes names another run", _invoking(_OLD), _recovered(_NEW, _OTHER), _NEW, _OLD),
            ("recovery_run_id is not the owner", _invoking(_OLD), _recovered(_NEW, _OLD, recovery_run_id=_OTHER), _NEW, _OLD),
            ("expected prior run differs from disk", _invoking(_OTHER), _recovered(_NEW, _OLD), _NEW, _OLD),
            ("existing record is pre_close", _cascade_pre_close(_OLD), _recovered(_NEW, _OLD), _NEW, _OLD),
            ("existing record is post_close", _record(cascade_record, phase="post_close", run_id=_OLD),
             _recovered(_NEW, _OLD), _NEW, _OLD),
            ("record run_id is not the owner", _invoking(_OLD), _recovered(_OTHER, _OLD), _NEW, _OLD),
            ("no existing record", None, _recovered(_NEW, _OLD), _NEW, _OLD),
        ]
        for label, existing, record, owner, prior in cases:
            with self.subTest(label):
                workspace, before = self._setup(existing)
                with self.assertRaises(CascadeEvidenceError):
                    write_evidence_atomic(workspace.evidence, record, owner_run_id=owner, recover_from_run_id=prior)
                if before is None:
                    self.assertFalse(workspace.evidence.exists())
                else:
                    self.assertEqual(workspace.evidence.read_bytes(), before)

    def test_recovery_requires_the_pair_lock(self) -> None:
        workspace, before = self._setup(_invoking(_OLD), lock_run=_OTHER)
        with self.assertRaises(CascadeEvidenceError):
            write_evidence_atomic(
                workspace.evidence, _recovered(_NEW, _OLD), owner_run_id=_NEW, recover_from_run_id=_OLD
            )
        self.assertEqual(workspace.evidence.read_bytes(), before)

    def test_ordinary_writers_still_cannot_finalize_another_runs_invoking_record(self) -> None:
        workspace, before = self._setup(_invoking(_OLD))
        record = _record(cascade_record, phase="post_close", run_id=_NEW)
        with self.assertRaises(CascadeEvidenceError):
            write_evidence_atomic(workspace.evidence, record, owner_run_id=_NEW)
        self.assertEqual(workspace.evidence.read_bytes(), before)

    def test_only_one_special_transition_may_be_requested_at_a_time(self) -> None:
        workspace, before = self._setup(_invoking(_OLD))
        with self.assertRaises(CascadeEvidenceError):
            write_evidence_atomic(
                workspace.evidence,
                _recovered(_NEW, _OLD),
                owner_run_id=_NEW,
                recover_from_run_id=_OLD,
                takeover_from_run_id=_OLD,
            )
        self.assertEqual(workspace.evidence.read_bytes(), before)


class RollbackTransitionTest(unittest.TestCase):
    def _setup(self, existing: dict | None, lock_run: str):
        workspace = _Workspace(self)
        lock = acquire_pair_lock(workspace.root, _S, _F, lock_run)
        self.addCleanup(lock.release)
        before = workspace.place(existing) if existing is not None else None
        return workspace, lock, before

    def test_same_run_rollback_then_attached_takeover(self) -> None:
        workspace, lock, _ = self._setup(_invoking(_OLD), _OLD)
        proof = RollbackProof(never_started=True, child_started=False, original_run_id=_OLD)
        write_evidence_atomic(
            workspace.evidence, _cascade_pre_close(_OLD), owner_run_id=_OLD, rollback_proof=proof
        )
        self.assertEqual(json.loads(workspace.evidence.read_text(encoding="utf-8"))["phase"], "pre_close")
        lock.release()
        # An attached invocation now takes the pre_close record over normally.
        attached = acquire_pair_lock(workspace.root, _S, _F, _NEW)
        self.addCleanup(attached.release)
        handed = persist.check_existing_record(attached, mode=persist.MODE_MUTATING)
        restamped = copy.deepcopy(handed)
        restamped["run_id"] = _NEW
        write_evidence_atomic(
            workspace.evidence, restamped, owner_run_id=_NEW, takeover_from_run_id=handed["run_id"]
        )
        invoking = copy.deepcopy(restamped)
        invoking["phase"] = "invoking"
        write_evidence_atomic(workspace.evidence, invoking, owner_run_id=_NEW)
        self.assertEqual(json.loads(workspace.evidence.read_text(encoding="utf-8"))["phase"], "invoking")

    def test_recovery_owner_rollback_for_a_provably_dead_owner(self) -> None:
        workspace, _, _ = self._setup(_invoking(_OLD), _NEW)
        proof = RollbackProof(
            never_started=True, child_started=False, original_run_id=_OLD, owner_provably_dead=True
        )
        write_evidence_atomic(
            workspace.evidence, _cascade_pre_close(_NEW), owner_run_id=_NEW, rollback_proof=proof
        )
        on_disk = json.loads(workspace.evidence.read_text(encoding="utf-8"))
        self.assertEqual((on_disk["phase"], on_disk["run_id"]), ("pre_close", _NEW))
        self.assertNotIn("post_close", on_disk)

    def test_rollback_refusals(self) -> None:
        good = dict(never_started=True, child_started=False, original_run_id=_OLD, owner_provably_dead=True)
        with_invocation = _cascade_pre_close(_NEW)
        with_invocation["invocation"] = {"started_at": "2026-10-16T00:00:00Z"}
        cases = [
            ("no proof", None, _cascade_pre_close(_NEW), _invoking(_OLD), _NEW),
            ("never_started false", {**good, "never_started": False}, _cascade_pre_close(_NEW), _invoking(_OLD), _NEW),
            ("child started", {**good, "child_started": True}, _cascade_pre_close(_NEW), _invoking(_OLD), _NEW),
            ("proof names another run", {**good, "original_run_id": _OTHER}, _cascade_pre_close(_NEW),
             _invoking(_OLD), _NEW),
            ("recovery owner without dead-owner proof", {**good, "owner_provably_dead": False},
             _cascade_pre_close(_NEW), _invoking(_OLD), _NEW),
            ("new record carries an invocation", good, with_invocation, _invoking(_OLD), _NEW),
            ("new record is not pre_close", good, _invoking(_NEW), _invoking(_OLD), _NEW),
            ("existing record is pre_close", good, _cascade_pre_close(_NEW), _cascade_pre_close(_OLD), _NEW),
            ("existing record is post_close", good, _cascade_pre_close(_NEW),
             _record(cascade_record, phase="post_close", run_id=_OLD), _NEW),
            ("no existing record", good, _cascade_pre_close(_NEW), None, _NEW),
        ]
        for label, proof_args, record, existing, owner in cases:
            with self.subTest(label):
                workspace, _, before = self._setup(existing, owner)
                proof = RollbackProof(**proof_args) if proof_args is not None else None
                with self.assertRaises(CascadeEvidenceError):
                    write_evidence_atomic(workspace.evidence, record, owner_run_id=owner, rollback_proof=proof)
                if before is None:
                    self.assertFalse(workspace.evidence.exists())
                else:
                    self.assertEqual(workspace.evidence.read_bytes(), before)

    def test_without_proof_an_invoking_record_never_rolls_back(self) -> None:
        workspace, _, before = self._setup(_invoking(_OLD), _OLD)
        with self.assertRaises(CascadeEvidenceError):
            write_evidence_atomic(workspace.evidence, _cascade_pre_close(_OLD), owner_run_id=_OLD)
        self.assertEqual(workspace.evidence.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
