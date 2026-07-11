"""Tests for the copilot-code-review focus instruction artifact and its wiring.

Shipment 086-S / feature 074-F: a dedicated GitHub Copilot code-review focus
instruction file that directs the code-review agent to high-value defects and
away from harness-enforced mechanical concerns, woven through install, tune,
verify, the verifier engine, and both elective agents.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

from autoharness.verify_workspace import FOUNDATION_ASSERTIONS

REPO_ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_PATH = REPO_ROOT / "templates" / "instructions" / "copilot-code-review.instructions.md.tmpl"
DOGFOOD_PATH = REPO_ROOT / ".github" / "instructions" / "copilot-code-review.instructions.md"
INSTALL_SKILL = REPO_ROOT / ".github" / "skills" / "install-harness" / "SKILL.md"
TUNE_SKILL = REPO_ROOT / ".github" / "skills" / "tune-harness" / "SKILL.md"
VERIFY_SKILL = REPO_ROOT / ".github" / "skills" / "verify-harness" / "SKILL.md"
MERGEINSTALL_AGENT = REPO_ROOT / ".github" / "agents" / "auto-mergeinstall.agent.md"
TUNE_AGENT = REPO_ROOT / ".github" / "agents" / "auto-tune.agent.md"

ALLOWED_VARIABLES = {"PROJECT_NAME", "HARNESS_ENFORCED_SUMMARY"}


def _parse_frontmatter(path: Path) -> dict:
    """Return the parsed YAML frontmatter mapping for a Markdown file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise AssertionError(f"{path} has no YAML frontmatter")
    _, frontmatter, _ = text.split("---", 2)
    data = yaml.safe_load(frontmatter)
    if not isinstance(data, dict):
        raise AssertionError(f"{path} frontmatter is not a mapping")
    return data


# Framing phrases that encode the FOCUS-not-blanket-IGNORE design decision.
FOCUS_PHRASES = [
    "Focus on high-value concerns",
    "Secret or credential exposure",
    "Injection",
    "Concurrency",
    "Data-loss",
    "De-prioritize",
    "weakened enforcement",
]


class CopilotCodeReviewTemplateTests(unittest.TestCase):
    def test_template_exists_with_focus_frontmatter_and_variables(self) -> None:
        self.assertTrue(TEMPLATE_PATH.exists(), f"missing template: {TEMPLATE_PATH}")
        content = TEMPLATE_PATH.read_text(encoding="utf-8")

        # Frontmatter: path-scoped, code-review-only via excludeAgent.
        self.assertIn("applyTo: '**'", content)
        self.assertIn("excludeAgent: 'cloud-agent'", content)

        # Base-branch activation caveat must be documented.
        self.assertIn("base branch", content)

        # FOCUS-not-blanket-IGNORE framing.
        for phrase in FOCUS_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, content)

        # Never suppress substantive defects.
        self.assertRegex(content, r"[Nn]ever\s+suppress|not\s+suppression")

        # Both required variables are present.
        self.assertIn("{{PROJECT_NAME}}", content)
        self.assertIn("{{HARNESS_ENFORCED_SUMMARY}}", content)

    def test_template_uses_only_registered_variables(self) -> None:
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        used = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", content))
        unexpected = used - ALLOWED_VARIABLES
        self.assertFalse(
            unexpected,
            f"template uses unregistered variables: {sorted(unexpected)}",
        )

    def test_frontmatter_pins_exclude_agent_and_applyto(self) -> None:
        # Parse the actual YAML frontmatter so a regression that flips ONLY the
        # frontmatter value (while body prose still mentions the old string) is
        # caught. `code-review` would silence the reviewer; `coding-agent` is
        # invalid; only `cloud-agent` is correct.
        for path in (TEMPLATE_PATH, DOGFOOD_PATH):
            with self.subTest(path=path.name):
                fm = _parse_frontmatter(path)
                self.assertEqual(fm.get("excludeAgent"), "cloud-agent")
                self.assertEqual(fm.get("applyTo"), "**")
                self.assertIn("description", fm)

    def test_template_and_dogfood_are_drift_free_after_substitution(self) -> None:
        # Everything except the two variable placeholders must be identical
        # between the product template and the dogfood render.
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        dogfood = DOGFOOD_PATH.read_text(encoding="utf-8")
        resolved = template.replace("{{PROJECT_NAME}}", "autoharness")
        self.assertEqual(resolved.count("{{HARNESS_ENFORCED_SUMMARY}}"), 1)
        prefix, suffix = resolved.split("{{HARNESS_ENFORCED_SUMMARY}}")
        self.assertTrue(dogfood.startswith(prefix), "dogfood prefix diverges from template")
        self.assertTrue(dogfood.endswith(suffix), "dogfood suffix diverges from template")
        summary = dogfood[len(prefix): len(dogfood) - len(suffix)]
        self.assertTrue(summary.strip(), "resolved HARNESS_ENFORCED_SUMMARY is empty")
        self.assertIn("* ", summary)


