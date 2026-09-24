---
title: "Proof B run 3 (PE-1.4) - CLI authenticity: findings (PASS, disposable stub and predicate only)"
source: "docs/decisions/2026-09-24-cli-authenticity-proof-b-run3-spike.md"
doc_type: decision
description: "Stage-authored formal adjudication of Proof B run 3 under charter PE-1.4 section 6.4 (unchanged from PE-1.3) and the PE-1.4 section 6.1 evidence handoff. In the one current worktree at HEAD 669ee9f6, Ship ran the byte-identical Proof B disposable stub (4872 B, 84ce8654...2165f) and verifier (10928 B, 193cba3f...e095) from a new ignored scratch directory, .proof-scratch/B-run3-20260924-164112/. Stage re-hashed both read-only, and they match runs 1 and 2. Before the first scratch write Ship ran a same-invocation CLI refresh (backlogit --no-update-check --log-level error sync: exit 0, stdout 23 B cf46e51c...e873, stderr 0 B). It bracketed that refresh with a 3882-path .backlogit stat inventory: before 7ae89877...42f4, after 1d5fd10f...4b43. Only the ignored .backlogit/backlogit.db and .backlogit/backlogit.db-wal changed. Ship then launched the verifier directly, with no runpy wrapper and no interception of the verifier's subprocess calls: C:\\Python\\Python314\\python.exe -B .proof-scratch\\B-run3-20260924-164112\\proof_b_verify.py. The verifier exited 0, with stdout 8628 B (9865ffee...15e8) and stderr empty. Its summary was PASS, 25 cases, 25 passed and 0 failed. Ship relayed a native status and full stdout and stderr SHA-256 for every one of the 25 child cases. Stage reproduced 20 of those digests from the stub source by hashing predicted bytes, without running the fixture. Of the 4 interpreter-dependent streams, I2 stderr equals the run 1 digest, and I1 stderr, I3 stderr and I4 stdout are new under Python 3.14.3. This closes run 2's evidence gaps G1 to G4. All 5 genuine verdicts are accepted and all 20 impostors are rejected. No status value alone predicts acceptance, and no accepted case carries missing or truncated content. Explicit finding on the tool spool: while Ship was reporting the G4 inventory, one command accidentally sent the whole 3882-entry inventory JSON to the console, and the host tool wrapper spooled it outside the current working directory. It was cache stat metadata, not a section 6.1 P-001 list, not checkpoint output and not fixture stdout, and no agent directed the write. Under the Proof A run 5 and Proof C run 2 readings of section 6.1, it is not a ground for BLOCKED. This is Stage's interpretation, not an operator sign-off, and an operator veto converts the verdict to BLOCKED, not FAIL. Verdict PASS for the disposable stub and predicate only. No production resolver was exercised. Runs 1 (PASS, PE-1.3) and 2 (BLOCKED, PE-1.4) stay as recorded. No plan, charter or backlog edit. No claim authority."
docline:
  type: spike
  date: 2026-09-24
  time_box: "60m"
  conclusion: "proceed"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "cli-authenticity"
    - "resolver-contract"
    - "acceptance-predicate"
    - "proof-entry"
    - "ship-lifecycle"
proof: B
proof_run: 3
proof_verdict: PASS
proof_verdict_scope: disposable-stub-and-predicate-only
proof_verdict_conditions: "Stage interpretations recorded without operator sign-off: (1) tool-wrapper spool of the G4 cache inventory is not a section 6.1 breach; (2) direct CLI refresh transport accepted as in Proof A run 5. An operator veto of either converts this verdict to BLOCKED, not FAIL"
behavior_disproven: false
production_resolver_exercised: false
candidate_schema_status: proof-b-local-candidate-not-finalized
prior_run_artifacts:
  - {run: 1, path: docs/decisions/2026-09-24-cli-authenticity-proof-b-spike.md, commit: 83525c62, verdict: PASS, matrix: PE-1.3, pe_1_4_status: "historical PASS; does not satisfy PE-1.4 proof exit (section 3.3)"}
  - {run: 2, path: docs/decisions/2026-09-24-cli-authenticity-proof-b-run2-spike.md, commit: 669ee9f6, verdict: BLOCKED, matrix: PE-1.4, pe_1_4_status: "historical BLOCKED; evidence gaps G1-G4 closed by this run's own evidence, not by transcription into run 2"}
