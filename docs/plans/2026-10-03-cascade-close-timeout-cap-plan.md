---
title: "cascade-close --timeout cap: raise the fixed range to 30-3600 s (default 1800 s) and document the cascade sizing rule"
description: "Closure-blocking remediation for stash F50BD40F. Raise MAX_TIMEOUT_SECONDS 900 -> 3600 and DEFAULT_TIMEOUT_SECONDS 120 -> 1800 in src/autoharness/shipment_close/runner.py, align the cli.py help text, docs/gates-reference.md, and the shipment-reconcile Cascade Close Sub-Procedure (template and mirror) with a sizing rule, and pin all surfaces to the runner constants in tests. Harvested under active feature 192-F into the active 198-S manifest (operator-authorized)."
doc_type: plan
status: draft
created: 2026-10-03
supersedes: "docs/plans/2026-09-27-cascade-close-evidence-capture-plan.md, A3a timeout clause only (`timeout` defaults to 120 s; `--timeout` accepts 30-900 s) and the matching A3d argument-parsing range (30-900 s). Every other clause of that plan stands."
source_stash: F50BD40F
source_deliberation: docs/decisions/2026-10-03-cascade-close-timeout-cap-deliberation.md
review_record: docs/reviews/2026-10-03-cascade-close-timeout-cap-plan-review.md
operator_decision: "Fix the cap first. Option 1. (2026-10-03, Orchestrator relay, dark-factory P-017)"
operator_authorization: "Modification of the active 198-S manifest (append remediation tasks under active feature 192-F) is explicitly operator-authorized as closure-blocking remediation; pre_claim forbids a second active shipment (PRECLAIM_ACTIVE_SHIPMENT_PRESENT)."
provenance: "198-S / 192-F post-merge closure halt (PR #482, merge eb8b7811; closure branch chore/198-s-closure; halt report .backlogit/reconcile/198-S-cascade-close-20261003-051645.md)"
requires_plan_hardening: "yes"
---

# cascade-close `--timeout` cap: 30-3600 s, default 1800 s

## Outcome

The mutating `autoharness shipment cascade-close` must be able to finish the
cascade for every realistic shipment without the operator passing a
`--timeout`. It must still keep a finite guard against a hung engine.

After this plan, each surface reads as follows:

* `runner.py` accepts `--timeout` in **30-3600 s** with a default of
  **1800 s**.
* `cli.py` help, `docs/gates-reference.md`, and the shipment-reconcile Cascade
  Close Sub-Procedure state the same numbers, and tests pin all of them to the
  runner constants.
* A documented sizing rule tells Ship when the default is enough, when to pass
  an explicit `--timeout`, and when to halt instead.
* The remediated 198-S closes with the default (N = 28, budget 1670 s ≤ 1800 s).

## Problem Frame

`src/autoharness/shipment_close/runner.py` sets `DEFAULT_TIMEOUT_SECONDS = 120`,
`MIN_TIMEOUT_SECONDS = 30`, and `MAX_TIMEOUT_SECONDS = 900`. `validate_timeout`
enforces the inclusive integer range. `_parse_cascade_close_args` in
`src/autoharness/cli.py` defaults to `DEFAULT_TIMEOUT_SECONDS` and validates
through `validate_timeout`. `run_cascade_close` in `command.py` passes the value
to `run_bounded`, which kills the backlogit process group on expiry. The command
then exits 6 (`mutation_possible: indeterminate`).

Measured `backlogit shipment ship` cost on this workspace (backlogit 1.11.0,
~1,692 indexed artifacts) is about **133 s + 35 s × N**, where N =
|closure_scope(S)| = manifest items + 1. For 198-S (N = 24), the prediction is
973-1020 s, which is above the 900 s ceiling. Every recent cascade has exceeded
the 120 s default. The skill's mutating invocation passes no `--timeout`, so
the default is the operative value. Ship halted the 198-S closure before the
mutating run, and the backlog is unmodified. Full analysis: source deliberation.

