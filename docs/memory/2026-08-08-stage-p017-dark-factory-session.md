# Stage Session Memory — P-017 Dark-Factory Activation (2026-08-08)

- **Agent**: Stage (autoharness). Model route pinned: `claude-opus-4.8` / `anthropic` / `high`.
- **Mode**: P-017 dark-factory (AFK). `visibility_mode=local-only/degraded` (agent-intercom unavailable).
- **Boundary honored**: no source/config/template edits, no build/test/lint, no shipment claim, no PR/push/merge. Planning + backlog artifacts only.

## Tool / gate status

- `TOOL_OK: backlogit` (v1.8.0), registry `features.sizing:true`, `features.shipments:true`.
- `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE` — file-based fallback over read-only source workspaces `C:\Source\GitHub\{backlogit,engram,graphtor}`.
- `INDEX_SYNC_OK` at start (726 artifacts).
- Crash-resumption: 21 stage checkpoints, quarantined=0, zero active candidates → no recovery needed (steady state).

## Frozen scope disposition

| Unit | Source | Outcome | Shipment |
|---|---|---|---|
| 1 | 082-F (mandated first cursor) | Staged: 3 tasks | **120-S** (first eligible, no predecessor) |
| 2 | F02FD596 + E8B5B3C5 (routing group) | Feature 113-F, 5 tasks | **121-S** (depends_on 120-S) |
| 3 | BED0DDED | DEFERRED external-blocked — no shipment | — (tracker kept ACTIVE) |
| 4 | 47971057 (bounded increment) | Feature 114-F, 3 tasks | **122-S** (depends_on 121-S) |

Living trackers untouched / kept ACTIVE: 34D50F2D, 33CC445C, 936C68F3, 84D8E6AB.

## Shipments (dependency / queue order)

1. **120-S** — `[082-F, 082.001-T, 082.002-T, 082.003-T]`. First eligible cursor; contains 082-F. Intra: 082.003-T depends_on 082.001-T + 082.002-T.
2. **121-S** — `[113-F, 113.001-T..113.005-T]`. depends_on 120-S. Intra: 002→001, 003→001, 004→002, 005→004.
3. **122-S** — `[114-F, 114.001-T, 114.002-T, 114.003-T]`. depends_on 121-S. Intra: 002→001, 003→002.

## Review outcomes

- 082.001-R **PASS** (no P0/P1; hardening not required).
- 113.001-R **PASS** (1 fix cycle; plan-hardening H1–H9 applied per P-006).
- 114.001-R **PASS** (bounded detection-only increment; hardening not required).
- **No unresolved P0/P1 findings.**

## Sizing (two-axis, 2h-rule-v1)

- 082: 082.001-T S/low, 082.002-T S/low, 082.003-T M/medium.
- 113: 113.001-T S/medium, 113.002-T M/high, 113.003-T M/medium, 113.004-T M/high, 113.005-T M/high (high-complexity de-risked by hardening doc; sizes held ≤M).
- 114: 114.001-T M/medium, 114.002-T M/medium, 114.003-T S/low.

## Stash disposition

- **Archived (fully consumed)**: F02FD596, E8B5B3C5 → became 113-F/121-S.
- **Kept ACTIVE (deferred/partially-consumed living trackers)**: BED0DDED (external-blocked: backlogit hardcodes `.backlogit`, no dir override — annotated), 47971057 (bounded increment harvested as 114-F/122-S; provisioning execution + open design questions deferred — annotated), 34D50F2D, 33CC445C, 936C68F3, 84D8E6AB.

## Deferred / halted with reason

- **BED0DDED** — `.backlogit`→`.backlog` rename is EXTERNAL-BLOCKED: external backlogit binary hardcodes `.backlogit` (`WorkspaceStorageRoot` internal/core/workspace.go:56 + ~31 literals; only `BACKLOGIT_LOG_LEVEL/_FORMAT` env, no dir knob). Autoharness-side-first rename would silently split state. Fail-closed DEFER; no shipment created.
- **47971057** — actual runtime provisioning EXECUTION + all supply-chain/OS-matrix/version-channel/elevation/offline/model-provisioning/rollback open questions deferred pending operator; only bounded detection+checklist+ordering increment staged.

## Next session

- Ship owns execution: first eligible cursor = **120-S** (082-F). Serial chain 120-S → 121-S → 122-S.
- Re-triage deferred portions only after operator answers: BED0DDED (needs backlogit dir-override upstream or sanctioned migration path), 47971057 (open design questions).
