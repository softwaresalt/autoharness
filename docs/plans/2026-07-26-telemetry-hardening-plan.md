---
title: PR #227 telemetry hardening + ship-lifecycle sizing genericization
date: 2026-07-26
source_stash: 638AA991, A465162F, A7DBF981, 346DF592, 2D22ED3D, 64C01A60, 59E6CD50, 4C4A8F0B, 435F201D, D194A24B, 3EFC51DE
origin_feature: 090-F (PR #227 telemetry hardening)
shipment: 095-S
---

# PR #227 Telemetry Hardening Plan

## Problem Frame

PR #227 Copilot review left 16 deferred follow-up findings across the
telemetry subsystem (`src/autoharness/telemetry/*`, `src/autoharness/eval/summary.py`,
`src/autoharness/cli.py`, the embedded `WorkSizingSnapshot` JSON Schema, and the
092-S sizing-readiness documentation in `.ship.agent.md`). All 16 stash entries
were re-verified line-by-line against current HEAD (`b32254e6`); none were
already resolved by merged work (e.g. `feat/079-telemetry-metrics-core`, 092-S)
and none required a spike — every entry is a confirmed, still-open defect or
gap.

### Sizing rationale (11 in-shipment, 5 left-stashed)

Not every open entry belongs in one release unit. Five entries are
**deliberately left in the stash** because they are separable from the
telemetry-hardening theme by priority or by coupling:

* **54B8CF8A (low)** — self-declared open design question, not a confirmed bug.
* **406F60E1 (low)** — self-declared "scope-expansion beyond 092-S shipment."
* **0655AE38 (low)** — confirmed real (`cli.py:919` bypasses the
  `idempotency_outcome="disabled"` path) but low priority and unrelated to the
  other fixes' call paths.
* **AD855510 (medium, separable)** — `record.py`/`jsonl_sink.py` duplicate
  `find_epoch_digest` scans; explicitly framed by the stash itself as "a
  performance optimization, not a correctness defect." No shared file or
  function with any in-shipment task.
* **B51B8123 (medium, separable)** — `test_telemetry_ship_lifecycle.py:90-94`
  mocks `capture_work_sizing_snapshot` entirely and never exercises the real
  backlogit sync/freshness path; this is test-hardening only, orthogonal to
  the 8 correctness/schema/documentation fixes below, and touches the same
  test file as Task 1 — bundling it would blur Task 1's already-elevated
  blast radius (ratified-test-contract change) with an unrelated test-quality
  concern.

The remaining 11 entries are genuinely open, medium-or-higher priority,
directly coupled to the telemetry-hardening theme, and file-disjoint from each
other. They are grouped into **8 TDD-scoped tasks** (two coupled pairs
merged, six standalone) under one covering feature and one queued shipment —
a focused, reviewable release unit rather than a mega-batch.

## Requirements Trace

| Requirement (stash ID) | Implementation action |
|---|---|
| 638AA991 (anchor) — genericize hard-coded `079.013-T`/`079.015-T` execution-ready gate literals in `.ship.agent.md` | Task 1 |
| A465162F — explicit close-timestamp guidance for the context-ref telemetry record step | Task 1 |
| A7DBF981 — non-context telemetry record path must validate/require timestamp for idempotent retries | Task 2 |
| 346DF592 — enforce `backlog_item_id`/`task_id` consistency at context-begin time, not only at close | Task 3 |
| 2D22ED3D — `WorkSizingSnapshot` unsized-count must surface data-quality unavailability, not silently clamp to 0 | Task 4 |
| 64C01A60 — embedded `WorkSizingSnapshot` schema must declare `feature_skipped_ids`/`shipment_skipped_ids` | Task 5 |
| 59E6CD50 — quality reports must distinguish "no label ever recorded" from "observed" | Task 6 |
| 4C4A8F0B — `snapshot_boundary` must be validated against its enum (reject null/unknown) | Task 7 |
| 435F201D — `AbsoluteOutcome` exit-code coercion must strictly type-check elements | Task 7 |
| D194A24B — eval-summary must surface estimated-vs-observed provenance for derived ratios | Task 8 |
| 3EFC51DE — `gap_rate`/`_derived_ratio` must be quality-aware, not just null/zero-guarded | Task 8 |
| Left-stashed (54B8CF8A, 406F60E1, 0655AE38, AD855510, B51B8123) | Not implemented by this shipment; left in stash per sizing rationale above |
| All tasks: TDD red-then-green, tests co-located with existing suites | Each Implementation Unit below specifies failing tests first |

## Implementation Units

### Task 1 — 090.001-T: Genericize 092-S sizing-readiness gate + explicit close timestamp (638AA991, A465162F)

* **Files** (5): `templates/agents/.ship.agent.md.tmpl`, `.github/agents/.ship.agent.md`, `tests/test_telemetry_ship_lifecycle.py`, `tests/test_telemetry_record_cli.py`, `.autoharness/harness-manifest.yaml`
* **Execution posture**: test-first (red → green). **Elevated blast radius — see Plan Hardening Signals; this task requires plan-harden.**
* **Current state**: both agent docs hard-code `079.013-T`/`079.015-T` as the
  literal execution-ready gate condition; the ratified test
  `test_092s_execution_ready_guardrails_are_documented_in_ship_agents`
  (`tests/test_telemetry_ship_lifecycle.py:156-165`) asserts those literals
  are present verbatim. Neither doc instructs Ship to pass an explicit close
  timestamp in the telemetry record payload (`.ship.agent.md:242`);
  `cli.py:887-888` falls back to the context's `captured_at` (begin time)
  when timestamp is omitted.
* **Tests to add/change first (must fail before the fix — test-contract-update-first sequencing)**:
  1. Update `test_092s_execution_ready_guardrails_are_documented_in_ship_agents`
     to remove the two hard-literal (`079.013-T`/`079.015-T`) assertions and
     replace them with an assertion on a generic dependency-derivation phrase
     (e.g. asserting both docs state that execution-readiness is derived from
     the shipment's own declared task dependencies, never embedded ID
     literals). Keep the existing `task-only manifests` / `parent_id` /
     `execution-ready` assertions unchanged.
  2. Add an assertion to the same test (or a sibling test in the same file)
     proving both docs instruct capture-once/reuse of an explicit close
     timestamp (the same value reused on every retry, never regenerated per
     attempt) at the telemetry record step — not merely "an explicit
     timestamp".
  3. Add `test_record_replays_idempotently_with_same_explicit_close_timestamp`
     to `tests/test_telemetry_record_cli.py`: two context-ref records sharing
     one explicit close timestamp yield `created` then `idempotent_replay`,
     locking the capture-once/reuse contract behaviorally.
  4. Run the updated/added tests against current (unmodified) doc content and
     confirm they fail (red) — the docs still contain the old literals and
     lack capture-once/reuse guidance.
* **Fix**: edit both `templates/agents/.ship.agent.md.tmpl` and
  `.github/agents/.ship.agent.md` identically in substance: (a) replace the
  literal `079.013-T`/`079.015-T` sentence with a generic rule deriving
  execution-readiness from the shipment's own declared task dependencies; (b)
  add close-timestamp guidance at the `telemetry record --context-ref` step
  (`.ship.agent.md:242`) that requires Ship to capture the close timestamp ONCE
  and reuse that exact value on every retry (never regenerate `now` per
  attempt), so a retried record keeps a stable `payload_digest` and replays as
  `idempotent_replay` rather than `conflict_rejected`; (c) after editing the
  `.github/agents/.ship.agent.md` mirror, refresh its sha256 entry in
  `.autoharness/harness-manifest.yaml` so
  `test_manifest_tracks_dogfood_ship_agent_checksum`
  (`tests/test_telemetry_ship_lifecycle.py:45-52`) stays green. Confirm the
  updated/added tests are green.
* **Guardrail**: do not weaken `_merge_telemetry_context_payload`'s protected
  `captured_at` fallback (covered by
  `test_record_context_idempotency_and_conflict_outcomes`,
  `tests/test_telemetry_record_cli.py:199`) — satisfy this via explicit
  documentation guidance, not by modifying that function.
* **Verification**: `python -m pytest tests/test_telemetry_ship_lifecycle.py tests/test_telemetry_record_cli.py -v`

### Task 2 — 090.002-T: Stable timestamp for non-context telemetry record retries (A7DBF981)

* **Files** (2): `src/autoharness/cli.py`, `tests/test_telemetry_record_cli.py`
* **Execution posture**: test-first (red → green)
* **Current state**: the non-context telemetry record path (`cli.py:945-952`)
  validates only `epoch_id` via `_validate_record_epoch_id` (`cli.py:820-840`).
  When `timestamp` is omitted, `ExecutionEpoch.from_mapping` (`epoch.py:822-823`)
  leaves the dataclass default `field(default_factory=_utc_now_iso)`
  (`epoch.py:700`) to stamp a fresh wall-clock value on every call, so an
  intended idempotent retry produces a different `payload_digest` and is
  rejected as `conflict_rejected` instead of recognized as `idempotent_replay`.
* **Tests to add first (must fail before the fix)**:
  1. `test_record_rejects_missing_timestamp_without_context` — a payload
     omitting `timestamp` on the non-context path must raise `EpochError` /
     exit 2, mirroring `test_record_rejects_missing_epoch_id_without_context`
     (line 108).
  2. `test_record_replays_idempotently_with_explicit_timestamp_without_context`
     — the same payload with an explicit `timestamp`, recorded twice, yields
     `created` then `idempotent_replay`.
* **Fix**: add a `_validate_record_timestamp(value)` helper beside
  `_validate_record_epoch_id` in `cli.py`, called at `cli.py:951` alongside
  the existing non-context `epoch_id` validation, raising `EpochError` with an
  actionable message when `timestamp` is `None`/blank.
* **Guardrail**: `_merge_telemetry_context_payload` and the context-ref path
  are untouched.
* **Verification**: `python -m pytest tests/test_telemetry_record_cli.py -v`

### Task 3 — 090.003-T: Fail-fast backlog/task ID consistency check at context-begin (346DF592)

* **Files** (2): `src/autoharness/telemetry/context.py`, `tests/test_telemetry_begin_context.py`
* **Execution posture**: test-first (red → green)
* **Current state**: `_build_context_payload` (`context.py:127-165`) builds the
  begin-context payload without ever comparing `backlog_item_id`/`task_id` for
  consistency; only `ExecutionEpoch.__post_init__` (`epoch.py:732-737`)
  enforces equality, and only at close time — a mismatched begin call
  succeeds silently and the operator only discovers the conflict when closing
  the epoch, often after doing the wrong work.
* **Tests to add first (must fail before the fix)**:
  1. `test_begin_context_rejects_backlog_task_id_mismatch` — a begin-context
     call with inconsistent `backlog_item_id`/`task_id` must raise
     `TelemetryContextError` immediately (the type `_telemetry_begin_command`
     catches at `cli.py:776-810`).
* **Fix**: add an early consistency check in `_build_context_payload` (or the
  begin-context CLI entry point that calls it), raising `TelemetryContextError`
  (so the existing `_telemetry_begin_command` handler at `cli.py:776-810`
  catches it and emits the exit-2 diagnostic instead of an uncaught traceback)
  with the same actionable message style used at `epoch.py:732-737`, before the
  payload is constructed.
* **Guardrail**: the `epoch.py` close-time check remains as defense-in-depth
  (not removed); existing consistent begin-context calls remain unaffected.
* **Verification**: `python -m pytest tests/test_telemetry_begin_context.py -v`

### Task 4 — 090.004-T: Surface WorkSizingSnapshot unsized-count data-quality gap (2D22ED3D)

* **Files** (2): `src/autoharness/telemetry/sizing.py`, `tests/test_telemetry_backlogit_sizing.py`
* **Execution posture**: test-first (red → green)
* **Current state**: `_composition` (`sizing.py:104-159`) computes
  `unsized = max(len(unique_ids) - sized_count, 0)` at line 147, silently
  clamping to 0 whenever the histogram overcounts relative to `unique_ids`.
  This masks a data-quality problem that the same function already has a
  precedent for surfacing: malformed values elsewhere return the
  "unavailable" tuple (lines 139-145) instead of a coerced number.
* **Tests to add first (must fail before the fix)**:
  1. `test_composition_flags_inconsistent_sized_count_as_unavailable` —
     construct a histogram where `sized_count` exceeds `len(unique_ids)`,
     assert `_composition` degrades the ENTIRE composition to the existing
     unavailable tuple (`None`, `{}`, `None`, preserved `ruleset_version`,
     preserved `skipped`), matching `sizing.py:139-145`. There is no
     per-field/per-bucket "unavailable" marker, and `WorkSizingSnapshot`
     forbids an "unavailable" histogram bucket (`epoch.py:526-531,568-573`).
* **Fix**: change line 147 to detect `sized_count > len(unique_ids)` and
  return that same 5-tuple, exactly like the existing malformed-value
  pattern (`sizing.py:139-145`), instead of clamping via `max(...,0)`.
* **Guardrail**: normal (non-overfull) histograms are unaffected.
* **Verification**: `python -m pytest tests/test_telemetry_backlogit_sizing.py -v`

### Task 5 — 090.005-T: Add skipped-ID fields to embedded WorkSizingSnapshot schema (64C01A60)

* **Files** (3): `schemas/tool-telemetry-event.schema.json`, `schemas/tool-telemetry-event/1.0.0.schema.json`, `tests/test_telemetry_schema_contracts.py`
* **Execution posture**: test-first (red → green)
* **Current state**: the embedded `WorkSizingSnapshot` schema block
  (`schemas/tool-telemetry-event.schema.json:727-900` and the versioned mirror
  `schemas/tool-telemetry-event/1.0.0.schema.json`) declares
  `additionalProperties:false` but has no `feature_skipped_ids` or
  `shipment_skipped_ids` properties, even though `epoch.py:545,549,643,647`
  (`WorkSizingSnapshot` dataclass + `from_mapping`) already produce and
  round-trip both fields. Any event payload containing them currently fails
  schema validation.
* **Tests to add first (must fail before the fix)**:
  1. `test_work_sizing_snapshot_schema_allows_skipped_id_fields` — validate a
     sample `WorkSizingSnapshot` payload including `feature_skipped_ids` and
     `shipment_skipped_ids` against both schema files; assert validation
     currently fails.
* **Fix**: add both properties (array of string) to the `WorkSizingSnapshot`
  property block in both schema files, keeping them in sync.
* **Explicitly out of scope**: `schemas/execution-epoch.schema.json` (+
  versioned mirror) already declares `feature_skipped_ids` /
  `shipment_skipped_ids` (`execution-epoch.schema.json:1546,1615`;
  `execution-epoch/1.1.0.schema.json`), so no analogous gap remains there; it
  is NOT touched by this task, per stash 64C01A60's narrow framing.
* **Verification**: `python -m pytest tests/test_telemetry_schema_contracts.py -v`

### Task 6 — 090.006-T: Distinguish unknown vs observed quality in telemetry reports (59E6CD50)

* **Files** (2): `src/autoharness/telemetry/report.py`, `tests/test_telemetry_reports.py`
* **Execution posture**: test-first (red → green)
* **Current state**: `_quality` (`report.py:98-115`) defaults `worst` to
  `"observed"` whenever `worst is None`, unless the metric field name is in
  `_unavailable_metrics` (`report.py:51-60`), which only flags fields whose
  VALUE is `None`/`"unavailable"` — it does not distinguish "no quality label
  was ever attached" from "quality label was attached and is genuinely
  observed."
* **Tests to add first (must fail before the fix)**:
  1. `test_quality_reports_unavailable_when_no_label_recorded` — a metric
     history with zero quality-label entries must report `"unavailable"`, not
     `"observed"`.
  2. `test_quality_reports_unavailable_for_mixed_missing_label_history` — a
     mixed history with one genuinely `"observed"` record and one populated
     record lacking a same-named quality label must degrade the aggregate to
     `"unavailable"` (the real 59E6CD50 failure mode, since `_quality` skips
     missing labels per record).
* **Fix**: treat each populated record with a missing same-named quality label
  as `"unavailable"` in `_quality` (so any missing provenance degrades the
  aggregate), while preserving current behavior for fields already in
  `_unavailable_metrics`. Do NOT add a new `"unknown"` value — the documented
  vocabulary is observed/derived/estimated/unavailable/not-applicable
  (`docs/telemetry-reference.md:27,47`); reuse `"unavailable"`.
* **Guardrail**: metrics whose populated records all carry a real `"observed"`
  quality label (none missing) continue to report `"observed"`.
* **Verification**: `python -m pytest tests/test_telemetry_reports.py -v`

### Task 7 — 090.007-T: Strict validation for snapshot_boundary and exit-code coercion (4C4A8F0B, 435F201D)

* **Files** (2): `src/autoharness/telemetry/epoch.py`, `tests/test_telemetry_epoch.py`
* **Execution posture**: test-first (red → green)
* **Current state (two related defects in the same file)**:
  1. `WorkSizingSnapshot.__post_init__` (`epoch.py:551-596`) never validates
     `snapshot_boundary` against its allowed enum; `from_mapping`
     (`epoch.py:654`) does `str(data.get("snapshot_boundary", "pre_execution"))`,
     so an explicit `null` becomes the literal string `"None"` instead of
     being rejected.
  2. `AbsoluteOutcome.from_mapping` (`epoch.py:504`) does raw
     `tuple(int(c) for c in codes)` after `_as_tuple` (line 498), with no
     per-element type check, unlike the strict-type coercion pattern already
     used by `_coerce_nonneg_metric` (`epoch.py:99-153`, esp. 129-142)
     elsewhere in the same module.
* **Tests to add first (must fail before the fix)**:
  1. `test_work_sizing_snapshot_rejects_null_snapshot_boundary` — explicit
     `null` must raise `EpochError`, not become the literal string `"None"`.
  2. `test_work_sizing_snapshot_rejects_invalid_snapshot_boundary_enum` — an
     unrecognized string must raise `EpochError`.
  3. `test_absolute_outcome_from_mapping_rejects_non_numeric_exit_code` — a
     bool or string element in `codes` must raise `EpochError` with an
     actionable message, mirroring the `_coerce_nonneg_metric` pattern.
* **Fix**: add `snapshot_boundary` enum validation in
  `WorkSizingSnapshot.__post_init__`/`from_mapping`, raising `EpochError` on
  null or unrecognized values; add per-element strict-type validation in
  `AbsoluteOutcome.from_mapping`'s exit-code tuple construction, following the
  `_coerce_nonneg_metric` pattern.
* **Guardrail**: valid `snapshot_boundary` values and valid integer exit-code
  tuples continue to round-trip unchanged.
* **Verification**: `python -m pytest tests/test_telemetry_epoch.py -v`

### Task 8 — 090.008-T: Surface estimated-vs-observed provenance in eval-summary derived ratios (D194A24B, 3EFC51DE)

* **Files** (4): `src/autoharness/telemetry/aggregation.py`, `src/autoharness/eval/summary.py`, `tests/test_eval_summary.py`, `tests/test_telemetry_aggregation.py`
* **Execution posture**: test-first (red → green)
* **Current state (two coupled defects)**: `eval/summary.py` has no general
  mechanism surfacing whether an economics metric was estimated vs observed
  in its output — only one special case exists for `context_area_tokens`
  (`summary.py:161`). `gap_rate` (`summary.py:143`:
  `float | str = UNAVAILABLE if expected == 0 else missing / expected`)
  ignores `metric_quality` entirely, and `_derived_ratio`
  (`aggregation.py:118-121`) is likewise not quality-aware — it only guards
  against `None` values / zero denominators, not against a denominator whose
  provenance is "estimated".
* **Tests to add first (must fail before the fix)**:
  1. `test_gap_rate_flags_estimated_denominator_provenance` — a metric history
     where the denominator's quality is "estimated" must surface a provenance
     marker in the summary output distinguishing it from a genuinely observed
     ratio.
  2. `test_gap_rate_unavailable_when_numerator_unavailable` — 3EFC51DE's
     concrete case: a usable denominator (`expected_tool_count=1`) with an
     `"unavailable"` numerator (`missing_expected_tool_count=0` marked
     unavailable) must surface `"unavailable"` provenance, not a bare `0.0`.
  3. In `tests/test_telemetry_aggregation.py` (which owns the
     `derived_efficiency_metrics` contract at lines 182-224), operand-quality
     regression cases for the OTHER `_derived_ratio` consumers —
     `consumption_generation_ratio` and `cost_per_successful_epoch`
     (`aggregation.py:140,142`) — asserting an unavailable/estimated numerator
     or denominator degrades those ratios' provenance too and does not silently
     change their shape, covering the broadened `_derived_ratio` where it is
     actually consumed, not only via `gap_rate` in `test_eval_summary.py`.
     (`net_offload_tokens` at `aggregation.py:136-139` is a direct subtraction,
     not a `_derived_ratio` consumer, and already returns `UNAVAILABLE` when
     either operand is `None`; out of scope for this broadening.)
* **Fix**: extend `_derived_ratio` in `aggregation.py` to accept/propagate a
  quality indicator for BOTH its numerator and denominator operands (a
  denominator-only design still returns `0.0` for the unavailable-numerator
  case and does not fix 3EFC51DE); update `summary.py`'s `gap_rate` computation
  (and other `_derived_ratio` consumers sharing the same gap) to surface that
  provenance in the returned summary structure, generalizing the existing
  `context_area_tokens` special case rather than duplicating it.
* **Guardrail**: ratios with fully-observed numerator and denominator are
  unaffected (no provenance noise added for the common case).
* **Verification**: `python -m pytest tests/test_eval_summary.py tests/test_telemetry_aggregation.py -v`

## Dependency Graph

Tasks 3-8 touch mutually disjoint file sets and share no runtime state. Tasks 1
and 2 both add cases to `tests/test_telemetry_record_cli.py` (Task 1 for the
context-ref explicit-timestamp idempotency regression, Task 2 for the
non-context path), so that single shared test file is their only overlap —
implement Tasks 1 and 2 sequentially (or merge their test additions carefully)
to avoid a conflict there. The remaining tasks may be implemented in any order
or in parallel within the same build session. No task depends on another task's
runtime output. No cycles. No `backlogit dep` entries were created between
tasks.

## Decisions and Rationale

* **Task-only shipment manifest** — `095-S`'s `custom_fields.items` lists only
  the 8 task IDs (`090.001-T` … `090.008-T`); the covering feature `090-F` is
  the derived/protected parent and is never listed as a shipment item, per the
  authoritative convention in `.ship.agent.md` (safe-close procedure) and the
  092-S/093-S/094-S task-only precedent. Verified directly against
  `backlogit shipment get 095-S` output (see Plan Review).
* **Two coupled pairs merged (Task 1, Task 7, Task 8)** — 638AA991 and
  A465162F both touch the same two agent docs and the same ratified test;
  4C4A8F0B and 435F201D both touch the same function neighborhood in
  `epoch.py`; D194A24B and 3EFC51DE both touch the same
  `aggregation.py`/`summary.py` provenance gap. Splitting these pairs into
  separate tasks would create artificial file-overlap and sequencing risk
  between tasks. Tasks 7 and 8 stay within the 2-Hour Rule's `<3 files`
  bound; Task 1 is the one deliberate exception at 5 files (two lockstep
  agent-doc mirrors that must change together + two co-located test files +
  a mechanical `harness-manifest.yaml` checksum bump) — a single cohesive,
  width-isolated change carried under explicit plan-hardening (see Plan
  Hardening Signals), not a claim of blanket `<3 files` compliance. Splitting
  it would only re-introduce the same file-overlap between the halves.
* **Five entries left in the stash rather than force-fit into this shipment**
  — see Sizing Rationale above. Keeps this shipment focused and reviewable
  instead of a mega-batch.

## Risks and Caveats

* **Task 1 is the highest-risk task in this shipment** — it changes a
  ratified test contract (`test_092s_execution_ready_guardrails_are_documented_in_ship_agents`,
  `test_telemetry_ship_lifecycle.py:156-165`) and edits `.ship.agent.md`
  literals that Ship's own execution-readiness gate logic depends on.
  **Mitigation**: explicit plan-harden pass below (test-contract-update-first
  sequencing); the task's acceptance criteria require the updated test to run
  red before any doc edit, and require the `task-only manifests`/`parent_id`/
  `execution-ready` assertions to remain unchanged and passing throughout.
* **Task 2 risk**: adding a hard `timestamp` requirement to the non-context
  record path could reject payloads that previously succeeded silently.
  **Mitigation**: this is the intended fail-closed behavior (Constitution I);
  the new test explicitly proves the previously-silent case now fails
  loudly, and the guardrail test proves the explicit-timestamp path still
  succeeds and replays idempotently.
* **Task 5 risk**: widening `additionalProperties:false` schemas could
  theoretically reject events other schema consumers currently produce.
  **Mitigation**: task is additive-only (two new optional array properties);
  no existing property is removed or retyped; both schema files are updated
  in lockstep to avoid drift between the base and versioned mirror.
* **Invariant preservation**: no task touches `_merge_telemetry_context_payload`,
  the context-ref record path's protected `captured_at` fallback, decide-then-
  stash ordering, or any secret-handling logic. All fixes are validation/
  reporting/documentation-scoped.

## Plan Hardening Signals (REQUIRED)

* Public API, schema, or contract change: **present (Task 5, additive-only;
  Task 1, documentation-contract change to a ratified test + agent docs)**.
* Security, auth, permission, or compliance-sensitive behavior: **absent** —
  no task touches authentication, authorization, or secret handling.
* Migration, backfill, destructive data/config action, or irreversible step:
  **absent**.
* External integration, operator checkpoint, or external dependency:
  **absent** — all changes are internal to the telemetry subsystem and its
  own test/schema/doc contracts.
* High runtime, rollout, or rollback risk: **absent** for Tasks 2-8 (isolated,
  file-disjoint, additive validation/reporting fixes with full test coverage).
  **Present (narrow) for Task 1** — it changes the literal condition Ship's
  own agent definition uses to determine execution-readiness gating; an
  incorrect generic-derivation rewrite could silently break the 092-S gate
  for future shipments.

**Requires plan hardening: YES, for Task 1 only.** Task 1's dual touch (a
ratified test contract + the `.ship.agent.md` execution-readiness gate
literals that downstream Ship sessions depend on) constitutes elevated blast
radius per this shipment's explicit sizing directive. Tasks 2-8 do not require
hardening (additive, file-disjoint, fully test-covered, no contract/gate
change). See Plan Hardening applied below.

