---
title: "DAG-authoritative predecessor derivation for the pipeline-topology pre_claim gate"
description: "Decision to make explicit backlogit `blocks` dependencies the sole source of predecessor derivation in `pipeline-topology --phase pre_claim`, replacing the implicit numeric-adjacency heuristic with a four-state declared-root contract that is fail-closed without deadlocking legitimate DAG roots, and aligning `dag-readiness` advisory output with the same model."
doc_type: decision
source: docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
date: 2026-09-12
status: decided
deciders: operator, Stage
revision: 7
revision_note: "PR review-fix cycle 1 (staging PR #448, Copilot review threads, 2026-09-13) — supersession notes added in place; the prior analysis bodies are preserved unchanged as historical record. Thread PRRT_kwDORzpWpM6h3Tgb: D6's operator authorization (force pre_claim for 173-S only, at most three times, token PREDECESSOR_NOT_SHIPPED, predecessor 172-S) STANDS, but its assumption that the ORCHESTRATOR AND SHIP execute those forced invocations (U0/U1/U2) is RETRACTED as not executable — no installed agent contract passes --force, both halt on exit 1/2, and --force is stateless; the executable replacement is BOOTSTRAP-A (one-time operator-run entry) plus BOOTSTRAP-B (future-facing product grant mechanism, tasks 165.011-T/165.012-T), authoritative in the 173-S record and plan §H6, together with the branch-vantage and 9-to-11-item manifest corrections. Thread PRRT_kwDORzpWpM6h3Tgi: D3's absolute 'writes nothing, persists nothing' claim is narrowed to no backlog mutation and no migration-state/ledger write, with the unconditional, observational, fail-open pipeline-topology telemetry emission explicitly allowed. PR REVIEW-FIX CYCLE 2 (staging PR #448, 2026-09-13) — further supersession notes added in place; all prior analysis bodies again preserved unchanged as historical record, and EVERY G2/G3/G4 reference anywhere in this document (including the D1 state table, the case-coverage table, and the risk tables) is historical only. Thread PRRT_kwDORzpWpM6h3frF: D1's three-probe genesis rule (G2 shipped-terminal / G3 sole-extant-nonterminal / G4 abandoned) is RETRACTED AS STILL FAIL-OPEN because the shipment status enum includes `blocked`, which appears in none of the three probes; it is replaced by the SOLE-RECORD rule — genesis only when the candidate is the only shipment record across all live and archived records regardless of status or provenance, with absent/empty/non-string/unparseable/unrecognized status counting as disqualifying fail-closed and an enumeration failure raising. The conclusions of the historical analysis (cardinality-1 genesis, archived shipped history disqualifies, abandoned-only history disqualifies, populated-but-never-shipped disqualifies, dag-root always passes, one shared snapshot) are PRESERVED AND STRENGTHENED, not reversed; the shared fact drops from three probes to one count. Authoritative text is plan §3.1. Thread PRRT_kwDORzpWpM6h3fq1: BOOTSTRAP-A B4's reverse-the-claim instruction is REMOVED as unexecutable (no active->queued transition exists in backlogit) and replaced by halt-with-173-S-active plus explicit operator remediation, with the supported and verified active->abandoned transition as the only alternative and no promise of requeue. Thread PRRT_kwDORzpWpM6h3fqf: BOOTSTRAP-B's at-most-once bound gains a concrete durable atomic mechanism (O_EXCL exclusive-create consumption record claimed before the force, audit emitted from the claimed record, fail-closed contention/replay/malformed, no TTL, grant-digest binding, operator-only recovery, per-workspace-clone scope bound), authoritative in 165.011-T Deliverable 6 and plan §T10/§H5. Neither the operator authorization, the three-invocation sizing, nor the 173-S-only binding is changed. Prior revision 4-5 notes retained in git history. PR REVIEW-FIX CYCLE 3 (staging PR #448, three same-contract-surface Copilot threads, 2026-09-13; annotations only, no decision reversed). Thread PRRT_kwDORzpWpM6h3ttS: the D1 genesis banner's claim that ``blocked`` is a member of the shipment status enum is RETRACTED — the current vocabulary is {queued, active, shipped, abandoned} and ``blocked`` is malformed legacy data; the fail-open finding and the sole-record replacement both stand, and ``blocked`` splits by location (live raises at reader time, archived counts as disqualifying). Thread PRRT_kwDORzpWpM6h3ttV: D6's BOOTSTRAP-A step B6 direct Ship invocation is SUPERSEDED as not executable (Ship Work Intake step 3 runs pre_claim unconditionally) and replaced by a checkpoint-mediated handoff; B0-B5 and D6's authorization are unaffected. Thread PRRT_kwDORzpWpM6h3ttF touches 165.011-T only and lands no deliberation change. Prior revision 4-6 notes retained in git history."
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

