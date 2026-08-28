---
title: "Harness-wide deterministic pre-review evidence DAG and staged shipment portfolio"
description: "Normalizes nine imported harness-level stash entries against the 15 dual-source recurring review families, selects a detector-SDK-plus-composable-derived-DAG architecture, defines an epoch-indexed evidence DAG contract, and stages an eleven-shipment dependency-ordered portfolio with report-only-first rollout."
topic: "Harness-wide deterministic pre-review evidence DAG and staged shipment portfolio"
depth: "deep"
date: 2026-08-27
status: "decided"
decision_status: "decided"
promoted_to: "none"
deliberation_id: "031-DL"
agent: "stage"
route: "claude-opus-5 / anthropic / high"
doc_type: "decision"
artifact_kind: "deliberation"
source: "docs/decisions/2026-08-27-pre-review-evidence-dag-shipment-portfolio-deliberation.md"
source_stash:
  - "D911A3B2"
  - "39AA674D"
  - "926FEA6D"
  - "A02280C8"
  - "3F80F8A3"
  - "C327A8DE"
  - "7A3F570B"
  - "89E833E1"
  - "8CB5A9B9"
  - "34AAF1C7"
related_artifacts:
  - "028-DL"
  - "029-DL"
prior_spike: "docs/decisions/2026-08-27-recurring-review-issues-tooling-opportunities-spike.md"
linked_artifacts:
  - "docs/decisions/2026-08-27-recurring-review-issues-tooling-opportunities-spike.md"
  - "docs/decisions/2026-08-25-pr-review-convergence-finding-ledger-deliberation.md"
  - "docs/decisions/2026-08-25-machine-produced-structure-determinism-and-the-surviving-dag-partition.md"
tags:
  - "pre-review-evidence"
  - "fault-line-dag"
  - "detector-sdk"
  - "shipment-portfolio"
  - "stage-deliberation"
---

# Pre-Review Evidence DAG and Staged Shipment Portfolio

* **Deliberation artifact**: `031-DL`
* **Mode**: normal (non-dark) Stage deliberation; **strictly read-only**
* **Verdict**: **STAGE THE PORTFOLIO.** Architecture selected, taxonomy fixed,
  DAG contract specified, eleven shipments defined and dependency-ordered.
  **No backlog mutation, no harvest, no shipment allocation, no plan** this
  session — `promote_to: none` was explicit.
* **Session degradation**: `ENGRAM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`,
  `INTERCOM_DEGRADED`. File-based fallback used per
  `.github/instructions/agent-engram.instructions.md`. `TOOL_OK: backlogit 1.10.1`,
  `INDEX_SYNC_OK` (996 items). No ad-hoc substitution for a reachable tool
  occurred (P-012 preserved).

## Scope and constraints

Read-only inspection of this repository, its backlogit stash/query surfaces, and
the three prior decision artifacts. **No source, template, schema, or config file
was modified. No backlog item, shipment, feature, task, or stash mutation was
performed. No branch, worktree, commit, push, or PR was created.** The P-016
Stage spike/research worktree exception was deliberately **not** exercised.

Pre-existing dirty worktree state was preserved untouched:
`.backlogit/stash.jsonl` (modified by an external backlogit-workspace agent) and
`docs/decisions/2026-08-27-recurring-review-issues-tooling-opportunities-spike.md`
(untracked artifact from the immediately preceding spike).

**Non-goals of this artifact.** It does not allocate backlogit IDs, does not
constitute an impl-plan, does not authorize any blocking gate, and does not
revise the `dag-readiness` no-scheduler non-goal.

## Problem Frame

The operator asked for one durable decision artifact that answers a compound
question:

> Review the newly imported harness-level stash findings together with the
> recurring local-adversarial/Copilot review findings; group common patterns;
> design a DAG-oriented approach that mechanically and deterministically
> identifies, addresses, and remediates fault lines **before** PR review; then
> define the shipments to stage and their priority/dependency order.

Three bodies of evidence converge on this frame and must be reconciled rather
than concatenated:

1. **Nine imported/elevated stash entries** (`D911A3B2` epic + eight features)
   proposing a harness-wide deterministic pre-review evidence system, written
   with backlogit as the pilot workspace.
2. **The 2026-08-27 recurring-review spike**, which measured 1,980 Copilot
   findings across 303 PRs and 598 HEAD-keyed rounds against 149 numbered local
   adversarial findings, and produced **15 dual-source recurring families** ranked
   into three determinism tiers.
3. **`028-DL` and `029-DL`**, which already ruled on the DAG question and left
   behind four binding laws plus two measured refutations that constrain any
   architecture proposed here.

The economic case is not in dispute. 53 PRs required 3+ review rounds, 24
required 5+, one required 20. `028-DL` §2 establishes *why* the loop does not
terminate: the review node set is generated on demand by a nondeterministic
external oracle, so acyclicity cannot imply termination. **The only lever that
dominates round count is the node-generation rate** — the number of genuine
defects that reach a review surface at all. Everything in this portfolio attacks
that rate.

What *is* in dispute, and what this deliberation must settle:

* Whether the imported entries describe the right scope, the right owner, and
  the right number of things.
* Whether a DAG is the correct organizing structure given `029-DL`'s headline
  finding that **structure survives iff a machine produces it or penalizes its
  absence**, and given that `029-DL` pruned one DAG candidate on a measured 0%
  defect rate.
* How remediation loops are represented without reintroducing the
  non-termination `028-DL` diagnosed.

## Research Findings

### R1 — The four inherited laws are intact and constrain the design

`029-DL` survived three adversarial rounds and produced laws that this artifact
adopts without amendment except where explicitly noted:

| Law | Statement | Status here |
|---|---|---|
| **Law 1 — DERIVE, NEVER PERSIST** | Analyzers compute the graph as a read-time view over markdown/config that already exists for an independent reason; no analyzer may persist a graph. | **ADOPTED.** One narrowly-justified exception (§DAG Contract, D9) for a HEAD-keyed evidence *report*, which is not a graph. |
| **Law 2 (CORRECTED) — PRODUCE OR PENALIZE** | A convention survives iff a machine either produces it or penalizes its absence. Being read is neither necessary nor sufficient (p = 1.97e-05, confound isolated). | **ADOPTED, and it is the single strongest constraint on this portfolio.** It kills any detector that requires authors to mint new per-artifact identifiers. |
| **Report-only first slice** | Every candidate starts read-only, always exit 0; promotion to blocking is a separate authority-expanding decision. | **ADOPTED** (`028-DL` §9.1, `029-DL` §8, §A9). |
| **Authority test v2** | Consent required if the gate creates a novel obligation **or** its activation blast radius against the current corpus exceeds a stated threshold. | **ADOPTED**, and it supplies the migration story: detectors that validate Stage's own harvest output are intrinsically enforce-on-new-only, day-one blast radius zero. |

Two further inherited constraints:

* **A3 — ready-set without a total order is not determinism.** Any ready-set of
  size > 1 hands the agent a choice. `compute_next_eligible`'s `(-fan_out, id)`
  tie-break (`topology.py`) is the in-repo reference and must be imitated.
* **A8 — never invent node identity.** `029-DL` §C1.2 partitioned nine closed
  surfaces on exactly this test: seven survive, and the two that die
  (impl-plan units needing `R#`, acceptance criteria needing `ACn`) die
  precisely because they require authors to mint identifiers.

### R2 — The `029-DL` C4.2 blocker has been cleared since 2026-08-25

`029-DL` ended **BLOCKED** on a named harness gap: "autoharness ships the entire
Stage planning gate chain to consumer workspaces and installs none of it for
itself" (4 of 29 skills installed).

**Measured this session: `.github/skills/` now contains 18 skills**, including
`impl-plan`, `plan-harden`, `plan-review`, `harvest`, `deliberate`, `spike`,
`review`, `fix-ci`, `pr-lifecycle`, `operational-closure`, `runtime-verification`,
and `shipment-reconcile`. **The Step-3 planning gate is now structurally
available in this workspace.** `029-DL`'s criterion 1 is satisfied; its criteria
2 and 3 remain open and are re-inherited below as Open Decisions.

This is the single most consequential state change since `029-DL` and is why a
staging deliberation is appropriate now rather than another deferral.

### R3 — Two hidden prerequisites are already captured and must not be duplicated

| Stash | Nature | Consequence for this portfolio |
|---|---|---|
| `336F3AB7` (critical bug) | "Policy registry and review-persona layer are cited repo-wide but were never installed." **Verified**: `templates/policies/workflow-policies.md.tmpl` exists; no installed counterpart. | **Hard external prerequisite** for any detector that cites a policy ID (plan soundness, circuit breaker, human-routing) and for the persona-routing decision in F14. Owned by `336F3AB7`, **not re-owned here**. |
| `8AC574F1` (high bug) | 13 referenced skills not installed. | **Largely satisfied** (18/29 now present). Residual gap (`brainstorm`, `build-feature`, `compound`, `learn`, `doc-review`, `harness-doctor`, `security-audit`, others) does not block this portfolio. Downgrade recommended; **not re-owned here**. |

### R4 — The existing gate surface is the correct substrate, and it is small

Measured surface:

* `autoharness gate {check, size, copilot-review, pipeline-topology, dag-readiness}`
  (`src/autoharness/cli.py` L358-366).
* `autoharness verify-workspace` (`verify_workspace.py`, 226 KB) already owns
  `PORTABILITY_RULES` + `PORTABILITY_ALLOW_LIST` (L958-L1000), `checksum_scan`
  with `user-modified` / `checksum-untracked` statuses, and the `upstream_updated`
  template-mirror comparison (L5056-L5076).
* `gates/discovery.py::discover_modified_files` already produces the changed-file
  set every applicability predicate needs.
* `gates/topology.py` already implements `CheckResult{name,status,token,message,details}`,
  `TopologyResult` with exit codes 0/1/2/3, three-colour cycle detection,
  `compute_dag_readiness` (`ready_set`, `critical_path`), and
  `compute_next_eligible` with a deterministic total order.
* `schemas/validation-gates.schema.json` (v1.0.0) is the declaration extension point.
* `.autoharness/gates/` already carries force-audit logs and gate telemetry —
  the audited-override precedent already exists in file form.

**Conclusion: no new scheduler, no new persistence layer, no new verdict
vocabulary, and no new backlogit change are required.** Requirement 13 is
satisfiable by extension, not by new plumbing. This mirrors both `028-DL` §8 and
`029-DL` §7 finding that a zero-change cross-repo boundary is itself evidence the
boundary is correct.

### R5 — The imported entries and the spike families do not cover the same ground

This is the central reconciliation finding, and it cuts both ways.

**Families with high measured recurrence that NO imported entry covers:**

| Family | PRs | Gap |
|---|---|---|
| **F10** template/placeholder parity | **71** (2nd largest) | `39AA674D` is *transport* parity (CLI vs MCP vs event), not template↔installed-mirror parity. Entirely uncovered. |
| **F08** platform/shell portability | 55 | Uncovered. Existing `PORTABILITY_RULES` is the cheapest delta in the whole program and no entry claims it. |
| **F09** injection/traversal/secret leakage | 35, **67% high-round** | `A02280C8` mentions "fail-open branches" (F05) but not containment. Uncovered. |
| **F02** enumeration/registry drift | 27 | Uncovered. |
| **F07** status/outcome conflation | 30 | Uncovered. |
| **F03a** normative-surface contradiction | **135 (largest)** | Uncovered, and correctly so — it is not mechanizable at acceptable precision. Requires an explicit human-routing decision, not a checker. |
| **F14** resource/concurrency | 18, **76% high-round** | Uncovered, and correctly so. Spike recommends mandatory Concurrency Reviewer persona + non-optional hosted review. |

**Imported entries whose in-repo consumer is absent or cross-repo:**

`39AA674D` (cross-surface golden parity) and `926FEA6D` (mutation postcondition)
both declare backlogit as "pilot and live validation". autoharness's own
`workspace-profile.yaml` declares exactly one runtime surface (`cli: true`;
`public_api: false`, `web_ui: false`, `background_jobs: false`). **A cross-surface
parity framework in a single-surface repository is a framework with no in-repo
reader — the exact F5 / Law-2 failure mode.** Same for a mutation-postcondition
framework whose state adapters all live in another repository.

**Two entries are broader than their evidence:**

* `D911A3B2` calls for "evidence persistence". Under Law 1 that is a data-loss
  architecture unless narrowly justified. Scope must be narrowed to a HEAD-keyed
  report, never a persisted graph.
* `89E833E1` calls for "query/visualization". No reader has been named for it;
  under Law 2 it decays. Prune until a consumer exists.

### R6 — A direct evidence conflict between the spike and `029-DL` on F01

The spike ranks **cross-reference integrity (F01) as Tier 1 #4** on 28 PRs of
Copilot recurrence. `029-DL` §C1.3 **pruned exactly this candidate on
measurement**: 400 markdown links across `docs/`, `.github/`, `templates/`,
`AGENTS.md`, `README.md`; 343 resolve locally; 4 dangling, all documentation
placeholders — **real defect rate 0%**.

