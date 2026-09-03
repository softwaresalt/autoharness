---
type: session-memory
agent: stage
date: 2026-09-03
branch: chore/stage-159-167-publication
reviewed_head: 35c081d50efc78301d1f76ad1dbb25c92c117786
publication_base: origin/main 1d40c0babfc543a6c76e5a8eee73435957747afa
cycle: review-fix-cycle-1
verdict: READY_WITH_FOLLOWUPS
---

# Stage — Orchestrator review-fix cycle 1 (159-S … 168-S publication)

## Context

The Orchestrator's local review of reviewed HEAD `35c081d5` returned **BLOCKED**
with 20 numbered findings. Stage executed review-fix cycle 1: each finding was
adjudicated against **P-021 C1** (same-contract-surface test), legitimate defects
were remediated through **official backlogit operations**, false positives were
recorded with measured evidence, and genuinely out-of-scope work was captured as
**P-021 C2 compliant deferred entries**.

Hard constraints held throughout: **no** commits, pushes, or PR actions; **no**
source/template/schema/test implementation; **no** shipment claims; **no**
parallel worktrees. Verified at close: 0 commits ahead of reviewed HEAD, HEAD
still `35c081d5`, single worktree, all ten shipments still `queued`.

## Degradations declared (P-012)

| Capability | Status |
|---|---|
| engram (`get_workspace_status`) | `ENGRAM_DEGRADED` — file-based exploration |
| intercom | `INTERCOM_DEGRADED` — no operator broadcast |
| graphtor-docs | `GRAPHTOR_UNAVAILABLE` — grep over `docs/` |
| reviewer-subagent dispatch | `TOOL_DEGRADED` — `dispatch_mode: single-agent-declared-degradation`; full persona rubric applied inline |

## Finding adjudication (20 findings)

| # | Verdict | Resolution |
|---|---|---|
| 1 | Fixed | 16 compliant C2 captures created; all 10 pseudo IDs (`DSE-S3-1`…`DSE-S8-2`) replaced with generated IDs; 0 residual |
| 2 | Fixed (P0) | `160.005-T` rewritten to **red-harness-completion** semantics; green ownership assigned per case; full prerequisite DAG machine-encoded via `backlogit dep add` |
| 3 | Fixed (P0) | **H2 safety mode** (`careful` + `freeze-scope`) declared in plan and propagated verbatim into all 15 task records, incl. publication/rollback checkpoints |
| 4 | Fixed (P1) | Plan decomposition table rewritten in execution order with a Task ID column; all `(Tn)` back-refs corrected to T1–T15, no gaps or duplicates |
| 5 | Fixed (P0) | AC6 split into **AC6a** (Python pip/clone resolver) + **AC6b** (plugin-root resolver) with negative assertions and a mandatory disjointness assertion; AC7 rewritten as a channel × environment support matrix |
| 6 | Fixed (P1) | `build_support/**`, `dist/plugin/**`, manifest-by-name added to AC11; **AC2b** unbypassable in-job release gate; **AC2c** single deterministic generation command; **AC2d** centralized target-workspace classifier |
| 7 | Fixed (P1) | `160.008-T` split → `160.008/012/013-T`; additionally `160.004-T`→`160.014-T` and `160.006-T`→`160.015-T`. **15 tasks**, all ≤ 2h |
| 8 | Fixed (P2) | P2-8 / P2-9 removed from `160.011-T`; captured as `00C2B1F9` / `F73A04A2` with explicit C1 discrimination |
| 9 | **REJECTED** | False positive — see evidence below |
| 10 | Fixed | `154.001-T` corrected to `.github/agents/subagents/security-reviewer.agent.md` |
| 11 | Fixed | SHIP-4 Decision F rewritten into non-overlapping conditions A/B/C + F1-scope + negative assertion |
| 12 | Fixed | `156.002-T` **H6a-CLARIFICATION**: declaration identity vs. derived validation set |
| 13 | Fixed | SHIP-7 **H3a** (value equality over 6 surfaces) + **H3b** (closed 4-field override allow-list) |
| 14 | Fixed | SHIP-8 undefined budget **withdrawn**; replaced with `size_composition.unsized == 0` + B1–B5 boundary table; aggregate policy deferred as `C754A19B` |
| 15 | Fixed | SHIP-2 H2a binding + hermetic cases C1–C6 (added C4 wrong-host redirect, C5 malformed JSON, C6 mismatched version); recovery corrected to R1/R2/R3 against the actual single-job workflow |
| 16 | Fixed | `153.004-T` gains canonical token/digest vectors V-a…V-e; `153.002-T` prerequisite encoded |
| 17 | Fixed | 37 tasks normalized `autoharness-stage-2h-v1` → **`ah-stage-sizing-v1`**; 3 doc references updated; 0 residual |
| 18 | Fixed (scoped) | 0 bare `{{AUTOHARNESS_VERSION}}` remain in changed docs/queue — all backticked or reworded |
| 19 | Fixed | Spike **does** materially inform SHIP-2 → traceable link established (frontmatter + plan + `152-F` + `152.002-T`) |
| 20 | **REJECTED** | False positive — see evidence below |

