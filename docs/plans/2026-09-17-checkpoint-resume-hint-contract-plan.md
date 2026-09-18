---
title: "Checkpoint resume_hint: producer guarantee, deterministic validation, and historical-record compatibility policy"
description: "Implementation plan closing the autoharness-owned half of the checkpoint resume_hint gap: a historical-record COMPATIBILITY POLICY for pre-existing resolved checkpoints lacking the field (classification and reporting only — no migration mechanism ships and no committed checkpoint file is ever rewritten), a producer guarantee that every harness checkpoint author emits a specific top-level resume_hint including the minimal end-of-session shape, and deterministic author-time validation exposed as one callable boundary, implemented as its own task and ENABLED by a separate task that cannot run until both producer paths are updated, with invariant-based regression tests rather than a pinned record count — ordered policy-first so the validator cannot deadlock startup on an unrepairable historical record, with that ordering encoded as explicit task dependencies rather than prose. The upstream backlogit validator, schema, and CLI-help change is explicitly excluded."
doc_type: plan
source: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
date: 2026-09-17
status: reviewed
revision: 5
revision_note: "Revision 5 (remediation cycle 3) answers review attempt 05, which returned BLOCKED at revision 4 on two findings. (1) NOT AN ENFORCEABLE BOUNDARY. Revision 4 named a package-local Python function, `validate_checkpoint_payload()` in `src/autoharness/`, as the boundary both producer paths must route through — but Stage and Ship are MARKDOWN AGENT TEMPLATES that call `backlogit_create_checkpoint` (MCP) or `backlogit checkpoint create` (CLI) DIRECTLY and import no Python. A library function beside that call path cannot intercept it, so 'both producer paths call this exact function' was an instruction with no mechanism, and T6's structural assertion had no wiring to assert. Revision 5 replaces it with an EXECUTABLE ADAPTER, `autoharness checkpoint create --state-dump <payload> [--origin harness]`, which producers invoke INSTEAD OF the raw create operation: it validates pre-write, writes NOTHING on a failing outcome, and performs the official backlogit create call itself on a clean one. `validate_checkpoint_payload()` remains the single predicate and the adapter is its only producer-side caller, so instruction rule 2 is preserved and 'did this template invoke the adapter or the raw tool?' becomes a decidable property of the template text. (2) DEPENDENCY INVERSION. Revision 4 encoded `T5c -> T3, T4, T5, T6` while T6 was specified to assert the producer call sites that T5c CREATES — a structural assertion preceding its own wiring, which could only have failed or been quietly weakened. Revision 5 swaps the edges: `T5c -> T3, T4, T5` and `T6 -> T5c`, with `T7 -> T6`. Final order: policy -> producers -> red -> implementation -> enable -> green/structural -> live audit. Revision 5 is STAGE-REMEDIATED AND PENDING INDEPENDENT REVIEW ATTEMPT 06; Stage does not review its own remediation and asserts no PASS. Revision 4 (remediation cycle 2) closed four findings and superseded revision 3. (1) The word 'migration' is removed from the title and throughout: no migration mechanism ships, so the surface is renamed to a historical-record COMPATIBILITY POLICY. (2) The volatile inventory count pin is eliminated in fact, not just in intent — the corpus enumerated 53 records at this session against the 51 pinned in the harvested task and the 52 noted in revision 3, which is itself the proof that a cardinality literal is the wrong assertion; the audit is re-specified over three invariants (classification totality, active-never-exempt, no-new-legacy-after-enforcement). (3) Validator IMPLEMENTATION and ENFORCEMENT ENABLEMENT are split into separate tasks, because revision 3 had one task both implement and wire the validator while its prose promised enforcement would wait for the producers — a contradiction that no dependency graph could express. Enablement now blocks on both producer tasks plus the implementation plus the green suite. (4) A red-phase task is added ahead of the implementation so the three-token contract tests are authored and observed failing before the boundary exists. Revision 4 also adopts decision revision 3. The bounded audit trail lives in `review_history`."
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
linked_review: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
review_history:
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-05.md
review_history_note: "Attempts 01-02 were authored as one mutable file covering two cycles; it is preserved verbatim and classified rather than retroactively split into records that were never independently authored. Attempt 03 is a conforming single-attempt immutable artifact. Attempt 04 records local review cycle 2 (BLOCKED at revision 3, on non-propagation of the design into the executable backlog records) and the Stage remediation response that produced this revision."
latest_review_attempt: 5
latest_review_artifact: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-05.md
latest_review_verdict: REMEDIATED-PENDING-REVIEW
latest_review_verdict_note: "Attempt 05 returned BLOCKED at plan revision 4. Stage remediation cycle 3 closed every attempt-05 finding and raised this plan to revision 5. Stage does not review its own remediation, so NO PASS is asserted at revision 5; the next independent reviewer pass is attempt 06."
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
this session over the Ship-owned residual-risk records and **no late identifier
surfaced**. The `N/A` values stand as truthful terminal records. Non-blocking.

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
treated by the fail-closed startup scan:

