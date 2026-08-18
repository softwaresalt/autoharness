---
shipment: 139-S
feature: 130-F
feature_pr: 357
merge_commit: 9bb3a24b946694924e2d7306daa9a5b863784d2a
merged_at: "2026-08-18T03:13:14Z"
reviewed_head: b35b994ec2adf908b45db6a2bcaba6e46bd6d0dd
closure_status: READY_WITH_CONDITIONS
compaction_status: done
conditions:
  - id: "topology-forward-dependent-suppression-fix"
    description: >-
      Apply the verified fix in
      docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md
      to src/autoharness/gates/topology.py's _prior_shipment_id, restricting
      the reverse-edge suppression check to numerically-lower dependents
      only, plus its accompanying regression test. Must be fixed and
      verified via a dedicated Stage-triaged hotfix task before any future
      shipment relies on the numeric-adjacency implicit-predecessor
      fallback in a configuration where a numerically-higher shipment
      declares a normal forward dependency on the target.
    satisfied: false
    evidence: "Not yet applied; verified diff + regression test embedded in the compound doc for hand-off. No currently-known live shipment configuration triggers this false negative today."
---

# 139-S / 130-F Post-Merge Closure — Enforce Backlogit Checkpoint Payload Contract

Shipment 139-S shipped a canonical CheckpointV1 payload contract
(`schema_version: 1`, official CLI/MCP write route, auto-populated/validated
timestamps, domain data nested under `context`) enforced consistently across
the Stage and Ship instruction templates, their installed mirrors
(`.github/agents/_stage.agent.md`, `.github/agents/_ship.agent.md`,
`.github/instructions/backlogit.instructions.md`), a `cli_command` fallback
registry entry for `create_checkpoint`, refreshed manifest checksums, and a
new contract-test module proving malformed top-level payload shapes cannot
recur through any documented write site.

## Merge Confirmation

- PR #357 merged to `main` at `2026-08-18T03:13:14Z` with merge commit
  `9bb3a24b946694924e2d7306daa9a5b863784d2a`.
- The merge commit has two parents (`a31cb1e3` and `14767738`), preserving
  the P-009 merge-commit strategy.
- `git merge-base --is-ancestor 9bb3a24b... origin/main` confirmed exit 0.
- Closure began from synced `main` at `9bb3a24b...`.

## Runtime Verification

**Surface**: `cli` (per `.autoharness/workspace-profile.yaml`
`runtime_validation.validator_manifest.surfaces`) — the topology-gate fix
(`src/autoharness/gates/topology.py`) and checkpoint-contract enforcement
are exercised through the `autoharness` CLI.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (CLI) |
| Runtime probe | `autoharness --help` — exits 0, prints CLI help text |
| Canonical gate | `.venv\Scripts\python.exe -m pytest tests\test_checkpoint_payload_contract.py tests\test_gates_topology.py -q` plus full suite |
| Result | Targeted: 30 checkpoint-contract tests + 93 topology tests, all pass. Full suite: 1549 passed, 1 pre-existing unrelated flaky failure (confirmed via isolated re-run, not introduced by this shipment). |
| Verdict | **PASS** |

`releasability.required` is `false` in the workspace profile with
`required_evidence: []`, so no additional structured releasability artifact
beyond the evidence above is mandated; `status_when_satisfied: READY` applies.

## Backlog Reconciliation

The shipment manifest (`130-F` + `130.001-T`..`130.007-T`) includes the
covering feature itself as a root member with all 7 children present, so
`classify_shipment_close_path` returned **CASCADE** — the P-015 verified
fully-covered-root exception. The safe-close manual procedure was correctly
bypassed in favor of the cascade command:

```
backlogit shipment ship 139-S --sha 9bb3a24b946694924e2d7306daa9a5b863784d2a \
  --message "Merge pull request #357 from softwaresalt/feat/enforce-backlogit-checkpoint-payload-contract" \
  --author "Derek Williams <42183845+softwaresalt@users.noreply.github.com>"
```