prior_run_verdicts_changed: false
run2_gaps_closed_by_this_run: [G1-per-child-status-and-stream-digests, G2-parent-execution-record, G3-wrapper-source-or-hash, G4-pre-refresh-ignored-inventory]
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.4"
matrix_id: PE-1.4
charter_sections: ["3.3", "6.1", "6.4"]
matrix_rows: [PE-INTERFACE-02, PE-SAFETY-05]
evidence_rows_assessed: [PE-EVIDENCE-01, PE-EVIDENCE-05, PE-AUTH-01, PE-AUTH-02, PE-AUTH-03, PE-ACTIVATE-01, PE-SCOPE-07]
scratch_path: "C:\\Source\\GitHub\\autoharness\\.proof-scratch\\B-run3-20260924-164112\\"
fixture_files:
  - {name: proof_b_stub.py, bytes: 4872, sha256: 84ce86549fcd2672cf9ad3b412909c428a545ed89d49cf3db38d26da94a2165f, stage_verified: true, identical_to_runs_1_and_2: true}
  - {name: proof_b_verify.py, bytes: 10928, sha256: 193cba3fa0cb61b5988bba0c05041003dcdc9d5474b02e8e1b00a45af339e095, stage_verified: true, identical_to_runs_1_and_2: true}
host: {os: "Windows 11 build 26200", filesystem: NTFS, interpreter: "Python 3.14.3 (C:\\Python\\Python314\\python.exe)", jsonschema: "4.26.0"}
verifier_launch: "C:\\Python\\Python314\\python.exe -B .proof-scratch\\B-run3-20260924-164112\\proof_b_verify.py"
verifier_native_exit: 0
verifier_stdout: {bytes: 8628, sha256: 9865ffee0eb7b7734c8345a837c174a9ac9c45180a6af1231b12afa3529215e8}
verifier_stderr: {bytes: 0, sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855}
capture_helper_source_sha256: c8fa4ca69f8e24877b6f3772f6042c2aab68cdffb01bc0c2162471c4ddbed7fa
verifier_subprocess_intercepted: false
cases_total: 25
cases_passed: 25
cases_genuine_accepted: 5
cases_impostor_rejected: 20
per_case_digests_relayed: "all 25 (native status, stdout SHA-256, stderr SHA-256)"
stage_reproduced_digests: "20 of 20 source-determined streams (plus EMPTY); I2 stderr equals run 1; I1 stderr, I3 stderr, I4 stdout interpreter-dependent and not predicted"
stderr_channel_rule: "any stderr byte => resolver-not-observed (R2)"
index_refresh: {transport: "CLI", command: "backlogit --no-update-check --log-level error sync", native_exit: 0, stdout_bytes: 23, stdout_sha256: cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873, stderr_bytes: 0}
backlogit_ignored_inventory: {paths: 3882, before_sha256: 7ae898773ae1e2f9fb2731d9c3e7a96dc525443929cd2e72f53acbc0c5d942f4, after_sha256: 1d5fd10fcddc38b2078ea240aa07ac23bd75d5beca34cb242044d008b8734b43, changed: [.backlogit/backlogit.db, .backlogit/backlogit.db-wal], changed_all_git_ignored: true}
tool_spool_status: "one automatic host tool-wrapper spool outside cwd of the G4 .backlogit stat inventory JSON (3882 entries) emitted by a reporting command; not P-001 list, checkpoint or fixture output; not agent-directed; Stage interpretation: not a section 6.1 ground; disclosed; not an operator sign-off; veto => BLOCKED"
branch: chore/stage-176-s-workflow-defects
head_at_ship_execution: 669ee9f6
head_at_authoring: 669ee9f63d5cdd569c3465c194b2c30efcf750f5
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: "queued, 17 members, unclaimed (Ship-reported; not re-read by Stage)"
shipment_claim_ready: false
publication_eligible: false
backlog_item_created: false
plan_changed: false
charter_changed: false
fail_route: none
reopened_decision: none
time_bound_status: met
file_bound_status: "met (2 disposable files; the capture helper was inline and wrote no file)"
scratch_cleanup_status: "retained; Stage deleted nothing"
stage_model_route: "claude-opus-5.5/anthropic/high requested; unverified by Stage (route not self-verifiable)"
---

# Proof B run 3 findings (PE-1.4): CLI authenticity

## Verdict

