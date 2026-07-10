---
title: Copilot-Review Merge Gate Reference
description: The fail-closed autoharness gate copilot-review CLI, its verdict enum, enforcement modes, bounded timeout, audited --force override, and the P-018 policy that binds it into the merge path
doc_type: reference
source: docs/copilot-review-gate.md
---

> **Navigation**: [README](../README.md) · [Validation Gates Reference](gates-reference.md) · [Primitives](primitives.md) · [Tuning Guide](tuning-guide.md)

## Overview

The **copilot-review merge gate** is a deterministic, non-LLM, exit-code-based
pre-merge check that verifies GitHub Copilot code review has actually completed
for the current PR HEAD **and** that every Copilot-authored review thread is
resolved before a pull request may merge.

Unlike the [validation gates](gates-reference.md) (`autoharness gate check`),
which are **fail-open-to-current** and advisory-by-default, this gate is
deliberately **fail-CLOSED**: when Copilot review is enabled for a PR and its
completion or thread resolution is incomplete or unverifiable, the gate
**BLOCKS** (non-zero exit). A GitHub `--admin` merge does **not** bypass a
copilot-review BLOCK — the block is resolved only by review completion plus
thread resolution, or by an explicit, audited operator `--force`.

This gate closes the class of failure where a merge proceeds while Copilot
review is still in flight, was requested but never completed for the latest
push, or left unresolved review threads. See the accepted design and approved
plan:

* [Copilot-review merge-gate deliberation](decisions/2026-07-09-copilot-review-merge-gate-deliberation.md) (accepted, hardened)
* [Copilot-review merge-gate plan](plans/2026-07-09-copilot-review-merge-gate-plan.md) (Plan Review: APPROVED)

## The `autoharness gate copilot-review` CLI Contract

```bash
autoharness gate copilot-review <pr> --repo <owner/name> \
    [--enforcement auto|required|disabled] [--max-wait <seconds>] \
    [--json] [--force] [--workspace <path>] [--gh <path>]
```

