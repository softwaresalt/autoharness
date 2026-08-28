# Stage session — S0 + S1 portfolio staging (031-DL)

> **⚠️ PARTIALLY SUPERSEDED — 2026-08-28.** Two "Decisions worth carrying forward"
> entries below (**#2 `python-reviewer` has no template** and **#3 three persona
> templates deliberately NOT installed**) were **FALSE** and are **NO LONGER
> OPERATIVE**. They are retained verbatim, struck through and annotated in place,
> because they are the record of a measurement-shape defect worth compounding —
> not because they are true. **Authoritative correction:**
> [`docs/memory/2026-08-28-stage-156s-blocked-review-repair.md`](2026-08-28-stage-156s-blocked-review-repair.md).
>
> **Corrected canonical mapping**: `python-reviewer.agent.md` is a **render
> target**, not a missing template. Its canonical source is the **existing**
> `templates/agents/review/technology-reviewer.agent.md.tmpl`, mapped by installed
> `.github/skills/install-harness/SKILL.md` L1203
> (`technology-reviewer.agent.md -> .github/agents/subagents/{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md`)
> with `PRIMARY_LANGUAGE_LOWER: "python"` bound at `.autoharness/harness-manifest.yaml`
> L394. **No `python-reviewer.agent.md.tmpl` is authored.**
>
> **Corrected canonical persona set**: the Law-2 exclusion set is **EMPTY**. All 12
> `templates/agents/review/` templates plus `learnings-researcher` install, giving
> **13 personas / 14 installed artifacts** (was 11 / 12). `correctness-reviewer`,
> `maintainability-reviewer`, and `technology-reviewer` are **all** accounted for:
> the first two are "Always-on" per `install-harness/SKILL.md` L1200-L1201 and
> gate `tune-harness` L462-L469 drift detection; the third is the *source template*
> for `python-reviewer`, not a separate excluded identity.

* **Date**: 2026-08-27
* **Agent**: Stage (`claude-opus-5` / anthropic / high — route freshly resolved and honored)
* **Operator authorization (verbatim)**: `Approve Q1/Q5/Q7 as recommended; stage S0, then S1.`
* **Scope**: exactly two shipment units — **S0 then S1**. S2–S11 and S9 explicitly **not** staged.

## Outcome

| Unit | Feature | Tasks | Shipment | Items | Status |
|---|---|---|---|---|---|
| **S0** | `148-F` | 8 (`148.001-T`–`148.008-T`) | **`156-S`** | 9 | queued |
| **S1** | `149-F` | 11 (`149.001-T`–`149.011-T`) | **`157-S`** | 12 | queued |

`157-S` **depends_on** `156-S` (`blocks`), verified bidirectionally. Neither shipment claimed.

## Gate chain

Both plans ran impl-plan → plan-harden → plan-review and end with literal harvest markers.

* S0 — `docs/plans/2026-08-27-policy-registry-and-review-persona-layer-plan.md`
  * hardening triggered on **4/5** signals; `decision: PASS`
* S1 — `docs/plans/2026-08-27-pre-review-detector-sdk-plan.md`
  * hardening **mandatory** (critical new abstraction), **5/5** signals; `decision: PASS`

Both recorded `dispatch_mode: single-agent-declared-degradation`. This was **not** a
convenience fallback: reviewer subagent dispatch routes to
`.github/agents/subagents/*.agent.md`, which **does not exist** — that is S0's own GAP 2.
Every selected persona was covered inline. **If S1's successor review still cannot
dispatch after S0 lands, S0 did not actually close GAP 2.**

## Decisions worth carrying forward

1. **Q5 is load-bearing for S0, not just S4/S6.** The policy-registry template carries a
   `{{TEST_COMMAND}}` placeholder, so the approved
   `PYTHONPATH=src python -m unittest discover -s tests` is bound at render time.
   `workspace-profile.yaml` still declares `pytest` — the stale side, deliberately **not**
   fixed here (it feeds `profile_hash`).
