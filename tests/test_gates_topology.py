"""Deterministic tests for the pipeline-topology gate core."""

from __future__ import annotations

from contextlib import contextmanager
import ast
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from _env_patch import patched_environ
from autoharness.cli import _format_dag_readiness_report
from autoharness.gates.topology import (
    ArtifactState,
    BacklogUnavailableError,
    FilesystemTopologyReaders,
    ShipmentState,
    TopologyInput,
    _active_invariant_check,
    _run_git,
    _shipment_readiness_check,
    audit_sequencing,
    compute_dag_readiness,
    compute_next_eligible,
    evaluate,
)
from support.red import expect_red


class _FakeReaders:
    def __init__(
        self,
        shipments=(),
        artifacts=None,
        branch='main',
        default_branch='main',
        worktrees=None,
        worktree_markers=None,
        git_errors=None,
    ):
        if shipments and isinstance(shipments[0], (list, tuple)):
            self._snapshots = [tuple(snapshot) for snapshot in shipments]
        else:
            self._snapshots = [tuple(shipments)]
        self._artifacts = dict(artifacts or {})
        self._branch = branch
        self._default_branch = default_branch
        self._worktrees = worktrees or (
            'worktree C:/repo\n'
            'HEAD 0000000000000000000000000000000000000000\n'
            f'branch refs/heads/{branch}\n\n'
        )
        self._worktree_markers = dict(worktree_markers or {})
        # A3R: simulated captured git-invocation-failure state, keyed by
        # call-site name ("current_branch" / "default_branch" /
        # "worktree_porcelain"). Empty by default so every pre-existing
        # `_FakeReaders`-based test is completely unaffected (this reader
        # never exposed `git_invocation_error` before; now it exposes it but
        # it always returns `None` unless a test explicitly opts in).
        self._git_errors = dict(git_errors or {})
        self._calls = 0

    def list_shipments(self):
        index = min(self._calls, len(self._snapshots) - 1)
        self._calls += 1
        return self._snapshots[index]

    def read_artifact(self, artifact_id: str):
        return self._artifacts.get(artifact_id)

    def current_branch(self) -> str:
        return self._branch

    def default_branch(self) -> str:
        return self._default_branch

    def worktree_porcelain(self) -> str:
        return self._worktrees

    def read_worktree_marker(self, worktree_path: str):
        return self._worktree_markers.get(worktree_path)

    def git_invocation_error(self, name: str):
        return self._git_errors.get(name)

    def closure_complete(self, shipment_id: str):
        return None


def _shipment(
    shipment_id: str,
    status: str,
    *items: str,
    title: str | None = None,
    archived_status: str | None = None,
    archived_record_present: bool | None = None,
    deps=(),
) -> ShipmentState:
    return ShipmentState(
        shipment_id=shipment_id,
        title=title or shipment_id,
        live_status=status,
        archived_status=archived_status,
        archived_record_present=archived_record_present if archived_record_present is not None else archived_status is not None,
        manifest_item_ids=tuple(items),
        blocking_predecessor_ids=tuple(deps),
    )


def _check(result, name: str):
    for check in result.checks:
        if check.name == name:
            return check
    raise AssertionError(f'missing check: {name}')


def _task(task_id: str, status: str) -> ArtifactState:
    return ArtifactState(artifact_id=task_id, artifact_type='task', live_status=status)


_TOPOLOGY_UNSET = object()


class _FixtureFilesystemReaders(FilesystemTopologyReaders):
    def __init__(
        self,
        workspace: Path,
        *,
        closure=None,
        branch: str = 'main',
        default_branch: str = 'main',
        worktrees: str | None = None,
    ) -> None:
        super().__init__(workspace)
        self._closure = dict(closure or {})
        self._branch = branch
        self._default_branch = default_branch
        self._worktrees = worktrees or (
            'worktree C:/repo\n'
            'HEAD 0000000000000000000000000000000000000000\n'
            f'branch refs/heads/{branch}\n\n'
        )

    def current_branch(self) -> str:
        return self._branch

    def default_branch(self) -> str:
        return self._default_branch

    def worktree_porcelain(self) -> str:
        return self._worktrees

    def read_worktree_marker(self, worktree_path: str):
        return None

    def closure_complete(self, shipment_id: str):
        return self._closure.get(shipment_id)


