---
name: harness-architect
description: "Scaffolds compilable but failing test harnesses for feature and chore tasks"
argument-hint: "feature=001-{SUFFIX_FEATURE} tasks=001.001-{SUFFIX_TASK}"
input:
  properties:
    feature:
      type: string
      description: "Feature or chore ID to scaffold harnesses for"
    tasks:
      type: string
      description: "Exactly one current task ID, supplied by the caller (the actor never selects or claims backlog work)"
  required:
    - feature
    - tasks
---

# Harness Architect Skill

Scaffold a strict test harness for the current task of a feature or chore.
The output must compile cleanly, fail for the intended not-yet-implemented
behavior, and leave clear harness commands for downstream build execution.

## Purpose

Use this skill when a release unit needs executable test boundaries before
implementation starts. The skill prepares the red phase and stops there. It
does not implement production logic.

## Agent-Intercom Communication

When the `agent-intercom` capability pack is installed, call `ping` at
session start. If reachable, broadcast at every step. If unreachable,
warn the operator that visibility is degraded and continue locally.

| Event | Level | Message prefix |
|---|---|---|
| Session start | info | `[HARNESS] Starting: feature={input.feature}` |
| Task loaded | info | `[HARNESS] Current task: {task_id}` |
| Codebase analyzed | info | `[HARNESS] Context gathered: {module_count} modules` |
| Harness generated | info | `[HARNESS] Generated: {test_file} ({scenario_count} scenarios)` |
| Compilation check | info | `[HARNESS] Compilation: {result}` |
| Red phase check | info | `[HARNESS] Red phase: {result}` |
| Label applied | success | `[HARNESS] harness-ready: {task_id}` |
| Complete | success | `[HARNESS] Complete: {task_id} harnessed` |

## Inputs

* `${input:feature}`: (Required) Feature or chore ID such as `001-F`
* `${input:tasks}`: (Required) Exactly one current task ID under the
  feature, supplied by the caller. See Step 1.

## Workflow

### Step 1: Select the current task

The actor operates on exactly one current task supplied by the caller
(`${input:tasks}`). The actor never claims backlog work: it claims no
shipment or task and changes no work-item status. Claiming stays with
the caller.

1. If `${input:tasks}` names no task, or more than one task, halt and
   report. The actor never defaults to a ready-task set.
2. Load the current task through the backlog tool's read operation and
   confirm that it belongs to `${input:feature}`. If it does not, halt
   and report.
3. Preserve the work-item-to-task mapping so the harness can be traced
   back to the current task.

### Step 2: Read task intent

1. Read the current task's title, description, acceptance criteria,
   and file references.
2. Pull in feature-level acceptance criteria when task text depends on
   broader feature behavior.
3. Translate acceptance criteria into named test scenarios before writing
   code.
4. Identify the correct module, test tier, and affected files for each
   harness.

When the `agent-engram` capability pack is installed, prefer indexed
symbol lookup and code-graph tools over broad grep when surveying
existing modules, test patterns, and import paths.

### Step 3: Determine execution posture

For the current task, select the appropriate harness strategy:

| Posture | When to use | Harness pattern |
|---|---|---|
| **test-first** | New functionality with clear inputs/outputs | Write failing tests for expected behavior |
| **characterization-first** | Modifying existing behavior | Write tests that capture current behavior then modify |
| **migration-first** | Moving code between modules | Write tests at the destination, verify source behavior |
| **spike** | Exploratory with uncertain approach | Write minimal integration test, implement spike, expand tests |

In a characterization-first posture, the characterization tests are
recorded outside the expected-RED roster: they pin current behavior, may
pass, and are listed apart from the roster in the Step 6 evidence record
(P-004). Tests for new or changed behavior remain roster tests, except
structural tests that reach no stub, which stay outside the roster
(Marker Convention, Step 5.2).

### Step 4: Generate failing harness skeletons

1. Create test files that express the task intent as compilable tests.
2. Prefer table-driven or parameterized tests when the task describes
   multiple scenarios.
3. Create matching production stubs with raise NotImplementedError("...") bodies
   so the module compiles while the tests still fail for the intended
   reason.
4. Keep signatures, types, and module names aligned with the current
   codebase.

### File placement rules

Write harness files into the module that matches the work item's scope:

* **Unit harnesses**: colocated with the production code in the
  appropriate src/autoharness subdirectory
* **Integration harnesses**: in `tests/integration/` when the
  task spans modules or runtime boundaries
* **Contract harnesses**: in `tests/contract/` when the task
  defines API, CLI, or schema behavior

Write companion stub files into the production module that the tests
exercise. Do not place scaffolding in unrelated modules.

### Step 5: Verify harness

#### Step 5.1: Compilation check

Run `python -m py_compile src/autoharness/cli.py` including tests. The harness MUST compile.

If compilation fails, fix the harness until it compiles. Do not proceed
with a non-compiling harness.

