---
title: "Proof C run 2 - one-entry SurfaceSpec and total reason truth table: findings (BLOCKED, PE-1.4)"
source: "docs/decisions/2026-09-24-surface-taxonomy-proof-c-run2-spike.md"
doc_type: decision
description: "Stage-authored formal adjudication of Proof C run 2 under charter PE-1.4 section 6.5 (charter commit 52c985cb). The run 1 FAIL artifact (docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md, 9d0ed834) is unchanged. At HEAD 06f8930b, Ship ran the disposable two-file fixture in .proof-scratch/C-20260924-143026/ six times with the same command. The native exits were [1,1,1,1,1,0]. Stage checked both fixture hashes, read both files and compared them with the charter without running anything. It found that the fixture's candidate order and the schema enum each equal the charter's 47-code Stage candidate exactly, in order. The governing constant is a separate literal that matches the charter's 8-code governing table. READ_BUDGET_EXHAUSTED appears only in negative checks. The schema partitions the 47 codes into 6 top-level branches (40 oneOf branches in 6 groups). Stage's arithmetic reproduces the reported counts: 2522 inputs, 2162 precedence orderings, 294 two-error read-limit orderings and 21 single injections. Stage found no section 6.5 fail condition in the source, so the verdict is not FAIL. The verdict is BLOCKED, not PASS, on two grounds, and each alone rules out PASS. (1) Same-error circuit breaker: all six executions share one operation fingerprint. Only execution 1 has observably different evidence (1108 B of stderr against 0 B for the others). Executions 2 to 5 have no normalized failure messages or per-execution fixture hashes, and executions 2 and 3 have the same stdout length. Different stdout hashes do not prove different errors, because the stdout carries elapsed time and the fixture's own hash. So the evidence does not show that executions 5 and 6 were permitted. (2) A tool wrapper automatically spooled an oversized early-snapshot output to host Temp, outside the current working directory. Section 6.1 says large raw output is never dumped to the console and never written outside the recorded scratch directory. Stage cannot show the snapshot was outside that rule, so it fails closed. This spill is not the earlier, explicit Ship %TEMP% redirect P-005 incident, which stays logged separately. Real-surface control: manifest closure true and raw checksum match true (39089629...). Render parity is FALSE with full resolution from the top-level variables_used (41 keys, 5 placeholders): the render is 7501 B, the same length as the installed file, and first differs at byte 4994. Stage reproduced this read-only. The difference is only a line reflow in Step 5.2, and the texts are equal after whitespace normalization. This is an operator observation and a follow-up need, not a Proof C FAIL. PE-ACTIVATE-01: all three HEAD blobs equal the setup snapshot 4acba14a. No claim authority."
docline:
  type: spike
  date: 2026-09-24
  time_box: "75m"
  conclusion: "blocked"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "surface-taxonomy"
    - "reason-codes"
    - "schema-parity"
    - "proof-entry"
    - "ship-lifecycle"
    - "circuit-breaker"
    - "render-parity"
proof: C
proof_run: 2
proof_verdict: BLOCKED
proof_verdict_basis: "admissibility not established: same-error circuit-breaker compliance for executions 5-6 unproven (no normalized failure messages), and a tool-wrapper spool of oversized output outside the current working directory that cannot be shown to lie outside the section 6.1 bounded-output rule"
section_6_5_fail_condition_found: false
proof_verdict_scope: synthetic-candidate-taxonomy-and-schema
production_resolver_exercised: false
render_parity_observed: "false (fully resolved from top-level variables_used; Stage-reproduced read-only)"
render_parity_is_proof_fail: false
candidate_schema_status: "Stage candidate (proposal, not ratified API); unchanged by this BLOCKED verdict"
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.4"
charter_commit: 52c985cb
matrix_id: PE-1.4
charter_sections: ["3.3", "4.3", "6.1", "6.5"]
matrix_rows: [PE-INTERFACE-03, PE-DATA-01, PE-DATA-02]
evidence_rows_self_assessed: [PE-EVIDENCE-01, PE-ACTIVATE-01, PE-ACTIVATE-03, PE-FLOW-04]
previous_run: {run: 1, verdict: FAIL, artifact: docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md, commit: 9d0ed834, changed: false}
scratch_path: "C:\\Source\\GitHub\\autoharness\\.proof-scratch\\C-20260924-143026\\"
fixture_files:
  - {name: c_truth.py, bytes: 42021, sha256: 256e2d85b733b85e4eea53f14eef15115bc6ad3f70cee8b61f9f30aee1f96ca2, stage_verified: true}
  - {name: c_schema.json, bytes: 25254, sha256: d5f172930a52f08f59bc694e37f2cd02dd761da12c1570d6c7fa2794237c5675, stage_verified: true}
