"""Shared raw-YAML guard: anchors, aliases, and merge keys under `model_routing`.

Loading YAML into data resolves these constructs at parse time, so the prohibition
(040-DL D2, D9) can only be enforced on the raw text before loading. This is
the single scanner; the `routing resolve` CLI and `verify-workspace` both
call it. It walks the parser event stream and is pure over text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import yaml

ROUTING_KEY = "model_routing"
FINDING_CODE = "ROUTING_ANCHOR_UNSUPPORTED"
ENFORCED_FROM = (1, 2, 0)


@dataclass(frozen=True)
class YamlGuardResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    parse_error: str | None


def _enforced(schema_version: str | None) -> bool:
    """Fail closed: enforce unless the declared version is parsable and below 1.2.0."""
    if not isinstance(schema_version, str) or not re.fullmatch(r"\d+(\.\d+)*", schema_version.strip()):
        return True
    parts = tuple(int(part) for part in schema_version.strip().split("."))
    padded = parts + (0,) * (len(ENFORCED_FROM) - len(parts))
    return padded >= ENFORCED_FROM


def _scan(raw_text: str) -> tuple[list[str], str | None]:
    findings: list[str] = []
    stack: list[dict[str, Any]] = []
    in_target_depth = 0
    pending_target = False

    def flag(kind: str, event: Any) -> None:
        findings.append(f"{FINDING_CODE}: {kind} at line {event.start_mark.line + 1}")

    try:
        for event in yaml.parse(raw_text):
            if isinstance(event, (yaml.DocumentStartEvent, yaml.DocumentEndEvent)):
                stack, in_target_depth, pending_target = [], 0, False
                continue
            if isinstance(event, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                stack.pop()
                if in_target_depth and len(stack) < in_target_depth:
                    in_target_depth = 0
                continue
            if not isinstance(
                event,
                (yaml.ScalarEvent, yaml.AliasEvent, yaml.MappingStartEvent, yaml.SequenceStartEvent),
            ):
                continue

            parent = stack[-1] if stack else None
            is_key = bool(parent and parent["map"] and parent["key_turn"])
            if parent and parent["map"]:
                parent["key_turn"] = not parent["key_turn"]
            is_root_value = bool(parent and parent["map"] and len(stack) == 1 and not is_key)
            starts_target = is_root_value and pending_target
            if parent and len(stack) == 1 and is_key:
                pending_target = isinstance(event, yaml.ScalarEvent) and event.value == ROUTING_KEY
            elif is_root_value:
                pending_target = False

            inside = bool(in_target_depth) or starts_target
            if inside:
                if isinstance(event, yaml.AliasEvent):
                    flag("alias", event)
                else:
                    if getattr(event, "anchor", None):
                        flag("anchor", event)
                    if is_key and isinstance(event, yaml.ScalarEvent) and event.style is None and event.value == "<<":
                        flag("merge_key", event)

            if isinstance(event, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
                stack.append({"map": isinstance(event, yaml.MappingStartEvent), "key_turn": True})
                if starts_target:
                    in_target_depth = len(stack)
    except yaml.YAMLError as exc:
        message = str(exc).strip().splitlines()
        return findings, (message[0] if message else type(exc).__name__)
    return findings, None


def check_model_routing_yaml(raw_text: str, schema_version: str | None) -> YamlGuardResult:
    """Scan raw YAML text; findings are errors at schema 1.2.0+ (or unknown), warnings below."""
    findings, parse_error = _scan(raw_text)
    if _enforced(schema_version):
        return YamlGuardResult(tuple(findings), (), parse_error)
    return YamlGuardResult((), tuple(findings), parse_error)