**Source status corrected in review-fix cycles 2–3.** That investigation was
recorded in `docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`.
Cycle 1 removed every reference to it because the file was untracked, which left
the stash record `AF2890B7` and the cycle-1 session memory pointing at a path no
reader could resolve — durable artifacts referencing a non-durable file. Cycle 2
committed the document so the reference resolves and the supersession is auditable
against the text it supersedes. **Cycle 3 made the committed copy self-contained**:
its frontmatter now declares its own local path and `doc_type: bug`, and its
transfer note now names its external provenance explicitly
(`softwaresalt/backlogit#438`, plus the source commit and source path, labelled as
*source-workspace* references that do **not** resolve in this repository) rather
than describing itself as living at a `docs/scratch/` path it no longer occupies.
The **analysis body is unchanged** and its historical meaning is preserved; only
self-locating metadata and provenance framing were corrected. The document is a
historical record only: it is not a design input, and where it conflicts with this
decision, this decision governs. Every finding below is independently re-derived
from committed sources (production code, committed tests, committed
`docs/compound/` learnings, and committed backlog records) and cites them directly,
so no conclusion here *depends* on that document.

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

> **SUPERSEDED — PR review-fix cycle 2 (staging PR #448, thread
> `PRRT_kwDORzpWpM6h3frF`, 2026-09-13).** The three-probe formulation below
> (`G2`/`G3`/`G4`) is **retracted as still fail-open** and is replaced by a single
> **SOLE-RECORD** rule: genesis holds only when the candidate has no `blocks` edges
> and no `dag-root` label **and** is the **only shipment record in the workspace**,
> live and archived counted together, **regardless of status or provenance**. The
> defect: G2/G3/G4 each enumerated statuses — G3 enumerated nonterminal states as
> `queued`/`active` only, G2 covered shipped-terminal only, G4 abandoned only — so
> **any value outside those three enumerations appeared in none of them**, and a
> workspace holding such a record plus an edge-less candidate
> satisfied all three probes and returned `genesis`, an unearned pass. Enumerating
> statuses is fragile by construction: every future vocabulary member silently
> re-opens
> the same hole. Counting **records** is status-agnostic and cannot be widened by a
> new status. A record whose status is absent, empty, non-string, unparseable, or
> unrecognized (including an unrecognized `archived_status`) **counts as
> disqualifying, fail closed**; an enumeration failure raises rather than concluding
> sole-extancy from a partial read.
>
> > **ENUM CORRECTION — PR review-fix cycle 3 (thread `PRRT_kwDORzpWpM6h3ttS`,
> > 2026-09-13).** The cycle-2 banner above originally illustrated this defect with
> > a `blocked` shipment and asserted "the shipment status enum is {`queued`,
> > `blocked`, `active`, `shipped`, `abandoned`}". **That assertion is false and is
> > retracted.** The current shipment status vocabulary is exactly {`queued`,
> > `active`, `shipped`, `abandoned`} (`_VALID_LIVE_SHIPMENT_STATUSES`,
> > `topology.py` L35; backlogit declares four `ShipmentStatus` constants), and
> > `blocked` on a shipment is **malformed legacy data**. The fail-open finding and
> > the sole-record replacement both **stand**, and the hole was *wider* than
> > described. `blocked` also **splits by location**: a live record raises
> > `BacklogUnavailableError` at reader time and reaches no verdict; an archived
> > `archived_status: blocked` record counts as disqualifying and the candidate
> > resolves to `unsequenced`. The **conclusions** of the analysis below are
> preserved and strengthened, not reversed — genesis remains **cardinality-1**,
> archived shipped history still disqualifies, abandoned-only history still
> disqualifies, a populated-but-never-shipped workspace still disqualifies, and
> `dag-root` still passes in every one of those workspaces. The shared-snapshot
> requirement in the closing paragraph also survives, and is **strengthened**: the
> shared fact drops from three probes to **one** sole-record count, strictly
> lowering divergence risk. The authoritative statement of the rule is plan §3.1;
> the body below is retained verbatim as the historical reasoning that produced it.

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

