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
- Ensure the scripted deploy wrappers honor the opt-in: an **omitted** pack selection
  resolves to the selected preset's `default_in_preset` members only, while an **explicit**
  `all` still deploys every registry pack (see "Additional required scope — deploy
  wrappers").

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

## Files changed in the committed patch (13)

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
2. Complete the deploy-wrapper scope in "Additional required scope — deploy wrappers"
   below (it is **not** in the 13-file patch) and add its wrapper tests. Do this
   **before** the verification steps so the evidence below covers the full change.
3. Run the targeted tests **and the new wrapper tests** (after the wrapper
   implementation is in place):

   ```bash
   python -m pytest tests/test_capability_pack_registry.py \
     tests/test_graphtor_docs_full_suite.py \
     tests/test_manifest_capability_pack_enum.py -q
   # plus the new deploy-wrapper tests added in step 2
   ```

4. Refresh the 3 manifest-tracked checksums in `.autoharness/harness-manifest.yaml`
   (`.github/instructions/agent-intercom.instructions.md`,
   `.github/skills/install-harness/SKILL.md`,
   `.github/skills/workspace-discovery/SKILL.md`) using raw-bytes `sha256` of the
   on-disk (CRLF) file, matching the existing manifest convention.
5. Run dogfood `verify_workspace` to confirm 0 blockers and no unresolved
   `{{VARIABLE}}` placeholders.
6. Open a dedicated PR for this change. Do **not** bundle it with the 079 telemetry
   ship work.

## Additional required scope — deploy wrappers (found in review)

The 13-file patch above is **not sufficient** on its own to achieve the opt-in goal.
Both deploy wrappers default omitted pack input to `all` and, for any non-`starter`
preset, enumerate **every** registry pack — they never consult `default_in_preset`:

- `scripts/deploy-harness.ps1` — `[string]$Packs = "all"` (line ~42); the
  `elseif ($Packs -eq "all")` branch (lines ~258-269) calls `Get-RegistryPacks`, which
  reads only `- id:` lines and ignores `default_in_preset`.
- `scripts/deploy-harness.sh` — `PACKS="all"` (line ~45); the `elif [[ "$PACKS" == "all" ]]`
  branch (lines ~221-225) enumerates via `registry_packs`, likewise ignoring
  `default_in_preset`.

Consequently a normal `full`/`standard` deploy with omitted `--packs`/`-Packs` still
writes `agent-intercom` into `.autoharness/config.yaml` without an explicit operator
selection, defeating the opt-in reclassification. The later shipment MUST also:

1. Distinguish an **omitted** pack input from an **explicit** `all`. Change the default
   sentinel (e.g. `preset` or empty) so omission is detectable rather than pre-set to `all`.
2. When pack input is omitted, resolve packs to the selected preset's defaults — the
   registry packs whose `default_in_preset` includes the chosen preset (so `agent-intercom`,
   with `default_in_preset: []`, is excluded from every preset default).
3. Keep an explicit `--packs all` / `-Packs all` meaning **all** registry packs.
4. Teach the registry enumerators to parse `default_in_preset` (both scripts currently read
   only `id:`), and add wrapper tests covering: omitted input on `full`/`standard` excludes
   opt-in add-ons; explicit `all` includes them; `starter` stays empty.

## Notes

- Dogfood keeps agent-intercom woven in (agents, `review/SKILL.md`, constitution)
  because `.autoharness/config.yaml` explicitly opts in. Do not remove that weave.
- `agent_engram` and `graphtor_docs` keep their `mcp_configured` fields — only
  `agent_intercom` loses MCP.
- The deploy wrappers (`scripts/deploy-harness.{sh,ps1}`) currently default omitted pack
  input to `all` and enumerate every registry pack for non-`starter` presets, so the
  `default_in_preset: []` change alone does **not** stop a default `full`/`standard` deploy
  from writing agent-intercom — see "Additional required scope — deploy wrappers" above.
  This wrapper fix must ship together with the patch.