| Field | Value |
|---|---|
| Proof | B, CLI authenticity ([charter](2026-09-23-lifecycle-proof-entry-charter.md) section 6.4, unchanged by PE-1.4) |
| Run | 3, scratch `.proof-scratch/B-run3-20260924-164112/`. This is a new admissible-run attempt under section 3.3, with its own time and file bound |
| Verdict | **`PASS`**, for the disposable stub CLI and acceptance predicate only. No production resolver exists, and none was exercised |
| Conditions | Two Stage interpretations are recorded without an operator sign-off: the tool-wrapper spool (see Tool-Wrapper Spool: Explicit Finding) and the direct CLI refresh transport. **If the operator vetoes either, this verdict becomes `BLOCKED`, not `FAIL`** |
| `PE-INTERFACE-02` (`P1`) | **Met** for the disposable fixture. Every impostor yields `resolver-not-observed`, and every genuine verdict is accepted |
| `PE-SAFETY-05` (`P1`, Proof B half) | **Met.** No Proof B case returns success with missing or truncated content. Proof G holds the other half |
| `PE-EVIDENCE-01` (`P1`) | **Met** from Ship's own evidence for this invocation. Run 2 gaps G1 to G4 are closed here (see Closure of Run 2 Gaps) |
| Earlier runs | Run 1 `PASS` (PE-1.3, `83525c62`) and run 2 `BLOCKED` (PE-1.4, `669ee9f6`) stay as recorded. Neither is re-labelled, and neither artifact is edited |
| Authority | None. This run grants no claim, publication, P-004 red or `harness-ready` authority. `187-S` stays `queued` |

## Goal

Charter section 6.4: can Ship tell a real resolver verdict from a crash or
impostor output, using process status plus exactly one schema-valid document?

## Success Criteria (charter section 6.4, in substance)

* **Pass.** The predicate accepts only one schema-valid JSON document on
  stdout whose requested shipment, state, reason code and exit code all match
  the request and the process status. It returns `resolver-not-observed` for
  every impostor:
  * startup failure, unknown command, argparse usage error and help text;
  * empty stdout and malformed JSON;
  * two documents, and leading or trailing output;
  * a status-to-document exit mismatch, a shipment mismatch and a
    schema-invalid document.

  The proof fixes and records the stderr channel rule.
* **Fail.** Any impostor is accepted, any genuine verdict is rejected, or the
  schema cannot discriminate without relying on status alone.
* **PE-1.4 admissibility (sections 6.1 and 3.3).** The run needs all of
  these:
  * a same-invocation refresh before P-001;
  * bounded projections;
  * the `PE-ACTIVATE-01` blob check before the first write;
  * the full evidence handoff and safety statement (`PE-EVIDENCE-01`,
    `PE-AUTH-01`, `PE-AUTH-02`).

## Scope Constraints and Stage Actions

* **Compound entries read first.**
  * `docs/compound/2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`:
    a wrapper can drop a correctly propagated status while still passing
    output through. This run removes the in-process wrapper.
  * `docs/compound/2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`:
    a timeout is not a clean signal. R0 rejects whatever was captured.
  * `docs/compound/2026-07-01-subprocess-validation-gating.md`: use argv
    arrays with `shell=False`. The verifier and the outer helper both do.
* **Other reads.** Charter sections 3.3, 6.1, 6.2, 6.4 and 7; the run 1 and
  run 2 Proof B artifacts; the Proof A run 5 and Proof C run 2 spool
  precedents; and both run 3 scratch scripts.
* **Read-only commands only:**
  * `git status --porcelain`, `git log`, `git worktree list --porcelain`,
    `git rev-parse HEAD:<path>` and `git check-ignore -v`;
  * a recursive `-Force` listing and `Get-FileHash` of the run 3 scratch
    directory;
  * `Test-Path` on the interpreter's `jsonschema-4.26.0.dist-info`;
  * one `backlogit_get_version` probe with `no_update_check: true`;
  * one inline Python computation that hashed byte strings Stage predicted
    from the stub source. It did not import, run or read-execute the stub or
    the verifier.
* **Stage executed nothing.** It ran no fixture, verifier, stub, test, build,
  lint, index sync or backlog mutation, did no scratch cleanup, and made no
  plan, charter or backlog edit. Its only write is this file, committed
  normally (no amend, push or PR).

## Session and Tool State (`PE-EVIDENCE-05`)

| Surface | State | Note |
|---|---|---|
| backlogit | `TOOL_OK` | `backlogit_get_version` (`no_update_check: true`) returned `1.10.1-0.20260823032255-b07729386a31+dirty` |
| Index sync (Stage Step 0.1) | Skipped by operator scope | The operator forbade a Stage index sync, and section 6.1 gives the refresh to Ship alone. Stage made no semantic backlog read |
| agent-engram | `ENGRAM_DEGRADED` | No engram tool on this session's surface. Bounded file reads were used instead |
| agent-intercom | `INTERCOM_DEGRADED` | No intercom tool on this session's surface. No broadcast was made. No destructive or approval-dependent action was taken |
| graphtor-docs | `GRAPHTOR_UNAVAILABLE` | No server tool on this session's surface. Direct file reads were used instead |
| Checkpoint recovery (Stage) | Not run | The session was scoped to findings only. Ship reported the unfiltered scan |
| Git at authoring | Tracked tree clean | Branch `chore/stage-176-s-workflow-defects`, HEAD `669ee9f63d5cdd569c3465c194b2c30efcf750f5`, exactly one worktree (porcelain) |

