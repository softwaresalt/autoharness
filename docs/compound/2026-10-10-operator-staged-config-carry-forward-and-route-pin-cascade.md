---
title: "Operator-staged config edits and the route-pin cascade: no carry-forward for non-backlog paths, and a model_routing change must ship with its pins and mirrors"
problem_type: process-gap
category: workflow
root_cause: "The pre-claim topology gate treats any staged or modified path outside .backlogit/ as WORKTREE_DIRTY, and P-011 forbids stashing dirt to pass it, so an operator edit to a non-backlog file such as .autoharness/config.yaml has no supported carry-forward into a shipment. A model_routing change also cascades into route-pin tests, harness-manifest checksums, and the installed Stage and Ship mirror renders; a config commit made alone fails 16 test outcomes across two modules."
tags: [p-011, p-016, worktree-cleanliness, carry-forward, model-routing, route-pin, harness-manifest, mirror-render, escalation, pre-push]
shipment: 208-S
date: 2026-10-10
source: docs/compound/2026-10-10-operator-staged-config-carry-forward-and-route-pin-cascade.md
doc_type: learning
---

## Problem

On 2026-10-09 the operator edited `.autoharness/config.yaml` in the main worktree
and staged it. The edit reassigned the model routes: the Ship route, the nested Ship
escalation, the Stage route, and the tier and orchestrator routes. The operator then
asked for the edit to be carried into shipment 208-S.

Three things became clear while doing that:

* **No supported carry-forward exists for non-backlog paths.** The pre-claim gate
  reports `WORKTREE_DIRTY` for any staged or modified path. Its only carry-forward
  prefix is the resolved backlog directory (`.backlogit/` in this checkout).   P-011 forbids stashing dirt to pass the gate, so the operator's edit could not be claimed or committed through the normal path.
* **A routing change cascades.** The same edit broke 16 failing outcomes across two test
  modules: 15 failures and one error. In `tests/test_dogfood_ship_route_pin.py`, 5 failures
  and 1 error across 12 test methods. In `tests/test_role_bound_pipeline_render.py`, 10
  failures, which are subtest outcomes spread over 6 of 16 test methods. The pins
  hard-coded the superseded values, the harness-manifest checksums and `config_hash`
  covered the old bytes, and the installed Stage and Ship mirror frontmatter no longer
  matched a fresh render of the template.
* **Dropping the flat escalation block has a consequence.** With no flat block and no
  nested `stage.escalation`, Stage's escalation route resolves through tier3 to
  `claude-sonnet-5.5`, `anthropic`, `xhigh`. That is Stage's own route, so every
  Stage auto-escalation is an `ESCALATION_DEGRADED` same-route no-op.

## Solution

### 1. The one-time exception (operator-authorized only)

The procedure used, with each step verified:

1. Park the operator's edit by its stash **commit SHA**, not `stash@{0}`. Stash
   indices shift as other stashes are created. Record the blob hash
   (`git rev-parse <stash-sha>:<path>`) and write a backup patch outside the tree.
2. Create the shipment branch from a clean `main`, then run
   `git checkout <stash-sha> -- <path>` to restore the file byte-exact.
3. Verify the blob, not the working copy. Under `core.autocrlf=true` a Windows
   working file is CRLF while the blob is LF, so compare with the filtered
   `git hash-object <path>`, not `--no-filters`.
4. Commit the file alone as the first, isolated commit, and confirm the committed
   path set with `git show --name-only`. Only then run the pre-claim gate again on the
   branch. It must report `WORKTREE_CLEAN`.
5. Never pop, apply, or drop any other stash.

Risks of this procedure:

* A stash commit reached only by SHA stays recoverable through the reflog. A dropped
  stash is recoverable only while its object survives. Do not drop it until the merge
  is verified.
* The isolated commit lands on the shipment branch before the operator's change has
  any review, and it sets routing for every role. It needs explicit operator
  authorization, and it should name the stash SHA and blob in its message.
* The restore writes a CRLF working file on a `core.autocrlf` checkout. That is normal
  on this platform, but any check that hashes raw working bytes will disagree with the
  blob. Verify with the filtered hash.

### 2. A config edit must ship with its pins and mirrors

Treat a `model_routing` change as a bundle. In one commit:

* update every route pin that asserts the old values, with exact values, never a
  weaker assertion;
* re-render the installed Stage and Ship mirrors route frontmatter, and update any
  route-derived prose so it matches the new routes;
* refresh the harness-manifest checksums of the changed artifacts and the top-level
  `config_hash`, computed from the LF-normalized bytes that the tests read.

The check that catches this is the two route modules. Run them before the full
suite, because they fail fast and name the stale pin.

### 3. Batch pushes

The full canonical suite took 11 to 15 minutes per run (698, 661, and 904 seconds for
the three full runs on this shipment). The pre-push hook runs the same suite on every
`git push`, so each push costs a full run. Batch related commits into one push, and
run the targeted modules while iterating.

## Prevention

* Before the claim, list every staged or modified path outside the carry-forward
  prefixes. If the list is not empty, stop and ask the operator where the change
  should go. Do not stash it.
* Record the escalation tuple of every role after a routing change. A same-route
  escalation is a degraded state, not a silent pass. For 208-S it is tracked as
  stash `3C19FA0F`.
* Keep route-provenance comments in the config. The operator's edit removed the
  rulings that explained the earlier pins, so the pins now carry the only record.

## Known stale route surfaces (disclosed, not fixed in this shipment)

Shipment 208-S refreshed the Stage and Ship mirrors only. These surfaces still carry the
old routes, and no test pins them: the installed Orchestrator frontmatter (capture
`1F13DF5E`), the installed escalation-protocol instruction, which still says there is no
nested override and gives the old tier3 values (capture `5493E44F`), and the installed
Tier-1 and Tier-2 review personas under `.github/agents/subagents/`. The bundle rule
above applies to them as well. Until they are re-rendered, the config is authoritative
and these surfaces are stale.

## Structural follow-ups (captured, not implemented here)

* Stash `80CD43B8`: extend the P-011 carry-forward to operator-designated non-backlog
  paths, with an explicit, auditable opt-in. Related, but separate: queued shipment
  `203-F` (B1 to B6) covers stash-referenced paths only.
* Shipment `210-S` (queued) covers stash-referenced companion documents through P-011
  and `worktree_cleanliness`. It does not cover operator-designated non-backlog paths.
  The orchestrator's note also cites stash `FB6F9FE0` as the source of that work. It
  was not present in the active stash list when checked on 2026-10-10.

## References

* `templates/policies/workflow-policies.md.tmpl`, P-011 and P-016.
* `src/autoharness/gates/topology.py` (the `worktree_cleanliness` check; its
  `carry_forward_prefixes` is `.backlogit/`).
* `tests/test_dogfood_ship_route_pin.py` and `tests/test_role_bound_pipeline_render.py`
  (the 16 failing outcomes above).
* Commits on PR #511: `7b34ba47` (isolated carry-forward) and `d89125d0` (pins,
  mirrors, and manifest).
