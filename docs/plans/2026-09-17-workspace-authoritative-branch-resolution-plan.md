---
title: "Workspace-authoritative implementation-branch resolution for the pipeline-topology gate"
description: "Implementation plan routing every pipeline-topology branch decision through one shared resolve_expected_branches() applying strict two-rung precedence — explicit custom_fields.implementation_branch, then title-derived aliases as fallback only — with a present-but-malformed explicit value failing closed as IMPLEMENTATION_BRANCH_MALFORMED and never falling back, validation implementing a STRICT SUPERSET of the git check-ref-format --branch rejection set with one enumerated deliberate divergence set D of exactly two shapes (the bare `@`, and the resolvable `@{-N}` previous-checkout shorthand; the wider `@{...}` family is a SHARED rejection that git also refuses) plus explicit rejection of leading-hyphen and option-like values as a standalone invariant, gate JSON emitting resolution_source, selected_branch, and ordered expected_branches, and the seven-row regression matrix from stash 14F4D6F3 pinned alongside the 018-S/020-S/025-S field regressions."
doc_type: plan
source: docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
date: 2026-09-17
status: reviewed
plan_id: workspace-authoritative-branch-resolution
plan_role: active
revision: 7
supersedes: null
superseded_by: null
source_history:
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-05.md
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-06.md
  - docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-07.md
  - docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md
review_manifest: docs/reviews/2026-09-17-workspace-authoritative-branch-resolution-plan-review.md
revision_note: "Revision 7 is maintained as one coherent current-state contract rather than as an accreting record of corrections. Prior-revision deltas, superseded requirement variants, and reviewer chronology are not carried in the body: the immutable per-attempt review artifacts listed in source_history and the mutable verdict manifest named by review_manifest are the authoritative record of that chronology. Latest attempt and verdict are read from the manifest, never from this file."
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

The precedence ladder has **exactly two rungs**, and carries no reserved
position for the deferred declarative workspace-naming tier. No
`.autoharness/config.yaml` key authorizes such a tier, no schema declares it,
and decision **D1** explicitly defers it. A wired-but-unreachable precedence
position backed by no config contract is a speculative surface that constrains
a future design before that design is decided, and a test asserting it is never
selected is a tautology that pins nothing. When the declarative tier is
actually decided and an authorized config contract exists, inserting a rung
between rung 1 and rung 2 is a small, local change to a single ordered ladder.

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

**The relationship is a STRICT SUPERSET OF REJECTIONS, not an identity:**

> For every value `v`, if `git check-ref-format --branch v` rejects `v`, this
> validator also rejects `v`. The converse does **not** hold. The set of values
> this validator rejects and git accepts is exactly the enumerated divergence
> set **D**, defined below. There is no other divergence, in either direction.

**Divergence set D — the bare `@`, and the resolvable `@{-N}` shorthand only.**
Measured behaviour (`git version 2.55.0`, this repository, read-only probe):

| Probe | `git check-ref-format --branch` | V10 | Relationship |
|---|---|---|---|
| `@{-1}`, `@{-2}`, `@{-99}` | **exit 0**, prints the resolved branch name | rejects | **divergence** |
| `@` | **exit 0**, prints `@` | rejects | **divergence** |
| `@{-0}` | exit 128 | rejects | shared rejection |
| `foo@{1}`, `main@{0}`, `a@{b}` | exit 128 | rejects | **shared rejection** |
| `@{u}`, `@{upstream}`, `foo@{upstream}` | exit 128 | rejects | **shared rejection** |

git does **not** accept the wider `@{...}` family. `--branch` runs
`interpret_branch_name`, which expands only the `@{-N}` previous-checkout
shorthand; everything else is handed to `check_refname_format`, whose
"cannot contain the sequence `@{`" rule rejects it exactly as V10 does. The
ordinary `@{...}` suffix forms are therefore a **shared rejection**, not a
divergence; classifying them as divergences would make the superset test assert
a disagreement that does not exist.

The divergence is exactly two shapes:

1. the bare value `@`, which git accepts and V10 rejects; and
2. `@{-N}` for `N >= 1` **that actually resolves in the invoking repository**.