### Plan Hardening Applied — Task 1

**Hardening action: test-contract-update-first sequencing (explicit,
non-negotiable ordering within Task 1).**

1. The ratified test `test_092s_execution_ready_guardrails_are_documented_in_ship_agents`
   MUST be updated (literals removed, generic-derivation-phrase + explicit-
   timestamp assertions added) BEFORE either agent doc is edited.
2. The updated test MUST be confirmed to fail (red) against the *current,
   unmodified* doc content — proving the test change alone doesn't
   accidentally pass against stale docs (which would mean the new assertions
   are too weak).
3. Only then may `templates/agents/.ship.agent.md.tmpl` and
   `.github/agents/.ship.agent.md` be edited, identically in substance.
4. The test must go green against the edited docs, and the pre-existing
   `task-only manifests`/`parent_id`/`execution-ready` assertions in the same
   test must remain unchanged and passing throughout — these are NOT part of
   this task's scope and must not regress.
5. Both doc files must be diffed against each other after the edit to confirm
   substantive parity (no drift between the template and the installed doc).

This sequencing is captured verbatim in Task 1's Implementation Unit above and
is a binding acceptance criterion for the task, not an optional suggestion.

## Runtime Verification and Closure

* Four of these tasks DO change an operator- or consumer-visible contract, so
  `pytest` green is necessary but not sufficient — each carries an explicit
  compatibility expectation and a runtime check:
  * **Task 2 (090.002-T)** makes `timestamp` mandatory (and ISO-8601-valid) on
    the non-context `telemetry record` path — previously omitted timestamps were
    auto-stamped. This is a fail-closed CLI behavior change: callers omitting or
    malforming `timestamp` now exit 2. Compatibility: harness/agents already pass
    explicit ISO-8601 timestamps; runtime check — a `telemetry record` smoke call
    with a valid explicit timestamp confirms created/idempotent_replay, and calls
    omitting or malforming it confirm the new exit-2 diagnostic.
  * **Task 3 (090.003-T)** makes `telemetry begin` fail fast (exit 2,
    `TelemetryContextError`) on a backlog_item_id/task_id mismatch that
    previously succeeded silently. Compatibility: only genuinely inconsistent
    begin calls change outcome; runtime check — a `telemetry begin` smoke call
    with a deliberate mismatch confirms the exit-2 diagnostic.
  * **Task 5 (090.005-T)** changes the public embedded WorkSizingSnapshot JSON
    Schema (adds `feature_skipped_ids`/`shipment_skipped_ids`). The change is
    additive/permissive (previously-rejected valid payloads now validate);
    runtime check — validate a sample event carrying both fields against the
    base and versioned schema files.
  * **Task 8 (090.008-T)** changes serialized eval-summary output (adds a
    provenance/quality marker to derived ratios). Compatibility: additive field
    on the summary structure; runtime check — an `eval summary` run over a
    fixture with estimated and observed operands confirms the new provenance
    marker appears without breaking existing consumers of the structure.
