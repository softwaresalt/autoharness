---
title: "Shipment-reconcile post-169-S hygiene: status-keyed Safe-Close skip, status placeholders, P-002.7 cross-references, cascade timeout calibration"
description: "Implementation plan for four post-169-S follow-ups on the shipment-reconcile skill and adjacent policy text (stash D16452D7, 814BB949, B5AB7D95, 4CB6A1E0). Chained after 171-S."
date: 2026-10-08
status: reviewed
deliberation: "docs/decisions/2026-10-08-171s-regrounding-and-reconcile-hygiene-deliberation.md (D-5, D-6)"
stash_entries: [D16452D7, 814BB949, B5AB7D95, 4CB6A1E0]
not_included: "F0F8916F (design decision, left in stash), 675EA40E (blocked on operator diagram publication), D6502107/E1E31E6A/A9BABC8B (folded into 171-S / 163-F R2)"
requires_plan_hardening: "yes"
plan_hardening_status: "hardened"
plan_review_verdict: "PASS"
plan_review_cycles: 1
tags: [plan, shipment-reconcile, safe-close, template-portability, p-002-7, cascade-close-timeout, dogfood-parity]
---

## Problem Frame

Four independent defects in the same skill family, each small, surfaced at or after
169-S (PR #506):

1. **D16452D7 — location-keyed skip (bug).** Safe-Close step 4 (`.github/skills/shipment-reconcile/SKILL.md`
   ~L887-L891, same lines in the `.tmpl`) classifies `pre-archived` and **skips** any
   manifest item whose file is in `archive/`. A task relocated by a done-move (status
   `done`, no `archived` stamp — `docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md`)
   is skipped and closes without an explicit single-artifact archive. Pre-Mode already
   classifies by declared status (Member-Class Status Contract, ~L90-L160), and its
   ~L124-L126 sentence records this skip as a deferred pre-existing gap.
2. **814BB949 — hardcoded vocabulary.** The template carries literal `status: done`
   in Step 0(b) (~L579) and the Cascade pre-archived preamble (~L1040), plus ~L643 and
   ~L1113, where the rest of the template uses `{{STATUS_DONE}}`. Non-backlogit renders
   get the wrong vocabulary. `tests/test_cascade_close_archived_ids_postcondition.py`
   (~L294, ~L1176, ~L1181; 147-F) pins the literal wording.
3. **B5AB7D95 — adjacent contracts not cross-referenced.** The skill's Member-Class
   Status Contract (Pre-Mode classification) and P-002.7 Post-Claim Member-Status
   Contract (`templates/policies/workflow-policies.md.tmpl` / `.github/policies/workflow-policies.md`
   L55) govern member status at different boundaries and neither names the other.
4. **4CB6A1E0 — timeout budget underestimates wall time (bug).** The Cascade Close
   Sub-Procedure (~L999-L1002) sizes `--timeout` as `B = ceil(1.5 * (F + P * N))` with
   `F = 133 s, P = 35 s (backlogit 1.11.0)`. 169-S (N = 9) ran 1153 s against B = 672 s.
   Nine evidence records under `docs/closure/evidence/` carry `invocation.started_at` /
   `finished_at` (observed 156 s - 1153 s), so the skill can point at real calibration
   data. The entry's "record the child duration" ask is already met by 192-F;
   recording the effective `--timeout` stays with `A5FA81C4`.

## Implementation Units

### B1 — Safe-Close step 4 classifies by declared status (D16452D7)

Both skill copies. Replace the location-keyed branches of step 4 with:

* locate the record in `queue/` or `archive/` (location is a label only, as in Pre-Mode R-1);
* declared `status: archived` → `pre-archived`, skip (no `{{STATUS_ARCHIVED}}`
  placeholder exists — verified 2026-10-08 — so `archived` stays literal, as it does
  in the Member-Class Status Contract table);
* any other declared status, in either location → move to done if not already done,
  then **explicit single-artifact archive** (`backlogit_archive_item` / `backlogit archive {id}`)
  with the merge SHA → `matched`;
* neither location → `missing`, `RECONCILE_FAIL` (unchanged).
* If the archive operation refuses an `archive/`-resident `done` record, HALT for
  operator review (never skip silently). Ship verifies the engine's behaviour on a
  scratch item in a temp backlog root before relying on it, and records the result in
  the task's closure note.

Update the Pre-Mode ~L124-L126 sentence (the skip is no longer location-keyed), the
verify-after-each step if it names location, and add a Deterministic Scenario Matrix
negative/positive row ("archive/-resident `done` task is explicitly archived, not
skipped"). Add a section-scoped guard test (new or extended
`tests/test_shipment_reconcile_*` module) asserting the status-keyed wording in both
copies. **Size M, complexity medium.**

### B2 — Status placeholders in the template (814BB949)

`templates/skills/shipment-reconcile/SKILL.md.tmpl` only: replace literal `status: done`
at the four sites with `status: {{STATUS_DONE}}` where the text describes a backlog
status value. Do NOT change `archived_status: done` legacy-field prose (~L946, ~L1956)
— that names a backlogit field value in a compatibility rule, not the workspace
vocabulary; record that judgement in the task. The rendered dogfood mirror stays
byte-identical (placeholder renders to `done` here). Update the 147-F test pins to
assert the placeholder in the template and the literal in the mirror. Must land after
B1 (same regions). **Size S, complexity low.**

### B3 — Reciprocal cross-references (B5AB7D95)

One sentence each, both copies of each file: the skill's Member-Class Status Contract
section names P-002.7 as the claim-to-admission member-status contract; P-002.7 names
the skill's Member-Class Status Contract as the pre-close classification contract.
Check the Ship agent's P-002.7 reference (`templates/agents/_ship.agent.md.tmpl` ~L295)
and any policy-parity test (`POLICY_PARITY_ALLOWLIST`, e.g. 049094FC context) for a
pinned excerpt that the new sentence would break; update the pin, do not edit the Ship
agent. **Size S, complexity low.**

### B4 — Cascade-close timeout calibration (4CB6A1E0)

Both skill copies, Cascade Close Sub-Procedure sizing paragraph: replace the reference
values with ones re-derived from the evidence records (duration =
`invocation.finished_at - invocation.started_at`, N = manifest size from `pre_close`),
choosing conservative values that cover every observed record including 169-S
(1153 s at N = 9). State the derivation source and date, tell the operator to
recompute from the workspace's own evidence records rather than reuse the numbers,
and replace "If B <= 1800, the default suffices" with guidance that holds under the
new values. No CLI default change (`autoharness shipment cascade-close` default
stays 1800 s; changing it is a CLI decision outside this plan). **Size S, complexity low.**

### B5 — Checksums and GREEN

Recompute `checksum:` for the `.autoharness/harness-manifest.yaml` entries whose `path:`
is `.github/skills/shipment-reconcile/SKILL.md` and `.github/policies/workflow-policies.md`
(locate by path). Run `PYTHONPATH=src python -m unittest discover -s tests`; confirm
templates/ ↔ .github/ parity. **Size XS, complexity low.**

## Dependency Graph

B1 → B2 (same regions); B3 and B4 independent; {B1, B2, B3, B4} → B5. Shipment blocks
on 171-S (same skill file and manifest; 171-S's Step 0(d) relabel shifts lines).

## Sequencing and shared files

Shared with 171-S: both skill copies, manifest. Shared with 208-S/210-S/212-S: the
workflow-policies copies (B3) and manifest. Rebase onto merged predecessors before B1
and again before B5; recompute checksums after the final rebase.

## Non-Goals

F0F8916F (invocation discriminator), 675EA40E (diagram), A5FA81C4 (record effective
timeout), 218DF163 (path literals), CLI default timeout, Pre-Mode contract changes.

## Plan Hardening Signals

Safe-close behaviour change (B1) on a destructive path; policy registry edit (B3);
dogfood parity. **Requires plan hardening: yes.**

## Plan Hardening (2026-10-08)

* **H1 — destructive-path change (B1).** The new branch adds an archive call for
  `archive/`-resident non-archived records; it never skips one that was skipped
  before *unless* it is now archived explicitly. Failure is HALT, never silent. The
  engine-behaviour probe on a scratch backlog root is mandatory before relying on
  `archive_item` for an `archive/`-resident record.
* **H2 — verify-after-each invariant.** Explicitly archiving a relocated `done` record
  changes its bytes; it is a manifest member, not an observation-set member, so the
  out-of-manifest fingerprint check is unaffected. Ship confirms this while editing.
* **H3 — no satisfiability regression.** B2 renders identically in this workspace;
  B3/B4 are prose. B4 only raises budgets.
* **H4 — protected invariants.** Member-Class Status Contract rows, Step 0(c)/(d) text
  owned by 171-S, R1-14 path-keyed checksum rule.

## Plan Review (cycle 1, 2026-10-08)

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
Personas: Architecture Strategist, Template Integrity, Test Strategy, Operational Safety.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| B-R1 | P1 | B1 must not assume `archive_item` accepts an `archive/`-resident record. | Fixed: HALT-on-refusal + mandatory scratch probe (B1, H1). |
| B-R2 | P2 | B2 could over-reach into `archived_status: done` legacy-field prose. | Fixed: explicitly excluded with rationale. |
| B-R3 | P2 | B3 may break a pinned policy-parity excerpt. | Fixed: check and update pins; Ship agent untouched. |
| B-R4 | P2 | B4 must not silently change CLI behaviour. | Fixed: CLI default out of scope. |
| B-R5 | P3 | Pre-Mode ~L124-L126 sentence becomes stale after B1. | Fixed: updated in B1. |

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

**Gate decision: PASS** — zero P0; P1 fixed in-plan; every task ≤ 2 h; no
`complexity: high`.