#### Step 5.2: Red phase check

Run `PYTHONPATH=src python -m unittest discover -s tests` for the harness tests,
invoking exactly the resolved test command with no runner substitution.
EVERY generated harness test MUST be discovered AND MUST fail with its
own expected failure marker (raise NotImplementedError("...")); evaluate
each test individually rather than relying on an aggregate non-zero
exit code.

Here "every generated harness test" means every test in the current
task's expected-RED roster, as P-004 defines it:

* **Roster**: The current task's expected-RED roster is the current
  task's generated harness tests, excluding characterization tests.
  Characterization tests are recorded separately, outside the roster,
  and may pass. Structural tests that reach no stub are likewise outside
  the roster (Marker Convention below). A task declaring
  `harness-surface:none` has no roster and no RED obligation.
  `harness-surface:none` is allowed only for a task whose file budget
  contains no Python production module under `src/`; if the current task
  declares it but its file budget contains one, halt and report without
  applying `harness-ready`.
* **RED (R2)**: RED for a roster test is that test reported as `ERROR`
  in the canonical command's output with its own unique
  `NotImplementedError` marker. Attribution is roster-relative (R2):
  each roster test is checked against the named `ERROR` set by its own
  marker. A roster test absent from the named `ERROR` set, or named
  with a different marker, is refused.

**Marker Convention** (P-004, stated verbatim from the governing plan,
where FI-9 is the RED-evidence rule P-004 states and a Proof G case ID is
that plan's test case identifier):

Each task's `Marker` value is a **prefix**. Every roster test `t` has its
own marker `<prefix>:<t>`, where `<t>` is its Proof G case ID or test
method name. It reaches a RED-phase stub that raises exactly
`NotImplementedError("<prefix>:<t>")`. The stub is either per behavior, or
derives the suffix deterministically from the test's distinct request.
The harness asserts the roster's markers are pairwise distinct, and the RED
record maps each roster test to its marker. Two roster tests sharing one
marker is a cross-test marker, which FI-9 refuses. Structural tests that
reach no stub (API, docstring, schema parity, pinned hash, alias, audit)
are recorded outside the roster, like characterization tests.

The following outcomes are NEVER valid red-phase evidence for a roster
test and MUST be treated as harness defects requiring a fix before
proceeding:

* **Zero-discovery**: the test command reports zero tests collected —
  test discovery failed to find the harness at all.
* **Wrong-reason failure**: a roster test fails for a reason other than
  its own expected failure marker (a different exception type or
  message).
* **Marker-bearing `AssertionError`**: a roster test reported as a
  failure whose `AssertionError` carries its marker is refused; RED
  requires the test's own `NotImplementedError` marker reported as
  `ERROR`.
* **Cross-test marker**: two roster tests sharing one marker, or a
  roster test credited with another test's marker, is refused.
* **Collection/import/syntax failure**: the run aborts during
  collection due to an import error, syntax error, or module-load
  failure — this is not the same signal as a running test raising the
  expected marker.
* **Skip or expected-failure (xfail)**: a roster test reported as
  skipped or marked expected-to-fail counts as no observation, not as red
  evidence.
* **Pass or unexpectedSuccess**: a roster test that passes outright, or is
  reported as an `unexpectedSuccess` (an `expectedFailure`-decorated
  test that unexpectedly succeeded), is a false positive -- the
  harness does not yet exercise the not-yet-implemented behavior.

If any roster test exhibits one of these outcomes, fix the harness until
every roster test is discovered and is reported as `ERROR` with its own
marker. Passing characterization tests are not harness defects.

### Step 6: Apply harness-ready label to the current task

`harness-ready` applies to the current task only. After both checks
pass for the current task (P-004 gate satisfied):

1. Apply the `harness-ready` label to the current task only, using the
   backlog tool's update operation. Never label another task, the
   parent feature, or a shipment.
2. Add an implementation note with the harness command.
3. Record the per-task harness-ready evidence record: the task ID, the
   exact command run, its native exit code, each roster test's outcome
   and marker, and the characterization tests, listed apart from the
   roster together with any structural tests that reach no stub.
4. Record the harness manifest: `Compilation: PASS`,
   `Red Phase: CONFIRMED`.

## Completion Criteria

The skill is complete only when the current task has:

* harness files in the correct modules
* structural stubs with intentional not-implemented behavior
* a successful `python -m py_compile src/autoharness/cli.py` result after scaffolding
* every roster test reported as `ERROR` with its own marker, and its
  characterization tests listed apart from the roster
* clear mapping from backlog task to harness command

## Guardrails

* Do not implement production logic — stubs only.
* Do not skip compilation verification.
* Do not apply the harness-ready label until both compilation and red
  phase checks pass.
* Keep test scenarios traceable to acceptance criteria.

## Model Routing

This skill operates at **Tier 2 (Standard)** — test scaffolding is structured but routine.
