---
title: "Stage session memory — 029-DL DAG-as-steering determinism opportunity map (34AAF1C7 widening)"
date: 2026-08-25
agent: stage
route: claude-opus-5 / anthropic / high
session_id: stage-2026-08-25-029DL-dag-steering-determinism
source_stash: 34AAF1C7
deliberation_id: 029-DL
prior_deliberation: 028-DL
decision_artifact: docs/decisions/2026-08-25-dag-as-steering-mechanism-determinism-opportunity-map.md
source: docs/memory/2026-08-25-stage-029-dl-dag-steering-determinism.md
doc_type: memory
---

# Stage session memory — 029-DL

## Session type

Operator-directed **expansive brainstorm / deliberation cycle**. Read-only.
Widens `028-DL` from the narrow question *"can a DAG prove PR-review
convergence?"* to *"where can DAG structure act as a **steering** mechanism
toward determinism across the whole autoharness workflow surface?"*

## Disposition

**Deliberation-only.** No impl-plan, no plan-harden, no plan-review, no harvest,
no shipment — **by choice, not deferral** (see "Why no harvest" below).

## Artifacts

| Kind | Path / ID |
|---|---|
| Decision artifact | `docs/decisions/2026-08-25-dag-as-steering-mechanism-determinism-opportunity-map.md` |
| Session memory | `docs/memory/2026-08-25-stage-029-dl-dag-steering-determinism.md` (this file) |
| backlogit deliberation | **`029-DL`** (queued) |
| Links created | `029-DL --informs--> 028-DL`; `029-DL --related_to--> 115-F`; `029-DL --related_to--> 110-F` |
| Stash | `34AAF1C7` annotated in place (14,042 → 22,621 chars). **ACTIVE, MEDIUM, NOT archived.** |
| Shipment | **none created** |

## Verdict in one line

The operator's pushback was correct. `028-DL` is **not overturned** but **is
re-scoped** — from a general verdict on DAGs to a correct verdict about
*open-node-set convergence graphs*. Several DAG opportunities are genuinely
strong; one is ready to plan on operator go.

## Key results

### 1. Six determinism properties disambiguated

D1 reproducibility · D2 choice elimination · D3 coverage/reachability proof ·
D4 termination · D5 memoization · D6 auditability.

A DAG delivers **D2, D3, D6 outright over closed node sets**; delivers **D1/D5
only inside the hermetic installer**; **cannot deliver D4** (that is `028-DL`'s
correct result). `028-DL` tested the DAG against **D4 only** — the single
property of six that DAGs provably cannot deliver — and generalized the negative.
That is the quantifier error.

Corollary: `028-DL`'s premise *"the node set is not fixed"* is **true for review
findings, false almost everywhere else** — plan units close at plan-review,
shipment manifests close at assembly, pack composition closes at install.

### 2. Report-only ≠ non-steering (the reframe that preserves the non-goal)

`compute_next_eligible` (115-F) is read-only, honors P-001/P-016, creates no
scheduler — and yet **uniquely determines the next shipment** via a total order
(`-fan_out`, `id`). **Steering comes from constraining choice, not scheduling.**
The `dag-readiness` no-scheduler NON-GOAL is therefore **respected, not
revisited** (option (a), not (b)).

### 3. Empirical ground truth (measured over 964 artifacts)

* **452 task→task `blocks` edges have NO reader** — dark data; the F5
  written-but-unread failure is *present today*.
* The only graph with a reader carries **26 edges across 149 shipments**;
  `dag-readiness` reports a **critical path of 2 nodes** — a measure of graph
  poverty, not work structure.
* **24/149** shipments declare `dependencies:`; **1/149** uses `queue_position`.
  ~84% of ordering rides on an **undeclared numeric-ID convention**, which
  `pipeline-topology` reverse-engineers in `_prior_shipment_id` — a heuristic
  that produced **two recorded correctness defects** (`docs/compound/2026-08-18-*`,
  one severity **high**). **Missing graph structure has already shipped bugs here.**
* Read-only prototype found **44 findings invisible to every existing tool**:
  9 malformed dependency endpoints (literal `'["003.001-T"]'`, undetected 4 months),
  3 orphan tasks, 11 tasks in no shipment manifest, **21 cross-shipment task edges
  with no declared shipment ordering** (33% of 63), 0 cycles.
* `backlogit_doctor` covers orphans / duplicates / partial mutations /
  shipped-event completeness — **no dependency-topology checks at all**.
