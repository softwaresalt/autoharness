"""End-to-end smoke tests for the `autoharness eval` CLI subcommand.

Hermetic: `eval run` uses the default replay runner (no models) and telemetry
defaults to disabled; `eval review` runs against a non-git temp workspace so
the injectable git path degrades to a clean result. No network, no models.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from autoharness.cli import main

_MATRIX = {
    "version": "1.0.0",
    "frozen_state": {"base": "main", "head": "HEAD"},
    "configs": [
        {
            "name": "opus",
            "models": ["claude-opus-4.6"],
            "baseline": {
                "economics": {"input_tokens": 2000, "output_tokens": 1000, "cogs_usd": 0.20, "duration_seconds": 120},
                "operations": {"cli_tools": ["git"]},
                "outcome": {"gate_exit_codes": [0]},
            },
        },
        {
            "name": "sonnet",
            "models": ["claude-sonnet-4.5"],
            "baseline": {
                "economics": {"input_tokens": 1000, "output_tokens": 500, "cogs_usd": 0.05, "duration_seconds": 60},
                "operations": {"cli_tools": ["git"]},
                "outcome": {"gate_exit_codes": [0]},
            },
        },
    ],
}


class EvalHelpSmokeTests(unittest.TestCase):
    def _help_text(self, *argv: str) -> str:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(list(argv))
        return buffer.getvalue()

    def test_eval_help(self) -> None:
        text = self._help_text("eval", "--help")
        self.assertIn("autoharness eval", text)
        self.assertIn("run", text)
        self.assertIn("review", text)

    def test_eval_run_help(self) -> None:
        self.assertIn("--matrix", self._help_text("eval", "run", "--help"))

    def test_eval_review_help(self) -> None:
        self.assertIn("--base", self._help_text("eval", "review", "--help"))


class EvalRunCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        self.matrix_path = self.workspace / "matrix.json"
        self.matrix_path.write_text(json.dumps(_MATRIX), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_json(self, *extra: str) -> dict:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main([
                "eval", "run", "--matrix", str(self.matrix_path),
                "--workspace", str(self.workspace), "--json", *extra,
            ])
        return json.loads(buffer.getvalue())

    def test_run_emits_comparative_summary(self) -> None:
        data = self._run_json()
        self.assertEqual(len(data["configs"]), 2)
        self.assertEqual(data["cheapest_config"], "sonnet")
        self.assertEqual(data["costliest_config"], "opus")

    def test_run_with_review_folds_quality(self) -> None:
        data = self._run_json("--review")
        # Non-git temp workspace -> reviewer degrades to a clean 10.0 result.
        for config in data["configs"]:
            self.assertEqual(config["quality_overall"], 10.0)

    def test_run_requires_matrix(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            main(["eval", "run", "--workspace", str(self.workspace)])
        self.assertEqual(ctx.exception.code, 2)

    def test_run_rejects_invalid_matrix(self) -> None:
        bad = self.workspace / "bad.json"
        bad.write_text('{"configs": []}', encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            main(["eval", "run", "--matrix", str(bad), "--workspace", str(self.workspace)])
        self.assertEqual(ctx.exception.code, 2)


class EvalReviewCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_review_degrades_cleanly_outside_git(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(["eval", "review", "--base", "main",
                  "--workspace", str(self.workspace), "--json"])
        data = json.loads(buffer.getvalue())
        self.assertEqual(data["overall"], 10.0)

    def test_review_requires_base(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            main(["eval", "review", "--workspace", str(self.workspace)])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
