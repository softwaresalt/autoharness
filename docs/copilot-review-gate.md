---
title: Copilot-Review Merge Gate Reference
description: The fail-closed autoharness gate copilot-review CLI, its verdict enum, enforcement modes, bounded timeout, audited --force override, and the P-018 policy that binds it into the merge path
doc_type: reference
source: docs/copilot-review-gate.md
---

> **Navigation**: [README](../README.md) · [Validation Gates Reference](gates-reference.md) · [Pipeline-Topology Gate Reference](pipeline-topology-gate.md) · [Primitives](primitives.md) · [Tuning Guide](tuning-guide.md)

## Overview

The **copilot-review merge gate** is a deterministic, non-LLM, exit-code-based
pre-merge check that verifies GitHub Copilot code review has actually completed
for the current PR HEAD **and** that every Copilot-authored review thread is
resolved **and** that every threadless finding in a completed Copilot review body
is dispositioned by a trusted PR comment before a pull request may merge (201-F).

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
enablement signals (`reviewRequests` / `reviews`, including each review's
`databaseId` and `body`), review completion **for the current HEAD**, unresolved
Copilot-authored `reviewThreads`, and the PR conversation `comments(last:100)` with
their `authorAssociation` (read for disposition markers; a missing connection, or a comment
entry that is not an object, fails closed on every evaluation; a comment with an
unattributable author or a non-string body or association is ignored and cannot clear a
finding). All subprocess
invocation is a fixed argv array executed with `shell=False`; the repo slug and
PR number are validated to reject shell metacharacters before any process runs. Stdout from `gh` is decoded as strict UTF-8, never with the locale codec, and malformed stdout BLOCKS (`VERIFY_FAILED`). Stderr is diagnostic only.

### Output

The human-readable output begins with `Copilot-review gate — <VERDICT>: PASS` or `BLOCK`
and the verdict message. It adds these lines when they apply:

* `  unresolved Copilot threads: <count>`, when threads are open.
* `  undispositioned Copilot review-body findings in reviews: <ids>` and the marker hint,
  only for `UNDISPOSITIONED_BODY_FINDINGS`.