class _TopologyWorkspaceMixin:
    @contextmanager
    def _topology_workspace(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as tmp:
            workspace = Path(tmp)
            (workspace / '.backlogit' / 'queue').mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            yield workspace

    def _write_shipment_record(
        self,
        workspace: Path,
        shipment_id: str | object,
        *,
        folder: str = 'queue',
        filename: str | None = None,
        title: str | object = _TOPOLOGY_UNSET,
        status: object = _TOPOLOGY_UNSET,
        archived_status: object = _TOPOLOGY_UNSET,
        dependencies: object = _TOPOLOGY_UNSET,
        labels: object = _TOPOLOGY_UNSET,
        artifact_type: str = 'shipment',
        extra_fields: dict[str, object] | None = None,
    ) -> Path:
        payload: dict[str, object] = {'artifact_type': artifact_type}
        if shipment_id is not _TOPOLOGY_UNSET:
            payload['id'] = shipment_id
        if title is not _TOPOLOGY_UNSET:
            payload['title'] = title
        if status is not _TOPOLOGY_UNSET:
            payload['status'] = status
        if archived_status is not _TOPOLOGY_UNSET:
            payload['archived_status'] = archived_status
        if dependencies is not _TOPOLOGY_UNSET:
            payload['dependencies'] = dependencies
        if labels is not _TOPOLOGY_UNSET:
            payload['labels'] = labels
        if extra_fields:
            payload.update(extra_fields)
        record_name = filename
        if record_name is None:
            record_name = shipment_id.strip() if isinstance(shipment_id, str) and shipment_id.strip() else 'shipment-record'
        record_path = workspace / '.backlogit' / folder / f'{record_name}.md'
        body = yaml.safe_dump(payload, sort_keys=False).strip()
        record_path.write_text(f'---\n{body}\n---\n', encoding='utf-8')
        return record_path

    def _reader(self, workspace: Path, *, closure=None) -> _FixtureFilesystemReaders:
        return _FixtureFilesystemReaders(workspace, closure=closure)

    def _list_shipments(self, workspace: Path) -> tuple[ShipmentState, ...]:
        return tuple(self._reader(workspace).list_shipments())

    def _shipment_from_workspace(self, workspace: Path, shipment_id: str) -> ShipmentState:
        for shipment in self._list_shipments(workspace):
            if shipment.shipment_id == shipment_id:
                return shipment
        raise AssertionError(f'missing shipment record: {shipment_id}')

    def _evaluate_workspace(self, workspace: Path, target: str, *, closure=None, phase: str = 'pre_claim'):
        return evaluate(TopologyInput(mode='agent', phase=phase, target_shipment_id=target), readers=self._reader(workspace, closure=closure))

    def _expect_equal(self, label: str, actual, expected) -> None:
        if actual != expected:
            raise AssertionError(f'expected {label}={expected!r}, got {actual!r}')

    def _expect_contains(self, label: str, container: str, member: str) -> None:
        if member not in container:
            raise AssertionError(f'expected {label} to contain {member!r}, got {container!r}')

    def _expect_backlog_unavailable(self, func, *, description: str) -> None:
        try:
            func()
        except BacklogUnavailableError:
            return
        raise AssertionError(f'expected BacklogUnavailableError for {description}')

    def _readiness_check(self, result):
        return _check(result, 'shipment_readiness')

    def _assert_predecessor_source(self, check, expected: str) -> None:
        self._expect_equal('predecessor_source', check.details.get('predecessor_source'), expected)

    def _assert_predecessor_ids(self, check, expected) -> None:
        self._expect_equal('predecessor_ids', tuple(check.details.get('predecessor_ids', ())), tuple(expected))

    def _assert_readiness_pass(self, result, *, source: str, predecessor_ids=()) -> None:
        self._expect_equal('result.exit_code', result.exit_code, 0)
        check = self._readiness_check(result)
        self._expect_equal('shipment_readiness.status', check.status, 'passed')
        self._assert_predecessor_source(check, source)
        self._assert_predecessor_ids(check, predecessor_ids)

    def _assert_explicit_block(self, result, *, predecessor_id: str) -> None:
        self._expect_equal('result.exit_code', result.exit_code, 1)
        check = self._readiness_check(result)
        self._expect_equal('shipment_readiness.status', check.status, 'blocked')
        self._expect_equal('shipment_readiness.token', check.token, 'PREDECESSOR_NOT_SHIPPED')
        self._expect_equal('shipment_readiness.predecessor_id', check.details.get('predecessor_id'), predecessor_id)
        self._assert_predecessor_source(check, 'explicit')

    def _assert_unsequenced_block(self, result, *, target: str) -> None:
        self._expect_equal('result.exit_code', result.exit_code, 1)
        check = self._readiness_check(result)
        self._expect_equal('shipment_readiness.status', check.status, 'blocked')
        self._expect_equal('shipment_readiness.token', check.token, 'UNSEQUENCED_SHIPMENT')
        self._expect_equal('shipment_readiness.target_shipment_id', check.details.get('target_shipment_id'), target)
        self._assert_predecessor_source(check, 'unsequenced')
        self._assert_predecessor_ids(check, ())
        self._expect_contains('shipment_readiness.message', check.message, 'blocks')
        self._expect_contains('shipment_readiness.message', check.message, 'root')

    def _assert_shipment_labels(self, shipment: ShipmentState, expected) -> None:
        self._expect_equal('ShipmentState.labels', getattr(shipment, 'labels', None), tuple(expected))


class FilesystemTopologyReadersTests(unittest.TestCase):
    def test_missing_backlog_dir_blocks_in_agent_and_ci_modes(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            reader = FilesystemTopologyReaders(workspace)
            cases = (
                ('agent', 'pre_claim', '114-S'),
                ('ci', None, None),
            )
            for mode, phase, target in cases:
                with self.subTest(mode=mode):
                    result = evaluate(
                        TopologyInput(mode=mode, phase=phase, target_shipment_id=target),
                        readers=reader,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_empty_queue_and_archive_dirs_pass_as_zero_shipments(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as tmp:
            workspace = Path(tmp)
            (workspace / '.backlogit' / 'queue').mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir(parents=True)
            reader = FilesystemTopologyReaders(workspace)

            self.assertEqual(tuple(reader.list_shipments()), ())
            result = evaluate(
                TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                readers=reader,
            )
            self.assertEqual(result.exit_code, 0)

    def test_missing_queue_or_archive_dir_blocks(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        for missing_folder in ('queue', 'archive'):
            with self.subTest(missing_folder=missing_folder):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    backlog_dir = workspace / '.backlogit'
                    backlog_dir.mkdir(parents=True)
                    (backlog_dir / ('archive' if missing_folder == 'queue' else 'queue')).mkdir()
                    reader = FilesystemTopologyReaders(workspace)

                    result = evaluate(
                        TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                        readers=reader,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_closure_complete_accepts_done_or_degraded_only(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            closure_dir = workspace / 'docs' / 'closure'
            closure_dir.mkdir(parents=True)
            cases = (
                ('done', True),
                ('degraded', True),
                ('ready', False),
                ('pending', False),
            )
            for status, expected in cases:
                with self.subTest(status=status):
                    for existing in closure_dir.glob('*.md'):
                        existing.unlink()
                    (closure_dir / '114-S-2026-08-05-post-merge-closure.md').write_text(
                        f"---\ncompaction_status: {status}\nclosure_status: READY\n---\n",
                        encoding='utf-8',
                    )
                    reader = FilesystemTopologyReaders(workspace)
                    self.assertIs(reader.closure_complete('114-S'), expected)

    def test_closure_complete_enforces_closure_status_and_conditions(self) -> None:
        # 109.023-T (114-S closure pre-activation fix, Defect 3):
        # closure_complete() must require BOTH a passing compaction_status
        # AND closure_status==READY (or a fully-verified conditions block
        # for READY_WITH_CONDITIONS) -- compaction_status alone is never
        # sufficient. Mandatory negative + positive cases below.
        from autoharness.gates.topology import FilesystemTopologyReaders

        def _write(workspace: Path, closure_dir: Path, body: str) -> None:
            for existing in closure_dir.glob('*.md'):
                existing.unlink()
            (closure_dir / '114-S-2026-08-05-post-merge-closure.md').write_text(body, encoding='utf-8')

        satisfied_conditions = (
            "conditions:\n"
            "  - id: fix-one\n"
            "    satisfied: true\n"
            "    evidence: '115-S/109.021-T'\n"
        )
        unsatisfied_conditions = (
            "conditions:\n"
            "  - id: fix-one\n"
            "    satisfied: false\n"
            "    evidence: '115-S/109.021-T'\n"
        )
        evidence_less_conditions = (
            "conditions:\n"
            "  - id: fix-one\n"
            "    satisfied: true\n"
        )
        cases = (
            ("BLOCKED closure_status", "closure_status: BLOCKED\n", False),
            ("missing closure_status", "", False),
            (
                "READY_WITH_CONDITIONS without conditions block",
                "closure_status: READY_WITH_CONDITIONS\n",
                False,
            ),
            (
                "READY_WITH_CONDITIONS with unverified condition",
                "closure_status: READY_WITH_CONDITIONS\n" + unsatisfied_conditions,
                False,
            ),
            (
                "READY_WITH_CONDITIONS with evidence-less condition",
                "closure_status: READY_WITH_CONDITIONS\n" + evidence_less_conditions,
                False,
            ),
            ("READY closure_status", "closure_status: READY\n", True),
            (
                "READY_WITH_CONDITIONS with fully-verified conditions",
                "closure_status: READY_WITH_CONDITIONS\n" + satisfied_conditions,
                True,
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            closure_dir = workspace / 'docs' / 'closure'
            closure_dir.mkdir(parents=True)
            reader = FilesystemTopologyReaders(workspace)
            for label, extra_frontmatter, expected in cases:
                with self.subTest(label=label):
                    body = f"---\ncompaction_status: done\n{extra_frontmatter}---\n"
                    _write(workspace, closure_dir, body)
                    self.assertIs(reader.closure_complete('114-S'), expected)

    def test_closure_complete_malformed_frontmatter_raises_backlog_unavailable(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            closure_dir = workspace / 'docs' / 'closure'
            closure_dir.mkdir(parents=True)
            (closure_dir / '114-S-2026-08-05-post-merge-closure.md').write_text(
                "---\ncompaction_status: [unterminated\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            with self.assertRaises(BacklogUnavailableError):
                reader.closure_complete('114-S')

    def test_malformed_shipment_frontmatter_blocks_as_backlog_unavailable(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        cases = {
            'invalid_yaml': "---\nid: [unterminated\n---\n",
            'missing_delimiter': "id: 114-S\nartifact_type: shipment\n",
            'non_mapping_body': "---\n- just\n- a\n- list\n---\n",
        }
        for label, content in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '114-S.md').write_text(content, encoding='utf-8')
                    reader = FilesystemTopologyReaders(workspace)

                    with self.assertRaises(Exception):
                        reader.list_shipments()

                    result = evaluate(
                        TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                        readers=reader,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_shipment_shaped_record_with_missing_or_wrong_artifact_type_blocks(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        cases = {
            'missing_artifact_type_by_filename': ("114-S.md", "---\nid: 114-S\nstatus: active\n---\n"),
            'misspelled_artifact_type_by_filename': ("114-S.md", "---\nid: 114-S\nartifact_type: shpiment\nstatus: active\n---\n"),
            'missing_artifact_type_by_declared_id': ("weird-name.md", "---\nid: 114-S\nstatus: active\n---\n"),
        }
        for label, (filename, content) in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / filename).write_text(content, encoding='utf-8')
                    reader = FilesystemTopologyReaders(workspace)

                    with self.assertRaises(Exception):
                        reader.list_shipments()

                    result = evaluate(
                        TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                        readers=reader,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_non_shipment_shaped_record_without_artifact_type_is_skipped(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            # A task/feature-shaped record (not shipment-shaped) with no
            # artifact_type is a different concern (validated separately via
            # read_artifact) and must not block the shipment scan itself.
            (queue / '109.001-T.md').write_text("---\nid: 109.001-T\nstatus: queued\n---\n", encoding='utf-8')
            reader = FilesystemTopologyReaders(workspace)
            self.assertEqual(tuple(reader.list_shipments()), ())

    def test_malformed_task_frontmatter_blocks_via_detect_before_consistency(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            (queue / '114-S.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n"
                "custom_fields:\n  items:\n  - 109.001-T\n---\n",
                encoding='utf-8',
            )
            # Malformed task artifact frontmatter: valid delimiters but invalid YAML body.
            (queue / '109.001-T.md').write_text("---\nstatus: [unterminated\n---\n", encoding='utf-8')
            reader = FilesystemTopologyReaders(workspace)

            result = evaluate(
                TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                readers=reader,
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_shipment_record_with_missing_or_blank_id_blocks(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        cases = {
            'missing_id': "---\nartifact_type: shipment\nstatus: queued\n---\n",
            'blank_id': "---\nid: '  '\nartifact_type: shipment\nstatus: queued\n---\n",
        }
        for label, content in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '114-S.md').write_text(content, encoding='utf-8')
                    reader = FilesystemTopologyReaders(workspace)

                    with self.assertRaises(Exception):
                        reader.list_shipments()

                    result = evaluate(
                        TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                        readers=reader,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_queue_shipment_with_missing_or_unsupported_status_blocks(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        cases = {
            'missing_status': "---\nid: 114-S\nartifact_type: shipment\n---\n",
            'blank_status': "---\nid: 114-S\nartifact_type: shipment\nstatus: '  '\n---\n",
            'unsupported_status': "---\nid: 114-S\nartifact_type: shipment\nstatus: blocked\n---\n",
        }
        for label, content in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '114-S.md').write_text(content, encoding='utf-8')
                    reader = FilesystemTopologyReaders(workspace)

                    with self.assertRaises(Exception):
                        reader.list_shipments()

                    result = evaluate(
                        TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                        readers=reader,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_queue_shipment_with_supported_status_passes(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        for status in ('queued', 'active', 'shipped', 'abandoned'):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '114-S.md').write_text(
                        f"---\nid: 114-S\nartifact_type: shipment\nstatus: {status}\n---\n",
                        encoding='utf-8',
                    )
                    reader = FilesystemTopologyReaders(workspace)
                    shipments = reader.list_shipments()
                    self.assertEqual(len(shipments), 1)
                    self.assertEqual(shipments[0].live_status, status)

    def test_archived_record_present_tracked_independently_of_archived_status_content(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            archive = workspace / '.backlogit' / 'archive'
            queue.mkdir(parents=True)
            archive.mkdir(parents=True)
            (queue / '113-S.md').write_text(
                "---\nid: 113-S\nartifact_type: shipment\nstatus: shipped\n---\n",
                encoding='utf-8',
            )
            # A malformed/generic archive duplicate that carries no readable
            # archived_status field must still be tracked as an archive-file
            # presence, not collapsed to "no archive record".
            (archive / '113-S.md').write_text(
                "---\nid: 113-S\nartifact_type: shipment\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            shipments = reader.list_shipments()
            self.assertEqual(len(shipments), 1)
            self.assertIsNone(shipments[0].archived_status)
            self.assertTrue(shipments[0].archived_record_present)

            from autoharness.gates.topology import _has_ambiguous_shipment_records

            self.assertTrue(_has_ambiguous_shipment_records(shipments[0]))

    def test_queue_task_with_missing_or_unsupported_status_blocks_via_read_artifact(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        cases = {
            'missing_status': "---\nid: 109.001-T\nartifact_type: task\n---\n",
            'blank_status': "---\nid: 109.001-T\nartifact_type: task\nstatus: '  '\n---\n",
            'unsupported_status': "---\nid: 109.001-T\nartifact_type: task\nstatus: not-a-real-status\n---\n",
        }
        for label, content in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '109.001-T.md').write_text(content, encoding='utf-8')
                    reader = FilesystemTopologyReaders(workspace)

                    with self.assertRaises(Exception):
                        reader.read_artifact('109.001-T')

    def test_queue_task_with_supported_status_reads_correctly(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        for status in ('queued', 'active', 'blocked', 'review', 'done', 'accepted', 'rejected', 'archived'):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '109.001-T.md').write_text(
                        f"---\nid: 109.001-T\nartifact_type: task\nstatus: {status}\n---\n",
                        encoding='utf-8',
                    )
                    reader = FilesystemTopologyReaders(workspace)
                    artifact = reader.read_artifact('109.001-T')
                    self.assertIsNotNone(artifact)
                    self.assertEqual(artifact.live_status, status)

    def test_archive_only_task_has_no_live_status_requirement(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / '.backlogit' / 'queue').mkdir(parents=True)
            archive = workspace / '.backlogit' / 'archive'
            archive.mkdir(parents=True)
            (archive / '109.001-T.md').write_text(
                "---\nid: 109.001-T\nartifact_type: task\narchived_status: done\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            artifact = reader.read_artifact('109.001-T')
            self.assertIsNotNone(artifact)
            self.assertIsNone(artifact.live_status)
            self.assertEqual(artifact.archived_status, 'done')

    def test_malformed_queue_task_status_blocks_via_detect_before_consistency(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            (queue / '114-S.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n"
                "custom_fields:\n  items:\n  - 109.001-T\n---\n",
                encoding='utf-8',
            )
            # Syntactically valid task frontmatter with an unsupported status
            # value must not be silently normalized away by the
            # detect-before-consistency scan.
            (queue / '109.001-T.md').write_text(
                "---\nid: 109.001-T\nartifact_type: task\nstatus: not-a-real-status\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)

            result = evaluate(
                TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                readers=reader,
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_malformed_artifact_id_shape_blocks_before_glob(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        malformed_ids = (
            '../../etc/passwd',
            '/etc/passwd',
            '109.001-T/../../secret',
            '109.001-T*',
            '109.001-T[',
            '',
            '   ',
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / '.backlogit' / 'queue').mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir(parents=True)
            reader = FilesystemTopologyReaders(workspace)
            for artifact_id in malformed_ids:
                with self.subTest(artifact_id=artifact_id):
                    # A malformed id must fail closed via the gate's own
                    # exception type -- never an unhandled low-level
                    # pathlib/glob exception (e.g. ValueError for an
                    # absolute-looking pattern) and never a silent None
                    # that masks the artifact as merely "not found".
                    with self.assertRaises(BacklogUnavailableError):
                        reader.read_artifact(artifact_id)

    def test_valid_artifact_id_shapes_are_not_blocked_by_shape_check(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        for artifact_id in ('114-S', '109-F', '109.001-T'):
            with self.subTest(artifact_id=artifact_id):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    (workspace / '.backlogit' / 'queue').mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir(parents=True)
                    reader = FilesystemTopologyReaders(workspace)
                    # No record on disk for these ids; the shape check must
                    # pass and fall through to a normal "not found" result
                    # rather than raising.
                    self.assertIsNone(reader.read_artifact(artifact_id))

    def test_duplicate_queue_shipment_record_blocks(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            # Two distinct files in the SAME (queue) folder both declaring
            # the same shipment id. Sort-order-dependent field overwrites
            # (e.g. a "queued" first file silently overwritten by an
            # "active" second file, or vice versa) must never be merged
            # silently -- this must fail closed instead.
            (queue / '114-s-a.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\nstatus: active\n---\n",
                encoding='utf-8',
            )
            (queue / '114-s-b.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            with self.assertRaises(BacklogUnavailableError):
                reader.list_shipments()

    def test_duplicate_archive_shipment_record_blocks(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / '.backlogit' / 'queue').mkdir(parents=True)
            archive = workspace / '.backlogit' / 'archive'
            archive.mkdir()
            # Two distinct files in the SAME (archive) folder both declaring
            # the same shipment id must also fail closed.
            (archive / '114-s-a.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\narchived_status: shipped\n---\n",
                encoding='utf-8',
            )
            (archive / '114-s-b.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\narchived_status: abandoned\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            with self.assertRaises(BacklogUnavailableError):
                reader.list_shipments()

    def test_single_live_and_archive_pair_for_same_id_is_not_a_duplicate(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            archive = workspace / '.backlogit' / 'archive'
            archive.mkdir()
            # One queue record and one archive record for the same id is a
            # legitimate (non-duplicate) predecessor-ambiguity case handled
            # elsewhere -- it must not trip the same-folder duplicate check.
            (queue / '113-S.md').write_text(
                "---\nid: 113-S\nartifact_type: shipment\nstatus: queued\n---\n",
                encoding='utf-8',
            )
            (archive / '113-S.md').write_text(
                "---\nid: 113-S\nartifact_type: shipment\narchived_status: shipped\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            shipments = reader.list_shipments()
            self.assertEqual(len(shipments), 1)
            self.assertTrue(shipments[0].archived_record_present)

    def test_dependencies_present_but_not_a_sequence_blocks(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        cases = {
            'bare_string': "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\ndependencies: 100-S\n---\n",
            'mapping': "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\ndependencies:\n  a: 100-S\n---\n",
            'integer': "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\ndependencies: 42\n---\n",
        }
        for label, content in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '114-S.md').write_text(content, encoding='utf-8')
                    reader = FilesystemTopologyReaders(workspace)
                    # A present-but-wrong-shaped `dependencies` field (e.g. a
                    # bare string) must never be silently coerced to "no
                    # predecessors": that drops a real blocking predecessor
                    # and can falsely unlock a dependent successor.
                    with self.assertRaises(BacklogUnavailableError):
                        reader.list_shipments()

    def test_custom_fields_items_present_but_not_a_sequence_blocks(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        cases = {
            'bare_string': (
                "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n"
                "custom_fields:\n  items: 109.001-T\n---\n"
            ),
            'integer': (
                "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n"
                "custom_fields:\n  items: 42\n---\n"
            ),
        }
        for label, content in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '114-S.md').write_text(content, encoding='utf-8')
                    reader = FilesystemTopologyReaders(workspace)
                    # A present-but-wrong-shaped `custom_fields.items` field
                    # must never be silently coerced to "no manifest items":
                    # that hides active/done tasks from the
                    # detect-before-consistency scan.
                    with self.assertRaises(BacklogUnavailableError):
                        reader.list_shipments()

    def test_custom_fields_present_but_not_a_mapping_blocks(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            (queue / '114-S.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\ncustom_fields: not-a-mapping\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            with self.assertRaises(BacklogUnavailableError):
                reader.list_shipments()

    def test_missing_dependencies_and_custom_fields_default_to_empty(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            (queue / '114-S.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            shipments = reader.list_shipments()
            self.assertEqual(len(shipments), 1)
            self.assertEqual(shipments[0].manifest_item_ids, ())
            self.assertEqual(shipments[0].blocking_predecessor_ids, ())

    def test_valid_dependencies_and_custom_fields_items_still_resolve(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            (queue / '114-S.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n"
                "dependencies:\n  - 113-S\ncustom_fields:\n  items:\n  - 109.001-T\n  - 109.002-T\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            shipments = reader.list_shipments()
            self.assertEqual(len(shipments), 1)
            self.assertEqual(shipments[0].manifest_item_ids, ('109.001-T', '109.002-T'))
            self.assertEqual(shipments[0].blocking_predecessor_ids, ('113-S',))

    def test_dependencies_member_with_path_traversal_or_glob_metachars_blocks(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        cases = {
            'path_traversal': "dependencies:\n  - ../../outside\n",
            'absolute_path': "dependencies:\n  - /etc/passwd\n",
            'glob_metachar': "dependencies:\n  - 113-S*\n",
            'lowercase_suffix': "dependencies:\n  - 113-s\n",
            'blank_member': "dependencies:\n  - '  '\n",
            'non_string_member': "dependencies:\n  - 42\n",
        }
        for label, deps_yaml in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '114-S.md').write_text(
                        f"---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n{deps_yaml}---\n",
                        encoding='utf-8',
                    )
                    reader = FilesystemTopologyReaders(workspace)
                    # A malformed dependency member must never be silently
                    # stringified/dropped into `blocking_predecessor_ids`:
                    # it could later be interpolated into
                    # `closure_complete()`'s filesystem glob and traverse
                    # outside the intended backlog directory, or silently
                    # vanish from the readiness scan.
                    with self.assertRaises(BacklogUnavailableError):
                        reader.list_shipments()

    def test_custom_fields_items_member_with_invalid_shape_blocks(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        cases = {
            'path_traversal': "custom_fields:\n  items:\n  - ../../outside-T\n",
            'blank_member': "custom_fields:\n  items:\n  - '  '\n",
            'non_string_member': "custom_fields:\n  items:\n  - 42\n",
        }
        for label, items_yaml in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '114-S.md').write_text(
                        f"---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n{items_yaml}---\n",
                        encoding='utf-8',
                    )
                    reader = FilesystemTopologyReaders(workspace)
                    with self.assertRaises(BacklogUnavailableError):
                        reader.list_shipments()

    def test_shipment_typed_record_with_non_shipment_shaped_id_blocks(self) -> None:
        from autoharness.gates.topology import BacklogUnavailableError, FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            # Correctly typed (`artifact_type: shipment`) but the declared
            # id does not match the module's own shipment id shape
            # (digits + "-S"). Must fail closed rather than being admitted
            # as a legitimate shipment (e.g. becoming the sole active
            # ambient target).
            (queue / 'not-a-shipment.md').write_text(
                "---\nid: not-a-shipment\nartifact_type: shipment\nstatus: active\n---\n",
                encoding='utf-8',
            )
            reader = FilesystemTopologyReaders(workspace)
            with self.assertRaises(BacklogUnavailableError):
                reader.list_shipments()

    def test_read_worktree_marker_reads_repo_local_marker(self) -> None: 
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            worktree = workspace / 'spike-research'
            marker_dir = worktree / '.autoharness'
            marker_dir.mkdir(parents=True)
            marker = marker_dir / 'stage-worktree-marker.yaml'
            marker.write_text('role: spike-research\nexpires_at: "2999-01-01T00:00:00Z"\n', encoding='utf-8')
            reader = FilesystemTopologyReaders(workspace)
            self.assertEqual(reader.read_worktree_marker(str(worktree)), marker.read_text(encoding='utf-8'))
            self.assertIsNone(reader.read_worktree_marker(str(worktree / 'missing')))


class ActiveInvariantTests(unittest.TestCase):
    def test_phase_matrix(self) -> None:
        cases = (
            ('pre_claim', (), None, 'passed', None),
            ('pre_claim', (_shipment('114-S', 'active'),), '114-S', 'blocked', 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT'),
            ('pre_claim', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 'blocked', 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT'),
            ('post_claim', (), '114-S', 'blocked', 'LIFECYCLE_NO_ACTIVE_SHIPMENT'),
            ('post_claim', (_shipment('114-S', 'active'),), '114-S', 'passed', None),
            ('post_claim', (_shipment('115-S', 'active'),), '114-S', 'blocked', 'LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH'),
            ('post_claim', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 'blocked', 'LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS'),
            ('lifecycle', (), '114-S', 'blocked', 'LIFECYCLE_NO_ACTIVE_SHIPMENT'),
            ('lifecycle', (_shipment('114-S', 'active'),), '114-S', 'passed', None),
            ('lifecycle', (_shipment('115-S', 'active'),), '114-S', 'blocked', 'LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH'),
            ('lifecycle', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 'blocked', 'LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS'),
            ('ambient', (), None, 'passed', None),
            ('ambient', (_shipment('114-S', 'active'),), '114-S', 'passed', None),
            ('ambient', (_shipment('115-S', 'active'),), '114-S', 'blocked', 'AMBIENT_ACTIVE_SHIPMENT_MISMATCH'),
            ('ambient', (_shipment('115-S', 'active'),), None, 'blocked', 'AMBIENT_TARGET_REQUIRED_FOR_ACTIVE_SHIPMENT'),
            ('ambient', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 'blocked', 'AMBIENT_MULTIPLE_ACTIVE_SHIPMENTS'),
        )
        for phase, shipments, target, status, token in cases:
            with self.subTest(phase=phase, shipments=[s.shipment_id for s in shipments], target=target):
                check = _active_invariant_check(phase, target, shipments)
                self.assertEqual(check.status, status)
                self.assertEqual(check.token, token)

    def test_ambient_zero_active_differs_from_lifecycle(self) -> None:
        ambient = _active_invariant_check('ambient', None, ())
        lifecycle = _active_invariant_check('lifecycle', '114-S', ())
        self.assertEqual(ambient.status, 'passed')
        self.assertEqual(lifecycle.token, 'LIFECYCLE_NO_ACTIVE_SHIPMENT')


class DetectBeforeConsistencyTests(unittest.TestCase):
    def test_detect_before_runs_before_active_invariant(self) -> None:
        readers = _FakeReaders(
            shipments=(
                _shipment('114-S', 'queued', '109.002-T', '109-F'),
                _shipment('115-S', 'active'),
            ),
            artifacts={
                '109.002-T': _task('109.002-T', 'done'),
                '109-F': ArtifactState(artifact_id='109-F', artifact_type='feature', live_status='active'),
            },
        )
        result = evaluate(
            TopologyInput(mode='manual', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.primary_token, 'SHIPMENT_STATE_INCONSISTENT')
        self.assertIn('109.002-T', result.message)


if __name__ == '__main__':
    unittest.main()


def _clear_ambient_github_head_ref() -> None:
    """Clear any ambient ``GITHUB_HEAD_REF`` value before wrapping it with
    ``patched_environ()``.

    GitHub Actions sets ``GITHUB_HEAD_REF`` to the empty string (present,
    not absent) on ``push``-triggered CI runs -- as opposed to
    ``pull_request``-triggered runs, where it is genuinely set to the PR's
    source branch name, or a bare local shell, where it is typically unset
    entirely. ``patched_environ()``'s A5 entry-guard (144.002-T, BINDING)
    deliberately fails closed rather than attempt an unsafe empty-string
    restore for any key whose CURRENT ambient value is already ``""`` --
    see ``tests/_env_patch.py``. Tests that manage ``GITHUB_HEAD_REF`` via
    ``patched_environ()`` must therefore first ensure any ambient value is
    fully cleared, exactly the same established convention already used
    elsewhere in this file for the identical root cause (commit
    ``8c4c35ad``, for ``GITHUB_EVENT_PATH``/``GITHUB_HEAD_REF`` leakage from
    a live ``pull_request``-triggered CI run).
    """
    import os as _os

    _os.environ.pop('GITHUB_HEAD_REF', None)


class BranchOwnershipTests(unittest.TestCase):
    def test_matching_target_branch_passes(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'),),
            branch='feat/114-s',
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'branch_ownership').token, 'BRANCH_OK')

    def test_default_branch_is_create_eligible(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='main')
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'branch_ownership').token, 'BRANCH_CREATE_ELIGIBLE')

    def test_post_merge_closure_branch_passes_for_lifecycle_phase(self) -> None:
        """Regression test for code-review finding: post-merge closure branches
        (`post-merge/{feature_slug}`) are named after the covering FEATURE, not
        the shipment, so shipment-branch alias matching can never succeed for
        them. The Ship agent's mandatory closure lifecycle gate call runs while
        checked out on exactly this branch shape -- it must not be rejected as
        BRANCH_MISMATCH."""
        readers = _FakeReaders(
            shipments=(_shipment('115-S', 'active'),),
            branch='post-merge/109-f-topology-gate-b',
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='lifecycle', target_shipment_id='115-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            _check(result, 'branch_ownership').token, 'BRANCH_POST_MERGE_CLOSURE_ELIGIBLE'
        )

    def test_post_merge_closure_branch_passes_for_ambient_and_pre_claim(self) -> None:
        """The same post-merge branch pass-through also unblocks: (a) ambient
        hook invocations (pre-commit/pre-push) made from a post-merge closure
        branch while the shipment being closed is still active, and (b) the
        Orchestrator's cursor-advance pre_claim eligibility check for the next
        shipment, which can run before the checkout has returned to the
        default branch."""
        readers_ambient = _FakeReaders(
            shipments=(_shipment('115-S', 'active'),),
            branch='post-merge/109-f-topology-gate-b',
        )
        ambient_result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=readers_ambient,
        )
        self.assertEqual(ambient_result.exit_code, 0)
        self.assertEqual(
            _check(ambient_result, 'branch_ownership').token, 'BRANCH_POST_MERGE_CLOSURE_ELIGIBLE'
        )

        readers_pre_claim = _FakeReaders(
            shipments=(_shipment('116-S', 'queued'),),
            branch='post-merge/109-f-topology-gate-b',
        )
        pre_claim_result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='116-S'),
            readers=readers_pre_claim,
        )
        self.assertEqual(pre_claim_result.exit_code, 0)
        self.assertEqual(
            _check(pre_claim_result, 'branch_ownership').token,
            'BRANCH_POST_MERGE_CLOSURE_ELIGIBLE',
        )

    def test_detached_head_blocks(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='')
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 1)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_MISMATCH')
        self.assertTrue(check.details['detached_head'])

    def test_ci_mode_detached_head_resolves_via_github_head_ref(self) -> None:
        """Regression test (116-S live-CI finding): `actions/checkout` always
        leaves a `pull_request`-triggered run in detached HEAD, so
        `git branch --show-current` reports empty even though the PR's real
        source branch is known via `GITHUB_HEAD_REF`. `--mode ci` must resolve
        the branch from this CI-platform environment variable rather than
        fail-closed on every single PR run -- that would make the CI
        topology-check entrypoint (Gate C) permanently non-functional for its
        stated purpose."""
        readers = _FakeReaders(shipments=(_shipment('116-S', 'active'),), branch='')
        _clear_ambient_github_head_ref()
        with patched_environ(
            GITHUB_HEAD_REF='feat/116-s-topology-gate-c-remote-ci-validation-backstop',
        ):
            result = evaluate(
                TopologyInput(mode='ci', phase='ambient', target_shipment_id=None),
                readers=readers,
            )
        self.assertEqual(result.exit_code, 0)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_OK')
        self.assertTrue(check.details['resolved_via_ci_env_fallback'])

    def test_ci_mode_detached_head_resolves_via_github_ref_name_for_push(self) -> None:
        """`push`-triggered CI runs have no `GITHUB_HEAD_REF` (that variable is
        `pull_request`-only); the pushed branch name is `GITHUB_REF_NAME`
        instead (e.g. `main` for a push to the default branch), disambiguated
        from a tag push via `GITHUB_REF_TYPE == 'branch'`."""
        readers = _FakeReaders(shipments=(_shipment('116-S', 'active'),), branch='', default_branch='main')
        _clear_ambient_github_head_ref()
        with patched_environ(
            GITHUB_REF_NAME='main', GITHUB_REF_TYPE='branch', GITHUB_HEAD_REF=None,
        ):
            result = evaluate(
                TopologyInput(mode='ci', phase='ambient', target_shipment_id=None),
                readers=readers,
            )
        self.assertEqual(result.exit_code, 0)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_CREATE_ELIGIBLE')
        self.assertTrue(check.details['resolved_via_ci_env_fallback'])

    def test_ci_mode_push_branch_name_with_slash_is_accepted(self) -> None:
        """Regression test for code-review finding: a naive `'/' in ref_name`
        heuristic would misclassify a legitimate slash-containing
        push-triggered branch name (this repo's own `feat/…`/`chore/…`
        convention) as a non-branch merge-ref and fail closed. Disambiguation
        must use `GITHUB_REF_TYPE`, not a substring check on the name."""
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='')
        _clear_ambient_github_head_ref()
        with patched_environ(
            GITHUB_REF_NAME='feat/114-s',
            GITHUB_REF_TYPE='branch',
            GITHUB_HEAD_REF=None,
        ):
            result = evaluate(
                TopologyInput(mode='ci', phase='pre_claim', target_shipment_id='114-S'),
                readers=readers,
            )
        self.assertEqual(result.exit_code, 0)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_OK')
        self.assertTrue(check.details['resolved_via_ci_env_fallback'])

    def test_ci_mode_tag_push_does_not_resolve_as_branch(self) -> None:
        """A tag-triggered `push` event sets `GITHUB_REF_TYPE == 'tag'` and
        `GITHUB_REF_NAME` to a version string, not a branch. This must NOT be
        accepted as a resolved branch name -- the gate keeps failing closed
        (detached HEAD, unresolvable) rather than treating a tag as ownership
        evidence."""
        readers = _FakeReaders(shipments=(_shipment('116-S', 'active'),), branch='')
        _clear_ambient_github_head_ref()
        with patched_environ(
            GITHUB_REF_NAME='v1.2.3', GITHUB_REF_TYPE='tag', GITHUB_HEAD_REF=None,
        ):
            result = evaluate(
                TopologyInput(mode='ci', phase='ambient', target_shipment_id=None),
                readers=readers,
            )
        self.assertEqual(result.exit_code, 1)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_MISMATCH')
        self.assertTrue(check.details['detached_head'])
        self.assertFalse(check.details['resolved_via_ci_env_fallback'])

    def test_ci_mode_detached_head_with_no_env_fallback_still_blocks(self) -> None:
        """Fail-closed is preserved when neither CI environment variable
        resolves a usable branch name (e.g. a CI platform this fallback does
        not recognize, or genuinely malformed environment)."""
        readers = _FakeReaders(shipments=(_shipment('116-S', 'active'),), branch='')
        _clear_ambient_github_head_ref()
        with patched_environ(
            GITHUB_HEAD_REF=None, GITHUB_REF_NAME=None, GITHUB_REF_TYPE=None,
        ):
            result = evaluate(
                TopologyInput(mode='ci', phase='ambient', target_shipment_id=None),
                readers=readers,
            )
        self.assertEqual(result.exit_code, 1)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_MISMATCH')
        self.assertTrue(check.details['detached_head'])
        self.assertFalse(check.details['resolved_via_ci_env_fallback'])

    def test_non_ci_mode_detached_head_ignores_github_env_fallback(self) -> None:
        """The CI-env fallback is gated on `mode == 'ci'` only: `agent`/`manual`
        mode detached-HEAD checkouts must keep failing closed exactly as
        before even if a `GITHUB_HEAD_REF`-shaped variable happens to be set
        in the environment (e.g. a local shell that inherited it)."""
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='')
        _clear_ambient_github_head_ref()
        with patched_environ(GITHUB_HEAD_REF='feat/114-s'):
            result = evaluate(
                TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
                readers=readers,
            )
        self.assertEqual(result.exit_code, 1)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_MISMATCH')
        self.assertTrue(check.details['detached_head'])

    def test_ci_mode_default_branch_resolves_via_github_event_path(self) -> None:
        """Regression test (Copilot review finding on PR #302,
        PRRT_kwDORzpWpM6WzWf9): `FilesystemTopologyReaders.default_branch()`
        resolves from `refs/remotes/origin/HEAD`, falling back to a
        hard-coded `main` when that symref is unset -- which
        `actions/checkout` never sets (shallow, single-ref fetch, no
        `git remote set-head`). For a repository whose real default branch is
        `master`, a push to `master` while a shipment is active must still
        resolve `BRANCH_CREATE_ELIGIBLE`, using the platform-authoritative
        `repository.default_branch` field from the `GITHUB_EVENT_PATH` event
        payload rather than the incorrect hard-coded `main` fallback."""
        readers = _FakeReaders(
            shipments=(_shipment('116-S', 'active'),),
            branch='',
            default_branch='main',  # simulates the git-based main-fallback bug
        )
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / 'event.json'
            event_path.write_text('{"repository": {"default_branch": "master"}}', encoding='utf-8')
            _clear_ambient_github_head_ref()
            with patched_environ(
                GITHUB_REF_NAME='master',
                GITHUB_REF_TYPE='branch',
                GITHUB_EVENT_PATH=str(event_path),
                GITHUB_HEAD_REF=None,
            ):
                result = evaluate(
                    TopologyInput(mode='ci', phase='ambient', target_shipment_id=None),
                    readers=readers,
                )
        self.assertEqual(result.exit_code, 0)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_CREATE_ELIGIBLE')
        self.assertEqual(check.details['default_branch'], 'master')
        self.assertTrue(check.details['default_branch_resolved_via_ci_env_fallback'])

    def test_ci_mode_default_branch_fallback_missing_event_path_uses_reader_value(self) -> None:
        """When `GITHUB_EVENT_PATH` is unset, unreadable, or lacks a usable
        `repository.default_branch`, the gate preserves the existing
        git-based `default_branch()` resolution (including its `main`
        fallback) rather than raising or fabricating a value."""
        readers = _FakeReaders(
            shipments=(_shipment('116-S', 'active'),),
            branch='main',
            default_branch='main',
        )
        _clear_ambient_github_head_ref()
        with patched_environ(GITHUB_EVENT_PATH=None, GITHUB_HEAD_REF=None):
            result = evaluate(
                TopologyInput(mode='ci', phase='ambient', target_shipment_id=None),
                readers=readers,
            )
        self.assertEqual(result.exit_code, 0)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_CREATE_ELIGIBLE')
        self.assertEqual(check.details['default_branch'], 'main')
        self.assertFalse(check.details['default_branch_resolved_via_ci_env_fallback'])

    def test_ci_mode_fork_pr_head_ref_matching_default_branch_name_blocks(self) -> None:
        """Regression test (Copilot review finding on PR #302,
        PRRT_kwDORzpWpM6WzvNo): a fork PR whose source branch happens to be
        named the same as the target repository's default branch (`main` is
        the common default for a fork) must NOT be granted
        `BRANCH_CREATE_ELIGIBLE` just because `current_branch == default_branch`
        -- that equality can arise from `GITHUB_HEAD_REF` resolving a PR's
        head branch name, not from an actual push to the target repository's
        default branch. `GITHUB_HEAD_REF` is set only for
        `pull_request`/`pull_request_target` events, so its presence is the
        signal used to suppress the default-branch shortcut and fall through
        to ordinary shipment-branch matching (correctly blocking here, since
        `main` is neither a canonical `feat/`/`chore/` alias for the active
        shipment nor the actual default branch of a genuine push)."""
        readers = _FakeReaders(
            shipments=(_shipment('116-S', 'active'),),
            branch='',  # actions/checkout always leaves CI on detached HEAD
            default_branch='main',
        )
        _clear_ambient_github_head_ref()
        with patched_environ(
            GITHUB_HEAD_REF='main',
            GITHUB_EVENT_PATH=None,
        ):
            result = evaluate(
                TopologyInput(mode='ci', phase='ambient', target_shipment_id=None),
                readers=readers,
            )
        self.assertEqual(result.exit_code, 1)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_MISMATCH')
        self.assertEqual(check.details['current_branch'], 'main')
        self.assertEqual(check.details['default_branch'], 'main')

    def test_ci_mode_push_to_default_branch_named_main_still_eligible(self) -> None:
        """Companion to the fork-PR regression above: a genuine `push` event
        (no `GITHUB_HEAD_REF`) to the actual default branch must still
        resolve `BRANCH_CREATE_ELIGIBLE` -- the fix is scoped to suppressing
        the shortcut only when a `pull_request` event is active, not to
        removing the shortcut altogether."""
        readers = _FakeReaders(
            shipments=(_shipment('116-S', 'active'),),
            branch='',
            default_branch='main',
        )
        _clear_ambient_github_head_ref()
        with patched_environ(
            GITHUB_REF_NAME='main',
            GITHUB_REF_TYPE='branch',
            GITHUB_HEAD_REF=None,
            GITHUB_EVENT_PATH=None,
        ):
            result = evaluate(
                TopologyInput(mode='ci', phase='ambient', target_shipment_id=None),
                readers=readers,
            )
        self.assertEqual(result.exit_code, 0)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_CREATE_ELIGIBLE')

    def test_non_ci_mode_ignores_github_event_path_default_branch_fallback(self) -> None:
        """The `GITHUB_EVENT_PATH`-based default-branch fallback is gated on
        `mode == 'ci'` only, mirroring the detached-HEAD branch fallback:
        `agent`/`manual` mode must ignore it even if the variable happens to
        be set in the environment."""
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'),),
            branch='master',
            default_branch='main',
        )
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / 'event.json'
            event_path.write_text('{"repository": {"default_branch": "master"}}', encoding='utf-8')
            with patched_environ(GITHUB_EVENT_PATH=str(event_path)):
                result = evaluate(
                    TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
                    readers=readers,
                )
        # 'master' is neither the (reader-reported) default branch 'main' nor
        # a feat/chore/114-s alias, so agent mode must still block -- the
        # event-path override must not have applied.
        self.assertEqual(result.exit_code, 1)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_MISMATCH')
        self.assertEqual(check.details['default_branch'], 'main')
        self.assertFalse(check.details['default_branch_resolved_via_ci_env_fallback'])

    def test_non_target_branch_blocks(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'), _shipment('115-S', 'queued')),
            branch='feat/115-s',
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.primary_token, 'BRANCH_MISMATCH')

    def test_agent_target_must_resolve(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='main')
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='999-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 2)

    def test_agent_target_must_resolve_even_with_empty_shipment_map(self) -> None:
        # Regression: an explicit --shipment target naming an unknown/nonexistent
        # shipment must be rejected (exit 2) even when list_shipments() returns
        # zero records (e.g. an empty/uninitialized backlog). A vacuous
        # shipment_map must never short-circuit target validation to a silent
        # pass-through.
        readers = _FakeReaders(shipments=(), branch='main')
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='999-S-DOES-NOT-EXIST'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 2)

    def test_ambient_uses_active_target_before_branch(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'active'), _shipment('115-S', 'queued')),
            branch='feat/115-s',
        )
        result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=readers,
        )
        self.assertEqual(result.resolved_target_shipment_id, '114-S')
        self.assertEqual(result.primary_token, 'BRANCH_MISMATCH')

    def test_ambient_without_target_skips_only_ownership(self) -> None:
        readers = _FakeReaders(shipments=(), branch='topic/misc')
        result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'branch_ownership').status, 'skipped')


class WorktreeTopologyTests(unittest.TestCase):
    def test_stage_spike_research_exception_does_not_count(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(
                shipments=(_shipment('114-S', 'queued'),),
                branch='feat/114-s',
                worktrees=worktrees,
                worktree_markers={
                    'C:/repo-stage-spike-001': 'role: spike-research\nexpires_at: "2999-01-01T00:00:00Z"\n',
                },
            ),
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'worktree_topology').token, 'WORKTREE_TOPOLOGY_OK')

    def test_stage_spike_missing_marker_counts_as_implementation(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='feat/114-s', worktrees=worktrees),
        )
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')

    def test_stage_spike_expired_marker_counts_as_implementation(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(
                shipments=(_shipment('114-S', 'queued'),),
                branch='feat/114-s',
                worktrees=worktrees,
                worktree_markers={
                    'C:/repo-stage-spike-001': 'role: spike-research\nexpires_at: "2000-01-01T00:00:00Z"\n',
                },
            ),
        )
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')

    def test_stage_spike_wrong_role_counts_as_implementation(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(
                shipments=(_shipment('114-S', 'queued'),),
                branch='feat/114-s',
                worktrees=worktrees,
                worktree_markers={
                    'C:/repo-stage-spike-001': 'role: implementation\nexpires_at: "2999-01-01T00:00:00Z"\n',
                },
            ),
        )
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')

    def test_stage_spike_unparseable_marker_counts_as_implementation(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(
                shipments=(_shipment('114-S', 'queued'),),
                branch='feat/114-s',
                worktrees=worktrees,
                worktree_markers={
                    'C:/repo-stage-spike-001': 'role: [unterminated',
                },
            ),
        )
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')

    def test_multiple_implementation_worktrees_block(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-2\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/feat/115-s\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='feat/114-s', worktrees=worktrees),
        )
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')


class TargetShipmentReadinessTests(unittest.TestCase):
    def test_pre_claim_target_must_be_queued(self) -> None:
        cases = (
            _shipment('114-S', 'shipped'),
            _shipment('114-S', 'abandoned'),
            _shipment('114-S', '', archived_status='shipped'),
        )
        for shipment in cases:
            with self.subTest(shipment=shipment):
                check = _shipment_readiness_check('pre_claim', '114-S', (shipment,), _FakeReaders())
                self.assertEqual(check.status, 'blocked')
                self.assertEqual(check.token, 'TARGET_NOT_CLAIMABLE')

    def test_pre_claim_queued_target_still_passes(self) -> None:
        check = _shipment_readiness_check('pre_claim', '114-S', (_shipment('114-S', 'queued'),), _FakeReaders())
        self.assertEqual((check.status, check.token), ('passed', None))

    def test_post_claim_and_lifecycle_target_must_be_active(self) -> None:
        for phase in ('post_claim', 'lifecycle'):
            with self.subTest(phase=phase, state='queued'):
                check = _shipment_readiness_check(phase, '114-S', (_shipment('114-S', 'queued'),), _FakeReaders())
                self.assertEqual(check.status, 'blocked')
                self.assertEqual(check.token, 'TARGET_NOT_ACTIVE')
            with self.subTest(phase=phase, state='active'):
                check = _shipment_readiness_check(phase, '114-S', (_shipment('114-S', 'active'),), _FakeReaders())
                self.assertEqual((check.status, check.token), ('passed', None))

    def test_ambient_target_status_check_remains_permissive(self) -> None:
        for shipment in (
            _shipment('114-S', 'queued'),
            _shipment('114-S', 'active'),
            _shipment('114-S', 'shipped'),
        ):
            with self.subTest(shipment=shipment):
                check = _shipment_readiness_check('ambient', '114-S', (shipment,), _FakeReaders())
                self.assertEqual((check.status, check.token), ('passed', None))


class ShipmentReadinessTests(unittest.TestCase):
    def test_live_shipped_with_complete_closure_passes(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return shipment_id == '113-S'

        readers = Readers(shipments=(
            _shipment('113-S', 'shipped'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)

    def test_archived_done_with_complete_closure_passes(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return shipment_id == '113-S'

        readers = Readers(shipments=(
            _shipment('113-S', '', archived_status='done'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)

    def test_non_terminal_predecessor_blocks(self) -> None:
        readers = _FakeReaders(shipments=(
            _shipment('113-S', 'queued'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_NOT_SHIPPED')

    def test_ambiguous_live_and_archived_predecessor_blocks(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return True

        readers = Readers(shipments=(
            _shipment('113-S', 'queued', archived_status='shipped'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_STATE_AMBIGUOUS')

    def test_live_shipped_duplicate_archive_predecessor_blocks(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return True

        readers = Readers(shipments=(
            _shipment('113-S', 'shipped', archived_status='shipped'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_STATE_AMBIGUOUS')

    def test_ambiguous_target_itself_blocks_before_phase_check(self) -> None:
        # The target shipment (not just a predecessor) has both a live
        # "queued" status (which would otherwise satisfy pre_claim's phase
        # requirement) and an archive-folder record present. This same
        # provenance corruption already blocks a predecessor and must also
        # block the target -- rejected BEFORE the phase status check passes
        # it through.
        readers = _FakeReaders(shipments=(
            _shipment('114-S', 'queued', archived_status='shipped'),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'TARGET_STATE_AMBIGUOUS')

    def test_ambiguous_target_blocks_in_post_claim_phase_too(self) -> None:
        readers = _FakeReaders(shipments=(
            _shipment('114-S', 'active', archived_status='shipped'),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'TARGET_STATE_AMBIGUOUS')

    def test_incomplete_closure_blocks_even_when_terminal(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return False

        readers = Readers(shipments=(
            _shipment('113-S', 'shipped'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_CLOSURE_INCOMPLETE')


class DagAuthoritativePredecessorCharacterizationTests(unittest.TestCase, _TopologyWorkspaceMixin):
    def test_c1_explicit_linear_chain_blocks_on_unshipped_predecessor(self) -> None:
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(
                shipments=(
                    _shipment('113-S', 'queued'),
                    _shipment('114-S', 'queued', deps=('113-S',)),
                ),
                branch='main',
            ),
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_NOT_SHIPPED')
        self.assertEqual(self._readiness_check(result).details['predecessor_id'], '113-S')

    def test_c2_explicit_predecessor_requires_closure_evidence(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return False

        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=Readers(
                shipments=(
                    _shipment('113-S', 'shipped'),
                    _shipment('114-S', 'queued', deps=('113-S',)),
                ),
                branch='main',
            ),
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_CLOSURE_INCOMPLETE')

    def test_c3_converging_dag_evaluates_every_explicit_predecessor(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return shipment_id == '112-S'

        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=Readers(
                shipments=(
                    _shipment('112-S', 'shipped'),
                    _shipment('113-S', 'queued'),
                    _shipment('114-S', 'queued', deps=('112-S', '113-S')),
                ),
                branch='main',
            ),
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_NOT_SHIPPED')
        self.assertEqual(self._readiness_check(result).details['predecessor_id'], '113-S')

    def test_c4_malformed_dependency_ids_fail_closed(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '114-S', status='queued', dependencies=['../../outside'])
            self._expect_backlog_unavailable(
                lambda: self._list_shipments(workspace),
                description='a malformed dependency id',
            )

    def test_c5_labels_frontmatter_currently_reads_without_error(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '173-S', status='queued', labels=['dag-root', 'topology-gate'])
            shipments = self._list_shipments(workspace)
            self.assertEqual(len(shipments), 1)
            self.assertEqual(shipments[0].shipment_id, '173-S')
            self.assertEqual(shipments[0].live_status, 'queued')
            result = self._evaluate_workspace(workspace, '173-S')
            self.assertEqual(result.exit_code, 0)

    def test_n5f1_live_blocked_status_fails_closed_at_reader_time(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', status='blocked')
            self._expect_backlog_unavailable(
                lambda: self._list_shipments(workspace),
                description='a live shipment record with status blocked',
            )

    def test_n5g_live_record_with_missing_status_fails_closed_at_reader_time(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', filename='199-S-missing-status')
            self._expect_backlog_unavailable(
                lambda: self._list_shipments(workspace),
                description='a live shipment record with a missing status',
            )

    def test_n5g_live_record_with_blank_status_fails_closed_at_reader_time(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', filename='199-S-blank-status', status='  ')
            self._expect_backlog_unavailable(
                lambda: self._list_shipments(workspace),
                description='a live shipment record with a blank status',
            )

    def test_n5g_live_record_with_non_string_status_fails_closed_at_reader_time(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', filename='199-S-non-string-status', status=['queued'])
            self._expect_backlog_unavailable(
                lambda: self._list_shipments(workspace),
                description='a live shipment record with a non-string status',
            )

    def test_n5g_live_record_with_unrecognized_status_fails_closed_at_reader_time(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', filename='199-S-unrecognized-status', status='retired')
            self._expect_backlog_unavailable(
                lambda: self._list_shipments(workspace),
                description='a live shipment record with an unrecognized status',
            )

    def test_n5h_enumeration_failure_fails_closed(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            reader = self._reader(workspace)
            original_glob = Path.glob

            def raising_glob(path_obj: Path, pattern: str):
                if path_obj == workspace / '.backlogit' / 'archive' and pattern == '*.md':
                    raise OSError('archive directory unreadable')
                return original_glob(path_obj, pattern)

            with mock.patch('autoharness.gates.topology.Path.glob', autospec=True, side_effect=raising_glob):
                result = evaluate(
                    TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='200-S'),
                    readers=reader,
                )
            self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')


class DagAuthoritativePredecessorDerivationTests(unittest.TestCase, _TopologyWorkspaceMixin):
    def test_n1_two_adjacent_edge_less_shipments_are_not_blocked_by_numeric_inference(self) -> None:
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='149-S'),
            readers=_FakeReaders(shipments=(_shipment('148-S', 'queued'), _shipment('149-S', 'queued')), branch='main'),
        )
        self._assert_unsequenced_block(result, target='149-S')

    def test_n2_closure_evidence_is_never_demanded_for_numeric_adjacency_alone(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return False

        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='149-S'),
            readers=Readers(shipments=(_shipment('148-S', 'shipped'), _shipment('149-S', 'queued')), branch='main'),
        )
        self._assert_unsequenced_block(result, target='149-S')

    def test_n3_passing_payload_reports_predecessor_source(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return shipment_id == '113-S'

        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=Readers(shipments=(_shipment('113-S', 'shipped'), _shipment('114-S', 'queued', deps=('113-S',))), branch='main'),
        )
        self._assert_readiness_pass(result, source='explicit', predecessor_ids=('113-S',))

    def test_n3_blocked_payload_reports_predecessor_source(self) -> None:
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(shipments=(_shipment('113-S', 'queued'), _shipment('114-S', 'queued', deps=('113-S',))), branch='main'),
        )
        self._assert_explicit_block(result, predecessor_id='113-S')

    def test_n4_declared_root_passes_with_declared_root_provenance(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '173-S', status='queued', labels=['dag-root'])
            result = self._evaluate_workspace(workspace, '173-S')
        self._assert_readiness_pass(result, source='declared_root')

    def test_n5a_genesis_passes_only_for_the_sole_record(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_readiness_pass(result, source='genesis')

    def test_n5b_archived_shipped_history_prevents_genesis(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='shipped')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_unsequenced_block(result, target='200-S')

    def test_n5c_first_of_multiple_queued_shipments_is_not_genesis(self) -> None:
        with self._topology_workspace() as workspace:
            for shipment_id in ('200-S', '201-S', '202-S'):
                self._write_shipment_record(workspace, shipment_id, status='queued')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_unsequenced_block(result, target='200-S')

    def test_n5c_later_numbered_queued_shipment_is_not_genesis(self) -> None:
        with self._topology_workspace() as workspace:
            for shipment_id in ('200-S', '201-S', '202-S'):
                self._write_shipment_record(workspace, shipment_id, status='queued')
            result = self._evaluate_workspace(workspace, '202-S')
        self._assert_unsequenced_block(result, target='202-S')

    def test_n5d_abandoned_only_history_prevents_genesis(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='abandoned')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_unsequenced_block(result, target='200-S')

    def test_n5f2_archived_blocked_history_prevents_genesis(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='blocked')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_unsequenced_block(result, target='200-S')


class DagAuthoritativePredecessorLabelDerivationTests(unittest.TestCase, _TopologyWorkspaceMixin):
    def test_n5g_archived_unrecognized_status_prevents_genesis(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='retired')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_unsequenced_block(result, target='200-S')

    def test_n5e_declared_root_overrides_archived_shipped_history(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root'])
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='shipped')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_readiness_pass(result, source='declared_root')

    def test_n5e_declared_root_overrides_multiple_queued_shipments(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '201-S', status='queued')
            self._write_shipment_record(workspace, '202-S', status='queued', labels=['dag-root'])
            result = self._evaluate_workspace(workspace, '202-S')
        self._assert_readiness_pass(result, source='declared_root')

    def test_n5e_declared_root_overrides_abandoned_only_history(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root'])
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='abandoned')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_readiness_pass(result, source='declared_root')

    def test_n5e_declared_root_overrides_archived_blocked_history(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root'])
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='blocked')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_readiness_pass(result, source='declared_root')

    def test_n5e_declared_root_overrides_archived_unrecognized_status_history(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root'])
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='retired')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_readiness_pass(result, source='declared_root')

    def test_n6_unsequenced_message_names_both_remedies(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='shipped')
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_unsequenced_block(result, target='200-S')
        self._expect_contains('shipment_readiness.message', self._readiness_check(result).message, 'declare the shipment a root')

    def test_n7_exact_dag_root_membership_stores_labels_tuple_and_declares_root(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '173-S', status='queued', labels=['dag-root', 'topology-gate'])
            shipment = self._shipment_from_workspace(workspace, '173-S')
            self._assert_shipment_labels(shipment, ('dag-root', 'topology-gate'))
            result = self._evaluate_workspace(workspace, '173-S')
        self._assert_readiness_pass(result, source='declared_root')

    def test_n7_absent_labels_yield_empty_tuple_without_declaring_root(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued')
            shipment = self._shipment_from_workspace(workspace, '200-S')
            self._assert_shipment_labels(shipment, ())
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_readiness_pass(result, source='genesis')

    def test_n7_unrelated_or_case_variant_labels_do_not_declare_root(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['Dag-Root', 'topology-gate'])
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='shipped')
            shipment = self._shipment_from_workspace(workspace, '200-S')
            self._assert_shipment_labels(shipment, ('Dag-Root', 'topology-gate'))
            result = self._evaluate_workspace(workspace, '200-S')
        self._assert_unsequenced_block(result, target='200-S')

    def test_n8_bare_string_labels_are_rejected(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels='dag-root')
            self._expect_backlog_unavailable(lambda: self._list_shipments(workspace), description='labels declared as a bare string')

    def test_n8_scalar_labels_are_rejected(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=42)
            self._expect_backlog_unavailable(lambda: self._list_shipments(workspace), description='labels declared as a scalar')

    def test_n8_non_string_label_members_are_rejected(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root', 7])
            self._expect_backlog_unavailable(lambda: self._list_shipments(workspace), description='labels containing a non-string member')

    def test_n8_blank_label_members_are_rejected(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root', '   '])
            self._expect_backlog_unavailable(lambda: self._list_shipments(workspace), description='labels containing a blank member')

    def test_n8_labels_with_forward_slashes_are_rejected(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root', 'release/train'])
            self._expect_backlog_unavailable(lambda: self._list_shipments(workspace), description='labels containing a forward slash')

    def test_n8_labels_with_backslashes_are_rejected(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root', r'release\train'])
            self._expect_backlog_unavailable(lambda: self._list_shipments(workspace), description='labels containing a backslash')

    def test_n8_labels_with_dotdot_segments_are_rejected(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root', '..root'])
            self._expect_backlog_unavailable(lambda: self._list_shipments(workspace), description='labels containing a dotdot segment')


class ImplicitNumericPredecessorTests(unittest.TestCase, _TopologyWorkspaceMixin):
    """Historical context for the retired claim-path numeric heuristic.

    `_shipment_readiness_check` no longer consults `_prior_shipment_id` when
    deciding whether a shipment may be claimed. The historical defect cycles
    captured in the compound entries now live here as explicit-DAG claim
    assertions plus read-only sequencing-audit expectations over the raw numeric
    candidate the retired heuristic would have guessed.
    """

    def _future_audit_report(self, target: str, shipments: tuple[ShipmentState, ...]):
        from autoharness.gates import topology

        return topology.audit_sequencing(target_shipment_id=target, shipments=shipments)

    def test_lower_numbered_shipment_declaring_target_as_its_own_dependency_is_not_treated_as_predecessor(
        self,
    ) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return shipment_id == '137-S'

        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='139-S'),
            readers=Readers(
                shipments=(
                    _shipment('137-S', 'shipped'),
                    _shipment('138-S', 'queued', deps=('139-S',)),
                    _shipment('139-S', 'queued', deps=('137-S',)),
                ),
                branch='main',
            ),
        )
        self._assert_readiness_pass(result, source='explicit', predecessor_ids=('137-S',))

    def test_implicit_numeric_predecessor_still_blocks_when_no_declared_reverse_dependency(
        self,
    ) -> None:
        report = self._future_audit_report(
            '114-S',
            (
                _shipment('113-S', 'queued'),
                _shipment('114-S', 'queued'),
            ),
        )
        self._expect_equal(
            'audit.raw_numeric_candidate_ids',
            tuple(report['raw_numeric_candidate_ids']),
            ('113-S',),
        )

    def test_implicit_numeric_predecessor_still_blocks_when_lower_shipment_has_unrelated_deps(
        self,
    ) -> None:
        report = self._future_audit_report(
            '114-S',
            (
                _shipment('112-S', 'shipped'),
                _shipment('113-S', 'queued', deps=('112-S',)),
                _shipment('114-S', 'queued'),
            ),
        )
        self._expect_equal(
            'audit.raw_numeric_candidate_ids',
            tuple(report['raw_numeric_candidate_ids']),
            ('113-S',),
        )

    def test_multi_hop_reverse_dependency_disables_fallback_entirely_not_just_the_violator(
        self,
    ) -> None:
        report = self._future_audit_report(
            '139-S',
            (
                _shipment('137-S', 'queued'),
                _shipment('138-S', 'queued', deps=('139-S',)),
                _shipment('139-S', 'queued'),
            ),
        )
        self._expect_equal(
            'audit.raw_numeric_candidate_ids',
            tuple(report['raw_numeric_candidate_ids']),
            ('138-S',),
        )

    def test_higher_numbered_forward_dependent_does_not_suppress_targets_own_predecessor_check(
        self,
    ) -> None:
        without_forward_dependent = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='112-S'),
            readers=_FakeReaders(
                shipments=(
                    _shipment('111-S', 'queued'),
                    _shipment('112-S', 'queued'),
                ),
                branch='main',
            ),
        )
        with_forward_dependent = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='112-S'),
            readers=_FakeReaders(
                shipments=(
                    _shipment('111-S', 'queued'),
                    _shipment('112-S', 'queued'),
                    _shipment('113-S', 'queued', deps=('112-S',)),
                ),
                branch='main',
            ),
        )
        self._assert_unsequenced_block(without_forward_dependent, target='112-S')
        self._assert_unsequenced_block(with_forward_dependent, target='112-S')

    def test_higher_numbered_forward_dependent_history_is_preserved_for_future_audit_surface(
        self,
    ) -> None:
        report = self._future_audit_report(
            '112-S',
            (
                _shipment('111-S', 'queued'),
                _shipment('112-S', 'queued'),
                _shipment('113-S', 'queued', deps=('112-S',)),
            ),
        )
        self._expect_equal(
            'audit.raw_numeric_candidate_ids',
            tuple(report['raw_numeric_candidate_ids']),
            ('111-S',),
        )


class SequencingAuditTests(unittest.TestCase, _TopologyWorkspaceMixin):
    _ENABLED_CONFIG = """
schema_version: "1.0.0"
telemetry:
  mode: "sqlite"
  database_path: ".autoharness/metrics/execution_epochs.db"
  emit_jsonl: true
"""

    _DISABLED_CONFIG = """
schema_version: "1.0.0"
telemetry:
  mode: "none"
"""

    def _audit_entry(self, result, shipment_id: str):
        check = _check(result, 'sequencing_audit')
        for entry in check.details.get('edge_less_shipments', ()):
            if entry.get('target_shipment_id') == shipment_id:
                return entry
        raise AssertionError(f'missing sequencing audit entry: {shipment_id}')

    def _render_result(self, result) -> str:
        return json.dumps(result.to_dict(), sort_keys=True)

    def _snapshot_backlog_tree(self, workspace: Path) -> dict[str, str]:
        backlog_root = workspace / '.backlogit'
        return {
            str(path.relative_to(backlog_root)).replace('\\', '/'): path.read_text(encoding='utf-8')
            for path in sorted(backlog_root.rglob('*'))
            if path.is_file()
        }

    def _write_telemetry_config(self, workspace: Path, text: str) -> None:
        (workspace / '.autoharness').mkdir(parents=True, exist_ok=True)
        (workspace / '.autoharness' / 'config.yaml').write_text(text, encoding='utf-8')

    def test_audit_output_reports_declared_root_state_and_raw_candidate(self) -> None:
        from autoharness.gates import topology

        report = topology.audit_sequencing(
            target_shipment_id='200-S',
            shipments=(
                ShipmentState(
                    shipment_id='199-S',
                    title='199-S',
                    live_status='queued',
                ),
                ShipmentState(
                    shipment_id='200-S',
                    title='200-S',
                    live_status='queued',
                    labels=('dag-root',),
                ),
            ),
        )
        self._expect_equal('audit.derived_state', report['derived_state'], 'declared_root')
        self._expect_equal('audit.raw_numeric_candidate_ids', tuple(report['raw_numeric_candidate_ids']), ('199-S',))
        self._expect_equal('audit.blocking', report['blocking'], False)
        self._expect_equal('audit.authorizes_claim', report['authorizes_claim'], False)
        self._expect_equal('audit.genesis_disqualifying_records', tuple(report['genesis_disqualifying_records']), ())
        self._expect_equal(
            'audit.remediation_options',
            tuple(report['remediation_options']),
            ('record the real blocks edge', 'declare the shipment a root'),
        )

    def test_audit_output_reports_genesis_state_without_disqualifiers(self) -> None:
        from autoharness.gates import topology

        report = topology.audit_sequencing(
            target_shipment_id='200-S',
            shipments=(
                ShipmentState(
                    shipment_id='200-S',
                    title='200-S',
                    live_status='queued',
                ),
            ),
        )
        self._expect_equal('audit.derived_state', report['derived_state'], 'genesis')
        self._expect_equal('audit.raw_numeric_candidate_ids', tuple(report['raw_numeric_candidate_ids']), ())
        self._expect_equal('audit.genesis_disqualifier', report['genesis_disqualifier'], None)
        self._expect_equal('audit.genesis_disqualifying_records', tuple(report['genesis_disqualifying_records']), ())

    def test_audit_output_reports_unsequenced_state_and_names_disqualifying_records(self) -> None:
        from autoharness.gates import topology

        report = topology.audit_sequencing(
            target_shipment_id='200-S',
            shipments=(
                ShipmentState(
                    shipment_id='197-S',
                    title='197-S',
                    live_status=None,
                    archived_status='mystery',
                    archived_record_present=True,
                ),
                ShipmentState(
                    shipment_id='198-S',
                    title='198-S',
                    live_status=None,
                    archived_status=None,
                    archived_record_present=True,
                ),
                ShipmentState(
                    shipment_id='199-S',
                    title='199-S',
                    live_status='blocked',
                ),
                ShipmentState(
                    shipment_id='200-S',
                    title='200-S',
                    live_status='queued',
                ),
            ),
        )
        self._expect_equal('audit.derived_state', report['derived_state'], 'unsequenced')
        self._expect_equal('audit.raw_numeric_candidate_ids', tuple(report['raw_numeric_candidate_ids']), ('199-S',))
        self._expect_equal(
            'audit.genesis_disqualifier',
            report['genesis_disqualifier'],
            'another shipment record exists in this workspace',
        )
        disqualifiers = tuple(
            (entry['shipment_id'], entry['record_provenance'], entry['status'])
            for entry in report['genesis_disqualifying_records']
        )
        self._expect_equal(
            'audit.genesis_disqualifying_records',
            disqualifiers,
            (
                ('197-S', 'ARCHIVED', 'mystery'),
                ('198-S', 'ARCHIVED', 'missing'),
                ('199-S', 'LIVE', 'blocked'),
            ),
        )

    def test_audit_phase_never_blocks_or_authorizes_for_declared_root_genesis_and_unsequenced(self) -> None:
        cases = (
            (
                'declared_root',
                '200-S',
                lambda workspace: (
                    self._write_shipment_record(workspace, '199-S', status='queued'),
                    self._write_shipment_record(workspace, '200-S', status='queued', labels=['dag-root']),
                ),
            ),
            (
                'genesis',
                '200-S',
                lambda workspace: self._write_shipment_record(workspace, '200-S', status='queued'),
            ),
            (
                'unsequenced',
                '200-S',
                lambda workspace: (
                    self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='shipped'),
                    self._write_shipment_record(workspace, '200-S', status='queued'),
                ),
            ),
        )
        for expected_state, shipment_id, setup in cases:
            with self.subTest(state=expected_state):
                with self._topology_workspace() as workspace:
                    setup(workspace)
                    result = evaluate(
                        TopologyInput(mode='manual', phase='audit_sequencing', target_shipment_id=None),
                        readers=self._reader(workspace),
                    )
                self._expect_equal('result.exit_code', result.exit_code, 0)
                self._expect_equal('result.primary_token', result.primary_token, None)
                self._expect_equal('result.target', result.resolved_target_shipment_id, None)
                check = _check(result, 'sequencing_audit')
                self._expect_equal('sequencing_audit.status', check.status, 'passed')
                self._expect_equal('sequencing_audit.blocking', check.details.get('blocking'), False)
                self._expect_equal('sequencing_audit.authorizes_claim', check.details.get('authorizes_claim'), False)
                entry = self._audit_entry(result, shipment_id)
                self._expect_equal('audit.derived_state', entry['derived_state'], expected_state)
                self._expect_equal('audit.blocking', entry['blocking'], False)
                self._expect_equal('audit.authorizes_claim', entry['authorizes_claim'], False)

    def test_audit_phase_registration_does_not_change_preclaim_postclaim_lifecycle_or_ambient_behavior(self) -> None:
        pre_claim = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='112-S'),
            readers=_FakeReaders(
                shipments=(
                    _shipment('111-S', 'queued'),
                    _shipment('112-S', 'queued'),
                ),
                branch='main',
            ),
        )
        self._assert_unsequenced_block(pre_claim, target='112-S')

        post_claim = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='112-S'),
            readers=_FakeReaders(shipments=(_shipment('112-S', 'active'),), branch='main'),
        )
        self._expect_equal('post_claim.exit_code', post_claim.exit_code, 0)

        lifecycle = evaluate(
            TopologyInput(mode='agent', phase='lifecycle', target_shipment_id='112-S'),
            readers=_FakeReaders(shipments=(_shipment('112-S', 'active'),), branch='main'),
        )
        self._expect_equal('lifecycle.exit_code', lifecycle.exit_code, 0)

        ambient = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=_FakeReaders(shipments=(_shipment('112-S', 'active'),), branch='main'),
        )
        self._expect_equal('ambient.exit_code', ambient.exit_code, 0)
        self._expect_equal('ambient.target', ambient.resolved_target_shipment_id, '112-S')

    def test_audit_phase_is_read_only_and_telemetry_is_observational_and_fail_open(self) -> None:
        from autoharness.cli import _emit_pipeline_topology_telemetry
        from autoharness.telemetry.record import load_workspace_telemetry_config
        from autoharness.telemetry.tool_event_jsonl import journal_path_for_config

        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='shipped')
            self._write_shipment_record(workspace, '200-S', status='queued')
            backlog_before = self._snapshot_backlog_tree(workspace)

            disabled_result = evaluate(
                TopologyInput(mode='manual', phase='audit_sequencing', target_shipment_id=None),
                readers=FilesystemTopologyReaders(workspace),
            )
            disabled_rendered = self._render_result(disabled_result)
            self._write_telemetry_config(workspace, self._DISABLED_CONFIG)
            disabled_path, disabled_warnings = _emit_pipeline_topology_telemetry(workspace, disabled_result)
            self._expect_equal('disabled.telemetry_path', disabled_path, None)
            self._expect_equal('disabled.telemetry_warnings', disabled_warnings, ())
            self._expect_equal('disabled.backlog_snapshot', self._snapshot_backlog_tree(workspace), backlog_before)

            enabled_result = evaluate(
                TopologyInput(mode='manual', phase='audit_sequencing', target_shipment_id=None),
                readers=FilesystemTopologyReaders(workspace),
            )
            enabled_rendered = self._render_result(enabled_result)
            self._expect_equal('audit.rendered_output', enabled_rendered, disabled_rendered)
            self._expect_equal('audit.exit_code', enabled_result.exit_code, disabled_result.exit_code)

            self._write_telemetry_config(workspace, self._ENABLED_CONFIG)
            enabled_path, enabled_warnings = _emit_pipeline_topology_telemetry(workspace, enabled_result)
            self._expect_equal('enabled.telemetry_warnings', enabled_warnings, ())
            config = load_workspace_telemetry_config(workspace)
            journal_path = journal_path_for_config(config)
            self.assertIsNotNone(journal_path)
            self._expect_equal('enabled.telemetry_path', enabled_path, str(journal_path))
            self.assertTrue(journal_path.exists())
            event = json.loads(journal_path.read_text(encoding='utf-8').splitlines()[0])
            self._expect_equal('event.phase', event['phase'], 'audit_sequencing')
            self._expect_equal('event.status', event['status'], 'success')
            self._expect_equal('event.shipment_id', event['shipment_id'], None)
            self._expect_equal('enabled.backlog_snapshot', self._snapshot_backlog_tree(workspace), backlog_before)

            with mock.patch(
                'autoharness.telemetry.record.load_workspace_telemetry_config',
                side_effect=RuntimeError('telemetry boom'),
            ):
                failure_path, failure_warnings = _emit_pipeline_topology_telemetry(workspace, enabled_result)
            self._expect_equal('failure.telemetry_path', failure_path, None)
            self.assertEqual(len(failure_warnings), 1)
            self.assertIn('pipeline-topology telemetry warning: telemetry boom', failure_warnings[0])
            self._expect_equal('failure.rendered_output', self._render_result(enabled_result), enabled_rendered)
            self._expect_equal('failure.exit_code', enabled_result.exit_code, disabled_result.exit_code)
            self._expect_equal('failure.backlog_snapshot', self._snapshot_backlog_tree(workspace), backlog_before)


class DagReadinessPreClaimParityTests(unittest.TestCase, _TopologyWorkspaceMixin):
    @staticmethod
    def _pre_claim_readers(
        shipments: tuple[ShipmentState, ...], *, closure_complete: bool = True
    ) -> _FakeReaders:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return closure_complete

        return Readers(shipments=shipments, branch='main')

    def _dag_payload(self, shipments: tuple[ShipmentState, ...]) -> dict[str, object]:
        readiness = compute_dag_readiness(shipments)
        payload = readiness.to_dict()
        payload['status'] = 'empty' if not shipments else 'ok'
        payload['degraded_reason'] = None
        payload.update(compute_next_eligible(shipments, readiness).to_dict())
        return payload

    def _parity_snapshot(
        self,
        *,
        target: str,
        shipments: tuple[ShipmentState, ...],
        closure_complete: bool = True,
    ) -> tuple[dict[str, object], object, object, object]:
        audit = audit_sequencing(target_shipment_id=target, shipments=shipments)
        pre_claim = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id=target),
            readers=self._pre_claim_readers(shipments, closure_complete=closure_complete),
        )
        readiness = compute_dag_readiness(shipments)
        next_eligible = compute_next_eligible(shipments, readiness)
        return audit, pre_claim, readiness, next_eligible

    def _assert_pre_claim_matches_authoritative_state(
        self,
        pre_claim,
        *,
        expected_state: str,
        expected_token: str | None,
    ) -> None:
        check = self._readiness_check(pre_claim)
        self._expect_equal(
            'shipment_readiness.predecessor_source',
            check.details.get('predecessor_source'),
            expected_state,
        )
        self._expect_equal('pre_claim.primary_token', pre_claim.primary_token, expected_token)
        if expected_token is None:
            self._expect_equal('shipment_readiness.status', check.status, 'passed')
            self._expect_equal('pre_claim.exit_code', pre_claim.exit_code, 0)
        else:
            self._expect_equal('shipment_readiness.status', check.status, 'blocked')
            self._expect_equal('pre_claim.exit_code', pre_claim.exit_code, 1)

    def _assert_target_advertised(
        self,
        *,
        target: str,
        state: str,
        readiness,
        next_eligible,
    ) -> None:
        if target not in readiness.ready_set:
            raise AssertionError(
                f'{state} parity requires target {target} in ready_set when pre_claim passes it'
            )
        if next_eligible.next_eligible != target:
            raise AssertionError(
                f'{state} parity requires next_eligible {target} when pre_claim passes it'
            )

    def _assert_target_suppressed(
        self,
        *,
        target: str,
        state: str,
        readiness,
        next_eligible,
    ) -> None:
        if target in readiness.ready_set:
            raise AssertionError(
                f'{state} parity requires target {target} absent from ready_set when pre_claim blocks it'
            )
        if next_eligible.next_eligible == target:
            raise AssertionError(
                f'{state} parity requires next_eligible to exclude blocked target {target}'
            )

    def test_explicit_unshipped_predecessor_parity_suppresses_target(self) -> None:
        target = '114-S'
        shipments = (
            _shipment('113-S', 'queued'),
            _shipment(target, 'queued', deps=('113-S',)),
        )
        audit, pre_claim, readiness, next_eligible = self._parity_snapshot(
            target=target,
            shipments=shipments,
        )
        self._expect_equal('audit.derived_state', audit['derived_state'], 'explicit')
        self._assert_pre_claim_matches_authoritative_state(
            pre_claim,
            expected_state='explicit',
            expected_token='PREDECESSOR_NOT_SHIPPED',
        )
        self._assert_target_suppressed(
            target=target,
            state='explicit',
            readiness=readiness,
            next_eligible=next_eligible,
        )

    def test_explicit_shipped_terminal_predecessor_parity_advertises_target(self) -> None:
        target = '114-S'
        shipments = (
            _shipment('113-S', '', archived_status='done'),
            _shipment(target, 'queued', deps=('113-S',)),
        )
        audit, pre_claim, readiness, next_eligible = self._parity_snapshot(
            target=target,
            shipments=shipments,
            # Closure evidence is out of scope for this matrix; force it
            # complete so the predecessor-state parity signal is isolated.
            closure_complete=True,
        )
        self._expect_equal('audit.derived_state', audit['derived_state'], 'explicit')
        self._assert_pre_claim_matches_authoritative_state(
            pre_claim,
            expected_state='explicit',
            expected_token=None,
        )
        self._assert_target_advertised(
            target=target,
            state='explicit',
            readiness=readiness,
            next_eligible=next_eligible,
        )

    @expect_red(
        raises=AssertionError,
        message_contains='declared_root parity requires next_eligible 200-S when pre_claim passes it',
        reason='dag-readiness still lets ready_set ordering advisory-block a declared root target',
    )
    def test_declared_root_parity_never_advisory_blocks_a_root_target(self) -> None:
        target = '200-S'
        shipments = (
            _shipment('199-S', 'queued'),
            ShipmentState(
                shipment_id=target,
                title=target,
                live_status='queued',
                archived_status=None,
                archived_record_present=False,
                manifest_item_ids=(),
                blocking_predecessor_ids=(),
                labels=('dag-root',),
            ),
        )
        audit, pre_claim, readiness, next_eligible = self._parity_snapshot(
            target=target,
            shipments=shipments,
        )
        self._expect_equal('audit.derived_state', audit['derived_state'], 'declared_root')
        self._assert_pre_claim_matches_authoritative_state(
            pre_claim,
            expected_state='declared_root',
            expected_token=None,
        )
        self._assert_target_advertised(
            target=target,
            state='declared_root',
            readiness=readiness,
            next_eligible=next_eligible,
        )

    def test_genesis_parity_advertises_the_sole_record(self) -> None:
        target = '200-S'
        shipments = (_shipment(target, 'queued'),)
        audit, pre_claim, readiness, next_eligible = self._parity_snapshot(
            target=target,
            shipments=shipments,
        )
        self._expect_equal('audit.derived_state', audit['derived_state'], 'genesis')
        self._assert_pre_claim_matches_authoritative_state(
            pre_claim,
            expected_state='genesis',
            expected_token=None,
        )
        self._assert_target_advertised(
            target=target,
            state='genesis',
            readiness=readiness,
            next_eligible=next_eligible,
        )

    @expect_red(
        raises=AssertionError,
        message_contains='unsequenced parity requires target 200-S absent from ready_set when pre_claim blocks it',
        reason='dag-readiness still advertises an unsequenced target as ready while pre_claim blocks it',
    )
    def test_unsequenced_parity_never_advertises_a_blocked_target(self) -> None:
        target = '200-S'
        shipments = (
            _shipment('199-S', '', archived_status='shipped'),
            _shipment(target, 'queued'),
        )
        audit, pre_claim, readiness, next_eligible = self._parity_snapshot(
            target=target,
            shipments=shipments,
        )
        self._expect_equal('audit.derived_state', audit['derived_state'], 'unsequenced')
        self._assert_pre_claim_matches_authoritative_state(
            pre_claim,
            expected_state='unsequenced',
            expected_token='UNSEQUENCED_SHIPMENT',
        )
        self._assert_target_suppressed(
            target=target,
            state='unsequenced',
            readiness=readiness,
            next_eligible=next_eligible,
        )

    @expect_red(
        raises=AssertionError,
        message_contains='unsequenced parity requires target 200-S absent from ready_set when pre_claim blocks it',
        reason='a second queued shipment still leaves the target in dag-readiness ready_set instead of preserving genesis narrowness',
    )
    def test_genesis_narrowness_second_queued_record_stays_unsequenced_in_both_gates(self) -> None:
        target = '200-S'
        shipments = (
            _shipment('199-S', 'queued'),
            _shipment(target, 'queued'),
        )
        audit, pre_claim, readiness, next_eligible = self._parity_snapshot(
            target=target,
            shipments=shipments,
        )
        self._expect_equal('audit.derived_state', audit['derived_state'], 'unsequenced')
        self._assert_pre_claim_matches_authoritative_state(
            pre_claim,
            expected_state='unsequenced',
            expected_token='UNSEQUENCED_SHIPMENT',
        )
        self._assert_target_suppressed(
            target=target,
            state='unsequenced',
            readiness=readiness,
            next_eligible=next_eligible,
        )

    @expect_red(
        raises=AssertionError,
        message_contains='unsequenced parity requires target 200-S absent from ready_set when pre_claim blocks it',
        reason='an archived blocked legacy record still leaves the target ready instead of preserving genesis narrowness',
    )
    def test_genesis_narrowness_archived_blocked_record_stays_unsequenced_in_both_gates(self) -> None:
        target = '200-S'
        shipments = (
            _shipment('199-S', '', archived_status='blocked'),
            _shipment(target, 'queued'),
        )
        audit, pre_claim, readiness, next_eligible = self._parity_snapshot(
            target=target,
            shipments=shipments,
        )
        self._expect_equal('audit.derived_state', audit['derived_state'], 'unsequenced')
        self._assert_pre_claim_matches_authoritative_state(
            pre_claim,
            expected_state='unsequenced',
            expected_token='UNSEQUENCED_SHIPMENT',
        )
        self._assert_target_suppressed(
            target=target,
            state='unsequenced',
            readiness=readiness,
            next_eligible=next_eligible,
        )

    def test_live_blocked_record_fails_closed_identically_before_state_derivation(self) -> None:
        with self._topology_workspace() as workspace:
            self._write_shipment_record(workspace, '199-S', status='blocked')
            self._write_shipment_record(workspace, '200-S', status='queued')
            self._expect_backlog_unavailable(
                lambda: tuple(self._reader(workspace).list_shipments()),
                description='pre-claim shipment enumeration with a live blocked legacy record',
            )
            pre_claim = self._evaluate_workspace(workspace, '200-S')
            self._expect_equal('pre_claim.primary_token', pre_claim.primary_token, 'BACKLOG_UNAVAILABLE')
            self._expect_backlog_unavailable(
                lambda: self._dag_payload(tuple(self._reader(workspace).list_shipments())),
                description='dag-readiness shipment enumeration with a live blocked legacy record',
            )

    @expect_red(
        raises=AssertionError,
        message_contains='dag-readiness advisory report must say advisory and non-authorizing',
        reason='dag-readiness human output is not yet explicitly labelled advisory/non-authorizing',
    )
    def test_dag_readiness_report_is_explicitly_advisory_and_non_authorizing(self) -> None:
        rendered = _format_dag_readiness_report(self._dag_payload((_shipment('200-S', 'queued'),)))
        lowered = rendered.casefold()
        if 'advisory' not in lowered or 'non-authorizing' not in lowered:
            raise AssertionError('dag-readiness advisory report must say advisory and non-authorizing')

    @expect_red(
        raises=AssertionError,
        message_contains='dag-readiness next_eligible line must disclaim claim authorization',
        reason='the next_eligible line still reads like an authorization-capable scheduler output',
    )
    def test_next_eligible_output_is_explicitly_non_authorizing(self) -> None:
        rendered = _format_dag_readiness_report(self._dag_payload((_shipment('200-S', 'queued'),)))
        next_line = next(
            line for line in rendered.splitlines() if 'next eligible' in line.casefold()
        )
        lowered = next_line.casefold()
        if 'advisory' not in lowered or 'authorization' not in lowered:
            raise AssertionError('dag-readiness next_eligible line must disclaim claim authorization')

    @expect_red(
        raises=AssertionError,
        message_contains='dag-readiness payload must publish authorizes_claim=false for explicit state',
        reason='dag-readiness payload does not yet publish a machine-readable non-authorizing contract',
    )
    def test_dag_readiness_payload_publishes_authorizes_claim_false_for_all_states(self) -> None:
        cases = (
            (
                'explicit',
                (
                    _shipment('113-S', '', archived_status='done'),
                    _shipment('114-S', 'queued', deps=('113-S',)),
                ),
            ),
            ('genesis', (_shipment('200-S', 'queued'),)),
            (
                'unsequenced',
                (
                    _shipment('199-S', '', archived_status='shipped'),
                    _shipment('200-S', 'queued'),
                ),
            ),
        )
        for state, shipments in cases:
            payload = self._dag_payload(shipments)
            if payload.get('authorizes_claim') is not False:
                raise AssertionError(
                    f'dag-readiness payload must publish authorizes_claim=false for {state} state'
                )



class PostClaimVerifyTests(unittest.TestCase):
    def test_target_sole_active_passes(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'active'),))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)

    def test_active_target_passes_post_claim_despite_unshipped_explicit_predecessor(self) -> None:
        # Sequencing/predecessor readiness is a claim-ELIGIBILITY check --
        # it belongs to pre_claim only. Once the target has successfully
        # claimed (live_status == 'active'), post_claim must never
        # re-apply predecessor sequencing: a claim that has already
        # succeeded cannot be un-succeeded by a predecessor that is still
        # unshipped. The identical fixture must still block at pre_claim,
        # proving this is a phase-scoping fix and not a removal of the
        # predecessor check itself.
        readers = _FakeReaders(shipments=(
            _shipment('113-S', 'queued'),
            _shipment('114-S', 'active', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIsNone(result.primary_token)

        pre_claim_readers = _FakeReaders(shipments=(
            _shipment('113-S', 'queued'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        pre_claim_result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=pre_claim_readers,
        )
        self.assertEqual(pre_claim_result.primary_token, 'PREDECESSOR_NOT_SHIPPED')

    def test_active_target_passes_post_claim_despite_unshipped_implicit_numeric_predecessor(self) -> None:
        # Same phase-scoping guarantee, but for the implicit
        # numeric-adjacency predecessor heuristic (`_prior_shipment_id`)
        # rather than an explicit declared dependency.
        readers = _FakeReaders(shipments=(
            _shipment('113-S', 'queued'),
            _shipment('114-S', 'active'),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIsNone(result.primary_token)

    def test_target_queued_zero_active_is_retry_required_not_terminal_or_pass(self) -> None:
        # A genuinely-delayed claim (target still `queued`, zero active) is
        # indistinguishable from a genuinely-failed one on a single
        # read-only post-claim snapshot. The gate must therefore return the
        # retry-required `CLAIM_NOT_OBSERVED` token -- neither a false
        # `PASS` (the old illusory self-retry silently advanced its fake
        # snapshot to mask this) nor a premature terminal
        # `CLAIM_VERIFY_FAILED` (that classification, on retry-exhaustion,
        # is owned by 109.017-T's Ship-side bounded reclaim loop, not this
        # gate). Only the natural floor of reads is made here (evaluate()'s
        # target-resolution read + the single post-claim core-evaluation
        # read) -- there is no additional/third internal read to silently
        # observe a different snapshot.
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 3)
        self.assertFalse(result.blocked)
        self.assertEqual(result.primary_token, 'CLAIM_NOT_OBSERVED')
        self.assertEqual(readers._calls, 2)

    def test_target_queued_zero_active_failed_claim_is_also_retry_required(self) -> None:
        # A genuinely FAILED claim presents identically to a delayed one at
        # this snapshot (target `queued`, zero active) -- the gate MUST NOT
        # assert terminal CLAIM_VERIFY_FAILED here; that would require the
        # detector to discriminate delayed-vs-failed, which a stateless
        # read-only snapshot cannot do.
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertNotEqual(result.primary_token, 'CLAIM_VERIFY_FAILED')
        self.assertEqual(result.primary_token, 'CLAIM_NOT_OBSERVED')

    def test_other_active_blocks_with_claim_verify_failed(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('115-S', 'active'), _shipment('114-S', 'queued')))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'CLAIM_VERIFY_FAILED')

    def test_inconsistent_state_blocks_with_claim_verify_failed(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued', '109.002-T'),),
            artifacts={'109.002-T': _task('109.002-T', 'done')},
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'CLAIM_VERIFY_FAILED')


class AgentInputValidationTests(unittest.TestCase):
    def test_missing_phase_in_agent_mode_is_invalid(self) -> None:
        result = evaluate(
            TopologyInput(mode='agent', phase=None, target_shipment_id='114-S'),
            readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),)),
        )
        self.assertEqual(result.exit_code, 2)

    def test_empty_shipment_in_agent_mode_is_invalid(self) -> None:
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id=''),
            readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),)),
        )
        self.assertEqual(result.exit_code, 2)

    def test_scoped_phase_without_shipment_is_invalid_in_any_mode(self) -> None:
        for mode in ('manual', 'ci'):
            for phase in ('pre_claim', 'post_claim', 'lifecycle'):
                with self.subTest(mode=mode, phase=phase):
                    result = evaluate(
                        TopologyInput(mode=mode, phase=phase, target_shipment_id=None),
                        readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),)),
                    )
                    self.assertEqual(result.exit_code, 2)
                    self.assertIn('requires --shipment', result.message)

    def test_ambient_phase_without_shipment_is_valid_in_any_mode(self) -> None:
        for mode in ('manual', 'ci'):
            with self.subTest(mode=mode):
                result = evaluate(
                    TopologyInput(mode=mode, phase='ambient', target_shipment_id=None),
                    readers=_FakeReaders(shipments=()),
                )
                self.assertNotEqual(result.exit_code, 2)

    def test_scoped_phase_with_shipment_remains_valid_in_manual_and_ci_mode(self) -> None:
        for mode in ('manual', 'ci'):
            with self.subTest(mode=mode):
                result = evaluate(
                    TopologyInput(mode=mode, phase='pre_claim', target_shipment_id='114-S'),
                    readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),)),
                )
                self.assertNotEqual(result.exit_code, 2)


class ReadinessMatrixTests(unittest.TestCase):
    def _result(self, predecessor: ShipmentState, closure_complete: bool | None) -> tuple[int, str | None]:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return closure_complete

        readers = Readers(shipments=(predecessor, _shipment('114-S', 'queued', deps=('113-S',))))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        return result.exit_code, result.primary_token

    def test_terminal_states_require_complete_closure(self) -> None:
        pass_cases = (
            _shipment('113-S', 'shipped'),
            _shipment('113-S', '', archived_status='shipped'),
            _shipment('113-S', '', archived_status='done'),
        )
        for predecessor in pass_cases:
            with self.subTest(predecessor=predecessor):
                exit_code, token = self._result(predecessor, True)
                self.assertEqual((exit_code, token), (0, None))
                exit_code, token = self._result(predecessor, False)
                self.assertEqual(token, 'PREDECESSOR_CLOSURE_INCOMPLETE')

    def test_non_terminal_or_ambiguous_states_block(self) -> None:
        block_cases = (
            (_shipment('113-S', 'queued'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', 'active'), 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT'),
            (_shipment('113-S', 'abandoned'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status='queued'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status='active'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status='blocked'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status='abandoned'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status=None), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', 'queued', archived_status='shipped'), 'PREDECESSOR_STATE_AMBIGUOUS'),
        )
        for predecessor, expected_token in block_cases:
            with self.subTest(predecessor=predecessor):
                exit_code, token = self._result(predecessor, True)
                self.assertEqual(token, expected_token)


class SuppliedTargetTests(unittest.TestCase):
    def test_branch_and_readiness_use_supplied_target(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return shipment_id == '113-S'

        readers = Readers(
            shipments=(
                _shipment('113-S', 'shipped'),
                _shipment('114-S', 'queued', deps=('113-S',)),
                _shipment('115-S', 'queued', deps=('114-S',)),
            ),
            branch='feat/114-s',
        )
        pass_result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(pass_result.exit_code, 0)

        block_result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='115-S'),
            readers=readers,
        )
        self.assertEqual(block_result.primary_token, 'BRANCH_MISMATCH')


class AmbientResolutionTests(unittest.TestCase):
    def test_currently_claimed_target_is_used(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'active'), _shipment('115-S', 'queued')),
            branch='feat/114-s',
        )
        result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.resolved_target_shipment_id, '114-S')

    def test_no_target_ambient_still_runs_ambient_invariants(self) -> None:
        readers = _FakeReaders(shipments=(), branch='topic/misc')
        result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'branch_ownership').status, 'skipped')
        self.assertEqual(_check(result, 'shipment_readiness').status, 'skipped')
        self.assertEqual(_check(result, 'worktree_topology').token, 'WORKTREE_TOPOLOGY_OK')



class RunGitDiagnosticTests(unittest.TestCase):
    """Direct tests of `_run_git`'s A3R diagnostic seam via a simulated
    (mocked) subprocess result -- no real git invocation failure is needed
    or reliably reproducible cross-platform, so the nonzero exit is
    constructed directly, exactly as the plan's own language ("for a
    simulated nonzero git exit") anticipates."""

    def test_expected_absence_code_produces_no_error_and_returns_empty(self) -> None:
        fake = subprocess.CompletedProcess(args=['git'], returncode=1, stdout='', stderr='')
        with mock.patch('autoharness.gates.topology.subprocess.run', return_value=fake):
            errors: dict[str, str] = {}
            result = _run_git(
                ['git', '--no-pager', 'symbolic-ref', '--quiet', '--short', 'refs/remotes/origin/HEAD'],
                Path('.'),
                expected_absence_codes=frozenset({1}),
                error_sink=errors,
                error_key='default_branch',
            )
        self.assertEqual(result, '')
        self.assertNotIn('default_branch', errors)

    def test_unexpected_exit_populates_error_sink_with_captured_stderr(self) -> None:
        fake = subprocess.CompletedProcess(
            args=['git'], returncode=128, stdout='',
            stderr='fatal: bad config line 3 in file .git/config\n',
        )
        with mock.patch('autoharness.gates.topology.subprocess.run', return_value=fake):
            errors: dict[str, str] = {}
            result = _run_git(
                ['git', '--no-pager', 'symbolic-ref', '--quiet', '--short', 'refs/remotes/origin/HEAD'],
                Path('.'),
                expected_absence_codes=frozenset({1}),
                error_sink=errors,
                error_key='default_branch',
            )
        self.assertEqual(result, '')
        self.assertEqual(errors['default_branch'], 'fatal: bad config line 3 in file .git/config')

    def test_unexpected_exit_with_no_stderr_records_exit_code_not_empty_string(self) -> None:
        fake = subprocess.CompletedProcess(args=['git'], returncode=128, stdout='', stderr='')
        with mock.patch('autoharness.gates.topology.subprocess.run', return_value=fake):
            errors: dict[str, str] = {}
            result = _run_git(
                ['git', '--no-pager', 'symbolic-ref', '--quiet', '--short', 'refs/remotes/origin/HEAD'],
                Path('.'),
                expected_absence_codes=frozenset({1}),
                error_sink=errors,
                error_key='default_branch',
            )
        self.assertEqual(result, '')
        self.assertIn('default_branch', errors)
        self.assertNotEqual(errors['default_branch'], '')
        self.assertIn('128', errors['default_branch'])

    def test_success_never_populates_error_sink(self) -> None:
        fake = subprocess.CompletedProcess(args=['git'], returncode=0, stdout='main\n', stderr='')
        with mock.patch('autoharness.gates.topology.subprocess.run', return_value=fake):
            errors: dict[str, str] = {}
            result = _run_git(
                ['git', '--no-pager', 'branch', '--show-current'],
                Path('.'),
                error_sink=errors,
                error_key='current_branch',
            )
        self.assertEqual(result, 'main')
        self.assertNotIn('current_branch', errors)

    def test_no_sink_supplied_is_a_silent_noop(self) -> None:
        # Callers that never pass error_sink/error_key (the plain two-arg
        # call shape used everywhere before this task) see EXACTLY the
        # pre-change behavior -- no AttributeError, no accidental key.
        fake = subprocess.CompletedProcess(args=['git'], returncode=128, stdout='', stderr='fatal: x')
        with mock.patch('autoharness.gates.topology.subprocess.run', return_value=fake):
            result = _run_git(['git', '--no-pager', 'branch', '--show-current'], Path('.'))
        self.assertEqual(result, '')


class BranchOwnershipGitInvocationErrorTests(unittest.TestCase):
    """Propagation tests: `_branch_ownership_check`'s `CheckResult.details`
    gains `git_invocation_error` ONLY when the reader reports one, and every
    pre-existing key/verdict is byte-identical either way (A3/A3R)."""

    def test_no_git_error_leaves_details_byte_identical_to_baseline(self) -> None:
        baseline_readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'),), branch='feat/114-s',
        )
        baseline = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=baseline_readers,
        )
        errored_readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'),), branch='feat/114-s', git_errors={},
        )
        errored = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=errored_readers,
        )
        baseline_check = _check(baseline, 'branch_ownership')
        errored_check = _check(errored, 'branch_ownership')
        self.assertEqual(baseline.exit_code, errored.exit_code)
        self.assertEqual(baseline_check.token, errored_check.token)
        self.assertEqual(baseline_check.details, errored_check.details)
        self.assertNotIn('git_invocation_error', baseline_check.details)
        self.assertNotIn('git_invocation_error', errored_check.details)

    def test_git_invocation_error_present_is_additive_on_branch_mismatch(self) -> None:
        # Verdict-equality test (A3): a simulated invocation-error reader
        # produces the IDENTICAL exit_code/token/pre-existing-details keys
        # as the pre-change (no-error) reader, PLUS the new key carrying the
        # captured stderr.
        baseline_readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='')
        baseline = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=baseline_readers,
        )
        errored_readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'),),
            branch='',
            git_errors={'default_branch': 'fatal: bad config line 3 in file .git/config'},
        )
        errored = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=errored_readers,
        )
        baseline_check = _check(baseline, 'branch_ownership')
        errored_check = _check(errored, 'branch_ownership')

        self.assertEqual(errored.exit_code, baseline.exit_code)
        self.assertEqual(errored_check.token, baseline_check.token)
        self.assertEqual(errored_check.status, baseline_check.status)
        for key, value in baseline_check.details.items():
            self.assertEqual(errored_check.details[key], value)
        self.assertNotIn('git_invocation_error', baseline_check.details)
        self.assertEqual(
            errored_check.details['git_invocation_error'],
            'fatal: bad config line 3 in file .git/config',
        )

    def test_git_invocation_error_present_is_additive_on_branch_ok(self) -> None:
        baseline_readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'),), branch='feat/114-s',
        )
        baseline = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=baseline_readers,
        )
        errored_readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'),),
            branch='feat/114-s',
            git_errors={'current_branch': 'git exited with status 128'},
        )
        errored = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=errored_readers,
        )
        baseline_check = _check(baseline, 'branch_ownership')
        errored_check = _check(errored, 'branch_ownership')

        self.assertEqual(errored.exit_code, baseline.exit_code)
        self.assertEqual(errored_check.token, baseline_check.token)
        for key, value in baseline_check.details.items():
            self.assertEqual(errored_check.details[key], value)
        self.assertEqual(
            errored_check.details['git_invocation_error'], 'git exited with status 128',
        )

    def test_reader_without_git_invocation_error_method_is_unaffected(self) -> None:
        # A reader that does not expose `git_invocation_error` at all (e.g.
        # `_NullReaders`, or any third-party TopologyReaders implementation
        # written before this task) must not raise AttributeError and must
        # never gain the new key -- `_collect_git_invocation_error` looks it
        # up defensively via getattr.
        #
        # Copilot review finding on PR #398: the previous version of this
        # test used `target_shipment_id=None` against `_NullReaders` (which
        # has no shipments), so `_branch_ownership_check` returned at its
        # EARLIER "ambient target did not resolve" skip path and never
        # actually reached `_collect_git_invocation_error` at all -- the
        # test only proved the skip path itself doesn't raise, not that the
        # defensive getattr path is exercised. It also defined an unused
        # `_NoErrorMethodReaders(_FakeReaders)` subclass that inherited
        # `git_invocation_error` from `_FakeReaders` (so it could never have
        # simulated the "method absent" case even if it had been used).
        #
        # This version defines a reader that implements every
        # `TopologyReaders` method EXCEPT `git_invocation_error`, and
        # supplies shipments/branch data so `_branch_ownership_check`
        # actually reaches its `_collect_git_invocation_error(readers,
        # "current_branch", "default_branch")` call (a matching target with
        # `shipment is not None`), and so `_worktree_uniqueness_check`
        # reaches its own `_collect_git_invocation_error(readers,
        # "worktree_porcelain")` call too -- proving the defensive `getattr`
        # guard is genuinely exercised on both checks, not skipped past.
        class _ReaderWithoutGitInvocationErrorMethod:
            def list_shipments(self):
                return (_shipment('114-S', 'queued'),)

            def read_artifact(self, artifact_id: str):
                return None

            def current_branch(self) -> str:
                return 'feat/114-s'

            def default_branch(self) -> str:
                return 'main'

            def worktree_porcelain(self) -> str:
                return (
                    'worktree C:/repo\n'
                    'HEAD 0000000000000000000000000000000000000000\n'
                    'branch refs/heads/feat/114-s\n\n'
                )

            def read_worktree_marker(self, worktree_path: str):
                return None

            def closure_complete(self, shipment_id: str):
                return None

            # Deliberately NO `git_invocation_error` method defined.

        baseline_readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'),), branch='feat/114-s',
        )
        baseline = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=baseline_readers,
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_ReaderWithoutGitInvocationErrorMethod(),
        )
        baseline_branch_check = _check(baseline, 'branch_ownership')
        result_branch_check = _check(result, 'branch_ownership')
        baseline_worktree_check = _check(baseline, 'worktree_topology')
        result_worktree_check = _check(result, 'worktree_topology')

        # Both checks actually ran (were NOT skipped), proving the reader
        # lacking the method did reach the `_collect_git_invocation_error`
        # call site in each -- not merely that `evaluate()` as a whole
        # didn't raise.
        self.assertNotEqual(result_branch_check.status, 'skipped')
        self.assertNotEqual(result_worktree_check.status, 'skipped')

        # No AttributeError propagated (evaluate() completed and returned),
        # and neither check gained the new key when the reader cannot
        # report one.
        self.assertNotIn('git_invocation_error', result_branch_check.details)
        self.assertNotIn('git_invocation_error', result_worktree_check.details)
        self.assertEqual(result_branch_check.details, baseline_branch_check.details)
        self.assertEqual(result_worktree_check.details, baseline_worktree_check.details)
        self.assertEqual(result.exit_code, baseline.exit_code)

        # Also cover the REAL production `_NullReaders` (which likewise
        # defines no `git_invocation_error` method): worktree_topology has
        # no target-shipment skip gate, so it reaches
        # `_collect_git_invocation_error(readers, "worktree_porcelain")`
        # even under `_NullReaders`, proving the defensive getattr guard
        # handles the actual shipped null-reader implementation too, not
        # just this test's synthetic stand-in.
        from autoharness.gates.topology import _NullReaders

        null_result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=_NullReaders(),
        )
        null_worktree_check = _check(null_result, 'worktree_topology')
        self.assertNotEqual(null_worktree_check.status, 'skipped')
        self.assertNotIn('git_invocation_error', null_worktree_check.details)
        self.assertEqual(_check(null_result, 'branch_ownership').status, 'skipped')


class WorktreeGitInvocationErrorTests(unittest.TestCase):
    def test_git_invocation_error_present_is_additive_on_worktree_topology_ok(self) -> None:
        baseline_readers = _FakeReaders(shipments=())
        baseline = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=baseline_readers,
        )
        errored_readers = _FakeReaders(
            shipments=(), git_errors={'worktree_porcelain': 'fatal: unable to read worktree config'},
        )
        errored = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=errored_readers,
        )
        baseline_check = _check(baseline, 'worktree_topology')
        errored_check = _check(errored, 'worktree_topology')
        self.assertEqual(errored.exit_code, baseline.exit_code)
        self.assertEqual(errored_check.token, baseline_check.token)
        for key, value in baseline_check.details.items():
            self.assertEqual(errored_check.details[key], value)
        self.assertNotIn('git_invocation_error', baseline_check.details)
        self.assertEqual(
            errored_check.details['git_invocation_error'],
            'fatal: unable to read worktree config',
        )


class AmbientEmptyGithubHeadRefPushContextEndToEndTests(unittest.TestCase):
    """152.003-T: an end-to-end regression test for the actual ambient
    condition that broke CI (116-S live-CI finding; hotfix commit
    ``2661c1c8``).

    GitHub Actions sets ``GITHUB_HEAD_REF`` to the empty string -- PRESENT,
    not absent -- on ``push``-triggered runs, as opposed to
    ``pull_request``-triggered runs (where it is genuinely the PR's source
    branch name) or a bare local shell (where it is typically unset
    entirely). This test drives ``evaluate()`` through that literal ambient
    state end to end, rather than through five individually patched call
    sites, asserting the push-context outcome: an empty ``GITHUB_HEAD_REF``
    must NOT be mistaken for a `pull_request` event, and branch resolution
    must fall through to ``GITHUB_REF_NAME``/``GITHUB_REF_TYPE``.

    This manipulates ``os.environ`` directly rather than via
    ``patched_environ()``: ``patched_environ()``'s A5 entry-guard
    (144.002-T, BINDING) deliberately refuses to patch a key whose ambient
    value is already the empty string, which is exactly the state this test
    needs to hold for the duration of the ``evaluate()`` call.
    """

    _MANAGED_KEYS = (
        'GITHUB_HEAD_REF',
        'GITHUB_REF_NAME',
        'GITHUB_REF_TYPE',
        'GITHUB_EVENT_PATH',
    )

    def setUp(self) -> None:
        self._prior = {key: os.environ.get(key) for key in self._MANAGED_KEYS}

    def tearDown(self) -> None:
        for key, value in self._prior.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_ambient_empty_head_ref_is_not_treated_as_pull_request(self) -> None:
        from autoharness.gates.topology import _ci_pull_request_event_active

        os.environ['GITHUB_HEAD_REF'] = ''
        self.assertFalse(_ci_pull_request_event_active())

    def test_ambient_empty_head_ref_push_context_resolves_via_ref_name(self) -> None:
        """The literal push-context ambient state: `GITHUB_HEAD_REF` present
        as `""`, `GITHUB_REF_NAME`/`GITHUB_REF_TYPE` naming the pushed
        branch. `--mode ci` must resolve the branch via the `GITHUB_REF_NAME`
        fallback, exactly as a real `push`-triggered CI run requires."""
        os.environ['GITHUB_HEAD_REF'] = ''
        os.environ['GITHUB_REF_NAME'] = 'main'
        os.environ['GITHUB_REF_TYPE'] = 'branch'
        os.environ.pop('GITHUB_EVENT_PATH', None)

        readers = _FakeReaders(
            shipments=(_shipment('116-S', 'active'),), branch='', default_branch='main',
        )
        result = evaluate(
            TopologyInput(mode='ci', phase='ambient', target_shipment_id=None),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_CREATE_ELIGIBLE')
        self.assertTrue(check.details['resolved_via_ci_env_fallback'])


class GithubHeadRefClearHelperGuardTests(unittest.TestCase):
    """152.003-T: a machine-enforced guard for the `_clear_ambient_github_head_ref()`
    convention (029-DL: a convention survives only if a machine produces it
    or penalizes its absence).

    Statically parses THIS test file's own source and asserts that every
    `patched_environ(...)` call naming `GITHUB_HEAD_REF` -- whether used as
    a `with` context manager or invoked bare -- is immediately preceded, in
    its own enclosing statement block, by a call to
    `_clear_ambient_github_head_ref()`. This guards against reintroducing
    the ambient-empty-string failure class (hotfix commit `2661c1c8`) the
    next time a test is written against
    `patched_environ(GITHUB_HEAD_REF=...)` without the clear helper.

    The traversal covers every nested statement-list block reachable from a
    statement, including the two block kinds that live inside non-statement
    child nodes rather than a top-level `body`/`orelse`/`finalbody` field:
    `Try.handlers` (each `ExceptHandler.body`) and `Match.cases` (each
    `match_case.body`). Without those two, a call written inside an
    `except:` clause or a `case:` block would be invisible to the guard
    despite the guard's claim to cover every call in the file (local review
    finding, PR #439).
    """

    @staticmethod
    def _call_targets_patched_environ_with_head_ref(call: ast.Call) -> bool:
        if not (isinstance(call.func, ast.Name) and call.func.id == 'patched_environ'):
            return False
        return any(kw.arg == 'GITHUB_HEAD_REF' for kw in call.keywords)

    @staticmethod
    def _is_clear_helper_call(stmt: ast.stmt) -> bool:
        return (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name)
            and stmt.value.func.id == '_clear_ambient_github_head_ref'
        )

    def _find_violations(self, tree: ast.Module) -> list[int]:
        violations: list[int] = []

        def nested_blocks(stmt: ast.stmt) -> list[list[ast.stmt]]:
            """Every statement-list block nested directly inside `stmt`.

            Covers the generic `body`/`orelse`/`finalbody` fields (If, For,
            While, With, Try, function/class bodies, ...) AND the two block
            kinds that live inside non-statement child nodes rather than a
            top-level field: `ast.Try.handlers` (a list of `ExceptHandler`,
            each with its own `.body`) and `ast.Match.cases` (a list of
            `match_case`, each with its own `.body`). Without these two, a
            `patched_environ(GITHUB_HEAD_REF=...)` call written inside an
            `except:` clause or a `case:` block is silently invisible to
            this guard even though the guard claims to cover every call in
            the file.
            """
            blocks: list[list[ast.stmt]] = []
            for field in ('body', 'orelse', 'finalbody'):
                nested = getattr(stmt, field, None)
                if isinstance(nested, list) and nested:
                    blocks.append(nested)
            for handler in getattr(stmt, 'handlers', None) or []:
                handler_body = getattr(handler, 'body', None)
                if isinstance(handler_body, list) and handler_body:
                    blocks.append(handler_body)
            for case in getattr(stmt, 'cases', None) or []:
                case_body = getattr(case, 'body', None)
                if isinstance(case_body, list) and case_body:
                    blocks.append(case_body)
            return blocks

        def visit_body(body: list[ast.stmt]) -> None:
            for index, stmt in enumerate(body):
                target_call = None
                if isinstance(stmt, ast.With):
                    for item in stmt.items:
                        ctx = item.context_expr
                        if isinstance(ctx, ast.Call) and self._call_targets_patched_environ_with_head_ref(ctx):
                            target_call = ctx
                            break
                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    if self._call_targets_patched_environ_with_head_ref(stmt.value):
                        target_call = stmt.value

                if target_call is not None:
                    preceded = index > 0 and self._is_clear_helper_call(body[index - 1])
                    if not preceded:
                        violations.append(stmt.lineno)

                for nested in nested_blocks(stmt):
                    visit_body(nested)

        visit_body(tree.body)
        return violations

    def test_every_patched_environ_github_head_ref_call_is_preceded_by_clear_helper(self) -> None:
        source_path = Path(__file__)
        source = source_path.read_text(encoding='utf-8')
        tree = ast.parse(source, filename=str(source_path))
        violations = self._find_violations(tree)
        self.assertEqual(
            violations,
            [],
            'patched_environ(...) call(s) naming GITHUB_HEAD_REF at line(s) '
            f'{violations} in {source_path.name} are not immediately preceded '
            'by a call to _clear_ambient_github_head_ref() -- see hotfix '
            'commit 2661c1c8 and 152.003-T.',
        )

    def test_guard_detects_a_violation_when_the_clear_call_is_missing(self) -> None:
        """Proves the guard is not vacuously true: a synthetic module whose
        `patched_environ(GITHUB_HEAD_REF=...)` call is NOT preceded by the
        clear helper must be reported as a violation."""
        synthetic_source = (
            "def test_example():\n"
            "    readers = None\n"
            "    with patched_environ(GITHUB_HEAD_REF='feat/x'):\n"
            "        pass\n"
        )
        tree = ast.parse(synthetic_source, filename='<synthetic>')
        violations = self._find_violations(tree)
        self.assertEqual(violations, [3])

    def test_guard_accepts_a_call_immediately_preceded_by_the_clear_helper(self) -> None:
        synthetic_source = (
            "def test_example():\n"
            "    _clear_ambient_github_head_ref()\n"
            "    with patched_environ(GITHUB_HEAD_REF='feat/x'):\n"
            "        pass\n"
        )
        tree = ast.parse(synthetic_source, filename='<synthetic>')
        violations = self._find_violations(tree)
        self.assertEqual(violations, [])

    def test_guard_detects_a_violation_inside_an_except_handler(self) -> None:
        """A `patched_environ(GITHUB_HEAD_REF=...)` call written inside an
        `except:` clause is ordinary control flow, not an escape hatch: the
        guard must traverse `Try.handlers` (each `ExceptHandler.body`) and
        report the violation exactly as it would for the same call at the
        top level of a function."""
        synthetic_source = (
            "def test_example():\n"
            "    try:\n"
            "        pass\n"
            "    except ValueError:\n"
            "        with patched_environ(GITHUB_HEAD_REF='feat/x'):\n"
            "            pass\n"
        )
        tree = ast.parse(synthetic_source, filename='<synthetic>')
        violations = self._find_violations(tree)
        self.assertEqual(violations, [5])

    def test_guard_accepts_a_call_preceded_by_the_clear_helper_inside_an_except_handler(self) -> None:
        synthetic_source = (
            "def test_example():\n"
            "    try:\n"
            "        pass\n"
            "    except ValueError:\n"
            "        _clear_ambient_github_head_ref()\n"
            "        with patched_environ(GITHUB_HEAD_REF='feat/x'):\n"
            "            pass\n"
        )
        tree = ast.parse(synthetic_source, filename='<synthetic>')
        violations = self._find_violations(tree)
        self.assertEqual(violations, [])

    def test_guard_detects_a_violation_inside_a_match_case(self) -> None:
        """A `patched_environ(GITHUB_HEAD_REF=...)` call written inside a
        `match`/`case` block is ordinary control flow, not an escape hatch:
        the guard must traverse `Match.cases` (each `match_case.body`) and
        report the violation exactly as it would for the same call at the
        top level of a function."""
        synthetic_source = (
            "def test_example(value):\n"
            "    match value:\n"
            "        case 'x':\n"
            "            with patched_environ(GITHUB_HEAD_REF='feat/x'):\n"
            "                pass\n"
        )
        tree = ast.parse(synthetic_source, filename='<synthetic>')
        violations = self._find_violations(tree)
        self.assertEqual(violations, [4])

    def test_guard_accepts_a_call_preceded_by_the_clear_helper_inside_a_match_case(self) -> None:
        synthetic_source = (
            "def test_example(value):\n"
            "    match value:\n"
            "        case 'x':\n"
            "            _clear_ambient_github_head_ref()\n"
            "            with patched_environ(GITHUB_HEAD_REF='feat/x'):\n"
            "                pass\n"
        )
        tree = ast.parse(synthetic_source, filename='<synthetic>')
        violations = self._find_violations(tree)
        self.assertEqual(violations, [])

