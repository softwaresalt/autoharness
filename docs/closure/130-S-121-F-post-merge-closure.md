---
shipment: 130-S
feature: 121-F
tasks: [121.001-T, 121.002-T, 121.003-T, 121.004-T, 121.005-T, 121.006-T, 121.007-T, 121.008-T]
feature_pr: 337
closure_pr: 338
merge_commit: ed78afed97391984430de502230e53ae37b620ea
merged_at: "2026-08-14T14:52:44Z"
reviewed_head: 3682d8df10ca8e1537b91a2c747700e11055bcdb
closure_status: READY
compaction_status: degraded
feature_terminal_status: done
feature_archived_status: done
---

# 130-S / 121-F Post-Merge Closure — Plan 2 V1 Remote Control Plane (Observe + Steer)

Shipment `130-S` implemented covering feature `121-F`: the bounded Plan 2 V1
remote control plane over the local Copilot supervisor. `121-F` is a root
feature (no parent) with exactly 8 children — `121.001-T` through
`121.008-T` — all of which are this shipment's manifest, so `121-F` is
fully covered by `130-S` alone (no partial-feature sibling protection
needed at closure). Scope: redacted status/phase/progress/output-stream
tail/journal-tail Observe over an authenticated devtunnel to a loopback-only
Gradio UI, and pause/resume/cancel/request-checkpoint Steer over the same
interface, preserving the four-tier Observe/Steer/Approve/Privileged
authorization model with only Observe/Steer exposed remotely in V1.

## Merge Confirmation

- PR **#337** ("Plan 2 V1 remote control plane — Observe + Steer") merged
  to `main` at `2026-08-14T14:52:44Z` with merge commit
  `ed78afed97391984430de502230e53ae37b620ea`. Confirmed via
  `git show -s --format="%H %P" ed78afed`: two parents
  (`d911d0a980344b6c138c828cc073f56da054903c` prior `main` tip +
  `3682d8df10ca8e1537b91a2c747700e11055bcdb` feature branch HEAD),
  preserving the P-009 merge-commit strategy. Confirmed ancestor of
  `origin/main` (`git fetch origin main` then `git merge-base
  --is-ancestor ed78afed... origin/main` -> exit 0).
