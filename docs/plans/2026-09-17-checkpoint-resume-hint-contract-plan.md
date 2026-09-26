---
title: "Checkpoint resume_hint: producer guarantee, deterministic validation, and historical-record compatibility policy"
description: "Implementation plan closing the autoharness-owned half of the checkpoint resume_hint gap: a historical-record COMPATIBILITY POLICY for pre-existing resolved checkpoints lacking the field (classification and reporting only — no migration mechanism ships and no committed checkpoint file is ever rewritten), a producer guarantee that every harness checkpoint author emits a specific top-level resume_hint including the minimal end-of-session shape, and deterministic author-time validation exposed as one executable adapter boundary in front of the official create operation, implemented as its own task and ENABLED by a separate task that cannot run until both producer paths are updated, with invariant-based regression tests rather than a pinned record count — ordered policy-first so the validator cannot deadlock startup on an unrepairable historical record, with that ordering encoded as explicit task dependencies rather than prose. The upstream backlogit validator, schema, and CLI-help change is explicitly excluded."
doc_type: plan
source: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
date: 2026-09-17
status: reviewed
plan_id: checkpoint-resume-hint-contract
plan_role: superseded
revision: 7
supersedes: null
superseded_by: docs/plans/2026-09-18-checkpoint-authority-plan.md
superseded_by_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
supersession_note: "Superseded at architecture level by the 2026-09-18 shared-execution-architecture decision. This document is retained unchanged as the historical contract of attempts 1-8; it is no longer the operative plan for its shipment and is not to be edited further. The successor named in superseded_by is the current state."
source_history:
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-05.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-06.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-07.md
  - docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md
review_manifest: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
revision_note: "Revision 7 is maintained as one coherent current-state contract rather than as an accreting record of corrections. Prior-revision deltas, superseded requirement variants, and reviewer chronology are not carried in the body: the immutable per-attempt review artifacts listed in source_history and the mutable verdict manifest named by review_manifest are the authoritative record of that chronology. Latest attempt and verdict are read from the manifest, never from this file."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 71200CBB
stash_ids:
  - 71200CBB
deferred_scope_expansions:
  - 71200CBB
excluded_upstream_report: docs/scratch/bugs/2026-09-17-backlogit-checkpoint-v1-resume-hint-validation-gap.md
prior_learnings:
  - docs/compound/2026-08-18-stage-agent-checkpoint-index-sync-ordering-self-contradiction.md
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
covering_feature: 172-F
shipment: 180-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
plan_hardening_section: "## Plan Hardening Record (P-006)"
source_refs:
  originating_pr: 452
  originating_review_thread: PRRT_kwDORzpWpM6i_UrE
  originating_task_id: "N/A"
  originating_feature_id: "N/A"
  originating_shipment_id: "N/A"
tags:
  - "checkpoint"
  - "recovery-contract"
  - "compatibility-policy"
  - "fail-closed-design"
---

# Checkpoint `resume_hint` contract

## Provenance

Deferred scope expansion `71200CBB`, discovered via hosted Copilot review of
PR 452, thread `PRRT_kwDORzpWpM6i_UrE`. Task, feature, and shipment IDs were
recorded `N/A` at capture; the P-021 C6 late-identifier reconciliation was run
over the Ship-owned residual-risk records and **no late identifier surfaced**.
The `N/A` values stand as truthful terminal records. Non-blocking.

Unconditional P-021 C5 duplicate detection: **clean scan, no duplicate.**
`904C47BC` (top-level `progress` context-nesting) is a different defect class
on a different field; `445C1DFB` / `032-DL` is a distinct, already-repaired
earlier instance on a different file. Not merged.

## Ownership boundary

**In scope (autoharness-owned).** The producer guarantee, autoharness-side
deterministic validation and tests, and the historical-record policy.

**Excluded (backlogit-owned, upstream).** Any change to backlogit's CheckpointV1
validator or schema requiredness for `resume_hint`, and any change to the
`checkpoint create` CLI help text or its example payload. That half is written
up separately at
`docs/scratch/bugs/2026-09-17-backlogit-checkpoint-v1-resume-hint-validation-gap.md`
for parallel work in the backlogit workspace. This release unit is **not
blocked** on that report landing.

## Problem

`.github/instructions/backlogit.instructions.md` lines 147–151 require every
checkpoint to carry a specific resume hint **even when the record is
immediately resolved**. backlogit does not auto-populate the field — only
`created_at`, `updated_at`, and `status` are auto-populated — so the producer
is the only place it can originate. backlogit also does not consider the
omission an error: `backlogit checkpoint get` returns `"valid": true` with no
warning and no quarantine flag, and `checkpoint create --help` lists
`resume_hint` among the modeled top-level keys without stating it is required,
with an example payload that omits it entirely.

The startup recovery protocol fails closed on missing or malformed required
fields **without exempting resolved records**, and a resolved checkpoint cannot
be repaired through the official create operation. Therefore shipping
validation ahead of a historical-record policy converts a latent gap into a
hard, self-inflicted startup block.

## Ordering hazard (binding)

Work lands in the order **(3) policy → (1) producer → (2) validation**. The
validator is the last thing enabled. This is a correctness constraint, not a
preference: it is the difference between closing a gap and manufacturing a
deadlock.

## Design

### Part 3 first — historical-record policy

Define how a pre-existing `schema_version: 1` record lacking `resume_hint` is
treated by the fail-closed startup scan. The classification is **total**: every
historical record lands in exactly one of two outcomes, and neither is
"unspecified".

* A record with `status: resolved` **and** no `resume_hint` is classified
  `CHECKPOINT_LEGACY_HINTLESS_RESOLVED`. It is enumerated, reported, and
  **excluded from the candidate set** — it can never be an active recovery
  candidate by definition, so excluding it removes no recovery capability.
  This outcome is **reported, non-blocking**.
* A record with `status: active` and a missing, empty, or whitespace-only
  `resume_hint` is classified **`CHECKPOINT_ACTIVE_HINTLESS`** — a **concrete,
  blocking** token that fails closed to operator handoff. It is **never**
  exempt and **never** grandfathered, regardless of how old the record is or
  whether this harness authored it.
* **The two outcomes are deterministic and disjoint**, decided by a single
  field: `status`. There is no path on which an active hintless historical
  record produces a silent pass, an unclassified result, or a
  compatibility-exempt classification. Stating "it fails closed exactly as
  today" without naming a token is precisely the gap this clause closes — a
  fail-closed behaviour with no token is not observable, not testable, and not
  reportable.
