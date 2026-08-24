---
title: "Plan review - docs/compound source value semantics"
date: 2026-08-23
source: "docs/reviews/2026-08-23-docs-compound-source-value-semantics-review.md"
doc_type: "review"
plan: docs/plans/2026-08-23-docs-compound-source-value-semantics-plan.md
stash_id: FAE1E7B7
deliberation: "026-DL"
verdict: PASS
review_fix_cycle: 1
---

# Plan Review - docs/compound `source` value semantics

Date: 2026-08-23
Agent: Stage (plan-review gate)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)
Plan under review: `docs/plans/2026-08-23-docs-compound-source-value-semantics-plan.md`

## Verdict

**PASS** after review-fix cycle 1.

3 P1 raised, all RESOLVED by amendments A1, A2, A3.
2 P2 raised, both RESOLVED by amendments A4, A5.

**0 unresolved P0/P1.** Review-fix cycles used: **1** of 3.

## Findings

### P1-1 (RESOLVED by amendment A1) - AC2.2 invited mutating tracked corpus data

As written, AC2.2 permitted proving the new assertion's discriminating power via
"a temporary local edit" to the real `docs/compound/` corpus, with correctness
resting on a manual revert plus a `git status` check. That is a
mutate-then-remember-to-undo pattern on tracked data, inside a task whose entire
purpose is to guarantee that corpus's integrity. The repository already has a
recorded learning against exactly this shape
(`docs/compound/2026-08-15-torn-archive-log-entry-without-file-mutation-must-not-be-committed.md`).
A missed revert would commit a deliberately corrupted learning document, and the
newly ratcheted guard would then be the thing that catches it - after the fact.

The plan also offered "or a fixture-driven negative case" as an alternative,
which is strictly safer at identical cost, so the hazardous option had no
justification for existing.

### P1-2 (RESOLVED by amendment A2) - the ">1 non-conforming file" branch deadlocks Task 2

Task 1 step 1 instructs: if re-measurement finds MORE than one non-conforming
file, fix only the known outlier and capture the rest as a new P-021 entry. Task
2 then adds a **corpus-wide** value-shape assertion. Those two instructions are
mutually incompatible: in that branch Task 2's assertion is guaranteed RED
against the surviving non-conforming files, so Task 2 cannot reach `done` and the
shipment deadlocks on its own scope guard.

This is the same failure shape 024-DL had to correct in PR #386 cycle 2 - a plan
branch that terminates in a state no executing agent can discharge. The scope
guard itself is correct and must be kept; what was missing is the mechanism that
lets the guard hold WITHOUT stalling execution.

The plan also lacked any statement of what the "zero non-conforming files found"
branch does to the shipment's own narrative.

### P1-3 (RESOLVED by amendment A3) - the plan omitted a test that directly pins the edited template section

The plan's blast-radius statement, AC3.4 ("the workspace's template-render/verify
path" - unnamed) and AC3.6 (manifest/dogfood only) all missed
`tests/test_compound_template_docline_frontmatter.py`, which was landed by
`140.002-T` under this very surface's predecessor and which pins
`templates/skills/compound/SKILL.md.tmpl` directly. Two of its assertions bear on
Task 3's exact edit:

* `QualityCriteriaTests::test_quality_criteria_mentions_source_and_doc_type`
  slices the template from the `## Quality Criteria` marker to end-of-file and
  requires the literal backticked tokens `` `source` `` and `` `doc_type` `` to
  appear in that slice. A rewrite of the bullet that dropped either token - for
  instance one that moved `doc_type` out of the bullet entirely - turns this
  test RED.
* `CapabilityNeutralGuidanceTests::test_no_forbidden_tool_tokens_anywhere_in_template`
  scans the WHOLE file for the tokens `backlogit`, `docs classify`,
  `docs migrate`, `docs lint`, `docs scope`. This is the mechanical enforcement
  of the capability-neutrality rule the plan stated only in prose.

Leaving these unnamed meant Task 3's verification was under-specified and its
"stop and return to Stage" trigger (AC3.6) was aimed at the wrong assumptions:
the plan checked for a dogfood counterpart and a manifest entry (correctly absent)
while missing the actual live constraint. Note this does NOT change the P-006
hardening determination - a repo-side test pinning a template is ordinary
regression coverage, not a paired-edit or checksum obligation - but it must be
named in the task.

### P2-1 (RESOLVED by amendment A4) - `citations` addition vs. the docline non-contract-key normalizer

Task 1 adds a `citations` key. docline's normalizer folds non-contract keys under
a `docline` namespace ("move, never drop"), so a reviewer could reasonably ask
whether adding a key invites future churn. The plan asserted the choice was
contract-designated but offered no evidence that non-contract keys survive the
tooling in practice.

The evidence exists and should be stated: 74 of the 75 corpus files already carry
non-contract keys (`title`, `date`, `tags`, and in many cases `problem_type`,
`category`, `root_cause`, `component`, `severity`, `citations`), all of which
survived `140.001-T`'s migration with proven body invariance and verbatim key
preservation. `citations` is therefore no more exposed than `tags` already is.