| Flag | Default | Description |
|---|---|---|
| `<pr>` | *required* | Pull request number (positive integer). |
| `--repo <owner/name>` | *required* | GitHub repository slug (validated against `^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$`). |
| `--enforcement <mode>` | `auto` | `auto` \| `required` \| `disabled` — see [Enforcement Modes](#enforcement-modes). |
| `--max-wait <seconds>` | `0` | Bounded window to wait for an engaged reviewer to complete for the current HEAD. `0` means a single-shot check. |
| `--json` | off | Emit the gate result as a machine-readable JSON object. |
| `--force` | off | Operator-only audited override of a BLOCK verdict. Exits 0 and appends to the force audit log. |
| `--workspace`, `-w` | `.` | Workspace root (used to locate the `--force` audit log). |
| `--gh <path>` | `gh` | Path to the `gh` executable. |

The gate queries GitHub via `gh api graphql` for the PR `headRefOid`, Copilot
enablement signals (`reviewRequests` / `reviews`), review completion **for the
current HEAD**, and unresolved Copilot-authored `reviewThreads`. All subprocess
invocation is a fixed argv array executed with `shell=False`; the repo slug and
PR number are validated to reject shell metacharacters before any process runs.

### Enforcement Modes

| Mode | Behavior |
|---|---|
| `auto` (default) | Detect Copilot engagement from per-PR signals. If Copilot was requested or has any review on the PR, the gate is **fail-closed** until review completes for HEAD and threads resolve. If Copilot never engaged, the gate is **not-applicable** (PASS). This preserves "advisory by default" for repositories where Copilot review is not in play. |
| `required` | Forces fail-closed **even before** Copilot is requested. Use when the workspace mandates Copilot review on every PR. |
| `disabled` | The gate is off and always returns `NOT_APPLICABLE` (PASS). |

The mode is normally sourced from `copilot_review.enforcement` in the workspace
profile (`.autoharness/workspace-profile.yaml`; default `auto`). The
[workspace-profile schema](../schemas/workspace-profile.schema.json)
`copilot_review` object defines both `enforcement` and `max_wait_seconds`, and the
harness agent/instruction wiring reads those values when constructing the gate
command.

### Verdict Enum

| Verdict | Result | Meaning |
|---|---|---|
| `SATISFIED` | PASS (exit 0) | Copilot review completed for the current HEAD and all Copilot threads are resolved. |
| `NOT_APPLICABLE` | PASS (exit 0) | Copilot is not in play — `enforcement: disabled`, or `auto` with no Copilot engagement on the PR. |
| `WAITING_FOR_REVIEW` | BLOCK (exit 1) | Copilot is engaged but has not completed a review for the current HEAD. |
| `UNRESOLVED_THREADS` | BLOCK (exit 1) | Review completed but one or more Copilot-authored threads remain unresolved. |
| `REVIEW_TIMEOUT` | BLOCK (exit 1) | `--max-wait` elapsed while still waiting for an engaged reviewer. Logged distinctly, but **still blocks**. |
| `DETECTION_AMBIGUOUS` | BLOCK (exit 1) | Enablement or HEAD could not be determined (e.g., missing `headRefOid`, malformed response, or API reachable but enablement unknown). |
| `VERIFY_FAILED` | BLOCK (exit 1) | The GitHub query itself failed (API unreachable / non-zero `gh`). |

`PASS_VERDICTS = {SATISFIED, NOT_APPLICABLE}`. Every other verdict blocks.

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | PASS — `SATISFIED`, `NOT_APPLICABLE`, or an audited `--force` override. |
| `1` | BLOCK — review incomplete, unresolved threads, timeout, ambiguous, or unverifiable. |
| `2` | Invalid arguments (bad PR number, malformed `--repo`, unknown flag, bad `--enforcement`). |

### Bounded Timeout

`--max-wait <seconds>` gives an engaged reviewer a bounded window to finish for
the current HEAD. A value of `0` (the default) performs a single-shot check and
returns `WAITING_FOR_REVIEW` immediately if the review is not yet complete. When
`--max-wait > 0` and the window elapses without completion, the verdict escalates
to a distinct `REVIEW_TIMEOUT` that is logged and **still blocks** — a timeout is
never treated as a pass. Because each push re-arms Copilot review, the gate is
re-run whenever the branch HEAD advances.

### Audited `--force` Override

`--force` is an **operator-only** control that converts a BLOCK verdict into an
exit-0 pass. It must never be invoked from an agent surface. Every override is
appended to the gitignored audit log:

```text
.autoharness/gates/copilot-review-force-audit.log
```

The audit line records the timestamp, PR, repo, and the verdict that was
overridden. `--force` only writes an audit entry when the underlying verdict was
actually a BLOCK (a forced pass over an already-passing verdict is a no-op).

## P-018: Copilot-Review Completion Merge Gate

**P-018** in the [workflow policy registry](../templates/policies/workflow-policies.md.tmpl)
binds this gate into the harness merge path as a NON-NEGOTIABLE, fail-closed
pre-merge dependency:

* **Precondition** — a PR is about to be presented as merge-ready or merged.
* **Gate point** — `.ship` agent Step 4/5 PR lifecycle, and
  [`github-pr-automation.instructions.md`](../.github/instructions/github-pr-automation.instructions.md)
  §1.9.4 **Check 5**, run before any `gh pr merge` (including `--admin`).
* **Postcondition** — the gate returns a PASS verdict for the current HEAD, or an
  audited operator `--force` is on record.
* **Violation action** — halt, emit `COPILOT_REVIEW_BLOCK`, and record a P-005
  telemetry event. `--admin` and dark-mode admin fallback may **never** bypass a
  `COPILOT_REVIEW_BLOCK`.

The gate is wired into the §1.9 pre-merge readiness verification as an additional
fail-closed check (Check 5), and `COPILOT_REVIEW_BLOCK` is a first-class state in
the dark-mode merge/admin fallback state machine that admin fallback cannot
override.

## Runtime Artifacts

`autoharness gate copilot-review` writes only its audit log, under the same
gitignored runtime directory used by the validation gates:

* `.autoharness/gates/copilot-review-force-audit.log` — append-only `--force`
  override audit.

Running the gate never dirties the working tree.

## References

* [Copilot-review merge-gate deliberation](decisions/2026-07-09-copilot-review-merge-gate-deliberation.md)
* [Copilot-review merge-gate plan](plans/2026-07-09-copilot-review-merge-gate-plan.md)
* [Validation Gates Reference](gates-reference.md)
* [Workflow policy registry template](../templates/policies/workflow-policies.md.tmpl) (P-018)
* [GitHub PR automation instructions](../.github/instructions/github-pr-automation.instructions.md) (§1.1, §1.8, §1.9)
* [`.ship` agent definition](../.github/agents/.ship.agent.md)
* [Workspace-profile JSON Schema](../schemas/workspace-profile.schema.json) (`copilot_review`)