### Recorded rejections

**Finding 9 — backlog template integrity.** Measured: **0 section markers across
all 1070 queue + archive records**. Section-aware read fails *identically* on the
long-shipped `013-S` (`backlogit get 013-S --section description` →
`Error: section "description" not found`) and on the brand-new `160.014-T`. All
shipments `159-S`–`168-S` **do** carry `title:`. Shipments are frontmatter-only
by tool design, so this is a workspace-wide storage-format property, not a defect
introduced by this branch. Deferred as `056DD04F`.

**Finding 20 — shipment 167→168 ordering.** The `167-S ← 168-S` edge is
**deliberately preserved**. The Orchestrator/Backlogit sequencing contract
explicitly permits `blocks` edges to encode deterministic one-at-a-time priority
order, and the operator explicitly required feature/refactor work *before*
documentation. That policy evidence defeats the maintainability reviewer's
"unrelated coupling" characterization. Removing the edge would also transiently
unblock a successor.

## Additional defects found by the Stage plan-review gate itself

1. **Authoring-surface defect (Architecture / template-integrity lens).** SHIP-4
   task 3 and `154.003-T` directed the executor to amend
   `templates/instructions/harness-architecture.instructions.md.tmpl`, which
   **does not exist**. `harness-architecture.instructions.md` is the *sole*
   manifest entry whose template field reads `"global instruction definition"` —
   it has no `.tmpl` source and is amended directly with a checksum refresh,
   while `role-enforcement.instructions.md` *is* template-backed. Corrected in
   both the plan and the task. Same defect class as finding 10.
2. **Schema publication layout (Learnings Researcher, P1).** Creating
   `payload-manifest.schema.json` at `1.0.0` is necessary but not sufficient
   against this repository's recorded *three-occurrence* schema-mutation-in-place
   bug class, whose shorter and more dangerous fix path applies exactly to
   contracts **unregistered in `SCHEMA_CONTRACTS`**. SHIP-10 now requires the
   versioned mirror `schemas/payload-manifest/1.0.0.schema.json`, registration in
   `src/autoharness/schema_contracts.py`, and a divergence assertion. Propagated
   into `160.001-T` and AC11.

## Deferred entries created (17, all full C2 payload)

`13F5EEF0` `A7AD3044` `24374649` `A4DAC571` `05877865` `0F6B2B3B` `9938CA1D`
`1747F703` `FE098366` `D456616B` `00C2B1F9` `F73A04A2` `CE441101` `C754A19B`
`056DD04F` `9B5FD7D5` `75A78433`

## Verification evidence

* **Schema validation** — 35 created/modified records via `backlogit doctor --target`: **all exit 0**.
* **SHIP-10 DAG** — topological sort terminates in 8 tiers over 15 tasks, roots `160.001-T` + `160.002-T`, single sink `160.011-T`. **Acyclic.**
* **Shipment `168-S`** — 16 items (`160-F` + 15 tasks); `size_composition`: 15 members, **`unsized: 0`**, histogram `{M:5, S:10}`.
* **Shipment chain** — `159→160→161→162→163→164→165→166→168→167`; exactly one ready root, acyclic.
* **Cross-references** — every referenced path in the 9 changed plans resolves, except 6 intentional cases (4 artifacts SHIP-10 *creates*, 1 negative assertion that must stay absent, 1 explicitly rejected placement).
* **Residual tokens** — 0 `DSE-S\d`, 0 `autoharness-stage-2h-v1` (except the intentional backticked audit note), 0 bare `{{AUTOHARNESS_VERSION}}`.
* **`backlogit doctor`** — 63 issues (59 `archived_from_self_ref` + 4 `orphaned_artifact`). Cross-checked all 63 flagged IDs against the 98 `.backlogit` records modified this session: **overlap ZERO**. Pre-existing baseline, deferred as `75A78433`.
* **P-010** — 0 source/test/template/schema/config files modified. Changes confined to `.backlogit/` (98) and `docs/` (10).

## Next steps

1. Orchestrator re-reviews the working tree (all changes **uncommitted**).
2. Orchestrator decides the disposition of
   `docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`
   — Stage established the traceable link rather than deleting it (finding 19).
3. Ship claims `159-S` first once the publication lands.
