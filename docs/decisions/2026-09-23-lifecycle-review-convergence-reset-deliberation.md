---
title: "Lifecycle review convergence reset: Option B governance reset with proportionate Option D containment"
description: "Stage deep decision, approved by the operator on 2026-09-23, issued after the eleventh consecutive FAIL/BLOCK verdict against the Ship pre-task harness-generation lifecycle plan. Attempts 07-11 reviewed revisions 8-12; each closed most of its predecessor's findings and each raised a fresh set, so the loop showed no path to zero. Diagnoses the root cause as plan review being used as implementation research over an unbuilt three-subsystem shipment. Decides Option B (freeze the current artifacts as a diagnostic record, charter a versioned acceptance matrix, answer the open questions with bounded executable proofs, and re-slice 187-S into independently valuable release units) combined with the proportionate Option D containment scope. That scope assumes an operator-controlled local workspace with no hostile concurrent filesystem actor. It requires ordinary static containment on actual Windows and Linux, bounded reads and explicit failure, and it makes no TOCTOU or hardlink-alias claim. Seven bounded proofs, defined in the companion proof-entry charter, replace the retired native-security proof portfolio. Mutates no plan, review, backlog or shipment state."
doc_type: decision
source: docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md
date: 2026-09-23
decision_date: 2026-09-23
status: decided
decision_status: decided
decision_approval: operator
decided_option: "B+D"
containment_scope: proportionate-ordinary-static-containment
platform_mandate: [windows, linux]
depth: deep
deciders: operator, Stage
revision: 2
revision_note: "Revision 2 records the operator's 2026-09-23 decision. Revision 1 (commit 082df7b2) was the exploring deliberation; git history retains it."
promoted_to: none
promoted_to_note: "Remains none until Phase 1 proof entry. This decision does not create, edit or retire any plan, revision 13, attempt 12, backlog item, carrier or shipment. The companion proof-entry charter defines proof entry."
linked_artifacts:
  - docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
branch: chore/stage-176-s-workflow-defects
head_at_deliberation: 246d8b73
head_at_decision: 082df7b2
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
resolved_decisions: [C1]
open_decisions: [C2, C3, C4]
state_mutation_performed: false
review_performed: false
retrieval_state: degraded
policies: [P-001, P-002, P-004, P-005, P-006, P-009, P-010, P-012, P-016, P-017, P-020]
labels:
  - deliberation
  - deep
  - decided
  - review-convergence
  - governance-reset
  - proof-first
  - proportionate-containment
  - ship-lifecycle
---

# Lifecycle review convergence reset

## Decision

On **2026-09-23** the operator approved **Option B**: a governance reset, a
proof-first rebaseline and a release-unit split. The operator combined it with
the **proportionate Option D** containment scope. The operator made this choice
after challenging the adversarial threat assumptions that had driven the
reviewed plan's secure-reader design.

| Element | Decision |
|---|---|
| Governance | Option B. The current artifacts are frozen as a diagnostic record. A charter and a versioned acceptance matrix precede any proof. Proofs precede any plan. Review runs under frozen rubric, personas and route, with the stop rules in the governance section below |
| Threat model | The operator controls the local development workspace. There is no hostile concurrent filesystem actor |
| Containment | Static containment within the configured workspace root and the autoharness root. Lexical rejection of invalid paths. Rejection of any path whose resolved target lies outside its root, including ordinary symlink and junction escapes. Bounded reads with explicit, closed failure codes |
| Non-claims | No TOCTOU or race resistance, no hardlink alias resistance, and no resistance to hostile concurrent mutation are claimed |
| Platforms | Windows **and** Linux, both first-release functional support, verified by tests executed on each actual operating system. There is no POSIX-only first release |
| Removed obligations | `NtCreateFile` `RootDirectory` descent and other handle-relative traversal, a public `TraversalAdapter`, and native-platform security spikes |
| Proof portfolio | Seven bounded proofs, defined in `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` |
| Resolved | C1 (threat model and platform mandate) |
| Still open | C2 (release-unit split), C3 (migration and the fate of `187-S`), C4 (`P2` publication policy, reviewer lead and routing). Each is a bounded proposal pending future operator approval |

`promoted_to` stays `none` until Phase 1 proof entry. The intended next Stage
step is bounded proof experiments, taken only after the charter is coherent.
`187-S` remains `queued` and is **not** claim-ready as a result of Phase 0.

## Question

The Ship pre-task harness-generation lifecycle plan was independently reviewed
eleven times and failed eleven times. The operator asked for the loop to be
paused and for a coherent strategy to replace it:

> **What should replace the plan-revise-review loop, given that five
> consecutive revisions each closed most of their predecessor's findings and
> each raised a fresh set, so the loop has no demonstrated path to zero?**

## Decision chronology

