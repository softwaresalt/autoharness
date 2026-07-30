---
title: Multi-Shipment Dark-Factory Sequencing Hardening
doc_type: plan
date: 2026-07-30
source_stash: 60C57761
origin: cross-repo intake from backlogit orchestrator
grounding_decision: backlogit spike 001-SP (DEFER standalone ship_sequence.jsonl; reuse queue + item_deps)
status: reviewed
---

# Implementation Plan: Multi-Shipment Dark-Factory Sequencing Hardening

## Problem Frame

During a long-running P-017 dark run, the Orchestrator must parcel a **chosen or
calculated sequence** of queued shipments one-by-one. Today three template
surfaces under-specify how that sequence is authored, selected, and audited:

1. **Selection is priority-only.** `templates/agents/_orchestrator.agent.md.tmpl`
   Step 2 (line 257) reads: `1. Select the highest-priority queued shipment.`
   Shipments rarely carry priority, so "highest-priority" is effectively
   arbitrary. There is no rule to honor an explicit ordering or to skip a
   shipment whose predecessor has not shipped.

2. **Dark-mode scope is unordered.** `templates/policies/workflow-policies.md.tmpl`
   P-017 activation contract item 1 records "the bounded scope (stash IDs,
   feature ID, shipment ID, or explicit backlog selection)" and emits a
   `DARK_MODE_SCOPE` telemetry event, but neither captures an **ordered**
   shipment sequence or **resume/audit evidence** for a restartable long run.

3. **No authoring playbook.** `templates/instructions/backlogit.instructions.md.tmpl`
   (the backlogit capability-pack overlay) documents queue/dependency protocols
   generically but gives no concrete recipe for chaining shipments into a
   self-enforcing sequence.

The grounding decision (backlogit spike `001-SP`, tracked in the *backlogit*
project — file intentionally absent from this repo) is to **reuse `queue` +
`item_deps`** rather than introduce a standalone `ship_sequence.jsonl`
scheduler. This plan is the upstream autoharness-template counterpart and MUST
stay consistent with that decision: build on `custom_fields.queue_position` +
`item_deps` blocks-chains; introduce **no new sequence-manifest file** and **no
new scheduler**.

### Verified backlogit primitives (grounding)

* `backlogit queue view` sorts by **manually assigned queue positions first,
  then priority** (`queue view --help`). This validates `queue_position` as a
  first-class ordering primitive. `--type shipment --status queued` flags exist.
* `item_deps` is a documented table: `dep_type ∈ {blocks, relates_to, parent_of}`
  (`backlogit-sql-schema.instructions.md.tmpl` line 46).
* Prior learning `2026-05-07-backlogit-shipment-status-constraints`: a shipment
  gated on a dependency should sit at `status: blocked`, returning to `queued`
  only when the gate clears. The selection rule must reconcile with this
  canonical lifecycle (see Decisions).

## Requirements Trace

| Req | Source (intake) | Implementation action | Unit |
|---|---|---|---|
| R1 | Orchestrator selection must honor `custom_fields.queue_position` and suppress shipments with unresolved blocking `item_deps`; claim the top of `queue view --type shipment --status queued` | Rewrite Step 2 rule #1 in `_orchestrator.agent.md.tmpl` | U1 |
| R2 | P-017 `DARK_MODE_SCOPE` must record the ORDERED shipment scope plus resume/audit evidence; no new scheduler | Extend P-017 activation contract + `DARK_MODE_SCOPE` telemetry semantics in `workflow-policies.md.tmpl` | U2 |
| R3 | Add a shipment-sequencing playbook (`queue view --type shipment --status queued`; `dep add <next> <prev> --type blocks`; note `dep_type` collapses to `blocks` on sync/rehydrate) | Add a Shipment Sequencing Protocol to `backlogit.instructions.md.tmpl` | U3 |
| R4 | Keep the three templates coherent as a cross-cutting set; valid Markdown across ≥3 tech profiles; no unresolved `{{...}}`; no undocumented new variables | Cross-reference coherence + multi-profile render validation sweep | U4 |

