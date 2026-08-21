---
title: "Plan review - docs/compound docline conformance"
date: 2026-08-21
plan: docs/plans/2026-08-21-docs-compound-docline-conformance-plan.md
stash_id: F73BA065
deliberation: "025-DL"
verdict: PASS
---

# Plan Review - docs/compound docline conformance

Date: 2026-08-21
Agent: Stage (plan-review gate)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Verdict

**PASS** - 1 P1 raised and RESOLVED by amendment C1; 2 P2 raised, both resolved
by amendment C2. **0 unresolved P0/P1.** Review-fix cycles used: 1 of 3.

## P1-1 (RESOLVED by amendment C1) - the verification gate proves too little

**Finding.** The shipment verification gate reads "`backlogit docs lint --path
docs/compound` reports zero required-field errors for `source`/`doc_type`."
That is scoped to the two fields the stash entry happened to observe. The docline
base contract may require additional fields that were never reached, because the
linter reports per-file errors and the entry only recorded the first two. If a
third required field exists, this shipment closes reporting success while the
corpus still fails lint - converting a real gap into a believed-closed gap, which
is strictly worse than the current state.

**Why it is P1.** The whole value of this shipment is a trustworthy lint signal
for `docs/compound/`. An acceptance criterion that cannot distinguish "conformant"
from "conformant with respect to two fields I already knew about" does not
deliver that value.

**Resolution (C1).** The gate is rewritten to require ZERO required-field errors
of ANY kind for `docs/compound`. If residual error classes appear, they must be
enumerated by field name and either fixed in Task 1 (if mechanically derivable
like `doc_type`) or captured as a NEW deferred stash entry under P-021 C1 - never
silently accepted.

## P2-1 (RESOLVED by amendment C2) - the four no-frontmatter files were left unnamed

**Finding.** The plan says four files have no frontmatter block and requires them
to be enumerated during execution. Stage already has that list; withholding it
makes the executing agent redo Stage's measurement and risks a different count if
the corpus changes.

**Resolution (C2).** The four files are now named in the plan.

## P2-2 (RESOLVED by amendment C2) - test scope must exclude non-markdown

**Finding.** `docs/compound/` contains a `.gitkeep`. The proposed contract test
says "every `*.md`", which is correct, but the plan's prose elsewhere says "every
document". Tighten to `*.md` explicitly so a future non-markdown asset does not
fail the guard spuriously.

**Resolution (C2).** Folded in.

## Confirmed strengths (no action)

* The dry-run-then-gate-then-apply ordering, with a blocking human-readable check
  on the `source` value before any write, is the correct shape for a 73-file
  mechanical migration and is the single most important safety property here.
* Requiring PROOF of body invariance by diff (AC2) rather than trusting the
  tool's own `body_bytes_changed: false` claim is properly sceptical.
* Requiring an idempotence re-run (AC4) is the right acceptance test for a
  migration and is frequently omitted.
* The width isolation between the data migration (Task 1) and the template
  contract edit (Task 2) is correct and should not be collapsed for convenience.
* The `requires_plan_hardening: no` determination is explicitly reasoned rather
  than defaulted, satisfying P-006's fail-safe intent.
