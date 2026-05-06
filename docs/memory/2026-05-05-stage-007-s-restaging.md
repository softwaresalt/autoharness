# 2026-05-05 Stage Memory: 007-S Restaging

## Scope Completed

Restaged shipment `007-S` after reviewing 006-S learnings and the current queued shipment/plan. No new feature scope was introduced; this was a plan and backlog refinement pass only.

## Decisions

- Kept `007.001-T` unchanged. The browser skill template task was already appropriately scoped.
- Strengthened `007.002-T` to require collision-resistant experiment result filenames under `{{EXPERIMENT_RESULTS_DIR}}` and to treat `docs/experiments` as a default, not a hardcoded path.
- Broadened `007.003-T` so install-harness work now includes explicit `browser-verification` overlay contract / weaving updates for `browser-automation/SKILL.md`, not just variable registration and skill manifest wiring.
- Added `007.004-T` as a separate verification task to preserve width isolation and the 2-hour rule. Verification now has first-class backlog representation rather than being hidden inside implementation tasks.
- Added dependency edges so Task 3 depends on Tasks 1-2, and Task 4 depends on Tasks 1-3.
- Rewrote the implementation plan so the plan and harvested backlog are consistent again.

## Artifacts Updated

- `.backlogit/queue/007-S.md`
- `.backlogit/queue/007.002-T.md`
- `.backlogit/queue/007.003-T.md`
- `.backlogit/queue/007.004-T.md` (new)
- `docs/exec-plans/2026-05-05-browser-experiment-skills-plan.md`

## Next Step for Ship

Claim `007-S` on the restaged branch/backlog state. Execute Tasks 1-2 in parallel if desired, then Task 3, then Task 4.
