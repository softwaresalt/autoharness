---
chunk_strategy: h1-h2-h3
description: "autoharness advisory-semantics mismatch: dag-readiness is advisory-only visibility/reporting whose ready_set/cursor does NOT authorize a claim, while pipeline-topology --phase pre_claim is the sole claim authority and intentionally blocks 148-S/149-S via the implicit numeric-adjacency predecessor. Differing results are NOT competing claim authorities; the gap is that advisory readiness output can mislead operators when it does not prominently label its non-authorizing model and the implicit predecessors pre_claim may add"
doc_type: guide
docline:
  author: Stage
  date: 2026-09-11
  status: draft-for-transfer
ingested_at: "2026-09-11T00:00:00Z"
schema_version: "1.0"
source: docs/scratch/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md
title: "autoharness advisory-semantics mismatch — dag-readiness advisory output can mislead because pipeline-topology pre_claim is the sole claim authority"
---

# autoharness advisory-semantics mismatch — `dag-readiness` advisory output can mislead operators because `pipeline-topology pre_claim` is the sole claim authority

> **Transfer note & lifecycle.** This document was authored in the `backlogit`
> workspace but describes a defect that belongs to the **separate `autoharness`
> workspace** (the `autoharness` gate binary). It is written to be self-contained
> so it can be copied verbatim into the `autoharness` workspace as a bug report /
> issue. No fix is applied in `backlogit`; `backlogit` carries only this
> documentation and a tracking stash entry (`6D53A33F`) that references this path.
>
> **This file lives under `docs/scratch/`, which is intentionally ephemeral.**
> Per `.github/instructions/context-efficiency.instructions.md`, scratch files
> may be archived/compacted once they age past the retention window, so this path
> is **not** durable and may stop resolving. That placement is deliberate: this is
> a **temporary transfer artifact** whose only job is to be **manually copied into
> the `autoharness` workspace** before the next scratch compaction/archive cycle.
> **Do not treat this path as durable provenance, and do not rely on it surviving.**
> Durable provenance is preserved independently of this file:
>
> - **PR #438** in `softwaresalt/backlogit` carries this document and the stash
>   entry in version history (recoverable even after scratch compaction).
> - A prior **source-workspace** analysis lives at
>   `docs/decisions/2026-09-06-queued-shipment-ordered-scope-decision.md`
>   (section 4, "Topology gate: numeric-predecessor behavior", and follow-up 7a).
>   That document is **historical source-workspace analysis, superseded by this
>   report's verified upstream semantics** (see §1 and §9): it predates the
>   verification that `dag-readiness` is advisory-only and that
>   `pipeline-topology --phase pre_claim` is the sole claim authority. It is
>   **not authoritative** for claim decisions and is cited for provenance and
>   history only.
>
> If you are reading this after transfer, copy it into a durable `autoharness`
> location; do not link back to this `docs/scratch/` path as a stable reference.

## 1. Summary

Two sibling gates in the `autoharness` binary answer different questions for the
same shipment, and the **advisory** gate's output can mislead operators into
believing a shipment is claimable when the **authoritative** claim gate blocks it:

- `dag-readiness` reads the explicit shipment **`blocks` DAG** and reports
  `148-S` (and `149-S`) in its `ready_set`. **`dag-readiness` is advisory
  visibility/reporting only.** Its `ready_set`/cursor/`next_eligible` output is an
  explicit-DAG analysis; it does **NOT** authorize a shipment claim.
- `pipeline-topology --phase pre_claim` is the **sole BLOCK/claim authority**. It
  reports the *same* shipments as **`blocked` with `PREDECESSOR_NOT_SHIPPED`**,
  because it applies an **implicit numeric-adjacency predecessor** (nearest
  lower-numbered shipment) when no explicit `blocks` predecessor is declared.

