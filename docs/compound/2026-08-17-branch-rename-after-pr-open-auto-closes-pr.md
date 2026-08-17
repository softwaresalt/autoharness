---
title: "Renaming a branch via the GitHub API after its PR is open silently closes the PR"
description: "gh api POST .../branches/{branch}/rename can auto-close an already-open PR instead of retargeting it; fix branch-alias mismatches before pushing/opening the PR, or open a fresh PR rather than renaming."
problem_type: "process-pitfall"
category: "workflow-issues"
component: "ship-agent-pr-lifecycle"
root_cause: "The GitHub branch-rename API fully replaces the ref (old ref deleted, new ref created) rather than performing an in-place rename GitHub's PR machinery can transparently retarget; an open PR whose head branch is deleted this way auto-closes and cannot be reopened."
resolution_type: "workaround"
severity: "medium"
tags:
  - "ship"
  - "pr-lifecycle"
  - "github-api"
  - "pipeline-topology"
  - "branch-naming"
citations:
  - "PR #353 (closed, superseded)"
  - "PR #354 (opened as recovery)"
  - "Shipment 137-S"
---

# Renaming a Branch After PR Open Auto-Closes the PR

## Context

Shipment 137-S's `pipeline-topology (ambient)` CI job reported
`BRANCH_MISMATCH`: the branch `feat/spike-template-docline-conformance` did
not match the gate's expected branch-alias slugs derived from the feature
title. The job was advisory (`continue-on-error`), so `ci gate` still
passed, but the mismatch was a real, fixable gate violation.

## The mistake

To fix the mismatch on an already-open PR (#353), the branch was renamed
server-side via:

```text
gh api -X POST repos/{owner}/{repo}/branches/{old}/rename -f new_name={new}
```

This **did not retarget PR #353** onto the renamed branch. Instead, GitHub
deleted the old ref entirely and created a new one, and the PR — whose head
ref no longer existed — **auto-closed**. A closed PR with a deleted head
branch cannot be reopened (`gh pr reopen` fails with "Could not open the pull
request").

## Recovery

A brand-new PR (#354) had to be opened from the renamed branch, with a body
noting it superseded #353, plus an explanatory comment on #353 linking to
#354. No commits were lost (the renamed branch still pointed at the same
history), but the PR number, review state, and CI history on #353 were
discarded and had to be rebuilt on #354.

## The rule that should have been followed instead

**Get the branch name right before pushing / opening the PR.** If a
branch-alias mismatch is discovered only after a PR is already open:

* Prefer **not renaming the existing branch** at all if the mismatch is only
  advisory (as it was here) — the safer fix is to fix the *rule* (e.g. add
  the actual branch name as an accepted alias) or accept the advisory finding
  and move on.
* If the branch genuinely must be renamed, do it by pushing a **new** branch
  under the correct name (`git push origin HEAD:refs/heads/{new_name}`) and
  opening a **new** PR from it, then closing the old PR with an explanit
  comment — i.e., treat it as the recovery path directly, rather than
  attempting the rename API first and only falling back to a new PR after
  the rename silently destroys the old one.
* Never use the branch-rename API as a "retarget this open PR" operation —
  it is not designed to and does not reliably do that.

## Applicability

Any Ship session that discovers a branch-naming gate mismatch (topology
gate, branch-protection naming rules, CI job naming conventions, etc.)
**after** a PR is already open should apply this rule: push a differently
named branch + new PR, never rename-in-place via the GitHub API.
