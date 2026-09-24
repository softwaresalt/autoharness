---
title: "Proof B - CLI authenticity: findings (PASS, disposable stub and predicate only)"
source: "docs/decisions/2026-09-24-cli-authenticity-proof-b-spike.md"
doc_type: decision
description: "Stage-authored findings for Proof B under charter PE-1.3 section 6.4. In the one current worktree, Ship ran a disposable stub CLI (module form) and a disposable acceptance predicate with an embedded Proof-B-local candidate schema over 25 cases (5 genuine, 20 impostor), on Windows 11 build 26200 / NTFS / Python 3.12.10 / jsonschema 4.26.0. Stage independently confirmed both fixture SHA-256 values and sizes, and reproduced 19 of Ship's reported stdout hashes and the X3 stderr hash from the stub source by hashing predicted bytes (fixture not run). Ship's I8 stdout hash was relayed with 63 hex digits, and the Stage-predicted 64-digit value equals it with one digit restored. Judged against the charter's binary criterion, all 5 genuine verdicts are accepted, all 20 impostors are rejected (resolver-not-observed), no process status value alone predicts acceptance, and no accepted case carries missing or truncated content. The predicate labels two cases with different rejection sub-codes than Stage's earlier sketch (I4 help R6 instead of R5; X2 scalar R8 instead of R5). The charter defines no sub-code taxonomy and Stage's sketch was never ratified, so these differences do not decide any charter row and are recorded as a change request. Stderr channel rule fixed: any stderr byte rejects. Verdict PASS for the disposable fixture only. No production resolver exists or was exercised. Untested edge cases (float-form exit_code accepted, deep-nesting RecursionError not caught) are recorded as change requests. PE-ACTIVATE-01 drift from setup commit d20820ec is a separate Stage change-control issue, not part of this verdict. No claim authority."
docline:
  type: spike
  date: 2026-09-24
  time_box: "60m"
  conclusion: "proceed"
  confidence: "medium"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "cli-authenticity"
    - "resolver-contract"
    - "acceptance-predicate"
    - "proof-entry"
    - "ship-lifecycle"
proof: B
proof_run: 1
proof_verdict: PASS
proof_verdict_scope: disposable-stub-and-predicate-only
production_resolver_exercised: false
candidate_schema_status: proof-b-local-candidate-not-finalized
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.3"
matrix_id: PE-1.3
charter_section: "6.4"
matrix_rows: [PE-INTERFACE-02, PE-SAFETY-05]
evidence_rows_self_assessed: [PE-EVIDENCE-01, PE-EVIDENCE-05]
scratch_path: "C:\\Source\\GitHub\\autoharness\\.proof-scratch\\B-20260924-114058\\"
fixture_files:
  - {name: proof_b_stub.py, bytes: 4872, sha256: 84ce86549fcd2672cf9ad3b412909c428a545ed89d49cf3db38d26da94a2165f, stage_verified: true}
  - {name: proof_b_verify.py, bytes: 10928, sha256: 193cba3fa0cb61b5988bba0c05041003dcdc9d5474b02e8e1b00a45af339e095, stage_verified: true}
cases_total: 25
cases_genuine_accepted: 5
cases_impostor_rejected: 20
stage_sketch_sub_code_differences: [I4, X2]
stage_sketch_sub_code_differences_binding: false
stderr_channel_rule: "any stderr byte => resolver-not-observed"
evidence_transcription_discrepancy: "I8 stdout hash relayed with 63 hex digits; Stage-predicted 64-digit value recorded"
branch: chore/stage-176-s-workflow-defects
head_at_ship_execution: d20820ec
head_at_authoring: d20820ec
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: "queued/frozen (as reported; not re-read by Stage)"
shipment_claim_ready: false
publication_eligible: false
backlog_item_created: false
plan_changed: false
charter_changed: false
fail_route: none
separate_issue: "PE-ACTIVATE-01 baseline 5bcb00e5 vs setup commit d20820ec - Stage change-control required before proof exit; not part of this verdict"
time_bound_status: met-on-cumulative-active-time-accounting
file_bound_status: met
scratch_cleanup_status: left-in-place-no-cleanup-approval
---

# Proof B findings - CLI authenticity

## Verdict

