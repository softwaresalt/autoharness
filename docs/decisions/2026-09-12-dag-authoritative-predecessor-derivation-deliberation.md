---
title: "DAG-authoritative predecessor derivation for the pipeline-topology pre_claim gate"
description: "Decision to make explicit backlogit `blocks` dependencies the sole source of predecessor derivation in `pipeline-topology --phase pre_claim`, replacing the implicit numeric-adjacency heuristic with a four-state declared-root contract that is fail-closed without deadlocking legitimate DAG roots, and aligning `dag-readiness` advisory output with the same model."
doc_type: decision
source: docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
date: 2026-09-12
status: decided
deciders: operator, Stage
revision: 3
revision_note: "Review-fix cycle 2 — genesis narrowed to a non-fail-open sole-extancy rule (D1), bootstrap re-scoped to exactly two audited forced pre_claim invocations (D6), original intake bug report committed verbatim as the durable source artifact, rollback re-posed as data-ordered with a migration ledger (D3)."
source_bug_report: docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md
stash_ids:
  - AF2890B7
related_stash_ids:
  - 86498B64
  - 9B582824
  - 97B28746
  - 50434138
deferred_scope_expansions:
  - FD0CCB42
---

# DAG-Authoritative Predecessor Derivation for `pipeline-topology pre_claim`

## Problem Frame

The autoharness gate binary derives a shipment's claim-blocking predecessors in
`src/autoharness/gates/topology.py::_shipment_readiness_check` from **two**
sources unioned together:

1. `ShipmentState.blocking_predecessor_ids` — the explicit backlogit `blocks`
   DAG edges (the documented dependency protocol).
2. `_prior_shipment_id()` (`topology.py` L1433) — an **implicit numeric-adjacency**
   heuristic that, when no explicit predecessor exists, substitutes the nearest
   lower-numbered `{N}-S` shipment as a synthetic predecessor.

The operator has directed (2026-09-12) that explicit DAG dependencies become the
authoritative sequencing source, because the numeric heuristic "is consistently
causing problems in this and other workspaces."

### Historical context (the original intake, now a committed source)

An earlier in-workspace investigation of this behaviour recommended a
**presentation-only** remedy — relabel the advisory gate, surface the
authoritative outcome, disambiguate `next_eligible` — and explicitly classified
removal of the numeric fallback as a *future* contract-change option rather than
the presumed fix. Operator product direction on 2026-09-12 **supersedes that
recommendation**.

**Source status corrected in review-fix cycle 2.** That investigation was
recorded in `docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`.
Cycle 1 removed every reference to it because the file was untracked, which left
the stash record `AF2890B7` and the cycle-1 session memory pointing at a path no
reader could resolve — durable artifacts referencing a non-durable file. Under
operator authorization, that document is now **committed verbatim and
unmodified** as the intake record, so the reference resolves and the supersession
is auditable against the text it supersedes. The document is a historical record
only: it is not a design input, and where it conflicts with this decision, this
decision governs. Every finding below is independently re-derived from committed
sources (production code, committed tests, committed `docs/compound/` learnings,
and committed backlog records) and cites them directly, so no conclusion here
*depends* on that document.

## Research Findings

All findings were reproduced against committed sources in this workspace on
2026-09-12.

### Finding 1 (CRITICAL — corrects the triggering framing)

The framing that reached Stage stated the gate blocked `163-S` because it
*inferred* archived `162-S` as a numeric predecessor. **This is factually
incorrect.**

```text
$ backlogit dep list 163-S
163-S → 162-S (blocks)                      # EXPLICIT DAG edge

$ Get-Content .backlogit/queue/163-S.md
dependencies:
    - 162-S                                  # EXPLICIT, recorded in frontmatter

$ autoharness gate pipeline-topology --mode agent --shipment 163-S \
      --phase pre_claim --json
"token": "PREDECESSOR_CLOSURE_INCOMPLETE",
"details": { "predecessor_id": "162-S", "closure_complete": null }
```

`162-S` is an **explicit** `blocks` predecessor of `163-S`. Because
`_prior_shipment_id()` only appends a synthetic predecessor when it is *not
already present* (`if prior_id and prior_id not in predecessor_ids`, L1576), and
the numerically adjacent shipment here **is** `162-S`, the numeric heuristic is a
**no-op** for `163-S`.

