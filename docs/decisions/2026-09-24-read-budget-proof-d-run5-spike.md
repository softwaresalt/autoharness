---
title: "Proof D run 5 (PE-1.5) - budget equation and read-limit exhaustion: findings (PASS, synthetic contract only)"
source: "docs/decisions/2026-09-24-read-budget-proof-d-run5-spike.md"
doc_type: decision
description: "Stage-authored findings for the operator-authorized fresh Proof D run 5 under charter PE-1.5 (charter commit d31d7b42, 2026-09-24T17:29:37-07:00, committed before run 5). Section 6.6 and the section 6.1 gates are unchanged, and no threshold was changed. Ship ran one retained disposable scratch fixture once, with no retry. It exited 0 natively, with stdout 1,153 B (SHA-256 2ff1aeba...8ca99b) and empty stderr. Stage hashed the fixture read-only: 27,658 B, SHA-256 B54BBFDB...707782. This matches the handoff and is byte-for-byte identical to the run 4 fixture that Stage verified statically in 36f65975. So run 4's static part-by-part verification applies to run 5 unchanged. The fixture is deterministic apart from elapsed_ms. It can exit 0 with empty stderr only after every check passes. Parts 1 to 4 are met: 192 cases; C_max 202 with margin 54; N=17 gives 78; N=49/512/513 give MEMBERS_TOO_MANY with 4 claims and 0 lookups; the 416 MiB worst case means no byte fit is claimed; TOTAL_SIZE_LIMIT, FILE_SIZE_LIMIT and FILE_COUNT_LIMIT each give UNRESOLVED / 2; there are 108 stage-matrix, 27 precedence and 24 incomplete-recheck cases; and 9 of 9 mutants are caught through validate_model. The verdict is PASS for the synthetic decided contract only, not for a production resolver. Run 5 follows PE-FLOW-04's rule: a new charter version existed before the re-run. It does not undo run 4's literal, historical breach of that row. Closing the row needs an operator ruling on OD-2. Runs 1 and 3 stay FAIL, and runs 2 and 4 stay historical PASS. No history is rewritten."
docline:
  type: spike
  date: 2026-09-24
  time_box: "45m"
  conclusion: "proceed"
  confidence: "high"
  recommendation: "Record Proof D run 5 PASS (PE-1.5, synthetic decided contract only) as Proof D's standing for PE-DATA-03 and the Proof D half of PE-SAFETY-04. Keep runs 1-4 as recorded history. The operator should close OD-2 explicitly (option 2: run 4 kept as history, run 5 is the admissible run), and rule whether PE-FLOW-04 is read prospectively over the admissible evidence chain, with run 4 listed as a recorded historical exception."
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "read-budget"
    - "file-count-limit"
    - "reducer"
    - "negative-controls"
    - "proof-entry"
    - "ship-lifecycle"
    - "pe-flow-04"
proof: D
proof_run: 5
proof_verdict: PASS
proof_verdict_scope: synthetic-decided-contract-only-not-production-resolver
contract_counterexample_found: false
fixture_identical_to_run: 4
prior_run_artifacts:
  - {run: 1, path: docs/decisions/2026-09-23-read-budget-proof-d-spike.md, verdict: FAIL, matrix: PE-1.1}
  - {run: 2, path: docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md, verdict: PASS, matrix: PE-1.2, pe_1_4_admissible: false}
  - {run: 3, path: docs/decisions/2026-09-24-read-budget-proof-d-run3-spike.md, verdict: FAIL, matrix: PE-1.4}
  - {run: 4, path: docs/decisions/2026-09-24-read-budget-proof-d-run4-spike.md, verdict: PASS, matrix: PE-1.4, pe_flow_04_literal_breach: true}
prior_run_verdicts_changed: false
charter_threshold_changed: false
decision: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md
decision_reopened: false
decision_implemented: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.5"
charter_commit: d31d7b42286ccce005d7f46f444bc5ded9b94443
matrix_id: PE-1.5
matrix_rows: [PE-DATA-03, PE-SAFETY-04, PE-EVIDENCE-01, PE-AUTH-02, PE-FLOW-04, PE-ACTIVATE-01]
operator_authorization: "2026-09-24T18:21:44-07:00 'I authorize Proof C run 3 with the new verifier and a fresh Proof D run under PE-1.5'"
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 9c83517d
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

