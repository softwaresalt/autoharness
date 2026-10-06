"""Unit B, task B5 (189.003-T): ``harness resolve`` CLI adapter (one JSON document).

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "B5: CLI adapter".

``autoharness harness resolve --workspace <path> --shipment <id> --json``:
parse errors behave as ordinary argparse (usage on stderr, exit 2, no
document) and ``--help`` prints help to stdout with exit 0 and no document.
After a successful parse the command writes exactly one UTF-8 document and one
LF to stdout, nothing to stderr (CR-B5), and exits with the document's
``exit_code``. IM-03 (B5 half): all 47 codes through ``_resolve`` (small limits
for the read-limit codes), every code reachable with the defaults also through
``resolve_shipment`` and the CLI, and every output validates against the B1
schema. Every fixture is a temporary workspace (IM-10).

``CliEnvelopeRosterTests`` is the expected-RED roster (see its docstring for
the marker attribution). ``CliEnvelopeCharacterizationTests`` (the 47 codes
through ``_resolve``, parse errors and help) and the ``test_structural_*``
tests (the captured help audit and the roster check) reach no CLI stub on
their own and are outside it (reclassified by the 195-S local review).
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from _env_patch import patched_environ
from test_harness_noclaim_audit import audit
from test_harness_surfaces_digest import (
    DEFAULT_READS,
    INSTALLED,
    RENDERED,
    SHIPMENT_ID,
    SHIPMENT_RECORD,
    TEMPLATE,
    ResolverFixture,
    manifest_bytes,
)

from autoharness import cli
from autoharness import harness_surfaces as hs
from autoharness.harness_read import ReadLimits

MARKER = "AHLC_B5_CLI_ENVELOPE"
REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "harness-resolution" / "1.0.0.schema.json"
VALIDATOR = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
MIB = 1024 * 1024
FIRST_PASS = len(DEFAULT_READS)  # first-pass requests of the default fixture
ALL_CODES = tuple(spec.code for spec in hs.REASON_REGISTRY)
DEFAULT_REACHABLE = tuple(code for code in ALL_CODES if code != "FILE_COUNT_LIMIT")


def run_cli(argv: list[str]) -> tuple[int, bytes, bytes]:
    """Run ``cli.main(argv)`` in process; return the exit status and the raw stdout and stderr bytes."""
    out, err = io.BytesIO(), io.BytesIO()
    stdout = io.TextIOWrapper(out, encoding="utf-8", newline="")
    stderr = io.TextIOWrapper(err, encoding="utf-8", newline="")
    status = 0
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            cli.main(argv)
        except SystemExit as exit_:
            status = exit_.code if isinstance(exit_.code, int) else (0 if exit_.code is None else 1)
        finally:
            stdout.flush()
            stderr.flush()
    return status, out.getvalue(), err.getvalue()


def resolve_argv(ws: Path, shipment_id: str = SHIPMENT_ID) -> list[str]:
    return ["harness", "resolve", "--workspace", str(ws), "--shipment", shipment_id, "--json"]


def pad_record(data: bytes, size: int) -> bytes:
    """``data`` padded with body text to exactly ``size`` bytes."""
    return data + b"x" * (size - len(data) - 1) + b"\n"


def child_env() -> dict[str, str]:
    """The environment for a child CLI process: ``src`` first on PYTHONPATH, no stderr-noise switches."""
    env = {key: value for key, value in os.environ.items()
           if key not in ("PYTHONWARNINGS", "PYTHONDEVMODE", "PYTHONVERBOSE")}
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(REPO_ROOT / "src"), env.get("PYTHONPATH"))))
    return env


def captured_help() -> bytes:
    """The captured ``harness resolve --help`` text at a fixed width (a residue unit, IM-14-F51)."""
    with patched_environ(COLUMNS="80"):
        status, out, err = run_cli(["harness", "resolve", "--help"])
    if (status, err) != (0, b""):
        raise AssertionError((status, err))
    return out


class CliFixture(ResolverFixture):
    """One arrangement per reason code over the shared resolver fixture."""

    def arrange(
        self, code: str, ws: Path, defaults: bool = False
    ) -> tuple[str, ReadLimits, dict[int, Callable[[], None]]]:
        """Arrange ``ws`` for ``code``: the shipment ID, the limits and any read-hook actions.

        With ``defaults`` the arrangement reaches ``code`` under the FI-2
        defaults (``FILE_COUNT_LIMIT`` cannot: ``ValueError``).
        """
        manifest = self.path(".autoharness/harness-manifest.yaml", ws)
        template = self.path("templates/" + TEMPLATE, ws)
        installed = self.path(INSTALLED, ws)
        shipment_id, limits = SHIPMENT_ID, ReadLimits()
        actions: dict[int, Callable[[], None]] = {}

        def record(item_id: str, folder: str = "queue") -> Path:
            return self.record_path(item_id, folder, ws)

        def write(item_id: str, data: bytes, folder: str = "queue") -> None:
            self.write_record(item_id, data, folder, ws)

        def task(*labels: str) -> None:
            write("7.002-T", self.task_record("7.002-T", *labels))

        def entries(*items: tuple[str, str, str | None]) -> bytes:
            out = b"variables_used:\n  SKILL_NAME: Harness Architect\n  TEST_COMMAND: make test\nartifacts:\n"
            for path, template_name, checksum in items:
                checksum = hashlib.sha256(RENDERED).hexdigest() if checksum is None else checksum
                out += (
                    b"  - path: " + path.encode() + b"\n    template: " + template_name.encode()
                    + b"\n    checksum: '" + checksum.encode() + b"'\n"
                )
            return out

        if code == "INPUT_CHANGED_DURING_RESOLUTION":
            actions = {FIRST_PASS: lambda: record("7-S").write_bytes(SHIPMENT_RECORD + b"changed\n")}
        elif code == "FILE_COUNT_LIMIT":
            if defaults:
                raise ValueError("FILE_COUNT_LIMIT is not reachable with the defaults (FI-3 margin)")
            limits = ReadLimits(max_files=0)
        elif code == "FILE_SIZE_LIMIT":
            if defaults:
                write("7-S", pad_record(SHIPMENT_RECORD, 4 * MIB + 1))
            else:
                limits = ReadLimits(max_file_bytes=0)
        elif code == "TOTAL_SIZE_LIMIT":
            if defaults:
                # Four 4 MiB records: 16 MiB in the first pass; the recheck passes 32 MiB.
                for item_id in ("7-S", "7-F", "7.001-T", "7.002-T"):
                    write(item_id, pad_record(record(item_id).read_bytes(), 4 * MIB))
            else:
                limits = ReadLimits(max_total_bytes=0)
        elif code == "BACKLOG_ROOT_NOT_FOUND":
            shutil.rmtree(ws / ".backlogit")
        elif code == "BACKLOG_ROOT_AMBIGUOUS":
            (ws / ".backlog").mkdir()
        elif code == "SHIPMENT_ID_INVALID":
            shipment_id = "7S"
        elif code == "SHIPMENT_NOT_FOUND":
            record("7-S").unlink()
        elif code == "SHIPMENT_AMBIGUOUS":
            write("7-S", SHIPMENT_RECORD, "archive")
        elif code == "SHIPMENT_RECORD_INVALID":
            write("7-S", b"no frontmatter\n")
        elif code == "SHIPMENT_ID_MISMATCH":
            write("7-S", SHIPMENT_RECORD.replace(b"id: 7-S", b"id: 8-S"))
        elif code == "MEMBERS_INVALID":
            write("7-S", b"---\nid: 7-S\nartifact_type: shipment\ncustom_fields:\n    items: nope\n---\n")
        elif code == "MEMBERS_EMPTY":
            write("7-S", b"---\nid: 7-S\nartifact_type: shipment\ncustom_fields:\n    items: []\n---\n")
        elif code == "MEMBERS_TOO_MANY":
            write("7-S", self.shipment_record(*(f"7.{index:03d}-T" for index in range(1, 50))))
        elif code == "MEMBER_ID_INVALID":
            write("7-S", self.shipment_record("7-F", "7.001-T", "bad"))
        elif code == "MEMBER_KIND_UNSUPPORTED":
            write("7-S", self.shipment_record("7.001-T", "9-ST"))
        elif code == "MEMBER_DUPLICATE":
            write("7-S", self.shipment_record("7.001-T", "7.001-T"))
        elif code == "MEMBER_NOT_FOUND":
            record("7.002-T").unlink()
        elif code == "MEMBER_AMBIGUOUS":
            write("7.002-T", record("7.002-T").read_bytes(), "archive")
        elif code == "MEMBER_RECORD_INVALID":
            write("7.002-T", b"junk\n")
        elif code == "MEMBER_ID_MISMATCH":
            write("7.002-T", self.task_record("7.003-T", "harness-surface:none"))
        elif code == "NO_TASK_MEMBERS":
            write("7-S", self.shipment_record("7-F"))
        elif code == "FEATURE_DECLARES_SURFACE":
            write("7-F", b"---\nid: 7-F\nartifact_type: feature\nlabels:\n    - harness-surface:none\n---\n")
        elif code == "DECLARATION_MISSING":
            task()
        elif code == "DECLARATION_MALFORMED":
            task("harness-surface:Bad")
        elif code == "DECLARATION_DUPLICATE":
            task("harness-surface:none", "harness-surface:none")
        elif code == "DECLARATION_MIXED":
            task("harness-surface:none", "harness-surface:harness-architect")
        elif code == "SURFACE_UNSUPPORTED":
            task("harness-surface:other-surface")
        elif code == "NO_SURFACES_REQUIRED":
            write("7.001-T", self.task_record("7.001-T", "harness-surface:none"))
        elif code == "MANIFEST_NOT_FOUND":
            manifest.unlink()
        elif code == "MANIFEST_UNREADABLE":
            self.replace_with_directory(manifest)()
        elif code == "MANIFEST_DECODE_INVALID":
            manifest.write_bytes(b"artifacts: []\nnote: \xff\n")
        elif code == "MANIFEST_YAML_INVALID":
            manifest.write_bytes(b"artifacts: [\n")
        elif code == "MANIFEST_DUPLICATE_KEY":
            manifest.write_bytes(b"artifacts: []\nartifacts: []\nvariables_used: {}\n")
        elif code == "MANIFEST_SHAPE_INVALID":
            manifest.write_bytes(b"- 1\n")
        elif code == "MANIFEST_ENTRY_AMBIGUOUS":
            manifest.write_bytes(entries((INSTALLED, TEMPLATE, None), (INSTALLED, TEMPLATE, None)))
        elif code == "MANIFEST_TEMPLATE_MISMATCH":
            manifest.write_bytes(entries((INSTALLED, "skills/other/SKILL.md.tmpl", None)))
        elif code == "MANIFEST_ENTRY_INVALID":
            manifest.write_bytes(entries((INSTALLED, TEMPLATE, "not-a-checksum")))
        elif code == "TEMPLATE_NOT_FOUND":
            template.unlink()
        elif code == "TEMPLATE_UNREADABLE":
            self.replace_with_directory(template)()
        elif code == "TEMPLATE_VARIABLE_UNRESOLVED":
            template.write_bytes(b"# {{UNKNOWN_VARIABLE}}\n")
        elif code == "INSTALLED_UNREADABLE":
            self.replace_with_directory(installed)()
        elif code == "MANIFEST_ENTRY_NOT_FOUND":
            manifest.write_bytes(entries((".github/skills/other/SKILL.md", TEMPLATE, None)))
        elif code == "INSTALLED_NOT_FOUND":
            installed.unlink()
        elif code == "CHECKSUM_MISMATCH":
            installed.write_bytes(RENDERED + b"stale\n")
        elif code == "RENDER_MISMATCH":
            installed.write_bytes(RENDERED + b"stale\n")
            manifest.write_bytes(manifest_bytes(hashlib.sha256(RENDERED + b"stale\n").hexdigest()))
        elif code != "ALL_SURFACES_PRESENT":
            raise KeyError(code)
        return shipment_id, limits, actions

    def assert_document(self, data: bytes, code: str) -> dict[str, Any]:
        """``data`` is exactly one UTF-8 JSON document plus one LF, schema-valid, for ``code``."""
        self.assertTrue(data.endswith(b"\n"), data[-80:])
        self.assertEqual(data.count(b"\n"), 1)
        document = json.loads(data[:-1].decode("utf-8"))
        self.assertEqual([error.message for error in VALIDATOR.iter_errors(document)], [])
        self.assertEqual(document["reason_code"], code)
        self.assertEqual(document["exit_code"], hs.reason_spec(code).exit_code)
        return document


class CliEnvelopeRosterTests(CliFixture):
    """Expected-RED roster: the ``harness resolve`` document envelope (B5).

    Each roster test first runs the command on its own default workspace, so
    in the RED phase (where the CLI stub derived its marker suffix from the
    ``--workspace`` basename) each reached its own marker
    ``AHLC_B5_CLI_ENVELOPE:<test>``. In the RED run of record (76df115c) that
    first call was unasserted in three of the four tests; since the review fix
    it asserts the ``ALL_SURFACES_PRESENT`` document. The RED outcome is the
    same, because the stub raised before any assertion.
    """

    def assert_baseline_document(self) -> None:
        status, out, err = run_cli(resolve_argv(self.ws))
        self.assertEqual((status, err), (0, b""))
        self.assert_document(out, "ALL_SURFACES_PRESENT")

    def test_one_document_per_state_through_the_cli(self) -> None:
        self.assert_baseline_document()
        for code in ("ALL_SURFACES_PRESENT", "CHECKSUM_MISMATCH", "MEMBER_NOT_FOUND"):
            with self.subTest(code=code):
                ws = self.fresh(f"state-{code}")
                self.arrange(code, ws)
                status, out, err = run_cli(resolve_argv(ws))
                document = self.assert_document(out, code)
                self.assertEqual(err, b"")
                self.assertEqual(status, document["exit_code"])
                self.assertEqual(document["state"], hs.reason_spec(code).state.value)

    def test_default_reachable_codes_through_resolve_shipment_and_the_cli(self) -> None:
        self.assert_baseline_document()
        self.assertEqual(len(DEFAULT_REACHABLE), 46)
        with self.assertRaises(ValueError):
            self.arrange("FILE_COUNT_LIMIT", self.fresh("count"), defaults=True)
        for code in DEFAULT_REACHABLE:
            with self.subTest(code=code):
                ws = self.fresh(f"default-{code}")
                shipment_id, limits, actions = self.arrange(code, ws, defaults=True)
                self.assertEqual(limits, ReadLimits())
                with self.reads(actions):
                    result = hs.resolve_shipment(workspace_root=ws, shipment_id=shipment_id)
                self.assertEqual(result.reason_code, code)
                if actions:  # the hook mutated ws: arrange a fresh one for the CLI run
                    ws = self.fresh(f"default-cli-{code}")
                    shipment_id, _limits, actions = self.arrange(code, ws, defaults=True)
                with self.reads(actions):
                    status, out, err = run_cli(resolve_argv(ws, shipment_id))
                document = self.assert_document(out, code)
                self.assertEqual(err, b"")
                self.assertEqual(status, document["exit_code"])
                self.assertEqual(document["inputs_sha256"], result.inputs_sha256)

    def test_stdout_is_one_document_and_one_lf_in_a_real_process(self) -> None:
        self.assert_baseline_document()
        cases = (("ALL_SURFACES_PRESENT", 0), ("INSTALLED_NOT_FOUND", 1), ("SHIPMENT_NOT_FOUND", 2))
        for code, exit_code in cases:
            with self.subTest(code=code):
                ws = self.fresh(f"process-{code}")
                self.arrange(code, ws)
                completed = subprocess.run(
                    [sys.executable, "-c", "from autoharness.cli import main; main()", *resolve_argv(ws)],
                    capture_output=True,
                    env=child_env(),
                    cwd=str(self.scratch),
                    timeout=120,
                    check=False,
                )
                self.assertEqual(completed.stderr, b"")
                document = self.assert_document(completed.stdout, code)
                self.assertEqual(completed.returncode, exit_code)
                self.assertEqual(completed.returncode, document["exit_code"])

    def test_invalid_shipment_id_is_a_document_not_a_parse_error(self) -> None:
        self.assert_baseline_document()
        for shipment_id in ("7S", "../7-S", "", "7-S\n"):
            with self.subTest(shipment_id=shipment_id):
                status, out, err = run_cli(resolve_argv(self.ws, shipment_id))
                document = self.assert_document(out, "SHIPMENT_ID_INVALID")
                self.assertIsNone(document["shipment_id"])
                self.assertEqual((status, err), (2, b""))


class CliEnvelopeCharacterizationTests(CliFixture):
    """Outside the roster (reclassified by the 195-S local review).

    The 47-code test runs ``_resolve`` (green since B4b). The parse-error and
    help tests specify argparse behavior, which a stub-raised marker cannot
    show as missing. In the RED run of record all three errored on the stub;
    their characterization outcomes before B5 are inferred, not observed:
    the 47 codes pass, and parse errors and help needed the ``harness``
    command. The empty, ``--work`` and ``--js`` argv cases were added with
    the review fix that refuses them (before it, argparse abbreviations and
    an empty path were accepted and produced a document).
    """

    def test_all_47_codes_through_resolve_validate_against_the_schema(self) -> None:
        self.assertEqual(len(ALL_CODES), 47)
        seen = set()
        for code in ALL_CODES:
            with self.subTest(code=code):
                ws = self.fresh(f"resolve-{code}")
                shipment_id, limits, actions = self.arrange(code, ws)
                with self.reads(actions):
                    result, _usage = hs._resolve(workspace_root=ws, shipment_id=shipment_id, limits=limits)
                self.assertEqual([error.message for error in VALIDATOR.iter_errors(result.to_document())], [])
                self.assertEqual(result.reason_code, code)
                seen.add(result.reason_code)
        self.assertEqual(seen, set(ALL_CODES))

    def test_parse_errors_emit_no_document(self) -> None:
        ws = str(self.ws)
        for argv in (
            ["harness", "resolve", "--workspace", ws, "--shipment", SHIPMENT_ID],  # no --json
            ["harness", "resolve", "--workspace", ws, "--json"],  # no --shipment
            ["harness", "resolve", "--shipment", SHIPMENT_ID, "--json"],  # no --workspace
            ["harness", "resolve", "--workspace", "", "--shipment", SHIPMENT_ID, "--json"],  # empty
            ["harness", "resolve", "--work", ws, "--shipment", SHIPMENT_ID, "--json"],  # no abbreviations
            ["harness", "resolve", "--workspace", ws, "--shipment", SHIPMENT_ID, "--js"],
            ["harness", "resolve", "--workspace", ws, "--shipment", SHIPMENT_ID, "--json", "--extra"],
            ["harness", "resolve", "--workspace", ws, "--shipment", SHIPMENT_ID, "--json", "positional"],
            ["harness", "resolve", "--workspace", ws, "--shipment"],
            ["harness", "unknown"],
            ["harness"],
        ):
            with self.subTest(argv=argv):
                status, out, err = run_cli(argv)
                self.assertEqual(status, 2)
                self.assertEqual(out, b"")
                self.assertTrue(err.startswith(b"usage:"), err)
                self.assertNotIn(b'"schema_version"', err)
                self.assertIn(b"autoharness harness", err)
                if "" in argv:  # the empty path is refused while parsing, by the resolve parser
                    self.assertIn(b"usage: autoharness harness resolve", err)
                    self.assertIn(b"expected a non-empty path", err)

    def test_help_prints_to_stdout_and_emits_no_document(self) -> None:
        for argv in (
            ["harness", "resolve", "--help"],
            ["harness", "resolve", "--workspace", str(self.ws), "-h"],
            ["harness", "--help"],
        ):
            with self.subTest(argv=argv):
                status, out, err = run_cli(argv)
                self.assertEqual((status, err), (0, b""))
                self.assertTrue(out.startswith(b"usage:"), out)
                self.assertNotIn(b'"schema_version"', out)


class CliEnvelopeStructuralTests(unittest.TestCase):
    def test_structural_roster_markers_pairwise_distinct(self) -> None:
        names = [name for name in dir(CliEnvelopeRosterTests) if name.startswith("test_")]
        markers = [f"{MARKER}:{name}" for name in names]
        self.assertEqual(len(names), 4)
        self.assertEqual(len(set(markers)), len(markers))
        self.assertFalse(any(name.startswith("test_structural_") for name in names))
        self.assertEqual([name for name in dir(CliFixture) if name.startswith("test")], [])

    def test_structural_captured_help_names_the_options_and_has_no_claim_form(self) -> None:
        # IM-14 / PE-SAFETY-06: the captured 'harness resolve --help' text is a residue
        # unit (IM-14-F51). It is captured at a fixed width and run through the plan's
        # audit (lines, space joins and hyphen joins), which must find no claim form.
        text = captured_help()
        for option in (b"--workspace", b"--shipment", b"--json"):
            self.assertIn(option, text)
        root = Path(tempfile.mkdtemp(prefix="ahlc-b5-help-"))
        self.addCleanup(shutil.rmtree, root, True)
        (root / "help.txt").write_bytes(text)
        self.assertEqual(audit(root, ["help.txt"], ()).failures, [])


if __name__ == "__main__":
    unittest.main()