fixture_command: "C:\\Python\\Python314\\python.exe -B .proof-scratch/C-20260924-143026/c_truth.py (cwd: repository root)"
executions:
  - {n: 1, exit: 1, stdout_bytes: 9795, stdout_sha256: 4e9775bb415a3c316f7fdc65f9df0919e29a76335f9b9a5a5dda114b5dd16f6d, stderr_bytes: 1108, stderr_sha256: 6d8f486c5927993a63e8858c2e7016d18e38fb5130b8f9cc76f51df3e715d0b7}
  - {n: 2, exit: 1, stdout_bytes: 9898, stdout_sha256: 50c8b5bf86dbfbba18dd9cba82006193c65a922ee5d03970f8ae18d4d92ecef4, stderr_bytes: 0, stderr_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855}
  - {n: 3, exit: 1, stdout_bytes: 9898, stdout_sha256: cba97bffd2a0384a036cdd005f277a469364ca5c77513af117b39e812c9a70f6, stderr_bytes: 0, stderr_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855}
  - {n: 4, exit: 1, stdout_bytes: 11260, stdout_sha256: 1d7b3da24888c2644c43a535c52fa1b04dff0d6fa58de48b5f50665cc7c0c5f3, stderr_bytes: 0, stderr_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855}
  - {n: 5, exit: 1, stdout_bytes: 12104, stdout_sha256: 642d0fe8a87b3277fe00d708c0059c1ed934a4ba87197b7f9a18313e567c7734, stderr_bytes: 0, stderr_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855}
  - {n: 6, exit: 0, stdout_bytes: 11783, stdout_sha256: dae868d70d156e868780d9d312dcd50b6e188d0e9696c0ed4cd7c890cabfa041, stderr_bytes: 0, stderr_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855}
final_exit_code: 0
nonzero_executions: [1, 2, 3, 4, 5]
circuit_breaker_status: "compliance-not-established (evidence limitation)"
tool_wrapper_spill: "automatic host-Temp spool of oversized early-snapshot output; not agent-directed; content not read by Stage; treated fail-closed"
prior_explicit_temp_redirect_incident: "separate P-005 incident; remains logged; not re-adjudicated here"
real_surface_head: 06f8930b89054d5c350d35b1644c93f7f4f57931
activate_01_matches_4acba14a: true
reopened_decision: "none (BLOCKED routes to the operator, not to architecture or charter)"
blocked_route: operator
branch: chore/stage-176-s-workflow-defects
head_at_ship_execution: 06f8930b
head_at_authoring: 06f8930b
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: "queued/frozen (as reported; not re-read by Stage)"
shipment_claim_ready: false
publication_eligible: false
backlog_item_created: false
plan_changed: false
charter_changed: false
other_proof_verdicts_changed: false
time_bound_status: met-on-conservative-active-time-accounting
file_bound_status: met
scratch_cleanup_status: left-in-place-no-cleanup-approval
---

# Proof C run 2 findings - one-entry SurfaceSpec and total reason truth table

## Verdict