**Label parsing needs its own validator, and the tuple is retained (review-fix
cycle 2, refined in cycle 3).** The reader must parse `labels` with a
**labels-specific** fail-closed validator, *not* with the existing
`_tuple_of_str`. Verified: `_tuple_of_str` (`topology.py` L331) validates every
member against `_ARTIFACT_ID_PATTERN` (`^\d+(?:\.\d+)*-[A-Z]+$`) and raises
`BacklogUnavailableError` on any non-match. `dag-root` does not match that
pattern, so reusing that function would make **every labelled shipment record** —
including `173-S`, whose labels are `[dag-root, topology-gate]` — a hard read
failure across the whole gate. The fail-closed *discipline* (absent field is fine;
present-but-wrong-shaped container raises; malformed member raises; never coerce
or drop) is what carries over; the artifact-ID *syntax* does not.

`ShipmentState` **retains the validated, immutable `labels` tuple** rather than
collapsing it to a boolean, and root classification is **derived** from that tuple
by exact, case-sensitive membership. Keeping the tuple preserves the evidence
behind the classification, so output can show which labels were read rather than
only the verdict.

**Declaration authority — what it is, and what it is not (narrowed in cycle 3).**
Declaring a root is an operator/Stage act performed on backlog data. Ship **must
not** self-declare a root to unblock its own claim.

The declaration's force is that it is a **version-controlled, review-gated
statement inside the repository trust boundary**: applying the label produces a
committed diff, that diff passes through the same review path as any other change,
and `predecessor_source: declared_root` names the state on every payload so each
pass is attributable after the fact.

It is therefore **auditable but not mechanically permission-enforced**, and it is
**not a security boundary**. Any actor able to commit to the repository can apply
the label, and the gate neither detects nor prevents that; enforcing it mechanically
would require a backlogit-side permission model that this decision explicitly does
not build (D2 adds no surface, and the scope fences exclude modifying backlogit).
The prohibition on Ship self-declaring is an **agent-contract rule carried in the
agent instructions**, enforced by review and audit rather than by the gate. No
claim is made that the declaration has no escape hatch — within the repository
trust boundary it is a convention backed by review and provenance, and that is the
whole of its strength.

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
  the retired heuristic *would* have inferred, and the remediation options
  available (record the real `blocks` edge, or declare the shipment a root).
* `_prior_shipment_id` survives **only** as this audit report's input. It is
  never a claim input again.
* The audit reports the **raw** numerically-adjacent candidate and must **not**
  inherit the reverse-dependency suppression predicate. That predicate is the
  source of the three recorded defect cycles (Finding 4) and of the non-uniform
  fail-open (Finding 5); in an advisory report it would silently omit candidates
  the operator needs to see. This is asserted by test.

Operators run the audit once, act on it with ordinary backlogit commands, and the
workspace is migrated. No workspace is left depending on an inference.

