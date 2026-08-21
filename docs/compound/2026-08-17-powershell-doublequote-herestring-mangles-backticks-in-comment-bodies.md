---
title: "PowerShell double-quoted here-strings silently mangle backticks in GitHub comment/PR bodies"
description: "@\"...\"@ here-strings process backtick escape sequences (e.g. `t -> tab, `v -> vertical tab), corrupting any Markdown inline-code backticks written into a file this way before it is ever sent to gh api; always use single-quoted @'...'@ here-strings for literal body text."
problem_type: "process-pitfall"
category: "tooling-issues"
component: "ship-agent-github-automation"
root_cause: "PowerShell double-quoted strings and here-strings (\"...\" and @\"...\"@) treat the backtick as the escape character, so literal Markdown backticks in a comment/PR body (e.g. `` `test` ``, `` `v1.9.0` ``) get interpreted as escape sequences (`t -> TAB, `v -> VT) before the text is ever written to disk or sent to an API."
resolution_type: "workaround"
severity: "low"
tags:
  - "ship"
  - "github-pr-automation"
  - "powershell"
  - "shell-safety"
  - "copilot-review"
citations:
  - "PR #354 comment 3799056616 (posted mangled, then corrected via PATCH)"
  - "Shipment 137-S"
source: docs/compound/2026-08-17-powershell-doublequote-herestring-mangles-backticks-in-comment-bodies.md
doc_type: learning
---

# PowerShell Double-Quoted Here-Strings Mangle Backticks in Comment Bodies

## Context

While replying to a Copilot review comment on PR #354, the reply body was
built with a double-quoted here-string:

```powershell
$body = @"
Fixed in b145578c: the `test` job now downloads ... pinned `v1.9.0` ...
"@
```

The resulting GitHub comment showed corrupted text: `` `test` `` became a
literal tab character, `` `v1.9.0` `` became a vertical-tab control character
followed by stray text, and other backtick-quoted identifiers were similarly
mangled. This happened even though the value was later passed through
`gh api ... -f body="$(Get-Content -Raw file)"` — the corruption occurred at
the point the here-string itself was evaluated (writing to the file), not at
the `gh api` call.

## The rule

In PowerShell, **only single-quoted here-strings preserve backticks
literally**:

```powershell
# WRONG — backtick is the PowerShell escape character inside "..."
$body = @"
Fixed in `commit_sha`: uses `some_flag` ...
"@

# RIGHT — single-quoted here-string, no escape processing
$body = @'
Fixed in `commit_sha`: uses `some_flag` ...
'@
```

Any text destined for a Markdown-formatted GitHub artifact (PR body, review
comment, issue comment) that contains inline-code backticks **must** be
built with `@'...'@`, never `@"..."@`, and never a bare double-quoted `"..."`
string if it contains backticks. This applies regardless of whether the text
is written straight to `gh api`/`gh pr edit --body-file` or piped through
intermediate variables — the mangling happens the moment PowerShell parses
the double-quoted literal, before any downstream tool sees it.

## Detection and recovery

If a mangled comment is discovered after posting (e.g. by re-fetching it via
`gh api .../pulls/{pr}/comments --jq '.[].body'` and seeing control
characters or missing backticks), it can be corrected in place without
creating a duplicate: build a JSON payload file (`{"body": "..."}`) from a
correctly single-quoted here-string and `PATCH` the existing comment:

```powershell
gh api -X PATCH repos/{owner}/{repo}/pulls/comments/{comment_id} --input payload.json
```

## Applicability

Any Ship (or Stage) session on Windows/PowerShell building file-backed
comment, PR, or issue bodies containing Markdown inline code should default
to single-quoted here-strings (`@'...'@`) for the literal text, reserving
double-quoted here-strings only for cases that genuinely need PowerShell
variable interpolation (and even then, avoid backticks in the same block).
