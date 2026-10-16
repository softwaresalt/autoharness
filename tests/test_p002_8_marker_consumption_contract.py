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


if __name__ == "__main__":
    unittest.main()
