---
title: "SAFE_CLOSE record-transition gap: in-workspace evidence, upstream escalation, and an operator-only interim close"
description: "Implementation plan for the autoharness-owned half of the SAFE_CLOSE terminal-transition gap. 181-S is a LOCAL DISPOSITION, not a resolution of the underlying defect: it re-derives the four externally-measured backlogit refusal behaviours as hermetic in-workspace fixtures to replace P-005-tainted indicative evidence, generates a portable upstream report and records the decided escalation route, documents an operator-only approval-gated interim close procedure that no agent may execute, corrects every in-repository claim that split multi-shipment delivery is operationally complete while INV-11 remains blocked, and establishes a durable active external-dependency tracker so the underlying gap cannot read as resolved when this local work closes. The fixtures are version-aware: CI pins backlogit v1.9.0 while the local binary is a dirty 1.10.1 build, and no behaviour is asserted against a binary it was not observed on."
doc_type: plan
source: docs/plans/2026-09-17-safe-close-record-transition-disposition-plan.md
date: 2026-09-17
status: reviewed
revision: 4
revision_note: "Revision 4 (remediation cycle 2) adopts decision revision 3 and closes the propagation findings from local review cycle 2. The revision-3 design was correct but was not encoded into the executable backlog records: the v1.9.0 baseline task existed without being a predecessor of anything, so a fixture could have been executed first and pinned its assertions to the local dirty 1.10.1 build; and the tracker back-pointer tasks referenced the tracker by the plan-relative label `T8` rather than by a resolvable backlog ID. Revision 4 requires the baseline task to block all four hermetic fixtures, the portable upstream report and the version-aware fixture contract; requires the documentation-truth audit and the tracker regression to reference chore `002-C` and task `173.010-T` by exact resolvable ID; and states the task count precisely as TEN feature tasks plus ONE external tracker that is deliberately neither a child of the covering feature nor a shipment member. Revision 4 also records that the tracker linkage is a `relates_to` edge and NOT a `blocks` edge: the tracker is designed never to close during this portfolio, so a blocking edge would make the shipment permanently unclosable and would, for the regression, demand the very terminal state it exists to forbid. The bounded audit trail lives in `review_history`."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 7F9CB5E9
stash_ids:
  - 7F9CB5E9
deferred_scope_expansions:
  - 7F9CB5E9
predecessor_stash_id: 2B42392E
prior_learnings:
  - docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md
  - docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md
  - docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md
  - docs/compound/2026-08-01-shipment-record-status-integrity.md
linked_review: docs/reviews/2026-09-17-safe-close-record-transition-disposition-plan-review.md
review_history:
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-04.md
review_history_note: "Attempts 01-02 were authored as one mutable file covering two cycles; it is preserved verbatim and classified rather than retroactively split into records that were never independently authored. Attempt 03 is a conforming single-attempt immutable artifact. Attempt 04 records local review cycle 2 (BLOCKED at revision 3, on non-propagation of the design into the executable backlog records) and the Stage remediation response that produced this revision."
latest_review_attempt: 3
latest_review_artifact: docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-04.md
latest_review_verdict: PASS
covering_feature: 173-F
shipment: 181-S
shipment_disposition_class: local-disposition
underlying_defect_status: unresolved-external
requires_plan_hardening: "yes"
plan_hardening_status: complete
plan_hardening_section: "## Plan Hardening Record (P-006)"
source_refs:
  originating_prs: [450, 451]
  originating_review_thread: "N/A (threadless — discovered during Ship post-merge closure)"
  originating_feature_id: 166-F
  originating_shipment_id: 174-S
  originating_task_id: 166.005-T
tags:
  - "shipment-closure"
  - "upstream-dependency"
  - "evidence-provenance"
  - "p-005"
  - "documentation-truth"
---

# SAFE_CLOSE record-transition gap — autoharness disposition

## Why this entry is retained

The operator imported this entry specifically to make operational
multi-shipment delivery resolvable, and explicitly directed that it not be
discarded merely because part of the fix is upstream. Decision **D7** upholds
that: the remedy is external, but three autoharness-owned obligations are real
and are delivered here.

This plan does **not** claim to fix the gap. It makes the gap honestly
evidenced, properly escalated, safely worked around by an operator, truthfully
documented, and — new in revision 3 — **durably tracked as an open external
dependency that survives this shipment's own closure.**

