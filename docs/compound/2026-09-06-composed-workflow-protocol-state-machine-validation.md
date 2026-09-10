---
title: "Independently authored workflow protocols must be validated as a composed state machine against the tool lifecycle they sit on — local gate correctness is not evidence of global correctness"
description: "Two clauses of the same skill, each internally correct, produced a gate that no legitimate system state could satisfy: shipment-reconcile Pre-Mode demanded a covering feature declare `done` at closure, while the P-015 cascade contract in the same file declared that feature's pre-close status irrelevant because the cascade operation is what archives it. The defect was invisible to every local review because each clause reviews clean in isolation; it only exists at the seam between the two protocols and backlogit's actual lifecycle semantics."
problem_type: "composed-contract-conflict"
category: "workflow-protocol-design"
component: "shipment-reconcile Pre-Mode vs P-015 Cascade Close Sub-Procedure; autoharness workflow protocols layered over backlogit lifecycle"
root_cause: "autoharness workflow protocols are authored as independent, locally-reviewed documents (a skill's Pre-Mode section, that same skill's Safe-Close section, the Ship agent's closure step, the P-015 policy, and the Python close-path classifier), but the runtime behavior is their COMPOSITION over a third party's state machine — backlogit's artifact lifecycle. Pre-Mode encodes a single-scalar `expected_status` model in which every manifest member shares one status; the P-015 cascade path requires the manifest to contain a qualifying ROOT FEATURE whose full coverage is a classifier precondition, and that feature is validly `active` until the cascade operation itself archives it. The scalar model has no vocabulary for a heterogeneous manifest (shipment record `active`, tasks `done`, qualifying feature `active`), so it classifies the feature `status-mismatch` and returns a fail-closed HALT on every cascade-eligible closure — before Safe-Close Step 0, the only step that knows the member is a qualifying feature, has run. The same skill's Cascade Close Sub-Procedure step 3 simultaneously computes `required_ids` as the shipment record plus every qualifying feature member 'both unconditionally — never conditioned on either artifact's own pre-close declared status', so one clause makes the status decisive while the other declares it irrelevant. Neither clause is wrong on its own; no review that reads either clause in isolation can see the conflict, because the conflict is a property of the composition, not of either part. Corroborating evidence that this is a class and not an incident: the identical artifact-type filter that would have prevented this already exists in THREE sibling checks (Ship's intake early-warning, Ship's executable-task-set derivation, and Pre-Mode's own record-scope classification — the last explicitly justified in-skill as preventing a covering feature from 'falsely halt[ing] an otherwise-consistent shipment') and is missing only from Pre-Mode's per-item check; and the Ship agent already documents the single-scalar limitation in prose for the INTAKE invocation while never extending the accommodation to the CLOSURE invocation."
resolution_type: "process"
severity: "high"
date: 2026-09-06
tags:
  - "composed-state-machine"
  - "contract-conflict"
  - "cross-tool-integration"
  - "workflow-protocol"
  - "shipment-closure"
  - "cascade-close"
  - "p-015"
  - "p-021"
  - "fail-closed-design"
  - "unreachable-gate"
  - "backlogit-lifecycle"
  - "review-coverage"
citations:
  - "Stash entry 15A02E21 (P-021 C2 deferred scope expansion; REQUIRES DELIBERATION: yes)"
  - "docs/bugs/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-mismatch.md"
  - "docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md"
  - ".github/skills/shipment-reconcile/SKILL.md (Pre-Mode steps 3/5/7; Safe-Close Step 0(c); Cascade Close Sub-Procedure step 3)"
  - ".github/policies/workflow-policies.md (P-015)"
  - ".github/agents/_ship.agent.md (Step 0.5 scope note; Step 2 C1-C6 derivation; Step 5 closure)"
  - "src/autoharness/gates/shipment_closure.py (classify_shipment_close_path)"
  - "docs/closure/2026-09-06-159-s-151-f-cascade-close-completion.md (verbatim status-mismatch/HALT disclosure)"
  - "PR #436 (159-S / 151-F post-merge closure), review thread PRRT_kwDORzpWpM6ft_fB"
  - "docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md (stash 7F93FA0C) — same class, distinct bug"
  - "docs/diagrams/05-shipment-reconcile-cascade-premode.mmd and 06-evidence-contract.mmd"
