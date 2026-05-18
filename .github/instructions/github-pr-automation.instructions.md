---
description: "GitHub-specific PR automation: Copilot Review polling, comment resolution, and CI check monitoring"
applyTo: '**'
---

# GitHub PR Automation Instructions

These instructions define the GitHub-specific automation protocols for
pull request review and CI check monitoring. They extend the general
`pull-request.instructions.md` and `ci-security.instructions.md` with
concrete GitHub API operations, polling cadences, and comment lifecycle
management.

## Scope

These instructions apply when the target workspace is hosted on GitHub
and agents interact with pull requests via GitHub MCP tools or the `gh`
CLI. Agents MUST follow these protocols for all PR review polling,
comment addressing, and CI status monitoring.

---

## Part 1: Copilot Review Automation

### 1.1 Request Copilot Review

After creating or updating a PR, request a Copilot review:

```text
Tool: mcp_github_request_copilot_review
  owner: softwaresalt
  repo:  autoharness
  pullNumber: <pr_number>
```

If the MCP tool is unavailable, fall back to the CLI:

```bash
gh pr edit <pr_number> --add-reviewer "copilot"
```

### 1.2 Poll for Review Completion

Copilot review typically completes within 2–5 minutes. Use a
back-off polling strategy:

| Attempt | Wait before poll | Cumulative wait |
|---------|-----------------|-----------------|
| 1       | 2 minutes       | 2 min           |
| 2       | 2 minutes       | 4 min           |
| 3       | 3 minutes       | 7 min           |
| 4       | 3 minutes       | 10 min          |
| 5       | 5 minutes       | 15 min          |

**Poll mechanism** — use the MCP tool to read review comments:

```text
Tool: mcp_github_pull_request_read
  owner: softwaresalt
  repo:  autoharness
  pullNumber: <pr_number>
```

Inspect the returned reviews and review comments. Copilot review
comments are identified by the author login `copilot-pull-request-reviewer[bot]`
or similar bot author association.

**Completion signal**: Treat any Copilot-authored review with `state != PENDING`
as complete, including `COMMENTED`, `CHANGES_REQUESTED`, and `APPROVED`.
Review comments attached to a non-`PENDING` review also count as completion.

**Timeout**: If no Copilot review appears after 15 minutes (5 poll
attempts), proceed without it. Log a warning and note in the PR
description that automated review was unavailable.

### 1.3 Categorize Review Comments

For each Copilot review comment, classify it:

| Category | Criteria | Action |
|----------|----------|--------|
| **Valid** | Comment identifies a real issue confirmed by local analysis | Fix the code |
| **Partial** | Comment is partially correct or overly broad | Fix the valid part, reply with explanation |
| **Invalid** | Comment is a false positive or stylistic disagreement | Decline with rationale |
| **Informational** | Comment is a suggestion, not a defect | Acknowledge, apply if low-risk |

### 1.4 Address and Fix Comments

For each comment requiring a fix:

1. **Understand context**: Read the file and surrounding code referenced
   by the comment's `path` and `line`/`start_line` fields.
2. **Apply the fix**: Make the minimal targeted change that resolves the
   issue without introducing scope creep.
3. **Verify locally**: Run the relevant quality gate
   (`# no format check command configured`, `markdownlint "**/*.md"`, `uv run python -m pytest`)
   to confirm the fix doesn't break anything.
4. **Commit**: Use a `fix:` conventional commit referencing the comment
   (e.g., `fix: address copilot review — null check on user input`).

### 1.5 Reply to Addressed Comments

After fixing each comment, reply to the review thread:

```text
Tool: mcp_github_add_reply_to_pull_request_comment
  owner: softwaresalt
  repo:  autoharness
  pullNumber: <pr_number>
  commentId: <comment_id>
  body: "Fixed in <commit_sha>. <brief description of the fix>"
```

For declined comments, reply with the rationale:

```text
body: "Declined — <rationale>. The current implementation <explanation>."
```

For partial comments:

```text
body: "Partially addressed in <commit_sha>. Applied: <what was fixed>.
Not applied: <what was declined and why>."
```

### 1.6 Resolve Review Threads

After replying to a comment, resolve the review thread using the
GitHub GraphQL API. There is no REST endpoint or MCP tool for thread
resolution — use `gh api graphql`:

```bash
gh api graphql -f query='
  mutation ResolveThread($threadId: ID!) {
    resolveReviewThread(input: { threadId: $threadId }) {
      thread { isResolved }
    }
  }
' -f threadId="<thread_node_id>"
```

**Obtaining the thread node ID**: When reading PR review comments via
MCP or REST, each review comment includes a `node_id` field (the
GraphQL global ID). For threaded review comments, query the thread:

```bash
gh api graphql -f query='
  query GetThreads($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            comments(first: 1) {
              nodes { body path line }
            }
          }
        }
      }
    }
  }
' -f owner="softwaresalt" -f repo="autoharness" -F pr=<pr_number>
```

Match threads to addressed comments by `path` and `line`, then resolve
each thread using its `id`.

**Rules**:

* Only resolve threads for comments that have been fixed or explicitly
  declined with a rationale reply.
* Never resolve threads without first posting a reply explaining the
  resolution.
* Never resolve threads authored by human reviewers — only bot-authored
  threads (Copilot, linters, etc.) may be auto-resolved.

### 1.7 Push Fixes and Re-request Review

After all addressable comments are handled:

1. Push the fix commits to the branch.
2. Re-request Copilot review if new code was pushed:

   ```text
   Tool: mcp_github_request_copilot_review
     owner: softwaresalt
     repo:  autoharness
     pullNumber: <pr_number>
   ```

3. Poll again per Section 1.2 to verify the new review is clean.

### 1.8 Stop Conditions for Review Cycles

| Counter | Limit | Action |
|---------|-------|--------|
| Review-fix-push cycles | 3 | Accept remaining comments as backlog follow-ups |
| Same comment re-raised after fix | 2 | Escalate to operator — likely a fundamental disagreement |

**Cycle limits do not clear the merge gate.** When the review-fix cycle
limit is reached with unresolved Copilot threads remaining, the agent
MUST NOT proceed to merge. Unresolved Copilot review threads remain
merge-blocking until resolved or explicitly overridden by the operator.
The cycle limit stops additional automated fixing, not the merge gate.

### 1.9 Pre-Merge Review Readiness Verification (Defense in Depth)

This gate is a **NON-NEGOTIABLE** pre-merge verification that runs
independently of the review-fix loop. Even if the review-fix loop in
§1.7–§1.8 reports completion, this gate re-checks from scratch using
the GitHub GraphQL API. It must pass before any merge is presented as
ready or executed.

This gate applies to **all pull requests** created or merged by the Ship agent:
feature PRs, chore PRs, and post-merge closure PRs. There is no exception for
"small" or "hygiene" PRs. Every merge requires a fresh Copilot review covering
the current HEAD and zero unresolved Copilot threads.

#### 1.9.1 Readiness Query

Run a single GraphQL query to fetch PR head SHA, pending review
requests, completed reviews, review decision, and unresolved threads:

```bash
gh api graphql -f query='
  query PRReviewReadiness($owner: String!, $repo: String!, $pr: Int!, $threadCursor: String) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        headRefOid
        reviewDecision
        reviewRequests(first: 100) {
          nodes {
            requestedReviewer {
              __typename
              ... on Bot  { login }
              ... on User { login }
              ... on Team { name  }
            }
          }
        }
        reviews(last: 50) {
          nodes {
            author { login }
            state
            submittedAt
            commit { oid }
          }
        }
        reviewThreads(first: 100, after: $threadCursor) {
          nodes {
            id
            isResolved
            comments(first: 1) {
              nodes { author { login } body path line }
            }
          }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
  }
' -f owner="softwaresalt" -f repo="autoharness" -F pr=<pr_number> -f threadCursor=""
```

If `pageInfo.hasNextPage` is true, re-run the query with
`-f threadCursor="{endCursor}"` and merge the `reviewThreads.nodes`
results. Repeat until `hasNextPage` is false. **Do not skip
pagination** — a hard gate that misses blocking data is unsafe. If
pagination cannot complete (API error, rate limit), fail closed and
halt rather than declaring readiness.

#### 1.9.2 Bot Identity

The Copilot review bot appears under different login strings depending
on the API surface:

| API context | Login string |
|-------------|-------------|
| GraphQL `Bot.login` (reviews, reviewRequests) | `copilot-pull-request-reviewer` (no `[bot]` suffix) |
| REST `review.user.login` | `copilot-pull-request-reviewer[bot]` |
| REST timeline `requested_reviewer.login` | `Copilot` (display form) |

When matching in GraphQL responses, use `copilot-pull-request-reviewer`
(without `[bot]`). When matching in REST responses, use
`copilot-pull-request-reviewer[bot]`. For review thread comments
returned via GraphQL, the `author.login` field uses the no-suffix form.

#### 1.9.3 Gate Checks

Evaluate three checks in order. All three must pass for merge readiness.

**Check 1 — Review completion (no pending Copilot review)**:

1. Inspect `reviewRequests.nodes[].requestedReviewer`. If any node has
   `login == "copilot-pull-request-reviewer"`, a Copilot review is still
   pending (requested but not yet submitted).
2. If pending: wait using the back-off cadence from §1.2 (max 15 min).
   Re-run the readiness query after each wait interval.
3. If no Copilot review request is pending, proceed to Check 2.

