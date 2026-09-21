"""Contract tests for attempt-08 review finding S14/P0 (PR #457).

The installed dogfood ``harness-architect`` actor (``.github/skills/harness-architect/SKILL.md``,
structurally installed by commit 07b4be79) hard-codes ``pytest`` as its Step 5.2
red-phase test command, while the authoritative P-004 policy
(``.github/policies/workflow-policies.md``) and the harness manifest's
``variables_used.TEST_COMMAND`` both require exactly
``PYTHONPATH=src python -m unittest discover -s tests`` -- this repository's real
CI gate (``.github/workflows/ci.yml``, "Run unittest suite" step). autoharness has
no pytest configuration at all (no ``[tool.pytest]`` in ``pyproject.toml``), so the
installed actor's command has never matched anything this repository can actually
run.

``src/autoharness/verify_workspace.py::_derive_template_variables`` already treats
``manifest["variables_used"]`` as authoritative (it seeds the ``variables`` dict
from the manifest FIRST, and every profile-derived default uses
``.setdefault(...)``, which is a no-op once a key already exists -- see
line ~2958, ``variables.setdefault("TEST_COMMAND", str(test["command"]))``). The
manifest's own recorded note (artifacts block, near ``FORMAT_CHECK_COMMAND``)
already documents that ``workspace-profile.yaml``'s ``test.command`` field
(``"pytest"``) is KNOWN-STALE against this repository's real gates, and that
re-running workspace-discovery to correct the profile itself was DELIBERATELY
deferred as an out-of-scope follow-up. This test suite does not reopen that
follow-up (P-021 C1: same-contract-surface only) -- it treats the actually
observed CI command in ``.github/workflows/ci.yml`` as the fourth, independent
"profile canonical test command" signal, precisely because the stored
``workspace-profile.yaml`` field is knowingly excluded from the parity set by
that existing deferral.

The fix corrects only the installed actor's Step 5.2 text (and its manifest
checksum) to the canonical, already-authoritative command, and strengthens the
Step 5.2 red-phase guardrail prose (installed copy AND the source template) so
red-phase evidence requires each generated harness test to fail individually with
its own expected marker -- rejecting zero-discovery, wrong-reason failures,
collection/import/syntax failures, skips/xfails, and passes as valid red
evidence. The template stays environment-agnostic (``{{TEST_COMMAND}}`` /
``{{UNIMPLEMENTED_MARKER}}`` placeholders); no ecosystem runner is hard-coded
into it.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]

_INSTALLED_ACTOR = _REPO_ROOT / ".github" / "skills" / "harness-architect" / "SKILL.md"
_SOURCE_TEMPLATE = _REPO_ROOT / "templates" / "skills" / "harness-architect" / "SKILL.md.tmpl"
_POLICY_REGISTRY = _REPO_ROOT / ".github" / "policies" / "workflow-policies.md"
_MANIFEST = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

_ACTOR_MANIFEST_PATH_KEY = ".github/skills/harness-architect/SKILL.md"

# The canonical, authoritative command per P-004 / the manifest / CI ground truth.
_CANONICAL_TEST_COMMAND = "PYTHONPATH=src python -m unittest discover -s tests"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_manifest() -> dict:
    return yaml.safe_load(_read(_MANIFEST))


def _step_5_2_section(content: str) -> str:
    """Extract the 'Step 5.2: Red phase check' section body."""
    match = re.search(
        r"#### Step 5\.2: Red phase check\s*\n(.*?)(?=\n#### |\n### |\Z)",
        content,
        re.DOTALL,
    )
    assert match, "Step 5.2: Red phase check section not found"
    return match.group(1)


class TemplateEnvironmentAgnosticTests(unittest.TestCase):
    """The source template must stay ecosystem-agnostic."""

    def test_template_exists(self) -> None:
        self.assertTrue(_SOURCE_TEMPLATE.exists())

    def test_template_step_5_2_uses_test_command_placeholder(self) -> None:
        content = _read(_SOURCE_TEMPLATE)
        section = _step_5_2_section(content)
        self.assertIn("{{TEST_COMMAND}}", section)

    def test_template_never_hard_codes_pytest_or_unittest(self) -> None:
        content = _read(_SOURCE_TEMPLATE)
        section = _step_5_2_section(content)
        self.assertNotIn("pytest", section)
        self.assertNotIn("unittest", section)
        self.assertNotIn(_CANONICAL_TEST_COMMAND, section)


class FourSourceParityTests(unittest.TestCase):
    """Installed actor, P-004, manifest variable, and CI ground truth agree."""

    def test_installed_actor_step_5_2_contains_canonical_command(self) -> None:
        content = _read(_INSTALLED_ACTOR)
        section = _step_5_2_section(content)
        self.assertIn(_CANONICAL_TEST_COMMAND, section)
        self.assertNotIn("pytest", section)

    def test_installed_p004_precondition_requires_canonical_command(self) -> None:
        content = _read(_POLICY_REGISTRY)
        # Find the P-004 entry specifically, not just anywhere in the file.
        match = re.search(r"## P-004: Red Phase Before Implementation.*?(?=\n## P-005|\Z)", content, re.DOTALL)
        self.assertIsNotNone(match, "P-004 entry not found in policy registry")
        p004_text = match.group(0)
        self.assertIn(_CANONICAL_TEST_COMMAND, p004_text)
        self.assertNotIn("pytest", p004_text)

    def test_manifest_variables_used_test_command_is_canonical(self) -> None:
        manifest = _load_manifest()
        variables_used = manifest.get("variables_used") or {}
        self.assertEqual(variables_used.get("TEST_COMMAND"), _CANONICAL_TEST_COMMAND)

    def test_ci_workflow_observed_command_is_canonical(self) -> None:
        content = _read(_CI_WORKFLOW)
        self.assertIn(_CANONICAL_TEST_COMMAND, content)
        self.assertIn("Run unittest suite", content)

    def test_all_four_sources_agree_verbatim(self) -> None:
        actor_section = _step_5_2_section(_read(_INSTALLED_ACTOR))
        policy_match = re.search(
            r"## P-004: Red Phase Before Implementation.*?(?=\n## P-005|\Z)",
            _read(_POLICY_REGISTRY),
            re.DOTALL,
        )
        assert policy_match
        manifest = _load_manifest()
        manifest_value = (manifest.get("variables_used") or {}).get("TEST_COMMAND")
        ci_content = _read(_CI_WORKFLOW)

        sources = {
            "installed actor Step 5.2": _CANONICAL_TEST_COMMAND in actor_section,
            "installed P-004": _CANONICAL_TEST_COMMAND in policy_match.group(0),
            "manifest variables_used.TEST_COMMAND": manifest_value == _CANONICAL_TEST_COMMAND,
            "CI workflow (profile canonical/ground-truth command)": _CANONICAL_TEST_COMMAND in ci_content,
        }
        failing = [name for name, ok in sources.items() if not ok]
        self.assertEqual(
            failing,
            [],
            f"sources disagree with canonical command {_CANONICAL_TEST_COMMAND!r}: {failing}",
        )


class ExactInvocationTests(unittest.TestCase):
    """The actor invokes exactly the resolved TEST_COMMAND -- no runner substitution."""

    def test_actor_invokes_exact_resolved_command_no_substitution(self) -> None:
        content = _read(_INSTALLED_ACTOR)
        section = _step_5_2_section(content)
        match = re.search(r"Run `([^`]+)` for the harness tests", section)
        self.assertIsNotNone(match, "expected 'Run `<command>` for the harness tests' in Step 5.2")
        invoked_command = match.group(1)
        self.assertEqual(
            invoked_command,
            _CANONICAL_TEST_COMMAND,
            "actor must invoke exactly the resolved TEST_COMMAND, not a substituted runner",
        )


class RedEvidenceMarkerCorrelationTests(unittest.TestCase):
    """P-004 red evidence requires each test to fail with its own marker."""

    _REJECTED_CONCEPTS = [
        "zero-discovery",
        "wrong-reason",
        "collection/import/syntax",
        "skip",
        "xfail",
    ]

    def test_installed_actor_step_5_2_requires_per_test_marker(self) -> None:
        section = _step_5_2_section(_read(_INSTALLED_ACTOR)).lower()
        self.assertIn("own expected failure marker", section)

    def test_installed_actor_step_5_2_rejects_degenerate_red_evidence(self) -> None:
        section = _step_5_2_section(_read(_INSTALLED_ACTOR)).lower()
        missing = [c for c in self._REJECTED_CONCEPTS if c not in section]
        self.assertEqual(missing, [], f"Step 5.2 does not reject: {missing}")
        # "pass" as a rejected outcome, distinct from the prose verb "passes".
        self.assertIn("false positive", section)

    def test_template_step_5_2_requires_per_test_marker_and_stays_generic(self) -> None:
        section = _step_5_2_section(_read(_SOURCE_TEMPLATE)).lower()
        self.assertIn("own expected failure marker", section)
        missing = [c for c in self._REJECTED_CONCEPTS if c not in section]
        self.assertEqual(missing, [], f"template Step 5.2 does not reject: {missing}")
        self.assertIn("{{test_command}}", section)
        self.assertIn("{{unimplemented_marker}}", section)


class ChecksumAndSingleEntryTests(unittest.TestCase):
    """The installed actor's bytes match its manifest checksum; no duplicates."""

    def test_manifest_has_exactly_one_actor_entry(self) -> None:
        manifest = _load_manifest()
        artifacts = [a for a in (manifest.get("artifacts") or []) if isinstance(a, dict)]
        matches = [a for a in artifacts if a.get("path") == _ACTOR_MANIFEST_PATH_KEY]
        self.assertEqual(
            len(matches),
            1,
            f"expected exactly one manifest artifact entry for {_ACTOR_MANIFEST_PATH_KEY}, found {len(matches)}",
        )

    def test_installed_actor_bytes_match_manifest_checksum(self) -> None:
        import hashlib

        manifest = _load_manifest()
        artifacts = [a for a in (manifest.get("artifacts") or []) if isinstance(a, dict)]
        matches = [a for a in artifacts if a.get("path") == _ACTOR_MANIFEST_PATH_KEY]
        self.assertEqual(len(matches), 1)
        expected_checksum = matches[0].get("checksum")
        actual_checksum = hashlib.sha256(_INSTALLED_ACTOR.read_bytes()).hexdigest()
        self.assertEqual(
            actual_checksum,
            expected_checksum,
            "installed actor bytes do not match the manifest-recorded checksum",
        )


if __name__ == "__main__":
    unittest.main()
