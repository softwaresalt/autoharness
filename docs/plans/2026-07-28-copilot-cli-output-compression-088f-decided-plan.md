---
source: docs/plans/2026-07-28-copilot-cli-output-compression-088f-decided-plan.md
title: "Copilot CLI Output Compression Experiment Hardening Lineage"
doc_type: decided-plan
status: shipped
created: 2026-07-28
feature:
  - "088-F"
  - "093-F"
supersedes:
  - docs/archive/plans/2026-07-15-copilot-cli-output-compression-experiment-plan.md
  - docs/archive/plans/2026-07-26-088-f-review-followup-hardening-plan.md
  - docs/archive/plans/2026-07-28-088-failure-content-in-success-decline-followup-plan.md
---

# Decided Plan: Copilot CLI Output Compression Experiment Hardening Lineage

**Outcome:** Consolidated the 088-F/093-F Copilot CLI output-compression lineage into a reviewed end state. The 2026-07-15 origin plan and the 2026-07-28 follow-up both carried `approved-with-conditions` verdicts, and the 2026-07-26 hardening follow-up passed plan review. The source plans themselves record that `088.004-T` shipped the failure-bearing-success decline detector in commit `118bf21`, but they do not carry one final PR/merge note for the full 088-F/093-F lineage, so this decided-plan records the lineage as **reviewed** rather than shipped. It replaces the verbose originals archived at the paths listed under `supersedes`.

**Delivery status (verified against the backlog at compaction time):** shipped — `088-F`, `088.001-T`, `088.004-T`, `088.007-T`, `093-F` confirmed complete in `.backlogit/`. Remaining open follow-up work tracked separately: `093.001-T` (queued), `093.003-T` (queued).

## Evolution

| Date | Link | What changed | Status evidence |
|---|---|---|---|
| 2026-07-15 | `088-F` origin experiment | Defined a bounded throwaway experiment with seven tasks: contained local store, `postToolUse` hook, byte-equivalent retrieval, decline/evidence policy, AUC measurement, benchmark corpus/report, and a findings memo. | Plan-review `approved-with-conditions`; later in-file notes record that `088.004-T` shipped the failure-bearing-success detector in commit `118bf21`. |
| 2026-07-26 | `088-F` review follow-up | Closed two PR #229 follow-up findings: non-string payload `cwd` must fail safe through `WorkspaceContainmentError`, and early-decline benchmark results must preserve `capture_failed` and non-live `provenance`. | Plan-review PASS; `Requires plan hardening: no`. |
| 2026-07-28 | `093-F` spec-reconciliation follow-up | Promoted the failure-bearing-success decline invariant into the system-of-record, broadened the detector beyond colon-anchored forms, and required parity across `policy.py`, `hook.py`, and `evidence_oracle.py`. | Plan-review `approved-with-conditions`; no final shipped note is appended in the source plan. |

## Decisions

1. **Keep the experiment throwaway, flag-gated, and disabled by default.** No default install, no generated-harness dependency, no base-harness behavior change, and no second graph stack.
2. **Treat containment, decide-then-stash, and byte-equivalent retrieval as hard invariants.** Secret screening precedes durable storage; any store/screen/guard error passes the original result through unchanged; retrieval must not silently truncate.
3. **Treat failure-bearing-success detection as a hard evidence-integrity gate.** A successful `postToolUse.textResultForLlm` carrying non-zero exit evidence, `stderr`, a stack trace, or a gate/readiness verdict must be declined, not compressed.
4. **Use the broadened, colon-agnostic failure-signal set and keep semantic parity across `policy.py`, `hook.py`, and `evidence_oracle.py`.** Every added pattern requires positive and negative controls.
5. **Preserve benchmark honesty.** Early-decline reporting must carry `capture_failed` and `provenance`, and benchmark safe wins remain gated by the evidence oracle.

## Implementation (10 units across the lineage)

* **`088-F` origin experiment (`088.001-T`..`088.007-T`)** — contained local store/resolver under `.autoharness/cache/brainspace/`; `postToolUse` hook with deterministic placeholder and never-expand guard; byte-equivalent retrieval tool; decline/evidence policy; AUC measurement harness; benchmark corpus/report; findings and operator decision memo.
* **`088-F` review follow-up hardening** — tightened `resolve_workspace_root` so a truthy non-string payload `cwd` becomes a catchable `WorkspaceContainmentError` instead of a raw `TypeError`, and extended early-decline `CaseResult` reporting so `capture_failed` and non-live `provenance` survive into benchmark output.
* **`093-F` follow-up (`093.001-T`..`093.003-T`)** — broadened detector coverage to common non-colon exit/stderr forms, aligned hook/oracle evidence-line protection to the same set, and reconciled the 2026-07-15 plan so the archived 088-F spec remains the system-of-record for the deferred narrow pilot.

## Key constraints preserved

* Optional overlay only: the experiment stays disabled by default and does not become a production capability pack.
* No schema changes, CLI-distribution changes, or default-install behavior changes are introduced by this lineage.
* Failure-signal detection stays precise and enumerated; the plans explicitly reject a generic "any error/failed/non-zero" heuristic.
* Negative controls are mandatory for every broadened failure-bearing-success pattern so AUC-savings measurements stay honest.
* The failure-bearing-success decline invariant is a promotion gate and must not regress in any future narrow pilot.
* The 2026-07-26 hardening task deliberately kept the optional `hook_cli.py` end-to-end case out of required scope so the fix stayed inside its intended file-count boundary.

## Rejected alternatives

* **Production/default compression install** — rejected until the experiment proves honest savings without compromising evidence integrity.
* **Generic "any error/failed/non-zero" matching** — rejected because the experiment needs precise, testable forms and paired negative controls to protect measurement fidelity.
* **Sentinel return or ad hoc `hook_cli.py` catch-path instead of `WorkspaceContainmentError`** — rejected because the module already had a single fail-safe exception contract that `hook_cli.py` could catch consistently.
* **Widening `CaseResult` with new top-level fields** — rejected because the existing `criteria`/`notes` shape could carry `capture_failed` and `provenance` with a smaller blast radius.
* **Making the optional `hook_cli.py` subprocess test mandatory in the 2026-07-26 task** — rejected because it would have expanded that task past its intended width; it was preserved only as an advisory follow-up.

## Post-review refinements folded in

* The 2026-07-15 origin plan kept four standing conditions: stay flag-gated, make no schema/CLI-distribution changes, prove byte-equivalent retrieval plus decide-then-stash before claiming savings, and re-verify the Copilot CLI hooks contract against the target CLI version.
* The 2026-07-26 hardening review raised one P1 scope finding that changed the plan: the end-to-end `hook_cli.py` case was removed from required scope so Task 1 stayed at two edited files instead of three. The shared-helper concern for benchmark notes was kept as a non-blocking follow-up rather than widening the task.
* The 2026-07-28 follow-up review required Ship to extend the already-shipped detector/tests rather than re-implement them, to add a paired negative control for every new failure-signal pattern, and to keep `policy.py`, `hook.py`, and `evidence_oracle.py` semantically aligned.

## Rollback

Disable the experiment flag and purge `.autoharness/cache/brainspace/` to remove the prototype. The review-followup and spec-reconciliation changes are localized to the throwaway experiment module, its tests, and the archived 088-F plan text.