| Field | Value |
|---|---|
| Verdict | **`PASS` (disposable stub and predicate only)** |
| What passed | A disposable acceptance predicate, together with a Proof-B-local candidate result schema, told every genuine verdict apart from every impostor. The genuine verdicts and impostors came from a disposable stub CLI. **No production resolver exists, and none was exercised.** Nothing here proves how any `backlogit harness resolve` implementation behaves |
| Pass criterion (charter section 6.4) | Met. Only a single schema-valid JSON document on stdout, whose shipment, state, reason code and exit code match the request and the process status, is accepted. Every listed impostor class is rejected. The stderr channel rule is fixed and recorded (see Channel Rule) |
| Fail criteria (charter section 6.4) | None met. No impostor is accepted, no genuine verdict is rejected, and discrimination does not rest on process status alone (see Discrimination Analysis) |
| `PE-INTERFACE-02` (`P1`) | **Satisfied for proof entry.** Every impostor yields `resolver-not-observed` (represented as `accepted=False`), and every genuine verdict is accepted |
| `PE-SAFETY-05` (`P1`, Proof B half) | **Proof B half satisfied.** No Proof B case returns success with missing or truncated content. The row still awaits Proof G |
| Time bound (60m, Stage plus Ship) | **Met on cumulative active-time accounting**, with an upper bound of about 48.5m. The wall-clock span from the earliest Stage analysis is not determinable from the available evidence and is not claimed (see Time and File Bounds) |
| File bound (2 disposable) | **Met.** Two files, and no `__pycache__` |
| Stage-sketch sub-code differences | I4 and X2 carry different rejection sub-codes than Stage's earlier sketch. They are **non-binding**: they do not decide any charter row (see Adjudication) |
| Implementation status | Nothing is implemented. Plan revision 12 stays frozen as a diagnostic record |
| Shipment | `187-S` stays queued and frozen. This verdict grants no claim, publication, P-004 red or `harness-ready` authority |

## Goal

Charter PE-1.3 section 6.4 asks: can Ship distinguish a real resolver verdict
from a crash or impostor output, using only the process status plus exactly one
schema-valid document?

## Success Criteria

Quoted from charter section 6.4 and applied without reinterpretation:

* **Pass.** The predicate accepts only a single schema-valid JSON document on
  stdout whose requested shipment, state, reason code and exit code all match
  the request and the process status. It returns `resolver-not-observed` for
  every impostor: startup failure, unknown command, argparse usage error, help
  text, empty stdout, malformed JSON, two documents, leading or trailing output,
  a status-to-document exit mismatch, a shipment mismatch, and a schema-invalid
  document. The proof fixes and records the channel rule for stderr.
* **Fail.** Any impostor is accepted, any genuine verdict is rejected, or the
  schema cannot discriminate without relying on status alone.
* Matrix rows `PE-INTERFACE-02` and `PE-SAFETY-05` (section 7), each `P1` and
  `not-deferrable`.

The charter's outcome is **binary**: accept, or `resolver-not-observed`. The
charter defines no sub-code taxonomy or sub-code precedence for rejections.

## Scope Constraints

* Section 6.1 actor split. Ship wrote and ran the two disposable scratch files
  in the one current worktree. Stage performed only read-only analysis:
  reading fixture and library source, file metadata and SHA-256 hashing,
  hashing predicted byte strings, and git status and log reads. Stage then
  authored this artifact. Stage did not run the fixture, any test, build or
  lint, or any validation CLI.
* No backlog, charter, plan, template, configuration, test or source file was
  changed by Stage. This artifact is the only tracked change.
* The scratch directory is left in place. No cleanup approval was given, and
  Stage performs no cleanup.

## Tool and Degradation State (PE-EVIDENCE-05)

| Tool | State |
|---|---|
| backlogit | Ship reported: MCP unavailable, CLI fallback works, no index sync, no backlog changes. Stage: MCP tools appear in this session's deferred tool list but were **not invoked**, because the dispatch scope forbids backlog work and no backlog read was needed. Shipment and queue state are taken from Ship's report |
| agent-engram | Ship reported unavailable. Stage: not present on this session's tool surface. File-based reading was used instead |
| agent-intercom | Ship reported unavailable. Stage: not present on this session's tool surface. **Local degraded note:** operator visibility is reduced and no broadcast was made. No approval-dependent or destructive action was taken. Scratch cleanup is not performed |
| graphtor-docs | Ship reported unavailable. Stage: not present on this session's tool surface. Direct file reading was used |

## Ship Execution Evidence (as reported to Stage)

### Host and environment

