---
session: ship-010-S
feature: 010-F
shipment: 010-S
branch: feat/session-lifecycle-gates
pr: 38
merged_at: "2026-05-07T01:53:32Z"
merge_sha: 81cfa39a46751fe285e32a54b97ed7262c099a51
status: shipped
---

# Ship Session Memory — 010-S

## What was shipped

Session lifecycle gates and backlogit sync for Stage and Ship agent templates.

## Tasks completed

- 010.001-T: Step 0.1 (Backlog Index Sync) added to Stage and Ship templates + dogfood agents
- 010.002-T: Closure DB resync step added to Ship Step 6 (step 9)
- 010.003-T: Merge Confirmation Gate (NON-NEGOTIABLE) added before Ship Step 6.0

## Key decisions

- Step 0.1 wording: "after tool probes, before semantic reads" — not "before any reads"
  (MCP probes in Step 0.0 are themselves reads; Copilot review caught this)
- Closure sync failure broadcast gated behind agent-intercom pack
- `merge-base --is-ancestor` used for merge confirmation (not `git log --oneline -1`)
- 010.001-T and 010.002-T collapsed into one Ship Step 6 step (avoid duplicate adjacent sync calls)

## Files changed

- `templates/agents/stage.agent.md.tmpl`
- `templates/agents/ship.agent.md.tmpl`
- `src/autoharness/verify_workspace.py`
- `.github/agents/stage.agent.md`
- `.github/agents/ship.agent.md`
- `.github/skills/install-harness/SKILL.md`
- `tests/test_verify_workspace.py`

## Next steps

None. Shipment complete and shipped.
