"""Deterministic workspace verification for installed autoharness artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator

from autoharness.schema_contracts import (
    classify_schema_error,
    collect_contract_state_warnings,
    plan_schema_contract_migrations,
    resolve_contract_schema_path,
    summarize_schema_contract,
)


PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")
CODE_FENCE_RE = re.compile(r"^\s*```")
SUPPORTED_CAPABILITY_PACKS = {
    "agent-intercom",
    "agent-engram",
    "backlogit",
    "browser-verification",
    "continuous-learning",
    "strict-safety",
    "release-observability",
    "adversarial-review",
}
WORKSPACE_SOURCE_TEMPLATES = {
    "workspace merge install",
    "workspace deliberation template",
}
DEFAULT_SUFFIXES = {
    "feature": "F",
    "chore": "C",
    "task": "T",
    "spike": "SP",
    "deliberation": "D",
    "bug": "B",
    "epic": "E",
    "subtask": "ST",
    "shipment": "S",
}
OPERATION_VARIABLES = {
    "create_task": "OP_CREATE_MCP",
    "list_tasks": "OP_LIST_MCP",
    "get_task": "OP_GET_MCP",
    "update_task": "OP_UPDATE_MCP",
    "move_task": "OP_MOVE_MCP",
    "search_tasks": "OP_SEARCH_MCP",
    "complete_task": "OP_COMPLETE_MCP",
    "create_shipment": "OP_CREATE_SHIPMENT_MCP",
    "get_shipment": "OP_GET_SHIPMENT_MCP",
    "list_shipments": "OP_LIST_SHIPMENTS_MCP",
    "claim_shipment": "OP_CLAIM_SHIPMENT_MCP",
    "ship_shipment": "OP_SHIP_SHIPMENT_MCP",
    "add_to_shipment": "OP_ADD_TO_SHIPMENT_MCP",
    "return_blocked": "OP_RETURN_BLOCKED_MCP",
    "create_checkpoint": "OP_CREATE_CHECKPOINT_MCP",
    "list_checkpoints": "OP_LIST_CHECKPOINTS_MCP",
    "get_checkpoint": "OP_GET_CHECKPOINT_MCP",
    "resolve_checkpoint": "OP_RESOLVE_CHECKPOINT_MCP",
    "poll_hook_events": "OP_POLL_HOOK_EVENTS_MCP",
    "ack_hook_events": "OP_ACK_HOOK_EVENTS_MCP",
}
CLI_OPERATION_VARIABLES = {
    "create_task": "OP_CREATE_CLI",
    "list_tasks": "OP_LIST_CLI",
    "get_task": "OP_GET_CLI",
    "update_task": "OP_UPDATE_CLI",
    "move_task": "OP_MOVE_CLI",
    "search_tasks": "OP_SEARCH_CLI",
    "complete_task": "OP_COMPLETE_CLI",
}
STATUS_VARIABLES = {
    "STATUS_QUEUED": ("queued", "todo"),
    "STATUS_ACTIVE": ("active", "in_progress"),
    "STATUS_DONE": ("done",),
    "STATUS_BLOCKED": ("blocked",),
}
CORE_OPERATIONS = {
    "create_task",
    "list_tasks",
    "get_task",
    "update_task",
    "move_task",
    "delete_task",
    "search_tasks",
    "complete_task",
}
FIELD_VARIABLES = {
    "FIELD_TASK_ID": ("task_id", "id"),
    "FIELD_TITLE": ("title",),
    "FIELD_STATUS": ("status",),
    "FIELD_LABELS": ("labels",),
    "FIELD_PARENT_ID": ("parent_id",),
    "FIELD_TYPE": ("item_type", "artifact_type", "type"),
    "FIELD_DESCRIPTION": ("description",),
}
PACK_ASSERTIONS = {
    "backlogit": [
        {
            "key": "backlogit_instruction_guidance",
            "path": ".github/instructions/backlogit.instructions.md",
            "must_contain": ["checkpoint", "queue", "traceability"],
        },
        {
            "key": "backlogit_sql_schema_instruction",
            "path": ".github/instructions/backlogit-sql-schema.instructions.md",
            "must_contain": ["backlogit_query_sql", "stash_entries", "SELECT"],
        },
        {
            "key": "backlogit_yaml_header_instruction",
            "path": ".github/instructions/backlogit-yaml-header-tooling.instructions.md",
            "must_contain": ["custom_fields", "references", "backlogit_update_item"],
        },
        {
            "key": "agents_metadata_catalog_guidance",
            "path": "AGENTS.md",
            "must_contain": [
                "backlogit_get_metadata_catalog",
                "backlogit_export_command_map",
            ],
        },
        {
            "key": "ship_source_artifact_cleanup",
            "path": ".github/agents/ship.agent.md",
            "must_contain": [
                "source_stash_id",
                "source_deliberation_id",
                "backlogit_stash_remove",
                "backlogit_archive_item",
            ],
        },
        {
            "key": "closure_source_artifact_cleanup",
            "path": ".github/skills/operational-closure/SKILL.md",
            "must_contain": [
                "Source artifact cleanup",
                "source_stash_id",
                "source_deliberation_id",
            ],
        },
    ],
    "strict-safety": [
        {
            "key": "strict_safety_instruction",
            "path": ".github/instructions/strict-safety.instructions.md",
            "must_contain": ["ProposedAction", "ActionRisk", "ActionResult"],
        }
    ],
    "agent-intercom": [
        {
            "key": "agent_intercom_instruction",
            "path": ".github/instructions/agent-intercom.instructions.md",
            "must_contain": ["broadcast", "approval", "standby"],
        },
        {
            "key": "review_intercom_workflow",
            "path": ".github/skills/review/SKILL.md",
            "must_contain": [
                "Agent-Intercom Communication (NON-NEGOTIABLE)",
                "Review written",
                "Waiting for input",
            ],
            "must_precede": [
                [
                    "## Agent-Intercom Communication (NON-NEGOTIABLE)",
                    "## Subagent Depth Constraint",
                ]
            ],
        }
    ],
    "agent-engram": [
        {
            "key": "agent_engram_instruction",
            "path": ".github/instructions/agent-engram.instructions.md",
            "must_contain": ["unified_search", "map_code", "impact_analysis"],
        }
    ],
    "adversarial-review": [
        {
            "key": "adversarial_review_instruction",
            "path": ".github/instructions/adversarial-review.instructions.md",
            "must_contain": ["confidence", "reviewers", "consensus"],
        }
    ],
    "release-observability": [
        {
            "key": "release_observability_instruction",
            "path": ".github/instructions/release-observability.instructions.md",
            "must_contain": ["monitoring", "rollback", "observation window"],
        }
    ],
    "browser-verification": [
        {
            "key": "browser_verification_instruction",
            "path": ".github/instructions/browser-verification.instructions.md",
            "must_contain": ["headed", "headless", "route"],
        }
    ],
    "continuous-learning": [
        {
            "key": "continuous_learning_instruction",
            "path": ".github/instructions/continuous-learning.instructions.md",
            "must_contain": ["observe", "learn", "evolve"],
        }
    ],
}
FOUNDATION_ASSERTIONS = [
    {
        "key": "copilot_durable_knowledge_layout",
        "path": ".github/copilot-instructions.md",
        "must_contain": [
            "Reusable learnings and hard-won fixes",
            "Session memory and checkpoints",
            "Graduated architecture and design rationale",
        ],
    },
    {
        "key": "copilot_session_memory_guidance",
        "path": ".github/copilot-instructions.md",
        "must_contain": [
            "## Session Memory Requirements",
            "65%",
            "phase or major task group",
        ],
    },
    {
        "key": "copilot_remote_operator_guidance",
        "path": ".github/copilot-instructions.md",
        "must_contain": [
            "## Remote Operator Integration",
            "### agent-intercom",
            "### agent-engram",
            "ping-loop.prompt.md",
            "sync_workspace",
        ],
    },
    {
        "key": "copilot_backlog_workflow_expectations",
        "path": ".github/copilot-instructions.md",
        "must_contain": [
            "queue-aware and dependency-aware operations",
            "commit-tracking",
            "parallel markdown trackers",
        ],
    },
    {
        "key": "stage_shipment_determinism",
        "path": ".github/agents/stage.agent.md",
        "must_contain": [
            "Step Sequence Contract (NON-NEGOTIABLE)",
            "Shipment Assembly (NON-NEGOTIABLE when shipments are supported)",
            "Pre-Summary Verification Gate (NON-NEGOTIABLE)",
            "Never skip shipment assembly",
        ],
    },
    {
        "key": "ship_branch_management",
        "path": ".github/agents/ship.agent.md",
        "must_contain": [
            "Branch retention (NON-NEGOTIABLE)",
            "Post-Merge Branch Protocol (NON-NEGOTIABLE)",
            "Branch Management Rules (NON-NEGOTIABLE)",
            "post-merge/{feature_slug}",
        ],
    },
    {
        "key": "pr_lifecycle_branch_retention",
        "path": ".github/skills/pr-lifecycle/SKILL.md",
        "must_contain": [
            "Branch retention (NON-NEGOTIABLE)",
            "Do NOT checkout",
            "post-merge/",
        ],
    },
    {
        "key": "auto_tune_learning_loop_contract",
        "path": ".github/agents/auto-tune.agent.md",
        "must_contain": [
            "Step 1.8",
            "compound library",
            "continuous-learning",
            "closure artifacts",
            "learning_signals{}",
        ],
    },
    {
        "key": "tune_harness_learning_loop_contract",
        "path": ".github/skills/tune-harness/SKILL.md",
        "must_contain": [
            "#### Step 1.8: Mine Learning Signals for Improvement Proposals",
            "produced by compound, continuous-learning, and closure systems",
            "learning_signals{}",
            "Learning-driven proposals",
        ],
    },
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_yaml_file(path: Path) -> Any:
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    return {} if data is None else data


def _schema_errors(schema_path: Path, data: Any) -> list[str]:
    if not schema_path.exists():
        return [f"schema file is missing: {schema_path}"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path)
        location = path if path else "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def _warning_group_key(warning: dict[str, Any]) -> tuple[Any, ...]:
    return (
        warning.get("kind"),
        warning.get("path"),
        warning.get("contract"),
        warning.get("current_version"),
        warning.get("suggested_action"),
    )


def _summarize_warnings(warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    order: list[tuple[Any, ...]] = []

    for warning in warnings:
        key = _warning_group_key(warning)
        if key not in grouped:
            grouped_warning = dict(warning)
            grouped_warning["occurrence_count"] = 1
            field = warning.get("field")
            if field is not None:
                grouped_warning["fields"] = [str(field)]
            legacy_value = warning.get("legacy_value")
            if legacy_value is not None:
                grouped_warning["legacy_values"] = [str(legacy_value)]
            grouped[key] = grouped_warning
            order.append(key)
            continue

        grouped_warning = grouped[key]
        grouped_warning["occurrence_count"] += 1

        field = warning.get("field")
        if field is not None:
            field_text = str(field)
            fields = grouped_warning.setdefault("fields", [])
            if field_text not in fields:
                fields.append(field_text)

        legacy_value = warning.get("legacy_value")
        if legacy_value is not None:
            legacy_value_text = str(legacy_value)
            legacy_values = grouped_warning.setdefault("legacy_values", [])
            if legacy_value_text not in legacy_values:
                legacy_values.append(legacy_value_text)

    summarized: list[dict[str, Any]] = []
    for key in order:
        grouped_warning = grouped[key]
        if grouped_warning["occurrence_count"] == 1:
            grouped_warning.pop("occurrence_count", None)
            grouped_warning.pop("fields", None)
            grouped_warning.pop("legacy_values", None)
        else:
            grouped_warning.pop("field", None)
            grouped_warning.pop("legacy_value", None)
            contract_name = grouped_warning.get("contract") or grouped_warning.get("kind")
            grouped_warning["message"] = (
                f"Grouped compatibility drift for {contract_name} with repeated {grouped_warning['kind']} findings."
            )
        summarized.append(grouped_warning)

    return summarized


def _normalize_stage_path(staging_dir: Path, relative_path: str) -> Path:
    return staging_dir / Path(relative_path.replace("/", "/"))


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _render_template(content: str, variables: dict[str, str]) -> str:
    rendered = content
    for key, value in variables.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def _find_unresolved_placeholders(file_path: Path) -> list[dict[str, Any]]:
    unresolved: list[dict[str, Any]] = []
    in_code_fence = False
    for line_number, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        if CODE_FENCE_RE.match(line):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        for match in PLACEHOLDER_RE.finditer(line):
            unresolved.append(
                {
                    "path": str(file_path),
                    "line": line_number,
                    "placeholder": match.group(0),
                }
            )
    return unresolved


def _extract_markdown_frontmatter(file_path: Path) -> dict[str, Any]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    closing_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        return {}

    try:
        data = yaml.safe_load("\n".join(lines[1:closing_index]))
    except yaml.YAMLError:
        return {}

    return data if isinstance(data, dict) else {}


def _normalize_text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        normalized = []
        for item in value:
            item_text = str(item).strip()
            if item_text:
                normalized.append(item_text)
        return normalized
    return []


def _relative_workspace_path(workspace_path: Path, file_path: Path) -> str:
    try:
        return file_path.relative_to(workspace_path).as_posix()
    except ValueError:
        return file_path.as_posix()


def _empty_learning_signals() -> dict[str, list[dict[str, Any]]]:
    return {
        "compound_patterns": [],
        "promotion_candidates": [],
        "observation_patterns": [],
        "closure_patterns": [],
    }


def _iter_signal_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []

    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".yaml", ".yml"}
    )


def _load_structured_signal_file(file_path: Path) -> dict[str, Any]:
    try:
        if file_path.suffix.lower() == ".json":
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        if file_path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        if file_path.suffix.lower() == ".md":
            return _extract_markdown_frontmatter(file_path)
    except (json.JSONDecodeError, OSError, yaml.YAMLError):
        return {}

    return {}


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, list):
        return len(value)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.isdigit():
            return int(normalized)
    return None


def _normalize_signal_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _extract_signal_timestamp(file_path: Path, metadata: dict[str, Any]) -> str:
    for key in (
        "recorded_at",
        "generated_at",
        "tuned_at",
        "created_at",
        "timestamp",
        "date",
        "first_seen",
        "last_seen",
    ):
        value = _normalize_signal_text(metadata.get(key))
        if value:
            return value

    try:
        return datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
    except OSError:
        return ""


def _timestamp_bounds(values: list[str]) -> tuple[str, str]:
    normalized = sorted(value for value in values if value)
    if not normalized:
        return "", ""
    return normalized[0], normalized[-1]


def _mine_compound_patterns(
    workspace_path: Path,
    compound_dir: Path,
    affected_artifacts: list[str],
) -> list[dict[str, Any]]:
    compound_patterns: list[dict[str, Any]] = []
    compound_files = _iter_signal_files(compound_dir)
    if len(compound_files) < 3:
        return compound_patterns

    root_causes: dict[str, list[str]] = {}
    categories: dict[str, list[str]] = {}
    components: dict[str, list[str]] = {}
    tag_refs: dict[str, list[str]] = {}
    tag_categories: dict[str, set[str]] = {}
    high_severity_refs: list[str] = []
    parsed_entries = 0

    for file_path in compound_files:
        frontmatter = _extract_markdown_frontmatter(file_path)
        if not frontmatter:
            continue

        parsed_entries += 1
        relative_path = _relative_workspace_path(workspace_path, file_path)

        root_cause = _normalize_signal_text(frontmatter.get("root_cause"))
        if root_cause:
            root_causes.setdefault(root_cause, []).append(relative_path)

        category = _normalize_signal_text(frontmatter.get("category"))
        if category:
            categories.setdefault(category, []).append(relative_path)

        component = _normalize_signal_text(frontmatter.get("component"))
        if component:
            components.setdefault(component, []).append(relative_path)

        for tag in _normalize_text_list(frontmatter.get("tags")):
            tag_refs.setdefault(tag, []).append(relative_path)
            if category:
                tag_categories.setdefault(tag, set()).add(category)

        severity = _normalize_signal_text(frontmatter.get("severity")).lower()
        if severity in {"critical", "high"}:
            high_severity_refs.append(relative_path)

    if parsed_entries < 3:
        return compound_patterns

    for root_cause, evidence_refs in sorted(root_causes.items()):
        if len(evidence_refs) < 3:
            continue
        compound_patterns.append(
            {
                "pattern_type": "recurring_root_cause",
                "key": root_cause,
                "evidence_count": len(evidence_refs),
                "evidence_refs": evidence_refs,
                "affected_artifacts": affected_artifacts,
                "suggested_action": (
                    f"Generate a learning-driven tuning proposal for recurring root cause '{root_cause}'."
                ),
            }
        )

    for category, evidence_refs in sorted(categories.items()):
        if len(evidence_refs) < 3 or (len(evidence_refs) / parsed_entries) < 0.5:
            continue
        compound_patterns.append(
            {
                "pattern_type": "category_concentration",
                "key": category,
                "evidence_count": len(evidence_refs),
                "evidence_refs": evidence_refs,
                "affected_artifacts": affected_artifacts,
                "suggested_action": (
                    f"Investigate whether category '{category}' needs stronger harness guidance or a dedicated reviewer surface."
                ),
            }
        )

    for component, evidence_refs in sorted(components.items()):
        if len(evidence_refs) < 3:
            continue
        compound_patterns.append(
            {
                "pattern_type": "component_hotspot",
                "key": component,
                "evidence_count": len(evidence_refs),
                "evidence_refs": evidence_refs,
                "affected_artifacts": affected_artifacts,
                "suggested_action": (
                    f"Review harness coverage for hotspot component '{component}'."
                ),
            }
        )

    for tag, evidence_refs in sorted(tag_refs.items()):
        categories_for_tag = tag_categories.get(tag, set())
        if len(categories_for_tag) < 3:
            continue
        compound_patterns.append(
            {
                "pattern_type": "cross_cutting_tags",
                "key": tag,
                "evidence_count": len(evidence_refs),
                "evidence_refs": evidence_refs,
                "affected_artifacts": affected_artifacts,
                "suggested_action": (
                    f"Consider a cross-cutting instruction or review rule for tag '{tag}'."
                ),
            }
        )

    if len(high_severity_refs) >= 3 and (len(high_severity_refs) / parsed_entries) >= 0.5:
        compound_patterns.append(
            {
                "pattern_type": "severity_trend",
                "key": "high_severity_pressure",
                "evidence_count": len(high_severity_refs),
                "evidence_refs": sorted(high_severity_refs),
                "affected_artifacts": affected_artifacts,
                "suggested_action": "Escalate the next learning-driven tuning proposal for repeated high-severity compound entries.",
            }
        )

    compound_patterns.sort(
        key=lambda item: (str(item.get("pattern_type") or ""), str(item.get("key") or ""))
    )
    return compound_patterns


def _mine_continuous_learning_patterns(
    workspace_path: Path,
    continuous_learning_dir: Path,
    promotion_threshold: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    observation_dir = continuous_learning_dir / "observations"
    instinct_dir = continuous_learning_dir / "instincts"
    learned_dir = continuous_learning_dir / "learned"

    observation_files = _iter_signal_files(observation_dir)
    phase_counter: Counter[str] = Counter()
    total_observations = 0
    for file_path in observation_files:
        metadata = _load_structured_signal_file(file_path)
        phase = _normalize_signal_text(
            metadata.get("affected_workflow_phase") or metadata.get("workflow_phase")
        ).lower()
        if not phase:
            continue
        phase_counter[phase] += 1
        total_observations += 1

    observation_patterns = [
        {
            "phase": phase,
            "observation_count": count,
            "proportion": round(count / total_observations, 2) if total_observations else 0.0,
            "suggested_action": (
                f"Strengthen the {phase} workflow guidance because it accounts for {count} corroborating observations."
            ),
        }
        for phase, count in sorted(phase_counter.items())
    ]

    promoted_instinct_paths: set[str] = set()
    promoted_instinct_names: set[str] = set()
    for file_path in _iter_signal_files(learned_dir):
        metadata = _load_structured_signal_file(file_path)
        source_instinct = _normalize_signal_text(
            metadata.get("instinct_path")
            or metadata.get("source_instinct")
            or metadata.get("source_instinct_path")
        )
        if source_instinct:
            normalized_path = Path(source_instinct).as_posix()
            promoted_instinct_paths.add(normalized_path)
            promoted_instinct_names.add(Path(normalized_path).stem)

    promotion_candidates: list[dict[str, Any]] = []
    for file_path in _iter_signal_files(instinct_dir):
        metadata = _load_structured_signal_file(file_path)
        instinct_path = _relative_workspace_path(workspace_path, file_path)
        observation_count = _coerce_int(
            metadata.get("observation_count")
            or metadata.get("corroborating_observation_count")
            or metadata.get("corroborating_observations")
            or metadata.get("observation_refs")
        )
        if observation_count is None or observation_count < promotion_threshold:
            continue
        if instinct_path in promoted_instinct_paths or file_path.stem in promoted_instinct_names:
            continue

        suggested_target = _normalize_signal_text(
            metadata.get("suggested_target") or metadata.get("promotion_target") or "instruction"
        ) or "instruction"
        learned_suffix = ".instructions.md" if suggested_target == "instruction" else ".md"
        promotion_candidates.append(
            {
                "instinct_path": instinct_path,
                "observation_count": observation_count,
                "threshold": promotion_threshold,
                "suggested_target": suggested_target,
                "suggested_action": (
                    f"Invoke evolve skill to promote to learned-{file_path.stem}{learned_suffix}"
                ),
            }
        )

    promotion_candidates.sort(key=lambda item: str(item.get("instinct_path") or ""))
    return promotion_candidates, observation_patterns


def _mine_closure_patterns(
    workspace_path: Path,
    tuning_reports_dir: Path,
    closure_dir: Path,
) -> list[dict[str, Any]]:
    proposal_occurrences: dict[str, list[dict[str, str]]] = {}
    closure_occurrences: dict[str, list[dict[str, str]]] = {}

    for file_path in _iter_signal_files(tuning_reports_dir):
        metadata = _load_structured_signal_file(file_path)
        timestamp = _extract_signal_timestamp(file_path, metadata)
        proposals = metadata.get("proposals") or metadata.get("learning_driven_proposals") or []
        if not isinstance(proposals, list):
            continue
        for proposal in proposals:
            if isinstance(proposal, dict):
                key = _normalize_signal_text(
                    proposal.get("key")
                    or proposal.get("summary")
                    or proposal.get("artifact")
                    or proposal.get("title")
                )
                status = _normalize_signal_text(proposal.get("status") or proposal.get("resolution")).lower()
                prior_fix_ref = _normalize_signal_text(
                    proposal.get("prior_fix_ref") or proposal.get("applied_ref")
                )
            else:
                key = _normalize_signal_text(proposal)
                status = ""
                prior_fix_ref = ""

            if not key or status in {"resolved", "complete", "completed"}:
                continue
            proposal_occurrences.setdefault(key, []).append(
                {
                    "timestamp": timestamp,
                    "ref": _relative_workspace_path(workspace_path, file_path),
                    "prior_fix_ref": prior_fix_ref,
                }
            )

    for file_path in _iter_signal_files(closure_dir):
        metadata = _load_structured_signal_file(file_path)
        timestamp = _extract_signal_timestamp(file_path, metadata)
        findings = metadata.get("closure_findings") or metadata.get("findings") or metadata.get("runtime_findings") or []
        if not isinstance(findings, list):
            continue
        for finding in findings:
            if isinstance(finding, dict):
                key = _normalize_signal_text(
                    finding.get("key")
                    or finding.get("summary")
                    or finding.get("finding")
                    or finding.get("issue")
                    or finding.get("rollback_trigger")
                )
            else:
                key = _normalize_signal_text(finding)
            if not key:
                continue
            closure_occurrences.setdefault(key, []).append(
                {
                    "timestamp": timestamp,
                    "ref": _relative_workspace_path(workspace_path, file_path),
                }
            )

    closure_patterns: list[dict[str, Any]] = []
    for key, occurrences in sorted(proposal_occurrences.items()):
        if len(occurrences) < 2:
            continue
        first_seen, last_seen = _timestamp_bounds([item["timestamp"] for item in occurrences])
        prior_fix_refs = sorted({item["prior_fix_ref"] for item in occurrences if item["prior_fix_ref"]})
        closure_patterns.append(
            {
                "pattern_type": "recurring_tuning_proposal",
                "key": key,
                "occurrences": len(occurrences),
                "first_seen": first_seen,
                "last_seen": last_seen,
                "prior_fix_refs": prior_fix_refs,
                "suggested_action": f"Escalate recurring tuning proposal '{key}' to a structural harness fix.",
            }
        )

    for key, occurrences in sorted(closure_occurrences.items()):
        if len(occurrences) < 2:
            continue
        first_seen, last_seen = _timestamp_bounds([item["timestamp"] for item in occurrences])
        closure_patterns.append(
            {
                "pattern_type": "recurring_closure_finding",
                "key": key,
                "occurrences": len(occurrences),
                "first_seen": first_seen,
                "last_seen": last_seen,
                "prior_fix_refs": [],
                "suggested_action": f"Add or strengthen harness guidance for recurring closure finding '{key}'.",
            }
        )

    closure_patterns.sort(
        key=lambda item: (str(item.get("pattern_type") or ""), str(item.get("key") or ""))
    )
    return closure_patterns


def _mine_learning_signals(
    workspace_path: Path,
    variables: dict[str, str],
    config: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    learning_signals = _empty_learning_signals()
    compound_dir = workspace_path / Path(str(variables.get("DOCS_COMPOUND") or "docs/compound"))
    affected_artifacts = [
        ".github/agents/auto-tune.agent.md",
        ".github/skills/tune-harness/SKILL.md",
    ]

    learning_signals["compound_patterns"] = _mine_compound_patterns(
        workspace_path,
        compound_dir,
        affected_artifacts,
    )

    continuous_learning_dir = workspace_path / Path(str(variables.get("CONTINUOUS_LEARNING_DIR") or ".autoharness/continuous-learning"))
    promotion_threshold = _coerce_int(
        (config.get("continuous_learning") or {}).get("promotion_threshold")
    ) or 3
    promotion_candidates, observation_patterns = _mine_continuous_learning_patterns(
        workspace_path,
        continuous_learning_dir,
        promotion_threshold,
    )
    learning_signals["promotion_candidates"] = promotion_candidates
    learning_signals["observation_patterns"] = observation_patterns

    learning_signals["closure_patterns"] = _mine_closure_patterns(
        workspace_path,
        workspace_path / ".autoharness" / "tuning-reports",
        workspace_path / Path(str(variables.get("DOCS_CLOSURE") or "docs/closure")),
    )

    return learning_signals


def _resolve_source_template(
    autoharness_home: Path,
    workspace_path: Path,
    artifact: dict[str, Any],
) -> tuple[Path | None, str | None]:
    template = str(artifact.get("template", ""))
    artifact_relative_path = Path(str(artifact.get("path", "")))
    artifact_name = artifact_relative_path.name

    if template.startswith("templates/"):
        return autoharness_home / template, "template"

    if template.endswith((".tmpl", ".yaml", ".json", ".md", ".ps1", ".sh")):
        return autoharness_home / "templates" / template, "template"

    if template == "concurrency pack script":
        return autoharness_home / "templates" / "skills" / "file-lock" / "scripts" / artifact_name, "copy"

    if template == "skill-search pack script":
        return autoharness_home / "templates" / "skills" / "skill-search" / "scripts" / artifact_name, "copy"

    if template in WORKSPACE_SOURCE_TEMPLATES:
        return workspace_path / artifact_relative_path, "workspace"

    return None, None


def _build_extended_operations_table(registry: dict[str, Any]) -> str:
    operations = registry.get("operations") or {}
    rows = []
    for operation_name in sorted(operations):
        if operation_name in CORE_OPERATIONS:
            continue
        operation = operations[operation_name] or {}
        mcp_tool = str(operation.get("mcp_tool") or "")
        cli_command = str(operation.get("cli_command") or "")
        purpose = operation_name.replace("_", " ")
        rows.append(f"| `{operation_name}` | `{mcp_tool}` | `{cli_command}` | {purpose} |")

    if not rows:
        return ""

    header = [
        "| Operation | MCP Tool | CLI Command | Purpose |",
        "|---|---|---|---|",
    ]
    return "\n".join(header + rows)


def _language_defaults(language: str) -> dict[str, str]:
    defaults = {
        "unsafe_policy": "Use the language's safe default constructs and avoid unsafe escape hatches unless the repository explicitly requires them.",
        "lint_policy": "Treat lint failures as actionable defects.",
        "error_handling_policy": "Use explicit error propagation and repository-standard error types.",
        "error_handling_conventions": "Prefer explicit, typed error handling with context at the boundary where failures matter.",
        "naming_conventions": "Follow the repository's established naming rules for files, types, and symbols.",
        "documentation_conventions": "Document public surfaces and non-obvious decisions close to the code that owns them.",
        "concurrency_patterns": "thread, lock, queue, worker, async",
    }

    language = language.lower()
    if language == "go":
        return {
            "unsafe_policy": "Prefer standard-library concurrency and avoid unsafe or panic-driven control flow in library code.",
            "lint_policy": "golangci-lint warnings are treated as real defects.",
            "error_handling_policy": "Return explicit errors, wrap them with context, and prefer errors.Is/errors.As friendly patterns.",
            "error_handling_conventions": "Use explicit error returns with wrapping context instead of panic in normal library flows.",
            "naming_conventions": "Use MixedCaps for exported Go identifiers and short, descriptive package names.",
            "documentation_conventions": "Write GoDoc comments on exported packages, types, and functions.",
            "concurrency_patterns": "goroutine, channel, mutex, WaitGroup, context.Context",
        }
    if language == "python":
        return {
            "unsafe_policy": "Prefer typed, explicit Python over dynamic shortcuts that hide failure modes.",
            "lint_policy": "Lint and format failures should block the change until corrected.",
            "error_handling_policy": "Raise specific exceptions and handle them at clear boundaries.",
            "error_handling_conventions": "Use explicit exceptions with contextual messages and avoid bare except blocks.",
            "naming_conventions": "Use snake_case for modules, functions, and variables; PascalCase for classes.",
            "documentation_conventions": "Use docstrings for public modules, classes, and functions.",
            "concurrency_patterns": "asyncio, task, queue, thread, process",
        }
    if language in {"typescript", "javascript"}:
        return {
            "unsafe_policy": "Prefer strict typing and avoid unchecked dynamic access to unknown values.",
            "lint_policy": "Lint and typecheck failures are blocking quality gates.",
            "error_handling_policy": "Throw typed errors or Error subclasses and handle them at boundary layers.",
            "error_handling_conventions": "Use explicit errors, preserve stack context, and avoid silent promise rejection paths.",
            "naming_conventions": "Use camelCase for values and PascalCase for classes, components, and types.",
            "documentation_conventions": "Document exported APIs and non-obvious contracts with concise comments or JSDoc.",
            "concurrency_patterns": "Promise, async, await, worker, stream",
        }
    return defaults


def _derive_template_variables(
    workspace_path: Path,
    manifest: dict[str, Any],
    config: dict[str, Any],
    profile: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, str]:
    variables = {
        str(key): str(value)
        for key, value in (manifest.get("variables_used") or {}).items()
        if value is not None
    }

    variables.setdefault("PROJECT_NAME", workspace_path.name)
    variables.setdefault("DATE", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    config_packs = [str(pack) for pack in config.get("capability_packs") or []]
    manifest_packs = [str(pack) for pack in manifest.get("capability_packs") or []]
    packs = manifest_packs or config_packs
    if packs:
        variables.setdefault("CAPABILITY_PACKS", ",".join(packs))
    variables.setdefault(
        "CONTINUOUS_LEARNING_DIR",
        str((config.get("continuous_learning") or {}).get("directory") or ".autoharness/continuous-learning"),
    )

    backlog_config = config.get("backlog") or {}
    suffix_map = backlog_config.get("suffix_map") or {}
    for key, default in DEFAULT_SUFFIXES.items():
        prefix_key = f"PREFIX_{key.upper()}"
        suffix_key = f"SUFFIX_{key.upper()}"
        value = suffix_map.get(key) or variables.get(prefix_key) or variables.get(suffix_key) or default
        variables.setdefault(prefix_key, str(value))
        variables.setdefault(suffix_key, str(value))

    docs_config = config.get("docs") or {}
    docs_root = str(docs_config.get("root") or variables.get("DOCS_ROOT") or "docs")
    docs_subdirs = docs_config.get("subdirectories") or {}
    docs_defaults = {
        "COMPOUND": "compound",
        "PLANS": "plans",
        "DECISIONS": "decisions",
        "MEMORY": "memory",
        "CLOSURE": "closure",
        "DESIGN_DOCS": "design-docs",
        "PRODUCT_SPECS": "product-specs",
    }
    variables.setdefault("DOCS_ROOT", docs_root)
    for suffix, default in docs_defaults.items():
        config_key = suffix.lower()
        subdir = str(
            docs_subdirs.get(config_key)
            or variables.get(f"DOCS_{suffix}_DIR")
            or default
        )
        variables.setdefault(f"DOCS_{suffix}_DIR", subdir)
        variables.setdefault(f"DOCS_{suffix}", f"{docs_root}/{subdir}")

    languages = profile.get("languages") or {}
    build = profile.get("build") or {}
    test = profile.get("test") or {}
    lint = profile.get("lint") or {}
    format_cfg = profile.get("format") or {}
    ci = profile.get("ci") or {}
    if languages.get("primary"):
        primary_language = str(languages["primary"])
        variables.setdefault("PRIMARY_LANGUAGE", primary_language)
        variables.setdefault("PRIMARY_LANGUAGE_LOWER", primary_language.lower())
        language_defaults = _language_defaults(primary_language)
        variables.setdefault("UNSAFE_POLICY", language_defaults["unsafe_policy"])
        variables.setdefault("LINT_POLICY", language_defaults["lint_policy"])
        variables.setdefault("ERROR_HANDLING_POLICY", language_defaults["error_handling_policy"])
        variables.setdefault("ERROR_HANDLING_CONVENTIONS", language_defaults["error_handling_conventions"])
        variables.setdefault("NAMING_CONVENTIONS", language_defaults["naming_conventions"])
        variables.setdefault("DOCUMENTATION_CONVENTIONS", language_defaults["documentation_conventions"])
        variables.setdefault("CONCURRENCY_PATTERNS", language_defaults["concurrency_patterns"])
    if languages.get("version"):
        language_version = str(languages["version"])
        variables.setdefault("LANGUAGE_VERSION", language_version)
        variables.setdefault("LANGUAGE_NOTES", f"({language_version})")
    if build.get("command"):
        variables.setdefault("BUILD_COMMAND", str(build["command"]))
    if build.get("check_command"):
        variables.setdefault("BUILD_CHECK_COMMAND", str(build["check_command"]))
    if build.get("tool"):
        variables.setdefault("BUILD_TOOL", str(build["tool"]))
    if test.get("command"):
        variables.setdefault("TEST_COMMAND", str(test["command"]))
    if test.get("runner"):
        variables.setdefault("TEST_RUNNER", str(test["runner"]))
    if test.get("directory"):
        variables.setdefault("TEST_DIR", str(test["directory"]))
    if lint.get("command"):
        variables.setdefault("LINT_COMMAND", str(lint["command"]))
    if lint.get("tool"):
        variables.setdefault("LINTER", str(lint["tool"]))
    if format_cfg.get("command"):
        variables.setdefault("FORMAT_COMMAND", str(format_cfg["command"]))
    if format_cfg.get("check_command"):
        variables.setdefault("FORMAT_CHECK_COMMAND", str(format_cfg["check_command"]))
    if format_cfg.get("tool"):
        variables.setdefault("FORMATTER", str(format_cfg["tool"]))
    if ci.get("platform"):
        ci_platform = str(ci["platform"])
        variables.setdefault("CI_PLATFORM", ci_platform)
        variables.setdefault("CI_NOTES", str(ci.get("notes") or f"Uses {ci_platform} for CI validation."))
        workflow_glob = "**/.github/workflows/*.yml" if ci_platform.lower() == "github actions" else ""
        variables.setdefault("CI_WORKFLOW_GLOB", workflow_glob)

    test_dir = variables.get("TEST_DIR", "tests/")
    test_command = variables.get("TEST_COMMAND", "")
    if test_command:
        variables.setdefault("TEST_TIER_DESCRIPTION", f"Primary test command: {test_command}")
    variables.setdefault("TEST_STRUCTURE", f"Primary tests live in {test_dir}.")

    project_description = str(
        (profile.get("harness_recommendations") or {}).get("project_description")
        or f"{workspace_path.name} workspace"
    )
    variables.setdefault("PROJECT_DESCRIPTION", project_description)
    variables.setdefault(
        "REPOSITORY_OPERATING_MODEL",
        f"Git-tracked workspace with generated harness artifacts under .github/, .autoharness/, and the configured docs root ({docs_root}/).",
    )
    variables.setdefault("ADDITIONAL_STACK_ROWS", "")

    tool_name = str(registry.get("tool_name") or backlog_config.get("tool") or variables.get("BACKLOG_TOOL_NAME") or "")
    if tool_name:
        variables.setdefault("BACKLOG_TOOL_NAME", tool_name)
        variables.setdefault("BACKLOG_TOOLS", tool_name)
    directory = str(registry.get("directory") or backlog_config.get("directory") or variables.get("BACKLOG_DIRECTORY") or "")
    if directory:
        variables.setdefault("BACKLOG_DIRECTORY", directory)
    tool_type = str(registry.get("tool_type") or variables.get("BACKLOG_TOOL_TYPE") or "")
    if tool_type:
        variables.setdefault("BACKLOG_TOOL_TYPE", tool_type)

    features = registry.get("features") or {}
    variables.setdefault("FEATURE_SHIPMENTS", str(bool(features.get("shipments", False))).lower())

    operations = registry.get("operations") or {}
    for operation_name, variable_name in OPERATION_VARIABLES.items():
        operation = operations.get(operation_name) or {}
        mcp_tool = operation.get("mcp_tool")
        if mcp_tool:
            variables.setdefault(variable_name, str(mcp_tool))
        else:
            variables.setdefault(variable_name, "")
    for operation_name, variable_name in CLI_OPERATION_VARIABLES.items():
        operation = operations.get(operation_name) or {}
        cli_command = operation.get("cli_command")
        if cli_command:
            variables.setdefault(variable_name, str(cli_command))
        else:
            variables.setdefault(variable_name, "")
    variables.setdefault("EXTENDED_OPERATIONS_TABLE", _build_extended_operations_table(registry))

    status_values = registry.get("status_values") or {}
    for variable_name, aliases in STATUS_VARIABLES.items():
        for alias in aliases:
            value = status_values.get(alias)
            if value is not None:
                variables.setdefault(variable_name, str(value))
                break
        variables.setdefault(variable_name, variables.get(variable_name, ""))

    field_mapping = registry.get("field_mapping") or {}
    for variable_name, aliases in FIELD_VARIABLES.items():
        for alias in aliases:
            value = field_mapping.get(alias)
            if value is not None:
                variables.setdefault(variable_name, str(value))
                break
        variables.setdefault(variable_name, variables.get(variable_name, ""))

    return variables


def _add_text_check(
    report: dict[str, Any],
    key: str,
    file_path: Path,
    must_contain: list[str],
    must_precede: list[tuple[str, str]] | None = None,
) -> None:
    if not file_path.exists():
        report["targeted_checks"][key] = {
            "path": str(file_path),
            "ok": False,
            "reason": "missing file",
        }
        return

    content = file_path.read_text(encoding="utf-8")
    missing = [needle for needle in must_contain if needle not in content]
    order_violations = []
    for first, second in must_precede or []:
        first_index = content.find(first)
        second_index = content.find(second)
        if first_index == -1 or second_index == -1 or first_index >= second_index:
            order_violations.append({"before": first, "after": second})
    report["targeted_checks"][key] = {
        "path": str(file_path),
        "ok": not missing and not order_violations,
        "missing": missing,
        "order_violations": order_violations,
    }


def _write_markdown_report(report: dict[str, Any], markdown_path: Path) -> None:
    lines = [
        "# verify-workspace report",
        "",
        f"- Workspace: `{report['workspace_path']}`",
        f"- autoharness_home: `{report['autoharness_home']}`",
        f"- Staging dir: `{report['staging_dir']}`",
        "",
        "## Strict-Schema Blockers",
        "",
    ]

    if report["strict_schema_blockers"]:
        for blocker in report["strict_schema_blockers"]:
            lines.append(f"- {json.dumps(blocker, ensure_ascii=False)}")
    else:
        lines.append("none")

    lines.extend(["", "## Blockers", ""])
    if report["blockers"]:
        for blocker in report["blockers"]:
            lines.append(f"- {json.dumps(blocker, ensure_ascii=False)}")
    else:
        lines.append("none")

    lines.extend(["", "## Warnings", ""])
    if report["warnings"]:
        if report.get("warning_instances", len(report["warnings"])) > len(report["warnings"]):
            lines.append(
                "grouped summaries: "
                f"{len(report['warnings'])} (from {report['warning_instances']} findings)"
            )
            lines.append("")
        for warning in report["warnings"]:
            occurrence_count = int(warning.get("occurrence_count", 1))
            if occurrence_count > 1:
                details = [f"{occurrence_count} findings"]
                legacy_values = warning.get("legacy_values") or []
                if legacy_values:
                    details.append("values: " + ", ".join(str(value) for value in legacy_values))
                fields = warning.get("fields") or []
                if fields:
                    details.append("fields: " + ", ".join(str(field) for field in fields))
                lines.append(
                    f"- {warning['kind']} @ {warning['path']}: {warning['message']} "
                    f"({'; '.join(details)})"
                )
                if warning.get("suggested_action"):
                    lines.append(f"  suggested_action: {warning['suggested_action']}")
                continue

            lines.append(f"- {json.dumps(warning, ensure_ascii=False)}")
    else:
        lines.append("none")

    lines.extend(["", "## Schema Contracts", ""])
    if report["schema_contracts"]:
        for contract in report["schema_contracts"].values():
            observed = contract["observed_version"] or "(missing)"
            lines.append(
                f"- {contract['contract_name']}: {contract['status']} "
                f"(observed {observed}, current {contract['current_version']})"
            )
    else:
        lines.append("none")

    lines.extend(["", "## Migration Proposals", ""])
    if report["migration_proposals"]:
        for proposal in report["migration_proposals"]:
            from_version = proposal["from_version"] or "(missing)"
            lines.append(
                f"- {proposal['contract']}: {proposal['summary']} "
                f"({from_version} -> {proposal['to_version']})"
            )
    else:
        lines.append("none")

    lines.extend(["", "## Unresolved Placeholders", ""])
    if report["unresolved"]:
        for unresolved in report["unresolved"]:
            lines.append(
                f"- {unresolved['path']}:{unresolved['line']} {unresolved['placeholder']}"
            )
    else:
        lines.append("none")

    lines.extend(["", "## Targeted Checks", ""])
    if report["targeted_checks"]:
        for key, check in report["targeted_checks"].items():
            status = "PASS" if check.get("ok") else "FAIL"
            lines.append(f"- {key}: {status}")
            if check.get("missing"):
                lines.append(f"  missing: {', '.join(check['missing'])}")
            elif check.get("reason"):
                lines.append(f"  reason: {check['reason']}")
    else:
        lines.append("none")

    lines.extend(["", "## Learning Signals", ""])
    learning_signals = report.get("learning_signals") or {}
    if any(learning_signals.get(key) for key in learning_signals):
        for key in (
            "compound_patterns",
            "promotion_candidates",
            "observation_patterns",
            "closure_patterns",
        ):
            lines.append(f"- {key}: {len(learning_signals.get(key) or [])}")
    else:
        lines.append("none")

    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_workspace(
    workspace_path: Path,
    autoharness_home: Path,
    staging_dir: Path | None = None,
) -> dict[str, Any]:
    """Verify an installed autoharness workspace and write staged outputs."""
    workspace_path = workspace_path.resolve()
    autoharness_home = autoharness_home.resolve()
    staging_root = (staging_dir or workspace_path / ".autoharness" / "staging").resolve()
    staging_root.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "mode": "verify-workspace",
        "workspace_path": str(workspace_path),
        "autoharness_home": str(autoharness_home),
        "staging_dir": str(staging_root),
        "strict_schema_blockers": [],
        "warnings": [],
        "warning_instances": 0,
        "blockers": [],
        "rendered": [],
        "skipped": [],
        "unresolved": [],
        "checksum_scan": [],
        "schema_contracts": {},
        "migration_proposals": [],
        "targeted_checks": {},
        "learning_signals": _empty_learning_signals(),
        "report_paths": {},
    }

    manifest_path = workspace_path / ".autoharness" / "harness-manifest.yaml"
    config_path = workspace_path / ".autoharness" / "config.yaml"
    profile_path = workspace_path / ".autoharness" / "workspace-profile.yaml"
    registry_path = workspace_path / ".autoharness" / "backlog-registry.yaml"

    if not manifest_path.exists():
        report["blockers"].append(
            {
                "kind": "missing-manifest",
                "path": str(manifest_path),
                "message": "verify-workspace requires an installed .autoharness/harness-manifest.yaml",
            }
        )
        json_path = staging_root / "verify-workspace-report.json"
        markdown_path = staging_root / "verify-workspace-report.md"
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_markdown_report(report, markdown_path)
        report["report_paths"] = {"json": str(json_path), "markdown": str(markdown_path)}
        return report

    try:
        manifest = _load_yaml_file(manifest_path)
    except Exception as exc:
        report["blockers"].append(
            {
                "kind": "invalid-manifest-yaml",
                "path": str(manifest_path),
                "message": str(exc),
            }
        )
        manifest = {}

    config = {}
    if config_path.exists():
        try:
            config = _load_yaml_file(config_path)
        except Exception as exc:
            report["strict_schema_blockers"].append(
                {
                    "kind": "invalid-config-yaml",
                    "path": str(config_path),
                    "message": str(exc),
                }
            )

    profile = {}
    if profile_path.exists():
        try:
            profile = _load_yaml_file(profile_path)
        except Exception as exc:
            report["strict_schema_blockers"].append(
                {
                    "kind": "invalid-profile-yaml",
                    "path": str(profile_path),
                    "message": str(exc),
                }
            )

    registry = {}
    if registry_path.exists():
        try:
            registry = _load_yaml_file(registry_path)
        except Exception as exc:
            report["warnings"].append(
                {
                    "kind": "invalid-registry-yaml",
                    "path": str(registry_path),
                    "message": str(exc),
                }
            )

    schema_targets = [
        ("manifest", manifest_path, manifest),
        ("config", config_path, config),
        ("profile", profile_path, profile),
    ]
    for kind, path, data in schema_targets:
        if path.exists():
            report["schema_contracts"][kind] = summarize_schema_contract(kind, path, data)
        if not path.exists() or not data:
            continue
        report["warnings"].extend(collect_contract_state_warnings(kind, path, data))
        schema_path = resolve_contract_schema_path(kind, autoharness_home, data)
        for error in _schema_errors(schema_path, data):
            classification, payload = classify_schema_error(kind, path, data, error)
            if classification == "warning":
                report["warnings"].append(payload)
            else:
                report["strict_schema_blockers"].append(payload)

    for kind, path, data in schema_targets:
        if not path.exists() or not data:
            continue
        contract_warnings = [warning for warning in report["warnings"] if warning.get("path") == str(path)]
        report["migration_proposals"].extend(
            plan_schema_contract_migrations(kind, path, data, contract_warnings)
        )

    variables = _derive_template_variables(workspace_path, manifest, config, profile, registry)
    report["learning_signals"] = _mine_learning_signals(workspace_path, variables, config)

    for artifact in manifest.get("artifacts") or []:
        if not isinstance(artifact, dict):
            report["warnings"].append(
                {
                    "kind": "malformed-artifact-entry",
                    "path": str(artifact),
                    "message": "Manifest artifact entry is not an object; expected {path, checksum, template, primitive}. Skipping.",
                }
            )
            continue
        relative_path = str(artifact.get("path", ""))
        workspace_file = workspace_path / Path(relative_path)
        raw_expected_checksum = artifact.get("checksum")
        expected_checksum = _normalize_signal_text(raw_expected_checksum)
        if not workspace_file.exists():
            checksum_entry = {"path": relative_path, "status": "missing"}
            if expected_checksum:
                checksum_entry["expected"] = expected_checksum
            else:
                checksum_entry["reason"] = "manifest checksum missing"
            report["checksum_scan"].append(checksum_entry)
            report["warnings"].append(
                {
                    "kind": "missing-installed-artifact",
                    "path": relative_path,
                    "message": "Manifest-listed artifact is missing from the workspace.",
                }
            )
        else:
            actual_checksum = _sha256_bytes(workspace_file.read_bytes())
            if expected_checksum:
                status = "unchanged" if actual_checksum == expected_checksum else "user-modified"
                report["checksum_scan"].append(
                    {
                        "path": relative_path,
                        "status": status,
                        "expected": expected_checksum,
                        "actual": actual_checksum,
                    }
                )
            else:
                report["checksum_scan"].append(
                    {
                        "path": relative_path,
                        "status": "checksum-untracked",
                        "actual": actual_checksum,
                        "reason": "manifest checksum missing",
                    }
                )
                report["warnings"].append(
                    {
                        "kind": "manifest-checksum-missing",
                        "path": relative_path,
                        "message": "Manifest-listed artifact has no checksum; drift scan skipped checksum comparison for this path.",
                    }
                )

        source_path, mode = _resolve_source_template(autoharness_home, workspace_path, artifact)
        if source_path is None or mode is None:
            report["skipped"].append(
                {
                    "path": relative_path,
                    "template": str(artifact.get("template", "")),
                    "reason": "template source could not be resolved deterministically",
                }
            )
            continue

        if not source_path.exists():
            if mode == "workspace":
                report["skipped"].append(
                    {
                        "path": relative_path,
                        "template": str(artifact.get("template", "")),
                        "reason": "workspace-owned source file is missing from the installed workspace",
                    }
                )
                continue
            report["blockers"].append(
                {
                    "kind": "missing-template-source",
                    "path": str(source_path),
                    "artifact": relative_path,
                    "message": "Manifest points at a template or source artifact that does not exist in autoharness_home.",
                }
            )
            continue

        stage_path = _normalize_stage_path(staging_root, relative_path)
        _ensure_parent(stage_path)
        source_content = source_path.read_text(encoding="utf-8")
        if source_path.suffix == ".tmpl" or mode == "template":
            stage_path.write_text(_render_template(source_content, variables), encoding="utf-8")
            render_mode = "rendered"
        else:
            stage_path.write_text(source_content, encoding="utf-8")
            render_mode = "workspace-copied" if mode == "workspace" else "copied"
        report["rendered"].append(
            {
                "path": relative_path,
                "template": str(source_path),
                "mode": render_mode,
            }
        )
        report["unresolved"].extend(_find_unresolved_placeholders(stage_path))

    installed_packs = [
        str(pack)
        for pack in (manifest.get("capability_packs") or config.get("capability_packs") or [])
        if str(pack) in SUPPORTED_CAPABILITY_PACKS
    ]
    for pack in installed_packs:
        for assertion in PACK_ASSERTIONS.get(pack, []):
            _add_text_check(
                report,
                assertion["key"],
                workspace_path / assertion["path"],
                assertion["must_contain"],
                [tuple(pair) for pair in assertion.get("must_precede") or []],
            )

    for assertion in FOUNDATION_ASSERTIONS:
        foundation_path = workspace_path / assertion["path"]
        if not foundation_path.exists():
            continue
        _add_text_check(
            report,
            assertion["key"],
            foundation_path,
            assertion["must_contain"],
            [tuple(pair) for pair in assertion.get("must_precede") or []],
        )

    report["warning_instances"] = len(report["warnings"])
    report["warnings"] = _summarize_warnings(report["warnings"])

    json_path = staging_root / "verify-workspace-report.json"
    markdown_path = staging_root / "verify-workspace-report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown_report(report, markdown_path)
    report["report_paths"] = {"json": str(json_path), "markdown": str(markdown_path)}
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report