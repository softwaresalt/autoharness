---
title: "Path traversal validation requires Path.parts, not startswith"
problem_type: security-validation-bypass
category: verify_workspace
root_cause: "raw_value.startswith('..') only catches paths that start with a traversal segment. Embedded traversal like 'logs/../../outside' bypasses the check. The correct guard is '..' in Path(value).parts."
tags: [verify_workspace, path-validation, workspace-containment, security, traversal]
shipment: 007-S
date: 2026-05-05
---

## Problem

When validating `EXPERIMENT_RESULTS_DIR` to prevent workspace escapes, the initial implementation used:

```python
if _results_path.is_absolute() or raw_results_dir.startswith(".."):
    raw_results_dir = "docs/experiments"
```

This accepts `logs/../../outside` as valid — the string doesn't start with `..` even though `Path("logs/../../outside").parts` contains a `..` segment that resolves outside the workspace root.

## Fix

```python
if _results_path.is_absolute() or ".." in _results_path.parts:
    raw_results_dir = "docs/experiments"
```

`Path.parts` splits the path into its components: `("logs", "..", "..", "outside")`. Checking for `".."` in parts catches all embedded traversal, not just leading traversal.

## Pattern

For any workspace-containment validation that must reject relative traversal paths:

```python
_p = Path(user_value)
if _p.is_absolute() or ".." in _p.parts:
    user_value = safe_default
```

This pattern is reusable for any path variable that must remain within the workspace root.
