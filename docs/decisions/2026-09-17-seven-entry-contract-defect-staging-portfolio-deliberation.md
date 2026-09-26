---
title: "Seven-entry contract-defect staging portfolio: grouping, ownership boundaries, and execution sequence"
description: "Stage deliberation over the operator-selected stash scope 3EF5AAF2, 14F4D6F3, 86498B64, 76EBDE6D, C9CD24F3, 7F9CB5E9, and 71200CBB. Establishes per-entry disposition, one evidence-backed merge (14F4D6F3 into 86498B64), five further single-entry groups held apart under width isolation, the autoharness-versus-upstream ownership boundary for each, and a six-shipment fan-out execution DAG rooted at the P-004 policy correction because that correction is a precondition of 168-S, which already sits inside the existing 175-S dependency chain."
doc_type: decision
source: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
date: 2026-09-17
status: decided
revision: 3
revision_note: "Revision 3 is a BINDING revision issued in remediation cycle 2. Unlike revision 2 (which corrected two factual records without reopening any decision), revision 3 AMENDS FOUR DECISIONS so the decision record truthfully governs the remediated backlog state rather than describing a shape that no longer exists. (1) D8 is amended from a six-shipment SERIAL CHAIN to a SIX-SHIPMENT FAN-OUT DAG: 176-S is the single declared root and 177-S through 181-S are five parallel-eligible successors of it with no edges among themselves. The serial-chain rationale in revision 1/2 was a P-016 single-branch argument, but P-016 constrains concurrent EXECUTION, not the recorded dependency graph; encoding execution policy as false technical edges made the decision contradict the shipment records, which have always carried only a 176-S edge. (2) D1's branch-resolver ladder is amended from three rungs to EXACTLY TWO: explicit_contract then title_alias. The reserved empty workspace_convention rung is withdrawn -- an empty precedence rung is untestable and its presence invited consumers to depend on a tier that resolves nothing. (3) D5's scope ceiling is TIGHTENED: repository-wide plan migration, its regression suite, compact-context auto-consolidation, backlog-reference atomicity/harvest rewiring, and the plan budget contract are moved OUT of the C9CD24F3 feature and deferred to their own feature with P-021 capture. Revision 1/2 declared them 'in scope of this feature but as their own tasks', which kept the highest-blast-radius surface inside a unit whose shipment then could not close. (4) D3's contemplated downstream-conformance detector is WITHDRAWN: the spike concluded the remedy is contract-naming plus cross-surface structural evidence only, and no detector, fourth transition state, or POST_CLAIM_CONTRACT_CONTRADICTED token ships. Revision 2's two factual corrections are retained. D2, D4, D6, D7 and D9 are unchanged."
depth: deep
deciders: operator, Stage
decision_status: decided
promoted_to: plan
execution_architecture_status: superseded
execution_architecture_superseded_by: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
supersession_note: "PARTIAL supersession, recorded 2026-09-18 after the terminal attempt-08 plan-review block of all six derived plans. The EXECUTION ARCHITECTURE and EXECUTION SEQUENCE decided here are superseded: D8's six-shipment fan-out DAG rooted at 176-S is withdrawn as a false star (176-S is not a technical prerequisite of 177-S through 181-S), and D3's spike-first sequencing edge is withdrawn now that the spike has concluded. The PORTFOLIO SCOPE decided here REMAINS IN FORCE and is not reopened: the same seven source entries, the D1 merge of 14F4D6F3 into 86498B64 with both IDs preserved, the D2 width-isolation separation of the five remaining single-entry groups, and the per-entry ownership boundaries of D4, D5, D6, D7 and D9. Read this document for WHAT is in the portfolio and WHO owns each entry; read the superseding decision for HOW the portfolio is built and IN WHAT ORDER."
still_authoritative_for:
  - "seven-source portfolio scope (stash_ids)"
  - "D1, D2, D4, D5, D6, D7, D9"
no_longer_authoritative_for:
  - "D8 execution DAG and shipment sequencing"
  - "D3 spike-first sequencing edge"
stash_ids:
  - 3EF5AAF2
  - 14F4D6F3
  - 86498B64
  - 76EBDE6D
  - C9CD24F3
  - 7F9CB5E9
  - 71200CBB