## Implementation Units

### U1 — Queue-ordering-aware shipment selection (Orchestrator)

* **Change**: Replace Step 2 rule #1 (`Select the highest-priority queued
  shipment.`) with a queue-ordering-aware rule:
  * Use `queue view --type shipment --status queued` as the **first-pass**
    candidate source: it returns shipments in execution order
    (`custom_fields.queue_position` first, then priority) and, per the canonical
    lifecycle, withholds shipments parked at `status: blocked`. Treat it as an
    ordering aid and first filter — **not** the sole eligibility authority.
  * **Constrain the candidate to the recorded scope.** In a multi-shipment dark
    run the candidate is the **next shipment ID recorded in the P-017
    `DARK_MODE_SCOPE` ordered cursor** (U2), not merely the global queue head.
    Verify that exact shipment is the eligible next one; if the queue head is a
    different, out-of-scope shipment, **halt** rather than substitute it —
    silently claiming another queue head would violate P-017's
    no-silent-scope-expansion rule (`workflow-policies.md.tmpl:462`).
  * **Re-check eligibility before claim (explicit, required).** Before claiming,
    perform an explicit `item_deps` + status check confirming the candidate has
    **no unshipped blocking predecessor** — do **not** rely solely on the queue
    result. This honors the existing Queue and Dependency Protocol
    (`backlogit.instructions.md.tmpl:43-46`, "Re-check unfinished dependencies
    before claiming"): a stale or non-filtering `queue view` could otherwise
    surface a successor early. The queue query plus this re-check together make
    an `item_deps` blocks-chain a self-enforcing sequence: a shipment is claimed
    only once its predecessor has shipped.
  * Do **not** use `queue view` to reconstruct the full ordered sequence for
    scope/audit — it returns only the currently eligible head and hides blocked
    successors. Deriving the complete ordered shipment list (for the P-017 scope
    and restart cursor; see U2) requires listing shipments across **both
    `queued` and `blocked` statuses** (or an unfiltered shipment listing), then
    traversing the `item_deps` blocks-chain — because dependency-gated successors
    sit at `status: blocked`, a queued-only listing would truncate the sequence.
  * **Precedence (explicit)**: `item_deps` suppression is a **hard eligibility
    gate** — a queued shipment with an unshipped blocking predecessor is never
    eligible, regardless of its `queue_position`. `queue_position` only orders
    among the *already-eligible* shipments. When the two appear to disagree
    (e.g., queue_position lists A before B but A is blocked by B), eligibility
    wins: B is claimed first. Author the rule so this precedence is unambiguous.
  * Cross-reference the P-017 ordered scope (U2) and the backlogit playbook (U3)
    so the three surfaces name the same mechanism.
* **Files**: `templates/agents/_orchestrator.agent.md.tmpl` **and its
  source-controlled dogfood mirror** `.github/agents/_orchestrator.agent.md` (the
  same Step 2 rule #1 lives at `.github/agents/_orchestrator.agent.md:196`); after
  editing the mirror, **regenerate its checksum** in
  `.autoharness/harness-manifest.yaml` (the `.github/agents/_orchestrator.agent.md`
  entry, ~lines 117-121). Editing only the template would leave this repository's
  active Orchestrator on the old selection behavior.
* **Verification**: the rule renders as valid Markdown in **both** the template
  and the installed mirror; the numbered list stays well-formed; the existing
  P-001/P-016/P-020 guard in rule #2 is preserved verbatim; template and mirror
  carry the same selection rule (the mirror contains no `{{VARIABLE}}`); the
  manifest checksum for `.github/agents/_orchestrator.agent.md` is regenerated to
  match the edited mirror; no new `{{VARIABLE}}` is introduced in the template
  (reuse `{{STATUS_QUEUED}}`).
* **Execution posture**: documentation edit (characterization-by-reading; no
  runtime code).

### U2 — P-017 DARK_MODE_SCOPE ordered scope + resume/audit evidence

* **Change**: In P-017 (`workflow-policies.md.tmpl`):
  * Extend activation-contract item 1 so the bounded scope, when it is a
    multi-shipment dark run, records the **ordered shipment sequence** (the
    resolved `queue_position` / `item_deps` blocks-chain order) rather than an
    unordered set.
  * Extend the `DARK_MODE_SCOPE` telemetry event semantics to carry
    **resume/audit evidence**: the ordered shipment list, the last completed
    shipment, and the next shipment to claim — an authoritative, **restartable**
    cursor derived from `queue` + `item_deps`, explicitly **without** a new
    scheduler or sequence-manifest file.
  * State that the ordered sequence is derived from the same `queue_position` +
    `item_deps` mechanism the Orchestrator selection rule (U1) consumes, so
    resume is deterministic across restarts. **Reconstruction caveat**: the full
    ordered list cannot be read from `queue view` (which returns only the
    currently *ready* head and hides blocked successors). Deriving and recording
    the complete ordered scope + restart cursor requires listing shipments across
    **both `queued` and `blocked` statuses** (or an unfiltered shipment listing),
    then traversing the `item_deps` blocks-chain (walk the blocks-edges) — a
    queued-only listing omits the dependency-gated successors that sit at
    `status: blocked`. `queue view` stays reserved for selecting the next
    *eligible* shipment (U1).
* **Files**: `templates/policies/workflow-policies.md.tmpl` (1 file).
* **Verification**: P-017 table/section structure intact; `DARK_MODE_SCOPE`
  remains in the telemetry event list; no contradiction with the existing
  "Scope rule" (no silent expansion) or P-001 one-release-unit relationship;
  changelog row optional.
* **Execution posture**: policy documentation edit.
* **Depends on**: U1 (must reference the selection mechanism U1 establishes).

### U3 — backlogit shipment-sequencing playbook

* **Change**: Add a **Shipment Sequencing Protocol** subsection to
  `backlogit.instructions.md.tmpl` (adjacent to the existing "Queue and
  Dependency Protocol"):
  * **Select the next eligible shipment** (execution): `queue view --type
    shipment --status queued` returns queue-ordered *ready* candidates
    (`custom_fields.queue_position` first) and withholds shipments parked at
    `status: blocked`. Treat it as a first-pass filter, then **re-check the
    candidate's `item_deps` + status before claiming** (per the "Re-check
    unfinished dependencies before claiming" rule in the Queue and Dependency
    Protocol) rather than trusting the query alone.
  * **Reconstruct the full ordered sequence** (scope / audit / resume): because
    `queue view` hides blocked successors, list shipments across **both `queued`
    and `blocked` statuses** (or use an unfiltered shipment listing) and traverse
    `item_deps` blocks-edges to rebuild the complete ordered chain and restart
    cursor. A queued-only listing truncates the chain, since dependency-gated
    successors remain at `status: blocked` until their gate clears. Do not rely
    on `queue view` for the full sequence.
  * Chain shipments into a self-enforcing sequence:
    `dep add <next-shipment> <prev-shipment> --type blocks`.
  * Honor `custom_fields.queue_position` for explicit manual ordering.
  * Note that `dep_type` collapses to `blocks` on sync/rehydrate, so author
    ordering with `--type blocks` explicitly and do not rely on other dep types
    surviving.
  * Cross-reference: the Orchestrator consumes this ordering (U1) and P-017
    records it as the ordered dark-mode scope (U2).
* **Files**: `templates/instructions/backlogit.instructions.md.tmpl` (1 file).
* **Verification**: valid Markdown; consistent with the "Semantic Links vs
  Dependencies" guidance already in the file (blocks = execution-blocking
  dependency, not a link); no new `{{VARIABLE}}`.
* **Execution posture**: instruction documentation edit.
* **Depends on**: U1.

### U4 — Cross-reference coherence + multi-profile validation sweep

* **Change**: After U1–U3, validate the three templates as a coherent set:
  * All three name the same mechanism (`queue_position` + `item_deps` blocks-chain)
    with consistent terminology and reciprocal cross-references.
  * Each renders valid Markdown when variables resolve. Per `AGENTS.md`
    (templates must work for ≥3 technology profiles and be tested *after*
    variable resolution), **actually render** all three templates against **three
    profile fixtures** (e.g., Rust, TypeScript, Python) and validate each rendered
    output: valid Markdown, correct heading hierarchy, and **no unresolved
    `{{...}}`** in the rendered result. A conceptual "identical modulo variables"
    argument does **not** satisfy this gate — produce the three renders and check
    them.
  * No unresolved `{{...}}` beyond pre-existing legitimate template variables;
    confirm **no new template variable was introduced** (so the install-harness
    SKILL.md variable-resolution table needs no update).
  * **Validation-only**: this unit does not author new content. If a coherence
    mismatch is found, route the fix back to the owning unit (U1–U3) rather than
    editing here; U4 records the finding and re-verifies after the owning unit
    corrects it. This keeps authorship in one place and prevents scope drift.
* **Files**: reads all three; no authoring edits (records findings; owning unit
  fixes and U4 re-verifies).
* **Verification**: three rendered profile fixtures produced and checked (valid
  Markdown, MD001/MD025/MD041 heading hierarchy clean, and no unresolved `{{...}}`
  in each render); cross-reference integrity holds across the set; variable
  completeness confirmed (no new variable introduced).
* **Execution posture**: verification / coherence gate.
* **Depends on**: U1, U2, U3.

## Dependency Graph

```text
U1 (orchestrator selection)
 ├── blocks ──> U2 (P-017 ordered scope)
 ├── blocks ──> U3 (backlogit playbook)