**Consequence: removing the numeric fallback would NOT unblock `163-S`.**

### Finding 2 — the actual cause of the `163-S` block (now descoped)

`163-S` is blocked by `PREDECESSOR_CLOSURE_INCOMPLETE`.
`FilesystemTopologyReaders.closure_complete()` (`topology.py` L654–658) globs
`docs/closure/{shipment_id}-*-post-merge-closure.md`. The closure artifact for
`162-S` **exists** and is committed — `docs/closure/2026-09-11-162-s-154-f-closure.md`
(commit `c6ed877b`) — but it is written under a **different naming contract** than
the one the gate reads.

The drift point is exact: every shipment from `134-S` through `161-S` has a
`{ID}-{FEAT}-post-merge-closure.md` artifact, matching the gate's glob. `162-S`
is the **first** shipment closed under the newer producer convention documented at
`.github/skills/operational-closure/SKILL.md:23`
(`docs/closure/{YYYY-MM-DD}-{slug}-closure.md`). Neither the date prefix nor the
`-closure.md` suffix can match `{ID}-*-post-merge-closure.md`. The producer's
naming changed; the consumer's glob never did.

This is a **producer/consumer contract defect**, structurally unrelated to
predecessor derivation. See decision **D4** below: it is descoped from this
feature and captured as deferred scope expansion **FD0CCB42**.

### Finding 3 — the advisory contradiction, precisely located

`dag-readiness` places `163-S` in `ready_set`; `pre_claim` blocks it. Both gates
**agree** on the edge `163-S → 162-S`. They diverge because `pre_claim` applies a
requirement `dag-readiness` does not model at all: closure evidence.
`_dag_all_predecessors_finished` (L1873) tests only shipped-terminal status.

The divergence is therefore an **advisory-parity** defect: two code paths model
different subsets of the same contract. Deleting the heuristic does not fix it;
only modelling the same inputs in one shared derivation path does.

### Finding 4 — prior learnings strongly favour retirement (confidence: high)

Retrieved from `docs/compound/`:

* `2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md`
* `2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`

Together these record **three successive correctness defects in the same
heuristic**: a multi-hop reverse-dependency false PASS; an opposite-direction
false NEGATIVE introduced by the fix for it; and a third iteration restricting
suppression to numerically *lower* declarants. The second learning is still
marked **"unfixed on `main`"**.

The recurring failure mode is **directional numeric reasoning**: each defect came
from getting the *direction* of a numeric comparison wrong in a predicate whose
numbers carry no semantic meaning. That is the strongest argument for retirement,
and it also constrains the replacement: the replacement must not reintroduce any
claim-affecting numeric comparison.

### Finding 5 — the current heuristic is itself a silent fail-open

`_prior_shipment_id` returns `None` — disabling the fallback entirely for the
whole target — whenever any numerically lower shipment declares the target as its
dependency (L1458). The "safety" heuristic is therefore already silently absent
for an arbitrary subset of shipments. Its protection is **not uniform**, so
"it currently provides dependable fail-closed sequencing" is false.

### Finding 6 (review-fix cycle 1) — a blocking mode is not a legacy mode

The first-round design offered `gates.pipeline_topology.unsequenced_shipment:
block` as a switch that "restores legacy behaviour". It does not. Legacy
behaviour blocked an edge-less shipment **only when a numerically lower shipment
existed and was unshipped**; a genuine first/root shipment passed. A flat `block`
policy blocks **every** edge-less shipment unconditionally, including every
legitimate DAG root, with **no** in-contract way to ever become claimable. That
is not a compatibility mode — it is a deadlock, and it makes intentional roots
unrepresentable. The replacement contract below (D1) therefore distinguishes
*declared* roots from *unaudited* edge-less shipments instead of treating all
edge-less shipments identically.

## Options Evaluated

### Option A: Presentation-only fix

Label `dag-readiness` advisory, surface `pre_claim` outcome, disambiguate
`next_eligible`. Leave numeric derivation intact as the claim authority.

### Option B: Hard removal

Delete `_prior_shipment_id`, derive predecessors exclusively from
`blocking_predecessor_ids`, delete the numeric test class. Every edge-less
shipment becomes claimable immediately.

