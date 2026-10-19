"""Legacy tolerance for the removed ``agent-intercom`` capability pack (209-F U6).

Documents that still list the retired pack must never crash or block
``verify_workspace``: they degrade to a ``removed-capability-pack`` warning and a
``remove-retired-capability-pack`` migration proposal, independent of the
document's pinned schema version.
"""

from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

import yaml

from autoharness import verify_workspace as vw
from autoharness.schema_contracts import (
    REMOVED_CAPABILITY_PACKS,
    classify_schema_error,
    collect_contract_state_warnings,
    plan_schema_contract_migrations,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
RETIRED = "agent-intercom"
OVERLAY_PATH = ".github/instructions/agent-intercom.instructions.md"
KIND = "removed-capability-pack"
PROPOSAL = "remove-retired-capability-pack"
_FILES = {
    "manifest": "harness-manifest.yaml",
    "config": "config.yaml",
    "profile": "workspace-profile.yaml",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _documents(
    *,
    manifest_version: str,
    config_version: str,
    profile_version: str,
    packs: tuple[str, ...] = (RETIRED, "backlogit"),
    overlay_checksum: str | None = None,
) -> dict[str, dict]:
    """Minimal documents that list ``packs`` everywhere the pack can be recorded."""
    artifacts = []
    if overlay_checksum is not None:
        artifacts.append({"path": OVERLAY_PATH, "primitive": 4, "template": "t", "checksum": overlay_checksum})
    manifest = {
        "schema_version": manifest_version,
        "installed_at": "2026-04-24T00:00:00Z",
        "autoharness_version": "1.4.11",
        "profile_hash": "abc",
        "primitives_installed": [4],
        "capability_packs": list(packs),
        "capability_pack_overlays": [
            {"pack": pack, "overlay_targets": ["instructions"], "verification_checks": ["x"]} for pack in packs
        ],
        "artifacts": artifacts,
        "variables_used": {"PROJECT_NAME": "demo"},
    }
    config = {"schema_version": config_version, "capability_packs": list(packs)}
    profile = {
        "schema_version": profile_version,
        "generated_at": "2026-05-08T09:42:00Z",
        "workspace_path": ".",
        "languages": {"primary": "python"},
        "build": {"tool": "hatchling", "command": "pip install -e ."},
        "test": {"runner": "pytest", "command": "pytest", "directory": "tests"},
        "harness_recommendations": {
            "preset": "full",
            "capability_packs": list(packs),
            "recommendation_reasons": {
                "capability_packs": [{"item": pack, "because": "b", "signals": ["s"]} for pack in packs],
            },
        },
    }
    if RETIRED in packs:
        profile["agent_intercom"] = {"detected": True, "recommended": True}
    return {"manifest": manifest, "config": config, "profile": profile}


def _run_verify(documents: dict[str, dict], *, overlay_text: str | None = None, extra_files: dict[str, str] | None = None) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        (workspace / ".autoharness").mkdir(parents=True)
        for kind, name in _FILES.items():
            (workspace / ".autoharness" / name).write_text(yaml.safe_dump(documents[kind], sort_keys=False), encoding="utf-8")
        if overlay_text is not None:
            target = workspace / OVERLAY_PATH
            target.parent.mkdir(parents=True)
            target.write_text(overlay_text, encoding="utf-8")
        for relative, text in (extra_files or {}).items():
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        return vw.verify_workspace(workspace, _REPO_ROOT, workspace / ".autoharness" / "staging")


def _removed_warnings(report: dict, kind: str) -> list[dict]:
    name = _FILES[kind]
    return [w for w in report["warnings"] if w.get("kind") == KIND and str(w.get("path", "")).endswith(name)]


def _fields(warning: dict) -> list[str]:
    return list(warning.get("fields") or [warning.get("field")])


def _proposals(report: dict, kind: str) -> list[dict]:
    name = _FILES[kind]
    return [
        p
        for p in report["migration_proposals"]
        if p.get("proposal_id") == PROPOSAL and str(p.get("path", "")).endswith(name)
    ]


class RemovedPackMetadataTests(unittest.TestCase):
    def test_registry_is_immutable_and_names_the_retired_pack(self) -> None:
        self.assertIn(RETIRED, REMOVED_CAPABILITY_PACKS)
        with self.assertRaises(TypeError):
            REMOVED_CAPABILITY_PACKS["other"] = None  # type: ignore[index]
        self.assertEqual(REMOVED_CAPABILITY_PACKS[RETIRED].overlay_instruction_path, OVERLAY_PATH)


class FrozenVersionToleranceTests(unittest.TestCase):
    """(a) documents pinned to frozen versions that list the pack."""

    def test_frozen_documents_warn_without_blockers(self) -> None:
        report = _run_verify(_documents(manifest_version="1.0.0", config_version="1.2.0", profile_version="1.0.0"))
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["strict_schema_blockers"], [])
        for kind, expected_field in (
            ("manifest", "capability_packs.0"),
            ("config", "capability_packs.0"),
            ("profile", "harness_recommendations.capability_packs.0"),
        ):
            with self.subTest(kind=kind):
                warnings = _removed_warnings(report, kind)
                self.assertEqual(len(warnings), 1)
                self.assertIn(expected_field, _fields(warnings[0]))
                self.assertIn(RETIRED, warnings[0].get("legacy_values") or [warnings[0].get("legacy_value")])

    def test_earlier_frozen_config_versions_warn_without_blockers(self) -> None:
        for version in ("1.0.0", "1.1.0"):
            with self.subTest(version=version):
                report = _run_verify(
                    _documents(manifest_version="1.0.0", config_version=version, profile_version="1.0.0")
                )
                self.assertEqual(report["strict_schema_blockers"], [])
                self.assertEqual(len(_removed_warnings(report, "config")), 1)


class CurrentVersionToleranceTests(unittest.TestCase):
    """(b) documents claiming the current version yet listing the pack."""

    def test_current_version_documents_warn_instead_of_blocking(self) -> None:
        report = _run_verify(_documents(manifest_version="1.1.0", config_version="1.3.0", profile_version="1.1.0"))
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["strict_schema_blockers"], [])
        for kind in ("manifest", "config", "profile"):
            with self.subTest(kind=kind):
                self.assertEqual(len(_removed_warnings(report, kind)), 1)

    def test_classify_schema_error_downgrades_every_recording_site(self) -> None:
        path = Path("manifest.yaml")
        message = "is not one of ['agent-engram', 'backlogit']"
        sites = {
            "manifest": ("capability_packs.0", "capability_pack_overlays.0.pack"),
            "config": ("capability_packs.0",),
            "profile": (
                "harness_recommendations.capability_packs.0",
                "harness_recommendations.recommendation_reasons.capability_packs.1.item",
            ),
        }
        for kind, fields in sites.items():
            for field in fields:
                with self.subTest(kind=kind, field=field):
                    classification, payload = classify_schema_error(kind, path, {}, f"{field}: '{RETIRED}' {message}")
                    self.assertEqual(classification, "warning")
                    self.assertEqual(payload["kind"], KIND)
                    self.assertEqual(payload["field"], field)
                    self.assertEqual(payload["legacy_value"], RETIRED)
                    self.assertTrue(payload["message"])
                    self.assertTrue(payload["suggested_action"])

    def test_unrelated_pack_errors_stay_strict_blockers(self) -> None:
        classification, _payload = classify_schema_error(
            "config", Path("config.yaml"), {}, "capability_packs.0: 'not-a-pack' is not one of ['backlogit']"
        )
        self.assertEqual(classification, "strict_schema_blocker")

    def test_reason_entry_for_legacy_circuit_breaker_pack_still_warns(self) -> None:
        classification, payload = classify_schema_error(
            "profile",
            Path("profile.yaml"),
            {},
            "harness_recommendations.recommendation_reasons.capability_packs.0.item: 'circuit-breaker' is not one of ['backlogit']",
        )
        self.assertEqual(classification, "warning")
        self.assertEqual(payload["kind"], "legacy-profile-capability-pack")