* A record with `status: resolved` **and** no `resume_hint` is classified
  `LEGACY_HINTLESS_RESOLVED`. It is enumerated, reported, and **excluded from
  the candidate set** — it can never be an active recovery candidate by
  definition, so excluding it removes no recovery capability.
* A record with `status: active` and no `resume_hint` is **not** exempt. It
  fails closed to operator handoff exactly as today. No active record is ever
  grandfathered.
* `LEGACY_HINTLESS_RESOLVED` is a **closed, enumerable** classification, not an
  open-ended tolerance: the scan reports the count and the filenames so the
  exemption is visible rather than silent.
* An operator may repair a historical record out-of-band; the policy neither
  requires nor performs such a repair.

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

| Token | Condition |
|---|---|
| `CHECKPOINT_RESUME_HINT_MISSING` | Harness-authored V1 payload with no top-level `resume_hint` |
| `CHECKPOINT_RESUME_HINT_EMPTY` | Present but blank or whitespace-only |
| `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` | Pre-existing resolved record, reported and excluded |

Validation applies at **author time** on payloads this harness produces. It
does not retroactively invalidate records it did not author, which is precisely
what Part 3 makes safe.

#### The validation boundary (revision 5 — an executable adapter, not a library call)

Revision 2 specified the three tokens but named no callable surface. Revision 4
named one — `validate_checkpoint_payload(payload, *, origin)` in
`src/autoharness/` — but review attempt 05 found that **it is not an enforceable
boundary for the two producers it is supposed to guard.** Stage and Ship are
**Markdown agent templates**. They do not import Python; they call
`backlogit_create_checkpoint` (MCP) or `backlogit checkpoint create` (CLI)
**directly**. A package-local Python function sitting beside that call path
cannot intercept it. "Both producer paths call this exact function" was
therefore an instruction an agent had no mechanism to obey, and T6's structural
assertion would have been asserting a wiring that could not exist.

**The boundary is an executable adapter command** that producers invoke
*instead of* the backlogit create operation:

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
  remains the single predicate**, in `src/autoharness/`, and the adapter is its
  only producer-side caller. The startup recovery scan calls the same predicate
  with `origin="historical"`. One definition, two callers, no per-agent copy
  and no re-stated rule in an agent template.
* **`origin` still partitions the token space structurally.** Only
  `origin="harness"` can emit the missing/empty tokens; only
  `origin="historical"` can emit `CHECKPOINT_LEGACY_HINTLESS_RESOLVED`.
* **Outcome is data, not an exception**, so the scan can report while the
  adapter halts.
* The adapter **adds no capability** beyond backlogit's own create operation
  and introduces no second checkpoint store. It is a gate in front of one call,
  nothing more. `.github/instructions/backlogit.instructions.md` rule 2 —
  checkpoints are written only through the official create operation — is
  preserved, because the adapter *is* how that operation is reached.

