---
title: Pipeline-Topology Gate Reference
description: The deterministic autoharness gate pipeline-topology CLI — DAG-authoritative pre_claim predecessor derivation, the audit_sequencing migration path, pre-claim bootstrap grants, force audit provenance, exit codes, and cross-machine scope limits
doc_type: reference
source: docs/pipeline-topology-gate.md
---

> **Navigation**: [README](../README.md) · [Validation Gates Reference](gates-reference.md) · [DAG Readiness Gate Reference](dag-readiness-gate.md) · [Copilot-Review Merge Gate Reference](copilot-review-gate.md) · [Primitives](primitives.md) · [Tuning Guide](tuning-guide.md)

## Overview

The **pipeline-topology gate** is a deterministic, non-LLM, exit-code-based check
that guards the P-001 (at-most-one-active-shipment) and P-016 (single
implementation worktree/branch) topology invariants across the Stage → Ship
lifecycle.

For shipment sequencing, `pipeline-topology --phase pre_claim` is now
**DAG-authoritative**: it derives predecessors from explicit backlog `blocks`
edges only, then resolves edge-less shipments through a four-state contract with
explicit provenance:

- `explicit`
- `declared_root`
- `genesis`
- `unsequenced`

`dag-readiness` remains **advisory only**. It reuses the same shipment data model,
but it is not a claim authority and it never overrides `pre_claim`.
This contract and the retirement of numeric adjacency are the product decision for
feature `165-F` / shipment `173-S`; see
[`docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md`](decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md),
[`docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md`](plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md),
and the original intake record
[`docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`](bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md).

The gate is still **fail-closed** for its scoped lifecycle phases. A failed
active-shipment invariant, branch mismatch, worktree conflict, malformed live
shipment record, or unmet explicit predecessor **BLOCKS** (exit `1`). The only
non-blocking non-pass outcome remains the read-only retry-required
`CLAIM_NOT_OBSERVED` contract (exit `3`) at `post_claim`.

The **core evaluation path** is read-only: it reads backlog and git state through
injected reader interfaces and derives a result. The CLI has two additive runtime
write paths around that evaluation:

1. operator `--force` appends a force-audit record; and
2. `--bootstrap-grant-invocation` may atomically claim a bootstrap-grant
   consumption record and then append a force-audit record if an exact matching
   grant authorizes the blocked `pre_claim` result.

