"""Backlog operation surface contract (P-012 per-operation surface choice).

Declared MCP and CLI surfaces are equal supported surfaces per operation. This module holds the
deterministic parts of that contract: registry verification, surface selection that fails closed,
and the hook poll/ack rules (acknowledge only the highest concrete event sequence).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

REQUIRED_HOOK_CLI_COMMANDS = {
    "poll_hook_events": "backlogit hooks poll --consumer-id {{consumer_id}}",
    "ack_hook_events": "backlogit hooks ack --consumer-id {{consumer_id}} --seq {{seq}}",
}
MCP_ONLY_OPERATIONS = ("log_telemetry",)
UNREGISTERED_OPERATIONS = ("dispose_shipment",)


class ToolUnavailable(Exception):
    """No declared surface of an operation works (reported as TOOL_UNAVAILABLE)."""


def cli_command_path(cli_command: str, binary: str = "backlogit") -> str:
    """Return the command path (for example `hooks ack`) of a cli_command template."""
    tokens = cli_command.split()
    if tokens and tokens[0] == binary:
        tokens = tokens[1:]
    path: list[str] = []
    for token in tokens:
        if token.startswith("-") or token.startswith("{{"):
            break
        path.append(token)
    return " ".join(path)


def registry_cli_surface_errors(
    registry: dict[str, Any], inventory: Iterable[str] | None = None
) -> list[str]:
    operations = registry.get("operations") or {}
    errors: list[str] = []
    for name, expected in REQUIRED_HOOK_CLI_COMMANDS.items():
        declared = (operations.get(name) or {}).get("cli_command")
        if declared != expected:
            errors.append(f"{name}: cli_command must be `{expected}` (found {declared!r})")
    for name in MCP_ONLY_OPERATIONS:
        if (operations.get(name) or {}).get("cli_command"):
            errors.append(f"{name}: is MCP-only and must not declare cli_command")
    for name in UNREGISTERED_OPERATIONS:
        if name in operations:
            errors.append(f"{name}: must not be registered (not implemented in backlogit)")
    if inventory is not None:
        known = set(inventory)
        binary = str((registry.get("cli") or {}).get("binary") or "backlogit")
        for name, operation in operations.items():
            command = (operation or {}).get("cli_command")
            if command and cli_command_path(str(command), binary) not in known:
                errors.append(f"{name}: cli_command `{command}` is not in the pinned command inventory")
    return errors


def select_surface(registry: dict[str, Any], operation: str, working: Iterable[str]) -> str:
    """Pick a working declared surface (`mcp` or `cli`); fail closed when none exists."""
    declared = (registry.get("operations") or {}).get(operation) or {}
    available = set(working)
    for surface, key in (("mcp", "mcp_tool"), ("cli", "cli_command")):
        if declared.get(key) and surface in available:
            return surface
    raise ToolUnavailable(f"TOOL_UNAVAILABLE: {operation}")


def parse_hook_poll(output: str) -> tuple[list[dict[str, Any]], list[Any]]:
    """Parse poll output into (events, derived_signals), preserving both."""
    start = output.find("{")
    data = json.JSONDecoder().raw_decode(output[start:])[0] if start >= 0 else {}
    return list(data.get("events") or []), list(data.get("derived_signals") or [])


def ack_sequence(events: Iterable[dict[str, Any]]) -> int | None:
    """Highest concrete event sequence, or None when there is nothing to acknowledge."""
    sequences = [
        event["seq"]
        for event in events
        if isinstance(event.get("seq"), int) and not isinstance(event.get("seq"), bool)
    ]
    return max(sequences) if sequences else None
