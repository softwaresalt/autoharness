"""Unit tests for the agent and skill frontmatter conformity contract (193.001-T, B1).

Plan: docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md section B1.
"""

from __future__ import annotations

import dataclasses
import tempfile
import unittest
from pathlib import Path

from autoharness import frontmatter_contract as fc
from autoharness.frontmatter_contract import (
    FM_BARE_MODEL,
    FM_FORBIDDEN_KEY,
    FM_MISSING_REQUIRED,
    FM_PARSE_ERROR,
    FM_TYPE_INVALID,
    FM_UNKNOWN_KEY,
    FM_UNRESOLVED_PLACEHOLDER,
    MODE_INSTALLED,
    MODE_TEMPLATE,
    PROFILE_PLUGIN_GLOBAL,
    PROFILE_TIER_ROUTED,
    Finding,
    ParsedFrontmatter,
    agent_key_sets,
    agent_profile_for,
    check_agent,
    check_skill,
    has_blocking_findings,
    parse_frontmatter,
    read_frontmatter,
    skill_key_sets,
)
from autoharness.verify_workspace import _add_frontmatter_model_routing_check

_TIER_ROUTED_BASE = [
    "name: Example",
    'description: "An example agent"',
    "max_subagent_tier: 2",
    "subagent_depth: 0",
    'model_family: "claude-sonnet-5"',
    'model_provider: "anthropic"',
    'reasoning_effort: "high"',
]

_PLUGIN_GLOBAL_BASE = [
    "name: Auto-Tune",
    'description: "Plugin agent"',
    "max_subagent_tier: 2",
    "subagent_depth: 2",
]

_SKILL_BASE = [
    "name: build-feature",
    'description: "Builds a feature"',
]


def _doc(lines: list[str], body: str = "\n# Body\n") -> str:
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def _replace(lines: list[str], key: str, new_line: str | None) -> list[str]:
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(f"{key}:"):
            replaced = True
            if new_line is not None:
                out.append(new_line)
        else:
            out.append(line)
    if not replaced and new_line is not None:
        out.append(new_line)
    return out


def _codes(findings: list[Finding]) -> list[tuple[str, str]]:
    return [(f.code, f.key) for f in findings]


def _blocking_codes(findings: list[Finding]) -> list[tuple[str, str]]:
    return [(f.code, f.key) for f in findings if not f.informational]