**The implicit numeric-adjacency predecessor is an intentional current
`autoharness` safety behavior, not an accidental bug.** It is preserved on
purpose — see upstream commit `14c32ef879fd7d67a8ac6b0dfd55dad056ba34d2`, which
*retains* the numeric-adjacency implicit-predecessor behavior (while fixing a
separate fail-open suppression bug), and
`tests/test_gates_topology.py::ImplicitNumericPredecessorTests`, which documents
the heuristic as intentional: it catches an **unstated-but-intended sequential
predecessor** when no shipment declares dependencies. This report therefore does
**not** assert that numeric-predecessor logic is itself a defect.

**These differing results do NOT create competing claim authorities.** There is
exactly one claim authority — `pipeline-topology --phase pre_claim` — and it is
authoritative. `dag-readiness` and `pre_claim` answer *different questions*
(explicit-DAG readiness analysis vs. claim gating), so their differing answers are
expected and not a contract conflict. Concretely: **`148-S` is NOT claimable**
under the gate-compliant path unless **either** its implicit predecessor (`147-S`)
reaches the shipped terminal state, **or** an explicit, operator-authorized,
audited `pre_claim --force` override is issued for that specific shipment. A
`dag-readiness` `ready_set` entry never changes that.

**The actionable follow-up is an advisory-semantics / presentation-model gap.**
Because `dag-readiness` presents a shipment as "ready" without prominently
explaining that it is advisory-only and that `pre_claim` may add an implicit
numeric predecessor, an operator (or agent) can misread advisory readiness as
claim authorization. The remedy belongs in `autoharness` and is about making the
advisory output honest about its model and non-authorizing status, and surfacing
the authoritative `pre_claim` outcome — **not** about forcing both gates to return
identical claim answers (see §7).

## 2. Environment

- Component: `autoharness` gate binary (`pipeline-topology`, `dag-readiness`).
- Surface: `autoharness gate ...` CLI, `--mode agent`.
- Backlog source: a `backlogit` workspace whose shipment artifacts carry explicit
  `blocks` dependency edges.
- **Upstream evidence that the numeric fallback is intentional (verified):**
  - Commit `14c32ef879fd7d67a8ac6b0dfd55dad056ba34d2` intentionally **preserves**
    the numeric-adjacency implicit-predecessor fallback and fixes a fail-open
    suppression bug (it hardens, rather than removes, the heuristic).
  - `tests/test_gates_topology.py::ImplicitNumericPredecessorTests` asserts the
    heuristic is intentional — it exists to catch an unstated-but-intended
    sequential predecessor when **no** shipment declares dependencies.
- Reproduction below uses a placeholder `<WORKSPACE>` for the backlog workspace
  path; substitute the local checkout path. No machine-specific or secret values
  are required to reproduce.

## 3. Reproduction

Assume a backlog whose shipment `blocks` DAG has two independent numeric-adjacent
roots (neither blocks the other), for example `148-S` and `149-S`, plus a linear
track ending at `147-S`:

```text
137-S (SHIPPED) -> 138-S -> 139-S -> ... -> 147-S      (linear track)
148-S            (independent ROOT — no explicit predecessor)
149-S            (independent ROOT — no explicit predecessor)
   (148-S, 149-S) -> 150-S
   (148-S, 149-S) -> 151-S
```

> **Workspace binding.** `backlogit dep list` and `pipeline-topology` are
> **cwd-relative** — they inspect the workspace of the current directory. Only
> `dag-readiness` accepts an explicit `--workspace`. So the portable `sh` blocks
> below bind the workspace explicitly with `cd <WORKSPACE>` before every
> cwd-relative command, and pass `--workspace <WORKSPACE>` to `dag-readiness`.
> Without this, the same commands copied into another checkout would silently
> inspect the wrong workspace.

### 3.1 Confirm the true dependency edges (backlogit)

```sh
cd <WORKSPACE>

# Forward edges — what 148-S depends on. Expect NONE (148-S is a DAG root).
backlogit dep list 148-S

# Reverse edges — what depends on 148-S. Expect only 150-S and 151-S.
backlogit dep list 148-S --reverse
```

Observed:

- `backlogit dep list 148-S` (forward) → **no incoming/forward dependencies**
  for `148-S` (empty result): it has zero explicit `blocks` predecessors.
