---
title: "DAG-authoritative predecessor derivation for pipeline-topology pre_claim — decided plan"
description: "Test-first implementation plan retiring the implicit numeric-adjacency predecessor heuristic in `pipeline-topology --phase pre_claim` in favour of explicit backlogit `blocks` DAG edges, adding deterministic predecessor provenance to gate output, aligning `dag-readiness` advisory output with the authoritative model (including closure evidence), and coupling templates, installed dogfood instructions, and documentation."
doc_type: plan
source: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
date: 2026-09-12
status: decided
decision_source: docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
bug_source: docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md
stash_ids:
  - AF2890B7
---

# Decided Plan — DAG-Authoritative Predecessor Derivation

## 1. Source Understanding

Implements Option C of
`docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md`:
explicit backlogit `blocks` edges become the sole predecessor authority for
`pipeline-topology --phase pre_claim`; the implicit numeric-adjacency heuristic is
retired as a claim-blocking input; gate output gains deterministic provenance; and
`dag-readiness` is aligned to the same authoritative model.

This plan **supersedes** the presentation-only remedy recommended in
`docs/bugs/2026-09-11-...-numeric-predecessor-bug.md` §7 under explicit operator
direction. The bug document remains unmodified as the historical record.

### Carried-forward critical correction

Reproduced in-workspace (deliberation Finding 1): `163-S` declares
`dependencies: [162-S]` **explicitly**. The numeric heuristic is a **no-op** for
`163-S`, and its block token is `PREDECESSOR_CLOSURE_INCOMPLETE`
(`closure_complete: null`), not `PREDECESSOR_NOT_SHIPPED`.

**Retiring the numeric fallback will not, by itself, unblock `163-S`.** The
`163-S` symptom is a closure-evidence defect, addressed by T7 below and tracked
as a distinct task. No task in this plan may claim to fix `163-S` via predecessor
derivation.

## 2. Codebase Research

| Surface | Location | Change |
|---|---|---|
| Numeric heuristic | `src/autoharness/gates/topology.py::_prior_shipment_id` (L1433–1469) | Retire as claim-blocking input |
| Predecessor union | `topology.py::_shipment_readiness_check` (L1574–1578) | Derive from explicit edges only; add provenance |
| Block tokens | `topology.py` L1585–1628 | Add `predecessor_source`; add `UNSEQUENCED_SHIPMENT` |
| Advisory readiness | `topology.py::_dag_all_predecessors_finished` (L1873), `compute_dag_readiness` (L1968) | Model closure evidence; advisory labelling |
| Next-eligible | `topology.py::compute_next_eligible` (L2075) | Non-authorizing disambiguation |
| Closure evidence | `topology.py::FilesystemTopologyReaders.closure_complete` (L654) | Shared with advisory path |
| Engine tests | `tests/test_gates_topology.py::ImplicitNumericPredecessorTests` (L1648–~1750, 5 cases) | Migrate, not delete |
| CLI tests | `tests/test_gate_pipeline_topology_cli.py` | Provenance in JSON output |
| Templates | `templates/policies/workflow-policies.md.tmpl`, `templates/agents/_orchestrator.agent.md.tmpl`, `templates/agents/_ship.agent.md.tmpl` | Sequencing contract text |
| Installed dogfood | `.github/instructions/workflows.instructions.md`, `.github/agents/_ship.agent.md`, `.github/agents/_orchestrator.agent.md` | Mirror template changes |

### Prior-defect history (from `docs/compound/`)

`_prior_shipment_id` has produced three successive correctness defects
(multi-hop reverse-dependency false PASS; forward-dependent false NEGATIVE;
numeric-direction predicate correction). The forward-dependent defect is recorded
as **still unfixed on `main`**. T2 must confirm retirement renders it moot rather
than assuming so.

## 3. Contract Definition

### 3.1 Predecessor derivation (authoritative, `pre_claim`)

```text
predecessor_ids := ShipmentState.blocking_predecessor_ids   # explicit `blocks` only
predecessor_source :=
    "explicit"    when predecessor_ids is non-empty
    "none"        when predecessor_ids is empty  (legitimate DAG root)
```

`_prior_shipment_id` is **never** consulted for claim blocking.

### 3.2 Migration posture (fail-closed, explicit)

A shipment with no explicit predecessor is a **legitimate DAG root** under the new
contract. Default behaviour: **pass with `predecessor_source: "none"`** and an
advisory `UNSEQUENCED_SHIPMENT` note in gate output.

For workspaces that relied on unstated numeric sequencing, an **opt-in** strict
mode (`.autoharness/config.yaml` → `gates.pipeline_topology.unsequenced_shipment:
block|warn`, default `warn`) restores blocking. The setting is declarative data
only — no executable workspace rules, no vendor identifiers.