* `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` is a **closed, enumerable**
  classification, not an open-ended tolerance: the scan reports the count and
  the filenames so the exemption is visible rather than silent. Resolved
  compatibility and active fail-closure are **separate** rules; neither widens
  the other.
* An operator may repair a historical record out-of-band; the policy neither
  requires nor performs such a repair.

### Part 1b — activation is atomic, and it is LAST

The Checkpoint Payload Contract currently advertises
`backlogit_create_checkpoint` (MCP) and `backlogit checkpoint create` (CLI) as
the permitted way a harness producer writes a checkpoint. Once the adapter
exists, that advertisement is **wrong** — it names the exact bypass the adapter
is a gate in front of, in the document agents are instructed to obey.

**But the correction cannot land first.** A committed contract that prohibits
the raw create path while no adapter exists and no producer is wired to one
leaves every producer with no lawful way to write a checkpoint: the only
documented path is forbidden and the replacement is unavailable. That
intermediate state is not a transient inconvenience — it is a committed,
reviewable state of the repository in which the harness cannot checkpoint at
all. **No committed intermediate contract may prohibit the raw path before the
replacement is both available and wired.**

The rollout is therefore split into an **inert build-out** phase and a single
**atomic activation**.

#### Phase 1 — inert build-out (prohibits nothing, changes no producer)

Each of these lands independently and leaves the system fully operational on
the existing raw path:

1. The historical-record **classification policy** and its outcome set —
   descriptive only. It classifies records; it forbids no producer path.
2. `validate_checkpoint_payload()` and the `autoharness checkpoint create`
   adapter, implemented and tested but **referenced by no agent template, no
   registry, and no instruction**.
3. The executable historical-scan command and its MCP counterpart, likewise
   unreferenced.
4. The CLI ↔ MCP parity adapter surface and the typed producer inventory.

At the end of phase 1 the adapter is available and proven, and **nothing has
been prohibited**.

#### Phase 2 — atomic activation (one change set)

Exactly one task flips the system over, and it changes **all** of the following
together or none of them:

| Surface | Change |
|---|---|
| `.github/instructions/backlogit.instructions.md` | Checkpoint Payload Contract rule 2 now names `autoharness checkpoint create` as the producer path; the raw create operation is described as internal to the adapter |
| `templates/instructions/backlogit.instructions.md.tmpl` | Byte-identical change |
| `templates/agents/_stage.agent.md.tmpl` + `.github/agents/_stage.agent.md` | Stage's Step 6 checkpoint write invokes the adapter |
| `templates/agents/_ship.agent.md.tmpl` + `.github/agents/_ship.agent.md` | Ship's closure checkpoint write invokes the adapter |
| Every installed and template **backlog registry** | `create_checkpoint` maps to the guarded operation (see the inventory below) |
| Every installed and template **agent tool declaration** | The checkpoint create tool declared to an agent is the guarded one |
| Enforcement | The structural verifier's prohibition assertion is switched on |

Both the installed copy and its template change in the same task and revert
together. Changing one alone produces a workspace whose installed instruction
and its own template disagree, which is a drift defect the next `autoharness
install` would silently resolve in the wrong direction. The same
template/installed pairing rule applies to every row above.

**Manifest checksum obligation — planned, not implemented here.** Any installed
file the activation touches is recorded in the workspace install manifest with a
content checksum. The activation task regenerates those checksums for every file
it modifies, in the same change, so the manifest does not report drift against
files the activation itself authored. The exact obligation is:

| Surface class | Files | Manifest obligation |
|---|---|---|
| Installed instruction | `.github/instructions/backlogit.instructions.md` | Recompute and rewrite its checksum entry |
| Installed agent mirrors | `.github/agents/_stage.agent.md`, `.github/agents/_ship.agent.md` | Recompute and rewrite each checksum entry |
| Installed registry | `.autoharness/backlog-registry.yaml` | Recompute and rewrite if manifest-tracked; if not tracked, record that explicitly |
| Templates | `templates/instructions/…`, `templates/agents/…`, `templates/backlog/registries/…` | Not install-manifest-tracked; asserted byte-identical to their installed mirrors instead |

Enumerating the obligation is in scope for this plan; **performing** the
checksum regeneration is Ship's work under `180-S` and is not done by Stage.

**Not implemented in this Stage cycle.** This plan *plans* the change; no
source file, template, or instruction is edited by Stage.

### CLI ↔ MCP parity, and the full producer inventory

A gate that guards the CLI while the MCP tool remains directly callable is not a
gate. Parity is structural:

* **One adapter, two front ends.** `autoharness checkpoint create` (CLI) and
  the guarded MCP operation both call the **same** adapter entry point
  `autoharness.checkpoint.adapter.create_checkpoint()`. They share validation,
  token vocabulary, exit/error mapping, and JSON shape; a divergence between
  them is itself a test failure.
* **The raw backlogit create operation is reachable from exactly one place in
  the tree** — inside the adapter. This is asserted structurally against the
  typed inventory below, not by a text scan.
* **Registry and agent declarations map the guarded operation.** After
  activation, no registry operation and no agent tool declaration resolves to
  the raw create call.

**Inventory of surfaces that must be updated at activation** (enumerated from
the workspace, and re-enumerated by the activation task rather than trusted from
this table):

| Class | Surface | Current mapping |
|---|---|---|
| Installed registry | `.autoharness/backlog-registry.yaml` | `create_checkpoint` → MCP `backlogit_create_checkpoint`, CLI `backlogit checkpoint create --state-dump {{state_dump}}` |
| Staging registry | `.autoharness/staging/.autoharness/backlog-registry.yaml` | same |
| Template registry | `templates/backlog/registries/backlogit.registry.yaml` | same |
| Template registry (other backend) | `templates/backlog/registries/backlog-md.registry.yaml` | no checkpoint operation — asserted absent, not silently skipped |
| Agent declaration | `templates/agents/_stage.agent.md.tmpl` + `.github/agents/_stage.agent.md` | declares `backlogit_create_checkpoint` |
| Agent declaration | `templates/agents/_ship.agent.md.tmpl` + `.github/agents/_ship.agent.md` | declares `backlogit_create_checkpoint` |
| Instruction | `.github/instructions/backlogit.instructions.md` + its template | Checkpoint Payload Contract rule 2 |

The activation task **re-derives** this inventory and fails closed if it finds a
surface not listed here, so a registry or agent added between planning and
execution cannot be silently missed.

### Part 1 — producer guarantee

