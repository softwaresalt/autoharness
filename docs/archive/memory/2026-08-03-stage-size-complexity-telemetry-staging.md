# Stage session memory — 2026-08-03 — size/complexity first-class + backlogit telemetry mapping

- **Route:** claude-opus-4.8 / anthropic / high (P-013.5), carried through all steps.
- **Mode:** DEGRADED (engram/intercom/graphtor-docs MCP tools absent → file-based fallback); backlogit healthy (CLI+MCP, 1.8.0 @ fd8d2c9d). Index synced (646 → re-synced at close).

## Outcome (reviewed, dependency-correct backlog)
- **Gate chain:** deliberate → impl-plan → plan-harden (P-006 APPLIED, schema blast radius) → plan-review **PASS**.
  - Deliberation: `docs/decisions/2026-08-03-size-complexity-telemetry-staging-deliberation.md`
  - Plan: `docs/archive/plans/2026-08-03-size-complexity-telemetry-staging-plan.md`
  - Review: `docs/reviews/2026-08-03-size-complexity-telemetry-staging-review.md`
- **Ordered shipment chain (only 112-S eligible; 113-S blocked on 112-S):**
  - **112-S** = S1 "size+complexity first-class in staging" — feature **107-F** — tasks 107.001-T, 107.002-T, 107.003-T, 107.004-T, 107.005-T (sizes M:2/S:3)
  - **113-S** = S2 "backlogit telemetry evidence mapping + complexity dimension" — feature **108-F** — tasks 108.001-T, 108.002-T, 108.003-T, 108.004-T (sizes M:3/S:1); `dependencies:[112-S]`

## Review-fix cycle — Copilot PR #291 (2026-08-03, re-review PASS retained)
Four blocking Copilot comments corrected; re-review now covers all **9 published tasks**:
- **3708167171 (108.002-T):** schema is NOT inert — live strict runtime model (`tool_event.py`, `additionalProperties:false`) + composer + jsonl + byte-identical root mirror (parity test) + `schema_contracts` registration all depend on it. 108.002-T re-scoped to BOTH schema mirrors + registration + contract tests (schema family); runtime model/composer/jsonl + runtime tests split into new **108.004-T** (python-runtime, dep 108.002-T) added to 108-F and 113-S.
- **3708167225 (review):** prior PASS reviewed 7 tasks but 112-S published 107.005-T; now documented as plan F1.T5 with dep/width/risk and covered by re-review.
- **3708167265 (107.004-T):** scope+acceptance now include the installed dogfood `.github/agents/_stage.agent.md` edit + `.autoharness/harness-manifest.yaml` checksum refresh (per 110-S/106.004-T).
- **3708167293 (108.001-T):** aggregate-only backlogit values (session cumulative tokens, tool_usage roll-ups, compaction_count) must NOT map onto per-operation event fields; added explicit event-vs-epoch granularity dimension; `compaction_count` is NOT a ToolTelemetryEvent field (route to ExecutionEpoch or mark unavailable at event granularity).
- **Size/complexity:** every task carries native `size` (size_source=agent, size_ruleset_version=`ah-stage-sizing-v1`). Complexity recorded as enum-validated planned metadata **via comments** because this workspace's `.backlogit/header-def.yaml` defines `size` but NOT `complexity` for the task type (1.8.0 binary supports it; workspace config predates it). Bootstrap task **107.005-T** stages the Ship-owned config enablement (P-010: Stage must not hand-edit config). Complexity map: 107.001=low, 107.002=medium, 107.003=low, 107.004=medium, 107.005=low, 108.001=high, 108.002=high, 108.003=medium, 108.004=high.
- **Non-conflation invariant** (adopted verbatim from backlogit help): size = implementation VOLUME/effort; complexity = implementation DIFFICULTY/UNCERTAINTY. Never combined into one scalar.

## Dispositions
- **082-F:** partial unblock/split. Backlogit portion carved to 108-F/113-S (actionable). Label added `backlogit-portion-carved-108F`; link 108-F --informs--> 082-F; comment recorded. Stays `blocked` for Engram/graphtor-docs/agent-intercom (access still absent).
- **Stash 34D50F2D (medium, ACTIVE):** candidates (a)/(c)/(d) remain DEFERRED (not harvested — 011-DL discipline). Tracker updated to note this session's 107-F/108-F work touches the (c) measurability facet only.
- **Stash 936C68F3 (low, ACTIVE):** EXTERNAL active→queued guard **RESOLVED-UPSTREAM** (backlogit 1.8 `isValidShipmentTransition` forbids active→queued + 061-F all-or-nothing claim rollback; evidence `internal/core/shipment.go`). Part (2) decision-gated self-repair still DEFERRED pending operator lifting report-and-halt stance. No harvest.

## Telemetry mapping (evidence for 108.001-T) — corrected per PR #291 finding 3708167293
- backlogit `session_summary`/`tool_usage` + `telemetry_sessions`/`telemetry_tool_usage` + shipment `size_composition` map to the ratified contract with an **explicit granularity dimension (per-invocation ToolTelemetryEvent vs per-epoch ExecutionEpoch)**. **Observed (event granularity, host_reported/backlogit-direct, per-invocation ONLY):** server_name, tool_name, operation, duration_ms, per-call in/out/cached tokens. **Aggregate-only (route to ExecutionEpoch economics OR mark unavailable at event granularity):** session cumulative tokens, tool_usage roll-ups, `compaction_count` (NOTE: `compaction_count` is NOT a ToolTelemetryEvent field — confirmed absent from both event and epoch schemas). **Derived:** tokens_per_task, depletion_rate, peak_utilization, remaining_capacity, offload estimates (labelled at their computable granularity). **Unavailable/not_applicable:** event_id/epoch_id/argv_fingerprint/exit_code/error_kind (autoharness-only identity). Gap: WorkSizingSnapshot carries size but no complexity → 108.002-T adds a structurally-separate complexity field (both schema mirrors + registration), 108.004-T threads it through the runtime model/composer/jsonl.

## Next steps (Ship)
1. Claim 112-S; execute 107.005-T first (enable complexity field), then 107.001-T → templates/skill/checklist.
2. After 112-S ships, 113-S unblocks: 108.001-T (evidence map w/ granularity) → 108.002-T (schema: both mirrors + registration + contract tests) → 108.004-T (runtime model/composer/jsonl + runtime tests) → 108.003-T (082-F backlogit carve-out landed).
3. Operator decisions still pending: 34D50F2D lead-capability selection + model-pick reconciliation; 936C68F3 part (2) stance lift.

## Stop conditions
None hit. Tasks attempted well under 20; no consecutive failures; no escalation triggered.
