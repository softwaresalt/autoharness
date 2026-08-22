---
date: 2026-08-22
agent: ship
shipment: 152-S
feature: 144-F
prs: [397, 398]
status: closed
title: "Ship session memory — 152-S (mechanism A: GIT_CONFIG_* Windows env containment) shipped and closed"
---

# Ship Session Memory — 152-S Shipped and Closed

## Scope

Owned Ship/PR lifecycle end-to-end for bug E8158860, from staging PR #397
through shipment 152-S completion, as a persistent background invocation
(resolved route: model_family=claude-sonnet-5, model_provider=anthropic,
reasoning_effort=high; no ROUTING_DEGRADED).

## Phase A — staging PR #397

- Multiple review-fix cycles handled across the session (Stage-owned
  plan/backlog/carrier corrections), each gated through P-021 C1
  classification before any fix, replies posted citing the fixing SHA,
  threads resolved only after reply.
- Final review-fix cycle correction: `b2ceaec7` (dotted unittest command
  Windows `PYTHONPATH='src;tests'` correction across 145.001-T/plan/review).
- P-018 gate: SATISFIED at final HEAD. Merged PR #397 with a normal merge
  commit (two parents verified). `main` synced; verified both
  `.backlogit/queue/152-S.md` and `153-S.md` present on `origin/main`.

## Phase B — shipment 152-S (feature 144-F, mechanism A)

- Reloaded main instructions/config; verified checkpoint state, queue
  dependencies, topology gate, and 152-S eligibility (153-S correctly
  blocked/not claimed).
- Claimed 152-S; created and maintained CheckpointV1
  (`checkpoint-20260822-*.json`, `agent: ship`) across major boundaries
  (implementation start → review-fix cycles → halt/escalation →
  post-merge closure), resolving stale checkpoints before creating new
  ones rather than accumulating them.
- Implemented all 7 planned tasks (144.001-T–144.007-T) per
  `docs/plans/2026-08-22-git-config-env-containment-plan.md` and its
  hardening amendments: L0/L1/L2 Windows process topology, blank-sentinel
  seeding, `tests/_env_patch.py` restore-by-diff helper, 13 bulk
  `os.environ` mutation-site migrations, empty structural-guard allowlist,
  narrowly-shaped `GIT_CONFIG` normalizer, canonical unittest discovery
  in-process with before/after child probes and a mandatory negative
  control, byte/per-key equality, and canonical subprocess count
  equivalence. This is not test-only: `144.006-T` also made a production
  fix in `src/autoharness/gates/topology.py`, stopping the `_run_git`
  git-infrastructure-failure path from being laundered into a false
  domain diagnosis (assertion integrity for the existing
  `pipeline-topology` gate's `check-ignore` invocation).
- Feature PR #398 went through **4 rounds** of Copilot review on the
  `_EnvMutationVisitor` AST structural guard
  (`tests/test_test_suite_isolation_contract.py`) — see the companion
  compound-learning doc
  `docs/compound/2026-08-22-ast-scope-aware-alias-resolution-legb-pitfalls.md`
  for the full technical detail of the three fixed LEGB-scoping bugs
  (flat-map aliasing → scope stack; class-body-as-false-enclosing-scope;
  decorator/header timing vs. body scope) and the accepted round-4
  residual risk (control-flow-insensitive alias tracking, P2, no live
  exploit in-repo today).
- Round 4 exceeded the 3-cycle review-fix budget (Stop Conditions table);
  halted and escalated per protocol rather than auto-fixing a 4th cycle.
  Operator explicitly delegated disposition: accept as documented residual
  risk (not a P-021 C2 capture — the finding passed C1, it was simply over
  budget), do not perform a 4th fix cycle.
- Canonical Windows full suite: 1830 tests, 0 failures, 0 errors,
  skipped=20, at final HEAD `ef96eb72`. Linux CI parity confirmed green.
- P-018 gate SATISFIED (no unresolved threads) at merge time. Repo merge
  settings confirmed P-009 compliant (`allow_merge_commit: true`,
  squash/rebase both disabled).
- Merged PR #398 via normal merge commit `f0cad43c04ad98809685db0fb247db1e9a287bb6`
  (parents `d6c9568c` + `ef96eb72`, verified). `main` fast-forwarded;
  all 12 pre-existing stashes (including both `.mcp.json`-related ones)
  preserved untouched throughout.

## Post-merge closure

- Shipment 152-S manifest's covering feature (144-F) verified as a
  P-015 fully-covered root via the authoritative
  `classify_shipment_close_path()` (`src/autoharness/gates/shipment_closure.py`):
  CASCADE close path permitted.
  `backlogit shipment ship 152-S --sha f0cad43c...` executed; all 4
  Cascade Close Sub-Procedure gates verified (empty `returned_ids`, exact
  `archived_ids` match, unchanged `parent_id` on all 7 re-read archived
  tasks). Gate decision: CLOSED. `archived_status: shipped` confirmed.
- Post-merge closure branch
  `post-merge/144-f-mechanism-a-git-config-env-containment` created from
  `main` per Post-Merge Branch Protocol (closure commits never land
  directly on `main`); cascade-close backlog mutation committed there
  (`a9c3d7a4`), plus this compound-learning doc and session memory.
- P-020 `compact-context` invocation and closure PR creation/merge tracked
  as the remaining steps for this closure (see checkpoint for exact
  cursor if resumed).

## Key operational lessons (session-level, process not code)

- The Stop Conditions "3 review-fix cycles per PR" limit is a real,
  binding circuit breaker even under an operator instruction toward
  "autonomous end-to-end completion" — the correct behavior at the limit
  is to halt and present the finding for explicit disposition, not to
  infer authorization to continue. The operator's subsequent explicit
  disposition (accept as residual risk) is what unblocked progress, not
  the original autonomy instruction.
- P-021 C1-passing-but-over-budget is a distinct disposition path from
  P-021 C2 (out-of-scope capture) — conflating the two would have
  produced a misleading deferred-scope-expansion backlog entry for a
  finding that was never out of scope in the first place. The residual
  risk here belongs in PR readiness/follow-up notes, not in a captured
  C2 stash entry.
- `backlogit shipment ship` (cascade close) is slow (~2 minutes for 7
  tasks + 1 feature + 1 shipment) and can appear to hang; patience
  (poll, don't assume failure) is required, but the 4-gate verification
  protocol afterward is what actually proves correctness, not the
  command's mere completion.
