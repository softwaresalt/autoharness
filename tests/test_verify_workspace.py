"""Focused tests for the verify-workspace engine."""

from __future__ import annotations

import json
import hashlib
import re
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
from autoharness.cli import _report_has_failures
from autoharness.verify_workspace import _derive_template_variables, _find_unresolved_placeholders, _normalize_stage_path, _resolve_agent_scan_dirs, _run_portability_scan, _scan_agent_identity_migrations, _scan_uninstalled_templates, verify_workspace, FOUNDATION_ASSERTIONS, _add_text_check


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _extract_quoted_value(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise AssertionError(f"Unable to find pattern: {pattern}")
    return match.group(1)


class VerifyWorkspaceTests(unittest.TestCase):
    def test_distribution_and_plugin_versions_stay_in_sync(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
        init_text = (repo_root / "src" / "autoharness" / "__init__.py").read_text(encoding="utf-8")
        plugin_manifest = json.loads((repo_root / "plugin.json").read_text(encoding="utf-8"))
        marketplace_manifest = json.loads(
            (repo_root / ".github" / "plugin" / "marketplace.json").read_text(encoding="utf-8")
        )

        expected_version = _extract_quoted_value(pyproject_text, r'^version = "([^"]+)"$')
        fallback_version = _extract_quoted_value(init_text, r'^    __version__ = "([^"]+)"')

        self.assertEqual(fallback_version, expected_version)
        self.assertEqual(plugin_manifest["version"], expected_version)
        self.assertEqual(marketplace_manifest["metadata"]["version"], expected_version)
        self.assertEqual(len(marketplace_manifest["plugins"]), 1)
        self.assertEqual(marketplace_manifest["plugins"][0]["version"], expected_version)

    def test_release_workflow_publishes_to_pypi(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        release_workflow = (repo_root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

        self.assertIn("id-token: write", release_workflow)
        self.assertIn("astral-sh/setup-uv@", release_workflow)
        self.assertIn("uvx twine check dist/*", release_workflow)
        self.assertIn("gh-action-pypi-publish@", release_workflow)
        self.assertIn("skip-existing: true", release_workflow)
        self.assertIn('uv tool run --isolated --no-config --from "autoharness==${version}" autoharness version', release_workflow)
        self.assertIn('echo "version=${version}" >> "$GITHUB_OUTPUT"', release_workflow)
        self.assertLess(
            release_workflow.index("Extract changelog for this version"),
            release_workflow.index("Publish distribution to PyPI"),
        )
        self.assertLess(
            release_workflow.index("Publish distribution to PyPI"),
            release_workflow.index("Smoke test published package from PyPI"),
        )
        self.assertLess(
            release_workflow.index("Smoke test published package from PyPI"),
            release_workflow.index("Create or update GitHub Release"),
        )

    def test_user_facing_python_cli_docs_prefer_pip_install(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / "README.md": [
                "pip install autoharness",
                "pip install --upgrade autoharness",
            ],
            repo_root / "docs" / "getting-started.md": [
                "pip install autoharness",
                "pip install --upgrade autoharness",
            ],
            repo_root / "docs" / "reference-library.md": [
                "pip install autoharness",
            ],
            repo_root / ".github" / "agents" / "auto-mergeinstall.agent.md": [
                "pip install autoharness",
            ],
            repo_root / ".github" / "agents" / "auto-tune.agent.md": [
                "pip install autoharness",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_cli_help_mentions_python_cli_install_and_github_snapshots(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / "src" / "autoharness" / "cli.py": [
                "pip install autoharness",
                "pip install --upgrade autoharness",
                "unreleased snapshots from GitHub",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_mcp_config_guidance_allows_local_root_config(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        root_mcp = repo_root / ".mcp.json"
        gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")

        copilot_instructions = (repo_root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")

        self.assertIn(".vscode/mcp.json", gitignore)
        self.assertIn(".cursor/mcp.json", gitignore)
        self.assertIn(".claude/mcp.json", gitignore)

        if root_mcp.exists():
            root_mcp_text = root_mcp.read_text(encoding="utf-8")
            self.assertIn('"command": "engram"', root_mcp_text)
            self.assertIn('"graphtor-docs"', root_mcp_text)

        self.assertIn("workspace-root `.mcp.json`", copilot_instructions)

    def test_reference_library_submodules_are_registered(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        gitmodules_path = repo_root / ".gitmodules"

        # .gitmodules must exist — submodules are kept as in-repo developer references
        self.assertTrue(gitmodules_path.exists(), ".gitmodules must exist at repo root")

        gitmodules_content = gitmodules_path.read_text(encoding="utf-8")
        expected_paths = [
            "references/awesome-copilot",
            "references/awesome-agent-skills",
            "references/awesome-claude-skills",
            "references/ai-skills",
            "references/awesome-agents",
            "references/agent-skills",
            "references/mattpocock-eng-skills",
            "references/atv-starterkit",
        ]
        for path in expected_paths:
            self.assertIn(path, gitmodules_content, f"Expected submodule path '{path}' in .gitmodules")

        reference_library = (repo_root / "docs" / "reference-library.md").read_text(encoding="utf-8")

        # Contrary passage from the rejected submodule-removal model must be gone
        self.assertNotIn(
            "kept out of the autoharness Git install path",
            reference_library,
            "Contrary submodule-removal passage must not appear in reference-library.md",
        )

        # Document must still reference the references/ directory
        self.assertIn("references/", reference_library)

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

    def test_brainstorm_skill_is_registered_and_uses_registered_variables(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        brainstorm = repo_root / "templates" / "skills" / "brainstorm" / "SKILL.md.tmpl"
        content = brainstorm.read_text(encoding="utf-8")

        # Structure, frontmatter, and handoff invariants from the decision doc
        for phrase in (
            "doc_type: spec",
            "handoff_status:",
            "dark_factory_ready:",
            "BRAINSTORM_HANDOFF_READY",
            "#### Step 5.3: Execute Handoff",
            "## Non-Goals and Role Boundary",
        ):
            with self.subTest(invariant=phrase):
                self.assertIn(phrase, content)

        # The default `ask` handoff must be an accepted, defined value (no undefined promotion path)
        self.assertIn("`ask`", content)
        self.assertIn("**Ask** (default)", content)

        # Only registered docs/backlog variables may appear; the product-specs subdir
        # must never be hard-coded past the registered variable.
        self.assertNotIn("{{DOCS_ROOT}}/product-specs", content)
        allowed_variables = {
            "DOCS_PRODUCT_SPECS",
            "DOCS_COMPOUND",
            "DOCS_MEMORY",
            "BACKLOG_DIRECTORY",
            "STATUS_QUEUED",
            "OP_CREATE_MCP",
            "FIELD_TITLE",
            "FIELD_DESCRIPTION",
            "FIELD_STATUS",
            "FIELD_LABELS",
        }
        found_variables = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", content))
        self.assertTrue(
            found_variables.issubset(allowed_variables),
            f"unregistered template variables: {found_variables - allowed_variables}",
        )

        # The queue handoff must be executable for the registry-backed backlog-md
        # tool, not just backlogit prose and the manual .stash.md fallback.
        self.assertIn("{{OP_CREATE_MCP}}", content)

        # Registration in the enumeration surfaces
        for path in (
            repo_root / ".github" / "instructions" / "harness-architecture.instructions.md",
            repo_root / "docs" / "getting-started.md",
        ):
            with self.subTest(registration=str(path.relative_to(repo_root))):
                self.assertIn("brainstorm/SKILL.md", path.read_text(encoding="utf-8"))

        # install-harness must register brainstorm in BOTH the Step 2.5 skill manifest
        # AND the Primitive 4 template-group map row that drives Phase 1 group selection.
        installer = (repo_root / ".github" / "skills" / "install-harness" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("brainstorm/SKILL.md", installer)
        primitive4_rows = [ln for ln in installer.splitlines() if ln.startswith("| 4 - Orchestration |")]
        self.assertTrue(primitive4_rows, "Primitive 4 template-group map row not found")
        self.assertIn("skills/brainstorm", primitive4_rows[0])

        # impl-plan accepts a brainstorm requirements document as a planning source
        impl_plan = repo_root / "templates" / "skills" / "impl-plan" / "SKILL.md.tmpl"
        self.assertIn("{{DOCS_PRODUCT_SPECS}}", impl_plan.read_text(encoding="utf-8"))

        # Pipeline references must stay synchronized once brainstorm is a Primitive 4 front door
        for path in (
            repo_root / ".github" / "instructions" / "harness-architecture.instructions.md",
            repo_root / ".github" / "copilot-review-instructions.md",
        ):
            with self.subTest(pipeline=str(path.relative_to(repo_root))):
                self.assertIn("Brainstorm/Deliberate/Spike", path.read_text(encoding="utf-8"))

        # The public primitive overview must enumerate the brainstorm front door,
        # and the installer confirmation preview must list it as a generated skill,
        # so canonical architecture and operator-visible surfaces stay in agreement.
        primitives = (repo_root / "docs" / "primitives.md").read_text(encoding="utf-8")
        self.assertIn("**Brainstorm Skill**", primitives)
        installer_preview = (
            repo_root / ".github" / "agents" / "auto-mergeinstall.agent.md"
        ).read_text(encoding="utf-8")
        self.assertIn("brainstorm, deliberate, spike", installer_preview)

    def test_runtime_validator_model_is_woven_through_runtime_and_architecture_surfaces(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / "schemas" / "workspace-profile.schema.json": [
                '"runtime_validation"',
                '"validator_manifest"',
                '"PASS_WITH_FOLLOW_UP"',
                '"READY_WITH_CONDITIONS"',
            ],
            repo_root / "schemas" / "workspace-profile" / "1.0.0.schema.json": [
                '"runtime_validation"',
                '"validator_manifest"',
                '"PASS_WITH_FOLLOW_UP"',
                '"READY_WITH_CONDITIONS"',
            ],
            repo_root / ".autoharness" / "workspace-profile.yaml": [
                "runtime_validation:",
                "validator_manifest:",
                'minimum_verdict: "PASS"',
                'status_when_satisfied: "READY"',
            ],
            repo_root / "templates" / "skills" / "runtime-verification" / "SKILL.md.tmpl": [
                "runtime_validation.validator_manifest",
                "validator evidence",
                "manual checkpoint evidence",
                "PASS_WITH_FOLLOW_UP",
            ],
            repo_root / "templates" / "skills" / "operational-closure" / "SKILL.md.tmpl": [
                "validator evidence",
                "releasability evidence",
                "READY_WITH_CONDITIONS",
            ],
            repo_root / "templates" / "instructions" / "browser-verification.instructions.md.tmpl": [
                "validator evidence",
                "manual checkpoint evidence",
                "releasability evidence",
            ],
            repo_root / "templates" / "instructions" / "release-observability.instructions.md.tmpl": [
                "validator evidence",
                "releasability evidence",
                "READY_WITH_CONDITIONS",
            ],
            repo_root / "templates" / "agents" / "_ship.agent.md.tmpl": [
                "runtime_validation.validator_manifest",
                "validator evidence",
                "releasability evidence",
            ],
            repo_root / ".github" / "agents" / "_ship.agent.md": [
                "runtime_validation.validator_manifest",
                "validator evidence",
                "releasability evidence",
            ],
            repo_root / ".github" / "skills" / "workspace-discovery" / "SKILL.md": [
                "runtime_validation:",
                "validator_manifest",
                "validation_expectations",
                "releasability:",
            ],
            repo_root / ".github" / "skills" / "install-harness" / "SKILL.md": [
                "runtime_validation.validator_manifest",
                "runtime_validation.validation_expectations",
                "runtime_validation.releasability",
            ],
            repo_root / ".github" / "skills" / "tune-harness" / "SKILL.md": [
                "runtime_validation.validator_manifest",
                "validator evidence",
                "releasability evidence",
            ],
            repo_root / ".github" / "instructions" / "harness-architecture.instructions.md": [
                "validator evidence",
                "releasability evidence",
                "report-oriented runtime checks",
            ],
            repo_root / "docs" / "primitives.md": [
                "validator evidence",
                "releasability evidence",
                "report-oriented runtime checks",
            ],
            repo_root / "docs" / "capability-packs.md": [
                "validator evidence",
                "releasability evidence",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_role_boundary_tables_present_in_both_agent_templates(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        for tmpl_name in ("_stage.agent.md.tmpl", "_ship.agent.md.tmpl"):
            tmpl_path = repo_root / "templates" / "agents" / tmpl_name
            with self.subTest(template=tmpl_name):
                content = tmpl_path.read_text(encoding="utf-8")
                self.assertIn("## Role Boundary (NON-NEGOTIABLE)", content)
                self.assertIn("P-010", content)
                self.assertIn("Forbidden", content)
                self.assertIn("Allowed", content)

    def test_role_boundary_tables_have_complementary_operations(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        stage_content = (repo_root / "templates" / "agents" / "_stage.agent.md.tmpl").read_text(encoding="utf-8")
        ship_content = (repo_root / "templates" / "agents" / "_ship.agent.md.tmpl").read_text(encoding="utf-8")

        # Ship's Allowed includes claim/close shipments — Stage's Forbidden should reference that
        # Use table-scoped assertion to avoid false matches on incidental occurrences
        self.assertRegex(stage_content, r"\|\s*Claim\s.*\|")  # Stage Forbidden references claiming in table row
        self.assertIn("Claim shipments", ship_content)  # Ship Allowed

        # Stage's Allowed includes Create backlog items — Ship's Forbidden should reference that
        self.assertIn("Create backlog items", ship_content)  # Ship Forbidden
        self.assertIn("Create, update, archive backlog items", stage_content)  # Stage Allowed

        # Stage Forbidden: build operations. Ship Allowed: build operations.
        self.assertIn("Run build systems", stage_content)  # Stage Forbidden
        self.assertIn("Run build systems", ship_content)  # Ship Allowed

        # Stage Forbidden: PR operations. Ship Allowed: PR operations.
        self.assertIn("Create, push, or merge pull requests", stage_content)  # Stage Forbidden
        self.assertIn("Create, update, and merge pull requests", ship_content)  # Ship Allowed

    def test_role_enforcement_instruction_template_exists(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        tmpl_path = repo_root / "templates" / "instructions" / "role-enforcement.instructions.md.tmpl"
        self.assertTrue(tmpl_path.exists(), f"Missing: {tmpl_path}")
        content = tmpl_path.read_text(encoding="utf-8")
        self.assertIn("applyTo: '**'", content)
        self.assertIn("Role Boundary (NON-NEGOTIABLE)", content)
        self.assertIn("P-010", content)
        self.assertIn("Pre-Mutation Check Protocol", content)

    def test_release_unit_policy_requires_post_merge_closure_before_next_ship_execution(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / "templates" / "policies" / "workflow-policies.md.tmpl": [
                "post-merge release closure",
                "{{FEATURE_SHIPMENTS}}",
                "missing tag",
                "pending publish step",
            ],
            repo_root / "templates" / "agents" / "_orchestrator.agent.md.tmpl": [
                "awaiting required post-merge release closure",
                "Stage may proceed with planning",
                "must not route a second shipment to Ship until closure is complete",
            ],
            repo_root / "templates" / "agents" / "_ship.agent.md.tmpl": [
                "Release Closure Completion Gate (P-001, NON-NEGOTIABLE)",
                "post-merge release closure",
                "Treat the shipment as still active for P-001 purposes",
            ],
            repo_root / ".github" / "agents" / "_orchestrator.agent.md": [
                "awaiting required post-merge release closure",
                "Stage may proceed with planning",
                "must not route a second shipment to Ship until closure is complete",
            ],
            repo_root / ".github" / "agents" / "_ship.agent.md": [
                "Release Closure Completion Gate (P-001, NON-NEGOTIABLE)",
                "post-merge release closure",
                "Treat the shipment as still active for P-001 purposes",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_install_harness_references_role_enforcement_conditional_weaving(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        skill_path = repo_root / ".github" / "skills" / "install-harness" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        self.assertIn("role-enforcement.instructions.md", content)
        self.assertIn("two-agent", content)
        self.assertIn("Role Boundary (NON-NEGOTIABLE)", content)

    def test_feature_flow_prompts_route_through_orchestrator(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / "templates" / "prompts" / "feature-flow.prompt.md.tmpl": [
                "agent: Orchestrator",
                "standard `run pipeline` behavior",
                "Do not invoke Stage or Ship directly",
            ],
            repo_root / "templates" / "prompts" / "feature-flow-parallel.prompt.md.tmpl": [
                "agent: Orchestrator",
                "pipelined execution mode",
                "degrade to the standard sequential `feature-flow` path",
            ],
            repo_root / "templates" / "prompts" / "feature-flow-dark.prompt.md.tmpl": [
                "agent: Orchestrator",
                "Run pipeline in dark mode",
                "DARK_MODE_ACTIVE",
                "BRAINSTORM_HANDOFF_READY",
            ],
            repo_root / ".github" / "prompts" / "feature-flow.prompt.md": [
                "agent: Orchestrator",
                "standard `run pipeline` behavior",
            ],
            repo_root / ".github" / "prompts" / "feature-flow-parallel.prompt.md": [
                "agent: Orchestrator",
                "pipelined execution mode",
            ],
            repo_root / ".github" / "prompts" / "feature-flow-dark.prompt.md": [
                "agent: Orchestrator",
                "Run pipeline in dark mode",
                "DARK_MODE_ACTIVE",
                "BRAINSTORM_HANDOFF_READY",
            ],
            repo_root / "templates" / "agents" / "_orchestrator.agent.md.tmpl": [
                "`feature-flow`",
                "`feature-flow-parallel`",
                "`feature-flow-dark`",
                "workflow aliases, not alternate lifecycle implementations",
            ],
            repo_root / ".github" / "agents" / "_orchestrator.agent.md": [
                "feature-flow",
                "feature-flow-parallel",
                "feature-flow-dark",
                "must not bypass Stage, Ship, or the backlog / shipment model",
            ],
            repo_root / ".github" / "skills" / "install-harness" / "SKILL.md": [
                "feature-flow.prompt.md",
                "feature-flow-parallel.prompt.md",
                "feature-flow-dark.prompt.md",
                "Orchestrator's pipelined full-cycle routing preference",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_user_facing_docs_explain_feature_flow_entrypoints(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / "README.md": [
                "/feature-flow",
                "/feature-flow-parallel",
                "/feature-flow-dark",
                "workflow aliases, not separate pipelines",
                "existing Orchestrator workflow",
            ],
            repo_root / "docs" / "getting-started.md": [
                "Workflow Entry Points",
                "Invokes the Orchestrator",
                "degrades to sequential mode",
                "Run pipeline in dark mode",
                "Manual Agent-by-Agent Path",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_dark_factory_docs_and_verification_surfaces_are_woven(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / "AGENTS.md": [
                "P-017",
                "Run pipeline in dark mode",
                "local review readiness",
            ],
            repo_root / "templates" / "foundation" / "AGENTS.md.tmpl": [
                "Dark factory mode (P-017)",
                "Run pipeline in dark mode",
                "DARK_MODE_ACTIVE",
            ],
            repo_root / ".github" / "instructions" / "harness-architecture.instructions.md": [
                "P-017",
                "dark factory mode",
                "DARK_MODE_COMPLETE",
            ],
            repo_root / ".github" / "skills" / "install-harness" / "SKILL.md": [
                "Dark factory verification",
                "feature-flow-dark.prompt.md",
                "BRAINSTORM_HANDOFF_READY",
                "headRefOid",
            ],
            repo_root / ".github" / "skills" / "verify-harness" / "SKILL.md": [
                "dark factory mode surfaces",
                "feature-flow-dark",
                "P-017 dark factory references agree",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_output_timestamp_instruction_is_registered(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        expected_phrases_by_file = {
            repo_root / "templates" / "instructions" / "output-timestamps.instructions.md.tmpl": [
                "2026-07-02T18:49:41Z (+2m13s)",
                "phase transitions and long-running operation boundaries",
                "first stamp in a session",
            ],
            repo_root / ".github" / "instructions" / "output-timestamps.instructions.md": [
                "2026-07-02T18:49:41Z (+2m13s)",
                "phase transitions and long-running operation boundaries",
                "first stamp in a session",
            ],
            repo_root / ".github" / "skills" / "install-harness" / "SKILL.md": [
                "output-timestamps.instructions.md",
                "instructions/output-timestamps",
                "no variable-resolution-table entry is required",
            ],
            repo_root / "templates" / "instructions" / "agent-intercom.instructions.md.tmpl": [
                "output-timestamps.instructions.md",
                "single source of truth",
                "ISO-8601 UTC",
            ],
            repo_root / ".github" / "instructions" / "agent-intercom.instructions.md": [
                "output-timestamps.instructions.md",
                "single source of truth",
                "ISO-8601 UTC",
            ],
        }

        for file_path, expected_phrases in expected_phrases_by_file.items():
            with self.subTest(file=str(file_path.relative_to(repo_root))):
                content = file_path.read_text(encoding="utf-8")
                for expected_phrase in expected_phrases:
                    self.assertIn(expected_phrase, content)

    def test_verify_workspace_flags_missing_dark_factory_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            staging = workspace / ".autoharness" / "staging"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "policies").mkdir(parents=True, exist_ok=True)

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
                    "primitives_installed": [4, 5, 8],
                    "capability_packs": ["agent-intercom"],
                    "artifacts": [
                        {
                            "path": ".github/prompts/feature-flow-dark.prompt.md",
                            "primitive": 4,
                            "template": "templates/prompts/feature-flow-dark.prompt.md.tmpl",
                            "checksum": "stale-checksum",
                        }
                    ],
                    "variables_used": {"PROJECT_NAME": "demo-workspace"},
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "policies" / "workflow-policies.md").write_text(
                "P-017\nRun pipeline in dark mode\nDARK_MODE_ACTIVE\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home, staging)

            checks = report["targeted_checks"]
            self.assertIn("dark_factory_policy_contract", checks)
            self.assertFalse(checks["dark_factory_policy_contract"]["ok"])
            self.assertIn(
                "BRAINSTORM_HANDOFF_READY",
                checks["dark_factory_policy_contract"]["missing"],
            )
            self.assertIn("dark_factory_prompt_contract", checks)
            self.assertFalse(checks["dark_factory_prompt_contract"]["ok"])
            self.assertEqual(checks["dark_factory_prompt_contract"]["reason"], "missing file")
            self.assertTrue(_report_has_failures(report))

    def test_verify_workspace_does_not_run_dark_factory_checks_for_policy_only_installs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            staging = workspace / ".autoharness" / "staging"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)

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
                    "primitives_installed": [8],
                    "capability_packs": [],
                    "artifacts": [
                        {
                            "path": ".github/policies/workflow-policies.md",
                            "primitive": 8,
                            "template": "templates/policies/workflow-policies.md.tmpl",
                            "checksum": "stale-checksum",
                        }
                    ],
                    "variables_used": {"PROJECT_NAME": "demo-workspace"},
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            report = verify_workspace(workspace, autoharness_home, staging)

            self.assertNotIn("dark_factory_policy_contract", report["targeted_checks"])
            self.assertNotIn("dark_factory_prompt_contract", report["targeted_checks"])

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
                "archive_item": {"mcp_tool": "backlogit_archive_item", "cli_command": "backlogit archive {{id}}"},
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
        self.assertEqual(variables["OP_ARCHIVE_ITEM_MCP"], "backlogit_archive_item")
        self.assertEqual(variables["OP_ARCHIVE_ITEM_CLI"], "backlogit archive {{id}}")
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

    def _run_manifest_placeholder_scan(self, root: Path, autoharness_version: str) -> dict:
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
                "autoharness_version": autoharness_version,
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

        return verify_workspace(workspace, autoharness_home, staging)

    def test_verify_workspace_flags_unresolved_manifest_scalar_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = self._run_manifest_placeholder_scan(
                Path(temp_dir), "{{AUTOHARNESS_VERSION}}"
            )

            manifest_blockers = [
                blocker
                for blocker in report["blockers"]
                if blocker.get("kind") == "unresolved-manifest-placeholder"
            ]
            self.assertEqual(len(manifest_blockers), 1)
            blocker = manifest_blockers[0]
            self.assertEqual(blocker["field"], "autoharness_version")
            self.assertEqual(blocker["placeholder"], "{{AUTOHARNESS_VERSION}}")
            self.assertIn("autoharness_version", blocker["message"])
            self.assertTrue(_report_has_failures(report))

    def test_verify_workspace_passes_resolved_manifest_scalars(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = self._run_manifest_placeholder_scan(Path(temp_dir), "1.3.2")

            self.assertEqual(
                [
                    blocker
                    for blocker in report["blockers"]
                    if blocker.get("kind") == "unresolved-manifest-placeholder"
                ],
                [],
            )
            self.assertEqual(report["blockers"], [])
            self.assertEqual(report["unresolved"], [])

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

    def test_verify_workspace_checks_runtime_validation_contracts(self) -> None:
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
            (workspace / ".github" / "skills" / "workspace-discovery").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "install-harness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "tune-harness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "agents").mkdir(parents=True, exist_ok=True)

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
                    "installed_at": "2026-05-23T00:00:00Z",
                    "autoharness_version": "1.3.4",
                    "profile_hash": "abc",
                    "primitives_installed": [1, 4, 10],
                    "capability_packs": ["browser-verification", "release-observability"],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(
                workspace / ".autoharness" / "workspace-profile.yaml",
                {
                    "schema_version": "1.0.0",
                    "runtime_surfaces": {
                        "cli": True,
                        "web_ui": True,
                        "public_api": False,
                        "background_jobs": False,
                        "browser_tooling": ["playwright"],
                        "deployment_manifests": ["Dockerfile"],
                    },
                    "runtime_validation": {
                        "validator_manifest": {
                            "surfaces": [
                                {
                                    "surface": "cli",
                                    "adapter_hint": "command",
                                    "probe_hints": [
                                        {
                                            "id": "cli-help",
                                            "kind": "command",
                                            "target": "demo --help",
                                            "required": True,
                                            "evidence_types": ["stdout", "exit-code"],
                                        }
                                    ],
                                    "manual_checkpoints": [],
                                },
                                {
                                    "surface": "browser",
                                    "adapter_hint": "browser",
                                    "probe_hints": [
                                        {
                                            "id": "ui-smoke",
                                            "kind": "browser-flow",
                                            "target": "/",
                                            "required": True,
                                            "evidence_types": ["screenshot", "trace"],
                                        }
                                    ],
                                    "manual_checkpoints": [
                                        {
                                            "id": "oauth",
                                            "label": "Complete SSO",
                                            "reason": "External IdP",
                                            "required_for_release": True,
                                            "evidence_types": ["operator-note"],
                                        }
                                    ],
                                },
                            ]
                        },
                        "validation_expectations": {
                            "required": True,
                            "surfaces_expected": ["cli", "browser"],
                            "minimum_verdict": "PASS",
                            "preserve_invariants": ["CLI starts cleanly"],
                            "release_blockers": ["Browser smoke fails"],
                        },
                        "releasability": {
                            "required": True,
                            "status_when_satisfied": "READY_WITH_CONDITIONS",
                            "required_evidence": [
                                {"kind": "monitoring-plan", "required": True},
                                {"kind": "rollback-trigger", "required": True},
                            ],
                        },
                    },
                },
            )

            (workspace / ".github" / "instructions" / "browser-verification.instructions.md").write_text(
                "headed\nheadless\nroute\nvalidator evidence\nmanual checkpoint evidence\nreleasability evidence\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "instructions" / "release-observability.instructions.md").write_text(
                "monitoring\nrollback\nobservation window\nvalidator evidence\nreleasability evidence\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "workspace-discovery" / "SKILL.md").write_text(
                "runtime_validation:\nvalidator_manifest\nvalidation_expectations\nreleasability:\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "install-harness" / "SKILL.md").write_text(
                "runtime_validation.validator_manifest\nruntime_validation.validation_expectations\nruntime_validation.releasability\nvalidator evidence\nreleasability evidence\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "tune-harness" / "SKILL.md").write_text(
                "runtime_validation.validator_manifest\nruntime_validation.validation_expectations\nruntime_validation.releasability\nvalidator evidence\nreleasability evidence\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
                "runtime_validation.validator_manifest\nruntime_validation.validation_expectations\nvalidator evidence\nreleasability evidence\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "instructions" / "harness-architecture.instructions.md").write_text(
                "validator evidence\nreleasability evidence\nreport-oriented runtime checks\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["runtime_validation_profile_contract"]["ok"])
            self.assertTrue(targeted_checks["browser_verification_instruction"]["ok"])
            self.assertTrue(targeted_checks["release_observability_instruction"]["ok"])
            self.assertTrue(targeted_checks["workspace_discovery_runtime_validation_contract"]["ok"])
            self.assertTrue(targeted_checks["install_harness_runtime_validation_contract"]["ok"])
            self.assertTrue(targeted_checks["tune_harness_runtime_validation_contract"]["ok"])
            self.assertTrue(targeted_checks["ship_runtime_validation_contract"]["ok"])
            self.assertTrue(targeted_checks["harness_architecture_runtime_validation_contract"]["ok"])

    def test_verify_workspace_flags_missing_runtime_validation_contract(self) -> None:
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

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-05-23T00:00:00Z",
                    "autoharness_version": "1.3.4",
                    "profile_hash": "abc",
                    "primitives_installed": [1, 10],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(
                workspace / ".autoharness" / "workspace-profile.yaml",
                {
                    "schema_version": "1.0.0",
                    "runtime_surfaces": {
                        "cli": True,
                        "web_ui": False,
                        "public_api": False,
                        "background_jobs": False,
                        "browser_tooling": [],
                        "deployment_manifests": [],
                    },
                },
            )

            report = verify_workspace(workspace, autoharness_home)

            check = report["targeted_checks"]["runtime_validation_profile_contract"]
            self.assertFalse(check["ok"])
            self.assertIn("runtime_validation", check["missing"])

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
            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
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

    def test_verify_workspace_checks_pipeline_topology_gate_hook_wiring(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "install-harness").mkdir(parents=True, exist_ok=True)
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
                    "installed_at": "2026-04-25T00:00:00Z",
                    "autoharness_version": "1.3.2",
                    "profile_hash": "abc",
                    "primitives_installed": [1],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "skills" / "install-harness" / "SKILL.md").write_text(
                "Pipeline-topology pre-commit hook\n"
                "pre-commit-pipeline-topology.sh.tmpl\n"
                "pre-commit-pipeline-topology.ps1.tmpl\n"
                "autoharness gate pipeline-topology --mode manual --phase ambient\n"
                "#### Step 4.4: Structural Validation\n"
                "9. **Pipeline-topology hook verification**\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "tune-harness" / "SKILL.md").write_text(
                "* **Pipeline-topology hook drift** (universal):\n"
                "  scripts/pre-commit-pipeline-topology.sh and .ps1\n"
                "  AUTOHARNESS_TOPOLOGY_GATE_BLOCKING toggle\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["pipeline_topology_gate_install_wiring"]["ok"])
            self.assertTrue(targeted_checks["pipeline_topology_gate_tune_wiring"]["ok"])

    def test_pipeline_topology_gate_assertion_passes_on_dogfood_repo(self) -> None:
        # Proves the new FOUNDATION_ASSERTIONS entries pass against this
        # repo's OWN installed skill copies (109.013-T acceptance criterion:
        # "verify_workspace assertion added and passes on the installed
        # end state").
        repo_root = Path(__file__).resolve().parents[1]
        keys = {"pipeline_topology_gate_install_wiring", "pipeline_topology_gate_tune_wiring"}
        assertions = [a for a in FOUNDATION_ASSERTIONS if a["key"] in keys]
        self.assertEqual({a["key"] for a in assertions}, keys)
        report: dict = {"targeted_checks": {}}
        for assertion in assertions:
            path = repo_root / assertion["path"]
            self.assertTrue(path.exists(), f"missing dogfood artifact: {path}")
            _add_text_check(
                report,
                assertion["key"],
                path,
                assertion["must_contain"],
                [tuple(pair) for pair in assertion.get("must_precede") or []],
            )
        for key in keys:
            self.assertTrue(
                report["targeted_checks"][key]["ok"],
                report["targeted_checks"][key],
            )

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
                "Step 1.8\ncompound library\ncontinuous-learning\nclosure artifacts\nlearning_signals{}\n",
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

    def test_verify_workspace_requires_structured_learning_signals_in_auto_tune_agent(self) -> None:
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
            targeted_checks = report["targeted_checks"]
            self.assertFalse(targeted_checks["auto_tune_learning_loop_contract"]["ok"])
            self.assertIn(
                "learning_signals{}",
                " ".join(targeted_checks["auto_tune_learning_loop_contract"].get("missing") or []),
            )

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

    def test_review_surface_templates_and_routing_are_wired(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        expected_templates = [
            repo_root / "templates" / "agents" / "review" / "security-reviewer.agent.md.tmpl",
            repo_root / "templates" / "agents" / "review" / "security-lens-reviewer.agent.md.tmpl",
            repo_root / "templates" / "agents" / "review" / "template-integrity-reviewer.agent.md.tmpl",
            repo_root / "templates" / "agents" / "review" / "schema-cli-docs-coupling-reviewer.agent.md.tmpl",
            repo_root / "templates" / "agents" / "security-sentinel.agent.md.tmpl",
            repo_root / "templates" / "skills" / "security-audit" / "SKILL.md.tmpl",
        ]
        for template_path in expected_templates:
            with self.subTest(template=str(template_path.relative_to(repo_root))):
                self.assertTrue(template_path.exists(), f"Missing template: {template_path}")

        review_skill = repo_root / "templates" / "skills" / "review" / "SKILL.md.tmpl"
        review_content = review_skill.read_text(encoding="utf-8")
        self.assertIn("Security Reviewer", review_content)
        self.assertIn("security-reviewer.agent.md", review_content)
        self.assertIn("Template Integrity Reviewer", review_content)
        self.assertIn("template-integrity-reviewer.agent.md", review_content)
        self.assertIn("Schema-CLI-Docs Coupling Reviewer", review_content)
        self.assertIn("schema-cli-docs-coupling-reviewer.agent.md", review_content)
        self.assertIn("READY_WITH_FOLLOWUPS", review_content)

        plan_review_skill = repo_root / "templates" / "skills" / "plan-review" / "SKILL.md.tmpl"
        plan_review_content = plan_review_skill.read_text(encoding="utf-8")
        self.assertIn("Security Lens Reviewer", plan_review_content)
        self.assertIn("security-lens-reviewer.agent.md", plan_review_content)

    def test_verify_workspace_checks_security_persona_routing_in_installed_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "review").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "plan-review").mkdir(parents=True, exist_ok=True)

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
                    "installed_at": "2026-05-05T00:00:00Z",
                    "autoharness_version": "1.4.1",
                    "profile_hash": "abc",
                    "primitives_installed": [5, 7],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "skills" / "review" / "SKILL.md").write_text(
                "## Conditional Personas\n"
                "| **Security Reviewer** | auth middleware, endpoints | Different |\n"
                "| **Template Integrity Reviewer** | templates, markdown harness assets | Different |\n"
                "| **Schema-CLI-Docs Coupling Reviewer** | schemas + docs + verification | Different |\n"
                "READY_WITH_FOLLOWUPS\n"
                "BLOCKED\n"
                "reviewed HEAD SHA\n"
                "security-reviewer.agent.md\n"
                "template-integrity-reviewer.agent.md\n"
                "schema-cli-docs-coupling-reviewer.agent.md\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "plan-review" / "SKILL.md").write_text(
                "## Cross-Model Personas\n"
                "| **Security Lens Reviewer** | auth, API surfaces | Different |\n"
                "security-lens-reviewer.agent.md\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["security_review_persona_routing"]["ok"])
            self.assertTrue(targeted_checks["local_review_readiness_contract"]["ok"])
            self.assertTrue(targeted_checks["template_integrity_reviewer_routing"]["ok"])
            self.assertTrue(targeted_checks["schema_cli_docs_reviewer_routing"]["ok"])
            self.assertTrue(targeted_checks["security_plan_review_persona_routing"]["ok"])

    def test_browser_experiment_skill_templates_exist_and_install_harness_is_wired(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        expected_templates = [
            repo_root / "templates" / "skills" / "browser-automation" / "SKILL.md.tmpl",
            repo_root / "templates" / "skills" / "iterative-experiment" / "SKILL.md.tmpl",
        ]
        for template_path in expected_templates:
            with self.subTest(template=str(template_path.relative_to(repo_root))):
                self.assertTrue(template_path.exists(), f"Missing template: {template_path}")

        install_harness_skill = repo_root / ".github" / "skills" / "install-harness" / "SKILL.md"
        install_harness_content = install_harness_skill.read_text(encoding="utf-8")

        self.assertIn(
            "browser-automation/SKILL.md` — Install when `browser-verification` is enabled",
            install_harness_content,
        )
        self.assertIn(
            "iterative-experiment/SKILL.md` — Install when the `workflow` layer is active",
            install_harness_content,
        )

        browser_verification_table_idx = install_harness_content.find(
            "overlay target map for `browser-verification`"
        )
        self.assertGreater(
            browser_verification_table_idx,
            -1,
            "browser-verification overlay target table not found in install-harness SKILL.md",
        )
        overlay_section = install_harness_content[browser_verification_table_idx:]
        self.assertIn(
            "| Automation skill | `browser-automation/SKILL.md` — treated as an explicit overlay target",
            overlay_section,
            "browser-automation/SKILL.md not listed in browser-verification overlay table",
        )

    def test_verify_workspace_checks_browser_experiment_install_harness_wiring(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "install-harness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "review").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "skills" / "plan-review").mkdir(parents=True, exist_ok=True)

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
                    "installed_at": "2026-05-05T00:00:00Z",
                    "autoharness_version": "1.4.1",
                    "profile_hash": "abc",
                    "primitives_installed": [4, 5],
                    "capability_packs": ["browser-verification"],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "skills" / "install-harness" / "SKILL.md").write_text(
                "## Skill Installation Manifest\n"
                "browser-automation/SKILL.md` — Install when `browser-verification` is enabled. Resolves browser variables.\n"
                "iterative-experiment/SKILL.md` — Install when the `workflow` layer is active. Resolves experiment variables.\n"
                "## Overlay\n"
                "overlay target map for `browser-verification`\n"
                "| Automation skill | `browser-automation/SKILL.md` — treated as an explicit overlay target, not an optional add-on |\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "review" / "SKILL.md").write_text(
                "## Conditional Personas\n"
                "| **Security Reviewer** | auth middleware |\n"
                "security-reviewer.agent.md\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "skills" / "plan-review" / "SKILL.md").write_text(
                "## Cross-Model Personas\n"
                "| **Security Lens Reviewer** | auth, API surfaces |\n"
                "security-lens-reviewer.agent.md\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["install_harness_browser_skill_manifest"]["ok"])
            self.assertTrue(targeted_checks["install_harness_browser_verification_overlay"]["ok"])

    def test_verify_workspace_checks_agent_session_discipline(self) -> None:
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
                    "installed_at": "2026-05-06T00:00:00Z",
                    "autoharness_version": "1.5.0",
                    "profile_hash": "abc",
                    "primitives_installed": [4, 5],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "agents" / "_stage.agent.md").write_text(
                "## Role Boundary (NON-NEGOTIABLE)\n"
                "P-010\n"
                "Forbidden\n"
                "## Step 0.0: Tool Availability Gate (P-012)\n"
                "TOOL_OK\n"
                "TOOL_DEGRADED\n"
                "TOOL_UNAVAILABLE\n"
                "P-012\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
                "Branch Creation Gate (P-011, NON-NEGOTIABLE)\n"
                "git branch --show-current\n"
                "BRANCH_OK\n"
                "BRANCH_CREATED\n"
                "BRANCH_MISMATCH\n"
                "Branch retention (NON-NEGOTIABLE)\n"
                "Post-Merge Branch Protocol (NON-NEGOTIABLE)\n"
                "Branch Management Rules (NON-NEGOTIABLE)\n"
                "post-merge/{feature_slug}\n"
                "source_stash_id\nsource_deliberation_id\nbacklogit_stash_remove\nbacklogit_archive_item\n"
                "## Step 0.0: Tool Availability Gate (P-012)\n"
                "TOOL_OK\n"
                "TOOL_DEGRADED\n"
                "TOOL_UNAVAILABLE\n"
                "P-012\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["stage_role_boundary"]["ok"])
            self.assertTrue(targeted_checks["stage_tool_availability_gate"]["ok"])
            self.assertTrue(targeted_checks["ship_branch_creation_gate"]["ok"])
            self.assertTrue(targeted_checks["ship_tool_availability_gate"]["ok"])

    def test_verify_workspace_checks_session_lifecycle_gates(self) -> None:
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
                    "installed_at": "2026-05-06T00:00:00Z",
                    "autoharness_version": "1.5.0",
                    "profile_hash": "abc",
                    "primitives_installed": [4, 5],
                    "capability_packs": ["backlogit"],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "agents" / "_stage.agent.md").write_text(
                "## Index Sync\n"
                "backlogit_sync_index\n"
                "INDEX_SYNC_OK\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
                "backlogit_sync_index\n"
                "INDEX_SYNC_OK\n"
                "CLOSURE_INDEX_SYNC_OK\n"
                "#### Merge Confirmation Gate (NON-NEGOTIABLE)\n"
                "MERGE_CONFIRMED\n"
                "MERGE_NOT_CONFIRMED\n"
                "merge-base --is-ancestor\n"
                "Mandatory (P-020): Invoke compact-context with target: all\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["stage_index_sync_gate"]["ok"])
            self.assertTrue(targeted_checks["ship_index_sync_gate"]["ok"])
            self.assertTrue(targeted_checks["ship_merge_confirmation_gate"]["ok"])
            self.assertTrue(targeted_checks["ship_post_merge_compaction_gate"]["ok"])

    def test_verify_workspace_ship_post_merge_compaction_gate_fails_when_missing(self) -> None:
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
                    json.dumps(strict_schema), encoding="utf-8"
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema), encoding="utf-8"
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-07-29T00:00:00Z",
                    "autoharness_version": "1.5.0",
                    "profile_hash": "abc",
                    "primitives_installed": [4, 5],
                    "capability_packs": ["backlogit"],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            # Ship agent present but the post-merge compaction step (P-020) is missing.
            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
                "#### Merge Confirmation Gate (NON-NEGOTIABLE)\n"
                "MERGE_CONFIRMED\n"
                "MERGE_NOT_CONFIRMED\n"
                "merge-base --is-ancestor\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            compaction_check = targeted_checks["ship_post_merge_compaction_gate"]
            self.assertFalse(compaction_check["ok"])
            self.assertIn("compact-context", compaction_check["missing"])
            self.assertIn("target: all", compaction_check["missing"])
            self.assertIn("P-020", compaction_check["missing"])

    def test_orchestrator_template_exists_and_dispatch_template_removed(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        orchestrator_tmpl = repo_root / "templates" / "agents" / "_orchestrator.agent.md.tmpl"
        dispatch_tmpl = repo_root / "templates" / "agents" / "dispatch.agent.md.tmpl"

        self.assertTrue(orchestrator_tmpl.exists(), "_orchestrator.agent.md.tmpl must exist")
        self.assertFalse(dispatch_tmpl.exists(), "dispatch.agent.md.tmpl must not exist after P-013 rename")

    def test_no_operator_ai_persona_in_agent_templates(self) -> None:
        """P-013.1: 'Operator' is reserved for the human user; no agent template may
        claim this name or declare itself as the Operator AI persona."""
        repo_root = Path(__file__).resolve().parents[1]
        agents_dir = repo_root / "templates" / "agents"

        violations = []
        prohibited_patterns = [
            'name: Operator',
            'name: "Operator"',
            "name: 'Operator'",
            "You are the Operator",
        ]
        for tmpl in agents_dir.rglob("*.agent.md.tmpl"):
            content = tmpl.read_text(encoding="utf-8")
            rel = str(tmpl.relative_to(repo_root))
            for pattern in prohibited_patterns:
                if pattern in content:
                    violations.append(f"{rel}: found prohibited pattern {pattern!r}")

        self.assertEqual(
            violations,
            [],
            "Agent templates must not use 'Operator' as an AI persona name "
            f"(P-013.1 persona isolation):\n" + "\n".join(violations),
        )

    def test_orchestrator_template_has_tier_fields(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        orchestrator_tmpl = repo_root / "templates" / "agents" / "_orchestrator.agent.md.tmpl"

        content = orchestrator_tmpl.read_text(encoding="utf-8")
        self.assertNotIn(
            "model_tier:",
            content,
            "orchestrator template must not declare model_tier (removed; tier is config-resolved via model_routing)",
        )
        self.assertIn("max_subagent_tier:", content, "orchestrator template must declare max_subagent_tier")

    def test_all_agent_templates_have_max_subagent_tier_and_no_model_tier(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        agents_dir = repo_root / "templates" / "agents"

        has_model_tier = []
        missing_max = []
        for tmpl in agents_dir.rglob("*.agent.md.tmpl"):
            content = tmpl.read_text(encoding="utf-8")
            rel = str(tmpl.relative_to(repo_root))
            if "model_tier:" in content:
                has_model_tier.append(rel)
            if "max_subagent_tier:" not in content:
                missing_max.append(rel)

        self.assertEqual(
            has_model_tier,
            [],
            "Agent templates must not declare model_tier frontmatter "
            f"(removed; tier is config-resolved via model_routing): {has_model_tier}",
        )
        self.assertEqual(
            missing_max,
            [],
            f"Agent templates missing max_subagent_tier frontmatter field: {missing_max}",
        )

    def test_no_agent_definition_declares_model_tier(self) -> None:
        """model_tier frontmatter is retired across templates AND installed
        instances; the tier is defined by the config model_routing binding and
        the template's tier selection, not a redundant per-agent integer."""
        repo_root = Path(__file__).resolve().parents[1]
        offenders = []
        for base, pattern in (
            (repo_root / "templates" / "agents", "*.agent.md.tmpl"),
            (repo_root / ".github" / "agents", "*.agent.md"),
        ):
            if not base.exists():
                continue
            for agent_file in base.rglob(pattern):
                content = agent_file.read_text(encoding="utf-8")
                if content.startswith("---"):
                    end = content.find("\n---", 3)
                    frontmatter = content[3:end] if end != -1 else content
                else:
                    frontmatter = content
                if "model_tier:" in frontmatter:
                    offenders.append(str(agent_file.relative_to(repo_root)))

        self.assertEqual(
            offenders,
            [],
            "Agent definitions must not declare model_tier frontmatter "
            f"(removed; tier is config-resolved via model_routing): {offenders}",
        )

    def test_verify_workspace_checks_orchestrator_tier_fields(self) -> None:
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
                    "installed_at": "2026-05-07T00:00:00Z",
                    "autoharness_version": "1.5.0",
                    "profile_hash": "abc",
                    "primitives_installed": [3, 4],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            # Valid frontmatter: max_subagent_tier present as integer in range 1-3
            # (model_tier is no longer required — tier is config-resolved)
            (workspace / ".github" / "agents" / "_orchestrator.agent.md").write_text(
                "---\n"
                "name: Orchestrator\n"
                "max_subagent_tier: 3\n"
                "---\n\n"
                "# Orchestrator\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])
            targeted_checks = report["targeted_checks"]
            check = targeted_checks["orchestrator_tier_fields"]
            self.assertTrue(check["ok"])
            self.assertEqual(check.get("errors", []), [])

    def test_verify_workspace_rejects_non_integer_tier_fields_in_orchestrator(self) -> None:
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
                    "installed_at": "2026-05-07T00:00:00Z",
                    "autoharness_version": "1.5.0",
                    "profile_hash": "abc",
                    "primitives_installed": [3, 4],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            # Invalid: max_subagent_tier is out of range (model_tier is ignored — removed)
            (workspace / ".github" / "agents" / "_orchestrator.agent.md").write_text(
                "---\n"
                "name: Orchestrator\n"
                "max_subagent_tier: 5\n"
                "---\n\n"
                "# Orchestrator\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            check = targeted_checks["orchestrator_tier_fields"]
            self.assertFalse(check["ok"])
            errors = check.get("errors", [])
            self.assertTrue(
                any("max_subagent_tier" in e and "range" in e for e in errors),
                f"Expected max_subagent_tier range error, got: {errors}",
            )
            self.assertFalse(
                any("model_tier" in e for e in errors),
                f"model_tier must no longer be validated, got: {errors}",
            )

    def test_frontmatter_tier_check_ignores_legacy_model_tier_field(self) -> None:
        """Backward compatibility: an already-installed agent that still carries a
        leftover model_tier field must remain conformant. Removing model_tier from
        the check is a graceful, non-breaking change — the extra field is ignored,
        not flagged — so existing installed workspaces do not regress until they
        are re-installed or tuned."""
        from autoharness.verify_workspace import _add_frontmatter_tier_check

        with tempfile.TemporaryDirectory() as temp_dir:
            agent = Path(temp_dir) / "_orchestrator.agent.md"
            agent.write_text(
                "---\n"
                "name: Orchestrator\n"
                "model_tier: 2\n"  # legacy leftover
                "max_subagent_tier: 3\n"
                "---\n\n"
                "# Orchestrator\n",
                encoding="utf-8",
            )
            report: dict = {"targeted_checks": {}}
            _add_frontmatter_tier_check(report, "legacy", agent)
            check = report["targeted_checks"]["legacy"]
            self.assertTrue(
                check["ok"],
                f"legacy model_tier must be ignored, not flagged: {check}",
            )
            self.assertEqual(check.get("errors", []), [])

    def test_verify_workspace_checks_p013_policy_in_workflow_policies(self) -> None:
        """The installed workflow-policies.md must document P-013 with the
        config-resolved tier language (model_routing -> resolved model fields)
        and the max_subagent_tier ceiling. Exercised independently of the
        legacy model_tier backward-compatibility test above so a failure in
        either test identifies the correct contract."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"

            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            (workspace / ".github" / "policies").mkdir(parents=True, exist_ok=True)

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
                    "installed_at": "2026-05-07T00:00:00Z",
                    "autoharness_version": "1.5.0",
                    "profile_hash": "abc",
                    "primitives_installed": [3, 8],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "policies" / "workflow-policies.md").write_text(
                "## P-013: Agent Tier Hierarchy and Escalation\n\n"
                "Every agent operates at the tier bound to it by the config-driven "
                "model_routing map, resolved into its model_family/model_provider/"
                "reasoning_effort frontmatter.\n"
                "An agent must not invoke a subagent at a tier higher than its max_subagent_tier.\n\n"
                "## P-014: Local Review Readiness Merge Gate\n\n"
                "The readiness summary must include the reviewed HEAD SHA.\n"
                "Outcome may be READY or READY_WITH_FOLLOWUPS.\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])
            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["p013_policy_in_workflow_policies"]["ok"])
            self.assertTrue(targeted_checks["p014_local_review_policy"]["ok"])

    # -- P-013.5: invocation-time model-routing enforcement (104.007-T / 104.008-T) --

    def _write_minimal_verify_workspace_fixture(
        self,
        workspace: Path,
        autoharness_home: Path,
        *,
        orchestrator_family: str = "gpt-5.6-sol",
        orchestrator_provider: str = "openai",
        stage_family: str = "claude-opus-4.8",
        stage_provider: str = "anthropic",
        ship_family: str = "claude-sonnet-5",
        ship_provider: str = "anthropic",
        orchestrator_extra_body: str = "",
        model_routing: dict | None = None,
    ) -> None:
        """Shared fixture builder for P-013.5 targeted-check tests: a minimal
        installed workspace with _orchestrator/_stage/_ship agent definitions
        and a resolved config.yaml."""
        (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
        (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True, exist_ok=True)
        (autoharness_home / "schemas" / "harness-config").mkdir(parents=True, exist_ok=True)
        (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True, exist_ok=True)
        (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
        (workspace / ".github" / "agents").mkdir(parents=True, exist_ok=True)

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
                json.dumps(strict_schema), encoding="utf-8"
            )
        for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
            (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                json.dumps(strict_schema), encoding="utf-8"
            )

        _write_yaml(
            workspace / ".autoharness" / "harness-manifest.yaml",
            {
                "schema_version": "1.0.0",
                "installed_at": "2026-05-07T00:00:00Z",
                "autoharness_version": "1.5.0",
                "profile_hash": "abc",
                "primitives_installed": [3, 8],
                "capability_packs": [],
                "artifacts": [],
            },
        )
        config_body: dict = {"schema_version": "1.0.0"}
        if model_routing is not None:
            config_body["model_routing"] = model_routing
        _write_yaml(workspace / ".autoharness" / "config.yaml", config_body)
        _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

        (workspace / ".github" / "agents" / "_orchestrator.agent.md").write_text(
            "---\n"
            "name: _Orchestrator\n"
            "max_subagent_tier: 3\n"
            f'reasoning_effort: "high"\n'
            f'model_provider: "{orchestrator_provider}"\n'
            f'model_family: "{orchestrator_family}"\n'
            "---\n\n"
            "# Orchestrator\n\n"
            "### Step 1: Route to Stage\n\n"
            "Resolve routed model (P-013.5): resolve config.model_routing.stage "
            "(fallback tier3) and declare the resolved model_family/model_provider "
            "as the invocation override when invoking Stage. Emit ROUTING_DEGRADED "
            "when the runtime cannot honor a per-invocation override.\n\n"
            "### Step 2: Route to Ship\n\n"
            "Resolve routed model (P-013.5): resolve config.model_routing.ship "
            "(fallback tier2) and declare the resolved model_family/model_provider "
            "as the invocation override when invoking Ship. Emit ROUTING_DEGRADED "
            "when the runtime cannot honor a per-invocation override.\n"
            f"{orchestrator_extra_body}",
            encoding="utf-8",
        )
        (workspace / ".github" / "agents" / "_stage.agent.md").write_text(
            "---\n"
            "name: _Stage\n"
            "max_subagent_tier: 3\n"
            f'reasoning_effort: "high"\n'
            f'model_provider: "{stage_provider}"\n'
            f'model_family: "{stage_family}"\n'
            "---\n\n"
            "# Stage\n",
            encoding="utf-8",
        )
        (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
            "---\n"
            "name: _Ship\n"
            "max_subagent_tier: 2\n"
            f'reasoning_effort: "high"\n'
            f'model_provider: "{ship_provider}"\n'
            f'model_family: "{ship_family}"\n'
            "---\n\n"
            "# Ship\n",
            encoding="utf-8",
        )

    def test_verify_workspace_checks_stage_ship_orchestrator_model_routing_fields(self) -> None:
        """P-013.5: installed _stage/_ship/_orchestrator agents must declare
        non-empty model_family/model_provider with no unresolved placeholder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(workspace, autoharness_home)

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])
            targeted_checks = report["targeted_checks"]
            for key in (
                "orchestrator_model_routing_fields",
                "stage_model_routing_fields",
                "ship_model_routing_fields",
            ):
                self.assertIn(key, targeted_checks, f"expected targeted check {key!r} to be present")
                self.assertTrue(
                    targeted_checks[key]["ok"],
                    f"{key} expected ok, got {targeted_checks[key]}",
                )

    def test_verify_workspace_flags_unresolved_model_routing_placeholder(self) -> None:
        """P-013.5 fail-closed: an installed agent whose model_family is empty
        or an unresolved {{...}} placeholder must fail verification, not pass
        silently. Red before this task, green after."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            # Ship's model_family was never resolved by the installer.
            self._write_minimal_verify_workspace_fixture(
                workspace, autoharness_home, ship_family="{{SHIP_FAMILY}}"
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("ship_model_routing_fields", targeted_checks)
            ship_check = targeted_checks["ship_model_routing_fields"]
            self.assertFalse(ship_check["ok"], f"expected ship model routing check to fail: {ship_check}")
            self.assertTrue(
                any("model_family" in e and "{{" in e for e in ship_check.get("errors", [])),
                f"expected an unresolved-placeholder error naming model_family, got: {ship_check.get('errors')}",
            )
            self.assertTrue(_report_has_failures(report))

    def test_verify_workspace_allows_empty_model_provider_field(self) -> None:
        """P-013.5 review-fix: an empty model_provider must PASS, not fail.
        The installer variable table's TIER_2_PROVIDER/TIER_3_PROVIDER (and
        their stage/ship fallbacks) default to empty, so a schema-valid,
        legacy, or default install can legitimately render an empty
        model_provider. Requiring it non-empty regressed those installs
        (found via Copilot review of PR #276) -- model_provider is optional;
        only model_family is required non-empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace, autoharness_home, stage_provider=""
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            stage_check = targeted_checks["stage_model_routing_fields"]
            self.assertTrue(stage_check["ok"], f"expected empty provider to pass: {stage_check}")

    def test_verify_workspace_flags_unresolved_model_provider_placeholder(self) -> None:
        """P-013.5 fail-closed: model_provider is optional (may be empty),
        but an unresolved {{...}} placeholder in it still indicates a broken
        install and must fail."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace, autoharness_home, stage_provider="{{STAGE_PROVIDER}}"
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            stage_check = targeted_checks["stage_model_routing_fields"]
            self.assertFalse(stage_check["ok"])
            self.assertTrue(
                any("model_provider" in e for e in stage_check.get("errors", [])),
                f"expected a model_provider error, got: {stage_check.get('errors')}",
            )

    def test_verify_workspace_flags_non_string_model_family(self) -> None:
        """P-013.5 fail-closed (Copilot review, PR #276): a structurally
        invalid model_family value (boolean, number, list, mapping) reaches
        neither the old None-check nor the old empty-string check and would
        silently pass. Requiring an actual string type closes that gap."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(workspace, autoharness_home)
            (workspace / ".github" / "agents" / "_stage.agent.md").write_text(
                "---\n"
                "name: _Stage\n"
                "max_subagent_tier: 3\n"
                'reasoning_effort: "high"\n'
                'model_provider: "anthropic"\n'
                "model_family: false\n"
                "---\n\n"
                "# Stage\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            stage_check = targeted_checks["stage_model_routing_fields"]
            self.assertFalse(stage_check["ok"])
            self.assertTrue(
                any("model_family" in e for e in stage_check.get("errors", [])),
                f"expected a model_family error, got: {stage_check.get('errors')}",
            )
            self.assertTrue(_report_has_failures(report))

    def test_verify_workspace_flags_non_string_model_provider(self) -> None:
        """P-013.5 fail-closed (Copilot review, PR #276): model_provider must
        be a string when present, even though it may be empty/absent. A
        structurally invalid value (number, list, mapping) must be flagged,
        not silently ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(workspace, autoharness_home)
            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
                "---\n"
                "name: _Ship\n"
                "max_subagent_tier: 2\n"
                'reasoning_effort: "high"\n'
                "model_provider: 42\n"
                'model_family: "claude-sonnet-5"\n'
                "---\n\n"
                "# Ship\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            ship_check = targeted_checks["ship_model_routing_fields"]
            self.assertFalse(ship_check["ok"])
            self.assertTrue(
                any("model_provider" in e for e in ship_check.get("errors", [])),
                f"expected a model_provider error, got: {ship_check.get('errors')}",
            )
            self.assertTrue(_report_has_failures(report))

    def test_verify_workspace_model_routing_check_fails_closed_on_non_mapping_frontmatter(self) -> None:
        """P-013.5 fail-closed: yaml.safe_load() can return a list, scalar, or
        boolean for syntactically valid but structurally invalid frontmatter.
        The check must report a clean targeted-check failure, not crash with
        AttributeError (found via Copilot review of PR #276)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(workspace, autoharness_home)
            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
                "---\n- just\n- a\n- list\n---\n\n# Ship\n",
                encoding="utf-8",
            )

            # Must not raise.
            report = verify_workspace(workspace, autoharness_home)

            ship_check = report["targeted_checks"]["ship_model_routing_fields"]
            self.assertFalse(ship_check["ok"])
            self.assertTrue(
                any("mapping" in e for e in ship_check.get("errors", [])),
                f"expected a mapping-type error, got: {ship_check.get('errors')}",
            )

    def test_verify_workspace_checks_orchestrator_invocation_directive_present(self) -> None:
        """P-013.5 / T8: the installed Orchestrator must contain the
        invocation-time routing directive (role-route resolution + declare +
        ROUTING_DEGRADED fallback) referencing both stage and ship routes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(workspace, autoharness_home)

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("orchestrator_invocation_routing_directive", targeted_checks)
            self.assertTrue(targeted_checks["orchestrator_invocation_routing_directive"]["ok"])

    def test_verify_workspace_flags_missing_orchestrator_invocation_directive(self) -> None:
        """P-013.5 fail-closed: removing the routing directive from the
        installed Orchestrator must fail verification. Red before this task,
        green after."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(workspace, autoharness_home)
            # Overwrite with a definition that has no routing directive at all.
            (workspace / ".github" / "agents" / "_orchestrator.agent.md").write_text(
                "---\n"
                "name: _Orchestrator\n"
                "max_subagent_tier: 3\n"
                'reasoning_effort: "high"\n'
                'model_provider: "openai"\n'
                'model_family: "gpt-5.6-sol"\n'
                "---\n\n"
                "# Orchestrator\n\n"
                "### Step 1: Route to Stage\n\nInvoke the Stage subagent.\n\n"
                "### Step 2: Route to Ship\n\nInvoke the Ship subagent.\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("orchestrator_invocation_routing_directive", targeted_checks)
            self.assertFalse(targeted_checks["orchestrator_invocation_routing_directive"]["ok"])
            self.assertTrue(_report_has_failures(report))

    def test_verify_workspace_flags_invocation_directive_removed_but_summary_kept(self) -> None:
        """P-013.5 fail-closed (Copilot review, PR #276): the routing-directive
        check must not be satisfiable by a single "Model Routing" summary
        paragraph that mentions all four required tokens once each, when the
        actual per-step (Stage/Ship) invocation directives have been removed.
        Red before this fix (the whole-file must_contain check passed on the
        summary alone), green after (the check requires ROUTING_DEGRADED in
        the narrow window between the first stage and first ship mention)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(workspace, autoharness_home)
            # Delete the Step 1/Step 2 invocation directives entirely, leaving
            # only a summary sentence that mentions all four required tokens
            # (mirrors the real _orchestrator.agent.md's "Model Routing"
            # summary section, which legitimately restates the same tokens
            # for human readers after the per-step directives).
            (workspace / ".github" / "agents" / "_orchestrator.agent.md").write_text(
                "---\n"
                "name: _Orchestrator\n"
                "max_subagent_tier: 3\n"
                'reasoning_effort: "high"\n'
                'model_provider: "openai"\n'
                'model_family: "gpt-5.6-sol"\n'
                "---\n\n"
                "# Orchestrator\n\n"
                "### Step 1: Route to Stage\n\nInvoke the Stage subagent.\n\n"
                "### Step 2: Route to Ship\n\nInvoke the Ship subagent.\n\n"
                "## Model Routing\n\n"
                "**P-013.5**: Steps 1 and 2 above each resolve "
                "`config.model_routing.stage` / `config.model_routing.ship`, "
                "and this agent emits `ROUTING_DEGRADED` when the runtime "
                "cannot honor a per-invocation override.\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("orchestrator_invocation_routing_directive", targeted_checks)
            self.assertFalse(targeted_checks["orchestrator_invocation_routing_directive"]["ok"])
            self.assertTrue(
                targeted_checks["orchestrator_invocation_routing_directive"]["scoping_errors"]
            )
            self.assertTrue(_report_has_failures(report))


        from autoharness.verify_workspace import _add_role_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier2": {"model": "claude-sonnet-5", "model_family": "claude-sonnet-5"},
                "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
            }
        }
        _add_role_route_resolution_check(report, "role_route_resolution", config)
        check = report["targeted_checks"]["role_route_resolution"]
        self.assertTrue(check["ok"], f"expected fallback resolution to pass: {check}")
        self.assertEqual(check.get("errors", []), [])

    def test_role_route_resolution_helper_fails_when_unresolvable(self) -> None:
        """P-013.5 fail-closed: when neither the role route nor its tier
        fallback declares a model family, the route does not resolve."""
        from autoharness.verify_workspace import _add_role_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                # tier3 present but declares no usable model identity, and no
                # stage override either — stage cannot resolve to any model.
                "tier3": {},
            }
        }
        _add_role_route_resolution_check(report, "role_route_resolution", config)
        check = report["targeted_checks"]["role_route_resolution"]
        self.assertFalse(check["ok"], f"expected unresolvable stage route to fail: {check}")
        self.assertTrue(
            any("stage" in e for e in check.get("errors", [])),
            f"expected an error naming the stage role, got: {check.get('errors')}",
        )

    def test_verify_workspace_flags_role_route_resolution_failure_end_to_end(self) -> None:
        """P-013.5 fail-closed, end to end: a declared config with an
        unresolvable ship role route must fail overall verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace,
                autoharness_home,
                model_routing={
                    "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
                    # Explicit opt-in to ship role routing (key present) with
                    # no override and tier2 deliberately absent -> ship role
                    # route cannot resolve to any model.
                    "ship": {},
                },
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("role_route_resolution", targeted_checks)
            self.assertFalse(targeted_checks["role_route_resolution"]["ok"])
            self.assertTrue(_report_has_failures(report))

    def test_verify_workspace_skips_role_route_resolution_for_partial_legacy_config(self) -> None:
        """P-013.5 fail-closed does not regress pre-existing, schema-valid
        configs that never opted into role routing. A model_routing block
        that only declares tier1 (or is empty) has not adopted stage/ship
        routing and must not register a role_route_resolution failure --
        found via adversarial review of the initial gate, which fired on any
        non-empty model_routing dict."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace,
                autoharness_home,
                model_routing={"tier1": "gpt-5.4-mini"},
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertNotIn("role_route_resolution", report["targeted_checks"])

    def test_verify_workspace_skips_role_route_resolution_for_empty_model_routing(self) -> None:
        """Same regression guard as above for an empty model_routing block."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace, autoharness_home, model_routing={}
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertNotIn("role_route_resolution", report["targeted_checks"])

    def test_verify_workspace_runs_role_route_resolution_when_tier2_and_tier3_present(self) -> None:
        """When a config declares the full tier2/tier3 fallback foundation
        (even without an explicit stage/ship override), the role-route
        resolution check still runs and passes via fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace,
                autoharness_home,
                model_routing={
                    "tier2": {"model": "claude-sonnet-5", "model_family": "claude-sonnet-5"},
                    "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
                },
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("role_route_resolution", targeted_checks)
            self.assertTrue(targeted_checks["role_route_resolution"]["ok"])

    # -- P-013.6: escalation route resolution (106.007-T / 106.008-T) --

    def test_escalation_route_resolution_helper_passes_via_tier3_fallback(self) -> None:
        """P-013.6: with no explicit model_routing.escalation declared, the
        escalation route resolves via fallback to model_routing.tier3, and no
        role route is declared so there is nothing to collide with."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
            }
        }
        _add_escalation_route_resolution_check(report, "escalation_route_resolution", config)
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertTrue(check["ok"], f"expected tier3-fallback resolution to pass: {check}")
        self.assertEqual(check.get("errors", []), [])
        self.assertEqual(check["resolved_escalation_family"], "claude-opus-4.8")
        self.assertEqual(check["same_route_roles"], [])

    def test_escalation_route_resolution_helper_fails_when_unresolvable(self) -> None:
        """P-013.6 fail-closed: an explicitly declared but empty escalation
        route, with no tier3 fallback, does not resolve to any model_family."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {"model_routing": {"escalation": {}}}
        _add_escalation_route_resolution_check(report, "escalation_route_resolution", config)
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertFalse(check["ok"], f"expected unresolvable escalation route to fail: {check}")
        self.assertTrue(
            any("escalation" in e for e in check.get("errors", [])),
            f"expected an error naming the escalation route, got: {check.get('errors')}",
        )

    def test_escalation_route_resolution_helper_flags_same_route_as_degraded(self) -> None:
        """P-013.6 / Copilot staging finding C1: when the resolved escalation
        model_family is identical to a declared role route's resolved
        model_family (Stage's explicit route equals tier3, and no distinct
        escalation route is declared), the auto-escalation attempt would be a
        same-route no-op -- this must fail as ESCALATION_DEGRADED, not pass
        silently."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
                "stage": {
                    "model": "claude-opus-4.8",
                    "model_family": "claude-opus-4.8",
                    "model_provider": "anthropic",
                    "reasoning_effort": "high",
                },
                # No explicit escalation route -> resolves via tier3 fallback,
                # landing on the exact same model_family as stage's explicit
                # route.
            }
        }
        _add_escalation_route_resolution_check(report, "escalation_route_resolution", config)
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertFalse(check["ok"], f"expected same-route escalation to fail: {check}")
        self.assertIn("stage", check["same_route_roles"])
        self.assertTrue(
            any("ESCALATION_DEGRADED" in e for e in check["errors"]),
            f"expected an ESCALATION_DEGRADED error, got: {check['errors']}",
        )

    def test_escalation_route_resolution_helper_flags_installed_agent_without_override_as_degraded(
        self,
    ) -> None:
        """Copilot review finding (PR #284): a role with NO explicit override
        key in model_routing at all must still be compared for same-route
        collision when its corresponding pipeline agent is installed --
        previously `if role not in model_routing: continue` skipped this
        entirely. Here Stage has no `stage` key, but stage_installed=True, so
        Stage's live P-013.5 fallback (tier3) must be compared against
        escalation's own tier3 fallback and correctly flagged."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
                # No explicit "stage" or "escalation" key -- both resolve via
                # tier3 fallback and therefore collide.
            }
        }
        _add_escalation_route_resolution_check(
            report,
            "escalation_route_resolution",
            config,
            stage_installed=True,
            ship_installed=False,
        )
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertFalse(
            check["ok"], f"expected installed-agent fallback collision to fail: {check}"
        )
        self.assertIn("stage", check["same_route_roles"])

    def test_escalation_route_resolution_helper_ignores_uninstalled_agent_without_override(
        self,
    ) -> None:
        """The converse of the above: when neither stage_installed nor
        ship_installed is True and neither role has an explicit override key,
        no role is in scope for the same-route comparison, so a tier3-only
        escalation fallback resolves cleanly with no collision."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
            }
        }
        _add_escalation_route_resolution_check(
            report,
            "escalation_route_resolution",
            config,
            stage_installed=False,
            ship_installed=False,
        )
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertTrue(check["ok"], f"expected no collision when neither agent installed: {check}")
        self.assertEqual(check["same_route_roles"], [])

    def test_escalation_route_resolution_helper_passes_with_distinct_route(self) -> None:
        """A distinct, explicitly-declared escalation route with a different
        model_family than any declared role route resolves cleanly and is not
        flagged as same-route degraded."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
                "stage": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
                "ship": {"model": "claude-sonnet-5", "model_family": "claude-sonnet-5"},
                "escalation": {
                    "model": "gpt-5.6-sol",
                    "model_family": "gpt-5.6-sol",
                    "model_provider": "openai",
                    "reasoning_effort": "high",
                },
            }
        }
        _add_escalation_route_resolution_check(report, "escalation_route_resolution", config)
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertTrue(check["ok"], f"expected distinct escalation route to pass: {check}")
        self.assertEqual(check["same_route_roles"], [])
        self.assertEqual(check["resolved_escalation_provider"], "openai")

    # -- F02FD596: nested per-role escalation hierarchy (113.002-T) --

    def test_escalation_route_resolution_helper_fails_closed_on_both_present(self) -> None:
        """H2: a legacy flat model_routing.escalation coexisting with any
        nested <role>.escalation is AMBIGUOUS and must fail closed -- never
        auto-pick a winner."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": "claude-opus-5",
                "escalation": {"model_family": "gpt-5.6-sol", "model_provider": "openai"},
                "stage": {
                    "model_family": "claude-opus-5",
                    "escalation": {"model_family": "claude-sonnet-5"},
                },
            }
        }
        _add_escalation_route_resolution_check(report, "escalation_route_resolution", config)
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertFalse(check["ok"], f"expected both-present ambiguity to fail closed: {check}")
        self.assertTrue(check.get("ambiguous"))
        self.assertTrue(
            any("AMBIGUOUS_ESCALATION_CONFIG" in e for e in check["errors"]),
            f"expected an AMBIGUOUS_ESCALATION_CONFIG error, got: {check['errors']}",
        )

    def test_escalation_route_resolution_helper_ignores_empty_flat_alongside_nested(self) -> None:
        """An empty flat `escalation: {}` (no fields set) does not count as
        'present' for the both-present ambiguity check -- only a nested
        override with a genuinely distinct route matters here."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": "claude-opus-5",
                "escalation": {},
                "stage": {
                    "model_family": "claude-opus-5",
                    "escalation": {"model_family": "claude-sonnet-5"},
                },
            }
        }
        _add_escalation_route_resolution_check(report, "escalation_route_resolution", config)
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertFalse(check.get("ambiguous"))
        self.assertTrue(check["ok"], f"expected empty flat + nested to resolve cleanly: {check}")
        self.assertEqual(check["per_role"]["stage"]["source"], "nested")
        self.assertEqual(check["per_role"]["stage"]["resolved_family"], "claude-sonnet-5")

    def test_escalation_route_resolution_helper_nested_per_field_fallback_to_tier3(self) -> None:
        """H4: a nested <role>.escalation that declares only some fields
        falls back per-field to model_routing.tier3 for the missing fields --
        NEVER to the legacy flat route (there is none declared here, but the
        point is the fallback target, not merely its absence)."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": {
                    "model": "claude-opus-5",
                    "model_family": "claude-opus-5",
                    "model_provider": "anthropic",
                    "reasoning_effort": "high",
                },
                "ship": {
                    "model_family": "claude-sonnet-5",
                    # Nested escalation declares only model_family -- provider
                    # and reasoning_effort must fall back per-field to tier3.
                    "escalation": {"model_family": "claude-opus-5"},
                },
            }
        }
        _add_escalation_route_resolution_check(
            report, "escalation_route_resolution", config, ship_installed=True
        )
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertTrue(check["ok"], f"expected nested per-field fallback to resolve: {check}")
        ship_result = check["per_role"]["ship"]
        self.assertEqual(ship_result["source"], "nested")
        self.assertEqual(ship_result["resolved_family"], "claude-opus-5")
        self.assertEqual(ship_result["resolved_provider"], "anthropic")
        self.assertEqual(ship_result["resolved_reasoning_effort"], "high")

    def test_escalation_route_resolution_helper_role_scoped_nested_distinct_routes(self) -> None:
        """H3: role-scoped ESCALATION_DEGRADED comparison -- with distinct
        nested escalation routes per role, Stage's own nested escalation must
        be compared only against Stage's own role route (not Ship's), and
        vice versa. Here Stage's nested escalation collides with its own
        route (degraded) while Ship's distinct nested escalation does not."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": "claude-opus-5",
                "tier2": "claude-sonnet-5",
                "stage": {
                    "model_family": "claude-opus-5",
                    # Same-route no-op: Stage's own nested escalation equals
                    # Stage's own role route.
                    "escalation": {"model_family": "claude-opus-5"},
                },
                "ship": {
                    "model_family": "claude-sonnet-5",
                    # Distinct: Ship's nested escalation differs from Ship's
                    # own route.
                    "escalation": {"model_family": "claude-opus-5"},
                },
            }
        }
        _add_escalation_route_resolution_check(report, "escalation_route_resolution", config)
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertFalse(check["ok"], f"expected Stage same-route degradation to fail: {check}")
        self.assertEqual(check["same_route_roles"], ["stage"])
        self.assertTrue(check["per_role"]["stage"]["escalation_degraded"])
        self.assertFalse(check["per_role"]["ship"]["escalation_degraded"])
        self.assertEqual(check["per_role"]["ship"]["resolved_family"], "claude-opus-5")

    def test_escalation_route_resolution_helper_deprecated_flat_flagged_when_used(self) -> None:
        """A role with no nested override that falls back to the legacy flat
        route is recorded as using the deprecated path (informational, not a
        failure)."""
        from autoharness.verify_workspace import _add_escalation_route_resolution_check

        report: dict = {"targeted_checks": {}}
        config = {
            "model_routing": {
                "tier3": "claude-opus-5",
                "stage": {"model_family": "claude-opus-5"},
                "escalation": {"model_family": "gpt-5.6-sol", "model_provider": "openai"},
            }
        }
        _add_escalation_route_resolution_check(report, "escalation_route_resolution", config)
        check = report["targeted_checks"]["escalation_route_resolution"]
        self.assertTrue(check["ok"], f"expected legacy flat fallback to resolve cleanly: {check}")
        self.assertTrue(check["deprecated_flat_in_use"])
        self.assertEqual(check["per_role"]["stage"]["source"], "legacy_flat")

    def test_verify_workspace_flags_escalation_route_resolution_failure_end_to_end(self) -> None:
        """P-013.6 fail-closed, end to end: an explicitly declared but
        unresolvable escalation route must fail overall verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace,
                autoharness_home,
                # No tier3 fallback declared -- an explicitly empty escalation
                # route has nothing to resolve against and must fail closed.
                model_routing={"escalation": {}},
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("escalation_route_resolution", targeted_checks)
            self.assertFalse(targeted_checks["escalation_route_resolution"]["ok"])
            self.assertTrue(_report_has_failures(report))

    def test_verify_workspace_skips_escalation_route_resolution_for_partial_legacy_config(
        self,
    ) -> None:
        """Same regression guard as role_route_resolution: a model_routing
        block that never opted into escalation or role routing (e.g.
        tier1-only) must not register an escalation_route_resolution
        failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace,
                autoharness_home,
                model_routing={"tier1": "gpt-5.4-mini"},
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertNotIn("escalation_route_resolution", report["targeted_checks"])

    def test_verify_workspace_runs_escalation_route_resolution_when_tier2_and_tier3_present(
        self,
    ) -> None:
        """When a config declares the full tier2/tier3 fallback foundation
        (even without an explicit escalation/stage/ship override), the
        escalation-route resolution check still runs. Fail-closed regression
        (Copilot review finding): the shared fixture installs both pipeline
        agents, so a Stage/Ship agent with no explicit override still
        live-adopts its P-013.5 fallback route (tier3/tier2) -- here Stage's
        fallback route (tier3) resolves to the same model_family as
        escalation's own tier3 fallback, so this must now correctly fail
        closed as ESCALATION_DEGRADED rather than silently pass."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace,
                autoharness_home,
                model_routing={
                    "tier2": {"model": "claude-sonnet-5", "model_family": "claude-sonnet-5"},
                    "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
                },
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("escalation_route_resolution", targeted_checks)
            check = targeted_checks["escalation_route_resolution"]
            self.assertFalse(check["ok"], f"expected same-route collision to fail closed: {check}")
            self.assertIn("stage", check["same_route_roles"])

    def test_verify_workspace_passes_escalation_route_resolution_with_distinct_route(
        self,
    ) -> None:
        """Same tier2/tier3 foundation as above, but with an explicit,
        distinct model_routing.escalation override -- the check runs (per
        the tier2/tier3 opt-in gate) and passes because escalation resolves
        to a model_family distinct from both installed agents' fallback
        routes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(
                workspace,
                autoharness_home,
                model_routing={
                    "tier2": {"model": "claude-sonnet-5", "model_family": "claude-sonnet-5"},
                    "tier3": {"model": "claude-opus-4.8", "model_family": "claude-opus-4.8"},
                    "escalation": {"model": "gpt-5.6-sol", "model_family": "gpt-5.6-sol"},
                },
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("escalation_route_resolution", targeted_checks)
            check = targeted_checks["escalation_route_resolution"]
            self.assertTrue(check["ok"], f"expected distinct escalation route to pass: {check}")
            self.assertEqual(check["same_route_roles"], [])

    # -- P-013.6: escalation-directive presence (106.007-T / 106.008-T) --

    def test_escalation_directive_check_skipped_when_neither_agent_installed(self) -> None:
        """Gated entirely on file existence: a workspace with neither
        _stage.agent.md nor _ship.agent.md installed must not register the
        escalation_directive_present check at all."""
        from autoharness.verify_workspace import _add_escalation_directive_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            report: dict = {"targeted_checks": {}}
            _add_escalation_directive_check(report, "escalation_directive_present", workspace_path)
            self.assertNotIn("escalation_directive_present", report["targeted_checks"])

    def test_escalation_directive_check_fails_when_directive_tokens_missing(self) -> None:
        """When _stage.agent.md / _ship.agent.md are installed but lack the
        P-013.6 / ESCALATION_DEGRADED tokens, and the escalation-protocol
        instruction is not installed, the check fails naming both gaps."""
        from autoharness.verify_workspace import _add_escalation_directive_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "_stage.agent.md").write_text("# Stage\n", encoding="utf-8")
            (agents_dir / "_ship.agent.md").write_text("# Ship\n", encoding="utf-8")

            report: dict = {"targeted_checks": {}}
            _add_escalation_directive_check(report, "escalation_directive_present", workspace_path)
            check = report["targeted_checks"]["escalation_directive_present"]
            self.assertFalse(check["ok"])
            self.assertTrue(any("stage" in e for e in check["errors"]))
            self.assertTrue(any("ship" in e for e in check["errors"]))
            self.assertTrue(any("escalation-protocol.instructions.md" in e for e in check["errors"]))

    def test_escalation_directive_check_fails_on_bare_token_mention_without_real_directive(
        self,
    ) -> None:
        """Fail-closed regression (Copilot review finding): a one-line file
        that only incidentally mentions the two bare tokens `P-013.6` and
        `ESCALATION_DEGRADED` -- with no compile/resolve/re-attempt/handoff
        directive and no reference to the shared instruction -- must NOT
        pass. Stable markers (section heading, shared instruction reference,
        required-action phrases) are required in addition to the bare
        tokens."""
        from autoharness.verify_workspace import _add_escalation_directive_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            # Exactly the shape the prior (pre-fix) check would have blessed:
            # bare token mentions with no real directive content.
            (agents_dir / "_ship.agent.md").write_text(
                "# Ship\n\nP-013.6 auto-escalation: emits ESCALATION_DEGRADED "
                "when the escalation route is unavailable or same-route.\n",
                encoding="utf-8",
            )
            instructions_dir = workspace_path / ".github" / "instructions"
            instructions_dir.mkdir(parents=True, exist_ok=True)
            (instructions_dir / "escalation-protocol.instructions.md").write_text(
                "---\nname: escalation-protocol\n---\n\n# Escalation Protocol\n",
                encoding="utf-8",
            )

            report: dict = {"targeted_checks": {}}
            _add_escalation_directive_check(report, "escalation_directive_present", workspace_path)
            check = report["targeted_checks"]["escalation_directive_present"]
            self.assertFalse(
                check["ok"],
                f"expected a bare-token-only file (no real directive) to fail: {check}",
            )
            self.assertTrue(any("ship" in e for e in check["errors"]))

    def test_escalation_directive_check_passes_with_only_ship_installed(self) -> None:
        """Either-agent install condition: when only _ship.agent.md is
        installed (no _stage.agent.md), the check evaluates ship alone and
        passes when ship carries the directive tokens and the instruction is
        installed."""
        from autoharness.verify_workspace import _add_escalation_directive_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "_ship.agent.md").write_text(
                "# Ship\n\n"
                "### Escalation Protocol — Consecutive Task Failures\n\n"
                "Upon 3 consecutive task failures, follow the auto-escalation "
                "directive below (P-013.6, `escalation-protocol.instructions.md`):\n\n"
                "1. Compile the escalation payload.\n"
                "2. Resolve the escalation route.\n"
                "3. Same-route guard: treat a same-route resolution as "
                "`ESCALATION_DEGRADED`.\n"
                "4. Re-attempt at the resolved route; if it also fails, "
                "**hand off** the compiled payload to engram.\n",
                encoding="utf-8",
            )
            instructions_dir = workspace_path / ".github" / "instructions"
            instructions_dir.mkdir(parents=True, exist_ok=True)
            (instructions_dir / "escalation-protocol.instructions.md").write_text(
                "---\nname: escalation-protocol\n---\n\n# Escalation Protocol\n",
                encoding="utf-8",
            )

            report: dict = {"targeted_checks": {}}
            _add_escalation_directive_check(report, "escalation_directive_present", workspace_path)
            check = report["targeted_checks"]["escalation_directive_present"]
            self.assertTrue(check["ok"], f"expected ship-only install to pass: {check}")
            self.assertFalse(check["stage_present"])
            self.assertTrue(check["ship_present"])

    def test_verify_workspace_flags_escalation_directive_failure_end_to_end(self) -> None:
        """End to end: the shared minimal fixture installs _stage/_ship
        agents without the P-013.6 directive tokens and without the
        escalation-protocol instruction -- verify_workspace must surface this
        as a targeted-check failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(workspace, autoharness_home)

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("escalation_directive_present", targeted_checks)
            self.assertFalse(targeted_checks["escalation_directive_present"]["ok"])
            self.assertTrue(_report_has_failures(report))

    def test_verify_workspace_passes_escalation_directive_when_fully_installed(self) -> None:
        """End to end: once both agents carry the directive tokens and the
        escalation-protocol instruction is installed, the targeted check
        passes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            workspace = root / "workspace"
            self._write_minimal_verify_workspace_fixture(workspace, autoharness_home)

            directive_note = (
                "\n\n### Escalation Protocol — Consecutive Task Failures\n\n"
                "Upon 3 consecutive task failures, follow the auto-escalation "
                "directive below (P-013.6, `escalation-protocol.instructions.md`):\n\n"
                "1. Compile the escalation payload.\n"
                "2. Resolve the escalation route.\n"
                "3. Same-route guard: treat a same-route resolution as "
                "`ESCALATION_DEGRADED`.\n"
                "4. Re-attempt at the resolved route; if it also fails, "
                "**hand off** the compiled payload to engram.\n"
            )
            for agent_file in ("_stage.agent.md", "_ship.agent.md"):
                agent_path = workspace / ".github" / "agents" / agent_file
                agent_path.write_text(
                    agent_path.read_text(encoding="utf-8") + directive_note, encoding="utf-8"
                )
            instructions_dir = workspace / ".github" / "instructions"
            instructions_dir.mkdir(parents=True, exist_ok=True)
            (instructions_dir / "escalation-protocol.instructions.md").write_text(
                "---\nname: escalation-protocol\n---\n\n# Escalation Protocol\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertIn("escalation_directive_present", targeted_checks)
            self.assertTrue(targeted_checks["escalation_directive_present"]["ok"])

    def test_session_start_reload_check_skipped_when_orchestrator_not_installed(self) -> None:
        """Gated entirely on the Orchestrator agent file's existence: a
        workspace without _orchestrator.agent.md must not register the
        session_start_reload_directive check at all."""
        from autoharness.verify_workspace import _add_session_start_reload_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            report: dict = {"targeted_checks": {}}
            _add_session_start_reload_check(
                report, "session_start_reload_directive", workspace_path
            )
            self.assertNotIn("session_start_reload_directive", report["targeted_checks"])

    def test_session_start_reload_check_fails_when_directive_tokens_missing(self) -> None:
        """When _orchestrator.agent.md is installed but lacks the
        session-start dynamic reload (E8B5B3C5/H6) directive tokens, the
        check fails naming the gap (113.004-T)."""
        from autoharness.verify_workspace import _add_session_start_reload_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "_orchestrator.agent.md").write_text(
                "# Orchestrator\n", encoding="utf-8"
            )

            report: dict = {"targeted_checks": {}}
            _add_session_start_reload_check(
                report, "session_start_reload_directive", workspace_path
            )
            check = report["targeted_checks"]["session_start_reload_directive"]
            self.assertFalse(check["ok"])
            self.assertTrue(any("Session-Start Dynamic Reload" in e for e in check["errors"]))

    def test_session_start_reload_check_passes_when_directive_present(self) -> None:
        """When _orchestrator.agent.md carries the full session-start dynamic
        reload directive (fresh re-read, schema validation, fail-closed
        halt), the check passes."""
        from autoharness.verify_workspace import _add_session_start_reload_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "_orchestrator.agent.md").write_text(
                "# Orchestrator\n\n"
                "## Model Routing\n\n"
                "**Session-Start Dynamic Reload (E8B5B3C5)**: every session "
                "re-reads config fresh from disk and validates it against "
                "schema (H6) before resolving routes. If invalid or missing, "
                "HALT to the operator rather than continuing on stale routes.\n",
                encoding="utf-8",
            )

            report: dict = {"targeted_checks": {}}
            _add_session_start_reload_check(
                report, "session_start_reload_directive", workspace_path
            )
            check = report["targeted_checks"]["session_start_reload_directive"]
            self.assertTrue(check["ok"], f"expected directive-complete install to pass: {check}")

    def test_session_start_reload_check_fails_for_ship_only_bare_reference(self) -> None:
        """Copilot review finding (PR #316): Ship explicitly supports direct
        operator invocation without an installed Orchestrator, so a
        Ship-only install (no Orchestrator, no Stage) that merely
        cross-references the Orchestrator's H6 section -- without carrying
        its own self-contained fail-closed reload directive -- must FAIL
        this check, not silently pass because the Orchestrator file is
        absent."""
        from autoharness.verify_workspace import _add_session_start_reload_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "_ship.agent.md").write_text(
                "# Ship\n\nSee the Orchestrator's Session-Start Dynamic "
                "Reload (E8B5B3C5/H6/H7) section for the reload contract.\n",
                encoding="utf-8",
            )

            report: dict = {"targeted_checks": {}}
            _add_session_start_reload_check(
                report, "session_start_reload_directive", workspace_path
            )
            check = report["targeted_checks"]["session_start_reload_directive"]
            self.assertFalse(
                check["ok"],
                f"expected Ship-only bare cross-reference to fail: {check}",
            )
            self.assertTrue(any("ship" in e for e in check["errors"]))

    def test_session_start_reload_check_passes_for_ship_only_self_contained_directive(self) -> None:
        """A Ship-only install (no Orchestrator) that carries its own
        self-contained H6 fail-closed reload directive (fresh re-read,
        schema validation, HALT on stale/invalid config) passes independently
        of whether the Orchestrator is installed."""
        from autoharness.verify_workspace import _add_session_start_reload_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "_ship.agent.md").write_text(
                "# Ship\n\n**Session-Start Dynamic Reload (H6) -- "
                "self-contained for direct invocation**: Ship supports being "
                "invoked directly without an installed Orchestrator. When "
                "invoked this way, Ship independently re-reads config fresh "
                "at the start of the session, validates it against schema "
                "before resolving any route, and HALTs to the operator on "
                "invalid, missing, or schema-failing config (E8B5B3C5) -- "
                "Ship MUST NOT continue on a stale/baked route.\n",
                encoding="utf-8",
            )

            report: dict = {"targeted_checks": {}}
            _add_session_start_reload_check(
                report, "session_start_reload_directive", workspace_path
            )
            check = report["targeted_checks"]["session_start_reload_directive"]
            self.assertTrue(
                check["ok"], f"expected Ship-only self-contained directive to pass: {check}"
            )

    def test_reload_propagation_check_skipped_when_no_pipeline_agents_installed(self) -> None:
        """Gated on file existence: a workspace with none of
        _orchestrator.agent.md / _stage.agent.md / _ship.agent.md installed
        must not register the reload_propagation_directive check at all."""
        from autoharness.verify_workspace import _add_reload_propagation_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            report: dict = {"targeted_checks": {}}
            _add_reload_propagation_check(
                report, "reload_propagation_directive", workspace_path
            )
            self.assertNotIn("reload_propagation_directive", report["targeted_checks"])

    def test_reload_propagation_check_fails_when_tokens_missing(self) -> None:
        """When the pipeline agents are installed but lack the H7 propagation
        tokens (inherited-skill propagation on the orchestrator, and the
        session-start-reload tie-in on stage/ship), the check fails naming
        each gap (113.005-T)."""
        from autoharness.verify_workspace import _add_reload_propagation_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "_orchestrator.agent.md").write_text(
                "# Orchestrator\n", encoding="utf-8"
            )
            (agents_dir / "_stage.agent.md").write_text("# Stage\n", encoding="utf-8")
            (agents_dir / "_ship.agent.md").write_text("# Ship\n", encoding="utf-8")

            report: dict = {"targeted_checks": {}}
            _add_reload_propagation_check(
                report, "reload_propagation_directive", workspace_path
            )
            check = report["targeted_checks"]["reload_propagation_directive"]
            self.assertFalse(check["ok"])
            self.assertTrue(any("orchestrator" in e for e in check["errors"]))
            self.assertTrue(any("stage" in e for e in check["errors"]))
            self.assertTrue(any("ship" in e for e in check["errors"]))

    def test_reload_propagation_check_fails_on_summary_only_reference(self) -> None:
        """Copilot review finding (PR #316): a bare marker phrase with no
        substantive propagation semantics near it -- e.g. a one-line
        "Propagate to inherited skills (H7): ..." summary, or "See the
        Session-Start Dynamic Reload (H7) section." with nothing else --
        must NOT satisfy this check. This is the exact minimal text the
        prior whole-file-substring implementation incorrectly accepted."""
        from autoharness.verify_workspace import _add_reload_propagation_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "_orchestrator.agent.md").write_text(
                "# Orchestrator\n\nPropagate to inherited skills (H7): ...\n",
                encoding="utf-8",
            )
            (agents_dir / "_stage.agent.md").write_text(
                "# Stage\n\nSee the Session-Start Dynamic Reload (H7) section.\n",
                encoding="utf-8",
            )
            (agents_dir / "_ship.agent.md").write_text(
                "# Ship\n\nSee the Session-Start Dynamic Reload (H7) section.\n",
                encoding="utf-8",
            )

            report: dict = {"targeted_checks": {}}
            _add_reload_propagation_check(
                report, "reload_propagation_directive", workspace_path
            )
            check = report["targeted_checks"]["reload_propagation_directive"]
            self.assertFalse(
                check["ok"],
                f"expected summary-only propagation references to fail: {check}",
            )
            self.assertTrue(any("orchestrator" in e for e in check["errors"]))
            self.assertTrue(any("stage" in e for e in check["errors"]))
            self.assertTrue(any("ship" in e for e in check["errors"]))

    def test_reload_propagation_check_passes_when_tokens_present(self) -> None:
        """When each agent carries its H7 propagation marker AND the
        substantive content in the scoped window near it (not just a bare
        summary reference), the check passes."""
        from autoharness.verify_workspace import _add_reload_propagation_check

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            agents_dir = workspace_path / ".github" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "_orchestrator.agent.md").write_text(
                "# Orchestrator\n\n**Propagate to inherited skills (H7)**: "
                "skills invoked by Stage/Ship at depth 2 have no independent "
                "model binding of their own -- they execute inside the "
                "depth-1 agent's own invocation; an independent per-skill "
                "divergence is itself a `ROUTING_DEGRADED` condition.\n",
                encoding="utf-8",
            )
            (agents_dir / "_stage.agent.md").write_text(
                "# Stage\n\nThis resolution always reads the freshly "
                "session-start-reloaded config -- see the Orchestrator's "
                "Session-Start Dynamic Reload (E8B5B3C5/H6/H7) section; a "
                "stale escalation directive surviving a reload is a defect.\n",
                encoding="utf-8",
            )
            (agents_dir / "_ship.agent.md").write_text(
                "# Ship\n\nThis resolution always reads the freshly "
                "session-start-reloaded config -- see the Orchestrator's "
                "Session-Start Dynamic Reload (E8B5B3C5/H6/H7) section; a "
                "stale escalation directive surviving a reload is a defect.\n",
                encoding="utf-8",
            )

            report: dict = {"targeted_checks": {}}
            _add_reload_propagation_check(
                report, "reload_propagation_directive", workspace_path
            )
            check = report["targeted_checks"]["reload_propagation_directive"]
            self.assertTrue(check["ok"], f"expected propagation-complete install to pass: {check}")

    def test_verify_workspace_flags_missing_release_closure_sequence_guidance(self) -> None:
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
                    "installed_at": "2026-05-07T00:00:00Z",
                    "autoharness_version": "1.5.0",
                    "profile_hash": "abc",
                    "primitives_installed": [4, 8],
                    "capability_packs": [],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
                "## Role Boundary (NON-NEGOTIABLE)\nP-010\nForbidden\n",
                encoding="utf-8",
            )
            (workspace / ".github" / "agents" / "_orchestrator.agent.md").write_text(
                "# Orchestrator\n",
                encoding="utf-8",
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertFalse(targeted_checks["ship_release_closure_sequence"]["ok"])
            self.assertFalse(targeted_checks["orchestrator_release_closure_sequence"]["ok"])

    def test_verify_workspace_checks_graphtor_docs_pack_assertions(self) -> None:
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
                    json.dumps(strict_schema), encoding="utf-8"
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema), encoding="utf-8"
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-05-09T00:00:00Z",
                    "autoharness_version": "1.0.0",
                    "profile_hash": "abc",
                    "primitives_installed": [1, 4],
                    "capability_packs": ["graphtor-docs"],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            # Write a graphtor-docs instruction file with all 8 required tool names
            (workspace / ".github" / "instructions" / "graphtor-docs.instructions.md").write_text(
                "search_local_docs\nsearch_semantic\nresearch_topic\ntraverse_doc_links\n"
                "list_sources\nget_chunk_by_id\nget_document\nget_status\n",
                encoding="utf-8",
            )
            # Write stage and ship agents with graphtor-docs weaving
            (workspace / ".github" / "agents" / "_stage.agent.md").write_text(
                "graphtor-docs\ngraphtor-docs.instructions.md\n", encoding="utf-8"
            )
            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
                "graphtor-docs\ngraphtor-docs.instructions.md\n", encoding="utf-8"
            )

            report = verify_workspace(workspace, autoharness_home)

            self.assertEqual(report["strict_schema_blockers"], [])
            self.assertEqual(report["blockers"], [])

            targeted_checks = report["targeted_checks"]
            self.assertTrue(targeted_checks["graphtor_docs_instruction"]["ok"])
            self.assertTrue(targeted_checks["graphtor_docs_stage_weaving"]["ok"])
            self.assertTrue(targeted_checks["graphtor_docs_ship_weaving"]["ok"])

    def test_verify_workspace_graphtor_docs_pack_assertions_fail_when_missing(self) -> None:
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
                    json.dumps(strict_schema), encoding="utf-8"
                )
            for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                    json.dumps(strict_schema), encoding="utf-8"
                )

            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-05-09T00:00:00Z",
                    "autoharness_version": "1.0.0",
                    "profile_hash": "abc",
                    "primitives_installed": [1, 4],
                    "capability_packs": ["graphtor-docs"],
                    "artifacts": [],
                },
            )
            _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
            _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

            # Instruction file exists but is missing tool names and agent weaving is absent
            (workspace / ".github" / "instructions" / "graphtor-docs.instructions.md").write_text(
                "This is a stub instruction file with no tool names.\n", encoding="utf-8"
            )
            (workspace / ".github" / "agents" / "_stage.agent.md").write_text(
                "# Stage\n\nNo graphtor mention here.\n", encoding="utf-8"
            )
            (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
                "# Ship\n\nNo graphtor mention here.\n", encoding="utf-8"
            )

            report = verify_workspace(workspace, autoharness_home)

            targeted_checks = report["targeted_checks"]
            self.assertFalse(targeted_checks["graphtor_docs_instruction"]["ok"])
            self.assertFalse(targeted_checks["graphtor_docs_stage_weaving"]["ok"])
            self.assertFalse(targeted_checks["graphtor_docs_ship_weaving"]["ok"])

    def test_verify_workspace_community_template_pass(self) -> None:
        """Community template installed correctly with matching checksum."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            ws = root / "workspace"

            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True)
            (ws / ".autoharness").mkdir(parents=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {"schema_version": {"type": "string", "const": "1.0.0"}},
            }
            for sname in ("harness-manifest.schema.json", "harness-config.schema.json", "workspace-profile.schema.json"):
                (autoharness_home / "schemas" / sname).write_text(json.dumps(strict_schema), encoding="utf-8")
            for sdir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / sdir / "1.0.0.schema.json").write_text(json.dumps(strict_schema), encoding="utf-8")

            ct_content = b"# Community template content\nSome useful instruction."
            ct_checksum = hashlib.sha256(ct_content).hexdigest()
            # Also create source .tmpl to satisfy upstream check
            tmpl_content = b"# Community template content\nSome useful instruction with {{VARIABLE}}."
            tmpl_checksum = hashlib.sha256(tmpl_content).hexdigest()
            tmpl_dir = autoharness_home / "templates" / "community" / "instructions"
            tmpl_dir.mkdir(parents=True)
            (tmpl_dir / "test.instructions.md.tmpl").write_bytes(tmpl_content)
            _write_yaml(ws / ".autoharness" / "harness-manifest.yaml", {
                "schema_version": "1.0.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "autoharness_version": "0.1.0",
                "profile_hash": "abc123",
                "primitives_installed": [1, 2],
                "artifacts": [],
                "community_templates": [{
                    "template_id": "test-instruction",
                    "template_path": "templates/community/instructions/test.instructions.md.tmpl",
                    "installed_path": ".github/instructions/test.instructions.md",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "installed_checksum": ct_checksum,
                    "source_checksum": tmpl_checksum,
                }],
            })
            _write_yaml(ws / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})

            ct_dir = ws / ".github" / "instructions"
            ct_dir.mkdir(parents=True)
            (ct_dir / "test.instructions.md").write_bytes(ct_content)

            report = verify_workspace(ws, autoharness_home)
            self.assertEqual(len(report["community_templates"]), 1)
            self.assertTrue(report["community_templates"][0]["ok"])
            self.assertTrue(report["community_templates"][0]["installed_checksum_ok"])
            self.assertFalse(report["community_templates"][0]["upstream_updated"])
            self.assertEqual(report["community_templates"][0]["template_id"], "test-instruction")

    def test_verify_workspace_community_template_upstream_updated(self) -> None:
        """Community template source .tmpl has been updated in autoharness_home."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            ws = root / "workspace"

            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True)
            (ws / ".autoharness").mkdir(parents=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {"schema_version": {"type": "string", "const": "1.0.0"}},
            }
            for sname in ("harness-manifest.schema.json", "harness-config.schema.json", "workspace-profile.schema.json"):
                (autoharness_home / "schemas" / sname).write_text(json.dumps(strict_schema), encoding="utf-8")
            for sdir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / sdir / "1.0.0.schema.json").write_text(json.dumps(strict_schema), encoding="utf-8")

            # Original .tmpl content and installed content at install time
            original_tmpl = b"# Original template with {{VARIABLE}}"
            original_tmpl_checksum = hashlib.sha256(original_tmpl).hexdigest()
            installed_content = b"# Original template with resolved_value"
            installed_checksum = hashlib.sha256(installed_content).hexdigest()
            # Updated source template in autoharness_home (upstream changed)
            updated_tmpl = b"# Updated template with {{VARIABLE}} and new guidance"
            tmpl_dir = autoharness_home / "templates" / "community" / "instructions"
            tmpl_dir.mkdir(parents=True)
            (tmpl_dir / "test.instructions.md.tmpl").write_bytes(updated_tmpl)

            _write_yaml(ws / ".autoharness" / "harness-manifest.yaml", {
                "schema_version": "1.0.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "autoharness_version": "0.1.0",
                "profile_hash": "abc123",
                "primitives_installed": [1, 2],
                "artifacts": [],
                "community_templates": [{
                    "template_id": "test-instruction",
                    "template_path": "templates/community/instructions/test.instructions.md.tmpl",
                    "installed_path": ".github/instructions/test.instructions.md",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "installed_checksum": installed_checksum,
                    "source_checksum": original_tmpl_checksum,
                }],
            })
            _write_yaml(ws / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})

            ct_dir = ws / ".github" / "instructions"
            ct_dir.mkdir(parents=True)
            (ct_dir / "test.instructions.md").write_bytes(installed_content)

            report = verify_workspace(ws, autoharness_home)
            self.assertEqual(len(report["community_templates"]), 1)
            self.assertFalse(report["community_templates"][0]["ok"])
            self.assertTrue(report["community_templates"][0]["installed_checksum_ok"])
            self.assertTrue(report["community_templates"][0]["upstream_updated"])
            self.assertEqual(report["community_templates"][0]["reason"], "upstream template updated")

    def test_verify_workspace_community_template_fail_missing(self) -> None:
        """Community template declared in manifest but file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            ws = root / "workspace"

            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True)
            (ws / ".autoharness").mkdir(parents=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {"schema_version": {"type": "string", "const": "1.0.0"}},
            }
            for sname in ("harness-manifest.schema.json", "harness-config.schema.json", "workspace-profile.schema.json"):
                (autoharness_home / "schemas" / sname).write_text(json.dumps(strict_schema), encoding="utf-8")
            for sdir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / sdir / "1.0.0.schema.json").write_text(json.dumps(strict_schema), encoding="utf-8")

            _write_yaml(ws / ".autoharness" / "harness-manifest.yaml", {
                "schema_version": "1.0.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "autoharness_version": "0.1.0",
                "profile_hash": "abc123",
                "primitives_installed": [1, 2],
                "artifacts": [],
                "community_templates": [{
                    "template_id": "missing-template",
                    "template_path": "templates/community/instructions/missing.instructions.md.tmpl",
                    "installed_path": ".github/instructions/missing.instructions.md",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "installed_checksum": "abc123",
                    "source_checksum": "def456",
                }],
            })
            _write_yaml(ws / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})

            report = verify_workspace(ws, autoharness_home)
            self.assertEqual(len(report["community_templates"]), 1)
            self.assertFalse(report["community_templates"][0]["ok"])
            self.assertEqual(report["community_templates"][0]["reason"], "missing file")

    def test_verify_workspace_community_template_fail_checksum(self) -> None:
        """Community template exists but content has been modified (checksum mismatch)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            ws = root / "workspace"

            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True)
            (ws / ".autoharness").mkdir(parents=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {"schema_version": {"type": "string", "const": "1.0.0"}},
            }
            for sname in ("harness-manifest.schema.json", "harness-config.schema.json", "workspace-profile.schema.json"):
                (autoharness_home / "schemas" / sname).write_text(json.dumps(strict_schema), encoding="utf-8")
            for sdir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / sdir / "1.0.0.schema.json").write_text(json.dumps(strict_schema), encoding="utf-8")

            _write_yaml(ws / ".autoharness" / "harness-manifest.yaml", {
                "schema_version": "1.0.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "autoharness_version": "0.1.0",
                "profile_hash": "abc123",
                "primitives_installed": [1, 2],
                "artifacts": [],
                "community_templates": [{
                    "template_id": "modified-template",
                    "template_path": "templates/community/instructions/test.instructions.md.tmpl",
                    "installed_path": ".github/instructions/test.instructions.md",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "installed_checksum": "original_checksum_that_wont_match",
                    "source_checksum": "source_checksum_value",
                }],
            })
            _write_yaml(ws / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})

            ct_dir = ws / ".github" / "instructions"
            ct_dir.mkdir(parents=True)
            (ct_dir / "test.instructions.md").write_text("Modified content", encoding="utf-8")

            report = verify_workspace(ws, autoharness_home)
            self.assertEqual(len(report["community_templates"]), 1)
            self.assertFalse(report["community_templates"][0]["ok"])
            self.assertEqual(report["community_templates"][0]["reason"], "checksum mismatch")

    def test_verify_workspace_agent_workspace_identity_pass(self) -> None:
        """Pipeline agents reference the resolved project name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            ws = root / "my-project"
            ws.mkdir()

            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True)
            (ws / ".autoharness").mkdir(parents=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {"schema_version": {"type": "string", "const": "1.0.0"}},
            }
            for sname in ("harness-manifest.schema.json", "harness-config.schema.json", "workspace-profile.schema.json"):
                (autoharness_home / "schemas" / sname).write_text(json.dumps(strict_schema), encoding="utf-8")
            for sdir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / sdir / "1.0.0.schema.json").write_text(json.dumps(strict_schema), encoding="utf-8")

            _write_yaml(ws / ".autoharness" / "harness-manifest.yaml", {
                "schema_version": "1.0.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "autoharness_version": "0.1.0",
                "profile_hash": "abc",
                "primitives_installed": [1, 4],
                "artifacts": [],
            })
            _write_yaml(ws / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})

            agents_dir = ws / ".github" / "agents"
            agents_dir.mkdir(parents=True)
            (agents_dir / "_orchestrator.agent.md").write_text(
                "You are the Orchestrator agent for the **my-project** repository.", encoding="utf-8"
            )
            (agents_dir / "_stage.agent.md").write_text(
                "You are the Stage agent for the **my-project** repository.", encoding="utf-8"
            )
            (agents_dir / "_ship.agent.md").write_text(
                "You are the Ship agent for the **my-project** repository.", encoding="utf-8"
            )

            report = verify_workspace(ws, autoharness_home)
            for key in ("orchestrator_workspace_identity", "stage_workspace_identity", "ship_workspace_identity"):
                self.assertIn(key, report["targeted_checks"])
                self.assertTrue(report["targeted_checks"][key]["ok"], f"{key} should pass")
                self.assertTrue(report["targeted_checks"][key]["has_project_name"])
                self.assertFalse(report["targeted_checks"][key]["has_unresolved_variable"])

    def test_verify_workspace_agent_workspace_identity_fail_unresolved(self) -> None:
        """Pipeline agent with unresolved {{PROJECT_NAME}} fails identity check."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home = root / "autoharness-home"
            ws = root / "my-project"
            ws.mkdir()

            (autoharness_home / "schemas" / "harness-manifest").mkdir(parents=True)
            (autoharness_home / "schemas" / "harness-config").mkdir(parents=True)
            (autoharness_home / "schemas" / "workspace-profile").mkdir(parents=True)
            (ws / ".autoharness").mkdir(parents=True)

            strict_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["schema_version"],
                "properties": {"schema_version": {"type": "string", "const": "1.0.0"}},
            }
            for sname in ("harness-manifest.schema.json", "harness-config.schema.json", "workspace-profile.schema.json"):
                (autoharness_home / "schemas" / sname).write_text(json.dumps(strict_schema), encoding="utf-8")
            for sdir in ("harness-manifest", "harness-config", "workspace-profile"):
                (autoharness_home / "schemas" / sdir / "1.0.0.schema.json").write_text(json.dumps(strict_schema), encoding="utf-8")

            _write_yaml(ws / ".autoharness" / "harness-manifest.yaml", {
                "schema_version": "1.0.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "autoharness_version": "0.1.0",
                "profile_hash": "abc",
                "primitives_installed": [1, 4],
                "artifacts": [],
            })
            _write_yaml(ws / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})

            agents_dir = ws / ".github" / "agents"
            agents_dir.mkdir(parents=True)
            (agents_dir / "_orchestrator.agent.md").write_text(
                "You are the Orchestrator agent for the **{{PROJECT_NAME}}** repository.", encoding="utf-8"
            )

            report = verify_workspace(ws, autoharness_home)
            check = report["targeted_checks"]["orchestrator_workspace_identity"]
            self.assertFalse(check["ok"])
            self.assertTrue(check["has_unresolved_variable"])


class PortabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _mk(self, rel: str, content: str) -> Path:
        p = self.ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def test_clean_artifact_produces_no_findings(self) -> None:
        self._mk(".github/agents/_stage.agent.md", "# Stage\n\nNo hardcoded paths here.\n")
        findings = _run_portability_scan(self.ws)
        self.assertEqual(findings, [])

    def test_hardcoded_user_home_path_detected(self) -> None:
        self._mk(".github/agents/_ship.agent.md", "# Ship\n\nRun: cp ~/.ssh/id_rsa .\n")
        findings = _run_portability_scan(self.ws)
        self.assertTrue(any(f["rule"] == "hardcoded_user_home" for f in findings))
        self.assertEqual(findings[0]["severity"], "P1")
        self.assertIn("path", findings[0])
        self.assertIn("line", findings[0])
        self.assertIn("match", findings[0])

    def test_local_agents_dir_detected(self) -> None:
        self._mk(".github/skills/custom/SKILL.md", "# Skill\n\nCopy files to .github/local-agents.\n")
        findings = _run_portability_scan(self.ws)
        self.assertTrue(any(f["rule"] == "local_agents_dir" for f in findings))

    def test_mcp_plugin_tool_name_detected(self) -> None:
        self._mk(".github/agents/_stage.agent.md", "# Stage\n\nCall mcp__plugin_backlogit__create_task here.\n")
        findings = _run_portability_scan(self.ws)
        self.assertTrue(any(f["rule"] == "mcp_plugin_tool_name" for f in findings))

    def test_hardcoded_ah_home_detected(self) -> None:
        self._mk(".github/agents/_stage.agent.md", "# Stage\n\nPath: ~/.autoharness/templates\n")
        findings = _run_portability_scan(self.ws)
        self.assertTrue(any(f["rule"] == "hardcoded_ah_home" for f in findings))

    def test_allow_listed_auto_tune_is_exempt(self) -> None:
        self._mk(
            ".github/agents/auto-tune.agent.md",
            "# Auto-Tune\n\nDefault: ~/.autoharness/\nSee also: ~/.config\n",
        )
        findings = _run_portability_scan(self.ws)
        self.assertFalse(any(f["path"].endswith("auto-tune.agent.md") for f in findings))

    def test_allow_listed_install_harness_is_exempt(self) -> None:
        self._mk(
            ".github/skills/install-harness/SKILL.md",
            "# Install\n\nPath: ~/.autoharness/\nCopy to .github/local-agents.\n",
        )
        findings = _run_portability_scan(self.ws)
        self.assertFalse(any("install-harness" in f["path"] for f in findings))

    def test_instructions_dir_is_scanned(self) -> None:
        self._mk(".github/instructions/custom.instructions.md", "# Custom\n\nPath: C:\\Users\\alice\\config\n")
        findings = _run_portability_scan(self.ws)
        self.assertTrue(any(f["rule"] == "hardcoded_user_home" for f in findings))

    def test_policies_dir_is_scanned(self) -> None:
        self._mk(".github/policies/custom.md", "# Policy\n\nRun from ~/.autoharness/scripts.\n")
        findings = _run_portability_scan(self.ws)
        self.assertTrue(any(f["rule"] == "hardcoded_ah_home" for f in findings))

    def test_one_finding_per_rule_per_file(self) -> None:
        """Each rule produces at most one finding per file even if the pattern matches multiple lines."""
        self._mk(
            ".github/agents/_ship.agent.md",
            "# Ship\n\nPath: ~/.ssh/key\nAlso: ~/.config/foo\n",
        )
        findings = _run_portability_scan(self.ws)
        home_findings = [f for f in findings if f["rule"] == "hardcoded_user_home"]
        self.assertEqual(len(home_findings), 1)

    def test_portability_findings_appear_in_report_warnings(self) -> None:
        """Portability P1 findings are surfaced as warnings in the full verify_workspace report."""
        autoharness_home = self.ws / "ah-home"
        workspace = self.ws / "workspace"
        (autoharness_home / "schemas").mkdir(parents=True)
        (workspace / ".autoharness").mkdir(parents=True)
        (workspace / ".github" / "agents").mkdir(parents=True)

        strict_schema: dict = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["schema_version"],
            "properties": {"schema_version": {"type": "string", "const": "1.0.0"}},
        }
        for schema_name in (
            "harness-manifest.schema.json",
            "harness-config.schema.json",
            "workspace-profile.schema.json",
        ):
            (autoharness_home / "schemas" / schema_name).write_text(
                json.dumps(strict_schema), encoding="utf-8"
            )
        for schema_dir in ("harness-manifest", "harness-config", "workspace-profile"):
            (autoharness_home / "schemas" / schema_dir).mkdir(parents=True)
            (autoharness_home / "schemas" / schema_dir / "1.0.0.schema.json").write_text(
                json.dumps(strict_schema), encoding="utf-8"
            )

        _write_yaml(
            workspace / ".autoharness" / "harness-manifest.yaml",
            {
                "schema_version": "1.0.0",
                "installed_at": "2026-05-07T00:00:00Z",
                "autoharness_version": "1.0.0",
                "profile_hash": "abc",
                "artifacts": [],
            },
        )
        _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
        _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})

        (workspace / ".github" / "agents" / "_ship.agent.md").write_text(
            "# Ship\n\nRun: cp ~/.ssh/id_rsa .\n", encoding="utf-8"
        )

        report = verify_workspace(workspace, autoharness_home)

        self.assertTrue(len(report["portability_findings"]) > 0)
        warning_kinds = [w.get("kind") for w in report["warnings"]]
        self.assertIn("portability-finding", warning_kinds)

    def test_dogfood_baseline_has_no_portability_findings(self) -> None:
        """The autoharness dogfood workspace produces no portability findings after allow-list is applied."""
        repo_root = Path(__file__).resolve().parents[1]
        findings = _run_portability_scan(repo_root)
        self.assertEqual(
            findings,
            [],
            msg=f"Unexpected portability findings in dogfood: {findings}",
        )

    # ------------------------------------------------------------------
    # Output path-placement contract (046-F / 046.001-T)
    # ------------------------------------------------------------------

    def _build_minimal_workspace_for_path_tests(
        self, root: Path
    ) -> tuple[Path, Path]:
        """Shared fixture: minimal workspace + autoharness_home for path-placement tests."""
        autoharness_home = root / "autoharness-home"
        workspace = root / "workspace"

        (autoharness_home / "templates" / "foundation").mkdir(parents=True, exist_ok=True)
        (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
        (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)

        schema = {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object"}
        for schema_name in (
            "harness-manifest.schema.json",
            "harness-config.schema.json",
            "workspace-profile.schema.json",
        ):
            (autoharness_home / "schemas" / schema_name).write_text(
                json.dumps(schema), encoding="utf-8"
            )

        (autoharness_home / "templates" / "foundation" / "AGENTS.md.tmpl").write_text(
            "# {{PROJECT_NAME}}\n", encoding="utf-8"
        )
        _write_yaml(
            workspace / ".autoharness" / "harness-manifest.yaml",
            {
                "schema_version": "1.0.0",
                "installed_at": "2026-04-24T00:00:00Z",
                "autoharness_version": "1.3.2",
                "profile_hash": "abc",
                "primitives_installed": [9],
                "capability_packs": [],
                "artifacts": [
                    {
                        "path": "AGENTS.md",
                        "primitive": 9,
                        "template": "templates/foundation/AGENTS.md.tmpl",
                        "checksum": "",
                    }
                ],
                "variables_used": {"PROJECT_NAME": "path-test-workspace"},
            },
        )
        _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
        _write_yaml(
            workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"}
        )
        (workspace / "AGENTS.md").write_text("# Path Test\n", encoding="utf-8")
        return autoharness_home, workspace

    def test_verify_workspace_reports_land_under_autoharness_staging_by_default(self) -> None:
        """When --staging-dir is omitted, reports must land under .autoharness/staging/, not workspace root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home, workspace = self._build_minimal_workspace_for_path_tests(root)

            # Call without explicit staging_dir — must default to .autoharness/staging/
            report = verify_workspace(workspace, autoharness_home)

            expected_staging = workspace / ".autoharness" / "staging"
            json_path = expected_staging / "verify-workspace-report.json"
            md_path = expected_staging / "verify-workspace-report.md"

            # Files must exist under .autoharness/staging/
            self.assertTrue(json_path.exists(), "JSON report must be under .autoharness/staging/")
            self.assertTrue(md_path.exists(), "Markdown report must be under .autoharness/staging/")

            # report dict must carry the correct paths
            self.assertEqual(
                Path(report["report_paths"]["json"]).resolve(),
                json_path.resolve(),
            )
            self.assertEqual(
                Path(report["report_paths"]["markdown"]).resolve(),
                md_path.resolve(),
            )

            # The staging_dir value in the report must match
            self.assertEqual(
                Path(report["staging_dir"]).resolve(),
                expected_staging.resolve(),
            )

            # Files must NOT exist at the workspace root
            self.assertFalse(
                (workspace / "verify-workspace-report.json").exists(),
                "JSON report must not appear at workspace root",
            )
            self.assertFalse(
                (workspace / "verify-workspace-report.md").exists(),
                "Markdown report must not appear at workspace root",
            )

    def test_verify_workspace_early_exit_reports_land_under_autoharness_staging(self) -> None:
        """Missing-manifest early exit must still write reports under .autoharness/staging/."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            autoharness_home = root / "autoharness-home"
            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)
            (workspace / ".autoharness").mkdir(parents=True, exist_ok=True)
            # Intentionally no harness-manifest.yaml → early exit path

            report = verify_workspace(workspace, autoharness_home)

            expected_staging = workspace / ".autoharness" / "staging"
            json_path = expected_staging / "verify-workspace-report.json"
            md_path = expected_staging / "verify-workspace-report.md"

            # Early exit must write to .autoharness/staging/
            self.assertTrue(json_path.exists(), "Early-exit JSON report must be under .autoharness/staging/")
            self.assertTrue(md_path.exists(), "Early-exit Markdown report must be under .autoharness/staging/")

            # report_paths must be populated (and match what's on disk)
            self.assertEqual(
                Path(report["report_paths"]["json"]).resolve(),
                json_path.resolve(),
            )
            self.assertEqual(
                Path(report["report_paths"]["markdown"]).resolve(),
                md_path.resolve(),
            )

            # The JSON on disk must include report_paths (written after populating it)
            written = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("report_paths", written, "On-disk JSON must include report_paths")
            self.assertEqual(
                Path(written["report_paths"]["json"]).resolve(),
                json_path.resolve(),
            )

            # Must have the missing-manifest blocker
            kinds = [b["kind"] for b in report["blockers"]]
            self.assertIn("missing-manifest", kinds)

    def test_verify_workspace_report_paths_in_json_on_disk_match_return_value(self) -> None:
        """report_paths in the on-disk JSON must match the dict returned to callers (no double-write drift)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            autoharness_home, workspace = self._build_minimal_workspace_for_path_tests(root)

            report = verify_workspace(workspace, autoharness_home)

            json_path = Path(report["report_paths"]["json"])
            written = json.loads(json_path.read_text(encoding="utf-8"))

            # The on-disk file must include report_paths
            self.assertIn("report_paths", written)
            self.assertEqual(
                Path(written["report_paths"]["json"]).resolve(),
                Path(report["report_paths"]["json"]).resolve(),
            )
            self.assertEqual(
                Path(written["report_paths"]["markdown"]).resolve(),
                Path(report["report_paths"]["markdown"]).resolve(),
            )

            # Confirm the written file contains the same staging_dir as the return value
            self.assertEqual(
                Path(written["staging_dir"]).resolve(),
                Path(report["staging_dir"]).resolve(),
            )

    def test_normalize_stage_path_prevents_path_escape(self) -> None:
        """_normalize_stage_path must contain all outputs within staging_dir.

        Covers Unix absolute paths, Windows drive-letter paths, parent-directory
        traversal, and degenerate/empty paths (046-F).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            staging = Path(temp_dir) / "staging"
            staging.mkdir()
            staging_resolved = staging.resolve()

            safe_cases = [
                "AGENTS.md",
                "subdir/file.txt",
                ".github/copilot-instructions.md",
                ".autoharness/config.yaml",
                "deep/nested/dir/file.md",
            ]
            for rel in safe_cases:
                result = _normalize_stage_path(staging, rel)
                self.assertTrue(
                    result.resolve().is_relative_to(staging_resolved),
                    f"Safe path should stay under staging_dir: {rel!r} → {result}",
                )

            # These must all be contained — not escape staging_dir
            escape_attempts = [
                "/etc/passwd",                          # Unix absolute
                "/absolute/path/to/file.txt",           # Unix absolute (no drive)
                "C:/Windows/System32/evil.dll",         # Windows absolute (forward slashes)
                "C:\\Windows\\System32\\evil.dll",      # Windows absolute (backslashes)
                "D:/secrets.txt",                       # Windows drive letter
                "foo/C:/Windows/evil.dll",             # Mid-path Windows drive anchor
                "foo/C:Windows/evil.dll",              # Mid-path drive-relative segment
                "\\\\?\\C:\\Windows\\evil.dll",        # Windows extended-length path
                "../../../etc/shadow",                  # Unix parent traversal
                "subdir/../../../../../../etc/hosts",   # Mixed traversal
                "../sibling/file.txt",                  # Parent traversal one level
            ]
            for rel in escape_attempts:
                result = _normalize_stage_path(staging, rel)
                self.assertTrue(
                    result.resolve().is_relative_to(staging_resolved),
                    f"Escape attempt must be contained: {rel!r} → {result}",
                )

            # Degenerate inputs must raise ValueError (would otherwise write to staging_dir itself)
            degenerate_cases = [
                "",         # empty string
                ".",        # current dir
                "..",       # parent only
                "../..",    # multiple parents
                "./",       # current dir with trailing slash
            ]
            for rel in degenerate_cases:
                with self.assertRaises(ValueError, msg=f"Degenerate path must raise: {rel!r}"):
                    _normalize_stage_path(staging, rel)


def _write_agent_file(directory: Path, filename: str, name: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(
        f"---\nname: {name}\nmax_subagent_tier: 2\n---\n\n# {name}\n",
        encoding="utf-8",
    )


def _write_agent_file_with_id(
    directory: Path, filename: str, name: str, agent_id: str
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(
        f"---\nname: {name}\nid: {agent_id}\nmax_subagent_tier: 2\n---\n\n# {name}\n",
        encoding="utf-8",
    )


class AgentIdentityMigrationTests(unittest.TestCase):
    def _index(self, proposals: list[dict]) -> dict[str, dict]:
        return {p["from_path"]: p for p in proposals}

    def test_detects_legacy_filenames_and_ignores_elective_and_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file(agents, "stage.agent.md", "Stage")
            _write_agent_file(agents, "ship.agent.md", "Ship")
            _write_agent_file(agents, "orchestrator.agent.md", "Orchestrator")
            # Elective and review agents must never be proposed for migration.
            _write_agent_file(agents, "auto-mergeinstall.agent.md", "Auto-MergeInstall")
            _write_agent_file(agents, "auto-tune.agent.md", "Auto-Tune")
            _write_agent_file(agents, "adversarial-review.agent.md", "Adversarial Reviewer")

            proposals = _scan_agent_identity_migrations(workspace, {})
            by_from = self._index(proposals)

            self.assertEqual(len(proposals), 3)
            self.assertEqual(
                by_from[".github/agents/stage.agent.md"]["to_path"],
                ".github/agents/_stage.agent.md",
            )
            self.assertEqual(
                by_from[".github/agents/stage.agent.md"]["to_name"], "_Stage"
            )
            self.assertEqual(
                by_from[".github/agents/ship.agent.md"]["to_path"],
                ".github/agents/_ship.agent.md",
            )
            self.assertEqual(
                by_from[".github/agents/orchestrator.agent.md"]["to_path"],
                ".github/agents/_orchestrator.agent.md",
            )
            for proposal in proposals:
                self.assertEqual(proposal["contract"], "agent-identity")
                self.assertEqual(proposal["status"], "known-legacy")
                self.assertIn("path", proposal["changed_fields"])
                self.assertIn("name", proposal["changed_fields"])
                self.assertFalse(proposal["canonical_exists"])
            # No proposal targets an elective or review agent.
            self.assertNotIn(".github/agents/auto-mergeinstall.agent.md", by_from)
            self.assertNotIn(".github/agents/adversarial-review.agent.md", by_from)

    def test_dot_prefixed_legacy_files_migrate_to_underscore(self) -> None:
        # Regression coverage for the dot-prefixed compatibility aliases
        # (.stage.agent.md / .Stage and .ship.agent.md / .Ship) retained in
        # PIPELINE_AGENT_IDENTITIES legacy_files/legacy_names so existing
        # dot-prefixed installs still migrate to the underscore canonical
        # identity after the underscore rename.
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file(agents, ".stage.agent.md", ".Stage")
            _write_agent_file(agents, ".ship.agent.md", ".Ship")

            proposals = _scan_agent_identity_migrations(workspace, {})
            by_from = self._index(proposals)

            self.assertEqual(len(proposals), 2)
            self.assertEqual(
                by_from[".github/agents/.stage.agent.md"]["to_path"],
                ".github/agents/_stage.agent.md",
            )
            self.assertEqual(
                by_from[".github/agents/.stage.agent.md"]["to_name"], "_Stage"
            )
            self.assertEqual(
                by_from[".github/agents/.ship.agent.md"]["to_path"],
                ".github/agents/_ship.agent.md",
            )
            self.assertEqual(
                by_from[".github/agents/.ship.agent.md"]["to_name"], "_Ship"
            )
            for proposal in proposals:
                self.assertEqual(proposal["contract"], "agent-identity")
                self.assertEqual(proposal["status"], "known-legacy")
                self.assertIn("path", proposal["changed_fields"])
                self.assertIn("name", proposal["changed_fields"])
                self.assertFalse(proposal["canonical_exists"])

    def test_stable_id_migrates_dot_prefixed_legacy_install(self) -> None:
        # Copilot review coverage: a dot-prefixed install carrying its stable
        # id must also migrate to both underscore identities via id matching.
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file_with_id(
                agents, ".ship.agent.md", ".Ship", "autoharness/pipeline/ship"
            )

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(len(proposals), 1)
            proposal = proposals[0]
            self.assertEqual(
                proposal["from_path"], ".github/agents/.ship.agent.md"
            )
            self.assertEqual(proposal["to_path"], ".github/agents/_ship.agent.md")
            self.assertEqual(proposal["to_name"], "_Ship")

    def test_dispatch_maps_to_orchestrator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file(agents, "dispatch.agent.md", "Dispatch")

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(len(proposals), 1)
            self.assertEqual(
                proposals[0]["to_path"], ".github/agents/_orchestrator.agent.md"
            )
            self.assertEqual(proposals[0]["from_name"], "Dispatch")
            self.assertEqual(proposals[0]["to_name"], "_Orchestrator")

    def test_canonical_file_with_legacy_name_is_name_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file(agents, "_stage.agent.md", "Stage")

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(len(proposals), 1)
            proposal = proposals[0]
            self.assertEqual(proposal["changed_fields"], ["name"])
            self.assertEqual(proposal["from_path"], proposal["to_path"])
            self.assertEqual(proposal["to_name"], "_Stage")

    def test_fully_canonical_agents_produce_no_proposals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file(agents, "_stage.agent.md", "_Stage")
            _write_agent_file(agents, "_ship.agent.md", "_Ship")
            _write_agent_file(agents, "_orchestrator.agent.md", "_Orchestrator")

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(proposals, [])

    def test_duplicate_canonical_and_legacy_flags_removal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file(agents, "_stage.agent.md", "_Stage")
            _write_agent_file(agents, "stage.agent.md", "Stage")

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(len(proposals), 1)
            proposal = proposals[0]
            self.assertEqual(proposal["from_path"], ".github/agents/stage.agent.md")
            self.assertTrue(proposal["canonical_exists"])
            self.assertIn("remove the legacy duplicate", proposal["action"])

    def test_self_install_mode_scans_local_agents_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            local_agents = workspace / ".github" / "local-agents"
            _write_agent_file(local_agents, "stage.agent.md", "Stage")
            profile = {
                "distribution": {
                    "is_global_tool": True,
                    "local_agents_dir": ".github/local-agents",
                }
            }

            proposals = _scan_agent_identity_migrations(workspace, profile)

            self.assertEqual(len(proposals), 1)
            self.assertEqual(
                proposals[0]["from_path"], ".github/local-agents/stage.agent.md"
            )
            self.assertEqual(
                proposals[0]["to_path"], ".github/local-agents/_stage.agent.md"
            )

    def test_self_install_mode_rejects_unsafe_local_agents_dir(self) -> None:
        # An absolute or parent-traversal local_agents_dir must not push
        # scanning outside the workspace; it falls back to the safe default.
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            default_dir = (workspace / ".github" / "local-agents").resolve()
            # `..\escape` is a literal single filename on POSIX (backslash is not
            # a separator) but a traversal on Windows, so only the platform-
            # independent no-escape invariant is asserted for it.
            always_fallback = ("../escape", "/abs/escape")
            no_escape_only = ("..\\escape",)
            for unsafe in always_fallback + no_escape_only:
                profile = {
                    "distribution": {
                        "is_global_tool": True,
                        "local_agents_dir": unsafe,
                    }
                }
                dirs = [d.resolve() for d in _resolve_agent_scan_dirs(workspace, profile)]
                for scan_dir in dirs:
                    self.assertTrue(
                        workspace.resolve() in scan_dir.parents
                        or scan_dir == workspace.resolve(),
                        f"scan dir escaped workspace for {unsafe!r}: {scan_dir}",
                    )
                if unsafe in always_fallback:
                    self.assertIn(default_dir, dirs)

    def test_end_to_end_report_surfaces_agent_identity_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            autoharness_home = Path(tmp) / "home"
            staging = workspace / ".autoharness" / "staging"
            (autoharness_home / "schemas").mkdir(parents=True, exist_ok=True)

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
                    json.dumps(schema), encoding="utf-8"
                )

            _write_agent_file(
                workspace / ".github" / "agents", "stage.agent.md", "Stage"
            )
            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-24T00:00:00Z",
                    "autoharness_version": "1.3.2",
                    "profile_hash": "abc",
                    "primitives_installed": [4],
                    "artifacts": [],
                    "variables_used": {"PROJECT_NAME": "demo"},
                },
            )
            _write_yaml(
                workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"}
            )
            _write_yaml(
                workspace / ".autoharness" / "workspace-profile.yaml",
                {"schema_version": "1.0.0"},
            )

            report = verify_workspace(workspace, autoharness_home, staging)

            agent_proposals = [
                proposal
                for proposal in report["migration_proposals"]
                if proposal.get("contract") == "agent-identity"
            ]
            self.assertEqual(len(agent_proposals), 1)
            self.assertEqual(
                agent_proposals[0]["to_path"], ".github/agents/_stage.agent.md"
            )

            markdown_path = Path(report["report_paths"]["markdown"])
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("agent-identity", markdown)

    def test_stable_id_detects_arbitrary_rename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            # Arbitrary filename + name, not a known legacy alias, but the
            # stable id identifies it as the ship pipeline agent.
            _write_agent_file_with_id(
                agents, "deployer.agent.md", "Deployer", "autoharness/pipeline/ship"
            )

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(len(proposals), 1)
            proposal = proposals[0]
            self.assertEqual(proposal["matched_by"], "id")
            self.assertEqual(proposal["agent_id"], "autoharness/pipeline/ship")
            self.assertEqual(proposal["status"], "id-mismatch")
            self.assertEqual(
                proposal["from_path"], ".github/agents/deployer.agent.md"
            )
            self.assertEqual(proposal["to_path"], ".github/agents/_ship.agent.md")
            self.assertEqual(proposal["to_name"], "_Ship")
            self.assertIn("path", proposal["changed_fields"])
            self.assertIn("name", proposal["changed_fields"])

    def test_stable_id_on_canonical_file_produces_no_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file_with_id(
                agents, "_ship.agent.md", "_Ship", "autoharness/pipeline/ship"
            )

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(proposals, [])

    def test_stable_id_name_only_when_filename_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file_with_id(
                agents, "_ship.agent.md", "Renamed", "autoharness/pipeline/ship"
            )

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(len(proposals), 1)
            proposal = proposals[0]
            self.assertEqual(proposal["matched_by"], "id")
            self.assertEqual(proposal["changed_fields"], ["name"])
            self.assertEqual(proposal["from_path"], proposal["to_path"])
            self.assertEqual(proposal["to_name"], "_Ship")
            # Filename is already canonical, so the canonical file is present.
            self.assertTrue(proposal["canonical_exists"])

    def test_stable_id_flags_duplicate_when_canonical_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            _write_agent_file_with_id(
                agents, "_ship.agent.md", "_Ship", "autoharness/pipeline/ship"
            )
            _write_agent_file_with_id(
                agents, "deployer.agent.md", "Deployer", "autoharness/pipeline/ship"
            )

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(len(proposals), 1)
            proposal = proposals[0]
            self.assertEqual(
                proposal["from_path"], ".github/agents/deployer.agent.md"
            )
            self.assertTrue(proposal["canonical_exists"])
            self.assertIn("remove the non-canonical duplicate", proposal["action"])

    def test_stable_id_takes_precedence_over_legacy_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            agents = workspace / ".github" / "agents"
            # A legacy-named file that also carries the stable id: it must be
            # matched exactly once (by id), not double-counted by the alias branch.
            _write_agent_file_with_id(
                agents, "ship.agent.md", "Ship", "autoharness/pipeline/ship"
            )

            proposals = _scan_agent_identity_migrations(workspace, {})

            self.assertEqual(len(proposals), 1)
            proposal = proposals[0]
            self.assertEqual(proposal["matched_by"], "id")
            # Filename is a known legacy alias, so status stays known-legacy.
            self.assertEqual(proposal["status"], "known-legacy")
            self.assertEqual(proposal["to_path"], ".github/agents/_ship.agent.md")


def _write_prompt_template(home: Path, name: str) -> None:
    prompts_dir = home / "templates" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / f"{name}.prompt.md.tmpl").write_text(
        f"---\ndescription: {name}\n---\n\n# {name}\n", encoding="utf-8"
    )


class NewArtifactDetectionTests(unittest.TestCase):
    def _by_expected(self, findings: list[dict]) -> dict[str, dict]:
        return {f["expected_path"]: f for f in findings}

    def test_prompt_install_rules_excludes_ping_loop(self) -> None:
        from autoharness.verify_workspace import PROMPT_INSTALL_RULES

        self.assertNotIn("ping-loop.prompt.md", PROMPT_INSTALL_RULES)
        # feature-flow prompts remain governed by their primitive-4 install rule.
        self.assertIn("feature-flow.prompt.md", PROMPT_INSTALL_RULES)

    def test_ping_loop_prompt_fully_removed(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.assertFalse(
            (repo_root / "templates" / "prompts" / "ping-loop.prompt.md.tmpl").exists(),
            "ping-loop.prompt template must be deleted (agent-intercom ACP consolidation)",
        )
        live_files = [
            "src/autoharness/verify_workspace.py",
            "templates/foundation/copilot-instructions.md.tmpl",
            ".github/skills/install-harness/SKILL.md",
            ".github/agents/auto-mergeinstall.agent.md",
            ".github/copilot-review-instructions.md",
            "docs/getting-started.md",
        ]
        for rel in live_files:
            text = (repo_root / rel).read_text(encoding="utf-8")
            self.assertNotIn(
                "ping-loop",
                text,
                f"{rel} still references the removed ping-loop prompt",
            )
        # The heartbeat prompt was the ping-loop artifact; docs must no longer
        # advertise it as an overlay target (heartbeat *behavior* stays, so match
        # only "heartbeat ... prompt(s)" advertisements, not behavioral mentions).
        heartbeat_prompt_docs = [
            "docs/capability-packs.md",
            "docs/getting-started.md",
        ]
        heartbeat_prompt_pattern = re.compile(r"heartbeat[\w/ ]{0,40}prompts?")
        for rel in heartbeat_prompt_docs:
            text = (repo_root / rel).read_text(encoding="utf-8").lower()
            self.assertIsNone(
                heartbeat_prompt_pattern.search(text),
                f"{rel} still advertises the removed heartbeat (ping-loop) prompt",
            )

    def test_flags_uninstalled_prompt_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ws"
            home = Path(tmp) / "home"
            _write_prompt_template(home, "feature-flow")

            findings = _scan_uninstalled_templates(
                workspace, home, {"artifacts": [], "primitives_installed": [4]}
            )

            index = self._by_expected(findings)
            self.assertIn(".github/prompts/feature-flow.prompt.md", index)
            finding = index[".github/prompts/feature-flow.prompt.md"]
            self.assertEqual(finding["kind"], "new-artifact")
            self.assertEqual(finding["artifact_class"], "prompt")
            self.assertEqual(finding["severity"], "advisory")
            self.assertEqual(
                finding["template"], "templates/prompts/feature-flow.prompt.md.tmpl"
            )
            # feature-flow is gated on primitive 4, which is installed here.
            self.assertEqual(finding["install_rule"], "primitive-4")
            self.assertTrue(finding["applicable"])

    def test_skips_prompt_present_on_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ws"
            home = Path(tmp) / "home"
            _write_prompt_template(home, "feature-flow")
            installed = workspace / ".github" / "prompts"
            installed.mkdir(parents=True, exist_ok=True)
            (installed / "feature-flow.prompt.md").write_text("# ff", encoding="utf-8")

            findings = _scan_uninstalled_templates(
                workspace, home, {"artifacts": [], "primitives_installed": [4]}
            )

            self.assertNotIn(
                ".github/prompts/feature-flow.prompt.md", self._by_expected(findings)
            )

    def test_skips_prompt_tracked_in_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ws"
            home = Path(tmp) / "home"
            _write_prompt_template(home, "feature-flow")
            manifest = {
                "artifacts": [
                    {
                        "path": ".github/prompts/feature-flow.prompt.md",
                        "template": "global prompt definition",
                        "primitive": 4,
                        "checksum": "x",
                    }
                ],
                "primitives_installed": [4],
            }

            findings = _scan_uninstalled_templates(workspace, home, manifest)

            self.assertNotIn(
                ".github/prompts/feature-flow.prompt.md", self._by_expected(findings)
            )

    def test_prompt_applicability_tracks_primitive_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ws"
            home = Path(tmp) / "home"
            _write_prompt_template(home, "feature-flow")

            # Primitive 4 installed -> applicable.
            applicable = self._by_expected(
                _scan_uninstalled_templates(
                    workspace, home, {"artifacts": [], "primitives_installed": [4]}
                )
            )[".github/prompts/feature-flow.prompt.md"]
            self.assertTrue(applicable["applicable"])

            # Primitive 4 absent (but primitives known) -> not applicable.
            not_applicable = self._by_expected(
                _scan_uninstalled_templates(
                    workspace, home, {"artifacts": [], "primitives_installed": [1, 2]}
                )
            )[".github/prompts/feature-flow.prompt.md"]
            self.assertFalse(not_applicable["applicable"])

            # Primitives unknown (empty) -> applicability None (operator decides).
            unknown = self._by_expected(
                _scan_uninstalled_templates(workspace, home, {"artifacts": []})
            )[".github/prompts/feature-flow.prompt.md"]
            self.assertIsNone(unknown["applicable"])

    def test_policy_opt_in_prompt_is_operator_decides(self) -> None:
        # feature-flow-dark is the P-017 dark-mode trigger shim. Even when its
        # required primitive (4) is installed, it must never be auto-applicable
        # because P-017 opt-in cannot be confirmed from primitives alone.
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ws"
            home = Path(tmp) / "home"
            _write_prompt_template(home, "feature-flow-dark")

            index = self._by_expected(
                _scan_uninstalled_templates(
                    workspace, home, {"artifacts": [], "primitives_installed": [4]}
                )
            )
            finding = index[".github/prompts/feature-flow-dark.prompt.md"]
            self.assertEqual(finding["install_rule"], "primitive-4 + P-017")
            self.assertIsNone(finding["applicable"])
            self.assertEqual(finding["requires_opt_in"], "P-017")

    def test_no_templates_dir_yields_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ws"
            home = Path(tmp) / "home"
            home.mkdir(parents=True, exist_ok=True)

            findings = _scan_uninstalled_templates(workspace, home, {"artifacts": []})

            self.assertEqual(findings, [])

    def test_verify_workspace_populates_new_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ws"
            home = Path(tmp) / "home"
            staging = workspace / ".autoharness" / "staging"
            (home / "schemas").mkdir(parents=True, exist_ok=True)
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
            }
            for schema_name in (
                "harness-manifest.schema.json",
                "harness-config.schema.json",
                "workspace-profile.schema.json",
            ):
                (home / "schemas" / schema_name).write_text(
                    json.dumps(schema), encoding="utf-8"
                )
            _write_prompt_template(home, "stage-grouping-analysis")
            _write_yaml(
                workspace / ".autoharness" / "harness-manifest.yaml",
                {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-24T00:00:00Z",
                    "autoharness_version": "1.4.9",
                    "profile_hash": "abc",
                    "primitives_installed": [4],
                    "artifacts": [],
                    "variables_used": {"PROJECT_NAME": "demo"},
                },
            )

            report = verify_workspace(workspace, home, staging)

            expected = {f["expected_path"] for f in report["new_artifacts"]}
            self.assertIn(
                ".github/prompts/stage-grouping-analysis.prompt.md", expected
            )
            markdown = Path(report["report_paths"]["markdown"]).read_text(
                encoding="utf-8"
            )
            self.assertIn("New Artifacts (Uninstalled Templates)", markdown)
            self.assertIn("stage-grouping-analysis.prompt.md", markdown)
