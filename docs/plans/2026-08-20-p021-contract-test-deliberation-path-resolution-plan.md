---
title: "Gate-atomic baseline repair - malformed plan frontmatter and the archived 019-DL contract-test load"
date: 2026-08-20
stash_id: 7852CE0D
deliberation: "021-DL (archived 2026-08-20 to .backlogit/archive/021-DL.md)"
requires_plan_hardening: no
blast_radius: "low (three test modules under tests/ plus one quoted line in one docs plan; no source, schema, template, or CLI change)"
---

# Implementation Plan - P-021 contract-test deliberation-path resolution

Date: 2026-08-20
Agent: Stage (planning only - Ship executes)
Stash source: `7852CE0D`
Deliberation: `021-DL` (archived 2026-08-20 to `.backlogit/archive/021-DL.md`)
Classification: **bug / baseline test-harness availability**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Goal

Make the configured pytest suite green at baseline again by resolving the
019-DL deliberation artifact through its current lifecycle location instead of
a hardcoded `.backlogit/queue/` path, and prevent the same queue-to-archive
drift from silently re-reddening the suite.

## Why this is a separate shipment

The suite is red before shipment 144-S starts. Ship evaluates the full
configured suite at each task completion gate, so no 144-S or 145-S task can go
green on its own merits while this defect stands. Under P-021 C1 the defect
fails the same-contract-surface test against both shipments (144-S owns the
`backlogit docs lint` / plan-frontmatter surface; 145-S owns the agent-template
paired-edit and stash-archive naming surface), so it is not absorbed into
either. It ships first, in its own shipment, wired as an execution-blocking
prerequisite.

## Non-goals

* No generic backlog-path abstraction in `src/`. `resolve_backlog_root`
  already is that abstraction.
* No change to `src/autoharness/backlog_root.py` or any other source file.
* No change to any B1-B18 assertion's subject or strength.
* No edits to other `.backlogit`-referencing tests. `test_gates_sizing.py`
  reads `.backlogit/header-def.yaml`, a stable non-lifecycle file;
  `test_backlog_root.py` and `test_ci_topology_check_entrypoint.py` construct
  roots deliberately inside temp workspaces.
* No revival of the abandoned 138-S root migration.
* No new deferred entries expected; anything found outside this surface is
  captured under P-021 C1 rather than absorbed.

## Root cause

