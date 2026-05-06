---
title: "Browser CLI detection must use runtime_surfaces.browser_tooling, not tools"
problem_type: schema-field-mismatch
category: verify_workspace
root_cause: "profile.get('tools') is an object with markdownlint properties; iterating it yields dict keys, never matching playwright/puppeteer. The schema-backed array for browser automation tooling is runtime_surfaces.browser_tooling."
tags: [verify_workspace, workspace-profile, schema, browser-tooling, runtime_surfaces]
shipment: 007-S
date: 2026-05-05
---

## Problem

When adding browser CLI auto-detection in `_derive_template_variables()`, the first implementation read:

```python
tools_in_profile = [str(t) for t in (profile.get("tools") or [])]
```

`profile.tools` is a schema object with properties like `markdownlint` and `markdownlint_config` — not a list. Iterating it yields dict keys (`["markdownlint", "markdownlint_config"]`), which never match `"playwright"` or `"puppeteer"`. BROWSER_CLI always fell back to `agent-browser` regardless of what was installed.

## Root Cause

The workspace-profile schema defines two separate structures:
- `tools` — object with boolean/string properties for specific dev tools (markdownlint only at present)
- `runtime_surfaces.browser_tooling` — array of strings for detected browser automation tooling

Copilot caught this in review: "Consider detecting from `profile.runtime_surfaces.browser_tooling` (array) or another schema-backed field instead."

## Fix

```python
runtime_surfaces = profile.get("runtime_surfaces") or {}
browser_tooling = [str(t) for t in (runtime_surfaces.get("browser_tooling") or [])]
```

Always check the schema before assuming the type of a profile field. When adding profile-based detection, confirm the field is an array, not an object.

## Verification

Read `schemas/workspace-profile.schema.json` to confirm the type of any profile field before iterating it.
