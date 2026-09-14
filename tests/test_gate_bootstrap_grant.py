"""Bootstrap-grant matching and containment tests for pipeline-topology."""

from __future__ import annotations

import json
import multiprocessing
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.gates.bootstrap_grant import (
    BootstrapGrantArgumentError,
    BootstrapGrantHooks,
    compute_manifest_digest,
    evaluate_bootstrap_grant,
    load_consumption_record,
    mark_consumption_record_consumed,
)
from autoharness.gates.topology import ShipmentState

_MATCHING_ITEMS = ('165.011-T', '165.012-T')
_MATCHING_MANIFEST_DIGEST = compute_manifest_digest(list(_MATCHING_ITEMS))
_MATCHING_PREDECESSOR_ID = '172-S'
_MATCHING_SHIPMENT_ID = '173-S'
_MATCHING_LABEL = 'ship_pre_claim'


def _shipment(
    shipment_id: str,
    status: str,
    *,
    manifest_items: tuple[str, ...] = (),
    predecessors: tuple[str, ...] = (),
) -> ShipmentState:
    return ShipmentState(
        shipment_id=shipment_id,
        title=shipment_id,
        live_status=status,
        manifest_item_ids=manifest_items,
        blocking_predecessor_ids=predecessors,
    )



def _matching_shipments() -> tuple[ShipmentState, ...]:
    return (
        _shipment(_MATCHING_PREDECESSOR_ID, 'active'),
        _shipment(
            _MATCHING_SHIPMENT_ID,
            'queued',
            manifest_items=_MATCHING_ITEMS,
            predecessors=(_MATCHING_PREDECESSOR_ID,),
        ),
    )



def _matching_payload(*, target: str = _MATCHING_SHIPMENT_ID, checks: list[dict] | None = None) -> dict:
    payload_checks = checks if checks is not None else [
        {
            'name': 'shipment_readiness',
            'status': 'blocked',
            'token': 'PREDECESSOR_NOT_SHIPPED',
            'message': (
                f'PREDECESSOR_NOT_SHIPPED: predecessor {_MATCHING_PREDECESSOR_ID} '
                'is not in a shipped terminal state'
            ),
            'details': {
                'target_shipment_id': target,
                'predecessor_id': _MATCHING_PREDECESSOR_ID,
                'predecessor_ids': [_MATCHING_PREDECESSOR_ID],
                'selected_predecessor_ids': [_MATCHING_PREDECESSOR_ID],
                'predecessor_source': 'explicit',
                'genesis_disqualifier': None,
                'genesis_disqualifying_records': [],
            },
        }
    ]
    return {
        'mode': 'agent',
        'phase': 'pre_claim',
        'target_shipment_id': target,
        'exit_code': 1,
        'blocked': True,
        'invalid': False,
        'message': payload_checks[0].get('message', 'topology gate blocked'),
        'checks': payload_checks,
        'token': payload_checks[0].get('token'),
        'forced': False,
    }



def _write_grant(
    workspace: Path,
    *,
    shipment_id: str = _MATCHING_SHIPMENT_ID,
    authorized_invocations: tuple[str, ...] = ('orchestrator_pre_route', 'ship_pre_branch', 'ship_pre_claim'),
    expected_token: str = 'PREDECESSOR_NOT_SHIPPED',
    expected_predecessor_id: str = _MATCHING_PREDECESSOR_ID,
    manifest_digest: str = _MATCHING_MANIFEST_DIGEST,
    authorizing_decision: str = 'D6',
    operator: str = 'Casey',
    expires_on_claim: bool = True,
    raw_text: str | None = None,
) -> Path:
    grant_path = workspace / '.autoharness' / 'bootstrap-grants' / f'{shipment_id}.yaml'
    grant_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_text is not None:
        grant_path.write_text(raw_text, encoding='utf-8')
        return grant_path
    lines = [
        'schema_version: 1',
        f'shipment_id: {shipment_id}',
        'authorized_invocations:',
        *[f'  - {label}' for label in authorized_invocations],
        f'expected_token: {expected_token}',
        f'expected_predecessor_id: {expected_predecessor_id}',
        f'manifest_digest: {manifest_digest}',
        f'authorizing_decision: {authorizing_decision}',
        f'operator: {operator}',
        f'expires_on_claim: {str(expires_on_claim).lower()}',
    ]
    grant_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return grant_path



