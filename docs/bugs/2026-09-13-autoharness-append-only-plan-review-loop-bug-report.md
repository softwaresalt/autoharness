---
title: "Bug report — Append-only plan review loops keep historical prose operative"
description: "Autoharness reuses a single live plan file for review history and remediation narrative, causing later reviewers to treat superseded text as current contract and trapping stable designs in non-convergent review loops"
status: proposed
date: 2026-09-13
severity: high
component: "autoharness / plan-review / remediation loop"
owner_repo: "softwaresalt/autoharness"
source_workspace: "softwaresalt/intercom"
tags:
  - autoharness
  - bug
  - plan-review
  - remediation
  - compact-context
  - backlog
  - contracts
---

# Bug report — Append-only plan review loops keep historical prose operative

## Executive summary

Autoharness currently allows the operative plan-remediation loop to append every
review attempt, withdrawal note, and remediation narrative into the same live
plan file. Later review attempts then consume the entire file as if it were one
authoritative contract. Superseded findings, withdrawn wording, and current
instructions are therefore reviewed together, which turns historical prose into
fresh defects and traps otherwise stable designs in a non-convergent loop.

Plain-language impact: the harness keeps rereading its own stale review history
and mistaking it for the current plan. Teams pay for larger prompts, spend
cycles repairing contradictions that should already be retired, and can exhaust
circuit breakers even after the architecture itself is settled.

> [!IMPORTANT]
> This is a harness-level operational bug, not user error and not evidence that
> one specific plan was architecturally unsound. The failure is the lack of a
> machine-enforced separation between authoritative contract text and archived
> review history.

## Symptoms and minimal deterministic reproduction

### Symptoms

* Review findings repeat after they were already fixed because old review text
  still sits inline beside current operative sections.
* Withdrawn or superseded contract wording continues to be flagged as if it
  were current requirements.
* Each remediation makes the live plan longer, more contradictory, and more
  expensive to review.
* Reviewers spend effort patching semantic mismatches between old and new prose
  instead of judging the current design.
* Later attempts increasingly fail for mechanical text contradictions rather
  than design defects.

### Minimal deterministic reproduction

1. Start with a live plan file that is both the governing contract and the
   destination for review history.
2. Run plan review and append the findings, rebuttals, withdrawals, and
   remediation notes into that same file.
3. Remediate by editing selected paragraphs in place while leaving the old
   review text inline.
4. Re-run review over the entire live plan file without a separate
   authoritative-section boundary or an input manifest that excludes historical
   review prose.
5. Observe that the reviewer flags contradictions between historical and current
   prose, including issues already closed in the prior cycle.
6. Repeat steps 2 through 5 and observe monotonically increasing file size,
   review surface, and duplicate or stale findings.

### Workspace reproduction evidence

This workspace produced the defect in a concrete, repeatable way:

* Plan A evolved through multiple revisions and review attempts while prior
  review sections remained inline.
* By attempt 3, the plan exceeded roughly 3,000 lines, and reviewers continued
  finding contradictions between historical inventory or withdrawal prose and
  the current operative sections.
* Three remediation and re-review cycles closed earlier defects but then
  introduced or rediscovered stale semantic contradictions.
* A five-model escalation concluded that the feature was sufficiently
  decomposed and that the remaining blockers were mechanical plan-text
  contradictions, not architecture defects.
* The efficient recovery was to stop patching append-only prose, materialize
  one concise decided plan, archive verbose history, update references, and
  review only the final contract.

## Actual versus expected behavior

| Surface | Actual behavior | Expected behavior |
|---|---|---|
| Governing plan | One live file accumulates current contract text and historical review prose | One concise active governing plan contains only current requirements |
| Review input | Later reviewers read historical and operative prose together | Reviewers receive only the active plan plus explicitly declared context |
| State discovery | Latest attempt is inferred by scanning inline markers and narrative text | Latest review state is stored structurally and read deterministically |
| Remediation | Agents patch local discrepancies inside append-only prose | Agents regenerate a normalized authoritative contract after remediation |
| Backlog references | Backlog records may copy plan excerpts that drift from the active plan | Backlog references point atomically to one governing plan path |
| Retry control | Repeated failed cycles can continue without automatic consolidation | The harness consolidates context before later review attempts |

## Root-cause analysis

### 1. `plan-review` appends findings into its input artifact

The current loop uses the plan itself as both review subject and review log.
That merges two lifecycles that should stay separate: a contract needs stable,
low-entropy authoritative text, while review history is necessarily verbose,
adversarial, and supersedable.

### 2. No machine-enforced authoritative-section boundary exists

The harness relies on prose conventions and inline markers to imply which
sections are current. That works only while files are short and readers are
careful. It fails once the file contains multiple withdrawals, amendments, and
review attempts, because nothing mechanically prevents older text from being
treated as still operative.

