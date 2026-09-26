---
title: "Proof B run 2 (PE-1.4) - CLI authenticity: findings (BLOCKED, evidence contract incomplete; behavior not disproven)"
source: "docs/decisions/2026-09-24-cli-authenticity-proof-b-run2-spike.md"
doc_type: decision
description: "Stage-authored formal adjudication of Proof B run 2 under charter PE-1.4 section 6.4 (unchanged from PE-1.3) and the PE-1.4 section 6.1 evidence handoff. In the one current worktree at HEAD 4d132bf9, Ship ran the byte-identical Proof B disposable stub (4872 B, 84ce8654...2165f) and verifier (10928 B, 193cba3f...e095) from a new ignored scratch directory, .proof-scratch/B-run2-20260924-162527/. Stage re-hashed both read-only and they match the PE-1.3 run 1 files. Ship ran the verifier unchanged inside an in-memory runpy.run_path capture wrapper that intercepted subprocess.run only to log metrics, under Python 3.14.3 on Windows 11 build 26200 and NTFS. It reported a same-invocation cache-only backlogit sync (exit 0, stdout 23 B cf46e51c...e873, stderr 0 B), 24 child exits plus one bounded timeout, and 25 of 25 verifier cases where the expected label equalled the observed label (5 genuine accepted, 20 impostors rejected). It relayed one full child stdout SHA-256 (I8, b179b199...0573, which equals the value Stage predicted in PE-1.3) and an in-memory capture manifest SHA-256 (cd860c1e...b43). Nothing observed contradicts the section 6.4 pass criterion, and no FAIL disjunct is shown. The verdict is still BLOCKED, not PASS, because mandatory PE-EVIDENCE-01 / section 6.1 evidence for this invocation is missing. First, native status and stdout and stderr SHA-256 per child invocation: only I8 stdout was relayed, although the verifier computes all three fields per case. Second, the parent execution record: the verbatim wrapper launch, the wrapper's native exit status, and the length and SHA-256 of its stdout and stderr and of the verifier's own output. Third, the wrapper's source or hash, so pass-through integrity is Ship-attested only. Fourth, the pre-refresh .backlogit ignored inventory, so the refresh footprint half of the safety statement is incomplete. Stage predictions from PE-1.3 cannot substitute: PE-EVIDENCE-01 fields must come from Ship's reported evidence, and the I1-I3 stderr and I4 stdout depend on the interpreter (3.12.10 then, 3.14.3 now). The PE-1.3 run 1 PASS stands as recorded and still does not satisfy PE-1.4 proof exit. No plan, charter or backlog edit. No claim authority."
docline:
  type: spike
  date: 2026-09-24
  time_box: "60m"
  conclusion: "blocked"
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
proof_run: 2
proof_verdict: BLOCKED
proof_verdict_basis: "PE-EVIDENCE-01 / section 6.1 evidence handoff incomplete for this invocation (gaps G1-G4); behavior not disproven; no FAIL disjunct shown"
proof_verdict_scope: disposable-stub-and-predicate-only
behavior_disproven: false
production_resolver_exercised: false
candidate_schema_status: proof-b-local-candidate-not-finalized
prior_run_artifacts:
  - {run: 1, path: docs/decisions/2026-09-24-cli-authenticity-proof-b-spike.md, commit: 83525c62, verdict: PASS, matrix: PE-1.3, pe_1_4_status: "historical PASS; does not satisfy PE-1.4 proof exit (section 3.3)"}
prior_run_verdicts_changed: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.4"
matrix_id: PE-1.4
charter_sections: ["3.3", "6.1", "6.4"]
matrix_rows: [PE-INTERFACE-02, PE-SAFETY-05]
evidence_rows_assessed: [PE-EVIDENCE-01, PE-EVIDENCE-05, PE-AUTH-01, PE-AUTH-02, PE-ACTIVATE-01]
scratch_path: "C:\\Source\\GitHub\\autoharness\\.proof-scratch\\B-run2-20260924-162527\\"
fixture_files:
  - {name: proof_b_stub.py, bytes: 4872, sha256: 84ce86549fcd2672cf9ad3b412909c428a545ed89d49cf3db38d26da94a2165f, stage_verified: true, identical_to_run_1: true}
  - {name: proof_b_verify.py, bytes: 10928, sha256: 193cba3fa0cb61b5988bba0c05041003dcdc9d5474b02e8e1b00a45af339e095, stage_verified: true, identical_to_run_1: true}
