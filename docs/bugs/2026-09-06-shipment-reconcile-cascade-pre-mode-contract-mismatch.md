---
title: "shipment-reconcile Pre-Mode contradicts the P-015 CASCADE close contract, making every cascade-eligible closure an inevitable HALT"
description: "Pre-Mode compares every manifest member to a single scalar expected_status (done at closure), but a CASCADE-eligible manifest must contain its qualifying root feature, which is validly active until the cascade itself archives it — so the gate can never be satisfied and closure authorization becomes ambiguous"
status: "decided — fix authorized 2026-09-07 (Option A); implementation not started"
severity: "high"
priority: "high"
kind: "bug"
date: 2026-09-06
decided_date: 2026-09-07
authorization_disposition: "159-S close recorded as an accepted-with-remediation P-005 deviation (operator, 2026-09-07); this bug's fix is the named remediation"
discovered_in: "159-S / 151-F post-merge closure (PR #436)"
stash_entry: "15A02E21"
producer: ".github/skills/shipment-reconcile/SKILL.md — Required Protocol / Pre-Mode step 3 and step 7"
consumer: ".github/skills/shipment-reconcile/SKILL.md — Safe-Close Mode Step 0(c) and the Cascade Close Sub-Procedure step 3"
classifier: "src/autoharness/gates/shipment_closure.py — classify_shipment_close_path"
gate_token: "RECONCILE_FAIL / HALT — operator reconcile required"
governing_policies: ["P-015", "P-005", "P-009", "P-021"]
shipment: "159-S"
covering_feature: "151-F"
pull_request: 436
review_thread: "PRRT_kwDORzpWpM6ft_fB"
related_bugs:
  - "docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md (stash 7F93FA0C) — related, distinct, NOT a duplicate"
  - "docs/bugs/2026-09-07-backlog-lifecycle-missing-temporary-out-of-queue-status.md (stash 4D3826FE, parked/hold) — related, distinct, NOT a duplicate; shares the explicit-status-semantics principle and consumes this fix's member-class matrix, but is a backlogit lifecycle-vocabulary gap requiring an upstream tool change. MUST NOT be merged into this fix's shipment"
decision_artifact: "docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md"
compound_learning: "docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md"
diagrams:
  - "docs/diagrams/05-shipment-reconcile-cascade-premode.mmd"
  - "docs/diagrams/06-evidence-contract.mmd"
  - "docs/diagrams/04-ship-workflow.mmd"
tags:
  - "bug"
  - "workflow-protocol"
  - "cross-tool-integration"
  - "contract-drift"
  - "composed-state-machine"
  - "shipment-closure"
  - "cascade-close"
  - "p-015"
  - "p-021"
  - "backlogit-lifecycle"
---

## Summary

`shipment-reconcile` Pre-Mode classifies **every** manifest member by comparing that member's
declared frontmatter `status` against a **single scalar** `expected_status`. At Ship Step 5/6
closure that scalar is `done`.

A manifest that qualifies for the P-015 **verified fully-covered-root** CASCADE close path is
*required* to contain its qualifying root feature — full coverage of the root is itself a
classifier precondition. That feature is validly `active` at the instant before close, because
the cascade operation is what archives it. No earlier step transitions it.

The two facts cannot both hold. Pre-Mode therefore classifies the qualifying feature
`status-mismatch` and returns `HALT — operator reconcile required` on **every** cascade-eligible
closure, before Safe-Close Step 0 — the step that actually runs the P-015 classifier — is ever
reached. The HALT is not the detection of drift; it is a structural artifact of the protocol.

The second-order consequence is the one that produced deferred entry `15A02E21`: because the only
ways forward are (a) mutating backlog state that Pre-Mode is explicitly forbidden to mutate, or
(b) proceeding past a literal fail-closed HALT, the *authorization basis* for the resulting close
becomes ambiguous. An operator authorization scoped to one thing (removing a stale lock) ends up
being relied upon, implicitly, for something else (overriding a per-item status gate).

## Affected components