* Closure `conditions:` requires `evidence` to be **non-empty but never
  resolves it** — a closure citing a nonexistent file **passes today**.

### 4. Architecture

**One node namespace (UAR: `bl:` / `path:` / `git:` / `gh:`), several typed edge
families, explicitly NOT one merged graph** (merging would repeat `028-DL` §2.1's
four-graphs-collided error).

* **Law 1 — DERIVE, NEVER PERSIST.** Graphs are views computed at read time from
  existing markdown. Structurally dissolves `028-DL` §2.2's disposable-cache
  objection; **zero new storage, zero schema, zero backlogit change**.
* **Law 2 — NO GRAPH WITHOUT A READER; NO READER WITHOUT A BINDING.** The anti-F5 law.

Boundary extension: **backlogit must never learn that a task-level `blocks` edge
implies a shipment-level ordering.** backlogit stores edges; autoharness
interprets them.

### 5. Ranked keeps / prunes

**Keep:** (1) backlog graph integrity + edge lift + coverage; (2) cross-reference
integrity graph — makes F5 *mechanically detectable*; (3) evidence/provenance
graph; (4) plan-as-DAG — highest yield overall, medium-high blast radius (F4);
(5) install/tune composition graph — the one hermetic island where D1/D5 apply.

**Pruned as cargo-cult:** quality-gate DAG (5 nodes, known order — the real
problem is a *cache key*), policy-interaction DAG (contradiction/shadowing are
*logical*, not topological — a precedence DAG is false precision), memoization
DAG (fails all three hermeticity tests; keep HEAD-pinned *invalidation*, reject
*caching*).

### 6. New triage heuristic (A8)

> **"Must I invent node identity?"** is the primary triage question for any
> future DAG candidate. Every surviving candidate uses externally-supplied
> identity. The moment a proposal must invent stable IDs, it inherits the exact
> blocker that has defeated the reasoning-state strand across five sessions.

## Recommended first slice

`autoharness gate backlog-graph-integrity` — read-only, report-only, six finding
classes, modelled on the proven `dag-readiness` contract. **Zero new prose**
(dodges F4), **reader-only** (dodges F5), **zero new authority**, always exit 0 in v0.

Its one open unknown — shipment manifest format drift — was **closed this
session** (`items:` present 149/149; covering feature derivable from item parents
141/149). **The slice is unblocked and plan-ready.**

**Pre-registered falsification test:** (a) undeclared-ordering findings correlate
with the two recorded `_prior_shipment_id` defects; (b) ≥1 finding actionable on
inspection; (c) total findings < ~100 or it is noise; **(d) PROSPECTIVE — over
the next ≥3 Stage harvest cycles the gate must fire at least once on
newly-created structure before it ships.** (a)–(c) are already satisfied by the
prototype and are therefore weak; **(d) is the real test and can fail.** Three
consecutive clean harvests ⇒ the defect class is historical ⇒ demote the gate to
an occasional hygiene command and re-derive the near-term ranking from C6/C8.

## Why no harvest (stated so a future session does not mistake this for deferral)

The first slice is **genuinely ready to plan** — precise requirements, exact
in-repo prior art, existing data, low blast radius, zero new authority,
prototyped and validated. It is withheld for two correctness reasons, not caution:

1. The requested deliverable is a **ranked map intended to inform an operator
   choice** among candidates committing multi-phase capacity; harvesting one
   pre-empts that choice.
2. **Q1's two architectural laws are policy-shaped and would be assumed by the
   code** — they want ratification *before* implementation, not retrofit.

**One word from the operator moves this to plan.** §8 of the decision artifact is
plan-ready as written.

## Operator authority required (029-DL Q1–Q5)

* **Q1** — Ratify the two architectural laws (Derive-Never-Persist; No-Graph-Without-A-Reader).
* **Q2** — May any of these gates ever **block**? All are report-only as proposed.
  C8 (evidence resolution) is the least controversial promotion since
  P-014/P-018/P-020 already fail closed.
* **Q3** — Is plan-as-DAG worth its agent-contract blast radius (F4)?
* **Q4** — **Retire** the numeric-ID shipment convention by materializing implied
  edges and deleting `_prior_shipment_id` [**recommended**], or **ratify** it and
  validate conformance?
* **Q5** — Split `34AAF1C7`, now **three-stranded**: (a) PR-review convergence
  [`028-DL`, executable]; (b) reasoning-state identity [still blocked by A8];
  (c) DAG-as-steering program [`029-DL`]. **Not executed** — operator-visible
  reclassification.