U2 ──┐
U3 ──┴── blocks ──> U4 (coherence + multi-profile validation)
```

No cycles. U1 is the anchor because U2 and U3 both reference the selection
mechanism it establishes. U4 is terminal (validates the whole set).

## Decisions and Rationale

1. **Reuse `queue_position` + `item_deps`; no `ship_sequence.jsonl`.** Consistent
   with backlogit spike `001-SP` DEFER conclusion. Avoids a parallel scheduler;
   the queue and dependency graph already express ordering and gating.
2. **Selection reconciles with the `blocked` shipment lifecycle.** Prior learning
   `2026-05-07-backlogit-shipment-status-constraints` establishes that a shipment
   gated on a dependency should sit at `status: blocked`. The U1 rule therefore
   operates on `--status queued` (already excluding `blocked` shipments) AND adds
   an `item_deps` suppression check as a **belt-and-suspenders** guard for cases
   where a predecessor is queued/active but not yet shipped. U3 will note both
   the `blocked`-status path and the `item_deps` blocks-chain path so authors
   pick the right one. This is called out for review as the primary coherence
   risk.
3. **Four tasks, one per template + a terminal coherence sweep.** Each edit is a
   single file (satisfies the 2-hour rule and `<3 files`), single skill domain
   (template authoring). Cross-set coherence can only be validated after all
   three edits exist, so U4 is a distinct verifiable milestone — matching the
   intake's "coherent as a set, not three isolated edits" requirement. The
   shipment keeps the four tasks together.
4. **No new template variables.** All edits reference backlogit-native concepts
   (`custom_fields.queue_position`, `item_deps`, `queue view --type shipment`),
   not new customization points. This keeps the install-harness SKILL.md
   variable-resolution table untouched and lowers blast radius.

## Risks and Caveats

* **R-1 (coherence): the two suppression mechanisms.** `status: blocked` (canonical
  lifecycle) vs `item_deps` suppression in the selection rule could confuse
  authors. *Mitigation*: U1 scopes suppression to `--status queued` shipments
  only; U3 documents both paths and when to use each. Flagged for plan-review.
* **R-2 (external assumption): `dep_type` collapse to `blocks`.** The intake asserts
  backlogit v1.7.0 collapses `dep_type` to `blocks` on sync/rehydrate. Verified
  only from the schema doc's allowed set, not by a live mutation (mutation is out
  of Stage scope). *Mitigation*: U3 states the behavior descriptively and tells
  authors to use `--type blocks` explicitly; if the collapse behavior differs in
  a future backlogit version, only the playbook note needs updating.
* **R-3 (blast radius): three coupled template families.** A change in one that is
  not mirrored in the others degrades cross-reference integrity. *Mitigation*:
  U4 terminal coherence sweep; reciprocal cross-references authored in U1–U3.
* **R-4 (rollback): trivial, but targets Ship's implementation commit(s), not
  this staging commit.** This staging commit contains only the plan + backlog
  metadata and does **not** modify the templates or the installed mirror, so
  reverting it cannot undo a sequencing regression. Rollback = `git revert` the
  **downstream Ship implementation commit(s)** that edit the three templates, the
  installed Orchestrator mirror (`.github/agents/_orchestrator.agent.md`), and the
  manifest checksum. No data migration, no runtime state.

## Plan Hardening Signals (REQUIRED)

| Signal | Present? | Justification |
|---|---|---|
| Public API, schema, or contract change | **yes** | Changes the Orchestrator shipment-**selection contract** (Step 2) and the P-017 dark-mode activation/telemetry **policy contract**. No JSON schema change, but agent-behavior contracts change. |
| Security, auth, permission, or compliance-sensitive behavior | no | No auth/secrets/permission surface touched. |
| Migration, backfill, destructive/irreversible action | no | Template text only; no data migration; `git revert` reverses it. |
| External integration, operator checkpoint, or external dependency | **yes** | Depends on external backlogit binary (v1.7.0) behavior: `queue_position` sort, `item_deps` blocks semantics, and `dep_type→blocks` collapse. |
| High runtime, rollout, or rollback risk | partial | Rollback is trivial; but a mis-authored selection rule could **mis-sequence shipments during an autonomous P-017 dark run** — elevated rollout consequence in dark mode. |

**Requires plan hardening: yes** — two clear signals (behavior-contract change +
external-dependency assumption) plus elevated dark-mode rollout consequence and a
broad blast radius across three template families. Proceed to `plan-harden`
before `plan-review`.

## Runtime Verification and Closure

* **Runtime surfaces changed**: none at execution time — these are documentation
  templates. The *effective* runtime surface is the Orchestrator's dark-run
  selection behavior once installed. Verification is by review/render, not by
  executing code.
* **What verification should prove before absorption**: (a) valid Markdown across
  ≥3 profiles; (b) no unresolved variables; (c) reciprocal cross-references
  resolve; (d) the selection rule, P-017 scope, and playbook describe one
  coherent mechanism; (e) the `blocked`-vs-`item_deps` reconciliation is
  unambiguous.
* **Operational closure artifact**: none beyond the shipment closure the Ship
  agent produces downstream. Rollback trigger = any post-merge report that dark
  runs mis-sequence shipments; rollback = **revert the downstream Ship
  implementation commit(s)** (the template + installed-mirror + manifest-checksum
  edits), **not** this staging commit, which carries only plan/backlog metadata.
  Owner = Stage (author) → Ship (execution).

## Plan Hardening

**Hardening required: yes.** Two hardening signals are present (agent-behavior
contract change + external-dependency assumption on backlogit v1.7.0), the blast
radius spans three coupled template families, and the effective change alters
autonomous P-017 dark-run shipment selection. Hardening was performed as a
narrow reinforcement between `impl-plan` and `plan-review`.

### Risk triggers and protected invariants

* **Trigger T1 — behavior-contract change**: Orchestrator Step 2 selection rule
  and P-017 activation/telemetry contract.
* **Trigger T2 — external dependency**: backlogit `queue_position` sort,
  `item_deps` blocks semantics, and `dep_type→blocks` collapse-on-sync.
* **Invariant I1**: Preserve P-001 (one Ship release unit at a time) — the new
  selection rule must not enable parallel release-unit shipping.
* **Invariant I2**: Preserve P-016 (single active worktree) — sequencing is about
  *ordering* queued shipments, never about running them in parallel.
* **Invariant I3**: Preserve P-017 "Scope rule" — the ordered scope MUST NOT
  silently expand beyond the declared shipment sequence.
* **Invariant I4**: Preserve the existing Step 2 rule #2 guard (P-001/P-016/P-020
  post-merge-closure gating) verbatim; the selection edit touches only rule #1.
* **Invariant I5**: Preserve 097-S — downstream shipment manifests stay
  task-ID-only; nothing in this plan lists a covering feature in a manifest.

### Learnings and instruction files consulted

* `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md` — shipment
  `blocked` lifecycle; drives the `blocked`-vs-`item_deps` reconciliation.
* `docs/compound/097-S-shipment-task-only-safe-close.md` — task-only manifest
  contract (relevant to harvest/shipment, not the edits themselves).
* `templates/instructions/backlogit-sql-schema.instructions.md.tmpl` —
  `item_deps` schema and `dep_type` allowed values.
* `templates/policies/workflow-policies.md.tmpl` P-017 section — activation
  contract and `DARK_MODE_SCOPE` telemetry event (edit target).

### Risky actions (ProposedAction / ActionRisk)

This plan produces **no destructive or irreversible runtime actions**. The only
mutations are documentation-template edits and backlog/shipment creation, all
`git revert`-reversible.

| ProposedAction | ActionRisk | Approval needed | ActionResult expectation |
|---|---|---|---|
| Edit three `.tmpl` files (U1–U3) | low | no (Stage may commit planning/backlog + template staging artifacts? NO) | **NOTE:** template `.tmpl` mutation is Ship execution, NOT Stage. Stage produces the *plan* only; the edits are executed by Ship. |
| Create backlog feature+tasks, wire deps, create queued shipment | low | no | Reversible via archive/delete; task-only manifest. |

> **Role-boundary reinforcement (P-010/P-016)**: This plan is authored by Stage.
> Stage does **not** perform the U1–U4 template `.tmpl` edits — those are Ship
> execution work. Stage's deliverable is the reviewed plan + backlog + queued
> shipment. The "Files" and "Execution posture" notes in each unit are
> instructions **for Ship**, not actions Stage will take.

### Added verification / rollback / monitoring detail

* **Verification depth**: U4 must run markdownlint heading checks (MD001/MD025/
  MD041) and a variable-completeness scan (`grep '{{' | grep -v known-vars`) on
  all three files; confirm reciprocal cross-references resolve by name.
* **Reconciliation acceptance (R-1)**: U3 must contain an explicit "when to use
  `status: blocked` vs an `item_deps` blocks-chain" note; plan-review must FAIL
  U3 if that note is absent.
* **External-assumption guard (R-2)**: U3 phrases the `dep_type→blocks` collapse
  descriptively and instructs `--type blocks` explicitly; no code depends on the
  collapse, so a future backlogit change only requires a doc-note update.
* **Rollback trigger**: any post-merge evidence that dark runs mis-sequence
  shipments → `git revert` the **downstream Ship implementation commit(s)** that
  edit the templates, the installed Orchestrator mirror
  (`.github/agents/_orchestrator.agent.md`), and the manifest checksum. Reverting
  this staging commit would only remove plan/backlog metadata and would **not**
  undo the behavior change. Ship should keep the implementation to a cohesive
  commit set (all four tasks in one shipment) so the revert target is
  well-defined.
* **Owner / validation window**: Stage (author) → Ship (executes + validates at
  build/review) → operator confirms during the first multi-shipment dark run.

### Review-gate capability risks carried forward

* Reviewer-subagent dispatch is **not** exposed in this Stage session. Plan-review
  MUST therefore run in `single-agent-declared-degradation` mode, apply every
  selected persona's rubric inline, and emit literal `dispatch_mode:` and
  `decision:` markers (P-012). Do not silently skip a persona.
* Triggered personas: Constitution Reviewer, Scope Boundary Auditor, Learnings
  Researcher (always-on); Architecture Strategist (always-on cross-model);
  **Agent-Native Parity Reviewer** (this plan changes agent-facing orchestration
  behavior). Security Lens is **not** triggered (no auth/secrets/API surface).

### Unresolved operator decisions

None block safe planning. Open item for review awareness only: whether U3 should
also cross-link `backlogit-sql-schema.instructions.md.tmpl` (out of the declared
3-file scope). Default: **do not** expand scope; keep the reference conceptual.

## Plan Review

dispatch_mode: single-agent-declared-degradation
decision: PASS

**Gate: PASS.** No P0/P1 findings. Two P2 findings were raised and resolved
in-plan within a single review-fix cycle (see below); residual items are P3
advisory. Plan hardening was required (P-006) and is present and materially
complete.

### Dispatch capability declaration (P-012)

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent
persona pass`. Reviewer-subagent dispatch is not exposed in this Stage session,
so every selected persona rubric was applied inline. `TOOL_DEGRADED:
model-specific-review-routing — declared fallback: same-model rubric pass` (no
anchor cross-model route available). No persona was skipped.