- `backlogit dep list 148-S --reverse` →

  ```text
  150-S → 148-S (blocks)
  151-S → 148-S (blocks)
  ```

  only `150-S` and `151-S` depend on `148-S`.

### 3.2 Confirm the explicit-DAG ready-set (autoharness dag-readiness)

```sh
autoharness gate dag-readiness --workspace <WORKSPACE> --json
```

Observed: `ready_set` includes `148-S` (e.g. `[141-S, 148-S, 149-S, 152-S]`);
`148-S` is reported ready under the explicit-DAG model.

### 3.3 Run the authoritative claim gate (autoharness pipeline-topology pre_claim)

```sh
cd <WORKSPACE>

autoharness gate pipeline-topology --mode agent --shipment 148-S --phase pre_claim --json
```

## 4. Observed vs. expected

### Observed

- `pre_claim 148-S` → `blocked: true` with `PREDECESSOR_NOT_SHIPPED`, selecting
  predecessor **`147-S`** via the implicit numeric-adjacency predecessor. `147-S`
  is *not* an explicit `blocks` predecessor of `148-S` (which has zero explicit
  predecessors); it is the numerically-adjacent ID that the intentional heuristic
  substitutes when no dependency is declared. **This is the authoritative claim
  answer: `148-S` is not claimable while `147-S` is unshipped.**
- `pre_claim 149-S` → `blocked: true`, selecting predecessor **`148-S`** — again
  the implicit numeric-adjacency predecessor, not an explicit edge.
- `pre_claim 138-S` → `blocked: false`, because its numeric neighbor `137-S`
  happens to be shipped (the implicit predecessor coincidentally matches reality).
- `dag-readiness` reports `148-S`/`149-S` in its advisory `ready_set` at the same
  time — advisory-only, and **not** a claim authorization.

The observed *behavior of each gate individually* is consistent with its own
question. `pre_claim` is the authoritative claim gate; `dag-readiness` is an
advisory explicit-DAG analysis. They answer different questions, so they are
**not** in contract conflict. The presentation problem is that advisory readiness
does not label itself as non-authorizing, so it can be misread as claim
authorization.

### Expected (honest advisory presentation — the remedy is an upstream decision, see §7)

- The gate suite already has one claim authority (`pre_claim`); that is correct
  and must not change. The fix is **presentation-model honesty**, not making the
  two gates return identical claim answers.
- `dag-readiness` advisory output must **prominently label its model and
  non-authorizing status** and make clear that `pre_claim` may add an implicit
  numeric predecessor, so an operator can tell *why* a root with a lower-numbered
  neighbor that appears "ready" is nonetheless not claimable. The authoritative
  `pre_claim` outcome should be **surfaced alongside/within** the advisory report.

This report deliberately does **not** assert the "expected" result is
`blocked: false`. The `pre_claim` block on `148-S` behind `147-S` is the
**intended, authoritative** behavior. The advisory `dag-readiness` `ready_set`
entry is not wrong either — it is simply an explicit-DAG analysis that does not
speak to claim authority. The remedy is to make the advisory output say so
prominently (see §7); it is **not** to force the two gates to return identical
claim answers.

## 5. Impact

- **Advisory readiness can be misread as claim authorization.** `dag-readiness`
  presents `148-S`/`149-S` as "ready" without prominently stating that it is
  advisory-only and that `pre_claim` may add an implicit numeric predecessor. An
  operator or agent can mistake the advisory `ready_set`/`next_eligible` for a
  green light to claim, then hit the authoritative `pre_claim` block — or worse,
  reach for an override they did not need.
- **Sequencing intent is invisible in the advisory view.** The intentional
  implicit numeric predecessor (catching an unstated-but-intended predecessor) is
  applied by `pre_claim` but not surfaced by `dag-readiness`, so a DAG-independent
  root looks freely claimable in the advisory view and serialized by the
  authoritative gate with no explanation linking the two.
