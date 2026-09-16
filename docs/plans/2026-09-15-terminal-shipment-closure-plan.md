---
title: "Terminal-shipment closure path for fully-archived shipment scope — implementation plan"
description: "Test-first implementation plan for feature 166-F: adds a third machine-checkable shipment-close classification (TERMINAL_CLOSE) to classify_shipment_close_path, a fail-closed terminal-descope protected-set exemption to shipment-reconcile safe-close Steps 2-3, a Terminal-Close Sub-Procedure replacing the refused Step 8 direct transition, the mirrored P-015 policy amendment, and source/template mirror parity plus read-only 173-S/168-S classification dry-runs."
doc_type: plan
source: docs/plans/2026-09-15-terminal-shipment-closure-plan.md
date: 2026-09-15
status: superseded
superseded_by: docs/plans/2026-09-15-flat-manifest-shipment-closure-plan.md
superseded_on: 2026-09-15
revision: 1
revision_note: "Initial plan produced by impl-plan for 166-F, then hardened under P-006 (policy + skill + classifier + template-mirror blast radius) and gated through plan-review cycle 1 (three P1 findings resolved in-cycle: missing red-phase coverage for the policy/skill contract surfaces, an unstated architectural boundary for TERMINAL_CLOSE precondition 4, and an archived_ids post-condition that had to be stated as containment of the manifest closure set rather than an exact match)."
decision_source: docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md
memory_source: docs/memory/2026-09-15-stage-173-s-closure-deadlock-deliberation.md
feature_id: 166-F
shipment_id: 174-S
stash_ids:
  - FBD2F6BE
  - 2B42392E
related_stash_ids:
  - 3CA122AC
---

# Implementation Plan — Terminal-Shipment Closure Path

> ## ⛔ SUPERSEDED — 2026-09-15 — DO NOT EXECUTE
>
> This plan implements **Option E (`TERMINAL_CLOSE` + terminal-descope
> exemption)** of a decision whose **core premise has since been superseded by
> an operator architectural correction**. Its `plan-review` `PASS` verdict
> applied to that superseded premise and **no longer authorizes execution**.
> The document is retained **unmodified below this banner** for traceability.
>
> * **Superseded by plan:** `docs/plans/2026-09-15-flat-manifest-shipment-closure-plan.md`
> * **Superseded by decision:** `docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md`
> * **Superseded decision:** `docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md`
>
> **Why:** a shipment manifest is a **flat manifest of exactly what is
> delivered**; it is not a container over a covering feature and its
> descendants, and carries no implicit hierarchical closure semantics.
> `TERMINAL_CLOSE` is **withdrawn** (its precondition 2 restates hierarchical
> closure; its precondition 3 makes multi-shipment feature delivery
> unreachable), and the terminal-descope exemption is **withdrawn** (it gates
> closure on a disposition note for artifacts that must not gate closure at
> all). No third close verdict is added by the successor plan.
>
> **Still-valid material:** the affected-surface inventory (classifier,
> protected set, Step 8), the template-mirror parity requirements, and the
> read-only `173-S` / `168-S` dry-run discipline are carried forward into the
> successor plan.

## 1. Source Understanding

Implements **Option E** of
`docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md`
(coupled deliberation of stash `FBD2F6BE` + `2B42392E`; related `3CA122AC`),
as harvested into feature `166-F` and carried by planning-handoff shipment
`174-S`.

### Problem frame (technical restatement)

The shipment-closure contract models closure over a **live** backlog. Three
concrete surfaces encode that assumption, and all three fail on a
fully-terminal shipment:

| Surface | File | Failing assumption |
|---|---|---|
| Classifier | `src/autoharness/gates/shipment_closure.py` | `ClosePath` has exactly two members (`SAFE_CLOSE`, `CASCADE`); the fully-covered-root test discounts nothing for terminality, so an out-of-manifest descendant forces `SAFE_CLOSE` regardless of whether it is live or already archived. |
| Protected set | `.github/skills/shipment-reconcile/SKILL.md` Safe-Close Step 2 + Step 3 | Step 2 enumerates every hierarchy-prefix sibling from `queue/` **and** `archive/` into the protected set; the only escape is the sequence-aware exclusion, which demands predecessor provenance `archived_status: shipped\|done`. Step 3 then requires every protected-set member to be live in `queue/`. |
| Record transition | same skill, Safe-Close Step 8 | Mandates `backlogit move <shipment_id> --status shipped`, which backlogit 1.10.1 refuses (exit 9, `ShipShipment` guard). |

**Verified live state** (read-only, this session, `main` @ `358b63b4`):

```text
165-F      queue=False archive=True   status: done            (no archived_status)
165.007-T  queue=False archive=True   status: archived  archived_status: blocked  parent_id: 165-F
165.010-T  queue=False archive=True   status: archived  archived_status: blocked  parent_id: 165-F
173-S      queue=True  archive=False  status: active
160-F + 160.001..018-T, 160.020-T     queue=True   status: queued          (LIVE)
160.019-T  queue=False archive=True   status: archived  archived_status: blocked
168-S      queue=True  status: queued
```

This confirms both shapes the change must discriminate:

* **`173-S` is fully terminal** — every closure-scope artifact is archived and
  terminal, and the only live artifact is the shipment record. → `TERMINAL_CLOSE`.
* **`168-S` is NOT fully terminal** — 19 of 20 manifest members plus the covering
  feature `160-F` are live `queued`; only the out-of-manifest descoped sibling
  `160.019-T` is archived. → must remain `SAFE_CLOSE`, and is unblocked instead by
  the **E2 protected-set exemption**, not by E1.

`165-F` declaring `status: done` (not `archived`) inside `archive/` is the exact
shape the 1029-record archive survey flagged: terminality **must** accept
`done | archived | shipped`, never "declares `status: archived`".

### Scope boundaries carried from the decision

Non-negotiable, operator-stated:

1. Do **not** clear `parent_id` on `165.007-T` / `165.010-T`.
2. Do **not** weaken the live-sibling baseline-integrity gate.
3. Do **not** introduce any feature-ID, shipment-ID, or manifest-shape special case.
4. Terminality accepts `status ∈ {done, archived, shipped}` inside `archive/`.
5. A post-condition deviation **never** triggers an automatic `git restore`;
   it captures evidence → HALTs → emits P-005 → requests explicit operator
   approval → rolls back only after approval (Constitution Principle VII).

**Out of scope**: closing `173-S` or `168-S`; any mutation of `173-S`, `165-F`,
the 11 manifest members, `165.007-T`, `165.010-T`, or the `160-F` family;
upstream backlogit CLI changes (Option C, retained as an optional follow-up).

## 2. Requirements Trace