| Step | Event |
|---|---|
| 1 | Attempt 11 recorded a terminal FAIL against revision 12 at `246d8b73` |
| 2 | Stage opened this deliberation as `exploring` at `082df7b2`. It recommended Option B and left four operator decisions open, the first being the threat model and platform mandate |
| 3 | The operator challenged the adversarial threat assumptions behind the handle-relative, race-resistant reader design |
| 4 | The recommendation was refined to Option B governance combined with a proportionate Option D reader: portable, ordinary filesystem operation for an operator-controlled development workspace on Windows and Linux, rather than a race-proof boundary against hostile junction or hardlink manipulation |
| 5 | The operator selected that combination on 2026-09-23. C1 is resolved; C2, C3 and C4 remain open |

## What this decision does not do

Stage's role boundary (P-010) and the operator's instruction both constrain
this session. None of the following is authorized or performed:

| Not done | Reason |
|---|---|
| Edit the lifecycle plan or create revision 13 | Revision 13 would repeat the failure mode diagnosed here |
| Run a review or create attempt 12 | The manifest records `attempt_12_authorized: false`; Stage does not self-authorize review |
| Edit the verdict manifest or any attempt artifact | Attempt artifacts are immutable; the manifest is the review skill's authority |
| Record the `HALTED_NONCONVERGENT` transition | It is a manifest mutation, performed once by review-skill authority on operator instruction |
| Edit the governing decision (revision 9) | Amending it is a separate, operator-approved act |
| Create, edit, claim, retire or re-charter any backlog item, carrier, shipment or stash entry | `187-S` and `181-F` remain exactly as they are; retirement or re-charter is C3 |
| Write production code, templates, tests, schemas, configuration or the harness manifest | Stage does not write production surfaces |
| Run executable proofs or native security spikes | Proofs are Phase 1; native security spikes are removed from scope |
| Touch the pre-existing P-004 locks under `docs/plans/` and `docs/reviews/` | They belong to blocked P-004 work, and P-004 follow-up is out of scope |
| Push, open or comment on anything in GitHub | No network mutation |
| Modify dirty or untracked working-tree files | All pre-existing dirty and untracked artifacts are preserved |

The only repository change is this rewrite and the companion charter, in one
commit.

## Evidence base and retrieval conditions

Every claim below was read directly from the repository on branch
`chore/stage-176-s-workflow-defects`: the deliberation at `246d8b73` and the
decision at `082df7b2`.

### Retrieval degradation (P-012)

| Capability | State | Effect |
|---|---|---|
| Indexed knowledge retrieval (engram) | Circuit-open; not retried | No semantic search. Compound learnings were located by directory listing and read by exact path |
| Intercom visibility | Unavailable | No phase broadcasts. Operator visibility is limited to this artifact and the session summary |
| Graphtor-docs | Unavailable | Documentation questions were resolved by direct reads |
| backlogit MCP | Available | Index sync reported 1472 items; the shipment read and the Stage checkpoint enumeration (all resolved, none active) succeeded |

This degradation is a session condition. It is not a defect in the strategy or
in the reviewed plan. It narrows confidence about undiscovered related work,
and it does not weaken any cited finding, since each was read from its source
file.

### Primary evidence

| Artifact | Exact state observed |
|---|---|
| Lifecycle plan | Revision **12**, commit `0806b601` |
| Verdict manifest | Revision **21**; `verdict: FAIL`, `disposition: FAIL-BLOCKING-P1`, `decision: BLOCK` |
| Finding counts at attempt 11 | `P0` 0, `P1` 8, `P2` 4, `P3` 1; 13 merged, 8 blocking |
| Publication gate | `portfolio-strict-zero-p0-p1-p2`; `publication_eligible: false` |
| Attempt 12 | Does not exist; `attempt_12_authorized: false` |
| Terminal attempt | Attempt 11, `review_terminal: true`, commit `246d8b73` |
| Governing decision | Revision **9**, `status: decided`, `promoted_to: plan` |
| Shipment `187-S` | `status: queued`; covering feature `181-F` plus 16 live tasks; `181.001-T` archived and not a live member |
| Live P-004 | `.github/policies/workflow-policies.md`: canonical whole-suite command, per-test marker correlation, closed list of rejected outcomes |
| Installed actor | `.github/skills/harness-architect/SKILL.md` Step 4 item 3 and Step 5.2 require `raise NotImplementedError("...")` stubs and per-test marker attribution |
| Manifest bindings | `.autoharness/harness-manifest.yaml:472` `TEST_COMMAND`; `:473` `UNIMPLEMENTED_MARKER`; `:237-239` the `harness-architect` surface entry |
| Ship surfaces | `templates/agents/_ship.agent.md.tmpl` Step 2 (line 326) "runs once, up front - not in a loop"; the installed mirror `.github/agents/_ship.agent.md` has a different step structure and no `harness-architect` reference |
| Containment norms | `.github/instructions/constitution.instructions.md` sections III and IV: operations resolve within the configured root; traversal and symlink escapes are refused |
| Reviewer routing | The working configuration, inspected read-only, declares no `model_routing.anchor_review` key |
| Pre-existing locks | `docs/plans/.2026-09-18-p004-observation-gate-plan.md.lock` and `docs/reviews/.2026-09-18-p004-observation-gate-plan-review.md.lock`, both untouched |