- **Operator-trust and latency risk from a presentation gap.** Because the
  advisory and authoritative views are not shown together, operators can lose
  trust in the gate suite or make mis-sequenced decisions. This is a
  presentation/model-honesty risk, not evidence that either gate's internal logic
  is broken — and specifically not a competing-claim-authority problem.

## 6. Likely contract boundary (where the remedy belongs)

- The gap is in how the **`autoharness` gate core** *presents* two correctly
  differing answers: the authoritative `pre_claim` predecessor-derivation step
  (explicit `blocks` edges **plus** the intentional implicit numeric-adjacency
  predecessor) and the advisory `dag-readiness` ready-set computation (explicit
  `blocks` edges **only**).
- The remedy therefore belongs in `autoharness`: keep `pre_claim` as the sole
  claim authority and make the advisory `dag-readiness` output **honest about its
  model and non-authorizing status**, surface the authoritative `pre_claim`
  outcome alongside/within the report, and (optionally) model/report implicit
  predecessors as a separate field/view. The specific remedy is the §7 decision.
  This does **not** require both gates to return the same claim answer.
- **No `backlogit` change is required or appropriate.** The dependency data is
  already correct and consistent in `backlogit` (`dep list` and the explicit-DAG
  `dag-readiness` agree). No `backlogit`-side lever (dependency edges, priority,
  or `queue_position`) can change a predecessor that the intentional heuristic
  derives from the shipment ID itself — the presentation remedy is inside
  `autoharness`.

## 7. Requested upstream remedy & acceptance criteria

**This is a follow-up requiring an upstream product/contract decision, not a
settled bug fix.** `pipeline-topology --phase pre_claim` remains the sole claim
authority and the intentional numeric predecessor (commit `14c32ef` +
`ImplicitNumericPredecessorTests`) must **not** be deleted as though it were a
proven accidental bug. The requested remedy is to make the **advisory output
honest and the authoritative outcome visible** — the gates are **not** required
to return identical claim answers.

### Requested remedy (one or more of the following)

- **Label the advisory model and non-authorizing status.** `dag-readiness` output
  must clearly state that it is advisory explicit-DAG analysis and that its
  `ready_set`/cursor/`next_eligible` does **NOT** authorize a claim.
- **Surface the authoritative outcome.** Show the `pipeline-topology --phase
  pre_claim` result (block state + selected predecessor) alongside or within the
  advisory report, so the authoritative answer travels with the advisory one.
- **Model implicit predecessors explicitly (optional).** Represent/report the
  implicit numeric-adjacency predecessor as a separate field or view in the
  advisory output, so an operator can see *why* an apparently-ready root is held.
- **Disambiguate `next_eligible`.** Ensure `next_eligible` (and any cursor
  affordance) cannot be mistaken for claim authorization — e.g. rename, annotate,
  or gate it behind the authoritative `pre_claim` result.

### Numeric-fallback removal is an explicit *future* option, not the presumed fix

Removing or migrating the numeric-adjacency implicit predecessor from `pre_claim`
(so predecessors derive **exclusively** from the explicit `blocks` DAG) remains a
**possible future contract change** — but it is **not** the presumed or requested
fix here. If upstream ever chooses it, it is a deliberate contract change that
must update `ImplicitNumericPredecessorTests` (and any peer fixtures) to the new
contract, document the removed safety behavior, and provide a migration path for
backlogs that relied on implicit sequencing (e.g. require explicit `blocks` edges
where implicit adjacency previously served). Until then, the numeric predecessor
stays and the requested remedy is presentation honesty (above).

### Acceptance criteria

1. **`pre_claim` stays the sole claim authority.** No change makes `dag-readiness`
   (or its `ready_set`/cursor/`next_eligible`) authorize a claim. The two gates
   are **not** required to return identical claim answers.
2. **Advisory output is honest about its model.** `dag-readiness` output labels
   itself advisory explicit-DAG analysis and states it does not authorize claims.
3. **Authoritative outcome is visible.** The `pre_claim` block state and selected
   predecessor (explicit `blocks` edge vs. implicit numeric-adjacency) are
   surfaced alongside/within the advisory report and are auditable.