host: {os: "Windows 11 build 26200", filesystem: NTFS, interpreter: "Python 3.14.3 (C:\\Python\\Python314\\python.exe)", jsonschema: "not relayed by Ship; Stage observed jsonschema-4.26.0.dist-info in that interpreter's site-packages (corroboration only)"}
cases_total: 25
cases_reported_expected_equals_observed: 25
cases_genuine_accepted_reported: 5
cases_impostor_rejected_reported: 20
per_case_output_digests_relayed: "I8 stdout only"
evidence_gaps: [G1-per-child-status-and-stream-digests, G2-parent-execution-record, G3-wrapper-source-or-hash, G4-pre-refresh-ignored-inventory]
branch: chore/stage-176-s-workflow-defects
head_at_ship_execution: 4d132bf9
head_at_authoring: 4d132bf9
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: "queued, 17 members, unclaimed (Ship-reported; not re-read by Stage)"
shipment_claim_ready: false
publication_eligible: false
backlog_item_created: false
plan_changed: false
charter_changed: false
reopened_decision: "none (BLOCKED routes to the operator, not to architecture or charter)"
blocked_route: operator
time_bound_status: met
file_bound_status: "met (2 disposable files; the capture wrapper was in-memory and wrote no file)"
tool_spool_status: "Ship-reported automatic tool-wrapper spool of an ignored-status listing outside cwd; Stage interpretation as in Proof A run 5 (not agent-directed, not raw proof output); disclosed; not an operator sign-off"
scratch_cleanup_status: "retained; Stage deleted nothing"
stage_model_route: "claude-opus-5.5/anthropic/high requested; unverified by Stage (route not self-verifiable)"
---

# Proof B run 2 findings (PE-1.4): CLI authenticity

## Verdict

| Field | Value |
|---|---|
| Proof | B, CLI authenticity ([charter](2026-09-23-lifecycle-proof-entry-charter.md) section 6.4, unchanged by PE-1.4) |
| Run | 2, scratch `.proof-scratch/B-run2-20260924-162527/`. This is the new admissible-run attempt that section 3.3 requires for B |
| Verdict | **`BLOCKED`**. It is not `PASS` and not `FAIL` |
| Why not `FAIL` | No impostor was reported accepted, no genuine verdict was reported rejected, and the predicate's discrimination does not rest on status alone (see Criterion Assessment). The behavior is **not disproven** |
| Why not `PASS` | Mandatory `PE-EVIDENCE-01` and section 6.1 evidence-handoff fields for **this** invocation are missing (gaps G1 to G4 below). `PE-EVIDENCE-01` is `P1` and `not-deferrable`. Its fields must be "taken from Ship's reported evidence", and Stage may not supply them by prediction |
| `PE-INTERFACE-02`, `PE-SAFETY-05` (Proof B half) | **Not satisfied at PE-1.4 proof exit by this run.** Every relayed observation is consistent with them |
| Run 1 (PE-1.3) | `PASS` at `83525c62` stands as recorded and is not re-labelled. Under section 3.3 it still does not satisfy PE-1.4 proof exit |
| Route | Operator (section 6.1 `BLOCKED` routing). See Closure Routes |
| Authority | None. No claim, publication, P-004 red or `harness-ready` authority. `187-S` stays `queued` |