### Option C: DAG-authoritative + workspace config switch (SUPERSEDED in cycle 1)

Explicit edges authoritative; edge-less shipments pass with provenance under a
`warn` default, with an opt-in `block` mode via a new
`.autoharness/config.yaml` key. **Rejected on review** — see Finding 6 (the
`block` mode deadlocks all roots) and D2 (the config key was avoidable).

### Option D: DAG-authoritative + declared-root contract (ADOPTED)

Explicit edges are the sole claim-blocking authority. An edge-less shipment is
resolved by a **four-state** derivation over data that already exists in the
backlog records — no new configuration surface — with an explicit, one-time audit
path for previously-implicit sequencing.

## Trade-off Comparison

| Criterion | A: Presentation-only | B: Hard removal | C: Config switch | D: Declared root |
|---|---|---|---|---|
| Satisfies operator direction | No | Yes | Yes | Yes |
| Unblocks `163-S` | No | No | No | No (separate defect, FD0CCB42) |
| Eliminates the fragile heuristic from the claim path | No | Yes | Yes | Yes |
| Backward-compat safety | High (no change) | **Low — silent fail-open** | Split: `warn` fails open, `block` deadlocks | High — fail-closed with a bounded, self-service remedy |
| Intentional DAG roots representable | N/A | Yes (but indistinguishable from unaudited) | **No under `block`** | Yes — explicitly declared and auditable |
| New configuration/schema surface | None | None | **New config key + schema version + template + install/tune + parity tests** | **None** |
| Reintroduces numeric reasoning into claims | Yes (keeps it) | No | No | No |
| Auditability of sequencing | Poor | Poor | Good | Best — provenance names the reason |
| Migration path for other workspaces | N/A | None | Declarative but fail-open by default | One-time audit phase + explicit declaration |

## Decision

**Adopt Option D — DAG-authoritative predecessor derivation with a four-state
declared-root contract.**

### D1 — The derivation contract (authoritative, `pre_claim`)

`predecessor_ids := ShipmentState.blocking_predecessor_ids` (explicit `blocks`
edges only). `_prior_shipment_id` is **never** consulted on the claim path.

When that set is empty, exactly one of three terminal states applies. The four
states are total, mutually exclusive, and each emits a distinct
`predecessor_source` value:

| State | Condition | Outcome | `predecessor_source` |
|---|---|---|---|
| **Explicit** | `blocking_predecessor_ids` is non-empty | Evaluate every explicit predecessor under the existing ambiguity, shipped-terminal, and closure-evidence checks | `explicit` |
| **Declared root** | No edges **and** the shipment record declares itself a root | **Pass** | `declared_root` |
| **Genesis** | No edges, no declaration, and the workspace satisfies **all** of G2/G3/G4 below | **Pass** (bootstrap) | `genesis` |
| **Unsequenced** | No edges, no declaration, and any genesis condition fails | **Block**, token `UNSEQUENCED_SHIPMENT` | `unsequenced` |

#### The genesis rule (narrowed in review-fix cycle 2)

Cycle 1 defined genesis as "the workspace has no shipped-terminal shipment". That
is **insufficient and fail-open**, and it is replaced. Genesis now requires **all**
of the following, in addition to the candidate having no edges and no `dag-root`:

* **G2 — no shipped-terminal shipment exists anywhere**, live *or* archived.
* **G3 — the candidate is the SOLE EXTANT NONTERMINAL shipment**: no other
  shipment record exists in a nonterminal state (`queued` or `active`), live or
  archived.
* **G4 — no `abandoned` shipment record exists anywhere**, live or archived.

**Why absence of shipped history is insufficient.** A workspace can hold a dozen
queued shipments and have shipped nothing — this repository was in exactly that
shape for its first weeks. Under the cycle-1 rule, *every* edge-less shipment in
such a workspace returns `genesis` and **passes simultaneously**, including
shipments that are numerically and semantically downstream of other pending work.
That is an unearned pass, in precisely the fail-open direction this feature exists
to close, and it would be indistinguishable at the gate from a genuine bootstrap.

**Why later-numbered candidates cannot silently pass.** G3 makes `genesis` a
**cardinality-1** state: it is a property of a workspace holding exactly one
shipment record, so it can never be true for two candidates at once, and it stops
being available the moment a second shipment record of any kind exists. A
later-numbered edge-less candidate in a populated workspace therefore has no
genesis path at all — it is `unsequenced` and blocks until someone records intent.
The bootstrap escape is available exactly once in a workspace's life, when there
is provably nothing to sequence against.

