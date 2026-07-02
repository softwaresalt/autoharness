"""Tests for the eval model-config matrix loader (055.004-T, U8 sub-unit).

Scope: load + validate the eval model-configuration matrix for a frozen
baseline run. No model execution, no reviewer scoring.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from autoharness.eval.matrix import (
    EvalMatrix,
    EvalMatrixError,
    ModelConfig,
    load_matrix,
    load_matrix_file,
)

_VALID = {
    "version": "1.0.0",
    "frozen_state": {"base": "main", "head": "HEAD"},
    "configs": [
        {"name": "baseline-opus", "models": ["claude-opus-4.6"]},
        {
            "name": "baseline-sonnet",
            "models": ["claude-sonnet-4.5"],
            "baseline": {
                "economics": {"input_tokens": 100, "output_tokens": 50},
                "operations": {"cli_tools": ["git"]},
                "outcome": {"gate_exit_codes": [0]},
            },
        },
    ],
}


class LoadMatrixTests(unittest.TestCase):
    def test_valid_matrix_loads_configs_and_frozen_state(self) -> None:
        matrix = load_matrix(_VALID)
        self.assertIsInstance(matrix, EvalMatrix)
        self.assertEqual(matrix.version, "1.0.0")
        self.assertEqual(len(matrix.configs), 2)
        self.assertIsInstance(matrix.configs[0], ModelConfig)
        self.assertEqual(matrix.configs[0].name, "baseline-opus")
        self.assertEqual(matrix.configs[0].models, ("claude-opus-4.6",))
        self.assertIsNotNone(matrix.frozen_state)
        assert matrix.frozen_state is not None
        self.assertEqual(matrix.frozen_state.base, "main")
        self.assertEqual(matrix.frozen_state.head, "HEAD")

    def test_baseline_block_is_retained_for_replay(self) -> None:
        matrix = load_matrix(_VALID)
        self.assertIsNone(matrix.configs[0].baseline)
        self.assertIsNotNone(matrix.configs[1].baseline)
        assert matrix.configs[1].baseline is not None
        self.assertEqual(matrix.configs[1].baseline["economics"]["input_tokens"], 100)

    def test_frozen_state_head_defaults_to_head(self) -> None:
        data = {"configs": [{"name": "c", "models": ["m"]}], "frozen_state": {"base": "dev"}}
        matrix = load_matrix(data)
        assert matrix.frozen_state is not None
        self.assertEqual(matrix.frozen_state.head, "HEAD")

    def test_absent_frozen_state_is_none(self) -> None:
        data = {"configs": [{"name": "c", "models": ["m"]}]}
        matrix = load_matrix(data)
        self.assertIsNone(matrix.frozen_state)

    def test_non_mapping_root_raises(self) -> None:
        with self.assertRaises(EvalMatrixError):
            load_matrix(["not", "a", "mapping"])

    def test_missing_configs_raises(self) -> None:
        with self.assertRaises(EvalMatrixError):
            load_matrix({"version": "1.0.0"})

    def test_empty_configs_raises(self) -> None:
        with self.assertRaises(EvalMatrixError):
            load_matrix({"configs": []})

    def test_duplicate_config_names_raise(self) -> None:
        data = {
            "configs": [
                {"name": "dup", "models": ["a"]},
                {"name": "dup", "models": ["b"]},
            ]
        }
        with self.assertRaises(EvalMatrixError):
            load_matrix(data)

    def test_config_missing_models_raises(self) -> None:
        with self.assertRaises(EvalMatrixError):
            load_matrix({"configs": [{"name": "c"}]})

    def test_config_missing_name_raises(self) -> None:
        with self.assertRaises(EvalMatrixError):
            load_matrix({"configs": [{"models": ["m"]}]})

    def test_models_as_string_raises(self) -> None:
        # A bare string must be rejected, never silently split into chars.
        with self.assertRaises(EvalMatrixError):
            load_matrix({"configs": [{"name": "c", "models": "claude"}]})

    def test_baseline_not_mapping_raises(self) -> None:
        with self.assertRaises(EvalMatrixError):
            load_matrix({"configs": [{"name": "c", "models": ["m"], "baseline": "nope"}]})

    def test_baseline_sub_block_not_mapping_raises(self) -> None:
        # A present economics/operations/outcome sub-block must be a mapping so
        # the replay runner never hits an uncaught AttributeError downstream.
        for key in ("economics", "operations", "outcome"):
            with self.subTest(sub_block=key):
                data = {
                    "configs": [
                        {"name": "c", "models": ["m"], "baseline": {key: "not-a-map"}}
                    ]
                }
                with self.assertRaises(EvalMatrixError):
                    load_matrix(data)

    def test_frozen_state_missing_base_raises(self) -> None:
        with self.assertRaises(EvalMatrixError):
            load_matrix({"configs": [{"name": "c", "models": ["m"]}], "frozen_state": {}})


class LoadMatrixFileTests(unittest.TestCase):
    def _write(self, name: str, text: str) -> Path:
        path = Path(self._tmp.name) / name
        path.write_text(text, encoding="utf-8")
        return path

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_loads_yaml_file(self) -> None:
        yaml_text = (
            "version: '1.0.0'\n"
            "frozen_state:\n"
            "  base: main\n"
            "configs:\n"
            "  - name: c1\n"
            "    models: [m1]\n"
        )
        path = self._write("matrix.yaml", yaml_text)
        matrix = load_matrix_file(path)
        self.assertEqual(matrix.configs[0].name, "c1")

    def test_loads_json_file(self) -> None:
        path = self._write("matrix.json", json.dumps(_VALID))
        matrix = load_matrix_file(path)
        self.assertEqual(len(matrix.configs), 2)

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(EvalMatrixError):
            load_matrix_file(Path(self._tmp.name) / "nope.yaml")


if __name__ == "__main__":
    unittest.main()
