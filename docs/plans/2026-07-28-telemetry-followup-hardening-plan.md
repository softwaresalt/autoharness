---
title: Telemetry subsystem follow-up hardening
date: 2026-07-28
source_stash: B51B8123, AD855510, 54B8CF8A, 406F60E1, 0655AE38
source_acceptance_criteria:
  - .backlogit/archive/079.015-T.md
  - .backlogit/archive/079.011-T.md
status: reviewed
plan_hardened: true
---

# Telemetry Follow-up Hardening Plan

## Stage Scope

This Stage pass promotes exactly five stash entries into one telemetry-domain
shipment:

| Stash ID | Priority | Kind | Classification | One-line scope |
|---|---:|---|---|---|
| B51B8123 | medium | task | test-hardening | Prove `telemetry begin` refreshes backlogit sizing through the CLI path before freezing context. |
| AD855510 | medium | task | performance | Avoid duplicate full JSONL scans while preserving direct-call and concurrent replay conflict checks. |
| 54B8CF8A | low | task | design decision | Decide advisory vs gate vs flag for populated metrics lacking provenance. |
| 406F60E1 | low | task | derived observation | Add cross-label size/cost monotonicity observation required by 079.011-T, not a hard assertion. |
| 0655AE38 | low | task | structured no-op contract | Default disabled `RecordSummary` no-op summaries to `idempotency_outcome: "disabled"`. |

No other stash entries are included. The grouping is contextually coherent:
all five entries touch `src/autoharness/telemetry/` and
`tests/test_telemetry_*.py`, with no template/source execution work performed by
Stage.

## Tool and Capability Posture

* `backlogit` MCP is not exposed for this session; the registry declares a CLI
  fallback, and `C:\Tools\backlogit.exe` v1.7.0 is available.
* Backlog index sync completed successfully before semantic stash reads.
* Engram MCP was unavailable (`ENGRAM_DEGRADED`); planning used exact-path and
  literal searches under the direct-tool exemptions.
* Graphtor-docs was reachable but had zero indexed sources; documentation
  lookups used direct file reads for exact archived acceptance-criteria paths.
* Project skills such as `impl-plan`, `plan-harden`, `plan-review`, and
  `harvest` are present as templates but not invokable through the current CLI
  skill surface. This plan applies their protocols inline and records the
  declared degradation in the review section.

## Acceptance-Criteria Verification

### B51B8123 against 079.015-T

`.backlogit/archive/079.015-T.md` explicitly requires the lifecycle workflow
test to prove begin-time freshness:

* seed a stale index and mutate membership on disk before `telemetry begin`;
* assert the begin-time `WorkSizingSnapshot` reflects a freshly synced backlogit
  index;
* mutate again after `telemetry begin`; and
* assert the persisted SQLite and JSONL epochs retain the frozen begin snapshot.

Current `tests/test_telemetry_ship_lifecycle.py` patches
`capture_work_sizing_snapshot` directly, so it verifies frozen-after behavior but
bypasses the CLI-to-sizing freshness path. B51B8123 is therefore required, but
the implementation should stay test-hardening-only: exercise `main()` through a
fake backlogit process/runner instead of changing Ship templates.

### 406F60E1 against 079.011-T

`.backlogit/archive/079.011-T.md` explicitly says aggregation groups by
`task_size_label`, `feature_planned_size_label`, and
`shipment_planned_size_label` as ordinal buckets and reports "within-label
dispersion and monotonicity observations without numeric label distances."

Current `_size_groups` reports per-label `count`, `cogs_usd_range`, and
`ordinal_only` only. 406F60E1 is therefore required, but it must be a derived
observation: real cost data may be non-monotonic, so the implementation must
surface the trend state without failing aggregation or claiming numeric label
distances.

## Relevant Learnings

`docs/compound/095-S-derived-metric-provenance-additive-map.md` is relevant:

* keep machine-readable metric values numeric or `"unavailable"`;
* carry qualitative provenance or observations in additive sibling maps; and
* adding fields to exported dataclasses should be optional, defaulted, and
  appended last.

This informs the provenance decision (54B8CF8A) and monotonicity observation
shape (406F60E1): prefer additive metadata over overloading existing values.

