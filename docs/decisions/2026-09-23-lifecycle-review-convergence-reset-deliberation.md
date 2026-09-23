---
title: "Pausing the non-convergent lifecycle review loop: a governance reset, a proof-first rebaseline, and a release-unit split for the Ship pre-task harness-generation lifecycle"
description: "Stage deep deliberation opened after the eleventh consecutive FAIL/BLOCK verdict against the Ship pre-task harness-generation lifecycle plan. Attempts 07-11 reviewed revisions 8, 9, 10, 11 and 12; every attempt closed most of its predecessor's findings and every attempt raised a fresh set, so the loop has never reached zero and shows no mechanism by which it would. Diagnoses the root cause as plan review being used as implementation research over an unbuilt three-subsystem shipment, and proposes Option B: freeze the current artifacts as a diagnostic record, charter an operator-approved versioned acceptance matrix, answer the open questions with nine bounded executable proofs instead of more prose revisions, and re-slice 187-S into independently valuable release units. Recommends Option B but remains exploring: four operator decisions are unresolved and this artifact mutates nothing."
doc_type: decision
source: docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md
date: 2026-09-23
status: exploring
decision_status: exploring
depth: deep
deciders: operator, Stage
promoted_to: none
promoted_to_note: "Deliberate-only. No plan, no revision 13, no attempt 12, no backlog item, no shipment and no carrier is created, edited or retired by this artifact. Option B is a recommendation awaiting operator approval; the four unresolved decisions below gate every subsequent step."
branch: chore/stage-176-s-workflow-defects
head_at_deliberation: 246d8b73
subject_plan: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
subject_plan_revision: 12
subject_plan_revision_commit: 0806b601
subject_verdict_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
subject_verdict_manifest_revision: 21
subject_latest_attempt: 11
subject_latest_attempt_artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-11.md
subject_latest_attempt_commit: 246d8b73
governing_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
governing_decision_revision: 9
feature_id: 181-F
shipment_id: 187-S
attempts_reviewed: [7, 8, 9, 10, 11]
revisions_reviewed: [8, 9, 10, 11, 12]
proposed_epoch_id: LIFECYCLE-E2-R1
mutation_performed: false
review_performed: false
retrieval_state: degraded
policies: [P-001, P-005, P-006, P-009, P-010, P-012, P-016, P-017, P-020]
labels:
  - deliberation
  - deep
  - exploring
  - review-convergence
  - governance-reset
  - proof-first
  - ship-lifecycle
---

# Pausing the non-convergent lifecycle review loop

## Question

The Ship pre-task harness-generation lifecycle plan has been independently
reviewed eleven times and has failed eleven times. The operator has asked for
the loop to be paused and for a coherent, comprehensive strategy to replace it.

This artifact answers one question:

> **What should replace the plan-revise-review loop, given that five
> consecutive revisions have each closed most of their predecessor's findings
> and each raised a fresh set, so the loop has no demonstrated path to zero?**

It is a deliberation, not a decision of record and not a review. It mutates
nothing. It recommends **Option B** — governance reset, proof-first
rebaseline, release-unit split — and remains `decision_status: exploring`
until the operator resolves the four decisions listed at the end.

## What this artifact deliberately does not do

Stage's role boundary (P-010) and the operator's instruction both constrain
this session. For the avoidance of doubt, none of the following happened:

| Not done | Reason |
|---|---|
| Edit the lifecycle plan or create revision 13 | Revision 13 is not authorized; creating it would repeat the failure mode this artifact diagnoses |
| Run a review or authorize/create attempt 12 | `attempt_12_authorized: false` in the manifest; Stage does not self-authorize review |
| Edit the verdict manifest or any attempt artifact | Attempt artifacts are immutable; the manifest is the review skill's authority, not Stage's |
| Edit the governing decision (revision 9) | It governs the whole portfolio; amending it is a separate, operator-approved act |
| Create, edit, retire or archive any backlog item, carrier, shipment or stash entry | 187-S and 181-F remain exactly as they are |
| Create, resolve or prune a checkpoint | No session checkpoint was written |
| Touch the two pre-existing locks under `docs/plans/` and `docs/reviews/` | They belong to the blocked P-004 work; they were read-only observed and left alone |
| Touch source, templates, tests or `.autoharness/harness-manifest.yaml` | Stage does not write production surfaces |
| Push, open, or comment on anything in GitHub | No network mutation |
| Remove or modify untracked working-tree files | All pre-existing untracked artifacts preserved |

The only repository mutation is the creation of this one file and one commit
containing only this file.

## Evidence base and retrieval conditions

Every claim below was read directly from the repository at
`head_at_deliberation: 246d8b73` on branch `chore/stage-176-s-workflow-defects`.

### Retrieval degradation (P-012)

| Capability | State | Effect |
|---|---|---|
| Indexed knowledge retrieval (engram) | `TOOL_UNAVAILABLE` — circuit-open | No semantic search. Compound learnings were located by exact directory listing and read by exact path. Not retried. |
| Intercom visibility | `TOOL_UNAVAILABLE` | No phase broadcasts. Operator visibility is reduced to this artifact and the session summary. |
| Graphtor-docs | `TOOL_UNAVAILABLE` | Documentation questions resolved by direct reads under `docs/`, `.github/` and `.autoharness/`. |
| backlogit MCP | `TOOL_OK` | `backlogit_sync_index` returned 1472 indexed items; shipment and checkpoint reads succeeded. |

