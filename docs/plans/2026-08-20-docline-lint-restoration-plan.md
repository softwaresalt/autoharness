---
title: "Restore workspace-wide docline lint by fixing malformed plan frontmatter"
date: 2026-08-20
stash_id: 395EBE60
deliberation: docs/decisions/2026-08-20-docline-lint-hard-abort-malformed-frontmatter-deliberation.md
requires_plan_hardening: no
blast_radius: "low (one docs file, a bounded docs sweep, one new test)"
---

# Implementation Plan - Restore workspace-wide docline lint

Date: 2026-08-20
Agent: Stage (planning only - Ship executes)
Stash source: `395EBE60`
Deliberation: `docs/decisions/2026-08-20-docline-lint-hard-abort-malformed-frontmatter-deliberation.md`
Classification: **bug / docs-toolchain availability**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Goal

Make `backlogit docs lint` produce a workspace-wide report again, and make the
malformed-frontmatter failure class non-recurring.

## Non-goals

* No change to backlogit (external product decision - see deliberation Q2).
* No docline schema change.
* No edits to the 2026-08-02 plan beyond the malformed line.
* **No remediation of docline findings newly surfaced once the lint runs.**
  Those are captured as new deferred entries under P-021 C1.

## Task 1 - Quote the malformed `blast_radius` scalar

**File**: `docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md`

Line 12 currently:

```yaml
blast_radius: elevated (result-integrity + multi-family: eval code / tests / docs / fixtures)
```

Change to (content byte-identical inside the quotes):

```yaml
blast_radius: "elevated (result-integrity + multi-family: eval code / tests / docs / fixtures)"
```

**Acceptance**
* The file's frontmatter parses as YAML.
* No other line in the file is modified (`git diff` shows exactly one changed line).
* `backlogit docs lint --path docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md`
  no longer reports a decode error.

## Task 2 - Sweep `docs/` for the same hazard

Scan every YAML frontmatter block under `docs/` for **unquoted** scalar values
containing `": "`, and quote each one found, preserving content verbatim.

**Method**: parse each `docs/**/*.md` frontmatter block; any file that fails to
decode is a hit. Do not rely on a regex alone - decode failure is the ground truth.

**Acceptance**
* Every `docs/**/*.md` frontmatter block decodes successfully.
* The count of files corrected is reported in the PR description (may legitimately
  be zero beyond Task 1).
* Only quoting changes; no semantic edits to any frontmatter value.
* **Historical records** (`docs/closure/`, `docs/memory/`) are corrected **only**
  if they fail to decode, and then only by quoting - never by rewording.

## Task 3 - Regression guard

Add a test asserting that the YAML frontmatter of every `docs/**/*.md` file
decodes.

**Requirements**
* Discovers files dynamically - a newly added doc is covered with no test edit.
* Failure message names the **offending file path and line**, so the next
  occurrence is diagnosed in one step rather than by bisecting a silent
  whole-repo lint abort.
* Files with no frontmatter block are skipped, not failed - frontmatter is not
  universally required, and this guard is about *malformed* frontmatter only.

**Acceptance**
* Test passes after Tasks 1-2.
* Test demonstrably fails if the Task 1 quoting is reverted (verify by temporary
  local revert; do not commit the revert).

## Verification (Ship)

1. `backlogit docs lint` runs repo-wide and **emits a report** (exit status may
   still be non-zero if it finds real docline findings - that is success for this
   plan, not failure; the defect was the *absent report*, not the exit code).
2. The new regression test passes.
3. Any docline findings the restored lint surfaces are **captured as new deferred
   stash entries**, not fixed here.

## Sequencing

Task order is **Task 1 -> Task 2 -> Task 3** (`136.001-T` -> `136.002-T` ->
`136.003-T`), recorded as `blocks` dependency edges. Task 2's sweep is
repository-wide and would otherwise consume Task 1's single known file, leaving
Task 1's `exactly ONE changed line` acceptance impossible to satisfy. Task 3
verifies the result of both and stays last.

Predecessor of the harness-consistency shipment. Restoring the repo-wide lint
first means that shipment's new and edited documentation can actually be
validated workspace-wide.

## Plan Review (plan-review gate)

**Verdict: PASS.** Reviewed 2026-08-20 by Stage.

| Check | Result |
|---|---|
| Root cause verified, not assumed | PASS - confirmed by direct file inspection at line 12 |
| Scope matches the deliberation's accepted disposition | PASS - external linter behaviour excluded |
| Each task within the 2-hour rule | PASS |
| Width isolation | PASS - Task 1/2 docs-only, Task 3 tests-only |
| Acceptance criteria falsifiable | PASS - Task 3 includes a negative test |
| Blast radius honestly stated | PASS - low |
| Hardening required (P-006) | NO - `requires_plan_hardening: no`; single-family, reversible, no policy or contract surface touched |
| Known consequence planned for | PASS - newly surfaced findings explicitly deferred, per the checksum-drift compound learning |

No blocking findings. One advisory: Task 2's sweep count is unknown until
executed; if it exceeds a handful of files, Ship should report the count and
confirm the change remains quoting-only before proceeding.
