---
title: "Flat-manifest shipment closure: superseding the hierarchical-closure premise (operator architectural correction)"
description: "A shipment manifest is a flat list of exactly what is delivered, not a container over a covering feature and its descendants. Replaces the TERMINAL_CLOSE + terminal-descope-exemption decision with an engine-inertness containment model grounded in measured backlogit 1.10.1 behavior."
topic: "Shipment closure scope semantics: flat manifest vs. hierarchical closure"
depth: "deep"
decision_status: "decided"
revision: 5
revision_note: "Revision 5 (2026-09-16) resolves a single P1 raised by the Copilot P-018 review gate on 174-S/PR #454: D1a's `required_ids(S)` formula (as stated in this document) contradicted the already-established, tested, and shipped 155-S/PR #407 correction -- the shipment record and every qualifying feature member are required UNCONDITIONALLY regardless of their own pre-close declared status, not merely `x is not already truly archived`; `validated_linked_deliberations(S)` DOES enter `required_ids(S)` (conditionally, when not already truly archived), contrary to this document's prior 'never enters `required_ids(S)`' claim. `.github/policies/workflow-policies.md`, `.github/skills/shipment-reconcile/SKILL.md`, and `src/autoharness/gates/shipment_closure.py` already implement and test the 155-S-corrected rule; this document's D1a table was the stale surface and is now reconciled to match, not the other way around -- no closure-scope behavior changes as a result of this revision, only this document's own description of already-shipped behavior. Revision 4 (2026-09-16) resolves the four deduplicated P1 groups of the THIRD AND FINAL permitted external review-fix cycle over the revision-3 package. All four narrow a claim, delete a false claim, or add a proof obligation; none widens an authorization. (A) Test-granularity contradiction: D11 mandated exactly one class per test while assigning two classes (CLASS 4 verdict, must start green; CLASS 1 reason text, must start red) to a single named test for A2/A3/A9/A10 — the observables are now SPLIT into separately named single-class tests, and class is gated at test-function granularity. (B) Evidence-honesty propagation completed: the residual 'classifier fixtures become the authoritative record of engine law' claims and the 'measured engine' phrasings for returned_ids and parent_id clearing are withdrawn on every remaining surface; those effects are INDICATIVE/UNPROVEN and cannot authorize cascade. (C) Historical replay/evidence correctness: D4's current-recorded-manifest 12-ID must-language is explicitly superseded by D10 G1/G2/G3; G1 now materializes the COMPLETE pre-close shape including the excluded descendants 165.007-T and 165.010-T, blob-OID-pinned, with non-vacuous discovered->parsed-canonical-archived->excluded-as-inert assertions; G3 no longer claims the unfiltered `git show --stat e4ca20e5` contains 12 paths nor that e4ca20e5 is close-only (it is the COMBINED PUBLICATION COMMIT, 34 paths) and is replaced by explicit path-scoped before/after evidence between 358b63b4 and e4ca20e5. (D) Constitutional workspace containment: the revision-3 permission for tempfile.TemporaryDirectory() under OS %TEMP% is WITHDRAWN as a Constitution IV containment violation and its automatic cleanup as a Principle VII destructive-approval violation; ALL fixture/scratch/replay workspaces must resolve under the repository-internal git-ignored root .autoharness/staging/tmp/ with canonical resolved-realpath containment checks, no writes outside cwd, and operator-controlled (D6-routed) deletion only. Revision 3 (2026-09-16) resolves the five deduplicated P1 blockers from the completed local fix-verification review, all of which narrow a claim or state an existing limit honestly: the red matrix is corrected to four classes because most revision-2 CLASS 1 cases are already green on current main (D11); engine-law and classifier-law evidence are separated into disjoint classes so no classifier fixture is claimed to prove engine behaviour, and the containment rule is re-scoped (SUPERSEDED BY REVISION 4) (D7a, D7b); the 173-S retrospective gate is pinned to the immutable pre-close revision 358b63b4 and split into replay/current-state/engine-effect gates (D10); the contradictory 2026-09-14 closure artifact is recorded as a historical blocked-phase record that Stage may not rewrite, with a Ship/operator-owned superseding closure record recorded as a 174-S readiness prerequisite and the unqualified P-001 discharge claim withdrawn (D8a); and the unimplementable byte-for-byte status contract is replaced by exact parsed-scalar equality with non-string fail-closed, since every record reaches the predicate through yaml.safe_load (D1b). Revision 2 (2026-09-16) resolved consolidated local-review blockers: INV-1/INV-2 reconciled against explicit manifest/closure/allowed/required set definitions (D1a); INV-6 tightened to an exact canonical status match with torn/duplicate-ID fail-closed (D1b); multi-shipment delivery honestly split into contract-complete vs. operationally-blocked with INV-11 and an external runtime prerequisite; destructive-rollback language replaced by the capture-halt-P-005-approve-revalidate sequence; spike evidence downgraded to non-authoritative with a recorded P-005 containment violation; 173-S recorded as operator-closed and verified."
promoted_to: "both"
linked_artifacts:
  - "docs/plans/2026-09-15-flat-manifest-shipment-closure-plan.md"
  - "docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md"
supersedes:
  - "docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md"
stash_entries:
  - "FBD2F6BE"
  - "2B42392E"
related_entries:
  - "3CA122AC"
  - "7F9CB5E9"
  - "63363CF5"
tags:
  - "shipment-closure"
  - "flat-manifest"
  - "p-015"
  - "blast-radius-containment"
  - "backlogit-tooling"
  - "supersession"
  - "revision-2"
  - "revision-3"
  - "revision-4"
  - "revision-5"
---

# Flat-Manifest Shipment Closure — Deliberation

> ## 🔄 REVISION 5 — 2026-09-16 — AUTHORITATIVE
>
> Revision 5 resolves a **single P1** raised by the **Copilot P-018 review
> gate** on `174-S`/PR #454 against D1a's `required_ids(S)` table below.
>
> | Blocker | Disposition | Where |
> |---|---|---|
> | D1a's `required_ids(S)` formula — `{ x ∈ closure_scope(S) : x is not already truly archived }`, with linked deliberations stated to "never enter `required_ids(S)`" — contradicted the already-established, tested, and shipped **155-S/PR #407** correction, creating two authoritative-looking but mutually incompatible destructive-close postcondition surfaces | `required_ids(S)` is restated to match the **already-shipped** rule: `{S} ∪ {qualifying feature members of S}` (both **unconditionally** required regardless of their own pre-close declared status) `∪ {x ∈ allowed_ids(S) : x is not already truly archived in the pre-close snapshot}` (every other member — a manifest task item, or a qualifying feature member's validated linked deliberation — required only when not already truly archived). `.github/policies/workflow-policies.md`, `.github/skills/shipment-reconcile/SKILL.md`, and `src/autoharness/gates/shipment_closure.py` already implement and test this rule; **this document's table was the stale surface**, not the implementation | **D1a** |
>
> **No closure-scope behavior changes as a result of this revision.** This
> revision corrects this document's own description of already-shipped,
> already-tested behavior to match reality; it does not authorize, widen, or
> narrow anything the implementation does.

> ## 🔄 REVISION 4 — 2026-09-16 — superseded in part by Revision 5
>
> Revision 4 resolves the **four deduplicated P1 groups** raised by the **third
> and final permitted external review-fix cycle** against the revision-3
> package. **Option F, the six units, the 1:1 task mapping, INV-1..INV-11, and
> the withdrawal of `TERMINAL_CLOSE`/E2 are all UNCHANGED.**
>
> | P1 group | Blocker | Disposition | Where |
> |---|---|---|---|
> | **A** | **Test-granularity contradiction** — D11 required *exactly one class per test* while assigning **two** classes (CLASS 4 verdict, must start **green**; CLASS 1 reason text, must start **red**) to the **same named test** for A2/A3/A9/A10 | **Observables SPLIT into separately named single-class tests.** Class is declared and gated at **test-function granularity**; a CLASS 4 verdict test may not assert on `reason`, and a CLASS 1 reason test may not assert a verdict | **D11** (granularity rule + split table) |
> | **B** | **Incomplete evidence-honesty propagation** — residual "classifier fixtures become the authoritative record" claims, and `returned_ids` / `parent_id` effects still stated as *measured facts* | Residual claims **withdrawn on every surface**. Classifier-law/engine-law separation restated; unproven engine behaviour is **indicative + fail-closed** and **cannot authorize cascade** | **D7a**, `166-F`, `166.003-T`, `166.004-T`, `166.005-T`, handoff memory |
> | **C** | **Historical replay/evidence correctness** — D4 still demanded a current recorded-manifest dry-run reproduce the pre-close 12-ID result while D10 withdrew it; G1 asserted only *absence* of the excluded siblings; G3 claimed the unfiltered `git show --stat e4ca20e5` contains exactly 12 paths and treated `e4ca20e5` as close-only | D4's must-language **explicitly superseded/withdrawn**, repointed to G1/G2/G3. **G1 materializes the complete 14-row pre-close shape** (record + 11 members + `165.007-T`/`165.010-T`), blob-OID-pinned, with **non-vacuous** discovered → parsed-canonical-`archived` → excluded-as-inert assertions. **G3 replaced by explicit path-scoped before/after evidence** between `358b63b4` and `e4ca20e5`; `e4ca20e5` is recorded as the **combined publication commit (34 paths)**, distinct from the separately adjudicated Ship verification | **D4**, **D7a**, **D10** |
> | **D** | **Constitutional workspace containment** — revision 3 permitted `tempfile.TemporaryDirectory()` under OS `%TEMP%`, and described its automatic cleanup as permitted | Permission **withdrawn** on two independent grounds: **Constitution IV** (write outside the workspace/cwd) and **Principle VII** (automatic recursive deletion is an unapproved destructive operation). ALL fixture/scratch/replay workspaces — including pure-classifier tests and the G1 replay — MUST resolve under the **repository-internal, already-git-ignored** root `.autoharness/staging/tmp/`, guarded by a **resolved-realpath containment check**. Deletion only via **D6** | **D7b** |
>
> **Every revision-4 change narrows an authorization, deletes a false or
> unprovable claim, or adds a proof obligation. None widens closure scope, blast
> radius, or claimability, and no evidence was fabricated — every new assertion
> is re-derivable from an immutable git object already in this repository.**

> ## 🔄 REVISION 3 — 2026-09-16 — superseded in part by Revision 4
>
> Revision 3 resolves the **five deduplicated P1 blockers** raised by the
> completed local fix-verification review against the revision-2 package.
> **Option F, the six units, the 1:1 task mapping, INV-1..INV-11, and the
> withdrawal of `TERMINAL_CLOSE`/E2 are all UNCHANGED.**
>
> | P1 | Blocker | Disposition | Where |
> |---|---|---|---|
> | 1 | Unsatisfiable red matrix — A2–A4, A5-live, A9, A10 already return `SAFE_CLOSE` naming the ID on current `main` | Four-class scheme; new **CLASS 4 containment-regression** (must start *green*); genuine red relocated to the observed-status and torn-specific **reason-text** assertions | **D11** |
> | 2 | Classifier fixtures cannot prove engine behaviour; containment rule over-broad | **Disjoint evidence classes** (CLASSIFIER LAW vs ENGINE LAW). *(Revision 4: the engine-evidence formulation `git show --stat e4ca20e5` is **withdrawn as factually wrong** and replaced by path-scoped evidence; the containment re-scope is **withdrawn in full** — see the Revision 4 banner, D7a and D7b.)* | **D7a, D7b** |
> | 3 | Retrospective gate asked post-close records to predict a pre-close, status-sensitive result | Immutable pre-close pin **`358b63b4`**; split into **G1 replay / G2 current-state / G3 engine-effect**. *(Revision 4: G1 and G3 replaced — see D10.)* | **D10** |
> | 4 | `docs/closure/2026-09-14-173-s-165-f-closure.md` still says `BLOCKED` / `satisfied: false` | Recorded as a **historical blocked-phase record**; Stage annotates supersession on Stage-owned surfaces only; **Ship/operator-owned superseding closure record** is a `174-S` readiness prerequisite; unqualified P-001 discharge **withdrawn** | **D8a** |
> | 5 | "byte-for-byte" status contract is unimplementable under `yaml.safe_load` | **Exact parsed-scalar equality**, no post-parse normalization, **non-`str` fails closed**; the `archived ` (unquoted, trailing space) distinctness claim is **withdrawn as factually wrong** | **D1b** |
>
> **Every revision-3 change narrows an authorization, removes an unprovable
> claim, or states an existing limit honestly. None widens closure scope, blast
> radius, or claimability. No fabricated evidence was introduced; where a
> proposition could not be proven, the dependent behaviour is fail-closed and
> the gap is recorded.**