| Role | Component | Contract it declares |
|---|---|---|
| Producer of the expectation | `.github/skills/shipment-reconcile/SKILL.md` — Pre-Mode step 3 | For **each manifest item**: read frontmatter `status`, compare to `expected_status`, classify `matched` or `status-mismatch`. No artifact-type scoping. |
| Gate | `.github/skills/shipment-reconcile/SKILL.md` — Pre-Mode step 7 | Any `missing`, `status-mismatch`, or `orphan` item ⇒ `HALT — operator reconcile required`; do **not** call the close operation. |
| Consumer of reality | `.github/skills/shipment-reconcile/SKILL.md` — Safe-Close Step 0(c) | CASCADE is permitted only when every feature member is a **root**, is **fully covered** at every depth, and the manifest contains nothing beyond the qualifying root feature(s) and their descendants. |
| Contradicting clause | `.github/skills/shipment-reconcile/SKILL.md` — Cascade Close Sub-Procedure step 3 | `required_ids` = the shipment record **and every qualifying feature member**, "**both unconditionally** — never omitted, and never conditioned on either artifact's own pre-close declared status". |
| Classifier | `src/autoharness/gates/shipment_closure.py` — `classify_shipment_close_path` | Machine-checkable CASCADE / SAFE_CLOSE verdict, executed inside Safe-Close Step 0 — i.e. **after** the Pre-Mode gate has already decided. |
| Caller | `.github/agents/_ship.agent.md` — Step 5 Closure Tasks | Runs `mode: pre` → `mode: safe-close` → `mode: post`; must halt on `RECONCILE_FAIL`. |
| Underlying tool | backlogit ≥ 1.8.0 shipment/feature lifecycle | The cascade engine (`internal/core/shipment_lifecycle.go`) is what transitions the covering feature to archived. |

## Observed versus expected behavior

**Expected.** A shipment whose manifest the P-015 classifier has positively verified as a
fully-covered root should pass Pre-Mode when every member holds a status that is *legitimate for
its member class at that point in the lifecycle*, and should then proceed to the classifier-selected
CASCADE close path.

**Observed (159-S, 2026-09-06).** Pre-Mode ran with `expected_status: done` against the full
manifest `[151-F, 151.001-T … 151.007-T]`:

* all seven tasks classified `matched` or `pre-archived`;
* orphan scan clean;
* shipment record `active` ⇒ `record-consistent`;
* **`151-F` declared `status: active`, not `done` ⇒ `status-mismatch` ⇒ `HALT — operator reconcile required`.**

The session proceeded past the literal HALT as a disclosed, reasoned deviation. The reconcile
report is `.backlogit/reconcile/159-S-pre-20260906-072505.md`; the disclosure is recorded in
`docs/closure/2026-09-06-159-s-151-f-cascade-close-completion.md` §"Actions performed" item 5.

## Reproduction

The defect is deterministic and requires no unusual state — only a CASCADE-eligible manifest.

1. Assemble a shipment whose manifest is a root feature plus **all** of its descendants at every
   depth (this is what Stage's shipment assembly produces for a full-feature shipment; `159-S` is
   an instance: `custom_fields.items = [151-F, 151.001-T … 151.007-T]`, `covering_feature: 151-F`).
2. Execute and merge the shipment normally. Tasks reach `done`; the covering feature remains
   `active` because nothing transitions it.
3. At closure, invoke `shipment-reconcile` `mode: pre` with `expected_status: done`.
4. Pre-Mode step 3 compares `151-F.status` (`active`) to `done` ⇒ `status-mismatch`;
   step 7 ⇒ `HALT — operator reconcile required`.

Read-only confirmation of the manifest shape and the classifier's own precondition:

```powershell
backlogit shipment get 159-S          # items include the covering feature 151-F
backlogit get 151-F                   # artifact_type: feature, root (no parent_id)
```

There is no manifest state that both (a) satisfies Pre-Mode's `expected_status: done` for the
feature member and (b) leaves the feature available for the cascade to archive under the terms the
Cascade Close Sub-Procedure's `required_ids` demands.

## Root cause

**Two independently authored contracts, each locally correct, that cannot both be satisfied when
composed — and neither was ever validated against the other or against backlogit's actual
lifecycle semantics.**

Three specific factors:

1. **A single scalar cannot express a multi-class expectation.** `mode: pre` accepts exactly one
   `expected_status` and classifies every other value as `status-mismatch`. A closure-time manifest
   is intrinsically **heterogeneous**: the shipment record is `active`, the tasks are `done`, and
   the qualifying feature is `active`. The scalar model has no way to represent that.

   This limitation is *already documented*, but only for the intake invocation.
   `.github/agents/_ship.agent.md` Step 0.5 carries an explicit scope note: "`shipment-reconcile`'s
   `mode: pre` accepts only one `expected_status` value and classifies any other status as
   `status-mismatch`, so it cannot represent a legitimately mixed manifest." The equivalent
   accommodation was never extended to the closure invocation.