deferred_scope_expansions:
  - 7F9CB5E9
  - 71200CBB
source_bug_reports:
  - docs/bugs/2026-09-17-autoharness-shipment-claim-wave-admission-contract-conflict.md
  - docs/bugs/2026-09-16-autoharness-pipeline-topology-explicit-branch-contract-bug.md
  - docs/bugs/2026-09-13-autoharness-append-only-plan-review-loop-bug-report.md
  - docs/scratch/bugs/2026-09-17-backlogit-checkpoint-v1-resume-hint-validation-gap.md
source_prior_deliberation: docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
source_prior_review: docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md
prior_learnings:
  - docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
  - docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md
  - docs/compound/2026-08-18-stage-agent-checkpoint-index-sync-ordering-self-contradiction.md
  - docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md
  - docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md
linked_artifacts:
  - docs/spikes/2026-09-17-post-claim-member-status-contract-spike.md
  - docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
  - docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
  - docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
  - docs/plans/2026-09-17-single-governing-plan-contract-plan.md
  - docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
  - docs/plans/2026-09-17-safe-close-record-transition-disposition-plan.md
tags:
  - "staging-portfolio"
  - "contract-drift"
  - "width-isolation"
  - "dag-sequencing"
  - "ownership-boundary"
---

# Seven-entry contract-defect staging portfolio

## Context

The operator selected an exact seven-entry stash scope for a full Stage
pipeline run. The scope is closed: no unrelated stash entry may be pulled into
implementation scope, and every selected entry must receive an explicit
disposition.

Two of the seven entries (`7F9CB5E9`, `71200CBB`) carry the literal
`DEFERRED SCOPE EXPANSION` marker. Under the Stage Step 1 precedence rule that
marker forces the `deliberate` route regardless of shape, size, or apparent
triviality, and forbids those entries from reaching implementation planning
without a deliberation artifact (P-021 C6). This document is that artifact for
both.

### Session degradation declared

* **Engram** `unified_search` / `query_memory`: circuit **OPEN** for this
  session after three identical `error-5001` failures (`content_record` lacks
  `chunk_id`). Not re-invoked. Codebase and history evidence in this document
  was obtained by exact-path reads, `git grep`, `git log -S`, and backlogit
  `get`/`dep list`/`shipment get`/`stash get` operations. This is the required
  pack-routing deviation signal.
* **Intercom**: unavailable in this CLI session. Operator visibility is local
  only; phase broadcasts were skipped. Non-destructive work continued.
* **graphtor-docs**: not probed; documentation evidence taken from exact-path
  reads of `docs/`.
* All backlogit MCP operations probed OK. `backlogit_sync_index` returned
  `{"indexed":1270}` (`INDEX_SYNC_OK`).

### Recovery gate

Full unfiltered checkpoint enumeration **at session start**: 51 records. Zero
validation or quarantine anomalies; zero empty `agent`/`status` fields. Status
histogram: 50 `resolved`, 1 `abandoned`. The single non-resolved record
(`checkpoint-20260914-210050.json`) is `ship`-owned and `abandoned`, therefore
neither a Stage candidate nor Stage's to touch (P-001). **Zero active
`stage`-owned checkpoints** — zero-candidate normal startup, not a failure.
`checkpoint-20260916-064310.json` is valid and carries a non-empty
`resume_hint`; it was read only and is not modified by this session.

*(Remediation cycle 1 note: the count above is a point-in-time session-start
observation and is correct as such. The corpus is 52 as of the remediation
cycle, because this session's own checkpoints were written after the
enumeration. Any downstream artifact that pins this number as a durable
inventory figure is wrong — see the checkpoint plan's T7, which is
invariant-based and pins no count for exactly this reason.)*

## Research Findings

### F1 — `P-002.6` does not exist in autoharness (decisive, `3EF5AAF2`)

`git grep -l -E "WAVE_NO_PROGRESS|ready_k" -- '*.md' '*.tmpl'` returns exactly
one path: the bug report itself. `git log -S "P-002.6" --all` and
`git log -S "WAVE_NO_PROGRESS" --all` each return exactly one commit,
`187526c0` — the commit that added that report. `.github/policies/workflow-policies.md`
contains `P-002` with no `.6` sub-clause, and `.github/agents/_ship.agent.md`
has no Step 4.0 wave-admission item. A repo-wide search finds no wave
scheduler, no `ready_k` set, and no `active residual` concept anywhere in the
policy registry, agent templates, installed agents, or skills.