* Tasks 4, 6, and 7 are internal validation/computation/reporting fixes with no
  new CLI-contract or public-schema change; `pytest` green for each task's
  modified test file is sufficient proof of absorption.
* Task 1 changes agent-definition documentation (and its harness-manifest checksum) consumed by the Ship agent's
  own execution-readiness gate logic at build/PR time. Runtime verification
  for Task 1 is: (a) the updated ratified test passing, and (b) a manual diff
  confirming both `.ship.agent.md` and its template mirror state the generic
  derivation rule identically. No live Ship session needs to be run to absorb
  this change — the next real shipment's execution-readiness gate check will
  naturally exercise the new generic rule.
* **Operational closure artifact**: the per-task runtime checks above are
  recorded in this shipment's PR local review readiness record; none of these 8
  tasks touch a monitored production surface, so no separate monitoring/rollback
  artifact is required.

Generated by: Stage (staging session) | PR #227 telemetry hardening

## Plan Review

**Gate decision: PASS.**

Cross-model persona spawning was not available in this session (single-model
Stage context); all personas below were evaluated by the caller model. This is
non-blocking per the plan-review skill contract ("If cross-model invocation is
not available, run all personas with the caller's model. Multi-model is
preferred but not blocking.").

### Plan Hardening Requirement Check

The plan declares `Requires plan hardening: YES, for Task 1 only`, per the
Orchestrator's explicit instruction that Task 1 (ratified test contract change
+ `.ship.agent.md` execution-readiness literals) is elevated blast radius.
Reviewed the applied hardening (test-contract-update-first sequencing,
above): the sequencing is explicit, binding, and embedded directly in Task 1's
Implementation Unit and acceptance criteria, requiring red-before-docs-edit
verification and preservation of the unrelated `task-only manifests`/
`parent_id`/`execution-ready` assertions. **Hardening requirement confirmed as
satisfied.** Tasks 2-8 correctly do not require hardening (additive,
file-disjoint, fully test-covered, no gate/contract change).