> ## 🔄 REVISION 2 — 2026-09-16 — superseded in part by Revision 3
>
> This decision remains **authoritative and decided**. Revision 2 corrects
> validated local-review blockers found in the revision-1 publication package
> (`e4ca20e5`). Revision 1's Option F adoption, INV numbering, and the
> withdrawal of `TERMINAL_CLOSE`/E2 are **unchanged**. What changed:
>
> | # | Correction | Where |
> |---|---|---|
> | 1 | INV-1/INV-2 reconciled; manifest / closure / allowed / required sets defined explicitly | D1a, INV-1, INV-2, INV-10 |
> | 2 | Inertness requires an **exact canonical** `status: archived`; no case/whitespace normalization may broaden authorization; torn/duplicate IDs fail closed | D1b, INV-6 |
> | 3 | Multi-shipment delivery is **contract-complete but operationally blocked** on an external backlogit prerequisite | INV-11, Option F, trade-off table, R1 |
> | 4 | Destructive rollback is capture → halt → P-005 → explicit operator approval → revalidate → approved rollback | D6 |
> | 5 | `%TEMP%` spike evidence marked **non-compliant and non-authoritative**; P-005 containment violation recorded | F3 preamble, D7 |
> | 6 | `173-S` recorded as **operator-closed and Ship-verified**; P-001 overlap no longer applies | D5, D8 |
>
> **No closure scope is widened by Revision 2.** Every change either narrows an
> authorization, states an existing limit honestly, or records evidence
> provenance.

## Problem Frame

The operator has issued an **architectural correction that supersedes the core
premise** of decision `docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md`
and its reviewed plan `docs/plans/2026-09-15-terminal-shipment-closure-plan.md`.

**The operator directive (binding product constraint, not an option):**

1. The current policy is **defective** because it ties a shipment to a covering
   feature *and all descendants* instead of treating it as a **flat manifest of
   exactly what is delivered**.
2. A shipment manifest **is not a container** and carries **no implicit
   hierarchical closure semantics**.
3. A feature **may be decomposed across multiple shipments**.
4. The **final** shipment for that feature carries the **feature item itself as
   the final manifest entry**, after the tasks delivered across the sequence are
   complete.
5. Items under a feature that are **excluded, removed, descoped, rejected,
   merged into other work, or otherwise absent from a shipment** must **never**
   block the feature record or shipment record from being marked shipped
   *solely because of their ancestry*.
6. **Shipment closure applies only to explicitly listed manifest items plus the
   shipment record.** Hierarchy may remain useful for planning and traceability
   but **must not expand closure scope**.

This deliberation treats (1)–(6) as **binding**. The prior decision's
`TERMINAL_CLOSE` + terminal-descope-exemption design is evaluated *against* that
constraint, not alongside it.

**Presenting symptom (as it stood at revision 1).** Shipment `173-S` was
functionally complete — PR #450 merged (`9cc98c41`), closure PR #451 merged
(`358b63b4`), all 11 manifest members terminal — but remained `active` because
the P-015 classifier, the `shipment-reconcile` safe-close protected-set gate, and
the policy text all expand closure scope through `parent_id` descendants and
there find two **archived, descoped, out-of-manifest** siblings, `165.007-T` and
`165.010-T`.

**Status at revision 2 (2026-09-16).** `173-S` is **no longer active**. The
**operator manually executed an explicitly authorized administrative close**
after a Ship read-only preview; Ship then verified `archived_status: shipped`,
release SHA `9cc98c41`, the exact 11-member closure, byte-identical excluded
siblings, zero active shipments, and a `174-S` `pre_claim` **PASS**. This was an
**operator action, not a Stage close and not a Ship reconcile run** — see D8. It
does **not** retire the defect: the classifier, policy, and skill surfaces still
encode hierarchical closure and will block the **next** shipment of this shape
(`3CA122AC` / `168-S`). This deliberation's scope is therefore **unchanged**.

**Out of scope**: implementation; source/template/schema mutation; shipment
claim/close; PR creation; any mutation of `173-S`; granting P-001 overlap
authority; expanding `174-S` claimability.

## Research Findings

### F1 — The defect reproduces exactly as the operator characterizes it

Running the live classifier against `173-S`'s actual stored manifest:

```text
CLOSE_PATH: ClosePath.SAFE_CLOSE
REASON: feature member '165-F' has descendants outside the manifest:
        ('165.007-T', '165.010-T')
```

The disqualifying predicate in `src/autoharness/gates/shipment_closure.py` is
literally a **hierarchical-closure test**:

```python
missing = tuple(d for d in descendants if d not in manifest_id_set)
if missing:
    return ClosePathDecision(close_path=ClosePath.SAFE_CLOSE, ...)
```

It asks *"is every descendant a manifest member?"* — i.e. it requires the
manifest to be a **closed container over the feature subtree**. That is precisely
the premise the operator declares defective. The same predicate is mirrored in
P-015 precondition 1 and in `shipment-reconcile` Step 0(c).

### F2 — Verified live state of the 173-S closure scope

| Artifact | Location | declared `status` | `archived_status` | `parent_id` | In manifest |
|---|---|---|---|---|---|
| `165-F` | `archive/` | `done` | — | *(root)* | **yes** |
| `165.001-T` … `165.006-T`, `165.008-T`, `165.009-T`, `165.011-T`, `165.012-T` | `archive/` | `done` | — | `165-F` | **yes** |
| `165.007-T` | `archive/` | **`archived`** | `blocked` | `165-F` | **no** (descoped) |
| `165.010-T` | `archive/` | **`archived`** | `blocked` | `165-F` | **no** (merged) |
| `173-S` | `queue/` | `active` | — | — | *(the record)* |

The full `parent_id` walk from `165-F` yields exactly 12 descendants; exactly two
are out-of-manifest, and **both declare `status: archived`** in their own
frontmatter.

### F3 — Spike: what the backlogit 1.10.1 engine *actually* does