## Disposition class (binding)

**`181-S` is a LOCAL DISPOSITION. It is not a resolution of `7F9CB5E9`.**

This distinction is normative, not editorial, and it governs how every
downstream record must read:

| | |
|---|---|
| What `181-S` closes | The four autoharness-owned obligations: hermetic evidence, escalation report and route, operator-only interim procedure, documentation truth |
| What `181-S` does **not** close | The SAFE_CLOSE record-transition gap itself, which is external to this repository |
| Status of the underlying defect when `181-S` ships | **Still unresolved.** `underlying_defect_status: unresolved-external` |
| Status of `INV-11` when `181-S` ships | **Still blocked** |

Shipping every task in `173-F` and archiving `181-S` produces a workspace in
which all local work is done and the defect is exactly as unfixed as it was
before. Any record — backlog entry, closure artifact, memory file, PR
description, or compound entry — that describes `181-S` as fixing, closing, or
resolving `7F9CB5E9` or `INV-11` is **wrong**, and correcting such statements
is T7's explicit scope.

### Durable external-dependency tracker (Part E)

The structural hazard is that `7F9CB5E9`'s stash entry is consumed and archived
by this staging session, `181-S` ships, `173-F` closes — and nothing left
active in the workspace still says the gap is open. The entry that used to
carry it is in `.backlogit/archive/stash.jsonl`, which is history, not a live
signal. The defect would then be invisible until someone re-encounters it.

**Therefore a durable tracker is a deliverable of this plan (T8), and it
outlives `181-S` by construction:**

* A **separate, active backlog item** of type chore, `status: queued`, titled
  for the external dependency, **not** a member of `181-S`'s manifest and not
  parented to `173-F`. It cannot be closed by `181-S` shipping because it is
  not in it.
* It carries the upstream reference (issue/PR URL once filed), the four
  measured refusal behaviours by reference to the T1–T4 fixtures, the
  `INV-11` back-pointer, and the binary version the observations hold for.
* Its **closure condition is stated on the item itself**: a released backlogit
  version providing a non-cascading transition to
  `archived_status: shipped`, verified by the T1–T4 fixtures re-run against
  that version and flipping from "refusal observed" to "capability present".
  Nothing else closes it — not the upstream issue being filed, not `181-S`
  archiving, not the interim procedure being documented.
* **`INV-11` points at the tracker, not at `181-S`.** T7's back-pointer
  targets the durable item, so a reader arriving from the invariant reaches a
  live record rather than a shipped one.
* A regression assertion (T9) fails if the tracker item is absent or has
  reached a terminal state while the fixtures still observe the refusals. This
  makes premature closure a test failure rather than a silent drift.

**External (backlogit, Go binary, third-party dependency).** The capability to
transition a shipment record to `status: archived` + `archived_status: shipped`
**without** invoking the cascading `ShipShipment` operation. This cannot be
implemented in this repository (P-021 C1).

**Already delivered, not re-delivered here.** The fail-closed halt
`RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` with its explicit no-substitution
prohibition, shipped by `166.005-T`.

**Autoharness-owned and delivered by this plan.** Evidence re-derivation,
escalation route and portable report, operator-only interim procedure, and
documentation truth.

## Problem

The four behaviours below were measured against backlogit
`1.10.1-0.20260823032255-b07729386a31+dirty`, the binary installed on the
authoring workstation:

1. `backlogit move <S> --status shipped` → refused, exit 9, "shipment must be
   shipped via ShipShipment, not a direct status update".
2. `backlogit update <S> --status shipped` → refused identically, exit 9.
3. `backlogit archive <S>` on an active shipment → stamps
   `archived_status: active`, failing the shipment-reconcile Step 8 provenance
   gate (`RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE`).
4. `backlogit shipment ship <S>` → the only mechanism producing
   `archived_status: shipped`, and it has no `--no-cascade` flag.

### Binary-version divergence (binding constraint)

**The binary those measurements came from is not the binary CI runs.**

| Context | backlogit binary | Provenance |
|---|---|---|
| Authoring workstation | `1.10.1-0.20260823032255-b07729386a31+dirty` | Local build; `+dirty` means uncommitted upstream working-tree state, so it corresponds to **no released version** and is not reproducible |
| CI (`.github/workflows/ci.yml`) | **`v1.9.0`**, checksum-verified (`sha256 5bf29fda…87de`) | Pinned release download |

