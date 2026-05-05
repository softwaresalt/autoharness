---
problem_type: template-authoring
category: quality-criteria
root_cause: design-finding-location-requirements
tags: [review, quality-criteria, STRIDE, file-line, evidence-anchor]
created: 2026-05-05
shipment: 006-S
---

# STRIDE Findings and the File:Line Requirement

## Problem

Review and audit skill templates commonly require all findings to include a `file:line` location as a quality criterion. This works for code-level findings (injection, secrets in code, OWASP patterns) but breaks down for STRIDE threat model analysis, which produces **design-level advisory findings** that describe risks in system architecture — not a specific line of code.

If the `file:line` requirement applies uniformly, STRIDE findings would either fail the quality gate or be suppressed entirely, degrading the threat model output.

## Root Cause

The quality criterion was written as a blanket rule without considering that different finding types have inherently different location semantics.

## Solution

Add an explicit exception for STRIDE (and similar design-level analysis phases) in the quality criteria section:

```markdown
## Quality Criteria

* All findings include a specific file:line location, **except STRIDE findings** which
  require an **evidence anchor** instead:
  * A specific system component (e.g., "the authentication middleware layer")
  * A data flow step (e.g., "the token passed from login endpoint to session store")
  * A design decision (e.g., "the choice to store session tokens in URL query parameters")
```

## Rule

> Blanket `file:line` quality requirements must carry a named exception for design-level finding categories. Use "evidence anchor" (component / data flow / design decision) as the alternative location format for STRIDE and architecture-level findings.

## Applied In

- `templates/skills/security-audit/SKILL.md.tmpl` — Phase 5 and Quality Criteria sections
- `templates/agents/review/security-reviewer.agent.md.tmpl` — could apply if STRIDE is added to future code reviewers
