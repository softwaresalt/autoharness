---
title: Tuning Guide
description: How to iteratively maintain and adapt an installed agent harness as the codebase evolves
---

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Installation](installation.md) · [Environment Setup](environment-setup.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md) · [Backlog Integration](backlog-integration.md) · [Credits](credits.md)

## Why Tune

Agent harnesses degrade over time. Common causes:

* **New technologies added**: A Python backend gains a Go microservice, but no Go review persona exists
* **Build tool changes**: Migration from webpack to vite breaks build-feature skill commands
* **Directory restructuring**: `applyTo` patterns in instruction files match no files after a rename
* **CI pipeline changes**: Quality gate commands in the constitution no longer match CI steps
* **Runtime surface changes**: A repo grows a web UI or public API but the harness still assumes static-only validation
* **Composition-model changes**: The repo shifts from `library` to `api-service` or gains new additive stack packs, but the installed harness still reflects the older composition shape
* **Operator workflow changes**: agent-intercom is configured (or removed) but the harness does not reflect the required heartbeat, broadcast, or approval-routing behavior
* **Indexed-search workflow changes**: agent-engram is configured (or removed) but the harness does not reflect engram-first search, binding, or freshness behavior
* **Backlog workflow changes**: backlogit is present but the harness still uses only generic CRUD patterns and ignores queue, query, dependency, or checkpoint capabilities
* **Convention drift**: Team adopts new naming patterns not reflected in language instructions

## When to Tune

| Trigger | Urgency | Likely Drift Category |
|---------|---------|----------------------|
| Major release shipped | Medium | Growth, Cosmetic |
| New language/framework added | High | Breaking, Growth |
| CI/CD pipeline modified | High | Breaking, Degrading |
| Runtime verification surface added | High | Growth, Degrading |
| Directory restructuring | High | Breaking |
| Agent outputs degrading | Medium | Degrading |
| Monthly maintenance window | Low | All categories |

## How to Tune

The tuner is invoked from the global autoharness installation against a target workspace. It reads updated templates from autoharness home and proposes changes to the target's harness artifacts.

Capability packs are tuned using the same overlay contract used during installation: eligibility signals, target artifacts, behavior deltas, verification checks, and drift heuristics. See [Capability Packs](capability-packs.md).

The tuner also uses `.autoharness/harness-manifest.yaml` as a checksum inventory
of generated artifacts. When `.autoharness/drift-ignore` exists, matching paths
are treated as intentional local divergence rather than unexpected drift.

In Git-backed workspaces, treat tuning output as feature-branch work. If you
start tuning from the default branch, the intended outcome is reviewed local
changes or a later feature-branch handoff, not a direct default-branch commit
or push. `auto_apply` applies file edits only; it does not authorize a commit
or push.

### Interactive Tuning (Recommended)

Open the target workspace in VS Code, then select **Auto-Tune** from the agents dropdown in the Chat view, or type:

```text
/tune-harness
```

The tuner will:

1. Re-run workspace discovery to produce a fresh profile
2. Run `autoharness verify-workspace --json` to collect deterministic contract, warning, and targeted-check results
3. Compare against the profile used during installation
4. Compare manifest checksums against installed artifacts and classify missing, user-modified, unchanged, or ignored paths
5. Categorize each difference by impact
6. Scan all harness artifacts for health issues
7. Present a prioritized list of proposed changes
8. Apply changes you approve (with backups)

### Scoped Tuning

Focus on specific areas by describing the scope to the Auto-Tune agent, or pass a scope parameter:

```text
/tune-harness scope=instructions    # Only check instruction files
/tune-harness scope=agents          # Only check agent definitions
/tune-harness scope=skills          # Only check skill workflows
/tune-harness scope=policies        # Only check workflow policies
/tune-harness scope=constitution    # Only check constitutional docs
```

## Drift Categories

### Breaking

Harness references are invalid. Artifacts reference files, tools, or commands that no longer exist.

**Examples**: Build command changed from `npm run build` to `pnpm build`, test directory renamed from `tests/` to `__tests__/`, removed CI step still referenced in constitution.

**Action**: Fix immediately. Breaking drift causes agent failures.

### Degrading

Harness works but produces suboptimal results. Artifacts are valid but miss new capabilities or use outdated patterns.

