# Stage session — dark-factory staging (2026-08-01)

Route: claude-opus-4.8 / anthropic / high (P-013.5). Visibility: local session
(intercom degraded). Worktree: main only, no new branch/worktree.

## Scope (immutable): 2970FA4E, 34D50F2D, 010-DL, 077-F, 080-F, 081-F, 082-F, 084-F, 104-F

## Grouping rationale (real dependency/cohesion analysis)
- **Already SHIPPED (housekeeping):** 104-F (via 108-S archived, 9/9 done),
  084-F (via 107-S archived, 8/8 done; gate 079-F/092-S archived). 010-DL was the
  design deliberation that produced 104-F. → rolled 104-F/084-F to done; linked
  010-DL --informs--> 104-F and archived it. NOT new shippable work.
- **Blocked-on-operator (cannot advance without operator decisions):** 077-F
  (github/pwsh/env/pinning tradeoffs), 080-F (multi-repo architecture decision),
  081-F (WSL inspect/provision authorization), 082-F (external pack read access).
  Surfaced; not planned (would fabricate operator decisions = stop condition).
- **Deferred, needs operator prioritization:** 34D50F2D framework spec overlaps
  heavily with shipped routing/telemetry/checkpoint work → gap-analysis
  deliberation 011-DL created; net-new capabilities isolated; kept in stash.
- **Genuinely stageable now (the one coherent shipment):** 2970FA4E part (1)
  shipment-reconcile record-status classification (+ part 3 learning).

## Outcome
- **Shipment 109-S (QUEUED, the single eligible shipment)** — "Ship
  claim-integrity: shipment-record-status classification (105-F)".
  Items: 105-F, 105.002-T (T1 template), 105.001-T (T2 docs/learning).
  Intra-feature order: T2 depends_on T1. No successor shipments (rest of scope is
  shipped/blocked-on-operator/operator-prioritization) → "exactly one eligible" holds.
- **Deliberation 011-DL** — 34D50F2D gap analysis (surface for operator).
- Stash: 2970FA4E archived (consumed); 936C68F3 created (deferred part 2 +
  EXTERNAL backlogit guard referral); 34D50F2D edited (deferred, links 011-DL).

## Planning artifacts (uncommitted; operator said do NOT commit)
- docs/plans/2026-08-01-shipment-reconcile-record-status-classification-plan.md
  (requires_plan_hardening: no — single template family, additive, fail-safe)
- docs/reviews/2026-08-01-shipment-reconcile-record-status-classification-review.md
  (verdict PASS, P0=0, P1=0, 2×P2 folded into T1)

## Blockers surfaced (require operator action, not shippable now)
- 077-F, 080-F, 081-F, 082-F: blocked-on-operator (specific decisions per feature).
- 34D50F2D (011-DL): pick lead net-new capability; reconcile spec model picks
  (Ship=Terra/escalation=Sonnet 5) vs shipped P-013.5 (Ship=claude-sonnet-5);
  confirm Verification/Compaction + crash-resumption in-repo vs external.
- 936C68F3: self-repair auto-mutation gated on lifting no-auto-repair stance;
  backlogit-internal active->queued guard is EXTERNAL (upstream to backlogit).

## Next steps (Ship)
Ship claims 109-S, executes T1 then T2, runs shipment-reconcile pre/safe-close/post.
