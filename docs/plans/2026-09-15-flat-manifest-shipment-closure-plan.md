---
title: "Flat-manifest shipment closure — implementation plan"
description: "Test-first implementation plan for the reframed feature 166-F: replaces the P-015 hierarchical-closure precondition with an engine-inertness blast-radius containment gate in classify_shipment_close_path, redefines the shipment-reconcile protected-set gate from baseline-presence to baseline-invariance, records the fail-closed escalation for the unresolved partial-shipment record transition, mirrors both contract surfaces into templates/, and proves 173-S closable via a read-only dry-run without mutating its excluded siblings."
doc_type: plan
source: docs/plans/2026-09-15-flat-manifest-shipment-closure-plan.md
date: 2026-09-15
status: reviewed
revision: 1
revision_note: "Produced by impl-plan for the reframed 166-F after the operator architectural correction superseded the TERMINAL_CLOSE premise. Hardened under P-006 (policy + skill + classifier + template-mirror blast radius), then gated through plan-review cycle 1 (two P0 and three P1 findings resolved in-cycle)."
decision_source: docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md
supersedes_plan: docs/plans/2026-09-15-terminal-shipment-closure-plan.md
superseded_decision: docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md
feature_id: 166-F
shipment_id: 174-S
stash_ids:
  - FBD2F6BE
  - 2B42392E
related_stash_ids:
  - 3CA122AC
---

# Implementation Plan — Flat-Manifest Shipment Closure

## 1. Source Understanding

Implements the decision
`docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md`
(**Option F** — flat manifest + engine-inertness containment), which supersedes
`docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md`
(Option E, `TERMINAL_CLOSE`) following a binding operator architectural
correction.

### Problem frame (technical restatement)

A shipment manifest is a **flat list of exactly what is delivered**. Closure
scope is `items(S) ∪ {S}`. Three surfaces currently violate this by expanding
closure scope through `parent_id` ancestry:

| Surface | File | Defective assumption |
|---|---|---|
| Classifier | `src/autoharness/gates/shipment_closure.py` | `missing = [d for d in descendants if d not in manifest_id_set]` requires the manifest to be a **closed container** over the feature subtree. Disqualifies `173-S` on two archived, descoped siblings. |
| Protected set | `.github/skills/shipment-reconcile/SKILL.md` Safe-Close Steps 2–3 | Step 2 enumerates hierarchy-prefix siblings into a protected set; Step 3 requires **every** member to be **present in `queue/`**, so a sibling already archived *before the run* is misread as a pre-existing cascade and halts closure. |
| Policy | `.github/policies/workflow-policies.md` P-015 precondition 1 | States the hierarchical-closure rule in normative prose, mirrored to `templates/policies/workflow-policies.md.tmpl`. |

### The safety constraint that must survive (measured, not assumed)

