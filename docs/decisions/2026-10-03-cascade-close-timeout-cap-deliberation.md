---
title: "cascade-close --timeout contract: raise the fixed ceiling and the default to cover the measured backlogit 1.11.0 cascade cost"
description: "Deliberation on stash F50BD40F. The mutating `autoharness shipment cascade-close` caps `--timeout` at 900 s (default 120 s), below the measured `backlogit shipment ship` cost (~133 s + ~35 s per artifact). Decision: keep a fixed, finite range and raise it: MAX_TIMEOUT_SECONDS 900 -> 3600, DEFAULT_TIMEOUT_SECONDS 120 -> 1800, MIN unchanged at 30. A documented sizing rule tells Ship when to pass an explicit --timeout and when to halt instead."
topic: "Stash F50BD40F — cascade-close --timeout hard cap below observed backlogit 1.11.0 shipment ship cost"
depth: "standard"
decision_status: "decided"
promoted_to: "plan"
source_stash: F50BD40F
operator_decision: "Fix the cap first. Option 1. (recorded 2026-10-03; Orchestrator relay, dark-factory P-017, operator AFK)"
linked_artifacts:
  - ".backlogit/reconcile/198-S-cascade-close-20261003-051645.md"
  - "docs/plans/2026-10-03-cascade-close-timeout-cap-plan.md"
  - "src/autoharness/shipment_close/runner.py"
  - "src/autoharness/cli.py"
  - "docs/gates-reference.md"
  - "templates/skills/shipment-reconcile/SKILL.md.tmpl"
tags:
  - "cascade-close"
  - "timeout"
  - "P-015"
  - "closure-blocking"
  - "198-S"
---

# cascade-close `--timeout` contract (stash F50BD40F)

## Problem Frame

`autoharness shipment cascade-close` (shipped by 198-S / 192-F, PR #482, merge
`eb8b7811`) bounds its single `backlogit shipment ship` spawn with
`run_bounded(..., timeout=timeout)`. `src/autoharness/shipment_close/runner.py`
fixes the accepted range and the default:

```python
DEFAULT_TIMEOUT_SECONDS: Final = 120
MIN_TIMEOUT_SECONDS: Final = 30
MAX_TIMEOUT_SECONDS: Final = 900
```

On expiry the runner kills the backlogit process group. The command then exits
6 with `mutation_possible: indeterminate`. That leaves a torn backlog that only
an operator can recover. Re-running, committing, and substituting `SAFE_CLOSE`
are all forbidden.

The measured cost of `backlogit shipment ship` on this workspace is far above
both numbers (halt report
`.backlogit/reconcile/198-S-cascade-close-20261003-051645.md`, from backlogit's
own event logs):

| Shipment | Artifacts (N) | Model 133 + 35 N | Actual |
|---|---|---|---|
| 201-S | 12 | 553 s | 581 s |
| 202-S | 10 | 483 s | ~486 s |
| 198-S (as halted) | 24 | 973 s (~1020 s at +5 %) | not invoked |

The per-artifact term is ~8.6 s `commit_tracked` plus ~26.4 s `archived`. The
archive term tracks a full index rebuild (`backlogit sync` measured 25.45 s at
~1,692 indexed artifacts), so it grows with the index.

Every cascade measured on this workspace has exceeded the 120 s default. The
skill's mutating invocation passes no `--timeout`, so it would always get 120 s.
198-S cannot reach `post_close` at all, because even `--timeout 900` is below
the prediction. Ship correctly halted after `--classify-only` exit 0 and before
the mutating run. The backlog is unmodified.

**Operator decision (recorded):** "Fix the cap first. Option 1." Fix stash
`F50BD40F` before completing the 198-S post-merge closure (halt-report option
1), then re-run the mutating command.

