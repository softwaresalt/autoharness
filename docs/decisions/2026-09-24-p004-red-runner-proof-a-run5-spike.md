---
title: "Proof A run 5 (PE-1.4) - live P-004 RED conformance: A-STATIC adjudication and findings (PASS, synthetic fixture only)"
source: "docs/decisions/2026-09-24-p004-red-runner-proof-a-run5-spike.md"
doc_type: decision
description: "Stage-authored Proof A findings under charter PE-1.4 section 6.3. Ship's run 5 driver (.proof-scratch/A-run5-20260924-160006/proof_driver.py, 12521 B, SHA-256 052447ac...b29e4a, re-hashed read-only by Stage) generated ten disposable source-layout workspaces and ran the exact canonical command PYTHONPATH=src python -m unittest discover -s tests in each, with no -v flag and no subset. All ten native runs exited 1. Every stdout was empty. Driver stdout was 17466 B (SHA-256 6ab05c08...823932), driver stderr was empty and the driver exited 0. Positive case: Ran 5, FAILED (errors=3). Three named ERROR blocks each carried exactly their own NotImplementedError marker, and the unrelated and characterization tests passed anonymously. All nine required rejections are refused under the written contract. A-STATIC settles the historical R1/R2 'canonical output alone' question as R2 from the cited text of P-004, charter section 6.3 and harness-architect Step 5.2, under the operator's bounded instruction. It does not edit any row and does not expand scope. Verdict PASS for the synthetic fixture only. It is not P-004 gate evidence for any task and makes no harness-ready or claim assertion. The in-place addendum of 2026-09-24 copies in the PE-EVIDENCE-01 fields from Ship's existing handoff, with no new execution. Those fields are the host (Windows 11 10.0.26200 SP0, NTFS, Python 3.14.3 64-bit), the ten per-run stderr lengths and SHA-256 values, the timing, the P-010 and P-002 itemization, the .backlogit ignored-status comparison and the refresh record. With them, PE-EVIDENCE-01 is met. The file-bound count (authored disposable scripts, not generated section 6.3 setup data) and the tool-wrapper spool classification are recorded as Stage interpretations of the charter text. They are not operator sign-offs, and the operator may still veto them at proof exit."
docline:
  type: spike
  date: 2026-09-24
  time_box: "1h"
  conclusion: "proceed"
  confidence: "medium"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "p-004"
    - "red-phase"
    - "unittest"
    - "proof-entry"
    - "ship-lifecycle"
proof: A
proof_run: 5
proof_verdict: PASS
proof_verdict_scope: synthetic-fixture-only-not-p004-gate-evidence-for-any-task
prior_run_artifacts:
  - {runs: "invocations 1-3", path: docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md, verdict: BLOCKED, matrix: PE-1.1}
  - {run: 4, path: "none (no findings artifact; scratch .proof-scratch/A-run4-20260924-154828)", verdict: "none - driver projection defect, superseded"}
prior_run_verdicts_changed: false
a_static_reading: R2
a_static_reading_basis: "P-004 Statement and Precondition 3; charter section 6.3 Pass, Required rejections and Fail structure; harness-architect Step 5.2"
charter_row_changed: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.4"
matrix_id: PE-1.4
matrix_rows: [PE-EVIDENCE-03, PE-FLOW-02]
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 36f65975
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
publication_eligible: false
actor_invoked: false
p004_gate_evidence_for_any_task: false
harness_ready_asserted: false
backlog_item_created: false
plan_changed: false
time_bound_status: met
file_bound_status: "met under the Stage interpretation (authored disposable scripts = 1; the 40 generated section 6.3 setup data files are not counted); not an operator sign-off; operator veto possible at proof exit"
tool_spool_status: "Stage interpretation: automatic tool-wrapper spools are not agent-directed Ship writes and not raw proof output; disclosed; not an operator sign-off"
pe_evidence_01_status: "met (addendum 2026-09-24, transcribed from Ship's existing handoff, no new execution)"
host: {os: "Windows 11 10.0.26200 SP0", filesystem: "NTFS (C:)", interpreter: "Python 3.14.3 64-bit"}
addendum:
  date: 2026-09-24
  base_commit: 99e9ff5f
  scope: "PE-EVIDENCE-01 transcription and interpretation record only; no charter, plan or backlog edit; no runner, test or index sync"
  verdict_changed: false
scratch_cleanup_status: "retained at authoring; Stage deleted nothing"
stage_model_route: "claude-opus-5.5/anthropic/high requested; unverified by Stage (route not self-verifiable)"
---

# Proof A run 5 findings (PE-1.4): live P-004 RED conformance

## Verdict

| Field | Value |
|---|---|
| Proof | A, live P-004 RED conformance ([charter](2026-09-23-lifecycle-proof-entry-charter.md) section 6.3, unchanged by PE-1.4) |
| Run | 5, scratch `.proof-scratch/A-run5-20260924-160006/` |
| Matrix rows | `PE-EVIDENCE-03`, `PE-FLOW-02` |
| Verdict | **`PASS`**, for the synthetic fixture only |
| A-runner | Met, on Ship's reported evidence (see Runner Behavior) |
| A-static | Met. `ERROR` for an uncaught own-marker `NotImplementedError` is consistent with "fails with its own expected marker". Each of the nine required rejections is refused under the written contract. Attribution is read under R2, decided below from the cited text |
| Fail clause | Not triggered. No required rejection qualifies. Each positive roster test is individually attributed from canonical output alone. No runner classification contradicts P-004 |
| Time bound (60m, Stage plus Ship) | **Met** (see Time and File Bounds) |
| File bound (3 disposable) | **Met under the Stage interpretation** recorded in the addendum. One authored disposable script is counted. The 40 generated setup data files that section 6.3 requires are not counted. This is an interpretation, not an operator sign-off. If the operator vetoes it at proof exit, the literal count of 41 makes the run `FAIL` under `PE-SCOPE-07` |
| `PE-EVIDENCE-01` | **Met** by the addendum, which copies the fields from Ship's existing handoff |
| Open for proof exit | Operator review of the three Stage interpretations: the R2 reading, the file-bound count and the spool classification (see Unresolved Gates). Also the portfolio-level `PE-FLOW-02` |
| Earlier verdicts | Invocations 1-3 stay `BLOCKED` (PE-1.1), as recorded. Run 4 has no verdict |