* `  --force override recorded: <path>`, after an audited `--force`.
* `  advisory: <message>`, for an advisory (see [Review-Body Findings](#review-body-findings)).

`--json` emits the result object. It includes `verdict`, `enforcement`,
`head_ref_oid`, `unresolved_thread_ids`, `undispositioned_body_finding_review_ids`,
`advisory`, `rounds`, `forced`, `blocked`, `exit_code`, and `message`. It adds
`force_audit_log` when an audited `--force` applies.

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
| `SATISFIED` | PASS (exit 0) | Copilot review completed for the current HEAD, all Copilot threads are resolved, and every Copilot review-body finding is dispositioned (or there are none). |
| `NOT_APPLICABLE` | PASS (exit 0) | Copilot is not in play — `enforcement: disabled`, or `auto` with no Copilot engagement on the PR. |
| `WAITING_FOR_REVIEW` | BLOCK (exit 1) | Copilot is engaged but has not completed a review for the current HEAD. |
| `UNRESOLVED_THREADS` | BLOCK (exit 1) | Review completed but one or more Copilot-authored threads remain unresolved. |
| `UNDISPOSITIONED_BODY_FINDINGS` | BLOCK (exit 1) | A completed Copilot review (any round) carries threadless body findings, and no trusted PR comment carries `Copilot-Review-Body-Disposition: <review databaseId>`. See [Review-Body Findings](#review-body-findings). |
| `REVIEW_TIMEOUT` | BLOCK (exit 1) | `--max-wait` elapsed while still waiting for an engaged reviewer. Logged distinctly, but **still blocks**. |
| `DETECTION_AMBIGUOUS` | BLOCK (exit 1) | Enablement or HEAD could not be determined (e.g., missing `headRefOid`, malformed response, or API reachable but enablement unknown), or a review-body disposition cannot be confirmed (for example a truncated PR comments page while findings remain undispositioned). |
| `VERIFY_FAILED` | BLOCK (exit 1) | The GitHub query itself failed (API unreachable / non-zero `gh`). |

`PASS_VERDICTS = {SATISFIED, NOT_APPLICABLE}`. Every other verdict blocks.

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | PASS — `SATISFIED`, `NOT_APPLICABLE`, or an audited `--force` override. |
| `1` | BLOCK — review incomplete, unresolved threads, undispositioned review-body findings, timeout, ambiguous, or unverifiable. |
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

### Review-Body Findings

Copilot can report a valid finding **only** in its review body, with no inline
comment and no review thread. The body shows it as a `Previously missed (N)` or
`Suppressed comments (N)` section, or as open findings with no `#discussion_r`
anchor. Before 201-F the gate ignored bodies. PR #506 rounds 2 to 5 each carried
one such finding under a `0 open findings` headline, and the gate returned
`SATISFIED` each time.

**Detector rules** (`detect_body_findings`, pure, standard library `re`):

* `count = max(S, PM) + U`.
* `S` is the largest `Suppressed comments (N)` count and `PM` is the largest
  `Previously missed (N)` count (the maximum over occurrences keeps the detector on
  the fail-closed side).
* `U = max(0, N_open - A)`. Each `N open finding(s)` headline gives `N_open` and its own
  span. `A` is the number of distinct `#discussion_r`   IDs on list-marker lines, or on indented
    lines that lead with the link,     inside that span, so a prose link does not count. `U` is the largest value over all headlines.
* **Span ends:** a span ends at the next headline-shaped header: a `<summary>` headline (with or without `<strong>`), a `### ` line, or a bold count or section headline. A bold location label such as
  `**src/a.py:12**` does not end a span. Nested `<summary><picture>` per-finding blocks do
  not end a span.
* **Fenced code:** a closed fence starting at column 0 is excluded, with a closer of the
  same character at least as long as the opener, indented 0 to 3 spaces (CommonMark rules).
    An indented opener is
  not excluded, so a headline inside it still counts (fail-closed). An unclosed opener
  keeps the rest of the body. CRLF is normalized first.
* **Indentation:** a headline indented by any amount still counts (fail-closed).
* **Not counted:** `resolved since last review`, `What changed in this PR`, the
  overview risk line (for example `Needs a closer look`), and prose that merely
  mentions a headline phrase. Counts are read only at structural positions: inside a
  `<summary>` header, on a `### ` heading line, or on a bold line.

**Review scope:** every completed Copilot review (`COMMENTED`, `APPROVED`, or
`CHANGES_REQUESTED`) in any round, on any HEAD. `DISMISSED` and `PENDING` reviews are
excluded.

**Disposition marker contract:** a PR conversation comment, authored by an account
whose `authorAssociation` is `OWNER`, `MEMBER`, or `COLLABORATOR`, that contains the
exact line `Copilot-Review-Body-Disposition: <review databaseId>` on its own line.
Use one line per review; one comment may carry several lines. A line with trailing
text (for example `... 101 later`) does not count. Comments from the Copilot bot,
or from any other association (`NONE`, `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or a
missing association), are ignored.

*Trust rationale:* on a public repository any user can post a PR comment. The
`OWNER`, `MEMBER`, and `COLLABORATOR` associations exclude ordinary outside
commenters, so they cannot clear a P-018 BLOCK, and the Copilot bot cannot clear its
own findings. This is an **association** check, not a write-permission check:
`COLLABORATOR` can include read-only outside collaborators, and `MEMBER` can include
members with read access. A write-permission check on the marker author is tracked as
a follow-up.

**Fail-closed rules:**

* An absent, null, or non-string review body, a body finding without an integer
  `databaseId`, a digit run too large to count, or a missing `comments` connection
  gives `DETECTION_AMBIGUOUS`.
* A comment with an unreadable author (for example a deleted account) is ignored. It
  cannot clear a disposition, so it does not make the gate ambiguous.
* A truncated `comments` connection (`hasPreviousPage`) is not ambiguous by itself.
  It becomes `DETECTION_AMBIGUOUS` only when undispositioned findings remain, because
  the marker could sit on an unfetched page. The remedy is to post a fresh disposition
  comment for each affected review, so the marker falls within the newest 100 comments.
* The new check runs only after `completed_for_head()`. A `REVIEW_TIMEOUT` or
  `WAITING_FOR_REVIEW` state is never treated as clean.

**Known limitation:** the detector matches the observed Copilot formats
(`ccr-overview-v2` and the legacy `Suppressed comments` layout). A format drift can
cause a miss. The instruction layer
([`github-pr-automation.instructions.md`](../.github/instructions/github-pr-automation.instructions.md)
§1.6.1) is the backstop, and the `advisory` field reports an unrecognized overview
version.

**`advisory` field (OQ-1):** a list of strings in `--json` output, and `  advisory:`
lines in human output. Advisories never change the verdict. The current advisory is
`unrecognized ccr-overview version v<N>: review-body detection may be incomplete;
read review bodies manually`.

**Rollout (OQ-2):** an open PR that already handled body findings must post a
disposition comment for each affected review before the gate passes. Do not post
markers on historical or merged PRs. The gate does not re-check them.

## P-018: Copilot-Review Completion Merge Gate

**P-018** in the [workflow policy registry](../templates/policies/workflow-policies.md.tmpl)
binds this gate into the harness merge path as a NON-NEGOTIABLE, fail-closed
pre-merge dependency:

* **Precondition** — a PR is about to be presented as merge-ready or merged.
* **Gate point** — `_ship` agent Step 4/5 PR lifecycle, and
  [`github-pr-automation.instructions.md`](../.github/instructions/github-pr-automation.instructions.md)
  §1.9.4 **Check 5**, run before any `gh pr merge` (including `--admin`).
* **Postcondition** — the gate returns a PASS verdict for the current HEAD (every
  Copilot-authored thread resolved and every threadless Copilot review-body finding
  dispositioned by a trusted marker comment), or an audited operator `--force` is on
  record.
* **Violation action** — halt, record a P-018 violation through P-005 telemetry, and do not
  merge.   Ship Step 4 (the P-018 gate item) names the `COPILOT_REVIEW_BLOCK`   event. `--admin` and dark-mode admin fallback may **never** bypass a BLOCK verdict.

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
* [Pipeline-Topology Gate Reference](pipeline-topology-gate.md) — the sibling deterministic shipment/worktree topology gate (P-001/P-016)
* [Workflow policy registry template](../templates/policies/workflow-policies.md.tmpl) (P-018)
* [GitHub PR automation instructions](../.github/instructions/github-pr-automation.instructions.md) (§1.1, §1.8, §1.9)
* [`_ship` agent definition](../.github/agents/_ship.agent.md)
* [Workspace-profile JSON Schema](../schemas/workspace-profile.schema.json) (`copilot_review`)
