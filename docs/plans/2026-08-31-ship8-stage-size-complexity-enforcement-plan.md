---
title: "SHIP-8 — Stage size/complexity decomposition enforcement"
date: 2026-08-31
slug: stage-size-complexity-enforcement
doc_type: plan
source_stash: "2E67938C (primary); 6A2D62DD (bounded, non-consuming)"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-8"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "no"
plan_review_verdict: "PASS"
---

# SHIP-8 — Stage size/complexity decomposition enforcement

## Problem

`2E67938C`: backlogit exposes `size` and `complexity` as first-class fields.
Stage must **actually use them, robustly and enforceably**, when decomposing
work, so that shipment and session growth is bounded and multiplicative AI
token/credit consumption is controlled. Today the fields exist; the requirement
is that Stage's decomposition consumes them as a gate rather than as decoration.

Two concrete gaps, both verified at `2661c1c8`:

1. **The mandate is authored but the enforcement is advisory.**
   `templates/agents/_stage.agent.md.tmpl` carries the two-axis rule (14
   occurrences of `complexity`) and `templates/skills/harvest/SKILL.md.tmpl`
   carries 22. But the documented failure path when the registry does not
   advertise sizing is to **degrade to prose in the description and flag it** —
   the agent continues. There is no point at which a missing or invalid
   `size`/`complexity` **stops** the harvest.
2. **The degradation path was silently live in this very workspace.** Because the
   installed registry omitted `features.sizing` (SHIP-7), the enforcement branch
   was unreachable here. This is the `029-DL` law again: the rule is produced by
   nothing and penalizes nothing, so it survives only by agent goodwill.

Evidence that the fields are usable once advertised: `backlogit_update_item`
declares `size` (with `size_source` and `size_ruleset_version`) and `complexity`
as **separate, mutually exclusive, body-preserving** mutation seams;
`backlogit_create_item` accepts no sizing params at all;
`backlogit_list_items` exposes a `complexity` filter and a computed
`size_composition` rollup on features and shipments. The write sequence is
therefore fixed at three calls per task (create → size → complexity), and the
rollup gives a shipment-level budget surface for free.

## Direction

Convert the two-axis rule from documentation into a gate at three points:

* **Harvest-time, per task.** A task without both a valid `size` and a valid
  `complexity` is not a harvested task. Enum-validate both before writing;
  reject and halt on an invalid value rather than coercing or defaulting.
* **Harvest-time, per split trigger.** `size` implying more than two hours of
  human-equivalent effort forces a split regardless of `complexity`;
  `complexity: high` forces a split or an explicit de-risking step (spike,
  further decomposition, or additional deliberation) regardless of `size`. Both
  triggers already exist in prose; they become checked conditions.
* **Shipment-assembly-time, per shipment.** Read the shipment's
  `size_composition` rollup back after assembly and fail the assembly if
  `unsized > 0`.

  **Scope narrowed in review-fix cycle 1 (Orchestrator local-review finding 14).**
  An earlier draft added "or if the composition exceeds the declared budget". There
  is **no declared aggregate budget** anywhere in this workspace — no numeric
  threshold, no histogram-to-effort mapping, no boundary tie-break rule — so that
  clause promised a gate that could not be implemented deterministically and could
  not be boundary-tested. It is **withdrawn**. This shipment enforces exactly one
  shipment-level predicate, and it is fully deterministic:

  > **BUDGET PREDICATE (the whole of it):** `size_composition.unsized == 0`.
  > Any other value fails the assembly. Nothing else about the composition is gated.

  Deciding an aggregate threshold is a **policy** decision, not a gate
  implementation, and is deferred through compliant P-021 capture `C754A19B`. The
  2-hour reliability constraint remains enforced **per task** by the two
  harvest-time gates above, which is where it actually governs agent success rate.

**Fail-closed when advertised; degrade loudly when not.** If the active registry
advertises `features.sizing`, a missing or invalid value is a **halt**. If it
does not (for example a `backlog-md` install), the existing behaviour is
retained — enum-validated values preserved as clearly-labelled prose in the
description — but the degradation must be reported explicitly in the harvest
report, not merely noted. That preserves the documented multi-registry contract
while removing the silent path.

## Hardening (P-006)