### Persona coverage

| Persona | Trigger | Mode | Findings |
|---|---|---|---|
| Constitution Reviewer | always-on | inline | 0 (P-001/P-006/P-008/P-010/P-016/097-S all preserved) |
| Python Reviewer | always-on | inline | 0 (no code change; documentation templates only) |
| Scope Boundary Auditor | always-on | inline | 1 P2 (resolved) |
| Learnings Researcher | always-on | inline | 1 P3 (advisory) |
| Architecture Strategist | always-on cross-model | inline (same-model degraded) | 1 P2 (resolved) |
| Agent-Native Parity Reviewer | triggered (agent-facing orchestration behavior) | inline | 1 P3 (advisory) |
| Security Lens Reviewer | not triggered (no auth/secrets/API/trust boundary) | n/a | — |

### Findings by severity

**P0 — none.**

**P1 — none.**

**P2 (resolved in this cycle):**

* **P2-A (Architecture Strategist) — precedence between `queue_position` and
  `item_deps` was implicit.** If manual queue order disagrees with the
  blocks-chain, the rule did not state which wins. *Resolution*: U1 now specifies
  `item_deps` suppression as a **hard eligibility gate**; `queue_position` orders
  only among eligible shipments. Eligibility wins on conflict.
* **P2-B (Scope Boundary Auditor) — U4 "minor coherence touch-ups" invited scope
  drift.** *Resolution*: U4 is now **validation-only**; non-trivial fixes route
  back to the owning unit (U1–U3), keeping authorship in one place.

