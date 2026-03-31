---
description: "Install a complete agent harness into the target workspace"
agent: Harness Installer
argument-hint: "[workspace=...] [primitives=1,2,3,4,5,6,7,8]"
---

# Install Harness

## Inputs

* ${input:workspace}: (Optional) Target workspace path. Defaults to the current workspace.
* ${input:primitives}: (Optional) Comma-separated primitive numbers (1-8) to install. Defaults to all.
