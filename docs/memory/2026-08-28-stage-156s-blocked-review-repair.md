---
title: "Stage session — 156-S BLOCKED-review repair"
date: 2026-08-28
agent: stage
session_id: "stage-2026-08-28-156S-blocked-review-repair"
branch: "chore/stage-156-S"
reviewed_commit: "1bafd85e65df6c3228c863cdbf6fa72561c8a115"
amended_at: 2026-08-28
amended_for_commit: "f54152ec"
amendment_cycle: "review-fix cycle 2"
shipments: ["156-S", "157-S"]
features: ["148-F", "149-F"]
deliberation: "031-DL"
checkpoint: "checkpoint-20260828-064518.json"
supersedes_checkpoint: "checkpoint-20260828-041509.json"
---

# Stage session — 156-S BLOCKED-review repair (2026-08-28)

## Trigger

A current-HEAD local review of commit `1bafd85e` returned **BLOCKED**
(P0=0, P1=1, P2=6, P3=2) against the S0/S1 staging artifacts. This session applied
the full authorized S0/S1 staging correction — not only the P1 — as Stage-owned
planning/backlog work.

## Role boundary observed

Planning and backlog only. No source, template, schema, or config implementation;
no build, test, or lint run; no commit, push, or PR; no shipment claimed; Ship not
invoked. Shipment IDs `156-S`/`157-S`, feature IDs `148-F`/`149-F`, queued and
unclaimed status, and the `157-S depends_on 156-S` edge were all preserved.

## The P1 — a measurement-shape defect

The plan asserted *"`python-reviewer` has NO template anywhere in the tree —
confirmed by exhaustive filename search"* and scheduled authoring a new
Python-specific template.

That was false. `templates/agents/review/technology-reviewer.agent.md.tmpl`
exists, and installed `.github/skills/install-harness/SKILL.md` L1203 declares:

```text
technology-reviewer.agent.md -> .github/agents/subagents/{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md
```

`.autoharness/harness-manifest.yaml` L394 binds `PRIMARY_LANGUAGE_LOWER: "python"`,
so that mapping renders exactly `python-reviewer.agent.md` in this workspace.

**Root cause worth compounding**: a filename search cannot find a template whose
render target is *renamed by a mapping*, and a path-shaped grep
(`.github/agents/subagents/...`) cannot see a **bare-filename** citation. Both
blind spots produced false "missing"/"unread" conclusions in the same plan. The
archived stash `336F3AB7` text had listed all 12 review templates — including
`technology-reviewer` — in-workspace the entire time.

## Corrections applied

| Finding | Correction |
|---|---|
| **P1** false python-reviewer premise | U3 repurposed from template authoring to render-mapping pinning; U5 renders from the existing `technology-reviewer` template; `technology-reviewer` dropped from every exclusion list; plan, `148-F`, `148.003-T`, `148.005-T`, `148.006-T`, `148.008-T` all revised |
| **P2.1** dangling `031-DL` | Created deliberation item `031-DL` (DL counter was at `030-DL`, so the ID allocated exactly), linked to the decision doc + `148-F`/`149-F`/`028-DL`/`029-DL`, moved `queued -> active -> done` |
| **P2.2** missing plan dependency | `148.007-T depends_on 148.001-T` added and read back |
| **P2.3** stale DANGLING notes | U7/`148.007-T` now reconciles **three** notes — plan-review, review, **and shipment-reconcile** (the last becomes false once U1 installs the registry and `336F3AB7` is archived) |
| **P2.4** impossible raw-path assertion | U8 scenario 2 must **EXPAND** (preferred) or **EXEMPT** the literal `{{PRIMARY_LANGUAGE_LOWER}}` citation by a named rule; asserting raw resolution is forbidden |
| **P2.5** always-on personas wrongly excluded | `correctness-reviewer` + `maintainability-reviewer` added to U6 (3 -> 5 renders, XS -> S); Law-2 exclusion set now **EMPTY** |
| **P2.6** checkpoint handoff contradiction | New checkpoint `checkpoint-20260828-064518.json` with `context.shipment_id=156-S`, `s0_shipment_id=156-S`, `s1_shipment_id=157-S`; prior checkpoint left intact and recorded as superseded by filename |
| **P3.1** stale promotion metadata | Decision artifact `promoted_to: partial` + `promoted_units` for both units; `linked_artifacts` gained both plans |
| **P3.2** stash forward traceability | No official backlogit mutation exists for archived stash entries — reverse lineage documented in the plan and as a `148-F` comment; archived entry left unchanged |