**This degradation is a session condition, not a defect in the strategy below
and not a defect in the reviewed plan.** It is recorded because a reader
comparing this artifact to a later, fully-instrumented session should know
that discovery here was bounded and exact rather than broad and semantic. It
narrows confidence about *undiscovered* related work; it does not weaken any
cited finding, all of which were read from their source files.

### Primary evidence

| Artifact | Exact state observed |
|---|---|
| Lifecycle plan | revision **12**, commit `0806b601` |
| Verdict manifest | revision **21**, `verdict: FAIL`, `disposition: FAIL-BLOCKING-P1`, `decision: BLOCK` |
| Finding counts at attempt 11 | `P0` 0, `P1` 8, `P2` 4, `P3` 1; 13 merged, 8 blocking |
| Publication gate | `portfolio-strict-zero-p0-p1-p2`; `publication_eligible: false` |
| Attempt 12 | `attempt_12_exists: false`, `attempt_12_authorized: false`, awaiting revision 13 |
| Terminal attempt artifact | attempt 11, `review_terminal: true`, `terminal-fail-recording-only-no-follow-on-authorized`, commit `246d8b73` |
| Governing decision | revision **9**, `status: decided`, `promoted_to: plan` |
| Shipment `187-S` | `status: queued`, covering feature `181-F` + 16 live tasks; `181.001-T` archived, not a live member |
| Live P-004 | `.github/policies/workflow-policies.md` — canonical whole-suite command, per-test marker correlation, closed rejected-outcome list |
| Installed actor | `.github/skills/harness-architect/SKILL.md:124-131` requires `raise NotImplementedError("...")` per generated test |
| Manifest bindings | `.autoharness/harness-manifest.yaml:472` `TEST_COMMAND`, `:473` `UNIMPLEMENTED_MARKER: 'raise NotImplementedError("...")'` |
| Pre-existing locks | `docs/plans/.2026-09-18-p004-observation-gate-plan.md.lock`, `docs/reviews/.2026-09-18-p004-observation-gate-plan-review.md.lock` — untouched |

### The 187-S budget, computed from the carriers

Summing the `IMPLEMENTATION BUDGET` / `VERIFICATION BUDGET` line of each of
the sixteen live carriers:

```text
181.002  90    181.008 105    181.013 100
181.003  90    181.009  90    181.014 100
181.004  60    181.010 100    181.015 110
181.005 110    181.011 110    181.016  90
181.006  75    181.012  90    181.017  75
181.007  90
                       total = 1485 minutes = 24.75 hours
```

Sixteen tasks, 24.75 engineering hours, in **one** shipment, all serial, none
of which has produced a single line of executable code. Size composition is
15 x `S` and 1 x `XS`, with the archived `181.001-T` the only `M`.

## The convergence record

This is the core evidence. Each row is read from that attempt's own immutable
frontmatter.

| Attempt | Revision reviewed | Verdict | New findings raised | Blocking |
|---|---|---|---|---|
| 07 | 8 | FAIL / BLOCK | `S14`-`S25` (12) | P0 + P1 |
| 08 | 9 | FAIL / BLOCK | `S26`-`S34` (9) | P0 + P1 |
| 09 | 10 | FAIL / BLOCK | `S35`-`S52` (18) | 24 |
| 10 | 11 | FAIL / BLOCK | `S53`-`S66` (14) | 14 (`P1` 14, `P2` 2) |
| 11 | 12 | FAIL / BLOCK | `S69`-`S81` (13) | 8 (`P1` 8, `P2` 4, `P3` 1) |

Read this table carefully, because it contains both the good news and the
fatal news.

**The good news.** Blockers are declining: 24, then 14, then 8. Revision 12 is
genuinely better than revision 11 — attempt 11 closed eleven of the attempt-10
findings outright and partially closed three more. Nobody is doing bad work.

**The fatal news.** *Every single revision raised a fresh set of findings:
12, 9, 18, 14, 13.* Eighty-one findings have been issued and the number of
newly-discovered defects has never approached zero. A loop converges when the
discovery rate falls, not when the backlog of known defects is worked off. The
discovery rate here is flat.

The mechanism is visible in the attempt-11 record. Revision 12 closed `S61`
(membership totalization) by enumerating eleven closed member reason codes —
and that very act exposed `S76`, because the *manifest* reason codes were
never given the same treatment. It closed `S56` (public contract) by naming
the modules and types — and that act exposed `S75`, because naming
`TraversalAdapter` as public without specifying it created a new, larger hole.
It closed `S66` (oversized tasks) by splitting into sixteen tasks — and that
act exposed `S80`, because the complexity labels were chosen to satisfy the
splitting constraint rather than derived from the work.

**Each revision converts an unanswered question into a more precisely stated
unanswered question.** That is what research looks like. It is not what
convergence looks like. Five more revisions would produce five more precisely
stated unanswered questions, and the loop would still not terminate, because
nothing in it ever executes anything.

