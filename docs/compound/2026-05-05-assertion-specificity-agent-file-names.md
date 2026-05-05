---
problem_type: verify-workspace
category: assertion-design
root_cause: weak-string-matching-in-assertions
tags: [verify_workspace, assertions, routing, test-fixtures, specificity]
created: 2026-05-05
shipment: 006-S
---

# Verify Workspace Assertions: Check Agent File Names, Not Persona Names

## Problem

`FOUNDATION_ASSERTIONS` in `verify_workspace.py` use a `must_contain` list to verify that routing is correctly wired into installed skill files. An initial assertion checked for `"security-reviewer"` as the marker that routing was wired.

This is too weak: table headers, list items, and comments that mention the persona name by text will satisfy the assertion without the actual agent file routing being present. A developer could add a row to the conditional persona table without wiring up the `spawn security-reviewer.agent.md` call in the Step 2 routing block — and the assertion would pass.

## Root Cause

The assertion was authored to check "is the persona mentioned?" rather than "is the routing call present?".

## Solution

Check for the agent **filename** as the `must_contain` string, not the persona label:

```python
# Weak — could match table header
{"path": "...", "must_contain": ["security-reviewer"]}

# Strong — only matches when the routing call references the agent file
{"path": "...", "must_contain": ["security-reviewer.agent.md"]}
```

## Rule

> `FOUNDATION_ASSERTIONS` for routing wiring must check for the agent file name (e.g., `security-reviewer.agent.md`), not just the persona display name. This ensures the assertion only passes when the routing step references the correct file, not merely when the persona appears in documentation.

## Applied In

- `src/autoharness/verify_workspace.py` — `security_review_persona_routing` and `security_plan_review_persona_routing` assertions
- `tests/test_verify_workspace.py` — updated fixture strings to use agent file names
