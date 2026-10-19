"""Config template and install-harness surfaces for catalog/bindings (208-F B8).

The harness-config template renders the 1.2.0 contract with empty ``routes`` and
``bindings`` blocks and no new variable; the global, non-rendered install-harness
skill validates by the document's own ``schema_version`` and states the shared
site-composition rule for bound agents without install-time substitution.
Plan: docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md (### B8).
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

from _config_schema_contract import CURRENT_CONFIG_SCHEMA_VERSION, current_config_mirror_path
from autoharness.verify_workspace import _derive_template_variables, _render_template

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "templates" / "harness-config.yaml.tmpl"
_SKILL = _REPO_ROOT / ".github" / "skills" / "install-harness" / "SKILL.md"
_MIRROR_1_2_0 = _REPO_ROOT / "schemas" / "harness-config" / "1.2.0.schema.json"
_PLACEHOLDER = re.compile(r"\{\{[^}\n]*\}\}")
_PROFILE_STACKS = ("python", "typescript", "rust")


def _template_text() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


def _skill_text() -> str:
    return _SKILL.read_text(encoding="utf-8").replace("\r\n", "\n")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _live() -> tuple[dict, dict, dict, dict]:
    directory = _REPO_ROOT / ".autoharness"
    load = lambda name: yaml.safe_load((directory / name).read_text(encoding="utf-8"))
    return (
        load("harness-manifest.yaml"),
        load("config.yaml"),
        load("workspace-profile.yaml"),
        load("backlog-registry.yaml"),
    )


def _render(stack: str | None = None) -> str:
    manifest, config, profile, registry = _live()
    config = copy.deepcopy(config)
    if stack is not None:
        config["primary_stack_pack"] = stack
        config["stack_packs"] = [stack]
    variables = _derive_template_variables(_REPO_ROOT, manifest, config, profile, registry)
    return _render_template(_template_text(), variables)


def _install_validation_step() -> str:
    match = re.search(r"(?ms)^#### Step 1\.0b: Load Operator Configuration\n(.*?)^#### Step 1\.1: ", _skill_text())
    if match is None:
        raise AssertionError("install-harness Step 1.0b not found")
    return match.group(1)


class TemplateRoutesBindingsBlockTests(unittest.TestCase):
    def test_template_declares_the_current_schema_version_literal(self) -> None:
        self.assertEqual(yaml.safe_load(_render())["schema_version"], CURRENT_CONFIG_SCHEMA_VERSION)
        self.assertEqual(CURRENT_CONFIG_SCHEMA_VERSION, "1.2.0")
        self.assertRegex(_template_text(), r'(?m)^schema_version: "1\.2\.0"$')

    def test_rendered_config_has_empty_routes_and_bindings_under_model_routing(self) -> None:
        model_routing = yaml.safe_load(_render())["model_routing"]
        self.assertEqual(model_routing["routes"], {})
        self.assertEqual(model_routing["bindings"], {})

    def test_blocks_are_literal_empty_maps_with_an_explanatory_comment(self) -> None:
        text = _template_text()
        self.assertRegex(text, r"(?m)^  routes: \{\}\s*$")
        self.assertRegex(text, r"(?m)^  bindings: \{\}\s*$")
        comment = text[text.index("tier-delta catalog") - 400 : text.index("  bindings: {}")]
        flat = _flat(comment)
        self.assertIn("tier-delta catalog", flat)
        self.assertIn("no YAML anchors", flat)
        self.assertIn("agent:<id>", flat)

    def test_template_has_no_anchor_alias_or_merge_key(self) -> None:
        lines = [line for line in _template_text().splitlines() if not line.lstrip().startswith("#")]
        code = "\n".join(re.sub(r"\s#.*$", "", line) for line in lines)
        self.assertNotIn("&", code)
        self.assertNotRegex(code, r"(?m)(^|[\s:\[,-])\*[A-Za-z0-9_-]")
        self.assertNotIn("<<:", code)

    def test_new_blocks_add_no_template_variable(self) -> None:
        block = _template_text()[_template_text().index("  routes: {}") :]
        block = block[: block.index("# AI CLI tool startup configuration")]
        self.assertEqual(_PLACEHOLDER.findall(block), [])


class RenderedConfigValidationTests(unittest.TestCase):
    def test_rendered_default_config_validates_against_the_1_2_0_mirror(self) -> None:
        schema = json.loads(_MIRROR_1_2_0.read_text(encoding="utf-8"))
        validator = Draft7Validator(schema)
        for stack in (None, *_PROFILE_STACKS):
            with self.subTest(stack=stack):
                rendered = yaml.safe_load(_render(stack))
                self.assertEqual([e.message for e in validator.iter_errors(rendered)], [])

    def test_rendered_default_config_validates_against_the_current_mirror(self) -> None:
        schema = json.loads(current_config_mirror_path().read_text(encoding="utf-8"))
        self.assertEqual(list(Draft7Validator(schema).iter_errors(yaml.safe_load(_render()))), [])

    def test_rendering_leaves_no_unresolved_placeholder(self) -> None:
        for stack in (None, *_PROFILE_STACKS):
            with self.subTest(stack=stack):
                self.assertEqual(_PLACEHOLDER.findall(_render(stack)), [])


class InstallHarnessSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.step = _install_validation_step()
        self.flat = _flat(self.step)

    def test_validation_selects_the_schema_by_the_documents_own_version(self) -> None:
        for token in (
            "schema_version",
            "schemas/harness-config/<schema_version>.schema.json",
            "resolve_contract_schema_path",
            "contract finding",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.flat)

    def test_root_schema_is_not_the_sole_validation_target(self) -> None:
        item = re.search(r"(?ms)^1\. (.*?)^2\. Extract operator preferences", self.step)
        self.assertIsNotNone(item)
        self.assertNotRegex(item.group(1).strip(), r"^Validate against `\{autoharness_home\}/schemas/harness-config\.schema\.json`$")
        self.assertRegex(item.group(1), r"(?i)root[^\n]*tracks only the current version")

    def test_bound_agent_route_variables_come_from_the_shared_site_composition(self) -> None:
        for token in (
            "four route variables",
            "shared site composition",
            "binding's route",
            "config.overrides",
            "template default tier is never consulted for a bound agent",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.flat)

    def test_unbound_agent_renders_its_template_default_tier(self) -> None:
        self.assertRegex(self.flat, r"unbound agent renders its template default tier as before")

    def test_binding_on_unresolvable_managed_default_tier_is_rejected(self) -> None:
        self.assertIn("ROUTING_BINDING_UNRESOLVED_SITE", self.flat)
        self.assertRegex(self.flat, r"cannot be established")

    def test_new_guidance_reads_config_at_runtime_without_placeholders(self) -> None:
        paragraph = next(block for block in self.step.split("\n\n") if "shared site composition" in block)
        self.assertNotIn("{{", paragraph)
        self.assertIn("at runtime", _flat(paragraph))

    def test_skill_frontmatter_name_unchanged(self) -> None:
        self.assertTrue(_skill_text().startswith("---\nname: install-harness\n"))

    def test_manifest_checksum_matches_committed_skill(self) -> None:
        manifest = yaml.safe_load((_REPO_ROOT / ".autoharness" / "harness-manifest.yaml").read_text(encoding="utf-8"))
        entry = next(a for a in manifest["artifacts"] if a["path"] == ".github/skills/install-harness/SKILL.md")
        blob = _SKILL.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(entry["checksum"], hashlib.sha256(blob).hexdigest())


class StepThreeFourPreservationTests(unittest.TestCase):
    def setUp(self) -> None:
        match = re.search(r"(?ms)^#### Step 3\.4: Write Resolved Configuration\n(.*?)^### Phase 4", _skill_text())
        self.assertIsNotNone(match, "install-harness Step 3.4 not found")
        self.flat = _flat(match.group(1))

    def test_operator_routes_and_bindings_are_carried_over_verbatim(self) -> None:
        for token in (
            "non-empty `model_routing.routes` and `model_routing.bindings`",
            "carried over verbatim",
            "never regenerated, emptied, or variable-substituted",
            "literal `{}` applies only when the existing config has none and the config is written at schema `1.2.0` or later",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.flat)

    def test_existing_schema_version_is_not_silently_bumped(self) -> None:
        self.assertRegex(self.flat, r"keep the observed `schema_version`")
        self.assertIn("tune-harness approval path", self.flat)

    def test_installed_config_list_names_routes_and_bindings(self) -> None:
        self.assertRegex(self.flat, r"`model_routing` \(including any operator `routes` and `bindings`\)")

    def test_manifest_note_records_the_review_fix(self) -> None:
        manifest = yaml.safe_load((_REPO_ROOT / ".autoharness" / "harness-manifest.yaml").read_text(encoding="utf-8"))
        entry = next(a for a in manifest["artifacts"] if a["path"] == ".github/skills/install-harness/SKILL.md")
        self.assertIn("208.010-T review", entry["note"])

    def test_pre_1_2_0_retention_omits_absent_routes_and_bindings(self) -> None:
        for token in (
            "below `1.2.0`",
            "omit the `routes` and `bindings` keys entirely",
            "template's empty-block lines",
            "empty `{}` defaults apply only to a fresh install or a config written at schema `1.2.0` or later",
            "`ROUTING_KEYS_REQUIRE_1_2_0`",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.flat)

    def test_omission_rule_is_not_a_license_to_drop_operator_values(self) -> None:
        self.assertIn("never drops an operator-authored value", self.flat)

    def test_manifest_note_records_the_legacy_rerender_fix(self) -> None:
        manifest = yaml.safe_load((_REPO_ROOT / ".autoharness" / "harness-manifest.yaml").read_text(encoding="utf-8"))
        entry = next(a for a in manifest["artifacts"] if a["path"] == ".github/skills/install-harness/SKILL.md")
        self.assertIn("pre-1.2.0 retention omits absent routes and bindings", entry["note"])


class LegacyRerenderInertKeyTests(unittest.TestCase):
    """Why the Step 3.4 omission rule exists: routing_inert_keys flags key presence below 1.2.0."""

    @staticmethod
    def _inert_check(schema_version: str, model_routing: dict) -> dict:
        from autoharness.verify_workspace import _add_model_routing_catalog_checks

        report: dict = {"targeted_checks": {}, "warnings": []}
        config = {"schema_version": schema_version, "model_routing": model_routing}
        _add_model_routing_catalog_checks(report, config, Path("config.yaml"), None, "registry unavailable")
        return report["targeted_checks"]["routing_inert_keys"]

    def test_empty_maps_at_1_1_0_fail_the_inert_key_check(self) -> None:
        check = self._inert_check("1.1.0", {"routes": {}, "bindings": {}})
        self.assertFalse(check["ok"])
        self.assertEqual(2, len(check["errors"]))
        self.assertTrue(all(e.startswith("ROUTING_KEYS_REQUIRE_1_2_0") for e in check["errors"]))

    def test_omitted_keys_at_1_1_0_pass_the_inert_key_check(self) -> None:
        self.assertTrue(self._inert_check("1.1.0", {"tier1": {}})["ok"])

    def test_empty_maps_at_1_2_0_pass_the_inert_key_check(self) -> None:
        self.assertTrue(self._inert_check("1.2.0", {"routes": {}, "bindings": {}})["ok"])


if __name__ == "__main__":
    unittest.main()
