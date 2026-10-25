---
title: "Harness Tuning Report — 2026-10-24"
date: "2026-10-24T18:40:00Z"
workspace: "C:\\Source\\GitHub\\autoharness"
autoharness_version: "1.6.0"
mode: "applied"
auto_apply: true
---

# Harness Tuning Report — 2026-10-24

## Branch Safety Notice (Phase 0c)

* **Current branch**: `main` (repository default branch: `origin/main`)
* **Branch-safety rule**: Never commit or push autoharness tune output directly to `main`. Before applying and committing any accepted tuning proposals, create and switch to a feature branch (for example `chore/autoharness-tune-2026-10-24`), review the diff, and open a pull request.
* **CLI Workspace Containment (Principle IV)**: All writes in this session are strictly contained within `C:\Source\GitHub\autoharness`. Read-only `verify-workspace` assessments for `C:\Source\GitHub\backlogit` and `C:\Source\GitHub\engram` are included in the Cross-Workspace Assessment section below.

## Drift Summary (`C:\Source\GitHub\autoharness`)

* Breaking changes (P0): `0`
* Degrading changes (P1): `17` (`1` schema-contract upgrade, `13` subagent route-frontmatter drift proposals, `2` targeted-check/mirror gaps, `1` legacy `.backlogit/` root advisory)
* Growth opportunities (P2): `2` (`1` uninstalled prompt template, `1` learning-driven `compound-refresh` consolidation)
* Cosmetic adjustments (P3): `1` (`harness-manifest.yaml` recorded `autoharness_version` bump `1.4.11` -> `1.6.0`, plus `16` Windows CRLF working-copy line-ending differences whose LF-normalized blobs match manifest checksums)

## Composition

* Installed primary stack pack: `cli-tool`
* Current primary stack pack: `cli-tool`
* Installed stack packs: `["cli-tool"]`
* Current stack packs: `["cli-tool"]`
* Installed layers: `["foundation", "instructions", "workflow", "review", "runtime", "backlog", "knowledge", "overlays"]`
* Recommended layers: `["foundation", "instructions", "workflow", "review", "runtime", "backlog", "knowledge", "overlays"]`
* Enabled capability packs: `["backlogit", "agent-engram", "graphtor-docs"]`
* Startup-script contracts: `start.ps1` = `current` (`1.1.0`), `start.sh` = `current` (`1.1.0`)
* Copilot code-review focus instruction: `.github/instructions/copilot-code-review.instructions.md` = `PASS` (`applyTo: '**'`, `excludeAgent: 'cloud-agent'`, FOCUS framing intact)

## Checksum Scan

* Total manifest-tracked artifacts: `72`
* Unchanged (exact byte match): `56`
* Missing installed artifacts: `0`
* User-modified artifacts: `16` (all `16` match their recorded manifest SHA-256 byte-for-byte after CRLF-to-LF normalization; caused by Windows checkout line endings rather than content edits)
* Ignored artifacts: `0`

## Schema Contracts

* `harness-manifest` (`.autoharness/harness-manifest.yaml`): `current` (observed `1.1.0`, current `1.1.0`)
* `harness-config` (`.autoharness/config.yaml`): `known-legacy` (observed `1.2.0`, current `1.3.0`)
* `workspace-profile` (`.autoharness/workspace-profile.yaml`): `current` (observed `1.1.0`, current `1.1.0`)

## Learning Signals

* Compound patterns detected: `22` (`1` component hotspot: `pipeline-topology-gate` [3]; `21` cross-cutting tags led by `copilot-review` [25], `ship` [18], `backlogit` [17], `p-018` [16], `ship-agent` [11], `p-021` [10], `cascade-close` [9], `shipment-reconcile` [9], `p-015` [8])
* Promotion-ready instincts: `0`
* Recurring closure findings: `0`
* Policy-gap candidates detected: `0` (all recurring compound patterns map to existing policies `P-001`–`P-021`)
* Learning-driven proposals generated: `1`