## Requirements Trace

| # | Requirement (source) | Unit |
|---|---|---|
| R1 | Raise the ceiling above observed cost while keeping it finite (F50BD40F; deliberation D1) | A8a |
| R2 | Raise the default so the skill's no-`--timeout` invocation covers realistic sizes (D1, D3) | A8a |
| R3 | `validate_timeout` docstring and range stay coherent; the integer-only and bool rejection are unchanged (D1, D5) | A8a |
| R4 | CLI help states `30-3600 seconds` and `Default: 1800.` (D2) | A8b |
| R5 | `docs/gates-reference.md` states the range and default and documents the sizing rule (D2, D3; F50BD40F proposal) | A8d |
| R6 | shipment-reconcile Cascade Close Sub-Procedure carries the sizing note and the stay-attached sentence, in template and mirror (D3, D4; F50BD40F proposal) | A8c |
| R7 | Tests derive expectations from the runner constants, so no surface can drift again (D2) | A8a, A8b, A8d |
| R8 | No change to the exit codes, the evidence record, the validator, `run_bounded`, the kill path, or the probe timeout (D5) | constraint, all units |
| R9 | Remediation harvested under active 192-F and appended to active 198-S, operator-authorized (D6) | harvest |
| R10 | The 198-S `pre_close` refresh needed by the grown manifest is named for Ship (D7) | Runtime Verification and Closure |

## Decisions and Implementation

Decision source: `docs/decisions/2026-10-03-cascade-close-timeout-cap-deliberation.md`
(Option A, D1-D7).

* **D1 constants:** `MAX_TIMEOUT_SECONDS = 3600`, `DEFAULT_TIMEOUT_SECONDS = 1800`,
  and `MIN_TIMEOUT_SECONDS = 30` (unchanged).
* **D3 sizing rule:**
  * B(N) = ⌈1.5 × (133 + 35 × N)⌉ s.
  * B ≤ 1800 (N ≤ 30): use the default.
  * 1800 < B ≤ 3600 (31 ≤ N ≤ 64): pass `--timeout B`.
  * B > 3600 (N ≥ 65): HALT before the mutating run for an operator decision.
* **D4:** stay attached to the mutating run until the command exits.

### Implementation Units

All four units belong to one release unit (label `release-unit-a8`) and land
in one pull request, so the code, help, and docs never disagree on `main`. The
unit names continue the 192-F plan's `A*` series.

#### A8a — Raise the runner range and default; re-pin the runner and CLI range tests (code + tests)

* **Files (3):**
  * `src/autoharness/shipment_close/runner.py`
  * `tests/test_shipment_close_runner.py`
  * `tests/test_cli_shipment_cascade_close.py`
* **Changes:**
  * `DEFAULT_TIMEOUT_SECONDS: Final = 1800` and `MAX_TIMEOUT_SECONDS: Final = 3600`.
  * The `validate_timeout` docstring reads `30-3600 s`. Its body and error
    message are unchanged, since the message is already built from the
    constants.
* **Tests:**
  * Runner scenario "timeout bounds" (`tests/test_shipment_close_runner.py`,
    in the binary-trust test class):
    * Assert `DEFAULT_TIMEOUT_SECONDS == 1800`, `MAX_TIMEOUT_SECONDS == 3600`,
      `MIN_TIMEOUT_SECONDS == 30`, and `MIN <= DEFAULT <= MAX`.
    * Accept `MIN`, `DEFAULT`, `900`, and `MAX`.
    * Reject `MIN - 1`, `MAX + 1`, `0`, `-1`, `True`, `1.5`, and `"60"`, each
      with `EXIT_INPUT`.
  * CLI scenario (`tests/test_cli_shipment_cascade_close.py`):
    * `test_invalid_argument_table`: "timeout above range" uses
      `str(runner.MAX_TIMEOUT_SECONDS + 1)` and "timeout below range" uses
      `str(runner.MIN_TIMEOUT_SECONDS - 1)`.
    * `test_routing_table`: the explicit-`--timeout` case passes
      `str(runner.MAX_TIMEOUT_SECONDS)` and expects it.
    * The default case already reads `runner.DEFAULT_TIMEOUT_SECONDS`.
