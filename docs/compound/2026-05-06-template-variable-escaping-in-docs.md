---
problem_type: template_variable_residue
category: template_authoring
root_cause: Double-brace {{VARIABLE}} syntax used in documentation examples inside .tmpl files is treated as an unresolved variable by the installer's residue checker, causing false-positive failures.
tags: [templates, variable-residue, documentation, escaping]
shipment: 008-S
date: 2026-05-06
---

# Escaping `{{VARIABLE}}` in Template Documentation

## Problem

Template files (`.tmpl`) use `{{VARIABLE}}` as the substitution syntax.
When a template contains illustrative documentation that shows variable
syntax as an example (not an actual placeholder), the installer's residue
check flags these as unresolved variables after install.

## Root Cause

The installer scans installed output for any `{{...}}` pattern. It cannot
distinguish between:

1. `{{AUTOHARNESS_VERSION}}` — a real placeholder that must be resolved
2. `{{HARNESS_MANIFEST_PATH}}` shown in a code block as documentation

Both match the same regex.

## Fix

Use escaped form for illustrative variables inside `.tmpl` documentation:

```markdown
<!-- In a .tmpl file — for documentation-only references -->
\{\{VARIABLE_NAME\}\}

<!-- This is a real placeholder — will be resolved at install time -->
{{VARIABLE_NAME}}
```

The backslash-escaped form survives the install residue check because it
does not match the `{{...}}` regex, and renders as literal `{{VARIABLE_NAME}}`
in the final Markdown.

## Verification

After install, run the residue check:
```
grep -r '{{' <workspace>/.github/ --include="*.md"
```
Any hit is a real unresolved variable; escaped `\{\{` will not appear.
