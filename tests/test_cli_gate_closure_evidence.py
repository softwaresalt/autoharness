"""CLI tests for `autoharness gate closure-evidence` (167.004-T U4, 167.011-T U11).

Write-time validation of a post-merge closure artifact against the
closure-evidence naming contract. Every fixture lives in a temporary scratch
workspace; canonical names come from ``build_closure_path`` and legacy names
from ``tests/_closure_legacy_names.py`` (plan C6).
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from _closure_legacy_names import legacy_closure_filename
from autoharness.cli import main
from autoharness.gates.closure_contract import (
    CANONICAL_CLOSURE_PATTERN_DOC,
    CLOSURE_PREDICATE_REQUIREMENT_DOC,
    build_closure_path,
)

_READY = "---\ncompaction_status: done\nclosure_status: READY\n---\n"


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - CLI harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


def _run_json(*argv: str) -> tuple[dict, int | None]:
    out, _err, code = _run(*argv, "--json")
    return json.loads(out), code


def _make_dir_link(link: Path, target: Path) -> str | None:
    try:
        os.symlink(target, link, target_is_directory=True)
        return None
    except (OSError, NotImplementedError) as exc:
        symlink_error = exc
    if os.name == "nt":
        try:
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
            return None
        except (OSError, ImportError, AttributeError) as exc:  # pragma: no cover - platform
            return f"cannot create symlink ({symlink_error}) or junction ({exc})"
    return f"cannot create directory symlink: {symlink_error}"


class _ClosureWorkspaceMixin:
    def setUp(self) -> None:  # noqa: D401 - unittest hook
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "workspace"
        self.outside = base / "outside"
        self.closure_dir = self.root / "docs" / "closure"
        self.closure_dir.mkdir(parents=True)
        self.outside.mkdir()

    def tearDown(self) -> None:  # noqa: D401 - unittest hook
        self._tmp.cleanup()

    def _canonical(self, shipment_id: str = "175-S", feature_id: str = "167-F", body: str = _READY) -> Path:
        path = build_closure_path("docs/closure", shipment_id, feature_id, workspace_root=self.root)
        path.write_text(body, encoding="utf-8")
        return path

    def _gate(self, path: Path | str, *extra: str) -> tuple[dict, int | None]:
        return _run_json(
            "gate", "closure-evidence", "--path", str(path), "--workspace", str(self.root), *extra
        )


class ClosureEvidenceCliTests(_ClosureWorkspaceMixin, unittest.TestCase):
    def test_help_lists_closure_evidence(self) -> None:
        out, _, _ = _run("gate", "--help")
        self.assertIn("closure-evidence", out)
        out, _, code = _run("gate", "closure-evidence", "--help")
        self.assertIn("--path", out)
        self.assertIn(code, (0, None))

    def test_canonical_acceptable_artifact_passes(self) -> None:
        path = self._canonical()
        payload, code = self._gate(path, "--shipment", "175-S")
        self.assertIn(code, (0, None))
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["exit_code"], 0)
        self.assertIsNone(payload["failed_check"])
        self.assertEqual(payload["shipment_id"], "175-S")
        # Human-readable form also passes.
        out, _, human_code = _run(
            "gate", "closure-evidence", "--path", str(path), "--workspace", str(self.root)
        )
        self.assertIn(human_code, (0, None))
        self.assertIn("PASS", out)

    def test_legacy_filename_fails_write_time_with_canonical_pattern(self) -> None:
        legacy = self.closure_dir / legacy_closure_filename("175-s", "167-f")
        legacy.write_text(_READY, encoding="utf-8")
        payload, code = self._gate(legacy)
        self.assertEqual(code, 1)
        self.assertEqual(payload["failed_check"], "filename")
        self.assertIn(CANONICAL_CLOSURE_PATTERN_DOC, payload["message"])
        self.assertIn(legacy.name, payload["message"])

    def test_absent_or_unparseable_path_is_invalid_input(self) -> None:
        missing = self.closure_dir / "175-S-167-F-post-merge-closure.md"
        payload, code = self._gate(missing)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")
        self.assertIn(str(missing), payload["message"])

        unparseable = self._canonical(body="---\nclosure_status: [unterminated\n---\n")
        payload, code = self._gate(unparseable)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")
        self.assertIn(str(unparseable), payload["message"])

        no_frontmatter = self._canonical(shipment_id="176-S", body="no frontmatter here\n")
        payload, code = self._gate(no_frontmatter)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")

    def test_path_outside_workspace_is_rejected_before_other_checks(self) -> None:
        outside_file = self.outside / "175-S-167-F-post-merge-closure.md"
        outside_file.write_text(_READY, encoding="utf-8")
        rows = [
            ("absolute out-of-root", str(outside_file)),
            ("traversal", "../outside/175-S-167-F-post-merge-closure.md"),
        ]
        link = self.root / "docs" / "escape-link"
        reason = _make_dir_link(link, self.outside)
        for label, path in rows:
            with self.subTest(row=label):
                payload, code = self._gate(path)
                self.assertEqual(code, 2)
                self.assertEqual(payload["failed_check"], "workspace_containment")
                self.assertIn(str(self.root), payload["message"])
                self.assertIn("175-S-167-F-post-merge-closure.md", payload["message"])
        with self.subTest(row="symlink/junction escaping root"):
            if reason:
                self.skipTest(reason)
            payload, code = self._gate(link / "175-S-167-F-post-merge-closure.md")
            self.assertEqual(code, 2)
            self.assertEqual(payload["failed_check"], "workspace_containment")
            self.assertIn(str(self.root), payload["message"])

    def test_json_failed_check_discriminator(self) -> None:
        legacy = self.closure_dir / legacy_closure_filename("175-s", "167-f")
        legacy.write_text(_READY, encoding="utf-8")
        rejected = self._canonical(
            shipment_id="177-S", body="---\ncompaction_status: done\nclosure_status: BLOCKED\n---\n"
        )
        foreign = self._canonical(shipment_id="178-S")
        rows = (
            ("workspace_containment", self.outside / "x.md", (), 2),
            ("input", self.closure_dir / "missing.md", (), 2),
            ("filename", legacy, (), 1),
            ("frontmatter_predicate", rejected, (), 1),
            ("discoverability", foreign, ("--shipment", "179-S"), 1),
            (None, self._canonical(), (), 0),
        )
        for failed_check, path, extra, exit_code in rows:
            with self.subTest(failed_check=failed_check):
                payload, code = self._gate(path, *extra)
                self.assertEqual(payload["failed_check"], failed_check)
                self.assertEqual(payload["exit_code"], exit_code)
                self.assertEqual(code if code is not None else 0, exit_code)
                self.assertIn("path", payload)

    def test_missing_path_argument_is_invalid(self) -> None:
        _out, err, code = _run("gate", "closure-evidence", "--workspace", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("--path", err)
        _out, err, code = _run("gate", "closure-evidence", "--path", "x", "--bogus")
        self.assertEqual(code, 2)

    def test_invalid_declared_shipment_is_invalid_input(self) -> None:
        payload, code = self._gate(self._canonical(), "--shipment", "175-s")
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")

    def test_artifact_outside_consumer_closure_dir_is_not_discoverable(self) -> None:
        elsewhere = self.root / "other"
        elsewhere.mkdir()
        path = build_closure_path("other", "175-S", "167-F", workspace_root=self.root)
        path.write_text(_READY, encoding="utf-8")
        payload, code = self._gate(path)
        self.assertEqual(code, 1)
        self.assertEqual(payload["failed_check"], "discoverability")

    def test_symlinked_artifact_is_rejected_as_input(self) -> None:
        # A canonically-named link to another shipment's evidence must not pass:
        # the filename check, the read, and discoverability must see one object.
        target = self._canonical(shipment_id="174-S", feature_id="166-F")
        alias = self.closure_dir / target.name.replace("174-S-166-F", "175-S-167-F")
        try:
            os.symlink(target, alias)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"cannot create file symlink: {exc}")
        payload, code = self._gate(alias)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")
        self.assertIn("symbolic link", payload["message"])

    def test_filename_check_uses_the_on_disk_name(self) -> None:
        canonical = self._canonical()
        canonical.unlink()
        lowered = canonical.with_name(canonical.name.lower())
        lowered.write_text(_READY, encoding="utf-8")
        if not canonical.exists():
            self.skipTest("filesystem is case-sensitive; spelling cannot diverge from the on-disk name")
        # The caller spells the canonical name, but the file on disk is lowercase.
        payload, code = self._gate(canonical)
        self.assertEqual(code, 1)
        self.assertEqual(payload["failed_check"], "filename")
        self.assertIn(lowered.name, payload["message"])

    def test_help_token_as_option_value_is_not_help(self) -> None:
        out, _err, code = _run("gate", "closure-evidence", "--path", "help", "--workspace", str(self.root))
        self.assertNotIn("Subcommands:", out)
        self.assertEqual(code, 2)
        out, _err, code = _run("gate", "closure-evidence", "--path", "x.md", "-h")
        self.assertIn("closure-evidence", out)
        self.assertIn(code, (None, 0))

    def test_unreadable_closure_directory_is_invalid_input(self) -> None:
        from unittest import mock

        from autoharness.gates import closure_contract

        artifact = self._canonical()
        with mock.patch.object(
            closure_contract, "classify_closure_candidates", side_effect=PermissionError("denied")
        ):
            payload, code = self._gate(artifact)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")
        self.assertIn("unreadable", payload["message"])


_CONDITIONS_OK = (
    "conditions:\n"
    "  - id: c1\n"
    "    satisfied: true\n"
    "    evidence: 'PR #1'\n"
)
# (label, frontmatter body lines) -- one row per consumer-predicate branch
# enumerated from topology._closure_artifact_complete/_closure_conditions_satisfied.
_PARITY_ROWS = (
    ("accept READY + compaction_status done", "compaction_status: done\nclosure_status: READY\n"),
    ("accept READY + compaction_status degraded", "compaction_status: degraded\nclosure_status: READY\n"),
    ("accept READY + compaction_status padded/cased", "compaction_status: ' DONE '\nclosure_status: ' ready '\n"),
    ("accept READY via legacy compaction alias", "compaction: done\nclosure_status: READY\n"),
    ("accept READY_WITH_CONDITIONS all satisfied", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\n" + _CONDITIONS_OK),
    ("reject READY_WITH_CONDITIONS absent conditions", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\n"),
    ("reject READY_WITH_CONDITIONS empty conditions", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\nconditions: []\n"),
    ("reject READY_WITH_CONDITIONS conditions not a list", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\nconditions: {id: c1}\n"),
    ("reject READY_WITH_CONDITIONS non-mapping entry", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\nconditions:\n  - just-a-string\n"),
    ("reject READY_WITH_CONDITIONS satisfied false", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\nconditions:\n  - id: c1\n    satisfied: false\n    evidence: 'x'\n"),
    ("reject READY_WITH_CONDITIONS satisfied truthy string", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\nconditions:\n  - id: c1\n    satisfied: 'true'\n    evidence: 'x'\n"),
    ("reject READY_WITH_CONDITIONS missing evidence", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\nconditions:\n  - id: c1\n    satisfied: true\n"),
    ("reject READY_WITH_CONDITIONS non-string evidence", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\nconditions:\n  - id: c1\n    satisfied: true\n    evidence: 42\n"),
    ("reject READY_WITH_CONDITIONS blank evidence", "compaction_status: done\nclosure_status: READY_WITH_CONDITIONS\nconditions:\n  - id: c1\n    satisfied: true\n    evidence: '   '\n"),
    ("reject closure_status BLOCKED", "compaction_status: done\nclosure_status: BLOCKED\n"),
    ("reject closure_status missing", "compaction_status: done\n"),
    ("reject closure_status blank", "compaction_status: done\nclosure_status: '  '\n"),
    ("reject closure_status non-string", "compaction_status: done\nclosure_status: 42\n"),
    ("reject closure_status out-of-enum", "compaction_status: done\nclosure_status: MAYBE\n"),
    ("reject compaction_status missing", "closure_status: READY\n"),
    ("reject compaction_status out-of-enum", "compaction_status: partial\nclosure_status: READY\n"),
    ("reject compaction_status non-string", "compaction_status: 1\nclosure_status: READY\n"),
)

# Keys the closure-evidence JSON payload may carry. A field- or reason-level
# key (e.g. "reason", "field", "cause") would be a second validity definition.
_PAYLOAD_KEYS = frozenset(
    {"gate", "path", "workspace", "shipment_id", "canonical_pattern", "passed", "exit_code", "failed_check", "message"}
)


class ClosureEvidenceSemanticBatteryTests(_ClosureWorkspaceMixin, unittest.TestCase):
    """167.011-T (U11): write-time and read-time validity are one definition."""

    def test_consumer_branch_parity_matrix(self) -> None:
        from autoharness.gates.topology import (
            FilesystemTopologyReaders,
            _closure_artifact_complete,
            _frontmatter,
        )

        for label, body in _PARITY_ROWS:
            with self.subTest(row=label):
                for existing in self.closure_dir.glob("*.md"):
                    existing.unlink()
                path = self._canonical(body=f"---\n{body}---\n")
                payload, _code = self._gate(path)
                self.assertIn(payload["failed_check"], (None, "frontmatter_predicate"))
                write_time = payload["exit_code"] == 0
                read_time = _closure_artifact_complete(_frontmatter(path))
                reader_verdict = FilesystemTopologyReaders(self.root).closure_complete("175-S")
                # The assertion is EQUALITY of the verdicts, never independent correctness.
                self.assertEqual(write_time, read_time)
                self.assertEqual(write_time, reader_verdict is True)
                self.assertEqual(write_time, label.startswith("accept"), "row label/verdict drift")

    def test_generic_predicate_rejection_diagnostic(self) -> None:
        unsatisfied = self._canonical(
            shipment_id="175-S",
            body=(
                "---\ncompaction_status: done\nclosure_status: READY_WITH_CONDITIONS\n"
                "conditions:\n  - id: c1\n    satisfied: false\n    evidence: 'x'\n---\n"
            ),
        )
        blocked = self._canonical(
            shipment_id="176-S", body="---\ncompaction_status: done\nclosure_status: BLOCKED\n---\n"
        )
        messages = []
        for path in (unsatisfied, blocked):
            payload, code = self._gate(path)
            self.assertEqual(code, 1)
            self.assertEqual(payload["failed_check"], "frontmatter_predicate")
            self.assertEqual(set(payload), _PAYLOAD_KEYS)
            message = payload["message"]
            self.assertIn(str(path), message)
            self.assertIn("topology._closure_artifact_complete", message)
            self.assertIn(CLOSURE_PREDICATE_REQUIREMENT_DOC, message)
            messages.append(message.replace(str(path), "<path>"))
        # Negative form: two different refusal causes yield the IDENTICAL
        # generic message -- no field-level or reason-level cause leaks.
        self.assertEqual(messages[0], messages[1])
        for leaked in ("satisfied: false", "BLOCKED", "because", "reason"):
            self.assertNotIn(leaked, messages[0])

    def test_cli_owned_diagnostic_fidelity(self) -> None:
        legacy = self.closure_dir / legacy_closure_filename("175-s", "167-f")
        legacy.write_text(_READY, encoding="utf-8")
        foreign = self._canonical(shipment_id="180-S")
        missing = self.closure_dir / "181-S-167-F-post-merge-closure.md"
        rows = (
            ("filename", legacy, (), 1, (legacy.name, CANONICAL_CLOSURE_PATTERN_DOC)),
            ("discoverability", foreign, ("--shipment", "182-S"), 1, (str(foreign), "180-S", "182-S")),
            ("input", missing, (), 2, (str(missing),)),
        )
        for failed_check, path, extra, exit_code, fragments in rows:
            with self.subTest(failed_check=failed_check):
                payload, code = self._gate(path, *extra)
                self.assertEqual(code, exit_code)
                self.assertEqual(payload["failed_check"], failed_check)
                for fragment in fragments:
                    self.assertIn(fragment, payload["message"])

    def test_predicate_reuse_is_structural(self) -> None:
        import ast

        import autoharness.cli as cli_module

        tree = ast.parse(Path(cli_module.__file__).read_text(encoding="utf-8"))
        functions = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and "closure_evidence" in node.name
        }
        self.assertIn("_evaluate_closure_evidence", functions)
        evaluate_fn = functions["_evaluate_closure_evidence"]
        attributes = {node.attr for node in ast.walk(evaluate_fn) if isinstance(node, ast.Attribute)}
        self.assertIn("_closure_artifact_complete", attributes)
        forbidden = {
            "ready", "ready_with_conditions", "blocked", "done", "degraded", "pending",
            "closure_status", "compaction_status", "compaction", "conditions", "satisfied", "evidence",
        }
        for name, function in functions.items():
            for node in ast.walk(function):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    with self.subTest(function=name, constant=node.value):
                        self.assertNotIn(node.value.strip().lower(), forbidden)


if __name__ == "__main__":
    unittest.main()
