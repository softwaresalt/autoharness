"""Focused tests for the verify-workspace engine."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from autoharness.schema_contracts import (
    classify_schema_error,
    plan_schema_contract_migrations,
    resolve_contract_schema_path,
    summarize_schema_contract,
)
from autoharness.verify_workspace import _derive_template_variables, _find_unresolved_placeholders, verify_workspace


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class VerifyWorkspaceTests(unittest.TestCase):
    def test_branch_safety_guidance_is_woven_through_install_and_tune_workflows(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / ".github" / "agents" / "auto-mergeinstall.agent.md": [
                "Never commit or push autoharness install output directly to the default branch",
                "feature branch",
                "pull request",
                "local uncommitted changes",
            ],
            repo_root / ".github" / "agents" / "auto-tune.agent.md": [
                "Never commit or push autoharness tune output directly to the default branch",
                "feature branch",
                "pull request",
                "local uncommitted changes",
            ],
            repo_root / ".github" / "skills" / "install-harness" / "SKILL.md": [
                "Never commit or push autoharness install output directly to the default",
                "feature branch",
                "pull request",
                "local uncommitted changes",
            ],
            repo_root / ".github" / "skills" / "tune-harness" / "SKILL.md": [
                "only covers file updates",
                "Never commit or push autoharness tune output directly to the default branch",
                "feature branch",
                "pull request",
                "local uncommitted changes",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_auto_tune_learning_loop_guidance_is_woven_through_agent_and_skill(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / ".github" / "agents" / "auto-tune.agent.md": [
                "learning_signals{}",
                "compound library",
                "continuous-learning observations/instincts",
                "closure artifacts",
            ],
            repo_root / ".github" / "skills" / "tune-harness" / "SKILL.md": [
                "learning_signals{}",
                "distribution.local_agents_dir",
                ".github/local-agents/",
                "produced by compound, continuous-learning, and closure systems",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_unresolved_placeholders_ignore_code_fences(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "sample.md"
            test_file.write_text(
                "Line with {{REAL_PLACEHOLDER}}\n```md\n{{IGNORED_PLACEHOLDER}}\n```\n",
                encoding="utf-8",
            )

            unresolved = _find_unresolved_placeholders(test_file)

            self.assertEqual(len(unresolved), 1)
            self.assertEqual(unresolved[0]["placeholder"], "{{REAL_PLACEHOLDER}}")

    def test_derive_template_variables_maps_suffix_and_registry_ops(self) -> None:
        workspace_path = Path("demo")
        manifest = {
            "variables_used": {
                "PREFIX_DELIBERATION": "DL",
            },
            "capability_packs": ["backlogit"],
        }
        config = {
            "backlog": {
                "suffix_map": {
                    "feature": "F",
                    "task": "T",
                }
            },
            "docs": {
                "root": "docs",
                "subdirectories": {
                    "plans": "exec-plans",
                },
            },
        }
        profile = {
            "languages": {"primary": "Python", "version": "3.12"},
            "build": {"command": "python -m build"},
        }
        registry = {
            "tool_name": "backlogit",
            "directory": ".backlogit",
            "tool_type": "both",
            "operations": {
                "create_task": {"mcp_tool": "backlogit_create_item"},
                "create_checkpoint": {"mcp_tool": "backlogit_create_checkpoint"},
            },
            "status_values": {"todo": "queued", "in_progress": "active", "done": "done", "blocked": "blocked"},
            "field_mapping": {"task_id": "id", "artifact_type": "artifact_type"},
            "features": {"shipments": True},
        }

        variables = _derive_template_variables(workspace_path, manifest, config, profile, registry)

        self.assertEqual(variables["SUFFIX_DELIBERATION"], "DL")
        self.assertEqual(variables["DOCS_PLANS"], "docs/exec-plans")
        self.assertEqual(variables["OP_CREATE_MCP"], "backlogit_create_item")
        self.assertEqual(variables["OP_CREATE_CHECKPOINT_MCP"], "backlogit_create_checkpoint")
        self.assertEqual(variables["STATUS_QUEUED"], "queued")
        self.assertEqual(variables["FIELD_TYPE"], "artifact_type")
        self.assertEqual(variables["FEATURE_SHIPMENTS"], "true")

    def test_classify_schema_error_downgrades_known_legacy_values(self) -> None:
        classification, payload = classify_schema_error(
            "manifest",
            Path("manifest.yaml"),
            {"schema_version": "1.0.0"},
            "capability_packs.5: 'circuit-breaker' is not one of ['agent-intercom']",
        )
        self.assertEqual(classification, "warning")
        self.assertEqual(payload["kind"], "legacy-manifest-capability-pack")

        classification, payload = classify_schema_error(
            "profile",
            Path("workspace-profile.yaml"),
            {"schema_version": "1.0.0"},
            "drift_report.changes.0.category: 'interrupted_tuning' is not one of ['breaking']",
        )
        self.assertEqual(classification, "warning")
        self.assertEqual(payload["kind"], "legacy-profile-drift-category")

        classification, payload = classify_schema_error(
            "config",
            Path("config.yaml"),
            {},
            "<root>: 'schema_version' is a required property",
        )
        self.assertEqual(classification, "warning")
        self.assertEqual(payload["kind"], "missing-config-schema-version")

        classification, payload = classify_schema_error(
            "profile",
            Path("workspace-profile.yaml"),
            {"schema_version": "1.0.0"},
            "languages.primary: 'Go' is not of type 'object'",
        )
        self.assertEqual(classification, "strict_schema_blocker")
        self.assertEqual(payload["kind"], "invalid-profile-schema")

    def test_summarize_schema_contract_reports_current_version(self) -> None:
        summary = summarize_schema_contract(
            "manifest",
            Path("harness-manifest.yaml"),
            {"schema_version": "1.0.0"},
        )

        self.assertEqual(summary["contract_name"], "harness-manifest")
        self.assertEqual(summary["status"], "current")
        self.assertEqual(summary["observed_version"], "1.0.0")

    def test_summarize_schema_contract_reports_known_legacy_version(self) -> None:
        summary = summarize_schema_contract(
            "config",
            Path("config.yaml"),
            {"schema_version": "0.9.0"},
        )

        self.assertEqual(summary["contract_name"], "harness-config")
        self.assertEqual(summary["status"], "known-legacy")
        self.assertEqual(summary["observed_version"], "0.9.0")

    def test_resolve_contract_schema_path_prefers_versioned_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            autoharness_home = Path(temp_dir)
            versioned_schema = autoharness_home / "schemas" / "harness-manifest" / "1.0.0.schema.json"
            versioned_schema.parent.mkdir(parents=True, exist_ok=True)
            versioned_schema.write_text("{}\n", encoding="utf-8")
            (autoharness_home / "schemas" / "harness-manifest.schema.json").write_text(
                "{\"type\": \"object\"}\n",
                encoding="utf-8",
            )

            resolved = resolve_contract_schema_path(
                "manifest",
                autoharness_home,
                {"schema_version": "1.0.0"},
            )

            self.assertEqual(resolved, versioned_schema)

    def test_resolve_contract_schema_path_uses_legacy_versioned_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            autoharness_home = Path(temp_dir)
            versioned_schema = autoharness_home / "schemas" / "harness-config" / "0.9.0.schema.json"
            versioned_schema.parent.mkdir(parents=True, exist_ok=True)
            versioned_schema.write_text("{}\n", encoding="utf-8")
            (autoharness_home / "schemas" / "harness-config.schema.json").write_text(
                "{\"type\": \"object\"}\n",
                encoding="utf-8",
            )

            resolved = resolve_contract_schema_path(
                "config",
                autoharness_home,
                {"schema_version": "0.9.0"},
            )

            self.assertEqual(resolved, versioned_schema)

    def test_plan_schema_contract_migrations_for_legacy_config(self) -> None:
        config = {
            "backlog": {
                "prefix_map": {
                    "feature": "F",
                }
            }
        }

        proposals = plan_schema_contract_migrations(
            "config",
            Path("config.yaml"),
            config,
            [
                {
                    "kind": "missing-config-schema-version",
                    "path": "config.yaml",
                },
                {
                    "kind": "legacy-config-key",
                    "path": "config.yaml",
                    "field": "backlog.prefix_map",
                    "legacy_value": "backlog.prefix_map",
                },
            ],
        )

        proposal_ids = {proposal["proposal_id"] for proposal in proposals}
        self.assertIn("backfill-config-schema-version", proposal_ids)
        self.assertIn("rename-config-prefix-map", proposal_ids)

    def test_plan_schema_contract_migrations_for_known_legacy_contract(self) -> None:
        proposals = plan_schema_contract_migrations(
            "profile",
            Path("workspace-profile.yaml"),
            {"schema_version": "0.9.0"},
            [],
        )

        proposal_ids = {proposal["proposal_id"] for proposal in proposals}
        self.assertIn("upgrade-profile-contract-0.9.0-to-1.0.0", proposal_ids)

    def test_verify_workspace_writes_reports_for_minimal_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            staging = workspace / ".autoharness" / "staging"

            (autoharness_home / "templates" / "foundation").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)

            (autoharness_home / "templates" / "foundation" / "AGENTS.md.tmpl").write_text(
                "# {{PROJECT_NAME}}\n",
                encoding="utf-8",
            )

            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-24T00:00:00Z",
                    "autoharness_version": "1.3.2",
                    "profile_hash": "abc",
                    "primitives_installed": [1],
                    "capability_packs": [],
                    "artifacts": [
                        {
                            "path": "AGENTS.md",
                            "primitive": 9,
                            "template": "templates/foundation/AGENTS.md.tmpl",
                            "checksum": "stale-checksum",
                        }
                    ],
                    "variables_used": {"PROJECT_NAME": "demo-workspace"},
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})
            (workspace / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
            (workspace / ".backlogit").mkdir(parents=True, exist_ok=True)
            (workspace / ".backlogit" / "config.yaml").write_text("artifact_types: []\n", encoding="utf-8")

            manifest_path = workspace / ".autoharness" / "harness-manifest.yaml"
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"].append(
                {
                    "path": ".backlogit/config.yaml",
                    "primitive": 2,
                    "template": "workspace merge install",
                    "checksum": "stale-config-checksum",
                }
            )
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

            report = verify_workspace(workspace, autoharness_home, staging)

            self.assertTrue((staging / "AGENTS.md").exists())
            self.assertTrue((staging / ".backlogit" / "config.yaml").exists())
            self.assertTrue((staging / "verify-workspace-report.json").exists())
            self.assertTrue((staging / "verify-workspace-report.md").exists())
            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])
            self.assertEqual(report["unresolved"], [])
            self.assertEqual(report["migration_proposals"], [])
            self.assertEqual(report["schema_contracts"]["manifest"]["status"], "current")
            self.assertEqual(report["rendered"][0]["path"], "AGENTS.md")
            self.assertTrue(
                any(
                    item["path"] == ".backlogit/config.yaml" and item["mode"] == "workspace-copied"
                    for item in report["rendered"]
                )
            )
            self.assertEqual(report["skipped"], [])

    def test_verify_workspace_reports_legacy_config_migrations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "templates" / "foundation").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)

            (autoharness_home / "templates" / "foundation" / "AGENTS.md.tmpl").write_text(
                "# {{PROJECT_NAME}}\n",
                encoding="utf-8",
            )

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "const": "1.0.0",
                    }
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-24T00:00:00Z",
                    "autoharness_version": "1.3.2",
                    "profile_hash": "abc",
                    "primitives_installed": [1],
                    "capability_packs": [],
                    "artifacts": [],
                    "variables_used": {"PROJECT_NAME": "demo-workspace"},
                },
            )
            _write_yaml(
                workspace / ".autoharness" / "config.yaml",
                {
                    "backlog": {
                        "prefix_map": {
                            "feature": "F",
                        }
                    }
                },
            )
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            proposal_ids = {proposal["proposal_id"] for proposal in report["migration_proposals"]}
            self.assertIn("backfill-config-schema-version", proposal_ids)
            self.assertIn("rename-config-prefix-map", proposal_ids)

    def test_verify_workspace_groups_repeated_contract_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)

            manifest_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                    "capability_packs": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["agent-intercom"]},
                    },
                    "capability_pack_overlays": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "pack": {"type": "string", "enum": ["agent-intercom"]}
                            },
                        },
                    },
                },
            }
            config_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            profile_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                    "drift_report": {
                        "type": "object",
                        "properties": {
                            "changes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "category": {
                                            "type": "string",
                                            "enum": ["breaking"],
                                        }
                                    },
                                },
                            }
                        },
                    },
                },
            }

            schema_map = {
                "harness-manifest": manifest_schema,
                "harness-config": config_schema,
                "workspace-profile": profile_schema,
            }
            for schema_name, schema in schema_map.items():
                (autoharness_home / "schemas" / f"{schema_name}.schema.json").write_text(
                    json.dumps(schema),
                    encoding="utf-8",
                )
                (autoharness_home / "schemas" / schema_name / "1.0.0.schema.json").write_text(
                    json.dumps(schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-24T00:00:00Z",
                    "autoharness_version": "1.3.2",
                    "profile_hash": "abc",
                    "primitives_installed": [1],
                    "capability_packs": ["circuit-breaker", "concurrency"],
                    "capability_pack_overlays": [
                        {"pack": "circuit-breaker"},
                        {"pack": "concurrency"},
                    ],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(
                workspace / ".autoharness" / "workspace-profile.yaml",
                {
                    "schema_version": "1.0.0",
                    "drift_report": {
                        "changes": [
                            {"category": "interrupted_tuning"},
                            {"category": "deleted_artifact"},
                            {"category": "deprecated_agents_removed"},
                            {"category": "existing_modified"},
                            {"category": "gitignore_updated"},
                        ]
                    },
                },
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["warning_instances"], 9)
            self.assertEqual(len(report["warnings"]), 2)

            warnings_by_kind = {warning["kind"]: warning for warning in report["warnings"]}

            manifest_warning = warnings_by_kind["legacy-manifest-capability-pack"]
            self.assertEqual(manifest_warning["occurrence_count"], 4)
            self.assertEqual(manifest_warning["legacy_values"], ["circuit-breaker", "concurrency"])
            self.assertEqual(
                manifest_warning["fields"],
                [
                    "capability_pack_overlays.0.pack",
                    "capability_pack_overlays.1.pack",
                    "capability_packs.0",
                    "capability_packs.1",
                ],
            )

            profile_warning = warnings_by_kind["legacy-profile-drift-category"]
            self.assertEqual(profile_warning["occurrence_count"], 5)
            self.assertEqual(
                profile_warning["legacy_values"],
                [
                    "interrupted_tuning",
                    "deleted_artifact",
                    "deprecated_agents_removed",
                    "existing_modified",
                    "gitignore_updated",
                ],
            )

            proposals = {proposal["proposal_id"]: proposal for proposal in report["migration_proposals"]}
            self.assertEqual(
                len(proposals["normalize-legacy-manifest-capability-packs"]["evidence"]),
                4,
            )
            self.assertEqual(
                len(proposals["normalize-legacy-profile-drift-categories"]["evidence"]),
                5,
            )

            markdown_report = (workspace / ".autoharness" / "staging" / "verify-workspace-report.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("grouped summaries: 2 (from 9 findings)", markdown_report)

    def test_verify_workspace_checks_backlogit_overlay_docs_and_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "instructions").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "agents").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "operational-closure").mkdir(parents=True, exist_ok=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-25T00:00:00Z",
                    "autoharness_version": "1.3.2",
                    "profile_hash": "abc",
                    "primitives_installed": [4, 9, 10],
                    "capability_packs": ["backlogit"],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / "AGENTS.md").write_text(
                "backlogit_get_metadata_catalog\nbacklogit_export_command_map\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "instructions" / "backlogit.instructions.md").write_text(
                "checkpoint\nqueue\ntraceability\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "instructions" / "backlogit-sql-schema.instructions.md").write_text(
                "backlogit_query_sql\nstash_entries\nSELECT\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "instructions" / "backlogit-yaml-header-tooling.instructions.md").write_text(
                "custom_fields\nreferences\nbacklogit_update_item\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "agents" / "ship.agent.md").write_text(
                "source_stash_id\nsource_deliberation_id\nbacklogit_stash_remove\nbacklogit_archive_item\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "operational-closure" / "SKILL.md").write_text(
                "Source artifact cleanup\nsource_stash_id\nsource_deliberation_id\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["backlogit_instruction_guidance"]["ok"])
            self.assertTrue(targeted_checks["backlogit_sql_schema_instruction"]["ok"])
            self.assertTrue(targeted_checks["backlogit_yaml_header_instruction"]["ok"])
            self.assertTrue(targeted_checks["agents_metadata_catalog_guidance"]["ok"])
            self.assertTrue(targeted_checks["ship_source_artifact_cleanup"]["ok"])
            self.assertTrue(targeted_checks["closure_source_artifact_cleanup"]["ok"])

    def test_verify_workspace_checks_review_intercom_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "instructions").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "review").mkdir(parents=True, exist_ok=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-25T00:00:00Z",
                    "autoharness_version": "1.3.2",
                    "profile_hash": "abc",
                    "primitives_installed": [4, 6, 7],
                    "capability_packs": ["agent-intercom"],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "instructions" / "agent-intercom.instructions.md").write_text(
                "broadcast\napproval\nstandby\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "review" / "SKILL.md").write_text(
                "## Agent-Intercom Communication (NON-NEGOTIABLE)\n"
                "Review written\n"
                "Waiting for input\n"
                "## Subagent Depth Constraint\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["agent_intercom_instruction"]["ok"])
            self.assertTrue(targeted_checks["review_intercom_workflow"]["ok"])
            self.assertEqual(targeted_checks["review_intercom_workflow"]["order_violations"], [])

    def test_verify_workspace_checks_foundation_copilot_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github").mkdir(parents=True, exist_ok=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-25T00:00:00Z",
                    "autoharness_version": "1.3.2",
                    "profile_hash": "abc",
                    "primitives_installed": [1, 6, 9],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "copilot-instructions.md").write_text(
                "## Durable Knowledge Layout\n"
                "Reusable learnings and hard-won fixes\n"
                "Session memory and checkpoints\n"
                "Graduated architecture and design rationale\n"
                "## Session Memory Requirements\n"
                "65%\n"
                "phase or major task group\n"
                "## Remote Operator Integration\n"
                "### agent-intercom\n"
                "ping-loop.prompt.md\n"
                "### agent-engram\n"
                "sync_workspace\n"
                "## Backlog Workflow Expectations\n"
                "queue-aware and dependency-aware operations\n"
                "commit-tracking\n"
                "parallel markdown trackers\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["copilot_durable_knowledge_layout"]["ok"])
            self.assertTrue(targeted_checks["copilot_session_memory_guidance"]["ok"])
            self.assertTrue(targeted_checks["copilot_remote_operator_guidance"]["ok"])
            self.assertTrue(targeted_checks["copilot_backlog_workflow_expectations"]["ok"])

    def test_verify_workspace_checks_auto_tune_learning_loop_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "agents").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "tune-harness").mkdir(parents=True, exist_ok=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-26T00:00:00Z",
                    "autoharness_version": "1.3.3",
                    "profile_hash": "abc",
                    "primitives_installed": [1, 4],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "agents" / "auto-tune.agent.md").write_text(
                "Step 1.8\ncompound library\ncontinuous-learning\nclosure artifacts\nlearning_signals\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "tune-harness" / "SKILL.md").write_text(
                "#### Step 1.8: Mine Learning Signals for Improvement Proposals\n"
                "produced by compound, continuous-learning, and closure systems\n"
                "learning_signals{}\n"
                "Learning-driven proposals\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["auto_tune_learning_loop_contract"]["ok"])
            self.assertTrue(targeted_checks["tune_harness_learning_loop_contract"]["ok"])

    def test_verify_workspace_reports_learning_signals_from_compound_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / "docs" / "compound").mkdir(parents=True, exist_ok=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-26T00:00:00Z",
                    "autoharness_version": "1.3.3",
                    "profile_hash": "abc",
                    "primitives_installed": [1],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            compound_entry = (
                "---\n"
                "root_cause: stale-cache\n"
                "category: build-errors\n"
                "component: auto-tune\n"
                "severity: high\n"
                "tags:\n"
                "  - cache\n"
                "  - tuning\n"
                "---\n"
                "Recurring stale-cache issue.\n"
            )
            for index in range(1, 4):
                (workspace / "docs" / "compound" / f"stale-cache-{index}.md").write_text(
                    compound_entry,
                    encoding="utf-8",
                )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            compound_patterns = report["learning_signals"]["compound_patterns"]
            recurring_root_cause = next(
                pattern for pattern in compound_patterns if pattern["pattern_type"] == "recurring_root_cause"
            )
            self.assertEqual(recurring_root_cause["key"], "stale-cache")
            self.assertEqual(recurring_root_cause["evidence_count"], 3)
            self.assertEqual(
                recurring_root_cause["evidence_refs"],
                [
                    "docs/compound/stale-cache-1.md",
                    "docs/compound/stale-cache-2.md",
                    "docs/compound/stale-cache-3.md",
                ],
            )

    def test_verify_workspace_reports_learning_signals_from_continuous_learning_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness" / "continuous-learning" / "observations").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness" / "continuous-learning" / "instincts").mkdir(parents=True, exist_ok=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-26T00:00:00Z",
                    "autoharness_version": "1.3.3",
                    "profile_hash": "abc",
                    "primitives_installed": [1],
                    "capability_packs": ["continuous-learning"],
                    "artifacts": [],
                },
            )
            _write_yaml(
                workspace / ".autoharness" / "config.yaml",
                {
                    "schema_version": "1.0.0",
                    "continuous_learning": {
                        "directory": ".autoharness/continuous-learning",
                        "promotion_threshold": 3,
                    },
                },
            )
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            for index in range(1, 3):
                _write_yaml(
                    workspace / ".autoharness" / "continuous-learning" / "observations" / f"build-{index}.yaml",
                    {
                        "affected_workflow_phase": "build",
                    },
                )

            (workspace / ".autoharness" / "continuous-learning" / "instincts" / "cache-invalidation.md").write_text(
                "---\n"
                "observation_count: 4\n"
                "suggested_target: instruction\n"
                "---\n"
                "Promote this instinct.\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            promotion_candidates = report["learning_signals"]["promotion_candidates"]
            self.assertEqual(len(promotion_candidates), 1)
            self.assertEqual(
                promotion_candidates[0]["instinct_path"],
                ".autoharness/continuous-learning/instincts/cache-invalidation.md",
            )
            self.assertEqual(promotion_candidates[0]["observation_count"], 4)

            observation_patterns = report["learning_signals"]["observation_patterns"]
            self.assertEqual(len(observation_patterns), 1)
            self.assertEqual(observation_patterns[0]["phase"], "build")
            self.assertEqual(observation_patterns[0]["observation_count"], 2)

    def test_verify_workspace_reports_promotion_candidates_without_observations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness" / "continuous-learning" / "instincts").mkdir(parents=True, exist_ok=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-26T00:00:00Z",
                    "autoharness_version": "1.3.3",
                    "profile_hash": "abc",
                    "primitives_installed": [1],
                    "capability_packs": ["continuous-learning"],
                    "artifacts": [],
                },
            )
            _write_yaml(
                workspace / ".autoharness" / "config.yaml",
                {
                    "schema_version": "1.0.0",
                    "continuous_learning": {
                        "directory": ".autoharness/continuous-learning",
                        "promotion_threshold": 3,
                    },
                },
            )
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".autoharness" / "continuous-learning" / "instincts" / "cache-invalidation.md").write_text(
                "---\n"
                "observation_count: 4\n"
                "suggested_target: instruction\n"
                "---\n"
                "Promote this instinct.\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            promotion_candidates = report["learning_signals"]["promotion_candidates"]
            self.assertEqual(len(promotion_candidates), 1)
            self.assertEqual(
                promotion_candidates[0]["instinct_path"],
                ".autoharness/continuous-learning/instincts/cache-invalidation.md",
            )
            self.assertEqual(promotion_candidates[0]["observation_count"], 4)
            self.assertEqual(report["learning_signals"]["observation_patterns"], [])

    def test_verify_workspace_reports_learning_signals_from_closure_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / "docs" / "closure").mkdir(parents=True, exist_ok=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-26T00:00:00Z",
                    "autoharness_version": "1.3.3",
                    "profile_hash": "abc",
                    "primitives_installed": [10],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            closure_entry = (
                "---\n"
                "generated_at: 2026-04-0{index}T00:00:00Z\n"
                "closure_findings:\n"
                "  - database-migration-rollback\n"
                "---\n"
                "Recurring rollback trigger.\n"
            )
            for index in range(1, 3):
                (workspace / "docs" / "closure" / f"closure-{index}.md").write_text(
                    closure_entry.format(index=index),
                    encoding="utf-8",
                )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            closure_patterns = report["learning_signals"]["closure_patterns"]
            self.assertEqual(len(closure_patterns), 1)
            self.assertEqual(closure_patterns[0]["pattern_type"], "recurring_closure_finding")
            self.assertEqual(closure_patterns[0]["key"], "database-migration-rollback")
            self.assertEqual(closure_patterns[0]["occurrences"], 2)

    def test_verify_workspace_skips_checksum_comparison_when_manifest_checksum_is_blank(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (autoharness_home / "schemas" / schema_name).write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema),
                    encoding="utf-8",
                )

            (workspace / "AGENTS.md").write_text("tracked file\n", encoding="utf-8")

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-26T00:00:00Z",
                    "autoharness_version": "1.3.3",
                    "profile_hash": "abc",
                    "primitives_installed": [9],
                    "capability_packs": [],
                    "artifacts": [
                        {
                            "path": "AGENTS.md",
                            "primitive": 9,
                            "template": "workspace merge install",
                            "checksum": "",
                        }
                    ],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            checksum_entry = report["checksum_scan"][0]
            self.assertEqual(checksum_entry["path"], "AGENTS.md")
            self.assertEqual(checksum_entry["status"], "checksum-untracked")
            self.assertEqual(checksum_entry["reason"], "manifest checksum missing")
            self.assertIn(
                {
                    "kind": "manifest-checksum-missing",
                    "path": "AGENTS.md",
                    "message": "Manifest-listed artifact has no checksum; drift scan skipped checksum comparison for this path.",
                },
                report["warnings"],
            )


if __name__ == "__main__":
    unittest.main()