### The 187-S budget

The sum of each of the sixteen live carriers' implementation and verification
budget lines:

```text
181.002  90    181.008 105    181.013 100
181.003  90    181.009  90    181.014 100
181.004  60    181.010 100    181.015 110
181.005 110    181.011 110    181.016  90
181.006  75    181.012  90    181.017  75
181.007  90
                       total = 1485 minutes = 24.75 hours
```

That is sixteen serial tasks and 24.75 engineering hours in **one** shipment,
and none of them has produced executable code. The size composition is 15 x `S`
and 1 x `XS`; archived `181.001-T` is the only `M`.

## The convergence record

Each row is read from that attempt's own immutable frontmatter.

| Attempt | Revision reviewed | Verdict | New findings raised | Blocking |
|---|---|---|---|---|
| 07 | 8 | FAIL / BLOCK | `S14`-`S25` (12) | P0 + P1 |
| 08 | 9 | FAIL / BLOCK | `S26`-`S34` (9) | P0 + P1 |
| 09 | 10 | FAIL / BLOCK | `S35`-`S52` (18) | 24 |
| 10 | 11 | FAIL / BLOCK | `S53`-`S66` (14) | 14 (`P1` 14, `P2` 2) |
| 11 | 12 | FAIL / BLOCK | `S69`-`S81` (13) | 8 (`P1` 8, `P2` 4, `P3` 1) |

**Blockers are declining:** 24, then 14, then 8. Revision 12 is genuinely
better than revision 11. Attempt 11 closed eleven attempt-10 findings outright
and partially closed three more.

**The discovery rate is flat:** each revision raised 12, 9, 18, 14 and then 13
new findings. A loop converges when the discovery rate falls, not when the
backlog of known defects is worked off.

The mechanism shows in the attempt-11 record. Revision 12 closed `S61` by
enumerating eleven member reason codes, which exposed `S76`, because the
manifest reason codes never got the same treatment. It closed `S56` by naming
modules and types, which exposed `S75`, because `TraversalAdapter` became
public without a contract. It closed `S66` by splitting into sixteen tasks,
which exposed `S80`, because the complexity labels were chosen to satisfy the
split rather than derived from the work.

**Each revision turns an unanswered question into a more precisely stated
unanswered question.** That is what research looks like, not convergence.
`docs/compound/093-S-review-loop-convergence.md` recorded the same shape at
PR #229: fresh containment and safety-critical code invites deep, iterative
scrutiny, and without an explicit stop condition the loop does not converge in
any bounded number of cycles.

## Architecture diagnosis

### Root cause: plan review used as implementation research

A plan review asks whether a plan is implementable as written. It is a cheap
gate for catching structural mistakes before code exists.

For five revisions it was asked instead to establish the correct design of a
cross-platform secure filesystem reader, a backlog resolver with a closed
reason taxonomy, and a Ship lifecycle activation. That is a research question,
and prose review is a poor instrument for it, because prose cannot fail. The
only reliable way to falsify a claim about how a platform resolves a junction,
or how a test runner classifies an exception, is to execute it on that
platform. Attempt 11 confirmed by directory inspection that the planned modules
do not exist: eleven reviews, 24.75 hours of planned work and 81 findings, with
zero executed lines.

### Recurring issue families

Four families persisted across revisions in changed form. They signal
unresolved architecture, not careless editing.

| Family | Early form | Form at attempt 11 | Why it recurs | Disposition under B+D |
|---|---|---|---|---|
| RED / P-004 evidence ownership | `S14` (attempt 07, `P0`): wrong red-phase command in the actor | `S69` (marker exception type, characterization carve-out); `S78` (command not pinned to the canonical form) | The plan asserts the actor is conformant and keeps actor changes out of scope, while specifying an evidence shape the actor rejects | Proof A settles it by execution |
| Registry and reason taxonomy closure | `S61`, `S63` (attempt 10) | `S70` (surface registry undefined); `S76` (global manifest reason codes not enumerated) | One enum is totalized at a time; a taxonomy closes only when the whole classification pipeline closes at once | One-entry `SurfaceSpec`; Proof C |
| Ship placement and checkpoint restore | `S58`, `S59` (attempt 10) | `S73` (per-task invariant against pre-loop anchors); `S72` (verdict consumed by exit status) | The per-task contract is anchored at a step whose own text says it runs once, up front | Proofs B and E |
| Secure traversal containment | `S53`, `S54`, `S55` (attempt 10) | `S75` (undefined `TraversalAdapter`); `S77` (hardlink aliasing, unreachable `OUTSIDE_TRUST_ROOT`); `S79` (Windows reparse flags) | Race-resistant containment properties are platform facts that prose can assert indefinitely | Rescoped to ordinary containment; Proofs D and G |

