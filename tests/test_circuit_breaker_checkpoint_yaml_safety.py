"""Regression guard: circuit-breaker checkpoint frontmatter YAML-safety.

Covers the four hazard classes identified for the prescribed circuit-breaker
checkpoint format (``docs/memory/{YYYY-MM-DD}/circuit-break-{operation-slug}.md``):
embedded double quote, embedded backslash, trailing backslash, colon-space, and
space-hash. Each free-form frontmatter value (``agent``, ``skill``,
``operation``, ``identity``) must be emitted as a JSON string literal
(``json.dumps``-style output) rather than a naively double-quoted value.

Each case asserts BOTH:

1. The emitted frontmatter block PARSES as YAML (``yaml.safe_load``), and
2. The parsed value ROUND-TRIPS to the original raw value byte-for-byte.

A value that parses but decodes to a different string (silent truncation) is
a REGRESSION FAILURE, not a pass -- this is the failure mode already observed
in the wild for the space-hash case (see
``docs/archive/memory/circuit-break-copilot-review-cycle.md``), and a
parse-only assertion would not catch it.

See:
* .github/instructions/circuit-breaker.instructions.md (## Log Format,
  "Frontmatter YAML-Safety Regression Cases")
* templates/instructions/circuit-breaker.instructions.md.tmpl (paired template)
"""

from __future__ import annotations

import json
import unittest

import yaml

# The five representative hazard values used throughout the instruction's
# worked table. Four are named "hazard classes" in the task/instruction;
# colon-space is included as a fifth measured case that a bare-unquoted
# scalar already mishandles differently (parse failure rather than silent
# truncation), which is why JSON-escaping is required for all of them.
_HAZARD_VALUES = {
    "embedded_double_quote": 'say "hi"',
    "embedded_backslash": r"C:\path\file",
    "trailing_backslash": "ends\\",
    "colon_space": "key: value",
    "space_hash": "note #1",
}

_FREE_FORM_FIELDS = ("agent", "skill", "operation", "identity")


def _json_string_literal(value: str) -> str:
    """The prescribed encoding: a JSON string literal (json.dumps output)."""
    return json.dumps(value)


def _naive_bare_double_quote(value: str) -> str:
    """The rejected encoding: wrapping the raw value in bare double quotes."""
    return f'"{value}"'


def _build_frontmatter(field: str, encoded_value: str) -> str:
    """Build a full checkpoint frontmatter block with ``field`` set to the
    already-encoded ``encoded_value``, and every other free-form field held
    at a safe default so only ``field`` is under test."""
    defaults = {
        "agent": '"Ship"',
        "skill": '"direct"',
        "operation": '"probe"',
        "identity": '"probe"',
    }
    values = dict(defaults)
    values[field] = encoded_value
    return (
        "---\n"
        "type: circuit-breaker\n"
        "timestamp: 2026-08-30T00:00:00Z\n"
        f"agent: {values['agent']}\n"
        f"skill: {values['skill']}\n"
        "breaker_type: universal\n"
        f"operation: {values['operation']}\n"
        "attempts: 1\n"
        f"identity: {values['identity']}\n"
        "---\n"
    )


def _parse_frontmatter(block: str) -> dict:
    inner = block.split("---\n", 2)[1]
    return yaml.safe_load(inner)


class CircuitBreakerCheckpointYamlSafetyTests(unittest.TestCase):
    """Assert JSON-string-literal encoding parses and round-trips for all
    four hazard classes, across all four free-form frontmatter fields."""

    def test_json_escaped_values_parse_and_round_trip_for_every_field(self) -> None:
        for field in _FREE_FORM_FIELDS:
            for hazard_name, raw_value in _HAZARD_VALUES.items():
                with self.subTest(field=field, hazard=hazard_name):
                    encoded = _json_string_literal(raw_value)
                    block = _build_frontmatter(field, encoded)
                    try:
                        parsed = _parse_frontmatter(block)
                    except yaml.YAMLError as exc:  # pragma: no cover - failure path
                        self.fail(
                            f"JSON-escaped {field}={encoded!r} failed to parse: {exc}"
                        )
                    self.assertEqual(
                        parsed.get(field),
                        raw_value,
                        f"JSON-escaped {field} did not round-trip to the original "
                        f"raw value for hazard class {hazard_name!r}",
                    )

    def test_naive_bare_double_quoting_fails_at_least_one_hazard_class_per_field(
        self,
    ) -> None:
        """Demonstrates why naive bare-double-quoting is insufficient: for
        every free-form field, at least one hazard class either fails to
        parse or silently round-trips to a different value."""
        for field in _FREE_FORM_FIELDS:
            failures = []
            for hazard_name, raw_value in _HAZARD_VALUES.items():
                encoded = _naive_bare_double_quote(raw_value)
                block = _build_frontmatter(field, encoded)
                try:
                    parsed = _parse_frontmatter(block)
                except yaml.YAMLError:
                    failures.append(hazard_name)
                    continue
                if parsed.get(field) != raw_value:
                    failures.append(hazard_name)
            with self.subTest(field=field):
                self.assertTrue(
                    failures,
                    f"expected naive bare-double-quoting to fail at least one "
                    f"hazard class for field {field!r}, but all passed",
                )
                # The three quote/backslash hazard classes must always be
                # among the failures -- these are PARSE-FAIL under naive
                # quoting regardless of field.
                for required in (
                    "embedded_double_quote",
                    "embedded_backslash",
                    "trailing_backslash",
                ):
                    self.assertIn(required, failures)

    def test_bare_unquoted_space_hash_silently_truncates(self) -> None:
        """The exact failure already observed in the wild: an unquoted
        scalar containing ' #' parses successfully but silently truncates at
        the hash, which a parse-only assertion would not catch."""
        raw_value = _HAZARD_VALUES["space_hash"]
        block = (
            "---\n"
            "type: circuit-breaker\n"
            "timestamp: 2026-08-30T00:00:00Z\n"
            f"agent: {raw_value}\n"
            "breaker_type: universal\n"
            "operation: probe\n"
            "attempts: 1\n"
            'identity: "probe"\n'
            "---\n"
        )
        parsed = _parse_frontmatter(block)
        self.assertNotEqual(
            parsed.get("agent"),
            raw_value,
            "expected the bare-unquoted space-hash case to silently truncate",
        )
        self.assertEqual(parsed.get("agent"), "note")

    def test_bare_unquoted_colon_space_fails_to_parse(self) -> None:
        """The exact failure already observed in the wild: an unquoted
        scalar containing ': ' aborts YAML parsing entirely."""
        raw_value = _HAZARD_VALUES["colon_space"]
        block = (
            "---\n"
            "type: circuit-breaker\n"
            "timestamp: 2026-08-30T00:00:00Z\n"
            f"agent: {raw_value}\n"
            "breaker_type: universal\n"
            "operation: probe\n"
            "attempts: 1\n"
            'identity: "probe"\n'
            "---\n"
        )
        with self.assertRaises(yaml.YAMLError):
            _parse_frontmatter(block)


if __name__ == "__main__":
    unittest.main()