**Routing constraint and its authorization (recorded):** the `pre_claim`
machine gate requires zero active shipments (`src/autoharness/gates/topology.py`,
`PRECLAIM_ACTIVE_SHIPMENT_PRESENT`). 198-S (feature 192-F) is still `active`
because its closure is pending. A new shipment therefore cannot be claimed. The
fix is harvested as remediation tasks under the still-active feature `192-F`
and appended to the active `198-S` manifest. **The operator explicitly
authorized this change to the active shipment manifest as closure-blocking
remediation** (Orchestrator relay, 2026-10-03, dark-factory P-017). Without
that authorization, Stage would not modify an active shipment's manifest.

Depth: **standard**. The change is a shipped command's input contract, but it
only involves constants, help text, and docs. No new mechanism is introduced.

## Research Findings

* **Where the numbers live.** The numbers appear only in `runner.py`
  (constants, the `validate_timeout` docstring, and the error message, which is
  built from the constants), in `cli.py` `SHIPMENT_USAGE` (the literal
  `30-900 seconds` and `Default: 120.`), and in `docs/gates-reference.md` (the
  mode-table row, `30-900 seconds (default 120)`). `command.py` imports
  `DEFAULT_TIMEOUT_SECONDS` and `validate_timeout`. The CLI parser calls
  `validate_timeout`. The evidence record and its validator
  (`gates/cascade_evidence.py`) do not record or check the timeout. A change
  to the constants therefore does not change the record shape or older records.
* **Test pins.** `tests/test_shipment_close_runner.py` asserts
  `DEFAULT_TIMEOUT_SECONDS == 120`, accepts `(30, 120, 900)`, and rejects
  `901`. `tests/test_cli_shipment_cascade_close.py` rejects `--timeout 901` and
  accepts an explicit `900`. Both must change together with the constants, or
  the suite goes red.
* **The skill's invocation.** `shipment-reconcile` (Cascade Close
  Sub-Procedure, `cascade-close-routing` block `cascade-sub-procedure`) runs the
  mutating command without `--timeout`. In practice, the default is the
  operative value.
* **Historical shipment size.** All 201 shipment records on this workspace
  have a manifest of at most 23 items (198-S is the largest; the median is 5).
  So N = |closure_scope(S)| = items + 1 is at most 24. With the four
  remediation tasks added, 198-S becomes 27 items, so N = 28.
* **Learnings.** `docs/compound/` has no prior solution for subprocess timeout
  sizing. `2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md` is
  about a different surface. Engram, intercom, and graphtor are degraded for
  this session, so file search was used.

## Options Evaluated

### Option A: Raise the fixed range (chosen)

Set `MAX_TIMEOUT_SECONDS = 3600` and `DEFAULT_TIMEOUT_SECONDS = 1800`. Keep
`MIN_TIMEOUT_SECONDS = 30`. Document one sizing rule that Ship applies before
the mutating run.

* Planning budget: B(N) = ⌈1.5 × (133 + 35 × N)⌉ seconds. The 1.5 factor
  absorbs the +5 % model error seen on 201-S, host variance, and index growth
  (the archive term grows with index size).
* B(N) ≤ 1800 exactly when N ≤ 30, that is, manifests of up to 29 items. That
  covers every shipment recorded on this workspace, including the remediated
  198-S (N = 28, C = 1113 s, B = 1670 s). The skill's invocation, which passes
  no `--timeout`, is therefore safe by default.
* B(N) ≤ 3600 exactly when N ≤ 64, so an explicit `--timeout` covers manifests
  of up to 63 items.
* Above that, Ship halts before the mutating run. It never invokes with a
  timeout that is known to be too short.

Cost: two constants, one docstring, two help lines, one docs row plus a short
sizing section, a skill note, and the test pins.

### Option B: Default derived from the closure-scope size, bounded by a ceiling

When `--timeout` is absent, compute the default after classification from
|closure_scope(S)|, for example `min(MAX, ⌈1.5 × (133 + 35 × N)⌉)`.

* The fixed and per-artifact coefficients would be built into code. They
  were measured on one workspace, one host, one engine version, and one index
  size, and they drift with all four. A wrong coefficient in code is harder to
  see and to correct than a documented rule.
