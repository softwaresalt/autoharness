"""Text-contract tests for 216.004-T: Ship accepts the verification-gated docs-only route."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
MIRROR = _REPO_ROOT / ".github" / "agents" / "_ship.agent.md"

CODE_LABEL = "harness-ready"
DOCS_LABEL = "harness-verification-gated"
EXCLUSIVITY = re.compile(r"never|exclusive|not both|\bnot\b|neither|either|instead|without|excluded|excludes", re.IGNORECASE)


def lf_text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


class ShipDocsRouteTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = lf_text(TEMPLATE)

    def step(self, start: str, end: str) -> str:
        begin = self.text.index(start)
        return self.text[begin : self.text.index(end, begin)]

    def test_code_route_text_unchanged(self) -> None:
        for needle in (
            "* **Already harnessed**: tasks carrying the `harness-ready` label — skip these.",
            "* **Needs harness**: tasks without the `harness-ready` label — scaffold these",
            "4. After scaffolding completes, confirm every queued task now carries the `harness-ready` label. If any task still lacks it, halt and report the gap rather than proceeding with a partial set.",
            "2. List all tasks with `harness-ready` label and `{{STATUS_QUEUED}}` status for the target feature or chore.",
            "* `harness_cmd`: The test command from the task's harness-ready metadata",
            "1. Commit changes with a conventional commit message",
        ):
            self.assertIn(needle, self.text)

    def test_step_2_partition_accepts_exactly_the_matching_route(self) -> None:
        step2 = self.step("### Step 2: Harness Generation", "### Step 3: Build Ready Queue")
        self.assertIn("**Docs route**", step2)
        self.assertIn(DOCS_LABEL, step2)
        self.assertIn("excluded from the scaffold list", step2)
        self.assertIn("no stub, test or RED evidence", step2)
        self.assertIn("re-checks qualification at intake", step2)
        self.assertIn("never applies either route label", step2)

    def test_step_3_admit(self) -> None:
        step3 = self.step("### Step 3: Build Ready Queue", "### Step 4: Execute Task Loop")
        self.assertIn("**Docs route admit**", step3)
        self.assertIn(DOCS_LABEL, step3)
        self.assertIn("re-checks qualification at claim", step3)

    def test_step_4_1_baseline_capture(self) -> None:
        block = self.step("#### Step 4.1: Claim Task", "#### Step 4.1a: Begin Telemetry Context")
        self.assertIn("<!-- P-002.8:END ship step 4.1 start record -->", block)
        tail = block.split("<!-- P-002.8:END ship step 4.1 start record -->", 1)[1]
        for needle in (
            "autoharness harness docs-only-check --phase baseline",
            "--backlog-root", "--task {item_id}", "--feature {parent_id}", "--shipment {shipment_id}",
            "head_sha", "self-digest", "task comment", "git-ignored",
            "never pre-cleans", "claim writes", "route label", "close-out", "session memory",
            "OWNED_PATH_DIRTY_AT_BASELINE", "P-002 violation", "P-005",
        ):
            self.assertIn(needle, tail)

    def test_completion_gate_precedes_commit_and_close_out(self) -> None:
        step45 = self.text[self.text.index("#### Step 4.5: Complete Task") :]
        step45 = step45[: step45.index("### Step 5: PR Lifecycle")]
        gate = step45.index("**Docs-route completion gate")
        commit = step45.index("1. Commit changes with a conventional commit message")
        self.assertLess(gate, commit)
        text = step45[gate:commit]
        for needle in (
            "recorded executable verification gate", "autoharness harness docs-only-check --phase completion",
            "--baseline", "--backlog-root", "--task {item_id}", "--feature {parent_id}", "--shipment {shipment_id}",
            "P-002 violation", "P-005", "exit 1 or 2", "before the task commit",
        ):
            self.assertIn(needle, text)

    def test_step_4_2_harness_cmd_is_code_route_only(self) -> None:
        step42 = self.step("#### Step 4.2: Delegate to Build Feature", "#### Step 4.3: Quality Gates")
        for needle in (
            "code route only", "docs-route task", "do not look up `harness_cmd`",
            "recorded verification commands, working directories, and pass criteria", "Docs Route section",
        ):
            self.assertIn(needle, step42)

    def test_baseline_precedes_telemetry(self) -> None:
        self.assertLess(
            self.text.index("--phase baseline"), self.text.index("#### Step 4.1a: Begin Telemetry Context")
        )

    def test_labels_never_coexist(self) -> None:
        offenders = [
            line for line in self.text.splitlines()
            if CODE_LABEL in line and DOCS_LABEL in line and not EXCLUSIVITY.search(line)
        ]
        self.assertEqual(offenders, [])


class ShipDocsRouteMirrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = lf_text(MIRROR)

    def test_mirror_carries_docs_route_contract(self) -> None:
        for needle in (
            DOCS_LABEL, "accepts exactly the route", "re-checks qualification at intake and at claim",
            "autoharness harness docs-only-check --phase baseline", "autoharness harness docs-only-check --phase completion",
            "--baseline", "--backlog-root", "--task {task_id}", "--feature {parent_id}", "--shipment {shipment_id}",
            "never pre-cleans", "OWNED_PATH_DIRTY_AT_BASELINE", "P-002 violation", "P-005",
        ):
            self.assertIn(needle, self.text)

    def test_mirror_ordering(self) -> None:
        baseline = self.text.index("--phase baseline")
        telemetry = self.text.index("2. **Begin telemetry context**")
        gate = self.text.index("--phase completion")
        commit = self.text.index("6. **Commit**")
        self.assertLess(baseline, telemetry)
        self.assertLess(gate, commit)

    def test_mirror_keeps_numbered_steps_and_anchors(self) -> None:
        for needle in ("5. **Validate**: Run quality gates.", "6. **Commit**: Use conventional commits",
                       "which is built for exactly that mixed state."):
            self.assertIn(needle, self.text)

    def test_mirror_hands_docs_verification_to_build_feature(self) -> None:
        for needle in (
            "`harness_cmd` lookup from harness-ready metadata is code-route-only;",
            "recorded verification commands, working directories, and pass criteria", "Docs Route section",
        ):
            self.assertIn(needle, self.text)

    def test_mirror_labels_never_coexist(self) -> None:
        offenders = [
            line for line in self.text.splitlines()
            if CODE_LABEL in line and DOCS_LABEL in line and not EXCLUSIVITY.search(line)
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