## Standing safety note (reaffirmed unchanged)

Any mechanism that **governs when agents stop reasoning** is authority-expanding
runtime behaviour and requires explicit operator consent. **Every `029-DL`
candidate is report-only and governs nothing.**

## Process compliance

* Read-only throughout. No source, template, schema, or config file modified.
* No branch, worktree, commit, push, or PR. P-016 Stage spike-worktree exception
  **not exercised**.
* Pre-existing dirty worktree preserved untouched (`.mcp.json`,
  `.backlogit/stash.jsonl`, `.backlogit/runtime/`, `.backlogit/queue/028-DL.md`,
  `.backlogit/checkpoints/checkpoint-20260825-165846.json`, and the two prior-session
  docs artifacts).
* All backlog mutations via backlogit MCP/CLI. Index synced at session start and end.
* Startup checkpoint recovery: 4 checkpoints enumerated, **all `resolved`**,
  0 quarantined, 0 anomalies ⇒ zero-candidate normal startup, no recovery needed.

## Next actor

**OPERATOR** — decide Q1–Q5. If Q1 is ratified and the first slice authorized,
the next actor is **Stage** (impl-plan → plan-harden if signalled → plan-review →
harvest), then **Ship**.

---

## ADDENDUM — Pushback Round 1 (Orchestrator adversarial review)

Eight adversarial positions. **Five adopted, one adopted with a material
precision, one refuted with data, one reversed my own #1.** Full analysis in the
decision artifact's `ADDENDUM — Pushback Round 1` section.

### What changed

| # | Position | Outcome |
|---|---|---|
| 0 | Don't produce a fifth deferral | **ADOPTED** — Q1 was a *manufactured gate*; **withdrawn** |
| 1 | Termination objection doesn't transfer | **CONFIRMED**, with a precision that matters |
| 2 | Steering ≠ scheduling | **ADOPTED**, precedent stronger than claimed |
| 3 | Confront enforcement now | **ADOPTED** — concrete gate proposed, needs *no consent* |
| 4 | Tie-breaks are the bottleneck | **REFUTED with data** — and it **falsified my own #1** |
| 5a | Coverage as reachability | **ADOPTED and promoted to #1** |
| 5b | Memoization | strong form **pruned**; weak form **conceded and promoted** |
| 6 | Pipeline is already a prose DAG | **CONFIRMED** — now the organizing frame |
| 7 | Their first-slice candidate | **THEIRS WINS** — conceded on measurement |

### New measurements taken this round

* **Order determinacy**: declared edges **0.34%**, with C13's lift **0.55%**,
  numeric-ID convention **100%** of 11,026 shipment pairs — **never contradicted**
  (0/63 cross-shipment edges). **Tie-breaks already do ~100% of the work.**
* **Acceptance-criteria block**: 166/612 tasks (27%); **numbered `ACn` IDs in only
  4 tasks**. Adoption by band: 0 → 26 → 43 → **46** → 38 → 39 → **0%**.
* **Closure artifacts**: 45/148; adoption by band 0 → 20 → 80 → 47 → **100%**.
* **Closure `evidence:` refs**: task IDs **3/3** and commit SHAs **2/2** resolve.
* **Checkpoint `phase`**: **27 distinct ad-hoc values** across sessions.
* **Session journals**: supervisor lifecycle is **coded and journaled**
  (`SessionPhaseChanged`, 11 transitions); agent Required Steps is **prose only**.
* **`R#` requirement IDs**: mandated by the brainstorm skill ("never renumbered"),
  present in 18/71 plans.

### The single most important result — a natural experiment

Two structurally identical prose conventions, one repository, same authors, same
period. One acquired a mechanical reader; the other did not.

| Convention | Reader | Adoption trajectory |
|---|---|---|
| Closure artifact | **YES** (`pipeline-topology`, P-014/P-015) | 0% → … → 80% → **100%** |
| `acceptance-criteria` block | **NONE** | 0% → … → 46% → **0%** |

**Reader ⇒ converged to 100%. No reader ⇒ rose to 46%, collapsed to zero.**

This is empirical proof of **Law 2**, of the **F5** failure mode, and of the
extraction thesis in one observation. It also upgrades the assessment of
"emitted" graphs from *low value* to **negative value** — they decay silently
while projecting rigor.

**Law 2 is therefore not hygiene. It is the load-bearing finding**, and Law 1
(derive, never persist) is merely the cheapest way to satisfy it.