The report's own frontmatter corroborates this: `external_provenance.origin_repository`
is `softwaresalt/backlogit`, and the transfer note states it was authored in
the backlogit workspace. `P-002.6` is therefore a **downstream-authored policy
in a consuming workspace**, not an autoharness policy.

### F2 — autoharness's canonical Ship contract already resolves the conflict

Prior learning `docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`
(confidence **high**, direct hit) records that `templates/agents/_ship.agent.md.tmpl`
**already tolerates** every manifest member reading `active` immediately after
a shipment claim: its Step 4a wording acknowledges a task can already be active
before Step 4.1 runs, and intake-reconciliation item 6 explicitly allows
"all `active` immediately after this session's own claim." That learning's own
conclusion is that the tolerance was correct and that what was missing was the
**causal attribution**, which the learning then supplied.

So the canonical contract and the backlogit claim contract agree. The conflict
exists only where a consuming workspace authored an admission rule that
contradicts the canonical tolerance. The autoharness-owned defect is therefore
not "fix P-002.6" — it is that the canonical tolerance is **prose-only,
unnamed, and untestable**, so nothing stops a downstream harness from
authoring a contradictory admission gate and nothing detects it when one does.

### F3 — P-004's precondition is self-contradictory against the required CI gate

`.github/policies/workflow-policies.md` lines 78–90 state the P-004
precondition as `PYTHONPATH=src python -m unittest discover -s tests` exiting
**non-zero** with expected failure markers **for every test function**. The
same command is the authoritative required CI gate on the default branch,
where it exits **zero**. Both cannot hold. The entry's second obstruction is
independent of suite size: a CHARACTERIZATION case passes by construction, so
an every-function-red precondition is unsatisfiable for any mixed
RED/CHARACTERIZATION harness even on an empty pre-existing suite.

### F4 — `168-S` sits inside the existing chain and is blocked by F3

