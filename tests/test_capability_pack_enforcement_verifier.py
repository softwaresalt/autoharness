"""Behavior matrix for ``_check_capability_pack_enforcement`` (075.002-T).

Covers: no pack enabled (no-op vs orphaned overlay), engram-only / graphtor-only
/ both enabled, missing file, missing manifest entry, missing/empty checksum,
checksum mismatch (tampering), wrong route set, wrong/missing deferral set,
gutted safeguard marker, flipped applyTo, unresolved placeholder, and the
config-authoritative-when-present enabled-set gate (in both divergence
directions). Also guards that the verifier's ``RETRIEVAL_ENFORCED_PACKS``
constant equals the ``retrieval_enforced``-marked set in the capability-pack
registry data.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from autoharness.verify_workspace import (
    RETRIEVAL_ENFORCED_PACKS,
    verify_workspace,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REGISTRY_DATA = _REPO_ROOT / "templates" / "packs" / "capability-pack-registry.yaml"
_CPE_REL = ".github/instructions/capability-pack-enforcement.instructions.md"

_ROUTE_ROWS = {
    "agent-engram": "| code | agent-engram | <!-- route:agent-engram --> |\n",
    "graphtor-docs": "| docs | graphtor-docs | <!-- route:graphtor-docs --> |\n",
}
_DEFER_BULLETS = {
    "agent-engram": (
        "* `.github/instructions/agent-engram.instructions.md` "
        "<!-- defer:agent-engram -->\n"
    ),
    "graphtor-docs": (
        "* `.github/instructions/graphtor-docs.instructions.md` "
        "<!-- defer:graphtor-docs -->\n"
    ),
}
_SAFEGUARDS = (
    "<!-- safeguard:pack-deferral -->",
    "<!-- safeguard:direct-search-exemptions -->",
    "<!-- safeguard:per-phase-health-reuse -->",
    "<!-- safeguard:internal-no-public-web -->",
)


def _instruction(
    route_ids,
    *,
    defer_ids=None,
    include_defer_block: bool = True,
    apply_to: str = "**",
    drop_safeguard: str | None = None,
    placeholder: bool = False,
) -> str:
    if defer_ids is None:
        defer_ids = route_ids
    rows = "".join(_ROUTE_ROWS[r] for r in route_ids)
    defers = "".join(_DEFER_BULLETS[d] for d in defer_ids)
    safeguards = "\n".join(m for m in _SAFEGUARDS if m != drop_safeguard)
    defer_block = (
        f"<!-- BEGIN:capability-pack-deferral -->\n"
        f"{defers}"
        f"<!-- END:capability-pack-deferral -->\n\n"
        if include_defer_block
        else ""
    )
    body = (
        f"---\n"
        f"description: \"cpe\"\n"
        f"applyTo: '{apply_to}'\n"
        f"---\n\n"
        f"# Capability-Pack Usage-Enforcement Instructions\n\n"
        f"{safeguards}\n\n"
        f"{defer_block}"
        f"<!-- BEGIN:capability-pack-routes -->\n"
        f"{rows}"
        f"<!-- END:capability-pack-routes -->\n"
    )
    if placeholder:
        body += "\nUnresolved {{PROJECT_NAME}} token.\n"
    return body


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_STRICT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["schema_version"],
    "properties": {"schema_version": {"type": "string", "const": "1.0.0"}},
}


def _run(
    *,
    manifest_packs,
    config_packs,
    file_text: str | None,
    manifest_checksum: str | None,
    manifest_listed: bool,
    crlf: bool = False,
):
    """Build a temp workspace and return the targeted_checks dict."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        home = root / "home"
        ws = root / "ws"
        (home / "schemas" / "harness-manifest").mkdir(parents=True)
        (home / "schemas" / "harness-config").mkdir(parents=True)
        (home / "schemas" / "workspace-profile").mkdir(parents=True)
        (ws / ".autoharness").mkdir(parents=True)
        (ws / ".github" / "instructions").mkdir(parents=True)

        for name in (
            "harness-manifest.schema.json",
            "harness-config.schema.json",
            "workspace-profile.schema.json",
        ):
            (home / "schemas" / name).write_text(json.dumps(_STRICT_SCHEMA))
        for sdir in ("harness-manifest", "harness-config", "workspace-profile"):
            (home / "schemas" / sdir / "1.0.0.schema.json").write_text(
                json.dumps(_STRICT_SCHEMA)
            )

        artifacts = []
        if manifest_listed:
            entry = {"path": _CPE_REL, "template": "x.tmpl", "primitive": 6}
            if manifest_checksum is not None:
                entry["checksum"] = manifest_checksum
            artifacts.append(entry)

        manifest = {
            "schema_version": "1.0.0",
            "installed_at": "2026-05-09T00:00:00Z",
            "autoharness_version": "1.0.0",
            "profile_hash": "abc",
            "primitives_installed": [6],
            "capability_packs": list(manifest_packs),
            "artifacts": artifacts,
        }
        (ws / ".autoharness" / "harness-manifest.yaml").write_text(
            yaml.safe_dump(manifest), encoding="utf-8"
        )
        config: dict = {"schema_version": "1.0.0"}
        if config_packs is not None:
            config["capability_packs"] = list(config_packs)
        (ws / ".autoharness" / "config.yaml").write_text(
            yaml.safe_dump(config),
            encoding="utf-8",
        )
        (ws / ".autoharness" / "workspace-profile.yaml").write_text(
            yaml.safe_dump({"schema_version": "1.0.0"}), encoding="utf-8"
        )

        if file_text is not None:
            data = file_text.encode("utf-8")
            if crlf:
                data = data.replace(b"\n", b"\r\n")
            (ws / _CPE_REL).write_bytes(data)

        return verify_workspace(ws, home)["targeted_checks"]


