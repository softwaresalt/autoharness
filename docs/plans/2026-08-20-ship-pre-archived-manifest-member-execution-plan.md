---
title: "Ship execution contract - exclude pre-archived manifest members from the executable task set"
date: 2026-08-20
stash_id: B19E9662
deliberation: "022-DL (archived 2026-08-20 to .backlogit/archive/022-DL.md)"
requires_plan_hardening: yes
blast_radius: "elevated (the authoritative installed Ship execution contract governing every future shipment, its template counterpart, one new regression-test module, and the harness-manifest checksum for the installed agent artifact; no src/, no schema, no CLI change)"
---

# Implementation Plan - Ship pre-archived manifest-member execution exclusion

Date: 2026-08-20
Agent: Stage (planning only - Ship executes)
Stash source: `B19E9662`
Deliberation: `022-DL` (archived 2026-08-20 to `.backlogit/archive/022-DL.md`)
Classification: **bug / execution-contract defect**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)
Source refs: PR #375; local review at HEAD `e88a8d62` on branch `chore/stage-144-s`;
review-thread ID `N/A`; affected shipments 144-S, 145-S; affected tasks 136.001-T,
137.005-T, 137.006-T.

## Goal

Make Ship derive its executable task set from live task records instead of
treating the shipment manifest as that set, and have it explicitly exclude
`pre-archived` manifest members, so that a closure-valid manifest containing
superseded archived children can be executed without attempting to reactivate
them - while the manifest itself stays byte-for-byte unchanged for P-015
cascade classification.

## Why this is a separate shipment

The manifest membership correction at `e88a8d62` (144-S and 145-S) is a
shipment-membership / closure-classifier surface. This defect lives on the
agent-instruction execution contract and its regression-test surface. Under
P-021 C1 those are different contract surfaces with different test surfaces,
so the fix is not absorbed into 144-S, 145-S, or 146-S. It is captured
(`B19E9662`), deliberated (`022-DL`), and shipped in its own shipment, wired
as an execution-blocking prerequisite ahead of 144-S.

This shipment contains only newly created queued items and therefore has **no
pre-archived manifest members of its own**, so it is safely executable under
the current, still-unfixed contract.

## Non-goals

* No change to any shipment manifest. 144-S and 145-S keep their pre-archived
  members exactly as restored at `e88a8d62`. Closure membership is not weakened.
* No unarchiving, requeueing, or reactivation of 136.001-T, 137.005-T, or
  137.006-T. They remain archived and superseded.
* No change to `src/autoharness/gates/shipment_closure.py` or any other source
  module, schema, or CLI surface.
* No change to the Step 0.5 item 1a queued-with-active-work early-warning.
  It fires on `active`/`done` by design; teaching it about `archived` would
  risk a false fail-closed halt on every closure-valid manifest. The task-loop
  derivation step is the correct seam.
* No new `autoharness gate` subcommand. Executable enforcement is recorded in
  `022-DL` open question 1 as a deferred follow-up, not part of this fix.
* No full re-render of either agent file. The installed mirror carries
  pre-existing, unrelated drift (798 lines vs. the template's 1073); the new
  contract text is mirrored into each file's own structure per the
  width-isolation precedent recorded throughout `.autoharness/harness-manifest.yaml`.

## Contract to be written (identical semantics in both files)

1. The shipment manifest (`custom_fields.items`) is the **closure membership
   record**. It is never the executable task set and is never mutated to make
   execution proceed.
2. Before the task loop, derive the **executable task set**: filter the
   manifest to task artifacts (IDs ending `-T`; the covering feature is
   resolved through `parent_id` and is never executed), read each task record,
   and keep only records whose status is `queued` or `active`.
3. Explicitly **exclude** members whose record is archived - the `pre-archived`
   classification already defined by `shipment-reconcile`. Record them in a
   reported `pre_archived_skipped` set. Never claim them, never move them to
   `active`, never unarchive them, never remove them from the manifest.
4. A `pre-archived` member is **expected and tolerated**, not an error. It must
   not halt the run and must not be conflated with the Step 0.5 item 1a
   `SHIPMENT_STATE_INCONSISTENT` early-warning.
5. If the derived executable set is **empty while the manifest is non-empty**,
   halt and report rather than proceeding to build or PR. A fully pre-archived
   manifest is a closure case, not an execution case.
6. Installed copy only: add the `shipment-reconcile` `mode: pre` intake
   reconciliation reference that the template already carries at Step 0.5
   item 6, adapted to this repository's self-hosting note (the skill is read
   from `templates/skills/shipment-reconcile/SKILL.md.tmpl`, because
   `.github/skills/shipment-reconcile/SKILL.md` is not installed here).

## Task decomposition

### Task 1 - Contract text in both Ship agent files + atomic checksum refresh

Files:

* `.github/agents/_ship.agent.md` - Step 2 "Task Execution Loop": insert the
  executable-set derivation (contract items 1-5) as a preamble before the
  existing `For each task ...` loop, and reword the loop header to iterate the
  **derived executable task set** rather than "each task in the
  shipment/feature". Add contract item 6 (the `mode: pre` intake reference) to
  Step 0.5.
