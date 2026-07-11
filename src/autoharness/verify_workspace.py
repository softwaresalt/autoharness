"""Deterministic workspace verification for installed autoharness artifacts."""

from __future__ import annotations

import fnmatch
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
    "graphtor-docs",
}
WORKSPACE_SOURCE_TEMPLATES = {
    "workspace merge install",
    "workspace deliberation template",
}
# Artifact classes eligible for new-template (uninstalled) detection during
# tune. The manifest-scoped drift scan only re-hashes artifacts already recorded
# in the manifest, so templates newly added by a harness upgrade are invisible
# to drift detection. Each entry maps a template subdirectory to the workspace
# install directory plus the template/install suffixes so the catalog can be
# diffed against installed artifacts. The set is intentionally conservative:
# prompts are small and broadly installed, whereas instructions/skills/agents
# are heavily capability-pack and stack gated and would need a pack-gate map to
# scan without false positives. Add classes here as gating support grows.
NEW_ARTIFACT_SCAN_CLASSES = (
    {
        "artifact_class": "prompt",
        "template_subdir": "prompts",
        "install_subdir": ".github/prompts",
        "template_suffix": ".prompt.md.tmpl",
        "install_suffix": ".prompt.md",
    },
)
# Documented install rules for prompt templates (install-harness Step 2.7). Used
# only to annotate new-artifact findings with applicability guidance; the tuner
# and operator make the final install decision. `requires_primitive` of None
# means the prompt is universal (always applicable when prompts are used).
# `requires_opt_in` names a workflow-policy opt-in (for example P-017 dark
# factory mode) that cannot be confirmed from `primitives_installed` alone; such
# prompts are always annotated operator-decides so the tuner never auto-installs
# a policy-gated shim into a workspace that did not opt into that policy.
PROMPT_INSTALL_RULES = {
    "ping-loop.prompt.md": {"rule": "universal", "requires_primitive": None},
    "feature-flow.prompt.md": {"rule": "primitive-4", "requires_primitive": 4},
    "feature-flow-parallel.prompt.md": {"rule": "primitive-4", "requires_primitive": 4},
    "feature-flow-dark.prompt.md": {
        "rule": "primitive-4 + P-017",
        "requires_primitive": 4,
        "requires_opt_in": "P-017",
    },
}
# Canonical pipeline agent identities and their known legacy aliases. Older
# harness installs used unprefixed filenames/names (and, earlier still,
# `dispatch` for the orchestrator). Harness upgrades (auto-tune) and merge
# installs standardize any legacy pipeline agent onto its canonical filename and
# `name:` frontmatter so downstream cross-references stay coherent. Only these
# three pipeline agents are in scope; elective agents (auto-mergeinstall,
# auto-tune) and review/research agents are never migrated by this scan.
PIPELINE_AGENT_IDENTITIES = (
    {
        "canonical_id": "autoharness/pipeline/orchestrator",
        "canonical_file": "_orchestrator.agent.md",
        "canonical_name": "_Orchestrator",
        "legacy_files": ("orchestrator.agent.md", "dispatch.agent.md"),
        "legacy_names": ("Orchestrator", "Dispatch"),
    },
    {
        "canonical_id": "autoharness/pipeline/stage",
        "canonical_file": ".stage.agent.md",
        "canonical_name": ".Stage",
        "legacy_files": ("stage.agent.md",),
        "legacy_names": ("Stage",),
    },
    {
        "canonical_id": "autoharness/pipeline/ship",
        "canonical_file": ".ship.agent.md",
        "canonical_name": ".Ship",
        "legacy_files": ("ship.agent.md",),
        "legacy_names": ("Ship",),
    },
)
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
    "sync_index": "OP_SYNC_INDEX_MCP",
    "create_shipment": "OP_CREATE_SHIPMENT_MCP",
    "get_shipment": "OP_GET_SHIPMENT_MCP",
    "list_shipments": "OP_LIST_SHIPMENTS_MCP",
    "claim_shipment": "OP_CLAIM_SHIPMENT_MCP",
    "ship_shipment": "OP_SHIP_SHIPMENT_MCP",
    "add_to_shipment": "OP_ADD_TO_SHIPMENT_MCP",
    "return_blocked": "OP_RETURN_BLOCKED_MCP",
    "archive_item": "OP_ARCHIVE_ITEM_MCP",
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
    "sync_index": "OP_SYNC_INDEX_CLI",
    "archive_item": "OP_ARCHIVE_ITEM_CLI",
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
            "path": ".github/agents/.ship.agent.md",
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
        {
            "key": "stage_index_sync_gate",
            "path": ".github/agents/.stage.agent.md",
            "must_contain": [
                "Index Sync",
                "backlogit_sync_index",
                "INDEX_SYNC_OK",
            ],
        },
        {
            "key": "ship_index_sync_gate",
            "path": ".github/agents/.ship.agent.md",
            "must_contain": [
                "backlogit_sync_index",
                "CLOSURE_INDEX_SYNC_OK",
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
            "must_contain": [
                "monitoring",
                "rollback",
                "observation window",
                "validator evidence",
                "releasability evidence",
            ],
        }
    ],
    "browser-verification": [
        {
            "key": "browser_verification_instruction",
            "path": ".github/instructions/browser-verification.instructions.md",
            "must_contain": [
                "headed",
                "headless",
                "route",
                "validator evidence",
                "manual checkpoint evidence",
                "releasability evidence",
            ],
        }
    ],
    "continuous-learning": [
        {
            "key": "continuous_learning_instruction",
            "path": ".github/instructions/continuous-learning.instructions.md",
            "must_contain": ["observe", "learn", "evolve"],
        }
    ],
    "graphtor-docs": [
        {
            "key": "graphtor_docs_instruction",
            "path": ".github/instructions/graphtor-docs.instructions.md",
            "must_contain": [
                "search_local_docs",
                "search_semantic",
                "research_topic",
                "traverse_doc_links",
                "list_sources",
                "get_chunk_by_id",
                "get_document",
                "get_status",
            ],
        },
        {
            "key": "graphtor_docs_stage_weaving",
            "path": ".github/agents/.stage.agent.md",
            "must_contain": ["graphtor-docs", "graphtor-docs.instructions.md"],
        },
        {
            "key": "graphtor_docs_ship_weaving",
            "path": ".github/agents/.ship.agent.md",
            "must_contain": ["graphtor-docs", "graphtor-docs.instructions.md"],
        },
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
        "key": "copilot_code_review_focus_instruction",
        "path": ".github/instructions/copilot-code-review.instructions.md",
        "must_contain": [
            "applyTo: '**'",
            "excludeAgent: 'cloud-agent'",
            "Focus on high-value concerns",
            "De-prioritize",
            "weakened enforcement",
            "base branch",
        ],
        "must_precede": [
            ["Focus on high-value concerns", "De-prioritize"],
        ],
    },
    {
        "key": "workspace_discovery_runtime_validation_contract",
        "path": ".github/skills/workspace-discovery/SKILL.md",
        "must_contain": [
            "runtime_validation:",
            "validator_manifest",
            "validation_expectations",
            "releasability:",
        ],
    },
    {
        "key": "install_harness_runtime_validation_contract",
        "path": ".github/skills/install-harness/SKILL.md",
        "must_contain": [
            "runtime_validation.validator_manifest",
            "runtime_validation.validation_expectations",
            "runtime_validation.releasability",
            "validator evidence",
            "releasability evidence",
        ],
    },
    {
        "key": "tune_harness_runtime_validation_contract",
        "path": ".github/skills/tune-harness/SKILL.md",
        "must_contain": [
            "runtime_validation.validator_manifest",
            "runtime_validation.validation_expectations",
            "runtime_validation.releasability",
            "validator evidence",
            "releasability evidence",
        ],
    },
    {
        "key": "ship_runtime_validation_contract",
        "path": ".github/agents/.ship.agent.md",
        "must_contain": [
            "runtime_validation.validator_manifest",
            "runtime_validation.validation_expectations",
            "validator evidence",
            "releasability evidence",
        ],
    },
    {
        "key": "harness_architecture_runtime_validation_contract",
        "path": ".github/instructions/harness-architecture.instructions.md",
        "must_contain": [
            "validator evidence",
            "releasability evidence",
            "report-oriented runtime checks",
        ],
    },
    {
        "key": "stage_shipment_determinism",
        "path": ".github/agents/.stage.agent.md",
        "must_contain": [
            "Step Sequence Contract (NON-NEGOTIABLE)",
            "Shipment Assembly (NON-NEGOTIABLE when shipments are supported)",
            "Pre-Summary Verification Gate (NON-NEGOTIABLE)",
            "Never skip shipment assembly",
        ],
    },
    {
        "key": "stage_role_boundary",
        "path": ".github/agents/.stage.agent.md",
        "must_contain": [
            "Role Boundary (NON-NEGOTIABLE)",
            "P-010",
            "Forbidden",
        ],
    },
    {
        "key": "ship_role_boundary",
        "path": ".github/agents/.ship.agent.md",
        "must_contain": [
            "Role Boundary (NON-NEGOTIABLE)",
            "P-010",
            "Forbidden",
        ],
    },
    {
        "key": "ship_release_closure_sequence",
        "path": ".github/agents/.ship.agent.md",
        "must_contain": [
            "Release Closure Completion Gate (P-001, NON-NEGOTIABLE)",
            "post-merge release closure",
            "Treat the shipment as still active for P-001 purposes",
            "another top-level release unit may not begin yet",
        ],
    },
    {
        "key": "orchestrator_release_closure_sequence",
        "path": ".github/agents/_orchestrator.agent.md",
        "must_contain": [
            "awaiting required post-merge release closure",
            "Stage may proceed with planning",
            "must not route a second shipment to Ship until closure is complete",
        ],
    },
    {
        "key": "install_harness_two_agent_role_enforcement",
        "path": ".github/skills/install-harness/SKILL.md",
        "must_contain": [
            "role-enforcement.instructions.md",
            "two-agent",
            "Role Boundary (NON-NEGOTIABLE)",
        ],
    },
    {
        "key": "stage_tool_availability_gate",
        "path": ".github/agents/.stage.agent.md",
        "must_contain": [
            "Tool Availability Gate",
            "TOOL_OK",
            "TOOL_DEGRADED",
            "TOOL_UNAVAILABLE",
            "P-012",
        ],
    },
    {
        "key": "ship_branch_management",
        "path": ".github/agents/.ship.agent.md",
        "must_contain": [
            "Branch retention (NON-NEGOTIABLE)",
            "Post-Merge Branch Protocol (NON-NEGOTIABLE)",
            "Branch Management Rules (NON-NEGOTIABLE)",
            "post-merge/{feature_slug}",
        ],
    },
    {
        "key": "ship_branch_creation_gate",
        "path": ".github/agents/.ship.agent.md",
        "must_contain": [
            "Branch Creation Gate (P-011, NON-NEGOTIABLE)",
            "git branch --show-current",
            "BRANCH_OK",
            "BRANCH_CREATED",
            "BRANCH_MISMATCH",
        ],
    },
    {
        "key": "ship_tool_availability_gate",
        "path": ".github/agents/.ship.agent.md",
        "must_contain": [
            "Tool Availability Gate",
            "TOOL_OK",
            "TOOL_DEGRADED",
            "TOOL_UNAVAILABLE",
            "P-012",
        ],
    },
    {
        "key": "ship_merge_confirmation_gate",
        "path": ".github/agents/.ship.agent.md",
        "must_contain": [
            "Merge Confirmation Gate",
            "MERGE_CONFIRMED",
            "MERGE_NOT_CONFIRMED",
            "merge-base --is-ancestor",
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
    {
        "key": "security_review_persona_routing",
        "path": ".github/skills/review/SKILL.md",
        "must_contain": [
            "Security Reviewer",
            "security-reviewer.agent.md",
        ],
    },
    {
        "key": "local_review_readiness_contract",
        "path": ".github/skills/review/SKILL.md",
        "must_contain": [
            "READY_WITH_FOLLOWUPS",
            "BLOCKED",
            "reviewed HEAD SHA",
        ],
    },
    {
        "key": "template_integrity_reviewer_routing",
        "path": ".github/skills/review/SKILL.md",
        "must_contain": [
            "Template Integrity Reviewer",
            "template-integrity-reviewer.agent.md",
        ],
    },
    {
        "key": "schema_cli_docs_reviewer_routing",
        "path": ".github/skills/review/SKILL.md",
        "must_contain": [
            "Schema-CLI-Docs Coupling Reviewer",
            "schema-cli-docs-coupling-reviewer.agent.md",
        ],
    },
    {
        "key": "security_plan_review_persona_routing",
        "path": ".github/skills/plan-review/SKILL.md",
        "must_contain": [
            "Security Lens Reviewer",
            "security-lens-reviewer.agent.md",
        ],
    },
    {
        "key": "install_harness_browser_skill_manifest",
        "path": ".github/skills/install-harness/SKILL.md",
        "must_contain": [
            "browser-automation/SKILL.md` — Install when `browser-verification` is enabled",
            "iterative-experiment/SKILL.md` — Install when the `workflow` layer is active",
        ],
    },
    {
        "key": "install_harness_browser_verification_overlay",
        "path": ".github/skills/install-harness/SKILL.md",
        "must_contain": [
            "| Automation skill | `browser-automation/SKILL.md` — treated as an explicit overlay target",
        ],
    },
    {
        "key": "tune_harness_dynamic_policy_generation",
        "path": ".github/skills/tune-harness/SKILL.md",
        "must_contain": [
            "policy-gap candidates",
            ".autoharness/policy-proposals/",
            "3 or more",
            "APPLIES_TO",
            "GATE_POINT",
            "PRECONDITION",
            "POSTCONDITION",
            "VIOLATION_ACTION",
        ],
    },
    {
        "key": "auto_tune_dynamic_policy_phase",
        "path": ".github/agents/auto-tune.agent.md",
        "must_contain": [
            "policy-gap",
            "policy-proposals",
        ],
    },
    {
        "key": "p013_policy_in_workflow_policies",
        "path": ".github/policies/workflow-policies.md",
        "must_contain": [
            "P-013",
            "model_tier",
            "max_subagent_tier",
        ],
    },
    {
        "key": "p014_local_review_policy",
        "path": ".github/policies/workflow-policies.md",
        "must_contain": [
            "Local Review Readiness Merge Gate",
            "READY_WITH_FOLLOWUPS",
            "reviewed HEAD SHA",
        ],
    },
]

DARK_FACTORY_ASSERTIONS = [
    {
        "key": "dark_factory_policy_contract",
        "path": ".github/policies/workflow-policies.md",
        "required": True,
        "must_contain": [
            "P-017",
            "Run pipeline in dark mode",
            "DARK_MODE_ACTIVE",
            "BRAINSTORM_HANDOFF_READY",
            "DARK_MODE_COMPLETE",
        ],
    },
    {
        "key": "dark_factory_orchestrator_contract",
        "path": ".github/agents/_orchestrator.agent.md",
        "required": True,
        "must_contain": [
            "Run pipeline in dark mode",
            "DARK_MODE_ACTIVE",
            "merge_approval_pre_authorized",
            "DARK_MODE_START",
            "DARK_MODE_COMPLETE",
            "reviewed HEADs",
        ],
    },
    {
        "key": "dark_factory_ship_contract",
        "path": ".github/agents/.ship.agent.md",
        "must_contain": [
            "LOCAL_REVIEW_READY",
            "DARK_MODE_MERGE_AUTHORIZED",
            "ADMIN_FALLBACK_ATTEMPTED",
            "headRefOid",
            "P-009",
            "P-016",
        ],
    },
    {
        "key": "dark_factory_pr_lifecycle_contract",
        "path": ".github/skills/pr-lifecycle/SKILL.md",
        "must_contain": [
            "headRefOid",
            "NORMAL_MERGE_READY",
            "MERGE_SUCCEEDED",
            "admin_fallback_pre_authorized",
        ],
    },
    {
        "key": "dark_factory_intercom_contract",
        "path": ".github/instructions/agent-intercom.instructions.md",
        "requires_pack": "agent-intercom",
        "must_contain": [
            "Dark Factory Visibility Protocol",
            "BRAINSTORM_HANDOFF_READY",
            "DARK_MODE_COMPLETE",
            "degraded-visibility",
        ],
    },
    {
        "key": "dark_factory_prompt_contract",
        "path": ".github/prompts/feature-flow-dark.prompt.md",
        "required": True,
        "must_contain": [
            "agent: Orchestrator",
            "Run pipeline in dark mode",
            "DARK_MODE_ACTIVE",
            "BRAINSTORM_HANDOFF_READY",
            "does not bypass",
        ],
    },
    {
        "key": "dark_factory_github_pr_automation_contract",
        "path": ".github/instructions/github-pr-automation.instructions.md",
        "must_contain": [
            "Dark-Mode Merge Authorization",
            "headRefOid",
            "admin_fallback_pre_authorized",
            "P-009",
            "P-016",
        ],
    },
    {
        "key": "dark_factory_foundation_contract",
        "path": "AGENTS.md",
        "must_contain": [
            "P-017",
            "Run pipeline in dark mode",
            "local review readiness",
        ],
    },
]


PORTABILITY_RULES = [
    {
        "rule": "hardcoded_user_home",
        "pattern": r"~/\.[a-zA-Z]|%USERPROFILE%|%APPDATA%|C:\\Users\\",
        "severity": "P1",
        "message": "Hardcoded home or user-profile path detected; use an env var or runtime path resolution instead",
    },
    {
        "rule": "local_agents_dir",
        "pattern": r"\.github/local-agents",
        "severity": "P1",
        "message": ".github/local-agents is injected at runtime by start scripts, not a stable harness artifact location",
    },
    {
        "rule": "mcp_plugin_tool_name",
        "pattern": r"mcp__plugin_[a-zA-Z0-9_\-]+__[a-zA-Z0-9_\-]+",
        "severity": "P1",
        "message": "MCP plugin tool name is environment-specific; use {{OP_*}} template variables so tool names resolve at install time",
    },
    {
        "rule": "hardcoded_ah_home",
        "pattern": r"~/\.autoharness|~\\\.autoharness",
        "severity": "P1",
        "message": "Hardcoded autoharness home path detected; use AUTOHARNESS_HOME env var or runtime resolution",
    },
]

# Allow-list: (rule, workspace-relative file glob) pairs matched via fnmatch.
# A finding is suppressed when both the rule name and the file path match.
# Entries document known explanatory references in autoharness engine artifacts.
PORTABILITY_ALLOW_LIST: list[tuple[str, str]] = [
    # auto-mergeinstall: explains path-resolution, local-agents setup, and default install path as instructional text
    ("hardcoded_user_home", ".github/agents/auto-mergeinstall.agent.md"),
    ("local_agents_dir", ".github/agents/auto-mergeinstall.agent.md"),
    ("hardcoded_ah_home", ".github/agents/auto-mergeinstall.agent.md"),
    # auto-tune: explains autoharness_home resolution including the default ~/.autoharness path
    ("hardcoded_user_home", ".github/agents/auto-tune.agent.md"),
    ("hardcoded_ah_home", ".github/agents/auto-tune.agent.md"),
    # install-harness: documents path resolution, setup commands, and local-agents injection
    ("hardcoded_user_home", ".github/skills/install-harness/SKILL.md"),
    ("local_agents_dir", ".github/skills/install-harness/SKILL.md"),
    ("hardcoded_ah_home", ".github/skills/install-harness/SKILL.md"),
    # tune-harness: documents autoharness_home resolution and local-agents context
    ("hardcoded_user_home", ".github/skills/tune-harness/SKILL.md"),
    ("local_agents_dir", ".github/skills/tune-harness/SKILL.md"),
    ("hardcoded_ah_home", ".github/skills/tune-harness/SKILL.md"),
    # workspace-discovery: documents platform-specific path detection (e.g., %APPDATA% on Windows)
    ("hardcoded_user_home", ".github/skills/workspace-discovery/SKILL.md"),
    ("local_agents_dir", ".github/skills/workspace-discovery/SKILL.md"),
    # copilot-instructions.md: describes ~/.autoharness as the default global install path
    ("hardcoded_user_home", ".github/copilot-instructions.md"),
    ("hardcoded_ah_home", ".github/copilot-instructions.md"),
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
        warning.get("rule"),
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
    """Map a relative artifact path into the staging directory.

    Normalises path separators and sanitises the path so that absolute paths
    (Unix-rooted, Windows drive-letter, or extended-length form), later
    drive-anchored path components, parent-directory traversal (``..``), and
    degenerate self-references (``.``) cannot escape or corrupt
    ``staging_dir``.

    Raises :class:`ValueError` when the sanitised path is empty (e.g. the
    input was ``""``, ``"."``, or only ``".."`` components), because writing
    to ``staging_dir`` itself would raise ``IsADirectoryError`` at the call
    site.
    """
    # Normalise to forward slashes, strip any leading separators.
    normalized = relative_path.replace("\\", "/").lstrip("/")
    clean_parts: list[str] = []
    for raw_part in normalized.split("/"):
        # Drop empty/current/parent markers and the extended-path marker left
        # behind when normalising paths like "\\\\?\\C:\\...".
        if not raw_part or raw_part in (".", "..", "?"):
            continue
        # Strip Windows drive prefixes even when they appear mid-path
        # (e.g. "foo/C:/Windows/evil.dll" or "foo/C:Windows/evil.dll").
        if len(raw_part) >= 2 and raw_part[1] == ":" and raw_part[0].isalpha():
            part = raw_part[2:]
        else:
            part = raw_part
        if not part or part in (".", "..", "?"):
            continue
        clean_parts.append(part)
    if not clean_parts:
        raise ValueError(
            f"Artifact path {relative_path!r} is empty or degenerate after sanitisation"
        )
    candidate = staging_dir.joinpath(*clean_parts)
    staging_resolved = staging_dir.resolve()
    if not candidate.resolve().is_relative_to(staging_resolved):
        raise ValueError(
            f"Artifact path {relative_path!r} escapes staging_dir after sanitisation"
        )
    return candidate


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


def _scan_manifest_scalar_placeholders(
    manifest: dict[str, Any], manifest_path: Path
) -> list[dict[str, Any]]:
    """Detect unresolved ``{{...}}`` placeholders in top-level manifest scalars.

    Only string-valued top-level fields are inspected. Lists and dicts such as
    ``artifacts`` are rendered and scanned separately, so they are skipped here.
    Detection reuses :data:`PLACEHOLDER_RE` for placeholder token matching.
    Unlike rendered artifact Markdown, manifest scalar values are not treated
    as fenced Markdown content.
    """
    blockers: list[dict[str, Any]] = []
    if not isinstance(manifest, dict):
        return blockers
    for field, value in manifest.items():
        if not isinstance(value, str):
            continue
        for match in PLACEHOLDER_RE.finditer(value):
            placeholder = match.group(0)
            blockers.append(
                {
                    "kind": "unresolved-manifest-placeholder",
                    "path": str(manifest_path),
                    "field": str(field),
                    "placeholder": placeholder,
                    "message": (
                        f"Manifest scalar field '{field}' contains an unresolved "
                        f"placeholder {placeholder}; installed manifests must not ship "
                        "with unresolved template variables."
                    ),
                }
            )
    return blockers


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


def _agent_frontmatter_name(file_path: Path) -> str | None:
    """Return the trimmed `name:` frontmatter value, or None when absent."""
    try:
        frontmatter = _extract_markdown_frontmatter(file_path)
    except OSError:
        return None
    name = frontmatter.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None


def _agent_frontmatter_id(file_path: Path) -> str | None:
    """Return the trimmed `id:` frontmatter value, or None when absent.

    The stable `id:` is the filename-independent identity signal for pipeline
    agents. When present it is preferred over filename/`name:` alias matching,
    so an agent that was renamed to an arbitrary filename can still be recognized
    and standardized onto its canonical identity.
    """
    try:
        frontmatter = _extract_markdown_frontmatter(file_path)
    except OSError:
        return None
    agent_id = frontmatter.get("id")
    if isinstance(agent_id, str) and agent_id.strip():
        return agent_id.strip()
    return None


def _resolve_agent_scan_dirs(workspace_path: Path, profile: Any) -> list[Path]:
    """Return directories that may hold installed pipeline agent files.

    Always includes ``.github/agents/``. In self-install mode (a globally
    distributed tool with a configured local agents dir) the local agents
    directory is also scanned, since workflow agents live there instead of
    ``.github/agents/``.
    """
    dirs = [workspace_path / ".github" / "agents"]
    distribution = profile.get("distribution") if isinstance(profile, dict) else None
    if isinstance(distribution, dict) and distribution.get("is_global_tool"):
        default_local = ".github/local-agents"
        local_rel = Path(str(distribution.get("local_agents_dir") or default_local))
        # Treat local_agents_dir as workspace-relative only. A rooted/absolute
        # path (anchor) or a parent-traversal segment could push scanning
        # outside the workspace, so fall back to the safe default in that case.
        # `.anchor` (not `.is_absolute()`) is used so root-anchored but
        # driveless paths (e.g. "/abs" on Windows) are also rejected.
        if local_rel.anchor or ".." in local_rel.parts:
            local_rel = Path(default_local)
        candidate = workspace_path / local_rel
        if candidate not in dirs:
            dirs.append(candidate)
    return dirs


def _agent_identity_proposal(
    *,
    rel_from: str,
    rel_to: str,
    from_name: str | None,
    to_name: str,
    changed_fields: list[str],
    severity: str,
    action: str,
    canonical_exists: bool,
    status: str = "known-legacy",
    matched_by: str = "legacy-name",
    agent_id: str | None = None,
) -> dict[str, Any]:
    from_label = rel_from + (f" / {from_name}" if from_name else "")
    to_label = f"{rel_to} / {to_name}"
    if matched_by == "id":
        evidence = (
            f"Pipeline agent matched by stable id `{agent_id}` uses a "
            f"non-canonical identity ({from_label}); the canonical identity "
            f"is ({to_label})."
        )
    else:
        evidence = (
            f"Installed pipeline agent uses a legacy identity ({from_label}); "
            f"the canonical identity is ({to_label})."
        )
    return {
        "contract": "agent-identity",
        "path": rel_from,
        "from_path": rel_from,
        "to_path": rel_to,
        "from_name": from_name,
        "to_name": to_name,
        "from_version": from_label,
        "to_version": to_label,
        "status": status,
        "severity": severity,
        "summary": "standardize legacy pipeline agent to canonical identity",
        "changed_fields": list(changed_fields),
        "action": action,
        "manual_review": False,
        "canonical_exists": canonical_exists,
        "matched_by": matched_by,
        "agent_id": agent_id,
        "evidence": evidence,
    }


def _scan_agent_identity_migrations(
    workspace_path: Path, profile: Any
) -> list[dict[str, Any]]:
    """Detect installed pipeline agents that drifted from their canonical identity.

    Emits ``agent-identity`` migration proposals so upgrades (auto-tune) and
    merge installs can standardize pipeline agents onto their canonical
    filename and ``name:`` frontmatter. Only the three pipeline agents are in
    scope; elective and review/research agents are never proposed for renaming.

    Detection prefers the stable ``id:`` frontmatter field: any agent file whose
    ``id:`` matches a canonical identity is standardized regardless of its current
    filename, so arbitrary renames are still recognized. Files without a matching
    ``id:`` (legacy agents authored before the field existed) fall back to the
    filename/``name:`` alias registry.
    """
    proposals: list[dict[str, Any]] = []
    id_to_identity = {
        identity["canonical_id"]: identity for identity in PIPELINE_AGENT_IDENTITIES
    }
    for agent_dir in _resolve_agent_scan_dirs(workspace_path, profile):
        if not agent_dir.is_dir():
            continue
        present = {
            entry.name: entry
            for entry in sorted(agent_dir.iterdir())
            if entry.is_file() and entry.name.endswith(".agent.md")
        }
        # Files resolved by stable-id matching are skipped by the fallback
        # alias branches below to avoid duplicate proposals for one file.
        handled: set[str] = set()

        # 0) Stable-id matching (preferred). Survives arbitrary renames: a file
        # whose `id:` matches a canonical identity is standardized onto the
        # canonical filename/name regardless of its current filename.
        for filename, entry in present.items():
            agent_id = _agent_frontmatter_id(entry)
            if agent_id is None:
                continue
            identity = id_to_identity.get(agent_id)
            if identity is None:
                continue
            handled.add(filename)
            canonical_file = identity["canonical_file"]
            canonical_name = identity["canonical_name"]
            current_name = _agent_frontmatter_name(entry)
            if filename == canonical_file and current_name == canonical_name:
                continue  # already fully canonical

            needs_rename = filename != canonical_file
            canonical_present = canonical_file in present
            duplicate = needs_rename and canonical_present
            changed_fields: list[str] = []
            if needs_rename:
                changed_fields.append("path")
            if current_name != canonical_name:
                changed_fields.append("name")
            status = (
                "known-legacy"
                if filename in identity["legacy_files"] or filename == canonical_file
                else "id-mismatch"
            )
            if duplicate:
                action = (
                    f"Canonical `{canonical_file}` already exists. Back up and "
                    f"remove the non-canonical duplicate `{filename}` (matched by "
                    f"stable id `{agent_id}`), then reconcile cross-references and "
                    "the manifest artifact path onto the canonical file."
                )
            elif needs_rename:
                action = (
                    f"Rename `{filename}` to `{canonical_file}` (matched by stable "
                    f"id `{agent_id}`), set `name: {canonical_name}`, update all "
                    "cross-references (AGENTS.md, agents, skills, prompts, "
                    "instructions, policies), and update the manifest artifact path."
                )
            else:
                action = (
                    f"Update `{canonical_file}` frontmatter to "
                    f"`name: {canonical_name}` and update any cross-references "
                    "that use the non-canonical name."
                )
            rel_from = _relative_workspace_path(workspace_path, entry)
            rel_to = _relative_workspace_path(
                workspace_path, agent_dir / canonical_file
            )
            proposals.append(
                _agent_identity_proposal(
                    rel_from=rel_from,
                    rel_to=rel_to,
                    from_name=current_name,
                    to_name=canonical_name,
                    changed_fields=changed_fields,
                    severity="P1",
                    action=action,
                    canonical_exists=canonical_present,
                    status=status,
                    matched_by="id",
                    agent_id=agent_id,
                )
            )

        # Filename/`name:` alias fallback for files without a matching `id:`.
        for identity in PIPELINE_AGENT_IDENTITIES:
            canonical_file = identity["canonical_file"]
            canonical_name = identity["canonical_name"]
            canonical_present = canonical_file in present

            # 1) Legacy-named files -> rename (and normalize name) to canonical.
            for legacy_file in identity["legacy_files"]:
                if legacy_file in handled:
                    continue
                entry = present.get(legacy_file)
                if entry is None:
                    continue
                current_name = _agent_frontmatter_name(entry)
                rel_from = _relative_workspace_path(workspace_path, entry)
                rel_to = _relative_workspace_path(
                    workspace_path, agent_dir / canonical_file
                )
                changed_fields = ["path"]
                if current_name != canonical_name:
                    changed_fields.append("name")
                if canonical_present:
                    action = (
                        f"Canonical `{canonical_file}` already exists. Back up and "
                        f"remove the legacy duplicate `{legacy_file}`, then reconcile "
                        "cross-references and the manifest artifact path onto the "
                        "canonical file."
                    )
                else:
                    action = (
                        f"Rename `{legacy_file}` to `{canonical_file}`, set "
                        f"`name: {canonical_name}`, update all cross-references "
                        "(AGENTS.md, agents, skills, prompts, instructions, policies), "
                        "and update the manifest artifact path."
                    )
                proposals.append(
                    _agent_identity_proposal(
                        rel_from=rel_from,
                        rel_to=rel_to,
                        from_name=current_name,
                        to_name=canonical_name,
                        changed_fields=changed_fields,
                        severity="P1",
                        action=action,
                        canonical_exists=canonical_present,
                    )
                )

            # 2) Canonical file carrying a non-canonical name -> normalize name.
            if canonical_file in handled:
                continue
            entry = present.get(canonical_file)
            if entry is not None:
                current_name = _agent_frontmatter_name(entry)
                if current_name is not None and current_name != canonical_name:
                    rel = _relative_workspace_path(workspace_path, entry)
                    proposals.append(
                        _agent_identity_proposal(
                            rel_from=rel,
                            rel_to=rel,
                            from_name=current_name,
                            to_name=canonical_name,
                            changed_fields=["name"],
                            severity="P1",
                            action=(
                                f"Update `{canonical_file}` frontmatter to "
                                f"`name: {canonical_name}` and update any "
                                "cross-references that use the legacy name."
                            ),
                            canonical_exists=True,
                        )
                    )
    return proposals


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


def _scan_uninstalled_templates(
    workspace_path: Path,
    autoharness_home: Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    """Detect templates in autoharness_home with no installed workspace artifact.

    The deterministic checksum scan only re-hashes artifacts already recorded in
    the manifest, so templates newly added by a harness upgrade (for example new
    prompt variants) are invisible to drift detection. This scan diffs the
    autoharness_home template catalog against installed artifacts — matching by
    manifest artifact path, manifest template source, community-template install
    path, and file presence on disk — and surfaces uninstalled templates as
    advisory ``new-artifact`` findings so the tuner can propose installing them.

    Findings are advisory: for prompts the documented install rules annotate
    each finding with applicability, but the tuner and operator make the final
    install decision. The scan never fails verification.
    """
    findings: list[dict[str, Any]] = []

    autoharness_home = autoharness_home.resolve()
    workspace_path = workspace_path.resolve()

    artifacts = [
        artifact
        for artifact in (manifest.get("artifacts") or [])
        if isinstance(artifact, dict)
    ]

    installed_paths: set[str] = set()
    for artifact in artifacts:
        raw_path = artifact.get("path")
        if raw_path:
            installed_paths.add(Path(str(raw_path)).as_posix())
    for community in manifest.get("community_templates") or []:
        if isinstance(community, dict) and community.get("installed_path"):
            installed_paths.add(Path(str(community["installed_path"])).as_posix())

    installed_template_sources: set[str] = set()
    for artifact in artifacts:
        source_path, _mode = _resolve_source_template(
            autoharness_home, workspace_path, artifact
        )
        if source_path is None:
            continue
        try:
            installed_template_sources.add(
                source_path.resolve().relative_to(autoharness_home).as_posix()
            )
        except ValueError:
            installed_template_sources.add(source_path.resolve().as_posix())

    primitives_installed = {
        value
        for value in (manifest.get("primitives_installed") or [])
        if isinstance(value, int)
    }

    for spec in NEW_ARTIFACT_SCAN_CLASSES:
        template_dir = autoharness_home / "templates" / spec["template_subdir"]
        if not template_dir.is_dir():
            continue
        template_suffix = spec["template_suffix"]
        for template_file in sorted(template_dir.glob(f"*{template_suffix}")):
            install_name = (
                template_file.name[: -len(template_suffix)] + spec["install_suffix"]
            )
            expected_rel = f"{spec['install_subdir']}/{install_name}"
            try:
                template_rel = template_file.resolve().relative_to(
                    autoharness_home
                ).as_posix()
            except ValueError:
                template_rel = template_file.resolve().as_posix()

            if expected_rel in installed_paths:
                continue
            if template_rel in installed_template_sources:
                continue
            if (workspace_path / Path(expected_rel)).exists():
                continue

            finding: dict[str, Any] = {
                "kind": "new-artifact",
                "artifact_class": spec["artifact_class"],
                "template": template_rel,
                "expected_path": expected_rel,
                "severity": "advisory",
                "reason": (
                    "Template exists in autoharness_home but has no installed "
                    "artifact or manifest entry; it may be newly added by a "
                    "harness upgrade. Review install applicability before adding."
                ),
            }

            rule = (
                PROMPT_INSTALL_RULES.get(install_name)
                if spec["artifact_class"] == "prompt"
                else None
            )
            if rule is not None:
                finding["install_rule"] = rule["rule"]
                required = rule["requires_primitive"]
                opt_in = rule.get("requires_opt_in")
                if opt_in:
                    # A workflow-policy opt-in (for example P-017 dark factory
                    # mode) cannot be confirmed from primitives_installed alone,
                    # so leave applicability to the operator. This prevents the
                    # tuner from auto-installing a policy-gated shim (such as the
                    # dark-mode trigger) into a workspace that never opted in.
                    finding["applicable"] = None
                    finding["requires_opt_in"] = opt_in
                elif required is None:
                    finding["applicable"] = True
                elif primitives_installed:
                    finding["applicable"] = required in primitives_installed
                else:
                    finding["applicable"] = None

            findings.append(finding)

    return findings


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

    browser_config = config.get("browser") or {}
    runtime_surfaces = profile.get("runtime_surfaces") or {}
    browser_tooling = [str(t) for t in (runtime_surfaces.get("browser_tooling") or [])]
    browser_cli_candidates = ["playwright", "puppeteer", "agent-browser"]
    detected_browser_cli = next(
        (t for t in browser_cli_candidates if any(t in tool for tool in browser_tooling)),
        "agent-browser",
    )
    browser_cli = str(browser_config.get("cli") or detected_browser_cli)
    variables.setdefault("BROWSER_CLI", browser_cli)
    variables.setdefault("BROWSER_HEADLESS_FLAG", str(browser_config.get("headless_flag") or "--headless"))

    experiments_config = config.get("experiments") or {}
    raw_branch_prefix = str(experiments_config.get("branch_prefix") or "experiment/")
    if not raw_branch_prefix.endswith("/"):
        raw_branch_prefix = raw_branch_prefix + "/"
    variables.setdefault("EXPERIMENT_BRANCH_PREFIX", raw_branch_prefix)

    raw_results_dir = str(experiments_config.get("results_dir") or "docs/experiments")
    _results_path = Path(raw_results_dir)
    if _results_path.is_absolute() or ".." in _results_path.parts:
        raw_results_dir = "docs/experiments"
    variables.setdefault("EXPERIMENT_RESULTS_DIR", raw_results_dir)

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


def _add_frontmatter_tier_check(
    report: dict[str, Any],
    key: str,
    file_path: Path,
) -> None:
    """Validate that an agent file declares model_tier and max_subagent_tier
    as integers (in range 1–3) within its YAML frontmatter block."""
    if not file_path.exists():
        report["targeted_checks"][key] = {
            "path": str(file_path),
            "ok": False,
            "reason": "missing file",
        }
        return

    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        report["targeted_checks"][key] = {
            "path": str(file_path),
            "ok": False,
            "reason": "no YAML frontmatter (file does not begin with ---)",
        }
        return

    end_marker = content.find("\n---", 3)
    if end_marker == -1:
        report["targeted_checks"][key] = {
            "path": str(file_path),
            "ok": False,
            "reason": "unclosed YAML frontmatter (no closing ---)",
        }
        return

    frontmatter_text = content[3:end_marker].strip()
    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        report["targeted_checks"][key] = {
            "path": str(file_path),
            "ok": False,
            "reason": f"invalid YAML frontmatter: {exc}",
        }
        return

    errors = []
    for field in ("model_tier", "max_subagent_tier"):
        value = frontmatter.get(field)
        if value is None:
            errors.append(f"missing field: {field}")
        elif not isinstance(value, int):
            errors.append(
                f"{field} must be an integer, got {type(value).__name__}: {value!r}"
            )
        elif value < 1 or value > 3:
            errors.append(f"{field} out of range 1–3: {value}")

    report["targeted_checks"][key] = {
        "path": str(file_path),
        "ok": not errors,
        "errors": errors,
    }


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


def _defined_policy_ids(registry_text: str) -> set[int]:
    """Return the set of policy numbers defined by heading lines in a workflow
    policy registry (``## P-001: ...`` / ``### P-013.1 — ...``)."""
    return {
        int(match)
        for match in re.findall(r"^#{2,4}\s+P-(\d+)", registry_text, re.MULTILINE)
    }


def _resolve_policy_registry(
    workspace_path: Path, autoharness_home: Path | None
) -> Path | None:
    """Resolve the authoritative workflow-policy registry.

    Prefers the installed registry (``.github/policies/workflow-policies.md`` in a
    real target install), then falls back to the ``autoharness_home`` template
    (the dogfood self-install never installs a policies mirror). Returns ``None``
    when neither is resolvable so reference validation is existence-gated rather
    than a false failure.
    """
    installed = workspace_path / ".github" / "policies" / "workflow-policies.md"
    if installed.exists():
        return installed
    if autoharness_home is not None:
        template = (
            Path(autoharness_home)
            / "templates"
            / "policies"
            / "workflow-policies.md.tmpl"
        )
        if template.exists():
            return template
    return None


def _check_copilot_code_review_instruction(
    report: dict[str, Any],
    workspace_path: Path,
    manifest: dict[str, Any],
    autoharness_home: Path | None = None,
) -> None:
    """Deterministic frontmatter + placeholder guard for the Copilot code-review
    focus instruction.

    Expectedness is gated on manifest membership: the installer only records
    ``.github/instructions/copilot-code-review.instructions.md`` in the harness
    manifest for GitHub-hosted compositions, so a manifest-listed entry means the
    file is a required focus surface for this workspace. When the file is expected
    (manifest-listed) but missing, this records an ``ok: false`` targeted check so
    verification fails — the manifest checksum scan only warns on a deleted
    artifact, and warnings do not fail the report. When the file is not
    manifest-listed (a composition that never installed it), an absent file is a
    no-op. When the file is present it is always validated: the YAML frontmatter is
    parsed so a flipped ``excludeAgent`` value is caught (a substring check cannot
    distinguish the frontmatter value from the identical string in the body prose),
    and the installed file is scanned for unresolved ``{{PLACEHOLDER}}`` tokens.
    Finally, any ``P-NNN`` policy references in the harness-enforced summary are
    resolved against the authoritative workflow-policy registry (the installed
    ``.github/policies/workflow-policies.md`` or the ``autoharness_home`` template
    fallback); a reference to an undefined policy fails the check so a stale
    enforcement summary cannot pass silently. Reference validation is
    existence-gated: when no registry is resolvable it is skipped rather than
    failed.
    """
    relative_path = ".github/instructions/copilot-code-review.instructions.md"
    path = workspace_path / relative_path
    manifest_paths = {
        str(artifact.get("path") or "").replace("\\", "/")
        for artifact in (manifest.get("artifacts") or [])
        if isinstance(artifact, dict)
    }
    expected = relative_path in manifest_paths

    if not path.exists():
        if expected:
            report["targeted_checks"]["copilot_code_review_frontmatter"] = {
                "path": str(path),
                "ok": False,
                "errors": [
                    "manifest-listed copilot-code-review focus instruction is "
                    "missing from the workspace"
                ],
            }
        return

    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", text, re.DOTALL)
    frontmatter: dict[str, Any] = {}
    if not match:
        errors.append("missing or unterminated YAML frontmatter block")
    else:
        try:
            loaded = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            errors.append(f"invalid YAML frontmatter: {exc}")
        else:
            if isinstance(loaded, dict):
                frontmatter = loaded
            else:
                errors.append("frontmatter is not a mapping")

    exclude_agent = frontmatter.get("excludeAgent")
    if exclude_agent != "cloud-agent":
        errors.append(
            f"excludeAgent must be 'cloud-agent' (got {exclude_agent!r}); "
            "'code-review' would silence the reviewer and 'coding-agent' is invalid"
        )
    apply_to = frontmatter.get("applyTo")
    if apply_to != "**":
        errors.append(f"applyTo must be '**' (got {apply_to!r})")

    unresolved = _find_unresolved_placeholders(path)
    if unresolved:
        tokens = sorted({item["placeholder"] for item in unresolved})
        errors.append("unresolved template placeholders: " + ", ".join(tokens))

    registry = _resolve_policy_registry(workspace_path, autoharness_home)
    if registry is not None:
        defined = _defined_policy_ids(registry.read_text(encoding="utf-8"))
        referenced = {
            token: int(token[2:]) for token in re.findall(r"P-\d+", text)
        }
        undefined = sorted(
            token for token, number in referenced.items() if number not in defined
        )
        if undefined:
            errors.append(
                "harness-enforced summary references undefined policies: "
                + ", ".join(undefined)
            )

    report["targeted_checks"]["copilot_code_review_frontmatter"] = {
        "path": str(path),
        "ok": not errors,
        "errors": errors,
    }


def _add_runtime_validation_profile_check(
    report: dict[str, Any],
    profile_path: Path,
    profile: dict[str, Any],
    installed_packs: list[str],
) -> None:
    runtime_validation = profile.get("runtime_validation")
    runtime_surfaces = profile.get("runtime_surfaces") or {}

    missing: list[str] = []
    errors: list[str] = []
    manifest_surfaces: set[str] = set()
    expected_surfaces_from_profile: set[str] = set()
    surfaces_expected: set[str] = set()

    surface_flags = {
        "cli": bool(runtime_surfaces.get("cli")),
        "api": bool(runtime_surfaces.get("public_api")),
        "browser": bool(runtime_surfaces.get("web_ui")),
        "background-job": bool(runtime_surfaces.get("background_jobs")),
    }
    expected_surfaces_from_profile = {
        surface_name for surface_name, present in surface_flags.items() if present
    }

    if not isinstance(runtime_validation, dict):
        missing.append("runtime_validation")
    else:
        validator_manifest = runtime_validation.get("validator_manifest")
        validation_expectations = runtime_validation.get("validation_expectations")
        releasability = runtime_validation.get("releasability")

        if not isinstance(validator_manifest, dict):
            missing.append("runtime_validation.validator_manifest")
        else:
            raw_surfaces = validator_manifest.get("surfaces")
            if not isinstance(raw_surfaces, list):
                missing.append("runtime_validation.validator_manifest.surfaces")
            else:
                for index, entry in enumerate(raw_surfaces):
                    if not isinstance(entry, dict):
                        errors.append(
                            f"runtime_validation.validator_manifest.surfaces[{index}] must be an object"
                        )
                        continue
                    surface_name = entry.get("surface")
                    if isinstance(surface_name, str) and surface_name:
                        manifest_surfaces.add(surface_name)
                    else:
                        errors.append(
                            f"runtime_validation.validator_manifest.surfaces[{index}].surface missing"
                        )

                    probe_hints = entry.get("probe_hints")
                    if not isinstance(probe_hints, list):
                        errors.append(
                            f"runtime_validation.validator_manifest.surfaces[{index}].probe_hints missing"
                        )

                    manual_checkpoints = entry.get("manual_checkpoints")
                    if not isinstance(manual_checkpoints, list):
                        errors.append(
                            f"runtime_validation.validator_manifest.surfaces[{index}].manual_checkpoints missing"
                        )

        if not isinstance(validation_expectations, dict):
            missing.append("runtime_validation.validation_expectations")
        else:
            raw_surfaces_expected = validation_expectations.get("surfaces_expected")
            if not isinstance(raw_surfaces_expected, list):
                missing.append("runtime_validation.validation_expectations.surfaces_expected")
            else:
                surfaces_expected = {
                    str(surface_name)
                    for surface_name in raw_surfaces_expected
                    if isinstance(surface_name, str) and surface_name
                }

            if "required" not in validation_expectations:
                missing.append("runtime_validation.validation_expectations.required")
            elif expected_surfaces_from_profile and not bool(validation_expectations.get("required")):
                errors.append(
                    "runtime_validation.validation_expectations.required must be true when runtime surfaces were detected"
                )

            if "minimum_verdict" not in validation_expectations:
                missing.append("runtime_validation.validation_expectations.minimum_verdict")

        if not isinstance(releasability, dict):
            missing.append("runtime_validation.releasability")
        else:
            if "required" not in releasability:
                missing.append("runtime_validation.releasability.required")
            if "status_when_satisfied" not in releasability:
                missing.append("runtime_validation.releasability.status_when_satisfied")
            if not isinstance(releasability.get("required_evidence"), list):
                missing.append("runtime_validation.releasability.required_evidence")

            needs_releasability = bool(runtime_surfaces.get("deployment_manifests")) or (
                "release-observability" in installed_packs
            )
            if needs_releasability and not bool(releasability.get("required")):
                errors.append(
                    "runtime_validation.releasability.required must be true when deployment or release-observability signals are present"
                )

    missing_manifest_surfaces = sorted(expected_surfaces_from_profile - manifest_surfaces)
    if missing_manifest_surfaces:
        errors.append(
            "validator_manifest is missing detected runtime surfaces: "
            + ", ".join(missing_manifest_surfaces)
        )

    missing_expected_surfaces = sorted(expected_surfaces_from_profile - surfaces_expected)
    if missing_expected_surfaces:
        errors.append(
            "validation_expectations.surfaces_expected is missing detected runtime surfaces: "
            + ", ".join(missing_expected_surfaces)
        )

    report["targeted_checks"]["runtime_validation_profile_contract"] = {
        "path": str(profile_path),
        "ok": not missing and not errors,
        "missing": missing,
        "errors": errors,
        "expected_surfaces": sorted(expected_surfaces_from_profile),
        "manifest_surfaces": sorted(manifest_surfaces),
        "surfaces_expected": sorted(surfaces_expected),
    }


def _run_portability_scan(workspace_path: Path) -> list[dict[str, Any]]:
    """Scan harness artifact directories for non-portable environment-specific paths."""
    scan_dirs = [
        ".github/agents",
        ".github/skills",
        ".github/instructions",
        ".github/prompts",
        ".github/policies",
    ]
    scan_files = [
        ".github/copilot-instructions.md",
    ]
    compiled = [
        (r["rule"], re.compile(r["pattern"]), r["severity"], r["message"])
        for r in PORTABILITY_RULES
    ]
    allow_globs: dict[str, list[str]] = {}
    for rule_name, glob_pattern in PORTABILITY_ALLOW_LIST:
        allow_globs.setdefault(rule_name, []).append(glob_pattern)

    findings: list[dict[str, Any]] = []
    candidate_files: list[Path] = []
    for scan_dir in scan_dirs:
        base = workspace_path / scan_dir
        if base.exists():
            candidate_files.extend(sorted(base.rglob("*.md")))
    for rel_file in scan_files:
        p = workspace_path / rel_file
        if p.exists():
            candidate_files.append(p)

    for file_path in candidate_files:
        relative = _relative_workspace_path(workspace_path, file_path)
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for rule_name, compiled_re, severity, message in compiled:
            if any(
                fnmatch.fnmatch(relative, g)
                for g in allow_globs.get(rule_name, [])
            ):
                continue
            for line_no, line in enumerate(lines, start=1):
                match = compiled_re.search(line)
                if match:
                    findings.append({
                        "rule": rule_name,
                        "severity": severity,
                        "path": relative,
                        "line": line_no,
                        "match": match.group(0),
                        "message": message,
                    })
                    break
    return findings


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
            from_version = proposal.get("from_version") or "(missing)"
            to_version = proposal.get("to_version") or "(current)"
            summary = (
                proposal.get("summary")
                or proposal.get("action")
                or proposal.get("contract", "migration")
            )
            lines.append(
                f"- {proposal.get('contract', 'migration')}: {summary} "
                f"({from_version} -> {to_version})"
            )
    else:
        lines.append("none")

    lines.extend(["", "## New Artifacts (Uninstalled Templates)", ""])
    if report.get("new_artifacts"):
        for finding in report["new_artifacts"]:
            applicable = finding.get("applicable")
            opt_in = finding.get("requires_opt_in")
            if applicable is True:
                applicability = "applicable"
            elif applicable is False:
                applicability = "not applicable"
            elif opt_in:
                applicability = f"operator-decides (requires {opt_in} opt-in)"
            elif "applicable" in finding:
                applicability = "applicability unknown"
            else:
                applicability = "review applicability"
            rule = finding.get("install_rule")
            rule_note = f", rule: {rule}" if rule else ""
            lines.append(
                f"- {finding.get('artifact_class', 'artifact')}: "
                f"`{finding.get('template', '')}` -> "
                f"`{finding.get('expected_path', '')}` "
                f"({applicability}{rule_note})"
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
            if check.get("errors"):
                lines.append(f"  errors: {'; '.join(check['errors'])}")
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

    lines.extend(["", "## Portability Findings", ""])
    portability_findings = report.get("portability_findings") or []
    if portability_findings:
        for finding in portability_findings:
            lines.append(
                f"- [{finding['severity']}] {finding['rule']} @ "
                f"{finding['path']}:{finding['line']}: {finding['message']} "
                f"(match: `{finding['match']}`)"
            )
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
        "new_artifacts": [],
        "targeted_checks": {},
        "learning_signals": _empty_learning_signals(),
        "portability_findings": [],
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
        report["report_paths"] = {"json": str(json_path), "markdown": str(markdown_path)}
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_markdown_report(report, markdown_path)
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

    report["migration_proposals"].extend(
        _scan_agent_identity_migrations(workspace_path, profile)
    )

    report["new_artifacts"] = _scan_uninstalled_templates(
        workspace_path, autoharness_home, manifest
    )

    installed_packs = [
        str(pack)
        for pack in (manifest.get("capability_packs") or config.get("capability_packs") or [])
        if str(pack) in SUPPORTED_CAPABILITY_PACKS
    ]

    variables = _derive_template_variables(workspace_path, manifest, config, profile, registry)
    report["learning_signals"] = _mine_learning_signals(workspace_path, variables, config)

    report["blockers"].extend(_scan_manifest_scalar_placeholders(manifest, manifest_path))

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

        try:
            stage_path = _normalize_stage_path(staging_root, relative_path)
        except ValueError as exc:
            report["skipped"].append(
                {
                    "path": relative_path,
                    "template": str(artifact.get("template", "")),
                    "reason": str(exc),
                }
            )
            continue
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

    if profile_path.exists() and profile:
        _add_runtime_validation_profile_check(
            report,
            profile_path,
            profile,
            installed_packs,
        )

    for pack in installed_packs:
        for assertion in PACK_ASSERTIONS.get(pack, []):
            _add_text_check(
                report,
                assertion["key"],
                workspace_path / assertion["path"],
                assertion["must_contain"],
                [tuple(pair) for pair in assertion.get("must_precede") or []],
            )

    community_templates = manifest.get("community_templates") or []
    community_results: list[dict[str, Any]] = []
    for ct in community_templates:
        if not isinstance(ct, dict):
            community_results.append({
                "template_id": "unknown",
                "installed_path": "",
                "ok": False,
                "reason": "malformed entry (not a dict)",
            })
            continue
        tid = ct.get("template_id", "unknown")
        installed = str(ct.get("installed_path", ""))
        expected_installed_checksum = ct.get("installed_checksum", "")
        expected_source_checksum = ct.get("source_checksum", "")
        template_path_rel = str(ct.get("template_path", ""))
        # Validate paths are relative and don't escape roots
        if (
            not installed
            or not template_path_rel
            or installed.startswith(("/", "\\"))
            or template_path_rel.startswith(("/", "\\"))
            or ".." in installed.split("/")
            or ".." in installed.split("\\")
            or ".." in template_path_rel.split("/")
            or ".." in template_path_rel.split("\\")
        ):
            community_results.append({
                "template_id": tid,
                "installed_path": installed,
                "ok": False,
                "reason": "invalid path (must be relative, no parent traversal)",
            })
            continue
        ct_path = workspace_path / installed
        if ct_path.exists():
            actual_installed_checksum = hashlib.sha256(
                ct_path.read_bytes()
            ).hexdigest()
            installed_ok = actual_installed_checksum == expected_installed_checksum
            # Check for upstream template updates via source_checksum
            upstream_updated = False
            if expected_source_checksum and template_path_rel:
                source_tmpl = autoharness_home / template_path_rel
                if source_tmpl.exists():
                    actual_source_checksum = hashlib.sha256(
                        source_tmpl.read_bytes()
                    ).hexdigest()
                    if actual_source_checksum != expected_source_checksum:
                        upstream_updated = True
            entry: dict[str, Any] = {
                "template_id": tid,
                "installed_path": installed,
                "ok": installed_ok and not upstream_updated,
                "installed_checksum_ok": installed_ok,
                "upstream_updated": upstream_updated,
            }
            if not installed_ok:
                entry["reason"] = "checksum mismatch"
                entry["expected_checksum"] = expected_installed_checksum
                entry["actual_checksum"] = actual_installed_checksum
            elif upstream_updated:
                entry["reason"] = "upstream template updated"
            community_results.append(entry)
        else:
            community_results.append({
                "template_id": tid,
                "installed_path": installed,
                "ok": False,
                "reason": "missing file",
            })
    report["community_templates"] = community_results

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

    _check_copilot_code_review_instruction(
        report, workspace_path, manifest, autoharness_home
    )

    artifact_paths = {
        str(artifact.get("path") or "").replace("\\", "/")
        for artifact in (manifest.get("artifacts") or [])
        if isinstance(artifact, dict)
    }
    dark_factory_installed = bool(
        {
            ".github/prompts/feature-flow-dark.prompt.md",
        }
        & artifact_paths
    )
    if dark_factory_installed:
        for assertion in DARK_FACTORY_ASSERTIONS:
            assertion_path = str(assertion["path"]).replace("\\", "/")
            assertion_file = workspace_path / assertion["path"]
            requires_pack = assertion.get("requires_pack")
            if requires_pack and requires_pack not in installed_packs:
                continue
            if (
                not assertion.get("required")
                and assertion_path not in artifact_paths
                and not assertion_file.exists()
            ):
                continue
            _add_text_check(
                report,
                assertion["key"],
                assertion_file,
                assertion["must_contain"],
                [tuple(pair) for pair in assertion.get("must_precede") or []],
            )

    # Conditional: when both stage and ship agents are installed (two-agent
    # model) AND the workspace is a harness-installed workspace (manifest
    # present), the role-enforcement instruction file must also be present.
    # We gate on the manifest to avoid false failures in the autoharness repo
    # itself, which defines the templates but does not install them locally.
    stage_agent = workspace_path / ".github/agents/.stage.agent.md"
    ship_agent = workspace_path / ".github/agents/.ship.agent.md"
    role_enforcement_instruction = workspace_path / ".github/instructions/role-enforcement.instructions.md"
    if stage_agent.exists() and ship_agent.exists() and manifest_path.exists():
        _add_text_check(
            report,
            "installed_role_enforcement_instruction",
            role_enforcement_instruction,
            [
                "Pre-Mutation Check Protocol",
                "Role Boundary (NON-NEGOTIABLE)",
                "P-010",
                "Fail-closed",
            ],
        )

    _add_frontmatter_tier_check(
        report,
        "orchestrator_tier_fields",
        workspace_path / ".github/agents/_orchestrator.agent.md",
    )

    project_name = variables.get("PROJECT_NAME", workspace_path.name)
    project_name_pattern = re.compile(
        r"for the \*\*" + re.escape(project_name) + r"\*\* repository"
    )
    for agent_file, check_key in [
        (".github/agents/_orchestrator.agent.md", "orchestrator_workspace_identity"),
        (".github/agents/.stage.agent.md", "stage_workspace_identity"),
        (".github/agents/.ship.agent.md", "ship_workspace_identity"),
    ]:
        agent_path = workspace_path / agent_file
        if agent_path.exists():
            content = agent_path.read_text(encoding="utf-8")
            has_project_name = bool(project_name_pattern.search(content))
            has_unresolved = "{{PROJECT_NAME}}" in content
            report["targeted_checks"][check_key] = {
                "path": agent_file,
                "ok": has_project_name and not has_unresolved,
                "has_project_name": has_project_name,
                "has_unresolved_variable": has_unresolved,
            }

    portability_findings = _run_portability_scan(workspace_path)
    report["portability_findings"] = portability_findings
    for finding in portability_findings:
        report["warnings"].append({
            "kind": "portability-finding",
            "path": finding["path"],
            "message": finding["message"],
            "rule": finding["rule"],
            "severity": finding["severity"],
        })

    report["warning_instances"] = len(report["warnings"])
    report["warnings"] = _summarize_warnings(report["warnings"])

    json_path = staging_root / "verify-workspace-report.json"
    markdown_path = staging_root / "verify-workspace-report.md"
    report["report_paths"] = {"json": str(json_path), "markdown": str(markdown_path)}
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown_report(report, markdown_path)
    return report