* The CLI resolves the default before the shipment is read
  (`_parse_cascade_close_args`). Option B needs a sentinel "unset" value,
  plumbed through `run_cascade_close` to the point where N is known, plus
  evidence or JSON output saying which timeout was used. That touches more
  functions and more tests than a constant change.
* For every shipment this workspace has produced, the result equals Option A's
  default anyway, because B(N) ≤ 1800.

Rejected for now, as complexity without a present need (coding discipline:
simplest change that fully solves the problem).

### Option C1: Remove the ceiling (or make it very large, for example 24 h)

Rejected. The timeout is the only guard against a hung engine that holds the
pair lock and the queue lock indefinitely. The operator brief requires a finite
ceiling.

### Option C2: Stall-based (no-progress) timeout instead of a wall-clock timeout

Kill only when the engine produces no output for some interval. `shipment ship
--format json` emits its result at the end, so stdout silence is normal for the
whole run. A progress signal would need log-file tailing of `.backlogit/logs`,
which is a new mechanism. Rejected. This is the design space of stash
`9869AA32` (below).

### Option C3: Pre-invocation preflight that refuses an under-sized timeout

Have the command estimate the cost and exit 2 when `--timeout` is below it.
This has the same coefficient-in-code problem as Option B, plus a new
refusal path in the exit-code contract. Rejected. The same protection is given
procedurally by the sizing rule's HALT branch.

### Option C4: Also keep the evidence of which timeout was used

Recording `timeout_seconds` in the `invoking` record would aid post-mortems of
an exit 6. But it changes the evidence schema and validator for a value that
is already visible in the command line and the closure report. Rejected as out
of scope.

## Trade-off Comparison

| Criterion | A: fixed raise | B: size-derived default | C1: no ceiling | C2: stall | C3: preflight |
|---|---|---|---|---|---|
| Covers measured cost for all historical sizes | yes (default) | yes | yes | yes | n/a |
| Finite safety guard kept | yes (3600 s) | yes | no | yes | yes |
| Coefficients in code | no | yes | no | no | yes |
| Files / functions touched | fewest | more | fewest | many (new mechanism) | more |
| Exit-code / evidence contract change | none | JSON/evidence addition | none | new | new refusal path |

## Decision

**Adopt Option A.**

* **D1 — Constants.** `MAX_TIMEOUT_SECONDS = 3600`, `DEFAULT_TIMEOUT_SECONDS =
  1800`, `MIN_TIMEOUT_SECONDS = 30` (unchanged). `validate_timeout` keeps its
  integer-only, bool-rejecting, inclusive-range rule. Only its docstring changes
  (`30-3600 s`). Its error message is already built from the constants.
* **D2 — Surfaces stay coherent.** `cli.py` help (`30-3600 seconds`,
  `Default: 1800.`) and `docs/gates-reference.md` (`30-3600 seconds (default
  1800)`) state the new range. Tests derive their expectations from the runner
  constants, so the next change cannot leave a stale literal behind.
* **D3 — Sizing rule (documented, not coded).** Use the formula in
  `docs/gates-reference.md` and a one-paragraph note in the shipment-reconcile
  Cascade Close Sub-Procedure (template and installed mirror):
  * N = |closure_scope(S)| = manifest items + 1 (the shipment record).
  * B(N) = ⌈1.5 × (133 + 35 × N)⌉ seconds.
  * B ≤ 1800: use the default.
  * 1800 < B ≤ 3600: pass `--timeout B`.
  * B > 3600: HALT before the mutating run. That needs an operator decision,
    and Ship never invokes with a timeout known to be too short.
  * The coefficients are the backlogit 1.11.0 measurements from this
    workspace. Re-derive them from `.backlogit/logs` when a cascade runs longer
    than its model prediction by more than the margin's headroom.
* **D4 — Attached run.** The note tells Ship to stay attached to the mutating
  run until the command exits, and never to abandon or kill it on an agent-tool
  wait shorter than `--timeout`. Killing the command externally mid-cascade
  has the same torn-backlog effect as an internal timeout. This one sentence is
  the only part of the agent-runtime question that the fix trivially requires.
