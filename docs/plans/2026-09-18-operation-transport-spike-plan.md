---
title: "Bounded spike: autoharness operation transport — MCP/sidecar feasibility, tool authority, and distribution impact"
description: "Time-boxed spike deciding how autoharness exposes Python-backed atomic operations to agents over MCP, what tool authority that exposure declares, and what both cost a PyPI-distributed CLI whose entire runtime dependency set is jsonschema and PyYAML. Produces a findings artifact carrying seven required findings, each with a determining task and named acceptance evidence: the measured transport comparison, the recommendation, the rejected alternative, the exact .mcp.json registration entry, the per-tool authority allowlist with its fail-closed default, the CLI/MCP parity-test strategy, and an explicit statement of whether the PyPI distribution contract changes. A wildcard tool allowance is rejected unless proven necessary and bounded. The prototype registration has a stated lifecycle with a bounded owner and an explicit cleanup point, so the observation F7 requires is made against a registration that is actually running. The spike carries an executable composed-state gate: TRANSPORT_DECIDED is emitted by a determining task that checks every required finding against the ledger, and TRANSPORT_UNDECIDED blocks harvest of the consuming foundation plan. No production code ships."
doc_type: plan
source: docs/plans/2026-09-18-operation-transport-spike-plan.md
date: 2026-09-18
plan_id: operation-transport-spike
plan_path: docs/plans/2026-09-18-operation-transport-spike-plan.md
plan_role: active
revision: 3
verdict: null
disposition: REMEDIATED-PENDING-REVIEW
verdict_note: "verdict is null because no independent reviewer has judged revision 3. REMEDIATED-PENDING-REVIEW is recorded under disposition, where it belongs: it states what Stage produced, never what a reviewer found. Revision 3 is the product of one authorized Stage remediation cycle against attempt 02, which returned ADVISORY on revision 2 with one P2 (E1, the unspecified prototype lifetime on which F7's acceptance evidence depends) and two P3s (E2, manifest order; E3, F6 omitted from H7). Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 3
review_manifest: docs/reviews/2026-09-18-operation-transport-spike-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 71200CBB
  - 76EBDE6D
feature_id: 176-F
shipment_id: 182-S
unit_role: precursor-spike
dag_role: root
depends_on_shipments: []
gates: 184-S
requires_plan_hardening: true
hardening_rationale: "The spike's subject is distribution blast radius and a new agent trust boundary: it recommends a runtime dependency for a PyPI-distributed CLI, the registration entry that admits an autoharness server into .mcp.json, and the tool authority that registration grants over operations that write files and execute subprocesses. Stage's planning gate names CLI distribution an elevated-blast-radius signal, and Q1-Q3 and Q6 are entirely about CLI distribution. The blast radius that matters is the decision's, not the artifact's: a wrong or omitted answer is inherited by 184-S as an activation step. The hardening pass is present below and is a gate, not a completeness note."
tags:
  - spike
  - mcp
  - transport
  - distribution
  - tool-authority
  - precursor
---

# Bounded spike: autoharness operation transport

## Problem frame

Two release units in this portfolio specify an MCP-reachable operation, and
neither can be planned honestly today.

* `180-S` specifies a "guarded MCP create" for checkpoints. Attempt-08 finding
  `B3` recorded that the plan "names no MCP server that exposes it, no owner
  that implements it, and no registration step that makes it callable."
* `176-S` requires an "MCP parity boundary" for the P-004 gate. Attempt-08
  finding `B6` recorded that the gate is CLI-only, so an agent operating
  through MCP crosses no gate at all.

Both findings have the same cause: **there is no `autoharness` MCP server, and
whether there can be one is unresearched.**

`.mcp.json` registers six servers — `backlogit`, `engram`, `graphtor-docs`,
`context7`, `tavily`, `github`. `autoharness` is not among them.
`pyproject.toml` declares exactly two runtime dependencies (`jsonschema`,
`PyYAML`) with `requires-python = ">=3.10"`, and ships a console script. There
is no MCP SDK, and adding one to a PyPI-distributed CLI has consequences this
repository has already paid for once
(`docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`).

A third unknown sits on the same surface and is not separable from it. Per D1
the operations behind this server write to the filesystem through the atomic
write primitive and execute subprocesses through the fixed-argv primitive. The
governing decision's security-boundary table enforces tool authority by
"explicit per-tool allowlist in agent frontmatter and `.mcp.json`", and F8
records that `.mcp.json`'s `"tools": ["*"]` for the `backlogit` server is a
**current defect** whose removal `180-S` performs in its activation commit. A
registration shape researched without an authority answer would be adopted by
`184-S` at whatever default the throwaway prototype happened to use — and the
default already present in this repository is `["*"]`. The portfolio would
remove a wildcard from `backlogit` while introducing one on a
subprocess-executing server.

