---
description: "Install a complete agent harness into a target workspace from the global autoharness installation"
agent: Harness Installer
argument-hint: "workspace=<target-path> [primitives=1,2,3,4,5,6,7,8,9]"
---

# Install Harness

autoharness is installed globally and generates harness artifacts into a target workspace. The target workspace receives only the generated output — not the autoharness engine itself.

## Inputs

* ${input:workspace}: (Required in CLI environments, auto-detected in editors) Absolute path to the target workspace.
* ${input:primitives}: (Optional) Comma-separated primitive numbers (1-9) to install. Defaults to all.