### Fresh defects the revisions introduced

| Defect | Finding | What went wrong |
|---|---|---|
| Mutually incompatible budgets | `S71` (`P1`) | `max_files=256` (plan line 78) against a membership bound of `1..512` (line 144), with queue and archive candidates consulted and then re-observed. It breaks near `N = 63`; `187-S` itself fits, so dogfooding would never surface it |
| Exit-code aliasing | `S72` (`P1`) | Ship maps exit 1 to `NO_HARNESS` and exit 2 to `UNRESOLVED` without first requiring a resolver document, so a crashed resolver is indistinguishable from a clean verdict |
| Ambiguous checksum procedure | `S74` (`P1`) | Plan line 231 says "the exact installed bytes" and names no method, contradicting `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md` section 1 |
| Unearned public adapter debt | `S75` (`P1`) | `TraversalAdapter` and `adapter=None` were made public before any implementation constrained them; a caller-supplied adapter could defeat containment while results still report success |
| Unsupported estimates | `S80` (`P2`) | The two NT-API tasks are labelled `S` / `medium` with no codebase precedent for NT structure marshalling |

The common pattern: **abstractions were published before anything earned
them.**

### Revision 12 is a requirements inventory

As an inventory it is good. But it is the wrong artifact to hand to Ship, and it
bundles three independent subsystems:

1. **A containment reader.** Revision 12 specifies it as handle-relative,
   no-follow traversal with NT API marshalling, identity and version snapshots,
   and budget accounting. Under B+D it becomes a portable reader built on
   ordinary path resolution with bounded reads.
2. **A backlog and manifest resolver.** Membership, surface classification,
   manifest snapshot, reducer, digest, versioned result schema and CLI. This is
   pure domain logic, testable in memory.
3. **A Ship lifecycle activation.** Template, mirror and manifest checksum
   changes: one atomic change to the live agent.

Bundling them blocks the whole unit on its least-understood part and forces
every review to hold all three in view at once. That is how a reviewer produces
13-18 findings per pass.

### Stable boundaries

* **An internal containment helper with no adapter seam.** It resolves paths
  with the standard library, compares them against resolved roots, and reads
  within fixed bounds. There is no public or caller-supplied adapter, and any
  test seam stays private.
* **A resolver domain with a closed `SurfaceSpec` map, a reducer and a
  digest.** The map is data: surface ID to installed artifact path to expected
  template, with one exact match predicate.
* **A versioned result schema** as the single interchange contract.
* **A thin CLI** that parses, calls, serializes exactly one document, and exits
  with that document's own code.
* **Ship as a consumer of a validated document**, never of a process status.

Two corollaries remove work:

* **Support exactly one surface initially: `harness-architect`.** All sixteen
  live tasks declare `harness-surface:harness-architect`, and the manifest
  already tracks that surface with a template. A one-entry map with an explicit
  `SURFACE_UNSUPPORTED` outcome for everything else answers `S70` completely.
* **Delete the unearned public abstractions:** the public `TraversalAdapter`,
  the public `adapter=` parameter, and the general surface registry. This
  retires `S75` by construction.

### The architectural rule

> **No future plan is written until the required proofs pass. When a proof
> fails, the architecture or charter decision changes. A failure never
> triggers another prose remediation.**

This rule makes the loop terminate. Today a failure produces a revision, a
revision produces new findings, and new findings produce a failure. Under this
rule a failure produces a changed design, and designs have a finite number of
viable shapes.

## Containment scope (proportionate Option D)

### Threat model

The resolver reads this repository's own backlog, manifest, template and
installed files, inside a development workspace that the operator controls. The
threat model admits **no hostile concurrent filesystem actor**. The hazards it
does admit are ordinary ones: a malformed or escaping path, a static link that
points outside the workspace, oversized or unexpected input, and a target that
is not a regular file.

### Required properties

1. **Static containment roots.** The configured workspace root and the
   autoharness root (`.autoharness/`), each resolved once per run.
2. **Lexical rejection** of invalid paths before any filesystem access: empty,
   NUL-bearing, absolute where relative is required, and escaping `..`. On
   Windows this also covers drive-relative, UNC and device-prefixed forms,
   alternate data streams, reserved device names, and trailing dots or spaces.
3. **Resolved-path rejection.** A target whose final resolved path lies outside
   its root is rejected, including ordinary symlink and junction escapes
   present at read time. Links that resolve inside the root are allowed. On
   Windows, root comparison is case-insensitive.
4. **Bounded reads.** Per-file byte, total byte and file-count limits, each
   with its own explicit exhaustion code. There is no silent truncation.