4. **`next_eligible` cannot be mistaken for authorization.** The cursor/eligibility
   affordance is renamed, annotated, or gated so it reads as advisory only.
5. **Regression coverage for the presentation contract.** Cover the independent
   numeric-adjacent roots fixture (`148-S`/`149-S`: numerically adjacent, both DAG
   roots, neither an explicit predecessor of the other), a convergence case
   (`150-S`/`151-S` depending on both roots), and a linear-track case, asserting
   the advisory output carries the non-authorizing label and the authoritative
   `pre_claim` outcome for each.
6. **If numeric-fallback removal is later chosen:** apply the contract-change
   hygiene above (`ImplicitNumericPredecessorTests` + dependent fixtures/docs
   updated, removed safety behavior documented, migration/back-compat stated).

## 8. Safe interim & gate-compliant paths (until the advisory presentation is fixed)

- **Ordinary gate-compliant path (preferred).** Ship the numeric predecessor
  chain first: claim/ship `147-S` (and the linear track ahead of it) so that
  `pre_claim` on `148-S` clears normally. This requires **no override** and is the
  intended sequencing — the implicit predecessor is satisfied by shipping it.
- **`--force` override (only to claim before the predecessor is shipped).** The
  **only** way to claim `148-S` **before** `147-S` reaches the shipped terminal
  state is an **operator-authorized, audited** `pre_claim --force` override.
- **This override must be explicitly authorized by a human operator for a
  specific, named shipment, and recorded in the audit trail. It must NEVER be
  applied automatically, blanket-enabled, or issued by an agent on its own
  authority.**
- The override is a stopgap for a single known-good claim, not a substitute for
  fixing the advisory presentation. Each use should reference this report and the
  `dag-readiness` evidence showing the shipment is ready under the explicit-DAG
  model (advisory-only).

## 9. Supporting evidence

- **Upstream (autoharness), verified — implicit predecessor is intentional; `dag-readiness` is advisory-only:**
  - Commit `14c32ef879fd7d67a8ac6b0dfd55dad056ba34d2` preserves the
    numeric-adjacency implicit-predecessor behavior (and fixes a separate
    fail-open suppression bug).
  - `tests/test_gates_topology.py::ImplicitNumericPredecessorTests` documents the
    heuristic as intentional (catches an unstated-but-intended sequential
    predecessor when no shipment declares dependencies).
  - Verified upstream semantics: `dag-readiness` is **advisory** visibility/
    reporting only — its `ready_set`/cursor does **not** authorize a claim — and
    `pipeline-topology --phase pre_claim` is the **sole** BLOCK/claim authority.
- **Backlogit-side, read-only:**
  - `backlogit dep list 148-S` (forward): no incoming dependencies;
    `backlogit dep list 148-S --reverse`: only `150-S` and `151-S` depend on
    `148-S`.
  - `autoharness gate dag-readiness --workspace <WORKSPACE> --json`: `ready_set`
    contains `148-S` (advisory-only; ready under explicit-DAG model, not a claim
    authorization).
  - `autoharness gate pipeline-topology --mode agent --shipment 148-S --phase pre_claim --json`:
    `blocked: true`, `predecessor_id: 147-S` (implicit numeric-adjacency
    predecessor, not an explicit `blocks` edge) — the authoritative claim answer.
- **Historical source-workspace analysis, superseded (does not resolve after transfer).**
  A prior analysis exists in the *source* `backlogit` workspace at
  `docs/decisions/2026-09-06-queued-shipment-ordered-scope-decision.md`
  (section 4 "Topology gate: numeric-predecessor behavior" and follow-up 7a). It
  is **historical source-workspace analysis, superseded by this report's verified
  upstream semantics** (advisory `dag-readiness` vs. authoritative `pre_claim`),
  and is **not authoritative** for claim decisions. This path is internal to the
  `backlogit` workspace and will **not** resolve in the `autoharness` workspace;
  it is cited for provenance/history only. This report is self-contained — all
  evidence needed to understand and remedy the advisory-semantics mismatch is in
  sections 1–8 above and does not depend on that document.