`docs/compound/093-S-review-loop-convergence.md` recorded this exact shape at
PR #229: *"Without an explicit stop condition, this loop does not naturally
converge to zero findings within any bounded number of cycles for a codebase
this novel (fresh containment/safety-critical code invites deep, iterative
scrutiny)."* The subject here is fresh containment/safety-critical code. The
prediction has held for five revisions.

---

# Part 1 — Architecture diagnosis

## 1.1 The root cause: plan review is being used as implementation research

A plan review asks *"is this plan implementable as written?"* It is a cheap,
fast gate designed to catch structural mistakes before anyone writes code.

For five revisions it has instead been asked *"what is the correct design of a
cross-platform secure filesystem reader, a backlog resolver with a closed
reason taxonomy, and a Ship lifecycle activation?"* That is a research
question, and prose review is close to the worst available instrument for
answering it, because prose cannot fail. A specification that is wrong in a
way no reader notices passes review; a specification that is right but
unfamiliar attracts findings. The only thing that reliably falsifies a claim
about `NtCreateFile` semantics is running `NtCreateFile`.

Attempt 11's own closure assessment states the consequence plainly: the planned
modules *"do not exist at the reviewed HEAD, which was confirmed by directory
inspection only."* Eleven reviews, 24.75 hours of planned work, 81 findings —
and zero executed lines.

## 1.2 Recurring issue families that survived every revision

Four families have persisted across revisions in changed form. They are the
signature of unresolved architecture, not of sloppy editing.

| Family | Early form | Current form (attempt 11) | Why it recurs |
|---|---|---|---|
| **RED / P-004 evidence ownership** | `S14` (attempt 07, `P0`): installed actor hard-coded the wrong red-phase command | `S69` (marker exception type + characterization carve-out), `S78` (observation command not pinned to the canonical whole-suite form) | The plan asserts the actor is already conformant and puts actor changes out of scope, while specifying an evidence shape the actor rejects. The contradiction is a *scope* decision that no revision has been permitted to make. |
| **Registry / reason taxonomy closure** | `S61`, `S63` (attempt 10): membership and manifest classification not total | `S70` (surface registry never defined), `S76` (global manifest reason codes never enumerated) | The plan keeps totalizing one enum at a time. A taxonomy is only closed when the *whole* classification pipeline is closed at once, including the map it classifies against. |
| **Ship placement / checkpoint restore** | `S58`, `S59` (attempt 10): restore replacement and asymmetric placement | `S73` (per-task invariant vs. pre-loop anchors), `S72` (verdict consumed by exit status alone) | The plan states a per-task contract and anchors it at a step whose own retained text says it *"runs once, up front — not in a loop"*. Prose can hold both sentences; a state machine cannot. |
| **Secure traversal containment** | `S53`, `S54`, `S55` (attempt 10): handle traversal, byte cap, same-size mutation | `S75` (undefined `TraversalAdapter`), `S77` (hardlink aliasing, unreachable `OUTSIDE_TRUST_ROOT`), `S79` (contradictory Windows reparse flags) | Containment properties are platform facts. They can be asserted in prose indefinitely without ever being true. |

## 1.3 Fresh defects that each revision introduced

Equally important: the revisions did not merely fail to finish. They
manufactured new, genuine defects that did not exist before.

| Defect | Finding | What went wrong |
|---|---|---|
| **Mutually incompatible budgets** | `S71` (`P1`) | `max_files=256` (plan line 78) against a membership bound of `1..512` (line 144), with queue *and* archive candidates consulted and then re-observed. `(1+N) x 2` claims, repeated on recheck, breaks at roughly `N = 63` — well inside the legal range. `187-S` itself (~77 claims) fits, so dogfood execution would never surface it. |
| **Exit-code aliasing** | `S72` (`P1`) | Ship maps process exit 1 to `NO_HARNESS` and 2 to `UNRESOLVED` without first requiring that a resolver document was emitted. Startup failure, unknown command and argparse usage errors all produce the same statuses, so a crashed resolver is indistinguishable from a clean verdict. |
| **Ambiguous checksum procedure** | `S74` (`P1`) | Plan line 231 says "the exact installed bytes" and names no method, in the terminal task of the DAG, directly contradicting the documented procedure in `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md` §1 (compute from the LF-normalized committed blob via `git cat-file -p :<path>`, never a PowerShell capture). |
| **Unearned public adapter debt** | `S75` (`P1`) | `TraversalAdapter` and `adapter=None` were made *public* before any implementation existed to constrain them. Five serial tasks across four files must now agree on a contract nothing fixes, and a caller-supplied adapter can defeat every containment guarantee while all result types still report success. |
| **Unsupported estimates** | `S80` (`P2`) | The two NT-API tasks are labelled `size: S` / `complexity: medium` with no precedent in the codebase (`src/` has exactly two `ctypes` references, neither marshalling NT structures). The plan's own risk table names the mitigation "no high-complexity live task" — the label satisfies the constraint instead of describing the work. |

The pattern connecting all five: **abstractions were published before anything
earned them.** A public adapter seam, a general registry, a 512-member bound —
each was specified in advance of a single executed call that would have shown
what shape it needed.