This artifact does not state that the harness-architect actor accepted or
refused any fixture. The actor was not invoked. The runner did not claim P-004
acceptance. This artifact presents no scratch result as P-004 gate evidence
for any task. It asserts no red-phase confirmation, no `harness-ready` state
and no claim or publication readiness (`PE-EVIDENCE-03`, `PE-AUTH-03`,
`PE-ACTIVATE-03`). `187-S` remains `queued` and is not claim-ready.

## Goal

What evidence shape does the live P-004 contract accept when the canonical
whole-suite command `PYTHONPATH=src python -m unittest discover -s tests` runs
over generated tests whose production stubs each raise a unique
`NotImplementedError` marker? Is every rejected outcome that P-004 lists
refused?

## Success Criteria

These are taken verbatim in substance from charter section 6.3 (lines
606-655) and are not amended here:

* **Pass (A-runner).** The run exits non-zero. Each roster test is
  individually identifiable in the output with its own marker (line 640). The
  unrelated passing test does not affect the verdict. The characterization
  test does not contaminate roster attribution. The output shows how unittest
  classifies an uncaught `NotImplementedError`.
* **Pass (A-static).** That classification is consistent with P-004's wording,
  "fails with its own expected marker".
* **Required rejections (lines 646-650).** Each of the nine outcomes is shown,
  "from actual runner output compared with the written contract", to be
  refused as RED evidence.
* **Fail (lines 651-655).** Any required rejection qualifies, any roster test
  cannot be individually attributed from canonical output alone, or the runner
  classification contradicts the P-004 wording. The time or file bound is
  exceeded (section 6.1, line 556).

## Scope Constraints

* **Stage did read-only work only.** Stage read compound `097-S`; the charter
  (sections 2, 3, 3.2, 3.3, 6.1, 6.2, 6.3, 7, 8 and 10); P-004 in
  `.github/policies/workflow-policies.md` (lines 78-104); harness-architect
  Step 4 item 3 and Step 5.2; manifest `variables_used.TEST_COMMAND` and
  `variables_used.UNIMPLEMENTED_MARKER` (lines 472-473); the historical
  Proof A artifact; the run 4 and run 5 driver scripts; and the run 5
  generated fixture files. It also read earlier Proof F and Proof G artifacts
  for the file-bound precedent.
* **Stage executed nothing.** Stage ran no fixture command, driver, runner,
  test suite, build or linter. It re-ran no Ship command and did not reproduce
  any runner fact. Its only commands were read-only: `git status`,
  `git rev-parse`, `git log`, `git worktree list`, directory listings,
  `Get-FileHash` and `Get-Content` over scratch, and one `backlogit_get_version`
  probe with the update check skipped.
* **Stage made no mutations.** It ran no index sync or backlog CLI mutation,
  made no backlog, stash, shipment, carrier, label or checkpoint change, and
  opened no branch, pull request or push. It wrote no source, test, template,
  schema or configuration file and did no scratch cleanup. Its only write is
  this file, committed normally (no amend).
* **No actor invocation, no `harness-ready` read, add or remove.**

## Session and Tool State (`PE-EVIDENCE-05`)

| Surface | State | Note |
|---|---|---|
| backlogit | `TOOL_OK` | `backlogit_get_version` (`no_update_check: true`) returned `1.10.1-0.20260823032255-b07729386a31+dirty` |
| Index sync (Stage Step 0.1) | Skipped by operator scope | The operator forbade Stage index sync. Stage made no semantic backlog read. Charter section 6.1 assigns the refresh to Ship alone. This is not a claim that sync is unnecessary |
| agent-engram | `ENGRAM_DEGRADED` | No engram tool exposed in this session. Bounded exact file reads used instead |
| agent-intercom | `INTERCOM_DEGRADED` | No intercom tool exposed. No broadcast was made |
| graphtor-docs | `GRAPHTOR_UNAVAILABLE` | No server tool exposed. No documentation search was made |
| Checkpoint recovery (Stage) | Not run | The operator scoped this session to authoring findings only. Ship reported the unfiltered scan (below) |
| Git at authoring | Tracked tree clean | `git status --porcelain` empty. `.proof-scratch/` ignored (`!!`). Branch `chore/stage-176-s-workflow-defects`, HEAD `36f65975`, one worktree |

## Ship Invocation Record (as reported to Stage)

| Item | Reported value |
|---|---|
| Scratch path | `.proof-scratch/A-run5-20260924-160006/`, a direct child of the current working directory. The driver refuses to run elsewhere (`EXPECTED_SCRATCH`, `SCRATCH.parents[1]` checks) and refuses a non-fresh workspace |
| Index refresh | Cache-only sync, native exit 0 |
| Checkpoint scan | Unfiltered, 71 total, 0 quarantined, 0 active. Abandoned records `valid: true` |
| P-001 projections | Active counts 0. `173-S` closure READY, compaction done |
| P-011 | Branch `chore/stage-176-s-workflow-defects`, HEAD `36f65975`, clean before the first write |
| P-016 | One worktree |
| `PE-ACTIVATE-01` | The three blobs match `4acba14a` |
| P-010 self-check, P-002 | Itemized in the addendum. P-010: only scratch writes were authorized. P-002: no claim and no `harness-ready` consumption |
| Driver | Native exit 0. stdout 17466 B, SHA-256 `6ab05c08...823932` (full value below). stderr 0 B |
| Canonical runs | 10, each native exit 1. Each stdout 0 B, SHA-256 of empty input. The addendum lists each run's stderr byte length and full SHA-256 |
| Separate collector | A separate Ship evidence-collector command exited 5 because it expected 31 generated files and found 41. It is not a runner or driver result, and no runner was re-executed |
| Tool-wrapper spools | Three automatic spools by the tool wrapper to the OS Temp directory, of document, search and bounded summary output. They are not raw runner output and not agent-issued file writes (classified under Evidence Caveats) |
| Cleanup | Not performed, per operator instruction |

Full digests:

```text
driver script   12521 B  052447ac2a5c778c5d0555359d9bd1ea658335c618370de08fbac5a355b29e4a
driver stdout   17466 B  6ab05c082956edae6fe25d22f05b7cc9c332e7cdd9f7840d03b1e0eec8823932
driver stderr       0 B  (empty)
each run stdout     0 B  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**Environment assignment on Windows** (from the driver source).
`subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=workspace, env=...)`,
with `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, and `TEMP` and `TMP` set to
`workspace/.tmp`, and `capture_output=True`. There is no `-v` flag, no pattern
and no subset. This is the section 6.3 exact command. The `PYTHONPATH=src`
prefix is carried in the child environment, because a POSIX-style inline
assignment is not a Windows shell construct. Runner temp writes were
redirected into scratch. All ten `.tmp` directories are empty, and no
`__pycache__` exists.