# Proof D run 5 findings (PE-1.5): budget equation and exhaustion

## Verdict

| Field | Value |
|---|---|
| Verdict | **`PASS`**, for the **synthetic decided contract only** |
| Scope limit | The fixture models `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`. It tests no production code. No production resolver exists, and none was exercised or is claimed. `187-S` is not made claim-ready |
| Parts (section 6.6) | Parts 1, 2, 3 and 4 are all met. The fixture is byte-identical to run 4's, so run 4's static verification applies. Ship's native exit 0 with empty stderr is this run's execution evidence |
| Fail criteria (section 6.6) | None present. No admitted case exceeds 256 or breaks the margin rule. No closed form disagrees with its simulation. No exhaustion case gives exit 0, exit 1 or the wrong reason. Every control is caught. No byte fit is claimed. The time and file bounds are met |
| Charter | PE-1.5 (`d31d7b42`). Sections 6.1 and 6.6 are unchanged from PE-1.4. No threshold change |
| `PE-FLOW-04` | Run 5 **follows** the rule: it is a re-run of run 3's failed question under a newer charter version. It **does not undo** run 4's literal, historical breach (see below). Closing the row is an operator ruling (OD-2), and Stage does not record the row as `MET` |
| Prior runs | Run 1 stays **`FAIL`** (PE-1.1). Run 2 stays a historical **`PASS`** (PE-1.2). Run 3 stays **`FAIL`** (PE-1.4). Run 4 stays **`PASS`** (PE-1.4) as recorded. No earlier artifact is edited or re-labelled |

## Goal