**`@{-N}` acceptance is repository-state-dependent, which is why the test needs
a fixture.** `git check-ref-format --branch '@{-1}'` succeeds only where the
reflog holds a previous checkout; in a freshly-initialized repository with no
checkout history the same value fails. The superset test therefore constructs a
**hermetic fixture repository** with a deterministic, scripted checkout history
so that `@{-1}` and `@{-2}` are known-resolvable, and asserts the divergence
only for those controlled cases. It MUST NOT probe `@{-N}` against the ambient
repository, whose reflog is arbitrary — that would make the assertion depend on
the developer's last `git checkout`. Unresolvable `@{-N}` values are asserted as
**shared rejections** in the same fixture.

This divergence is **deliberate, and normalization is explicitly rejected.**
The two available resolutions were:

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
| V10 | Is exactly `@`, or contains the sequence `@{`. Only two shapes here are **divergence set D** — the bare `@`, and a resolvable `@{-N}`. Every other `@{...}` form is a **shared rejection**: git rejects it too |
| V11 | Ends with `.` |

**V2 and V3 are a standalone workspace invariant, NOT a git derivation.**
git's CLI cannot unambiguously *receive* a leading-hyphen argument in the first
place — the shell and git's own option parser consume it before any ref-name
check runs — so git's behaviour cannot establish the rule either way. V2/V3 are
therefore asserted on their own terms, as a property this workspace requires of
any value it will place on a command line, and they are **excluded from the
git-driven arm** of the corpus rather than pinned by it. Without them,
`--force`, `-D`, `--all`, and any other option-shaped string would validate as
a branch name and then be emitted as `selected_branch` into gate JSON and
downstream Git invocations — an argument-injection-shaped hazard, not a
cosmetic gap.

**Option-like rejection is stated as its own invariant**, independent of any
`check-ref-format` derivation: no resolved `selected_branch` may begin with
`-`, on any rung, from any source, including a title-derived alias. The
title-alias path is slug-derived and cannot normally produce one, but the
invariant is asserted at the resolver's exit rather than assumed from its
inputs.

**Superset pinning.** A test drives a corpus of accept and reject values
through both the Python validator and `git check-ref-format --branch`, and
asserts the **superset property** rather than identity:

* Any value git rejects, the validator must reject. A disagreement here is a
  failure.
* Any value git accepts, the validator must also accept **unless the value is a
  member of D**, in which case the validator must reject it. A value that
  diverges *outside* D is a failure, in either direction.
* **D is enumerated explicitly in the test as a frozen literal set of exactly
  two shapes** — the bare `@`, and `@{-N}` restricted to the controlled,
  known-resolvable `N` values the fixture repository creates. Silently growing
  the divergence is itself a test failure.
* **The `@{-N}` arm runs only inside a hermetic fixture repository.** The test
  `git init`s a scratch repository, scripts a deterministic checkout history so
  that `@{-1}` and `@{-2}` are known-resolvable, and probes only those values
  there. The ambient repository is never used for an `@{-N}` probe: its reflog
  is arbitrary session state, and an assertion that depends on it is not a
  contract test.
* **Ordinary `@{...}` values are asserted as SHARED REJECTIONS, not as
  divergences.** `foo@{1}`, `main@{0}`, `a@{b}`, `@{u}`, `@{upstream}`,
  `foo@{upstream}` and `@{-0}` must be rejected by **both** git and the
  validator.
* V2/V3 inputs are excluded from the git-driven arm and are asserted against the
  frozen expected-outcome corpus only.

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

### Ship consumption of `selected_branch` — comparison AND creation

Emitting `selected_branch` is necessary but not sufficient. Today the Ship
agent derives the branch name **itself**, from the shipment title, in two
separate places in `templates/agents/_ship.agent.md.tmpl` (and byte-identically
in the installed mirror `.github/agents/_ship.agent.md`):

* the **comparison** site — "already on a branch matching this shipment (e.g.
  `feat/{slug}` or `chore/{slug}`)";
* the **creation** site — `git checkout -b feat/{feature-slug}`, "where
  `{feature-slug}` is derived from the shipment title: lowercase, spaces
  replaced with hyphens".