## 1.4 Revision 12 is a requirements inventory, not an implementation-ready plan

This is not a criticism of its quality. As an inventory it is good. But it is
the wrong artifact class to hand to Ship, and one shipment currently combines
three genuinely independent subsystems:

1. **A cross-platform secure-input security subsystem** — handle-relative
   traversal, no-follow guarantees, NT API marshalling, identity and version
   snapshots, budget accounting. Safety-critical, platform-specific, novel to
   this codebase.
2. **A backlog/manifest resolver** — record membership, surface
   classification, manifest snapshot, reducer, evidence digest, versioned
   result schema, CLI. Pure domain logic, fully testable in memory.
3. **A Ship lifecycle activation** — template and mirror edits, checkpoint
   restore reordering, manifest checksum refresh. A three-file atomic change
   to the live agent.

These have different risk profiles, different evidence needs, different
failure modes and different audiences. Bundling them means the *entire* unit
is blocked by whichever component is least understood — currently the Windows
NT traversal — and that every review must hold all three in view at once,
which is precisely how a reviewer generates 13-18 findings per pass.

## 1.5 The stable boundaries this work actually has

The recurring families point at the boundaries the design keeps reaching for:

* **An internal secure-input package with private platform adapters.** Not
  public. The adapter seam exists so tests can inject a fake syscall table;
  that is a test seam, and test seams belong behind a private name until
  something outside the package genuinely needs to supply one.
* **A resolver domain with a closed `SurfaceSpec` map, a reducer, and a
  digest.** The map is data, not an abstraction: surface ID to manifest
  artifact path to expected template, with one exact match predicate.
* **A versioned result schema** as the single interchange contract between
  resolver and every consumer.
* **A thin CLI** that is a pure adapter over the resolver — parses, calls,
  serializes one document, exits with the document's own code.
* **Ship as a consumer of a validated document**, never of a process status.

Two corollaries follow directly, and both *remove* work:

* **Support exactly one surface initially: `harness-architect`.** All sixteen
  live tasks already declare `harness-surface:harness-architect`, and
  `.autoharness/harness-manifest.yaml:237-240` already tracks
  `.github/skills/harness-architect/SKILL.md` with an existing template. The
  one surface in use resolves today; the general registry is speculative.
  A closed one-entry map with an explicit `SURFACE_UNSUPPORTED` outcome for
  everything else is smaller, safer and answers `S70` completely.
* **Delete the unearned public abstractions** — the public `TraversalAdapter`,
  the public `adapter=` parameter, and the general surface registry. This
  retires `S75` by construction rather than by specifying it, and shrinks the
  contract that must be reviewed.

## 1.6 The architectural rule going forward

> **No future plan is written until the executable proofs pass. When a proof
> fails, the architecture decision changes — it does not trigger another prose
> remediation.**

This is the load-bearing sentence of the whole strategy. It is what makes the
loop terminate. Today a failure produces a revision; a revision produces new
findings; new findings produce a failure. Under this rule a failure produces a
*changed design*, and designs have a finite number of viable shapes.

---

# Part 2 — The proof-first work

No production implementation is authorized by this artifact. What follows is a
portfolio of nine small, executable experiments. Each has one fixed question,
a fixed file and time budget, and a pass/fail criterion that is decided by
running something, not by reading something.

A proof is **not** a prototype and **not** a first draft of the feature. Its
only output is an answer plus the evidence for it. Proof code is expected to be
thrown away.

## Proof 1 — RED / P-004 conformance (1 test file + temp fixtures, 60m)

**Question:** what evidence shape does the *installed* actor actually accept?

Run the exact canonical whole-suite command. Generate current-task tests that
reach production stubs raising the exact unique `NotImplementedError` marker.
Prove the run exits non-zero, that each generated test is individually
discovered, and that it fails with *its own* marker. Then prove rejection: a
marker-bearing `AssertionError`, a pass, a skip, and a wrong/cross-test marker
must each be refused as evidence. Prove that characterization assertions living
*outside* the generated roster do not contaminate the observation.

**Settles:** `S69` and `S78`, and the scope question of whether
`.github/policies/workflow-policies.md` and the actor skill must enter scope.

## Proof 2 — CLI authenticity (1 test file, 60m)

**Question:** can Ship distinguish a real resolver verdict from a crash?

Invoke the exact module form with the source environment set. Prove Ship
accepts only one schema-valid JSON document whose requested shipment, state,
reason, exit code and process status all match. Then prove halt-with
`resolver-not-observed` for every impostor: startup failure, unknown command,
parser/usage error, help output, malformed JSON, and trailing output after the
document.

**Settles:** `S72`.

## Proof 3 — POSIX traversal, on Linux CI (<=2 files, 60m)

**Question:** do the POSIX containment invariants hold when executed?

Held-descriptor relative traversal with no-follow; a successful nested read; a
symlink swapped in mid-traversal must be refused; capture the exact flag/call
trace; capture identity and version fields.

**Settles:** the POSIX half of `S53`/`S75`/`S77`.

## Proof 4 — Windows traversal, on actual Windows (<=2 files, 120m)