| Field | Value |
|---|---|
| Verdict | **`BLOCKED`** (PE-1.4, section 6.5, run 2). It is not `PASS` and not `FAIL` |
| What was tested | A disposable synthetic model of the charter's Stage candidate (47 codes) and a candidate Draft 7 result schema, plus read-only real-surface controls over Git blobs at `HEAD`. **No production resolver exists, and none was exercised** |
| Why not `FAIL` | Stage checked the hash-pinned final fixture source and schema read-only against sections 6.5 and 3.3. It found **no** section 6.5 fail condition (see Static Verification). The render-parity `false` is fully resolved from the top-level mapping, so by the charter's own text it is an operator observation and not a `FAIL` |
| Why not `PASS` (ground 1) | **Same-error circuit breaker, evidence limitation.** Five of the six executions exited non-zero. The evidence cannot show that executions 2 to 5 failed with genuinely different errors, so it cannot show that executions 5 and 6 were permitted (see Circuit-Breaker Assessment) |
| Why not `PASS` (ground 2) | **Tool-wrapper spill outside the current working directory.** Section 6.1 says large raw output "is never dumped to the console or the transcript" and "is never written outside the recorded scratch directory". A wrapper spooled an oversized early-snapshot output to host Temp. Stage cannot show that this snapshot was outside that rule, so it fails closed (see Spill Assessment) |
| Final process exit | **0** (execution 6). The first five exits were **1, 1, 1, 1, 1**. None of them is hidden or re-labelled |
| `PE-INTERFACE-03`, `PE-DATA-01`, `PE-DATA-02` (`P1`) | **Not satisfied at proof entry.** Their evidence is the Proof C run 2 findings, and this run is `BLOCKED`. The static observations below carry forward only as supporting evidence |
| Real-surface render parity | **`false`**, fully resolved (5 of 5 placeholders from top-level `variables_used`). The only difference is a line reflow in Step 5.2. **This needs an operator follow-up.** It does not by itself make Proof C `FAIL` (section 6.5 item 5) |
| `PE-ACTIVATE-01` | All three `HEAD` blobs equal the `4acba14a` setup snapshot (confirmed by the parent and again by Stage) |
| Claim authority | **None.** No proof result confers publication, claim or closure readiness (`PE-ACTIVATE-03`). `187-S` is not claimed or changed |
| Run 1 | `FAIL` (PE-1.3, `9d0ed834`), unchanged and not re-labelled |

## Question

Charter section 6.5 (PE-1.4, run 2): "Is the taxonomy closed, and does the
schema match the runtime exactly?" Section 6.2 row C asks: "Is a one-entry
`SurfaceSpec` with total member and manifest reason codes a closed,
schema-parity-complete truth table?"

## Evidence as reported by Ship (relayed by the parent)