These are reconcilable and the reconciliation is load-bearing:

> `029-DL` measured **markdown link syntax** on the *current* tree. The spike's
> F01 population is a **superset**: paths cited inside prose and template
> comments (PR #115 cited a `docs/reference/…` path from inside a template
> comment — invisible to a markdown-link extractor), `file:line-range`
> citations, plan references to product templates that do not exist (PR #258),
> and citations on the *diff*, not the current tree, many of which were fixed
> during review and therefore cannot appear in a present-tense scan.

**Consequence, recorded as a hard gate:** the F01 detector must be scoped to
`superset minus plain markdown links`, and **S4 may not be planned until
retro-validation demonstrates non-zero yield on that reduced surface**. If it
cannot re-detect PR #115 and PR #258, it is ceremony and must be dropped — the
same standard `029-DL` §C1.3 applied to itself.

### R7 — Remediation loops are the unaddressed structural problem

The spike's mechanism finding #3 is decisive:
`docs/compound/2026-08-07-copilot-review-fix-introduces-new-filter-bug.md` records
three consecutive rounds in which **each fix for an unsafe filter introduced a
subtler unsafe filter**. `093-S` records 13 rounds where the final convergence
pass fixed 9 findings and still surfaced 2 new hard blockers.

A naive "remediate and re-run" edge is therefore a genuine cycle in the runtime
sense even though it is acyclic in the graph sense. **The resolution adopted here
is epoch indexing** (§DAG Contract, D6): the DAG is acyclic *within* a HEAD-keyed
epoch, remediation advances the epoch, and the epoch counter — not the graph — is
what the circuit breaker bounds. This is the direct application of `028-DL` §4.1's
empirical finding that **push, not thread resolution, is the epoch boundary**.

## Normalization of the Imported Scope

Disposition of every imported entry. `retain` = keep as written; `split` = divide
across shipments; `merge` = fold into another entry's scope; `defer` = keep in
stash at adjusted priority, do not stage; `supersede` = replaced by prior art.

| Stash | Kind / pri | Disposition | Rationale | Target shipment(s) |
|---|---|---|---|---|
| `D911A3B2` | epic / critical | **RETAIN (scope-narrowed)** | Correct program frame. Two narrowings: "evidence persistence" is bounded to a HEAD-keyed report under Law 1; "extension points for repository-specific adapters" is deferred until a second consumer repository actually exists (Law 2 — a framework with one consumer is a library, not a framework). | Program epic over **S1–S10** |
| `39AA674D` | feature / critical | **DEFER** (priority critical -> low) | autoharness declares one runtime surface. No in-repo consumer; pilot and every transport adapter live in backlogit. Staging it here builds an unread framework. Revisit when autoharness itself grows a second surface, or re-home to backlogit. | **S11** (deferred), not staged |
| `926FEA6D` | feature / critical | **SPLIT + mostly DEFER** (critical -> low) | Same cross-repo consumer problem. **Split:** the *crash-boundary / non-idempotent-resume* invariant subset is a real in-repo F13 concern and merges into S7; the representation/atomicity/state-adapter framework defers. | subset -> **S7**; remainder **S11** |
| `A02280C8` | feature / high | **SPLIT** | Two separable things fused. **(a) Analyzer-pack discovery + registration + evidence output** is a genuine prerequisite for the entire AST tier and is retained at high priority. **(b) Compatibility corpus, fuzz/property matrices, legacy-version and platform execution** is a distinct, heavier concern with no measured in-repo recurrence and defers. | (a) -> **S5**; (b) -> **S11** |
| `3F80F8A3` | feature / high | **SPLIT** | Fuses two determinism classes. **(a) API-derived provenance** (reviewed HEAD, review cycles, unresolved threads, CI state, merge SHAs, shipment membership, closure facts) is class C3. **(b) Documentation validator** (frontmatter, tables, headings, numeric/topology claims, symbol/path citations, task refs, stale terminology, comment drift) is class C1/C4. Different producers, different failure modes, different retro-validation corpora. | (a) -> **S4-PROV**; (b) -> **S4-DOC**, both inside **S4** |
| `C327A8DE` | feature / high | **RETAIN + MERGE** | Plan/work-item soundness and the Tier-1 backlogit artifact linter (F12) are the same surface read at two moments (pre-harvest and post-harvest). Splitting them duplicates the artifact reader. Merge into one D-ART shipment. **This is the archetypal enforce-on-new-only gate** — it validates Stage's own harvest output, day-one blast radius against 612 existing tasks is exactly zero. | **S2** |
| `7A3F570B` | feature / high | **RETAIN + MERGE** | Red-test honesty (`7A3F570B`) and the vacuous-test detector (spike Tier 2 #8, F06) are one coverage-instrumented mechanism with two assertions (fails-before, executes-the-new-lines). | **S6** |
| `89E833E1` | feature / critical | **SPLIT (3 ways)** | Fuses foundation, composition, and policy. **(a) Detector/evidence-node SDK + node contract** is the foundation everything else plugs into. **(b) DAG family assembly + incremental evaluation + shipment attachment** composes the detectors. **(c) "Require verified evidence at every applicable terminal node before review readiness" + waiver/override authority** is a blocking-policy promotion and must not travel with (a) or (b). **Prune** "query/visualization" until a reader exists. | (a) -> **S1**; (b) -> **S8**; (c) -> **S10** |
| `8CB5A9B9` | feature / high | **RETAIN, DEPENDENCY-DEFERRED** | Correct and well-evidenced (PR #348 breaker deliberately exceeded twice; `128-S` 3-of-3 cap consumed with round 5 still finding). But it cannot be built before there is a machine-derived cycle count, which is `028-DL` Phase 1. And moving a limit "from prompt-only policy into harness state transitions" is authority-expanding by `028-DL` Q1. | **S10**, gated on **S9** |
| `34AAF1C7` | feature / medium | **RETAIN as living tracker; SPLIT recommended, not executed** | `028-DL` Q4's recommended split — (a) PR-review convergence [executable] vs (b) reasoning-state identity [still blocked] — remains unexecuted. This artifact consumes only branch (a) via S9. Branch (b) is untouched and still blocked on inventing node identity (A8). Splitting a living tracker is an operator-visible reclassification and is **not performed here**. | (a) -> **S9**; (b) stays in stash |

### Missing fault lines added to the program by this normalization

The imported nine, taken alone, would have built the program around its weakest
half. These are added as first-class scope:

| Added scope | Family | Evidence | Owning shipment |
|---|---|---|---|
| Template/placeholder parity + installed-mirror integrity | **F10** | 71 PRs; `verify_workspace` `upstream_updated` exists and PR #53 proves its checksum semantics are wrong | **S3** |
| Enumeration/registry set-equality | **F02** | 27 PRs; PR #196, #183, #3 | **S3** |
| Containment / injection / secret-leak AST guard | **F09** | 35 PRs, 67% high-round; PR #326 redaction leak | **S5** |
| Exit-status contract guard | **F07** | 30 PRs; `set -e` and `$LASTEXITCODE` classes | **S5** |
| Portability scan extension | **F08** | 55 PRs; lowest marginal cost — extends `PORTABILITY_RULES` | **S5** |
| Status-lattice conformance | **F13** subset | 87 PRs; PR #386 deadlock class | **S7** |
| SSOT governed-token check | **F03a** subset | 135 PRs; only a narrow mechanical subset is reachable | **S7** |
| Explicit human/persona routing policy | **F03a** general, **F14** | 76% high-round on F14; local-only governance findings Copilot structurally cannot raise | **S10** (routing policy), no detector |

## Options Evaluated

### Option A: Independent gates

Each fault-line family becomes its own top-level `autoharness gate <name>`
subcommand, following the `pipeline-topology` / `dag-readiness` precedent
exactly. No shared abstraction. Callers compose them in agent prose or CI.

**Pros.** Zero new abstraction; each gate is independently shippable, testable,
and deletable; matches every existing gate in the repo; smallest possible first
slice; a failing gate cannot break its siblings.

**Cons.** Composition lives in prose, which is precisely the `029-DL` cell-4
condition (no producer, no penalty) that decayed to 15%. Every gate re-implements
applicability, changed-file discovery, evidence emission, provenance pinning, and
verdict mapping — five duplications across ten-plus detectors. There is no single
place to answer "is this shipment review-ready?", which is the actual operator
question. Cross-detector dependencies (red-test proof must precede test-evidence
consumption) become undeclared ordering conventions — the exact `_prior_shipment_id`
defect class that has already shipped two bugs.

### Option B: Monolithic meta-gate

One `autoharness gate pre-review` that internally hard-codes every check in a
fixed sequence and emits a single verdict.

**Pros.** One reader, one invocation, one report; composition is code, not prose;
trivially answers the operator question; no plugin machinery to design.

**Cons.** No applicability model, so it runs template checks on Python-only diffs
and AST checks on docs-only diffs — inflating cost and false positives on exactly
the surfaces the spike says are already noisy. Every new detector edits one large
module (blast radius grows monotonically). Report-only and blocking checks cannot
be mixed cleanly, so the report-only-first law becomes an all-or-nothing switch.
Retro-validating one detector requires running all of them. And it repeats
`028-DL` §2.1's cardinal error at a different level: collapsing distinct evidence
families with different validity rules, owners, and consumers into one object.

### Option C: Detector/evidence-node SDK plus composable derived DAG families (SELECTED)

A small in-tree SDK (`src/autoharness/detectors/`) defines one node contract. Each
detector is a pure function `(applicability_context) -> NodeResult` registered in a
declarative registry. A **derived-at-read-time** DAG is assembled per invocation
from the registry plus repo state — never persisted. One reader,
`autoharness gate pre-review`, walks it. Detector *domains* are the composable
families; individual detectors are the nodes.

**Pros.** Applicability, changed-file discovery, provenance pinning, evidence
emission, verdict mapping, and cycle detection are written once. Each detector is
independently retro-validatable and independently promotable from report-only to
blocking, satisfying requirement 9 structurally rather than by discipline. New
detectors are additive registry entries, so blast radius per addition is
bounded. Reuses `CheckResult`/`TopologyResult`, `discover_modified_files`, the
three-colour cycle detector, and `validation-gates.schema.json`. Composition is
machine-read, so it lands in Law 2's produced cell rather than the prose cell.
The DAG is derived, so Law 1 and `028-DL` §2.2's disposable-cache objection are
dissolved.

**Cons.** The SDK is genuinely new abstraction, and an SDK with no detectors is
the archetypal write-only artifact (`029-DL` F5). This is mitigated, not
hand-waved: **S1 must ship one real detector end-to-end** or it does not ship.
Registry-based indirection is harder to read than a straight-line gate. There is
a real risk of over-generalizing toward the deferred cross-repo adapter model in
`D911A3B2` — explicitly ruled out of S1 scope.

### Option D: Extend `verify-workspace` only

Add every check as a new finding class inside the existing 226 KB
`verify_workspace.py`, reusing `PORTABILITY_RULES`, `checksum_scan`, and the
existing severity ladder (strict blockers / blockers / warnings / migration
proposals).

**Pros.** Cheapest possible first slice; a mature severity ladder and allow-list
mechanism already exist; one command operators already run; zero new surface.

**Cons.** `verify-workspace` is a *workspace installation integrity* command, not
a *change-scoped pre-review* command — it has no diff, no base/head provenance,
no epoch, and no per-shipment applicability. Bolting change-scoped detectors onto
it conflates two audiences. The module is already 226 KB and the largest in the
tree; adding ten detector families to it is a width-isolation violation at the
architecture level. And it cannot express inter-detector dependencies at all.

## Trade-off Comparison

| Criterion | A: Independent gates | B: Monolithic meta-gate | **C: SDK + derived DAG** | D: Extend verify-workspace |
|---|---|---|---|---|
| First-slice cost | **Lowest** | Low | Medium | **Lowest** |
| Duplication across detectors | High (5x per detector) | None | **None** | Medium |
| Applicability / change-scoping | Per-gate, ad hoc | **Absent** | **First-class** | Absent |
| Answers "is this review-ready?" | No | **Yes** | **Yes** | No |
| Inter-detector dependency expression | Prose only (decays) | Hard-coded order | **Declared edges, cycle-checked** | **Impossible** |
| Per-detector report-only -> blocking promotion | Yes | **No (all-or-nothing)** | **Yes** | Partial (severity ladder) |
| Per-detector retro-validation | **Yes** | No | **Yes** | Partial |
| Blast radius per new detector | Low | **Grows monotonically** | **Bounded (registry entry)** | Grows monotonically |
| Law 1 (derive-never-persist) | Satisfied | Satisfied | **Satisfied** | Satisfied |
| Law 2 (produced or penalized) | **Fails** — composition is prose | Satisfied | **Satisfied** | Satisfied |
| Reuses existing gate substrate | **Fully** | Fully | **Fully** | Fully |
| Risk of write-only abstraction | None | None | **Real — mitigated by S1 shipping a detector** | None |
| Width isolation | Good | Poor | **Good** | **Poor** |

## Decision

**Adopt Option C: a detector/evidence-node SDK with composable, derived-at-read-time
DAG families, read by a single `autoharness gate pre-review` command, landing
report-only and promoted per-detector.**

The decision turns on three criteria that Option C alone satisfies simultaneously:

1. **Inter-detector dependency must be machine-expressed.** The red-test proof
   must precede consumption of test evidence; provenance must be pinned before
   any evidence claim is validated; plan soundness must precede work-item
   conformance. Option A leaves these as prose conventions, and `029-DL` measured
   what happens to prose conventions with no producer and no penalty: decay to
   15% adoption. Option D cannot express them at all.
2. **Per-detector promotion is a hard requirement, not a preference.**
   Requirement 9 and the inherited report-only-first law demand that report-only
   infrastructure land before any fail-closed promotion, and that promotion be
   evaluated per detector against its own measured precision. Option B forces one
   global switch and therefore cannot comply.
3. **Applicability is what makes the false-positive budget achievable.** The
   spike's own limitation #5 names unmeasured false-positive cost as the reason
   nothing may block yet. A detector that only runs when its path class is in the
   changed-file set has a structurally smaller false-positive surface. Options B
   and D have no applicability model.

**Explicitly preserved from `029-DL`:** derive-never-persist; no-graph-without-a-
reader (strengthened here to *no SDK without a detector*); read-only/report-only
first slices; promotion to blocking as a separate authority decision. **None is
overturned; no evidence gathered this session contradicts any of them.**

**Explicitly preserved from `028-DL`:** acyclicity does not imply termination;
the epoch boundary is a push, not a resolution; backlogit never learns what a
review finding or a convergence threshold is; the harness reads and writes only
through backlogit's public MCP/CLI surfaces.

**One scope narrowing applied to the operator's framing.** The request asks for a
DAG that "mechanically and deterministically identifies, addresses, and
remediates" fault lines. **Identification is fully mechanizable. Remediation is
not**, and the portfolio does not pretend otherwise: only two of six remediation
classes may mutate anything automatically (§Mechanical Remediation Classes), and
both are confined to machine-produced artifacts. Claiming automated remediation
across the board would be an F03b overclaim — prose asserting a guarantee the
code cannot provide — inside a document whose purpose is to detect exactly that.

## Rejected Alternatives

* **Option A (independent gates)** — rejected on criterion 1. Its composition
  layer is prose, which is empirically the decaying cell. It remains the correct
  answer if the SDK proves unjustified after S1; the fallback is explicitly cheap
  because each detector is a pure function either way.
* **Option B (monolithic meta-gate)** — rejected on criteria 2 and 3, and on
  repeating `028-DL` §2.1's four-graphs-collided-into-one error.
* **Option D (extend verify-workspace)** — rejected on audience conflation and
  width isolation. Note the partial adoption: **S5 deliberately extends
  `PORTABILITY_RULES` in place** rather than reimplementing it, because that
  specific control already exists, already has an allow-list mechanism
  (`docs/compound/012-S-portability-scan-allow-list.md`), and its extension is
  the lowest-marginal-cost item in the whole program. Rejecting D as the
  *architecture* does not mean rejecting reuse of its *controls*.
* **A persisted evidence graph** (implied by `D911A3B2`'s "evidence persistence")
  — rejected under Law 1 and `028-DL` §2.2. Derived views cannot be destroyed by
  `backlogit_sync_index`; persisted ones can.
* **A separate scheduler or work queue for detector execution** — rejected per
  requirement 13 and `dag-readiness`'s permanent no-scheduler non-goal. Ordering
  comes from declared edges evaluated in one process; shipment sequencing comes
  from backlogit `blocks` edges that already exist.
* **Building `39AA674D` / `926FEA6D` now** — rejected on the absence of an
  in-repo consumer. Deferred to S11, not deleted.
* **A general-case F03a contradiction detector** — rejected on the spike's own
  measurement: broadening to catch it produced a 659-finding catch-all driven by
  the bare idioms "even though" and "still says". Only the SSOT governed-token
  subset is built.

## Taxonomy

### Determinism classes (the vertical axis)

Every fault line is assigned exactly one class. The class dictates the producer,
the retro-validation method, and whether promotion to blocking is ever reachable.

| Class | Name | Definition | Producer | Promotion ceiling |
|---|---|---|---|---|
| **C1** | Fully deterministic, closed surface | Decided by a filesystem predicate, a set-equality, or a declared-shape match over a closed, enumerable vocabulary. No inference. | Pure function over repo files + backlogit markdown | **Blocking reachable** |
| **C2** | AST / coverage / property | Decided by parsing to a syntax tree, by coverage instrumentation, or by executing a property over a generated input set. Deterministic given the same tree and the same tool version. | AST walker or instrumented test run | **Blocking reachable**, tool-version-pinned |
| **C3** | API / provenance-derived | Decided against an authoritative external record (GitHub API, git object store, backlogit state). Deterministic given the same records, but availability-dependent. | Read-only API/CLI query | **Blocking reachable**, fail-closed on unavailability |
| **C4** | Mechanized semantic subset | The general family is semantic; a strictly narrower predicate is mechanical. The subset must be stated, and findings must never be labelled as covering the family. | Same as C1/C2 over a restricted surface | **Report-only ceiling** until precision measured; blocking only with named subset |
| **C5** | Irreducibly human / persona | No mechanical predicate at acceptable precision. Value comes from *routing* to the right reviewer, not from detection. | Human, persona, or hosted review | **Never blocking as a detector**; may be a mandatory routing obligation |

### Detector domains (the horizontal axis)

The 15 spike families plus the imported concerns consolidate into **six
mechanical domains plus one routing domain**. Consolidation is by *mechanism and
producer*, not by topic — the spike's own v1 taxonomy failure (a 609-finding
"workflow-state" bucket) is the recorded evidence for why topic grouping fails.
Traceability is preserved because every family keeps its own detector ID inside
its domain; the domain is a packaging unit, never a merge.

| Domain | Name | Mechanism | Families | Classes | Owning shipment |
|---|---|---|---|---|---|
| **D-ART** | Artifact conformance and plan soundness | Declared-shape match over `.backlogit/**` markdown + plan artifacts; width/granularity budgets | F12, `C327A8DE` | C1 | **S2** |
| **D-PAR** | Parity and enumeration agreement | Set equality and mirror-parity between two declared surfaces | F10, F02, F04-subset | C1, C4 | **S3** |
| **D-PROV** | Provenance, freshness, and documentation validity | Authoritative-record comparison + citation resolution + dangling-definition reachability | F11, F01, F03b-subset, `3F80F8A3` | C3, C1, C4 | **S4** |
| **D-CODE** | Code-safety static analysis | AST structural guards over `src/**` and shell/PowerShell scripts | F05, F09, F07, F08 | C2 | **S5** |
| **D-TEST** | Test honesty and coverage | Base-revision execution + coverage instrumentation | F06, `7A3F570B` | C2 | **S6** |
| **D-STATE** | Lifecycle and state semantics | Status-lattice membership/transition legality; governed-token identity | F13-subset, F03a-subset, `926FEA6D`-subset | C4 | **S7** |
| **D-HUMAN** | Routing obligations (no detector) | Mandatory persona and hosted-review routing by path class | F14, F03a general, F04 semantic, F13 ordering, governance/authority findings | C5 | **S10** (policy) |

**Why six and not fifteen.** Each domain shares one producer and one evidence
shape, so the SDK writes its applicability and evidence emission once. Each
domain also shares a retro-validation corpus, so precision is measurable per
domain and per detector without fifteen separate replay harnesses.

**Why not fewer.** Collapsing D-PROV into D-PAR would merge C3 (availability-
dependent, fail-closed) with C1 (pure predicate) — different failure semantics.
Collapsing D-TEST into D-CODE would merge a *static* producer with one that must
*execute* the suite at a base revision. Both merges would repeat the
four-graphs-collided error.

### Explicit distinctions the operator asked for

* **Fully deterministic closed-surface (C1):** D-ART entirely; D-PAR's mirror
  parity, unresolved-placeholder scan, variable-table set equality, enumeration
  agreement; D-PROV's citation resolution.
* **AST / coverage / property (C2):** D-CODE entirely; D-TEST entirely.
* **API / provenance-derived (C3):** D-PROV's reviewed-HEAD comparison, review
  cycle counts, unresolved-thread state, CI verdict, merge SHAs, shipment
  membership and status, task counts, closure facts.
* **Mechanized semantic subsets (C4), with the subset named:**
  * F04 -> "every backlogit MCP/CLI parameter named in `templates/**`,
    `.github/agents/**`, `.github/skills/**` exists in the installed tool's
    advertised `params` map in `.autoharness/backlog-registry.yaml`."
  * F03b -> "a variable/list/step introduced in an agent contract is referenced
    by at least one later step" and "a documented config key is read by at least
    one code path."
  * F13 -> "every status literal used in an agent contract is in the modelled
    lattice, and every named transition is legal."
  * F03a -> "when a governed token appears in two or more governed surfaces, the
    claim-bearing text is byte-identical or an explicit cross-reference."
* **Irreducibly human (C5):** F14 concurrency and acquire/release ordering;
  general F03a contradiction between differently-worded normative surfaces;
  F04 semantic strictness drift; F13 TOCTOU and fail-closed filter placement;
  and the entire **local-only governance class** — role boundaries, P-021 scope
  containment, review-cycle-budget dispositions, and "who is authorised to
  perform this mutation". The spike records that **Copilot structurally cannot
  raise these**, which is the strongest evidence that deterministic tooling must
  be additive and must displace neither review surface.

## DAG Contract

### D1 — Node identity

Nodes are named in the `029-DL` Universal Artifact Reference style, extended with
one scheme. **No new identifier is minted for any artifact** (A8):

```text
det:<domain>/<detector-id>@<version>     e.g. det:D-PAR/PAR-01@1
```

`domain` and `detector-id` come from the registry; `version` is the detector's
own contract version and increments only on a semantics change. Evidence and
subject references reuse existing schemes unchanged:
`bl:115.001-T`, `path:templates/agents/ship.agent.md.tmpl`, `git:8996b46`,
`gh:pr/348`, `gh:thread/<nodeid>`.

Node *instance* identity within a run is `(node_id, epoch)` where epoch is
defined in D6. Instance identity is never persisted as an identifier; it is
recomputed.

### D2 — Applicability predicate

Every node declares `applies_when`, evaluated against an applicability context
built once per run from `discover_modified_files` (`gates/discovery.py`), the
resolved shipment manifest, and the workspace profile:

```yaml
applies_when:
  changed_paths_any: ["templates/**", ".github/**"]     # glob, gates/match.py semantics
  shipment_has_items_of_type: ["task"]                  # optional
  workspace_surfaces_any: ["cli"]                       # optional, workspace-profile.yaml
  always: false
```

**Fail-closed rule (FC1).** If the applicability context cannot be built — the
diff base is unresolvable, the manifest is unreadable, the profile is missing —
the node evaluates to `insufficient_evidence`, **never** to `not_applicable`.
Silently pre-filtering a node out of its own enumeration is the F13 defect class
this program exists to catch, and the harness must not commit it.

**Recorded non-applicability (FC2).** Every `not_applicable` verdict records the
predicate clause that excluded it. An unaudited non-applicability decision is
indistinguishable from a skipped check.

### D3 — Evidence producer and validator

The two are separated so that evidence can be produced once and validated by
several nodes (requirement 10's "multiple consumers of evidence").

```yaml
producer:
  kind: pure | ast | coverage | api | command
  ref: "autoharness.detectors.par.mirror_parity:produce"
  tool_version_dims: ["python", "gh"]        # required for kind: ast|coverage|api
validator:
  ref: "autoharness.detectors.par.mirror_parity:validate"
  consumes: ["det:D-PAR/PAR-01@1#evidence"]  # may reference sibling evidence
```

A producer emits an `Evidence` record; a validator is a pure function over
evidence and returns a verdict. **A validator may consume evidence produced by an
upstream node but may never re-run that node's producer** — this is what makes
incremental evaluation possible without duplicate execution.

### D4 — Dependencies and cycle detection

```yaml
depends_on: ["det:D-TEST/TEST-01@1"]
```

Edges mean **"must be evaluated, and must not have verdict `failed`, before this
node is evaluated"**. Two rules:

* The registry is validated with the **three-colour cycle detection already
  implemented in `topology.py`**. A cycle is a **registry defect**: the run exits
  `2` (invalid) and evaluates nothing. It is never tolerated and never
  auto-broken.
* An upstream node with verdict `failed` or `insufficient_evidence` yields
  `blocked_upstream` downstream — **not** `passed`, and **not** `skipped`.
  Downstream silence on upstream failure is the fail-open class the program is
  built to eliminate.

### D5 — Verdict and status vocabulary

Reuses `CheckResult{name,status,token,message,details}` and `TopologyResult`
exit-code semantics unchanged; the extension is three additional statuses.

| Verdict | Meaning | Report-only exit | Blocking-mode exit |
|---|---|---|---|
| `passed` | Applicable, evidence present, validator satisfied | 0 | 0 |
| `failed` | Applicable, evidence present, validator violated | **0** | 1 |
| `insufficient_evidence` | Applicable, evidence missing/unreadable/stale (FC1) | **0** | 1 |
| `blocked_upstream` | A `depends_on` node did not pass (D4) | **0** | 1 |
| `not_applicable` | Predicate excluded it; exclusion clause recorded (FC2) | 0 | 0 |
| `skipped` | Detector disabled in `.autoharness/config.yaml` | 0 | 0 |
| `waived` | Audited override present, in date, in scope (D10) | 0 | 0 |
| `invalid` | Registry/config defect: cycle, bad schema, unknown ref | 2 | 2 |

**In v0 every detector is report-only and the run always exits 0** unless the
registry itself is invalid (exit 2). Exit 2 for a registry defect is not a policy
promotion — it is the gate refusing to report a result it cannot compute.

### D6 — Provenance, epoch, and freshness

Every node result carries:

```yaml
provenance:
  base_sha: "<merge-base of head and default branch>"
  head_sha: "<current HEAD>"
  reviewed_sha: "<HEAD the last review round was keyed to, or null>"
  platform: "windows|linux|darwin"
  tool_versions: {python: "3.13.x", gh: "2.x", backlogit: "1.10.1"}
  produced_at: "<RFC3339>"
```

**The epoch is `head_sha`.** This is the direct adoption of `028-DL` §4.1's
empirical finding that a push, not a thread resolution, is the review-round
boundary. `gate_evidence.head_sha` is the correct in-repo pinning precedent
(`028-DL` §2.2, §R5).

**Freshness rule.** A node result is fresh iff its `head_sha` equals current
HEAD **and** every `tool_versions` dimension it declared in
`producer.tool_version_dims` is unchanged. A stale result is
`insufficient_evidence`, never a reused `passed`. This is the direct mechanization
of family F11, applied to the harness's own output — the program must not commit
the defect it detects.

**Docs-only epochs.** Per `028-DL` R2, epochs are additionally labelled
`touches_reviewable_paths: true|false` so that documentation-only pushes do not
inflate the epoch count the circuit breaker bounds.

### D7 — Severity and blocking policy

Severity and mode are **orthogonal**, and conflating them is how a report-only
program silently becomes a blocking one.

```yaml
severity: critical | high | medium | low     # analyst-assigned consequence
mode: report_only | blocking                 # authority-bearing, per-detector
```

`severity` is advisory metadata for triage ordering. `mode` is the only field
that changes exit codes, defaults to `report_only` for **every** detector, and
may be changed to `blocking` **only** by the S10 promotion gate against the
criteria in §Rollout and Promotion Gates. **A detector may never set its own
`mode`, and no detector ships with `mode: blocking`.**

### D8 — Remediation class and fix hint

Every node declares one remediation class from the six in §Mechanical
Remediation Classes, plus a structured hint:

```yaml
remediation:
  class: auto_fix_safe | guided_fix | regenerate | require_plan_revision | require_human_review | policy_halt
  hint: "Re-render from templates/agents/ship.agent.md.tmpl; do not hand-patch the installed copy."
  target_refs: ["path:templates/agents/ship.agent.md.tmpl"]
  authority: none | ship | stage | operator
```

### D9 — Artifact references and the one persistence exception

Nodes reference evidence by UAR. **The graph itself is never persisted** (Law 1):
it is reassembled from the registry on every invocation, so
`backlogit_sync_index` cannot destroy it and no schema migration is ever needed.

**The single justified persistence exception** is the run *report*:
`.autoharness/gates/pre-review/<head_sha>.json`, append-only per epoch, alongside
the existing `.autoharness/gates/*-force-audit.log` and
`pipeline-topology-telemetry.jsonl` precedents.

Justification, stated so it can be challenged: the report is (a) **not a graph** —
it is a flat list of node results, so no derived topology is stored; (b) **keyed
by immutable epoch**, so it is a historical record rather than mutable state, and
unlike `gate_evidence` it is not overwritten (`028-DL` §2.2 R5); (c) **required by
a named consumer** — the PR body's readiness block and the closure record's
`conditions:` block, which are exactly the F11 surfaces that today carry
unverified claims; and (d) reconstructible from the tree at that SHA, so its loss
is a cost, not a correctness failure. **If no consumer is wired in S8, the report
must not be written** — Law 2 applies to the harness's own output.

### D10 — Waiver and override semantics

A waiver is a scoped, dated, authored record that converts an applicable `failed`
into `waived`, and **only** in `blocking` mode — waiving a report-only finding is
meaningless and is rejected as `invalid`.

```yaml
waiver:
  node_id: "det:D-PAR/PAR-01@1"
  scope_refs: ["path:templates/skills/fix-ci/SKILL.md.tmpl"]   # never a bare glob
  rationale: "<required, non-empty>"
  approver: "<operator identity>"
  expires_at: "<RFC3339, required, bounded>"
  recorded_at: "<RFC3339>"
```

**Non-negotiable constraints.** A waiver (i) is written to the existing
`.autoharness/gates/` audit-log surface, never to a detector's own config; (ii)
**cannot be self-issued by an agent** — `authority: operator` is required; (iii)
is scope-bounded to named refs, never repo-wide; (iv) expires, and an expired
waiver is inert, not renewed; and (v) **carries no authority over any other
control.** A waiver on a pre-review detector never authorizes a destructive
action, never substitutes for merge-commit policy (P-009), never relaxes
worktree/branch topology (P-014), never satisfies a closure obligation (P-018),
and never permits a compaction or archival decision (P-020). Those approvals
remain separately required and separately recorded.

## The End-to-End DAG

Eleven stages, modelled as an executable checklist. `->` is a `depends_on` edge.
Every node is report-only in v0.

```text
                    [N00] intake / plan produced
                            |
                    [N10] D-ART plan soundness
                            |
                    [N20] D-ART work-item conformance
                            |
        +-------------------+-------------------+
        |                                       |
  [N30] D-TEST red-test proof            [N40] D-CODE static/AST
        |                                       |
        +-------------------+-------------------+
                            |
                  [N50] D-PAR parity / enumeration
                            |
                  [N55] D-STATE lattice / SSOT tokens
                            |
                  [N60] D-PROV provenance / docs
                            |
                  [N70] local build + test evidence
                            |
                  [N80] current-HEAD review readiness
                            |
                  [N90] Copilot review (optional / engaged)
                            |
                  [N95] review-cycle circuit breaker
```

| Node | Stage | Domain | Class | `depends_on` | Produces | Gate question |
|---|---|---|---|---|---|---|
| **N00** | Intake / plan | — | — | — | plan artifact ref | Does a reviewed plan exist for this scope? |
| **N10** | Plan soundness | D-ART | C1 | N00 | plan diagnostics | Width budgets, single responsibility, dependency consistency, resolvable refs, explicit verification surfaces, no title/semantic duplication, no contradiction with the originating decision. |
| **N20** | Work-item conformance | D-ART | C1 | N10 | artifact diagnostics | Section markers present; manifest carries task IDs only; ID shape valid per type; `size` **and** `complexity` present on every task; 2-hour and width-isolation budgets. |
| **N30** | Red-test proof | D-TEST | C2 | N20 | red/green evidence | Does the new regression test **fail** at `base_sha` (or against an equivalent fault injection) and **pass** at `head_sha`, and does it execute the new SUT lines? |
| **N40** | Static / AST | D-CODE | C2 | N20 | AST findings | Fail-open parse guard; containment/injection guard; exit-status contract; portability rules. |
| **N50** | Parity / enumeration | D-PAR | C1, C4 | N30, N40 | parity findings | No unresolved `{{...}}` in installed output; template<->mirror parity modulo variables; variable table set-equality both directions; every linked repo path is actually installed; declared registry pairings agree; every cited backlogit param exists in the registry. |
| **N55** | Lattice / SSOT | D-STATE | C4 | N50 | conformance findings | Every status literal is in the lattice; every named transition is legal; governed tokens appearing on 2+ surfaces are byte-identical or cross-referenced. |
| **N60** | Provenance / docs | D-PROV | C3, C1, C4 | N55 | provenance evidence | Cited paths/anchors/line-ranges resolve; declared reviewed HEAD equals current HEAD; quoted verification command is the authoritative gate; closure/memory records name a HEAD that exists; no dangling definitions or dead config keys. |
| **N70** | Local build/test | — | C2 | N30, N40 | suite evidence | Authoritative suite green at `head_sha`, recorded with tool versions. |
| **N80** | Review readiness | — | C3 | N50, N55, N60, N70 | readiness report | Every applicable terminal node is `passed`, `not_applicable`, or `waived`; provenance is fresh at current HEAD. |
| **N90** | Copilot review | — | C5 | N80 | review threads | Hosted review executed for current HEAD; **mandatory, not optional**, when the diff touches locking, redaction, process control, or destructive classifiers (F14 routing). |
| **N95** | Circuit breaker | — | C3 | N90 | cycle verdict | Epoch count against threshold; `CONVERGING | STALLED | DIVERGING | INSUFFICIENT_DATA`; audited override required to continue. |

### Where remediation returns, and why it does not cycle

Remediation is **not** an edge in the DAG. It is an **epoch transition**.

```text
  epoch e:  evaluate N00..N95  ->  one or more nodes verdict `failed`
                  |
                  v
     remediation applied (class-gated, see below)  ->  commit  ->  new head_sha
                  |
                  v
  epoch e+1: re-evaluate from the *shallowest* failed node onward
                  |
                  v
     N95 counts epochs, not fixes
```

Three properties follow, and they are the whole reason for this shape:

1. **The graph stays acyclic within an epoch**, so cycle detection remains a real
   registry-integrity check rather than a runtime concept.
2. **Re-evaluation is bounded**, because a node result is fresh only at its own
   `head_sha` (D6) — nothing carries over silently.
3. **Termination is not claimed from the graph.** `028-DL` §5 is explicit that
   acyclicity cannot deliver termination over an unbounded node set. Termination
   comes from N95 bounding the **epoch count** with an audited override, which is
   a well-founded decreasing budget — exactly the mechanism `028-DL` says is
   required and a DAG cannot supply. The fix-regenerates-the-family evidence
   (`docs/compound/2026-08-07-copilot-review-fix-introduces-new-filter-bug.md`,
   three consecutive rounds each introducing a subtler bug) is precisely why the
   budget is on epochs and not on findings.

## Fault-Line Coverage Matrix

### Family -> node -> detector -> remediation -> residual human gate

All **15** families (F01, F02, F03a, F03b, F04–F14) are assigned. `PRs` is the
spike's dedup-safe U3 metric. `Det` is the determinism class from §Taxonomy.

| Family | PRs | DAG node | Detector ID | Detection method | Det | Remediation route | Residual human gate | Shipment |
|---|---:|---|---|---|:--:|---|---|---|
| **F12** work-item / backlog conformance | 30 | N20 | `ART-01..04` | Required `BEGIN:`/`END:` markers per `.backlogit/templates/*.md`; manifest contains task IDs only; ID shape per type; `size` **and** `complexity` present | **C1** | `auto_fix_safe` (marker regeneration, sizing write-back via the `gate size` precedent) | Granularity judgment when a split is genuinely ambiguous | **S2** |
| **F10** template / placeholder parity | **71** | N50 | `PAR-01..04` | Unresolved `{{...}}` in installed output; `{{VAR}}` <-> variable-table set equality both directions; template<->mirror parity modulo variables; every template-linked repo path is installed | **C1** | `regenerate` (re-render from `.tmpl`; **never** hand-patch the installed copy) | Deciding whether a divergence is intentional customization | **S3** |
| **F11** evidence staleness vs HEAD | 66 | N60 | `PROV-01..03` | Declared reviewed HEAD == current HEAD; quoted verification command == authoritative CI gate; closure/memory HEAD exists in the object store | **C3** | `guided_fix` (re-derive and rewrite the claim) | Whether a stale claim is an error or a deliberate historical record | **S4** |
| **F05** silent fail-open parsing | 48 | N40 | `CODE-01` | AST: bare `except Exception`; `return {} / None / ()` inside a handler; `setdefault` keyed on an artifact id; container shape validated without members; regex frontmatter parsing in a module that imports `yaml` | **C2** | `guided_fix` | Whether a broad catch is deliberate at a real trust boundary | **S5** |
| **F01** cross-reference integrity | 28 | N60 | `PROV-04` | Resolution of cited paths, anchors, and `file:line-range` **inside prose and template comments**, over the **diff**, excluding plain markdown links (§R6) | **C1** | `guided_fix` | Intentional forward references to not-yet-created files | **S4** |
| **F02** enumeration / registry drift | 27 | N50 | `PAR-05` | Set equality over a small **declared** registry of must-agree pairings (capability-pack registry <-> manifest <-> preflight <-> docs table; role classifier; template-group map; variable table) | **C1** | `guided_fix` | Authoring the pairing declarations themselves | **S3** |
| **F09** traversal / injection / secret leak | 35 | N40 | `CODE-02` | AST: non-literal interpolation into `Path.glob` / `subprocess` / `re.compile`; exception text or class interpolated into a redaction return; missing `resolve()` + `relative_to(root)` on path-bearing external fields | **C2** | `guided_fix` (**never** auto-fix — a wrong containment fix is worse than none) | Trust-boundary judgment; **mandatory Security persona** | **S5** |
| **F08** platform / shell portability | 55 | N40 | `CODE-03` | **Extend existing `PORTABILITY_RULES` + allow-list**: hard-coded ID prefix/suffix literals in `.tmpl`; `git ls-files` not root-anchored; cwd-derived repo root; documented OS-matrix variables absent from the template they govern | **C2** | `guided_fix` | Deliberate platform-specific branches | **S5** |
| **F07** status / outcome conflation | 30 | N40 | `CODE-04` | Shell declaring an exit-code contract while relying on `set -e` without `if`-wrapping; PowerShell native invocation with no `$LASTEXITCODE` check; telemetry outcome mapping not switching over the full exit-code domain | **C2** | `guided_fix` | Whether a substring check is an acceptable proxy | **S5** |
| **F06** vacuous / missing test | 26 | N30 | `TEST-01..03` | Run each new/changed test under coverage and assert the new SUT lines execute; flag unused fixtures/readers; flag tautological assertions | **C2** | `require_plan_revision` (a vacuous test means the acceptance surface was wrong) | Whether the assertion is *meaningful*, not merely reached | **S6** |
| **F04** schema / API / capability drift | 28 | N50 | `PAR-06` | **Named subset only**: every backlogit MCP/CLI param cited in `templates/**`, `.github/agents/**`, `.github/skills/**` exists in `.autoharness/backlog-registry.yaml` `params`; doc-referenced schema keys exist where `additionalProperties: false` | **C4** | `guided_fix` | **Semantic strictness drift stays human** (schema says any non-whitespace string; normalizer forces a UUID) | **S3** |
| **F03b** claim-vs-reality / unwired derivation | 61 | N60 | `PROV-05..06` | **Named subset only**: dangling-definition check (a variable/list/step introduced in an agent contract is referenced by >= 1 later step); dead-config check (a documented key is read by >= 1 code path) | **C4** | `guided_fix` | **"Is this guarantee achievable?" stays human** (the PR #296 impossible-observability class) | **S4** |
| **F13** lifecycle ordering / precondition | 87 | N55 | `STATE-01..02` | **Named subset only**: model the shipment/task status lattice once; assert every status literal used in an agent contract is in it and every named transition is legal; plus the crash-boundary/non-idempotent-resume invariant subset lifted from `926FEA6D` | **C4** | `guided_fix` / `require_plan_revision` | **Ordering hazards, TOCTOU windows, and fail-closed filter placement stay human** | **S7** |
| **F03a** normative-surface contradiction | **135** | N55 | `STATE-03` | **Named subset only**: when a governed token (policy ID, status enum, variable name, numeric constant) appears on 2+ governed surfaces, require byte-identical claim text or an explicit cross-reference | **C4** | `guided_fix` | **Genuine contradiction between differently-worded normative surfaces is NOT mechanizable at acceptable precision** — persona + hosted review | **S7** detector; **S10** routing |
| **F14** resource / concurrency | 18 | N90 | *(none — by design)* | No detector. **Routing obligation**: Concurrency Reviewer persona mandatory and hosted review non-optional for diffs touching locking, redaction, process control, or destructive classifiers | **C5** | `require_human_review` | **Entire family** — 76% high-round, the most expensive per finding | **S10** (policy only) |

**No family is unassigned.** Three (F14 entirely; F03a and F13 in their general
cases) are assigned to a *routing obligation* rather than a detector, which is a
deliberate, evidence-backed assignment — not a coverage gap. The spike's
single-source exclusions are also honoured: **local-only governance findings**
(role boundaries, P-021 containment, authority questions) remain the exclusive
province of local adversarial review, because Copilot has no model of the
harness's role separation.

### Honest coverage arithmetic

Weighting each family by its PR recurrence, detectors of class C1–C2 (blocking
reachable) address families totalling **~334 PR-incidences**; C4 subsets add
partial coverage over **~311** more but explicitly do **not** claim their
families; C5 covers **0** by detection and is handled by routing. **The largest
single family (F03a, 135 PRs) remains predominantly uncovered by design.** Any
claim that this portfolio eliminates the review loop would be false; the
supportable claim is that it reduces the node-generation rate `028-DL` §2
identifies as the reason the loop does not terminate.

## Shipment Portfolio

Eleven conceptual shipments. **Labels `S0`–`S11` are conceptual only — no
backlogit IDs are allocated by this artifact.** Task clusters are indicative
decomposition targets, each written to sit inside the 2-hour rule with width
isolation (no shipment mixes template work with CLI work with schema work inside
one task). All rollout modes are report-only unless stated.

### S0 — Prerequisite closure (EXTERNAL, not owned here)

* **Objective**: install the policy registry and review-persona layer so policy
  IDs cited by S2, S7, and S10 resolve.
* **Owner**: existing stash **`336F3AB7`** (critical bug). **Not re-owned, not
  duplicated** — requirement 10's exactly-once rule.
* **Blocks**: S2 (plan-soundness diagnostics cite policy IDs), S10 (persona
  routing and override authority).
* **Waivable**: yes, by explicit operator decision to let S2 emit
  policy-ID-free diagnostics; recorded as Open Decision Q7.

### S1 — Detector SDK, evidence-node contract, and `gate pre-review` reader

* **Slug**: `pre-review-detector-sdk`
* **Objective**: land the node contract (D1–D10), the registry, the applicability
  engine, the derived-DAG assembler with cycle detection, the report emitter, and
  **one real detector end-to-end** proving the contract.
* **Imported stash**: `89E833E1` (a); `D911A3B2` (program frame)
* **Families covered**: F12 (narrowest slice only, as the reference detector)
* **Deliverables**: `src/autoharness/detectors/` package; `NodeSpec` /
  `Evidence` / `NodeResult` dataclasses reusing `CheckResult` semantics;
  registry + schema extension to `schemas/validation-gates.schema.json`;
  `autoharness gate pre-review [--json] [--base <ref>]`; reference detector
  `ART-01` (backlogit section-marker conformance); report writer under
  `.autoharness/gates/pre-review/`; unit tests.
* **Candidate task clusters**: (1) node/evidence dataclasses + verdict mapping;
  (2) registry loader + schema extension; (3) applicability engine over
  `discover_modified_files`; (4) DAG assembler + cycle detection reusing
  `topology.py`; (5) `ART-01` reference detector; (6) CLI wiring + `--json`;
  (7) report emitter + freshness rule; (8) tests.
* **Prerequisites**: none
* **Priority**: **critical** — **Risk**: medium (new abstraction)
* **Acceptance evidence**: `gate pre-review` runs on a real diff, emits a valid
  report, `ART-01` re-detects at least one of PR #234 / #185 / #183 / #189 /
  #202 / #123 / #213; registry cycle injection exits 2.
* **Rollout**: report-only, exit 0 except registry-invalid.
* **Non-goals**: no repository-specific adapter extension points; no second
  detector; no blocking; no visualization; no persisted graph.

### S2 — D-ART: work-item conformance and plan soundness

* **Slug**: `pre-review-artifact-and-plan-soundness`
* **Objective**: complete the D-ART domain — the closed-surface, declared-shape
  detectors over `.backlogit/**` and plan artifacts.
* **Imported stash**: `C327A8DE` (retain+merge)
* **Families covered**: F12 (full)
* **Deliverables**: `ART-02` manifest task-IDs-only + ID shape; `ART-03`
  `size`+`complexity` presence; `ART-04` width/granularity budget (configurable);
  `PLAN-01` single-responsibility + dependency consistency + resolvable refs;
  `PLAN-02` title/semantic duplication; `PLAN-03` contradiction against the
  originating decision and sibling items.
* **Candidate task clusters**: (1) `.backlogit/templates/*.md` shape reader;
  (2) `ART-02`+`ART-03`; (3) `ART-04` budget config; (4) plan artifact reader;
  (5) `PLAN-01`; (6) `PLAN-02`; (7) `PLAN-03`; (8) retro-validation harness.
* **Prerequisites**: **S1**; **S0** (for policy-ID citations)
* **Priority**: **critical** — **Risk**: low
* **Acceptance evidence**: re-detects the covering-feature-in-task-manifest class
  (PR #237, #262) and the granularity class (PR #224); **day-one blast radius
  against the 612 existing tasks is exactly zero** because it validates only
  newly harvested output (Authority Test v2 migration story).
* **Rollout**: report-only. **Best promotion candidate in the portfolio**
  precisely because of the zero-history blast radius.
* **Non-goals**: no backlogit schema change; no auto-splitting of oversized
  tasks; no shipment-level evaluation.

### S3 — D-PAR: template parity, enumeration agreement, registry-param check

* **Slug**: `pre-review-parity-and-enumeration`
* **Objective**: close the largest uncovered mechanical family (F10, 71 PRs) and
  the two set-equality families beside it.
* **Imported stash**: none directly — **added scope** (§R5)
* **Families covered**: F10, F02, F04 (named subset)
* **Deliverables**: `PAR-01` unresolved `{{...}}` in installed output; `PAR-02`
  variable-table set equality both directions; `PAR-03` template<->mirror parity
  modulo variables (**fixes the `upstream_updated` checksum semantics PR #53
  proved wrong** rather than building new); `PAR-04` template-linked repo path is
  actually installed; `PAR-05` declared must-agree registry pairings; `PAR-06`
  backlogit param existence against `.autoharness/backlog-registry.yaml`.
* **Candidate task clusters**: (1) variable extraction from `templates/**`;
  (2) `PAR-01`+`PAR-02`; (3) `upstream_updated` checksum-semantics fix;
  (4) `PAR-03` on the corrected semantics; (5) `PAR-04`; (6) pairing declaration
  file + schema; (7) `PAR-05`; (8) `PAR-06`; (9) retro-validation.
* **Prerequisites**: **S1**
* **Priority**: **high** — **Risk**: medium (mirror-parity false positives on
  intentional customization)
* **Acceptance evidence**: re-detects PR #3, #292, #379 (F10), PR #196/#183/#3
  (F02), and **PR #292 exactly** for `PAR-06`.
* **Rollout**: report-only.
* **Non-goals**: no template authoring changes; no installer changes; no semantic
  schema-strictness analysis (stays human per F04 C5 half).

### S4 — D-PROV: provenance freshness and documentation validity

* **Slug**: `pre-review-provenance-and-docs`
* **Objective**: mechanize the provenance claims that today are asserted rather
  than verified.
* **Imported stash**: `3F80F8A3` (split (a) PROV + (b) DOC)
* **Families covered**: F11, F01 (reduced surface), F03b (named subset)
* **Deliverables**: `PROV-01` declared reviewed HEAD == current HEAD; `PROV-02`
  quoted verification command == authoritative gate
  (`PYTHONPATH=src python -m unittest discover -s tests`); `PROV-03`
  closure/memory HEAD exists; `PROV-04` prose/comment citation resolution over
  the diff (§R6 reduced surface); `PROV-05` dangling-definition; `PROV-06`
  dead-config-key.
* **Candidate task clusters**: (1) authoritative-record readers (git + `gh`
  read-only + backlogit query); (2) `PROV-01`; (3) `PROV-02`; (4) `PROV-03`;
  (5) citation extractor for prose/comments; (6) `PROV-04`; (7) `PROV-05`;
  (8) `PROV-06`; (9) retro-validation **including the §R6 yield gate**.
* **Prerequisites**: **S1**; **`PROV-04` additionally gated on the §R6
  yield gate passing**
* **Priority**: **high** — **Risk**: **high** for `PROV-04` (029-DL measured 0%
  on the adjacent surface); low for `PROV-01..03`
* **Acceptance evidence**: re-detects PR #212, #230, #376 (F11); `PROV-04` must
  re-detect PR #115 and #258 **or be dropped**.
* **Rollout**: report-only. C3 detectors are **fail-closed on API
  unavailability** (`insufficient_evidence`, never `passed`).
* **Non-goals**: no achievability judgment (the PR #296 class stays human); no
  PR body mutation; no GraphQL review-body sweep.

### S5 — D-CODE: analyzer-pack framework and code-safety AST guards

* **Slug**: `pre-review-code-safety-analyzers`
* **Objective**: land the analyzer-pack mechanism and the four highest-cost AST
  families on it.
* **Imported stash**: `A02280C8` **(a) only** — analyzer discovery/registration/
  evidence output
* **Families covered**: F05, F09, F07, F08
* **Deliverables**: analyzer-pack discovery + registration + evidence contract
  (language-scoped, no Go/Python rules hard-coded into the core); `CODE-01`
  fail-open parse guard; `CODE-02` containment/injection guard; `CODE-03`
  **extension of the existing `PORTABILITY_RULES` + allow-list**; `CODE-04`
  exit-status contract guard.
* **Candidate task clusters**: (1) analyzer-pack registry + discovery;
  (2) Python AST walking harness (reusing the `docs/compound/2026-08-21-ast-*`
  technique precedents incl. LEGB scope-aware alias resolution);
  (3) `CODE-01`; (4) `CODE-02`; (5) shell/PowerShell parser adapter;
  (6) `CODE-04`; (7) `CODE-03` rule extension; (8) allow-list migration;
  (9) retro-validation.
* **Prerequisites**: **S1**
* **Priority**: **high** — **Risk**: medium-high (AST false positives)
* **Acceptance evidence**: re-detects PR #297, #387, #122 (F05); PR #326, #53,
  #31 (F09). **F05 and F09 carry the highest high-round shares (68%, 67%) and are
  therefore the highest expected review-cycle savings in the portfolio.**
* **Rollout**: report-only. **`CODE-02` is permanently `guided_fix`** — never
  `auto_fix_safe`, because an incorrect containment fix is more dangerous than
  the finding.
* **Non-goals**: no compatibility corpus, no fuzz/property matrices, no
  legacy-version or multi-platform execution matrix (all deferred to S11).

### S6 — D-TEST: red-test honesty and vacuous-test detection

* **Slug**: `pre-review-test-honesty`
* **Objective**: prove that a regression test actually regresses.
* **Imported stash**: `7A3F570B` (retain+merge with spike Tier 2 #8)
* **Families covered**: F06
* **Deliverables**: base-revision (or fault-injected) execution contract;
  `TEST-01` fails-at-base assertion; `TEST-02` coverage assertion that the new
  SUT lines execute; `TEST-03` unused-fixture and tautological-assertion flags;
  red/green evidence persisted **as node evidence only**, per D9.
* **Candidate task clusters**: (1) base-revision execution harness (worktree-free,
  read-only checkout of the base tree); (2) fault-injection fallback contract;
  (3) `TEST-01`; (4) coverage instrumentation wiring; (5) `TEST-02`;
  (6) `TEST-03`; (7) evidence emission; (8) retro-validation.
* **Prerequisites**: **S1**, **S5** (analyzer-pack + AST harness reuse for
  `TEST-03`)
* **Priority**: **medium** — **Risk**: **high**: the workspace profile declares
  no coverage tool (`lint.tool` and `format.tool` are empty; `test.runner` is
  `pytest` but the authoritative CI gate is `unittest discover`). A coverage
  dependency and a **single authoritative runner** must be settled first
  (Open Decision Q5).
* **Acceptance evidence**: re-detects PR #398's "never reaches" class.
* **Rollout**: report-only.
* **Non-goals**: no mutation testing; no test generation; no CI pipeline change;
  **no P-014 violation** — base-revision execution must not create a second
  worktree.

### S7 — D-STATE: status-lattice conformance and SSOT governed tokens

* **Slug**: `pre-review-state-semantics`
* **Objective**: mechanize the two named semantic subsets on the two largest
  families.
* **Imported stash**: `926FEA6D` **subset only** (crash-boundary / non-idempotent
  resume invariants)
* **Families covered**: F13 (named subset), F03a (named subset)
* **Deliverables**: one modelled shipment/task status lattice sourced from the
  backlog registry `status_values` plus the workspace profile's declared
  statuses; `STATE-01` status-literal membership; `STATE-02` transition legality
  + resume-idempotence invariants; `STATE-03` governed-token SSOT check.
* **Candidate task clusters**: (1) lattice model + single source of truth;
  (2) agent-contract status-literal extractor; (3) `STATE-01`;
  (4) transition extractor; (5) `STATE-02`; (6) governed-token registry;
  (7) `STATE-03`; (8) retro-validation.
* **Prerequisites**: **S1**, **S2** (artifact reader)
* **Priority**: **medium** — **Risk**: **high**. `STATE-03` is the mechanical
  edge of a 135-PR family that the spike could not reduce to a predicate without
  discarding most members. It must be held to a strict precision floor or
  dropped.
* **Acceptance evidence**: re-detects PR #386's deadlock class (`STATE-01`).
* **Rollout**: report-only, **and `STATE-03` carries a report-only ceiling** — it
  may not be proposed for promotion in the first promotion round regardless of
  measured precision.
* **Non-goals**: no general contradiction detection; no ordering-hazard or TOCTOU
  analysis; no mutation-postcondition framework (deferred to S11).

### S8 — Shipment evidence-DAG assembly and review-readiness integration

* **Slug**: `pre-review-shipment-evidence-dag`
* **Objective**: compose the detector domains into a per-shipment DAG family and
  wire the readiness report into the consumers that need it.
* **Imported stash**: `89E833E1` **(b)**
* **Families covered**: none new — this is the composition layer
* **Deliverables**: versioned DAG family definitions attached to a shipment;
  incremental evaluation keyed on epoch freshness; applicability resolution from
  the shipment manifest; `N80` review-readiness node; **the named consumers**
  that make D9's report legitimate — the PR-body readiness block and the closure
  record `conditions:` block.
* **Candidate task clusters**: (1) DAG family definition + versioning;
  (2) shipment-manifest applicability resolution; (3) incremental evaluation +
  freshness; (4) `N80` readiness aggregation; (5) PR-body readiness consumer;
  (6) closure `conditions:` consumer; (7) audited non-applicability records
  (FC2); (8) tests.
* **Prerequisites**: **S2, S3, S4** (three domains minimum, so composition is
  exercised across differing determinism classes); S5/S6/S7 attach incrementally
* **Priority**: **critical** (spine) — **Risk**: medium
* **Acceptance evidence**: a real shipment produces a complete readiness report
  whose consumers render it; **at least one previously-unverified readiness claim
  is caught** (the F11 mechanism turned on the harness itself).
* **Rollout**: report-only. **Still exits 0 even when terminal nodes fail.**
* **Non-goals**: **no blocking**, no waiver enforcement, no query/visualization
  surface (pruned — no reader), no backlogit schema change.

### S9 — Review-convergence analyzer (`028-DL` Phase 1 MVE)

* **Slug**: `review-convergence-analyzer`
* **Objective**: derive HEAD-keyed rounds and the `new_findings_per_round` series
  so a cycle count exists as a machine-derived fact.
* **Imported stash**: `34AAF1C7` branch (a)
* **Families covered**: none — supplies the input N95 requires
* **Deliverables**: `autoharness gate review-convergence <pr> --repo <owner/name>
  [--json]`, reusing the GraphQL surface `copilot_review.py` already queries;
  per-round new/carried/resolved classification; verdict
  `CONVERGING | STALLED | DIVERGING | INSUFFICIENT_DATA`; **the `028-DL` §9.3
  falsification run**.
* **Candidate task clusters**: (1) GraphQL round derivation; (2) thread
  classification + R1 secondary identity fallback `(path, normalized message
  hash)`; (3) R2 reviewable-path epoch labelling; (4) measure over a 3-round
  window (R4); (5) verdict emission; (6) falsification run against PR #229,
  #325, #328, #348 + two healthy PRs.
* **Prerequisites**: none (`028-DL` §9.2 — needs no instrumentation, and needs
  **zero backlogit change**). **Plannable fully in parallel with S1.**
* **Priority**: **medium** — **Risk**: medium (R1 thread-ID instability, R3
  suppressed findings)
* **Acceptance evidence**: **the `028-DL` §9.3 gate is binding** — it MUST
  classify the pathological PRs `DIVERGING`/`STALLED` and the healthy ones
  `CONVERGING`. **If it cannot separate the populations, S9 fails, S10 loses its
  input, and `8CB5A9B9` must be re-deliberated rather than staged.**
* **Rollout**: report-only, always exit 0.
* **Non-goals**: no persistence, no blocking, no `regression_of` link type, no
  backlogit change (`028-DL` Phase 2 and Q3 remain unauthorized).

### S10 — Policy promotion: blocking thresholds, audited overrides, circuit breaker, and review routing

* **Slug**: `pre-review-policy-promotion`
* **Objective**: convert measured, retro-validated detectors into enforcement —
  as a **single, explicit, authority-expanding decision**, separated from every
  foundation shipment above.
* **Imported stash**: `89E833E1` **(c)**; `8CB5A9B9`
* **Families covered**: F14 and F03a-general by **routing obligation**; all
  others by mode change only
* **Deliverables**: per-detector `mode` promotion mechanism with recorded
  criteria; the D10 waiver record + audit surface reusing `.autoharness/gates/`;
  N95 circuit-breaker state transition consuming S9's cycle count; **mandatory
  Concurrency Reviewer persona and non-optional hosted review for diffs touching
  locking, redaction, process control, or destructive classifiers**; cycle counts
  surfaced in the readiness report and closure records.
* **Candidate task clusters**: (1) promotion criteria evaluator + record;
  (2) per-detector mode switch + exit-code mapping; (3) waiver schema + audit
  writer; (4) waiver scope/expiry validation; (5) N95 breaker transition;
  (6) override authority binding; (7) persona routing policy; (8) closure-record
  surfacing.
* **Prerequisites**: **S8** *and* **S9**, *and* the §Rollout promotion criteria
  met per detector, *and* **explicit operator consent**; **S0** for persona and
  policy-ID resolution
* **Priority**: **high**, but **not eligible** until its prerequisites clear
* **Risk**: **highest in the portfolio** — this is the only authority-expanding
  shipment.
* **Acceptance evidence**: each promoted detector has a recorded precision
  measurement above its floor; the breaker fires on a reconstructed `128-S` /
  PR #348 scenario; **no override can be self-issued by an agent**.
* **Rollout**: promotion is per detector and reversible.
* **Non-goals**: **no weakening of P-009, P-014, P-018, P-020, or destructive-
  action approval** — a pre-review waiver carries no authority over any of them
  (D10); no automatic promotion; no repo-wide waivers; no unbounded overrides.

### S11 — Deferred frameworks (staged for visibility, not for execution)

* **Slug**: `cross-surface-and-compatibility-frameworks`
* **Objective**: hold the deferred imported scope explicitly so it is not lost.
* **Imported stash**: `39AA674D` (full), `926FEA6D` (remainder), `A02280C8` **(b)**
* **Deliverables**: none this cycle.
* **Prerequisites**: **a named in-repo consumer must exist** — autoharness must
  grow a second runtime surface, or this scope re-homes to backlogit where the
  pilot and adapters already live.
* **Priority**: **low** (down from critical/high on import) — **Risk**: n/a
* **Rollout**: not staged. Revisit when the consumer condition is met.
* **Non-goals**: everything, this cycle.

## Coverage Matrix (Imported Scope x Families x Nodes x Shipments)

Requirement 10: every unit of scope is **owned exactly once** at its
implementation layer, while evidence may have many consumers.

| Imported stash | Disposition | Families it owns | DAG nodes | Owning shipment | Consumers of its evidence |
|---|---|---|---|---|---|
| `D911A3B2` (epic) | retain, narrowed | — (program frame) | all | **S1–S10** | — |
| `89E833E1` (a) | split | — (contract) | node contract | **S1** | every detector |
| `C327A8DE` + F12 | retain + merge | F12 | N10, N20 | **S2** | S8 readiness, S10 promotion |
| *added scope* | new | F10, F02, F04-subset | N50 | **S3** | S8 readiness |
| `3F80F8A3` (a)+(b) | split | F11, F01, F03b-subset | N60 | **S4** | S8 readiness, PR body, closure `conditions:` |
| `A02280C8` (a) | split | F05, F09, F07, F08 | N40 | **S5** | S6 (`TEST-03` AST reuse), S8 readiness |
| `7A3F570B` + F06 | retain + merge | F06 | N30 | **S6** | N70 build/test evidence, S8 readiness |
| `926FEA6D` (subset) | split | F13-subset, F03a-subset | N55 | **S7** | S8 readiness |
| `89E833E1` (b) | split | — (composition) | N80 | **S8** | PR body, closure record, S10 |
| `34AAF1C7` (a) | retain (tracker) | — (measure) | N95 input | **S9** | S10 breaker |
| `89E833E1` (c) + `8CB5A9B9` | split + retain | F14, F03a-general (routing) | N90, N95 | **S10** | closure records, operator |
| `39AA674D`, `926FEA6D` (rest), `A02280C8` (b) | defer | — | — | **S11** | none this cycle |

**Exactly-once verification.** No family appears as *owned* in two shipments.
Three families are split by named subset (F04, F03b, F13/F03a) and in every case
the mechanical subset is owned by exactly one shipment while the semantic
remainder is owned by S10's routing policy — a different layer, not a duplicate
owner. `926FEA6D` and `A02280C8` appear twice only because they were **split**,
and the two halves are disjoint. F01's owner is S4 alone, subject to the §R6
yield gate.

**Multiple-consumer cases (intended, not duplication).** S5's AST harness is
consumed by S6. S4's provenance evidence is consumed by S8, the PR body, and
closure records. S9's cycle count is consumed by S10. S2's artifact reader is
consumed by S7. Each is a *read* of evidence produced once (D3), never a second
producer.

## Shipment Dependency and Order

### Adjacency table

| Shipment | `depends_on` | Priority | Risk | Mode |
|---|---|---|---|---|
| **S0** (external, `336F3AB7`) | — | critical | low | n/a |
| **S1** | — | critical | medium | report-only |
| **S2** | S1, S0 | critical | low | report-only |
| **S3** | S1 | high | medium | report-only |
| **S4** | S1 | high | high (`PROV-04`) | report-only |
| **S5** | S1 | high | medium-high | report-only |
| **S6** | S1, S5 | medium | high (tooling) | report-only |
| **S7** | S1, S2 | medium | high (`STATE-03`) | report-only |
| **S8** | S2, S3, S4 | critical | medium | report-only |
| **S9** | — | medium | medium | report-only |
| **S10** | S8, S9, S0 + promotion criteria + operator consent | high | **highest** | **blocking** |
| **S11** | S5 (for the analyzer half), + a named in-repo consumer | low | n/a | not staged |

### Topological staging order

```text
tier 0:  S0*  S1  S9          (* external; S9 independent)
tier 1:  S2   S3  S4  S5
tier 2:  S6   S7
tier 3:  S8
tier 4:  S10
tier 5:  S11  (conditional on a named consumer; may never execute)
```

A valid serial execution order — the recommended one, sequenced by build cost
rather than recurrence per the spike's Next Step 2:

```text
S0 -> S1 -> S2 -> S3 -> S5 -> S4 -> S9 -> S8 -> S6 -> S7 -> S10 -> (S11)
```

`S5` is placed ahead of `S4` despite equal priority because F05/F09 carry the
highest high-round shares (68% / 67%) and therefore the largest expected
review-cycle saving, and because `S4`'s `PROV-04` is gated on an unresolved yield
question (§R6). `S9` is placed before `S8` only because `S10` needs both; it may
legitimately move anywhere in tiers 0–3.

### Critical path

```text
S1 -> S2 -> S8 -> S10        (4 shipments)
```

with **S9 -> S10** as a co-critical branch of length 2 that cannot be compressed,
because S10 cannot start until both branches land. **S0 is critical-path-adjacent**:
it does not lengthen the path but S2 and S10 both stall without it, so it should
be cleared first even though it is externally owned.

Longest chain by node count including the external prerequisite:
`S0 -> S2 -> S8 -> S10` (4) and `S1 -> S2 -> S8 -> S10` (4). The measure is
node count in the `blocks` DAG, matching `dag-readiness`'s documented
`critical_path` semantics.

### What may be planned in parallel

**Planning parallelism is permitted; execution parallelism is not.** P-001
(single-active) and P-016 (one worktree; the Stage spike/research exception is
time-boxed and explicitly not for implementation) are unchanged by this artifact.

* **Freely parallel to plan**: `S1` and `S9` (no shared prerequisite, disjoint
  surfaces — detector SDK vs. GraphQL analyzer).
* **Parallel to plan once S1 is planned**: `S2`, `S3`, `S4`, `S5` — they share
  the node contract but touch disjoint detector packages and disjoint retro-
  validation corpora.
* **Must be planned after their prerequisite is planned**: `S6` (needs S5's AST
  harness shape), `S7` (needs S2's artifact reader shape), `S8` (needs three
  domains' evidence shapes), `S10` (needs S8 + S9 measured outputs).
* **Execution remains strictly serial** through backlogit's existing `blocks`
  edges and `compute_next_eligible`'s deterministic total order. **No second
  active shipment. No second worktree. No new scheduler** — requirement 13 and
  the standing `dag-readiness` non-goal.

### Why priority cannot override dependency eligibility

`S8` and `S2` are both **critical** priority; `S9` is **medium**. Yet `S8` cannot
start before `S2`, `S3`, and `S4`, while `S9` can start immediately. If priority
selected work, a critical-priority `S8` would be chosen first and would produce a
composition layer over detectors that do not exist — a readiness report that
aggregates nothing, which is the write-only artifact failure this whole program
exists to prevent.

The correct model is the one already implemented in `topology.py`:

1. **Eligibility filter first.** `ready_set` contains only items whose every
   blocking predecessor is complete. `S8` is simply not in the ready set until
   tier 1 lands. This is a hard constraint, not a preference.
2. **Deterministic total order second.** Among the ready set, `compute_next_eligible`
   tie-breaks on `(-fan_out, id)`. Priority is a *tie-break input within the
   eligible set*, never a filter over it.
3. **A ready set of size > 1 is a choice, not a decision** (`029-DL` A3). The
   tie-break is what makes the next action unique, and that uniqueness — not
   priority — is where determinism comes from.

Priority answers "which of the things I *may* do matters most." Dependency
answers "which things I *may* do at all." Letting the first override the second
is how a portfolio ships its integration layer before its integrands.

### Recommended first shipment to stage next

**`S1` — Detector SDK, evidence-node contract, and `gate pre-review` reader.**

Rationale:

* It is the only tier-0 shipment inside this portfolio's ownership (`S0` is
  externally owned by `336F3AB7`; `S9` is independent and can be staged
  alongside it).
* It has **zero prerequisites** and unblocks four tier-1 shipments at once — the
  highest fan-out in the graph, which is exactly what the `(-fan_out, id)`
  tie-break selects for.
* It is **report-only, exit 0, zero new authority, zero blast radius against
  history**, so it needs no operator consent under Authority Test v2.
* Its `F5` write-only risk is structurally mitigated by the requirement that it
  ship `ART-01` end-to-end. **If S1 cannot ship one working detector, the SDK is
  not justified and Option A should be reconsidered** — a cheap, early,
  falsifiable decision point.

**Recommended to stage in the same planning pass (not the same execution
window): `S9`**, because it is independent, needs no backlogit change, and its
`028-DL` §9.3 falsification gate is the cheapest way to learn whether `8CB5A9B9`
is buildable at all.

**Explicitly not recommended first**: `S3`, despite owning the largest mechanical
family (F10, 71 PRs). Recurrence is not build cost, and the spike's own Next Step
2 says to sequence by build cost.

## Mechanical Remediation Classes

Six classes. **Only two may mutate anything automatically, and both are confined
to machine-produced artifacts.**

| Class | Definition | May auto-mutate? | Authority | Examples | Guard |
|---|---|:--:|---|---|---|
| **`auto_fix_safe`** | Deterministic, total, idempotent rewrite of a **machine-produced** artifact where the correct output is uniquely determined. | **YES** | `ship` | Regenerate missing `BEGIN:`/`END:` section markers; write back `size`/`complexity` (the `gate size` precedent — advisory, fail-open, and at 100% adoption because the machine writes it). | Never touches source code, tests, or schemas. Never touches an artifact a human authored by hand. Emits a diff in the report. |
| **`regenerate`** | Re-render an installed artifact from its authoritative template. | **YES** | `ship` | Template<->mirror parity divergence -> re-render from `templates/**`. | **Template-first, never hand-patch the installed copy** (the standing rule recorded in stash `74C62374`). If the divergence is in the template, this class does not apply — it becomes `guided_fix`. |
| **`guided_fix`** | The defect is localized and a fix hint is derivable, but the correct fix is not uniquely determined. | **NO** — advisory only | `ship` applies manually | All D-CODE findings; F11 stale claims; F01 citation failures; F02 enumeration gaps; F03b dangling definitions. | **`CODE-02` containment/injection is permanently pinned here** — a wrong containment fix is more dangerous than the finding. |
| **`require_plan_revision`** | The finding indicates the *plan or acceptance surface* is wrong, not the implementation. | **NO** | **Stage** (Ship must not self-authorize) | Vacuous test (F06) — the acceptance criterion was vacuously satisfiable; plan-soundness failures (N10). | Routes back to `impl-plan` / `plan-review`. **Ship may not "fix" a plan defect in code.** |
| **`require_human_review`** | No mechanical predicate; value is in routing. | **NO** | operator / persona | F14 concurrency; F03a general contradiction; F04 semantic strictness; F13 ordering/TOCTOU; all governance and role-authority findings. | Becomes a **mandatory routing obligation** in S10, not a detector. |
| **`policy_halt`** | The finding is a policy violation, not a defect. | **NO** | operator | P-005/P-010 violations; tripped circuit breaker; attempted self-issued waiver. | Halt and report. **No retry, no fourth attempt** per the circuit-breaker instruction's MAXIMUM_RETRY_THRESHOLD = 3. |

**Ordering guard (mandatory).** All evaluation completes before any
`auto_fix_safe` or `regenerate` mutation runs, and any mutation advances the
epoch and forces re-evaluation. Mutating mid-walk would place the gate *after*
the mutation it guards — family F13's exact defect class, which the harness must
not commit inside the mechanism built to detect it.

**Mode guard.** Auto-mutation is available **only** in an explicitly invoked
fix mode (`gate pre-review --apply-safe-fixes`). A blocking-mode evaluation never
mutates. Detection and remediation are separate invocations with separate
authority.

## Rollout and Promotion Gates

### Phase 1 — Report-only foundations (S1–S9)

Every detector ships `mode: report_only`, exit 0. No waivers are accepted (D10
rejects a waiver on a report-only node as `invalid`). No agent contract prose
changes, so `029-DL`'s F4 blast-radius objection is dodged for the entire phase.
No new authority is created, so no operator consent is required to build any of
S1–S9.

### Phase 2 — Retro-validation (gate on everything downstream)

Adapted from the spike's Next Step 1 and `029-DL` §8.1, and **binding**:

| Criterion | Threshold | Consequence of failure |
|---|---|---|
| **Re-detection** | Each detector must re-detect **>= 1** of the specific PRs cited in its own evidence anchors. | **Drop the detector.** A checker that cannot find its own motivating finding is ceremony. |
| **Precision floor** | **>= 0.80** true positives on a hand-adjudicated sample of its findings over the replay corpus. | No promotion; stays report-only. |
| **False-positive budget** | **<= 5** findings per 100 changed files; **< 100** total findings per full-corpus run. | No promotion; tighten or drop. |
| **Signal, not triage burden** | If every finding requires operator judgment, the detector adds burden rather than removing choice. | Drop (`029-DL` §8.1 FALSIFIED clause). |
| **Prospective firing** | Must fire **>= 1 time on newly created structure, before it ships**, across **>= 3** Stage harvest cycles. | Demote from gate to occasional hygiene command (`029-DL` §8.1(d) — the half that can actually fail). |

**Replay corpus** (from the spike's dual-source anchors, all internal):
F12 — PR #234, #185, #183, #189, #202, #123, #213, #237, #262, #224.
F10 — PR #3, #292, #379, #53. F11 — PR #212, #230, #376.
F05 — PR #297, #387, #122. F09 — PR #326, #53, #31.
F01 — PR #115, #258. F02 — PR #196, #183, #3. F06 — PR #398.
F13 — PR #386. F04 — PR #292.
Convergence (S9) — PR #229, #325, #328, #348 + **>= 2** healthy 0–1-round PRs.

### Phase 3 — Promotion to blocking (S10 only, per detector)

A detector may be proposed for `mode: blocking` **only** when **all** hold:

1. Phase-2 thresholds met **for that detector**, recorded with the measurement.
2. **Activation blast radius stated and bounded** (Authority Test v2). Detectors
   validating Stage's own harvest output are intrinsically enforce-on-new-only
   with day-one blast radius **zero**; any detector with non-zero historical
   blast radius must ship a warn-then-block sequence.
3. **New-item adoption sustained >= 90% across >= 2 shipment bands** in warn mode
   (`029-DL` §B2 step 3).
4. **Explicit operator consent**, recorded. Blocking is authority-expanding
   (`028-DL` Q1). **No agent may promote a detector.**
5. Reversibility: mode is a config value; demotion requires no code change.

**Detectors with a report-only ceiling in the first promotion round regardless of
measurement**: `STATE-03` (F03a subset — mechanical edge of a family the spike
could not reduce), `PROV-04` (F01 — unresolved §R6 yield conflict), and every
C4-class detector until its named subset is separately validated.

**Convergence-verdict blocking (`028-DL` Q1/Q2) remains a distinct, later
decision** and is not authorized by this artifact. `028-DL` Q2 is unresolved:
genuine deep review of novel safety-critical code may legitimately diverge, and
the classifier has no novelty/criticality input.

### Success metrics

| Metric | Baseline (measured) | Target | Measurement |
|---|---|---|---|
| Median Copilot review rounds on PRs touching covered path classes | 598 rounds / 303 PRs = **1.97 mean**; 53 PRs >= 3, 24 >= 5, max 20 | **>= 20% reduction** in mean rounds for covered path classes | S9 analyzer, 3 shipment bands post-S8 |
| PRs requiring >= 3 rounds | **53 / 303 (17.5%)** | **<= 12%** | S9 analyzer |
| Detector precision | unmeasured | **>= 0.80** per detector | Phase-2 hand adjudication |
| False positives | unmeasured | **<= 5 / 100 changed files** | Phase-2 full-corpus run |
| Findings caught pre-review that historically reached review | 0 | **>= 1 per shipment band per promoted domain** | pre-review report vs. Copilot findings on the same PR |
| Report-only detectors that never fire in 3 harvest cycles | n/a | **0** (any such detector is demoted) | `029-DL` §8.1(d) |

**Honest caveat carried forward from the spike, restated here so it is not lost
in the shipment framing:** counts are lexically derived lower bounds with 47% of
the Copilot corpus unclassified; recurrence *ordering* is trustworthy, absolute
counts are not. The 20% round-reduction target is therefore a **directional
target measured against the S9 analyzer's own consistent series**, not a claim
derived from the classifier counts.

## Open Decisions

Decisions requiring **operator authority**. None was taken this session; each is
recorded so it cannot be resolved by silent default.

| ID | Decision | Why it needs authority | Blocks |
|---|---|---|---|
| **Q1** | **May the D9 report be written at all?** It is the one persistence exception to Law 1. | Law 1 is an architectural law from `029-DL`; exceptions must be granted, not assumed. **If S8 does not wire a named consumer, the report must not be written.** | S1 (writer), S8 (consumers) |
| **Q2** | **Does autoharness own `39AA674D` / `926FEA6D` at all,** given both declare backlogit as pilot and every adapter is cross-repo? | Cross-repo ownership is an authority question, and building an unread framework violates Law 2. Alternatives: re-home to backlogit; or hold in S11 until autoharness grows a second surface. | S11 |
| **Q3** | **Is the §R6 F01 conflict resolved by the reduced surface?** The spike ranks F01 Tier 1 (28 PRs); `029-DL` measured 0% on the adjacent surface. | Two internally-measured results disagree. Building on the unreconciled version risks ceremony. | `PROV-04` in S4 |
| **Q4** | **May a convergence verdict ever block a merge?** (`028-DL` Q1, unchanged.) And is `DIVERGING` always pathological? (`028-DL` Q2 — deep review of novel safety-critical code may legitimately diverge.) | Governing when agents stop reasoning is authority-expanding; reserved across four prior triages. | S10 breaker |
| **Q5** | **What is the single authoritative test runner?** The profile declares `pytest`; the authoritative CI gate quoted in F11 evidence is `PYTHONPATH=src python -m unittest discover -s tests`. A coverage dependency must also be adopted (`lint.tool`/`format.tool` are empty). | `PROV-02` asserts against "the authoritative gate" and S6 needs coverage instrumentation. **This ambiguity is itself an instance of family F03a** and must be resolved before either is built. | S4 (`PROV-02`), S6 |
| **Q6** | **Should stash `34AAF1C7` be split** into (a) PR-review convergence and (b) reasoning-state identity? (`028-DL` Q4, still unexecuted.) | Splitting a living tracker is an operator-visible reclassification. This artifact consumes only branch (a). | housekeeping only |
| **Q7** | **Is `S0` (`336F3AB7`) cleared or waived** before S2? Without it, plan-soundness diagnostics cannot cite resolvable policy IDs and persona routing has no persona layer. | Waiving it changes what S2 and S10 can assert. | S2, S10 |
| **Q8** | **What is the promotion authority record format,** and where does it live? Proposed: `.autoharness/gates/` alongside the existing force-audit logs. | Establishes a new audited authority surface. | S10 |
| **Q9** | **Confirm no backlogit change is required.** This artifact asserts zero backlogit change for S1–S9 (matching `028-DL` §8 and `029-DL` §7). `028-DL` Q3 flagged a possible `regression_of` link type for its Phase 2, which this portfolio does **not** authorize. | Cross-repo change requires separate authorization. | S9 scope boundary |

## Unresolved Questions

Items needing further **investigation** (as distinct from authority):

1. **Will the S1 SDK justify itself?** The falsifiable test is built in: if S1
   cannot ship `ART-01` end-to-end within its own task budget, Option A
   (independent gates) should be reconsidered. This is a genuine early exit, not
   a formality.
2. **F03a `STATE-03` precision is unknown.** The spike could not reduce a
   135-PR family to a predicate without discarding most members. The governed-
   token subset may prove too narrow to be worth building. Measure before
   planning S7's third cluster.
3. **AST false-positive rate on `src/**` is unmeasured.** The technique precedent
   exists (`docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md`,
   `2026-08-22-ast-scope-aware-alias-resolution-legb-pitfalls.md`) but no rule set
   has been run against this tree.
4. **Base-revision test execution without a second worktree** is asserted as
   achievable (read-only tree materialization) but not demonstrated. If it turns
   out to require a worktree, S6 collides with P-014/P-016 and must be
   re-deliberated rather than worked around.
5. **Thread-ID instability (`028-DL` R1)** and **suppressed body-only findings
   (R3)** remain unquantified and will bias S9's measure by an unknown margin.
6. **The 47% unclassified Copilot residue.** A hand-coded stratified sample
   (n ~ 200) would convert the spike's lower bounds into confidence-bounded
   estimates and could re-rank the portfolio. Not commissioned.
7. **Whether `PORTABILITY_RULES` extension re-triggers the allow-list problem**
   recorded in `docs/compound/012-S-portability-scan-allow-list.md`. New rules
   over an existing corpus have non-zero historical blast radius and therefore
   need the warn-then-block sequence, unlike S2.

## Risks and Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **RK1** | **The SDK becomes a write-only abstraction** — the `029-DL` F5 failure mode, and the strongest objection to Option C. | medium | high | S1 ships `ART-01` end-to-end or does not ship. Named early-exit to Option A. |
| **RK2** | **Detectors decay** because they depend on author-maintained per-artifact conventions (Law 2 cell 3/4). | medium | high | **No detector may require a new author-minted identifier** (A8). Detectors read data that already exists for other reasons, and are consumed at a decision point rather than maintained per artifact — the same escape `029-DL` §B1.2 identified. |
| **RK3** | **False positives convert review cost into build cost** — the spike's own unmeasured limitation #5. | **high** | high | Applicability predicates bound the surface; Phase-2 precision floor 0.80 and a <= 5/100 budget gate promotion; report-only until measured; any detector requiring judgment on every finding is dropped. |
| **RK4** | **Silent promotion to blocking.** A report-only program becomes enforcing by accretion. | medium | **high** | `severity` and `mode` are orthogonal (D7); no detector may set its own mode; promotion is S10-only, per-detector, operator-consented, recorded, reversible. |
| **RK5** | **Waiver semantics leak authority** into P-009/P-014/P-018/P-020 or destructive approval. | low | **critical** | D10 constraints: operator-only, scope-bounded to named refs, mandatory expiry, blocking-mode only, written to the existing audit surface, and explicitly carrying **no** authority over any other control. |
| **RK6** | **The portfolio is too large to finish** and lands three foundations plus no composition — the worst possible partial state. | medium | high | S8 requires only **three** domains (S2, S3, S4), not all six. S5/S6/S7 attach incrementally. A partial portfolio still produces a working readiness report. |
| **RK7** | **Auto-fix regenerates the family** — the `2026-08-07-copilot-review-fix-introduces-new-filter-bug` mechanism applied to the harness's own fixer. | medium | high | Only two classes may mutate, both confined to machine-produced artifacts; `CODE-02` permanently pinned to `guided_fix`; every mutation advances the epoch and forces full re-evaluation; the epoch budget (N95) bounds the loop. |
| **RK8** | **S9 fails its `028-DL` §9.3 falsification test**, leaving `8CB5A9B9` without an input. | medium | medium | This is a *designed* failure path, not an accident: S10's breaker is explicitly gated on S9, and failure means re-deliberating `8CB5A9B9` rather than building it blind. |
| **RK9** | **Over-claiming coverage.** Presenting 15 assigned families as 15 solved families would itself be an F03b defect inside the anti-F03b program. | medium | high | §"Honest coverage arithmetic" states the uncovered remainder explicitly; three families are assigned to routing, not detection; the C4 rule forbids labelling a subset finding as covering its family. |
| **RK10** | **Cross-repo scope creep** — building backlogit's frameworks inside autoharness. | medium | medium | `39AA674D` / `926FEA6D` / `A02280C8`(b) deferred to S11 behind a named-consumer condition; the `028-DL` §8 / `029-DL` §7 boundary rules are restated and unchanged. |
| **RK11** | **Detector registry cycles or schema drift** silently degrade the walk. | low | medium | A registry cycle is `invalid` -> exit 2, evaluates nothing, never auto-breaks; the registry is schema-validated; FC1 forbids `not_applicable` as a failure fallback. |

## Next Steps

Per `promote_to: none`, **no backlog item, plan, shipment, feature, task, or
stash mutation was created by this deliberation.** The following are
recommendations for a *future, operator-authorised* Stage pass, not actions taken:

1. **Resolve Q1, Q5, and Q7 first.** All three change what S1/S2/S4/S6 may
   assert, and all three are cheap to decide.
2. **Stage `S1` next**, with `S9` planned in the same pass (execution still
   serial). `S1` is the unique zero-prerequisite, highest-fan-out,
   zero-authority entry point.
3. **Run the §R6 yield probe before planning `PROV-04`.** It is a read-only
   measurement and it decides whether S4 carries three detectors or six.
4. **Do not re-own `336F3AB7` or `8AC574F1`.** Clear or waive them in their own
   right; recommend downgrading `8AC574F1` given 18/29 skills are now installed.
5. **Re-price the imported stash entries** to match this artifact's dispositions:
   `39AA674D` critical -> low; `926FEA6D` critical -> low (subset lifted into S7);
   `A02280C8` split with (b) -> low. **Not performed here** — re-prioritizing
   imported entries is operator-visible and this pass was read-only.
6. **Do not authorize any blocking promotion** until Phase 2 is complete per
   detector.

## References

**Prior work reconciled (mandatory scope)**

* `docs/decisions/2026-08-27-recurring-review-issues-tooling-opportunities-spike.md` — 15 dual-source families, counts, dual-source anchors, Tier 1/2/3 candidates, limitations
* `docs/decisions/2026-08-25-pr-review-convergence-finding-ledger-deliberation.md` (`028-DL`) — HEAD-keyed epochs, monotone measure, four-graph disambiguation, disposable-cache objection, cross-repo boundary, Phase 1 MVE and §9.3 falsification test
* `docs/decisions/2026-08-25-machine-produced-structure-determinism-and-the-surviving-dag-partition.md` (`029-DL`) — Law 1, Law 2 (corrected), Authority Test v2, the nine-surface partition, the pruned C6 candidate, and the C4.2 harness gap now cleared

**Compound learnings grounding specific design choices**

* `docs/compound/2026-08-07-copilot-review-fix-introduces-new-filter-bug.md` — fix-regenerates-the-family; the reason the epoch budget, not a finding budget, bounds the loop (RK7)
* `docs/compound/2026-08-12-hosted-review-catches-fail-closed-gaps-local-review-and-ci-miss.md` — F05/F09/F14 are structurally invisible to the implementer's own tests; the basis for S10's mandatory persona routing
* `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md` — the F03b generating mechanism; the basis for `PROV-05` dangling-definition
* `docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md` and `docs/compound/2026-08-22-ast-scope-aware-alias-resolution-legb-pitfalls.md` — S5 technique precedent
* `docs/compound/012-S-portability-scan-allow-list.md` — the existing F08 control S5 extends rather than replaces
* `docs/compound/114-S-109-F-copilot-review-fix-patterns.md` — the three-layer presence/shape/member checklist `CODE-01`/`CODE-02` enforce; suppressed-finding evidence (`028-DL` R3)
* `docs/compound/093-S-review-loop-convergence.md` — 13-round loop; push-not-resolution epoch boundary; S9 falsification population
* `docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md` — the regenerating-oracle mechanism

**Existing controls and contracts reused (requirement 13)**

* `src/autoharness/gates/topology.py` — `CheckResult`, `TopologyResult`, exit codes 0/1/2/3, three-colour cycle detection, `compute_dag_readiness`, `compute_next_eligible` `(-fan_out, id)` total order, the `_prior_shipment_id` defect precedent
* `src/autoharness/gates/discovery.py` — `discover_modified_files`, the applicability context source
* `src/autoharness/gates/copilot_review.py` — the GraphQL review-thread surface S9 reuses
* `src/autoharness/gates/sizing.py` — the gate-produced write-back precedent for `auto_fix_safe`
* `src/autoharness/verify_workspace.py` — `PORTABILITY_RULES`, `PORTABILITY_ALLOW_LIST`, `checksum_scan`, `upstream_updated`
* `schemas/validation-gates.schema.json` (v1.0.0) — the detector registry declaration point
* `.autoharness/backlog-registry.yaml` — `PAR-06`'s authoritative param map
* `.autoharness/gates/*-force-audit.log`, `pipeline-topology-telemetry.jsonl` — the audited-override and gate-telemetry precedents
* `.github/instructions/circuit-breaker.instructions.md` — MAXIMUM_RETRY_THRESHOLD = 3, the `policy_halt` binding

**Stash entries consumed as input (all left ACTIVE and unmodified)**

`D911A3B2`, `39AA674D`, `926FEA6D`, `A02280C8`, `3F80F8A3`, `C327A8DE`,
`7A3F570B`, `89E833E1`, `8CB5A9B9`, `34AAF1C7`, and as named prerequisites
`336F3AB7`, `8AC574F1`, `74C62374`.
