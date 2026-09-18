---
title: "SAFE_CLOSE record-transition gap: in-workspace evidence, upstream escalation, and an operator-only interim close"
description: "Implementation plan for the autoharness-owned half of the SAFE_CLOSE terminal-transition gap. 181-S is a LOCAL DISPOSITION, not a resolution of the underlying defect: it re-derives the four externally-measured backlogit refusal behaviours as hermetic in-workspace fixtures to replace P-005-tainted indicative evidence, generates a portable upstream report and records the decided escalation route, documents an operator-only approval-gated interim close procedure that no agent may execute, and corrects every in-repository claim that split multi-shipment delivery is operationally complete while INV-11 remains blocked. The durable external-dependency tracker chore 002-C is PRE-CREATED BY STAGE at publication time rather than produced during Ship execution, is held blocked on a purely external condition, and is referenced by non-blocking related_to links so the underlying gap cannot read as resolved when this local work closes. The fixtures are version-aware: CI pins backlogit v1.9.0 while the local binary is a dirty 1.10.1 build, and no behaviour is asserted against a binary it was not observed on."
doc_type: plan
source: docs/plans/2026-09-17-safe-close-record-transition-disposition-plan.md
date: 2026-09-17
status: reviewed
plan_id: safe-close-record-transition-disposition
plan_role: active
revision: 7
supersedes: null
superseded_by: null
source_history:
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-05.md
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-06.md
  - docs/reviews/review-history/2026-09-17-safe-close-record-transition-disposition-plan-review-attempt-06-supplement.md
  - docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md
review_manifest: docs/reviews/2026-09-17-safe-close-record-transition-disposition-plan-review.md
revision_note: "Revision 7 is maintained as one coherent current-state contract rather than as an accreting record of corrections. Prior-revision deltas, superseded requirement variants, and reviewer chronology are not carried in the body: the immutable per-attempt review artifacts listed in source_history and the mutable verdict manifest named by review_manifest are the authoritative record of that chronology. Latest attempt and verdict are read from the manifest, never from this file."
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
that: the remedy is external, but four autoharness-owned obligations are real
and are delivered here.

This plan does **not** claim to fix the gap. It makes the gap honestly
evidenced, properly escalated, safely worked around by an operator, truthfully
documented, and **durably tracked by a record that already exists and that
survives this shipment's own closure.**

## Disposition class (binding)

**`181-S` is a LOCAL DISPOSITION. It is not a resolution of `7F9CB5E9`.**

This distinction is normative, not editorial, and it governs how every
downstream record must read:

| | |
|---|---|
| What `181-S` closes | The autoharness-owned obligations: hermetic evidence, escalation report and route, operator-only interim procedure, and documentation truth |
| What `181-S` does **not** close | The SAFE_CLOSE record-transition gap itself, which is external to this repository; and the durable tracker `002-C`, which is outside its manifest entirely |
| Status of the underlying defect when `181-S` ships | **Still unresolved.** `underlying_defect_status: unresolved-external` |
| Status of `INV-11` when `181-S` ships | **Still blocked** |

Shipping every task in `173-F` and archiving `181-S` produces a workspace in
which all local work is done and the defect is exactly as unfixed as it was
before. Any record — backlog entry, closure artifact, memory file, PR
description, or compound entry — that describes `181-S` as fixing, closing, or
resolving `7F9CB5E9` or `INV-11` is **wrong**, and correcting such statements
is T7's explicit scope.

### Ownership split

**External (backlogit, Go binary, third-party dependency).** The capability to
transition a shipment record to `status: archived` + `archived_status: shipped`
**without** invoking the cascading `ShipShipment` operation. This cannot be
implemented in this repository (P-021 C1).

**Already delivered, not re-delivered here.** The fail-closed halt
`RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` with its explicit no-substitution
prohibition, shipped by `166.005-T`.

**Autoharness-owned and delivered by this plan.** Evidence re-derivation
(Part A), escalation route and portable report (Part B), operator-only interim
procedure (Part C), and documentation truth (Part D).

**Autoharness-owned and already in place before execution.** The durable
external-dependency tracker chore `002-C` (Part E). It is a Stage
publication-time record, not a Ship deliverable, and it is not created by any
task in `173-F`.

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
  contract. T0 re-derives all four behaviours against `v1.9.0` specifically,
  and *those* observations are what T1–T4 assert.
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
* **The pin itself is in scope.** T10 records the version contract — the
  pinned CI version, the observation baseline, and the re-observation
  obligation when the pin moves — in `docs/`, so a future pin bump is a
  known, checklisted action rather than a silent invalidation of every fixture.

