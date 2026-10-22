"""Tests for ``autoharness harness docs-only-check``, its JSON schema and docs (216.002-T)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from _docs_only_repo import BACKLOG, DOCS, ShipmentRepo
from autoharness import cli
from autoharness.schema_contracts import SCHEMA_CONTRACTS, resolve_contract_schema_path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_SCHEMA = REPO_ROOT / "schemas" / "docs-only-check.schema.json"
MIRROR_SCHEMA = REPO_ROOT / "schemas" / "docs-only-check" / "1.0.0.schema.json"
VALIDATOR = Draft202012Validator(json.loads(ROOT_SCHEMA.read_text(encoding="utf-8")))


def run_cli(cwd: Path, argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    previous = Path.cwd()
    os.chdir(cwd)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                cli.main(argv)
                status = 0
            except SystemExit as exit_:
                status = exit_.code if isinstance(exit_.code, int) else (0 if exit_.code is None else 1)
    finally:
        os.chdir(previous)
    return status, out.getvalue(), err.getvalue()


class DocsOnlyCheckCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = ShipmentRepo()
        self.addCleanup(self.repo.cleanup)
        self.t1 = self.repo.TASKS[0]
        self.repo.claim_all()

    def common(self, owned: str = "docs/a.md") -> list[str]:
        return ["harness", "docs-only-check", "--owned", owned, "--docs-root", DOCS, "--backlog-root", BACKLOG, "--json"]

    def baseline(self, owned: str = "docs/a.md") -> tuple[int, dict]:
        status, out, _ = run_cli(self.repo.root, [*self.common(owned), "--phase", "baseline"])
        return status, json.loads(out)

    def completion_args(self, baseline_path: Path, owned: str = "docs/a.md") -> list[str]:
        return [
            *self.common(owned), "--phase", "completion", "--baseline", str(baseline_path),
            "--task", self.t1, "--feature", self.repo.FEATURE, "--shipment", self.repo.SHIPMENT,
        ]

    def test_baseline_and_completion_json_validate(self) -> None:
        status, record = self.baseline()
        self.assertEqual(status, 0)
        self.assertEqual(list(VALIDATOR.iter_errors(record)), [])
        self.assertTrue(any("body_sha256" in e for e in record["entries"]))
        path = self.repo.root.parent / f"{self.repo.root.name}-baseline.json"
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        path.write_text(json.dumps(record), encoding="utf-8")
        self.repo.write("docs/a.md", "edit\n")
        status, out, _ = run_cli(self.repo.root, self.completion_args(path))
        done = json.loads(out)
        self.assertEqual(status, 0, done)
        self.assertEqual(list(VALIDATOR.iter_errors(done)), [])
        self.assertEqual(done["phase"], "completion")
        self.assertEqual(done["implementation"]["result"], "pass")
        self.assertEqual(done["lifecycle"]["result"], "pass")

    def test_exit_1_on_violation_with_separate_classes(self) -> None:
        _, record = self.baseline()
        path = self.repo.root.parent / f"{self.repo.root.name}-baseline.json"
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        path.write_text(json.dumps(record), encoding="utf-8")
        self.repo.write("docs/a.md", "edit\n")
        self.repo.write(f"{BACKLOG}/stash.jsonl", "{\"x\":1}\n")
        self.repo.write("src/mod.py", "x = 2\n")
        status, out, _ = run_cli(self.repo.root, self.completion_args(path))
        done = json.loads(out)
        self.assertEqual(status, 1)
        self.assertEqual(list(VALIDATOR.iter_errors(done)), [])
        self.assertEqual(done["implementation"]["result"], "violation")
        self.assertEqual(done["lifecycle"]["result"], "violation")
        rules = {v["rule"] for v in done["violations"]}
        self.assertIn("BACKLOG_PATH_NOT_LIFECYCLE", rules)

    def test_baseline_violation_exit_1(self) -> None:
        self.repo.write("docs/a.md", "dirty\n")
        status, record = self.baseline()
        self.assertEqual(status, 1)
        self.assertEqual(record["violations"][0]["rule"], "OWNED_PATH_DIRTY_AT_BASELINE")
        self.assertEqual(list(VALIDATOR.iter_errors(record)), [])

    def test_exit_2_cases_emit_valid_error_documents(self) -> None:
        _, record = self.baseline()
        path = self.repo.root.parent / f"{self.repo.root.name}-baseline.json"
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        record["entries"].append({"path": "src/mod.py", "index": None, "worktree": None})
        path.write_text(json.dumps(record), encoding="utf-8")
        status, out, _ = run_cli(self.repo.root, self.completion_args(path))
        self.assertEqual(status, 2)
        self.assertEqual(list(VALIDATOR.iter_errors(json.loads(out))), [])
        path.write_text("not json", encoding="utf-8")
        self.assertEqual(run_cli(self.repo.root, self.completion_args(path))[0], 2)
        status, out, _ = run_cli(self.repo.root, self.common("docs/a.md")[:-1] + ["--docs-root", "", "--phase", "baseline", "--json"])
        self.assertEqual(status, 2)
        self.repo.write(self.repo.path_of(self.t1), "---\nid: [bad\n---\n")
        self.assertEqual(self.baseline()[0], 2)

    def test_argument_errors_exit_2(self) -> None:
        self.assertEqual(run_cli(self.repo.root, ["harness", "docs-only-check", "--json"])[0], 2)
        status, _, err = run_cli(self.repo.root, [*self.common(), "--phase", "completion"])
        self.assertEqual(status, 2)
        self.assertIn("--baseline", err)

    def test_not_a_git_repository_exits_2(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            status, out, _ = run_cli(Path(tmp), [*self.common(), "--phase", "baseline"])
        self.assertEqual(status, 2)
        self.assertEqual(list(VALIDATOR.iter_errors(json.loads(out))), [])

    def test_text_output_without_json(self) -> None:
        argv = [a for a in self.common() if a != "--json"] + ["--phase", "baseline"]
        status, out, _ = run_cli(self.repo.root, argv)
        self.assertEqual(status, 0)
        self.assertIn("baseline", out)

    def test_help_lists_command(self) -> None:
        status, out, _ = run_cli(self.repo.root, ["harness", "docs-only-check", "--help"])
        self.assertEqual(status, 0)
        for option in ("--phase", "--owned", "--docs-root", "--backlog-root", "--task", "--feature", "--shipment", "--baseline", "--json"):
            self.assertIn(option, out)
        self.assertIn("docs-only-check", run_cli(self.repo.root, ["--help"])[1])


class DocsOnlyCheckContractTests(unittest.TestCase):
    def test_schema_registered_and_versioned_like_harness_resolution(self) -> None:
        contract = SCHEMA_CONTRACTS["docs-only-check"]
        self.assertEqual(contract["schema_file"], "docs-only-check.schema.json")
        self.assertEqual(contract["versioned_schema_dir"], "docs-only-check")
        self.assertEqual(contract["current_version"], "1.0.0")
        self.assertEqual(contract["known_versions"], ("1.0.0",))
        self.assertEqual(resolve_contract_schema_path("docs-only-check", REPO_ROOT, {"schema_version": "1.0.0"}), MIRROR_SCHEMA)

    def test_root_and_mirror_differ_only_in_id(self) -> None:
        root = json.loads(ROOT_SCHEMA.read_text(encoding="utf-8"))
        mirror = json.loads(MIRROR_SCHEMA.read_text(encoding="utf-8"))
        self.assertTrue(root.pop("$id").endswith("/schemas/docs-only-check.schema.json"))
        self.assertTrue(mirror.pop("$id").endswith("/schemas/docs-only-check/1.0.0.schema.json"))
        self.assertEqual(root, mirror)

    def test_gates_reference_documents_mechanism_and_residual_risk(self) -> None:
        text = (REPO_ROOT / "docs" / "gates-reference.md").read_text(encoding="utf-8")
        start = text.index("## Docs-Only Route Checker")
        section = text[start:]
        for needle in (
            "autoharness harness docs-only-check", "--phase baseline", "--phase completion", "snapshot-and-delta",
            "residual risk", "OWNED_PATH_DIRTY_AT_BASELINE", "BACKLOG_PATH_NOT_LIFECYCLE", "exit code",
            "docs-only-check.schema.json",
        ):
            self.assertIn(needle, section)


if __name__ == "__main__":
    unittest.main()
