---
title: "Deliberation: verification-gated disposition for documentation-only tasks"
description: "Options, trade-offs and decisions for a durable, explicit, diff-verified route that lets strictly qualifying docs-only tasks proceed without the harness-ready label or a RED harness, while every code, test, template and config task stays test-first. Reuses the intended design of engram deliberation 036-D and its operator install, simplified where the autoharness workspace already provides the guarantee."
doc_type: deliberation
date: 2026-10-19
stash_entries: [E89674F1]
upstream_sources:
  - "engram deliberation 036-D / stash 1AD161B8 (C:/Source/GitHub/engram/docs/decisions/2026-09-24-docs-only-task-harness-disposition-deliberation.md)"
  - "engram plan C:/Source/GitHub/engram/docs/exec-plans/2026-09-24-docs-only-verification-gated-harness-disposition-plan.md (revision 3, review circuit open, superseded by the operator's manual install, engram commit f6f3171f)"
deliberation_id: "042-DL"
status: decided
requires_plan_hardening: "yes"
---

# Deliberation: docs-only task disposition

All times UTC. Staged unattended (operator AFK-capable), so each decision is Stage's recommendation with the trade-off
recorded. Items the operator may overturn are listed under Assumptions and are repeated in the plan (section S5).

## Problem frame

Facts read on 2026-10-19:

* **P-002** (`templates/policies/workflow-policies.md.tmpl`, lines 36-55) makes the `harness-ready` label the only Ship
  precondition. Its postcondition requires a compiling harness and a confirmed RED roster.
* **P-004** scopes RED to a per-task roster. `harness-surface:none` removes the roster and the RED obligation, but the
  task still ends the harness-architect step with `harness-ready`, so the label still asserts "the harness compiles"
  for a task that has no harness. The label therefore carries no information about what the task may touch, and nothing
  verifies afterwards that a task declared harness-free stayed out of production code.
* **Ship** (`templates/agents/_ship.agent.md.tmpl`, lines 344-349, 413, 487) filters, scaffolds and admits tasks strictly
  by `harness-ready`. `build-feature` (line 12) is documented as invoked only for `harness-ready` tasks.
* **harness-architect** (`templates/skills/harness-architect/SKILL.md.tmpl`, Step 6) is the only applier of `harness-ready`.
* **No gate code** in `src/autoharness/gates/` reads `harness-ready`. The check is template and policy text only.
  `src/autoharness/harness_surfaces.py` resolves `harness-surface:<id>` declarations; `SUPPORTED_SURFACES` holds only
  `harness-architect`, and `harness-surface:none` already means "no surfaces required".
* **Engram's field experience (036-D).** Docs-only task 142.059-T (owns only `docs/troubleshooting.md`) deadlocked
  its shipment because no label let Ship start it. Engram's operator installed a manual route in its workspace
  (`harness-verification-gated`, policy 1.25.0, `_ship` Step 2, build-feature, harness-architect) and asked for the same
  route upstream so the next re-render does not overwrite it. Engram's installed text is the reference design.

## Options

| # | Option | Pro | Con |
|---|---|---|---|
| A | Status quo: docs-only tasks use `harness-surface:none` and still get `harness-ready` | No change | `harness-ready` is a false claim for a harness-free task; no scope fence; no diff-verified evidence; engram's deadlock recurs whenever harness-architect cannot honestly apply the label |
| B | One-off waivers per task | Fast | Not durable, not auditable as policy, self-authorized override risk (P-005); engram's operator already rejected it |
| C | Engram's installed route verbatim (label, qualification, durable verification record, full workspace baseline snapshot at Step 4.1 incl. per-file content hashes) | Proven shape; converges with the operator's downstream install | The snapshot machinery is large (symlink targets, index vs worktree hashes) and duplicates what P-011 already guarantees (clean worktree at branch creation) |
| D | **Route C's qualification and evidence contract, with the baseline reduced to the recorded start SHA plus a deterministic diff checker** | Same fail-closed qualification; diff-provable and auditable; small enough for one shipment; testable as a pure function | Departs from engram's installed baseline wording (engram re-renders will replace its manual text; behaviour stays stricter or equal) |

## Decision D-1: adopt Option D

A task takes the docs-only route if and only if all of the following hold, otherwise it stays on the code route and
unresolved ownership is a halt, never permission to use the docs label:

1. **Explicit owned paths.** The task declares its `Owned files`. Missing, empty or ambiguous declaration disqualifies.
2. **Prose Markdown under the docs root only.** Every owned path, after normalization (no empty/`.`/`..` segment, no
   drive, colon or backslash, no absolute path, no symlink or Windows reparse point in the path or any parent, resolving
   inside the workspace), is a regular `.md` file under `{{DOCS_ROOT}}`. Fail closed when `{{DOCS_ROOT}}` is empty, `.`
   or the repository root. Case-insensitive comparison on case-insensitive file systems.
3. **Deny list wins.** No owned path may be under `.github/`, `.autoharness/`, the backlog root, `templates/`, `schemas/`,
   `scripts/`, `src/`, `tests/`, or be a policy, config, schema, template, script, build or test artifact, even when it
   sits under the docs root (for example a file a test pins). Mixed scope disqualifies the whole task (split it).
4. **Durable verification record before implementation.** A comment on the task (or another Ship-owned execution
   record) lists executable gates separately from manual gates. Each executable gate has an exact non-empty literal
   command, working directory, exact pass criteria and a result/evidence field. Each manual gate names source and target
   paths, exact pass/fail criteria and required evidence. At least one executable gate exists and it includes the
   workspace's Markdown lint command (P-008) over the owned paths. Missing, empty, ambiguous or unreadable records fail
   closed; a prose cross-check is not a command.

The label is `harness-verification-gated` (the name engram already installed, so the downstream manual install and the
upstream template converge). It is exclusive with `harness-ready`: a task never carries both. A docs-route task also
declares `harness-surface:none` so the existing harness-surface resolver reports "no surfaces required" unchanged.

## Decision D-2: roles

* **harness-architect** classifies, validates the verification record and applies only the route label. It creates no
  stub, no test and no RED evidence for a docs-route task.
* **Ship** re-checks qualification at intake and at claim, accepts exactly the route matching the task's qualified
  ownership (`harness-ready` for code, `harness-verification-gated` for docs-only), and halts on a missing or
  mismatched route.
* **build-feature** executes the docs route with the recorded commands; it never invents a RED phase.
* **Stage** never applies either label (it only declares `harness-surface:none` on a task whose file budget qualifies
  and says in the task body that it is a docs-route candidate).

## Decision D-3: baseline and completion proof (the divergence from engram)

* Baseline is the **start SHA**: Ship records `git rev-parse HEAD` in a task comment at Step 4.1, immediately after the
  task is `active`, before any telemetry, pre-build read or docs edit. P-011 requires a clean worktree only **before
  the claim**, so the start SHA characterizes the pre-claim state and not a clean tree: after the claim and task
  activation, Ship's own lifecycle writes legitimately change tracked backlog files (`status`, `updated_at`,
  `custom_fields.scheduler_baseline_claim` and the route label on the task, its feature and its shipment, plus new
  checkpoint files). The start-SHA comment itself goes to the item log under `<backlog root>/logs/`, which is
  git-ignored, so it adds no tracked change. An owned path that is already modified at qualification fails closed (no
  retroactive qualification of partial work).
