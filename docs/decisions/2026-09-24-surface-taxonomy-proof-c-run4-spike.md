---
title: "Proof C run 4 - one-entry SurfaceSpec and total reason truth table: findings (PASS, PE-1.6)"
source: "docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md"
doc_type: decision
description: "Stage final adjudication of operator-authorized Proof C run 4 under charter PE-1.6 (sections 3.5, 6.1, 6.2 and 6.5). Verdict PASS. The run reused run 3's frozen two-file pair byte for byte. Stage re-read and re-hashed it inside run 4's clock and recorded FREEZE-OK. Ship ran it exactly once: native exit 0, failure_count 0, 47 of 47 codes reachable, 47 of 47 schema and surface branches produced, 9 of 9 mutants rejected. Stage independently reproduced the relayed stdout SHA-256. The 120-minute continuous bound held from T0 (the 22:24:25 authorization) to T1. Render parity false (fully resolved) goes to the operator as a follow-up. R-C3b stays disputed and is not assumed. A PASS ratifies none of the candidate proposals. Runs 1 to 3 keep their verdicts."
docline:
  type: spike
  date: 2026-09-24
  time_box: "120m"
  conclusion: "pass"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "surface-taxonomy"
    - "proof-c"
    - "pe-1.6"
---

# Proof C run 4: findings (PASS, PE-1.6)

## Verdict

**PASS.** Every section 6.5 pass condition (items 1 to 6) is met, and the
section 3.5 bound is met. T1 = 2026-09-24T22:37:06.287-07:00, and T1 − T0 = 12 m 41 s, which is
within the 120-minute limit. No fail clause applies. This PASS is Proof C's
effective evidence under PE-1.6. It ratifies none of the section 6.5
candidate proposals: the codes outside the governing set, the order within
classes 2, 3 and 5 to 7, the tie-break between declaration issues, and the
shape of `declarations` items.

## Time accounting (PE-1.6 section 3.5, continuous, no reset)

| Mark | Local time (2026-09-24, -07:00) | Source |
|---|---|---|
| **T0**: operator authorization "Proof C run 4 under PE-1.6" (earliest of Stage design, Ship work and authorization) | **22:24:25** | operator, relayed verbatim by the Orchestrator |
| First Stage design mark | 22:27:08.078 | Stage `Get-Date` |
| Stage HEAD and PE-ACTIVATE-01 blob check | 22:27:29.827 | Stage `Get-Date` |
| Stage design ended; directive issued | 22:28:20.900 | Stage `Get-Date` |
| Orchestrator set aside the `_ship.agent.md` edit (`git stash push`) | 22:29:05 | Orchestrator |
| Ship authoring invocation | 22:29:38 to 22:31:16 | Ship report |
| Stage FREEZE inspection started | 22:32:00.419 | Stage `Get-Date` |
| **FREEZE-OK** | **22:32:01.059** | Stage `Get-Date` |
| Ship execution invocation | 22:32:44.562 to 22:33:35.481 | Ship report |
| Single fixture execution | 22:33:22.144 to 22:33:28.558 (6.414 s) | wrapper output |
| Orchestrator restored the edit (`git stash pop`) | 22:34:22 | Orchestrator |
| Stage adjudication started | 22:34:55.641 | Stage `Get-Date` |
| **T1**: verdict line written | **2026-09-24T22:37:06.287-07:00** | Stage `Get-Date` |
| Deadline (T0 + 120 m) | 2026-09-25T00:24:25 | arithmetic |

Stage took the T1 `Get-Date` read in the same command that wrote this
verdict line's timestamps into the file, before any commit. Nothing paused
or restarted the clock. Run 4's budget does not pool with runs 1 to 3 or
with any Proof D run.

## Candidate and freeze