5. **Explicit failure.** Every rejection maps to a closed failure code. There
   is no silent fallback and no partial success.

### Non-claims

The reader does **not** claim TOCTOU or race resistance, hardlink alias
resistance, or resistance to hostile concurrent mutation. No later plan, task,
test name or review response may claim these properties. Adding any of them as
a requirement is a threat-model change and requires a re-charter.

### Platform mandate

Windows and Linux are both first-release platforms, and each is verified by
tests executed on that actual operating system. Mocked or simulated platforms
are not evidence. A POSIX-only first release is not adopted, because this is a
Windows-hosted development workspace and the dogfood path must run locally.

### Risk grading

Risk is graded per hazard class. A single blanket grade is not used, because
it would conflate classes that are mitigated with classes that are outside the
model.

| Hazard class | In model | Treatment | Residual risk |
|---|---|---|---|
| Lexical traversal and malformed paths | Yes | Lexical rejection | Low |
| Static symlink or junction escape present at read time | Yes | Resolved-path rejection | Low |
| Oversized or excess input | Yes | Bounded reads with explicit codes | Low |
| Non-regular target or reserved device name | Yes | Explicit rejection | Low |
| Concurrent swap between check and use (TOCTOU) | No | Not defended; recorded non-claim | Accepted by the operator as outside the model |
| Hardlink alias to outside content | No | Not defended; recorded non-claim. The retired handle-relative design did not close this vector either (`S77`) | Accepted by the operator as outside the model |
| Hostile local process | No | Not defended. The workspace's advisory lock skill makes the same bound explicit | Accepted by the operator as outside the model |

If the workspace trust boundary changes (for example, shared or multi-tenant
hosts, or untrusted checkouts), the accepted classes re-enter the model through
a re-charter.

### Normative alignment

Constitution section III requires every filesystem operation to resolve within
the configured workspace root and requires path traversal attempts to be
rejected. Section IV refuses paths that resolve outside the tree through
absolute paths, `..`, symlinks or environment expansion. The required properties
above implement those statements as written. This decision does not amend or
reinterpret the constitution. If a later review contends that the constitution
requires race-proof guarantees, that contention goes to the operator as a
constitutional question. It is not a finding to be absorbed into a plan.

### Disposition of reader-family findings

| Finding | Subject | Disposition |
|---|---|---|
| `S53` | Handle-relative traversal | Retired from scope: handle-relative traversal is no longer required |
| `S54` | Byte cap | Retained as a bounded-read requirement; Proof G |
| `S55` | Same-size mutation between reads | Out of model (concurrent mutation); recorded non-claim |
| `S71` | Budget incompatibility | Retained; Proof D |
| `S75` | Public `TraversalAdapter` | Retired by construction: no adapter seam |
| `S77` | Hardlink aliasing; unreachable `OUTSIDE_TRUST_ROOT` | Hardlink half becomes a recorded non-claim; the outside-root half is answered by resolved-path rejection with a closed code; Proof G |
| `S79` | Windows reparse flag precedence and final-path check | Native flag half retired; the Windows junction and symlink behaviour is tested functionally in Proof G |
| `S80` | NT-API task sizing | Retired: no NT-API tasks remain |

These dispositions describe the future scope. The attempt-11 record itself is
not edited.

## Proof-first work

This decision authorizes no production implementation. The questions are
answered by a portfolio of **seven** bounded, executable proofs. Each has one
narrow question, fixed time and file bounds, and a pass/fail criterion decided
by running something. Proof code is disposable. Its only durable output is an
answer and the evidence for it.

| Proof | Question | Budget | Settles |
|---|---|---|---|
| A | Live P-004 canonical whole-suite command plus a unique `NotImplementedError` marker: acceptance and every rejected failure mode | 60m, 3 files | `S69`, `S78` |
| B | CLI authenticity: status plus exactly one schema-valid document | 60m, 2 files | `S72` |
| C | One-entry `SurfaceSpec` and a total member and manifest reason truth table with schema parity | 75m, 2 files | `S70`, `S76` |
| D | One budget equation for all admitted members, candidates and rechecks | 45m, 1 file | `S71` |
| E | Ship per-task actor placement and a checkpoint-first state machine against the exact template and mirror | 60m, 2 files | `S73`, placement half of `S72` |
| F | Raw staged and HEAD checksum replay of the established compound learning | 30m, 1 script in a disposable repository | `S74` |
| G | Portable ordinary-path containment functional tests on actual Windows and Linux, including static symlink and junction escapes and read bounds | 90m, 2 files | `S54`, `S77`, `S79` (functional) |

Total: **420 minutes (7.0 hours), at most 13 disposable files.** The charter
fixes each proof's setup, pass criteria, required rejections, failure routing
and host requirements.