2. **An artifact-type filter that exists in three sibling checks is missing from the fourth.**

   | Check | Filters to task artifacts before status logic? |
   |---|---|
   | Ship Step 0.5 item 1a intake early-warning (`custom_fields.items`) | **Yes** |
   | Ship Step 2 executable-task-set derivation (C1–C6) — "artifact-type filtering always precedes any status read"; the covering feature "is never executed" | **Yes** |
   | Pre-Mode step 5 shipment-record-status classification — mandatory task-artifact filter, justified in-skill so a covering feature "can never be misread as a 'conflicting task' and falsely halt an otherwise-consistent shipment" | **Yes** |
   | **Pre-Mode step 3 per-item status check** | **No** |

   The skill already articulates, in its own words, the exact failure mode — for the record scope —
   and then omits the same protection at item scope.

3. **Ordering.** The P-015 classifier is the only component that knows a member is a *qualifying
   feature* rather than an ordinary manifest item. It runs in Safe-Close Step 0(c), which is
   downstream of the Pre-Mode gate. Pre-Mode is therefore structurally unable to reason about
   member class, even though the information exists a few steps later.

### The intra-skill contradiction, stated plainly

Both of these clauses are in the same file:

* **Pre-Mode step 3/7** — the qualifying feature must declare `done`, or closure halts.
* **Cascade Close Sub-Procedure step 3** — `required_ids` includes the shipment record and every
  qualifying feature member "both unconditionally … never conditioned on either artifact's own
  pre-close declared status".

One clause makes the feature's pre-close status decisive. The other declares it irrelevant. A fix
that changes only one of them leaves the skill self-inconsistent.

## Why the available workarounds are all defective

| Workaround | Why it fails |
|---|---|
| Move `151-F` to `done` before Pre-Mode | Pre-Mode is **detect-and-report only — NO auto-repair**. The mutation also falls outside Safe-Close's manifest-scoped mutation authority, and it fabricates a lifecycle transition that backlogit's cascade engine performs itself. It is ceremony with mutation risk, and the two-set gate makes the feature's pre-close status irrelevant anyway. |
| Proceed past the literal HALT as a disclosed deviation | What the 159-S session did. It is honest and auditable, but it institutionalises overriding a fail-closed gate, and it is precisely the authorization ambiguity captured as `15A02E21`. Repeating it on every cascade closure erodes the meaning of every other HALT. |
| Fall back to manual safe-close | Safe-Close Step 0 never ran, so no verdict was ever selected; and once CASCADE *is* selected the **No-Substitution rule** makes `CASCADE → manual safe-close` a P-005 process deviation. |
| Exclude the feature from the manifest | Directly contradicts the P-015 classifier's full-coverage precondition and would flip the verdict to `SAFE_CLOSE`, which is a different (and for a full-feature shipment, incorrect) close path. |

## Blast radius

* **Every** future CASCADE-eligible closure reproduces this deterministically. It is not
  state-dependent or timing-dependent.
* Full-feature shipments — the normal output of Stage's shipment assembly, which places the
  covering feature first in the manifest — are exactly the shape that qualifies for CASCADE.
* Each occurrence forces a fresh, ad-hoc operator authorization decision at the most
  consequential moment in the pipeline (immediately before an irreversible archival), which is the
  worst possible place to require improvised judgement.
* The disclosed-deviation precedent is now recorded in a merged closure artifact, so subsequent
  sessions may cite it as prior art for overriding a status-mismatch HALT — including in cases
  where the HALT is genuine.

## Distinction from related bugs (cross-reference, not duplicate)

* **`7F93FA0C` — `docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md`.**
  Same *defect class* (independently specified contracts that cannot compose), different surfaces
  and a different fix. That bug is about closure-evidence **filename and metadata** divergence
  between `operational-closure` (producer) and the `pipeline-topology` closure reader (consumer).
  This bug is about **status semantics** inside a single skill and its relationship to backlogit's
  lifecycle. They must be fixed independently; neither supersedes the other. Diagram
  `docs/diagrams/06-evidence-contract.mmd` places both on one evidence map precisely to make the
  shared class visible.
* **The Engram content-record schema incident** is another instance of the same class and is cited
  in the compound learning as corroboration. It is **explicitly out of this bug's fix scope**.

## Acceptance criteria

A fix is complete when all of the following hold.

1. **No unreachable gate.** A shipment whose manifest the P-015 classifier verifies as a
   fully-covered root, and whose members each hold a status legitimate for their member class,
   returns `PROCEED` from Pre-Mode without any deviation, override, or pre-close mutation.