### 3. Reviewer prompts receive historical and operative prose together

Later review attempts are assembled from the same large file that contains both
current sections and their superseded predecessors. The prompt therefore asks
the reviewer to infer temporal validity from natural language rather than from
structure. Models are good at finding contradictions; they are not reliable at
ignoring stale text unless the harness excludes it explicitly.

### 4. Latest-attempt parsing depends on inline markers instead of a separate registry or artifact

The harness currently infers "what happened last" by scanning appended
narrative sections, revision markers, and attempt prose. That state-discovery
strategy is brittle, expensive, and ambiguous once multiple attempts exist. A
review system should not need to parse an execution log to discover the current
verdict.

### 5. Backlog records duplicate plan excerpts and drift

When backlog items or review records copy large plan excerpts instead of
referencing one active plan, the same contract text begins to exist in multiple
places. After remediation, one copy changes and another does not. That creates
another stale-text channel that can feed contradictory requirements back into
later review rounds.

### 6. `compact-context` is not triggered automatically before repeated review cycles

The harness already has primitives for consolidation, but repeated review
failures can continue without forcing a context-compaction or decided-plan
regeneration step. That allows the prompt size, token cost, and contradiction
surface to grow across attempts instead of being reset after the first sign of
non-convergence.

### 7. Remediation patches prose instead of regenerating a normalized contract

The loop optimizes for local diffs inside the existing file rather than for
re-emitting a clean authoritative artifact. That patch-in-place strategy
preserves every superseded paragraph and makes future reviewers compare old
semantics to new semantics sentence by sentence. The result is an append-only
contradiction engine, not a convergent review loop.

## Harness-level resolution

The simplest composable fix is structural separation: keep immutable history,
but make exactly one concise artifact authoritative at any time.

1. Store each review attempt as an immutable artifact under a `review-history/`
   path rather than appending it into the live plan.
2. Maintain one concise active `*-decided-plan.md` file as the only governing
   plan for review and downstream references.
3. Add stable plan identity metadata such as `plan_id`, `revision`,
   `supersedes`, and `source_history` so the active plan and its archived
   lineage remain linked.
4. Assemble review inputs from an explicit manifest that names the active plan
   and any allowed supporting context, and excludes archived history files by
   default.
5. After remediation, materialize or regenerate the active plan from the latest
   resolved contract instead of patching inline historical prose.
6. Automatically invoke `compact-context` or decided-plan consolidation after
   the first failed remediation cycle, or before any later review attempt.
7. Update backlog references atomically to the active plan path instead of
   copying large operative sections into backlog artifacts.
8. Store latest review state structurally in metadata or a small review record,
   not by scanning appended narrative history.
9. Enforce bounded line, section, and token budgets plus contradiction
   detection before dispatching a new review attempt.
10. Preserve archived traceability and never delete historical review artifacts.

## Proposed changes by harness surface

| Harness surface | Proposed change |
|---|---|
| `plan-review` skill | Emit a new immutable review artifact per attempt, consume the active decided plan through an explicit manifest, and fail closed if archived review history is present in the operative input set |
| Stage agent | After a failed remediation cycle, regenerate the active decided plan from resolved requirements, update references, and route future review attempts to that regenerated artifact rather than to append-only prose |
| `compact-context` skill | Add a first-class consolidation mode for plan remediation loops that extracts the current contract into a concise decided plan and moves prior attempts into traceable history artifacts |
| Plan schema and metadata | Introduce durable fields for `plan_id`, `plan_role`, `revision`, `supersedes`, `source_history`, `review_manifest`, and an unambiguous single-active marker |
| Backlog harvest and references | Replace copied operative excerpts with atomic path references to the active decided plan; when the path changes, update all related references in the same operation |
| Reviewer prompt assembly | Build prompts from the active decided plan plus explicitly declared contextual files only; exclude `review-history`, archived plans, superseded decisions, and backlog narrative copies unless a manifest opts them in |
| Verification commands | Add a pre-dispatch verifier that checks single-governing-plan invariants, active-input manifests, budget thresholds, stale-inline-review markers, and contradiction signals before another review is launched |

## Governing flow

```text
Draft Plan
  -> Review Artifact (attempt N, immutable)
  -> Remediate / Regenerate
  -> Active Decided Plan (single governing artifact)
  -> Review Artifact (attempt N+1, immutable)
  -> Remediate / Regenerate
  -> Active Decided Plan

Rules:
- At most one active governing plan exists for a plan_id
- Review artifacts are traceable history, never operative by default
- Backlog and downstream consumers resolve the active decided plan, not
  appended narrative history
```

## Backward-compatible migration for existing append-only plans