> **⚠️ EVIDENCE PROVENANCE — NON-AUTHORITATIVE (added revision 2).**
> The four spike arms below were run in **external `%TEMP%` workspaces outside
> this repository**. That is a **P-005 containment violation** and a
> **destructive-approval violation**: creating and then destroying external
> working directories was neither contained to the workspace nor covered by an
> explicit operator approval, and no evidence survives for independent re-audit.
> Consequently **F3 is recorded as INDICATIVE, NOT AUTHORITATIVE**, and no
> acceptance criterion in the successor plan may rest on F3 alone.
>
> * **Authoritative confidence** for the `173-S` case comes instead from the
>   **operator-performed administrative close** and **Ship's in-workspace
>   post-close verification** (D8): `archived_status: shipped`, SHA `9cc98c41`,
>   exactly 12 changed paths (11 manifest members + the record), both excluded
>   siblings byte-identical, zero active shipments, `174-S` `pre_claim` PASS.
>   **REVISION-4 SCOPE NOTE:** this is **Ship's separately adjudicated
>   in-workspace observation of the close operation**. It is a **distinct**
>   evidence surface from the git-derivable path-scoped historical evidence in
>   **D7a / D10 G3**, and the two MUST NOT be conflated or used to substitute for
>   one another. In particular, Ship's "12 changed paths" observation is about
>   the **close operation**, not about the unfiltered diffstat of the combined
>   publication commit `e4ca20e5`.
> * **REVISION 3 — the "re-derive every F3 claim as a `tests/` fixture"
>   consequence is WITHDRAWN as unsound.** The `tests/` fixtures are
>   **classifier** fixtures: they build synthetic Markdown and call a pure Python
>   function. They never invoke the backlogit engine and therefore **cannot**
>   re-derive `archived_ids`, `returned_ids`, descendant archival, or `parent_id`
>   clearing. Claiming they do would be fabricated evidence. See **D7a** for the
>   disjoint CLASSIFIER-LAW / ENGINE-LAW evidence classes.
> * **REVISION 3 — the one engine proposition that IS authoritatively held** is
>   re-derivable from git alone. **REVISION-4 CORRECTION:** the revision-3
>   formulation *"`git show --stat e4ca20e5` shows the real close touched exactly
>   12 paths"* is **withdrawn as factually wrong** — `e4ca20e5` is the **combined
>   publication commit** (`chore(stage): publish flat-manifest closure package`,
>   **34** changed paths), not a close-only commit. The proposition is held
>   through **path-scoped** before/after evidence between `358b63b4` and
>   `e4ca20e5` (see **D7a**'s corrected block and **D10 G3**): the 11 manifest
>   members modified, the record renamed `queue/ → archive/`, and
>   `165.007-T`/`165.010-T` **byte-identical by matching blob OID**. That — and
>   only that — is what D1b's inertness grant rests on. Arms 2–4 remain
>   **indicative** and are **not** authorized as proof of anything.
> * See D7/D7a/D7b for the recorded violation, the evidence classes, and the
>   correctly scoped containment rule for any future spike.

Four time-boxed Stage spikes (P-016 spike/research exception) ran in **disposable
`%TEMP%` workspaces** — no git branch, no worktree, repository untouched; all
four workspaces destroyed afterwards. Each mirrored a manifest shape exactly and
measured `archived_ids` / `returned_ids` plus per-file SHA-256 before and after.

**Arm 1 — the 173-S shape** (feature member in manifest; one out-of-manifest
sibling truly `status: archived`, `archived_status: blocked`):

```json
{ "archived_ids": ["001.001-T","001.003-T","001-F","001-S"],
  "returned_ids": [] }
```

| Artifact | Result |
|---|---|
| in-manifest members + feature + record | archived (expected) |
| **out-of-manifest, truly `archived` sibling** | **byte-identical** — hash, `updated_at`, `archived_status: blocked`, `parent_id` all preserved |

**The engine already behaves flat here.** `archived_ids` was exactly
`manifest ∪ {record}`. The truly-archived out-of-manifest sibling was *skipped*,
never touched.

**Arm 2 — feature member in manifest, out-of-manifest descendants NOT truly
archived** (one `status: done`, one **live `status: queued`**):

```json
{ "archived_ids": ["001.001-T","001.002-T","001.003-T","001-F","001-S"],
  "returned_ids": [] }
```

Both out-of-manifest descendants were **archived** — including the **live
`queued`** one, which was forced to `done` and archived. **`returned_ids` was
empty**, so the skill's step-2 `returned_ids` guard did **not** fire. This is a
genuinely destructive, out-of-scope cascade that only the *post-mutation*
`archived_ids - allowed_ids` check would catch.

**Arm 3 / Arm 4 — partial-feature shape, no feature member in manifest**
(manifest `[001.001-T]`; live parent `001-F` and live sibling `001.002-T` both
out-of-manifest), reproduced twice in independent clean workspaces:

```json
{ "archived_ids": ["001.001-T","001-S"],
  "returned_ids": ["001.002-T"] }
```

| Artifact | Result |
|---|---|
| live parent feature `001-F` (out-of-manifest) | **untouched** — engine never walks *up* to parents |
| in-manifest `001.001-T` | archived, `parent_id` **preserved** |
| live out-of-manifest sibling `001.002-T` | returned — **but its `parent_id` was silently CLEARED** (orphaned) |

**Synthesis of F3 (the governing empirical law).** The engine's blast radius is
**not** a function of hierarchy per se; it is a function of **the presence of a
feature member in the manifest** and **the declared status of out-of-manifest
descendants**:

| Manifest shape | Out-of-manifest descendant state | Engine effect on it |
|---|---|---|
| contains a feature member | declared `status: archived` | **inert** — skipped, byte-identical |
| contains a feature member | `done`, or live (`queued`/`active`) | **archived** (destructive; `returned_ids` empty) |
| no feature member | live | **returned, `parent_id` cleared** (orphaned) |
| any | *parent/ancestor* of a manifest item | untouched (no upward walk) |

### F4 — `move --status shipped` is refused; `ShipShipment` is the only path to provenance

Reproduced independently (2B42392E):

```text
$ backlogit move 001-S --status shipped
move shipment 001-S to shipped via generic path:
backlogit: shipment must be shipped via ShipShipment, not a direct status update
EXITCODE=9
```

`backlogit shipment ship` yields exactly `status: archived` +
`archived_status: shipped` — the precise provenance safe-close Step 8 demands.
There is **no non-cascading path to `shipped` in 1.10.1**.

### F5 — The autoharness overlay is *stricter* than the engine, and in the wrong dimension

Arm 1 proves the engine is already flat for truly-archived out-of-manifest
descendants. `173-S` is therefore blocked **not by the engine**, but by an
autoharness-invented hierarchical-closure precondition that the engine itself
does not enforce. Conversely, Arm 2 proves the overlay's *`returned_ids`* guard
is **insufficient** where the engine genuinely is destructive.

So the existing design is simultaneously **too strict** (blocks 173-S on inert
artifacts) and **too weak** (relies on a guard that does not fire on the real
destructive case). Both errors share one root cause: the overlay reasons about
**hierarchy membership** when the safety-relevant question is **mutability**.

### F6 — Why the superseded TERMINAL_CLOSE design is structurally incompatible

The prior decision's E1 preconditions cannot be reconciled with the directive:

* **E1 precondition 2** — "*every descendant, at every depth, of every manifest
  feature member … is likewise already archived and terminal, whether or not it
  is a manifest member*" — is hierarchical closure **restated**, merely with a
  terminality test substituted for a membership test. It still expands closure
  scope through ancestry, violating directive (6).
* **E1 precondition 3** — "*the only artifact in the closure scope still live is
  the shipment record*" — makes **multi-shipment feature delivery unreachable**.
  When feature `F` is split across `S1..Sn`, at `S1`'s closure the tasks destined
  for `S2..Sn` are live descendants of `F`, so `TERMINAL_CLOSE` can never fire.
  This directly contradicts directive (3).
* **E2**'s exemption requires a sibling to carry "*a verified P-021 C1
  descope/merge disposition*". Directive (5) says excluded items must never block
  closure **solely because of their ancestry** — it grants no license to demand a
  disposition note as the price of exclusion. E2 replaces an ancestry gate with a
  *paperwork* gate over the same out-of-scope artifacts.

E1/E2 are therefore not merely sub-optimal under the new premise; they encode the
superseded premise. They must be withdrawn, not tuned.

### F7 — Class scope is unchanged

Stash `3CA122AC` records the identical failure for `168-S` / `160-F` /
`160.019-T`. P-015 forbids narrowing any exception "to any particular feature ID,
shipment ID, or manifest shape". The remedy below is defined purely by
**declared status and manifest membership**, never by ID.

## Options Evaluated

### Option F (RECOMMENDED): Flat manifest + engine-inertness containment gate

Redefine closure scope as flat, and demote the descendant walk from a
*scope-definition* device to a *blast-radius containment* check over the engine.

* Closure scope is **exactly** `items(S) ∪ {S}` (plus engine-forced linked
  deliberations of manifest feature members).
* The cascade op is permitted **only when every out-of-manifest artifact the
  engine can reach is provably engine-inert** — i.e. declares `status: archived`.
* Out-of-manifest artifacts require **no** manifest membership, **no** disposition
  note, and **no** particular `archived_status`.
* **Pros**: implements the directive exactly; unblocks `173-S` with *no* new
  verdict; strictly **safer** than today (Arm 2's destructive case is caught
  *before* mutation rather than after); **states** multi-shipment feature
  delivery normatively; purely shape-based; eliminates E1/E2 machinery entirely.
* **Cons**: touches classifier + policy + skill + mirrors (elevated blast radius,
  P-006 hardening mandatory); does not by itself fix the partial-shipment record
  transition (see Option H / residual R1) — and **that gap is precisely what
  keeps multi-shipment delivery operationally unreachable**, see INV-11.
* **Effort**: medium. **Fit**: best.

**Honest limit on the multi-shipment claim (revision 2).** Option F makes split
delivery **contract-complete**: INV-4/INV-5 are stated normatively and no
*ancestry* rule blocks it any more. It does **not** make split delivery
**operationally complete**. An intermediate shipment `S1..Sn-1` carries **no**
feature member, so it can never qualify for `CASCADE`; it is a genuine
`SAFE_CLOSE` shipment, and under backlogit 1.10.1 there is **no safe path** to
`archived_status: shipped` for that shape (F4 + Arms 3–4). Such a closure halts
at `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`. This is recorded as **INV-11** and
tracked as an **external runtime prerequisite** (Option H / R1), not as a
capability this decision delivers.

**Is this "hierarchy closure under another name"?** No — and the difference is
*observable*, which is the test that matters:

| Out-of-manifest descendant | Hierarchical closure (old) | Inertness containment (new) |
|---|---|---|
| archived, descoped (`165.007-T`) | **disqualifies** | **passes** (inert) |
| archived, no disposition note | disqualifies (and fails E2) | **passes** (inert) |
| `done`, not archived | disqualifies | disqualifies — *because the engine would archive it* |
| live `queued` | disqualifies | disqualifies — *because the engine would destroy it* |
| live, in a later shipment `S2` of the same feature | disqualifies → blocks split delivery | disqualifies **this cascade only**; `S1` closes via safe-close, `Sn` carries the feature |

The old predicate asks *"is the subtree inside the manifest?"* (scope). The new
predicate asks *"can this tool mutate anything outside the manifest?"* (blast
radius). The first grows closure scope; the second constrains an instrument. The
row that proves they are different is row 1 — the exact `173-S` case.

### Option G: Pure flat manifest with no descendant inspection at all

Take directive (6) maximally literally: never enumerate descendants; always
invoke the cascade; rely solely on the post-hoc `archived_ids - allowed_ids` gate.

* **Pros**: simplest possible reading; zero hierarchy code.
* **Cons**: **empirically unsafe**. Arm 2 shows the engine archives live
  out-of-manifest tasks and reports `returned_ids: []`; Arm 3/4 show it silently
  clears `parent_id` on returned siblings. A post-mutation check halts *after*
  the corruption, and P-015's own violation action then demands a destructive
  `git restore`. This would make the policy *cause* the corruption it exists to
  prevent.
* **Fit**: rejected — the directive constrains **closure scope**, not the
  agent's duty to avoid destroying out-of-scope artifacts. Declining to mutate
  what is outside the manifest is the directive's *enforcement*, not a violation
  of it.

### Option H: Upstream backlogit change for a non-cascading `shipped` transition

Request `shipment ship --no-cascade`, or permit a direct status update.

* **Pros**: the only clean fix for the partial-shipment record transition (F4);
  would let a flat manifest close with literally zero engine scope expansion;
  **is the sole unblocker for operational multi-shipment delivery** (INV-11).
* **Cons**: external Go project; unbounded timeline; cannot unblock `173-S` now;
  **cannot be implemented in this repository** — `backlogit` is a third-party
  binary dependency, not autoharness source.
* **Fit**: **required external/runtime prerequisite**, not the critical path.
  Recorded as R1 and tracked by a durable **active** P-021 follow-up that
  explicitly BLOCKS the operational multi-shipment capability (see D9).

### Option I: Reframe 166-F in place vs. supersede with a new feature/shipment

* **Reframe in place** (`166-F`, `166.001-T`..`166.006-T`, `174-S` retained):
  preserves the **operator-authorized `dag-root` label already on `174-S`**;
  requires no new authorization; keeps one traceable lineage.
* **Supersede with a new `NNN-F`/`NNN-S`**: would require a **new** operator
  `dag-root` authorization — i.e. it would *expand* operator-owned authority,
  which the operator explicitly forbade in this session.
* **Fit**: **reframe in place**, with explicit supersession markers on the old
  decision and plan.

### Option J: Retain TERMINAL_CLOSE as a third verdict alongside the flat model

* **Cons**: `TERMINAL_CLOSE`'s preconditions are unreachable under Option F
  (anything it would accept, Option F already accepts via inertness), so it is
  dead code carrying a superseded premise into the codebase.
* **Fit**: rejected as redundant and premise-contaminating.

## Trade-off Comparison

| Criterion | F (flat + inertness) | G (no inspection) | H (upstream) | J (keep TERMINAL_CLOSE) |
|---|---|---|---|---|
| Honors operator directive (flat manifest) | **Yes** | Yes (literal) | N/A | **No** |
| States multi-shipment delivery normatively (contract) | **Yes** | Yes | N/A | **No** |
| Multi-shipment delivery **operationally usable** | **No — blocked by R1/INV-11** | **No — same block** | **Yes (this is the unblocker)** | **No** |
| Excluded items never block on ancestry | **Yes** | Yes | N/A | Only with a disposition note |
| Unblocks `173-S`-shaped closures (CASCADE path) | **Yes** | Yes (unsafely) | No | Yes |
| Prevents Arm-2 destructive cascade | **Yes (pre-mutation)** | **No** | Yes | Yes |
| Prevents Arm-3/4 `parent_id` orphaning | **Yes** | **No** | Yes | Partially |
| Adds new closure verdicts | No | No | No | Yes |
| Self-owned / bounded timeline | Yes | Yes | **No** | Yes |
| Generalizes to `168-S` / the class | Yes | Yes | Yes | Yes |

## Decision

**Adopt Option F (flat manifest + engine-inertness containment), reframing
`166-F`/`174-S` in place per Option I, and record Option H as required follow-up
R1. The prior decision's `TERMINAL_CLOSE` (E1) and terminal-descope exemption
(E2) are WITHDRAWN.**

### D1 — Closure-scope invariants (normative)

Let `S` be a shipment with declared manifest `items(S)`.

#### D1a — Scope vocabulary (REVISION 2, normative and exhaustive; `required_ids(S)` CORRECTED in REVISION 5)

Four sets are defined, and **they are not interchangeable**. Revision 1 stated
INV-1 with a linked-deliberation extension and INV-2 with a bare `iff`, which
were mutually inconsistent and left INV-10's `validated_linked_deliberations`
term undefined. The four sets below replace that reading; no set is widened
relative to revision 1's intent.

> **⚠️ REVISION 5 CORRECTION.** The `required_ids(S)` row below previously read
> `{ x ∈ closure_scope(S) : x is not already truly archived in the pre-close
> snapshot }`, and the paragraph following the table claimed
> `validated_linked_deliberations(S)` "never enters `required_ids(S)`". Both
> statements are **withdrawn**: they contradicted the already-established,
> tested, and shipped 155-S/PR #407 correction (the shipment record and every
> qualifying feature member are required *unconditionally*, regardless of
> their own pre-close declared status) and were never true of the actual
> implementation, which already applied the corrected rule in
> `.github/policies/workflow-policies.md` item 7,
> `.github/skills/shipment-reconcile/SKILL.md`'s Cascade Close Sub-Procedure,
> and `src/autoharness/gates/shipment_closure.py`. The row and paragraph are
> restated below to match that already-shipped behavior; this is a
> documentation reconciliation only and changes no runtime behavior.

