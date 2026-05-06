---
title: "harness-config.yaml.tmpl must include all new variables for round-trip correctness"
problem_type: config-roundtrip-gap
category: install-harness
root_cause: "New template variables documented in install-harness SKILL.md resolution tables must also appear in harness-config.yaml.tmpl. Without this, the resolved values are never written back to the workspace config file and are lost on re-install or tune."
tags: [install-harness, harness-config, config-writeback, round-trip, template-variables]
shipment: 007-S
date: 2026-05-05
---

## Problem

When adding new template variables (`BROWSER_CLI`, `BROWSER_HEADLESS_FLAG`, `EXPERIMENT_BRANCH_PREFIX`, `EXPERIMENT_RESULTS_DIR`), the variables were documented in the install-harness SKILL.md resolution table but were not added to `templates/harness-config.yaml.tmpl`.

This breaks the round-trip contract: install/tune resolves the variables, but cannot write them back to the workspace's `harness-config.yaml` because the sections `browser:` and `experiments:` did not exist in the template. On re-install or tune, the variables would re-resolve from defaults instead of from the committed workspace config.

Copilot caught this: "The generated `harness-config.yaml.tmpl` still has no `browser:` or `experiments:` sections. Install/tune therefore can't write back or round-trip the resolved values it just discovered."

## Fix

For every new group of variables, add a matching section to `templates/harness-config.yaml.tmpl`:

```yaml
browser:
  cli: "{{BROWSER_CLI}}"
  headless_flag: "{{BROWSER_HEADLESS_FLAG}}"

experiments:
  branch_prefix: "{{EXPERIMENT_BRANCH_PREFIX}}"
  results_dir: "{{EXPERIMENT_RESULTS_DIR}}"
```

## Checklist

When adding new template variables to autoharness, always:
1. Add to install-harness SKILL.md resolution table ✓
2. Add to `_derive_template_variables()` in verify_workspace.py ✓
3. Add to `templates/harness-config.yaml.tmpl` ← often missed
4. Add FOUNDATION_ASSERTIONS for wiring correctness ✓
