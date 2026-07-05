---
description: "GitHub-specific PR automation: local-review readiness verification, optional shadow review, and CI check monitoring"
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

## Part 1: Optional Shadow Review Automation

### 1.1 Request Shadow Review

After creating or updating a PR, optionally request a Copilot shadow review during migration:

```text
Tool: mcp_github_request_copilot_review
  owner: softwaresalt
  repo:  autoharness
  pullNumber: <pr_number>
```

If the MCP tool is unavailable, fall back to the CLI:

```bash
gh pr edit <pr_number> --add-reviewer "@copilot"
```

Shadow review is advisory by default. The required dependency for merge
readiness is a current-HEAD local review result.

When `DARK_MODE_ACTIVE` is present under P-017, keep the workflow local-review-first:
the current-HEAD local review readiness record is the authoritative merge gate,
and Copilot/GitHub-hosted review remains optional advisory shadow review unless
the dark-mode activation contract or operator explicitly elevates it. A clean
shadow review cannot compensate for stale or missing local readiness, and shadow
review timeout or unavailability does not block by default.

### 1.2 Poll for Review Completion

Copilot shadow review typically completes within 2–5 minutes. Use a
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

### 1.8 Stop Conditions for Shadow-Review Cycles

| Counter | Limit | Action |
|---------|-------|--------|
| Review-fix-push cycles | 3 | Accept remaining comments as backlog follow-ups |
| Same comment re-raised after fix | 2 | Escalate to operator — likely a fundamental disagreement |

**Cycle limits do not make shadow review merge-blocking by default.** When the
cycle limit is reached, unresolved Copilot comments must be surfaced in the PR
readiness summary and converted into follow-up items or residual-risk notes.
They become merge-blocking only if the operator explicitly elevates shadow
review for the current PR.

### 1.9 Pre-Merge Review Readiness Verification (Defense in Depth)

This gate is a **NON-NEGOTIABLE** pre-merge verification that runs
independently of shadow review. Even if the local review gate reported success
earlier, this step re-checks from scratch that the PR still reflects a
current-HEAD local review result before any merge is presented as ready or
executed.

This gate applies to **all pull requests** created or merged by the Ship agent:
feature PRs, chore PRs, and post-merge closure PRs. There is no exception for
"small" or "hygiene" PRs. Every merge requires a local review readiness record
covering the current HEAD. Copilot shadow review is optional and advisory by
default.

In dark mode, this gate is still local-review-first: unresolved local P0/P1
findings block merge, `READY_WITH_FOLLOWUPS` is allowed only when follow-up item
IDs or explicit residual-risk notes are recorded, and advisory shadow-review
comments are surfaced as follow-ups unless elevated by policy or operator.

#### 1.9.1 Readiness Query

Run a single GraphQL query to fetch PR head SHA, PR body, review decision,
shadow-review state, and review threads:

```bash
gh api graphql -f query='
  query PRReviewReadiness($owner: String!, $repo: String!, $pr: Int!, $threadCursor: String) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        headRefOid
        body
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

#### 1.9.2 Local Readiness Record

The PR description or other operator-visible readiness summary MUST contain a
local review block for the current HEAD:

```markdown
## Local Review Readiness

- Reviewed HEAD: `<sha>`
- Outcome: `READY` | `READY_WITH_FOLLOWUPS` | `BLOCKED`
- Blocking findings: `P0=0, P1=0`
- Follow-ups: `none` | `<item ids or residual-risk notes>`
- Shadow review: `not requested` | `requested` | `clean` | `comments pending`
```

#### 1.9.3 Advisory Bot Identity

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

#### 1.9.4 Gate Checks

Evaluate three checks in order. All three must pass for merge readiness.

**Check 1 — Local review coverage (record covers current HEAD)**:

1. Record `headRefOid` from the query response.
2. Parse the PR `body` for the `## Local Review Readiness` block.
3. Extract `Reviewed HEAD`.
4. If the block is missing or `Reviewed HEAD` does not match `headRefOid`, halt
   and require a fresh local review for the current HEAD.