**Wiring — both producer paths, named explicitly:**

| Producer path | Call site | Enforced by |
|---|---|---|
| Stage checkpoint author | The Step 6 checkpoint write becomes an `autoharness checkpoint create` invocation, in `templates/agents/_stage.agent.md.tmpl` + installed mirror | T3 (text) / T5c (adapter wiring) |
| Ship checkpoint author | The closure-step checkpoint write becomes an `autoharness checkpoint create` invocation, in `templates/agents/_ship.agent.md.tmpl` + installed mirror | T4 (text) / T5c (adapter wiring) |
| Startup recovery scan | Inside the enumeration loop, calling the predicate with `origin="historical"` | T2 |

A producer path that constructs a payload and writes it without going through
the adapter is itself the defect. **T6 asserts that**, and T6 therefore runs
**after** T5c — see the ordering section.

## Evidence recorded this session (read-only)

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
  reason Part 3 exists. Treating this file as a "worked example of a migrated
  historical record" — as revision 2 did — overstates it, because no migration
  ran.
  **Residual policy risk, recorded not waived:** the repair was a direct edit
  to a file under `.backlogit/checkpoints/`, which
  `.github/instructions/backlogit.instructions.md` rule 2 reserves to the
  official create operation. It was operator-performed and operator-authorized,
  which is the only authority under which it is permissible, and it is recorded
  here so the deviation is visible rather than silently normalized. No agent
  may cite it as precedent. This plan modifies neither the file nor its
  archived history.
* Full unfiltered checkpoint enumeration at this session's remediation cycle:
  **53** records under `.backlogit/checkpoints/`, plus 75 under
  `.backlogit/archive/checkpoints/`. Zero validation anomalies, zero active
  `stage`-owned candidates. The count was recorded as **51** in revision 2 and
  **52** in revision 3, and was already stale at each writing. **Three
  successive readings, three different values — this is exactly why the
  inventory test is invariant-based and pins no count** (see T7).
* backlogit version `1.10.1-0.20260823032255-b07729386a31+dirty` locally.
  CI installs a **different** binary: pinned `v1.9.0`, checksum-verified
  (`.github/workflows/ci.yml`). Any behavioural assertion about the checkpoint
  API must therefore hold on `v1.9.0` or be explicitly version-guarded; see
  the sibling SAFE_CLOSE plan, which carries the same divergence.

## Work Breakdown

| # | Task | Scope | Blocked by |
|---|---|---|---|
| T1 | Author the historical-record **compatibility policy** and the `LEGACY_HINTLESS_RESOLVED` classification | `.github/instructions/backlogit.instructions.md` + `templates/instructions/` | — |
| T2 | Wire the classification into the startup recovery scan contract in the agent templates and installed mirrors | `templates/agents/` + `.github/agents/` | T1 |
| T3 | **Producer 1 of 2** — guarantee for the Stage checkpoint author, including the minimal completion shape | `templates/agents/_stage.agent.md.tmpl` + installed mirror | T1 |
| T4 | **Producer 2 of 2** — guarantee for the Ship checkpoint author, including the minimal completion shape | `templates/agents/_ship.agent.md.tmpl` + installed mirror | T1 |
| T5a | **RED** — author the three-token contract tests against `validate_checkpoint_payload` and the `autoharness checkpoint create` adapter, and observe them failing before either exists | `tests/` | T1, T2 |
| T5 | **IMPLEMENTATION** — implement `validate_checkpoint_payload()`, the three tokens, and the `autoharness checkpoint create` adapter command as a callable/invocable boundary, **not yet referenced by either agent template** | `src/autoharness/` | T5a |
| T5c | **ENABLE** — route both producer templates through `autoharness checkpoint create`, replacing their direct `backlogit_create_checkpoint` / `backlogit checkpoint create` invocations | `templates/agents/` + both installed mirrors | T3, T4, T5 |
| T6 | **GREEN + structural verifier** — observe the token suite passing against the shipped adapter, plus the active-record-not-exempt regression, **plus the structural assertion that both producer templates invoke the adapter and that neither retains a direct backlogit create call or re-states the predicate inline** | `tests/` | T5c |
| T7 | Invariant-based **live-corpus audit** over the committed checkpoint corpus | `tests/` | T6 |