Silent behaviour change is forbidden: the provenance field must always state
which model produced the outcome.

### 3.3 Advisory alignment (`dag-readiness`)

`dag-readiness` remains **advisory and non-authorizing**. It must:

* model the **same** closure-evidence requirement `pre_claim` applies, via the
  shared `closure_complete` reader (one shared helper, not a parallel
  reimplementation);
* label its output explicitly advisory/non-authorizing;
* disambiguate `next_eligible` so it cannot read as authorization.

`pipeline-topology --phase pre_claim` remains the **sole claim authority**.

## 4. Test-First Task Breakdown

All tasks are sized ≤ 2 hours human-equivalent. RED tests precede implementation.
Width isolation observed: engine, CLI, templates, and docs are separate tasks.

| # | Task | Kind | Size | Complexity | Depends on |
|---|---|---|---|---|---|
| T1 | RED: authoritative derivation matrix | test | S | medium | — |
| T2 | Engine: DAG-authoritative derivation + provenance | impl | M | high | T1 |
| T3 | Migrate `ImplicitNumericPredecessorTests` | test | S | medium | T2 |
| T4 | RED: advisory alignment + closure modelling | test | S | medium | T2 |
| T5 | Engine: `dag-readiness` alignment + advisory labelling | impl | M | high | T4 |
| T6 | CLI: surface provenance in JSON/text output + tests | impl | S | low | T2 |
| T7 | `163-S` closure-evidence defect: diagnose + remediate | bug | S | medium | T2 |
| T8 | Templates, policies, installed dogfood instructions | docs | M | medium | T5, T6 |
| T9 | Gate documentation + migration guide | docs | S | low | T5, T6 |

### T1 — RED test matrix (engine, authoritative derivation)

Author failing tests in `tests/test_gates_topology.py` covering **all six**
operator-required regression dimensions:

1. **Independent numerically adjacent DAG roots** — two roots with no explicit
   edges (fixture mirroring 148-S/149-S) both derive `predecessor_source: "none"`
   and are not blocked by numeric inference.
2. **Explicit dependency chains** — linear explicit chain blocks correctly with
   `predecessor_source: "explicit"`.
3. **Closure evidence only for actual explicit predecessors** — closure evidence
   is demanded for an explicit predecessor and **never** for a
   numerically-adjacent non-predecessor.
4. **Converging DAGs** — two explicit predecessors converging on one successor;
   every explicit predecessor is evaluated.
5. **Missing/invalid dependency data** — unresolvable/malformed dependency IDs
   fail closed, never silently drop a predecessor.
6. **Backward-compatibility / migration** — `unsequenced_shipment: warn` (default)
   passes with provenance; `block` restores the legacy blocking posture.

Tests must fail against current `main` for the stated reason.

### T2 — Engine change

Derive predecessors exclusively from `blocking_predecessor_ids`; add
`predecessor_source` to every `shipment_readiness` `details` payload (blocked and
passed); implement the `UNSEQUENCED_SHIPMENT` migration signal and its config
switch; retire `_prior_shipment_id` as a claim-blocking input. Confirm in the task
record whether the still-unfixed forward-dependent suppression defect is rendered
moot; if not, record a follow-up rather than silently fixing it.

### T3 — Test migration (explicitly not deletion)

Each of the 5 `ImplicitNumericPredecessorTests` cases is migrated to an equivalent
explicit-DAG or migration-state assertion preserving its encoded safety intent.
Any case with no equivalent is documented with rationale in the task record.
Bulk deletion is forbidden.

### T4/T5 — Advisory alignment

T4 authors RED tests asserting `dag-readiness` and `pre_claim` cannot report
contradictory readiness for the same shipment on the closure-evidence dimension
(the exact `163-S` divergence), plus advisory labelling and `next_eligible`
disambiguation. T5 implements via a **shared** derivation/closure helper consumed
by both gates.

### T6 — CLI output

Surface `predecessor_source` and `selected_predecessor_ids` in `--json` and human
output; assert in `tests/test_gate_pipeline_topology_cli.py`.

### T7 — `163-S` closure-evidence defect

Diagnose why `docs/closure/162-S-*-post-merge-closure.md` is absent while `162-S`
is archived/shipped. Remediate by authoring the missing closure evidence **or** by
correcting the reader's archived-predecessor handling — whichever the evidence
supports. **Must not weaken the closure gate** to make the symptom disappear.

### T8/T9 — Coupled documentation