Asserting a `1.10.1+dirty` observation as a test expectation that CI evaluates
against `v1.9.0` is an unsound claim: it asserts one binary's behaviour against
a different binary. It would either pass by luck, or fail in CI for a reason
unrelated to the defect, and in neither case would it be evidence.

**Reconciliation, binding on every fixture (T1–T4):**

* **Fixtures are version-aware, not version-blind.** Each fixture reads the
  installed binary's version at run time (`backlogit --version` /
  `backlogit_get_version`) and records it in the assertion output.
* **The authoritative observation baseline is `v1.9.0`** — the version CI runs
  and the only pinned, reproducible, checksum-verified binary in the
  contract. T0 (new) re-derives all four behaviours against `v1.9.0`
  specifically, and *those* observations are what T1–T4 assert.
* **The `1.10.1+dirty` measurements are retained as corroborating evidence
  only**, explicitly labelled as such, and no fixture asserts them. A `+dirty`
  build is by definition unreproducible; it can corroborate, never pin.
* **Divergence is a signal, not a failure.** If a behaviour observed on
  `v1.9.0` differs from the `1.10.1+dirty` corroboration, the fixture records
  the divergence and the upstream report (T5) carries both observations. A
  behaviour that changed between the two is precisely the kind of fact the
  upstream maintainers need.
* **Version drift fails loudly.** If the installed binary is neither `v1.9.0`
  nor a version the fixture declares it has been re-observed against, the
  fixture **fails with an explicit version-mismatch message** rather than
  skipping or assuming. A silent skip here would delete the entire evidentiary
  value of the release unit.
* **The pin itself is in scope.** T10 (new) records the version contract — the
  pinned CI version, the observation baseline, and the re-observation
  obligation when the pin moves — in `docs/`, so a future pin bump is a
  known, checklisted action rather than a silent invalidation of every fixture.

Substituting the cascade on a non-cascade-eligible manifest is **prohibited**:
the engine returns live out-of-manifest siblings and silently clears their
`parent_id` (tracked separately as `63363CF5`, untouched and outside scope).

**Blocking relationship.** This blocks `INV-11` of
`docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md` —
operational multi-shipment feature delivery. `INV-4`/`INV-5` make split
delivery *contract-complete* (an ordered sequence `S1..Sn`, feature item last in
`Sn`), but every intermediate shipment `S1..Sn-1` carries no feature member,
therefore can never qualify for CASCADE, therefore is a genuine SAFE_CLOSE
shipment, therefore hits this exact refusal.

## Evidence provenance defect (P-005) — the first deliverable

The four measurements originate from Stage spike arms run in **external
`%TEMP%` workspaces**, which is a P-005 containment and destructive-approval
violation. That evidence is therefore **indicative, not authoritative**, and no
remedy may be accepted on it.

Re-derivation is hermetic and in-workspace: checked-in fixtures under `tests/`
that exercise each refusal against the pinned backlogit binary, with the
observed version recorded in the fixture so a version change is a test signal
rather than a silent drift. No external workspace is created. No shipment
record in this repository is mutated by any fixture.

This plan's own spike discipline is the corrected pattern: the companion spike
for `3EF5AAF2` was run read-only and in-workspace for exactly this reason.

## Design

### Part A — hermetic evidence (blocks everything else)

Four fixtures, one per measured behaviour, each asserting the exact exit code
and the exact refusal message, each recording the observed backlogit version.
The fixtures operate on disposable in-`tests/` records, never on live workspace
shipments.

### Part B — escalation route and portable report

Decided route (**D7**): **file an upstream issue/PR against
`softwaresalt/backlogit`** requesting a genuine non-cascading transition to
`archived_status: shipped` — for example `shipment ship --no-cascade`, or a
permitted direct terminal status update guarded by manifest-scope verification.

Rejected and recorded: vendoring a wrapper (would reimplement archive semantics
the engine owns) and pin-and-patch (forks a binary dependency this workspace
already consumes at a moving version).

The portable report is generated **from the Part A fixtures**, so what is filed
upstream is hermetic evidence rather than the tainted measurements. The same
escalation channel is reused where it overlaps `63363CF5`; `63363CF5` itself
remains untouched.

