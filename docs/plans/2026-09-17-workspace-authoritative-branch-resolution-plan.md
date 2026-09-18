---
title: "Workspace-authoritative implementation-branch resolution for the pipeline-topology gate"
description: "Implementation plan routing every pipeline-topology branch decision through one shared resolve_expected_branches() applying strict two-rung precedence — explicit custom_fields.implementation_branch, then title-derived aliases as fallback only — with a present-but-malformed explicit value failing closed as IMPLEMENTATION_BRANCH_MALFORMED and never falling back, validation implementing a STRICT SUPERSET of the git check-ref-format --branch rejection set with one enumerated deliberate divergence (the @{...} revision-suffix family, which git accepts and this workspace path contract rejects) plus explicit rejection of leading-hyphen and option-like values as a standalone invariant, gate JSON emitting resolution_source, selected_branch, and ordered expected_branches, and the seven-row regression matrix from stash 14F4D6F3 pinned alongside the 018-S/020-S/025-S field regressions."
doc_type: plan
source: docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
date: 2026-09-17
status: reviewed
revision: 4
revision_note: "Revision 4 (remediation cycle 2) adopts decision revision 3 and closes two findings. (1) FACTUAL CORRECTION: revision 3 claimed the validator's accept/reject sets were IDENTICAL to `git check-ref-format --branch`. That claim was false. `git check-ref-format --branch` ACCEPTS and resolves the `@{-N}` shorthand, while rule V10 rejects any name containing `@{`; and the leading-hyphen rejection (V2/V3) cannot be derived from git's behaviour at all, because git's CLI cannot unambiguously receive a leading-hyphen argument to judge. Revision 4 restates the relationship truthfully as a STRICT SUPERSET OF REJECTIONS with an explicitly enumerated divergence set D = the `@{...}` revision-suffix family including `@{-N}`. The shorthand is DELIBERATELY REJECTED under a stricter workspace path contract; normalization was considered and explicitly NOT chosen. V2/V3 are asserted as a standalone workspace invariant rather than as git equivalence. (2) PROPAGATION: the revision-3 design was never encoded into the executable backlog records — the withdrawn `workspace_convention` rung still appeared in the feature and task bodies, and the red-before-implementation ordering existed only as prose. Revision 4 requires exactly two rungs everywhere and requires the task graph to be machine-encoded with red contract tests preceding implementation, green verification following it, and workaround retirement gated on ALL proving test families. The bounded audit trail lives in `linked_review`."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_prior_deliberation: docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
source_prior_review: docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md
source_bug_report: docs/bugs/2026-09-16-autoharness-pipeline-topology-explicit-branch-contract-bug.md
source_design_document:
  path: "N/A — not present in this repository"
  status: unavailable-external
  note: "Stash 86498B64's intake named docs/design-docs/2026-09-10-autoharness-workspace-driven-branch-resolution-design.md. No such file exists in this repository at any ref (verified by git log --all -- <path>, zero results). It is treated as unavailable external provenance. The operative, durable, in-repository source is the design summary preserved verbatim inside the 86498B64 stash entry, archived at .backlogit/archive/stash.jsonl."
durable_design_source: .backlogit/archive/stash.jsonl
source_stash_id: 86498B64
stash_ids:
  - 86498B64
  - 14F4D6F3
merged_stash_ids:
  - 14F4D6F3
prior_learnings:
  - docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md
  - docs/compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
  - docs/compound/2026-08-17-branch-rename-after-pr-open-auto-closes-pr.md
linked_review: docs/reviews/2026-09-17-workspace-authoritative-branch-resolution-plan-review.md
review_history:
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-04.md
review_history_note: "Attempts 01-02 were authored as one mutable file covering two cycles; it is preserved verbatim and classified rather than retroactively split into records that were never independently authored. Attempt 03 is a conforming single-attempt immutable artifact. Attempt 04 records local review cycle 2 (BLOCKED at revision 3, on non-propagation of the design into the executable backlog records) and the Stage remediation response that produced this revision."
latest_review_attempt: 3
latest_review_artifact: docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-04.md
latest_review_verdict: PASS
covering_feature: 170-F
shipment: 178-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
plan_hardening_section: "## Plan Hardening Record (P-006)"
tags:
  - "pipeline-topology"
  - "branch-ownership"
  - "p-022"
  - "fail-closed-design"
  - "merged-stash"
---

# Workspace-authoritative implementation-branch resolution

## Provenance and merge

This plan covers **two stash entries merged on evidence** (decision **D1**):