**Check 2 — Review freshness (review covers current HEAD)**:

1. Record `headRefOid` from the query response.
2. Filter `reviews.nodes` to entries where
   `author.login == "copilot-pull-request-reviewer"`.
3. Find the most recent Copilot review by `submittedAt`.
4. Compare its `commit.oid` against `headRefOid`.
   - If they match: the review covers the current code. Proceed to Check 3.
   - If they do not match: the latest Copilot review is stale (applies to
     an older commit). Treat this as equivalent to "review pending" — wait
     and re-poll per Check 1, or halt if the wait budget (15 min) is
     already exhausted.
   - If no Copilot review exists at all: the review was never requested or
     timed out. Log a warning and proceed only if §1.2 timeout already
     applied. Otherwise, request a review per §1.1 and wait.

**Check 3 — Thread resolution (no unresolved Copilot threads)**:

1. From the paginated `reviewThreads.nodes`, filter to threads where:
   - `isResolved == false`, AND
   - the first comment's `author.login == "copilot-pull-request-reviewer"`
2. If zero unresolved Copilot threads: **GATE PASSES**. The PR is ready
   for merge presentation.
3. If any unresolved Copilot threads remain: **GATE FAILS**. List each
   unresolved thread (path, line, comment summary) and halt. Do not
   present the PR as merge-ready.

**Human and other-bot threads**: Human review threads and non-Copilot
bot threads are surfaced in the merge-readiness summary but do not
block this Copilot-specific gate. However, if the repository has branch
protection rules requiring conversation resolution, approved reviews,
or if a human reviewer submitted a `CHANGES_REQUESTED` review, those
constraints may independently block the merge at the GitHub level. The
`reviewDecision` field from the query reflects the overall PR review
decision (`APPROVED`, `CHANGES_REQUESTED`, `REVIEW_REQUIRED`, or null)
and should be reported in the merge-readiness summary.

#### 1.9.4 Terminal States

| Condition | Action |
|-----------|--------|
| Copilot review pending, wait budget (15 min) exhausted | **Halt.** Report to operator. Do not proceed to merge. |
| Copilot review stale (wrong HEAD), wait budget exhausted | **Halt.** Report stale review and current HEAD SHA to operator. |
| Unresolved Copilot threads remain after fix cycles exhausted | **Halt.** List unresolved threads. Do not proceed to merge. |
| No Copilot review exists and §1.2 timeout previously applied | **Warning.** Note in PR summary that Copilot review was unavailable. Gate passes for Copilot-specific checks only. |
| All 3 checks pass | **Ready.** Present PR for merge approval. |

The timeout for a pending Copilot review results in a **halt**, not
"proceed without review." This is the defense-in-depth distinction from
§1.2: the initial poll (§1.2) may allow proceeding after timeout with a
warning during the review-fix loop, but this pre-merge gate does not.
If the operator wants to merge without Copilot review, they must
explicitly override.

### 1.10 Post-Merge Closure PR Copilot Surveillance

When the Ship agent creates a dedicated post-merge closure branch and PR:

1. Request Copilot Review per §1.1 immediately after PR creation.
2. Poll per §1.2 back-off cadence.
3. Apply the full §1.3–§1.7 fix cycle for any comments raised.
4. Run §1.9 readiness gate before presenting the post-merge closure PR for merge.
5. Obtain explicit operator approval before merging the post-merge closure PR.

Post-merge closure PRs are not exempt from the P-014 gate. The operator must
approve each merge individually — approval for the main PR does not carry over
to the post-merge closure PR.

---

## Part 2: CI Check Monitoring

### 2.1 Wait for CI Checks to Start

After pushing commits or creating a PR, CI checks may take 10–30
seconds to initialize. Wait at least 30 seconds before the first
status poll.

### 2.2 Poll CI Check Status

Use the MCP tool to read check run status:

```text
Tool: mcp_github_pull_request_read
  owner: softwaresalt
  repo:  autoharness
  pullNumber: <pr_number>
```

Alternatively, use the `gh` CLI for more granular check-run data:

```bash
gh pr checks <pr_number> --watch --fail-fast
```

Or query check runs directly:

```bash
gh api repos/softwaresalt/autoharness/commits/<head_sha>/check-runs \
  --jq '.check_runs[] | {name, status, conclusion}'
```

### 2.3 Polling Cadence for CI

| Attempt | Wait before poll | Cumulative wait |
|---------|-----------------|-----------------|
| 1       | 30 seconds      | 30 sec          |
| 2       | 1 minute        | 1.5 min         |
| 3       | 2 minutes       | 3.5 min         |
| 4       | 2 minutes       | 5.5 min         |
| 5       | 3 minutes       | 8.5 min         |
| 6       | 3 minutes       | 11.5 min        |
| 7       | 5 minutes       | 16.5 min        |
| 8+      | 5 minutes       | +5 min each     |

