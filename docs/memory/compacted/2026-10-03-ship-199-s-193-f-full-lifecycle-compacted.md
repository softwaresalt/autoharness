---
title: "Ship 199-S / 193-F post-merge closure (compacted)"
description: "Compacted Tier-1 release-unit memory for 199-S / 193-F (agent and skill frontmatter conformity contract). Covers the PR #487 merge and the CASCADE close through autoharness shipment cascade-close (P-020)."
doc_type: memory
source: docs/memory/compacted/2026-10-03-ship-199-s-193-f-full-lifecycle-compacted.md
date: 2026-10-03
agent: ship
session_id: ship-2026-10-03-199s-closure
compacted_from:
  - docs/archive/memory/2026-10-03-ship-199-s-193-f-closure-session.md
---

# Ship 199-S / 193-F Post-Merge Closure (Compacted)

The verbose original is listed in `compacted_from`. Closure record:
`docs/closure/199-S-193-F-post-merge-closure.md`. Close evidence:
`docs/closure/evidence/199-S-193-F-close-evidence.json` and
`.backlogit/reconcile/199-S-cascade-close-20261004-061145.md`.

## Delivery

* PR #487 merged as `30095385` (reviewed HEAD `1c5c379e`). It delivered the
  `frontmatter_contract` module, the `verify_workspace`
  `frontmatter_conformity` check and migration proposals, agent and skill
  remediation, tune-harness Step 1.5c, and the P-013.1 / P-013.4
  plugin-global clarification (`193.001-T` .. `193.008-T`,
  `193.004.001-ST`, `193.004.002-ST`).

## Close

* The lifecycle gate exited 0. Pre-mode returned `PROCEED` for 11 items.
  `--classify-only` exited 0 (`CASCADE`, `VERIFIED` `1.11.0` / cli).
* Sizing: N = 12 and B = 830 s, so the default timeout was used.
* The mutating `cascade-close` exited 0 after 563 s (child about 540 s). It
  archived 12 IDs, `returned_ids` was `[]`, and postconditions passed. The
  whole-tree guard found only the 14 closure-scope paths changed.
* INV-12: `037-DL` was `retained_shared_reference`, giving
  `DISPOSITION_COMPLETE`. Post-mode returned `PROCEED`.
* Source cleanup: `EF96B695` was already archived. The `037-DL` outcome was
  copied from the report.
* `backlogit sync` reported `Indexed 1698 artifacts` after the cascade and
  `Indexed 1704 artifacts` after the follow-up stash entries
  (`CLOSURE_INDEX_SYNC_OK`).

## Learnings

* The duration model (133 s + 35 s per artifact) predicted 553 s for 12
  artifacts, and the actual time was 540 s. The engine spent about 122 s
  before its first status change, then about 25 s per artifact.
* The 198-S scratch scripts can be reused by changing only the IDs. Drop
  `--replace-pre-close` when no earlier `pre_close` record exists.
* Capture follow-up stash entries only after the disposition step.

## Follow-Ups

New: `4C6CBA75`, `A6CF06E6`, `2568A99A`, `24BA1B8F`, `BE6C7DF8`, and
`3E60149D`. Existing: `9F6AC6B3` and `09EA8F24`.