This run answers charter section 6.6, "Proof D - budget equation", under the
section 6.1 execution rules of PE-1.5. The operator explicitly authorized it
at 2026-09-24T18:21:44-07:00, taking the second option of proof-exit
decision OD-2 ("keep run 4 as history and order a fresh Proof D run under
PE-1.5 or later").

1. With admitted membership `1..48`, does the claim count fit `max_files=256`
   with the recorded margin for every admitted input?
2. Does every read-limit error at every read or recheck stage reduce to
   `UNRESOLVED / 2`, never `NO_HARNESS / 1` or `HARNESS_READY / 0`? This
   includes byte exhaustion, which is explicitly not guaranteed to fit.

Section 3.4 (PE-1.5) explicitly allows a Proof D run recorded under PE-1.5:
"a run recorded under PE-1.4, or one recorded later under PE-1.5, meets that
requirement".

## Success Criteria

* **Pass**: all four section 6.6 parts are met, the time and file bounds are
  met, and the `PE-EVIDENCE-01` fields are present.
* **Fail**: any section 6.6 fail criterion is present, or a bound is
  exceeded. The run 4 rule still applies: any vacuous control is `FAIL`.
* **Blocked**: a section 6.1 gate rejected execution, or missing evidence
  made a determination impossible.

## Scope Constraints and Learnings

* Stage worked read-only. It ran no fixture, test, build, linter or index
  sync, and made no backlog read or edit (operator scope; P-010; section 6.1).
  Stage's only commands were:
  * a SHA-256 of the run 5 fixture, plus the retained run 4 fixture for the
    identity check;
  * read-only `git` queries (`show --stat`, `log`, `rev-parse`, `status`,
    `ls-tree`, `diff --stat`, `worktree list`, `check-ignore`);
  * a single-directory listing of the run 5 scratch directory, and a
    timestamp filter on `.backlogit/` top-level files;
  * `python --version`, which does not execute the fixture.
* Stage read no external Temp or spool paths. This artifact is the only
  tracked change: no amend, push, PR, branch or claim. The P-016 exception was
  not used.
* **Compound learnings.** Stage did not repeat the `docs/compound/` search,
  because the fixture is unchanged. The learning run 4 applied still holds:
  `docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`
  (a check is vacuous when the defect and the fallback give the same answer).
  Run 4's part 4 analysis showed that the healthy model gets zero findings
  from the same validator that flags each mutant.
* **Tool states (`PE-EVIDENCE-05`).** Stage did not probe backlogit (the
  operator and section 6.1 forbid Stage backlog reads and refreshes). Ship
  reported that the MCP transport was absent and that the registered CLI
  fallback was used. Stage did not probe engram, intercom or graphtor-docs,
  because a static adjudication does not need them. This is declared
  degraded visibility, not a silent fallback. Stage pipeline steps 1 to 5.6
  (triage, grouping, harvest, shipment, stash archive) do not apply to a
  findings-only proof session.

## Inputs (decided, unchanged since PE-1.2)

```text
C(N,U,rho) = 4(N+1) + 3U(1+rho)     N in 1..48, U,rho in {0,1}  -> 192 cases
max_files=256, max_file_bytes=4 MiB, max_total_bytes=32 MiB
margin rule: C(N,U,1) + (N+1) <= 256
worst-case bytes: [2(N+1) + 3U(1+rho)] * max_file_bytes = 416 MiB at N=48,U=1,rho=1
class 1b: read-limit error at any stage -> UNRESOLVED / 2 / <code>
stages (9): shipment queue|archive candidate, member queue|archive candidate,
  manifest, template, installed, candidate recheck, surface recheck
```

## Evidence Provenance

### Timeline (ordering relevant to `PE-FLOW-04`)

| Event | Time (-07:00) | Source |
|---|---|---|
| Run 3 `FAIL` recorded (PE-1.4) | `8179feb1` | Git |
| Run 4 `PASS` recorded (PE-1.4) | 15:41:51 (`36f65975`) | Git |
| PE-1.5 charter committed | **17:29:37** (`d31d7b42`) | Git (Stage) |
| Proof-exit report with the `PE-FLOW-04` finding and OD-2 | 18:02:24 (`9c83517d`) | Git (Stage) |
| Operator authorizes a fresh Proof D run under PE-1.5 | 18:21:44 | Operator message |
| Ship index refresh writes the cache | 18:24:34 (`backlogit.db`), 18:24:35 (`-wal`) | Stage file timestamps |
| Run 5 scratch directory created | 18:28:58.49 | Stage file timestamps |
| Run 5 single execution | **18:29:08.410 to 18:29:10.698** (2.288 s) | Ship |

The new charter version and the operator authorization both came before the
run 5 execution.

### Fixture (Stage, independent and read-only)

| Item | Value |
|---|---|
| Scratch path | `.proof-scratch\D-run5-20260924-182847\`, Git-ignored by `.gitignore:10 .proof-scratch/` (Stage ran `git check-ignore -v`). Directory created 18:28:58-07:00 |
| Listing | Exactly one file, `proof_d_run5.py`, 27,658 bytes. It was created 18:28:58, and its last-write time is 15:32:34, carried over from the copied run 4 file. No `__pycache__` |
| SHA-256 (Stage-computed) | `B54BBFDB76E4F93DB2D6FCA17DBBBAD2005311082AEAA08D1157AE135D707782`. This matches the handoff |
| Identity with run 4 | The retained `.proof-scratch\D-run4-20260924-152723\proof_d_run4.py` hashes to the same value, which is also the value in the run 4 findings. The file is byte-for-byte identical |
| Imports | `dataclasses` (`dataclass`, `replace`), `itertools.product`, `sys` and `time.monotonic` only. No production code, and no filesystem, backlog, network or random input |
| Self-labels | The docstring and the stderr failure prefixes still say "run 4" (`PROOF_D_RUN4_FIXTURE_FAIL` / `_ERROR`). This is cosmetic, and nothing in the success path depends on it. stderr was empty |

### Ship verification-only invocation (as relayed, not re-run)

| Gate / fact | Result (Ship-reported unless marked Stage) |
|---|---|
| Index refresh | P-012: the registry's MCP transport was absent, so Ship used the registered **CLI fallback**. Native exit 0. stdout 23 B, SHA-256 `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873`. **stderr 0 B, empty**. This closes run 4's two refresh disclosures (unnamed transport, 489 B stderr) |
| Refresh footprint (Stage) | Since 18:20, the only top-level `.backlogit/` files written are `backlogit.db` (18:24:34) and `backlogit.db-wal` (18:24:35). These are cache paths the section 6.1 refresh bullet allows. Ship reported only ignored DB, WAL and SHM paths |
| Checkpoint scan | Unfiltered list: 71 summaries, 0 anomalies, 0 active |
| P-001 | These reads were made after the refresh: active tasks, features, chores and shipments are all 0. `173-S` is archived, with closure READY and compaction done (context only) |
| P-002 / P-011 / P-016 | No claim. Clean current branch `chore/stage-176-s-workflow-defects` at `9c83517d`. One worktree. **Stage confirmed**: `git worktree list --porcelain` lists only `C:/Source/GitHub/autoharness` on that branch at `9c83517d8542b702806a19820a54de6f0dd14bac` |
| P-010 self-check | Not itemized as a named self-check in the handoff. Ship's safety statement (no tracked edits, claim, backlog mutation, PR, push or commit) is consistent with it. See Disclosures |
| PE-ACTIVATE-01 | Ship: blobs match `4acba14a` before and after. **Stage confirmed at HEAD `9c83517d`**: `4ccd7fdc2d134de485487acd75bfbc105d6f40ee` (template), `e22916b62f36f1c25c421882a05f4049f1862c02` (mirror) and `251f46e8c95703ed65e421210d3b08682d79d8bc` (manifest). `git diff --stat 4acba14a HEAD` over the three paths is empty |
| Command (verbatim) | `python -B .proof-scratch/D-run5-20260924-182847/proof_d_run5.py`, cwd `C:\Source\GitHub\autoharness` |
| Host | Windows, NTFS. Ship gave Python 3.14.3 as "probable". **Stage corroboration** at 18:33 in the same cwd: `python` resolves to `C:\Python\Python314\python.exe`, `Python 3.14.3`; OS `Microsoft Windows NT 10.0.26200.0`; drive C: `NTFS` |
| Execution | Exactly one, no retry. Native exit 0. 18:29:08.410 to 18:29:10.698 (2.288 s) |
| stdout | 1,153 B, SHA-256 `2ff1aebaf03f7bf8a134ff7f404391f20571f4ae8a1f637d3ca032e05ca8c99b` |
| stderr | 0 B, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (the empty digest) |
| Safety statement | Ship: no tracked edits, claim, backlog mutation, PR, push or commit. **Stage after-state check**: `git status --porcelain` is empty at `9c83517d`, and the before state is the same clean commit. Ignored `.backlogit` changes in the window are only the cache files above |

### Why an identical fixture still gives independent execution evidence

* The fixture is deterministic apart from `elapsed_ms`. It has no random,
  clock-dependent or I/O-dependent branch. The only time use is the
  `MAX_RUNTIME_SECONDS = 45 * 60` guard, and 2.288 s is far inside it.
* Every failed check raises `ProofFailure` (exit 1, with a stderr line) or
  an unexpected exception (exit 2, with a stderr line). `main` has no early
  successful return (run 4 findings, Part 4 note 1). So a native **exit 0
  with 0 bytes of stderr** means every healthy-model assertion and every
  control assertion passed in this execution.
* stdout is again 1,153 bytes, and its SHA-256 differs from run 4's
  (`c4980048...32c2802`). This fits byte-identical text in which only a
  4-digit `elapsed_ms` changed (run 4 printed 1467; any value from 1000 to
  9999 keeps the length). Stage did **not** reconstruct and hash the run 5
  text, so this is consistency only, not corroboration.

## Findings by Part

The static analysis is run 4's
(`docs/decisions/2026-09-24-read-budget-proof-d-run4-spike.md`, "Findings by
Part"). It covers the same bytes, which Stage checked by hash above. It is
not repeated here. This run supplies execution under PE-1.5.

### Part 1 - File-slot guarantee: met

All 192 admitted cases are traced claim by claim and each equals the closed
form. `C_max = C(48,1,1) = 202`, capacity margin 54, and the margin rule
holds with slack 5. `C(17,1,1) = 78`. `N` in `{49, 512, 513}` gives
`MEMBERS_TOO_MANY -> UNRESOLVED / 2`, with 4 claims and 0 counted member
lookups. The run 4 limitation carries over: the early stop is by
construction.

### Part 2 - Byte distinction: met

The worst case, 416 MiB (104 present reads of 4 MiB at `N=48, U=1, rho=1`),
is derived from the trace and is over 32 MiB, so `fit=none`. No byte fit is
claimed. The `N=17` stream fails with `TOTAL_SIZE_LIMIT` at
`member_queue_candidate`, a 4 MiB + 1 file gives `FILE_SIZE_LIMIT` at
`installed_read`, and 257 reads give `FILE_COUNT_LIMIT` at
`member_archive_candidate`. Each reduces to `UNRESOLVED / 2` with its own
code, and none succeeds.

### Part 3 - Exhaustion at every stage: met

There are 108 injections (9 stages × 3 codes × 4 would-be outcomes). The
seven non-recheck stages give `UNRESOLVED / 2 / <code>`, and the two
recheck stages give the same with the recheck state `INCOMPLETE`. The 27
completed-disagreement cases give `INPUT_CHANGED_DURING_RESOLUTION`. The 24
incomplete-recheck cases stay `INCOMPLETE` with `UNRESOLVED / 2`. The matrix
discriminates: mutants PE-2, PE-3 and PE-4 are rejected by it. The run 4
limitations carry over unchanged:
* the precedence cases are short-circuited, with exit `None`;
* byte-code applicability at absent candidates is not modelled separately;
* first-code selection is never tested with competing errors.

### Part 4 - Negative controls: met

There are 9 of 9 behaviour-changing mutants: R1-1 to R1-4 (the run 1
counts 42, 39, 129 and 79/77) and PE-1 to PE-5. Each runs through the same
`validate_model()` that gives zero findings for the healthy model. Each is
rejected at a real counterexample, and its full coverage vector is asserted
(the run 4 table). No vacuous control remains.

## `PE-FLOW-04`: prospective resolution versus the historical breach

The row reads: "A `FAIL`ed proof is re-run only under a new charter
version". Its pass criterion is "No second attempt of a failed proof question
exists without a charter version bump".

1. **Historical breach (unchanged, not rewritten).** Run 3 `FAIL`ed under
   PE-1.4 (`8179feb1`). Run 4 (`36f65975`, 15:41:51) asked the same section
   6.6 question under the same version, PE-1.4. The next version, PE-1.5,
   was committed later (17:29:37). Run 4 therefore **exists** as a second
   attempt without a version bump. The pass criterion is a claim about what
   exists in the record, so it stays **literally unmet** by run 4, and no
   later run can change that. Stage does not re-label, edit or withdraw
   run 4. Its `PASS` (PE-1.4) stands as recorded.
2. **Run 5 is compliant.** PE-1.5 is a new charter version, and it was
   committed before run 5 and before the operator's authorization. Run 5 is
   therefore an attempt made "under a new charter version". Section 3.4
   (PE-1.5) explicitly lets a later PE-1.5 Proof D run meet the required-run
   requirement.
3. **What run 5 changes going forward.** Proof D's standing for
   `PE-DATA-03` and the Proof D half of `PE-SAFETY-04` can now rest on
   run 5 alone, so it no longer depends on run 4's admissibility. That is
   OD-2's second option ("keep run 4 as history and order a fresh Proof D
   run under PE-1.5 or later"). The operator's 18:21:44 authorization chose
   that option in substance.
4. **What run 5 does not settle.**
   * **Row status is an operator ruling.** The criterion is phrased over
     everything that exists, so it cannot be met after the fact while run 4
     exists. Whether `PE-FLOW-04` is read prospectively (the admissible
     evidence chain contains no non-compliant re-run, and run 4 is listed as
     a recorded historical exception) needs an operator ruling. It could be
     recorded in a proof-exit addendum or a later charter version. Stage
     does **not** record the row as `MET`.
   * **The bump did not touch section 6.6.** PE-1.5 is limited to section
     6.7. Run 3's `FAIL` route ("charter change control", to make "caught"
     concrete) is still not enacted. Runs 4 and 5 were both adjudicated
     under run 3's stricter reading. Run 5 meets the row's literal rule (a
     new version) but not a stronger reading (a version that addresses the
     failed question). This is disclosed for the `PE-FLOW-01` / OD-2
     ruling. It is not a Proof D fail criterion.
   * **OD-2 is not formally closed.** The authorization orders the run. It
     does not explicitly say "run 4 is history-only" or record a ruling on
     the row.

**Stage row finding:** `PE-FLOW-04` is `UNSATISFIED-AS-WRITTEN
(historical: run 4)`. Remediation is complete going forward through run 5,
**pending the operator's OD-2 closure**.

## Disclosures

* **Interpreter.** Ship relayed Python 3.14.3 as "probable". Stage checked
  that `python` in this cwd resolves to 3.14.3 at 18:33. That confirms the
  environment, but it is not Ship's record of the invoking interpreter. The
  fixture uses only features from Python 3.10 or later. Ship should add the
  interpreter version it actually captured to its record.
* **P-010 self-check.** The handoff does not name Ship's P-010 self-check
  result as a separate item. This is the same class of gap the proof-exit
  report counts under `PE-AUTH-02` for F run 2. It does not change the
  section 6.6 verdict, because no gate rejected execution and the safety
  statement is clean.
* **stdout text.** Only the length and SHA-256 were relayed. Stage did not
  reconstruct the text (see above).
* **Run 4 scratch.** `.proof-scratch\D-run4-20260924-152723\` is still
  retained. Cleanup belongs to Ship or the parent under section 6.1. It is
  not counted against run 5's file bound.
* **Scope.** `PASS` covers the synthetic decided contract only. It proves
  nothing about a production resolver, and it does not make `187-S`
  claim-ready.

## Matrix Row Status (Proof D only; not a proof-exit audit)

| Row | Status |
|---|---|
| `PE-DATA-03` | **Proof D evidence satisfied by run 5 (PE-1.5)** for the synthetic contract. It no longer depends on run 4's admissibility |
| `PE-SAFETY-04` | **Proof D half satisfied by run 5.** The Proof G half is unchanged (Windows met, Linux `PENDING`) |
| `PE-EVIDENCE-01` | **Met for this run**, with one residual: the interpreter version is Ship-"probable" and Stage-corroborated. The refresh transport and stderr are now recorded |
| `PE-AUTH-02` | Worktree, refresh (transport, native result, bounded output), P-001, P-002, P-011 and P-016 are recorded. **Open for this run: the P-010 self-check is not itemized** |
| `PE-FLOW-04` | `UNSATISFIED-AS-WRITTEN (historical: run 4)`. Run 5 is compliant, and remediation is complete going forward. Closing the row needs the operator's OD-2 ruling |
| `PE-ACTIVATE-01` | Met at HEAD `9c83517d` for this run (Stage read-only confirmation). The proof-exit comparison stays with the proof-exit audit |

No reason code is used or created beyond `MEMBERS_TOO_MANY`,
`FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT` and
`INPUT_CHANGED_DURING_RESOLUTION`.

## Time and File Bounds

| Item | Value |
|---|---|
| Conservative start | 2026-09-24T18:21:44-07:00 (operator authorization, before Ship's 18:24:34 refresh) |
| Ship fixture window | 18:29:08.410 to 18:29:10.698 (2.288 s) |
| Stage start | Operator directive, about 18:31:22-07:00 |
| Authoring | 18:36:06-07:00 (host clock), before the commit |
| Combined elapsed | About 15 min to authoring (Stage plus Ship), within the 45m bound. **Met** |
| File bound | One disposable file. **Met** |

## Consequences and Recommendation

**Conclusion: proceed (confidence: high), limited to Proof D's
synthetic-contract question.**

* Proof D's admissible standing under PE-1.5 is run 5 `PASS`. It counts
  toward proof exit only together with every other proof and the section 8
  audit.
* **Operator actions (open):**
  1. Close OD-2 explicitly: run 4 stays as history, and run 5 is the
     admissible Proof D run.
  2. Rule on whether `PE-FLOW-04` is evaluated prospectively over the
     admissible chain, with run 4 as a recorded historical exception.
  3. Optionally, route run 3's unenacted "caught" clarification through
     charter change control (`PE-FLOW-01`).
* **Ship evidence follow-ups (non-blocking for this verdict):** the captured
  interpreter version, and the itemized P-010 self-check result.
* `187-S` stays queued and not claim-ready, and `publication_eligible:
  false`. There are no backlog, shipment, label or plan effects.
* The run 4 limitations carry forward unchanged into the later
  implementation acceptance matrix.

## References

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (version 1.5,
  `d31d7b42`: sections 3.4, 6.1, 6.2, 6.6, 7.4 `PE-FLOW-04`, 7.6
  `PE-SAFETY-04`, 7.7 `PE-DATA-03`, 7.9 `PE-EVIDENCE-01`, 7.10
  `PE-ACTIVATE-01`, 8, 10)
* `docs/decisions/2026-09-24-lifecycle-proof-exit-spike.md` (`9c83517d`:
  `PE-FLOW-04` finding, OD-2)
* `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
* `docs/decisions/2026-09-24-read-budget-proof-d-run4-spike.md` (run 4, static verification of the identical fixture)
* `docs/decisions/2026-09-24-read-budget-proof-d-run3-spike.md` (run 3, FAIL)
* `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md` (run 2)
* `docs/decisions/2026-09-23-read-budget-proof-d-spike.md` (run 1)
* `docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`