* **Candidate.** Run 3's frozen pair, reused as input under section 3.5
  item 6 with no edits. Stage re-read and re-hashed it from
  `.proof-scratch\C-run3-20260924-185023\` inside run 4's clock (22:27:08,
  binary Python read):
  * `c3_verify.py`: 44083 B, SHA-256 `f7bb864376fd39d8a769fa0dc8f8b347762d847e3948715decfcba96e19392e3`
  * `c3_schema.json`: 23483 B, SHA-256 `a659c4ad7e3fc91517c5348449703c2667c3ad33aa8d75de41d427749831b1d3`
* **Static check against section 6.5.** `CANDIDATE_GROUPS` lists the 47 section
  6.5 candidate codes in charter order (1 + 3 + 18 + 6 + 1 + 6 + 7 + 4 + 1).
  The `GOVERNING` literal equals the charter's governing table: 8 codes with
  their states, exits and classes. The verifier locates the repository and
  its schema from `__file__` (`parents[2]` and a sibling name), so it runs
  unchanged at the same depth under `.proof-scratch\`. It makes read-only git
  calls only (`rev-parse HEAD`, `show HEAD:<path>`) and writes no files.
* **Run-4 scratch directory.** Ship created
  `.proof-scratch\C-run4-20260924-222729\` new (ignored via
  `.gitignore:10`) and copied both files byte for byte. At FREEZE-OK Stage
  re-hashed both with a binary read. They match the values above, and the
  directory holds exactly these two files, with no hidden entries or
  subdirectories. Ship re-confirmed both hashes and the two-file listing
  before and after execution.
* **Real-surface inputs.** `git diff --stat 4acba14a HEAD` is empty for
  `.autoharness/harness-manifest.yaml`,
  `.github/skills/harness-architect/SKILL.md` and
  `templates/skills/harness-architect/SKILL.md.tmpl`.

## Evidence recorded

* **Host:** Microsoft Windows 11 Enterprise (NT 10.0.26200.0), NTFS.
  Interpreter `C:\Python\Python314\python.exe` 3.14.3, jsonschema 4.26.0,
  PyYAML 6.0.3, git 2.55.0.windows.5. `PYTHONPATH` was unset. The command
  ran from the repository root `C:\Source\GitHub\autoharness` at `HEAD`
  `cd2ef2618c65ec98d49e5cbe7b4c7f0c8f9693d7`.
* **Exact command.** One execution with no retry. An inline stdin wrapper,
  which wrote no file, ran
  `subprocess.run([sys.executable, "-B", "-X", "utf8", r".proof-scratch\C-run4-20260924-222729\c3_verify.py"], capture_output=True)`
  and exited with the child's return code.
* **Wrapper output (verbatim, Ship-relayed):**

  ```text
  START=2026-09-24T22:33:22.144-07:00 END=2026-09-24T22:33:28.558-07:00 ELAPSED_S=6.414 EXIT=0
  STDOUT_LEN=1052 STDOUT_SHA256=5d75c454752d8a787a4c6e8ef3e51ada03d5951961fb71a25620bfb08d3e7324
  STDERR_LEN=0 STDERR_SHA256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  LASTEXITCODE=0
  ```

* **Raw stdout (verbatim, Ship-relayed; one line, CRLF-terminated):**

  ```json
  {"charter":"docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md#6.5","charter_version":"PE-1.5; Proof C candidate remains PE-1.4","counts":{"candidate":47,"governing":8,"labels":8,"manifest_order":30,"mutants":9,"pairs":2162,"reachability":47,"read_cross_stage_pairs":294,"read_pairs":42,"read_single":21,"reference_47_difference":0,"schema_branches":47,"surface_branches":47},"failure_count":0,"failure_examples":[],"failure_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","r_c3b":{"id":"R-C3b","later_completed_recheck_O":"INPUT_CHANGED_DURING_RESOLUTION","note":"Separate early-return variant only; Decision 2 items 2 and 5 leave this interaction unresolved.","read_limit_first_variant":"FILE_COUNT_LIMIT","status":"DISPUTED_NOT_ASSUMED"},"real_surface":{"checksum_match":true,"head":"cd2ef2618c65ec98d49e5cbe7b4c7f0c8f9693d7","manifest_closure":true,"render_parity":false,"render_reason":"evaluated","unresolved":[]},"state_split":{"HARNESS_READY":2,"NO_HARNESS":4,"UNRESOLVED":41},"status":"NO_FIXTURE_FAILURE"}
  ```

  Raw stderr: empty (0 B).
* **Stage cross-check of the relay.** Stage hashed the relayed JSON text
  with a CRLF terminator (Windows text-mode `print` to a pipe). It is 1052 B
  with SHA-256 `5d75c454...3d7324`, equal to the relayed `STDOUT_LEN` and
  `STDOUT_SHA256`. The relayed bytes therefore match the executed output.
  Stage did not run or import the fixture.
* **Fixture listing and file count:** 2 files, `c3_verify.py` and
  `c3_schema.json`, with the hashes above. No other file was written.
* **Gates (Ship-reported, before authoring, before execution and after
  execution):**
  * `backlogit sync` exited 0 and indexed 1472 artifacts (CLI).
  * Checkpoints: 71 in total, 70 resolved, 1 abandoned (the known `ship`
    one), 0 active, 0 needing quarantine, 0 quarantined.
  * Shipments: 69, none active.
  * 173-S closure READY, compaction done.
  * One worktree; branch and `HEAD` unchanged at `cd2ef261`.
  * No source, backlog, claim, PR or push mutation. The only mutation was
    the backlogit index cache refresh.
* **Comparison with run 3's stdout.** Run 3's stdout was also 1052 B, but its
  SHA-256 was `7da03bd3...2f56c`. The report has no timestamps. Its one
  run-dependent field is `real_surface.head`, a fixed-width 40-hex value, so
  a hash change with the same length is expected. Run 3's artifact records
  only that truncated hash and not the raw bytes, so Stage cannot confirm
  from the record that `head` is the only differing field. Run 3's output is
  not run-4 evidence (section 3.5 item 6), so this has no bearing on the
  verdict.

## Per-criterion adjudication (section 6.5)

| # | Criterion | Evidence | Result |
|---|---|---|---|
| 1 | Enumeration: each input class maps to exactly one outcome. The label classes are supported, `none`, missing, duplicate, malformed, mixed and unknown-but-well-formed; unknown gives `SURFACE_UNSUPPORTED`, which is UNRESOLVED and never NO_HARNESS. Manifest failure precedence is fixed | `labels` 8: the 7 classes, with two unknown-but-well-formed cases (`harvest`, `impl-plan`), each asserted to give UNRESOLVED. `manifest_order` 30 = 6 × 5 ordered pairs of manifest failures, each checked against the independent oracle. `failure_count` 0 | Met |
| 2 | Governing-set check, run against the governing constant: each code is present, reachable, has the right state and exit, and validates. Each read-limit code at any stage gives UNRESOLVED/2 with that code. Two read-limit errors in both orders give the first one | `governing` 8. `read_single` 21 = 3 codes × 7 stages. `read_pairs` 42 = 6 ordered pairs × 7 stages. `read_cross_stage_pairs` 294 = 6 × 7 × 7. `failure_count` 0 | Met |
| 3 | Closure: every candidate code is reachable, and precedence is a strict total order apart from the class 1b first-occurrence rule | `reachability` 47. `pairs` 2162 = 47 × 46 ordered pairs. `candidate` 47, `reference_47_difference` 0. `state_split` 2 / 4 / 41 equals the section 6.5 reference | Met |
| 4 | Schema parity: every output validates, every schema branch is produced, and mutants are rejected, including `READ_BUDGET_EXHAUSTED` and a class 1b code replaced by a non-read-limit code | `schema_branches` 47, `surface_branches` 47. `mutants` 9: the retired `READ_BUDGET_EXHAUSTED` code, a read-limit code replaced by `MEMBERS_TOO_MANY`, a missing read stage, wrong state, wrong exit, an extra property, an unknown read stage, a checksum-mismatch/INVALID surface mismatch, and an enum-deletion control. Each is required to be rejected by both the predicate and the schema. `failure_count` 0 | Met |
| 5 | Real-surface controls from Git blobs at `HEAD` `cd2ef261`: (a) manifest closure, (b) checksum reported separately, (c) render parity from the top-level `variables_used` only | (a) `manifest_closure` true. (b) `checksum_match` true. (c) `render_parity` false with `render_reason` evaluated and `unresolved` `[]`. The verifier reads `manifest.get("variables_used")`, the top-level mapping, never an artifact entry. It encodes the render as UTF-8 and compares bytes with the raw installed blob | Met. Render parity `false` is an operator follow-up, not a FAIL (see below) |
| 6 | Evidence (`PE-EVIDENCE-01`): native exit plus stdout and stderr length and SHA-256 for every execution | One execution: exit 0 (`LASTEXITCODE` 0), stdout 1052 B / `5d75c454...`, stderr 0 B / `e3b0c442...`. Stage reproduced the stdout hash from the relayed bytes | Met |
| — | Section 3.5 bound: T1 − T0 ≤ 120 m | T0 22:24:25, T1 2026-09-24T22:37:06.287-07:00, elapsed 12 m 41 s | Met |

**Fail clause check.** None of the fail conditions occurred:

* no input mapped to zero or more than one outcome;
* no governing or candidate code was unreachable;
* no governing code was missing, renamed or remapped;
* no read-limit error gave a different code;
* schema and runtime agreed;
* render parity was computed from the top-level mapping and reported
  `false` only with full resolution;
* the bound was met.

## Observations (not Proof C conditions)

* **Render parity `false` (operator follow-up).** The real `harness-architect`
  surface fails byte-exact render parity although every placeholder resolved.
  This is the known observation from runs 2 and 3, with the first difference
  at byte 4994 (a line reflow). Section 6.5 item 5 records it for the
  operator; it does not make Proof C fail. Stage did not loosen the byte
  comparison or touch any production surface.
* **R-C3b `DISPUTED_NOT_ASSUMED`.** The fixture keeps one interaction
  separate: a read-limit error followed by a later completed recheck that
  gives `INPUT_CHANGED_DURING_RESOLUTION`. The early-return variant gives
  `FILE_COUNT_LIMIT`; the oracle gives `INPUT_CHANGED_DURING_RESOLUTION`. It
  is reported, not counted as a failure, and neither answer is assumed.
  Section 6.5 does not decide this interaction. Its class 1b rule covers the
  first occurrence among read-limit codes only, and the fixture's note says
  Decision 2 items 2 and 5 leave it unresolved. It is therefore outside the
  section 6.5 pass list. Run 3's artifact did not mention it. This PASS does
  not settle it, and it stays open for an architecture or operator ruling.
* **Stale `charter_version` label.** The frozen verifier reports
  `"charter_version":"PE-1.5; Proof C candidate remains PE-1.4"`. PE-1.6
  changed only the clock and bound, not the candidate or the pass list, so
  the label is a report annotation and not a criterion. It was left as is
  to keep the frozen hash. This run was adjudicated under PE-1.6
  (`cd2ef261`).

## Working-tree disclosure

The operator made uncommitted edits to three files. The operator's
statement at 22:24:25 was: "I manually made the edits, which conveys implicit
operator approval".

| File | Change |
|---|---|
| `.autoharness/config.yaml` | Lines 74-76 and 83-85 of `model_routing` (the Orchestrator and Ship route blocks) change from `gpt-6-sol`/xhigh/openai and `gpt-6-luna`/openai/xhigh to `claude-opus-5.5`/anthropic/high. The new lines carry a copied "Stage role route" comment |
| `.github/agents/_orchestrator.agent.md` | Frontmatter route lines only |
| `.github/agents/_ship.agent.md` | Frontmatter lines 8-10 (`reasoning_effort`, `model_provider`, `model_family`) change to high/anthropic/`claude-opus-5.5` |

* **Why one edit was set aside.** PE-ACTIVATE-01 requires
  `.github/agents/_ship.agent.md` to be at blob `e22916b6...` with no
  uncommitted change.
* **Set-aside.** The Orchestrator ran `git stash push --
  .github/agents/_ship.agent.md` at 22:29:05. The stash entry was
  `stash@{0}`, with message "operator-approved ship routing edit (set aside
  for Proof C run 4 PE-ACTIVATE-01)".
* **Check during Ship's invocations.** Ship confirmed before its first write
  and again after execution that the three blobs match `4ccd7fdc...`,
  `e22916b6...` and `251f46e8...` and that the scoped `git status
  --porcelain` output was empty.
* **Restore.** A first `git stash pop` attempt at 22:34:16 failed before
  doing anything: PowerShell parsed the unquoted `stash@{0}` and git
  reported "unknown switch `e'". The quoted `git stash pop 'stash@{0}'` at
  22:34:22 restored the edit and dropped stash `1f6fbac8`. The working-tree
  blob of `_ship.agent.md` is `66933efa` again.