class CopilotCodeReviewDogfoodTests(unittest.TestCase):
    def test_dogfood_render_present_and_fully_resolved(self) -> None:
        self.assertTrue(DOGFOOD_PATH.exists(), f"missing dogfood render: {DOGFOOD_PATH}")
        content = DOGFOOD_PATH.read_text(encoding="utf-8")

        self.assertIn("applyTo: '**'", content)
        self.assertIn("excludeAgent: 'cloud-agent'", content)
        self.assertIn("base branch", content)
        for phrase in FOCUS_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, content)

        # No unresolved placeholders in the installed render.
        leftover = re.findall(r"\{\{[A-Z0-9_]+\}\}", content)
        self.assertFalse(leftover, f"unresolved placeholders in dogfood render: {leftover}")

        # Resolved project name.
        self.assertIn("autoharness", content)


class CopilotCodeReviewWiringTests(unittest.TestCase):
    def test_install_harness_registers_instruction_and_variable(self) -> None:
        content = INSTALL_SKILL.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Registration line exists, is GitHub-conditional, and documents excludeAgent.
        reg_lines = [ln for ln in lines if "copilot-code-review.instructions.md" in ln]
        self.assertTrue(reg_lines, "install-harness does not register the instruction")
        self.assertTrue(
            any(("github.com" in ln) or ("GitHub" in ln) for ln in reg_lines),
            "registration is not gated to GitHub-hosted workspaces",
        )
        self.assertTrue(
            any("excludeAgent" in ln for ln in reg_lines),
            "registration does not document excludeAgent scoping",
        )

        # Variable-resolution row exists with a non-empty (bulleted) default so
        # installs never leave the placeholder unresolved.
        var_rows = [
            ln for ln in lines
            if "{{HARNESS_ENFORCED_SUMMARY}}" in ln and ln.lstrip().startswith("|")
        ]
        self.assertTrue(var_rows, "HARNESS_ENFORCED_SUMMARY variable-resolution row missing")
        self.assertIn("*", var_rows[0], "variable-resolution row lacks a bulleted default")

    def test_tune_harness_has_drift_check(self) -> None:
        content = TUNE_SKILL.read_text(encoding="utf-8")
        self.assertIn("copilot-code-review.instructions.md", content)

    def test_verify_harness_has_coherence_check(self) -> None:
        content = VERIFY_SKILL.read_text(encoding="utf-8")
        self.assertIn("copilot-code-review.instructions.md", content)

    def test_elective_agents_reference_capability_and_base_branch(self) -> None:
        for agent_path in (MERGEINSTALL_AGENT, TUNE_AGENT):
            with self.subTest(agent=agent_path.name):
                content = agent_path.read_text(encoding="utf-8")
                self.assertIn("copilot-code-review.instructions.md", content)
        # The activation caveat lives with the install/discover agent.
        mergeinstall = MERGEINSTALL_AGENT.read_text(encoding="utf-8")
        self.assertIn("base branch", mergeinstall)


class CopilotCodeReviewVerifierTests(unittest.TestCase):
    def test_foundation_assertion_registered(self) -> None:
        entries = [
            a
            for a in FOUNDATION_ASSERTIONS
            if a.get("path") == ".github/instructions/copilot-code-review.instructions.md"
        ]
        self.assertTrue(
            entries,
            "FOUNDATION_ASSERTIONS missing copilot-code-review.instructions.md entry",
        )
        must_contain = entries[0]["must_contain"]
        joined = "\n".join(must_contain)
        self.assertIn("excludeAgent", joined)
        self.assertIn("Focus on high-value concerns", joined)


if __name__ == "__main__":
    unittest.main()
