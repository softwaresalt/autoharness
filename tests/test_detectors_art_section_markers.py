"""ART-01 section-marker conformance tests (149.006-T / 149.011-T)."""

from __future__ import annotations

import subprocess
import tempfile
import types
import unittest
from pathlib import Path

from autoharness.detectors.art.section_markers import MalformedTemplateSectionsError, produce, validate
from autoharness.detectors.contract import (
    ApplicabilitySpec,
    NodeSpec,
    ProducerSpec,
    RemediationSpec,
    ValidatorSpec,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMP_ROOT = _REPO_ROOT / ".test-output"
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "detectors" / "art" / "pr-202-075.006-T-before.md"


class ArtSectionMarkerTests(unittest.TestCase):
    def _node(self) -> NodeSpec:
        return NodeSpec(
            node_id="det:D-ART/ART-01@1",
            domain="D-ART",
            detector_id="ART-01",
            version="1",
            applies_when=ApplicabilitySpec(changed_paths_any=(".backlogit/**",)),
            producer=ProducerSpec(kind="pure", ref="autoharness.detectors.art.section_markers:produce"),
            validator=ValidatorSpec(ref="autoharness.detectors.art.section_markers:validate"),
            severity="medium",
            remediation=RemediationSpec(class_name="guided_fix", authority="stage"),
        )

    def _write_workspace(self, workspace: Path, *, task_body: str) -> None:
        templates_dir = workspace / ".backlogit" / "templates"
        queue_dir = workspace / ".backlogit" / "queue"
        templates_dir.mkdir(parents=True, exist_ok=True)
        queue_dir.mkdir(parents=True, exist_ok=True)
        for name in ("task.md", "shipment.md"):
            source = _REPO_ROOT / ".backlogit" / "templates" / name
            (templates_dir / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        (queue_dir / "157-S.md").write_text(
            """---
artifact_type: shipment
id: 157-S
priority: medium
status: active
title: Shipment
---

## Description

<!-- BEGIN:description -->
A valid shipment artifact.
<!-- END:description -->

## Items

<!-- BEGIN:items -->
- 149.006-T
<!-- END:items -->

## Blocked Returns

<!-- BEGIN:blocked-returns -->
<!-- END:blocked-returns -->
""",
            encoding="utf-8",
        )
        (queue_dir / "149.006-T.md").write_text(task_body, encoding="utf-8")

    def test_art_01_passes_conformant_artifact(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_workspace(
                workspace,
                task_body="""---
artifact_type: task
id: 149.006-T
priority: medium
status: queued
title: Task
---

## Description

<!-- BEGIN:description -->
Valid body.
<!-- END:description -->

## Acceptance Criteria

<!-- BEGIN:acceptance-criteria -->
- one
<!-- END:acceptance-criteria -->

## Implementation Notes

<!-- BEGIN:implementation-notes -->
None.
<!-- END:implementation-notes -->
""",
            )
            evidence = produce(self._node(), types.SimpleNamespace(workspace=workspace))
            result = validate(self._node(), {self._node().node_id: evidence}, types.SimpleNamespace(workspace=workspace))
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.details["failure_count"], 0)

    def test_art_01_flags_missing_or_unpaired_markers(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_workspace(workspace, task_body=_FIXTURE.read_text(encoding="utf-8"))
            evidence = produce(self._node(), types.SimpleNamespace(workspace=workspace))
            result = validate(self._node(), {self._node().node_id: evidence}, types.SimpleNamespace(workspace=workspace))
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.details["failure_count"], 1)
        failure = result.details["failures"][0]
        self.assertTrue(failure["path"].endswith("149.006-T.md"))
        self.assertIn("acceptance-criteria", failure["sections"])
        self.assertIn("implementation-notes", failure["sections"])

    def test_art_01_redetects_historical_pr_202_defect_without_mutation(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_workspace(workspace, task_body=_FIXTURE.read_text(encoding="utf-8"))
            queue_dir = workspace / ".backlogit" / "queue"
            before = {
                path.name: (path.read_text(encoding="utf-8"), path.stat().st_mtime_ns)
                for path in queue_dir.glob("*.md")
            }
            evidence = produce(self._node(), types.SimpleNamespace(workspace=workspace))
            result = validate(self._node(), {self._node().node_id: evidence}, types.SimpleNamespace(workspace=workspace))
            after = {
                path.name: (path.read_text(encoding="utf-8"), path.stat().st_mtime_ns)
                for path in queue_dir.glob("*.md")
            }
        self.assertEqual(before, after)
        self.assertEqual(result.status, "failed")
        self.assertIn("149.006-T.md", result.message)

    def test_art_01_reports_insufficient_evidence_for_unresolvable_artifact_type(self) -> None:
        # A missing/malformed `artifact_type` (or one with no matching
        # template) must never be silently treated as "conformant" just
        # because there are zero declared sections to check against it.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_workspace(
                workspace,
                task_body="""---
artifact_type: unknown-type
id: 149.006-T
priority: medium
status: queued
title: Task
---

## Description

Some body with no recognizable sections at all.
""",
            )
            evidence = produce(self._node(), types.SimpleNamespace(workspace=workspace))
            result = validate(self._node(), {self._node().node_id: evidence}, types.SimpleNamespace(workspace=workspace))
        self.assertEqual(result.status, "insufficient_evidence")
        self.assertEqual(result.details["failure_count"], 0)
        self.assertEqual(result.details["unresolved_count"], 1)
        self.assertTrue(result.details["unresolved"][0]["path"].endswith("149.006-T.md"))

    def test_art_01_reports_insufficient_evidence_when_templates_directory_is_missing(self) -> None:
        # Without any loadable templates, every artifact_type lookup misses;
        # this must resolve to the same fail-closed `insufficient_evidence`
        # path as an unresolvable per-artifact type, never a false "passed".
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            queue_dir = workspace / ".backlogit" / "queue"
            queue_dir.mkdir(parents=True, exist_ok=True)
            # Deliberately no ".backlogit/templates" directory at all.
            (queue_dir / "149.006-T.md").write_text(
                """---
artifact_type: task
id: 149.006-T
priority: medium
status: queued
title: Task
---

## Description

Body.
""",
                encoding="utf-8",
            )
            evidence = produce(self._node(), types.SimpleNamespace(workspace=workspace))
            result = validate(self._node(), {self._node().node_id: evidence}, types.SimpleNamespace(workspace=workspace))
        self.assertEqual(result.status, "insufficient_evidence")
        self.assertEqual(result.details["unresolved_count"], 1)

    def test_art_01_uses_shared_backlog_root_resolver_for_dot_backlog_default(self) -> None:
        # backlogit now defaults to `.backlog/` (with `.backlogit` remaining
        # supported); ART-01 must resolve the actual backlog root via the
        # shared resolver rather than hardcoding `.backlogit`, or it would
        # scan an absent tree and falsely report "passed" with zero
        # artifacts in a `.backlog/`-only workspace.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            templates_dir = workspace / ".backlog" / "templates"
            queue_dir = workspace / ".backlog" / "queue"
            templates_dir.mkdir(parents=True, exist_ok=True)
            queue_dir.mkdir(parents=True, exist_ok=True)
            for name in ("task.md", "shipment.md"):
                source = _REPO_ROOT / ".backlogit" / "templates" / name
                (templates_dir / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            (queue_dir / "149.006-T.md").write_text(
                """---
artifact_type: task
id: 149.006-T
priority: medium
status: queued
title: Task
---

## Description

<!-- BEGIN:description -->
Valid body.
<!-- END:description -->

## Acceptance Criteria

<!-- BEGIN:acceptance-criteria -->
- one
<!-- END:acceptance-criteria -->

## Implementation Notes

<!-- BEGIN:implementation-notes -->
None.
<!-- END:implementation-notes -->
""",
                encoding="utf-8",
            )
            evidence = produce(self._node(), types.SimpleNamespace(workspace=workspace))
            result = validate(self._node(), {self._node().node_id: evidence}, types.SimpleNamespace(workspace=workspace))
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.details["artifact_count"], 1)
        self.assertEqual(result.details["failure_count"], 0)

    def test_art_01_raises_when_no_backlog_root_is_present(self) -> None:
        # Absent both `.backlog` and `.backlogit`, ART-01 must not silently
        # report "passed" with zero artifacts (that would look identical to
        # a clean, checked workspace) -- it must propagate the shared
        # resolver's failure so the assembler converts it to
        # `insufficient_evidence`.
        from autoharness.backlog_root import BacklogUnavailableError

        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            with self.assertRaises(BacklogUnavailableError):
                produce(self._node(), types.SimpleNamespace(workspace=workspace))

    def _init_git_repo(self, workspace: Path) -> None:
        for argv in (
            ["git", "init", "--quiet"],
            ["git", "config", "user.email", "test@example.com"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(argv, cwd=str(workspace), check=True, capture_output=True, text=True)

    def _git_commit_all(self, workspace: Path, message: str) -> None:
        subprocess.run(["git", "add", "-A"], cwd=str(workspace), check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "--quiet", "-m", message],
            cwd=str(workspace),
            check=True,
            capture_output=True,
            text=True,
        )

    def test_art_01_rejects_dirty_worktree_when_head_sha_is_supplied(self) -> None:
        # Copilot review finding (PR #420): ART-01 reads the live working
        # tree while the report key (`detectors/report.py`) and the
        # applicability diff (`detectors/applicability.py`) are based only
        # on immutable base/HEAD SHAs. If the relevant paths have
        # uncommitted changes, the evidence produced cannot be reconstructed
        # from that HEAD later, and because report publication is
        # append-only/no-clobber, a later clean run at the same epoch could
        # never replace it. When the real `ApplicabilityContext.head_sha` is
        # present, a positively-confirmed dirty git status for the relevant
        # paths must reject the evidence as `insufficient_evidence` rather
        # than a false `passed`/`failed`.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_workspace(
                workspace,
                task_body="""---
artifact_type: task
id: 149.006-T
priority: medium
status: queued
title: Task
---

## Description

<!-- BEGIN:description -->
Valid body.
<!-- END:description -->

## Acceptance Criteria

<!-- BEGIN:acceptance-criteria -->
- one
<!-- END:acceptance-criteria -->

## Implementation Notes

<!-- BEGIN:implementation-notes -->
None.
<!-- END:implementation-notes -->
""",
            )
            self._init_git_repo(workspace)
            self._git_commit_all(workspace, "initial commit")
            head_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=str(workspace), check=True, capture_output=True, text=True
            ).stdout.strip()
            # Dirty the queue file *after* the commit -- this is the
            # scenario the finding describes.
            queue_dir = workspace / ".backlogit" / "queue"
            (queue_dir / "149.006-T.md").write_text(
                (queue_dir / "149.006-T.md").read_text(encoding="utf-8") + "\nDirty edit.\n",
                encoding="utf-8",
            )
            context = types.SimpleNamespace(workspace=workspace, head_sha=head_sha)
            evidence = produce(self._node(), context)
            result = validate(self._node(), {self._node().node_id: evidence}, context)
        self.assertEqual(result.status, "insufficient_evidence")
        self.assertFalse(evidence.payload["worktree_clean"])
        self.assertIn("uncommitted changes", result.message)

    def test_art_01_passes_clean_committed_worktree_when_head_sha_is_supplied(self) -> None:
        # Sanity companion to the dirty-worktree rejection above: a fully
        # committed, clean working tree with `head_sha` supplied must still
        # reach the normal `passed` verdict -- the new check must not
        # over-reject a genuinely clean, reproducible state.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_workspace(
                workspace,
                task_body="""---
artifact_type: task
id: 149.006-T
priority: medium
status: queued
title: Task
---

## Description

<!-- BEGIN:description -->
Valid body.
<!-- END:description -->

## Acceptance Criteria

<!-- BEGIN:acceptance-criteria -->
- one
<!-- END:acceptance-criteria -->

## Implementation Notes

<!-- BEGIN:implementation-notes -->
None.
<!-- END:implementation-notes -->
""",
            )
            self._init_git_repo(workspace)
            self._git_commit_all(workspace, "initial commit")
            head_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=str(workspace), check=True, capture_output=True, text=True
            ).stdout.strip()
            context = types.SimpleNamespace(workspace=workspace, head_sha=head_sha)
            evidence = produce(self._node(), context)
            result = validate(self._node(), {self._node().node_id: evidence}, context)
        self.assertEqual(result.status, "passed")
        self.assertTrue(evidence.payload["worktree_clean"])

    def test_art_01_rejects_working_tree_deletion_of_relevant_directory_when_head_sha_is_supplied(self) -> None:
        # Copilot review finding (PR #420, round 8): filtering the git-status
        # pathspecs by `path.exists()` misses a staged or unstaged deletion
        # of an entire `templates/`/`queue/` directory. Once the directory is
        # gone from disk, the old code would drop it from the pathspec list
        # entirely, so git status was never asked about it -- production
        # would see zero templates/artifacts and could still publish
        # `passed`/`artifact_count: 0` for a HEAD whose files were removed
        # only in the working tree. The fix always passes both pathspecs
        # regardless of current existence, so a working-tree-only deletion
        # is still positively detected as dirty.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_workspace(
                workspace,
                task_body="""---
artifact_type: task
id: 149.006-T
priority: medium
status: queued
title: Task
---

## Description

<!-- BEGIN:description -->
Valid body.
<!-- END:description -->

## Acceptance Criteria

<!-- BEGIN:acceptance-criteria -->
- one
<!-- END:acceptance-criteria -->

## Implementation Notes

<!-- BEGIN:implementation-notes -->
None.
<!-- END:implementation-notes -->
""",
            )
            self._init_git_repo(workspace)
            self._git_commit_all(workspace, "initial commit")
            head_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=str(workspace), check=True, capture_output=True, text=True
            ).stdout.strip()
            # Remove the entire templates/ directory from the working tree
            # only (never staged, never committed) -- the exact scenario
            # the finding describes.
            import shutil

            shutil.rmtree(workspace / ".backlogit" / "templates")
            context = types.SimpleNamespace(workspace=workspace, head_sha=head_sha)
            evidence = produce(self._node(), context)
        self.assertFalse(evidence.payload["worktree_clean"])

    def _write_malformed_template(self, workspace: Path, *, sections_yaml: str) -> None:
        templates_dir = workspace / ".backlogit" / "templates"
        queue_dir = workspace / ".backlogit" / "queue"
        templates_dir.mkdir(parents=True, exist_ok=True)
        queue_dir.mkdir(parents=True, exist_ok=True)
        (templates_dir / "task.md").write_text(
            f"""---
name: task-template
type: task
description: "A discrete unit of work"
sections:
{sections_yaml}
---
# {{title}}
""",
            encoding="utf-8",
        )
        (queue_dir / "149.006-T.md").write_text(
            """---
artifact_type: task
id: 149.006-T
priority: medium
status: queued
title: Task
---

## Description

<!-- BEGIN:description -->
Body.
<!-- END:description -->
""",
            encoding="utf-8",
        )

    def test_art_01_fails_evidence_production_on_malformed_section_name(self) -> None:
        # Copilot review finding (PR #420): a malformed section declaration
        # (e.g. a `names:` typo instead of `name:`) was previously silently
        # dropped from the loaded template rather than failing loudly. That
        # would let a typo remove a required check entirely, and every
        # artifact of that type would then falsely report `passed`.
        # Evidence production must instead fail outright so the assembler
        # converts this into `insufficient_evidence`.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_malformed_template(
                workspace,
                sections_yaml="  - names: acceptance-criteria\n    required: true\n",
            )
            with self.assertRaises(MalformedTemplateSectionsError):
                produce(self._node(), types.SimpleNamespace(workspace=workspace))

    def test_art_01_fails_evidence_production_on_non_boolean_required(self) -> None:
        # Copilot review finding (PR #420): a non-boolean `required` value
        # (e.g. the YAML string `"false"`) was previously coerced via
        # `bool(...)`, which is Python-truthy for any non-empty string --
        # silently turning a *disabled* required-check declaration into an
        # *enabled* one. Evidence production must instead fail outright.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_malformed_template(
                workspace,
                sections_yaml='  - name: acceptance-criteria\n    required: "false"\n',
            )
            with self.assertRaises(MalformedTemplateSectionsError):
                produce(self._node(), types.SimpleNamespace(workspace=workspace))


if __name__ == "__main__":
    unittest.main()