### Findings

| ID | Severity | Persona | Finding | Resolution |
|---|---|---|---|---|
| P2-1 | P2 | Scope Boundary Auditor | Task 5 leaves the analogous `schemas/execution-epoch.schema.json` gap unaddressed. | Accepted — explicitly out of scope per stash 64C01A60's own framing; recorded as a residual observation in the Requirements Trace and Task 5's Implementation Unit. Candidate for a future stash entry. |
| P2-2 | P2 | Python Reviewer | Task 8's fix note leaves the exact shape of the new provenance field (e.g. a nested `quality` key vs. a suffix-named sibling field) unprescribed, deferring the concrete schema choice to build time. | Accepted as a backlog/build-time decision — the acceptance criteria constrain the *behavior* (provenance must be surfaced, existing case preserved) without over-prescribing the JSON shape, consistent with this repo's plan-doc convention of leaving reviewer's-call implementation choices to build time when they don't affect correctness. |
| P3-1 | P3 | Architecture Strategist | Tasks 4 and 7 both touch data-quality "unavailable" surfacing patterns in different modules (`sizing.py`, `epoch.py`) that could eventually be unified into a shared helper. | Advisory only. Not required for this shipment; no existing shared abstraction exists to extend, and forcing one now would expand blast radius beyond the 2-Hour Rule for either task. |

