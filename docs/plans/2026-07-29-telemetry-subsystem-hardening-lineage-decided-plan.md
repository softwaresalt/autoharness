---
title: "Telemetry Subsystem Hardening Lineage"
doc_type: decided-plan
status: shipped
created: 2026-07-29
feature:
  - "090-F"
  - "092-F"
  - "095-F"
supersedes:
  - docs/archive/plans/2026-07-26-telemetry-hardening-plan.md
  - docs/archive/plans/2026-07-28-telemetry-followup-hardening-plan.md
  - docs/archive/plans/2026-07-29-telemetry-jsonl-sink-rotation-retention-plan.md
---

# Decided Plan: Telemetry Subsystem Hardening Lineage

**Outcome:** This lineage ends in an explicitly shipped final link: feature `095-F` / shipment `100-S`, shipped 2026-07-29 in PR #250, merge commit `ac94a3f`, per the 2026-07-29 source plan. The earlier links are preserved here as predecessor reviewed/hardened plans: the 2026-07-26 `090-F`/`095-S` plan passed review and hardened Task 1, and the 2026-07-28 `092-F`/`097-S` plan is marked reviewed/hardened and is later referenced by the shipped 095-F plan as `prior_work: 092-F / 097-S (PR #241, telemetry subsystem hardening)`. This decided-plan replaces the verbose originals archived at the paths listed under `supersedes`.

## Evolution

| Date | Link | What changed | Status evidence |
|---|---|---|---|
| 2026-07-26 | `090-F` / `095-S` | Collapsed 11 coupled telemetry findings into eight TDD tasks covering ship-gate genericization, close-timestamp reuse, non-context timestamp validation, early backlog/task mismatch rejection, honest unavailable semantics, embedded schema fixes, report-quality semantics, strict epoch validation, and derived-ratio provenance. | `origin_feature: 090-F (PR #227 telemetry hardening)`; plan-review PASS; Task 1 required explicit P-006 hardening, but the plan itself carries no appended merge-commit note for this link. |
| 2026-07-28 | `092-F` / `097-S` | Picked up the five deliberately deferred leftovers: disabled `RecordSummary` default, persist-time `missing_provenance`, JSONL duplicate-scan optimization, CLI-level backlogit freshness proof, and ordinal size-label monotonicity observations. | Frontmatter `status: reviewed`, `plan_hardened: true`; explicitly left JSONL rotation/retention out of scope; the later 095-F source cites this link as `prior_work: 092-F / 097-S (PR #241, telemetry subsystem hardening)`. |
| 2026-07-29 | `095-F` / `100-S` | Picked up the deferred JSONL rotation/retention work with segment generations, cross-segment replay, reader support, no-replace sealing, bounded retention, explicit retention-horizon semantics, and a code-evidenced concurrent-writer mirror contract. | Frontmatter `shipped: 2026-07-29 (PR #250, merge commit ac94a3f ...)`. |

## Decisions

1. **Telemetry remains observational and fail-open.** Missing provenance becomes additive structured reporting, not a persistence error; disabled/no-op summaries return explicit `"disabled"`.
2. **Validate earlier and surface uncertainty honestly.** Non-context records require stable explicit timestamps; begin-context rejects backlog/task ID mismatches early; invalid `snapshot_boundary` values and non-integer exit codes fail closed; impossible sizing histograms and missing quality labels degrade to `"unavailable"` instead of being silently coerced.
3. **Preserve task-only shipment manifests and generic ship gating.** Execution-readiness derives from declared task dependencies, not embedded task IDs, and close timestamps are captured once and reused on retry.
4. **Keep size-label analysis ordinal-only.** Monotonicity is an additive observation, not a hard assertion or numeric point system.
5. **Keep the JSONL sink as a best-effort concurrent-writer mirror with SQLite authoritative.** Rotation is size-based, uses monotonic sealed generations and no-replace generation claims, scans retained segments for replay/conflict checks within the retention horizon, and extends the reader across active plus sealed segments. No global lock, no compaction, and no config-schema expansion.

## Implementation (17 tasks across three links)

