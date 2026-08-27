---
shipment: 108-S
feature: 104-F
tasks: [104.001-T, 104.002-T, 104.003-T, 104.004-T, 104.005-T, 104.006-T, 104.007-T, 104.008-T, 104.009-T]
feature_pr: 276
merge_commit: f37e251e6bda94dd1233c11907054f71bc8f529e
merged_at: "2026-08-02T01:41:59Z"
reviewed_head: e30456062038b08b8692c46deb7c4b599f470ad9
closure_status: READY
compaction_status: done
---

# 108-S / 104-F Post-Merge Closure — Role-based model routing enforcement (invocation-time, verifiable)

Shipment `108-S` (feature `104-F`) makes P-013.5 role-based model routing
executable and verifiable at invocation time instead of an informal session
promise: schema → config → installer → Orchestrator invocation directive →
skill-delegation inheritance → policy → fail-closed verifier assertions →
docs/compound learning. Executed end-to-end under P-017 dark factory mode
routed to `claude-sonnet-5`. This is the **final shipment** in the bounded
dark scope `[107-S, 108-S]`.

## Merge Confirmation

- PR **#276** merged to `main` at `2026-08-02T01:41:59Z` with merge commit
  `f37e251e6bda94dd1233c11907054f71bc8f529e`.
- The merge commit has **two parents** (`df361b38e164563a0b7d3a1a12beb832e12996e9`
  base + `e30456062038b08b8692c46deb7c4b599f470ad9` feature HEAD), preserving
  the P-009 merge-commit strategy. Repo settings verified pre-merge:
  `mergeCommitAllowed: true`, `squashMergeAllowed: false`,
  `rebaseMergeAllowed: false` — only "Create a merge commit" was possible.
- Merge SHA confirmed as ancestor of `origin/main` (`merge-base
  --is-ancestor` exit 0); local `main` fast-forwarded to `f37e251`. Closure
  work was cut from synced `main` on branch
  `post-merge/104-role-based-model-routing`.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Reviewed HEAD | `e30456062038b08b8692c46deb7c4b599f470ad9` (== PR HEAD at merge) |
| Local review (adversarial, code-review subagent) | **READY** — P0=0, P1=0 (1 P1 found and fixed pre-PR: `role_route_resolution` over-broad gating) |
| §1.9 pre-merge readiness (Checks 1–5) | **PASS** at final HEAD |
| P-018 copilot-review gate | **SATISFIED** (exit 0, 0 unresolved threads across all 10 findings; re-run unconditionally immediately before merge — still SATISFIED, HEAD unchanged) |
| Copilot shadow review | **3 rounds** on PR #276 — round 1: 8 threads; round 2: 2 further threads (surfaced only after round 1's fixes were pushed); round 3: clean (`SATISFIED: PASS`, 0 unresolved) |
| CI (`ci gate`, `detect code changes`, `test`) | all **pass** on final HEAD; mergeState CLEAN / MERGEABLE |
| Full build (`uv build`) | succeeded (`autoharness-1.4.11.tar.gz`, `autoharness-1.4.11-py3-none-any.whl`) |
| Full unittest gate (`PYTHONPATH=src uv run python -m unittest discover -s tests`) | **920 passed, 7 skipped, 0 failed** (final) |
| Review-fix cycles | **3 / 3** — cycle 1 (local adversarial review, pre-PR): `role_route_resolution` gating P1 (`1f722a1`); cycle 2 (hosted Copilot round 1): 8-thread batch (`e3c89b1`); cycle 3 (hosted Copilot round 2): 2-thread batch (`d114eec`). Round 3 found nothing new, so the cycle limit was never exceeded. Fix-CI cycles: 0 / 5 |

## Hosted Copilot Review Rounds (P-018 engaged)

**Round 1** (8 threads, all resolved, fixed in `e3c89b1`):

| # | File | Finding | Resolution |
| --- | --- | --- | --- |
| 1 | `.github/skills/install-harness/SKILL.md` | manifest checksum not refreshed after 104.004-T edit | refreshed checksum + note |
| 2 | `verify_workspace.py` | `yaml.safe_load()` non-dict frontmatter crashed `AttributeError` | `isinstance(frontmatter, dict)` guard, fails closed |
| 3 | `verify_workspace.py` | `model_provider` unconditionally required non-empty, breaking legacy defaults | made optional; only unresolved placeholder flagged |
| 4, 6 | `role-enforcement.instructions.md` (+ `.tmpl`) | precondition contradicted `ROUTING_DEGRADED` propagation step | reworded to "confirm and propagate" instead of "non-degraded" |
| 5, 7 | compound doc + product spec | described superseded (any-`model_routing`) gating condition | corrected to explicit-opt-in condition |
| 8 | `_orchestrator.agent.md.tmpl` | hardcoded vendor strings in "Configuration example" | rewritten to `{{STAGE_FAMILY}}`/etc. placeholders |