Relative to the retired nine-proof portfolio, the POSIX traversal, Windows
`NtCreateFile` traversal and adapter-authority proofs are removed with their
native mechanisms. Proof G replaces them with one functional containment proof
that runs on both platforms. The budget, taxonomy, CLI, P-004, state-machine
and checksum proofs carry forward as Proofs D, C, B, A, E and F.

A `FAIL` returns to architecture or charter. It never returns to a prose
rewrite. `BLOCKED` (for example, when no Linux host is available) goes to the
operator and never counts as `PASS`.

## Governance reset

### Immediate freeze

* No revision 13, no attempt 12, no carrier synchronization, no remediation.
* Revision 12 and attempts 07 through 11 are preserved unchanged as the
  diagnostic record.
* The `HALTED_NONCONVERGENT` state is recorded once, in the verdict manifest,
  by review-skill authority on operator instruction. This decision does not
  record it, and no other artifact restates it.

### Charter and versioned acceptance matrix

The companion charter fixes scope, threat model, platforms and budget. It also
fixes acceptance matrix **PE-1.0**. Every row carries a normative source, a
pass criterion, evidence, a violation severity and a deferral status, in nine
categories:

| Category | What it fixes |
|---|---|
| `AUTH` | Who may authorize what; role boundaries |
| `SCOPE` | What is in and out; which files may be touched |
| `FLOW` | Control flow, ordering, state transitions |
| `INTERFACE` | Public and private surfaces, seams |
| `SAFETY` | Containment, threat model, fail-closed behaviour |
| `DATA` | Schemas, enums, taxonomies, digests |
| `TASK` | Decomposition, sizing, the 2-hour rule |
| `EVIDENCE` | What proves a row satisfied |
| `ACTIVATE` | Rollout, atomicity, rollback |

PE-1.0 is frozen **for proof entry only**. The implementation acceptance matrix
is drafted from proof evidence and ratified after proof exit, before any new
review epoch opens. Against a frozen matrix, a requirement that is not a row is
a change request, not a blocker.

### One authority chain

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

Each fact lives in exactly one place. Today the same verdict is restated in the
manifest, the attempt artifact, the shipment description and sixteen carriers,
which gives authority sixteen extra places to drift. Removing those restatements
belongs to a later migration (C3).

### Issue taxonomy and what may block

| Class | Meaning | Blocks |
|---|---|---|
| `CRITERION` | Violates a frozen matrix row | **Yes** |
| `EVIDENCE` | Matrix-required evidence is missing | **Yes** |
| `CONSISTENCY` | Two artifacts disagree | No; mechanical check |
| `RISK` | Hazard noted, no row violated | No |
| `CHANGE` | New requirement not in the matrix | No; change control |
| `PROCESS` | Workflow or hygiene observation | No |
| `DUPLICATE` / `CHILD` | Restates or narrows an existing finding | No |

### Finding identity and closure

* Stable finding IDs are tied to matrix rows, so identity survives revisions.
* Each finding closes independently, on named evidence.
* Residue after a partial close gets an explicitly linked child.
* Nothing is carried forward, as open or as closed, without revalidation.

### Reviewer stability

Freeze before the epoch begins: lead reviewer, rubric version, persona set,
severity mapping and routing. Then run one initial full review, delta reviews
against changes only, and one final full consistency pass. **A reviewer route
change pauses the epoch.** Attempt 11 ran with a declared same-model
degradation for the Architecture Strategist persona because no anchor route is
configured. A rubric executed by a different route is a different rubric. The
lead and the routing are **not selected** by this decision (C4).

### Three distinct gates

| Gate | Question | Criterion |
|---|---|---|
| Publication | Is the contract sound enough to publish? | Zero admitted `P0` and `P1`. The **proposed default** is that only matrix-critical `P2` blocks (C4) |
| Execution (implementation) | May implementation begin? | All required proofs pass and the implementation matrix is ratified |
| Claim / closure | May this ship and close? | Ordinary runtime, CI, P-002/P-004 and P-020 gates |

A blanket zero-`P2` rule is not used. The current
`portfolio-strict-zero-p0-p1-p2` gate puts `S81`, an argument-passing style
inconsistency rated `P3`, in the same blocking bucket as a containment defect.
Criticality is predesignated per matrix row, not argued per finding.

### Remediation budget

| Limit | Value |
|---|---|
| Consolidated revisions per epoch | At most **2** |
| Local remediation cycles after a review | At most **1** |
| New API, subsystem, threat class or platform mechanism | Requires a **re-charter** |
| Implementation tasks per shipment | At most **6** |
| Engineering hours per shipment | At most **8** |
| Budget overrun or repeated failure | Escalates per P-013.6 and ends in a permitted outcome |
| Contract growth over 20% | Ends the epoch |

`187-S` exceeds the task limit by 167% (16 against 6) and the hour limit by
209% (24.75 against 8).

### Stop conditions and permitted outcomes