* `templates/agents/_ship.agent.md.tmpl` - Step 3 "ready queue" construction:
  state the manifest-derived executable set and the explicit `pre-archived`
  exclusion alongside the existing label+`{{STATUS_QUEUED}}` derivation, and
  carry contract items 1-5. Use the template's own `{{STATUS_*}}` and
  `{{BACKLOG_DIRECTORY}}` variables; introduce no new unresolved placeholder.
* `.autoharness/harness-manifest.yaml` - refresh the `checksum` for
  `.github/agents/_ship.agent.md` **in the same change**, computed from the
  LF-normalized committed git blob via `git cat-file -p :<path>` (staged) or
  `HEAD:<path>` (post-commit), never a raw Windows working-tree read; append a
  provenance sentence to that artifact's `note` naming this shipment and task.

Atomicity: the two agent files and the checksum move together in one task, so
the workspace is never in a state where the mirror is edited but its checksum
is stale, or where one file declares the contract and the other does not.

Acceptance criteria:

* Both files state contract items 1-5 in their own structure and vocabulary.
* Neither file retains an unconditional "iterate every manifest entry and move
  it to active" formulation.
* The installed file's Step 0.5 gains the `mode: pre` intake reference with the
  self-hosting note; the template's existing item 6 is left as-is.
* `.autoharness/harness-manifest.yaml` checksum for the installed agent matches
  the LF-normalized committed blob; note updated.
* No manifest record, backlog item, or archived task is touched.
* Configured suite green at task completion.

Size: S. Complexity: medium.

### Task 2 - Regression coverage for the pre-archived execution exclusion

File: new `tests/test_ship_pre_archived_manifest_members.py`, following the
established `tests/test_ship_safe_close_pointer.py` template+mirror contract-test
pattern.

Assertions:

* **A1 (contract present, both files)**: for each of the template and the
  installed mirror, the text declares the executable-set derivation and the
  explicit `pre-archived` exclusion, and states that the manifest is the
  closure membership record rather than the executable set.
* **A2 (negative control)**: the pre-fix unconditional formulation - a loop
  header iterating "each task in the shipment/feature" with no derivation
  preamble - is no longer present in the installed mirror. This is what makes
  the guard discriminating rather than vacuous: it is written to fail against
  the `e88a8d62` text.
* **A3 (tolerated, not fatal)**: both files state that a `pre-archived` member
  is expected and tolerated and does not halt the run.
* **A4 (empty-set halt)**: both files state the halt-and-report rule for an
  empty executable set over a non-empty manifest.
* **A5 (closure invariant pinned)**: a data-level regression over a synthetic
  closure-valid manifest whose covering feature has a superseded archived
  child - built with the existing fixtures of
  `tests/test_shipment_closure_classification.py` - asserting
  `classify_shipment_close_path` still returns the cascade verdict **with the
  archived member present in the manifest**. This pins the invariant that the
  execution fix must never be "fixed" later by stripping pre-archived members
  back out of manifests.

Acceptance criteria:

* Module imports and runs under the configured suite with no new dependency.
* A2 is demonstrably discriminating (documented in the module docstring:
  it fails against the pre-Task-1 text).
* No existing test is weakened, deleted, or re-scoped.
* Configured suite green at task completion.

Size: S. Complexity: low.

## Ordering and gate atomicity

Task 1 precedes Task 2. Ship evaluates the configured suite at every task
boundary, so a test-first ordering would land a red gate on Task 1. Writing the
contract first and the discriminating guard second keeps both boundaries green
while still proving the guard discriminates (assertion A2 plus the docstring
note).

Each task is independently gate-atomic: after Task 1 the suite is green with
the contract in place and the checksum current; after Task 2 the suite is green
with the contract pinned.

## Sequencing and the mandatory instruction reload

Chain: `146-S -> <this shipment> -> 144-S -> 145-S`.

* 146-S first: it repairs the red baseline (malformed plan frontmatter + the
  archived 019-DL contract-test load) and has no pre-archived manifest members.
* This shipment second: it has no pre-archived manifest members either, so it
  is executable under the current unfixed contract, and it is the thing that
  makes 144-S executable.
* **MANDATORY post-merge instruction reload before 144-S begins.** The fix only
  takes effect for a Ship session that reloads `.github/agents/_ship.agent.md`
  after this shipment merges. A session still holding the pre-merge contract in
  context would re-expose the original failure. This is an Orchestrator
  sequencing obligation recorded in the shipment-order record and the staging
  handoff memory; there is no backlog-record mechanism that enforces it.
* The direct `144-S -> 146-S` edge is replaced by the two-hop path so the chain
  is a simple, self-enforcing line rather than a diamond.

## Risks

* **R1 - reload skipped.** Mitigated by the explicit reload obligation above and
  by the shipment title naming it.
* **R2 - checksum drift.** Mitigated by folding the checksum refresh into the
  same task as the instruction edit and by pinning the LF-normalized
  committed-blob procedure in the acceptance criteria.
* **R3 - contract stated in only one file.** Mitigated by A1 asserting over both
  files and by keeping both edits in Task 1.
