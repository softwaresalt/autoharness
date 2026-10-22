"""Text-contract tests for 216.006-T: build-feature docs-route execution and harvest/Stage candidate wording."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
BUILD_FEATURE = _ROOT / "templates" / "skills" / "build-feature" / "SKILL.md.tmpl"
HARVEST = {
    "template": _ROOT / "templates" / "skills" / "harvest" / "SKILL.md.tmpl",
    "mirror": _ROOT / ".github" / "skills" / "harvest" / "SKILL.md",
}
STAGE = {
    "template": _ROOT / "templates" / "agents" / "_stage.agent.md.tmpl",
    "mirror": _ROOT / ".github" / "agents" / "_stage.agent.md",
}


def collapsed(path: Path) -> str:
    text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    return re.sub(r"\s+", " ", text)


class BuildFeatureDocsRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = collapsed(BUILD_FEATURE)

    def test_states_both_invocation_conditions(self) -> None:
        self.assertIn("Invoked by the ship agent when a task has the `harness-ready` label", self.text)
        self.assertIn("the `harness-verification-gated` label (docs-only route", self.text)
        self.assertIn("Not invoked directly by users.", self.text)

    def test_docs_route_executes_recorded_commands_and_never_invents_red(self) -> None:
        section = self.text[self.text.index("## Docs Route") :]
        section = section[: section.index("## Required Protocol")]
        for needle in (
            "recorded executable verification gate commands", "recorded working directory",
            "never invents a RED phase", "never creates a stub, test or harness",
            "owned prose `.md` paths", "never by weakening or editing the recorded gate",
            "autoharness harness docs-only-check",
        ):
            self.assertIn(needle, section)

    def test_code_route_text_unchanged(self) -> None:
        for needle in (
            "Implement a requested feature by continuously looping against a strict, compiling, but failing test harness until all tests pass.",
            "* `harness_cmd`: (Required) The test command to run",
            "After 5 failures → mark task as BLOCKED → exit",
        ):
            self.assertIn(needle, self.text)


class CandidateWordingTests(unittest.TestCase):
    def test_harvest_and_stage_declare_surface_none_and_never_apply_route_labels(self) -> None:
        for group, paths in (("harvest", HARVEST), ("stage", STAGE)):
            for which, path in paths.items():
                with self.subTest(group=group, source=which):
                    text = collapsed(path)
                    start = text.index("Docs-route candidates")
                    block = text[start : start + 700]
                    for needle in (
                        "`harness-surface:none`", "docs-route candidate", "prose `.md` under the docs root",
                        "Never apply either route label", "`harness-ready`", "`harness-verification-gated`",
                        "only harness-architect applies a route label",
                    ):
                        self.assertIn(needle, block)

    def test_two_hour_rule_text_unchanged(self) -> None:
        self.assertIn("* **2-Hour Rule**: Fewer than 3 files, fewer than 5 functions, fewer than 4 test scenarios", collapsed(STAGE["template"]))


if __name__ == "__main__":
    unittest.main()
