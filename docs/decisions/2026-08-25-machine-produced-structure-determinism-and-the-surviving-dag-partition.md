---
title: "Machine-Produced Structure, Not Graph Structure, Is the Binding Constraint on Determinism — with the DAG partition that survives"
date: 2026-08-25
status: decided
topic: "Where can DAG structure act as a steering mechanism toward determinism in autoharness workflows, and what actually determines whether such structure survives?"
description: "Three adversarial rounds. Isolating a confound (two conventions read by the same gate, differing only in whether absence is penalized) shows adoption diverging to 100% vs 41% at p=1.97e-05. Headline finding — the binding constraint is whether a machine produces the structure or penalizes its absence, not whether the structure is a graph. Seven of nine closed-world surfaces survive the resulting filter; two die. Ends BLOCKED on a named harness gap rather than a deferral."
depth: deep
source_stash: 34AAF1C7
deliberation_id: 029-DL
related_artifacts: [028-DL, 110-F, 115-F, 139-S, 001-SP]
linked_artifacts:
  - "docs/decisions/2026-08-25-pr-review-convergence-finding-ledger-deliberation.md"
  - "docs/decisions/2026-08-16-observable-termination-record-spike.md"
  - "docs/memory/2026-08-25-stage-029-dl-dag-steering-determinism.md"
prior_spike: docs/decisions/2026-08-16-observable-termination-record-spike.md
tags:
  - "dag"
  - "determinism"
  - "convention-durability"
  - "architecture"
  - "stage-deliberation"
source: docs/decisions/2026-08-25-machine-produced-structure-determinism-and-the-surviving-dag-partition.md
doc_type: decision
artifact_kind: deliberation
agent: stage
route: claude-opus-5 / anthropic / high
---

# Machine-Produced Structure, Not Graph Structure, Is the Binding Constraint on Determinism

> **ABSTRACT (rewritten after three adversarial rounds — read this, not §0).**
>
> This document opened as a survey of where DAG structure could steer the
> autoharness workflow toward determinism. It does not conclude that.
>
> **Headline finding: the binding constraint on determinism is not whether
> structure is a graph. It is whether a MACHINE PRODUCES THE STRUCTURE OR
> PENALIZES ITS ABSENCE.** Measured in-repo at p = 1.97e-05 by isolating the
> confound: two conventions read by the *same* gate over the *same* corpus in the
> *same* period, differing only in whether absence is tolerated, diverged to
> **100%** and **41%** adoption.
>
> **The DAG question is ANSWERED, not abandoned or superseded** — but the answer
> is a precondition the original question did not anticipate: *graph structure
> steers only where its node identity is machine-produced.* Applying that filter
> partitions the nine closed-world surfaces into graphs that are derivable from
> data machines already write (viable, and always were) and graphs requiring new
> author-maintained node identity (will decay; must be paired with a generator
> first). §C1 gives the partition.
>
> **Two of this document's own #1 recommendations were withdrawn on measurement**
> (§A4, §B1.2), and one DAG-shaped candidate was rejected on a measured 0% defect
> rate (§C1.3). The surviving recommendation is read-only, retrospective, and
> requires no new authority — and §C4 records that even it does not fully clear
> Stage's own gates, with the unmet criteria named.
>
> Original title: *DAG as Steering Mechanism: A Determinism Opportunity Map.*
> Retitled per Round-3 §1: a document titled for the question it began with while
> concluding something else is the silent-drift failure this program exists to
> detect.

## DAG as Steering Mechanism: A Determinism Opportunity Map

* **Stash (living tracker)**: `34AAF1C7` — annotated, linked, **not archived**
* **Deliberation artifact**: `029-DL`
* **Widens**: `028-DL` (narrow question: PR-review convergence). Does **not** overturn it.
* **Mode**: normal (non-dark) Stage deliberation; **strictly read-only**
* **Verdict**: **The operator is right. Several opportunities are genuinely strong.**
  One first slice is ready to plan on operator go. No harvest this session — by
  choice, stated and defended in §12, not by deferral.

---

### 0. Executive answer

The prior deliberation's conclusion — "the DAG here is a diagnostic layer" — is
**sound for its question and too narrow as a general claim**, in one precise
respect:

> `028-DL` tested the DAG against **termination**, which is the single
> determinism property a DAG provably *cannot* deliver, and generalized that
> failure to DAGs as such. Of the six determinism properties in play, a DAG
> delivers **three** outright (choice elimination, coverage/reachability,
> auditability), delivers one **only inside a hermetic sub-executor**
> (reproducibility), and cannot deliver two (termination, memoization).
> The three it delivers are precisely the three this harness is weakest at.

The second, independently important reframe:

> **Report-only is not the same as non-steering.** The declared no-scheduler
> non-goal constrains *who dispatches work and how many at once*. It does not
> constrain *narrowing the choice set to a singleton*. `compute_next_eligible`
> already proves this in-repo: it is read-only, honors P-001/P-016, creates no
> scheduler — and yet **uniquely determines the next shipment** through a total
> order. Steering comes from **constraining choice**, not from scheduling.
> **The non-goal does not need revisiting.** Every proposal below fits inside it.

And the empirical headline, measured this session over 964 artifacts:

> **The richest dependency graph in this workspace has no reader.** There are
> **452 task→task `blocks` edges** and **no analyzer reads them**. The graph
> that *does* have a reader — the shipment graph — carries **26 edges across 149
> shipments**, which is why `dag-readiness` reports a **critical path of 2 nodes
> over 149 shipments**. That number measures the poverty of the graph, not the
> structure of the work. Real ordering is carried by an **undeclared numeric-ID
> convention**, which the topology gate is forced to reverse-engineer in
> `_prior_shipment_id` — a heuristic that has produced **two consecutive
> correctness defects** (both recorded in `docs/compound/`, 2026-08-18).

Missing graph structure in this repo is not a theoretical tidiness concern.
It has already shipped bugs.

---

### 1. Disambiguating "determinism in outcome delivery"

The operator's phrase bundles six distinct properties. They have different
mechanisms and different feasibility. Telling them apart is the first
deliverable.

