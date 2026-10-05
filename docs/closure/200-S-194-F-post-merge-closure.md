---
shipment: 200-S
feature: 194-F
pr: 490
prs: [490]
merge_commit: b264efd5dfbd5f16e86e2e16b427463f88b5902c
reviewed_head: d7721b00
date: 2026-10-04
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/200-S-194-F-close-evidence.json
---

# 200-S / 194-F Post-Merge Closure: `context_tier` on Model Routing Routes and Agent Frontmatter

## Summary

Shipment 200-S delivers feature 194-F. It adds `context_tier` to model
routing routes and agent frontmatter, seeds a generic Ship route on fresh
installs, and pins the dogfood Ship route. It has these parts:

* an optional `context_tier` (`default` | `long_context`) on every
  `model_routing` route (tiers, `stage`, `ship`, `orchestrator`, and flat and
  nested escalation), edited in place in harness-config schema 1.1.0 under
  D-C5, plus a `context_tier` validator in the shared frontmatter contract
* role-scoped `SHIP_*` / `STAGE_*` route variables, `*_CONTEXT_TIER`, and
  `ESCALATION_CONTEXT_TIER`, with a per-field fallback chain that ends at the
  terminal default `default`
* a fresh-install Ship seed (`gpt-6-luna` / `openai` / `xhigh` /
  `long_context`) that applies only when no `ship` key exists on first install
* the dogfood Ship pin (`claude-opus-5.5` / `anthropic` / `high` /
  `long_context`) and Ship/Stage templates bound to role variables
* `verify-workspace` config-authoritative route precedence (override > config
  > `variables_used`), the `ROUTE_VARIABLE_STALE` warning, and a bounded
  orchestrator `context_tier` directive check
* P-013.5 / P-013.6 policy, install-harness, tune-harness, tuning-guide,
  getting-started, and CHANGELOG updates

Its manifest is `194-F` plus 14 tasks (`194.001-T` .. `194.014-T`). Source
stash: `6EC29DD6`. Source deliberation: `036-DL`.