### P2-2 (RESOLVED by amendment A5) - AC1.5 names a tool command the plan elsewhere forbids

AC1.5 requires running `backlogit docs lint --path docs/compound`. That is correct
and desirable for a TASK acceptance criterion in THIS workspace. But the plan also
insists (Task 3 step 3) on capability neutrality, and the distinction between
"this repository's own verification commands" and "text written into a base
Primitive 1 template that installs elsewhere" was implicit. 025-DL's amendment C3
and review P1-3 exist precisely because that distinction was previously blurred.
It should be stated once, explicitly, so the executing agent does not either
(a) omit a useful local gate out of misplaced neutrality, or (b) copy a local
command into the template.

## Amendments (binding; applied to the plan in place)

* **A1** - AC2.2 rewritten: discriminating power MUST be proven with an isolated
  fixture (a temporary directory or in-test synthetic document), never by
  mutating any tracked file under `docs/`. The "temporary local edit" option is
  REMOVED, not merely discouraged.
* **A2** - Task 1 step 1 and Task 2 reconciled with a shrinking exemption
  allowlist, following the precedent of `141.002-T`'s shrinking allowlist:
  * If exactly one non-conforming file is found (the expected case), Task 2's
    exemption allowlist MUST be EMPTY, and an emptiness assertion is added as
    AC2.7.
  * If more than one is found, Task 1 records them and captures the extras as a
    new P-021 entry; Task 2 then enumerates those extra files EXPLICITLY in a
    named allowlist constant, each entry annotated with the deferring P-021
    capture ID, and AC2.7 asserts the allowlist contains exactly and only those
    recorded files. Task 2 terminates `done` in both branches.
  * If zero are found, Task 1 records "no longer reproduces" with evidence and
    closes `done`; Tasks 2 and 3 still proceed, and the shipment records the
    data-fix half as a no-op rather than silently implying a correction occurred.
* **A3** - Task 3 gains AC3.7 naming
  `tests/test_compound_template_docline_frontmatter.py` as a directly-affected
  regression test, with two explicit sub-obligations: the amended Quality
  Criteria bullet MUST keep the literal backticked tokens `` `source` `` and
  `` `doc_type` `` within the `## Quality Criteria` section, and MUST NOT
  introduce any of the forbidden tokens `backlogit`, `docs classify`,
  `docs migrate`, `docs lint`, `docs scope` anywhere in the template. AC3.4's
  vague "template-render/verify path" is replaced by naming this module plus the
  canonical gate. AC3.6's stop-and-return trigger is narrowed to its true
  subjects (a newly-discovered dogfood counterpart or manifest checksum entry)
  and explicitly does NOT fire on the existence of this test.
* **A4** - Task 1 gains a rationale note recording the 74-of-75 non-contract-key
  precedent that makes the `citations` addition safe, and AC1.3 is extended to
  require that no OTHER key is added beyond `citations`.
* **A5** - A one-line scope note is added to Task 3: capability neutrality
  constrains TEXT WRITTEN INTO THE TEMPLATE only. It does not constrain this
  repository's own task acceptance commands, which may and should name concrete
  local tooling (AC1.5, AC2.1).

## Confirmed strengths (no action)

* The P-006 `no` is a considered determination with three independently
  re-verified supports (no dogfood counterpart, no manifest checksum entry,
  single template family), and it survives P1-3 unchanged.
* Width isolation is correct and non-negotiable: corpus data, test surface and
  template family are three separate tasks (P-003 / 026-DL R6).
* The deviation from RED-harness-first is justified in writing rather than
  silently taken, and the discriminating-power obligation is the correct
  compensating control - now made safe by A1.
* The corpus-drift risk K1 is real (73 -> 75 in two days) and the re-measure-first
  instruction is the right mitigation; A2 completes it.
* The location-derived predicate requirement (AC2.4) correctly anticipates the
  category-subdirectory shape the template already models. This is the kind of
  false-failure that would otherwise surface months later.
* The refusal to ratchet `doc_type` (026-DL R3) is correct: a literal `learning`
  assertion would hard-code rung 3 of the capability-neutral authority order.

## Gate record

| Gate | Result |
| --- | --- |
| P-003 width isolation | PASS - three surfaces, three tasks |
| 2-hour rule per task | PASS - largest task (Task 2) is a single test module |
| P-006 hardening determination | PASS - considered `no`, three supports, unaffected by P1-3 |
| P-021 C1 scope containment | PASS - non-goals pin the surface; A2 keeps the guard executable |
| P-021 C5 duplicate scan | PASS - CLEAN over 190 entries (recorded in 026-DL) |
| P-021 C6 late-identifier reconciliation | PASS - performed, no result, `N/A`s stand as truthful |
| Predecessor acceptance contracts preserved | PASS - 140.001-T AC3 explicitly not amended; 025-DL R3/R4/R5/R6 carried forward |
| Unresolved P0/P1 | **0** |