## Investigation Approach

1. Re-read the normative inputs verbatim, compound `097-S` first.
2. Compare the run 4 and run 5 drivers (read-only diff) and review the run 5
   generator and parser for how the fixture is built and how attributions are
   projected.
3. Re-hash the run 5 fixture tree read-only and check its structure against
   the section 6.3 setup.
4. Map each reported outcome to its P-004 and Step 5.2 clause (A-static).
5. Decide the R1/R2 reading from the written text, or record `BLOCKED` if the
   text cannot decide it.
6. Record bounds, caveats, per-criterion verdicts and open gates.

## Findings

### Run 4 versus Run 5 Driver (read-only diff)

The two drivers differ in exactly two lines:

| Line | Run 4 (`345aca5a...ba0554`, 12518 B) | Run 5 (`052447ac...b29e4a`, 12521 B) |
|---|---|---|
| Scratch constant | `A-run4-20260924-154828` | `A-run5-20260924-160006` |
| Header parser | `re.finditer(r"^(ERROR\|FAIL): ([^\r\n]+)$", text, re.MULTILINE)` | `re.finditer(r"^(ERROR\|FAIL): ([^\r\n]+)\r?$", text, re.MULTILINE)` |

On Windows, unittest's text-mode stderr ends lines with `\r\n`. With
`re.MULTILINE`, Python's `$` matches only before `\n`. `[^\r\n]+` cannot
consume the `\r`, so the run 4 pattern cannot match any `ERROR:` or `FAIL:`
header line. Its per-test attribution projection would be empty whatever the
runner emitted. The run 5 `\r?$` form fixes this. The `Ran` pattern
(`[^\r\n]+` with no `$` anchor) and the exception-type pattern were not
affected.

**Adjudication.** Run 4 had a defect in the driver's own summary projection.
It is not an evaluation of the proof question. No run 4 verdict is recorded,
and run 5 is not a `PE-FLOW-04` re-run of a failed question. This follows the
Proof F run 2 precedent for fixing an ephemeral command before evidence
exists. Run 5 used a fresh scratch directory and gets its own section 6.2
bound (section 3.3, line 352). Stage has no run 4 output.

### Fixture Construction (run 5 driver, read-only)

* **Production stubs.** `src/proof_stubs.py` defines `alpha`, `bravo` and
  `charlie`. In the positive workspace each raises `NotImplementedError` with
  its own marker: `PE14_A_ALPHA_EXPECTED`, `PE14_A_BRAVO_EXPECTED` and
  `PE14_A_CHARLIE_EXPECTED`. This matches harness-architect Step 4 item 3
  (line 95) and manifest `UNIMPLEMENTED_MARKER` =
  `raise NotImplementedError("...")`. The markers are in the stubs, not in the
  tests, which fixes the invocation 2 defect.
* **Three roster tests.** `tests/test_roster.py` holds `TestRoster` with
  `test_roster_alpha`, `test_roster_bravo` and `test_roster_charlie`. Each
  calls its own stub.
* **Two additional passing tests.** `tests/test_unrelated.py`
  (`TestUnrelated.test_unrelated_established_pass`) and
  `tests/test_characterization.py`
  (`TestCharacterization.test_characterization_outside_roster`), outside the
  roster.
* **Nine negative variants.** Each is generated into its own fresh workspace
  by mutating only the alpha test or alpha stub, or the roster module for the
  import case:

| Variant workspace | Construction |
|---|---|
| `marker_assertion` | `alpha` raises `AssertionError("PE14_A_ALPHA_EXPECTED")` |
| `passing_roster_test` | `alpha` returns `None` |
| `skipped_roster_test` | The alpha test body calls `self.skipTest(...)` |
| `expected_failure` | The alpha test is decorated `@unittest.expectedFailure`, and its stub still raises its own marker |
| `unexpected_success` | The alpha test is decorated `@unittest.expectedFailure`, and `alpha` returns `None` |
| `wrong_marker` | `alpha` raises `NotImplementedError("PE14_A_ALPHA_WRONG")` |
| `cross_test_marker` | `alpha` raises `NotImplementedError("PE14_A_BRAVO_EXPECTED")` |
| `zero_discovery_one_roster_test` | The alpha method is renamed `roster_alpha_not_discovered`, which lacks the `test` prefix. Bravo and charlie are unchanged |
| `roster_import_error` | The roster module imports a missing module `pe14_missing_roster_dependency` |

* **Parser projection.** Each `ERROR:` or `FAIL:` header opens a block that
  runs to the next header. Test IDs come from the runner's own header line.
  The driver's marker list is used only to report which markers occur in each
  block. The `output_names_nonverbose: false` field is a constant label in the
  driver, not an observation, and this artifact gives it no weight.

### Fixture Listing (Stage read-only re-hash)

41 regular files: the driver plus four generated files in each of ten
workspaces. There are ten empty `.tmp` directories and no `__pycache__`.
Ship's own per-file `FILE` lines are in the driver stdout (`6ab05c08...`).
Stage re-hashed the tree read-only with `Get-FileHash` as a corroborating
check. That check is not Ship evidence.