## Evidence that settled P2.5

Installed `tune-harness/SKILL.md` L462-L469 treats a review layer that *lacks*
`correctness-reviewer.agent.md` or `maintainability-reviewer.agent.md` as real
**local-first review drift**, and `install-harness/SKILL.md` L1200-L1201 marks both
**"Always-on"**. Shipping S0 without them would have left the layer in a state the
workspace's own installed drift contract reports as drifted — i.e. S0 would not
have closed GAP 2. Law 2 is upheld by *measuring readers correctly*, not by
freezing an exclusion list.

## Counts after correction

* Personas installed: **11 -> 13**; installed artifacts: **12 -> 14**
* Templates authored: **1 -> 0**
* DANGLING notes reconciled: **2 -> 3**
* Task sizes: `148.003-T` S -> XS, `148.006-T` XS -> S; all others unchanged. Every
  task remains inside the 2-hour rule, so no split was required.

## Gate outcomes

* S0 plan re-hardened and re-reviewed -> **`decision: PASS`**, `dispatch_mode:
  single-agent-declared-degradation` (reviewer-subagent dispatch is still
  genuinely unavailable — `.github/agents/subagents/` does not exist until S0
  lands — and was re-probed, not assumed). The operative markers are terminal in
  the document; the 2026-08-27 review is retained as a clearly-labelled superseded
  appendix with its markers demoted to prose.
* Shipment reconciliation re-run: all members `queued`, zero duplicate ownership,
  S1 still blocked by S0.

## Operator approvals preserved exactly

* **Q1** — report persistence allowed, with named consumers
* **Q5** — authoritative test command `PYTHONPATH=src python -m unittest discover -s tests`
* **Q7** — S0 is **not** waived

## Next actor

**Ship, via Orchestrator: execute `156-S` FIRST.** `157-S` is not eligible until
`156-S` ships. Do **not** stage S2-S11; stash `D911A3B2` and `89E833E1` remain
ACTIVE and own that later scope.

## Review-fix cycle 2 — second local review of `f54152ec` (2026-08-28)

A second local review of `chore/stage-156-S` at `f54152ec` returned **P2×2 + P3×3**
against the staging artifacts. All in-scope findings applied; still Stage-owned S0
staging correction (no source/template/config implementation, no build, no commit,
no PR, no claim, Ship not invoked).

