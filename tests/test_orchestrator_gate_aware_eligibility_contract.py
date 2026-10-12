"""Contract tests for the 202-F gate-aware Orchestrator eligibility (P1) and
dark-mode activation preflight (P3) text (shipment 209-S, unit 202.004-T).

These tests pin the load-bearing instruction text in BOTH the Orchestrator
template and its installed dogfood mirror, plus the ``feature-flow-dark``
prompt template and its installed mirror:

* Step 0 runs a per-candidate ``--phase pre_claim`` probe that never carries
  ``--bootstrap-grant-invocation`` or ``--force`` (Step 2a stays the only
  bootstrap-grant consumption site);
* the probe's outcomes are reported (``ELIGIBLE``, ``INELIGIBLE: {token}``,
  ``GLOBAL_GATE_BLOCK``, ``ELIGIBILITY_GATE_SKIPPED``), the
  ``ORCHESTRATOR STATE`` block carries the eligible / gate-blocked fields, and
  Step 2 first-pass selection skips gate-blocked candidates while Step 2a
  remains binding;
* the dark-mode activation preflight text precedes the instruction that records
  ``DARK_MODE_ACTIVE`` and names ``DARK_MODE_PREFLIGHT_BLOCKED``, ``PENDING``,
  ``EXTERNAL_BLOCKER`` and the optional ``preflight`` activation-record field;
* the dark prompt cites the scope-head preflight, the prompt mirror is
  byte-identical to its template, and the harness manifest checksums of the
  touched mirrors match their LF-normalized content.
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]

_ORCHESTRATORS = {
    "template": _REPO_ROOT / "templates" / "agents" / "_orchestrator.agent.md.tmpl",
    "mirror": _REPO_ROOT / ".github" / "agents" / "_orchestrator.agent.md",
}
_PROMPTS = {
    "template": _REPO_ROOT / "templates" / "prompts" / "feature-flow-dark.prompt.md.tmpl",
    "mirror": _REPO_ROOT / ".github" / "prompts" / "feature-flow-dark.prompt.md",
}
_MANIFEST_PATH = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"

_PROBE_COMMAND = (
    "autoharness gate pipeline-topology --mode agent "
    "--shipment {candidate_shipment_id} --phase pre_claim --json"
)
_RECORD_INSTRUCTION = "record `DARK_MODE_ACTIVE` in session state"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _section(text: str, start_heading: str, end_heading: str) -> str:
    start = text.index(start_heading)
    end = text.index(end_heading, start + len(start_heading))
    return text[start:end]


class Step0ProbeContractTests(unittest.TestCase):
    """Scenario 1: Step 0 per-candidate probe never forces or consumes a grant."""

    def test_step0_probe_has_no_grant_or_force_flag(self) -> None:
        for label, path in _ORCHESTRATORS.items():
            with self.subTest(surface=label):
                step0 = _section(_read(path), "### Step 0: State Assessment", "### Step 1: Route to Stage")
                self.assertIn(_PROBE_COMMAND, step0)
                probe_lines = [ln for ln in step0.splitlines() if "pipeline-topology" in ln]
                self.assertTrue(probe_lines)
                for line in probe_lines:
                    self.assertNotIn("--bootstrap-grant-invocation", line)
                    self.assertNotIn("--force", line)
                self.assertIn("Step 2a", step0)
                self.assertIn("ONLY Orchestrator bootstrap-grant consumption site", step0)


class Step0ReportingContractTests(unittest.TestCase):
    """Scenario 2: outcome vocabulary, state block, and Step 2 first-pass skip."""

    def test_reporting_state_block_and_first_pass_skip(self) -> None:
        for label, path in _ORCHESTRATORS.items():
            with self.subTest(surface=label):
                text = _read(path)
                step0 = _section(text, "### Step 0: State Assessment", "### Step 1: Route to Stage")
                for token in (
                    "`ELIGIBLE`",
                    "`INELIGIBLE: {token}`",
                    "`GLOBAL_GATE_BLOCK: {token}`",
                    "`ELIGIBILITY_GATE_SKIPPED`",
                    "bootstrap grant present",
                ):
                    self.assertIn(token, step0)
                state_block = _section(step0, "ORCHESTRATOR STATE:", "```\n\n")
                self.assertIn("Eligible shipments", state_block)
                self.assertIn("Gate-blocked shipments", state_block)
                self.assertIn("GLOBAL_GATE_BLOCK", state_block)
                step2 = _section(text, "### Step 2: Route to Ship", "### Step 3: Iteration Decision")
                self.assertIn("Gate-blocked first-pass skip", step2)
                self.assertIn("advisory", step2)
                self.assertIn("step 2a", step2)


class DarkPreflightContractTests(unittest.TestCase):
    """Scenario 3: preflight text precedes DARK_MODE_ACTIVE recording."""

    def test_preflight_precedes_activation_record(self) -> None:
        for label, path in _ORCHESTRATORS.items():
            with self.subTest(surface=label):
                text = _read(path)
                end = "## Stash Grouping Heuristic" if label == "template" else "## Domain Context"
                dark = _section(text, "### Dark Factory Mode Trigger Semantics (P-017)", end)
                preflight_at = dark.index("**Activation preflight")
                record_at = dark.index(_RECORD_INSTRUCTION)
                self.assertLess(preflight_at, record_at)
                preflight_text = dark[preflight_at:record_at]
                for token in (
                    "scope head",
                    "DARK_MODE_PREFLIGHT_BLOCKED",
                    "PENDING",
                    "EXTERNAL_BLOCKER",
                    "`preflight`",
                    "not_applicable",
                ):
                    self.assertIn(token, preflight_text)
                self.assertIn("--phase pre_claim", preflight_text)
                self.assertNotIn("--bootstrap-grant-invocation orchestrator", preflight_text)


class DarkPromptAndManifestContractTests(unittest.TestCase):
    """Scenario 4: prompt cites preflight; mirrors stay checksummed and in parity."""

    def test_prompt_preflight_parity_and_manifest_checksums(self) -> None:
        for label, path in _PROMPTS.items():
            with self.subTest(surface=label):
                text = _read(path)
                for token in (
                    "scope head",
                    "DARK_MODE_PREFLIGHT_BLOCKED",
                    "PENDING",
                    "EXTERNAL_BLOCKER",
                ):
                    self.assertIn(token, text)
                self.assertLess(text.index("preflight"), text.index("DARK_MODE_PREFLIGHT_BLOCKED"))
        self.assertEqual(_read(_PROMPTS["template"]), _read(_PROMPTS["mirror"]))
        manifest = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        by_path = {entry["path"]: entry for entry in manifest["artifacts"]}
        for rel in (
            ".github/agents/_orchestrator.agent.md",
            ".github/prompts/feature-flow-dark.prompt.md",
        ):
            with self.subTest(path=rel):
                data = (_REPO_ROOT / rel).read_bytes().replace(b"\r\n", b"\n")
                self.assertEqual(by_path[rel]["checksum"], hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    unittest.main()
