---
title: "shipment-reconcile Pre-Mode: classifier-aware, member-class-scoped status contract"
description: "Implementation plan for Option A — add a classifier invocation as Pre-Mode step 2b and replace Pre-Mode step 3's single-scalar expected_status comparison with a member-class status matrix that reads declared frontmatter status regardless of storage location, tolerates-and-reports an archived qualifying feature, records the classifier reason verbatim, and halts on any unrecognised status"
source: "docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md"
date: 2026-09-07
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
stash_entry: "15A02E21"
bug_record: "docs/bugs/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-mismatch.md"
compound_learning: "docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md"
decision_status_at_planning: "decided (operator, 2026-09-07) — D-1 accepted-with-remediation, D-2 Option A, D-3 status contract; refinements R-1..R-5 binding"
related_but_distinct:
  - "docs/bugs/2026-09-07-backlog-lifecycle-missing-temporary-out-of-queue-status.md (stash 4D3826FE) — MUST NOT be merged into this shipment; interacts only via R-5"
tags:
  - "plan"
  - "shipment-closure"
  - "p-015"
  - "fail-closed-design"
  - "dogfood-parity"
---

## Problem Frame

`shipment-reconcile` Pre-Mode step 3 compares **every** manifest member's declared frontmatter
`status` against a **single scalar** `expected_status` (`done` at Ship Step 5/6 closure).

A manifest that qualifies for the P-015 CASCADE close path is **required** to contain its qualifying
root feature — full coverage is a classifier precondition — and that feature is validly `active`
until the cascade operation itself archives it. Pre-Mode therefore computes `status-mismatch` and
returns `HALT — operator reconcile required` on **every** cascade-eligible closure, before
Safe-Close Step 0(c) — the step that runs the classifier and could have known the member was a
qualifying feature — has ever executed.

The same file contradicts itself: the Cascade Close Sub-Procedure step 3 computes `required_ids`
including every qualifying feature member *"both unconditionally — never conditioned on either
artifact's own pre-close declared status"*, while Pre-Mode step 3 makes that same status decisive.

**Grounded code/text locations (verified 2026-09-07):**

| Surface | Location | Note |
|---|---|---|
| Defective per-item check | `.github/skills/shipment-reconcile/SKILL.md` line 267 (`3. **Check each manifest item**`) | resolved dogfood copy, 1082 lines |
| Paired template | `templates/skills/shipment-reconcile/SKILL.md.tmpl` line 267 | 1082 lines; **same line numbers** |
| Existing type-filter precedent | same files, Pre-Mode step 5 ("Filter to task artifacts first") | the corrective filter already exists here |
| Classifier | `src/autoharness/gates/shipment_closure.py` — `classify_shipment_close_path` (line 284), `ClosePathDecision` (line 76) | **already exposes everything needed** |
| Existing contract test | `tests/test_shipment_reconcile_record_status.py` | asserts against the **template only** |

### Critical correction to the source document's scope note

The decision artifact states Pre-Mode step 3 is *"byte-identical"* across the skill and its
template. **It is not.** Verified line-by-line: the two files are identical **modulo the
`{{BACKLOG_DIRECTORY}}` template variable**. Within the step 3 block, exactly three lines differ:

```text
line 268  resolved: `.backlogit/queue/{id}.*`      template: `{{BACKLOG_DIRECTORY}}/queue/{id}.*`
line 272  resolved: `.backlogit/archive/{id}.*`    template: `{{BACKLOG_DIRECTORY}}/archive/{id}.*`
line 277  resolved: `.backlogit/queue/`            template: `{{BACKLOG_DIRECTORY}}/queue/`
```

**Implementation hazard this creates:** R-1 requires reading declared `status` from `queue/` *or*
`archive/`, so the new text will reference both directories more, not less. A copy-paste paired edit
will silently hardcode `.backlogit` into the template and break variable resolution for any
non-`.backlogit` workspace (the classifier docstring itself notes `.backlog` is the new-install
default). Every unit below that touches the template carries an explicit `{{BACKLOG_DIRECTORY}}`
preservation check.

### Second finding: the resolved dogfood copy is untested

`tests/test_shipment_reconcile_record_status.py` declares in its module docstring:

> `templates/skills/shipment-reconcile/SKILL.md.tmpl` is a template-only skill with **no installed
> `.github/skills/shipment-reconcile` dogfood mirror**, so this contract is verified against the
> template alone.

That premise is now **false** — `.github/skills/shipment-reconcile/SKILL.md` exists (1082 lines).
The resolved copy therefore has **no contract-test coverage at all**, which is precisely the
condition under which paired-edit drift goes undetected. Closing this is in scope (unit U6).

## Requirements Trace

| Source requirement | Origin | Implementation unit |
|---|---|---|
| Run the classifier as Pre-Mode step 2b; record verdict + qualifying set | Decision item 1 | U1 |
| Evaluate each member against its member class | Decision item 2, D-3 | U1 |
| Membership from classifier set only — never an ID pattern | P-015, criterion 4 | U1 |
| `SAFE_CLOSE` / classifier error ⇒ today's strict scalar semantics | Decision item 3, OQ-4 | U1 |
| Read declared `status` from `queue/` **or** `archive/`; `pre-archived` demoted to a location label | **R-1** | U1 |
| `archived` qualifying feature tolerated **and reported** under its own label | **R-2** | U1 |
| Classifier `reason` recorded **verbatim** | **R-3** | U1 |
| Unrecognised status ⇒ explicit HALT row | **R-5** | U1 |
| step 2b + matrix ship together, atomically | **R-4** | U1 (single unit, by construction) |
| Member-class rules stated **once**; other sites reference it | Decision item 4, criterion 5 | U1 (statement) + U2 (references) |
| Report contract: verdict, qualifying set, per-item class | Decision item 5, criterion 7 | U1 |
| Ship agent pointers reference the member-class contract | Scope section | U3 |
| Regression coverage (a)–(d) | Criterion 8 | U4 |
| Task-class / orphan / record-scope regressions unchanged | Verification plan 3–5 | U5 |
| 159-S shape replay ⇒ `PROCEED`, no deviation | Verification plan 6 | U5 |
| Contract-consistency: rules in exactly one place | Verification plan 7 | U6 |
| Dogfood parity: resolved copy covered by tests | This plan (new finding) | U6 |
| Diagram currency | Verification plan 8 | U7 |
| Authorization disposition recorded | Criterion 9 | **Already done** — decision D-1; no unit |
| `classify_shipment_close_path` logic unchanged | Scope section | **No unit** — see below |

### Explicitly requiring no code change

`src/autoharness/gates/shipment_closure.py` needs **no modification**. The decision artifact hedged
(*"only if the classifier needs a callable surface suitable for the earlier invocation"*).
Verified: it does not. `classify_shipment_close_path(manifest_items, workspace_backlog_dir)` is
already a pure, side-effect-free function returning a frozen `ClosePathDecision` carrying exactly
the three fields Pre-Mode needs — `close_path`, `reason` (for R-3), and `qualifying_feature_ids`
(for the membership set). Invoking it earlier requires nothing new.

**This is a material scope reduction:** the change is confined to skill/agent Markdown plus tests.
No Python source is modified, so no runtime surface changes.

