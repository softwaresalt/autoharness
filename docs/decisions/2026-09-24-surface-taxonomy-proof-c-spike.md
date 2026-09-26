---
title: "Proof C - one-entry SurfaceSpec and total reason truth table: findings (FAIL, PE-1.3)"
source: "docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md"
doc_type: decision
description: "Stage-authored formal adjudication of Proof C run 1 under charter PE-1.3 section 6.5. Ship ran one disposable two-file synthetic fixture (c_truth.py, c_schema.json) once in the one current worktree at HEAD 83525c62, on Windows 11 build 26200 / NTFS / Python 3.12.10 / jsonschema 4.26.0 / PyYAML 6.0.3. The final invocation exited 1. Stage independently confirmed both fixture SHA-256 values and sizes and read both files and the governing texts without running anything. Inside the fixture, the candidate behaved as intended: 45 unique codes, each reached by one synthetic input with exactly one outcome; all 45 outputs schema-valid; 14 leaf schema branches; 935 pairwise precedence cases; unknown well-formed labels (harvest, impl-plan) yield SURFACE_UNSUPPORTED -> UNRESOLVED / 2; 12 output mutants rejected. The exit 1 came only from a fixture self-check of an unratified Stage count statement (38 UNRESOLVED; the arithmetic gives 39). That check is recorded, but it does not decide the verdict. The verdict is decided by a defect the fixture did not test. Charter section 6.6 at PE-1.3 and the decided read-budget decision (Decision 2) fix the class 1b read-limit reason codes as FILE_COUNT_LIMIT, TOTAL_SIZE_LIMIT and FILE_SIZE_LIMIT, say no new reason code is created, and say Proof C's truth table and schema parity must include them. The executed candidate has none of the three and instead invents READ_BUDGET_EXHAUSTED. So three governing reason codes cannot be reached, and a governing class 1b output is rejected by the candidate schema. Both are section 6.5 fail conditions. Verdict FAIL. PE-INTERFACE-03, PE-DATA-01 and PE-DATA-02 are not satisfied at proof entry. The route is charter change control (a PE-1.4 bump of section 6.5 under PE-FLOW-04), then Proof C run 2. No plan rewrite follows. No production resolver exists or was exercised. Render parity was not observed. No claim authority."
docline:
  type: spike
  date: 2026-09-24
  time_box: "75m"
  conclusion: "pivot"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "surface-taxonomy"
    - "reason-codes"
    - "schema-parity"
    - "proof-entry"
    - "ship-lifecycle"
proof: C
proof_run: 1
proof_verdict: FAIL
proof_verdict_scope: synthetic-candidate-taxonomy-and-schema
production_resolver_exercised: false
render_parity_observed: false
candidate_schema_status: rejected-candidate-not-finalized
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.3"
matrix_id: PE-1.3
charter_section: "6.5"
matrix_rows: [PE-INTERFACE-03, PE-DATA-01, PE-DATA-02]
evidence_rows_self_assessed: [PE-EVIDENCE-01, PE-EVIDENCE-05]
governing_inputs:
  - "docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md sections 3.1, 6.1, 6.5, 6.6"
  - "docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md Decision 2 (status decided)"
  - "docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md revision 12 (frozen diagnostic record, read-only)"
  - ".autoharness/harness-manifest.yaml at HEAD 83525c62 (read-only)"
scratch_path: "C:\\Source\\GitHub\\autoharness\\.proof-scratch\\C-20260924-120736\\"
fixture_files:
  - {name: c_truth.py, bytes: 21300, sha256: da5277edfa269f96e64a0df525c7fa4ccdbea1a824c786eeca2ead52ed27f9e9, stage_verified: true}
  - {name: c_schema.json, bytes: 23610, sha256: c80cab23bfae45ff34e799abb7d0be1787c1d89ceab0fce0f3cc2c70f89345ae, stage_verified: true}
