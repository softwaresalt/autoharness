---
title: "SHIP-10 minimal Copilot plugin payload plan — review history"
date: 2026-09-03
slug: minimal-copilot-plugin-payload-plan-review-history
doc_type: review
shipment_unit: "SHIP-10"
plan: "docs/plans/2026-09-03-minimal-copilot-plugin-payload-plan.md"
status: active
---

# SHIP-10 plan — review history

Consolidated review-cycle history for
[`docs/plans/2026-09-03-minimal-copilot-plugin-payload-plan.md`](../plans/2026-09-03-minimal-copilot-plugin-payload-plan.md).

**Purpose.** The plan states only the current execution contract. Every
superseded clause, withdrawn formulation, historical verification table, and
per-cycle disposition lives here instead. This is the single traceability
artifact for the plan's review lineage.

**Scope rules.**

* This file records dispositions and the reasons clauses were withdrawn. It does
  **not** duplicate raw session transcripts.
* Session memory files under `docs/memory/` remain pointers to their own
  sessions; they are listed below and are not reproduced here.
* Where a clause was withdrawn, the entry names the withdrawn text and the
  clause that replaced it in the current plan, so a reader encountering the old
  wording elsewhere can resolve it.

## Session memory pointers

| Cycle | Memory file |
|---|---|
| Staging | `docs/memory/2026-09-03-stage-minimal-plugin-payload-staging.md` |
| 1 | `docs/memory/2026-09-03-stage-review-fix-cycle-1.md` |
| 2 | `docs/memory/2026-09-03-stage-review-fix-cycle-2.md` |
| 3 | `docs/memory/2026-09-03-stage-review-fix-cycle-3.md` |
| 4 | `docs/memory/2026-09-03-stage-review-fix-cycle-4.md` |
| 5–8 | Folded into the cycle-9 record; no separate memory files were written |
| 9 | `docs/memory/2026-09-03-stage-review-fix-cycle-9.md` |
| 10 | `docs/memory/2026-09-03-stage-review-fix-cycle-10.md` |
| 11 | `docs/memory/2026-09-03-stage-review-fix-cycle-11.md` |
| 12 | `docs/memory/2026-09-03-stage-review-fix-cycle-12.md` |

## Cycle summaries

### Staging — initial decomposition

Stash entry `E9E5E6CC` was deliberated into
`docs/decisions/2026-09-03-minimal-copilot-plugin-payload-deliberation.md`,
planned, hardened, reviewed, and harvested into feature `160-F` and shipment
`168-S`. The measured problem statement (3,238 plugin-reachable files, 2,110 of
them `.backlogit/`, 642 force-included `docs/` files against 21 actual root
guides, and the omitted `.github/policies/**` and `scripts/` subset) was
established here and remains current in the plan.

### Cycle 1 — acceptance-criteria completeness

Established AC1–AC11 and the initial task decomposition. Introduced the
requirement that the manifest be the sole source of payload paths, and that
development surfaces be excluded from both channels.

### Cycle 2 — machine decidability

Converted prose acceptance criteria into decidable predicates. Introduced the
AC2c four-predicate single-generation-path check and the AC2c-R deterministic
rendering rules (narrow TOML line renderer; `tomli-w`, `tomlkit`, and `ruamel`
prohibited; canonical JSON serialization; UTF-8 without BOM; LF only; forward
slashes; binary-mode `--check`).

### Cycle 3 — test class contract and case ledger

Introduced the RED-FIRST / CHARACTERIZATION class contract, the case ledger, and
machine-checked author-before-owner ordering over the dependency DAG. The ledger
stabilised at 46 unique cases (32 RED-FIRST, 14 CHARACTERIZATION), 52 owner
edges, and 34 ordering paths — figures unchanged since.

### Cycle 4 — evidence and provenance

Introduced the evidence-verification contract and task T16. Established the
provenance protocol (commit first; capture `git rev-parse HEAD` and
`git status --porcelain=v1` into the raw-log head before the command runs;
recorded observations require a clean committed tree) and the log bounds
(256 KiB and 2,000 lines per log, 3 logs per case, 200 files per shipment, no
binaries).

### Cycle 5 — write partition and approval model

**Withdrawn:** a branch-keyed approval set, under which approval requirements
varied by the branch being worked on.