* **Untouched.** The unrelated operator stash "On main: operator WIP before
  173-S bootstrap" was not touched. `config.yaml` and
  `_orchestrator.agent.md` are not PE-ACTIVATE-01 paths and stayed modified
  throughout.
* **Routing.** The Ship route is resolved from config, not from frontmatter
  (P-013.5 H8).
* **Not committed.** Stage did not commit, revert or stage any of the three
  files. The untracked `docs/scratch/2026-09-24-workflow-defects-session-pickup.md`
  (written by the Orchestrator) is not part of this commit.

## Degraded surfaces

* **Intercom, Engram and graphtor-docs:** not probed by Stage or Ship in this
  run, so their state is unverified. They are recorded as degraded or
  unverified, not as absent. Operator visibility went through the
  Orchestrator relay.
* **backlogit:** Ship used the CLI, not MCP; `sync` exited 0. Stage made no
  backlog reads or writes in this proof run, and stash triage, harvest and
  shipment steps do not apply to an Orchestrator-directed proof turn.

## Matrix rows

| Row | Status after run 4 |
|---|---|
| `PE-INTERFACE-03` | Met by Proof C run 4 (PASS, PE-1.6) |
| `PE-DATA-01` | Met by Proof C run 4 (PASS, PE-1.6) |
| `PE-DATA-02` | Met by Proof C run 4 (PASS, PE-1.6) |
| `PE-EVIDENCE-01` | This run records the required fields (question, host, filesystem, interpreter, command, raw output and hashes, fixture listing, per-criterion verdict, elapsed time, file count) |
| `PE-FLOW-04` | Proof C part: run 4 re-asks run 3's failed question only after the PE-1.6 version bump, so it complies. Stage does not declare the whole row met, because the Proof D run 4 breach (`36f65975`) stays on the record and needs an operator ruling (section 3.5) |
| `PE-ACTIVATE-01` | No activation. The three blobs equal the `4acba14a` setup snapshot before and after, and the scoped porcelain check was empty during Ship's invocations |