| Path (relative to scratch) | Bytes | SHA-256 |
|---|---|---|
| `proof_driver.py` | 12521 | `052447ac2a5c778c5d0555359d9bd1ea658335c618370de08fbac5a355b29e4a` |
| `*/tests/test_unrelated.py` (all 10) | 139 | `5756bb941554c859b8a13036175392931fba7708aaee25f52293b281ebfb476e` |
| `*/tests/test_characterization.py` (all 10) | 179 | `e2de8cf0e3abaf57c3b2097e687d8beb7b68d7ff3d11f48a1b84b36001ae66e5` |
| `src/proof_stubs.py` in `positive`, `expected_failure`, `skipped_roster_test`, `zero_discovery_one_roster_test`, `roster_import_error` | 264 | `3c4b77a094575be59f59ebd42fbdfe1dd1a72c79ae40a2104efd55e57886d528` |
| `src/proof_stubs.py` in `passing_roster_test`, `unexpected_success` | 225 | `b4feed375efbfebc0987ff3f855cbe384aebf83f186e19e7f248cf3c799a419e` |
| `marker_assertion/src/proof_stubs.py` | 259 | `d9cdf4176ae5bb5ea9b5ac12c362847a8f5f45c8f847e839671d818dc413d52e` |
| `wrong_marker/src/proof_stubs.py` | 261 | `a6c114fece10565eefd5326ea337719b1fbe0336d34c0be0615c05090351667f` |
| `cross_test_marker/src/proof_stubs.py` | 264 | `fb8e4e8fcd1690569f610f52ed053cff8588129724eaa123179943d63469e410` |
| `tests/test_roster.py` in `positive`, `marker_assertion`, `passing_roster_test`, `wrong_marker`, `cross_test_marker` | 251 | `09d903acdc4fda3899af84ee443f6eb53b2d1366ba5e1afbd1554fe6c11fc17c` |
| `tests/test_roster.py` in `expected_failure`, `unexpected_success` | 281 | `b8a14c6b211f61d8e3d556265c38f416c60ecf3edafcc18871353bb9cf947fa4` |
| `skipped_roster_test/tests/test_roster.py` | 289 | `a31487293d63c9ef4c3e8cf829946bf46f5a91d0abf0182f95ed36a1560d3a6e` |
| `zero_discovery_one_roster_test/tests/test_roster.py` | 261 | `7ca228880492f5bf205c8021c3732fecf63905e7144946d94910b6c3ac5eb640` |
| `roster_import_error/tests/test_roster.py` | 74 | `d90ae3de5d528da51c814ff4d68f25894cf1981a805b1d30dc4297978034dd6c` |

The hash-sharing pattern matches the generator. For example, the
`expected_failure` stub is byte-identical to the positive stub, because only
the decorator differs. The 31-versus-41 collector mismatch was an error in
the collector's own expectation (41 = 1 + 10 x 4), not a fixture discrepancy.

### Runner Behavior (A-runner, Ship-reported, not reproduced by Stage)

| # | Workspace | Native exit | Reported outcome |
|---|---|---|---|
| P | `positive` | 1 | `Ran 5 tests`, `FAILED (errors=3)`. Named `ERROR` blocks: `test_roster_alpha`, whose only marker is `PE14_A_ALPHA_EXPECTED` with `NotImplementedError`; `test_roster_bravo`, only `PE14_A_BRAVO_EXPECTED`; and `test_roster_charlie`, only `PE14_A_CHARLIE_EXPECTED`. The unrelated and characterization tests passed anonymously |
| N1 | `marker_assertion` | 1 | alpha is a named `FAIL` with `AssertionError`, carrying the alpha marker text |
| N2 | `passing_roster_test` | 1 | alpha passed. There is no named alpha entry, and the other two roster tests are named `ERROR` |
| N3 | `skipped_roster_test` | 1 | Summary counter `skipped=1`. No named alpha `ERROR` |
| N4 | `expected_failure` | 1 | Summary counter `expected failures=1`. No named alpha `ERROR` |
| N5 | `unexpected_success` | 1 | Summary counter `unexpected successes=1`. No named alpha `ERROR`. The parser captures only `ERROR` and `FAIL` headers, so it does not show whether a separate `UNEXPECTED SUCCESS` line named alpha. The refusal below does not depend on that |
| N6 | `wrong_marker` | 1 | alpha is a named `ERROR`. The expected marker is absent and `PE14_A_ALPHA_WRONG` is present |
| N7 | `cross_test_marker` | 1 | alpha is a named `ERROR` carrying `PE14_A_BRAVO_EXPECTED` |
| N8 | `zero_discovery_one_roster_test` | 1 | `Ran 4 tests`. alpha was not discovered |
| N9 | `roster_import_error` | 1 | `Ran 3 tests`, `FAILED (errors=1)`. One named `ERROR` for the loader-synthesized `_FailedTest.test_roster`, with `ImportError`. No roster test ID and no marker |

**Classification.** unittest reports an uncaught `NotImplementedError` from a
running test as **`ERROR`**, not `FAIL`. A marker-bearing `AssertionError` is
**`FAIL`**. This matches invocation 1's PE-1.1 observation. Run 5 is the first
gate-valid run with three roster tests and `src/` stubs. It also supplies the
two variants that PE-1.1 left unobserved: per-test partial non-discovery (N8)
and the import-error form of a collection failure (N9).

**Aggregate exit is not enough.** Every one of the ten runs exits 1, including
all nine rejections, because the sibling roster tests (or the `_FailedTest`)
are still red. So the exit status alone cannot tell valid RED evidence from
invalid. That confirms P-004 Precondition 3's instruction to "evaluate each
such test individually rather than relying on the aggregate non-zero exit
code alone" (line 92) and Step 5.2's matching instruction (lines 128-131).

### A-STATIC: Reading of "Canonical Output Alone" (R1 versus R2)

**The question** (historical artifact, "Canonical Output Alone"). The Fail
clause includes "any roster test cannot be individually attributed from
canonical output alone" (charter line 652). A pass (`.`), skip (`s`) or
`expectedFailure` (`x`), and partial non-discovery, leave no named entry in
default output. Wrong and cross-test markers are classified the same way as a
valid marker. **R1**: roster metadata is excluded, so these outcomes are
unattributable and Fail triggers. **R2**: the roster and its test-to-marker
mapping are inputs of the written contract. A roster test with no named
own-marker entry is refused fail-closed, and an anonymous outcome never needs
to be identified.

**Decision: R2, which the written text implies.** Stage records it under the
operator's instruction for this session. That instruction asks Stage to
decide only if the reading is clearly implied by P-004's "each generated
harness test for the current task", and otherwise to record `BLOCKED`. Five
grounds follow. Each is quoted text, not the more convenient choice (charter
section 2, lines 101-104):

1. **P-004 quantifies over a known roster.** The Statement (line 86) scopes the
   gate to "the current task's generated harness tests" and requires that
   "every generated harness test for the current task fails with its own
   expected marker". Precondition 3 (line 92) requires that "every generated
   harness test for the current task is discovered by that run AND fails with
   its own expected failure marker; evaluate each such test individually".
   "Every ... for the current task" and "its own ... marker" both presuppose
   the set of generated tests and each test's marker. The evaluator does not
   take these from runner output. They are part of the contract. The
   generator authored them at Step 4, and Step 5.2 (line 128) says "EVERY
   generated harness test MUST be discovered".