**Replaced by:** the eight-class write partition with the approval set fixed at
exactly `OVERWRITE ∪ REMOVE`, and Principle VII two-layer approval, in which the
Layer 1 generator accepts no approval input at all so its refusal of a tracked
`OVERWRITE` or `REMOVE` is unforgeable.

Also settled in this cycle: tracked-ness is determined by
`git ls-files --error-unmatch -- <path>` **in the tree under test**, never "at a
commit".

### Cycle 6 — AC2d occurrence semantics withdrawn

**Withdrawn:** "the target-workspace prefix literal must appear exactly once".
Measurement at the tip found **57 occurrences across 23 files**, making the
criterion unsatisfiable as written.

**Replaced by:** the AC2d P1–P4 derivation predicate (AST declaration
uniqueness; call-site routing through `classify_target_workspace_path`; no
fixture ingestion bypass; a frozen symbol-keyed allow-list that may not increase
and contains exactly two `verify_workspace.py` literals). Gate A asserts the
derivation predicate only and asserts nothing about occurrence counts.

The corresponding ledger case was named
`test_target_workspace_prefix_derivation_is_centralized` so that the case name
states the property actually asserted. The rename was atomic across the ledger
and all task records and did not change the case count.

### Cycle 7 — hermetic upgrade formulation withdrawn

**Withdrawn:** the "HERMETIC UPGRADE CASE", which asserted a real installed
upgrade executed in a hermetic rebuild environment, together with the two
earlier formulations of V3 that preceded it. Three formulations in total were
withdrawn.

**Replaced by:** V3 in its **local-artifact / `RECORD` form only**, consuming
T2a's recorded facts. Real offline end-to-end installed-upgrade execution was
deferred as `60C207F1` (high) and remains an open residual risk. The plan makes
no claim of real installed-upgrade execution, network fetch, or hermetic
rebuild.

The schema-mutation third-occurrence learning applied here: a third attempt at
the same formulation opened the circuit and the approach was withdrawn rather
than retried again.

### Cycle 8 — producer-local FORMAT lists removed

**Withdrawn:** per-producer FORMAT field lists, which restated the evidence
record's field list inside each producing task. Restating the list in N places
guaranteed drift between them.

**Replaced by:** a single canonical evidence table in the plan that producers
**reference**. The zero-token result (no producer-local field list survives in
any task record) was verified in cycle 8 and re-verified in cycles 9 and 10;
this is a closed circuit and field lists are not to be reintroduced.

Also in this cycle: scratch containment was tightened to a unique resolved,
gitignored, workspace-contained root with canonical containment validation, OS
temporary directories prohibited, exclusion applied before classifier and
payload input, and no automatic deletion.

### Cycle 9 — pytest prerequisite added

**Finding.** `pyproject.toml` already declared `[tool.pytest.ini_options]`, but
`uv.lock` contained no pytest and `ci.yml` explicitly invoked `unittest`. The
Constitution and PR automation require pytest. T14 would therefore have been
knowingly blocked.

**Disposition.** One bounded prerequisite task was added to `160-F` / `168-S` as
same-contract completion: `160.020-T` (**T0**), covering a pinned pytest
dependency through the project's supported dependency-group mechanism, the
`uv.lock` update, and the CI test-invocation change. Three DAG edges were wired
(`T3a←T0`, `T3b←T0`, `T14←T0`), placing T0 before every pytest author or
consumer and before T14. The task authors no payload behaviour test. `160.019-T`
was already retired and its ID was not reused. Case, class, owner, and ordering
counts were unchanged.

**Also fixed in cycle 9:** one live P1 — a surviving "hermetic actual upgrade"
claim in the mandatory-durable-outputs table, withdrawn back in cycle 7. The
cycle-8 review section had never been written, leaving a dangling forward
reference; it was reconstructed from the dated inline annotations and written,
followed by the cycle-9 section.

**Verdict:** PASS, zero P0/P1.

### Cycle 10 — root-cause consolidation

Independent review was blocked by stale operational clauses accumulated across
nine appended amendment cycles. The plan had reached 3,784 lines / 355,752
bytes, with multiple statements per subject and superseded clauses still
readable as if current.

**Action:** the plan was rewritten as one canonical current execution contract
(850 lines / 41,014 bytes, down from 3,784 lines / 355,752 bytes — a 78% line
and 89% byte reduction) with all cycle narratives, historical verification
tables, withdrawn clauses, and duplicate definitions removed to this file.

**Corrections applied in cycle 10:**

