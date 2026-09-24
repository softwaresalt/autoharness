---
title: "Proof D run 4 (PE-1.4) - budget equation and read-limit exhaustion: findings (PASS, synthetic contract only)"
source: "docs/decisions/2026-09-24-read-budget-proof-d-run4-spike.md"
doc_type: decision
description: "Stage-authored findings for Proof D run 4 under charter PE-1.4. Section 6.6 parts 1-4 and the section 6.1 gates are unchanged, and no charter threshold was changed. Ship ran one disposable synthetic scratch fixture once. It exited 0 natively, with stdout 1,153 B (SHA-256 c4980048...32c2802) and empty stderr. Stage hashed the retained fixture read-only (27,658 B, SHA-256 B54BBFDB...707782, which matches the handoff). Stage then checked every validator and mutant statically. Parts 1 and 2 are met from a claim-by-claim trace: 192 cases, C_max 202, margin 54, N=17 gives 78, and N=49/512/513 give MEMBERS_TOO_MANY with 4 claims and 0 lookups. The worst case of 416 MiB is derived from the trace and no byte fit is claimed. The N=17 total reservation, the oversize file and the file count each yield UNRESOLVED / 2 with their own code. Part 3 is met: 108 injections, 27 precedence cases and 24 incomplete-recheck cases. Part 4 is met. Each of the nine controls is a behaviour-changing mutant of the model functions. Each goes through the same validate_model() that returns zero findings for the healthy model, and each is rejected at a real counterexample. No constant, short-circuit or impossible string comparison remains. Stage's static derivation of all nine first counterexamples reproduces Ship's stdout SHA-256 byte for byte (elapsed_ms=1467, CRLF). This is corroboration, not evidence. The verdict is PASS for the synthetic decided contract only, not for a production resolver. Run 1 stays FAIL, run 2 stays historical PASS and run 3 stays FAIL."
docline:
  type: spike
  date: 2026-09-24
  time_box: "45m"
  conclusion: "proceed"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "read-budget"
    - "file-count-limit"
    - "reducer"
    - "negative-controls"
    - "mutation-testing"
    - "proof-entry"
    - "ship-lifecycle"
proof: D
proof_run: 4
proof_verdict: PASS
proof_verdict_scope: synthetic-decided-contract-only-not-production-resolver
contract_counterexample_found: false
prior_run_artifacts:
  - {run: 1, path: docs/decisions/2026-09-23-read-budget-proof-d-spike.md, verdict: FAIL, matrix: PE-1.1}
  - {run: 2, path: docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md, verdict: PASS, matrix: PE-1.2, pe_1_4_admissible: false}
  - {run: 3, path: docs/decisions/2026-09-24-read-budget-proof-d-run3-spike.md, verdict: FAIL, matrix: PE-1.4}
prior_run_verdicts_changed: false
charter_threshold_changed: false
decision: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md
decision_reopened: false
decision_implemented: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.4"
matrix_id: PE-1.4
matrix_rows: [PE-DATA-03, PE-SAFETY-04, PE-EVIDENCE-01, PE-ACTIVATE-01]
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 8179feb1
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
publication_eligible: false
actor_invoked: false
backlog_item_created: false
plan_changed: false
time_bound_status: met
file_bound_status: met
scratch_cleanup_status: "retained at authoring; Stage deleted nothing"
stage_model_route: "claude-opus-5.5/anthropic/high requested; unverified by Stage (DEGRADED: route not self-verifiable)"
---

# Proof D run 4 findings (PE-1.4): budget equation and exhaustion

## Verdict

| Field | Value |
|---|---|
| Verdict | **`PASS`**, for the **synthetic decided contract only** |
| Scope limit | The fixture models `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`. It tests no production code. No production resolver exists, and none was exercised or is claimed |
| Parts | Part 1: met. Part 2: met. Part 3: met, and it discriminates. **Part 4: met.** All nine controls are behaviour-changing model mutants, and the shared validator rejects each one |
| Fail criteria (section 6.6) | None present. No admitted case exceeds 256 or breaks the margin rule. No closed form disagrees with its simulation. No exhaustion case yields exit 0, exit 1 or the wrong reason. Every control is caught. No byte fit is claimed. The time and file bounds are met |
| Charter | PE-1.4 is unchanged. No threshold change. Run 3's recommended clarification of "caught" was not enacted. Stage applied run 3's stricter reading anyway: each control must mutate the model and be rejected by the validators that accept the healthy model. Run 4 meets that reading |
| Prior runs | Run 1 stays **`FAIL`** (PE-1.1). Run 2 stays a historical **`PASS`** (PE-1.2) and is still not admissible for PE-1.4. Run 3 stays **`FAIL`** (PE-1.4) as a historical record. No earlier artifact is edited |
| Decision | Decisions 1 and 2 stay decided, not reopened and not implemented |