### Ordering enforcement (revision 5)

The binding order is **policy → producers → red → implementation → enable →
green/structural → live audit**. Revision 4 encoded
`T5c → T3, T4, T5, T6` and `T6 → T5`, which inverted the last two steps: T6 was
specified to assert that both producer call sites exist, while T5c — the task
that *creates* those call sites — was blocked by T6. A structural assertion
cannot precede the wiring it asserts; as encoded, T6 could only ever have
failed, or have been quietly weakened until it asserted nothing. Revision 5
swaps the two edges:

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
  T5c no longer depends on T6.
* `T6 → T5c`: **green and the structural verifier observe the wired system.**
  The token suite is asserted against the shipped adapter, and the structural
  assertion — both templates invoke `autoharness checkpoint create`, neither
  retains a direct backlogit create call, neither re-states the predicate —
  is made against wiring that now exists.
* `T7 → T6`: auditing the live corpus is only meaningful once enforcement is on
  and verified.

### T7 — invariant-based, not count-pinned

Revision 2's T7 asserted the classification over "this repository's 51
committed records", and the harvested task record still carried that literal.
Revision 4 records the decisive evidence: **the corpus enumerated 53 records at
this session** — against 51 in revision 2 and 52 in revision 3. A value that has
been wrong at three successive readings is not a stale constant to refresh; it is
the wrong kind of assertion. The count changes on every session that writes a
checkpoint, so the test would fail for a reason unrelated to the contract it
guards — a brittleness defect, not a coverage gain.

T7 instead asserts **invariants over whatever corpus is present**, with no
cardinality pinned anywhere:

1. Every record under `.backlogit/checkpoints/` classifies into exactly one
   bucket: valid-with-hint, `LEGACY_HINTLESS_RESOLVED`, or fail-closed
   candidate. No record is unclassified.
2. The fail-closed bucket is **empty**. This is the property that actually
   matters — a non-empty bucket means startup halts.
3. Every `LEGACY_HINTLESS_RESOLVED` record has `status: resolved`. An `active`
   record is never in that bucket, **at any corpus size**.
4. The classification is **total and deterministic**: running it twice over the
   same corpus yields identical results.
5. The legacy set is **monotonically non-increasing with respect to newly
   authored records**: no record authored after T5c enables enforcement may
   enter it. This is the real "the exemption cannot silently grow" property the
   count pin was reaching for, expressed as an invariant over **authorship**
   rather than over **cardinality**.
6. The reported `LEGACY_HINTLESS_RESOLVED` set is enumerated by filename and
   count in the test output, so growth is visible in CI logs. The count is
   **observed and reported, never asserted against a literal.**

Synthetic fixture corpora cover the shapes the live corpus may not contain —
an `active` hintless record, a whitespace-only hint, a legacy payload with no
`schema_version` — so coverage does not depend on what the repository happens
to hold on a given day.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* The startup scan over the committed corpus produces zero fail-closed
  handoffs and reports its `LEGACY_HINTLESS_RESOLVED` set by filename.
* No test asserts a checkpoint record count.
* Both producer templates invoke `autoharness checkpoint create`, neither
  retains a direct `backlogit_create_checkpoint` / `backlogit checkpoint create`
  invocation on the producer path, and neither agent template re-states the
  predicate inline.
* The adapter exits non-zero and writes **nothing** on
  `CHECKPOINT_RESUME_HINT_MISSING` / `_EMPTY`; no record is created.