2. ~~**`python-reviewer` has no template anywhere in the tree.** It is cited by
   installed skills but has no source; `language-engineer` is an implementation
   agent, not a substitute. S0 `148.003-T` authors it, fixed-name rather than
   `{{PRIMARY_LANGUAGE}}`-parameterized, because the skills cite the literal
   filename.~~
   **SUPERSEDED 2026-08-28 — THIS WAS FALSE.**
   `templates/agents/review/technology-reviewer.agent.md.tmpl` existed in-workspace
   the entire time and is the canonical source. `python-reviewer.agent.md` is its
   **render target** via `install-harness/SKILL.md` L1203 with
   `PRIMARY_LANGUAGE_LOWER: "python"`. `148.003-T` (U3) was repurposed from
   *template authoring* to *render-mapping and binding pinning*; **it authors no
   template**, and creating `python-reviewer.agent.md.tmpl` is now explicitly
   forbidden in this shipment. **Root cause worth compounding**: a filename search
   cannot find a template whose render target is renamed by a mapping.
   See `2026-08-28-stage-156s-blocked-review-repair.md`.
3. ~~**Three persona templates are deliberately NOT installed**
   (`correctness-reviewer`, `maintainability-reviewer`, `technology-reviewer`) —
   no citing reader, Law 2. The exclusion is asserted by a test so it stays
   intentional.~~
   **SUPERSEDED 2026-08-28 — THIS WAS FALSE, and the test that would have frozen
   it MUST NOT be written.** All three classifications were wrong:
   `correctness-reviewer` and `maintainability-reviewer` are cited by **bare
   filename** (`install-harness/SKILL.md` L1200-L1201 "Always-on";
   `tune-harness/SKILL.md` L462-L469 treats their absence as real local-first
   review drift) — a path-shaped grep structurally cannot see that citation shape.
   `technology-reviewer` is not a separate excludable identity at all; it is the
   source template for `python-reviewer`. **The Law-2 exclusion set is EMPTY**;
   all **13** personas install. `148.008-T` (U8) scenario 3 is INVERTED to assert
   reader *existence*, never absence.
   See `2026-08-28-stage-156s-blocked-review-repair.md`.
4. **`verify_workspace.py` contains two contradictory contracts** about
   `.github/policies/workflow-policies.md`: `_resolve_policy_registry` documents that the
   dogfood self-install *never* installs a mirror, while `DARK_FACTORY_ASSERTIONS` marks it
   `required: True`. S0 `148.002-T` reconciles this rather than fixing only the symptom.
5. **S1 does not refactor `topology.py`.** Cycle detection is mirrored self-contained.
   Generalizing `_dag_detect_cycle` would push S1's blast radius into P-001/P-016
   enforcement code. Deliberate, recorded duplication — this is what keeps `149.005-T` at
   medium rather than high complexity.
6. **P0 raised and contained in S1 review**: `producer.ref`/`validator.ref` resolve
   importable callables from configuration. Contained by a strict `autoharness.detectors`
   namespace allow-list; the PASS verdict is **contingent** on that containment surviving
   into the built artifact, enforced by `149.009-T`.
7. **Q1's persistence exception is conditional.** The report is derived evidence, not SSOT,
   with no read-back API and no blocking authority. **If S8 wires no named consumer, the
   writer must be withdrawn.**

## Stash disposition

* `336F3AB7` — **archived** (non-destructively, via `backlogit stash archive`) after lineage
  was preserved in `148-F` and shipment verification passed.
* `D911A3B2` — **ACTIVE, not archived.** Program frame; owns S1–S10.
* `89E833E1` — **ACTIVE, not archived.** Only split (a) staged; (b) → S8, (c) → S10;
  query/visualization pruned under Law 2.

## Verification

* `dag-readiness`: `ready_set=[156-S]`, `next_eligible=156-S` (`ready_set_head`),
  `cycle_detected=false`, `156-S` downstream dependents `[157-S]`, **`157-S` not in ready set**.
* Both manifests: `unsized: 0`, covering feature resolved and listed first.
* 151 shipment files scanned — **no duplicate ownership** of any of the 21 new IDs.
* `doctor`: 3 orphan findings, all pre-existing `048.*-T`, outside scope and untouched.

## Known degradations

`INTERCOM_DEGRADED`, `ENGRAM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`, reviewer-subagent dispatch
unavailable. Also: `.autoharness/backlog-registry.yaml` **omits a `features.sizing` key**
even though the MCP surface fully supports `size`/`complexity` — registry drift, worked
around by using the executable contract; worth correcting in a later housekeeping pass.

## Next actor

**Ship, via Orchestrator** — execute `156-S` first, then `157-S`. Watch `149.011-T`: the
RK1 falsification gate is a genuine early exit. If `ART-01` re-detects no historical defect,
**halt and escalate for the Option A reconsideration** rather than proceeding with a weaker
claim.
