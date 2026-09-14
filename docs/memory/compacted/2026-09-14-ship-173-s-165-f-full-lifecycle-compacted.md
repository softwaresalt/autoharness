---
title: Compacted memory — 173-S SHIP-15 DAG-authoritative predecessor derivation, full lifecycle through merge (PR #450)
doc_type: memory
memory_class: compacted
created: 2026-09-14
shipment: [173-S]
feature: [165-F]
tasks: [165.001-T, 165.002-T, 165.003-T, 165.004-T, 165.005-T, 165.006-T, 165.008-T, 165.009-T, 165.011-T, 165.012-T]
merge_commit: 9cc98c41de1cad9175e29b8190dbe4b81c85a1d5
pr: [448, 450]
consolidates:
  - docs/archive/memory/2026-09-12/stage-165f-173s-review-fix-cycle-1.md
  - docs/archive/memory/2026-09-12/stage-165f-173s-review-fix-cycle-2.md
  - docs/archive/memory/2026-09-13/stage-165-f-173-s-cycle-3-final-correction.md
  - docs/archive/memory/2026-09-13/stage-165f-173s-pr448-review-fix-cycle-1.md
  - docs/archive/memory/2026-09-13/stage-165f-173s-pr448-review-fix-cycle-2.md
  - docs/archive/memory/2026-09-13/circuit-break-pr448-thread-reply.md
  - docs/archive/memory/2026-09-14/ship-173-s-merge-and-post-merge-closure-blocked.md
---

# Session Memory — 2026-09-14 — 173-S SHIP-15 full lifecycle (Stage planning through Ship merge)

## Scope

Replace the pipeline-topology `pre_claim` gate's numeric-adjacency
predecessor heuristic with a DAG-authoritative, four-state predecessor
derivation engine driven by explicit `blocks` edges in backlog data, add a
read-only `audit_sequencing` phase, align `dag-readiness` advisory output
with `pre_claim`'s authoritative derivation, surface predecessor
provenance/audit rendering in the CLI, and add an at-most-once
bootstrap-grant consumption surface for documented pre-claim gate bypass
scenarios. Feature `165-F`, 10 executable tasks (`165.007-T`/`165.010-T`
descoped/merged during Stage planning, not part of the executable set).

## Stage planning: three review-fix cycles (2026-09-12/13)

- **Cycle 1** (four-state root contract): narrowed the predecessor-source
  enum to four states (`explicit`/`declared_root`/`genesis`/`unsequenced`),
  retiring numeric adjacency from the claim path entirely. Descoped
  `165.007-T` (closure-evidence producer/consumer naming-contract defect —
  a different contract surface, forward-referenced to stash `FD0CCB42`).
- **Cycle 2** (narrow genesis, two-use bootstrap, atomic parity): tightened
  `genesis` to apply only when the candidate is the sole shipment record
  (live + archived); made bootstrap-grant consumption at-most-once per
  label; merged `165.010-T` into `165.008-T` for atomicity (template source
  + installed dogfood mirror in one commit, closing a wrong-contract-window
  risk).
- **Cycle 3** (authorized final correction set): four contract
  corrections finalized before PR.
- PR #448 (an earlier PR number for this same shipment, later
  re-numbered/re-opened as **PR #450**) went through its own three
  review-fix cycles (executable bootstrap split, audit-purity narrowing;
  five contract corrections; containment/status-enum/checkpoint-handoff
  corrections) plus a circuit-breaker event: three consecutive upstream
  GitHub 5xx failures replying to/resolving thread `PRRT_kwDORzpWpM6h3ttV`,
  resumed under operator direction, resolved via REST fallback after a
  120s cooldown — no operator action left outstanding.

## Ship execution + PR #450: 6 rounds of hosted Copilot review, 9 genuine bugs

11-persona local review: zero unresolved P0/P1. Initial CI surfaced two
cross-platform bugs in bootstrap-grant code never exercised on POSIX during
Windows-only development (fixed `1ae5c894`/`b17cc530`). Four further hosted
Copilot rounds found 7 more genuine bugs in the bootstrap-grant/
pipeline-topology surface: two unguarded symlink-following reads
(`9a87d745`), a grant-scoping gap bypassing undeclared blocking predecessors
(`1bfa41ea`), a missing directory-fsync + pathname-based scan regression
(`d9958ee4`), a missing mode/phase authority-boundary check + symlink-
following audit-log append (`408ae4a2`), an intermediate-directory symlink
check gap in grant reads (`1dac0613`), and a short-`os.write()` durability
bug affecting every claim/append/consume path, fixed via a shared
`_write_all()` helper (`164e06a6`). All 9 fixed with dedicated regression
tests, validated on both Windows and native POSIX (WSL). Two process/hygiene
findings (stale PR-body HEAD references) fixed by rewriting affected prose
to defer to live external state instead of a fixed HEAD — this pattern
recurred twice (rounds 5 and 6) before being fully addressed.

Out-of-scope P-021 captures during this build: `EB9CB9E8` (new, flaky
telemetry-sink test), `24A85BF8` (reused, same flaky-test root cause as a
159-S capture). No out-of-scope finding fixed in-cycle.

## Merge (2026-09-14, separate session from the build)

Revalidated all prior-session readiness claims fresh rather than trusting
them (headRefOid match, P-018 `SATISFIED`, 4/4 CI green, P-009 repo settings
merge-commit-only, P-016 worktree clean, pipeline-topology lifecycle pass).
Checkpoint `checkpoint-20260913-225705.json` validated and confirmed its
resume_hint work already complete by direct evidence before treating the
resume as successful. Merged via `gh pr merge 450 --merge` on narrowly
scoped operator approval — first attempt succeeded, no admin fallback.
Merge commit `9cc98c41...`, two parents, confirmed ancestor of
`origin/main`.

## Post-merge closure: shipment-record safe-close BLOCKED

All 11 manifest items were already correctly `status: archived` (not just
file-relocated) from prior sessions — no archival action needed.
`classify_shipment_close_path` confirmed `SAFE_CLOSE` (165-F has
descendants `165.007-T`/`165.010-T` outside the manifest; P-015 cascade
exception does not apply). Closing the shipment record itself (Step 8)
hit two blockers, both captured per P-021 with full evidence and NO ad hoc
workaround attempted:

- **`FBD2F6BE`**: `165.007-T`/`165.010-T` are pre-existing, permanently
  descoped/archived siblings (parent_id retained, predates this shipment's
  claim) enumerated into the safe-close protected set; already outside
  `queue/` at the baseline gate, which is a hard no-exemption halt per the
  `2026-08-02` compound doc's "sixth occurrence" guidance — exactly the
  pattern predicted in advance for the analogous `168-S`/`160.019-T` case
  (`3CA122AC`).
- **`2B42392E`**: the installed backlogit CLI (1.10.1) rejects
  `backlogit move <shipment_id> --status shipped` (must use `ShipShipment`)
  even though `--status active`/`--status queued` succeed — breaking
  `shipment-reconcile`'s documented non-cascading Step 8 for every
  `SAFE_CLOSE`-classified shipment workspace-wide, not just `173-S`.

`173-S` remains `status: active` in backlogit (P-001: still active until
Stage resolves both findings and safe-close can complete). PR merge, CLI
post-merge re-verification, and all manifest artifact archival are
otherwise fully complete.

## Follow-ups (Stage deliberation required)

`FBD2F6BE`, `2B42392E` (new, this closure), `72676271` (pre-existing,
installed Ship agent never invokes `shipment-reconcile mode: post`),
`FD0CCB42` (165.007-T's original closure-evidence naming-contract defect,
forward-referenced from Stage planning).