* Validation runs **before** the create call, never after.
* No committed checkpoint file is modified by this release unit.
* `autoharness gate check` passes on every modified file.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Validator lands before policy and deadlocks startup | T5c blocks on T1, T2 (via T3/T4), T3, T4 and T5 — every functional predecessor, not just the policy pair. This is the entry's own recorded escalation trigger (b) |
| R2 | The legacy exemption silently grows into a permanent tolerance | The classification is enumerated and reported by filename at every scan, and T7 asserts the fail-closed bucket stays empty |
| R3 | An `active` record is accidentally grandfathered | T6 carries an explicit active-record-not-exempt case; T7 invariant 3 asserts it over the live corpus |
| R4 | Someone pulls the upstream validator change into this scope | Stated as excluded in frontmatter, in the Ownership boundary section, and in Out of scope |
| R5 | A producer path constructs a payload without validating it | The adapter command is the only create path; T6 asserts structurally that neither template retains a direct backlogit create call. A second implementation is a review-visible defect |
| R6 | The inventory test fails for reasons unrelated to the contract | T7 pins no count and no filename set; it asserts totality, emptiness of the fail-closed bucket, and determinism |
| R7 | Validation after write leaves a malformed record on disk that cannot be repaired | The adapter validates the pre-write payload and writes nothing on a failing outcome; Verification asserts ordering explicitly |
| R8 | The adapter is treated as a second checkpoint store or drifts from backlogit's create semantics | The adapter adds no capability: it validates, then performs the official `backlogit checkpoint create` call. Instruction rule 2 is preserved because the adapter *is* how that operation is reached |
| R9 | A structural assertion is written against wiring that does not yet exist and is quietly weakened until it asserts nothing | T6 blocks on T5c, so the wiring exists before it is asserted; the revision-4 inversion (`T5c → T6`) is removed |

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
  superseded during remediation cycle 1 through the official checkpoint
  lifecycle, and the malformed record was preserved as history rather than
  hand-edited. That handling is recorded in the session memory artifact; it is
  not a deliverable of this plan and does not reopen `904C47BC`.

## Plan Hardening Record (P-006)

Hardening applied 2026-09-18 during remediation cycle 1. Revision 2 declared
`requires_plan_hardening: "no"`; that declaration was wrong and is corrected
here (H0). The plan changes an instruction file **and** its template, changes
**both** agent templates and **both** installed mirrors, and adds executable
validation on the startup-recovery path.

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

