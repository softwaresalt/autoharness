"""AST-based structural regression guard: no module under ``tests/`` may
construct ``tempfile.TemporaryDirectory(dir=Path.cwd())`` -- creating a
temp workspace INSIDE the live repository working tree (141.002-T /
141.003-T / 141.004-T, shipment 149-S).

Uses an AST visitor rather than a line regex, per
docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md:
a regex only encodes the textual shapes its author anticipated, while an AST
visitor keyed on the underlying call structure is robust to line-wrapping and
argument-order variations.

The guard asserts the ABSENCE of the anti-pattern (not the presence of a
fix), and NAMES every offending file and line in its failure message
(amendment A3). It ships with an EXPLICIT, SHRINKING allowlist (amendment
A4): a module on the allowlist is exempt from the anti-pattern check, but the
allowlist itself is asserted to be exactly the expected set at each stage, so
it cannot silently grow or survive as a permanent escape hatch.

Scope is EVERY ``*.py`` file under ``tests/``, scanned RECURSIVELY (Copilot
review finding on PR #390, thread PRRT_kwDORzpWpM6bWClz): the guard's own
stated invariant is "no module under tests/", not "no top-level
test_*.py-named module" -- a non-recursive ``test_*.py``-only glob would
silently exempt any nested test package or non-``test_``-prefixed helper
module from the very check it exists to enforce.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_DIR = _REPO_ROOT / "tests"

# Amendment A4: shrinks as 141.002-T / 141.003-T / 141.004-T land. This task
# (141.004-T) empties it -- no allowlist entry survives as a permanent
# escape hatch.
ALLOWLIST: frozenset[str] = frozenset()


class _CwdAnchoredTempDirVisitor(ast.NodeVisitor):
    """Find every ``tempfile.TemporaryDirectory(...)`` call whose ``dir=``
    keyword argument is (or contains, as a call) ``Path.cwd()`` / ``cwd()``.
    """

    def __init__(self) -> None:
        self.offending_lines: list[int] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 - ast.NodeVisitor API
        if _is_temporary_directory_call(node):
            for kw in node.keywords:
                if kw.arg == "dir" and _is_cwd_call(kw.value):
                    self.offending_lines.append(node.lineno)
        self.generic_visit(node)


def _is_temporary_directory_call(node: ast.Call) -> bool:
    """True if ``node`` calls ``tempfile.TemporaryDirectory`` (attribute
    access) or a bare ``TemporaryDirectory`` (direct import)."""
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "TemporaryDirectory":
        return True
    if isinstance(func, ast.Name) and func.id == "TemporaryDirectory":
        return True
    return False


def _is_cwd_call(node: ast.expr) -> bool:
    """True if ``node`` is a call to ``.cwd()`` -- ``Path.cwd()``,
    ``pathlib.Path.cwd()``, or a bare ``cwd()`` (direct import), reached
    ANYWHERE in the expression (e.g. as one operand of a ``/`` path-join),
    matching the AST-over-regex principle: walk the tree for the underlying
    call, not a specific textual shape."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Attribute) and func.attr == "cwd":
                return True
            if isinstance(func, ast.Name) and func.id == "cwd":
                return True
    return False


def _find_offenses(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    visitor = _CwdAnchoredTempDirVisitor()
    visitor.visit(tree)
    return visitor.offending_lines


class TestSuiteIsolationContract(unittest.TestCase):
    """No module under tests/ may anchor a temp workspace inside the live
    working tree via ``tempfile.TemporaryDirectory(dir=Path.cwd())``."""

    def test_no_cwd_anchored_temp_directories_outside_allowlist(self) -> None:
        offenses: list[str] = []
        for path in sorted(_TESTS_DIR.rglob("*.py")):
            if path.name in ALLOWLIST:
                continue
            for lineno in _find_offenses(path):
                offenses.append(f"{path.relative_to(_REPO_ROOT).as_posix()}:{lineno}")

        self.assertFalse(
            offenses,
            "tempfile.TemporaryDirectory(dir=Path.cwd()) anchors a temp "
            "workspace inside the live working tree -- creates cross-test "
            "pollution risk. Offending site(s):\n" + "\n".join(offenses),
        )

    def test_allowlist_is_exactly_expected(self) -> None:
        """Pins the allowlist so it cannot silently grow or survive as a
        permanent escape hatch (amendment A4). Final state (post-141.004-T):
        EMPTY -- no module may anchor a temp workspace inside the live
        working tree via dir=Path.cwd()."""
        self.assertEqual(ALLOWLIST, frozenset())

    def test_guard_detects_a_known_offending_shape(self) -> None:
        """Non-vacuity: the visitor must actually be able to detect the
        anti-pattern it exists to catch."""
        sample = "import tempfile\nfrom pathlib import Path\n\ndef f():\n    with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:\n        pass\n"
        tree = ast.parse(sample)
        visitor = _CwdAnchoredTempDirVisitor()
        visitor.visit(tree)
        self.assertEqual(visitor.offending_lines, [5])

    def test_guard_ignores_anchored_or_plain_temp_directories(self) -> None:
        """Non-vacuity (negative case): the authorized replacements (plain
        system-temp, or an explicit non-cwd anchor) must NOT be flagged."""
        sample = (
            "import tempfile\n"
            "from pathlib import Path\n\n"
            "def f():\n"
            "    with tempfile.TemporaryDirectory() as t1:\n"
            "        pass\n"
            "    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as t2:\n"
            "        pass\n"
        )
        tree = ast.parse(sample)
        visitor = _CwdAnchoredTempDirVisitor()
        visitor.visit(tree)
        self.assertEqual(visitor.offending_lines, [])


if __name__ == "__main__":
    unittest.main()