### Self-falsification recorded

My §5 ranked C13 (edge lift) **#1** and credited it with **D2 / choice
elimination**. Measurement withdraws that credit: it moves order determinacy
**0.34% → 0.55%**, resolving 23 pairs of 11,026, against a convention that
already orders 100% correctly. **C13 survives only as a bug fix** (retire
`_prior_shipment_id`'s *adjacency heuristic* — not the numeric convention, which
has never been wrong) **and an auditability check.**

### Revised #1

**`autoharness gate coverage-integrity`** — read-only, report-only, merging the
computable coverage checks with the new **convention-decay detector** (flag any
structured convention whose adoption is *declining* — Law 2 made mechanical,
self-applying, would have caught the AC collapse four bands early).

Then promote to a **fail-closed harvest-output gate** under the **authority
test**: *a gate is authority-expanding iff it creates an obligation not already
in policy.* P-003 already obliges decomposition integrity ⇒ enforcing it
mechanically **needs no operator consent**.

**Not computable today**: `AC_WITHOUT_COVERING_TASK` — only 4/612 tasks carry AC
IDs. Needs plan-unit identity (C1) first ⇒ **C1 becomes phase 2, not an option.**

### Revised falsification (genuinely refutable)

* **Law 2 falsified** if the decay detector flags a declining convention that
  *does* have a reader, or a readerless convention proves stable/rising across ≥4 bands.
* **Coverage thesis falsified** if the 446 criterion-less tasks show **no higher
  review-finding rate** than the 166 with criteria ⇒ the gap is cosmetic ⇒ close
  the program rather than stage it.

### Revised disposition

* **Q1 — WITHDRAWN** as a gate. Law 2 is now evidence, not a proposal.
* **Q4 — ANSWERED by measurement**: keep the numeric-ID convention; retire
  `_prior_shipment_id`'s adjacency heuristic.
* **Q2 — narrowed**: the harvest-output gate needs no consent; only "must claim
  `next_eligible`" would, and it is not proposed.
* **Q3 — sequenced, not optional**: C1 is phase 2.
* **Q5 — unchanged.**

**Ready for `impl-plan` now against the revised slice, with no ratification
precondition.**

---

## ADDENDUM — Pushback Round 2

**The round-1 #1 was withdrawn.** Position 1 correctly identified that the Law 2
evidence could not distinguish "has a reader" from "has a reader with teeth."
I ran the experiment that separates them.

### The isolating experiment

Same gate (`pipeline-topology`), same corpus, same period, same authors, both
conventions introduced in the same band. Only difference: whether **absence** is
penalized.

| Band | Closure (absence **blocks**) | `dependencies:` (absence **compensated**) |
|---|---|---|
| 95–116 | 68% | 18% |
| 117–138 | 91% | 59% |
| **139–155** | **100%** | **41%** |

Mature bands n=39: 37/39 vs 20/39. **Fisher exact p = 1.97e-05.**
`_prior_shipment_id` (topology.py L1433-1465) silently falls back to numeric
adjacency, so the blocking gate tolerates the field's absence.

**Readership is not the variable.**

### Law 2, corrected

> **A convention survives iff a machine either PRODUCES it or PENALIZES ITS
> ABSENCE. Being read is neither necessary nor sufficient.**

Four measured cells:

| Cell | Example | Trajectory |
|---|---|---|
| produced | `size`/`complexity` (advisory, fail-open, gate **writes** it) | 0→48→**100→100%** |
| penalized | closure artifact | 0→68→91→**100%** |
| read-but-tolerated | `dependencies:` | 0→18→59→**41%** |
| unread | `acceptance-criteria` block | 0→22→62→52→**15%** |

`gate size` is the counterexample to a pure teeth reading: `cli.py` L516-519 says
"advisory and must never block," yet 100% — because `sizing.py` L343 writes the
field. **Generation is as durable as enforcement and needs no consent.**

### What was withdrawn and why