**Examples**: New framework added without review persona, new test patterns without matching instructions, stale architecture documentation.

Additional examples: a web UI exists but no browser-verification pack is enabled, operational closure templates omit monitoring expectations, safety-mode guidance is missing from risky maintenance workflows, or risky plans never pass through `plan-harden` before review.

Additional examples: the workspace now exposes MCP tool handlers or agent-facing product actions, but the review layer still lacks the `agent-native-parity-reviewer` persona and parity-focused routing guidance.

Additional examples: the workspace depends on local-first PR review, but the installed harness still lacks the `template-integrity-reviewer` / `schema-cli-docs-coupling-reviewer` personas or still treats Copilot review as the required pre-merge gate.

Additional examples: the team wants recurring workflow observations to become explicit harness guidance, but the `continuous-learning` pack and its `observe` / `learn` / `evolve` workflows are missing.

Additional examples: discovery now classifies the repo as `web-app` + `deployable-service`, but the installed composition still lacks the expected `runtime` or `overlays` layers.

Additional examples: agent-intercom is configured in `.intercom/settings.json` or via existing instruction markers, but the harness does not install the intercom instruction file or thread heartbeat / approval guidance through the execution pipeline.

Additional examples: agent-engram is configured in `.mcp.json` or `.engram/`, but the harness never installs the engram instruction file and still defaults to grep-heavy repo exploration even when indexed lookup is available.

Additional examples: backlogit is detected, but the harness never recommends the backlogit pack and therefore misses SQL query, queue, memory, checkpoint, comment, and commit-trace workflows.

**Action**: Fix at next opportunity. Degrading drift reduces agent effectiveness.

### Growth

New capabilities that the harness could leverage. The workspace has evolved in ways that create opportunities for new harness features.

**Examples**: New database added (opportunity for database reviewer persona), Docker introduced (opportunity for container instructions), API documentation added (opportunity for API review).

Additional examples: web UI added (opportunity for browser verification), deployment manifests added (opportunity for release observability pack), higher-risk production changes (opportunity for strict safety defaults and explicit action classification).

Additional examples: a team adopts remote operator approval and progress visibility through agent-intercom (opportunity for the `agent-intercom` capability pack and intercom-woven workflow guidance).

Additional examples: a team adopts agent-engram for code graph indexing and workspace memory (opportunity for the `agent-engram` capability pack and engram-first search guidance).

Additional examples: a team standardizes on backlogit as its AI-native system of record (opportunity for the `backlogit` capability pack and deeper backlogit-native workflow guidance).

Additional examples: a team wants recurring practice captured as explicit repository knowledge (opportunity for the `continuous-learning` capability pack and the observe / learn / evolve workflow).

Additional examples: a product starts exposing MCP tools or agent-facing actions that must stay aligned with user-visible flows (opportunity for the `agent-native-parity-reviewer` persona).

Additional examples: discovery now detects additive stack packs such as `web-app`, `api-service`, or `mcp-server`, creating an opportunity to clarify install layers and composition reasoning in the resolved config and manifest.

**Action**: Evaluate and implement when beneficial.

### Cosmetic

Functional but may cause minor confusion. Version numbers updated, minor naming changes, additional config files added.

**Action**: Fix in batch during maintenance windows.

## Deterministic Artifact Drift Scanning

During tuning, autoharness re-hashes every manifest-tracked artifact and
classifies it before generating proposals.

| Classification | Meaning |
|---|---|
| `missing` | The manifest expects the artifact, but the file is gone |
| `user-modified` | The file exists, but its checksum no longer matches the installed manifest |
| `unchanged` | The file still matches the installed manifest |
| `ignored` | The file matches a pattern in `.autoharness/drift-ignore` and is treated as an intentional local customization |

Use `.autoharness/drift-ignore` to suppress known local harness customizations
that should not be treated as accidental drift. Ignored files should still be
reviewed occasionally, but they should not drown out genuine breakage.

## Schema Contract Compatibility

The installed `.autoharness/config.yaml`, `.autoharness/workspace-profile.yaml`,
and `.autoharness/harness-manifest.yaml` files are versioned contracts, not
just YAML blobs to parse once.

Use deterministic verification as the system of record for contract state:

```text
autoharness verify-workspace --workspace {workspace_path} --autoharness-home {autoharness_home} --json
```

Review these fields from the JSON report before proposing tune changes:

* `schema_contracts{}` — observed version, current version, and contract status
* `migration_proposals[]` — upgrade, backfill, and normalization proposals
* `warnings[]` — compatibility drift evidence, including grouped summaries when repeated findings collapse into fewer warning rows

The current config contract is `1.1.0`; the workspace profile and harness
manifest contracts are `1.0.0`. autoharness also recognizes `0.9.0` as a known
legacy version for all three, and `1.0.0` as a known legacy config version.
Those workspaces should generate explicit upgrade proposals instead of being
treated as unknown-contract failures.

| Contract status | Meaning | Tuning action |
|---|---|---|
| `current` | Installed file matches the current contract | Normal drift detection only |
| `known-legacy` | Installed file matches a recognized older contract such as `0.9.0` | Present an upgrade proposal with the observed and target versions |
| `missing-version` | Installed file omits `schema_version` | Treat as degraded legacy state and propose backfill or regeneration |
| `unknown-version` | Installed file claims an unrecognized contract | Stop auto-apply and require manual review |

Repeated compatibility findings may appear in CLI and Markdown output as
grouped warning summaries. When that happens, review both the grouped warning
count and the underlying finding count so a high-volume compatibility problem is
not mistaken for a single isolated warning.

## Agent and Skill Frontmatter Contract

The YAML frontmatter keys that agents and skills may, must, and must not carry
are defined once, in `src/autoharness/frontmatter_contract.py`. The
`verify-workspace` `frontmatter_conformity` targeted check, the repository's
template conformity test, and the tune-harness Step 1.5c migration all read that
single definition.

### Routing Key Constants

| Constant | Keys |
|---|---|
| `TIER_KEYS` | `max_subagent_tier`, `subagent_depth` |
| `ROUTE_VALUE_KEYS` | `model_family`, `model_provider`, `reasoning_effort`, `context_tier`, `anchor_review_family`, `anchor_review_provider`, `anchor_review_reasoning_effort`, `alt_review_family`, `alt_review_provider`, `alt_review_reasoning_effort` |
| `routing_keys()` | `max_subagent_tier`, `subagent_depth`, `model_family`, `model_provider`, `reasoning_effort`, `context_tier`, `anchor_review_family`, `anchor_review_provider`, `anchor_review_reasoning_effort`, `alt_review_family`, `alt_review_provider`, `alt_review_reasoning_effort` |

The shared routing-key set is the union of `TIER_KEYS` and `ROUTE_VALUE_KEYS`.
It is computed at call time by `routing_keys()` rather than stored as a
separate literal, so extending the contract with a new route-value key is a
single edit to `ROUTE_VALUE_KEYS`. A bare `model:` key is never valid on any
agent or skill.

### Key Sets by Profile

| Artifact | Required keys | Optional keys | Forbidden keys |
|---|---|---|---|
| Agent, `tier-routed` | `name`, `description`, `max_subagent_tier`, `subagent_depth`, `model_family`, `model_provider`, `reasoning_effort` | `id`, `maturity`, `tools`, `argument-hint`, `handoffs`, `target`, `context_tier`, `anchor_review_family`, `anchor_review_provider`, `anchor_review_reasoning_effort`, `alt_review_family`, `alt_review_provider`, `alt_review_reasoning_effort` | `model` |
| Agent, `plugin-global` | `name`, `description`, `max_subagent_tier`, `subagent_depth` | `id`, `maturity`, `tools`, `argument-hint`, `handoffs`, `target` | `model`, `model_family`, `model_provider`, `reasoning_effort`, `context_tier`, `anchor_review_family`, `anchor_review_provider`, `anchor_review_reasoning_effort`, `alt_review_family`, `alt_review_provider`, `alt_review_reasoning_effort` |
| Skill | `name`, `description` | `argument-hint`, `input`, `license`, `compatibility`, `metadata`, `allowed-tools` | `model`, `max_subagent_tier`, `subagent_depth`, `model_family`, `model_provider`, `reasoning_effort`, `context_tier`, `anchor_review_family`, `anchor_review_provider`, `anchor_review_reasoning_effort`, `alt_review_family`, `alt_review_provider`, `alt_review_reasoning_effort` |

