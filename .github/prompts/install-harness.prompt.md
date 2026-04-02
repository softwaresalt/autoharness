---
description: "Install a complete agent harness into a target workspace from the global autoharness installation"
agent: Harness Installer
argument-hint: "workspace=<target-path> [preset=starter|standard|full] [primitives=1,2,3,4,5,6,7,8,9,10] [capability_packs=agent-intercom,agent-engram,backlogit,browser-verification,strict-safety,release-observability]"
---

# Install Harness

autoharness is installed globally and generates harness artifacts into a target workspace. The target workspace receives only the generated output — not the autoharness engine itself.

## Inputs

* ${input:workspace}: (Required in CLI environments, auto-detected in editors) Absolute path to the target workspace.
* ${input:preset}: (Optional) Install preset: `starter`, `standard`, or `full`. Defaults to `standard`.
* ${input:primitives}: (Optional) Comma-separated primitive numbers (1-10) to install. Defaults to the selected preset.
* ${input:capability_packs}: (Optional) Comma-separated capability packs: `agent-intercom`, `agent-engram`, `backlogit`, `browser-verification`, `strict-safety`, `release-observability`.
