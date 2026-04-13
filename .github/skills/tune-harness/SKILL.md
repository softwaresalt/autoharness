---
description: "Maintenance and tuning workflow that iteratively adapts an installed agent harness to match the current state of a codebase as it evolves"
---

## Tune Harness

Analyze an installed agent harness against the current workspace state, detect drift, and propose targeted updates to keep the harness aligned with codebase evolution. Tuning is a non-destructive process: it proposes changes for review rather than silently overwriting artifacts.

autoharness operates as a globally-installed tool. Templates for regenerating artifacts are read from the autoharness home directory; only updated harness artifacts are written to the target workspace.

## When to Use

Invoke this skill periodically or when significant codebase changes occur:

* New languages, frameworks, or build tools added to the project
* Major directory restructuring
* CI/CD pipeline changes
* New runtime surfaces (web UI, API, background jobs, deployment manifests)
* agent-intercom configuration added, removed, or partially woven into the workspace
* agent-engram configured, removed, or partially woven into the workspace
* backlogit detected or upgraded but the harness still only uses generic backlog CRUD guidance
* After a large feature merge that introduces new patterns or conventions
* When agent behavior becomes noticeably less effective
* At regular intervals (recommended: monthly or after every major release)

## Inputs

* `autoharness_home`: (Required) Absolute path to the autoharness installation (contains `templates/`, `schemas/`). Resolved by the invoking agent via: `AUTOHARNESS_HOME` env var → `autoharness home` CLI → agent directory traversal → `~/.autoharness/`.
* `workspace_path`: (Required) Absolute path to the target workspace root.
* `scope`: (Optional) Comma-separated list of tune targets: `instructions`, `agents`, `skills`, `policies`, `constitution`, `all`. Defaults to `all`.
* `auto_apply`: (Optional, default false) When true, apply proposed changes without interactive review.

## Output

* Tuning report at `.autoharness/tuning-reports/{YYYY-MM-DD}-tuning-report.md`
* Updated harness artifacts (if changes accepted)
* Updated harness manifest

## Required Protocol

### Phase 0: Validate autoharness Home

Verify the `autoharness_home` path contains the expected structure:

* `{autoharness_home}/templates/` — template files for artifact regeneration
* `{autoharness_home}/schemas/` — JSON schemas for validation

If any are missing, halt and report the issue. All template reads for regenerating artifacts use `{autoharness_home}/templates/` as the base path.

### Phase 0b: Load Operator Configuration

Read `.autoharness/config.yaml` from the target workspace (if present). The operator config represents the intended harness configuration. During tuning, it serves two purposes:

1. **Intent comparison**: If the operator config specifies preferences that differ from what's currently installed, those are intentional tuning targets (not drift)
2. **Override preservation**: When regenerating artifacts, operator config values take precedence over both auto-detected values and previously installed values

