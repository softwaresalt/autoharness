# Implementation Plan — Preserve full Recommended Action literals in non-interactive checklist output

Date: 2026-08-20
Agent: Stage (planning only — Ship executes)
Stash source: `D71F6283`
Deliberation: `020-DL` · `docs/decisions/2026-08-20-checklist-recommended-action-truncation-ci-unblocker-deliberation.md`
Classification: **bug / CI unblocker (auxiliary work unit, P-021 C4 forward-authorized)**
Feature: `135-F` · Task: `135.001-T` · Shipment: **none** (rides PR #373; see "Sequencing")
Execution branch: `feat/143-s-p-021-bounded-fix-cycle-scope-containment-and-deferred-expansion-capture`
PR: #373 (open, HEAD `fab2ed60220733777087bb23f614bcd6e54e2bd0`)

## Goal

Make the pre-merge-install checklist report print **complete** Recommended Action
literals when stdout is redirected or non-TTY, so the operator-visible report is
truthful in CI and under test capture — and so PR #373's required `test` /
`ci gate` checks can go green without expanding shipment `143-S`'s approved scope.

## Non-goals (do not expand — a finding here needs its own P-021 C2 capture)

* **No change to `scripts/deploy-harness.sh`.** Its `invoke_checklist` already emits
  fixed-width `printf '%-24s'` rows and is not defective. It is the **control** for
  this fix: its tests must pass both before and after. Touching it is scope creep.
* **No change to the workflow's "detect code changes" gate**, even though it is the
  reason this defect went unobserved on `main` since 2026-08-16. Different contract surface.
* **No other checklist behaviour**: interactivity, pack detection, provisioning,
  column set, or the REPORT-ONLY wording.
* **No mutation of the `143-S` shipment manifest**, and no new branch, worktree,
  shipment or PR.

## Root cause

`scripts/deploy-harness.ps1:291` (and its template twin
`templates/scripts/deploy-harness.ps1.tmpl:291`):

```powershell
$rows | Format-Table -AutoSize | Out-String | Write-Host
```

`Out-String` falls back to an 80-column default when stdout is not a console, which
clamps `-AutoSize` and ellipsis-truncates the `RecommendedAction` column before
`retain-present` / `needs-install (deferred)` / `unsupported-undetectable` complete.
Exactly one such call site exists in the script.

## Steps

1. **Confirm RED for the right reason** (AC1). Run the canonical gate filtered to
   `test_checklist_report_prints_non_interactively` and record that
   `DeployHarnessPs1ChecklistExecutionTests` fails on the recommended-action-category
   assertion with a visibly truncated cell in the captured output. Do not edit
   production code before this observation exists.
2. **Strengthen the test, still RED** (AC2). In
   `_ChecklistExecutionMixin.test_checklist_report_prints_non_interactively`, replace
   the weak any-of substring check with assertions that pin the real contract:
   at least one category appears as a **complete literal**, and the rendered checklist
   block contains **no truncation marker** (U+2026, or a trailing `...` in a table cell).
   The strengthened test must still fail for `ps1` before the fix, pass after it, and
   pass for `sh` throughout.
3. **Fix production output** (AC3). Remove the dependence on the redirected-stdout
   default width. Either pass an explicit, generous `-Width` to `Out-String`, or emit
   fixed-width rows mirroring the `sh` `%-24s` contract. **The mechanism must be
   deterministic** — it must not consult `$Host.UI.RawUI.WindowSize`,
   `[Console]::IsOutputRedirected`, or any terminal detection, and must produce
   identical untruncated output with or without a TTY.
4. **Mirror into the template** (AC4). Apply the byte-identical change at
   `templates/scripts/deploy-harness.ps1.tmpl:291`. `DeployHarnessRenderingTests.test_template_renders_to_committed_instance`
   is a hard parity guard: the committed instance must be exactly the template rendered
   with the dogfood variable map. Refresh any harness-manifest checksum for the touched
   paths from the committed blob per the established procedure.
5. **Verify no regression** (AC5, AC6). `scripts/deploy-harness.sh` byte-unchanged;
   `DeployHarnessSh*` and both `*ChecklistPackDetectionTests` classes still pass; full
   canonical gate `$env:PYTHONPATH='src'; python -m unittest discover -s tests` green.
6. **Commit separately and disclose** (AC7). One commit naming `135.001-T` and stating
   that it is a P-021 C4 forward-authorized auxiliary unit, not `143-S` scope. Add an
   "Auxiliary scope" section to PR #373's body naming `135.001-T`, `135-F`, `020-DL`
   and `D71F6283`. Push and confirm `test` / `ci gate` reach SUCCESS.

## Sequencing and dependencies

```text
D71F6283 (C2 capture, Ship)
  └─ 020-DL (C6 deliberation, Stage)          ← this plan's authority
       └─ 135-F
            └─ 135.001-T   ──informs──▶  143-S / PR #373
                  (must land BEFORE 143-S can reach a green-CI merge-ready state)
```

* `135.001-T` is **not** in the `143-S` manifest and **must not** be added to it.
  The relationship is carried by the `informs` link and by this plan, not by membership.
* `135.001-T` must land on PR #373 **before** `143-S`'s merge gates can pass.
* `143-S` closure (`shipment-reconcile` safe-close) archives **only** its manifest
  items; `135-F`/`135.001-T` are outside both the manifest and the P-015 protected set
  and are therefore **invisible** to that loop.

## Closure (do not skip — this unit has no shipment to close it)

After PR #373 merges:

1. Move `135.001-T` → done; track the merge SHA on it.
2. Move `135-F` → done; track the merge SHA.
3. Archive both, on their **own** path — **not** inside the `143-S` closure loop.

Stash `D71F6283` has **already been reconciled and archived by Stage** in this
session (Stage Step 5.6), carrying forward references to `020-DL`, `135-F` and
`135.001-T`. Ship must **not** re-archive or otherwise mutate it (P-021 C5).

## Blast radius

**Low.** One PowerShell formatting call site plus its template twin, and one test
method. No schema, no CLI, no agent/instruction/skill template, no `sh` surface. The
`sh` implementation is an existing, passing reference for the intended output shape.

## Plan hardening (P-006)

**Requires plan hardening: no.** Single call site, single template family, no schema
or CLI-distribution surface, existing test coverage already asserts the contract, and
the correct behaviour is already demonstrated by the `sh` sibling.