An agent is checked against the `plugin-global` profile only when all of the
following hold; every other agent is `tier-routed`:

* the harness manifest records `install_mode: "self-install"` (autoharness
  verifying its own source repository);
* the workspace-root `plugin.json` is a regular file inside the workspace —
  not a symlink or reparse point — that parses as a JSON object;
* its `name` is exactly `autoharness`; and
* its `agents[]` (a list of strings) lists the agent's workspace-relative path.

When `plugin.json` is a symlink or reparse point, is not a regular file,
resolves outside the workspace, is unreadable or invalid JSON, is not a JSON
object, or has a malformed `agents[]`, verify does not trust it: it emits one
`frontmatter-conformity-plugin-json` warning and treats the plugin-agent set as
empty, so every agent fails safe to `tier-routed`. A missing `plugin.json`, a
different `name`, or any other `install_mode` selects `tier-routed` silently,
with no warning.

Skills are leaf executors (P-013.5): they inherit the invoking agent's route
and carry no routing key.

Value rules:

* `max_subagent_tier` is an integer from 1 to 3, and `subagent_depth` is a
  non-negative integer.
* `name`, `description`, and `model_family` are non-empty strings. The
  provider, reasoning-effort, `anchor_review_family`, and `alt_review_family`
  keys are strings and may be empty.
* `context_tier` is optional on a `tier-routed` agent and, when present, is
  exactly `default` or `long_context`. An empty value (`""`, which means
  unset/inherit in config) is never valid in frontmatter.
* A skill's `name` equals its directory name, matches
  `^[a-z0-9]+(-[a-z0-9]+)*$`, and is at most 64 characters long.
* An installed artifact must not contain an unresolved `{{...}}` placeholder.
* A key outside every set is reported as `FM_UNKNOWN_KEY`, which is
  informational only and never fails verification.

### Plugin-Global Agents