2. **P-004 treats the anonymous outcomes as absence of observation, not as
   something to identify.** Line 99: a generated test that "passes, is
   skipped, is marked expected-to-fail, or unexpectedly succeeds counts as no
   red-phase observation for that test". Line 98 rejects a test that "is
   credited with a different test's marker, rather than evaluated
   individually". A roster member with no named own-marker entry is exactly
   "no red-phase observation", so it is refused. The contract never asks which
   anonymous `.`, `s` or `x` belongs to which test.
3. **The charter separates the two halves.** Required rejections are judged
   "from actual runner output compared with the written contract" (lines
   646-647). That comparison expressly brings in the contract's own inputs,
   which are the roster and markers in point 1. "Canonical output alone" sits
   in the Fail clause's second disjunct. That disjunct negates the Pass
   criterion "each roster test is individually identifiable in the output with
   its own marker" (line 640), which concerns the positive setup. Each Fail
   disjunct negates one Pass or Rejection element: rejections qualify;
   positive attribution is impossible; classification contradicts. Under R2
   all three are evaluable.
4. **R1 cannot be applied consistently.** Even the positive criterion, "with
   its own marker", needs the test-to-marker mapping. If roster metadata were
   excluded, positive "own marker" attribution could not be evaluated either.
   Applying R1 to the rejection half would make the proof `FAIL` exactly when
   the contract refuses an anonymous outcome correctly. That contradicts the
   Required rejections clause, which demands that refusal.
5. **R1 cannot be implemented without breaking a higher source.** The only
   output that would name passing, skipped or expected-failure tests is
   verbose output. Section 6.3 forbids "a verbosity flag", and P-004
   Precondition 2 (line 91) requires the command "invoked exactly as resolved
   with no runner substitution and no scoped/targeted subset". If the charter
   meant R1, it would conflict with P-004, and under charter section 2 "the
   higher source governs".

**What R2 does and does not do.** It adds no requirement and relaxes none. The
positive half is still judged from canonical output alone: in run P, each of
the three roster test IDs is named by the runner itself with exactly its own
marker. The rejection half is judged against the roster and mapping that P-004
already quantifies over. No row, threshold or charter text is edited
(`charter_row_changed: false`). This is a recorded static reading, not a
version bump. The operator may veto it at proof exit. On a veto, Proof A
becomes `BLOCKED`, never `FAIL`, pending the smallest versioned decision:
PE-1.5, changing section 6.3 line 652 only, to read "any positive roster test
cannot be individually attributed from canonical output alone; rejection
outcomes are judged against the known roster and its test-to-marker mapping".
That would codify R2. R1 is not offered as an alternative, because by point 5
it cannot be run without a P-004 change, which is out of scope.

### A-STATIC: Per-Outcome Comparison with the Written Contract

The contract: P-004 (lines 86-99); harness-architect Step 4 item 3 (line 95)
and Step 5.2 (lines 124-153); manifest `TEST_COMMAND` =
`PYTHONPATH=src python -m unittest discover -s tests` and
`UNIMPLEMENTED_MARKER` = `raise NotImplementedError("...")` (lines 472-473);
compound `097-S` (canonical gate is `unittest`, not root `pytest`).

| # | Outcome | Under the written contract | Clause |
|---|---|---|---|
| P | Three named `ERROR`s, each with exactly its own `NotImplementedError` marker. Two non-roster tests pass | **Qualifies** (synthetic only). Each roster test is discovered and fails with its own marker. The exit is non-zero. Unrelated tests passing is not a violation | P-004 Precondition 2 ("Unrelated established tests ... may pass") and 3; Step 5.2 |
| - | `ERROR` versus `FAIL` | **Consistent.** Neither text uses unittest's categories. Both say "fails with its own expected failure marker" and define the marker as the `NotImplementedError` raise. "Fails" is the generic non-passing outcome attributed to that marker. An observation (`P3`, not a rewording request): the written text never names `ERROR` | P-004 line 86 and 92; Step 5.2 line 128-129; manifest line 473 |
| N1 | Marker-bearing `AssertionError` (`FAIL`) | **Refused.** Different exception type | Step 5.2 "Wrong-reason failure ... (a different exception type or message)"; P-004 line 98 "fails for a reason other than its own expected marker" |
| N2 | Pass | **Refused.** No red-phase observation for alpha | P-004 line 99; Step 5.2 "Pass ... false positive" |
| N3 | Skip | **Refused** | P-004 line 99; Step 5.2 "Skip or expected-failure" |
| N4 | `expectedFailure` | **Refused**, even though the stub raised the correct marker, because the decorator turns it into no observation | P-004 line 99; Step 5.2 "Skip or expected-failure (xfail)" |
| N5 | `unexpectedSuccess` | **Refused** | P-004 line 99; Step 5.2 "Pass or unexpectedSuccess" |
| N6 | Wrong marker | **Refused.** alpha's own marker is absent | P-004 line 98 "Missing, wrong ... markers"; Step 5.2 "different ... message" |
| N7 | Cross-test marker | **Refused.** alpha carries bravo's marker | P-004 line 98 "credited with a different test's marker" |
| N8 | One roster test not discovered | **Refused.** The exit is still non-zero | P-004 Precondition 3 "is discovered by that run"; Step 5.2 "MUST be discovered" |
| N9 | Roster-module import error | **Refused.** It is superficially red (exit 1, one `ERROR`), but the entry is the loader's `_FailedTest`, no roster test is exercised, and no marker is present | P-004 line 97 "Collection/import/syntax errors"; Step 5.2 "Collection/import/syntax failure" |

No required rejection qualifies. The first Fail disjunct is not triggered.

### Evidence Caveats

* **Relay, not raw.** Every runner fact above is Ship's parser projection of
  hashed raw stderr, relayed to Stage. Stage has not seen the raw stderr and
  did not reproduce any run. Confidence is therefore `medium`.
* **Tool-wrapper Temp spools.** Charter section 6.1 limits **Ship's**
  writes: "Ship's fixture writes go only inside" scratch, "Ship's only other
  write is the separate tool-managed index refresh", and "Every Ship write
  stays inside the current working directory" (lines 462-467). It also says
  "Large raw output ... is never written outside the recorded scratch
  directory" (line 515, in the bounded-projection context). Ship reports that
  the three spools were written by the tool wrapper automatically, were not
  issued by the agent, and held document, search and bounded summary output,
  with no raw runner or P-001 output. On that report Stage classifies them as
  **not a Ship write and not synthetic fixture data**. The runner's own temp
  files were redirected into scratch (`TEMP` and `TMP`). If the operator reads
  "Ship write" to include host-level tool plumbing, the constraint cannot be
  avoided. The host spools above an output-size threshold by itself, and it
  also writes the session transcript outside the working directory for every
  agent session, so no invocation could comply. The addendum (Tool-Wrapper
  Spool Interpretation) records Stage's reading of the text. **Disclosure:** during this
  Stage session the wrapper also spooled one Stage directory listing of
  scratch paths, sizes and timestamps to OS Temp
  (`...\AppData\Local\Temp\...-copilot-tool-output-...txt`). It was not runner
  output. It is recorded under the same classification. During the addendum
  session the wrapper spooled one more Stage read-only output to OS Temp: a
  `Select-String` over the driver source, a `.backlogit` file count and
  `git status --porcelain --ignored -- .backlogit`. It held no runner output
  and falls under the same classification.