| # | Requirement (decision artifact) | Implementation unit(s) | Verification |
|---|---|---|---|
| R1 | Third verdict `TERMINAL_CLOSE`, fail-closed, defaulting to `SAFE_CLOSE`, never `CASCADE` | U2 (impl), U1 (red tests) | Fixtures 1, 5 in U1 |
| R2 | Precondition 1 — every manifest member in `archive/` **and** terminal by its own frontmatter `status` | U2 | Fixture 6 terminality matrix |
| R3 | Precondition 2 — full `parent_id` descendant walk of every manifest feature member, all depths, `queue/`+`archive/`, all terminal | U2 | Fixtures 1, 2 |
| R4 | Precondition 3 — shipment record is the only live closure-scope artifact in `queue/` | U2 | Fixture 2, fixture 6 |
| R5 | Precondition 4 — git baseline proves archives pre-exist the run | U5 (skill, **not** the classifier — see D3) | U5 doc-contract test; U6 dry-run |
| R6 | Precondition 5 — torn / missing / malformed / enumeration failure → `SAFE_CLOSE` | U2 | Fixture 5 (four negative cases) |
| R7 | Terminality vocabulary accepts `done \| archived \| shipped` | U2 | Fixture 6 |
| R8 | E2 protected-set terminal-descope exemption with four independent conditions (a)-(d), fail-closed | U4 | U1 doc-contract assertions; U6 168-S dry-run |
| R9 | Step 5 verify-after-each invariant unchanged | U4 (explicit non-goal) | U1 negative doc-contract assertion |
| R10 | Terminal-Close Sub-Procedure replacing Step 8 for `TERMINAL_CLOSE` | U5 | U1 doc-contract assertions |
| R11 | Post-condition gate: `archived_ids ⊆ manifest closure set`, no out-of-set content change vs. baseline | U5 | U1 doc-contract assertions |
| R12 | Deviation-handling sequence (capture → HALT → P-005 → approval → approved rollback); automatic `git restore` PROHIBITED | U3 (policy) + U5 (skill) | U1 doc-contract assertions on both surfaces |
| R13 | Record backlogit 1.10.1 refusals (exit 9) and the residual SAFE_CLOSE-with-live-scope tooling gap | U5 | U1 doc-contract assertion |
| R14 | P-015 amendment mirrored into the policy template | U3 | U6 parity check |
| R15 | Shape-based generality; no ID special case | U1, U2, U3, U4, U5 | U1 asserts no literal feature/shipment ID in fixtures |
| R16 | Source/template mirror parity, harness gates, full suite, read-only 173-S + 168-S dry-runs | U6 | U6 acceptance |

Every requirement maps to at least one unit; every unit traces to at least one
requirement.

## 3. Implementation Units

Granularity constraints applied to every unit: **2-hour rule** (< 3 files,
< 5 functions, < 5 test scenarios per pass), **width isolation** (single domain
per unit), **atomic milestone** (each unit ends at a verifiable state).

### U1 — Red-phase test suite (`166.002-T`)

* **Domain**: tests only. **Posture**: test-first (RED before any U2–U5 edit).
* **Files**: `tests/test_shipment_closure_classification.py` (extend),
  `tests/test_terminal_close_contract.py` (new doc-contract module).
* **Change**:
  * **Classifier characterization** (extends the existing
    `_write_artifact(...)` fixture helper and `unittest` + `tempfile` pattern
    already established in `ShipmentClosureClassificationTests`):
    1. **173-S shape** → `TERMINAL_CLOSE`: manifest members in `archive/`
       declaring `status: done` with no `archived_status`; two out-of-manifest
       descendants (`parent_id` → covering feature) in `archive/` declaring
       `status: archived` + `archived_status: blocked`; shipment record live in
       `queue/`.
    2. **168-S shape** → `SAFE_CLOSE`: covering feature and remaining scope LIVE
       in `queue/`, one archived descoped out-of-manifest sibling.
    3. **Fully-covered root, all live** → `CASCADE` (unchanged).
    4. **Partial-feature with live unshipped siblings** → `SAFE_CLOSE` (unchanged).
    5. **Fail-closed matrix** → `SAFE_CLOSE` in every case, never
       `TERMINAL_CLOSE`, never `CASCADE`: record present in **both** `queue/` and
       `archive/` (torn); record missing; malformed frontmatter; enumeration
       failure (unreadable/absent backlog subdirectory).
    6. **Terminality vocabulary matrix**: `done`, `archived`, `shipped` inside
       `archive/` each count as terminal; a member still live in `queue/`
       disqualifies `TERMINAL_CLOSE`.
  * **Doc-contract tests** (new module, mirroring the established
    `tests/test_shipment_reconcile_safe_close.py` template-assertion pattern and
    `tests/test_scope_containment_policy_contract.py`): assert on **both** the
    installed artifact and its template mirror that the P-015 amendment, the
    Step 2/3 terminal-descope exemption, the Terminal-Close Sub-Procedure, the
    two-part post-condition gate, the ordered five-step deviation sequence, the
    literal prohibition of automatic `git restore`, the Constitution Principle
    VII citation, the backlogit 1.10.1 exit-9 record, and the unchanged Step 5
    invariant are all present.
* **Acceptance**: fixtures are declarative and shape-derived; **no test asserts
  on a literal feature or shipment ID**; the new classifier cases and every
  doc-contract assertion fail RED against current `main`; all 9 existing
  pre-archived regression tests and the rest of
  `ShipmentClosureClassificationTests` continue to pass.
* **Size** `M` · **Complexity** `medium`.

### U2 — `TERMINAL_CLOSE` branch in the classifier (`166.001-T`)

* **Domain**: Python only. **Posture**: implement-to-green after U1.
* **Files**: `src/autoharness/gates/shipment_closure.py`.
* **Change**:
  * Add `TERMINAL_CLOSE = "terminal_close"` to `ClosePath`.
  * Extend `_ArtifactRecord` with `status: str` and `location: str`
    (`"queue"` | `"archive"`), both populated in `_read_artifact_record` from the
    record's own frontmatter `status` field and the resolved folder respectively.
    Location is recorded **only** to answer "is it still live in `queue/`?";
    terminality itself is read from frontmatter and never inferred from location.
  * Evaluate `TERMINAL_CLOSE` **after** the existing `CASCADE` qualification path
    fails, so every current `CASCADE` verdict is bit-for-bit unchanged, then
    require all three preconditions:
    1. every manifest member resolves in `archive/` **and** declares
       `status ∈ {done, archived, shipped}`;
    2. reusing `_build_children_index` + `_enumerate_descendants` (already
       whole-backlog, all-depth, cycle-guarded), every descendant of every
       manifest **feature** member is likewise in `archive/` and terminal,
       manifest member or not;
    3. the shipment record is the only closure-scope artifact still in `queue/`.
  * Reuse the existing fail-closed surfaces verbatim: `BacklogUnavailableError`
    from `_read_artifact_record` (torn / malformed / unsafe-id) and
    `_build_children_index() is None` (failed enumeration) both already return
    `SAFE_CLOSE` with a reason string — `TERMINAL_CLOSE` inherits them by
    construction rather than adding a parallel error path.
  * Extend `ClosePathDecision` with `terminal_evidence: tuple[str, ...]`
    (default empty) naming the artifacts that justified the verdict, for the
    reconcile report.
* **Explicit non-goal**: do **not** relax the `CASCADE` coverage check to ignore
  terminal descendants. Discounting archived descendants to make a covering
  feature "fully covered" would widen the destructive cascade's reachable scope
  and is rejected by the decision artifact.