**Why `abandoned` needs its own clause.** `abandoned` is terminal but **not
shipped**, so G2 alone would admit a workspace whose entire history is abandoned
shipments. Such a workspace has demonstrably been sequenced before; treating it as
a fresh install would re-open the same unearned pass through a narrower door. G4
closes it.

**Case coverage.**

| Workspace | Genesis? | Result for an edge-less, undeclared candidate |
|---|---|---|
| Exactly one shipment record, nothing else | yes | pass `genesis` |
| Several `queued` shipments, nothing ever shipped | **no** (G3) | block `unsequenced` |
| Shipped history exists only as archived records | **no** (G2) | block `unsequenced` |
| Only an `abandoned` record in history | **no** (G4) | block `unsequenced` |
| Any of the above, candidate carries `dag-root` | n/a | pass `declared_root` |

G2/G3/G4 are **workspace-level facts computed once per evaluation** from a single
snapshot and shared by both gates (see D5) — three independent probes taken
separately would be three chances to observe divergent snapshots.

Rationale for each property:

* **No fail-open.** In any workspace with shipping history — precisely the
  workspaces that could have relied on implicit numeric sequencing — an edge-less
  shipment is **blocked** until someone records intent. No previously-blocked
  claim silently becomes a pass.
* **No deadlock.** The block is not terminal: it names a bounded, self-service
  remedy that is an ordinary backlog data operation (add the real `blocks` edge,
  or declare the shipment a root). Intentional roots are therefore representable
  *and* claimable — the Finding 6 defect is resolved.
* **Bootstrap is defined, and bounded.** A workspace holding exactly one shipment
  record has nothing to sequence against, so its **first** shipment passes as
  `genesis` and a fresh install can never deadlock on its first claim. From the
  second shipment record onward the escape closes and intent must be recorded.
* **No numeric comparison on the claim path**, in any state — which is what
  Finding 4's directional-numeric lesson demands.

**Root declaration surface.** The declaration is the label `dag-root` on the
shipment's own backlogit record, read from frontmatter by the existing shipment
reader. This was **empirically validated** before adopting it: `backlogit update
173-S --labels "dag-root,topology-gate"` persists `labels:` on a shipment record,
so the surface exists today and needs no backlogit change.

**Label parsing needs its own validator (review-fix cycle 2).** The reader must
parse `labels` with a **labels-specific** fail-closed validator, *not* with the
existing `_tuple_of_str`. Verified: `_tuple_of_str` (`topology.py` L331) validates
every member against `_ARTIFACT_ID_PATTERN` (`^\d+(?:\.\d+)*-[A-Z]+$`) and raises
`BacklogUnavailableError` on any non-match. `dag-root` does not match that
pattern, so reusing that function would make **every labelled shipment record** —
including `173-S`, whose labels are `[dag-root, topology-gate]` — a hard read
failure across the whole gate. The fail-closed *discipline* (absent field is fine;
present-but-wrong-shaped container raises; malformed member raises; never coerce
or drop) is what carries over; the artifact-ID *syntax* does not.

**Declaration authority.** Declaring a root is an operator/Stage act performed on
backlog data. Ship **must not** self-declare a root to unblock its own claim; that
is the same authority boundary that keeps `--force` human-authorized. Because
`predecessor_source: declared_root` appears in gate output, every such pass is
auditable after the fact.

### D2 — No new configuration or schema surface

The declared-root contract is carried entirely by data that already exists in the
backlog records. Therefore this feature adds **no** `.autoharness/config.yaml`
key, and consequently no root-schema change, **no new immutable versioned schema
mirror**, no `schema_contracts.py` current-version resolution work, no
`templates/harness-config.yaml.tmpl` change, no install/tune preservation logic,
no dogfood config change, and no config parity/validation tests.

This is a deliberate simplification demanded by review finding 7. It also avoids
the failure mode recorded in
`docs/compound/2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md`
(a versioned schema mirror mutated in place, three occurrences) by adding no
schema surface to mutate. The cheapest way to honour immutable-mirror versioning
is not to need a new schema version at all.