Every harness checkpoint producer — Stage, Ship, and any other — emits a
top-level `resume_hint` specific enough to support a later recovery decision.
This explicitly includes the **minimal end-of-session completion checkpoint**,
which is the shape `checkpoint-20260916-064310.json` appears to be. A hint must
name the next actionable step or state explicitly that no re-entry is required;
a generic or empty string does not satisfy the guarantee.

### The executable historical scan

The startup recovery protocols in the Stage and Ship agents must classify the
existing checkpoint corpus. **A Markdown agent cannot call a Python predicate.**
Instructing it to "call `validate_checkpoint_payload` with
`origin='historical'`" is an instruction with no mechanism — the agent has no
import, and a structural test has no wiring to assert.

The scan is therefore an **executable surface**, available identically from both
front ends:

```text
autoharness checkpoint scan [--json]
```

and the guarded MCP operation `autoharness_checkpoint_scan`. Both call the same
adapter, emit the **same structured tokens**, and produce the same JSON:

```json
{
  "scanned": 57,
  "blocking": 0,
  "records": [
    {"file": "checkpoint-20260916-064310.json",
     "status": "active",
     "outcome": "CLEAN",
     "token": null,
     "agent": "stage"}
  ]
}
```

Stage's and Ship's startup recovery steps **invoke that command** and consume
its JSON. They restate no predicate and describe no classification rule in
prose. `--origin historical` is **not** a user-facing option: the historical
origin is set internally by the scanner and by nothing else.

### Part 2 last — deterministic validation

Autoharness-side validation plus regression tests that fail deterministically
when a **harness-authored** `schema_version: 1` payload omits `resume_hint`, so
the gap is caught at author time rather than at recovery time.

| Token | Origin | Severity | Condition |
|---|---|---|---|
| `CHECKPOINT_RESUME_HINT_MISSING` | `harness` | blocking | Harness-authored V1 payload with no top-level `resume_hint` |
| `CHECKPOINT_RESUME_HINT_EMPTY` | `harness` | blocking | Present but blank or whitespace-only |
| `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` | `historical` | reported | Pre-existing record in a **terminal** status (`resolved`, `shipped`, `abandoned`) with no usable hint; reported and excluded from the candidate set |
| `CHECKPOINT_ACTIVE_HINTLESS` | `historical` | **blocking** | Pre-existing record in a **non-terminal** status (`active`, `queued`) with a missing, empty, or whitespace-only hint; fails closed to operator handoff |
| `CHECKPOINT_RECORD_MALFORMED` | `historical` | **blocking** | The record cannot be classified at all: unparseable JSON, duplicate object keys, non-object root, missing `status`, `status` of the wrong type, an unrecognized `status` value, `schema_version` absent or not the integer `1`, or a required field of the wrong type |

#### Historical classification is TOTAL

`validate_checkpoint_payload` returns a **`ValidationOutcome` for every input**,
never `None`, never an exception-as-control-flow, and never an unclassified
result. For `origin="historical"` the decision procedure is:

1. **Parse.** Unparseable bytes, a non-object root, or **duplicate keys** in the
   JSON object → `CHECKPOINT_RECORD_MALFORMED` (blocking). Duplicate keys are
   detected explicitly via an `object_pairs_hook`, because the default parser
   silently keeps the last occurrence — which would let a record carry two
   different `status` values and be classified on whichever the parser happened
   to keep.
2. **Schema gate.** `schema_version` absent, non-integer, or ≠ `1` →
   `CHECKPOINT_RECORD_MALFORMED`. A future `schema_version: 2` is explicitly
   blocking rather than optimistically parsed: this validator does not know
   that format and must not guess.
3. **Status gate.** `status` absent, not a string, or **not a member of the
   accepted set** → `CHECKPOINT_RECORD_MALFORMED`. The accepted set is taken
   verbatim from the installed backlogit contract, which states that status
   "only ever holds `queued`, `active`, `shipped`, or `abandoned`", plus
   `resolved`, which is the value `resolve_checkpoint` writes.
4. **Field-type gate.** `agent`, `session_id`, `phase`, `resume_hint`, or
   `context` present with the wrong type → `CHECKPOINT_RECORD_MALFORMED`.
5. **Hint classification**, reached only by a well-formed record:

| `status` | Terminality | Usable hint | Outcome |
|---|---|---|---|
| `active` | non-terminal | yes | `CLEAN` |
| `active` | non-terminal | no | `CHECKPOINT_ACTIVE_HINTLESS` (blocking) |
| `queued` | non-terminal | yes | `CLEAN` |
| `queued` | non-terminal | no | `CHECKPOINT_ACTIVE_HINTLESS` (blocking) |
| `resolved` | terminal | yes | `CLEAN` |
| `resolved` | terminal | no | `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` (reported) |
| `shipped` | terminal | yes | `CLEAN` |
| `shipped` | terminal | no | `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` (reported) |
| `abandoned` | terminal | yes | `CLEAN` |
| `abandoned` | terminal | no | `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` (reported) |

Every accepted status appears in this table, and every remaining input falls to
`CHECKPOINT_RECORD_MALFORMED`. There is no default branch, no "other" row, and
no silently-skipped record: a record that cannot be classified **blocks**,
because a recovery scan that quietly drops an unreadable candidate is exactly
the failure the fail-closed startup protocol exists to prevent.

`queued` is grouped with `active` as non-terminal because a queued record is a
pending recovery candidate; treating it as terminal would let an unresolved
candidate be excluded from the scan on the strength of its status alone.

Validation applies at **author time** on payloads this harness produces. It
does not retroactively invalidate records it did not author, which is precisely
what the compatibility policy makes safe. The one thing it *does* enforce
against historical records is the non-terminal-hintless fail-closure and the
malformed fail-closure, both of which are **recovery-time** judgements about
candidate eligibility rather than author-time judgements about authorship.

#### The validation boundary — an executable adapter, not a library call

The two producers this contract must guard are **Markdown agent templates**.
Stage and Ship import no Python; they call `backlogit_create_checkpoint` (MCP)
or `backlogit checkpoint create` (CLI) **directly**. A package-local Python
function sitting beside that call path cannot intercept it, so "both producer
paths call this exact function" would be an instruction with no mechanism, and
a structural test would have no wiring to assert.

**The boundary is therefore an executable adapter command** that producers
invoke *instead of* the backlogit create operation:

```text
autoharness checkpoint create (--state-dump-file <path> | --state-dump-json <json>) [--json]
```

**Argument contract (hardened).**