* Completion proof is a deterministic, pure, no-network checker, `autoharness harness docs-only-check` (module
  `src/autoharness/docs_only_check.py`), run in two phases against the same inputs: the repository root, the start SHA,
  the owned paths, the docs root, the backlog root, the lifecycle IDs (`--task`, its `--feature`, its `--shipment`) and
  the shipment's live manifest member list (read from the shipment file, never supplied by the caller).
  The claim is a **shipment-wide** write: P-002.7/P-002.8 specify that `ClaimShipment` activates and stamps every
  queued manifest member, so after the claim the tracked backlog diff contains sibling-task writes as well as the
  current task's. A fixed three-ID allowlist would reject a valid multi-task shipment (PR 543 review thread 3), so the
  checker separates *claim-only deltas* from *task-time deltas*:
  1. **Baseline phase** (`--phase baseline`, run by Ship at Step 4.1 right after the task is `active`): computes the
     union of `git diff --name-status <start-sha>`, staged, unstaged and untracked paths and requires that every changed
     path is a backlog file of the task, its feature, its shipment or one of the shipment's manifest members, and that
     each such file's change is a **claim-only delta**: frontmatter limited to `status` queued to active, `updated_at`
     and `custom_fields.scheduler_baseline_claim` equal to the shipment ID, body byte-identical. Any other changed path
     (outside or inside the backlog root), any owned path already modified, or any non-claim delta fails closed
     (`BASELINE_NOT_CLAIM_ONLY`), so partial work can never be retroactively qualified. On pass it emits the
     **lifecycle baseline**: a map of each such backlog file path to the SHA-256 of its LF-normalized content at that
     moment, which Ship records in the task comment (item log).
  2. **Completion phase** (`--phase completion --baseline <record>`): computes the same changed-path union and
     partitions it into two classes.
     * **Implementation class**: every path outside the backlog root. It passes only when every such path is an owned
       path satisfying D-1 item 2 and item 3.
     * **Lifecycle class**: every path under the backlog root. A sibling manifest member file must be byte-identical
       to its baseline digest (a sibling never changes during this task). The task, its feature and its shipment may
       differ from baseline only in the allowlisted frontmatter keys (`status`, `updated_at`, `commit`,
       `archived_from`, `archived_status`, `labels` limited to adding or removing `harness-verification-gated` and
       `harness-ready`, `custom_fields.scheduler_baseline_claim`, `custom_fields.harness_status`) with the body
       byte-identical; a newly added `<root>/checkpoints/*.json` is admitted. Every other backlog path (an item outside
       the manifest, a stash file, a body edit, a non-allowlisted key) is a violation (`BACKLOG_PATH_NOT_LIFECYCLE`),
       so arbitrary backlog changes are never exempted.
  Exit `0` pass, `1` violation (names each offending path and rule), `2` invalid input or git failure (fail closed).
  `--json` emits a schema-stable record for the task comment.
* Ship Step 4.3 (full gate) still runs; the docs route removes only the harness-ready/RED obligation, never a
  completion gate. The task cannot move to `done` until every recorded executable and manual gate has a recorded
  passing result and the checker has returned `pass`.

## Decision D-4: anti-loophole

A declared or actual non-docs path (checker exit `1`) is a P-002 violation: halt, emit the P-005 telemetry event, do not
complete the task on the docs route. Recovery is to revert the stray change and re-run, or to re-scope the task as a
code task through harness-architect. A task may not be moved between routes after implementation started.

## Decision D-5: scope of this shipment

In scope: P-002 and P-004 amendments (policy version 1.39.0), the Ship, harness-architect and build-feature templates
with installed mirrors, backlog config label list, `harness_surfaces.py` interaction test (no code change expected),
the new checker plus CLI, schema for the checker JSON record, tests, `docs/gates-reference.md`, and the Stage harvest
wording. Out of scope: any change to the code route, any change to the P-004 roster rules, retrofitting existing tasks.

## Assumptions (safe, fail-closed defaults; operator may overturn)

* **AS-1** Reuse the label name `harness-verification-gated` (convergence with engram's install).
* **AS-2** Only prose `.md` under the docs root qualifies; `.mdx`, images, diagrams and any non-Markdown file do not.
* **AS-3** The deny list overrides the docs root, so a docs file that a test pins is not docs-only.
* **AS-4** Start-SHA baseline (D-3) is accepted in place of engram's full workspace snapshot.
* **AS-5** The Markdown lint command is mandatory in every verification record.
* **AS-6** The checker is a new CLI subcommand under the existing `autoharness harness` group, additive, no schema
  version bump of existing contracts.
* **AS-7** (PR 543 review threads 1 and 3) Backlog-root writes are admitted only through the two-phase, structurally
  validated mechanism in D-3 (claim-only baseline over the whole shipment manifest, then sibling-unchanged and
  allowlisted task/feature/shipment deltas); the acceptance tests must run the full sequence claim, baseline,
  start-SHA comment, docs edit, completion on a **two-task shipment** and still reject unrelated edits (an item outside
  the manifest, a stash file, a body edit, a non-allowlisted frontmatter key, a sibling edited during the task, a
  `src/` file).

## Open questions (none blocking)

* Whether engram's operator wants the downstream install text replaced by the upstream render on the next tune (the
  upgrade guide tells them how; no action in this repository).
* Whether the docs-only route should later extend to `.autoharness`-owned prose such as session memory (not decided;
  excluded by AS-2/AS-3).

## Plan hardening requirement

Elevated blast radius: policy text, three template families plus mirrors, a new CLI surface and a new JSON schema.
`requires_plan_hardening: yes`; the hardening record is the plan's "Plan hardening" section.
