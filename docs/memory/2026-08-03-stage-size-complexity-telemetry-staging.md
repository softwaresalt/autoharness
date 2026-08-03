# Stage session memory — 2026-08-03 — size/complexity first-class + backlogit telemetry mapping

- **Route:** claude-opus-4.8 / anthropic / high (P-013.5), carried through all steps.
- **Mode:** DEGRADED (engram/intercom/graphtor-docs MCP tools absent → file-based fallback); backlogit healthy (CLI+MCP, 1.8.0 @ fd8d2c9d). Index synced (646 → re-synced at close).

## Outcome (reviewed, dependency-correct backlog)
- **Gate chain:** deliberate → impl-plan → plan-harden (P-006 APPLIED, schema blast radius) → plan-review **PASS**.
  - Deliberation: `docs/decisions/2026-08-03-size-complexity-telemetry-staging-deliberation.md`
  - Plan: `docs/plans/2026-08-03-size-complexity-telemetry-staging-plan.md`
  - Review: `docs/reviews/2026-08-03-size-complexity-telemetry-staging-review.md`
- **Ordered shipment chain (only 112-S eligible; 113-S blocked on 112-S):**
  - **112-S** = S1 "size+complexity first-class in staging" — feature **107-F** — tasks 107.001-T, 107.002-T, 107.003-T, 107.004-T, 107.005-T (sizes M:2/S:3)
  - **113-S** = S2 "backlogit telemetry evidence mapping + complexity dimension" — feature **108-F** — tasks 108.001-T, 108.002-T, 108.003-T (sizes M:2/S:1); `dependencies:[112-S]`
- **Size/complexity:** every task carries native `size` (size_source=agent, size_ruleset_version=`ah-stage-sizing-v1`). Complexity recorded as enum-validated planned metadata **via comments** because this workspace's `.backlogit/header-def.yaml` defines `size` but NOT `complexity` for the task type (1.8.0 binary supports it; workspace config predates it). Bootstrap task **107.005-T** stages the Ship-owned config enablement (P-010: Stage must not hand-edit config). Complexity map: 107.001=low, 107.002=medium, 107.003=low, 107.004=medium, 107.005=low, 108.001=high, 108.002=high, 108.003=medium.
- **Non-conflation invariant** (adopted verbatim from backlogit help): size = implementation VOLUME/effort; complexity = implementation DIFFICULTY/UNCERTAINTY. Never combined into one scalar.

## Dispositions
- **082-F:** partial unblock/split. Backlogit portion carved to 108-F/113-S (actionable). Label added `backlogit-portion-carved-108F`; link 108-F --informs--> 082-F; comment recorded. Stays `blocked` for Engram/graphtor-docs/agent-intercom (access still absent).
- **Stash 34D50F2D (medium, ACTIVE):** candidates (a)/(c)/(d) remain DEFERRED (not harvested — 011-DL discipline). Tracker updated to note this session's 107-F/108-F work touches the (c) measurability facet only.
- **Stash 936C68F3 (low, ACTIVE):** EXTERNAL active→queued guard **RESOLVED-UPSTREAM** (backlogit 1.8 `isValidShipmentTransition` forbids active→queued + 061-F all-or-nothing claim rollback; evidence `internal/core/shipment.go`). Part (2) decision-gated self-repair still DEFERRED pending operator lifting report-and-halt stance. No harvest.

## Telemetry mapping (evidence for 108.001-T)
- backlogit `session_summary`/`tool_usage` + `telemetry_sessions`/`telemetry_tool_usage` + shipment `size_composition` map to ToolTelemetryEvent. Observed: server_name, tool_name, duration_ms, in/out/cached tokens, compaction_count, context tokens. Derived: tokens_per_task, depletion_rate, peak_utilization, remaining_capacity, offload estimates. Unavailable/not_applicable: event_id/epoch_id/argv_fingerprint/exit_code/error_kind (autoharness-only identity). Gap: WorkSizingSnapshot carries size but no complexity → 108.002-T adds a structurally-separate complexity field.

## Next steps (Ship)
1. Claim 112-S; execute 107.005-T first (enable complexity field), then 107.001-T → templates/skill/checklist.
2. After 112-S ships, 113-S unblocks: 108.001-T → 108.002-T (schema) → 108.003-T (082-F backlogit carve-out landed).
3. Operator decisions still pending: 34D50F2D lead-capability selection + model-pick reconciliation; 936C68F3 part (2) stance lift.

## Stop conditions
None hit. Tasks attempted well under 20; no consecutive failures; no escalation triggered.
