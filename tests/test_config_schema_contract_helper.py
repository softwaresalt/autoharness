"""Guards the version-agnostic harness-config test helper (208-F B3a/B3b).

The schema modules that validate current-version fixtures must obtain the
harness-config schema version and current mirror path only through
``tests/_config_schema_contract.py``. Hardcoding the literal would make the
atomic cut-over (B5) cascade into every one of those modules.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from _config_schema_contract import CURRENT_CONFIG_SCHEMA_VERSION, current_config_mirror_path
from autoharness.schema_contracts import SCHEMA_CONTRACTS

_TESTS_DIR = Path(__file__).resolve().parent
_ROOT_CONFIG_SCHEMA = _TESTS_DIR.parent / "schemas" / "harness-config.schema.json"

_VERSION_AGNOSTIC_MODULES = (
    "test_escalation_hierarchy_schema.py",
    "test_anchor_review_routing.py",
    "test_context_tier_schema.py",
    "test_context_tier_resolution.py",
)
_HARDCODED_PIN = re.compile(r"1\.1\.0")


class ConfigSchemaContractHelperTests(unittest.TestCase):
    def test_current_version_comes_from_schema_contracts(self) -> None:
        self.assertEqual(
            CURRENT_CONFIG_SCHEMA_VERSION,
            str(SCHEMA_CONTRACTS["config"]["current_version"]),
        )

    def test_current_mirror_exists_and_pins_current_version(self) -> None:
        mirror = current_config_mirror_path()
        self.assertTrue(mirror.is_file(), f"current mirror missing: {mirror}")
        self.assertEqual(mirror.name, f"{CURRENT_CONFIG_SCHEMA_VERSION}.schema.json")
        schema = json.loads(mirror.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], CURRENT_CONFIG_SCHEMA_VERSION)

    def test_root_schema_tracks_current_version(self) -> None:
        root = json.loads(_ROOT_CONFIG_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(root["properties"]["schema_version"]["const"], CURRENT_CONFIG_SCHEMA_VERSION)

    def test_version_agnostic_modules_carry_no_hardcoded_pin(self) -> None:
        for name in _VERSION_AGNOSTIC_MODULES:
            source = (_TESTS_DIR / name).read_text(encoding="utf-8")
            self.assertIsNone(
                _HARDCODED_PIN.search(source),
                f"{name} hardcodes the 1.1.0 harness-config pin; use tests/_config_schema_contract.py",
            )


if __name__ == "__main__":
    unittest.main()