Not triggered: confined to Stage/harvest template text plus tests. No schema, no
CLI distribution surface, no template family beyond the two documents already
carrying the rule. Two constraints are nonetheless recorded as binding.

* **H1 (binding).** The gate applies to **newly harvested output only**. Day-one
  blast radius against the existing corpus must be exactly zero — no retroactive
  validation sweep, no migration of existing unsized items. This mirrors the
  Authority Test v2 migration story that portfolio unit S2 relies on, and it is
  what makes the gate promotable at all.
* **H2 (binding).** The three-call write sequence must be respected exactly:
  create with no sizing params; then one update setting `size` together with
  `size_source: agent` and a non-empty `size_ruleset_version`; then a separate
  update setting `complexity`. These seams are mutually exclusive and cannot be
  combined with each other or with any other field update.
* **H3 (binding) — TDD sequencing: the red test lands FIRST, and the split that
  makes it expressible.** Cycle 0 ordered task 1 (the harvest gate) ahead of task 2
  (which carried the regression tests for *both* gates), so the tests for task 1's
  behaviour would have been authored against an already-conforming implementation.
  Cycle 1 corrected the *order* but expressed it as two "halves" of a single task
  `158.002-T`, while simultaneously encoding `158.001-T` as blocked by the **whole**
  of `158.002-T`.

  **That dependency model is impossible, and it is corrected in review-fix cycle 2
  by an actual task split.** A task cannot be a prerequisite of `158.001-T` while
  also owning work that must happen *after* `158.001-T`: `158.001-T` could never
  start, because part B of its own prerequisite could never finish first. "Part A"
  and "part B" are not schedulable units — only tasks are, and a `blocks` edge
  binds the whole task.

  `158.002-T` is therefore **re-scoped to the red-test half only**, and the
  post-implementation shipment-assembly/green half becomes a **separate successor
  task, `158.003-T`**. The order is now explicit, acyclic, and machine-encoded as
  test → implementation → assembly:

  1. **`158.002-T` — red tests, completes first.** Write the negative tests:
     **T1** harvest a task with no `complexity` **must halt**; **T2** assemble a
     shipment with `unsized > 0` **must fail**; **T3** a `backlog-md`-shaped
     registry without `features.sizing` **must complete with a reported
     degradation**. **Observe and record them red.** Scope is `tests/` only.
  2. **`158.001-T` — implementation.** The harvest-gate change turns **T1** and
     **T3** green. Encoded edge: `158.001-T` blocked by `158.002-T`.
  3. **`158.003-T` — post-implementation assembly + green.** The shipment-assembly
     `size_composition` budget check turns **T2** green, and re-confirms T1/T3 still
     green. Encoded edge: `158.003-T` blocked by `158.001-T`.

  Both edges are **task-level** `blocks` edges in backlogit. They are distinct from
  the **shipment-level** edge `166-S` blocked by `165-S` (SHIP-7 → SHIP-8); see the
  Registry note below. Cycle 1's phrase "real blocks edge, not a comment" was true
  of the shipment edge but read as though a task edge to a `157-*` task existed. No
  such task edge exists, and none is needed.
* **H4 (binding) — the assembly gate reads `unsized`/`histogram`, never the
  shipment-level `ruleset_version`.** The one unverified assumption behind the
  assembly check was that the shipment `size_composition` rollup **actually reports
  `unsized`** and can be read back after assembly. **Verified in review-fix cycle 1
  and re-verified in cycle 2** — `backlogit_list_shipments` / `get_shipment` return,
  for every shipment in this run's own portfolio, a `size_composition` object of the
  shape `{"histogram":{...},"unsized":0,"members":[...],"ruleset_version":null}`.
  Re-measured at cycle 2 against `166-S` after the split:
  `{"histogram":{"M":2,"S":1},"unsized":0,...,"ruleset_version":null}`. The
  read-back gate is therefore buildable as specified, and `ruleset_version` is
  observed **null at the shipment level** even though every member task carries
  `size_ruleset_version: ah-stage-sizing-v1`.

  Two consequences, both binding on **`158.003-T`** (the assembly task created by
  the H3 split) and both mandatory acceptance there:
  * The budget check reads **`unsized`** and the **`histogram`**, which are
    populated and trustworthy. It **must not** gate on the shipment-level
    `ruleset_version`, which is observed null and would fail every shipment. A
    **positive test** must assert that a shipment with `unsized == 0` and a null
    shipment-level `ruleset_version` **passes**.
  * The shipment-level `ruleset_version: null` against populated per-task
    `size_ruleset_version` values is a **rollup-provenance gap**. It is recorded
    as deferred scope (`FE098366`), not fixed here — **N1** forbids schema
    change.

  With the assumption resolved, the assembly work carries `complexity: medium`, and
  the red-test task `158.002-T` carries `S`/`low`.
