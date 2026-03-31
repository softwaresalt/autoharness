---
description: "Tune an installed agent harness to match current workspace state"
agent: Harness Tuner
argument-hint: "[workspace=...] [scope=all|instructions|agents|skills|policies|constitution]"
---

# Tune Harness

## Inputs

* ${input:workspace}: (Optional) Target workspace path. Defaults to the current workspace.
* ${input:scope}: (Optional) Scope of tuning: `all`, `instructions`, `agents`, `skills`, `policies`, `constitution`. Defaults to `all`.