**Filing the upstream issue is an operator action.** This plan produces the
report; it does not authorize an agent to open it.

### Part C — operator-only interim procedure

Document an approval-gated administrative-close procedure, modelled on the
explicitly authorized, Ship-verified operator close of `173-S` on 2026-09-16.

Binding constraints:

* It is **operator-only**. No agent may execute it, propose executing it, or
  treat its existence as authorization.
* It does **not** weaken `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`. The halt
  still fires; the procedure is what an operator may do *after* the halt, with
  explicit approval.
* It requires manifest-scope verification before any record mutation, and it
  records the verification as closure evidence.
* Every invocation is logged as a P-005 telemetry event, because an
  administrative close is a deviation from the normal path even when authorized.

### Part D — documentation truth

Audit every in-repository statement about split multi-shipment delivery and
correct any that describes it as operationally complete or end-to-end supported
while `INV-11` is blocked. Add a durable pointer from the `INV-11` text to this
entry so the blocked status is discoverable from the invariant itself.

## Work Breakdown

| # | Task | Scope | Blocked by |
|---|---|---|---|
| T0 | Establish the `v1.9.0` observation baseline: install the pinned checksum-verified binary and re-derive all four behaviours against it, recording any divergence from the `1.10.1+dirty` corroboration | `tests/` + `docs/` | — |
| T1 | Hermetic fixture: `move --status shipped` refusal, exit 9, exact message, version-aware | `tests/` | T0 |
| T2 | Hermetic fixture: `update --status shipped` refusal, exit 9, exact message, version-aware | `tests/` | T0 |
| T3 | Hermetic fixture: `archive` on active stamps `archived_status: active` and fails the Step 8 provenance gate, version-aware | `tests/` | T0 |
| T4 | Hermetic fixture: `shipment ship` is the sole `archived_status: shipped` producer and exposes no `--no-cascade`, version-aware | `tests/` | T0 |
| T5 | Generate the portable upstream report from T0–T4 and record the decided escalation route, carrying both observation sets | `docs/` | T1, T2, T3, T4 |
| T6 | Document the operator-only approval-gated interim close procedure with its four binding constraints | `docs/` | T1, T2, T3, T4 |
| T7 | Documentation-truth audit; `INV-11` back-pointer targeting the **durable tracker** chore `002-C`, not `181-S` | `docs/` | T8 |
| T8 | Create the durable external-dependency tracker item — chore **`002-C`** — with its stated closure condition, outside `181-S`'s manifest and not parented to `173-F` | backlog data + `docs/` | T1, T2, T3, T4 |
| T9 | Regression assertion: the tracker `002-C` exists and is non-terminal while the fixtures still observe the refusals | `tests/` | T8 |
| T10 | Record the backlogit version contract: pinned CI version, observation baseline, and the re-observation obligation when the pin moves | `docs/` | T0 |

**Task count (revision 4, stated precisely).** This feature carries **TEN
feature tasks** — T0–T7 and T9–T10, harvested as `173.001-T` … `173.010-T` —
**plus ONE external tracker**, chore `002-C`, which is deliberately neither a
child of the covering feature nor a member of `181-S`. The plan-relative label
`T8` names that external tracker, not an eleventh feature task. Revision 3
stated the count ambiguously and referenced the tracker only by the
plan-relative label `T8`; revision 4 requires every record that references it
to use the **exact resolvable backlog ID `002-C`**, and requires the
documentation-truth audit and the tracker regression — harvested as
`173.007-T` and `173.010-T` respectively — to name `002-C` and `173.010-T` by
exact ID rather than by plan-relative label.

**T0 is a hard predecessor (revision 4).** Revision 3 defined the `v1.9.0`
baseline task but left it unwired, so a fixture could have been executed first
and pinned its assertions to the local dirty `1.10.1` build. T0 now blocks all
four hermetic fixtures (T1–T4), the portable upstream report (T5), and the
version-aware fixture contract (T10) as machine-encoded `blocks` edges.

**Tracker linkage is `relates_to`, NOT `blocks` (revision 4).** `002-C`'s only
closure condition is an upstream backlogit release, so it is designed never to
close during this portfolio. A `blocks` edge from `173.007-T` or `173.010-T`
onto it would make both tasks permanently unstartable and `181-S` permanently
unclosable — reintroducing the exact partial-closure deadlock this remediation
exists to remove. For `173.010-T` it would additionally be self-contradictory:
that regression asserts the tracker **remains open**, so blocking on its
closure would demand the very terminal state the assertion forbids. Both edges
are therefore `relates_to` reference edges.