* **`coverage-integrity` (round-1 #1) — WITHDRAWN**, two independent grounds:
  1. Report-only = cell 3 = the cell that decayed.
  2. Its falsifier is **not computable** (`copilot_review.py` has no per-task
     attribution), and the replacement local test reads **null**: 58 mature
     shipments, AC-rich 0.20 vs AC-poor 0.18 compound records, task counts
     matched, underpowered at base rate 0.2.

### New #1 — `autoharness gate convention-durability`

Classify all conventions into the four cells and **predict** decay.
Enumeration is **derived, not curated**: 48 frontmatter keys + 18 delimited body
blocks = **66**, zero judgment calls.

Already surfaced: a **schism** (`acceptance_criteria` key on 3 vs
`acceptance-criteria` block on 169) and two DOA conventions (`queue_position`
1/149, `covering_feature_id` 1/149).

Escapes its own law: maintains **no per-artifact convention**. Already made a
correct prediction before it was built. Falsifier: any produced/penalized
convention decaying over ≥2 bands, or any unread/tolerated one stable/rising over
≥4 bands. **Authority: none.**

**#2** — AC-ID **generator** (cell-1 shape, `gate size` pattern), gated on #1.

### Other adoptions

* **Authority test v2**: obligation novelty **OR** activation blast radius.
* **Migration solved**: the harvest-output gate is intrinsically
  enforce-on-new-only — day-one blast radius against 612 existing tasks is zero.
* **P-021 reframe** — labelled **INSIGHT**; one narrow sequencing mechanism only
  (coverage proofs must run after C2 capture, else the node set is still open).

### Next actor

**OPERATOR** — no ratification gate remains. New #1 is read-only, zero authority,
ready for impl-plan against §B4.

---

## ADDENDUM — Pushback Round 3 (final)

### Artifact retitled

`docs/decisions/2026-08-25-dag-as-steering-mechanism-determinism-opportunity-map.md`
→ **`docs/decisions/2026-08-25-machine-produced-structure-determinism-and-the-surviving-dag-partition.md`**

New title: *Machine-Produced Structure, Not Graph Structure, Is the Binding
Constraint on Determinism — with the DAG partition that survives.*
Abstract rewritten; `original_title` / `original_filename` preserved in frontmatter.

### Headline finding, stated plainly

> **The DAG is not the lever. The lever is whether a machine PRODUCES the
> artifact or PENALIZES ITS ABSENCE.**

### The DAG question: ANSWERED, not abandoned

The law and the DAG question are **orthogonal**: the law governs whether a
representation *persists*; a DAG governs what you can *prove* once it exists.
The law **filters** which graphs can exist. Applied to the nine closed surfaces:

**7 survive** — shipment manifest (`items` 149/149), decomposition (`parent_id`
630), gate set, policy set, cross-reference graph, pack composition (caveat),
Required Steps (conditional).
**2 die** — impl-plan units (`R#` 18/71), acceptance criteria (`ACn` 4/612) —
exactly the two needing authors to mint new identifiers.

### DAG-shaped challenger tested and pruned on data

Cross-reference integrity graph: 400 links, 343 local, **4 dangling (1.2%), all
documentation placeholders → real defect rate 0%.** The 131 unresolved backlog
`references:` are historical link rot on archived artifacts. **A gate with a 0%
defect rate is ceremony.** Pruned on measurement.

### Produced cell split (n question)

* **Store-produced** (backlogit writes it): ~10 members, 100%, **full 4-month
  corpus, zero decay**.
* **Gate-produced** (advisory gate writes back): **`size` only**, ~3 bands.

#2 is a bet on a pattern replicated **once**, inside a class replicated ~10
times. **#1 is now a formal prerequisite for #2.**

### Correction to §B3

Underpowered null = **"no supporting evidence found," not evidence of absence.**
No longer counted as an independent demotion. Coverage demoted on §B1.2 alone.

### GATE VERDICT: BLOCKED — three named criteria

1. **`impl-plan` skill not installed.** `.github/skills/` = **4**;
   `templates/skills/` = **29** including impl-plan/plan-harden/plan-review/harvest.
   **autoharness ships the whole Stage planning chain to consumers and installs
   none of it for itself.** I did not hand-write a fake impl-plan.
2. **Slice 1b not specifiable.** Mechanism attribution is not mechanically
   derivable: `archived_from` (559, machine-written) has **0** refs in
   autoharness source — the producer is **cross-repo** (backlogit). The
   hand-maintained map fails the document's own durability law.
3. **#2 rests on n=1** gate-produced pattern.

**Slice 1a (adoption-trend detector over 66 conventions) is READY IN SUBSTANCE**
— bounded, read-only, mechanical, no new authority. Blocked only by criterion 1.

**Recommended unblock (operator, one action):** install `impl-plan`,
`plan-review`, `harvest` from the templates this repo already ships.

### Outcome

**Deliberation-only. No harvest. No shipment.** Blocked on a named harness gap,
not deferred by habit.