## Ship Invocation Record (relayed by Ship; digests copied exactly)

`EMPTY` below means the SHA-256 of zero bytes,
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

### Per-invocation gates

| Gate | Relayed result |
|---|---|
| Order | Refresh first, then the checkpoint scan and the P-001 reads, then the `PE-ACTIVATE-01` check, then the first scratch write |
| Index refresh | Transport: CLI. Command: `backlogit --no-update-check --log-level error sync`. Native exit **0**. stdout 23 B, `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873`. stderr 0 B, `EMPTY` |
| Checkpoint scan | Unfiltered, 71 total: 70 resolved and 1 abandoned (`valid: true` by an official get). 0 quarantined, 0 active. No `ship`-owned active record |
| P-001 (after the refresh) | Active shipments, tasks, features and chores: 0 each. `173-S` archived, closure READY, compaction done. `187-S` `queued`, 17 members, unclaimed |
| P-002 | No claim, and no `harness-ready` consumption |
| P-010 | Writes limited to scratch and cache |
| P-011 / P-016 | One clean branch, one worktree, HEAD `669ee9f6` |
| `PE-ACTIVATE-01` (before the first write) | All three blobs match `4acba14a` |
| Scratch | New, Git-ignored, created before the two unchanged scripts were copied in. No `__pycache__` |

### Refresh footprint (closes run 2 G4)

| Snapshot | Scope | Canonical inventory SHA-256 |
|---|---|---|
| Before the refresh | 3882 `.backlogit` paths (stat mtime and size) | `7ae898773ae1e2f9fb2731d9c3e7a96dc525443929cd2e72f53acbc0c5d942f4` |
| After | 3882 paths | `1d5fd10fcddc38b2078ea240aa07ac23bd75d5beca34cb242044d008b8734b43` |
| Changed | `.backlogit/backlogit.db` and `.backlogit/backlogit.db-wal` only | Both Git-ignored. Stage confirmed them read-only with `git check-ignore -v`: `.gitignore:11:.backlogit/*.db` and `.gitignore:14:.backlogit/*.db-wal`. The path count is unchanged, so nothing was added or removed |

Tracked status was clean before and after, and the final tracked status was
clean.

### Verifier launch (closes run 2 G2 and G3)

| Item | Value |
|---|---|
| Command, verbatim | `C:\Python\Python314\python.exe -B .proof-scratch\B-run3-20260924-164112\proof_b_verify.py` |
| cwd and environment | `C:\Source\GitHub\autoharness`, with the inherited environment |
| Outer capture helper | Inline Python, source SHA-256 `c8fa4ca69f8e24877b6f3772f6042c2aab68cdffb01bc0c2162471c4ddbed7fa`. It calls `subprocess.run` with `capture_output=True`, `stdin=DEVNULL`, `shell=False`, `check=False` and `timeout=900`. **It does not intercept or patch the verifier's subprocess calls**, and it uses no `runpy` wrapper |
| Verifier native exit | **0** |
| Verifier stdout | 8628 B, `9865ffee0eb7b7734c8345a837c174a9ac9c45180a6af1231b12afa3529215e8` |
| Verifier stderr | 0 B, `EMPTY` |
| Summary line | `PASS`: 25 cases, 25 passed, 0 failed. Host facts: Python 3.14.3, jsonschema 4.26.0 |
| Child command (in the verifier source) | `python.exe -B -m proof_b_stub harness resolve --workspace . --shipment REQ --json`, with `PROOF_B_MODE` set per case and `PYTHONPATH` set to scratch, except for I1, where it is removed. I2 to I4 change argv exactly as in `CASES` |
| Elapsed | Ship 6m45s |

### Per-child records (closes run 2 G1)

Format: `expected = observed`, native exit, stdout SHA-256, stderr SHA-256.
The "Stage" column shows the result of hashing the bytes Stage predicted from
the stub source. **It is corroboration, not a substitute for Ship's values.**