* **D5 — No change** to the exit-code table, the evidence record, the
  validator, `run_bounded`, the kill path, `PROBE_TIMEOUT_SECONDS` (30 s; the
  version probe is fast), or `_KILL_WAIT_SECONDS`.
* **D6 — Closure-blocking remediation routing** (operator-authorized). The
  remediation is harvested under the still-active feature `192-F`, as the next
  task IDs after `192.022-T`, and appended to the active `198-S` manifest in
  dependency order, after the existing items, with the feature first. No new
  shipment is created (the `pre_claim` gate forbids a second active shipment).
* **D7 — Consequence for the 198-S closure** (procedural, Ship-owned). The
  `pre_close` record `docs/closure/evidence/198-S-192-F-close-evidence.json`
  snapshots the 23-item manifest. Once the remediation tasks join the manifest,
  the mutating run's revalidation will see a different manifest and exit 4,
  with nothing invoked. Before the mutating run, Ship must refresh the record
  with `--classify-only --replace-pre-close`. That is a destructive command
  that needs operator (destructive-command) approval. It must run after the
  remediation tasks are `done` and the fix is merged. The mutating run then
  uses the default 1800 s (N = 28, B = 1670 s).

### Relation to stash `9869AA32` (out of scope)

`9869AA32` asks whether long-running P-015 cascade closes need their own
stall-detection timeout class in the agent circuit-breaker policy (the 5-minute
"other commands" limit, which did not terminate the 9.8-minute 201-S run). That
question is about agent-runtime policy (the circuit-breaker instruction). It is
a different contract surface from this command's own `--timeout` bound. This
fix does not need it. The command's bounded timeout stays the authoritative
guard, and D4's single "stay attached" sentence covers the only interaction
that matters here. `9869AA32` stays deferred in the stash, unchanged.

## Rejected Alternatives

* **Option B (size-derived default):** coefficients in code, more plumbing, and
  no present benefit over A for any shipment size seen so far. Revisit if
  shipments routinely exceed about 29 items.
* **Option C1 (no ceiling):** removes the hung-engine guard. Excluded by the
  brief.
* **Option C2 (stall timeout):** needs a new progress mechanism. Its design
  space is `9869AA32`.
* **Option C3 (preflight refusal):** coefficients in code, plus a new refusal
  path. The sizing rule's HALT branch gives the same protection.
* **Option C4 (record the timeout in evidence):** schema change, not needed for
  the fix.
* **Running 198-S now with `--timeout 900`** (halt-report option 2): the
  operator chose option 1. That run is predicted to time out mid-archive.

## Unresolved Questions

* None blocks planning.
* The sizing coefficients are measurements, not guarantees. Recalibration is a
  documented manual step, not an automatic one.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| A hung engine now holds the locks for up to 30 min by default, or 60 min at the ceiling, instead of 2 or 15 min | Accepted. A hang ends in exit 6 and operator review either way. A too-short timeout tears a *healthy* cascade, which is the worse outcome. The ceiling stays finite. |
| Index growth raises the per-artifact cost beyond the 1.5× margin | The sizing rule names the re-derivation source (`.backlogit/logs`). The margin absorbs about +45 % per-artifact growth. |
| Docs, help, and constants drift apart again | Tests derive expected strings from the runner constants (D2). |
| Ship forgets the sizing rule for a large shipment | For every size seen so far, the default already covers B(N). Above N = 30, the skill note is pinned by a docs test. |
| The 198-S record no longer matches the grown manifest | D7: a `--replace-pre-close` refresh under operator approval before the mutating run. Exit 4 is non-mutating, so a missed refresh fails safe. |

## Quality Criteria

* After the change, the mutating run's default covers B(N) for N ≤ 30, and the
  remediated 198-S (N = 28) closes without an explicit `--timeout`.
* No literal `30-900` or `default 120` remains in `src/`, `docs/gates-reference.md`,
  or the shipment-reconcile skill (template and mirror).
* The canonical unittest suite stays green.
