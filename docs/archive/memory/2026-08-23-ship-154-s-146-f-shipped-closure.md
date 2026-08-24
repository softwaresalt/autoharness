---
title: "Ship session 2026-08-23/24 - 154-S / 146-F merge and post-merge closure"
date: 2026-08-23
source: "docs/memory/2026-08-23-ship-154-s-146-f-shipped-closure.md"
doc_type: "reference"
agent: ship
route: "claude-sonnet-5 / anthropic / high"
mode: dark-factory
---

# Ship Session Memory - 154-S / 146-F merge and closure

## Scope

Resumed Ship ownership for active shipment `154-S` (manifest: `146-F`,
`146.001-T`, `146.002-T`, `146.003-T`) with PR #404 already OPEN, gates
green, and operator authorization limited to: normal merge-commit merge of
PR #404 only (admin fallback explicitly unauthorized); any dedicated
post-merge closure PR requires its own separate approval.

## Pre-merge re-verification

* `pipeline-topology --phase lifecycle` -> PASS (branch/worktree ownership
  confirmed, single active shipment `154-S`).
* `copilot-review` gate (P-018) re-run immediately before merge -> `SATISFIED`
  at HEAD `01968b1239cd81a6eef11592c222c21695fd8e72`, all Copilot threads
  resolved.
* `gh pr checks 404` -> all 4 required checks green (`ci gate`,
  `detect code changes`, `pipeline-topology (ambient)`, `test`).

## Merge

`gh pr merge 404 --merge` (no `--admin`). Result: `MERGED` at
`2026-08-24T01:56:19Z`, merge commit
`98e2d7264c8089250a0cf442aef362c98287ef77`. Verified two parents
(`cd15a22410fb...` prior main, `01968b1239cd...` merged feature HEAD) -
P-009 merge-commit strategy preserved. `git merge-base --is-ancestor`
confirmed the SHA landed in `origin/main`.

## Backlog reconciliation (P-015)

Local `main` sync surfaced an anomaly: `146-F`, `146.001-T`, `146.002-T`,
`146.003-T` were already physically present in `.backlogit/archive/`
(routed there by `registry.yaml`'s `status: done -> archive/` rule via an
earlier in-PR commit `42d8a7b2`), but carried `status: done` with **no**
`archived_from`/`archived_status`/`commit` stamp - i.e. directory-archived
but not "hard-archived" via the single-artifact `archive` command. Ran
`backlogit archive <id>` on all four to correct this before shipment
closure.

`classify_shipment_close_path(['146-F','146.001-T','146.002-T','146.003-T'],
'.backlogit')` -> `CASCADE` (146-F is a root, fully covered by its three
manifest-member children). Invoked
`backlogit shipment ship 154-S --sha 98e2d7264c...` in place of manual
safe-close per the P-015 verified fully-covered-root exception.

Result: `shipment_status: shipped`, `archived_ids: ["146-F","154-S"]`,
`returned_ids: []`. The `archived_ids` list under-reported the three
pre-archived task items relative to the 2026-08-18 spike's documented
invariant (backlogit 1.9.0) - a live-workspace check (queue/archive
presence, `parent_id` preservation, `archived_status`/`commit` provenance)
confirmed the operation was nonetheless fully correct. Recorded as a new
compound learning:
`docs/compound/2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md`.

All backlog mutation work was committed to a new
`post-merge/154-s-docs-compound-source-value-semantics` branch created from
`main` (not committed directly to `main`), per the Post-Merge Branch
Protocol.

## Runtime verification

Single configured surface `cli`
(`.autoharness/workspace-profile.yaml` `runtime_validation`). Probe
`uv run autoharness --help` -> exit 0, PASS. `minimum_verdict: PASS`
satisfied. This shipment made no production source changes (frontmatter +
one test module + one template prose bullet), so this smoke probe is the
full extent of applicable runtime verification.

## Operational closure

Closure artifact: `docs/closure/154-S-146-F-post-merge-closure.md`.
Releasability: `READY` (`runtime_validation.releasability.required: false`,
no additional required evidence for this workspace). No residual risk, no
open follow-ups beyond routine.

## Compaction (P-020)

`compact-context --target all` performed manually (skill template only,
not installed as a resolved `.github/skills/` copy in this self-hosting
repo). The eligible fresh-memory candidate was Stage's own pre-claim
session memory for this same release unit,
`docs/memory/2026-08-23-stage-external-backlogit-verification-and-compound-source-semantics.md`
(now that 154-S has shipped), plus this Ship closure memory itself. Both
were consolidated into
`docs/memory/compacted/2026-08-23-154s-146f-compacted.md`; verbose
originals moved to `docs/archive/memory/`. `compaction_status: done`.

## Preserved state, untouched per operator instruction

Stashes `96deb084ced0e57255abbc09d5cf071dcef16b3c` (primary) and
`9439ecf93dbe03f50c8a7969ed35d077e3dd126e` (safety duplicate) were left
completely untouched - not popped, not dropped, not inspected for
mutation. Orchestrator restores them after closure per the operator's
instruction.

## Dark mode / scope note

`DARK_MODE_ACTIVE` remained bounded to this shipment and its original
six-item scope for the duration of this session. External entry
`B57F9E24` (backlogit upstream defect, still active, unrelated surface)
was not touched or implemented.

## Next steps

1. Push `post-merge/154-s-docs-compound-source-value-semantics`, open the
   post-merge closure PR, run local review readiness + CI + P-018 for that
   PR.
2. Halt at that PR's explicit operator merge-approval gate per the
   operator's instruction that closure-PR approval is separate and must
   not be inferred from the feature-PR approval.
