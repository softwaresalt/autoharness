---
problem_type: headless-eval-runner-deterministic-reviewer
category: evaluation
root_cause: building an evaluation harness inside an install/tune tool that has no live model runtime forces injectable execution + rule-based grading, and coupling/parsing shortcuts leak state or misread diffs
tags: [eval, reviewer, deterministic, injectable-runner, replay, unified-diff, telemetry-coupling, hermetic-test, backlogit, shipment-ship, cascade-bug]
created: 2026-07-02
shipment: 056-S
---

# Headless Eval Runner + Deterministic Reviewer Matrix (No Live Model Runtime)

## Problem

autoharness is a template/install/tune tool, not a model host. Shipment B of
055-F needed an *evaluation* capability (run a task through a model matrix and
grade the result) even though the tool has **no live model runtime** and CI must
stay hermetic. Naive designs either (a) reach for a network model call, (b) let
the grader depend on non-deterministic model output, or (c) couple evaluation
and telemetry so tightly that a telemetry failure aborts the eval — or vice
versa. Several correctness traps only surfaced under adversarial review.

## Root Cause

- **No runtime → cannot call a model.** The runner must accept an *injectable*
  execution function and support a *replay* path so the same eval is
  reproducible offline and in CI.
- **Deterministic grading is not "ask a model to review".** A model-graded
  reviewer is non-reproducible and untestable. The grade must come from a
  *rule-based, line-cited* diff grader whose output is a pure function of the
  diff text.
- **Bidirectional coupling is a footgun.** If eval writes telemetry *and*
  telemetry can re-enter eval, a failure on either side cascades. The correct
  shape is **one-way eval → telemetry** (fail-open emit), never the reverse.
- **Unified-diff parsing is deceptively stateful.** An added source line whose
  *content* begins with `+++ ` looks exactly like a new-file header, so a parser
  that always treats `+++ ` as a header resets hunk state and silently drops the
  rest of the hunk's added/context lines.

## Solution

- **Injectable / replay runner.** `eval/runner.py` executes through a frozen
  execution loop that takes the model-invocation callable as a parameter; a
  replay path re-runs recorded outputs so CI never needs a model. Tests inject a
  deterministic fake instead of a network call.
- **Rule-based, line-cited diff grader.** `eval/reviewer.py` parses the unified
  diff into `AddedLine` records (path + new-line number) and applies explicit
  penalty rules, so every finding cites an exact file+line and the same diff
  always yields the same matrix result. `matrix.py` loads the model-config
  matrix; `summary.py` produces the comparative baseline summary.
- **One-way eval → telemetry coupling.** Eval emits telemetry as a fail-open
  side effect only; telemetry never calls back into eval. A telemetry sink error
  degrades to no-op and does not fail the eval.
- **Hermetic boundary test.** A boundary/hermeticity test asserts the eval path
  performs no live model call and stays inside the workspace, locking in the
  "no live runtime" invariant against regressions.
- **`+++ ` unified-diff edge case.** Gate new-file-header detection on hunk
  state: only treat `+++ ` as a header when **not** already inside a hunk
  (`if not in_hunk and raw.startswith("+++ ")`), and track the hunk's declared
  new-line count from the hunk header regex
  (`^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@`) so header detection stops once the
  hunk is exhausted. This prevents an added line like `+++ TODO` from resetting
  parser state and dropping subsequent added lines
  (`src/autoharness/eval/reviewer.py`, fixed in `46db958`). A sibling CLI fix in
  the same commit only treats the *leading* token as a help request so a git ref
  literally named `help` can still be passed as `--base`/`--head`.

## Prevention

- When adding an eval capability to a tool with no model runtime, make the
  execution callable a parameter and ship a replay path from day one; add a
  hermetic boundary test as an acceptance-blocking gate.
- Grade with rule-based, line-cited logic that is a pure function of its input;
  never route grading through a live model if reproducibility matters.
- Keep eval → telemetry coupling strictly one-way and fail-open.
- For any hand-rolled unified-diff parser, add a negative test for an added line
  whose content starts with `+++ ` (and `--- `), and derive header-detection
  from hunk state + the declared `@@ +c,d @@` count rather than a bare prefix
  check.

## backlogit `shipment ship` parent-cascade bug (operational hazard)

Closing this shipment surfaced (again) a destructive backlogit defect that must
be worked around during any shipment closure.

- **Bug.** `backlogit shipment ship <id>` walks from the shipped tasks to their
  **parent feature** and archives the parent, **orphaning/cascading its
  siblings** — including still-unimplemented tasks. On 056-S this would archive
  parent `055-F` and cascade `055.001-T` / `055.003-T` (the latter still blocked
  on an external `--size` dependency). `backlogit archive` is suspected of the
  same walk.
- **Safeguard: single-artifact operations + verify-after-every-mutation.**
  Never call `shipment ship` or `archive` for closure. Instead:
  1. `backlogit move <shipment> --status done` (single-artifact status change;
     transitions must be legal — a `queued` item needs `queued → active → done`,
     not a direct `queued → done`).
  2. `backlogit update <shipment> --commit <sha> --description ...` to record the
     release.
  3. After **every** mutation, re-read the parent feature and sibling tasks and
     assert their status/parent are unchanged (parent stays `blocked`, blocked
     sibling stays `blocked` with `parent_id` intact).
  4. If any invariant breaks, immediately `git restore .backlogit/`, delete any
     untracked ship-created files under `.backlogit/`, log which command
     cascaded, and switch to the fallback (record closure via `update` only).
- **Ship-then-verify / git-revert discipline.** The prior 056-S closure attempt
  hit the cascade and was git-reverted wholesale; treating the backlog as
  revertible working-tree state (not an irreversible tool action) is what makes
  recovery safe. A follow-up chore is stashed to upgrade/patch backlogit past
  this defect.
- **Version note.** In backlogit 1.3.0 the status enum is a single global set
  (`queued, active, blocked, review, done, accepted, rejected, archived`); a
  shipment can legitimately move to `done`. This supersedes the older
  `2026-05-07-backlogit-shipment-status-constraints` learning (per-type
  `shipped/abandoned` enum), which reflected an earlier `header-def.yaml` schema.