* **H5 (binding) — safety mode.** Every task enters `careful`, and this is
  propagated into each executable task's own body, not merely declared here.
  `158.001-T` additionally enters `freeze-scope` bounded to
  `templates/skills/harvest/SKILL.md.tmpl` and `templates/agents/_stage.agent.md.tmpl`
  plus their mirrors, because it edits the decomposition contract every future Stage
  run reads.

## Tasks

| # | ID | Title | Size | Complexity | Surface |
|---|---|---|---|---|---|
| 1 | `158.002-T` | Author the red regression tests for both sizing gates and record them observed failing | S | low | `tests/` |
| 2 | `158.001-T` | Make the harvest sizing gate fail closed when the registry advertises sizing, with explicit reported degradation when it does not | M | medium | `templates/skills/harvest/SKILL.md.tmpl`, `templates/agents/_stage.agent.md.tmpl` + mirrors |
| 3 | `158.003-T` | Implement the shipment-assembly size-composition budget check and turn the assembly test green | M | medium | `templates/agents/_stage.agent.md.tmpl`, `tests/` |

**Execution order is the table order**, and it is the machine-encoded order:
`158.002-T` → `158.001-T` → `158.003-T` (**H3**). The table is listed in execution
order rather than in ID order precisely because ID order is *not* execution order
after the cycle-2 split.

Cycle 0 carried two tasks; cycle 1 reduced task 2's complexity from `high` to
`medium` by measurement (**H4**); **cycle 2 split the former task 2 into the
red-test task `158.002-T` and the post-implementation assembly task `158.003-T`**,
which is what makes the dependency model satisfiable at all (**H3**).

**Registry note (measured cycle 1, re-verified cycle 2) — the authority question is
now ANSWERED.** `.autoharness/backlog-registry.yaml`'s `features:` block advertises
`shipments: true`, `queue: true`, `dependencies: true` and 12 others, but declares
**no `sizing` key at all** — while `backlogit_update_item` does expose `size`,
`size_source`, `size_ruleset_version`, and `complexity` params. Cycle 1 required
task 1's acceptance to "state explicitly which of the two is authoritative" without
deciding it. **Decided here, and binding on `158.001-T`:**

> **The advertised `features.sizing` flag is the sole authoritative signal.** The
> mere presence of sizing parameters on an operation **never** enables the gate on
> its own, and must not be used as an alternative or fallback trigger.

The registry is the declared contract every generated agent resolves against;
operation parameters are an implementation surface that varies by tool build.
Deriving the gate from parameters would make the same workspace fail closed or
degrade depending on which binary happened to be installed. The measured
consequence is that **this** workspace takes the degrade-and-report path until
SHIP-7 regenerates the registry — the gate is present but correctly inert locally.
That is the honest outcome, and it is sequenced away by the **shipment-level**
`blocks` edge `166-S` blocked by `165-S`. `158.001-T` ships a test asserting **both**
directions. Recorded as `D456616B`, now resolved rather than open.

## Non-goals

* **N1.** No backlogit schema change and no new sizing field.
* **N2.** No derivation of a range-deterministic per-session token/complexity
  threshold. `6A2D62DD` states plainly that "the threshold value is YET TO BE
  DETERMINED — establishing it is part of what the spike should explore". This
  shipment enforces against the thresholds that **already exist** (the 2-hour
  rule and the two enum axes). `6A2D62DD` stays active and is unconsumed.
* **N3.** No one-shipment-per-session execution policy. That is the second,
  coupled half of `6A2D62DD` and is Ship-side session lifecycle, not Stage
  decomposition.
* **N4.** No auto-splitting of oversized tasks. The gate **halts and reports**;
  a human or a subsequent Stage pass decides the split. Auto-splitting is
  explicitly a non-goal of portfolio unit S2 as well, and the two must not
  disagree.