The gate's active-shipment scan and worktree-uniqueness check are **local to the
current checkout** — see [Cross-Machine Scope Limitation](#cross-machine-scope-limitation).

## The `autoharness gate pipeline-topology` CLI Contract

```bash
autoharness gate pipeline-topology [--mode agent|manual|ci]
                        [--shipment <shipment_id>]
                        [--phase pre_claim|post_claim|lifecycle|ambient|audit_sequencing]
                        [--bootstrap-grant-invocation <label>]
                        [--json] [--force]
```

| Flag | Default | Description |
|---|---|---|
| `--mode <m>` | `manual` | `agent` \| `manual` \| `ci` — see [Modes](#modes). |
| `--shipment <id>` | — | Explicit shipment target. **Required** in `agent` mode, and required in **any** mode whenever `--phase` is `pre_claim`, `post_claim`, or `lifecycle`. Not required for `ambient` or `audit_sequencing`. |
| `--phase <p>` | `ambient` (manual/ci); none (agent) | `pre_claim` \| `post_claim` \| `lifecycle` \| `ambient` \| `audit_sequencing`. **Required** in `agent` mode. `agent` mode accepts only `pre_claim`, `post_claim`, or `lifecycle`; `audit_sequencing` is a manual/CI report phase, not an agent claim/lifecycle phase. |
| `--bootstrap-grant-invocation <label>` | off | Agent-consumable **pre-claim only** bootstrap-grant label: `orchestrator_pre_route`, `ship_pre_branch`, or `ship_pre_claim`. Loads `.autoharness/bootstrap-grants/<shipment_id>.yaml` and forces only on an exact, one-time matching grant. Cannot be combined with `--force`. |
| `--json` | off | Emit the topology gate result as a machine-readable JSON object. |
| `--force` | off | Operator-only audited override of a **BLOCK** (exit `1`) verdict. Does **not** affect a `CLAIM_NOT_OBSERVED` (exit `3`) retry-required result. Semantics are unchanged by the bootstrap-grant feature. |

### Core evaluation vs. runtime writes

The topology engine (`src/autoharness/gates/topology.py`) itself reads backlog and
git state only. Runtime writes happen only around a blocked CLI result:

- `--force` appends `.autoharness/gates/pipeline-topology-force-audit.log`.
- `--bootstrap-grant-invocation` may create or update a gitignored consumption
  record under `.autoharness/gates/bootstrap-grant-consumption/` and then append
  the same force-audit log if the blocked `pre_claim` result exactly matches a
  committed grant.
- `pipeline-topology` telemetry is observational and fail-open. It may append a
  telemetry event on every phase, including `audit_sequencing`, but that
  telemetry is **not** a migration record and does not change the gate verdict.

### The `--shipment <SHIPMENT_ID>` target contract

- **Agent shipment-scoped mode** (`--mode agent`): `--shipment` is **required**.
  Omitting it is fail-closed — exit `2`, never inferred.
- **Manual/CI scoped phases** (`--phase pre_claim|post_claim|lifecycle`):
  `--shipment` is also **required**.
- **Ambient** (`--phase ambient`, default in `manual`/`ci`): target resolution is
  deterministic and implicit:
  1. if exactly one shipment is active, that shipment is the target;
  2. otherwise resolve from the current branch slug (`feat/{slug}` /
     `chore/{slug}`) against known shipment branch aliases;
  3. otherwise there is no target and the gate proceeds in ambient-only,
     existence-guarded mode.
- **Sequencing audit** (`--phase audit_sequencing`): no target is required. The
  phase scans the current workspace's shipment records and renders a read-only
  migration report.

### The `--phase <pre_claim|post_claim|lifecycle|ambient|audit_sequencing>` contract

- **Agent mode** (`--mode agent`): `--phase` is **required** and must be one of
  `pre_claim | post_claim | lifecycle`. `ambient` and `audit_sequencing` are
  rejected in agent mode.
- **Manual/CI mode** (`--mode manual|ci`): `--phase` defaults to `ambient` when
  omitted — **not** `lifecycle`.
- **`audit_sequencing`** is a workspace-wide, advisory report phase. It never
  authorizes a claim, never blocks the gate, and exists to migrate workspaces
  that relied on unstated numeric sequencing.

#### Phase semantics matrix

| Phase | Zero active shipments | Exactly one active, matches target | Exactly one active, does **not** match target (or no target) | Two or more active |
|---|---|---|---|---|
| `pre_claim` | **PASS** — required precondition before a claim | n/a (a claim has not yet happened) | `PRECLAIM_ACTIVE_SHIPMENT_PRESENT` — **BLOCK** | `PRECLAIM_ACTIVE_SHIPMENT_PRESENT` — **BLOCK** |
| `post_claim` | `LIFECYCLE_NO_ACTIVE_SHIPMENT` — **BLOCK** | **PASS** | `LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH` — **BLOCK** | `LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS` — **BLOCK** |
| `lifecycle` | `LIFECYCLE_NO_ACTIVE_SHIPMENT` — **BLOCK** | **PASS** | `LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH` — **BLOCK** | `LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS` — **BLOCK** |
| `ambient` | **PASS** — existence-guarded, non-blocking (no claim to validate) | **PASS** | `AMBIENT_TARGET_REQUIRED_FOR_ACTIVE_SHIPMENT` (no resolvable target) or `AMBIENT_ACTIVE_SHIPMENT_MISMATCH` — **BLOCK** | `AMBIENT_MULTIPLE_ACTIVE_SHIPMENTS` — **BLOCK** |
| `audit_sequencing` | **PASS** — read-only report, no target required | n/a | n/a | n/a |

`post_claim` additionally runs the
[`CLAIM_NOT_OBSERVED` retry-required contract](#the-claim_not_observed-retry-required-contract)
instead of an immediate block when the target is still `queued` with zero active
shipments after a claim attempt.

#### Which lifecycle point passes which phase

| Lifecycle point | Phase |
|---|---|
| Ship: branch/worktree creation (P-011) | `pre_claim` |
| Ship: immediately before claim | `pre_claim` |
| Ship: immediate post-claim verification | `post_claim` |
| Ship: build / PR lifecycle / closure | `post_claim` or `lifecycle` |
| Orchestrator: route-to-Ship eligibility + cursor advance | `pre_claim`, against the candidate/successor shipment ID |
| Local git hooks (`pre-commit`, `pre-push`) | `ambient` |
| CI ambient runs | `ambient` |
| Operator migration audit for edge-less shipments | `audit_sequencing` |

### Modes

| Mode | Behavior |
|---|---|
| `agent` | Fail-closed shipment-scoped invocation. Requires `--shipment` and an explicit scoped `--phase`. Used by Ship and Orchestrator at claim/route/build/PR/closure points. |
| `manual` (default) | Human-invoked (or hook-invoked) check. `--phase` defaults to `ambient`; `--shipment` is optional unless a scoped phase is explicitly passed. `audit_sequencing` lives here. |
| `ci` | Same resolution rules as `manual`, used from CI ambient runs. Detached-HEAD and default-branch fallback behavior is CI-only and preserves fail-closed ownership checks while still allowing GitHub Actions to identify the real branch name. |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | PASS — all checks passed for the resolved phase/target, or an audited `--force`/bootstrap-grant override of a BLOCK. |
| `1` | BLOCK — the active-shipment invariant, branch ownership, worktree uniqueness, shipment readiness, or backlog read failed for the resolved phase/target. |
| `2` | Invalid arguments or invalid gate configuration. |
| `3` | `CLAIM_NOT_OBSERVED` — read-only retry-required outcome. Only reachable at `post_claim` when the target shipment is still `queued` with zero active shipments after a claim attempt. |

## DAG-authoritative predecessor derivation (`pre_claim`)

`pre_claim` is the **sole claim authority**. It does **not** consult numeric
adjacency anymore. For predecessor sequencing it derives from explicit backlog
`blocks` edges only, then annotates the result with `predecessor_source`.

### Four derivation states

| State | Condition | Outcome | `predecessor_source` |
|---|---|---|---|
| Explicit | `blocking_predecessor_ids` is non-empty | Evaluate each explicit predecessor under the existing shipped-terminal / ambiguity / closure checks | `explicit` |
| Declared root | No explicit predecessor edges, and the shipment record carries the `dag-root` label | **PASS** | `declared_root` |
| Genesis | No explicit predecessor edges, no `dag-root`, and the workspace satisfies the sole-record rule below | **PASS** | `genesis` |
| Unsequenced | No explicit predecessor edges, no `dag-root`, and genesis does not apply | **BLOCK** with `UNSEQUENCED_SHIPMENT` | `unsequenced` |

`UNSEQUENCED_SHIPMENT` is the explicit fail-closed token for an edge-less,
undeclared, non-genesis shipment. Its remediation text is closed and intentional:

1. record the real `blocks` edge; or
2. declare the shipment a root.

### Root declaration surface: `labels: [dag-root]`

The root declaration surface is the shipment record's `labels` list. A shipment is
a declared root only when that record already carries the exact label `dag-root`.

`dag-root` is a **version-controlled, review-gated declaration** in backlog data
inside the repository trust boundary:

- it is visible in diffs;
- attributable to a commit and author;
- reviewable like any other committed backlog change; and
- auditable after the fact.

It is **not** mechanically permission-enforced and it is **not** a security
boundary. The implementation does not cryptographically prevent someone from
editing backlog data. The contract is policy and review driven:

- **operator or Stage may apply `dag-root`;**
- **Ship must not self-declare `dag-root` to unblock its own claim.**

That prohibition is real, but it is enforced by workflow policy and review, not by
a separate permission subsystem.

### Genesis is the sole-record rule

Genesis is deliberately narrow. It requires **all** of the following:

1. the candidate has **no explicit `blocks` edges**;
2. the candidate carries **no `dag-root` label**; and
3. the candidate is the **only shipment record in the workspace**.

"Only shipment record" is literal and status-agnostic:

- live and archived shipment records are counted **together**;
- status and provenance do **not** matter to the count; and
- **any other shipment record disqualifies genesis**.

That explicitly includes the current four-value live shipment status vocabulary:

- `queued`
- `active`
- `shipped`
- `abandoned`

It also includes shipment records whose status is malformed or unclassifiable:

- missing status
- empty status
- non-string status
- unrecognized status
- unrecognized `archived_status`

Those records are **not skipped**. They disqualify genesis **fail closed**.

#### `blocked` is malformed legacy data, not a shipment status

Per the current shipped implementation, the live shipment status vocabulary is
exactly `queued`, `active`, `shipped`, and `abandoned`.
`blocked` is **not** a shipment status for this contract. See the correction note
in [`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`](compound/2026-05-07-backlogit-shipment-status-constraints.md).

The two dispositions are intentionally different:

- **Live record with `status: blocked`**: the reader fails closed at read time as
  `BacklogUnavailableError` (`shipment record has a missing or unsupported
  status`). No derivation state is produced at all.
- **Archived record with `archived_status: blocked`**: the record is still counted
  as an existing shipment record, but its archived status is unclassifiable for
  terminal reasoning. That disqualifies genesis, so an otherwise edge-less,
  undeclared candidate resolves to `unsequenced`.

Do **not** add `blocked` to the documented live shipment status list.

### Why the rule counts records instead of enumerating statuses

The rejected "no shipped history" style rule was too weak. In a workspace with
several queued shipments and nothing yet shipped, every one of those shipments
would satisfy "no shipped history" at the same time, so they would all receive an
unearned `genesis` pass. That is exactly the fail-open direction this change was
meant to close.

Counting shipment **records** avoids that hole:

- it is cardinality based, so only one shipment can ever be genesis;
- it is status agnostic, so a future vocabulary change does not silently reopen a
  status-enumeration bug; and
- it treats malformed or unknown records as disqualifying instead of invisible.

### Practical operator consequence

A fresh install's **first** shipment passes as `genesis` and therefore cannot
deadlock. The **second shipment onward** must do one of two things before it can
claim cleanly:

- declare the real `blocks` predecessor edge; or
- carry `dag-root` explicitly.

An edge-less, undeclared, non-genesis shipment blocks as `UNSEQUENCED_SHIPMENT`
until one of those declarations is committed.

## Migration from unstated numeric sequencing (`audit_sequencing`)

Workspaces that previously relied on the retired numeric-adjacency heuristic
migrate through `audit_sequencing`.

Run the audit in manual mode:

```bash
autoharness gate pipeline-topology --phase audit_sequencing --json
```

This phase is a **read-only report**:

- it performs **no backlog mutation**;
- it performs **no migration-state or ledger write**; and
- it may still emit ordinary observational, fail-open `pipeline-topology`
  telemetry, because telemetry emits on every phase and is not a migration record.

For each edge-less shipment the report lists:

- the shipment id;
- its derived state (`declared_root`, `genesis`, or `unsequenced`);
- any `raw_numeric_candidate_ids` the retired heuristic would have guessed;
- the same two remediation options the authoritative gate uses; and
- when relevant, the genesis disqualifier plus the specific disqualifying
  shipment records.

### Required migration procedure

1. Run `audit_sequencing`.
2. Review **every** edge-less shipment the report lists.
3. For each shipment, choose one real declaration:
   - record the actual `blocks` edge; or
   - declare the shipment a root with `dag-root`.
4. **Commit that backlog-data change.**

The commit is the migration record. There is no hidden migration ledger in the
gate.

### Fail-closed posture during migration

In any workspace already disqualified from genesis, an edge-less shipment that has
not been audited and declared blocks as `unsequenced`. That is intentional. The
blocking token names both remedies: record the real `blocks` edge or declare the
shipment a root.

## Removed behavior: numeric adjacency

Older `pre_claim` behavior could synthesize a predecessor from the nearest lower
numeric shipment id when no explicit edge existed. That behavior is retired from
the claim path.

It was removed because repeated defect cycles all traced back to the same root
cause: **directional numeric reasoning** over shipment ids that do not themselves
encode authoritative dependency intent.

The clearest prior defect history is preserved in:

- [`docs/compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md`](compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md)
- [`docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`](compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md)

Those cycles show the same pattern repeatedly:

- a numeric-direction predicate is too narrow;
- the fix overcorrects and becomes too broad; then
- another boundary case appears because the contract still depends on numbers
  rather than declared backlog intent.

`audit_sequencing` preserves the retired numeric candidate only as a migration
hint (`raw_numeric_candidate_ids`). It does **not** re-authorize numeric
sequencing.

## No configuration key, schema version, or install/tune preservation surface

This contract is **per-shipment declared intent in backlog data**. There is no
`.autoharness/config.yaml` key for it, no schema version to track, and nothing
for install/tune to preserve.

The operative declarations live in shipment records themselves:

- explicit `blocks` dependencies; and
- the `dag-root` label when a shipment is intentionally a root.

That keeps the contract on the artifact it governs instead of inventing a second,
parallel configuration surface.

## The `CLAIM_NOT_OBSERVED` retry-required contract

A single stateless read of backlog state cannot distinguish "the claim is merely
delayed" from "the claim genuinely failed" when both present as target `queued`
and zero active shipments. The gate therefore:

- performs exactly one read at `post_claim`;
- returns `CLAIM_NOT_OBSERVED` (exit `3`, `status: retry_required`) rather than
  guessing PASS or BLOCK; and
- leaves convergence to the external caller.

`CLAIM_NOT_OBSERVED` is a first-class token, not a BLOCK variant. `--force` does
not act on it.

## Pre-claim bootstrap grants (future-facing migration surface)

A **bootstrap grant** is a committed, operator-authored authorization for one very
specific blocked `pre_claim` result. It exists for later self-hosted migrations
that need a narrow, reviewable bridge into the new contract.

### Storage and authorship

Bootstrap grants live at:

```text
.autoharness/bootstrap-grants/{shipment_id}.yaml
```

That location is deliberately **outside** the gitignored `.autoharness/gates/`,
`.autoharness/staging/`, and `.autoharness/metrics/` runtime trees, so a grant can
be committed, reviewed, and reverted like other backlog-policy inputs.

A bootstrap grant is:

- **operator-authored**;
- **review-gated**; and
- never authored, edited, or extended by an agent.

No agent may create a grant, modify a grant, broaden its scope, or roll its
constraints forward.

### Exact-match bounds

A grant matches only when **all** bounded fields match exactly:

- one shipment id;
- one expected blocking token;
- one expected predecessor id;
- one manifest digest;
- one closed-set invocation label (`orchestrator_pre_route`, `ship_pre_branch`, or
  `ship_pre_claim`); and
- `pre_claim` phase only.

A missing grant and a present-but-non-matching grant are intentionally
indistinguishable in effect: both leave the original halt in place.

### 173-S did not use this product surface

The grant mechanism is **future-facing** product behavior. It did **not** and
could **not** authorize `173-S`'s own claim. `173-S` entered through the one-time,
operator-run **BOOTSTRAP-A** path, recorded in
[`docs/bootstrap/2026-09-13-173-S-bootstrap-evidence.md`](bootstrap/2026-09-13-173-S-bootstrap-evidence.md),
not through a bootstrap-grant file.

### Full-provenance force audit fields

When a grant matches, the gate converts the blocked result into a forced pass and
appends the ordinary topology force-audit log. The audit payload records full
provenance, including:

- `timestamp`
- `actor`
- `reason`
- `mode`
- `phase`
- `target_shipment_id`
- `token`
- `message`
- `invocation`
- `observed_payload`
- `head_sha`
- `manifest.shipment_id`
- `manifest.items`
- `manifest.digest`
- `blocking_token`
- `inferred_predecessor_id`
- `authorization.source`
- `authorization.decision`
- `authorization.grant_path`
- `authorization.operator`
- `authorization.grant_digest`
- `authorization.consumption_record_path`

For operator `--force`, the same audit surface remains in use. The grant-specific
authorization fields become `null` and `authorization.source` is
`operator_force`. The `--force` flag itself remains operator-only with unchanged
semantics.

## At-most-once grant consumption and its honest scope bound

Bootstrap-grant use is not just matched; it is also **consumed at most once per
workspace clone**.

### Durable exclusive-create record

Before the blocked result is converted into a forced pass, the CLI attempts to
claim an exclusive-create consumption record under the gitignored runtime tree:

```text
.autoharness/gates/bootstrap-grant-consumption/{shipment_id}/{invocation}.json
```

That record is claimed atomically before the force conversion. The audit is then
emitted from the claimed record.

### Operator-visible behavior

- A **second attempt** on the same label fails closed with the ordinary exit `1`.
  The CLI does not retry, wait, or steal the record.
- There is **no TTL** and **no auto-expiry**.
- Editing the grant does **not** reset consumption, because the consumption record
  binds the grant's digest.
- A malformed, unreadable, stale, or mismatched consumption record is treated as
  **consumed** — fail closed. This is the deliberate opposite of malformed-grant
  handling, where a malformed grant behaves like **no grant** and therefore also
  resolves toward **no force**.
- Recovery from a crashed or abandoned claimed record is an **operator-only,
  out-of-band act**. The CLI intentionally offers **no reset flag**.

### Honest scope bound: per workspace clone

At-most-once holds **per workspace clone**, not globally across machines, because
`.autoharness/gates/bootstrap-grant-consumption/` is gitignored runtime state. A
fresh clone starts with no consumption record tree.

That is an intentional bound, compensated by the grant's other exact-match limits:

- `expires_on_claim: true`
- exact-token binding
- exact predecessor binding
- manifest-digest binding
- closed invocation-label binding

A cross-machine once-only guarantee is **not** provided and was deliberately not
invented.

## Bypass / audit

`--force` is an **operator-only** control that converts a BLOCK (exit `1`) verdict
into an exit-`0` pass. It must never be invoked from an agent surface.
Bootstrap-grant forcing uses the same audit log but a different authorization
source.

```text
.autoharness/gates/pipeline-topology-force-audit.log
```

This audit log is **not** the migration record. It is gitignored runtime
telemetry-style evidence of a force decision.

## Opt-in install / activation

The pipeline-topology gate ships as part of the `autoharness` CLI itself. Its
**hook** artifacts remain opt-in:

1. `install-harness` copies the rendered hook scripts into `{workspace}/scripts/`.
2. Activation into `.git/hooks/` (or a custom `core.hooksPath`) is a separate,
   explicit operator step.
3. `tune-harness` tracks hook drift.
4. `verify-workspace` asserts the install/tune wiring.

## Manual-developer compatibility (advisory-degrade mode)

The local hook invocations are **advisory-first by default**: a BLOCK prints a
warning but does not fail the git operation unless the developer explicitly opts
into blocking mode with `AUTOHARNESS_TOPOLOGY_GATE_BLOCKING=true`. CI and Ship's
own `agent`-mode invocations remain the actual enforcement backstop.

## CI topology-check entrypoint (Gate C)

CI uses the same `ambient` topology contract as the local hooks, but without the
local advisory-degrade toggle. A missing `autoharness` binary is a CI
configuration failure, not a warn-and-skip. See
[`docs/pipeline-topology-gate-ci-rollout.md`](pipeline-topology-gate-ci-rollout.md)
for rollout detail.

## Rollback posture

A code-only rollback does **not** restore the pre-migration workspace. Migration
mutates **backlog data**: `blocks` edges added during audit and `dag-root` labels
applied during audit survive any later engine revert.

That matters because the reverted numeric engine still reads real explicit edges.
A migrated workspace rolled back in the wrong order can therefore block claims the
pre-migration engine would previously have allowed.

### What code alone can and cannot reverse

Code alone can reverse these **engine surfaces** with **no orphaned configuration**:

- DAG-authoritative derivation logic
- the additive `predecessor_source` output field
- the `audit_sequencing` phase
- the `UNSEQUENCED_SHIPMENT` token
- the bootstrap-grant CLI surface itself

Code alone does **not** reverse these **data surfaces**:

- `blocks` edges committed into shipment records during migration
- `dag-root` labels committed into shipment records during migration

### The migration record is the operator commit

The gate writes **no migration state** and owns **no ledger**, durable audit
artifact, or persistence subsystem for migration tracking.

Do **not** overstate that as "the gate persists nothing" or "the gate has no
write path at all":

- every phase may emit ordinary, observational, fail-open topology telemetry; and
- `--force` appends the force audit log.

Neither of those is the migration record. The recoverable pre-migration state
lives in the **version-controlled commit(s) and diffs** that added the `blocks`
edges or `dag-root` labels.

### Required rollback ordering

Rollback ordering is mandatory:

1. **revert the backlog-data migration commit(s) first**; then
2. **revert the engine**.

Reverting code first leaves the migrated backlog declarations in place while the
restored numeric engine interprets them as real explicit predecessors.

### If the migration was never committed

If a workspace's migration edits were **never committed**, there is no diff to
revert. Data rollback is manual, and any rollback claim must be narrowed to that
fact.

The preventive rule is simple: **commit the migration as its own reviewable
change**.

## Cross-machine scope limitation

The gate's active-shipment scan and worktree-uniqueness check are **local to the
current checkout**. backlogit provides no workspace-wide claim lock, so the gate
is a deterministic guardrail, not a distributed lock.

The same honest scope bound applies to bootstrap-grant at-most-once consumption:
it is per workspace clone because the consumption tree is gitignored runtime
state.

## Runtime and storage surfaces

| Path | Tracked? | Purpose |
|---|---|---|
| `.autoharness/bootstrap-grants/{shipment_id}.yaml` | version-controlled when authored | Operator-authored pre-claim bootstrap grant surface |
| `.autoharness/gates/pipeline-topology-force-audit.log` | gitignored | Append-only force audit log for operator `--force` and grant-authorized force |
| `.autoharness/gates/bootstrap-grant-consumption/{shipment_id}/{invocation}.json` | gitignored | Durable at-most-once consumption record |
| telemetry journal path (workspace-config dependent) | typically gitignored | Observational tool-event emission, fail-open |

Running the gate does not dirty tracked working-tree state **unless** an operator
intentionally adds or edits a tracked bootstrap-grant file.

## References

- [`docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md`](decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md)
- [`docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md`](plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md)
- [`docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`](bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md)
- [`docs/bootstrap/2026-09-13-173-S-bootstrap-evidence.md`](bootstrap/2026-09-13-173-S-bootstrap-evidence.md)
- [`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`](compound/2026-05-07-backlogit-shipment-status-constraints.md)
- [`docs/compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md`](compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md)
- [`docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`](compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md)
- [DAG Readiness Gate Reference](dag-readiness-gate.md)
- [Validation Gates Reference](gates-reference.md)
- [Copilot-Review Merge Gate Reference](copilot-review-gate.md)
- [`_ship` agent definition](../.github/agents/_ship.agent.md)
- [`_orchestrator` agent definition](../.github/agents/_orchestrator.agent.md)