| Set | Definition | Role |
|---|---|---|
| **`manifest_scope(S)`** | exactly `items(S)` | what is **delivered**. Membership is declared, explicit, and exhaustive. |
| **`closure_scope(S)`** | `items(S) ∪ {S}` | what this closure **is about** and the only artifacts it may **deliberately** transition. |
| **`allowed_ids(S)`** | `closure_scope(S) ∪ validated_linked_deliberations(S)` | the **maximal permitted postcondition set** — the only IDs that MAY appear in `archived_ids`. |
| **`required_ids(S)`** (REVISION 5) | `{ S } ∪ { qualifying feature members of S }` (both **unconditionally** required regardless of their own pre-close declared status) `∪ { x ∈ allowed_ids(S) : x is not already truly `archived` in the pre-close snapshot }` (every other `allowed_ids(S)` member — a manifest task item, or a qualifying feature member's validated linked deliberation — required only when not already truly archived) | the **minimal mandatory postcondition set** — every member MUST appear in `archived_ids`. |

`validated_linked_deliberations(S)` is admitted **only** under all four of:

1. the record is a **deliberation/decision artifact**, never a backlog work item
   (never a feature, task, subtask, spike, or shipment);
2. it is reached **solely** through the engine's own linked-deliberation
   expansion from a manifest **feature** member — never through `parent_id`,
   never through ancestry, never through a sibling walk;
3. it is present in the **Step 0(b) pre-close snapshot**, so it is enumerable and
   hash-pinned *before* any mutation; and
4. it is **narrowly validated** per record, individually, at that snapshot — an
   unvalidatable or newly-appearing linked deliberation fails closed.

`validated_linked_deliberations(S)` **never** enters `manifest_scope(S)`,
**never** enters `closure_scope(S)`, and **never** makes any out-of-manifest
*work item* closable. **(REVISION 5 CORRECTION: it DOES enter `required_ids(S)`**
whenever it is not already truly archived in the pre-close snapshot, exactly
like any other `allowed_ids(S)` member that is not the shipment record or a
qualifying feature member — the prior "never enters `required_ids(S)`" claim
above is withdrawn as false; this is a postcondition-check participation only
and widens `allowed_ids(S)` by zero *work items*.) It exists only to keep
`allowed_ids(S)` honest about an engine-forced side effect that would otherwise
trip the postcondition gate. It is therefore an **allowed-set widening of
exactly zero work items**.

#### D1b — Inertness is an exact canonical match (REVISION 2; comparison domain CORRECTED in REVISION 3)

> **⚠️ REVISION 3 CORRECTION — the revision-2 "byte-for-byte" formulation was
> UNIMPLEMENTABLE and is WITHDRAWN.** Every backlog record reaches this code
> through `gates.topology._frontmatter`, which parses the frontmatter with
> `yaml.safe_load`. A YAML load **erases lexical form**: quoting style, plain
> vs. quoted scalars, and trailing whitespace on a plain scalar are all gone
> before any comparison can happen. No predicate downstream of `_frontmatter`
> can observe bytes, so a "byte-for-byte" contract could never have been
> satisfied, and the specific claim that unquoted `status: archived ` is a
> distinct non-inert value was **factually wrong** — YAML resolves it to
> exactly `"archived"`.

Engine-inertness is decided by comparing the artifact's **parsed `status`
scalar** — the value `yaml.safe_load` produces for the record's own frontmatter
`status:` key — for **exact equality against the canonical `str` `"archived"`**.

Normative rules:

1. **Exact parsed-scalar equality.** The comparison is `status == "archived"`.
2. **No post-parse normalization for the purpose of granting inertness.** No
   `.lower()`, no `.casefold()`, no `.strip()`, no synonym set, no alias table,
   and no coercion may be applied to the parsed value before the comparison.
   `"Archived"`, `"ARCHIVED"`, and the **YAML-quoted** `status: " archived "`
   (which *does* survive parsing as `" archived "`) are **NOT inert** and force
   `SAFE_CLOSE`.
3. **Non-`str` fails closed.** A `status` that parses to anything other than a
   `str` — a bool (`status: yes` → `True`), an int, `None` (`status:` or
   `status: ~`), a list, or a mapping — is **NOT inert** and forces
   `SAFE_CLOSE`. It is never coerced with `str()`.
4. **Absent fails closed.** A record declaring no `status` key at all is **NOT
   inert** (this is what keeps the entire pre-existing negative fixture suite
   valid — see D3).
5. **Malformed / torn / duplicate records fail closed** unchanged, per D1c and
   the existing `_frontmatter` fail-closed contract.

**Accepted, documented limitation (REVISION 3, stated honestly rather than
papered over).** Because the comparison happens *after* YAML parsing, forms
that are lexically distinct but **YAML-equivalent** collapse together and ARE
treated as inert: unquoted `status: archived` with trailing spaces, and
`status: "archived"`, both parse to `"archived"`. This is **deliberate and
correct**, not a concession: the backlogit engine also reads these records
through a YAML parser, so the **parsed scalar is the domain in which autoharness
and the engine actually agree**. A byte-level comparison would make autoharness
disagree with the engine's own view of the record and reject records the engine
genuinely skips — a fail-safe but incorrect divergence.

**Rejected alternative (REVISION 3):** authorize a raw-scalar *lexical* parser
that reads the `status:` line pre-YAML and compares bytes. Rejected — it adds a
hand-rolled parser surface outside the declared `freeze-scope` boundary, it
duplicates and can drift from `_frontmatter`, and it deliberately diverges from
the engine's parse semantics for no measured safety gain.

#### D1c — Torn and duplicate identity fails closed (REVISION 2)

The queue+archive scan that builds the children/status index MUST be a **full
scan of both roots** and MUST **fail closed** (`SAFE_CLOSE`) when any ID resolves
to more than one record — whether the duplication is two records in the same
root, a torn record present in **both** `queue/` and `archive/`, or any other
non-unique resolution. This applies to **every** record encountered by the scan,
explicitly **including out-of-manifest descendants**, because a torn
out-of-manifest descendant has an **ambiguous declared status** and therefore can
never satisfy D1b's exact-match inertness test. A partial, aborted, or
ambiguous scan may **never** yield `CASCADE`.

#### D1d — Invariants

* **INV-1 (Flat closure scope).** `closure_scope(S) = items(S) ∪ {S}`.
  **Ancestry never adds a member.** Linked deliberations do **not** extend
  `closure_scope(S)`; they are accounted for only in `allowed_ids(S)` per D1a.
  No artifact outside `allowed_ids(S)` may be created, modified, moved, or
  deleted by closing `S`.
* **INV-2 (Membership is explicit and exhaustive).** An artifact is a **manifest
  member** — i.e. in `manifest_scope(S)` — **iff** its ID appears in `items(S)`.
  Absence from `items(S)` is a complete and sufficient statement that the
  artifact is **not** part of this delivery. INV-2 governs **membership**, not
  the postcondition sets; the engine-forced linked deliberations of D1a are
  **not** members and INV-2's `iff` is not weakened by them.
* **INV-3 (Exclusion is never a gate).** An artifact under a feature but absent
  from `items(S)` may be in **any** state — `queued`, `active`, `blocked`,
  `archived`, descoped, merged, rejected, or absent from the workspace entirely —
  and **MUST NOT** block `S`, or the feature record, from reaching a terminal
  state *on the ground of ancestry*. No disposition note, no `archived_status`
  value, and no provenance is required of it.
* **INV-4 (Multi-shipment feature delivery).** A feature `F` MAY be delivered
  across an ordered sequence `S1 … Sn`. `S1..Sn-1` carry **no** feature member.
  **Exactly one** shipment — the final `Sn` — carries `F` itself as a manifest
  entry, placed **last** in `items(Sn)`. *(Contract-level; see INV-11 for the
  operational prerequisite.)*
* **INV-5 (Feature terminality precondition).** `Sn` may carry `F` only when every
  task **actually delivered** by `S1..Sn` is terminal. Tasks excluded from every
  manifest in the sequence are **not** subject to this precondition (INV-3).
* **INV-6 (Engine-inertness containment gate).** The cascade op MAY be used only
  when **every** artifact reachable by the engine's own scope expansion from
  `items(S)` but **outside** `closure_scope(S)` declares, in its own frontmatter
  and as an **exact canonical match** per D1b, `status: archived` (read from the
  record, never inferred from `queue/`/`archive/` location, never normalized to
  broaden the match). Any such artifact that is live, merely `done`, carries a
  non-canonical status variant, or has **torn/duplicate identity** per D1c
  **forbids the cascade** and forces safe-close. This is a **blast-radius
  constraint on an instrument**, not a definition of closure scope — it never
  adds a member to `closure_scope(S)` or `manifest_scope(S)`, and never requires
  an out-of-manifest artifact to join the manifest.
* **INV-7 (Baseline invariance replaces baseline presence).** Safe-close's
  protected-set gate is redefined: record each out-of-manifest artifact's
  **baseline location and content hash**, and require that **nothing outside
  `closure_scope(S)` changes** during the run. A protected artifact that was
  *already* archived, descoped, or missing **at baseline** is recorded as baseline
  state and is **NOT** a halt — it carries no signal about *this* run.
* **INV-8 (Manifest ordering is an assembly convention, never a closure gate).**
  INV-4's "feature last" ordering is enforced by **Stage at shipment assembly**.
  Ship MUST NOT evaluate manifest ordering as a closure precondition. *(Required
  for backward compatibility — see D3.)*
* **INV-9 (DAG orthogonality).** Shipment sequencing (`dag-root`, declared
  predecessors, `pipeline-topology`) is **orthogonal** to closure scope. INV-4
  creates a shipment-level ordering `S1 → … → Sn`; it does **not** create or
  imply any dependency edge, and closure never consults the DAG.
* **INV-10 (Postconditions).** After closing `S`, using the D1a set vocabulary:
  `archived_ids ⊆ allowed_ids(S)`; `required_ids(S) ⊆ archived_ids`; every
  artifact **outside `allowed_ids(S)`** is **byte-identical** to baseline
  (including `parent_id`); and `S` declares `status: archived` +
  `archived_status: shipped`.
  *Worked example (`173-S`, confirmed by the operator close):* its 11 manifest
  members declared `status: done` — **not** truly `archived` — so all 11 are in
  `required_ids(173-S)` and MUST appear in `archived_ids`, together with the
  record itself: **12 IDs**. Only records that are **truly `status: archived`**
  in the pre-close snapshot are skipped by the engine and therefore excluded from
  `required_ids`.
* **INV-11 (Multi-shipment delivery has an external runtime prerequisite)
  (REVISION 2).** INV-4/INV-5 are **contract-complete but not operationally
  complete** under backlogit 1.10.1. An intermediate shipment `S1..Sn-1` carries
  no feature member, therefore cannot qualify for `CASCADE`, therefore is a
  genuine `SAFE_CLOSE` shipment — and F4 plus Arms 3–4 establish that **no safe
  path to `archived_status: shipped` exists for that shape**. Closing such a
  shipment MUST halt fail-closed with
  `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`; the cascade MUST NOT be
  substituted. Split delivery becomes operationally usable **only** when the
  external prerequisite (R1 / Option H — a genuine non-cascading record
  transition in the backlogit engine) lands. **No autoharness-side change in
  scope of `166-F` can satisfy INV-11**, and no acceptance criterion of `166-F`
  may claim end-to-end split delivery works.

### D2 — What changes, concretely

1. **Classifier** (`src/autoharness/gates/shipment_closure.py`): replace the
   `descendants ⊆ manifest` coverage predicate with the INV-6 inertness predicate,
   compared as an **exact canonical match** (D1b) with **no normalization applied
   for the purpose of granting inertness**. The descendant walk is **retained** —
   it is the only way to compute the engine's reachable set — but its verdict
   changes from *"must be in the manifest"* to *"must be engine-inert"*. The
   full queue+archive index build **fails closed on torn/duplicate IDs anywhere,
   including out-of-manifest descendants** (D1c). Fail-closed default remains
   `SAFE_CLOSE`.
2. **P-015** (`.github/policies/workflow-policies.md` + `templates/` mirror):
   restate the exception in flat-manifest terms; add the D1a set vocabulary and
   INV-1..INV-11; record the withdrawal of the hierarchical-closure preconditions
   with a supersession note; state INV-11's external prerequisite explicitly so
   no reader infers that split delivery is operationally available.
3. **`shipment-reconcile` skill** (both mirrors): Step 0(c) adopts INV-6;
   Step 2/3 adopt INV-7; the Arm-2 finding is recorded as the reason the
   `returned_ids` guard is **not** sufficient on its own.
4. **No `TERMINAL_CLOSE` verdict is added.** The classifier keeps exactly two
   verdicts.

### D3 — Migration and backward compatibility

* **Existing manifests are unaffected in membership.** No manifest is rewritten.
* **Ordering**: every historical manifest (including `173-S`) lists the covering
  feature **first**, not last. INV-8 therefore makes ordering non-normative at
  closure, so **no historical manifest is invalidated** and `173-S` need not be
  touched. INV-4's "feature last" applies to **newly assembled** shipments only.
* **`173-S` closure path (RESOLVED 2026-09-16 by operator action).** Out-of-manifest
  descendants `{165.007-T, 165.010-T}` both declare an exact canonical
  `status: archived` → **inert** → INV-6 satisfied. The closure was **executed by
  the operator as an explicitly authorized administrative close** after a Ship
  read-only preview, and **verified in-workspace by Ship**: `173-S` now declares
  `status: archived` + `archived_status: shipped` with `commit: 9cc98c41`;
  `archived_ids` covered exactly the 11 manifest members + `173-S` = **12 paths**;
  `165.007-T` and `165.010-T` are **byte-identical** (`archived_status: blocked`,
  no `commit:` stamp added); zero shipments remain active; `174-S` `pre_claim`
  **PASSES**. This confirms the INV-10 worked example above. It was **not** a
  Stage close and **not** a Ship `shipment-reconcile` run, and it does **not**
  discharge this decision: the three defective surfaces are unchanged and the
  next same-shaped closure (`168-S`) is still blocked.
* **`168-S` / `160-F`** (`3CA122AC`): classified at its own closure by the same
  shape-based rule; used as a **control fixture**, never assumed.

### D4 — Read-only dry-run obligation

A mandatory, **read-only** dry-run must prove, without mutating anything, that
the classifier's new verdict is correct and containment-clean on real workspace
shapes. It computes the classifier verdict, the engine-reachable set, the
predicted `archived_ids`/`required_ids`/`allowed_ids`, and a pre-image hash
manifest of every out-of-manifest artifact. It performs **no** writes.

> **⚠️ REVISION 4 — D4's `173-S` BULLET IS SUPERSEDED AND ITS MUST-LANGUAGE IS
> WITHDRAWN.** The revision-2 bullet reproduced below required *"the dry-run
> over its **recorded** manifest shape"* — i.e. a classification performed over
> the **current, recorded** records — to *"reproduce `CASCADE` with the
> `archived_ids` set the operator close actually produced (12 IDs)"*. **D10
> (revision 3) already established that this is unsatisfiable** over current
> state, and D10's **G2** row explicitly **withdraws** the 12-ID expectation for
> current-state classification. The two sections therefore contradicted each
> other: D4 still said *must reproduce 12*, while D10 said *asserting 12 here is
> INVALID*. **D10 governs. D4's `173-S` bullet is retained below as
> HISTORICAL PROVENANCE ONLY and MUST NOT be executed, cited, or used as an
> acceptance criterion.** The operative retrospective obligation is **exactly**
> D10's three pinned gates — **G1** (replay over the immutable pre-close pin
> `358b63b4`), **G2** (current-state classification, `required_ids` = ∅), and
> **G3** (path-scoped historical engine effect between `358b63b4` and
> `e4ca20e5`). Any surface still demanding a current recorded-manifest dry-run
> reproduce the pre-close 12-ID result is stale and must be repointed at
> G1/G2/G3.

