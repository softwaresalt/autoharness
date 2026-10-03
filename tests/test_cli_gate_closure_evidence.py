"""CLI tests for `autoharness gate closure-evidence` (167.004-T U4, 167.011-T U11, 192.007-T A4).

Write-time validation of a post-merge closure artifact against the
closure-evidence naming contract. Every fixture lives in a temporary scratch
workspace; canonical names come from ``build_closure_path`` and legacy names
from ``tests/_closure_legacy_names.py`` (plan C6).

192.007-T (plan unit A4) adds the ``close_path`` and ``close_evidence``
requirement: ``_canonical`` now writes a valid ``safe_close`` evidence record
(materialized against a scratch ``.backlogit`` tree) unless told not to, and
:class:`CloseEvidenceRequirementTests` holds the four A4 scenarios.
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
from test_cascade_evidence_contract import (
    _engine_record,
    cascade_record,
    safe_close_record,
)

from autoharness.cli import main
from autoharness.gates.cascade_evidence import (
    build_evidence_path,
    serialize_evidence_record,
)
from autoharness.gates.closure_contract import (
    CANONICAL_CLOSURE_PATTERN_DOC,
    CLOSURE_PREDICATE_REQUIREMENT_DOC,
    build_closure_path,
)

_READY = "---\ncompaction_status: done\nclosure_status: READY\n---\n"
_MERGE_SHA = "bd824b97999832aa38122f2f70d300ebbb5d2e09"
_MAX_EVIDENCE_BYTES = 512 * 1024


def evidence_relpath(shipment_id: str, feature_id: str) -> str:
    """The canonical ``close_evidence`` value for a pair (``build_evidence_path``, POSIX, relative)."""

    root = Path(tempfile.gettempdir()).resolve()
    return build_evidence_path(root, shipment_id, feature_id).relative_to(root).as_posix()


def write_backlog_record(root: Path, folder: str, artifact_id: str, *, status: str = "done", extra: str = "") -> Path:
    """Write one ``.backlogit/{folder}/{id}.md`` record; returns its path."""

    directory = root / ".backlogit" / folder
    directory.mkdir(parents=True, exist_ok=True)
    (root / ".backlogit" / ("archive" if folder == "queue" else "queue")).mkdir(exist_ok=True)
    path = directory / f"{artifact_id}.md"
    path.write_text(
        f"---\nid: {artifact_id}\nartifact_type: task\nstatus: {status}\n{extra}---\n# {artifact_id}\n",
        encoding="utf-8",
    )
    return path


def materialize_observation(root: Path, record: dict) -> dict:
    """Make every observation-set entry true of ``root``: write its file and record the real SHA-256."""

    import hashlib

    for entry in record.get("pre_close", {}).get("observation_set", []):
        if entry["location"] == "missing":
            (root / ".backlogit" / "queue").mkdir(parents=True, exist_ok=True)
            (root / ".backlogit" / "archive").mkdir(parents=True, exist_ok=True)
            continue
        status = entry["declared_status"] if isinstance(entry["declared_status"], str) else "done"
        path = write_backlog_record(root, entry["location"], entry["id"], status=status)
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return record


def evidence_record(close_path: str, shipment_id: str, feature_id: str, **kwargs: object) -> dict:
    """A valid record for the pair: ``safe_close`` (A1 builder) or ``cascade``."""

    record = safe_close_record(**kwargs) if close_path == "safe_close" else cascade_record(**kwargs)
    if close_path == "cascade":
        # The shipment ID is a captured fact the derived post_close fields are
        # recomputed from, so rebind it consistently (PR #482 review).
        original = record["shipment_id"]
        post = record["post_close"]
        post["parsed_result"]["shipment_id"] = shipment_id
        for container, key in (
            (post["parsed_result"], "archived_ids"),
            (post, "allowed_ids"),
            (post, "required_ids"),
        ):
            container[key] = [shipment_id if item == original else item for item in container[key]]
    record["shipment_id"] = shipment_id
    record["feature_id"] = feature_id
    record["merge_commit_sha"] = _MERGE_SHA
    return record


def write_evidence(root: Path, shipment_id: str, feature_id: str, record: dict | str | bytes) -> Path:
    """Write ``record`` at ``build_evidence_path`` for the pair (materializing a SAFE_CLOSE observation set)."""

    path = build_evidence_path(root, shipment_id, feature_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(record, dict):
        materialize_observation(root, record)
        record = serialize_evidence_record(record)
    if isinstance(record, str):
        record = record.encode("utf-8")
    path.write_bytes(record)
    return path


def with_close_keys(body: str, close_path: str | None, close_evidence: str | None, *, merge_commit: str | None = None) -> str:
    """Insert ``close_path`` / ``close_evidence`` (and ``merge_commit``) keys into a frontmatter body."""

    if not body.startswith("---\n"):
        return body
    lines = []
    if close_path is not None:
        lines.append(f"close_path: {close_path}\n")
    if close_evidence is not None:
        lines.append(f"close_evidence: {close_evidence}\n")
    if merge_commit is not None:
        lines.append(f"merge_commit: '{merge_commit}'\n")
    return "---\n" + "".join(lines) + body[4:]


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

    def _canonical(
        self,
        shipment_id: str = "175-S",
        feature_id: str = "167-F",
        body: str = _READY,
        *,
        evidence: bool = True,
    ) -> Path:
        """Write a canonical closure artifact; by default with a valid ``safe_close`` evidence record (A4)."""

        if evidence:
            write_evidence(self.root, shipment_id, feature_id, evidence_record("safe_close", shipment_id, feature_id))
            body = with_close_keys(body, "safe_close", evidence_relpath(shipment_id, feature_id))
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

    def test_symlinked_closure_dir_entry_is_not_discovery_evidence(self) -> None:
        # A regular file stored elsewhere must not be "discovered" through a
        # canonically-named link placed in the consumer's closure directory.
        notes = self.root / "notes"
        notes.mkdir()
        stored = build_closure_path("notes", "175-S", "1-F", workspace_root=self.root)
        stored.write_text(_READY, encoding="utf-8")
        alias = self.closure_dir / stored.name.replace("175-S-1-F", "175-S-2-F")
        try:
            os.symlink(stored, alias)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"cannot create file symlink: {exc}")
        payload, code = self._gate(stored)
        self.assertEqual(code, 1)
        self.assertEqual(payload["failed_check"], "discoverability")

    def test_unc_and_device_paths_are_rejected_before_filesystem_access(self) -> None:
        from unittest import mock

        from autoharness.gates import closure_contract

        name = "175-S-167-F-post-merge-closure.md"
        raws = [f"//attacker/share/{name}", os.path.join("..", "..", name)]
        if os.name == "nt":
            raws += [f"\\\\attacker\\share\\{name}", f"\\\\?\\UNC\\attacker\\share\\{name}"]
        for raw in raws:
            with self.subTest(raw=raw), mock.patch.object(
                closure_contract,
                "assert_path_within_workspace",
                side_effect=AssertionError("filesystem resolution attempted"),
            ):
                payload, code = self._gate(raw)
                self.assertEqual(code, 2)
                self.assertEqual(payload["failed_check"], "workspace_containment")

    def test_inspection_oserror_is_invalid_input_not_a_crash(self) -> None:
        from unittest import mock

        artifact = self._canonical()
        with mock.patch("pathlib.Path.is_file", side_effect=PermissionError("denied")):
            payload, code = self._gate(artifact)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")
        self.assertIn("cannot be inspected", payload["message"])

    def test_workspace_symlink_loop_is_invalid_input_not_a_crash(self) -> None:
        from unittest import mock

        artifact = self._canonical()
        with mock.patch("pathlib.Path.resolve", side_effect=RuntimeError("Symlink loop")):
            payload, code = self._gate(artifact)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")
        self.assertIn("workspace root", payload["message"])

    def test_workspace_spelled_through_a_link_is_accepted(self) -> None:
        # The caller's own (unresolved) spelling of the workspace must not be
        # rejected by the textual pre-check that runs before resolution.
        artifact = self._canonical()
        link = self.root.parent / "workspace-link"
        reason = _make_dir_link(link, self.root)
        if reason:
            self.skipTest(reason)
        spelled = link / artifact.relative_to(self.root)
        payload, code = _run_json(
            "gate", "closure-evidence", "--path", str(spelled), "--workspace", str(link)
        )
        self.assertEqual((code, payload["failed_check"]), (0, None), payload["message"])

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
    {
        "gate",
        "path",
        "workspace",
        "shipment_id",
        "canonical_pattern",
        "passed",
        "exit_code",
        "failed_check",
        "message",
        "warnings",
    }
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



class CloseEvidenceRequirementTests(_ClosureWorkspaceMixin, unittest.TestCase):
    """192.007-T (plan unit A4): ``close_path`` and the ``close_evidence`` requirement."""

    def _artifact(
        self,
        close_path: str | None,
        record: dict | str | bytes | None,
        *,
        close_evidence: str | None = None,
        merge_commit: str | None = _MERGE_SHA,
        body: str = _READY,
    ) -> Path:
        for existing in self.closure_dir.glob("*.md"):
            existing.unlink()
        evidence_path = self.root / evidence_relpath("175-S", "167-F")  # textual: never follow a test link
        if evidence_path.is_symlink() or evidence_path.is_file():
            evidence_path.unlink()
        if record is not None:
            write_evidence(self.root, "175-S", "167-F", record)
        keys = with_close_keys(
            body,
            close_path,
            close_evidence if close_evidence is not None else evidence_relpath("175-S", "167-F"),
            merge_commit=merge_commit,
        )
        return self._canonical(body=keys, evidence=False)

    def test_per_path_verdict_table(self) -> None:
        unverified = _engine_record("1.10.1")
        failed = evidence_record("cascade", "175-S", "167-F")
        failed["post_close"]["postcondition_verdict"] = "fail"
        failed["post_close"]["failures"] = ["returned_ids non-empty"]
        foreign = evidence_record("safe_close", "175-S", "167-F")
        foreign["shipment_id"] = "176-S"
        # PR #482 review: stored success conclusions over empty sets and an
        # active shipment are recomputed from captured facts and refused.
        tampered = evidence_record("cascade", "175-S", "167-F")
        tampered["post_close"]["parsed_result"]["shipment_status"] = "active"
        tampered["post_close"]["parsed_result"]["archived_ids"] = []
        tampered["post_close"]["shipment_record_status"] = "active"
        tampered["post_close"]["allowed_ids"] = []
        tampered["post_close"]["required_ids"] = []
        other_shipment_result = evidence_record("cascade", "175-S", "167-F")
        other_shipment_result["post_close"]["parsed_result"]["shipment_id"] = "176-S"
        rows = [
            ("cascade, no record", "cascade", None, "close_evidence"),
            ("cascade, fail verdict record", "cascade", failed, "close_evidence"),
            ("cascade, tampered derived fields", "cascade", tampered, "close_evidence"),
            ("cascade, engine result names another shipment", "cascade", other_shipment_result, "close_evidence"),
            (
                "cascade, UNVERIFIED engine record",
                "cascade",
                evidence_record("cascade", "175-S", "167-F", engine=unverified),
                "close_evidence",
            ),
            ("cascade, valid record", "cascade", evidence_record("cascade", "175-S", "167-F"), None),
            ("safe_close, no record", "safe_close", None, "close_evidence"),
            ("safe_close, cascade record", "safe_close", evidence_record("cascade", "175-S", "167-F"), "close_evidence"),
            ("safe_close, valid record", "safe_close", evidence_record("safe_close", "175-S", "167-F"), None),
            (
                "safe_close, classifier CASCADE with UNVERIFIED engine",
                "safe_close",
                evidence_record("safe_close", "175-S", "167-F", classifier="CASCADE", engine=unverified),
                None,
            ),
            ("mismatched shipment ID in the record", "safe_close", foreign, "close_evidence"),
            ("close_path missing", None, evidence_record("safe_close", "175-S", "167-F"), "close_path"),
            ("close_path out of vocabulary", "CASCADE", evidence_record("cascade", "175-S", "167-F"), "close_path"),
            ("record is not JSON", "safe_close", "not json", "close_evidence"),
            ("record is a JSON array", "safe_close", "[]", "close_evidence"),
        ]
        for label, close_path, record, failed_check in rows:
            with self.subTest(row=label):
                artifact = self._artifact(close_path, record)
                payload, code = self._gate(artifact)
                self.assertEqual(payload["failed_check"], failed_check, payload["message"])
                self.assertEqual(code if code is not None else 0, 0 if failed_check is None else 1)
                self.assertEqual(payload["passed"], failed_check is None)
                self.assertIsInstance(payload["warnings"], list)

        with self.subTest(row="close_evidence key missing"):
            for existing in self.closure_dir.glob("*.md"):
                existing.unlink()
            write_evidence(self.root, "175-S", "167-F", evidence_record("safe_close", "175-S", "167-F"))
            artifact = self._canonical(body=with_close_keys(_READY, "safe_close", None), evidence=False)
            payload, code = self._gate(artifact)
            self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"))

    def test_evidence_path_containment_table(self) -> None:
        valid = evidence_record("safe_close", "175-S", "167-F")
        outside_record = self.outside / "175-S-167-F-close-evidence.json"
        outside_record.write_text(serialize_evidence_record(valid), encoding="utf-8")
        other = evidence_relpath("176-S", "167-F")
        write_evidence(self.root, "176-S", "167-F", evidence_record("safe_close", "176-S", "167-F"))
        rows = [
            ("dot-dot traversal", "docs/closure/evidence/../evidence/175-S-167-F-close-evidence.json"),
            ("escape to outside", "../outside/175-S-167-F-close-evidence.json"),
            ("absolute path", outside_record.as_posix()),
            ("drive-qualified path", "C:/docs/closure/evidence/175-S-167-F-close-evidence.json"),
            ("UNC path", "//attacker/share/175-S-167-F-close-evidence.json"),
            ("backslash separators", "docs\\closure\\evidence\\175-S-167-F-close-evidence.json"),
            ("outside the evidence directory", "docs/closure/175-S-167-F-close-evidence.json"),
            ("another pair's record", other),
        ]
        opened: list[str] = []
        real_open = os.open

        def spy(path, *args, **kwargs):
            opened.append(os.path.abspath(os.fspath(path)))
            return real_open(path, *args, **kwargs)

        from unittest import mock

        for label, close_evidence in rows:
            with self.subTest(row=label):
                artifact = self._artifact("safe_close", valid, close_evidence=close_evidence)
                opened.clear()
                with mock.patch("os.open", side_effect=spy):
                    payload, code = self._gate(artifact)
                self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"), payload["message"])
                self.assertFalse(
                    [path for path in opened if path.startswith(str(self.outside))], "read outside the workspace"
                )

        with self.subTest(row="oversize record"):
            oversize = evidence_record("safe_close", "175-S", "167-F")
            oversize["pre_close"]["captured_at"] = "x" * (_MAX_EVIDENCE_BYTES + 1)
            artifact = self._artifact("safe_close", oversize)
            payload, code = self._gate(artifact)
            self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"))
            self.assertIn("512", payload["message"])

        with self.subTest(row="symlinked record"):
            artifact = self._artifact("safe_close", None)
            link = build_evidence_path(self.root, "175-S", "167-F")
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.symlink(outside_record, link)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"cannot create file symlink: {exc}")
            opened.clear()
            with mock.patch("os.open", side_effect=spy):
                payload, code = self._gate(artifact)
            self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"))
            self.assertFalse([path for path in opened if path.startswith(str(self.outside))])

        with self.subTest(row="junctioned evidence directory"):
            artifact = self._artifact("safe_close", None)
            evidence_dir = (self.root / evidence_relpath("175-S", "167-F")).parent
            for leftover in evidence_dir.iterdir():
                leftover.unlink()
            evidence_dir.rmdir()
            target = self.outside / "evidence"
            target.mkdir()
            (target / "175-S-167-F-close-evidence.json").write_text(
                serialize_evidence_record(evidence_record("safe_close", "175-S", "167-F")), encoding="utf-8"
            )
            reason = _make_dir_link(evidence_dir, target)
            if reason:
                self.skipTest(reason)
            opened.clear()
            with mock.patch("os.open", side_effect=spy):
                payload, code = self._gate(artifact)
            self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"))
            self.assertFalse([path for path in opened if path.startswith(str(self.outside))])

    def test_merge_commit_cross_check(self) -> None:
        record = evidence_record("safe_close", "175-S", "167-F")
        with self.subTest(row="matching merge_commit"):
            payload, code = self._gate(self._artifact("safe_close", copy_record(record)))
            self.assertEqual((code, payload["failed_check"]), (0, None), payload["message"])
            self.assertFalse([w for w in payload["warnings"] if "merge_commit" in w])
        with self.subTest(row="mismatched merge_commit"):
            artifact = self._artifact("safe_close", copy_record(record), merge_commit="0" * 40)
            payload, code = self._gate(artifact)
            self.assertEqual((code, payload["failed_check"]), (1, "close_evidence"))
            self.assertIn("merge_commit", payload["message"])
        with self.subTest(row="absent merge_commit"):
            artifact = self._artifact("safe_close", copy_record(record), merge_commit=None)
            payload, code = self._gate(artifact)
            self.assertEqual((code, payload["failed_check"]), (0, None), payload["message"])
            self.assertTrue([w for w in payload["warnings"] if "merge_commit" in w], payload["warnings"])

    def test_non_regression_pins(self) -> None:
        from autoharness.gates.closure_contract import classify_closure_candidates
        from autoharness.gates.topology import FilesystemTopologyReaders

        with self.subTest(row="BLOCKED still fails frontmatter_predicate first"):
            blocked = self._canonical(
                body="---\ncompaction_status: done\nclosure_status: BLOCKED\n---\n", evidence=False
            )
            payload, code = self._gate(blocked)
            self.assertEqual((code, payload["failed_check"]), (1, "frontmatter_predicate"))
            blocked.unlink()

        with self.subTest(row="INV-P5: the topology reader still accepts an artifact without close_path"):
            committed = self._canonical(evidence=False)
            payload, code = self._gate(committed)
            self.assertEqual((code, payload["failed_check"]), (1, "close_path"))
            self.assertIs(FilesystemTopologyReaders(self.root).closure_complete("175-S"), True)

        with self.subTest(row="classify_closure_candidates ignores docs/closure/evidence/"):
            committed.unlink()
            write_evidence(self.root, "175-S", "167-F", evidence_record("safe_close", "175-S", "167-F"))
            (self.closure_dir / "evidence" / "175-S-167-F-post-merge-closure.md").write_text(_READY, encoding="utf-8")
            discovery = classify_closure_candidates(self.closure_dir, "175-S")
            self.assertEqual(discovery.outcome, "absent")
            self.assertEqual(list(discovery.canonical_matches), [])

        with self.subTest(row="USAGE documents the new failed_check values and warnings[]"):
            out, _err, _code = _run("gate", "--help")
            for token in ("close_path", "close_evidence", "warnings"):
                self.assertIn(token, out)


def copy_record(record: dict) -> dict:
    import copy

    return copy.deepcopy(record)


if __name__ == "__main__":
    unittest.main()
