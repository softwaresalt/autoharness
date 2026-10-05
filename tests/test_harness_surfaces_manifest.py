"""Unit B, task B3 (188.003-T): manifest snapshot and surface classification.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "B3: Manifest snapshot and surface classification".

The private helper under test is ``harness_surfaces._classify_surfaces(reader,
*, surface_ids)``. Every fixture is a real temporary workspace named after the
test method; no test reads the real repository surface (IM-10). In the RED
phase the stub derives its marker suffix from that request (the reader's
workspace directory name), so each roster test reaches its own marker
``AHLC_B3_MANIFEST_CLASSIFY:<test>``. ``ManifestRosterTests`` is the
expected-RED roster; ``test_structural_*`` tests (the renderer alias and the
roster check) reach no stub and are outside it.
"""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

from autoharness import harness_surfaces as hs
from autoharness import verify_workspace
from autoharness.harness_read import ReadErrorCode, ReadLimits, open_reader

MARKER = "AHLC_B3_MANIFEST_CLASSIFY"
INSTALLED = ".github/skills/harness-architect/SKILL.md"
TEMPLATE = "skills/harness-architect/SKILL.md.tmpl"
TEMPLATE_TEXT = "# {{SKILL_NAME}}\n\nRun `{{TEST_COMMAND}}`.\n"
VARIABLES = {"SKILL_NAME": "Harness Architect", "TEST_COMMAND": "make test", "UNUSED": "x"}
RENDERED = b"# Harness Architect\n\nRun `make test`.\n"


class ManifestFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = Path(tempfile.mkdtemp(prefix="ahlc-b3-"))
        self.addCleanup(shutil.rmtree, self.scratch, True)
        self.ws = self.scratch / self._testMethodName
        (self.ws / ".autoharness").mkdir(parents=True)
        self.template_path = self.ws / "templates" / TEMPLATE
        self.installed_path = self.ws / INSTALLED
        self.template_path.parent.mkdir(parents=True)
        self.installed_path.parent.mkdir(parents=True)
        self.template_path.write_bytes(TEMPLATE_TEXT.encode("utf-8"))
        self.installed_path.write_bytes(RENDERED)
        self.entry: dict[str, Any] = {
            "path": INSTALLED,
            "primitive": 4,
            "template": TEMPLATE,
            "checksum": hashlib.sha256(RENDERED).hexdigest(),
        }
        self.write_manifest()

    def manifest(self, entries: list[Any] | None = None, variables: Any = None, **extra: Any) -> dict[str, Any]:
        other = {"path": ".github/agents/x.agent.md", "template": "agents/x.agent.md.tmpl", "checksum": "0" * 64}
        return {
            "schema_version": "1.0.0",
            "artifacts": [other, self.entry] if entries is None else entries,
            "variables_used": dict(VARIABLES) if variables is None else variables,
            **extra,
        }

    def write_manifest(self, data: Any = None, raw: bytes | None = None) -> None:
        path = self.ws / ".autoharness" / "harness-manifest.yaml"
        if raw is None:
            raw = yaml.safe_dump(self.manifest() if data is None else data, sort_keys=False).encode("utf-8")
        path.write_bytes(raw)

    def classify(self, surface_ids: tuple[str, ...] = ("harness-architect",), limits: ReadLimits | None = None) -> Any:
        reader = open_reader(workspace_root=self.ws, limits=limits)
        return hs._classify_surfaces(reader, surface_ids=surface_ids), reader

    def assert_global(self, code: str) -> Any:
        result, _reader = self.classify()
        self.assertEqual(result.global_code, code)
        self.assertEqual(result.rows, ())
        self.assertEqual(result.reason_code, code)
        return result

    def assert_row(self, code: str, state: str) -> Any:
        result, _reader = self.classify()
        self.assertIsNone(result.global_code)
        self.assertEqual(
            result.rows,
            (hs.SurfaceRow("harness-architect", INSTALLED, TEMPLATE, hs.SurfaceState[state], code),),
        )
        self.assertEqual(result.reason_code, code)
        return result