| # | Correction |
|---|---|
| 1 | Plan reduced to one statement per subject; history relocated here and linked from the plan |
| 2 | Plan reconciled against the live records: wheel+plugin scope, `99818C6D`, `60C207F1`, 19 tasks including T0, exact 51-edge DAG, 46-case ledger, 32R/14C, 52 owners, eight-class partition, single scratch root, pytest toolchain, two release gates, evidence/output contract, rollback, verification |
| 3 | `160.001-T` (T2a) record E3 rewritten: OS `tempfile.TemporaryDirectory()`, the baseline wheel rebuild feeding T10, and the withdrawn hermetic upgrade case were all removed. T2a records inventories, digests, and its own reproducibility facts only; T10 consumes recorded facts |
| 4 | "Two ephemeral roots" removed everywhere, including Principle VII rule 9. Exactly one scratch root |
| 5 | Capture count corrected from "seven captures across four tasks" to **six**: T0 owns three (pyproject test-dependency region, `uv.lock`, `ci.yml`), T7 one, T8 one, T14 one. T14 never owns `ci.yml` |
| 6 | T0's `ci.yml` scope corrected from "exactly two changes" to **exactly three** (pinned setup-uv, fail-closed pytest preflight, replace the unittest invocation) |
| 7 | `observation_phase` introduced (`baseline` / `post-change`) with two phase-selected `artifact_ref` identity sources. A post-change digest is never required to equal baseline. `160.017-T`'s unconditional baseline check withdrawn |
| 8 | Canonical evidence table carries every required field exactly once; producers reference it only. `160.017-T` now verifies `owner_task` explicitly |
| 9 | Plugin `install_root` stated as `""` in the plan **and** corrected in `160.003-T`, whose surviving clause still made `plugin-payload/` the plugin install root; `plugin-payload/**` restated as a branch-(b) materialization output root, never an install-root prefix |
| 10 | AC11 restated as candidate rules + most-specific selection + equal-specificity fail-closed, with generated roots removed before matching. False "exactly one raw match" and "no precedence" claims removed |
| 11 | Placeholder hygiene: the literal brace form of the version token appears only inside fenced fixture examples; headings and prose use the symbolic form |
| 12 | Baseline aggregate digest stated once, as sorted `(path, size, sha256)` triples |
| 13 | `160.001-T` resized S → M on remeasured baseline inventory workload; histogram and derived rollup recomputed. T10 and T14 remain M |
| 14 | Producer-local FORMAT lists re-verified absent (cycle-8 circuit remains closed) |
| 15 | Missing future implementation artifacts and unchanged current CI/release files are explicitly not review findings |
| 16 | Plan ↔ 19 tasks ↔ `168-S` ↔ 51 edges reconciled both ways; 46/32/14/52/34 metrics, mandatory outputs, frontmatter, Markdown, placeholders, and control characters re-checked |

**Verdict:** PASS, zero current P0/P1 across all six review personas
(architecture, security, test/QA, release/ops, simplicity/maintainability,
policy).

**Open P2 — `168-S` size rollup counts a retired task.** `backlogit shipment
get 168-S` derives `size_composition` by resolving `160-F` into every child
carrying `parent_id: 160-F`, which includes the archived, retired `160.019-T`
(M). The derived rollup reads `M:11, S:9` over 20 members; the **live 19-task
histogram is `M:10, S:9`**. The 20-entry manifest itself is correct and does not
contain `160.019-T`. This is backlogit rollup behaviour, not a plan, manifest,
or task defect. Never quote `M:11, S:9` as the live task histogram.

### Cycle 11 — dual-phase runner contract and stale-clause corrections

Cycle 10 left the plan concise but carried nine correctness defects into the
independent review, plus one unresolved policy conflict: **P-004 states its
red-phase precondition literally as `PYTHONPATH=src python -m unittest discover
-s tests`, while the Constitution names `pytest`.** Cycle 9 had added the pytest
toolchain task (T0) without reconciling the two documents, and T0 itself claimed
to author no test at all.

**Resolution — minimal dual-phase contract, no policy expansion.** Every case
this shipment authors is a `unittest.TestCase` method, so both runners collect
it. P-004's gate confirmation is whole-suite and gate-scoped and is always taken
with its exact unittest command (stdlib — no lock, no dependency group, no
network needed), before and after T0. Per-case ledger observations use
`uv run python -m pytest` once locked, with exactly one pre-lock exception:
T0's own red. `test_node_id` needed no runner field, because a node ID is a
property of a case's file and class location, fixed at authoring time and
verified by T16 against a terminal `--collect-only` run.

