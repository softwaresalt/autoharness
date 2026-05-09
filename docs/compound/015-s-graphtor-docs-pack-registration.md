---
id: compound-015-s-graphtor-docs-pack-registration
title: "Capability Pack Registration: graphtor-docs overlay pattern"
problem_type: capability-pack-registration
category: autoharness-templates
root_cause: "Capability packs with dual config surfaces (MCP tool registration + source-index config) require a dedicated profile field per surface to avoid ambiguous variable resolution."
tags: [capability-pack, graphtor-docs, workspace-profile, sources_path, config_paths, schema-design]
created: 2026-05-09
shipment: 015-S
merge_sha: d8b039e14d119fe2a7b226e5be662040a9a1091e
---

# Capability Pack Registration: graphtor-docs overlay pattern

## Problem

When registering a capability pack whose tool has two distinct config surfaces
(MCP server registration vs. source/index configuration), using a single
`config_paths[]` array for both leads to:

1. Ambiguous `config_paths[0]` resolution — `.mcp.json` could sort before `sources.yaml`
2. Template variables pointing to the wrong file at install time
3. Instruction template language that conflates tool-name registration with data configuration

## Solution

Separate the two config surfaces into dedicated profile fields:

* `config_paths[]` — MCP and other non-sources config files (.mcp.json, .vscode/mcp.json)
* `sources_path` (string) — path to the source-index configuration file (sources.yaml)

Resolve `{{GRAPHTOR_SOURCES_PATH}}` from `graphtor_docs.sources_path` (not `config_paths[0]`).

## Registration Checklist (for any future capability pack)

When a pack has multiple config file types, ask:
- Does each config file serve a distinct purpose?
- Could a single `config_paths[]` array produce ambiguous `[0]` resolution?
- If yes → add a dedicated profile field per config type

## Template Language Rule

MCP tool names are registered through MCP configuration files (`.mcp.json`, `.vscode/mcp.json`,
editor settings). They are NOT derived from data/index configuration files. Keep these concepts
separate in instruction templates, schema descriptions, and skill documentation.

## Files Changed per Registration Point

A complete capability pack registration touches 10 artifact locations:
1. `schemas/harness-config.schema.json` — enum + config block
2. `schemas/workspace-profile.schema.json` — enum(s) + detection block
3. `templates/instructions/{pack}.instructions.md.tmpl` — new instruction template
4. `.github/skills/workspace-discovery/SKILL.md` — detection step
5. `.github/skills/install-harness/SKILL.md` — overlay table, instructions, weaving, variables
6. `.github/skills/tune-harness/SKILL.md` — drift detection + coherence checks
7. `templates/agents/stage.agent.md.tmpl` — pack guidance woven in
8. `templates/agents/ship.agent.md.tmpl` — pack guidance woven in
9. `src/autoharness/verify_workspace.py` — SUPPORTED_CAPABILITY_PACKS + PACK_ASSERTIONS
10. `docs/capability-packs.md` — row + full overlay contract section

## JSON Schema Editing Gotcha

`workspace-profile.schema.json` has enum arrays that appear in multiple places.
When editing with `old_str` matching, always include the full surrounding JSON
structure (closing braces, adjacent properties) to avoid ambiguous matches.
Use `python -c "import json; json.load(open('schemas/workspace-profile.schema.json'))"` to
validate after every edit.
