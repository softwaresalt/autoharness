---
title: "Plan review attempt 10 - SHIP-HARNESS-LIFECYCLE-FOUNDATION (187-S)"
description: "Immutable per-attempt artifact for the TENTH independent review of the Ship harness lifecycle plan and the FIRST review of revision 11. FAIL/BLOCK: P0 0, P1 14, P2 2. The multi-persona review completed, but secure-read traversal and bounds, RED validity, resolver totality, CLI behavior, Ship placement, rollback scope and task granularity remain insufficient. The mutable verdict manifest remains stale because its existing empty lock was left untouched."
doc_type: review
source: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-10.md
date: 2026-09-20
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 10
attempt_range: "10"
attempt_conformance: conforming
review_terminal: true
terminal_designation: terminal-fail-recording-only-no-follow-on-authorized
terminal_disposition: FAIL-BLOCKING-P1
terminal_note: "Attempt 10 consumes attempt number 10. This narrow persistence directive authorizes only this immutable artifact and no remediation, attempt 11, mutable-manifest update or backlog mutation."
verdict_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
verdict_manifest_mutated_by_this_attempt: false
predecessor_artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-09.md
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_id: ship-harness-lifecycle-foundation
reviewed_revision: 11
plan_revision_commit: 0bd74189
reviewed_content_head: d8b04112
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
plan_mutated_by_this_attempt: false
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 8
feature_id: 181-F
shipment_id: 187-S
declared_surface_count: 1
review_cycle: 10
dispatch_mode: multi-agent
security_lens_triggered: false
gate_result: FAIL
decision: BLOCK
verdict_is_pass: false
verdict_at_entry: null
verdict_at_entry_disposition: PENDING-INDEPENDENT-REVIEW
verdict_at_entry_plan_revision: 11
verdict_at_entry_manifest_revision: 19
verdict_at_entry_publication_eligible: false
remediation_authorization: not-authorized
remediation_performed: false
remediation_cycle_proposed: false
disposition: FAIL-BLOCKING-P1
p0_findings: 0
p1_findings: 14
p2_findings: 2
p3_findings: 0
merged_findings_count: 16
blocking_findings_count: 14
findings_raised_at_this_attempt: [S53, S54, S55, S56, S57, S58, S59, S60, S61, S62, S63, S64, S65, S66]
nonblocking_findings_raised_at_this_attempt: [S67, S68]
predecessor_closure_assessment: not-totalized-in-known-merged-summary
previously_closed_findings_unchanged:
  - finding: S14
    state: CLOSED
    closed_at_attempt: 8
    reaffirmed_at_this_attempt: true
    note: "S14 remains closed on the external Ship evidence recorded at attempt 08. This attempt does not reopen it or extend that closure to another finding."
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_note: "Revision 11 adds substantial hardening, but the secure-read primitive, resolver input model, CLI failure envelope, Ship replacement semantics, rollback scope and task granularity remain insufficient for execution."
personas_applied:
  - constitution
  - python
  - scope-boundary
  - learnings
  - architecture
  - agent-native-parity
personas_not_applied:
  - security-lens
tags:
  - "plan-review"
  - "attempt"
  - "fail"
  - "revision-11"
  - "secure-read-contract"
  - "portfolio-2026-09-18"
---

# Plan review attempt 10 — Ship pre-task harness-generation lifecycle

## Reviewed subject

`docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` at **revision 11**, committed by `0bd74189` and reviewed at content HEAD `d8b04112` on branch `chore/stage-176-s-workflow-defects`, together with live carriers `181-F`, `181.001-T`–`181.007-T` and `187-S`, governing decision revision 8, and mutable verdict manifest revision 19.

This is the **first** independent review of revision 11. The multi-persona review completed and merged the known findings below. This artifact records that merged set only; it does not invent model routes, per-persona result counts or a predecessor-finding closure matrix that was not included in the known summary.

The mutable manifest could not be updated. The existing zero-byte lock `docs/reviews/.2026-09-18-ship-harness-lifecycle-foundation-plan-review.md.lock` was observed and left untouched. The lock does not cover this new immutable history path.

## Gate result

**FAIL / BLOCK**, under the standing decision rule: any `P0` or `P1` produces `FAIL`; `P2`-only produces `ADVISORY`; `P3`-or-none produces `PASS`.

* `P0`: 0.
* `P1`: 14, all blocking.
* `P2`: 2.
* `P3`: 0.

The known merged set contains **16 findings**, 14 blocking. `SM-2` `HARVEST_ADMITTED` remains **SHUT**, the plan remains not publication-eligible, and `187-S` is not authorized for execution.

## Findings and actionable recommendations

### `S53` — root/component handle traversal is incomplete (P1, BLOCKING)

The Windows description opens path strings and does not define a trusted root handle plus component-by-component descent equivalent to the POSIX parent-FD model. The contract does not prove that every component and the final file are reached from one anchored root without a string re-resolution gap.