class ManifestRosterTests(ManifestFixture):
    """Expected-RED roster: one fixture per class 5, 6 and 7 code, plus B3 bounds."""

    # Class 5: global manifest failures (no per-surface rows).

    def test_manifest_not_found(self) -> None:
        (self.ws / ".autoharness" / "harness-manifest.yaml").unlink()
        self.assert_global("MANIFEST_NOT_FOUND")

    def test_manifest_unreadable(self) -> None:
        path = self.ws / ".autoharness" / "harness-manifest.yaml"
        path.unlink()
        path.mkdir()
        self.assert_global("MANIFEST_UNREADABLE")

    def test_manifest_decode_invalid(self) -> None:
        self.write_manifest(raw=b"schema_version: '1.0.0'\nnote: \xff\xfe\n")
        self.assert_global("MANIFEST_DECODE_INVALID")

    def test_manifest_yaml_invalid(self) -> None:
        for raw in (
            b"artifacts: [\n",
            b"a: 1\n---\nb: 2\n",
            b"x: &a 1\ny: *a\n",
            b"\t- bad\n:",
            b"<<: {artifacts: []}\nvariables_used: {}\n",
            b"artifacts: []\nvariables_used: {}\ncreated: 2026-13-01\n",
            b"artifacts: []\nvariables_used: {}\nx: " + b"9" * 5000 + b"\n",
            b"artifacts: []\nvariables_used: {}\nx: " + b"[" * 2000 + b"]" * 2000 + b"\n",
        ):
            with self.subTest(raw=raw):
                self.write_manifest(raw=raw)
                self.assert_global("MANIFEST_YAML_INVALID")

    def test_manifest_duplicate_key(self) -> None:
        top = b"artifacts: []\nartifacts: []\nvariables_used: {}\n"
        nested = (
            b"artifacts:\n  - path: .github/skills/harness-architect/SKILL.md\n"
            b"    template: a\n    template: b\n    checksum: '0'\nvariables_used: {}\n"
        )
        for raw in (top, nested):
            with self.subTest(raw=raw):
                self.write_manifest(raw=raw)
                self.assert_global("MANIFEST_DUPLICATE_KEY")

    def test_manifest_shape_invalid(self) -> None:
        shapes: list[Any] = [
            ["artifacts"],
            "text",
            None,
            {"variables_used": dict(VARIABLES)},
            {"artifacts": {"path": INSTALLED}, "variables_used": dict(VARIABLES)},
            {"artifacts": ["x"], "variables_used": dict(VARIABLES)},
            {"artifacts": [{"template": TEMPLATE}], "variables_used": dict(VARIABLES)},
            {"artifacts": [{"path": 3}], "variables_used": dict(VARIABLES)},
            {"artifacts": [self.entry]},
            {"artifacts": [self.entry], "variables_used": ["SKILL_NAME"]},
            {"artifacts": [self.entry], "variables_used": {"SKILL_NAME": 3}},
            {"artifacts": [self.entry], "variables_used": {3: "x"}},
        ]
        for shape in shapes:
            with self.subTest(shape=shape):
                self.write_manifest(raw=yaml.safe_dump(shape).encode("utf-8"))
                self.assert_global("MANIFEST_SHAPE_INVALID")

    # Class 6: INVALID surface rows.

    def test_manifest_entry_ambiguous(self) -> None:
        self.write_manifest(self.manifest(entries=[self.entry, dict(self.entry)]))
        self.assert_row("MANIFEST_ENTRY_AMBIGUOUS", "INVALID")

    def test_manifest_template_mismatch(self) -> None:
        self.write_manifest(self.manifest(entries=[{**self.entry, "template": "skills/other/SKILL.md.tmpl"}]))
        self.assert_row("MANIFEST_TEMPLATE_MISMATCH", "INVALID")
        # Listed order: a template mismatch outranks an invalid checksum on the same entry.
        self.write_manifest(self.manifest(entries=[{**self.entry, "template": "x", "checksum": "bad"}]))
        self.assert_row("MANIFEST_TEMPLATE_MISMATCH", "INVALID")

    def test_manifest_entry_invalid(self) -> None:
        for change in (
            {"template": 3},
            {"template": None},
            {"checksum": "XYZ"},
            {"checksum": "A" * 64},
            {"checksum": 7},
        ):
            with self.subTest(change=change):
                self.write_manifest(self.manifest(entries=[{**self.entry, **change}]))
                self.assert_row("MANIFEST_ENTRY_INVALID", "INVALID")
        entry = dict(self.entry)
        del entry["checksum"]
        self.write_manifest(self.manifest(entries=[entry]))
        self.assert_row("MANIFEST_ENTRY_INVALID", "INVALID")

    def test_template_not_found(self) -> None:
        self.template_path.unlink()
        self.assert_row("TEMPLATE_NOT_FOUND", "INVALID")
        shutil.rmtree(self.ws / "templates")
        self.assert_row("TEMPLATE_NOT_FOUND", "INVALID")

    def test_template_unreadable(self) -> None:
        self.template_path.write_bytes(b"# \xff\n")
        self.assert_row("TEMPLATE_UNREADABLE", "INVALID")
        self.template_path.unlink()
        self.template_path.mkdir()
        self.assert_row("TEMPLATE_UNREADABLE", "INVALID")

    def test_template_variable_unresolved(self) -> None:
        self.write_manifest(self.manifest(variables={"SKILL_NAME": "Harness Architect"}))
        self.assert_row("TEMPLATE_VARIABLE_UNRESOLVED", "INVALID")

    def test_installed_unreadable(self) -> None:
        self.installed_path.unlink()
        self.installed_path.mkdir()
        self.assert_row("INSTALLED_UNREADABLE", "INVALID")

    # Class 7: MISSING and STALE surface rows.

    def test_manifest_entry_not_found(self) -> None:
        self.write_manifest(self.manifest(entries=[{**self.entry, "path": ".github/skills/other/SKILL.md"}]))
        self.assert_row("MANIFEST_ENTRY_NOT_FOUND", "MISSING")
        self.write_manifest(self.manifest(entries=[]))
        self.assert_row("MANIFEST_ENTRY_NOT_FOUND", "MISSING")

    def test_installed_not_found(self) -> None:
        self.installed_path.unlink()
        self.assert_row("INSTALLED_NOT_FOUND", "MISSING")

    def test_checksum_mismatch(self) -> None:
        self.write_manifest(self.manifest(entries=[{**self.entry, "checksum": "0" * 64}]))
        self.assert_row("CHECKSUM_MISMATCH", "STALE")
        # Both disagree: listed order puts CHECKSUM_MISMATCH first.
        self.installed_path.write_bytes(RENDERED + b"edited\n")
        self.assert_row("CHECKSUM_MISMATCH", "STALE")

    def test_render_mismatch(self) -> None:
        edited = RENDERED.replace(b"\n", b"\r\n")
        self.installed_path.write_bytes(edited)
        self.write_manifest(self.manifest(entries=[{**self.entry, "checksum": hashlib.sha256(edited).hexdigest()}]))
        self.assert_row("RENDER_MISMATCH", "STALE")

    # Class 8 and bounds.

    def test_all_surfaces_present(self) -> None:
        result, reader = self.classify()
        self.assert_row("ALL_SURFACES_PRESENT", "PRESENT")
        self.assertIsNone(result.read_limit)
        self.assertEqual(reader.usage.files_claimed, 3)
        # A CRLF template renders as LF (one grammar; UTF-8, LF).
        self.template_path.write_bytes(TEMPLATE_TEXT.replace("\n", "\r\n").encode("utf-8"))
        self.assert_row("ALL_SURFACES_PRESENT", "PRESENT")

    def test_empty_union_reads_nothing(self) -> None:
        (self.ws / ".autoharness" / "harness-manifest.yaml").unlink()
        result, reader = self.classify(surface_ids=())
        self.assertEqual((result.global_code, result.rows, result.read_limit), (None, (), None))
        self.assertIsNone(result.reason_code)
        self.assertEqual(reader.usage.files_claimed, 0)

    def test_read_limit_stops_reads(self) -> None:
        cases = (
            (ReadLimits(max_file_bytes=16), ReadErrorCode.FILE_SIZE_LIMIT, hs.ReadStage.MANIFEST, 1),
            (ReadLimits(max_files=1), ReadErrorCode.FILE_COUNT_LIMIT, hs.ReadStage.TEMPLATE, 1),
            (ReadLimits(max_files=2), ReadErrorCode.FILE_COUNT_LIMIT, hs.ReadStage.INSTALLED, 2),
        )
        for limits, code, stage, claimed in cases:
            with self.subTest(code=code, stage=stage):
                result, reader = self.classify(limits=limits)
                self.assertEqual(result.read_limit, hs.ReadLimitHit(code, stage))
                self.assertEqual((result.global_code, result.rows), (None, ()))
                self.assertEqual(reader.usage.files_claimed, claimed)
        # Byte limits after the manifest prove no later read (FI-5): the installed
        # file is never claimed after a template byte limit.
        manifest_size = (self.ws / ".autoharness" / "harness-manifest.yaml").stat().st_size
        self.template_path.write_bytes(TEMPLATE_TEXT.encode("utf-8") + b"pad\n" * 2048)
        for limits, code in (
            (ReadLimits(max_file_bytes=manifest_size + 64), ReadErrorCode.FILE_SIZE_LIMIT),
            (ReadLimits(max_total_bytes=manifest_size + 64), ReadErrorCode.TOTAL_SIZE_LIMIT),
        ):
            with self.subTest(code=code, stage="template bytes"):
                result, reader = self.classify(limits=limits)
                self.assertEqual(result.read_limit, hs.ReadLimitHit(code, hs.ReadStage.TEMPLATE))
                self.assertEqual(reader.usage.files_claimed, 2)