**Question:** does `RootDirectory`-relative `NtCreateFile` descent work here?

Per-component `RootDirectory`-relative `NtCreateFile`; junction and reparse
point must be refused with the observed `NTSTATUS` recorded; normalized final
path captured; identity and version captured; trace captured. **No descendant
pathname fallback is permitted** — if the handle-relative path fails, the proof
fails. It does not quietly reopen by string.

This is the largest budget in the portfolio because it is the largest unknown:
nothing in `src/` marshals NT structures today.

**Settles:** `S79`, the Windows half of `S53`, and the real input to `S80`.

## Proof 5 — Adapter authority (1 file, 45m, runs *after* Proofs 3 and 4)

**Question:** must the adapter seam be public or private?

Write an adversarial adapter that omits the mandatory flags and attempt to
obtain a working reader through it. The result decides the seam.

**Expected recommendation:** *private test seam* — unless the reader can
independently enforce the invariants regardless of which adapter is supplied.
If the reader cannot, a public seam is a containment hole and must not exist.

**Settles:** `S75`.

## Proof 6 — Budget arithmetic truth table (1 test file, 45m)

**Question:** can the admitted maximum shipment exhaust the reader budget?

Build a truth table over the real claim sources: queue candidates, archive
candidates, stable absence entries, manifest reads, template reads, installed
reads, and ledger rechecks. Prove the formula and prove that the admitted
maximum membership *cannot intrinsically exhaust* the file budget.

**Settles:** `S71`, and forces the missing reducer class for budget exhaustion.

## Proof 7 — `SurfaceSpec` and reason taxonomy ratification (2 files, 75m)

**Question:** is the taxonomy closed and does the schema match the runtime?

Ratify exactly one supported mapping (`harness-architect`). Prove every unknown
but well-formed surface ID yields `SURFACE_UNSUPPORTED` -> `UNRESOLVED`, never
`NO_HARNESS`. Enumerate closed global manifest failure codes with fixed
precedence. Prove reducer/schema parity — every runtime outcome validates
against the schema's `oneOf`, and no schema branch is unreachable.

**Settles:** `S70` and `S76`.

## Proof 8 — Checksum replay (disposable repo, 30m, no repository files)

**Question:** none. **This is established procedure, not research.**

`docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md` §1 already
answers it. Proof 8 exists only to replay the known-good steps so the terminal
activation task cannot improvise: read the raw staged `:<path>` bytes via a
Python subprocess with binary capture, then verify against the `HEAD` blob.
Runs in a disposable repository and touches **no file in this repository**.

**Settles:** `S74`.

## Proof 9 — Ship consumer state machine (small fixture proof)

**Question:** where exactly does the per-task harness call sit?

A small fixture standing in for the template and mirror loops. Prove per-task
placement *inside* the exact template and mirror loops; prove
checkpoint-validate-and-resolve *before* cursor restore; prove the consumer
gates on a validated document rather than on status alone.

**Budget derivation.** This proof is bounded by the same rule as the rest of
the portfolio, and its size follows from the two surfaces it must model: the
template loop and the mirror loop. That is **2 files** (one fixture, one test)
and **60 minutes** — the same shape and budget as Proofs 1 and 2, which also
assert structure over a fixed small surface. It is deliberately *not* given
Proof 4's 120 minutes, because unlike the NT work it has no unknown external
API: both loops already exist and were quoted verbatim in attempt 11's `S73`.

**Settles:** `S73` and the placement half of `S72`.

## Portfolio total

Nine proofs, **555 minutes (9.25 hours)**, at most 13 files, none of them
production code. Compare with 24.75 hours of blocked implementation that has
produced nothing for five revisions.

---

# Part 3 — Governance reset

## 3.1 Immediate freeze

Effective on operator approval of this deliberation:

* No revision 13. No attempt 12. No carrier synchronization. No remediation.
* Revision 12 and attempt 11 are **preserved unchanged as the diagnostic
  record** of how the loop failed. They are not errors to be corrected; they
  are the evidence.

The lifecycle state should become `HALTED_NONCONVERGENT`. **This artifact does
not make that transition** — recording it is a mutation of the manifest, which
Stage will not perform here. It happens only after the operator approves.

## 3.2 Charter and versioned acceptance matrix, before any proof

Before proofs run and before any new plan is written, the operator approves a
**charter** (scope, threat model, platform support, budget) and a **versioned
acceptance matrix**. The matrix is the contract review evaluates against, and
it is frozen before evaluation begins.

Nine categories, each row carrying five fields:

| Category | What it fixes |
|---|---|
| `AUTH` | Who may authorize what; role boundaries |
| `SCOPE` | What is in and out; which files may be touched |
| `FLOW` | Control flow, ordering, state transitions |
| `INTERFACE` | Public and private surfaces, signatures, seams |
| `SAFETY` | Containment, threat model, fail-closed behaviour |
| `DATA` | Schemas, enums, taxonomies, digests |
| `TASK` | Decomposition, sizing, the 2-hour rule |
| `EVIDENCE` | What proves a row satisfied |
| `ACTIVATE` | Rollout, atomicity, rollback |

