---
title: P-020 Post-Merge Context Compaction — mandatory closure gate + dogfood drift fix
doc_type: plan
status: reviewed
created: 2026-07-29
feature: 098-F
shipment: 103-S
stash: 9940C563
deliberation: 009-DL
blast_radius: high
---

# Plan: P-020 Post-Merge Context Compaction

## Decision: (A) SHIPPABLE

Stash **9940C563** asks whether post-merge context compaction should be a
**mandatory** workflow step so context is consolidated after every merge. After
deliberation (**009-DL**), this is a clear, low-risk, environment-agnostic
design — **Option 3** — so the full Stage pipeline was run and a shipment
(`103-S`) was harvested. The (B) human-decision path was evaluated and rejected;
see *Why (A) not (B)* below.

## Problem

The stash proposes enforcing "/compact after each PR merge". Two autoharness
constraints reshape it:

1. **Environment-agnostic (core rule).** `/compact` is a Copilot-CLI-specific
   command and MUST NOT be hard-wired. The environment-agnostic mechanism already
   exists — the **compact-context skill** (Primitive 1), which consolidates
   memory/plan/closure artifacts into durable docs-root files and archives verbose
   originals. Prior spike **022-S**
   (`docs/exec-plans/2026-05-09-context-window-compaction-spike.md`) established
   that autoharness cannot hook `/compact` or in-conversation summarization — those
   are environment-controlled — and that compact-context is the file-level analog.
2. **Templates are the product.** A new policy belongs in the policy template; the
   wiring belongs in the relevant template artifacts; and (dogfood) the installed
   `.github/…` copies must stay coherent, matching how P-016/P-017 were woven.

### Current state (discovered)

* The Ship **template** (`templates/agents/_ship.agent.md.tmpl`) Step 6 closure
  **step 8 already mandates** `Invoke compact-context with target: all …` — it
  invokes the env-agnostic skill, not `/compact`. So per-merge invocation is
  already the intended design.
* But it is only a **bare "Mandatory" bullet** — not a first-class policy (no
  precondition/postcondition/gate-point/violation-action), not verify-asserted,
  not tune drift-detectable.
* **Drift:** the installed dogfood `.github/agents/_ship.agent.md` Step 5 closure
  has **already lost** that step (close-shipment → compound → docs → session memory
  → dark-mode summary → index resync; no compact-context). Direct evidence that
  doc-only guidance is insufficient.
* compact-context uses **threshold-based internal candidate selection**
  (`threshold_days=14`, `max_files=40`, `max_size_kb=500`; never compacts active
  checkpoints) and runs at **Tier 1 (fast/cheap)** — an idempotent no-op when
  nothing qualifies.

## Approach

Formalize the already-intended behavior as first-class policy **P-020**, wire it
consistently, fix the installed drift, and add a verify assertion so the gate is
machine-checked henceforth. **Key design:** decouple mandatory **INVOCATION**
(guaranteed at the Ship Step 6 post-merge closure boundary = per-merge) from
threshold-based **CANDIDATE SELECTION** (skill-internal, unchanged). Mandating
invocation is *not* mandating heavy compaction — the Tier-1 skill is a cheap
idempotent no-op when nothing qualifies, which neutralizes the cost/latency
objection.

Eight width-isolated tasks (each ≤2h), dependency-ordered:

| Task | Domain | Depends on |
|---|---|---|
| 098.001-T | Author P-020 in `workflow-policies.md.tmpl` + amendment log 1.15.0 | — |
| 098.002-T | Wire P-020 into Ship agent template (Step 6 step 8 + dark-mode summary) | 001 |
| 098.003-T | Wire P-020 into Orchestrator agent template (closure sequencing + DARK_MODE_COMPLETE) | 001 |
| 098.004-T | Reference P-020 in compact-context skill + Primitive 1/10 + context-efficiency instructions | 001 |
| 098.005-T | Enumerate P-020 in foundation templates (AGENTS + constitution) | 001 |
| 098.006-T | **Drift fix:** installed `.github/agents/_ship.agent.md` + `_orchestrator.agent.md` | 002, 003 |
| 098.007-T | Sweep P-020 into installed instruction/foundation copies (harness-architecture, AGENTS.md) | 004, 005 |
| 098.008-T | `ship_post_merge_compaction_gate` verify assertion + tests + manifest + gates (FINAL) | 001–007 |

