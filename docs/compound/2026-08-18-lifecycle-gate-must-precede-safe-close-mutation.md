---
title: "The lifecycle topology gate must run while the target shipment is still active — before safe-close, not after"
description: "autoharness gate pipeline-topology --phase lifecycle asserts exactly one active shipment matching the target; running safe-close's shipped+archive mutation first leaves zero active shipments and makes the gate unconditionally fail (LIFECYCLE_NO_ACTIVE_SHIPMENT) even though nothing was actually wrong."
problem_type: "process-pitfall"
category: "ship-agent-lifecycle-ordering"
component: "pipeline-topology-gate"
root_cause: "The Ship agent instructions list the lifecycle gate invocation and the shipment-reconcile safe-close invocation as adjacent steps under Closure Tasks, but the gate's own active_shipment_invariant check for phase=lifecycle requires target status active (see src/autoharness/gates/topology.py's _phase_requirement mapping: lifecycle -> (\"active\", \"TARGET_NOT_ACTIVE\", ...)) -- if safe-close (move --status shipped + archive) runs first, the target is no longer active and the gate can never pass for that shipment again."
resolution_type: "workaround"
severity: "medium"
tags:
  - "ship"
  - "pipeline-topology"
  - "shipment-reconcile"
  - "safe-close"
  - "ordering"
citations:
  - "Shipment 140-S post-merge closure"
  - "src/autoharness/gates/topology.py: VALID_PHASES, _phase_requirement, LIFECYCLE_NO_ACTIVE_SHIPMENT"
---

# Lifecycle Topology Gate Must Precede Safe-Close, Not Follow It

## Context

During shipment 140-S's post-merge closure, safe-close was executed (moved
140-S to `shipped`, archived it, verified `archived_status: shipped`)
*before* the mandatory `autoharness gate pipeline-topology --phase lifecycle`
check that the Ship agent instructions require ("Closure Tasks" item 1:
"before invoking `shipment-reconcile` below, run ... `--phase lifecycle`").
Running the gate afterward returned:

```json
{
  "exit_code": 1,
  "blocked": true,
  "token": "LIFECYCLE_NO_ACTIVE_SHIPMENT",
  "message": "LIFECYCLE_NO_ACTIVE_SHIPMENT: expected exactly one active shipment"
}
```

This is not a false positive — it is exactly what the gate is designed to
report. The `lifecycle` phase's `active_shipment_invariant` check requires
the target shipment to currently be `active` (see
`_phase_requirement("lifecycle") == ("active", "TARGET_NOT_ACTIVE", "during
lifecycle execution")`). Once safe-close has already moved the target to
`shipped` and archived it, there are zero active shipments and the gate can
**never** pass for that target again, regardless of whether the underlying
topology was actually fine.

## The rule

Always run `autoharness gate pipeline-topology --phase lifecycle --shipment
<id>` **strictly before** any shipment-status-mutating step in
`shipment-reconcile` (safe-close's `move --status shipped` / `archive`, or
the P-015 cascade `shipment ship` call) — never after. The gate's whole
purpose at this phase is to catch topology problems (multiple active
shipments, wrong branch, worktree issues) *while there is still an active
shipment to check against*; it is not a general-purpose retrospective audit
and has no "the shipment was active a moment ago" leniency.

## Recovery if the ordering is accidentally reversed

If safe-close's mutations have not yet been committed to git, recovery is
possible by re-materializing the pre-close file state from the last commit
that had it (the queue file, before it was archived, is almost always
still recoverable from a recent commit — e.g. the feature-branch merge
commit that claimed/moved the shipment to `active`):

```powershell
# PS7+ accepts -Encoding utf8NoBOM; Windows PowerShell 5.1's -Encoding utf8
# writes a BOM (a stray U+FEFF at the start of the file), which
# `topology._frontmatter`'s `utf-8` reader rejects since it requires `---`
# at byte/character zero. Use the repo-approved BOM-less .NET writer, which
# works identically on both PowerShell 5.1 and 7 (see
# .github/instructions/github-pr-automation.instructions.md:195-198 for the
# same pattern applied to PR reply bodies):
$restoredContent = (git show <last-known-active-commit>:.backlogit/queue/<id>-S.md) -join "`n"
[System.IO.File]::WriteAllText(
  (Join-Path $PWD '.backlogit\queue\<id>-S.md'),
  $restoredContent,
  (New-Object System.Text.UTF8Encoding $false))
Remove-Item .backlogit\archive\<id>-S.md
backlogit sync   # re-index so `shipment get` reflects the restored state
```

Then re-run the lifecycle gate (it should now pass), and only then redo the
safe-close mutation (`move --status shipped` -> verify -> `archive` ->
verify `archived_status: shipped`).

If the mutation has **already been committed and pushed**, do not attempt
this file-surgery recovery — treat it as a genuine `HALT — cascade
detected, revert required` scenario per the `shipment-reconcile` skill and
use `git revert` on the offending commit instead.

## Applicability

Any Ship session performing post-merge closure should treat "run the
lifecycle gate" and "invoke shipment-reconcile safe-close" as a strict
two-step sequence with no reordering, and should double-check gate
invocation order against the agent instructions' numbered list rather than
relying on memory of "which gates I've already run this session" once
several gate invocations have accumulated across pre_claim/post_claim/
lifecycle phases.
