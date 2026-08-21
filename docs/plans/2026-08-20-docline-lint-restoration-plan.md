---
title: "Restore workspace-wide docline lint by fixing malformed plan frontmatter"
date: 2026-08-20
stash_id: 395EBE60
deliberation: docs/decisions/2026-08-20-docline-lint-hard-abort-malformed-frontmatter-deliberation.md
requires_plan_hardening: no
blast_radius: "low (a bounded docs sweep and one new test; the single-file repair relocated to 146-S)"
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

**Scope**: exactly one hazard - an **unquoted plain scalar** whose value contains
`": "`. Nothing else.

**Method**
1. Parse each `docs/**/*.md` frontmatter block. A decode failure is a
   **candidate**, not a confirmed hit - a YAML decode error is *not* by itself
   evidence of this specific unquoted-colon hazard.
2. **Confirm before editing**: read the parser's reported error location
   (line/column) and the source line it points at, and verify that line is an
   unquoted plain scalar whose value contains `": "`. Only a confirmed candidate
   is in scope.
3. Correct a confirmed hit by quoting the value verbatim; change nothing else.
4. Do not rely on a regex alone as ground truth - it both misses cases and
   produces false positives. Use a regex only to *locate* the candidate line in a
   file the parser has already flagged, never to *decide* that a file is a hit.
5. **Any other decode failure** (tab indentation, duplicate key, malformed block
   scalar, unterminated quote, bad list or indentation, encoding fault, and so
   on) is **out of scope**. Leave that file byte-unmodified and capture it
   separately as a deferred stash entry under **P-021 C1**, naming the file path,
   the parser error text, and the reported location - the same capture-only
   boundary this plan's non-goals apply to newly surfaced docline findings.

**Acceptance**
* Every `docs/**/*.md` frontmatter block that fails to decode is triaged into
  exactly one recorded disposition: **(a)** confirmed unquoted-plain-scalar
  hazard, corrected by quoting only; or **(b)** other decode failure, left
  unmodified and captured as a deferred stash entry under P-021 C1.
* Every file corrected under (a) decodes successfully after the change.
* Both counts - (a) corrected and (b) captured - are reported in the PR
  description (either may legitimately be zero beyond Task 1).
* Only quoting changes; no semantic edits to any frontmatter value. No (b) file
  is modified by this task.
* **Historical records** (`docs/closure/`, `docs/memory/`) are corrected **only**
  if they fail to decode **and** the failure is confirmed under (a), and then
  only by quoting - never by rewording.
* If any (b) file exists, state so explicitly and note that Task 3's guard cannot
  pass repo-wide until those separately captured findings are resolved; do not
  absorb a (b) file into Task 2 to make that guard green.

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
* **Precondition**: Task 2 left no out-of-scope (b) decode failure behind. If it
  did, halt and report - do not widen Task 3 to fix those files, and do not
  weaken the guard to skip them.

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
---

## Amendment R1 (Stage bounded correction, 2026-08-20) - Task 1 relocated to 146-S

**Status: additive. Nothing above is deleted; R1 supersedes the specific
statements it names.**

### Finding - circular mandatory-gate dependency between 146-S and 144-S

Ship evaluates **all** mandatory gates before completing **every** task. Task 1
of this plan (`136.001-T`) owned the only repair for **Gate 1 - YAML frontmatter
validity**, but it sat inside `144-S`, which is blocked by the prerequisite
shipment `146-S`. `146-S` in turn repaired only the stale P-021 test-fixture
resolution, so *its* first task would have completed with Gate 1 still red;
and running `144-S` first would still have hit the P-021 pytest `setUpClass`
collapse.

The recorded `blocks` edges were acyclic, but the **gate** dependency was
circular: **there was no executable first task anywhere in the chain.**

### Resolution

**Task 1 of this plan is superseded and relocated**, not dropped. Its full
scope - the same file, the same line 12, the same byte-identical quoted
replacement, and all three of its acceptance criteria - is carried **verbatim**
into `138.001-T` as **Scope A** of the gate-atomic baseline repair in `146-S`.
See Amendment A4 in
`docs/plans/2026-08-20-p021-contract-test-deliberation-path-resolution-plan.md`.

**Nothing in Task 1 is weakened, deferred, or lost.** Only its owning task and
shipment change.

### Superseded statements in this plan

| Statement | Status |
| --- | --- |
| `## Task 1 - Quote the malformed blast_radius scalar` | **Relocated** to `138.001-T` Scope A (`146-S`). Retained above as the authoritative wording of that scope. |
| Sequencing: "Task order is Task 1 -> Task 2 -> Task 3 (`136.001-T` -> `136.002-T` -> `136.003-T`)" | **Superseded** - see corrected sequencing below. |
| Verification step 1 (repo-wide lint emits a report) | **Still applies**, but is first satisfied by `138.001-T` in `146-S`; `136.002-T` and `136.003-T` inherit an already-decoding baseline. |

### Corrected sequencing

```text
146-S : 138.001-T  (gate-atomic: Scope A = former Task 1, Scope B = P-021 resolver)
  |
  v   [shipment edge: 144-S depends on 146-S (blocks)]
144-S : 136.002-T  (Task 2, docs/ sweep)  ->  136.003-T  (Task 3, regression guard)
  |
  v   [shipment edge: 145-S depends on 144-S (blocks)]
145-S : harness consistency
```

* `136.002-T` is now the **first task of `144-S`** and has **no** task-level
  dependency.
* `136.003-T` now depends on `136.002-T` **alone**.
* The former edges `136.002-T -> 136.001-T` and `136.003-T -> 136.001-T` were
  removed.
* Ordering across shipments is carried by the pre-existing shipment edge
  `144-S depends on 146-S (blocks)`. **No cross-shipment task edge was added**,
  so no reference dangles once `146-S`'s items are archived.
* Task 2's original rationale still holds: its sweep is repository-wide and
  would otherwise consume Task 1's single known file, making Task 1's "exactly
  one changed line" acceptance impossible. Separating them across shipments
  preserves that property rather than weakening it.

### Task 2 and Task 3 acceptance clarifications

* Task 2 (`136.002-T`): on arrival the 2026-08-02 benchmark plan **already
  decodes**. Do not re-fix it and do not count it among this task's (a)
  corrections. "Zero additional (a) files" now means zero beyond the one already
  repaired by `138.001-T` Scope A. If that file does *not* decode on arrival,
  `138.001-T` did not land as specified - **halt and report**, do not absorb.
* Task 3 (`136.003-T`): the negative test is now "the guard fails if the
  **`138.001-T` Scope A** quoting is reverted" (same file, same line).

### Scope guarantee

`136-F` retains ownership of the sweep and the regression guard. Only the
single-file repair moved. `136.001-T` is stamped `[SUPERSEDED by 138.001-T]`,
**archived rather than deleted**, and removed from `144-S` membership, so the
original wording stays auditable.

### Plan-review status

The PASS verdict recorded above is **unchanged**. The relocation removes a task
from this plan's execution scope and adds no new work, so no new blast radius,
no new hardening trigger (`requires_plan_hardening` remains `no`), and no
re-review of Tasks 2-3 is warranted. The receiving plan was re-gated instead.