1. Detect plans whose live file contains appended review history, repeated
   attempt markers, or budget breaches.
2. Extract the latest resolved operative contract into a new
   `*-decided-plan.md` artifact with stable identity metadata and links back to
   its source history.
3. Preserve the existing append-only file as archived traceability input, or
   split its review attempts into dedicated history artifacts without deleting
   the original evidence.
4. Emit a structural latest-review record so the harness no longer infers the
   current verdict by scanning narrative prose.
5. Rewrite backlog, review, and decision references atomically to the new
   active decided plan.
6. Fail closed if the migration cannot prove which content is currently
   operative, and require human resolution rather than silently dropping current
   findings.

## Acceptance criteria

1. A fixed historical finding does not reappear solely because old review text
   remains archived.
2. Reviewers receive only the active decided plan plus explicitly declared
   context.
3. The latest verdict is deterministic without scanning appended narrative
   history.
4. All backlog references resolve to one active governing plan.
5. After repeated failure, consolidation occurs before another later review
   attempt is dispatched.
6. Archived reviews remain traceable but non-operative by default.
7. Breaching the configured line or token budget fails closed with
   consolidation guidance.
8. Migration never silently drops a still-current finding.
9. Regenerated active plans carry stable identity and source-history metadata.
10. Contradiction checks run on the operative input set before review dispatch.

## Regression test matrix

| Class | Scenario | Expected result |
|---|---|---|
| Unit | Review-input assembler receives one active decided plan and two archived review artifacts | Only the active decided plan enters the reviewer prompt |
| Unit | Latest-verdict resolver reads metadata for a plan with multiple prior attempts | It returns the current verdict without scanning narrative sections |
| Unit | Budget checker sees an operative plan above the configured line or token threshold | Review dispatch fails closed and recommends consolidation |
| Integration | First review fails, remediation regenerates a decided plan, and second review runs | Second review consumes the regenerated active plan and not the first review artifact |
| Integration | Archived review contains a fixed P0 finding that conflicts with current text | The finding does not reappear unless the active plan still carries the defect |
| Integration | Backlog record points to an active plan that is superseded by a new decided plan | References update atomically to the new governing path |
| Migration | Existing append-only plan contains historical withdrawals and current contract text | Migration preserves traceability, emits one active decided plan, and retains all current findings |
| Migration | Existing append-only plan contains ambiguous current-state markers | Migration fails closed and requests operator resolution |
| Failure | Review manifest accidentally includes a `review-history` path | Verification rejects dispatch and names the excluded input |
| Failure | No single governing artifact exists for a `plan_id` | Verification rejects dispatch until one authoritative plan is selected |
| Concurrency | One agent regenerates a decided plan while another tries to update backlog references | Atomic reference update preserves one active governing path and avoids split-brain state |
| Concurrency | Archived history files appear during a later review cycle | They remain non-operative unless explicitly added to the manifest |

## Risks and tradeoffs

* More artifacts will exist per plan, which slightly increases repository
  object count.
* Migration tooling must preserve lineage carefully to avoid losing
  traceability.
* Agents will need a small amount of metadata discipline to maintain `plan_id`
  and `supersedes` consistency.
* Some reviewers may want historical context in rare cases, so the manifest
  must support explicit opt-in without making history operative by default.

Separate artifacts are still preferable to smarter prose markers. Prose markers
do not reduce token load, do not create hard exclusion boundaries, and still
require a model to infer which paragraphs matter. A separate active artifact
gives the harness a mechanical contract boundary, a smaller input set,
deterministic state discovery, and simpler verification.

## Suggested severity, priority, and bounded implementation decomposition

Suggested severity: `high`

Suggested priority: `P1`, because the defect can block stable work from
converging, multiply review cost, and exhaust circuit-breaker cycles without
any underlying architecture problem.

Suggested bounded decomposition:

1. Define the single-active-plan metadata schema and review-history path
   conventions.
2. Change `plan-review` to emit immutable attempt artifacts and consume explicit
   manifests.
3. Add decided-plan regeneration to the remediation path used after failed
   review cycles.
4. Extend `compact-context` to auto-consolidate on repeated failures or budget
   breaches.
5. Rewrite backlog reference handling to store active-plan paths instead of
   copied operative prose.
6. Add pre-dispatch verification for single-governing-plan invariants,
   exclusions, budgets, and contradictions.
7. Ship migration tooling and coverage for existing append-only plans.

## Out of scope

* Introducing a new service, database, or non-Git storage system.
* Deleting historical review evidence.
* Solving every possible plan-quality issue through prompt wording alone.
* Replacing human judgment about design quality.
* Changing product architecture requirements that are unrelated to the
  plan-review loop.
* Reopening the resolved workspace feature decomposition that triggered this
  report.
