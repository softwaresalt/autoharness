---
title: "Ship lifecycle release units A to D (rebaselined plan, LIFECYCLE-E3 subject)"
description: "Single governing plan for the four C2 release units that succeed the retired 187-S / 181-F: A (P-002/P-004 and actor evidence conformance with per-task semantics), C (portable ordinary-containment reader, Windows and Linux), B (one-entry SurfaceSpec resolver, result schema and CLI, delivered as two shipments, B-core and B-entry, to stay within budget) and D (Ship-side validated-document consumer and the one-task, one-commit Ship activation). Every ratified implementation-matrix row IM-01 to IM-17 is mapped to a unit, a task and a verification. Carries the Decision 1 admitted bound (1..48 members, max_files 256, C_max 202, margin 54, no byte fit), the class 1b read-limit mapping, the OD-11-ratified 47-code list and precedence, the OD-10 early-return rule with the IM-16 both-order tests, P-002/P-004 TDD under the ratified R2 reading, the non-waivable Linux-native gate IM-01 and the section 9 budgets (at most 6 tasks and 8 hours per shipment). C does not fold into B: the combined unit would exceed both budgets. Shipments are sequenced A -> C -> B-core -> B-entry -> D with A as the only dag-root, and S(D) also waits on the separate IM-10 shipment. Revision 4 is the subject of epoch LIFECYCLE-E3, scoped to the IM-14 non-claim audit after the E2 epoch stop and the operator-ratified spike (27bcc254); not publication-eligible; not implementation-ready until a LIFECYCLE-E3 PASS."
doc_type: plan
source: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
date: 2026-09-25
plan_id: ship-lifecycle-release-units
plan_path: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
plan_role: active
revision: 4
status: pending-review
prior_revision: {revision: 3, commit: bd7002d5, blob: ffa663de030a0a07baa5b62ea1078b750a0a4009}
review_epoch: LIFECYCLE-E3
review_manifest: docs/reviews/2026-09-25-ship-lifecycle-release-units-plan-review.md
review_epoch_family: LIFECYCLE-E3
review_epoch_token_rule: "LIFECYCLE-E3-<first 8 hex of this file's reviewed blob SHA-1>, fixed at epoch open in the review manifest"
publication_eligible: false
implementation_ready: false
requires_plan_hardening: yes
hardening_status: hardened
hardening_pass: "plan-harden run as its own pass on 2026-09-25 (revision 1), and its checks re-run over every section revisions 2, 3 and 4 touched"
supersedes_plan: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
supersedes_note: "The revision 12 plan is the frozen diagnostic record for the retired 187-S / 181-F (charter section 4.2, PE-SCOPE-01). It is not edited. This plan does not restate it and does not inherit any of its contracts except where a section below cites it as a frozen diagnostic input."
governing_sources:
  - {path: docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md, relation: "architectural rule, containment scope (Option D), issue taxonomy, gates, budgets, Phase 2 table"}
  - {path: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md, commit: e65887d8, relation: "PE-1.7; sections 5, 6.3 to 6.9, 7, 9"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md, commit: a04dea18, relation: "implementation matrix IM-01 to IM-17"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings.md, commit: 928bf3ff, relation: "OD-3 (R2 ratified), OD-5, OD-9"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-2.md, commit: 2634bac2, relation: "matrix ratified; C2 approved; C3 retire 187-S; C4 lead gpt-6-sol"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-3.md, commit: 347771bd, relation: "OD-4, OD-12; C4 P2 rule"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-4.md, commit: b8a7b100, relation: "OD-11 47-code list ratified; IM-17 closed"}
  - {path: docs/decisions/2026-09-25-read-limit-early-return-r-c3b-decision.md, commit: 8fa08913, relation: "OD-10 early return; IM-16 both-order tests"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-5.md, commit: 2ca9d9a5, relation: "section 9 items 1 to 5 ratified; epoch parameters frozen; Go"}
  - {path: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md, commit: 286aa4af, relation: "Decision 1 bound; Decision 2 class 1b mapping"}
  - {path: docs/decisions/2026-09-25-187-s-retirement-mechanics-c3-record.md, commit: 1610e181, relation: "C3 retirement; successor pointers into this plan"}
  - {path: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md, relation: "portfolio map; D4, D9, D11; P-004 plan blocked_on"}
matrix_version: "IM-01 to IM-17 (a04dea18 rows; ratified 2634bac2; IM-17 closed b8a7b100; IM-16 decided 8fa08913); proof-entry matrix PE-1.7 (e65887d8)"
source_stash_id: 76EBDE6D
portfolio_stash_ids: [3EF5AAF2, 14F4D6F3, 86498B64, 76EBDE6D, C9CD24F3, 7F9CB5E9, 71200CBB]
related_stash_ids: [9144435A]
retired_carriers: [187-S, 181-F, 181.002-T, 181.003-T, 181.004-T, 181.005-T, 181.006-T, 181.007-T, 181.008-T, 181.009-T, 181.010-T, 181.011-T, 181.012-T, 181.013-T, 181.014-T, 181.015-T, 181.016-T, 181.017-T]
release_units:
  - {unit: A, shipment: S(A), tasks: 2, minutes: 170, dag: root}
  - {unit: C, shipment: S(C), tasks: 5, minutes: 435, dag: "after S(A)"}
  - {unit: B, shipment: S(B-core), tasks: 3, minutes: 280, dag: "after S(C)"}
  - {unit: B, shipment: S(B-entry), tasks: 3, minutes: 275, dag: "after S(B-core)"}
  - {unit: D, shipment: S(D), tasks: 4, minutes: 395, dag: "after S(B-entry) and the IM-10 shipment; D3 also gated on IM-01"}
c_folds_into_b: false
harvest_gate: "Harvest only after a LIFECYCLE-E2 review PASS recorded in the review manifest. Not before."
labels:
  - ship-lifecycle
  - harness-architect
  - containment
  - resolver
  - p-004
  - release-units
---

# Ship lifecycle release units A to D

## Bottom Line