class KeySetTests(unittest.TestCase):
    def test_routing_key_constants(self) -> None:
        self.assertEqual(fc.TIER_KEYS, frozenset({"max_subagent_tier", "subagent_depth"}))
        for key in ("model_family", "model_provider", "reasoning_effort"):
            self.assertIn(key, fc.ROUTE_VALUE_KEYS)
        for prefix in ("anchor", "alt"):
            for suffix in ("family", "provider", "reasoning_effort"):
                key = f"{prefix}_review_{suffix}"
                self.assertIn(key, fc.ROUTE_VALUE_KEYS)
                self.assertRegex(key, fc.REVIEW_ROUTE_KEY_PATTERN)
        self.assertEqual(fc.routing_keys(), fc.TIER_KEYS | fc.ROUTE_VALUE_KEYS)
        # 194.007-T (C5a): context_tier joins ROUTE_VALUE_KEYS and only there.
        self.assertIn("context_tier", fc.ROUTE_VALUE_KEYS)
        self.assertNotIn("context_tier", fc.TIER_KEYS)
        self.assertIn("context_tier", fc.VALIDATORS)

    def test_tier_routed_profile(self) -> None:
        sets = agent_key_sets(PROFILE_TIER_ROUTED)
        self.assertEqual(
            sets.required,
            frozenset(
                {
                    "name",
                    "description",
                    "max_subagent_tier",
                    "subagent_depth",
                    "model_family",
                    "model_provider",
                    "reasoning_effort",
                }
            ),
        )
        for key in ("id", "maturity", "tools", "argument-hint", "handoffs", "target"):
            self.assertIn(key, sets.optional)
        self.assertIn("anchor_review_family", sets.optional)
        self.assertEqual(sets.forbidden, frozenset({"model"}))

    def test_plugin_global_profile(self) -> None:
        sets = agent_key_sets(PROFILE_PLUGIN_GLOBAL)
        self.assertEqual(
            sets.required,
            frozenset({"name", "description", "max_subagent_tier", "subagent_depth"}),
        )
        self.assertTrue(fc.ROUTE_VALUE_KEYS <= sets.forbidden)
        self.assertIn("model", sets.forbidden)
        self.assertFalse(sets.optional & fc.ROUTE_VALUE_KEYS)
        self.assertIn("tools", sets.optional)

    def test_skill_key_sets(self) -> None:
        sets = skill_key_sets()
        self.assertEqual(sets.required, frozenset({"name", "description"}))
        self.assertEqual(
            sets.optional,
            frozenset(
                {"argument-hint", "input", "license", "compatibility", "metadata", "allowed-tools"}
            ),
        )
        self.assertEqual(sets.forbidden, fc.routing_keys() | {"model"})

    def test_unknown_profile_rejected(self) -> None:
        with self.assertRaises(ValueError):
            agent_key_sets("bogus")

    def test_b_to_c_extension_via_route_value_keys(self) -> None:
        """AS-F6 / C5a: the single ROUTE_VALUE_KEYS edit extends every profile live."""
        self.assertIn("context_tier", agent_key_sets(PROFILE_TIER_ROUTED).optional)
        self.assertNotIn("context_tier", agent_key_sets(PROFILE_TIER_ROUTED).required)
        self.assertIn("context_tier", agent_key_sets(PROFILE_PLUGIN_GLOBAL).forbidden)
        self.assertIn("context_tier", skill_key_sets().forbidden)

        tier_routed = check_agent(
            parse_frontmatter(_doc(_TIER_ROUTED_BASE + ["context_tier: long_context"]), MODE_INSTALLED),
            PROFILE_TIER_ROUTED,
            MODE_INSTALLED,
        )
        self.assertEqual(tier_routed, [])

        plugin = check_agent(
            parse_frontmatter(_doc(_PLUGIN_GLOBAL_BASE + ["context_tier: long_context"]), MODE_INSTALLED),
            PROFILE_PLUGIN_GLOBAL,
            MODE_INSTALLED,
        )
        self.assertEqual(_codes(plugin), [(FM_FORBIDDEN_KEY, "context_tier")])

        skill = check_skill(
            parse_frontmatter(_doc(_SKILL_BASE + ["context_tier: long_context"]), MODE_INSTALLED),
            "build-feature",
            MODE_INSTALLED,
        )
        self.assertEqual(_codes(skill), [(FM_FORBIDDEN_KEY, "context_tier")])