The backlogit 1.10.1 engine expands scope hierarchically. Stage spike evidence
(four disposable `%TEMP%` workspaces, all destroyed; see the decision's F3):

| Manifest shape | Out-of-manifest descendant | Engine effect |
|---|---|---|
| has feature member | declares `status: archived` | **inert** — skipped, byte-identical |
| has feature member | `status: done` | **archived** (out-of-scope mutation) |
| has feature member | live `queued` | **archived**, and `returned_ids` was **`[]`** |
| no feature member | live | **returned, `parent_id` silently CLEARED** |
| any | ancestor/parent of a manifest item | untouched (no upward walk) |

So the descendant walk must be **retained**, but its verdict must change from
*"is it in the manifest?"* (scope) to *"can the engine mutate it?"* (blast
radius). This is the single conceptual change the whole plan implements.

### Scope boundaries carried from the decision

* **No third close verdict.** `ClosePath` keeps exactly `SAFE_CLOSE` and
  `CASCADE`. `TERMINAL_CLOSE` is **not** added.
* **No git-baseline precondition** inside the classifier; it stays a pure,
  read-only function.
* **No disposition-note requirement** on out-of-manifest artifacts.
* **`173-S` MUST NOT be mutated** by this shipment.
* **No P-001 overlap authority, no bootstrap grant, no claimability expansion.**
  `174-S` keeps its existing operator-authorized `dag-root` label and empty
  `dependencies`.
* **R1 (partial-shipment record transition) is NOT solved here** — it is
  surfaced as a fail-closed halt and routed upstream.

## 2. Requirements Trace

| # | Requirement (decision ref) | Unit | Verified by |
|---|---|---|---|
| R01 | INV-1 closure scope = `items(S) ∪ {S}` | U3 | doc-contract test |
| R02 | INV-2 membership explicit/exhaustive | U2, U3 | classifier + doc tests |
| R03 | INV-3 excluded items never gate on ancestry | U2 | `test_archived_out_of_manifest_child_selects_cascade` |
| R04 | INV-3 no disposition note required | U2, U4 | fixture with no `archived_status` still CASCADEs |
| R05 | INV-4 multi-shipment delivery; feature last in final manifest | U3 | split-delivery doc-contract test |
| R06 | INV-5 feature terminality over *delivered* tasks only | U3 | doc-contract test |
| R07 | INV-6 engine-inertness gate (`status: archived` only) | U2 | inertness positive + 2 negatives |
| R08 | INV-6 status read from frontmatter, never location | U2 | `archive/`-located, no-`status` fixture → SAFE_CLOSE |
| R09 | INV-7 baseline-invariance replaces baseline-presence | U5 | skill doc-contract test |
| R10 | INV-8 ordering is assembly-only, never a closure gate | U3, U4 | doc-contract test; `173-S` feature-first still CASCADEs |
| R11 | INV-9 DAG orthogonality | U3 | doc-contract test |
| R12 | INV-10 postconditions incl. byte-identity | U4, U6 | two-set gate retained + dry-run |
| R13 | `returned_ids` recorded as **insufficient** | U4 | skill doc-contract test |
| R14 | Arm-2 destructive case blocked **pre-mutation** | U1, U2 | negative classifier tests |
| R15 | Template mirrors byte-parity | U6 | parity test |
| R16 | `173-S` closable, siblings untouched | U6 | read-only dry-run |
| R17 | `168-S` control fixture | U6 | dry-run control |
| R18 | R1 fail-closed escalation, no silent workaround | U5 | skill doc-contract test |

## 3. Implementation Units

### U1 — Red-phase test suite (`166.002-T`) — size M, complexity medium

Add failing tests **before** any implementation (Constitution Principle II).

1. **Extend the fixture helper.** `tests/test_shipment_closure_classification.py`'s
   `_write_artifact` currently writes **no `status` field**. Add an optional
   `status: str | None = None` parameter. *(This is why the entire existing
   negative suite survives — see §5 D3.)*
2. **New positive (the `173-S` shape, R03/R07):**
   `test_archived_out_of_manifest_child_selects_cascade` — feature + one manifest
   task + an out-of-manifest child declaring `status: archived` and **no**
   `archived_status` → expect `CASCADE`.
3. **New negatives (Arm 2, R14):**
   `test_done_but_not_archived_out_of_manifest_child_falls_back_to_safe_close`
   and `test_live_out_of_manifest_child_falls_back_to_safe_close` → both expect
   `SAFE_CLOSE`, reason naming the offending ID.
4. **Location-never-sufficient (R08):**
   `test_out_of_manifest_child_in_archive_without_status_falls_back_to_safe_close`.
5. **Grandchild depth (R07):** archived out-of-manifest **grandchild** → `CASCADE`;
   live out-of-manifest grandchild → `SAFE_CLOSE`.
6. **Doc-contract tests** in a new `tests/test_flat_manifest_closure_docs.py`
   asserting INV-1..INV-10 phrasing is present in **both** policy mirrors and
   **both** skill mirrors, that the strings `TERMINAL_CLOSE` and
   "fully covered" no longer appear as normative preconditions, and that the
   `returned_ids`-is-insufficient statement is present (R13).

**Exit**: every new test fails for the right reason; the pre-existing suite
still passes untouched.

### U2 — Classifier: coverage → inertness containment (`166.001-T`) — size M, complexity high

`src/autoharness/gates/shipment_closure.py`:

1. Extend `_ArtifactRecord` with `status: str | None`, read from frontmatter and
   normalized (lower-cased, stripped). A **declared-but-unnormalizable** `status`
   fails closed exactly as the existing malformed-`parent_id` path does.
2. Extend `_build_children_index` to return `(children_index, status_index)` so
   the declared status of **every** backlog record is available without a second
   scan. A malformed record anywhere still invalidates the whole index
   (`None` → `SAFE_CLOSE`).
3. **Replace** the coverage predicate:

   ```python
   # WAS: every descendant must be a manifest member (hierarchical closure)
   missing = tuple(d for d in descendants if d not in manifest_id_set)

   # NOW: every out-of-manifest descendant must be ENGINE-INERT (INV-6)
   out_of_manifest = tuple(d for d in descendants if d not in manifest_id_set)
   non_inert = tuple(d for d in out_of_manifest if status_index.get(d) != "archived")
   ```

   `non_inert` non-empty → `SAFE_CLOSE`, reason naming the IDs **and** their
   observed status.
4. **`accounted_ids` / `extras` must remain unchanged.** `extras` still rejects a
   manifest member that is neither a qualifying root feature nor its descendant.
   *(Do not add inert out-of-manifest descendants to `accounted_ids` — they are
   not manifest members; adding them would silently re-widen closure scope.)*
5. Update the module docstring to state the flat-manifest contract and INV-6,
   and to record that the descendant walk is a **blast-radius** check.

**Purity preserved**: no git access, no mutation, no backlogit calls.

### U3 — P-015 policy rewrite + mirror (`166.003-T`) — size M, complexity medium

`.github/policies/workflow-policies.md` and
`templates/policies/workflow-policies.md.tmpl` (identical edits):

1. Rewrite the **Statement** in flat-manifest terms: closure scope is the
   manifest's explicit item IDs plus the shipment record; **ancestry never
   expands closure scope**.
2. Replace the "VERIFIED FULLY-COVERED-ROOT EXCEPTION" heading and
   preconditions 1–5 with **INV-1..INV-10**, verbatim from the decision.
3. Rewrite **Precondition** and **Required Check** to baseline-**invariance**
   (INV-7) rather than baseline-**presence**.
4. Add a **SUPERSESSION NOTE (2026-09-15)** withdrawing the hierarchical-closure
   preconditions, naming the operator correction and the superseded decision, and
   preserving the existing 155-S supersession note.
5. State INV-8 explicitly: manifest **ordering** is a Stage assembly convention
   and MUST NOT be evaluated as a closure precondition.

### U4 — Skill Step 0(c): inertness classification + mirror (`166.004-T`) — size M, complexity medium

`.github/skills/shipment-reconcile/SKILL.md` and
`templates/skills/shipment-reconcile/SKILL.md.tmpl`:

1. Rewrite Step 0(c) to the INV-6 inertness predicate; delete the
   "fully covered"/"nothing extra" coverage wording.
2. Add the measured engine-behavior table (decision F3) as the stated rationale.
3. **Record that `returned_ids` is insufficient** (R13): Arm 2 archived a live
   out-of-manifest task while returning `[]`. Step 2's guard is retained but
   explicitly demoted to a secondary check; the **pre-mutation** inertness gate is
   the primary protection.
4. Leave the Cascade Close Sub-Procedure's two-set `allowed_ids`/`required_ids`
   gate **unchanged** — it is already flat-manifest-shaped and remains the
   post-mutation guard (INV-10).

### U5 — Safe-close baseline invariance + R1 escalation + mirror (`166.005-T`) — size M, complexity high

Both skill mirrors:

1. **Step 2** — the protected set becomes an **observation set**: out-of-manifest
   artifacts are enumerated to be *watched*, not to be *required present*. Delete
   the sequence-aware-exclusion provenance requirement (INV-3 makes it moot).
2. **Step 3** — replace the presence gate with the **baseline-invariance** gate
   (INV-7): record each observed artifact's location + content hash; a member
   already archived/descoped/missing **at baseline** is recorded, **not** a halt.
3. **Step 5** — the verify-after-each invariant compares against the **baseline
   fingerprint** (changed vs. baseline), not against "present in `queue/`".
4. **Step 8** — when `move --status shipped` is refused (exit 9) and the manifest
   is **not** cascade-eligible, halt fail-closed with a new, explicit code
   `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`, naming R1, stating that the
   cascade MUST NOT be substituted (Arms 3–4 clear `parent_id` on returned
   siblings), and routing to the operator/upstream. **No silent workaround.**

### U6 — Mirror parity, harness validation, read-only dry-runs (`166.006-T`) — size S, complexity medium

1. Add a parity test asserting the two skill mirrors and the two policy mirrors
   agree on the INV-1..INV-10 block (R15).
2. Run `pytest`, frontmatter/markdown/cross-reference/placeholder validation.
3. **Read-only `173-S` dry-run** (R16) — no writes; emits classifier verdict,
   engine-reachable set, predicted `allowed_ids`/`required_ids`/`archived_ids`,
   and a pre-image hash manifest for `165.007-T`/`165.010-T`.
   **Expected**: `CASCADE`; predicted `archived_ids` = 11 manifest members +
   `173-S`; `returned_ids` = `[]`; both siblings absent from every predicted set.
4. **`168-S` control dry-run** (R17) — classify only; **any** unexpected
   `CASCADE` grant with a non-inert out-of-manifest descendant is a **STOP,
   DO-NOT-SHIP** condition.
5. Verify `173-S`, `165.007-T`, `165.010-T` are byte-identical to `HEAD`.

## 4. Dependency Graph

```text
166.002-T  (U1 red phase; no prerequisites)
   ├─> 166.001-T  (U2 classifier)
   ├─> 166.003-T  (U3 P-015 policy + mirror)
   └─> 166.004-T  (U4 skill Step 0(c) + mirror)

166.005-T  (U5 safe-close Steps 2/3/5/8 + mirror)
             <- 166.001-T, 166.003-T, 166.004-T
166.006-T  (U6 parity, gates, read-only dry-runs)
             <- 166.004-T, 166.005-T
```

Edges as stored in backlogit (verified acyclic; topological order
`166.002-T → 166.001-T → 166.003-T → 166.004-T → 166.005-T → 166.006-T`).
The `166.005-T ← 166.004-T` edge was added deliberately: U4 and U5 edit the
**same two skill mirrors**, so they must be serialized to avoid a same-file
conflict. Task-level only — `174-S`'s own `dependencies` field stays empty.
Every unit is sized at or below the 2-hour rule.

## 5. Decisions and Rationale

* **D1 — Keep the descendant walk.** Deleting it (decision Option G) is
  empirically destructive. The walk is the only way to compute the engine's
  reachable set; only its *verdict* changes.
* **D2 — Inertness is keyed on `status: archived` alone.** Not on
  `archived_status`, not on a disposition note, not on location — this is exactly
  what the engine's `archiveItems()` skip-condition keys on, and exactly what
  INV-3 permits us to demand.
* **D3 — The existing negative test suite survives unchanged.** `_write_artifact`
  writes no `status` field, so every existing out-of-manifest fixture is
  *non-inert* under INV-6 and still yields `SAFE_CLOSE`; each assertion checks
  only `close_path` and that the offending ID appears in `reason`, both of which
  still hold. Migration is therefore **purely additive** — a strong
  backward-compatibility signal, and the reason no test file is rewritten.
* **D4 — Reframe `166-F` in place.** A replacement shipment would require a new
  operator `dag-root` authorization, which this session is forbidden to expand.
* **D5 — R1 is not solved by substitution.** For a genuine `SAFE_CLOSE`
  shipment there is no safe path to `archived_status: shipped` in 1.10.1; the
  honest engineering answer is a fail-closed halt plus an upstream request.

## 6. Risks and Caveats

| Risk | Mitigation |
|---|---|
| Implementer restores the coverage check "for safety" | U1 pins the inverted expectation *first*; the `173-S` positive fixture fails if coverage returns |
| `accounted_ids` widened to include inert descendants | Explicit U2 step 4 prohibition + `extras` regression tests |
| Inertness inferred from `archive/` location | R08 fixture: `archive/`-located, no `status` → `SAFE_CLOSE` |
| Policy/skill mirrors drift | U6 parity test over the INV block |
| Dry-run mutates `173-S` | Read-only by construction; byte-identity re-verified against `HEAD` |
| R1 silently worked around with the cascade | New explicit failure code + skill prohibition citing Arms 3–4 |

### Negative scenarios to add to the Scenario Matrix (U5)

1. Out-of-manifest descendant `status: done` → `SAFE_CLOSE`.
2. Out-of-manifest descendant live `queued` → `SAFE_CLOSE`.
3. Out-of-manifest descendant in `archive/` with no `status` → `SAFE_CLOSE`.
4. Out-of-manifest **grandchild** live → `SAFE_CLOSE`.
5. Protected artifact archived **at baseline** → recorded, **not** a halt.
6. Protected artifact changed **during** the run → halt (INV-7).
7. Partial shipment, `move --status shipped` refused →
   `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`, cascade **not** substituted.

## 7. Plan Hardening Signals (REQUIRED)

| Signal | Present | Evidence |
|---|---|---|
| Touches a NON-NEGOTIABLE policy | **yes** | P-015 statement + preconditions rewritten |
| Touches a safety classifier | **yes** | `shipment_closure.py` verdict predicate |
| Multi-surface blast radius | **yes** | classifier + policy ×2 + skill ×2 + tests |
| Changes a destructive-op gate | **yes** | governs when the cascade op may run |
| External tool behavior dependency | **yes** | backlogit 1.10.1 engine semantics |

**Requires plan hardening: yes** (4 of 5 → P-006 mandatory).

## 8. Runtime Verification and Closure

* `pytest tests/` green, including the new inertness suite.
* Frontmatter, markdown, cross-reference, and unresolved-placeholder validation on
  all four contract files.
* Mirror parity test green.
* `173-S` dry-run returns `CASCADE` with a containment-clean prediction.
* `168-S` control dry-run does not grant an unsafe `CASCADE`.
* `git status` shows no modification to `173-S`, `165.007-T`, `165.010-T`.

---

## Plan Hardening

Executed under **P-006** (mandatory: 4 of 5 signals present).

### Risk triggers and protected invariants

| # | Protected invariant | Pinning test |
|---|---|---|
| H1 | Classifier never grants `CASCADE` with a live out-of-manifest descendant | `test_live_out_of_manifest_child_falls_back_to_safe_close` |
| H2 | Classifier never grants `CASCADE` with a `done`-not-archived out-of-manifest descendant | `test_done_but_not_archived_..._safe_close` |
| H3 | Inertness never inferred from location | `test_out_of_manifest_child_in_archive_without_status_..._safe_close` |
| H4 | Archived descoped sibling **does not** block (the operator's core requirement) | `test_archived_out_of_manifest_child_selects_cascade` |
| H5 | Fail-closed default on any index/parse failure remains `SAFE_CLOSE`, never `CASCADE` | existing `..._query_failure_...` test retained |
| H6 | `extras` check not weakened | existing extras tests retained |
| H7 | Post-mutation two-set gate unchanged | skill diff review + doc test |
| H8 | `173-S` and its excluded siblings unmutated | byte-identity check vs `HEAD` |
| H9 | Ordering never becomes a closure gate | `173-S` (feature-**first**) still classifies `CASCADE` |

### Same-field consumer sweep

Consumers of `classify_shipment_close_path` / `ClosePath`:
`src/autoharness/gates/shipment_closure.py` (definition),
`tests/test_shipment_closure_classification.py`,
`.github/skills/shipment-reconcile/SKILL.md` Step 0(c) + Cascade Sub-Procedure,
`templates/skills/shipment-reconcile/SKILL.md.tmpl`,
`.github/policies/workflow-policies.md` P-015,
`templates/policies/workflow-policies.md.tmpl`.
**No `ClosePath` enum member is added or removed**, so no consumer needs a new
branch — this is a deliberate hardening property of Option F over Option J.

### Risky actions (`ProposedAction` / `ActionRisk`)

| Action | Risk | Control |
|---|---|---|
| Rewrite classifier verdict predicate | **high** — governs a destructive op | Red-phase first; 9 pinning tests; fail-closed default preserved |
| Rewrite P-015 normative text | **high** — NON-NEGOTIABLE policy | Supersession note; mirror parity; doc-contract tests |
| Rewrite safe-close Steps 2/3/5 | **medium** — loosens a halt gate | Replaced by a *stricter-in-kind* invariance check, not removed |
| Add `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` | **low** | Additive; fail-closed |
| Read-only dry-runs | **low** | No writes; hash-verified |

### Environment prechecks

* backlogit pinned at **1.10.1** (`1.10.1-0.20260823032255-b07729386a31+dirty`);
  the inertness law is version-specific — re-run the spike arms if the engine
  version changes.
* Single worktree on `main` (P-016 verified).
* Unrelated dirty worktree state must be preserved.

### Target dry-run scenarios with STOP conditions

1. `173-S` → expect `CASCADE`, containment-clean. **STOP** if `SAFE_CLOSE` or if
   either sibling appears in any predicted set.
2. `168-S` → classify only. **STOP, DO-NOT-SHIP** if `CASCADE` is granted while a
   non-inert out-of-manifest descendant exists.
3. Synthetic Arm-2 fixture → expect `SAFE_CLOSE`. **STOP** if `CASCADE`.

### Rollback

* **Trigger**: any pinning test fails, or a dry-run hits a STOP condition.
* **Procedure**: revert the unit's commit; contract files are text-only and the
  classifier change is confined to one predicate.
* **Owner**: Ship, with operator notification.
* **Validation window**: through U6's dry-runs.

### Partial-rollout / external-dependency constraints

R1 (upstream backlogit) is **explicitly out of scope** and must not be
back-doored. R2 (engine `parent_id` clearing on returned siblings) is an upstream
report, not a code change here.

### Unresolved operator decisions still blocking safe execution

1. **P-001 overlap authority** for `174-S` against the still-active `173-S` —
   operator-owned, **open**, sole claim blocker.
2. R1 / R2 upstream disposition.

---

## Plan Review

`dispatch_mode: single-agent-declared-degradation` (P-012 — reviewer subagent
dispatch probed and unavailable).

### Gate decision

**`decision: PASS`** after one review-fix cycle. **2 P0** and **3 P1** findings
raised; **all resolved in-cycle**.

### Persona coverage

Selected 7; ran 6. *Security Lens Reviewer* trigger condition unmet (no
authn/authz/secret surface) — recorded, not silently skipped.

### Findings — P0 (blocking; resolved in cycle 1)

* **P0-1 — Original draft deleted the descendant walk entirely.** A literal
  reading of "hierarchy must not expand closure scope" removed
  `_enumerate_descendants`. Spike Arm 2 proves this permits the engine to archive
  a **live** out-of-manifest task while reporting `returned_ids: []`.
  **Resolution**: walk retained; only the verdict predicate changed. Recorded as
  decision Option G (rejected) and plan §5 D1.
* **P0-2 — `accounted_ids` was to absorb inert out-of-manifest descendants.**
  That would have let the `extras` check pass for manifest members outside any
  qualifying root — silently re-widening closure scope through the back door.
  **Resolution**: explicit prohibition, U2 step 4, plus retained `extras`
  regression tests (H6).

### Findings — P1 (blocking; resolved in cycle 1)

* **P1-1 — Manifest ordering would have invalidated every historical manifest.**
  INV-4 places the feature **last**, but all existing manifests (including
  `173-S`) list it **first**. Enforcing ordering at closure would have blocked
  `173-S` — the very shipment this plan unblocks.
  **Resolution**: INV-8 added — ordering is a Stage **assembly** convention, never
  a closure gate; pinned by H9.
* **P1-2 — Red phase did not cover the policy/skill contract surfaces.**
  **Resolution**: U1 item 6 adds `tests/test_flat_manifest_closure_docs.py`;
  red-phase edges added from `166.002-T` to `166.003-T` and `166.004-T`.
* **P1-3 — R1 had no defined failure behavior**, risking a silent cascade
  substitution on a partial shipment (which Arms 3–4 prove orphans siblings).
  **Resolution**: U5 step 4 adds `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` with
  an explicit no-substitution prohibition (R18).

### Findings — P2 (non-blocking; follow-ups)

* **P2-1** — Report backlogit `parent_id`-clearing upstream (decision R2).
* **P2-2** — `168-S` closure remains unclassified until its own closure (R4).

### Findings — P3 (advisory)

* **P3-1** — Consider surfacing the inertness verdict in the closure report for
  auditability.
* **P3-2** — The `done`-without-provenance archive shape (366 records) remains
  accommodated, not corrected (R5).

### Scope boundary audit

No unit touches `173-S`, `165.007-T`, `165.010-T`, the `160-F` family, or
`174-S`'s `dependencies`/`labels`. No P-001 authority, bootstrap grant, or
claimability change is introduced.

### Constitutional compliance

Principle II (test-first) satisfied via U1 and the red-phase edges; Principle VII
(destructive-command approval) unaffected — this plan **narrows** the conditions
under which the destructive op may run.