**Corrections applied in cycle 11:**

| # | Correction |
|---|---|
| 1 | `160.017-T` terminal rejection list: the unconditional baseline-E1 rejection deleted. `artifact_ref` validation is now **always** phase-and-kind selected across five sub-cases (baseline/post-change x wheel/plugin, plus static contract) |
| 2 | `160.005-T`'s release-workflow case widened to the six-part predicate already carried by `160.015-T`: both gates, Gate A before build, Gate B after build and before publish, and no `dist` mutation between Gate B and publish. One case, wider predicate, no new row |
| 3 | Generic "gitignored temporary path" replaced in `160.002-T`, `160.008-T`, `160.009-T`, `160.010-T`, `160.013-T` with the single contained root `dist/.autoharness-scratch/<run-id>/` plus canonical containment, pre-matching exclusion, and no-auto-delete |
| 4 | T10 inventory normalization: T2a's E1 wheel side is the distribution's own `RECORD` / archive-member inventory, **not** an installed-workspace listing. `160.012-T`'s U1/U4 rewritten as a `RECORD`-to-`RECORD` set difference with a **closed** allowed-metadata-difference list. The withdrawn install-output-vs-`RECORD` comparison produced a phantom orphan set indistinguishable from a real regression |
| 5 | Forward correction appended to the `160-F` feature log recording the cycle-10 state (live S9/M10, derived S9/M11) as superseded by the cycle-11 state (live **S8/M11**, derived **S8/M12**). Append-only history was not altered |
| 6 | T16 log bounds reduced to one executable rule: **fail closed** on any log over 256 KiB or 2,000 lines. The truncation path, the `truncated` field and the pre-truncation counts were deleted from `160.017-T` **and from all seven producer records**, which had still instructed producers to truncate while T16 rejected the result |
| 7 | Tracked-write approval parity: T0 and T14 now carry the same external fresh-live-approval-over-the-reviewed-partition obligation as T7 and T8. AC3e's *classification machinery* is generator-scoped; the Layer-2 *approval obligation* is not — otherwise "author it by hand" silently bypasses Principle VII |
| 8 | T0 red-first: `160.020-T` authors and owns ledger case 47, `test_ci_invokes_the_locked_canonical_test_runner`, observed red under P-004's unittest command on the committed pre-change tree and green under the canonical runner. The "authors no test" and "authors no case" claims were withdrawn. Ledger 46 -> **47**, RED-FIRST 32 -> **33**, owner assignments 52 -> **53**, ordering paths unchanged at **34** (author and owner are the same task). `160.020-T` resized S -> **M** |
| 9 | Stale AC2d single-occurrence authority deleted from `160.008-T` and `160.010-T`; stale case-name-retained rationale deleted from `160.003-T` and `160.004-T` |
| 10 | T3a's 22-case M sizing captured as deferred stash entry `0B83AC8F` with a named disposition and stated residual risk. Splitting requires choosing a boundary, re-deriving the author column for 22 rows, adding a DAG node and edges, and recomputing ordering paths — that is separate execution-planning work, forbidden by this cycle's no-new-task constraint. Publication readiness is **`READY_WITH_FOLLOWUPS`**. The old rationale understating 22 cases as "a few scenarios" was corrected explicitly |
| 11 | Canonical evidence table re-verified: every required field present exactly once, phase-specific identity sources defined for both artifact kinds and for the static-contract case; producer-local FORMAT lists re-verified absent |
| 12 | Full recomputation and cross-check. Two arithmetic defects found in the plan's own rollups and fixed: the per-author line still read 32 R and omitted T0, and the per-owner itemization summed to 52 while claiming 53. The plan's Open-P2 block still quoted the cycle-10 rollup figures. A dangling cross-reference to a withdrawn plan section name was repointed. Three further live stale "46" figures were corrected in `160.005-T`, `160.017-T` and `160.020-T`. P-004's gate scope was clarified as whole-suite in both the plan and `160.020-T`, and T0's first `ci.yml` / `uv.lock` write was added to the checkpoint list |
| 13 | Fresh changed-artifact multi-persona review re-run |

**Verdict:** PASS, zero current P0/P1 across all six personas.