**Recommendation:** specify one implementable root-handle algorithm per platform. Every descendant component and final file must be opened from an already validated parent handle; name the exact Windows API and flags that provide the anchoring property, and fail closed when unavailable.

### `S54` — during-read byte cap is missing (P1, BLOCKING)

The per-file cap is checked only from pre-read size, and the aggregate budget is not debited while chunks are read. A growing file can exceed both limits before post-read checks observe the change.

**Recommendation:** enforce per-file and aggregate limits inside the read loop. Check each chunk before retaining it, stop at the first byte beyond the remaining budget, and return the bounded-read reason without decoding or retaining the over-limit payload.

### `S55` — Windows same-size mutation detection is incomplete (P1, BLOCKING)

The Windows pre/post tuple includes volume, file index and size but no last-write or change indicator. Same-file, same-size in-place mutation can pass the comparison.

**Recommendation:** bind a handle-reported mutation indicator into both snapshots and require it to remain equal with file identity and size. Add a deterministic same-size mutation case to the Windows adapter tests.

### `S56` — public `harness_read` contract is incomplete (P1, BLOCKING)

The plan declares a public module and makes it the resolver filesystem boundary, but gives no public callable name, signature, result/error type, budget object, decoding boundary, adapter contract or handle-ownership rule.

**Recommendation:** define the exact public API before execution: keyword parameters, immutable result and error types, budget lifetime, byte ownership, adapter seam, close guarantees, and the mapping from every primitive failure to the closed resolver reason codes.

### `S57` — invalid RED import laundering and characterization/RED mixing (P1, BLOCKING)

`181.001-T` converts `ImportError` and `ModuleNotFoundError` into `AssertionError`. Changing the exception class does not prove behavior and launders an absent module into acceptable RED evidence. The task also mixes characterization of missing interfaces with behavior-first RED across three modules.

**Recommendation:** prohibit import-error laundering and split characterization from RED. Establish an importable interface in a reviewed predecessor before behavior RED, or record missing-module evidence as characterization only and never as P-004 RED.

### `S58` — checkpoint restore replacement is not required (P1, BLOCKING)

The five-step Ship sequence is inserted into each crash-resumption section, but the plan does not require the old restore order to be replaced or removed. A cursor-first path can survive beside the new prose.

**Recommendation:** identify and atomically replace the exact existing restore block in both Ship files. Tests must prove the prior cursor-first sequence is absent, the new sequence occurs once, and no alternate path restores execution state before a fresh resolver succeeds.

### `S59` — asymmetric Ship placement is incorrectly modeled as symmetric (P1, BLOCKING)

The template updates an existing `Step 2` section while the mirror inserts `Step 1.5`, yet `PAR-2` requires one equivalent position in both files. That symmetric criterion conflicts with the intentionally asymmetric established layouts.

**Recommendation:** define separate exact placement invariants for template and mirror, then assert semantic body parity independently. Do not use one positional rule for two different step structures.

### `S60` — CLI invalid-usage envelope is incomplete (P1, BLOCKING)

The CLI assigns exit `2` to invalid usage and requires the JSON schema on every outcome, but does not totalize missing arguments, unknown options, malformed IDs, help, parser termination, stdout, stderr and non-JSON mode.

**Recommendation:** specify the parser boundary and every invalid-usage outcome, including exact state, reason, exit code and stream behavior. Define how parser termination is intercepted so the emitted `exit_code` and process status cannot diverge.

### `S61` — zero, duplicate and unsupported shipment members are not totalized (P1, BLOCKING)

The plan bounds membership and requires one record per member ID, but does not define deterministic outcomes for an empty list, duplicate IDs in `custom_fields.items`, or member records outside the supported feature/task shapes.

**Recommendation:** add explicit grammar rows and closed reason codes for zero members, duplicate member IDs and every unsupported member type. State how feature members contribute evidence and preserve every rejected raw member in diagnostics and digest inputs.

### `S62` — digest omits consulted records and `shipment_id` (P1, BLOCKING)

The digest binds the shipment record and derived declarations, but not the caller-supplied `shipment_id` as its own domain input and not the raw bytes of every consulted member-record candidate. Materially different consultations can therefore share a preimage.

**Recommendation:** bind `shipment_id` explicitly and bind every consulted record candidate with stable labels containing member ID, record class/source and occurrence ordinal. Derived declarations may supplement but not replace raw consulted evidence.

### `S63` — duplicate manifest-load classification (P1, BLOCKING)

Manifest availability appears as an A1 precondition while parsing, top-level shape and matched-entry handling also occur in surface classification. The plan does not require one typed load result, so the same failure can be classified twice with different precedence.

**Recommendation:** load and parse the manifest exactly once into one typed result. Define one ordered mapping for missing, unreadable, invalid YAML, invalid top-level shape, duplicate entries and surface mismatch; all later logic must consume that result.

### `S64` — canonical commands omit `PYTHONPATH=src` (P1, BLOCKING)

Several unit-test commands include `PYTHONPATH=src`, but canonical CLI examples and the ACTIVATE carrier full-suite command are not consistent with the source-layout import contract.