class ProfileBlockAndOverlayRecordTests(unittest.TestCase):
    """(c) the open profile root yields no schema error; detection is by key presence."""

    def test_profile_block_is_detected_by_key_presence(self) -> None:
        docs = _documents(manifest_version="1.1.0", config_version="1.3.0", profile_version="1.1.0")
        warnings = collect_contract_state_warnings("profile", Path("workspace-profile.yaml"), docs["profile"])
        self.assertIn("agent_intercom", [w["field"] for w in warnings if w["kind"] == KIND])

    def test_overlay_record_and_reason_entry_are_detected(self) -> None:
        docs = _documents(manifest_version="1.0.0", config_version="1.2.0", profile_version="1.0.0")
        manifest_fields = [
            w["field"] for w in collect_contract_state_warnings("manifest", Path("m.yaml"), docs["manifest"])
        ]
        self.assertIn("capability_pack_overlays.0.pack", manifest_fields)
        profile_fields = [
            w["field"] for w in collect_contract_state_warnings("profile", Path("p.yaml"), docs["profile"])
        ]
        self.assertIn("harness_recommendations.recommendation_reasons.capability_packs.0.item", profile_fields)

    def test_verify_tolerates_the_profile_block_and_overlay_record(self) -> None:
        report = _run_verify(_documents(manifest_version="1.1.0", config_version="1.3.0", profile_version="1.1.0"))
        profile_fields = _fields(_removed_warnings(report, "profile")[0])
        self.assertIn("agent_intercom", profile_fields)
        manifest_fields = _fields(_removed_warnings(report, "manifest")[0])
        self.assertIn("capability_pack_overlays.0.pack", manifest_fields)
        self.assertEqual(report["strict_schema_blockers"], [])

    def test_documents_without_the_pack_are_silent(self) -> None:
        docs = _documents(
            manifest_version="1.1.0", config_version="1.3.0", profile_version="1.1.0", packs=("backlogit",)
        )
        for kind, name in _FILES.items():
            self.assertEqual(collect_contract_state_warnings(kind, Path(name), docs[kind]), [])

    def test_collector_ignores_non_mapping_and_malformed_documents(self) -> None:
        for kind in _FILES:
            for data in (None, [], "text", {"capability_packs": "agent-intercom"}, {"capability_packs": [None, 3]}):
                with self.subTest(kind=kind, data=data):
                    collect_contract_state_warnings(kind, Path("x.yaml"), data)