### D3 — One-time audit/migration contract

Previously-implicit sequencing is migrated by **audit**, not by a fail-open
default:

* A read-only, **non-authorizing** audit surface is added as a new phase of the
  existing gate command (`--phase audit_sequencing`). It never blocks, never
  authorizes, and never mutates.
* For every edge-less shipment it reports: the current derivation state
  (`declared_root` / `genesis` / `unsequenced`), the numeric-adjacency candidate
  the retired heuristic *would* have inferred, and the remediation choice (record
  the real `blocks` edge, or declare the shipment a root).
* `_prior_shipment_id` survives **only** as this audit report's input. It is
  never a claim input again.
* The audit reports the **raw** numerically-adjacent candidate and must **not**
  inherit the reverse-dependency suppression predicate. That predicate is the
  source of the three recorded defect cycles (Finding 4) and of the non-uniform
  fail-open (Finding 5); in an advisory report it would silently omit candidates
  the operator needs to see. This is asserted by test.

Operators run the audit once, act on it with ordinary backlogit commands, and the
workspace is migrated. No workspace is left depending on an inference.

**Migration ledger and rollback ordering (review-fix cycle 2).** Migration
mutates **backlog data** — `blocks` edges recorded and `dag-root` labels applied.
A revert of the engine change does **not** undo those mutations, and the reverted
numeric engine would then read the migrated edges as real explicit predecessors,
producing a state that existed in neither the before nor the after configuration.
The audit therefore emits a **durable, append-only migration ledger** recording,
per shipment, the pre-migration edge set and label set, the derived state, the raw
candidate, and the remediation chosen. Rollback is consequently **ordered**:
revert backlog data first using the ledger, then revert the engine — never the
reverse. Where a workspace was migrated by hand and has no ledger, the rollback
claim is explicitly narrowed to manual reconstruction from record history.

### D4 — The closure-evidence defect is DESCOPED from this feature

Finding 2's producer/consumer naming defect is **removed** from `165-F` / `173-S`.
It is a different contract surface (closure-evidence authoring and reading) with a
different owner, different tests, and a design question of its own — reconciling
two naming conventions plus deciding compatibility for the `134-S`..`161-S`
historical corpus.

Disposition: captured as **DEFERRED SCOPE EXPANSION `FD0CCB42`** (kind `bug`,
priority `high`), requiring its own deliberation and its own work unit. Task
`165.007-T`, which previously carried this remediation, is **archived** with a
forward reference to `FD0CCB42` and removed from the `173-S` manifest.

Constraints carried into that entry, not weakened here:

* The closure gate **must not** be weakened, relaxed, or bypassed.
* A competing/duplicate `162-S` closure artifact under the old naming **must not**
  be authored. `docs/closure/2026-09-11-162-s-154-f-closure.md` already exists and
  is correct; the defect is the unreconciled contract, not a missing document.

### D5 — Advisory parity across every derivation state

`dag-readiness` remains advisory and non-authorizing, and must model **all four**
D1 states plus the closure-evidence dimension through the **same shared helper**
`pre_claim` uses. In particular a `unsequenced`-blocked shipment must never be
reported `next_eligible` or placed in `ready_set` while `pre_claim` blocks it, and
a `declared_root` must never be reported blocked while `pre_claim` passes it.
Parity is asserted as a full state matrix, not sampled — consistent with
`docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`,
which records that a tie-break/ordering test can pass vacuously when its fixture
cannot distinguish the outcomes.

`pipeline-topology --phase pre_claim` remains the **SOLE** claim authority under
every configuration and in every state.

### D6 — Bootstrap disposition for `173-S` (durable, shipment-specific)

`173-S` is a genuine DAG root: it declares no `blocks` edge, and the urgent
contract work it carries is independent of the queued `163-S → 164-S → 165-S →
166-S → 168-S → 167-S` documentation chain and of `169-S`..`172-S`.

Under the **currently shipped** code, `173-S` is edge-less, so `_prior_shipment_id`
synthesises `172-S` as its predecessor; `172-S` is queued and unshipped, so
`pre_claim` blocks `173-S` with `PREDECESSOR_NOT_SHIPPED`. The shipment that fixes
the defect is blocked *by the defect*.