| Case | Expected = observed | Native exit | stdout SHA-256 | stderr SHA-256 | Stage |
|---|---|---|---|---|---|
| G1 | accept = accept | 0 | `116f55cc0c1c8b5b5f4c711c9772a7f4fdb44691ee94fd41a0833f1abf3da709` | `EMPTY` | reproduced (272 B) |
| G2 | accept = accept | 0 | `63826056b6d0e99a0221ab18a0fd708c740ae88aafcc9a44b5767b0eb29a7c63` | `EMPTY` | reproduced (LF) |
| G3 | accept = accept | 1 | `4100ec1a740883b0153eb2ae1c3849bd1580c4d415ff68c00d6165d17580b37a` | `EMPTY` | reproduced (CRLF) |
| G4 | accept = accept | 2 | `629160ad55e7a27a7c1553737a3723d42b157b37b099cc582ad0b21ea75b4def` | `EMPTY` | reproduced |
| G5 | accept = accept | 2 | `ea80f80b331b2007d5716c824b50c23b42e73745d4dfe4466fb34321cbfcb0b0` | `EMPTY` | reproduced (LF) |
| I1 startup failure | R2 = R2 | 1 | `EMPTY` | `24c37441f4cb6382d4e3bc337621440d2d8bda43453e1551f50806102b8148c6` | Interpreter text, not predicted. New under 3.14.3 |
| I2 unknown command | R2 = R2 | 2 | `EMPTY` | `51f7a569abb8d8780688ce3a4d519cf326784d1e58ed0c97e813d1c48545091a` | Equals run 1's digest |
| I3 usage error | R2 = R2 | 2 | `EMPTY` | `0016fd10badf06a798ca9340a84d0999825f3f15f26d47e9b45967b60057a027` | Interpreter text, not predicted. New under 3.14.3 |
| I4 help text | R6 = R6 | 0 | `ca93acd0e60ebf8a545261ac9d74491d4be7445919c1750ed5762c709014fedd` | `EMPTY` | Interpreter text, not predicted. New under 3.14.3 |
| I5 empty | R3 = R3 | 0 | `EMPTY` | `EMPTY` | reproduced |
| I6 malformed | R6 = R6 | 0 | `86cc54391c010498d9a5999ac5f89ecc44677452ac75191f9aefd346230a5725` | `EMPTY` | reproduced (18 B) |
| I7 two documents | R7 = R7 | 0 | `e67ab29dadbdd98906774fc6f2bd2a442d16bda340d494ac37abaeedcf8ad246` | `EMPTY` | reproduced (546 B, Windows text-mode `\r\n`) |
| I8 leading banner | R5 = R5 | 0 | `b179b199abc6ccec8bce33a95a49f80a517d24c9d01862d1cd79b66b9afc0573` | `EMPTY` | reproduced (298 B) |
| I9 trailing output | R7 = R7 | 0 | `8f7d9576cb99fe7895a9cdd20ddaf6d677ee2d9a5a88f84a00d828a489a4bac3` | `EMPTY` | reproduced |
| I10 exit mismatch | R9 = R9 | 1 | `116f55cc0c1c8b5b5f4c711c9772a7f4fdb44691ee94fd41a0833f1abf3da709` | `EMPTY` | reproduced (= G1) |
| I11 shipment mismatch | R10 = R10 | 0 | `bb45eb4a00a47fb545d2cd579b281bdedb96045cf8f4fd6daf4ebb1b8171b9b4` | `EMPTY` | reproduced |
| I12a READY exit 2 | R8 = R8 | 2 | `a142d038efc0701c83ff1861f68486f2f828330260e9ee84407cb715de26ddbf` | `EMPTY` | reproduced |
| I12b wrong reason | R8 = R8 | 2 | `1b7ef5f7b39a61791129516f750b9bb7e3679651d6d9994657c4a882a524860c` | `EMPTY` | reproduced |
| I12c missing hash | R8 = R8 | 0 | `b16e6e4c3e765979d5b37ec09f18d4edc2ffc9052472cb5122e0e875293ad8f0` | `EMPTY` | reproduced (189 B) |
| X1 invalid UTF-8 | R4 = R4 | 0 | `a8100ae6aa1940d0b663bb31cd466142ebbdbd5187131b92d93818987832eb89` | `EMPTY` | reproduced (`0xFF`) |
| X2 JSON scalar | R8 = R8 | 0 | `b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b` | `EMPTY` | reproduced (`true`) |
| X3 JSON plus stderr | R2 = R2 | 0 | `116f55cc0c1c8b5b5f4c711c9772a7f4fdb44691ee94fd41a0833f1abf3da709` | `e99c2db6865fb97b3f1f8fb6e78a33109251200cc4fad899488b6a6bdf5c8883` | both reproduced (stderr `diagnostic\r\n`, 12 B) |
| X4 duplicate key | R6 = R6 | 0 | `318be7735e486b3e97d2339adc7909eb92d7f056131f98c428ab37f9c779faa5` | `EMPTY` | reproduced |
| N1 status out of domain | R1 = R1 | 3 | `116f55cc0c1c8b5b5f4c711c9772a7f4fdb44691ee94fd41a0833f1abf3da709` | `EMPTY` | reproduced (= G1) |
| R0 timeout | R0 = R0 | null (timeout) | `EMPTY` | `EMPTY` | consistent: the sleep mode writes nothing |