class DedupeTests(unittest.TestCase):
    """Warnings dedupe by (path, field, value) across collector and schema-error paths."""

    def test_current_version_listing_yields_one_warning_per_site(self) -> None:
        docs = _documents(
            manifest_version="1.1.0", config_version="1.3.0", profile_version="1.1.0", packs=(RETIRED,)
        )
        report = _run_verify(docs)
        raw = report["warning_instances"]
        removed = sum(w.get("occurrence_count", 1) for w in report["warnings"] if w.get("kind") == KIND)
        # manifest: 2 sites, config: 1, profile: 3 (list, reason, block)
        self.assertEqual(removed, 6)
        self.assertGreaterEqual(raw, removed)

    def test_collector_does_not_repeat_a_site(self) -> None:
        docs = _documents(manifest_version="1.0.0", config_version="1.2.0", profile_version="1.0.0")
        for kind in _FILES:
            sites = [
                (w["path"], w["field"], w["legacy_value"])
                for w in collect_contract_state_warnings(kind, Path("x.yaml"), docs[kind])
            ]
            self.assertEqual(len(sites), len(set(sites)))


class MigrationProposalTests(unittest.TestCase):
    """(d) the remove-retired-capability-pack proposal and its manual-review rule."""

    _OVERLAY = "# overlay as installed\n"

    def test_proposal_present_per_contract_kind(self) -> None:
        report = _run_verify(_documents(manifest_version="1.0.0", config_version="1.2.0", profile_version="1.0.0"))
        for kind in _FILES:
            with self.subTest(kind=kind):
                proposals = _proposals(report, kind)
                self.assertEqual(len(proposals), 1)
                self.assertIn(RETIRED, proposals[0]["legacy_values"])
                self.assertFalse(proposals[0]["manual_review"])

    def test_matching_overlay_checksum_is_not_manual_review(self) -> None:
        docs = _documents(
            manifest_version="1.0.0",
            config_version="1.2.0",
            profile_version="1.0.0",
            overlay_checksum=_sha(self._OVERLAY.encode()),
        )
        report = _run_verify(docs, overlay_text=self._OVERLAY)
        for kind in _FILES:
            with self.subTest(kind=kind):
                self.assertFalse(_proposals(report, kind)[0]["manual_review"])

    def test_crlf_checkout_of_an_unmodified_overlay_is_not_manual_review(self) -> None:
        docs = _documents(
            manifest_version="1.0.0",
            config_version="1.2.0",
            profile_version="1.0.0",
            overlay_checksum=_sha(self._OVERLAY.encode()),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / ".autoharness" / "harness-manifest.yaml"
            path.parent.mkdir()
            path.write_text(yaml.safe_dump(docs["manifest"], sort_keys=False), encoding="utf-8")
            overlay = Path(temp_dir) / OVERLAY_PATH
            overlay.parent.mkdir(parents=True)
            overlay.write_bytes(self._OVERLAY.replace("\n", "\r\n").encode())
            findings = collect_contract_state_warnings("manifest", path, docs["manifest"])
            proposals = plan_schema_contract_migrations("manifest", path, docs["manifest"], findings)
        self.assertFalse([p for p in proposals if p["proposal_id"] == PROPOSAL][0]["manual_review"])

    def test_modified_overlay_requires_manual_review(self) -> None:
        docs = _documents(
            manifest_version="1.0.0",
            config_version="1.2.0",
            profile_version="1.0.0",
            overlay_checksum=_sha(self._OVERLAY.encode()),
        )
        report = _run_verify(docs, overlay_text=self._OVERLAY + "operator edit\n")
        for kind in _FILES:
            with self.subTest(kind=kind):
                proposal = _proposals(report, kind)[0]
                self.assertTrue(proposal["manual_review"])
                self.assertEqual(report["blockers"], [])

    def test_untracked_overlay_requires_manual_review(self) -> None:
        docs = _documents(manifest_version="1.0.0", config_version="1.2.0", profile_version="1.0.0")
        report = _run_verify(docs, overlay_text=self._OVERLAY)
        self.assertTrue(_proposals(report, "manifest")[0]["manual_review"])

    def test_no_proposal_for_documents_without_the_pack(self) -> None:
        docs = _documents(
            manifest_version="1.1.0", config_version="1.3.0", profile_version="1.1.0", packs=("backlogit",)
        )
        report = _run_verify(docs)
        for kind in _FILES:
            self.assertEqual(_proposals(report, kind), [])
            self.assertEqual(_removed_warnings(report, kind), [])


class MixedPackTests(unittest.TestCase):
    """(e) legacy and supported packs together: supported packs are still verified."""

    def test_supported_pack_is_verified_next_to_the_retired_one(self) -> None:
        docs = _documents(
            manifest_version="1.0.0",
            config_version="1.2.0",
            profile_version="1.0.0",
            packs=(RETIRED, "strict-safety"),
        )
        report = _run_verify(docs)
        checks = report["targeted_checks"]
        self.assertNotIn(RETIRED, vw.SUPPORTED_CAPABILITY_PACKS)
        self.assertNotIn(RETIRED, vw.PACK_ASSERTIONS)
        self.assertIn("strict_safety_instruction", checks)
        self.assertNotIn("agent_intercom_instruction", checks)
        self.assertNotIn("review_intercom_workflow", checks)
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["strict_schema_blockers"], [])
        self.assertEqual(len(_removed_warnings(report, "manifest")), 1)


