# Deliberation — CI-blocking checklist Recommended-Action truncation: authorize as a separate auxiliary work unit on PR #373

Date: 2026-08-20
Agent: Stage (planning only — Ship executes)
Stash source: `D71F6283` (high, bug, P-021 C2 `DEFERRED SCOPE EXPANSION`)
Backlogit deliberation: `020-DL`
Feature: `135-F` · Task: `135.001-T` · Shipment: **none (deliberately)**
Related shipment: `143-S` (active) · Covering feature `134-F` · PR #373
Residual-risk record: PR #373 issue comment `5354283673`

## Decision (one line)

**Authorized.** The CI unblocker is approved as a **separate work unit**
(`135-F` / `135.001-T`) under **P-021 C4 forward authorization**, to be executed
by Ship **on the existing branch and PR #373**, with **no** mutation of the
`143-S` shipment manifest and **no** second shipment.

## Problem statement

Shipment `143-S`'s required `test` and downstream `ci gate` checks fail on
`DeployHarnessPs1ChecklistExecutionTests.test_checklist_report_prints_non_interactively`.
Ship classified the defect out of scope under P-021 C1 and captured it as
`D71F6283`, discharging C3 through the threadless residual-risk record on the PR.

Three constraints then interlock into a deadlock:

* **P-021 C4** forbids fixing the expansion inside the cycle that discovered it —
  unconditionally, and explicitly including under explicit operator authorization.
* **P-001** forbids a second in-flight release-unit PR while `143-S` is active.
* `143-S` **cannot merge** while CI is red, so "merge first, fix after" is unreachable.

The question this deliberation answers is narrow: may a C4 forward-authorized
separate work unit execute on the **already-open** branch/PR without becoming a
silent manifest expansion of `143-S`?

## Root cause (confirmed statically, single call site)

`scripts/deploy-harness.ps1:291`

```powershell
$rows | Format-Table -AutoSize | Out-String | Write-Host
```

PowerShell's `Out-String` falls back to an **80-column default** when stdout is
redirected or non-TTY (as under `subprocess` capture in the test harness and under
CI log capture). That clamps `-AutoSize`, and the `RecommendedAction` column is
ellipsis-truncated — `retain-pre…`, `needs-inst…` — before the literals the test
asserts on complete.

The `sh` counterpart (`scripts/deploy-harness.sh` `invoke_checklist`) already emits
fixed-width rows via `printf '%-24s'` and is **not** defective. That asymmetry is
exactly why only the `Ps1` execution class fails, and it makes the `sh` class a
useful control. There is **exactly one** `Format-Table`/`Out-String` call site in
the `ps1`, so the defect surface is precisely bounded.

Pre-existing and unrelated to `143-S`: neither `tests/test_deploy_harness_scripts.py`
nor `scripts/` appear in the diff against merge-base `94898dc7`; it reproduces on
`main` and on a local Windows run. It surfaced only now because `143-S`'s PR is the
first since 2026-08-16 (run `31942166603`) to touch real `.py` test files and so the
first to clear the workflow's "detect code changes" gate.

## Options considered

| # | Option | Verdict |
|---|--------|---------|
| 1 | Expand `143-S` scope; fix inside the active cycle | **Rejected** — P-021 C4 is unconditional and admits no override, including explicit operator authorization. Authorization is a *forward* act, never retroactive. |
| 2 | Create a second shipment now; fix on its own branch/PR | **Rejected/blocked** — P-001 (one in-flight release unit) and P-016 (no parallel branch/worktree). Also does not unblock `143-S`, whose own checks stay red. |
| 3 | Merge `143-S` first, fix afterwards | **Unavailable** — CI is red *because of* this defect; merge gates (P-014/P-018) cannot be satisfied. Hard deadlock. |
| 4 | Weaken/retarget the failing assertion instead of fixing output | **Rejected** — the assertion encodes a real operator-visible contract. Retargeting would green CI while shipping the defect; it is the drift risk recorded in `docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md`. |
| **5** | **Separate auxiliary work unit, own covering feature, executed on the existing branch/PR, not added to the `143-S` manifest** | **CHOSEN** |

## Why Option 5 is compliant, clause by clause

* **P-021 C4 — satisfied.** C4 explicitly permits creating or approving a
  **separate work unit** through the normal intake path: C2 capture → mandatory C6
  Stage deliberation → new approved scope carried by that unit. All three steps
  have been walked (`D71F6283` → this deliberation / `020-DL` → `135-F`/`135.001-T`).
  C4's boundary is on **scope authority**, not on branch or PR identity. C1 states
  that "same PR" is not a sufficient test of scope; symmetrically, a *different* PR
  is not a **necessary** condition of scope separation.