**Recommendation:** make `PYTHONPATH=src` part of every canonical repo-local command, including CLI examples, targeted verification and full-suite execution, with platform-appropriate syntax wherever cross-platform execution is claimed.

### `S65` — rollback approval asks for a fourth repo file (P1, BLOCKING)

The ACTIVATE task freezes scope to three activation files, then requires fresh approval to be copied into `181.005-T` before `git revert`. That task record is a fourth repository file and contradicts the frozen rollback unit.

**Recommendation:** retain approval evidence in the approved operator or telemetry channel rather than the rollback diff, or explicitly redesign and re-review the rollback scope. Do not require a task-file write inside a three-file frozen-scope revert path.

### `S66` — `181.001-T`, `181.002-T` and `181.006-T` exceed the 2-hour rule (P1, BLOCKING)

All three are `M` / `high`. The RED task owns three broad test modules, the secure-read task owns a cross-platform security primitive, and the resolver task owns lookup, declarations, rendering, diagnostics, aggregation and digests. Each exceeds a reliable two-hour unit despite the revision-11 split.

**Recommendation:** split each into independently verifiable tasks below two hours. Isolate platform traversal, public API and budgeting, record/declaration logic, rendering and digests, and test families. Any remaining `complexity: high` task requires another split or de-risking spike.

### `S67` — mutable manifest stale (P2)

`docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md` still selects attempt 09, reports revision 11 as unreviewed and awaits attempt 10. The existing empty lock prevented a safe update.

**Recommendation:** after the lock owner resolves the lock through normal ownership policy, perform a separate authorized manifest-only update selecting this immutable attempt. Do not force-release the lock.

### `S68` — decision three/four-unit count is inconsistent (P2)

Decision revision 8 says there are three genuinely queued and unclaimable units, then lists `185-S`, `186-S`, `178-S` and `180-S` — four units.

**Recommendation:** in a separately authorized decision update, change the count to four or change the list if one entry is unintended, then revalidate the surrounding portfolio table.

## Recommended remediation order

1. Split `181.001-T`, `181.002-T` and `181.006-T`, and place the public `harness_read` API and budget ownership in the earliest prerequisite task.
2. Correct root-anchored traversal, during-read caps and Windows same-size mutation detection.
3. Rebuild the RED sequence without import laundering and with characterization separated from behavioral RED.
4. Totalize shipment membership, single-load manifest classification, consulted-input digests and CLI invalid usage.
5. Replace rather than supplement checkpoint restore, and model template and mirror placement with separate anchors.
6. Normalize canonical commands and remove the fourth-file rollback-record requirement.
7. Only after the existing lock is resolved, update the mutable lifecycle manifest and correct the decision count in separately authorized edits.

## Runtime verification and closure assessment

No runtime verification was executed by this Stage recording turn. The planned modules `src/autoharness/harness_read.py` and `src/autoharness/harness_surfaces.py`, and their planned tests, do not exist at the reviewed HEAD. Stage is not authorized to run build systems, test suites or linters. The review assessed whether the planned runtime proof would be sufficient; it did not claim runtime evidence that does not exist.

No attempt-10 closure is granted for the blocking contract. `S14` remains closed on the external Ship evidence recorded at attempt 08. The known merged summary did not provide a predecessor closure matrix for `S13` and `S15`–`S52`, so this artifact does not invent one; this FAIL stands independently on `S53`–`S68`.

P-004 attempt 03 was **not reviewed**. `docs/plans/2026-09-18-p004-observation-gate-plan.md` and `docs/reviews/2026-09-18-p004-observation-gate-plan-review.md` remain blocked. Nothing in this lifecycle attempt changes that state or authorizes P-004 attempt 03.

## Persona coverage

| Persona | Applied |
|---|---|
| Constitution | yes |
| Python | yes |
| Scope boundary | yes |
| Learnings | yes |
| Architecture | yes |
| Agent-Native Parity | yes |
| Security Lens | no |

`dispatch_mode: multi-agent`. The established persona coverage is preserved exactly. This artifact records only the merged findings and does not invent model routes, per-persona result counts or unreported dispatch metadata.

## Authorization boundary

This attempt **consumed attempt number 10** and is terminal for the present authorization. Only this immutable history artifact was authorized. No remediation, attempt 11, mutable-manifest update, plan or decision edit, backlog mutation, checkpoint action, stash action, shipment action, source change, GitHub action or push was performed.

The lock helper was not used for the new path because `scripts/acquire_lock.ps1` requires the target file to exist before acquisition. No manual lock or policy bypass was invented. The pre-existing mutable-manifest lock was left untouched.

## Scope statement

Reviewed: plan revision 11; `181-F`, `181.001-T`–`181.007-T`, `187-S`; governing decision revision 8; mutable lifecycle manifest revision 19 as the stale selection surface; and attempt-09 history.

Not reviewed: P-004 attempt 03; runtime implementation of the planned modules; source, test, template or installed-agent changes; backlog, checkpoint, stash, shipment or GitHub mutations.