Writing a plan over those unknowns is what produced eight review cycles. This
spike exists so the foundation plan can be written over a measured answer.

## Questions

| # | Question | Determined by |
|---|---|---|
| Q1 | Hand-rolled JSON-RPC-over-stdio, or an MCP SDK runtime dependency? | `176.001-T` measurement, confirmed by `176.002-T` prototype |
| Q2 | What is the wheel/install-size and dependency-tree cost of each? | `176.001-T` |
| Q3 | Does either option constrain `requires-python >=3.10`? | `176.001-T` |
| Q4 | What is the exact `.mcp.json` registration entry for an `autoharness` server? | `176.002-T` |
| Q5 | How does a test prove CLI and MCP expose the same operation set? | `176.002-T` |
| Q6 | Does the recommendation change the PyPI distribution contract? | `176.003-T` |
| Q7 | What **tool authority** does that registration entry grant? | `176.004-T` |

### Q7 in full, because it is the question attempt 01 found missing

Q7 asks three things and is not answered by answering fewer:

1. **The literal per-tool allowlist** the `autoharness` server declares in
   `.mcp.json`, written out as the exact value that would be committed.
2. **The projection rule** that derives that allowlist from the operation
   registry — how a newly registered operation becomes (or fails to become)
   callable, stated as a rule rather than as a one-time list.
3. **The default for a registered-but-not-allowlisted operation.** The
   required answer is **not callable** — fail closed. If the prototype shows
   any other default, that is itself a finding and must be recorded as one.

**Wildcard authority is rejected.** `"tools": ["*"]` may appear in the
recommendation only if `176.004-T` records all three of the following, and
records them as observations rather than as reasoning:

* a specific capability that no enumerated allowlist can express;
* the exact bound that replaces enumeration, stated as a checkable predicate;
* why that bound is not weaker than enumeration, in terms a reviewer can
  falsify.

Absent all three, the recommendation is an explicit enumerated allowlist, and
the finding records the wildcard as **rejected with its reason**. A wildcard
that is merely convenient, merely the prototype's default, or merely consistent
with the existing `backlogit` entry is rejected on each of those grounds
separately.

## Required findings

Every required finding has one determining task and one named acceptance
evidence. A finding with no evidence in the shape named below is **not
recorded**, and the composed-state gate treats it as absent.

| # | Required finding | Question | Determining task | Acceptance evidence |
|---|---|---|---|---|
| F1 | Transport options inventoried and compared | Q1 | `176.001-T` | Comparison table with one row per option, each row carrying added runtime dependencies, maintenance surface, and the measurement's source command |
| F2 | Distribution cost measured, not estimated | Q2 | `176.001-T` | Measured wheel-size delta in bytes against the current two-dependency baseline, plus the resolved dependency tree for each option |
| F3 | Python floor impact resolved | Q3 | `176.001-T` | Each option's declared `requires-python` range, and a statement of whether `>=3.10` survives |
| F4 | Registration entry determined | Q4 | `176.002-T` | The literal `.mcp.json` entry, byte-exact, as it would be committed by `184-S` |
| F5 | Parity strategy determined | Q5 | `176.002-T` | The enumerating test's shape plus its recorded output over the prototype's registry, showing both transports resolving the same operation set and parameter names |
| F6 | Distribution contract impact stated | Q6 | `176.003-T` | An explicit "changes" / "does not change" sentence naming each contract term affected |
| F7 | Tool authority determined and bounded | Q7 | `176.004-T` | The literal allowlist value, the projection rule, the observed registered-but-not-allowlisted default, and either the wildcard rejection with its reason or the three-part wildcard justification above |

## Out of scope

* Any production code. The `176.002-T` prototype is **discarded at spike
  close**, on the schedule stated under *Prototype lifecycle* below; only
  findings survive.
* Any change to `.mcp.json`, `pyproject.toml`, or any agent surface. Those are
  activation steps and belong to `184-S`. The authority *answer* is in scope
  here precisely because the authority *edit* is not — Q7 has no other owner.
* Choosing which operations to expose. That is the foundation's concern. Q7
  determines how authority is expressed over whatever set is chosen, not the
  set.

## Prototype lifecycle

F7's third part requires the registered-but-not-allowlisted default to be an
**observed** property of a running registration (R3, H7). The only running
registration this unit produces is `176.002-T`'s prototype, so its lifetime is
specified here rather than left to inference.