* **P-021 C1 — preserved.** The published classification stands unamended: a
  checklist table-rendering width defect remains a different contract surface from
  authoring P-021 policy carriers. Nothing here re-classifies it as in-scope for `143-S`.
* **P-001 — satisfied.** No second shipment and no second release-unit PR. Exactly
  one release unit (`143-S`) remains in flight. The auxiliary unit is deliberately
  shipment-less.
* **P-016 — satisfied, and this is the deciding constraint.** Same-branch execution
  is the *only* compliant option: creating a branch or worktree for the auxiliary
  unit while `143-S`'s implementation branch is in use is precisely the prohibited
  parallel-implementation state. Same-branch is not a concession; it is what P-016 requires.
* **P-015 — satisfied by construction, and it drives the parenting decision.**
  P-015's protected set for `143-S` closure is `134-F` plus every unshipped
  `134.*-T` sibling outside the manifest, and every protected-set member must remain
  in `queue/` throughout closure. Parenting this work under `134-F` would make it a
  protected-set member, so completing and archiving it before or during `143-S`
  closure would trip the verify-after-each cascade gate as a **false positive** and
  halt closure. Its own covering feature places it outside both the manifest and the
  protected set. **This is why `135-F` exists rather than reusing `134-F`.**
* **P-010 — preserved.** Stage authored intake, deliberation, plan and backlog only.
  No source, template, test or config file was modified; no branch, worktree or
  shipment was created; no test suite was run.

## Not a silent expansion

The relationship is recorded in the open, in five places: a distinct
feature/task pair with its own acceptance criteria; a `related_to` link
`135-F → 134-F`; an `informs` link `135.001-T → 143-S`; this decision record and
`020-DL`; and the existing residual-risk comment on PR #373 that already names
`D71F6283`. An auditor reading PR #373 sees **two clearly labelled, separately
approved scopes**, not one quietly widened one.

## P-021 C5/C6 triage obligations discharged

* **(A) Unconditional duplicate detection — CLEAN SCAN.** All 14 active stash
  entries scanned. Two incidental matches positively excluded as different
  expansions: `47971057` (capability-pack runtime installer TUI) and `3C7AAC71`
  (external backlogit checkpoint-writer context-key drop). `D71F6283` is the sole
  entry for this expansion and is the surviving stable identity. Nothing archived,
  nothing removed. No `DISCOVERY-STATUS` token present.
* **(B) Late-identifier reconciliation — TRIGGERED (`task=N/A`, `review-thread=N/A`),
  PERFORMED, NO LATE IDENTIFIER FOUND.** The Ship-owned residual-risk record was
  located (PR #373 issue comment `5354283673`) and confirmed to cite `D71F6283`.
  All 8 review threads on PR #373 were enumerated; every one targets a P-021 carrier
  surface and none concerns the checklist defect, so **no late-surfacing thread
  exists** and `review-thread: N/A` **stands** as a truthful terminal record. No
  originating task ID surfaced either — the defect was found post-implementation
  during PR CI — so `task: N/A` **stands**. Reconciliation is a no-op on both fields
  and is **non-blocking**; this is not a C3 or C6 shortfall. The entry was updated
  **additively** with forward refs only.

## Open risks (accepted)

1. **Audit visibility.** The PR merge commit will carry two separately approved
   scopes. Mitigated by a distinct commit with the task ID, an explicit
   "Auxiliary scope" section in the PR body, and this record. No policy requires a
   PR to contain only its shipment manifest's scope — but it must be *visible*.
2. **Closure ordering.** `135-F`/`135.001-T` are outside the `143-S` manifest **and**
   outside its P-015 protected set, so `shipment-reconcile`'s safe-close loop will
   neither archive nor validate them. They must be closed on their **own** path after
   the PR #373 merge. Their absence from the manifest must not be read as incomplete closure.
3. **Latent coverage gap — explicitly NOT expanded into.** The workflow's
   "detect code changes" gate skipped the test job for docs/backlog-only merges, which
   is why a defect present on `main` went unobserved from 2026-08-16. Fixing that gate
   is a different contract surface again and needs its own C2 capture and intake.

## Learnings consulted (Stage Step 1.8, confidence medium)

* `docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`
  — the C1 worked discrimination that classifies this as case (b): different surface,
  defer, *even though* same PR.
* `docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md`
  — do not reshape an assertion to accommodate a defect; fix the real contract. This
  is what rejected Option 4.

## Ship may proceed

No safe-sequencing blocker remains. Exact authority and scope are recorded on
`135.001-T`.
