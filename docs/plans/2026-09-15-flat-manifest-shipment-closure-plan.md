---
title: "Flat-manifest shipment closure — implementation plan"
description: "Test-first implementation plan for the reframed feature 166-F: replaces the P-015 hierarchical-closure precondition with an engine-inertness blast-radius containment gate in classify_shipment_close_path, redefines the shipment-reconcile protected-set gate from baseline-presence to baseline-invariance, records the fail-closed escalation for the unresolved partial-shipment record transition, mirrors both contract surfaces into templates/, and proves 173-S closable via a read-only dry-run without mutating its excluded siblings."
doc_type: plan
source: docs/plans/2026-09-15-flat-manifest-shipment-closure-plan.md
date: 2026-09-15
status: reviewed
revision: 5
revision_note: "Revision 5 (2026-09-16) is a NARROWLY BOUNDED, operator-authorized (cycle-4 disposition option (a)) correction resolving EXACTLY ONE finding: the cycle-4 open blocker P1-C4-1, a non-canonical verification gate. Section 3 U6 item 2 ('Run `pytest`') and section 8 ('`pytest tests/` green') contradicted durable learning docs/compound/097-S-canonical-unittest-gate.md, which establishes `PYTHONPATH=src python -m unittest discover -s tests` as THE canonical source-validation gate for this workspace because pyproject.toml declares only pythonpath=['src'] with no testpaths/norecursedirs, so a repository-root pytest run collects vendored references/* tests and can FALSELY BLOCK a green shipment. Both surfaces now mandate the canonical unittest invocation (with the PowerShell equivalent), demote path-scoped `pytest tests/` to an explicitly SECONDARY, NON-AUTHORITATIVE convenience run that may never stand as closure evidence, and PROHIBIT bare root pytest as a gate. Decision D16's load-bearing justification, which cited an invocation 'this plan mandates' that the plan did not in fact mandate, now names the canonical invocation and the two surfaces that mandate it, with the pre-revision-5 mismatch recorded. 097-S is added to section 1 as a BINDING referenced durable learning with path and provenance. NO unit, task mapping, decision outcome, freeze-scope boundary, closure scope, blast radius, authorization, or claimability changes; no new hardening signal (5/5 unchanged, re-check recorded). Task record 166.006-T already stated the correct gate and is unchanged. Verified by a single focused plan-review verification pass over exactly this correction. Revision 4 (2026-09-16) resolves the four deduplicated P1 groups of the THIRD AND FINAL permitted external review-fix cycle over the revision-3 package."
revision_4_note: "Revision 4 (2026-09-16) resolves the four deduplicated P1 groups of the THIRD AND FINAL permitted external review-fix cycle over the revision-3 package. (A) TEST GRANULARITY: the revision-3 red matrix required exactly one class per test yet assigned two classes (CLASS 4 verdict, must start green; CLASS 1 reason text, must start red) to a single named test for A2/A3/A9/A10 — the verdict and diagnostic observables are now SPLIT into separately named single-class tests and class is gated at test-function granularity (D11/D16/U1/H19). (B) EVIDENCE HONESTY PROPAGATION: residual fixture-as-engine-proof claims and 'measured engine' phrasings for returned_ids and parent_id clearing are withdrawn on every remaining surface; classifier-law/engine-law separation is restated on every authoritative execution surface and unproven engine behaviour is indicative + fail-closed and cannot authorize cascade (R24/D13/H17). (C) HISTORICAL REPLAY/EVIDENCE: decision D4's current-recorded-manifest 12-ID must-language is explicitly superseded by D10 G1/G2/G3; G1 materializes the COMPLETE 14-row pre-close shape from immutable 358b63b4 including the excluded descendants 165.007-T/165.010-T, blob-OID-pinned, with non-vacuous discovered -> parsed-canonical-archived -> excluded-as-inert assertions; G3 no longer claims the unfiltered `git show --stat e4ca20e5` contains exactly 12 paths nor that e4ca20e5 is close-only (it is the COMBINED PUBLICATION COMMIT, 34 paths) and is replaced by explicit path-scoped before/after evidence, distinguished from the separately adjudicated Ship in-workspace verification (R16/D10/H20). (D) CONSTITUTIONAL CONTAINMENT: the revision-3 permission for tempfile.TemporaryDirectory() under OS %TEMP% is WITHDRAWN as a Constitution IV containment violation, and its automatic cleanup as a Principle VII destructive-approval violation; ALL fixture/scratch/replay workspaces including pure-classifier tests and the G1 replay must resolve under the repository-internal git-ignored root .autoharness/staging/tmp/ with canonical resolved-realpath containment checks, no writes outside cwd, and D6-routed operator-controlled deletion only (D7b/R27/H21). Mandatory plan-harden impact re-check re-run. Plan-review CYCLE 4 NOT RUN at revision-4 publication time — the Stage 3-cycles-per-plan review-fix limit is exhausted at cycle 3; recorded and halted for operator disposition rather than bypassed. It was SUBSEQUENTLY RUN under a one-time operator override and returned decision: FAIL with the single open P1 (P1-C4-1) that revision 5 resolves. Revision 3 (2026-09-16) resolves the five deduplicated P1 blockers from the completed local fix-verification review. (1) The red matrix was UNSATISFIABLE: A2-A4, A5-live, A9 and A10 already return SAFE_CLOSE naming the offending ID on current main, so they are reclassified into a new CLASS 4 containment-regression class that must START GREEN, and mandatory red is relocated to the genuinely-absent observed-status and torn-specific reason-text observables (D11/R19/R20). (2) Classifier fixtures CANNOT re-derive engine behaviour; CLASSIFIER LAW and ENGINE LAW are now disjoint evidence classes, and the containment precheck was re-scoped (SUPERSEDED BY REVISION 4) (D7a/D7b/R24). (3) The 173-S retrospective gate is pinned to the immutable pre-close revision 358b63b4 and split into G1 replay / G2 current-state / G3 engine-effect, withdrawing the invalid post-close 12-ID assertion (D10/R16). (4) The contradictory 2026-09-14 closure artifact is recorded as a historical blocked-phase record which Stage MUST NOT rewrite; a Ship/operator-owned superseding closure record is recorded as a 174-S readiness prerequisite and the unqualified P-001 discharge claim is withdrawn (D8a/R26). (5) The byte-for-byte status contract is unimplementable under yaml.safe_load and is replaced by exact parsed-scalar equality with non-str fail-closed (D1b/R25). Revision 2 (2026-09-16) applied consolidated local-review blocker corrections; revision 1 was produced by impl-plan for the reframed 166-F after the operator architectural correction superseded the TERMINAL_CLOSE premise."
decision_source: docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md
supersedes_plan: docs/plans/2026-09-15-terminal-shipment-closure-plan.md
superseded_decision: docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md
memory_source: docs/memory/2026-09-15-stage-flat-manifest-closure-supersession.md
feature_id: 166-F
shipment_id: 174-S
stash_ids:
  - FBD2F6BE
  - 2B42392E
related_stash_ids:
  - 3CA122AC
  - 7F9CB5E9
  - 63363CF5
---

# Implementation Plan — Flat-Manifest Shipment Closure

> ## 🔄 REVISION 5 — 2026-09-16 — AUTHORITATIVE, NARROWLY BOUNDED CORRECTION
>
> Revision 5 exists for **exactly one purpose**: to resolve **P1-C4-1**, the
> single open P1 returned by `plan-review` **cycle 4** over revision 4 — the
> plan mandated a **non-canonical** `pytest` verification gate, contradicting
> durable learning `docs/compound/097-S-canonical-unittest-gate.md`.
>
> **Operator authorization (2026-09-16).** Cycle-4 disposition option **(a)**:
> apply revision 5 **ONLY** to resolve **P1-C4-1**, then run **one focused
> `plan-review` verification over that exact correction**. The override does
> **NOT** reset counters, does **NOT** authorize any broader fix, does **NOT**
> waive P0/P1, and does **NOT** alter any implementation, claim, or closure
> gate. Any P0/P1 found beyond P1-C4-1 halts with no further edits.
>
> | Change | Surface | Nature |
> |---|---|---|
> | Bare `pytest` mandate replaced by `PYTHONPATH=src python -m unittest discover -s tests` (+ PowerShell equivalent), with root `pytest` recorded as withdrawn/non-canonical and `pytest tests/` demoted to a secondary, non-authoritative convenience run | **§3 U6 item 2** | Correction of a non-canonical gate |
> | `` `pytest tests/` green `` → canonical unittest gate green, same demotion and prohibition of bare root `pytest` as a gate | **§8** | Correction of a non-canonical gate |
> | D16's "the plain `python -m unittest discover -s tests` invocation this plan mandates" restated to name the canonical invocation **and** the two surfaces (§3 U6 item 2, §8) that now actually mandate it, with the pre-revision-5 mismatch recorded | **§5 D16** | Removal of a self-contradiction |
> | `097-S` added as a **binding referenced durable learning** with its path, provenance, and binding effect | **§1** | Missing direct reference added |
>
> **Scope guarantees.** No unit, task mapping, decision outcome, freeze-scope
> boundary, closure scope, blast radius, authorization, or claimability is
> changed. No new hardening signal is introduced (`Requires plan hardening`
> remains **yes**, 5/5 — see `## Plan Hardening — Revision-5 Impact Re-check`).
> Revision 5 **narrows** an evidence surface (it removes a gate that could
> falsely block a green shipment) and adds **no** new authority. Task record
> `166.006-T` already stated the correct gate and is **unchanged** — revision 5
> brings the plan into agreement with it, not the reverse.
>
> **Review status.** Verified by the focused, operator-authorized
> `## Plan Review — Cycle 4 Verification Pass (revision 5, focused)` below. The
> cycle-1..3 PASS record and the cycle-4 findings remain of record; revision 5
> is not a fourth fix cycle over the whole plan.

> ## 🔄 REVISION 4 — 2026-09-16 — AUTHORITATIVE, RE-HARDENED
>
> Revision 4 resolves the **four deduplicated P1 groups** raised by the **third
> and final permitted external review-fix cycle** against the revision-3
> package. These are **P1-class plan changes**, so the mandatory `plan-harden`
> impact check was **re-run** — see
> `## Plan Hardening — Revision-4 Impact Re-check`. **Option F, the six units,
> and the 1:1 task mapping are unchanged.**
>
> | Group | Blocker (as raised) | Disposition | Landed in |
> |---|---|---|---|
> | **A** | **Test-granularity contradiction** — the exit matrix said *every test belongs to exactly one class*, yet A2/A3/A9/A10 mixed a **CLASS 4 verdict** assertion (must start **green**) and a **CLASS 1 reason-text** assertion (must start **red**) inside the **same named test**. Such a test can satisfy neither obligation, and the CLASS 4 before/after green pair — the whole containment proof — becomes unobtainable | **Split surgically.** Verdict and diagnostic/reason observables are now **separately named tests**, each declaring **exactly one** class. Class is declared and gated at **test-function granularity**; a CLASS 4 verdict test may not assert on `reason`, and a CLASS 1 reason test may not assert a verdict | §3 U1 exit table + split table, §5 **D16**, §7/§8, **H19**, decision **D11**, `166.002-T`, `166.001-T`, `166.006-T` |
> | **B** | **Incomplete evidence-honesty propagation** — stale fixture-as-engine-proof claims survived on `166-F`, `166.003-T`, `166.004-T`, `166.005-T` and the handoff memory; `166.004-T` still called `returned_ids` and `parent_id` effects **measured facts** | **All residual claims withdrawn.** Every authoritative execution surface now restates **classifier-law / engine-law separation**: pure classifier fixtures prove **only** classifier behaviour; `returned_ids` and `parent_id` clearing are **INDICATIVE and UNPROVEN**, stay **fail-closed**, and **cannot authorize cascade** | §2 **R24**, §5 **D13**, §6 risks, **H17**, decision **D7a**, `166-F`, `166.003-T`, `166.004-T`, `166.005-T`, memory |
> | **C** | **Historical replay/evidence correctness** — decision **D4** still required a **current recorded-manifest** dry-run to reproduce the pre-close **12-ID** result while **D10** withdrew it; **G1** asserted only the *absence* of the excluded siblings (**vacuous**); **G3** claimed the unfiltered `git show --stat e4ca20e5` contains exactly 12 paths and treated `e4ca20e5` as a **close-only** commit | **D4's must-language explicitly superseded/withdrawn** and repointed at G1/G2/G3. **G1 materializes the complete 14-row pre-close shape** from immutable `358b63b4` — `173-S` + its **11** manifest members + excluded descendants **`165.007-T`/`165.010-T`** — all **blob-OID-pinned**, with **non-vacuous** *discovered → parsed canonical `archived` → excluded as inert* assertions. **G3 replaced by explicit path-scoped before/after evidence** between `358b63b4` and `e4ca20e5`, with exact expected transition/rename semantics and explicit unchanged/blob-identity evidence for the two siblings; `e4ca20e5` is recorded as the **combined publication commit (34 paths)** and is **distinguished from** the separately adjudicated **Ship in-workspace verification** | §1, §2 **R16**, §3 U6, §8, Plan Hardening dry-runs, **H20**, decision **D4**/**D7a**/**D10**, `166.006-T`, `166-F`, `174-S`, memory |
> | **D** | **Constitutional workspace containment + destructive cleanup** — revision 3 permitted `tempfile.TemporaryDirectory()` under OS `%TEMP%` (**Constitution IV** violation: a write outside the workspace/cwd) and described its **automatic cleanup** as permitted (**Principle VII** violation: unapproved destructive operation) | **Permission withdrawn in full.** ALL fixture/scratch/backlog/replay workspaces — **including** pure-classifier tests and the **G1 replay** — MUST resolve under the **repository-internal, already-git-ignored** root `.autoharness/staging/tmp/`, guarded by a **canonical resolved-realpath containment check**. **No writes outside cwd.** Scratch directories are **persistent and uniquely named**; deletion only via **capture evidence → halt/P-005 → explicit operator approval → revalidate → approved deletion**. **No surface may describe a self-cleaning tempdir as permitted**, and no automatic deletion authority is invented | §2 **R27**, §3 U1/U6, §5 **D17**, Plan Hardening prechecks, **H21**, decision **D7b**, `166.002-T`, `166.006-T`, `174-S`, memory |
>
> **Every revision-4 change narrows an authorization, deletes a false or
> unprovable claim, or adds a proof obligation. None widens closure scope, blast
> radius, or claimability, and no evidence was fabricated — every new assertion
> is re-derivable from an immutable git object already in this repository.**
>
> **REVIEW-CYCLE ACCOUNTING (read before treating this revision as reviewed).**
> **⚠️ SUPERSEDED BY REVISION 5 — this paragraph states the position AS OF
> revision-4 publication and is retained as a historical record. Cycle 4 was
> SUBSEQUENTLY RUN under an explicit, narrowly scoped one-time operator
> override and returned `decision: FAIL` with one open P1 (**P1-C4-1**); see
> `## Plan Review — Cycle 4 (revision 4, 2026-09-16)`. That P1 is resolved by
> **revision 5**, which was verified by
> `## Plan Review — Cycle 4 Verification Pass (revision 5, focused)`. The
> verdict of record is now that focused verification pass over revision 5, NOT
> cycle 3.**
> `plan-review` has run **three** cycles against this plan (cycle 1 / revision 1,
> cycle 2 / revision 2, cycle 3 / revision 3). The Stage **review-fix cycle
> limit is 3 per plan**, so a **cycle 4 is NOT policy-permitted** and was **NOT
> run, NOT simulated, and NOT relabelled**. The **review verdict of record
> remains cycle 3 over revision 3** and does **not** extend to revision-4 text.
> This is **recorded and halted for operator disposition**, not bypassed — see
> `## Plan Review — Cycle 4 NOT RUN (limit reached)`.

> ## 🔄 REVISION 3 — 2026-09-16 — superseded in part by Revision 4
>
> Revision 3 resolves the **five deduplicated P1 blockers** raised by the
> completed local fix-verification review against the revision-2 package. These
> are **P1-class plan changes**, so the mandatory `plan-harden` impact check and
> `plan-review` were **both re-run** — see
> `## Plan Hardening — Revision-3 Impact Re-check` and
> `## Plan Review — Cycle 3`. **Option F, the six units, and the 1:1 task
> mapping are unchanged.**
>
> | P1 | Blocker (as raised) | Disposition | Landed in |
> |---|---|---|---|
> | 1 | **Unsatisfiable red matrix** — the plan demanded A2–A4, A5-live, A9 and likely A10 fail on current `main`, but the live `missing` predicate already returns `SAFE_CLOSE` naming the offending ID for *every* out-of-manifest descendant | **Reclassified.** New **CLASS 4 containment-regression** (MUST START GREEN, MUST STAY GREEN). Mandatory red is relocated to genuinely-absent observables: the **observed-status** reason text and the **torn-specific** containment reason | §3 U1 exit table, §5 D3/D12, §6 risks, §8, decision **D11**, `166.002-T`, `166.001-T` |
> | 2 | **Engine evidence + containment** — synthetic classifier fixtures cannot re-derive Backlogit 1.10.1 effects; `tempfile.TemporaryDirectory()` violates the new in-repository rule | **Claims narrowed, no evidence fabricated.** CLASSIFIER LAW and ENGINE LAW made disjoint; `returned_ids`/`parent_id`-clearing stay **unproven and blocked**. *(Revision 4: the engine-evidence formulation `git show --stat e4ca20e5` is **withdrawn as factually wrong** and replaced by path-scoped evidence; the containment re-scope is **withdrawn in full** — `%TEMP%` is prohibited for every purpose. See the Revision 4 banner, R24, R27, decision D7a/D7b.)* | §1 provenance, §2 R24, §5 D8/D13, Plan Hardening prechecks, decision **D7a/D7b**, `166.001-T`, `166.002-T`, `166.006-T` |
> | 3 | **173-S retrospective snapshot** — U6/`166.006-T` asked post-close records to predict the pre-close 12-ID result, impossible because `required_ids` is status-sensitive | **Pinned and split.** Immutable pre-close revision **`358b63b4`** (parent of the close commit `e4ca20e5`), SHA-256-digested; gates split **G1 replay / G2 current-state / G3 engine-effect**; the post-close 12-ID assertion is **withdrawn** | §3 U6, §2 R16, §8, Plan Hardening dry-runs, decision **D10**, `166.006-T` |
> | 4 | **Stale operational closure artifact** — `docs/closure/2026-09-14-173-s-165-f-closure.md` still reads `BLOCKED` / `satisfied: false` | **Annotated on Stage-owned surfaces only.** Recorded as a **historical blocked-phase record**; Stage does **not** rewrite Ship-owned closure truth; a **Ship/operator-owned superseding closure record** is a `174-S` readiness prerequisite; the unqualified "P-001 discharged" claim is **withdrawn** | §1 current state, §2 R26, §5 D14, Plan Hardening unresolved decisions, decision **D8a**, `174-S` |
> | 5 | **Exact-status contract vs YAML parser** — "byte-for-byte" is unimplementable because `_frontmatter` uses `yaml.safe_load` | **Narrowed honestly.** Contract becomes **exact parsed-scalar equality** to `"archived"` with no post-parse normalization and **non-`str` fails closed**; the `archived ` (unquoted, trailing space) distinctness claim is **withdrawn as factually wrong**; fail-closed on non-string/malformed/torn/duplicate preserved | §2 R19/R25, §3 U2, §5 D2/D15, §6 risks, decision **D1b**, `166.001-T`, `166.002-T` |
>
> **Every revision-3 change narrows an authorization, deletes an unprovable
> claim, or states an existing limit honestly. None widens closure scope, blast
> radius, or claimability. Nothing was asserted that is not re-derivable from an
> immutable artifact already in this repository.**

> ## 🔄 REVISION 2 — 2026-09-16 — superseded in part by Revision 3
>
> Revision 2 corrects validated local-review blockers in the `e4ca20e5`
> publication package. The changes are **P1-class plan changes**, so the
> mandatory `plan-harden` impact check and `plan-review` were **both re-run** —
> see `## Plan Hardening` (§ Revision-2 impact re-check) and `## Plan Review`
> (cycle 2). Option F, the six units, and the 1:1 task mapping are **unchanged**.
>
> **Every revision-2 change narrows an authorization or states an existing limit
> honestly. None widens closure scope, blast radius, or claimability.**

## 1. Source Understanding

Implements the decision
`docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md`
(**Option F** — flat manifest + engine-inertness containment), which supersedes
`docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md`
(Option E, `TERMINAL_CLOSE`) following a binding operator architectural
correction.

### Referenced durable learnings (compound library)

| Learning | Path | Binding effect on this plan |
|---|---|---|
| **`097-S` — the canonical repository test gate is `unittest`, not root `pytest`** (shipment `097-S`, feature `092-F`, PR 241) | `docs/compound/097-S-canonical-unittest-gate.md` | **BINDING (added revision 5).** The source-validation gate of record for every unit in this plan is `PYTHONPATH=src python -m unittest discover -s tests` (PowerShell: `$env:PYTHONPATH = 'src'; python -m unittest discover -s tests`). Repository-root `pytest` is **not canonical** here — `pyproject.toml` sets only `pythonpath = ["src"]`, with no `testpaths`/`norecursedirs`, so root collection wanders into vendored `references/*` and fails on unrelated import-file-mismatch errors. Mandated in **§3 U6 item 2** and **§8**; relied on by **D16**; already stated by task record `166.006-T`. |

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

