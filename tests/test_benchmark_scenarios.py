"""Tests for the benchmark scenario corpus model + loader (085.001-T)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.eval.benchmark.scenarios import (
    CorpusError,
    Scenario,
    ScenarioCorpus,
    compute_manifest_hash,
    load_corpus,
    load_corpus_file,
    load_default_corpus,
)

_BALANCED = {
    "scenarios": [
        {
            "id": "pos-1",
            "scenario_class": "positive",
            "index_state": "warm",
            "task": "find X",
            "gold_answer": ["a.py"],
            "rationale": "r",
        },
        {
            "id": "neutral-1",
            "scenario_class": "neutral",
            "index_state": "warm",
            "task": "find Y",
            "gold_answer": ["b.py"],
            "rationale": "r",
        },
        {
            "id": "neg-1",
            "scenario_class": "negative",
            "index_state": "warm",
            "task": "find nothing",
            "gold_answer": [],
            "rationale": "r",
        },
    ]
}


class ScenarioCorpusTests(unittest.TestCase):
    def test_load_corpus_balanced(self) -> None:
        corpus = load_corpus(_BALANCED)
        self.assertEqual(len(corpus.scenarios), 3)
        classes = {s.scenario_class for s in corpus.scenarios}
        self.assertEqual(classes, {"positive", "neutral", "negative"})

    def test_unbalanced_corpus_rejected_missing_negative(self) -> None:
        data = {"scenarios": [s for s in _BALANCED["scenarios"] if s["scenario_class"] != "negative"]}
        with self.assertRaises(CorpusError):
            load_corpus(data)

    def test_unbalanced_corpus_rejected_missing_positive(self) -> None:
        data = {"scenarios": [s for s in _BALANCED["scenarios"] if s["scenario_class"] != "positive"]}
        with self.assertRaises(CorpusError):
            load_corpus(data)

    def test_unbalanced_corpus_rejected_missing_neutral(self) -> None:
        data = {"scenarios": [s for s in _BALANCED["scenarios"] if s["scenario_class"] != "neutral"]}
        with self.assertRaises(CorpusError):
            load_corpus(data)

    def test_duplicate_scenario_id_rejected(self) -> None:
        data = {"scenarios": _BALANCED["scenarios"] + [_BALANCED["scenarios"][0]]}
        with self.assertRaises(CorpusError):
            load_corpus(data)

    def test_invalid_scenario_class_rejected(self) -> None:
        scenarios = [dict(s) for s in _BALANCED["scenarios"]]
        scenarios[0]["scenario_class"] = "bogus"
        with self.assertRaises(CorpusError):
            load_corpus({"scenarios": scenarios})

    def test_invalid_index_state_rejected(self) -> None:
        scenarios = [dict(s) for s in _BALANCED["scenarios"]]
        scenarios[0]["index_state"] = "bogus"
        with self.assertRaises(CorpusError):
            load_corpus({"scenarios": scenarios})

    def test_negative_scenario_with_nonempty_gold_answer_rejected(self) -> None:
        # Review-fix (Copilot thread PRRT_kwDORzpWpM6V5nzv): the
        # balanced-class check alone does not stop a mislabeled scenario
        # from evading the anti-cherry-picking invariant — a 'negative'
        # scenario's gold_answer must be validated as empty too.
        scenarios = [dict(s) for s in _BALANCED["scenarios"]]
        scenarios[2]["gold_answer"] = ["unexpected.py"]
        with self.assertRaises(CorpusError):
            load_corpus({"scenarios": scenarios})

    def test_positive_scenario_with_empty_gold_answer_rejected(self) -> None:
        scenarios = [dict(s) for s in _BALANCED["scenarios"]]
        scenarios[0]["gold_answer"] = []
        with self.assertRaises(CorpusError):
            load_corpus({"scenarios": scenarios})

    def test_neutral_scenario_with_empty_gold_answer_rejected(self) -> None:
        scenarios = [dict(s) for s in _BALANCED["scenarios"]]
        scenarios[1]["gold_answer"] = []
        with self.assertRaises(CorpusError):
            load_corpus({"scenarios": scenarios})

    def test_manifest_hash_deterministic(self) -> None:
        corpus_a = load_corpus(_BALANCED)
        corpus_b = load_corpus(_BALANCED)
        self.assertEqual(corpus_a.manifest_hash, corpus_b.manifest_hash)
        self.assertEqual(corpus_a.manifest_hash, compute_manifest_hash(corpus_a.scenarios))

    def test_manifest_hash_order_independent(self) -> None:
        reordered = {"scenarios": list(reversed(_BALANCED["scenarios"]))}
        corpus_a = load_corpus(_BALANCED)
        corpus_b = load_corpus(reordered)
        self.assertEqual(corpus_a.manifest_hash, corpus_b.manifest_hash)

    def test_manifest_hash_changes_with_content(self) -> None:
        corpus_a = load_corpus(_BALANCED)
        scenarios = [dict(s) for s in _BALANCED["scenarios"]]
        scenarios[0]["task"] = "a different task"
        corpus_b = load_corpus({"scenarios": scenarios})
        self.assertNotEqual(corpus_a.manifest_hash, corpus_b.manifest_hash)

    def test_load_corpus_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corpus.yaml"
            path.write_text(
                "scenarios:\n"
                "  - id: pos-1\n"
                "    scenario_class: positive\n"
                "    index_state: warm\n"
                "    task: q\n"
                "    gold_answer: [a.py]\n"
                "    rationale: r\n"
                "  - id: neutral-1\n"
                "    scenario_class: neutral\n"
                "    index_state: warm\n"
                "    task: q\n"
                "    gold_answer: [b.py]\n"
                "    rationale: r\n"
                "  - id: neg-1\n"
                "    scenario_class: negative\n"
                "    index_state: warm\n"
                "    task: q\n"
                "    gold_answer: []\n"
                "    rationale: r\n",
                encoding="utf-8",
            )
            corpus = load_corpus_file(path)
            self.assertEqual(len(corpus.scenarios), 3)

    def test_load_default_corpus(self) -> None:
        corpus = load_default_corpus()
        self.assertGreaterEqual(len(corpus.scenarios), 5)
        classes = {s.scenario_class for s in corpus.scenarios}
        self.assertEqual(classes, {"positive", "neutral", "negative"})
        index_states = {s.index_state for s in corpus.scenarios}
        self.assertEqual(index_states, {"warm", "cold", "stale"})

    def test_scenario_is_frozen(self) -> None:
        scenario = load_corpus(_BALANCED).scenarios[0]
        with self.assertRaises(Exception):
            scenario.id = "mutated"  # type: ignore[misc]

    def test_corpus_is_frozen(self) -> None:
        corpus = load_corpus(_BALANCED)
        with self.assertRaises(Exception):
            corpus.scenarios = ()  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