**P0 = 0, P1 = 0.**

### Persona Notes

* **Constitution Reviewer**: No violations. Principle II (TDD) satisfied by
  test-first sequencing in all 8 tasks. Principle IV (CLI workspace
  containment) not implicated — no task touches workspace-root resolution.
  Principle XI (merge-commit-only) and P-016 (single worktree) are Ship-phase
  concerns, out of scope for this Stage-only plan.
* **Python Reviewer**: All 8 fixes follow existing idiomatic patterns already
  present in the same modules (reusing `EpochError`, the `_coerce_nonneg_metric`
  strict-type pattern, the existing "unavailable" tuple convention, and the
  existing `criteria`/`notes` report shape). See P2-2.
* **Scope Boundary Auditor**: Confirmed every task stays within its declared
  file set and is width-isolated to a single domain. Seven tasks are ≤3 files;
  Task 1 is 5 files (two lockstep agent-doc mirrors + two co-located test files
  + a mechanical manifest-checksum bump) — a single cohesive width-isolated
  change carried under explicit plan-hardening, not a granularity violation.
  Confirmed the 5 left-stashed entries are genuinely separable (see Sizing
  Rationale) and not silently dropped. See P2-1.
* **Learnings Researcher**: No prior compound learning found that
  contradicts this plan's sizing or task-only manifest convention; the
  092-S/093-S/094-S precedent for task-only shipment manifests is directly
  confirmed by this shipment's own `backlogit shipment get 095-S` output
  (feature `090-F` absent from `custom_fields.items`).