final_exit_code: 1
final_exit_cause: "fixture self-check of the unratified Stage count statement (38 vs arithmetic 39)"
final_exit_cause_binding: false
decisive_defect: "class 1b read-limit reason codes FILE_COUNT_LIMIT, TOTAL_SIZE_LIMIT, FILE_SIZE_LIMIT absent; READ_BUDGET_EXHAUSTED invented"
decisive_defect_detected_by_fixture: false
reopened_decision: "charter section 6.5 Proof C setup (fold in the section 3.1 / Decision 2 change request); no architecture decision reopened"
fail_route: "charter change control: PE-1.4 bump of section 6.5 under PE-FLOW-04, then Proof C run 2"
branch: chore/stage-176-s-workflow-defects
head_at_ship_execution: 83525c62
head_at_authoring: 83525c62
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: "queued/frozen (as reported by Ship; not re-read by Stage)"
shipment_claim_ready: false
publication_eligible: false
backlog_item_created: false
plan_changed: false
charter_changed: false
other_proof_verdicts_changed: false
time_bound_status: met-on-cumulative-active-time-accounting
file_bound_status: met
scratch_cleanup_status: left-in-place-no-cleanup-approval
---

# Proof C findings - one-entry SurfaceSpec and total reason truth table

## Verdict

| Field | Value |
|---|---|
| Verdict | **`FAIL`** (PE-1.3, section 6.5, run 1) |
| What was tested | A disposable synthetic model of a Stage-derived candidate reason taxonomy, plus a candidate Draft 7 result schema. **No production resolver exists, and none was exercised.** Nothing here says how any `harness resolve` implementation behaves |
| Decisive finding | The candidate taxonomy does not contain the three class 1b read-limit reason codes that the governing texts require (`FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT`). It adds a code that no governing text defines (`READ_BUDGET_EXHAUSTED`). This hits two section 6.5 fail conditions: "any code is unreachable" and "schema and runtime disagree" (see Adjudication) |
| Final process exit | **1.** It is recorded as exit 1 and is never reported as exit 0. Its only cause is a non-binding count self-check (see Exit 1 Classification). The verdict does not rest on it |
| `PE-INTERFACE-03` (`P1`) | **Not satisfied at proof entry.** The row criterion (unknown well-formed values yield `SURFACE_UNSUPPORTED`, which reduces to `UNRESOLVED`) was observed in the synthetic candidate. The one mapping closed against the HEAD manifest. The row's evidence is the Proof C findings, and this proof is `FAIL`. There is no partial pass, so the observation carries forward to run 2 only as supporting evidence |
| `PE-DATA-01` (`P1`) | **Not satisfied.** The candidate is closed over its own 45 codes, but not over the governing reason set |
| `PE-DATA-02` (`P1`) | **Not satisfied.** The candidate schema rejects a governing class 1b output |
| Time bound (75m, Stage plus Ship) | **Met on cumulative active-time accounting** (about 44m upper bound; see Time and File Bounds). Not a cause of the verdict |
| File bound (2 disposable) | **Met.** Exactly two files, and no `__pycache__` (per Ship; the listing was confirmed by Stage) |
| Other proofs | Proofs B and D are not re-labelled. `187-S` is not claimed or changed |

## Question

Charter section 6.5: "Is the taxonomy closed, and does the schema match the
runtime exactly?" Section 6.2 row C asks: "Is a one-entry `SurfaceSpec` with
total member and manifest reason codes a closed, schema-parity-complete truth
table?"

## Governing reason-code requirement (read-only, verbatim anchors)

* Charter section 6.6 (PE-1.3, in force): "Read-limit errors are
  `FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT` and `FILE_SIZE_LIMIT`. They map to
  reducer class 1b (after mutation, before class 2), with the triggering code
  as `reason_code`."
* Charter section 3.1: these three values "are recorded as a change request for
  Proof C's truth table and schema parity. Proof C's question, bounds and rows
  are unchanged."
* Decision 2 (`status: decided`), item 4: "The result's `reason_code` is the
  existing `ReadErrorCode` value that occurred first ... **No new reason code or
  taxonomy is created.**" It then adds: "Proof C's reason truth table and schema
  parity must include these three values as `UNRESOLVED` reasons."
* Plan revision 12 line 77 (frozen) lists all three as `ReadErrorCode` members.

These texts are ratified. The Stage count statement is not (see below). Both
the decision and the section 6.6 amendment were committed before this run.

## Adjudication

**Decisive defect.** Stage searched both hash-verified fixture files for
`FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT` and `ReadErrorCode`.
There are zero occurrences in either file. `READ_BUDGET_EXHAUSTED` appears in
`c_truth.py` (group `G1B`) and twice in `c_schema.json` (the top-level
`reason_code` enum and the `UNRESOLVED` empty-surfaces branch). It appears in no
tracked document under `docs/`. So:

1. The three governing class 1b codes have no input class and no schema branch
   in the candidate. Measured against the governing reason set, they are
   unreachable. That is section 6.5 fail condition "any code is unreachable",
   and `PE-DATA-01` closure is not met.
2. A governing class 1b output (`UNRESOLVED / 2 / FILE_COUNT_LIMIT`) fails the
   candidate schema's closed `reason_code` enum. The candidate's own class 1b
   output (`READ_BUDGET_EXHAUSTED`) breaks Decision 2 item 4. That is section
   6.5 fail condition "schema and runtime disagree", measured against the
   governing runtime contract, so `PE-DATA-02` parity is not met.

**Why this is `FAIL` and not `BLOCKED` or `PASS`.** Section 6.1 limits
`BLOCKED` to an unavailable environment or a rejecting per-invocation gate.
Neither happened: Ship's gates passed and the host was available. The proof
was executed, and the truth table it tested falls short of a governing
criterion. `PASS` is ruled out on every reading. Even if "runtime" meant only
the fixture's model, the governing texts say that Proof C's truth table "must
include" the three values, and this one does not. The final exit is also 1,
and raw stdout is not evidenced (see Evidence Gaps). The failure is in the
Stage-derived candidate, not in the architecture. No architecture decision is
shown to be wrong, so the `FAIL` routes to charter change control (section
6.1 FAIL routing; `PE-FLOW-01`).

**The fixture did not detect the defect.** Ship's C1-C9 summary ("all met")
describes the candidate measured against itself. It does not imply `PASS`.

## Exit 1 classification (count self-check)

`c_truth.py` appends a failure when `len(UNRESOLVED) != 38`. This matches the
earlier Stage candidate handoff statement ("38 unresolved codes", session
`b69dd2d1-17d9-4590-8013-c5791afd75f5`). That handoff is not a durable
artifact. Stage could not re-read it and relies on Ship's report and the
fixture source for its content. The arithmetic is 45 total − 2 `HARNESS_READY`
(`NO_SURFACES_REQUIRED`, `ALL_SURFACES_PRESENT`) − 4 `NO_HARNESS`
(`MANIFEST_ENTRY_NOT_FOUND`, `INSTALLED_NOT_FOUND`, `CHECKSUM_MISMATCH`,
`RENDER_MISMATCH`) = **39**. Stage confirmed the schema encodes 39: a 32-value
empty-surfaces `UNRESOLVED` branch plus a 7-value `INVALID`-row `UNRESOLVED`
branch.

Classification: this is a **non-binding fixture self-check of an unratified
Stage sketch statement**. Section 6.5 prescribes no count. The run is still
admissible: it ran under the section 6.1 gates, and both fixture files are
hash-pinned. By itself the check would not show a contract `FAIL`. It is
recorded as a Stage derivation defect: the handoff was internally inconsistent
(code list against count). The exit status stays **1**, and it is not
disregarded.

## Per-criterion evidence (section 6.5 pass text)

In this table, "Observed" means the behavior was seen in the synthetic
candidate only.

