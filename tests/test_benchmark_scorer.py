"""Tests for the benchmark correctness scorer (085.003-T)."""

from __future__ import annotations

import unittest

from autoharness.eval.benchmark.scorer import CorrectnessScore, regressed, score_arm


class ScoreArmTests(unittest.TestCase):
    def test_exact_match_nonempty(self) -> None:
        score = score_arm("s1", "baseline", ["a.py", "b.py"], ["b.py", "a.py"])
        self.assertTrue(score.exact_match)
        self.assertEqual(score.classification, "exact")
        self.assertEqual(score.precision, 1.0)
        self.assertEqual(score.recall, 1.0)

    def test_exact_match_both_empty_negative_scenario(self) -> None:
        score = score_arm("neg-1", "treatment", [], [])
        self.assertTrue(score.exact_match)
        self.assertEqual(score.classification, "exact")
        self.assertIsNone(score.precision)
        self.assertIsNone(score.recall)

    def test_full_miss(self) -> None:
        score = score_arm("s1", "treatment", ["z.py"], ["a.py"])
        self.assertFalse(score.exact_match)
        self.assertEqual(score.classification, "miss")
        self.assertEqual(score.precision, 0.0)
        self.assertEqual(score.recall, 0.0)

    def test_empty_produced_against_nonempty_gold_is_miss_not_zero_precision(self) -> None:
        score = score_arm("s1", "treatment", [], ["a.py"])
        self.assertEqual(score.classification, "miss")
        self.assertIsNone(score.precision)  # undefined, not 0 or 1
        self.assertEqual(score.recall, 0.0)

    def test_partial_match(self) -> None:
        score = score_arm("s1", "treatment", ["a.py"], ["a.py", "b.py"])
        self.assertFalse(score.exact_match)
        self.assertEqual(score.classification, "partial")
        self.assertEqual(score.precision, 1.0)
        self.assertEqual(score.recall, 0.5)

    def test_partial_match_with_extra_and_missing(self) -> None:
        score = score_arm("s1", "treatment", ["a.py", "z.py"], ["a.py", "b.py"])
        self.assertEqual(score.classification, "partial")
        self.assertEqual(score.precision, 0.5)
        self.assertEqual(score.recall, 0.5)

    def test_order_and_duplicate_insensitive(self) -> None:
        score_a = score_arm("s1", "baseline", ["a.py", "a.py", "b.py"], ["b.py", "a.py"])
        score_b = score_arm("s1", "baseline", ["b.py", "a.py"], ["a.py", "b.py"])
        self.assertEqual(score_a.exact_match, score_b.exact_match)
        self.assertEqual(score_a.classification, score_b.classification)

    def test_to_dict_roundtrip_shape(self) -> None:
        score = score_arm("s1", "baseline", ["a.py"], ["a.py"])
        payload = score.to_dict()
        self.assertEqual(payload["scenario_id"], "s1")
        self.assertEqual(payload["arm"], "baseline")
        self.assertIn("classification", payload)


class RegressedTests(unittest.TestCase):
    def test_treatment_full_miss_after_baseline_exact_is_regression(self) -> None:
        baseline = score_arm("s1", "baseline", ["a.py"], ["a.py"])
        treatment = score_arm("s1", "treatment", [], ["a.py"])
        self.assertTrue(regressed(baseline, treatment))

    def test_treatment_partial_after_baseline_exact_is_regression(self) -> None:
        baseline = score_arm("s1", "baseline", ["a.py", "b.py"], ["a.py", "b.py"])
        treatment = score_arm("s1", "treatment", ["a.py"], ["a.py", "b.py"])
        self.assertTrue(regressed(baseline, treatment))

    def test_both_exact_is_not_regression(self) -> None:
        baseline = score_arm("s1", "baseline", ["a.py"], ["a.py"])
        treatment = score_arm("s1", "treatment", ["a.py"], ["a.py"])
        self.assertFalse(regressed(baseline, treatment))

    def test_both_empty_negative_scenario_is_not_regression(self) -> None:
        baseline = score_arm("neg-1", "baseline", [], [])
        treatment = score_arm("neg-1", "treatment", [], [])
        self.assertFalse(regressed(baseline, treatment))

    def test_equal_hits_but_baseline_exact_treatment_not_is_regression(self) -> None:
        # Baseline correctly finds nothing; treatment spuriously produces an
        # extra (wrong) item — same hit-count (0) but treatment is worse.
        baseline = score_arm("neg-1", "baseline", [], [])
        treatment = score_arm("neg-1", "treatment", ["spurious.py"], [])
        self.assertTrue(regressed(baseline, treatment))

    def test_treatment_strictly_better_is_not_regression(self) -> None:
        baseline = score_arm("s1", "baseline", ["a.py"], ["a.py", "b.py"])
        treatment = score_arm("s1", "treatment", ["a.py", "b.py"], ["a.py", "b.py"])
        self.assertFalse(regressed(baseline, treatment))

    def test_precision_drop_with_unchanged_recall_is_regression(self) -> None:
        # Review-fix (Copilot thread PRRT_kwDORzpWpM6V5Utv): baseline {a} and
        # treatment {a, spurious} against gold {a, b} have equal hit counts
        # (1) — recall is unchanged (0.5 for both) — but treatment's
        # precision drops from 1.0 (1/1) to 0.5 (1/2). This must be a
        # regression, or reporting could emit an efficiency "win" over a
        # noisier treatment, violating H3.
        baseline = score_arm("s1", "baseline", ["a.py"], ["a.py", "b.py"])
        treatment = score_arm("s1", "treatment", ["a.py", "spurious.py"], ["a.py", "b.py"])
        self.assertEqual(baseline.recall, treatment.recall)
        self.assertGreater(baseline.precision, treatment.precision)
        self.assertTrue(regressed(baseline, treatment))

    def test_equal_precision_and_recall_is_not_regression(self) -> None:
        # Same hit count and same false-positive count (zero, for both) —
        # not a regression; guards the precision-drop fix above against a
        # false positive on ordinary equal-quality arms.
        baseline = score_arm("s1", "baseline", ["a.py"], ["a.py", "b.py"])
        treatment = score_arm("s1", "treatment", ["a.py"], ["a.py", "b.py"])
        self.assertFalse(regressed(baseline, treatment))


if __name__ == "__main__":
    unittest.main()