* **Architecture Strategist**: Tasks 3–8 are fully decoupled (disjoint files,
  no shared state, no `backlogit dep` edges needed); Tasks 1 and 2 share only
  `tests/test_telemetry_record_cli.py` and are sequenced for that file. See P3-1.
* **Security Lens Reviewer**: Not triggered as a P0/P1 concern — no task
  touches authentication, authorization, secret handling, or workspace
  containment. Task 1's touch to `.ship.agent.md` is a documentation/gate-logic
  change, not a security-boundary change; covered by the plan-hardening
  sequencing above rather than a separate security finding.
* **Agent-Native Parity Reviewer**: Triggered for Task 5 (schema surface
  change) and Task 1 (agent-doc/gate-logic change). Task 5 is additive-only
  and preserves `additionalProperties:false` semantics for all previously-valid
  payloads. Task 1's plan-harden sequencing directly addresses parity risk
  between the template and installed doc (explicit post-edit diff
  requirement). No P0/P1 parity finding.

### Runtime Verification and Closure Check

Confirmed adequate: Tasks 2-8 are local, non-runtime-surface changes; `pytest`
green per task is sufficient absorption evidence. Task 1's runtime
verification (ratified test green + template/doc parity diff) is explicit in
its Implementation Unit and the Runtime Verification and Closure section
above. No monitoring, rollback, or operator checkpoint artifacts are required
for this shipment.