**Totals.**

* All 25 records have expected equal to observed.
* 5 cases are accepted, and those are exactly G1 to G5.
* Every native exit is an integer, except R0, whose `null` means the timeout
  fired.
* The 20 source-determined streams (plus `EMPTY`) that Stage predicted all
  reproduce exactly. Every other stdout and stderr is `EMPTY`.
* The I8 digest equals the summary pointer that Ship relayed separately.

## Closure of Run 2 Gaps (from this run's own evidence)

| Run 2 gap | How run 3 closes it |
|---|---|
| G1: per-child records | Ship relayed a native status and full stdout and stderr SHA-256 for all 25 cases (table above) |
| G2: parent execution record | Ship relayed the verbatim verifier command, cwd and environment, native exit 0, and the verifier's stdout (8628 B) and stderr (0 B) lengths and SHA-256 values, plus the summary line |
| G3: wrapper integrity | The `runpy` wrapper that patched `subprocess.run` is gone. The verifier ran as its own process, and its child calls were not intercepted. The only remaining layer is an outer helper that captures the verifier's streams. Its parameters are recorded and its source SHA-256 is relayed. **Residual:** Stage has the helper's hash, not its text, so it cannot recompute the hash. That leaves no trust gap in the case labels, because the helper sits outside the verifier and cannot alter what the verifier's own `subprocess.run` receives from each child. The 20 reproduced child digests are evidence that the verifier saw the true child bytes |
| G4: pre-refresh inventory | Ship recorded the before and after 3882-path inventories around the refresh itself. The delta is limited to the two ignored cache files |

This run's own same-invocation evidence closes each gap. Nothing is copied in
from run 2, and nothing is supplied by Stage prediction.

## Criterion Assessment

**Pass: genuine verdicts accepted.** G1 to G5 are accepted with native exits
0, 0, 1, 2 and 2. Each stdout is exactly the schema-valid document for `REQ`,
with no terminator, LF or CRLF (all three reproduced). Every stderr is
`EMPTY`. **Met.**

**Pass: every impostor gives `resolver-not-observed`.**

| Charter impostor class | Cases | Result |
|---|---|---|
| Startup failure | I1 | Rejected (R2) |
| Unknown command | I2 | Rejected (R2) |
| Argparse usage error | I3 | Rejected (R2) |
| Help text | I4 | Rejected (R6) |
| Empty stdout | I5 | Rejected (R3) |
| Malformed JSON | I6 | Rejected (R6) |
| Two documents | I7 | Rejected (R7) |
| Leading output | I8 | Rejected (R5) |
| Trailing output | I9 | Rejected (R7) |
| Status-to-document exit mismatch | I10 | Rejected (R9) |
| Shipment mismatch | I11 | Rejected (R10) |
| Schema-invalid document | I12a to I12c | Rejected (R8) |

The six extra cases, X1 to X4, N1 and R0, are rejected as well. **Met.** The
R-sub-codes are verifier-local and non-binding (CR-B1).

**Fail disjunct 1: an impostor accepted.** None was: the accept count is
exactly 5, all of them G cases. In `classify()`, every rejection path returns
before the single final `return True`. **Not shown.**

**Fail disjunct 2: a genuine verdict rejected.** None was. **Not shown.**

**Fail disjunct 3: status alone discriminates.**

* Accepted cases exist at rc 0 (G1), rc 1 (G3) and rc 2 (G4).
* Rejected cases exist at the same legal rc values: I12a and I12b at rc 2 and
  I12c at rc 0 (R8), I10 at rc 1 (R9), and I11 at rc 0 (R10).
* I10, X3 and N1 carry stdout byte-identical to the accepted G1 document
  (`116f55cc...a709`), yet all three are rejected. That shows the process
  status and the stderr channel are bound to the document, rather than either
  one deciding alone.

So no status value predicts acceptance. **Not shown.**

**`PE-SAFETY-05` (Proof B half).** Missing or truncated content is never
accepted: I6 (truncated), I12c (missing `inputs_sha256`), I5 (empty) and R0
(timeout, nothing captured) are all rejected. **Met.**

**Stderr channel rule (fixed and recorded, unchanged since run 1).**

* Any stderr byte means `resolver-not-observed` (R2).
* The check runs after the status-domain check (R1) and before any stdout
  inspection.
* X3 shows that a byte-identical genuine document is refused when stderr
  holds `diagnostic\r\n`.
* G1 to G5 have `EMPTY` stderr under Python 3.14.3. This time that is
  evidenced by digest, not just implied by the labels. No interpreter warning
  turned a genuine verdict into a rejection.