## Implementation Units

Each unit obeys the 2-hour rule (<3 files, <5 functions, <4 test scenarios), width isolation
(single domain), and produces a verifiable atomic milestone.

---

### U1 — Pre-Mode member-class status contract (THE ATOMIC CORE — R-4)

**Domain:** skill documentation (paired).
**Files (2):** `.github/skills/shipment-reconcile/SKILL.md`,
`templates/skills/shipment-reconcile/SKILL.md.tmpl`.
**Posture:** contract-first (write the authoritative statement, then wire the steps to it).

**R-4 NON-NEGOTIABLE:** step 2b (classifier invocation) and the member-class matrix are **one unit**
and MUST NOT be split. Splitting them reproduces rejected Option B in production, with no component
anywhere validating the qualifying feature's status (F9). If this unit is judged oversized during
right-sizing, it is split **only** by extracting documentation/report prose into U2 — never by
separating 2b from the matrix.

**Changes:**

1. **New authoritative block: "Member-class status contract."** The single source of truth. States,
   per member class, which declared statuses are valid, tolerated (with label), and halting:

   | Member class | Valid | Tolerated (labelled, reported) | HALT |
   |---|---|---|---|
   | Shipment record | `active` (via existing record-scope classification) | — | `queued`, legacy `blocked` |
   | Qualifying feature — membership **only** from step 2b's `qualifying_feature_ids`, and **only** under a `CASCADE` verdict | `active`, `done` | `archived` ⇒ label `qualifying-feature-pre-archived-anomaly` (R-2) | `queued`; **any unrecognised value** (R-5) |
   | Task member | `done` (`expected_status`) | truly `archived` ⇒ `pre-archived`; relocated-but-`done` | `queued`, `active`; any unrecognised value (R-5) |
   | Any member under `SAFE_CLOSE`, classifier error, or ambiguity | today's strict scalar semantics, unchanged | | |

2. **New Pre-Mode step 2b.** Run **the machine-checkable P-015 close-path classification described
   in Safe-Close Step 0(c)** over the loaded manifest before the gate decision. **Specify it
   portably, in Step 0(c)'s existing phrasing** — *a
   `classify_shipment_close_path(manifest_items, workspace_backlog_dir)`-shaped function where a
   Python implementation is installed (this repository's lives at
   `src/autoharness/gates/shipment_closure.py`); the equivalent structural check against
   `queue/` + `archive/` otherwise* — and **reference Step 0(c) rather than restating it**. Naming a
   concrete Python symbol as the mechanism would make Pre-Mode unimplementable in workspaces without
   the Python gate, regressing a deliberate portability contract *inside the same file*. (P1-1)

   Record `close_path`, the qualifying-feature set, and a **distinguishing reason string**:
   **verbatim** where the implementation supplies one (R-3), and otherwise an explicitly-authored
   reason naming the precondition that failed. A report with no reason available records the
   explicit label `classifier-reason-unavailable` — **never a blank field** (P1-2). State explicitly
   that this invocation is **advisory for gating only** and that Safe-Close Step 0(c) remains
   **authoritative** for the pre-close snapshot and the two-set gate; a disagreement between the two
   invocations is itself a halt condition.

3. **Amended Pre-Mode step 3 — R-1 is the structural change.** Reorder from *locate-then-classify*
   to **locate → read declared `status` → classify by member class**:
   * Look in `queue/`, then `archive/`. Record **where** the record was found as a *descriptive
     location label*.
   * **Always read the frontmatter `status`**, from whichever directory holds the record. Location
     never short-circuits the status read.
   * `pre-archived` becomes a location label recorded **alongside** the declared status, never
     instead of it.
   * Evaluate the declared status against the member class from the contract block.
   * `missing` (neither directory) is unchanged.

4. **Report contract** (feeds step 7): verdict, verbatim `reason`, qualifying set, and per-item
   `{location label, declared status, member class, classification}`.

**Template hazard:** all new directory references use `{{BACKLOG_DIRECTORY}}` in the `.tmpl` and the
literal `.backlogit` in the resolved copy. Verify by diffing the two files and confirming the delta
is *exclusively* `{{BACKLOG_DIRECTORY}}` substitutions.

**Verified by:** U4 (behavioural), U6 (single-location + parity).

---

### U2 — Remove the intra-skill contradiction (reference, do not restate)

**Domain:** skill documentation (paired). **Files (2):** same pair as U1. **Depends on:** U1.

Update **three** sites to *reference* U1's authoritative block instead of independently restating
status expectations:

1. the **Output classification table** (and add the new
   `qualifying-feature-pre-archived-anomaly` label);