**Reading of `BLOCKED`.** Section 6.1 defines `BLOCKED` as "could not be
executed under this section". Stage reads an execution whose section 6.1
evidence handoff is incomplete as not yet shown to have run *under this
section*. That follows the Proof C run 2 precedent ("admissibility not
established") and the operator's instruction for this session. It is Stage's
reading. It is not an operator sign-off.

## Evidence Gaps (precise)

| ID | Gap | Charter source | Closable without re-execution? |
|---|---|---|---|
| **G1** | **Per-child records.** Ship reported "24 child exits and one bounded timeout". It did not itemize each child's native status, and it did not report the stdout SHA-256 for 24 of the 25 cases (every case except I8) or the stderr SHA-256 for any case. The verifier computes exactly these fields for every case (`native_status`, `stdout_sha256` and `stderr_sha256` in `run_case`, printed one JSON line per case), so they existed in that process | `PE-EVIDENCE-01` ("raw outputs or their SHA-256"); section 6.1 evidence handoff ("stdout, stderr and exit status (raw, or by SHA-256 when large)") | Yes, if Ship's existing handoff or capture still holds the 25 verifier case lines. Ship transcribes them, and Stage records them as an addendum |
| **G2** | **Parent execution record.** Missing: the verbatim launch of the capture wrapper (its code or command line); the wrapper's native exit status; the byte length and SHA-256 of the wrapper's stdout and stderr; and the byte length and SHA-256 of the verifier's own output (25 case lines plus the summary line, which also carries `python`, `jsonschema`, `elapsed_seconds` and `timeout_seconds`). The capture manifest SHA-256 `cd860c1e...b43` was relayed, but not its content or format. Stage therefore cannot tell what it covers, and cannot verify it | `PE-EVIDENCE-01` ("exact commands", "raw outputs or their SHA-256"); section 6.1 ("each bounded command verbatim") | Yes, if it was retained. Otherwise no |
| **G3** | **Wrapper integrity.** The wrapper replaced `subprocess.run` in the verifier's runtime. Its source and hash are not recorded. Ship attests that it logged metrics and returned the original outputs unchanged, but Stage cannot check that (see Proxy-Wrapper Integrity) | `PE-EVIDENCE-01` ("exact commands"); compound lesson on wrapper exit-status masking | Yes, if the wrapper code is transcribed verbatim with its hash. Otherwise no |
| **G4** | **Pre-refresh `.backlogit` ignored inventory.** Ship did not capture it before `backlogit sync`. Its before and after snapshots bracket the fixture phase only. So the safety statement cannot show that the refresh changed only the tool-managed cache paths. Other ignored `.backlogit` writes would have to be "recorded by name". Proof A run 5 recorded this footprint | Section 6.1 refresh Scope bullet and safety statement; `PE-AUTH-01` evidence column | **No.** It was a point-in-time state. It needs an operator ruling or a fresh run |

**Why Stage predictions cannot fill G1.** In PE-1.3, Stage reproduced 19
stdout hashes and one stderr hash by hashing the bytes it predicted from the
stub source. Those checks corroborated values that **Ship had reported**. They
never replaced them. Three things rule out reusing them now:

* `PE-EVIDENCE-01` requires the fields to be "taken from Ship's reported
  evidence".
* Section 3.3 requires each run to stand on its own evidence from that same
  invocation. For the refresh it says outright that "a missing refresh cannot
  be supplied afterwards".
* The I1 to I3 stderr and the I4 stdout come from interpreter and argparse
  text. That text was Python 3.12.10 in run 1 and is Python 3.14.3 now, so
  those four streams are not predictable at all.

Stage records no predicted hash as evidence for this run.

**Not grounds (disclosed):**

* The refresh excerpt was not relayed. Only the length and SHA-256 were. That
  matches the accepted Proof A run 5 record.
* Per-case elapsed times were not relayed. The overall Ship elapsed time was.
* The tool wrapper automatically spooled an ignored-status listing outside the
  current working directory. See Tool-Wrapper Spool.

## Goal

Charter section 6.4: can Ship distinguish a real resolver verdict from a crash
or impostor output, using process status plus exactly one schema-valid
document?

## Success Criteria (charter section 6.4, verbatim in substance)

* **Pass.** The predicate accepts only a single schema-valid JSON document on
  stdout whose requested shipment, state, reason code and exit code all match
  the request and the process status. It returns `resolver-not-observed` for
  every impostor, which means all of these:
  * startup failure, unknown command, argparse usage error and help text;
  * empty stdout and malformed JSON;
  * two documents, and leading or trailing output;
  * a status-to-document exit mismatch, a shipment mismatch and a
    schema-invalid document.

  The proof fixes and records the channel rule for stderr.
* **Fail.** Any impostor is accepted, any genuine verdict is rejected, or the
  schema cannot discriminate without relying on status alone.
* **PE-1.4 admissibility (section 6.1, section 3.3).** The run needs:
  * a same-invocation refresh before P-001;
  * bounded projections;
  * the `PE-ACTIVATE-01` blob check before the first write;
  * the full evidence handoff and safety statement (`PE-EVIDENCE-01`,
    `PE-AUTH-01`, `PE-AUTH-02`).

## Scope Constraints and Stage Actions

* **Read first.** Compound entries:
  * `2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`: a
    wrapper can discard a correctly propagated status while still forwarding
    output;
  * `2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`: a
    timeout is not a clean signal;
  * `2026-07-01-subprocess-validation-gating.md`: argv arrays and
    `shell=False`.

  Stage then read the run 1 artifact, charter sections 3.3, 6.1, 6.2, 6.4 and
  7, the Proof A run 5 and Proof C run 2 precedent artifacts, and both
  scratch scripts.
* **Read-only commands only:**
  * `git status`, `git log`, `git worktree list --porcelain` and
    `git rev-parse HEAD:<path>`;
  * recursive `-Force` listings and `Get-FileHash` over the run 1 and run 2
    scratch directories;
  * `git check-ignore`;
  * a directory listing of the interpreter's `site-packages`;
  * one `backlogit_get_version` probe with the update check skipped.
* **Stage executed nothing.** It ran no fixture, verifier, stub, test, build,
  lint, index sync or backlog mutation. It made no scratch cleanup and no
  plan, charter or backlog edit. Its only write is this file, committed
  normally (no amend, push or PR).

## Session and Tool State (`PE-EVIDENCE-05`)

| Surface | State | Note |
|---|---|---|
| backlogit | `TOOL_OK` | `backlogit_get_version` (`no_update_check: true`) returned `1.10.1-0.20260823032255-b07729386a31+dirty` |
| Index sync (Stage Step 0.1) | Skipped by operator scope | The operator forbade Stage index sync. Section 6.1 assigns the refresh to Ship alone. Stage made no semantic backlog read |
| agent-engram | `ENGRAM_DEGRADED` | Instruction file present, but no engram tool on this session's surface. Bounded file reads were used instead |
| agent-intercom | `INTERCOM_DEGRADED` | Instruction file present, but no intercom tool on this session's surface. No broadcast was made. No destructive or approval-dependent action was taken |
| graphtor-docs | `GRAPHTOR_UNAVAILABLE` | Instruction file present, but no server tool on this session's surface. Direct file reads were used instead |
| Checkpoint recovery (Stage) | Not run | Session scoped to findings only. Ship reported the unfiltered scan |
| Git at authoring | Tracked tree clean | Branch `chore/stage-176-s-workflow-defects`, HEAD `4d132bf98e33c9c58dc7b66a3315c862fd55659c`, exactly one worktree |

## Ship Invocation Record (as relayed to Stage)

| Item | Relayed value |
|---|---|
| Index refresh | Same invocation, cache-only `backlogit sync`, native exit 0. stdout 23 B, SHA-256 `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873`. stderr 0 B. The transport is the CLI, and whether the MCP call was attempted first was not relayed. The same 23-byte digest appears in the Proof A run 5 refresh record |
| Checkpoint scan | Unfiltered, 71 total: 70 resolved and 1 abandoned (`valid: true` by official get). 0 quarantined, 0 active |
| P-001 (after refresh) | Active shipments, tasks, features and chores: 0. `173-S` closure READY, compaction done |
| P-002 | No claim and no `harness-ready` consumption |
| P-010 | Scratch writes only |
| P-011 / P-016 | Single clean branch, HEAD `4d132bf9`. One worktree |
| `PE-ACTIVATE-01` (before the first write) | The three blobs match `4acba14a` |
| `187-S` | `queued`, 17 members, unclaimed |
| Fixture | New ignored scratch with two scripts, byte-identical to run 1 (hashes above) |
| Execution | The verifier ran unchanged via an in-memory `runpy.run_path` capture wrapper. The wrapper intercepted `subprocess.run` only to log metrics, returning the original outputs unchanged (Ship attestation) |
| Child command | `C:\Python\Python314\python.exe -B -m proof_b_stub harness resolve --workspace . --shipment REQ --json`, cwd = repository root. I2 to I4 alter the argv exactly as in the verifier's `CASES` |
| Child env | `PYTHONPATH` = new scratch path (removed for I1), `PYTHONDONTWRITEBYTECODE=1`, and `PROOF_B_MODE` per case (from verifier source) |
| Outcomes | 24 child exits plus 1 bounded timeout. 25 of 25 cases had expected label = observed label: 5 genuine accepted, 20 impostors rejected. Case IDs and results are in Ship's handoff |
| Child digests | I8 stdout: `b179b199abc6ccec8bce33a95a49f80a517d24c9d01862d1cd79b66b9afc0573`. **No other per-case digest was relayed** |
| Capture manifest | SHA-256 `cd860c1e77d23ff643722c6b05abcbde181b91525f037aa7df166a149ad31b43`. Content and format not relayed |
| Host | Windows 11 build 26200, NTFS, Python 3.14.3 |
| Elapsed | Ship 7m30s |
| Safety | Tracked status clean. `.backlogit` ignored snapshot identical across the fixture phase. Pre-refresh ignored inventory **not captured** (G4) |
| Spool | The tool wrapper automatically spooled an ignored-status listing outside the current working directory. Ship states it was not raw proof output and not a Ship-directed write |

## Stage Read-Only Corroboration (not Ship evidence)

| Check | Result |
|---|---|
| Run 2 fixture hashes and sizes | `proof_b_stub.py` 4872 B `84ce8654...2165f`. `proof_b_verify.py` 10928 B `193cba3f...e095`. **Both match Ship and the run 1 files.** The run 1 scratch (`B-20260924-114058`) still holds files with the same two hashes |
| Scratch contents | A recursive `-Force` listing shows exactly two files and no `__pycache__`. Both files show CreationTime and LastWriteTime 16:25:38, so neither was edited after creation. Metadata is corroboration only |
| Ignore status | `.gitignore:10:.proof-scratch/` covers the run 2 path |
| `PE-ACTIVATE-01` at HEAD | `4ccd7fdc...`, `e22916b6...` and `251f46e8...` for the template, mirror and manifest, equal to the `4acba14a` blobs. `git status --porcelain` is empty for the three paths |
| Worktrees | Exactly one |
| Relayed digests | All three relayed digests (refresh, I8 and manifest) are 64 lowercase hex digits |
| I8 digest | Equals the 64-digit value Stage predicted from the stub source in run 1. That closes run 1's 63-digit transcription discrepancy as corroboration. It is not a substitute for G1 |
| jsonschema in the child's interpreter | `C:\Python\Python314\Lib\site-packages\jsonschema-4.26.0.dist-info` exists, which is the same version as run 1. Ship did not relay the verifier's summary-line `jsonschema` value (part of G2) |

## Criterion Assessment (behavior; conditional on Ship's report and wrapper pass-through)

Each observed label is a **logical consequence** of the unchanged
`classify()` source, because the checks run in a fixed order. The table
states what each reported label *implies* about the child's native status and
streams. It is not a set of invented digests.

| Case | Stub behavior (source) | Reported label | What the label implies (from `classify()`) |
|---|---|---|---|
| G1 to G5 | Genuine documents: READY/0 with no terminator, READY/0 with LF, NO_HARNESS/1 with CRLF, UNRESOLVED/2, UNRESOLVED/2 with LF | accept | rc is in `{0,1,2}` and equals the document `exit_code` (0, 0, 1, 2, 2). **stderr is empty.** stdout is strict UTF-8, one schema-valid object, shipment `REQ`, and at most one LF or CRLF terminator |
| I1 startup failure | `PYTHONPATH` removed, so `-m proof_b_stub` is not found from the repository-root cwd | R2 | rc is in `{0,1,2}` and stderr is non-empty |
| I2 unknown command / I3 usage error | argparse error | R2 | rc is in `{0,1,2}` and stderr is non-empty |
| I4 help text | argparse help on stdout | R6 | rc is in `{0,1,2}`, stderr is empty, and stdout is non-empty UTF-8 that does not start with `{`, is not JSON, and has no leading whitespace or later `{` |
| I5 empty | no output | R3 | stderr is empty and stdout is empty |
| I6 malformed | `{"schema_version":` | R6 | The document is truncated and **not accepted** |
| I7 two documents / I9 trailing output | two objects / object followed by `\ntrailer` | R7 | The bytes after the first object are not a single terminator |
| I8 leading output | `NOTICE: resolver starting\n` followed by a G1 document | R5 | The leading banner is rejected. The stdout digest was relayed (above) |
| I10 exit mismatch | G1 document, process returns 1 | R9 | The document is schema-valid, but rc (1 or 2) differs from the document's `exit_code` 0 |
| I11 shipment mismatch | `shipment_id: OTHER` | R10 | Every earlier check passed, and only the shipment binding rejected it |
| I12a, I12b, I12c | READY with exit 2 / UNRESOLVED with a READY reason / missing `inputs_sha256` | R8 | rc is legal (in `{0,1,2}`), yet the document fails the schema. **The missing field is not accepted** |
| X1 / X2 / X4 | byte `0xFF` / `true` / duplicate key | R4 / R8 / R6 | Each is rejected by the document channel |
| X3 valid JSON plus stderr | G1 document, then `diagnostic\n` on stderr | R2 | rc is in `{0,1,2}` and **stderr is non-empty. A valid document is refused on the stderr channel alone** |
| N1 status out of domain | G1 document, process returns 3 | R1 | rc is not in `{0,1,2}` |
| R0 timeout | sleeps 31 s against a 30 s timeout | R0 | `TimeoutExpired` reached the verifier, so the wrapper did not swallow it. The case is rejected whatever was captured |

**Pass criterion.**

* All five genuine verdicts are accepted.
* Every charter-listed impostor class is rejected: I1 to I4 for startup,
  unknown command, usage error and help text; I5 and I6 for empty stdout and
  malformed JSON; I7 to I9 for two documents and leading or trailing output;
  I10 and I11 for the exit and shipment mismatches; and I12a to I12c for
  schema-invalid documents.
* So are the six extra classes: X1 to X4, N1 and R0.

**Consistent with the criterion, but unevidenced for this run** (G1 to G3).

**No false positive.**

* The accept count is exactly 5, and those are the G cases.
* Every rejection path returns `accepted=False` before the final
  `return True`. There is no fall-through that accepts.
* A missing or truncated document (I6, I12c) is never accepted, which is the
  Proof B half of `PE-SAFETY-05`.
* Run 1 recorded two edge cases as untested change requests:
  * float-form `exit_code` would be accepted (CR-B3);
  * deeply nested input raises `RecursionError`, which escapes `classify()`
    and crashes the verifier non-zero (CR-B4).

  Neither is in the case set, neither changes this assessment, and both stay
  open.

**Status alone cannot discriminate (fail disjunct 3).** The labels alone prove
this, without any digest:

* G1, G3 and G4 are accepted, which fixes rc at 0, 1 and 2 respectively. So
  every legal status value has an accepted case.
* I12a and I12b are rejected (R8) with a legal rc, and I10 is rejected (R9)
  with a legal rc.
* So no status value predicts acceptance, and the in-document `oneOf` binding
  of state, exit code and reason decides the result.

**Stderr channel rule (unchanged from run 1).** Any stderr byte means
`resolver-not-observed` (R2). The check runs after the status-domain check
and before any stdout inspection. This run gives two pieces of evidence:

* X3 shows that a valid document is refused when stderr is non-empty.
* The five accepted G cases imply that stderr was empty under Python 3.14.3
  for genuine output. No interpreter warning turned a genuine verdict into a
  rejection.

CR-B5, which carries this rule into the production `--json` contract, stays
open.

**Timeout case.** R0 depends only on `TimeoutExpired` reaching the verifier.
It needs no captured bytes, so a hung child is rejected whatever partial
output it wrote. That is consistent with the compound lesson that a timeout is
not a clean signal. Ship reported exactly one bounded timeout, which matches
the single sleeping mode.

## Proxy-Wrapper Integrity

The verifier's source is unchanged: its hash matches. But it ran with a
replaced `subprocess.run`, and each verifier label is only as trustworthy as
that replacement. A wrapper could mask the native status, or alter or drop
streams, while the verifier still prints labels. This is the compound
exit-masking pattern.

What supports pass-through:

1. The logged I8 stdout digest equals the stub-source prediction.
2. All 25 labels match, and several of them need specific, different stream
   properties:
   * X3 needs non-empty stderr;
   * I10 needs rc 1 or 2 with stdout identical to G1;
   * N1 needs rc 3;
   * G3 needs a trailing CRLF to be tolerated;
   * R0 needs the exception to propagate.

   A wrapper that altered outputs would be unlikely to keep all 25 labels
   correct by accident.
3. The file bound holds, because the wrapper was never written as a file.

What is missing:

* The wrapper code and its hash.
* Its native exit status and output digests, which would show that the
  verifier returned exit 0 with a `PASS` summary.
* An independent digest of the verifier's stdout. The logged I8 digest is the
  wrapper's own observation, not independent evidence of what the verifier
  received.

Pass-through is therefore **Ship-attested and strongly corroborated, but not
evidenced** (G2, G3). Stage does not treat it as disproven.

## Comparison with Run 1 (PE-1.3, `PASS`)

| Aspect | Run 1 | Run 2 |
|---|---|---|
| Fixture bytes | `84ce8654...` / `193cba3f...` | Identical |
| Interpreter | Python 3.12.10 in `.venv` | Python 3.14.3 at `C:\Python\Python314` |
| Launch | Verifier launched directly. Parent exit 0, final run 34.562 s | Verifier launched in memory through a capture wrapper. Parent exit and digests not relayed |
| Refresh | None ("no index sync") | Same invocation, exit 0, digests relayed |
| Per-case digests | Relayed for all 25 cases, and Stage reproduced 19 stdout values plus X3 stderr | Only I8 stdout relayed |
| Outcome | 5 accepted, 20 rejected | 5 accepted, 20 rejected (reported) |
| Verdict | `PASS` (PE-1.3); does not satisfy PE-1.4 proof exit | `BLOCKED` (PE-1.4) |

The sub-code labels (R0 to R10) and the I4 and X2 differences from Stage's
earlier sketch are the same as in run 1. They remain non-binding (CR-B1).
Change requests CR-B1 to CR-B5 carry forward unchanged.

## Tool-Wrapper Spool

Ship reported one automatic tool-wrapper spool of an ignored-status listing
outside the current working directory. Stage applies the same interpretation
as Proof A run 5: the spool is host plumbing, not an agent-directed Ship
write, and not raw proof output. The Proof C run 2 precedent treated a similar
spool fail-closed. The operator may veto this reading.

**Disclosure:** during this Stage session, the wrapper also spooled one Stage
read-only output to OS Temp. It was a `Select-String` of charter headings and
row line numbers, and it held no proof output. This spool is not a ground for
this verdict.

## Per-Criterion Verdict

| Criterion or row | Status |
|---|---|
| Section 6.4 Pass: genuine verdicts accepted | Reported met (5/5). Per-case evidence incomplete (G1) |
| Section 6.4 Pass: every impostor gives `resolver-not-observed` | Reported met (20/20). Per-case evidence incomplete (G1) |
| Section 6.4: stderr channel rule fixed and recorded | Met (unchanged rule, recorded above) |
| Section 6.4 Fail disjuncts | None shown. Behavior not disproven |
| `PE-INTERFACE-02` (`P1`) | Not satisfied at proof exit by this run (`BLOCKED`) |
| `PE-SAFETY-05` (`P1`, Proof B half) | Not satisfied at proof exit by this run (`BLOCKED`). No missing or truncated content was accepted. Proof G holds the other half |
| `PE-EVIDENCE-01` (`P1`) | **Not met**: G1, G2 and G3 (missing digests, exit status and the verbatim parent command) and G4 (safety statement) |
| `PE-EVIDENCE-05` (`P2`) | Met (see Session and Tool State) |
| `PE-AUTH-01` | This commit changes only this `docs/decisions/*-spike.md` file. On Ship's side, the tracked tree was clean and there were scratch-only fixture writes. Whether the refresh touched only cache paths cannot be shown (G4) |
| `PE-AUTH-02` | Met on Ship's report: one worktree; same-invocation refresh with exit 0 and digests; P-001 read after the refresh with bounded active projections; P-002, P-010, P-011 and P-016 passed; checkpoint scan unfiltered with 0 anomalies and 0 active |
| `PE-ACTIVATE-01` | Blobs match `4acba14a` (Ship before the write; Stage at authoring). Final check is at proof exit |
| `PE-AUTH-03`, `PE-ACTIVATE-03`, `PE-SCOPE-04` | No authorization, claim, P-004 red, `harness-ready` or publication assertion |
| `PE-SCOPE-07` | Time met, and file bound met (2 files) |
| `PE-FLOW-04` | Not engaged. This run is `BLOCKED`, not `FAIL` |

## Time and File Bounds

| Bound | Charter | Recorded |
|---|---|---|
| Time (Stage plus Ship) | 60m | Ship took 7m30s. The scratch stamp is 16:25:27 -07:00, and files were created at 16:25:38. This Stage session started at 16:29:08 -07:00. The commit timestamp of this artifact is the durable end record, and it lands before 17:21. **Met.** No pooling with run 1 (section 3.3) |
| File (2 disposable) | 2 | 2 (`proof_b_stub.py`, `proof_b_verify.py`). The capture wrapper was in memory and wrote no file. **Met** |

## Closure Routes (operator decides; Stage authorizes nothing)

1. **Transcription addendum, no re-execution.** Ship may still hold these
   items in its existing handoff or capture:
   * the 25 verifier case lines and the summary line;
   * the wrapper's verbatim code or launch, its native exit status, and the
     length and SHA-256 of its stdout and stderr;
   * the capture manifest content.

   If it does, Stage can record them as an in-place addendum to this
   artifact, as done for Proof A run 5. That closes G1 to G3. **G4 is not
   closed by transcription.** The operator would rule whether Ship's
   post-refresh, post-fixture identity plus a clean tracked tree is enough
   for the refresh-footprint half of the safety statement.
2. **Fresh PE-1.4 run (run 3).** This means a new scratch directory and its
   own time bound. Ship would:
   * capture the pre-refresh `.backlogit` ignored inventory;
   * launch the verifier directly, as in run 1, so that its native exit and
     stdout and stderr digests are first-class, or else record the wrapper
     source and its hash;
   * relay every case line.

   Stage would then adjudicate afresh.

If neither route happens, run 2 stays `BLOCKED`. It is never converted into
`PASS`.

## Non-Claims

* No production resolver, and no `backlogit harness resolve` command, was
  exercised. The stub's `prog="backlogit"` is a stand-in only.
* The candidate schema and the R0 to R10 sub-codes are not finalized.
* Scratch results are not P-004 gate evidence, and grant no claim,
  publication or `harness-ready` authority.
* No race, TOCTOU or hardlink-alias resistance is claimed (`PE-SAFETY-06`).
* Windows only. No cross-platform claim is made.
* No digest in this artifact is Stage-predicted evidence for run 2.

## Recommendation

**Conclusion**: blocked (route to operator).
**Confidence**: medium.

The behavior matches run 1 on byte-identical fixtures under a newer
interpreter, and every relayed fact is consistent with `PASS`. But this
invocation's evidence handoff lacks mandatory per-command digests, exit
statuses and the verbatim parent command, and the refresh-footprint baseline
is missing. Proof B therefore has no admissible PE-1.4 `PASS` yet.

## References

* Charter: [2026-09-23-lifecycle-proof-entry-charter.md](2026-09-23-lifecycle-proof-entry-charter.md), sections 3.3, 6.1, 6.2, 6.4, 7.5, 7.6, 7.9 and 7.10
* Run 1 (PE-1.3, `PASS`): [2026-09-24-cli-authenticity-proof-b-spike.md](2026-09-24-cli-authenticity-proof-b-spike.md)
* Precedents: [2026-09-24-p004-red-runner-proof-a-run5-spike.md](2026-09-24-p004-red-runner-proof-a-run5-spike.md) (addendum and spool reading), [2026-09-24-surface-taxonomy-proof-c-run2-spike.md](2026-09-24-surface-taxonomy-proof-c-run2-spike.md) (`BLOCKED` on admissibility)
* Compound: `docs/compound/2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`, `docs/compound/2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md` and `docs/compound/2026-07-01-subprocess-validation-gating.md`
* Spike skill: `.github/skills/spike/SKILL.md`