> **⚠️ EVIDENCE PROVENANCE (revision 3 — corrected).** The engine-behavior table
> below comes from Stage spike arms run in **external `%TEMP%` workspaces**,
> recorded as a **P-005 containment and destructive-approval violation**
> (decision D7). It is **INDICATIVE, NOT AUTHORITATIVE**. **No acceptance
> criterion in this plan may cite it as sole evidence.**
>
> **Revision 3 withdraws the revision-2 remedy as unsound.** Revision 2 said
> every claim below "MUST be re-derived in-workspace as a hermetic, checked-in
> fixture under `tests/` (unit U1)". That is **impossible**: U1's fixtures are
> **classifier** fixtures — they write synthetic Markdown and call
> `classify_shipment_close_path`, a pure Python function. They **never invoke the
> backlogit engine** and therefore cannot re-derive `archived_ids`,
> `returned_ids`, descendant archival, or `parent_id` clearing. Asserting that
> they do would have been a **fabricated-evidence claim**.
>
> Two **disjoint** evidence classes now govern (decision D7a):
>
> | Class | Proposition | Authoritative evidence | Provable here? |
> |---|---|---|---|
> | **CLASSIFIER LAW** | what `classify_shipment_close_path` returns for a record shape | U1's hermetic checked-in fixtures | **YES** |
> | **ENGINE LAW** | what backlogit 1.10.1 actually mutates/returns/skips | a real, observed, in-repository engine execution | **NO — not by any fixture in this plan** |
>
> **The one ENGINE-LAW proposition authoritatively held**, re-derivable from git
> by anyone at any time.
>
> > **⚠️ REVISION 4 — THE `git show --stat e4ca20e5` FORMULATION IS WITHDRAWN AS
> > FACTUALLY WRONG.** `e4ca20e5` is **`chore(stage): publish flat-manifest
> > closure package`** — a **COMBINED PUBLICATION COMMIT** whose **unfiltered
> > diffstat contains 34 changed paths** (the 12 close-effect paths **plus** the
> > entire Stage publication package). It is **not** a close-only commit, and its
> > unfiltered diffstat does **not** contain exactly 12 paths. Both claims are
> > withdrawn. The evidence is real but must be extracted **path-scoped**:
>
> ```text
> # (a) the 11 manifest members -> expect 11 MODIFIED (no add/delete/rename)
> git diff --stat 358b63b4 e4ca20e5 -- \
>   .backlogit/archive/165-F.md   .backlogit/archive/165.001-T.md \
>   .backlogit/archive/165.002-T.md .backlogit/archive/165.003-T.md \
>   .backlogit/archive/165.004-T.md .backlogit/archive/165.005-T.md \
>   .backlogit/archive/165.006-T.md .backlogit/archive/165.008-T.md \
>   .backlogit/archive/165.009-T.md .backlogit/archive/165.011-T.md \
>   .backlogit/archive/165.012-T.md
>     -> 11 files changed
>
> # (b) the shipment record -> expect EXACTLY ONE entry, RENAME + modify
> git diff --stat -M --find-renames 358b63b4 e4ca20e5 -- \
>   .backlogit/queue/173-S.md .backlogit/archive/173-S.md
>     -> .backlogit/{queue => archive}/173-S.md | 1 file changed
>
> # (c) the two EXCLUDED out-of-manifest siblings -> expect EMPTY output
> git diff --stat 358b63b4 e4ca20e5 -- \
>   .backlogit/archive/165.007-T.md .backlogit/archive/165.010-T.md
>     -> (no output)
>
> # (d) blob identity for (c) -- the POSITIVE (non-vacuous) form of the fact
> git rev-parse 358b63b4:.backlogit/archive/165.007-T.md  # 544c2377b38e9ba2df123f5b8d9bf359dacb89ea
> git rev-parse e4ca20e5:.backlogit/archive/165.007-T.md  # 544c2377b38e9ba2df123f5b8d9bf359dacb89ea
> git rev-parse 358b63b4:.backlogit/archive/165.010-T.md  # 609ad8bc7839fca8b5273d777a6acdc590aacb6f
> git rev-parse e4ca20e5:.backlogit/archive/165.010-T.md  # 609ad8bc7839fca8b5273d777a6acdc590aacb6f
> ```
>
> (a) + (b) are the **12 close-effect paths as a path-scoped subset** of
> `e4ca20e5`. (c) + (d) show `165.007-T`/`165.010-T` — both `parent_id: 165-F`
> descendants declaring `status: archived` at `358b63b4` — are **byte-identical
> across the close**, proved by **matching blob OIDs**, not by mere absence from
> a listing. This establishes **exactly one** engine law — *an out-of-manifest
> sibling declaring `status: archived` is skipped by the cascade* — and that is
> **precisely and only** the law INV-6's inertness grant rests on.
>
> **This is historical, git-derivable evidence.** It is a **distinct** surface
> from the separately adjudicated **Ship in-workspace verification** of the close
> (decision D8); the two MUST NOT be conflated or substituted for one another.
>
> **Explicitly still UNPROVEN, and therefore never citable as fact:** Arm 2's
> `returned_ids: []`-while-archiving (usable as *rationale* for demoting the
> `returned_ids` guard, never as proof), Arm 3/4's `parent_id` clearing
> (**blocked**, follow-up `63363CF5`), and `status: done` descendant archival
> (**not load-bearing** — `done ≠ archived`, so it is non-inert and forces
> `SAFE_CLOSE` regardless). Where an engine behavior is unproven, the dependent
> autoharness behavior **is the fail-closed one**.

The backlogit 1.10.1 engine expands scope hierarchically. Stage spike evidence
(four disposable `%TEMP%` workspaces, all destroyed; see the decision's F3),
**with each row's evidence class labelled (revision 4 — no row may be read as a
measured fact unless its class says PROVEN)**:

| Manifest shape | Out-of-manifest descendant | Engine effect | Evidence class (D7a) |
|---|---|---|---|
| has feature member | declares exact canonical `status: archived` | **inert** — skipped, byte-identical | **PROVEN (ENGINE LAW)** — path-scoped `git diff`/`git rev-parse` between `358b63b4` and `e4ca20e5`, above. The **only** proven row |
| has feature member | `status: done` | archived (out-of-scope mutation) | **INDICATIVE / UNPROVEN** — and **NOT load-bearing**: `done ≠ archived`, so the record is non-inert and forces `SAFE_CLOSE` regardless |
| has feature member | live `queued` | archived, with `returned_ids` reported `[]` | **INDICATIVE / UNPROVEN** — usable as *rationale* for demoting the `returned_ids` guard; **never** citable as measured fact; **cannot authorize cascade** |
| no feature member | live | returned, with `parent_id` cleared | **INDICATIVE / UNPROVEN and BLOCKED** — follow-up `63363CF5`; **cannot authorize cascade** |
| any | ancestor/parent of a manifest item | untouched (no upward walk) | **INDICATIVE / UNPROVEN** |

**Revision-4 rule (binding on every surface): only the first row may be stated
as a measured engine fact. Every other row MUST be presented as indicative and
unproven, the dependent autoharness behaviour MUST be the fail-closed one, and
no unproven row may be used — alone or in combination — to authorize a
`CASCADE`.**

So the descendant walk must be **retained**, but its verdict must change from
*"is it in the manifest?"* (scope) to *"can the engine mutate it?"* (blast
radius). This is the single conceptual change the whole plan implements.

### Current state (revision 3, 2026-09-16)

`173-S` is **closed**: `status: archived`, `archived_status: shipped`,
`commit: 9cc98c41`. It was closed by an **operator-executed, explicitly
authorized administrative close** performed after a **Ship read-only preview**;
Ship then verified in-workspace that exactly **12 paths** changed (the 11 manifest
members + the record), that `165.007-T`/`165.010-T` are **byte-identical**
(`archived_status: blocked`, no `commit:` stamp added), that **zero shipments are
active**, and that `174-S` `pre_claim` **PASSES**. This was **not** a Stage close
and **not** a Ship `shipment-reconcile` run; it is **not** a Stage P-010
violation and MUST NOT be reported as one. The close effect landed in commit
**`e4ca20e5`**; the immutable **pre-close** tree is its parent, **`358b63b4`**.

> **REVISION-4 SCOPE NOTE (P1 group C).** Ship's in-workspace verification above
> is a **separately adjudicated** evidence surface about the **close operation**.
> It is **distinct** from the git-derivable, path-scoped historical evidence in
> §"The safety constraint that must survive" and in U6's **G3**, and the two
> MUST NOT be conflated or substituted for one another. In particular, **no
> surface may infer Ship's 12-path observation from the unfiltered diffstat of
> `e4ca20e5`** — `e4ca20e5` is the **combined publication commit** and contains
> **34** changed paths.

> **⚠️ THE CLOSURE EVIDENCE OF RECORD IS CONTRADICTORY (revision 3, P1-4).**
>
> | Surface | Asserts | Owner |
> |---|---|---|
> | `.backlogit/archive/173-S.md` | `archived` / `shipped` / `9cc98c41` — **closed** | backlogit state |
> | `git diff` path-scoped, `358b63b4` → `e4ca20e5` (D7a / D10 G3) | the 12 close-effect paths changed, both excluded siblings byte-identical — the close **happened**. *(`e4ca20e5` is the **combined publication commit**, 34 paths; the 12 are a path-scoped subset, never its unfiltered diffstat.)* | git (immutable) |
> | `docs/closure/2026-09-14-173-s-165-f-closure.md` | `closure_status: BLOCKED`; condition 2 `satisfied: false`; *"The shipment record remains status: active in backlogit"* | **Ship / operator** |
>
> **Stage's disposition — annotate, do not rewrite:**
>
> 1. The 2026-09-14 artifact is a **historical, blocked-phase, pre-close
>    record**. It was accurate when written and was **overtaken by events** on
>    2026-09-16. It is **not** evidence that `173-S` is open.
> 2. **Stage MUST NOT edit it.** `closure_status` and `satisfied:` are
>    **Ship/operator-owned** fields consumed by
>    `gates.topology._closure_artifact_complete`; Stage flipping either is a
>    **P-010** violation. This plan therefore annotates supersession **only on
>    Stage-owned surfaces** (this plan, the decision, `174-S`, session memory).
> 3. **There is no closure record of record for `173-S`.**
>    `topology.closure_complete()` globs
>    `docs/closure/{shipment_id}-*-post-merge-closure.md`. The stale filename
>    `2026-09-14-173-s-165-f-closure.md` **does not match**, so
>    `closure_complete("173-S")` returns **`None` (not found)**, not `False`. The
>    gate is **not** currently tripped by the stale file — the real gap is that
>    **no matching post-merge closure artifact exists at all**.
> 4. **`174-S`'s `pre_claim` PASS does NOT evidence `173-S` closure.** `174-S` is
>    `labels: [dag-root]` with **empty** `dependencies`, deriving
>    `predecessor_source: declared_root`, so it **never consults** `173-S`'s
>    closure artifact. Citing `pre_claim: PASS` as proof that `173-S` closure is
>    documented is an unsupported inference and is **prohibited**.
> 5. **P-001 is discharged IN FACT but NOT EVIDENCED OF RECORD** — see
>    § "Unresolved operator decisions".
> 6. **Readiness prerequisite (routed, not self-granted):** a
>    **Ship/operator-owned** superseding closure record for `173-S`
>    (conventionally `docs/closure/173-S-165-F-post-merge-closure.md`) carrying
>    the operator-action provenance, the `e4ca20e5` diffstat, and an explicit
>    supersession pointer retiring the 2026-09-14 artifact. **Stage cannot
>    satisfy this and does not claim it is satisfied.**

Consequences for this plan:

* **The defect is NOT retired.** All three defective surfaces are unchanged, and
  the next same-shaped closure (`168-S` / `3CA122AC`) is still blocked. The
  motivation, scope, and unit list are **unchanged**.
* **`173-S` becomes a retrospective regression fixture**, not a live unblock
  target. **Revision 3 (P1-3):** the gate is evaluated against the **immutable
  pre-close pin `358b63b4`**, not against current post-close state — see U6 for
  the G1/G2/G3 split and decision D10. **Revision 4 (P1 group C):** decision
  **D4's** bullet requiring a dry-run over the *current recorded manifest shape*
  to reproduce the pre-close **12-ID** result is **explicitly superseded and its
  must-language withdrawn**; D10's **G1/G2/G3** are the sole operative
  retrospective obligation. Any surface still demanding that recorded-manifest
  reproduction is stale.
* **The P-001 sequencing overlap no longer applies IN FACT** — `174-S`'s claim
  condition 5 ceased to exist by state, not by any Stage grant. **Revision 3:
  it is NOT evidenced of record** while the only closure artifact naming `173-S`
  reads `BLOCKED`; a Ship/operator-owned superseding closure record is a
  readiness prerequisite.
* `173-S`, `165.007-T`, `165.010-T` remain **immutable to this work**.

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
  surfaced as a fail-closed halt and routed upstream as an **external runtime
  prerequisite** (durable active follow-up `7F9CB5E9`).
* **Multi-shipment feature delivery is delivered at the CONTRACT level only**
  (INV-4/INV-5/INV-11). It is **operationally blocked** on `7F9CB5E9`. No unit,
  test, or acceptance criterion in this plan may claim end-to-end split-delivery
  support is complete.
* **R2 (engine `parent_id` clearing on returned siblings)** is tracked by durable
  active follow-up `63363CF5`; mitigations only here, no fix.

## 2. Requirements Trace

