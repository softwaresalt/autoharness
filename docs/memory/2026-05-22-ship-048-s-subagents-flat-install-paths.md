---
session_id: ship-048-s
shipment_id: 048-S
date: 2026-05-22
stash_source: 0EBC97D5
pr_number: 104
merge_sha: 605fb0565a0a7ccd010dae022a0205275ddda5d4
status: shipped
---

# Ship Session Memory — 048-S: Subagents Flat Install Path Consolidation

## Summary

Shipped shipment 048-S: consolidated non-top-level agent install path references
from legacy `agents/review/` and `agents/research/` to the canonical
`agents/subagents/` flat directory across three files.

## Commits

| SHA | Message |
|---|---|
| `2b5983a` | `feat: consolidate subagent install paths from review/ and research/ to subagents/ (048-S)` |
| `f4cc8a6` | `fix: address copilot review — revert Primitive map rows to template-source paths` |
| `605fb05` | Merge PR #104 (merge commit) |

## Changes Delivered

| File | Change |
|---|---|
| `.github/skills/install-harness/SKILL.md` | Install-paths table: replaced separate Review Personas + Research Agents rows with single consolidated `Subagents` row referencing `.github/agents/subagents/`; also updated `Agents` row to clarify top-level scope |
| `.github/skills/verify-harness/SKILL.md` | Review payload build step: `agents/review/` → `agents/subagents/` |
| `templates/foundation/AGENTS.md.tmpl` | Legacy-agent migration table: both `review` and `plan-review` rows updated to reference `agents/subagents/` |

## Copilot Review Findings

Copilot reviewed commit `2b5983a` and raised 3 threads:

1. **verify-harness/SKILL.md line 60** — "extra trailing backtick" — **Declined as false positive**: line has exactly 4 balanced backticks (2 code spans).

2. **install-harness/SKILL.md line 753** (Primitive 1 row) — "Template Groups column should reference template source paths, not install destinations" — **Valid**. `templates/agents/research/` exists; reverted to `agents/research/learnings-researcher`.

3. **install-harness/SKILL.md line 759** (Primitive 7 row) — "no `templates/agents/subagents/` directory" — **Valid**. `templates/agents/review/` exists; reverted to `agents/review/*`.

All 3 threads resolved before merge.

## Key Learning

The `install-harness/SKILL.md` Primitive map table column is **"Template Groups"** —
it documents autoharness source template directory paths, NOT install destination
paths. Template source directories like `templates/agents/research/` and
`templates/agents/review/` are stable identifiers that should not change when the
install output is consolidated to `agents/subagents/`. The correct place to document
consolidated install destinations is the **install-paths table** (the table with
`{workspace}/.github/...` paths), not the Primitive map.

This distinction is easy to miss: both tables look like path lists, but they serve
different documentation purposes. The Stage task spec (048.001-T) requested changes
to both tables, but only the install-paths table change was correct.

## Acceptance Criteria Status

| Criterion | Status |
|---|---|
| No `agents/review/` refs in install-harness/SKILL.md install-paths table | ✅ |
| No `agents/research/` refs in install-harness/SKILL.md install-paths table | ✅ |
| Install paths table consolidated to single Subagents row | ✅ |
| verify-harness/SKILL.md references `agents/subagents/` in review payload step | ✅ |
| AGENTS.md.tmpl legacy-agent table references `agents/subagents/` | ✅ |
| Primitive map rows preserved with template-source paths | ✅ (fixed via Copilot review) |