* **R4 - a later change "simplifies" manifests by dropping pre-archived
  members.** Mitigated by A5.
* **R5 - prose contract, not executable enforcement.** Accepted for this fix;
  the executable-gate alternative is deferred in `022-DL` open question 1.

## Verification (Ship, at execution time)

* Configured suite green after each task.
* `.autoharness/harness-manifest.yaml` checksum matches the committed blob.
* No diff to `.backlogit/queue/`, `.backlogit/archive/`, or any shipment record.
* Both agent files parse as valid Markdown with intact frontmatter, LF endings
  preserved.
* No unresolved `{{VARIABLE}}` introduced in the template.

## Amendments A1 and A2 (plan-harden, 2026-08-20)

Applied from `docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-hardening.md`.

### A1 (from H1) - the derivation is work-selection, never an integrity guard

Contract items 2-4 are refined as follows, and both agent files must say so:

* The Step 0.5 item 1a queued-with-active-work early-warning is **unchanged** and
  runs strictly **before** the new derivation, exactly where it runs today. The
  derivation never suppresses, replaces, softens, or pre-empts its
  `SHIPMENT_STATE_INCONSISTENT` halt.
* Status handling is **positive and exhaustive** (from H5): keep `queued` and
  `active`; skip-and-report `archived` as `pre_archived_skipped`; report an
  already-`done` member separately as `already_done`; **any other, missing, or
  unreadable status is a fail-closed halt, never a skip**.
* `already_done` and `pre_archived_skipped` are **distinct reported outcomes**.
  A `done` member must never be laundered as a tolerated pre-archived skip.
* Artifact-type filtering (`-T` only, feature resolved via `parent_id`) happens
  **before** any status read (H3).
* The empty-executable-set halt (item 5) must **not** advance to build or PR and
  must **not** trigger any closure path (H4).

Task 1 acceptance criteria gain: the unchanged-item-1a ordering is stated; the
exhaustive status table is stated; `-T` filtering precedes status reads; the
checksum is computed from the LF-normalized committed blob and never from a
working-tree hash (H2).

Task 2 gains assertion **A6**: both files state the unchanged-item-1a ordering
and the distinct `already_done` / `pre_archived_skipped` reporting.

### A2 (from H6) - no new template status variable

The template defines exactly `{{STATUS_QUEUED}}`, `{{STATUS_ACTIVE}}`,
`{{STATUS_DONE}}`. The archived state is expressed through the `pre-archived`
classification vocabulary already defined by `shipment-reconcile` (record
archived / archive file present), **never** through a new `{{STATUS_ARCHIVED}}`
or any other new variable.

Task 1 acceptance criteria gain: no new `{{VARIABLE}}` is introduced and the
template contains zero unresolved placeholders.

Task 2 gains assertion **A7**: the template contains no `{{STATUS_ARCHIVED}}`
token.

Neither amendment adds a work surface; both tasks remain within the 2-hour rule
and no task split is required.

## Amendment A3 (plan-review, 2026-08-20)

Applied from `docs/reviews/2026-08-20-ship-pre-archived-manifest-member-execution-review.md`
(P1-1, P2-1, P2-2).

### A3.1 - Task 2 assertion A5 is REMOVED (duplicate of shipped coverage)

The closure-side invariant is already pinned and green in
`tests/test_shipment_closure_classification.py`:

* `test_mixed_pre_archived_and_queued_manifest_members_still_selects_cascade`
  (queued feature + mixed queued/pre-archived children -> CASCADE; the 144-S shape)
* `test_feature_queued_children_pre_archived_still_selects_cascade`
* `test_feature_pre_archived_children_queued_still_selects_cascade`
* `test_all_manifest_members_pre_archived_still_selects_cascade`
* `test_pre_archived_out_of_manifest_child_falls_back_to_safe_close`

That suite shipped with feature 132-F / shipment 141-S from archived stash
`EDE3CC2D`. Task 2 therefore adds **no new `classify_shipment_close_path`
test**. Instead its module docstring cites those tests by name as the
authoritative closure-side invariant and states that the execution-side
exclusion must never be "fixed" by stripping pre-archived members out of a
manifest.

Task 2's new assertions are exactly **A1, A2, A3, A4, A6, A7** - all confined
to the execution-contract text, which is genuinely uncovered today.

### A3.2 - Restated goal boundary

The closure path is already covered; the **execution** path is not. This fix
adds execution-contract coverage only. Do not re-add a closure-classifier test.

### A3.3 - Existing agent-contract tests must stay green

Task 1 inserts text near anchors asserted by existing modules. Acceptance
criteria gain: the insertion must not relocate, reword, or break any asserted
anchor phrase, and these modules are named must-stay-green:

* `tests/test_ship_safe_close_pointer.py`
* `tests/test_ship_claim_integrity_guards.py`
* `tests/test_pipeline_topology_gate_agent_wiring.py`

### A3.4 - Place text by semantic anchor, not line number

The installed mirror and the template diverge structurally (installed Step 2 is
the task loop; the template's loop is Step 4 after a Step 3 ready-queue
construction). Locate the insertion points by semantic anchor. Do not
re-render either file.