| Stage | Owner | What holds |
|---|---|---|
| Created | `176.002-T` | A throwaway registration and a throwaway operation, reachable through both transports |
| **Survives** | `176.002-T` → `176.004-T` | The registration is **left running, or left restartable from a recorded local configuration**, until `176.004-T` has recorded its F7 observation. Discard at the close of `176.002-T` is **prohibited** |
| Observed | `176.004-T` | F7's default is read off the running registration |
| Discarded | `176.003-T` | At spike close, after F7 is recorded. `176.003-T` records the disposal in the findings artifact |

**Owner of the surviving state is `176.002-T`.** It is the task that creates
the registration, and it is the task whose record carries the obligation to
leave it observable. `176.004-T` is a consumer of that state, not its creator,
and it carries no prototyping budget.

**Restart, bounded.** If the registration is not running when `176.004-T`
begins, `176.004-T` may restart it from the local configuration `176.002-T`
recorded, **inside its own 45-minute bound**. It may not re-prototype: building
a new registration is `176.002-T`'s work, and a restart that does not succeed
inside the bound resolves F7 to `NOT-ANSWERED-FALLBACK` with the restart
failure recorded as what blocked it. This keeps F7's pass state reachable
without silently widening an `XS` task into a prototyping task.

**Cleanup is explicit and is not a workspace mutation.** The prototype lives
only in the working tree and in a local throwaway MCP configuration. Nothing is
committed, the tracked `.mcp.json` is never edited (that is a `184-S`
activation step), and `176.003-T` records that the registration was torn down
and that no artifact of it survives. No task in `184-S` depends on prototype
artifacts — only on the findings document.

## Tasks

| ID | Task | Phase | Size | Complexity | Elapsed bound |
|---|---|---|---|---|---|
| `176.001-T` | Inventory both transport options; measure distribution impact (F1, F2, F3) | research | XS | low | 45 min |
| `176.002-T` | Prototype registration and parity-test shape on a throwaway operation (F4, F5) | research | S | medium | 90 min |
| `176.004-T` | Determine the per-tool authority allowlist, its projection rule, and its fail-closed default (F7) | research | XS | medium | 45 min |
| `176.003-T` | Author the findings artifact with recommendation and rejected alternatives (F6, and the transcription of F1-F5, F7) | authoring | XS | low | 45 min |
| `176.005-T` | Composed-state validation: check every required finding against the ledger and emit the gate verdict | gate | XS | low | 20 min |

Sequence: `176.001-T` → `176.002-T` → `176.004-T` → `176.003-T` →
`176.005-T`. `176.004-T` follows the prototype because the
registered-but-not-allowlisted default is an **observed** property of a running
registration, not a design preference — and the *Prototype lifecycle* section
above is what makes that registration still there to observe.

Each task is bounded by both a size estimate and the elapsed bound above; the
two-hour rule is satisfied on both axes with the widest task at 90 minutes.

## Deliverable

`docs/spikes/2026-09-18-autoharness-operation-transport-findings.md`,
containing:

1. the measured comparison table for Q1–Q3 (F1, F2, F3);
2. the recommended transport, with its rationale;
3. the rejected alternative, with the reason it was rejected;
4. the exact `.mcp.json` registration entry (F4);
5. the tool-authority allowlist, its projection rule, its fail-closed default,
   and the wildcard disposition (F7);
6. the parity-test strategy and its recorded prototype output (F5);
7. an explicit statement of whether the PyPI distribution contract changes
   (F6);
8. the required-findings ledger below, completed.

This artifact is the **input contract** for
`docs/plans/2026-09-18-operation-substrate-transport-plan.md`. That plan must
not be harvested into executable tasks that assume a transport, or that assume
an authority model, before this artifact names both.

### Required-findings ledger

`176.003-T` writes this table into the findings artifact; `176.005-T` reads it.
Every row resolves to exactly one of three values:

* **`ANSWERED`** — the acceptance evidence named in the Required findings
  table is present in the artifact.
* **`NOT-ANSWERED-FALLBACK`** — the finding could not be determined inside the
  elapsed bound, the artifact records **what was attempted, what blocked it,
  and what an implementer must do instead**, and the R1 CLI-only fallback is
  invoked in writing for the affected scope.
* **`ABSENT`** — anything else, including a finding present as prose with no
  evidence in the named shape.

