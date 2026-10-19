"""Version-agnostic access to the harness-config schema contract (208-F B3a).

Test modules that validate current-version fixtures must read the harness-config
schema version and current mirror path ONLY through this module, so the atomic
contract cut-over (root schema const, ``SCHEMA_CONTRACTS`` current_version,
current mirror file, dogfood marker) never cascades into hardcoded literals.

The module name does not match the ``test*.py`` discovery pattern, so it is
never collected as a test module itself.
"""

from __future__ import annotations

from pathlib import Path

from autoharness.schema_contracts import SCHEMA_CONTRACTS

_REPO_ROOT = Path(__file__).resolve().parents[1]

CURRENT_CONFIG_SCHEMA_VERSION: str = str(SCHEMA_CONTRACTS["config"]["current_version"])


def current_config_mirror_path() -> Path:
    """Return the versioned harness-config mirror for the current contract version."""
    contract = SCHEMA_CONTRACTS["config"]
    return _REPO_ROOT / "schemas" / contract["versioned_schema_dir"] / f"{CURRENT_CONFIG_SCHEMA_VERSION}.schema.json"
