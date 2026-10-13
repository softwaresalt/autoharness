---
title: "Requesting a Copilot review from a Ship session without GitHub MCP: gh reviewer flags did not register it, a GraphQL requestReviews mutation did (observed in 209-S)"
problem_type: tooling-gap
category: workflow
root_cause: "In a session with no GitHub MCP tools, neither `gh pr edit --add-reviewer @copilot`, `--add-reviewer Copilot`, nor the REST requested_reviewers endpoint with `copilot-pull-request-reviewer[bot]` registered a review request on gh 2.81.0 (the first two returned `'' not found`, the REST call silently left reviewRequests empty). Only the GraphQL requestReviews mutation with botIds registered the Copilot reviewer."
tags: [copilot-review, p-018, github-pr-automation, graphql, gh-cli, powershell, resolve-review-thread]
shipment: 209-S
date: 2026-10-12
source: docs/compound/2026-10-12-requesting-copilot-review-via-graphql-bot-id.md
doc_type: learning
---

## Problem

During shipment 209-S (PR #514) the Ship agent had no `mcp_github_request_copilot_review`
tool. `github-pr-automation.instructions.md` section 1.1 says not to rely on
`gh pr edit --add-reviewer` for Copilot and to use a wrapper only when one is explicitly
configured. No wrapper was configured, and every `gh`/REST attempt left `reviewRequests` empty. In
this workspace `copilot_review.enforcement` is not overridden (default `auto`), so with no
requested reviewer and no existing review the P-018 gate would have returned `NOT_APPLICABLE`
rather than blocking. What required a real Copilot review was the operator's dark-mode brief, not
the gate.

## Status: observed technique, not a configured fallback

`github-pr-automation.instructions.md` section 1.1 permits a wrapper for requesting Copilot
review only when one is explicitly configured, and otherwise requires recording shadow review as
unavailable/advisory. This learning does NOT configure the mutation below as a fallback and does
not change that rule. It was used in 209-S only because the operator's dark-mode brief explicitly
required Ship to request a Copilot review and wait for it. Whether to adopt it as a configured
fallback is an operator policy decision, captured as stash `1AD61D32`.

## What was observed

In 209-S the GraphQL `requestReviews` mutation with `botIds` and `union: true` registered the
reviewer and the review arrived about four minutes later. This is the command that was run, recorded
as an observation rather than as guidance:

```powershell
$m = 'mutation { requestReviews(input:{pullRequestId:"<PR node id>", botIds:["BOT_kgDOCnlnWA"], union:true}) { pullRequest { reviewRequests(first:5){ nodes { requestedReviewer { __typename ... on Bot { login } } } } } } }'
gh api graphql -f query=$m
```

The PR node ID came from `gh api graphql` (`repository.pullRequest.id`), and the response listed the
requested reviewer as `Bot` / `copilot-pull-request-reviewer`. The same mutation was issued again after
each push in that session to get a review of the new HEAD.

## Related PowerShell pitfalls hit in the same loop

* `gh api graphql -f id=$thread.id` interpolates the whole object (`@{id=...; ...}.id`) and
  the mutation fails with `NOT_FOUND`. Copy the ID into a plain string first
  (`$tid = [string]$thread.id`, then `-f "id=$tid"`).
* Reply bodies built from a file with `--field body=@file` kept markdown backticks intact;
  verify one posted body with `gh api repos/<owner>/<repo>/pulls/comments/<id> --jq .body`.
* Every reply posted through the replies endpoint also appears as a `COMMENTED` entry in
  `pulls/<n>/reviews`, authored by the poster. Filter on the Copilot login when counting
  Copilot review rounds.

## Rule that stands

Section 1.1 is unchanged by this learning: a Copilot-review request wrapper is used only when it is
explicitly configured, and otherwise shadow review is recorded as unavailable/advisory. Reusing the
mutation above in a later session is not directed here; it requires the operator's decision on stash
`1AD61D32` or an explicit operator instruction for that session. Any session that does use it should
say so in the PR body's `Shadow review` line.
