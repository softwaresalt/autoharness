---
title: "Ship claim-integrity verification (queued-with-active-work mitigation)"
type: plan
date: 2026-07-30
source: docs/decisions/2026-07-30-ship-claim-integrity-preflight-spike.md
stash_ref: "6D6CACC1"
tags:
  - "ship-agent"
  - "claim-integrity"
  - "backlogit-shipment"
---

## Problem Frame

The autoharness Ship agent claims a shipment at build start
(`_ship.agent.md` Step 0.5.4 → `backlogit_claim_shipment`, template
`{{OP_CLAIM_SHIPMENT_MCP}}`), then moves each manifest task to `active`
(Step 2.1 → `backlogit_move_item`). There is **no post-claim assertion** that the
shipment *record's own* status actually reached `active` before tasks are moved.
A transient claim failure (e.g., the `backlogit MCP: Transport closed` drops
observed live this session) leaves the shipment `queued` while its tasks go
`active` — the "queued-with-active-work" inconsistency observed on `103-S`, which
required a manual archived-status surgical fix.

Per the spike (`2026-07-30-ship-claim-integrity-preflight-spike.md`):

* The **internal** backlogit transition guard is EXTERNAL (route upstream) — not
  implementable here.
* The **in-repo mitigation** lives entirely in autoharness agent-template
  workflow (Ship agent), is additive/fail-safe, and is **not** already covered by
  `shipment-reconcile` pre-mode (which checks manifest-item statuses, never the
  shipment record's own status).

This plan covers only the in-repo mitigation.

## Requirements Trace

| # | Requirement (from spike) | Implementation action |
|---|---|---|
| R1 | Reliably record the active claim; prevent tasks going active while shipment stays queued | Add a **post-claim verification** to Ship Step 0.5: re-read the shipment after claim; assert `status == active`; retry-once via CLI fallback; halt fail-closed `CLAIM_VERIFY_FAILED` before Step 2 (Unit A) |
| R2 | Detect the queued-with-active-work inconsistency instead of manual archived-status surgery | Add an **intake early-warning that runs before status validation and before the claim**: if the loaded shipment record is `queued`/`blocked` while any manifest task is already `active`/`done`, halt for reconcile (Unit B) |
| R3 | Do not touch backlogit internals | All edits are Ship-agent workflow instructions (template + dogfood); no backlogit source, schema, or CLI-distribution change |
| R4 | Preserve the external portion's traceability | Spike records the upstream referral; plan notes it; no code action here |

## Implementation Units

### Unit A — Post-claim shipment-status verification (Ship Step 0.5)

* **What changes**: Immediately after the claim call in Ship Step 0.5, add a
  verification step: re-read the shipment (`backlogit_get_shipment` /
  `{{OP_GET_SHIPMENT_MCP}}`, CLI fallback `backlogit shipment get`); assert the
  shipment `status` is `active` (template: `{{STATUS_ACTIVE}}`). Because the MCP
  surface is the unreliable path this guard exists to catch (`Transport closed`
  observed live), the verify re-read MUST prefer the CLI fallback
  (`backlogit shipment get`) when MCP is degraded, so the verification itself
  cannot be defeated by the same transient it is checking for. If the re-read
  status is `queued`: retry the claim exactly once (CLI fallback
  `backlogit shipment claim`) and re-read; if still not `active`, **halt
  fail-closed** with `CLAIM_VERIFY_FAILED: shipment {id} did not reach active
  after claim` and record a P-005 event. If the re-read status is `blocked`:
  **halt immediately** with `CLAIM_VERIFY_FAILED` — **no retry, no claim**:
  `blocked` is the repository's claim-prevention state and must transition
  `blocked → queued` (after its gate clears) before `queued → active`
  (`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md:32-44`), so
  re-issuing a claim on a `blocked` record would bypass that gate. Both halts fire
  **before** Step 2 moves any task to `active`. Broadcast the claim-verify result
  when intercom is available.
* **Files affected** (3 — 2 authored + 1 mechanical checksum refresh):
  `templates/agents/_ship.agent.md.tmpl` (post-claim verify),
  `.github/agents/_ship.agent.md` (post-claim verify — installed dogfood mirror),
  `.autoharness/harness-manifest.yaml` (regenerate the `sha256` `checksum` for the
  `.github/agents/_ship.agent.md` entry to match the edited mirror). Editing the
  dogfood mirror without refreshing this checksum fails
  `test_manifest_tracks_dogfood_ship_agent_checksum`
  (`tests/test_telemetry_ship_lifecycle.py:46-53`), which hashes the mirror bytes
  and asserts equality with the manifest entry.
* **Tests / verification**: (1) YAML frontmatter validity of both edited files;
  (2) no unresolved `{{VAR}}` introduced into the installed dogfood file;
  (3) markdownlint heading/structure unaffected; (4) manual read-through confirms
  the verify step is sequenced *after* claim and *before* the task loop, with the
  halt token spelled `CLAIM_VERIFY_FAILED`; (5) `.autoharness/harness-manifest.yaml`
  checksum for the mirror refreshed so
  `test_manifest_tracks_dogfood_ship_agent_checksum` passes.
* **Execution posture**: characterization-first (assert the current ordering,
  insert the gate, re-read to confirm ordering preserved).

### Unit B — Queued-with-active-work early-warning at Ship intake

* **What changes**: Add an intake consistency early-warning to Ship Step 0.5 that
  runs **immediately after the shipment record is loaded and BEFORE the existing
  status validation and BEFORE the Step 0.5.4 claim** — in BOTH the template and
  the dogfood. Placement rationale (two masking effects force the pre-claim,
  pre-validation position):
    * The Step 0.5.4 claim transitions `queued → active`, so a scan running after
      the claim (e.g., near Step 0.5.6) would observe `active` and **mask** a
      pre-existing queued-with-active/done-task inconsistency.
    * The existing status validation (template `_ship.agent.md.tmpl` Step 0.5.1,
      lines ~160-164) accepts only `queued` or `active` and halts/rejects other
      states, so a `blocked`-with-active-work record is rejected before it could
      reach a near-Step-0.5.6 warning. The `blocked` diagnostic is only reachable
      when the scan precedes that validation.
  The scan: if the loaded shipment record status is `queued` or `blocked` while any
  manifest task is already `active`/`done`, halt with
  `SHIPMENT_STATE_INCONSISTENT: shipment {id} is {status} but task {task_id} is
  {task_status}`. Remediation (detect-and-report only, no auto-repair): for a
  `queued` record, resolve and re-claim; for a `blocked` record, resolve the
  blocking gate and transition `blocked → queued` **before** any claim — **never**
  re-claim-to-`active` directly on a `blocked` record, which would bypass the
  documented blocking gate
  (`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md:32-44`); a
  genuinely stale record is archive-repaired instead. Enumerate the manifest task
  IDs from `backlogit shipment get {id}` and read each task status via
  `backlogit get {task_id}`; the whole check uses the CLI fallback path since MCP
  is the unreliable surface being guarded. Only manifest task IDs are read
  (task-only manifest, per the 097-S contract) — the covering feature is derived
  via `parent_id` and is not part of the consistency scan. In the template, insert
  the check right after Step 0.5.1's shipment load and **ahead of** the
  queued/active status validation; in the dogfood — whose Step 0.5 currently lacks
  the Step 0.5.6 intake reconcile step — add the same check inline right after the
  shipment is loaded and ahead of its status validation and claim.
* **Files affected** (3 — 2 authored + 1 mechanical checksum refresh):
  `templates/agents/_ship.agent.md.tmpl` (Step 0.5 intake, pre-validation),
  `.github/agents/_ship.agent.md` (Step 0.5 intake — installed dogfood mirror),
  `.autoharness/harness-manifest.yaml` (regenerate the `sha256` `checksum` for the
  `.github/agents/_ship.agent.md` entry). Because Unit B edits the mirror **after**
  Unit A, Unit B lands the **final** mirror bytes and therefore writes the
  authoritative end-state checksum; the gate is
  `test_manifest_tracks_dogfood_ship_agent_checksum`
  (`tests/test_telemetry_ship_lifecycle.py:46-53`).
* **Tests / verification**: (1) YAML frontmatter validity; (2) no unresolved
  `{{VAR}}` in the dogfood output; (3) markdownlint structure; (4) read-through
  confirms the early-warning is positioned **before** the status validation and the
  claim, and halts with `SHIPMENT_STATE_INCONSISTENT` on the queued/blocked-record
  + active/done-task condition; (5) `.autoharness/harness-manifest.yaml` checksum
  for the mirror refreshed to the end state so
  `test_manifest_tracks_dogfood_ship_agent_checksum` passes.
* **Execution posture**: test-first on the documented condition table (queued/
  blocked record × active/done task → halt).

## Dependency Graph

```
Unit A (post-claim verify)  ──blocks──▶  Unit B (intake early-warning)
```

Both units edit the same file pair (`_ship.agent.md.tmpl` + `.github/agents/_ship.agent.md`)
but in **different regions** of Step 0.5 (Unit B: right after the shipment load,
ahead of the status validation and the claim; Unit A: right after the claim).
Keeping **A → B** avoids same-file conflicts, lands the higher-value prevention (A)
first, and makes Unit B the **last** mirror edit — so Unit B writes the
authoritative end-state `.autoharness/harness-manifest.yaml` checksum. Each unit
still refreshes the checksum at its own completion so the manifest test is green
after either task lands. No re-sequencing required; no cycles.

## Decisions and Rationale

1. **Prevent + detect, not auto-repair.** `shipment-reconcile` explicitly reserves
   auto-mutation for a future version. Post-claim verification (prevent) plus
   intake early-warning (detect-and-report) closes the observed hole while
   honoring that design constraint. True self-repair (auto re-claim/repair) is
   recorded as a deferred follow-up, not scoped here.
2. **Edit both template and dogfood.** Templates are the product; the dogfood
   `.github/agents/` mirror is the same family's installed instance. Both must
   carry the guard so the dogfood harness dogfoods it.
3. **Fail-closed before the task loop.** The verification halts *before* Step 2
   moves any task to `active`, so the inconsistency can never be created in the
   first place under a detected claim failure.
4. **Split into two atomic units** rather than one edit, so the high-value
   prevention (A) is independently reviewable/shippable and B can be deferred if
   the operator prefers to ship A alone.
5. **Scope excludes** extending `shipment-reconcile` pre-mode with a
   shipment-record-status classification and any backlogit-internal change — both
   recorded as follow-ups (one deferred stash, one upstream referral).
6. **Consistency scan must precede validation and claim.** The Step 0.5.1 status
   validation accepts only `queued`/`active` (rejecting `blocked` earlier) and the
   Step 0.5.4 claim flips `queued → active`; both mask the inconsistency. Unit B is
   therefore positioned immediately after the shipment load and before both, in
   template and dogfood.
7. **Never re-claim a `blocked` shipment.** Retry-on-claim (Unit A) applies only to
   `queued`; `blocked` halts with no retry/claim. Remediation transitions
   `blocked → queued` after the gate clears, never a direct re-claim-to-`active`
   (`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md:32-44`).

## Risks and Caveats

| Risk | Mitigation |
|---|---|
| Template/dogfood drift (dogfood Step 0.5 lacks the intake reconcile step the template has) | Unit B adds the early-warning inline in the dogfood; note the drift for Ship, but do **not** expand scope to a full template↔dogfood reconciliation here |
| Over-hardening a low-frequency incident | Both units are lightweight instruction additions; no runtime code, no new dependency; recovery-cost (manual surgery) justifies the small guard |
| Introducing an unresolved `{{VAR}}` into the dogfood output | Verification step (2) in each unit explicitly checks for unresolved placeholders in the installed file |
| Halt tokens must be greppable/consistent | Fixed literals: `CLAIM_VERIFY_FAILED` (A), `SHIPMENT_STATE_INCONSISTENT` (B) |
| Editing the dogfood mirror stales its manifest checksum → `test_manifest_tracks_dogfood_ship_agent_checksum` fails | Each unit that edits `.github/agents/_ship.agent.md` refreshes the `sha256` `checksum` in `.autoharness/harness-manifest.yaml`; Unit B (last mirror edit) writes the end-state checksum (`tests/test_telemetry_ship_lifecycle.py:46-53`) |
| Retrying a claim on a `blocked` record bypasses the documented blocking gate | Retry applies only to `queued`; `blocked` halts with no retry/claim and requires `blocked → queued` before any claim |

## Plan Hardening Signals (REQUIRED)

* public API, schema, or contract change — **absent**. No schema/`header-def`
  change; no CLI contract change; agent-instruction edits only.
* security, auth, permission, or compliance-sensitive behavior — **absent**.
* migration, backfill, destructive data/config action, or irreversible step —
  **absent**. Additive fail-safe instruction text; the new behavior only *halts*
  earlier, it never mutates or archives anything.
* external integration, operator checkpoint, or external dependency — **absent**
  for the in-repo scope. (The backlogit-internal guard is external but explicitly
  out of scope; no external integration is built here.)
* high runtime, rollout, or rollback risk — **absent**. Edits are confined to a
  single template family (agent templates) + its installed mirror, plus a
  mechanical `.autoharness/harness-manifest.yaml` checksum refresh; trivially
  revertible by reverting the commit.

Blast radius: single template family (agents), additive, reversible. No schema,
no CLI distribution, no multi-family coupling.

**Requires plan hardening: no**

## Runtime Verification and Closure

* **Runtime surface changed?** No executable runtime surface (CLI/API/UI/jobs)
  changes. The Ship *agent workflow* changes — its runtime "surface" is the
  agent's own claim sequence.
* **Runtime verification** (for Ship at build time): after applying, a Ship dry
  read-through must show (a) the post-claim verify step sequenced after claim and
  before the task loop, halting on `CLAIM_VERIFY_FAILED` (retry only on `queued`;
  immediate halt with no retry/claim on `blocked`); (b) the intake early-warning
  positioned **before** the status validation and the claim, halting on
  `SHIPMENT_STATE_INCONSISTENT` for the queued/blocked-record + active/done-task
  condition. Frontmatter + placeholder + markdownlint gates pass on the edited
  files, and `test_manifest_tracks_dogfood_ship_agent_checksum` passes after the
  mirror checksum is refreshed in `.autoharness/harness-manifest.yaml`.
* **Operational closure artifact**: the two guard tokens
  (`CLAIM_VERIFY_FAILED`, `SHIPMENT_STATE_INCONSISTENT`) are greppable evidence
  in `.github/agents/_ship.agent.md` and `templates/agents/_ship.agent.md.tmpl`;
  their presence is the absorbed-into-workflow signal.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

**Capability declaration (P-012)**: reviewer-subagent dispatch is unavailable in
this Stage session; declared fallback = single-agent inline persona pass
(`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent
persona pass`). Model-specific/anchor routing unavailable →
`TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model
rubric pass`. Every selected persona's rubric was applied inline and findings
normalized to the P0-P3 scale; no persona was skipped.

**Plan hardening**: The plan declares `Requires plan hardening: no`. Blast radius
is a single template family (agent templates) + its installed dogfood mirror,
additive and reversible, with no schema / CLI-distribution / multi-family
coupling. P-006 hardening was correctly not required; the field is present, so no
fail-safe trigger.

### Persona coverage

| Persona | Mode | Triggered | Result |
|---|---|---|---|
| Constitution Reviewer | inline (same-model) | always-on | No P0/P1. Plan respects P-010 (Stage plans; Ship implements), P-016, P-008, Core Rule 2 (edits template + dogfood). |
| Python Reviewer | inline (same-model) | always-on | No Python surface changes (markdown agent-template edits). No findings. |
| Scope Boundary Auditor | inline (same-model) | always-on | Scope is tightly bounded; out-of-scope items (reconcile-skill extension, backlogit-internal change, auto-repair) explicitly excluded. 1×P3. |
| Learnings Researcher | inline (same-model) | always-on | Plan is consistent with `2026-05-07-backlogit-shipment-status-constraints` and `097-S`; contradicts no prior resolution. 1×P3. |
| Architecture Strategist | inline (same-model degradation) | always-on | Guard's home (Ship workflow) is cohesive; no new coupling. 1×P3 (long-term home may be the reconcile skill — already noted as follow-up). |
| Agent-Native Parity Reviewer | inline (same-model degradation) | triggered (agent-facing claim workflow + MCP tools) | Degraded-mode read paths now specified for both units; P-012 fallbacks declared. 1×P3 (resolved in-plan). |
| Security Lens Reviewer | n/a | not triggered (no auth/authz/secrets/API/external trust boundary) | No review needed. |

### Findings

* **P0/P1**: none.
* **P2**: none. (Two refinements initially raised — degraded-mode read path for
  the Unit A verify re-read, and manifest-task enumeration + degraded read path
  for Unit B — were resolved by tightening the plan before this gate, so they do
  not remain as gaps.)
* **P3-1 (Scope Boundary Auditor, advisory)**: Unit B is defense-in-depth for a
  once-observed condition (`103-S`). Already mitigated: the plan makes B depend on
  A and independently deferrable, so A can ship alone if the operator prefers.
* **P3-2 (Learnings Researcher, advisory)**: After implementation, capture the two
  guard tokens + the queued-with-active-work pattern as a compound learning so the
  learnings-researcher surfaces it in future work.
* **P3-3 (Architecture Strategist, advisory)**: The long-term home for
  shipment-record-status integrity may be `shipment-reconcile` pre-mode (a new
  shipment-record-status classification). The plan scopes this out and records it
  as a deferred follow-up to keep single-family blast radius.
* **P3-4 (Agent-Native Parity Reviewer, advisory)**: Prefer the CLI fallback for
  the verify re-read since MCP is the flaky surface — folded into Unit A before
  this gate.

### Runtime verification / closure readiness

Present and adequate for the change class: no executable runtime surface changes;
the plan defines a Ship dry read-through verification (correct sequencing +
halt-token presence) and a greppable operational-closure signal. No gap.

### Gate

**Decision: PASS** — only P3 advisories remain, all either resolved in-plan or
recorded as explicit deferred follow-ups. The plan is harvest-ready.

## Revision Log

### r1 — PR #269 Copilot review (2026-07-30)

8 substantive, valid Copilot review comments on the plan + task files were
applied (grouped into 3 themes). All are content fixes to the plan/task
artifacts; the `decision: PASS` marker and hardening conclusion are unchanged.

* **Theme A — consistency scan must precede validation and claim** (plan.md:88,
  plan.md:78). Unit B (the queued/blocked-with-active-work early-warning) was
  relocated to run **immediately after the shipment record is loaded and before
  the Step 0.5.1 status validation and the Step 0.5.4 claim**, in both template
  and dogfood. Rationale added: the claim flips `queued → active` (masking the
  inconsistency if scanned later) and the status validation rejects `blocked`
  before a near-Step-0.5.6 warning could fire (so the `blocked` diagnostic is only
  reachable pre-validation). Updated: Unit B "What changes", R2 row, Decision #6,
  verification item, Runtime Verification bullet.
* **Theme B — dogfood manifest checksum** (plan.md:68, plan.md:89, 102.001-T:18,
  102.002-T:20). Added `.autoharness/harness-manifest.yaml` to both units'
  affected-file lists (3 files = 2 authored + 1 mechanical checksum refresh) and
  to both task descriptions, with the explicit gate
  `test_manifest_tracks_dogfood_ship_agent_checksum`
  (`tests/test_telemetry_ship_lifecycle.py:46-53`). Noted that Unit B lands the
  **final** mirror edit and therefore writes the authoritative end-state checksum,
  while each unit refreshes the checksum at its own completion. Added a Risks row.
* **Theme C — never retry/claim a `blocked` shipment** (plan.md:61, 102.001-T:18,
  plan.md:80). Unit A retry-on-claim now applies **only to `queued`**; `blocked`
  halts immediately with no retry and no claim. Remediation wording corrected:
  for `blocked`, resolve the gate and transition `blocked → queued` before any
  claim — never re-claim-to-`active` on a blocked record. Cited
  `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md:32-44`.
  Updated: Unit A "What changes", Unit B remediation, Decision #7, Risks row, both
  task descriptions.

Dependency direction unchanged (`102.001-T` blocks `102.002-T`): the two units
edit different regions of Step 0.5, so no re-sequencing was required; keeping
`A → B` also makes Unit B the last mirror edit that writes the end-state checksum.