* **Collector exit 5.** This is an evidence-tooling expectation error (31
  versus 41). It is not a runner result, and there was no re-execution.

## Addendum (2026-09-24): `PE-EVIDENCE-01` Record and Interpretations

**Scope.** This addendum sits on base commit `99e9ff5f`. It copies into this
artifact the `PE-EVIDENCE-01` facts that Ship already reported in its existing
handoff. There was no new Ship execution, and Stage re-ran nothing. Stage
edited no charter, plan or backlog, ran no proof runner, test or index sync,
and changed no verdict. Where Stage's own read-only corroboration appears, it
is labeled and is not Ship evidence.

### Host

| Field | Value (Ship-reported) |
|---|---|
| OS and version | Windows 11, 10.0.26200, SP0 |
| Filesystem | NTFS (`C:`) |
| Interpreter | Python 3.14.3, 64-bit |
| Proof A host requirement (section 6.2: Windows) | Met |

### Exact Runner Invocation (all ten cases)

| Field | Value |
|---|---|
| Canonical command | `PYTHONPATH=src python -m unittest discover -s tests`, once per case, each case in its own separately generated workspace |
| Python argv | `[sys.executable, '-m', 'unittest', 'discover', '-s', 'tests']` |
| cwd | That case's workspace root |
| env | `dict(os.environ, PYTHONPATH='src', PYTHONDONTWRITEBYTECODE='1')`, with `TEMP` and `TMP` set to `<workspace>/.tmp` |
| Flags or subset | None: no `-v`, no pattern, no subset |
| Driver launch | The driver reads no `sys.argv` (0 occurrences, Stage source read). It refuses to run anywhere other than the recorded scratch path. Its behavior is fixed by the script SHA-256 below. The shell line Ship typed to launch the driver is not quoted in the relayed handoff. `PE-EVIDENCE-01` needs the exact proof commands, and the ten runner commands above are those commands |

### Per-Run Results (Ship-reported)

Every run: native exit `1`. stdout was 0 B, SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

| # | Case | Exit | stderr bytes | stderr SHA-256 (full) |
|---|---|---|---|---|
| P | `positive` | 1 | 2118 | `1355b0031965152de9c9ee772f1df2a23c7c6d711d8aef7531e6430c734b0813` |
| N1 | `marker_assertion` | 1 | 2167 | `a9113aa1e276b1cd0229b9f20fed53462a0d92f13c78ad2c42ecef57cf09be40` |
| N2 | `passing_roster_test` | 1 | 1503 | `aaa2428f08a4a54683768f7b196f54a6d122237d03752e58ed01a1c29f8c3a79` |
| N3 | `skipped_roster_test` | 1 | 1514 | `acd2f0cf43643a7c3cf949c1a54f532dd472ea088f38189afe9348a8b084643d` |
| N4 | `expected_failure` | 1 | 1512 | `dec7fe2c9c2544a96c53bcad28665a04e25e35a93fbb5cdce371228bee34b529` |
| N5 | `unexpected_success` | 1 | 1677 | `c32b5a1373581e9f6aa30e95a45d5fcbfa8e9d88f3bb2ed17be76ed529af8d8c` |
| N6 | `wrong_marker` | 1 | 2136 | `b3ba137a47f7b57da53576bcb8c0333c387c90d878b77b87763713a92ce0d21d` |
| N7 | `cross_test_marker` | 1 | 2172 | `9d845b44a5f95a5b616f597a6d292c7aa72b3d50bbfb5f8f5676b147ed1ec350` |
| N8 | `zero_discovery_one_roster_test` | 1 | 1546 | `16d3f58eb409d5d2a01ea56e74ab8717c6063e92d8e35f430677f7c07beff6c6` |
| N9 | `roster_import_error` | 1 | 970 | `1e63f52ace3a2d8c620cdd6ec1af9d87620b53a20d98383f5513146dff7d5de5` |

Raw runner stderr was captured in the driver process's memory, and only
lengths, hashes and bounded projections were reported. No raw proof output
was written outside scratch.

### Driver, Collector and Refresh Executions

| Execution | Exit | stdout | stderr |
|---|---|---|---|
| Driver (`proof_driver.py`, 12521 B, `052447ac2a5c778c5d0555359d9bd1ea658335c618370de08fbac5a355b29e4a`) | 0 | 17466 B, `6ab05c082956edae6fe25d22f05b7cc9c332e7cdd9f7840d03b1e0eec8823932` | 0 B, `e3b0c442...b855` (empty) |
| Index refresh: exact CLI `backlogit sync` (the registered transport; native exit code) | 0 | 23 B, `cf46e51cd5d2efb42eed64050ed1021ad708c7bc50d4b54d51bcd0427d1ae873` | 0 B |
| Separate Ship evidence collector | 5 | Not relayed | Not relayed |

**Collector exit 5: disclosed, and outside the row.** The collector is not
one of the ten runner commands, not the driver and not the refresh. It is a
Ship post-hoc tally, and it exited 5 because it expected 31 generated files
where 41 exist (1 driver plus 10 workspaces with 4 files each, which Stage's
read-only re-hash confirms). The failure is in the collector's own
expectation. It is not a fixture or runner discrepancy. No A-runner or
A-static finding depends on the collector's output. The fixture listing comes
from the driver's hashed `FILE` lines and Stage's re-hash, and the runner
facts come from the driver. So the collector's missing stdout and stderr
digests leave no `PE-EVIDENCE-01` field empty. Nothing was re-executed
because of it.

### Timing