| Finding | Value | Evidence location in the artifact |
|---|---|---|
| F1 | | |
| F2 | | |
| F3 | | |
| F4 | | |
| F5 | | |
| F6 | | |
| F7 | | |

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `TRANSPORT_DECIDED` — every row of the required-findings ledger is `ANSWERED` or `NOT-ANSWERED-FALLBACK`, and no row is `ABSENT` |
| Fail state | `TRANSPORT_UNDECIDED` — one or more ledger rows is `ABSENT` |
| Not-observed state | `TRANSPORT_NOT_OBSERVED` — the findings artifact does not exist, or exists without a completed ledger. Distinct from `TRANSPORT_UNDECIDED` and never a pass |
| Producer | `docs/spikes/2026-09-18-autoharness-operation-transport-findings.md` (created in `182-S` by `176.003-T`), whose final line is the verdict token written by `176.005-T` |
| Consumer | `docs/plans/2026-09-18-operation-substrate-transport-plan.md` (`184-S`), which reads the verdict token before harvest |
| Activation commit | None — the spike activates nothing. The gate is read at `184-S` harvest time |

**The transition is executable and auditable.** `176.005-T` performs it
mechanically: read the ledger, resolve each of F1–F7 to one of the three
values, and append a single verdict line to the findings artifact in the exact
form

```text
COMPOSED_STATE: TRANSPORT_DECIDED | absent=0 | fallback=<n> | checked=2026-09-DD
```

or

```text
COMPOSED_STATE: TRANSPORT_UNDECIDED | absent=<n> | absent_findings=F<x>,F<y>
```

Auditability is the naming: `TRANSPORT_UNDECIDED` names the absent findings, so
a reader can check the verdict against the ledger without re-running the spike.
A verdict line whose `absent` count disagrees with the ledger is itself a fail.

**`TRANSPORT_UNDECIDED` blocks `184-S` harvest.** It does not degrade to a
partial pass, and an unanswered finding is never inherited by `184-S` as an
assumption. `NOT-ANSWERED-FALLBACK` is a pass value only because it carries the
R1 fallback in writing; silence does not.

## Time box

Each task carries the elapsed bound stated in the Tasks table. The bounds are
individual, not a shared pool: exceeding one bound does not borrow from
another.

On reaching a bound, the task **stops** and records
`NOT-ANSWERED-FALLBACK` for its findings, naming what was attempted and what
blocked it. For Q1 specifically the fallback is the **CLI-only** transport (see
R1). The spike does not expand to finish; an unfinished finding recorded
honestly is a usable input and an unrecorded one is not.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Both transport options prove unacceptable for a PyPI CLI | The CLI transport in `184-S` is unconditional and ships regardless. The sidecar degrades to a separately-installed optional surface, and the parity requirement is restated against that surface. Consuming units are told this explicitly through a `NOT-ANSWERED-FALLBACK` ledger row rather than inheriting a silent gap. |
| R2 | The prototype is mistaken for shippable code | `176.002-T` states discard explicitly, the Prototype lifecycle section names the discard point and its owner, nothing is committed and the tracked `.mcp.json` is never edited, and no task in `184-S` depends on prototype artifacts — only on the findings document. |
| R3 | The authority answer is a design preference rather than an observation | `176.004-T` follows the prototype and must record the **observed** registered-but-not-allowlisted default. A preference with no observation is `ABSENT`, not `ANSWERED`. The Prototype lifecycle section keeps the registration observable until that record exists, so the observation is reachable rather than assumed. |
| R4 | A wildcard allowance enters `184-S` by default rather than by decision | Q7 rejects `["*"]` outright unless the three-part justification is recorded. The rejection and its reason are themselves acceptance evidence for F7, so the absence of a decision is visible rather than silent. |
| R5 | The gate is claimed rather than executed | `176.005-T` is a separate task whose only output is the verdict line, and the line's `absent` count is checkable against the ledger by any reader. |

## Hardening review

