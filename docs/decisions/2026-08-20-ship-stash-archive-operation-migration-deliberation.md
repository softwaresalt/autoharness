---
title: "Migrating Ship post-merge Step 7 from the deprecated backlogit_stash_remove to backlogit_stash_archive"
date: 2026-08-20
doc_type: decision
stash_id: 8D570CF8
agent: "Stage (planning only - Ship executes)"
classification: "chore / deprecated-API migration on a shipped contract surface"
blast_radius: "elevated (multi-family: agent template plus dogfood mirror, policy registry, backlog registry, verifier, contract tests, manifest checksums)"
---

# Deliberation - Ship Step 7 stash-retirement operation migration (`8D570CF8`)

Date: 2026-08-20
Agent: Stage (planning only - Ship executes)
Stash source: `8D570CF8` (low, task, P-021 C2 `DEFERRED SCOPE EXPANSION`)
Source refs: PR #372, task `134.008-T`, feature `134-F`, shipment `143-S`
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Decision (one line)

**Migrate.** Replace `backlogit_stash_remove` with `backlogit_stash_archive`
across the **prescriptive** carriers only, leave every **historical** record
untouched, and hold priority at **low-but-not-deferrable** because the CLI
fallback path documented for this operation **no longer exists**.

## Problem statement

Ship's post-merge Step 7 source-artifact cleanup is documented as calling
`backlogit_stash_remove` on `custom_fields.source_stash_id`. backlogit has
deprecated that operation in favour of `backlogit_stash_archive`.

### Stage verification (read-only)

* `backlogit stash --help` (v1.10.0) lists exactly: `add`, `archive`, `edit`,
  `get`, `harvest`, `list`. There is **no `remove` subcommand**. Confirmed.
* `templates/agents/_ship.agent.md.tmpl` still prescribes `backlogit_stash_remove`
  at **line 38** (Role Boundary table) and **line 819** (post-merge Step 7).
* The dogfood mirror `.github/agents/_ship.agent.md` carries it at **line 47**.
* The `backlogit_stash_remove` **MCP** tool is still exposed by the server and
  still functions today.

## Severity re-assessment

The entry provisionally rated this **low** on the grounds that "the deprecated
MCP tool still functions". That is true but incomplete, and the rating deserves
a correction on the record.

The harness's standard degradation pattern is **MCP tool first, CLI fallback
second** (P-012). For this operation the CLI fallback **does not exist** - there
is no `backlogit stash remove` to fall back to. So the documented step is not
merely stale wording: it is a step whose degraded path is unreachable. If the
MCP tool is withdrawn, or is unavailable in a degraded session, Ship's post-merge
Step 7 has no route to completion and post-merge closure stalls.

**Decision: keep priority `low`** (there is no correctness impact today and no
user-visible breakage), **but treat it as non-deferrable within this staging
cycle** and record the reasoning above so a future triage does not re-defer it
on the incomplete "still functions" rationale.

## Scope boundary - prescriptive vs historical

`backlogit_stash_remove` appears in 15 files. They are **not** all in scope.
Getting this boundary wrong is the main risk in this change.

### In scope - prescriptive carriers (instruct an agent to call the operation)

| File | Sites | Family |
|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | 38, 819 | agent template |
| `.github/agents/_ship.agent.md` | 47 | dogfood mirror (paired edit) |
| `templates/policies/workflow-policies.md.tmpl` | 726 | policy registry (P-021 C5 text) |
| `templates/backlog/registries/backlogit.registry.yaml` | 278 | backlog registry |
| `src/autoharness/verify_workspace.py` | 296 | verifier marker assertion |
| `tests/test_verify_workspace.py` | 1860, 3135 | contract tests |
| `tests/test_scope_containment_boundary_contract.py` | 79, 87, 332, 552 | contract tests |
| `tests/test_scope_containment_policy_contract.py` | 595 | contract tests |

### Explicitly NOT in scope - historical records (immutable)

| File | Why |
|---|---|
| `docs/closure/143-S-134-F-post-merge-closure.md` | closure record of what was actually done |
| `docs/memory/2026-08-18-stage-b48a482a-p021-scope-containment.md` | session memory |
| `docs/memory/2026-08-20-ship-143-s-full-lifecycle-closure.md` | session memory |
| `docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-hardening.md` | shipped hardening record |

These describe decisions taken at a point in time. Rewriting them would falsify
the historical record and is **forbidden** in this change.

### Already correct - no edit needed

`templates/agents/_stage.agent.md.tmpl:309` and `.github/agents/_stage.agent.md`
already describe the deprecation accurately - they are the source that flagged
it. They are **reference text, not migration targets.**

## Coupling to `6D62077C` (the reason these ship together)

`_ship.agent.md.tmpl` <-> `.github/agents/_ship.agent.md` is **one of the four
divergent pairs** that the companion spike `6D62077C` analyses. This migration
therefore *is* a paired edit on a divergent pair, and it must be performed under
whatever maintenance contract that spike settles.