Queued shipment dependency edges (`backlogit dep list`, direction confirmed
against `dep list --reverse`; `X → Y (blocks)` means Y is X's predecessor):

```text
chain A:  175-S → 163-S → 164-S → 165-S → 166-S → 168-S → 167-S      (175-S is dag-root)
chain B:  169-S → 170-S → 172-S
          169-S → 171-S                                              (169-S has NO edge and NO label)
          162-S additionally precedes 163-S and 170-S; 162-S is archived
```

`168-S` is chain A's sixth element and `167-S` its leaf. `76EBDE6D` states
`168-S` cannot pass the harness-ready gate as P-004 is written. Sequencing the
P-004 correction behind chain A's leaf therefore places the fix behind the very
shipment the fix unblocks — an unreachable-fix deadlock.

### F5 — `169-S` is unsequenced and chain B is unreachable

`_predecessor_source()` in `src/autoharness/gates/topology.py` derives
`explicit` from a `blocks` edge, `declared_root` from a `dag-root` label, and
`genesis` only when the workspace holds exactly one physical shipment record.
`169-S` has neither an edge nor the label, and the workspace holds many
shipment records, so it derives `unsequenced` and `pre_claim` blocks it with
`UNSEQUENCED_SHIPMENT`. `170-S`, `171-S`, and `172-S` all depend on `169-S`, so
chain B is unreachable in its entirety. This is pre-existing, outside the
selected scope, and is surfaced rather than silently repaired.

### F6 — `14F4D6F3` and `86498B64` are the same contract surface

Both name `src/autoharness/gates/topology.py`. Both name the same authority
question: what is the release unit's implementation branch called. Both
prescribe the same mechanism — one shared resolver used by all phases, strict
precedence `explicit custom_fields.implementation_branch` > configured naming
convention > title-derived aliases, fail-closed on a present-but-malformed
explicit value with a distinct token, and gate JSON carrying
`resolution_source` / `selected_branch` / ordered `expected_branches`. `86498B64`
is the design-doc-backed covering feature; `14F4D6F3` is the same defect
observed in the field with a seven-row regression matrix and a distinct
fail-closed token name. They differ only in the token spelling
(`IMPLEMENTATION_BRANCH_MALFORMED` versus `BRANCH_POLICY_INVALID`) and in
whether the declarative workspace-convention tier ships now.

**Provenance gap (recorded, not resolved).** `86498B64`'s intake text declares
an exact repository-relative source design document at
`docs/design-docs/2026-09-10-autoharness-workspace-driven-branch-resolution-design.md`.
That file does **not** exist in this repository at `main` as of 2026-09-17
(`docs/design-docs/` contains no branch-resolution document, and the path
appears in no commit). The phrase "design-doc-backed" throughout this
deliberation and the derived plan therefore refers to the **design summary
preserved verbatim inside the `86498B64` stash entry itself**, which is the
operative design record. No planning conclusion in this portfolio depends on
the absent file: every requirement is restated in full in
`docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md`. The
closest surviving in-repo prior art is
`docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md`
and its review, recorded in this document's frontmatter. Surfaced to the
operator as an advisory provenance finding.

`86498B64`'s own Stage annotation kept it apart from `165-F`/`173-S` because
that work changed **sequencing** authority while this changes **branch-naming**
authority — a different-contract judgement, not a same-file one. That
distinction does not separate `14F4D6F3` from `86498B64`: they are the same
contract.

`86498B64`'s recorded sequencing precondition — "deliberate and harvest this
immediately after `173-S` is assembled/executed" — is **satisfied**:
`backlogit shipment get 173-S` and `174-S` both report `status: archived`.

### F7 — `7F9CB5E9`'s fix is genuinely external; its autoharness surface is not empty

The record-transition capability (`archived_status: shipped` without cascade)
lives in the backlogit Go binary and cannot be implemented here. But three
autoharness-owned obligations remain, and the entry is explicitly retained
because the operator imported it to make multi-shipment delivery operational:

1. The measurements backing the whole claim were taken in external `%TEMP%`
   workspaces — a recorded P-005 containment violation making the evidence
   **indicative, not authoritative**. Re-deriving them as hermetic in-workspace
   fixtures is autoharness work and is a precondition of accepting any remedy.
2. The upstream escalation route (file an issue/PR, vendor a wrapper, or
   pin-and-patch) is an autoharness decision with an autoharness-owned record.
3. Documentation truth: nothing in this repository may describe split delivery
   as operationally complete while `INV-11` is blocked, and the
   approval-gated operator close procedure (modelled on the Ship-verified
   operator close of `173-S` on 2026-09-16) must be documented as an
   operator-only escape hatch, never an agent-executable path.

### F8 — `71200CBB`'s ordering hazard is load-bearing

The entry's own refinement is correct and is adopted: shipping the validator
(item 2) before the historical-record policy (item 3) converts a latent gap
into a hard startup block, because the startup contract fails closed on missing
required fields without exempting resolved records, and a resolved checkpoint
cannot be repaired through the official create operation. The upstream half
(backlogit CheckpointV1 requiredness, `checkpoint create --help` text) is
excluded and already written up at
`docs/scratch/bugs/2026-09-17-backlogit-checkpoint-v1-resume-hint-validation-gap.md`.

Directly related provenance observed in the dirty worktree: the
`checkpoint-20260916-064310.json` record carries a populated `resume_hint`.
**Provenance, stated precisely (corrected in remediation cycle 1):** this is an
**operator-authored, operator-authorized pre-existing repair**, performed by
the human operator outside the agent pipeline and explicitly directed to be
preserved. It was included in the publication diff of commit `1b6a312d` for
durable startup consistency. It is **not** an agent-performed migration and
**not** evidence that an official repair mechanism for resolved checkpoints
exists — no such mechanism exists, which is precisely why item 3 (the
historical-record policy) is needed. Revision 1 of this deliberation described
it as "what a migrated historical record looks like"; that framing overstated
it, because no migration ran. **Residual policy risk, recorded not waived:**
the repair was a direct edit to a file under `.backlogit/checkpoints/`, which
`.github/instructions/backlogit.instructions.md` rule 2 reserves to the
official create operation. Operator authorship and authorization is the only
authority under which that is permissible. No agent may cite it as precedent.
The file is preserved unmodified by this session.

### F9 — `C9CD24F3` is corroborated by this repository's own artifacts

`docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md` and
`docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`
describe the same non-convergence mechanism from the inside. The remedy is
already being applied by hand in this repository: the current
`docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md` is at
`revision: 5` and its `revision_note` records "a full canonical rewrite …
maintained as one coherent specification … rather than an accreting record of
corrections," with the audit trail segregated into `linked_review`. The defect
is that this discipline is **manual and unenforced**.

## Decision

### D1 — Merge `14F4D6F3` into `86498B64`; preserve both source IDs

Per **F6**. `86498B64` is the covering identity (design-doc-backed, feature
kind); `14F4D6F3` contributes the field observation, the seven-row regression
matrix, and the `IMPLEMENTATION_BRANCH_MALFORMED` token. Both stash IDs are
carried on the feature, on every task, on the plan, and on the review. Neither
entry is destroyed: both are archived as **consumed** with a forward reference
to the same feature. This is the only merge in the portfolio.

Token reconciliation: adopt `IMPLEMENTATION_BRANCH_MALFORMED` as the
fail-closed token for a present-but-malformed explicit value, because it names
the field rather than an abstract policy, and record `BRANCH_POLICY_INVALID`
as the design-doc synonym so the design doc remains readable.

Open decision carried forward by `86498B64` and resolved here: the declarative
workspace-level branch-template tier in `.autoharness/config.yaml` is
**deferred**.

**AMENDED IN REVISION 3 — the ladder is exactly two rungs.** Revision 1/2
directed that the resolver ship "with the tier present as an explicit, tested,
empty middle precedence rung so adding it later is additive". That is
withdrawn. The precedence ladder is **exactly `explicit_contract` >
`title_alias`**, with no third rung present in any form.

Rationale for the amendment: an empty precedence rung cannot be meaningfully
tested — there is no input that makes it fire, so any "test" of it asserts only
that it is skipped, which is indistinguishable from the rung not existing. Worse,
a named-but-empty tier is a public affordance: a consuming workspace can read the
rung name, believe a workspace-convention tier is supported, and author
configuration against a tier that resolves nothing. Adding a third rung later
remains additive whether or not a placeholder exists today, so the placeholder
bought nothing and carried a real misreading risk.

Adjacency to `165-F`'s new `gates.pipeline_topology.unsequenced_shipment` key is
noted; no config key is added by this release unit.

### D2 — No other merge. Five single-entry groups held apart

`3EF5AAF2`, `76EBDE6D`, `C9CD24F3`, `7F9CB5E9`, and `71200CBB` each get their
own covering feature and their own shipment.

The closest merge candidates were considered and rejected:

* `3EF5AAF2` + `76EBDE6D` — both are Ship-execution-gate precondition defects
  touching `workflow-policies.md` and the Ship agent template. **Rejected**:
  this repository's own recorded precedent (the `86498B64` annotation, upheld
  by the Scope Boundary Auditor persona in
  `docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md`)
  is that same-file adjacency is not same-contract necessity. One is a
  post-claim **status** contract, the other a red-phase **evidence** contract.
  Merging would also block the small, self-contained P-004 correction behind
  `3EF5AAF2`'s required spike.
