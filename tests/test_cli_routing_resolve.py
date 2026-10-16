"""A4 (214-S): the read-only, fail-closed `autoharness routing resolve` CLI."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness import cli, model_routing_yaml

DOCUMENT_KEYS = {
    "schema_version",
    "site",
    "kind",
    "resolved",
    "resolution_chain",
    "degraded",
    "errors",
    "exit_code",
}

CONFIG = """\
schema_version: "{version}"
model_routing:
  tier1: {{model: haiku, model_family: haiku, model_provider: anthropic, reasoning_effort: low}}
  tier2: {{model: sonnet, model_family: sonnet, model_provider: anthropic, reasoning_effort: medium, context_tier: long_context}}
  tier3: {{model: opus, model_family: opus, model_provider: anthropic, reasoning_effort: high}}
  stage: {{model_family: opus, model_provider: anthropic, reasoning_effort: xhigh}}
  ship:
    model_family: sonnet
    model_provider: anthropic
    reasoning_effort: medium
    context_tier: long_context
    escalation: {{model_family: gpt-x, model_provider: openai, reasoning_effort: high}}
"""

SAME_ROUTE_CONFIG = """\
schema_version: "1.1.0"
model_routing:
  tier3: {model: opus, model_family: opus, model_provider: anthropic, reasoning_effort: high}
  stage: {model_family: opus, model_provider: anthropic, reasoning_effort: high}
  escalation: {model_family: opus, model_provider: anthropic, reasoning_effort: high}
"""

ALIASED_BODY = """\
model_routing:
  tier3: {model: opus, model_family: opus, model_provider: &p anthropic, reasoning_effort: high}
  stage: {model_family: opus, model_provider: *p, reasoning_effort: high}
"""

MERGED_BODY = """\
model_routing:
  tier3: {model: opus, model_family: opus, model_provider: anthropic, reasoning_effort: high}
  stage:
    <<: {model_family: opus, model_provider: anthropic}
    reasoning_effort: high
"""

PLAIN_BODY = """\
model_routing:
  tier3: {model: opus, model_family: opus, model_provider: anthropic, reasoning_effort: high}
  stage: {model_family: opus, model_provider: anthropic, reasoning_effort: high}
