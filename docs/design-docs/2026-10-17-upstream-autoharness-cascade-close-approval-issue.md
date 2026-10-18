# Upstream autoharness issue: cascade-close approval and closure text

Carry-over note for the autoharness repository. Source workspace: intercom-go.
Origin: stash 40BCCD69 (upstream issue request), 004-DL, 005-DL. Do not hand-edit
rendered files in intercom-go; fix the templates upstream, then re-render with
`autoharness install` or `autoharness tune`.

## Summary

The rendered Ship agent and shipment-reconcile skill never clearly separate two
different approvals:

* **Merge approval** (P-014, or the pre-authorization in a `DARK_MODE_ACTIVE` record).
* **Per-closure destructive approval** for `autoharness shipment cascade-close`
  (mutating mode), which archives manifest items and closes the shipment record.

Several text paths let a merge approval, a dark-mode activation, or routine
Orchestrator autonomy read as if they also authorize the cascade-close. The
policy (P-014, P-015, P-017, P-018) already forbids that. The agent text
under-states it. This is a wording defect, not a policy change.

## Defects, highest risk first

### 1. Merge approval can be read as cascade-close approval (stash 724FA2FB, medium)

`_ship.agent.md` step 6.1.b.3 should state that a P-014 merge approval,
including a "merge approved" message, cannot satisfy the per-closure
destructive cascade-close approval. This mirrors the existing closure-PR
non-transfer rule. The closure step should ask for the cascade approval
explicitly.

### 2. Dark-mode text under-states P-018 and per-closure approval (stash 8E1E2D80, high)

* Ship Steps 7b and 14: the P-018 Copilot review block applies once Copilot is
  engaged. The shadow-review timeout is advisory only when Copilot is not
  engaged. Current text (around line 582) can be read as keeping it advisory
  in dark mode.
* Ship Step 14 dark-mode approval list must include the P-018 PASS requirement.
* Orchestrator autonomy text must carve out per-closure destructive approval.
  It is never a routine coordination decision, and a `DARK_MODE_ACTIVE` record
  does not satisfy it.

### 3. Reconcile text vs. P-015 INV-6 and the post-mode HALT order (stash F2759510, high)

1. Align the cascade sub-procedure pre-archived paragraph and safe-close
   Step 0(c) parenthetical with the INV-6 engine-inertness predicate, not
   "full coverage".
2. Order a post-mode HALT as: restore, re-run mode post, commit only on
   PROCEED. This is an unsafe-ordering gap in a destructive close path, so it
   should lead the issue.
3. State the key mapping once: `selected_close_path` (engine JSON) equals
   `pre_close.close_path_selection` (evidence record).
4. Define or correct the INV-12 and D6 anchors where they are cited.
5. Remove the duplicated step-3 prose.

### 4. Related template nits (same request, lower priority)

* 9B7E94E9: Ship Step 6 item 1.a says manifest items must be present in queue
  with status done. Backlogit archives a task on move to done, so done members
  are always pre-archived. Align the Ship text with the shipment-reconcile
  pre-mode, which classifies them pre-archived (valid for expected_status done).
* 4B2EB2FB: the exit-code and `selected_close_path` routing gate is restated in
  at least ten places across SKILL.md and `_ship.agent.md`. Consolidate on the
  Step 0(c) routing table and have the other sections cite it.
* D5D103A1: shipment-reconcile SKILL.md line 549 renders a literal `{{id}}`
  placeholder in the backlogit archive CLI fallback.
* 0606E72F: operational-closure SKILL.md line 25 says `merge_commit` must equal
  `merge_commit_sha`. The canonical frontmatter key is `merge_commit_sha`.
* 92708A06: AGENTS.md lines 323-327 link to docs that do not exist
  (ARCHITECTURE.md, product-specs/, QUALITY_SCORE.md, references/).
* 8134B7B7 items 1-6: `_ship` frontmatter differs from the routing config,
  footer template name, missing referenced scripts, intercom references without
  the pack, `applyTo` double-star, and harness-manifest `alt_doc_review` route
  variables.

## Interim operator guidance in intercom-go

Until the re-render lands, treat dark-mode merge approval as insufficient for
any cascade-close and require an explicit per-closure approval before running
`autoharness shipment cascade-close`.

## Acceptance for the upstream fix

* The Ship template states that merge approval and dark-mode activation never
  satisfy the per-closure cascade-close approval.
* The Steps 7b and 14 text matches P-018, so a Copilot review block holds in
  dark mode once Copilot is engaged.
* The post-mode HALT order is restore, re-run post, commit only on PROCEED.
* After re-render, `autoharness verify-workspace` shows no drift for these files.

## References in intercom-go

* docs/decisions/2026-10-15-intercom-go-closure-reconcile-text-alignment-deliberation.md
* docs/decisions/2026-10-15-intercom-go-ship-dark-mode-copilot-approval-text-deliberation.md
* docs/decisions/2026-10-15-intercom-go-residual-batch-triage-deliberation.md (D-RB-7)
* docs/closure/043-S-053-F-post-merge-closure.md
