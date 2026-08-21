---
title: "A described derivation is not a wired derivation: Copilot review caught two P1s that local review missed"
description: "A new agent-instruction derivation step can be internally coherent and still be a functional no-op if it is never wired into the specific variable a later, unedited step consumes by name."
problem_type: "unwired_contract_derivation_and_hardcoded_portability_token"
category: "workflow-issues"
component: "ship-agent-templates"
root_cause: "A new agent-instruction derivation step described a correct replacement for an existing status-filtered task list, but never stated that it replaces that list, so the unedited consuming step kept reading the old list; separately, the fix for that gap hard-coded an installation-specific ID suffix into the portable template instead of the existing template variable for it."
resolution_type: "code_fix"
severity: "high"
file_path: "templates/agents/_ship.agent.md.tmpl"
citations:
  - "PR #379"
  - "docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-plan.md"
date: 2026-08-21
shipment: 147-S
feature: 139-F
tasks: [139.001-T, 139.002-T]
pr: 379
tags: [ship-agent, template-portability, agent-contract-wiring, p-018, copilot-review]
source: docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md
doc_type: learning
---

# Compound Learning: a described derivation is not a wired derivation

## What happened

147-S added an "executable task set derivation" contract to both Ship agent
files (installed mirror + template) so that Ship stops treating a shipment
manifest as its unconditional executable task set (needed so `144-S`/`145-S`
can carry pre-archived, superseded children for P-015 closure validity
without Ship trying to reactivate them).

A local adversarial code-review pass (via the `code-review` subagent) on the
first commit returned **READY** — it confirmed the contract text was
internally consistent, said what it claimed to say, and didn't contradict
itself. It was correct on those terms. But Copilot's hosted PR review caught
two P1s the local pass missed:

1. **Template Step 3's new derivation text was never wired into the actual
   "ready queue" variable that Step 4 iterates.** Steps 1-3 (pre-existing)
   built a queued-status-only list; the new item 4 *described* a different,
   correct derived set alongside it, but nothing said "and this replaces
   that list." Step 4 kept iterating the old list. The new prose was
   accurate in isolation and functionally inert in context.
2. **The new Step 0.5 item 6 (installed mirror) mandated a
   `shipment-reconcile mode: pre` check with a single `expected_status`,
   which cannot represent the mixed queued+active manifest the new
   derivation explicitly permits.** The contradiction was between two
   pieces of *my own* new text, not between old and new.

A third Copilot pass (on the fix commit) caught a third, unrelated issue:
the fix for #1 hard-coded the dogfood `-T` task-ID suffix into the
**template** (not the installed mirror, where the literal value is
correct), which would silently break any downstream installation configured
with a different `backlog.suffix_map` task suffix — every real task would
fail the artifact-type filter and the run would hit the empty-executable-set
halt. The fix already existed as a defined variable (`{{SUFFIX_TASK}}`,
already used in `templates/backlog/config.yml.tmpl`); it just hadn't been
reached for.

## Why local review missed these

The local review scope (correctly) checked "does this text say what it
claims, coherently, in both files?" It did not simulate **executing** the
described algorithm against the surrounding, unedited steps that reference
the same queue/check by name. A prose contract can be internally coherent
and still be a no-op, or contradict a *different* piece of prose in the
same diff, if the reviewer never traces the actual data-flow: "which
variable does Step 4 read, and did my new text touch that variable?"

## Generalizable takeaway

When adding a derivation/filter step to an agent-instruction contract that
is supposed to change what a *later*, unedited step does:

1. **Name the exact variable/list the later step consumes**, and make the
   new step explicitly say it replaces (or feeds) that named thing — not
   just "here is a new, correct set" sitting next to the old one.
2. **Check every other place in the same file that assumes the property
   your new contract just relaxed.** Here, "the manifest is status-uniform
   at intake" was an implicit assumption baked into a pre-existing
   mandatory check (`shipment-reconcile mode: pre`'s single
   `expected_status`); introducing "queued+active can legitimately coexist"
   without re-checking that assumption left a live contradiction.
3. **In a template file, treat every literal ID-suffix, prefix, or
   installation-specific token as a violation of Template Testing
   Convention (3 technology profiles) unless it is unconditionally true for
   every installation** — reach for the existing `{{SUFFIX_*}}`/`{{PREFIX_*}}`
   variable family first; do not assume dogfood conventions transfer.
4. Local review and hosted (Copilot) review are complementary, not
   redundant: local review is fast and always available; hosted review
   independently re-derives execution semantics and template-portability
   concerns from a different vantage point. Neither should be treated as
   sufficient in isolation for template/contract-surface changes — this is
   exactly the kind of diff the `Template Integrity Reviewer` persona and
   `Schema-CLI-Docs Coupling Reviewer` persona exist to catch, and is worth
   deliberately routing to those personas (or an equivalent standalone
   agent-of-record) even when a general-purpose local review already
   returned READY.

## Evidence

* PR #379, review rounds 1-2 (Copilot), commits `f065106b` and `08607503`.
* Fixed contradiction verified structurally: template Step 3 item 1
  ("derived set") -> item 2 ("replace queued-only membership with item 1's
  derived set") -> Step 4 ("For each task in the ready queue").
* `{{SUFFIX_TASK}}` verified against `src/autoharness/verify_workspace.py`
  `DEFAULT_SUFFIXES["task"] = "T"` and the `suffix_map` derivation loop.