LEGACY_OVERLAY_TEMPLATE = "templates/instructions/agent-intercom.instructions.md.tmpl"


class LegacyOverlayArtifactRecordTests(unittest.TestCase):
    """A legacy manifest's overlay artifact record degrades to a warning, never a blocker."""

    _OVERLAY = "# overlay as installed\n"

    def _docs(self) -> dict[str, dict]:
        docs = _documents(
            manifest_version="1.0.0",
            config_version="1.2.0",
            profile_version="1.0.0",
            overlay_checksum=_sha(self._OVERLAY.encode()),
        )
        docs["manifest"]["artifacts"][0]["template"] = LEGACY_OVERLAY_TEMPLATE
        return docs

    def _assert_tolerated(self, report: dict) -> None:
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["strict_schema_blockers"], [])
        self.assertTrue(_removed_warnings(report, "manifest"))
        self.assertEqual(len(_removed_warnings(report, "manifest")), 1)

    def test_template_is_really_absent_from_autoharness_home(self) -> None:
        self.assertFalse((_REPO_ROOT / LEGACY_OVERLAY_TEMPLATE).exists())

    def test_record_with_installed_overlay_yields_warning_not_blocker(self) -> None:
        report = _run_verify(self._docs(), overlay_text=self._OVERLAY)
        self._assert_tolerated(report)

    def test_record_without_installed_overlay_yields_warning_not_blocker(self) -> None:
        report = _run_verify(self._docs())
        self._assert_tolerated(report)

    def test_record_matched_by_template_alone(self) -> None:
        docs = self._docs()
        docs["manifest"]["artifacts"][0]["path"] = "somewhere/else.md"
        report = _run_verify(docs)
        self.assertEqual(report["blockers"], [])

    def test_unrelated_missing_template_still_blocks(self) -> None:
        docs = self._docs()
        docs["manifest"]["artifacts"][0]["path"] = ".github/instructions/other.instructions.md"
        docs["manifest"]["artifacts"][0]["template"] = "templates/instructions/other-missing.instructions.md.tmpl"
        report = _run_verify(docs)
        self.assertTrue([b for b in report["blockers"] if b.get("kind") == "missing-template-source"])