| Field | Value |
|---|---|
| Host OS | Windows 11, build 26200 |
| Filesystem | NTFS |
| Interpreter | Python 3.12.10, `.venv\Scripts\python.exe` |
| jsonschema | 4.26.0 (Stage confirmed `jsonschema-4.26.0.dist-info` in `.venv`) |
| Branch / HEAD | `chore/stage-176-s-workflow-defects` / `d20820ec881e92b248ad62004b8dfd105b536626` |
| Worktrees | One (`git worktree list` shows only the current worktree; Stage re-checked it read-only at authoring) |

### Per-invocation gates (Ship)

| Gate | Result |
|---|---|
| P-001 | Pass. No active tasks, features, chores or shipments |
| P-002 | Pass. No claim and no `harness-ready` consumption |
| P-010 | Pass. Direct scratch permission, verification only |
| P-011 | Pass. Existing clean chore branch, no branch created or switched |
| P-016 | Pass. One worktree |
| P-012 | Degraded. backlogit CLI fallback works, MCP unavailable. Engram, Intercom and Graphtor unavailable |
| Checkpoints | 71 unfiltered checkpoint summaries, none active |

### Commands

* Parent (exit 0):
  `& .venv\Scripts\python.exe -B .proof-scratch\B-20260924-114058\proof_b_verify.py`
* Child, per case (`shell=False`, `cwd` = repository root, `stdin=DEVNULL`,
  stdout and stderr captured, `timeout=30`):
  `[sys.executable, '-B', '-m', 'proof_b_stub', 'harness', 'resolve', '--workspace', '.', '--shipment', 'REQ', '--json']`.
  I2 to I4 alter the argv (see the case table).
* Child environment: `PYTHONPATH` = absolute scratch path (removed for I1),
  `PYTHONDONTWRITEBYTECODE=1`, and `PROOF_B_MODE` selects the stub behavior.

### Fixture listing (PE-EVIDENCE-01)

| File | Bytes | SHA-256 (Ship) | Stage independent check |
|---|---|---|---|
| `proof_b_stub.py` | 4,872 | `84ce86549fcd2672cf9ad3b412909c428a545ed89d49cf3db38d26da94a2165f` | **Match** (`Get-FileHash`, size match) |
| `proof_b_verify.py` | 10,928 | `193cba3fa0cb61b5988bba0c05041003dcdc9d5474b02e8e1b00a45af339e095` | **Match** (`Get-FileHash`, size match) |