class ManifestReviewFixTests(ManifestFixture):
    """Local-review fixes (194-S): bounded rendering and total classification."""

    def test_chained_variables_render_is_bounded(self) -> None:
        # Each value names the next variable 64 times: unbounded sequential rendering
        # grows to 64**3 * 40 characters (over 10 MB), past the 4 MiB per-file read
        # bound, so no installed file the reader can read could ever match it.
        variables = {
            **VARIABLES,
            "TEST_COMMAND": "{{V1}}" * 64,
            "V1": "{{V2}}" * 64,
            "V2": "{{V3}}" * 64,
            "V3": "y" * 40,
        }
        self.write_manifest(self.manifest(variables=variables))
        self.assert_row("TEMPLATE_UNREADABLE", "INVALID")

    def test_render_within_bound_still_classifies(self) -> None:
        variables = {**VARIABLES, "TEST_COMMAND": "{{V1}}" * 4, "V1": "make test"}
        self.write_manifest(self.manifest(variables=variables))
        self.assert_row("RENDER_MISMATCH", "STALE")

    def test_surrogate_variable_is_a_render_mismatch(self) -> None:
        raw = (
            b"artifacts:\n- path: " + INSTALLED.encode() + b"\n  template: " + TEMPLATE.encode()
            + b"\n  checksum: '" + hashlib.sha256(RENDERED).hexdigest().encode() + b"'\n"
            + b'variables_used:\n  SKILL_NAME: "\\uD800"\n  TEST_COMMAND: make test\n'
        )
        self.write_manifest(raw=raw)
        self.assert_row("RENDER_MISMATCH", "STALE")


class ManifestRosterStructuralTests(unittest.TestCase):
    def test_structural_roster_markers_pairwise_distinct(self) -> None:
        names = [name for name in dir(ManifestRosterTests) if name.startswith("test_")]
        markers = [f"{MARKER}:{name}" for name in names]
        self.assertEqual(len(names), 20)
        self.assertEqual(len(set(markers)), len(markers))
        self.assertFalse(any(name.startswith("test_structural_") for name in names))


class RendererAliasStructuralTests(unittest.TestCase):
    def test_structural_render_template_alias(self) -> None:
        self.assertIs(verify_workspace.render_template, verify_workspace._render_template)


if __name__ == "__main__":
    unittest.main()