**Round 2** (2 threads, all resolved, fixed in `d114eec`):

| # | File | Finding | Resolution |
| --- | --- | --- | --- |
| 1 | `verify_workspace.py` | `orchestrator_invocation_routing_directive` whole-file check satisfiable by summary paragraph alone after deleting real directives | dedicated scoped check requiring `ROUTING_DEGRADED` between first stage/ship mentions |
| 2 | `verify_workspace.py` | non-string `model_family`/`model_provider` silently accepted as valid | require `isinstance(str)`; confirmed config-side path already type-safe |

All 10 threads replied to with the fixing commit SHA before GraphQL
resolution — reply-then-resolve ordering preserved throughout. Full narrative
and reusable lessons captured in
`docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md`
(extended in this closure pass with the round-2 findings).

## Runtime Verification

**Surface**: `runtime_validation.validator_manifest` declares one surface,
`cli`, with a single required probe (`cli-help`).

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | CLI (command) |
| Runtime probe | `uv run autoharness --help` (probe `cli-help`, required) |
| Result | **PASS** — exit 0, CLI help printed (stdout + exit-code evidence), run post-merge on the closure branch cut from synced `main` |
| Preserve-invariant | "The autoharness CLI starts without import, packaging, or option-parsing failures" — HELD |
| Manual checkpoints | none defined |
| Blocked prerequisites | none |
| Release blocker (`The CLI help smoke check fails`) | NOT triggered |
| Verdict | **PASS** (meets `minimum_verdict: PASS`; `surfaces_expected: [cli]`) |

No unsupported automation was fabricated. This shipment's new surfaces
(schema fields, config template, installer variables, Orchestrator invocation
directive, verifier assertions) are exercised by the 920-test unittest suite
and the dogfood `verify-workspace` re-check; the declared validator manifest
only requires the `cli-help` smoke probe, which passed cleanly post-merge.

## Backlog Reconciliation (single-artifact safe-close, P-015 / 097-S)

Safe-close used per-item / single-artifact operations only. The cascade
command `backlogit shipment ship 108-S` was **not** run.

| Item | Final state |
| --- | --- |
| `104.001-T`–`104.009-T` (manifest tasks) | pre-archived automatically by the registry's `done`→archive routing during task execution; manifest-item skip applied (already in `.backlogit/archive/` at closure start) |
| `108-S` (shipment record) | moved to `done`, then archived as a single artifact (`backlogit archive 108-S`) |
| `104-F` (covering feature — **protected set**) | **preserved in `.backlogit/queue/` — NOT cascaded** |

- **Protected set = {`104-F`}**: all 9 tasks under `104-F` are exactly the
  manifest tasks (task-only manifest, per the 097-S contract); no unshipped
  sibling tasks exist under the feature (confirmed by enumerating
  `.backlogit/queue/104*` and `.backlogit/archive/104*` — the 9 archived
  tasks are the complete set, plus an unrelated pre-existing `104-S.md`
  archive entry from a different, older shipment numbering). Baseline gate
  (`104-F` present in queue before mutation, clean `git status -- .backlogit/`),
  verify-after-each (`git status -- .backlogit/` after the shipment archival),
  and the P-007 post re-verify all confirmed `104-F` stayed in queue
  throughout, with the only queue→archive relocation being `108-S.md` (the
  shipment, expected). Closure index resynced (`backlogit sync` → 620
  artifacts indexed).

## Context Compaction (P-020)

- **Status: `done`** (mandatory per-merge invocation; bounded Tier-1
  per-release-unit post-merge floor). Invoked `compact-context` (target:
  all).
- **Memory**: the just-closed release unit's session memory (written fresh
  as `docs/memory/2026-08-01-ship-108-S-104-F-session.md`) is the intended
  candidate under the completed-work rule; this closure pass compacted it to
  `docs/memory/compacted/2026-08-01-108S-104F-compacted.md` and moved the
  verbose original to `docs/archive/memory/2026-08-01-ship-108-S-104-F-session.md`.