* Scratch path: `C:\Source\GitHub\autoharness\.proof-scratch\B-20260924-114058\`.
  Stage confirmed it is ignored (`.gitignore:10:.proof-scratch/`). A
  recursive `-Force` listing at authoring shows exactly the two files, and no
  `__pycache__`.
* File metadata (read-only, NTFS):
  * the directory and both files have CreationTime 11:41:59;
  * `proof_b_verify.py` has LastWriteTime 11:41:59, equal to its CreationTime;
  * `proof_b_stub.py` has LastWriteTime 11:43:57.

  This metadata is consistent with Ship's report that only the stub was
  corrected after the earlier runs. It suggests the verifier's expected labels
  were written before any run and not edited afterwards. Metadata can be set,
  so this is corroboration only, not proof.

### Run history and safety statement

* Ship reported two earlier full runs. They exposed two defects in the fixture
  only, both in the stub's own output writing:
  * Windows text-mode newline translation;
  * mixed text and binary buffer ordering.

  Ship corrected only its ignored stub. The verifier was not changed (the
  metadata agrees), and no charter-scored behavior was re-labelled from
  accept to reject or back.
* The final complete run took 34.562s, including one 30s timeout case. The
  whole Ship invocation took about 10m36s.
* Ship's summary: 25 of 25 internal expected labels matched.
* Safety statement: `git status --porcelain` was empty before and after the
  run. Stage re-checked it at authoring: still empty before this artifact.

## Case Table and Per-Row Assessment

Ø is the SHA-256 of the empty stream,
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

"Stage hash check" means Stage built the exact bytes the stub source would
emit, from reading the stub, and hashed them in PowerShell. The fixture was
not run. "Not reproducible" marks streams that depend on interpreter or
argparse message text, which Stage cannot predict byte-exactly from source.

| Case | Stub mode / argv | Native rc | stdout SHA-256 | stderr SHA-256 | Ship sub-code | Stage hash check | Charter outcome | Assessment |
|---|---|---|---|---|---|---|---|---|
| G1 | g1, HARNESS_READY / NO_SURFACES_REQUIRED / 0, no terminator | 0 | `116f55cc0c1c8b5b5f4c711c9772a7f4fdb44691ee94fd41a0833f1abf3da709` | Ø | accept | stdout match | accept | Genuine accepted. **Pass** |
| G2 | g2, HARNESS_READY / ALL_SURFACES_PRESENT / 0, one surface, LF | 0 | `63826056b6d0e99a0221ab18a0fd708c740ae88aafcc9a44b5767b0eb29a7c63` | Ø | accept | stdout match | accept | Genuine accepted. **Pass** |
| G3 | g3, NO_HARNESS / MANIFEST_ENTRY_NOT_FOUND / 1, CRLF | 1 | `4100ec1a740883b0153eb2ae1c3849bd1580c4d415ff68c00d6165d17580b37a` | Ø | accept | stdout match | accept | Genuine accepted. **Pass** |
| G4 | g4, UNRESOLVED / INPUT_CHANGED_DURING_RESOLUTION / 2 | 2 | `629160ad55e7a27a7c1553737a3723d42b157b37b099cc582ad0b21ea75b4def` | Ø | accept | stdout match | accept | Genuine accepted. **Pass** |
| G5 | g5, UNRESOLVED / MEMBER_NOT_FOUND / 2, LF | 2 | `ea80f80b331b2007d5716c824b50c23b42e73745d4dfe4466fb34321cbfcb0b0` | Ø | accept | stdout match | accept | Genuine accepted. **Pass** |
| I1 startup failure | g1, `PYTHONPATH` removed (`No module named` path) | 1 | Ø | `953f422d7c404e1bae682a547d527f267e784a477bd509be3b76a9f0964adf50` | R2 | stdout Ø match; stderr not reproducible | resolver-not-observed | Impostor rejected. **Pass** |
| I2 unknown command | argv `harness unknown ...` | 2 | Ø | `51f7a569abb8d8780688ce3a4d519cf326784d1e58ed0c97e813d1c48545091a` | R2 | stdout Ø match; stderr not reproducible | resolver-not-observed | Impostor rejected. **Pass** |
| I3 usage error | argv without `--shipment` | 2 | Ø | `ca7256dda5225d24b3ea1603f8976bc5c1f75619df6a305918a7753eea547f37` | R2 | stdout Ø match; stderr not reproducible | resolver-not-observed | Impostor rejected. **Pass** |
| I4 help text | argv `harness resolve --help` | 0 | `92ac013e732082b995d8e3e64e9cc5f0db5a24778760b9d67551c9bb80db480b` | Ø | R6 (sketch: R5) | stdout not reproducible (argparse layout) | resolver-not-observed | Impostor rejected. **Pass**. Sub-code difference is non-binding (see Adjudication) |
| I5 empty stdout | empty | 0 | Ø | Ø | R3 | match | resolver-not-observed | Impostor rejected. **Pass** |
| I6 malformed / truncated | `{"schema_version":` | 0 | `86cc54391c010498d9a5999ac5f89ecc44677452ac75191f9aefd346230a5725` | Ø | R6 | stdout match | resolver-not-observed | Impostor rejected (truncated content not accepted). **Pass** |
| I7 two documents | G1 doc, newline, G1 doc (text mode) | 0 | `e67ab29dadbdd98906774fc6f2bd2a442d16bda340d494ac37abaeedcf8ad246` | Ø | R7 | stdout match (**CRLF** variant, so Windows text-mode translation is confirmed) | resolver-not-observed | Impostor rejected. **Pass** |
| I8 leading output | `NOTICE: resolver starting\n` + G1 doc | 0 | Relayed: `b179b199abc6ccec8bce33a95a9f80a517d24c9d01862d1cd79b66b9afc0573` (63 hex, malformed). Stage-predicted: `b179b199abc6ccec8bce33a95a49f80a517d24c9d01862d1cd79b66b9afc0573` | Ø | R5 | Predicted equals relayed with the `4` at offset 26 restored | resolver-not-observed | Impostor rejected. **Pass**. Relay transcription discrepancy recorded (P3) |
| I9 trailing output | G1 doc + `\ntrailer` | 0 | `8f7d9576cb99fe7895a9cdd20ddaf6d677ee2d9a5a88f84a00d828a489a4bac3` | Ø | R7 | stdout match | resolver-not-observed | Impostor rejected. **Pass** |
| I10 status/document exit mismatch | G1 doc, process returns 1 | 1 | `116f55cc0c1c8b5b5f4c711c9772a7f4fdb44691ee94fd41a0833f1abf3da709` (= G1) | Ø | R9 | stdout match (identical bytes to G1) | resolver-not-observed | Impostor rejected. **Pass** |
| I11 shipment mismatch | doc `shipment_id: OTHER` | 0 | `bb45eb4a00a47fb545d2cd579b281bdedb96045cf8f4fd6daf4ebb1b8171b9b4` | Ø | R10 | stdout match | resolver-not-observed | Impostor rejected. **Pass** |
| I12a schema-invalid: READY with exit 2 | HARNESS_READY / NO_SURFACES_REQUIRED / 2, process 2 | 2 | `a142d038efc0701c83ff1861f68486f2f828330260e9ee84407cb715de26ddbf` | Ø | R8 | stdout match | resolver-not-observed | Impostor rejected by the document, although status 2 is a legal status. **Pass** |
| I12b schema-invalid: UNRESOLVED wrong reason | UNRESOLVED / ALL_SURFACES_PRESENT / 2, process 2 | 2 | `1b7ef5f7b39a61791129516f750b9bb7e3679651d6d9994657c4a882a524860c` | Ø | R8 | stdout match | resolver-not-observed | Impostor rejected by the document. **Pass** |
| I12c schema-invalid: missing `inputs_sha256` | G1 doc without the key | 0 | `b16e6e4c3e765979d5b37ec09f18d4edc2ffc9052472cb5122e0e875293ad8f0` | Ø | R8 | stdout match | resolver-not-observed | Impostor rejected (missing content not accepted). **Pass** |
| X1 invalid UTF-8 | byte `0xFF` | 0 | `a8100ae6aa1940d0b663bb31cd466142ebbdbd5187131b92d93818987832eb89` | Ø | R4 | stdout match | resolver-not-observed | Extra impostor rejected. **Pass** |
| X2 JSON scalar | `true` | 0 | `b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b` | Ø | R8 (sketch: R5, R8 secondary) | stdout match | resolver-not-observed | Extra impostor rejected. **Pass**. Sub-code difference is non-binding (see Adjudication) |
| X3 valid JSON plus stderr | G1 doc + stderr `diagnostic\n` (text mode) | 0 | `116f55cc0c1c8b5b5f4c711c9772a7f4fdb44691ee94fd41a0833f1abf3da709` (= G1) | `e99c2db6865fb97b3f1f8fb6e78a33109251200cc4fad899488b6a6bdf5c8883` | R2 | stdout match; stderr match (**CRLF** variant) | resolver-not-observed | Channel-rule case rejected. **Pass** |
| X4 duplicate key | G1 doc with a repeated `schema_version` | 0 | `318be7735e486b3e97d2339adc7909eb92d7f056131f98c428ab37f9c779faa5` | Ø | R6 | stdout match | resolver-not-observed | Extra impostor rejected. **Pass** |
| N1 status out of domain | G1 doc, process returns 3 | 3 | `116f55cc0c1c8b5b5f4c711c9772a7f4fdb44691ee94fd41a0833f1abf3da709` (= G1) | Ø | R1 | stdout match | resolver-not-observed | Extra impostor rejected. **Pass** |
| R0 timeout | sleep 31s against a 30s timeout | none | Ø | Ø | R0 | match | resolver-not-observed | Hang/crash-class impostor rejected. **Pass** |

Totals:

* 5 of 5 genuine verdicts accepted.
* 20 of 20 impostors rejected. Every charter-listed impostor class is covered:
  * startup failure (I1), unknown command (I2), argparse usage error (I3) and
    help text (I4);
  * empty stdout (I5) and malformed JSON (I6);
  * two documents (I7), leading output (I8) and trailing output (I9);
  * status-to-document exit mismatch (I10) and shipment mismatch (I11);
  * schema-invalid document (I12a to I12c).

  The run also covered six extra classes: X1 to X4, N1 and R0.
* Stage independently reproduced these hashes: 19 stdout values exactly (G1 to
  G5, I5 to I7, I9 to I12c, X1 to X4, N1, R0), plus the X3 stderr value. I8
  was reproduced subject to the transcription note. Not reproduced: I4 stdout
  and I1 to I3 stderr.

## Adjudication of the Stage-Sketch Differences (I4, X2)

**What differs.** Stage's earlier read-only predicate sketch, as quoted in the
dispatch, had the rule `R5 LEADING_OUTPUT if not text.startswith('{')`, with
I4 help expected as R5 and X2 scalar expected as R5 (R8 secondary). Ship's
verifier narrows R5 to "leading output before an object". It fires only when:

* JSON parsing succeeds and the text starts with whitespace; or
* parsing fails and the text starts with whitespace or contains a `{` after
  offset 0.

Anything else that does not start with `{` is either R6 (parse failure) or R8
(valid JSON whose root is not an object). As a result:

* I4 (argparse help, no `{`, not JSON) is R6;
* X2 (`true`, valid JSON, root not an object) is R8.

Reading `classify()` confirms that both labels follow deterministically from
the code.

**Why the differences are non-binding:**

1. Charter section 6.4 and `PE-INTERFACE-02` score only the binary outcome:
   every impostor yields `resolver-not-observed`, and every genuine verdict is
   accepted. I4 and X2 are rejected under both labelings. No outcome flips.
2. No charter section, matrix row or committed decision defines rejection
   sub-codes or their precedence. A read-only search of `docs/` finds
   `resolver-not-observed` only in the charter and no `LEADING_OUTPUT` token
   anywhere. The Stage sketch was never ratified and never committed. It was
   diagnostic reasoning, not a normative contract.
3. Ship's refinement is also the more precise diagnostic. The sketch's rule
   would label non-JSON text and a non-object JSON root as "leading output",
   though neither has any leading bytes before an object. Stage's sketch
   remains an equally valid rejection policy, but it is not preferred.

**The self-score caveat stands.** Ship's "25/25" compares observed labels with
Ship's own expected labels, and those expected labels differ from Stage's
sketch on I4 and X2. The 25/25 figure is therefore **not** evidence that
Stage's planned sub-code matrix matched exactly. Stage does not rely on it.
This verdict rests on Stage's own per-row evaluation above, against the
charter's binary criterion, with outcomes traced through the verifier source
and confirmed by the reproduced hashes.

**Conclusion.** No charter row fails. The differences are recorded as change
request CR-B1. They are not a FAIL, and they start no proof-fix loop.

## Discrimination Analysis (section 6.4 fail criterion 3)

* **Process status alone cannot discriminate:**
  * status 0 occurs in 14 cases: 2 accepted (G1, G2) and 12 rejected (I4 to
    I9, I11, I12c, X1 to X4);
  * status 1 occurs in 3 cases: 1 accepted (G3) and 2 rejected (I1, I10);
  * status 2 occurs in 6 cases: 2 accepted (G4, G5) and 4 rejected (I2, I3,
    I12a, I12b).

  No status value predicts acceptance.
* **The document discriminates independently of status.** I12a and I12b carry
  a legal status (2) that equals the document's own `exit_code`, yet they are
  rejected. The candidate schema's `oneOf` binds `state`, `exit_code` and
  `reason_code` together inside the document, so an internally inconsistent
  document fails validation whatever the process status is.
* **Both channels are required, and the binding is to the actual process
  status.** G1, I10, X3 and N1 emit byte-identical stdout (the same SHA-256).
  Only G1 is accepted. I10 fails on status/document exit mismatch, X3 on a
  non-empty stderr, and N1 on a status outside `{0,1,2}`.
* **Shipment binding.** I11 is rejected after schema validation, because the
  document's `shipment_id` does not equal the requested shipment.

## Channel Rule (fixed by this proof)

| Channel | Rule |
|---|---|
| Process status | Must be in `{0,1,2}`. Anything else, including Windows NTSTATUS-style crash codes, is rejected (R1). A timeout is rejected (R0) whatever was captured |
| stderr | **Must be empty. Any stderr byte means `resolver-not-observed` (R2), even alongside a valid document (X3).** This check runs before any stdout inspection |
| stdout | Must be non-empty (R3) and strict UTF-8 (R4). It must start with `{` (leading whitespace, BOM or banner is R5). Exactly one JSON object is allowed, with no duplicate keys and no `NaN`/`Infinity` constants (R6). The only trailing bytes allowed are one terminator: none, LF, or CRLF (R7). The root must be an object that validates against the candidate schema (R8), with document `exit_code` equal to the native status (R9) and `shipment_id` equal to the request (R10) |

Implications recorded for later phases (not proven here):

* A production resolver in `--json` mode must write nothing to stderr on a
  genuine verdict. Interpreter warnings or logging would therefore turn a
  genuine verdict into `resolver-not-observed`, which fails closed.
* On Windows, text-mode writes translate LF to CRLF. I7 and X3 confirm this
  empirically. The rule accepts one trailing CRLF for that reason.

## Rejection Precedence (as implemented in the disposable predicate; candidate only)

R1 status domain, then R2 stderr, then R3 empty, then R4 UTF-8, then the
non-`{` branch (R5 / R6 / R8), then R6 malformed or duplicate key, then R7
trailing bytes, then R8 non-object or schema, then R9 exit mismatch, then R10
shipment mismatch. The case outputs show the ordering matters in several
places:

* X3 and N1 carry a G1-valid document but stop at R2 and R1;
* I12a stops at R8 before R9 could fire;
* I10 reaches R9 only after the schema passes.

This precedence and the R0 to R10 sub-code set are **not** a finalized
taxonomy (CR-B1).

## Edge-Case Analysis (read-only, untested)

Stage derived these from reading the verifier source and the installed
jsonschema 4.26.0 source. **None was executed.** None is a charter-listed
impostor, and none changes this verdict. Each is recorded as a change request
for the implementation matrix.

1. **Float-form `exit_code` is accepted (CR-B3).** jsonschema Draft 6 and later
   (including 2020-12) treats integral floats as `integer`
   (`_types.py:195-199`), and `const` equality evaluates `0 == 0.0` as true
   (`_utils.py:equal` via `unbool`). The Python comparison
   `document["exit_code"] != returncode` also treats `0.0` as equal to `0`. A
   document otherwise identical to G1 but carrying `"exit_code":0.0` or `1e0`
   would therefore be accepted. This is a numeric-form looseness in the
   candidate schema, not missing or truncated content. It should be closed by
   requiring a JSON integer token (for example, a `parse_float` rejection or an
   exact `int` type check).
2. **Deep nesting is not a closed rejection (CR-B4).** `json.loads` and
   `raw_decode` raise `RecursionError` on pathologically nested input.
   `RecursionError` is not a `ValueError`, so it escapes `classify()` and the
   verifier would crash (fail closed, non-zero, never "accept") instead of
   returning a closed code. stdout is also captured without a size bound. The
   production predicate must be total: catch recursion and memory exhaustion,
   bound the captured bytes, and map both to a closed rejection.
3. **Leading whitespace or a UTF-8 BOM** (`\ufeff{...}`) is rejected as R5,
   derived by reading the code paths. It was not in the executed case set.
4. **Nested duplicate keys** are rejected (R6), because the
   `object_pairs_hook` applies at every object level. Only the top-level
   duplicate was executed (X4).
5. **The literal token is not emitted (CR-B2).** The predicate represents
   rejection as `accepted=False` plus a sub-code. It does not return the
   literal string `resolver-not-observed`. For proof entry, Stage treats
   `accepted=False` as `resolver-not-observed`. A production consumer should
   emit the literal closed outcome token, with the sub-code as a secondary
   field.
6. **Diagnostic text.** For schema errors, `error` reports the first yielded
   validation error, whose order is not a stable priority. It is diagnostic
   only and does not affect the outcome.

## Scope of the Candidate Schema (not finalized)

The schema is embedded in `proof_b_verify.py` and is **Proof-B-local**. It is
not Proof C's schema, because Proof C has not produced one (the section 6.1
combination option to reuse C's schema was not used). Its state and
reason-code enums are illustrative. `surfaces`, `declarations` and
`diagnostics` are untyped arrays, and `backlog_root` accepts any string.

Proof B shows that a predicate of this shape (a strict single-object channel
rule, `additionalProperties: false`, and a `oneOf` binding of state, exit code
and reason inside the document, cross-checked against native status and the
requested shipment) discriminates genuine verdicts from impostors. That
property carries over to the final schema only if the final schema keeps the
in-document binding and strictness. Proof C's truth table remains the
authority for reason codes. Nothing here pre-judges Proof C.

## Change Requests (charter section 3: not PE-1.3 rows, not blockers)

| ID | Request |
|---|---|
| CR-B1 | Ratify the consumer rejection sub-code taxonomy and precedence in the implementation matrix, choosing between the Ship refinement and the Stage sketch for R5, R6 and R8 labeling |
| CR-B2 | The production consumer emits the literal outcome `resolver-not-observed` with a sub-code |
| CR-B3 | Reject non-integer JSON number tokens for `exit_code` |
| CR-B4 | Make the predicate total: handle `RecursionError` and memory exhaustion, and bound stdout and stderr capture |
| CR-B5 | Carry the stderr-empty channel rule into the production resolver's `--json` output contract, or re-charter it explicitly |

## Time and File Bounds

| Component | Time | Basis |
|---|---|---|
| Earlier Stage read-only analysis (agent `329072c1-9e57-4c92-9168-a3ec6f73e43d`) | about 8m active | Operator dispatch estimate |
| First Ship attempt | about 2m56s active | Operator dispatch estimate |
| Second (stopped) Ship attempt | 1 to 2m (upper 2m used) | Operator dispatch estimate |
| Ship execution invocation (three full runs, including the final 34.562s run) | about 10m36s | Ship report |
| This Stage authoring session | Started 11:48:52-07:00. Upper bound 25m to this artifact's commit (the commit timestamp is the durable record) | Measured |
| **Cumulative active total** | **Upper bound about 48.5m** (the dispatch estimate of about 21.5m before authoring, plus at most 25m authoring, rounded up) | Within 60m |

**Idle gap, reported separately and conservatively.** Stage cannot determine
the wall-clock interval between the earlier Stage analysis and the Ship
attempts, the gaps between attempts, or the wall-clock start of the earliest
Stage work. None of these is claimed. Known wall-clock anchors:

* setup commit `d20820ec` at 11:33:50-07:00;
* scratch path recorded as `B-20260924-114058` (11:40:58);
* scratch directory and files created at 11:41:59;
* final stub write at 11:43:57;
* this dispatch at 11:48:52.

The time verdict rests on active-time accounting, which is how the charter
states the bound ("covers its Stage analysis and its Ship execution together")
and how the 2-hour effort rule is framed. **If the operator rules that the
bound is wall-clock including idle gaps, the time row must be re-evaluated. It
cannot be shown met or exceeded from the evidence Stage holds.**

**File bound.** 2 of 2 disposable files. Met.

## Separate Issue: PE-ACTIVATE-01 (not part of this verdict)

Setup commit `d20820ec` ("chore: permit Ship to use ignored verification
scripts", approved per the dispatch) changes three files that
`PE-ACTIVATE-01` compares against the raw blobs at snapshot `5bcb00e5`:

* `.autoharness/harness-manifest.yaml`;
* `.github/agents/_ship.agent.md`;
* `templates/agents/_ship.agent.md.tmpl`.

It also changes `.gitignore`. The row's comparator therefore no longer matches
as written. This finding is also relevant to the `PE-AUTH-01` commit-scope
audit at proof exit. It is a **separate, required Stage change-control issue
before proof exit** (for example, a charter-recorded rebaseline or an
operator-recorded exception). It is not resolved, waived or decided here, and
it does not affect the Proof B verdict.

## Non-Claims

* No production resolver, and no `backlogit harness resolve` command, was
  exercised or proven. The stub's `prog="backlogit"` is a stand-in only.
* The candidate schema and the R0 to R10 sub-codes are not a finalized
  taxonomy or contract.
* Scratch results are not P-004 gate evidence, and grant no claim,
  publication or `harness-ready` authority (`PE-ACTIVATE-03`, `PE-AUTH-03`).
* No race, TOCTOU or hardlink-alias resistance is claimed (`PE-SAFETY-06`).
* Cross-platform behavior is not claimed. The evidence is Windows only.

## Recommendation

**Conclusion**: proceed. Record Proof B as `PASS` for the proof-exit report.

**Confidence**: medium. Confidence in the binary discrimination property is
high: it was executed and hash-corroborated. Overall confidence is medium
because of four recorded caveats:

* time accounting rests on active time;
* one relayed hash has a transcription defect;
* the verifier's expected labels were Ship-chosen;
* edge cases CR-B3 and CR-B4 are untested.

## Next Steps

1. Carry this verdict and CR-B1 to CR-B5 into the proof-exit report and the
   draft implementation matrix (charter section 8). No harvest, plan or
   backlog item follows from this artifact.
2. Stage opens the separate `PE-ACTIVATE-01` change-control item for
   `d20820ec` before proof exit.
3. Scratch cleanup requires handoff or operator approval. The directory stays
   in place until then.

## References

* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md`,
  version 1.3 (sections 6.1, 6.2 and 6.4; rows `PE-INTERFACE-02`,
  `PE-SAFETY-05`, `PE-EVIDENCE-01`, `PE-EVIDENCE-05`, `PE-ACTIVATE-01`)
* Spike skill: `.github/skills/spike/SKILL.md`
* Precedent formats: `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md`,
  `docs/decisions/2026-09-24-ship-activation-proof-e-run3-spike.md`
* Library source read: `.venv/Lib/site-packages/jsonschema/_types.py` and
  `_utils.py` (jsonschema 4.26.0)
