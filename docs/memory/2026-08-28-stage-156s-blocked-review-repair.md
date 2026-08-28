---
title: "Stage session — 156-S BLOCKED-review repair"
date: 2026-08-28
agent: stage
session_id: "stage-2026-08-28-156S-blocked-review-repair"
branch: "chore/stage-156-S"
reviewed_commit: "1bafd85e65df6c3228c863cdbf6fa72561c8a115"
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

## Tooling notes for future sessions

* `backlogit_update_item`'s `description` parameter is a **whole-body replace** —
  it wipes existing `<!-- BEGIN:section -->` blocks. Set `description` first, then
  re-supply **all** sections via `sections` in a follow-up call.
* `size` (with `size_source` + `size_ruleset_version`) and `complexity` are
  separate, mutually exclusive, body-preserving mutation seams.
* Status transitions are gated: `queued -> done` is rejected; go via `active`.
* `.autoharness/backlog-registry.yaml` declares no `features.sizing` key, but the
  MCP surface accepts and persists `size`/`complexity` into `custom_fields`.
* Archived stash entries are unreachable from `stash get`/`stash edit`/`stash
  archive`; there is no official update path for them.
