"""AST-based structural regression guard: no module under ``tests/`` may
construct ``tempfile.TemporaryDirectory(dir=Path.cwd())`` -- creating a
temp workspace INSIDE the live repository working tree (141.002-T /
141.003-T / 141.004-T, shipment 149-S).

ALSO (144.004-T, shipment 152-S): no module under ``tests/`` may call
``patch.dict(os.environ, ...)`` (however spelled -- ``patch.dict``,
``mock.patch.dict``, ``unittest.mock.patch.dict``, any import alias, string
literal ``'os.environ'`` first argument, decorator or context-manager form)
or ``os.environ.clear()`` -- the destructive clear-then-update / full-clear
restore path that destroys any blank-valued (``""``) environment variable on
Windows (``SetEnvironmentVariableW`` empty-value-delete semantics). The
authorized replacement is ``tests/_env_patch.py``'s ``patched_environ(...)``
restore-by-diff helper, which is scanned by this SAME guard on EQUAL TERMS
with every other module under ``tests/`` -- it needs no exemption because it
implements targeted ``os.environ[k] = v`` / ``del os.environ[k]``, which the
guard does not forbid (amendment A1R).

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


# --------------------------------------------------------------------------
# 144.004-T (shipment 152-S): forbid patch.dict(os.environ, ...) / clear()
# --------------------------------------------------------------------------

# Amendment A1R (BINDING): EMPTY, with NO exemption for tests/_env_patch.py.
# The helper implements targeted os.environ[k]=v / del os.environ[k], which
# this guard does not forbid -- it needs no exemption because it never
# performs the forbidden forms below. A path exemption would make the one
# file most likely to reintroduce the defect the one file in which the
# destructive forms are permitted, inverting the guard's entire purpose.
ENV_MUTATION_ALLOWLIST: frozenset[str] = frozenset()


def _resolve_dotted(expr: ast.expr, alias_map: dict[str, str]) -> str | None:
    """Resolve a ``Name``/``Attribute`` chain to its canonical dotted string,
    substituting the ORIGIN of any imported/aliased name (e.g. ``p`` bound by
    ``from unittest.mock import patch as p`` resolves to
    ``"unittest.mock.patch"``, not the literal local name ``"p"``) so the
    guard is structurally robust to import aliasing, not just to literal
    spelling. Falls back to the literal name for anything not tracked as an
    import (e.g. locals in a synthetic test snippet with no import
    statement), which is exactly what lets the guard's own non-vacuity
    samples exercise the forbidden shapes without needing a full import
    preamble."""
    if isinstance(expr, ast.Name):
        return alias_map.get(expr.id, expr.id)
    if isinstance(expr, ast.Attribute):
        base = _resolve_dotted(expr.value, alias_map)
        if base is None:
            return None
        return f"{base}.{expr.attr}"
    return None


class _ImportAliasCollector(ast.NodeVisitor):
    """Collects every ``import``/``from ... import`` binding anywhere in the
    module (not just at module top level -- a function-local import is still
    a valid Python idiom) into ``alias_map``: local bound name -> canonical
    dotted origin."""

    def __init__(self) -> None:
        self.alias_map: dict[str, str] = {}

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            bound = alias.asname or alias.name.split(".")[0]
            origin = alias.asname and alias.name or alias.name.split(".")[0]
            self.alias_map[bound] = origin
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        module = node.module or ""
        for alias in node.names:
            bound = alias.asname or alias.name
            origin = f"{module}.{alias.name}" if module else alias.name
            self.alias_map[bound] = origin
        self.generic_visit(node)


def _collect_alias_map(tree: ast.AST) -> dict[str, str]:
    collector = _ImportAliasCollector()
    collector.visit(tree)
    return collector.alias_map


def _is_os_environ_expr(node: ast.expr, alias_map: dict[str, str]) -> bool:
    """True if ``node`` is ``os.environ`` (attribute access, through any
    import alias of ``os``) or the string literal ``'os.environ'``."""
    if isinstance(node, ast.Constant) and node.value == "os.environ":
        return True
    return _resolve_dotted(node, alias_map) == "os.environ"


class _EnvMutationVisitor(ast.NodeVisitor):
    """Find every ``patch.dict(os.environ, ...)`` (however spelled: bare,
    ``mock.``-qualified, ``unittest.mock.``-qualified, any import alias,
    string-literal first argument, decorator or context-manager form) and
    every ``os.environ.clear()`` call."""

    def __init__(self, alias_map: dict[str, str]) -> None:
        self.alias_map = alias_map
        self.offending_lines: list[int] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        resolved_func = _resolve_dotted(node.func, self.alias_map)
        if resolved_func is not None and resolved_func.endswith("patch.dict"):
            if node.args and _is_os_environ_expr(node.args[0], self.alias_map):
                self.offending_lines.append(node.lineno)
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "clear":
            if _is_os_environ_expr(node.func.value, self.alias_map):
                self.offending_lines.append(node.lineno)
        self.generic_visit(node)


def _find_env_mutation_offenses(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    alias_map = _collect_alias_map(tree)
    visitor = _EnvMutationVisitor(alias_map)
    visitor.visit(tree)
    return visitor.offending_lines


class EnvMutationContract(unittest.TestCase):
    """No module under tests/ may destructively mutate the whole
    ``os.environ`` mapping via ``patch.dict(os.environ, ...)`` or
    ``os.environ.clear()`` -- both clear-then-restore the ENTIRE mapping,
    which destroys any blank-valued (``""``) variable on Windows. The
    authorized replacement is ``tests/_env_patch.py``'s ``patched_environ``
    restore-by-diff helper (144.001-T/144.002-T/144.003-T, shipment 152-S)."""

    def test_no_env_mutation_outside_allowlist(self) -> None:
        offenses: list[str] = []
        for path in sorted(_TESTS_DIR.rglob("*.py")):
            if path.name in ENV_MUTATION_ALLOWLIST:
                continue
            for lineno in _find_env_mutation_offenses(path):
                offenses.append(f"{path.relative_to(_REPO_ROOT).as_posix()}:{lineno}")

        self.assertFalse(
            offenses,
            "patch.dict(os.environ, ...) / os.environ.clear() destructively "
            "clears-then-restores the ENTIRE os.environ mapping, destroying "
            "any blank-valued variable on Windows -- use "
            "tests/_env_patch.py's patched_environ(...) instead. Offending "
            "site(s):\n" + "\n".join(offenses),
        )

    def test_env_mutation_allowlist_is_exactly_expected(self) -> None:
        """Pins the allowlist so it cannot silently grow into an escape
        hatch (amendment A1R). Final state: EMPTY -- including
        tests/_env_patch.py, which is scanned on equal terms with every
        other module because it implements only the authorized targeted
        set/delete forms, never the forbidden bulk-clear forms."""
        self.assertEqual(ENV_MUTATION_ALLOWLIST, frozenset())

    def test_guard_detects_every_known_offending_shape(self) -> None:
        """Non-vacuity POSITIVE (R5R): every forbidden shape named by the
        task -- context-manager form, decorator form, aliased import (both
        ``from ... import patch as p`` and ``import unittest.mock as um``),
        multi-line/split-argument call, string-literal 'os.environ' first
        argument, and os.environ.clear() -- is detected. Also doubles as the
        task's required "guard provably fails if a migrated site is
        reverted" demonstration: every one of these shapes is exactly what a
        reverted 144.003-T site would look like, exercised here via a
        synthetic source string rather than by reverting committed code."""
        sample = (
            "import unittest.mock as um\n"
            "from unittest.mock import patch\n"
            "from unittest.mock import patch as p\n"
            "import os\n"
            "\n"
            "\n"
            "@patch.dict(os.environ, {'A': '1'})  # OFFENSE decorator form\n"
            "def decorated():\n"
            "    pass\n"
            "\n"
            "\n"
            "def context_manager_form():\n"
            "    with patch.dict(os.environ, {'B': '2'}):  # OFFENSE context-manager form\n"
            "        pass\n"
            "\n"
            "\n"
            "def aliased_import_form():\n"
            "    with p.dict(os.environ, {'C': '3'}):  # OFFENSE aliased import (patch as p)\n"
            "        pass\n"
            "\n"
            "\n"
            "def module_alias_form():\n"
            "    with um.patch.dict(os.environ, {'D': '4'}):  # OFFENSE module alias (unittest.mock as um)\n"
            "        pass\n"
            "\n"
            "\n"
            "def multiline_split_form():\n"
            "    with patch.dict(  # OFFENSE multi-line/split-argument call\n"
            "        'os.environ',\n"
            "        {'E': '5'},\n"
            "        clear=False,\n"
            "    ):\n"
            "        pass\n"
            "\n"
            "\n"
            "def string_literal_form():\n"
            "    with patch.dict('os.environ', {'F': '6'}):  # OFFENSE string-literal first argument\n"
            "        pass\n"
            "\n"
            "\n"
            "def clear_form():\n"
            "    os.environ.clear()  # OFFENSE os.environ.clear()\n"
        )
        expected = sorted(
            i + 1 for i, line in enumerate(sample.splitlines()) if "# OFFENSE" in line
        )
        self.assertEqual(len(expected), 7, "sanity check: sample must carry exactly 7 markers")
        tree = ast.parse(sample)
        alias_map = _collect_alias_map(tree)
        visitor = _EnvMutationVisitor(alias_map)
        visitor.visit(tree)
        self.assertEqual(sorted(visitor.offending_lines), expected)

    def test_guard_ignores_authorized_forms(self) -> None:
        """Non-vacuity NEGATIVE (R5R, MANDATORY -- without it an empty
        allowlist is unworkable): patched_environ(...), patch.dict on some
        OTHER dict, os.environ[k] = v, and del os.environ[k] must NOT be
        flagged."""
        sample = (
            "from unittest.mock import patch\n"
            "import os\n"
            "from _env_patch import patched_environ\n"
            "\n"
            "\n"
            "def uses_helper():\n"
            "    with patched_environ(X='1'):\n"
            "        pass\n"
            "\n"
            "\n"
            "def patches_some_other_dict():\n"
            "    some_other_dict = {}\n"
            "    with patch.dict(some_other_dict, {'A': '1'}):\n"
            "        pass\n"
            "\n"
            "\n"
            "def sets_a_key():\n"
            "    os.environ['X'] = '1'\n"
            "\n"
            "\n"
            "def deletes_a_key():\n"
            "    del os.environ['X']\n"
        )
        tree = ast.parse(sample)
        alias_map = _collect_alias_map(tree)
        visitor = _EnvMutationVisitor(alias_map)
        visitor.visit(tree)
        self.assertEqual(visitor.offending_lines, [])


if __name__ == "__main__":
    unittest.main()
