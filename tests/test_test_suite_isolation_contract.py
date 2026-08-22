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


class _EnvMutationVisitor(ast.NodeVisitor):
    """Find every ``patch.dict(os.environ, ...)`` (however spelled: bare,
    ``mock.``-qualified, ``unittest.mock.``-qualified, any import alias,
    string-literal first argument, positional OR keyword (``in_dict=``)
    target argument, decorator or context-manager form) and every
    ``os.environ.clear()`` call.

    Alias resolution is SCOPE-AWARE (Copilot review finding on PR #398):
    import bindings are tracked on a stack of per-scope dicts (module scope
    at the bottom, pushed/popped for every function/async-function/class
    body), and resolution at any given call site merges only the scopes
    lexically enclosing that call site -- outermost first, so an inner
    scope's binding correctly SHADOWS an outer one of the same name, exactly
    as genuine Python name resolution works. A single flat whole-module map
    (the pre-review design) let an unrelated, later, function-local import
    silently overwrite an earlier, valid module-level alias binding for the
    same name, corrupting resolution for call sites that have nothing to do
    with that later import.
    """

    def __init__(self) -> None:
        self._scopes: list[dict[str, str]] = [{}]
        self.offending_lines: list[int] = []

    def _current_alias_map(self) -> dict[str, str]:
        merged: dict[str, str] = {}
        for scope in self._scopes:
            merged.update(scope)
        return merged

    def _is_env_expr(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Constant) and node.value == "os.environ":
            return True
        return _resolve_dotted(node, self._current_alias_map()) == "os.environ"

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            bound = alias.asname or alias.name.split(".")[0]
            origin = alias.name if alias.asname else alias.name.split(".")[0]
            self._scopes[-1][bound] = origin
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        module = node.module or ""
        for alias in node.names:
            bound = alias.asname or alias.name
            origin = f"{module}.{alias.name}" if module else alias.name
            self._scopes[-1][bound] = origin
        self.generic_visit(node)

    def _visit_scoped(self, node: ast.AST) -> None:
        self._scopes.append({})
        self.generic_visit(node)
        self._scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_scoped(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_scoped(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        # Copilot review finding on PR #398: Python class bodies are NOT
        # enclosing (LEGB) scopes for nested function or class definitions
        # -- a method never sees a name bound directly in its own
        # enclosing class's body (only module/enclosing-function/builtin
        # scopes apply inside a method), even though the method is
        # lexically written inside that class's body. The previous
        # `_visit_scoped(node)` treated ClassDef exactly like FunctionDef,
        # so a class-body-level import (e.g. `import json as p`) was
        # incorrectly inherited by every method nested in that class,
        # potentially SHADOWING a genuine module-level alias (e.g. `p` from
        # `from unittest.mock import patch as p`) that Python itself would
        # actually resolve from the module scope inside that method body --
        # a false negative on the very offense this guard exists to catch.
        #
        # Decorators/bases/keywords evaluate in the ENCLOSING scope (never
        # the class's own body scope), so they are visited before the
        # class scope is pushed. Direct class-body statements (e.g. a
        # class-level `import ... as X` or a class attribute assignment)
        # DO execute in the class's own namespace, so they see the pushed
        # class scope. But a nested `FunctionDef`/`AsyncFunctionDef`/
        # `ClassDef` child is visited with that class scope temporarily
        # removed, since neither methods nor nested classes ever see their
        # immediately enclosing class's own namespace.
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for kw in node.keywords:
            self.visit(kw)

        class_scope: dict[str, str] = {}
        self._scopes.append(class_scope)
        try:
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    popped = self._scopes.pop()
                    self.visit(stmt)
                    self._scopes.append(popped)
                else:
                    self.visit(stmt)
        finally:
            self._scopes.pop()

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        resolved_func = _resolve_dotted(node.func, self._current_alias_map())
        if resolved_func is not None and resolved_func.endswith("patch.dict"):
            # `patch.dict`'s target is its first POSITIONAL argument, but it
            # may also be passed by its keyword name `in_dict` (Copilot
            # review finding on PR #398: `patch.dict(in_dict=os.environ,
            # values={...})` bypassed the guard when only `node.args[0]` was
            # checked).
            target: ast.expr | None = node.args[0] if node.args else None
            if target is None:
                for kw in node.keywords:
                    if kw.arg == "in_dict":
                        target = kw.value
                        break
            if target is not None and self._is_env_expr(target):
                self.offending_lines.append(node.lineno)
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "clear":
            if self._is_env_expr(node.func.value):
                self.offending_lines.append(node.lineno)
        self.generic_visit(node)


def _find_env_mutation_offenses(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    visitor = _EnvMutationVisitor()
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
        visitor = _EnvMutationVisitor()
        visitor.visit(tree)
        self.assertEqual(sorted(visitor.offending_lines), expected)

    def test_guard_detects_keyword_argument_target_form(self) -> None:
        """Non-vacuity POSITIVE (Copilot review finding on PR #398):
        ``patch.dict`` accepts its target as the keyword argument
        ``in_dict``, not only positionally. A call spelled
        ``patch.dict(in_dict=os.environ, values={...})`` must still be
        detected -- checking only ``node.args[0]`` missed this shape."""
        sample = (
            "from unittest.mock import patch\n"
            "import os\n"
            "\n"
            "\n"
            "def keyword_target_form():\n"
            "    with patch.dict(in_dict=os.environ, values={'A': '1'}):  # OFFENSE keyword in_dict=\n"
            "        pass\n"
        )
        expected = [
            i + 1 for i, line in enumerate(sample.splitlines()) if "# OFFENSE" in line
        ]
        tree = ast.parse(sample)
        visitor = _EnvMutationVisitor()
        visitor.visit(tree)
        self.assertEqual(visitor.offending_lines, expected)

    def test_alias_resolution_is_scope_aware_not_a_flat_whole_module_map(self) -> None:
        """Non-vacuity POSITIVE + shadowing (Copilot review finding on PR
        #398): a VALID module-level offense using ``patch as p`` must still
        be detected even when some UNRELATED, LATER function defines its own
        local ``import other_module as p`` that shadows the name ``p``
        within that function's own scope only. A flat whole-module alias
        map would let the later local import overwrite the earlier
        module-level binding and cause the module-level offense to be
        missed (a false negative) -- scope-aware resolution must not let a
        sibling function's local import affect resolution anywhere outside
        that function's own body."""
        sample = (
            "from unittest.mock import patch as p\n"
            "import os\n"
            "\n"
            "\n"
            "with p.dict(os.environ, {'A': '1'}):  # OFFENSE module-level, alias p\n"
            "    pass\n"
            "\n"
            "\n"
            "def unrelated_function_shadows_p_locally():\n"
            "    import json as p  # unrelated local shadow of the name 'p'\n"
            "    return p.dumps({})\n"
        )
        expected = [
            i + 1 for i, line in enumerate(sample.splitlines()) if "# OFFENSE" in line
        ]
        self.assertEqual(len(expected), 1, "sanity check: sample must carry exactly 1 marker")
        tree = ast.parse(sample)
        visitor = _EnvMutationVisitor()
        visitor.visit(tree)
        self.assertEqual(visitor.offending_lines, expected)

    def test_class_body_is_not_an_enclosing_scope_for_its_own_methods(self) -> None:
        """Non-vacuity POSITIVE + correct-scoping (Copilot review finding
        on PR #398): Python class bodies are NOT enclosing (LEGB) scopes
        for their own nested methods -- a method never sees a name bound
        directly in its immediately enclosing class's body, only the
        module scope (or an enclosing FUNCTION scope, for a method defined
        inside a function) applies inside it. With a module-level `p`
        bound to `unittest.mock.patch`, a CLASS-level `import json as p`,
        and `with p.dict(os.environ, ...)` inside a METHOD of that class,
        real Python resolves the method's `p` from the MODULE scope (so
        the forbidden `patch.dict(os.environ, ...)` genuinely executes at
        runtime) -- the guard must resolve it the same way, not from the
        class's own (invisible-to-methods) namespace, or it would produce
        a false negative on a real offense."""
        sample = (
            "from unittest.mock import patch as p\n"
            "import os\n"
            "\n"
            "\n"
            "class SomeTestCase:\n"
            "    import json as p  # class-body-only shadow of 'p' -- invisible to methods\n"
            "\n"
            "    def test_something(self):\n"
            "        with p.dict(os.environ, {'A': '1'}):  # OFFENSE resolves via module scope\n"
            "            pass\n"
        )
        expected = [
            i + 1 for i, line in enumerate(sample.splitlines()) if "# OFFENSE" in line
        ]
        self.assertEqual(len(expected), 1, "sanity check: sample must carry exactly 1 marker")
        tree = ast.parse(sample)
        visitor = _EnvMutationVisitor()
        visitor.visit(tree)
        self.assertEqual(visitor.offending_lines, expected)

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
        visitor = _EnvMutationVisitor()
        visitor.visit(tree)
        self.assertEqual(visitor.offending_lines, [])


if __name__ == "__main__":
    unittest.main()
