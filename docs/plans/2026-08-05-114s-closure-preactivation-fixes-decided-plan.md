---
source: docs/plans/2026-08-05-114s-closure-preactivation-fixes-decided-plan.md
title: "114-S Closure Pre-Activation Fixes"
doc_type: decided-plan
status: shipped
created: 2026-08-05
feature: "109-F"
shipment: "115-S"
tasks: ["109.021-T", "109.022-T", "109.023-T"]
supersedes:
  - docs/archive/plans/2026-08-05-114s-closure-preactivation-fixes-plan.md
---

# Decided Plan: 114-S Closure Pre-Activation Fixes

**Outcome:** Reviewed and stabilized as the pre-activation correction set for feature `109-F` / shipment `115-S`. The source plan records multiple re-review addenda ending in **PASS — 0 P0, 0 unresolved P1**, but it does not record a PR number or merge commit, so status remains `reviewed`. The decided scope is to fix three already-merged correctness defects **before** any `115-S` activation task wires the topology gate into a live caller.

**Delivery status (verified against the backlog at compaction time):** shipped — `109-F`, `109.007-T`, `109.008-T`, `109.013-T`, `109.017-T`, `109.018-T`, `109.021-T`, `109.022-T`, `109.023-T`, `114-S`, `115-S` confirmed complete in `.backlogit/`.

## Decisions

- Replace the post-claim gate's illusory internal self-retry with an explicit **retry-required outcome contract**: `CLAIM_NOT_OBSERVED` is a non-zero, non-`blocked` result that tells Ship to reclaim and re-verify externally. The gate stays read-only and never performs the claim itself.
- Tighten `closure_complete()` so completion requires `compaction_status` in `{done, degraded}` **and** either `closure_status: READY` or a non-empty machine-readable `READY_WITH_CONDITIONS` block in which every condition is `satisfied: true` and carries evidence.
- Fix CLI telemetry outcome mapping so `forced` becomes `operator_required`, exit code `1` remains `blocked`, exit code `0` remains `success`, and every other non-zero outcome becomes `failed`.
- Keep the `114-S` audit-log discrepancy out of autoharness scope. It remains external backlogit-owned follow-up work, not part of these fixes.

## Implementation (3 tasks)

- **109.021-T — Gate retry-required contract:** remove the fake second read in `post_claim`, emit `CLAIM_NOT_OBSERVED` for any first-snapshot `queued` + zero-active case, and keep terminal `CLAIM_VERIFY_FAILED` only for snapshots the read-only detector can actually distinguish.
- **109.022-T — CLI telemetry mapping:** repair the `success`-default fall-through in `cli.py` so retry-required and other non-zero error outcomes are reported as failures without regressing the earlier fingerprinting fix.
- **109.023-T — `closure_complete()` releasability enforcement:** require `READY` or fully verified conditions, fail closed on malformed or incomplete frontmatter, and keep the compaction prerequisite intact.

All three fixes gate the activation set in `115-S`: `109.007-T`, `109.008-T`, `109.013-T`, `109.017-T`, and `109.018-T` each depend on these corrections, while `109.023-T` is serialized after `109.021-T` because both edit `topology.py`.

## Key constraints preserved

- The topology gate remains a **pure detector** on the post-claim path: no backlog mutation, no claim side effect, and no breach of P-001/P-016 authority boundaries.
- A first-snapshot `queued` + zero-active state is never classified terminally by the gate. Delayed and failed claims are indistinguishable there, so both surface as retry-required and only Ship's bounded retry consumer can decide exhaustion.
- The four topology invariants are not changed; only the retry outcome contract and closure-completeness predicate are tightened.
- Malformed or incomplete frontmatter fails closed in `closure_complete()`; there is no `{}`-swallow path back to accidental success.
- Updating the `114-S` closure artifact from `READY_WITH_CONDITIONS` to `READY` (or to a fully verified conditions block) is a separate handoff note, not part of these three fix tasks.
- Documentation and test tasks outside the activation path stay intentionally unblocked so parallelism is preserved without making the gate live prematurely.

## Rejected alternatives

- **Keeping the gate's internal second read as a "retry"** — rejected because a second read with no intervening mutation cannot converge anything and only masks the contract gap.
- **Treating `READY_WITH_CONDITIONS` as complete without structured verified evidence** — rejected because it recreates the fail-open releasability defect.
- **Fixing the audit-log discrepancy inside autoharness** — rejected because it is a backlogit-owned issue, not a topology-gate or CLI defect.
- **Creating a separate prerequisite shipment for the fixes** — rejected because the three repairs are small, same-feature, and belong directly ahead of the activation tasks already queued in `115-S`.

## Review findings that changed the plan

- **2026-08-05b re-review:** the plan was tightened so `109.017-T` is the sole consumer of `CLAIM_NOT_OBSERVED`, with a bounded reclaim-and-reverify path, double-claim guard, and terminal exhaustion handling. The gate still detects only; Ship owns the one bounded retry.
- **2026-08-05c re-review:** the source plan removed the unsatisfiable idea that the gate could distinguish delayed from failed claims on the first `queued` + zero-active snapshot. That snapshot now always emits `CLAIM_NOT_OBSERVED`; only a second failure after Ship's bounded retry becomes terminal.
- The final reviewed shape therefore cleanly separates **producer** behavior (`109.021-T`, read-only detection) from **consumer** behavior (`109.017-T`, bounded retry and exhaustion classification).