## P-020 design (what 098.001-T authors)

* **Applies To**: `ship`, `orchestrator`, `compact-context`.
* **Gate Point**: Ship post-merge closure (Step 6).
* **Statement**: at every post-merge closure, invoke the env-agnostic
  compact-context skill (`target: all`). **No `/compact` literal.**
* **Precondition**: PR merged and Ship Step 6 entered.
* **Postcondition**: compact-context invoked before the shipment is declared closed.
* **Violation-Action**: **SKIPPING invocation** is a P-020 violation recorded via
  P-005 telemetry, and closure is treated as **incomplete** (shipment remains
  active under P-001 so it is caught/retried) — it does **not** hard-halt in a way
  that strands the merged PR. A **FAILED** compact-context run is **NON-BLOCKING**
  (log warning, continue): the merge already landed and the skill is
  non-destructive.
* **Relationship to P-001**: required post-merge compaction is part of the closure
  set that keeps a merged shipment in-flight until complete (composes with, does
  not duplicate, P-001).
* **Relationship to P-017**: in dark mode, closure must report compaction status
  before `DARK_MODE_COMPLETE`.

## Blast-radius file list

**Product templates (the product):**

* `templates/policies/workflow-policies.md.tmpl` — P-020 + amendment log 1.15.0
* `templates/agents/_ship.agent.md.tmpl` — Step 6 step 8 + dark-mode summary
* `templates/agents/_orchestrator.agent.md.tmpl` — closure sequencing + DARK_MODE_COMPLETE
* `templates/skills/compact-context/SKILL.md.tmpl` — When-to-Use (P-020 + invocation/candidate note)
* `templates/instructions/context-efficiency.instructions.md.tmpl` — cross-ref
* `templates/foundation/AGENTS.md.tmpl`, `templates/foundation/constitution.instructions.md.tmpl` — enumeration

**Dogfood installed copies (coherence, per P-016/P-017 weave):**

* `.github/agents/_ship.agent.md` — **drift fix** (add missing mandatory step)
* `.github/agents/_orchestrator.agent.md` — closure-sequencing note
* `.github/instructions/harness-architecture.instructions.md` — Primitive 1/10 note (global artifact — no template exists; edited directly, task 098.007-T)
* `AGENTS.md` — quality-gate/policy enumeration
* (verify during impl) `.github/copilot-instructions.md`, `.github/instructions/constitution.instructions.md` — only where a P-016/P-017 enumeration already exists

**Verification / test / manifest source:**

* `src/autoharness/verify_workspace.py` — `ship_post_merge_compaction_gate` in `FOUNDATION_ASSERTIONS`
* `tests/test_verify_workspace.py` — coverage
* `.autoharness/harness-manifest.yaml` — checksums/assertion-text for changed **installed** artifacts only

**Not tracked / not edited:** there is **no installed `workflow-policies.md`** in
the dogfood — the manifest tracks only installed `.github/…` copies and never
`templates/` — so P-020 is **defined only in the template**; dogfood copies
reference P-020 by ID. Confirmed: `Select-String templates/` → 0 manifest hits;
`workflow-policies` → 0 manifest hits.

## Completion gate

* Canonical gate: `PYTHONPATH=src python -m unittest discover -s tests`
  (CI surface, `.github/workflows/ci.yml:89`). Root `pytest` is **noncanonical**.
* **Applicability:** the build/test gate is **APPLICABLE to 098.008-T only**
  (it changes Python source + tests). Tasks 098.001–098.007 are docs/templates
  and installed-copy prose — their gate is markdown/frontmatter/cross-reference
  validation + no unresolved `{{VARIABLE}}`; the unittest build gate is **N-A**
  for them. `autoharness verify` is run in 098.008-T after the drift fix lands.

## Plan-harden (P-006)

High blast radius (workflow policy + closure sequencing + dogfood installed copies
+ verify/manifest) → hardening required and performed:

* **H1 — Env-agnostic fidelity (the #1 constraint).** Every task explicitly
  forbids a literal `/compact` and frames enforcement on the compact-context skill.
  Acceptance criteria on 098.001/002/003/004/006 each carry a "no `/compact`
  literal" check. Add a zero-residual guard in 098.008-T: grep touched templates +
  installed copies for a hard-wired `/compact` command token; assert none is
  introduced as an enforcement mechanism (documentation *about why we don't use it*
  is allowed).
* **H2 — Failure vs skip semantics (refined).** Resolved a latent ambiguity:
  SKIP = violation + closure-incomplete (P-001), **not** a hard halt that strands a
  merged PR; FAILED run = non-blocking warn+continue (non-destructive Tier-1 skill).
  Codified in 098.001-T acceptance criteria.
* **H3 — Verify/drift coupling.** `ship_post_merge_compaction_gate`
  (098.008-T) checks the installed `.github/agents/_ship.agent.md`, so it FAILS
  until 098.006-T fixes the drift. Dependency edges (008 → 006) enforce ordering,
  making the drift fix non-optional.
* **H4 — Manifest checksum method (CRLF-safe).** 098.008-T refreshes checksums
  using the repo's normalize-then-hash (LF, raw-bytes) recipe — `verify_workspace`
  hashes raw working-tree bytes, and a `.gitattributes eol=lf` pin only governs
  future conversion (lesson from the 097-F rename plan H2). Only changed **installed**
  artifacts are re-hashed; templates are not manifest-tracked.
* **H5 — Composition, not duplication.** P-020 composes with P-001 (closure set)
  and P-017 (dark-mode closure) via explicit "Relationship to" clauses rather than
  re-stating those policies, preventing conflicting gate definitions.
* **H6 — Mechanically verifiable acceptance.** Every task carries file-scoped,
  greppable acceptance criteria; the feature (098-F) records AC1–AC10.

## Plan-review outcome

Self plan-review across five personas (completeness, correctness, safety,
environment-agnostic fidelity, test/manifest integrity):

* **Completeness** — all stash touch points covered: workflow-policies (001),
  compact-context skill wiring (004), Ship closure (002/006), Orchestrator closure
  (003/006), P-017 dark-mode closure (002/003/006), two-agent Stage↔Ship handoff
  (resolved: no new Stage obligation; Orchestrator closure-gating in 003/006).
  Verify/drift-detection (008) and foundation enumeration (005/007) added.
* **Correctness** — P-020 gate point is post-merge closure (not a merge gate);
  Option 4 (block-merge) was correctly rejected.
* **Safety** — no destructive operations; compact-context archives, never deletes;
  verify coupling ordered by dependencies.
* **Env-agnostic fidelity** — every task forbids a hard-wired `/compact`; the
  design leans entirely on the existing compact-context skill.
* **Test/manifest integrity** — canonical unittest gate identified and scoped to
  098.008-T; manifest scope limited to installed copies (verified: 0 template hits).

Two precision issues surfaced and were fixed during hardening: **H2**
(skip-vs-failure semantics — avoid stranding a merged PR) and **H4**
(CRLF-safe checksum method). **Verdict: READY, P0 = 0, P1 = 0.**

## Why (A) not (B)

The only debatable points both resolve clearly:

* *"Force invocation even for tiny merges?"* — invocation is a ~one Tier-1
  directory scan and a no-op when nothing qualifies; the cost is negligible and the
  benefit (guaranteed consolidation floor + no silent drift) is real.
* *"Policy vs. mere guidance?"* — the observed drift (the installed Ship copy
  already lost the guidance-only bullet) is direct proof that first-class,
  verify-asserted policy is the correct remedy, consistent with the
  P-016/P-017/P-018/P-019 convention and the 010-S session-lifecycle-gate precedent.

No material, unresolvable product judgment remains, so this was harvested as a
shippable plan rather than escalated for human decision.

## Handoff

Ship implements shipment **103-S** (feature **098-F**, tasks 098.001–098.008-T)
in dependency order. Stage does not implement, build, branch, PR, or merge.
Backlog + plan artifacts are committed to **local `main` only** (not pushed);
the Orchestrator owns Step 1.5 staging and all merges.