| Finding | Correction |
|---|---|
| **P2-1** stale memory artifact | `2026-08-27-stage-s0-s1-portfolio-staging.md` amended, **not erased**: top-of-file supersession banner + both false decisions (#2 `python-reviewer` has no template, #3 three personas deliberately NOT installed) struck through and annotated in place, pointing here and stating the corrected canonical mapping and 13-persona set. |
| **P2-2** unbound synthesized persona content | **Plan decision D8 added.** All five synthesized variables pinned with reviewed in-repo derivations *before* render. U3 (`148.003-T`) scope extended to be the **single binding-pin unit** for both templates; U5/U6 gained verbatim-binding contracts; **new `148.006-T -> 148.003-T` blocks edge**; U8 gained **scenario 5** (verbatim conformance + live-resolver cross-check + templates-unmodified) and the **D8-D fenced-code exemption**. |
| **P3-1** obsolete `U3 template` rollback step | Relabelled to *"U3 pinned-bindings record"* with an explicit note that U3 **writes no file**, so there is nothing to roll back, and Ship must not look for a `python-reviewer.agent.md.tmpl`. |
| **P3-2** future-tense stash archive | `336F3AB7` restated in **past tense** across plan (provenance, U7, D6, review finding table), `148-F`, and `148.007-T`: archived **2026-08-28T04:14:26Z during staging, before execution**; **Ship must not archive it again**. Reverse-lineage caveat preserved verbatim in all three places. |
| **P3-3** unamendable superseded checkpoint | Recorded as **accepted bounded residual risk RK-K** (plan Risks table + `148-F` DoD + below). Checkpoint left byte-intact; **not hand-edited**. |

### The five pinned synthesized values (D8)

| Variable | Pinned value | Derivation |
|---|---|---|
| `{{CONCURRENCY_PATTERNS}}` | `asyncio, task, queue, thread, process` | **Code-backed.** `verify_workspace.py` `_language_defaults("python")["concurrency_patterns"]` L2200, wired L2885. Copied verbatim from the shipped resolver — *not* synthesized. |
| `{{LANGUAGE_SAFETY_CHECKS}}` | D8-B bullet list | `_language_defaults("python")` `unsafe_policy` + `lint_policy`; `constitution.instructions.md` §I. |
| `{{LANGUAGE_IDIOM_CHECKS}}` | D8-B bullet list | `_language_defaults("python")` `naming_conventions` + `documentation_conventions`; constitution §I. |
| `{{LANGUAGE_ERROR_HANDLING_CHECKS}}` | D8-B bullet list | `_language_defaults("python")` `error_handling_policy` + `error_handling_conventions` + `error_pattern`; constitution §I. |
| `{{LANGUAGE_PERFORMANCE_CHECKS}}` | D8-B bullet list | **Weakest (RK-J)** — `_language_defaults` has **no** performance key. Constitution §X + §I. |

**Template discipline held**: values bind at *render time into installed artifacts*;
both `.tmpl` files keep their placeholders unmodified (D8-C), and U8 scenario 5
asserts that inverted polarity explicitly. Q5's authoritative test command is
unchanged.

### Why the S0 plan review was NOT re-run

The PASS is **retained**. No new unit; identical file set (still **0 new
templates**); INV-1…INV-5 untouched; Q1/Q5/Q7 unchanged. Ship's discretion is
**narrowed**, never widened — D8 replaces *"synthesize these five values"* with
*"bind these five exact values"*. The DoD **already** demanded zero unresolved
`{{...}}`; the plan simply gave no reviewed means of reaching it, and D8 closes
that contract gap. Full justification table recorded in the plan's
**Amendment record** section.

### Size/complexity after cycle 2

`148.003-T` **XS -> S** (complexity held `low`) — the only estimate that moved;
scope grew from one template's bindings to five pinned values across two
templates, but remains analysis-and-record with no file authored. All others
unchanged (`148.005-T` S/trivial, `148.006-T` S/trivial, `148.007-T` S/low,
`148.008-T` M/medium). **Every task still inside the 2-hour rule; no split
required.**

### Accepted bounded residual risks

* **RK-J** — the four `LANGUAGE_*_CHECKS` pins are **Stage-reviewed prose, not
  resolver-derived**; `_language_defaults` has no performance key at all. They are
  authoritative *for this shipment only*. Follow-up (out of S0 scope, changes the
  resolver): add `safety/idiom/error/performance_checks` keys to
  `_language_defaults`. U8 scenario 5 locks the shipped values against silent drift.
* **RK-K** — resolved checkpoint `checkpoint-20260828-041509.json` records the
  pre-correction S0 state and **has no official amendment path**
  (`create`/`resolve` only). **Deliberately left byte-intact — not hand-edited**,
  since hand-editing tool-owned state is forbidden. **Bounded** because: it is
  `resolved`, and the crash-resumption candidate scan partitions on `status:
  active`, so it can never be selected for restore; the superseding checkpoint
  `checkpoint-20260828-064518.json` names it in `supersedes_checkpoint`; and the
  correction is recorded here, in the plan (RK-K), and in `148-F`'s DoD. The only
  exposure is an operator reading that resolved checkpoint directly and out of
  context. **Not a gate on execution.**

## Tooling notes for future sessions

* `backlogit_update_item`'s `description` parameter is a **whole-body replace** —
  it wipes existing `<!-- BEGIN:section -->` blocks. Set `description` first, then
  re-supply **all** sections via `sections` in a follow-up call.
  **Cycle-2 refinement**: passing **only** `sections` (omitting `description`)
  updates the named blocks and **preserves** both the lead paragraph and any
  section not named — this is the safe body-editing seam.
* `size` (with `size_source` + `size_ruleset_version`) and `complexity` are
  separate, mutually exclusive, body-preserving mutation seams.
* Status transitions are gated: `queued -> done` is rejected; go via `active`.
* `.autoharness/backlog-registry.yaml` declares no `features.sizing` key, but the
  MCP surface accepts and persists `size`/`complexity` into `custom_fields`.
* Archived stash entries are unreachable from `stash get`/`stash edit`/`stash
  archive`; there is no official update path for them.