* **Why three files:** changing the constants turns both existing test pins
  red (`DEFAULT == 120` and `901` rejected), so the three files are one
  suite-green atomic change and cannot be split. This matches the accepted
  three-file residual precedent of A5 and A6 in the 192-F plan.
* **Functions touched:** 1 (`validate_timeout`, docstring only).
* **Test scenarios:** 2.
* **Posture:** test-first. Re-pin the tests to the new values (red), then
  change the constants (green).
* **Size / complexity:** XS / low. **Harness surface:**
  `harness-surface:harness-architect` (code-bearing, per the 192-F convention).
* **Depends on:** none (first remediation unit).

#### A8b — CLI help text states the new range and default (code + tests)

* **Files (2):**
  * `src/autoharness/cli.py` (`SHIPMENT_USAGE` only)
  * `tests/test_cli_shipment_cascade_close.py`
* **Changes:** the `--timeout <secs>` help lines read
  `` `shipment ship` timeout, 30-3600 seconds (mutating mode only). `` and
  `Default: 1800.`. No parser change.
* **Tests (1 scenario):** in the existing usage test (the one asserting
  `cli.SHIPMENT_USAGE` tokens), assert that the usage contains
  `f"{runner.MIN_TIMEOUT_SECONDS}-{runner.MAX_TIMEOUT_SECONDS} seconds"` and
  `f"Default: {runner.DEFAULT_TIMEOUT_SECONDS}."`, and does not contain
  `30-900`.
* **Functions touched:** 0 (module constant) plus 1 test method.
* **Posture:** test-first.
* **Size / complexity:** XS / trivial. **Harness surface:**
  `harness-surface:harness-architect`.
* **Depends on:** A8a.

#### A8c — shipment-reconcile Cascade Close Sub-Procedure sizing note (template + mirror + manifest checksum)

* **Files (3, one atomic rendered-surface triple):**
  * `templates/skills/shipment-reconcile/SKILL.md.tmpl`
  * `.github/skills/shipment-reconcile/SKILL.md`
  * the `.github/skills/shipment-reconcile/SKILL.md` entry's `checksum` and
    `note` in `.autoharness/harness-manifest.yaml`
* **Changes:**
  * Inside the `<!-- cascade-close-routing:BEGIN cascade-sub-procedure -->`
    block, immediately after the sentence that ends "...only with the
    destructive-command approval Step 0(c) names.", insert one paragraph, the
    **timeout sizing note**. It says:
    * on expiry the command kills the engine mid-cascade and exits 6
      (`mutation_possible: indeterminate`);
    * N = |closure_scope(S)| (manifest items plus the shipment record);
    * B = ⌈1.5 × (133 + 35 × N)⌉ seconds;
    * B ≤ 1800: the default `--timeout` (1800 s) suffices;
    * 1800 < B ≤ 3600: Ship adds `--timeout B`;
    * B > 3600: Ship HALTs before the mutating run for an operator decision and
      never invokes with a timeout known to be too short;
    * Ship stays attached to the run until the command exits and never abandons
      or kills it on an agent-tool wait;
    * the coefficients and their re-derivation are in `docs/gates-reference.md`.
  * The mutating invocation string itself is unchanged, so the existing pin
    (`MUTATING_INVOCATION`) still matches.
  * Template and mirror get byte-identical inserts. The parity test
    `test_cascade_sub_procedure_and_marker_region_parity` must stay green.
  * Ship refreshes the manifest checksum from the LF-normalized staged blob
    (`git cat-file blob :<path>`) and appends a dated note clause
    (`F50BD40F/192.025-T: Cascade Close Sub-Procedure timeout sizing note`),
    following the entry's existing convention.