Templates, policies, and installed dogfood copies updated together; Orchestrator
and Ship shipment-sequencing text must match the new gate contract (operator
requirement 5). T9 adds the migration guide for workspaces relying on numeric
sequencing.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Silent fail-open for prior numeric-reliant workspaces | `UNSEQUENCED_SHIPMENT` signal + opt-in strict mode + migration guide (T9) |
| Advisory/authoritative divergence recurs | Shared helper (T5), not parallel logic |
| Loss of encoded safety knowledge | T3 migrates rather than deletes |
| `163-S` premise error propagating | Correction recorded §1; T7 scoped separately |
| Template/installed-copy drift | T8 updates both in one task |

## 6. Quality Criteria

* Every behaviour change has a RED test landing before implementation.
* `pre_claim` remains sole claim authority in code, output, templates, and docs.
* No unresolved `{{VARIABLE}}` in touched templates; markdownlint clean (P-008).
* Gate output provenance is deterministic and auditable.
* Engine, CLI, templates, installed dogfood copies, and docs ship together.

## 7. Hardening Assessment

Blast radius is elevated: this changes the **sole claim authority** for every
shipment in every autoharness-managed workspace, alters CLI output contracts,
introduces a new config surface, and carries cross-workspace migration impact.
It also supersedes a documented intentional safety behaviour.

**Requires plan hardening: yes**

## Plan Hardening

Performed 2026-09-12 (Stage, `claude-opus-5`/`anthropic`/`high`) per P-006, because
§7 concluded `Requires plan hardening: yes`.

### H1 — Reinforcing context pulled

* `docs/compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md`
* `docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`
  (records a **verified but uncommitted** fix, still unfixed on `main`)
* `docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`
* Template sequencing surfaces confirmed by grep:
  `templates/agents/_orchestrator.agent.md.tmpl` (L312, L314, L339, L341),
  `templates/agents/_ship.agent.md.tmpl` (L172–175, L200–201, L224–225, L235),
  and the installed dogfood copies `.github/agents/_orchestrator.agent.md` and
  `.github/agents/_ship.agent.md`.
* `templates/policies/workflow-policies.md.tmpl` contains **no** `pre_claim` or
  `PREDECESSOR_` token. **Correction to §2**: the policy template is therefore
  *not* a confirmed edit surface. T8 must verify before editing and must not
  manufacture a change there to satisfy the plan.

### H2 — Hardened failure modes

| ID | Failure mode | Hardening |
|---|---|---|
| F1 | T2 lands provenance only on the blocked path, leaving passes unattributable | `predecessor_source` is REQUIRED on **both** blocked and passed `shipment_readiness` payloads; T1 asserts it on a passing case |
| F2 | `UNSEQUENCED_SHIPMENT` default flips every existing DAG root to blocked | Default is `warn`; `block` is opt-in; T1 case 6 asserts **both** modes |
| F3 | Advisory alignment reimplements closure logic, re-diverging later | T5 MUST consume the shared `closure_complete` reader; a parallel implementation is a review-blocking defect |
| F4 | T3 deletes safety cases under cover of "migration" | T3 must enumerate all 5 cases with per-case disposition; unmigratable cases need written rationale |
| F5 | T7 "fixes" `163-S` by weakening the closure gate | Explicitly forbidden; remedy must be evidence-authoring or reader correction, never gate relaxation |
| F6 | Retirement silently inherits the unfixed forward-dependent defect | T2 must **prove** moot-ness by test, not assert it; if not moot, record follow-up |
| F7 | Config key added without schema validation | T2 must validate `gates.pipeline_topology.unsequenced_shipment` against an enum and fail closed on invalid values |
| F8 | Installed dogfood copies drift from templates | T8 updates template **and** installed copy in the same task; width isolation is preserved because both are documentation-class edits |

### H3 — Explicit non-goals (scope fences)

* Does **not** change branch-naming authority (`86498B64`, separate).
* Does **not** alter `--force` override semantics; `--force` remains
  human-authorized, shipment-specific, and audited — never agent-issued.
* Does **not** make `dag-readiness` authorizing under any configuration.
* Does **not** modify backlogit; dependency data is already correct.

### H4 — Rollback posture

The change is behaviour-flagged: setting
`gates.pipeline_topology.unsequenced_shipment: block` restores the legacy
blocking posture for unsequenced shipments without a code revert. Provenance
fields are additive to output and safe to ignore by older consumers.

### H5 — Residual risk accepted

Workspaces with *no* explicit `blocks` edges anywhere will see all shipments
become claimable in default `warn` mode. This is the intended contract change,
is signalled by `UNSEQUENCED_SHIPMENT` provenance, and is documented in the T9
migration guide. Operators wanting the old posture set `block`.

**Hardening complete. Plan is ready for `plan-review`.**
