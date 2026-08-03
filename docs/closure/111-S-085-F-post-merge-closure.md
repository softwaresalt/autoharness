---
shipment: 111-S
feature: 085-F
tasks: [085.001-T, 085.002-T, 085.003-T, 085.004-T, 085.005-T, 085.006-T, 085.007-T, 085.008-T]
feature_pr: 289
merge_commit: 806f2fc23872fb073051c11c5d1c18d9836c3cca
merged_at: "2026-08-03T20:16:24Z"
reviewed_head: 938c178084282a5d8a89d16960e10352a26b05e1
closure_status: READY
compaction_status: done
---

# 111-S / 085-F Post-Merge Closure — Structural-Navigation Benchmark Suite

Shipment `111-S` (feature `085-F`) ships the deterministic-core-first
structural-navigation benchmark suite: a new `src/autoharness/eval/benchmark/`
package (scenario corpus + loader, run harness with isolated telemetry sink,
correctness scorer, telemetry A/B delta adapter, reproducibility controls,
honest reporting renderer), 98 new targeted unit tests plus full-suite
verification, and a methodology/interpretation design doc. Purely additive:
no shipped telemetry/eval/CLI/schema file was modified; live-run mode is
explicitly deferred/out of scope. All 8 manifest tasks (`085.001-T`–
`085.008-T`) executed under TDD in the plan's dependency order.

## Merge Confirmation

- PR **#289** merged to `main` at `2026-08-03T20:16:24Z` with merge commit
  `806f2fc23872fb073051c11c5d1c18d9836c3cca`.
- The merge commit has **two parents**
  (`f4349899b9cc83913f43bfb5873c95ac796d716b` base +
  `938c178084282a5d8a89d16960e10352a26b05e1` feature HEAD), preserving the
  P-009 merge-commit strategy. Repo settings verified pre-merge:
  `mergeCommitAllowed: true`, `squashMergeAllowed: false`,
  `rebaseMergeAllowed: false` — only "Create a merge commit" was possible.
- Merge SHA confirmed as ancestor of `origin/main`
  (`git merge-base --is-ancestor` exit 0); local `main` fast-forwarded to
  `806f2fc`. Closure work was cut from synced `main` on branch
  `post-merge/structural-navigation-benchmark-suite`.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Reviewed HEAD | `938c178084282a5d8a89d16960e10352a26b05e1` (== PR HEAD at merge) |
