# Stage session memory — 156-S review-fix cycle 3 (FINAL cycle)

* **Date**: 2026-08-28
* **Branch**: `chore/stage-156-S` · **HEAD at session start**: `e3b2f591`
* **Shipment**: `156-S` (queued, unclaimed) · **Feature**: `148-F`
* **Cycle**: 3 of 3 — **the review-fix budget is now exhausted**
* **Supersedes**: `docs/memory/2026-08-28-stage-156s-blocked-review-repair.md`
  (cycle 1) and the cycle-2 record embedded in the plan's Amendment record
* **Scope**: Stage-owned S0 plan/backlog correction only. No source, template,
  schema, config, build, commit, push, PR, claim, or Ship invocation (P-010).

## Findings closed

| # | Finding | Fix | Artifacts |
|---|---|---|---|
| **P1-1** | `{{BUILD_CHECK_COMMAND}}` bound to `pip install -e .` (profile `build.command`) | New plan decision **D9** binds it to the authoritative manifest value `python -m py_compile src/autoharness/cli.py`; `BUILD_COMMAND` vs `BUILD_CHECK_COMMAND` semantics separated; **D9-A** value-level assertion added | plan U1/D9/D2-table/RK-A/U8-scenario-1/hardening, `148.001-T`, `148-F`, `148.008-T` |
| **P1-2** | `{{principle_number}}` unaccounted for | **D8-D** rewritten as **one named rule** `EXEMPT_OUTPUT_SCHEMA_EXEMPLARS` over a **closed 3-token allow-list** scoped to fenced output-schema blocks | plan D8-D/U8/hardening, `148-F` DoD, `148.003-T`, `148.008-T` |
| **P2** | Bare zero-placeholder assertions in U4/U5/U6 | Each now incorporates D8-D by name with the closed allow-list and per-template line evidence | `148.004-T`, `148.005-T`, `148.006-T` |
| **P3-a** | `148.004-T` said "all 11 personas" | Corrected to **13** (U4 4 + U5 4 + U6 5) | `148.004-T` |
| **P3-b** | Plan U8 heading "Scenarios (4)" | Corrected to **Scenarios (5)** | plan U8 |
| **P3-c** | Verdict rationale "max 4 files / max 4 scenarios" | Corrected to **U6=5 files, U8=5 scenarios** with a 2-hour-rule justification that does not weaken the rule | plan verdict rationale |

## Authoritative binding evidence (P1-1)

`.autoharness/harness-manifest.yaml` `variables:` declares **two distinct**
variables. They are not interchangeable and neither is edited by this shipment:

| Variable | Value | Meaning | Bound by U1? |
|---|---|---|---|
| `BUILD_COMMAND` | `pip install -e .` | install/build the distribution | **No** — not referenced by the registry template |
| `BUILD_CHECK_COMMAND` | `python -m py_compile src/autoharness/cli.py` | cheap **compile check** | **Yes** |

`templates/policies/workflow-policies.md.tmpl` references
`{{BUILD_CHECK_COMMAND}}` at exactly two sites, both requiring a *compile*
property:

* **L48** — harness-architect postcondition: "the harness compiles
  (`{{BUILD_CHECK_COMMAND}}`)".
* **L88** — red-phase precondition: "`{{BUILD_CHECK_COMMAND}}` exits 0 AND
  `{{TEST_COMMAND}}` exits non-zero with expected failure markers".

**Key lesson (D9-A, and the reason this defect survived two prior reviews): a
resolved placeholder is not a correct placeholder.** Every assertion the plan
previously carried was resolution-shaped (`zero unresolved {{...}}`), and a
wrong value resolves exactly as cleanly as a right one. Where a binding is
contested or semantically load-bearing, assert the **value**.

## Exemption evidence (P1-2)

Enumerated all `{{...}}` tokens across the 13 S0 persona templates. The
output-schema exemplar set inside fenced code blocks is exactly three:

