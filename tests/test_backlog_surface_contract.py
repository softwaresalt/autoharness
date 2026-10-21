"""Contract tests for 214.005-T: backlog CLI is a first-class peer of MCP (P-012 surface choice)."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

import yaml

from autoharness.backlog_surface_contract import (
    ToolUnavailable,
    ack_sequence,
    cli_command_path,
    parse_hook_poll,
    registry_cli_surface_errors,
    select_surface,
)
from autoharness.verify_workspace import verify_workspace

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_TEMPLATE_REGISTRY = _REPO_ROOT / "templates" / "backlog" / "registries" / "backlogit.registry.yaml"
_INSTALLED_REGISTRY = _REPO_ROOT / ".autoharness" / "backlog-registry.yaml"

POLL_CLI = "backlogit hooks poll --consumer-id {{consumer_id}}"
ACK_CLI = "backlogit hooks ack --consumer-id {{consumer_id}} --seq {{seq}}"


def _registry(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _inventory() -> set[str]:
    data = json.loads((_FIXTURES / "backlogit_command_inventory.json").read_text(encoding="utf-8"))
    return set(data["commands"])


def _poll_output() -> str:
    data = json.loads((_FIXTURES / "backlogit_hook_poll_output.json").read_text(encoding="utf-8"))
    return json.dumps(data["poll_output"])


class RegistryCliSurfaceTests(unittest.TestCase):
    def test_hook_operations_declare_exact_cli_commands(self) -> None:
        for path in (_TEMPLATE_REGISTRY, _INSTALLED_REGISTRY):
            with self.subTest(path=path.name):
                ops = _registry(path)["operations"]
                self.assertEqual(ops["poll_hook_events"]["cli_command"], POLL_CLI)
                self.assertEqual(ops["ack_hook_events"]["cli_command"], ACK_CLI)

    def test_every_cli_command_names_a_pinned_inventory_command(self) -> None:
        inventory = _inventory()
        for path in (_TEMPLATE_REGISTRY, _INSTALLED_REGISTRY):
            with self.subTest(path=path.name):
                for name, op in _registry(path)["operations"].items():
                    command = op.get("cli_command")
                    if command:
                        self.assertIn(cli_command_path(command), inventory, f"{name}: {command}")

    def test_registry_has_no_surface_contract_errors(self) -> None:
        for path in (_TEMPLATE_REGISTRY, _INSTALLED_REGISTRY):
            with self.subTest(path=path.name):
                self.assertEqual(registry_cli_surface_errors(_registry(path), _inventory()), [])

    def test_log_telemetry_stays_mcp_only_and_dispose_is_unregistered(self) -> None:
        for path in (_TEMPLATE_REGISTRY, _INSTALLED_REGISTRY):
            with self.subTest(path=path.name):
                ops = _registry(path)["operations"]
                self.assertNotIn("cli_command", ops["log_telemetry"])
                self.assertNotIn("dispose_shipment", ops)
        self.assertNotIn("shipment dispose", _inventory())

    def test_missing_hook_cli_command_fails(self) -> None:
        for operation in ("poll_hook_events", "ack_hook_events"):
            with self.subTest(operation=operation):
                registry = _registry(_TEMPLATE_REGISTRY)
                del registry["operations"][operation]["cli_command"]
                errors = registry_cli_surface_errors(registry)
                self.assertTrue(any(operation in error for error in errors), errors)

    def test_cli_command_absent_from_inventory_fails(self) -> None:
        registry = _registry(_TEMPLATE_REGISTRY)
        registry["operations"]["get_task"]["cli_command"] = "backlogit shipment dispose {{id}}"
        errors = registry_cli_surface_errors(registry, _inventory())
        self.assertTrue(any("get_task" in error for error in errors), errors)

    def test_log_telemetry_cli_and_dispose_registration_fail(self) -> None:
        registry = _registry(_TEMPLATE_REGISTRY)
        registry["operations"]["log_telemetry"]["cli_command"] = "backlogit telemetry list"
        registry["operations"]["dispose_shipment"] = {"mcp_tool": "backlogit_dispose_shipment"}
        errors = registry_cli_surface_errors(registry)
        self.assertTrue(any("log_telemetry" in error for error in errors), errors)
        self.assertTrue(any("dispose_shipment" in error for error in errors), errors)

    def test_cli_command_path_skips_flags_and_placeholders(self) -> None:
        self.assertEqual(cli_command_path(ACK_CLI), "hooks ack")
        self.assertEqual(cli_command_path("backlogit get {{id}}"), "get")
        self.assertEqual(cli_command_path("backlogit queue view"), "queue view")


class VerifyWorkspaceRegistryCheckTests(unittest.TestCase):
    def _verify(self, registry: dict) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            home = root / "home"
            schema = json.dumps({"$schema": "http://json-schema.org/draft-07/schema#", "type": "object"})
            for name, directory in (
                ("harness-manifest.schema.json", "harness-manifest"),
                ("harness-config.schema.json", "harness-config"),
                ("workspace-profile.schema.json", "workspace-profile"),
            ):
                (home / "schemas" / directory).mkdir(parents=True, exist_ok=True)
                (home / "schemas" / name).write_text(schema, encoding="utf-8")
                (home / "schemas" / directory / "1.0.0.schema.json").write_text(schema, encoding="utf-8")
            workspace = root / "workspace"
            files = {
                "harness-manifest.yaml": {
                    "schema_version": "1.0.0",
                    "installed_at": "2026-04-25T00:00:00Z",
                    "autoharness_version": "1.3.2",
                    "profile_hash": "abc",
                    "primitives_installed": [9],
                    "capability_packs": [],
                    "artifacts": [],
                },
                "config.yaml": {"schema_version": "1.0.0"},
                "workspace-profile.yaml": {"schema_version": "1.0.0"},
                "backlog-registry.yaml": registry,
            }
            for name, data in files.items():
                target = workspace / ".autoharness" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            return verify_workspace(workspace, home)["targeted_checks"]

    def test_rendered_registry_with_hook_cli_commands_passes(self) -> None:
        check = self._verify(_registry(_INSTALLED_REGISTRY))["backlog_registry_cli_surface"]
        self.assertTrue(check["ok"], check)

    def test_rendered_registry_lacking_hook_cli_command_fails(self) -> None:
        for operation in ("poll_hook_events", "ack_hook_events"):
            with self.subTest(operation=operation):
                registry = _registry(_INSTALLED_REGISTRY)
                del registry["operations"][operation]["cli_command"]
                check = self._verify(registry)["backlog_registry_cli_surface"]
                self.assertFalse(check["ok"])
                self.assertTrue(any(operation in error for error in check["errors"]))


class HookContractTests(unittest.TestCase):
    def test_poll_output_preserves_events_and_derived_signals(self) -> None:
        events, derived = parse_hook_poll(_poll_output())
        self.assertEqual([event["seq"] for event in events], [4, 7, 5])
        self.assertEqual(derived, [{"signal": "queue_changed", "seq": 99}])

    def test_poll_output_tolerates_log_lines_around_json(self) -> None:
        noisy = 'time=2026 level=INFO msg="workspace initialized"\n' + _poll_output()
        events, derived = parse_hook_poll(noisy)
        self.assertEqual(len(events), 3)
        self.assertEqual(len(derived), 1)

    def test_ack_is_limited_to_highest_concrete_event_sequence(self) -> None:
        events, derived = parse_hook_poll(_poll_output())
        self.assertEqual(ack_sequence(events), 7)
        self.assertNotEqual(ack_sequence(events), derived[0]["seq"])

    def test_no_ack_when_no_concrete_events(self) -> None:
        events, derived = parse_hook_poll(json.dumps({"events": [], "derived_signals": [{"seq": 3}]}))
        self.assertEqual(derived, [{"seq": 3}])
        self.assertIsNone(ack_sequence(events))

    def test_ack_ignores_non_integer_sequences(self) -> None:
        self.assertEqual(ack_sequence([{"seq": "9"}, {"seq": True}, {"seq": 2}, {}]), 2)

    def test_surface_selection_accepts_either_declared_working_surface(self) -> None:
        registry = _registry(_INSTALLED_REGISTRY)
        self.assertEqual(select_surface(registry, "poll_hook_events", ["cli"]), "cli")
        self.assertEqual(select_surface(registry, "poll_hook_events", ["mcp"]), "mcp")

    def test_mcp_only_operation_never_selects_cli(self) -> None:
        registry = _registry(_INSTALLED_REGISTRY)
        with self.assertRaises(ToolUnavailable):
            select_surface(registry, "log_telemetry", ["cli"])

    def test_neither_surface_declared_fails_closed(self) -> None:
        registry = {"operations": {"poll_hook_events": {"params": {"consumer_id": "consumer_id"}}}}
        with self.assertRaises(ToolUnavailable):
            select_surface(registry, "poll_hook_events", ["mcp", "cli"])
        with self.assertRaises(ToolUnavailable):
            select_surface(registry, "unknown_operation", ["mcp", "cli"])

    def test_no_working_declared_surface_fails_closed(self) -> None:
        registry = _registry(_INSTALLED_REGISTRY)
        with self.assertRaises(ToolUnavailable):
            select_surface(registry, "poll_hook_events", [])


_AGENTS = ("_stage", "_ship", "_orchestrator")
_STATIC_TARGETS = (
    *(_REPO_ROOT / "templates" / "agents" / f"{name}.agent.md.tmpl" for name in _AGENTS),
    *(_REPO_ROOT / ".github" / "agents" / f"{name}.agent.md" for name in _AGENTS),
    _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl",
    _REPO_ROOT / ".github" / "policies" / "workflow-policies.md",
    _REPO_ROOT / "templates" / "instructions" / "backlogit.instructions.md.tmpl",
    _REPO_ROOT / "templates" / "instructions" / "backlog-integration.instructions.md.tmpl",
    _REPO_ROOT / ".github" / "instructions" / "backlogit.instructions.md",
)

_CLI_ONLY_ON_MCP_FAILURE = (
    re.compile(r"registry declares a CLI fallback", re.IGNORECASE),
    re.compile(r"If CLI fallback exists", re.IGNORECASE),
    re.compile(r"using CLI fallback", re.IGNORECASE),
    re.compile(r"On failure: run (the CLI fallback|`backlogit sync`)", re.IGNORECASE),
    re.compile(r"CLI (only|solely) (on|when|if) (the )?MCP", re.IGNORECASE),
)


class NoCliOnlyOnMcpFailureWordingTests(unittest.TestCase):
    def test_templates_do_not_restate_cli_only_on_mcp_failure(self) -> None:
        for path in _STATIC_TARGETS:
            text = path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
            for pattern in _CLI_ONLY_ON_MCP_FAILURE:
                with self.subTest(path=path.name, pattern=pattern.pattern):
                    self.assertIsNone(pattern.search(text))

    def test_pipeline_agents_name_surface_choice_and_report_tokens(self) -> None:
        for path in _STATIC_TARGETS[:6]:
            text = path.read_bytes().decode("utf-8")
            with self.subTest(path=path.name):
                self.assertIn("TOOL_OK: {operation} via {mcp|cli}", text)
                self.assertIn("equal supported surface", text)
                self.assertIn("TOOL_UNAVAILABLE", text)


if __name__ == "__main__":
    unittest.main()