class ContextTierContractTests(unittest.TestCase):
    """194.007-T (C5a): context_tier is an optional, enum-validated route-value key."""

    def _tier_routed(self, extra: list[str], mode: str = MODE_INSTALLED) -> list[Finding]:
        return check_agent(parse_frontmatter(_doc(_TIER_ROUTED_BASE + extra), mode), PROFILE_TIER_ROUTED, mode)

    def test_tier_routed_without_context_tier_passes(self) -> None:
        self.assertEqual(self._tier_routed([]), [])

    def test_tier_routed_with_each_enum_value_passes(self) -> None:
        for value in fc.CONTEXT_TIER_VALUES:
            with self.subTest(value=value):
                self.assertEqual(self._tier_routed([f'context_tier: "{value}"']), [])

    def test_invalid_values_are_type_invalid(self) -> None:
        for line in ("context_tier: huge", 'context_tier: ""', "context_tier: 3", "context_tier: [default]"):
            with self.subTest(line=line):
                findings = self._tier_routed([line])
                self.assertEqual(_codes(findings), [(FM_TYPE_INVALID, "context_tier")])
                self.assertTrue(has_blocking_findings(findings))

    def test_validator_registered_in_registry(self) -> None:
        validator = fc.VALIDATORS["context_tier"]
        for value in fc.CONTEXT_TIER_VALUES:
            self.assertIsNone(validator(value))
        for value in ("huge", "", None, 1, "Default"):
            with self.subTest(value=value):
                self.assertIsNotNone(validator(value))

    def test_plugin_global_with_context_tier_is_forbidden(self) -> None:
        findings = check_agent(
            parse_frontmatter(_doc(_PLUGIN_GLOBAL_BASE + ["context_tier: default"]), MODE_INSTALLED),
            PROFILE_PLUGIN_GLOBAL,
            MODE_INSTALLED,
        )
        self.assertEqual(_codes(findings), [(FM_FORBIDDEN_KEY, "context_tier")])

    def test_skill_with_context_tier_is_forbidden(self) -> None:
        findings = check_skill(
            parse_frontmatter(_doc(_SKILL_BASE + ["context_tier: default"]), MODE_INSTALLED),
            "build-feature",
            MODE_INSTALLED,
        )
        self.assertEqual(_codes(findings), [(FM_FORBIDDEN_KEY, "context_tier")])

    def test_template_mode_placeholder_skips_enum_check(self) -> None:
        findings = self._tier_routed(['context_tier: "{{TIER_2_CONTEXT_TIER}}"'], MODE_TEMPLATE)
        self.assertEqual(findings, [])

    def test_installed_mode_placeholder_is_unresolved(self) -> None:
        findings = self._tier_routed(['context_tier: "{{TIER_2_CONTEXT_TIER}}"'], MODE_INSTALLED)
        self.assertEqual(_codes(findings), [(FM_UNRESOLVED_PLACEHOLDER, "context_tier")])