"""


def run_cli(argv):
    out, err = io.BytesIO(), io.BytesIO()
    stdout = io.TextIOWrapper(out, encoding="utf-8", newline="")
    stderr = io.TextIOWrapper(err, encoding="utf-8", newline="")
    status = 0
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            cli.main(argv)
        except SystemExit as exit_:
            status = exit_.code if isinstance(exit_.code, int) else (0 if exit_.code is None else 1)
        finally:
            stdout.flush()
            stderr.flush()
    return status, out.getvalue(), err.getvalue()


def snapshot(root: Path):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class RoutingResolveCliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ws = Path(self._tmp.name)

    def write_config(self, text, workspace=None):
        root = workspace or self.ws
        (root / ".autoharness").mkdir(parents=True, exist_ok=True)
        (root / ".autoharness" / "config.yaml").write_text(text, encoding="utf-8")

    def resolve(self, site, *extra, workspace=None):
        argv = ["routing", "resolve", "--workspace", str(workspace or self.ws), "--site", site, *extra, "--json"]
        before = snapshot(workspace or self.ws)
        status, out, err = run_cli(argv)
        self.assertEqual(snapshot(workspace or self.ws), before, "the command must be read-only")
        self.assertEqual(err, b"", "nothing on stderr after a successful parse")
        self.assertTrue(out.endswith(b"\n") and not out.endswith(b"\n\n"))
        document = json.loads(out.decode("utf-8"))
        self.assertEqual(set(document), DOCUMENT_KEYS)
        self.assertEqual(document["exit_code"], status)
        self.assertEqual(document["schema_version"], "1.0.0")
        return status, document

    def test_stage_ship_orchestrator_and_escalation_tuples(self):
        self.write_config(CONFIG.format(version="1.1.0"))
        status, stage = self.resolve("stage")
        self.assertEqual(status, 0)
        self.assertEqual(
            stage["resolved"],
            {
                "model_family": "opus",
                "model_provider": "anthropic",
                "reasoning_effort": "xhigh",
                "context_tier": "default",
                "tier_class": "tier3",
            },
        )
        self.assertEqual(stage["site"], "stage")
        self.assertEqual(stage["kind"], "route")
        self.assertEqual((stage["degraded"], stage["errors"]), ([], []))

        _, ship = self.resolve("ship")
        self.assertEqual(ship["resolved"]["context_tier"], "long_context")
        _, orchestrator = self.resolve("orchestrator")
        self.assertEqual(orchestrator["resolved"]["model_provider"], "anthropic")
        status, escalation = self.resolve("ship", "--kind", "escalation")
        self.assertEqual(status, 0)
        self.assertEqual(escalation["kind"], "escalation")
        self.assertEqual(escalation["resolved"]["model_family"], "gpt-x")

    def test_same_route_escalation_exits_one_with_degraded(self):
        self.write_config(SAME_ROUTE_CONFIG)
        status, document = self.resolve("stage", "--kind", "escalation")
        self.assertEqual(status, 1)
        self.assertEqual(document["degraded"], ["ESCALATION_DEGRADED: same-route"])
        self.assertEqual(document["errors"], [])

    def test_missing_empty_versionless_unparseable_and_invalid_configs_exit_two(self):
        cases = {
            "missing": None,
            "empty": "",
            "versionless": "model_routing:\n  tier3: {model: opus, model_family: opus}\n",
            "unparseable": "model_routing: [unclosed\n  a: : b\n",
            "schema-invalid": 'schema_version: "1.1.0"\nmodel_routing: oops\n',
            "not-a-mapping": "- a\n- b\n",
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    if text is not None:
                        self.write_config(text, workspace)
                    status, document = self.resolve("stage", workspace=workspace)
                    self.assertEqual(status, 2)
                    self.assertTrue(document["errors"])
                    self.assertEqual(document["resolved"]["model_family"], "")

    def test_unknown_schema_version_exits_two_with_a_document(self):
        self.write_config('schema_version: "9.9.9"\nmodel_routing: {tier3: {model: opus, model_family: opus}}\n')
        status, document = self.resolve("stage")
        self.assertEqual(status, 2)
        self.assertTrue(document["errors"])

    def test_schema_resolution_failure_exits_two_with_a_document(self):
        self.write_config(CONFIG.format(version="1.1.0"))
        with mock.patch("autoharness.verify_workspace._schema_errors", side_effect=OSError("boom")):
            status, document = self.resolve("stage")
        self.assertEqual(status, 2)
        self.assertEqual(document["errors"], ["CONFIG_SCHEMA_UNAVAILABLE: OSError"])

    def _link_or_skip(self, link, target, is_dir):
        try:
            link.symlink_to(target, target_is_directory=is_dir)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this platform/privilege level")

    def test_symlinked_config_file_escaping_workspace_exits_two(self):
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "config.yaml"
            external.write_text(CONFIG.format(version="1.1.0"), encoding="utf-8")
            (self.ws / ".autoharness").mkdir()
            self._link_or_skip(self.ws / ".autoharness" / "config.yaml", external, False)
            status, document = self.resolve("stage")
        self.assertEqual(status, 2)
        self.assertTrue(document["errors"][0].startswith("CONFIG_UNREADABLE"))

    def test_symlinked_autoharness_directory_escaping_workspace_exits_two(self):
        with tempfile.TemporaryDirectory() as outside:
            (Path(outside) / "config.yaml").write_text(CONFIG.format(version="1.1.0"), encoding="utf-8")
            self._link_or_skip(self.ws / ".autoharness", Path(outside), True)
            status, document = self.resolve("stage")
        self.assertEqual(status, 2)
        self.assertTrue(document["errors"][0].startswith("CONFIG_UNREADABLE"))

    def test_unresolved_family_exits_two(self):
        self.write_config('schema_version: "1.1.0"\nmodel_routing: {}\n')
        status, document = self.resolve("stage")
        self.assertEqual(status, 2)
        self.assertEqual(document["errors"], ["ROUTING_UNRESOLVED: model_family"])

    def test_orchestrator_escalation_is_unsupported_exit_two(self):
        self.write_config(CONFIG.format(version="1.1.0"))
        status, document = self.resolve("orchestrator", "--kind", "escalation")
        self.assertEqual(status, 2)
        self.assertTrue(document["errors"][0].startswith("UNSUPPORTED"))


class AnchorGuardTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ws = Path(self._tmp.name)

    def run_with(self, version, body):
        (self.ws / ".autoharness").mkdir(parents=True, exist_ok=True)
        (self.ws / ".autoharness" / "config.yaml").write_text(
            f'schema_version: "{version}"\n{body}', encoding="utf-8"
        )
        status, out, err = run_cli(
            ["routing", "resolve", "--workspace", str(self.ws), "--site", "stage", "--json"]
        )
        self.assertEqual(err, b"")
        return status, json.loads(out.decode("utf-8"))

    def test_1_2_0_with_alias_or_merge_key_exits_two_with_the_named_code(self):
        for name, body in (("alias", ALIASED_BODY), ("merge", MERGED_BODY)):
            with self.subTest(construct=name):
                status, document = self.run_with("1.2.0", body)
                self.assertEqual(status, 2)
                self.assertTrue(any(e.startswith("ROUTING_ANCHOR_UNSUPPORTED") for e in document["errors"]))

    def test_1_1_0_with_aliases_is_not_rejected_and_matches_the_dealiased_config(self):
        for name, body in (("alias", ALIASED_BODY), ("merge", MERGED_BODY)):
            with self.subTest(construct=name):
                status, document = self.run_with("1.1.0", body)
                plain_status, plain = self.run_with("1.1.0", PLAIN_BODY)
                self.assertEqual((status, plain_status), (0, 0))
                self.assertEqual(document, plain)

    def test_command_delegates_to_the_shared_guard_and_has_no_scanner_of_its_own(self):
        with mock.patch.object(
            model_routing_yaml, "check_model_routing_yaml", wraps=model_routing_yaml.check_model_routing_yaml
        ) as spy:
            self.run_with("1.2.0", PLAIN_BODY)
        self.assertEqual(spy.call_count, 1)
        raw_text, version = spy.call_args.args
        self.assertIn("model_routing", raw_text)
        self.assertEqual(version, "1.2.0")
        source = Path(cli.__file__).read_text(encoding="utf-8")
        for needle in ("yaml.parse", "AliasEvent", "ROUTING_ANCHOR"):
            self.assertNotIn(needle, source)


class ArgumentTests(unittest.TestCase):
    def test_argument_errors_exit_two_with_usage_and_no_document(self):
        for argv in (
            ["routing", "resolve", "--site", "stage", "--json"],
            ["routing", "resolve", "--workspace", "x", "--json"],
            ["routing", "resolve", "--workspace", "x", "--site", "stage"],
            ["routing", "resolve", "--workspace", "x", "--site", "bogus", "--json"],
            ["routing", "resolve", "--workspace", "", "--site", "stage", "--json"],
            ["routing", "resolve", "--workspace", "x", "--site", "stage", "--kind", "nope", "--json"],
            ["routing", "resolve", "--workspace", "x", "--sit", "stage", "--json"],
        ):
            with self.subTest(argv=argv):
                status, out, err = run_cli(argv)
                self.assertEqual(status, 2)
                self.assertEqual(out, b"")
                self.assertIn(b"usage", err.lower())

    def test_usage_lists_the_command(self):
        self.assertIn("autoharness routing resolve", cli.USAGE)


if __name__ == "__main__":
    unittest.main()