* `3EF5AAF2` + `7F9CB5E9` — both are backlogit shipment-lifecycle interop.
  **Rejected**: claim-phase versus close-phase, and `7F9CB5E9`'s resolution is
  externally owned while `3EF5AAF2`'s is not. They share only the
  upstream-escalation *question*, which D7 answers once for both.
* `C9CD24F3` + `71200CBB` — both are harness-artifact schema/contract defects.
  **Rejected**: plan artifacts versus checkpoint records; disjoint producers,
  disjoint consumers, disjoint tests.

### D3 — `3EF5AAF2` is re-scoped, not rejected, and requires a spike first

The report's stated fix ("stop P-002.6 halting on post-claim active members")
is **not actionable in this repository** because P-002.6 does not exist here
(**F1**). The report's ownership claim — "primarily the autoharness
integration/policy layer" — is upheld, but the integration defect is the
inverse of what the report assumed: autoharness's canonical Ship contract is
**correct and already tolerant** (**F2**), and what is missing is that the
tolerance is unnamed, unversioned, and unenforced, so a consuming workspace
can author a contradictory admission gate undetected.

A **spike** runs first, as the report itself requires, but re-aimed: confirm
the provenance of `P-002.6`, confirm the canonical tolerance is in both the
template and the installed mirror, and decide whether the remedy is
contract-naming only or also needs a downstream-conformance check. The spike is
read-only and in-workspace; no external `%TEMP%` arm is permitted (P-005).