class ParseFrontmatterTests(unittest.TestCase):
    def test_valid_document_parses(self) -> None:
        parsed = parse_frontmatter(_doc(_SKILL_BASE), MODE_INSTALLED)
        self.assertIsInstance(parsed, ParsedFrontmatter)
        self.assertIsNone(parsed.error)
        self.assertEqual(parsed.data["name"], "build-feature")

    def test_bom_and_crlf_parse_cleanly(self) -> None:
        text = "\ufeff" + _doc(_SKILL_BASE).replace("\n", "\r\n")
        parsed = parse_frontmatter(text, MODE_INSTALLED)
        self.assertIsNone(parsed.error)
        self.assertEqual(parsed.data["description"], "Builds a feature")
        parsed_bytes = parse_frontmatter(text.encode("utf-8"), MODE_INSTALLED)
        self.assertIsNone(parsed_bytes.error)
        self.assertEqual(parsed_bytes.data["name"], "build-feature")

    def test_closing_delimiter_trailing_whitespace_allowed(self) -> None:
        text = "---\n" + "\n".join(_SKILL_BASE) + "\n---   \nbody\n"
        self.assertIsNone(parse_frontmatter(text, MODE_INSTALLED).error)

    def test_opening_delimiter_trailing_whitespace_allowed(self) -> None:
        for opening in ("--- ", "---\t", "---  \t"):
            with self.subTest(opening=opening):
                text = opening + "\n" + "\n".join(_SKILL_BASE) + "\n---\nbody\n"
                self.assertIsNone(parse_frontmatter(text, MODE_INSTALLED).error)
        self.assertIsNotNone(parse_frontmatter(" ---\nname: x\n---\n", MODE_INSTALLED).error)

    def test_four_dash_line_is_not_a_closing_delimiter(self) -> None:
        text = "---\n" + "\n".join(_SKILL_BASE) + "\n----\nbody\n"
        parsed = parse_frontmatter(text, MODE_INSTALLED)
        self.assertIsNotNone(parsed.error)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("unclosed", parsed.error.message)

    def test_four_dash_line_then_real_delimiter(self) -> None:
        # "----" inside the block is skipped; the later exact "---" closes it,
        # so the YAML block contains "----" (a plain scalar line) -> invalid mapping.
        text = "---\nname: x\n----\n---\n"
        parsed = parse_frontmatter(text, MODE_INSTALLED)
        self.assertIsNotNone(parsed.error)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)

    def test_missing_opening_delimiter(self) -> None:
        parsed = parse_frontmatter("name: x\n---\n", MODE_INSTALLED)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("missing", parsed.error.message)
        four = parse_frontmatter("----\nname: x\n---\n", MODE_INSTALLED)
        self.assertEqual(four.error.code, FM_PARSE_ERROR)

    def test_duplicate_key_rejected(self) -> None:
        parsed = parse_frontmatter(_doc(_SKILL_BASE + ["name: other"]), MODE_INSTALLED)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("duplicate", parsed.error.message)

    def test_nested_duplicate_key_rejected(self) -> None:
        parsed = parse_frontmatter(
            _doc(_SKILL_BASE + ["input:", "  a: 1", "  a: 2"]), MODE_INSTALLED
        )
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)

    def test_non_mapping_rejected(self) -> None:
        parsed = parse_frontmatter("---\n- a\n- b\n---\n", MODE_INSTALLED)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("mapping", parsed.error.message)

    def test_invalid_yaml_rejected(self) -> None:
        parsed = parse_frontmatter("---\nname: [unclosed\n---\n", MODE_INSTALLED)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("invalid", parsed.error.message)

    def test_undecodable_bytes_rejected(self) -> None:
        parsed = parse_frontmatter(b"---\nname: \xff\xfe\n---\n", MODE_INSTALLED)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("undecodable", parsed.error.message)

    def test_comment_lines_tolerated(self) -> None:
        lines = ["# Source: references/x.md", "# License: MIT"] + _SKILL_BASE[:1] + [
            "# interleaved comment"
        ] + _SKILL_BASE[1:]
        parsed = parse_frontmatter(_doc(lines), MODE_INSTALLED)
        self.assertIsNone(parsed.error)
        self.assertEqual(check_skill(parsed, "build-feature", MODE_INSTALLED), [])

    def test_check_functions_surface_parse_error(self) -> None:
        parsed = parse_frontmatter("no frontmatter\n", MODE_INSTALLED)
        findings = check_skill(parsed, "build-feature", MODE_INSTALLED)
        self.assertEqual([f.code for f in findings], [FM_PARSE_ERROR])
        self.assertFalse(findings[0].informational)
        findings = check_agent(parsed, PROFILE_TIER_ROUTED, MODE_INSTALLED)
        self.assertEqual([f.code for f in findings], [FM_PARSE_ERROR])

    def test_read_frontmatter_missing_file_is_parse_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parsed = read_frontmatter(Path(tmp) / "missing.md", MODE_INSTALLED)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)

    def test_read_frontmatter_reads_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_bytes(("\ufeff" + _doc(_SKILL_BASE)).replace("\n", "\r\n").encode("utf-8"))
            parsed = read_frontmatter(path, MODE_INSTALLED)
        self.assertIsNone(parsed.error)

    def test_invalid_mode_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_frontmatter(_doc(_SKILL_BASE), "bogus")

    def test_alias_rejected(self) -> None:
        parsed = parse_frontmatter(
            _doc(_SKILL_BASE + ["input:", "  a: &shared hello", "  b: *shared"]), MODE_INSTALLED
        )
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("anchors/aliases", parsed.error.message)

    def test_merge_key_alias_rejected(self) -> None:
        parsed = parse_frontmatter(
            _doc(_SKILL_BASE + ["base: &b {x: 1}", "input:", "  <<: *b"]), MODE_INSTALLED
        )
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("anchors/aliases", parsed.error.message)

    def test_inline_merge_key_rejected(self) -> None:
        parsed = parse_frontmatter(
            _doc(_SKILL_BASE + ["input:", "  <<: {model_family: fam}"]), MODE_INSTALLED
        )
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("merge keys", parsed.error.message)

    def test_top_level_inline_merge_key_rejected(self) -> None:
        parsed = parse_frontmatter(_doc(_SKILL_BASE + ["<<: {model_family: fam}"]), MODE_INSTALLED)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("merge keys", parsed.error.message)

    def test_self_referential_alias_rejected(self) -> None:
        parsed = parse_frontmatter(_doc(_SKILL_BASE + ["input: &loop", "  self: *loop"]), MODE_INSTALLED)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)
        self.assertIn("anchors/aliases", parsed.error.message)

    def test_billion_laughs_alias_rejected(self) -> None:
        lines = _SKILL_BASE + ['a: &a ["x","x","x","x","x","x","x","x","x"]']
        for level in "bcdefghi":
            prev = chr(ord(level) - 1)
            lines.append(f"{level}: &{level} [" + ",".join([f"*{prev}"] * 9) + "]")
        parsed = parse_frontmatter(_doc(lines), MODE_INSTALLED)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)

    def test_deep_nesting_is_parse_error_not_crash(self) -> None:
        depth = 20000
        parsed = parse_frontmatter(_doc(_SKILL_BASE + ["input: " + "[" * depth + "]" * depth]), MODE_INSTALLED)
        self.assertIsNotNone(parsed.error)
        self.assertEqual(parsed.error.code, FM_PARSE_ERROR)

    def test_literal_sentinel_marker_text_preserved(self) -> None:
        for literal in ("AHFMPLACEHOLDER0X", "AHFMPLACEHOLDER7X", "AHFMPLACEHOLDER99999X"):
            with self.subTest(literal=literal):
                parsed = parse_frontmatter(
                    _doc(_SKILL_BASE + [f'argument-hint: "{literal} {{{{ARG}}}}"']), MODE_TEMPLATE
                )
                self.assertIsNone(parsed.error)
                self.assertEqual(parsed.data["argument-hint"], f"{literal} {{{{ARG}}}}")
                self.assertIn("argument-hint", parsed.placeholder_keys)

    def test_repeated_and_distinct_placeholders_restore_correctly(self) -> None:
        lines = [
            'name: "{{NAME}}"',
            'description: "{{DESC}} for {{NAME}} and {{ NAME }}"',
            'argument-hint: "{{DESC}}"',
        ]
        parsed = parse_frontmatter(_doc(lines), MODE_TEMPLATE)
        self.assertIsNone(parsed.error)
        self.assertEqual(parsed.data["name"], "{{NAME}}")
        self.assertEqual(parsed.data["description"], "{{DESC}} for {{NAME}} and {{ NAME }}")
        self.assertEqual(parsed.data["argument-hint"], "{{DESC}}")