### Part A0 — acquiring the pinned binary is an ELEVATED, APPROVAL-GATED action

`T0` re-derives the baseline against `v1.9.0`, and the authoring workstation
does **not** have `v1.9.0` installed — it has an unreproducible
`1.10.1+dirty` local build. T0 therefore has to **acquire and install a
different backlogit binary**, which is an elevated and potentially destructive
action: the tool being replaced is the one that owns every backlog record in
this workspace, and a wrong install can leave the workspace unable to read its
own queue. Treating that as ordinary test setup is the defect this section
closes. **Ordinary PR review does not satisfy this gate**, and nothing in this
plan may be read as claiming it does: PR review approves a *merged diff*, while
this action mutates the *executing machine* before any diff exists.

The following are **binding preconditions on T0**, each of which must hold
before a single byte is written:

1. **Explicit operator approval, obtained in-session, for the specific
   action.** The approval must name the version being installed and the fact
   that a binary is being placed or replaced. A standing authorization, an
   autopilot directive, or an approved pull request is **not** sufficient and
   may not be cited as sufficient.
2. **Workspace-contained installation.** The binary is installed **into a
   path inside this repository's working tree** (a git-ignored tool directory)
   and invoked by explicit path. It **must not** replace, shadow, or modify any
   machine-global, user-global, or `PATH`-resolved backlogit installation, and
   it must not write outside the working tree. No `%TEMP%` workspace is created
   — that is the P-005 violation this whole plan exists to correct.
3. **Checksum verification before use.** The downloaded artifact's SHA-256 is
   verified against the value pinned in `.github/workflows/ci.yml`
   (`sha256 5bf29fda…87de`) **before** the binary is made executable or
   invoked. A mismatch **halts**; it is never retried past, never warned
   through, and never resolved by re-downloading.
4. **Bounded execution mode — `careful` or `investigate-first`.** T0 runs in a
   bounded mode with an explicit step budget and an operator-visible log of
   every command issued. It does not run in an unattended or autopilot mode.
5. **No live backlog mutation, enforced by construction.** Every observation
   command runs against **disposable fixture records inside `tests/`**, never
   against `.backlogit/`. The pinned binary is never invoked with this
   workspace as its `--cwd`. A pre-flight assertion records the `.backlogit/`
   tree state and a post-flight assertion proves it unchanged.
6. **Rollback and restoration are defined before the action, not after.** The
   pre-existing binary's location and version are recorded first. Rollback is:
   delete the workspace-contained binary directory; no global state was
   touched, so nothing needs restoring outside the working tree. If the
   recorded pre-state cannot be captured, T0 **halts rather than proceeding**.
7. **Cleanup is part of the task, not a follow-up.** The workspace-contained
   binary directory is removed at the end of T0 unless the operator explicitly
   directs it be retained for T1–T4. If retained, it is git-ignored and named
   in the task's completion record so it cannot become undeclared state.

**If operator approval is withheld, T0 halts and reports.** It does not
silently fall back to asserting the `1.10.1+dirty` observations — that
substitution is exactly the unsound claim the binary-version divergence section
prohibits — and it does not degrade to a skip, which would delete the release
unit's evidentiary value. A halted T0 blocks `T1`–`T4` and `T10` by the
existing edges, which is the correct outcome: with no authoritative baseline
there is nothing sound for the fixtures to assert.



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
while `INV-11` is blocked. Add a durable pointer from the `INV-11` text to the
Part E tracker so the blocked status is discoverable from the invariant itself.

### Part E — durable external-dependency tracker (pre-created, not built here)

The structural hazard is that `7F9CB5E9`'s stash entry is consumed and archived
by this staging session, `181-S` ships, `173-F` closes — and nothing left
active in the workspace still says the gap is open. The entry that used to
carry it is in `.backlogit/archive/stash.jsonl`, which is history, not a live
signal. The defect would then be invisible until someone re-encounters it.

**The tracker therefore already exists.** Chore `002-C` was created by Stage at
the publication time of `173-F` and `181-S`, before any execution begins. The
plan-relative label **`T8` names that record itself**, not a task. Nothing in
this plan creates it, no task in `173-F` creates it, and it is never created
during Ship execution. Creating a record that a sibling task must already be
able to resolve is an ordering defect, and pre-creation removes it outright.

