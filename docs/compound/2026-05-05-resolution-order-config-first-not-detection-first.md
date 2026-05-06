---
title: "Resolution-order docs must match code: explicit config override beats auto-detection"
problem_type: docs-code-mismatch
category: install-harness
root_cause: "The install-harness SKILL.md resolution note said 'detect from workspace profile first, then fall back to config override.' The code did the opposite (config override first, detection as fallback). Docs and code were inverted. Config-first is the correct semantics: explicit user choice overrides auto-detection."
tags: [install-harness, resolution-order, documentation, config-override, BROWSER_CLI]
shipment: 007-S
date: 2026-05-05
---

## Problem

The initial SKILL.md resolution note for `BROWSER_CLI` read:

> Detect from workspace profile tool inventory first. Fall back to the `config.browser.cli` override, then the schema default `agent-browser`.

The code was:
```python
browser_cli = str(browser_config.get("cli") or detected_browser_cli)
```

This is **config first, detection as fallback** — the opposite of what the docs said. The docs were wrong.

## Correct Semantics

Explicit config overrides should always win over auto-detection. An operator who sets `config.browser.cli: playwright` is making an explicit choice that must not be silently overridden by auto-detection. Auto-detection is only the default when no explicit config exists.

## Fix

Updated the resolution note to match the code:

> Override via `config.browser.cli` if set; otherwise detect from `runtime_surfaces.browser_tooling` in the workspace profile; falls back to the schema default `agent-browser`.

## Rule

When writing resolution notes for install-harness variables:
- "Override via `config.X`" means config wins (explicit user choice)
- "Detect from workspace profile" is the auto-detection fallback
- The order in the note must match the order in `_derive_template_variables()`
- Read the code before writing the docs, or the docs will mislead future agents