* **Tests:** the existing parity and checksum-coherence tests (no new test in
  this unit; A8d pins the note's content).
* **Functions touched:** 0.
* **Test scenarios:** 0 new; 2 existing (parity, checksum).
* **Posture:** test-after-edit.
* **Size / complexity:** XS / low. **Harness surface:** `harness-surface:none`.
* **Depends on:** A8a (the numbers cite the constants).
* **Residual:** three files is the accepted rendered-surface-triple residual
  (192-F A5, A5b, A6 precedent).

#### A8d — `docs/gates-reference.md` range, default and sizing rule, plus doc pins (docs + tests)

* **Files (2):**
  * `docs/gates-reference.md`
  * `tests/test_flat_manifest_closure_docs.py`
* **Changes in `docs/gates-reference.md`:**
  * The mutating-mode row of the cascade-close mode table reads
    `` `--timeout` is 30-3600 seconds (default 1800). ``
  * Add a short `### Timeout sizing` subsection after the mode table, under the
    cascade-close section. It records:
    * the cost model 133 s + 35 s × N, with N = |closure_scope(S)|, measured on
      backlogit 1.11.0 at ~1,700 indexed artifacts from `.backlogit/logs`
      (201-S: 553 s predicted, 581 s actual; 202-S: 483 s predicted, ~486 s
      actual);
    * the budget B(N) = ⌈1.5 × (133 + 35 × N)⌉ and its three branches (default
      / explicit `--timeout B` / HALT above 3600);
    * the fact that the per-archive term tracks a full index rebuild and grows
      with index size, and that the coefficients are re-derived from
      `.backlogit/logs` when a cascade exceeds its prediction by more than the
      margin's headroom;
    * the reason for the finite ceiling: a timeout ends in exit 6
      `indeterminate`, and a too-short timeout tears a healthy cascade.
* **Tests (2 scenarios, new test class in `tests/test_flat_manifest_closure_docs.py`):**
  1. *gates-reference coherence.* `docs/gates-reference.md` contains
     `` f"`--timeout` is {MIN}-{MAX} seconds (default {DEFAULT})" ``, built
     from the runner constants. It has exactly one `### Timeout sizing`
     heading, and that section contains the budget formula string and a HALT
     branch naming `{MAX}`.
  2. *skill sizing note.* For both `RECONCILE_FILES`, the
     `cascade-sub-procedure` marker region contains the budget formula, the
     default `{DEFAULT}` and ceiling `{MAX}` values from the runner constants,
     the HALT branch, and the stay-attached sentence. Neither file contains
     `30-900`.
* **Functions touched:** 0 production; 2 test methods.
* **Posture:** test-after-edit (docs are prose). Write the gates-reference
  edit, then the pins over it and the A8c note.
* **Size / complexity:** XS / low. **Harness surface:** `harness-surface:none`.
* **Depends on:** A8b and A8c. A8d pins the A8c note, and is the last unit,
  so the docs change lands after the code.

## Dependency Graph

```text
A8a (192.023-T)
 ├── A8b (192.024-T) ──┐
 └── A8c (192.025-T) ──┴── A8d (192.026-T)
```

Edges (`later blocks-on earlier`):

* 192.024-T ← 192.023-T
* 192.025-T ← 192.023-T
* 192.026-T ← 192.024-T
* 192.026-T ← 192.025-T

There are no cycles. Manifest order (appended to 198-S after `192.010-T`):
192.023-T, 192.024-T, 192.025-T, 192.026-T.

## Constraints

* **Role boundary.** Stage plans and harvests only. Ship implements, runs
  tests, refreshes the manifest checksum, and opens the PR.
* **Width.** Each unit keeps to one concern. Code and tests are coupled in A8a
  and A8b because they pin the same constant. Docs and tests are coupled in A8d.
* **Scope (P-021 C1).** No change to:
  * the exit-code table, `_CASCADE_CLOSE_MUTATION`, or the evidence record
    shape;
  * `gates/cascade_evidence.py`;
  * `run_bounded` and its kill path;
  * `PROBE_TIMEOUT_SECONDS`, `_KILL_WAIT_SECONDS`, or `_READER_JOIN_SECONDS`;
  * the Ship agent templates;
  * the circuit-breaker instruction (stash `9869AA32` stays deferred).
* **Linked-deliberation hygiene.** New task bodies cite no deliberation
  artifact ID (`NNN-DL`). Doing so would add linking members to the 198-S
  disposition snapshot and widen the closure-time drift surface. The source
  deliberation is cited by path.
* **Manifest change authorization.** Appending to the active 198-S manifest is
  operator-authorized closure-blocking remediation (frontmatter
  `operator_authorization`). Feature first; tasks follow in dependency order
  after the existing items.
* **Canonical test runner.** `$env:PYTHONPATH='src'; python -m unittest discover -s tests`.

## Rejected Alternatives

Details are in the source deliberation.

* **Size-derived default (B):** puts coefficients in code and needs more
  plumbing, for no present benefit.
* **No ceiling (C1):** removes the hung-engine guard.
* **Stall timeout (C2):** needs a new mechanism (that is stash `9869AA32`'s
  design space).
* **Preflight refusal (C3):** puts coefficients in code and adds a new exit
  path.
* **Recording the timeout in evidence (C4):** a schema change that the fix does
  not need.
* **Running 198-S now with `--timeout 900`:** the operator chose option 1.
* **A new shipment for the fix:** blocked by `pre_claim`
  (`PRECLAIM_ACTIVE_SHIPMENT_PRESENT`).
* **Two tasks (code + tests, then docs/template):** each would exceed the
  fewer-than-3-files rule (four and five files).

## Risks and Caveats

| Risk | Mitigation |
|---|---|
| A longer default delays detection of a hung engine (up to 30 min, or 60 min at the ceiling) | Accepted. Either way the result is exit 6 and operator review. A too-short timeout damages a healthy cascade. |
| Index growth outpaces the 1.5× margin | Re-derivation rule documented (A8d). The margin absorbs about +45 % per-artifact cost. |
| Template and mirror diverge, or the manifest checksum goes stale | Existing parity and checksum tests. A8c names the LF staged-blob procedure. |
| 198-S `pre_close` record mismatches the grown manifest | Mutating run exits 4 (non-mutating). Refresh procedure in Runtime Verification and Closure. |
| A future change to the constants leaves a stale literal | A8a, A8b, and A8d derive every expected string from the runner constants. |

## Plan Hardening Signals

* **Public API, schema, or contract change:** present. The input range of a
  shipped CLI command widens and its default changes. Every previously valid
  value stays valid, and no schema or evidence change is made.
* **Security, auth, permission, or compliance-sensitive behavior:** absent.
* **Migration, backfill, destructive data or config action, or irreversible
  step:** present, indirectly. The command whose bound changes is destructive,
  and the 198-S closure needs `--replace-pre-close` (destructive) before its
  mutating run.
* **External integration, operator checkpoint, or external dependency:**
  present. The backlogit 1.11.0 cost model is an external measurement, and the
  `--replace-pre-close` and mutating-run approvals are operator checkpoints.
* **High runtime, rollout, or rollback risk:** absent. The change is constants
  and prose, and reverting one commit restores the old range.

Requires plan hardening: yes

## Runtime Verification and Closure

* **A8a and A8b change a runtime surface (CLI).** Ship verifies:
  * `autoharness shipment cascade-close --help` prints `30-3600 seconds` and
    `Default: 1800.`;
  * a mutating argv with `--timeout 3601` exits 2 before any resolution;
  * `--timeout 3600` parses (the CLI tests stub the resolution).
* **A8c and A8d change no runtime surface.** They are prose, verified by the
  doc pins.
* **198-S closure (Ship, after the remediation PR merges):**
  1. Move the four remediation tasks to `done` in the normal Ship flow.
  2. **With operator destructive-command approval**, run
     `--classify-only --replace-pre-close` for 198-S / 192-F at the original
     merge SHA `eb8b7811...`. Do not run plain `--classify-only`: the existing
     `pre_close` record makes it exit 2 (no-clobber). Skipping the replace
     means the mutating run's revalidation of the 23-item record against the
     27-item manifest exits 4, with nothing mutated.
  3. Compute N = 28 and B = 1670 ≤ 1800, so no `--timeout` is needed.
  4. Run the mutating `cascade-close` with destructive-command approval,
     attached until exit.
  * If the merge commit used for the close changes, Ship follows the
    shipment-reconcile rules for the SHA; this plan does not change them.
* **Operational closure.**
  * Rollback trigger: any cascade that exits 6 with `timed_out` under a budget
    the rule said was sufficient. Ship records a residual-risk entry and Stage
    re-derives the coefficients.
  * Monitoring window: the next three CASCADE closes record their wall time in
    the closure artifact against B(N).
  * Owner: Ship.

## Plan Hardening

* **Hardening required:** yes (three signals present). The hardening is
  proportionate to a constants-and-prose change.
* **Learnings and instructions consulted:**
  * `docs/compound/2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`.
    A timeout is never a clean negative. This is why exit 6 stays
    `indeterminate`, and the plan does not change that.
  * shipment-reconcile Step 0(c) and Cascade Close Sub-Procedure routing.
  * the `.backlogit/reconcile/198-S-cascade-close-20261003-051645.md` measurements.
* **Protected invariants:**
  * INV-T1: `MIN_TIMEOUT_SECONDS <= DEFAULT_TIMEOUT_SECONDS <= MAX_TIMEOUT_SECONDS`,
    all finite integers.
  * INV-T2: `validate_timeout` still rejects bool, float, and str, and every
    out-of-range value, with `EXIT_INPUT` (exit 2) before any spawn.
  * INV-T3: a timeout still kills the process group and exits 6
    `indeterminate`. It is never re-read as no mutation.
  * INV-T4: the help, gates-reference, and skill numbers equal the runner
    constants (test-derived).
  * INV-T5: the evidence record shape and the validator are unchanged.
* **ProposedAction / ActionRisk:**

  | ProposedAction | ActionRisk | Approval |
  |---|---|---|
  | Widen the `--timeout` range and raise the default (A8a) | low: additive, reversible, tests pinned | PR review |
  | Edit the shipment-reconcile Cascade Close Sub-Procedure in template and mirror, and refresh the manifest checksum (A8c) | low: prose plus parity | PR review |
  | `cascade-close --classify-only --replace-pre-close` for 198-S/192-F (closure) | high: destructive overwrite of the `pre_close` record | operator destructive-command approval |
  | Mutating `cascade-close` for 198-S/192-F (closure) | high: destructive cascade | operator destructive-command approval |

* **Review-gate capability risk:** reviewer-subagent dispatch is not exposed
  in this Stage session as a native tool. Plan review must emit literal
  `dispatch_mode:` and `decision:` markers. If subagent dispatch is
  unavailable, it must declare `single-agent-declared-degradation` and still
  cover every selected persona.
* **Unresolved operator decisions blocking safe execution:** none for
  implementation. The two closure approvals above are taken at closure time
  (dark-factory P-017: Orchestrator relay).

## Review Refinement

Review record: `docs/reviews/2026-10-03-cascade-close-timeout-cap-plan-review.md`.
Refinements applied from review are listed in the review record and in this
section.