* `--state-dump-file` and `--state-dump-json` are **mutually exclusive and
  exactly one is required**. The former ambiguous `--state-dump <path-or-json>`
  is removed: a single option that guesses whether its argument is a path or a
  document is undecidable for inputs that are legal as both, and the guess
  determines whether a file is read from disk.
* **`--origin` is not a public option.** The create origin is an **internal
  constant** (`harness`) fixed by the adapter; the historical origin is set by
  the internal scanner and by nothing else. No caller can select the token space
  it is validated against.
* **`--state-dump-file` containment.** The path is resolved and proven inside
  the workspace root by canonicalized parts comparison. Rejected: absolute
  paths, `..` traversal, environment/user expansion (`$`, `${}`, `%…%`, `~`),
  and any component that is a symlink, junction, or reparse point.
* **File-type rejection.** The resolved target must be a **regular file**.
  Directories, FIFOs, sockets, device and character-special files, and
  reparse-point targets are rejected before any read.
* **Bounds, all enforced before the payload is used.** Maximum file size
  (1 MiB); maximum JSON nesting depth (32); maximum string length (64 KiB);
  maximum collection length (4096 elements); maximum total key count (4096).
  Each bound has its own token-bearing rejection and its own test.
* **Duplicate keys** in the supplied JSON are rejected via `object_pairs_hook`,
  for the same reason as in the scanner.
* **Process execution is a fixed argv with `shell=False`.** No string
  interpolation into a shell command, ever. The `--` option terminator is
  emitted before any value-derived argument, and any value whose first character
  is `-` is additionally rejected at the adapter boundary rather than relying on
  the terminator alone.
* **No-write, no-delegate on every validation failure.** Any failure above —
  argument, containment, file-type, bound, parse, or payload — exits non-zero,
  writes nothing, and **does not invoke backlogit at all**. There is no partial
  write and no "validate then delegate anyway" path.

Further properties of the boundary:

* **It is the only create path a harness producer may use.** The adapter
  validates the payload and, only on a clean outcome, performs the
  `backlogit checkpoint create` call itself. A producer that reaches
  `backlogit_create_checkpoint` / `backlogit checkpoint create` directly has
  bypassed the gate.
* **Validation is strictly pre-write.** The adapter evaluates the payload
  before any create call is issued. On `CHECKPOINT_RESUME_HINT_MISSING` or
  `CHECKPOINT_RESUME_HINT_EMPTY` it exits non-zero and **writes nothing**, so
  no malformed record is created — which matters because a written checkpoint
  cannot be repaired through the official create operation.
* **`validate_checkpoint_payload(payload, *, origin) -> ValidationOutcome`
  is the single predicate**, in `src/autoharness/checkpoint/`, and the adapter
  is its only producer-side caller. The scan command calls the same predicate
  with `origin="historical"`. One definition, three callers (CLI create, MCP
  create, scan), no per-agent copy and no re-stated rule in an agent template.
* **`origin` partitions the token space structurally.** Only
  `origin="harness"` can emit `CHECKPOINT_RESUME_HINT_MISSING` /
  `CHECKPOINT_RESUME_HINT_EMPTY`; only `origin="historical"` can emit
  `CHECKPOINT_LEGACY_HINTLESS_RESOLVED`, `CHECKPOINT_ACTIVE_HINTLESS`, or
  `CHECKPOINT_RECORD_MALFORMED`. The historical outcomes are disjoint and
  selected by the total decision procedure above, so the compatibility exemption
  can never absorb a non-terminal or malformed record.
* **Outcome is data, not an exception**, so the scan can report while the
  adapter halts.
* The adapter **adds no capability** beyond backlogit's own create operation
  and introduces no second checkpoint store. It is a gate in front of one call,
  nothing more. `.github/instructions/backlogit.instructions.md` rule 2 —
  checkpoints are written only through the official create operation — is
  preserved, because the adapter *is* how that operation is reached.

**Wiring — the producer surfaces known today:**

| Producer path | Call site | Enforced by |
|---|---|---|
| Stage checkpoint author | The Step 6 checkpoint write becomes an `autoharness checkpoint create` invocation, in `templates/agents/_stage.agent.md.tmpl` + installed mirror | T3 (text) / T9 (activation) |
| Ship checkpoint author | The closure-step checkpoint write becomes an `autoharness checkpoint create` invocation, in `templates/agents/_ship.agent.md.tmpl` + installed mirror | T4 (text) / T9 (activation) |
| Startup recovery scan | Stage and Ship invoke `autoharness checkpoint scan --json` and consume its JSON | T2, T7a/T7 |
| Registries and agent tool declarations | `create_checkpoint` maps to the guarded operation | T9 (activation) |
| Checkpoint Payload Contract (installed + template) | Stops advertising the raw create call as a producer path | T9 (activation) |

This table is **not an exhaustive whitelist**. It records the surfaces known at
authoring time. A structural assertion hardcoded to these rows would silently
pass the moment a third producer appears — which is how this class of gate is
normally defeated — so the structural verification is **inventory-derived**
(T8), not table-derived.

### The typed producer inventory — markers, not a text scan

The former design scanned the tree for occurrences of the raw operation names.
That is unusable: the prohibition itself is written in the instruction file, the
plan, the tests, and the review artifacts, so the scan's own governing documents
are indistinguishable from violations. Raising the prohibition text as a
violation is a false positive; suppressing it by path is an allowlist that a new
producer silently joins.

The replacement is a **typed inventory plus bounded machine markers**:

* **`schemas/checkpoint-producer-inventory.json`** is a typed, schema-validated
  declaration of every checkpoint-producing surface in the repository:

  ```json
  {"schema_version": 1,
   "producers": [
     {"surface": ".github/agents/_stage.agent.md",
      "kind": "agent-template",
      "create_path": "adapter"},
     {"surface": "src/autoharness/checkpoint/adapter.py",
      "kind": "python-module",
      "create_path": "raw-allowed"}
   ]}
  ```

  `create_path` is `adapter` | `raw-allowed`, and **exactly one** surface in the
  whole inventory may declare `raw-allowed`: the adapter itself.
* **Markdown surfaces carry bounded HTML-comment markers** at their call sites,
  which are structurally distinct from prose:

  | Marker | Meaning |
  |---|---|
  | `<!-- checkpoint-producer:adapter -->` | This call site produces checkpoints through the adapter |
  | `<!-- checkpoint-producer:raw-allowed -->` | This call site is the adapter boundary itself |
  | `<!-- checkpoint-prohibition-reference -->` | This occurrence of the raw name is **documentation of the prohibition**, not a producer declaration |