T5, T6, T7, and T8 all block on T1–T4: nothing may be filed, documented,
corrected, or tracked on indicative evidence. T7 additionally references `002-C`
because its `INV-11` back-pointer must resolve to a tracker that already
exists — as a `relates_to` edge, per the paragraph above.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* All four fixtures pass against the **pinned `v1.9.0`** binary and record its
  version in the assertion output.
* A fixture run against an undeclared binary version fails with an explicit
  version-mismatch message; it never skips and never assumes.
* No live shipment record in `.backlogit/` is mutated by any fixture.
* No external `%TEMP%` workspace is created at any point.
* `autoharness gate check` passes on every modified file.
* A repository-wide search finds no remaining claim that split delivery is
  operationally complete, and none that `181-S` resolves `7F9CB5E9` or
  `INV-11`.
* The durable tracker item exists, is `queued`, is **not** a member of
  `181-S`, and is not parented to `173-F`.
* `INV-11`'s back-pointer resolves to the tracker, not to `181-S`.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | The interim procedure is read as an agent-executable path | Operator-only is stated in the procedure title, its first paragraph, and its telemetry requirement; T6's acceptance criteria include a negative assertion that no agent template references it as executable |
| R2 | Fixtures mutate live workspace records | Fixtures operate on disposable in-`tests/` records only; Verification asserts `.backlogit/` is unmodified |
| R3 | Upstream never lands and the entry stays open indefinitely | This plan's deliverables are complete without the upstream fix; T8's durable tracker is what keeps the open state visible after `181-S` archives |
| R4 | Re-derivation is attempted in `%TEMP%` again for speed | Explicitly prohibited in Verification and Out of scope; this is the exact P-005 violation being corrected |
| R5 | The cascade is substituted on a non-eligible manifest to "just close it" | Already prohibited by `166.005-T`'s no-substitution clause, which this plan does not weaken |
| R6 | `181-S` shipping is read as resolving the defect | Disposition class is normative frontmatter (`shipment_disposition_class: local-disposition`, `underlying_defect_status: unresolved-external`) and a dedicated plan section; T7 audits for the mis-statement; T9 fails if the tracker closes prematurely |
| R7 | Fixture expectations are asserted against a binary they were not observed on | T0 establishes `v1.9.0` as the authoritative baseline; `+dirty` observations are corroboration only and are never asserted; version mismatch fails loudly |
| R8 | The CI pin moves and silently invalidates every fixture | T10 records the version contract and the re-observation obligation; the version-aware fixtures fail on an undeclared version rather than passing against it |

## Out of scope

* Implementing the record transition. It is external.
* Any change to `166.005-T`'s halt or its no-substitution prohibition.
* Stash `63363CF5` (sibling `parent_id` clearing) — shares the escalation
  channel only; the entry itself is untouched.
* Archived predecessor `2B42392E`, whose append-only record is **not**
  rewritten; traceability runs forward from `7F9CB5E9` to it.
* `3CA122AC` (classifier/protected-set class) — confirmed distinct, active,
  unmerged, untouched.
* Any agent-executable administrative close.

## Plan Hardening Record (P-006)

Hardening applied 2026-09-17, re-run 2026-09-18 during remediation cycle 1.
Revision 2 declared `plan_hardening_status: complete` without persisting this
record; that gap is H0 below.

**Hardening trigger.** Elevated risk on three distinct axes: the plan documents
an **operator-only administrative-close procedure** that mutates terminal
shipment state and could be mis-read as agent-executable; its evidence base was
a recorded **P-005 containment violation** being remediated; and it depends on
an **external binary dependency at a moving, partly unreproducible version**.

**Protected invariants.**

* `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` and its no-substitution
  prohibition (shipped by `166.005-T`) are never weakened, bypassed, or
  conditioned.
* No agent may execute, propose, or cite the interim close procedure as
  authorization.
* No fixture creates an external `%TEMP%` workspace or mutates any live
  `.backlogit/` record.
* `181-S` never reads as resolving `7F9CB5E9` or unblocking `INV-11`.
* The cascade is never substituted on a non-cascade-eligible manifest.