**PR #490** (`feat(routing): context_tier on model_routing routes and agent
frontmatter, fresh-install Ship seed, dogfood Ship pin (200-S / 194-F)`)
merged as `b264efd5` at `2026-10-04T21:36:18Z`, with reviewed HEAD
`d7721b00`.

## Gates

| Gate | Result |
|---|---|
| Feature PR merge | #490 `b264efd5`, `MERGED` by merge commit (P-009). `b264efd5` has two parents (`47be1007`, `d7721b00`) and is an ancestor of `origin/main` |
| Merge authority | Dark-mode activation record (P-017), merges pre-authorized |
| Local review | Multi-persona review at `5afcb166` (correctness, Python, template integrity, schema-CLI-docs coupling): 0 P0. The P1s and all P2s were fixed in `5d995604`, `d7605ac3`, `6c47b1ab`, `a4ef648f`, `e0f09cbd`, and `be05ed3e`. Outcome `READY_WITH_FOLLOWUPS` at `d7721b00` (P0 = 0, P1 = 0) |
| Copilot review | Cycle 1: one thread, fixed in `d7721b00` (enum-validate `*_CONTEXT_TIER` `config.overrides`). Cycle 2: clean. `autoharness gate copilot-review`: PASS for `d7721b00` |
| CI | Green on `d7721b00` |
| Pre-merge full build | `PYTHONPATH=src python -m unittest discover -s tests`: `Ran 3138 tests`, `OK (skipped=54)` |
| Closure lifecycle topology gate | `autoharness gate pipeline-topology --mode agent --shipment 200-S --phase lifecycle --json`: exit 0 on `chore/200-s-closure` (`BRANCH_OK`, `WORKTREE_TOPOLOGY_OK`, sole active shipment `200-S`, predecessor `199-S` explicit) |
| Pre-mode reconcile | `PROCEED` (15 items: `194-F` `active` in queue; 14 tasks `done` in archive; no orphans; `record-consistent`) |
| `--classify-only` | Exit 0: `CASCADE`, engine `VERIFIED` (`1.11.0` / `131577c`, cli) |
| Mutating `cascade-close` | Exit 0, `postcondition_verdict: pass`, 737 s |
| INV-12 disposition | `DISPOSITION_COMPLETE` |
| Post-mode reconcile | `PROCEED` |
| Closure index resync | `CLOSURE_INDEX_SYNC_OK` (`backlogit sync` after the follow-up stash entries, the final backlog mutation: `Indexed 1711 artifacts`) |
| Closure-evidence gate | `autoharness gate closure-evidence --path docs/closure/200-S-194-F-post-merge-closure.md --shipment 200-S --json`: exit 0 with `compaction_status: done` (the earlier `pending` run failed only `frontmatter_predicate`, as expected) |
| Full unit suite | `Ran 3143 tests`, `OK (skipped=54)` on `chore/200-s-closure` (`acb57265`) |

## Validator Evidence / Runtime Verification

194-F changes the install render and the `autoharness verify-workspace`
runtime surface, so the plan's three runtime proofs
(`docs/plans/2026-09-27-context-tier-model-routing-plan.md`, section Runtime
Verification and Closure) were run against the merged code (`b264efd5`).

* **How proofs ran**: `.proof-scratch/proofs-200-closure.py` (git-ignored)
  drove `.venv\Scripts\autoharness.exe verify-workspace` and the install
  render against scratch workspaces in the Git-ignored, workspace-contained
  `.proof-scratch/200-closure-proofs/` (constitution Principle IV). They were
  left in place, not deleted. Full results:
  `.proof-scratch/200-closure-proofs/results.md`.
* **What was asserted**: `targeted_checks.role_route_resolution`,
  `frontmatter_conformity`, `_ship` migration proposals, `ROUTE_VARIABLE_STALE`
  warnings, and the rendered Ship frontmatter and written config. Exit code 1
  is recorded for information only. Scratch workspaces lack the full pipeline
  agent set, so legacy checks (`escalation_directive_present`,
  `escalation_route_resolution`, `orchestrator_tier_fields`,
  `pipeline_topology_gate_ship_agent_wiring`) fail there independently.

| # | Scenario | Exit | Result | Plan expectation |
|---|---|---|---|---|
| 1 | This repository at `b264efd5`, compared with a pre-200-S extraction at `300d0716` | 1 | `role_route_resolution` `ok: true`; `frontmatter_conformity` ok; no `_ship` migration proposal; no `ROUTE_VARIABLE_STALE`; derived and installed Ship route `claude-opus-5.5` / `anthropic` / `high` / `long_context`. The 10 failing checks are identical at `300d0716` and `b264efd5` (`new_failures: []`) | Dogfood Ship pin holds with no new failure: **met** |
| 2 | Fresh scratch install with no config | 1 | First pass: seed applied, Ship frontmatter `gpt-6-luna` / `openai` / `xhigh` / `long_context`, no placeholders, written config `ship` route identical; `tier2` written with `context_tier: default`. Second pass: `first_install: false`, no re-seed, route unchanged | Seed on first install only, written back: **met** |
| 3 | First install with an explicitly present empty `ship` block, both `{}` and all-`""` fields | 1 | No seed; Ship renders from `tier2` (`claude-sonnet-5` / `anthropic` / `medium` / `default`); family, provider, and effort unchanged against the pre-200-S render of the same config (which had no `context_tier`) | Present `ship` key suppresses the seed; tier2 fallback unchanged: **met** |

The 10 pre-existing failing checks in this repository (proof 1) are
`agents_metadata_catalog_guidance`, `backlogit_sql_schema_instruction`,
`backlogit_yaml_header_instruction`, `copilot_backlog_workflow_expectations`,
`copilot_durable_knowledge_layout`, `copilot_remote_operator_guidance`,
`copilot_session_memory_guidance`, `ship_branch_management`,
`ship_source_artifact_cleanup`, and `stage_shipment_determinism`. They are
already tracked by `50434138`, `97B28746`, and `BCD87392`. Runtime
verification: **PASSED**. `RUNTIME_VERIFICATION_BLOCKED` does not apply.

## Closure Path

`close_path: cascade`. `close_evidence`:
`docs/closure/evidence/200-S-194-F-close-evidence.json` (phase `post_close`,
run `764b96beacbe4535944593ccd6901aca`, `merge_commit_sha` `b264efd5…`).

* **Lock**: `.backlogit/queue/200-S.md` was held from pre-mode
  (`2026-10-04T21:46:29Z`) through post-mode (released
  `2026-10-05T00:00:09Z`).
* **Classification**: classifier `CASCADE`, qualifying root `194-F`, no
  out-of-manifest descendants. Disposition snapshot: `036-DL`.
* **Timeout sizing**: N = 15 + 1 = 16. B = ceil(1.5 × (133 + 35 × 16)) =
  1040 s, which is at most 1800 s, so the default `--timeout` (1800 s) was
  used. The supervision budget was 2400 s. The Orchestrator ran the command
  attached and waited until it exited.
* **Mutating run**: `autoharness shipment cascade-close --shipment 200-S
  --feature 194-F --sha b264efd5… --message "Merge pull request #490 …"
  --author "Derek Williams <…>" --json`. Exit 0. The command took 737 s; the
  `backlogit shipment ship` child took about 710 s
  (`23:45:54Z` → `23:57:44Z`), with `timed_out: false` and
  `mutation_state: completed`.
* **Postconditions** (from the `post_close` record):
  * `archived_ids`: 16 IDs (`194-F`, the 14 tasks, and `200-S`)
  * `returned_ids`: `[]`
  * `allowed_ids` and `required_ids` are the same 16 IDs
  * `unexpected_archived` and `missing_required` are both `[]`
  * `parent_id_preserved`, `baseline_invariant`, and
    `disposition_byte_identical` are all `true`
  * shipment record `status: archived`, `archived_status: shipped`
* **Whole-tree guard**: the Orchestrator fingerprinted 1895 files (every file
  under `.backlogit/queue/` and `.backlogit/archive/`, including both stash
  files and lock files) before the run. Ship re-fingerprinted the same set
  after the run (1895 files). Only the 18 `closure_scope(S)` paths changed
  (16 archive records plus the `194-F` and `200-S` queue copies); 0 changes
  were out of scope.
* Cascade gate: **`CLOSED`**. No P-005 event. Ship made no direct
  `backlogit shipment ship` call and did not substitute `SAFE_CLOSE`.

## Linked-Deliberation Disposition (P-015 INV-12)

The step ran under the same lock, after `CLOSED` and before post-mode, with
all inputs taken from the evidence record. The planner result equals the
`pre_close` snapshot. There was no planned `archive`, so Ship made no
deliberation mutation. The final invariance check found no fingerprint diff
(1753 non-exempt paths) and no porcelain diff.

| id | link_kinds | linking_members | outcome | reason_code | referrers |
|---|---|---|---|---|---|
| `036-DL` | `source_deliberation_id`, `description` | `194-F`, `194.001-T` .. `194.014-T` | `retained_shared_reference` | `retained_shared_reference` | `BAF15C62` |

No unresolved references and no read failures. Neither
`ENGINE_SEMANTICS_UNVERIFIED` nor `ENGINE_LINE_UNVERIFIED_ADVISORY` applies.
`stranded_linked_deliberation`: `["036-DL"]`.
**`recommendation: DISPOSITION_COMPLETE`**.

Reports:

* Pre-mode: `.backlogit/reconcile/200-S-pre-20261004-214630.md` (`PROCEED`)
* Cascade close and disposition:
  `.backlogit/reconcile/200-S-cascade-close-20261004-235951.md` (`CLOSED`,
  `DISPOSITION_COMPLETE`)
* Post-mode: `.backlogit/reconcile/200-S-post-20261005-000007.md` (`PROCEED`)

## Source Artifact Cleanup

The only shipped top-level item is `194-F`. None of the 14 tasks declares a
`source_stash_id` or `source_deliberation_id`.

| Item | Field | Value | Outcome | reason_code |
|---|---|---|---|---|
| `194-F` | `source_stash_id` | `6EC29DD6` | skipped: already archived (in `.backlogit/archive/stash.jsonl`) | n/a |
| `194-F` | `source_deliberation_id` | `036-DL` | `retained_shared_reference` (copied from the disposition report; active stash entry `BAF15C62` still references it; Ship did not archive it) | `retained_shared_reference` (copied) |

Archived source artifacts: 0 stash entries and 0 deliberations. Ship made no
change to plan, decision, review, or spike artifacts (P-010).

## Releasability Evidence

* **Status**: READY. The change is already on `main` (#490).
* **Invariants to preserve**: the following must keep holding:
  * a role route resolves `context_tier` per field and ends at the terminal
    default `default`; an absent `context_tier` never changes family,
    provider, or effort
  * the fresh-install Ship seed fires only on first install when no `ship`
    key exists, and is never re-applied
  * `verify-workspace` keeps override > config > `variables_used` precedence
    only when the config carries a `model_routing` mapping, and reports
    `ROUTE_VARIABLE_STALE` instead of failing
* **Deployment path**: merge-only. Consumers get the change in the next
  autoharness release; existing installs pick up `context_tier` on their next
  re-render or tune.
* **Monitoring**: the CI `test` job, the canonical unit suite, and
  `autoharness verify-workspace` on installed workspaces (`role_route_resolution`,
  `context_tier_overrides`, and `ROUTE_VARIABLE_STALE` warnings).
* **Healthy signals**: `role_route_resolution` `ok: true` in this repository
  and in fresh installs; fresh installs render the seeded Ship route; no
  `ROUTE_VARIABLE_STALE` in this repository.
* **Failure signals**: any of the following:
  * a Ship or Stage agent rendered with an unresolved `{{*_CONTEXT_TIER}}`
    placeholder
  * the seed re-applied over an operator `ship` route
  * family, provider, or effort changing for a config that sets no
    `context_tier`
  * a suite regression in the routing, seed, or role-render tests
* **Rollback trigger**: a routing or render defect that changes resolved
  routes for configs without `context_tier`, or a suite regression
  attributable to 194-F.
* **Rollback procedure**: `git revert -m 1 b264efd5`. The backlog state
  committed by this closure stays valid either way. Restoring individual
  archived records uses `backlogit restore`.
* **Owner**: operator (softwaresalt). The Ship agent owns closure mechanics.
* **Validation window**: through the next two install, tune, or verify runs
  against an installed consumer workspace.
* **Risky action record**: the mutating `cascade-close` (destructive,
  archives 16 artifacts): ActionRisk high. Approved through the dark-mode
  activation record (P-017) and the classify-only `CASCADE` / `VERIFIED`
  routing. Result: exit 0, postconditions pass.

## Verification

`$env:PYTHONPATH='src'; python -m unittest discover -s tests` (venv Python) on
the closure branch at `acb57265`: `Ran 3143 tests in 490.406s`,
`OK (skipped=54)`, exit 0.

## Follow-Up Items

All follow-ups are active stash entries. Stage owns triage. The new entries
are P-021 C2 `DEFERRED SCOPE EXPANSION` captures that require deliberation.

* `09DFC9F9` (new, task/low): `context_tier` route-resolution hardening in
  `verify_workspace.py`: the resolver neither strips nor enum-validates a
  config route `context_tier` (the schema is the guard); `str()` coerces
  non-string `config.overrides`; `per_role.source` reads `legacy_flat` when
  the flat route declares only `context_tier`; and three render-path helpers
  default `config_authoritative=True`.
* `EFC48191` (new, task/low): the fresh-install seed trigger test
  re-implements the rule instead of calling it, and the no-literal
  `long_context` template scan is broader than the frontmatter guarantee.
* `D6FE4677` (new, task/low): pre-existing stale vendor prose (hardcoded
  default-routing table and the GPT-5.4 cross-provider example) in the
  orchestrator template.
* `8447F9EB` (new, task/low): a stale line-range reference in a
  `harness-manifest.yaml` note.
* `9039DA3F` (new, bug/low): `autoharness verify-workspace --help`, a missing
  option value, or a positional path prints "Unknown verify-workspace
  argument" and the top-level usage, and exits 2.
* `7A3E1AD7` (new, task/low): an orphan test block in
  `tests/test_verify_workspace.py` (location to confirm at triage).
* `50434138`, `97B28746`, and `BCD87392` (existing): the 10 pre-existing
  dogfood `verify-workspace` instruction-content check failures.
* `24BA1B8F` (existing, task/low): the pre-existing MD001 heading error in
  `.github/policies/workflow-policies.md` (now at line 500).
* `BAF15C62` (existing, chore/low): subagent mirror tier1 route drift. It
  also keeps `036-DL` retained.

## Residual Risks

* `036-DL` remains live (`queued`) and stranded. `194-F` is now archived, so
  no later closure re-runs the disposition step for 194-F. Its active
  referrer `BAF15C62` keeps it retained until Stage acts on that entry.
* The cascade rewrote each task's `commit` field to `b264efd5`. The
  implementing commits remain in git history (#490).
* Installs rendered before 200-S fail the stricter orchestrator `context_tier`
  directive check until re-rendered (documented in the CHANGELOG and the
  tuning guide).

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this closure's
session memory was written.

* **Assessment**: `docs/memory` held 179 files (about 1315 KB), which
  exceeds the generic thresholds in aggregate.
* **Candidates**: the run was a bounded Tier-1 pass over this release unit.
  The single 200-S memory (the 2026-10-04 closure session) was consolidated
  into
  `docs/memory/compacted/2026-10-04-ship-200-s-194-f-full-lifecycle-compacted.md`.
  The verbose original is under `docs/archive/memory/`.
* **Excluded**:
  * other release units' memories, which are out of scope for this bounded
    run
  * plans, because Stage owns that work (P-010)
  * closure records, which are fresh (under `threshold_days`)