2. **Member-class semantics are explicit.** The skill states, per member class (shipment record,
   qualifying feature, task, validated linked deliberation), which declared statuses are valid,
   which are tolerated, and which halt. See the valid-status matrix in
   `docs/diagrams/05-shipment-reconcile-cascade-premode.mmd`.
3. **Fail-closed posture preserved.** A `queued` qualifying feature, a `queued`/`active` task at
   closure, any `missing` member, and any `orphan` still produce
   `HALT — operator reconcile required`. The change narrows the check to the one class the
   classifier has positively identified; it does not weaken any other class.
4. **No ID special-casing.** Qualifying-feature membership is taken **only** from the classifier's
   own determination, never from an ID pattern, a `-F` suffix heuristic, or a named exception.
   P-015 explicitly forbids per-member or per-ID qualification.
5. **Internal consistency.** Pre-Mode's expectation and the Cascade Close Sub-Procedure's
   `required_ids` rule no longer contradict each other, and the skill says so in one place rather
   than restating status rules in two.
6. **Classifier-failure default is fail-closed.** Any classifier error, ambiguity, or unresolved
   precondition falls back to today's strict per-item semantics, matching the existing Step 0(c)
   default ("including any classifier error, ambiguity, or unresolved precondition → SAFE_CLOSE").
7. **Auditable report.** The Pre-Mode report records the close-path verdict, the qualifying-feature
   set, and the member class applied to each item, so a future auditor can reconstruct *why* a
   feature member was accepted while `active` without reading the skill.
8. **Regression coverage.** Tests cover: (a) a fully-covered-root manifest with an `active`
   qualifying feature ⇒ `PROCEED`; (b) the same manifest with a **`queued`** feature ⇒ `HALT`;
   (c) a partial-feature manifest (`SAFE_CLOSE`) ⇒ today's strict behaviour unchanged;
   (d) classifier failure ⇒ strict behaviour, fail-closed.
9. **Authorization disposition recorded.** — **SATISFIED 2026-09-07.** The already-executed 159-S
   close has an explicit, recorded operator disposition: **`accepted-with-remediation` P-005
   deviation** (decision D-1). `15A02E21` is closed on evidence rather than on silence.
10. **Declared status is read regardless of storage location (R-1).** Member-class evaluation reads
    the frontmatter `status` field of every member from `queue/` **or** `archive/`. `pre-archived`
    is a *descriptive location label* recorded **alongside** the declared status — never a
    substitute for it, and never a short-circuit that skips the status comparison. Without this,
    criterion 3's "`queued` qualifying feature still HALTs" promise is false for an
    archive-resident record, because today's step 3 classifies on location before ever reading
    `status`.
11. **`archived` is tolerated *and reported* (R-2).** A qualifying feature declaring `archived`
    pre-close is accepted, but MUST be emitted in the Pre-Mode report under its own
    anomalous-provenance label. Silent tolerance is a defect, not a pass.
12. **The classifier `reason` is recorded verbatim (R-3).** The report carries the close-path
    verdict **and** the classifier's `reason` string exactly as returned, so a `SAFE_CLOSE` caused
    by a transient workspace read failure is distinguishable from a genuine partial manifest.
13. **Atomicity (R-4).** The Pre-Mode step 2b classifier invocation and the member-class matrix
    land in the **same shipment**, in the same atomic task contract. No sizing split may produce an
    interim state in which the matrix ships without the classifier — that state *is* the rejected
    Option B, with criterion 3's feature-status signal absent in production.
14. **Unrecognised status is an explicit HALT row (R-5).** The member-class matrix treats a declared
    status it does not recognise as an explicit `HALT`, never as a silent fall-through or an
    implicit tolerate. This costs nothing today and guarantees that any future lifecycle status
    (for example a `parked`/`hold` state — see
    `docs/bugs/2026-09-07-backlog-lifecycle-missing-temporary-out-of-queue-status.md`) surfaces as
    a loud, triageable HALT forcing a deliberate contract decision, rather than being silently
    absorbed by whichever branch happens to catch it.

## The durable principle this bug establishes

**Lifecycle states must be self-describing. Storage location, and surrounding workflow context,
must never silently substitute for declared state.**

This bug is one instance of that principle being violated; it is stated here as a rule because the
instance is not the point.