While those two sites stand, a shipment carrying an explicit
`implementation_branch` that differs from its title alias produces a gate that
expects one branch and a Ship that creates and compares against another — the
gate blocks on a branch Ship will never be on, and the explicit contract is
inert. Retiring the title-alias workarounds on `025-S`/`020-S` before Ship
consumes the emitted value would therefore **strand two live shipments**.

The contract is consequently:

1. Ship runs the pipeline-topology gate **before** branch comparison or
   creation, and reads `selected_branch` from its JSON.
2. On a **successful** gate result, `selected_branch` is the **sole** authority
   for both sites. The comparison site asserts `HEAD` equals
   `selected_branch`; the creation site runs `git checkout -b -- <selected_branch>`
   with the emitted value verbatim.
3. Ship performs **no** slug derivation, no lowercasing, no space substitution,
   no `feat/`/`chore/` prefixing, and no title parsing of any kind. Every
   title-derived branch expression is deleted from both copies, not merely
   supplemented — a surviving derivation is a second authority and is exactly
   the defect.
4. On a **blocked or errored** gate result, Ship halts. It does not fall back
   to a derived name. A gate that could not select a branch has not authorized
   one.
5. **Leading-hyphen safety is preserved end to end.** The validator already
   rejects a standalone option-like short name, and the emitted value is passed
   to `git` after the `--` option terminator with a fixed argv and
   `shell=False`, so a value that is legal as a branch name but option-like as
   an argument cannot be re-interpreted at the Ship boundary either.
6. **The two-rung resolver is unchanged.** Ship consumes whatever
   `selected_branch` the resolver produced, whether its `resolution_source` is
   `explicit_contract` or `title_alias`. Consumption does not add a third rung
   and does not inspect `resolution_source` to decide behaviour.

## Work Breakdown

| # | Task | Scope | Blocked by |
|---|---|---|---|
| T0 | **RED** — author the validator, precedence and gate-JSON contract tests and observe them failing before any implementation exists | `tests/` | — |
| T1 | **IMPLEMENTATION** — branch short-name validator: rules V1–V11, the standalone option-like invariant, and the `git check-ref-format --branch` **superset** corpus with divergence set D enumerated as exactly two shapes (bare `@`, resolvable `@{-N}`) and the `@{-N}` arm confined to a hermetic fixture repository | `src/autoharness/gates/topology.py` | T0 |
| T2 | Parse `custom_fields.implementation_branch` in `list_shipments()`; validate it via T1; add the field to `ShipmentState` | `src/autoharness/gates/topology.py` | T1 |
| T3 | Implement `resolve_expected_branches()` with the **two-rung** precedence and the no-fallback-on-malformed asymmetry | `src/autoharness/gates/topology.py` | T1, T2 |
| T4 | Route all four phases through the single resolver; remove every other branch-derivation path | `src/autoharness/gates/topology.py` | T3 |
| T5 | Emit `resolution_source`, `selected_branch`, ordered `expected_branches` on pass and block paths | `src/autoharness/gates/topology.py` | T4 |
| T6 | **GREEN** — seven-row regression matrix from `14F4D6F3` observed passing | `tests/test_gates_topology.py` | T4 |
| T7 | **GREEN** — field regressions for `018-S`, `020-S`, `025-S`, plus the no-field compatibility invariant | `tests/test_gates_topology.py` | T4 |
| T8 | **GREEN** — CLI-surface tests for the new JSON fields and the malformed-value exit path | `tests/test_gate_pipeline_topology_cli.py` | T5 |
| T8a | **RED** — author the failing end-to-end Ship-consumption fixture: a shipment whose explicit `implementation_branch` differs from **every** title-derived alias; assert Ship compares against and creates **exactly** the emitted `selected_branch`, that no title-derived expression survives in either copy, that a blocked gate produces a halt with no derived fallback, and that a leading-hyphen-adjacent value survives the `--`-terminated fixed-argv boundary. Observe it failing | `tests/` | T5 |
| T8b | **IMPLEMENTATION** — rewrite the Ship **template** comparison and creation sites to consume `selected_branch` verbatim, deleting every title-derived branch expression | `templates/agents/_ship.agent.md.tmpl` | T8a |
| T8c | **IMPLEMENTATION** — apply the byte-identical rewrite to the installed mirror, atomically with T8b | `.github/agents/_ship.agent.md` | T8b |
| T8d | **GREEN** — observe the end-to-end consumption fixture passing against both copies, and add the mirror-divergence and no-surviving-derivation regressions | `tests/` | T8c |
| T9 | Gate documentation: precedence table, validation rule set including divergence set D, token table, compatibility note, and the Ship-consumption contract | `docs/` | T5, T8c |
| T10 | Retire the temporary title-alias workarounds on `025-S`/`020-S`, under the approval/snapshot/rollback procedure below | backlog data + docs | T6, T7, T8, T8d |

