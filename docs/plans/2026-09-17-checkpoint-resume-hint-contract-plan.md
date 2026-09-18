---
title: "Checkpoint resume_hint: producer guarantee, deterministic validation, and historical-record compatibility policy"
description: "Implementation plan closing the autoharness-owned half of the checkpoint resume_hint gap: a historical-record COMPATIBILITY POLICY for pre-existing resolved checkpoints lacking the field (classification and reporting only — no migration mechanism ships and no committed checkpoint file is ever rewritten), a producer guarantee that every harness checkpoint author emits a specific top-level resume_hint including the minimal end-of-session shape, and deterministic author-time validation exposed as one executable adapter boundary in front of the official create operation, implemented as its own task and ENABLED by a separate task that cannot run until both producer paths are updated, with invariant-based regression tests rather than a pinned record count — ordered policy-first so the validator cannot deadlock startup on an unrepairable historical record, with that ordering encoded as explicit task dependencies rather than prose. The upstream backlogit validator, schema, and CLI-help change is explicitly excluded."
doc_type: plan
source: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
date: 2026-09-17
status: reviewed
plan_id: checkpoint-resume-hint-contract
plan_role: active
revision: 6
supersedes: null
superseded_by: null
source_history:
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-05.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-06.md
  - docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md
review_manifest: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
revision_note: "Revision 6 is maintained as one coherent current-state contract rather than as an accreting record of corrections. Prior-revision deltas, superseded requirement variants, and reviewer chronology are not carried in the body: the immutable per-attempt review artifacts listed in source_history and the mutable verdict manifest named by review_manifest are the authoritative record of that chronology. Latest attempt and verdict are read from the manifest, never from this file."
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

### Part 1b — the authoritative Checkpoint Payload Contract is updated atomically

The Checkpoint Payload Contract currently advertises
`backlogit_create_checkpoint` (MCP) and `backlogit checkpoint create` (CLI) as
the permitted way a harness producer writes a checkpoint. Once the adapter in
Part 2 exists, that advertisement is **wrong** — it names the exact bypass the
adapter is a gate in front of, in the document agents are instructed to obey.

The contract is therefore updated so that, **for harness producers**, the only
permitted create path is `autoharness checkpoint create`. The raw backlogit
create operation remains the mechanism the adapter itself calls; it is no
longer a path a producer may reach directly.

The update is **atomic across the authoritative document and its template**:

| Surface | Role |
|---|---|
| `.github/instructions/backlogit.instructions.md` | Installed authoritative contract |
| `templates/instructions/backlogit.instructions.md.tmpl` | Template the installed copy is generated from |

Both are changed in the same task and revert together. Changing one alone
produces a workspace whose installed instruction and its own template disagree,
which is a drift defect the next `autoharness install` would silently resolve in
the wrong direction.

**Manifest checksum obligation.** Any installed file this update touches is
recorded in the workspace install manifest with a content checksum. The task
regenerates those checksums for every file it modifies, in the same change, so
the manifest does not report drift against files the update itself authored. If
a modified surface is not manifest-tracked, that is recorded explicitly rather
than assumed.

**Not implemented in this Stage cycle.** This plan *plans* the change; no
source file, template, or instruction is edited by Stage. The work is executed
by Ship under `180-S`.

### Part 1 — producer guarantee

Every harness checkpoint producer — Stage, Ship, and any other — emits a
top-level `resume_hint` specific enough to support a later recovery decision.
This explicitly includes the **minimal end-of-session completion checkpoint**,
which is the shape `checkpoint-20260916-064310.json` appears to be. A hint must
name the next actionable step or state explicitly that no re-entry is required;
a generic or empty string does not satisfy the guarantee.

### Part 2 last — deterministic validation

Autoharness-side validation plus regression tests that fail deterministically
when a **harness-authored** `schema_version: 1` payload omits `resume_hint`, so
the gap is caught at author time rather than at recovery time.

| Token | Origin | Severity | Condition |
|---|---|---|---|
| `CHECKPOINT_RESUME_HINT_MISSING` | `harness` | blocking | Harness-authored V1 payload with no top-level `resume_hint` |
| `CHECKPOINT_RESUME_HINT_EMPTY` | `harness` | blocking | Present but blank or whitespace-only |
| `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` | `historical` | reported | Pre-existing record with `status: resolved` and no usable hint; reported and excluded from the candidate set |
| `CHECKPOINT_ACTIVE_HINTLESS` | `historical` | **blocking** | Pre-existing record with `status: active` and a missing, empty, or whitespace-only hint; fails closed to operator handoff |