If the config was modified since the last installation (compare against the manifest's recorded config hash), flag this as an intentional configuration change and prioritize it in the tuning report.

#### Step 0b.1: Config Schema Validation

Validate the loaded config against `{autoharness_home}/schemas/harness-config.schema.json`. For each discrepancy, classify as:

| Discrepancy | Classification | Action |
|---|---|---|
| Unknown top-level key | Warning | Report in tuning output; may indicate a renamed key |
| Unknown nested key that matches a renamed schema key | Migration | Generate a config-key migration proposal (P1 Degrading) |
| Missing required key | Error | Halt tuning and report |
| Value type mismatch | Warning | Report in tuning output |
| Map object missing entries that have schema defaults | Backfill | Generate a config-backfill proposal (P1 Degrading) |

**Config-key migration**: When a config key matches a known rename (e.g., `prefix_map` → `suffix_map`), generate a migration proposal that:

1. Renames the key in `.autoharness/config.yaml` while preserving all child values
2. Backs up the original config to `.autoharness/backups/{YYYY-MM-DD}/`
3. Updates the manifest's config hash after migration
4. Classifies as P1 Degrading because downstream template variable resolution may silently fall back to defaults when the old key name is present

Known config-key renames:

| Old Key Path | Current Key Path | Renamed In |
|---|---|---|
| `backlog.prefix_map` | `backlog.suffix_map` | v1.0.0 |

**Config-entry backfill**: When a map object in the config (e.g., `backlog.suffix_map`, `docs.subdirectories`) is present but missing entries that the schema defines with defaults, generate a backfill proposal that:

1. Adds the missing entries using the schema default values
2. Preserves all existing operator-specified values unchanged
3. Backs up the original config to `.autoharness/backups/{YYYY-MM-DD}/`
4. Updates the manifest's config hash after backfill
5. Classifies as P1 Degrading because templates referencing the missing entries (e.g., `{{SUFFIX_EPIC}}`, `{{SUFFIX_CHORE}}`) resolve to defaults during install but are invisible in the operator config, creating a silent divergence between what the config declares and what the harness uses

For `backlog.suffix_map`, the canonical entry set is defined by the schema:

| Entry | Default | Purpose |
|---|---|---|
| `feature` | `F` | Feature work items |
| `chore` | `C` | Maintenance/housekeeping work items |
| `task` | `T` | Individual task units |
| `spike` | `S` | Time-boxed investigation |
| `deliberation` | `D` | Structured decision capture |
| `bug` | `B` | Defect tracking |
| `epic` | `E` | Multi-feature grouping |
| `subtask` | `ST` | Task subdivision |
| `shipment` | `S` | Lifecycle envelope grouping work items for release |

Any entry present in the schema but absent from the config is a backfill candidate. The backfill proposal must list each missing entry and its default value so the operator can accept or override.

### Phase 1: Drift Detection

#### Step 1.1: Re-run Workspace Discovery

Invoke the workspace-discovery skill with `existing_profile` set to the current `.autoharness/workspace-profile.yaml`. This produces a fresh profile with a drift report comparing current state against the installed profile.

#### Step 1.2: Categorize Drift

Classify each detected change by impact and urgency:

| Drift Category | Impact | Examples |
|---|---|---|
| **Breaking** | Harness references are invalid | Removed build tool, renamed source directory, deleted CI pipeline |
| **Degrading** | Harness works but is suboptimal | New framework added without instructions, new test patterns without review persona, config key renamed but old key still present, suffix_map missing entries that schema defines |
| **Cosmetic** | Function unaffected | Minor version bumps, additional config files |
| **Growth** | New capabilities to harness | New languages in project, new documentation patterns |

Include any config-key migration and config-entry backfill proposals from Step 0b.1 as **Degrading** drift entries. Config migrations and backfills are applied in Phase 4 alongside other accepted proposals.

#### Step 1.3: Deterministic Artifact Drift Scan

Use `.autoharness/harness-manifest.yaml` as the source of truth for installed
generated artifacts:

* re-hash every manifest-listed artifact that still exists
* classify at least:
  * `missing`
  * `user-modified`
  * `unchanged`
* support ignore patterns from `.autoharness/drift-ignore`; classify matching
  paths as `ignored` rather than surfacing them as drift
* record per-artifact path, manifest checksum, current checksum, classification,
  and reason

Record the result under `drift_report.checksum_scan{}` so later proposals can
distinguish broken installs from intentional local customization.

#### Step 1.4: Scan Harness Artifact Health

For each installed artifact, check:

* **Instruction files**: Do `applyTo` glob patterns match files that still exist?
* **Agent files**: Do referenced skills, tools, and file paths resolve?
* **Skill files**: Do build/test/lint commands match current tooling?
* **Compound library**: Are existing learnings stale, duplicated, contradicted by current code, or strong candidates for `compound-refresh`?
* **Policies**: Do referenced agents and gate points still apply?
* **Constitution**: Do technology-specific rules match the current stack?
* **AGENTS.md**: Do quality gates and commands match current tooling?
* **Backlog registry**: Does the registered backlog tool still match the installed tool? Has the tool been switched?
* **Runtime verification and closure skills**: Do they match the current runtime surfaces and deployment model?
* **Risky-plan hardening coherence**: Verify the plan-hardening pipeline is consistent:
  1. impl-plan template still includes the `Plan Hardening Signals` section and concludes with `Requires plan hardening: yes|no`
  2. stage agent Step 3 references the `Requires plan hardening` conclusion and invokes plan-harden when `yes`
  3. plan-harden template references `{{DOCS_PLANS}}/` and appends a `## Plan Hardening` section
  4. plan-review Step 1 extracts hardening signals and the gate decision table includes the hardening-required-but-missing FAIL condition
  If any of these four checks fail, flag as P1 Degrading drift.
* **Agent-intercom weaving**: If intercom markers exist, do AGENTS.md, copilot-instructions, relevant agents, and relevant skills consistently reference heartbeat, broadcast, approval-routing, and degraded-mode handling?
* **Agent-engram weaving**: If engram markers exist, do AGENTS.md, copilot-instructions, relevant agents, and relevant skills consistently reference engram-first search, workspace binding, and freshness / fallback behavior?
* **backlogit weaving**: If backlogit is the selected backlog tool, do instructions and backlog-aware agents consistently reference queue, query, dependency, memory, checkpoint, or traceability behaviors?
* **Browser-verification weaving**: If browser tooling and web UI surfaces exist, do AGENTS.md, copilot-instructions, runtime verification, operational closure, and the browser-verification instruction file consistently reference server readiness, route selection, headed/headless choice, and human checkpoints?
* **Continuous-learning weaving**: If the pack is enabled, do AGENTS.md, copilot-instructions, the continuous-learning instruction file, and the `observe` / `learn` / `evolve` skills consistently reference observation capture, instinct formation, and promotion thresholds?
* **Strict-safety weaving**: If the pack is enabled, do AGENTS.md, copilot-instructions, `strict-safety.instructions.md`, `safety-modes`, `plan-harden`, review, and closure workflows consistently reference `ProposedAction`, `ActionRisk`, `ActionResult`, and approval expectations?
* **Release-observability weaving**: If the pack is enabled, do AGENTS.md, copilot-instructions, `release-observability.instructions.md`, operational-closure, and runtime-verification consistently reference monitoring plans, observation windows, and rollback triggers?
* **Agent-native parity reviewer**: If MCP or parity-sensitive agent tooling is now present, does the review layer install and route `agent-native-parity-reviewer.agent.md` where appropriate?
* **Script artifacts**: For each manifest-recorded script artifact (acquire_lock.ps1/.sh, release_lock.ps1/.sh, search.ps1/.sh):
  1. Verify the file exists at `{workspace_path}/scripts/{script_name}`
  2. Compare checksum to manifest value
  3. Classify as `missing`, `user-modified`, or `unchanged`
  4. Flag missing scripts as P0 Breaking drift — agents referencing these scripts will fail at runtime
  5. If `concurrency.instructions.md` is installed but lock scripts are missing, flag as P0 Breaking
  6. If `skill-search/SKILL.md` is installed but `search.ps1`/`search.sh` is missing, flag as P0 Breaking
* **Circuit breaker and concurrency instructions**: If these instruction files are installed:
  1. Verify they are referenced from the constitution's Stop Conditions section
  2. Verify the `.gitignore` contains an autoharness dot-lock ignore pattern (for example `.*.lock` or `**/.*.lock`) when concurrency instructions are present; do not require a broad `*.lock` pattern because that would ignore legitimate repository lockfiles such as `Cargo.lock` or `poetry.lock`
  3. Verify AGENTS.md contains the Foundational Protocols table referencing these instructions
* **Deprecated agents**: If deprecated agent files are found in `.github/agents/` that match AGENTS.md's deprecation table, flag as P2 Degrading drift and propose removal with a note that the functionality has been absorbed into the active agent/skill set.

Record: `health_report{}` with per-artifact status and any `compound-refresh`
recommendations for stale institutional knowledge.

#### Step 1.5: Backlog Tool Migration Detection

Compare the currently registered backlog tool (from `.autoharness/backlog-registry.yaml`) against what workspace-discovery detected:

| Scenario | Category | Action |
|----------|----------|--------|
| Same tool, no changes | Healthy | No action needed |
| Same tool, config changed | Degrading | Update registry with new status values, features |
| Tool switched (e.g., backlog-md → backlogit) | Breaking | Generate migration proposal |
| Tool removed | Breaking | Propose fallback to manual backlog or new tool registration |
| New tool added (was manual/none) | Growth | Propose tool registration |

**Migration proposal** (tool switch) includes:

1. Replace `.autoharness/backlog-registry.yaml` with the new tool's registry
2. Update `backlog-integration.instructions.md` with new operation names
3. Update all agent files that reference backlog MCP tool names
4. Update all skill files that reference backlog operations
5. Update status values throughout (e.g., `queued` → `To Do`)
6. Map the directory structure if different (e.g., `.backlogit/` → `backlog/`)
7. Do NOT migrate task data — that is the backlog tool's responsibility

#### Step 1.6: Preset, Stack-Pack, Layer, and Capability-Pack Drift

Compare the installed preset, primary stack pack, additive stack packs, install
layers, and capability packs in `.autoharness/harness-manifest.yaml` against the
current workspace profile recommendations:

| Scenario | Category | Action |
|----------|----------|--------|
| Same preset, stack packs, layers, and packs still appropriate | Healthy | No action needed |
| Primary stack pack shifted (for example `library` -> `web-app`) | Growth or Degrading | Propose recomposing install layers and any affected guidance |
| Additive stack packs changed materially | Growth or Degrading | Propose updating the recorded composition model and any affected recommendations |
| Installed layers no longer match recommended layers | Growth or Degrading | Propose expanding or reducing the affected artifact classes |
| Same preset, missing recommended pack | Growth | Propose enabling the pack |
| Installed pack no longer matches runtime surfaces | Cosmetic or Degrading | Propose disabling or retargeting the pack |
| agent-intercom markers detected but `agent-intercom` pack missing | Growth or Degrading | Propose enabling the pack and weaving intercom guidance through the harness |
| agent-engram markers detected but `agent-engram` pack missing | Growth or Degrading | Propose enabling the pack and weaving engram-first search guidance through the harness |
| backlogit detected as the active backlog tool but `backlogit` pack missing | Growth or Degrading | Propose enabling the pack and weaving backlogit-native workflows through the harness |
| Browser tooling and web UI detected but `browser-verification` pack missing | Growth or Degrading | Propose enabling the pack and weaving browser-verification guidance through runtime verification and closure |
| Recurring observation/learning workflow desired but `continuous-learning` pack missing | Growth | Propose enabling the pack and installing observe / learn / evolve workflows |
| Elevated runtime, migration, or security risk detected but `strict-safety` pack missing | Growth or Degrading | Propose enabling the pack and weaving explicit action classification through risky workflows |
| Risky-plan hardening guidance missing or stale | Degrading | Propose retuning stage, plan-harden, and plan-review together so risky plans are hardened before harvest |
| Starter preset on a repo that now has complex runtime surfaces | Growth | Propose moving to `standard` or `full` |

Use the profile's structured recommendation reasons when available so proposals
can explain **why** the preset, layers, or packs changed rather than only
listing the new target values.

#### Step 1.7: Overlay-Coherence Drift

For every enabled capability pack, compare the manifest's declared overlay targets against the currently installed artifacts.

Flag drift when:

* the pack is enabled but one or more declared target artifacts are missing
* only some of the targeted artifacts mention the pack's behavior delta
* the workspace still contains woven overlay guidance after the pack was removed
* the workspace now exposes new eligibility signals that should expand the overlay target set

Treat partially woven overlays as a first-class drift category rather than a cosmetic doc mismatch.

Separately, treat conditional reviewer drift as real harness drift when the
workspace now requires parity-sensitive review but the review layer still lacks
`agent-native-parity-reviewer.agent.md` or the routing logic to invoke it.

### Phase 2: Change Proposal Generation

#### Step 2.1: Priority Ranking

Rank proposed changes by impact:

1. **P0 — Breaking**: Artifacts that reference non-existent files, tools, or commands
2. **P1 — Degrading**: Artifacts that work but produce suboptimal agent behavior
3. **P2 — Growth**: Opportunities to extend the harness for new capabilities
4. **P3 — Cosmetic**: Minor alignment improvements

#### Step 2.2: Generate Change Proposals

For each detected issue, generate a specific change proposal:

```yaml
- id: "TUNE-001"
  priority: "P0"
  category: "breaking"
  artifact: ".github/instructions/rust.instructions.md"
  issue: "References clippy lint 'clippy::unwrap_used' but project now uses Python"
  proposal: "Replace with python.instructions.md using ruff/mypy conventions"
  diff_preview: |
    - applyTo: '**/*.rs'
    + applyTo: '**/*.py'
```

Checksum-based drift findings should cite whether the artifact is `missing`,
`user-modified`, or `ignored` so the operator can tell whether the proposal is
recovery, retuning, or intentional local divergence.

When discovery produced recommendation reasons, include the relevant preset,
install-layer, or capability-pack rationale in the proposal body so operators can
see the causal signals behind the retune.

#### Step 2.3: Detect New Primitive Opportunities

Scan for workspace patterns that suggest missing harness capabilities:

* Database access code without a database reviewer persona
* API endpoint code without an API review persona
* Security-sensitive patterns (auth, crypto, input validation) without security review
* Infrastructure-as-code files without IaC instructions
* Containerization (Dockerfile, docker-compose) without container instructions
* Web UI or API runtime surfaces without matching runtime verification or operational closure guidance
* Remote operator workflow markers without matching agent-intercom guidance in the harness
* agent-engram markers or `.engram/` state without matching engram-first search guidance in the harness
* backlogit-specific features available without matching backlogit-native guidance in the harness
* Browser automation tooling without the browser-verification overlay
* MCP or agent-facing product surfaces without the agent-native parity reviewer
* Repeated recurring-practice evidence without the continuous-learning overlay
* High-risk runtime or migration work without strict-safety or plan-hardening guidance

### Phase 3: Proposal Review

#### Step 3.1: Present Tuning Report

Generate and display the tuning report:

```markdown
## Harness Tuning Report — {{DATE}}

### Drift Summary
- Breaking changes: {{count}}
- Degrading changes: {{count}}
- Growth opportunities: {{count}}
- Cosmetic adjustments: {{count}}

### Composition
- Installed primary stack pack: {{INSTALLED_PRIMARY_STACK_PACK}}
- Current primary stack pack: {{CURRENT_PRIMARY_STACK_PACK}}
- Installed stack packs: {{INSTALLED_STACK_PACKS}}
- Current stack packs: {{CURRENT_STACK_PACKS}}
- Installed layers: {{INSTALLED_INSTALL_LAYERS}}
- Recommended layers: {{RECOMMENDED_INSTALL_LAYERS}}

### Checksum Scan
- Missing installed artifacts: {{count}}
- User-modified artifacts: {{count}}
- Ignored artifacts: {{count}}

### Proposed Changes (ordered by priority)

#### P0 — Breaking
1. [TUNE-001] Replace rust.instructions.md with python.instructions.md
   ...

#### P1 — Degrading
...

### Recommendation
{{SUMMARY_RECOMMENDATION}}
```

#### Step 3.2: Interactive Review

Unless `auto_apply` is true, present each P0 and P1 change for user approval:

* Show the current artifact content and proposed change
* Accept, reject, or modify each proposal
* Batch-accept P2/P3 changes or review individually

### Phase 4: Apply Changes

#### Step 4.1: Apply Accepted Changes

For each accepted proposal:

1. Back up the existing artifact to `.autoharness/backups/{YYYY-MM-DD}/`
2. Apply the change
3. Update the harness manifest with the new artifact checksum

#### Step 4.2: Generate New Artifacts

If growth opportunities were accepted (new review personas, new instructions, new skills):

1. Generate from templates using the current workspace profile
2. Install to the appropriate directory
3. Update cross-references in AGENTS.md and copilot-instructions.md
4. Update manifest preset / stack-pack / install-layer / capability-pack metadata when installation shape changes
5. Update manifest overlay-target metadata when the pack's woven surface changes
6. If the workspace now requires the agent-native parity reviewer, install the
   reviewer agent and update plan-review / review routing guidance together
7. If risky-plan hardening or strict-safety expectations changed, update
   `plan-harden`, safety-mode, review, and closure artifacts together rather
   than patching only one surface

#### Step 4.3: Update Manifest

Update `.autoharness/harness-manifest.yaml`:

* Bump the `tuned_at` timestamp
* Record which proposals were applied
* Update artifact checksums
* Store the new workspace profile hash
* Store the new primary stack pack, additive stack packs, install layers, preset, and capability-pack metadata when composition changed

### Phase 5: Verification

Run the same verification algorithm as the install-harness skill Phase 4:

* **Step 4.1 (Template Variable Sweep)** — scan for unresolved `{{...}}` outside code fences
* **Step 4.2 (Cross-Reference Sweep)** — verify agent→skill, agent→tool, instruction→file, policy→agent, constitution→language, and layer→artifact consistency
* **Step 4.3 (Overlay Coherence Sweep)** — verify each enabled pack's targets exist and reference the pack's behavior keywords
* **Step 4.4 (Structural Validation)** — YAML frontmatter, code fence pairing, table column counts, file path resolution

After deterministic checks pass, invoke the **verify-harness** skill for
multi-model adversarial verification:

* **Step 4.5 (Adversarial Verification)** — dispatch parallel reviewer
  subagents using different models to audit template fidelity, overlay
  coherence, and cross-reference integrity against the authoritative templates
  and the workspace's current state. Findings are assembled into a
  confidence-weighted consensus report. HIGH-confidence additive fixes are
  applied automatically; remaining findings are presented alongside the tuning
  report.

Pass `scope: new-only` when the tuning session modified a small number of
artifacts (fewer than 10 changed) so reviewers focus on the changed surface
rather than re-auditing the entire harness. Use `scope: all` for broader tuning
sessions or when overlay-coherence drift was detected.

Report any failures alongside the tuning report so the operator can address
both drift and verification issues in a single pass.

## Quality Criteria

* All breaking drift is addressed (either fixed or explicitly acknowledged)
* No harness artifact references non-existent files after tuning
* Checksum scan classifies every manifest-tracked artifact or intentional ignore outcome
* Backup copies exist for every modified artifact
* The tuning report is comprehensive and actionable
* The harness manifest reflects the post-tuning state
