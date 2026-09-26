---
title: "Proof D run 3 (PE-1.4) - budget equation and read-limit exhaustion: findings (FAIL, fixture negative controls not admissible)"
source: "docs/decisions/2026-09-24-read-budget-proof-d-run3-spike.md"
doc_type: decision
description: "Stage-authored findings for the independent Proof D run 3 under charter PE-1.4, section 6.6 (unchanged since PE-1.2) and section 6.1 per-invocation gates. Ship ran one disposable synthetic scratch fixture once, and it exited 0. Stage hashed the retained fixture read-only (SHA-256 BB7E1EB0...3313FA, which matches the parent's value) and inspected every assertion. Part 1 (file-slot guarantee) and Part 2 (byte distinction, with non-refunding byte reservations actually simulated) are met. Part 3 is met as worded: 108 cases cover every charter-named stage, including the queue and archive subtypes (9 stages x 3 codes x 4 would-be outcomes). It does not discriminate, because the modelled reducer returns a constant and never uses the stage or the would-be outcome. Part 4 is NOT met. No control mutates the model the fixture validates, or passes a mutant through the fixture's own validators. Run 1 controls 1, 3 and 4 are not reproduced as defined in run 1 (control 1 is a literal 0 == 1), and PE-1.2 controls 5, 8 and 9 are caught by constant or short-circuit expressions that cannot fail. Under section 6.6 ('a negative control is not caught'), the verdict is FAIL. No counterexample to the decided contract was found, and decisions 1 and 2 of the budget decision are not reopened. The route is charter change control to make 'caught' in section 6.6 part 4 concrete before a run 4. Separately, Ship's stdout SHA-256 was reported truncated (bdeffb49...f5d34), so PE-EVIDENCE-01 is not met either, and that alone would have prevented a PASS. Run 1 stays FAIL and run 2 stays historical PASS. Nothing in production was exercised."
docline:
  type: spike
  date: 2026-09-24
  time_box: "45m"
  conclusion: "pivot"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "read-budget"
    - "file-count-limit"
    - "reducer"
    - "negative-controls"
    - "proof-entry"
    - "ship-lifecycle"
proof: D
proof_run: 3
proof_verdict: FAIL
proof_verdict_scope: synthetic-contract-fixture-admissibility
contract_counterexample_found: false
prior_run_artifacts:
  - {run: 1, path: docs/decisions/2026-09-23-read-budget-proof-d-spike.md, verdict: FAIL, matrix: PE-1.1}
  - {run: 2, path: docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md, verdict: PASS, matrix: PE-1.2, pe_1_4_admissible: false}
prior_run_verdicts_changed: false
decision: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md
decision_reopened: false
decision_implemented: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.4"
matrix_id: PE-1.4
matrix_rows: [PE-DATA-03, PE-SAFETY-04, PE-EVIDENCE-01, PE-ACTIVATE-01]
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 309ab0e2
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
publication_eligible: false
actor_invoked: false
backlog_item_created: false
plan_changed: false
fail_route: "charter change control: make section 6.6 part 4 'caught' concrete (each control mutates the fixture model under test and is rejected by the same validators that accept the correct model), then Proof D run 4 under PE-1.4 with full PE-EVIDENCE-01 output hashes"
time_bound_status: met-by-conservative-upper-bound
file_bound_status: met
scratch_cleanup_status: "retained at authoring; Stage deleted nothing"
stage_model_route: "claude-opus-5.5/anthropic/high requested; unverified by Stage (DEGRADED: route not self-verifiable)"
---

# Proof D run 3 findings (PE-1.4) - budget equation and exhaustion

## Verdict

