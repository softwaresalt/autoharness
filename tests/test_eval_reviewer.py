"""Tests for the deterministic reviewer matrix (055.002-T).

Scope: a rule-based, reproducible diff grader that scores a change per quality
dimension. Acceptance criterion: every penalty carries a line-number citation.
No model calls; fully hermetic.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from autoharness.eval.reviewer import (
    DIMENSIONS,
    ReviewMatrixResult,
    parse_unified_diff,
    review_diff,
    review_git_diff,
)

_DIFF_EVAL = """diff --git a/src/autoharness/foo.py b/src/autoharness/foo.py
index 1111111..2222222 100644
--- a/src/autoharness/foo.py
+++ b/src/autoharness/foo.py
@@ -1,2 +1,5 @@
 import os
+def run(cmd):
+    result = eval(cmd)
+    return result
 # tail
"""

_DIFF_CLEAN = """diff --git a/tests/test_x.py b/tests/test_x.py
index 1111111..2222222 100644
--- a/tests/test_x.py
+++ b/tests/test_x.py
@@ -1,1 +1,3 @@
 import unittest
+
+VALUE = 1
"""

_LONG_LINE = "x = " + "a" * 120
_DIFF_LONG = f"""diff --git a/src/autoharness/mod.py b/src/autoharness/mod.py
index 1111111..2222222 100644
--- a/src/autoharness/mod.py
+++ b/src/autoharness/mod.py
@@ -1,1 +1,2 @@
 import os
+{_LONG_LINE}
"""

_DIFF_EXCEPT = """diff --git a/src/autoharness/bar.py b/src/autoharness/bar.py
index 1111111..2222222 100644
--- a/src/autoharness/bar.py
+++ b/src/autoharness/bar.py
@@ -1,1 +1,5 @@
 import os
+try:
+    do()
+except:
+    handle()
"""

_DIFF_SRC_WITH_TEST = """diff --git a/src/autoharness/svc.py b/src/autoharness/svc.py
index 1111111..2222222 100644
--- a/src/autoharness/svc.py
+++ b/src/autoharness/svc.py
@@ -1,1 +1,2 @@
 import os
+def compute():
diff --git a/tests/test_svc.py b/tests/test_svc.py
index 1111111..2222222 100644
--- a/tests/test_svc.py
+++ b/tests/test_svc.py
@@ -1,1 +1,2 @@
 import unittest