**AMENDED IN REVISION 3 — the detector is withdrawn; the spike's open question
is now closed.** The spike ran and resolved the "or also needs a
downstream-conformance check" branch in the **negative**. The delivered remedy
is **contract-naming plus cross-surface structural evidence only**:

* The canonical post-claim member-status contract is **named and versioned**
  (P-002.7) and the claim-to-admission transition is stated as **exactly three
  states** — no fourth "contradicted" state exists.
* **No downstream-conformance detector ships.** No scanner, linter, or gate
  inspects consuming workspaces for contradictory admission gates.
* **No `POST_CLAIM_CONTRACT_CONTRADICTED` token ships**, in any artifact, at any
  severity.

Rationale for the amendment: detecting a contradictory admission gate in a
consuming workspace requires a typed, machine-comparable representation of the
policy clause to compare against. No such representation exists, so any detector
built now would have to pattern-match prose and would produce false verdicts about
other people's repositories. That prerequisite is captured as deferred work rather
than dropped. The contract-naming half is fully deliverable on its own and is what
this unit ships.

The report's Option A / Option B framing is **not adopted as stated**, because
both options presuppose changing what `ClaimShipment` does. backlogit is
behaving per its documented and unit-tested contract and per this repository's
own compound learning; no upstream change is requested for this entry.

### D4 — `76EBDE6D` is disposition (c): an explicit harness-scoped selector

