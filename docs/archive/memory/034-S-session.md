# Session Memory: 034-S Capability Packs Full Weave

**Date**: 2026-05-17  
**Branch**: `feat/capability-packs-full-weave`  
**PR**: #86  
**Shipment**: 034-S — Capability Packs Full Weave

---

## What Was Done

Installed and fully wove three capability packs into the autoharness dogfood workspace:

- **agent-engram** (036-F, 6 tasks) — Engram session-start binding, pre-work search, overlay contract
- **agent-intercom** (037-F, 4 tasks) — Intercom heartbeat, phase broadcasts, destructive-action gates, overlay contract
- **graphtor-docs** (038-F, 4 tasks) — graphtor-docs server check, pre-planning doc research, overlay contract

## Key Decisions

### graphtor-docs variable resolution
`graphtor-docs.instructions.md` is the only instruction template with `{{VARIABLE}}` placeholders. Must resolve at install time via discovery-first lookup before writing. Installed checksum is workspace-specific — tuner must re-render from template to compare (not raw template compare).

### binary_path vs binary_on_path (hard-won)
workspace-profile.yaml uses `binary_path: ""` (string path) for graphtor_docs, not `binary_path: true|false` (bool). workspace-discovery SKILL.md originally had `binary_on_path: true|false` in the struct definition — this was a P1 inconsistency caught in review cycle 1. Fixed by updating workspace-discovery to `binary_path: ""` and updating recommendation logic accordingly.

### Self-install mode placement
In self-install mode (`distribution.is_global_tool: true`), stage.agent.md and ship.agent.md live in `.github/agents/` alongside global artifacts, not in `.github/local-agents/`.

### Header corruption pattern
When making multi-block edits to agent files (e.g., inserting new Steps 0.1x), be careful not to accidentally delete existing heading lines. WS-D (036.004-T) accidentally removed `### Step 0: Session Start` from stage.agent.md and `### Step 0.5: Work Intake` + first bullet from ship.agent.md. These were caught and restored in GD-C (038.003-T). Always view the file context around the edit point before and after.

### graphtor-docs not in .mcp.json
The `.graphtor/bin/graphtor-docs.exe` binary exists but is NOT registered as an MCP server in `.mcp.json`. `mcp_configured: false` in workspace-profile. Pack is still installable and detectable via binary presence — `binary_path` being non-empty is sufficient for recommendation.

### Intercom + backlogit operator presentation rule
When both backlogit and agent-intercom are active, always present queued items to the operator via intercom before claiming — do not start build work silently. Combined rule documented in IC-D overlay contract.

### Admin merge for policy-separation
Branch protection on `softwaresalt/autoharness` requires at least one reviewer approval. Operator pre-authorized `--admin` flag for merge commits where review happens in-session via review skill. Using `gh pr merge {n} --merge --admin`.

## Routing Split (Engram + graphtor-docs)

When both packs are active:
- **Engram**: code relationships, impact analysis, git history, symbol lookup
- **graphtor-docs**: documentation lookup, API references, domain concept research

Both steps run before planning; only one step runs before build (use judgment based on question type).

## Review Findings (cycle 1)

Three P1 issues fixed post-PR:
1. `ship.agent.md` Step 0.5 — missing `* If a shipment exists, record its ID` sub-bullet
2. `workspace-discovery/SKILL.md` — `binary_on_path: bool` → `binary_path: string path`
3. `install-harness/SKILL.md` — `graphtor_docs.config_paths` → `graphtor_docs.sources_path`

## P2 Follow-up (stash 8FDEC777)

`workspace-profile.schema.json` lines 259-275 and `docs/capability-packs.md` lines 455-458 still reference `binary_on_path` — should be renamed to `binary_path` in a follow-up chore.

## Commit Log

```
fa9ff58 fix: address P1 review findings
75ae3c7 chore: archive completed 036-F/037-F/038-F task files post-done
74381c2 feat(038.004-T): harden graphtor-docs overlay contract in install-harness SKILL.md
fcb7c1e feat(038.003-T): weave graphtor-docs search-first protocol into stage.agent.md and ship.agent.md
5c447aa feat(038.002-T): install graphtor-docs.instructions.md with resolved template variables
6a6dd12 chore(038.001-T): GD-A graphtor-docs discovery complete
cb221ea feat(037.004-T): harden agent-intercom overlay contract in install-harness SKILL.md
[...11 more commits for 036-F and 037-F tasks]
```