**Disposition (operator-authorized 2026-09-12, re-scoped in review-fix cycle 2):**
**exactly two** audited `pre_claim --force` invocations for **`173-S` only**, to
break the bootstrap cycle.

**Why two, not one.** Cycle 1 recorded a *single-use* grant. That grant is
**unsatisfiable as written**: the Ship agent's claim protocol runs
`--phase pre_claim` **twice** before the claim — once **before** branch/worktree
creation (`_ship.agent.md` L227–229) and again **immediately before** the claim to
narrow the TOCTOU window (L254–255), with the claim gated on *both* runs passing
(L258). A single-use authorization would either halt Ship at the second gate, or —
worse — invite it to stretch one authorization silently across two invocations,
which is precisely the kind of unaudited reinterpretation `--force` discipline
exists to prevent. The grant is therefore stated as **exactly two**, mapped to the
two invocations that actually occur.

**Authorized invocations (exhaustive).**

| # | Invocation point |
|---|---|
| U1 | `pre_claim` run **before** branch/worktree creation |
| U2 | `pre_claim` run **immediately before** `backlogit_claim_shipment` |

**Per-invocation validity conditions.** All must hold at the moment of *that*
invocation; any one failing voids the authorization:

1. The **only** blocking token in the payload is `PREDECESSOR_NOT_SHIPPED`.
2. The inferred predecessor is **exactly `172-S`**.
3. The current reviewed/staged `HEAD` is the Stage review-fix cycle 2 commit under
   which this authorization was recorded, **and** the `173-S` manifest matches the
   reviewed 9-item manifest exactly.
4. **No other** topology, check, closure, or secrets violation is present —
   including `PRECLAIM_ACTIVE_SHIPMENT_PRESENT`, a non-zero active-shipment count,
   `SHIPMENT_STATE_INCONSISTENT`, an unresolvable shipment id, any closure-evidence
   block, or any secrets finding.
5. The force is recorded as an **audit event** naming the invocation (U1/U2), the
   observed payload, the blocking token, the inferred predecessor, the `HEAD` SHA,
   and decision D6 as its authorization source.

**Expiry.** The authorization expires immediately upon the earlier of (a) the
successful claim of `173-S`, or (b) **any** mismatch against conditions 1–4 at
either invocation. On expiry-by-mismatch Ship **halts** and returns to the
operator; it must not retry, must not force again, and must not reinterpret a
mismatch as an equivalent case.

**A third invocation is not authorized.** If the post-claim `CLAIM_NOT_OBSERVED`
retry path re-runs `--phase pre_claim` before reclaiming (`_ship.agent.md`
L282–283), the force authority is already **exhausted**. That run is evaluated
**without** `--force`; if it blocks, Ship halts for a fresh operator decision.

Unchanged bounds — narrow by construction:

1. It applies to **`173-S` only**. It is not a precedent, not a policy change, and
   confers **no broader force authority** over any other shipment.
2. It does **not** change `--force` semantics, which remain human-authorized,
   shipment-specific, and audited. No agent may self-authorize a force.
3. Ship **must record** the override in the claim evidence and in the shipment's
   PR/closure record, naming this decision (D6) as its authorization source.
4. It is **self-liquidating**: `173-S` has already been declared a root
   (`labels: [dag-root]` on its record), so once `165.002-T` lands, `173-S`
   derives `predecessor_source: declared_root` and passes **natively**, with no
   force, on any subsequent evaluation.

### Scope boundary decisions

* **`pipeline-topology pre_claim` remains the SOLE claim authority.**
* **The closure-evidence defect is OUT of scope** (D4 → `FD0CCB42`).
* **`86498B64` (workspace-driven `implementation_branch`) stays SEPARATE.** Same
  file (`topology.py`), genuinely different contract: *branch naming* authority,
  not *sequencing* authority. Same-file adjacency is not same-contract necessity.
  It is the recommended next unit of work.
* **`9B582824` (cost-per-unit-of-work epic) stays SEPARATE** — broad multi-component
  epic, no contract overlap.
* **`97B28746` / `50434138` (verify-workspace / Ship branch drift) stay SEPARATE**
  as related follow-ups.
* **`58A85283` (file-lock test follow-up) excluded** — unrelated.

## Rejected Alternatives

* **Option A (presentation-only)** — rejected: leaves the defect-generating
  heuristic authoritative and does not satisfy operator direction.
