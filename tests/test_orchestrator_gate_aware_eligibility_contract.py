"""Contract tests for the 202-F gate-aware Orchestrator eligibility (P1) and
dark-mode activation preflight (P3) text (shipment 209-S, unit 202.004-T).

These tests pin the load-bearing instruction text in BOTH the Orchestrator
template and its installed dogfood mirror, plus the ``feature-flow-dark``
prompt template and its installed mirror (four scenarios):

1. Step 0 runs a per-candidate ``--phase pre_claim`` probe that never carries
   ``--bootstrap-grant-invocation`` or ``--force`` (Step 2a stays the only
   bootstrap-grant consumption site).
2. The probe's outcomes are reported (``ELIGIBLE``, ``INELIGIBLE: {token}``,
   ``GLOBAL_GATE_BLOCK``, ``ELIGIBILITY_GATE_SKIPPED``, fail-closed
   ``GATE_PROBE_ERROR``), the ``ORCHESTRATOR STATE`` block carries the new
   fields, Step 2 first-pass selection skips only explicitly gate-blocked
   candidates with its three carve-outs while Step 2a stays binding, and the
   new regions are textually identical in the template and the mirror.
3. The dark-mode activation preflight text precedes the instruction that
   records ``DARK_MODE_ACTIVE`` and names ``DARK_MODE_PREFLIGHT_BLOCKED``,
   ``PENDING``, ``EXTERNAL_BLOCKER`` and the optional ``preflight`` field.
4. The dark prompt cites the scope-head preflight, the prompt mirror is
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
    "template": (
        _REPO_ROOT / "templates" / "prompts" / "feature-flow-dark.prompt.md.tmpl"
    ),
    "mirror": _REPO_ROOT / ".github" / "prompts" / "feature-flow-dark.prompt.md",
}
_MANIFEST_PATH = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"

_STEP0 = "### Step 0: State Assessment"
_STEP1 = "### Step 1: Route to Stage"
_STEP2 = "### Step 2: Route to Ship"
_STEP3 = "### Step 3: Iteration Decision"
_DARK = "### Dark Factory Mode Trigger Semantics (P-017)"
_PROBE_COMMAND = (
    "autoharness gate pipeline-topology --mode agent "
    "--shipment {candidate_shipment_id} --phase pre_claim --json"
)
_RECORD_INSTRUCTION = "record `DARK_MODE_ACTIVE` in session state"
_FORBIDDEN_FLAGS = ("--bootstrap-grant-invocation", "--force")


def _read(path: Path) -> str:
    """Read UTF-8 text with CRLF working-tree endings normalized to LF."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _orchestrator(path: Path) -> str:
    """Orchestrator text with the template's only variable rendered."""
    return _read(path).replace("{{STATUS_QUEUED}}", "queued")


def _between(text: str, start: str, end: str, where: Path) -> str:
    """Slice ``text`` from ``start`` up to (excluding) the next ``end``.

    Fails with an actionable assertion rather than a bare ValueError.
    """
    start_at = text.find(start)
    if start_at < 0:
        raise AssertionError(f"anchor {start!r} not found in {where}")
    end_at = text.find(end, start_at + len(start))
    if end_at < 0:
        raise AssertionError(f"anchor {end!r} not found after {start!r} in {where}")
    return text[start_at:end_at]


def _dark_section(text: str, where: Path) -> str:
    return _between(text, _DARK, "\n## ", where)


def _regions(text: str, where: Path) -> dict[str, str]:
    """The three new Orchestrator regions that must match across surfaces."""
    return {
        "step 2b": _between(text, "2b. **Gate-aware eligibility probe", "\n3. Check stash", where),
        "step 2 skip": _between(
            text, "   * **Gate-blocked first-pass skip", "\n   * **Scope-reconstruction caveat**", where
        ),
        "preflight": _between(
            text, "**Activation preflight", "Only after the activation preflight above", where
        ),
    }


def _flag_lines_are_prohibitions(testcase: unittest.TestCase, text: str) -> None:
    """Every line naming a grant/force flag must be a NEVER/never prohibition."""
    for line in text.splitlines():
        if any(flag in line for flag in _FORBIDDEN_FLAGS):
            testcase.assertTrue(
                "NEVER" in line or "never" in line,
                f"flag mentioned outside a prohibition: {line.strip()[:120]}",
            )


class Step0ProbeContractTests(unittest.TestCase):
    """Scenario 1: the Step 0 probe never forces or consumes a bootstrap grant."""

    def test_step0_probe_has_no_grant_or_force_flag(self) -> None:
        for label, path in _ORCHESTRATORS.items():
            with self.subTest(surface=label):
                step0 = _between(_orchestrator(path), _STEP0, _STEP1, path)
                self.assertIn(_PROBE_COMMAND, step0)
                command_lines = [ln for ln in step0.splitlines() if _PROBE_COMMAND in ln]
                self.assertEqual(len(command_lines), 1)
                for flag in _FORBIDDEN_FLAGS:
                    self.assertNotIn(flag, command_lines[0])
                _flag_lines_are_prohibitions(self, step0)
                self.assertIn("NEVER passes `--bootstrap-grant-invocation`", step0)
                self.assertIn("ONLY Orchestrator bootstrap-grant consumption site", step0)