**Timeout**: If checks have not completed after 30 minutes, halt
polling and report to the operator. Do not wait indefinitely.

### 2.4 Interpret Check Results

Parse check run results into actionable categories:

| Conclusion | Meaning | Action |
|------------|---------|--------|
| `success` | Check passed | No action needed |
| `failure` | Check failed with actionable errors | Invoke fix-ci protocol |
| `cancelled` | Check was cancelled (often by a newer push) | Re-trigger if needed |
| `timed_out` | Check exceeded its time limit | Investigate resource issues, re-trigger once |
| `action_required` | Check needs manual intervention (e.g., security review) | Report to operator |
| `skipped` | Check was skipped by condition | Verify the skip was expected |
| `neutral` | Informational check | Log and continue |
| `stale` | Check is outdated (superseded by newer commit) | Ignore, newer checks are authoritative |

### 2.5 Extract Failure Details

When a check fails, extract the failure details for diagnosis:

```bash
gh api repos/softwaresalt/autoharness/check-runs/<check_run_id>/annotations \
  --jq '.[] | {path, start_line, end_line, annotation_level, message}'
```

Check annotations provide file paths, line numbers, and error messages
that map directly to code locations — use these for targeted fixes.

For checks without annotations, retrieve the log output:

```bash
gh run view <run_id> --log-failed
```

### 2.6 Fix-Push-Poll Loop

After diagnosing and fixing CI failures:

1. Run the failing checks locally first (per fix-ci skill protocol).
2. Commit and push the fix.
3. Wait for CI to re-trigger (Section 2.1 timing).
4. Poll for new check results (Section 2.3 cadence).
5. Repeat until all checks pass or circuit breaker triggers.

### 2.7 CI Circuit Breakers

| Counter | Limit | Action |
|---------|-------|--------|
| Fix-push-poll iterations | 5 | Halt, leave PR for manual intervention |
| Same check fails 3 times consecutively | 3 | Halt that check's fix loop, report systematic failure |
| Total CI wait time | 30 minutes per cycle | Halt polling, report timeout |

---

## Part 3: Combined Review + CI Workflow

When both Copilot Review and CI checks are active on the same PR, follow
this sequencing:

1. **Push code** → triggers both CI and Copilot Review.
2. **Poll CI status** (Section 2.2) — CI results usually arrive first.
3. **Poll Copilot Review** (Section 1.2) — review typically takes 2–5 min.
4. **Fix CI failures first** — CI failures are typically more mechanical
   and faster to resolve.
5. **Address review comments** — may overlap with CI fixes. If a review
   comment targets the same code as a CI failure, fix once and reference
   both in the commit message.
6. **Push combined fixes** → re-triggers both CI and review.
7. **Resolve addressed threads** (Section 1.6) — only after fixes are
   pushed and replies posted.
8. **Final verification poll** — confirm both CI green and review clean.
9. **Pre-merge readiness gate** (Section 1.9) — run the defense-in-depth
   GraphQL verification to confirm the Copilot review covers the current
   HEAD and no unresolved Copilot threads remain. This gate runs even if
   step 8 reported clean status.

### Interaction with fix-ci Skill

When the pr-lifecycle skill delegates to fix-ci, the fix-ci skill
SHOULD follow the CI polling protocol in Part 2 of this document
rather than ad-hoc polling. The review comment handling in fix-ci
Step 3/Step 6 SHOULD follow Part 1 of this document for GitHub-hosted
repositories.

### Interaction with pr-lifecycle Skill

The pr-lifecycle skill's Step 3 (handle review feedback) SHOULD follow
Part 1 of this document for the complete Copilot Review workflow on
GitHub-hosted repositories. The pr-lifecycle skill's Step 4 (handle CI
failures) SHOULD reference Part 2 for GitHub-specific polling and
failure extraction.

---

## Environment Detection

These instructions apply when the repository is hosted on GitHub.
Agents detect this via:

* Git remote URL containing `github.com`
* Presence of GitHub repository metadata or tooling under `.github/`

For GitHub-hosted repositories:

* Part 1 (PR review polling, Copilot Review handling, and comment
  lifecycle management) applies whenever agents interact with pull
  requests via GitHub MCP tools or the `gh` CLI.
* Part 2 (CI polling and check monitoring) applies when the workspace
  CI platform is GitHub Actions. Agents MAY detect that via:
  * Presence of `.github/workflows/` directory
  * `GitHub Actions` as the CI platform

When the repository is not on GitHub, these instructions do not apply.
Fall back to the generic CI and PR protocols in `ci-security.instructions.md`
and `pull-request.instructions.md`.

Generated by autoharness | Template: github-pr-automation.instructions.md.tmpl
