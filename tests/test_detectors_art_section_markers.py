"""ART-01 section-marker conformance tests (149.006-T / 149.011-T)."""

from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path

from autoharness.detectors.art.section_markers import produce, validate
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


if __name__ == "__main__":
    unittest.main()