def _concurrency_worker(workspace: str, queue: multiprocessing.Queue) -> None:
    result = evaluate_bootstrap_grant(
        workspace=Path(workspace),
        shipments=_matching_shipments(),
        observed_payload=_matching_payload(),
        invocation_label=_MATCHING_LABEL,
        actor='agent',
        session_id='session-1',
        head_sha='deadbeef',
    )
    queue.put(0 if result.applied else 1)


class BootstrapGrantTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self._tmp.cleanup)
        self.workspace = Path(self._tmp.name)

    def _evaluate(
        self,
        *,
        workspace: Path | None = None,
        shipments: tuple[ShipmentState, ...] | None = None,
        observed_payload: dict | None = None,
        invocation_label: str = _MATCHING_LABEL,
        hooks: BootstrapGrantHooks | None = None,
        head_sha: str = 'deadbeef',
    ):
        return evaluate_bootstrap_grant(
            workspace=workspace or self.workspace,
            shipments=shipments or _matching_shipments(),
            observed_payload=observed_payload or _matching_payload(),
            invocation_label=invocation_label,
            actor='agent',
            session_id='session-1',
            head_sha=head_sha,
            hooks=hooks,
        )

    def _record_path(self, *, label: str = _MATCHING_LABEL, workspace: Path | None = None) -> Path:
        root = workspace or self.workspace
        return root / '.autoharness' / 'gates' / 'bootstrap-grant-consumption' / _MATCHING_SHIPMENT_ID / f'{label}.json'

    def _read_record_bytes(self, *, label: str = _MATCHING_LABEL, workspace: Path | None = None) -> bytes:
        return self._record_path(label=label, workspace=workspace).read_bytes()

    def _read_record_json(self, *, label: str = _MATCHING_LABEL, workspace: Path | None = None) -> dict:
        return json.loads(self._record_path(label=label, workspace=workspace).read_text(encoding='utf-8'))

    def _make_junction(self, link: Path, target: Path) -> None:
        if os.name != 'nt':
            self.skipTest('NTFS junctions are a Windows-only filesystem feature')
        link.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            ['cmd', '/c', 'mklink', '/J', str(link), str(target)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            shell=False,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr or completed.stdout or 'mklink /J failed')

    def _symlink_supported(self, *, directory: bool) -> bool:
        probe_root = self.workspace / 'symlink-probe'
        probe_root.mkdir(parents=True, exist_ok=True)
        target = probe_root / ('target-dir' if directory else 'target-file')
        link = probe_root / ('link-dir' if directory else 'link-file')
        if directory:
            target.mkdir(exist_ok=True)
        else:
            target.write_text('probe', encoding='utf-8')
        try:
            os.symlink(target, link, target_is_directory=directory)
        except (NotImplementedError, OSError):
            return False
        else:
            try:
                if link.is_dir() and not link.is_symlink():
                    link.rmdir()
                else:
                    link.unlink()
            except OSError:
                pass
            return True

    def _make_symlink_or_skip(self, link: Path, target: Path, *, directory: bool) -> None:
        if not self._symlink_supported(directory=directory):
            self.skipTest('Windows symbolic links unavailable on this machine')
        link.parent.mkdir(parents=True, exist_ok=True)
        if directory:
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('outside', encoding='utf-8')
        os.symlink(target, link, target_is_directory=directory)

    def test_no_grant_path_creates_no_consumption_directory(self) -> None:
        result = self._evaluate()
        self.assertFalse(result.applied)
        self.assertEqual(result.warnings, ())
        self.assertFalse((self.workspace / '.autoharness' / 'gates').exists())

    def test_exact_match_claims_record_and_marks_consumed(self) -> None:
        _write_grant(self.workspace)
        result = self._evaluate()
        self.assertTrue(result.applied)
        self.assertEqual(result.warnings, ())
        self.assertIsNotNone(result.claim_record)
        assert result.claim_record is not None
        self.assertEqual(result.claim_record.status, 'claimed')
        mark_consumption_record_consumed(
            result.claim_record,
            {'path': '.autoharness/gates/pipeline-topology-force-audit.log', 'record_digest': 'abc123'},
        )
        record_data = self._read_record_json()
        self.assertEqual(record_data['status'], 'consumed')
        self.assertEqual(record_data['audit_ref']['path'], '.autoharness/gates/pipeline-topology-force-audit.log')
        self.assertEqual(record_data['grant_path'], '.autoharness/bootstrap-grants/173-S.yaml')
        self.assertEqual(record_data['manifest_digest'], _MATCHING_MANIFEST_DIGEST)
        self.assertEqual(record_data['manifest_items'], list(_MATCHING_ITEMS))

    def test_replay_fails_closed_and_leaves_record_unchanged(self) -> None:
        _write_grant(self.workspace)
        first = self._evaluate()
        assert first.claim_record is not None
        mark_consumption_record_consumed(
            first.claim_record,
            {'path': '.autoharness/gates/pipeline-topology-force-audit.log', 'record_digest': 'digest-1'},
        )
        before = self._read_record_bytes()
        second = self._evaluate()
        self.assertFalse(second.applied)
        self.assertTrue(any('already exists' in warning for warning in second.warnings))
        self.assertEqual(self._read_record_bytes(), before)

    def test_non_matching_grant_dimensions_do_not_burn_label(self) -> None:
        cases = (
            ('wrong_shipment', dict(shipment_id='999-S')),
            ('unlisted_invocation', dict(authorized_invocations=('ship_pre_branch',))),
            ('wrong_token', dict(expected_token='PRECLAIM_ACTIVE_SHIPMENT_PRESENT')),
            ('wrong_predecessor', dict(expected_predecessor_id='171-S')),
            ('stale_manifest', dict(manifest_digest=compute_manifest_digest(['165.999-T']))),
        )
        for name, kwargs in cases:
            with self.subTest(name=name):
                case_workspace = self.workspace / name
                _write_grant(case_workspace, **kwargs)
                result = self._evaluate(workspace=case_workspace)
                self.assertFalse(result.applied)
                self.assertFalse(self._record_path(workspace=case_workspace).exists())
                _write_grant(case_workspace)
                success = self._evaluate(workspace=case_workspace)
                self.assertTrue(success.applied)

    def test_second_blocking_check_does_not_burn_label(self) -> None:
        _write_grant(self.workspace)
        payload = _matching_payload(
            checks=[
                _matching_payload()['checks'][0],
                {
                    'name': 'active_shipment_invariant',
                    'status': 'blocked',
                    'token': 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT',
                    'message': 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT: pre-claim requires zero active shipments',
                    'details': {'active_shipment_ids': ['170-S']},
                },
            ]
        )
        result = self._evaluate(observed_payload=payload)
        self.assertFalse(result.applied)
        self.assertFalse(self._record_path().exists())
        success = self._evaluate()
        self.assertTrue(success.applied)

    def test_claim_fsyncs_containing_directory_for_durability(self) -> None:
        # Regression coverage for a prior bug where _claim_record_posix
        # fsynced only the newly-created claim file, not its containing
        # directory. POSIX does not guarantee a new directory entry is
        # durable from a file-level fsync alone; without a directory fsync
        # too, a crash between record creation and the next read could lose
        # the claim name and allow the same grant label to be consumed
        # again, contradicting the documented durable at-most-once contract.
        if not hasattr(os, 'O_NOFOLLOW'):
            self.skipTest('exercises the POSIX claim strategy (dir-fd O_NOFOLLOW walk)')
        _write_grant(self.workspace)
        real_fsync = os.fsync
        observed_modes: list[int] = []

        def _tracking_fsync(fd: int) -> None:
            try:
                observed_modes.append(os.fstat(fd).st_mode)
            except OSError:
                pass
            real_fsync(fd)

        with mock.patch('os.fsync', side_effect=_tracking_fsync):
            result = self._evaluate()

        self.assertTrue(result.applied)
        self.assertTrue(
            any(stat.S_ISREG(mode) for mode in observed_modes),
            'expected at least one fsync of the claim file itself',
        )
        self.assertTrue(
            any(stat.S_ISDIR(mode) for mode in observed_modes),
            'expected an fsync of the containing directory for durability of the new entry',
        )

    def test_scan_existing_records_posix_dir_fd_reads_via_descriptor_not_pathname(self) -> None:
        # Regression coverage for a prior bug where the POSIX claim path's
        # existing-record scan re-resolved shipment_dir by pathname after an
        # O_NOFOLLOW dir-fd walk had already verified it, discarding that
        # containment guarantee. This test proves the scan reads relative to
        # the supplied dir_fd rather than re-resolving the shipment_dir
        # argument: the real record lives under a directory opened as
        # dir_fd, while shipment_dir points at an unrelated, never-created
        # decoy path used only for message text.
        if not hasattr(os, 'O_NOFOLLOW'):
            self.skipTest('exercises the POSIX descriptor-relative scan')
        from autoharness.gates.bootstrap_grant import _scan_existing_records_posix_dir_fd

        real_dir = self.workspace / 'real-consumption-dir'
        real_dir.mkdir(parents=True)
        record_path = real_dir / f'{_MATCHING_LABEL}.json'
        payload = {
            'schema_version': 1,
            'grant_digest': 'a-different-digest',
            'grant_path': '.autoharness/bootstrap-grants/173-S.yaml',
            'shipment_id': _MATCHING_SHIPMENT_ID,
            'label': _MATCHING_LABEL,
            'phase': 'pre_claim',
            'actor': 'agent',
            'session_id': 'session-1',
            'head_sha': 'deadbeef',
            'manifest_digest': _MATCHING_MANIFEST_DIGEST,
            'manifest_items': list(_MATCHING_ITEMS),
            'blocking_token': 'PREDECESSOR_NOT_SHIPPED',
            'claimed_at': '2026-01-01T00:00:00+00:00',
            'status': 'claimed',
            'authorizing_decision': 'D6',
            'operator': 'Casey',
            'observed_payload': {},
        }
        record_path.write_text(json.dumps(payload), encoding='utf-8')

        decoy_shipment_dir = self.workspace / 'decoy-consumption-dir' / _MATCHING_SHIPMENT_ID
        self.assertFalse(decoy_shipment_dir.exists())

        dir_fd = os.open(str(real_dir), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            disqualifying, warnings = _scan_existing_records_posix_dir_fd(
                dir_fd,
                decoy_shipment_dir,
                workspace=self.workspace,
                grant_digest=_MATCHING_MANIFEST_DIGEST,
            )
        finally:
            os.close(dir_fd)

        self.assertTrue(disqualifying)
        self.assertTrue(any('different grant digest' in warning for warning in warnings))

    def test_multiple_selected_predecessors_refuse_grant_even_when_first_matches(self) -> None:
        # Regression coverage for a prior bug where evaluate_bootstrap_grant
        # matched only details['predecessor_id'] (the single predecessor
        # that caused the topology check's fail-fast loop to return) while
        # ignoring that details['selected_predecessor_ids'] can list several
        # predecessors the target actually declares. A grant scoped to the
        # first predecessor must not silently authorize bypassing the whole
        # blocked result when other declared predecessors were never
        # evaluated for completeness.
        _write_grant(self.workspace)
        matching_check = _matching_payload()['checks'][0]
        multi_predecessor_check = {
            **matching_check,
            'details': {
                **matching_check['details'],
                'predecessor_ids': [_MATCHING_PREDECESSOR_ID, '171-S'],
                'selected_predecessor_ids': [_MATCHING_PREDECESSOR_ID, '171-S'],
            },
        }
        payload = _matching_payload(checks=[multi_predecessor_check])

        result = self._evaluate(observed_payload=payload)

        self.assertFalse(result.applied)
        self.assertFalse(self._record_path().exists())
        joined = ' '.join(result.warnings)
        self.assertIn('multiple blocking predecessors', joined)
        # A single-predecessor payload with the identical grant still
        # applies -- proves the refusal is specific to the multi-predecessor
        # case, not a general regression of grant matching.
        success = self._evaluate()
        self.assertTrue(success.applied)

    def test_concurrency_allows_exactly_one_claim(self) -> None:
        _write_grant(self.workspace)
        ctx = multiprocessing.get_context('spawn')
        queue = ctx.Queue()
        processes = [ctx.Process(target=_concurrency_worker, args=(str(self.workspace), queue)) for _ in range(8)]
        try:
            for process in processes:
                process.start()
            results = [queue.get(timeout=60) for _ in processes]
            for process in processes:
                process.join(timeout=60)
                self.assertEqual(process.exitcode, 0)
            self.assertEqual(results.count(0), 1)
            self.assertEqual(results.count(1), 7)
            records = list((self.workspace / '.autoharness' / 'gates' / 'bootstrap-grant-consumption' / _MATCHING_SHIPMENT_ID).glob('*.json'))
            self.assertEqual(len(records), 1)
        finally:
            queue.close()
            queue.join_thread()
            for process in processes:
                process.close()

    def test_crash_after_claim_persists_claimed_record_and_rerun_fails_closed(self) -> None:
        _write_grant(self.workspace)

        def _raise_after_claim(_record):
            raise RuntimeError('boom after claim')

        with self.assertRaisesRegex(RuntimeError, 'boom after claim'):
            self._evaluate(hooks=BootstrapGrantHooks(after_claim_persisted=_raise_after_claim))
        record_data = self._read_record_json()
        self.assertEqual(record_data['status'], 'claimed')
        rerun = self._evaluate()
        self.assertFalse(rerun.applied)
        self.assertTrue(any('already exists' in warning for warning in rerun.warnings))

    def test_claimed_record_without_audit_remains_spent(self) -> None:
        _write_grant(self.workspace)
        result = self._evaluate()
        assert result.claim_record is not None
        self.assertEqual(self._read_record_json()['status'], 'claimed')
        rerun = self._evaluate()
        self.assertFalse(rerun.applied)
        self.assertTrue(any('already exists' in warning for warning in rerun.warnings))

    def test_grant_digest_mismatch_blocks_every_label(self) -> None:
        _write_grant(self.workspace)
        first = self._evaluate(invocation_label='ship_pre_branch')
        self.assertTrue(first.applied)
        _write_grant(self.workspace, operator='Alex')
        second = self._evaluate(invocation_label='ship_pre_claim')
        self.assertFalse(second.applied)
        self.assertTrue(any('different grant digest' in warning for warning in second.warnings))

    def test_malformed_records_fail_closed_and_are_not_overwritten(self) -> None:
        _write_grant(self.workspace)
        cases = {
            'truncated': b'{',
            'unknown_schema': json.dumps({'schema_version': 2}).encode('utf-8'),
            'missing_field': json.dumps({'schema_version': 1, 'shipment_id': _MATCHING_SHIPMENT_ID}).encode('utf-8'),
            'path_mismatch': json.dumps(
                {
                    'schema_version': 1,
                    'grant_digest': 'abc',
                    'grant_path': '.autoharness/bootstrap-grants/173-S.yaml',
                    'shipment_id': _MATCHING_SHIPMENT_ID,
                    'label': 'ship_pre_branch',
                    'phase': 'pre_claim',
                    'actor': 'agent',
                    'session_id': 'session-1',
                    'head_sha': 'deadbeef',
                    'manifest_digest': _MATCHING_MANIFEST_DIGEST,
                    'manifest_items': list(_MATCHING_ITEMS),
                    'blocking_token': 'PREDECESSOR_NOT_SHIPPED',
                    'inferred_predecessor_id': _MATCHING_PREDECESSOR_ID,
                    'claimed_at': '2026-09-14T00:00:00+00:00',
                    'status': 'claimed',
                    'audit_ref': None,
                    'authorizing_decision': 'D6',
                    'operator': 'Casey',
                    'observed_payload': _matching_payload(),
                }
            ).encode('utf-8'),
        }
        for name, raw in cases.items():
            with self.subTest(name=name):
                case_workspace = self.workspace / name
                _write_grant(case_workspace)
                record_path = self._record_path(workspace=case_workspace)
                record_path.parent.mkdir(parents=True, exist_ok=True)
                record_path.write_bytes(raw)
                before = record_path.read_bytes()
                result = self._evaluate(workspace=case_workspace)
                self.assertFalse(result.applied)
                self.assertTrue(any('malformed' in warning or 'unsupported' in warning for warning in result.warnings))
                self.assertEqual(record_path.read_bytes(), before)

    def test_stale_record_has_no_auto_expiry(self) -> None:
        _write_grant(self.workspace)
        record_path = self._record_path()
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(
            json.dumps(
                {
                    'schema_version': 1,
                    'grant_digest': 'abc',
                    'grant_path': '.autoharness/bootstrap-grants/173-S.yaml',
                    'shipment_id': _MATCHING_SHIPMENT_ID,
                    'label': _MATCHING_LABEL,
                    'phase': 'pre_claim',
                    'actor': 'agent',
                    'session_id': 'session-1',
                    'head_sha': 'deadbeef',
                    'manifest_digest': _MATCHING_MANIFEST_DIGEST,
                    'manifest_items': list(_MATCHING_ITEMS),
                    'blocking_token': 'PREDECESSOR_NOT_SHIPPED',
                    'inferred_predecessor_id': _MATCHING_PREDECESSOR_ID,
                    'claimed_at': '2001-01-01T00:00:00+00:00',
                    'status': 'claimed',
                    'audit_ref': None,
                    'authorizing_decision': 'D6',
                    'operator': 'Casey',
                    'observed_payload': _matching_payload(),
                }
            ),
            encoding='utf-8',
        )
        result = self._evaluate()
        self.assertFalse(result.applied)

    def test_syntactically_unsafe_inputs_raise_before_filesystem_access(self) -> None:
        _write_grant(self.workspace)
        invalid_targets = ('..\\173-S', '../173-S', 'C:\\outside', '\\\\server\\share', '173-S\x00bad')
        for target in invalid_targets:
            with self.subTest(target=target):
                payload = _matching_payload(target=target)
                with mock.patch('autoharness.gates.bootstrap_grant.Path.resolve', side_effect=AssertionError('resolve called')):
                    with mock.patch('autoharness.gates.bootstrap_grant.os.lstat', side_effect=AssertionError('lstat called')):
                        with self.assertRaises(BootstrapGrantArgumentError):
                            self._evaluate(observed_payload=payload)
        with mock.patch('autoharness.gates.bootstrap_grant.Path.resolve', side_effect=AssertionError('resolve called')):
            with mock.patch('autoharness.gates.bootstrap_grant.os.lstat', side_effect=AssertionError('lstat called')):
                with self.assertRaises(BootstrapGrantArgumentError):
                    self._evaluate(invocation_label='..\\ship_pre_claim')

    def test_root_escape_rejected_for_junction_variants_and_does_not_burn_label(self) -> None:
        for relative in (
            Path('.autoharness'),
            Path('.autoharness') / 'gates',
            Path('.autoharness') / 'gates' / 'bootstrap-grant-consumption',
        ):
            with self.subTest(relative=str(relative)):
                case_workspace = self.workspace / relative.name.replace('.', 'root')
                outside = case_workspace / 'outside'
                link_path = case_workspace / relative
                self._make_junction(link_path, outside)
                _write_grant(case_workspace)
                result = self._evaluate(workspace=case_workspace)
                self.assertFalse(result.applied)
                self.assertTrue(result.warnings)
                self.assertFalse(any(outside.rglob('*.json')))
                link_path.rmdir()
                _write_grant(case_workspace)
                success = self._evaluate(workspace=case_workspace)
                self.assertTrue(success.applied)

    def test_root_escape_rejected_for_directory_symlink_variants(self) -> None:
        for relative in (
            Path('.autoharness'),
            Path('.autoharness') / 'gates',
            Path('.autoharness') / 'gates' / 'bootstrap-grant-consumption',
        ):
            with self.subTest(relative=str(relative)):
                case_workspace = self.workspace / ('symlink-' + relative.name.replace('.', 'root'))
                outside = case_workspace / 'outside'
                link_path = case_workspace / relative
                self._make_symlink_or_skip(link_path, outside, directory=True)
                _write_grant(case_workspace)
                result = self._evaluate(workspace=case_workspace)
                self.assertFalse(result.applied)
                self.assertTrue(result.warnings)
                self.assertFalse(any(outside.rglob('*.json')))

    def test_intermediate_component_link_rejected_for_junction_and_symlink(self) -> None:
        for link_type in ('junction', 'symlink'):
            with self.subTest(link_type=link_type):
                case_workspace = self.workspace / link_type
                outside = case_workspace / 'outside'
                link_path = case_workspace / '.autoharness' / 'gates' / 'bootstrap-grant-consumption' / _MATCHING_SHIPMENT_ID
                if link_type == 'junction':
                    self._make_junction(link_path, outside)
                else:
                    self._make_symlink_or_skip(link_path, outside, directory=True)
                _write_grant(case_workspace)
                result = self._evaluate(workspace=case_workspace)
                self.assertFalse(result.applied)
                self.assertFalse(any(outside.rglob('*.json')))

    def test_final_name_link_rejected_and_target_unmodified(self) -> None:
        for link_type in ('junction', 'symlink'):
            with self.subTest(link_type=link_type):
                case_workspace = self.workspace / f'final-{link_type}'
                outside_root = case_workspace / 'outside'
                target = outside_root / 'target-file.txt'
                logical_path = self._record_path(workspace=case_workspace)
                logical_path.parent.mkdir(parents=True, exist_ok=True)
                if link_type == 'junction':
                    self._make_junction(logical_path, outside_root / 'dir-target')
                else:
                    self._make_symlink_or_skip(logical_path, target, directory=False)
                _write_grant(case_workspace)
                before = target.read_text(encoding='utf-8') if target.exists() else None
                result = self._evaluate(workspace=case_workspace)
                self.assertFalse(result.applied)
                if target.exists():
                    self.assertEqual(target.read_text(encoding='utf-8'), before)

    def test_toctou_swap_hook_fails_closed_without_writing_outside_root(self) -> None:
        _write_grant(self.workspace)
        outside = self.workspace / 'outside'
        shipment_dir = self.workspace / '.autoharness' / 'gates' / 'bootstrap-grant-consumption' / _MATCHING_SHIPMENT_ID

        def _swap(_workspace: Path) -> None:
            shipment_dir.parent.mkdir(parents=True, exist_ok=True)
            self._make_junction(shipment_dir, outside)

        result = self._evaluate(hooks=BootstrapGrantHooks(before_claim_validation=_swap))
        self.assertFalse(result.applied)
        self.assertFalse(any(outside.rglob('*.json')))

    def test_windows_identity_mismatch_fails_closed_and_leaves_created_file(self) -> None:
        if os.name != 'nt':
            self.skipTest(
                'exercises _post_create_identity_error, which is only reached by the '
                'Windows-only claim strategy (_claim_record_posix uses O_NOFOLLOW+dir_fd '
                'containment instead and never calls it)'
            )
        _write_grant(self.workspace)
        with mock.patch('autoharness.gates.bootstrap_grant._post_create_identity_error', return_value='identity mismatch'):
            result = self._evaluate()
        self.assertFalse(result.applied)
        self.assertTrue(self._record_path().exists())
        self.assertTrue(any('failed identity verification' in warning for warning in result.warnings))

    def test_windows_open_directory_handle_raises_oserror_not_attributeerror_on_failure(self) -> None:
        if os.name != 'nt':
            self.skipTest(
                'exercises _windows_open_directory_handle, which uses CreateFileW/'
                'GetFileInformationByHandle -- Windows-only ctypes APIs'
            )
        from autoharness.gates.bootstrap_grant import _windows_open_directory_handle

        # CreateFileW must genuinely fail here (nonexistent path) so the
        # code reaches ctypes.get_last_error(). Regression coverage for a
        # prior bug where this line called the nonexistent os.get_last_error(),
        # which raised AttributeError instead of a clean OSError.
        missing_path = self.workspace / 'does-not-exist' / 'still-missing'
        with self.assertRaises(OSError) as ctx:
            _windows_open_directory_handle(missing_path)
        self.assertIsInstance(ctx.exception.errno, int)
        self.assertIn('CreateFileW failed', str(ctx.exception))

    def test_load_bootstrap_grant_rejects_symlinked_grant_file(self) -> None:
        # Regression coverage for a prior bug where load_bootstrap_grant()
        # read the grant file by pathname with no symlink verification at
        # all, so a symlinked grant file could make the process read and
        # parse arbitrary content from outside the workspace. The external
        # target below is deliberately invalid YAML: if the fix regresses
        # and the read follows the symlink, yaml.safe_load will run against
        # it and the warning text will say "invalid" (parser error) rather
        # than "unreadable" (open refused).
        from autoharness.gates.bootstrap_grant import load_bootstrap_grant

        grant_path = self.workspace / '.autoharness' / 'bootstrap-grants' / f'{_MATCHING_SHIPMENT_ID}.yaml'
        outside_target = self.workspace / 'outside-grant.yaml'
        outside_target.write_text('not: [valid, yaml', encoding='utf-8')
        self._make_symlink_or_skip(grant_path, outside_target, directory=False)

        grant, warnings = load_bootstrap_grant(self.workspace, _MATCHING_SHIPMENT_ID)

        self.assertIsNone(grant)
        self.assertTrue(warnings)
        joined = ' '.join(warnings)
        self.assertIn('unreadable', joined)
        self.assertNotIn('invalid', joined)

    def test_scan_existing_records_rejects_symlinked_record_file_on_posix(self) -> None:
        # Regression coverage for a prior bug where _scan_existing_records
        # only checked _is_reparse_point() (Windows-only; always False on
        # POSIX) before handing a consumption-record path to
        # _read_consumption_record(), so a symlinked .json record could
        # make the audit scan read arbitrary content from outside the
        # workspace. The external target below is deliberately invalid
        # JSON: if the fix regresses and the read follows the symlink,
        # json.loads will run against it and the warning text will say
        # "invalid JSON" rather than "unreadable".
        if not hasattr(os, 'O_NOFOLLOW'):
            self.skipTest('exercises the POSIX O_NOFOLLOW no-follow read path')
        from autoharness.gates.bootstrap_grant import _scan_existing_records

        record_path = self._record_path()
        outside_target = self.workspace / 'outside-record.json'
        outside_target.write_text('{not valid json', encoding='utf-8')
        self._make_symlink_or_skip(record_path, outside_target, directory=False)

        disqualifying, warnings = _scan_existing_records(
            record_path.parent,
            workspace=self.workspace,
            grant_digest=_MATCHING_MANIFEST_DIGEST,
        )

        self.assertTrue(disqualifying)
        self.assertTrue(warnings)
        joined = ' '.join(warnings)
        self.assertIn('unreadable', joined)
        self.assertNotIn('invalid JSON', joined)

    def test_capability_gate_refuses_plain_fallback(self) -> None:
        _write_grant(self.workspace)
        with mock.patch('autoharness.gates.bootstrap_grant._supports_posix_claim_strategy', return_value=False):
            with mock.patch('autoharness.gates.bootstrap_grant._supports_windows_claim_strategy', return_value=False):
                result = self._evaluate()
        self.assertFalse(result.applied)
        self.assertTrue(any('refusing to fall back' in warning for warning in result.warnings))
        self.assertFalse(self._record_path().exists())
        source = (Path(__file__).resolve().parents[1] / 'src' / 'autoharness' / 'gates' / 'bootstrap_grant.py').read_text(encoding='utf-8')
        self.assertNotIn('--reset-consumption', source)
        self.assertIn('refusing to fall back', source)

    def test_happy_path_creates_exactly_one_record(self) -> None:
        _write_grant(self.workspace)
        result = self._evaluate()
        self.assertTrue(result.applied)
        records = list(self._record_path().parent.glob('*.json'))
        self.assertEqual([record.name for record in records], [f'{_MATCHING_LABEL}.json'])
        if os.name != 'nt':
            self.assertEqual(self._record_path().stat().st_mode & 0o777, 0o600)

    def test_no_silent_reuse_or_reset_surface_by_source_and_behavior(self) -> None:
        _write_grant(self.workspace)
        first = self._evaluate()
        assert first.claim_record is not None
        mark_consumption_record_consumed(first.claim_record, {'path': 'audit.log', 'record_digest': 'digest'})
        before = self._read_record_bytes()
        second = self._evaluate()
        self.assertFalse(second.applied)
        self.assertEqual(self._read_record_bytes(), before)
        source = (Path(__file__).resolve().parents[1] / 'src' / 'autoharness' / 'gates' / 'bootstrap_grant.py').read_text(encoding='utf-8')
        self.assertNotIn('os.remove(record.path', source)
        self.assertNotIn('os.unlink(record.path', source)
        cli_source = (Path(__file__).resolve().parents[1] / 'src' / 'autoharness' / 'cli.py').read_text(encoding='utf-8')
        self.assertNotIn('--reset-consumption', cli_source)
        self.assertNotIn('--force-consume', cli_source)

    def test_load_consumption_record_round_trips(self) -> None:
        _write_grant(self.workspace)
        result = self._evaluate()
        assert result.claim_record is not None
        loaded = load_consumption_record(self._record_path(), workspace=self.workspace)
        self.assertEqual(loaded.grant_path, '.autoharness/bootstrap-grants/173-S.yaml')
        self.assertEqual(loaded.shipment_id, _MATCHING_SHIPMENT_ID)
        self.assertEqual(loaded.label, _MATCHING_LABEL)


if __name__ == '__main__':
    unittest.main()