class Step0ReportingContractTests(unittest.TestCase):
    """Scenario 2: outcome vocabulary, state block, Step 2 skip, mirror parity."""

    def test_reporting_state_block_first_pass_skip_and_parity(self) -> None:
        regions: dict[str, dict[str, str]] = {}
        for label, path in _ORCHESTRATORS.items():
            with self.subTest(surface=label):
                text = _orchestrator(path)
                regions[label] = _regions(text, path)
                step0 = _between(text, _STEP0, _STEP1, path)
                for token in (
                    "`ELIGIBLE`",
                    "`INELIGIBLE: {token}`",
                    "`INELIGIBLE: GATE_PROBE_ERROR`",
                    "`INELIGIBLE: GATE_INVALID`",
                    "`GLOBAL_GATE_BLOCK: {token}`",
                    "`ELIGIBILITY_GATE_SKIPPED`",
                    "`PREDECESSOR_CLOSURE_INCOMPLETE`",
                    "bootstrap grant present",
                    "This sub-step is read-only",
                    "every `blocks` predecessor of the candidate has shipped",
                    "does not exclude the candidate from probing",
                    "Every `INELIGIBLE` variant, including `GATE_PROBE_ERROR`",
                    "`active_shipment_invariant`",
                    "`detect_before_consistency`",
                    "`backlog_state`",
                    "`worktree_topology`",
                    "`worktree_cleanliness`",
                    "`branch_ownership`",
                ):
                    self.assertIn(token, step0)
                state_block = _between(step0, "ORCHESTRATOR STATE:", "```\n\n", path)
                for field in (
                    "Eligible shipments",
                    "Gate-blocked shipments",
                    "Unevaluated shipments",
                    "GLOBAL_GATE_BLOCK",
                ):
                    self.assertIn(field, state_block)
                skip = regions[label]["step 2 skip"]
                for token in (
                    "never skipped for want of a result",
                    "(a) a candidate reported `INELIGIBLE: {token} (bootstrap grant present",
                    "(b) while a `DARK_MODE_ACTIVE` run is in effect",
                    "(c) an operator-named `ship {id}` is never substituted",
                    "remains the sole claim authority",
                    "Carve-out (a) takes precedence over (c)",
                ):
                    self.assertIn(token, skip)
                self.assertIn("Gate-blocked first-pass skip", _between(text, _STEP2, _STEP3, path))
        # The mirror hand-maintains these regions; they must not drift apart.
        for name, template_text in regions["template"].items():
            with self.subTest(region=name):
                self.assertEqual(template_text, regions["mirror"][name])


class DarkPreflightContractTests(unittest.TestCase):
    """Scenario 3: the preflight text precedes DARK_MODE_ACTIVE recording."""

    def test_preflight_precedes_activation_record(self) -> None:
        for label, path in _ORCHESTRATORS.items():
            with self.subTest(surface=label):
                dark = _dark_section(_orchestrator(path), path)
                preflight_at = dark.find("**Activation preflight")
                record_at = dark.find(_RECORD_INSTRUCTION)
                self.assertGreaterEqual(preflight_at, 0)
                self.assertGreater(record_at, preflight_at)
                preflight_text = dark[preflight_at:record_at]
                for token in (
                    "scope head",
                    "DARK_MODE_PREFLIGHT_BLOCKED",
                    "do NOT record `DARK_MODE_ACTIVE`",
                    "PENDING",
                    "EXTERNAL_BLOCKER",
                    "`preflight`",
                    "never read as a pass",
                    "not_applicable",
                    "head: active (resume)",
                    "halts like any other blocked head",
                    "none of which is itself `EXTERNAL_BLOCKER`",
                    "not_applicable (no shipment in scope)",
                    "skipped (ELIGIBILITY_GATE_SKIPPED)",
                    "--phase pre_claim",
                ):
                    self.assertIn(token, preflight_text)
                _flag_lines_are_prohibitions(self, preflight_text)
                self.assertIn("| `preflight` (optional) |", dark)
                self.assertIn("the head is eligible or already `active`", dark[preflight_at:])


class DarkPromptAndManifestContractTests(unittest.TestCase):
    """Scenario 4: the prompt cites the preflight; mirrors stay checksummed."""

    def test_prompt_preflight_parity_and_manifest_checksums(self) -> None:
        for label, path in _PROMPTS.items():
            with self.subTest(surface=label):
                text = _read(path)
                for token in (
                    "scope head",
                    "`pipeline-topology --phase pre_claim`",
                    "DARK_MODE_PREFLIGHT_BLOCKED",
                    "PENDING",
                    "EXTERNAL_BLOCKER",
                    "`preflight`",
                    "has not yet shipped",
                    "already `active` on a resume",
                ):
                    self.assertIn(token, text)
                self.assertLess(
                    text.index("preflights the scope head"),
                    text.index("records `DARK_MODE_ACTIVE` only when the head passes"),
                )
        self.assertEqual(_read(_PROMPTS["template"]), _read(_PROMPTS["mirror"]))

        manifest = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        by_path = {entry["path"]: entry for entry in manifest["artifacts"]}
        for rel in (
            ".github/agents/_orchestrator.agent.md",
            ".github/prompts/feature-flow-dark.prompt.md",
        ):
            with self.subTest(path=rel):
                self.assertIn(rel, by_path, f"{rel} missing from the harness manifest")
                data = (_REPO_ROOT / rel).read_bytes().replace(b"\r\n", b"\n")
                self.assertEqual(by_path[rel].get("checksum"), hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    unittest.main()
