---
problem_type: gh_api_id_type_confusion
category: github_api
root_cause: GitHub review comment reply API requires the numeric integer comment ID for `in_reply_to`, not the GraphQL node ID string. Thread resolution requires the GraphQL node ID. Using the wrong ID type for each operation fails silently or with a 422.
tags: [github-api, review-comments, graphql, node-id, numeric-id]
shipment: 008-S
date: 2026-05-06
---

# GitHub PR Review: Numeric ID vs GraphQL Node ID

## Problem

Two different GitHub API operations on PR review comments each require a
**different** type of ID, and mixing them causes silent failures or HTTP 422.

## Root Cause

| Operation | Required ID | Example |
|---|---|---|
| Reply to review comment (`POST /pulls/{pr}/comments` with `in_reply_to`) | **Numeric integer** | `3196894537` |
| Resolve review thread (`resolveReviewThread` GraphQL mutation) | **GraphQL node ID** (thread, not comment) | `PRRT_kwDORzpWpM6AGmK7` |

Key confusion points:
* GraphQL comment node IDs start with `PRRC_...`
* GraphQL thread node IDs start with `PRRT_...`
* The REST API comment ID is a plain integer

## Fix

**Step 1 — Get numeric comment IDs for replies:**
```
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '[.[] | {id:.id, node_id:.node_id, body:.body[0:60]}]'
```
Use `.id` (integer) for `in_reply_to`.

**Step 2 — Get thread node IDs for resolution:**
```
gh api graphql -f query='{
  repository(owner:"{owner}",name:"{repo}") {
    pullRequest(number:{pr}) {
      reviewThreads(first:10) {
        nodes { id isResolved comments(first:1) { nodes { body } } }
      }
    }
  }
}'
```
Use thread `.id` (the `PRRT_...` value) in the `resolveReviewThread` mutation.

**Step 3 — Resolve thread:**
```
gh api graphql -f query='mutation {
  resolveReviewThread(input: {threadId: "PRRT_..."}) {
    thread { id isResolved }
  }
}'
```

## Verification

Resolved threads return `"isResolved": true` immediately in the mutation response.