## Goal

This run answers charter section 6.6 (unchanged since PE-1.2) under the
PE-1.4 section 6.1 execution rules. It is the new admissible PE-1.4 Proof D
run that section 3.3 requires, and it follows run 3's `FAIL`.

1. With admitted membership `1..48`, does the claim count fit `max_files=256`
   with the recorded margin for every admitted input?
2. Does every read-limit error at every read or recheck stage reduce to
   `UNRESOLVED / 2`, never `NO_HARNESS / 1` or `HARNESS_READY / 0`? This
   includes byte exhaustion, which is explicitly not guaranteed to fit.

## Success Criteria

* **Pass**: all four section 6.6 parts are met, the time and file bounds are
  met, and the `PE-EVIDENCE-01` fields are present.
* **Fail**: any section 6.6 fail criterion is present, or a bound is exceeded.
  The operator added an explicit rule: any remaining vacuous control is `FAIL`.
* **Blocked**: a section 6.1 gate rejected execution, or missing evidence made
  a determination impossible.

## Scope Constraints and Learnings

* Stage worked read-only. It ran no fixture, test, build, linter or index
  sync, and made no backlog read or edit (operator scope; P-010; section 6.1).
  Stage's only computations were:
  * a SHA-256 of the retained fixture file;
  * read-only `git` queries (`status`, `rev-parse`, `ls-tree`, `diff --stat`,
    `worktree list`, `log`);
  * file timestamp listings;
  * string hashing, without importing or executing the fixture, for the
    corroboration below.
* This artifact is the only tracked change: no amend, push, PR, branch or
  claim. The P-016 exception was not used.
* **Compound learnings.** Stage searched `docs/compound/` first.
  `docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`
  applies: a regression check is vacuous when the defect under test and the
  fallback give the same answer. Stage applied it as the admissibility test
  for part 4. For every control, the healthy model must produce **zero**
  findings from the same validator that must produce at least one finding for
  the mutant, so the two cannot agree. No entry on read budgets or Proof D
  exists.
* **Tool states (`PE-EVIDENCE-05`).** Stage did not probe backlogit (the
  operator and section 6.1 forbid Stage backlog reads and refreshes). Ship
  reported backlogit working. Stage did not probe engram, intercom or
  graphtor-docs, because a static adjudication does not need them. This is
  declared degraded visibility, not a silent fallback. Stage pipeline steps 1
  to 5.6 (triage, grouping, harvest, shipment, stash archive) do not apply
  to a findings-only proof session.

## Inputs (decided, unchanged)

```text
C(N,U,rho) = 4(N+1) + 3U(1+rho)     N in 1..48, U,rho in {0,1}  -> 192 cases
max_files=256, max_file_bytes=4 MiB, max_total_bytes=32 MiB
margin rule: C(N,U,1) + (N+1) <= 256
P_max = 2(N+1) + 3U(1+rho) non-refunded present-file reservations
class 1b: read-limit error at any stage -> UNRESOLVED / 2 / <first ReadErrorCode>
stages: shipment queue|archive candidate, member queue|archive candidate,
  manifest, template, installed, candidate recheck, surface recheck (9)
run 1 controls at N=17,U=1,rho=1: 42, 39, 129, 79/77 (reference 78)
```

## Evidence Provenance

### Fixture (Stage, independent and read-only)