| # | Property | Precise statement | DAG alone delivers? | Required pairing | Feasible in this harness? |
|---|---|---|---|---|---|
| D1 | **Reproducibility** | same inputs ⇒ same action sequence | **No** | hermetic nodes + content-addressed inputs | **Only inside the installer** (§4, C5) |
| D2 | **Choice elimination** | the next action is uniquely determined, not model-discretionary | **Yes**, given a closed node set | deterministic total order (tie-break) over the ready-set | **Yes — already demonstrated** |
| D3 | **Coverage / reachability proof** | outcome is *provably* complete, not plausibly complete | **Yes**, over a closed subgraph | closed-world node set + typed edges + completion predicates | **Yes** |
| D4 | **Termination** | work provably reaches a terminal state | **No** | well-founded strictly-decreasing measure | **No** (this is `028-DL`'s result) |
| D5 | **Memoization / incrementality** | re-runs are idempotent and skippable | **No** | hermeticity + content-addressed outputs | **No** for agent nodes; **yes** for the installer |
| D6 | **Auditability** | outcome verifiable from recorded structure, not trusted from prose | **Yes** | resolvable evidence edges + completion predicates | **Yes** |

**The quantifier error in the prior framing.** `028-DL` proved, correctly and
importantly, that *acyclicity implies termination only over a finite fixed node
set*. That is a result about **D4**. It says nothing about D2, D3, or D6, all of
which hold over *closed* subgraphs — and most of the autoharness workflow graph
*is* closed at the moment it matters. A plan's implementation-unit set is closed
at plan-review time. A shipment's manifest is closed at assembly time. A
capability-pack composition is closed at install time. The open node sets — review
findings, CI failures — are exactly the surfaces `028-DL` was studying.

**So the correct rule is not "DAGs are diagnostic here." It is:**

> Where the node set is **closed at gate time**, a DAG delivers D2/D3/D6 as
> *proof*. Where the node set is **generated by an external oracle during
> execution**, a DAG delivers only diagnosis, and D4 needs a monotone measure.

`028-DL` studied the second case. Nearly everything else in this harness is the
first case.

---

### 2. What a DAG structurally provides — and what it does not

**Provides (topology and provenance only):** partial order; reachability and
transitive closure; ready-set computation; frontier/cut semantics; critical
path; cycle and SCC detection; invalidation *boundaries*; lineage/provenance.

**Does not provide alone:** termination over a dynamic node set; a *total* order
(needs an explicit tie-break); idempotency; hermeticity; defense against a
nondeterministic oracle; semantic correctness of the edges themselves.

That last one deserves emphasis, because it is the failure mode this
deliberation is most at risk of: **a DAG cannot tell you its edges are the right
edges.** Every proposal below must therefore either derive its edges from data
that already exists for an independent reason, or subject asserted edges to a
consistency check against independently-derived ones. Proposals that invent
edges by fiat are ceremony.

#### 2.1 The build-graph hypothesis, evaluated honestly

> *Hypothesis under test: the autoharness pipeline is already a build graph
> executed by a nondeterministic agent, and the determinism gap is that its
> nodes, edges, inputs and completion predicates are asserted in prose rather
> than represented as a graph.*

**Where it holds — strongly, and more than expected:**

* The artifact chain *is* a dataflow: stash → deliberation → plan → review verdict
  → feature → tasks → shipment → branch → PR → merge → closure → compound learning.
  Each stage is a file that names its predecessors.
* **Node identity — the genuinely hard part of graph-building — is already
  solved and externally supplied.** backlogit IDs (`115.001-T`), repo-relative
  file paths, git SHAs, PR numbers, GitHub review-thread node IDs. Nothing needs
  inventing. This is the single strongest argument for the whole program, and it
  is the same unlock `028-DL` §9.2 identified for its narrow case.
* **HEAD-pinning already exists.** `gate_evidence` carries `head_sha` and
  `evidence_sha`. The repo independently invented the build-system idea that
  evidence is valid *relative to an input version*.
* **Machine-readable completion predicates already exist in places.**
  `status: shipped`; closure `conditions: [{satisfied: true, evidence: ...}]`;
  gate exit codes.

**Where it breaks — and these must be stated plainly, because they prune hard:**

1. **Agent nodes are not hermetic.** An agent node reads the entire repo, the
   model's weights, and the operator's replies. Its input set is not enumerable,
   so a content hash over "the inputs" is unsound. Bazel-style caching is
   unavailable.
2. **Outputs are not usefully content-addressable.** Two correct plans for the
   same input differ textually. Hash equality is too strict; semantic equality is
   undecidable. Cache hits would be vanishingly rare, and unsound when they occur.
3. **The executor is stochastic.** Same node, same inputs, different output.
   **D1 is unattainable for agent-executed nodes. Stop pursuing it there.**
4. **The node set is partly open.** Review findings, CI failures, and follow-up
   tasks are generated during execution. D4 is unattainable; D3 proofs are valid
   **only over the closed subgraph**, and must say so.

**Therefore, the disciplined form of the hypothesis:**

> autoharness is a build graph in its **topology and provenance**, but *not* in
> its **execution semantics**. Import from build systems exactly the parts that
> depend only on topology and provenance — ready-sets, frontiers, reachability,
> cycle detection, lineage, invalidation boundaries. Do **not** import the parts
> that depend on hermeticity and content-addressed outputs — caching, incremental
> skipping, remote execution, reproducible rebuild.

The right prior art is therefore **not** Bazel or Nix. It is closer to:

* **Make's `-n` / dependency checking** — a *checker* over the build graph rather
  than an executor of it;
* **SLSA-style provenance graphs** — lineage as evidence, with no re-execution claim;
* **Salsa's invalidation without its caching** — knowing what went stale, without
  claiming you can skip it;
* **Airflow's ready-set without its scheduler** — which is, precisely and
  literally, what `dag-readiness` + `compute_next_eligible` already are.

**One genuine exception, and it is important:** the **installer is hermetic**.
Composition of `preset + stack_packs + install_layers + capability_packs +
template variables` into a workspace is a **pure function executed by code, not
by an agent**. Inside that boundary, full build-system determinism — content
hashing, reproducible composition, drift detection, memoization — is legitimately
available. It is the only place in the harness where D1 and D5 are on the table.
See candidate **C5**.

---

### 3. Ground truth: the existing DAG surface (measured, not assumed)

Established by direct inspection this session. **Do not propose what already exists.**

#### 3.1 Already implemented

| Surface | What it is | Determinism property |
|---|---|---|
| `autoharness gate dag-readiness` | Read-only ready-set / critical-path / downstream-dependents over the **shipment-blocks** graph. Owns 3-colour DFS cycle detection. Existence-guarded; degrades non-fatally; never fabricates a graph on a detected cycle. | D3 (partial), D6 |
| `compute_next_eligible` (115-F) | **Read-only resumption cursor.** Anomaly-first resolution over the *full unfiltered* enumeration, then a **total order**: DESC downstream fan-out, then ASC id. 7 observable outcomes. | **D2 — genuine choice elimination** |
| `gate pipeline-topology` | Fail-closed shipment/worktree topology gate; branch ownership; predecessor closure; ambiguity detection. | D2, D6 |
| backlogit `item_deps` | 488 `blocks` edges (452 task→task, 26 shipment→shipment, 1 feature→feature). | storage only |
| backlogit `item_links` | 29 semantic links (`informs` 13, `related_to` 11, `supersedes` 3, `duplicate_of` 1, `spike_ref` 1). | storage only |
| `backlogit_doctor` | Structural scan: orphaned artifacts, duplicate IDs, partial mutations, shipped-event completeness. **No dependency-topology checks at all.** | D6 (partial) |
| Closure `conditions:` block | `_closure_artifact_complete` requires every condition `satisfied: true` **and** a non-empty `evidence` reference. | D6 (partial) |
| `gate_evidence` | `head_sha` / `evidence_sha` HEAD-pinning. One row per item (snapshot, not history — `028-DL` §2.2). | invalidation key |
| P-003 | Decomposition chain integrity — **already a graph-integrity policy**, enforced by prose + doctor's orphan check only. | D3 (asserted) |
| P-017 `DARK_MODE_SCOPE` | Ordered shipment sequence + restart cursor, reconstructed by traversing `item_deps`. | D2, D6 |

#### 3.2 Measured state of that surface — the findings that drive everything below

| Measurement | Value | Significance |
|---|---|---|
| Total artifacts indexed | 964 | |
| task→task `blocks` edges | **452** | **No reader exists.** Dark data. |
| shipment→shipment `blocks` edges | **26** across 149 shipments | The only graph with a reader is nearly empty |
| `dag-readiness` critical path (live) | **2 nodes** (`139-S` → `138-S`) | Measures graph poverty, not work structure |
| Shipments declaring `dependencies:` | **24 / 149** | 84% of ordering is undeclared |
| Shipments using `queue_position` | **1 / 149** | The Shipment Sequencing Protocol's explicit-ordering mechanism is *de facto* unused |
| Shipments with `items:` manifest | **149 / 149** | Membership **is** reliably derivable |
| Covering feature derivable from item parents | **141 / 149** (2 multi-feature, 6 underivable) | Covering feature does not need `covering_feature_id` (present in 1/149) |
| Cross-shipment task→task edges | **63** | Real cross-cutting structure exists |
| …of those, **with** a declared shipment-level ordering | 42 | |
| …of those, **without** any declared shipment-level ordering | **21 (33%)** | **The ordering constraint exists in data but is invisible to every shipment-level analyzer** |
| Cross-shipment edges violating the numeric-ID convention | **0** | The convention has held — by luck and discipline, unrepresented and unverifiable |
| Malformed dependency endpoints | **9** (literal `'["003.001-T"]'` — a JSON string leaked into a YAML list) | Undetected by doctor, by any gate, for 4 months |
| Cycles in the task graph | **0** | A *result*, and currently unverified by anything |
| Tasks with no parent (P-003) | **3** | Detected by doctor |
| Tasks in no shipment manifest | **11** | Undetected by anything |

#### 3.3 The load-bearing consequence

Because 84% of shipment ordering is undeclared, `pipeline-topology` cannot read
the order from the graph. It instead **reverse-engineers the numeric-ID
convention** in `_prior_shipment_id`: *"the highest-numbered shipment strictly
below the target is my implicit predecessor."*

That heuristic has produced **two consecutive recorded correctness defects**:

* `docs/compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md`
  — multi-hop reverse dependency yields a false PASS (severity medium);
* `docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`
  — the fix for the first introduced an opposite-direction false negative that
  **silently allows claiming a shipment that should have been blocked**
  (severity **high**).

> **This is the empirical core of the case for the operator's instinct.** The
> heuristic exists *only because the edges are not declared*. Every defect it has
> produced is a determinism defect caused by absent graph structure. Materializing
> the derivable edges removes the need for the heuristic entirely.

#### 3.4 The prose-vs-graph gap, in the planning path

Three graph predicates are stated as **quality criteria** in
`templates/skills/impl-plan/SKILL.md.tmpl` and evaluated by **a model reading
prose**:

* *"Every requirement from the source document maps to at least one implementation unit"* — a **reachability/coverage** claim (D3);
* *"Dependency graph has no cycles"* — a **graph property** (asserted, never computed);
* *"#### Dependency Graph — Identify which units depend on others."* — free-form prose.

`plan-review` checks **persona** coverage, not **plan-graph** coverage. It has no
graph-property check whatsoever.

Meanwhile `harvest` step 5 already consumes *"Dependency edges from the plan's
dependency graph"* and writes them to backlogit as real `blocks` edges. So:

> **The plan's graph becomes machine-readable exactly one step *after* the gate
> that should have validated it.** Shifting that one step left is candidate C1.

---

### 4. The opportunity map — 15 candidates, generated then pruned

Node identity is called out explicitly for each, because it is the hard part and
it is where most graph proposals die.

#### KEEP — near-term, bounded, zero new authority

---

**C13. Derived-vs-declared ordering consistency ("edge lift")** — *strongest evidence*

* **Nodes**: backlogit shipment IDs and task IDs. **Identity: externally supplied.** Nothing invented.
* **Edges**: existing task→task `blocks`; existing shipment→shipment `blocks`; shipment `items:` membership.
* **Semantics**: if task *a* (in shipment *S₁*) blocks-depends on task *b* (in shipment *S₂*), *S₁≠S₂*, then *S₂ must ship before S₁*. Check whether that ordering is reachable in the declared shipment graph.
* **Owner**: **autoharness**. The *lift* from task-level edges to shipment-level ordering is workflow semantics; backlogit must never learn it.
* **Storage**: none. **Derived at read time** from markdown. Zero schema change.
* **Delivers**: **D2** (a ready-set that is finally trustworthy) + **D6**.
* **Measured yield**: 21 undeclared ordering constraints; directly explains the two `_prior_shipment_id` defects.
* **Blast radius**: LOW as a report. **Authority: none.**
* **Falsifier**: if the numeric-ID convention is a *sufficient* substitute — i.e. the 21 gaps never correlate with a recorded defect and never will — the lift buys nothing.

---

**C12. Backlog graph integrity (P-003 made mechanical)**

* **Nodes**: backlogit artifact IDs. **Identity: supplied.**
* **Edges**: `item_deps` (blocks), `parent_id` (parent_of), shipment `items:` (contains).
* **Semantics**: endpoints must resolve; the task graph must be acyclic; every task must have a parent; every task must be covered by exactly one shipment manifest.
* **Owner**: autoharness (P-003 is autoharness policy). Overlaps doctor's orphan check — **cite it, do not duplicate it**.
* **Storage**: none; derived.
* **Delivers**: **D3** + **D6**.
* **Measured yield**: 9 malformed edges, 3 orphans, 11 uncovered tasks, 0 cycles — 23 real findings invisible to every existing tool.
* **Blast radius**: LOW. **Authority: none.**

---

**C6. Cross-reference integrity graph** *(absorbing C11, knowledge lineage)*

* **Nodes**: repo-relative file paths + frontmatter IDs. **Identity: supplied, free.**
* **Edges**: markdown links; explicit `see X` references; frontmatter `source:`, `citations:`, `supersedes:`, `related_artifacts:`.
* **Semantics**: every reference must resolve; every instruction/skill/agent file should be **reachable from at least one agent contract**.
* **Owner**: autoharness (`verify-harness` already owns adjacent checks — it scans unresolved `{{...}}` placeholders and name coherence, but has **no reference graph**).
* **Delivers**: **D6**, plus a property no other candidate offers —
  > **an artifact with zero inbound reference edges is *provably* never read.**
  > That makes the **F5 "written-but-unread" failure mode mechanically detectable**,
  > which is the objection that has killed two prior attempts in this line of work.
* **Also catches**: acting on a **superseded** compound learning. The 2026-08-18
  topology pair supersede each other partially — that relation is in frontmatter
  today and nothing enforces it.
* **Blast radius**: LOW. **Authority: none.**

---

**C8. Evidence / provenance graph (P-014 / P-018 / P-020 made structural)**

* **Nodes**: closure artifacts, gate evidence rows, commits, PRs, backlog items. **Identity: paths + SHAs + PR numbers — all supplied.**
* **Edges**: `evidences` (closure condition → evidence artifact), `attests` (gate evidence → head_sha), `merges` (PR → commit → item).
* **Semantics**: a closure condition is satisfied only if its evidence reference **resolves** and is **pinned to the reviewed HEAD**.
* **Current gap, precisely**: `_closure_artifact_complete` requires `evidence` to be **non-empty**. It never resolves it. **A closure artifact citing `docs/closure/does-not-exist.md` passes today.** The edge target is unvalidated.
* **Owner**: autoharness entirely.
* **Delivers**: **D6** in its strongest form — outcome verified from structure rather than trusted from prose. This is the literal definition the operator asked for.
* **Blast radius**: LOW report-only; **becomes authority-touching only if it blocks.**

---

#### KEEP — strategic, larger, still no new authority

---

**C1. Plan-as-DAG (shift the graph one step left)**

* **Nodes**: plan implementation units. **Identity: currently invented ad hoc in prose — but `harvest` already converts them into backlogit IDs one step later.** Fix: have `impl-plan` emit plan-local stable IDs (`U1..Un`) that `harvest` maps to backlog IDs, preserving lineage.
* **Edges**: `unit → unit` (depends_on); `requirement → unit` (covered_by); `unit → verification` (verified_by).
* **Semantics + gate**: `plan-review` mechanically checks — acyclic; no orphan units; **every acceptance criterion reachable from ≥1 unit**; every unit reachable from ≥1 requirement; every unit has ≥1 verification.
* **Delivers**: **D3** (coverage becomes a reachability *proof*, not a narrative claim) + **D6**.
* **Blast radius**: **MEDIUM-HIGH** — edits `impl-plan` and `plan-review` agent-contract prose. This is exactly the **F4** objection ("prose-only bounds ⇒ emission edits every agent's contract surface") that the 2026-08-16 spike raised. It is the reason C1 is *not* the first slice despite being the highest-yield candidate.
* **Authority: none**, but it changes what a plan *is*, so it wants operator ratification.

---

**C5. Install / tune composition graph — the one hermetic island**

* **Nodes**: presets, stack packs, install layers, capability packs, template files, template variables. **Identity: supplied (names + paths).**
* **Edges**: `layer_precedes`, `pack_overlays_base` (the Required Overlay Contract already mandates that an overlay reference its base), `template_requires_var`, `var_resolves_from`.
* **Key observation**: `install_layers` in `config.yaml` is an **ordered list** — a hand-maintained *linearization of a dependency graph that is never declared*. The graph is the source; the list is a derived artifact maintained by hand. That is backwards.
* **Why this one is special**: **composition is a pure function of config, executed by code, not by an agent.** This is the **only** place in the harness where **D1 (reproducibility)** and **D5 (memoization)** are legitimately attainable — and therefore the only place real build-system technique (content hashing, reproducible composition, drift detection) genuinely applies.
* **Delivers**: **D1 + D3 + D6** — and *drift detection*: prove the installed workspace equals the deterministic composition of its declared inputs.
* **Blast radius**: MEDIUM-HIGH (installer). **Authority: none.**

---

**C14. Shipment coverage closure**

* **Semantics**: a shipment is complete iff every task under its covering feature is either in its manifest or explicitly deferred with a recorded reason.
* **Nodes/edges**: reuses C12's `contains` + `parent_of`. Not a separate build — a query over the same graph.
* **Delivers**: **D3**. **Measured yield**: 11 tasks in no shipment; 2 shipments spanning multiple features; 6 with no derivable covering feature.
* Merge into C12's report as a finding class.

---

**C4. Pipeline phase graph (modest, honest)**

* **Nodes**: Stage/Ship phase names. **Identity: supplied by the agent contracts.**
* **Edges**: legal successor transitions.
* **Real gain, and it is narrow**: make the checkpoint `phase` field a **validated position in a transition graph**, so a crash-resume cannot land on an illegal phase. Today `phase` is a free string.
* **Caution**: phases are a mostly-linear *control-flow* graph with conditionals, not a dependency DAG. And this surface sits near "governing when agents stop" — keep it **report-only**.
* **Delivers**: D6 + a little D2. **Yield: modest. Rank: mid.** Do not oversell.

---

**C2. Traceability / coverage spine** — **not a separate build.** This is the
*composition* of C1 + C12 + C8 through the shared node namespace: requirement →
unit → task → shipment → commit → PR → evidence → closure. Framing it as its own
graph would be the `028-DL` §2.1 error (collapsing distinct graphs into one).
Treat as the **integration target**, delivered incrementally by C1/C8/C12.

**C9. Review-finding disposition graph** — already scoped by `028-DL` Phase 2.
Placed on the map; **not duplicated**. Note it is the *only* candidate whose node
set is genuinely open, and therefore the only one that needs a monotone measure
rather than a graph. That is what makes it the exception, not the rule.

---

#### PRUNE — cargo-cult DAG

A credible expansive analysis rejects some of its own ideas. These three add
ceremony without determinism.

---

**C3. Quality-gate DAG — PRUNED.** There are ~5 gates (`check`, `size`,
`copilot-review`, `pipeline-topology`, `dag-readiness`) in a mostly-linear order
with a documented fail-closed/advisory split. **A DAG over 5 nodes with a known
order is a table drawn as a graph.** Reachability, ready-sets, and critical paths
are all trivial at that size, so the DAG machinery delivers nothing the existing
table does not. *There is a real problem hiding here, but it is not a graph
problem*: gate-evidence **invalidation on HEAD change** — which is a **cache key**,
already embryonically solved by `gate_evidence.head_sha`. **Keep the cache-key
discipline; reject the graph.**

**C7. Policy interaction DAG — PRUNED.** The interesting policy failures —
contradiction, shadowing, unreachable conditions — are **logical**, not
topological. Reachability over a precedence graph cannot detect that two policies
impose incompatible obligations under the same condition; that needs a constraint
solver or at minimum an explicit condition matrix. Encoding policy precedence as
a DAG would produce **false precision**: a structure that looks checkable and
proves nothing. The genuinely useful artifact is a **policy cross-reference
matrix**, which is just C6 applied to `workflow-policies.md`. Fold it there.

**C10. Memoization / invalidation DAG — PRUNED (with one carve-out).** Fails on
all three hermeticity grounds in §2.1: non-enumerable inputs, non-content-addressable
outputs, stochastic executor. Cache hits would be vanishingly rare and unsound
when they occur. **Carve-outs, both already noted**: (i) the *invalidation* half
without the *caching* half is sound and already exists as `head_sha` pinning —
keep it, it is not a DAG; (ii) memoization is legitimate **inside the installer
only** (C5), because that executor is hermetic.

---

### 5. Ranked opportunity map

Ranked by **determinism yield ÷ (blast radius × authority required)**.

| Rank | ID | Candidate | Delivers | Status | Blast radius | Operator authority | Evidence today |
|---|---|---|---|---|---|---|---|
| — | — | `dag-readiness`, `compute_next_eligible`, `pipeline-topology` | D2, D3, D6 | **ALREADY IMPLEMENTED** | — | — | shipping |
| **1** | **C12+C13+C14** | **Backlog graph integrity + edge lift + coverage** | **D2, D3, D6** | **NEAR-TERM — first slice** | **LOW** | **none** | **44 real findings, measured this session** |
| 2 | C6 | Cross-reference integrity (+ knowledge lineage) | D6 | NEAR-TERM | LOW | none | verify-harness has adjacent checks, no ref graph |
| 3 | C8 | Evidence / provenance graph | D6 (strongest) | NEAR-TERM | LOW report-only | none until it blocks | `conditions:` block exists; refs never resolved |
| 4 | C1 | Plan-as-DAG | **D3 (highest yield)**, D6 | NEAR-TERM+ | **MEDIUM-HIGH** (agent-contract prose, F4) | ratification advised | harvest already consumes the graph, one step too late |
| 5 | C5 | Install/tune composition graph | **D1**, D3, D6 | STRATEGIC | MEDIUM-HIGH | none | `install_layers` is a hand-linearized DAG |
| 6 | C4 | Pipeline phase graph | D6, some D2 | SPECULATIVE | LOW report-only | keep report-only | checkpoint `phase` is a free string |
| 7 | C2 | Traceability spine | D3, D6 | **INTEGRATION TARGET** — not a build | — | — | emerges from C1+C8+C12 |
| 8 | C9 | Review-finding disposition | diagnosis only; D4 needs a measure | SCOPED IN `028-DL` | — | **yes, Phase 3** | see `028-DL` |
| ✗ | C3 | Quality-gate DAG | none | **PRUNED** — cargo cult | — | — | 5 nodes, known order |
| ✗ | C7 | Policy interaction DAG | none | **PRUNED** — cargo cult | — | — | failures are logical, not topological |
| ✗ | C10 | Memoization DAG | none for agent nodes | **PRUNED** — cargo cult | — | — | non-hermetic; carve-outs kept |

**The strongest opportunities, stated plainly, as the operator asked:**

1. **C12+C13** is the strongest *near-term* opportunity. It is zero-authority,
   read-only, requires no new storage, needs no new node identity, is prototyped
   and validated in this session, and it addresses a defect class that has
   **already shipped two bugs**.
2. **C1 (Plan-as-DAG)** is the strongest opportunity *overall*. It converts the
   single most important quality claim in the pipeline — *"every requirement maps
   to at least one implementation unit"* — from a model's prose judgment into a
   reachability proof. Its cost is real (agent-contract prose, F4) and that is
   the only reason it is not first.
3. **C6** is the highest leverage per line of effort, because it makes the
   **F5 written-but-unread failure mode mechanically detectable** — the exact
   objection that has repeatedly killed work in this line.

---

### 6. Recommended architecture: one node namespace, several typed edge families

**Answer to "one graph or several?": one *node namespace*, several *edge
families*, and explicitly NOT one graph.**

Rationale. The nodes are already unified by **identity** — everything is a
backlogit ID, a repo path, a git SHA, or an external ID. The edges are *not*
unified by **semantics**: `blocks` (execution order), `supersedes` (knowledge
lineage), and `evidences` (proof) have different validity rules, different
owners, and different consumers. Merging them into one graph would repeat
`028-DL` §2.1's error of collapsing four distinct graphs into one.

```text
L0  IDENTITY — Universal Artifact Reference (UAR). Scheme-prefixed, no new IDs invented.
      bl:115.001-T   path:docs/plans/x.md   git:8996b46   gh:pr/348   gh:thread/<nodeid>

L1  EDGE FAMILIES — each declares {owner, source of truth, validity rule, REQUIRED reader}
      blocks       bl:  -> bl:      backlogit item_deps          reader: dag-readiness, pipeline-topology  [EXISTS]
      parent_of    bl:  -> bl:      backlogit parent_id          reader: doctor / P-003                    [EXISTS]
      contains     bl:S -> bl:T     shipment custom_fields.items reader: NONE                              [GAP -> C12/C14]
      implies_order bl:S -> bl:S    DERIVED from blocks+contains  reader: NONE                             [GAP -> C13]
      references   path:-> path:    markdown links + frontmatter reader: NONE                              [GAP -> C6]
      supersedes   *    -> *        item_links + frontmatter     reader: NONE                              [GAP -> C6]
      evidences    path:-> path:|git: closure conditions:        reader: PARTIAL (non-empty only)          [GAP -> C8]
      covered_by   req  -> unit     impl-plan graph block        reader: NONE (prose)                      [GAP -> C1]
      composes     pack/layer -> path: installer composition     reader: PARTIAL (verify-harness)          [GAP -> C5]
      disposition  gh:thread -> gh:thread                        reader: proposed                          [028-DL Phase 2]

L2  ANALYZERS — pure functions over ONE edge subset. Read-only. No persistence.
L3  BINDINGS  — the agent-contract sentence that makes an analyzer's output authoritative.
```

#### Two architectural laws

**Law 1 — DERIVE, NEVER PERSIST.** The source of truth is always the
markdown/config that already exists for an independent reason. Analyzers compute
the graph as a **view at read time**; no analyzer may persist a graph.

*Why this matters:* it **dissolves `028-DL` §2.2's disposable-cache objection
entirely** for C1, C5, C6, C8, C12, C13, C14. A derived view cannot be destroyed
by `backlogit_sync_index`, because it is recomputed from the same markdown that
sync itself rehydrates from. It also means **zero new storage, zero new schema,
and zero backlogit change** for every KEEP candidate except `028-DL` Phase 2.
Precedent already exists: `FilesystemTopologyReaders` reads shipment markdown
directly rather than trusting the index.

**Law 2 — NO GRAPH WITHOUT A READER; NO READER WITHOUT A BINDING.** Every edge
family must name the analyzer that consumes it, and every analyzer must name the
gate or agent-contract step that acts on its output. An edge family with no
reader is dark data — which is **the present, measured condition of the 452
task→task edges** and precisely the F5 failure mode. C6 makes violations of Law 2
mechanically detectable, which is why it ranks so high for its size.

#### Where determinism actually comes from

The DAG is never sufficient on its own. Each property requires a named pairing:

| Property | DAG construct | **Required pairing — without which there is no determinism** |
|---|---|---|
| **D2** choice elimination | ready-set over `blocks` | **deterministic total order.** A ready-set of size >1 is a *choice*, not a decision. `compute_next_eligible`'s `(-fan_out, id)` tie-break is the in-repo reference implementation and must be imitated, not reinvented. |
| **D3** coverage proof | reachability / transitive closure | **closed-world node set** declared at gate time + **completion predicates**. A reachability proof over an open node set is a lie; every D3 claim must state its closure boundary. |
| **D6** auditability | provenance/lineage edges | **resolvable edge targets.** An unresolved `evidence:` string is not an edge (C8's exact gap). |
| **D1** reproducibility | composition graph | **hermeticity + content addressing.** Available **only** inside the installer. |
| **D4** termination | — | **well-founded monotone measure.** Not a graph property (`028-DL`). |
| **D5** memoization | invalidation boundary | **hermeticity.** Keep HEAD-pinned invalidation; reject caching. |

---

### 7. Cross-repo boundary

Consistent with and extending `028-DL` §8.

| Concern | Owner |
|---|---|
| Node persistence (markdown), generic edge storage (`item_deps`, `item_links`, `parent_id`, shipment `custom_fields.items`), generic query, append-only logs, structural doctor checks (orphan, duplicate) | **backlogit** |
| The UAR scheme; **all derived-edge semantics**; every analyzer; thresholds and verdicts; policy binding (P-003 / P-014 / P-018 / P-020); the meaning of "ready", "covered", "complete" | **autoharness** |

**New boundary rule established by this deliberation:**

> **backlogit must never learn that a task-level `blocks` edge implies a
> shipment-level ordering.** That lift is workflow semantics and belongs
> entirely to autoharness. backlogit stores edges; autoharness interprets them.

**Access rule:** analyzers read through public backlogit MCP/CLI surfaces and
through markdown — **never by direct SQLite writes**, and preferentially not by
direct SQLite reads either, since the index is a disposable cache. Markdown-first
reading (the `FilesystemTopologyReaders` precedent) also makes the analyzers
immune to index staleness.

**Change required in backlogit for the recommended first slice: none.** As in
`028-DL`, that is itself evidence the boundary is drawn in the right place.

---

### 8. Recommended FIRST SLICE

#### `autoharness gate backlog-graph-integrity` — read-only, report-only, exit 0 in v0

A read-only analyzer over the **already-existing** backlog graph, modelled
directly on the proven `dag-readiness` contract (existence-guarded, `--json`,
degrades non-fatally, never fabricates a graph).

**Six finding classes** (measured yield from this session's prototype in
parentheses):

| Class | Definition | Found |
|---|---|---|
| `MALFORMED_EDGE` | dependency endpoint is not a well-formed artifact ID | **9** |
| `DANGLING_EDGE` | well-formed endpoint that resolves to no artifact | 0 |
| `CYCLE` | cycle in the task-level `blocks` graph | **0** (a result — currently unverified by anything) |
| `ORPHAN_TASK` | task with no parent (P-003) — *cite `backlogit_doctor`, do not duplicate* | 3 |
| `UNCOVERED_TASK` | task in no shipment manifest | **11** |
| `UNDECLARED_SHIPMENT_ORDERING` | cross-shipment task edge with no reachable shipment-level ordering | **21** |

**Why this slice and not the higher-yield C1:**

* **Zero new prose.** It changes no agent contract, no template, no policy — the
  **F4** objection that killed the 2026-08-16 spike is dodged entirely. C1 cannot
  say this.
* **Reader-only.** Nothing write-only exists, so **F5** cannot apply — the same
  argument that made `028-DL`'s MVE acceptable.
* **No instrumentation needed.** 964 artifacts, 478 edges, 149 manifests already
  exist. Same unlock as `028-DL` §9.2.
* **It extends a proven surface.** `FilesystemTopologyReaders` already parses
  shipment markdown; `compute_dag_readiness` already does 3-colour cycle detection
  and transitive closure. This is an extension, not new plumbing.
* **Its one open unknown was closed in this session.** Manifest format drift was a
  live risk (`covering_feature_id` present in only 1/149). Resolved: `items:` is
  present in **149/149**, and the covering feature is derivable from item parents
  in **141/149**, with the 8 exceptions themselves being findings. **The slice is
  unblocked.**
* **It is already prototyped.** The analysis above was executed read-only this
  session and produced 44 findings. Confidence is high, not speculative.

**Scope guard:** report-only, always exit 0 in v0. It governs nothing. Promotion
to a blocking gate is a separate, authority-touching decision (§10, Q2).

#### 8.1 Falsification test — pre-registered

The broader DAG program is **SUPPORTED** only if all four hold:

* **(a) Correlation with recorded defects.** `UNDECLARED_SHIPMENT_ORDERING` must
  be non-empty **and** overlap the shipments implicated in the two
  `_prior_shipment_id` compound learnings (`docs/compound/2026-08-18-*`).
* **(b) Actionability.** ≥1 finding must be true and actionable on inspection.
  Pre-registered candidate: the 9 malformed `'["003.001-T"]'` edges.
* **(c) Signal, not noise.** Total findings < ~100. A report flagging hundreds of
  items is triage burden, not determinism.
* **(d) PROSPECTIVE — the half that can actually fail.** Over the next **≥3**
  Stage harvest cycles, the gate must fire **at least once on newly-created
  structure, before it ships**.

> **Honesty note on (a)–(c): these are already satisfied by this session's
> prototype**, which weakens them as tests. **(d) is the real test**, and it is
> capable of failing. If three consecutive harvests produce zero findings, the
> defect class is **historical**, the gate is not earning its place in the
> pipeline, and it should be demoted from a gate to an occasional hygiene command
> — and the broader program's near-term ranking should be re-derived from C6/C8
> instead.

**FALSIFIED if:** the findings are purely historical artifacts of early-harness
churn with no bearing on current behaviour; **or** `UNDECLARED_SHIPMENT_ORDERING`
does not correlate with any recorded defect (meaning the numeric convention is a
*sufficient* substitute and the missing edges cost nothing); **or** the findings
require operator judgment on every single one (meaning the graph adds triage
burden rather than removing choice).

---

### 9. Anti-patterns and failure modes

* **A1 — The written-but-unread graph (F5).** The measured, present condition:
  452 task edges with no reader. Any new edge family repeats this unless Law 2 is
  enforced. **Mitigation: C6 detects it mechanically.**
* **A2 — Conflating acyclicity with termination.** The `028-DL` result. Never
  claim D4 from a graph.
* **A3 — Ready-set without a total order.** A ready-set of size >1 hands the
  agent a *choice*, which is the nondeterminism the program exists to remove.
  Every ready-set must ship with a tie-break; imitate `compute_next_eligible`.
* **A4 — Coverage proofs over open node sets.** A reachability proof is only
  valid over a closed subgraph. Every D3 claim must state its closure boundary or
  it is a lie dressed as a proof.
* **A5 — Eroding the scheduler non-goal by accident.** `dag-readiness` declares
  no-scheduler / no-parallel-execution a **permanent** non-goal (P-001/P-016).
  **This deliberation takes option (a): steering comes from constraining choice,
  not from scheduling — the non-goal is respected and does not need revisiting.**
  The line to hold: an analyzer may narrow the legal next action **to one**; it
  may never dispatch work, permit a second active shipment, or authorize a second
  worktree. Any future proposal that wants concurrency must be raised
  **explicitly** as a non-goal revision under operator authority, never smuggled
  in as an optimization.
* **A6 — False precision (the cargo-cult trap).** C7 is the worked example: a
  structure that *looks* checkable and proves nothing is worse than prose,
  because it transfers unearned confidence.
* **A7 — Persisting derived graphs.** Violates Law 1 and walks straight back into
  `028-DL` §2.2's disposable-cache data-loss architecture.
* **A8 — Inventing node identity.** Every KEEP candidate uses externally-supplied
  identity. The moment a proposal needs to *invent* stable IDs (as the
  reasoning-state graph does), it inherits the blocker that has defeated that
  entry across five sessions. **Treat "must I invent identity?" as the primary
  triage question for any future candidate.**
* **A9 — Blocking before measuring.** Every candidate here starts report-only. A
  graph that blocks before its finding classes are validated converts a modelling
  error into a work stoppage.

---

### 10. Open questions requiring operator authority

* **Q1 — Ratify the two architectural laws?** *Derive, never persist* and *no
  graph without a reader; no reader without a binding* are policy-shaped
  commitments. Code written under C12/C13 will assume them. Recommend explicit
  ratification before implementation, not after.
* **Q2 — May any of these gates ever block?** All are report-only as proposed.
  Promotion of `UNDECLARED_SHIPMENT_ORDERING` or C8's evidence-resolution to
  fail-closed is authority-expanding and must be separate. **Note the asymmetry:
  C8 blocking would strengthen P-014/P-018/P-020, which already fail closed —
  arguably the least controversial promotion of the set.**
* **Q3 — Is C1 (Plan-as-DAG) worth its agent-contract blast radius?** Highest
  determinism yield of any candidate; highest prose cost. This is a genuine
  trade-off and it is the operator's call, not Stage's.
* **Q4 — Should the numeric-ID shipment convention be retired or ratified?** It
  is currently load-bearing (~124/149 shipments) and undeclared. Two options:
  **(i)** materialize the implied edges and delete `_prior_shipment_id` entirely;
  or **(ii)** ratify the convention explicitly and validate conformance. Option
  (i) removes a heuristic that has produced two defects; option (ii) is cheaper.
  **Recommend (i)**, informed by the first slice's findings.
* **Q5 — Does `34AAF1C7` now need splitting?** `028-DL` Q4 already raised this.
  This deliberation adds a third strand. Recommended split: **(a)** PR-review
  convergence [028-DL, executable]; **(b)** reasoning-state identity [still
  blocked by A8]; **(c)** DAG-as-steering program [029-DL, this document].
  **Not executed** — splitting a living tracker is an operator-visible
  reclassification.

---

### 11. Honest assessment: was "DAG is diagnostic only" too narrow?

**Yes — in three specific respects, and sound in a fourth.**

1. **Scope of the claim.** `028-DL` answered "can a DAG prove convergence of an
   externally-regenerated finding set?" It answered correctly: **no**. The claim
   that generalized beyond that question — that the DAG is *a* diagnostic layer —
   is true *for that graph* and false as a statement about DAGs in this harness.
2. **Property selection.** It tested the DAG against **D4 (termination)**, the one
   property of six that a DAG provably cannot deliver. D2, D3, and D6 were never
   evaluated. This is the quantifier error: a valid negative result about the
   weakest use case was carried over to the strongest ones.
3. **Node-set assumption.** Its central premise — *"the node set is not fixed"* —
   is **true for review findings and false almost everywhere else.** Plan units are
   closed at plan-review. Shipment manifests are closed at assembly. Pack
   composition is closed at install. Over those closed sets, D3 is available as
   genuine proof.
4. **Where it was exactly right, and remains binding.** Its Option B rejection —
   *do not extend the work-item DAG with runtime evidence semantics* — is correct
   and is **preserved and generalized** here as the typed-edge-families rule (§6).
   Its §2.2 disposable-cache warning is correct and is **answered structurally**
   by Law 1 rather than argued around. And its insistence on externally-supplied
   node identity is elevated here into A8, a primary triage question.

**Net:** `028-DL` is not overturned. It is **re-scoped from a general verdict on
DAGs to a specific and correct verdict about open-node-set convergence graphs**,
and its own architectural rules are carried forward and strengthened rather than
discarded. The operator's pushback was correct: the conclusion was being
over-generalized, and the over-generalization was costing this workspace a
measurable amount of determinism it could already have had.

---

### 12. Stage gate conclusion and disposition

**Deliberation-only this session — by choice, and stated plainly.**

No `impl-plan`, no `plan-harden`, no `plan-review`, no `harvest`, no shipment.
This is **not** a deferral, and it is **not** conservatism:

* The recommended first slice (§8) is **genuinely ready to plan**. Its
  requirements are precise, its prior art in-repo is exact (`dag-readiness`), its
  data exists, its blast radius is low, it needs **zero new authority**, and its
  single open unknown (manifest format drift) was **closed during this session**.
  It is more ready than most work this agent harvests.
* It is nevertheless **not harvested**, for two reasons that are about correctness,
  not caution: **(i)** the deliverable the operator asked for is a ranked
  opportunity map intended to *inform an operator choice* among candidates that
  commit engineering capacity across a multi-phase program — harvesting one
  pre-empts that choice; and **(ii)** Q1's two architectural laws are
  policy-shaped and would be **assumed by the code**, so they should be ratified
  before implementation, not retrofitted.

**One word from the operator moves this to plan.** The scope is written; §8 is
plan-ready as-is.

Stash `34AAF1C7` remains **ACTIVE at MEDIUM priority**, annotated with this
deliberation and **not archived**. Its frame is now three-stranded (Q5).

---
---

## ADDENDUM — Pushback Round 1 (2026-08-25, Orchestrator adversarial review)

Eight adversarial positions were put to this deliberation. **Five are adopted,
one is adopted with a material precision, one is refuted with data, and one
reverses this document's own #1 recommendation.** New measurements were taken to
settle three of them empirically. §A6 below is the most important result in this
document.

### A0. The manufactured gate — WITHDRAWN

**Position:** *do not produce a fifth deferral.*

**Adopted, and I over-gated.** §12 made implementation contingent on operator
ratification of the two architectural laws (Q1). That was a **manufactured
gate**. Both laws are *reversible design defaults* for a **report-only** slice
that persists nothing; if the operator later disagrees, the cost of reversal is
approximately zero. A precondition whose violation costs nothing is not a
precondition.

> **Q1 is withdrawn as a blocker.** It is downgraded to a design note. The only
> genuine operator decision remaining is **§A3's enforcement level**, and even
> that has a default that needs no consent.

### A1. Does the termination objection transfer? — CONFIRMED, with one precision that matters

**Position:** an impl-plan task graph is a closed, finite, fixed node set;
acyclicity + finiteness *does* imply termination there; topological order +
tie-break *does* imply a reproducible sequence. `028-DL` was over-generalized.

**Confirmed.** But one precision changes how the two deliberations relate:

> Acyclicity + finiteness gives termination of the **traversal**, not of the
> **work**. `028-DL`'s non-termination occurs **inside a node** — the review loop
> attached to a shipment — not between nodes. A finite acyclic plan graph whose
> node #3 contains an unbounded review cycle still does not terminate.

So the DAG bounds the **outer** loop; `028-DL`'s monotone measure bounds the
**inner** loop. **The two results compose rather than compete** — which is the
correct relationship and neither document had stated it.

Second precision on "reproducible sequence": topological order + tie-break gives
a reproducible **sequence of node selections**, *conditional on a frozen graph*.
The plan graph is authored by an LLM, so the graph itself varies run to run.
**Freezing the graph as an artifact is what makes the order reproducible** — which
is precisely §A6's thesis.

#### A1.1 The closed/open partition

| Surface | Node set | Closed at |
|---|---|---|
| impl-plan implementation units | **CLOSED** | plan-review |
| Acceptance criteria within a plan | **CLOSED** | plan-review |
| Harvested task set under a feature | **CLOSED** | harvest |
| Shipment manifest items | **CLOSED** | shipment assembly |
| Capability-pack / layer / template composition | **CLOSED (fully static)** | install |
| Policy set P-001..P-021 | **CLOSED (static file)** | — |
| File cross-reference graph | **CLOSED** | commit |
| Agent Required Steps | **CLOSED (static contract)** | — |
| Gate set | **CLOSED (static)** | — |
| PR review findings | **OPEN** (external oracle) | never — `028-DL`'s case |
| CI failures | **OPEN** | never |
| Deferred scope expansions (P-021 C2) | **OPEN** | never |
| Operator interjections / new stash entries | **OPEN** | never |

**Nine closed surfaces, four open ones.** `028-DL` generalized from the open
minority to the whole harness.

#### A1.2 Bonus finding — P-021 is a closed-world-preservation policy

**P-021 (Bounded Fix-Cycle Scope Containment and Deferred Expansion Capture)
exists precisely to keep the active node set closed.** Its C2 capture routes
newly discovered work to the **stash** rather than into the running shipment,
so the executing graph stays fixed. The harness therefore *already has* a
closed-world maintenance mechanism — it has simply never been described in graph
terms. Any future graph work over the shipment surface should cite P-021 as its
closure guarantee rather than inventing one.

### A2. Steering vs scheduling — ADOPTED, and the precedent is stronger than stated

**Position:** P-001/P-016 forbid *parallel execution*, not *deterministic
selection of the single next action*.

**Adopted; argued, not assumed.** P-001 (single-release-unit completion) and
P-016 (no parallel branch/worktree) both constrain the **cardinality of
concurrent execution contexts**. Choice elimination reduces `|ready_set|` toward
1 **for a single worker**; the count of active contexts stays exactly 1.
**The two are orthogonal**, and `compute_next_eligible` is the shipped existence
proof.

**And the precedent is materially stronger than the pushback claimed:**

> `pipeline-topology` is **already a fail-closed gate over the shipment
> dependency graph** — it blocks a claim on `PREDECESSOR_NOT_SHIPPED`. Fail-closed
> *graph enforcement* is therefore not merely "not unprecedented" here; **it is
> the current production state.**

The `dag-readiness` non-goal ("visibility/reporting only") binds **that gate's own
contract**, not the category. A different gate may be fail-closed, because one
already is.

### A3. Enforcement — CONFRONTED, with a principle that dissolves most of the objection

**Position:** only level (c), enforced, is genuinely steering; stop deferring it.

**Adopted.** The maturity ladder is right, and §A6's evidence shows level (a) is
worse than "near-zero value" — it is **negative**, because it decays while
projecting rigor. Proposing the concrete gate now:

> **AUTHORITY TEST.** *An enforced gate is authority-expanding **iff** it creates
> an obligation that did not previously exist in policy. A gate that mechanically
> checks an obligation **already stated** in policy is not authority expansion —
> it is the removal of unreliable enforcement.*

| Candidate enforced gate | Pre-existing obligation | Authority-expanding? |
|---|---|---|
| Reject harvest output with cycles / orphan tasks / dangling edges / uncovered tasks | **P-003 decomposition chain integrity** | **NO** |
| Reject closure whose evidence references do not resolve | **P-014 / P-018 / P-020** already require evidence | **NO** |
| Reject a claim of any shipment other than `next_eligible` | *no policy states this* | **YES — needs consent** |

**Smallest safe enforced gate — the recommendation:**

> **Fail-closed structural validation of Stage's own harvest output, at creation
> time.** It gates an *artifact's validity at the moment of authoring*, exactly as
> P-008 markdown conformance already does. It has **zero runtime effect**, adds
> **zero new obligations**, governs **no agent reasoning**, schedules nothing, and
> lies entirely within **Stage's own authority over its own output**. It prevents
> malformed structure from *entering* the graph rather than detecting it later.

That gate needs **no operator consent** under the authority test. Only row 3 —
constraining which work is taken next — does, and it is explicitly **not**
proposed here.

### A4. Are tie-breaks the bottleneck? — REFUTED, and the refutation reverses my own claim

**Position:** determinism may be bottlenecked on missing tie-break rules rather
than missing graph structure.

**Refuted — but the truth is more interesting than either of us proposed, and it
falsifies this document's own #1 rationale.**

Measured **order determinacy** over the 149-shipment graph (fraction of the
11,026 shipment pairs whose relative order the graph actually determines):

| Graph | Edges | Ordered pairs determined | % |
|---|---|---|---|
| Declared shipment edges only | 26 | 38 / 11,026 | **0.34%** |
| Declared **+ lifted task edges** (this document's C13) | 49 | 61 / 11,026 | **0.55%** |
| **Numeric-ID convention** | — | **11,026 / 11,026** | **100%** |

And: **0 of 63** cross-shipment task edges ever contradicted the numeric order.

Three consequences, stated plainly:

1. **Tie-breaks are not missing. They are already doing ~100% of the work.** The
   numeric-ID convention is a *complete total order* that has never once been
   observed wrong. `queue_position` is unused (1/149) because it is *redundant*.
2. **C13's edge lift raises order determinacy from 0.34% to 0.55%.** It resolves
   23 pairs out of 11,026. **It is not a determinism engine.**
3. **Therefore the DAG's job on this surface is not to *produce* the order — it is
   to *validate* a cheap order that is already deterministic.** That is a smaller,
   cheaper, and far more defensible program than the one §5 ranked #1.

> **Self-falsification, recorded:** §5 ranked C13 first and credited it with **D2
> (choice elimination)**. That credit is **withdrawn**. C13's real value is **D6
> (auditability)** plus a **bug fix** — letting `pipeline-topology` stop guessing
> with `_prior_shipment_id`, whose adjacency heuristic (*not* the numeric
> convention itself) produced the two recorded defects. Worth doing. **Not worth
> ranking first.**

### A5. The two untouched levers

#### A5a. Coverage as reachability — ADOPTED and promoted to #1 (see §A7)

Measured, and the numbers are decisive:

| Coverage surface | State |
|---|---|
| Tasks with a delimited `acceptance-criteria` block | **166 / 612 (27%)** |
| Tasks with *numbered* `ACn` identities | **4 / 612** — `115.001–003-T`, `135.001-T` |
| Plans using stable `R#` requirement IDs | 18 / 71 (25%) — *the brainstorm skill already mandates them and forbids renumbering* |
| Terminal shipments with a closure artifact | 45 / 148 |
| Closure `evidence:` references that resolve | task IDs **3/3**, commit SHAs **2/2** — *they do resolve; they are simply embedded in prose strings rather than typed fields* |

**Requirement identity is 2/3 solved already.** `R#` exists at brainstorm and
survives into 25% of plans; backlog task IDs exist universally. **The only missing
link in the whole `R# → unit → task → evidence → closure` chain is the plan-unit
ID** — which is exactly C1's fix, and it is one identifier, not a scheme.

#### A5b. Memoization — PRUNE DEFENDED for the strong form, CONCEDED for the weak form

The strong form (skip work when the input hash matches) stays pruned: agent nodes
are non-hermetic, outputs are not content-addressable, the executor is stochastic.
Nothing measured changes that.

**But I under-valued the weak form and §5 was wrong to file it as a carve-out.**
Input-hash **staleness detection** is not caching, and it does something no other
mechanism here does:

> **A reachability proof is a statement about a moment.** "Every acceptance
> criterion is covered by a task" computed at plan-review is **void** if the plan
> changed afterwards. **Input hashing is the mechanism that makes coverage proofs
> durable rather than momentary.** Without it, every D3 proof in this document
> silently expires.

Invalidation is therefore **promoted from carve-out to a first-class mechanism**:
it is the precondition for trusting *any* of the other graph properties over time.
Precedent already exists and is proven — `gate_evidence.head_sha`,
`copilot_review`'s HEAD-pinning.

### A6. The central thesis — CONFIRMED, and it now dominates

**Thesis:** *the pipeline is already a DAG, encoded in prose, re-derived by a
stochastic reader every session; the deficit is re-derivation variance, so the
program is extraction, not construction.*

**Confirmed, on four independent pieces of evidence — and the fourth is the most
important result in this document.**

1. **The harness contains both a coded and a prose phase machine.** The supervisor's
   lifecycle (`init → locking → bootstrapping → preflight → resolving → launching →
   running → draining → exited/cancelled`) is **implemented in code and journaled**
   — `.autoharness/sessions/*/journal.jsonl` records `SessionPhaseChanged` events
   across 11 distinct transitions. The **agent Required Steps** graph — the one that
   actually governs work — is **prose only**. Same repository, same authors: where
   the graph was coded it is deterministic and observable; where it was left in
   prose it is not.
2. **P-005 is proof of re-derivation failure.** A policy exists whose sole purpose
   is to record *skipped mandatory steps* as violations. **You do not need violation
   telemetry for a mechanically enforced sequence.** P-005's existence is a standing
   admission that the step graph is unreliably re-derived.
3. **Re-derivation variance is directly measurable in the checkpoint record.**
   `phase` is a free string, and across sessions it holds **27 distinct ad-hoc
   values** — `stage/complete`, `stage/review-fix`, `stage/cycle-23-validation`,
   `stage/authority-audit-readiness-blocked`, `ship/task2-done-task3-pending`… The
   same graph is re-invented with fresh vocabulary nearly every session. That is
   re-derivation variance, quantified.
4. **THE NATURAL EXPERIMENT — a controlled comparison inside one repository.**

> Two structurally identical prose conventions, same repo, same authors, same
> period. One acquired a mechanical reader; the other did not.
>
> | Convention | Reader | Adoption trajectory by band |
> |---|---|---|
> | **Closure artifact** | **YES** — `pipeline-topology._closure_artifact_complete`, gated by P-014/P-015 | 0% → 0% → 0% → 0% → 20% → 80% → 47% → **100%** |
> | **`acceptance-criteria` block** | **NONE** | 0% → 0% → 26% → 43% → 46% → 38% → 39% → **0%** |
>
> **The convention with a reader converged to 100%. The convention without a
> reader rose to 46% and collapsed to zero.**

This is empirical proof of **Law 2**, of the **F5** failure mode, and of the
extraction thesis in a single observation. It also upgrades the pushback's own
level-(a) assessment: an emitted-but-unread graph is not merely low value, it is
**negative** — it decays toward zero while projecting rigor, and it decays
*silently*, because nothing is watching.

**Consequence for the architecture:** §6's two laws survive, but their priority
inverts. **Law 2 (no graph without a reader) is not a hygiene rule — it is the
load-bearing finding.** Law 1 (derive, never persist) is merely the cheapest way
to satisfy it.

### A7. The competing first slice — the pushback's candidate WINS

**Direct answer: the plan-graph structural linter beats this document's
`backlog-graph-integrity`, and the data says so unambiguously.**

| | This doc's C12/C13 (ordering) | Pushback's candidate (coverage) |
|---|---|---|
| Target | shipment ordering integrity | requirement/task/evidence coverage |
| Measured gap | order already **100% determined**, **never observed wrong** | **73%** of tasks have no AC block; convention **decayed 46%→0%** |
| Determinism yield | **0.34% → 0.55%** order determinacy | closes a 73% coverage hole |
| Honest verdict | a **bug fix** worth doing | **the actual determinism program** |

**I concede the ranking.** §5 ranked ordering first because ordering *looked* like
the DAG-shaped problem. Measurement says ordering is solved by a convention and
coverage is not solved at all.

**Two corrections to the pushback's candidate, from measurement:**

* *"Acceptance criteria with no covering task"* is **not computable at criterion
  granularity today** — only **4 of 612** tasks carry numbered `ACn` IDs. That
  specific check requires C1's plan-unit identity first. It is the *right target*,
  reached in two steps rather than one.
* *"Leaves that never reach a closure/evidence node"* **is** computable — better
  than my own probe suggested. Closure `evidence:` fields carry **task IDs and
  commit SHAs that resolve** (3/3 and 2/2); they are merely embedded in prose
  strings rather than typed fields.

#### A7.1 Something sharper than either — the CONVENTION-DECAY DETECTOR

§A6's natural experiment generalizes into a check neither candidate proposed:

> **Measure the adoption trajectory of every structured convention in the
> workspace (delimited sections, frontmatter fields, ID schemes), and flag any
> convention whose adoption is *declining*.**

* It is **Law 2 made mechanical**: a declining convention is, by the natural
  experiment, a convention with no reader.
* It is **self-applying** — it tells you *which structure to build a reader for
  next*, rather than requiring that judgment up front.
* It is **fully retrospective**, needs no new authority, no backlogit change, and
  no new node identity — it counts existing artifacts.
* It would have caught the acceptance-criteria collapse **four feature-bands
  before it reached zero**.
* And it is **falsifiable in the strongest way**: it makes a *prediction*. Any
  convention it flags as declining must, on inspection, have no mechanical
  reader. A declining convention that *does* have a reader refutes Law 2 outright.

#### A7.2 Revised FIRST SLICE

**`autoharness gate coverage-integrity` — read-only, report-only, exit 0 in v0**,
merging the computable parts of both candidates plus the decay detector:

| Class | Computable today | Measured |
|---|---|---|
| `TASK_WITHOUT_ACCEPTANCE_CRITERIA` | yes | **446 / 612** |
| `CONVENTION_DECAY` (adoption trend declining) | yes | AC block **46% → 0%** |
| `SHIPMENT_WITHOUT_CLOSURE` | yes | 103 / 148 (banded: recent = 0) |
| `UNRESOLVED_EVIDENCE_REF` | yes | 0 today — *a clean baseline worth locking in* |
| `ORPHAN_TASK` / `UNCOVERED_TASK` / `CYCLE` / `MALFORMED_EDGE` | yes | 3 / 11 / 0 / 9 |
| `UNDECLARED_SHIPMENT_ORDERING` (demoted from C13) | yes | 21 — *retained as a bug-fix input, not a determinism claim* |
| `AC_WITHOUT_COVERING_TASK` | **NO — needs C1** | 4/612 have AC IDs |

**Then, immediately after and gated on nothing:** promote it to the **fail-closed
harvest-output gate** of §A3, which under the authority test needs no consent.

**Falsification test, revised and strengthened.** The former test's parts (a)–(c)
were already satisfied by the prototype and were therefore weak. The natural
experiment supplies a genuinely refutable one:

> **Law 2 is FALSIFIED if the decay detector flags a declining convention that
> *does* have a mechanical reader**, or if a convention *without* a reader is
> found to be **stable or rising** across ≥4 bands. Either observation breaks the
> reader⇒adoption link that this entire program now rests on.
>
> The **coverage thesis is FALSIFIED** if `TASK_WITHOUT_ACCEPTANCE_CRITERIA` turns
> out to be concentrated in tasks that were nonetheless *verifiably* completed with
> no defect attributable to missing criteria — i.e. if the 73% gap is **cosmetic**.
> Pre-registered probe: sample 20 of the 446 and check whether their shipments
> incurred review findings at a higher rate than the 166 with criteria. **No
> difference ⇒ the coverage hole is not costing anything ⇒ this program should be
> closed, not staged.**

### A8. Symmetric pruning — one addition

Prunes from §4 stand (quality-gate DAG, policy-interaction DAG, memoization's
strong form). **One prune is added against this document itself:** C13's claim to
**D2/choice elimination** is pruned as cargo-cult — it dressed a 0.21-percentage-
point ordering gain in determinism language. C13 survives **only** as a bug fix
and an auditability check (§A4).

Skepticism has not been used to recommend nothing: §A3 proposes a **concrete
fail-closed gate** requiring **no operator consent**, and §A7.2 names a single
revised #1 with a refutable prediction.

### A9. Revised disposition

* **Q1 (ratify the laws) — WITHDRAWN** as a gate (§A0). Law 2 is now evidence, not
  a proposal.
* **Q4 — ANSWERED by measurement.** Do **not** retire the numeric-ID convention. It
  delivers 100% order determinacy and has never been wrong. **Retire
  `_prior_shipment_id`'s *adjacency heuristic* instead** — that, not the
  convention, is what produced both defects.
* **Q2 — narrowed.** The harvest-output gate needs **no consent** under §A3's
  authority test. Only "you must claim `next_eligible`" would, and it is **not
  proposed**.
* **Q3 (plan-as-DAG) — now sequenced, not optional.** It owns the one missing
  identifier (plan-unit ID) blocking `AC_WITHOUT_COVERING_TASK`, the strongest
  coverage check. It becomes **phase 2**, not a parallel option.
* **Q5 (split `34AAF1C7`) — unchanged**, operator-visible reclassification.

**Revised gate conclusion:** the revised first slice (§A7.2) is **ready for
impl-plan now, with no ratification precondition**. This addendum changed the #1
recommendation on evidence, so `impl-plan` should run against §A7.2 rather than
§8 — but nothing further blocks it.


---

## ADDENDUM — Pushback Round 2 (Orchestrator adversarial review)

**Outcome: the round-1 #1 is withdrawn.** Position 1 was correct that my Law 2
evidence did not rule out the teeth hypothesis. I ran the experiment that
separates the variables. It refutes Law 2 as I stated it, and it also refutes
the round-1 slice. A new #1 follows from the corrected law.

### B1 — Law 2 REFUTED as stated. The variable is not readership.

The objection was that "has a reader" and "has a reader with teeth" were
perfectly collinear at n=2. Correct. So I found the cell that separates them.

`gate size` self-describes in code (`cli.py` L516-519):

> "Fail open by default: the sizing gate is **advisory and must never block**
> task execution."

And shipment `dependencies:` is read by `dag-readiness` (report-only by
declaration) **and** by `pipeline-topology` — but `_prior_shipment_id`
(`topology.py` L1433-1465) **falls back to numeric adjacency when no dependency
is declared**. The blocking gate reads the convention and *silently compensates
for its absence*.

That yields a paired comparison with the confound removed:

#### The isolating experiment — same gate, same corpus, same period

| Shipment band | **Closure artifact** (absence **blocks**) | **`dependencies:`** (absence **silently compensated**) |
|---|---|---|
| 1–22 | 0% | 0% |
| 23–50 | 0% | 0% |
| 51–72 | 0% | 0% |
| 73–94 | 9% | 0% |
| 95–116 | 68% | 18% |
| 117–138 | 91% | 59% |
| **139–155** | **100%** | **41%** |

Both conventions are read by **`pipeline-topology`**. Both were introduced in
the same band. Same authors, same period, same corpus. The **only** difference
is whether absence is penalized.

Mature bands (117-S+, n=39): closure present 37/39, `dependencies:` present
20/39. **Fisher exact two-sided p = 1.97e-05.**

**Readership is not the variable.** The Orchestrator is right.

### B1.1 — But the corrected law has TWO durable mechanisms, not one

The teeth hypothesis says "penalize absence." That is one durable cell. The data
show a second, and `gate size` is the proof:

| Convention | Mechanism | Trajectory |
|---|---|---|
| Closure artifact | machine **penalizes absence** | 0 → 68 → 91 → **100%** |
| `size` / `complexity` | machine **produces the value** (advisory, fail-open) | 0 → 48 → **100 → 100%** |
| `dependencies:` | machine reads, **tolerates absence** | 0 → 18 → 59 → **41%** |
| `acceptance-criteria` block | **no reader** | 0 → 22 → 62 → 52 → **15%** |

> **LAW 2 (CORRECTED): a convention survives iff a machine either PRODUCES it or
> PENALIZES ITS ABSENCE. Being read is neither necessary nor sufficient.**

`gate size` is the decisive counterexample to a pure teeth reading: it is
advisory, fail-open, and explicitly forbidden from blocking — and its convention
is at **100%**, because `sizing.py` L343 writes the field itself
(`backlogit update <task> --size <result>`).

**This is the escape route the teeth framing does not see.** Durability does not
require enforcement authority. It requires that a machine, not a stochastic
author, be the producer. Generation is as durable as enforcement and needs
**no consent at all**.

*Caveat stated plainly:* `size`/`complexity` are young (introduced band 4, ~3
bands of life). The AC block also looked healthy at band 3 (62%) before
collapsing. The 100% is consistent with the generation mechanism but not yet
proof of it over a long horizon.

### B1.2 — Consequence: the round-1 slice would have rotted

`autoharness gate coverage-integrity` as specified in §A7.2 is **report-only** —
cell 3, the `dependencies:` cell, the one that decayed. **The objection lands.
I withdraw it.**

**But the escape is not "add teeth."** A report-only gate rots when it depends on
authors maintaining a **per-artifact convention**. A gate that (a) reads only
data that *already exists* and (b) is consumed at a decision point rather than
maintained per artifact has **no per-artifact convention to decay**. That
distinction is what the new #1 is built on, and it is testable rather than
asserted.

### B2 — ADOPTED. The authority test needs an activation-blast-radius dimension.

Correct, and I measured the gap without connecting it. De jure / de facto is a
real distinction:

> **AUTHORITY TEST v2.** A gate requires operator consent if EITHER (1) it
> creates an obligation not already in policy, OR (2) its activation blast
> radius against the current corpus exceeds a stated threshold — even for a
> pre-existing obligation.

**Migration story, which the data hands me:** the phase-2 gate validates
**Stage's own harvest output at creation time**. It only ever sees items created
after activation. It is therefore **intrinsically enforce-on-new-only** — day-one
blast radius against the 612 existing tasks is **exactly zero**, with no
grandfathering clause to author, because the gate has no reach into history.

Sequencing that actually works, given 73%:
1. **Generate** the missing structure (B4 below) so new items are compliant by construction.
2. **Warn** on new items; publish adoption on new-items-only.
3. **Block** only once new-item adoption is sustained ≥90% across ≥2 bands — with the decay classifier as the readiness signal.

Absent step 1, step 3 is undeployable. The Orchestrator is right that this was missing.

### B3 — CONCEDED: the falsifier is NOT computable. Replaced, and the replacement reads null.

`copilot_review.py` operates on PR-level `reviewThreads`, storing thread IDs and
`isResolved` (L81, L297-314). **There is no per-task attribution of review
findings anywhere in the corpus.** The falsifier as written is not refinable — it
is not computable. Conceded.

**Replacement (fully local, controlled, computable).** `docs/compound/` holds 76
records **named by shipment ID** (`093-S-review-loop-convergence.md`) — a
shipment-attributed, locally recorded outcome signal.

* Unit: shipment (the finest granularity at which outcomes are actually attributed)
* Predictor: fraction of that shipment's tasks carrying an AC block
* Outcome: compound records attributed to that shipment
* Controls: task count, and `size` (now on 100% of mature-band tasks)
* Stratum: 117-S+ where both conventions are mature

**Computed now — 58 mature shipments:**

| Group | n | mean tasks | mean compound records |
|---|---|---|---|
| AC-rich (≥50% tasks with criteria) | 20 | 5.2 | **0.20** |
| AC-poor (<50%) | 38 | 4.7 | **0.18** |

Task counts are near-matched, so the size confound is small on this stratum.
**The result is null.** And it is **underpowered**: at a base rate of 0.2
records/shipment with n=20/38, only an enormous effect is detectable.

**Honest consequence: the coverage thesis has no supporting outcome evidence,
and the best available local test cannot supply any.** That is a second,
independent reason to demote it — on top of B1.2.

### B4 — B1 + B3 together produce a new #1

Coverage was round-1's #1 on the strength of a large *structural* gap (73%).
B3 shows that gap has **no measurable outcome consequence**, and B1.2 shows the
proposed instrument would decay. Two independent demotions. **Coverage is no
longer #1.**

The best-evidenced finding in this entire document is now **the durability law
itself** (p≈2e-5, confound isolated). The intervention that follows from it:

#### NEW #1 — `autoharness gate convention-durability` (read-only, retrospective)

Classify **every** structured convention in the corpus into the four durability
cells and **predict** which will decay.

**§4b answered concretely — the enumeration is derived, not curated.** Two
mechanically decidable families, zero judgment calls:

* **48 distinct frontmatter keys** (`updated_at` 956 … `queue_position` 1, `covering_feature_id` 1)
* **18 distinct delimited body blocks** (`description` 201, `acceptance-criteria` 169 … `hardening` 1, `acceptance` 1)
* **= 66 conventions**, machine-enumerable with no "what counts as a convention" judgment. The objection is answered on the merits: it is not a spreadsheet and no one owns the list, because the list is *computed*.

The long tail is the payload, not noise. It already surfaces a **schism** nobody
had named: `acceptance_criteria` exists as a frontmatter key (3 artifacts)
*alongside* `acceptance-criteria` as a body block (169) — two encodings of one
concept, drifting apart. And `queue_position` (1/149) and `covering_feature_id`
(1/149) are visibly **dead on arrival**.

**Why this one escapes its own law (the B1.2 test):** it maintains no per-artifact
convention. It reads frontmatter and block delimiters that already exist for
other reasons, and it is consumed at investment-decision time, not maintained by
authors. Cell 3 rot requires a per-artifact convention to rot. This has none.

**Why it is not ceremony:** it is a **predictive instrument that has already made
a correct prediction**. Classify by mechanism, and it predicts `dependencies:`
decays while closure converges — which is exactly what happened, at p≈2e-5,
before the classifier was built. It also predicts, right now, that `size` and
`complexity` will hold and that any of the 66 in the read-but-tolerated cell will
plateau below 60%.

**Falsification (sharp, and it can fail):** the classifier is refuted if any
convention in the *produced* or *penalized* cell decays across ≥2 bands, or if
any convention in the *unread* or *tolerated* cell is stable or rising across
≥4 bands. Both are computable today against the existing corpus.

**Authority: none.** Read-only, retrospective, zero corpus impact, no new
obligation, no consent.

#### #2 — AC-ID **generator**, not AC-ID reporter (gated on #1)

If #1 says coverage is worth investment, the instrument is **not** a report. It
is `gate size`'s shape applied to criteria: advisory, fail-open, never blocking —
mechanically assign stable `ACn` IDs to the criteria **already present** in the
169 delimited blocks, and write them back. That moves coverage from cell 3
(rots) to cell 1 (durable), needs no consent, and it is what makes
`AC_WITHOUT_COVERING_TASK` computable at all — answering **§4a**, which I concede
flatly: slice 1 could never have performed its flagship check, and I let the
slice inherit rhetorical weight it had not earned.

### B5 — P-021 reframe: one narrow mechanism, otherwise insight. Labelled.

Fair challenge. Honest answer: **one operational consequence, and it is small.**

Any graph-based coverage or completeness proof must be computed at a point where
P-021 C2 capture has already run. Before that point the node set is still open
and the proof is void. That is a real sequencing constraint on *where* such a
gate may execute.

Beyond that sequencing constraint, **it is a description, not a mechanism.** It
is hereby labelled **INSIGHT**, not architecture, and must not accrete further
weight.

### B6 — Revised disposition

* **Round-1 #1 (`coverage-integrity`) — WITHDRAWN** on two independent grounds (B1.2 decay, B3 null outcome).
* **NEW #1 — `gate convention-durability`**, read-only, retrospective, zero authority, already-validated prediction, sharp falsifier.
* **#2 — AC-ID generator** (cell-1 shape), gated on #1.
* **Law 2 — CORRECTED**: produce or penalize. Readership is neither necessary nor sufficient.
* **Authority test — v2**: obligation novelty **plus** activation blast radius.
* **Phase-2 gate — migration solved**: intrinsically enforce-on-new-only, day-one blast radius zero.
* **P-021 reframe — labelled INSIGHT**, one narrow sequencing mechanism only.

Two rounds, two of my own #1s withdrawn on measurement. Both reversals came from
running the experiment rather than defending the position.


---

## ADDENDUM — Pushback Round 3 (final round)

### C1 — Scope drift: the DAG question is **ANSWERED**, not abandoned or superseded

I pick **answered**, and I will defend it — but only after conceding the charge
is partly correct.

**Conceded:** #1 (`convention-durability`) and #2 (AC-ID generator) are **not
DAGs and do not steer anything**. Both are analytics. That is a real narrowing
and it happened across rounds rather than by decision. Naming it explicitly:

> **HEADLINE FINDING (stated in the words Round 3 asked for): the DAG is not the
> lever. The lever is whether a machine produces the artifact or penalizes its
> absence.**

#### C1.1 — But the durability law does NOT subsume the DAG question

The two are **orthogonal axes**, and conflating them would be a second drift in
the opposite direction:

* The **durability law** governs whether a representation *persists*.
* A **DAG** governs what you can *compute and prove* once a representation exists.

The law is a **filter on which graphs can exist**, not a replacement for graphs.
It answers "what will survive being represented," never "what is worth
representing." A graph that survives still has to earn its keep; a graph that
cannot survive never gets the chance.

#### C1.2 — The nine closed surfaces, with the durability filter applied

Round 3 asked precisely which survive. The discriminator is **where node
identity comes from**:

| Closed surface | Node identity source | Verdict under the law |
|---|---|---|
| Shipment manifest graph | `items:` **149/149**, machine-written by `add_to_shipment` | **SURVIVES** — produced |
| Decomposition chain (P-003) | `parent_id` **630**, machine-set at create | **SURVIVES** — produced |
| Gate set | enumerable from source; not a convention at all | **SURVIVES** — no decay surface |
| Policy set | enumerable from the policy registry file | **SURVIVES**, low yield |
| File cross-reference graph | extracted from links/`references:` that exist for other reasons | **SURVIVES** — derived, but see C1.3 |
| Pack/layer/template composition | `install_layers`, hand-maintained but **single-file config**, not per-artifact | **SURVIVES with caveat** — different decay profile |
| Agent Required Steps | prose in templates; runtime cursor is the free-string `phase` (**27 ad-hoc values**) | **CONDITIONAL** — needs a generator |
| Impl-plan units | requires new `R#` identity — **18/71** | **DIES** unless generated |
| Acceptance criteria | requires new `ACn` identity — **4/612** | **DIES** unless generated |

**Seven of nine survive.** The DAG program is not dissolved — it is *filtered*,
and the two that die are precisely the two that round 2 had promoted. That is
the answer to "does the law dissolve them too": **it dissolves exactly the ones
that require authors to mint new identifiers, and no others.**

#### C1.3 — I tested whether a DAG-shaped candidate beats my non-DAG #1. It lost, on data.

The fairest challenger was the **cross-reference integrity graph** (C6): a
genuine DAG, derived from existing data, zero authority, retrospective — it
passes every filter. So rather than argue it, I measured its defect rate.

**Result: 400 markdown links across `docs/`, `.github/`, `templates/`,
`AGENTS.md`, `README.md`; 343 resolve to local files; DANGLING = 4 (1.2%) — and
all four are documentation placeholders** (`url`, `path`, `../instructions/foo.md`
inside `markdown.instructions.md.tmpl`, `doc-review`, and `harness-doctor`
templates). **Real defect rate: 0%.**

The backlog `references:` field shows 131 unresolved entries across 309
artifacts, but spot-checking confirms these are **historical link rot on
archived/done artifacts** (`templates/agents/ship.agent.md.tmpl` →
`_ship.agent.md.tmpl`, a rename), not live integrity failures.

**A gate with a 0% defect rate is ceremony.** C6 is hereby pruned on
measurement, not on argument — which is the standard I demanded of myself in §8
and had not previously applied to a DAG candidate.

**Net answer to §1: the question was answered. The answer is a partition plus a
precondition, the headline is the durability law, and the document is retitled
accordingly.**

### C2 — The produced cell: n is not 1, but the cell #2 needs **is**

Round 3 is right that I buried this. Splitting the cell resolves it:

| Sub-cell | Producer | Members | Adoption | Span |
|---|---|---|---|---|
| **Store-produced** | backlogit itself (create/update/archive/ship) | `id`, `artifact_type`, `created_at`, `updated_at`, `status`, `title` (**956/956**), `items` (**149/149**), `parent_id` (630), `commit` (553), `archived_from` (559), `source_stash_*` | 100% where applicable | **full 4-month corpus, zero observed decay** |
| **Gate-produced** | an external advisory gate writes back | **`size` only** | 0→48→100→100% | **~3 bands** |

So: **n ≈ 10 for the mechanism class, n = 1 for the specific pattern #2 needs.**

> **#2 is a bet on a pattern replicated ONCE (~3 bands), inside a mechanism class
> replicated ~10 times across the entire corpus with zero observed decay.**

That is the honest framing — stronger than "n=1," weaker than "well replicated."

**Adopted: #1 is now a formal prerequisite for #2, not a loose ordering.** The
durability report must emit produced-cell membership and trend, **split by
store-produced vs gate-produced**, so #2's bet is evaluated against measured
gate-produced durability rather than assumed.

### C3 — The underpowered null is downgraded

Adopted without reservation. An underpowered null cannot distinguish *no effect*
from *insufficient power*.

> **CORRECTION to §B3.** The shipment-level coverage test (AC-rich 0.20 vs
> AC-poor 0.18 compound records, n=20/38, base rate 0.2) is recorded as
> **"no supporting evidence found," NOT as evidence of absence.** It is **not** a
> second independent demotion. Coverage is demoted on **§B1.2 cell placement
> alone**, which is sufficient. Any later reader who treats §B3 as showing
> coverage does not matter is over-reading it.

### C4 — Stage gate conclusion: **1a ready in substance, gate NOT cleared. Criteria named.**

Under the standing authorization I ran my own gates honestly. They do not clear,
and here is exactly why — three measured criteria, not a habit deferral.

#### C4.1 — The #1 slice must split, because it fails its own law

Building the classifier surfaced a genuine self-application failure:

* **Slice 1a — adoption-trend detector.** For each of the **66** conventions, emit
  banded adoption and flag declining ones. **Fully mechanical. Needs no mechanism
  map. READY IN SUBSTANCE.**
* **Slice 1b — cell classifier / predictor.** Requires knowing, per convention,
  whether a machine produces it, penalizes its absence, tolerates its absence, or
  ignores it. **BLOCKED.**

**Why 1b is blocked — measured, not asserted.** I tested whether the
convention→mechanism map is mechanically derivable by grepping autoharness source
for each key. **The proxy fails:** `archived_from` (559 artifacts, unambiguously
machine-written) has **0** references in autoharness source. So do `priority`
(761) and `complexity` (186).

**Because the producer of most conventions lives in a different repository.**
backlogit writes them; its source is out of tree. This is the §7 cross-repo
boundary biting the classifier directly.

So 1b's classification axis would require a **hand-maintained map** — a
per-artifact convention with no producer and no penalty, which **lands in cell 4
and decays by its own law.** Distinguishing "penalizes absence" from "tolerates
absence" is not mechanizable at all: finding it in `_prior_shipment_id` required
reading the fallback logic.

#### C4.2 — The Step-3 planning gate cannot be executed in this workspace

`.github/skills/` contains **four** installed skills: `install-harness`,
`tune-harness`, `verify-harness`, `workspace-discovery`.

`templates/skills/` ships **29**, including `impl-plan`, `plan-harden`,
`plan-review`, and `harvest`.

> **autoharness ships the entire Stage planning gate chain to consumer
> workspaces and installs none of it for itself.**

I will not hand-write a document and label it an impl-plan output. Substituting
prose for an absent mechanism is the exact failure this document spent three
rounds diagnosing, and doing it here would falsify the finding by example.

#### C4.3 — Gate verdict

**BLOCKED — unmet criteria, all measured:**

1. **`impl-plan` skill not installed** in this workspace (4 of 29 present). The
   Step-3 gate is structurally unavailable, not skipped.
2. **Slice 1b not specifiable**: mechanism attribution is not mechanically
   derivable in-repo (producer is cross-repo), and the hand-maintained
   alternative fails the document's own durability law.
3. **#2 depends on a gate-produced pattern with n=1** (C2), and #1 is now its
   formal prerequisite.

**Criterion 1 is a harness gap, not a work-readiness gap.** Slice 1a is
genuinely ready in substance: bounded, read-only, mechanical over 956 existing
artifacts, no new authority, decomposable well under the 2-hour rule. It is
blocked only by the missing skill.

**Recommended unblock (operator authority, one line):** install the `impl-plan`,
`plan-review`, and `harvest` skills into this workspace from the templates it
already ships. That is a dogfooding fix worth making on its own merits — it is
the same class of finding as everything else in this document: **the mechanism
exists as a template and is not installed, so the step is re-derived in prose
instead of executed.**

### C5 — Closing

Three rounds. Two of my own #1s withdrawn on measurement, one DAG candidate
pruned on a measured 0% defect rate, one of my own laws refuted and corrected,
one of my own conclusions (§B3) downgraded, and a final gate that honestly does
not clear — with the blocker named as a harness gap rather than dressed up as
caution.

The most uncomfortable result is the last one: **the framework repository cannot
execute its own planning gate.** That is not an aside. It is the strongest single
instance of this document's thesis.
