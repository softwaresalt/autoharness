---
session: stage-stash-triage-046-047
date: 2026-05-21
agent: stage
status: complete
---

# Stage Session — Stash Triage → 046-F / 047-F

## Session Summary

Processed 3 stash entries (BB67C7CC, B502B2EB, FBDBB5CC) into structured
backlog with two queued shipments ready for Ship.

## Tool Status

- TOOL_DEGRADED: backlogit MCP — CLI fallback active (`backlogit`)
- INDEX_SYNC_OK (CLI fallback) — 263 artifacts at start, 267 at end
- ENGRAM_DEGRADED — MCP unavailable; file-based exploration used
- INTERCOM_DEGRADED — MCP unavailable; no broadcast capability
- GRAPHTOR_UNAVAILABLE — MCP unavailable; file-based doc search used

## Stash Entries Consumed

| ID | Kind | Priority | Disposition |
|---|---|---|---|
| BB67C7CC | bug | medium | → 046-F + 046.001-T; stash archived |
| B502B2EB | feature | medium | → 047-F + 047.001-T; stash archived |
| FBDBB5CC | feature | medium | → 047-F + 047.002-T; stash archived |

## Grouping Rationale

**046-F (standalone bug)**: BB67C7CC is a self-contained CLI/Python bug
in `src/autoharness/verify_workspace.py` and `cli.py`. Isolated from
template work. Low blast radius. No deliberation needed.

**047-F (grouped feature)**: B502B2EB and FBDBB5CC are grouped because:
1. Both introduce alternate model provider support (Gemini) — a shared
   mechanism that implies common template variable conventions
   (`{{ALT_*_PROVIDER}}`, `{{ALT_*_FAMILY}}`).
2. Both strengthen the local-first review strategy (complements 044-F
   direction from existing deliberation 044.001-DL).
3. Both are pure template-authoring work with no CLI or schema changes.
4. The two tasks within 047-F are width-isolated: 047.001-T touches
   only `templates/skills/doc-review/`, 047.002-T touches only
   `templates/agents/adversarial-review.agent.md.tmpl` and
   `templates/instructions/adversarial-review.instructions.md.tmpl`.

## Backlog Artifacts Created

| ID | Type | Title | Parent |
|---|---|---|---|
| 046-F | feature | Fix verify_workspace verification output path | — |
| 046.001-T | task | Audit and fix verify_workspace file-write paths | 046-F |
| 047-F | feature | Multi-model review enhancement: doc-review skill + adversarial-review upgrade | — |
| 047.001-T | task | Author documentation-review skill template | 047-F |
| 047.002-T | task | Upgrade adversarial-review agent template: recursion + alternate model | 047-F |

## Shipments Created

| Shipment ID | Title | Status | Items | Priority for Ship |
|---|---|---|---|---|
| 040-S | Fix verify_workspace output path (046-F) | queued | 046-F, 046.001-T | **#1 — claim first** |
| 041-S | Multi-model review enhancement: doc-review + adversarial-review (047-F) | queued | 047-F, 047.001-T, 047.002-T | #2 |

## Blast Radius Assessment

**046-F**: Low. Single Python module (`verify_workspace.py` + `cli.py`).
No template, schema, or cross-feature impact. Safe to ship in isolation.

**047-F**: Medium. New template file created (`templates/skills/doc-review/`),
existing template modified (`templates/agents/adversarial-review.agent.md.tmpl`,
`templates/instructions/adversarial-review.instructions.md.tmpl`).
No schema evolution. No CLI distribution change. install-harness SKILL.md
variable resolution table needs update as part of 047.001-T.

Plan-harden was evaluated and not required: neither feature touches schemas,
CLI distribution, or multiple template families simultaneously.

## Review Gating / Blockers for Ship

**040-S (046-F)**:
- No plan-review required — bug fix, low blast radius, Python only.
- Ship should run `pytest` / `uv run python -m pytest` after fix.
- Verify `verify-workspace-report.*` files land in `.autoharness/staging/`
  (not workspace root) in both happy-path and early-exit error-path cases.

**041-S (047-F)**:
- 047.001-T and 047.002-T can execute in parallel (different file sets).
- Ship must register new `doc-review` skill in `templates/skills/install-harness/SKILL.md`
  variable resolution table as part of 047.001-T (width-locked to that task).
- Quality gate: new `.tmpl` files must have valid YAML frontmatter,
  no unresolved `{{...}}` variables, and pass markdownlint MD001/MD025/MD041.
- No PR review gate dependency change: these are template files only.

## Existing Queue Context (not disturbed)

- 044-F / 044.001-DL: PR review automation strategy (queued, deliberation stage)
- 045-F / 045.001-DL: Runtime validation strategy (queued, deliberation stage)
- Active features 022-F, 023-F, 026-F, 028-F, 035-F: not touched.

## Next Steps for Orchestrator

1. Direct Ship to claim **040-S** for immediate execution.
2. After 040-S ships, direct Ship to claim **041-S**.
3. 044-F and 045-F remain in deliberation; no shipment exists for them yet —
   they need their open questions resolved before impl-plan can proceed.