* The verifier reconciles the three: every marker in the tree must correspond to
  an inventory entry and vice versa; every occurrence of a raw operation name
  must fall under one of the three markers; an unmarked occurrence is a
  violation. A new producer that forgets its marker fails the reconciliation
  rather than passing silently, and the prohibition text in the instruction,
  plan, tests and reviews is classified correctly as reference rather than
  flagged.

## Evidence recorded (read-only)

* `.backlogit/checkpoints/checkpoint-20260916-064310.json` in the working tree
  carries a populated top-level `resume_hint`. **Provenance, stated precisely:**
  this is an **operator-authored, operator-authorized pre-existing repair**,
  performed by the human operator outside the agent pipeline and explicitly
  directed to be preserved. It is included in the publication diff of commit
  `1b6a312d` for durable startup consistency — so that a later startup scan
  reads the repaired record rather than re-encountering the gap.
  It is **not** an agent-performed migration, **not** produced by this plan or
  this session, and **not** evidence that an official repair mechanism for
  resolved checkpoints exists. No such mechanism exists: a resolved checkpoint
  cannot be repaired through the official create operation, which is the entire
  reason Part 3 exists. It is not a worked example of a migrated record,
  because no migration ran.
  **Residual policy risk, recorded not waived:** the repair was a direct edit
  to a file under `.backlogit/checkpoints/`, which
  `.github/instructions/backlogit.instructions.md` rule 2 reserves to the
  official create operation. It was operator-performed and operator-authorized,
  which is the only authority under which it is permissible, and it is recorded
  here so the deviation is visible rather than silently normalized. No agent
  may cite it as precedent. This plan modifies neither the file nor its
  archived history.
* Full unfiltered checkpoint enumeration at the most recent reading: **53**
  records under `.backlogit/checkpoints/`, plus 75 under
  `.backlogit/archive/checkpoints/`. Zero validation anomalies, zero active
  `stage`-owned candidates. The count changes on every session that writes a
  checkpoint and has differed at every reading taken, so it is **observed and
  reported, never asserted** — which is why the corpus audit is invariant-based
  (see T11).
* backlogit version `1.10.1-0.20260823032255-b07729386a31+dirty` locally.
  CI installs a **different** binary: pinned `v1.9.0`, checksum-verified
  (`.github/workflows/ci.yml`). Any behavioural assertion about the checkpoint
  API must therefore hold on `v1.9.0` or be explicitly version-guarded; see
  the sibling SAFE_CLOSE plan, which carries the same divergence.

## Work Breakdown

The rollout is **inert build-out first, atomic activation last**. No task before
`T9` prohibits anything, changes any producer call site, changes any registry,
or switches on any enforcement.

| # | Task | Scope | Phase | Blocked by |
|---|---|---|---|---|
| T1 | Author the historical-record **classification policy** and its outcome set — `CHECKPOINT_LEGACY_HINTLESS_RESOLVED`, the blocking `CHECKPOINT_ACTIVE_HINTLESS`, and the blocking `CHECKPOINT_RECORD_MALFORMED` — as **descriptive text that prohibits no producer path**. The Checkpoint Payload Contract's advertisement of the raw create call is **not** touched here | `.github/instructions/backlogit.instructions.md` + `templates/instructions/backlogit.instructions.md.tmpl` | INERT | — |
| T2 | Describe the startup recovery scan contract in the agent templates and installed mirrors as an **invocation of `autoharness checkpoint scan --json`** whose JSON the agent consumes, including the non-terminal → blocking and malformed → blocking branches. No predicate is restated in prose | `templates/agents/` + `.github/agents/` | INERT | T1 |
| T3 | **Producer 1 of 2** — resume-hint guarantee for the Stage checkpoint author, including the minimal completion shape. Text only; the call site is still the raw path | `templates/agents/_stage.agent.md.tmpl` + installed mirror | INERT | T1 |
| T4 | **Producer 2 of 2** — the same guarantee for the Ship checkpoint author | `templates/agents/_ship.agent.md.tmpl` + installed mirror | INERT | T1 |
| T5a | **RED** — author the **five-token** contract tests against `validate_checkpoint_payload` and the adapter command, plus the **total historical-classification matrix** (every accepted status × hint-usability, and every malformed class: unparseable, duplicate keys, non-object root, missing/typed-wrong/unrecognized `status`, missing/future `schema_version`, wrong-typed required fields), and observe them failing before either exists | `tests/` | RED | T1 |
| T5b | **RED** — author the adapter **argument-hardening** contract tests: mutual exclusivity of `--state-dump-file` / `--state-dump-json`, absence of a public `--origin`, workspace containment, symlink/junction/reparse rejection, non-regular-file rejection, each size/depth/string/collection bound, `--` terminator and leading-hyphen handling, fixed-argv `shell=False`, and **no-write/no-delegate on every failure path**. Observe failing | `tests/` | RED | T1 |
| T5 | **IMPLEMENTATION** — `validate_checkpoint_payload()`, the five tokens, the total historical decision procedure, and the `autoharness checkpoint create` adapter with the full argument-hardening contract, **referenced by no agent template, no registry, and no instruction** (inert) | `src/autoharness/checkpoint/` | INERT-IMPL | T5a, T5b |
| T7a | **RED** — author the contract tests for the executable historical scan: CLI and MCP produce identical structured tokens and identical JSON over the same corpus; `--origin` is not reachable from either front end. Observe failing | `tests/` | RED | T1 |
| T7b | **IMPLEMENTATION** — `autoharness checkpoint scan` and the guarded MCP scan operation over the same adapter, emitting the same structured tokens (inert: nothing invokes them yet) | `src/autoharness/checkpoint/` | INERT-IMPL | T7a, T5 |
| T8a | **RED** — author the typed-inventory and marker-reconciliation contract tests: `schemas/checkpoint-producer-inventory.json` shape, exactly-one-`raw-allowed` rule, marker-to-inventory bijection, and the case that **proves a prohibition-reference occurrence is not a violation**. Observe failing | `tests/` | RED | T1 |
| T8b | **IMPLEMENTATION** — the producer-inventory schema, the three bounded markers, and the reconciling structural verifier (inert: assertion present, prohibition assertion not yet switched on) | `schemas/` + `src/autoharness/checkpoint/` | INERT-IMPL | T8a |
| T6 | **GREEN** — observe the five-token suite, the total classification matrix, the argument-hardening suite, and the CLI/MCP parity suite passing against the shipped, still-inert adapter and scanner | `tests/` | GREEN | T5, T7b, T8b |
| T9 | **ATOMIC ACTIVATION** — in ONE change set: update the Checkpoint Payload Contract (installed instruction **and** template) to name the adapter as the producer path; rewrite both agent producer call sites (both templates, both installed mirrors) to invoke the adapter; re-derive and update **every** installed and template registry's `create_checkpoint` mapping and **every** agent tool declaration to the guarded operation; add the bounded markers and inventory entries; switch on the prohibition assertion; and regenerate install-manifest checksums for every modified tracked file | instructions + agents + registries + manifest | ACTIVATE | T6, T3, T4, T2 |
| T10 | **GREEN post-activation** — structural verification of the activated system: the inventory reconciles, no surface outside the adapter reaches the raw create operation, every registry and agent declaration maps the guarded operation, installed and template copies agree byte-for-byte, and the manifest reports no drift | `tests/` | GREEN | T9 |
| T11 | Invariant-based **live-corpus audit** over the committed checkpoint corpus | `tests/` | GREEN | T10 |