Stop the epoch immediately if **any** of these occurs:

* blockers do not decline across revisions;
* newly admitted findings are at least as many as findings closed;
* scope, rubric or reviewer route changes mid-epoch;
* an authority mismatch is found between artifacts;
* a new subsystem turns out to be required;
* any remediation budget limit is exceeded;
* a second remediation fails.

On stop, the permitted outcomes are **split**, **spike**, **re-charter / new
epoch**, **explicit risk acceptance**, **defer** or **cancel**. Another attempt
is not a permitted outcome.

### Epoch identity

Epochs are named by a token derived from the subject digest, matrix version and
rubric version, for example **`LIFECYCLE-E2-R1`**, never by attempt number. The
attempt 07-11 record belongs to a closed epoch.

## Recovery phases

### Phase 0 - operator reset (complete with this decision and the charter)

The operator approved B+D and resolved C1. The companion charter fixes PE-1.0
and the proof portfolio. The current artifacts are frozen as the diagnostic
record.

### Phase 1 - bounded proof portfolio (gate: proof exit)

Run the seven proofs under the spike skill, in one recorded, time-boxed P-016
spike worktree. A failed proof reopens architecture or charter; it does not
open a remediation cycle.

### Phase 2 - release-unit re-slice (gate: implementation matrix ratified)

The following is a **bounded proposal (C2)**, pending operator approval:

| Unit | Content | Independent value |
|---|---|---|
| A | Actor and P-004 conformance, plus per-task lifecycle semantics | The evidence contract becomes true and testable |
| B | Resolver, one-entry `SurfaceSpec`, result schema and CLI | A working, callable resolver |
| C | Portable ordinary-containment reader on Windows and Linux; may fold into B if B stays within budget | Required containment and bounds |
| D | Final Ship activation: template, mirror and manifest checksum in one task and one commit | The lifecycle goes live |

Each unit must satisfy the remediation budget: at most 6 tasks, at most 8
hours, independently valuable. Nothing is harvested before the implementation
matrix is ratified. Whether `187-S` is **retired or re-chartered** (never
patched) is **C3**.

### Phase 3 - compact active plan (gate: deterministic consistency checks)

Generate a compact plan from the ratified matrix and proof results. Carriers
are minimal generated projections. Cross-artifact consistency is checked by
script before review.

### Phase 4 - new review epoch (gate: publication)

The epoch opens with the lead, rubric, personas and route fixed (C4). At most
one local remediation cycle is allowed. Any architectural or new-mechanism
finding routes back to Phase 1 or Phase 0.

### Phase 5 - implementation (gate: ordinary runtime, closure and P-020)

1. Inert implementation of foundations: code lands, nothing is wired.
2. Atomic template, mirror and manifest activation in one task and one commit.
3. One dogfood task proving the exact marker transition from RED to GREEN.
4. Ordinary runtime, closure and P-020 gates.

## Options considered

### Option A - patch revision 12 and run attempt 12

**Rejected.** Attempts 8 through 11 each did exactly this, and each produced
9-18 fresh findings. Revision 13 would keep the same three subsystems, the same
prose instrument, the same unexecuted code and the same open questions.

### Option B - governance reset, proof-first rebaseline, release-unit split

**Selected, as the governance frame.** It is the only option that changes the
instrument. Open questions become decidable by execution, review runs against a
frozen contract, and the stop conditions guarantee a terminal outcome other
than another attempt. Under revision 12's native containment scope, B's proof
portfolio needed nine proofs and 555 minutes, including `NtCreateFile`
traversal and adapter-authority work with no codebase precedent.

### Option C - POSIX-only first release, Windows deferred

**Not adopted.** C was a scope answer that composed with B: it dropped the
Windows proof and deferred Windows support to a later epoch. The C1 answer
mandates Windows and Linux in the first release. This is also a Windows-hosted
workspace, where a POSIX-only reader would not exercise the dogfood path. Once
the native mechanisms leave scope under D, the Windows cost that motivated C
largely disappears as well.

### Option D - proportionate ordinary containment in place of the bespoke race-resistant reader

**Selected, as the containment scope of B.** D retires handle-relative
traversal, NT marshalling and the public adapter. It keeps static containment,
lexical and resolved-path rejection, bounded reads and explicit failure, on
both platforms. It rests on an explicit threat-model statement recorded by the
operator: an operator-controlled workspace with no hostile concurrent actor. It
names its non-claims instead of leaving them implicit. It retires `S53`, `S75`
and `S80` and the native half of `S79`, and it turns the hardlink half of `S77`
into a recorded non-claim. The budget, taxonomy and CLI questions still need
their proofs.

### Trade-off table