**Instructions and learnings consulted.**
`.github/instructions/backlogit.instructions.md` (Checkpoint Payload Contract,
rules 1–5; Checkpoint-Recovery / Prune-on-Restore Protocol),
`docs/compound/2026-08-18-stage-agent-checkpoint-index-sync-ordering-self-contradiction.md`,
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`,
the Stage and Ship Crash-Resumption / Startup Recovery Protocol sections, and
`docs/scratch/bugs/2026-09-17-backlogit-checkpoint-v1-resume-hint-validation-gap.md`.

| # | Hardening finding | Resolution |
|---|---|---|
| H0 | Revision 2 declared `requires_plan_hardening: "no"` despite two template families, two installed mirrors, and a startup-path validator | Corrected to `yes`; this section is the record |
| H1 | The binding policy→producers→validation order existed as prose plus one partial edge (`T5 → T1, T2`), leaving the producers unordered against the validator — the half that actually deadlocks | Every edge encoded. **Superseded in revision 4**, which split `T5a` (red) → `T5` (implement) → `T6` (green) → `T5c` (enable). **Further corrected in revision 5**: that split inverted the last two steps, because T6 asserts producer wiring that T5c creates. Final order is `T5a → T5 → T5c → T6 → T7` |
| H2 | "Author-time validation" named no callable surface and no wiring, so the two producer paths it was meant to guard were connected to nothing | `validate_checkpoint_payload(payload, *, origin)` defined as the single predicate. **Superseded in revision 5**: a package-local Python function is not enforceable against Markdown producers that call backlogit MCP/CLI directly. The enforceable boundary is the executable `autoharness checkpoint create` adapter, which producers invoke *instead of* the raw create operation, with the predicate as its single implementation |
| H3 | Nothing prevented each agent template from re-stating the predicate inline, producing two drifting definitions of the same rule | Single-definition constraint stated normatively; T6 asserts both templates invoke the adapter, retain no direct backlogit create call, and re-state nothing |
| H4 | Validation position relative to the write was unspecified; validating after the create call would leave a malformed record on disk that cannot be repaired through the official operation | The adapter validates the pre-write payload and writes nothing on a failing outcome; Verification asserts ordering |
| H5 | "Does not retroactively invalidate records it did not author" was a convention with no mechanism | `origin` parameter partitions the token space structurally: harness-origin cannot emit the legacy token, historical-origin cannot emit the missing/empty tokens |
| H6 | T7 pinned a record count (51) that was already stale when written and changes on every checkpoint-writing session — a test that fails for reasons unrelated to its contract | T7 re-specified with no cardinality pinned; synthetic fixtures cover shapes the live corpus may lack. **Revision 4** records the decisive evidence (51 → 52 → 53 across three readings), adds the no-new-legacy-after-enforcement invariant, and requires the count be observed and reported but never asserted |
| H7 | The `checkpoint-20260916-064310.json` evidence was described as "a worked example of a migrated historical record", implying a migration ran and an official repair mechanism exists — neither is true | Provenance restated precisely as an operator-authored, operator-authorized pre-existing repair, with the residual policy risk recorded and precedent-use explicitly denied |
| H8 | The recorded backlogit version was the local `+dirty` build, with no acknowledgement that CI runs a different pinned binary | Divergence recorded in the evidence section with a pointer to the sibling SAFE_CLOSE plan, which owns the version-contract deliverable |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Change the startup recovery scan contract in both agent templates and both mirrors (T2) | **High** — a defect is discovered only during crash recovery, when nothing else is working | Operator review; T2 blocks on T1 so the classification exists first | Revert all four copies together; contract is prose, no persisted state |
| Change the instruction file and its template (T1) | Medium — mirrored pair, consumer-installed | Standard PR review | Revert both together |
| Add producer-guarantee wiring to Stage and Ship templates + mirrors (T3, T4) | Medium — two mirrored pairs | Standard PR review | Revert each pair together; T3 and T4 are mutually independent |
| Enable `autoharness checkpoint create` on both producer paths (**T5c**) | **High** — mis-ordered, it deadlocks every agent's startup | Standard PR review; ordering enforced by three `blocks` edges into T5c (`T3, T4, T5`) and by `T6 → T5c` | Restore the direct create invocations in the two templates; the adapter is inert without them |
| *(explicitly excluded)* Repair any committed checkpoint record | High — prohibited by instruction rule 2 | Operator-only, outside this plan | Not applicable: out of scope |

**Rollback coupling.** T1's pair, T2's four copies, T3's pair, and T4's pair
each revert atomically. T5 is inert until its call sites exist. T6/T7 are
test-only. Nothing in the unit writes, edits, or deletes a checkpoint file.

**Monitoring and validation window.** The first agent session after merge is
the live signal: its end-of-session checkpoint must be written through
`autoharness checkpoint create`, which validates before the create call, and
the next session's startup scan must report a `LEGACY_HINTLESS_RESOLVED` set
with an empty fail-closed bucket. T7 asserts the latter on every CI run.

**Operator checkpoints.** One: review of the startup-recovery contract change
(T2) before merge, because a defect in it is only observable during recovery.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers and MUST apply the Agent-Native Parity
persona inline, because the change is almost entirely to agent-template
contract text consumed by agents rather than by code.

**Unresolved operator decisions blocking safe execution.** None.