**P3 (advisory, no action required):**

* **P3-A (Learnings Researcher)**: The `item_deps` suppression is redundant-by-
  design with the `status: blocked` lifecycle (`2026-05-07-backlogit-shipment-
  status-constraints`). U3 already documents when to use each (belt-and-
  suspenders); future authors should not delete one assuming it duplicates the
  other. Captured in Decision 2 and Risk R-1.
* **P3-B (Agent-Native Parity Reviewer)**: Ensure the playbook's CLI verbs map to
  canonical registry operations — `queue view`→`get_queue`, `dep add`→
  `add_dependency`. They do; parity between agent and human CLI is preserved.
* **P3-C (Constitution Reviewer)**: Consider adding a P-017 changelog row in
  `workflow-policies.md.tmpl` when U2 lands (optional; the section already has a
  changelog table).

### Hardening & runtime-surface check

* Plan hardening required and present: **yes / yes**. Risky-action classification
  present; no destructive/irreversible runtime actions (documentation edits +
  reversible backlog creation).
* Runtime surfaces: no executable surface changes. Effective surface = the
  Orchestrator's installed dark-run selection behavior; verified by render/review
  (U4), not by code execution. Verification and closure expectations are recorded
  in the plan's "Runtime Verification and Closure" section.

### Role-boundary note carried to harvest/Ship

The U1–U4 `.tmpl` edits are **Ship execution work**, not Stage actions. Stage's
output is this reviewed plan + the harvested backlog + a queued shipment. Harvest
may proceed on `decision: PASS`.
