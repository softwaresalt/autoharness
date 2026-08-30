"""Registry-loader tests for pre-review detectors (149.003-T / 149.009-T)."""

from __future__ import annotations

import copy
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from autoharness.detectors.registry import (
    DetectorRegistryError,
    load_detector_registry,
    load_detector_registry_from_workspace,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMP_ROOT = _REPO_ROOT / ".test-output"

VALID_CONFIG = {
    "detectors": [
        {
            "node_id": "det:D-ART/ART-01@1",
            "applies_when": {"changed_paths_any": [".backlogit/**"]},
            "producer": {
                "kind": "pure",
                "ref": "autoharness.detectors.stub:produce",
                "tool_version_dims": ["python"],
            },
            "validator": {
                "ref": "autoharness.detectors.stub:validate",
                "consumes": [],
            },
            "depends_on": [],
            "severity": "medium",
            "mode": "report_only",
            "remediation": {
                "class": "guided_fix",
                "hint": "Restore the section markers.",
                "target_refs": ["path:.backlogit/templates/task.md"],
                "authority": "stage",
            },
        }
    ]
}


class RegistryLoaderTests(unittest.TestCase):
    def _load(self, config: dict, module=None):
        if module is None:
            module = types.SimpleNamespace(produce=lambda *_args, **_kwargs: None, validate=lambda *_args, **_kwargs: None)
        with mock.patch("importlib.import_module", return_value=module):
            return load_detector_registry(config, _REPO_ROOT)

    def test_absent_registry_yields_zero_nodes(self) -> None:
        registry = load_detector_registry({}, _REPO_ROOT)
        self.assertEqual(registry.nodes, ())
        self.assertEqual(registry.exit_code, 0)

    def test_none_config_yields_zero_nodes(self) -> None:
        registry = load_detector_registry(None, _REPO_ROOT)
        self.assertEqual(registry.nodes, ())
        self.assertEqual(registry.exit_code, 0)

    def test_non_mapping_config_fails_closed(self) -> None:
        for malformed in (["detectors"], "detectors", 42, True):
            with self.subTest(malformed=malformed):
                with self.assertRaises(DetectorRegistryError):
                    load_detector_registry(malformed, _REPO_ROOT)

    def test_from_workspace_raises_detector_registry_error_on_malformed_yaml(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            config_dir = workspace / ".autoharness"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.yaml").write_text("detectors: [unterminated\n", encoding="utf-8")
            with self.assertRaises(DetectorRegistryError):
                load_detector_registry_from_workspace(workspace, _REPO_ROOT)

    def test_from_workspace_raises_detector_registry_error_on_non_mapping_yaml(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            config_dir = workspace / ".autoharness"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
            with self.assertRaises(DetectorRegistryError):
                load_detector_registry_from_workspace(workspace, _REPO_ROOT)

    def test_from_workspace_raises_detector_registry_error_on_falsey_non_mapping_yaml(self) -> None:
        # `yaml.safe_load(...) or {}` would silently coerce any *falsey*
        # non-mapping document (empty list, `false`, `0`, empty string) into
        # an empty registry before `load_detector_registry` could reject it.
        # Only a genuine YAML `null` document is intentionally empty.
        for falsey_yaml in ("[]\n", "false\n", "0\n", '""\n'):
            with self.subTest(falsey_yaml=falsey_yaml):
                _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
                    workspace = Path(tmp)
                    config_dir = workspace / ".autoharness"
                    config_dir.mkdir(parents=True, exist_ok=True)
                    (config_dir / "config.yaml").write_text(falsey_yaml, encoding="utf-8")
                    with self.assertRaises(DetectorRegistryError):
                        load_detector_registry_from_workspace(workspace, _REPO_ROOT)

    def test_from_workspace_yields_zero_nodes_on_yaml_null(self) -> None:
        # A genuine YAML `null` document (e.g. a fully empty/whitespace-only
        # file) is the one legitimately-empty case and must still succeed.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            config_dir = workspace / ".autoharness"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.yaml").write_text("", encoding="utf-8")
            registry = load_detector_registry_from_workspace(workspace, _REPO_ROOT)
            self.assertEqual(registry.nodes, ())
            self.assertEqual(registry.exit_code, 0)

    def test_from_workspace_raises_detector_registry_error_on_undecodable_bytes(self) -> None:
        # An unreadable/undecodable config.yaml (e.g. invalid UTF-8) must
        # follow the same documented exit-2 `DetectorRegistryError` path as
        # a malformed-YAML config, not escape as an uncaught exception that
        # the CLI's `except DetectorRegistryError` would fail to catch.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            config_dir = workspace / ".autoharness"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.yaml").write_bytes(b"\xff\xfe\x00\x01not valid utf-8")
            with self.assertRaises(DetectorRegistryError):
                load_detector_registry_from_workspace(workspace, _REPO_ROOT)

    def test_valid_registry_loads_node_specs(self) -> None:
        registry = self._load(copy.deepcopy(VALID_CONFIG))
        self.assertEqual(registry.exit_code, 0)
        self.assertEqual(len(registry.nodes), 1)
        self.assertEqual(registry.nodes[0].node_id, "det:D-ART/ART-01@1")
        self.assertTrue(callable(registry.nodes[0].producer.handler))
        self.assertTrue(callable(registry.nodes[0].validator.handler))

    def test_out_of_namespace_ref_is_rejected_without_importing(self) -> None:
        config = copy.deepcopy(VALID_CONFIG)
        config["detectors"][0]["producer"]["ref"] = "os:path.join"
        with mock.patch("importlib.import_module") as import_module:
            with self.assertRaises(DetectorRegistryError):
                load_detector_registry(config, _REPO_ROOT)
        import_module.assert_not_called()

    def test_unimportable_in_namespace_ref_is_invalid(self) -> None:
        config = copy.deepcopy(VALID_CONFIG)
        with mock.patch("importlib.import_module", side_effect=ModuleNotFoundError("missing")):
            with self.assertRaises(DetectorRegistryError):
                load_detector_registry(config, _REPO_ROOT)

    def test_registry_rejects_duplicate_unknown_and_command_defects(self) -> None:
        duplicate = copy.deepcopy(VALID_CONFIG)
        duplicate["detectors"].append(copy.deepcopy(duplicate["detectors"][0]))
        with self.assertRaises(DetectorRegistryError):
            self._load(duplicate)

        unknown_dep = copy.deepcopy(VALID_CONFIG)
        unknown_dep["detectors"][0]["depends_on"] = ["det:D-ART/ART-02@1"]
        with self.assertRaises(DetectorRegistryError):
            self._load(unknown_dep)

        blocking = copy.deepcopy(VALID_CONFIG)
        blocking["detectors"][0]["mode"] = "blocking"
        with self.assertRaises(DetectorRegistryError):
            self._load(blocking)

        command = copy.deepcopy(VALID_CONFIG)
        command["detectors"][0]["producer"]["kind"] = "command"
        with self.assertRaises(DetectorRegistryError):
            self._load(command)

    def _two_node_config(self) -> dict:
        first = copy.deepcopy(VALID_CONFIG["detectors"][0])
        second = copy.deepcopy(VALID_CONFIG["detectors"][0])
        second["node_id"] = "det:D-ART/ART-02@1"
        return {"detectors": [first, second]}

    def test_registry_rejects_dependency_cycle_at_load_time(self) -> None:
        config = self._two_node_config()
        config["detectors"][0]["depends_on"] = ["det:D-ART/ART-02@1"]
        config["detectors"][1]["depends_on"] = ["det:D-ART/ART-01@1"]
        with self.assertRaises(DetectorRegistryError) as ctx:
            self._load(config)
        self.assertIn("cycle", str(ctx.exception).lower())

    def test_registry_rejects_consumes_reference_to_unknown_node(self) -> None:
        config = self._two_node_config()
        config["detectors"][0]["depends_on"] = ["det:D-ART/ART-02@1"]
        config["detectors"][0]["validator"]["consumes"] = ["det:D-ART/ART-99@1"]
        with self.assertRaises(DetectorRegistryError) as ctx:
            self._load(config)
        self.assertIn("consumes", str(ctx.exception).lower())

    def test_registry_rejects_consumes_not_declared_as_a_dependency(self) -> None:
        config = self._two_node_config()
        # ART-01 declares it consumes ART-02's evidence but never depends_on it,
        # so evaluation order would not guarantee ART-02 already ran.
        config["detectors"][0]["validator"]["consumes"] = ["det:D-ART/ART-02@1"]
        with self.assertRaises(DetectorRegistryError) as ctx:
            self._load(config)
        self.assertIn("depends_on", str(ctx.exception).lower())

    def test_registry_accepts_consumes_that_is_a_subset_of_depends_on(self) -> None:
        config = self._two_node_config()
        config["detectors"][0]["depends_on"] = ["det:D-ART/ART-02@1"]
        config["detectors"][0]["validator"]["consumes"] = ["det:D-ART/ART-02@1"]
        registry = self._load(config)
        self.assertEqual(registry.exit_code, 0)
        self.assertEqual(len(registry.nodes), 2)

    def test_registry_normalizes_evidence_suffix_on_sibling_consumes(self) -> None:
        # D3 evidence-reference syntax (design doc): `<node_id>#evidence` is
        # accepted sugar for the bare `<node_id>` form already exercised
        # above. The suffix must be stripped consistently so the same
        # depends_on-subset rule applies regardless of which form is used.
        config = self._two_node_config()
        config["detectors"][0]["depends_on"] = ["det:D-ART/ART-02@1"]
        config["detectors"][0]["validator"]["consumes"] = ["det:D-ART/ART-02@1#evidence"]
        registry = self._load(config)
        self.assertEqual(registry.exit_code, 0)
        self.assertEqual(registry.nodes[0].validator.consumes, ("det:D-ART/ART-02@1",))

    def test_registry_accepts_self_evidence_reference_without_depends_on(self) -> None:
        # The schema example (tests/test_validation_gates_schema.py) declares
        # `consumes: ["det:D-ART/ART-01@1#evidence"]` on the SAME node with
        # `depends_on: []` -- a self-reference to the node's own
        # just-produced evidence, which the assembler always supplies
        # unconditionally. This must load successfully rather than raising
        # "unknown node" (missing suffix normalization) or "must also be
        # declared in depends_on" (a node can never depend on itself).
        config = copy.deepcopy(VALID_CONFIG)
        config["detectors"][0]["validator"]["consumes"] = ["det:D-ART/ART-01@1#evidence"]
        registry = self._load(config)
        self.assertEqual(registry.exit_code, 0)
        self.assertEqual(registry.nodes[0].validator.consumes, ("det:D-ART/ART-01@1",))

    def test_registry_rejects_sibling_evidence_reference_missing_from_depends_on(self) -> None:
        # A sibling `#evidence` reference still needs the depends_on
        # declaration for evaluation-order safety -- only the self-reference
        # case above is exempt.
        config = self._two_node_config()
        config["detectors"][0]["validator"]["consumes"] = ["det:D-ART/ART-02@1#evidence"]
        with self.assertRaises(DetectorRegistryError) as ctx:
            self._load(config)
        self.assertIn("depends_on", str(ctx.exception).lower())

    def test_schema_example_self_evidence_consumes_loads_via_full_config_validation(self) -> None:
        # End-to-end coverage of the exact schema-validated example from
        # tests/test_validation_gates_schema.py's DETECTOR_CONFIG, which
        # previously failed registry loading with "unknown node" despite
        # being schema-valid.
        config = {
            "detectors": [
                {
                    "node_id": "det:D-ART/ART-01@1",
                    "applies_when": {"changed_paths_any": [".backlogit/**"]},
                    "producer": {
                        "kind": "pure",
                        "ref": "autoharness.detectors.stub:produce",
                        "tool_version_dims": ["python"],
                    },
                    "validator": {
                        "ref": "autoharness.detectors.stub:validate",
                        "consumes": ["det:D-ART/ART-01@1#evidence"],
                    },
                    "depends_on": [],
                    "severity": "medium",
                    "mode": "report_only",
                    "remediation": {
                        "class": "guided_fix",
                        "hint": "Restore required section markers.",
                        "target_refs": ["path:.backlogit/templates/task.md"],
                        "authority": "stage",
                    },
                }
            ]
        }
        registry = self._load(config)
        self.assertEqual(registry.exit_code, 0)
        self.assertEqual(len(registry.nodes), 1)


if __name__ == "__main__":
    unittest.main()