| Local adversarial review (multi-persona, prior session) | 0 P0. 1 P1 (missing malformed-quality-label fail-closed test coverage) fixed in `0e29d14` (4 new tests); 1 P3 (stale docstring path) also fixed. Re-verified READY. |
| Copilot review (6 rounds, prior session, HEAD progression through `938c178`) | 15 findings total across R1–R6, all fixed and threads resolved via GraphQL — scenario-id collision, unavailable-not-zero label-trust ordering, reused-sink rejection, neutral-class rationale (x2), precision-only regression detection, estimated-quality label gap, sink workspace-root containment (raised twice, fully enforced in R3), H6 same-run-identity validation (R4), H6 hardening via unique per-run `run_id` (R5), mandatory isolated/enabled telemetry-config enforcement + every-repeat correctness scoring (R6). |
| P-018 copilot-review gate | **SATISFIED: PASS** at HEAD `938c178` — re-run immediately before merge in this session, unchanged. 0 unresolved Copilot threads. |
| §1.9 pre-merge readiness (Checks 1–5) | PASS at HEAD `938c178`; PR body's Local Review Readiness block matched this HEAD. |
| CI (`detect code changes`, `test`, `ci gate`) | all **SUCCESS** at HEAD `938c178`; `mergeStateStatus: CLEAN`, `mergeable: MERGEABLE`. |
| Full canonical unittest gate (`PYTHONPATH=src python -m unittest discover -s tests`) | **1065 passed, 7 skipped, 0 failed** at HEAD `938c178` (re-verified per PR body; no regressions). |
| New benchmark suite (targeted) | 98/98 pass at PR open; reporting+harness+controls re-verified 58/58 at final HEAD. |
| Full local build (`uv build`) | succeeded (sdist + wheel) at prior HEAD; no build-affecting change at final HEAD beyond two pure-library modules (R6). `uv run autoharness --help` CLI smoke re-run and passed at HEAD `938c178`. |
| Review-fix cycles | local review-fix: 1 cycle (well under 3). Copilot review-comment cycles: 6 rounds resolved across the PR's full history (bounded, all actionable, no unsafe/timeout exits). Fix-CI cycles: 0/5. |
| Repo merge-strategy settings (P-009) | `mergeCommitAllowed: true`, `squashMergeAllowed: false`, `rebaseMergeAllowed: false` — verified again at merge time in this session. |
| Worktree/PR topology | single open PR (#289) confirmed at merge time; single worktree, no parallel worktree violations (P-016). |

Operator merge approval (`2026-08-03T20:15:19Z`, scoped to PR #289 only —
does not transfer to any post-merge closure PR) was recorded in a PR
comment together with this session's own defense-in-depth re-verification,
immediately before the merge command was issued. No admin fallback was
authorized or used; the normal merge path (`gh pr merge 289 --merge`)
succeeded directly.

## Runtime Verification

**Surface**: `runtime_validation.validator_manifest` declares one surface,
`cli`, with a single required probe (`cli-help`). This shipment is a
purely-additive library package (`src/autoharness/eval/benchmark/`) with no
new or changed CLI/runtime surface of its own, so the CLI smoke probe is the
applicable — and only required — runtime check, matching the PR body's own
Runtime Verification section.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | CLI (command) |
| Runtime probe | `uv run autoharness --help` (probe `cli-help`, required) |
| Result | **PASS** — exit 0, CLI help printed, re-run post-merge on the closure branch cut from synced `main` |
| Preserve-invariant | "The autoharness CLI starts without import, packaging, or option-parsing failures" — HELD |
| Manual checkpoints | none defined |
| Blocked prerequisites | none |
| Release blocker (`The CLI help smoke check fails`) | NOT triggered |
| Verdict | **PASS** (meets `minimum_verdict: PASS`; `surfaces_expected: [cli]`) |

No unsupported automation was fabricated. The new benchmark package's own
surfaces are exercised entirely by its 98 new unit tests plus the canonical
suite (1065 passed / 7 skipped / 0 failed), not by a runtime-validator probe
(the package has no CLI/service entrypoint of its own).

## Backlog Reconciliation (single-artifact safe-close, P-015 / 097-S)

Safe-close used per-item / single-artifact operations only. The cascade
command `backlogit shipment ship 111-S` was **not** run.

| Item | Final state |
| --- | --- |
| 8 manifest tasks (`085.001-T`–`085.008-T`) | already archived (`status: done`) as part of the merged feature branch's own commit history at merge time — no re-archival needed; verified all 8 carry `status: done` in `.backlogit/archive/`. |
| `111-S` (shipment record) | explicitly archived as a single artifact via `backlogit archive 111-S` on the post-merge closure branch. |
| `085-F` (covering feature) | moved to `done` via `backlogit move 085-F --status done`, which (per this CLI's terminal-status side effect) relocated the file to `.backlogit/archive/085-F.md`. Confirmed via enumeration of `.backlogit/queue/085*` and `.backlogit/archive/085*` that the shipment manifest is this feature's entire task set (no other siblings), so terminal closure of `085-F` alongside `111-S` is within this shipment's explicit scope. |

- Baseline gate: `git status --short -- .backlogit/` clean before mutation;
  `085-F` present in `.backlogit/queue/` before any archival step.
- Verify-after-each: `git status --short -- .backlogit/` checked after both
  the `111-S` archive and the `085-F` move/archive — only `085-F.md` and
  `111-S.md` (plus their log files) changed at any point; no other
  `.backlogit/` path (other backlog items, stash, deliberations) was
  touched.
- **Process correction**: the `111-S` archival was first (mistakenly)
  committed directly on local `main` before the post-merge closure branch
  existed. Caught before pushing; recovered via `git reset --hard` to the
  merge commit (which also safely undid the premature file-move side
  effect) and redone correctly on
  `post-merge/structural-navigation-benchmark-suite`. See
  `docs/compound/2026-08-03-post-merge-closure-branch-before-first-commit.md`.
- Closure index resync: `backlogit sync` run after all archival mutations —
  `Indexed 646 artifacts` (`CLOSURE_INDEX_SYNC_OK`).

## Context Compaction (P-020)

- **Status: `done`** (mandatory per-merge invocation; bounded Tier-1
  per-release-unit post-merge floor).
- **Memory**: wrote
  `docs/memory/2026-08-03-ship-111-S-085-F-session.md`, then compacted it
  to `docs/memory/compacted/2026-08-03-111S-085F-compacted.md` and moved the
  verbose original to
  `docs/archive/memory/2026-08-03-ship-111-S-085-F-session.md`.
- **Docs**: a new compound learning,
  `docs/compound/2026-08-03-post-merge-closure-branch-before-first-commit.md`,
  records the branch-before-first-commit ordering lesson from this
  session's own process correction.

## Operational Closure

- **Healthy signals**:
  - PR #289 merged with a merge commit (two parents; P-009 preserved).
  - Local review READY_WITH_FOLLOWUPS (P0=0/P1=0); 6 rounds of Copilot
    review, all 15 findings fixed and threads resolved; §1.9 and P-018 both
    PASS/SATISFIED at final HEAD, re-verified unconditionally immediately
    before merge.
  - CI green at every merge gate; CLI smoke probe PASS; full canonical
    unittest gate 1065 passed / 7 skipped / 0 failed (no regressions; 98
    new benchmark-suite tests added).
  - Backlog safe-close archived the shipment and covering feature
    individually without the forbidden cascade command; 8 manifest tasks
    were already correctly archived from the feature branch's own history.
- **Failure signals to watch**:
  - None new. A local process error (committing archival work directly on
    `main` before creating the closure branch) occurred but was caught
    before any push and fully corrected — no artifact ever reached
    `origin/main` in a bad state.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): monitoring — the change is purely
  additive (a new library package, no shipped file modified, no
  schema/data migration); rollback = revert merge commit `806f2fc` (safe,
  no migration in either direction; live-run mode remains explicitly
  deferred/out of scope so no partially-wired runtime surface exists);
  validation window = immediate post-merge on 2026-08-03 after `main`
  synced to `806f2fc`; owner = Ship agent (closure evidence), operator
  (merge approval for PR #289, explicit and separately required for any
  post-merge closure PR per P-014).
  **Releasability: READY.**
- **Follow-ups** (carried from the PR's own Local Review Readiness
  follow-ups, non-blocking, no exploit path identified):
  - `controls._outcome_classification()`'s neutral-collapse for an
    already-`negative`-class degraded scenario has confusing but harmless
    semantics (correctness gating is independently computed via
    `scorer.regressed()`); untested combination since the shipped corpus
    has no negative+degraded scenario. Low residual risk; worth a
    clarifying test if the corpus is ever extended with such a scenario.
  - A caller-supplied `ArmExecutor` that legitimately varies correctness by
    `repeat_index` remains explicitly out of scope/deferred (live-run
    mode); `RepeatCorrectnessVarianceError` refuses such a run loudly
    rather than silently scoring only repeat 0 — a fail-closed boundary,
    not an unhandled gap.

**Closure verdict: READY.** Merge confirmed (P-009 preserved, two-parent
commit `806f2fc`), local review + 6 rounds of Copilot review (15/15
findings fixed) + §1.9 + P-018 gates passed at final HEAD `938c178`,
runtime CLI probe PASS + full canonical unittest gate (1065 passed / 7
skipped / 0 failed), single-artifact safe-close complete for the shipment
and the covering feature (8 manifest tasks already correctly archived, no
cascade corruption, no scope leakage into any other backlog item), and
P-020 context compaction is recorded `done` (see Context Compaction section
above).

**Remaining approval blocker**: this post-merge closure PR requires its own
**separate, explicit operator approval** before merge (P-014 — the PR #289
approval does not carry over). No merge of the closure PR will be attempted
without it.
