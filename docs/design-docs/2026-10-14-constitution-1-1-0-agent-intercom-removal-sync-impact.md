---
title: "Constitution 1.1.0 sync impact report: agent-intercom removal"
description: "Amendment rationale, version bump and sync impact for removing the agent-intercom capability overlay from the constitution"
status: accepted
date: 2026-10-19
source: "stash 0FD06900 operator decision; shipment 216-S, feature 209-F, task 209.010-T"
---

# Constitution 1.1.0 sync impact report: agent-intercom removal

The constitution's Governance section requires that any amendment carry a
version bump, a rationale, and a sync impact report. This document is that
record for the removal of the `agent-intercom` capability overlay. It is a dated
historical record and names the removed pack on purpose.

## Amendment

| Field | Value |
|---|---|
| Previous version | 1.0.0 |
| New version | 1.1.0 (MINOR: a capability overlay is removed; no principle is removed or redefined) |
| Artifacts | `templates/foundation/constitution.instructions.md.tmpl` and the installed mirror `.github/instructions/constitution.instructions.md` |
| Plan | `docs/plans/2026-10-14-remove-agent-intercom-pack-plan.md` (unit U10, decisions D-4 and D-8) |

### Changes

1. Removed the `Capability Overlay — agent-intercom` section from the template
   and the `agent-intercom` bullet from the mirror's `## Capability Overlays`
   list.
2. The NON-NEGOTIABLE enforcement sentence changes from "MUST broadcast a P-005
   event and halt" to "MUST report a P-005 event in the session output and
   halt". P-005 violation telemetry recording is unchanged.
3. `**Version**` bumped from 1.0.0 to 1.1.0 in the template and the mirror.

## Rationale

The operator no longer uses the `agent-intercom` capability pack and directed
its full removal from the product and the dogfood harness (stash 0FD06900,
resolved as plan decision D-1). The overlay clause described heartbeat,
milestone broadcasting, approval routing and operator steering waits that no
longer exist in the harness. Keeping it would leave a normative clause that
points at a removed instruction file and tool surface.

Normative operator-visible behavior that lived in that overlay was relocated,
not deleted (plan D-4): the Dark Factory Visibility Protocol now lives in the
P-017 section of `workflow-policies`, and the operator-choice presentation rule
now lives in `backlogit.instructions`.

## Principles I-XI

No principle text changes. In particular:

* Principle VII (Destructive Command Approval, NON-NEGOTIABLE) is independent of
  the removed overlay. Destructive terminal commands and destructive file
  operations still require operator approval before execution, through the
  workspace's native approval path (local confirmation, or `strict-safety`
  classification when that pack is installed).
* Nothing in this amendment permits skipping that approval when no remote
  channel exists. Absence of a remote channel never relaxes Principle VII.

## Sync Impact

| Surface | Impact |
|---|---|
| `templates/foundation/constitution.instructions.md.tmpl` | Overlay section removed; P-005 sentence retargeted; version 1.1.0 |
| `.github/instructions/constitution.instructions.md` | Overlay bullet removed; P-005 sentence retargeted; version 1.1.0 |
| `templates/foundation/AGENTS.md.tmpl` | Overlay section, interaction-table rows and Terminal Command Execution Policy rule 5 removed; the `Constitution version` stamp bumped from 1.0.0 to 1.1.0 |
| root `AGENTS.md` | Only the pack table row removed; the dogfood root file carries no overlay section, interaction table, terminal-policy rule or constitution version stamp |
| `templates/foundation/copilot-instructions.md.tmpl` | Pack section and remote-operator subsection removed; the `## Remote Operator Integration` heading and its `agent-engram` subsection are kept (plan D-8) |
| `.github/instructions/harness-architecture.instructions.md`, `.github/copilot-review-instructions.md` | Pack examples and references removed |
| Already-installed workspaces | Keep their rendered 1.0.0 constitution text until the operator runs tune; the retained text is inert prose |
| `.autoharness/harness-manifest.yaml` | Mirror checksums refreshed for the files edited by this task |
