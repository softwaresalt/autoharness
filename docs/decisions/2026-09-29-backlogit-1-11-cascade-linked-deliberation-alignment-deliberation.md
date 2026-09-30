---
title: "Align shipment-reconcile / P-015 CASCADE contract with backlogit >=1.11.0 flat cascade semantics"
description: "backlogit 1.11.0 stopped archiving feature-linked deliberations during `shipment ship`; autoharness still required them, so every CASCADE close with a live linked deliberation halts. Decision: realign the contract to the flat engine semantics, add a sanctioned path-independent linked-deliberation disposition step, and gate CASCADE on a verified backlogit engine-semantics line so the next drift is detected before mutation."
topic: "Stash 8FEE91F4 — P-015 / shipment-reconcile vs backlogit 1.11.0 cascade archival"
depth: "deep"
decision_status: "decided"
promoted_to: "plan"
source_stash: 8FEE91F4
deliberation_id: 038-DL
linked_artifacts:
  - "docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md"
  - ".backlogit/reconcile/190-S-cascade-close-20260929-061541.md"
  - "docs/closure/190-S-184-F-post-merge-closure.md"
tags:
  - "P-015"
  - "shipment-reconcile"
  - "cascade-close"
  - "backlogit-1.11.0"
  - "engine-behavior-drift"
  - "linked-deliberation"
---

# Align shipment-reconcile / P-015 CASCADE with backlogit >=1.11.0

## Problem Frame