Every row records: **normative source**, **pass criterion**, **evidence**,
**violation severity**, and **deferral rule**.

Why this ends the loop: today a reviewer evaluates a plan against their own
reading of the whole policy corpus, so each reviewer pass legitimately
discovers new requirements. Against a frozen matrix, a requirement that is not
a row is not a blocker — it is a change request.

## 3.3 One authority chain

```text
charter + acceptance matrix
        |
        v
governing decision
        |
        v
active plan
        |
        v
minimal carriers (generated projections)
        |
        v
structured mutable review index
        |
        v
immutable evidence artifacts
```

Each fact lives in exactly one place. In a future migration, duplicated
latest-attempt and verdict prose is removed from operative artifacts — today
the same verdict is restated in the manifest, the attempt artifact, the
shipment description and sixteen carriers, which is sixteen extra places for
authority to drift.

## 3.4 Issue taxonomy and what may block

| Class | Meaning | Blocks? |
|---|---|---|
| `CRITERION` | Violates a frozen matrix row | **Yes** |
| `EVIDENCE` | Matrix-required evidence missing | **Yes** |
| `CONSISTENCY` | Two artifacts disagree | No — mechanical check |
| `RISK` | Hazard noted, no row violated | No |
| `CHANGE` | New requirement not in the matrix | No — change control |
| `PROCESS` | Workflow/hygiene observation | No |
| `DUPLICATE` / `CHILD` | Restates or narrows an existing finding | No |

**Only frozen `CRITERION` violations and matrix-required missing `EVIDENCE`
can block.** New requirements go to change control; they are not in-epoch
blockers. This single rule is what prevents attempts 12 through 20 from
rediscovering the attempt-7-through-11 pattern.

## 3.5 Finding identity and closure

* Stable finding IDs tied to matrix rows, so a finding's identity survives
  revisions.
* Each finding closes **independently**, on specific named evidence.
* Residue after a partial close gets an explicitly **linked child**, never a
  silent carry-forward. (Attempt 11 did this correctly for `S56` -> `S75` and
  `S63` -> `S76`; it should be the rule, not good practice.)
* **No carry-forward without revalidation.** A finding is not assumed still
  open, or still closed, across a revision.

## 3.6 Reviewer stability

Freeze **before** the epoch begins: lead reviewer, rubric version, persona
set, severity mapping, routing. Then:

1. one **initial full review**;
2. **delta reviews** against changes only;
3. one **final full consistency pass**.

**A reviewer route change pauses the epoch.** Attempt 11 ran with
`anchor_review_route_state: TOOL_DEGRADED` — `.autoharness/config.yaml` declares
no `model_routing.anchor_review` key, so the Architecture Strategist persona ran
the same-model rubric. That was correctly declared, not hidden. But a rubric
executed by a different route is a different rubric, and a loop that changes
its measuring instrument between attempts cannot demonstrate convergence.

## 3.7 Three distinct gates

The current single gate is doing three unrelated jobs at once.

| Gate | Question | Criterion |
|---|---|---|
| **Publication** | Is the contract sound enough to publish? | Zero admitted `P0`/`P1`. `P2` is publishable **unless predesignated critical** in the matrix. |
| **Execution** | May implementation begin? | All required proofs pass. |
| **Claim / closure** | May this ship and close? | Ordinary runtime, CI and P-020 gates. |

**Do not use a blanket zero-`P2` rule.** Today's
`portfolio-strict-zero-p0-p1-p2` gate is why `S81` — an argument-passing style
inconsistency, correctly rated `P3` — sits in the same blocking bucket as a
containment hole. A gate that cannot distinguish a keyword-argument preference
from a security defect gives the operator no signal about how close the work
actually is. Criticality is predesignated per matrix row, in advance, not
argued per finding.

## 3.8 Remediation budget

| Limit | Value |
|---|---|
| Consolidated revisions per epoch | **2 maximum** |
| Local remediation cycles after a review | **1 maximum**, in recommended recovery |
| New API / subsystem / threat / platform mechanism | Requires **re-charter** |
| Implementation tasks per shipment | **6 maximum** |
| Engineering hours per shipment | **8 maximum** |
| High-uncertainty native work | Requires a **spike** first |
| Contract growth | **>20% ends the epoch** |

`187-S` violates the task limit by 167% (16 vs 6) and the hour limit by 209%
(24.75 vs 8).

## 3.9 Stop conditions and permitted outcomes

Stop the epoch immediately if **any** of:

* blockers do not decline across revisions;
* newly admitted findings >= findings closed;
* scope, rubric or reviewer route changes mid-epoch;
* an authority mismatch is found between artifacts;
* a new subsystem turns out to be required;
* any budget in 3.8 is exceeded;
* a second remediation fails.

On stop, the permitted outcomes are: **split**, **spike**,
**re-charter / new epoch**, **explicit risk acceptance**, **defer**, or
**cancel**. *"Another attempt"* is not on the list. That omission is the point.

## 3.10 Epoch identity

Identify epochs by a token derived from the subject digest, matrix version and
rubric version — for example **`LIFECYCLE-E2-R1`** — never by attempt number.
"Attempt 12" invites attempt 13. `LIFECYCLE-E2-R1` makes it explicit that a
*different contract* is being evaluated under a *different rubric*, and that
the attempt-7-through-11 record belongs to a closed epoch.

