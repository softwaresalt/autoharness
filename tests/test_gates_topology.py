"""Deterministic tests for the pipeline-topology gate core."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from autoharness.gates.topology import (
    ArtifactState,
    ShipmentState,
    TopologyInput,
    _active_invariant_check,
    _shipment_readiness_check,
    evaluate,
)


class _FakeReaders:
    def __init__(self, shipments=(), artifacts=None, branch='main', default_branch='main', worktrees=None, worktree_markers=None):
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


class FilesystemTopologyReadersTests(unittest.TestCase):
    def test_missing_backlog_dir_blocks_in_agent_and_ci_modes(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
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
        with patch.dict(
            'os.environ',
            {'GITHUB_HEAD_REF': 'feat/116-s-topology-gate-c-remote-ci-validation-backstop'},
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
        with patch.dict(
            'os.environ', {'GITHUB_REF_NAME': 'main', 'GITHUB_REF_TYPE': 'branch'}, clear=False
        ):
            import os as _os

            _os.environ.pop('GITHUB_HEAD_REF', None)
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
        with patch.dict(
            'os.environ',
            {'GITHUB_REF_NAME': 'feat/114-s', 'GITHUB_REF_TYPE': 'branch'},
            clear=False,
        ):
            import os as _os

            _os.environ.pop('GITHUB_HEAD_REF', None)
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
        with patch.dict(
            'os.environ', {'GITHUB_REF_NAME': 'v1.2.3', 'GITHUB_REF_TYPE': 'tag'}, clear=False
        ):
            import os as _os

            _os.environ.pop('GITHUB_HEAD_REF', None)
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
        with patch.dict('os.environ', {}, clear=False):
            import os as _os

            _os.environ.pop('GITHUB_HEAD_REF', None)
            _os.environ.pop('GITHUB_REF_NAME', None)
            _os.environ.pop('GITHUB_REF_TYPE', None)
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
        with patch.dict('os.environ', {'GITHUB_HEAD_REF': 'feat/114-s'}):
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
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            event_path = Path(tmp) / 'event.json'
            event_path.write_text('{"repository": {"default_branch": "master"}}', encoding='utf-8')
            with patch.dict(
                'os.environ',
                {
                    'GITHUB_REF_NAME': 'master',
                    'GITHUB_REF_TYPE': 'branch',
                    'GITHUB_EVENT_PATH': str(event_path),
                },
                clear=False,
            ):
                import os as _os

                _os.environ.pop('GITHUB_HEAD_REF', None)
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
        with patch.dict('os.environ', {}, clear=False):
            import os as _os

            _os.environ.pop('GITHUB_EVENT_PATH', None)
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
        with patch.dict(
            'os.environ',
            {'GITHUB_HEAD_REF': 'main'},
            clear=False,
        ):
            import os as _os

            _os.environ.pop('GITHUB_EVENT_PATH', None)
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
        with patch.dict(
            'os.environ',
            {'GITHUB_REF_NAME': 'main', 'GITHUB_REF_TYPE': 'branch'},
            clear=False,
        ):
            import os as _os

            _os.environ.pop('GITHUB_HEAD_REF', None)
            _os.environ.pop('GITHUB_EVENT_PATH', None)
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
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            event_path = Path(tmp) / 'event.json'
            event_path.write_text('{"repository": {"default_branch": "master"}}', encoding='utf-8')
            with patch.dict('os.environ', {'GITHUB_EVENT_PATH': str(event_path)}, clear=False):
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


class PostClaimVerifyTests(unittest.TestCase):
    def test_target_sole_active_passes(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'active'),))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)

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