* **`090-F` / `095-S` (`090.001-T`..`090.008-T`)** — genericized Ship readiness docs and close-timestamp reuse; required explicit timestamp validation on non-context `telemetry record`; failed fast on backlog/task mismatch at begin time; surfaced unavailable `unsized` composition honestly; added skipped-ID schema fields; distinguished missing quality labels from observed data; strictly validated `snapshot_boundary` and exit-code element types; propagated estimated/unavailable provenance through derived ratios.
* **`092-F` / `097-S` (`092.001-T`..`092.005-T`)** — standardized disabled `RecordSummary` output, added persist-time `missing_provenance`, reused JSONL preflight scans with a bounded tail rescan, proved backlogit freshness through a CLI-level lifecycle test, and added ordinal size-label monotonicity observations.
* **`095-F` / `100-S` (`095.001-T`..`095.004-T`)** — added segment enumeration plus generation-aware preflight identity; size-based rollover with a no-replace claim and oversized-record handling; bounded sealed-segment retention with an explicit byte bound and prune horizon; and reader traversal across rotated segments with late-line reconciliation.

## Key constraints preserved

* Shipment manifests stay task-only across `095-S`, `097-S`, and `100-S`; the covering feature is derived via `parent_id` and not listed in `custom_fields.items`.
* Telemetry stays fail-open: missing provenance is visible but non-blocking, and JSONL scan reuse cannot weaken idempotent replay or conflict detection.
* JSONL rotation/retention remained explicitly out of scope for `092-F` and was picked up later as its own width-isolated `095-F` shipment.
* Additive metadata is preferred over overloading numeric values; the lineage rejects a new `"unknown"` quality state and reuses the documented `"unavailable"` vocabulary.
* `095-F` keeps rollover policy in module constants rather than widening config/schema/CLI/template surfaces.
* No global writer lock is introduced; late writes into a just-sealed segment are accepted as best-effort mirror behavior and reconciled on read.
* Pruning touches only sealed mirror segments, never the active segment and never authoritative SQLite history.
* The retained-byte claim is the achievable `threshold + one max record` bound, not an impossible exact ceiling.

## Rejected alternatives

* **Force-fitting all 16 PR #227 follow-ups into one mega-batch** — rejected; five separable items were left out of the 2026-07-26 shipment so it stayed reviewable.
* **Keeping hard-coded `079.013-T` / `079.015-T` gate literals** — rejected; execution-readiness must derive from the shipment's own declared task dependencies.
* **Adding a new `"unknown"` quality state** — rejected because the documented vocabulary already uses `"unavailable"` for missing provenance.
* **Hard persist-time rejection for missing provenance** — rejected because it conflicts with telemetry's fail-open observational role; advisory-only silence was also rejected because it hides the contract breach. The chosen contract is an additive `missing_provenance` signal.
* **Numeric label-to-point mapping or hard monotonicity assertions** — rejected until a named/versioned mapping exists; the accepted contract is ordinal-only observation.
* **Pulling JSONL rotation/retention into `092-F`** — explicitly rejected to keep that shipment width-isolated.
* **Age-based rollover or in-place compaction** — rejected for `095-F`; size-based deterministic segments were simpler and safer.
* **Runtime-configurable segment thresholds** — rejected because they would have required a four-schema + config + caller blast radius with no demonstrated need.
* **Single-writer/global-lock semantics or a `sealed = immutable` claim** — rejected as refuted by the code-documented concurrent-writer contract; the fix targets no-replace sealing instead.
* **An exact `total bytes <= (window + 1) × threshold` guarantee** — rejected because oversized records must remain intact; the bound was restated to `threshold + one max record`.

## Review findings that changed the plan

* The 2026-07-26 link hardened Task 1 explicitly because it changed both a ratified test contract and Ship-agent gate wording. The red-before-doc-edit sequence, parity diff between template and installed agent doc, and unchanged task-only-manifest assertions became binding acceptance criteria.
* The 2026-07-26 review also kept two matters out of scope: the analogous execution-epoch schema gap stayed a residual follow-up, and the exact summary-field shape for ratio provenance was left to build time so the plan could constrain behavior without over-prescribing structure.
* The 2026-07-28 hardening pass locked in the fake backlogit boundary for lifecycle freshness, additive observation maps for provenance/monotonicity, bounded tail rescans for JSONL preflight reuse, and the explicit decision that rotation/retention stayed out of scope for `092-F`.
* The 2026-07-29 hardening pass made the biggest structural changes: it kept rollover thresholds as constants (finding 2), added `reader.py` as `095.004-T` so rotated history remained readable (finding 3), replaced an earlier single-writer/immutability framing with the code-evidenced no-replace concurrent-writer model (findings A and B), and restated the byte bound to an achievable guarantee (finding 5).

## Rollback

All three links remain localized source/test/schema/doc changes with no authoritative telemetry data migration. If a link regresses, revert that link's code and tests independently; for the `095-F` rotation work, SQLite remains authoritative and retained JSONL pruning never deletes authoritative history.