The tracker outlives `181-S` by construction:

* It is a **separate top-level backlog item** of type chore, **not** a member
  of `181-S`'s manifest and **not** parented to `173-F`. It cannot be closed by
  `181-S` shipping or by `173-F` closing, because it is in neither.
* Its status is **`blocked`**, which is the truthful encoding for a record
  whose only unblocking condition is external. `queued` would misrepresent it
  as ordinary work awaiting a turn.
* Its **unblocking condition is stated on the item itself, and it is the only
  one**: a released backlogit version providing a non-cascading transition to
  `archived_status: shipped`, **together with** an advance of this workspace's
  pinned CI backlogit version to that release, both performed in a **future,
  separate Stage cycle**. Nothing else unblocks it — not the upstream issue
  being filed, not `181-S` archiving, not the interim procedure being
  documented, and no action taken inside this portfolio.
* It carries the upstream reference (issue/PR URL once filed), the four
  measured refusal behaviours by reference to the T1–T4 fixtures, the
  `INV-11` back-pointer, and the binary version the observations hold for.
* **It carries no `blocks` dependency edges in either direction.** It is not
  blocked by the fixture tasks: the record already exists, so nothing can gate
  its creation, and an edge onto in-portfolio tasks would misrepresent a
  persistent external dependency as an ordinary local predecessor that `181-S`
  closure would satisfy. Nor does anything block on it.
* **`INV-11` points at the tracker, not at `181-S`.** T7's back-pointer
  targets the durable item, so a reader arriving from the invariant reaches a
  live record rather than a shipped one.
* A regression assertion (T9) fails if the tracker item is absent or has
  reached a terminal state while the fixtures still observe the refusals. This
  makes premature closure a test failure rather than a silent drift. T9
  asserts continued non-terminal state; it does not create the tracker.

## Work Breakdown

The ten rows below are the executable tasks of `173-F`, harvested as
`173.001-T` … `173.010-T`.

| # | Task | Scope | Blocked by |
|---|---|---|---|
| T0 | Establish the `v1.9.0` observation baseline. **Acquiring and installing the pinned checksum-verified binary is an ELEVATED, APPROVAL-GATED action** governed by Part A0: explicit in-session operator approval naming the version and the install/replacement, workspace-contained install invoked by explicit path (never replacing a global or `PATH`-resolved backlogit), SHA-256 verified against the CI pin **before** first invocation with a halt on mismatch, bounded `careful` / `investigate-first` execution, **no live `.backlogit/` mutation** (pre- and post-flight assertions), pre-recorded rollback, and cleanup inside the task. Then re-derive all four behaviours against `v1.9.0`, recording any divergence from the `1.10.1+dirty` corroboration. **Ordinary PR review does not satisfy this gate.** Approval withheld ⇒ **halt and report**, never a fallback to `+dirty` observations and never a skip | `tests/` + `docs/` | — |
| T1 | Hermetic fixture: `move --status shipped` refusal, exit 9, exact message, version-aware | `tests/` | T0 |
| T2 | Hermetic fixture: `update --status shipped` refusal, exit 9, exact message, version-aware | `tests/` | T0 |
| T3 | Hermetic fixture: `archive` on active stamps `archived_status: active` and fails the Step 8 provenance gate, version-aware | `tests/` | T0 |
| T4 | Hermetic fixture: `shipment ship` is the sole `archived_status: shipped` producer and exposes no `--no-cascade`, version-aware | `tests/` | T0 |
| T5 | Generate the portable upstream report from T0–T4 and record the decided escalation route, carrying both observation sets | `docs/` | T1, T2, T3, T4 |
| T6 | Document the operator-only approval-gated interim close procedure with its four binding constraints | `docs/` | T1, T2, T3, T4 |
| T7 | Documentation-truth audit; `INV-11` back-pointer targeting the **pre-existing tracker** chore `002-C`, not `181-S` | `docs/` | T1, T2, T3, T4 (`blocks`); `002-C` (`related_to` link, never a dependency edge) |
| T9 | Regression assertion: the tracker `002-C` exists and is non-terminal while the fixtures still observe the refusals | `tests/` | — (none); `002-C` (`related_to` link, never a dependency edge) |
| T10 | Record the backlogit version contract: pinned CI version, observation baseline, and the re-observation obligation when the pin moves | `docs/` | T0 |

### Plan-relative label `T8` — the pre-created tracker `002-C`