2. the **Cascade Close Sub-Procedure step 3** preamble;
3. **Safe-Close Step 0(b)** — **required, and the finding that makes this unit load-bearing (P1-3).**
   Step 0(b) *already* states the declared-status-over-location rule (*"location alone is never
   sufficient"*) for the pre-close snapshot. If it is left as an independent statement, this fix
   ends with the rule stated in **three** places instead of one — defeating decision item 4, bug
   acceptance criterion 5, and verification-plan item 7, and forcing U6's single-source assertion to
   either fail or be weakened.

**Re-framing R-1 (correction carried from review):** Pre-Mode did not lack the
declared-status-over-location rule for want of anyone stating it. **It failed to apply a rule the
same file already states in Step 0(b).** That is a stronger anti-recurrence argument than "add a
missing rule", and it is the argument the plan should carry.

**Verified by:** U6.

---

### U3 — Ship agent pointers

**Domain:** agent documentation (paired).
**Files (2):** `.github/agents/_ship.agent.md`, `templates/agents/_ship.agent.md.tmpl`.
**Depends on:** U1.

Update the Step 5 closure pointer and the Step 0.5 intake scope note to reference the member-class
contract by name. Ship's existing Step 0.5 / Step 2 task-artifact filters are **unchanged** — they
are cited as precedent, not modified. Preserve template placeholders (`{{STATUS_*}}`,
`{{OP_*_MCP}}`).

---

### U4 — Gate-behaviour regression tests (bug acceptance criterion 8)

**Domain:** tests. **Files (1):** new `tests/test_shipment_reconcile_member_class_contract.py`.
**Depends on:** U1 (authored **before** it — see Dependency Graph). **Posture:** **test-first,
mandatory.** Author, run, and capture the failing output as a recorded deliverable before U1 lands.

Four scenarios, matching the pattern of `tests/test_shipment_reconcile_record_status.py`
(doc-contract assertions over the skill text, bounded by protocol anchors):

* (a) fully-covered root, qualifying feature `active` ⇒ `PROCEED`
* (b) same manifest, feature `queued` ⇒ `HALT`
* (c) partial-feature manifest (`SAFE_CLOSE`) ⇒ strict behaviour unchanged
* (d) classifier error/ambiguity ⇒ strict behaviour, fail-closed

Assert against **both** the resolved skill and the template (parametrised over the pair).

---

### U5 — Non-regression + 159-S replay

**Domain:** tests. **Files (1):** new
`tests/test_shipment_reconcile_member_class_regression.py`. **Depends on:** U1 (authored **before**
it). **Posture:** **test-first, mandatory** — red phase authored, run, and captured before U1.

Three scenarios:

* Task class unchanged: `queued`/`active` task ⇒ HALT; truly-archived ⇒ `pre-archived`;
  relocated-but-`done` ⇒ tolerated.
* **R-1 targeted**: an **archive-resident** record declaring `queued` ⇒ **HALT**. This is the case
  today's location-first logic silently passes, and the single most important assertion in the plan.
* 159-S shape replay: manifest `[151-F, 151.001-T … 151.007-T]`, feature `active` ⇒ `PROCEED` with
  **no** deviation, override, or mutation — i.e. the recorded P-005 deviation would not have been
  necessary under the corrected contract. This is the executable evidence backing decision D-1's
  acceptance basis.

Orphan-scan and record-scope classification are covered by existing tests
(`test_shipment_reconcile_record_status.py`, `test_shipment_reconcile_safe_close.py`); assert they
still pass rather than duplicating them.

---

### U6 — Contract-consistency and dogfood-parity guard

**Domain:** tests. **Files (2):** new `tests/test_shipment_reconcile_contract_single_source.py`;
edit `tests/test_shipment_reconcile_record_status.py` (stale-docstring + parity fix).
**Depends on:** U1; authored **before** U2. **Posture:** **test-first, mandatory** — red phase
against U2's consolidation, captured before U2 lands.

**Declared scope addition (P2-3).** Editing `test_shipment_reconcile_record_status.py` is **outside**
the decision artifact's declared in-scope file list. It is retained deliberately: that file's
docstring asserts there is "no installed `.github/skills/shipment-reconcile` dogfood mirror", which
is **false** — the resolved 1082-line copy exists and is consequently **untested**. That is precisely
the condition that would let this change's own paired-edit drift ship undetected. Recorded here as an
**approved scope addition with rationale**, not absorbed silently.

* Assert the member-class status rules appear in **exactly one** authoritative location, and that
  Pre-Mode and the Cascade Close Sub-Procedure *reference* it.
* Assert `{{BACKLOG_DIRECTORY}}` is preserved in the template and that no literal `.backlogit`
  appears in `SKILL.md.tmpl`.
* **Parity fix:** correct the false "no installed dogfood mirror" docstring in
  `test_shipment_reconcile_record_status.py` and extend its assertions to the resolved
  `.github/skills/shipment-reconcile/SKILL.md`, so the installed copy is no longer untested.

---

### U7 — Diagram currency

**Domain:** docs. **Files (1):** `docs/diagrams/05-shipment-reconcile-cascade-premode.mmd`.
**Depends on:** U1, U2. **Posture:** documentation.

Mark the proposed path as shipped; add the R-1 declared-status-over-location read and the R-2
anomaly label to the diagram; keep it structurally valid (`scripts/check_eraser_diagrams.py` is
present for the eraser set).

**Narrowed per review (P2-4):** decision- and bug-record status bookkeeping is **removed** from this
unit — it is closure-path bookkeeping, not an implementation deliverable, and bundling it violated
width isolation. It moves to the closure checklist (see Runtime Verification and Closure).

---

## Dependency Graph

**Test-first ordering is mandatory (Constitution II, NON-NEGOTIABLE; P-004 red phase).** Doc-contract
tests assert strings the units introduce, so they fail cleanly before the text exists. Each test unit
is therefore authored, run, and **observed failing** *before* its corresponding content unit, and the
captured failure output is a recorded deliverable — not an aspiration (P1-4).

```text
U4 (tests, RED) ─┐
U5 (tests, RED) ─┼─> U1 (atomic core: 2b + matrix) ──> U4/U5 GREEN
                 │        ├─> U3 (ship agent pointers)
                 │        └─> U2 (contradiction removal: Output table,
                 │                 Cascade step 3, AND Safe-Close Step 0(b))
U6 (tests, RED) ─────────────────> U2 ──> U6 GREEN
                                    └─> U7 (diagram currency)
```

No cycles. Execution order: **U4, U5 (red) → U1 (green) → U6 (red) → U2 (green) → U3, U7.**
U3 and U7 are independent leaves. U6's red phase follows U1 because its single-source assertion
targets text U1 introduces and U2 consolidates.

## Decisions and Rationale

| Decision | Rationale |
|---|---|
| No change to `shipment_closure.py` | Verified: `ClosePathDecision` already carries `close_path`, `reason`, `qualifying_feature_ids`. Adding a wrapper would be ceremony, and touching the classifier would put its unchanged-verdict guarantee (verification plan item 1) at risk for zero benefit. |
| U1 is indivisible | R-4. Any split that lands the matrix before the classifier *is* Option B, which the operator rejected as disqualifying. |
| Reorder step 3 rather than patch it | R-1 is not an added condition — today's logic classifies on **location** before reading `status` at all. A patch cannot fix an ordering defect; the read must move ahead of the classification. |
| Restructure to reference, not restate (U2) | The defect's generative cause is two independent restatements of one rule. Fixing only the values would leave the mechanism intact. |
| `archived` gets its own label, not the generic `pre-archived` | R-2. Reusing `pre-archived` would make the anomaly indistinguishable from the benign archived-task case — silent tolerance by another name. |
| Unrecognised status is an explicit HALT row | R-5. Costs nothing today; guarantees a future `parked`/`hold` status (stash `4D3826FE`) surfaces loudly rather than being silently absorbed. |
| Doc-contract tests, not runtime tests | Matches the established pattern for this skill; the artifact under change *is* prose. |
| Fix the parity gap now (U6) | The resolved copy being untested is the exact condition that lets paired-edit drift ship undetected — and this change touches that pair heavily. |

## Risks and Caveats

| Risk | Severity | Mitigation |
|---|---|---|
| Right-sizing splits U1, producing interim Option-B behaviour | **High** | R-4 recorded in the plan, the decision, the bug record and every harvested task. U1 splits only by extracting prose into U2, never 2b from the matrix. |
| Paired edit hardcodes `.backlogit` into the template | **High** | U6 asserts no literal `.backlogit` in the `.tmpl` and that the skill/template delta is exclusively `{{BACKLOG_DIRECTORY}}`. |
| R-1 reorder unintentionally changes task-member behaviour | Medium | U5 pins all three task-class outcomes explicitly. |
| Widening admits a genuinely drifted feature | Medium | Relaxation applies only to the classifier-identified set, only under `CASCADE`, only for `active`/`done`. U4(b) and U5's archive-resident-`queued` case pin the HALTs. |
| Two classifier invocations disagree (TOCTOU) | Medium | Step 0(c) stays authoritative; disagreement is documented as a halt condition. |
| Scope creep into `4D3826FE`, `7F93FA0C`, or OQ-5 | Medium | Explicit non-goals; R-5 is the *only* permitted coupling to `4D3826FE`. |
| Existing test's stale premise masks drift | Medium | Closed by U6. |

## Plan Hardening Signals (REQUIRED)

| Signal | Present | Justification |
|---|---|---|
| Public API, schema, or contract change | **YES** | This changes a protocol contract governing shipment closure: Pre-Mode's per-item classification, the Output classification vocabulary (new label), and the report schema. Consumed by Ship and by operators. |
| Security, auth, permission, or compliance-sensitive behaviour | **YES (governance)** | It modifies a **fail-closed gate**. Widening it incorrectly permits an unauthorized irreversible archival; the authorization ambiguity it resolves already produced one recorded P-005 deviation. |
| Migration, backfill, destructive/irreversible step | **YES (adjacent)** | No migration is performed, but the gate sits directly on the **irreversible** cascade-archival path. A defect here manifests as wrongly-archived backlog state, and there is no `unarchive` operation. |
| External integration / operator checkpoint / external dependency | **YES** | Depends on backlogit's lifecycle semantics (CT-3: autoharness may constrain transitions but never assume one backlogit does not perform), and on the classifier's contract. The gate's HALT *is* an operator checkpoint. |
| High runtime, rollout, or rollback risk | **PARTIAL** | No runtime surface changes (no Python modified). Rollout risk is real via self-hosting: the resolved `.github/skills/` copy and `templates/` source must change together or the manifest/checksum diverges. |

**Requires plan hardening: yes.**

Rationale: four of five signals present, and the plan modifies a fail-closed gate on the pipeline's
least reversible path. P-006 mandates hardening before `plan-review`.

## Runtime Verification and Closure

* **Runtime surface changed:** none. No Python source is modified; `classify_shipment_close_path` is
  invoked, not altered. No CLI, API, or job behaviour changes.
* **Self-hosting surface changed:** yes — the installed `.github/skills/` and `.github/agents/`
  copies alongside their `templates/` sources. These MUST land in one shipment (decision:
  "Self-hosting order") or the manifest checksum diverges.
* **Canonical verification gate:**

  ```text
  PYTHONPATH=src python -m unittest discover -s tests
  ```

  Windows PowerShell equivalent for later execution by Ship:

  ```powershell
  $env:PYTHONPATH = 'src'; python -m unittest discover -s tests
  ```

  *Not executed during planning* — no planning validator requires it.
* **Additional verification:** Markdown/frontmatter validity on every changed doc; diagram
  structural validity (`scripts/check_eraser_diagrams.py` for the eraser set); template-variable
  completeness (no unresolved `{{...}}` in resolved copies, and `{{BACKLOG_DIRECTORY}}` **preserved**
  in templates).
* **Closure artifact:** standard post-merge closure. The closure record MUST state that this
  shipment is the **named remediation** for the `accepted-with-remediation` P-005 deviation recorded
  against `159-S` (decision D-1), so the deviation and its closure share a retrieval key.
* **Rollback trigger:** any cascade-eligible closure that HALTs where the contract says `PROCEED`, or
  — far more serious — any closure that `PROCEED`s where the contract says HALT (notably an
  archive-resident `queued` qualifying feature).
* **Rollback procedure:** revert the shipment's commits. There is no data migration and no state
  change, so revert is complete and sufficient.
* **Validation window:** the next cascade-eligible closure. Until one occurs, U5's 159-S replay is
  the standing evidence.

## Non-Goals

* Fixing `7F93FA0C`, the Engram content-record schema incident, or the `parked`/`hold` lifecycle gap
  (`4D3826FE`) — R-5 is the only permitted interaction with the last of these.
* OQ-5 (lifting the contract into `workflow-policies.md`) — still **undecided**; not planned.
* OQ-6 (a standing plan-review/plan-harden gate-satisfiability check) — out of scope.
* Changing the P-015 default, the two-set gate, snapshot rules, or the CT-1 declared-status rule.
* Any relaxation for task members.
* Changing `mode: post`, `mode: safe-close` steps 1–10, or `mode: detect-mixed-role`.
* Re-opening or re-closing `159-S`; modifying PR #436.

## Plan Hardening

**Hardening required: YES.** Confirmed against the plan's own signal table — four of five signals
present, and the change modifies a **fail-closed gate on the irreversible cascade-archival path**.
P-006 mandates hardening before `plan-review`.

### Learnings and instructions consulted

| Source | What it contributed |
|---|---|
| `docs/compound/097-S-shipment-task-only-safe-close.md` | **Resolved an apparent contradiction** — see H-1. Also supplied the anti-vacuity reasoning reused in H-2. |
| `docs/compound/096-S-template-vs-global-skill-placeholders.md` | Placeholders do **not** resolve in `.github/skills/`. Tightened the U6 parity assertion into a two-sided check (H-3). |
| `docs/compound/097-S-canonical-unittest-gate.md` | Confirms the canonical gate is `unittest`, **not** root `pytest` (root pytest collects vendored `references/` tests and fails). |
| `docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md` | Ordering hazard around safe-close mutation; drove the H-4 lock/ordering invariant. |
| `docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md` | Lesson 8 (self-describing states) — the R-1/R-5 rationale. |
| `.github/instructions/harness-architecture.instructions.md`, `workflows.instructions.md` | Paired-edit maintenance contract for skill/template pairs. |

### H-1 — Apparent contradiction investigated and CLEARED (do not re-litigate)

`097-S`'s Durable Rule states *"`custom_fields.items` contains task IDs only; the covering feature
is derived from task `parent_id` … Do not add it to `custom_fields.items`."* That reads as a direct
contradiction of this plan's premise (and of finding F1, and of Stage's own feature-first shipment
assembly).