class PlaceholderTests(unittest.TestCase):
    def test_quoted_placeholder_template_mode_allowed(self) -> None:
        lines = _replace(_TIER_ROUTED_BASE, "model_family", 'model_family: "{{TIER_2_FAMILY}}"')
        lines = _replace(lines, "max_subagent_tier", "max_subagent_tier: {{TIER}}")
        findings = check_agent(parse_frontmatter(_doc(lines), MODE_TEMPLATE), PROFILE_TIER_ROUTED, MODE_TEMPLATE)
        self.assertEqual(findings, [])

    def test_unquoted_leading_placeholder_template_mode_allowed(self) -> None:
        lines = _replace(_TIER_ROUTED_BASE, "model_family", "model_family: {{TIER_2_FAMILY}}")
        parsed = parse_frontmatter(_doc(lines), MODE_TEMPLATE)
        self.assertIsNone(parsed.error)
        self.assertEqual(parsed.data["model_family"], "{{TIER_2_FAMILY}}")
        self.assertIn("model_family", parsed.placeholder_keys)
        self.assertEqual(check_agent(parsed, PROFILE_TIER_ROUTED, MODE_TEMPLATE), [])

    def test_placeholder_rejected_in_installed_mode(self) -> None:
        for line in ('model_family: "{{TIER_2_FAMILY}}"', "model_family: {{TIER_2_FAMILY}}"):
            with self.subTest(line=line):
                lines = _replace(_TIER_ROUTED_BASE, "model_family", line)
                findings = check_agent(
                    parse_frontmatter(_doc(lines), MODE_INSTALLED), PROFILE_TIER_ROUTED, MODE_INSTALLED
                )
                self.assertEqual(_codes(findings), [(FM_UNRESOLVED_PLACEHOLDER, "model_family")])

    def test_nested_placeholder_rejected_in_installed_mode(self) -> None:
        lines = _SKILL_BASE + ["input:", "  target:", "    default: \"{{DEFAULT_BRANCH}}\""]
        findings = check_skill(parse_frontmatter(_doc(lines), MODE_INSTALLED), "build-feature", MODE_INSTALLED)
        self.assertEqual(_codes(findings), [(FM_UNRESOLVED_PLACEHOLDER, "input")])
        template = check_skill(parse_frontmatter(_doc(lines), MODE_TEMPLATE), "build-feature", MODE_TEMPLATE)
        self.assertEqual(template, [])

    def test_placeholder_presence_still_enforced_in_template_mode(self) -> None:
        lines = _replace(_TIER_ROUTED_BASE, "model_family", None)
        findings = check_agent(parse_frontmatter(_doc(lines), MODE_TEMPLATE), PROFILE_TIER_ROUTED, MODE_TEMPLATE)
        self.assertEqual(_codes(findings), [(FM_MISSING_REQUIRED, "model_family")])

    def test_check_accepts_plain_mapping(self) -> None:
        data = {"name": "{{SKILL}}", "description": "x"}
        self.assertEqual(check_skill(data, "build-feature", MODE_TEMPLATE), [])
        self.assertEqual(
            _codes(check_skill(data, "build-feature", MODE_INSTALLED)),
            [(FM_UNRESOLVED_PLACEHOLDER, "name")],
        )