Adversarial pass over this spike's failure modes, blast radius, trust boundary,
rollback and verification. This section is a gate, not a completeness note:
`requires_plan_hardening` is `true` because the unit's subject is distribution
blast radius and a new agent trust boundary, even though its artifact is one
document.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | The spike ships no code — why harden it at all? | Because the blast radius that matters is the **decision's**, not the artifact's. Every answer here is adopted by `184-S` as an activation step against `.mcp.json`, `pyproject.toml` and agent frontmatter. A question omitted here has no other owner, which is exactly how attempt 01's `A2` arose. |
| H2 | What does a wrong Q1/Q2/Q3 answer cost? | A runtime dependency added to a PyPI-distributed CLI. This repository has already paid a version-ceiling cost for that class of change once. The mitigation is measurement rather than estimation: F2 requires a measured byte delta and a resolved dependency tree, and an estimate is `ABSENT`. |
| H3 | What does a wrong Q4/Q7 answer cost? | A subprocess-executing, filesystem-writing server admitted to the agent trust boundary at whatever authority the recommendation carried. The fail-closed default (registered but not allowlisted ⇒ not callable) is stated here rather than discovered, and wildcard authority is rejected by default rather than permitted by silence. |
| H4 | What does a wrong Q5 answer cost? | The MCP-parity claims in `176-S` and `180-S` stay unfounded, which is the condition this portfolio already failed on twice. F5 therefore requires recorded prototype output, not a described strategy. |
| H5 | Is the trust boundary this spike designs wider than the one it replaces? | It is a **new** boundary, not a replacement. There is no `autoharness` server today, so every capability it gains is additive. That is the reason authority is enumerated at the outset rather than narrowed later: the portfolio is simultaneously removing `backlogit/*` in `180-S`, and introducing a second wildcard while removing the first would be a net regression. |
| H6 | What is the rollback if the recommendation is wrong? | For this unit, none is needed: no workspace state changes and the artifact is additive. For the consuming unit, the rollback is real and must be stated by the findings artifact — `184-S`'s activation commit is a single commit touching `.mcp.json`, `pyproject.toml` and agent frontmatter, and reverting that commit removes the server, its dependency and its authority together. The findings artifact records this explicitly so `184-S` does not have to invent it. |
| H7 | Is a documentation-derived answer sufficient? | Only for F3, where the declared `requires-python` range **is** the fact. F1, F2, F4, F5 and F7 require an observation: a measurement, a recorded output, or a running registration. A documentation citation in those rows is `ABSENT`. F6 is neither: it is **derived from F1–F3**, since whether the distribution contract changes follows from the measured dependency, size and Python-floor results rather than from a fresh observation. F6 is therefore recorded by the authoring task `176.003-T`, and it is `ABSENT` if its "changes"/"does not change" sentence does not name each contract term affected, or if the F1–F3 rows it derives from are not themselves `ANSWERED` or `NOT-ANSWERED-FALLBACK`. |
| H8 | What stops the spike from growing into the implementation? | The deliverable is a document; the prototype is declared discarded with a named discard point and owner; no task in this unit edits `.mcp.json`, `pyproject.toml` or any agent surface; and each task carries an individual elapsed bound with a recorded-fallback stop rather than an extension. `176.004-T`'s restart allowance is explicitly bounded by its own 45 minutes and explicitly excludes re-prototyping. |
| H9 | Can the gate pass with nothing determined? | No. An all-`NOT-ANSWERED-FALLBACK` ledger is a legitimate pass state only in the sense that it is honest, and it carries the CLI-only fallback in writing for every affected scope — which is a materially different input to `184-S` than a silent gap. An empty or missing ledger is `TRANSPORT_NOT_OBSERVED`, which is never a pass. |

### Blast radius

**In this unit:** one new file under `docs/spikes/`. Nothing is installed,
registered, executed on a consumer path, or mutated.

**Of this unit's decisions, which is what is being hardened:**

| Surface | Change this spike's answers authorize in `184-S` | Reversibility |
|---|---|---|
| `pyproject.toml` | Possibly one added runtime dependency, against a two-dependency baseline and a `>=3.10` floor | Revert of the single `184-S` activation commit |
| `.mcp.json` | A new `autoharness` server entry with a per-tool allowlist | Same commit |
| Agent frontmatter | A per-tool allowance for the new server | Same commit |
| PyPI distribution contract | Possibly changed; F6 states which terms | Requires a release, not a revert — which is why F6 is a required finding rather than a note |

The last row is the reason `requires_plan_hardening` is `true`. Every other
surface reverts with one commit; a shipped distribution contract does not.

### Trust boundary

The spike does not cross a trust boundary. It **specifies** one, and the
specification is the risk. Three properties are required of the recommendation
and are checked as F7's acceptance evidence: authority is enumerated, the
enumeration is derived from the operation registry by a stated rule, and the
default outside the enumeration is *not callable*. A recommendation missing any
of the three is `ABSENT` for F7 and therefore `TRANSPORT_UNDECIDED`.

### Rollback

Not applicable to this unit: no workspace state changes and the findings
artifact is additive. The consuming unit's rollback is stated under H6 and is
required content of the findings artifact, so `184-S` inherits it rather than
inventing it.

### Verification floor

A finding is recorded only with the acceptance evidence named in the Required
findings table. Prose without that evidence is `ABSENT`. The gate verdict is
written by a task whose only job is to write it, and its `absent` count is
checkable against the ledger by a reader who did not run the spike.