| Point | Value |
|---|---|
| Scratch stamp | 16:00:06 -07:00 |
| Fixture execution start and end (Ship) | 16:01:20 to 16:01:22 -07:00 |
| Driver-reported elapsed | 2.248 s |
| Stage findings commit `99e9ff5f` | 16:13:49 -07:00 |
| Combined Stage plus Ship | 13m49s (Ship-reported), or 13m43s measured from the scratch stamp. Either is at most 60m |

### Per-Invocation Gates and Safety Statement (Ship-reported)

| Gate | Result |
|---|---|
| P-010 self-check | Passed. Only scratch writes were authorized |
| P-002 | No claim and no `harness-ready` consumption |
| P-011 | Branch `chore/stage-176-s-workflow-defects` clean |
| P-016 | Exactly one worktree |
| P-001 | After the refresh, active counts were 0. `173-S` closure READY, compaction done |
| `PE-ACTIVATE-01` | The three blobs match `4acba14a` |
| Refresh footprint | Before the sync, the ignored footprint was `.backlogit/backlogit.db`, `-shm` and `-wal` only, each Git-ignored. These are exactly the cache paths that section 6.1 permits |
| `.backlogit` ignored status before and after fixture execution | Identical: 843 lines, SHA-256 `aa6f5600360375972f29839042057f64f3feb09078070494dbd513d862cd6517` |
| Tracked tree | Ship found it clean before the first write. Stage's `git status --porcelain` was empty when `99e9ff5f` was authored, after execution. The scratch directory is Git-ignored |

*Stage read-only corroboration, not Ship evidence.* When the addendum was
authored, `git status --porcelain --ignored -- .backlogit` returned 843 lines,
all `!!`. They include the three cache paths plus pre-existing ignored
`.lock` entries. The byte hash taken now (`028e25ce...`) is not compared with
Ship's, because Ship's capture method (encoding and line endings) is not
recorded, and lock files can change with time. Only the line count is
offered as corroboration.

### File-Bound Interpretation (Stage reading, not an operator sign-off)

Stage reads the Proof A bound "3 disposable" (section 6.2) as counting
**authored disposable scripts**, not the setup data that those scripts
generate as section 6.3 requires. Count: 1 authored script. On disk there are
41 files: the script plus 40 generated data files. The grounds come from the
charter text:

1. **Section 6.2 counts units that include generated trees.** Proof F's bound
   is "1 script, disposable repo". A disposable repository holds many files,
   so the table's unit is the authored artifact, not every file that
   artifact produces. Proof G run 2 took the same reading.
2. **Section 6.3 requires the setup data.** It requires a `src/` stub, three
   roster tests, an unrelated passing test, a characterization test and nine
   rejection variants, one of them a separately failing roster module. The
   40 generated files exist because the question requires them. The bound
   is not being used to buy extra scope.