+def test_compute():
"""


class ParseUnifiedDiffTests(unittest.TestCase):
    def test_added_lines_carry_correct_new_line_numbers(self) -> None:
        added = parse_unified_diff(_DIFF_EVAL)
        self.assertEqual(
            [(a.path, a.lineno) for a in added],
            [
                ("src/autoharness/foo.py", 2),
                ("src/autoharness/foo.py", 3),
                ("src/autoharness/foo.py", 4),
            ],
        )
        self.assertEqual(added[1].content, "    result = eval(cmd)")

    def test_removed_lines_do_not_advance_new_line_counter(self) -> None:
        diff = (
            "diff --git a/src/m.py b/src/m.py\n"
            "--- a/src/m.py\n"
            "+++ b/src/m.py\n"
            "@@ -1,2 +1,2 @@\n"
            " keep\n"
            "-old\n"
            "+new\n"
        )
        added = parse_unified_diff(diff)
        self.assertEqual([(a.path, a.lineno) for a in added], [("src/m.py", 2)])


class ReviewDiffTests(unittest.TestCase):
    def test_all_dimensions_present(self) -> None:
        result = review_diff(_DIFF_CLEAN)
        self.assertIsInstance(result, ReviewMatrixResult)
        self.assertEqual(set(result.dimensions), set(DIMENSIONS))

    def test_clean_diff_scores_max_with_no_penalties(self) -> None:
        result = review_diff(_DIFF_CLEAN)
        self.assertEqual(result.overall, 10.0)
        for dim in result.dimensions.values():
            self.assertEqual(dim.score, 10.0)
            self.assertEqual(dim.penalties, ())

    def test_security_flags_eval_with_line_citation(self) -> None:
        result = review_diff(_DIFF_EVAL)
        security = result.dimensions["security"]
        self.assertLess(security.score, 10.0)
        self.assertTrue(any(p.line == 3 for p in security.penalties))
        self.assertTrue(all(p.path == "src/autoharness/foo.py" for p in security.penalties))

    def test_every_penalty_carries_a_line_number_citation(self) -> None:
        # Acceptance criterion: mandatory line-number citation for every penalty.
        for diff in (_DIFF_EVAL, _DIFF_LONG, _DIFF_EXCEPT):
            result = review_diff(diff)
            penalties = [p for d in result.dimensions.values() for p in d.penalties]
            self.assertTrue(penalties, "expected at least one penalty")
            for penalty in penalties:
                self.assertIsInstance(penalty.line, int)
                self.assertGreater(penalty.line, 0)
                self.assertTrue(penalty.path)
                self.assertTrue(penalty.message)

    def test_maintainability_flags_long_line(self) -> None:
        result = review_diff(_DIFF_LONG)
        maint = result.dimensions["maintainability"]
        self.assertLess(maint.score, 10.0)
        self.assertTrue(any(p.line == 2 for p in maint.penalties))

    def test_reliability_flags_bare_except(self) -> None:
        result = review_diff(_DIFF_EXCEPT)
        rel = result.dimensions["reliability"]
        self.assertLess(rel.score, 10.0)
        self.assertTrue(any(p.line == 4 for p in rel.penalties))

    def test_testing_flags_src_def_without_tests(self) -> None:
        result = review_diff(_DIFF_EVAL)
        self.assertLess(result.dimensions["testing"].score, 10.0)

    def test_testing_not_flagged_when_tests_accompany_source(self) -> None:
        result = review_diff(_DIFF_SRC_WITH_TEST)
        self.assertEqual(result.dimensions["testing"].score, 10.0)

    def test_scores_are_reproducible(self) -> None:
        # Determinism: identical input yields byte-identical serialized output.
        self.assertEqual(review_diff(_DIFF_EVAL).to_dict(), review_diff(_DIFF_EVAL).to_dict())

    def test_score_is_floored_at_zero(self) -> None:
        # Many penalties on one line must not drive a dimension negative.
        secret_line = "api_key = 'abcdefdeadbeef'; token = 'xyztokenvalue'; eval(x); exec(y)"
        diff = (
            "diff --git a/src/autoharness/z.py b/src/autoharness/z.py\n"
            "--- a/src/autoharness/z.py\n"
            "+++ b/src/autoharness/z.py\n"
            "@@ -1,1 +1,2 @@\n"
            " import os\n"
            f"+{secret_line}\n"
        )
        result = review_diff(diff)
        for dim in result.dimensions.values():
            self.assertGreaterEqual(dim.score, 0.0)


class ReviewGitDiffTests(unittest.TestCase):
    def test_uses_injected_runner(self) -> None:
        def fake(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            self.assertEqual(argv, ["git", "diff", "main...HEAD"])
            return 0, _DIFF_EVAL, ""

        result = review_git_diff("main", git_runner=fake)
        self.assertLess(result.dimensions["security"].score, 10.0)

    def test_degrades_gracefully_when_git_missing(self) -> None:
        def missing(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            raise FileNotFoundError("git")

        result = review_git_diff("main", git_runner=missing)
        self.assertEqual(result.overall, 10.0)
        self.assertEqual(result.files, ())

    def test_degrades_gracefully_on_nonzero_exit(self) -> None:
        def failing(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
            return 128, "", "fatal: bad revision"

        result = review_git_diff("nope", git_runner=failing)
        self.assertEqual(result.overall, 10.0)


if __name__ == "__main__":
    unittest.main()