* `86498B64` — the covering feature (workspace-driven branch
  resolution), carrying the open decision about declarative workspace templates.
  Its intake declares a source design document at
  `docs/design-docs/2026-09-10-autoharness-workspace-driven-branch-resolution-design.md`.
  **That file has never existed in this repository.** `git log --all -- <path>`
  returns zero commits, and `docs/design-docs/` does not contain it at `HEAD`.
  It is therefore recorded as **unavailable external provenance**, not as a
  readable source, and nothing in this plan may be justified by citing it.
  The durable in-repository source is the design summary preserved verbatim
  inside the `86498B64` stash entry, now at `.backlogit/archive/stash.jsonl`;
  every requirement the summary states is restated in full in this plan, so no
  requirement below depends on the missing file. Recorded as an advisory
  provenance gap in the deliberation.
* `14F4D6F3` — the same defect observed in the field, carrying a seven-row
  regression matrix, acceptance criteria, and the
  `IMPLEMENTATION_BRANCH_MALFORMED` token name.

Both name `src/autoharness/gates/topology.py`, the same authority question
(what is the release unit's implementation branch called), and the same
mechanism. They are one contract. Both IDs are carried on this plan, on the
covering feature, on every task, and on the review; neither entry is destroyed.

`86498B64`'s recorded sequencing precondition — harvest immediately after
`173-S` is executed — is **satisfied**: `173-S` and `174-S` both report
`status: archived`.

## Problem

`_branch_aliases()` / `_resolve_shipment_from_branch()` in
`src/autoharness/gates/topology.py` build `expected_branches` only from
title-derived slug aliases. The authoritative P-022 branch contract recorded on
the shipment as `custom_fields.implementation_branch` is never read.

A shipment checked out on exactly the branch named in its own
`implementation_branch` is therefore false-blocked with `BRANCH_MISMATCH`
(`blocked: true`, exit 1) whenever its descriptive title does not slugify to
that branch. The block is fail-closed with no honored explicit-contract path,
so the only escapes are an unsafe `--force` or renaming the branch off its
authoritative contract — and renaming after a PR is open auto-closes the PR
(`docs/compound/2026-08-17-branch-rename-after-pr-open-auto-closes-pr.md`).

Observed on `025-S` and `020-S`, currently masked by temporary title-alias
workarounds; blocks downstream release unit `018-S`, whose explicit branch
cannot be renamed without violating P-016/P-022.

## Design

### Single resolver, strict precedence

One `resolve_expected_branches()` is the sole branch authority, used by **all
four phases** — `pre_claim`, `post_claim`, `lifecycle`, `ambient`. No phase may
compute branches by any other path.

| Rung | Source | `resolution_source` |
|---|---|---|
| 1 | Explicit `custom_fields.implementation_branch` on the shipment record | `explicit_contract` |
| 2 | Title-derived slug aliases (`_branch_aliases()`) | `title_alias` |

The precedence ladder has **exactly two rungs**. Revision 2 reserved a third,
"configured workspace naming convention — present, tested, and empty". That
rung is **removed**: no `.autoharness/config.yaml` key authorizes it, no schema
declares it, and decision **D1** explicitly defers the declarative-template
tier. A wired-but-unreachable precedence position backed by no config contract
is a speculative surface that constrains a future design before that design is
decided, and its "test asserting it is never selected" is a tautology that pins
nothing. When the declarative tier is actually decided and an authorized config
contract exists, inserting a rung between 1 and 2 is a small, local change to a
single ordered ladder — the cost this plan was paying rent to avoid is lower
than the cost of carrying an unauthorized contract surface.

Adjacency to `165-F`'s `gates.pipeline_topology.unsequenced_shipment` key is
noted and avoided; this release unit adds no config key at all.

### Fail-closed on malformed explicit value

A **present-but-malformed** `implementation_branch` — blank, whitespace-only,
not a valid Git branch short name, or otherwise unparseable — fails closed with
`IMPLEMENTATION_BRANCH_MALFORMED` and **never falls back to rung 2**.

This is the load-bearing asymmetry: *absent* means "no contract, fall back";
*present-but-invalid* means "a contract was declared and is broken, halt". The
design summary's `BRANCH_POLICY_INVALID` is recorded as a synonym so that text
remains readable; `IMPLEMENTATION_BRANCH_MALFORMED` is the emitted token
because it names the field rather than an abstract policy.

#### Validation rule set

Validation is a Git branch **short name** check implemented in Python and
pinned against the observed behaviour of `git check-ref-format --branch <value>`.

**The relationship is a STRICT SUPERSET OF REJECTIONS, not an identity.**
Revision 3 claimed the two accept/reject sets were *equivalent*. That claim was
false and is corrected here:

> For every value `v`, if `git check-ref-format --branch v` rejects `v`, this
> validator also rejects `v`. The converse does **not** hold. The set of values
> this validator rejects and git accepts is exactly the enumerated divergence
> set **D**, defined below. There is no other divergence, in either direction.

**Divergence set D — the `@{...}` revision-suffix family.** `git
check-ref-format --branch` treats its argument as a branch *expression* and
therefore **accepts and resolves** the `@{-N}` shorthand (`@{-1}` = "the
previously checked-out branch"), along with the wider `@{...}` suffix family.
Rule **V10** rejects any value containing `@{`.

This divergence is **deliberate, and normalization was explicitly considered and
not chosen.** The two available resolutions were:

1. **Normalize** — resolve `@{-N}` to the concrete branch name it denotes, then
   validate the result.
2. **Reject under a stricter workspace path contract** — treat `@{...}` as
   outside the set of values this workspace will accept at all.

Option 2 is adopted. `selected_branch` is not merely handed to `git`; it is
recorded in gate JSON, compared against shipment records, and used to build
**filesystem paths** for worktrees. A value whose meaning depends on the
*reflog state of the invoking checkout* is not a stable identifier: `@{-1}`
denotes a different branch in two different clones, and a different branch in
the same clone five minutes later. Normalizing it would mean the gate's recorded
answer silently depends on ambient session history, which defeats the entire
purpose of a workspace-**authoritative** resolution contract. Rejecting it keeps
the contract referentially transparent.

A value is rejected when **any** of the following holds:

| # | Rejection rule |
|---|---|
| V1 | Empty, or whitespace-only |
| V2 | Begins with `-` (hyphen). **Standalone workspace invariant** — see note below; a leading hyphen makes the value indistinguishable from a command-line option at every downstream call site |
| V3 | Is exactly `-` or consists only of `-` characters |
| V4 | Begins or ends with `/`, or contains `//` |
| V5 | Begins or ends with `.`, or contains `..` |
| V6 | Contains an ASCII control character (`\x00`–`\x1F`, `\x7F`) or a space |
| V7 | Contains any of `~ ^ : ? * [ \` |
| V8 | Ends with `.lock`, or any `/`-delimited component ends with `.lock` |
| V9 | Any `/`-delimited component begins with `.` |
| V10 | Is exactly `@`, or contains the sequence `@{` — **this is divergence set D**; git accepts `@{-N}` and this contract does not |
| V11 | Ends with `.` |

**V2 and V3 are a standalone workspace invariant, NOT a git derivation.**
Revision 2 omitted them entirely, so `--force`, `-D`, `--all`, and any other
option-shaped string would have been accepted as a valid branch name and then
emitted as `selected_branch` into gate JSON and downstream Git invocations —
an argument-injection-shaped hazard, not a cosmetic gap. Revision 3 added them
but justified them as "`git check-ref-format --branch` rejects it". **That
justification is withdrawn as unsound**: git's CLI cannot unambiguously *receive*
a leading-hyphen argument in the first place — the shell and git's own option
parser consume it before any ref-name check runs — so git's behaviour cannot
establish the rule either way. V2/V3 are therefore asserted on their own terms,
as a property this workspace requires of any value it will place on a command
line, and they are excluded from the equivalence corpus rather than pinned by it.

**Option-like rejection is stated as its own invariant**, independent of any
`check-ref-format` derivation: no resolved `selected_branch` may begin with
`-`, on any rung, from any source, including a title-derived alias. The
title-alias path is slug-derived and cannot normally produce one, but the
invariant is asserted at the resolver's exit rather than assumed from its
inputs.

**Superset pinning (replaces "equivalence pinning").** A test drives a corpus of
accept and reject values through both the Python validator and `git
check-ref-format --branch`, and asserts the **superset property** rather than
identity:

* Any value git rejects, the validator must reject. A disagreement here is a
  failure.
* Any value git accepts, the validator must also accept **unless the value is a
  member of D**, in which case the validator must reject it. A value that
  diverges *outside* D is a failure, in either direction.
* D is enumerated explicitly in the test as a frozen literal set, so silently
  growing the divergence is itself a test failure.
* V2/V3 inputs are excluded from the git-driven arm (git cannot judge them) and
  are asserted against the frozen expected-outcome corpus only.

Where the local `git` binary is unavailable, the test **skips explicitly and
loudly** rather than passing vacuously, and the frozen expected-outcome corpus
is asserted regardless.

### Gate output

Every phase's JSON gains, unconditionally:

* `resolution_source` — one of `explicit_contract`, `title_alias`
* `selected_branch` — the single branch the gate considers authoritative
* `expected_branches` — the **ordered** list actually evaluated

These are emitted on both the pass and the block path, so a `BRANCH_MISMATCH`
report says which authority produced the expectation it is enforcing.

### Reader change

`FilesystemTopologyReaders.list_shipments()` parses `custom_fields.implementation_branch`
from the nested map, validates it, and surfaces it on `ShipmentState`.
Shipments without the field behave **exactly** as before — this is the
compatibility invariant, and it has its own regression case.

## Work Breakdown

| # | Task | Scope | Blocked by |
|---|---|---|---|
| T0 | **RED** — author the validator, precedence and gate-JSON contract tests and observe them failing before any implementation exists | `tests/` | — |
| T1 | **IMPLEMENTATION** — branch short-name validator: rules V1–V11, the standalone option-like invariant, and the `git check-ref-format --branch` **superset** corpus with divergence set D enumerated | `src/autoharness/gates/topology.py` | T0 |
| T2 | Parse `custom_fields.implementation_branch` in `list_shipments()`; validate it via T1; add the field to `ShipmentState` | `src/autoharness/gates/topology.py` | T1 |
| T3 | Implement `resolve_expected_branches()` with the **two-rung** precedence and the no-fallback-on-malformed asymmetry | `src/autoharness/gates/topology.py` | T1, T2 |
| T4 | Route all four phases through the single resolver; remove every other branch-derivation path | `src/autoharness/gates/topology.py` | T3 |
| T5 | Emit `resolution_source`, `selected_branch`, ordered `expected_branches` on pass and block paths | `src/autoharness/gates/topology.py` | T4 |
| T6 | **GREEN** — seven-row regression matrix from `14F4D6F3` observed passing | `tests/test_gates_topology.py` | T4 |
| T7 | **GREEN** — field regressions for `018-S`, `020-S`, `025-S`, plus the no-field compatibility invariant | `tests/test_gates_topology.py` | T4 |
| T8 | **GREEN** — CLI-surface tests for the new JSON fields and the malformed-value exit path | `tests/test_gate_pipeline_topology_cli.py` | T5 |
| T9 | Gate documentation: precedence table, validation rule set including divergence set D, token table, compatibility note | `docs/` | T5 |
| T10 | Retire the temporary title-alias workarounds on `025-S`/`020-S` | backlog data + docs | T6, T7, T8 |

### Dependency rationale (revision 4)

Revision 2 listed the same surfaces but encoded no ordering beyond "T8 is
sequenced last" in prose, and its ordering was wrong in two places. Revision 3
corrected the ordering but left it partly unencoded in the backlog records.
Revision 4 requires all of the following as machine-encoded `blocks` edges:

0. **Red precedes implementation.** T0 authors the validator, precedence and
   gate-JSON contract tests and observes them **failing** against a missing
   entry point. T1 blocks on T0. **T0 does not depend on T1** — that asymmetry
   is what makes it a genuine red phase rather than a test-after task with a
   suggestive title.
1. **The model and the resolver must precede the integration.** T2 (reader
   surfacing the field on `ShipmentState`) and T3 (the resolver itself) are
   what T4 integrates the four phases against. Executing T4 first means
   rewriting four call sites to consume a resolver that does not yet exist,
   then rewriting them again. T1 precedes both because validation is the
   predicate T2 rejects malformed values with and T3's fail-closed asymmetry
   branches on — a resolver written before its validator has to inline a second
   provisional one, which is the duplicate-definition class this plan exists to
   eliminate.
2. **Green verification follows implementation.** T6 and T7 block on T4; T8
   blocks on T5. Each observes the previously-red contract passing against the
   shipped surface, and adds the regression cases that only make sense against
   a real implementation.
3. **Workaround removal is genuinely last, and gated on ALL proving families.**
   T10 retires the title-alias workarounds that currently keep `025-S` and
   `020-S` unblocked. It is blocked by T6, T7, **and** T8 — every test family
   that proves the explicit-contract path actually works, including the CLI
   surface. Revision 2's prose placed it "last" in a table whose order carried
   no enforcement; a mid-execution reordering could have removed the workaround
   while the replacement path was still only partially integrated, blocking two
   live shipments with no route back except a prohibited `--force`.

T9 is documentation and blocks on T5 so the emitted-field table it documents is
the one that shipped.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* All seven matrix rows pass, including both malformed-value rows.
* The **superset property** holds on every corpus value: every value git rejects
  is rejected by the validator; every value git accepts is accepted by the
  validator **unless** it is a member of divergence set D (the `@{...}`
  revision-suffix family, including `@{-N}`), which the validator rejects under
  V10. No divergence exists outside D, in either direction.
* Divergence set D is pinned as a frozen literal in the test, so growing it
  silently is a test failure.
* V2/V3 (leading-hyphen / option-shaped) inputs are asserted against the frozen
  expected-outcome corpus only and are **excluded** from the git-driven arm,
  because git's CLI cannot unambiguously receive such an argument to judge.
* Every option-shaped value in the corpus — `-`, `--`, `-D`, `--force`,
  `--all`, `-x`, `--` — is rejected with `IMPLEMENTATION_BRANCH_MALFORMED`,
  and no such value ever appears as `selected_branch` in gate JSON.
* The resolver-exit invariant holds: no returned `selected_branch` begins with
  `-` on any rung.
* Exactly two `resolution_source` values are reachable; no
  `workspace_convention` string appears anywhere in the shipped code, tests,
  docs, **or backlog records**.
* A shipment with no `implementation_branch` produces byte-identical gate JSON
  to `main` except for the three additive fields.
* `autoharness gate check` passes on every modified file.
* No `--force` invocation appears anywhere in the new tests or docs.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Malformed explicit value silently falls back, re-creating the defect inverted | Dedicated matrix rows assert `IMPLEMENTATION_BRANCH_MALFORMED` and assert rung 2 was **not** consulted |
| R2 | One of the four phases keeps a private branch-derivation path | T4 removes every other path; a structural test asserts exactly one call site computes branches |
| R3 | The Python validator drifts from real Git behaviour | T1's corpus is driven through `git check-ref-format --branch` itself and fails on any disagreement outside the frozen divergence set D; absence of `git` skips loudly rather than passing vacuously |
| R8 | Divergence set D grows silently, turning a deliberate exception into an unnoticed drift | D is pinned as a frozen literal set in the superset test; any value diverging outside D fails in either direction |
| R4 | Merge contention with `165-F`'s `_shipment_readiness_check` work | `165-F`/`173-S` is **archived**; the recorded contention window is closed |
| R5 | Retiring the title-alias workarounds breaks a shipment mid-flight | T10 is blocked by T6, T7, and T8 — a machine-encoded edge, not a table position — and touches only backlog data for shipments whose explicit contract the resolver now honors |
| R6 | An option-shaped branch value reaches a Git command line | V2/V3 reject it at validation as a **standalone workspace invariant** (not a git derivation — git cannot judge such input), and the resolver-exit invariant re-asserts it independently of which rung produced the value |
| R7 | Removing rung 2 makes the deferred declarative tier harder to add later | The ladder is a single ordered structure in one function; inserting a rung is local. Carrying an unauthorized config surface with no schema behind it was the larger cost |

## Out of scope

* Declarative workspace-level branch templates in `.autoharness/config.yaml`
  (deferred per decision **D1**). The reserved rung that revision 2 shipped for
  them is removed; no placeholder, no `resolution_source` value, and no config
  key is carried for the deferred tier.
* Any vendor identifier (ADO, Jira) in the engine.
* Repository-supplied executable branch rules — workspace policy stays
  declarative data only.
* Sequencing authority (`_shipment_readiness_check`, `dag-root`,
  `UNSEQUENCED_SHIPMENT`), which is a different contract surface.
* Any `--force` path.

## Plan Hardening Record (P-006)

Hardening applied 2026-09-17, re-run 2026-09-18 during remediation cycle 1.
Revision 2 declared `plan_hardening_status: complete` without persisting this
record; that gap is H0 below.

**Hardening trigger.** Elevated blast radius: the change rewrites the branch
authority for **all four phases** of a fail-closed gate that can block every
shipment in the workspace; it changes a gate's JSON output contract that other
tooling reads; and its final task mutates live backlog records for two
currently-unblocked shipments.

**Protected invariants.**

* A shipment with **no** `implementation_branch` must behave byte-identically
  to today apart from the three additive JSON fields. This is the compatibility
  invariant and it has its own regression case.
* Fail-closed posture is never weakened. A declared-but-broken contract halts;
  it never degrades to a guess.
* No `--force` path is introduced, documented, or exercised.
* No resolved `selected_branch` may begin with `-`.
* Branch renaming is **not** an acceptable remedy — renaming after a PR is open
  auto-closes the PR
  (`docs/compound/2026-08-17-branch-rename-after-pr-open-auto-closes-pr.md`).

**Instructions and learnings consulted.**
`docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`,
`docs/compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md`,
`docs/compound/2026-08-17-branch-rename-after-pr-open-auto-closes-pr.md`,
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`,
`.github/policies/workflow-policies.md` (P-016, P-022),
`docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md`,
and the verbatim `86498B64` design summary in `.backlogit/archive/stash.jsonl`.

| # | Hardening finding | Resolution |
|---|---|---|
| H0 | Revision 2 asserted `plan_hardening_status: complete` with no persisted hardening record | This section is the record; `plan_hardening_section` in frontmatter names it |
| H1 | The validation rule set omitted leading-hyphen and option-shaped values, so `--force` or `-D` would have validated as a branch name and been emitted as `selected_branch` into gate JSON and downstream Git invocations | V2/V3 added and enumerated; a resolver-exit invariant re-asserts it independently of rung; the corpus pins every option-shaped form |
| H2 | "Valid Git branch short name" was an informal list, not an equivalence claim, so validator/Git divergence was undetectable | Rule set V1–V11 stated explicitly and pinned by a corpus driven through `git check-ref-format --branch`. **Superseded in revision 4**: the equivalence claim was itself false (git accepts `@{-N}`, V10 rejects it; and git cannot judge leading-hyphen input at all). Restated as a strict superset of rejections with divergence set D enumerated as a frozen literal, and V2/V3 excluded from the git-driven arm |
| H3 | The equivalence test would pass vacuously on a machine without `git` | The test skips loudly and still asserts the frozen expected-outcome corpus |
| H4 | Task ordering existed only as table position; the integration task could execute before the resolver and reader it integrates | `blocks` edges encoded: T1 → T2 → T3 → T4 → T5; rationale recorded in the plan body |
| H5 | Workaround retirement was "sequenced last" in prose only, so a reordering could strand `025-S`/`020-S` with no non-`--force` route back | T10 blocked by T6, T7, **and** T8 — every proving test family including the CLI surface |
| H6 | Rung 2 was an unauthorized speculative contract surface: no config key, no schema, no decision authorizing it, and a tautological test | Rung removed; ladder reduced to two rungs; Verification asserts no `workspace_convention` token survives anywhere |
| H7 | The plan cited a design document that has never existed at any ref, so a reader could not verify any requirement traced to it | Recorded as `unavailable-external` provenance with the verification method stated; durable source redirected to the archived stash entry |
| H8 | T10 mutates live backlog records for two shipments — the only non-additive action in the unit | Classified below as the single Medium-risk `ProposedAction` with an explicit rollback |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Rewrite branch derivation for all four gate phases (T4) | Medium — a regression false-blocks every shipment | Standard PR review; gated by T1–T3 landing first | Revert `topology.py`; no persisted state changes |
| Add three fields to gate JSON on both paths (T5) | Low — additive only | Standard PR review | Revert; compatibility invariant test proves the non-additive surface is untouched |
| Retire live title-alias workarounds on `025-S`/`020-S` (T10) | **Medium** — mutates live backlog records for two unblocked shipments | Blocked by T6/T7/T8; operator confirmation before mutating either record | Re-add the title alias to the shipment record; the workaround is a backlog-data change, fully reversible |
| Remove rung 2 from the ladder | Low — the rung was unreachable by construction | Standard PR review | Re-insert; the ladder is one ordered structure in one function |

**Rollback coupling.** T1–T5 are source-only and revert as one `topology.py`
change set. T6–T9 are test/doc-only. T10 is the only task touching persisted
state and is independently reversible.

**Monitoring and validation window.** After merge, the first `pre_claim`
invocation on a shipment carrying an explicit `implementation_branch` is the
live signal: `resolution_source` must read `explicit_contract`. The first
invocation on a shipment with no such field must read `title_alias` and produce
an unchanged verdict. Both are observable in the gate's own JSON.

**Operator checkpoints.** One: before T10 mutates `025-S` or `020-S`.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers and MUST apply the Python Reviewer
persona inline, because this is the only plan in the portfolio whose primary
deliverable is executable Python on a fail-closed gate path.

**Unresolved operator decisions blocking safe execution.** None. The
declarative-template tier remains deferred and no longer has a placeholder in
this release unit.