### Dependency rationale

Every edge below is a machine-encoded `blocks` edge in the backlog, not a table
position:

0. **Red precedes implementation.** T0 authors the validator, precedence and
   gate-JSON contract tests and observes them **failing** against a missing
   entry point. T1 blocks on T0. **T0 does not depend on T1** — that asymmetry
   is what makes it a genuine red phase rather than a test-after task with a
   suggestive title. The same asymmetry holds for the consumption spine:
   **T8a does not depend on T8b/T8c.**
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
3. **Ship consumption precedes workaround retirement.** T8a/T8b/T8c/T8d exist
   because emitting `selected_branch` changes nothing on its own: the Ship
   template and its installed mirror still derive the branch from the shipment
   title at two separate sites. T8b and T8c are one atomic change set (T8c
   blocks on T8b) for the same template/mirror drift reason as elsewhere in
   this portfolio, and T8a blocks on T5 because the fixture asserts against the
   emitted field.
4. **Workaround removal is genuinely last, and gated on ALL proving families.**
   T10 retires the title-alias workarounds that currently keep `025-S` and
   `020-S` unblocked. It is blocked by T6, T7, T8, **and T8d** — every test
   family that proves the explicit-contract path actually works, including the
   CLI surface **and the end-to-end Ship consumption**. Without the T8d edge,
   a mid-execution reordering could remove the alias while Ship is still
   deriving its branch from the title, blocking two live shipments with no
   route back except a prohibited `--force`.

T9 is documentation and blocks on T5 and T8c so the emitted-field table and the
consumption contract it documents are the ones that shipped.

### Retirement of the live alias workaround (P2 hardening, directly touched by T10)

T10 mutates **live** backlog records for two shipments that are currently
unblocked only because of the alias. That is a risky action on live data, so
the retirement carries its own procedure:

* **Approval** — a fresh in-session operator approval naming `025-S` and
  `020-S` explicitly, the exact fields being removed, and the effect
  (title-alias resolution ceases for those shipments). A prior or portfolio-wide
  approval does not cover it.
* **Snapshot** — byte snapshot of both records plus their manifest and
  relationship hashes, captured immediately before mutation and recorded in the
  task's evidence.
* **Postcondition** — after mutation, the topology gate is re-run for both
  shipments and must return a successful result whose `resolution_source` is
  `explicit_contract` and whose `selected_branch` equals the value Ship would
  create.
* **Rollback** — on any failed postcondition, the snapshot is restored
  automatically and the task halts and reports; the shipments are never left in
  a state where neither authority resolves.

## Verification

### Ship consumption (T8a/T8d)

* An end-to-end fixture shipment declares `implementation_branch:
  `spike/explicit-authoritative-name`` while its title would derive
  `feat/some-other-title` and `chore/some-other-title`. The emitted
  `selected_branch` is the explicit value, and Ship **compares against** and
  **creates** exactly that branch — asserted against both the template and the
  installed mirror.
* A grep-equivalent structural assertion proves **no** title-derived branch
  expression survives in either copy: no `feat/{`, no `chore/{`, no
  lowercase/space-substitution instruction at either the comparison or the
  creation site.
* A blocked gate result produces a Ship halt with no branch creation and no
  derived fallback.
* A `selected_branch` whose first character is a hyphen is rejected by the
  validator upstream; a value that is legal but option-adjacent is passed after
  `--` with a fixed argv and `shell=False`, asserted at the Ship boundary.