- Repo merge-strategy settings (P-009), verified before and after merge:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` — only "Create a merge commit" is possible.
- Reviewed HEAD `3682d8df10ca8e1537b91a2c747700e11055bcdb` matches the
  feature-branch parent of the merge commit exactly.
- **Closure publication gap and remediation**: the shipment-archival and
  closure-artifact mutations were originally only applied in-worktree via
  the backlogit MCP tool and were never committed/pushed after PR #337
  merged, so `origin/main` retained `130-S` as `active`/queued with no
  archived shipment or closure artifact. This was caught by closure
  verification and republished via dedicated closure PR **#338**
  (`chore/130-s-post-merge-closure`, docs/backlog-only, merge-commit
  strategy) rather than amending or force-pushing the already-merged
  feature branch.

## Validator Evidence

| Area | Verdict | Evidence |
|---|---|---|
| Focused Plan 2 harness | PASS | `61 passed, 2 skipped, 9 subtests passed` |
| Authoritative repository suite | PASS | `python -m pytest tests -q`: `1987 passed, 24 skipped, 767 subtests passed` |
| Syntax and whitespace | PASS | `python -m compileall -q src tests`; `git diff --check` |
| Current-head local review (feature PR #337) | PASS | Reviewed HEAD `3682d8df`; `P0=0, P1=0` |
| Copilot review gate (feature PR #337) | PASS | `SATISFIED`; all Copilot-authored threads resolved |
| GitHub Actions (feature PR #337) | PASS | Required checks green before merge |
| GitHub Actions (closure PR #338) | PASS | `ci gate` green; `test` job correctly skipped (docs/backlog-only change) |
| Live Gradio/devtunnel probe | Deferred follow-up | This runner has neither the optional `gradio` package nor a `devtunnel` executable; injectable lifecycle/boundary tests cover these paths instead |

## Invariants to Preserve

- Bind the application to loopback only.
- Use devtunnel authenticated access control as the sole V1 remote identity mechanism.
- Reject mismatched workspace/session bindings and preserve local supervisor/journal authority.
- Dispatch only the closed structured Observe and Steer vocabulary.
- Enforce bounded requests, backpressure/drop-truncate signaling, request-size limits,
  and rate limits.
- Keep Approve and Privileged roles local-only.
- Do not add raw shell execution, browser terminal streaming, or a separate remote
  retention store.

## Pre-Deploy Audits and Deployment Path

The change was released by merge-only deployment to `main`. Before enabling the
remote surface in a deployment environment, confirm that the optional Gradio
dependency is installed at the configured floor (`gradio>=6.20.0`), the
authenticated devtunnel executable is available, and the listener remains
loopback-bound. No corporate-network fallback or additional application-layer
identity mechanism is required by the V1 decision.

## Post-Deploy Checks (Follow-Up — Not a Merge Precondition)

These checks require an environment with the optional Gradio dependency and a
`devtunnel` executable, neither of which is present on this runner. They are
monitoring/validation follow-ups for a deployment environment, not conditions
that gate this shipment's closure — the merged code is fully covered by the
injectable lifecycle and boundary test suite.

1. Start a supervisor session with the remote surface enabled and verify the
   listener binds only to loopback.
2. Establish the authenticated devtunnel and verify Observe responses for status,
   phase, progress, redacted output, and journal tail.
3. Verify pause, resume, cancel, and request-checkpoint dispatch against the
   active session, including duplicate and stale request behavior.
4. Confirm oversized requests and sustained requests above `30 req/min` with
   burst `5` are rejected with structured protocol errors.
5. Confirm tunnel loss and shutdown remove the exposed listener and terminate
   tunnel resources.

## Monitoring and Healthy Signals

Observe local supervisor logs and the authoritative journal for successful
request dispatch, structured rejection counts, redaction behavior, stream
truncation/drop signals, tunnel lifecycle transitions, and cleanup completion.
Healthy operation means all remote commands remain within the closed vocabulary,
no unredacted output is emitted, and the supervisor remains the sole execution
authority.

The initial validation window is the first deployment session plus 30 minutes
of normal operation. `ship` owns the first review; the deployment operator owns
any environment-specific tunnel or dependency remediation.

## Failure Signals and Rollback

Immediately disable the remote surface and terminate the devtunnel if any
unredacted data is observed, a non-loopback listener is detected, an unknown
command is dispatched, workspace/session binding is bypassed, request limits
fail open, or tunnel cleanup leaves an exposed listener.

Rollback is to disable Plan 2 remote configuration and redeploy the prior
`main` revision. Preserve the local journal and supervisor state; do not create
a remote retention store during incident response. If credentials are
compromised, revoke or replace them at the devtunnel issuer and restart the
supervisor under controlled local operation.

## Releasability Evidence

`closure_status: READY`. Merge, review, CI, and automated boundary evidence are
complete for the code that shipped in PR #337. The live Gradio/devtunnel probe
is recorded as a deployment-environment follow-up (see Post-Deploy Checks
above), not as an unmet precondition — it does not alter the locked V1
security scope and does not block this shipment's post-merge closure.

## P-020 Compaction

`compaction_status: degraded`. The mandatory `compact-context` invocation was
attempted at post-merge closure, but the runtime skill was unavailable in this
environment; only the repository template
(`templates/skills/compact-context/SKILL.md.tmpl`) exists. This is recorded as
a non-blocking closure condition per P-020, and no claim is made that
compaction completed.

## Backlog Archival

- Feature `121-F` and its 8 tasks (`121.001-T`–`121.008-T`) plus 2 review
  artifacts (`121.001-R`, `121.002-R`) moved to `done`/`accepted` and archived
  with `commit: ed78afed97391984430de502230e53ae37b620ea`.
- Shipment `130-S` archived with `archived_status: shipped` and the same
  merge commit.