CR-B5, which carries this rule into the production `--json` contract, stays
open.

**Timeout (R0).** The native status is `null`, and both streams are `EMPTY`.
The verifier rejects on `TimeoutExpired` whatever partial output was
captured, which is consistent with the compound timeout lesson. The outer
helper's 900 s timeout did not fire, because the verifier exited 0.

## Tool-Wrapper Spool: Explicit Finding

**Fact, as relayed.** Ship ran a command to report the G4 cache-inventory
result. By accident, it sent the whole 3882-entry `.backlogit` stat inventory
JSON to the console, and the host tool wrapper then spooled that output
automatically to a file outside the current working directory. Ship states:

* it contained no raw checkpoint output, no P-001 list output and no fixture
  stdout;
* Ship did not direct the write;
* no other agent-directed write occurred outside cwd.

Ship relayed no byte length for the spooled output.

**Charter text.**

* Section 6.1, "Bounded projections" sub-bullet: "Large raw output is never
  dumped to the console or the transcript. It is captured in process and
  reported by byte length and SHA-256, and it is never written outside the
  recorded scratch directory."
* Section 6.1, scratch bullet: "Every Ship write stays inside the current
  working directory."

**Stage reading.**

1. **Scope of the bounded-output sentence.** The sentence sits inside the
   sub-bullet that governs the P-001 active-filtered list reads and the
   unfiltered checkpoint scan, and its subject is the raw output of those
   reads. Proof C run 2 applied it the same way. There, Stage failed closed
   only because it could not show that the spooled snapshot was *not* one of
   the section 6.1 projection or checkpoint reads. Here, Ship names the
   command and its content class: a cache safety diagnostic made of path,
   mtime and size metadata, not a projection or checkpoint read. So the Proof
   C run 2 ground is answered by identification, and the sentence does not
   reach this output as written.
2. **"Every Ship write."** Following Proof A run 5 (a `PASS`) and Proof B run
   2, Stage reads this sentence as covering agent-directed writes. The host
   wrapper spools any oversized console output by itself. The spool is host
   plumbing, not a Ship file operation.
3. **Does the wider charter make any diagnostic spool a violation?** Stage
   finds no charter text that does. Section 6.1, rows `PE-AUTH-01` and
   `PE-EVIDENCE-01`, and section 3.3 never mention host spools. The only
   outcome rule on output location is the bounded-projections sentence above,
   which is scoped as described in item 1.
4. **Content risk.** The spooled data is `.backlogit` path names, mtimes and
   sizes. It holds no backlog item content, no checkpoint payload, and no
   status or claim data. The inventory's canonical hashes are recorded above,
   so the evidence does not depend on the spool.

**Finding.** Under the charter as written and the recorded precedents, the
spool is **not a ground for `BLOCKED`**, and it is disclosed here in full.
This is Stage's interpretation, not an operator sign-off.

* **If the operator reads section 6.1 more broadly**, so that any
  large diagnostic reaching the console or a host spool breaches it, then
  this run is **`BLOCKED`** on that ground alone. It routes to the operator
  and is never converted to `PASS`. It is not `FAIL`, because no section 6.4
  fail disjunct is shown.
* **Residual.** The spooled output's byte length, and whether it was the
  before or the after inventory, were not relayed. That does not change the
  finding. Proof C run 2's "Required next time" note asked for the size.
* **Stage-side disclosure.** During this Stage session the wrapper spooled
  one Stage read-only output to OS Temp: the display of the run 2 artifact
  (a tracked document). It held no proof output. The same classification
  applies.

## Other Residuals (disclosed, not grounds)

* **Refresh transport.** Ship ran the registered CLI fallback directly. The
  relay does not say whether `backlogit_sync_index` was attempted first.
  Section 6.1 names MCP first and the CLI "if that fails". Proof A run 5 (the
  same 23 B digest) accepted a CLI record, and the transport, command and
  native exit are recorded, which is what section 6.1 requires. Stage treats
  this as a disclosed residual and not a ground. An operator veto gives
  `BLOCKED`.
* **Refresh excerpt.** Only the byte length and SHA-256 of the refresh output
  were relayed, not an excerpt. Proof A run 5 accepted the same record.
* **Per-case elapsed times.** These were not relayed. The overall Ship
  elapsed time was.
* **Change requests.** CR-B1 to CR-B5 carry forward unchanged from run 1.
  CR-B3 covers float-form `exit_code` being accepted, and CR-B4 covers the
  `RecursionError` on deep nesting. Neither is in the case set, and neither
  affects this verdict.

## Stage Read-Only Corroboration (not Ship evidence)

