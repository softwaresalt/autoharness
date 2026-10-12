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

## Status: observed technique, not a configured fallback

`github-pr-automation.instructions.md` section 1.1 permits a wrapper for requesting Copilot
review only when one is explicitly configured, and otherwise requires recording shadow review as
unavailable/advisory. This learning does NOT configure the mutation below as a fallback and does
not change that rule. It was used in 209-S only because the operator's dark-mode brief explicitly
required Ship to request a Copilot review and wait for it. Whether to adopt it as a configured
fallback is an operator policy decision, captured as stash `1AD61D32`.

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

Until stash `1AD61D32` is decided: when no configured wrapper exists and the operator has not
explicitly asked for a Copilot review, follow section 1.1 and record shadow review as
unavailable/advisory. When the operator explicitly requires a Copilot review (as in the 209-S
dark-mode brief), the GraphQL mutation above is a known working technique; record that choice in
the PR body's `Shadow review` line. The `BOT_` node ID is a GitHub identifier for the Copilot
reviewer bot; verify it from the mutation response (`requestedReviewer.login`) rather than
trusting it blindly.