`tests/test_scope_containment_boundary_contract.py:127` and
`tests/test_scope_containment_semantics_contract.py:137` each build
`<repo>/.backlogit/queue/019-DL.md` and call `.read_text()` inside
`setUpClass`. The artifact was archived by merge `f72109e2` (PR #374) and now
exists only at `.backlogit/archive/019-DL.md`. Because the read happens in
`setUpClass`, the `FileNotFoundError` collapses both modules' entire test
classes rather than failing one assertion.

The boundary module's own comment already admits the hazard: "Still in queue
(not yet archived) at the time this test was authored." The failure mode was
foreseen and left unguarded.

## Verification evidence (read-only, gathered by Stage)

| Probe | Result |
| --- | --- |
| `git rev-parse HEAD` | `aea3b60a` |
| `git cat-file -e origin/main:.backlogit/queue/019-DL.md` | exit 128, absent |
| `git cat-file -e origin/main:.backlogit/archive/019-DL.md` | exit 0, present |
| `Test-Path .backlogit/queue/019-DL.md` | False |
| `Test-Path .backlogit/archive/019-DL.md` | True |
| `C4 AMENDMENT` / `C5 AMENDMENT` in archived copy | lines 116 and 111 |

The archived copy retains the swept content, so the repair is
content-equivalent and reduces no coverage.

## Task 1 (single atomic task) - resolve 019-DL through a lifecycle-stable resolver

This is deliberately ONE task. Splitting it would leave an intermediate commit
where one module is repaired and its sibling still raises in `setUpClass`, so
the suite would stay red at that task's completion gate. Ship's per-task
green-gate therefore requires atomicity.

### Step 1 - add the resolver to the base module

**File**: `tests/test_scope_containment_policy_contract.py`

Add a module-level helper that resolves a backlog artifact by ID:

* Resolve the storage root with
  `autoharness.backlog_root.resolve_backlog_root(_REPO_ROOT)`. This import is
  available at test time because `pyproject.toml` sets `pythonpath = ["src"]`.
* Probe `queue/<artifact_id>.md`, then `archive/<artifact_id>.md`.
* Return the first candidate that exists.
* On a miss, raise an error naming the artifact ID and every probed candidate
  path, so the next drift is diagnosed in one read.

This module is the correct host because both sibling modules already import
from it. The existing one-way allocation edge (011 -> 013 -> 012) is preserved
and no import cycle is introduced.

### Step 2 - repoint the boundary module

**File**: `tests/test_scope_containment_boundary_contract.py`

* Line 127: replace the hardcoded path construction with a resolver call, and
  import the resolver alongside the constants this module already shares.
* Lines 56, 69, 76, 214, 291, 329: update the stale prose citations of
  `.backlogit/queue/019-DL.md` to cite 019-DL by artifact ID and note that its
  location is resolved rather than hardcoded. These are docstring and comment
  lines only.

### Step 3 - repoint the semantics module

**File**: `tests/test_scope_containment_semantics_contract.py`

* Line 137: replace the hardcoded path construction with the same resolver
  call, imported from the base module alongside the constants it already
  imports.

### Step 4 - primary regression assertion (behavioural)

Add a test proving:

* the resolver locates 019-DL;
* it resolves to exactly ONE location. Simultaneous presence in both `queue/`
  and `archive/` indicates a half-completed archival and must fail loudly;
* the loaded text still contains the `C4 AMENDMENT` and `C5 AMENDMENT`
  markers, proving content equivalence rather than a silent coverage
  reduction.

The failure message must name backlog lifecycle drift explicitly.

### Step 5 - secondary regression assertion (structural)

Add a guard asserting that no P-021 contract module constructs a
lifecycle-volatile `queue/`-anchored artifact path outside the resolver. Scope
the scan to code lines of the three named modules so prose citations do not
false-positive.

This guard is what actually prevents recurrence: it fails at authoring time
rather than at the next archival.

## Acceptance criteria

1. The full configured pytest suite is green at task completion.
2. Neither `tests/test_scope_containment_boundary_contract.py` nor
   `tests/test_scope_containment_semantics_contract.py` contains a hardcoded
   `queue/019-DL.md` path.
3. Both modules load the artifact through the shared resolver.
4. The primary regression assertion fails, with a lifecycle-drift message, if
   019-DL is moved or duplicated across `queue/` and `archive/`.
5. The structural guard fails if a new lifecycle-volatile path literal is
   introduced into any of the three modules.
6. No B1-B18 assertion is weakened, removed, skipped, or has its subject
   changed.
7. No file outside `tests/` is modified.

## Risks and mitigations

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Textual overlap with `137.003-T` in 145-S, which also edits the boundary module | medium | This task touches only the `setUpClass` load, the resolver import, and the 019-DL path citations. Those line ranges are disjoint from the `stash remove` / `archive` CLI-alias comments `137.003-T` corrects. Because this shipment merges first, `137.003-T` rebases onto the repaired file. Trivial textual rebase, no semantic conflict, no re-plan of 145-S. |
| Structural guard false-positives on prose | low | Restrict the scan to code lines of the three named modules. If the guard proves brittle, it may be narrowed, but it MUST NOT be dropped silently without recording the reason. |
| Uniqueness assertion fires on a legitimate future dual-location state | low | Intended behaviour. A half-completed archival is itself a defect worth surfacing. Do not weaken by reflex. |
| New `tests` to `src/autoharness` import coupling | low | The target is a narrow public helper already covered by `tests/test_backlog_root.py` for override precedence, both-roots-present, and symlink rejection. `pythonpath = ["src"]` already makes it a first-class test-time import. Reimplementing root precedence locally would be strictly worse. |

## Sizing

Size `S`, complexity `low`. Three files, one helper, two call sites, two
guards, six comment corrections. Comfortably inside the 2-hour rule on the
effort axis, and no elevated uncertainty on the complexity axis, so neither
axis forces a split.

## Plan hardening conclusion

Requires plan hardening: **no**.

Blast radius is three test modules. No schema change, no CLI distribution
change, no template family touched, no multi-family fan-out, no public
interface change. The only new coupling is an import of an already-shipped,
already-contract-tested helper. None of the P-006 elevated-blast-radius
triggers is met.

## Execution ordering

This shipment is an execution-blocking prerequisite. Deterministic order:

```text
PREREQUISITE -> 144-S -> 145-S
```

Ship must not claim 144-S until this shipment ships. The pre-existing
`145-S depends on 144-S` edge is preserved unchanged.

## Review amendments (plan-review round 1, 2026-08-20)

Three findings from the adversarial review are resolved here. See
`docs/reviews/2026-08-20-p021-contract-test-deliberation-path-resolution-review.md`.

### A1 (P1) - baseline-green contingency

Stage ran no tests, so it cannot prove these two loads are the ONLY cause of
baseline red. Acceptance criterion 1 is amended:

* If, once the resolver repair lands, the suite exposes further pre-existing
  failures on OTHER surfaces, Ship MUST NOT absorb them. It classifies each
  under P-021 C1, captures a `DEFERRED SCOPE EXPANSION` entry, and reports the
  residual red. This task's own gate is satisfied when the two
  `setUpClass` collapses are eliminated and no NEW failure is introduced by
  this change.
* If further failures ARE found and block the shipment, that is a shipment-level
  blocker to escalate, not a licence to widen this task.

### A2 (P1) - resolver must not inherit ambient backlog-root configuration

`resolve_backlog_root` honours the `BACKLOGIT_WORKSPACE_DIR` environment
variable. A developer or CI runner with that variable set to an unrelated value
would make these contract tests fail for a reason unrelated to the code under
test - reintroducing exactly the nondeterministic-red class this task exists to
remove.

The resolver helper MUST therefore call `resolve_backlog_root` with an explicit
empty environment mapping (`env={}`), matching the pattern
`tests/test_backlog_root.py` already uses to isolate ambient configuration. The
contract tests resolve the repository's committed backlog root, deterministically,
regardless of the caller's environment.

### A3 (P2) - structural guard must exempt its own resolver

The guard in Step 5 scans code lines for lifecycle-volatile `queue/`-anchored
path construction. The resolver itself legitimately contains those segments.
The guard MUST exempt the resolver's own definition explicitly and by name, so
the exemption is visible and cannot silently widen to cover a future violation.
---

## Amendment A4 (Stage bounded correction, 2026-08-20) - gate-atomic scope expansion

**Status: additive. Nothing above is deleted; A4 supersedes the specific
statements it names.**

### Finding - circular mandatory-gate dependency between 146-S and 144-S

Ship evaluates **all** mandatory gates before completing **every** task. At the
time this plan was written, two independent blockers were red at baseline and
were owned by two different shipments that blocked each other in effect:

| Blocker | Gate | Former owner |
| --- | --- | --- |
| `docs/archive/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md` line 12 unquoted YAML scalar | Gate 1 - YAML frontmatter validity | `136.001-T` in `144-S` |
| Stale `.backlogit/queue/019-DL.md` load in two P-021 contract modules | configured pytest suite | `138.001-T` in `146-S` |

* `146-S` repaired only the pytest blocker, so `138.001-T` would have completed
  with **Gate 1 still red**.
* `144-S` owned the Gate 1 repair but is blocked by `146-S`, and running it
  first would still have hit the pytest `setUpClass` collapse.

The recorded `blocks` edges were acyclic, but the **gate** dependency was
circular: **there was no executable first task anywhere in the chain.**

### Resolution - Task 1 becomes the gate-atomic baseline repair

Task 1 above is expanded to repair **both** blockers atomically. Its original
content is unchanged and is now designated **Scope B**. A new **Scope A** is
added, carried in verbatim from the superseded `136.001-T`:

**Scope A - quote the malformed `blast_radius` scalar**

*File*: `docs/archive/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md`,
line 12.

```yaml
# from
blast_radius: elevated (result-integrity + multi-family: eval code / tests / docs / fixtures)
# to (content byte-identical inside the quotes)
blast_radius: "elevated (result-integrity + multi-family: eval code / tests / docs / fixtures)"
```

*Acceptance* (A1-A4): the file's frontmatter parses as YAML; `git diff` shows
**exactly one** changed line in that file; `backlogit docs lint --path <file>`
reports no decode error; Ship's Gate 1 is green at this task's completion gate.

### Amended file budget - supersedes acceptance criterion 7

Acceptance criterion 7 above ("No file outside `tests/` is modified") is
**superseded**. The task may modify **exactly four** files:

1. `tests/test_scope_containment_policy_contract.py`
2. `tests/test_scope_containment_boundary_contract.py`
3. `tests/test_scope_containment_semantics_contract.py`
4. `docs/archive/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md` - **one
   line only**

Nothing else. No `src/`, no `schemas/`, no `templates/`, no `.github/`, no other
file under `docs/`. The repo-wide `docs/` sweep is **not** part of this task; it
remains `136.002-T` in `144-S`.

### Amended acceptance criterion 1

Criterion 1 (as already narrowed by A1) is restated as: at this task's
completion gate **all** of Ship's mandatory gates are green - Gate 1 through
Gate 4 and the configured pytest suite - subject only to the A1 escape hatch for
**pre-existing** failures on *other* surfaces, which are classified under
P-021 C1, captured as `DEFERRED SCOPE EXPANSION` entries and escalated as a
shipment-level blocker, never absorbed.

### Width isolation

This task deliberately crosses two families (tests plus one docs line) because
gate-atomicity requires it. It is a bounded, explicitly enumerated four-file
exception recorded at staging time, not a licence to widen. The docs side is a
single quoting change whose value is byte-identical inside the quotes.

### Sizing after expansion

Unchanged: **size `S`, complexity `low`**. Scope A was previously sized `XS` /
`trivial` as `136.001-T`. Adding one trivial single-line quoting edit to an
`S`/`low` task keeps the effort axis comfortably inside the 2-hour rule and adds
no uncertainty on the complexity axis, so neither axis forces a split.

### Backlog effects

* `136.001-T` - **superseded by `138.001-T`**, stamped, archived (not deleted),
  and removed from `144-S` membership.
* Dependency edges `136.002-T -> 136.001-T` and `136.003-T -> 136.001-T`
  removed. `136.002-T` becomes the first task of `144-S`; `136.003-T` now
  depends on `136.002-T` alone.
* The shipment edge `144-S depends on 146-S (blocks)` is **preserved unchanged**
  and is what sequences the `docs/` sweep after this gate-atomic repair. No
  cross-shipment *task* edge was added, so nothing dangles once `146-S`'s items
  are archived.
* `145-S depends on 144-S (blocks)` preserved unchanged.

### Deliberation lifecycle

`021-DL` is complete and fully harvested into `138-F` / `138.001-T` / `146-S`,
and was **archived** by Stage on 2026-08-20 to `.backlogit/archive/021-DL.md`.
Provenance, capture text, amendments and timestamps are preserved unmodified.
`138-F.custom_fields.source_deliberation_id` is **retained** under the
established idempotent convention: it points at an already-archived source, so
the Ship cleanup step ("if it exists and is not already archived, archive it;
otherwise skip and log") is a **no-op**. This archival was performed by Stage
because the installed dogfood `.github/agents/_ship.agent.md` does not carry
that cleanup step at all - it exists only in
`templates/agents/_ship.agent.md.tmpl` - and `146-S` executes **before** the
`145-S` template/dogfood migration, so no later migration could have performed
it.

### Re-review

Re-gated 2026-08-20; see the scope-expansion addendum in
`docs/reviews/2026-08-20-p021-contract-test-deliberation-path-resolution-review.md`.
Hardening conclusion is unchanged: `requires_plan_hardening: no`. Adding one
quoted line to one documentation file triggers no P-006 elevated-blast-radius
condition.