class CapabilityPackEnforcementVerifierTests(unittest.TestCase):
    def test_no_pack_no_file_is_noop(self) -> None:
        checks = _run(
            manifest_packs=[],
            config_packs=[],
            file_text=None,
            manifest_checksum=None,
            manifest_listed=False,
        )
        self.assertNotIn("capability_pack_enforcement", checks)

    def test_orphaned_file_without_pack_fails(self) -> None:
        text = _instruction(["agent-engram", "graphtor-docs"])
        checks = _run(
            manifest_packs=[],
            config_packs=[],
            file_text=text,
            manifest_checksum=None,
            manifest_listed=False,
        )
        self.assertFalse(checks["capability_pack_enforcement"]["ok"])
        self.assertIn(
            "orphaned", checks["capability_pack_enforcement"]["errors"][0]
        )

    def test_orphaned_manifest_entry_without_pack_fails(self) -> None:
        checks = _run(
            manifest_packs=[],
            config_packs=[],
            file_text=None,
            manifest_checksum="deadbeef",
            manifest_listed=True,
        )
        self.assertFalse(checks["capability_pack_enforcement"]["ok"])

    def test_both_enabled_valid_passes(self) -> None:
        text = _instruction(["agent-engram", "graphtor-docs"])
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram", "graphtor-docs"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        self.assertTrue(
            checks["capability_pack_enforcement"]["ok"],
            checks["capability_pack_enforcement"]["errors"],
        )

    def test_engram_only_valid_passes(self) -> None:
        text = _instruction(["agent-engram"])
        checks = _run(
            manifest_packs=["agent-engram"],
            config_packs=["agent-engram"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        self.assertTrue(
            checks["capability_pack_enforcement"]["ok"],
            checks["capability_pack_enforcement"]["errors"],
        )

    def test_engram_only_but_both_rows_fails_wrong_set(self) -> None:
        text = _instruction(["agent-engram", "graphtor-docs"])
        checks = _run(
            manifest_packs=["agent-engram"],
            config_packs=["agent-engram"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("route rows" in e for e in check["errors"]))

    def test_crlf_working_tree_matches_lf_normalized_checksum(self) -> None:
        # Regression: instruction files are text; a CRLF working tree (Windows
        # autocrlf) must not be misreported as tampering when the manifest
        # records the LF-normalized content checksum. Both EOL styles pass.
        text = _instruction(["agent-engram", "graphtor-docs"])
        lf_checksum = _sha256(text)  # _sha256 hashes the LF form
        for crlf in (False, True):
            checks = _run(
                manifest_packs=["agent-engram", "graphtor-docs"],
                config_packs=["agent-engram", "graphtor-docs"],
                file_text=text,
                manifest_checksum=lf_checksum,
                manifest_listed=True,
                crlf=crlf,
            )
            self.assertTrue(
                checks["capability_pack_enforcement"]["ok"],
                f"crlf={crlf}: {checks['capability_pack_enforcement']['errors']}",
            )

    def test_missing_file_fails(self) -> None:
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram", "graphtor-docs"],
            file_text=None,
            manifest_checksum="x",
            manifest_listed=True,
        )
        self.assertFalse(checks["capability_pack_enforcement"]["ok"])

    def test_missing_manifest_entry_fails(self) -> None:
        text = _instruction(["agent-engram", "graphtor-docs"])
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram", "graphtor-docs"],
            file_text=text,
            manifest_checksum=None,
            manifest_listed=False,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("manifest artifacts" in e for e in check["errors"]))

    def test_missing_checksum_fails(self) -> None:
        text = _instruction(["agent-engram", "graphtor-docs"])
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram", "graphtor-docs"],
            file_text=text,
            manifest_checksum=None,
            manifest_listed=True,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("checksum" in e for e in check["errors"]))

    def test_checksum_mismatch_fails(self) -> None:
        text = _instruction(["agent-engram", "graphtor-docs"])
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram", "graphtor-docs"],
            file_text=text,
            manifest_checksum=_sha256("tampered"),
            manifest_listed=True,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("does not match" in e for e in check["errors"]))

    def test_gutted_safeguard_marker_fails(self) -> None:
        text = _instruction(
            ["agent-engram", "graphtor-docs"],
            drop_safeguard="<!-- safeguard:internal-no-public-web -->",
        )
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram", "graphtor-docs"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("safeguard" in e for e in check["errors"]))

    def test_flipped_applyto_fails(self) -> None:
        text = _instruction(["agent-engram", "graphtor-docs"], apply_to="**/*.py")
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram", "graphtor-docs"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("applyTo" in e for e in check["errors"]))

    def test_unresolved_placeholder_fails(self) -> None:
        text = _instruction(["agent-engram", "graphtor-docs"], placeholder=True)
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram", "graphtor-docs"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("placeholder" in e for e in check["errors"]))

    def test_config_enables_but_manifest_omits_still_gated(self) -> None:
        # Divergence A (config keeps, manifest drops): manifest drops the pack,
        # config still enables it. Config is authoritative when present, so the
        # check must still require the file (fail-closed), proving the check is
        # not silently disabled by manifest omission.
        checks = _run(
            manifest_packs=[],
            config_packs=["agent-engram"],
            file_text=None,
            manifest_checksum=None,
            manifest_listed=False,
        )
        self.assertIn("capability_pack_enforcement", checks)
        self.assertFalse(checks["capability_pack_enforcement"]["ok"])

    def test_stale_manifest_does_not_mask_config_removal(self) -> None:
        # Divergence B (config drops, manifest keeps): config now enables only
        # engram, but a stale manifest + a stale two-row/two-defer coordinator
        # still list both packs. Config is authoritative, so the two-row file is
        # the WRONG set and must FAIL — a stale manifest cannot keep the check
        # "enabled" for a pack the operator disabled.
        text = _instruction(["agent-engram", "graphtor-docs"])
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("route rows" in e for e in check["errors"]))

    def test_config_authoritative_engram_only_over_stale_manifest(self) -> None:
        # Config drops graphtor; the correct single-pack coordinator (engram-only
        # route + defer) must PASS even though the manifest still lists both.
        text = _instruction(["agent-engram"])
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        self.assertTrue(
            checks["capability_pack_enforcement"]["ok"],
            checks["capability_pack_enforcement"]["errors"],
        )

    def test_config_key_absent_falls_back_to_manifest(self) -> None:
        # When config does not declare capability_packs, the manifest is the
        # fallback source of truth for the enabled set.
        text = _instruction(["agent-engram"])
        checks = _run(
            manifest_packs=["agent-engram"],
            config_packs=None,
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        self.assertTrue(
            checks["capability_pack_enforcement"]["ok"],
            checks["capability_pack_enforcement"]["errors"],
        )

    def test_deferral_set_mismatch_fails(self) -> None:
        # Route rows are correct (engram-only) but the deferral bullets still
        # reference both packs — a single-pack install would point at a
        # graphtor-docs instruction file that was never installed.
        text = _instruction(
            ["agent-engram"], defer_ids=["agent-engram", "graphtor-docs"]
        )
        checks = _run(
            manifest_packs=["agent-engram"],
            config_packs=["agent-engram"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("deferral bullets" in e for e in check["errors"]))

    def test_missing_deferral_block_fails(self) -> None:
        text = _instruction(
            ["agent-engram", "graphtor-docs"], include_defer_block=False
        )
        checks = _run(
            manifest_packs=["agent-engram", "graphtor-docs"],
            config_packs=["agent-engram", "graphtor-docs"],
            file_text=text,
            manifest_checksum=_sha256(text),
            manifest_listed=True,
        )
        check = checks["capability_pack_enforcement"]
        self.assertFalse(check["ok"])
        self.assertTrue(any("deferral block markers" in e for e in check["errors"]))

    def test_constant_matches_registry_retrieval_enforced_set(self) -> None:
        data = yaml.safe_load(_REGISTRY_DATA.read_text(encoding="utf-8"))
        marked = {
            p["id"] for p in data["packs"] if p.get("retrieval_enforced") is True
        }
        self.assertEqual(
            set(RETRIEVAL_ENFORCED_PACKS),
            marked,
            "verifier RETRIEVAL_ENFORCED_PACKS drifted from registry data",
        )


if __name__ == "__main__":
    unittest.main()
