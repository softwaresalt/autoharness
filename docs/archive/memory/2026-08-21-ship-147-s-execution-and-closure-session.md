---
title: "Ship session memory - 147-S execution and closure"
date: 2026-08-21
agent: ship
route: "claude-sonnet-5 / anthropic / high (P-013.5)"
shipment: 147-S
feature: 139-F
tasks: [139.001-T, 139.002-T]
pr: 379
merge_commit: f57d0f0c50f2ea005a688e91ebf42f4decda51cd
---

# Ship session memory - shipment 147-S

## What shipped

Ship's Task Execution Loop now derives its **executable task set** from live
task records instead of treating the shipment manifest as that set
unconditionally, in both `.github/agents/_ship.agent.md` (installed mirror)
and `templates/agents/_ship.agent.md.tmpl` (template), plus a refreshed
`.autoharness/harness-manifest.yaml` checksum and a new discriminating
regression test module `tests/test_ship_pre_archived_manifest_members.py`.

This unblocks `144-S`/`145-S`, whose manifests correctly carry superseded,
archived children for P-015 closure validity but which the pre-fix contract
would have tried to reactivate.

## Pipeline trace

* Claimed 147-S (topology gate pre_claim x2, post_claim verify: all passed;
  `BRANCH_CREATED`/`BRANCH_OK` on
  `chore/147-s-prerequisite-ship-execution-contract-must-exclude-pre-archived-manifest-members-mandatory-post-merge-instruction-reload-before-144-s`).
  Noted: `backlogit shipment claim` in this backlogit version (1.10.0)
  atomically activates ALL manifest task items at claim time (not
  individually per Step 2's own `Claim` sub-step) -- both 139.001-T and
  139.002-T flipped to `active` together at claim, before the task loop's
  own explicit claim calls ran. Worth flagging for 144-S/145-S execution,
  where the manifest also includes pre-archived items -- confirmed
  (indirectly, via this session's own behavior) that the auto-activation
  only touches items still present in `queue/`; an archived item has no
  queue file for `move`/`claim` to touch.
* Local adversarial review (code-review subagent): READY on first commit.
* PR #379 created; CI green (`ci gate`, `detect code changes`,
  `pipeline-topology (ambient)`, `test`) on every push.
* Copilot hosted review, round 1: 2 P1 findings (Step 3-to-Step 4 wiring gap;
  Step 0.5 item 6 single-`expected_status` incompatible with mixed
  queued+active manifests). Fixed in `f065106b`.
* Copilot hosted review, round 2 (re-armed on push): 1 P1 finding
  (hard-coded `-T` suffix in the template instead of `{{SUFFIX_TASK}}`).
  Fixed in `08607503`.
* All 3 Copilot threads replied-to (citing the fixing commit) and resolved
  via GraphQL before merge, per P-018.
* `autoharness gate copilot-review 379` -> `SATISFIED: PASS` before merge.
* P-009 verified: repo allows merge-commit only
  (`allow_merge_commit: true`, squash/rebase both `false`).
* Merged via `gh pr merge --merge` at `f57d0f0c` (two parents confirmed:
  `e1a42a70` main tip + `08607503` branch tip).
* P-015 closure: `classify_shipment_close_path(['139-F','139.001-T',
  '139.002-T'], '.backlogit')` -> **CASCADE** (139-F is a root, fully
  covered by both manifest-member children, manifest contains nothing
  beyond the qualifying root + children). Cascade `backlogit shipment ship
  147-S --sha f57d0f0c...` executed and independently verified:
  `returned_ids: []`; `archived_ids` exactly
  `[139.001-T, 139.002-T, 139-F, 147-S]`; no `parent_id` cleared;
  `backlogit doctor` reports zero findings touching this scope.

## P-021 (no new capture)

Full local `python -m unittest discover -s tests` run showed the same 5
pre-existing, full-suite-only, order-dependent failures already captured
under stash entry `E8158860` (confirmed unrelated: no `src/` change in this
PR; each test passes in isolation; CI's Linux `test` job was green). Reused
`E8158860`, no new stash entry created.

## Follow-ups for the next Ship session (144-S)

* **MANDATORY**: reload the freshly merged `main` `.github/agents/_ship.agent.md`
  before claiming `144-S` -- this is the whole point of 147-S. Confirmed
  done for this session's own post-merge closure re-read; a *future*
  session claiming 144-S must independently re-read it fresh, not rely on
  this memory file as a substitute.
* 144-S's manifest carries pre-archived children (`136.001-T`) alongside
  queued/active ones -- this is the exact shape 147-S's derivation exists to
  handle. Watch for the Step 0.5 item 6 scope note: do not run the
  `shipment-reconcile mode: pre` intake check if 144-S resumes mid-loop with
  diverged per-task status; it only applies to true session-start intake
  with a uniform manifest status.