| Aspect | Rule |
|---|---|
| **Declared over inferred** | A state is what the artifact *declares* it to be. Location (`queue/` vs `archive/`), directory routing, presence in a manifest, or the stage of the workflow that happens to be running are **descriptive** signals. They may be recorded, and they may be cross-checked against the declared state to detect anomalies, but they may never *replace* the declared-state read. |
| **No tacit meaning** | A status value must carry its meaning explicitly. If understanding what a status means requires knowing which agent set it, which workflow step is running, or which directory the file sits in, the vocabulary is under-specified — and that tacit context *will* be lost, because it lives only in the head of whoever wrote the clause. |
| **Overloading is a defect** | When one status value is made to carry two distinct meanings (e.g. `archived` meaning both "finished" and "set aside for now"), readers must disambiguate from context. That disambiguation is exactly the tacit knowledge that evaporates. Overloaded values must be split into distinct, explicitly-named states. |
| **Unrecognised is loud** | Any consumer of a status vocabulary must fail closed and loudly on a value it does not recognise. Silent fall-through converts a vocabulary extension into an undetected behaviour change. |
| **One authoritative statement** | The valid/tolerated/halting statuses for a given class are stated in exactly **one** place; every other site references it. Two independent restatements will drift, and the drift will be invisible until a state arises that only one of them anticipated. |

**Where this principle is currently violated in this codebase, beyond this bug:** the absence of an
explicit *temporary out-of-queue* status. `archived` today silently carries both "done / will not be
done" **and** "removed from the queue but may return", and the only way to tell them apart is
surrounding context. That is a separate contract surface with a separate fix — recorded in
`docs/bugs/2026-09-07-backlog-lifecycle-missing-temporary-out-of-queue-status.md` — but it is the
*same* principle, which is why the principle is stated here rather than in either bug alone.

## Non-goals

* Relaxing `status-mismatch` handling for **task** members, or for any member class other than a
  classifier-identified qualifying feature.
* Changing the P-015 default. Safe-close remains the default close path; CASCADE remains the
  narrow, machine-verified exception.
* Altering the two-set `allowed_ids` / `required_ids` gate, the pre-close declared-status snapshot,
  or the CT-1 declared-status-over-location rule. Those are correct and load-bearing.
* Modifying PR #436, its body, or its review threads. This record is authored alongside it, not in it.
* Re-opening or re-closing shipment `159-S`. The archival already executed; only its authorization
  disposition is open.
* Fixing `7F93FA0C` or the Engram content-record schema incident. Cited as related evidence only.
* Any implementation work. This record is planning output; implementation is gated behind operator
  diagram review, then `impl-plan` and `harvest`.

## References

**Contract sources**

* `.github/skills/shipment-reconcile/SKILL.md` — Output/classification table; Required Protocol →
  Pre-Mode steps 3, 5, 7; Safe-Close Mode Step 0(a)(b)(c); Cascade Close Sub-Procedure steps 1–3.
* `.github/policies/workflow-policies.md` — **P-015** Single-Artifact Shipment Closure.
* `.github/agents/_ship.agent.md` — Step 0.5 item 6 intake reconciliation and its scope note;
  Step 2 executable-task-set derivation (C1–C6); Step 5 Closure Tasks.
* `src/autoharness/gates/shipment_closure.py` — `classify_shipment_close_path`.

**Instance evidence**

* Shipment `159-S` (`covering_feature: 151-F`; `custom_fields.items = [151-F, 151.001-T … 151.007-T]`).
* `docs/closure/2026-09-06-159-s-151-f-cascade-close-completion.md` — §Operator Authorization and
  §Actions performed item 5 (the verbatim `status-mismatch` / HALT disclosure).
* `.backlogit/reconcile/159-S-pre-20260906-072505.md` — the Pre-Mode report and its gate-decision
  disclosure.
* `.backlogit/reconcile/159-S-cascade-close-20260906-073211.md` — snapshot and two-set gate detail.
* PR [#436](https://github.com/softwaresalt/autoharness/pull/436) at HEAD `ad4cb74a`; review thread
  `PRRT_kwDORzpWpM6ft_fB`.
* Deferred stash entry `15A02E21` (P-021 C2 capture; `REQUIRES DELIBERATION: yes`).

**Companion artifacts authored with this record**

* `docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md`
* `docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
* `docs/diagrams/` — `00` conventions, `01` lifecycle, `02` orchestrator, `03` stage, `04` ship,
  `05` cascade pre-mode drill-down, `06` evidence contract.

**Related, distinct**

* `docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md` (stash `7F93FA0C`).