The spike concludes **paired-edit maintained** (do not extend the renderer), so:

* This migration edits **both** sides explicitly and in the same change.
* It refreshes the `harness-manifest.yaml` checksum for the mirrored file.
* The mirror's abridged form is expected: the dogfood copy carries the Role
  Boundary sentence but not the full Step 7 block. Only the sites that exist on
  each side get edited; **no content is back-ported between sides** as part of
  this migration.

**Ordering: the maintenance contract lands first, this migration second.** Doing
it in the other order would perform the paired edit before the rule governing
paired edits exists.

## Options considered

| # | Option | Verdict |
|---|---|---|
| A | Do nothing; the MCP tool still works | Rejected - documented step has no reachable fallback |
| B | Change only `templates/agents/_ship.agent.md.tmpl` | Rejected - leaves mirror, policy, registry, verifier and tests inconsistent; verifier marker would then fail |
| C | **Migrate all prescriptive carriers; leave historical records untouched** | **Chosen** |
| D | C + remove `stash_remove` from the registry entirely | Rejected - the operation still exists upstream; the registry should describe reality. Deprecate in place, do not delete |
| E | C + back-port the missing Step 7 block into the dogfood mirror | Rejected - that is the `6D62077C` drift problem, explicitly out of scope |

## Chosen direction

1. Ship agent template + dogfood mirror -> `backlogit_stash_archive` (paired edit).
2. P-021 C5 clause in the policy registry template -> archive operation, preserving
   the clause's existing removal/archival distinction wording.
3. Backlog registry template: keep `stash_remove` mapped but mark deprecated;
   ensure `stash_archive` is the operation the Ship contract names.
4. Verifier marker assertion -> assert the archive operation.
5. Contract tests + `harness-manifest.yaml` checksum refresh.

## Non-goals

* No change to backlogit itself.
* No edit to any historical closure/memory/hardening record.
* No back-porting of drifted content between template and mirror.
* No change to the workspace's live `.autoharness/backlog-registry.yaml`
  (it currently declares neither stash operation; that gap is noted below).

## Noted, not actioned

The **installed** registry `.autoharness/backlog-registry.yaml` declares neither
`stash_remove` nor `stash_archive`, while the **template** registry
`templates/backlog/registries/backlogit.registry.yaml` declares both. That is a
pre-existing template-vs-installed drift on a different artifact. It is recorded
here for visibility and is **not** fixed in this shipment.

## Traceability

* Stash `8D570CF8` - reconciled in place. Duplicate scan: CLEAN. Review-thread
  ID confirmed legitimately absent (an adjacent PR #374 Copilot thread cites the
  same line region but raises a different concern - executing Step 7, not its
  deprecation).
* Plan: `docs/plans/2026-08-20-ship-stash-archive-operation-migration-plan.md`
* Hardening: `docs/plans/2026-08-20-ship-stash-archive-operation-migration-hardening.md`

---

## ADDENDUM (Stage, 2026-08-20) - the two tool surfaces are INVERTED

Discovered while performing this session's own stash archival, after the plan
was drafted. This is a **material correction to the migration target** and must
be read before executing Task A / Task C.

The MCP and CLI surfaces of backlogit v1.10.0 expose **complementary, inverted**
subsets of this operation:

| Surface | `stash_remove` | `stash_archive` |
|---|---|---|
| **MCP** | EXPOSED, self-described as `[Deprecated: use backlogit_stash_archive]` | **NOT EXPOSED** |
| **CLI** | **NOT EXPOSED** (no `stash remove` subcommand) | EXPOSED (`backlogit stash archive`) |

So the MCP tool's own deprecation notice points at a tool name that this server
build **does not expose**, and the CLI exposes only the replacement.

### Consequence for the migration

A naive rename of the Ship contract to "call `backlogit_stash_archive`" would
name an MCP tool that does not currently exist, replacing a working-but-deprecated
call with a broken one. That is worse than the status quo.

### Corrected direction

The Ship contract must name **both** surfaces, in P-012 MCP-first / CLI-fallback
order, and must not assume the MCP archive tool is present:

1. **Canonical operation**: `backlogit stash archive <id>` (CLI) - exposed, non-destructive.
2. **MCP path**: call `backlogit_stash_archive` **when the server exposes it**;
   on server builds that do not (including v1.10.0), fall back to the deprecated
   `backlogit_stash_remove` alias, which **resolves to the same archive handler**
   and is therefore non-destructive despite its name.
3. The registry (Task B) must keep both mappings for exactly this reason - which
   independently vindicates hardening H5's "deprecate in place, do not delete".

This preserves the deprecation intent (stop naming removal semantics) without
introducing a call to a nonexistent tool, and it keeps a reachable degraded path,
which was the original severity argument for doing this work at all.