* The two-rung resolver is unchanged: a shipment with no explicit field still
  resolves via `title_alias`, and Ship consumes that `selected_branch`
  identically, without inspecting `resolution_source`.
* `T10` is unreachable in the machine DAG until `T8d` is complete.


* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* All seven matrix rows pass, including both malformed-value rows.
* The **superset property** holds on every corpus value: every value git rejects
  is rejected by the validator; every value git accepts is accepted by the
  validator **unless** it is a member of divergence set D — the bare `@`, and a
  **resolvable** `@{-N}` — which the validator rejects under V10. No divergence
  exists outside D, in either direction.
* Divergence set D is pinned as a frozen literal of exactly those two shapes, so
  growing it silently is a test failure.
* The `@{-N}` divergence assertions run **only** inside a hermetic fixture
  repository with a scripted checkout history; no `@{-N}` probe touches the
  ambient repository's reflog.
* Ordinary `@{...}` values — `foo@{1}`, `main@{0}`, `a@{b}`, `@{u}`,
  `@{upstream}`, `foo@{upstream}`, `@{-0}` — are asserted as **shared
  rejections** by both git and the validator, never as divergences.
* V2/V3 (leading-hyphen / option-shaped) inputs are asserted against the frozen
  expected-outcome corpus only and are **excluded** from the git-driven arm,
  because git's CLI cannot unambiguously receive such an argument to judge.
* Every option-shaped value in the corpus — `-`, `--`, `-D`, `--force`,
  `--all`, `-x`, `--` — is rejected with `IMPLEMENTATION_BRANCH_MALFORMED`,
  and no such value ever appears as `selected_branch` in gate JSON.
* The resolver-exit invariant holds: no returned `selected_branch` begins with
  `-` on any rung.
* Exactly two `resolution_source` values are reachable. The absence of the
  third rung is asserted by a **scoped, executable criterion**, not by a
  repository-wide string ban — a ban on the literal token is unsatisfiable by
  construction, because this plan, this release unit's own backlog records, and
  the review history all have to name the rung in order to state that it does
  not exist. The criterion is:
  1. **No resolver, config, or runtime source declares it.** The literal
     `workspace_convention` appears in no file under `src/autoharness/`, in no
     `schemas/*.json`, and in no `.autoharness/config.yaml` key path.
  2. **No fallback path can reach it.** `resolve_expected_branches()` returns a
     `resolution_source` drawn from a frozen two-member enum
     `{explicit_contract, title_alias}`; any other value is unconstructible, and
     the enum's membership is asserted directly rather than inferred from a
     text scan.
  3. **Any remaining textual occurrence is confined to an explicitly identified
     historical set** — this plan, the `170-*` backlog records, `docs/reviews/`,
     `docs/decisions/`, and `docs/memory/` — where every occurrence is a
     statement that the rung was removed and stays removed. The scan asserts
     that occurrences outside that identified set are zero, which is decidable,
     auditable, and does not require the token to be unmentionable.
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
| R4 | Merge contention with `165-F`'s `_shipment_readiness_check` work | `165-F`/`173-S` is **archived**; the recorded contention window is closed |
| R5 | Retiring the title-alias workarounds breaks a shipment mid-flight | T10 is blocked by T6, T7, and T8 — a machine-encoded edge, not a table position — and touches only backlog data for shipments whose explicit contract the resolver now honors |
| R6 | An option-shaped branch value reaches a Git command line | V2/V3 reject it at validation as a **standalone workspace invariant** (not a git derivation — git cannot judge such input), and the resolver-exit invariant re-asserts it independently of which rung produced the value |
| R7 | Carrying no reserved rung for the deferred declarative tier makes that tier harder to add later | The ladder is a single ordered structure in one function; inserting a rung is local. Carrying an unauthorized config surface with no schema behind it is the larger cost |
| R8 | Divergence set D grows silently, turning a deliberate exception into an unnoticed drift | D is pinned as a frozen literal of exactly two shapes (bare `@`, resolvable `@{-N}`) in the superset test; any value diverging outside D fails in either direction |
| R9 | The `@{-N}` divergence assertion depends on ambient reflog state and passes or fails by accident | The `@{-N}` arm runs only in a hermetic fixture repository with a scripted checkout history; unresolvable `@{-N}` is asserted as a shared rejection in the same fixture |