* **Acceptance**: U1's classifier cases go green; every pre-existing classifier
  test still passes; the module remains pure and read-only (no `git`, no
  `subprocess`, no `backlogit` call).
* **Size** `M` · **Complexity** `high`.

### U3 — P-015 policy amendment (`166.003-T`)

* **Domain**: policy docs only. **Posture**: doc-contract-test-first (U1).
* **Files**: `.github/policies/workflow-policies.md`,
  `templates/policies/workflow-policies.md.tmpl`.
* **Change**: add a **VERIFIED FULLY-TERMINAL CLOSURE EXCEPTION** subsection
  immediately after the existing **VERIFIED FULLY-COVERED-ROOT EXCEPTION**,
  stating: single-artifact safe-close remains the DEFAULT and this is a *second*
  narrow machine-checkable exception; the preconditions exactly as adopted
  (universal terminality of manifest members **and** of every descendant at every
  depth; the shipment record as the only live closure-scope artifact; git-proven
  pre-existence of the archives relative to this run; fail-closed fallback to
  `SAFE_CLOSE`, never `CASCADE`); the permitted close action (the backlogit
  shipment-ship engine op used **solely** to transition the shipment record,
  justified as the only mechanism producing `archived_status: shipped`); the
  post-condition gate; and the **ordered five-step deviation sequence** with the
  explicit prohibition of automatic or immediate `git restore` (or any other
  destructive revert/delete/overwrite), citing Constitution Principle VII
  (Destructive Command Approval, NON-NEGOTIABLE) and stating the agent NEVER
  silently auto-restores. Carry forward P-015's existing generality prohibition.
  Record the rationale (P-015 protects **live** artifacts; with no live artifact
  in scope the feared cascade failure mode is unreachable) citing the spike
  evidence. Add one version-history row in the existing Amendment Log format.
* **Template-variable parity note**: the P-015 region uses
  `{{BACKLOG_DIRECTORY}}`, `{{OP_SHIP_SHIPMENT_MCP}}`, `{{STATUS_DONE}}`,
  `{{DATE}}`. New text in the `.tmpl` MUST use those variables wherever the
  installed copy names a concrete path/op/status, so the two stay textually
  equivalent modulo substitution.
* **Explicit non-goal**: no existing P-015 clause is deleted, reworded to weaken
  it, or narrowed.
* **Acceptance**: both copies textually equivalent modulo template variables; the
  deviation text contains no automatic/unapproved destructive command; U1's
  policy doc-contract assertions go green.
* **Size** `S` · **Complexity** `high`.

### U4 — Steps 2–3 terminal-descope protected-set exemption (`166.004-T`)

* **Domain**: skill docs only. **Posture**: doc-contract-test-first (U1).
* **Files**: `.github/skills/shipment-reconcile/SKILL.md`,
  `templates/skills/shipment-reconcile/SKILL.md.tmpl`.
* **Change**:
  * **Step 2** — add a **Terminal-descope exclusion** bullet as a sibling of the
    existing *Sequence-aware exclusion*. Exclude an unshipped sibling from the
    protected set **only** when ALL of:
    (a) it currently resides in `{{BACKLOG_DIRECTORY}}/archive/`;
    (b) it declares `status ∈ {done, archived, shipped}` read from its own
    frontmatter, never inferred from location;
    (c) it carries a verified **P-021 C1 descope/merge disposition** — an
    explicit `custom_fields.blocked_reason` or a body marker recording the
    descope/merge decision;
    (d) git evidence proves the archived record **pre-exists this closure run**
    (present in `HEAD`, not produced by the working tree since claim).
  * State the fail-closed rule explicitly: a sibling missing **any** of (a)–(d),
    or whose disposition cannot be verified, **REMAINS PROTECTED**. Ambiguity
    never grants the exemption.
  * **Step 3** — state that the exemption applies when **computing** the protected
    set and that the gate itself is otherwise **UNCHANGED**: every member of the
    resulting protected set must still be present in `{{BACKLOG_DIRECTORY}}/queue/`,
    and the manifest-items-only `pre-archived` exemption still does **NOT** extend
    to the protected set.
  * Add a not-a-weakening note: the protection that detects **this run's** cascade
    is the Step 5 verify-after-each invariant measured against the Step 3 baseline,
    and an artifact already archived at baseline can carry no signal about this run.
* **Explicit non-goals**: do **not** modify Step 5; do **not** introduce clearing
  `parent_id` as an alternative or migration step (rejected by the decision).
* **Acceptance**: installed and template copies textually equivalent modulo
  variables; the `168-S`/`160-F`/`160.019-T` shape is covered by (a)–(d); a live
  sibling is still protected; U1's Step 2/3 doc-contract assertions go green.
* **Size** `S` · **Complexity** `medium`.

### U5 — Terminal-Close Sub-Procedure (`166.005-T`)

* **Domain**: skill docs only. **Posture**: doc-contract-test-first (U1).
* **Files**: `.github/skills/shipment-reconcile/SKILL.md`,
  `templates/skills/shipment-reconcile/SKILL.md.tmpl`.
* **Change**:
  * Extend **Safe-Close Step 0(c)** so the classification selects among **three**
    paths: `CASCADE` (existing fully-covered-root exception), `TERMINAL_CLOSE`
    (new), `SAFE_CLOSE` (default/fallback). Preserve verbatim the rule that any
    classifier error or ambiguity falls back to `SAFE_CLOSE` and never to
    `CASCADE`, and the no-substitution rule (once a verdict is selected,
    substituting another path is a **P-005 process deviation** — the exact
    failure recorded in
    `docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md`).
  * Add the **Terminal-Close Sub-Procedure**, running in place of safe-close steps
    1–10 when `TERMINAL_CLOSE` is selected:
    1. reuse the Step 0 manifest and pre-close snapshot (never reload);
    2. capture the git baseline for `{{BACKLOG_DIRECTORY}}/`;
    3. **re-verify the `TERMINAL_CLOSE` preconditions live, immediately before
       mutating**, including precondition 4 (git-proven pre-existence), and fall
       back to `SAFE_CLOSE` on any drift;
    4. invoke `{{OP_SHIP_SHIPMENT_MCP}}` **solely** to transition the shipment
       record;
    5. enforce the post-condition gate — `archived_ids` contains nothing outside
       the manifest closure set, **and** a git comparison against the step-2
       baseline shows no content change to any artifact outside that set;
    6. verify the shipment record now reports `status: archived` with
       `archived_status: shipped`, accepting legacy `done` only where it
       pre-existed as correct terminal provenance;
    7. on **ANY** deviation, execute the deviation-handling sequence below.
  * **Deviation-handling sequence** (fail-closed; Constitution Principle VII,
    NON-NEGOTIABLE) — the skill MUST specify this order and MUST NOT instruct any
    automatic or immediate restore:
    (a) **CAPTURE EVIDENCE** — record observed `archived_ids`, the git diff vs.
    the baseline, and every affected artifact ID into the closure report, leaving
    the deviating working-tree state in place as evidence;
    (b) **HALT** immediately — no further mutation, do not continue the
    sub-procedure;
    (c) **EMIT a P-005 violation event** naming the affected IDs and the deviation;
    (d) **REQUEST EXPLICIT OPERATOR APPROVAL**, presenting the captured evidence
    and the proposed repository-approved rollback action;
    (e) **PERFORM THE REPOSITORY-APPROVED ROLLBACK ONLY AFTER APPROVAL**.
    State explicitly that an automatic or immediate `git restore` — or any other
    destructive revert, delete, or overwrite — is **PROHIBITED**, and that the
    agent NEVER silently auto-restores.
  * **Step 8 tooling record**: document that a direct
    `backlogit move <shipment_id> --status shipped` is REFUSED by backlogit 1.10.1
    with exit 9 ("shipment must be shipped via ShipShipment"); that
    `backlogit update --status shipped` is refused identically; and that archiving
    an active shipment stamps `archived_status: active` and therefore fails the
    provenance gate (`RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE`). Document that
    for a `SAFE_CLOSE`-classified shipment **with live scope** this remains an
    **UNRESOLVED upstream tooling gap requiring operator escalation** —
    `TERMINAL_CLOSE` does **NOT** apply to it.
  * Update the **Output** recommendation vocabulary and the **Deterministic
    Safe-Close Scenario Matrix** to include the `TERMINAL_CLOSE` path, plus the
    negative scenarios enumerated in §6.