| Field | Value |
|---|---|
| Scratch path | `C:\Source\GitHub\autoharness\.proof-scratch\C-20260924-143026\`. It is ignored by `.gitignore:10 .proof-scratch/` (Stage confirmed with `git check-ignore -v`) |
| Fixture listing | `c_truth.py` 42021 B `256e2d85b733b85e4eea53f14eef15115bc6ad3f70cee8b61f9f30aee1f96ca2`; `c_schema.json` 25254 B `d5f172930a52f08f59bc694e37f2cd02dd761da12c1570d6c7fa2794237c5675`. Stage re-hashed both with `Get-FileHash` and they match. The directory holds exactly these two files, with no `__pycache__`. File bound: 2 of 2 |
| Command (verbatim) | `C:\Python\Python314\python.exe -B .proof-scratch/C-20260924-143026/c_truth.py`, run from the repository root |
| Executions | Six, all with this same command. See the table below |
| Final report (execution 6, per Ship) | 47 unique codes, including `FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT` and `FILE_SIZE_LIMIT`, with `READ_BUDGET_EXHAUSTED` absent. All 8 governing codes are reachable, map to their governing state and exit, and are schema-valid. 2522 unique input cases: 2162 precedence orderings, 294 two-error read-limit orderings and 21 single injections. 40 schema branches across 6 `oneOf` groups, each produced. 15 mutation negatives are rejected, including the banned code. Unknown well-formed labels yield `SURFACE_UNSUPPORTED / UNRESOLVED / 2`. Final script runtime 66.607 s |
| Real-surface control (per Ship) | Exactly one manifest entry, with the expected template. The raw installed checksum equals the manifest's, both `39089629cd115f80f801c61b37040e2cf5a937940b2ae16f929f184647ba9f36`. All 5 placeholders resolved from the top-level `variables_used` (41 entries). The UTF-8/LF render is 7501 B, the installed file is 7501 B, and the first difference is at offset 4994. Render parity is `false` |
| Index refresh (section 6.1) | The refresh ran in the same invocation: native exit 0, stdout 23 B with SHA-256 `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873`, and stderr 0 B. It touched only the Git-ignored `.backlogit/backlogit.db`, `-shm` and `-wal`. The transport was not named explicitly, and nothing says whether MCP was tried first. The single 23 B process-level result is consistent with the CLI fallback. This is recorded, and it does not decide the verdict |
| Checkpoint scan (unfiltered) | 71 total: 70 resolved and 1 abandoned. 0 `needs_quarantine`, 0 quarantined, 0 active |
| P-001 projections (active filter) | Shipments, tasks, features and chores: 0 each |
| Other gates | One clean worktree on the current branch. No tracked backlog mutation, claim, pull request, push or host branch change |
| `PE-ACTIVATE-01` (parent-verified) | Template `4ccd7fdc2d134de485487acd75bfbc105d6f40ee`, mirror `e22916b62f36f1c25c421882a05f4049f1862c02` and manifest `251f46e8c95703ed65e421210d3b08682d79d8bc` all equal the `4acba14a` values in section 3.3. An earlier Ship reply held a placeholder hash, so the parent-verified values are used here |
| Elapsed (Ship) | About 19 minutes in total |
| Cleanup | None. The scratch stays in place |

### Per-execution record (section 6.5 item 6; `PE-EVIDENCE-01`)

| # | Native exit | stdout bytes | stdout SHA-256 | stderr bytes | stderr SHA-256 |
|---|---|---|---|---|---|
| 1 | **1** | 9795 | `4e9775bb415a3c316f7fdc65f9df0919e29a76335f9b9a5a5dda114b5dd16f6d` | 1108 | `6d8f486c5927993a63e8858c2e7016d18e38fb5130b8f9cc76f51df3e715d0b7` |
| 2 | **1** | 9898 | `50c8b5bf86dbfbba18dd9cba82006193c65a922ee5d03970f8ae18d4d92ecef4` | 0 | `e3b0c442…b855` (empty) |
| 3 | **1** | 9898 | `cba97bffd2a0384a036cdd005f277a469364ca5c77513af117b39e812c9a70f6` | 0 | `e3b0c442…b855` (empty) |
| 4 | **1** | 11260 | `1d7b3da24888c2644c43a535c52fa1b04dff0d6fa58de48b5f50665cc7c0c5f3` | 0 | `e3b0c442…b855` (empty) |
| 5 | **1** | 12104 | `642d0fe8a87b3277fe00d708c0059c1ed934a4ba87197b7f9a18313e567c7734` | 0 | `e3b0c442…b855` (empty) |
| 6 | 0 | 11783 | `dae868d70d156e868780d9d312dcd50b6e188d0e9696c0ed4cd7c890cabfa041` | 0 | `e3b0c442…b855` (empty) |

The empty-stream digest is
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Ship
described executions 1 to 5 as failures caused by defects in its own fixture
instrumentation. It gave no normalized failure message for any of them, and
no fixture hash for executions 1 to 5.

## Circuit-breaker assessment (ground 1)

The rule is `.github/instructions/circuit-breaker.instructions.md`, sections
"Universal Retry Threshold" and "Same-Operation Identity and Hidden Details".

1. **One operation fingerprint.** All six executions have the same
   normalized command, target, working directory and workflow phase. That
   is the baseline identity the rule uses. The Proof E run 2 precedent
   (`docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md`)
   counts a re-run with a corrected script as the same counted operation.
2. **What the evidence distinguishes.** Only execution 1 shows different
   stable evidence: 1108 B of stderr, while executions 2 to 6 have none.
   That is consistent with an uncaught exception in execution 1 and a
   report-with-failures exit in executions 2 to 5. It is a difference in
   channel, and no normalized message is attached.
3. **What it does not distinguish.** Executions 2 to 5 all exited 1 with
   empty stderr. Their stdout hashes differ, but the fixture's stdout
   includes volatile fields: `elapsed_seconds`, and the fixture's own file
   SHA-256 under `fixture_files`, which changes with any edit. So different
   stdout hashes are expected even when the failure is identical.
   Executions 2 and 3 also have the same stdout length (9898 B). The rule
   says hidden output "cannot create the different-error exception". Only a
   genuinely different observable error, with distinct stable evidence,
   breaks the same-error chain.
4. **Consequence.** Take the reading most favourable to Ship, where
   execution 1 is a different error. The chain of executions 2, 3 and 4
   still reaches the threshold of three at execution 4, which leaves
   executions 5 and 6 unproven as permitted. On the stricter reading, where
   all failures share one fingerprint, the threshold is reached at
   execution 3. The evidence cannot rule this out. In either case, the
   admissibility of execution 6, the one exit 0, is not established.
5. **Not a finding against the result.** This is an evidence limitation. It
   is not a finding that Ship broke the breaker, and it is not a finding that
   the final fixture is wrong. The failed executions' errors may well have
   been genuinely different. The evidence handed to Stage does not show it.

## Spill assessment (ground 2)

* **What happened (as relayed).** During an early snapshot, the PowerShell
  tool wrapper automatically spooled an oversized command output to host
  Temp. Ship did not command any redirection and did not use the spooled
  artifact. Stage did not read anything outside the current working
  directory and does not infer what the spool contains.
* **Different from the earlier incident.** This is an automatic spill by the
  tool implementation, not a file operation that the agent directed. The
  earlier, explicit Ship `%TEMP%` redirect is a separate P-005 incident. It
  remains logged as it was, and this artifact does not re-adjudicate it or
  merge it with this one.
* **What the charter says, as written.** The "Bounded projections" sub-bullet
  of section 6.1 reads: "Large raw output is never dumped to the console or
  the transcript. It is captured in process and reported by byte length and
  SHA-256, and it is never written outside the recorded scratch directory."
  This states an outcome, not an actor duty. A wrapper spool happens only
  when output reached the tool's console channel at a size over the
  wrapper's limit, and the spool file then lay outside the scratch directory
  and outside the current working directory.
* **Adjudication.** Stage reads the separate sentence "Every Ship write stays
  inside the current working directory" as covering agent-directed writes.
  So the spill does not break that sentence by itself. But the evidence
  does not name the snapshot command, its output size, or whether it was one
  of the section 6.1 projection or checkpoint reads (for example the
  unfiltered 71-record checkpoint enumeration). So Stage cannot show that
  the bounded-output sentence did not apply. Stage fails closed, and this
  ground alone rules out `PASS`.
* **Required next time.** Every snapshot, projection and fixture output is
  captured in process. The console gets at most a 2 KiB excerpt, plus the
  byte length and SHA-256 of the full stream. Nothing reaches a size at
  which the tool wrapper spools. If a spool still happens, Ship reports the
  command, the size and the fact that a spool occurred. It does not report
  the spool's content or path contents.

## Static verification (Stage, read-only)

Stage did not run `c_truth.py` or any fixture command. It hashed files, read
both fixture files in full, and ran ad hoc read-only Python over the fixture
text, the schema JSON, the charter text and the `git cat-file blob HEAD:<path>`
bytes. It never imported or ran the fixture.

| # | Section 6.5 part | Stage finding | Limitation (non-binding) |
|---|---|---|---|
| S1 | Governing set held apart | `GOVERNING` is a literal dict of 8 codes with their states and exits. It matches the charter table exactly and is not derived from the candidate. The fixture checks that each governing code is in the candidate, is reached from a base input, validates against the schema and has its state and exit | - |
| S2 | Candidate equals charter | Stage parsed the charter's candidate table: 47 codes. It equals the fixture's `G1..G8` concatenation **and** the schema `reason_code` enum, in order. The run 1 enum minus `READ_BUDGET_EXHAUSTED` plus the three class 1b codes equals the run 2 set, and the run 1 order is kept. `READ_BUDGET_EXHAUSTED` occurs 7 times in `c_truth.py`, all in negative checks or report fields, and 0 times in the schema. The partition is 2 `HARNESS_READY`, 4 `NO_HARNESS` and 41 `UNRESOLVED`, which matches the charter reference | Ship's report as relayed does not name the charter commit it copied the constants from, as section 6.5 asks. Stage confirmed that the charter is unchanged since `52c985cb` (`git diff --stat 52c985cb HEAD` on the charter is empty), and that the constants equal it |
| S3 | Enumeration and member classes | 37 Stage-derived fault scenarios and 8 label inputs: one supported, `none`, missing, duplicate, malformed (`Harness-Architect`), mixed supported plus `none`, and unknown well-formed `harvest` and `impl-plan`. The label classifier derives the code from the label shape. Unknown well-formed labels are asserted to be `UNRESOLVED / 2` and never `NO_HARNESS` | The 37 fault scenarios reach their codes by injecting the code itself. Reachability holds by construction for those codes, as in run 1. The charter allows a model ("the fixture models the candidate"). `each_input_maps_to_one_result` is a hard-coded report field. Uniqueness is enforced by the duplicate-ID check and the pure resolver |
| S4 | Class 1b | 3 codes at 7 `ReadStage` values gives 21 single injections, each checked for `UNRESOLVED / 2`, its own code, and `read_error_code=` and `read_stage=` in the diagnostics. 7 × 7 stages × 6 ordered code pairs gives 294 two-error orderings, each expected to yield the first code, keeping the first stage. `choose` returns `matches[0]` for class 1b, so there is no fixed internal rank | The list order stands in for deterministic generation order. The schema's class 1b branch requires a `read_stage=` diagnostic but not a `read_error_code=` one. The runtime check covers that |
| S5 | Closure and precedence | Every ordered pair of distinct codes, with no exclusions: cross-group 2 × (47² − Σsize²)/2 = 2 × 868 = 1736, and within-group 2 × 213 = 426. Total 2162, which equals the report. Inputs: 37 + 8 + 21 + 294 + 2162 = **2522**, which equals the report. For a minimum over a total order, checking pairs is enough | - |
| S6 | Schema parity | The Draft 7 schema has `additionalProperties: false` and 10 required fields. It has 6 top-level branches (reason enums of 1, 1, 4, 3, 31 and 7, which partition the 47). Stage counts 6 `oneOf` groups with 40 branches, which equals the report. Branch coverage uses branch-isolated validators, so the validator itself says which branch matched (an improvement on run 1). An uncovered branch, a match count other than one, or an invalid output each add a failure | `valid_candidate_schema: true` is hard-coded. A malformed schema would raise in `check_schema` first |
| S7 | Mutation negatives | 15 mutants, including `READ_BUDGET_EXHAUSTED` in a class 1b output, a class 1b code replaced by `MEMBERS_TOO_MANY`, and class 1b with no `read_stage`. There is also a separate control that deletes an enum value. Any accepted mutant adds a failure | - |
| S8 | Exit semantics | `main` returns 1 when any check failed. The real-surface closure and checksum are hard checks. Render parity is reported but excluded from failures, as section 6.5 item 5 requires. An exit 0 from these exact hash-pinned bytes therefore means every internal check passed | The raw stdout of execution 6 was not handed to Stage, only its hash, so Stage cannot cross-check the relayed figures against the bytes. Stage's arithmetic reproduces every relayed count |

## Real-surface control and render mismatch (follow-up needed)

Stage reproduced the control read-only from the `HEAD` `06f8930b` blobs.
Nothing was changed since `4acba14a` on these paths:

| Item | Value |
|---|---|
| Installed `.github/skills/harness-architect/SKILL.md` | Blob `4a7d9776…`, 7501 B, 0 CRLF, raw SHA-256 `39089629cd115f80f801c61b37040e2cf5a937940b2ae16f929f184647ba9f36` |
| Template `templates/skills/harness-architect/SKILL.md.tmpl` | Blob `2aa1f9c5…`, 7423 B, 0 CRLF, raw SHA-256 `9360bea275d640b16efa7b261e39ae1cef68a16d5a00ed1c55e25345a74e99fd` |
| Manifest | Blob `251f46e8…`, raw SHA-256 `e3ddbac3…25d0`. One entry at lines 237-239, with template `skills/harness-architect/SKILL.md.tmpl` and `checksum` equal to the installed raw SHA-256. The entry has no `variables_used`. The top-level `variables_used` is at line 467, with 41 keys |
| Placeholders | `BUILD_CHECK_COMMAND`, `SOURCE_DIR`, `TEST_COMMAND`, `TEST_DIR` and `UNIMPLEMENTED_MARKER`: 8 occurrences, all resolved from the top-level mapping |
| Render | 7501 B, SHA-256 `9ebaaaf8525149ae67071fa2634f0c5152a38e5a2906813b744a6a1784e5d5b9`, **not equal**. First difference at byte 4994 |
| Nature of the difference | Only a Markdown line reflow of the Step 5.2 paragraph: installed lines 126-131 against five rendered lines. The two are equal after whitespace normalization |
| Section 6.5 status | Checksum match `true`. Render parity **`false`**, fully resolved from the top-level mapping and compared byte for byte. This is a recorded observation of the real installed surface. It goes to the operator, and it is not a Proof C `FAIL` |

**Follow-up for the operator.** A byte-exact render-parity resolver would
classify this one supported surface as `RENDER_MISMATCH`, which gives
`STALE` and then `NO_HARNESS / 1` at `HEAD` today, even though its manifest
checksum matches. The manifest entry's `note` says the template is "Mirrored
byte-for-byte (aside from resolved placeholders)". At `HEAD` that is not
exact, because of the Step 5.2 wrapping. Following
`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`,
the right answer is to reconcile the bytes, either by reflowing the template
or by re-rendering the installed file and refreshing its checksum. It is not
to loosen the comparison. Any such change is a production template, installed
or manifest change, which section 4.3 prohibits until proof exit. It needs
its own operator-approved release unit afterwards. Stage recorded no stash
entry, because backlog edits are out of scope here.

## Time and file bounds

This is conservative active-time accounting against 75 minutes, Stage and
Ship together, with nothing pooled with run 1:

* The Stage candidate was derived inside the PE-1.4 change-control session.
  At most 14 minutes are charged: the whole span from `4acba14a` (12:52:49)
  to `52c985cb` (13:06:00), though that session also covered other parts.
* Ship took about 19 minutes. The scratch directory is timestamped 14:30:26.
* This Stage adjudication runs from 14:48:52 to the commit of this artifact,
  about 25 minutes. The exact commit time is in the Git log.

The upper bound is about 58 minutes, so the bound is met. The time bound is
not a cause of the verdict. File bound: 2 of 2 disposable, met.

## Tool states and Stage compliance

| Item | State |
|---|---|
| Tool gate | No MCP tool was needed for this read-only adjudication. backlogit was not probed. engram, intercom and graphtor-docs exposed no tools this session (`ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`). File-based reading was used |
| Index sync | **Not run by Stage.** Section 6.1 says "Stage never runs the refresh or any backlog CLI mutation for a proof". That overrides Stage's general Step 0.1 for this session |
| Learnings | Read `docs/compound/096-S-template-vs-global-skill-placeholders.md` and the 2026-08-15 checksum-drift learning, both for render parity. Also read the circuit-breaker instructions and the Proof E run 2 precedent |
| Host (Stage-observed, supplementary) | Windows 11 Enterprise 10.0.26200, NTFS, Python 3.14.3, jsonschema 4.26.0, PyYAML 6.0.3. The fixture's own host block is inside the hashed stdout and was not relayed |
| Writes | Only this artifact. There was no session memory or checkpoint write, because the operator limited this session to one committed artifact. No backlog, plan, charter, stash, source, template or scratch change. Nothing outside the current working directory was read or written |

## Route and next step (BLOCKED goes to the operator)

1. `BLOCKED` goes to the operator and is never converted into `PASS`. No
   architecture or charter decision is reopened, so this is not a
   `PE-FLOW-04` charter bump.
2. **Resolving ground 1 without executing anything.** If Ship still holds
   the evidence it already captured, it can give, for executions 1 to 5, the
   normalized failure message (the `fixture_failures` entries, or the first
   stderr line for execution 1), plus the fixture SHA-256 in effect at each
   execution. Inspecting evidence that was already captured is not another
   attempt. If that evidence shows a genuinely different error at each step,
   Stage may record an addendum. This artifact stays immutable.
3. **Resolving ground 2.** Ship names the snapshot command that spooled, its
   output byte length, and whether it was a section 6.1 projection or
   checkpoint read. It does not report the spool's content. If the operator
   rules that section 6.1 does not cover this spill, that ruling goes on
   record. Otherwise the ground stands.
4. **If neither can be resolved, a fresh run needs explicit operator
   authorization**, because of the breaker. It needs a new scratch directory,
   fresh 75-minute and 2-file bounds, the final fixture frozen and hashed
   before the first execution, and one counted execution with bounded
   console output (see Spill Assessment). Normalized failure messages must be
   captured for any non-zero exit.
5. **Render parity.** This is an operator observation that needs a release
   unit after proof exit (see above).
6. **Scratch.** Both `C-20260924-120736` (run 1) and `C-20260924-143026`
   (run 2) stay in place as hash-pinned evidence until the operator approves
   cleanup (section 6.1).

## Cross-references

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (PE-1.4, `52c985cb`; sections 3.3, 4.3, 6.1 and 6.5)
* `docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md` (run 1 `FAIL`, unchanged)
* `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md` (Decision 2)
* `docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md` (circuit-breaker counting precedent)
* `.github/instructions/circuit-breaker.instructions.md`
* `docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`
* `docs/compound/096-S-template-vs-global-skill-placeholders.md`