**Check 2 — Local readiness outcome (no unresolved blocking findings)**:

1. Extract `Outcome` and `Blocking findings` from the local readiness block.
2. If `Outcome` is `BLOCKED`, halt and report the blocking local review.
3. If `Blocking findings` reports any unresolved P0 or P1 findings, halt even
   if the outcome string is malformed.
4. If `Outcome` is `READY` or `READY_WITH_FOLLOWUPS` and blocking findings are
   clear, proceed to Check 3.

**Check 3 — Follow-up handling is explicit**:

1. If `Outcome` is `READY`, the `Follow-ups` field may be `none`.
2. If `Outcome` is `READY_WITH_FOLLOWUPS`, the `Follow-ups` field must list
   follow-up item IDs, queued backlog work, or explicit residual-risk notes.
3. If the field is missing or empty for `READY_WITH_FOLLOWUPS`, halt.
4. Otherwise, **GATE PASSES**.

**Human and shadow-review threads**: Human review threads and advisory Copilot
shadow-review threads are surfaced in the merge-readiness summary but do not
block this local-readiness gate by default. However, if the repository has branch
protection rules requiring conversation resolution, approved reviews,
or if a human reviewer submitted a `CHANGES_REQUESTED` review, those
constraints may independently block the merge at the GitHub level. The
`reviewDecision` field from the query reflects the overall PR review
decision (`APPROVED`, `CHANGES_REQUESTED`, `REVIEW_REQUIRED`, or null)
and should be reported in the merge-readiness summary.

#### 1.9.5 Terminal States

| Condition | Action |
|-----------|--------|
| Local review block missing from PR body | **Halt.** Report that readiness evidence is absent. |
| Local review block references the wrong HEAD SHA | **Halt.** Report stale review and current HEAD SHA to operator. |
| Local readiness outcome is `BLOCKED` or blocking findings remain | **Halt.** List blocking findings. Do not proceed to merge. |
| `READY_WITH_FOLLOWUPS` omits follow-up handling | **Halt.** Report missing follow-up IDs or residual-risk notes. |
| Shadow review unavailable or still pending | **Warning.** Note in PR summary. Shadow review remains advisory unless operator elevated it. |
| All 3 checks pass | **Ready.** Present PR for merge approval. |

Shadow-review timeout does not fail this gate by itself. The required dependency
is local review coverage for the current HEAD.

### 1.10 Post-Merge Closure PR Shadow Review Surveillance

When the Ship agent creates a dedicated post-merge closure branch and PR:

1. Run local review for the closure branch and record the readiness outcome for the current HEAD.
2. Optional Copilot shadow review may run per §1.1–§1.7.
3. Run §1.9 readiness gate before presenting the post-merge closure PR for merge.
4. Obtain explicit operator approval before merging the post-merge closure PR.

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

## Part 3: Combined Local Review + CI Workflow

When optional shadow review and CI checks are active on the same PR, follow
this sequencing:

1. **Push code** → triggers both CI and optional Copilot shadow review.
2. **Poll CI status** (Section 2.2) — CI results usually arrive first.
3. **Poll shadow review** (Section 1.2) — review typically takes 2–5 min.
4. **Fix CI failures first** — CI failures are typically more mechanical
   and faster to resolve.
5. **Address review comments** — may overlap with CI fixes. If a review
   comment targets the same code as a CI failure, fix once and reference
   both in the commit message.
6. **Push combined fixes** → re-triggers both CI and review.
7. **Resolve addressed threads** (Section 1.6) — only after fixes are
   pushed and replies posted.
8. **Final verification poll** — confirm CI is green and shadow review, if requested, is summarized.
9. **Pre-merge readiness gate** (Section 1.9) — run the defense-in-depth
   GraphQL verification to confirm the local review readiness record covers the
   current HEAD and that residual follow-up handling is explicit. This gate runs
   even if step 8 reported clean status.

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
