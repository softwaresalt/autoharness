---
title: "Ship 200-S / 194-F post-merge closure (compacted)"
description: "Compacted Tier-1 release-unit memory for 200-S / 194-F (context_tier on model_routing routes and agent frontmatter, fresh-install Ship seed, dogfood Ship pin). Covers the PR #490 merge and the CASCADE close through autoharness shipment cascade-close (P-020)."
doc_type: memory
source: docs/memory/compacted/2026-10-04-ship-200-s-194-f-full-lifecycle-compacted.md
date: 2026-10-04
agent: ship
session_id: ship-2026-10-04-200s-closure
compacted_from:
  - docs/archive/memory/2026-10-04-ship-200-s-194-f-closure-session.md
---

# Ship 200-S / 194-F Post-Merge Closure (Compacted)

The verbose original is listed in `compacted_from`. Closure record:
`docs/closure/200-S-194-F-post-merge-closure.md`. Close evidence:
`docs/closure/evidence/200-S-194-F-close-evidence.json` and
`.backlogit/reconcile/200-S-cascade-close-20261004-235951.md`.

## Delivery

* PR #490 merged as `b264efd5` (reviewed HEAD `d7721b00`). It delivered
  `context_tier` on every `model_routing` route and on agent frontmatter,
  role-scoped `SHIP_*` / `STAGE_*` and `*_CONTEXT_TIER` variables, the
  fresh-install Ship seed, the dogfood Ship pin, config-authoritative verify
  precedence with `ROUTE_VARIABLE_STALE`, and the policy and docs updates
  (`194.001-T` .. `194.014-T`).

## Close

* The lifecycle gate exited 0. Runtime proofs 1 to 3 were met. Pre-mode
  returned `PROCEED` for 15 items. `--classify-only` exited 0 (`CASCADE`,
  `VERIFIED` `1.11.0` / cli).
* Sizing: N = 16 and B = 1040 s, so the default timeout was used.
* The mutating `cascade-close` exited 0 after 737 s (child about 710 s). It
  archived 16 IDs, `returned_ids` was `[]`, and postconditions passed. The
  whole-tree guard found only the 18 closure-scope paths changed.
* INV-12: `036-DL` was `retained_shared_reference` (referrer `BAF15C62`),
  giving `DISPOSITION_COMPLETE`. Post-mode returned `PROCEED`.
* Source cleanup: `6EC29DD6` was already archived. The `036-DL` outcome was
  copied from the report.
* `backlogit sync` reported `Indexed 1711 artifacts` after the follow-up
  stash entries (`CLOSURE_INDEX_SYNC_OK`). The full suite passed
  (`Ran 3143 tests`, `OK (skipped=54)`).

## Learnings

* The duration model predicted 693 s for 16 artifacts; the child took about
  710 s (about 176 s to the shipment status change, about 150 s more to the
  first task rewrite, then about 25 s per task).
* The 199-S scratch scripts can be reused by changing only the IDs.
* Stage queue-to-archive moves with `git add -A` on directories. A pathspec
  for a path that no longer exists fails the whole `git add`.

## Follow-Ups

New: `09DFC9F9`, `EFC48191`, `D6FE4677`, `8447F9EB`, `9039DA3F`, and
`7A3E1AD7`. Existing: `50434138`, `97B28746`, `BCD87392`, `24BA1B8F`, and
`BAF15C62`.