**Plan size:** 850 -> 979 lines, 41,014 -> 49,734 bytes. Still under the
sub-1,000-line target; the growth is the runner contract, the T0 red-first
contract, the tracked-write approval section, and the like-for-like comparison
block — all current contract, no history.

**Open P2 carried forward:** `0B83AC8F` (T3a sizing), `60C207F1` (offline
installed upgrade), and the `168-S` rollup anomaly, whose current figures are
derived **`M:12, S:8`** over 20 members against a live 19-task histogram of
**`M:11, S:8`**.


## Withdrawn clause index

Quick resolution for readers who encounter superseded wording in an older
artifact.

| Withdrawn wording | Cycle | Current replacement |
|---|---|---|
| `AC3b` — the sdist acceptance criterion | 5 | Deleted with the channel; sdist deferred as `99818C6D`. The plan's criteria run AC3, AC3c, AC3d, AC3e with no AC3a/AC3b |
| Branch-keyed approval set | 5 | Approval set is exactly `OVERWRITE ∪ REMOVE` (AC3e) |
| "Exactly one occurrence" of the target-workspace prefix | 6 | AC2d P1–P4 derivation predicate |
| "HERMETIC UPGRADE CASE" and two earlier V3 formulations | 7 | V3 local-artifact / `RECORD` form; real upgrade deferred `60C207F1` |
| Producer-local FORMAT field lists | 8 | Single canonical evidence table, referenced by producers |
| "Two declared ephemeral roots" | 10 | Exactly one: `dist/.autoharness-scratch/<run-id>/` |
| "Seven captures across four tasks" | 10 | Six captures across four tasks |
| T0 `ci.yml` "exactly two changes" | 10 | Exactly three changes |
| "Exactly one raw match / no precedence needed" (AC11) | 10 | Candidate set + most-specific selection + equal-specificity fail-closed |
| Baseline rebuild in T2a feeding T10 | 10 | T2a records facts only; T10 consumes recorded facts |
| OS `tempfile.TemporaryDirectory()` for scratch | 8, 10 | Workspace-contained `dist/.autoharness-scratch/<run-id>/` only |
| Plugin `install_root` = "the plugin payload root declared in `generated_output_roots`" | 10 | `plugin.install_root` = `""` (payload root) |
| `artifact_ref` checked against the T2a baseline inventory unconditionally | 10 | Phase-selected: `baseline` -> T2a E1; `post-change` -> current trimmed inventory |
| "CI has drifted from the mandate, which 160.015-T (T14) corrects" | 9, 10 | `160.020-T` (T0) corrects it; T14 owns `release.yml` only |
| "This task authors no test" / "authors no case" (`160.020-T`) | 11 | T0 authors and owns ledger case 47; red under P-004 unittest, green under the canonical runner |
| "NO AC3e PARTITION RECORD" exemption for T0 | 11 | T0, T7, T8 and T14 all record a reviewed OVERWRITE/REMOVE partition and obtain fresh live approval |
| Log truncation path, `truncated` field, pre-truncation counts | 11 | One rule, fail closed: a log over 256 KiB or 2,000 lines is rejected; producers halt and report |
| `artifact_ref` unconditional baseline-E1 rejection (terminal list) | 11 | Always phase-and-kind selected, including a source-tree identity for the static-contract case |
| Baseline install-output listing compared against the trimmed wheel `RECORD` | 11 | `RECORD`-to-`RECORD` set difference with a closed allowed-metadata-difference list |
| Single-gate release-workflow predicate in `160.005-T` | 11 | Six-part predicate matching `160.015-T`: both gates, ordering, and no `dist` mutation between Gate B and publish |
| "AC2d single-occurrence rule" cited as live authority (`160.008-T`, `160.010-T`) | 11 | Withdrawn in cycle 6; the no-local-re-listing requirement survives on AC2d predicate P2 |
| "THE CASE NAME IS RETAINED" / "the name is historical" rationale | 11 | Current case name only: `test_target_workspace_prefix_derivation_is_centralized` |
| Generic "gitignored temporary path" | 11 | The single contained root `dist/.autoharness-scratch/<run-id>/` |

## Cycle 12 - bounded final corrections after independent review of `b3156cb5`

Scope: Stage/backlog/docs only. No new task, channel, case, schema, engine or
dependency. One P-021 stash capture authorized and used (`76EBDE6D`).
Verdict: **PASS** - zero current P0/P1 across six personas.
Readiness: **READY_WITH_FOLLOWUPS** (`76EBDE6D`, `0B83AC8F`, `60C207F1`).