---

# Part 4 — Recommended recovery, phase by phase

## Phase 0 — Operator reset (gate: operator approval)

Operator approves the reset charter and scope, and **chooses the threat model
and platform support**. Current artifacts are frozen as the diagnostic record.
Nothing proceeds until this gate clears — the threat-model answer determines
whether Phase 1 contains Proof 4 at all.

## Phase 1 — Bounded executable proof portfolio (gate: all required proofs pass)

Run the nine proofs. Each has a fixed question, a fixed budget, and pass/fail
evidence.

**A failed proof reopens the architecture decision.** It does not open a
remediation cycle. If Proof 4 shows `RootDirectory` descent is not viable here,
that is an architecture answer, and Options C or D come back onto the table.

## Phase 2 — Re-slice into independently valuable release units (gate: matrix approved)

Likely shape:

| Unit | Content | Independent value |
|---|---|---|
| **A** | Actor / P-004 conformance + per-task lifecycle semantics | The evidence contract becomes true and testable |
| **B** | Resolver + `SurfaceSpec` + schema + CLI | A working, callable resolver |
| **C** | Secure-input platform work — **only if the threat model and proofs require it** | Containment, if genuinely needed |
| **D** | Final Ship activation | The lifecycle goes live |

Define the DAG. **Do not harvest until the matrix is approved.** Each unit must
satisfy 3.8: <=6 tasks, <=8 hours, independently valuable.

**`187-S` (16 tasks, ~24.75h) must be retired or re-chartered — not patched.**
It cannot be brought within budget by editing carriers; it is three subsystems
in one unit, and its size is a symptom of that.

## Phase 3 — Compact active plan (gate: deterministic consistency checks pass)

Generate a compact active plan **from the approved matrix and the proof
results**. Carriers are minimal generated projections, not hand-authored prose.
Run deterministic consistency checks before review — the kind of cross-artifact
drift attempt 11 had to verify by hand should be a script's job.

## Phase 4 — New review epoch (gate: publication)

Fixed lead, rubric, personas. Publication gate: zero `P0`/`P1`, with only
predesignated-critical `P2` blocking. **At most one local remediation cycle.**
Any architectural or new-mechanism finding routes back to Phase 1 or Phase 0 —
it is never absorbed as a fix.

## Phase 5 — Implementation (gate: ordinary runtime / closure / P-020)

1. **Inert implementation of foundations** — code lands, nothing is wired.
2. **Atomic template / mirror / manifest activation** — one task, one commit.
3. **One dogfood task** proving the exact marker transitions RED -> GREEN.
4. Ordinary runtime, closure and P-020 gates afterwards.

---

# Part 5 — Options considered

## Option A — Patch revision 12 and run attempt 12

Fix `S69`-`S81` in a revision 13 and request attempt 12.

**Rejected.** This is exactly what attempts 8, 9, 10 and 11 each did, and each
produced 9-18 fresh findings. Nothing about revision 13 differs structurally
from revisions 9 through 12: the same three subsystems, the same prose
instrument, the same unexecuted code, the same open architecture questions.
The prior is set by five observations, and it is not favourable. Choosing A is
choosing to run the same experiment a sixth time.

## Option B — Governance reset + proof-first rebaseline + release-unit split — **RECOMMENDED**

Freeze; charter and matrix; nine executable proofs; re-slice into bounded,
independently valuable units; new review epoch under a frozen rubric.

**Recommended** because it is the only option that changes the *instrument*.
Every open question becomes decidable by execution; the review gate is
evaluated against a frozen contract; and the stop conditions guarantee
termination in an outcome other than "try again". Cost is 9.25 hours of
throwaway proof work — roughly one third of the already-blocked 24.75 hours —
and it is the only option that retires whole finding families by construction
(private seam retires `S75`; one-entry surface map retires `S70`).

## Option C — Narrow to Linux/POSIX only now, defer Windows

Drop Proof 4 and release units involving Windows; ship POSIX first.

**Viable only if the operator changes the portability requirement and the
threat model.** It is attractive — Proof 4 is the single largest unknown and
`S79`/`S80` are both Windows-specific — but this is a Windows-hosted
development workspace, so a POSIX-only reader would not exercise the dogfood
path locally. This is a genuine product decision, not a technical shortcut, and
Stage will not presume it. If the operator takes C, it composes with B rather
than replacing it: the same governance reset applies to a smaller scope.

## Option D — Cancel the custom secure reader, accept ordinary containment

Drop the bespoke reader; use ordinary path validation and reads.

**Viable only with an explicit, recorded risk acceptance and threat-boundary
reduction.** It is by far the cheapest — it deletes the entire hardest
subsystem, all of `S53`-`S55`, `S71`, `S75`, `S77`, `S79`, `S80`, and Proofs 3,
4, 5 and 6 — and it deserves serious consideration precisely because the
resolver reads *this repository's own backlog files* under an assumed-trusted
workspace root. If that trust boundary is real, the custom reader may be
defending against an adversary that does not exist in the threat model. But
cancelling it is a security decision with a named owner, not an engineering
convenience, and `S77` already shows the current design does not close hardlink
aliasing anyway.