class RetiredOverlayLookupNeverRaisesTests(unittest.TestCase):
    """The overlay checksum lookup tolerates mangled manifests and symlinked overlays."""

    _OVERLAY = "# overlay as installed\n"

    def _plan(self, kind: str, manifest_bytes: bytes | None, manifest_doc: dict | None, *, symlink: bool = False) -> list[dict]:
        docs = _documents(manifest_version="1.0.0", config_version="1.2.0", profile_version="1.0.0")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".autoharness").mkdir()
            overlay = root / OVERLAY_PATH
            overlay.parent.mkdir(parents=True)
            if symlink:
                target = root / "real-overlay.md"
                target.write_text(self._OVERLAY, encoding="utf-8")
                try:
                    overlay.symlink_to(target)
                except (OSError, NotImplementedError):
                    self.skipTest("symlinks unavailable")
            else:
                overlay.write_text(self._OVERLAY, encoding="utf-8")
            manifest_path = root / ".autoharness" / "harness-manifest.yaml"
            if manifest_bytes is not None:
                manifest_path.write_bytes(manifest_bytes)
            data = docs[kind]
            if manifest_doc is not None:
                data = manifest_doc
            path = root / ".autoharness" / _FILES[kind]
            findings = collect_contract_state_warnings(kind, path, data)
            return plan_schema_contract_migrations(kind, path, data, findings)

    def test_invalid_utf8_sibling_manifest_does_not_raise(self) -> None:
        proposals = self._plan("config", b"\xff\xfe\x00bad: [", None)
        self.assertTrue([p for p in proposals if p["proposal_id"] == PROPOSAL][0]["manual_review"])

    def test_non_list_artifacts_does_not_raise(self) -> None:
        for artifacts in (5, "text", {"path": OVERLAY_PATH}):
            with self.subTest(artifacts=artifacts):
                manifest = _documents(manifest_version="1.0.0", config_version="1.2.0", profile_version="1.0.0")["manifest"]
                manifest["artifacts"] = artifacts
                proposals = self._plan("manifest", None, manifest)
                self.assertTrue([p for p in proposals if p["proposal_id"] == PROPOSAL][0]["manual_review"])

    def test_symlinked_overlay_requires_manual_review(self) -> None:
        manifest = _documents(
            manifest_version="1.0.0",
            config_version="1.2.0",
            profile_version="1.0.0",
            overlay_checksum=_sha(self._OVERLAY.encode()),
        )["manifest"]
        proposals = self._plan("manifest", None, manifest, symlink=True)
        self.assertTrue([p for p in proposals if p["proposal_id"] == PROPOSAL][0]["manual_review"])


class NeverRaisesTests(unittest.TestCase):
    def test_verify_never_raises_on_legacy_documents(self) -> None:
        base = _documents(manifest_version="1.0.0", config_version="1.2.0", profile_version="1.0.0")
        mangled = copy.deepcopy(base)
        mangled["manifest"]["capability_pack_overlays"] = [None, "text", {"pack": 5}]
        mangled["profile"]["harness_recommendations"]["recommendation_reasons"] = {"capability_packs": [None, "x"]}
        mangled["config"]["capability_packs"] = [RETIRED, None, 7, {"a": 1}]
        for name, docs in (("legacy", base), ("mangled", mangled)):
            with self.subTest(name=name):
                report = _run_verify(docs)
                self.assertIsInstance(report["warnings"], list)


if __name__ == "__main__":
    unittest.main()