| # | Correction | Disposition |
|---|---|---|
| 1 | P-002/P-004 harness-ready gate | Cycle-11 reconciliation withdrawn; harness-architect authors and confirms T0's red case; Ship must not claim before `harness-ready`; Ship halts per P-002 violation action; gate stays fail-closed; captured `76EBDE6D` |
| 2 | T10 installed-orphan claim | Narrowed to distribution-member removal; AC6/V3 renamed; case 29 renamed atomically across plan, ledger and 3 task records; count unchanged |
| 3 | Evidence subject and cardinality | `owner_task` -> `owner_tasks` (sorted unique array); `artifact_subject` enum `static\|wheel\|plugin`; subject mapping as a total function of the owner set; primary key `(case_name, observation_phase, artifact_subject)`; 106 record slots |
| 4 | T16 producer count | Seven -> **eight**, adding T0/`observations/T0.json` |
| 5 | Duplicate unconditional-baseline paragraph | Deleted from `160.017-T`; selection is `(observation_phase, artifact_subject)` pair-selected everywhere |
| 6 | Release Gate A/B assertion | Verified already correct in `160.005-T`; no edit |
| 7 | Generic scratch wording | Verified zero live occurrences; all hits are withdrawal text |
| 8 | Producer write scopes | Dual-destination clause inserted into all eight producers; zero surviving "only JSON" clauses |
| 9 | T10 baseline side | Install-output inventory wording deleted; wheel `RECORD`/member inventory only |
| 10 | `160.001-T` corrupted fragment | Orphaned `ely a recorded column` tail removed; sentence restored |
| 11 | Stale rename narratives | Deleted from `160.018-T`; `160.003-T`/`160.004-T` verified already corrected in cycle 11 |
| 12 | Log bounds | Verified fail-closed; no `truncated` field |
| 13 | Approvals, captures, follow-up IDs | Verified: T0/T7/T8/T14 approval parity, six captures, all deferred IDs intact |
| 14 | Absent queued implementation | Not treated as a finding; archived-child rollup caveat remains P2 |
| 15 | Full recomputation and fresh review | All metrics reconcile; DAG plan<->frontmatter exact 51/51 |

### Clauses withdrawn in cycle 12 (must not return)

| Withdrawn clause | Where it lived | Why it was false |
|---|---|---|
| P-004's gate confirmation "costs nothing to honour" / "is taken at every red-phase gate" | plan Runner contract, `160.020-T` | `tests/` holds 106 files / 2,025 test functions and `ci.yml` line 112 runs P-004's exact command as the required gate, so it exits 0 on the default branch while P-004 requires non-zero for every test function |
| "BOTH ARE SATISFIED WITHOUT AMENDING EITHER" | `160.020-T` | Same measurement; the unittest-compatible authoring convention is necessary but not sufficient for P-004's red gate |
| A mixed RED/CHARACTERIZATION whole-suite run satisfies "every function red" | plan, `160.020-T` | A characterization case passes by construction, so the claim fails independently of the 2,025 pre-existing tests |
| `test_upgrade_from_1_5_0_leaves_no_orphans` and every "no installed orphans" claim | plan ledger, `160.012-T`, `160.006-T`, `160.007-T` | `RECORD` is an inventory of what a distribution *contains*; member absence is silent on whether a prior install's copy is deleted during upgrade. Deferred in full to `60C207F1` |
| Singular `owner_task` | plan evidence table, `160.017-T` | Six cases carry two owners and could not be represented without dropping an owner |
| "seven authoring tasks" and its seven-entry path list | `160.017-T` | T0 has authored ledger case 47 since cycle 11; T16 would have read seven inputs then failed case 47 for having no record |
| Duplicate unconditional baseline-`artifact_ref` paragraph | `160.017-T` | Contradicted the phase-and-subject-selected rule stated in the same record |
| "the ONLY authorized write ... is its observation record" | `160.005-T`, `160.016-T` and six other producers | Contradicted the bounded raw-log directory those same producers are required to write |
| T10 baseline side "READ FROM 160.001-T's RECORDED INSTALL INVENTORY" | `160.012-T` | Compared target-workspace destination paths to wheel archive-member paths - two different universes |
| "the case NAME is retained deliberately ... historical rather than descriptive" | `160.018-T` | The case was renamed atomically in cycle 9; the rationale survived three cycles past the fact it described |