## Trade-off table

| | **A: patch + attempt 12** | **B: reset + proofs + split** | **C: POSIX-only now** | **D: cancel secure reader** |
|---|---|---|---|---|
| Changes the instrument | No | **Yes** | Partly | Partly |
| Evidence type | Prose review | **Execution** | Execution (POSIX) | Execution (reduced) |
| Near-term cost | ~1 revision + 1 review | **9.25h proofs + charter** | ~6h proofs + charter | ~3h proofs + charter |
| Blocked work released | None | **All, in bounded units** | POSIX subset | Most |
| Termination guaranteed | **No** | **Yes** — stop conditions | Yes, narrower | Yes |
| Retires finding families | No | **Yes, by construction** | Windows families only | Reader families only |
| Requires operator product decision | No | Scope + matrix approval | **Yes** — portability | **Yes** — risk acceptance |
| Requires threat-model change | No | No | **Yes** | **Yes** |
| Residual risk | **High** — loop continues | Low | Medium — Windows deferred | **Medium-high** — containment reduced |
| Recommended | No | **Yes** | Only with C1 answered | Only with C1 answered |

Options C and D are not independent of B. Each is a *scope* answer to the
threat-model question; whichever scope the operator picks, B's governance and
proof machinery is how it gets executed.

---

# Part 6 — Success criteria

The strategy has worked if all of the following hold.

1. **No new plan revision is written until all required proofs pass**, or the
   operator explicitly changes the architecture.
2. **The acceptance matrix, rubric and personas are frozen before evaluation
   begins.**
3. **Each release unit is <= 6 tasks and <= 8 hours and is independently
   valuable.**
4. **Blockers decline monotonically across at most two remediation revisions.**
5. **No repeated finding family appears without proof of a remediation
   regression** — a family recurring is a signal the proof was wrong, and is
   handled as an architecture reopen.
6. **Authority and state are single-source and mechanically consistent** —
   verified by script, not by a reviewer reading sixteen carriers.
7. **Publication, execution and activation gates are distinct**, with
   separately stated criteria.
8. **The future review ends in publish, split/spike/re-charter, or
   defer/cancel — never in an unbounded retry.**

Criteria 1, 4, 5 and 8 are the ones that directly falsify the failure mode
observed across attempts 07-11.

---

# Part 7 — Unresolved operator decisions

This deliberation cannot proceed past Phase 0 without these four answers. They
are listed in dependency order.

## C1 — Threat model and platform mandate

**What is the required threat model, and are both Windows and POSIX mandatory
in the first release?**

Gates: Options C and D, Proof 4 (120m — the largest single budget), release
unit C's existence, and findings `S77`, `S79`, `S80`. Nothing else can be
sized until this is answered.

## C2 — Release-unit split

**Do you accept the recommended A / B / C / D release-unit split?**

Gates: Phase 2, the shape of the DAG, and whether 8-hour units are achievable.

## C3 — Migration and the fate of 187-S

**Do you approve migration to the acceptance matrix and structured review
index, and the retirement or re-charter of `187-S`?**

Gates: Phase 2 and Phase 3. Note this is explicitly *retire or re-charter*, not
*patch* — `187-S` cannot be brought within budget by editing carriers.

## C4 — `P2` publication policy and reviewer routing

**Which `P2` publication policy, and who is reviewer lead with what routing?**

Gates: Phase 4, section 3.7's publication gate, and section 3.6's
route-stability rule. Relevant input:
`.autoharness/config.yaml` declares no `model_routing.anchor_review` key, which
is why attempt 11 ran the Architecture Strategist same-model as a declared
degradation. If anchor routing is wanted for the next epoch, it must be
configured *before* the epoch opens, because changing it mid-epoch pauses the
epoch under 3.6.

---

## Recommendation

**Adopt Option B.** Freeze the current artifacts as a diagnostic record,
charter the acceptance matrix, run the nine bounded proofs, and re-slice into
release units — with the scope of that work set by the operator's answer to C1.

`decision_status` remains **`exploring`** and `promoted_to` remains **`none`**.
No plan, queue item, shipment or carrier is linked to this artifact. It becomes
a decision of record only when the operator resolves C1 through C4.

## Cross-references

* Plan: `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` (revision 12, `0806b601`)
* Verdict manifest: `docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md` (revision 21)
* Terminal attempt: `docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-11.md`
* Prior attempts: `...-plan-review-attempt-07.md`, `-08`, `-09`, `-10` under `docs/reviews/review-history/`
* Governing decision: `docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md` (revision 9)
* Policy: `.github/policies/workflow-policies.md` (P-004)
* Actor: `.github/skills/harness-architect/SKILL.md` (Step 5.2)
* Manifest bindings: `.autoharness/harness-manifest.yaml` (`TEST_COMMAND`, `UNIMPLEMENTED_MARKER`)
* Learnings: `docs/compound/093-S-review-loop-convergence.md`,
  `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`,
  `docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md`,
  `docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md`,
  `docs/compound/097-S-canonical-unittest-gate.md`
