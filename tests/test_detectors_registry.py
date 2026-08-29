"""Registry-loader tests for pre-review detectors (149.003-T / 149.009-T)."""

from __future__ import annotations

import copy
import types
import unittest
from pathlib import Path
from unittest import mock

from autoharness.detectors.registry import DetectorRegistryError, load_detector_registry

_REPO_ROOT = Path(__file__).resolve().parents[1]

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


if __name__ == "__main__":
    unittest.main()
