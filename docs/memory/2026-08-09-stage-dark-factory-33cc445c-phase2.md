# Stage session — 2026-08-09 dark-factory bounded scope (six stash IDs)

**Route**: claude-opus-5 / anthropic / high. **Mode**: DARK_MODE_ACTIVE, P-017,
local-session visibility only (intercom unavailable).
**Base**: main @ `efeba82b`, single worktree, clean tree at session start.

## Outcome

Stage completed cleanly. Six scoped stash entries triaged; **one** actionable
local slice found and fully staged; five preserved as living trackers with
evidence-backed annotations. One shipment created: **`123-S`** (queued,
`queue_position: 1`) — the sole eligible Ship handoff token.

## Triage dispositions

| Stash | Disposition | Evidence |
|---|---|---|
| `84D8E6AB` | No local work; external tracker stays ACTIVE | Repo-wide search for `shipment_status_changed` = **0 hits**; no autoharness path reads `.backlogit/logs/*.jsonl`. The entry's own re-triage condition is not met. |
| `BED0DDED` | Still EXTERNAL-BLOCKED; ACTIVE | backlogit HEAD `fd8d2c9d` v1.8.0: `WorkspaceStorageRoot` still hardcodes `.backlogit` (workspace.go:57); hardcoded literals **grew to 245** under `internal/`; **no** directory-name env/config override exists. |
| `47971057` | Bounded increment SHIPPED (114-F/122-S); provisioning still DEFERRED; ACTIVE | All open design questions remain operator-unanswered. Supply-chain surface — must not be designed by agent guesswork. |
| `34D50F2D` | Candidate (d) SHIPPED (111-F/119-S); (a)/(c) DEFERRED; ACTIVE | Stale in-flight state superseded (uncommitted claims, "only 117-S eligible", checkpoint pointers). All checkpoints verified resolved. |
| `936C68F3` | Report-only slice SHIPPED (112-F/118-S); auto-repair still UNSUPPORTED; ACTIVE | Re-verified upstream: no `active->queued` edge, single-shot `ClaimShipment`, no record-only repair transition. Provenance guard reaffirmed — must stay active. |
| `33CC445C` | **FULLY CONSUMED → ARCHIVED** | Phase 1 shipped (110-F/117-S); Phase 2 re-validated as useful + non-duplicative, then harvested. |

## Created artifacts

* `014-DL` — deliberation, Option C (advisory-only deterministic resumption cursor)
* `docs/plans/2026-08-09-dag-next-eligible-resumption-advisory-plan.md` — impl-plan
  + P-006 hardening (H1–H6, H3b)
* `115-F` — covering feature
* `115.001-T` (M/medium) analyzer · `115.002-T` (S/low) CLI · `115.003-T` (S/medium) docs
* `115.001-R` — plan-review **PASS** after 1 fix cycle, P0/P1 clear
* `123-S` — shipment, task-only manifest `{115.001-T, 115.002-T, 115.003-T}`

Blocks edges: `115.002-T → 115.001-T`, `115.003-T → 115.002-T`. No cycles.

## Key design decision

Phase 2 is an **advisory-only** cursor. The shipped Phase 1 doc states a permanent
NON-GOAL that the gate will never "select or execute a 'next' shipment
automatically." That is preserved: the prohibited behavior is automatic
selection-*for-execution*; a read-only recommendation a human must still act on is
categorically different. `115.003-T` owns that reconciliation and it is a P0 defect
to delete or soften the non-goal.

Resolution order is **resumption-first and anomaly-first**: degraded → cycle →
`ambiguous_provenance` → `multi_active_anomaly` → `resume_active` (one active
shipment is the cursor — never recommend starting new work) → `ready_set_head` →
`no_candidates`. Tie-break: DESC downstream-dependent fan-out, then ASC id (total
order, since ids are unique).

## Review finding worth remembering

The first draft had 6 branches and buried ambiguous provenance in prose, so a
**single active shipment with corrupt provenance** had no branch and would have
fallen through to `resume_active` — recommending resumption of a corrupt record.
This is the exact shape in `docs/compound/2026-08-07-copilot-review-fix-introduces-new-filter-bug.md`.
Fixed by promoting it to its own anomaly-first branch with a distinct reason code.

## Cross-validation

`autoharness gate dag-readiness --json` (the Phase 1 tool this feature extends)
independently reports `ready_set: ["123-S"]` — exactly one eligible shipment,
confirming the handoff cursor.

## Next steps

1. Orchestrator publishes the uncommitted Stage artifacts (`.backlogit/`, `docs/plans/`, `docs/memory/`).
2. Ship claims **`123-S`** only after those artifacts land on `origin/main`.
3. Execute in dependency order: `115.001-T` → `115.002-T` → `115.003-T`.

## Carried / not addressed (out of scope, not regressions)

* Pre-existing orphaned artifacts `048.001-T`, `048.002-T`, `048.003-T` (doctor
  findings). Untouched — outside the bounded scope.
* Blocked features `077-F`, `080-F`, `081-F` — outside the six scoped IDs.
* `.autoharness/backlog-registry.yaml` does not declare `features.sizing` or
  size/complexity params on `update_task`, though the backlogit 1.8.0 MCP surface
  supports both. Sizing was written structurally **and** mirrored as prose. Worth a
  registry-accuracy follow-up.