| # | Criterion | Status | Evidence and limitation |
|---|---|---|---|
| P1 | Exhaustive enumeration maps each bounded input class to exactly one `(state, exit, reason_code)` | Observed (candidate only) | The resolver is `min` over a strict total order of 45 codes, so each outcome is deterministic and unique. There are 45 single-code inputs and 7 label inputs. **Limitation:** 38 of the 45 codes are reached by injecting the code itself as the input class (`candidate_codes: [code]`), so reachability holds by construction. Only the label classes are derived from input shape |
| P2 | Member classes: one supported, `none`, missing, duplicate, malformed, unknown-but-well-formed | Observed | The 7 label cases cover all of them. `Harness-Architect` (uppercase) is malformed. A mixed-label case (for example `harness-architect` plus `none`) is not in the label cases. `DECLARATION_MIXED` is reached by injection only |
| P3 | Unknown well-formed yields `SURFACE_UNSUPPORTED`, then `UNRESOLVED`, never `NO_HARNESS` | Observed | `harvest` and `impl-plan` are real manifest entries that are not supported surfaces. Both give `UNRESOLVED / 2`. Group `G3` precedes `G7` in every cross pair. **Limitation:** "zero manifest reads" is modelled from the winning code (`reads = 1 if winner in G5..G8`). It is not measured, and the section 6.5 text does not require it |
| P4 | Global manifest failure codes enumerated with a fixed precedence | Observed | 6 `G5` codes in a fixed order. Within-class pairs are included. Global errors give empty `surfaces` (as in plan revision 12) |
| P5 | Every code reachable | **Not met against the governing set.** Met within the candidate | The three class 1b `ReadErrorCode` values are absent (decisive defect) |
| P6 | Every runtime output validates against the candidate schema | Met for the model outputs. **Not met against the governing contract** | All 45 model outputs and the non-empty declaration payloads validated (per Ship). A governing class 1b output would be rejected |
| P7 | Every schema branch produced by at least one input | Observed | There are 14 leaf branches: 2 ready, 4 `NO_HARNESS`, 1 empty `UNRESOLVED` and 7 `INVALID`-row `UNRESOLVED`. Stage confirmed the top-level `oneOf` has 5 branches, with nested `oneOf` counts of 4 and 7. The branch enums partition the 45-value enum (1+1+4+32+7). **Limitation:** the fixture names branches with its own mapping function (`schema_branch_for`) and does not ask the validator which branch matched. Because the partition is disjoint and `oneOf` is used, each valid document still matches exactly one branch |
| P8 | Mutated outputs rejected | Observed | 12 output mutants rejected, plus a control that deletes a schema enum value. **Limitation:** the "unknown-surface manifest-read mutant" is a hard-coded constant (`bad_unknown_manifest_reads = 1`), so that control is vacuous. The PyYAML control shows that plain `safe_load` silently overwrites duplicate keys. It shows the hazard. It does not implement `MANIFEST_DUPLICATE_KEY` detection |

Stage checked the precedence count by arithmetic: 935 = 725 cross-group pairs
(44 codes excluding `G8`, minus the 11 `G4`×`G6`/`G7` pairs that were skipped
because no manifest read happens with an empty surface union, as in plan
revision 12) + 195 within `G2`/`G5`/`G6`/`G7` + 15 within `G3`. For a strict
total order, checking pairs is enough.

**Manifest closure (supporting evidence, `PE-INTERFACE-03`).** At HEAD
`83525c62`, the fixture reported that the installed path
`.github/skills/harness-architect/SKILL.md` matches exactly once, that the
template `skills/harness-architect/SKILL.md.tmpl` matches, and that the
manifest checksum equals the SHA-256 of the raw installed HEAD blob. Stage
confirmed by reading that the entry sits at manifest lines 237-239, which
agrees with the charter anchor.

**Render parity: not observed.** The fixture's
`render_equality_manifest_variables_only: false` cannot be trusted. It read
`variables_used` from the artifact entry, and the entry has none. The one
top-level mapping (plan revision 12: "Rendering uses the manifest's one
top-level variables mapping") starts at manifest line 467. Stage checked names
only: the template's 5 unique placeholders (`BUILD_CHECK_COMMAND`,
`SOURCE_DIR`, `TEST_COMMAND`, `TEST_DIR`, `UNIMPLEMENTED_MARKER`) all appear
among the mapping's 37 keys. Stage did not render or compare anything. No
raw-blob render parity is claimed, and whether the real surface would classify
as `PRESENT` is open. The section 6.5 pass text does not require this.

## Unratified candidate elements (non-binding)

* The count statement "38 unresolved" (see above).
* The shape of `declarations` items, `{member_id, surface_id}` with
  `additionalProperties: false`, is Ship's assumption. The Stage handoff did
  not specify it, and plan revision 12 says only "Declarations sort by task ID".
* The rule for choosing between declaration issues (lowest ASCII-sorted member
  ID first, then code order) is not in any governing text.

## Evidence record (`PE-EVIDENCE-01`)