| # | Requirement (decision ref) | Unit | Verified by |
|---|---|---|---|
| R01 | INV-1 closure scope = `items(S) ∪ {S}` | U3 | doc-contract test |
| R02 | INV-2 membership explicit/exhaustive | U2, U3 | classifier + doc tests |
| R03 | INV-3 excluded items never gate on ancestry | U2 | `test_archived_out_of_manifest_child_selects_cascade` |
| R04 | INV-3 no disposition note required | U2, U4 | fixture with no `archived_status` still CASCADEs |
| R05 | INV-4 multi-shipment delivery **contract text**; feature last in final manifest | U3 | split-delivery doc-contract test (**text only — NOT an end-to-end split-delivery proof**) |
| R06 | INV-5 feature terminality over *delivered* tasks only (**contract text**) | U3 | doc-contract test |
| R07 | INV-6 engine-inertness gate | U2 | inertness positive + 2 negatives |
| R08 | INV-6 status read from frontmatter, never location | U2 | `archive/`-located, no-`status` fixture → SAFE_CLOSE |
| R09 | INV-7 baseline-invariance replaces baseline-presence | U5 | skill doc-contract test |
| R10 | INV-8 ordering is assembly-only, never a closure gate | U3, U4 | doc-contract test; `173-S` feature-first still CASCADEs |
| R11 | INV-9 DAG orthogonality | U3 | doc-contract test |
| R12 | INV-10 postconditions incl. byte-identity | U4, U6 | two-set gate retained + dry-run |
| R13 | `returned_ids` recorded as **insufficient** | U4 | skill doc-contract test |
| R14 | Arm-2 destructive case blocked **pre-mutation** | U1, U2 | negative classifier tests |
| R15 | Template mirrors byte-parity | U6 | parity test |
| R16 | `173-S` **retrospective** gate over the **immutable pre-close pin `358b63b4`** (revision 3, D10; **G1 composition and G3 formulation REPLACED in revision 4**) | U6 | **G1** replay over the **complete 14-row** pinned snapshot (record + 11 members + `165.007-T`/`165.010-T`) with non-vacuous *discovered → parsed canonical `archived` → excluded as inert* assertions + **G2** current-state (`required_ids` = ∅) + **G3** **path-scoped** `git diff`/`git rev-parse` between `358b63b4` and `e4ca20e5` |
| R17 | `168-S` control fixture | U6 | dry-run control |
| R18 | R1 fail-closed escalation, no silent workaround | U5 | skill doc-contract test |
| **R19** | **D1b — inertness is EXACT PARSED-SCALAR equality to `"archived"`; no post-parse case-folding, stripping, aliasing or coercion may broaden it (revision 3: "byte-for-byte" WITHDRAWN as unimplementable under `yaml.safe_load`)** | **U2** | **variant-status negatives (`Archived`, `ARCHIVED`, YAML-quoted `" archived "`) → SAFE_CLOSE** |
| **R20** | **D1c — full queue+archive scan fails closed on torn/duplicate IDs anywhere, INCLUDING out-of-manifest descendants** | **U2** | **torn out-of-manifest-descendant fixture → SAFE_CLOSE with a TORN-SPECIFIC reason** |
| **R21** | **D1a — manifest / closure / allowed / required sets are distinct and defined; `validated_linked_deliberations` widens `allowed_ids` by zero work items** | **U2, U3** | **doc-contract test + `extras`/`accounted_ids` regression tests** |
| **R22** | **INV-11 — multi-shipment delivery is contract-complete but operationally blocked on external prerequisite `7F9CB5E9`; no surface may claim it works end-to-end** | **U3, U4, U5** | **doc-contract test asserting the prerequisite is stated; NEGATIVE assertion that no surface claims operational split delivery** |
| **R23** | **D6 — every destructive rollback instruction is capture → halt → P-005 → explicit approval → revalidate → approved rollback** | **U5** | **skill doc-contract test; NEGATIVE assertion that no automatic/notification-only revert language remains** |
| **R24** | **D7a — CLASSIFIER LAW and ENGINE LAW are DISJOINT. No fixture, test, or surface may claim a classifier fixture proves an engine behavior. Unproven engine behaviors stay fail-closed and blocked** (revision 3, replacing revision 2's unsound "re-derive every engine claim under `tests/`"). **REVISION 4 EXTENSION:** the separation MUST be restated on **every authoritative execution surface** — plan, decision, `166-F`, **all six task records**, both policy mirrors, both skill mirrors, and the handoff memory. Pure classifier fixtures prove **only** classifier behaviour; `returned_ids` and `parent_id`-clearing MUST NOT be described as *measured* facts and **may not authorize a `CASCADE`** | **U1, U2, U3, U4, U5, U6** | **NEGATIVE doc/test assertion that no engine-effect claim (`returned_ids`, descendant archival, `parent_id` clearing) is sourced to a classifier fixture or stated as measured fact; the single held engine law is sourced to the PATH-SCOPED `git diff`/`git rev-parse` evidence between `358b63b4` and `e4ca20e5`** |
| **R25** | **D1b (revision 3) — the inertness predicate compares the PARSED `status` scalar for exact equality to the `str` `"archived"`; a non-`str` parse (bool/int/`None`/list/mapping) is NOT inert and fails closed; absent `status` is NOT inert** | **U1, U2** | **`status: yes` (bool) and `status:` (null) fixtures → SAFE_CLOSE; existing no-`status` suite stays green** |
| **R26** | **D8a (revision 3) — the 2026-09-14 closure artifact is a HISTORICAL BLOCKED-PHASE record; Stage annotates supersession on Stage-owned surfaces only and MUST NOT rewrite it; a Ship/operator-owned superseding closure record is a `174-S` readiness prerequisite; P-001 is discharged in fact but NOT evidenced of record** | **plan/handoff surfaces only — NO unit** | **§1 current state, § Unresolved operator decisions, `174-S` handoff record; deliberately NOT a test (Stage cannot self-verify a Ship-owned artifact)** |
| **R27** | **D7b (revision 4) — CONSTITUTIONAL WORKSPACE CONTAINMENT. Every fixture, scratch, backlog, or replay workspace created by ANY unit — including pure-classifier unit tests and the G1 replay — MUST resolve under the repository-internal, git-ignored root `.autoharness/staging/tmp/<nonce>/`, guarded by a resolved-realpath `commonpath` containment check that fails closed. NO write of any kind outside the current working directory. `tempfile.TemporaryDirectory()` / `mkdtemp()` / `mkstemp()` / `TMPDIR`-rooted paths are PROHIBITED (Constitution IV), and their automatic cleanup is PROHIBITED (Principle VII). Scratch dirs are PERSISTENT and UNIQUELY NAMED; deletion only via capture → halt/P-005 → explicit operator approval → revalidate → approved deletion** | **U1, U2, U6** | **containment-check unit assertion; NEGATIVE grep across tests + plan + tasks for `TemporaryDirectory`/`mkdtemp`/`mkstemp`/`TMPDIR` and for any "self-cleaning"/auto-delete language; `git check-ignore -v .autoharness/staging/tmp/` confirms the root is ignored** |

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
6. **Exact parsed-scalar variants (R19/R25, CORRECTED in revision 3):**
   `test_titlecase_archived_out_of_manifest_child_falls_back_to_safe_close`,
   `test_uppercase_archived_out_of_manifest_child_falls_back_to_safe_close`, and
   `test_whitespace_padded_archived_out_of_manifest_child_falls_back_to_safe_close`
   — fixtures declaring `Archived`, `ARCHIVED`, and `" archived "` respectively
   → **all expect `SAFE_CLOSE`**.
   **⚠️ FIXTURE-ENCODING REQUIREMENT (revision 3, NON-NEGOTIABLE).** The padded
   variant MUST be written as a **YAML-quoted** scalar — literally
   `status: " archived "` — so it survives `yaml.safe_load` as `" archived "`.
   Written **unquoted** (`status:  archived  `) YAML resolves it to exactly
   `"archived"`, the fixture becomes an *inert* record, and the test would be
   asserting a falsehood. Add a docstring note recording this.
   **Plus two new non-`str` fail-closed fixtures (R25):** `status: yes` (parses
   to the bool `True`) and `status:` (parses to `None`) → **both
   `SAFE_CLOSE`**; the predicate must never `str()`-coerce them.
7. **Torn / duplicate identity (R20, revision 2; reason assertion sharpened in
   revision 3; SPLIT in revision 4):**
   `test_torn_out_of_manifest_descendant_falls_back_to_safe_close` — an
   out-of-manifest descendant present in **both** `queue/` and `archive/`
   (including the case where the `archive/` copy declares `archived` and would
   otherwise read as inert) → asserts **only** `SAFE_CLOSE`. This is **CLASS 4**
   (already green today, because the record is out-of-manifest) and **MUST NOT
   assert on `reason`**. The torn-specific reason text is asserted by a
   **separate** test,
   `test_torn_out_of_manifest_descendant_reason_is_torn_specific`, which is
   **CLASS 1** (genuinely red today — current `main` reports only
   `"has descendants outside the manifest"`) and **MUST NOT assert a verdict**.
   Plus `test_duplicate_id_within_single_root_falls_back_to_safe_close`
   (**CLASS 4**, verdict only).
7b. **CONTAINMENT RELOCATION (R27, NEW in revision 4 — Constitution IV +
   Principle VII).** `tests/test_shipment_closure_classification.py` currently
   builds its per-test scratch backlog with `tempfile.TemporaryDirectory()`,
   which resolves under the OS `%TEMP%`/`TMPDIR` location — **outside the
   repository and outside cwd** — and recursively deletes its tree on context
   exit **without approval**. Both are prohibited. Replace the scratch mechanism
   with a helper that:
   * builds every scratch backlog under
     `<repo_root>/.autoharness/staging/tmp/<unique-nonce>/` (root already
     git-ignored by `.gitignore` line 6 — verify with
     `git check-ignore -v .autoharness/staging/tmp/probe.txt`; **do not** edit
     `.gitignore`);
   * runs the canonical containment check **before the first write**, failing
     closed:

     ```python
     root = Path(os.getcwd()).resolve(strict=True)
     scratch = (root / ".autoharness" / "staging" / "tmp" / nonce).resolve()
     if os.path.commonpath([str(root), str(scratch)]) != str(root):
         raise AssertionError(f"containment violation: {scratch} escapes {root}")
     ```

     Both operands fully **resolved real paths**; `commonpath` /
     `is_relative_to`, **never** a raw string-prefix test;
   * **performs NO cleanup.** No `TemporaryDirectory`, no `mkdtemp`, no
     `mkstemp`, no `rmtree`, no `addCleanup`-delete, no `atexit` hook, no
     fixture teardown deletion. Persistent, uniquely named scratch left in place
     is the **correct terminal state**; deletion is operator-controlled and runs
     only through the D6 sequence.

   Add a **CLASS 3** characterization test asserting the containment check
   rejects an escaping path, and a **CLASS 2** negative doc/grep assertion that
   no surface describes a self-cleaning tempdir as permitted.
8. **Doc-contract tests** in a new `tests/test_flat_manifest_closure_docs.py`
   asserting the D1a set vocabulary and INV-1..INV-11 phrasing is present in
   **both** policy mirrors and **both** skill mirrors, that the strings
   `TERMINAL_CLOSE` and "fully covered" no longer appear as normative
   preconditions, that the `returned_ids`-is-insufficient statement is present
   (R13), that INV-11's external prerequisite is stated (R22), and that the
   approval-gated rollback sequence is stated with **no** automatic or
   notification-only revert language remaining (R23).

**Exit criteria (REWRITTEN in revision 3 — the revision-2 three-class table was
still UNSATISFIABLE; see decision D11).**

Revision 2 designated items 2–7 (A1–A5, R19, R20) as "MUST FAIL RED". Measured
against the current `shipment_closure.py`, that is **false for most of them**.
The live predicate is:

```python
missing = tuple(d for d in descendants if d not in manifest_id_set)
if missing:   # -> SAFE_CLOSE, reason naming the offending IDs
```

So **every** out-of-manifest descendant — live, `done`, `Archived`, `ARCHIVED`,
`" archived "`, torn, or status-less — **already** yields `SAFE_CLOSE` **with the
offending ID in `reason`**. A2, A3, A4, the **live half** of A5, all three A9
variants and both A10 cases are therefore **already green on verdict**, and
demanding they go red would force an author to weaken a correct test.

Every test declares **exactly one** of four classes in its docstring.

> **⚠️ REVISION 4 — THE REVISION-3 MEMBERSHIP ROWS WERE SELF-CONTRADICTORY AND
> ARE REPLACED (P1 group A).** Revision 3 mandated *"every test declares exactly
> one of four classes"* while simultaneously assigning **two** classes to a
> **single named test** for A2, A3, the three A9 variants, and A10: the CLASS 4
> **verdict** assertion (**must start green**) and the CLASS 1 **reason-text**
> assertion (**must start red**) lived in the same test function. Those
> obligations are mutually exclusive for one test — on current `main` it fails,
> which breaks its must-start-green obligation and makes the CLASS 4 before/after
> green pair (the **entire containment proof**, H16) unobtainable.

**GRANULARITY RULE (revision 4, NON-NEGOTIABLE).** Class is declared **and
gated** at **test-function granularity**, and **exactly one class per named
test** holds without exception:

* **No named test may assert both a VERDICT observable and a DIAGNOSTIC/REASON
  observable.** A verdict test asserts only on the returned `ClosePath`; a reason
  test asserts only on `reason` text. Wherever revision 3 bundled them, the test
  is **split into two separately named tests**, each carrying exactly one class.
* A **CLASS 4** verdict test **MUST NOT** assert on `reason` at all — any reason
  assertion makes it red today and destroys its must-start-green property.
* A **CLASS 1** reason test **MUST NOT** assert a verdict — its red must be
  caused by the missing reason text and by nothing else, so that it fails today
  "for its own specific named reason".
* The pair MAY share one fixture-builder helper; it is the **assertions**, and
  therefore the class gating, that must be separated.

**Required split (revision 4):**

| Split source | CLASS 4 test — MUST START GREEN, verdict only | CLASS 1 test — MUST FAIL RED, reason text only |
|---|---|---|
| A2 (`done`) | `test_done_but_not_archived_out_of_manifest_child_falls_back_to_safe_close` | `test_done_but_not_archived_out_of_manifest_child_reason_names_observed_status` |
| A3 (live `queued`) | `test_live_out_of_manifest_child_falls_back_to_safe_close` | `test_live_out_of_manifest_child_reason_names_observed_status` |
| A9 (`Archived`) | `test_titlecase_archived_out_of_manifest_child_falls_back_to_safe_close` | `test_titlecase_archived_out_of_manifest_child_reason_names_observed_status` |
| A9 (`ARCHIVED`) | `test_uppercase_archived_out_of_manifest_child_falls_back_to_safe_close` | `test_uppercase_archived_out_of_manifest_child_reason_names_observed_status` |
| A9 (`" archived "`) | `test_whitespace_padded_archived_out_of_manifest_child_falls_back_to_safe_close` | `test_whitespace_padded_archived_out_of_manifest_child_reason_names_observed_status` |
| A10 (torn) | `test_torn_out_of_manifest_descendant_falls_back_to_safe_close` | `test_torn_out_of_manifest_descendant_reason_is_torn_specific` |

| Class | Meaning | Required initial state | Members |
|---|---|---|---|
| **CLASS 1 — BEHAVIOUR-CHANGING** | asserts a verdict or reason the classifier does **not** yet produce | **MUST FAIL RED** on current `main`, each for its own **specific** named reason — never an import/collection error | **A1** (archived out-of-manifest child → `CASCADE`); **A5a** (archived out-of-manifest **grandchild** → `CASCADE`); the **six split reason-text tests** in the right-hand column above |
| **CLASS 2 — DOC-CONTRACT** | asserts contract text that does not yet exist | **MUST FAIL RED** on current `main` | all of item 8 (`tests/test_flat_manifest_closure_docs.py`) |
| **CLASS 3 — CHARACTERIZATION** | pins behaviour already correct and untouched by this change | **MAY START GREEN** — green is correct | fail-closed defaults, `extras` coverage, `accounted_ids` non-widening, INV-8 ordering (A8), fixture-helper plumbing (A0) |
| **CLASS 4 — CONTAINMENT-REGRESSION** | pins a `SAFE_CLOSE` **verdict** that is correct today and that the *new* predicate could silently re-widen | **MUST START GREEN and MUST STAY GREEN.** A red result here on current `main` means **the test is wrong**, not the code | the **six split verdict tests** in the left-hand column above, plus **A4**, **A5b** (live grandchild), `test_duplicate_id_within_single_root_falls_back_to_safe_close`, and R25's `status: yes` / `status:` null fixtures |

**Why CLASS 4 is not merely CLASS 3.** A CLASS 3 test pins behaviour this plan
does not touch. A CLASS 4 test pins behaviour whose **entire justification is
being replaced underneath it**: today these shapes are rejected for being *out of
manifest*; after U2 they must be rejected for being *non-inert*. The verdict is
identical, but a subtly wrong inertness predicate — a stray `.strip()`, a missing
torn check, a `str()` coercion — flips them to `CASCADE`, a **destructive**
regression. They are the load-bearing guards of this change; their green start is
**positive evidence of containment**, not an absence of evidence.

**Where the genuine red signal lives instead.** U2 requires the reason string to
name the offending IDs **and their observed status**, and requires a
**torn-specific** containment reason. Current `main` emits neither — it emits only
`"has descendants outside the manifest: (...)"`. Asserting that new text is a
**real, non-contrived** red observable: it fails today for a precise, nameable
reason and passes only after the intended change.

**PROHIBITED.** Contriving a failure, weakening an assertion, or re-shaping a
fixture for the sole purpose of driving a CLASS 3 or CLASS 4 test red is
**red-phase falsification**. Mandatory red applies **only** to genuinely missing
or behaviour-changing observables.

The pre-existing suite must still pass **untouched**. Every **CLASS 1** and
**CLASS 2** test must be individually demonstrated red before U2–U5 begin, and
every **CLASS 4** test must be individually demonstrated **green** before U2
begins and **re-run green** after U2 lands — the before/after pair is the
containment proof.

### U2 — Classifier: coverage → inertness containment (`166.001-T`) — size M, complexity high

`src/autoharness/gates/shipment_closure.py`:

1. Extend `_ArtifactRecord` with `status: object | None`, read from frontmatter
   and **stored as parsed** (revision 3: **no normalization, and no `str()`
   coercion**). A **declared-but-unreadable** `status` fails closed exactly as
   the existing malformed-`parent_id` path does.
   **Revision 3 (R25) — the stored value is whatever `yaml.safe_load` produced.**
   It may legitimately be a non-`str` (bool for `status: yes`, `None` for a bare
   `status:`, an int, a list, a mapping). Those are **NOT inert** and MUST fail
   closed; they must never be coerced into a string for comparison.
2. Extend `_build_children_index` to return `(children_index, status_index)` so
   the declared status of **every** backlog record is available without a second
   scan. A malformed record anywhere still invalidates the whole index
   (`None` → `SAFE_CLOSE`). **Revision 2 (R20): the scan MUST cover both
   `queue/` and `archive/` in full and MUST return `None` when any ID resolves
   to more than one record** — two records in one root, or a torn record present
   in **both** roots. This applies to **every** record the scan encounters,
   explicitly **including out-of-manifest descendants**, whose declared status
   would otherwise be ambiguous. A partial, aborted, or ambiguous scan may never
   yield `CASCADE`.
3. **Replace** the coverage predicate:

   ```python
   # WAS: every descendant must be a manifest member (hierarchical closure)
   missing = tuple(d for d in descendants if d not in manifest_id_set)

   # NOW: every out-of-manifest descendant must be ENGINE-INERT (INV-6),
   #      compared as an EXACT PARSED SCALAR against the canonical
   #      str literal (D1b / R19 / R25).
   CANONICAL_INERT_STATUS = "archived"

   def _is_engine_inert(status: object) -> bool:
       # Exact parsed-scalar equality. `is` on the type guard is deliberate:
       # a non-str parse (bool/int/None/list/dict) is NEVER inert and is
       # never str()-coerced. No .lower(), .strip(), casefold, or alias.
       return isinstance(status, str) and status == CANONICAL_INERT_STATUS

   out_of_manifest = tuple(d for d in descendants if d not in manifest_id_set)
   non_inert = tuple(d for d in out_of_manifest if not _is_engine_inert(status_index.get(d)))
   ```

   `non_inert` non-empty → `SAFE_CLOSE`, reason naming the IDs **and their
   observed status** (this observed-status text is the R19/R20 red observable —
   current `main` does not emit it; see U1's exit criteria).

   **Revision 3 — the comparison domain is the PARSED SCALAR, not bytes.**
   Revision 2 said "stored verbatim / byte-for-byte". That was **unimplementable
   and is withdrawn**: every record reaches this code through
   `gates.topology._frontmatter`, which parses with `yaml.safe_load`, and a YAML
   load **erases lexical form** — quoting style and trailing whitespace on a
   plain scalar are gone before any predicate can see them. The specific
   revision-2 claim that unquoted `status: archived ` is a distinct non-inert
   value was **factually wrong**; YAML resolves it to exactly `"archived"`.

   **DO NOT normalize for the purpose of granting inertness.** No `.lower()`, no
   `.strip()`, no casefold, no alias table, no synonym set, no `str()` coercion
   may be applied to the compared value. Normalization *broadens* an
   authorization to destroy out-of-scope artifacts. `Archived`, `ARCHIVED`, the
   YAML-quoted `" archived "`, and every non-`str` parse are **NOT inert** and
   force `SAFE_CLOSE`. (Normalization remains permissible *outside* this
   predicate — e.g. for diagnostics or reason strings — provided it can never
   feed the inertness comparison.)

   **Accepted, documented limitation (revision 3).** Forms that are lexically
   distinct but **YAML-equivalent** collapse together and ARE inert: unquoted
   `status: archived` with trailing spaces, and `status: "archived"`, both parse
   to `"archived"`. This is **correct, not a concession** — the backlogit engine
   also reads these records through a YAML parser, so the parsed scalar is the
   domain in which autoharness and the engine actually agree. **Rejected
   alternative:** a raw-scalar *lexical* parser reading the `status:` line
   pre-YAML. Rejected — it adds a hand-rolled parser surface outside
   `freeze-scope`, can drift from `_frontmatter`, and deliberately diverges from
   the engine's own parse semantics for no measured safety gain.
4. **`accounted_ids` / `extras` must remain unchanged.** `extras` still rejects a
   manifest member that is neither a qualifying root feature nor its descendant.
   *(Do not add inert out-of-manifest descendants to `accounted_ids` — they are
   not manifest members; adding them would silently re-widen closure scope. Per
   D1a/R21 they are not in `manifest_scope`, not in `closure_scope`, and not in
   `required_ids`.)*
5. Update the module docstring to state the flat-manifest contract, the D1a set
   vocabulary, INV-6, D1b's exact-match rule and D1c's torn/duplicate
   fail-closed rule, and to record that the descendant walk is a **blast-radius**
   check.

**Purity preserved**: no git access, no mutation, no backlogit calls.

### U3 — P-015 policy rewrite + mirror (`166.003-T`) — size M, complexity medium

`.github/policies/workflow-policies.md` and
`templates/policies/workflow-policies.md.tmpl` (identical edits):

1. Rewrite the **Statement** in flat-manifest terms: closure scope is the
   manifest's explicit item IDs plus the shipment record; **ancestry never
   expands closure scope**.
2. Replace the "VERIFIED FULLY-COVERED-ROOT EXCEPTION" heading and
   preconditions 1–5 with the **D1a set vocabulary** (`manifest_scope`,
   `closure_scope`, `allowed_ids`, `required_ids`, and the four admission
   conditions for `validated_linked_deliberations`) followed by
   **INV-1..INV-11**, verbatim from the decision.
3. Rewrite **Precondition** and **Required Check** to baseline-**invariance**
   (INV-7) rather than baseline-**presence**.
4. Add a **SUPERSESSION NOTE (2026-09-15, amended 2026-09-16)** withdrawing the
   hierarchical-closure preconditions, naming the operator correction and the
   superseded decision, and preserving the existing 155-S supersession note.
5. State INV-8 explicitly: manifest **ordering** is a Stage assembly convention
   and MUST NOT be evaluated as a closure precondition.
6. **State INV-11 explicitly (R22, revision 2).** Multi-shipment feature delivery
   is **permitted by contract** and **blocked in practice**: an intermediate
   shipment carries no feature member, cannot qualify for `CASCADE`, and there is
   **no safe record transition to `archived_status: shipped`** for that shape in
   backlogit 1.10.1. The policy MUST name this as an **external runtime
   prerequisite** tracked by `7F9CB5E9`, and MUST NOT describe split delivery as
   operationally available. State D1b (exact canonical inertness match) and D1c
   (torn/duplicate fail-closed) as normative.

### U4 — Skill Step 0(c): inertness classification + mirror (`166.004-T`) — size M, complexity medium

`.github/skills/shipment-reconcile/SKILL.md` and
`templates/skills/shipment-reconcile/SKILL.md.tmpl`:

1. Rewrite Step 0(c) to the INV-6 inertness predicate; delete the
   "fully covered"/"nothing extra" coverage wording.
2. Add the engine-behavior table (decision F3) as the stated rationale, **with
   every row labelled by its evidence class (revision 4, R24/H17/H20)**: the
   `status: archived` inertness row is **PROVEN** from the path-scoped
   `358b63b4`→`e4ca20e5` comparison; the other four rows are **INDICATIVE and
   UNPROVEN**. The revision-3 word "measured" is **withdrawn** from this
   instruction — an unproven row may never be written as a measured fact and may
   **never authorize a `CASCADE`**.
3. **Record that `returned_ids` is insufficient** (R13): Arm 2 **reportedly**
   archived a live out-of-manifest task while returning `[]` — an **indicative,
   unproven** observation from the non-authoritative external spike (revision 4:
   the "measured" framing is withdrawn). Step 2's guard is retained but
   explicitly demoted to a secondary check **because** the behaviour is
   unproven; the **pre-mutation** inertness gate is the primary protection and
   does not depend on any unproven row.
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
   `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`, naming R1 and the durable active
   follow-up `7F9CB5E9`, stating that the cascade MUST NOT be substituted (Arms
   3–4 / `63363CF5` clear `parent_id` on returned siblings), that this is an
   **external runtime prerequisite** and therefore **also blocks operational
   multi-shipment delivery (INV-11)**, and routing to the operator/upstream.
   **No silent workaround.**
5. **Step 6 — replace the destructive-rollback language (R23, NEW in revision 2;
   this supersedes revision 1's "preserve Step 6 unchanged" instruction).** Any
   `git restore` / `git revert` / `git checkout --` / `git reset` / deletion
   instruction reachable from safe-close MUST be restated as the D6 sequence, in
   this exact order: **(1) CAPTURE EVIDENCE** (observed deviation, offending IDs,
   actual `archived_ids`/`returned_ids`, `git status --short` plus per-path hash
   diff against the recorded baseline) → **(2) HALT** with no further mutation of
   any kind → **(3) EMIT P-005** with the captured evidence attached →
   **(4) REQUEST EXPLICIT OPERATOR APPROVAL**, naming the exact paths and the
   exact command (operator *notification* is **NOT** approval) →
   **(5) REVALIDATE AFTER APPROVAL** by re-reading the working tree immediately
   before execution and confirming the exact paths and their exact current state
   still match what was approved; any drift returns to step 1 →
   **(6) EXECUTE ONLY THE APPROVED ROLLBACK**, restricted to the approved paths,
   with no broader command and no retry on a different scope. Automatic revert,
   immediate revert, unqualified "revert the commit", and "rollback with operator
   notification" are **PROHIBITED FORMULATIONS** and must not remain anywhere in
   either mirror.

### U6 — Mirror parity, harness validation, read-only dry-runs (`166.006-T`) — size S, complexity medium

1. Add a parity test asserting the two skill mirrors and the two policy mirrors
   agree on the D1a set-vocabulary block and the INV-1..INV-11 block (R15).
2. **Run the CANONICAL repository test gate (revision 5, P1-C4-1):**
   `PYTHONPATH=src python -m unittest discover -s tests` (PowerShell equivalent:
   `$env:PYTHONPATH = 'src'; python -m unittest discover -s tests`), then
   frontmatter/markdown/cross-reference/placeholder validation.

   > **⚠️ Revision 5 — the revision-1..4 instruction "Run `pytest`" is
   > WITHDRAWN as NON-CANONICAL.** Durable learning
   > `docs/compound/097-S-canonical-unittest-gate.md` (shipment `097-S`,
   > feature `092-F`, PR 241) establishes the standard-library `unittest`
   > suite as **the** source-validation gate for this workspace, because
   > `pyproject.toml` `[tool.pytest.ini_options]` declares only
   > `pythonpath = ["src"]` — **no `testpaths`, no `norecursedirs`** — so a
   > repository-root `pytest` invocation wanders into vendored
   > `references/*` content and fails collection with unrelated
   > import-file-mismatch errors, which is **not** evidence that source
   > changes are broken. A path-scoped `pytest tests/` run is permitted
   > **only** as an explicitly **secondary, non-authoritative convenience
   > run**; it is **never** the gate of record, and its result **must not**
   > be recorded as closure evidence in place of the unittest result.
   > Record the unittest result verbatim (for example `Ran NNN tests ... OK`).
   > This matches the gate already stated by task record `166.006-T`.
3. **`173-S` RETROSPECTIVE GATE — PINNED AND SPLIT (R16, REWRITTEN in revision 3;
   decision D10).** No writes.

   > **⚠️ The revision-2 formulation was UNSATISFIABLE and is withdrawn.** It
   > asked a classification over the **current, post-close** records to reproduce
   > the **pre-close** 12-ID result. It cannot: `required_ids` is defined as
   > *"closure_scope members not already truly archived at the pre-close
   > snapshot"*, and **all 12** of those records are now `status: archived`.
   > Evaluated against current state `required_ids` is **∅**, not 12. As written
   > the gate would fail a **correct** implementation, or pressure an implementer
   > into hard-coding the 12.

   **Immutable pin.** The close effect landed in commit **`e4ca20e5`**; the
   pre-close tree is its parent, **`358b63b4`**. Both are immutable git objects
   already in this repository, so the snapshot is reproducible offline and
   without trusting any narrative text.

   > **⚠️ REVISION 4 (P1 group C) — G1 WAS INCOMPLETE AND G3 WAS FACTUALLY
   > WRONG.** G1 materialized only the record and the 11 members and asserted the
   > excluded siblings were *absent from every set* — **vacuous**, since a replay
   > that never materializes `165.007-T`/`165.010-T` satisfies that assertion
   > while proving nothing. G3 asserted the unfiltered `git show --stat
   > e4ca20e5` contains exactly 12 paths and treated `e4ca20e5` as a close-only
   > commit; **`e4ca20e5` is the combined publication commit
   > (`chore(stage): publish flat-manifest closure package`) with 34 changed
   > paths**. Both rows are replaced below.

   **G1 snapshot composition (revision 4, NON-NEGOTIABLE) — 14 rows, pinned by
   git blob OID at `358b63b4`, materialized at their PRE-CLOSE PATHS:**

   | # | Pre-close path at `358b63b4` | Declared `status` | Blob OID at `358b63b4` | Role |
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

   Rows **13–14 are mandatory**, not optional context. Every OID is re-derivable
   with `git rev-parse 358b63b4:<path>`; the executor MUST additionally record
   the **SHA-256** digest of each extracted byte stream in the task output.
   **Preserve the pre-close paths exactly** — the 11 members sat physically in
   `.backlogit/archive/` while still declaring `status: done`, which is itself
   the pre-close corroboration of R08 (*location is never sufficient*). A replay
   that relocates them into `queue/` changes the shape under test and is invalid.
   The scratch backlog MUST be built under the canonical repository-internal
   git-ignored root per **R27 / decision D7b** — **never** an OS temp directory —
   and MUST NOT be auto-deleted.

   **G1 non-vacuous sibling assertions (revision 4, in this order):**

   1. **DISCOVERED** — each of `165.007-T` / `165.010-T` appears in the
      descendant set enumerated from `165-F` (present, resolvable, unambiguous);
   2. **READ** — each resolves to a **parsed** frontmatter `status` that is a
      `str` **exactly equal** to `"archived"` (`isinstance(status, str) and
      status == "archived"`), asserted on the **parsed** value, never on file
      text;
   3. **CLASSIFIED INERT** — each is excluded from the non-inert set **because it
      is inert**; and only then
   4. **ABSENT** — each is absent from `archived_ids`, `required_ids`,
      `allowed_ids`.

   **Assertion 4 alone is INSUFFICIENT and MUST NOT be asserted without 1–3.** An
   absence produced by a record that was never materialized, never discovered, or
   never parsed is a **vacuous pass** and is a **STOP** condition.

   | Gate | Evaluated over | Expectation | Evidence class (D7a) |
   |---|---|---|---|
   | **G1 — historical operation replay** | the **14-row** pinned snapshot above, materialized by `git show 358b63b4:<path>` into a scratch backlog under the canonical repo-internal root (R27), blob-OID- and SHA-256-pinned | verdict `CASCADE`; `required_ids` = 11 members + `173-S` = **12**; `165.007-T`/`165.010-T` **discovered → parsed canonical `archived` → excluded as inert** (assertions 1–3) and only then absent from every set (assertion 4) | CLASSIFIER LAW |
   | **G2 — current-state classification** | the **current** archived records | verdict recorded for regression tracking; `required_ids` = **∅** because all 12 are already truly archived, so a re-close is a **no-op**. **Asserting a 12-ID `archived_ids` here is INVALID and is withdrawn.** | CLASSIFIER LAW |
   | **G3 — historical engine effect, PATH-SCOPED (revision 4)** | four path-scoped invocations between `358b63b4` and `e4ca20e5`: **(a)** `git diff --stat 358b63b4 e4ca20e5 -- <the 11 member paths>`; **(b)** `git diff --stat -M --find-renames 358b63b4 e4ca20e5 -- .backlogit/queue/173-S.md .backlogit/archive/173-S.md`; **(c)** `git diff --stat 358b63b4 e4ca20e5 -- .backlogit/archive/165.007-T.md .backlogit/archive/165.010-T.md`; **(d)** `git rev-parse {358b63b4,e4ca20e5}:<each sibling path>` | **(a)** exactly **11 files changed**, all **modified** — no add, no delete, no rename. **(b)** exactly **one** entry, a **rename-plus-modify** rendered `.backlogit/{queue => archive}/173-S.md` (the record transitions `queue/ → archive/` and its content changes). **(a)+(b)** = the **12 close-effect paths as a PATH-SCOPED SUBSET**. **(c)** **empty output**. **(d)** **identical blob OIDs at both commits** (`544c2377…`, `609ad8bc…`) — the positive, non-vacuous form of "unchanged". **`e4ca20e5` MUST NOT be called a close-only commit, and its UNFILTERED diffstat MUST NOT be claimed to contain exactly 12 paths — it is the combined publication commit and contains 34.** This is **historical git evidence**, **distinct from** the separately adjudicated **Ship in-workspace verification** | ENGINE LAW — immutable, reproducible, **already satisfied** |

   **Reproducibility requirement (NON-NEGOTIABLE).** G1's snapshot MUST be
   materialized from `358b63b4` (or an equivalent checked-in fixture carrying the
   same blob OIDs and SHA-256 digests), and the digests MUST be recorded in the
   task output so the gate is re-runnable later and cannot silently drift with
   the working tree. **No expectation in G1/G2/G3 may be hard-coded as a bare
   assertion without its pinned source.**

   **STOP, DO-NOT-SHIP** if: G1 returns anything but `CASCADE`; G1's
   `required_ids` ≠ the pinned 12; G1's snapshot omits either excluded sibling;
   either sibling passes only on absence without assertions 1–3; either sibling
   appears in **any** G1 set; G2 is asserted against the withdrawn 12-ID
   expectation; any G3 sub-command deviates from its stated expectation; or any
   surface re-asserts the withdrawn unfiltered-diffstat/close-only-commit claim.

   **Honest limit (revision 3).** G1 proves the **classifier** agrees with the
   recorded pre-close shape. It does **not** re-prove the **engine's** 12-path
   effect — that is G3's job, and G3 is satisfied by an immutable git artifact,
   **not** by any fixture in this plan.
4. **`168-S` control dry-run** (R17) — classify only; **any** unexpected
   `CASCADE` grant with a non-inert out-of-manifest descendant is a **STOP,
   DO-NOT-SHIP** condition. This is the **live forward-looking** control.
5. Verify `173-S`, `165.007-T`, `165.010-T` are byte-identical to `HEAD`
   (they are archived records and **immutable to this work**).
6. **Split-delivery honesty check (R22).** Assert that **no** surface —
   policy, skill, plan, task, or shipment record — claims multi-shipment
   delivery is operationally complete, and that each surface stating INV-4/INV-5
   also states INV-11's external prerequisite `7F9CB5E9`.

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
* **D2 — Inertness is keyed on EXACT PARSED-SCALAR equality to `"archived"`
  alone** (revision 3, correcting revision 2's "exact canonical literal /
  byte-for-byte"). Not on `archived_status`, not on a disposition note, not on
  location, **not on a normalized form**, and **never on a `str()`-coerced
  non-string**. This is exactly what the engine's `archiveItems()` skip-condition
  keys on, and exactly what INV-3 permits us to demand. Case-folding or stripping
  would grant inertness to values whose engine behavior has **not** been
  observed, i.e. it would broaden an authorization to destroy out-of-scope
  artifacts — the opposite of fail-closed.
* **D3 — The existing negative test suite survives unchanged.** `_write_artifact`
  writes no `status` field, so every existing out-of-manifest fixture is
  *non-inert* under INV-6 and still yields `SAFE_CLOSE`; each assertion checks
  only `close_path` and that the offending ID appears in `reason`, both of which
  still hold. Migration is therefore **purely additive** — a strong
  backward-compatibility signal, and the reason no test file is rewritten.
  *(Revision 3: this is why those tests are **CLASS 3 characterization** and are
  **expected to start green**. It is a separate point from why the new
  out-of-manifest negatives start green — those are **CLASS 4
  containment-regression**, green because the *current* `missing` predicate
  already rejects them; see D12 and U1's exit criteria.)*
* **D4 — Reframe `166-F` in place.** A replacement shipment would require a new
  operator `dag-root` authorization, which this session is forbidden to expand.
* **D5 — R1 is not solved by substitution.** For a genuine `SAFE_CLOSE`
  shipment there is no safe path to `archived_status: shipped` in 1.10.1; the
  honest engineering answer is a fail-closed halt plus an upstream request.
* **D6 — Split delivery is shipped as CONTRACT, not as CAPABILITY** (revision 2).
  Writing INV-4/INV-5 into the policy and skill is real, verifiable work and it
  discharges the operator's product invariant **at the contract level**. It does
  **not** make split delivery usable, because D5's gap is exactly what an
  intermediate shipment hits. The plan therefore states INV-11, names the
  external prerequisite `7F9CB5E9`, and **narrows R05/R06 to doc-contract text
  assertions**. Rejected alternative: claiming end-to-end split-delivery support
  on the strength of contract text alone — that would be a false acceptance
  claim, and the first real split delivery would fail at closure.
* **D7 — Torn/duplicate identity is a fail-closed condition, not an edge case**
  (revision 2). A torn out-of-manifest descendant has an **ambiguous declared
  status**; granting `CASCADE` on the basis of whichever copy the scan happened
  to read last would make a destructive authorization depend on filesystem
  iteration order. The full two-root scan must therefore reject non-unique ID
  resolution outright.
* **D8 — Spike evidence is not proof** (revision 2, **narrowed in revision 3**).
  The `%TEMP%` spike arms are recorded as a P-005 containment/destructive-approval
  violation and demoted to indicative. **Revision 3 withdraws the claim that
  U1's fixtures are "the authoritative, auditable, re-runnable record of the
  engine law"** — they are the authoritative record of the **classifier** law
  only (see D13). The authoritative record for the one held **engine** law is the
  **path-scoped** `git diff`/`git rev-parse` evidence between `358b63b4` and
  `e4ca20e5` (**revision 4** — the revision-3 `git show --stat e4ca20e5`
  formulation is withdrawn as factually wrong; `e4ca20e5` is the combined
  publication commit, 34 paths); the authoritative record for the `173-S` shape
  is the operator close plus Ship's **separately adjudicated** in-workspace
  verification.
* **D12 — CLASS 4 containment-regression is a distinct test class** (revision 3;
  decision D11). A CLASS 3 characterization test pins behaviour this plan does
  not touch. A CLASS 4 test pins a `SAFE_CLOSE` verdict whose **justification is
  being replaced underneath it** — today "out of manifest", after U2 "non-inert".
  A subtly wrong inertness predicate flips it to `CASCADE`, a destructive
  regression. Requiring these to **start green and stay green**, with the
  before/after pair recorded, is stronger evidence than a contrived red would be.
  Rejected alternative: forcing them red by reshaping fixtures — that is
  red-phase falsification and would have *weakened* the suite.
* **D13 — CLASSIFIER LAW and ENGINE LAW are disjoint** (revision 3; decision
  D7a). A fixture that writes synthetic Markdown and calls a pure Python function
  can prove what **autoharness** does; it can prove nothing about what the
  **backlogit Go engine** does. Revision 2's R24 conflated the two and would have
  had the plan assert fabricated evidence. The correction: the inertness grant
  rests on **one** engine proposition, and that proposition is evidenced by
  immutable in-repository git artifacts — **revision 4:** the **path-scoped**
  `git diff`/`git rev-parse` comparison between `358b63b4` and `e4ca20e5`
  showing two `status: archived` out-of-manifest siblings with **identical blob
  OIDs** across the close (the revision-3 "unfiltered `e4ca20e5` diffstat"
  wording is withdrawn; `e4ca20e5` is the **combined publication commit**).
  Every other engine behaviour stays **unproven**, is cited only as *rationale*,
  **is never described as a measured fact, and may never authorize a `CASCADE`**;
  where a behaviour is unproven the dependent autoharness behaviour is
  **fail-closed**.
  Rejected alternative: build a live in-repo engine-characterization harness
  inside this shipment — it is new surface outside `freeze-scope`, needs explicit
  destructive approval, and is not required for U1–U6 correctness; carried as
  follow-up P2-3 instead.
* **D14 — Stage annotates closure supersession; Stage does not rewrite it**
  (revision 3; decision D8a). `closure_status` and `satisfied:` in
  `docs/closure/**` are **Ship/operator-owned** fields consumed by
  `gates.topology._closure_artifact_complete`. Stage editing them is **P-010**.
  So the contradictory 2026-09-14 artifact is left **untouched**, is recorded as
  a **historical blocked-phase record** on Stage-owned surfaces, and a
  **Ship/operator-owned superseding closure record** is registered as a `174-S`
  readiness prerequisite. Rejected alternative: "Stage annotates supersession
  in-file without changing closure status" — rejected because even an
  annotation inside a Ship-owned closure artifact edits the artifact whose
  frontmatter is gate-consumed, and a reader would reasonably treat a
  Stage-authored line there as closure truth.
* **D15 — The safety predicate is narrowed to parsed-scalar equality rather than
  authorizing a lexical parser** (revision 3; decision D1b). Given
  `_frontmatter`'s `yaml.safe_load`, a byte-level contract is unreachable. Of the
  two honest options — (a) authorize a raw-scalar lexical parser as a new
  implementation surface, or (b) narrow the predicate to exact parsed-scalar
  equality — **(b) is adopted**: it is inside `freeze-scope`, adds no parser to
  maintain, and matches the domain the engine itself parses in. The accepted
  limitation (YAML-equivalent lexical variants collapse to inert) is documented
  rather than hidden, and fail-closed behaviour for non-string, malformed, torn,
  and duplicate records is **preserved and extended**.
* **D16 — Class is gated at TEST-FUNCTION granularity, and mixed observables are
  SPLIT rather than re-labelled** (revision 4; decision D11). Revision 3 demanded
  *exactly one class per test* while placing a CLASS 4 verdict assertion
  (must-start-**green**) and a CLASS 1 reason assertion (must-start-**red**) in
  the same named test for A2/A3/A9/A10 — an unsatisfiable pairing that also
  destroys the CLASS 4 before/after green pair, i.e. the entire containment
  proof (H16). Two honest options existed: **(a)** keep one test per fixture and
  define/gate class at **assertion** granularity, or **(b)** split verdict and
  diagnostic observables into **separately named single-class tests**. **(b) is
  adopted**, per the reviewer's stated preference for mechanically verifiable
  red/green evidence: a per-test pass/fail result is directly observable by the
  runner and by CI, whereas assertion-level gating would require a bespoke
  harness to attribute a single test's failure to one of its assertions — new
  surface outside `freeze-scope`, and unverifiable by the canonical
  `PYTHONPATH=src python -m unittest discover -s tests` invocation this plan
  mandates in **§3 U6 item 2** and **§8** (revision 5: that mandate is now
  stated there in exactly these terms — before revision 5 those two surfaces
  mandated `pytest`, so this justification referenced an invocation the plan did
  not in fact mandate; see **P1-C4-1** and `097-S`). The split costs six extra
  test functions, adds no new module, and leaves U1 within `size: M`.
* **D17 — Workspace containment is absolute; cleanup authority is not delegated**
  (revision 4; decision D7b, Constitution IV + Principle VII). Revision 3
  permitted an OS-`%TEMP%` tmpdir for hermetic unit tests on the reasoning that
  hermeticity made it harmless. That conflated two distinct properties:
  hermeticity constrains *what the process reads*, containment constrains *where
  the process writes*. A write outside cwd is a containment breach however
  hermetic the writer, so the permission is **withdrawn** and all scratch is
  relocated under the already-ignored `.autoharness/staging/tmp/`. Separately,
  `TemporaryDirectory()`'s on-exit recursive delete is an **unapproved
  destructive operation**; describing it as "self-cleaning" renames the problem
  rather than solving it. Of the two options — **(a)** keep automatic cleanup but
  contain the path, or **(b)** contain the path **and** remove all automatic
  deletion — **(b) is adopted**: Principle VII admits no agent-side exemption for
  "small" or "temporary" deletions, and a persistent uniquely-named scratch
  directory is inspectable evidence rather than a vanished one. Accumulated
  scratch is accepted as an **operator-controlled hygiene matter**; this plan
  invents **no** deletion authority and routes any deletion through D6.

## 6. Risks and Caveats

| Risk | Mitigation |
|---|---|
| Implementer restores the coverage check "for safety" | U1 pins the inverted expectation *first*; the `173-S` positive fixture fails if coverage returns |
| `accounted_ids` widened to include inert descendants | Explicit U2 step 4 prohibition + `extras` regression tests |
| Inertness inferred from `archive/` location | R08 fixture: `archive/`-located, no `status` → `SAFE_CLOSE` |
| **Inertness broadened by status normalization** | **R19: exact canonical compare; `Archived`/`ARCHIVED`/`" archived "` negative fixtures must all yield `SAFE_CLOSE`; U2 step 3 forbids `.lower()`/`.strip()` in the predicate** |
| **Torn/duplicate ID silently trusted, making a destructive verdict depend on scan order** | **R20: full two-root scan returns `None` on any non-unique ID resolution, including out-of-manifest descendants; dedicated torn-descendant fixture** |
| Policy/skill mirrors drift | U6 parity test over the set-vocabulary and INV blocks |
| Dry-run mutates `173-S` | Read-only by construction; `173-S` is an archived, immutable retrospective fixture; byte-identity re-verified against `HEAD` |
| R1 silently worked around with the cascade | New explicit failure code + skill prohibition citing Arms 3–4 / `63363CF5`; durable active follow-up `7F9CB5E9` |
| **Split delivery advertised as working when it is not** | **R22: INV-11 stated on every surface that states INV-4/INV-5; R05/R06 narrowed to contract-text assertions; U6 item 6 negative check that no surface claims operational completeness** |
| **A destructive rollback is executed automatically or on notification only** | **R23 / D6 six-step approval-gated sequence replaces every such instruction; U1 item 8 asserts no prohibited formulation remains in either mirror** |
| **Red phase weakened by contriving failures in correct characterization tests** | **U1's revision-3 four-class exit criteria; CLASS 3 and CLASS 4 are explicitly permitted — and required — to start green; red-phase falsification is named and prohibited** |
| **Spike-only evidence treated as proof** | **R24 / D8 / D13: CLASSIFIER LAW and ENGINE LAW disjoint; the single held engine law sourced to the PATH-SCOPED `git diff`/`git rev-parse` evidence between `358b63b4` and `e4ca20e5`; F3 marked non-authoritative; `returned_ids` and `parent_id`-clearing are INDICATIVE/UNPROVEN, may not be stated as measured fact, and MAY NOT AUTHORIZE A CASCADE; unproven engine behaviours stay fail-closed and blocked (revision 4)** |
| **A classifier fixture is cited as proof of an engine behaviour** | **R24 negative assertion; no `returned_ids` / descendant-archival / `parent_id`-clearing claim may be sourced to `tests/`** |
| **Status contract asserts a distinction the parser cannot see** | **R19/R25 / D15: exact PARSED-scalar equality; non-`str` fails closed; the padded fixture MUST be YAML-quoted or it silently becomes an inert record and asserts a falsehood** |
| **`173-S` retrospective gate evaluated against status-sensitive post-close state** | **R16 / D10: immutable pre-close pin `358b63b4`, SHA-256-digested; G1/G2/G3 split; the post-close 12-ID assertion withdrawn** |
| **A contradictory Ship-owned closure artifact is read as current truth, or is "fixed" by Stage** | **R26 / D14: recorded as a historical blocked-phase record on Stage-owned surfaces only; Stage MUST NOT edit `docs/closure/**`; superseding Ship/operator record registered as a `174-S` readiness prerequisite** |

### Negative scenarios to add to the Scenario Matrix (U5)

1. Out-of-manifest descendant `status: done` → `SAFE_CLOSE`.
2. Out-of-manifest descendant live `queued` → `SAFE_CLOSE`.
3. Out-of-manifest descendant in `archive/` with no `status` → `SAFE_CLOSE`.
4. Out-of-manifest **grandchild** live → `SAFE_CLOSE`.
5. Protected artifact archived **at baseline** → recorded, **not** a halt.
6. Protected artifact changed **during** the run → halt (INV-7).
7. Partial shipment, `move --status shipped` refused →
   `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`, cascade **not** substituted.
8. **(revision 2)** Out-of-manifest descendant declaring a **non-canonical status
   variant** (`Archived`, `ARCHIVED`, `" archived "`) → `SAFE_CLOSE`.
9. **(revision 2)** Out-of-manifest descendant with **torn identity** (present in
   both `queue/` and `archive/`) → `SAFE_CLOSE`, even when the `archive/` copy
   alone would read as inert.
10. **(revision 2)** Deviation detected after mutation → the D6 sequence fires
    (capture → halt → P-005 → explicit approval → revalidate → approved
    rollback); an automatic or notification-only revert is a **failure** of this
    scenario.
11. **(revision 2)** Intermediate shipment of a split delivery (no feature member)
    reaches closure → halts on INV-11 / `7F9CB5E9`; **no** surface reports split
    delivery as operationally supported.

## 7. Plan Hardening Signals (REQUIRED)

| Signal | Present | Evidence |
|---|---|---|
| Touches a NON-NEGOTIABLE policy | **yes** | P-015 statement + preconditions rewritten; D1a vocabulary and INV-11 added |
| Touches a safety classifier | **yes** | `shipment_closure.py` verdict predicate |
| Multi-surface blast radius | **yes** | classifier + policy ×2 + skill ×2 + tests |
| Changes a destructive-op gate | **yes** | governs when the cascade op may run **and** (revision 2) rewrites the rollback gate |
| External tool behavior dependency | **yes** | backlogit 1.10.1 engine semantics; INV-11 declares an external *prerequisite* |

**Requires plan hardening: yes** — revision 1: 4 of 5; **revision 2: 5 of 5**;
**revision 3: 5 of 5**; **revision 4: 5 of 5**; **revision 5: 5 of 5, unchanged**
(P-006 mandatory; re-run for each P1-class revision — see
`## Plan Hardening — Revision-2 Impact Re-check`,
`## Plan Hardening — Revision-3 Impact Re-check`,
`## Plan Hardening — Revision-4 Impact Re-check` and
`## Plan Hardening — Revision-5 Impact Re-check`).

## 8. Runtime Verification and Closure

* **CANONICAL GATE (revision 5, P1-C4-1):**
  `PYTHONPATH=src python -m unittest discover -s tests` green (PowerShell
  equivalent: `$env:PYTHONPATH = 'src'; python -m unittest discover -s tests`),
  including the new inertness suite and the revision-2/3 exact-match, non-`str`,
  and torn-identity fixtures. The revision-1..4 wording "`pytest tests/` green"
  is **WITHDRAWN** as non-canonical per durable learning
  `docs/compound/097-S-canonical-unittest-gate.md`; a path-scoped `pytest tests/`
  run remains permissible only as a **secondary, non-authoritative convenience
  run** and may **never** substitute for the unittest result as closure evidence.
  A repository-root bare `pytest` is **PROHIBITED** as a gate here: it collects
  vendored `references/*` tests and can falsely block a green shipment.
* **Every CLASS 1 / CLASS 2 test demonstrated RED before U2–U5 begin; every
  CLASS 4 test demonstrated GREEN before U2 and re-run GREEN after — the
  before/after pair is the containment proof (revision 3). Revision 4: this is
  only obtainable because verdict and reason observables now live in
  SEPARATELY NAMED single-class tests (D16/H19); no named test may carry two
  classes.**
* Frontmatter, markdown, cross-reference, and unresolved-placeholder validation on
  all four contract files.
* Mirror parity test green over the D1a set-vocabulary and INV-1..INV-11 blocks.
* **`173-S` gate: G1 replay over the pinned 14-row `358b63b4` snapshot (record +
  11 members + both excluded siblings) returns `CASCADE` with `required_ids` =
  the pinned 12, and both siblings are DISCOVERED, parsed to canonical
  `archived`, and excluded as INERT before being asserted absent; G2
  current-state reports `required_ids` = ∅ (no-op) and asserts NO 12-ID
  expectation; G3's four PATH-SCOPED commands each reproduce their stated
  expectation between `358b63b4` and `e4ca20e5` (11 modified members; one
  rename-plus-modify of the record; empty sibling diff; identical sibling blob
  OIDs).**
* **No surface claims the unfiltered `git show --stat e4ca20e5` contains exactly
  12 paths, and no surface calls `e4ca20e5` a close-only commit.**
* `168-S` control dry-run does not grant an unsafe `CASCADE`.
* Non-canonical-status, non-`str`-status, and torn-descendant dry-runs all return
  `SAFE_CLOSE`.
* **No surface claims a classifier fixture proves an engine behavior, and no
  surface states `returned_ids` or `parent_id` effects as measured fact; the
  single held engine law is sourced to the path-scoped `358b63b4`→`e4ca20e5`
  evidence and nothing else.**
* **Containment (R27): every scratch/fixture/replay workspace resolves under
  `.autoharness/staging/tmp/` with the resolved-realpath check green; a negative
  grep for `TemporaryDirectory`/`mkdtemp`/`mkstemp`/`TMPDIR` and for
  self-cleaning/auto-delete language returns only withdrawal notices.**
* No surface claims operational multi-shipment delivery; every INV-4/INV-5
  statement carries INV-11 and names `7F9CB5E9`.
* No automatic, immediate, or notification-only destructive-rollback language
  remains in either skill mirror.
* **No file under `docs/closure/**` is modified by this shipment.**
* `git status` shows no modification to `173-S`, `165.007-T`, `165.010-T`, and
  preserves the untracked
  `docs/bugs/2026-09-13-autoharness-append-only-plan-review-loop-bug-report.md`.

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
| **H10** | **Inertness is granted only on the exact canonical `archived`; no normalization may broaden it** | `test_titlecase_archived_..._safe_close`, `test_uppercase_archived_..._safe_close`, `test_whitespace_padded_archived_..._safe_close` |
| **H11** | **Any non-unique ID resolution across the full `queue/`+`archive/` scan fails closed, including out-of-manifest descendants** | `test_torn_out_of_manifest_descendant_..._safe_close`, `test_duplicate_id_within_single_root_..._safe_close` |
| **H12** | **No surface claims multi-shipment delivery is operationally complete; every INV-4/INV-5 statement carries INV-11** | doc-contract test (R22) + U6 item 6 negative check |
| **H13** | **No automatic, immediate, or notification-only destructive-rollback language survives in either skill mirror** | doc-contract negative assertion (R23) |
| **H14** | **The classifier's postcondition vocabulary keeps `manifest_scope`/`closure_scope`/`allowed_ids`/`required_ids` distinct; `validated_linked_deliberations` adds zero work items** | `extras`/`accounted_ids` regression tests + doc-contract test (R21) |
| **H15** | **A non-`str` parsed `status` (bool/int/`None`/list/mapping) is NEVER inert and is never `str()`-coerced** | `status: yes` and bare `status:` fixtures → `SAFE_CLOSE` (R25) |
| **H16** | **The CLASS 4 containment set stays `SAFE_CLOSE` across the U2 predicate replacement** | every CLASS 4 test demonstrated green **before** U2 and re-run green **after** — the before/after pair is the proof (D12). **Revision 4:** obtainable only because CLASS 4 verdict tests are now separately named and assert **no** `reason` text (H19) |
| **H19** | **(revision 4)** **Exactly one class per named test, gated at test-function granularity.** No test asserts both a verdict observable and a diagnostic/reason observable; CLASS 4 verdict tests never assert on `reason`; CLASS 1 reason tests never assert a verdict | the six split verdict/reason pairs (D16/U1 split table); a class-declaration lint over every test docstring in both test modules |
| **H20** | **(revision 4)** **No surface claims the unfiltered `git show --stat e4ca20e5` contains exactly 12 paths, or that `e4ca20e5` is a close-only commit; the held engine law rests only on PATH-SCOPED before/after evidence between `358b63b4` and `e4ca20e5`, and G1's replay proves sibling inertness NON-VACUOUSLY (discovered → parsed canonical `archived` → excluded as inert), never by bare absence** | U6 G1 assertions 1–4 + G3's four path-scoped commands; negative grep for the withdrawn diffstat/close-only formulations (R16/R24) |
| **H21** | **(revision 4)** **No write of any kind occurs outside the current working directory. Every scratch/fixture/replay workspace resolves under `.autoharness/staging/tmp/<nonce>/` and passes the resolved-realpath containment check; no automatic deletion of any workspace occurs anywhere** | containment-check unit assertion; negative grep for `TemporaryDirectory`/`mkdtemp`/`mkstemp`/`TMPDIR`/`rmtree`/self-cleaning language (R27, Constitution IV + Principle VII) |
| **H17** | **No classifier fixture is cited as proof of an engine behaviour, and no surface states `returned_ids` or `parent_id` effects as measured fact; the single held engine law traces to the PATH-SCOPED `358b63b4`→`e4ca20e5` evidence. Unproven engine behaviour is indicative + fail-closed and CANNOT authorize a `CASCADE` (revision 4)** | R24 negative assertion over plan/task/skill/policy/feature/memory surfaces (D7a/D13) |
| **H18** | **No file under `docs/closure/**` is modified by this shipment** | `git status` / diff check in U6 item 7 (D14/R26) |

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
  the inertness law is version-specific. **Revision 3:** if the engine version
  changes, the single held **ENGINE LAW** (D7a) must be re-established from a
  real observed close — **not** from any `tests/` fixture, which can only
  re-derive **CLASSIFIER LAW**.
* Single worktree on the working branch (P-016 verified).
* **CONTAINMENT (RE-SCOPED in revision 3; REPLACED IN REVISION 4; decision
  D7b).**

  > **⚠️ REVISION 4 — THE REVISION-3 `PERMITTED` CARVE-OUT IS WITHDRAWN IN
  > FULL.** Revision 3 permitted *"an OS-temp scratch directory used by a
  > read-only, hermetic, self-cleaning Python unit test"* and asserted that
  > relocating it *"would add git-ignore surface and buy zero auditability"*.
  > Both are wrong. **(i) Constitution IV — workspace containment:** an OS
  > `%TEMP%`/`TMPDIR` path resolves **outside this repository and outside cwd**;
  > hermeticity and tool-freeness describe *what the test does* and are **not**
  > containment arguments. **(ii) Constitution Principle VII —
  > destructive-operation approval:** `tempfile.TemporaryDirectory()` performs an
  > **automatic, unapproved, recursive deletion** on context exit; "self-cleaning"
  > names an unapproved destructive operation rather than excusing one. And **no
  > git-ignore surface needs adding** — the canonical root below is *already*
  > ignored.

  * **PROHIBITED — for ANY purpose in this plan, including pure classifier unit
    tests and the G1 replay:** `tempfile.TemporaryDirectory()`,
    `tempfile.mkdtemp()`, `tempfile.mkstemp()`, `TMPDIR`/`%TEMP%`-rooted paths,
    any path resolving outside cwd, **any write outside cwd**, out-of-repository
    workspaces in which the backlogit engine is executed, and **any** automatic,
    implicit, on-exit, `atexit`, teardown, or "best-effort" deletion of a scratch
    workspace.
  * **REQUIRED — canonical repository-internal scratch root:**

    ```text
    <repo_root>/.autoharness/staging/tmp/<unique-run-or-test-nonce>/
    ```

    Already git-ignored by `.gitignore` line 6 (`.autoharness/staging/`),
    confirmed with `git check-ignore -v .autoharness/staging/tmp/probe.txt`
    (exit 0). **No `.gitignore` change is required and none is authorized.**
  * **REQUIRED — canonical containment check**, run **before the first write**
    and **failing closed**:

    ```python
    root = Path(os.getcwd()).resolve(strict=True)
    scratch = (root / ".autoharness" / "staging" / "tmp" / nonce).resolve()
    if os.path.commonpath([str(root), str(scratch)]) != str(root):
        raise AssertionError(f"containment violation: {scratch} escapes {root}")
    ```

    Both operands fully **resolved real paths**; comparison via `commonpath` or
    `is_relative_to` — a raw string-prefix test is **NOT** sufficient.
  * **REQUIRED — cleanup is operator-controlled.** Scratch directories are
    **persistent and uniquely named**; leaving them in place is the **correct
    terminal state**. No unit may delete, prune, truncate, or `rmtree` them.
    Deletion only via the **D6** sequence: capture evidence → **HALT** → emit
    **P-005** → request **explicit operator approval** → **revalidate** exact
    paths and state → execute **only** the approved deletion. Accumulated scratch
    is an operator hygiene matter, never an agent-invented deletion authority.
  * **CONDITIONAL, AND STILL NOT AUTHORIZED HERE** — a real engine
    characterization additionally requires an explicit time-boxed P-016
    declaration and **explicit operator destructive approval before creation**.
    **NOT authorized by this plan and NOT in `174-S`** — follow-up P2-3.
* **No file under `docs/closure/**` may be modified by any unit of this plan**
  (revision 3, D14 — Ship-owned closure truth).
* Unrelated dirty worktree state must be preserved — specifically the untracked
  `docs/bugs/2026-09-13-autoharness-append-only-plan-review-loop-bug-report.md`.

### Target dry-run scenarios with STOP conditions

1. **`173-S` retrospective (revision 3, PINNED + SPLIT; G1/G3 REPLACED in
   revision 4)** →
   **G1** over the immutable **14-row** pre-close snapshot from `358b63b4`
   (`173-S` + 11 members + `165.007-T`/`165.010-T`, blob-OID-pinned, materialized
   under the canonical repo-internal scratch root per R27): expect `CASCADE`,
   `required_ids` = the pinned **12**, containment-clean, and both siblings
   **discovered → parsed canonical `archived` → excluded as inert** before being
   asserted absent. **STOP** on `SAFE_CLOSE`, on a `required_ids` set differing
   from the pinned 12, if either sibling is omitted from the snapshot, if either
   sibling passes on bare absence without the discovery/parse/inertness
   assertions, or if either sibling appears in any predicted set.
   **G2** over current post-close state: expect `required_ids` = **∅** (re-close
   is a no-op). **STOP** if any 12-ID expectation is asserted here — that
   expectation is **withdrawn** for current state.
   **G3** — four **path-scoped** commands between `358b63b4` and `e4ca20e5`:
   (a) `git diff --stat … -- <11 member paths>` → **11 modified**; (b)
   `git diff --stat -M --find-renames … -- .backlogit/queue/173-S.md
   .backlogit/archive/173-S.md` → **exactly one rename-plus-modify**,
   `.backlogit/{queue => archive}/173-S.md`; (c) `git diff --stat … -- <both
   sibling paths>` → **empty**; (d) `git rev-parse` on both siblings at both
   commits → **identical blob OIDs**. **STOP** if any sub-command deviates, or if
   any surface asserts the withdrawn claim that the **unfiltered** `git show
   --stat e4ca20e5` contains exactly 12 paths or that `e4ca20e5` is a close-only
   commit (it is the **combined publication commit**, 34 paths).
2. `168-S` → classify only. **STOP, DO-NOT-SHIP** if `CASCADE` is granted while a
   non-inert out-of-manifest descendant exists.
3. Synthetic Arm-2 fixture → expect `SAFE_CLOSE`. **STOP** if `CASCADE`.
4. **(revision 2)** Non-canonical status variant fixture → expect `SAFE_CLOSE`.
   **STOP** if `CASCADE`.
5. **(revision 2)** Torn out-of-manifest descendant fixture → expect
   `SAFE_CLOSE`. **STOP** if `CASCADE`.
6. **(revision 3)** Non-`str` status fixtures (`status: yes` → bool, `status:` →
   `None`) → expect `SAFE_CLOSE`. **STOP** if `CASCADE` or if the value is
   `str()`-coerced anywhere in the predicate path.

### Rollback (REWRITTEN in revision 2 — approval-gated, NON-NEGOTIABLE)

* **Trigger**: any pinning test fails, a dry-run hits a STOP condition, or a
  postcondition deviation is observed.
* **Procedure — the D6 sequence, in this exact order. There is NO automatic,
  immediate, or notification-only rollback path.**

  1. **CAPTURE EVIDENCE** — the observed deviation, the offending IDs, the actual
     `archived_ids`/`returned_ids`, `git status --short`, and a per-path hash diff
     against the recorded baseline. Write the capture down before anything else.
  2. **HALT** — perform **no** further mutation of any kind, including no
     "cleanup", no retry, and no partial completion of the unit in flight.
  3. **EMIT P-005** — log the process-deviation telemetry event with the captured
     evidence attached.
  4. **REQUEST EXPLICIT OPERATOR APPROVAL** — present the exact paths proposed
     for rollback and the exact command to be run. **Operator notification is NOT
     operator approval.** Absent approval, the run stays halted.
  5. **REVALIDATE AFTER APPROVAL** — immediately before executing, re-read the
     working tree and confirm the exact paths and their exact current state still
     match what was approved. **Any drift returns to step 1** and requires fresh
     approval.
  6. **EXECUTE ONLY THE APPROVED ROLLBACK** — restricted to the approved paths;
     no broader command, no `git reset --hard` on the worktree, no retry at a
     different scope, and no second attempt without repeating steps 1–5.

* **Owner**: Ship executes steps 1–3 and 5–6; **the operator owns step 4 and is
  the sole authority for it.** Revision 1's "Owner: Ship, with operator
  notification" is **withdrawn** — it described a notification-only path, which
  D6 prohibits.
* **Scope note**: contract files are text-only and the classifier change is
  confined to one predicate, so an approved rollback is narrow — but narrowness
  is **never** a reason to skip steps 1–5.
* **Validation window**: through U6's dry-runs.

### Partial-rollout / external-dependency constraints

R1 (upstream backlogit, durable follow-up `7F9CB5E9`) is **explicitly out of
scope** and must not be back-doored. R2 (engine `parent_id` clearing on returned
siblings, durable follow-up `63363CF5`) is an upstream report, not a code change
here. **INV-11's operational multi-shipment capability is an external runtime
prerequisite** gated entirely on `7F9CB5E9`; nothing in this plan may be
described as delivering it.

### Unresolved operator decisions still blocking safe execution

1. **P-001 overlap authority for `174-S` — DISCHARGED IN FACT, NOT EVIDENCED OF
   RECORD (CORRECTED in revision 3).**
   *In fact:* `173-S` is archived (`archived_status: shipped`) following the
   operator's explicitly authorized, Ship-verified administrative close; zero
   shipments are active; `pre_claim` **PASSES**. Nothing was granted by Stage —
   the condition retired because the state changed.
   *Of record:* **the closure evidence is contradictory.** The only closure
   artifact naming `173-S` —
   `docs/closure/2026-09-14-173-s-165-f-closure.md` — still reads
   `closure_status: BLOCKED` with condition 2 `satisfied: false` and the sentence
   *"The shipment record remains status: active in backlogit"*. And because its
   filename does not match `topology.closure_complete()`'s
   `{shipment_id}-*-post-merge-closure.md` glob, `173-S` has **no closure record
   of record at all** (the call returns `None`, not `False`).
   **Revision 2's flat claim "P-001 overlap — DISCHARGED BY STATE" is therefore
   WITHDRAWN as over-stated.** Stage does **not** declare P-001 discharged while
   the authoritative closure evidence contradicts it.
   **Required, and NOT satisfiable by Stage (P-010):** a **Ship/operator-owned**
   superseding closure record for `173-S` — conventionally
   `docs/closure/173-S-165-F-post-merge-closure.md` — carrying the operator-action
   provenance (decision D8), the **path-scoped** `358b63b4`→`e4ca20e5` evidence
   (D7a / D10 G3), and an
   explicit supersession pointer retiring the 2026-09-14 artifact. Stage
   **records** this prerequisite; Stage **cannot** and does **not** create it,
   and MUST NOT edit the existing artifact.
   *Note:* `174-S`'s `pre_claim` PASS does **not** evidence this — `174-S` is
   `dag-root` with empty `dependencies` (`predecessor_source: declared_root`) and
   never consults `173-S`'s closure artifact.
2. R1 / R2 upstream disposition (`7F9CB5E9`, `63363CF5`) — **open**, but
   **non-blocking** for this shipment: both are surfaced as fail-closed halts and
   neither is on the critical path.

**Execution safety is unblocked; CLAIM READINESS is NOT.** No operator decision
blocks safe *execution* of the six units. **One readiness prerequisite remains
outstanding (item 1): the Ship/operator-owned superseding `173-S` closure
record.** Revision 2's sentence "No operator decision currently blocks safe
execution of `174-S`" is retained only in that narrowed, execution-scoped sense
and MUST NOT be read as a readiness or claimability clearance.

---

## Plan Hardening — Revision-2 Impact Re-check (P-006, MANDATORY, re-run 2026-09-16)

Revision 2 changed plan content at **P1 severity**, so the P-006 hardening
impact check was **re-run in full** rather than assumed to carry over.

### Hardening-signal re-evaluation

| Signal | Rev 1 | Rev 2 | Note |
|---|---|---|---|
| Touches a NON-NEGOTIABLE policy | yes | **yes** | P-015 rewrite now also carries D1a/INV-11 |
| Touches a safety classifier | yes | **yes** | predicate now *narrower* (exact match + torn fail-closed) |
| Multi-surface blast radius | yes | **yes** | unchanged surface list |
| Changes a destructive-op gate | yes | **yes** | now also rewrites the **rollback** gate (D6/R23) |
| External tool behavior dependency | yes | **yes** | now explicitly declared an external *prerequisite* (INV-11) |

**`Requires plan hardening: yes` — 5 of 5 signals (up from 4 of 5).** Hardening
re-performed; H10–H14 added above.

### Blast-radius delta

| Dimension | Change | Direction |
|---|---|---|
| Files touched | **none added** — same classifier, 2 policy mirrors, 2 skill mirrors, tests | neutral |
| Classifier authorization surface | exact-match inertness + torn/duplicate fail-closed | **NARROWED** |
| Skill mutation surface | Step 6 rollback text now **changed** rather than preserved | +1 block, same two mirrors already edited by U5 — **no new file, no new unit** |
| Capability claims | split delivery demoted to contract-only | **NARROWED** |
| Test surface | +5 classifier fixtures, +2 doc-contract assertions | additive, no rewrite of existing tests |
| Unit count / task mapping | **unchanged** (U1–U6 ↔ `166.001-T`–`166.006-T`) | neutral |
| Sizing | `166.005-T` gains the Step 6 rollback rewrite; still text-only edits to two already-in-scope mirrors | **within `size: M` / 2-hour rule** — re-checked, no split required |

**Net: every delta narrows authorization or adds assertions. No delta widens
blast radius, adds a surface, adds a unit, or breaks the 2-hour rule.**

### Same-field consumer re-sweep (revision 2)

Re-ran the `classify_shipment_close_path` / `ClosePath` consumer sweep against
current `HEAD`: consumer set **unchanged**, and **no `ClosePath` enum member is
added or removed** by revision 2. The `status_index` return-shape change is
internal to `shipment_closure.py` and has no external consumer. `H5`'s
fail-closed default is strengthened, not altered in kind.

### Revision-2 risky actions

| Action | Risk | Control |
|---|---|---|
| Tighten inertness to exact canonical match | **low** — strictly narrows a destructive authorization | H10 negative fixtures; D3's characterization suite proves no regression |
| Add torn/duplicate fail-closed to the index build | **medium** — a false positive would block legitimate closures | H11 fixtures pin both the torn and the clean case; the clean `173-S` retrospective dry-run must still return `CASCADE` |
| Rewrite skill Step 6 rollback text | **medium** — edits a destructive-op gate | Replaced by a **strictly stricter** approval-gated sequence; H13 negative assertion; same mirrors already in U5's declared scope |
| Demote split-delivery claims | **low** | H12 + U6 item 6 |
| Mark spike evidence non-authoritative | **low** | R24 forces in-workspace re-derivation; no behavior depends on the external evidence after U1 |

### Safety mode

**`freeze-scope` — unchanged.** The declared boundary is still exactly the six
units, the four contract files, `src/autoharness/gates/shipment_closure.py`, and
the test modules. Revision 2 adds **no** file to that boundary.

---

## Plan Hardening — Revision-3 Impact Re-check (P-006, MANDATORY, re-run 2026-09-16)

Revision 3 changed plan content at **P1 severity** (five blockers), so the P-006
hardening impact check was **re-run in full** rather than assumed to carry over
from revision 2.

### Hardening-signal re-evaluation

| Signal | Rev 2 | Rev 3 | Note |
|---|---|---|---|
| Touches a NON-NEGOTIABLE policy | yes | **yes** | P-015 rewrite unchanged in scope |
| Touches a safety classifier | yes | **yes** | predicate narrowed again (parsed-scalar + non-`str` fail-closed) |
| Multi-surface blast radius | yes | **yes** | unchanged surface list |
| Changes a destructive-op gate | yes | **yes** | unchanged (D6 rollback rewrite retained) |
| External tool behavior dependency | yes | **yes** | now explicitly **unproven** for all but one proposition (D7a) |

**`Requires plan hardening: yes` — 5 of 5 signals (unchanged).** Hardening
re-performed; **H15–H18 added** above.

### Blast-radius delta (revision 3)

| Dimension | Change | Direction |
|---|---|---|
| Files touched by the plan's units | **none added** — same classifier, 2 policy mirrors, 2 skill mirrors, tests | neutral |
| Classifier authorization surface | non-`str` status now explicitly non-inert and fail-closed (R25/H15) | **NARROWED** |
| Evidence claims | engine-law claims reduced to **one** immutably-sourced proposition; all others demoted to indicative/unproven | **NARROWED** |
| Containment precheck | re-scoped from "no OS temp dir anywhere" to "no out-of-repository **engine** execution" | **widened in letter, unchanged in risk** — the prohibited act (external engine execution + uncontained destruction) is unchanged; the permitted act (hermetic read-only unit-test tmpdir) creates no engine state, runs no external tool, and was **already in use by the existing suite**. Net destructive surface: **zero change** |
| Red-phase obligation | CLASS 4 added: must start **and stay** green, before/after recorded | **STRENGTHENED** (adds a proof obligation) |
| `173-S` gate | pinned to immutable `358b63b4` + SHA-256 digests; invalid post-close assertion withdrawn | **NARROWED + made reproducible** |
| Closure-artifact surface | `docs/closure/**` explicitly declared **out of bounds** (H18) | **NARROWED** |
| Claim readiness | one readiness prerequisite **re-opened** (Ship/operator superseding closure record) | **NARROWED** (claimability reduced, never expanded) |
| Unit count / task mapping | **unchanged** (U1–U6 ↔ `166.001-T`–`166.006-T`) | neutral |
| Sizing | no unit gains new files; U1 gains 2 fixtures + a class label, U6 gains a pinned-snapshot step | **within `size: M`/`S` and the 2-hour rule** — re-checked, no split required |

**Net: every delta narrows an authorization, deletes an unprovable claim, adds a
proof obligation, or reduces claimability. The single "widening" — the
containment re-scope — permits only hermetic, read-only, tool-free Python
tmpdirs that the existing test suite already uses, and leaves the prohibited
destructive surface unchanged.**

### Same-field consumer re-sweep (revision 3)

Re-ran the `classify_shipment_close_path` / `ClosePath` consumer sweep against
current `HEAD`: consumer set **unchanged**, and **no `ClosePath` enum member is
added or removed** by revision 3. The `_ArtifactRecord.status` type widens from
`str | None` to `object | None` — this is **internal to `shipment_closure.py`**
(the dataclass is module-private and has no external consumer) and exists solely
so a non-`str` parse can be rejected rather than coerced.

Newly swept this revision: `gates.topology._frontmatter` (read-only consumer,
**unmodified** — revision 3 aligns the plan to its existing `yaml.safe_load`
semantics rather than changing it) and `gates.topology.closure_complete` /
`_closure_artifact_complete` (read-only consumers of `docs/closure/**`,
**unmodified** — H18 places that directory out of bounds).

### Revision-3 risky actions

| Action | Risk | Control |
|---|---|---|
| Reclassify most red-phase cases to CLASS 4 | **medium** — a weakened red phase could let a wrong predicate ship | CLASS 4 adds a *stronger* obligation (green before **and** after, pair recorded, H16); CLASS 1 retains genuine red on the observed-status and torn-specific reason text |
| Narrow the status contract to parsed-scalar equality | **low** — strictly narrows; adds non-`str` fail-closed | H15 fixtures; the YAML-quoting requirement on the padded fixture prevents a silently-false test |
| Re-scope the containment precheck | **low** | Prohibited destructive surface unchanged; permitted surface is hermetic, tool-free, and pre-existing; conditional engine harness explicitly **not authorized** here |
| Withdraw engine-law claims to one proposition | **low** — reduces asserted knowledge | Dependent behaviour is fail-closed wherever a behaviour is unproven; the retained proposition is git-immutable |
| Re-open a `174-S` readiness prerequisite | **low** — reduces claimability | Routed to Ship/operator; Stage self-grants nothing |

### Safety mode

**`freeze-scope` — unchanged.** The declared boundary is still exactly the six
units, the four contract files, `src/autoharness/gates/shipment_closure.py`, and
the test modules. Revision 3 adds **no** file to that boundary and explicitly
**removes** `docs/closure/**` from any possible reach (H18).

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

---

## Plan Review — Cycle 2 (revision 2, 2026-09-16)

`dispatch_mode: single-agent-declared-degradation` (P-012 — reviewer subagent
dispatch probed again and still unavailable; recorded, not silently skipped).

**Trigger**: revision 2 made P1-class changes to a plan that had already passed.
Per the gate contract, `plan-harden`'s impact check and `plan-review` were both
**re-run**; cycle 1's PASS does not carry over unexamined.

### Gate decision

**`decision: PASS`** — **0 P0**, **0 P1** open. Three P1 and two P0 findings from
cycle 1 remain resolved and were re-verified; the five consolidated local-review
blockers routed into revision 2 are all resolved. Two new P2 and two new P3
findings recorded as advisory.

### Persona coverage

Selected 7; ran 6. *Security Lens Reviewer* trigger condition remains unmet (no
authn/authz/secret surface) — recorded, not silently skipped.

### Re-verification of cycle-1 findings

| Cycle-1 finding | Status at cycle 2 |
|---|---|
| P0-1 descendant walk deleted | **still resolved** — walk retained; revision 2 strengthens its verdict |
| P0-2 `accounted_ids` absorbing inert descendants | **still resolved** — prohibition restated and now anchored in D1a/R21 |
| P1-1 ordering would invalidate historical manifests | **still resolved** — INV-8 intact; the real `173-S` close succeeded under feature-**first** ordering, which is now direct evidence |
| P1-2 no red phase for contract surfaces | **still resolved** — and U1's exit criteria corrected so the red phase is *achievable* rather than self-contradictory |
| P1-3 R1 had no defined failure behavior | **still resolved** — plus INV-11 and durable follow-up `7F9CB5E9` |

### Revision-2 blocker resolutions (verified)

| # | Blocker | Resolution | Verified by |
|---|---|---|---|
| 1 | Inertness could be broadened by normalization | D1b / U2 step 3: verbatim compare, `.lower()`/`.strip()` forbidden in the predicate | R19, H10 |
| 1 | Torn/duplicate IDs not fail-closed | D1c / U2 step 2: full two-root scan returns `None` on non-unique resolution, incl. out-of-manifest descendants | R20, H11 |
| 1 | Red-phase exit demanded all tests go red | U1 exit-criteria table splits behavior-changing/doc-contract (**must** fail red) from characterization (**may** start green) | U1 |
| 2 | INV-1 vs INV-2 contradiction; `validated_linked_deliberations` undefined | D1a defines `manifest_scope`/`closure_scope`/`allowed_ids`/`required_ids` and the four admission conditions; INV-1/INV-2/INV-10 restated coherently | R21, H14 |
| 3 | Split delivery claimed as delivered | INV-11 + external prerequisite `7F9CB5E9`; R05/R06 narrowed to contract text; U6 item 6 negative check | R22, H12 |
| 5 | Notification-only / automatic rollback | D6 six-step sequence; U5 step 5 rewrites skill Step 6; Rollback section rewritten | R23, H13 |
| 10 | Spike evidence treated as authoritative | F3/§1 provenance banners; D7/D8; authoritative confidence rebased on the operator close + Ship verification | R24 |

### Scope boundary audit (re-run)

No unit touches `173-S`, `165.007-T`, `165.010-T`, the `160-F` family, or
`174-S`'s `dependencies`/`labels`. Revision 2 introduces **no** new file, **no**
new unit, and **no** new surface. No P-001 authority, bootstrap grant, or
claimability change is introduced — `174-S`'s claimability improved solely
because `173-S`'s state changed by operator action.

### Consistency audit (new in cycle 2)

* `166.005-T`'s "PRESERVE Step 6 unchanged" instruction **conflicted** with the
  new D6 rollback requirement. Resolved: U5 step 5 now explicitly supersedes it,
  and the task description is updated to match. *(Would have been a P1 had it
  been left unreconciled.)*
* Human-readable dependency prose in `166.005-T` and `166.006-T` **disagreed**
  with the stored machine DAG. Resolved: prose corrected to match; the machine
  DAG is unchanged and remains the single source of truth.

### Findings — P2 (non-blocking; follow-ups)

* **P2-1** — Report backlogit `parent_id`-clearing upstream (decision R2) —
  now carried by durable active entry **`63363CF5`**.
* **P2-2** — `168-S` closure remains unclassified until its own closure (R4).
* **P2-3 (new)** — The `%TEMP%` spike arms should be replaced by a permanent,
  in-workspace, git-ignored spike harness so future engine-law questions are
  answerable without a containment violation.
* **P2-4 (new)** — `2B42392E` was archived too broadly. Not correctable in the
  append-only archive; mitigated by forward traceability from `7F9CB5E9`. A
  future stash-archival checklist item ("archive only the scope actually
  consumed") would prevent recurrence.

### Findings — P3 (advisory)

* **P3-1** — Consider surfacing the inertness verdict in the closure report for
  auditability.
* **P3-2** — The `done`-without-provenance archive shape (366 records) remains
  accommodated, not corrected (R5).
* **P3-3 (new)** — Consider a lint that rejects automatic-revert phrasing
  anywhere in `.github/skills/**` and `templates/skills/**`.
* **P3-4 (new)** — Consider promoting the D1a set vocabulary into a shared
  glossary so future closure work does not re-derive it.

### Constitutional compliance (re-checked)

Principle II (test-first) satisfied via U1, with the red-phase definition now
internally consistent. Principle VII (destructive-command approval) is
**strengthened**: revision 2 replaces the last notification-only rollback path in
this plan with an explicit approval gate, and narrows the destructive op's
authorization further via D1b/D1c.

---

## Plan Review — Cycle 3 (revision 3, 2026-09-16)

> **📜 HISTORICAL RECORD — DO NOT RE-LITIGATE, DO NOT REWRITE.** This section is
> the verbatim cycle-3 verdict **over revision 3**, retained as the audit trail.
> It remains the **review verdict of record**, and it does **not** extend to
> revision-4 text. Three revision-3 formulations quoted below were later found
> wrong and are **withdrawn by revision 4** — they are preserved here *as
> history*, not as operative requirements:
>
> * the P1-2 row's *"sourced to `git show --stat e4ca20e5`"* and the honesty
>   audit's *"The 12-path close … verifiable by `git show --stat e4ca20e5`"* →
>   **withdrawn**; the unfiltered diffstat contains **34** paths and `e4ca20e5`
>   is the **combined publication commit**. Superseded by the **path-scoped**
>   evidence in D7a / D10 G3 / R16 / H20.
> * the P1-2 row's *"containment re-scoped to out-of-repository engine
>   execution"* → **withdrawn in full** by D7b / R27 / H21 (Constitution IV +
>   Principle VII).
> * the P1-1 row's four-class scheme, as it stood, assigned two classes to one
>   named test → **corrected** by D16 / H19 (split into single-class tests).
>
> See **Plan Hardening — Revision-4 Impact Re-check** and **Plan Review — Cycle 4
> NOT RUN** below.

`dispatch_mode: single-agent-declared-degradation` (P-012 — reviewer subagent
dispatch probed again and still unavailable; recorded, not silently skipped).

**Trigger**: revision 3 made P1-class changes to a plan that had already passed
cycle 2. Per the gate contract, `plan-harden`'s impact check and `plan-review`
were both **re-run**; cycle 2's PASS does not carry over unexamined.

### Gate decision

**`decision: PASS`** — **0 P0**, **0 P1 open**. All **five** deduplicated P1
blockers from the local fix-verification review are resolved and verified below.
Cycle-1 and cycle-2 findings were re-verified and remain resolved. Two new P2 and
one new P3 finding recorded as advisory. **One non-finding readiness prerequisite
is recorded and routed** (the Ship/operator superseding `173-S` closure record) —
it is **outside Stage's authority by P-010**, so it is a handoff item, not an
open review finding against this plan.

### Persona coverage

Selected 7; ran 6. *Security Lens Reviewer* trigger condition remains unmet (no
authn/authz/secret surface) — recorded, not silently skipped.

### Re-verification of cycle-1 and cycle-2 findings

| Prior finding | Status at cycle 3 |
|---|---|
| P0-1 descendant walk deleted | **still resolved** — walk retained |
| P0-2 `accounted_ids` absorbing inert descendants | **still resolved** — prohibition intact (U2 step 4, R21) |
| P1-1 ordering would invalidate historical manifests | **still resolved** — INV-8 intact; H9 pins it |
| P1-2 no red phase for contract surfaces | **still resolved** — PART B is CLASS 2, genuinely red |
| P1-3 R1 had no defined failure behavior | **still resolved** — `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` + INV-11 + `7F9CB5E9` |
| Cycle-2 "red phase demanded all tests go red" | **re-opened and properly resolved** — cycle 2's three-class fix was itself still unsatisfiable; D11's four-class scheme measured against the live predicate resolves it |

### Revision-3 blocker resolutions (verified)

| P1 | Blocker | Resolution | Verified by |
|---|---|---|---|
| 1 | Unsatisfiable red matrix | Four-class scheme; CLASS 4 must start **and stay** green; red relocated to observed-status + torn-specific reason text, which current `main` provably does not emit | D11, U1 exit table, H16, `166.002-T`, `166.001-T` |
| 2 | Classifier fixtures cannot prove engine effects; containment over-broad | CLASSIFIER/ENGINE law disjoint; one engine proposition, sourced to `git show --stat e4ca20e5`; `returned_ids` / `parent_id`-clearing remain **unproven and blocked** (`63363CF5`, `7F9CB5E9`); containment re-scoped to out-of-repository **engine** execution; in-repo engine harness deferred to P2-3, **not** authorized here | D7a, D7b, D13, R24, H17, prechecks |
| 3 | `173-S` retrospective snapshot unsatisfiable | Immutable pre-close pin `358b63b4` (parent of `e4ca20e5`) + SHA-256 digests; G1 replay / G2 current-state / G3 engine-effect; post-close 12-ID assertion **withdrawn** | D10, U6 item 3, R16, dry-run scenario 1, `166.006-T` |
| 4 | Stale operational closure artifact | Recorded as a **historical blocked-phase record**; Stage annotates on Stage-owned surfaces only and **does not** edit `docs/closure/**` (H18); superseding Ship/operator record registered as a readiness prerequisite; unqualified P-001 discharge **withdrawn** | D8a, D14, R26, §1, § Unresolved operator decisions, `174-S` |
| 5 | Exact-status contract vs YAML parser | Exact **parsed-scalar** equality; no post-parse normalization; **non-`str` fails closed**; `archived ` distinctness claim **withdrawn as factually wrong**; padded fixture must be YAML-quoted; fail-closed for malformed/torn/duplicate preserved | D1b, D15, U2 step 1/3, R19/R25, H15, `166.001-T`, `166.002-T` |

### Honesty audit (new in cycle 3)

Every revision-3 assertion was traced to a source that a third party can
re-derive without trusting this document:

* `358b63b4` is the parent of `e4ca20e5` — verifiable by `git log`.
* The 12-path close and the two untouched siblings — verifiable by
  `git show --stat e4ca20e5`.
* The current `missing` predicate's already-`SAFE_CLOSE`-with-named-ID behaviour
  — verifiable by reading `src/autoharness/gates/shipment_closure.py`.
* `_frontmatter`'s `yaml.safe_load` — verifiable in
  `src/autoharness/gates/topology.py`.
* `closure_complete()`'s `{shipment_id}-*-post-merge-closure.md` glob and the
  stale artifact's non-matching filename — verifiable in the same file and on
  disk.

**No claim in revision 3 rests on an unreproducible narrative, and no evidence
was synthesized.** Where a proposition could not be sourced, it is labelled
unproven and the dependent behaviour is fail-closed.

### Scope boundary audit (re-run)

No unit touches `173-S`, `165.007-T`, `165.010-T`, the `160-F` family, `174-S`'s
`dependencies`/`labels`, or (newly, H18) `docs/closure/**`. Revision 3 introduces
**no** new file, **no** new unit, and **no** new surface. No P-001 authority,
bootstrap grant, or claimability change is introduced — and revision 3 in fact
**reduces** asserted readiness by re-opening one prerequisite.

### Findings — P2 (non-blocking; follow-ups)

* **P2-1** — Report backlogit `parent_id`-clearing upstream (R2) — carried by
  durable active entry **`63363CF5`**.
* **P2-2** — `168-S` closure remains unclassified until its own closure (R4).
* **P2-3 (sharpened in cycle 3)** — Build a **repository-internal, git-ignored,
  destructive-approval-gated** engine-characterization harness so ENGINE-LAW
  propositions (`returned_ids` behaviour, descendant archival, `parent_id`
  clearing) can be established without a containment violation. **Explicitly out
  of scope for `174-S`** (new surface, outside `freeze-scope`, requires operator
  destructive approval).
* **P2-4** — `2B42392E` was archived too broadly; mitigated by forward
  traceability from `7F9CB5E9`.
* **P2-5 (new)** — The closure-artifact naming convention is not enforced:
  `closure_complete()` requires `{shipment_id}-*-post-merge-closure.md`, but
  `docs/closure/` contains date-prefixed variants (e.g.
  `2026-09-14-173-s-165-f-closure.md`, `2026-09-11-162-s-154-f-closure.md`) that
  the glob silently never matches, returning `None` instead of a verdict.
  Consider a lint or a gate warning for orphaned closure artifacts.
* **P2-6 (new)** — Consider a doc-lint that rejects "byte-for-byte" /
  "verbatim" contract language on any value that reaches the code through a
  YAML parser, to prevent recurrence of the P1-5 class of defect.

### Findings — P3 (advisory)

* **P3-1** — Surface the inertness verdict in the closure report for auditability.
* **P3-2** — The `done`-without-provenance archive shape (366 records) remains
  accommodated, not corrected (R5).
* **P3-3** — Consider a lint rejecting automatic-revert phrasing anywhere in
  `.github/skills/**` and `templates/skills/**`.
* **P3-4** — Promote the D1a set vocabulary into a shared glossary.
* **P3-5 (new)** — Consider recording each test's red-phase class as a pytest
  marker rather than only a docstring line, so CLASS 1/2/4 obligations are
  machine-checkable in CI.

### Constitutional compliance (re-checked)

Principle II (test-first) satisfied via U1, with the red-phase definition now
**both internally consistent and achievable against the measured current
behaviour** — the first two revisions were internally consistent but factually
unsatisfiable. Principle VII (destructive-command approval) is **further
strengthened**: revision 3 narrows the inertness grant again (non-`str`
fail-closed), places `docs/closure/**` out of bounds, and reduces asserted claim
readiness rather than expanding it.


### Coupled-surface sweep (revision 3, completed after the cycle-3 findings table)

> **📜 HISTORICAL — retained as the audit trail.** Row **S-3**'s replacement
> wording (*"row (a) PROVEN from `git show --stat e4ca20e5`"*) is itself
> **withdrawn by revision 4**: the unfiltered diffstat has **34** paths.
> Row (a)'s evidence is now the **path-scoped** `358b63b4`→`e4ca20e5` comparison
> (D7a / D10 G3 / H20), and rows (b)–(e) additionally may not be stated as
> *measured* facts (R24 / H17). See the revision-4 sweep below.

A final sweep over every surface coupled to the five blockers found **four
residual revision-2 claims that the blocker edits had not yet reached**. All four
are corrected; each correction **narrows** a claim.

| # | Surface | Residual stale claim | Correction |
|---|---|---|---|
| S-1 | `.backlogit/queue/166-F.md` | Cited plan/decision **revision 2** as authoritative; HANDOFF asserted P-001 **"DISCHARGED BY STATE"** | Repointed to **revision 3** (incl. the rev-3 re-check and cycle 3); discharge claim rewritten to **discharged in fact, not of record**, with the Ship/operator-owned superseding closure record named as the outstanding prerequisite |
| S-2 | `.backlogit/queue/166.003-T.md` item 8 | D1b stated as *"exact canonical literal, compared verbatim"* | Restated as **exact parsed-scalar equality** with non-`str` fail-closed, the accepted YAML-equivalence limitation, and the engine-agreement rationale |
| S-3 | `.backlogit/queue/166.004-T.md` items 1a and 4 | Item 1a repeated the *"compared VERBATIM"* contract; **item 4 re-introduced the P1-2 defect verbatim** by instructing Ship to cite the 166.002-T classifier fixtures as the authoritative source for the **engine**-behaviour table | 1a restated as parsed-scalar with the withdrawn `archived ` claim called out; **item 4 rewritten to label each row with its evidence class** — row (a) PROVEN from `git show --stat e4ca20e5`, rows (b)–(e) **INDICATIVE AND UNPROVEN**, fail-closed, routed to `7F9CB5E9`/`63363CF5` |
| S-4 | Decision `D5` and `R3`; memory supersession table | Unqualified *"discharged by state"* | Qualified in all three places against **D8a**: discharged **in fact**, not **of record** |

**S-3 is the most significant finding of the sweep**: an unswept task record would
have instructed Ship to do precisely the thing `H17` prohibits, which would have
re-opened P1-2 at execution time even though the plan itself was correct. This is
the concrete justification for treating the backlog records as **coupled surfaces
of the plan** rather than as downstream copies.

After the sweep, a repeat scan for `byte-for-byte`, `compared VERBATIM`,
`DISCHARGED BY STATE`, `revision 2)` as an authoritative pointer, and the
`fixtures ... as the authoritative` engine-evidence phrasing returns **only**
historical labels, explicit withdrawal notices, and correctly-qualified
formulations. **No open P0 or P1 remains.**

---

## Plan Hardening — Revision-4 Impact Re-check (P-006, MANDATORY)

**Trigger.** Revision 4 makes P1-class changes to a hardened plan (four
deduplicated external P1 groups: A test-granularity, B evidence-honesty
propagation, C historical replay/evidence correctness, D constitutional
containment). P-006 requires the hardening impact check to be **re-run** on any
P1-class revision. This check is **not** gated by the `plan-review` cycle
counter and is run in full.

### Hardening signal re-assessment

| Signal | Rev-3 | Rev-4 | Note |
|---|---|---|---|
| Destructive or irreversible operation | present | **present** | D6/D7b; revision 4 **removes** the one automatic deletion revision 3 had permitted, so the destructive surface **shrinks** |
| Safety/authorization predicate change | present | **present** | unchanged — U2 predicate replacement |
| Cross-surface contract (mirrors, schema, gates) | present | **present** | unchanged |
| Historical/immutable-evidence dependence | present | **present** | **strengthened** — evidence now path-scoped and blob-OID-pinned |
| Multi-agent handoff (Stage→Ship) | present | **present** | unchanged |
| **Total** | **5/5** | **5/5** | hardening remains **mandatory and satisfied** |

### Blast-radius delta (revision 4)

| Dimension | Delta | Assessment |
|---|---|---|
| New source modules | **none** | all four groups are planning/backlog/docs corrections on the **same contract surface** |
| New implementation surface | **none** | the split in Group A adds test **functions**, not modules; the containment check in Group D is ~4 lines inside existing test setup |
| Files touched by the plan | **unchanged** | same four contract files, same two test modules |
| `freeze-scope` | **UNCHANGED — still `freeze-scope`** | no scope was added; three claims were **narrowed** and one permission **revoked** |
| Authorization strength | **strictly reduced** | Group B forbids unproven engine behaviour from authorizing `CASCADE`; Group C replaces a false evidential claim with a narrower true one; Group D revokes a write/delete permission |
| Test count | **+6 functions** (A) **+2 assertions** (D), **+3 assertions** (C/G1) | no new module; U1 stays `size: M` |
| Reversibility | **improved** | persistent scratch dirs are inspectable; nothing auto-deletes |

**Net blast-radius direction: NEGATIVE (contracting).** Revision 4 removes
authority and narrows claims; it grants nothing new. No unit crosses the 2-hour
rule as a result.

### New protected invariants

**H19** (test-class granularity), **H20** (path-scoped historical evidence;
non-vacuous sibling inertness), **H21** (absolute workspace containment; no
automatic deletion) — added to the invariant table above with their pinning
tests. **H1–H18 re-checked and all still hold**; H16 and H17 are **strengthened**
by H19 and H20 respectively.

### Sizing re-check (2-hour rule)

| Unit | Task | Rev-3 size / complexity | Rev-4 | Rationale |
|---|---|---|---|---|
| U1 | `166.002-T` | `M` / `medium` | **`M` / `medium` (unchanged)** | +6 test functions are mechanical splits of fixtures that already exist; the containment relocation is a one-line root change plus a 4-line check |
| U6 | `166.006-T` | `S` / `medium` | **`S` / `high`** | complexity raised: G1 now materializes a 14-row pinned snapshot and must prove sibling inertness **non-vacuously**; volume is still small, so `size` is unchanged. `complexity: high` triggers the split/de-risk gate → **de-risked by decomposition already present** (G1/G2/G3 are three independently STOP-gated sub-gates), not by adding a unit |
| U2–U5 | `166.001-T`, `166.003-T`, `166.004-T`, `166.005-T` | unchanged | **unchanged** | Group B/C edits narrow existing prose; no new work |

### Constitutional re-check

| Principle | Verdict |
|---|---|
| **IV — workspace containment** | **now satisfied** (was violated by the rev-3 `%TEMP%` carve-out); R27/H21/D7b/D17 |
| **VII — destructive-operation approval** | **now satisfied** (was violated by automatic tmpdir cleanup); all deletion routed through D6 |
| **Evidence honesty** | **strengthened**; no fixture-as-engine-proof claim survives, no unproven behaviour is stated as measured fact |
| **P-010 role boundary** | **preserved**; `docs/closure/**` untouched (H18) |

**Hardening verdict: PASS — 5/5 signals, `freeze-scope` UNCHANGED, blast radius
CONTRACTING, H19–H21 added, no new implementation surface.**

---

## Plan Review — Cycle 4 NOT RUN (per-plan review-cycle limit reached)

> **📜 SUPERSEDED 2026-09-16 BY EXPLICIT OPERATOR AUTHORIZATION — RETAINED AS
> THE AUDIT TRAIL OF THE HALT.** The operator subsequently granted a **narrowly
> scoped, one-time cycle-4 override** (option **(a)** from the disposition table
> below), authorizing exactly one `plan-review` run over revision 4. The
> override did **not** reset counters, waive P0/P1, authorize further fix
> cycles, permit implementation, or permit claim/shipment execution. This
> section's statement that no cycle-4 review was run was **true when written**
> and is **overtaken by events**. The operative verdict is
> `## Plan Review — Cycle 4 (revision 4, 2026-09-16)` below.

> **⛔ HALTED FOR OPERATOR DISPOSITION. This is a recorded limit, not a pass.**

### Cycle accounting

| Cycle | Plan revision reviewed | Verdict | Date |
|---|---|---|---|
| 1 | revision 1 | FAIL (2 P0, 3 P1) | 2026-09-15 |
| 2 | revision 2 | PASS | 2026-09-16 |
| 3 | revision 3 | PASS (0 P0, 0 P1 open) | 2026-09-16 |
| **4** | **revision 4** | **NOT RUN — limit reached** | — |

**Governing limit.** The Stage stop condition *"Review-fix cycles per plan: 3 →
accept remaining findings, move on"*. Cycles 1, 2 and 3 are consumed. **A fourth
`plan-review` invocation over this plan is therefore NOT policy-permitted.**

**What was NOT done, explicitly.** No cycle-4 review was run, simulated,
self-performed, summarized-as-if-run, relabelled as a "verification pass", a
"fix-verification", a "sweep", or a "re-check"; and **no counter was reset,
re-based, or re-scoped** (e.g. by arguing revision 4 constitutes a "new plan").
The operator's instruction was explicit on this point and is honoured literally.

**What WAS done under the still-permitted gates.**

* The **P-006 `plan-harden` impact re-check** above — mandatory on a P1-class
  revision and **not** governed by the review-cycle counter. Verdict **PASS**.
* The **revision-4 coupled-surface literal sweep** below — a mechanical grep for
  withdrawn claims and contradictory tokens. It is a **consistency check over
  text this session wrote**, not an adjudication of plan quality, and it is
  **not** counted or presented as a review cycle.

### Review-coverage gap (OPEN, operator-owned)

**The review verdict of record is cycle 3's PASS over *revision 3*. It does NOT
extend to revision-4 text.** Revision 4's corrections are therefore **hardened
but not externally reviewed**. This is the single open item on the Stage side.

**Operator disposition required — one of:**

| Option | Effect |
|---|---|
| **(a) Authorize a cycle-4 `plan-review`** (explicit limit override) | closes the coverage gap; requires the operator to lift the 3-cycle stop condition for this plan |
| **(b) Accept revision 4 on the hardening verdict alone** | proceed to execution with the gap recorded and accepted; consistent with the stop condition's *"accept remaining findings, move on"* |
| **(c) Freeze at revision 3** | discard revision 4 — **not recommended**: revision 3 contains a known-false evidential claim (Group C) and two constitutional violations (Group D) |

**Stage takes no option unilaterally.** Stage does not self-authorize a fourth
cycle, and does not declare revision 4 reviewed.

### Coupled-surface sweep (revision 4)

Mechanical literal scan across **every** coupled surface — plan, decision, all
seven `166.*` backlog records, `174-S`, and the handoff memory — for each claim
withdrawn by revision 4 and for tokens that would contradict H19/H20/H21.

| # | Token / claim swept | Required terminal state | Result |
|---|---|---|---|
| S4-1 | `git show --stat e4ca20e5` | only inside explicit withdrawal notices or historical-record banners; **never** as an operative evidence instruction | **clean** |
| S4-2 | `exactly 12 paths` / `EXACTLY 12 paths` (unqualified) | only as a withdrawn claim, or qualified as the **path-scoped** subset | **clean** |
| S4-3 | `close-only` applied to `e4ca20e5` | absent; `e4ca20e5` described as the **combined publication commit** (34 paths) | **clean** |
| S4-4 | `TemporaryDirectory` / `mkdtemp` / `mkstemp` / `TMPDIR` / `%TEMP%` as **permitted** | only in PROHIBITED lists and withdrawal notices | **clean** |
| S4-5 | `self-cleaning` / `SELF-CLEANING` / auto-delete / `rmtree` as permitted | only in withdrawal notices | **clean** |
| S4-6 | fixtures described as `the authoritative record` of **engine** behaviour | absent; fixtures are authoritative for **classifier** law only | **clean** |
| S4-7 | `measured engine` / `the measured engine RETURNS` / `SILENTLY CLEARS … parent_id` as fact | restated as **INDICATIVE / UNPROVEN**, fail-closed, cannot authorize `CASCADE` | **clean** |
| S4-8 | `re-derive … as … fixture` / `re-establishes every one of these claims` | withdrawn; classifier/engine separation stated instead | **clean** |
| S4-9 | `byte-for-byte` / `compared VERBATIM` / `EXACT canonical literal` | only as historical labels or withdrawal notices; operative text says **exact parsed-scalar equality** | **clean** |
| S4-10 | dual-class test labels (`VERDICT = CLASS 4 \| REASON = CLASS 1` and equivalents) | absent from operative text; replaced by the six single-class split pairs | **clean** |
| S4-11 | current-state dry-run required to reproduce the 12-ID pre-close result (old **D4**) | struck through and superseded; retrospective obligation routed **solely** to D10 G1/G2/G3 | **clean** |
| S4-12 | sibling inertness asserted by **bare absence** | every occurrence now carries the four ordered assertions (DISCOVERED → parsed canonical `archived` → CLASSIFIED INERT → ABSENT) | **clean** |

**Sweep result: 12/12 clean. No open P0 or P1 remains in Stage scope.**

---

## Plan Review — Cycle 4 (revision 4, 2026-09-16)

> **✅ RUN UNDER EXPLICIT, NARROWLY SCOPED OPERATOR OVERRIDE.** The operator
> authorized exactly **one** `plan-review` cycle over **revision 4**, lifting the
> 3-cycle stop condition for this single run only (disposition option **(a)**).
> The override does **not** reset counters, does **not** authorize a further
> review-fix cycle, does **not** waive P0/P1, does **not** permit
> implementation, and does **not** permit claim or shipment execution. This
> section **supersedes** `## Plan Review — Cycle 4 NOT RUN` and closes the
> recorded review-coverage gap over revision-4 text.

`dispatch_mode: single-agent-declared-degradation`

`decision: FAIL`

### Dispatch capability and declared degradation (P-012)

| Capability | Status | Disposition |
|---|---|---|
| Reviewer subagent dispatch | `TOOL_UNAVAILABLE` | No dispatch surface exposed in this session. Declared fallback applied: **inline single-agent persona pass**, one finding list per persona, all normalized to P0–P3. Recorded, **not** silently skipped |
| Model-specific / anchor reviewer routing | `TOOL_UNAVAILABLE` | `model_routing.anchor_review` not dispatchable; Architecture Strategist rubric applied inline with the caller's model |
| Indexed knowledge retrieval (`agent-engram`) | `ENGRAM_DEGRADED` | Fell back to `git`/`grep`/file reads for all code and symbol discovery |
| Documentation retrieval (`graphtor-docs`) | `GRAPHTOR_UNAVAILABLE` | Fell back to direct reads under `docs/` and `.github/` |
| Intercom visibility (`agent-intercom`) | `INTERCOM_DEGRADED` | Operator visibility reduced; no phase broadcasts emitted. Non-destructive work continued |
| Backlog registry (`backlogit`) | `TOOL_OK` | MCP probes succeeded; `INDEX_SYNC_OK` (1229 items) |

Consistent with cycles 1–3, which recorded the same dispatch degradation. Every
selected persona was covered; no persona was skipped for dispatch reasons.

### Persona coverage

Selected **7**, ran **7** (cycles 1–3 ran 6).

| Persona | Mode | Result |
|---|---|---|
| Constitution Reviewer | inline pass | 0 P0 / 0 P1 — Principles IV and VII **newly satisfied** by Group D |
| Python Reviewer | inline pass | **1 P1** (verification gate), 1 P3 |
| Scope Boundary Auditor | inline pass | 0 findings — blast radius contracting, `freeze-scope` unchanged |
| Learnings Researcher | inline pass | **1 P1** (contradicts durable learning `097-S`) — merged with the Python Reviewer finding |
| Architecture Strategist | inline pass (anchor route unavailable) | 1 P2, 1 P3 |
| Agent-Native Parity Reviewer | inline pass | 0 findings — no MCP tool or agent-facing action surface is added |
| Security Lens Reviewer | inline pass | 1 P3 |

> **Security Lens trigger note (changed in cycle 4).** Cycles 1–3 recorded this
> persona's trigger as **unmet**. Revision 4's **Group D** newly introduces a
> workspace **trust-boundary** question (writes resolving outside the repository)
> and an **unapproved destructive-deletion** question. Cycle 4 therefore **ran**
> the persona rather than carrying forward the prior not-triggered disposition.

### Evidence re-derivation (independent, not taken on the plan's word)

Every load-bearing revision-4 factual claim was **independently re-derived** from
immutable git objects and the working tree during this review:

| Claim | Verification | Result |
|---|---|---|
| `358b63b4` is the parent of `e4ca20e5` | `git rev-parse e4ca20e5^` | ✅ `358b63b4b4d02de50fa7abf4266e0e7c5886d6c1` |
| `e4ca20e5` is the **combined publication commit**, not close-only | `git log -1 --format=%s` | ✅ `chore(stage): publish flat-manifest closure package` |
| Its **unfiltered** diffstat contains **34** paths (not 12) | `git show --name-only` count | ✅ **34** |
| G1 row table: **all 14** blob OIDs at `358b63b4` | `git rev-parse 358b63b4:<path>` ×14 | ✅ **14/14 OID_OK** |
| G1 row table: all 14 declared `status` values | `git show 358b63b4:<path>` ×14 | ✅ **14/14 STATUS_OK** (1 `active`, 11 `done`, 2 `archived`) |
| G3(a) — 11 members, all **modified**, no add/delete/rename | `git diff --name-status`/`--stat` | ✅ `11 files changed`, all `M` |
| G3(b) — exactly one **rename-plus-modify** of the record | `git diff --stat -M --find-renames` | ✅ `.backlogit/{queue => archive}/173-S.md \| 1 file changed` |
| G3(c) — excluded-sibling diff is **empty** | `git diff --stat` on both siblings | ✅ empty output |
| G3(d) — **identical blob OIDs** across the close | `git rev-parse` ×4 | ✅ `544c2377…` and `609ad8bc…` identical at both commits |
| `173-S` pre-close manifest is **11 items**, feature-first | `git show 358b63b4:.backlogit/queue/173-S.md` | ✅ 11 items, `165-F` first |
| `.gitignore` **line 6** is `.autoharness/staging/` | direct read | ✅ exact |
| Scratch root is git-ignored | `git check-ignore -v .autoharness/staging/tmp/probe.txt` | ✅ exit 0, matched by `.gitignore:6` |
| `tests/…` currently uses `tempfile.TemporaryDirectory()` | grep | ✅ line 41 — Group D's premise is factual |
| Current reason text emits **neither** observed-status **nor** torn-specific text | read `shipment_closure.py` L389–399 | ✅ emits only `"…has descendants outside the manifest: {missing}"` |
| Constitution **IV** = CLI Workspace Containment; **VII** = Destructive Command Approval | read `constitution.instructions.md` | ✅ exact |

**No fabricated evidence was found. Every revision-4 assertion checked is true
and third-party re-derivable.** The Group C corrections are notably precise: the
34-path count, the rename-plus-modify rendering, and all fourteen blob OIDs match
byte-exactly.

### Independent re-run of the revision-4 coupled-surface sweep

The plan's self-reported **12/12 clean** sweep was **re-run independently** over
the plan, the decision, all seven `166.*` records, `174-S`, and the handoff
memory. Literal scans for `git show --stat e4ca20e5` (**0 hits**),
`measured engine` (**0**), `compared VERBATIM` (**0**), and contextual inspection
of every hit for `close-only`, `TemporaryDirectory`, `mkdtemp`, `self-cleaning`,
and `byte-for-byte` confirm **all surviving occurrences are inside withdrawal
notices, PROHIBITED lists, or historical-record banners** — **none operative**.
Group A's split table, Group B's evidence-class labelling, and Group C/D's G1/G3
and containment text are **correctly propagated** into `166.001-T`, `166.002-T`,
`166.003-T`, `166.004-T`, `166.006-T`, and `174-S`. **The sweep's claim holds.**

### Re-verification of cycle-1/2/3 findings

| Prior finding | Status at cycle 4 |
|---|---|
| P0-1 descendant walk deleted | **still resolved** — walk retained (D1) |
| P0-2 `accounted_ids` absorbing inert descendants | **still resolved** — U2 step 4 prohibition + R21 intact |
| P1-1 ordering would invalidate historical manifests | **still resolved** — INV-8 / H9 intact; verified `173-S` is feature-first at `358b63b4` |
| P1-2 no red phase for contract surfaces | **still resolved** — CLASS 2 doc-contract tests |
| P1-3 R1 had no defined failure behavior | **still resolved** — `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` |
| Cycle-3 P1-1 unsatisfiable red matrix | **resolved by Group A** — verified satisfiable against the live predicate |
| Cycle-3 P1-2 fixture-as-engine-proof | **resolved by Group B** — 0 residual operative claims |
| Cycle-3 P1-3 retrospective snapshot | **resolved and strengthened by Group C** — 14 rows, non-vacuous assertions |
| Cycle-3 P1-4 stale closure artifact | **still correctly routed** — `docs/closure/**` untouched (H18); prerequisite remains **OPEN and Ship/operator-owned** |
| Cycle-3 P1-5 byte-for-byte contract | **still resolved** — exact parsed-scalar equality |

### Findings — P0 (blocking)

**None.** 0 P0.

### Findings — P1 (blocking)

* **P1-C4-1 — The plan mandates a NON-CANONICAL verification gate, contradicting
  durable learning `097-S`.**
  *Raised by: Learnings Researcher + Python Reviewer (merged; conservative
  severity retained).*

  **What the plan says.** §3 **U6 item 2** instructs *"Run `pytest`, …"* — a bare
  repository-root invocation. §8 **Runtime Verification and Closure** opens with
  *"`pytest tests/` green …"*.

  **What the compound library already resolved.**
  `docs/compound/097-S-canonical-unittest-gate.md` (shipment `097-S`, feature
  `092-F`, PR 241) records the durable rule:

  > The source-validation gate for autoharness is the standard-library unittest
  > suite: `PYTHONPATH=src python -m unittest discover -s tests`. … A repository-root
  > `python -m pytest -q` invocation is **not canonical for this workspace**.

  **The precondition is still live — verified this cycle, not assumed.**
  `pyproject.toml` `[tool.pytest.ini_options]` still declares **only**
  `pythonpath = ["src"]` — **no `testpaths`, no `norecursedirs`** — and
  `references/` currently contains **199 `test_*.py` files**. A bare root
  `pytest` will therefore still wander into vendored reference repositories and
  fail during collection with unrelated import-file-mismatch errors. 097-S
  states the consequence explicitly: *"Using the wrong gate can falsely block a
  shipment after its real CI-equivalent suite is green."*

  **The plan also contradicts itself.** Decision **D16** (§5) argues for the
  test-split on the express ground that a per-test result is *"mechanically
  verifiable by the plain `python -m unittest discover -s tests` invocation
  **this plan mandates**"*. **The plan does not in fact mandate it anywhere** —
  §8 and U6 mandate `pytest`. D16's load-bearing justification for Group A rests
  on a gate the plan never actually declares.

  **Why P1 and not P0.** No unsafe or destructive authorization results, and the
  blast radius is bounded because the **coupled task record `166.006-T` already
  states the correct gate** (*"run the full suite (`python -m unittest discover
  -s tests`, and pytest if configured)"*). The exposure is a **false-block /
  non-canonical-evidence** risk plus an unsupported premise under D16 — an
  **absent/incorrect verification** gap, which is squarely P1.

  **Why P1 and not P2.** §8 is the plan's *closure gate* surface. A closure gate
  that names a known-broken command in a workspace where the breakage is
  documented, reproducible, and currently unremediated is a verification defect,
  not a wording preference. It is also exactly the **coupled-surface drift
  class** that cycle 3's own **S-3** finding identified as the most significant
  result of its sweep — here inverted, with the **task record correct and the
  plan stale**.

  **Recommended correction (NOT applied — see gate decision).** In §3 U6 item 2
  and §8, replace the `pytest` invocations with
  `PYTHONPATH=src python -m unittest discover -s tests` as the canonical gate,
  retaining `pytest tests/` only as an explicitly secondary, path-scoped
  convenience run; and add `097-S` to the plan's referenced learnings so D16's
  premise is sourced.

### Findings — P2 (non-blocking; follow-ups)

* **P2-C4-7 (new)** — **U6 sizing drift inside the plan.** §3's U6 heading still
  reads *"size S, complexity medium"*, while the **Revision-4 Impact Re-check**
  raises U6 to **`S` / `high`**. The authoritative backlog record `166.006-T`
  **already carries `complexity: high`**, so there is **no downstream drift** and
  the two-axis gate was satisfied (the `complexity: high` split/de-risk
  obligation is discharged by G1/G2/G3's existing STOP-gated decomposition). All
  five other units match their records exactly (`166.001-T` M/high, `166.002-T`
  M/medium, `166.003-T` M/medium, `166.004-T` M/medium, `166.005-T` M/high).
  **Single stale surface; update the §3 heading.**
* **P2-1 … P2-6** — carried forward from cycle 3, all still open and advisory
  (upstream `parent_id` report `63363CF5`; `168-S` unclassified; repo-internal
  engine-characterization harness; `2B42392E` over-archival; closure-artifact
  naming lint; YAML-contract doc-lint).

### Findings — P3 (advisory)

* **P3-C4-6 (new, Architecture Strategist)** — The Revision-4 re-check omits the
  `### Revision-N risky actions` and `### Safety mode` subsections that the
  revision-2 and revision-3 re-checks both carry. The equivalent content **is**
  present (the Blast-radius delta table covers `freeze-scope` **UNCHANGED** and
  authorization strength **strictly reduced**), and the **`strict-safety` pack is
  not enabled in this workspace**, so the plan-review strict-safety FAIL row does
  **not** apply. Structural consistency only.
* **P3-C4-7 (new)** — §7 *"Requires plan hardening"* enumerates revisions 1/2/3
  and cross-references only the Revision-2 and Revision-3 re-check sections;
  **revision 4 is not listed**, though its re-check exists and concludes 5/5.
* **P3-C4-8 (new, Security Lens)** — The canonical containment check raises
  `ValueError`, not the declared `AssertionError`, for a **cross-drive** escape on
  Windows, because `os.path.commonpath` rejects mixed drive letters. It **still
  fails closed** (the exception propagates and the test errors), so this is not a
  safety gap; consider wrapping in `try/except ValueError` and re-raising as the
  declared containment error for a clearer diagnostic.
* **P3-C4-9 (new)** — The protected-invariant table orders **H19/H20/H21 between
  H16 and H17**, so it is not ordinal. Harmless, mildly confusing to scan.
* **P3-1 … P3-5** — carried forward from cycle 3, all still advisory.

### Scope boundary audit (re-run)

No unit touches `173-S`, `165.007-T`, `165.010-T`, the `160-F` family, `174-S`'s
`dependencies`/`labels`, or `docs/closure/**`. Revision 4 adds **no** module,
**no** unit, and **no** file to `freeze-scope`; it adds six test **functions** and
~4 lines of containment check inside existing test setup. **Authorization
strength is strictly reduced**: Group B forbids unproven engine behaviour from
authorizing `CASCADE`, Group C replaces a false evidential claim with a narrower
true one, and Group D **revokes** a write/delete permission. **No P-001
authority, bootstrap grant, or claimability change is introduced.**

### Constitutional compliance

| Principle | Verdict at cycle 4 |
|---|---|
| **II — test-first** | **satisfied** — red phase verified satisfiable against the live predicate; Group A's split makes the CLASS 4 before/after green pair obtainable |
| **IV — CLI workspace containment** | **now satisfied** — the revision-3 `%TEMP%` carve-out is withdrawn; scratch root verified git-ignored with a fail-closed realpath check |
| **VII — destructive command approval** | **now satisfied** — automatic tmpdir cleanup withdrawn; all deletion routed through the D6 approval sequence |
| **Evidence honesty** | **strengthened** — 0 residual operative fixture-as-engine-proof claims; all checked evidence re-derived true |
| **P-010 role boundary** | **preserved** — `docs/closure/**` untouched (H18) |

### Hardening requirement

Plan hardening was **required** (5/5 signals) and **is satisfied**: the mandatory
P-006 Revision-4 Impact Re-check was run in full and returned **PASS**
(`freeze-scope` unchanged, blast radius contracting, H19–H21 added, no new
implementation surface). This review **confirms** that verdict. The
`strict-safety` overlay is **not enabled** in this workspace, so the
`ProposedAction`/`ActionRisk` FAIL row is not triggered; the plan supplies that
classification voluntarily regardless.

### Gate decision

**`decision: FAIL`** — **0 P0**, **1 P1**, **1 new P2** (+6 carried), **4 new P3**
(+5 carried).

Revision 4 is, on the evidence, a **high-quality, strictly narrowing revision**:
all four P1 groups are correctly resolved, every load-bearing factual claim was
independently re-derived and found **true**, the coupled-surface propagation is
complete, and two constitutional violations present in revision 3 are now
**cured**. The single P1 is **not** a defect introduced by revision 4 — it is a
**pre-existing verification-gate error inherited from revision 1** that revision
4's own decision **D16** newly leaned on, which is what surfaced it.

**Per the Stage stop condition, all three review-fix cycles are exhausted, and
the operator's override authorized exactly ONE cycle-4 run and explicitly did
NOT authorize a further fix cycle. No fix is applied. This P1 is HALTED and
REPORTED for operator disposition.**

**Operator disposition required — one of:**

| Option | Effect |
|---|---|
| **(a) Authorize a bounded revision-5 correction** of P1-C4-1 only (two lines in §3 U6 item 2 and §8, plus a `097-S` reference) | Closes the P1. Narrow, mechanical, non-scope-changing; no new hardening signal |
| **(b) Accept the P1 and proceed**, directing Ship to execute the gate as stated in `166.006-T` (`python -m unittest discover -s tests`) and to treat the plan's `pytest` wording as superseded by that record | Proceeds with the defect recorded and explicitly overridden at the execution surface |
| **(c) Accept as-is with no direction** | **Not recommended** — risks a false shipment block via root-`pytest` collection failures in `references/`, the precise failure 097-S documents |

**Stage takes no option unilaterally, applies no fix cycle, and does not declare
this plan harvest-ready while a P1 is open.**

> **✅ DISPOSITION RECORDED 2026-09-16 — OPTION (a) SELECTED; P1-C4-1 IS
> RESOLVED.** The operator selected option **(a)** and recorded an explicit,
> narrowly bounded override: apply **revision 5 ONLY** to resolve **P1-C4-1**,
> then perform **one focused `plan-review` verification over that exact
> correction**. The override did **not** reset counters, did **not** authorize
> any broader fix, did **not** waive P0/P1, and did **not** alter any
> implementation, claim, or closure gate. Revision 5 landed the correction and
> `## Plan Review — Cycle 4 Verification Pass (revision 5, focused)` returned
> **`decision: PASS`** with **0 P0 / 0 P1**. **P1-C4-1 is CLOSED.** The P2/P3
> findings recorded in this cycle-4 section remain **carried and open** as
> non-blocking follow-ups.

---

## Plan Hardening — Revision-5 Impact Re-check (P-006, MANDATORY)

**Trigger.** Revision 5 edits a hardened plan in response to a **P1-class**
finding (`P1-C4-1`). P-006 requires the hardening impact check to be **re-run**
on any P1-class revision, independently of the `plan-review` cycle counter. It is
run here in full, and is **not** abbreviated because the change is small.

### Hardening signal re-assessment

| Signal | Rev-4 | Rev-5 | Note |
|---|---|---|---|
| Destructive or irreversible operation | present | **present** | **unchanged** — revision 5 touches no deletion, rollback, or D6 surface |
| Safety/authorization predicate change | present | **present** | **unchanged** — U2's predicate replacement is untouched |
| Cross-surface contract (mirrors, schema, gates) | present | **present** | **unchanged** — the four contract files and two mirrors are untouched |
| Historical/immutable-evidence dependence | present | **present** | **unchanged** — `358b63b4`/`e4ca20e5` pinning untouched |
| Multi-agent handoff (Stage→Ship) | present | **present** | **unchanged in kind**; the *content* of the handed-off verification instruction is corrected |
| **Total** | **5/5** | **5/5** | hardening remains **mandatory and satisfied** |

**No new hardening signal is introduced by revision 5.**

### Blast-radius delta (revision 5)

| Dimension | Delta | Assessment |
|---|---|---|
| New source modules / units / tasks | **none** | revision 5 is a planning-document correction only |
| Implementation surface | **none** | no file in `freeze-scope` gains or loses work |
| `freeze-scope` | **UNCHANGED** | no scope added or removed |
| Authorization strength | **unchanged** | no authority granted, widened, or narrowed; a *verification instruction* is corrected |
| Evidence surface | **improved** | replaces a gate that could **falsely block** a green shipment with the canonical gate; demotes `pytest tests/` to non-authoritative |
| Self-consistency | **improved** | D16's justification now matches what §3 U6 item 2 and §8 actually mandate |
| Test count / sizing | **unchanged** | U6 stays `size: S`, `complexity: medium`; no unit approaches the 2-hour rule |
| Reversibility | **unchanged** | text-only change to a Stage-owned planning artifact |

**Net blast-radius direction: NEUTRAL-to-NEGATIVE.** Revision 5 removes a
false-block risk and grants nothing.

### Protected invariants

**H1–H21 re-checked; all still hold.** Revision 5 adds **no** new invariant —
the canonical-gate rule is an existing durable learning (`097-S`), now cited
and mandated rather than newly invented.

### Constitutional re-check

| Principle | Verdict at revision 5 |
|---|---|
| **II — test-first** | **satisfied, unchanged** — the red/green class obligations are untouched; only the runner invocation that observes them is corrected |
| **IV — CLI workspace containment** | **satisfied, unchanged** — the canonical invocation reads and writes nothing outside the repository |
| **VII — destructive command approval** | **satisfied, unchanged** — no deletion surface touched |
| **P-010 role boundary** | **preserved** — only Stage-owned planning/backlog/memory artifacts were edited; `docs/closure/**`, source, tests, templates, schemas and `.github/` untouched; no build or test execution |

**Revision-5 hardening re-check: PASS.**

---

## Plan Review — Cycle 4 Verification Pass (revision 5, focused)

> **⚠️ HONEST NUMBERING — THIS IS NOT A FIFTH REVIEW CYCLE.** The per-plan
> `plan-review` **cycle counter remains at 4** and is **not** reset. This section
> records the **single focused verification pass** the operator authorized as
> part of the **cycle-4 disposition option (a)**: verify **exactly** the
> revision-5 correction of **P1-C4-1**, nothing broader. It does **not** re-open
> or re-adjudicate revisions 1–4, and it grants **no** additional fix cycle. Per
> the operator's bound: **if any P0/P1 beyond P1-C4-1 were found, or if the
> correction had introduced broader changes, the mandate was to halt with no
> further edits.**

`dispatch_mode: single-agent-declared-degradation`

`decision: PASS`

### Scope of this pass (declared up front)

| In scope | Out of scope |
|---|---|
| The revision-5 edits only: frontmatter `revision`/`revision_note`, the REVISION 5 banner, §1 referenced-durable-learnings table, §3 U6 item 2, §5 D16, §7 hardening-pointer line, §8, the revision-4 banner's review-cycle-accounting supersession note, the cycle-4 disposition note, and the revision-5 hardening re-check | Revisions 1–4 substance, all units U1–U6, all decisions other than D16's cited invocation, `freeze-scope`, closure scope, claimability, the carried P2/P3 backlog, and the Ship/operator-owned `173-S` closure prerequisite |

### Dispatch capability and declared degradation (P-012)

| Capability | Status | Disposition |
|---|---|---|
| Reviewer subagent dispatch | `TOOL_UNAVAILABLE` | No dispatch surface exposed in this session. Declared fallback applied: **inline single-agent persona pass**, one finding list per persona, normalized to P0–P3. Recorded, **not** silently skipped |
| Model-specific / anchor reviewer routing | `TOOL_UNAVAILABLE` | `model_routing.anchor_review` not dispatchable; Architecture Strategist rubric applied inline with the caller's model |
| Indexed knowledge retrieval (`agent-engram`) | `ENGRAM_DEGRADED` | Fell back to `git`/`grep`/file reads for all discovery |
| Documentation retrieval (`graphtor-docs`) | `GRAPHTOR_UNAVAILABLE` | Fell back to direct reads under `docs/` |
| Intercom visibility (`agent-intercom`) | `INTERCOM_DEGRADED` | No phase broadcasts emitted; non-destructive work continued |
| Backlog registry (`backlogit`) | `TOOL_OK` | MCP probes succeeded; `INDEX_SYNC_OK` (1229 items) |

Consistent with cycles 1–4. **Every selected persona was covered; none was
skipped for dispatch reasons.**

### Persona coverage

Selected **7**, ran **7** — the same 7 as cycle 4 (Security Lens stays triggered,
because the revision-4 Group D containment surface it was triggered by is still
present in the plan under review).

| Persona | Mode | Result over the revision-5 correction |
|---|---|---|
| Constitution Reviewer | inline pass | **0 P0 / 0 P1** — Principles II, IV, VII untouched and still satisfied; evidence honesty **improved** (the D16 mismatch is recorded, not quietly erased) |
| Python Reviewer | inline pass | **0 P0 / 0 P1**, 1 P3 — invocation is correct for this layout: `PYTHONPATH=src` puts the `src/` package root on `sys.path`, `-m unittest discover -s tests` confines discovery to `tests/`, so vendored `references/*` is never collected |
| Scope Boundary Auditor | inline pass | **0 P0 / 0 P1** — no unit, task mapping, decision outcome, `freeze-scope` member, closure-scope member, authorization, or claimability changed; verified by direct re-read of §3 U1–U6, §4, §5 D1–D17 and §7 |
| Learnings Researcher | inline pass | **0 P0 / 0 P1**, 1 P3 — `097-S` is now cited by path with shipment/feature/PR provenance and a stated binding effect; the mandated string matches the learning's durable rule **verbatim** |
| Architecture Strategist | inline pass (anchor route unavailable) | **0 P0 / 0 P1**, 1 P3 — no architectural surface is touched; the change strictly removes a false-block failure mode |
| Agent-Native Parity Reviewer | inline pass | **0 P0 / 0 P1** — no MCP tool, no agent-facing action surface, and no new agent instruction contract is introduced |
| Security Lens Reviewer | inline pass | **0 P0 / 0 P1** — no trust boundary, credential, network, or destructive-operation surface is touched; `PYTHONPATH=src` only prepends an in-repository path |

### Verification of the correction (independent re-derivation)

Each check below was re-derived from the working tree, not taken from the
revision-5 banner's own claims.

| # | Check | Result |
|---|---|---|
| V-1 | §3 U6 item 2 mandates the canonical gate | **TRUE** — reads `PYTHONPATH=src python -m unittest discover -s tests` with the PowerShell equivalent; the prior "Run `pytest`" instruction is present **only** inside an explicit withdrawal notice |
| V-2 | §8 mandates the canonical gate | **TRUE** — "`pytest tests/` green" replaced by the canonical gate; `pytest tests/` retained **only** as a declared secondary, non-authoritative convenience run; bare root `pytest` explicitly **PROHIBITED** as a gate |
| V-3 | D16 now matches what the plan mandates | **TRUE** — D16 names `PYTHONPATH=src python -m unittest discover -s tests` and cites **§3 U6 item 2** and **§8**, the two surfaces that now mandate it, and records the pre-revision-5 mismatch instead of hiding it |
| V-4 | Direct `097-S` reference added | **TRUE** — §1 "Referenced durable learnings" cites `docs/compound/097-S-canonical-unittest-gate.md` (shipment `097-S`, feature `092-F`, PR 241) with its binding effect; **file existence confirmed** |
| V-5 | Mandated string matches `097-S` verbatim | **TRUE** — byte-identical to the learning's durable rule; the PowerShell form matches the learning's own code block |
| V-6 | P1-C4-1 precondition re-verified still live | **TRUE** — `pyproject.toml` `[tool.pytest.ini_options]` declares **only** `pythonpath = ["src"]` (no `testpaths`, no `norecursedirs`); `references/` currently holds **199** `test_*.py` files. The correction is therefore **necessary**, not cosmetic |
| V-7 | No residual **operative** `pytest`-as-gate mandate anywhere in the plan | **TRUE** — every surviving `pytest` occurrence is inside a withdrawal notice, an explicit prohibition, the demoted-convenience-run clause, or a historical review/disposition record |
| V-8 | Coupled Stage-owned surfaces carry no contradictory canonical-gate text | **TRUE** — `166.006-T` (item 2) and `166.002-T` (acceptance line) already state `python -m unittest discover -s tests`; `166.006-T` was **not modified** and remains correct, as the operator required |
| V-9 | Correction introduced no broader change | **TRUE** — units, task mapping, dependency graph, decisions D1–D15/D17, `freeze-scope`, closure scope, blast radius, authorization and claimability are all textually unchanged; the only non-P1-C4-1 edits are factual cross-reference/status annotations (§7 hardening pointers, the revision-4 accounting supersession note, the cycle-4 disposition note) required to keep this revision self-consistent |
| V-10 | P-010 role boundary held during the correction | **TRUE** — only Stage-owned planning/backlog/memory artifacts edited; no source, test, template, schema, `.github/`, or `docs/closure/**` file touched; **no build or test executed**; no commit, push, PR, or shipment claim |

### Findings — P0 (blocking)

**None.** 0 P0.

### Findings — P1 (blocking)

**None. 0 P1.**

**`P1-C4-1` — RESOLVED.** The plan now mandates the canonical gate on both
surfaces, D16's justification is true as written, and `097-S` is referenced
directly. **No P1 beyond `P1-C4-1` was found**, and the correction **did not**
introduce broader changes, so the operator's halt condition did **not** fire.

### Findings — P2 (non-blocking; follow-ups)

**0 new.** The **7 carried** P2 items from cycles 1–4 are **unchanged and still
open**; this focused pass did not re-adjudicate them and does not close them.

### Findings — P3 (advisory)

**3 new** (+**9 carried**, unchanged):

* **P3-R5-1** (Python Reviewer) — §8 states the canonical gate but does not
  repeat `097-S`'s recommendation to record the result verbatim
  (`Ran NNN tests ... OK`); §3 U6 item 2 does. Harmless duplication gap.
* **P3-R5-2** (Learnings Researcher) — `166.006-T` and `166.002-T` state the
  short form `python -m unittest discover -s tests` without the `PYTHONPATH=src`
  prefix. Treated as **under-specified, not contradictory** (the operator
  affirmed `166.006-T` as correct and it was deliberately left unmodified);
  a future non-blocking harmonization could align all four surfaces on the
  full canonical string.
* **P3-R5-3** (Architecture Strategist) — cycle-3 advisory **P3-5** (record each
  test's red-phase class as a **pytest marker**) is now **inert** under the
  canonical `unittest` gate. It lives in a historical review section, which was
  deliberately **not** rewritten; if ever actioned it must be re-expressed in
  `unittest` terms.

### Hardening requirement

Plan hardening remains **required** (5/5 signals) and **is satisfied**: the
mandatory P-006 **Revision-5 Impact Re-check** was run in full and returned
**PASS** (no new signal, `freeze-scope` unchanged, blast radius neutral-to-
contracting, H1–H21 all still holding). This pass **confirms** that verdict.

### Gate decision

**`decision: PASS`** — **0 P0**, **0 P1**, **0 new P2** (7 carried, open),
**3 new P3** (9 carried, open).

Revision 5 does **exactly** what the operator authorized and **nothing more**:
it closes `P1-C4-1`, removes a self-contradiction, and cites the governing
durable learning. **Scope was not expanded, no counter was reset, no P0/P1 was
waived, and no implementation, claim, or closure gate was altered.**

**Consequence for `174-S`.** Readiness blocker **(1) OPEN P1-C4-1 is CLEARED**.
Readiness blocker **(2) — the superseding `173-S` closure record of record —
remains OUTSTANDING and is Ship/operator-owned** (`docs/closure/**` is outside
Stage's authority, H18 / P-010). **`174-S` therefore remains queued and NOT
claim-ready**, and Stage neither claims it nor declares closure readiness. Stage
also takes no harvest action beyond what is already recorded: the `166-F`
hierarchy and the `174-S` manifest are unchanged by this pass.