`T8` is deliberately absent from the table above because **it is not a task**.
It names the durable external-dependency tracker chore `002-C`, which Stage
created at publication time and which is `blocked` on the external condition in
Part E. It is not executed, not harvested, and not assigned. There is no
`173.011-T`, and **no task depends on `T8`**, because there is no `T8` task to
depend on.

### Dependency and linkage contract

**Task count, stated precisely.** This feature carries **TEN feature tasks** —
T0–T7 and T9–T10, harvested as `173.001-T` … `173.010-T` — **plus ONE
pre-existing external tracker**, chore `002-C`, which is deliberately neither a
child of the covering feature nor a member of `181-S`. Every record that
references it uses the **exact resolvable backlog ID `002-C`**; the
documentation-truth audit and the tracker regression — harvested as
`173.007-T` and `173.010-T` — name `002-C` and `173.010-T` by exact ID rather
than by plan-relative label.

**T0 is a hard predecessor.** T0, harvested as `173.008-T`, blocks all four
hermetic fixtures (T1–T4), the portable upstream report (T5), and the
version-aware fixture contract (T10) as machine-encoded `blocks` edges, so no
fixture can pin its assertions to the local dirty `1.10.1` build. T0 remains
the observation baseline and nothing else; its role is unchanged.

**Nothing may be filed, documented, or corrected on indicative evidence.** T5,
T6 and T7 all block on T1–T4.

**Tracker linkage is a non-blocking `related_to` link, never a dependency
edge.** `002-C`'s only unblocking condition is external and is satisfied in a
future separate Stage cycle, so it is designed never to reach a terminal state
during this portfolio. A dependency edge from `173.007-T` or `173.010-T` onto
it would make both tasks permanently unstartable and `181-S` permanently
unclosable — reintroducing the exact partial-closure deadlock this disposition
exists to remove. For `173.010-T` it would additionally be self-contradictory:
that regression asserts the tracker **remains non-terminal**, so blocking on
its closure would demand the very terminal state the assertion forbids. Both
tasks therefore carry `related_to` semantic links to `002-C`, which are
informational reference edges outside the execution DAG.

**No dependency edge touches `002-C` in either direction.** Not inbound from
`173.007-T` or `173.010-T`, and not outbound onto `173.001-T`…`173.004-T`. The
tracker's relationship to this portfolio is entirely informational; its
blocked state is owned by the external condition alone.

**Existence ordering is resolved by pre-creation, not by an edge.** T7's
`INV-11` back-pointer must resolve to `002-C`; because `002-C` is created by
Stage before execution starts, it resolves whenever T7 runs, and no ordering
edge is needed or permitted to guarantee it.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* All four fixtures pass against the **pinned `v1.9.0`** binary and record its
  version in the assertion output.
* A fixture run against an undeclared binary version fails with an explicit
  version-mismatch message; it never skips and never assumes.
* No live shipment record in `.backlogit/` is mutated by any fixture, and T0's
  pre-flight and post-flight assertions prove the `.backlogit/` tree is
  byte-identical across the baseline derivation.
* No external `%TEMP%` workspace is created at any point.
* T0's binary acquisition is recorded with: the operator approval (naming the
  version and the install/replacement), the verified SHA-256 matching the CI
  pin, the workspace-contained install path, the pre-existing binary's location
  and version, and the cleanup or explicitly-authorized retention of the
  installed binary. A checksum mismatch is asserted to **halt**, never to warn
  or retry. No artifact claims that PR review satisfies this gate.
* A withheld approval is asserted to produce a **halt and report**, never a
  fallback to the `1.10.1+dirty` observations and never a skip.
* `autoharness gate check` passes on every modified file.
* A repository-wide search finds no remaining claim that split delivery is
  operationally complete, and none that `181-S` resolves `7F9CB5E9` or
  `INV-11`.
* The durable tracker item `002-C` exists, is `blocked`, is **not** a member of
  `181-S`, and is not parented to `173-F`.
* `002-C` carries no dependency edges in either direction; `173.007-T` and
  `173.010-T` reference it only through `related_to` links.