Plugin-distributed agents (for example `auto-tune` and `auto-mergeinstall`) are
shipped verbatim and are never install-rendered. They declare only the tier
keys — `max_subagent_tier`, the ceiling for the subagents they dispatch, and
`subagent_depth` — plus the tier statement in their persona body ("operates at
Tier N"). They carry no route-value frontmatter and run on the operator's
session model. There is no automatic route resolution for them: autoharness does
not claim to select or enforce a model for a plugin-global agent.

### Provenance Classes

`verify-workspace` classifies each agent and skill file by provenance before it
decides how a nonconformant file is reported:

| Class | Provenance | Verify outcome | Tune migration |
|---|---|---|---|
| `managed-rendered` | Manifest `artifacts[]` entry whose source template resolves to an existing file inside autoharness `templates/` | Fails closed | `rerender`, or `source-repair` when the template itself is defective (see the preconditions below) |
| `managed-community` | `community_templates[]` entry (matched by `installed_path`) | Fails closed | `reinstall-community`, or `source-repair` |
| `managed-source` | `artifacts[]` entry labeled `global agent definition` or `global skill definition` (autoharness's own source-controlled definitions) | Fails closed | Single-key frontmatter edits |
| `workspace-authored` | Not tracked by the harness manifest (`artifacts[]` or `community_templates[]`), or an `artifacts[]` entry labeled `workspace merge install` or `workspace deliberation template` | Advisory warning; never fails verification | Single-key edits, only with per-proposal operator approval |
| `unknown-provenance` | `artifacts[]` entry with any other label whose source template does not resolve to an existing file inside autoharness `templates/` | Advisory warning | Single-key edits, only with per-proposal operator approval |

Managed files fail closed regardless of checksum status: a `user-modified` or
`ignored` checksum does not excuse a nonconformant managed file.

Workspace-authored agents, such as a project's own `sqlite-reviewer` review
persona, are preserved and reported, not rewritten. Their findings appear as
advisory warnings and migration proposals that the operator approves one at a
time.

### Frontmatter Migration

Every blocking finding yields a `contract: frontmatter-conformity` entry in
`migration_proposals[]` with `from_version: null` and `to_version: fc-1`.
tune-harness promotes these in Step 1.5c:

* managed findings (`severity: P1`) are **Breaking** drift, and
  workspace-authored or unknown-provenance findings (`severity: P2`) are
  **Degrading** drift;
* each proposal carries one action — `rerender`, `reinstall-community`,
  `source-repair`, `manual-fix`, `migrate-key`, `remove-key`, `add-key`, or
  `replace-value`. `source-repair` and `manual-fix` are report-only, and the
  four key-level actions edit a single frontmatter key while preserving the
  body;
* `rerender` (managed-rendered) and `reinstall-community` (managed-community)
  are proposed only when the file has no path-escape finding, its checksum
  status is `unchanged`, and the freshly rendered source candidate passes the
  conformity check. When that candidate fails the check or cannot be produced,
  the action is `source-repair`, naming the defective template, whatever the
  checksum status. When the candidate passes but the file is not `unchanged`
  (for example `user-modified`), key-level actions are proposed instead;
* `reinstall-community` refreshes both the `installed_checksum` and the
  `source_checksum` of the community-template entry;
* `migrate-key` and `remove-key` proposals, every `manual_review: true`
  proposal, and every proposal against a workspace-authored or user-modified
  file need per-proposal operator approval;
* a bare `model:` → `model_family` migration never invents `model_provider`;
  a missing provider is supplied by the operator.

## Model Routing and Context Tier

Each `model_routing` route in `.autoharness/config.yaml` (`tier1`, `tier2`,
`tier3`, `orchestrator`, `stage`, `ship`, and the escalation routes) may carry
an optional `context_tier` beside `model_family`, `model_provider`, and
`reasoning_effort`. The frontmatter key sets and value rules for `context_tier`
are defined in the [Agent and Skill Frontmatter Contract](#agent-and-skill-frontmatter-contract)
tables above; this section covers how the value is resolved and used.

### Values and Fallback

`context_tier` is a provider- and environment-agnostic capacity class:

* `default` — the runtime's normal context window;
* `long_context` — a larger context window, where the runtime offers one;
* `""` (empty) or an absent key — unset; in config only, this means "inherit".
  An empty value is never valid in agent frontmatter.

Resolution is per sub-field, like the other route fields:

* `tier1`, `tier2`, and `tier3` resolve an unset value, or a legacy string-form
  tier, to `default`.
* `ship` falls back to `tier2`, then `default`. `stage` falls back to `tier3`,
  then `default`. `orchestrator` (object form) falls back to `tier2`, then
  `default`. The plain-string `orchestrator` form (for example
  `orchestrator: "gpt-5.4"`) carries no `context_tier`, so it also resolves
  from `tier2`, then `default`.
* The install write-back stores each resolved role value in config, so an
  inherited value becomes explicit after install.

Declaring `context_tier` anywhere in config requires `schema_version: "1.1.0"`;
the `1.0.0` config schema rejects the key.

### Escalation Variables: Raw Versus Resolved

The escalation route has one resolved variable and three raw variables:

| Variable | Kind | Source |
|---|---|---|
| `{{ESCALATION_CONTEXT_TIER}}` | resolved | the acting role's nested `<role>.escalation.context_tier`, else the legacy flat `escalation.context_tier` (only when the flat route is the selected escalation source), else `tier3`, else `default` |
| `{{LEGACY_ESCALATION_CONTEXT_TIER}}` | raw | `model_routing.escalation.context_tier`, as written |
| `{{STAGE_ESCALATION_CONTEXT_TIER}}` | raw | `model_routing.stage.escalation.context_tier`, as written |
| `{{SHIP_ESCALATION_CONTEXT_TIER}}` | raw | `model_routing.ship.escalation.context_tier`, as written |

The resolved variable is prose-only guidance for the escalation handoff. The raw
variables are never resolved or defaulted: they exist so the config write-back
preserves exactly what the operator declared, and escalation inheritance keeps
working after install. A nested escalation block that declares only
`context_tier` never selects the nested source on its own.

### Runtime Behavior

* The Orchestrator declares the resolved `context_tier` in the Stage and Ship
  invocation override. When the runtime cannot honor a non-`default` tier, the
  agent records `ROUTING_DEGRADED: context_tier` and proceeds at the default
  context without halting.
* The escalation handoff records the escalation tier in its own
  `resolved_escalation_context_tier` field. It is not part of the resolved
  escalation route tuple, so it is excluded from the same-route guard: two
  routes that differ only in `context_tier` are still the same route, and an
  unhonored tier never declares `ESCALATION_DEGRADED`.
* Plugin-distributed (`plugin-global`) agents, such as `auto-tune` and
  `auto-mergeinstall`, carry no `context_tier` and run on the operator's
  session model. `context_tier` applies only to installed `tier-routed` agents.

### Verification and Migration

* When the config is valid and `model_routing` is a mapping, `verify-workspace`
  treats the live config as authoritative for route variables. Precedence is
  `config.overrides`, then config, then the manifest's recorded
  `variables_used`.
* When a manifest-recorded route variable differs from that authoritative value,
  verify emits a non-fatal `ROUTE_VARIABLE_STALE:<VAR>` warning. It means the
  manifest snapshot is out of date, not that routing is broken. To clear it,
  re-run install or apply a tune re-render so `variables_used` is refreshed.
* The Orchestrator invocation directive check now requires `context_tier` and
  `ROUTING_DEGRADED: context_tier` at both the Stage and Ship invocation steps.
  An `_orchestrator.agent.md` rendered before this release fails that check
  until it is re-rendered through tune.

### Ship Route Default

On a first install, install-harness applies the fresh-install Ship seed
(install-harness Step 1.2). The seed fires only when the target has no harness
manifest yet, the operator input has no `model_routing.ship` key at all, and no
`SHIP_*` template-variable override is set. The seeded route, including its
`context_tier`, is then written back to config, so later installs, verifies, and
tunes read it as an explicit Ship route and never re-apply the seed.

Tune follows a no-silent-change posture for existing workspaces (tune-harness
Step 1.5d):

* tune surfaces an informational, opt-in "new generic Ship default available"
  proposal only when `model_routing.ship` declares no non-empty
  `model_family`;
* an explicitly declared Ship route is an operator override, and tune never
  proposes replacing it. Because the install write-back stores the resolved
  Ship family, every non-empty value counts as an override, so existing
  workspaces normally never see the proposal;
* tune never auto-applies the proposal, even with `auto_apply`.

To adopt the new generic Ship default in an existing workspace, edit
`model_routing.ship` in `.autoharness/config.yaml` to the seed route documented
in install-harness Step 1.2, then re-run install or tune.

## Manual Tuning

All harness artifacts are regular Markdown files. You can edit them directly:

* **Instructions**: Adjust `applyTo` patterns, add/remove rules
* **Agents**: Update tool lists, modify behavioral constraints, adjust model routing
* **Skills**: Change build/test commands, adjust circuit breaker limits
* **Skill Packs**: Enable richer verification or safety packs without redesigning the harness
* **Intercom Weaving**: Thread agent-intercom heartbeat, broadcast, approval, and standby guidance through the affected artifacts rather than adding a single isolated note
* **Continuous Learning**: Keep the observation lifecycle explicit by tuning `continuous-learning.instructions.md` and the `observe` / `learn` / `evolve` skills together
* **Strict Safety**: Tune `strict-safety.instructions.md`, `plan-harden`, `safety-modes`, review, and closure guidance together so risky actions stay legible across the workflow
* **Conditional Reviewers**: Install or retarget `agent-native-parity-reviewer.agent.md` when agent-facing product surfaces appear
* **Local Review Migration**: Tune workflow policies, `review/SKILL.md`, `pr-lifecycle`, and GitHub PR automation instructions together so the local readiness contract covers the current HEAD and Copilot stays advisory during migration
* **Policies**: Add new policies or modify existing gate conditions
* **Constitution**: Update quality gates, change error handling patterns

After manual changes, run the tuner to verify consistency.

## Best Practices

1. **Tune after every major change**, not just when agents start failing
2. **Review tuning reports** even when auto-applying — understand what changed
3. **Keep backups** — the tuner creates them automatically in `.autoharness/backups/`
4. **Test agents after tuning** — run a simple task through the pipeline to verify
5. **Track tuning history** — the manifest records when and what was tuned
6. **Use drift-ignore sparingly** — only for intentional local divergence, not as a way to hide real harness breakage
7. **Review tune output from a feature branch** — keep accepted changes on a feature branch or as local uncommitted work until they are ready for pull-request review