| Check | Result |
|---|---|
| Fixture hashes and sizes | `proof_b_stub.py` 4872 B `84ce86549fcd2672cf9ad3b412909c428a545ed89d49cf3db38d26da94a2165f`. `proof_b_verify.py` 10928 B `193cba3fa0cb61b5988bba0c05041003dcdc9d5474b02e8e1b00a45af339e095`. Both match Ship, run 1 and run 2 |
| Scratch contents | A recursive `-Force` listing shows exactly two files and no `__pycache__`. CreationTime is 16:41:13 (the copy) and LastWriteTime is 16:25:38 (kept from the source), so neither file was edited after the copy |
| Ignore status | `.gitignore:10:.proof-scratch/` covers both files |
| `PE-ACTIVATE-01` at HEAD | `4ccd7fdc2d134de485487acd75bfbc105d6f40ee`, `e22916b62f36f1c25c421882a05f4049f1862c02` and `251f46e8c95703ed65e421210d3b08682d79d8bc`, equal to `4acba14a`. `git status --porcelain` is empty for the three paths |
| Worktrees and status | `git worktree list --porcelain` shows one worktree. `git status --porcelain` is empty |
| jsonschema | `C:\Python\Python314\Lib\site-packages\jsonschema-4.26.0.dist-info` exists, which agrees with the version Ship relayed |
| Digest reproduction | 20 source-determined streams reproduce exactly (table above). The I2 stderr digest equals run 1's |

## Per-Criterion Verdict

| Criterion or row | Status |
|---|---|
| Section 6.4 Pass: genuine verdicts accepted | **Met** (5/5, evidenced per case) |
| Section 6.4 Pass: every impostor gives `resolver-not-observed` | **Met** (20/20, evidenced per case) |
| Section 6.4: stderr channel rule fixed and recorded | **Met** (any stderr byte gives R2) |
| Section 6.4 Fail disjuncts | None shown |
| `PE-INTERFACE-02` (`P1`) | **Met** (disposable fixture) |
| `PE-SAFETY-05` (`P1`, Proof B half) | **Met** |
| `PE-EVIDENCE-01` (`P1`) | **Met**. Recorded: question, host OS and version, filesystem, interpreter, exact commands, raw or SHA-256 outputs, fixture listing with SHA-256, scratch path, gate results with the refresh record, safety statement, per-criterion verdict, elapsed time and file count |
| `PE-EVIDENCE-05` (`P2`) | **Met** (Session and Tool State) |
| `PE-AUTH-01` (`P0`) | **Met.** On the Ship side: tracked tree clean before and after; fixture writes in scratch only; the refresh changed only the ignored `.db` and `.db-wal` cache. On the Stage side: this commit changes only this `docs/decisions/*-spike.md` file. The spool is classified under the finding above |
| `PE-AUTH-02` (`P1`) | **Met** on Ship's report: one worktree; same-invocation refresh with exit 0 and digests; P-001 read after the refresh with bounded, active-filtered projections; P-002, P-010, P-011 and P-016 passed; unfiltered checkpoint scan with 0 anomalies and 0 active. The CLI-transport residual is disclosed |
| `PE-AUTH-03`, `PE-SCOPE-04` | **Met.** No authorization, claim, P-004 red, `harness-ready` or publication assertion |
| `PE-ACTIVATE-01` (`P0`) | Blobs match `4acba14a` (Ship before the write, and Stage at authoring). The final check is at proof exit |
| `PE-SCOPE-07` | **Met** (see Time and File Bounds) |
| `PE-FLOW-04` | Not engaged (no `FAIL`) |

## Time and File Bounds

| Bound | Charter | Recorded |
|---|---|---|
| Time (Stage plus Ship) | 60m | Ship took 6m45s. The scratch stamp is 16:41:12 -07:00. The Stage session started at 16:44:56 -07:00, leaving at most about 53m. The commit timestamp of this artifact is the durable end record, and it lands well inside the bound. **Met.** It does not pool with runs 1 or 2 (section 3.3) |
| File (2 disposable) | 2 | 2 (`proof_b_stub.py` and `proof_b_verify.py`). The capture helper was inline and wrote no file. **Met** |

## Recommendation

Proof B has one admissible PE-1.4 `PASS` for the disposable stub and predicate,
subject to the two interpretations that await operator review at proof exit
(the spool and the refresh transport). Carry CR-B1 to CR-B5 into the
implementation matrix draft. Retaining or cleaning up the scratch directory is
the operator's call. Stage deleted nothing.

## Confidence

**High** for the behavioral result. Every child record is evidenced by
digest, 20 streams reproduce independently, and the verifier ran without
interception. Admissibility rests on two Stage interpretations that have no
operator sign-off. They are the only remaining route to a different verdict
(`BLOCKED`), and neither could lead to `FAIL`.