| Field | Value |
|---|---|
| Verdict | **`FAIL`** |
| Why | Section 6.6 part 4 is not met. The fixture's negative controls are constant or short-circuit expressions. None mutates the model the fixture validates, and none is rejected by the fixture's own validators. Run 1 controls 1, 3 and 4 are not reproduced as run 1 defined them. Section 6.6 fail criterion: "a negative control is not caught" |
| Contract status | **No counterexample** to `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md` was found. Decisions 1 and 2 are **not reopened**. The `FAIL` is about the admissibility of this run's evidence, not about the decided contract |
| Parts | Part 1: met. Part 2: met. Part 3: met as worded, but does not discriminate. **Part 4: not met** |
| Independent evidence gap | `PE-EVIDENCE-01` is not met: Ship reported the stdout SHA-256 truncated (`bdeffb49...f5d34`), and several listed fields were not in the relayed handoff (see Evidence Gaps). This alone would have prevented a `PASS`. The `FAIL` does not depend on it, because it follows from the hash-verified source |
| Why not `BLOCKED` | Every section 6.1 per-invocation gate passed as Ship reported, and the fixture executed. The failure details are precise and come from source that Stage hashed. The evidence gap would gate only a `PASS` |
| Route (section 6.1) | Charter change control (Phase 0), named in `fail_route` above. No plan rewrite |
| Prior runs | Run 1 stays **`FAIL`** (PE-1.1). Run 2 stays a historical **`PASS`** (PE-1.2, synthetic contract only), and under section 3.3 it is still not admissible for PE-1.4 proof exit. Neither artifact is edited |
| Production | No production resolver exists. None was exercised or is claimed |

## Goal

This run answers charter section 6.6 (unchanged in PE-1.4) under the PE-1.4
section 6.1 execution rules.

1. With admitted membership `1..48`, does the claim count fit `max_files=256`
   with the recorded margin for every admitted input?
2. Does every read-limit error at every read or recheck stage reduce to
   `UNRESOLVED / 2`, never `NO_HARNESS / 1` or `HARNESS_READY / 0`? This
   includes byte exhaustion, which is explicitly not guaranteed to fit.

Run 3 is the new admissible PE-1.4 run that section 3.3 requires, because
run 2 has no recorded Ship index refresh.

## Success Criteria

* **Pass**: all four section 6.6 parts are met, the time and file bounds are
  met, and the `PE-EVIDENCE-01` fields are complete.
* **Fail**: any section 6.6 fail criterion is present, or a bound is exceeded.
* **Blocked**: a section 6.1 gate rejected execution, or a required
  environment or evidence item made a determination impossible.

## Scope Constraints and Learnings

* Stage worked read-only. It ran no fixture, test, build, linter or index
  sync, and it made no backlog read or edit (operator scope; P-010;
  section 6.1).
* The only computation Stage ran was a SHA-256 of the retained fixture file,
  plus string hashing for the corroboration below. Neither executes the
  fixture.
* This artifact is the only tracked change. No amend, push, PR, branch or
  claim. The P-016 exception was not used.
* **Compound learnings.** Stage searched `docs/compound/` first and found no
  entry on read budgets, Proof D or negative-control admissibility. The
  matching entries concern shipment status, worktree topology and review
  scrutiny, and none applies here. No prior learning was used.
* **Tool states (`PE-EVIDENCE-05`).** backlogit was not probed by Stage,
  because the operator restricted Stage to no backlog read or sync. Ship
  reported backlogit working. engram, intercom and graphtor-docs were not
  probed (not needed for a read-only static adjudication). This is declared
  degraded visibility, not a silent fallback.

## Inputs

These are decided parameters from the decision and section 6.6:

```text
C(N,U,rho) = 4(N+1) + 3U(1+rho)     N in 1..48, U,rho in {0,1}  -> 192 cases
max_files=256, max_file_bytes=4 MiB, max_total_bytes=32 MiB
margin rule: C(N,U,1) + (N+1) <= 256
bytes: P_max = 2(N+1) + 3U(1+rho) non-refunded reservations (decision, Byte budget)
class 1b: read-limit error at any stage -> UNRESOLVED / 2 / <first ReadErrorCode>
stages (decision 2.1): shipment queue|archive candidate, member queue|archive candidate,
  manifest read, template read, installed-file read, candidate ledger recheck, surface recheck
```

The charter names seven stage groups, which make nine stages when the queue
and archive subtypes are counted. The operator's brief mentions eight groups.
Stage adjudicated against the charter and decision text: seven groups, nine
subtypes.

## Evidence Provenance

### Fixture (Stage, independent and read-only)

