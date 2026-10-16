"""Contract tests for P-002.8 (claim-marker consumption contract, marker_contract_version: 1)."""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_TEMPLATE = _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
POLICY_INSTALLED = _REPO_ROOT / ".github" / "policies" / "workflow-policies.md"
SHIP_TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
SHIP_INSTALLED = _REPO_ROOT / ".github" / "agents" / "_ship.agent.md"

P0028_BEGIN = "<!-- P-002.8:BEGIN canonical claim-marker consumption contract -->"
P0028_END = "<!-- P-002.8:END -->"
P0027_BEGIN = "<!-- P-002.7:BEGIN"
P0027_END = "<!-- P-002.7:END -->"

M8_TOKENS = (
    "claim-assigned",
    "claim-assigned waiting",
    "active residual",
    "WAVE_NO_PROGRESS",
    "WAVE_CLAIM_STATE_INDETERMINATE",
    "WORK_STARTED: <S>",
    "marker_contract_version: 1",
)

# SHA-256 of the P-002.7 block as it exists on main (LF bytes, BEGIN through END line).
P0027_BLOCK_SHA256 = "658f87b4dcb1d2c617b0e18caba7fcd1753fef109871525841bef261458fbb93"


def lf_text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def extract(text: str, begin_prefix: str, end_line: str) -> str:
    start = text.index(begin_prefix)
    end = text.index(end_line, start) + len(end_line)
    return text[start:end]


def p0028_block(path: Path) -> str:
    return extract(lf_text(path), P0028_BEGIN, P0028_END)


def p0027_block(path: Path) -> str:
    return extract(lf_text(path), P0027_BEGIN, P0027_END)


def parse_contract_version(block: str) -> int:
    match = re.search(r"marker_contract_version: (\d+)", block)
    assert match is not None
    return int(match.group(1))


class P0028PolicyContractTests(unittest.TestCase):
    def test_template_and_mirror_carry_identical_block(self) -> None:
        template_block = p0028_block(POLICY_TEMPLATE)
        self.assertEqual(template_block, p0028_block(POLICY_INSTALLED))
        self.assertIn("marker_contract_version: 1", template_block)
        self.assertIn("scheduler-baseline-marker/v1", template_block)
        self.assertIn(
            "https://github.com/softwaresalt/backlogit/blob/main/docs/design-docs/"
            "scheduler-baseline-marker-contract.md",
            template_block,
        )
        self.assertEqual(
            template_block.count("scheduler-baseline-marker-contract.md"),
            template_block.count(
                "https://github.com/softwaresalt/backlogit/blob/main/docs/design-docs/"
                "scheduler-baseline-marker-contract.md"
            ),
        )

    def test_rule_ids_and_shared_tokens_present(self) -> None:
        block = p0028_block(POLICY_TEMPLATE)
        for rule in range(1, 9):
            self.assertRegex(block, rf"\*\*M{rule}\b")
        for token in M8_TOKENS:
            self.assertIn(token, block)
        self.assertIn("bumps `marker_contract_version`", block)

    def test_p0027_block_is_stable_and_not_redeclared(self) -> None:
        for path in (POLICY_TEMPLATE, POLICY_INSTALLED):
            with self.subTest(path=path.name):
                text = lf_text(path)
                self.assertEqual(text.count(P0027_BEGIN), 1)
                block = p0027_block(path)
                self.assertNotIn("P-002.8", block)
                digest = hashlib.sha256((block + "\n").encode("utf-8")).hexdigest()
                self.assertEqual(digest, P0027_BLOCK_SHA256)
        self.assertEqual(p0027_block(POLICY_TEMPLATE), p0027_block(POLICY_INSTALLED))

    def test_block_placement_and_amendment_log(self) -> None:
        for path in (POLICY_TEMPLATE, POLICY_INSTALLED):
            with self.subTest(path=path.name):
                text = lf_text(path)
                end_027 = text.index(P0027_END) + len(P0027_END)
                begin_028 = text.index(P0028_BEGIN)
                self.assertGreater(begin_028, end_027 - 1)
                self.assertEqual(text[end_027:begin_028].strip(), "")
                log = text[text.index("## Amendment Log"):]
                rows = [r for r in log.split("\n") if r.startswith("|") and "P-002.8" in r]
                self.assertEqual(len(rows), 1)
                self.assertIn("Added P-002.8", rows[0])