**The audit is a pure report (review-fix cycle 3; narrowed in PR review-fix cycle
1, thread `PRRT_kwDORzpWpM6h3Tgi`).** It performs **no backlog mutation** and **no
migration-state or ledger write**, and owns no durable artifact or file format.
*(The cycle-3 wording here read "it writes nothing, persists nothing". That
absolute is **false and retracted**: `_gate_pipeline_topology_command` emits an
ordinary tool-telemetry event unconditionally on every run of every phase when
telemetry is enabled. That emission is allowed, unchanged, observational, and
fail-open, and is never read back as authorization or state.)* The cycle-2
requirement for a
"durable, append-only migration ledger" is **withdrawn**, together with the field
that would have recorded the remediation an operator *later* chose — a decision
that has not occurred at audit time. Building a ledger would have given a phase
whose defining property is that it does not mutate its own write path and its own
storage format, and would have created a second source of truth about backlog
state that can itself drift from the backlog.

**Rollback ordering (unchanged in force, re-sourced in cycle 3).** Migration
mutates **backlog data** — `blocks` edges recorded and `dag-root` labels applied.
A revert of the engine change does **not** undo those mutations, and the reverted
numeric engine would then read the migrated edges as real explicit predecessors,
producing a state that existed in neither the before nor the after configuration.
The record that makes data rollback possible is the **version-controlled commit
history** of the backlog records the operator edits: those migration commits and
their diffs show precisely which edges and labels were added and to which records,
and they are reversible by ordinary git operations. Rollback is consequently
**ordered**: revert backlog data first using those commits/diffs, then revert the
engine — never the reverse. Where migration was performed by hand and never
committed, the rollback claim is explicitly narrowed to manual reconstruction from
record history.

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

**`FD0CCB42` owns closure-evidence naming exclusively (review-fix cycle 3).** No
task in `165-F`/`173-S` may discover, read, evaluate, reuse, or assert parity over
closure evidence, and no acceptance criterion in the shipment may reference it.
Cycle 2 still left two footholds — a read-only `closure_complete` reuse inside the
shared helper (D5/T5) and a closure-variant dimension in the parity matrix (T4) —
and both are **removed**. A descoped surface that this shipment still consumes and
tests is not descoped: it would make `173-S` an installed consumer of the very
producer/consumer contract `FD0CCB42` must be free to redefine, forcing that work
to negotiate compatibility with a shipped dependent it never agreed to.
`pre_claim`'s own pre-existing closure check on the `explicit` path is untouched
and stays exactly where it is.

**Closure posture of `173-S` itself (verified, cycle 3).** Independently of the
above, `173-S` closes via **per-item `SAFE_CLOSE`** — a supported close path, and
**not** a blocker. Verified by read-only execution of
`classify_shipment_close_path` against the live workspace, which returns
`ClosePath.SAFE_CLOSE` with the reason naming `165.007-T` and `165.010-T` as
descendants of feature member `165-F` lying outside the manifest. `CASCADE` is
**unavailable by design**: it would require re-adding both archived tasks to the
manifest, which this decision (D4) and the cycle-2 merge forbid. The two tasks keep
their provenance and their off-manifest status — archived, not reparented, not
re-added, not moved under an invented holding feature. Any claim that `173-S`
cannot be closed, or that both close paths are impossible, is **false and is
retracted**; `SAFE_CLOSE` is the final closure strategy for this shipment.

### D5 — Advisory parity across every derivation state

`dag-readiness` remains advisory and non-authorizing, and must model **all four**
D1 states through the **same shared derivation helper** `pre_claim` uses. In
particular a `unsequenced`-blocked shipment must never be reported `next_eligible`
or placed in `ready_set` while `pre_claim` blocks it, and a `declared_root` must
never be reported blocked while `pre_claim` passes it. Parity is asserted as a full
matrix over the four derivation states, not sampled — consistent with
`docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`,
which records that a tie-break/ordering test can pass vacuously when its fixture
cannot distinguish the outcomes.