* **N5.** No retroactive validation of the 612 existing tasks (**H1**).
* **N6.** No gate on the shipment-level `size_composition.ruleset_version`, which
  is observed null (**H4**).

## Deferred scope (P-021, captured not silently broadened)

**Ref column = backlogit stash entry ID.** Each row below is backed by a compliant
P-021 C2 capture-only stash entry carrying the literal `DEFERRED SCOPE EXPANSION`
token, the expansion statement, the C1 out-of-scope reasoning, per-field source
refs, a `requires deliberation: true` flag, and kind + provisional priority. Read
one with `backlogit stash get <id>`. These IDs replace the pseudo-IDs used in the
first draft, which were in-plan labels with no backing stash record (a P-021 C2
shortfall corrected in review-fix cycle 1).

| Ref | Capture | Residual risk if never built |
|---|---|---|
| FE098366 | Shipment-level `size_composition.ruleset_version` is `null` on every shipment measured, while member tasks carry `size_ruleset_version: ah-stage-sizing-v1`. Propagating per-task ruleset provenance into the rollup is a **backlogit-side** change and is forbidden here by **N1**. | **Low.** Provenance survives on each task; only the aggregate view loses it. The budget check reads `unsized`/`histogram` instead (**H4**), so no gate depends on the null field. |
| D456616B | This workspace's registry advertises no `features.sizing` key although `backlogit_update_item` accepts the sizing params. Reconciling the registry's advertised feature set with the tool's real capability surface is **SHIP-7's** registry-parity charter, not SHIP-8's. | **Low, and now bounded by a decided rule rather than an open question.** Review-fix cycle 2 settled the authority question: the advertised flag is authoritative and parameter presence never arms the gate (see the Registry note). Left unreconciled, this workspace takes the degrade-and-report path and the gate is present but inert locally — a known, tested, reported state rather than a silent one. The SHIP-7 → SHIP-8 shipment-level `blocks` edge already sequences the parity work first. |
| C754A19B | **Aggregate shipment size/complexity budget** — the numeric threshold, the histogram-to-effort mapping, the boundary tie-break rule, and the boundary test vectors. Added in review-fix cycle 1 when the undefined "exceeds the declared budget" clause was withdrawn from §Direction. Deciding a threshold is a policy decision (C1 discrimination (c)), not a gate implementation. | **Medium.** An oversized shipment made entirely of correctly-sized tasks still passes assembly. Mitigated because the 2-hour rule is enforced **per task** by the two harvest-time gates, which is the constraint that governs agent reliability; shipment-level bloat remains a Stage planning-review concern rather than a machine gate. |

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `verify-harness`; a
negative test per gate (**T1** harvest a task with no `complexity` → must halt;
**T2** assemble a shipment with `unsized > 0` → must fail); a positive test
confirming a `backlog-md`-shaped registry without `features.sizing` still completes
with a reported degradation rather than a halt (**T3**); a positive test confirming
that a shipment with `unsized == 0` and a **null** shipment-level `ruleset_version`
**passes** the budget check (**H4**/**N6**); and a two-direction test confirming that
the advertised `features.sizing` flag — not operation-parameter presence — is what
arms the fail-closed branch.

**Budget-predicate boundary cases (added in review-fix cycle 1, finding 14).** The
assembly predicate is `unsized == 0` and nothing else, so its boundary is a single
integer and must be tested exhaustively at that boundary:

| Case | `size_composition` | Expected |
|---|---|---|
| B1 | `unsized: 0`, non-empty `histogram` | **pass** |
| B2 | `unsized: 1`, non-empty `histogram` | **fail**, naming the unsized member IDs |
| B3 | `unsized: 0`, **empty** `histogram` (shipment with no task members) | **pass** — an empty shipment is not an unsized one; emptiness is a different defect and is not gated here |
| B4 | `unsized` field **absent** from the rollup | **fail closed** — an absent field is not zero; the gate must not read a missing key as passing |
| B5 | `unsized: 0`, `ruleset_version: null` | **pass** (**H4**) |

B3 and B4 are the two cases a naive `if unsized:` truthiness check gets wrong in
opposite directions, which is why both are named rather than implied. **No test
asserts an aggregate size/complexity threshold**, because no such threshold is
declared or promised — see deferred capture `C754A19B`.

All three of T1–T3 are authored and **observed red** in `158.002-T` before any
implementation lands; T1/T3 turn green in `158.001-T`; T2 turns green in
`158.003-T` (**H3**).

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Correctness | **P1** | A fail-closed harvest gate can **strand a partially written task**: `create_item` succeeds, the `size` update succeeds, the `complexity` update fails, and the halt leaves a half-sized orphan in the backlog. | **Resolved.** Task 1's acceptance requires the gate to validate **both** enum values *before* the create call, so a rejection happens before any write. If a write nonetheless fails mid-sequence, the halt message must name the item ID and the exact remaining call, so the state is recoverable rather than mysterious. The three seams are ordered so that the item is never left in a state a subsequent run cannot complete idempotently. |
| 2 | Scope/Maintainability | **P1** | This overlaps portfolio unit **S2**, whose `ART-03` detector checks exactly "`size` **and** `complexity` present". Building both is duplicated effort or, worse, two disagreeing rules. | **Resolved.** They are the **producer** and the **detector** of the same invariant and are deliberately complementary: SHIP-8 makes Stage *emit* conforming items; S2 *verifies* that anything in the backlog conforms, including items Stage did not produce. To guarantee they cannot disagree, this plan adopts S2's own constraints verbatim — enforce-on-new-only (**H1**), no auto-split (**N4**), no schema change (**N1**) — and records that S2 is the authority if they ever diverge. |
| 3 | Architecture | **P1** | Enforcement lives in **template prose** read by an agent. Prose is not a machine gate, so this reproduces the `029-DL` failure it claims to fix. | **Accepted, honestly bounded.** Task 2's shipment-assembly check is a genuine machine check — it reads the `size_composition` rollup back from the tool and fails on `unsized > 0`, which no amount of agent goodwill can fake. The harvest-time gate is prose plus a regression test asserting the documented behaviour. This is a **partial** mechanisation and is labelled as such rather than overclaimed; full mechanisation of harvest-time validation is precisely what S2's `ART-03` delivers, and duplicating it here would violate finding 2's resolution. |
| 4 | Constitution | P2 | Halting a dark-factory session on a sizing violation could strand an AFK operator. | The halt is a **decomposition** halt, not a session halt: it rejects one malformed task and reports it. Other independent scoped items continue, consistent with this run's own operating rules. |
| 5 | Schema/CLI/docs coupling | P2 | The `size_ruleset_version` value must be non-empty and meaningful; an arbitrary string makes provenance useless. | Task 1's acceptance requires a single declared ruleset identifier recorded in the harvest documentation, written with `size_source: agent`, and used consistently. |
| 6 | Security | P3 | No security surface. | Confirmed: no credentials, no network, no path handling, no destructive command. |
| 7 | Maintainability | P3 | The gate depends on SHIP-7 having installed `features.sizing`. | Encoded as a real `blocks` edge (SHIP-7 → SHIP-8), not as a comment. |

**Verdict: PASS.** 3 P1 raised, all 3 resolved. Zero unresolved P0/P1. (Cycle-0
verdict, preserved. Cycles 1 and 2 are recorded in their own sections below.)

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass.`
Every selected persona was covered inline against the Persona Rubric Adapter and normalized to
the P0–P3 scale; no persona was skipped. Declared, not silent.

**Plan hardening (P-006): required — `no`.** Not triggered (Stage/harvest template
text plus tests; no schema, no CLI distribution surface). Constraints **H1**–**H5**
are recorded as binding regardless, and each is propagated into a task acceptance
criterion.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Correctness | inline persona pass | 1 P1 (cycle 0), 1 P1 (cycle 1), 1 P1 + 1 P2 (cycle 2) |
| Scope boundary / Maintainability | inline persona pass | 1 P1 + 1 P3 (cycle 0), 1 P1 (cycle 1), 1 P2 (cycle 2) |
| Architecture | inline persona pass | 1 P1 (cycle 0) |
| Constitution | inline persona pass | 1 P2 (cycle 0), 1 P1 (cycle 1) |
| Schema/CLI/docs coupling | inline persona pass | 1 P2 (cycle 0), 1 P1 (cycle 1), 1 P1 (cycle 2) |
| Security | inline persona pass | 1 P3 (cycle 0) |
| Template integrity | inline persona pass | — (no finding) |

### Review-fix cycle 1 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 8 | Correctness | **P1** | Task 1 (the gate) was ordered ahead of task 2 (which carries the regression tests for *both* gates), so task 1's tests could never be observed red. | **Resolved by H3.** Order is now task 2's test half → task 1 → task 2's implementation half, with the red results recorded before each fix. |
| 9 | Maintainability | **P1** | Task 2 was `M`/`high`, tripping the complexity axis with neither split nor de-risking step. | **Resolved by H4.** The single source of uncertainty — whether `size_composition` reports a readable `unsized` — was resolved by direct measurement in this cycle. Task 2 drops to `medium`, and two binding consequences (read `unsized`/`histogram`, never gate on the null `ruleset_version`) are recorded. |
| 10 | Schema/CLI/docs coupling | **P1** | The plan's fail-closed branch keys on `features.sizing`, but this workspace's registry declares **no `sizing` key** while the MCP tool does accept sizing params. The gate would be inert exactly where it was authored. | **Resolved.** Measured and recorded in the Registry note; task 1's acceptance must declare which surface is authoritative rather than assume agreement, and the reconciliation is routed to SHIP-7 as `D456616B` behind the existing `blocks` edge. |
| 11 | Constitution | **P1** | No safety mode declared on a shipment that rewrites the decomposition contract every future Stage run reads. | **Resolved by H5**: `careful` on all tasks, plus `freeze-scope` on the harvest/Stage template surfaces for task 1. |

**Verdict: PASS.** Cycle 1: 4 P1 raised, all 4 resolved. Cumulative: **zero
unresolved P0/P1**.

### Review-fix cycle 2 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 12 | Correctness | **P1** | **The dependency model was impossible.** `158.001-T` was encoded as blocked by the *whole* of `158.002-T`, while `158.002-T` owned both the red tests *and* the post-implementation assembly work. `158.001-T` could therefore never start: part B of its own prerequisite had to run after it. Cycle 1's "part A / part B" language described an ordering that no schedulable unit could express, because a `blocks` edge binds a whole task. | **Resolved by the H3 split.** `158.002-T` is re-scoped to the red-test half only; the assembly half becomes the new successor task `158.003-T`. Machine-encoded edges are now `158.001-T ← 158.002-T` and `158.003-T ← 158.001-T`, i.e. test → implementation → assembly. Verified acyclic and satisfiable by topological sort over all 37 tasks. |
| 13 | Schema/CLI/docs coupling | **P1** | The authority question raised as finding 10 was *deferred to task acceptance* rather than decided, so two reviewers could still read the plan and disagree about whether parameter presence arms the gate. | **Resolved and decided in the plan.** The advertised `features.sizing` flag is the sole authoritative signal; operation-parameter presence never enables the gate. Recorded in the Registry note and propagated into `158.001-T`'s acceptance with a two-direction test. `D456616B` drops from Medium to Low residual risk. |
| 14 | Correctness | P2 | The H4 acceptance ("read `unsized`/`histogram`, never the null shipment-level `ruleset_version`") was attached to a task that no longer exists under that number after the split, and had no positive test. | **Resolved.** H4 is re-pointed at `158.003-T`, re-measured against `166-S` post-split (`{"histogram":{"M":2,"S":1},"unsized":0,"ruleset_version":null}`), and now requires a **positive** test asserting that `unsized == 0` with a null shipment-level `ruleset_version` **passes**. |
| 15 | Maintainability | P2 | The plan described the SHIP-7 dependency as a "real blocks edge, not a comment" in language that read as though a *task*-level edge to a `157-*` task existed. It does not. | **Resolved.** The plan and both `158-*` task bodies now state explicitly that the SHIP-7 → SHIP-8 edge is **shipment-level** (`166-S` blocked by `165-S`) and that no `158-*` task declares a dependency on any `157-*` task. Both edges are real; they sit at different levels. |

**Verdict: PASS.** Cycle 2: 2 P1 and 2 P2 raised, all 4 resolved. Cumulative:
**zero unresolved P0/P1**. Three review-fix cycles of three consumed; the next
review is the final independent disposition cycle.