SHIP_ADMISSION_BEGIN = "<!-- P-002.8:BEGIN ship step 3 claim-marker admission -->"
SHIP_ADMISSION_END = "<!-- P-002.8:END ship step 3 claim-marker admission -->"


def ship_admission(path: Path) -> str:
    return extract(lf_text(path), SHIP_ADMISSION_BEGIN, SHIP_ADMISSION_END)


class P0028ShipStep3AdmissionTests(unittest.TestCase):
    def test_item_1b_cites_contract_in_template_and_mirror(self) -> None:
        for path in (SHIP_TEMPLATE, SHIP_INSTALLED):
            with self.subTest(path=path.name):
                block = ship_admission(path)
                self.assertIn("Claim-marker consumption (P-002.8", block)
                self.assertIn("marker_contract_version: 1", block)
                for rule in ("M1", "M3", "M4", "M5", "M6"):
                    self.assertIn(rule, block)

    def test_halt_tokens_and_waiting_report(self) -> None:
        for path in (SHIP_TEMPLATE, SHIP_INSTALLED):
            with self.subTest(path=path.name):
                block = ship_admission(path)
                for token in (
                    "WAVE_CLAIM_STATE_INDETERMINATE",
                    "WAVE_NO_PROGRESS",
                    "active residual",
                    "claim-assigned waiting",
                ):
                    self.assertIn(token, block)
                self.assertLess(
                    block.index("WAVE_CLAIM_STATE_INDETERMINATE"), block.index("WAVE_NO_PROGRESS")
                )

    def test_flag_false_states_no_behavior_change(self) -> None:
        for path in (SHIP_TEMPLATE, SHIP_INSTALLED):
            with self.subTest(path=path.name):
                flat = " ".join(ship_admission(path).split())
                self.assertIn(
                    "unchanged when `features.scheduler_baseline_claim` is false or absent", flat
                )

    def test_operator_resumed_carve_out_is_narrow(self) -> None:
        for path in (SHIP_TEMPLATE, SHIP_INSTALLED):
            with self.subTest(path=path.name):
                flat = " ".join(ship_admission(path).split())
                self.assertIn("active residual (operator-resumed)", flat)
                self.assertIn("`ship`-owned checkpoint", flat)
                self.assertIn("recorded current task ID", flat)
                self.assertIn("never applies to an indeterminate member", flat)
                self.assertIn("Any second residual", flat)
                self.assertIn("WORK_STARTED: <S>", flat)

START_RECORD_BEGIN = "<!-- P-002.8:BEGIN ship step 4.1 start record -->"
START_RECORD_END = "<!-- P-002.8:END ship step 4.1 start record -->"


def start_record(path: Path) -> str:
    return " ".join(extract(lf_text(path), START_RECORD_BEGIN, START_RECORD_END).split())


class P0028ShipStep41StartRecordTests(unittest.TestCase):
    def test_start_record_cites_m3_and_comment_text(self) -> None:
        for path in (SHIP_TEMPLATE, SHIP_INSTALLED):
            with self.subTest(path=path.name):
                block = start_record(path)
                self.assertIn("P-002.8", block)
                self.assertIn("M3", block)
                self.assertIn("WORK_STARTED: <S>", block)
                self.assertIn("`append_comment`", block)
                self.assertIn("actor `ship`", block)
                self.assertIn("never moves a claim-assigned task again", block)
                self.assertIn("WAVE_CLAIM_STATE_INDETERMINATE", block)

    def test_append_is_idempotent_via_reread(self) -> None:
        for path in (SHIP_TEMPLATE, SHIP_INSTALLED):
            with self.subTest(path=path.name):
                block = start_record(path)
                self.assertIn("immediately before appending", block)
                self.assertIn("re-reads the log before any retry or CLI fallback", block)
                self.assertIn("never appends a second", block)

    def test_flag_false_leaves_step_unchanged(self) -> None:
        for path in (SHIP_TEMPLATE, SHIP_INSTALLED):
            with self.subTest(path=path.name):
                self.assertIn(
                    "unchanged when `features.scheduler_baseline_claim` is false or absent",
                    start_record(path),
                )

if __name__ == "__main__":
    unittest.main()