## Out of scope

* Declarative workspace-level branch templates in `.autoharness/config.yaml`
  (deferred per decision **D1**). No reserved rung, no placeholder, no
  `resolution_source` value, and no config key is carried for the deferred
  tier.
* Any vendor identifier (ADO, Jira) in the engine.
* Repository-supplied executable branch rules — workspace policy stays
  declarative data only.
* Sequencing authority (`_shipment_readiness_check`, `dag-root`,
  `UNSEQUENCED_SHIPMENT`), which is a different contract surface.
* Any `--force` path.

## Plan Hardening Record (P-006)

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

| # | Hazard | Resolution in this contract |
|---|---|---|
| H1 | A validation rule set that omits leading-hyphen and option-shaped values lets `--force` or `-D` validate as a branch name and be emitted as `selected_branch` into gate JSON and downstream Git invocations | V2/V3 enumerated as a standalone workspace invariant; a resolver-exit invariant re-asserts it independently of rung; the corpus pins every option-shaped form |
| H2 | "Valid Git branch short name" stated as an informal list, or pinned as an *equivalence* with `git check-ref-format --branch`, makes validator/git divergence either undetectable or falsely asserted — git accepts the bare `@` and a resolvable `@{-N}`, and rejects the wider `@{...}` family exactly as V10 does | Rule set V1–V11 stated explicitly and pinned by a corpus driven through `git check-ref-format --branch` as a **strict superset of rejections**, with divergence set D frozen at exactly two shapes and the reflog-dependent `@{-N}` arm confined to a hermetic fixture repository |
| H3 | The git-driven arm passes vacuously on a machine without `git` | The test skips loudly and still asserts the frozen expected-outcome corpus |
| H4 | Task ordering carried only by table position lets the integration task execute before the resolver and reader it integrates | `blocks` edges encoded: T0 → T1 → T2 → T3 → T4 → T5; rationale recorded in the plan body |
| H5 | Workaround retirement "sequenced last" in prose only lets a reordering strand `025-S`/`020-S` with no non-`--force` route back | T10 blocked by T6, T7, **and** T8 — every proving test family including the CLI surface |
| H6 | A reserved-but-unreachable precedence rung for the deferred declarative tier is an unauthorized contract surface: no config key, no schema, no decision authorizing it, and only a tautological test | No such rung exists; the ladder is exactly two rungs. Absence is asserted by a scoped executable criterion — no `workspace_convention` occurrence under `src/autoharness/`, `schemas/`, or `.autoharness/config.yaml`; a frozen two-member `resolution_source` enum making a third value unconstructible; and zero occurrences outside an explicitly identified historical documentation set. A repository-wide ban on the literal token would be unsatisfiable, since the contract has to name the rung to state that it is gone |
| H7 | A cited design document that has never existed at any ref leaves a reader unable to verify any requirement traced to it | Recorded as `unavailable-external` provenance with the verification method stated; durable source redirected to the archived stash entry |
| H8 | T10 mutates live backlog records for two shipments — the only non-additive action in the unit | Classified below as a Medium-risk `ProposedAction` with an explicit rollback and an operator checkpoint |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Rewrite branch derivation for all four gate phases (T4) | Medium — a regression false-blocks every shipment | Standard PR review; gated by T1–T3 landing first | Revert `topology.py`; no persisted state changes |
| Add three fields to gate JSON on both paths (T5) | Low — additive only | Standard PR review | Revert; compatibility invariant test proves the non-additive surface is untouched |
| Retire live title-alias workarounds on `025-S`/`020-S` (T10) | **Medium** — mutates live backlog records for two unblocked shipments | Blocked by T6/T7/T8; operator confirmation before mutating either record | Re-add the title alias to the shipment record; the workaround is a backlog-data change, fully reversible |

**Rollback coupling.** T1–T5 are source-only and revert as one `topology.py`
change set. T0, T6, T7, T8 and T9 are test/doc-only. T10 is the only task
touching persisted state and is independently reversible.

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
declarative-template tier remains deferred and has no placeholder in this
release unit.