| | A: patch + attempt 12 | B with revision-12 native scope | B + C: POSIX-only first | **B + D: proportionate (selected)** |
|---|---|---|---|---|
| Changes the instrument | No | Yes | Yes | **Yes** |
| Evidence type | Prose review | Execution, including native API proofs | Execution, POSIX only | **Execution, portable on both OSes** |
| Proof cost before any plan | None, but one revision and one review per cycle with no bound | 9 proofs, 555m (9.25h) | 8 proofs, 435m (7.25h), plus a later Windows epoch | **7 proofs, 420m (7.0h)** |
| First-release platforms | Windows and Linux (as planned) | Windows and Linux | Linux only | **Windows and Linux** |
| Native security mechanisms | Planned, unproven | `NtCreateFile`, handle-relative POSIX, adapter authority | Handle-relative POSIX, adapter authority | **None** |
| Termination guaranteed | No | Yes, by stop conditions | Yes | **Yes** |
| Finding families retired by construction | None | `S70`, `S75` | `S70`, `S75`; Windows findings deferred | **`S70`, `S75`, `S53`, `S80`, native half of `S79`** |
| Residual risk | High: the loop continues | Low containment risk, high delivery risk from novel NT work | Windows functional gap in a Windows-hosted workspace | **Low for in-model classes; out-of-model classes accepted as recorded non-claims** |
| Threat-model statement | None | Implicit adversarial | Implicit adversarial, narrower platform | **Explicit: operator-controlled workspace** |
| Outcome | Rejected | Superseded by the B+D scope | Not adopted | **Selected** |

Options C and D were never alternatives to B's governance. Each was a scope
answer to C1, and B's governance and proof machinery executes whichever scope
applies. Under that machinery, the operator chose D's scope.

## Success criteria

The strategy has worked if all of the following hold:

1. No new plan revision is written until all required proofs pass, or the
   operator explicitly changes the architecture.
2. The acceptance matrix, rubric and personas are frozen before evaluation
   begins.
3. Each release unit is at most 6 tasks and 8 hours, and independently
   valuable.
4. Blockers decline monotonically across at most two consolidated revisions.
5. No finding family recurs without proof of a remediation regression. A
   recurring family is handled as an architecture reopen.
6. Authority and state are single-source and mechanically consistent, which is
   verified by script.
7. Publication, execution and claim gates are distinct, with separately stated
   criteria.
8. The future review ends in publish, split, spike, re-charter, defer or
   cancel, never in an unbounded retry.
9. No artifact claims TOCTOU or hardlink-alias resistance, and native security
   mechanisms return only through a re-charter.

Criteria 1, 4, 5 and 8 directly falsify the failure mode seen across attempts
07-11.

## Operator decisions

### C1 - threat model and platform mandate (resolved 2026-09-23)

Resolved by the B+D approval. The workspace is operator-controlled with no
hostile concurrent filesystem actor. Ordinary static containment is required
with the stated non-claims. Windows and Linux are both mandatory in the first
release, verified on each actual OS.

### C2 - release-unit split (open; bounded proposal)

**Proposal:** the A / B / C / D split in Phase 2, with unit C allowed to fold
into B when budget permits. **Gates:** Phase 2 and the DAG shape.

### C3 - migration and the fate of 187-S (open; bounded proposal)

**Proposal:** migrate to the acceptance matrix and a structured review index,
and retire or re-charter `187-S`. Patching is not an option, because `187-S`
cannot be brought within budget by editing carriers. **Gates:** Phases 2 and 3.
Until C3 is decided, `187-S` stays `queued` and is not claim-ready.

### C4 - `P2` publication policy, reviewer lead and routing (open; bounded proposal)

**Proposal:** only matrix-critical `P2` blocks publication. The reviewer lead
and routing are pending ratification, and neither is selected here. If anchor
routing is wanted, it must be configured before the epoch opens, because a
mid-epoch route change pauses the epoch. **Gates:** Phase 4.

## Next step

The intended next Stage step is the bounded Phase 1 proof experiments defined in
the charter, taken only after the charter is coherent. That step expands to no
branch or worktree beyond the single recorded P-016 spike worktree the charter
permits.

## Cross-references

* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md`
* Plan: `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` (revision 12, `0806b601`)
* Verdict manifest: `docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md` (revision 21)
* Terminal attempt: `docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-11.md`
* Prior attempts: attempts 07-10 under `docs/reviews/review-history/`
* Governing decision: `docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md` (revision 9)
* Constitution: `.github/instructions/constitution.instructions.md`
* Policy: `.github/policies/workflow-policies.md` (P-004, P-010, P-016)
* Actor: `.github/skills/harness-architect/SKILL.md` (Step 5.2)
* Ship surfaces: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`
* Manifest bindings: `.autoharness/harness-manifest.yaml` (`TEST_COMMAND`, `UNIMPLEMENTED_MARKER`)
* Learnings: `docs/compound/093-S-review-loop-convergence.md`,
  `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`,
  `docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md`,
  `docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md`,
  `docs/compound/097-S-canonical-unittest-gate.md`