* ~~**`173-S` is now a RETROSPECTIVE REGRESSION FIXTURE, not a live gate**
  (revision 2). Its closure already happened by operator action (D8), so the
  dry-run over its *recorded* manifest shape must reproduce `CASCADE` with the
  `archived_ids` set the operator close actually produced (12 IDs) and with
  `165.007-T`/`165.010-T` absent from every predicted set. A divergence is a
  **STOP, DO-NOT-SHIP** condition, because it would mean the new classifier
  disagrees with a verified real closure.~~ **WITHDRAWN IN REVISION 4 —
  superseded by D10 G1/G2/G3 (see the banner above). Historical text only.**
* **`173-S` remains a RETROSPECTIVE REGRESSION FIXTURE, not a live gate**, but
  the fixture is evaluated **only** through D10's G1/G2/G3, each against its own
  pinned immutable source. A divergence in **G1** (the replay over `358b63b4`)
  is the **STOP, DO-NOT-SHIP** condition; **G2** asserts `required_ids` = ∅ over
  current state; **G3** is path-scoped historical evidence, not a re-run.
* **`168-S` remains the LIVE forward-looking control.** A dry-run returning
  anything other than the containment-correct verdict is a **STOP,
  DO-NOT-SHIP** condition.
* Dry-runs may **not** mutate `173-S` or its excluded siblings; their archived
  records are immutable to this work.

### D5 — Authority boundaries (updated revision 2; qualified revision 3)

* **No P-001 overlap authority is granted or implied by Stage.** The overlap it
  addressed **no longer exists in fact**: `173-S` is archived, so `174-S`'s claim
  condition 5 is discharged **by state**, not by a Stage grant. Stage grants
  nothing here and never did. **Revision-3 qualification (see D8a):** "discharged
  by state" describes the *factual* position only. It is **not** discharged *of
  record* while the only closure artifact naming `173-S` still declares
  `closure_status: BLOCKED`. No surface may declare P-001 discharged without that
  qualification, and the superseding closure record remains an outstanding
  **Ship/operator-owned** claim-readiness prerequisite.
* **No bootstrap grant is issued.** `174-S` retains the *existing*
  operator-authorized `dag-root` label and its empty `dependencies` field. This
  deliberation does **not** prove the root itself must change, so it is preserved
  exactly as authorized.
* **`173-S` is not altered** by this deliberation or its plan. Its archived
  record is **immutable** to Stage; revision 2 records its state, it does not
  change it.

### D6 — Destructive rollback is approval-gated (REVISION 2, NON-NEGOTIABLE)

Every rollback instruction in this decision, its plan, and its tasks — `git
restore`, `git revert`, `git checkout --`, `git reset`, file deletion, or any
other reversal of a mutation — MUST follow this exact sequence and MUST NOT be
expressed as automatic, immediate, or notification-only:

1. **CAPTURE EVIDENCE** — the observed deviation, the offending IDs, the
   `archived_ids`/`returned_ids` actually returned, and a `git status --short` +
   per-path hash diff against the recorded baseline.
2. **HALT** — perform **no** further mutation of any kind.
3. **EMIT P-005** — log the process-deviation telemetry event with the captured
   evidence attached.
4. **REQUEST EXPLICIT OPERATOR APPROVAL** — state the exact paths proposed for
   rollback and the exact command. Operator *notification* is **not** approval.
5. **REVALIDATE AFTER APPROVAL** — immediately before executing, re-read the
   working tree and confirm the exact paths and their exact current state still
   match what was approved. Any drift returns to step 1.
6. **EXECUTE ONLY THE APPROVED ROLLBACK** — restricted to the approved paths, no
   broader command, no retry on a different scope.

Automatic revert, "revert the unit's commit" as an unqualified instruction, and
"rollback with operator notification" are **prohibited formulations** and are
replaced wherever they appear. This restates Constitution Principle VII.

### D7 — Spike containment violation (REVISION 2, recorded; SCOPE CORRECTED in REVISION 3)

The four F3 spike arms ran in **external `%TEMP%` workspaces**, outside this
repository. Recorded as a **P-005 process deviation** on two counts:
**containment** (work performed outside the workspace boundary, leaving no
auditable artifact) and **destructive approval** (external workspaces were
created and destroyed without an explicit operator approval for the destructive
step). Consequences, binding on the successor plan:

* F3 is **indicative, not authoritative**. No acceptance criterion may cite F3 as
  its sole evidence.
* **Future spikes AND all scratch/fixture workspaces MUST be contained** to the
  repository-internal, git-ignored canonical root defined in **D7b (revision
  4)** — `<repo_root>/.autoharness/staging/tmp/` — under an explicit,
  time-boxed P-016 declaration where an engine is involved, with **all** cleanup
  routed through D6. **Revision 4 note:** the revision-3 carve-out permitting an
  OS-`%TEMP%` scratch directory for hermetic, self-cleaning unit tests is
  **withdrawn in full**; see D7b.

#### D7a — Evidence classes are DISJOINT (REVISION 3, correcting an unsound claim)

> **⚠️ The revision-2 consequence "every engine-behavior claim MUST be
> re-derived in-workspace as a hermetic checked-in fixture under `tests/`" was
> UNSOUND and is WITHDRAWN as written.** The fixtures it referred to are
> **classifier** fixtures: they construct synthetic Markdown records and call
> `classify_shipment_close_path`, a pure Python function. They never invoke the
> backlogit Go engine, so they **cannot** re-derive `returned_ids`, descendant
> archival, or `parent_id` clearing. Asserting that they do would have been a
> fabricated-evidence claim.

Two disjoint evidence classes are hereby defined. No artifact may cite evidence
from one class as proof of a proposition in the other.

| Class | Proposition kind | Authoritative evidence | Provable by this plan? |
|---|---|---|---|
| **CLASSIFIER LAW** | What `classify_shipment_close_path` must return for a given record shape | Hermetic, self-contained, checked-in fixtures under `tests/` | **YES — fully** |
| **ENGINE LAW** | What backlogit 1.10.1 `archiveItems()` actually mutates, returns, and skips | Only a real, observed, in-repository engine execution | **NO — not by any fixture in this plan** |

**The only authoritative ENGINE-LAW evidence currently held** is the operator's
real close of `173-S`, which is in-repository, immutable, and independently
re-derivable from git.

> **⚠️ REVISION 4 — THE `git show --stat e4ca20e5` FORMULATION IS WITHDRAWN AS
> FACTUALLY WRONG.** The revision-3 text below said *"`git show --stat
> e4ca20e5` — the close changed **exactly 12 paths**"*. **That is false.**
> `e4ca20e5` is **`chore(stage): publish flat-manifest closure package`** — a
> **COMBINED PUBLICATION COMMIT** whose unfiltered diffstat contains **34
> changed paths**: the 12 close-effect paths **plus** the entire Stage
> publication package (`166-F` and its six task records, `174-S`, both
> deliberations, both plans, four memory files, stash/checkpoint/log files).
> Calling it a *close-only* commit, or asserting that its unfiltered diffstat
> contains exactly 12 paths, is an unsupported claim and is **withdrawn**. The
> engine evidence is real, but it must be extracted **path-scoped** — see the
> corrected formulation immediately below and D10's **G3**.

**Corrected engine-law evidence (revision 4) — explicit, path-scoped before/after
between the immutable pre-close tree `358b63b4` and the publication tree
`e4ca20e5`:**

```text
# (a) the 11 manifest members — expect 11 MODIFIED, no add, no delete, no rename
git diff --stat 358b63b4 e4ca20e5 -- \
  .backlogit/archive/165-F.md .backlogit/archive/165.001-T.md \
  .backlogit/archive/165.002-T.md .backlogit/archive/165.003-T.md \
  .backlogit/archive/165.004-T.md .backlogit/archive/165.005-T.md \
  .backlogit/archive/165.006-T.md .backlogit/archive/165.008-T.md \
  .backlogit/archive/165.009-T.md .backlogit/archive/165.011-T.md \
  .backlogit/archive/165.012-T.md
