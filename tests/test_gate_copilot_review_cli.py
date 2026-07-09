"""End-to-end smoke tests for the `autoharness gate copilot-review` CLI subcommand.

Hermetic: the GitHub query is patched so no external binary or network is touched.
Covers the fail-closed exit-code contract, --json, --force audit, and arg errors.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

from autoharness.cli import main
from autoharness.gates.copilot_review import ReviewRecord, ReviewState, Verdict

_HEAD = "c" * 40


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - test harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


def _state(*, requested=False, reviews=(), unresolved=(), head=_HEAD, parse_ok=True):
    return ReviewState(
        head_ref_oid=head,
        copilot_requested=requested,
        copilot_reviews=tuple(reviews),
        copilot_unresolved_thread_ids=tuple(unresolved),
        parse_ok=parse_ok,
    )


class CopilotReviewHelpTests(unittest.TestCase):
    def test_gate_help_lists_copilot_review(self) -> None:
        out, _, _ = _run("gate", "--help")
        self.assertIn("copilot-review", out)

    def test_copilot_review_help(self) -> None:
        out, _, _ = _run("gate", "copilot-review", "--help")
        self.assertIn("FAIL-CLOSED", out)
        self.assertIn("--enforcement", out)


class CopilotReviewArgErrorTests(unittest.TestCase):
    def test_missing_pr_exits_2(self) -> None:
        _, _, code = _run("gate", "copilot-review", "--repo", "o/n")
        self.assertEqual(code, 2)

    def test_missing_repo_exits_2(self) -> None:
        _, _, code = _run("gate", "copilot-review", "42")
        self.assertEqual(code, 2)

    def test_bad_enforcement_exits_2(self) -> None:
        _, _, code = _run(
            "gate", "copilot-review", "42", "--repo", "o/n", "--enforcement", "maybe"
        )
        self.assertEqual(code, 2)

    def test_bad_max_wait_exits_2(self) -> None:
        _, _, code = _run(
            "gate", "copilot-review", "42", "--repo", "o/n", "--max-wait", "soon"
        )
        self.assertEqual(code, 2)

    def test_unknown_flag_exits_2(self) -> None:
        _, _, code = _run("gate", "copilot-review", "42", "--repo", "o/n", "--bogus")
        self.assertEqual(code, 2)


class CopilotReviewVerdictTests(unittest.TestCase):
    def _patch(self, state):
        return mock.patch(
            "autoharness.gates.copilot_review.query_pr_review_state",
            return_value=state,
        )

    def test_satisfied_exits_0(self) -> None:
        st = _state(requested=True, reviews=[ReviewRecord("COMMENTED", _HEAD)])
        with self._patch(st):
            out, _, code = _run("gate", "copilot-review", "42", "--repo", "o/n")
        self.assertEqual(code, 0)
        self.assertIn("SATISFIED", out)
        self.assertIn("PASS", out)

    def test_not_applicable_exits_0(self) -> None:
        st = _state(requested=False, reviews=[])
        with self._patch(st):
            _, _, code = _run("gate", "copilot-review", "42", "--repo", "o/n")
        self.assertEqual(code, 0)

    def test_unresolved_threads_blocks_exit_1(self) -> None:
        st = _state(
            requested=True,
            reviews=[ReviewRecord("COMMENTED", _HEAD)],
            unresolved=["PRRT_1", "PRRT_2"],
        )
        with self._patch(st):
            out, _, code = _run("gate", "copilot-review", "42", "--repo", "o/n")
        self.assertEqual(code, 1)
        self.assertIn("UNRESOLVED_THREADS", out)
        self.assertIn("BLOCK", out)

    def test_waiting_blocks_exit_1(self) -> None:
        st = _state(requested=True, reviews=[])
        with self._patch(st):
            _, _, code = _run("gate", "copilot-review", "42", "--repo", "o/n")
        self.assertEqual(code, 1)

    def test_verify_failed_blocks_exit_1(self) -> None:
        with mock.patch(
            "autoharness.gates.copilot_review.query_pr_review_state",
            side_effect=RuntimeError("gh missing"),
        ):
            out, _, code = _run("gate", "copilot-review", "42", "--repo", "o/n")
        self.assertEqual(code, 1)
        self.assertIn("VERIFY_FAILED", out)

    def test_json_output(self) -> None:
        st = _state(
            requested=True,
            reviews=[ReviewRecord("COMMENTED", _HEAD)],
            unresolved=["PRRT_1"],
        )
        with self._patch(st):
            out, _, code = _run(
                "gate", "copilot-review", "42", "--repo", "o/n", "--json"
            )
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertEqual(payload["verdict"], "UNRESOLVED_THREADS")
        self.assertTrue(payload["blocked"])


class CopilotReviewForceTests(unittest.TestCase):
    def test_force_overrides_block_and_audits(self) -> None:
        st = _state(requested=True, reviews=[])  # WAITING -> BLOCK
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch(
                "autoharness.gates.copilot_review.query_pr_review_state",
                return_value=st,
            ):
                out, _, code = _run(
                    "gate", "copilot-review", "42", "--repo", "o/n",
                    "--force", "--workspace", tmp,
                )
            self.assertEqual(code, 0)
            self.assertIn("override recorded", out)
            audit = Path(tmp) / ".autoharness" / "gates" / "copilot-review-force-audit.log"
            self.assertTrue(audit.exists())
            body = audit.read_text(encoding="utf-8")
            self.assertIn("FORCE_BYPASS", body)
            self.assertIn("WAITING_FOR_REVIEW", body)

    def test_force_on_passing_verdict_does_not_audit(self) -> None:
        st = _state(requested=True, reviews=[ReviewRecord("COMMENTED", _HEAD)])
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch(
                "autoharness.gates.copilot_review.query_pr_review_state",
                return_value=st,
            ):
                _, _, code = _run(
                    "gate", "copilot-review", "42", "--repo", "o/n",
                    "--force", "--workspace", tmp,
                )
            self.assertEqual(code, 0)
            audit = Path(tmp) / ".autoharness" / "gates" / "copilot-review-force-audit.log"
            self.assertFalse(audit.exists())


if __name__ == "__main__":
    unittest.main()
