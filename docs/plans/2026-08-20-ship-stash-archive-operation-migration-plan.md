---
title: "Migrate Ship post-merge Step 7 to backlogit_stash_archive"
date: 2026-08-20
stash_id: 8D570CF8
deliberation: docs/decisions/2026-08-20-ship-stash-archive-operation-migration-deliberation.md
hardening: docs/plans/2026-08-20-ship-stash-archive-operation-migration-hardening.md
requires_plan_hardening: yes
hardening_present: yes
blast_radius: "elevated (multi-family: agent template plus dogfood mirror, policy registry, backlog registry, verifier, contract tests, manifest checksums)"
---

# Implementation Plan - Ship Step 7 stash-archive migration

Date: 2026-08-20
Agent: Stage (planning only - Ship executes)
Stash source: `8D570CF8`
Deliberation: `docs/decisions/2026-08-20-ship-stash-archive-operation-migration-deliberation.md`
Classification: **chore / deprecated-API migration on a shipped contract surface**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Goal

Make every **prescriptive** carrier name `backlogit_stash_archive` as the
operation Ship uses to retire a source stash entry at post-merge Step 7, leaving
every **historical** record untouched.

## Non-goals

* No change to backlogit itself.
* No edit to `docs/closure/`, `docs/memory/`, or the shipped 2026-08-18 hardening
  record - these are immutable history (deliberation lists them by name).
* No back-porting of drifted content between `_ship` template and mirror.
* No change to the live `.autoharness/backlog-registry.yaml`.
* No deletion of `stash_remove` from the registry - deprecate in place.

## Task A - Ship agent template + dogfood mirror (paired edit)

**Files**
* `templates/agents/_ship.agent.md.tmpl` - line 38 (Role Boundary), line 819 (Step 7)
* `.github/agents/_ship.agent.md` - line 47 (Role Boundary)

Replace the operation name with `backlogit_stash_archive` at each site. Preserve
the surrounding clause wording exactly, including the existing parenthetical
distinguishing this **manifest-derived closure operation** from **discretionary**
removal - that distinction is load-bearing for P-021 C5 and must survive.

At the Step 7 site, also update the follow-on sentence so the already-retired
case reads in archive terms ("if the stash entry is already archived, skip and
log it").

**Paired-edit obligation**: both sides edited in this same change, per the
maintenance contract landed earlier in this shipment. The mirror carries only
the Role Boundary site; that asymmetry is expected and is **not** to be
"fixed" here.

**Acceptance**
* No prescriptive occurrence of `backlogit_stash_remove` remains in either file.
* Role Boundary clause semantics unchanged apart from the operation name.
* Both sides changed in one commit.

## Task B - Policy registry + backlog registry templates

**Files**
* `templates/policies/workflow-policies.md.tmpl` - line 726 (P-021 C5)
* `templates/backlog/registries/backlogit.registry.yaml` - line 278

For C5: name the archive operation. **Preserve verbatim** the clause's existing
treatment of removal and archival as *separately named prohibited discretionary
dispositions*, and the manifest-derived exception. This clause was hardened
deliberately (H2); do not simplify it while renaming the operation.

For the registry: keep the `stash_remove` mapping present but marked deprecated,
and ensure `stash_archive` is the operation the Ship contract resolves to.

**Acceptance**
* C5 still prohibits discretionary removal **and** discretionary archival.
* The manifest-derived post-merge exception still reads as allowed.
* Registry still resolves both operations; `stash_remove` marked deprecated.

## Task C - Verifier marker assertion

**File**: `src/autoharness/verify_workspace.py` - line 296

The `ship_source_artifact_cleanup` check requires
`.github/agents/_ship.agent.md` to contain `backlogit_stash_remove`. Update the
required marker to `backlogit_stash_archive`.

**Ordering hazard**: this check and Task A must land together. If Task A lands
alone, this check fails; if Task C lands alone, it fails immediately. Sequence
them in the same commit or adjacent commits within the same PR.

**Acceptance**
* Marker list names the archive operation.
* `verify-workspace` passes against this repository's own install.

## Task D - Contract tests + manifest checksum refresh

**Files**
* `tests/test_verify_workspace.py` - lines 1860, 3135
* `tests/test_scope_containment_boundary_contract.py` - lines 79, 87, 332, 552
* `tests/test_scope_containment_policy_contract.py` - line 595
* `.autoharness/harness-manifest.yaml` - checksum for `.github/agents/_ship.agent.md`

Update expectations to the archive operation. Refresh the manifest checksum for
the mirrored file changed in Task A.

**Care required**: some of these assertions encode the P-021 C5 *clause
semantics*, not merely the operation string. Update the operation name without
weakening any assertion about the removal/archival distinction.

**Acceptance**
* Full test suite green.
* Manifest checksum matches the actual committed bytes of the edited mirror
  (this is the same property the divergent-pair contract test asserts).
* No historical record modified - confirm with `git diff --name-only` that
  nothing under `docs/closure/` or `docs/memory/` appears.

## Verification (Ship)

1. `grep -r backlogit_stash_remove` returns **only** historical records, the
   deprecated-but-retained registry mapping, and the Stage reference text that
   describes the deprecation.
2. `verify-workspace` clean.
3. Full test suite green.
4. `git diff --name-only` contains no path under `docs/closure/` or `docs/memory/`.

## Sequencing

Second within its shipment, **after** the paired-edit maintenance contract.

## Plan Review (plan-review gate)

**Verdict: PASS WITH CONDITIONS.** Reviewed 2026-08-20 by Stage.

| Check | Result |
|---|---|
| Prescriptive vs historical boundary explicit | PASS - both lists enumerated by file and line |
| Each task within the 2-hour rule | PASS |
| Width isolation | PASS - A templates, B policy/registry, C CLI source, D tests/manifest |
| Acceptance criteria falsifiable | PASS |
| Blast radius honestly stated | PASS - elevated |
| Hardening required (P-006) | **YES** - elevated blast radius, multiple template families, and a live policy clause. Hardening performed; see linked hardening record |
| Coupling to `6D62077C` acknowledged | PASS - ordering stated and justified |

**Conditions carried into execution** (from hardening):
1. Tasks A and C must not land in isolation from one another (H1).
2. The C5 removal/archival distinction must survive the rename verbatim (H2).
3. No historical record may be edited; verified by an explicit `git diff` check (H3).

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