3. **A literal count would reward weaker evidence.** *(This corrects the
   original Time and File Bounds text, which said a literal count "cannot
   fit".)* A literal three-file count could technically be met: one stub and
   one test module could be rewritten in place for each variant. But that
   would leave no retained per-variant fixture to hash. `PE-EVIDENCE-01`
   requires a fixture listing with a SHA-256 per file. A reading of the bound
   that pushes Ship to destroy the evidence another `P1` row demands is not a
   coherent reading of the charter as a whole.

This is Stage's interpretation, recorded for continued autonomous work. It is
not operator ratification, and Stage asserts none. If the operator prefers
the literal count at proof exit, `PE-SCOPE-07` makes run 5 `FAIL` (41 > 3).
That remains a residual unknown (Unresolved Gates, item 2).

### Tool-Wrapper Spool Interpretation (Stage reading, not an operator sign-off)

Section 6.1 bans raw proof output from being written outside scratch ("never
written outside the recorded scratch directory", line 517). Stage reads that
ban as applying to raw proof data, and here it was met: raw runner stderr
stayed captured in memory, and only lengths and SHA-256 were reported.
Section 6.1's "Ship's ... writes" (lines 462-467) is read as agent-directed
writes. The host tool wrapper automatically spooled document, search and
bounded summary output (three times in Ship's session, and twice more in
Stage's sessions, disclosed in Evidence Caveats). Those spools are host
plumbing, not agent-directed file writes and not raw runner output, so they
do not breach section 6.1. The disclosure is kept. This is Stage's
interpretation, not an operator sign-off. On a veto, the result is `BLOCKED`,
not `FAIL` (Unresolved Gates, item 3).

### Verdict After Addendum

**`PASS`** for the synthetic fixture only. It is unchanged, and the evidence
now in the record supports it. `PE-EVIDENCE-01` is met. The three Stage
interpretations (R2, the file-bound count and the spool classification) are
recorded, and none of them is presented as operator-approved.

## Time and File Bounds

| Bound | Charter | Recorded |
|---|---|---|
| Time (Stage plus Ship) | 60m | Ship's fixture execution ran from 16:01:20 to 16:01:22 -07:00, and the driver reported 2.248 s. The original findings commit `99e9ff5f` is stamped 16:13:49 -07:00. Ship reports 13m49s combined. Measured from the scratch stamp (16:00:06), the combined time is 13m43s. **Met** on either start reference. This addendum's commit is also before 17:00:06. Pooling with run 4 is not claimed, because section 3.3 line 352 gives each new run its own bound |
| File (3 disposable) | 3 | **Stage interpretation, not a charter change and not an operator sign-off.** The bound counts **authored disposable scripts**: 1 (`proof_driver.py`, 12521 B). It does not count the 40 generated data files that section 6.3 setup requires (41 files on disk in total). The grounds are in the addendum (File-Bound Interpretation). **Met under that interpretation.** Under a literal count of everything generated (41), `PE-SCOPE-07` makes run 5 `FAIL`. The operator may choose that reading at proof exit. Stage does not assert an overrun |

## Per-Criterion Verdict

| Criterion or row | Status |
|---|---|
| Section 6.3 Pass, A-runner: non-zero exit | Met (exit 1) |
| A-runner: each roster test individually identified with its own marker | Met (run P, three named `ERROR`s, each with exactly its own marker) |
| A-runner: the unrelated test does not affect the verdict | Met (anonymous pass, excluded by P-004 Precondition 2) |
| A-runner: the characterization test does not contaminate attribution | Met (anonymous pass, no marker, no named entry) |
| A-runner: classification shown | Met (`ERROR` for `NotImplementedError`, `FAIL` for `AssertionError`) |
| A-static: classification consistent with "fails with its own expected marker" | Met |
| Required rejections N1-N9 | Met. All nine refused |
| Fail disjuncts (qualifying rejection, unattributable positive, contradiction) | None triggered (R2) |
| Exact command, no `-v`, no subset, Windows method recorded | Met |
| `PE-EVIDENCE-03` | Met for Proof A. The runner half comes from Ship's actual execution in a synthetic source-layout workspace. The policy half is this static comparison. There is no actor claim and no gate-evidence claim |
| `PE-FLOW-02` | Not yet met at portfolio level. Proof A contributes `PASS`. Proof exit is not reached: the section 3.3 and section 10 runs still owed include PE-1.4 runs of B and E, and C run 2 is `BLOCKED` at `309ab0e2`. No Phase 2 artifact exists |
| `PE-EVIDENCE-01` | **Met (addendum).** Every listed field is now present, taken from Ship's existing handoff: question; host OS and version; filesystem; interpreter; the exact commands (ten runner argv, cwd and env, plus the refresh command); stdout and stderr lengths and SHA-256 for every runner, driver and refresh execution; the fixture listing with per-file SHA-256; the per-criterion verdict; elapsed time; file count; scratch path; per-invocation gate results, including the refresh record; and the safety statement. The collector's exit 5 is disclosed and falls outside the row (see the addendum) |
| `PE-AUTH-01` (both commits) | `99e9ff5f` and the addendum commit each change only this `docs/decisions/*-spike.md` file. Stage ran no fixture command, build, test, lint, index refresh or backlog mutation |
| `PE-AUTH-02` | Met on Ship's report: one worktree; refresh exit 0; P-001 after the refresh; P-010 authorized scratch writes only; P-002 had no claim and no `harness-ready` consumption; P-011 branch clean; P-016 |
| `PE-AUTH-03`, `PE-ACTIVATE-03`, `PE-SCOPE-04` | No authorization, P-004 red assertion, claim, `harness-ready` or publication assertion |
| `PE-ACTIVATE-01` | At authoring, `git rev-parse HEAD:<path>` gives `4ccd7fdc...`, `e22916b6...` and `251f46e8...` for the three paths, which equal `4acba14a`. The tracked tree is clean. Final check is at proof exit |
| `PE-SCOPE-07` | Time met. File bound met under the Stage interpretation (addendum) |
| `PE-FLOW-04` | Not engaged. Run 4 was a driver defect, not a `FAIL` |

## Unresolved Gates

1. **`PE-EVIDENCE-01` fields: closed by the addendum.** No re-run was needed.
2. **File-bound count.** Stage records its interpretation in the addendum. No
   operator sign-off is claimed. The operator can still veto it at proof exit.
   A veto would turn the verdict into `FAIL` under `PE-SCOPE-07` (41 files).
   Until the operator reviews it, the item is a residual unknown, not an
   asserted approval. Proof G shares this item.
3. **Tool-wrapper spool classification.** Stage records its interpretation in
   the addendum. No operator sign-off is claimed. If the operator vetoes it,
   the result is `BLOCKED` under the unavoidable host constraint stated in
   Evidence Caveats.
4. **R2 reading.** Recorded from the cited text. On an operator veto, the
   result is `BLOCKED` pending PE-1.5 (the section 6.3 line 652 wording
   above).
5. **Inadmissible-run time accounting** (charter section 3.2, line 230). This
   is still open in general. It is not needed for this verdict, because run 5
   has its own bound.
6. **Scratch hygiene.** Both `A-run4-...` and `A-run5-...` are retained,
   because no cleanup was approved. Ship removes them only under the section
   6.1 cleanup rule.
7. **Portfolio `PE-FLOW-02`.** Proof exit still needs the PE-1.4 runs owed for
   B and E, plus a resolution of C run 2 (`BLOCKED`). This is outside Proof A.

## Recommendation

**Conclusion**: proceed (to proof exit accounting only)
**Confidence**: medium

Record Proof A as `PASS` for the synthetic fixture under PE-1.4. Run 5 is the
first gate-valid, charter-complete positive observation. It has three `src/`
stub-backed roster tests, each attributed individually from default canonical
output with exactly its own marker. All nine required rejections, including
partial non-discovery and the import-error form, are refused under the written
P-004 and Step 5.2 text. The R2 reading is grounded in that text. Confidence is
medium rather than high for two reasons. First, Stage has not seen the raw
stderr: it holds Ship's parser projection plus full digests. Second, three
Stage interpretations (R2, the file-bound count and the spool classification)
are recorded without an operator sign-off. `PE-EVIDENCE-01` no longer lowers
confidence, because the addendum closes it.

## Next Steps

1. At proof exit, the operator reviews the R2 reading, the file-bound
   interpretation and the spool interpretation. Stage claims no approval of
   any of them.
2. Done: Stage copied the missing `PE-EVIDENCE-01` fields from the Ship
   handoff. The request for this addendum came later and named this existing
   artifact explicitly, so the fields are recorded here in place. That
   supersedes the earlier "new addendum artifact; this artifact is not edited"
   step. The addendum changes no verdict.
3. No actor invocation, `harness-ready` action, backlog item, shipment action,
   review, plan, attempt 12 or revision 13 is scheduled. `187-S` stays
   `queued`.

## References

* Charter: [2026-09-23-lifecycle-proof-entry-charter.md](2026-09-23-lifecycle-proof-entry-charter.md), sections 2, 3.2, 3.3, 6.1, 6.2, 6.3, 7.9, 8, 10
* Historical Proof A (PE-1.1, `BLOCKED`): [2026-09-23-p004-red-runner-proof-a-spike.md](2026-09-23-p004-red-runner-proof-a-spike.md)
* File-bound precedent: [2026-09-24-ordinary-path-containment-proof-g-spike.md](2026-09-24-ordinary-path-containment-proof-g-spike.md) (run 2 addendum), [2026-09-24-staged-blob-checksum-proof-f-run2-spike.md](2026-09-24-staged-blob-checksum-proof-f-run2-spike.md)
* Policy P-004: [workflow-policies.md](../../.github/policies/workflow-policies.md), lines 78-104
* Actor text: [harness-architect SKILL.md](../../.github/skills/harness-architect/SKILL.md), Step 4 item 3 (line 95) and Step 5.2 (lines 124-153)
* Manifest: [harness-manifest.yaml](../../.autoharness/harness-manifest.yaml), `variables_used.TEST_COMMAND` and `variables_used.UNIMPLEMENTED_MARKER` (lines 472-473)
* Compound: [097-S-canonical-unittest-gate.md](../compound/097-S-canonical-unittest-gate.md)