#   -> 11 files changed

# (b) the shipment record — expect EXACTLY ONE entry, a RENAME + modify
git diff --stat -M --find-renames 358b63b4 e4ca20e5 -- \
  .backlogit/queue/173-S.md .backlogit/archive/173-S.md
#   -> .backlogit/{queue => archive}/173-S.md | 1 file changed

# (c) the two EXCLUDED out-of-manifest siblings — expect EMPTY output
git diff --stat 358b63b4 e4ca20e5 -- \
  .backlogit/archive/165.007-T.md .backlogit/archive/165.010-T.md
#   -> (no output)

# (d) blob identity for (c) — the positive, non-vacuous form of the same fact
git rev-parse 358b63b4:.backlogit/archive/165.007-T.md   # 544c2377b38e9ba2df123f5b8d9bf359dacb89ea
git rev-parse e4ca20e5:.backlogit/archive/165.007-T.md   # 544c2377b38e9ba2df123f5b8d9bf359dacb89ea
git rev-parse 358b63b4:.backlogit/archive/165.010-T.md   # 609ad8bc7839fca8b5273d777a6acdc590aacb6f
git rev-parse e4ca20e5:.backlogit/archive/165.010-T.md   # 609ad8bc7839fca8b5273d777a6acdc590aacb6f
```

(a) + (b) = the **12 close-effect paths**, stated as a **path-scoped subset** of
`e4ca20e5`, never as its unfiltered diffstat. (c) + (d) show that
`165.007-T`/`165.010-T` — both of which declare `status: archived` at
`358b63b4` and are `parent_id: 165-F` descendants — are **byte-identical across
the close**, proved by matching blob object IDs rather than by mere absence from
a diff listing.

**Scope of this evidence.** It is **historical, git-derivable engine evidence**
about one real close. It is **NOT** the same thing as, and MUST NOT be conflated
with, the separately adjudicated **Ship in-workspace verification** of that close
(D8) — which is a distinct, separately recorded, operator-and-Ship-owned
observation. Neither substitutes for the other.

That establishes exactly **one** engine proposition: *a `status: archived`
out-of-manifest sibling is skipped by the engine's cascade.* This is precisely —
and only — the proposition D1b's inertness grant rests on, which is why the
grant is admissible.

**Everything else from F3 remains INDICATIVE and is NOT authorized as proof:**

* Arm 2's `returned_ids: []` while archiving a live task — **indicative**. It may
  be stated as *rationale* for treating the `returned_ids` guard as insufficient,
  and MUST NOT be stated as a proven engine law.
* Arm 3/4's `parent_id` clearing on returned siblings — **indicative**; remains
  **blocked** and carried by durable follow-up `63363CF5`.
* `status: done` descendant archival — **indicative**. Note this proposition is
  **not load-bearing**: `done` is not `archived`, so it is non-inert and forces
  `SAFE_CLOSE` under D1b regardless of what the engine would have done.

**No plan, task, skill, or policy surface may claim a classifier fixture proves
an engine behavior.** Where an engine behavior is unproven, the dependent
autoharness behavior MUST be the fail-closed one.

#### D7b — Containment rule, correctly scoped (REVISION 3; REPLACED IN REVISION 4)

> **⚠️ REVISION 4 — THE REVISION-3 `PERMITTED` CARVE-OUT IS WITHDRAWN IN FULL.**
> Revision 3 permitted *"an OS-temp scratch directory used by a read-only,
> hermetic, self-cleaning Python unit test"* and stated that
> `tempfile.TemporaryDirectory()` *"need NOT be relocated"*. **That permission
> violates two constitutional principles and is withdrawn:**
>
> 1. **Constitution Principle IV — workspace containment.** An OS `%TEMP%` /
>    `TMPDIR` path resolves **outside this repository and outside the current
>    working directory**. Hermeticity, read-only intent, and tool-freeness are
>    properties of *what the test does*; they are **not** containment arguments.
>    A write outside the workspace is a containment breach regardless of how
>    self-contained the writer is.
> 2. **Constitution Principle VII — destructive-operation approval.**
>    `tempfile.TemporaryDirectory()` performs an **automatic, unapproved,
>    recursive deletion** of its tree on context exit. "Self-cleaning" is a
>    description of an unapproved destructive operation, not a justification for
>    one. **No surface may describe a self-cleaning temporary directory as
>    permitted.**
>
> The revision-3 rationale that *"relocating them into the repository would add
> git-ignore surface and buy no auditability"* is **also withdrawn**: no
> git-ignore surface needs to be added (see the canonical root below, which is
> **already** ignored), and in-repository scratch is auditable precisely because
> it is reachable, inspectable, and operator-controlled.

The containment rule is therefore:

* **PROHIBITED — ALL of the following, for ANY purpose in this decision, its
  plan, or its tasks:**
  * `tempfile.TemporaryDirectory()`, `tempfile.mkdtemp()`, `tempfile.mkstemp()`,
    `TMPDIR`/`%TEMP%`-rooted paths, and any other mechanism whose result
    resolves outside the current working directory — **including** for pure
    classifier unit tests and **including** the G1 historical replay;
  * creating, mutating, destroying, or citing an out-of-repository workspace in
    which the backlogit engine is executed;
  * **any write of any kind outside the current working directory**;
  * any automatic, implicit, on-exit, atexit, fixture-teardown, or
    "best-effort" deletion of a scratch workspace.

* **REQUIRED — the canonical repository-internal scratch root.** Every fixture,
  scratch, replay, or synthetic-backlog workspace created by any unit MUST
  resolve under:

  ```text
  <repo_root>/.autoharness/staging/tmp/<unique-run-or-test-nonce>/
  ```

  This root is **already git-ignored** by `.gitignore` line 6
  (`.autoharness/staging/`), confirmed with
  `git check-ignore -v .autoharness/staging/tmp/probe.txt`. **No `.gitignore`
  change is required, and none is authorized** by this decision.

* **REQUIRED — the canonical containment check**, executed **before the first
  write** of every such workspace and **failing closed** on any mismatch:

  ```python
  root = Path(os.getcwd()).resolve(strict=True)
  scratch = (root / ".autoharness" / "staging" / "tmp" / nonce).resolve()
  if os.path.commonpath([str(root), str(scratch)]) != str(root):
      raise AssertionError(f"containment violation: {scratch} escapes {root}")
  ```

  Both operands MUST be fully **resolved real paths** (symlinks and `..`
  collapsed) before comparison, and the comparison MUST use `commonpath` or an
  equivalent `is_relative_to` test. A raw string-prefix test is **NOT**
  sufficient and MUST NOT be substituted.

* **REQUIRED — cleanup is operator-controlled, never agent-automatic.** Scratch
  directories under the canonical root are **persistent and uniquely named**.
  Leaving them in place at the end of a run is the **correct terminal state**.
  No unit may delete, prune, truncate, `rmtree`, or otherwise remove them.
  Deletion may occur **only** through the D6 sequence: **CAPTURE EVIDENCE →
  HALT → EMIT P-005 → REQUEST EXPLICIT OPERATOR APPROVAL → REVALIDATE the exact
  paths and their state after approval → EXECUTE ONLY THE APPROVED DELETION**.
  Accumulated scratch is an operator hygiene matter; it is **never** a licence
  for an agent to invent deletion authority.

* **CONDITIONAL, AND STILL NOT AUTHORIZED HERE** — a real engine
  characterization MUST additionally run under an explicit time-boxed P-016
  declaration with **explicit operator destructive approval obtained before
  creation** and D6-routed cleanup after. That work is **NOT authorized by this
  decision** and is **NOT in `174-S`**; it is carried as follow-up (P2-3).

### D8 — `173-S` closure provenance (REVISION 2, recorded)

| Fact | Value |
|---|---|
| Who closed it | **the operator**, manually |
| Authorization | **explicit**, given after a **Ship read-only preview** |
| Ship's role | read-only preview **before**; in-workspace verification **after** |
| Stage's role | **none** — Stage neither closed, claimed, previewed-as-authority, nor mutated `173-S` |
| Verified after close | `archived_status: shipped`; release SHA `9cc98c41`; exactly 11 manifest members + the record = **12 CLOSE-SCOPED paths**; excluded siblings byte-identical; **zero** active shipments; `174-S` `pre_claim` **PASS** |

> **⚠️ REVISION 4 — SCOPE NOTE.** The **12** above is Ship's **in-workspace,
> close-scoped** observation, separately adjudicated. It is **not** the diffstat
> size of any commit: the publication commit `e4ca20e5` contains **34** changed
> paths. Do not restate this row as "`git show --stat e4ca20e5` shows 12 paths"
> — see **D7a** / **D10 G3** for the path-scoped, git-derivable formulation, and
> keep the two evidence sources distinct.

This is **NOT** a Stage P-010 role-boundary violation and MUST NOT be recorded,
summarized, or reported as one. Any downstream surface (handoff memory, PR
readiness, shipment record) describing this event MUST carry the
**operator-action provenance** above.

#### D8a — The closure evidence of record is CONTRADICTORY (REVISION 3)

> **⚠️ The backlog state and the closure record of record DISAGREE.** Stage must
> not resolve this by rewriting closure truth — `closure_status` is a
> **Ship/operator-owned** field consumed by
> `gates.topology._closure_artifact_complete`. Stage records the contradiction
> and routes it.

| Surface | What it asserts | Owner |
|---|---|---|
| `.backlogit/archive/173-S.md` | `status: archived`, `archived_status: shipped`, `commit: 9cc98c41` — **closed** | backlogit state |
| `git diff` path-scoped, `358b63b4` → `e4ca20e5` (D7a / D10 G3) | the 12 close-effect paths changed and both excluded siblings are byte-identical; the close physically happened. *(`e4ca20e5` is the **combined publication commit**, 34 paths — the 12 are a **path-scoped subset**, never its unfiltered diffstat.)* | git (immutable) |
| `docs/closure/2026-09-14-173-s-165-f-closure.md` | `closure_status: BLOCKED`; condition 2 `satisfied: false`; *"The shipment record remains status: active in backlogit"* | **Ship / operator** |

Findings, binding on the successor plan:

1. That closure artifact is a **historical, blocked-phase, pre-close record**. It
   was accurate when written (2026-09-14) and was **overtaken by events** on
   2026-09-16. It is **not** evidence that `173-S` is open.
2. **Stage MUST NOT edit it.** Rewriting a Ship-owned closure verdict — including
   flipping `closure_status` or a `satisfied:` flag — is a **P-010** violation.
   Stage annotates supersession **only on Stage-owned surfaces** (this decision,
   the plan, the `174-S` handoff record, session memory).
3. **There is no closure record of record for `173-S`.**
   `topology.closure_complete()` globs
   `docs/closure/{shipment_id}-*-post-merge-closure.md`. The stale file is named
   `2026-09-14-173-s-165-f-closure.md`, which **does not match that glob**, so
   `closure_complete("173-S")` returns **`None` (no artifact found)** — not
   `False`. The gate is therefore **not currently tripped** by the stale file;
   the real gap is that **no matching post-merge closure artifact exists at all**.
4. **`174-S`'s `pre_claim` PASS does NOT evidence `173-S` closure.** `174-S`
   carries `labels: [dag-root]` and **empty** `dependencies`, so it derives
   `predecessor_source: declared_root` and **never consults** `173-S`'s closure
   artifact. Any surface citing `pre_claim: PASS` as proof that `173-S` closure is
   documented is making an unsupported inference and MUST be corrected.
5. **P-001 is discharged IN FACT but NOT EVIDENCED OF RECORD.** The sequencing
   overlap genuinely ceased to exist (zero active shipments; `173-S` archived).
   But while the only closure artifact naming `173-S` says `BLOCKED` and
   `satisfied: false`, no surface may declare P-001 "discharged" without
   qualification. The honest formulation is: *discharged by state; closure
   evidence contradictory; superseding record outstanding.*
6. **Readiness prerequisite (routed, not self-granted).** A
   **Ship/operator-owned superseding closure record** for `173-S` —
   conventionally `docs/closure/173-S-165-F-post-merge-closure.md`, carrying the
   operator-action provenance in D8, the `e4ca20e5` diffstat evidence, and an
   explicit supersession pointer retiring the 2026-09-14 artifact — is a
   **`174-S` claim-readiness prerequisite**. Stage records this requirement and
   **cannot satisfy it**.

### D10 — The `173-S` retrospective gate needs an IMMUTABLE PRE-CLOSE PIN (REVISION 3)

> **⚠️ The revision-2 formulation of the retrospective gate was
> UNSATISFIABLE.** It asked a classification performed over the **current,
> post-close** records to reproduce the **pre-close** 12-ID result. It cannot:
> `required_ids` is defined as *"closure_scope members not already truly
> archived at the pre-close snapshot"*, and **every** one of those 12 records is
> now `status: archived`. Evaluated against current state, `required_ids` is
> **∅**, not 12. The gate as written would have failed for a correct
> implementation, or pressured an implementer to hard-code the 12.

The retrospective obligation is split into **two disjoint, separately
reproducible gates**.

**Immutable pre-close pin.** The close effect landed in commit **`e4ca20e5`**;
the pre-close tree is therefore its parent, **`358b63b4`**. Both are immutable
git objects already present in this repository, so the snapshot is reproducible
without network access and without trusting any narrative text.

> **⚠️ REVISION 4 — G1 WAS INCOMPLETE AND G3 WAS FACTUALLY WRONG. Both rows are
> replaced below.** (i) G1 materialized only the shipment record and the 11
> manifest members, and asserted the excluded siblings were *"absent from every
> set"*. Absence is **vacuous** if the siblings are never materialized at all: a
> replay that simply omits `165.007-T`/`165.010-T` satisfies the old assertion
> while proving nothing about inertness. (ii) G3 asserted that
> `git show --stat e4ca20e5` contains exactly 12 paths and treated `e4ca20e5`
> as a close-only commit. `e4ca20e5` is **`chore(stage): publish flat-manifest
> closure package`** — a **combined publication commit** whose unfiltered
> diffstat contains **34 paths**. Both claims are **withdrawn**.

**G1 — required snapshot composition (revision 4, NON-NEGOTIABLE).** The replay
MUST materialize the **complete safety-relevant pre-close shape**, at the
**pre-close paths**, pinned by git blob object ID at `358b63b4`:

| # | Pre-close path at `358b63b4` | Pre-close declared `status` | Blob OID at `358b63b4` | Role in the replay |
|---|---|---|---|---|
| 1 | `.backlogit/queue/173-S.md` | `active` | `507508b2df41982b4c930f74bfe92ef495ce25f7` | shipment record `S` (11-item manifest) |
| 2 | `.backlogit/archive/165-F.md` | `done` | `90b50dd1eea3a387dfaf8d3d49fd04d263333ed6` | manifest member (covering feature) |
| 3 | `.backlogit/archive/165.001-T.md` | `done` | `181cf8b1fd07b969be7d7da99a015cdf4c8fb531` | manifest member |
| 4 | `.backlogit/archive/165.002-T.md` | `done` | `5ef5e91f7b201411678cc70a8664afb25f4ea7a1` | manifest member |
| 5 | `.backlogit/archive/165.003-T.md` | `done` | `3ce423785e8471f5770c6abe3ec447b95ee89157` | manifest member |
| 6 | `.backlogit/archive/165.004-T.md` | `done` | `954f82d3b6b136dc8d85f36f1b1117269ce94c6d` | manifest member |
| 7 | `.backlogit/archive/165.005-T.md` | `done` | `2390f5d7e6b4ef4c92c647648a80322b4acf5c59` | manifest member |
| 8 | `.backlogit/archive/165.006-T.md` | `done` | `623408f31d94f8e68dbd975de48c9e472a020c4b` | manifest member |
| 9 | `.backlogit/archive/165.008-T.md` | `done` | `a87a620181e757ac3fbb2aca5ff38432625da78c` | manifest member |
| 10 | `.backlogit/archive/165.009-T.md` | `done` | `d5ee0c78e0fdb2ae5f1e63bb7ca472b8e11d453c` | manifest member |
| 11 | `.backlogit/archive/165.011-T.md` | `done` | `3c68a702c94daacc8ae93c42df6e49501f9b42d2` | manifest member |
| 12 | `.backlogit/archive/165.012-T.md` | `done` | `6d154c15a5f2a2ef22aec93d58a656ce6f90f0ca` | manifest member |
| 13 | `.backlogit/archive/165.007-T.md` | `archived` | `544c2377b38e9ba2df123f5b8d9bf359dacb89ea` | **EXCLUDED out-of-manifest descendant** (`parent_id: 165-F`) |
| 14 | `.backlogit/archive/165.010-T.md` | `archived` | `609ad8bc7839fca8b5273d777a6acdc590aacb6f` | **EXCLUDED out-of-manifest descendant** (`parent_id: 165-F`) |

Rows **13 and 14 are mandatory members of the snapshot**, not optional context.
Each blob OID above is re-derivable with `git rev-parse 358b63b4:<path>`; the
executor MUST additionally record the SHA-256 digest of every extracted byte
stream in the task output. **Paths MUST be preserved exactly as listed** — the 11
manifest members sat physically in `.backlogit/archive/` while still declaring
`status: done`, which is itself the pre-close corroboration of INV-6's
*location-is-never-sufficient* rule (R08). A replay that relocates them into
`queue/` changes the shape under test and is invalid.

**G1 — required non-vacuous assertions on the excluded siblings.** The replay
MUST assert, in this order, that `165.007-T` and `165.010-T` are:

1. **DISCOVERED** — each is reached by the descendant walk from `165-F` (i.e.
   each appears in the enumerated descendant set), so it is present, resolvable,
   and unambiguous in the index;
2. **READ** — each resolves to a **parsed** frontmatter `status` that is a `str`
   **exactly equal** to `"archived"` under D1b (`isinstance(status, str) and
   status == "archived"`), asserted on the **parsed** value, not on the file text;
3. **CLASSIFIED INERT** — each is then excluded from the non-inert set **because
   it is inert**, and only then;
4. **ABSENT** — each is absent from `archived_ids`, `required_ids`, and
   `allowed_ids`.

**Assertion 4 alone is INSUFFICIENT and MUST NOT be asserted without 1–3.**
Absence produced by a record that was never materialized, never discovered, or
never parsed is a **vacuous pass** and is a STOP condition.

| Gate | Evaluated over | Expectation | Evidence kind |
|---|---|---|---|
| **G1 — historical operation replay** | the **14-row** snapshot above, materialized by `git show 358b63b4:<path>` into a scratch backlog under the canonical repository-internal root (D7b), blob-OID- and SHA-256-pinned | verdict `CASCADE`; `required_ids` = 11 members + `173-S` = **12**; `165.007-T`/`165.010-T` **discovered → parsed canonical `archived` → excluded as inert** (assertions 1–3) and only then absent from every set (assertion 4) | CLASSIFIER LAW (D7a) |
| **G2 — current-state classification** | The **current** archived records | verdict is reported for regression tracking; `required_ids` = **∅** because all 12 are already truly archived; re-closing would be a **no-op**. Asserting a 12-ID `archived_ids` here is **INVALID** and is withdrawn | CLASSIFIER LAW (D7a) |
| **G3 — historical engine effect, PATH-SCOPED (revision 4)** | four **path-scoped** `git diff`/`git rev-parse` invocations between `358b63b4` and `e4ca20e5` (see D7a's corrected block): (a) the 11 members → **11 modified**, no add/delete/rename; (b) `-M --find-renames` over `queue/173-S.md` + `archive/173-S.md` → **exactly one entry**, the rename-plus-modify `.backlogit/{queue => archive}/173-S.md`; (c) the two excluded siblings → **empty diff**; (d) `git rev-parse` blob identity for the two siblings → **identical OIDs at both commits** | (a)+(b) = the **12 close-effect paths as a path-scoped subset**; (c)+(d) = the siblings are byte-identical across the close. **`e4ca20e5` MUST NOT be described as a close-only commit, and its UNFILTERED diffstat MUST NOT be claimed to contain exactly 12 paths — it is the combined publication commit and contains 34.** This is historical git evidence and is **distinct from** the separately adjudicated Ship in-workspace verification (D8) | ENGINE LAW (D7a) — **immutable, reproducible, already satisfied** |

**Reproducibility requirement.** G1's snapshot MUST be materialized by
`git show 358b63b4:<path>` (or an equivalent checked-in fixture carrying the same
blob OIDs and SHA-256 digests), and the digests MUST be recorded in the plan and
the task, so the gate is re-runnable by anyone at any later date and cannot
silently drift with the working tree. **No expectation in G1, G2, or G3 may be
hard-coded as a bare assertion without its pinned source.**

### D9 — Residual-defect follow-up identity (REVISION 2)

Archived stash entry `2B42392E` was archived as fully consumed, but only its
**`173-S`-specific** aspect was consumed. Its **general** claim — that *every*
`SAFE_CLOSE`-classified shipment closure is blocked at the record transition
workspace-wide — remains **unresolved** and is exactly the R1 / INV-11 blocker.
Two **durable active** P-021 follow-ups therefore carry the residual identity
forward (IDs recorded in the successor plan and in `166-F`):

1. **`7F9CB5E9` — General `SAFE_CLOSE` record-transition defect** (active, bug,
   high) — successor to `2B42392E`'s unconsumed general scope; **BLOCKS** INV-11 /
   operational multi-shipment delivery, and blocks any future genuine
   `SAFE_CLOSE` closure. External/runtime prerequisite; not implementable here.
2. **`63363CF5` — backlogit clears `parent_id` on returned out-of-manifest
   siblings** (active, bug, high; R2) — a distinct upstream data-integrity defect
   discovered by the same work. Load-bearing for the no-substitution prohibition.

The append-only archived stash record is **not rewritten**. Traceability runs
**forward**: each new entry names `2B42392E` as its predecessor and states which
part of it was actually consumed, and this decision, the plan, `166-F`, and the
session memory all carry the same pointer.

### D11 — The red matrix is FOUR classes, not three (REVISION 3)

> **⚠️ The revision-2 three-class scheme was UNSATISFIABLE and is corrected
> here.** It designated A1–A5, A9 and A10 as CLASS 1 "behaviour-changing — MUST
> FAIL RED against current `main`". Measured against the current
> `shipment_closure.py`, that is false for most of them. The live predicate is:
>
> ```python
> missing = tuple(d for d in descendants if d not in manifest_id_set)
> if missing:  # -> SAFE_CLOSE, reason naming the offending IDs
> ```
>
> **Every** out-of-manifest descendant — live, `done`, `Archived`, `ARCHIVED`,
> `" archived "`, torn, or absent-status — already yields `SAFE_CLOSE` **with the
> offending ID named in `reason`**. So A2, A3, A4, the live half of A5, all three
> A9 variants, and both A10 cases are **already green on verdict**. Demanding
> they go red would force an author to weaken a correct test — exactly the
> failure mode revision 2 claimed to have fixed, reintroduced one level down.

Every test declares **exactly one** of four classes in its docstring.

> **⚠️ REVISION 4 — THE REVISION-3 MEMBERSHIP ROWS WERE SELF-CONTRADICTORY AND
> ARE REPLACED.** Revision 3 mandated *"every test declares **exactly one** of
> four classes"* while simultaneously assigning **two** classes to a **single
> named test** for A2, A3, the three A9 variants, and A10 — the CLASS 4 verdict
> assertion (which **must start green**) and the CLASS 1 reason-text assertion
> (which **must start red**) were placed inside the same test function. Those
> two requirements cannot both hold for one test: on current `main` it fails
> (breaking its CLASS 4 must-start-green obligation) and it cannot be
> individually demonstrated green, so the CLASS 4 before/after pair — the entire
> containment proof — is unobtainable. **Resolution: SPLIT THE OBSERVABLES INTO
> SEPARATELY NAMED TESTS.**

**GRANULARITY RULE (revision 4, NON-NEGOTIABLE).** Class is declared and gated at
**test-function granularity**, and **exactly one class per named test** holds
without exception. Therefore:

* **NO named test may assert both a VERDICT observable and a DIAGNOSTIC/REASON
  observable.** A verdict test asserts only on `ClosePath`; a reason test asserts
  only on `reason` text. Where the revision-3 matrix bundled them, the test is
  **split into two separately named tests**, each carrying exactly one class.
* A **CLASS 4** verdict test MUST NOT assert on `reason` at all — any reason
  assertion would make it red today and destroy its must-start-green property.
* A **CLASS 1** reason test MUST NOT assert a verdict — its red must be caused by
  the missing reason text and nothing else, so that it fails today "for its own
  specific named reason".
* The same split fixture shape MAY be shared between the pair via a helper; the
  **assertions**, and therefore the class gating, are what must be separated.

| Split source | CLASS 4 test (MUST START GREEN, verdict only) | CLASS 1 test (MUST FAIL RED, reason text only) |
|---|---|---|
| A2 | `test_done_but_not_archived_out_of_manifest_child_falls_back_to_safe_close` | `test_done_but_not_archived_out_of_manifest_child_reason_names_observed_status` |
| A3 | `test_live_out_of_manifest_child_falls_back_to_safe_close` | `test_live_out_of_manifest_child_reason_names_observed_status` |
| A9 (`Archived`) | `test_titlecase_archived_out_of_manifest_child_falls_back_to_safe_close` | `test_titlecase_archived_out_of_manifest_child_reason_names_observed_status` |
| A9 (`ARCHIVED`) | `test_uppercase_archived_out_of_manifest_child_falls_back_to_safe_close` | `test_uppercase_archived_out_of_manifest_child_reason_names_observed_status` |
| A9 (`" archived "`) | `test_whitespace_padded_archived_out_of_manifest_child_falls_back_to_safe_close` | `test_whitespace_padded_archived_out_of_manifest_child_reason_names_observed_status` |
| A10 (torn) | `test_torn_out_of_manifest_descendant_falls_back_to_safe_close` | `test_torn_out_of_manifest_descendant_reason_is_torn_specific` |

| Class | Meaning | Required initial state | Members |
|---|---|---|---|
| **CLASS 1 — BEHAVIOUR-CHANGING** | Asserts a verdict or reason the classifier does **not** yet produce | **MUST FAIL RED** on current `main`, each for its own **specific** named reason — never an import/collection error | **A1** (archived out-of-manifest child → `CASCADE`); **A5a** (archived out-of-manifest *grandchild* → `CASCADE`); the **six split reason-text tests** in the right-hand column above |
| **CLASS 2 — DOC-CONTRACT** | Asserts contract text that does not yet exist | **MUST FAIL RED** on current `main` | all of PART B |
| **CLASS 3 — CHARACTERIZATION** | Pins behaviour already correct and unrelated to the new predicate | **MAY START GREEN** — green is the correct outcome | A0, A6, A7, A8 |
| **CLASS 4 — CONTAINMENT-REGRESSION** (**NEW in revision 3**) | Pins a `SAFE_CLOSE` **verdict** that is already correct today and that the *new* predicate could silently re-widen | **MUST START GREEN and MUST STAY GREEN.** A red result here on current `main` means **the test is wrong**, not the code | the **six split verdict tests** in the left-hand column above, plus **A4**, **A5b** (live grandchild), `test_duplicate_id_within_single_root_falls_back_to_safe_close`, and A11's non-`str` fixtures |

**Why CLASS 4 is a distinct class and not "just characterization".** A CLASS 3
test pins behaviour nothing in this plan touches. A CLASS 4 test pins behaviour
that U2 **actively rewrites the predicate underneath**: today these shapes are
rejected because they are *out of manifest*; after U2 they must be rejected
because they are *non-inert*. The verdict is unchanged but its **entire
justification is replaced**, and a subtly wrong inertness predicate (a stray
`.strip()`, a missing torn check) would flip them to `CASCADE` — a destructive
regression. They are the load-bearing guards of this change, and their green
start is **positive evidence**, not an absence of evidence.

**Where genuine red signal comes from instead.** U2 requires the reason string to
name the offending IDs **and their observed status**, and requires a
**torn-specific** containment reason. Current `main` emits neither. Asserting
that text is a **real, non-contrived** red observable that fails today and passes
only after the intended change — which is why those assertions, and not the
verdicts, carry CLASS 1 in the table above.

**Prohibited.** Contriving a failure, weakening an assertion, or re-shaping a
fixture for the sole purpose of making a CLASS 3 or CLASS 4 test go red is a
**red-phase falsification** and is forbidden. Mandatory red applies **only** to
genuinely missing or behaviour-changing observables.

## Rejected Alternatives

* **Red-phase class scheme with only three classes (REVISION 3, rejected).**
  See D11 — the three-class scheme produced an unsatisfiable red matrix.
* **TERMINAL_CLOSE (prior E1)** — withdrawn: precondition 2 is hierarchical
  closure restated, and precondition 3 makes multi-shipment feature delivery
  unreachable (F6).
* **Terminal-descope exemption (prior E2)** — withdrawn: substitutes a
  disposition-note gate for an ancestry gate over artifacts that INV-3 says must
  not gate closure at all.
* **Option G (no descendant inspection)** — rejected: empirically destructive
  (Arms 2–4).
* **Option J (keep TERMINAL_CLOSE alongside)** — rejected as unreachable dead
  code carrying a superseded premise.
* **Clearing `parent_id` / re-manifesting the descoped siblings** — remain
  rejected exactly as in the prior decision; both falsify history, and INV-3 now
  makes both unnecessary.
* **Creating a replacement feature/shipment** — rejected per Option I: it would
  require new operator `dag-root` authorization the operator forbade expanding.

## Unresolved Questions

1. **R1 (operator/upstream) — EXTERNAL RUNTIME PREREQUISITE, durable follow-up
   created (revision 2):** the partial-shipment record transition. For a genuine
   `SAFE_CLOSE` shipment, `move --status shipped` is refused (F4) and the cascade
   is unsafe (Arms 3–4 clear `parent_id` on returned siblings), so **no safe path
   to `archived_status: shipped` exists in 1.10.1**. It is **not** on the
   `173-S` critical path (that closure went through `CASCADE`, and is now done),
   but it **is** the sole blocker on INV-11 / operational multi-shipment
   delivery. It **cannot be implemented in this repository** — `backlogit` is an
   external Go binary dependency. Surfaced as a fail-closed halt with an explicit
   escalation message rather than a silent workaround, pursued upstream (Option
   H), and tracked by **durable active** P-021 follow-up **`7F9CB5E9`** (D9 item
   1), which declares the blocking relationship explicitly.
2. **R2 — durable follow-up created (revision 2):** the engine's
   `parent_id`-clearing on returned siblings (Arms 3–4) is an upstream
   data-integrity defect; tracked by **durable active** P-021 follow-up
   **`63363CF5`** (D9 item 2) and reported upstream regardless of R1.
3. **R3 — DISCHARGED IN FACT, NOT EVIDENCED OF RECORD (2026-09-16; qualified in
   revision 3):** P-001 overlap authority for `174-S` vs. `173-S` **no longer
   applies in fact**. `173-S` is archived (`archived_status: shipped`) following
   the operator's authorized administrative close, so there is no overlap to
   authorize and `174-S`'s `pre_claim` gate **passes**. Nothing was granted by
   Stage. **However**, per **D8a**, the closure evidence of record is
   contradictory and `pre_claim: PASS` does **not** evidence `173-S` closure
   (`174-S` is `dag-root` with empty `dependencies`, so `predecessor_source` is
   `declared_root` and `pre_claim` never consults that artifact). The unqualified
   revision-2 phrasing "DISCHARGED BY STATE" is **withdrawn**; a
   **Ship/operator-owned** superseding closure record remains outstanding.
4. **R4:** whether `168-S` qualifies under INV-6 — to be classified at its own
   closure.
5. **R5:** the widespread `done`-without-provenance archive shape (366 records)
   remains an observation, accommodated rather than corrected.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Inertness gate misread as hierarchy closure in review or implementation | INV-6 is stated as a constraint on the *instrument*; the Option F discrimination table pins the observable difference (row 1 = `173-S`); a pinning test asserts an archived descoped sibling **passes** |
| Arm-2 destructive cascade regresses | Pre-mutation inertness check + retained post-mutation two-set gate; Arm 2 becomes a mandatory negative-scenario test |
| `returned_ids` treated as sufficient protection | Explicitly recorded as **insufficient** (Arm 2 returned `[]` while archiving a live task); the skill text must say so |
| Multi-shipment delivery still blocked in practice | **Stated honestly as INV-11**: contract-complete, operationally blocked on the external R1 prerequisite. INV-4/INV-5 pinned by a split-delivery **contract-text** fixture only; no acceptance criterion claims end-to-end split delivery works |
| Historical manifests invalidated by "feature last" | INV-8 makes ordering non-normative at closure; `173-S` remains untouched and was closed successfully under feature-**first** ordering |
| Change special-cased to `173-S` | INV-1..INV-11 are defined by declared status + membership only; acceptance requires the `168-S`/`160-F` control fixture |
| Dry-run mutates something | D4 dry-run is read-only by construction and hash-verifies the workspace before/after; `173-S` is a retrospective fixture and immutable |
| R1 silently worked around | Fail-closed halt with an explicit escalation message; never substitute the cascade on a non-inert manifest; durable active follow-up (D9) |
| Inertness broadened by status normalization | D1b exact canonical match; variant-status negative fixtures (`Archived`, `" archived "`) must classify `SAFE_CLOSE` |
| Torn/duplicate record silently trusted | D1c full-scan fail-closed, including out-of-manifest descendants; dedicated negative fixture |
| Spike-only evidence treated as proof | D7/D7a (rev 3) + **rev 4**: F3 is non-authoritative; CLASSIFIER LAW and ENGINE LAW are **disjoint**, so no classifier fixture may be cited as proof of an engine behaviour. The revision-2 mitigation *"every governing claim re-derived as an in-workspace checked-in fixture"* is **WITHDRAWN as unsound**. The single held engine proposition rests on **path-scoped git evidence** between `358b63b4` and `e4ca20e5` (D7a, D10 G3); `returned_ids` and `parent_id` clearing remain **INDICATIVE/UNPROVEN** and **cannot authorize cascade** |
| Destructive rollback executed without approval | D6 capture → halt → P-005 → explicit approval → revalidate → approved rollback; notification-only and automatic revert are prohibited formulations |