| Field | Value |
|---|---|
| Host | Windows 11 build 26200, NTFS (per Ship) |
| Interpreter | Python 3.12.10 from `.venv`, jsonschema 4.26.0, PyYAML 6.0.3 |
| Scratch path | `C:\Source\GitHub\autoharness\.proof-scratch\C-20260924-120736\` (ignored by `.gitignore:10 .proof-scratch/`; Stage confirmed) |
| Fixture listing | `c_truth.py` 21300 B `da5277ed…f9e9`; `c_schema.json` 23610 B `c80cab23…45ae`. Stage confirmed both with `Get-FileHash`. The full digests are in the frontmatter |
| Command (as reported) | `PYTHONDONTWRITEBYTECODE=1 .venv\Scripts\python.exe -B .proof-scratch\C-20260924-120736\c_truth.py`. Ship reported this literally, and it is not valid PowerShell assignment syntax. The operator reading is `$env:PYTHONDONTWRITEBYTECODE='1'; & .venv\Scripts\python.exe -B ...`. `-B` alone prevents bytecode writing either way. This is recorded as a transcription discrepancy and decides nothing |
| Exit / runtime | Exit **1**. Final fixture runtime 1.063 s |
| Invocations | More than one. An earlier run found and fixed a schema-nesting bug that Ship owned. The final run is the one adjudicated. No run happened after the verdict |
| Gates | P-001, P-002, P-010, P-011 and P-016 passed. One worktree. Clean status before and after, apart from scratch. No backlog mutation and no index sync (per Ship) |
| Stage verification | Read-only: file hashes and sizes, source reading, schema structure summary, verbatim governing text, manifest lines and placeholder names. Stage ran no fixture, test, build or linter (P-010) |

**Evidence gaps.** Ship's handoff contained no raw stdout or stderr and no
SHA-256 of either. The decisive defect does not depend on stdout, because it
rests on hash-verified fixture source and ratified text. Any run 2 `PASS` would
still need these fields.

## Time and file bounds

Cumulative active time: about 9m of earlier Stage analysis, 13m21s of Ship
execution, and about 21m of this Stage adjudication (12:14 to 12:35 local).
That is an upper bound of about 44m against 75m. The wall-clock span from the
earliest Stage analysis cannot be determined from the evidence available and
is not claimed. File bound: 2 of 2.

## Tool states (`PE-EVIDENCE-05`)

| Tool | State this session |
|---|---|
| engram | `ENGRAM_DEGRADED`: the pack instructions are present, but this session exposed no engram tools. File-based reading was used |
| intercom | `INTERCOM_DEGRADED`: no intercom tools were exposed, and nothing was broadcast |
| graphtor-docs | `GRAPHTOR_UNAVAILABLE`: no tools were exposed. `grep`/`view` over `docs/` was used |
| backlogit | The MCP tools were listed as deferred and were not probed. The CLI was not invoked. The index sync and checkpoint scan were skipped because the operator set a read-only, no-backlog-mutation scope. Ship reported the CLI available and MCP not |

No writes were made outside the current working directory. One read-only
directory listing of the user session-state folder, looking for the
`b69dd2d1` handoff, found nothing.

## Route and next step (`PE-FLOW-01`, `PE-FLOW-04`)

1. **Reopened decision:** charter section 6.5 (Proof C setup) only. No plan
   rewrite, no architecture reopening, and no Proof C re-run under PE-1.3.
2. **Stage, charter change control:** draft a charter PE-1.4 change record for
   the operator to approve. It would:
   * fold the section 3.1 / Decision 2 change request into section 6.5, with
     class 1b reason codes limited to the three `ReadErrorCode` values and no
     invented codes;
   * require a durable, hash-pinned Stage candidate (code list, state
     partition, precedence and declaration item shape) committed before Ship
     dispatch, with every count derived from the list rather than asserted;
   * state whether render parity using the top-level `variables_used` mapping
     is inside or outside Proof C.
3. **Then Proof C run 2** under PE-1.4, with a new scratch directory, a fresh
   75m bound and a fresh 2-file bound. The evidence handoff must include raw
   stdout/stderr or their SHA-256. Suggested fixture hygiene (non-binding):
   ask the validator which branch matched, observe reads instead of modelling
   them, and add a mixed-label case.
4. **Scratch:** `C-20260924-120736` stays in place as hash-pinned evidence.
   Ship removes it only after operator approval (section 6.1). Stage does not
   remove it.

## Cross-references

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (PE-1.3)
* `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
* `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md` (Proof D run 2; not re-labelled)
* `docs/decisions/2026-09-24-cli-authenticity-proof-b-spike.md` (Proof B; not re-labelled)
* `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` (revision 12; frozen, unchanged)
