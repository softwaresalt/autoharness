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

### Phase 1: Drift Detection

#### Step 1.1: Re-run Workspace Discovery

Invoke the workspace-discovery skill with `existing_profile` set to the current `.autoharness/workspace-profile.yaml`. This produces a fresh profile with a drift report comparing current state against the installed profile.

#### Step 1.2: Categorize Drift

Classify each detected change by impact and urgency:

| Drift Category | Impact | Examples |
|---|---|---|
| **Breaking** | Harness references are invalid | Removed build tool, renamed source directory, deleted CI pipeline |
| **Degrading** | Harness works but is suboptimal | New framework added without instructions, new test patterns without review persona |
| **Cosmetic** | Function unaffected | Minor version bumps, additional config files |
| **Growth** | New capabilities to harness | New languages in project, new documentation patterns |

#### Step 1.3: Scan Harness Artifact Health

For each installed artifact, check:

* **Instruction files**: Do `applyTo` glob patterns match files that still exist?
* **Agent files**: Do referenced skills, tools, and file paths resolve?
* **Skill files**: Do build/test/lint commands match current tooling?
* **Policies**: Do referenced agents and gate points still apply?
* **Constitution**: Do technology-specific rules match the current stack?
* **AGENTS.md**: Do quality gates and commands match current tooling?
* **Backlog registry**: Does the registered backlog tool still match the installed tool? Has the tool been switched?
* **Runtime verification and closure skills**: Do they match the current runtime surfaces and deployment model?
* **Agent-intercom weaving**: If intercom markers exist, do AGENTS.md, copilot-instructions, relevant agents, and relevant skills consistently reference heartbeat, broadcast, approval-routing, and degraded-mode handling?

Record: `health_report{}` with per-artifact status.

#### Step 1.4: Backlog Tool Migration Detection

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

#### Step 1.5: Preset and Capability-Pack Drift

Compare the installed preset and capability packs in `.autoharness/harness-manifest.yaml` against the current workspace profile recommendations:

| Scenario | Category | Action |
|----------|----------|--------|
| Same preset and packs still appropriate | Healthy | No action needed |
| Same preset, missing recommended pack | Growth | Propose enabling the pack |
| Installed pack no longer matches runtime surfaces | Cosmetic or Degrading | Propose disabling or retargeting the pack |
| agent-intercom markers detected but `agent-intercom` pack missing | Growth or Degrading | Propose enabling the pack and weaving intercom guidance through the harness |
| Starter preset on a repo that now has complex runtime surfaces | Growth | Propose moving to `standard` or `full` |

#### Step 1.6: Overlay-Coherence Drift

For every enabled capability pack, compare the manifest's declared overlay targets against the currently installed artifacts.

Flag drift when:

* the pack is enabled but one or more declared target artifacts are missing
* only some of the targeted artifacts mention the pack's behavior delta
* the workspace still contains woven overlay guidance after the pack was removed
* the workspace now exposes new eligibility signals that should expand the overlay target set

Treat partially woven overlays as a first-class drift category rather than a cosmetic doc mismatch.

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

#### Step 2.3: Detect New Primitive Opportunities

Scan for workspace patterns that suggest missing harness capabilities:

* Database access code without a database reviewer persona
* API endpoint code without an API review persona
* Security-sensitive patterns (auth, crypto, input validation) without security review
* Infrastructure-as-code files without IaC instructions
* Containerization (Dockerfile, docker-compose) without container instructions
* Web UI or API runtime surfaces without matching runtime verification or operational closure guidance
* Remote operator workflow markers without matching agent-intercom guidance in the harness

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
4. Update manifest preset / capability-pack metadata when installation shape changes
5. Update manifest overlay-target metadata when the pack's woven surface changes

#### Step 4.3: Update Manifest

Update `.autoharness/harness-manifest.yaml`:

* Bump the `tuned_at` timestamp
* Record which proposals were applied
* Update artifact checksums
* Store the new workspace profile hash

### Phase 5: Verification

Run the same verification checks as the install-harness skill Phase 4:

* Cross-reference validation
* Structural validation
* No unresolved template variables
* Updated report

## Quality Criteria

* All breaking drift is addressed (either fixed or explicitly acknowledged)
* No harness artifact references non-existent files after tuning
* Backup copies exist for every modified artifact
* The tuning report is comprehensive and actionable
* The harness manifest reflects the post-tuning state
