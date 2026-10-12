---
title: "Requesting a Copilot review from an automated Ship session: gh reviewer flags fail, GraphQL requestReviews with the bot node ID works"
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
`gh pr edit --add-reviewer` for Copilot and to use a configured fallback. No fallback was
configured, and every `gh`/REST attempt left `reviewRequests` empty, so the P-018 gate would
have blocked on `WAITING_FOR_REVIEW` indefinitely.

## What worked

The GraphQL `requestReviews` mutation with `botIds` and `union: true` registered the
reviewer and the review arrived about four minutes later:

```powershell
$m = 'mutation { requestReviews(input:{pullRequestId:"<PR node id>", botIds:["BOT_kgDOCnlnWA"], union:true}) { pullRequest { reviewRequests(first:5){ nodes { requestedReviewer { __typename ... on Bot { login } } } } } } }'
gh api graphql -f query=$m
```

The PR node ID comes from `gh api graphql` (`repository.pullRequest.id`). The response lists
the requested reviewer as `Bot` / `copilot-pull-request-reviewer`. Re-run the same mutation
after every push to re-arm review for the new HEAD.

## Related PowerShell pitfalls hit in the same loop

* `gh api graphql -f id=$thread.id` interpolates the whole object (`@{id=...; ...}.id`) and
  the mutation fails with `NOT_FOUND`. Copy the ID into a plain string first
  (`$tid = [string]$thread.id`, then `-f "id=$tid"`).
* Reply bodies built from a file with `--field body=@file` kept markdown backticks intact;
  verify one posted body with `gh api repos/<owner>/<repo>/pulls/comments/<id> --jq .body`.
* Every reply posted through the replies endpoint also appears as a `COMMENTED` entry in
  `pulls/<n>/reviews`, authored by the poster. Filter on the Copilot login when counting
  Copilot review rounds.

## Prevention

Treat the GraphQL mutation above as the configured Copilot-request fallback for sessions
without GitHub MCP, and record it in the PR body's `Shadow review` line. The `BOT_` node ID
is a stable GitHub identifier for the Copilot reviewer bot; re-verify it with the
mutation response (`requestedReviewer.login`) rather than trusting it blindly.