## Proposed Changes (Ordered by Priority)

### P0 — Breaking

None.

### P1 — Degrading

```yaml
- id: "TUNE-001"
  priority: "P1"
  category: "degrading"
  source: "schema-contract"
  proposal_id: "upgrade-config-contract-1.2.0-to-1.3.0"
  contract: "harness-config"
  artifact: ".autoharness/config.yaml"
  from_version: "1.2.0"
  to_version: "1.3.0"
  status: "known-legacy"
  severity: "degrading"
  changed_fields: ["schema_version", "capability_packs"]
  manual_review: false
  issue: "Upgrade the harness-config contract from 1.2.0 to 1.3.0 (the retired retired-remote-operator-pack capability pack is no longer a valid capability_packs entry)."
  proposal: "Back up .autoharness/config.yaml, bump schema_version from '1.2.0' to '1.3.0' (retired-remote-operator-pack is already absent from capability_packs), refresh config_hash and artifacts[].checksum in .autoharness/harness-manifest.yaml, and rerun verify-workspace."
  diff_preview: |
    - schema_version: "1.2.0"
    + schema_version: "1.3.0"

- id: "TUNE-002"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/agent-native-parity-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-003"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/architecture-strategist.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-004"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/concurrency-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-005"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/constitution-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-006"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/correctness-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-007"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/learnings-researcher.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-008"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/maintainability-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-009"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/python-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-010"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/schema-cli-docs-coupling-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-011"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/scope-boundary-auditor.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-012"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/security-lens-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-sonnet-5.5", model_provider: "anthropic", reasoning_effort: "high", context_tier: "long_context"}
    installed: {model_family: "claude-sonnet-5", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-013"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/security-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-sonnet-5.5", model_provider: "anthropic", reasoning_effort: "high", context_tier: "long_context"}
    installed: {model_family: "claude-sonnet-5", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-014"
  priority: "P1"
  category: "degrading"
  source: "route-drift"
  contract: "model-routing"
  action: "refresh-route-frontmatter"
  artifact: ".github/agents/subagents/template-integrity-reviewer.agent.md"
  status: "stale-route"
  severity: "P1"
  changed_fields: ["model_family", "model_provider", "reasoning_effort"]
  manual_review: false
  evidence:
    expected: {model_family: "claude-haiku-5.5", model_provider: "anthropic", reasoning_effort: "xhigh", context_tier: "long_context"}
    installed: {model_family: "gpt-5.6-luna", model_provider: "", reasoning_effort: "", context_tier: "long_context"}

- id: "TUNE-015"
  priority: "P1"
  category: "degrading"
  source: "structural-drift"
  artifact: ".github/instructions/backlogit-sql-schema.instructions.md, .github/instructions/backlogit-yaml-header-tooling.instructions.md"
  issue: "Targeted checks backlogit_sql_schema_instruction and backlogit_yaml_header_instruction fail because the two backlogit helper instructions are not installed in .github/instructions/."
  proposal: "Render and install backlogit-sql-schema.instructions.md and backlogit-yaml-header-tooling.instructions.md from templates/instructions/ and register both in .autoharness/harness-manifest.yaml."

- id: "TUNE-016"
  priority: "P1"
  category: "degrading"
  source: "structural-drift"
  artifact: "AGENTS.md, .github/copilot-instructions.md, .github/agents/_stage.agent.md, .github/agents/_ship.agent.md"
  manual_review: true
  issue: "8 targeted checks fail against the condensed hand-authored dogfood mirrors (agents_metadata_catalog_guidance, copilot_remote_operator_guidance, copilot_durable_knowledge_layout, copilot_session_memory_guidance, copilot_backlog_workflow_expectations, stage_shipment_determinism, ship_source_artifact_cleanup, ship_branch_management)."
  proposal: "Selectively weave the missing verifier anchor phrases into the condensed dogfood mirrors (preserving engine-specific dogfood sections) rather than overwriting them with generic target-workspace renders."

- id: "TUNE-017"
  priority: "P1"
  category: "degrading"
  source: "structural-drift"
  artifact: ".backlogit/"
  manual_review: true
  issue: "Workspace uses legacy-only backlog storage root (.backlogit/ present, .backlog/ absent)."
  proposal: "Detect-and-report only (Step 1.5): review `backlogit migrate --workspace-dir --dry-run` when ready to migrate to `.backlog/`."
```