* **Acceptance**: installed and template copies textually equivalent modulo
  variables; the sub-procedure contains no automatic/unapproved destructive
  command; U1's sub-procedure doc-contract assertions go green.
* **Size** `M` · **Complexity** `high`.

### U6 — Mirror parity, harness validation, read-only dry-runs (`166.006-T`)

* **Domain**: validation/integration. **Posture**: verification-only.
* **Change**:
  * Verify source-vs-mirror parity for every file this feature touches:
    `.github/policies/workflow-policies.md` ↔
    `templates/policies/workflow-policies.md.tmpl`, and
    `.github/skills/shipment-reconcile/SKILL.md` ↔
    `templates/skills/shipment-reconcile/SKILL.md.tmpl`. Parity edits MUST land in
    the **same commit** as the source edits they mirror (atomicity lesson recorded
    on `165.010-T`).
  * Run the four harness quality gates: YAML frontmatter validity; Markdown
    structure; no unresolved `{{...}}` variables in installed output;
    cross-reference integrity for every file referenced by the amended skill and
    policy.
  * Run the full test suite (`python -m unittest discover -s tests`, the canonical
    CI invocation) and confirm the new characterization and doc-contract tests
    pass with no shipment-closure regression.
  * **Read-only dry-run** of the classifier against the LIVE `173-S` manifest:
    confirm `TERMINAL_CLOSE` with a `terminal_evidence` payload naming
    `165.007-T` and `165.010-T` as already-terminal out-of-manifest descendants.
    **Do NOT close `173-S`.**
  * **Read-only dry-run** against the LIVE `168-S` manifest: record the verdict
    (expected `SAFE_CLOSE`, unblocked by U4's exemption, not by U2) for the
    `3CA122AC` follow-up.
* **Acceptance**: parity clean, four gates green, full suite green, both dry-run
  verdicts recorded in the task's completion notes for Ship's later closure run.
* **Size** `S` · **Complexity** `low`.

## 4. Dependency Graph

```text
U1 (166.002-T, tests)  ──┬──> U2 (166.001-T, classifier) ──┐
                         ├──> U3 (166.003-T, policy)     ──┼──> U5 (166.005-T, sub-procedure) ──┐
                         └──> U4 (166.004-T, Steps 2-3)  ──────────────────────────────────────┼──> U6 (166.006-T)
                                                                                                │
                                                        U2 ─────────────────────────────────────┘
```

Declared task-level edges (acyclic):

| Task | `dependencies` | Rationale |
|---|---|---|
| `166.002-T` | — | Red phase; the entry point for the whole feature. |
| `166.001-T` | `166.002-T` | Constitution Principle II / P-004: red before implementation. |
| `166.003-T` | `166.002-T` | Policy doc-contract assertions must be red first. |
| `166.004-T` | `166.002-T` | Step 2/3 doc-contract assertions must be red first. |
| `166.005-T` | `166.003-T`, `166.001-T` | Sub-procedure text cites the amended P-015 wording and the classifier's third verdict. |
| `166.006-T` | `166.004-T`, `166.005-T` | Integration/validation runs last. |

No cycles. `166.005-T` and `166.006-T` reach `166.002-T` transitively, so every
implementation unit is behind the red phase.

**Shipment-level sequencing: DAG root declared by operator authorization
(2026-09-15 post-review amendment).** `174-S` now carries `labels: [dag-root]`
on explicit operator authorization, deriving `predecessor_source:
declared_root`. It still carries **no** `dependencies` and **no** bootstrap
grant, and this plan adds neither. The shipment is no longer *unsequenced*, but
it is still **not claimable**: operator P-001 authority for the overlap with the
still-active `173-S` remains outstanding and claim-blocking.

## 5. Decisions and Rationale

**D1 — `TERMINAL_CLOSE` is a third verdict, not a relaxation of `CASCADE`.**
Making `165-F` "fully covered" by discounting its archived descendants would
change the *cascade's* reachable scope, which is the destructive path. A separate
verdict with its own strictly-additive preconditions leaves `CASCADE` bit-for-bit
unchanged, which U1 fixture 3 pins.

**D2 — Terminality is read from frontmatter, never inferred from location.**
`165-F` sits in `archive/` declaring `status: done`; 366 of 1029 archived records
share that shape. A location-derived test would be both too permissive (a record
relocated to `archive/` while still `active`) and — under the stricter
"declares `status: archived`" phrasing — too restrictive to ever fire on `173-S`.
Hence the accepted vocabulary `{done, archived, shipped}`.

**D3 — Precondition 4 (git-proven pre-existence) lives in the SKILL, not the
classifier.** `shipment_closure.py` is documented and tested as a *pure,
read-only* classification that "never mutates the backlog and never calls out to
`backlogit` itself". Introducing `git`/`subprocess` into it would break that
contract, make the function environment-dependent, and make its unit fixtures
require a git repository. The classifier therefore evaluates preconditions 1–3
(pure filesystem+frontmatter facts) and the Terminal-Close Sub-Procedure
evaluates precondition 4 immediately before mutating (step 3), where the git
baseline already exists for the post-condition comparison anyway. This is the
same split the existing design already uses: the classifier selects the path, the
skill owns the git baseline and the post-condition gate.

**D4 — E1 and E2 are separate mechanisms with separate beneficiaries.**
`173-S` needs E1 (its whole scope is terminal). `168-S` needs E2 (its scope is
live; only the descoped sibling is archived). Verified live state proves these
are different shapes, so neither mechanism is a special case of the other and
neither alone closes the class.

**D5 — The engine op is permitted only because precondition 3 bounds its blast
radius.** The spike proved `shipment ship` is the only 1.10.1 mechanism yielding
`archived_status: shipped`, and proved it inert against already-archived
artifacts. Precondition 3 reduces its reachable live scope to the shipment record
alone, and the post-condition gate is the live proof, not the prose.

**D6 — Deviation handling is fail-closed with no auto-restore.** The existing
safe-close Step 6 authorizes an immediate `git restore`. That is **not**
inherited by the Terminal-Close Sub-Procedure: Constitution Principle VII
(NON-NEGOTIABLE) requires operator approval before any destructive command
"regardless of permissive agent modes". The five-step sequence is stated
identically in both the policy (U3) and the skill (U5) so the two cannot drift.

**D7 — Doc-contract tests are the red phase for the doc surfaces.** U3/U4/U5
change *contract text*, which is this repository's product. The repo already
encodes such contracts as executable assertions
(`test_shipment_reconcile_safe_close.py`, `test_scope_containment_policy_contract.py`,
`test_cascade_close_archived_ids_postcondition.py`). Without them the policy and
skill amendments would land with no red phase and no regression protection,
violating Constitution Principle II.

**D8 — High-complexity tasks are de-risked, not split further.** `166.001-T`,
`166.003-T`, `166.005-T` carry `complexity: high`. The two-axis gate requires
high-complexity work to be de-risked *or* split. De-risking has been performed
and is on record: the coupled deliberation, the isolated `%TEMP%` spike (engine
behaviour + blast-radius measurement), the 1029-record archive survey, this plan,
its P-006 hardening, and the plan-review gate. Each remains within the 2-hour
volume bound (`S`/`M`), so further splitting would fragment single coherent
contract edits without reducing risk.

## 6. Risks and Caveats

| # | Risk | Mitigation |
|---|---|---|
| RK1 | `TERMINAL_CLOSE` misfires on a shipment with live scope | Preconditions 1–3 quantify terminality over the full descendant walk; default is `SAFE_CLOSE`, never `CASCADE`; U1 fixture 2 (168-S shape) pins the negative. |
| RK2 | Engine archives something unexpected | Post-condition gate (`archived_ids` ⊆ closure set + git content comparison); on deviation → capture / HALT / P-005 / approval / approved rollback only. |
| RK3 | Precondition written so strictly it never fires | Terminality accepts `done\|archived\|shipped`, validated against the 1029-record survey and against `165-F`'s live `status: done`; U6's 173-S dry-run is the empirical proof. |
| RK4 | E2 exemption becomes a general gate bypass | Four independent conditions, all required, fail-closed on any missing element; Step 5 invariant untouched; U1 asserts a live sibling stays protected. |
| RK5 | Change is special-cased to 173-S | Both mechanisms are defined purely by shape; U1 forbids literal IDs in fixtures; U6 requires the 168-S dry-run to also be recorded. |
| RK6 | Installed/template mirrors drift | U6 parity check plus U1 doc-contract assertions run against **both** copies; parity edits land in the same commit. |
| RK7 | Classifier change silently alters an existing `CASCADE` verdict | `TERMINAL_CLOSE` is evaluated only after `CASCADE` qualification fails; U1 fixture 3 and the 9 existing pre-archived regression tests pin current behaviour. |
| RK8 | Ship resumes `173-S` closure mid-procedure after this ships | The decision artifact requires a **full re-run of `shipment-reconcile` safe-close from Step 0/1**, never a resume at Step 8; restated in U5's Step 0(c) text. |

### Negative scenarios to add to the Scenario Matrix (U5)

* **Negative — live descendant**: any closure-scope descendant still in `queue/`
  → `SAFE_CLOSE`, never `TERMINAL_CLOSE`.
* **Negative — torn record**: a closure-scope record in both `queue/` and
  `archive/` → `SAFE_CLOSE`.
* **Negative — non-terminal archived member**: a member in `archive/` declaring a
  non-terminal `status` → `SAFE_CLOSE`.
* **Negative — baseline drift**: precondition 4 re-verification fails at step 3
  (an archive produced by the working tree since claim) → `SAFE_CLOSE`, no
  mutation.
* **Negative — post-condition deviation**: `archived_ids` contains an
  out-of-closure-set ID, or a git content change appears outside the set →
  capture evidence, HALT, P-005, operator approval, approved rollback only.
* **Negative — unverifiable descope disposition (E2)**: an archived sibling with
  no `blocked_reason` and no body marker → stays protected.
* **Negative — working-tree archive (E2)**: an archived sibling not present in
  `HEAD` → stays protected.

## 7. Plan Hardening Signals (REQUIRED)

| Signal | Present | Justification |
|---|---|---|
| Public API, schema, or contract change | **YES** | `ClosePath` is a public enum consumed by the `shipment-reconcile` skill; P-015 is a binding workflow policy; the skill is the executable closure contract. Three coupled contract surfaces plus two template mirrors. |
| Security / auth / permission / compliance-sensitive behavior | **NO** | No auth, secrets, credentials, network, or external trust boundary. Workspace-local filesystem and backlog records only. |
| Migration, backfill, destructive data/config action, or irreversible step | **YES** | The permitted close action invokes backlogit's **cascade** `ShipShipment` engine op, which archives records. Archival of the wrong artifact is a destructive, corrupting action on the backlog. |
| External integration, operator checkpoint, or external dependency | **YES** | Hard dependency on backlogit 1.10.1 engine behaviour (a separate Go project, not self-owned) whose refusal semantics (exit 9) and cascade blast radius were established empirically, not contractually. The deviation path mandates an explicit operator checkpoint. |
| High runtime, rollout, or rollback risk | **YES** | The gate this change touches is the last guard against corrupting the backlog during closure. A too-permissive `TERMINAL_CLOSE` authorizes a destructive engine op; a too-permissive E2 exemption blinds the protected-set gate. Rollback of a wrongly-archived backlog is itself a destructive git operation requiring operator approval. |

**Requires plan hardening: yes**

## 8. Runtime Verification and Closure

| Unit | Runtime surface changed? | Runtime verification | Operational closure artifact |
|---|---|---|---|
| U1 | No (tests) | Tests fail RED against `main`, then green | Red/green evidence in the task completion note |
| U2 | **Yes** — `autoharness.gates.shipment_closure` is consumed by the closure decision path | Full classifier suite green; read-only dry-run against LIVE `173-S` and `168-S` manifests (U6) | `terminal_evidence` payload recorded in the reconcile report |
| U3 | **Yes** — binding policy text that Ship executes | Doc-contract assertions green on installed + template copies | P-015 Amendment Log row |
| U4 | **Yes** — protected-set computation Ship executes | Doc-contract assertions green; 168-S shape covered; live sibling still protected | Step 2/3 text + not-a-weakening note |
| U5 | **Yes** — the close procedure Ship executes | Doc-contract assertions green; scenario matrix covers the TERMINAL_CLOSE path and all §6 negatives | Terminal-Close Sub-Procedure + deviation sequence |
| U6 | No new surface (validation) | Four harness gates + full suite + both read-only dry-runs | Dry-run verdicts recorded for Ship's later `173-S` closure run |

**Monitoring signal for the first real use**: the `173-S` closure run is the
first production exercise of the new path. Its reconcile report MUST record the
selected verdict, the `terminal_evidence` payload, the observed `archived_ids`,
and the post-condition git comparison result — that report is the validation
window artifact.

**Rollback trigger**: any post-condition deviation during that run, or any
protected-set member found archived during a subsequent `168-S` safe-close.

**Rollback procedure**: capture evidence → HALT → P-005 → explicit operator
approval → repository-approved rollback. Never an automatic `git restore`.

**Owner**: Ship, under an operator-granted P-001 authorization for the `173-S`
sequencing overlap (not granted by this plan).

## Plan Hardening

**Hardening required: YES.** Confirmed from §7 — four of five signals present
(contract change, destructive action, external dependency + operator checkpoint,
high rollout/rollback risk). Blast radius spans policy `P-015` + skill
`shipment-reconcile` + classifier `shipment_closure.py` + two template mirrors.

### Risk triggers and protected invariants

**Triggers**: (T1) a new verdict authorizes a *destructive* engine op;
(T2) an exemption is added to a fail-closed safety gate; (T3) the authorizing
evidence is empirical (a spike against a third-party Go engine), not contractual;
(T4) the change is made in prose contracts that two agents execute by reading.

**Invariants that MUST survive this change** (each mapped to the negative test
that pins it):

| # | Invariant | Pinned by |
|---|---|---|
| I1 | A **live** artifact anywhere in the closure scope forbids `TERMINAL_CLOSE` | U1 fixture 2, fixture 6 |
| I2 | Every current `CASCADE` verdict is bit-for-bit unchanged | U1 fixture 3 + 9 existing pre-archived regression tests |
| I3 | Ambiguity always resolves to `SAFE_CLOSE`, never `CASCADE`, never `TERMINAL_CLOSE` | U1 fixture 5 (4 cases) |
| I4 | Step 5 verify-after-each invariant is textually unchanged | U1 negative doc-contract assertion (byte-compare the Step 5 block) |
| I5 | A live sibling, or an archived sibling without a verified disposition, stays protected | U1 E2 negative assertions |
| I6 | `parent_id` is never cleared on any artifact | U1 asserts the skill text contains the explicit non-goal; U6 git diff shows no `165.007-T`/`165.010-T` change |
| I7 | No automatic `git restore` anywhere in the new path | U1 asserts the literal prohibition + Principle VII citation on all four files |
| I8 | No literal feature/shipment ID gates any behaviour | U1 fixture-ID audit assertion |

### Learnings and instructions consulted

* `docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md` —
  a close-path verdict is **final once selected**; substituting another path is a
  P-005 deviation, "regardless of how defensible the judgment feels in the
  moment". → U5 must restate the no-substitution rule for the *three*-way
  selection, not just the two-way one. **Carried into U5's Step 0(c) change.**
* `docs/compound/2026-09-03-copilot-review-surfaces-latent-parent-id-closure-blocker.md` —
  the durable rule: *grep for every other consumer of the same field before
  accepting a complete-sounding explanation*. → applied below (Phase-2 consumer
  sweep). Also the source of the `3CA122AC` / `168-S` class.
* `docs/compound/2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md`
  and the 155-S correction embedded in the 2026-08-18 learning — a truly
  `status: archived` item has **no transition to report** and is **correctly
  absent** from `archived_ids`. → **critical for U5's post-condition**: the gate
  must be `archived_ids ⊆ closure set` (a containment/allow-list check), **never**
  a full-set echo or exact-match of the manifest, because on the 173-S shape
  almost every member is already archived and will be legitimately absent.
* `docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md` —
  `move --status done` relocates to `archive/` while still declaring
  `status: done`. → reinforces D2's `{done, archived, shipped}` vocabulary and
  explains why `165-F` looks the way it does.
* `.github/instructions/constitution.instructions.md` — Principle II (test-first,
  NON-NEGOTIABLE), Principle VII (destructive command approval, NON-NEGOTIABLE),
  Principle VIII (explicit safety modes), Quality Gates 1–4.
* `.github/policies/workflow-policies.md` — P-002, P-004, P-005, P-006, P-015,
  P-021.

### Consumer sweep (applying the 2026-09-03 durable rule)

Every reader of the fields this change newly interprets was enumerated before
the plan was accepted:

| Field newly read | Other consumers found | Consequence |
|---|---|---|
| frontmatter `status` of an archived record | safe-close Step 0(b) snapshot; Cascade Sub-Procedure step 3 two-set gate; mixed-role detection; `shipment-reconcile` record-status classification | U2 must not change how any of them read `status`; it only *adds* a read. No shared mutable state. |
| `parent_id` | `_build_children_index`/`_enumerate_descendants`; protected-set Step 2; `backlogit shipment get` size rollup | Confirmed unchanged by this plan; U4 explicitly rejects clearing it. |
| `archived_status` | sequence-aware exclusion; Step 8 provenance gate; mixed-role detection | U4's exemption reads `blocked_reason`/body-marker disposition, **not** `archived_status`, so the existing provenance semantics are untouched. |

### Risky actions (`ProposedAction` / `ActionRisk`)

| ID | ProposedAction | ActionRisk | Approval |
|---|---|---|---|
| PA-1 | Invoke `{{OP_SHIP_SHIPMENT_MCP}}` (cascade engine op) solely to transition the shipment record, under `TERMINAL_CLOSE` | **HIGH** — destructive archival op; blast radius bounded by precondition 3 and proven inert against already-archived artifacts | No per-run approval required **once** all preconditions re-verify live at sub-procedure step 3; the preconditions ARE the approval boundary. Fails closed to `SAFE_CLOSE` on any drift. |
| PA-2 | Repository-approved rollback after a post-condition deviation | **HIGH** — destructive (revert/restore/overwrite) | **EXPLICIT OPERATOR APPROVAL REQUIRED** before execution. Never automatic. Constitution Principle VII. |
| PA-3 | Exclude an archived sibling from the protected set (E2) | **MEDIUM** — narrows a fail-closed safety gate | No approval; four independent machine-checkable conditions, all required, fail-closed. Step 5 invariant unchanged. |
| PA-4 | Amend binding policy P-015 text | **MEDIUM** — a permanently binding contract two agents execute | Covered by this plan-review gate; U3 forbids deleting or weakening any existing clause. |
| PA-5 | Read-only dry-runs against LIVE `173-S` / `168-S` (U6) | **LOW** — read-only | None; U6 explicitly forbids closing either shipment. |

**Safety mode for execution**: `freeze-scope` — Ship executes strictly within the
six declared units and the four declared files plus two test modules; any
surface outside that boundary halts for operator direction.

### Deepened runtime verification

**Environment prechecks before U6's dry-runs**:

1. `backlogit --version` reports **1.10.1** (the version whose refusal semantics
   and cascade behaviour this contract is written against). A different version
   invalidates the empirical basis — record it and halt the dry-run rather than
   re-interpreting the result.
2. `git status --porcelain -- .backlogit/` captured before and after each
   dry-run; the two MUST be identical. Any difference means the "read-only"
   dry-run mutated state → HALT, P-005.
3. Both `173-S` and `168-S` still `status: queued`/`active` and unclaimed.

**Target scenarios** (U6 must record the verdict + reason string for each):

| Scenario | Expected | Meaning if violated |
|---|---|---|
| LIVE `173-S` manifest | `TERMINAL_CLOSE`, evidence names `165.007-T` + `165.010-T` | Preconditions too strict (RK3) — the change does not solve the reported problem |
| LIVE `168-S` manifest | `SAFE_CLOSE` | Preconditions too loose (RK1) — **STOP, do not ship** |
| LIVE `174-S` manifest (control) | `SAFE_CLOSE` (all members live in `queue/`) | Precondition 3 is not being evaluated |

**Blocked-path handling**: if the backlog index is stale or a record is torn at
dry-run time, the expected outcome is `SAFE_CLOSE` with a reason string — record
it as a **passing** fail-closed observation, not a failure, and re-run after
`backlogit sync`.

### Deepened operational closure

* **Monitoring signal**: the `173-S` reconcile report (first production use) must
  record verdict, `terminal_evidence`, observed `archived_ids`, and the
  post-condition git comparison result.
* **Rollback trigger**: any post-condition deviation on that run; any
  protected-set member found archived during a later `168-S` safe-close; any
  `CASCADE` verdict appearing where `SAFE_CLOSE` was previously returned.
* **Rollback procedure**: PA-2 — capture → HALT → P-005 → operator approval →
  approved rollback. No auto-restore.
* **Owner**: Ship. **Validation window**: through the `173-S` closure run and the
  subsequent `168-S` classification recorded for `3CA122AC`.
* **Human checkpoints**: (1) operator P-001 authorization for the `173-S`
  sequencing overlap — **still outstanding**; (2) `174-S` DAG declaration —
  **SATISFIED 2026-09-15 by operator-authorized `labels: [dag-root]`**, without
  any bootstrap grant; (3) any PA-2 rollback. (1) and (3) remain operator-owned
  and **not** granted here.

### Partial-rollout / external-dependency constraints

The backlogit engine is a separate, non-self-owned Go project. This plan does
**not** assume any engine change (Option C remains an optional upstream
follow-up). If a future backlogit version adds a genuine non-cascading close, the
Terminal-Close Sub-Procedure's step 4 becomes a one-line substitution and the
post-condition gate remains valid unchanged — the contract is written against the
*observable result shape* (`status: archived` + `archived_status: shipped`),
not against the op name.

### Review-gate capability risks (carried into plan-review)

Reviewer subagent dispatch was **probed and found unavailable** in this session,
and the `agent-engram`, `agent-intercom`, and `graphtor-docs` MCP surfaces are
likewise unreachable. Plan-review MUST therefore:

* declare `dispatch_mode: single-agent-declared-degradation` explicitly,
* cover **every** selected persona inline with one finding list per persona
  (skipping a persona because dispatch failed is a P-012 violation),
* emit literal `dispatch_mode:` and `decision:` marker lines so `harvest` can
  fail closed,
* and record the `TOOL_DEGRADED` conditions for engram/intercom/graphtor-docs.

`strict-safety` is **not** installed in this workspace, so the
`ProposedAction`/`ActionRisk` table above is supplied as defence-in-depth rather
than as a gate precondition.

### Unresolved operator decisions still blocking safe execution

1. **P-001 authority** for the sequencing overlap: `174-S` must execute while
   `173-S` remains `active`-but-blocked. **STILL UNRESOLVED — claim-blocking.**
2. ~~**`174-S` sequencing**~~ **RESOLVED 2026-09-15**: the operator explicitly
   authorized `174-S` as a DAG root, and the record now carries `labels:
   [dag-root]` (`predecessor_source: declared_root`). No bootstrap grant was
   issued and no dependency edge was added; Stage still adds neither.
3. Whether to pursue Option C upstream once E1/E2 land (non-blocking).

## Plan Review

dispatch_mode: single-agent-declared-degradation
decision: PASS

### Gate decision and rationale

**Gate: PASS** (after one review-fix cycle). Cycle 1 surfaced three P1
findings, all three resolved in-cycle and reflected in the plan body above; the
re-review found no remaining P0/P1. Residual findings are two P2 (recorded as
follow-ups) and three P3 (advisory).

**Plan hardening**: required (§7 records four of five signals present) and
**satisfied** — a `## Plan Hardening` section is present and materially complete,
carrying protected invariants with per-invariant pinning tests, a consumer sweep,
a `ProposedAction`/`ActionRisk` table, environment prechecks, target scenarios
with stop conditions, rollback triggers/procedure/owner/validation window, and
the review-gate capability risks.

### Capability declaration (P-012)

| Capability | Status | Fallback |
|---|---|---|
| Reviewer subagent dispatch | `TOOL_DEGRADED` | Declared fallback: single-agent persona pass. Every selected persona applied inline with a separate finding list. |
| Model-specific reviewer routing (`model_routing.anchor_review`) | `TOOL_DEGRADED` | Declared fallback: same-model rubric pass for the cross-model personas. |
| `agent-engram` indexed retrieval | `TOOL_DEGRADED` | File-based grep/view over `src/`, `.github/`, `templates/`, `tests/`, `docs/compound/`. |
| `graphtor-docs` | `TOOL_UNAVAILABLE` | File-based search over `docs/`. |
| `agent-intercom` | `TOOL_DEGRADED` | Operator visibility reduced; no broadcasts emitted. Non-destructive review work proceeded. |
| `backlogit` MCP | `TOOL_OK` | — |

Every selected persona was covered and every finding normalized to the P0–P3
scale, so the degraded review is valid under the skill's own contract.

### Persona coverage

| Persona | Triggered | Mode | Findings |
|---|---|---|---|
| Constitution Reviewer | Always-on | inline (declared degradation) | 1×P1 (resolved), 1×P3 |
| Python Reviewer | Always-on | inline | 1×P2, 1×P3 |
| Scope Boundary Auditor | Always-on | inline | 1×P2 |
| Learnings Researcher | Always-on | inline | 1×P1 (resolved), 1×P3 |
| Architecture Strategist | Always-on cross-model | inline, same-model fallback | 1×P1 (resolved) |
| Agent-Native Parity Reviewer | **Triggered** — the plan changes contract text that agents execute, and changes a classifier consumed through an agent-facing skill | inline, same-model fallback | 1×P2 (merged) |
| Security Lens Reviewer | **Not triggered** — no auth/authz, API surface, sensitive data store, external trust boundary, or secrets handling. The external dependency (backlogit) is a local process boundary, not a trust boundary. | not run (trigger condition unmet) | — |

### Findings — P1 (blocking; all resolved in cycle 1)

**P1-1 — Missing red phase for the policy and skill contract surfaces**
(Constitution Reviewer; merged with Learnings Researcher's independent finding).
As originally planned, `166.002-T` scoped tests to the Python classifier only,
while `166.003-T`, `166.004-T`, and `166.005-T` changed binding contract text
with no test artifact at all and no dependency on the test task. In this
repository contract text *is* the product, and the codebase already encodes such
contracts as executable assertions
(`tests/test_shipment_reconcile_safe_close.py`,
`tests/test_scope_containment_policy_contract.py`,
`tests/test_cascade_close_archived_ids_postcondition.py`). Shipping P-015 and
`shipment-reconcile` amendments with no red phase violates Constitution
Principle II (NON-NEGOTIABLE) and P-004, and leaves the deviation-handling text —
the single most safety-critical prose in the change — unprotected against
regression.

*Resolution (applied)*: U1/`166.002-T` expanded to add a doc-contract test module
asserting, on **both** the installed artifact and its template mirror, the P-015
amendment, the Step 2/3 exemption, the Terminal-Close Sub-Procedure, the
post-condition gate, the ordered five-step deviation sequence, the literal
`git restore` prohibition, the Principle VII citation, the exit-9 record, and the
unchanged Step 5 block. Size raised `S` → `M`. Red-phase edges added:
`166.003-T` → `166.002-T` and `166.004-T` → `166.002-T` (`166.001-T` already had
one; `166.005-T`/`166.006-T` inherit transitively). Recorded as D7 and as
invariants I4/I7/I8.

**P1-2 — Architectural boundary for precondition 4 was unstated**
(Architecture Strategist). The decision artifact lists "a git baseline proves the
archives pre-exist this closure run" as E1 precondition 4 without saying which
component owns it. `166.001-T` implicitly excluded it while `166.005-T`
implicitly included it — an unstated split that would have been resolved
arbitrarily at execution time. Had it landed in the classifier it would have
broken that module's documented purity contract ("never mutates the backlog and
never calls out to `backlogit` itself"), forced `subprocess`/`git` into a pure
function, and made its `tempfile`-based unit fixtures require a git repository.

*Resolution (applied)*: recorded explicitly as **D3** — the classifier owns
preconditions 1–3 (pure filesystem + frontmatter facts); the Terminal-Close
Sub-Procedure owns precondition 4, re-verified live at step 3 immediately before
mutating, where the git baseline already exists for the post-condition
comparison. R5 in the requirements trace now names U5, not U2. U2's acceptance
criteria now state the module remains pure and read-only.

**P1-3 — Post-condition must be containment, not exact match**
(Learnings Researcher). The `archived_ids` post-condition risked being written as
an exact-match/full-set echo of the manifest, repeating the error that
`docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md` records
as twice-corrected: a truly `status: archived` item has **no transition to
report** and is **correctly absent** from `archived_ids`. On the 173-S shape
essentially every member is already archived, so an exact-match gate would fail
on a correct run and drive a false-positive deviation → false P-005 → an
unnecessary operator-approved rollback of a healthy closure.

*Resolution (applied)*: the hardening section's learnings entry now states the
gate explicitly as `archived_ids ⊆ closure set` (containment / allow-list),
"never a full-set echo or exact-match of the manifest", and U5's step 5 and R11
are phrased as "contains nothing outside the manifest closure set".

### Findings — P2 (non-blocking; recorded as follow-ups)

**P2-1 — `ClosePath` enum value string is a de facto wire format**
(Python Reviewer, merged with Agent-Native Parity Reviewer). `ClosePath` is a
`str, Enum`, so `"terminal_close"` may be serialized into reconcile reports and
read by agents. U2 should not later rename it. *Follow-up*: treat the literal
value as frozen once shipped; if a reconcile report schema is ever versioned, the
enum value belongs in it.

**P2-2 — `terminal_evidence` payload shape is unspecified**
(Scope Boundary Auditor). U2 specifies `tuple[str, ...]` but not whether entries
are bare IDs or ID+reason strings; U6 asserts it "names `165.007-T` and
`165.010-T`". Bare IDs satisfy both. *Follow-up*: if a richer payload is wanted
later, that is a separate, out-of-scope change — adding it now would be scope
creep (YAGNI) against a decision artifact that asks only for "a structured
reason/evidence payload naming the artifacts".

### Findings — P3 (advisory)

* **P3-1** (Constitution Reviewer): the plan could name the canonical test
  invocation in every unit rather than only U6. Acknowledged; U6 already pins
  `python -m unittest discover -s tests` as the canonical CI form.
* **P3-2** (Python Reviewer): `location: str` on `_ArtifactRecord` could be a
  two-member enum. A plain string matches the module's existing minimalism;
  either is acceptable.
* **P3-3** (Learnings Researcher): the `168-S` dry-run verdict should be written
  back to stash `3CA122AC` when it is eventually triaged. Already covered by U6's
  acceptance ("recorded for the `3CA122AC` follow-up") — noted so the linkage is
  not lost.

### Scope boundary audit

No scope creep detected after the P1-1 resolution. The added doc-contract tests
are *verification of already-planned changes*, not new product scope. Width
isolation holds: U1 tests-only, U2 Python-only, U3 policy-only, U4+U5 skill-only
(distinct, non-overlapping sections of the same file — U4 touches Steps 2–3, U5
touches Step 0(c), the new sub-procedure, Step 8, Output, and the Scenario
Matrix), U6 validation-only. Every unit stays within the 2-hour volume bound, and
every `complexity: high` unit has recorded de-risking (D8).

### Constitutional compliance

| Principle | Verdict |
|---|---|
| I — Safety-First Python | PASS — stdlib only; explicit fail-closed error handling reused from existing surfaces; no silent failures |
| II — Test-First (NON-NEGOTIABLE) | PASS after P1-1 resolution — U1 precedes every implementation unit by declared edge |
| III / IV — Workspace isolation & containment | PASS — `_ARTIFACT_ID_PATTERN` validation retained before any glob interpolation; all paths workspace-relative |
| V — Structured Observability | PASS — `terminal_evidence`, reconcile report, P-005 telemetry on deviation |
| VI — Single Responsibility | PASS — no new dependencies; D3 keeps the classifier pure |
| VII — Destructive Command Approval (NON-NEGOTIABLE) | PASS — the plan's central safety property; auto-restore explicitly prohibited in four places (U3, U5, D6, PA-2) |
| VIII — Explicit Safety Modes | PASS — `freeze-scope` declared for execution |
| IX — Git-Friendly Persistence | PASS — Markdown + YAML frontmatter throughout |
| X — Agent Context Efficiency | PASS — reuses the single whole-backlog `_build_children_index` scan rather than re-scanning per member |
| XI — Merge Commit Preservation | N/A — no merge-strategy change |

### Runtime verification and operational closure readiness

Present and specific: §8 plus the hardening section supply environment
prechecks (including the backlogit **1.10.1** version pin, whose violation halts
the dry-run rather than being re-interpreted), three target scenarios with an
explicit **STOP, do not ship** condition on the `168-S` control, blocked-path
handling, monitoring signals, rollback trigger/procedure/owner, and the
validation window. No gaps called out.

### Recommendations carried to harvest

1. Apply the P1-1 task-graph reconciliation: `166.002-T` scope + size `S`→`M`;
   add red-phase edges `166.003-T` → `166.002-T` and `166.004-T` → `166.002-T`.
2. Apply the D3 boundary to `166.001-T` (preconditions 1–3, purity preserved) and
   `166.005-T` (precondition 4 re-verified live at sub-procedure step 3).
3. Apply the P1-3 containment phrasing to `166.005-T`'s post-condition text.
4. Do **not** add shipment `dependencies` or a bootstrap grant to `174-S`.
   (Amended 2026-09-15: the operator explicitly authorized the `dag-root` label,
   which has been applied; it is **not** a bootstrap grant. `174-S` remains
   unclaimable pending operator P-001 overlap authority.)
