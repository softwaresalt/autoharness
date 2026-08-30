"""CLI acceptance tests for `autoharness gate pre-review` (149.008-T / 149.011-T)."""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import textwrap
import unittest
from contextlib import chdir, redirect_stderr, redirect_stdout
from pathlib import Path

from autoharness.cli import main
from autoharness.detectors.registry import load_detector_registry_from_workspace

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMP_ROOT = _REPO_ROOT / ".test-output"
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "detectors" / "art" / "pr-202-075.006-T-before.md"


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - CLI harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


class PreReviewCliTests(unittest.TestCase):
    def _git(self, workspace: Path, *args: str) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()

    def _write_common_workspace(self, workspace: Path, *, config_text: str) -> None:
        (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
        (workspace / ".backlogit" / "templates").mkdir(parents=True, exist_ok=True)
        (workspace / ".backlogit" / "queue").mkdir(parents=True, exist_ok=True)
        (workspace / ".backlogit" / "archive").mkdir(parents=True, exist_ok=True)
        (workspace / ".autoharness" / "config.yaml").write_text(config_text, encoding="utf-8")
        (workspace / ".autoharness" / "workspace-profile.yaml").write_text(
            "runtime_surfaces:\n  cli: true\n",
            encoding="utf-8",
        )
        for name in ("task.md", "shipment.md"):
            source = _REPO_ROOT / ".backlogit" / "templates" / name
            (workspace / ".backlogit" / "templates" / name).write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        (workspace / ".backlogit" / "queue" / "157-S.md").write_text(
            textwrap.dedent(
                """\
                ---
                artifact_type: shipment
                custom_fields:
                    items: []
                id: 157-S
                priority: medium
                status: active
                title: Shipment
                ---

                ## Description

                <!-- BEGIN:description -->
                Valid shipment artifact.
                <!-- END:description -->

                ## Items

                <!-- BEGIN:items -->
                <!-- END:items -->

                ## Blocked Returns

                <!-- BEGIN:blocked-returns -->
                <!-- END:blocked-returns -->
                """
            ),
            encoding="utf-8",
        )

    def _valid_task(self) -> str:
        return textwrap.dedent(
            """\
            ---
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
            """
        )

    def _init_repo(self, workspace: Path) -> str:
        self._git(workspace, "init", "-b", "feat/157-s-fixture")
        self._git(workspace, "config", "user.email", "test@example.com")
        self._git(workspace, "config", "user.name", "Test User")
        self._git(workspace, "add", ".")
        self._git(workspace, "commit", "-m", "base")
        return self._git(workspace, "rev-parse", "HEAD")

    def test_gate_help_lists_pre_review(self) -> None:
        out, _, _ = _run("gate", "--help")
        self.assertIn("pre-review", out)

    def test_shipped_registry_contains_exactly_one_detector(self) -> None:
        registry = load_detector_registry_from_workspace(_REPO_ROOT, _REPO_ROOT)
        self.assertEqual(len(registry.nodes), 1)
        self.assertEqual(registry.nodes[0].node_id, "det:D-ART/ART-01@1")

    def test_pre_review_json_emits_report_and_exits_zero_on_failed_art_01(self) -> None:
        config_text = textwrap.dedent(
            """\
            detectors:
              - node_id: "det:D-ART/ART-01@1"
                applies_when:
                  changed_paths_any:
                    - ".backlogit/**"
                producer:
                  kind: "pure"
                  ref: "autoharness.detectors.art.section_markers:produce"
                  tool_version_dims: ["python"]
                validator:
                  ref: "autoharness.detectors.art.section_markers:validate"
                  consumes: []
                depends_on: []
                severity: "medium"
                mode: "report_only"
                remediation:
                  class: "guided_fix"
                  authority: "stage"
            """
        )
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_common_workspace(workspace, config_text=config_text)
            (workspace / ".backlogit" / "queue" / "149.006-T.md").write_text(self._valid_task(), encoding="utf-8")
            base_sha = self._init_repo(workspace)
            (workspace / ".backlogit" / "queue" / "149.006-T.md").write_text(
                _FIXTURE.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            self._git(workspace, "add", ".")
            self._git(workspace, "commit", "-m", "historical defect")
            with chdir(workspace):
                out, err, code = _run("gate", "pre-review", "--base", base_sha, "--json")

            self.assertEqual(err, "")
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(payload["exit_code"], 0)
            self.assertEqual(payload["results"][0]["status"], "failed")
            self.assertEqual(payload["results"][0]["provenance"]["base_sha"], base_sha)
            report_path = workspace / payload["report_path"]
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIsInstance(report, list)
            self.assertEqual(report[0]["status"], "failed")

    def test_pre_review_cycle_registry_exits_2_and_evaluates_nothing(self) -> None:
        config_text = textwrap.dedent(
            """\
            detectors:
              - node_id: "det:D-ART/ART-01@1"
                applies_when: { always: true }
                producer:
                  kind: "pure"
                  ref: "autoharness.detectors.art.section_markers:produce"
                validator:
                  ref: "autoharness.detectors.art.section_markers:validate"
                depends_on: ["det:D-ART/ART-02@1"]
                severity: "medium"
                mode: "report_only"
                remediation:
                  class: "guided_fix"
                  authority: "stage"
              - node_id: "det:D-ART/ART-02@1"
                applies_when: { always: true }
                producer:
                  kind: "pure"
                  ref: "autoharness.detectors.art.section_markers:produce"
                validator:
                  ref: "autoharness.detectors.art.section_markers:validate"
                depends_on: ["det:D-ART/ART-01@1"]
                severity: "medium"
                mode: "report_only"
                remediation:
                  class: "guided_fix"
                  authority: "stage"
            """
        )
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_common_workspace(workspace, config_text=config_text)
            (workspace / ".backlogit" / "queue" / "149.006-T.md").write_text(self._valid_task(), encoding="utf-8")
            base_sha = self._init_repo(workspace)
            (workspace / ".backlogit" / "queue" / "149.006-T.md").write_text(self._valid_task() + "\n", encoding="utf-8")
            self._git(workspace, "add", ".")
            self._git(workspace, "commit", "-m", "touch")
            with chdir(workspace):
                out, _, code = _run("gate", "pre-review", "--base", base_sha, "--json")

            self.assertEqual(code, 2)
            payload = json.loads(out)
            self.assertEqual(payload["results"], [])
            self.assertEqual(payload["evaluated_count"], 0)
            # Cycle detection now runs at registry *load* time (shared with the
            # assembler via `topological_order_or_cycle`), fail-closed and before
            # a DetectorRegistry is ever constructed, so the cycle path never
            # reaches assembly and is reported via `message`, not `cycle_nodes`.
            self.assertEqual(payload["cycle_nodes"], [])
            self.assertIn("cycle", payload["message"].lower())
            self.assertFalse((workspace / ".autoharness" / "gates" / "pre-review").exists())

    def test_pre_review_rejects_option_like_base_with_no_report_side_effect(self) -> None:
        config_text = textwrap.dedent(
            """\
            detectors:
              - node_id: "det:D-ART/ART-01@1"
                applies_when: { always: true }
                producer:
                  kind: "pure"
                  ref: "autoharness.detectors.art.section_markers:produce"
                validator:
                  ref: "autoharness.detectors.art.section_markers:validate"
                depends_on: []
                severity: "medium"
                mode: "report_only"
                remediation:
                  class: "guided_fix"
                  authority: "stage"
            """
        )
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_common_workspace(workspace, config_text=config_text)
            (workspace / ".backlogit" / "queue" / "149.006-T.md").write_text(self._valid_task(), encoding="utf-8")
            self._init_repo(workspace)
            output_target = workspace / "should-not-exist.txt"
            with chdir(workspace):
                out, err, code = _run(
                    "gate",
                    "pre-review",
                    "--base",
                    f"--output={output_target}",
                    "--json",
                )

            self.assertEqual(err, "")
            self.assertEqual(code, 2)
            payload = json.loads(out)
            self.assertEqual(payload["exit_code"], 2)
            self.assertFalse(output_target.exists())
            self.assertFalse((workspace / ".autoharness" / "gates" / "pre-review").exists())


    def test_pre_review_exit_code_reflects_invalid_node_result_not_hardcoded_zero(self) -> None:
        # A detector can legitimately return status "invalid"
        # (`status_exit_code("invalid") == 2`); the CLI previously hard-coded
        # `exit_code=0` for the success/report-emission path regardless of
        # individual node statuses, silently reporting success. Patch the
        # assembler boundary (rather than fabricating a real detector ref
        # that returns "invalid") to exercise the CLI's own aggregation
        # logic in isolation.
        from unittest import mock

        from autoharness.detectors.assembler import DetectorAssemblyResult
        from autoharness.detectors.contract import NodeResult

        config_text = textwrap.dedent(
            """\
            detectors:
              - node_id: "det:D-ART/ART-01@1"
                applies_when: { always: true }
                producer:
                  kind: "pure"
                  ref: "autoharness.detectors.art.section_markers:produce"
                validator:
                  ref: "autoharness.detectors.art.section_markers:validate"
                depends_on: []
                severity: "medium"
                mode: "report_only"
                remediation:
                  class: "guided_fix"
                  authority: "stage"
            """
        )
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            self._write_common_workspace(workspace, config_text=config_text)
            (workspace / ".backlogit" / "queue" / "149.006-T.md").write_text(self._valid_task(), encoding="utf-8")
            base_sha = self._init_repo(workspace)

            fake_result = NodeResult(
                name="det:D-ART/ART-01@1", status="invalid", token="INVALID", message="contract violation"
            )
            fake_assembly = DetectorAssemblyResult(
                results=(fake_result,), exit_code=2, cycle_nodes=(), evaluated_count=1, evaluation_order=("det:D-ART/ART-01@1",)
            )
            with chdir(workspace):
                with mock.patch(
                    "autoharness.detectors.assembler.assemble_detector_results", return_value=fake_assembly
                ):
                    out, err, code = _run("gate", "pre-review", "--base", base_sha, "--json")

            self.assertEqual(err, "")
            self.assertEqual(code, 2)
            payload = json.loads(out)
            self.assertEqual(payload["exit_code"], 2)
            self.assertEqual(payload["results"][0]["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