source: docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
doc_type: learning
---

# A gate no legitimate state could satisfy, assembled from clauses that were each correct

## The pitfall

Every workflow protocol in this repository is authored, reviewed, and hardened as a **document**:
a skill section, an agent step, a policy clause, a gate implementation. Review operates at that
granularity too — a reviewer reads the clause, checks it against its stated purpose, and passes it.

But nothing at runtime executes a clause. Runtime executes the **composition** of all of them,
over a third party's state machine — backlogit's artifact lifecycle.

`shipment-reconcile` Pre-Mode is a well-written gate. Its per-item check reads each manifest
member's declared `status` and compares it to `expected_status`, halting on any mismatch. Read on
its own, it is exemplary fail-closed design.

The P-015 cascade close path is also well written. It permits the destructive cascade operation
only when a machine-checkable classifier verifies that every feature member is a **root** and is
**fully covered at every depth** — so a qualifying manifest is *required* to contain its covering
feature.

Compose the two at closure time, and:

* `expected_status` is `done`;
* the manifest **must** contain the covering feature;
* the covering feature is `active`, because the cascade operation is what archives it and nothing
  upstream transitions it.

The gate is unsatisfiable. Not rarely, not under load, not on drift — **on every cascade-eligible
closure, deterministically, forever**. And it fires *before* the only step that could have known
the member was a qualifying feature rather than an ordinary item.

Worse, the same skill contains the refutation of its own gate. The Cascade Close Sub-Procedure
computes `required_ids` as the shipment record plus every qualifying feature member "**both
unconditionally** — never conditioned on either artifact's own pre-close declared status." One
clause makes the feature's status decisive; the other declares it irrelevant. Both shipped.

## Why every local review passed it

Each clause is *individually* correct, so there is no defect for a clause-scoped reviewer to find:

* A reviewer of Pre-Mode asks "does this correctly detect status drift?" — yes, it does.
* A reviewer of the cascade path asks "does this correctly restrict the destructive operation?" —
  yes, it does.
* A reviewer of the P-015 policy asks "does this prevent partial-feature corruption?" — yes.
* A reviewer of `classify_shipment_close_path` asks "does this enumerate descendants correctly?" —
  yes, and it was even hardened once already (direct-children-only was found insufficient).

No question at clause scope surfaces the conflict, because **the conflict is not in any clause**.
It is a property of the graph they form. The only reviewer who can see it is one who asks a
different question: *what sequence of states does the composed machine actually traverse, and does
a legitimate state exist that satisfies every gate along the way?*

## The corroborating signal that this is a class, not an incident

Two facts show the codebase already knew the shape of this problem and still shipped it:

1. **The missing filter exists three times elsewhere.** The artifact-type filter that would have
   prevented this is applied by Ship's intake early-warning, by Ship's executable-task-set
   derivation ("artifact-type filtering always precedes any status read"; the covering feature "is
   never executed"), and by Pre-Mode's **own record-scope classification** — where the skill
   explicitly justifies it so that a covering feature "can never be misread as a 'conflicting task'
   and falsely halt an otherwise-consistent shipment." The skill articulates the exact failure mode
   at record scope, then omits the same protection at item scope, in the same file.

2. **The limitation is already documented — for the wrong invocation.** The Ship agent's Step 0.5
   scope note states plainly that `mode: pre` "accepts only one `expected_status` value and
   classifies any other status as `status-mismatch`, so it cannot represent a legitimately mixed
   manifest," and instructs against using it on a mixed-status resumed session. That accommodation
   was reasoned out for **intake** and never carried to **closure**, where the manifest is
   *intrinsically* mixed.

Both are the signature of document-scoped authorship: the insight was recorded where it was
discovered, and never propagated across the composition.

## The second-order damage: authorization ambiguity

An unsatisfiable fail-closed gate does not merely block work — it **corrupts the meaning of
authorization**.

Faced with a HALT that no legitimate action can clear, the operator's only paths are to mutate
state the gate forbids mutating, or to proceed past a fail-closed halt. In the 159-S instance the
session proceeded, honestly and with full disclosure, on the strength of an operator authorization
that had been scoped to something else entirely (removing a stale lock file). The resulting
question — *was that authorization sufficient?* — could not be answered from the record, and had to
be deferred as its own P-021 entry.

This is the compounding cost: **every unsatisfiable gate manufactures a precedent for overriding
gates.** Once a merged closure artifact records "we proceeded past a literal HALT as a disclosed,
reasoned deviation," that reasoning is available for citation the next time a HALT is inconvenient
— including when the HALT is genuine.

## What to do differently

1. **Validate protocols as a composed state machine, not as documents.** Before shipping a
   protocol change, enumerate the states the composed machine traverses and ask, for each gate:
   *does a legitimate system state exist that satisfies this gate?* A gate that no valid state can
   satisfy is a defect of the same severity as a gate that everything passes.

2. **Diagram the composition, and review the diagram.** Prose specifications hide seams; a
   state/flow diagram forces every handoff to be drawn. The diagram set authored with this learning
   (`docs/diagrams/`) exists for exactly this purpose, and its review is an explicit gate before
   implementation planning.

3. **Model the tool's lifecycle explicitly, and never assume a transition it does not perform.**
   autoharness protocols sit **on top of** backlogit. Write down, per artifact class, which
   statuses are legitimate at each pipeline point and **which component performs each transition**.
   The entire defect reduces to one unrecorded fact: *the cascade operation is what archives the
   covering feature, so `active` is its only valid pre-close state.*

4. **Where one check applies a scoping rule, ask which sibling checks should also apply it.**
   Treat an artifact-type filter, a status-set restriction, or a member-class carve-out as a
   **cross-cutting invariant** with an enumerated list of application sites — not as a local fix at
   the one site where the bug was found.

5. **Propagate documented limitations to every invocation of the limited thing.** A prose note
   saying "this check cannot represent a mixed manifest" is a latent bug report against **every**
   caller that passes it a mixed manifest, not just the one the note was written for.

6. **Add a "can this gate ever be satisfied?" question to plan-review and plan-harden.** For each
   newly introduced or modified gate: name a concrete, legitimate system state that passes it, and
   name a concrete state that fails it. If the first cannot be named, the gate is unreachable.

7. **Treat an unsatisfiable gate as a fail-closed *design* failure, not an operational nuisance.**
   The correct response is to fix the contract, not to establish a deviation ritual around it.

8. **Make lifecycle states self-describing; never let location or context substitute for declared
   state.** This is the specific sub-rule that lesson 3 kept re-discovering, promoted to a rule of
   its own because it generalises well beyond the cascade path:

   * **Declared over inferred.** A state is what the artifact *declares*. Storage location
     (`queue/` vs `archive/`), directory routing, manifest membership, or which workflow step
     happens to be running are **descriptive** signals. Record them, cross-check them against the
     declared state to *detect* anomalies — but never let them *replace* the declared-state read.
     This defect's own R-1 refinement exists because Pre-Mode's `pre-archived` classification reads
     location and then never reads `status` at all, which silently falsified the fix's own
     fail-closed promise for archive-resident records.
   * **No tacit meaning.** If knowing what a status *means* requires knowing who set it, which step
     is running, or which directory holds the file, the vocabulary is under-specified. That tacit
     context lives only in the head of whoever wrote the clause, and it *will* be lost.
   * **Overloading is a defect.** One value carrying two meanings forces readers to disambiguate
     from context — precisely the knowledge that evaporates. Split overloaded values into distinct,
     explicitly named states.
   * **Unrecognised is loud.** Every consumer of a status vocabulary must fail closed and loudly on
     a value it does not recognise. Silent fall-through turns a vocabulary extension into an
     undetected behaviour change — the same generative failure as the composition defect itself,
     just displaced in time.
   * **One authoritative statement.** State a class's valid/tolerated/halting statuses once;
     reference it everywhere else. Two independent restatements drift, and the drift stays invisible
     until a state arises that only one of them anticipated. (That is literally how this bug was
     born: Pre-Mode and the Cascade Sub-Procedure each stated the rule independently.)

   **Live instance of this rule, separate from this bug:** backlogit today has no explicit
   *temporary out-of-queue* status. `archived` silently carries both "done / will not be done" and
   "taken out of the queue but may come back", distinguishable only from surrounding context —
   textbook overloading. Recorded as a distinct contract surface in
   `docs/bugs/2026-09-07-backlog-lifecycle-missing-temporary-out-of-queue-status.md`. Different
   tool, different fix, same rule.

## The wider pattern this belongs to

This is the second contract-composition defect recorded in this repository on the same day, and
the third overall instance of the class:

| Instance | Producer contract | Consumer contract | Failure at the seam |
|---|---|---|---|
| `15A02E21` (this learning) | Pre-Mode: every manifest member declares `expected_status` | P-015 cascade: the qualifying feature is `active` until the cascade archives it | Unsatisfiable gate ⇒ inevitable HALT ⇒ authorization ambiguity |
| `7F93FA0C` | `operational-closure`: `docs/closure/{date}-{slug}-closure.md`, narrative content | `pipeline-topology`: `docs/closure/{shipment_id}-*-post-merge-closure.md`, machine-readable frontmatter | No filename satisfies both ⇒ valid evidence never opened ⇒ `PREDECESSOR_CLOSURE_INCOMPLETE` |
| Engram content-record schema incident | Record writer's schema | Record reader's schema | Schema divergence at the storage seam (cited as corroboration; out of scope for both fixes) |
| `parked`/`hold` lifecycle-vocabulary gap (2026-09-07) | backlogit's status enum: `archived` is the only non-terminal-looking way out of the queue | autoharness protocols + human readers, which need "set aside, may return" to be distinguishable from "done / won't do" | One value carries two meanings; disambiguation depends on tacit context ⇒ state is not self-describing |

They are **distinct bugs with distinct fixes** and must not be merged. What they share is the
generative cause: *independently authored contracts, each locally correct, never validated as a
composition.* The operator's standing goal — a consistent set of workflow protocols that compose
cleanly so autoharness and external tools work together seamlessly — is precisely the property this
class of defect destroys, one locally-correct clause at a time.

## Outcome (2026-09-07)

The `15A02E21` row above is now **decided and planned**, which makes this learning a closed loop
rather than an open observation:

* **Fix: Option A** — classifier-aware, member-class-scoped Pre-Mode (operator decision D-2).
* **Contract: `active | done` pass, `archived` tolerate-and-report, `queued` hard HALT, declared
  status read regardless of storage location** (decision D-3).
* **The authorization ambiguity in the "failure at the seam" column was itself dispositioned** as
  an `accepted-with-remediation` P-005 deviation (decision D-1), with *this* fix named as the
  remediation. That is the mechanism lesson 7 recommends: fix the contract, and label the deviation
  so it stays retrievable — rather than ratifying it and leaving unlabelled prior art for
  overriding a fail-closed HALT.
* **Lesson 6 is carried as OQ-6** in the decision artifact (a standing plan-review/plan-harden
  "name a legitimate passing state and a legitimate failing state" check) and is deliberately *not*
  bundled into this fix's shipment.

## Retrieval hint

Reach for this learning when a gate blocks work that appears legitimate, when a HALT recurs on
every instance of a workflow shape rather than on drift, when two specifications each look correct
but cannot both be satisfied, when a fix is tempting to apply at one call site of a shared rule,
when an operator authorization is being stretched to cover a decision it was not scoped for, or
when a status value's meaning depends on where the record is stored or on which workflow step is
reading it.
