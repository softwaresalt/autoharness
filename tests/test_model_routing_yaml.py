"""A2a (214-S): the shared raw-YAML guard for anchors, aliases, and merge keys under model_routing."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

from _resolver_purity_guard import forbid_io

from autoharness import model_routing_yaml
from autoharness.model_routing_yaml import YamlGuardResult


def check(text, version):
    with forbid_io():
        return model_routing_yaml.check_model_routing_yaml(text, version)


ANCHOR_DOC = """\
schema_version: "1.2.0"
model_routing:
  tier3: &t3
    model_family: f
  stage:
    model_family: g
"""

ALIAS_DOC = """\
model_routing:
  tier3: &t3
    model_family: f
  stage: *t3
"""

MERGE_DOC = """\
model_routing:
  tier3: &t3 {model_family: f}
  stage:
    <<: *t3
    model_provider: p
"""


class DetectionTests(unittest.TestCase):
    def test_anchor_alias_and_merge_key_are_flagged_with_kind_and_line(self):
        result = check(MERGE_DOC, "1.2.0")
        self.assertIsInstance(result, YamlGuardResult)
        self.assertEqual(
            result.errors,
            (
                "ROUTING_ANCHOR_UNSUPPORTED: anchor at line 2",
                "ROUTING_ANCHOR_UNSUPPORTED: merge_key at line 4",
                "ROUTING_ANCHOR_UNSUPPORTED: alias at line 4",
            ),
        )
        self.assertEqual(result.warnings, ())
        self.assertIsNone(result.parse_error)

    def test_alias_in_block_style(self):
        result = check(ALIAS_DOC, "1.2.0")
        self.assertEqual(
            result.errors,
            ("ROUTING_ANCHOR_UNSUPPORTED: anchor at line 2", "ROUTING_ANCHOR_UNSUPPORTED: alias at line 4"),
        )

    def test_anchor_on_a_sequence_node(self):
        result = check("model_routing:\n  list: &seq\n    - a\n    - b\n", "1.2.0")
        self.assertEqual(result.errors, ("ROUTING_ANCHOR_UNSUPPORTED: anchor at line 2",))

    def test_flow_style(self):
        result = check("model_routing: {a: &x 1, b: *x}\n", "1.2.0")
        self.assertEqual(
            result.errors,
            ("ROUTING_ANCHOR_UNSUPPORTED: anchor at line 1", "ROUTING_ANCHOR_UNSUPPORTED: alias at line 1"),
        )

    def test_anchor_on_the_model_routing_value_itself(self):
        result = check("model_routing: &mr\n  a: b\n", "1.2.0")
        self.assertEqual(result.errors, ("ROUTING_ANCHOR_UNSUPPORTED: anchor at line 1",))

    def test_alias_as_the_model_routing_value(self):
        result = check("base: &b\n  a: 1\nmodel_routing: *b\n", "1.2.0")
        self.assertEqual(result.errors, ("ROUTING_ANCHOR_UNSUPPORTED: alias at line 3",))


class SeverityTests(unittest.TestCase):
    def test_errors_at_1_2_0_missing_and_unparsable_versions(self):
        for version in ("1.2.0", "1.2.1", "2.0.0", "1.10.0", None, "", "banana", "1.x"):
            with self.subTest(version=version):
                result = check(ANCHOR_DOC, version)
                self.assertEqual(len(result.errors), 1)
                self.assertEqual(result.warnings, ())

    def test_warnings_below_1_2_0(self):
        for version in ("1.1.0", "1.0.0", "0.9.0", "1.1", "1.1.9"):
            with self.subTest(version=version):
                result = check(ANCHOR_DOC, version)
                self.assertEqual(result.errors, ())
                self.assertEqual(result.warnings, ("ROUTING_ANCHOR_UNSUPPORTED: anchor at line 3",))


class NonFindingTests(unittest.TestCase):
    def test_constructs_outside_model_routing_are_ignored(self):
        text = "other: &a\n  x: 1\ncopy: *a\nmodel_routing:\n  tier3:\n    model_family: f\n"
        result = check(text, "1.2.0")
        self.assertEqual((result.errors, result.warnings), ((), ()))

    def test_quoted_merge_key_and_markers_in_strings_and_comments(self):
        text = (
            'model_routing:\n  "<<": x\n  note: "uses &anchor and *alias"\n'
            "  other: 'a &b *c'  # &ignored *too\n"
        )
        result = check(text, "1.2.0")
        self.assertEqual((result.errors, result.warnings), ((), ()))

    def test_merge_marker_as_a_value_is_not_a_merge_key(self):
        result = check("model_routing:\n  a: <<\n", "1.2.0")
        self.assertEqual(result.errors, ())

    def test_nested_model_routing_key_is_not_the_top_level_one(self):
        result = check("outer:\n  model_routing:\n    a: &x 1\n", "1.2.0")
        self.assertEqual(result.errors, ())

    def test_empty_text_has_no_findings(self):
        result = check("", "1.2.0")
        self.assertEqual((result.errors, result.warnings, result.parse_error), ((), (), None))


class RobustnessTests(unittest.TestCase):
    def test_undefined_aliases_are_reported_without_raising(self):
        text = 'model_routing:\n  tier3: *tier3_default\n  stage: *stage_default\n'
        result = check(text, "1.2.0")
        self.assertEqual(
            result.errors,
            ("ROUTING_ANCHOR_UNSUPPORTED: alias at line 2", "ROUTING_ANCHOR_UNSUPPORTED: alias at line 3"),
        )
        self.assertIsNone(result.parse_error)

    def test_broken_yaml_sets_parse_error_and_does_not_raise(self):
        result = check("model_routing: [unclosed\n  a: : b\n", "1.2.0")
        self.assertIsInstance(result.parse_error, str)
        self.assertTrue(result.parse_error)

    def test_module_imports_standalone(self):
        src = str(Path(model_routing_yaml.__file__).resolve().parent.parent)
        env = {**os.environ, "PYTHONPATH": src}
        done = subprocess.run(
            [sys.executable, "-c", "import autoharness.model_routing_yaml"],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_module_has_no_io_surface(self):
        source = Path(model_routing_yaml.__file__).read_text(encoding="utf-8")
        for banned in ("open(", "subprocess", "socket", "environ", "getenv", "safe_load"):
            self.assertNotIn(banned, source)


if __name__ == "__main__":
    unittest.main()
