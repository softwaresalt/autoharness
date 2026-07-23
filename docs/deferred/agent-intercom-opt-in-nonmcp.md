---
title: "Deferred: agent-intercom opt-in / non-MCP reclassification"
description: Durable reimplementation plan and patch for the deferred agent-intercom opt-in and non-MCP capability-pack reclassification (backlogit stash DD75C983)
doc_type: reference
---

# Deferred: agent-intercom opt-in / non-MCP reclassification

Status: **completed but deferred** — the change is fully implemented and was passing
locally, but it is intentionally set aside for its own later shipment rather than
merged now. This document plus the committed patch make the deferred work durable and
reproducible from a fresh clone; it does not depend on any local `git stash` or
gitignored session checkpoint.

Backlog tracker: backlogit stash entry `DD75C983`.

## Goal

Reclassify the `agent-intercom` capability pack:

- Remove it from the `full` capability-pack preset; make it an **opt-in extra add-on**
  (not a preset default). It remains a woven overlay when explicitly enabled — it is
  **not** demoted to a detached single-file add-on, which would contradict the
  capability-pack overlay principle.
- Reflect that agent-intercom **no longer supports an MCP server**. It operates over a
  non-MCP intercom/ACP tool surface, so it carries no `mcp_requirements`.

## Durable artifact

The exact diffs are preserved in the committed patch:

- `docs/deferred/agent-intercom-opt-in-nonmcp.patch`

Apply it on a fresh feature branch:

```bash
git checkout -b feat/agent-intercom-opt-in-nonmcp origin/main
git apply --3way docs/deferred/agent-intercom-opt-in-nonmcp.patch
```

If `git apply` reports drift because base files moved, apply with fuzz or re-create the
edits from the "Files changed" section below.

## Files changed (13)

| File | Change |
|---|---|
| `templates/packs/capability-pack-registry.yaml` | agent-intercom → `default_in_preset: []`, `mcp_requirements: []`; eligibility signals rewritten to non-MCP; clarifying comment added. |
| `tests/test_capability_pack_registry.py` | Added `test_agent_intercom_is_opt_in_add_on` (asserts `default_in_preset == []` and `mcp_requirements == []`). |
| `tests/test_graphtor_docs_full_suite.py` | Replaced `test_every_pack_defaults_into_full_preset` with `test_every_non_opt_in_pack_defaults_into_full_preset` + `test_opt_in_add_ons_are_not_full_defaults` (class attr `_OPT_IN_ADD_ONS = {"agent-intercom"}`); docstring updated. |
| `schemas/workspace-profile.schema.json` | Removed `agent_intercom.mcp_configured`. |
| `schemas/workspace-profile/1.0.0.schema.json` | Removed `agent_intercom.mcp_configured` (mirror). |
| `.github/skills/install-harness/SKILL.md` | Full preset table drops agent-intercom; opt-in prose; config-paths example → `.intercom/settings.json`; overlay-contract eligibility/recommendation rewritten to non-MCP + opt-in; tuning drift check updated. (Manifest-tracked.) |
| `.github/skills/workspace-discovery/SKILL.md` | Step 1.5c table drops the `.mcp.json` MCP row; recorded structure + example drop `mcp_configured`; recommendation summary updated. (Manifest-tracked.) |
| `.github/instructions/agent-intercom.instructions.md` | Intro/Required Tool Surface note opt-in add-on with no MCP server (non-MCP intercom/ACP surface). (Manifest-tracked.) |
| `templates/instructions/agent-intercom.instructions.md.tmpl` | Same intercom-surface wording as the mirror. (Not manifest-tracked.) |
| `docs/capability-packs.md` | Overlay example notes opt-in / no-MCP; eligibility signals drop `.mcp.json`/legacy editor lines. |
| `docs/getting-started.md` | Intercom step reworded ("intercom tool surface / path is reachable", "no MCP server"). |
| `.autoharness/workspace-profile.yaml` | Drop `agent_intercom.mcp_configured`; recommendation rationale reflects opt-in/non-MCP; pack stays recommended/enabled (dogfood opts in). |
| `.autoharness/harness-manifest.yaml` | Refresh checksums for the 3 manifest-tracked mirrors above. |

## Resume + verification steps

1. Apply the patch on a fresh feature branch (see above).
2. Re-run targeted tests:

   ```bash
   python -m pytest tests/test_capability_pack_registry.py \
     tests/test_graphtor_docs_full_suite.py \
     tests/test_manifest_capability_pack_enum.py -q
   ```

3. Refresh the 3 manifest-tracked checksums in `.autoharness/harness-manifest.yaml`
   (`.github/instructions/agent-intercom.instructions.md`,
   `.github/skills/install-harness/SKILL.md`,
   `.github/skills/workspace-discovery/SKILL.md`) using raw-bytes `sha256` of the
   on-disk (CRLF) file, matching the existing manifest convention.
4. Run dogfood `verify_workspace` to confirm 0 blockers and no unresolved
   `{{VARIABLE}}` placeholders.
5. Open a dedicated PR for this change. Do **not** bundle it with the 079 telemetry
   ship work.

## Notes

- Dogfood keeps agent-intercom woven in (agents, `review/SKILL.md`, constitution)
  because `.autoharness/config.yaml` explicitly opts in. Do not remove that weave.
- `agent_engram` and `graphtor_docs` keep their `mcp_configured` fields — only
  `agent_intercom` loses MCP.
- deploy-harness `-Packs all` enumerates every registry pack regardless of preset, so
  the `default_in_preset` change does not alter deploy-harness behavior; the preset only
  affects `starter` (no packs).
