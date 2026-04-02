---
title: Tuning Guide
description: How to iteratively maintain and adapt an installed agent harness as the codebase evolves
---

## Why Tune

Agent harnesses degrade over time. Common causes:

* **New technologies added**: A Python backend gains a Go microservice, but no Go review persona exists
* **Build tool changes**: Migration from webpack to vite breaks build-feature skill commands
* **Directory restructuring**: `applyTo` patterns in instruction files match no files after a rename
* **CI pipeline changes**: Quality gate commands in the constitution no longer match CI steps
* **Runtime surface changes**: A repo grows a web UI or public API but the harness still assumes static-only validation
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

### Interactive Tuning (Recommended)

```text
@harness-tuner workspace=/path/to/target
```

The tuner will:

1. Re-run workspace discovery to produce a fresh profile
2. Compare against the profile used during installation
3. Categorize each difference by impact
4. Scan all harness artifacts for health issues
5. Present a prioritized list of proposed changes
6. Apply changes you approve (with backups)

### Scoped Tuning

Focus on specific areas:

```text
@harness-tuner workspace=/path/to/target scope=instructions    # Only check instruction files
@harness-tuner workspace=/path/to/target scope=agents          # Only check agent definitions
@harness-tuner workspace=/path/to/target scope=skills          # Only check skill workflows
@harness-tuner workspace=/path/to/target scope=policies        # Only check workflow policies
@harness-tuner workspace=/path/to/target scope=constitution    # Only check constitutional docs
```

## Drift Categories

### Breaking

Harness references are invalid. Artifacts reference files, tools, or commands that no longer exist.

**Examples**: Build command changed from `npm run build` to `pnpm build`, test directory renamed from `tests/` to `__tests__/`, removed CI step still referenced in constitution.

**Action**: Fix immediately. Breaking drift causes agent failures.

### Degrading

Harness works but produces suboptimal results. Artifacts are valid but miss new capabilities or use outdated patterns.

**Examples**: New framework added without review persona, new test patterns without matching instructions, stale architecture documentation.

Additional examples: a web UI exists but no browser-verification pack is enabled, operational closure templates omit monitoring expectations, safety-mode guidance is missing from risky maintenance workflows.

**Action**: Fix at next opportunity. Degrading drift reduces agent effectiveness.

### Growth

New capabilities that the harness could leverage. The workspace has evolved in ways that create opportunities for new harness features.

**Examples**: New database added (opportunity for database reviewer persona), Docker introduced (opportunity for container instructions), API documentation added (opportunity for API review).

Additional examples: web UI added (opportunity for browser verification), deployment manifests added (opportunity for release observability pack), higher-risk production changes (opportunity for strict safety defaults).

**Action**: Evaluate and implement when beneficial.

### Cosmetic

Functional but may cause minor confusion. Version numbers updated, minor naming changes, additional config files added.

**Action**: Fix in batch during maintenance windows.

## Manual Tuning

All harness artifacts are regular Markdown files. You can edit them directly:

* **Instructions**: Adjust `applyTo` patterns, add/remove rules
* **Agents**: Update tool lists, modify behavioral constraints, adjust model routing
* **Skills**: Change build/test commands, adjust circuit breaker limits
* **Skill Packs**: Enable richer verification or safety packs without redesigning the harness
* **Policies**: Add new policies or modify existing gate conditions
* **Constitution**: Update quality gates, change error handling patterns

After manual changes, run the tuner to verify consistency.

## Best Practices

1. **Tune after every major change**, not just when agents start failing
2. **Review tuning reports** even when auto-applying — understand what changed
3. **Keep backups** — the tuner creates them automatically in `.autoharness/backups/`
4. **Test agents after tuning** — run a simple task through the pipeline to verify
5. **Track tuning history** — the manifest records when and what was tuned