## Problem Frame

PR #227 follow-up work left five separable telemetry gaps after the higher
priority hardening shipment:

1. one lifecycle integration test still bypasses the acceptance-criteria path it
   is supposed to prove;
2. one JSONL mirror path has avoidable O(history) duplicate scans;
3. one provenance contract is visible only through advisory object methods;
4. one aggregation acceptance criterion has no cross-label observation; and
5. one disabled structured no-op path returns `null` where the contract expects
   `"disabled"`.

The work is code-changing and must be shipped by Ship using TDD. Stage only
creates the reviewed plan, backlog hierarchy, shipment manifest, and traceability.

## Requirements Trace

| Requirement | Implementation action |
|---|---|
| B51B8123 | Add a CLI-level lifecycle test that lets `main(["telemetry", "begin", ...])` invoke the real sizing adapter through a fake backlogit subprocess, proving sync-before-capture and freeze-after-begin across SQLite and JSONL. |
| AD855510 | Introduce a preflight scan result / bounded tail-rescan path so `record_epoch` can pass JSONL preflight state to `append_epoch` and avoid rescanning historical lines twice, while direct `append_epoch` calls and concurrent replay checks still scan appropriately. |
| 54B8CF8A | Make an explicit design choice: non-blocking persist-time flagging is recommended over hard rejection or advisory-only silence. Add TDD coverage for the chosen contract. |
| 406F60E1 | Add a cross-label monotonicity observation for ordinal size buckets, preserving `cost_per_size_point: "unavailable"` and no numeric distance assumptions. |
| 0655AE38 | Default `RecordSummary.idempotency_outcome` to `"disabled"` so disabled/no-op summaries share one structured contract even when `record_epoch` is bypassed. |

## Design Decision: Provenance Completeness at Persist Time

### Option A: keep advisory-only

`EconomicPayload.missing_provenance()`,
`OperationalReality.missing_provenance()`, and related properties remain the only
signals. This has the lowest compatibility risk but does not make the v1.1
"populated metrics MUST carry provenance" contract visible in CLI summaries or
record dispatch telemetry.

### Option B: hard persist-time gate

Reject epochs with populated metrics lacking both `metric_sources` and
`metric_quality`. This is contract-strict, but it conflicts with telemetry's
fail-open observational role, risks dropping useful historical/partial data, and
could make telemetry sink behavior block task-close workflows indirectly.

### Option C: non-blocking persist-time flag (recommended)

At record time, compute missing provenance for economics, operations, and outcome
payloads, and surface it in an additive summary field such as
`missing_provenance` / `provenance_complete`. Do not reject persistence and do
not overload `errors`, because missing provenance is a contract-quality signal,
not a sink failure. This makes the contract machine-visible while preserving
fail-open behavior and backward compatibility.

**Recommendation:** implement Option C. If a future policy wants hard gating, it
can be layered on top of the explicit summary signal without changing sink
immutability or CLI no-op behavior.

## Implementation Units

### Unit 1: Ship lifecycle begin freshness integration test (B51B8123)

* **Primary files:** `tests/test_telemetry_ship_lifecycle.py`
* **Related code read-only context:** `src/autoharness/cli.py`,
  `src/autoharness/telemetry/sizing.py`
* **Execution posture:** test-first; current test should fail because it does
  not exercise backlogit sync/freshness through `main()`.
* **Tests to write first:**
  1. Add a lifecycle test that configures telemetry with SQLite + JSONL, invokes
     `main(["telemetry", "begin", "--capture-backlogit-sizing", "--backlogit",
     "fake-backlogit", "--json", ...])`, and monkeypatches the fake process at
     the subprocess/default-runner boundary rather than patching
     `capture_work_sizing_snapshot`.
  2. Seed fake backlogit responses so a stale membership exists before begin;
     the fake `sync` call refreshes feature/shipment composition before the
     sizing `get` responses are returned.
  3. After begin, mutate the fake membership and then call
     `main(["telemetry", "record", "--context-ref", ...])`.
  4. Assert SQLite and JSONL payloads contain the refreshed-before membership
     hash and do not contain the post-begin mutation.
  5. Assert the fake process call log shows `sync` before feature/shipment `get`
     calls.