| Question | Answer |
|---|---|
| What is this? | The **single governing plan** for the four C2 release units that succeed the retired `187-S` / `181-F`. One plan, four unit sections, one review manifest, reviews kept outside this file |
| What does it deliver? | A: the P-002/P-004 and actor evidence contract made true and testable, per task. C: a portable ordinary-containment reader. B: a one-entry `SurfaceSpec` resolver with a closed 47-code result, schema and CLI. D: a Ship-side consumer that trusts only a validated document, and the one-task, one-commit Ship activation |
| Order | **A -> C -> B -> D**, as five shipments: S(A) -> S(C) -> S(B-core) -> S(B-entry) -> S(D). A is the only `dag-root`. S(D) also waits on the separate IM-10 shipment |
| Does C fold into B? | **No.** B alone needs 550 minutes and ships as two shipments. C adds 5 tasks and 435 minutes (see [Budgets](#release-units-and-budgets)) |
| Linux | IM-01 is a **non-waivable** release gate for C, B and D. Windows evidence never satisfies it |
| Status | Revision 3, consolidated revision 2 of 2 of `LIFECYCLE-E2-R1-2d562820` (findings in the review manifest). Not publication-eligible. Not implementation-ready. No backlog item exists yet |

## Authority and Status

* **Authority chain.** Charter PE-1.7 and the ratified implementation matrix
  -> the convergence-reset deliberation and rulings 1 to 5 -> **this plan**
  -> (after a review `PASS`) harvested carriers -> the review manifest
  `docs/reviews/2026-09-25-ship-lifecycle-release-units-plan-review.md` ->
  immutable per-epoch review artifacts under `docs/reviews/review-history/`.
  Each fact lives in one place. Carriers will cite this plan and restate no
  verdict.
* **Single-governing-plan contract.** This file is selected by its
  `plan_id` and `plan_role: active`. Review findings, rebuttals and verdicts
  are never appended here. They live in the review manifest and its
  immutable history artifacts. A revision replaces this file's content as a
  coherent current state; it is not a correction log.
* **Frozen record.** The revision 12 plan, its review manifest, attempts 07
  to 11 and the P-004 observation-gate plan and review (including its lock
  file) are not edited by this plan or by any task in it.
* **What this plan does not decide.** Anything outside the ratified matrix.
  A requirement not in the matrix is `CHANGE`, not a blocker. A new API,
  subsystem, threat class or platform mechanism requires a re-charter.

## Problem Frame

Ship has no executable way to know, before a task, whether the harness actor
surface it depends on is present and current, and it has no written rule
that makes the P-004 red-phase evidence both satisfiable and checkable per
task:

* **Evidence contract.** P-004 was re-scoped to the current task in
  `d8b04112`, but P-002's postcondition still says "all tests fail with
  expected failure markers" (`.github/policies/workflow-policies.md`, P-002
  section). Neither P-002, P-004 nor
  `.github/skills/harness-architect/SKILL.md` Step 5.2 defines the per-task
  expected-RED roster under the ratified R2 reading, names the
  marker-bearing `AssertionError` as refused, or carves characterization
  tests out of the roster. So a characterization-first task can never pass
  P-004 as written (the second obstruction of stash `76EBDE6D`).
* **No resolver.** `src/autoharness/harness_read.py` and
  `src/autoharness/harness_surfaces.py` do not exist. `src/autoharness/cli.py`
  has no `harness` command, and its unknown-command path exits `1`, which is
  also the `NO_HARNESS` exit code. A process status alone therefore proves
  nothing (Proof B).
* **Ship placement.** The template runs harness generation "once, up front -
  not in a loop" and the installed mirror has no `harness-architect`
  reference at all (Proof E anchors). The template also restores memory
  context before checkpoint validation.

Revision 12 bundled a handle-relative reader, the resolver and the activation
into 16 tasks and 24.75 hours. The reset replaced the reader with ordinary
containment (Option D) and split the work into independently valuable units.

## Fixed Inputs (not re-opened by this plan)

| ID | Input | Value | Source |
|---|---|---|---|
| FI-1 | Admitted membership | `custom_fields.items` is a list of **1..48** unique IDs. 49 or more is `MEMBERS_TOO_MANY` -> `UNRESOLVED / 2`, rejected before any member lookup, with at most 4 file claims | Decision 1 (`286aa4af`) |
| FI-2 | Read limits | `max_files=256`, `max_file_bytes=4 MiB`, `max_total_bytes=32 MiB`. File claims and byte reservations are never refunded. Every recheck is a new claim | Decision 1; charter 6.6 |
| FI-3 | Budget equation | `C(N,U,rho) = 4(N+1) + 3U(1+rho)`; `C_max = C(48,1,1) = 202`, margin 54; margin rule `C(N,U,1) + (N+1) <= 256`. **No byte fit is claimed.** Byte exhaustion is a bounded `UNRESOLVED / 2` | Decision 1; Proof D run 5 (`5976ff62`) |
| FI-4 | Class 1b | A read-limit error (`FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT`) at any stage -> `UNRESOLVED / 2` with that `ReadErrorCode` as `reason_code`; diagnostics keep the native code and the `ReadStage`. Never stable absence, never a surface classification, never agreement | Decision 2 items 1 to 4 |
| FI-5 | Early return | On the **first** read-limit error the resolver issues **no further read or recheck request**. A recheck that **completed** with a disagreement **before** it gives `INPUT_CHANGED_DURING_RESOLUTION` (class 1). A recheck whose own read ends in a read-limit error has not completed and is neither agreement nor disagreement | OD-10 decision (`8fa08913`) |
| FI-6 | Reason list and precedence | The 47-code section 6.5 Stage candidate, **ratified with no revision** (items a to d), hash-pinned: candidate block SHA-256 `64c41cd150dde7273506e0a2b179a04187bb80139216b14b5fe898cb896b6847`, governing block SHA-256 `cba91a303c24edf4b88a0a907d5caf8ca6c695a33c2b5cd256e1b7cba7f9f0cf` (LF-joined lines; charter `52c985cb` lines 717-749, byte-identical at `e65887d8` lines 1222-1254). Class order 1, 1b, 2 to 8; listed order within a class is precedence; class 1b is first-occurrence. State split 2 `HARNESS_READY` / 4 `NO_HARNESS` / 41 `UNRESOLVED`. `declarations` items are `{member_id, surface_id}`, both required strings, `additionalProperties: false`, sorted by task ID | OD-11 (`b8a7b100`) |
| FI-7 | Proven schema | Proof C run 4 fixture pair, frozen: `c3_schema.json` SHA-256 `a659c4ad7e3fc91517c5348449703c2667c3ad33aa8d75de41d427749831b1d3`, `c3_verify.py` SHA-256 `f7bb864376fd39d8a769fa0dc8f8b347762d847e3948715decfcba96e19392e3` (kept under OD-6). Its "provisional" note on `declarations` is superseded by FI-6 item (d) | Proof C run 4 (`4c6e2701`) |
| FI-8 | One surface | Exactly one supported mapping: `harness-architect` -> installed `.github/skills/harness-architect/SKILL.md`, template `skills/harness-architect/SKILL.md.tmpl` (manifest entry at `.autoharness/harness-manifest.yaml` line 237). Every other well-formed surface -> `SURFACE_UNSUPPORTED` -> `UNRESOLVED` | `PE-INTERFACE-03` |
| FI-9 | RED evidence (R2) | The canonical command `PYTHONPATH=src python -m unittest discover -s tests`, exactly, no `-v`, no subset. RED for a roster test is that test reported as `ERROR` with its own unique `NotImplementedError` marker (see [Marker Convention](#marker-convention)). Attribution is roster-relative: a roster test absent from the named `ERROR` set, or named with a different marker, is refused. Refused always: marker-bearing `AssertionError`, pass, skip, `expectedFailure`, `unexpectedSuccess`, wrong or cross-test marker, zero discovery, collection or import error | Proof A run 5 (`99e9ff5f`, `4d132bf9`); OD-3 (a) (`928bf3ff`) |
| FI-10 | Threat model and non-claims | Ordinary hazards only: malformed or escaping paths, static links outside a root at read time, oversized input, non-regular targets. **No artifact claims race, TOCTOU or hardlink-alias resistance** | Reset deliberation, containment scope; `PE-SAFETY-06`, IM-14 |
| FI-11 | Platforms | Windows (NTFS) and Linux (Linux-native filesystem), each verified by tests executed on that OS. Linux in CI on a Linux runner. Mocks and simulation are not evidence | Section 6.9; IM-01 |
| FI-12 | Activation comparator | `08787a4b`: template blob `4ccd7fdc2d134de485487acd75bfbc105d6f40ee`, mirror blob `66933efaf085e7acff0db47f0bdc452a4fe58830`, manifest blob `e4274043e66a104ca8cf9f43e0d4e939847ac30e` | PE-1.7 section 3.6; IM-08 |
| FI-13 | Recovery order and restore contract | Enumerate, anomaly check, unique selection, owner validation, confirmation, restore, prune, resume, then resolution. Post-activation restore contract rules 1 to 4 | Charter 6.7 (PE-1.3, PE-1.5) |

## Release Units and Budgets

| Shipment | Content | Independent value | Tasks | Minutes | Within budget |
|---|---|---|---:|---:|---|
| S(A) | P-002/P-004 policy and harness-architect actor text: per-task expected-RED roster (R2), `harness-surface` task scoping, characterization carve-out | The evidence contract is true, per task, and checked by structural tests | 2 | 170 | Yes |
| S(C) | Portable ordinary-containment reader, Windows and Linux, plus the Linux-native CI gate and the non-claim audit | Required containment and bounds, executed on both hosts | 5 | 435 | Yes |
| S(B-core) | B1 to B3: result contract, 47-code registry, schema mirrors, records and membership, manifest classification | The published result contract, plus tested record and surface classification | 3 | 280 | Yes |
| S(B-entry) | B4a to B5: ledger and digest, reducer with early return, `resolve_shipment`, CLI | A working, callable, schema-valid resolver | 3 | 275 | Yes |
| S(D) | Ship-side validated-document consumer, Ship structural tests, one-task one-commit activation, post-activation recovery fixture | The lifecycle goes live, fail-closed | 4 | 395 | Yes |

**B is split in two, and C does not fold into B.** The review re-estimate
(IM-11-F01) put B at 550 minutes, over the 480-minute limit. Section 9
allows only a split, never a seventh task or a stretched estimate. B-core
and B-entry are serial and share one module. C+B would be 11 tasks and 985
minutes. Any further growth in a shipment escalates per P-013.6.

### Marker Convention

Each task's `Marker` value is a **prefix**. Every roster test `t` has its
own marker `<prefix>:<t>`, where `<t>` is its Proof G case ID or test
method name. It reaches a RED-phase stub that raises exactly
`NotImplementedError("<prefix>:<t>")`. The stub is either per behavior, or
derives the suffix deterministically from the test's distinct request.
The harness asserts the roster's markers are pairwise distinct, and the RED
record maps each roster test to its marker. Two roster tests sharing one
marker is a cross-test marker, which FI-9 refuses. Structural tests that
reach no stub (API, docstring, schema parity, pinned hash, alias, audit)
are recorded outside the roster, like characterization tests.

## Requirements Trace (implementation matrix)

Every ratified row maps to a unit, a task and a named verification. Rows
predesignated `P2-critical` are marked. Severity and deferral are as ratified.

| Row | Sev | Requirement (short) | Unit / task | Verification |
|---|---|---|---|---|
| IM-01 | P1, non-waivable | Linux-native execution of the full Proof G case set in CI | C5 (gate); precondition of shipping C, B and D | C5's CI job on `ubuntu-latest` runs the four containment modules with `TMPDIR` exported; the job fails on a non-zero unittest exit or any skipped test, and records `platform.system()`, the kernel and the filesystem type of the effective fixture root. The Proof G case-ID coverage test (C5) proves G01 to G32 each map to a named test |
| IM-02 | P1 | Cross-platform acceptance | C5 + D3 preflight | Windows: Ship's local run of the containment modules on NTFS, recorded. Linux: IM-01 CI evidence. D3 halts if either is missing |
| IM-03 | P1 | Closed taxonomy and result schema, schema-parity-complete; reproduce 47 codes, 2/4/41, 9 mutants | B1, B5 | B1: registry equals FI-6 (governing constant held separately), derived counts, schema branch per code, 9 mutant rejections. B5: all 47 codes through the real reducer `_resolve` (small limits for read-limit codes), and through `resolve_shipment` and the CLI every code reachable with the defaults; every output validates |
| IM-04 | P1 | Admitted `1..48`, `max_files=256`, no byte fit, `UNRESOLVED / 2` at every stage; plus multi-error first-code, byte-code applicability at absent candidates, precedence without short-circuit | B2 (bound), B4b (stages and the three tests) | B2: 1, 48 admitted; 49, 512, 513 -> `MEMBERS_TOO_MANY` with at most 4 claims and zero member lookups. B4b: injection at each of the 7 `ReadStage` values; the three limitation tests named in [B4b](#b4b-reducer-early-return-and-resolver-entry) |
| IM-05 | P1 | Bounded raw reads loop to EOF or cap+1; same measure on both OSes | C3 | cap, cap+1, 4096 B over cap, total and count tests; unbuffered binary reads on both hosts, with every raw read request bounded by the remaining limit + 1; short reads continue the loop; `\r\n\x1a` bytes returned unchanged |
| IM-06 | P1 | No public or caller-supplied traversal adapter; test seams private | C1 (API), C3 (usage seam) | API test asserts the public names and that no public callable accepts an adapter or opener parameter. The private patch points are named in [Unit C](#unit-c-portable-ordinary-containment-reader) and [B4b](#b4b-reducer-early-return-and-resolver-entry) |
| IM-07 | P1 | Ship consumes a validated document; resolve CR-B1 to CR-B5 | D1 (consumer and handoff); D2 (Ship refusal); B5 (stderr rule, CR-B5) | D1: the Proof B impostor table plus float `exit_code` (CR-B3), deep nesting (CR-B4), duplicate keys and `NaN` -> `resolver-not-observed`; the handoff test runs the real B5 CLI for exits 0, 1 and 2 plus an impostor through D1's capture contract. D2: after `resolver-not-observed`, Ship runs no T2, T3 or Claim. B5: stderr is empty on every post-parse `--json` path |
| IM-08 | P1 | Activation of template, mirror and manifest checksum is one task and one commit against `08787a4b`; restore contract; session-start recovery invocation (E L6); C1-C6 wiring (E O4) | D3 | D2's structural tests go green only with D3; D3 preflight blob checks; `git show --name-only` of D3's commit lists exactly the three paths |
| IM-09 | P2, operator-deferrable | Post-activation recovery fixture closes E L1, L3, L4, L5 | D4 | Fixture over the rendered mirror form, an unknown event failing closed, and each previously unexercised branch |
| IM-10 | P1 | Reconcile the `harness-architect` render mismatch in its own operator-approved unit before any byte-exact render-parity resolver runs against it at HEAD | **Outside A to D** (stash `9144435A`); a `blocks` predecessor of S(D); gate in D3 | S(D) is not claimable until the IM-10 shipment has shipped ([Dependency Graph](#dependency-graph)). D3 preflight, as a second check: the real resolver over a real shipment returns `HARNESS_READY / 0 / ALL_SURFACES_PRESENT`; otherwise D3 halts. B's tests use fixtures only, never the real surface at HEAD |
| IM-11 | P1 | At most 6 tasks and 8 hours per shipment; independent value; two-axis sizing | Harvest (all units) | [Budgets](#release-units-and-budgets) table (B split into two shipments); harvest writes `size` and `complexity` on every task |
| IM-12 | P1 | Manifest checksums from raw staged-blob bytes | A1, A2, D3 | Before refresh, the recorded checksum equals the SHA-256 of `HEAD:<path>`, else halt on drift. Python subprocess with binary capture of `git cat-file -p :<path>` before commit and `HEAD:<path>` after; `git add --renormalize` only when an `eol=lf` pin is added; no PowerShell text capture |
| IM-13 | P1 | P-004 RED uses the exact canonical command and per-test marker attribution under R2 | A1, A2 (text); every `harness-surface:harness-architect` task (practice) | A1/A2 structural tests; each code task's RED record (task ID, exact command, native exit, per-roster-test outcome and its own marker per the [Marker Convention](#marker-convention)) before implementation |
| IM-14 | **P2-critical** | No artifact claims race, TOCTOU or hardlink-alias resistance | All units | The one [non-claim audit](#non-claim-audit-inventory): C5 creates it, later tasks add `LEDGER` entries and floor files, closures extend `AUDITED`, and D3's preflight and each closure run it with no skip |
| IM-15 | P1 | Publication, execution and claim/closure gates distinct; a test or proof `PASS` confers no claim authority | All units | No carrier or artifact asserts claim readiness from a review or test result; ordinary P-001/P-002/P-004/P-020 gates at claim and closure |
| IM-16 | P1 | Early return decided; test both orders | C3 (usage seam), B4b (private limits hook) | Test (a) disagreement first -> `INPUT_CHANGED_DURING_RESOLUTION`; test (b) read-limit first -> the read-limit code, native code and stage in diagnostics, and **zero** further claims after the first limit error; (b) covers all three codes and each feasible stage; infeasible stages recorded with reasons |
| IM-17 | P1 (closed) | The ratified 47-code list is the contract; no revision | B1 | B1's registry test compares against a constant copied from the hash-pinned block; any difference fails |

Proof-entry rows that constrain the implementation directly:

| Row | Sev | Unit / task | Verification |
|---|---|---|---|
| `PE-SAFETY-01` | P1 | C1 | Every Proof G lexical case (22 Windows variants; the Linux set) -> `LEXICAL_INVALID` with zero resolve calls |
| `PE-SAFETY-02` | P1 | C2 | Junction and symlink escapes rejected; in-root links accepted; the Windows symlink sub-case alone may skip, with the reason recorded, when the host lacks symlink privilege; the junction case never skips |
| `PE-SAFETY-03` | P1 | C2 | Both roots; case-insensitive root comparison on Windows; `commonpath` over `normcase`, never a string prefix; a `commonpath` `ValueError` (different drive) -> `OUTSIDE_TRUST_ROOT` |
| `PE-SAFETY-04`, `05` | P1 | C3 | Explicit exhaustion codes; no silent truncation or partial success |
| `PE-SAFETY-06` | **P2-critical** | All (with IM-14) | The [non-claim audit inventory](#non-claim-audit-inventory) |
| `PE-SAFETY-07` | **P2-critical** | C1 (reserved names), C4 (non-regular) | Directory, FIFO (G31, Linux), device node and junction-to-directory -> `NOT_REGULAR_FILE`; reserved device names -> `LEXICAL_INVALID` |
| `PE-INTERFACE-01` | P1 | C1 | As IM-06 |
| `PE-INTERFACE-03` | P1 | B2 | Unknown-but-well-formed surfaces -> `SURFACE_UNSUPPORTED` -> `UNRESOLVED` |
| `PE-DATA-01` to `03` | P1 | B1, B2, B4b, B5 | As IM-03 and IM-04 |
| `PE-ACTIVATE-02` | P1 | D3 | As IM-08 |
| `PE-TASK-02` | P1 | Harvest | As IM-11 |

## Unit A: Evidence Contract Conformance

**Goal.** Make the written P-002/P-004 and actor contract match the ratified
evidence shape (FI-9), per task, so every later code task's RED evidence is
both satisfiable and checkable. No executable RED observer is built here: the
P-004 observation gate stays in its own blocked plan.

### A1: P-002 and P-004 per-task roster wording

| Field | Value |
|---|---|
| Files | `templates/policies/workflow-policies.md.tmpl`; `.github/policies/workflow-policies.md`; `.autoharness/harness-manifest.yaml` (the policy entry's checksum and note only); `tests/test_harness_architect_p004_contract.py` (extend `PolicyQuantifierCoherenceTests`) |
| Change | P-002 postcondition: scope "all tests fail" to the current task's expected-RED roster, matching P-004. P-004: (1) define the roster as the current task's generated harness tests, excluding characterization tests, which are recorded separately and may pass; (2) state that RED for a roster test is `ERROR` with its own unique `NotImplementedError` marker in canonical output, attributed roster-relatively (R2); (3) add the marker-bearing `AssertionError` to the refused list; (4) state that a task declaring `harness-surface:none` has no roster and no RED obligation, and that `harness-surface:none` is allowed only for a task whose file budget contains no Python production module under `src/`. Add a version-history row. Template and installed file carry the same text; placeholders stay placeholders in the template |
| Verification | Structural tests: both files state each of (1) to (4), the [Marker Convention](#marker-convention) and the canonical command verbatim; the installed file equals the template render for the edited sections, compared over LF-normalized text because the template is not `eol=lf` pinned; the recorded checksum equals `HEAD:<path>` before refresh, and the refreshed checksum equals the raw staged-blob SHA-256 (IM-12); markdownlint passes |
| Posture | characterization-first on the existing contract tests. The new structural tests' pre-edit failing run is recorded as gap characterization, not RED, then edit |
| Label | `harness-surface:none` (text only) |
| Estimate | 75 min; size `M`; complexity `medium` |

### A2: harness-architect per-task semantics

| Field | Value |
|---|---|
| Files | `templates/skills/harness-architect/SKILL.md.tmpl`; `.github/skills/harness-architect/SKILL.md`; `.autoharness/harness-manifest.yaml` (this entry's checksum and note only); `tests/test_harness_architect_p004_contract.py` |
| Change | Step 1 selects exactly **one current task** supplied by the caller; the actor never claims backlog work. Step 3: a characterization-first harness is recorded outside the roster. Step 5.2: the roster rule, the `ERROR` classification and the R2 attribution from A1, and the marker-bearing `AssertionError` refusal, and the [Marker Convention](#marker-convention). Step 6: `harness-ready` applies to the current task only, with an evidence record (task ID, exact command, native exit, each roster test's outcome and marker, characterization tests listed apart). Edits are applied as parallel hunks to template and installed file. **The installed file is not re-rendered:** the existing byte-4994 line-reflow mismatch is left for the IM-10 unit |
| Verification | Structural tests over both files for each rule above, over LF-normalized text; the recorded checksum equals `HEAD:<path>` before refresh, and the refreshed checksum equals the raw staged-blob SHA-256; markdownlint passes |
| Posture | characterization-first. The pre-edit failing run is recorded as gap characterization, then edit |
| Label | `harness-surface:none` |
| Estimate | 95 min; size `M`; complexity `medium` |

A1 blocks A2 (A2 cites A1's wording). Both touch the manifest, so they are
serial.

## Unit C: Portable Ordinary-Containment Reader

**Module.** `src/autoharness/harness_read.py`, new, internal to the resolver.

**Public surface (closed).**

* `TrustRoot`: `WORKSPACE`, `AUTOHARNESS` (`<workspace>/.autoharness`).
* `ReadErrorCode`: `LEXICAL_INVALID`, `OUTSIDE_TRUST_ROOT`,
  `PATH_NOT_FOUND`, `NOT_REGULAR_FILE`, `FILE_SIZE_LIMIT`,
  `TOTAL_SIZE_LIMIT`, `FILE_COUNT_LIMIT`, `IO`. These are the Proof G codes
  plus `IO` for an ordinary operating-system read failure. The revision 12
  codes `RACE`, `IDENTITY_MISMATCH`, `REPARSE_POINT`, `ROOT_OPEN_FAILED`,
  `COMPONENT_LIMIT`, `SESSION_CLOSED` and `PLATFORM_INVARIANT_UNAVAILABLE`
  are not carried.
* Frozen `ReadLimits` with the FI-2 defaults; frozen `ReadUsage`
  (`files_claimed`, `bytes_reserved`); frozen `ReadResult` (`data` bytes on
  success only, else `error` with a code and a root-relative, redacted path).
* `open_reader(*, workspace_root, limits=None) -> Reader` with
  `read_bytes(root, relative_path) -> ReadResult` and read-only `usage`.
  There is **no adapter, opener or callback parameter** anywhere (IM-06).
  Tests use real temporary directories. The private patch points are
  exactly `_is_contained(root, target)` (C2) and `_read_chunk(fd, n)` (C3);
  tests patch no other module function; C1's resolve counter and C3's open counter only spy on `os.path.realpath` and `os.open`.

**Order of checks per request.** Lexical (no filesystem access) -> file
claim (one slot, never refunded; over the count limit -> `FILE_COUNT_LIMIT`
before any open) -> resolve -> containment -> regular-file check -> bounded
read. Containment is judged before existence, so a dangling link that points
outside is `OUTSIDE_TRUST_ROOT` and one that points inside is
`PATH_NOT_FOUND`.

### C1: Contracts and lexical rejection

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_read.py`; `tests/test_harness_read_lexical.py` |
| Change | The public surface above; lexical rules evaluated identically on every host: empty; NUL or other control characters; POSIX-absolute, rooted `\`, drive-qualified and drive-relative (`C:x`); UNC and `\\?\`, `//?/`, `\\.\` prefixes; `..` anywhere in the split components (both slash styles, per `docs/compound/2026-05-05-path-traversal-validation-parts.md`); alternate data streams (`:`); reserved device stems (`CON`, `NUL`, `COM1`, and so on, case-insensitive, with or without extension); trailing dot or space. All -> `LEXICAL_INVALID` with no resolve and no claim. The module docstring carries the fixed non-claim sentence (see the [inventory](#non-claim-audit-inventory)) |
| Verification | One test per Proof G lexical case (G01 to G13, G24), each named with its case ID; a resolve-call counter over a real directory shows zero resolves; the API test for IM-06; the docstring sentence is present |
| Marker | `AHLC_C1_READ_LEXICAL` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 80 min; size `S`; complexity `medium` |

### C2: Static roots and resolved-path containment

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_read.py`; `tests/test_harness_read_containment.py` |
| Change | Resolve both roots once per reader. Resolve each target with `os.path.realpath`; compare with `os.path.commonpath` over `os.path.normcase` forms (case-insensitive on Windows) inside the private `_is_contained`; never a string prefix. A `commonpath` `ValueError` (different drive or mixed prefix forms) means not contained -> `OUTSIDE_TRUST_ROOT`. Links inside the root are followed and accepted; links that resolve outside are rejected |
| Verification | Proof G G14 to G23, G30, G32 on each host: in-root accept with exact bytes; directory junction out (Windows, mandatory, created with `mklink /J` in a subprocess) rejected; in-root junction accepted; file and directory symlinks out rejected; in-root symlink accepted; dangling in -> `PATH_NOT_FOUND`, dangling out -> `OUTSIDE_TRUST_ROOT`; upper-case root spelling accepted on Windows; `AUTOHARNESS` escape via a junction into the workspace rejected. A sentinel file outside both roots never appears in any result. On Windows, symlink cases alone may skip with the recorded reason when the host lacks symlink privilege. On Linux, each junction case (G15, G16, G21b, G23, G30b) runs under the same case ID with a directory-symlink analogue and the same expected code, so the Linux run has no skip (C5). On Linux, the upper-case root case runs under the same ID as a case-sensitivity check: an in-root file requested through a root spelled in a different case -> `PATH_NOT_FOUND`. `_is_contained` over `C:\ws` and `D:\x` returns false without raising |
| Marker | `AHLC_C2_READ_CONTAINMENT` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 110 min; size `S`; complexity `medium` |

### C3: Bounded reads and read budget

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_read.py`; `tests/test_harness_read_bounds.py` |
| Change | Open unbuffered and binary on both hosts: `os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0))`, read only through the private `_read_chunk(fd, n)` (`os.read`), never through a buffered file object. Take the size from `os.fstat` on the open handle. If it exceeds `max_file_bytes` -> `FILE_SIZE_LIMIT`; if it exceeds the remaining total -> `TOTAL_SIZE_LIMIT`; both before reading. Reserve that size (never refunded). Read in a loop until EOF or until `min(max_file_bytes, remaining) + 1` bytes are held, never requesting more than that bound minus the bytes held; if more bytes arrive than were reserved, charge them and re-apply both limits. Return data only when the loop reached EOF within both limits. Every failure discards the bytes |
| Verification | G25 to G29 on each host: exactly 64 B accepted; 65 B and 4096 B over a 64 B cap -> `FILE_SIZE_LIMIT` after reading at most cap+1 bytes; total 64+64 accepted then `TOTAL_SIZE_LIMIT`; three accepts then `FILE_COUNT_LIMIT` with zero opens. Patching `_read_chunk` records every requested size (each within the bound; at most 65 bytes requested in total for the 4096 B file) and returns short reads, which the loop continues through. A fixture of `b"\r\n\x1a"` plus padding is returned byte-exact on Windows (no text mode). `usage` never decreases |
| Marker | `AHLC_C3_READ_BOUNDS` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 100 min; size `S`; complexity `medium` |

### C4: Non-regular targets

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_read.py`; `tests/test_harness_read_nonregular.py` |
| Change | After containment, `os.stat` the resolved path; anything not `S_ISREG` -> `NOT_REGULAR_FILE` before open. C3's open carries `O_NONBLOCK` on POSIX, so a FIFO present at read time cannot block the read; the post-open `fstat` must still be `S_ISREG`. This is ordinary input rejection, not a race defense (FI-10) |
| Verification | Directory and junction-to-directory (G30a, G30b) -> `NOT_REGULAR_FILE`; Linux FIFO (G31, `os.mkfifo`) -> `NOT_REGULAR_FILE` within a bounded time; Linux device node: a reader opened with `workspace_root=/dev` reading `null` -> `NOT_REGULAR_FILE` (containment passes, so the regular-file check decides), and an in-root symlink to `/dev/null` under a temporary workspace -> `OUTSIDE_TRUST_ROOT`, because containment precedes the regular-file check; missing file and missing parent (G32a, G32b) -> `PATH_NOT_FOUND` |
| Marker | `AHLC_C4_READ_NONREGULAR` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 65 min; size `S`; complexity `low` |

### C5: Linux-native gate and case coverage

| Field | Value |
|---|---|
| Files | `.github/workflows/ci.yml` (one new step in the existing `ubuntu-latest` test job); `tests/test_harness_read_case_coverage.py`; `tests/test_harness_noclaim_audit.py` |
| Change | The CI step uses `shell: bash`, `set -euo pipefail` and `export TMPDIR="$RUNNER_TEMP"`. It unshallows a shallow checkout (`git fetch --unshallow`), then runs `PYTHONPATH=src python -m unittest -v tests.test_harness_read_lexical tests.test_harness_read_containment tests.test_harness_read_bounds tests.test_harness_read_nonregular tests.test_harness_noclaim_audit` with output captured to a log file, records the exit code and fails on non-zero, then fails unless the summary is `OK` with no `skipped=`. It prints `platform.system()`, `uname -r`, and `stat -f -c %T` of the checkout and of the effective fixture root (`python -c "import tempfile; print(tempfile.gettempdir())"` under the same environment), asserts that root is under `$RUNNER_TEMP`, and fails unless both types are `ext2/ext3` (ext4), `xfs` or `btrfs` (so `tmpfs`, `overlayfs`, `9p` and `fuse` fail). The coverage test asserts every Proof G case ID G01 to G32 appears in at least one test name, G31 is Linux-only, and every other ID has a variant that runs on both hosts. The audit test implements the [non-claim audit](#non-claim-audit-inventory) |
| Verification | The pull request's CI log for the new step, with the job URL, runner OS, kernel, the unittest exit code, the effective fixture root, both filesystem types and zero skips, recorded by Ship as IM-01 evidence. The `test` job is path-gated and `ci gate` treats a skipped `test` job as OK, so the evidence must show the step itself executed; a green `ci gate` alone is not IM-01 evidence. Stage runs none of it |
| Label | `harness-surface:none` for the workflow step; the coverage and audit tests are structural |
| Estimate | 80 min; size `S`; complexity `low` |

`-v` appears only in this CI evidence step. It is not the P-004 canonical
command and is never used as RED evidence.

## Unit B: One-Entry Resolver, Schema and CLI

**Module.** `src/autoharness/harness_surfaces.py`, new. One resolver
invocation opens one reader and uses its budget throughout.

**Resolver `ReadStage`** (diagnostics only): `SHIPMENT_CANDIDATE`,
`MEMBER_CANDIDATE`, `MANIFEST`, `TEMPLATE`, `INSTALLED`,
`CANDIDATE_RECHECK`, `SURFACE_RECHECK` (Decision 2 item 1).

**Reader-error mapping (adds no code).** A read-limit error is class 1b at
any stage (FI-4, FI-5). Other reader codes map inside the ratified list:

| Stage | `PATH_NOT_FOUND` | `LEXICAL_INVALID`, `OUTSIDE_TRUST_ROOT`, `NOT_REGULAR_FILE`, `IO` |
|---|---|---|
| Shipment candidate | Stable absence (both absent -> `SHIPMENT_NOT_FOUND`) | `SHIPMENT_RECORD_INVALID` |
| Member candidate | Stable absence (both absent -> `MEMBER_NOT_FOUND`) | `MEMBER_RECORD_INVALID` |
| Manifest | `MANIFEST_NOT_FOUND` | `MANIFEST_UNREADABLE` |
| Template | `TEMPLATE_NOT_FOUND` | `TEMPLATE_UNREADABLE` |
| Installed | `INSTALLED_NOT_FOUND` (surface `MISSING`) | `INSTALLED_UNREADABLE` (surface `INVALID`) |
| Recheck | Compared as an observation | Recheck not completed -> the original stage's code; never agreement |

**Template root.** Templates are read from `<workspace>/templates/` through
the `WORKSPACE` root. A workspace without it yields `TEMPLATE_NOT_FOUND`
(fail-closed). Reading package-home templates would add a trust root, which
is a re-charter.

### B1: Contracts, reason registry and schema mirrors

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_surfaces.py`; `schemas/harness-resolution.schema.json`; `schemas/harness-resolution/1.0.0.schema.json`; `src/autoharness/schema_contracts.py`; `tests/test_harness_resolution_contract.py`; `tests/test_harness_noclaim_audit.py` |
| Change | Frozen result types, the state/exit table, `ReadStage`, and the 47-code registry with class, state and exit, in listed order (FI-6). The result field set is that of the proven `c3_schema.json` (FI-7), with `declarations` as ratified. Both schema files are new and equal except `$id` (the root file's `$id` names the unversioned path, the mirror's names `harness-resolution/1.0.0`), `additionalProperties: false`, closed enums, one `oneOf` branch per code binding state and exit; register the contract with `current_version` `1.0.0` (per `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`) |
| Verification | Registry equals a test-local constant copied from the hash-pinned block, and the governing 8 codes from a second constant, never derived from the registry; derived counts 47 and 2/4/41 recorded; the two schema files are equal after removing `$id`, and the `1.0.0` mirror's SHA-256 over LF-normalized bytes is pinned in the test; every code has exactly one schema branch; the 9 Proof C mutants are rejected, including `READ_BUDGET_EXHAUSTED` and a class 1b code replaced by `MEMBERS_TOO_MANY`; B1's paths are added to the audit inventory |
| Marker | `AHLC_B1_RESOLUTION_CONTRACT` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 85 min; size `M`; complexity `medium` |

### B2: Backlog root, records, membership and declarations

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_surfaces.py`; `tests/test_harness_surfaces_records.py` |
| Change | Backlog root: `.backlog/` or legacy `.backlogit/`; neither -> `BACKLOG_ROOT_NOT_FOUND`; both -> `BACKLOG_ROOT_AMBIGUOUS`. The two fixed names are probed with `os.path.isdir` under the workspace root; a probe is not a file claim. `BACKLOGIT_WORKSPACE_DIR` and `backlog_root.py` are not used, so no override can select a root. Shipment ID syntax, then both exact candidates (`queue/<id>.md`, `archive/<id>.md`); exactly one present; frontmatter `id` and `artifact_type` must agree. `custom_fields.items` 1..48 unique (FI-1); feature and task members only; features never expand; at least one task. Each task declares exactly one `harness-surface:<id>` label or `harness-surface:none`; feature members declare none; class 3 tie-break in listed order; an unknown well-formed surface -> `SURFACE_UNSUPPORTED` |
| Verification | One fixture per class 2 and class 3 code; 1 and 48 admitted; 49, 512, 513 -> `MEMBERS_TOO_MANY` with `usage.files_claimed <= 4` on the reader the test passes in, and no member candidate read; mixed, duplicate, malformed and missing declarations; class 3 tie-break fixtures in which listed order disagrees with both task-ID order and first-encountered order; with `BACKLOGIT_WORKSPACE_DIR` set, the result is unchanged |
| Marker | `AHLC_B2_RECORDS_MEMBERSHIP` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 95 min; size `S`; complexity `medium` |

### B3: Manifest snapshot and surface classification

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_surfaces.py`; `src/autoharness/verify_workspace.py` (alias only); `tests/test_harness_surfaces_manifest.py`; `tests/test_harness_noclaim_audit.py` |
| Change | Only when the surface union is non-empty. One manifest read and one YAML parse through a `yaml.SafeLoader` subclass that rejects duplicate mapping keys (`MANIFEST_DUPLICATE_KEY`), decode (`MANIFEST_DECODE_INVALID`), YAML (`MANIFEST_YAML_INVALID`) and shape (`MANIFEST_SHAPE_INVALID`) checks; a global failure emits no per-surface rows. Per surface, in order: zero path matches -> `MISSING` / `MANIFEST_ENTRY_NOT_FOUND`; several -> `INVALID` / `MANIFEST_ENTRY_AMBIGUOUS`; template mismatch -> `INVALID` / `MANIFEST_TEMPLATE_MISMATCH`; then template read and render with the manifest's one top-level `variables_used` mapping through the existing pure renderer, called via a new module-level alias `verify_workspace.render_template` bound to `_render_template` (one grammar; UTF-8, LF), unresolved placeholders -> `INVALID` / `TEMPLATE_VARIABLE_UNRESOLVED`; installed missing -> `MISSING`; render or checksum disagreement -> `STALE` (`RENDER_MISMATCH` or `CHECKSUM_MISMATCH`); both equal -> `PRESENT` |
| Verification | One fixture per class 5, 6 and 7 code, all in temporary workspaces; no test reads the real repository surface (IM-10); a duplicate key nested below the top level is rejected; `render_template is _render_template`; B2's and B3's paths are added to the audit inventory |
| Marker | `AHLC_B3_MANIFEST_CLASSIFY` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 100 min; size `S`; complexity `medium` |

### B4a: Observation ledger, recheck and digest

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_surfaces.py`; `tests/test_harness_surfaces_digest.py` |
| Change | Ledger every present or absent candidate and every surface read. After the provisional result, re-observe the ledger through the same reader (new claims). A completed recheck that disagrees -> class 1. `inputs_sha256`: 64 lowercase hex over a domain-separated canonical preimage of the request, both candidates per record including stable absence, raw selected records, manifest, template and installed observations, normalized declarations and the result projection without the digest itself; deterministic order |
| Verification | Digest stability across runs and platforms (LF bytes); every bound input changes the digest; a mutated record between read and recheck -> `INPUT_CHANGED_DURING_RESOLUTION`; both first and recheck observations are bound on mutation; one golden fixture pins the exact `inputs_sha256` hex |
| Marker | `AHLC_B4A_LEDGER_DIGEST` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 85 min; size `S`; complexity `medium` |

### B4b: Reducer, early return and resolver entry

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_surfaces.py`; `tests/test_harness_surfaces_reducer.py` |
| Change | The keyword-only entry `resolve_shipment(*, workspace_root, shipment_id)`, which calls the private `_resolve(*, workspace_root, shipment_id, limits)` with the FI-2 defaults. `_resolve`'s `limits` is the only B patch point (IM-06); no public caller can pass limits. `_resolve` returns the result and the reader's `ReadUsage`; `resolve_shipment` returns only the result. Reducer order 1, 1b, 2 to 8 with first-applicable selection (FI-6). Early return (FI-5): the first read-limit error stops all further read and recheck requests |
| Verification | IM-16 and IM-04 tests call `_resolve` with small `ReadLimits` so every read-limit code is reachable (with the defaults, `FILE_COUNT_LIMIT` is not). **IM-16 (a)**: a completed disagreeing ledger recheck, and separately a completed disagreeing surface recheck, each followed by a read-limit error -> `INPUT_CHANGED_DURING_RESOLUTION`. **IM-16 (b)**: for each of the three read-limit codes and each feasible stage, a read-limit error first with a later recheck arranged to disagree -> that code, native code and stage in diagnostics, and `usage.files_claimed` unchanged after the error; infeasible stages recorded with the reason (for example, byte codes at an absent candidate). **IM-04**: two read-limit errors in both orders -> the first-occurring code at the reducer; byte codes never raised at an absent candidate; each higher class beats every lower class, with the lower-class fact first in both encounter and task-ID order, without short-circuiting the collection of lower-class facts |
| Marker | `AHLC_B4B_REDUCER_EARLY_RETURN` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 110 min; size `S`; complexity `medium` |

### B5: CLI adapter

| Field | Value |
|---|---|
| Files | `src/autoharness/cli.py`; `tests/test_harness_resolve_cli.py`; `tests/test_harness_noclaim_audit.py` |
| Change | `harness resolve --workspace <path> --shipment <id> --json`. Parse errors behave as ordinary argparse (usage on stderr, exit 2, no document); `--help` prints help to stdout, exits 0 and emits no document. After a successful parse, `--json` writes exactly one UTF-8 document followed by one LF, as `sys.stdout.buffer.write(doc + b"\n")`, writes nothing to stderr (CR-B5), and exits with the document's `exit_code`. B4a's to B5's paths and the captured `harness resolve --help` text are added to the audit inventory |
| Verification | All 47 codes through `_resolve` (small limits for read-limit codes); every code reachable with the defaults also through `resolve_shipment` and the CLI; every output validates against the B1 schema (IM-03); stdout is exactly one document plus one LF; stderr is empty on every post-parse path; exit equals `exit_code`; parse errors emit no JSON |
| Marker | `AHLC_B5_CLI_ENVELOPE` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 80 min; size `S`; complexity `medium` |

Serial inside B: B1 -> B2 -> B3 -> B4a -> B4b -> B5 (one module, shared
file). S(B-core) holds B1 to B3 and S(B-entry) holds B4a to B5.

## Unit D: Validated Consumer and Ship Activation

### D1: Ship-side validated-document consumer

| Field | Value |
|---|---|
| Files | `src/autoharness/harness_verdict.py`; `tests/test_harness_verdict.py`; `tests/test_harness_verdict_handoff.py`; `tests/test_harness_noclaim_audit.py` |
| Change | `accept_resolution(*, requested_shipment, process_status, stdout: bytes, stderr: bytes) -> Accepted | NotObserved`. **Capture contract:** Ship runs `harness resolve ... --json` with stdout and stderr each redirected as raw bytes to its own file under the Git-ignored `.proof-scratch/harness-resolve/`, records the native exit status, then runs `python -m autoharness.harness_verdict --shipment <id> --status <int> --stdout-file <path> --stderr-file <path>`. The entry reads both files as bounded bytes and prints exactly one line: `accepted <state> <reason_code> <exit_code>` (exit 0) or `resolver-not-observed <sub-code>` (exit 1); an entry usage error (exit 2) is also not observed. Ship deletes both files after the entry returns. Accepted only when stdout holds exactly one UTF-8 JSON document followed by at most one LF, schema-valid against B1, with shipment, state, reason, `exit_code` and process status all consistent, and stderr empty. Otherwise the literal outcome `resolver-not-observed` (CR-B2) with a diagnostic sub-code. Sub-codes are diagnostics only; nothing branches on them (CR-B1). `exit_code` must be a JSON integer token, never a float such as `1.0` (CR-B3). Parsing is total: bounded input size, nesting depth bounded before `json.loads`, and `RecursionError` or `MemoryError` -> `resolver-not-observed` (CR-B4). `object_pairs_hook` rejects duplicate keys and `parse_constant` rejects `NaN` and `Infinity`. The module is added to the audit inventory |
| Verification | The Proof B impostor table (startup failure, unknown command, usage error, help text, empty stdout, malformed JSON, two documents, leading or trailing output, status/document mismatch, shipment mismatch, schema-invalid), plus float `exit_code`, deep nesting, oversized input, duplicate keys, `NaN` and a second trailing LF -> `resolver-not-observed`; one genuine document per state accepted. **Handoff test:** the real B5 CLI runs in a subprocess over fixture workspaces giving exits 0, 1 and 2, and an impostor (`harness bogus`, argparse exit 2) is also run; each capture goes through the entry in a subprocess, and the printed line and exit code are asserted |
| Marker | `AHLC_D1_VERDICT_CONSUMER` (prefix) |
| Label | `harness-surface:harness-architect` |
| Estimate | 110 min; size `S`; complexity `medium` |

### D2: Ship structural tests

| Field | Value |
|---|---|
| Files | `tests/test_ship_harness_activation.py`; `tests/fixtures/ship_activation/expected_anchors.json`; `tests/test_harness_noclaim_audit.py` |
| Change | Tests over both Ship surfaces for the post-activation text: the per-task pre-claim step (T1 resolve under D1's capture contract, including its capture path and cleanup, with exits 0/1/2 kept distinct and consumed only through D1's printed line; on `resolver-not-observed` or any D1 exit other than 0, the task halts with no T2, T3 or Claim; T2 harness-architect for the current task when it declares the surface; T3 the current task's valid RED record before Claim; a `harness-surface:none` task skips T2 and T3; T1 to T3 do not depend on a member being `queued`, because a backlogit 1.10 claim moves members to `active`); no Ship passage states an order that contradicts T1 -> T2 -> T3 -> Claim or FI-13; the template's run-once Step 2 and the `harness-ready` prefilter of Step 3 removed; the template's session-start memory restore and `### Resumption Protocol` replaced to meet restore contract rules 1 to 4; the recovery machine still invoked at session start (E L6) and the C1-C6 wiring intact (E O4); template and mirror semantically equal at their own anchors. The test files are added to the audit inventory |
| Verification | The tests fail against the pre-activation surfaces, and each failure names the missing anchor. This is a recorded gap characterization, **not** P-004 RED evidence (R2 refuses assertion failures) |
| Label | `harness-surface:none` |
| Estimate | 100 min; size `S`; complexity `medium` |

### D3: Ship activation (one task, one commit)

| Field | Value |
|---|---|
| Files | Exactly `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md` and `.autoharness/harness-manifest.yaml` (only the Ship mirror entry's checksum and note) |
| Preflight (all required; any failure halts before the first write) | (1) template and mirror blobs at the parent equal FI-12; the manifest's Ship mirror entry equals its `08787a4b` value and the SHA-256 of `HEAD:.github/agents/_ship.agent.md`, and every other manifest change since `08787a4b` is listed with its commit; (2) IM-01 CI evidence and the Windows run exist for C (IM-02); (3) B's suite, including the IM-16 tests, is green; (4) the IM-10 unit has shipped: `harness resolve` over a real shipment whose tasks declare `harness-architect` returns `HARNESS_READY / 0 / ALL_SURFACES_PRESENT`, accepted by D1; (5) D2's tests fail as recorded; (6) the non-claim audit passes with no skip |
| Change | Replace the passages named in charter 6.7 and insert the per-task pre-claim step in the mirror, as D2 asserts. Refresh the Ship mirror checksum from the raw staged blob (IM-12) |
| Mode | `careful` and `freeze-scope` (constitution VIII) for D3 and its rollback; the freeze boundary is the three paths |
| Verification | D2 green; the targeted and the whole canonical suite green; `git show --name-only` of the commit lists exactly the three paths; the checksum replayed from `HEAD:<path>`. Landed by merge commit only (P-009); after merge, the merge commit has two parents and the three paths equal the activation commit's blobs |
| Rollback | One rollback change, with fresh operator approval bound to the listed SHAs: revert D4's commit (if merged), then `<activation-sha>`, then D2's test commit, in that order, because D2 and D4 assert the activated text and would leave the canonical suite red after a D3-only revert. Then replay the three paths' checksums from `HEAD:<path>`, confirm the template and mirror blobs equal their pre-activation values, and run the whole canonical suite green. The rollback lands through a `chore/` branch pull request merged by merge commit (P-009), and the approved SHAs are rechecked against that branch before merge. D1 stays (inert without the activated text) |
| Label | `harness-surface:none` |
| Estimate | 110 min; size `M`; complexity `medium` |

### D4: Post-activation recovery fixture (IM-09)

| Field | Value |
|---|---|
| Files | `tests/test_ship_recovery_state_machine.py`; `tests/fixtures/ship_activation/recovery_traces.json`; `tests/test_harness_noclaim_audit.py` |
| Change | A state-machine test that closes the Proof E run 5 limitations L1, L3, L4 and L5 (`docs/decisions/2026-09-24-ship-activation-proof-e-run5-spike.md`, limitations table): L1, the fixture reads the activated rendered mirror (`docs/memory/`, never `{{DOCS_MEMORY}}/`); L3, the event vocabulary is closed, so `phase_restore`, `cursor_restore` and any unknown event type are rejected; L4, a candidate present without select, owner and confirm, and the post-validation next-action branch, are each exercised; L5, a `context_overflow_resume` after a full valid recovery that restores no next action has an explicit expected outcome taken from the activated text. The test files are added to the audit inventory |
| Verification | Canonical trace accepted; each L3 event and each FI-13 mis-ordering (every adjacent pair swapped) rejected; the L4 and L5 cases give their asserted outcomes |
| Label | `harness-surface:none` |
| Estimate | 75 min; size `S`; complexity `medium` |

IM-09 is `operator-deferrable`. If the operator defers it, D4 is removed
before harvest and the deferral is recorded with its rationale.

Serial inside D: D1 -> D2 -> D3 -> D4.

## Dependency Graph

```text
Shipments (blocks edges; exactly one dag-root):
  S(A) [dag-root] -> S(C) -> S(B-core) -> S(B-entry) -> S(D)
  S(IM-10) -> S(D)   (separate release unit, stash 9144435A)
  D3 also re-checks IM-01 CI evidence (C5) and IM-10 in its preflight.

Tasks:
  A1 -> A2
  C1 -> C2 -> C3 -> C4 -> C5
  B1 -> B2 -> B3 -> B4a -> B4b -> B5
  D1 -> D2 -> D3 -> D4
```

The graph is acyclic. Harvest adds shipment edges with
`backlogit dep add <next> <prev> --type blocks` and puts `dag-root` on S(A)
only. **S(D) is harvested only once the IM-10 shipment exists**, so its
`blocks` edge from S(IM-10) is created with it. S(D) therefore cannot be
claimed, and D2's red tests cannot sit in flight, while IM-10 waits behind
P-001 (IM-10-F01). The IM-10 plan places its shipment behind an existing
shipment, so S(A) stays the only `dag-root`. Each shipment is its own
feature and closes on its own on the close-path classifier's verdict,
never by `shipment ship` over part of a feature (P-015). Successors stay
`queued` behind their `blocks` edges.

## Trace From the Retired Tasks

| Retired item | Concern (revision 12) | Successor |
|---|---|---|
| `181-F` | Feature | One feature per shipment: A, C, B-core, B-entry, D |
| `181.001-T` | Standalone RED test writing (archived as superseded before revision 12 ran) | None. Per-task RED under A1, A2 and the [Marker Convention](#marker-convention) |
| `181.002-T` | Reader contracts and lexical validation | C1 |
| `181.008-T` | Budgets and bounded reads | C3 (snapshot, `RACE` and `IDENTITY_MISMATCH` semantics retired by Option D) |
| `181.009-T` | POSIX handle-relative adapter | None (Option D). Containment moves to C2, C4 and C5 |
| `181.010-T` | Windows `NtCreateFile` bindings | None (Option D). Windows containment moves to C2 |
| `181.011-T` | Windows parent-handle traversal | None (Option D). Bounded reads move to C3 |
| `181.012-T` | Integration, error mapping, cleanup | C2 and C3 (error mapping); B's reader-error mapping table; adapter cleanup retired |
| `181.006-T` | Resolver contracts and reason registry | B1 |
| `181.013-T` | Records, membership, declarations | B2 (`1..48`, not `1..512`) |
| `181.014-T` | Manifest snapshot and classification | B3 |
| `181.015-T` | Ledger, recheck, digest | B4a |
| `181.016-T` | Resolver and reducer | B4b (early return, IM-16) |
| `181.017-T` | Schema mirrors and registration | B1 |
| `181.007-T` | CLI adapter | B5. The Ship-side consumer (IM-07) is D1 |
| `181.003-T` | Ship text fixtures and structural tests | D2 |
| `181.004-T` | Pre-activation evidence | D3 preflight. Its "marker-bearing assertion failure" rule is superseded by FI-9 |
| `181.005-T` | Three-file activation | D3 |
| (none) | Evidence contract text | A1, A2 (new: the RED family `S69`, `S78`) |
| (none) | Post-activation recovery fixture | D4 (new: IM-09) |

The C3 record (`1610e181`) named `181.015-T` and `181.016-T` together as
"B4". This plan splits that concern into B4a and B4b to keep each task under
two hours.

## Portfolio Stash Coverage

The seven entries of the 2026-09-17 portfolio, and where each is carried now.
Only `76EBDE6D` is a source of this plan. The others stay separate (charter
`PE-SCOPE-05`).

| Entry | Defect | Carried by | This plan's role |
|---|---|---|---|
| `76EBDE6D` | P-004 red-phase precondition unsatisfiable | This plan (A1, A2 close the remaining text obstruction; B and D deliver the resolver the P-004 observation gate consumes). The executable RED observer stays in `docs/plans/2026-09-18-p004-observation-gate-plan.md` (blocked) | **Source** |
| `3EF5AAF2` | Shipment claim versus wave-admission conflict | `177-S` (post-claim member-status plan) | None. D's Ship edits must not change claim or wave-admission text |
| `86498B64` + `14F4D6F3` | Branch ownership ignores `implementation_branch` | `178-S` (branch-ensure plan) behind `185-S` | None |
| `C9CD24F3` | Append-only plan review loops | `186-S` (review-authority foundation) | Honored in practice: reviews are kept outside this plan |
| `7F9CB5E9` | No safe transition to `archived_status: shipped` | `183-S` spike; `181-S` withheld | None |
| `71200CBB` | Checkpoint without `resume_hint` | `180-S`, `182-S`, `185-S` | None. D3 keeps the recovery order unchanged |

## Decisions and Rationale

| ID | Decision | Rationale |
|---|---|---|
| PD-01 | C does not fold into B | 11 tasks and 985 minutes against 6 and 480 |
| PD-02 | Order A -> C -> B -> D, A the only root; S(D) also behind S(IM-10) | Evidence rules first; reader before resolver; activation last; no S(D) in flight while IM-10 waits |
| PD-03 | B4 is split into B4a and B4b | The two retired concerns total about 200 minutes; one task would break the 2-hour rule |
| PD-04 | Text-only tasks carry `harness-surface:none` | FI-9 accepts only an own-marker `NotImplementedError` `ERROR`. A text task has no production stub, and inventing one would be import laundering. A1 makes this explicit and restricts it to budgets without `src/` Python |
| PD-05 | The reader's code set is Proof G's plus `IO` | Option D retired the handle-relative codes. `IO` keeps ordinary OS failures explicit and closed |
| PD-06 | Lexical rules are the same on every host | The same input gives the same result on Windows and Linux (IM-05's "same measure"). Rejecting Windows-only forms on Linux is stricter and costs nothing for backlog paths |
| PD-07 | Reader errors map into the ratified list (table in Unit B) | No new code. Only read-limit codes are class 1b |
| PD-08 | Templates are read under `<workspace>/templates/` | Stays within the two static roots; anything else is a new trust root |
| PD-09 | Render uses the existing pure `_render_template` through a public alias | One renderer; no second placeholder grammar; no cross-module private import |
| PD-10 | D2 failures are gap characterization, not RED | R2 refuses assertion failures; D3 is `harness-surface:none` |
| PD-11 | A2 edits template and installed file in parallel and does not re-render | IM-10 requires the reflow reconciliation in its own operator-approved unit |
| PD-12 | IM-10 stays outside A to D and gates S(D) | Without it the real resolver reports `STALE` for `harness-architect`, and the activated Ship would halt on every task |
| PD-13 | CR-B1: sub-codes are diagnostics only | Ship branches only on accepted or `resolver-not-observed`, so no sub-code taxonomy becomes contract |
| PD-14 | Migration check for `1..48` | Read at plan time: the largest shipment membership in `.backlogit/queue` and `.backlogit/archive` is 20 (`168-S`, queued). No current shipment is affected |
| PD-15 | B ships as S(B-core) and S(B-entry) | The review re-estimate is 550 minutes, and section 9 permits a split, not an overrun |
| PD-16 | `harness resolve` is CLI-only | No MCP transport. A future MCP surface would call the same resolver and emit the same schema |

## Risks and Caveats

| Risk | Mitigation |
|---|---|
| Windows host lacks symlink privilege | Only the symlink sub-case may skip, with the reason recorded (`PE-SAFETY-02`); the junction case never skips; Linux runs every symlink case with zero skips (C5) |
| Linux CI unavailable or a push is not approved | IM-01 cannot be waived. C, B and D do not ship; D3's preflight halts |
| A shipment grows past 480 minutes | Split, never a seventh task or a longer estimate; escalate per P-013.6 (B is already split, PD-15) |
| A CRLF template checkout on Windows (templates are not `eol=lf` pinned) makes the real resolver report `STALE` | B's tests use LF fixture bytes. D3 preflight (4) fails closed rather than passing. The template pin and `git add --renormalize` belong to the IM-10 unit |
| IM-10 unit not approved | S(D) is not harvested or claimable; A, C and B remain inert |
| Ship text overlap with `177-S`, `178-S` or `180-S` | D3's preflight lists every change to the three paths since `08787a4b`; any unplanned change halts and returns to Stage |
| `harness-surface:none` misused on a code task | A1 restricts it to budgets without `src/` Python; harvest assigns labels from the file budgets in this plan |
| The P-004 observation-gate plan still names `187-S` in `blocked_on` | Not edited here (frozen, locked). Its re-pointing to the successor shipments is an operator item |
| A reviewer asks for race or hardlink defenses | Out of model (FI-10). Any such requirement is a threat-model change and a re-charter, never a plan finding to absorb |

## Plan Hardening Signals

| Signal | Present | Justification |
|---|---|---|
| Public API, schema or contract change | Yes | New result schema and registry (B1), CLI command (B5), P-002/P-004 wording (A1), actor text (A2), Ship activation (D3) |
| Security, auth, permission or compliance | Yes | Filesystem containment (C); trust-root boundary (PD-08) |
| Migration, backfill, destructive or irreversible step | Yes | D3 switches the live Ship agent; A1 changes a policy; membership bound lowered to 48 (checked, PD-14) |
| External integration, operator checkpoint or dependency | Yes | Linux CI (IM-01); IM-10 unit; operator approvals for policy text and activation rollback |
| High runtime, rollout or rollback risk | Yes | D3 changes how every future Ship task starts |

Requires plan hardening: yes

## Runtime Verification and Closure

| Unit | Runtime surface | What runtime verification proves | Closure artifact |
|---|---|---|---|
| A | None (text); code-affecting for closure because it changes procedure text | Structural tests and checksum replay | Closure note listing both checksum replays; closure-anchor refresh in a separate evidence-only commit |
| C | None user-facing (internal module) | Windows run of the four modules on NTFS; Linux CI step with zero skips (IM-01, IM-02) | CI job URL, runner OS, kernel, filesystem type, test counts |
| B-core | None (library and schema) | B1 to B3 suites green | Closure note with suite result |
| B-entry | CLI `harness resolve` | One document per class; stderr empty; exit equals `exit_code`; schema-valid | A recorded CLI transcript (bytes and SHA-256) for one fixture per state |
| D | Ship agent behavior | D2 and D4 green; D3 preflight record; one real dry resolution accepted by D1 | Activation record: SHA, three paths, checksum replay, rollback trigger, owner. The post-activation monitoring is recorded in Ship's `docs/memory/` session notes. It does not hold S(D) open |

Ship records every command and outcome. Stage runs none of them.

## Out of Scope

The P-004 observation gate and its plan, review and lock; any edit to the
revision 12 record; race, TOCTOU or hardlink defenses; more than one
supported surface; an MCP transport (PD-16); the IM-10 reconciliation itself; any
claim, push, pull request or merge by Stage.

## Operator Items

| ID | Item | Needed before |
|---|---|---|
| OP-1 | Approve and schedule the IM-10 release unit (stash `9144435A`) so it ships before S(D) | Harvest of S(D) |
| OP-2 | Keep or defer IM-09 (D4) | Harvest |
| OP-3 | Approve A1's P-002/P-004 wording at its pull request (a policy change) | A1 merge |
| OP-4 | Authorize re-pointing the P-004 observation-gate plan's `blocked_on` from `187-S` to the successor shipments, when appropriate (not by this plan) | P-004 gate planning |
| OP-5 | Authorize harvest to take `dispatch_mode:` and `decision:` from the review manifest entry bound to this plan's reviewed blob, not from an appended `## Plan Review` section (see [Review-Gate Capability Risks](#review-gate-capability-risks)) | Harvest |

## Plan Hardening

**Required: yes.** All five hardening signals are present (see
[Plan Hardening Signals](#plan-hardening-signals)).

### Learnings and Instructions Consulted

* `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`
  (raw staged-blob checksums; Proof F replay) -> IM-12 procedure in A1, A2
  and D3.
* `docs/compound/097-S-canonical-unittest-gate.md` -> FI-9 canonical
  command; `-v` confined to C5's evidence step.
* `docs/compound/2026-05-05-path-traversal-validation-parts.md` -> C1's
  component-based `..` rejection.
* `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`
  -> B1 creates both mirrors new at `1.0.0` and never edits a published
  mirror.
* `docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`
  -> D3 preflight lists all manifest drift since `08787a4b` instead of
  assuming none.
* `docs/compound/093-S-review-loop-convergence.md` -> the stop conditions
  below.
* `.github/instructions/constitution.instructions.md` sections III and IV
  (containment), V (explicit contracts) and VIII (safety modes, D3).
* `docs/decisions/2026-09-24-ship-activation-proof-e-run5-spike.md`
  limitations table -> D4's L1, L3, L4 and L5 cases.

### Protected Invariants

1. No result other than `UNRESOLVED / 2` after any read-limit error; no
   `NO_HARNESS` or `HARNESS_READY` from exhaustion (FI-4).
2. Nothing is read after the first read-limit error (FI-5).
3. No bytes from outside both roots in any result.
4. No public adapter seam (IM-06).
5. No race, TOCTOU or hardlink-alias claim (IM-14, `P2-critical`).
6. Ship never acts on a process status without an accepted document, and
   runs no T2, T3 or Claim after `resolver-not-observed` (IM-07).
7. Activation is one commit of exactly three paths (IM-08).
8. The recovery order FI-13 is unchanged.
9. The Linux-native gate IM-01 is never waived and never satisfied by
   Windows evidence, a mock, a container on a non-native filesystem or a
   skipped `test` job.
10. No test in A to D reads the real `harness-architect` surface at HEAD, and
    A2 never re-renders the installed actor file (IM-10).
11. No review, proof or test `PASS` is presented as claim authority (IM-15).
12. The published schema `1.0.0` mirrors are created once and never edited
    in place; any later change is a new version.

### Risky Actions

| ProposedAction | ActionRisk | Approval | ActionResult expected on failure |
|---|---|---|---|
| A1: change P-002/P-004 wording | High (policy) | Operator approval at the pull request (OP-3) | Pull request not merged; unit A stays open |
| A1, A2, D3: refresh manifest checksums | Medium | None beyond the task | Checksum replay fails -> task halts, no commit |
| B1: register a new schema contract at `1.0.0` | Medium (public contract) | Ordinary pull request review | Mirror parity or registration test red -> B does not ship; no mirror edited in place |
| B5: add the `harness resolve` CLI command | Medium (public CLI) | Ordinary pull request review | Envelope test red -> B does not ship; the command stays inert until D3 in any case |
| C2, C4 tests: create junctions, symlinks and FIFOs | Low (local filesystem) | None | Links are created only inside per-test temporary directories whose targets are also temporary, except the read-only Linux `/dev` targets (`/dev` as a reader root, `/dev/null` as a link target), which are never written; cleanup unlinks links and never follows them; cleanup failure fails the test rather than being ignored |
| B3: add the public alias `verify_workspace.render_template` | Low | Ordinary pull request review | Alias test red -> B-core does not ship; `_render_template` is unchanged |
| C5: add a CI step | Medium | Ordinary pull request review | CI red -> C does not ship |
| D3: activate Ship | High (live agent) | Preflight all green; operator merge | Preflight halt before any write; after merge, rollback below |
| D3 rollback: revert D4, D3 and D2 commits | High | Fresh operator approval bound to those SHAs | Halt and report if approval is absent |

### Added Verification

* **Environment prechecks per task.** `git worktree list` shows one
  worktree; `git status --porcelain` is empty for the task's files before
  the first write; the canonical command runs from the repository root.
* **Blocked paths.** No Linux evidence -> C, B and D do not ship. IM-10 not
  shipped -> S(D) is not claimable, and D3 preflight (4) re-checks. Any task over its estimate by more than 30 minutes ->
  stop and return to Stage for a split.
* **Monitoring after D3.** The first three Ship sessions after activation
  record each T1 outcome. Any `resolver-not-observed`, or any exit 1 or 2
  on a shipment expected to be ready, triggers the rollback review. Owner:
  the operator; validation window: those three sessions or seven days,
  whichever is longer.
* **Windows evidence (IM-02).** Ship's Windows run records
  `platform.system()`, `platform.version()`, the Python version, and the
  filesystem type of the volumes holding the checkout and
  `tempfile.gettempdir()`; both must be NTFS. `TMP` and `TEMP` point at the
  Git-ignored in-workspace `.proof-scratch/tmp`, so fixtures stay inside the
  workspace. It also records whether the
  host has symlink privilege, so any symlink skip is attributable.
* **Skip accounting.** On Windows the only permitted skips are the symlink
  sub-cases without privilege (`PE-SAFETY-02`) and G31
  (`NOT_APPLICABLE_ON_WINDOWS`). On Linux there are none. The C5 coverage
  test asserts that every case ID except G31 has a variant that runs on
  both hosts.
* **Unit D closure coupling.** D2's tests are red by design until D3. D2 is
  therefore not closed on its own: its closure evidence is D3's green
  canonical suite at D3's commit, both land in the same shipment pull
  request, and nothing between D2 and D3 is merged.
* **Rubric integrity at epoch open.** `git rev-parse HEAD:.github/skills/plan-review/SKILL.md`
  must equal the frozen R1 blob `c77f3685e81046195a55bcf4fc1e7d8973e40f97`.
  It did when this pass ran. If it differs when the epoch opens, that is a
  rubric change, and the epoch pauses.

### Non-Claim Audit Inventory

IM-14 and `PE-SAFETY-06` are `P2-critical`. The matrix, C5, D3 and closure
all cite this scope. It is a text audit (charter section 7.6): the test
guarantees coverage; a recorded disposition supplies judgment.

* **Audited commits.** `tests/test_harness_noclaim_audit.py` holds a
  closed list, `AUDITED`. C5 creates it with the harvest commit and S(A)'s
  merge and closure merge commits. Each later closure appends its
  shipment's merge commit and the previous closure's merge commit. After
  S(D) closes, the list is final.
* **Scope.** Every added line of each listed commit's first-parent diff
  (`git diff --no-renames -U0 <sha>^1 <sha>`), on every path, with no
  path exemption; renames and copies count as additions. A git-free floor
  also scans every line of the floor files, which must exist: C5 lists
  `harness_read.py`, B1 adds `harness_surfaces.py`, D1 `harness_verdict.py`.
* **Detector.** Case-insensitive, after whitespace runs collapse to one
  space, on each line and each adjacent pair of added lines:
  `\b(?:rac(?:e|es|ed|ing|y)|toctou|time[-\s]*of[-\s]*check|hard[-\s]*links?|hardlink\w*|symlink[-\s]*swap\w*)\b`.
  The vocabulary is closed.
* **Clearing.** A hit clears only if its line has no hit once the
  required sentence is removed, or the SHA-256 of its normalized line is
  in the test's closed `LEDGER` as `non-claim` or `fixture`. Any other
  hit fails, and so does a `LEDGER` entry that no scanned line uses. A
  task that adds paths or text "to the audit inventory" adds the entries
  for hits in its own lines; local review confirms them.
* **Base commits.** Only the `AUDITED` constants, never an environment
  variable. Without git or a listed commit the scan skips, naming the
  reason. The C5 step runs this module on an unshallowed checkout and
  fails on any skip, as closure and D3 preflight do.
* **Required sentence.** C1 writes it in the reader module docstring:
  "This reader makes no race, TOCTOU or hardlink-alias resistance claim."
  The audit asserts it is present.
* **Residue.** Claims outside the vocabulary, this plan, its review
  manifest and the final closure pull request fall to an agent's recorded
  text audit (an E3 review persona; Ship at harvest and each closure),
  with the `LEDGER` count. The operator need not take part. It covers
  this release only and creates no standing review of plan or review
  records.
* **Controls.** Must hit: every claim form in IM-14-F05, F10 and F11;
  `race-` then a newline then `free`; `hard-` then a newline then
  `link`. Must not hit: `trace-free`, `embrace-safe`, `grace period`.
  The required sentence hits and clears.

### Rollback and Closure by Unit

| Unit | Rollback trigger | Rollback procedure | Coupling | Owner | Validation window |
|---|---|---|---|---|---|
| A | Operator rejects the merged wording, or a structural test regresses | Revert A2's commit, then A1's, with operator approval (a policy change); replay both manifest checksums | Allowed only while no C, B or D task has recorded RED evidence under A's wording. After that, return to Stage, because those records would lose their contract | Operator | Until the first C task records RED |
| C | Linux or Windows containment defect found after merge | Revert C's commits. The reader has no caller until B, so the revert is inert | Blocks B. If B-core or B-entry has merged, B is reverted first | Ship, with operator approval | Until B-core merges |
| B | Resolver or schema defect found after merge | Revert B-entry's commits, then B-core's. There is no Ship caller until D3 | No release tag includes S(B-core) before S(B-entry) closes, so a schema defect B-entry finds reverts B-core, never a `1.1.0` bump. If a release tag included B, removing schema `1.0.0` or the CLI command is a contract removal and needs an operator decision instead of a plain revert. If D has merged, roll back D first, including D1, which validates against B1's schema | Ship, with operator approval | Until D3 merges or a release is tagged |
| D | See the monitoring bullet above | D3's Rollback row | D1 stays; D2 and D4 are reverted with D3 | Operator | Three Ship sessions or seven days, whichever is longer |

Partial rollout is safe by construction. A, C and B are inert until D3
calls the resolver. A shipped C or B without D changes no Ship behavior.

### Review-Gate Capability Risks

* The frozen parameters (rulings 5) require the lead Architecture
  Strategist to be dispatched as a subagent with the model `gpt-6-sol`
  named explicitly. If the runtime cannot do that, the review records
  `ROUTING_DEGRADED` and the epoch pauses. Same-model substitution for the
  lead is not allowed, so `dispatch_mode: same-model-declared-degradation`
  is not an acceptable outcome for the lead. In the initial review, the
  Orchestrator dispatched it this way (see the review manifest).
* The review record must carry literal `dispatch_mode:` and `decision:`
  lines. Harvest fails closed without a `decision: PASS` recorded for this
  plan's reviewed blob.
* Finding IDs are `<row>-F<NN>`. Only `P0`, `P1`, and `P2` on IM-14,
  `PE-SAFETY-06` or `PE-SAFETY-07` block.
* The Security Lens and Agent-Native Parity reviewers are also frozen on
  `anchor_review`. Ratified section 9 item 1 says a route change pauses the
  epoch. This plan reads that as covering them too: if either cannot run on
  `anchor_review`, the epoch pauses rather than falling back to the same
  model. The Orchestrator confirms this reading when it opens the epoch.
* **Harvest verdict source (blocks harvest, not review).** The installed
  `harvest` skill looks for a `## Plan Review` section in the plan, and the
  R1 rubric says to append reviews to the plan. This plan keeps reviews in
  its review manifest, and adding a section after review would change the
  reviewed blob. Harvest therefore needs an explicit authorization (OP-5)
  to read `dispatch_mode:` and `decision:` from the manifest entry bound to
  this plan's reviewed blob SHA. Without that authorization, harvest fails
  closed.

### Unresolved Operator Decisions

OP-1 blocks harvest of S(D) only. OP-2 must be answered before harvest, or D4 is
harvested as planned. OP-5 must be answered before harvest. OP-3 and OP-4
do not block harvest.

### Plan-Harden Record

**Revision 3 re-run.** Checks re-run over every touched section. No new
signal, risky action or public name. The audit scope became a rule over
listed artifacts plus each shipment's diff; the patterns became
inflection-tolerant. Each change is tied to its finding ID in the review
manifest.

**Revision 2 re-run.** No new signal. Changes: the B3 alias in Risky
Actions; rollback rows for B's two shipments and D1; one audit inventory;
B5's `--help` prints to stdout with exit 0, as argparse does.

**Revision 1 pass.** The `plan-harden` skill ran as its own pass over the
four required outputs (verification depth, rollback, guardrails, risk
triggers), also consulting the `plan-harden`, `plan-review` (R1 blob
verified) and `harvest` skills, `.github/workflows/ci.yml`, the Proof G
spike tables and the charter's `PE-SAFETY-07` row. It corrected four
verification defects in place (C4 device-node expectation and case IDs;
Linux junction analogues for C2 and C5; C5's fixture-root filesystem and
skipped-job evidence; D3's three-commit rollback) without changing a unit,
task, estimate, order or mapping, and added invariants 9 to 12, three
risky actions, the audit, Windows evidence, skip accounting, unit D
closure coupling, per-unit rollback, the rubric check, the supporting
route reading and OP-5.