- **Docs**: extended the existing compound learning
  (`docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md`)
  with the round-2 Copilot findings and two generalized lessons (whole-file
  substring checks don't prove placement; falsy-check ≠ type-check), and
  corrected the product spec's description of
  `orchestrator_invocation_routing_directive` to match the final scoped-check
  implementation, so future maintainers reading either doc see the shipped
  behavior rather than an intermediate state.
- **Plans**: `docs/plans/2026-07-31-role-based-model-routing-enforcement-plan.md`
  (original, now archived at
  `docs/archive/plans/2026-07-31-role-based-model-routing-enforcement-plan.md`)
  qualified as a candidate — feature `104-F` is complete (all 9 tasks done)
  and the plan carried an appended `## Plan Review` section. Consolidated
  into `docs/plans/2026-07-31-role-based-model-routing-enforcement-decided-plan.md`
  (final T1–T9 decisions, hardening mitigations, and post-harvest Copilot
  findings only — deliberation verbosity dropped); verbose original moved to
  `docs/archive/plans/2026-07-31-role-based-model-routing-enforcement-plan.md`.
  Repointed references: the live/active `104-F` feature record and the
  compound-learning doc now point to the decided-plan; the already-archived
  duplicate feature `103-F` and Stage's dated session memory
  (`docs/archive/memory/2026-07-31-stage-role-model-routing.md`) now point to the
  archived original-plan path (historical fidelity — that is what those
  artifacts referenced at the time they were written/archived).
- **Closure-record thresholds**: no `docs/closure` artifacts other than this
  one crossed their age/count thresholds in this pass; no additional closure
  compaction sweep was due.

## Operational Closure

- **Healthy signals**:
  - Feature PR #276 merged with a merge commit (two parents; P-009
    preserved).
  - Local review READY (P0=0/P1=0); §1.9 all-checks PASS; P-018 SATISFIED
    across 3 hosted Copilot review rounds (10 total findings, all resolved).
  - CI green at every merge gate; CLI smoke probe PASS; full unittest suite
    920 passed / 7 skipped / 0 failed; `uv build` succeeded.
  - Backlog safe-close archived the shipment without the forbidden cascade;
    covering feature `104-F` preserved throughout.
  - Dogfood `verify-workspace` re-checked post-merge on the closure branch:
    same 14 pre-existing unrelated failures as before this shipment, all 5
    P-013.5 targeted checks (`orchestrator_model_routing_fields`,
    `stage_model_routing_fields`, `ship_model_routing_fields`,
    `orchestrator_invocation_routing_directive`, `role_route_resolution`)
    pass.
- **Failure signals to watch**:
  - Any future edit to `_orchestrator.agent.md`'s Model Routing summary or
    Step 1/Step 2 invocation directives should re-run
    `test_verify_workspace_flags_invocation_directive_removed_but_summary_kept`
    to confirm the scoped check still catches directive removal.
  - Any new frontmatter-field verifier check added under P-013.x should use
    `isinstance(x, str)` rather than `is None or == ""` from the start (see
    compound-doc lesson).
  - Recurrence pattern to avoid: re-requesting Copilot review after a fix
    batch can surface *new* findings against the fix itself, not just the
    original diff — budget for at least 2 hosted-review rounds when adding
    new fail-closed verifier checks.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): monitoring — all changes are additive
  (new optional schema fields, new template sections, new verifier checks
  gated on file/config existence) with no destructive migration; rollback =
  revert merge commit `f37e251` (schema fields are optional with
  `additionalProperties: false`, so no data migration is needed either
  direction); validation window = immediate post-merge on 2026-08-02 after
  `main` synced to `f37e251`; owner = Ship agent (closure evidence),
  operator (merge approval — dark-contract pre-authorized for scope `108-S`,
  established by explicit operator clarification that dark factory mode
  includes approval). **Releasability: READY.**
- **Follow-ups**: none blocking. No P2/P3 findings were raised in any of the
  3 Copilot rounds requiring separate backlog tracking (all 10 findings
  across both fix batches were resolved inline as P1-equivalent hardening
  items). Per the Ship role boundary (P-010), no new backlog/stash items
  were created by this session; any future refinement ideas route through
  Stage.

## Dark Factory Scope Completion

Ordered scope was `[107-S, 108-S]` with cursor `last_completed: 107-S`,
`next: 108-S` at session start. `108-S` was the final and only remaining
shipment in this bounded scope. With `108-S` now merged, safe-closed, and
this closure artifact recorded `READY`/`compaction_status: done`, **the full
dark factory scope for this invocation is complete**. No further shipment is
in scope for automatic continuation; any subsequent work requires a new
routing decision.

**Closure verdict: READY.** Merge confirmed (P-009 preserved, two-parent
commit `f37e251`), local review + §1.9 + P-018 gates passed across 3 hosted
Copilot review rounds on PR #276, runtime CLI probe PASS + full suite 920
passed/7 skipped/0 failed, single-artifact safe-close complete with the
protected feature `104-F` intact throughout, and P-020 context compaction is
recorded `done` (see the Context Compaction section above).