* `INV-11`'s back-pointer resolves to `002-C`, not to `181-S`.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | The interim procedure is read as an agent-executable path | Operator-only is stated in the procedure title, its first paragraph, and its telemetry requirement; T6's acceptance criteria include a negative assertion that no agent template references it as executable |
| R2 | Fixtures mutate live workspace records | Fixtures operate on disposable in-`tests/` records only; Verification asserts `.backlogit/` is unmodified |
| R3 | Upstream never lands and the entry stays open indefinitely | This plan's deliverables are complete without the upstream fix; the pre-created `002-C` tracker is what keeps the blocked state visible after `181-S` archives |
| R4 | Re-derivation is attempted in `%TEMP%` again for speed | Explicitly prohibited in Verification and Out of scope; this is the exact P-005 violation being corrected |
| R5 | The cascade is substituted on a non-eligible manifest to "just close it" | Already prohibited by `166.005-T`'s no-substitution clause, which this plan does not weaken |
| R6 | `181-S` shipping is read as resolving the defect | Disposition class is normative frontmatter (`shipment_disposition_class: local-disposition`, `underlying_defect_status: unresolved-external`) and a dedicated plan section; T7 audits for the mis-statement; T9 fails if the tracker closes prematurely |
| R7 | Fixture expectations are asserted against a binary they were not observed on | T0 establishes `v1.9.0` as the authoritative baseline; `+dirty` observations are corroboration only and are never asserted; version mismatch fails loudly |
| R8 | The CI pin moves and silently invalidates every fixture | T10 records the version contract and the re-observation obligation; the version-aware fixtures fail on an undeclared version rather than passing against it |
| R9 | T0's binary acquisition is treated as ordinary test setup and performed unapproved, replacing the backlogit installation that owns this workspace's backlog | Part A0 makes it an elevated, approval-gated action with seven binding preconditions: in-session approval naming the version, workspace-contained install, pre-use checksum verification with a halt on mismatch, bounded `careful`/`investigate-first` mode, no live `.backlogit/` mutation with pre/post assertions, pre-recorded rollback, and in-task cleanup. Ordinary PR review is explicitly stated not to satisfy it |
| R10 | Approval is withheld and T0 quietly falls back to the `+dirty` observations or skips | Part A0 requires a halt and report; asserting a `+dirty` observation as a `v1.9.0` expectation is already prohibited by the binary-version divergence section, and a skip is prohibited by H4. The halt propagates through the existing T0 edges, which is the correct outcome |

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