| Item | Value |
|---|---|
| Scratch path | `.proof-scratch\D-run3-20260924-150500\` (Git-ignored by `.gitignore:10 .proof-scratch/`). The directory was created at 2026-09-24T15:11:13-07:00 |
| Listing | One file, `proof_d_run3.py`, 12,753 bytes, last written 2026-09-24T15:11:48-07:00 |
| SHA-256 (Stage-computed) | `BB7E1EB05701C386B22BFD479BF4F3A51AF542662476C78736889D877A3313FA`. It matches the parent-confirmed value |
| Imports | `itertools.product`, `sys`, `time` only. No production code and no filesystem or backlog I/O |

### Ship verification-only invocation (as relayed, not re-run)

This was a new Ship invocation, after an earlier invocation's PowerShell
checkpoint projection failed. That failed projection stays historical and is
not reinterpreted.

| Gate / fact | Result (Ship-reported) |
|---|---|
| Index refresh | Cache-only sync, exit 0. stdout 23 B, SHA-256 `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873`. stderr 0 B. The transport name was not stated in the relay |
| Checkpoint scan | Python in-process capture: 71 summaries, 0 quarantined, 0 anomalies, 0 active. The abandoned checkpoint's official get returned `valid: true` |
| P-001 | Active shipments, tasks, features and chores: 0 each, from reads made after the refresh. `173-S` closure is READY with compaction done (context only) |
| P-002 / P-010 / P-011 / P-016 | No claim. Self-check clean. Clean current branch. One worktree |
| PE-ACTIVATE-01 | Three blobs match `4acba14a`. **Stage confirmed read-only at HEAD `309ab0e2`**: `4ccd7fdc2d134de485487acd75bfbc105d6f40ee`, `e22916b62f36f1c25c421882a05f4049f1862c02` and `251f46e8c95703ed65e421210d3b08682d79d8bc`. `git status --porcelain` is empty for the three paths |
| Execution | One execution, exit 0 |
| stdout | 307 B. SHA-256 **reported truncated**: `bdeffb49...f5d34` |
| stderr | 0 B. SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (the empty digest) |
| Ship segment | About 8 min |

### Stage corroboration (non-evidentiary)

The fixture's only success output is one deterministic `print` line, and only
its `elapsed_ms` value varies. Stage hashed candidate strings without executing
the fixture. Exactly one candidate of 307 bytes matches both reported hash
fragments: `elapsed_ms=0` with a CRLF line ending, full SHA-256
`bdeffb492e4373fc292e76ad479faa1ae148ec2892362c5f9f41457cb8df5d34`.

This corroborates that Ship saw the `PROOF_D_RUN3_PASS` line. It is Stage
reconstruction, **not** Ship-recorded evidence, and it does not satisfy
`PE-EVIDENCE-01`. Ship must correct the record from its own capture. Stage
did not invent the value.

## Findings by Part

### Part 1 - File-slot guarantee: met

* `simulate_claims` appends one claim per source for each of `N+1` records
  (four core sources), plus 3U surface initial reads and 3U·rho surface
  rechecks. Every trace is counted by length and asserted equal to
  `closed_form` for all 192 cases (`admitted == 192`).
* `C_max = 202`, margin 54, and the margin rule is asserted for every `N` and
  `U`. `N=17` is inside the simulated loop, and `C(17,1,1) = 78` is asserted.
* For `N` in `{49, 512, 513}` the result is `MEMBERS_TOO_MANY -> UNRESOLVED / 2`
  with at most 4 claims and 0 member lookups.
* Limitations:
  * The over-limit path is an early return by construction, so the
    "no member lookup" result is structural rather than observed.
  * The shipment record's queue and archive candidates are both labelled
    stable absence, and every member is labelled present in both. The count is
    unaffected, but this does not model the one-present, one-absent case
    realistically.

### Part 2 - Byte distinction: met, and reservations are simulated

* The worst case of 416 MiB is computed by arithmetic, as the charter
  requires, and asserted to exceed 32 MiB. The fixture makes no byte-fit
  claim.
* **The reservations are simulated, not only computed.**
  `reservation_error` reserves each attempted read in order, with no refund.
  For each read it checks the count limit, then the per-file cap, then the
  running total.
  * The `N=17, U=1, rho=1` stream is 42 reads of 4 MiB each. The first 8 fit
    exactly (32 MiB), and the 9th raises `TOTAL_SIZE_LIMIT`, which reduces to
    `UNRESOLVED / 2 / TOTAL_SIZE_LIMIT`.
  * One file of 4 MiB + 1 byte raises `FILE_SIZE_LIMIT`, which reduces to
    `UNRESOLVED / 2 / FILE_SIZE_LIMIT`.
  * 257 one-byte reads raise `FILE_COUNT_LIMIT`.
* Limitations:
  * The byte stream is sized from `P_max` and is not derived from the claim
    trace.
  * The stage passed with the `N=17` error (`manifest_read`) is a fixed
    label, not the stage at which the 9th reservation actually occurs.

### Part 3 - Exhaustion at every stage: met as worded, does not discriminate

* **Stage coverage is complete.** `STAGES` holds all nine charter-named
  stages: the shipment queue, shipment archive, member queue and member
  archive candidates, the manifest, template and installed reads, the
  candidate recheck and the surface recheck.
* **All four would-be outcomes are iterated**: `NO_SURFACES_REQUIRED`,
  `ALL_SURFACES_PRESENT`, `MISSING` and `STALE`. The count is
  9 × 3 × 4 = 108, and all 108 results were asserted to be
  `UNRESOLVED / 2 / <code>`.
* **Precedence and incomplete rechecks.** 27 precedence cases yield
  `INPUT_CHANGED_DURING_RESOLUTION`, and 6 incomplete-recheck cases keep the
  injected code.
* **Why the matrix does not discriminate.** `read_failure` ignores `stage`
  and `would_be` and returns a constant. No would-be outcome is ever computed
  and then overridden. As a result, the 108 assertions, the 27 precedence
  assertions and the `complete = False` incomplete-recheck assertions cannot
  fail for any model defect.
* Additional limitations:
  * Byte codes are injected at candidate stages modelled as present files.
    The absent-candidate rule, under which only `FILE_COUNT_LIMIT` applies, is
    asserted only through `applicable_codes` for member candidates. It is not
    injected, and it is not checked for shipment candidates.
  * The precedence result carries exit `None`.
  * "First `ReadErrorCode` in generation order" is not exercised with more
    than one error.
* These are recorded as defects in the evidence. They are not the fail cause
  on their own, because the literal part 3 criterion is met.

### Part 4 - Negative controls: NOT met (fail cause)

`catch(name, mutant_accepted)` records a control as caught whenever the
expression passed to it is false. No control changes `simulate_claims`,
`read_failure` or `reservation_error`, and no control re-applies the
validators in `run()` to a mutant. Run 1 set the standard: "Each control
changes the claim model and asserts that the change is caught", with mutant
counts at `N=17`.

| # | Control | Run 1 definition (N=17) | Run 3 expression | Stage finding |
|---|---|---|---|---|
| R1-1 | Stable absence charged | Mutant count 42 | `0 == 1` (literal scalars) | **Not caught.** No model is involved, so the expression cannot fail. Run 1's mutant is not reproduced |
| R1-2 | Ledger rechecks charged | Mutant count 39 | `2(N+1)+3U(1+rho) = 42` vs `78` | Caught at formula level. The mutant differs from run 1's |
| R1-3 | Surfaces not re-read per task | Mutant count 129 (`+3NU`) | Sub-count `54 == 3` | **Not caught at model level.** Constant sub-count comparison. The model total is never mutated |
| R1-4 | Off-by-one | Mutant counts 79 / 77 (±1 claim) | `74` / `82` (N±1, which is ±4 claims) | **Run 1 control not included.** The ±1-claim mutant is absent |
| P-5 | Admitted max 512 must be over budget | - | `512 <= 48 and ...` | **Not caught as required.** The first conjunct short-circuits. The over-budget count (2058) is computed but never asserted to exceed 256 |
| P-6 | Installed exhaustion not `MISSING` | - | Literal tuple vs `read_failure(...)` | Caught, but against the constant reducer only |
| P-7 | Exhausted candidate not absence | - | Literal tuple vs `read_failure(...)` | Caught, but against the constant reducer only |
| P-8 | Incomplete recheck not agreement | - | `"AGREEMENT" == "INCOMPLETE"` | **Not caught.** Literal strings. No recheck model is involved |
| P-9 | No success when reservations exceed 32 MiB | - | `168 MiB <= 32 MiB and ...` | **Not caught as required.** Arithmetic short-circuit. `reservation_error` is not applied to the mutant |

The fixture's `negative_controls=9/9` counts expressions that evaluated
false. It does not show that the checker catches any of the defects. The
controls marked "not caught" meet the section 6.6 fail criterion, and
run 1 controls 1, 3 and 4 are not present in the form run 1 defined. The
verdict is therefore **`FAIL`**.

## Evidence Gaps (PE-EVIDENCE-01)

These fields were missing from, or incomplete in, the handoff relayed to
Stage. Each would block a `PASS` on its own.

* The stdout SHA-256 is truncated (see the corroboration above; it is not a
  substitute).
* Host OS and version, filesystem and interpreter version were not relayed.
* The exact fixture command was not relayed verbatim.
* Precise fixture and Ship elapsed times: only "about 8 min" was relayed for
  the Ship segment.
* The explicit before and after `git status --porcelain` safety statement and
  the `--ignored -- .backlogit` comparison were summarized as "cache-only" and
  "clean", not shown.

Stage asks Ship for a correction from Ship's own captured records, **with no
re-execution**. Stage has not reconstructed these fields and does not claim
them.

## Matrix Row Status (Proof D only; not a proof-exit audit)

| Row | Status |
|---|---|
| `PE-DATA-03` | **Not satisfied by run 3.** The arithmetic parts hold, but the proof run fails part 4 |
| `PE-SAFETY-04` | **Proof D half not satisfied under PE-1.4.** The Proof G half is unchanged |
| `PE-EVIDENCE-01` | **Not met** for this run (see Evidence Gaps) |
| `PE-ACTIVATE-01` | Met at HEAD `309ab0e2` for this run (Stage read-only confirmation) |

No reason code is used or created beyond `MEMBERS_TOO_MANY`,
`FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT` and
`INPUT_CHANGED_DURING_RESOLUTION`.

## Time and File Bounds

| Item | Value |
|---|---|
| Conservative start | 2026-09-24T15:05:00-07:00, the scratch directory's name timestamp, which is earlier than its creation at 15:11:13 |
| Stage start | Operator directive at 2026-09-24T15:13:11-07:00 |
| Authoring | 2026-09-24T15:18:30-07:00 (host clock), before the commit |
| Upper bound | Under 30 min, which is within the 45m bound (Stage plus Ship). **Met** |
| File bound | One disposable file. **Met** |

## Scratch Hygiene

The scratch directory still existed at authoring. Stage read and hashed it
only, and deleted nothing. Cleanup remains Ship's or the parent's duty under
section 6.1, after its path is verified.

## Consequences and Recommendation

**Conclusion: pivot (confidence: high).** Route under section 6.1: charter
change control.

1. Make section 6.6 part 4 "caught" concrete. Each control should be a mutant
   of the fixture's model functions, and the same validators that accept the
   correct model should reject it. Run 1's control definitions and mutant
   counts (42, 39, 129, 79/77) should be the reference for the four run 1
   controls. Controls 5 and 9 should assert the over-budget case and the
   simulated reservation.
2. Also require that the exhaustion reducer model consumes the would-be
   outcome, so that part 3 discriminates.
3. Then run Proof D run 4 under PE-1.4, with full 64-hex stdout and stderr
   SHA-256 values and every `PE-EVIDENCE-01` field.

Other effects:

* `187-S` stays not claim-ready, and `publication_eligible: false`. There are
  no backlog, shipment or label effects.
* The budget decision stays decided and unimplemented. This run shows no
  defect in it.

## References

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (version 1.4:
  sections 3.3, 6.1, 6.6, 7.6 `PE-SAFETY-04`, 7.7 `PE-DATA-03`, 7.9
  `PE-EVIDENCE-01`, 7.10 `PE-ACTIVATE-01`, 8)
* `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
  (Decision 1, Byte budget, Decision 2)
* `docs/decisions/2026-09-23-read-budget-proof-d-spike.md` (run 1, `FAIL`;
  negative-control definitions)
* `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md` (run 2,
  historical `PASS`, kept unchanged)
* `.github/skills/spike/SKILL.md`, `.github/agents/_stage.agent.md`