Verified post-conditions:

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` (empty — no TOCTOU mismatch against the classifier) |
| `archived_ids` | exactly `[130.001-T, 130.002-T, 130.003-T, 130.004-T, 130.005-T, 130.006-T, 130.007-T, 130-F, 139-S]` (9 items, no more/less) |
| `parent_id` preserved | all 7 tasks still show `parent_id: 130-F` (matches pre-close snapshot) |
| `139-S` archive record | `archived_status: shipped`, `status: archived` |

`backlogit sync` completed after the cascade close (`CLOSURE_INDEX_SYNC_OK`,
855 artifacts indexed). No active or queued artifacts remain for this
lineage.

## Operational Closure

- **Healthy signals**:
  - Feature PR #357 merged with a verified 2-parent merge commit.
  - Targeted and full-suite canonical tests passed (30 + 93 targeted;
    1549/1550 full suite, 1 pre-existing unrelated flake).
  - CI was green at the feature PR merge gate (`ci gate`, `detect code
    changes`, `pipeline-topology (ambient)`, `test`).
  - P-018 copilot-review gate SATISFIED (0 unresolved threads across two
    review rounds, 9 threads total).
  - Cascade close verified against the classifier's static enumeration with
    no TOCTOU drift (`returned_ids: []`).
- **Failure signals to watch**:
  - Any future shipment whose manifest declares a covering feature as a
    member but *not* all of its children — that must fall back to
    safe-close, never cascade (P-015).
  - Any future write site adding a checkpoint payload that hoists domain
    fields (`shipment_id`, `feature_id`, `stash_source`, `mode`, `route`,
    `artifacts`) to the top level instead of nesting them under `context` —
    covered by `tests/test_checkpoint_payload_contract.py`'s anti-regression
    suite, but new write sites outside the documented set are not
    automatically covered.
  - The topology gate's numeric-adjacency fallback: any future shipment
    numbering scheme that reintroduces ambiguity between explicit and
    implicit predecessor inference should be checked against
    `tests/test_gates_topology.py::ImplicitNumericPredecessorTests`.
- **Validation window**: immediate post-merge closure on 2026-08-18 after
  `main` synced to merge commit `9bb3a24b...`, merged at
  `2026-08-18T03:13:14Z`.
- **Rollback trigger**: revert merge commit `9bb3a24b...` if checkpoint
  writes from Stage or Ship begin failing schema validation, or if the
  topology gate begins misclassifying shipment predecessors (false
  `PRECLAIM_ACTIVE_SHIPMENT_PRESENT`/`BRANCH_MISMATCH` blocks or missed
  genuine predecessor blocks).
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Residual follow-up**: five Copilot-review threads were declined with
  rationale rather than fixed (documented in PR #357's Follow-ups
  section): (1) shell-safe transport for `cli_command` registry values (2
  threads) — confirmed documentation-only, never shell-executed, so no
  code change required; (2) CLI-fallback gating not wired into write-site
  conditionals (3 threads) — predates this PR in both template and mirror,
  tracked as pre-existing scope, not a regression introduced here. Neither
  requires a new backlog item; both are residual-risk notes only.
- **Known residual defect on `main` (not yet fixed)**: an independent
  adversarial review during post-merge closure found that the topology
  gate's `_prior_shipment_id` multi-hop redesign (this PR's own fix for a
  different Copilot finding) also wrongly suppresses the
  implicit-predecessor fallback whenever a numerically-HIGHER shipment
  declares a normal forward dependency on the target — a real correctness
  bug flagged only as a never-threaded "Suppressed comment" in the raw
  Copilot review body, never fixed before merge. A verified fix +
  regression test is fully written up but deliberately not committed to
  this closure branch (out of `139-S`'s bounded-stop scope and the
  Post-Merge Branch Protocol's closure-only scope). See
  `docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`.
  This should be routed to Stage as a dedicated hotfix task.
- **Predecessor unblock**: shipment `138-S` (declared dependency `138-S ->
  139-S`, blocking) is now dependency-eligible for claim in a future session;
  it remains `queued` and untouched by this session per the operator's
  bounded-stop instruction.

**Closure verdict: READY_WITH_CONDITIONS.** Runtime verification passed,
the P-015 cascade close completed with all post-conditions verified, the
five residual Copilot findings are documented, rationale-backed follow-ups
rather than unresolved defects, and P-020 compaction is recorded `done`
(see `compaction_status` above). This verdict is **`READY_WITH_CONDITIONS`
rather than an unconditional `READY`** because a genuine, high-severity
correctness defect was discovered in already-merged code during this
closure's own review (see the `conditions` block in this document's
frontmatter and the Known Residual Defect note above): the defect has zero
*known* live blast radius today (no current shipment configuration
triggers it) but is not unreachable in an absolute sense, and must be
fixed and verified via a dedicated Stage-triaged hotfix task — the fix
itself is fully verified and ready, just deliberately not applied on this
closure branch, per the same discipline as the `114-S`/`109-F` closure
precedent (`docs/closure/114-S-109-F-post-merge-closure.md`) for dormant
residual gate defects surfaced by a closure PR's own review.