**RED import safety (binding on T5a, T5b, T7a, T8a).** Each RED module imports
cleanly under `unittest.defaultTestLoader` with zero `loader.errors` and zero
`_FailedTest` placeholders; the not-yet-existing `autoharness.checkpoint.*`
boundaries are imported **inside** the test body through a `_load_boundary()`
helper. Each declared RED test individually executes and fails with its own
declared marker in its own `detail_text`.

### Ordering enforcement (machine-encoded)

The binding order is **policy → inert build-out (red → implement) → green →
ATOMIC ACTIVATION → post-activation green → live audit**, encoded as `blocks`
edges:

```text
T1 ─┬─> T2 ───────────────────────────────┐
    ├─> T3 ───────────────────────────────┤
    ├─> T4 ───────────────────────────────┤
    ├─> T5a ─┬─> T5 ─┬─> T7b ─┐           │
    ├─> T5b ─┘       │        │           │
    ├─> T7a ─────────┘        ├─> T6 ─────┴─> T9 ─> T10 ─> T11
    └─> T8a ─> T8b ───────────┘
```

* `T2, T3, T4 → T1`: the recovery scan contract and both producer guarantees
  are written against the classification policy, not ahead of it. T3 and T4 are
  mutually independent.
* `T5a, T5b, T7a, T8a → T1`: the tokens and the outcome set must be defined
  before tests can be authored against them. **None of the RED tasks depends on
  the implementation it describes** — that asymmetry is what makes them genuine
  red phases.
* `T5 → T5a, T5b`; `T7b → T7a, T5`; `T8b → T8a`: each implementation turns an
  existing, observed-failing suite green. All three ship **inert** — nothing
  invokes them, nothing is prohibited, and the raw create path still works.
* `T6 → T5, T7b, T8b`: green is observed against the complete, still-inert
  build-out.
* `T9 → T6, T2, T3, T4`: **activation cannot begin until the replacement is
  proven AND both producers and the scan contract have adopted the new text.**
  This is the correctness constraint that keeps every committed intermediate
  state operational: before `T9` nothing is prohibited; at `T9` the prohibition
  and the wiring land together; after `T9` there is no unwired producer.
* `T10 → T9`: a structural assertion may never precede the wiring it asserts.
* `T11 → T10`: auditing the live corpus is meaningful only once enforcement is
  on and verified.

**The activation invariant, stated once:** at no commit boundary in this DAG
does a contract prohibiting the raw create path exist while any producer lacks
a wired adapter. `T9` is the only task that changes that, and it changes every
affected surface together.

### T11 — invariant-based, not count-pinned

T11 asserts **invariants over whatever corpus is present**, with no cardinality
pinned anywhere. A record count changes on every checkpoint-writing session, so
a pinned literal fails for reasons unrelated to the contract it guards — a
brittleness defect, not a coverage gain.

1. Every record under `.backlogit/checkpoints/` classifies into exactly one
   bucket: valid-with-hint, `CHECKPOINT_LEGACY_HINTLESS_RESOLVED`, or fail-closed
   candidate. No record is unclassified.
2. The fail-closed bucket is **empty**. This is the property that actually
   matters — a non-empty bucket means startup halts.
3. Every `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` record has `status: resolved`.
   An `active` record is never in that bucket, **at any corpus size**; it lands
   in the fail-closed bucket under `CHECKPOINT_ACTIVE_HINTLESS`.
4. The classification is **total and deterministic**: running it twice over the
   same corpus yields identical results.
5. The legacy set is **monotonically non-increasing with respect to newly
   authored records**: no record authored after T9 activates enforcement may
   enter it. This is the "the exemption cannot silently grow" property,
   expressed as an invariant over **authorship** rather than over
   **cardinality**.
6. The reported `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` set is enumerated by filename and
   count in the test output, so growth is visible in CI logs. The count is
   **observed and reported, never asserted against a literal.**

Synthetic fixture corpora cover the shapes the live corpus may not contain —
an `active` hintless record, a whitespace-only hint, a legacy payload with no
`schema_version` — so coverage does not depend on what the repository happens
to hold on a given day.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* The startup scan over the committed corpus produces zero fail-closed
  handoffs and reports its `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` set by filename.
* No test asserts a checkpoint record count.
* Both producer templates invoke `autoharness checkpoint create`, neither
  retains a direct `backlogit_create_checkpoint` / `backlogit checkpoint create`
  invocation on the producer path, and neither agent template re-states the
  predicate inline.
* The adapter exits non-zero and writes **nothing** on
  `CHECKPOINT_RESUME_HINT_MISSING` / `_EMPTY`; no record is created.
* Validation runs **before** the create call, never after.
* An `active` hintless record is never classified
  `CHECKPOINT_LEGACY_HINTLESS_RESOLVED`; it yields the blocking
  `CHECKPOINT_ACTIVE_HINTLESS` token and fails closed to operator handoff.
  `validate_checkpoint_payload` is asserted **total**: every historical input
  returns a `ValidationOutcome`, never `None` and never an unclassified result.
* The **inventory-backed** structural verifier discovers producer surfaces by
  scanning the repository rather than reading a hardcoded list, and a synthetic
  third producer that reaches the raw create call is asserted to **fail** the
  test — proving the assertion is discovery-driven rather than list-driven.
