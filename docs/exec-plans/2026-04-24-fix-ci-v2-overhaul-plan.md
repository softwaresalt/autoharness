# fix-ci Skill Template v2 Overhaul — Implementation Plan

**Date**: 2026-04-24
**Source stash entry**: `1C1106B9`
**Covering feature**: fix-ci skill template v2 overhaul
**Risk level**: Low — single template file rewrite + minor install-harness variable table update
**Requires plan hardening**: no

---

## Objective

Major rewrite of `templates/skills/fix-ci/SKILL.md.tmpl` incorporating 10 generalizable
improvements sourced from the production-proven backlogit fix-ci skill. The v1 template
(~155 lines) is replaced with a v2 that preserves the existing step structure where it
works but enriches it with structured parameters, dedicated Copilot detection, a hard reply
gate, cascade restart logic, defect logging, granular intercom events, terminal output
management, and a fix-patterns taxonomy.

## Deliberation Decision

**Option A (Full rewrite)** selected over Option B (incremental patches) because 8 of 10
improvements require new sections or structural changes. The v1 structure is preserved
where it works (step numbering, circuit breakers, model routing), just enriched.

## Tasks

### T1: Add prerequisites, quick-start, and parameters sections

**Files**: `templates/skills/fix-ci/SKILL.md.tmpl`
**Scope**: Add structured Prerequisites (required tools, environment), Quick Start (one-liner
invocation example), and Parameters (table of all inputs with defaults and descriptions)
sections before Step 1.
**Acceptance**: New sections present with valid template variables.

### T2: Add extended input schema (poll-interval, max-wait)

**Files**: `templates/skills/fix-ci/SKILL.md.tmpl`, `.github/skills/install-harness/SKILL.md`
**Scope**: Add `{{POLL_INTERVAL}}` and `{{MAX_WAIT}}` template variables to the inputs/parameters
section. Update the install-harness variable resolution table.
**Depends on**: T1 (parameters section must exist).
**Acceptance**: New variables in inputs; install-harness variable table updated.

### T3: Add dedicated Copilot review comment detection step

**Files**: `templates/skills/fix-ci/SKILL.md.tmpl`
**Scope**: Add a new Step 2.5 that specifically detects Copilot-authored review comments
(bot reviewer ID matching), categorizes them separately from human comments, and flags
threads requiring reply.
**Depends on**: T1.
**Acceptance**: Copilot detection step present with bot-ID matching guidance.

### T4: Add hard reply gate (NON-NEGOTIABLE)

**Files**: `templates/skills/fix-ci/SKILL.md.tmpl`
**Scope**: Add a new Step 6.5 after review comment handling: every review thread (Copilot or
human) MUST have a reply before the skill can proceed to push. Mark as NON-NEGOTIABLE.
**Depends on**: T3 (Copilot detection creates the thread inventory that the gate validates).
**Acceptance**: Gate present, marked NON-NEGOTIABLE, checks all threads for replies.

### T5: Add cascade restart on regression

**Files**: `templates/skills/fix-ci/SKILL.md.tmpl`
**Scope**: Add logic to Step 7 (local quality gate): if a fix for a later gate causes an
earlier gate to regress, restart the fix loop from the first failing gate instead of
continuing forward. Track gate pass/fail state across iterations.
**Depends on**: T1.
**Acceptance**: Cascade restart logic documented with gate state tracking.

### T6: Add defect logging for unresolved CI failures

**Files**: `templates/skills/fix-ci/SKILL.md.tmpl`
**Scope**: Add Step 8.5: when the circuit breaker halts (max iterations or 3 consecutive
same-check failures), create a backlog item for each unresolved failure using the backlog
tool's create operation. Include failure details, iteration history, and a link to the PR.
**Depends on**: T1.
**Acceptance**: Defect logging step present with backlog item creation.

### T7: Add granular intercom event table (17 events)

**Files**: `templates/skills/fix-ci/SKILL.md.tmpl`
**Scope**: Replace the generic intercom broadcast guidance with a detailed event table listing
all 17 broadcast events across the fix-ci lifecycle (start, check-found, reproducing,
fix-applied, gate-pass, gate-fail, push, poll-start, poll-pass, poll-fail, regression,
cascade-restart, defect-logged, reply-sent, reply-gate-pass, halt, complete).
**Depends on**: T1.
**Acceptance**: Event table present with 17 named events and their trigger conditions.

### T8: Add terminal output management guidance

**Files**: `templates/skills/fix-ci/SKILL.md.tmpl`
**Scope**: Add a new section providing guidance on managing terminal output during CI
reproduction: truncation strategies for large test output, filtering irrelevant lines,
token budget awareness (CI output can consume significant context), and structured
output capture patterns.
**Depends on**: T1.
**Acceptance**: Terminal output management section present.

### T9: Add common fix patterns taxonomy

**Files**: `templates/skills/fix-ci/SKILL.md.tmpl`
**Scope**: Add a reference section at the end cataloging common fix patterns organized by
check type: format (auto-fix, config alignment), lint (suppression vs. fix, false positive
handling), test (assertion fix, fixture update, flaky test isolation), build (dependency
resolution, version conflict). Each pattern includes when to apply and when to escalate.
**Depends on**: T1.
**Acceptance**: Taxonomy section present with patterns for each check type.

### T10: Register new template variables in install-harness

**Files**: `.github/skills/install-harness/SKILL.md`
**Scope**: Add `POLL_INTERVAL` and `MAX_WAIT` to the variable resolution table with default
values and descriptions. These are resolved from the workspace profile or use sensible
defaults (poll-interval: 30s, max-wait: 600s).
**Depends on**: T2.
**Acceptance**: Variables present in install-harness resolution table.

## Dependency Graph

```text
T1 (prerequisites/quick-start/parameters)
├── T2 (input schema) → T10 (install-harness vars)
├── T3 (Copilot detection) → T4 (hard reply gate)
├── T5 (cascade restart)
├── T6 (defect logging)
├── T7 (intercom events)
├── T8 (terminal output)
└── T9 (fix patterns)
```

## Execution Order

1. T1 (structural foundation — must be first)
2. T2, T3, T5, T6, T7, T8, T9 (independent sections — can execute in parallel)
3. T4 (after T3)
4. T10 (after T2)