**Parity covers derivation state only (review-fix cycle 3).** The cycle-1/2 phrase
"plus the closure-evidence dimension" is **removed**. The shared helper is a
derivation helper; it does not wrap or re-expose `closure_complete`, and no parity
assertion in this feature concerns closure evidence. That dimension belongs
exclusively to `FD0CCB42` (D4).

`pipeline-topology --phase pre_claim` remains the **SOLE** claim authority under
every configuration and in every state.

### D6 — Bootstrap disposition for `173-S` (durable, shipment-specific)

> **SUPERSEDED IN PART — PR review-fix cycle 1 (staging PR #448, thread
> `PRRT_kwDORzpWpM6h3Tgb`, 2026-09-13).** The **operator authorization** recorded
> in this section stands: forcing `pre_claim` for `173-S` only, at most three
> times, bound to token `PREDECESSOR_NOT_SHIPPED` and predecessor `172-S`, is
> still the authority under which `173-S` is entered. What is **retracted** is the
> assumption about **who executes those forced invocations**. The U0/U1/U2
> mapping below assigns them to the **Orchestrator and Ship**, and no installed
> agent contract can perform them: neither agent passes `--force` to
> `autoharness gate pipeline-topology`, both halt on exit 1/2, and `--force` is
> stateless, so an operator force does not change the verdict an agent's own later
> unforced run computes. Two further errors are corrected downstream: validity
> condition 3 below names the **Stage branch** as the required HEAD, but
> `pre_claim` short-circuits on `branch_ownership` before `shipment_readiness`, so
> a Stage-branch run blocks on `BRANCH_MISMATCH` and never reaches
> `PREDECESSOR_NOT_SHIPPED`; and condition 3's "9-item manifest" is superseded by
> the 11-item manifest this cycle records. The executable replacement is
> **BOOTSTRAP-A** (a one-time operator-run entry path, B0–B6) and **BOOTSTRAP-B**
> (the product grant mechanism `173-S` ships as `165.011-T`/`165.012-T`, which
> applies to **future** migrations only and cannot retroactively authorize
> `173-S`'s own claim). The authoritative, current text is the `173-S` shipment
> record's BOOTSTRAP DISPOSITION section and plan §H6. **The analysis below is
> preserved unchanged as the historical record of why the grant was sized at three
> invocations; do not execute it as written.**
>
> > **B6 SUPERSESSION — PR review-fix cycle 3 (thread `PRRT_kwDORzpWpM6h3ttV`,
> > 2026-09-13).** BOOTSTRAP-A's final step **B6** — "operator invokes Ship
> > directly against an already-`active` `173-S`" — is **retracted as not
> > executable**. Ship's Work Intake **step 3 runs `pre_claim` unconditionally** on
> > a fresh invocation, before any already-active state is interpreted
> > (`_ship.agent.md` L226–257), and Ship's step-6
> > `expected_status: queued` "(or `active` if already claimed)" parenthetical
> > governs only the step-6 argument and confers **no** authority over step 3. B6 is
> > replaced by a **checkpoint-mediated** handoff: the operator creates a
> > ship-owned `schema_version: 1` / `agent: ship` / `status: active` checkpoint via
> > `backlogit checkpoint create --state-dump`, invokes Orchestrator Step 0.0b
> > recovery, explicitly selects it and confirms restore, and Ship resumes from the
> > recorded post-claim cursor instead of fresh Work Intake. **B0–B5 and decision
> > D6's authorization are unaffected.** Current text: `173-S` BOOTSTRAP
> > DISPOSITION and plan §H6.
>
> **AMENDED — PR review-fix cycle 2 (threads `PRRT_kwDORzpWpM6h3fq1` and
> `PRRT_kwDORzpWpM6h3fqf`, 2026-09-13).** Two further corrections land on the
> replacement surface named above, not on the historical body below.
> (1) **BOOTSTRAP-A B4** previously instructed the operator to *reverse the claim*
> on a non-zero `post_claim`. That step is **removed as unexecutable**: at this
> HEAD `backlogit shipment` exposes only `add`, `claim`, `create`, `get`, `list`,
> `return-blocked`, `ship` — there is no `unclaim`/`release`/`abort`, and `queued`
> is not reachable from `active`. The executable contract is to **halt with `173-S`
> still `active`** and require explicit operator remediation: either diagnose and
> converge (re-run B4 unforced until it exits 0, then resume at B5) or use the
> supported and **verified** `active` → `abandoned` transition, which is
> **terminal, not a requeue**. No artifact may promise automatic reversal.
> (2) **BOOTSTRAP-B's at-most-once property** — the "at most once per named site"
> bound the grant surface depends on — now has a **defined durable mechanism**
> rather than an undefined "not already consumed" predicate: an exclusive-create
> (`O_EXCL`) per-grant/per-label consumption record claimed **before** the force
> under the gitignored `.autoharness/gates/bootstrap-grant-consumption/` tree, with
> the audit emitted from the claimed record, fail-closed contention/replay/malformed
> handling, no TTL, grant-digest binding, operator-only recovery, and an honestly
> stated **per-workspace-clone** scope bound. The authoritative text is `165.011-T`
> Deliverable 6 and plan §T10/§H5. Neither amendment changes the operator
> authorization, the three-invocation sizing, or the `173-S`-only binding recorded
> below.

`173-S` is a genuine DAG root: it declares no `blocks` edge, and the urgent
contract work it carries is independent of the queued `163-S → 164-S → 165-S →
166-S → 168-S → 167-S` documentation chain and of `169-S`..`172-S`.

Under the **currently shipped** code, `173-S` is edge-less, so `_prior_shipment_id`
synthesises `172-S` as its predecessor; `172-S` is queued and unshipped, so
`pre_claim` blocks `173-S` with `PREDECESSOR_NOT_SHIPPED`. The shipment that fixes
the defect is blocked *by the defect*.

**Disposition (operator-authorized 2026-09-12, re-scoped in review-fix cycle 2,
corrected in review-fix cycle 3):** **exactly three** audited `pre_claim --force`
invocations for **`173-S` only**, to break the bootstrap cycle.

**Why three, not one or two.** Cycle 1 recorded a *single-use* grant, which is
**unsatisfiable as written**: the Ship agent's claim protocol runs
`--phase pre_claim` **twice** before the claim — once **before** branch/worktree
creation (`_ship.agent.md` L227–229) and again **immediately before** the claim to
narrow the TOCTOU window (L254–255), with the claim gated on *both* runs passing
(L258). Cycle 2 corrected that to two, but counted only Ship's runs and **missed
the gate that runs first**: the Orchestrator evaluates `--phase pre_claim` against
the candidate shipment as a **route-to-Ship eligibility check, before Ship is
invoked at all** (`_orchestrator.agent.md` L239–241). Under a two-use grant the
Orchestrator's own gate would have been unauthorized, so `173-S` would have blocked
at the pipeline's very first gate and never reached Ship — or the Orchestrator
would have silently consumed an authorization written for a run Ship had not yet
made, which is exactly the unaudited reinterpretation `--force` discipline exists
to prevent. The grant is therefore stated as **exactly three**, mapped to the three
invocations that actually occur against `173-S`.

**Authorized invocations (exhaustive).**

| # | Invoked by | Invocation point |
|---|---|---|
| U0 | **Orchestrator** | `pre_claim` route-to-Ship eligibility check, **before Ship is invoked** (L239–241) |
| U1 | Ship | `pre_claim` run **before** branch/worktree creation (L227–229) |
| U2 | Ship | `pre_claim` run **immediately before** `backlogit_claim_shipment` (L254–255) |

**Not covered.** The Orchestrator's **cursor-advance** eligibility check
(`_orchestrator.agent.md` L261–263) evaluates `{next_shipment_id}` — a *different*
shipment — and is therefore outside this grant entirely. It never consumes one of
the three invocations.

**Per-invocation validity conditions.** All must hold at the moment of *that*
invocation; any one failing voids the authorization:

1. The **only** blocking token in the payload is `PREDECESSOR_NOT_SHIPPED`.
2. The inferred predecessor is **exactly `172-S`**.
3. The current reviewed/staged `HEAD` is the Stage correction commit under which
   this authorization was recorded, **and** the `173-S` manifest matches the
   reviewed 9-item manifest exactly.
4. **No other** topology, check, closure, or secrets violation is present —
   including `PRECLAIM_ACTIVE_SHIPMENT_PRESENT`, a non-zero active-shipment count,
   `SHIPMENT_STATE_INCONSISTENT`, an unresolvable shipment id, any closure-evidence
   block, or any secrets finding.
5. The force is recorded as an **audit event** naming the invocation (U0/U1/U2),
   the observed payload, the blocking token, the inferred predecessor, the `HEAD`
   SHA, and decision D6 as its authorization source.

**Expiry.** The authorization expires immediately upon the earlier of (a) the
successful claim of `173-S`, or (b) **any** mismatch against conditions 1–4 at any
invocation. On expiry-by-mismatch the invoking agent **halts** and returns to the
operator; it must not retry, must not force again, and must not reinterpret a
mismatch as an equivalent case.

**A fourth invocation is not authorized.** If the post-claim `CLAIM_NOT_OBSERVED`
retry path re-runs `--phase pre_claim` before reclaiming (`_ship.agent.md`
L282–283), the force authority is already **exhausted** — the grant exists to reach
the claim and is consumed by it. That run is evaluated **without** `--force`; if it
blocks, Ship halts for a fresh operator decision. **Post-claim retry is never
authorized under this grant.**

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
| Rollback assumed to be code-only, leaving migrated edges/labels behind | Medium | D3 mandatory data-first rollback ordering against the operator's version-controlled migration commits/diffs; narrowed claim where migration was never committed |
| Ship self-declares `dag-root` to unblock itself | Medium | D1 declaration authority is operator/Stage; the label is a committed, diffable, review-gated record and `declared_root` provenance makes every such pass attributable; agent templates state the prohibition. **Not mechanically enforced** — accepted, see D1 |
| Advisory/authoritative divergence reappears on a new dimension | Medium | D5 shared **derivation** helper consumed by both gates; full parity matrix over the four derivation states |
| Audit surface inherits the suppression defect | Medium | D3 requires raw candidate reporting, asserted by test |
| A read-only audit acquires a durable write path and becomes a second source of truth | Medium | D3 removes the ledger; the audit reports only, and git history is the migration record |
| Scope creep into closure evidence or branch resolution | Medium | D4 descope to `FD0CCB42` with **exclusive** ownership — no reuse, no parity cell, no acceptance criterion; `86498B64` fenced out |

## Quality Criteria

* Test-first: every behaviour change lands with a failing test before the change,
  and genuinely-new behaviour is distinguished from characterization of existing
  behaviour rather than faked as "RED".
* Every task ends with a green suite — no task may leave the repository red for a
  successor task to repair.
* Regression coverage for: independent numerically adjacent DAG roots; explicit
  dependency chains; converging DAGs; malformed/unresolvable dependency data
  failing closed (a **characterization** test — that behaviour already exists);
  malformed label data failing closed (a genuine **expected failure** — labels are
  not validated today); and all four D1 derivation states, with each of the three
  genesis disqualifiers (G2 archived shipped history, G3 a second extant
  nonterminal shipment, G4 abandoned-only history) asserted independently rather
  than through one composite fixture. The pre-existing "closure evidence demanded
  only for actual explicit predecessors" case is retained solely as a
  characterization lock on untouched behaviour; no new closure-evidence
  requirement, evaluation, or parity assertion is introduced anywhere (D4).
* `pre_claim` remains sole claim authority in code, output, templates, and docs.
* Engine, CLI output, templates, installed dogfood copies, and documentation move
  together within this shipment.

## Model Routing

Stage route: `claude-opus-5` / `anthropic` / `high` (propagated to inherited
skills). Non-dark run.