* The Checkpoint Payload Contract no longer advertises
  `backlogit_create_checkpoint` / `backlogit checkpoint create` as a harness
  producer path; the installed instruction and its template agree byte-for-byte
  in the relevant clause; and the install-manifest checksum for every modified
  tracked file matches its new content.
* No committed checkpoint file is modified by this release unit.
* `autoharness gate check` passes on every modified file.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Validator lands before policy and deadlocks startup | T9 (atomic activation) blocks on T6, T2, T3 and T4 — every functional predecessor, not just the policy pair. This is the entry's own recorded escalation trigger (b) |
| R2 | The legacy exemption silently grows into a permanent tolerance | The classification is enumerated and reported by filename at every scan, and T11 asserts the fail-closed bucket stays empty and that no newly authored record may enter the legacy set |
| R3 | An `active` record is accidentally grandfathered, or lands in an unspecified outcome | The historical classification is **total**: a five-stage decision procedure (parse -> schema -> status -> field types -> hint) covers every accepted `status` value (`queued`, `active`, `shipped`, `abandoned`, `resolved`) plus every malformed class, with terminal statuses reaching the reported legacy outcome, non-terminal statuses reaching blocking `CHECKPOINT_ACTIVE_HINTLESS`, and everything else reaching blocking `CHECKPOINT_RECORD_MALFORMED`. There is no default branch. T5a asserts the full matrix red first, T6 observes it green, and T11 invariant 3 asserts it over the live corpus |
| R4 | Someone pulls the upstream validator change into this scope | Stated as excluded in frontmatter, in the Ownership boundary section, and in Out of scope |
| R5 | A producer path constructs a payload without validating it | The adapter command is the only create path; T6 asserts structurally that neither wired template retains a direct backlogit create call, and T10 asserts it across the discovered inventory so a third producer cannot slip past. A second implementation is a review-visible defect |
| R6 | The inventory test fails for reasons unrelated to the contract | T11 pins no count and no filename set; it asserts totality, emptiness of the fail-closed bucket, and determinism |
| R7 | Validation after write leaves a malformed record on disk that cannot be repaired | The adapter validates the pre-write payload and writes nothing on a failing outcome; Verification asserts ordering explicitly |
| R8 | The adapter is treated as a second checkpoint store or drifts from backlogit's create semantics | The adapter adds no capability: it validates, then performs the official `backlogit checkpoint create` call. Instruction rule 2 is preserved because the adapter *is* how that operation is reached |
| R9 | A structural assertion is written against wiring that does not yet exist and is quietly weakened until it asserts nothing | T10 blocks on T9, so the wiring exists before it is asserted, and no reverse edge from T9 onto T10 exists |
| R10 | The authoritative contract keeps advertising the raw create call, so agents are simultaneously told to use the adapter and told the raw call is permitted | T9 performs the contract update atomically across installed instruction, template, both agent mirrors, every registry and every agent tool declaration in ONE change set; T10 asserts the advertisement is gone, that every paired surface agrees, and that install-manifest checksums match |
| R12 | A committed intermediate state prohibits the raw path before the adapter is wired, leaving no lawful create path at all | The rollout is split into an inert build-out (T1-T8b, prohibits nothing) and a single atomic activation (T9). The activation invariant is asserted directly: at no commit boundary does a prohibiting contract coexist with an unwired producer |
| R13 | The CLI is guarded while the MCP operation remains directly callable | One adapter, two front ends; T7a asserts identical structured tokens and identical JSON from both, and T9 re-derives and maps every registry operation and agent tool declaration to the guarded operation |
| R14 | `--state-dump <path-or-json>` misclassifies an argument that is legal as both, changing whether a file is read from disk | The ambiguous option is removed in favour of mutually exclusive `--state-dump-file` / `--state-dump-json`, exactly one required; T5b asserts the mutual exclusion and every hardening rule |
| R15 | A broad text scan for raw operation names flags the prohibition documents themselves, and is then suppressed by a path allowlist a new producer silently joins | Typed producer inventory plus three bounded HTML-comment markers that distinguish producer declarations from prohibition references; T8a carries the case proving a prohibition reference is not a violation |
| R11 | A hardcoded two-file structural assertion silently passes when a third producer is added | T8b/T10 derive the surface set by repository scan and is verified against a synthetic third producer that must fail |

## Priority

Remains `medium`. Neither of the entry's own escalation triggers has fired: no
Orchestrator/Stage/Ship startup has been observed halting on this record, and
item (2) has not landed ahead of item (3) — this plan's ordering is what
guarantees the latter.

## Out of scope

* backlogit CheckpointV1 validator/schema requiredness for `resume_hint`.
* `checkpoint create` CLI help text and example payload.
* Repairing, recreating, or resolving `checkpoint-20260916-064310.json` or any
  other existing record.
* Stash entry `904C47BC` (top-level `progress` hoisting) — confirmed distinct,
  not merged, untouched. Note for traceability: the portfolio session's own
  `checkpoint-20260918-052706.json` exhibits that separate defect. It was
  superseded through the official checkpoint lifecycle and the malformed record
  was preserved as history rather than hand-edited. That handling is recorded
  in the session memory artifact; it is not a deliverable of this plan and does
  not reopen `904C47BC`.

## Plan Hardening Record (P-006)

**Hardening trigger.** Two template families plus their installed mirrors; a
change to the crash-resumption contract, which is the mechanism by which a
crashed session is recovered — a defect here is discovered at exactly the
moment recovery is needed and nothing else is working; and a fail-closed
validator whose mis-ordering can deadlock every agent's startup.

**Protected invariants.**

* No committed checkpoint file is modified, repaired, recreated, or resolved
  by this release unit.
* No `status: active` record is ever grandfathered by the legacy exemption.
* Validation never retroactively invalidates records this harness did not
  author.
* The upstream backlogit validator, schema, and CLI help are out of scope and
  stay out.
* The legacy exemption remains closed and enumerable, never an open-ended
  tolerance.
* Checkpoints are written only through the official create operation; the
  adapter is how that operation is reached, never a second store.