* **Acceptance criteria:**
  * 079.015-T freshness AC is directly covered by CLI-to-both-sinks integration.
  * Existing frozen-after-begin behavior remains covered.
  * The test remains deterministic and does not invoke a real backlogit binary.
* **Verification command for Ship:** `python -m pytest tests/test_telemetry_ship_lifecycle.py -v`

### Unit 2: JSONL sink duplicate-scan optimization (AD855510)

* **Primary files:** `src/autoharness/telemetry/jsonl_sink.py`,
  `src/autoharness/telemetry/record.py`,
  `tests/test_telemetry_jsonl_sink.py`
* **Execution posture:** TDD performance characterization first; preserve
  correctness before optimizing.
* **Tests to write first:**
  1. Add a record-path test that instruments JSONL scanning and proves
     `record_epoch` does not full-scan historical JSONL lines twice for the same
     epoch append.
  2. Keep/extend direct-call tests proving `append_epoch(epoch, path)` still
     detects identical replays and conflicting replays without a supplied
     preflight result.
  3. Add a bounded-concurrent replay test: if preflight found no epoch but bytes
     were appended after the preflight scan offset, `append_epoch` scans only
     the appended tail before writing and still detects an identical or
     conflicting concurrent replay.
* **Implementation shape:**
  * Return or pass a small JSONL preflight scan result containing at least the
    observed digest (if any) and the file offset/size reached by the scan.
  * Let `record._preflight_conflict` pass that result into `append_epoch`.
  * When the preflight result found an existing digest, avoid a second scan and
    return idempotent/conflict immediately.
  * When the preflight result found no digest, rescan only bytes appended since
    the recorded offset before appending, preserving concurrent-writer replay
    detection without walking the full historical file twice.
  * Direct `append_epoch` calls continue to perform their own full scan.
* **Acceptance criteria:**
  * No duplicate full historical scan on the `record_epoch` close path.
  * Direct-call conflict checks remain unchanged.
  * Concurrent replay checks remain intact.
  * No JSONL rotation/retention work is included; unbounded growth is recorded
    as an out-of-scope follow-up.
* **Verification command for Ship:** `python -m pytest tests/test_telemetry_jsonl_sink.py tests/test_telemetry_record_cli.py -v`

### Unit 3: Provenance completeness persist-time signal (54B8CF8A)

* **Primary files:** `src/autoharness/telemetry/record.py`,
  `tests/test_telemetry_record_cli.py`
* **Execution posture:** design-contract TDD first.
* **Chosen contract:** non-blocking persist-time flag, not hard rejection.
* **Tests to write first:**
  1. A `record_epoch` unit/CLI test builds an epoch with populated economics,
     operations, or outcome metrics lacking same-named `metric_sources` and
     `metric_quality` entries.
  2. Assert the epoch is still persisted successfully and
     `idempotency_outcome` remains `created`.
  3. Assert the structured summary includes an additive missing-provenance
     signal with section names and metric names.
  4. Assert a fully provenanced epoch reports no missing-provenance signal.
* **Implementation shape:**
  * Extend `RecordSummary` with an optional/defaulted additive field such as
    `missing_provenance: dict[str, list[str]]`.
  * Populate it from the epoch payload before sink writes.
  * Do not append these findings to `errors` and do not reject writes.
* **Acceptance criteria:**
  * The v1.1 provenance contract becomes machine-visible at persistence time.
  * Telemetry remains fail-open and backward-compatible.
  * The plan explicitly rejects hard gating for this shipment.
* **Verification command for Ship:** `python -m pytest tests/test_telemetry_record_cli.py -v`

### Unit 4: Size-label monotonicity observation (406F60E1)

* **Primary files:** `src/autoharness/telemetry/aggregation.py`,
  `tests/test_telemetry_aggregation.py`
* **Execution posture:** TDD derived-observation first.
* **Tests to write first:**
  1. Add an aggregation test with ordered labels such as `S`, `M`, `L` and
     measured `cogs_usd` ranges/centers that rise with ordinal label order;
     assert an additive observation reports a non-decreasing trend.
  2. Add a second test with non-monotonic costs; assert the observation reports
     non-monotonicity rather than failing or coercing values.
  3. Add an unavailable-data case where one or more labels have no measured
     cost; assert the observation is `"unavailable"` or equivalent and
     `cost_per_size_point` remains `"unavailable"`.