| # | Hazard | Resolution in this contract |
|---|---|---|
| H1 | Once the local deliverables ship and `181-S` archives, no active artifact still asserts the external gap is open — the consumed stash entry is archive history, not a live signal | Part E's tracker `002-C` already exists, pre-created by Stage at publication time, `blocked` on its external condition, outside `181-S`'s manifest and outside `173-F`'s parentage; T9 fails if it reaches a terminal state |
| H2 | `181-S` is not distinguished from resolution of the underlying defect anywhere machine-readable | `shipment_disposition_class: local-disposition` and `underlying_defect_status: unresolved-external` in frontmatter; a normative Disposition class section; T7 audits for mis-statements |
| H3 | Fixture expectations derived from a `+dirty` local 1.10.1 build would be evaluated by CI against a checksum-pinned v1.9.0 — asserting one binary's behaviour against another | T0 establishes v1.9.0 as the authoritative observation baseline; `+dirty` observations are labelled corroboration; T10 records the version contract |
| H4 | A version-mismatch fixture that degrades to a skip silently deletes the release unit's entire evidentiary value | Version mismatch **fails loudly** with an explicit message; skipping is prohibited in Verification |
| H5 | An `INV-11` back-pointer targeting `181-S` lands a reader on a shipped record and invites the inference that the defect is resolved | T7's back-pointer targets the pre-created durable tracker `002-C`, which already exists when T7 runs; the linkage is a non-blocking `related_to` link, never a dependency edge, because `002-C` is designed never to close during this portfolio |
| H9 | A tracker created *during* execution would not exist when a sibling task's back-pointer must already resolve to it, and encoding that ordering as a dependency edge onto a never-closing record would deadlock the shipment | The tracker is pre-created by Stage at publication time; `T8` names the record rather than a task; no `173.011-T` exists and no task depends on a `T8` task |
| H6 | The interim procedure is the highest-risk artifact in the unit — it describes a terminal-state mutation | Operator-only stated in title, first paragraph, and telemetry requirement; T6 carries a negative assertion that no agent template references it as executable; classified High-risk below |
| H7 | Re-derivation could regress to `%TEMP%` for convenience, repeating the P-005 violation being corrected | Prohibited in Verification and Out of scope; fixtures operate on disposable in-`tests/` records only |
| H8 | A future CI pin bump would silently invalidate every fixture observation | T10 records the re-observation obligation as a checklisted action tied to the pin |
| H10 | T0 has to install a *different* backlogit binary than the one present, and the tool being replaced is the one that owns every backlog record in this workspace — a wrong install can leave the workspace unable to read its own queue, yet it reads as ordinary test setup | Part A0 classifies it **elevated and destructive** with seven binding preconditions and classifies it **High** in the risky-actions table. Install is workspace-contained and invoked by explicit path; no global or `PATH`-resolved installation is replaced, shadowed, or modified |
| H11 | "Standard PR review" would be cited as the approval for a machine-mutating action | Part A0 states explicitly that ordinary PR review does **not** satisfy the gate, because PR review approves a merged diff while this action mutates the executing machine before any diff exists. Explicit in-session operator approval naming the version is required, and a standing authorization or autopilot directive is expressly insufficient |
| H12 | A checksum mismatch is warned through or retried, defeating the only integrity control on a downloaded executable | Verification asserts the mismatch path **halts**; it is never retried past, never warned through, and never resolved by re-downloading |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Document the operator-only administrative-close procedure (T6) | **High** — describes a terminal shipment-state mutation; mis-reading it as agent-executable would be a P-001/P-005 violation | Operator review required before merge | Remove the document; it is descriptive only and grants no capability |
| Acquire and install the pinned `v1.9.0` backlogit binary (**T0**, Part A0) | **High** — installs or replaces the tool that owns every backlog record in this workspace; a wrong install can leave the workspace unable to read its own queue | **Explicit in-session operator approval naming the version and the install/replacement. Ordinary PR review does NOT satisfy this gate, and a standing authorization or autopilot directive is expressly insufficient.** SHA-256 verified against the CI pin before first invocation (mismatch ⇒ halt). Bounded `careful` / `investigate-first` mode with an operator-visible command log | Delete the workspace-contained, git-ignored binary directory. No global or `PATH`-resolved installation is touched, so nothing outside the working tree needs restoring. Pre-existing binary location and version are recorded **before** the action; if they cannot be captured, T0 halts instead of proceeding. Cleanup runs inside T0 unless retention is explicitly authorized |
| Re-derive refusal behaviours against the installed binary (T0 observation phase, T1–T4) | Medium — executes backlogit commands | Standard PR review; hermetic in-`tests/` records only; the pinned binary is never invoked with this workspace as its `--cwd`, and pre/post-flight assertions prove `.backlogit/` unchanged | Delete fixtures; no live state touched |
| Create the durable tracker backlog item `002-C` (plan label `T8`) | Low — additive backlog record outside every manifest | **Already performed by Stage at publication time under explicit operator authorization**; not a Ship action and not agent-executable during execution | Archive the item |
| Generate and file the upstream report (T5) | Low locally; **filing is an operator action** | Plan produces the report; it does **not** authorize an agent to open the issue | Do not file |
| Correct in-repository completeness claims (T7) | Low — documentation truth | Standard PR review | Revert |

**Rollback coupling.** T0's binary acquisition is reversed by deleting the
workspace-contained, git-ignored binary directory; no global state was
modified. T0's observation output, T1–T4 and T9 are otherwise test-only.
T5/T6/T7/T10 are docs-only.
**No task in this plan creates or mutates persisted backlog state**: the only
such record, tracker `002-C`, was created by Stage before execution and is
reversible by archiving it. No task mutates a shipment record, a closure
artifact, or any live manifest.

**Monitoring and validation window.** The fixtures are the monitor: they run on
every CI invocation and flip from "refusal observed" to a failure the moment
upstream behaviour changes. That flip is the signal that the upstream half of
`002-C`'s unblocking condition may be met; unblocking the tracker still
requires advancing this workspace's CI version pin, and both are performed in a
future separate Stage cycle. Nothing in this portfolio unblocks it.

**Operator checkpoints.** Three. (1) **Explicit in-session approval of T0's
binary acquisition and install before it is performed** — the version, the
install/replacement, and the workspace-contained path are named in the request;
withheld approval halts T0 and, through its edges, T1–T4 and T10. (2) Review
and approval of T6's interim procedure before merge. (3) Filing the T5 upstream
report, which is explicitly an operator action and is never agent-initiated.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers and MUST apply the Constitution
Reviewer persona inline, because the unit's highest-risk artifact is a
documented deviation from a fail-closed policy path.

**Unresolved operator decisions blocking safe execution.** None blocking
execution. One standing operator decision remains open **outside** this unit:
whether and when to file the upstream issue.