* **Option B (hard removal)** — rejected: correct direction, unsafe execution;
  silently converts previously-blocked claims into passes.
* **Option C (config switch)** — rejected in review-fix cycle 1: its `block` mode
  deadlocks every legitimate DAG root (Finding 6) and its `warn` default is the
  very fail-open Option B was rejected for, so neither setting is a safe resting
  state. It also imposed a config-key surface (schema version, template, install/tune,
  dogfood config, parity tests) that Option D shows was never necessary.
* **A numeric "legacy compatibility mode"** — rejected: any mode that keeps a
  numeric comparison on the claim path preserves exactly the directional-numeric
  fragility of Finding 4 and would have to be deleted again later.
* **Bundling `86498B64`** — rejected: distinct contract surface; bundling inflates
  blast radius and violates width isolation.
* **Treating this as a trivial bug fix** — rejected: it is a contract change to the
  sole claim authority, with documented intentional prior behaviour and
  cross-workspace migration impact.

## Resolved Questions (cycle 1)

1. **Migration default** — RESOLVED by D1. Neither "warn-and-pass" nor flat
   "block": the state is resolved from per-shipment declared intent, so the answer
   is not a global default at all.
2. **Missing closure artifact for `162-S`** — RESOLVED by Finding 2 and D4: the
   artifact is **not** missing; it is unrecognized by the reader's glob. Descoped
   to `FD0CCB42`; no gate weakening, no competing artifact.
3. **Forward-dependent suppression defect** — RESOLVED in direction by D3:
   retirement removes it from the claim path, and the audit path is specified to
   not inherit the suppression predicate at all. The implementation task must still
   **prove** moot-ness on the claim path by test rather than assert it.

## Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Silent fail-open in workspaces relying on numeric sequencing | High | D1 blocks unsequenced shipments in any workspace disqualified from genesis (G2/G3/G4); D3 audit migrates them explicitly |
| A blocking posture deadlocks legitimate roots | High | D1 declared-root state + genesis bootstrap; remedy is one backlog command and is named in the block message |
| Genesis is granted too broadly and becomes a back-door fail-open | High | Genesis narrowed in cycle 2 to sole-extancy (G3) plus archived-inclusive shipped-history (G2) and abandoned-history (G4) probes; each disqualifier is asserted independently by test |
| `labels` parsing reuses the artifact-ID validator and hard-fails every labelled record | High | D1 requires a labels-specific fail-closed validator; a positive reader-level anti-regression test asserts `[dag-root, topology-gate]` parses cleanly |
| Rollback assumed to be code-only, leaving migrated edges/labels behind | Medium | D3 migration ledger plus mandatory data-first rollback ordering; narrowed claim where no ledger exists |
| Ship self-declares `dag-root` to unblock itself | Medium | D1 declaration authority is operator/Stage; `declared_root` provenance makes every such pass auditable; agent templates state the prohibition |
| Advisory/authoritative divergence reappears on a new dimension | Medium | D5 shared helper consumed by both gates; full state-matrix parity tests |
| Audit surface inherits the suppression defect | Medium | D3 requires raw candidate reporting, asserted by test |
| Scope creep into closure evidence or branch resolution | Medium | D4 descope to `FD0CCB42`; `86498B64` fenced out |

## Quality Criteria

* Test-first: every behaviour change lands with a failing test before the change,
  and genuinely-new behaviour is distinguished from characterization of existing
  behaviour rather than faked as "RED".
* Every task ends with a green suite — no task may leave the repository red for a
  successor task to repair.
* Regression coverage for: independent numerically adjacent DAG roots; explicit
  dependency chains; closure evidence demanded only for actual explicit
  predecessors; converging DAGs; malformed/unresolvable dependency data failing
  closed; and all four D1 derivation states, with each of the three genesis
  disqualifiers (G2 archived shipped history, G3 a second extant nonterminal
  shipment, G4 abandoned-only history) asserted independently rather than through
  one composite fixture.
* `pre_claim` remains sole claim authority in code, output, templates, and docs.
* Engine, CLI output, templates, installed dogfood copies, and documentation move
  together within this shipment.

## Model Routing

Stage route: `claude-opus-5` / `anthropic` / `high` (propagated to inherited
skills). Non-dark run.
