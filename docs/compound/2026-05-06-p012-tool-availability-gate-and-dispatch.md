---
title: "MCP Tool Pre-flight Gate (P-012) and Dispatch Agent Pattern"
date: 2026-05-06
problem_type: agent-workflow
category: harness-design
root_cause: Agents silently fell back to grep/cat filesystem reads when MCP tools were unavailable, without declaring degraded mode
tags: [p-012, mcp-tools, tool-availability, dispatch-agent, registry-driven]
shipment: 009-S
---

# MCP Tool Pre-flight Gate (P-012) and Dispatch Agent Pattern

## Problem: Silent Filesystem Fallback

When MCP tools were unavailable, agents would silently fall back to `grep`/`cat` operations on backlog JSONL and YAML files. This:
- Made failures invisible (no signal that the tool was down)
- Allowed operations to proceed with stale or partial data
- Violated the intent of the registry-driven tool abstraction

## Solution: P-012 and Step 0.0

P-012 (Tool Availability / Declared Degradation) requires agents to explicitly probe tools before any work begins and declare their mode. The probe uses read-only lightweight operations (not mutations). Outcomes:

- `TOOL_OK: {tool_name}` — tool responds correctly
- `TOOL_DEGRADED: {tool_name} — CLI fallback: {cli_command}` — MCP failed but registry has a CLI fallback
- `TOOL_UNAVAILABLE: {tool_name}` — no MCP and no CLI fallback → **halt**

**Exception**: If no backlog registry is installed at all (`.autoharness/backlog-registry.yaml` absent), file-backed mode is intentional (not degradation). P-012 applies only when a registry is present but tools are failing.

The probe reads `cli_command` from the registry for each required tool. This makes the gate registry-driven, not hardcoded to specific tool names.

## Dispatch Agent Template

The dispatch coordinator (`dispatch.agent.md.tmpl`) was added to support continuous Stage → Ship iteration. Key design decisions:

1. **Sequential mode (default)**: Stage → wait for shipment → Ship → repeat. Simpler, safer, P-001 compliant.
2. **Pipelined mode (opt-in)**: Stage prepares next batch while Ship executes current shipment. P-001 constraint: Stage MUST NOT touch the active Ship shipment's manifest.
3. **Stash reading**: Dispatch reads stash via the configured backlog tool (MCP or CLI) as declared in the registry. Do NOT hardcode `.autoharness/stash.jsonl` — the JSONL stash source of truth is marked **incubating** in the backlogit compatibility matrix and must not be assumed in templates.
4. **Circuit breakers**: 2 consecutive failures → halt; 5 cycles per session → halt; 2 stall iterations (Stage produces no shipment) → halt.

## Install-Harness Wiring Requirement

A new agent template is not useful unless it's listed in `install-harness/SKILL.md`. When adding any new `templates/agents/*.agent.md.tmpl`:
1. Add it to Step 2.4 pipeline agents list
2. Add it to the Primitive mapping table (Primitive 4 for orchestration agents)

Failing to wire it means target workspaces won't receive the agent during installation.

## Artifacts

- `templates/policies/workflow-policies.md.tmpl` — P-012 policy definition
- `templates/agents/stage.agent.md.tmpl` + `ship.agent.md.tmpl` — Step 0.0 Tool Availability Gate
- `templates/agents/dispatch.agent.md.tmpl` — new coordinator agent
- `.github/skills/install-harness/SKILL.md` — dispatch wired into Step 2.4 and Primitive 4
- `src/autoharness/verify_workspace.py` — `stage_tool_availability_gate`, `ship_tool_availability_gate` assertions