**It is not a contradiction.** The same document's "Reconciliation — the FULLY-COVERED ROOT
exception (2026-08-10, PR #325)" section scopes the Durable Rule explicitly to **PARTIAL-feature**
shipments, whose hazard is a covering feature with children *outside* the manifest. The
fully-covered-root case is the reconciled **exception**, where the predicate is quantified over
**every feature member** of `custom_fields.items` and each must satisfy FULL COVERAGE **and** ROOT
PLACEMENT. In that case the feature member is required to be present, and cascade is
structurally safe.

**Verdict: the plan's premise stands, unchanged.** Recorded here so plan-review does not re-open it,
and so a future reader who finds the Durable Rule in isolation does not "correct" this fix back into
a defect. This is itself an instance of the compound learning's lesson: a locally-correct clause read
without its reconciliation produces a wrong conclusion.

### H-2 — Protected invariants (verified against the classifier source, not assumed)

Read from `src/autoharness/gates/shipment_closure.py` at HEAD:

| # | Invariant | Evidence | Consequence for the matrix |
|---|---|---|---|
| I-1 | Under `CASCADE`, **every** feature-typed manifest member is in `qualifying_feature_ids` | Any feature member failing coverage/root placement returns `SAFE_CLOSE` early (lines ~404-430) | A feature-typed member **absent** from the qualifying set under a `CASCADE` verdict is structurally impossible ⇒ if observed it is a contract violation ⇒ **HALT**. Specify explicitly; never fall through to task semantics. |
| I-2 | `CASCADE` with an **empty** `qualifying_feature_ids` is impossible | With no feature members, `accounted_ids` is empty, so `extras` captures every item and returns `SAFE_CLOSE` (lines ~424-432) | If observed, treat as classifier contract violation ⇒ **HALT**, do not treat as "no qualifying features, therefore relax nothing". |
| I-3 | A **task-only** manifest always classifies `SAFE_CLOSE` | Same path as I-2 | Backward compatibility is provable, not merely likely: task-only manifests take today's strict scalar path **byte-for-byte unchanged**. |
| I-4 | `ClosePathDecision` is a frozen dataclass; the classifier is pure and side-effect-free | `@dataclass(frozen=True)`, no writes | Invoking it a second time in Pre-Mode cannot mutate workspace state — R-4's double invocation is safe. Pre-Mode's no-mutation constraint is preserved **by construction**. |

**I-1 and I-2 are new hardening content**: the pre-hardening plan specified the matrix for members
*in* the qualifying set but left the impossible-but-unspecified cases silent. Silence is exactly the
fall-through R-5 forbids. Both are now explicit HALT rows.

### H-3 — Two-sided placeholder parity (tightened)

`096-S` establishes that `{{VARIABLE}}` placeholders are **not** substituted in `.github/skills/`.
Current state verified: the resolved skill contains **0** `{{...}}` placeholders and the template
contains **0** literal `.backlogit` occurrences. U1 heavily edits directory references on both
sides, so U6's guard is tightened to assert **both** directions:

* `templates/skills/shipment-reconcile/SKILL.md.tmpl` ⇒ **0** literal `.backlogit`
* `.github/skills/shipment-reconcile/SKILL.md` ⇒ **0** unresolved `{{...}}`
* the skill/template delta remains **exclusively** `{{BACKLOG_DIRECTORY}}` substitutions

A one-sided check would pass while the pair silently diverged.

### H-4 — Ordering and lock invariants

* Step 2b is inserted **after** manifest load (step 2) and **before** the gate decision. It MUST NOT
  move ahead of step 1 (lock acquisition), so the classifier reads the manifest under the same
  single-writer lock that guards the rest of Pre-Mode.
* Pre-Mode remains **detect-and-report only**. Guaranteed by I-4, not merely asserted.
* Safe-Close Step 0(c) remains **authoritative** for the pre-close snapshot and the two-set gate.
  Step 2b is advisory-for-gating-only. A disagreement between invocations is a **halt** condition.
* Related but out of scope: `2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md` — the
  lifecycle topology gate must run while the shipment is still `active`. This plan does not move any
  mutation and so cannot perturb that ordering; recorded so plan-review can confirm rather than infer.

### Risky actions (ProposedAction / ActionRisk)

The `strict-safety` pack is **not installed** in this workspace, so this vocabulary is applied
voluntarily on blast-radius grounds. **No unit performs a destructive or irreversible action** — this
shipment changes Markdown and tests only. The risk is entirely in **what the changed contract later
authorizes**.

| ProposedAction | ActionRisk | Approval | Expected ActionResult |
|---|---|---|---|
| PA-1: Widen Pre-Mode acceptance for the qualifying-feature class (`active`/`done` pass) | **HIGH** — governs an irreversible archival gate; a defect permits an unauthorized cascade | Already granted: operator decisions D-2/D-3 | Cascade-eligible closures return `PROCEED`; every other class unchanged (U4a, U4c) |
| PA-2: Tolerate a declared-`archived` qualifying feature | **MEDIUM** — anomalous provenance accepted | D-3, conditioned on R-2 reporting | Accepted **and** emitted under `qualifying-feature-pre-archived-anomaly` (U4) |
| PA-3: Reorder step 3 to read declared status before classifying by location | **MEDIUM** — touches the classification path for **all** member classes, not just features | Implicit in R-1 | Task-class outcomes provably unchanged (U5); archive-resident `queued` feature now HALTs where it previously passed silently |
| PA-4: Paired edit across resolved + template copies | **MEDIUM** — divergence breaks manifest checksum / variable resolution | Standard paired-edit contract | Two-sided parity assertions pass (H-3, U6) |
| PA-5: Edit an existing test file's stale docstring and extend its assertions (U6) | **LOW** | — | `test_shipment_reconcile_record_status.py` covers both copies; no assertion weakened |

**PA-3 is the sleeper.** It is the only action whose blast radius exceeds the qualifying-feature
class. U5's task-class assertions are therefore **mandatory, not optional**, and U5 may not be
descoped during right-sizing.

### Deepened verification

**Environment prechecks (before any test run):**

1. `python --version` resolves; repository root is the working directory.
2. Canonical gate — **`unittest`, never root `pytest`** (`097-S-canonical-unittest-gate.md`: root
   pytest collects vendored `references/` tests and fails on unrelated collection):

   ```powershell
   $env:PYTHONPATH = 'src'; python -m unittest discover -s tests
   ```

   POSIX form of record: `PYTHONPATH=src python -m unittest discover -s tests`
3. Baseline the suite **before** U1 so the red phase (P-004) is attributable.

**Target scenarios — the four that must not regress silently:**

| # | Scenario | Expected | Unit |
|---|---|---|---|
| V-1 | Fully-covered root, feature `active`, queue-resident | `PROCEED` | U4a |
| V-2 | Fully-covered root, feature `queued`, **archive-resident** | **HALT** | U5 (the R-1 case; passes silently today) |
| V-3 | Task-only manifest (`SAFE_CLOSE`) | strict scalar semantics, unchanged (I-3) | U4c |
| V-4 | Classifier raises / returns `SAFE_CLOSE` with a read-failure `reason` | strict, fail-closed, **`reason` recorded verbatim** | U4d |

**Blocked-path handling:** if U1's prose cannot express the matrix without ambiguity, HALT and return
to `plan-review` — do **not** ship a partial matrix. A partially-specified matrix is
indistinguishable from Option B for the classes it fails to specify.

### Deepened operational closure

* **Monitoring signal:** every subsequent Pre-Mode report — the added fields (verdict, verbatim
  `reason`, qualifying set, per-item class) *are* the monitoring surface. Their presence is the
  positive signal; their absence indicates the resolved copy did not take effect.
* **Healthy signal:** the next cascade-eligible closure returns `PROCEED` with **no** deviation
  block, no override token, and no pre-close mutation.
* **Failure signals:** (a) `PROCEED` where the contract says HALT — **severity critical**, notably an
  archive-resident `queued` qualifying feature; (b) a `status-mismatch` HALT on a `CASCADE` manifest
  with an `active` feature — the original defect, unfixed; (c) a Pre-Mode report missing the verbatim
  `reason` — R-3 not delivered.
* **Rollback trigger:** any (a)-class observation, immediately.
* **Rollback procedure:** revert the shipment's commits. **Complete and sufficient** — no data
  migration, no state change, no runtime surface touched. Both copies revert together.
* **Owner:** Ship for execution; Stage owns the contract text.
* **Validation window:** the next cascade-eligible closure. Until one occurs, U5's 159-S replay is the
  standing evidence, which is why U5 is mandatory.
* **Closure artifact requirement (carried forward):** the post-merge closure record MUST state that
  this shipment is the **named remediation** for the `accepted-with-remediation` P-005 deviation
  recorded against `159-S` (decision D-1). Omitting it severs the deviation from its closure and
  defeats the entire reason ratification was rejected.

### Review-gate capability risks (carry into plan-review)

* **P-012:** `backlogit` MCP transport was **unavailable** during this planning session
  (`Transport closed`); all backlog operations ran through the declared CLI fallback
  (`DEGRADED_MODE`). Plan-review must re-probe rather than inherit this status.
* Plan-review MUST emit literal `dispatch_mode:` and `decision:` markers.
* If plan-review runs degraded, it must **declare the fallback explicitly** before harvest; a
  degraded review may not be recorded as a clean pass.

### Unresolved operator decisions that still block safe execution

**None block execution of this plan.** D-1/D-2/D-3 are recorded; R-1..R-5 are binding. Carried
forward, explicitly **not** blocking:

* **OQ-5** (lift the member-class contract into `workflow-policies.md` as a P-015 sub-clause) —
  undecided; deliberately unplanned.
* **OQ-6** (standing plan-review/plan-harden gate-satisfiability check) — out of scope.
* **`4D3826FE`** (`parked`/`hold`) — undecided and externally blocked; interacts **only** via R-5.

**Execution-order blocker (not a plan defect):** PR #436 / the `159-S` post-merge closure is still
open. The harvested shipment must remain **queued** and must not be routed to Ship until that prior
release-unit closure completes.

## Plan Review

dispatch_mode: single-agent-declared-degradation
decision: FAIL

**Cycle 1 of max 3.**

### Capability probe (P-012)

| Capability | Status | Note |
|---|---|---|
| reviewer-subagent-dispatch | `TOOL_DEGRADED` | declared fallback: single-agent persona pass. No subagent dispatch surface is available to this session. |
| model-specific-review-routing | `TOOL_UNAVAILABLE` | `.autoharness/config.yaml` declares no `model_routing.anchor_review`. Cross-model personas run same-model under the declared degradation. |
| backlogit MCP | `TOOL_DEGRADED` | `Transport closed`; CLI fallback in use (carried forward from the hardening record). |
| agent-intercom | `INTERCOM_DEGRADED` | no reachable endpoint; broadcasts skipped, operator visibility reduced. |
| agent-engram | `ENGRAM_DEGRADED` | file-based exploration used throughout. |

Every selected persona was covered inline with a separate finding list, so the degraded path is
valid. No persona was skipped.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Constitution Reviewer | inline (declared degradation) | 1 P1, 2 P3 |
| Python Reviewer | inline | 1 P2, 1 P3 |
| Scope Boundary Auditor | inline | 2 P2 |
| Learnings Researcher | inline | 1 P1, 1 P2 |
| Architecture Strategist | inline, same-model (no anchor route) | 2 P1 |
| Agent-Native Parity Reviewer | inline, same-model — **triggered** (skill/agent contract surfaces, agent-facing actions) | 1 P2 |
| Security Lens Reviewer | inline, same-model — **triggered** (plan modifies an authorization gate; hardening table declares the security signal present) | 2 P3 |

### Hardening check

Plan hardening was **required** and **is present and materially complete**: risk triggers,
protected invariants verified against source, `ProposedAction`/`ActionRisk` entries, deepened
verification, rollback, monitoring, owner, and validation window are all recorded. This condition
does **not** contribute to the FAIL.

### Findings

#### P1-1 — The classifier invocation is specified in a form the skill cannot use (Architecture Strategist)

U1 says "Run `classify_shipment_close_path` over the loaded manifest". But Safe-Close Step 0(c)
(`.github/skills/shipment-reconcile/SKILL.md` lines ~408-415) is deliberately written to be
**portable**:

> Workspaces with a Python implementation installed reuse a
> `classify_shipment_close_path(manifest_items, workspace_backlog_dir)`-shaped function (this
> self-hosting repository's own implementation lives at `src/autoharness/gates/shipment_closure.py`);
> **other workspaces implement the equivalent check directly against** `.backlogit/queue/` **+**
> `.backlogit/archive/`.

The skill is a **generated, distributable** artifact. Naming a concrete Python symbol as step 2b's
mechanism would make Pre-Mode unimplementable in every workspace without the Python gate installed —
a regression against an existing, deliberate portability contract, and a contradiction *inside the
same file*, which is the exact defect class this plan exists to eliminate.

**Recommendation.** Specify step 2b using Step 0(c)'s existing portable phrasing: "the
machine-checkable P-015 close-path classification — a `classify_shipment_close_path`-shaped function
where installed, the equivalent structural check otherwise" — and reference Step 0(c) rather than
restating it.

#### P1-2 — R-3 (verbatim `reason`) is undefined for non-Python workspaces (Architecture Strategist)

R-3 requires the report to record the classifier's `reason` **verbatim**. `reason` is a field of the
Python `ClosePathDecision` dataclass. A workspace implementing the equivalent check directly has no
such string. As written, R-3 is either unsatisfiable or silently optional there — and "silently
optional" is precisely the fall-through R-5 forbids.

**Recommendation.** Restate R-3 as a capability-neutral obligation: the report MUST record the
verdict **and a distinguishing reason string**, verbatim where the implementation supplies one, and
otherwise an explicitly-authored reason naming the precondition that failed. Add the
"no reason available" case as an explicit report label, never a blank field.

#### P1-3 — U2's scope omits Step 0(b), creating a *third* restatement (Learnings Researcher / Architecture Strategist)

The declared-status-over-location rule that R-1 introduces to Pre-Mode **already exists** in
Safe-Close Step 0(b), which states the pre-close declared-status snapshot must distinguish truly
archived records and that *"location alone is never sufficient"*.

U2 currently updates only the Output classification table and the Cascade Close Sub-Procedure. Leaving
Step 0(b) as an independent statement means that after this fix the rule is stated in **three**
places (U1's new block, Step 0(b), and the Cascade preamble) instead of one — directly defeating
decision item 4, bug acceptance criterion 5, and verification-plan item 7, which U6 is supposed to
assert. U6 would therefore either fail or be weakened to pass.

**Recommendation.** Extend U2 to bring Step 0(b) under the same authoritative block by reference.
Re-frame R-1 in the plan: Pre-Mode did not *lack* this rule for want of anyone stating it — it failed
to apply a rule the same file already states elsewhere. That framing strengthens the anti-recurrence
argument.

#### P1-4 — The dependency graph mandates a test-last order (Constitution Reviewer)

Constitution principle II (Test-First Development) is **NON-NEGOTIABLE**, and P-004 requires a red
phase. The graph sequences `U1 → U4, U5, U6`, i.e. the contract text lands before any test exists.
U4 hedges with "test-first where practical"; U5 and U6 declare no posture at all.

Doc-contract tests make test-first entirely practical here: the assertions target strings the unit
will introduce, so they fail cleanly beforehand.

**Recommendation.** Invert to author-test-then-text within each pairing, and make the red phase an
explicit, recorded deliverable (test authored, run, observed failing, failure captured) rather than
an aspiration. Add the declared posture to U5 and U6.

#### P2-1 — Two directly on-topic learnings were not consulted (Learnings Researcher)

* `docs/compound/2026-08-01-shipment-record-status-integrity.md` (109-S/105-F) is the **origin** of
  the record-scope classification that U1's matrix restates in its first row, and carries the
  `record-consistent` / `record-*-with-*-work` token vocabulary.
* `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md` documents that shipment
  artifacts accept `queued|blocked|active|shipped|abandoned` while work items accept a **broader**
  set — the precise asymmetry U1's shipment-record row depends on.

Neither appears in the hardening record's consulted table. Not a contradiction (no finding conflicts
with the plan), so P2 rather than P1.

**Recommendation.** Consult both, add them to the table, and confirm the matrix's shipment-record row
uses the established token vocabulary rather than inventing parallel terms.

#### P2-2 — New test files are not constrained to `unittest` (Python Reviewer)

`097-S-canonical-unittest-gate.md` records that root `pytest` collects vendored `references/` tests
and fails on unrelated collection; the canonical gate is `unittest`. The plan cites the gate command
but never constrains U4/U5/U6's **new** files to `unittest.TestCase`. A pytest-style bare-function
test file would pass under a developer's ad hoc `pytest tests/` and be invisible to the canonical
gate.

**Recommendation.** Require `unittest.TestCase` classes, no pytest-only constructs (no bare
`assert`-function tests, no fixtures, no `parametrize`), following the established shape of
`tests/test_shipment_reconcile_record_status.py`.

#### P2-3 — U6's parity fix is undeclared scope expansion (Scope Boundary Auditor)

The decision artifact's "In scope for the eventual implementation" list names the skill, its
template, the Ship agent pair, `shipment_closure.py` (conditionally), and "regression tests per bug
acceptance criterion 8". U6 additionally **edits an existing, otherwise-unrelated test file**
(`test_shipment_reconcile_record_status.py`) to correct a stale docstring and extend coverage to the
resolved copy.

The justification is sound — the untested resolved copy is exactly the condition that lets this
change's paired-edit drift ship undetected. But it is scope the operator has not seen declared.

**Recommendation.** Keep it (removing it would leave the change's own parity unguarded), but record
it explicitly as a declared scope addition with rationale, so it is approved rather than absorbed.

#### P2-4 — U7 mixes an implementation deliverable with artifact bookkeeping (Scope Boundary Auditor)

U7 bundles diagram currency (a real deliverable) with "status updates to the decision and bug
records". The decision artifact's status is already `decided`; flipping the bug record's status on
delivery is closure bookkeeping owned by the closure path, not an implementation unit. This violates
width isolation within the unit.

**Recommendation.** Narrow U7 to diagram currency only. Move bug-record status flipping to the
closure checklist.

#### P2-5 — The resolved-copy edit mechanism is unspecified (Agent-Native Parity Reviewer)

The plan requires the resolved `.github/skills/` copy and the `templates/` source to change together
but never states **how** the resolved copy is produced — hand-edited in parallel, or regenerated via
an install/render step. `096-S` says `.github/skills/` globals are *not* rendered, yet this pair
demonstrably **is** rendered (the template's `{{BACKLOG_DIRECTORY}}` appears as a literal
`.backlogit` in the resolved copy). Ship will otherwise improvise, and a regeneration step would
silently discard a hand-edit.

**Recommendation.** State the mechanism explicitly, and have U6's parity assertion be the arbiter
regardless of which is used.

#### P3-1 — U1 subordinates Single Responsibility to atomicity (Constitution Reviewer)

U1 bundles four concerns (authoritative block, step 2b, step 3 rewrite, report contract) against
principle VI. This is **correct** — R-4 forbids the split, and the alternative reproduces rejected
Option B. Advisory only: the plan should say explicitly that SRP is deliberately subordinated to R-4
so a future reviewer does not "fix" it.

#### P3-2 — Context efficiency (Constitution Reviewer)

The skill is already 1082 lines; U1/U2 add a matrix and a report contract. Principle X favours agent
context efficiency. Mitigated by U2 replacing restatements with references — net growth should be
modest. Advisory: prefer one table over prose restatements.

#### P3-3 — Recorded classifier output is not independently verified (Security Lens Reviewer)

Step 2b records a classifier verdict the agent itself ran; nothing cryptographically binds the
recorded output to an actual invocation. Materially mitigated: Step 0(c) re-runs the classifier
authoritatively and the plan already makes disagreement a halt condition. Advisory only.

#### P3-4 — R-1 broadens the read surface into `archive/` (Security Lens Reviewer)

Reading declared status from archive-resident records enlarges the gate's input surface to
historical artifacts. Risk is low (read-only, and the two-set gate remains authoritative), and the
alternative is the R-1 defect. Advisory.

### Runtime verification and operational closure

**No gaps.** Runtime surface impact is correctly assessed as none (no Python source modified),
self-hosting impact is identified, the canonical gate is named in both POSIX and PowerShell forms,
and rollback/monitoring/owner/validation-window detail is complete. The requirement that the closure
record name this shipment as the P-005 remediation is correctly carried forward.

### Gate decision

**FAIL** — four P1 findings. P1-1 and P1-2 would ship a Pre-Mode step that is unimplementable
outside a Python-equipped workspace; P1-3 would leave the fix creating a third restatement of the
very rule it exists to consolidate, defeating its own acceptance criterion; P1-4 conflicts with a
NON-NEGOTIABLE constitutional principle.

None of the four require re-deliberation or a new operator decision. All are addressable by
amending the plan. Proceed to fix cycle 1; do not harvest.

---

## Review Remediation — Cycle 1

All four P1 findings and all five P2 findings are addressed **in the plan body above**. This section
records the cross-cutting changes and the two newly-consulted learnings.

### P1 remediation (in-body)

| ID | Change | Location |
|---|---|---|
| P1-1 | Step 2b respecified in Step 0(c)'s portable phrasing; references Step 0(c) instead of restating it | U1 step 2 |
| P1-2 | R-3 restated capability-neutrally; explicit `classifier-reason-unavailable` label; blank fields forbidden | U1 step 2 |
| P1-3 | U2 extended to **Safe-Close Step 0(b)**; R-1 re-framed as "failed to apply a rule the file already states" | U2 |
| P1-4 | Dependency graph inverted to test-first; red phase is a recorded deliverable; U5/U6 postures declared | Dependency Graph, U4, U5, U6 |

### P2 remediation (in-body)

| ID | Change | Location |
|---|---|---|
| P2-2 | `unittest.TestCase` constraint (below) | this section |
| P2-3 | U6's parity edit recorded as an **approved scope addition with rationale** | U6 |
| P2-4 | U7 narrowed to diagram currency; record bookkeeping moved to the closure checklist | U7 |
| P2-5 | Resolved-copy edit mechanism stated (below) | this section |

### Cross-cutting test constraint (P2-2)

All new test files under U4, U5, U6 MUST be `unittest.TestCase`-based, following
`tests/test_shipment_reconcile_record_status.py`. **No pytest-only constructs** — no bare
`assert`-function tests, no fixtures, no `parametrize`. Rationale: `097-S-canonical-unittest-gate`
records that root `pytest` collects vendored `references/` tests and fails on unrelated collection;
the canonical gate is `unittest`. A pytest-style file would pass a developer's ad hoc `pytest tests/`
and be **invisible** to the canonical gate.

### Resolved-copy edit mechanism (P2-5)

The pair MUST be **hand-edited in parallel, in the same commit**. The resolved
`.github/skills/shipment-reconcile/SKILL.md` is *not* regenerated as part of this change. Basis:
`096-S` records that `.github/skills/` globals are not rendered at install time; the resolved copy's
literal `.backlogit` is a historical render, not a live binding. U6's parity assertion is the
**arbiter** regardless — if a future regeneration step is introduced, U6 fails loudly rather than
silently discarding a hand-edit.

### Newly consulted learnings (P2-1)

| Learning | Bearing | Verdict |
|---|---|---|
| `2026-08-01-shipment-record-status-integrity.md` (109-S/105-F) | Origin of the record-scope classification U1's matrix restates | **No contradiction.** Adopt its token vocabulary. |
| `2026-05-07-backlogit-shipment-status-constraints.md` (011-S, corrected 2026-08-04) | Shipment status enum and legal transitions | **Contradicts a plan premise — see below.** |

**Adopt the established token vocabulary (no parallel terms).** U1's shipment-record row MUST use
the four existing mutually-exclusive labels rather than inventing new ones:
`record-consistent`, `record-queued-with-active-work`, `record-blocked-with-active-work`,
`record-blocked-with-done-work`. Inventing parallel terms for an already-shipped classification
would reproduce this bug's own defect class at the vocabulary layer.

### Correction to a plan premise (from `2026-05-07`, CORRECTION block of 2026-08-04)

The plan's status survey listed shipment statuses as `queued|blocked|active|shipped|abandoned`,
read from `header-def.yaml`. That is the **declared** enum, not the **enforced** one. Verified
against backlogit source in that learning (`internal/core/shipment.go`, `isValidShipmentTransition`
L336-345, `MoveShipmentStatus` L107-108):

* The **only** legal shipment transitions are `queued -> active`, `active -> shipped`,
  `active -> abandoned`.
* `blocked` is **not a defined `ShipmentStatus` constant**. A shipment written to `blocked` is a
  **dead end that can never legally transition**.
* `backlogit move` **does not validate** — it silently accepts invalid status writes. That is how
  `blocked` shipment records came to exist at all.

**Consequences for this plan.**

1. U1's member-class matrix MUST NOT treat a `blocked` **shipment record** as a reachable-and-
   recoverable state. Where the matrix encounters one it is an **anomaly to report**, in the same
   tolerate-and-report shape as R-2's `archived` qualifying feature — not a state to wait on.
2. Dependency gating is modelled with shipment `blocks` **edges** at `status: queued`, never with a
   `blocked` shipment status. The plan must not recommend otherwise anywhere.
3. **A declared enum is not an enforced enum.** This is the same defect class the bug record
   generalises in the durable principle: the header definition and the binary disagree, and the
   silent-accept write path lets the disagreement persist undetected.

### Bearing on the related-but-distinct `parked`/`hold` record

This correction **resolves the open question** left in
`docs/bugs/2026-09-07-backlog-lifecycle-missing-temporary-out-of-queue-status.md` about whether
`header-def.yaml` is authoritative for transition validation. **It is not.** The Go binary hard-codes
the transition matrix, and `move` does not validate against the schema. Therefore adding
`parked`/`hold` by editing `header-def.yaml` alone would produce exactly the `blocked`-shipment
failure mode: a writable status with **no legal exit**. That record is updated accordingly. This
strengthens — and does not change — its conclusion that an upstream backlogit change is required.

---

## Plan Review — Cycle 2 (re-review after remediation)

dispatch_mode: single-agent-declared-degradation
decision: PASS

**Cycle 2 of max 3.** Capability posture unchanged from cycle 1 (`TOOL_DEGRADED:
reviewer-subagent-dispatch`; `TOOL_UNAVAILABLE: model-specific-review-routing`; backlogit MCP
degraded to CLI; intercom and engram degraded). Re-review scope: the four P1 findings, the five P2
findings, and any regression introduced by the remediation.

### P1 disposition

| ID | Verdict | Basis |
|---|---|---|
| P1-1 | **RESOLVED** | U1 step 2 now uses Step 0(c)'s portable phrasing verbatim and references it rather than restating. Pre-Mode is implementable in a workspace with no Python gate installed. |
| P1-2 | **RESOLVED** | R-3 restated capability-neutrally; a verbatim reason is used where supplied, an authored reason otherwise, and the `classifier-reason-unavailable` label closes the third case. No blank-field fall-through survives — consistent with R-5. |
| P1-3 | **RESOLVED** | U2 now covers Safe-Close Step 0(b), so the rule ends in **one** authoritative location. U6's single-source assertion is satisfiable as written rather than needing to be weakened. The R-1 re-framing is a genuine strengthening. |
| P1-4 | **RESOLVED** | Dependency graph inverted; U4/U5 precede U1 and U6 precedes U2; the red phase is a recorded deliverable, not an aspiration; U5 and U6 now declare postures. Constitution II satisfied. |

### P2 disposition

All five resolved: token vocabulary adopted from `109-S` rather than reinvented (P2-1);
`unittest.TestCase` constraint stated cross-cuttingly with rationale (P2-2); U6's parity edit
recorded as an approved scope addition with rationale rather than absorbed (P2-3); U7 narrowed to
diagram currency with bookkeeping moved to closure (P2-4); the hand-edit-in-parallel mechanism
stated with U6 as arbiter (P2-5).

### New finding introduced by remediation

#### P2-6 — The premise correction is material and must not be lost in decomposition (Learnings Researcher) — **ACCEPTED, MITIGATED IN-PLAN**

Consulting `2026-05-07` surfaced a **contradiction with a plan premise**: shipment `blocked` is
declared in `header-def.yaml` but is not a `ShipmentStatus` constant in the binary and has no legal
outbound transition, and `backlogit move` does not validate. The remediation records this correctly
and derives the right consequences (treat a `blocked` shipment record as a reportable anomaly, never
a waitable state; gate dependencies with `blocks` edges at `queued`).

This is exactly the class of finding that gets lost between a plan and its tasks. **Mitigation
(binding on harvest):** the constraint must appear in the acceptance criteria of the U1 task itself,
not only in this narrative section. Recorded here so the harvest step carries it.

No other regression found. The remediation did not enlarge blast radius, did not touch runtime
surface, and did not weaken any protected invariant (I-1..I-4 re-checked, all intact).

### Cross-check against the binding constraints

| Constraint | Status |
|---|---|
| R-1 declared-status-over-location | Satisfied, and now correctly framed as consolidation of an existing rule |
| R-2 `archived` tolerate-and-report | Satisfied; the `blocked`-shipment anomaly reuses the same shape |
| R-3 reason recorded verbatim | Satisfied and made capability-neutral |
| **R-4 step 2b + matrix atomic in one shipment** | **Satisfied — U1 is indivisible.** Explicitly re-verified: the remediation did not split U1. Any harvest that separates step 2b from the member-class matrix reproduces rejected Option B and is a gate violation. |
| R-5 unrecognised status ⇒ explicit HALT | Satisfied; reinforced by the no-blank-field rule |
| P-005 remediation named in closure record | Carried forward unchanged |
| Dogfood/template parity | Two-sided guard retained in U6 |

### Gate decision

**PASS.** No P1 findings remain. One new P2 (P2-6) is accepted with an in-plan mitigation binding on
harvest. Constitution II is satisfied. The plan is cleared for decomposition.

**Conditions carried into harvest:**

1. **U1 MUST be a single task.** Splitting step 2b from the member-class matrix violates R-4.
2. The `blocked`-shipment-is-a-dead-end constraint MUST appear in U1's task acceptance criteria.
3. Test units MUST be sequenced red-first ahead of their content units.
4. The execution shipment MUST NOT be routed to Ship while PR #436 / 159-S post-merge closure is
   open.