| Item | Value |
|---|---|
| Scratch path | `.proof-scratch\D-run4-20260924-152723\`, Git-ignored by `.gitignore:10 .proof-scratch/` (Stage ran `git check-ignore -v`). Directory created 2026-09-24T15:29:05-07:00 |
| Listing | Exactly one file, `proof_d_run4.py`, 27,658 bytes, last written 2026-09-24T15:32:34-07:00. No `__pycache__` |
| SHA-256 (Stage-computed) | `B54BBFDB76E4F93DB2D6FCA17DBBBAD2005311082AEAA08D1157AE135D707782`, which matches the handoff value |
| Imports | `dataclasses`, `itertools.product`, `sys` and `time.monotonic` only. No production code, and no filesystem, backlog or network I/O |

### Ship verification-only invocation (as relayed, not re-run)

| Gate / fact | Result (Ship-reported unless marked Stage) |
|---|---|
| Index refresh | Ran in the same invocation, before the P-001 reads. Native exit 0. stdout 23 B, SHA-256 `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873`. **stderr 489 B, not empty**, SHA-256 `97cfe9ce9ed5246f8f678e017753011191b192098e6d658d0bada0fbdeb27eaf`. The handoff did not name the transport or include the stderr text (see Disclosures) |
| Refresh footprint (Stage) | Since 15:15, the only files written under `.backlogit/` are `backlogit.db` and `backlogit.db-wal`, both at 15:21:10. These are the tool-managed cache paths the section 6.1 refresh bullet allows |
| Checkpoint scan | Unfiltered list: 71 summaries (70 resolved, 1 abandoned), 0 quarantined, 0 anomalies, 0 active. The abandoned record's official get returned `valid: true` |
| P-001 | Active shipments: 0. Active queue: `total_count` 0. `173-S` closure is READY with compaction done (context only) |
| P-002 / P-010 / P-011 / P-016 | No claim. Self-check clean. Clean current branch at `8179feb1`. One worktree. **Stage confirmed**: `git worktree list --porcelain` shows only `C:/Source/GitHub/autoharness` on `chore/stage-176-s-workflow-defects` at `8179feb1` |
| PE-ACTIVATE-01 | Ship: blobs unchanged from `4acba14a`. **Stage confirmed at HEAD `8179feb1`**: `4ccd7fdc2d134de485487acd75bfbc105d6f40ee` (template), `e22916b62f36f1c25c421882a05f4049f1862c02` (mirror) and `251f46e8c95703ed65e421210d3b08682d79d8bc` (manifest). `git diff --stat 4acba14a HEAD` over the three paths is empty. `git status --porcelain` is empty |
| Command (verbatim) | `python -B .proof-scratch/D-run4-20260924-152723/proof_d_run4.py`, cwd `C:\Source\GitHub\autoharness` |
| Host | Windows 11, NTFS, Python 3.14.3 |
| Execution | Exactly one, native exit 0. Window 15:33:42.034 to 15:33:43.619 PDT (1.585 s) |
| stdout | 1,153 B, SHA-256 `c49800489c0e37b49953b60fb1b6f5992f0a4b23382e22c668284050032c2802` |
| stderr | 0 B, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (the empty digest) |
| Safety statement | Ship: Git-ignore validated before the write, one script, no pycache, no tracked writes, no writes outside cwd, no PR, push, branch, claim or backlog mutation. **Stage after-state check**: `git status --porcelain` is empty. The before state is Stage's own commit `8179feb1` (15:18:35, one file, clean). `git status --porcelain --ignored -- .backlogit` shows only long-standing ignored cache, lock, log and runtime paths, and the only ones modified in the window are the two cache files above |

### Stage corroboration of stdout (not evidence)

Stage derived the text of all 11 output lines statically from the source,
including each mutant's first counterexample. It then hashed candidate
strings, without executing or importing the fixture, over `elapsed_ms` in
`0..99999` and both line endings. Exactly one candidate matches Ship's
stdout: CRLF line endings, `elapsed_ms=1467`, 1,153 bytes, SHA-256
`c49800489c0e37b49953b60fb1b6f5992f0a4b23382e22c668284050032c2802`.
The value 1,467 ms fits inside Ship's 1.585 s window. This shows that
Stage's hand trace of every first counterexample (see the table in Part 4)
matches, byte for byte, what the fixture printed. It is a Stage
reconstruction, not Ship's record.

## Findings by Part

### Part 1 - File-slot guarantee: met

* `claim_plan` builds an ordered `Read` trace. For each of the `N+1` records
  it adds a queue candidate, an archive stable-absence claim, a queue ledger
  recheck and an archive ledger recheck. It then adds `3U` surface initial
  reads and `3U·rho` surface rechecks.
* `validate_model` checks `len(trace) == closed_form` for every case in
  `product(range(1, admitted_max+1), (0,1), (0,1))`. `main` requires the
  healthy model's coverage to be exactly 192 admitted cases.
* It also checks `observed > 256`, `member_lookups == N` and, when `rho=1`,
  `observed + (N+1) <= 256`. `main` asserts `C_max = 202`, capacity margin
  `256 - 202 = 54`, margin-rule slack 5 (`202 + 49 = 251`) and `N=17 -> 78`.
* For over-limit `N` in `{49, 512, 513}`, `membership_result` returns
  `UNRESOLVED / 2 / MEMBERS_TOO_MANY`. The trace holds only the shipment
  record's 4 claims, and the counted member lookups are 0. `main` compares all
  three tuples to hard-coded values.
* Limitation: the no-lookup result is now counted from the trace rather than
  assumed, but the early stop is still by construction.

### Part 2 - Byte distinction: met, derived from the trace

* The worst-case demand is the sum of the present-read sizes in the `N=48,
  U=1, rho=1` trace: 104 reads, 416 MiB. It is asserted equal to
  `[2(N+1)+3U(1+rho)] * 4 MiB`. The fixture records that it exceeds 32 MiB,
  prints `fit=none` and claims no byte fit.
* `reserve_reads` reserves each present read in order, with no refund. For
  each read it checks the count, then the per-file cap, then the running
  total.
  * The `N=17` present-read stream is 42 reads of 4 MiB each. The 9th
    reservation fails with `TOTAL_SIZE_LIMIT` at the stage where it actually
    occurs, `member_queue_candidate` (`main` asserts this). The result reduces
    to `UNRESOLVED / 2 / TOTAL_SIZE_LIMIT`.
  * One installed file of 4 MiB + 1 byte gives `FILE_SIZE_LIMIT`, which
    reduces to `UNRESOLVED / 2 / FILE_SIZE_LIMIT`.
  * 257 one-byte reads give `FILE_COUNT_LIMIT` at `member_archive_candidate`,
    which reduces to `UNRESOLVED / 2 / FILE_COUNT_LIMIT`.
* Run 3 flagged that its byte stream was sized separately from the claim
  trace and that its stage was a fixed label. Both limitations are fixed.

### Part 3 - Exhaustion at every stage: met, and it discriminates

* `STAGES` holds all nine charter stages. The matrix covers 9 stages × 3
  codes × 4 would-be outcomes (`NO_SURFACES_REQUIRED`,
  `ALL_SURFACES_PRESENT`, `MISSING`, `STALE`), which is 108 cases.
  * At the seven non-recheck stages, each case must equal
    `UNRESOLVED / 2 / <code> / READ_LIMIT_ERROR`.
  * At the two recheck stages, the recheck is marked incomplete, and each case
    must equal `UNRESOLVED / 2 / <code> / INCOMPLETE`.
* 27 precedence cases (9 stages × 3 codes) with a completed disagreement must
  yield `INPUT_CHANGED_DURING_RESOLUTION / COMPLETED_DISAGREEMENT`.
* 24 incomplete-recheck cases (2 stages × 3 codes × 4 outcomes) must have
  `recheck_state == INCOMPLETE` and `UNRESOLVED / 2 / <code>`.
* **Discrimination.** The reducer now has access to the stage, the
  would-be outcome and the dominated outcome table `WOULD_BE_RESULTS`. The
  mutants PE-2, PE-3 and PE-4 each let one stage × would-be combination
  bypass class 1b. The matrix then rejects each of them with a concrete
  case. Run 3's constant reducer could not fail. This one can.
* Limitations (not fail causes, and the same as run 3's):
  * The 27 precedence cases come from a first-branch short-circuit, and no
    mutant targets precedence, so they do not discriminate. The precedence
    result still carries exit `None`. Part 3 requires only the reason.
  * Byte codes are injected at archive-candidate stages that the count trace
    models as absent. The absent-candidate restriction ("byte codes apply only
    where a present file is read") is not modelled separately. Every stage can
    read a present file in some admitted scenario (for example, an archived
    member).
  * "First `ReadErrorCode`" is only tested through the order of reservation
    checks, and never with competing errors reaching the reducer.

### Part 4 - Negative controls: met (independent static verification)

**What makes each control non-vacuous.**

1. `validate_model(model)` is one function. It has no early return and never
   reads `model.name` or any mutation flag. Its only model-dependent input is
   `admitted_max` (see note 3). All of its expected values are hard-coded
   constants or `closed_form`.
2. The healthy model `Model("healthy")` passes through `validate_model`, and
   `main` raises unless its findings list is empty.
3. Each mutant is `validate_model(replace(Model("mutant"), <one flag>))`. The
   only difference from the healthy model is one flag. Each flag is read
   **only** inside a model function (`claim_plan`, `read_observation`,
   `recheck_state`, `reduce_read_limit` or `reserve_reads`), and there it
   changes the trace or the reduction, not a constant or a label. So every
   finding for a mutant is caused by changed behaviour, and the same validator
   that accepts the healthy model detects it.
4. `require_target` demands a finding under a specific validator key. Each
   control then checks that the recorded counterexample is the expected
   behaviour (the run 1 counts at `N=17`, `N=62 -> 258`, `MISSING / 1`,
   `STABLE_ABSENCE` with exit 1, `AGREEMENT`, or a null reservation error).
   `main` also asserts every listed mutant's full coverage vector: admitted
   `= 4 × admitted_max`, overlimit 3, bytes 4, exhaustion 108, precedence 27
   and incomplete 24. A mutant cannot be scored as caught without having run
   the shared validators.
5. No control is a literal comparison, an arithmetic short-circuit or a
   string comparison that cannot fail. This fixes every run 3 finding.

| # | Control (flag) | Behaviour change | First counterexample from `validate_model` (Stage-derived; matches the stdout hash) | Target check |
|---|---|---|---|---|
| R1-1 | `charge_stable_absence=False` | Archive stable-absence claim and its recheck are dropped | `claim_trace` N1U0r0: 4 vs 8 | `N17 = 42` (run 1: 42) |
| R1-2 | `ledger_rechecks=False` | Queue, archive and surface ledger rechecks are dropped | `claim_trace` N1U0r0: 4 vs 8 | `N17 = 39` (run 1: 39) |
| R1-3 | `surfaces_per_member=True` | Three surface reads per member (`+3NU`) | `claim_trace` N1U1r0: 14 vs 11 | `N17 = 129` (run 1: 129) |
| R1-4 | `claim_adjustment=±1` | One real claim appended or popped | `claim_trace` N1U0r0: 9 vs 8 (+1); 7 vs 8 (−1) | `N17 = 79 / 77` (run 1: 79/77) |
| PE-1 | `admitted_max=512` | Admission domain widened, so the trace runs to N=512 | `margin_rule` N50U1r1: 261 > 256 | `admitted_file_budget` at `N=62, U=1, rho=1` = 258 > 256 (`4·63+6`) |
| PE-2 | `installed_exhaustion_is_missing=True` | Installed-read exhaustion with would-be `ALL_SURFACES_PRESENT` reduces to `MISSING` | `oversize_file` at installed/ALL: `MISSING / 1` (expected `UNRESOLVED / 2`) | Matrix case installed/ALL observed `MISSING / 1 / MISSING` |
| PE-3 | `member_exhaustion_is_absence=True` | Member-candidate exhaustion recorded as `STABLE_ABSENCE`, then the would-be result | `n17_total_reservation` at member queue: `HARNESS_READY / 0` | Matrix case member queue/NO_SURF observed exit 1 with `STABLE_ABSENCE` |
| PE-4 | `incomplete_recheck_is_agreement=True` | An incomplete recheck is treated as `AGREEMENT`, then the would-be result | `read_limit_matrix` candidate recheck/NO_SURF: `NO_HARNESS / 1` | Observed `AGREEMENT`, plus the 24-case incomplete-recheck check |
| PE-5 | `enforce_total_size_limit=False` | The total-reservation limit is not enforced | `n17_total_reservation`: error `None` gives `HARNESS_READY / 0` | Reservation error is `None` over the 42-read, 168 MiB stream |

Notes:

* The run 1 counts are reproduced by mutating the model, as run 1 defined
  them. R1-2 now drops the ledger rechecks (39), not run 3's formula
  substitute.
* PE-1: the validator's over-limit branch uses the mutant's own
  `admitted_max`. By itself, it would therefore not flag `N=49` or `N=512`
  for this mutant. The mutant is caught by the independent file-budget and
  margin checks at real counterexamples, which charter part 4 requires ("must
  produce an over-budget case"). For the healthy model, the over-limit
  results are compared to hard-coded tuples in `main`.
* R1-4: the −1 mutant runs the shared validator and passes its target checks.
  Only the +1 entry is in the coverage-vector loop. `validate_model` has no
  early exit, so the −1 mutant's coverage is still complete by structure.
  This is a minor reporting asymmetry, not a vacuity.
* `byte_non_guarantee` compares constants. It records the 416 MiB > 32 MiB
  fact and is not a control. The 416 MiB value itself is taken from the
  trace and asserted in `main`.

**Conclusion.** Nine of nine controls are caught by the same validator that
accepts the healthy model, and each at a real counterexample. No vacuous
control remains. Part 4 is met.

## Disclosures

* **Refresh stderr (489 B).** The refresh wrote 489 bytes to stderr. The
  handoff gives its length and full SHA-256 but not its text, so Stage cannot
  say what it contains. Stage does not claim the refresh stderr was empty.
  The charter's fail-closed triggers did not fire: exit was a native 0; Stage
  found only the allowed cache paths written; and the post-refresh reads
  succeeded. On that basis Stage treats the refresh record as meeting
  `PE-EVIDENCE-01`, which accepts raw output or its SHA-256. Ship should keep
  its bounded excerpt (at most 2 KiB) with its record.
* **Refresh transport.** The handoff did not name the transport. A native exit
  code with byte-counted stdout and stderr points to the CLI fallback
  `backlogit sync`, but Stage does not assert that. Run 3 had the same gap.
* **Charter clarification not enacted.** Run 3 routed to charter change
  control to make "caught" concrete. The operator kept the PE-1.4 thresholds
  unchanged. This PASS rests on the unchanged section 6.6 text, adjudicated
  under run 3's stricter reading.
* **Scope.** `PASS` covers the synthetic decided contract only. It proves
  nothing about a production resolver, which does not exist, and it does not
  make `187-S` claim-ready.

## Matrix Row Status (Proof D only; not a proof-exit audit)

| Row | Status |
|---|---|
| `PE-DATA-03` | **Proof D evidence satisfied by run 4 (PE-1.4)** for the synthetic contract |
| `PE-SAFETY-04` | **Proof D half satisfied by run 4.** The Proof G half is unchanged (including its Linux gate) |
| `PE-EVIDENCE-01` | **Met for this run.** It records the question, host OS and version, filesystem, interpreter, exact command, full stdout and stderr SHA-256, fixture listing with SHA-256, per-criterion verdict, elapsed time, file count, scratch path, gate results including the refresh record, and the safety statement. The refresh stderr text and transport are disclosed above |
| `PE-ACTIVATE-01` | Met at HEAD `8179feb1` for this run (Stage read-only confirmation). The proof-exit comparison is still the proof-exit audit's job |

No reason code is used or created beyond `MEMBERS_TOO_MANY`,
`FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT` and
`INPUT_CHANGED_DURING_RESOLUTION`. The would-be outcomes are inputs only.

## Time and File Bounds

| Item | Value |
|---|---|
| Conservative start | 2026-09-24T15:20-07:00 (Ship wall-clock start as relayed; earlier than the scratch directory's 15:27:23 name and 15:29:05 creation) |
| Ship fixture window | 15:33:42.034 to 15:33:43.619 (1.585 s) |
| Stage start | Operator directive at 2026-09-24T15:36:04-07:00 |
| Authoring | 2026-09-24T15:41:41-07:00 (host clock), before the commit |
| Combined elapsed | About 22 min to authoring (Stage plus Ship), within the 45m bound. **Met** |
| File bound | One disposable file. **Met** |

## Scratch Hygiene

The scratch directory still existed at authoring. Stage read and hashed it
only, and deleted nothing. Under section 6.1, cleanup is Ship's or the
parent's job, after the path is verified.

## Consequences and Recommendation

**Conclusion: proceed (confidence: high), limited to Proof D's
synthetic-contract question.**

* Proof D now has an admissible PE-1.4 `PASS`. It counts toward proof exit
  only together with every other proof and the section 8 audit.
* `187-S` stays not claim-ready, and `publication_eligible: false`. There are
  no backlog, shipment, label or plan effects.
* The limitations carried forward are: precedence is short-circuited with
  exit `None`; byte-code applicability at absent candidates is not modelled;
  and first-code selection is never tested with multiple errors. These are
  inputs for the later implementation acceptance matrix, not reasons to
  re-run Proof D.

## References

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (version 1.4:
  sections 3.3, 6.1, 6.6, 7.6 `PE-SAFETY-04`, 7.7 `PE-DATA-03`, 7.9
  `PE-EVIDENCE-01`, 7.10 `PE-ACTIVATE-01`, 8)
* `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
* `docs/decisions/2026-09-23-read-budget-proof-d-spike.md` (run 1, control table)
* `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md` (run 2)
* `docs/decisions/2026-09-24-read-budget-proof-d-run3-spike.md` (run 3, FAIL)
* `docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`