**Instructions and learnings consulted.**
`.github/instructions/backlogit.instructions.md` (Checkpoint Payload Contract,
rules 1–5; Checkpoint-Recovery / Prune-on-Restore Protocol),
`docs/compound/2026-08-18-stage-agent-checkpoint-index-sync-ordering-self-contradiction.md`,
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`,
the Stage and Ship Crash-Resumption / Startup Recovery Protocol sections, and
`docs/scratch/bugs/2026-09-17-backlogit-checkpoint-v1-resume-hint-validation-gap.md`.

| # | Hazard | Resolution in this contract |
|---|---|---|
| H1 | A binding policy->producers->validation order carried as prose leaves the producers unordered against the validator — the half that actually deadlocks | Every edge encoded: `T5a/T5b/T7a/T8a (RED) -> T5/T7b/T8b (inert IMPL) -> T6 (GREEN) -> T9 (ATOMIC ACTIVATION) -> T10 -> T11`, with `T9 -> T2, T3, T4` as well |
| H2 | A package-local Python function is not an enforceable boundary against Markdown producers that call backlogit MCP/CLI directly, so the guarded paths connect to nothing | The boundary is the executable `autoharness checkpoint create` adapter, which producers invoke *instead of* the raw create operation, with `validate_checkpoint_payload()` as its single implementation |
| H3 | Each agent template re-stating the predicate inline produces two drifting definitions of the same rule | Single-definition constraint stated normatively; T10 asserts both wired templates invoke the adapter, retain no direct backlogit create call, and re-state nothing, and extends that assertion to every inventoried producer surface |
| H4 | Validating after the create call leaves a malformed record on disk that cannot be repaired through the official operation | The adapter validates the pre-write payload and writes nothing on a failing outcome; Verification asserts ordering |
| H5 | "Does not retroactively invalidate records it did not author" is a convention with no mechanism | `origin` parameter partitions the token space structurally: harness-origin cannot emit either historical token, historical-origin cannot emit the missing/empty tokens |
| H6 | Pinning a checkpoint record count produces a test that fails on every checkpoint-writing session for reasons unrelated to its contract | T11 pins no cardinality; it asserts totality, an empty fail-closed bucket, determinism, and no-new-legacy-after-enforcement, with the count observed and reported only. Synthetic fixtures cover shapes the live corpus may lack |
| H7 | Describing the repaired record as a migrated historical record implies a migration ran and an official repair mechanism exists — neither is true | Provenance stated precisely as an operator-authored, operator-authorized pre-existing repair, with the residual policy risk recorded and precedent-use explicitly denied |
| H8 | Recording only the local `+dirty` backlogit build hides that CI runs a different pinned binary | Divergence recorded in the evidence section with a pointer to the sibling SAFE_CLOSE plan, which owns the version-contract deliverable |
| H9 | "An active hintless record fails closed exactly as today" names a behaviour but no token, so the outcome is unobservable, untestable, and indistinguishable from an unspecified result | `CHECKPOINT_ACTIVE_HINTLESS` is a concrete blocking token; `validate_checkpoint_payload` is specified **total** over historical input by a five-stage decision procedure covering every accepted `status` plus every malformed class, with the terminal-compatibility, non-terminal-fail-closed, and malformed-fail-closed rules disjoint and none widening another |
| H10 | The authoritative Checkpoint Payload Contract keeps advertising the raw create call as a permitted producer path, so the gate is contradicted by the very document agents obey | T9 updates installed instruction, template, both agent mirrors, every registry and every agent tool declaration atomically, regenerates install-manifest checksums for every modified tracked file, and T10 asserts all of it |
| H12 | Correcting the contract FIRST prohibits the only documented create path while no adapter is wired, so the committed intermediate state has no lawful checkpoint path at all | Inert build-out / atomic activation split with an explicit activation invariant: no commit boundary carries a prohibiting contract alongside an unwired producer |
| H13 | A Markdown agent cannot call a Python predicate, so "the scan calls `validate_checkpoint_payload(origin=historical)`" is an instruction with no mechanism | The scan is an executable surface (`autoharness checkpoint scan` + guarded MCP counterpart) emitting the same structured tokens from both front ends; agents invoke it and consume its JSON |
| H14 | A user-selectable `--origin` lets a caller choose which token space its payload is validated against | `--origin` is removed from the public surface: create origin is an internal constant, historical origin is set only by the internal scanner |
| H15 | An option that accepts either a path or an inline document decides by guessing, and the guess determines whether the filesystem is read | Mutually exclusive `--state-dump-file` / `--state-dump-json`, exactly one required, with containment, regular-file/link/reparse/device rejection, explicit bounds, duplicate-key rejection, `--` terminator plus leading-hyphen rejection, fixed argv with `shell=False`, and no-write/no-delegate on every failure |
| H11 | A structural gate hardcoded to the two producer surfaces known today is defeated by adding a third | T8b/T10 derive the surface set by repository scan across agents, skills, instructions, docs and source, and is itself verified against a synthetic bypassing producer that must fail |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Change the startup recovery scan contract in both agent templates and both mirrors (T2) | **High** — a defect is discovered only during crash recovery, when nothing else is working | Operator review; T2 blocks on T1 so the classification exists first | Revert all four copies together; contract is prose, no persisted state |
| Change the instruction file and its template (T1) | Medium — mirrored pair, consumer-installed; also removes the raw-create advertisement from the authoritative Checkpoint Payload Contract | Standard PR review | Revert both together and restore the install-manifest checksums in the same revert |
| Add producer-guarantee wiring to Stage and Ship templates + mirrors (T3, T4) | Medium — two mirrored pairs | Standard PR review | Revert each pair together; T3 and T4 are mutually independent |
| Atomic activation across contract, producers, registries and enforcement (**T9**) | **High** — mis-ordered, it deadlocks every agent's startup | Standard PR review; ordering enforced by three `blocks` edges into T9 (`T3, T4, T5`) and by `T6 → T9` | Restore the direct create invocations in the two templates; the adapter is inert without them |
| *(explicitly excluded)* Repair any committed checkpoint record | High — prohibited by instruction rule 2 | Operator-only, outside this plan | Not applicable: out of scope |

**Rollback coupling.** T1's pair, T2's four copies, T3's pair, and T4's pair
each revert atomically. T5, T7b and T8b are inert until T9 wires them. T5a, T5b, T7a, T8a, T6, T10 and
T11 are test-only. Nothing in the unit writes, edits, or deletes a checkpoint
file.

**Monitoring and validation window.** The first agent session after merge is
the live signal: its end-of-session checkpoint must be written through
`autoharness checkpoint create`, which validates before the create call, and
the next session's startup scan must report a `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` set
with an empty fail-closed bucket. T11 asserts the latter on every CI run.

**Operator checkpoints.** One: review of the startup-recovery contract change
(T2) before merge, because a defect in it is only observable during recovery.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers and MUST apply the Agent-Native Parity
persona inline, because the change is almost entirely to agent-template
contract text consumed by agents rather than by code.

**Unresolved operator decisions blocking safe execution.** None.