**Instructions and learnings consulted.**
`docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md`,
`docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md`,
`docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md`,
`docs/compound/2026-08-01-shipment-record-status-integrity.md`,
`docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md`,
`.github/policies/workflow-policies.md` (P-005, P-021),
`docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md`
(INV-4, INV-5, INV-11), and `.github/workflows/ci.yml` (the v1.9.0 pin).

| # | Hardening finding | Resolution |
|---|---|---|
| H0 | Revision 2 asserted `plan_hardening_status: complete` with no persisted hardening record | This section is the record; `plan_hardening_section` in frontmatter names it |
| H1 | Once the local deliverables ship and `181-S` archives, no active artifact would still assert the external gap is open — the consumed stash entry is in archive history, not a live signal | T8 delivers a durable tracker item outside `181-S`'s manifest and outside `173-F`'s parentage, with its closure condition stated on the item; T9 fails if it closes prematurely |
| H2 | `181-S` was not distinguished from resolution of the underlying defect anywhere machine-readable | `shipment_disposition_class: local-disposition` and `underlying_defect_status: unresolved-external` added to frontmatter; a normative Disposition class section added; T7 audits for mis-statements |
| H3 | Fixture expectations derived from a `+dirty` local 1.10.1 build would have been evaluated by CI against a checksum-pinned v1.9.0 — asserting one binary's behaviour against another | T0 establishes v1.9.0 as the authoritative observation baseline; `+dirty` observations demoted to labelled corroboration; T10 records the version contract |
| H4 | A version-mismatch fixture could have degraded to a skip, silently deleting the release unit's entire evidentiary value | Version mismatch **fails loudly** with an explicit message; skipping is prohibited in Verification |
| H5 | `INV-11`'s back-pointer targeted `181-S`, so a reader arriving from the invariant would land on a shipped record and infer resolution | T7's back-pointer retargeted to the durable tracker; T7 blocks on T8 so the target exists first |
| H6 | The interim procedure is the highest-risk artifact in the unit — it describes a terminal-state mutation | Operator-only stated in title, first paragraph, and telemetry requirement; T6 carries a negative assertion that no agent template references it as executable; classified High-risk below |
| H7 | Re-derivation could regress to `%TEMP%` for convenience, repeating the P-005 violation being corrected | Prohibited in Verification and Out of scope; fixtures operate on disposable in-`tests/` records only |
| H8 | A future CI pin bump would silently invalidate every fixture observation | T10 records the re-observation obligation as a checklisted action tied to the pin |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Document the operator-only administrative-close procedure (T6) | **High** — describes a terminal shipment-state mutation; mis-reading it as agent-executable would be a P-001/P-005 violation | Operator review required before merge | Remove the document; it is descriptive only and grants no capability |
| Re-derive refusal behaviours against a real binary (T0–T4) | Medium — executes backlogit commands | Standard PR review; hermetic in-`tests/` records only | Delete fixtures; no live state touched |
| Create the durable tracker backlog item (T8) | Low — additive backlog record outside every manifest | Standard PR review | Archive the item |
| Generate and file the upstream report (T5) | Low locally; **filing is an operator action** | Plan produces the report; it does **not** authorize an agent to open the issue | Do not file |
| Correct in-repository completeness claims (T7) | Low — documentation truth | Standard PR review | Revert |

**Rollback coupling.** T0–T4 are test-only. T5/T6/T7/T10 are docs-only. T8 is
the only task creating persisted backlog state and is reversible by archiving.
No task mutates a shipment record, a closure artifact, or any live manifest.

**Monitoring and validation window.** The fixtures are the monitor: they run on
every CI invocation and flip from "refusal observed" to a failure the moment
upstream behaviour changes. That flip is the signal to close the T8 tracker —
and the only thing that closes it.

**Operator checkpoints.** Two. (1) Review and approval of T6's interim
procedure before merge. (2) Filing the T5 upstream report, which is explicitly
an operator action and is never agent-initiated.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers and MUST apply the Constitution
Reviewer persona inline, because the unit's highest-risk artifact is a
documented deviation from a fail-closed policy path.

**Unresolved operator decisions blocking safe execution.** None blocking
execution. One standing operator decision remains open **outside** this unit:
whether and when to file the upstream issue.