| Token | Occurs in | Evidence |
|---|---|---|
| `{{file_path}}` | 11 of 13 persona templates | e.g. `constitution-reviewer.agent.md.tmpl` L38 |
| `{{line_number}}` | 10 of 13 persona templates | e.g. `constitution-reviewer.agent.md.tmpl` L39 |
| `{{principle_number}}` | `constitution-reviewer.agent.md.tmpl` **only**, **L43** | inside the same ```json fenced block |

All three are **exemplar tokens intentionally retained** as literal installed
content (they describe the JSON a reviewer subagent emits at review time). They
have no install-time value and **must not be bound to fabricated content** —
inventing a value for `{{principle_number}}` is a hard stop.

## Additional same-class defect found by the cycle-3 sweep

`templates/policies/workflow-policies.md.tmpl` **L359** carries a **literal
`{{...}}` ellipsis meta-token** in P-013.5 fail-closed-verification prose
("`model_family` / `model_provider` is empty or an unresolved `{{...}}`
placeholder"). It is intended literal registry content and survives the render,
so the registry's bare zero-placeholder assertion was **impossible as written** —
the same defect class as P1-2, on the registry surface. Closed by **D9-B**'s
named `EXEMPT_POLICY_PROSE_META_TOKEN` rule over a closed **1-token** allow-list.

**Final exemption inventory** — two rules for the placeholder scan, plus one
separate route exemption; three distinct things that must never be conflated:

1. `EXEMPT_OUTPUT_SCHEMA_EXEMPLARS` (D8-D) — personas, closed 3-token list,
   fenced output-schema blocks only.
2. `EXEMPT_POLICY_PROSE_META_TOKEN` (D9-B) — registry, closed 1-token list.
3. U8 scenario 2's `{{PRIMARY_LANGUAGE_LOWER}}` route EXPAND/EXEMPT branch —
   a *route-resolution* concern, not a placeholder-scan concern.

## Plan review state

**`decision: PASS` RETAINED, not re-run.** Contract-completion test applied and
recorded in the plan's "Amendment record — review-fix cycle 3": no unit added,
no change to files created/modified, INV-1…INV-5 unchanged, Q1/Q5/Q7 unchanged,
Ship's discretion strictly **narrowed** (a wrong pinned value replaced with the
authoritative existing one; an allow-list closed at three named tokens), and no
new content enters the product. Terminal gate markers remain unambiguous, with
the final fenced block at end-of-file:

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

The superseded 2026-08-27 verdict block is left **byte-intact** behind an
explicit non-operative STALE-COUNT MARKER — provenance is amended, never erased.

## Files and IDs changed

* `docs/plans/2026-08-27-policy-registry-and-review-persona-layer-plan.md`
* `.backlogit/queue/148-F.md` (DoD)
* `.backlogit/queue/148.001-T.md` (acceptance, description, impl-notes)
* `.backlogit/queue/148.003-T.md` (acceptance)
* `.backlogit/queue/148.004-T.md` (acceptance, impl-notes)
* `.backlogit/queue/148.005-T.md` (acceptance)
* `.backlogit/queue/148.006-T.md` (acceptance)
* `.backlogit/queue/148.008-T.md` (acceptance, description, impl-notes)
* `docs/memory/2026-08-28-stage-156s-review-fix-cycle-3.md` (this file)

All queue mutations were made through official backlogit operations
(`backlogit_update_item` section writes); bodies, sections, frontmatter,
`size`/`complexity`, labels, references, dependencies, and statuses preserved.

## State verified at session end

* `156-S` **queued and unclaimed**; manifest unchanged at 9 items
  (`148-F` + `148.001-T`…`148.008-T`); size composition `M:1, S:7`, unsized 0.
* `157-S` **queued**, still blocked by `156-S`. Execute `156-S` first.
* All `148.*` items **queued**. Dependency edges re-verified against the plan's
  dependency graph and match exactly: `148.002-T`←`148.001-T`;
  `148.005-T`←`148.003-T`; `148.006-T`←`148.003-T`;
  `148.007-T`←`148.001-T`,`148.004-T`,`148.005-T`,`148.006-T`;
  `148.008-T`←`148.002-T`,`148.007-T`.
* No shipment claimed, no Ship invoked, no source/template/config touched.

## What Ship must honour (delta since cycle 2)

1. `{{BUILD_CHECK_COMMAND}}` = `python -m py_compile src/autoharness/cli.py`
   (manifest `BUILD_CHECK_COMMAND`). **Not** `pip install -e .`, which is the
   separate `BUILD_COMMAND` and is bound nowhere in this render.
2. Assert the **value**, not just resolution: rendered L48/L88 clauses must
   contain the compile-check literal and the registry must contain no
   `pip install -e .` (D9-A).
3. The exemplar exemption covers **three** tokens including
   `{{principle_number}}` — one named rule, closed allow-list, fenced
   output-schema blocks only. Never bind any of them to invented content.
4. The registry needs its own separate named 1-token exemption (D9-B) for the
   literal `{{...}}` at template L359.
5. U8 has **5 scenarios**; U6 renders **5 files**; the persona set is **13**;
   installed artifacts total **14**.
6. Carried forward unchanged: `336F3AB7` already archived during staging (do not
   re-archive); no `.tmpl` may be edited; Q1/Q5/Q7 unchanged; S0 not waived;
   do not stage S2-S11; stash `D911A3B2` and `89E833E1` stay ACTIVE.

## Residual risk

**RK-K (extended)**. Resolved checkpoint `checkpoint-20260828-073155.json`
repeats the superseded two-token exemplar enumeration in its `resume_hint`.
backlogit exposes no official amendment path for a resolved checkpoint, and
hand-editing tool-owned state is forbidden, so it is left **byte-intact** and
superseded by this cycle's checkpoint (which records the complete three-token
rule). Contained: it is **resolved**, so the fail-closed recovery scan — which
partitions to `active` candidates — can never select it. Not a gate on
execution.