Of the three candidate dispositions the entry offers, adopt **"add an explicit
selector/marker for the harness under confirmation"**, with **"scope the red
confirmation to the shipment-scoped harness subset"** as its operational
consequence. The third candidate ("state the precondition over newly authored
RED-FIRST functions only") is rejected on its own terms: it re-introduces the
CHARACTERIZATION obstruction, because a newly authored characterization test is
both newly authored and green by construction.

The corrected precondition is stated over the **declared harness set** for the
shipment under confirmation — never over whole-suite discover — and admits two
disjoint declared classes, `expected-red` and `expected-green-characterization`,
with the gate asserting exact set equality against observed outcomes rather
than a blanket every-function-red. The default-branch whole-suite CI gate is
untouched and must continue to exit zero. No bypass is authorized; the gate
stays fail-closed.

### D5 — `C9CD24F3` is adopted with a hard scope ceiling

The report's direction is adopted in principle but **the 2-hour rule governs,
not the report's seven-step decomposition**. This release unit delivers the
load-bearing minimum: durable plan identity metadata, exactly one active
`*-decided-plan` per plan identity, immutable per-attempt review artifacts
outside the plan file, manifest-driven review-input assembly that fails closed
if history leaks into the operative set, and a pre-dispatch verifier.

**AMENDED IN REVISION 3 — the ceiling is tightened; four surfaces move out of
the feature entirely.** Revision 1/2 declared auto-consolidation triggers,
backlog-reference atomicity, and the migration of existing append-only plans
"**in scope of this feature but as their own tasks**". That is withdrawn. The
following are **out of scope of the `C9CD24F3` feature** and are deferred to a
separate feature with P-021 capture, preserving provenance and linkage:

* repository-wide migration of existing append-only plans, and its regression suite
* compact-context auto-consolidation triggers
* backlog-reference atomicity / harvest rewiring
* the plan budget contract and its `PLAN_BUDGET_BREACH` token

Rationale for the amendment: "in scope but as its own task" kept the
highest-blast-radius surface in the portfolio — a routine that rewrites
committed, history-bearing artifacts — inside a release unit that had to close.
Because the in-unit pre-dispatch verifier was made to block on that migration, the
unit's shipment could not reach a closable state without executing the migration,
which is precisely the partial-closure trap this portfolio exists to remove. The
in-unit replacement for migration is the **non-blocking `PLAN_LEGACY_UNIDENTIFIED`
classification signal**: pre-existing plans without a `plan_id` are *classified and
reported*, never converted, so the verifier can enforce at blocking severity
immediately and no in-scope task depends on any deferred surface.

Nothing in the report's out-of-scope list is reopened: no new service, no
database, no non-Git storage, no prompt-wording-only fix.

### D6 — `71200CBB` ships items (3) then (2) then (1), and stays at `medium`

Item (3), the historical-record policy, **must land with or before** item (2),
the validator (**F8**). The plan orders the tasks (3) → (1) → (2) so the
validator is the last thing enabled. Priority stays `medium`; neither escalation
trigger has fired — no startup halt on this record has been observed, and item
(2) has not landed ahead of item (3). The upstream half remains excluded and
this entry is not blocked on it.

### D7 — `7F9CB5E9` is retained as autoharness work with an explicit external boundary

Per **F7**. The autoharness-owned deliverables are the hermetic in-workspace
re-derivation of the four measured behaviours, the recorded upstream
escalation route, the documented operator-only approval-gated close procedure,
and the documentation-truth correction. The remedy itself is external and the
entry stays open against it.

Escalation route decided: **file an upstream issue/PR against `softwaresalt/backlogit`
requesting a non-cascading terminal transition**, with the portable report
generated from the hermetic fixtures. Vendoring a wrapper and pin-and-patch are
both rejected: a wrapper would have to reimplement archive semantics the engine
owns, and a patched pin forks a binary dependency that this workspace already
consumes at a moving version. The same escalation channel is reused for the
`63363CF5` parent-id-clearing defect where they overlap; `63363CF5` itself
remains untouched and outside scope.

**No agent-executable administrative close is created.** The interim procedure
is documented as operator-only.

### D8 — Sequence: a six-shipment fan-out DAG rooted at the P-004 correction

**AMENDED IN REVISION 3.** Revision 1/2 recorded a six-shipment *serial chain*
(`176-S → 177-S → 178-S → 179-S → 180-S → 181-S`). That encoding is withdrawn as
factually wrong: the shipment records have only ever carried a single `blocks`
edge each, onto `176-S`. The binding shape is a **fan-out**:

```text
                          176-S (dag-root, justified)
                    P-004 red-phase precondition scoping        [76EBDE6D]
                                    │
        ┌───────────┬───────────────┼───────────────┬───────────┐
        │           │               │               │           │
      177-S       178-S           179-S           180-S       181-S
   post-claim    branch        single-plan      checkpoint   SAFE_CLOSE
    contract    resolution       contract      resume_hint   disposition
   [3EF5AAF2]  [86498B64+      [C9CD24F3]      [71200CBB]   [7F9CB5E9]
                14F4D6F3]
```

`176-S` is the **single declared root**. `177-S`, `178-S`, `179-S`, `180-S` and
`181-S` are **five parallel-eligible successors**, each depending only on
`176-S`, with **no edges among themselves**.

**Why `176-S` is a declared root and not a successor of `167-S`.** Per **F4**,
`168-S` is inside chain A and is blocked at harness-ready by the very P-004
defect `176-S` corrects. Attaching `176-S` behind chain A's leaf `167-S` would
place the fix behind the shipment it unblocks, producing an unreachable fix.
`176-S` has no genuine technical predecessor, so `declared_root` is the
truthful derivation, not a convenience. The declaration is recorded as a
`dag-root` label on backlog data inside the repository trust boundary, visible
in diffs and attributable to a commit, exactly as the sequencing contract
prescribes. **No bootstrap grant is authored** — grants are operator-authored
and review-gated, and a self-authored grant would be a P-005/P-001 violation.

**Why the remaining five are recorded as parallel successors and not as a serial
chain.** They have **no technical inter-dependency** — that was true in revision 1
and is restated here. Revision 1/2 nonetheless serialized them, reasoning that
P-016 permits only one implementation branch at a time and that a chain was "the
honest encoding of how they will actually execute". That reasoning is rejected on
amendment for three reasons:

1. **P-016 constrains concurrent execution, not the recorded graph.** Encoding an
   execution-concurrency policy as technical `blocks` edges asserts a dependency
   that does not exist. A single-branch policy is satisfied by claiming one
   successor at a time out of five eligible heads; it does not require pretending
   `180-S` needs `179-S`.
2. **It contradicted the actual records.** The shipment artifacts encode the
   fan-out. A decision document that describes a chain while the data encodes a
   fan-out is not a governing record — it is a second, conflicting source of truth.
3. **It manufactured false blast radius.** Under the chain, a fault anywhere in
   `177-S`–`180-S` transitively blocks everything after it, even though none of
   those units touches the others' surfaces. The fan-out isolates failures to the
   single affected successor.

**Recommended claim order remains a preference, not an edge.** When the operator
chooses which eligible successor to claim next, order by unblocking power then
priority: `177-S` (external consumers blocked), `178-S` (claim-path correctness),
`179-S` (`high`), `180-S` (`medium`), `181-S` (evidence and documentation; the
real remedy is external). This is guidance for sequencing attention under P-016,
and it is deliberately **not** recorded as `blocks` edges.

**Existing scope is not rewritten.** Each `blocks` edge is recorded on the new
shipment, so no existing shipment record is mutated.

### D9 — Two pre-existing blockers surfaced, not repaired

* **BLOCKER-1**: `169-S` is `unsequenced` (**F5**). It and chain B
  (`170-S`, `171-S`, `172-S`) cannot be claimed. Remedy is to record a real
  `blocks` edge or apply `dag-root` to `169-S` — both mutate a shipment
  outside the selected scope. **Recommendation for operator authorization**:
  record `169-S` blocked by `167-S`, which merges chain B onto chain A's tail
  and creates no additional root. Not performed by this session.
* **BLOCKER-2**: `168-S` remains blocked at harness-ready until `176-S` ships
  (**F3**, **F4**). The honest edge is `168-S` blocked by `176-S`, which would
  mutate `168-S` — outside scope. **Recommendation for operator authorization**;
  not performed by this session.

Neither blocker prevents the newly staged sequence from being fully queued and
claimable: `176-S` is a declared root and `177-S`–`181-S` derive `explicit`.

*Revision 3 note: `168-S` was subsequently observed to carry
`dependencies: [166-S, 176-S]`, so the BLOCKER-2 edge appears to have been applied
under separate operator authorization. This is recorded as an observation only;
no shipment outside the selected scope was mutated by any Stage session.*

## Options Evaluated

*Non-binding historical analysis. The binding output of this deliberation is
the `## Decision` section alone.*

| Option | Grouping | Outcome |
|---|---|---|
| O1 | One covering feature for all seven entries | Rejected — six distinct contract surfaces, oversized shipment, violates width isolation and the operator's explicit instruction |
| O2 | Two groups (Ship-gate defects; harness-artifact defects) | Rejected — see D2; couples a spike-gated item to a self-contained one |
| O3 | Seven single-entry groups, no merge | Rejected — ignores the F6 evidence that `14F4D6F3` and `86498B64` are one contract |
| O4 | **Six groups: one evidence-backed merge, five held apart** | **Adopted** |
| O5 | Six groups, all declared `dag-root` | Rejected — six concurrently-eligible heads against a one-branch-at-a-time policy |
| O6 | Six groups chained after `167-S`, no new root | Rejected — unreachable-fix deadlock via `168-S` (F4) |

## Rejected Alternatives

*Non-binding.*

* **Discard `7F9CB5E9` as upstream-only.** Rejected: the operator imported it
  specifically to make multi-shipment delivery operational, and F7 identifies
  three real autoharness-owned deliverables.
* **Implement `3EF5AAF2` as written.** Rejected: the target policy does not
  exist in this repository (F1).
* **Raise `71200CBB` to `high`.** Rejected: neither of the entry's own recorded
  escalation triggers has fired.
* **Re-run the `7F9CB5E9` measurements in `%TEMP%` to confirm them quickly.**
  Rejected: that is the exact P-005 violation the entry already records.
* **Use Engram to widen the `P-002.6` provenance search.** Rejected: circuit
  open; `git log -S` over all refs is a stronger existence proof than semantic
  search for this specific question.