During the 190-S post-merge closure (PR #464, merge `ef661e90`), backlogit 1.11.0
`backlogit shipment ship 190-S` archived `[184.001-T, 184-F, 190-S]` with
`returned_ids: []`. It did not archive deliberation `034-DL`, which is linked from
the description of the qualifying root feature `184-F`. The shipment-reconcile
two-set gate had put `034-DL` in `required_ids`, so
`required_ids - archived_ids = [034-DL]`. The run halted with a P-005, and the
operator approved a one-off standalone `backlogit archive 034-DL`.

Operator goal (verbatim): "I also want to make sure that autoharness is aligned in
workflow with how backlogit operates such that we don't recreate this scenario."

Success criteria:

* A CASCADE close never halts only because the engine left a linked deliberation
  alone, as it is designed to do.
* A consumed linked deliberation is not left live after either close path. Today
  SAFE_CLOSE strands it silently.
* The next change to backlogit's cascade semantics is detected **before** the
  destructive call, not found by a postcondition failure.
* Template, dogfood mirror, policy, gate docstring, tests, and manifest checksums
  stay in parity.

Out of scope: changes to backlogit, relaxing INV-6 (see Unresolved Questions),
and the workspace-wide engine-behavior registry (deferred, see Decision D7).

## Research Findings

### Engine behavior (read-only verification, `C:\Source\GitHub\backlogit`)

* Commit `5a4b70dd` ("fix(core): flatten shipment member projection and
  closure", task 174.058-T, 2026-09-21) is contained only in tag `v1.11.0`. Its
  message says "preserve unlisted descendants and linked deliberations".
* At `v1.11.0`, `internal/core/shipment_lifecycle.go`
  `collectArchiveCandidateIDs` (L716-751) builds its candidates from three
  sources: the shipment, each release-scope item that is terminal and not yet
  archived, and each **explicit-member** feature that is not yet archived.
  Comment L734-735: "Its descendants and linked deliberations remain independent
  unless their own IDs are explicit members."
* `ShipShipment` (L620-651) forces each explicit feature member to `done`, then
  collects and archives. `archiveItems` (L906) calls `ArchiveItem` without cascade
  and skips anything already `archived`. The result always returns
  `ReturnedIDs: []`.
* The engine's own regression test pins the behavior:
  `shipment_archive_candidate_flat_harness_test.go`
  `TestUArchiveCandidateFlat_UnlistedLinkedDeliberationIsUntouched` (a
  description-linked deliberation stays non-archived) and
  `TestUArchiveCandidateFlat_UnlistedTerminalDescendantIsUntouched`.
* At `v1.10.0`, the helper `linkedDeliberationIDs` existed (L1186) and was
  appended to the candidates (L816). The old contract was therefore correct for
  1.10.x and is wrong for 1.11.x.
* backlogit `HEAD` (`af3d13ab`, 24 commits past `v1.11.0`) has no changes to
  `shipment_lifecycle.go` or `archive.go`.
* The installed engine is `backlogit_get_version` → `1.11.0` (commit `131577c`).
* Live observation (190-S): the SHA-256 of `034-DL` (`96600a28…`) was unchanged
  across the cascade.
* Upstream observation only, no action: `doctor.go` `strandedArchiveCandidates`
  still says it approximates the ship path's "feature-linked deliberation
  resolution". That comment is stale upstream.

### Where autoharness encodes the old behavior

| Surface | Location |
|---|---|
| shipment-reconcile template | `templates/skills/shipment-reconcile/SKILL.md.tmpl` L444-449 (INV-6 scoping), L503-548 (Linked-deliberation snapshot extension), L822-843 (pre-invocation re-collection), L876-893 (allowed/required), L905-920 (027-DL tolerance), L981, L1165-1172, L1204 |
| shipment-reconcile mirror | `.github/skills/shipment-reconcile/SKILL.md` (same sections; checksum-tracked in `.autoharness/harness-manifest.yaml`) |
| P-015 | `templates/policies/workflow-policies.md.tmpl` and `.github/policies/workflow-policies.md` L499-502 (D1a), L506 (INV-1), L511 (INV-6) |
| Ship agent | `templates/agents/_ship.agent.md.tmpl` L826-830 and its `.github/agents/_ship.agent.md` mirror (CASCADE bullet) |
| Gate docstring | `src/autoharness/gates/shipment_closure.py` L9-21. The classifier logic does not inspect deliberations |
| Tests | `tests/test_cascade_close_archived_ids_postcondition.py` `CascadeCloseLinkedDeliberationAllowanceTests` (~L407-480); `tests/test_flat_manifest_closure_docs.py` `D1A_TERMS` and `INVARIANT_TOKENS` (INV-1..INV-11) |

### Prior learnings (`docs/compound/`)

* `2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`:
  the 1.10-era surprise that created the allowance this decision now withdraws.
* `2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md`:
  the autoharness expectation was wrong, not the engine.
* `2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`: claim-time
  drift. Queued stash `62C1E11E` already asks for a version/behavior gate on
  P-002.7.

This is the fourth backlogit engine-behavior drift that autoharness found at
closure time. The recurrence, not the single defect, is what the operator asked
us to fix.

### Queued work that overlaps (not modified by this session)

* `198-S` (dag-root, 192-F, cascade-close evidence command). Its A2 snapshot
  records linked deliberations. Its A3b postcondition evaluator computes
  `allowed_ids` / `required_ids` "exactly as defined" in the shipment-reconcile
  Cascade Close Sub-Procedure. If 198-S lands first, the stale definition is
  frozen into code.
* `169-S` and `171-S` edit the same shipment-reconcile Step 0 region. The overlap
  is textual only.

## Options Evaluated

### Option A: Contract realignment only

Remove validated linked deliberations from `allowed_ids` and `required_ids`. Add a
sanctioned post-cascade step that archives them explicitly.

* Pros: small, and fixes the 190-S halt.
* Cons: assumes every workspace runs 1.11.x. On backlogit 1.10.x the engine still
  archives linked deliberations, so every such close would now fail the
  unexpected-artifact check **after** mutation. The contract is global and
  templates are the product, so other workspaces can run older engines. It does
  nothing about the next drift.
* Effort: low.

### Option B: A + engine-semantics gate + path-independent disposition (chosen)

Option A, plus two additions:

* CASCADE is permitted only when a fresh backlogit version probe falls inside the
  contract's verified engine-semantics line. Anything else selects SAFE_CLOSE,
  which never depends on cascade semantics.
* The explicit linked-deliberation disposition runs after **either** close path.

* Pros: correct on every engine version. Fails closed to a path that is always
  valid. Detects the next drift before mutation. Closes the SAFE_CLOSE stranding
  gap. The version constant has a single source and is parity-tested.
* Cons: a new backlogit minor line needs a deliberate verification and a range
  bump before CASCADE is available again. That cost is intended.
* Effort: medium.

### Option C: Dual-mode contract (pre-1.11 vs >=1.11 selected by version)

* Pros: keeps CASCADE available on 1.10.x.
* Cons: doubles the contract surface of an already very large skill, and the old
  mode must stay correct with no engine to test it against. SAFE_CLOSE already
  covers old engines correctly.
* Effort: high.

### Option D: Upstream backlogit option

For example, `ship --archive-linked-deliberations`, or returning the untouched
linked IDs.

* Pros: the contract could verify instead of infer.
* Cons: backlogit's flat semantics are deliberate (174.058-T). The fix belongs to
  autoharness's workflow, not the engine. It adds a cross-repo dependency to a
  high-priority bug.
* Effort: medium, cross-repo.

### Option E: Stage-side prevention

Add deliberations as explicit manifest members, or archive deliberations at
harvest.

* Pros: the cascade would never meet a live linked deliberation.
* Cons: a deliberation as a manifest member is claimed to `active` by
  `ClaimShipment` (L167) and forced to `done` by `completeReleaseScope`. It would
  also enter Ship's task loop and the topology, sizing, and P-002.7 member
  contracts, which is a large blast radius. Archiving at harvest retires the
  decision record while the work it justifies is still in flight. Either way,
  existing queued features with live linked deliberations still need closure-side
  handling.
* Effort: medium to high.

### Option F: Workspace-wide engine-behavior registry + verify-workspace probe in this unit

* Pros: addresses the general lesson in one go.
* Cons: needs an inventory of every engine assumption across other contract
  surfaces (P-002.7 claim, Ship agent, archive and done-move semantics), a
  registry format, and a design for distribution to non-self-hosting workspaces.
  Those are different surfaces and a design decision (P-021 C1(c)). It would push
  the unit well past the 2-hour-per-task decomposition without fixing the
  high-priority halt any sooner.
* Effort: high.

## Trade-off Comparison

| Criterion | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Fixes 190-S halt | yes | yes | yes | yes (after upstream) | partly | yes |
| Correct on 1.10.x engines | **no** (post-mutation halt) | yes (SAFE_CLOSE) | yes | depends | partly | yes |
| Closes SAFE_CLOSE stranding | yes, if the step is shared | yes | yes | no | yes | yes |
| Detects the next drift pre-mutation | no | yes (for P-015) | partly | no | no | yes (all surfaces) |
| Blast radius | low | medium | high | cross-repo | high | high |
| Fits the bounded unit | yes | yes | no | no | no | no |

## Decision

**Option B**, with the following decisions. D7 defers Option F as a separately
captured item.

* **D1 — Engine semantics of record.** For backlogit 1.11.x, `shipment ship`
  archives exactly:
  * the shipment record;
  * each explicit manifest member that is terminal after release (tasks are set
    to `done` unless they are already terminal);
  * each explicit feature member, which is forced to `done` first.

  Linked deliberations and unlisted descendants are never touched. Evidence class:
  **ENGINE LAW**, proven by the engine source at tag `v1.11.0`, the engine's own
  regression tests named above, and the live 190-S observation. The 155-S-era
  claim that `collectArchiveCandidateIDs` appends `linkedDeliberationIDs` is
  recorded as SUPERSEDED provenance: correct for 1.10.x, withdrawn for 1.11.x.
* **D2 — Postcondition sets.** `allowed_ids(S) = closure_scope(S)`.
  `required_ids(S) = {S} ∪ {qualifying feature members} ∪ {x ∈ items(S) : x not
  truly archived pre-close}`. `validated_linked_deliberations(S)` leaves both
  sets. If a linked deliberation appears in `archived_ids`, the
  unexpected-artifact check fires: the engine has drifted. Step 0(c)'s
  linked-deliberation snapshot is kept, now as the **disposition snapshot** (IDs,
  single resolved location, declared status, SHA-256), and it is revalidated
  before the call. After a cascade, each snapshotted linked deliberation must be
  byte-identical to its snapshot. Any change halts with P-005.
* **D3 — Linked-Deliberation Disposition step.** This step is sanctioned and
  path-independent. It runs after the CASCADE or SAFE_CLOSE postconditions pass
  and before post-mode. For each validated linked deliberation that was not truly
  archived pre-close:
  * **Shared-reference guard.** If any artifact outside `closure_scope(S)` that is
    not truly archived still links the deliberation through any of the three
    engine-defined sources, retain the deliberation and record
    `retained_shared_reference: [ids]`. Leaving an artifact alone never fails
    closed.
  * **Otherwise, archive it.** Archive it on its own with the non-cascading
    `archive_item`, one call per ID. Then verify:
    * the `queue/` copy is gone and the `archive/` copy exists;
    * `status: archived`;
    * `archived_status` equals the pre-close declared status;
    * the body and `custom_fields` are unchanged apart from the archive
      frontmatter fields.
  * **On failure.** Halt with P-005. Do not retry, do not roll back the completed
    closure, and do not advance the report to post-mode.

  The report records the outcome of each ID: archived, retained, or
  already-archived. This makes the 190-S operator-approved deviation the
  sanctioned path.
* **D4 — Engine-semantics gate (pre-mutation drift detection).** Step 0(c) probes
  the engine fresh with `backlogit_get_version` (`no_update_check: true`) or
  `backlogit version`. It may select CASCADE only when both conditions hold:
  * the classifier returns `CASCADE`;
  * the probed version's `major.minor` is in the verified engine-semantics set.
    Today that set is `{1.11}`. Pre-release and build metadata inside a verified
    minor line (such as `1.11.1-0.2026…+dirty`) are accepted. `1.12.0-rc1` is not.

  A missing, unparseable, or unverified version selects SAFE_CLOSE with the reason
  `ENGINE_SEMANTICS_UNVERIFIED`, recorded in the report. The self-hosting Python
  implementation is a new pure function in `shipment_closure.py`, plus one
  module-level constant that is the single source for the verified set. The
  signature of `classify_shipment_close_path` is **unchanged**, so 198-S's
  dependency stays stable. A parity test pins the template, mirror, and policy
  text to the constant. Adding a new minor line requires re-verifying the D1
  evidence for that line.
* **D5 — No upstream change requested.** The engine semantics are intentional.
  The stale `doctor.go` comment is noted for the backlogit maintainers, not
  requested.
* **D6 — Option E rejected** (see Rejected Alternatives).
* **D7 — General lesson deferred and captured.** A workspace-wide backlogit
  engine-behavior compatibility registry and a verify-workspace drift probe are
  captured as a separate `DEFERRED SCOPE EXPANSION` stash entry. That entry
  cross-references `62C1E11E` and this unit. D4's constant is designed to be the
  registry's first consumer. Deferring it does not leave this unit's surface
  unguarded, because D4 already gates P-015 pre-mutation.
* **D8 — Sequencing.** The shipment carries an explicit `blocks` edge on `190-S`
  (shipped). Stage recommends, and the operator decides, that `198-S` be blocked
  by this shipment. `198-S` is an operator-declared dag-root, so Stage does not
  change it.
* **D9 — Parity.** Each surface is edited as template plus dogfood mirror in the
  same task. Manifest checksums are refreshed for the tracked mirrors
  (shipment-reconcile skill, workflow-policies, Ship agent). The P-015 policy
  history gains a version row.

## Rejected Alternatives

* **A alone.** It is unsafe on older engines: the halt moves to post-mutation, and
  nothing detects future drift.
* **C.** It doubles the contract surface for a version line that SAFE_CLOSE
  already handles correctly.
* **D.** It fights an intentional engine design and adds a cross-repo dependency
  to a high-priority bug.
* **E.** A deliberation as a manifest member picks up claim and release semantics
  meant for work items. Archiving at harvest is premature. Neither handles the
  existing backlog.
* **F in-unit.** It spans different contract surfaces and needs a design decision
  (P-021 C1(c)). It is deferred and captured, not dropped.

## Unresolved Questions

* **OQ1 (operator):** should 198-S be blocked by this shipment (recommended)?
* **OQ2:** textual overlap with queued 169-S and 171-S in shipment-reconcile Step
  0. Whichever lands second rebases. No ordering is imposed by Stage.
* **OQ3:** INV-6's descendant-inertness gate is over-conservative under 1.11.x,
  because the engine proves unlisted descendants are untouched. It stays unchanged
  and fail-closed. A relaxation would need its own deliberation.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Shared-reference scan misses a linking source | It uses the same three engine-defined sources and matcher as the snapshot. A miss only causes an archive the engine would also have done under 1.10.x, and the deliberation is recoverable with `backlogit restore` |
| Version probe unavailable (MCP down, CLI absent) | Fails closed to SAFE_CLOSE, which is always valid |
| A future 1.11.x patch changes semantics inside the verified line | The post-cascade byte-identity check on linked deliberations plus the unexpected-artifact check halt with P-005. The D7 registry follow-up widens coverage |
| 198-S freezes the stale definition into code | OQ1 recommendation. 198-S computes by reference to the skill, so landing this unit first realigns it |
| Template and mirror drift | Every task edits both. The checksum refresh and parity tests are in the same unit |

## Amendments (2026-09-29, independent plan review)

An independent four-reviewer plan review (Architecture Strategist, Correctness
Reviewer, Scope Boundary Auditor, Schema-CLI-Docs Coupling Reviewer; each
PASS_WITH_CHANGES, 0 P0, 7 P1) ran before any Ship claim on shipment `201-S`. The
decisions below amend D3, D4, D8, and D9. Option B stands. Where an amendment and
the original text disagree, the amendment wins. The plan's section "Independent
review amendments (2026-09-29)" indexes every finding and its resolution.

* **D3a — Disposition, amended (P1-1, P1-2, P1-6, P1-7).**
  * **Set.** The disposition set is collected from **every explicit manifest
    member regardless of `artifact_type`**, through the three
    **autoharness-defined** link sources (frozen from backlogit 1.10.x
    `linkedDeliberationIDs`): `custom_fields.source_deliberation_id`, the
    description, and each frontmatter `references` entry. Self and every ID in
    `closure_scope(S)` are excluded (H10). Existence is validated before
    location, and unresolved IDs never halt.
  * **Planner.** A pure, read-only `compute_linked_deliberation_disposition` in
    `shipment_closure.py` plans the outcomes, with fixture tests written first.
  * **Outcomes**, first match wins: `retained_read_error`, `retained_ambiguous`,
    `already-archived`, `retained_engine_unverified`, `retained_live_status`,
    `retained_shared_reference`, `retained_description_mention`, `archived`.
    INV-12 is the invariant (the rule that assigns each disposition-set member
    exactly one outcome); `LinkedDeliberationOutcome` is the closed enum of these
    eight values (PR #466 review, cycle 5).
  * **Reason codes.** Every outcome carries a `reason_code`, which defaults to the
    outcome value. `retained_read_error` comes first, so a record that cannot be
    read never reaches later classification. It also records the
    workspace-relative `path` and a read-error reason code: `path_escape`,
    `symlink_or_reparse_point`, `unreadable_file`, `malformed_frontmatter`,
    `body_unseparable`, or `malformed_stash_entry`. The enum is closed; the
    reason-code vocabulary is extensible, and report consumers accept unknown
    codes.
  * **Engine-gated.** When the Step 0(c) engine verdict is UNVERIFIED, nothing is
    mutated on any path. This prevents the step from recreating the 190-S
    scenario.
  * **Auto-archive only `source_deliberation_id` links.** A description or
    `references` mention is weak provenance and is report-only.
  * **Live referrers** are work items outside `closure_scope(S)`, other unshipped
    shipments (manifest, description, or `source_deliberation_id`), and active
    stash entries. Other deliberations, docs, and archived records never count.
    A deliberation whose own status is live is retained.
  * **Mutation safety.** A defined disposition baseline; a hash and guard re-check
    immediately before each archive; verify-after-each with a semantic
    frontmatter comparison and a byte-exact body.
  * **Two layers.** P-015 is split into the close-path gate (INV-7, INV-10, and
    Postcondition (a), evaluated before disposition) and the separately
    sanctioned INV-12 post-gate mutation with its own invariance check.
  * **One archiver.** The generic Ship agent's post-merge Step 7 and the
    `operational-closure` skill consume the disposition report and never archive
    a retained deliberation. P-010 gains the matching clarification.
  * D3's "engine-defined sources" label and its archive-unless-shared rule are
    superseded by this amendment.
* **D4a — Engine-semantics gate, amended (P1-3, P1-7, P2 probe surface, P2
  pseudo-versions, P2 regex).**
  * **Released builds only.** This reverses D4's acceptance of pre-release and
    build metadata inside a verified minor line. Go pseudo-versions and `+dirty`
    builds may carry unreleased engine changes, so they are `UNVERIFIED`.
  * **Same surface.** The probe runs on the same surface (MCP or CLI) that the
    close path invokes. `probe_surface`, `version`, and `commit` are recorded,
    and the pre-invocation re-probe compares all three. A re-probe failure halts
    (non-mutating) rather than substituting SAFE_CLOSE for a CASCADE verdict.
  * **Composition.** `select_close_path(classifier, engine)` is the single
    executable composition point. The classifier stays unchanged.
  * **Two propositions.** The verified line covers flat `shipment ship`
    archive-candidate selection **and** non-cascading `archive_item`
    single-artifact semantics. The policy and skill carry the machine-readable
    token ``Verified engine-semantics lines: `1.11` ``, tested against the
    constant.
  * **SAFE_CLOSE reliance, reworded.** SAFE_CLOSE does not depend on cascade
    semantics, fails closed, and never invokes the cascade. It still depends on
    `archive_item` semantics, whose generalization is `8928EC67`. The Risks table
    wording "SAFE_CLOSE, which is always valid" is superseded.
* **D8a — Sequencing, amended (operator decision 2, 2026-09-29).**
  * OQ1 is resolved. The operator decided that `198-S` waits for `201-S`. Stage
    added the edge `198-S blocks-on 201-S` on that decision.
  * The three-point `SCOPE_GAP` guard stays as defense in depth: before U1a, at
    the P-014 PR-ready gate, and immediately before merge.
  * The `198-S` / `192-F` re-plan is captured as `DEFERRED SCOPE EXPANSION` stash
    entry `1263B218`. That entry also notes the now-stale `dag-root` label on
    `198-S`.
  * `8928EC67` is raised to priority high, with a hard trigger: it must be
    deliberated before changing the verified engine-semantics lines or adopting
    backlogit 1.12. It absorbs `62C1E11E` and `archive_item` semantics.
  * All units land in one `201-S` pull request.
  * Operator goal coverage is **partial**: the P-015 close path is covered. The
    claim cascade, `archive_item` generalization, and the workspace registry are
    deferred to `8928EC67`.
* **D9a — Parity, amended (P1-4, P1-5).**
  * Whole-section byte parity is replaced. Policy and skill pairs use
    rendered-region parity over the edited paragraphs, with an allowlist. The
    Ship agent pair uses phrase-level semantic parity.
  * Checksums are refreshed in the same unit that edits a tracked mirror. The
    `operational-closure` mirror joins the tracked set (U6b).
  * `INVARIANT_TOKENS` extends to INV-12 only when both skill files contain it
    (U4). U2a adds a policy-only INV-12 test, so the suite is never red between
    tasks.