## Prior runs (carried forward, not re-labelled)

* Proof C run 1: `FAIL` (PE-1.3, `9d0ed834`).
* Proof C run 2: `BLOCKED` (PE-1.4, `309ab0e2`).
* Proof C run 3: `FAIL` (PE-1.5, `f23b9549`, time bound). Its single execution
  stays unassessed evidence, not a PASS. Run 4 does not turn it into one.
* Proof D run 5: `PASS`, synthetic contract (PE-1.5, `5976ff62`).
* Every other verdict listed in charter sections 3.4 and 3.5 stands.

## Routing

PASS closes the Proof C question under PE-1.6. Open items for operator or
architecture ruling:

1. The render-parity `false` result on the real `harness-architect` surface
   (byte 4994 reflow).
2. R-C3b: whether a read-limit error that occurs first beats a later
   completed `INPUT_CHANGED_DURING_RESOLUTION` (Decision 2 items 2 and 5).
3. The section 6.5 candidate proposals, which this PASS does not ratify.
4. `PE-FLOW-04`: a prospective reading of the Proof D run 4 breach.
5. Cleanup of Proof C scratch directories. The run 1 to 4 directories stay
   in place as hash-pinned evidence until the operator approves their
   cleanup.

This artifact does not change the backlog, the charter, Ship surfaces,
config, claims or PRs, and it starts no further proof run.