`validate_checkpoint_payload` returns a **`ValidationOutcome` for every input**,
never `None` and never an unclassified result. For `origin="historical"` the
outcome is decided by `status` alone: `resolved` → the reported legacy
classification; `active` → the blocking `CHECKPOINT_ACTIVE_HINTLESS`. A
historical record with a usable hint returns a clean outcome. There is no
fourth branch.

Validation applies at **author time** on payloads this harness produces. It
does not retroactively invalidate records it did not author, which is precisely
what Part 3 makes safe. The one thing it *does* enforce against historical
records is the active-hintless fail-closure, which is a **recovery-time**
judgement about candidate eligibility rather than an author-time judgement
about authorship.

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
autoharness checkpoint create --state-dump <path-or-json> [--origin harness]
```

* **It is the only create path a harness producer may use.** The adapter
  validates the payload and, only on a clean outcome, performs the
  `backlogit checkpoint create` call itself. A producer that reaches
  `backlogit_create_checkpoint` / `backlogit checkpoint create` directly has
  bypassed the gate — and because the adapter is a *command*, "did this
  template invoke the adapter or the raw tool?" is a decidable, greppable
  property of the template text rather than an unverifiable intention.
* **Validation is strictly pre-write.** The adapter evaluates the payload
  before any create call is issued. On `CHECKPOINT_RESUME_HINT_MISSING` or
  `CHECKPOINT_RESUME_HINT_EMPTY` it exits non-zero and **writes nothing**, so
  no malformed record is created — which matters because a written checkpoint
  cannot be repaired through the official create operation.
* **`validate_checkpoint_payload(payload, *, origin) -> ValidationOutcome`
  is the single predicate**, in `src/autoharness/`, and the adapter is its
  only producer-side caller. The startup recovery scan calls the same predicate
  with `origin="historical"`. One definition, two callers, no per-agent copy
  and no re-stated rule in an agent template.
* **`origin` partitions the token space structurally.** Only
  `origin="harness"` can emit `CHECKPOINT_RESUME_HINT_MISSING` /
  `CHECKPOINT_RESUME_HINT_EMPTY`; only `origin="historical"` can emit
  `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` or `CHECKPOINT_ACTIVE_HINTLESS`. The
  two historical outcomes are disjoint and selected by `status`, so the
  compatibility exemption can never absorb an active record.
* **Outcome is data, not an exception**, so the scan can report while the
  adapter halts.
* The adapter **adds no capability** beyond backlogit's own create operation
  and introduces no second checkpoint store. It is a gate in front of one call,
  nothing more. `.github/instructions/backlogit.instructions.md` rule 2 —
  checkpoints are written only through the official create operation — is
  preserved, because the adapter *is* how that operation is reached. What
  changes (T1, Part 1b) is that document's advertisement of the **raw** create
  call as a path a **harness producer** may take directly; that advertisement
  is removed from the installed instruction and its template atomically.

**Wiring — the producer surfaces known today:**

| Producer path | Call site | Enforced by |
|---|---|---|
| Stage checkpoint author | The Step 6 checkpoint write becomes an `autoharness checkpoint create` invocation, in `templates/agents/_stage.agent.md.tmpl` + installed mirror | T3 (text) / T5c (adapter wiring) |
| Ship checkpoint author | The closure-step checkpoint write becomes an `autoharness checkpoint create` invocation, in `templates/agents/_ship.agent.md.tmpl` + installed mirror | T4 (text) / T5c (adapter wiring) |
| Startup recovery scan | Inside the enumeration loop, calling the predicate with `origin="historical"` | T2 |
| Checkpoint Payload Contract (installed + template) | Stops advertising the raw create call as a producer path | T1 (Part 1b) |

This table is **not an exhaustive whitelist**. It records the surfaces known at
authoring time. A structural assertion hardcoded to these rows would silently
pass the moment a third producer appears — which is how this class of gate is
normally defeated — so the structural verification is **inventory-derived**
(T6b), not table-derived.

A producer path that constructs a payload and writes it without going through
the adapter is itself the defect. **T6 asserts that for the wired producers**
and **T6b asserts it across the whole discovered inventory**; both therefore run
**after** T5c — see the ordering section.

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
  (see T7).
* backlogit version `1.10.1-0.20260823032255-b07729386a31+dirty` locally.
  CI installs a **different** binary: pinned `v1.9.0`, checksum-verified
  (`.github/workflows/ci.yml`). Any behavioural assertion about the checkpoint
  API must therefore hold on `v1.9.0` or be explicitly version-guarded; see
  the sibling SAFE_CLOSE plan, which carries the same divergence.

## Work Breakdown

| # | Task | Scope | Blocked by |
|---|---|---|---|
| T1 | Author the historical-record **compatibility policy**, the `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` classification and the blocking `CHECKPOINT_ACTIVE_HINTLESS` outcome, **and perform the atomic Checkpoint Payload Contract update (Part 1b)** so the raw backlogit create call is no longer advertised as a harness producer path — installed instruction and its template changed together, with install-manifest checksums regenerated for every modified tracked file | `.github/instructions/backlogit.instructions.md` + `templates/instructions/backlogit.instructions.md.tmpl` | — |
| T2 | Wire the classification into the startup recovery scan contract in the agent templates and installed mirrors, including the deterministic `active` → blocking branch | `templates/agents/` + `.github/agents/` | T1 |
| T3 | **Producer 1 of 2** — guarantee for the Stage checkpoint author, including the minimal completion shape | `templates/agents/_stage.agent.md.tmpl` + installed mirror | T1 |
| T4 | **Producer 2 of 2** — guarantee for the Ship checkpoint author, including the minimal completion shape | `templates/agents/_ship.agent.md.tmpl` + installed mirror | T1 |
| T5a | **RED** — author the four-token contract tests against **both** `validate_checkpoint_payload` and the `autoharness checkpoint create` adapter command, and observe them failing before either exists | `tests/` | T1, T2 |
| T5 | **IMPLEMENTATION** — implement `validate_checkpoint_payload()`, the four tokens, and the `autoharness checkpoint create` adapter command as an invocable boundary, **not yet referenced by any agent template** (inert) | `src/autoharness/` | T5a |
| T5c | **ENABLE** — route both producer templates through `autoharness checkpoint create`, replacing their direct `backlogit_create_checkpoint` / `backlogit checkpoint create` invocations | `templates/agents/` + both installed mirrors | T3, T4, T5 |
| T6 | **GREEN + structural verification of the wired producers** — observe the token suite passing against the shipped adapter, plus the active-hintless fail-closed regression, plus the assertion that both wired producer templates invoke the adapter and that neither retains a direct backlogit create call or re-states the predicate inline | `tests/` | T5c |
| T6b | **INVENTORY-BACKED structural verifier** — enumerate **every** checkpoint producer surface in the repository from an inventory rather than a hardcoded list, and assert that none of them reaches `backlogit_create_checkpoint` / `backlogit checkpoint create` directly. Also assert the Checkpoint Payload Contract no longer advertises the raw path, that installed instruction and template agree, and that install-manifest checksums match every modified tracked file | `tests/` | T6 |
| T7 | Invariant-based **live-corpus audit** over the committed checkpoint corpus | `tests/` | T6 |

#### T6b — what "inventory" means, precisely

The inventory is **derived, not written down**. T6b discovers producer surfaces
by scanning the repository for any file that references a checkpoint-create
operation by name, across **all** of:

* `templates/agents/` and `.github/agents/`
* `templates/skills/` and `.github/skills/`
* `templates/instructions/` and `.github/instructions/`
* `docs/` guidance that instructs an agent to create a checkpoint
* `src/autoharness/` (where only the adapter itself may reach the raw call)

Each discovered reference is classified as **adapter invocation** (allowed),
**raw create inside the adapter implementation** (allowed, exactly one site), or
**raw create anywhere else** (fail). A newly added producer that bypasses the
adapter therefore fails the test by being *discovered*, not by being *listed*.
Two agent templates are the surfaces known today; they are an input to the
assertion, never its boundary.


### Ordering enforcement (machine-encoded)

The binding order is **policy → producers → red → implementation → enable →
green/structural → live audit**, encoded as `blocks` edges:

* `T2 → T1`: the recovery scan cannot reference a classification the policy has
  not defined.
* `T3 → T1` and `T4 → T1`: a producer guarantee is written against the policy,
  not ahead of it. T3 and T4 are mutually independent and may execute in either
  order or in parallel; both are Medium-risk agent-template mirror pairs.
* `T5a → T1, T2`: the tokens must be defined before tests can be authored
  against them. **T5a does not depend on T5** — that is what makes it a genuine
  red phase.
* `T5 → T5a`: the implementation turns an existing, observed-failing suite
  green. The adapter ships here but nothing invokes it yet, so it is inert.
* `T5c → T3, T4, T5`: **enforcement cannot be switched on before BOTH producers
  are updated and the adapter exists.** This is the correctness constraint, not
  a preference: it is the difference between closing a gap and manufacturing a
  startup deadlock, and it is the entry's own recorded escalation trigger (b).
* `T6 → T5c`: **green and the structural verifier observe the wired system.**
  The token suite is asserted against the shipped adapter, and the structural
  assertion — both templates invoke `autoharness checkpoint create`, neither
  retains a direct backlogit create call, neither re-states the predicate — is
  made against wiring that exists. A structural assertion may never precede the
  wiring it asserts, so no edge runs from T5c to T6.
* `T7 → T6`: auditing the live corpus is only meaningful once enforcement is on
  and verified.
* `T6b → T6`: the inventory-backed structural verifier runs after the wired
  system is green. T6b and T7 are mutually independent terminal tasks and may
  execute in either order or in parallel.

**The five-node TDD spine, stated once and encoded exactly:**

```text
T5a (RED)  →  T5 (IMPLEMENT, inert)  →  T5c (ENABLE wiring)  →  T6 (GREEN + structural)  →  T7 (live audit)
172.008-T  →  172.005-T              →  172.009-T            →  172.006-T                →  172.007-T
```

No other edge exists among these five, and no edge runs backwards along it. The
only additional inbound edges are `T5c → T3, T4` (both producers must have
adopted the contract before enablement) and `T5a → T1, T2` (tokens must exist
before tests can assert them); neither reorders the spine.

### T7 — invariant-based, not count-pinned

T7 asserts **invariants over whatever corpus is present**, with no cardinality
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
   authored records**: no record authored after T5c enables enforcement may
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
| R1 | Validator lands before policy and deadlocks startup | T5c blocks on T1, T2 (via T3/T4), T3, T4 and T5 — every functional predecessor, not just the policy pair. This is the entry's own recorded escalation trigger (b) |
| R2 | The legacy exemption silently grows into a permanent tolerance | The classification is enumerated and reported by filename at every scan, and T7 asserts the fail-closed bucket stays empty and that no newly authored record may enter the legacy set |
| R3 | An `active` record is accidentally grandfathered, or lands in an unspecified outcome | The historical classification is **total** and decided by `status` alone: `resolved` → reported legacy, `active` → blocking `CHECKPOINT_ACTIVE_HINTLESS`. T6 carries an explicit active-hintless fail-closed case, T5a asserts it red first, and T7 invariant 3 asserts it over the live corpus |
| R4 | Someone pulls the upstream validator change into this scope | Stated as excluded in frontmatter, in the Ownership boundary section, and in Out of scope |
| R5 | A producer path constructs a payload without validating it | The adapter command is the only create path; T6 asserts structurally that neither wired template retains a direct backlogit create call, and T6b asserts it across the discovered inventory so a third producer cannot slip past. A second implementation is a review-visible defect |
| R6 | The inventory test fails for reasons unrelated to the contract | T7 pins no count and no filename set; it asserts totality, emptiness of the fail-closed bucket, and determinism |
| R7 | Validation after write leaves a malformed record on disk that cannot be repaired | The adapter validates the pre-write payload and writes nothing on a failing outcome; Verification asserts ordering explicitly |
| R8 | The adapter is treated as a second checkpoint store or drifts from backlogit's create semantics | The adapter adds no capability: it validates, then performs the official `backlogit checkpoint create` call. Instruction rule 2 is preserved because the adapter *is* how that operation is reached |
| R9 | A structural assertion is written against wiring that does not yet exist and is quietly weakened until it asserts nothing | T6 blocks on T5c, so the wiring exists before it is asserted, and no reverse edge from T5c onto T6 exists |
| R10 | The authoritative contract keeps advertising the raw create call, so agents are simultaneously told to use the adapter and told the raw call is permitted | T1 performs the contract update atomically across installed instruction and template, and T6b asserts the advertisement is gone, that the two surfaces agree, and that install-manifest checksums match |
| R11 | A hardcoded two-file structural assertion silently passes when a third producer is added | T6b derives the surface set by repository scan and is verified against a synthetic third producer that must fail |

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
| H1 | A binding policy→producers→validation order carried as prose leaves the producers unordered against the validator — the half that actually deadlocks | Every edge encoded: `T5a → T5 → T5c → T6 → T7`, with `T5c → T3, T4, T5` |
| H2 | A package-local Python function is not an enforceable boundary against Markdown producers that call backlogit MCP/CLI directly, so the guarded paths connect to nothing | The boundary is the executable `autoharness checkpoint create` adapter, which producers invoke *instead of* the raw create operation, with `validate_checkpoint_payload()` as its single implementation |
| H3 | Each agent template re-stating the predicate inline produces two drifting definitions of the same rule | Single-definition constraint stated normatively; T6 asserts both wired templates invoke the adapter, retain no direct backlogit create call, and re-state nothing; T6b extends that assertion to every discovered producer surface |
| H4 | Validating after the create call leaves a malformed record on disk that cannot be repaired through the official operation | The adapter validates the pre-write payload and writes nothing on a failing outcome; Verification asserts ordering |
| H5 | "Does not retroactively invalidate records it did not author" is a convention with no mechanism | `origin` parameter partitions the token space structurally: harness-origin cannot emit either historical token, historical-origin cannot emit the missing/empty tokens |
| H6 | Pinning a checkpoint record count produces a test that fails on every checkpoint-writing session for reasons unrelated to its contract | T7 pins no cardinality; it asserts totality, an empty fail-closed bucket, determinism, and no-new-legacy-after-enforcement, with the count observed and reported only. Synthetic fixtures cover shapes the live corpus may lack |
| H7 | Describing the repaired record as a migrated historical record implies a migration ran and an official repair mechanism exists — neither is true | Provenance stated precisely as an operator-authored, operator-authorized pre-existing repair, with the residual policy risk recorded and precedent-use explicitly denied |
| H8 | Recording only the local `+dirty` backlogit build hides that CI runs a different pinned binary | Divergence recorded in the evidence section with a pointer to the sibling SAFE_CLOSE plan, which owns the version-contract deliverable |
| H9 | "An active hintless record fails closed exactly as today" names a behaviour but no token, so the outcome is unobservable, untestable, and indistinguishable from an unspecified result | `CHECKPOINT_ACTIVE_HINTLESS` is a concrete blocking token; `validate_checkpoint_payload` is specified **total** over historical input, decided by `status` alone, with the resolved-compatibility and active-fail-closed rules disjoint and neither widening the other |
| H10 | The authoritative Checkpoint Payload Contract keeps advertising the raw create call as a permitted producer path, so the gate is contradicted by the very document agents obey | T1 updates installed instruction and template atomically (Part 1b), regenerates install-manifest checksums for every modified tracked file, and T6b asserts all three properties |
| H11 | A structural gate hardcoded to the two producer surfaces known today is defeated by adding a third | T6b derives the surface set by repository scan across agents, skills, instructions, docs and source, and is itself verified against a synthetic bypassing producer that must fail |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Change the startup recovery scan contract in both agent templates and both mirrors (T2) | **High** — a defect is discovered only during crash recovery, when nothing else is working | Operator review; T2 blocks on T1 so the classification exists first | Revert all four copies together; contract is prose, no persisted state |
| Change the instruction file and its template (T1) | Medium — mirrored pair, consumer-installed; also removes the raw-create advertisement from the authoritative Checkpoint Payload Contract | Standard PR review | Revert both together and restore the install-manifest checksums in the same revert |
| Add producer-guarantee wiring to Stage and Ship templates + mirrors (T3, T4) | Medium — two mirrored pairs | Standard PR review | Revert each pair together; T3 and T4 are mutually independent |
| Enable `autoharness checkpoint create` on both producer paths (**T5c**) | **High** — mis-ordered, it deadlocks every agent's startup | Standard PR review; ordering enforced by three `blocks` edges into T5c (`T3, T4, T5`) and by `T6 → T5c` | Restore the direct create invocations in the two templates; the adapter is inert without them |
| *(explicitly excluded)* Repair any committed checkpoint record | High — prohibited by instruction rule 2 | Operator-only, outside this plan | Not applicable: out of scope |

**Rollback coupling.** T1's pair, T2's four copies, T3's pair, and T4's pair
each revert atomically. T5 is inert until its call sites exist. T5a, T6, T6b and
T7 are test-only. Nothing in the unit writes, edits, or deletes a checkpoint
file.

**Monitoring and validation window.** The first agent session after merge is
the live signal: its end-of-session checkpoint must be written through
`autoharness checkpoint create`, which validates before the create call, and
the next session's startup scan must report a `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` set
with an empty fail-closed bucket. T7 asserts the latter on every CI run.

**Operator checkpoints.** One: review of the startup-recovery contract change
(T2) before merge, because a defect in it is only observable during recovery.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers and MUST apply the Agent-Native Parity
persona inline, because the change is almost entirely to agent-template
contract text consumed by agents rather than by code.

**Unresolved operator decisions blocking safe execution.** None.
