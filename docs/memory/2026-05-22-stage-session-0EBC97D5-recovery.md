---
session: stage-2026-05-22
type: memory
---

# Stage Session — 2026-05-22

## Stash Entry Investigated

**0EBC97D5** — "install non-Orchestrator/Stage/Ship agents into a single subagents/ directory instead of categorized subagent directories"

**Status**: Absent from both active `.backlogit/stash.jsonl` and `.backlogit/archive/stash.jsonl`. Entry was lost from backlogit state. Recovered as structured backlog feature 048-F.

## Investigation Findings

- Stash entry 0EBC97D5 was NOT in any stash file — lost from backlogit state
- Related archived feature 031-F (stash `6AB4534F`): "Subagent directory convention" — archived as `harness_status: pending` (never executed)
- Current `templates/agents/` has `review/` and `research/` categorized subdirectories (NOT flat `subagents/`)
- `install-harness/SKILL.md` still maps agents to `agents/review/` and `agents/research/` output paths
- Two agents (language-engineer, prompt-builder) were already mapped to `subagents/` in session state files (not committed) — confirms partial prior intent
- `verify-harness/SKILL.md` line 60 references `.github/agents/review/`
- `templates/foundation/AGENTS.md.tmpl` lines 340-341 reference `.github/agents/review/`
- `verify_workspace.py`: no hardcoded `review/` or `research/` path assertions — NO changes needed

## Backlog Artifacts Created

| ID | Type | Title | Status |
|---|---|---|---|
| 048-F | feature | Consolidate non-top-level agent install paths to single subagents/ directory | queued |
| 048.001-T | task | Update install-harness/SKILL.md: consolidate review/ and research/ to subagents/ | queued |
| 048.002-T | task | Update verify-harness/SKILL.md: review payload build step → subagents/ | queued |
| 048.003-T | task | Update templates/foundation/AGENTS.md.tmpl: legacy-agent table → subagents/ | queued |
| 048-S | shipment | Subagents flat install path consolidation (0EBC97D5) | queued |

Plan document: `docs/exec-plans/2026-05-22-subagents-flat-install-paths-plan.md`

## Queue State (undisturbed)

044-F / 044.001-DL and 045-F / 045.001-DL remain queued and undisturbed.
003-DL remains queued and undisturbed.

## Next Steps for Orchestrator

- 048-S is queued and ready for Ship to claim
- Ship should claim 048-S, execute tasks 048.001-T → 048.002-T → 048.003-T (any order, independent), verify checklist in plan doc, then PR/merge
- 044-F and 045-F deliberations remain pending operator scheduling