* **Implementation shape:**
  * Use only ordinal label order; do not infer numeric distances or points.
  * Prefer an additive sibling map (for example
    `size_observations[field]["cogs_usd_monotonicity"]`) over adding synthetic
    label entries to `size_groups`.
  * If adding a field to `AggregationResult`, append it with a default factory
    to preserve constructor compatibility.
* **Acceptance criteria:**
  * 079.011-T monotonicity-observation AC is satisfied.
  * Real non-monotonic data remains valid data.
  * Existing `planned_vs_composition` and `cost_per_size_point` values remain
    `"unavailable"` unless a named/versioned label-to-point mapping exists.
* **Verification command for Ship:** `python -m pytest tests/test_telemetry_aggregation.py -v`

### Unit 5: Disabled RecordSummary idempotency outcome default (0655AE38)

* **Primary files:** `src/autoharness/telemetry/record.py`,
  `tests/test_telemetry_record_cli.py`
* **Execution posture:** small contract TDD first.
* **Tests to write first:**
  1. Add a direct unit test for `RecordSummary(enabled=False).to_dict()` that
     expects `idempotency_outcome == "disabled"`.
  2. Keep/extend disabled CLI no-op coverage to assert `--json` emits the same
     disabled outcome when telemetry mode is `none` or absent.
* **Implementation shape:**
  * Change the dataclass default for `idempotency_outcome` from `None` to
    `"disabled"`.
  * Ensure enabled record paths still overwrite it with `created`,
    `idempotent_replay`, `partial_repaired`, or `conflict_rejected`.
* **Acceptance criteria:**
  * Every structured disabled/no-op summary returns `"disabled"` consistently,
    including direct `RecordSummary` construction and CLI fast/no-op paths.
  * No sink behavior changes.
* **Verification command for Ship:** `python -m pytest tests/test_telemetry_record_cli.py -v`

## Dependency Graph

1. Unit 5 should run before Unit 3 because both touch `RecordSummary`; the
   provenance flag tests can then assert the final default contract.
2. Unit 2 may run independently after Unit 5/3 sequencing is understood, but it
   also touches `record.py`; Ship should avoid interleaving edits to the same
   file across tasks.
3. Unit 1 and Unit 4 are independent of the `record.py` tasks.

Suggested task order:

1. disabled `RecordSummary` default;
2. provenance completeness flag;
3. JSONL preflight scan optimization;
4. ship lifecycle freshness integration test;
5. size-label monotonicity observation.

## Risks and Caveats

* `record.py` is touched by three tasks. Each task is still below the 2-hour
  rule, but Ship should sequence them rather than parallelize file edits.
* JSONL optimization must not trade correctness for performance. The required
  tail-rescan/concurrent-replay test is the guardrail.
* Provenance hard gating is deliberately out of scope. The selected flag
  contract gives downstream policies a future hook without breaking fail-open
  telemetry.
* JSONL rotation/retention is explicitly out of scope for this shipment even
  though the mirror grows unbounded beside the workspace database.
* Monotonicity is observational only; real telemetry can be non-monotonic.

## Plan Hardening Signals

| Signal | Present? | Justification |
|---|---|---|
| Public API, schema, or contract change | yes | `RecordSummary.to_dict()` and aggregation result shape are structured contracts. |
| Security, auth, permission, or compliance-sensitive behavior | no | No auth or secret-handling surfaces are touched. |
| Migration, backfill, destructive data/config action, or irreversible step | no | No migrations or destructive operations are planned. |
| External integration, operator checkpoint, or external dependency | yes | Unit 1 exercises the backlogit CLI/process integration path through a fake runner. |
| High runtime, rollout, or rollback risk | moderate | Telemetry is fail-open but used across Ship lifecycle, sinks, aggregation, and reports. |

Requires plan hardening: yes

## Plan Hardening

Hardening was required because this shipment changes structured telemetry
contracts and sink conflict-check performance behavior. The reinforced
invariants are:

* telemetry remains observational and fail-open;
* first-write immutability and idempotent replay semantics remain unchanged;
* disabled/no-op structured summaries are stable and explicit;
* size labels remain ordinal only with no implicit point mapping;
* fake backlogit tests must not invoke or mutate real backlogit state; and
* no production source/test/config files are modified by Stage.

Risk-specific guardrails:

* **JSONL optimization:** any preflight reuse must include a bounded tail rescan
  when the file grew after preflight. Skipping this check would be a correctness
  regression.
* **Provenance flag:** missing provenance is a quality signal, not a sink error.
  Do not append it to `errors` or reject the epoch in this shipment.
* **Aggregation observation:** use an additive observation map and preserve
  `"unavailable"` derived metrics where no point mapping exists.
* **Lifecycle freshness:** test through `main()` and a fake subprocess/default
  runner boundary so the acceptance criterion proves the actual CLI path.

Rollback is straightforward: each task is additive or localized. If a task
causes regressions, revert that task's source/test changes; no persisted telemetry
migration is required.

## Runtime Verification and Closure

* Unit 1 changes only tests but verifies a CLI runtime surface; Ship should run
  the targeted lifecycle test and inspect both SQLite and JSONL assertions.
* Units 2, 3, and 5 affect record/sink runtime behavior; Ship should run the
  targeted record + JSONL suites and confirm disabled, created, idempotent,
  partial repair, and conflict outcomes remain covered.
* Unit 4 affects aggregation/report input behavior; Ship should run aggregation
  tests and verify no ratio or cost-per-point contract changes.
* Operational closure should summarize the out-of-scope JSONL retention follow-up
  and the design decision selecting non-blocking provenance flagging.

## Plan Review

dispatch_mode: single-agent-declared-degradation
decision: PASS

Reviewer dispatch was unavailable as an invokable skill in this CLI session, so
Stage applied every selected persona rubric inline.

| Persona | Coverage | Findings |
|---|---|---|
| Constitution Reviewer | inline | PASS — plan preserves fail-open telemetry, TDD sequencing, workspace containment, and Stage role boundaries. |
| Python Reviewer | inline | PASS — tasks identify focused Python modules and targeted tests; dataclass additions are defaulted/additive. |
| Scope Boundary Auditor | inline | PASS — shipment includes exactly the five scoped stash entries; JSONL retention is explicitly out of scope. |
| Learnings Researcher | inline | PASS — additive provenance-map learning is applied to provenance and monotonicity design. |
| Architecture Strategist | inline | PASS — dependency order avoids conflicting `record.py` edits and preserves sink/aggregation boundaries. |
| Agent-Native Parity Reviewer | inline | PASS — backlogit/CLI integration is tested through fake process boundaries without changing MCP/agent surfaces. |
| Security Lens Reviewer | inline | PASS — no auth, secrets, or external trust boundary changes beyond fake local process tests. |

No P0/P1/P2 findings. Advisory notes are already captured as out-of-scope
follow-ups: JSONL rotation/retention and any future strict provenance gate.

## Harvest Model

Create one covering feature and five child tasks, one per implementation unit.
Every task must reference this plan and include test-first acceptance criteria.
The queued shipment manifest must include the feature first and
`custom_fields.items` listing the five task IDs for Ship's safe-close contract.

## Harvest Results

* Covering feature: `092-F` — Telemetry subsystem follow-up hardening
* Queued shipment: `097-S`
* Shipment manifest `custom_fields.items`:
  1. `092-F`
  2. `092.001-T` — Default disabled telemetry RecordSummary idempotency outcome
  3. `092.002-T` — Flag missing telemetry metric provenance at record time
  4. `092.003-T` — Reuse JSONL preflight scans without weakening replay checks
  5. `092.004-T` — Cover telemetry begin backlogit freshness through Ship lifecycle CLI
  6. `092.005-T` — Report ordinal size-label cost monotonicity observations
* Dependency edges:
  * `092.002-T` depends on `092.001-T`
  * `092.003-T` depends on `092.002-T`
* Consumed stash traceability:
  * `0655AE38` → `092.001-T`
  * `54B8CF8A` → `092.002-T`
  * `AD855510` → `092.003-T`
  * `B51B8123` → `092.004-T`
  * `406F60E1` → `092.005-T`