class AgentCheckTests(unittest.TestCase):
    def _check(self, lines: list[str], profile: str = PROFILE_TIER_ROUTED) -> list[Finding]:
        return check_agent(parse_frontmatter(_doc(lines), MODE_INSTALLED), profile, MODE_INSTALLED)

    def test_conformant_tier_routed_passes(self) -> None:
        self.assertEqual(self._check(_TIER_ROUTED_BASE), [])

    def test_conformant_plugin_global_passes(self) -> None:
        self.assertEqual(self._check(_PLUGIN_GLOBAL_BASE, PROFILE_PLUGIN_GLOBAL), [])

    def test_bare_model_gives_single_code(self) -> None:
        for profile, base in ((PROFILE_TIER_ROUTED, _TIER_ROUTED_BASE), (PROFILE_PLUGIN_GLOBAL, _PLUGIN_GLOBAL_BASE)):
            for line in ("model: gpt-x", "model: [gpt-x, gpt-y]"):
                with self.subTest(profile=profile, line=line):
                    self.assertEqual(_codes(self._check(base + [line], profile)), [(FM_BARE_MODEL, "model")])

    def test_plugin_global_route_value_key_forbidden(self) -> None:
        findings = self._check(_PLUGIN_GLOBAL_BASE + ['model_family: "x"'], PROFILE_PLUGIN_GLOBAL)
        self.assertEqual(_codes(findings), [(FM_FORBIDDEN_KEY, "model_family")])
        findings = self._check(_PLUGIN_GLOBAL_BASE + ['anchor_review_family: "x"'], PROFILE_PLUGIN_GLOBAL)
        self.assertEqual(_codes(findings), [(FM_FORBIDDEN_KEY, "anchor_review_family")])

    def test_missing_required(self) -> None:
        findings = self._check(_replace(_TIER_ROUTED_BASE, "max_subagent_tier", None))
        self.assertEqual(_codes(findings), [(FM_MISSING_REQUIRED, "max_subagent_tier")])
        findings = self._check(_replace(_PLUGIN_GLOBAL_BASE, "max_subagent_tier", None), PROFILE_PLUGIN_GLOBAL)
        self.assertEqual(_codes(findings), [(FM_MISSING_REQUIRED, "max_subagent_tier")])

    def test_type_validation(self) -> None:
        cases = [
            ("max_subagent_tier", "max_subagent_tier: true"),
            ("max_subagent_tier", "max_subagent_tier: 0"),
            ("max_subagent_tier", "max_subagent_tier: 4"),
            ("max_subagent_tier", 'max_subagent_tier: "2"'),
            ("subagent_depth", "subagent_depth: -1"),
            ("subagent_depth", "subagent_depth: false"),
            ("model_family", 'model_family: ""'),
            ("model_provider", "model_provider: 42"),
            ("reasoning_effort", "reasoning_effort: [high]"),
            ("name", "name: yes"),
            ("description", 'description: ""'),
        ]
        for key, line in cases:
            with self.subTest(line=line):
                self.assertEqual(
                    _codes(self._check(_replace(_TIER_ROUTED_BASE, key, line))),
                    [(FM_TYPE_INVALID, key)],
                )

    def test_empty_provider_and_effort_allowed(self) -> None:
        lines = _replace(_TIER_ROUTED_BASE, "model_provider", 'model_provider: ""')
        lines = _replace(lines, "reasoning_effort", 'reasoning_effort: ""')
        self.assertEqual(self._check(lines), [])

    def test_empty_review_route_families_allowed_but_typed(self) -> None:
        for key in ("alt_review_family", "anchor_review_family"):
            with self.subTest(key=key):
                self.assertEqual(self._check(_TIER_ROUTED_BASE + [f'{key}: ""']), [])
                self.assertEqual(
                    _codes(self._check(_TIER_ROUTED_BASE + [f"{key}: 42"])),
                    [(FM_TYPE_INVALID, key)],
                )

    def test_unknown_key_informational_only(self) -> None:
        findings = self._check(_TIER_ROUTED_BASE + ["color: blue"])
        self.assertEqual(_codes(findings), [(FM_UNKNOWN_KEY, "color")])
        self.assertTrue(findings[0].informational)
        self.assertFalse(has_blocking_findings(findings))

    def test_findings_sorted_and_frozen(self) -> None:
        lines = _replace(_TIER_ROUTED_BASE, "name", None) + ["model: gpt-x", "zeta: 1", "alpha: 2"]
        findings = self._check(lines)
        self.assertEqual(findings, sorted(findings, key=lambda f: (f.code, f.key)))
        self.assertEqual(
            _codes(findings),
            [
                (FM_BARE_MODEL, "model"),
                (FM_MISSING_REQUIRED, "name"),
                (FM_UNKNOWN_KEY, "alpha"),
                (FM_UNKNOWN_KEY, "zeta"),
            ],
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            findings[0].code = "X"  # type: ignore[misc]
        self.assertTrue(has_blocking_findings(findings))

    def test_validators_registry(self) -> None:
        self.assertIsInstance(fc.VALIDATORS, dict)
        for key in ("max_subagent_tier", "subagent_depth", "model_family", "model_provider", "reasoning_effort"):
            self.assertTrue(callable(fc.VALIDATORS[key]))


class SkillCheckTests(unittest.TestCase):
    def _check(self, lines: list[str], directory: str = "build-feature") -> list[Finding]:
        return check_skill(parse_frontmatter(_doc(lines), MODE_INSTALLED), directory, MODE_INSTALLED)

    def test_conformant_skill_passes(self) -> None:
        self.assertEqual(self._check(_SKILL_BASE + ['argument-hint: "x"', "input:", "  a: 1"]), [])

    def test_skill_routing_keys_forbidden(self) -> None:
        for key in ("model_family", "anchor_review_family", "max_subagent_tier", "reasoning_effort"):
            with self.subTest(key=key):
                self.assertEqual(
                    _codes(self._check(_SKILL_BASE + [f'{key}: "x"'])),
                    [(FM_FORBIDDEN_KEY, key)],
                )

    def test_skill_bare_model(self) -> None:
        self.assertEqual(_codes(self._check(_SKILL_BASE + ["model: gpt-x"])), [(FM_BARE_MODEL, "model")])

    def test_missing_skill_name(self) -> None:
        self.assertEqual(
            _codes(self._check(_replace(_SKILL_BASE, "name", None))),
            [(FM_MISSING_REQUIRED, "name")],
        )

    def test_skill_name_must_match_directory(self) -> None:
        self.assertEqual(
            _codes(self._check(_SKILL_BASE, directory="other-skill")),
            [(FM_TYPE_INVALID, "name")],
        )

    def test_skill_name_pattern_and_length(self) -> None:
        for name in ("Build-Feature", "build--feature", "-build", "a" * 65):
            with self.subTest(name=name):
                lines = _replace(_SKILL_BASE, "name", f"name: {name}")
                self.assertEqual(_codes(self._check(lines, directory=name)), [(FM_TYPE_INVALID, "name")])
        ok_name = "a" * 64
        self.assertEqual(self._check(_replace(_SKILL_BASE, "name", f"name: {ok_name}"), directory=ok_name), [])


class AgentProfileSelectorTests(unittest.TestCase):
    def test_selector(self) -> None:
        plugin_agents = [".github/agents/auto-tune.agent.md", "./.github/agents/auto-mergeinstall.agent.md"]
        self.assertEqual(agent_profile_for(".github/agents/auto-tune.agent.md", plugin_agents), PROFILE_PLUGIN_GLOBAL)
        self.assertEqual(
            agent_profile_for(Path(".github") / "agents" / "auto-mergeinstall.agent.md", plugin_agents),
            PROFILE_PLUGIN_GLOBAL,
        )
        self.assertEqual(agent_profile_for(".github\\agents\\auto-tune.agent.md", plugin_agents), PROFILE_PLUGIN_GLOBAL)
        self.assertEqual(agent_profile_for(".github/agents/_ship.agent.md", plugin_agents), PROFILE_TIER_ROUTED)
        self.assertEqual(agent_profile_for(".github/agents/auto-tune.agent.md", []), PROFILE_TIER_ROUTED)


class LegacyRoutingCheckParityTests(unittest.TestCase):
    """INV-B3: B1 agrees with _add_frontmatter_model_routing_check on routing values."""

    CASES = [
        ("conformant", None, None),
        ("model_family false", "model_family", "model_family: false"),
        ("model_family 42", "model_family", "model_family: 42"),
        ("model_family []", "model_family", "model_family: []"),
        ("model_family {}", "model_family", "model_family: {}"),
        ("model_provider 42", "model_provider", "model_provider: 42"),
        ("quoted placeholder", "model_family", 'model_family: "{{TIER_2_FAMILY}}"'),
        ("unquoted placeholder", "model_family", "model_family: {{TIER_2_FAMILY}}"),
        ("provider placeholder", "model_provider", 'model_provider: "{{TIER_2_PROVIDER}}"'),
    ]

    def test_parity_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for label, key, line in self.CASES:
                with self.subTest(case=label):
                    lines = _TIER_ROUTED_BASE if key is None else _replace(_TIER_ROUTED_BASE, key, line)
                    text = _doc(lines)
                    path = Path(tmp) / "agent.agent.md"
                    path.write_text(text, encoding="utf-8")
                    report: dict = {"targeted_checks": {}}
                    _add_frontmatter_model_routing_check(report, "legacy", path)
                    legacy_ok = report["targeted_checks"]["legacy"]["ok"]
                    findings = check_agent(
                        parse_frontmatter(text, MODE_INSTALLED), PROFILE_TIER_ROUTED, MODE_INSTALLED
                    )
                    self.assertEqual(not has_blocking_findings(findings), legacy_ok, findings)
                    if key is not None:
                        self.assertFalse(legacy_ok)


if __name__ == "__main__":
    unittest.main()