### P2 — Growth

```yaml
- id: "TUNE-019"
  priority: "P2"
  category: "growth"
  source: "structural-drift"
  artifact: ".github/prompts/stage-grouping-analysis.prompt.md"
  template: "templates/prompts/stage-grouping-analysis.prompt.md.tmpl"
  issue: "Template exists in autoharness_home but has no installed artifact or manifest entry in this workspace."
  proposal: "Optionally render and install .github/prompts/stage-grouping-analysis.prompt.md and add its manifest entry."

- id: "TUNE-020"
  priority: "P2"
  category: "growth"
  source: "learning-driven"
  artifact: "docs/compound/"
  issue: "Compound library has high-density clusters in copilot-review (25), ship (18), backlogit (17), p-018 (16), ship-agent (11), p-021 (10), cascade-close (9), and shipment-reconcile (9)."
  proposal: "Invoke compound-refresh to consolidate overlapping entries in the copilot-review, cascade-close, and shipment-reconcile clusters."
  evidence:
    pattern_type: "cross_cutting_tags"
    evidence_count: 25
    evidence_refs:
      - "docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md"
      - "docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md"
      - "docs/compound/2026-10-08-copilot-review-body-findings-without-threads.md"
```

### P3 — Cosmetic

```yaml
- id: "TUNE-018"
  priority: "P3"
  category: "cosmetic"
  source: "structural-drift"
  artifact: ".autoharness/harness-manifest.yaml"
  issue: "Manifest records autoharness_version: '1.4.11' while repository version is '1.6.0', and 16 tracked files have CRLF working-copy line endings on Windows."
  proposal: "Update autoharness_version to '1.6.0' and normalize the 16 working-copy files to LF when applying tune changes on a feature branch."
```

---

## Cross-Workspace Read-Only Assessment (`backlogit` & `engram` vs. autoharness 1.6.0)

Running `autoharness 1.6.0` `verify_workspace` read-only against `C:\Source\GitHub\backlogit` and `C:\Source\GitHub\engram` (both currently at `autoharness_version: "1.5.0"`) confirms how `1.6.0` addresses the harness/verifier issues encountered in **both** workspaces:

| Dimension | `C:\Source\GitHub\backlogit` (v1.5.0 installed) | `C:\Source\GitHub\engram` (v1.5.0 installed) | How autoharness 1.6.0 Addresses It |
|---|---|---|---|
| **Strict Schema / Verifier Blockers** | `0` strict blockers, `0` blockers | `0` strict blockers, `0` blockers | **Fixed in 1.6.0 (209-F / 216-S)**: Legacy `retired-remote-operator-pack` references in `1.0.0` profiles/manifests now degrade to non-blocking `removed-capability-pack` warnings + `remove-retired-capability-pack` proposals instead of failing schema validation. |
| **Pack-Scoped Verifier Assertions (G4)** | `agent-engram` is **not** enabled in `backlogit`; previously failed unconditional `copilot_remote_operator_guidance` (`### agent-engram`) check | `agent-engram` is enabled (`backlogit`, `agent-engram`, `continuous-learning`, `graphtor-docs`) | **Fixed in 1.6.0 (213-F / 220-S, G4)**: `copilot_remote_operator_guidance` is now scoped to workspaces with `agent-engram` enabled (`backlogit` passes!), and `pipeline_topology_gate_ship_agent_claim_ordering` is scoped to `backlogit`. |
| **Agent-Engram Tool Surface (G1)** | N/A (`agent-engram` not enabled) | Enabled; previously referenced unregistered `query_graph_neighborhood` | **Fixed in 1.6.0 (212-F / 219-S, G1)**: `agent-engram.instructions.md.tmpl` now routes graph queries exclusively through registered `query_graph` (`neighborhood`, `find_path`, `transitive_closure`). |
| **Docs-Only Task Route (G3)** | Supported on next tune | Needed for docs-only/schema-deliberation tasks (`0011C2DC`) | **Fixed in 1.6.0 (216-F / 223-S, G3)**: Adds `harness-verification-gated` route and `autoharness harness docs-only-check`. |
| **Backlog CLI as Peer of MCP (P-012)** | Currently fails `backlog_registry_cli_surface` on `1.5.0` registry | Passes `backlog_registry_cli_surface` | **Fixed in 1.6.0 (214-F / 221-S)**: Updated `backlogit.registry.yaml` template adds `cli_command` for hooks, comments, memory, stash, and metadata ops. |
| **Startup Script Contracts** | `start.sh`: `ambiguous` (`review-startup-script-sh-contract`, `manual_review: true`) | `start.ps1` & `start.sh`: `known-legacy` (`refresh-startup-script-ps1-contract`, `refresh-startup-script-sh-contract` preserving 790-byte custom section) | **Handled in 1.6.0**: Startup-script classifier detects `engram`'s legacy scripts and preserves `start.sh`'s custom tail on refresh while failing closed (`ambiguous`) on `backlogit`'s edited `start.sh`. |
| **Pending 1.5.0 -> 1.6.0 Tune Proposals** | `46` proposals (`3` contract upgrades, `1` retired-pack cleanup, `1` startup-script review, `29` frontmatter-conformity [7 managed skills + 22 workspace-authored], `12` subagent route refreshes) and `5` targeted-check refreshes (`frontmatter_conformity`, `ship_source_artifact_cleanup`, `dark_factory_visibility_contract`, `orchestrator_invocation_routing_directive`, `backlog_registry_cli_surface`) | `55` proposals (`3` contract upgrades, `1` retired-pack cleanup, `2` startup-script refreshes, `32` frontmatter-conformity [16 managed skills + 16 workspace-authored], `17` subagent route refreshes) and `5` targeted-check refreshes (`frontmatter_conformity`, `ship_release_closure_sequence`, `dark_factory_visibility_contract`, `orchestrator_invocation_routing_directive`, `escalation_route_resolution`) | Running `/tune-harness` inside each target workspace (`cd C:\Source\GitHub\backlogit` and `cd C:\Source\GitHub\engram`) on a feature branch will apply the `1.6.0` template upgrades. |

## Recommendation

1. **In `C:\Source\GitHub\autoharness`**: Switch to a feature branch (`git checkout -b chore/autoharness-tune-2026-10-24`) and approve `TUNE-001` (`.autoharness/config.yaml` `1.2.0 -> 1.3.0`), `TUNE-002`–`TUNE-014` (subagent route frontmatter refresh), `TUNE-015` (install the 2 missing backlogit helper instructions), and `TUNE-018` (manifest version `1.6.0`). Review `TUNE-016` (condensed dogfood mirror anchor phrases) and `TUNE-019` (`stage-grouping-analysis.prompt.md`) individually.
2. **In `C:\Source\GitHub\backlogit` and `C:\Source\GitHub\engram`**: Both workspaces had `1.5.0` harness drift that `autoharness 1.6.0` was specifically built to resolve (G4 pack-conditional checks and P-012 CLI-peer registry in `backlogit`; G1 `query_graph`, G3 `docs-only-check`, legacy startup-script migration, and `ESCALATION_DEGRADED` same-route detection in `engram`; plus `retired-remote-operator-pack` retirement, `context_tier` Orchestrator directives, and skill `name:` frontmatter conformity in both). Run `/tune-harness` from within each of those workspaces on a dedicated feature branch to apply their `1.6.0` migrations.
