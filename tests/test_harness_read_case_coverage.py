"""Unit C, task C5 (187.005-T): Proof G case-ID coverage for the containment reader.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "C5: Linux-native gate and case coverage".

Every Proof G case ID G01 to G32 appears in a test name in the four containment
test modules. G31 is Linux-only (every G31 test is skipped on Windows, and
never elsewhere). Every other ID has a variant with no host-conditional skip
decorator, so it runs on both hosts (Windows symlink sub-cases may still skip
at run time without symlink privilege; that is recorded skip accounting, not a
host condition).

Structural test: it reads the test modules' source with ``ast``, reaches no
RED-phase stub and is recorded outside any roster. It is not in the C5 CI
evidence step's module list (IM-14-F26); it runs in the canonical suite.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
# Keep in sync with the module list of the "Linux-native containment gate
# (IM-01)" step in .github/workflows/ci.yml (that step adds the audit module).
CONTAINMENT_MODULES = (
    "test_harness_read_lexical.py",
    "test_harness_read_containment.py",
    "test_harness_read_bounds.py",
    "test_harness_read_nonregular.py",
)
CASE_IDS = tuple(f"G{number:02d}" for number in range(1, 33))
CASE_NAME = re.compile(r"^test_(G\d\d)[a-z]?(?:_|$)")
LINUX_ONLY_IDS = frozenset({"G31"})


def _host_skip_decorators(node: ast.FunctionDef | ast.ClassDef) -> list[str]:
    found = []
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
        if name in {"skip", "skipIf", "skipUnless", "expectedFailure"}:
            found.append(ast.unparse(decorator))
    return found


def _in_body_skips(node: ast.FunctionDef) -> list[str]:
    """Direct ``skipTest`` calls in a test body (``require_symlinks`` is the recorded privilege skip)."""
    return [
        ast.unparse(call)
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "skipTest"
    ]


def collect_case_tests() -> dict[str, list[tuple[str, list[str]]]]:
    """Map each case ID to its ``(module::Class.test, host conditions)`` entries.

    Only test methods defined directly in a module-level class count; a host
    condition is a skip decorator on the method or its class, or a direct
    ``skipTest`` call in the method body.
    """
    by_case: dict[str, list[tuple[str, list[str]]]] = {}
    for module in CONTAINMENT_MODULES:
        tree = ast.parse((TESTS_DIR / module).read_text(encoding="utf-8"))
        for cls in tree.body:
            if not isinstance(cls, ast.ClassDef):
                continue
            class_conditions = _host_skip_decorators(cls)
            for node in cls.body:
                if not isinstance(node, ast.FunctionDef):
                    continue
                match = CASE_NAME.match(node.name)
                if match:
                    conditions = class_conditions + _host_skip_decorators(node) + _in_body_skips(node)
                    by_case.setdefault(match.group(1), []).append(
                        (f"{module}::{cls.name}.{node.name}", conditions)
                    )
    return by_case


class ProofGCaseCoverageTests(unittest.TestCase):
    def test_structural_every_case_id_has_a_named_test(self) -> None:
        by_case = collect_case_tests()
        missing = [case for case in CASE_IDS if case not in by_case]
        self.assertEqual(missing, [])
        self.assertEqual(sorted(by_case), list(CASE_IDS))

    def test_structural_g31_is_linux_only(self) -> None:
        entries = collect_case_tests()["G31"]
        for name, decorators in entries:
            with self.subTest(test=name):
                self.assertEqual(len(decorators), 1, decorators)
                self.assertRegex(decorators[0], r"^unittest\.skipIf\(IS_WINDOWS\b")

    def test_structural_every_other_case_runs_on_both_hosts(self) -> None:
        by_case = collect_case_tests()
        for case in CASE_IDS:
            if case in LINUX_ONLY_IDS:
                continue
            with self.subTest(case=case):
                unconditional = [name for name, decorators in by_case[case] if not decorators]
                self.assertTrue(unconditional, f"{case} has no variant that runs on both hosts")


if __name__ == "__main__":
    unittest.main()
