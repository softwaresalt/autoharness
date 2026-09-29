---
title: "Align P-015 / shipment-reconcile with backlogit >=1.11.0 flat cascade semantics"
description: "Realign the CASCADE postcondition sets to backlogit 1.11.x, which leaves linked deliberations independent. Add a sanctioned, path-independent linked-deliberation disposition step, and gate CASCADE on a fresh backlogit version probe inside a verified engine-semantics line, so the next engine drift is detected before mutation instead of at closure."
doc_type: plan
status: reviewed
review_record: "inline — see section Plan Review"
created: 2026-09-29
source_stash: 8FEE91F4
source_deliberation: docs/decisions/2026-09-29-backlogit-1-11-cascade-linked-deliberation-alignment-deliberation.md
deliberation_id: 038-DL
provenance: "190-S / 184-F CASCADE close halt (PR #464, merge ef661e90; closure PR #465; reconcile report .backlogit/reconcile/190-S-cascade-close-20260929-061541.md); backlogit commit 5a4b70dd / v1.11.0"
requires_plan_hardening: "yes"
---

# Align P-015 / shipment-reconcile with backlogit >=1.11.0 flat cascade semantics

## Problem Frame

backlogit `v1.11.0` (commit `5a4b70dd`, 174.058-T) made `ShipShipment` flat.
`collectArchiveCandidateIDs` (`internal/core/shipment_lifecycle.go` L716-751)
selects the following for archival:

* the shipment;
* each terminal, not-yet-archived explicit release-scope member;
* each explicit feature member (already forced to `done` at L644).

Linked deliberations and unlisted descendants "remain independent" (L734-735).
The engine's regression test
`TestUArchiveCandidateFlat_UnlistedLinkedDeliberationIsUntouched` pins this.

autoharness still assumes the 1.10.x behavior, where the removed
`linkedDeliberationIDs` helper appended linked deliberations to the candidates:

* `templates/skills/shipment-reconcile/SKILL.md.tmpl` and its mirror
  `.github/skills/shipment-reconcile/SKILL.md`: Step 0(c) Linked-deliberation
  snapshot extension, pre-invocation re-collection, Cascade Close step 3
  `allowed_ids` / `required_ids`, the step 6 report, Quality Criteria, and the
  vocabulary summary.
* P-015 in `templates/policies/workflow-policies.md.tmpl` and its mirror
  `.github/policies/workflow-policies.md`: D1a table, admission paragraph, INV-1,
  and INV-6.
* The Ship agent CASCADE bullet in `templates/agents/_ship.agent.md.tmpl` and its
  mirror `.github/agents/_ship.agent.md`.
* The docstring of `src/autoharness/gates/shipment_closure.py` (L9-21).
* The 155-S-era contract tests in `tests/test_cascade_close_archived_ids_postcondition.py`
  (`CascadeCloseLinkedDeliberationAllowanceTests`).

As a result, every CASCADE close whose explicit feature member links a live
deliberation halts after mutation (190-S / `034-DL`). SAFE_CLOSE silently strands
the same deliberation live. Nothing detects an engine-semantics change before the
destructive call.

## Requirements Trace

| # | Requirement (decision D*) | Unit(s) |
|---|---|---|
| R1 | Engine-semantics gate: pure function plus single-source verified-line constant; unverified → SAFE_CLOSE (D4) | U1 |
| R2 | Gate docstring realigned to the flat `allowed_ids` / `required_ids` (D2) | U1 |
| R3 | P-015 D1a, INV-1, and INV-6 realigned; new INV-12 disposition invariant; CASCADE engine-semantics precondition; supersession note; history row (D1, D2, D3, D4) | U2 |
| R4 | Skill Step 0(c): engine-semantics gate step; linked-deliberation snapshot re-purposed as the disposition snapshot with SHA-256; revalidation keeps re-collection plus re-probe (D2, D4) | U3 |
| R5 | Skill Cascade Close steps 3, 5, 6, 7, Quality Criteria, and vocabulary: flat sets; a linked deliberation in `archived_ids` is unexpected; post-cascade byte-identity of linked deliberations (D2) | U4 |
| R6 | Skill: new path-independent Linked-Deliberation Disposition step with shared-reference guard and verify-after-each; post-mode and scenario matrix integration (D3) | U5 |
| R7 | Ship agent CASCADE bullet realigned, template and mirror (D2, D4) | U6 |
| R8 | Every edited mirror keeps parity with its template; tracked checksums refreshed in the same unit that edits the mirror (D9) | U2-U6 |
| R9 | Compound learning, plus supersession of the 2026-08-20 learning (D1, D7) | U7 |
| R10 | General lesson captured as a separate deferred item, not implemented (D7) | Stage (stash capture), not a unit |

## Implementation Units

Harness-surface labels:

* U1 is code-bearing and carries `harness-surface:harness-architect`. The P-004
  per-task harness applies: tests first (red, then green).
* U2-U7 are contract prose plus their pinning tests. They carry
  `harness-surface:none` and use a **test-first contract posture**: update or add
  the pinning assertions first (red against the old text), then edit the template
  and mirror (green), then refresh the checksum.

**Parity-bundle convention (applies to U2-U6).** The 2-hour granularity rule
suggests fewer than 3 files per unit. Each prose unit instead edits a *parity
bundle* of up to four files:

* the template;
* its byte-parity dogfood mirror;
* the one-line `.autoharness/harness-manifest.yaml` checksum and note for that
  mirror;
* the contract-test file that pins the text.

Splitting the bundle would leave intermediate commits with a red suite or a stale
checksum. This is the established repository convention (see the manifest notes
for 166.004-T through 166.007-T). The *intellectual* scope of each unit is still a
single contract region.

### U1 — Engine-semantics gate function and gate docstring (code)

* **Changes** in `src/autoharness/gates/shipment_closure.py`, all additive:
  * Add `VERIFIED_CASCADE_ENGINE_MINOR_LINES: Final[frozenset[tuple[int, int]]] = frozenset({(1, 11)})`.
    It is the single source of truth for the backlogit minor lines whose
    `shipment ship` semantics this contract has verified.
  * Add `class EngineSemanticsVerdict(str, Enum)` with values `VERIFIED` and
    `UNVERIFIED`.
  * Add a frozen dataclass `EngineSemanticsDecision` with fields `verdict`,
    `reason: str`, `probed_version: str | None`, and
    `minor_line: tuple[int, int] | None`.
  * Add `assess_cascade_engine_semantics(probed_version: object) -> EngineSemanticsDecision`.
    It accepts only a `str` that fully matches
    `^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$`.
    It does no `.strip()` and no coercion. The result is `VERIFIED` only when
    `(major, minor)` is in the constant. Everything else is `UNVERIFIED`, with a
    reason starting with `ENGINE_SEMANTICS_UNVERIFIED:` that names the cause:
    `non-string`, `unparseable`, or `minor line X.Y not verified`.
  * The function never raises on bad input.
  * The signature and behavior of `classify_shipment_close_path` are
    **unchanged**. `198-S` depends on it.
  * Rewrite the module docstring L9-21:
    * `allowed_ids(S) = closure_scope(S)`;
    * `required_ids(S) = {S} ∪ qualifying feature members ∪ {x ∈ items(S): not truly archived pre-close}`;
    * one paragraph stating that validated linked deliberations are outside both
      sets under backlogit 1.11.x and are handled by the skill's disposition step;
    * a pointer to `assess_cascade_engine_semantics`.
* **Tests** (new) in `tests/test_cascade_engine_semantics_gate.py`:
  1. `1.11.0`, `v1.11.0`, and `1.11.1-0.20261001000000-abcdef+dirty` are
     `VERIFIED`, with `minor_line == (1, 11)`.
  2. These are `UNVERIFIED` and name the minor line:
     * `1.10.1-0.20260823032255-b07729386a31+dirty`
     * `1.10.0`
     * `1.12.0`
     * `1.12.0-rc1`
     * `2.11.0`
  3. These are `UNVERIFIED` as `non-string` or `unparseable`: `None`, `""`,
     `" 1.11.0"`, `"1.11"`, `"dev"`, `"(devel)"`, `1.11` (a float), and `b"1.11.0"`.
  4. The docstring contains the flat `allowed_ids(S)` definition and no longer
     contains `∪ validated_linked_deliberations(S)`. The constant is exposed and
     equals `frozenset({(1, 11)})`.
* **Posture:** test-first (red, then green).
* **Size:** S. **Complexity:** low.

### U2 — P-015 policy realignment (template and mirror)

Files:

* `templates/policies/workflow-policies.md.tmpl`
* `.github/policies/workflow-policies.md`
* `.autoharness/harness-manifest.yaml` (the checksum and note of the
  workflow-policies entry)
* `tests/test_flat_manifest_closure_docs.py`

Changes:

* **D1a.** `allowed_ids(S)` becomes `closure_scope(S)`. `required_ids(S)` becomes
  `{S} ∪ {qualifying feature members} ∪ {x ∈ items(S) : x not truly archived pre-close}`.
* **Admission paragraph.** Redefine `validated_linked_deliberations(S)` as the
  **disposition set**: the validated linked deliberations of every explicit
  feature member of `items(S)`. The same three engine-defined sources, the matcher
  `\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b`, and the existence plus
  `artifact_type: deliberation` validation all apply. The set enters neither
  `allowed_ids(S)` nor `required_ids(S)`. It **excludes every ID in
  `closure_scope(S)`** (hardening H10): a deliberation that is itself an explicit
  manifest member is governed by the ordinary member rules of `allowed_ids(S)` /
  `required_ids(S)`, not by INV-12, the byte-identity check, or the drift halt.
* **INV-1.** Linked deliberations are accounted for only by INV-12, never in
  `allowed_ids(S)`.
* **INV-6.** The "may be live/required and `CASCADE` archiving it is expected"
  clause becomes: "the engine leaves it independent under the verified engine
  line; its disposition is INV-12".
* **New CASCADE precondition** in the Precondition list. CASCADE requires
  `assess_cascade_engine_semantics` (or an equivalent check) to return `VERIFIED`
  for a **fresh** probe of the installed backlogit version. The verified line is
  stated literally as `1.11` and must equal the constant. Otherwise, select
  `SAFE_CLOSE` with the reason `ENGINE_SEMANTICS_UNVERIFIED`.
* **New INV-12 (Linked-deliberation disposition).** This paragraph must be the
  authoritative restatement of hardening decisions H3 and H5 (see Plan
  Hardening). After either close path's postconditions pass:
  * each member of the disposition set that was not truly archived pre-close is
    either retained (shared reference) or archived individually and verified;
  * disposition never widens `closure_scope(S)`;
  * failure halts with P-005 and does not advance to post-mode.
* **Supersession note (2026-09-29).** The 155-S linked-deliberation allowance was
  correct for backlogit 1.10.x and is superseded for 1.11.x. Cite `5a4b70dd`, the
  v1.11.0 engine test, and 190-S.
* **History row** `1.28.0 | {{DATE}} | Corrected P-015 | …` in the template. The
  mirror uses the concrete date.

Tests, written first:

* `INVARIANT_TOKENS` covers `INV-1`..`INV-12`.
* A new test asserts in both policy texts:
  * the flat `allowed_ids(S)` row;
  * the absence of `closure_scope(S) ∪ validated_linked_deliberations(S)`;
  * the presence of `ENGINE_SEMANTICS_UNVERIFIED` and INV-12;
  * that the stated verified line equals `VERIFIED_CASCADE_ENGINE_MINOR_LINES`
    (imported from U1).
* A parity test asserts that the mirror equals the rendered template text for the
  P-015 section. Reuse the existing parity helper if one exists; otherwise compare
  the sections with `{{DATE}}` normalized.

Size M. Complexity medium. Depends on U1.

### U3 — shipment-reconcile Step 0(c): engine-semantics gate and disposition snapshot

Files: the skill template, the skill mirror, the manifest checksum and note for
the skill mirror, and `tests/test_cascade_close_archived_ids_postcondition.py`.

Changes:

* **New Step 0(c) sub-step "Engine-semantics gate"**, placed before the
  classifier result is acted on:
  * Probe `{{OP_GET_VERSION_MCP}}`-equivalent `backlogit_get_version` with
    `no_update_check: true`. The CLI form is
    `backlogit version --no-update-check --format json`. Read the `version` field.
  * Apply the verified-line rule.
  * CASCADE is selectable only when both the classifier returns `CASCADE` **and**
    the gate returns `VERIFIED`. Otherwise select SAFE_CLOSE, record the reason
    `ENGINE_SEMANTICS_UNVERIFIED: …`, and record the probed version.
  * A probe failure is `UNVERIFIED`.
  * If the template has no registry placeholder for `get_version`, use literal
    tool/CLI wording. **Do not add a new placeholder** without registry support,
    because a new placeholder would need renderer and registry changes.
* **Replace the "Linked-deliberation snapshot extension (155-S)" text** with a
  "Linked-deliberation disposition snapshot":
  * It runs for **every explicit feature member**, on both paths.
  * It uses the same three sources, the same matcher, and the same validation.
  * It keeps the torn/missing halts (`RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS` /
    `RECONCILE_FAIL_SNAPSHOT_MISSING`).
  * It records ID, single resolved location, declared status, and **SHA-256**.
  * It states explicitly that the engine does not archive these under the
    verified line, and cites `5a4b70dd` and v1.11.0.
* **Update the INV-6 scoping sentence at L444-449** to match.
* **Pre-invocation revalidation (L822-843).** Keep the linked-deliberation
  re-collection and compare the SHA-256 as well. Add a fresh engine-version
  re-probe: a different version string, or a change of verdict, halts with
  `HALT — cascade pre-invocation revalidation drift detected` and P-005.

Tests, written first. Replace `CascadeCloseLinkedDeliberationAllowanceTests`
with `CascadeCloseLinkedDeliberationFlatSemanticsTests`, keeping the valid
assertions:

* torn/missing halts;
* exact sources;
* existence and `artifact_type`;
* no blanket allowance.

The following assertions are dropped or inverted:

* the text no longer contains `linkedDeliberationIDs`, except inside an explicit
  superseded-provenance sentence;
* it contains `Engine-semantics gate`, `ENGINE_SEMANTICS_UNVERIFIED`, and
  `no_update_check`;
* the snapshot records SHA-256;
* the verified line stated in the skill equals the U1 constant.

Also add a byte-parity assertion between the template and the mirror for the
edited region. Size M. Complexity medium. Depends on U1 and U2.

### U4 — shipment-reconcile Cascade Close: flat postcondition sets and linked-deliberation byte-identity

Files: the same bundle as U3.

Changes:

* **Step 3.**
  * `allowed_ids` becomes manifest task items, qualifying feature members, and the
    shipment record.
  * `required_ids` becomes the shipment record and qualifying features
    (unconditionally), plus non-archived manifest task items.
  * Remove the linked-deliberation clauses and the `027-DL` tolerance example.
  * Keep the task-only tolerance and the feature/shipment non-tolerance
    paragraphs.
  * Add: "a validated linked deliberation in `archived_ids` fails the
    unexpected-artifact check — engine drift".
* **Step 5.** Extend it to the disposition snapshot: every snapshotted linked
  deliberation must be byte-identical (location plus SHA-256) after the cascade.
  Otherwise halt with
  `HALT — cascade modified linked deliberation {id} — engine semantics drift` and
  P-005.
* **Steps 6 and 7.** The report and the gate cover the engine-semantics decision,
  the disposition snapshot, and the byte-identity outcome. The gate's `CLOSED`
  hands off to the Linked-Deliberation Disposition step (U5) and not directly to
  post-mode.
* **Quality Criteria (L1204)** and the **P-015 Vocabulary summary (L1165-1177)**
  are rewritten to match. Add `INV-12` to the summary.

Tests, written first:

* the `allowed_ids` / `required_ids` bullets are flat;
* the drift halt string is present;
* `027-DL` is absent from the tolerance paragraph;
* the vocabulary summary lists INV-12;
* template/mirror parity.

Size M. Complexity medium. Depends on U3.

### U5 — shipment-reconcile Linked-Deliberation Disposition step (new, path-independent)

Files: the same bundle as U3.

Changes: a new `### Linked-Deliberation Disposition` subsection. Safe-close step
10 `PROCEED` and Cascade step 7 `CLOSED` both route into it before post-mode. The
step is as follows:

1. **Input.** The Step 0(c) disposition snapshot. Members already truly `archived`
   pre-close are recorded as `already-archived`, with no mutation.
2. **Shared-reference guard.** Scan the queue root and the archive root for
   artifacts that are *not* truly archived, lie outside `closure_scope(S)`, and
   link the deliberation through any of the three sources. On a match, record
   `retained_shared_reference: [ids]` and make no mutation.
3. **Archive.** Otherwise, archive the deliberation on its own with
   `{{OP_ARCHIVE_ITEM_MCP}}`. This is non-cascading, with one call per ID in
   ascending ID order. Before each call, re-verify that the record still matches
   its snapshot hash. A mismatch halts with no mutation.
4. **Verify-after-each.** All of the following must hold:
   * the queue copy is absent and the archive copy is present, with exactly one
     record;
   * `status: archived`;
   * `archived_status` equals the snapshotted declared status;
   * body and `custom_fields` are unchanged except for the engine's archive
     frontmatter keys;
   * every artifact outside `closure_scope(S)` other than this deliberation is
     still baseline-invariant.

   Any failure halts with `HALT — linked-deliberation disposition failed {id}` and
   P-005. There is no retry and no rollback of the completed closure, and the run
   does not advance to post-mode.
5. **Report.** Record `linked_deliberation_disposition: [{id, outcome: archived|retained_shared_reference|already-archived, pre_sha256, post_sha256, archived_status}]`.
6. **Post-mode.** The step 2 per-item check also covers the `archived` outcomes.
   The deleted-file guard treats their queue→archive moves as expected.

Also:

* Add two scenario-matrix rows: shared-reference retained, and engine-drift halt.
* Add a Quality Criteria bullet.
* State that this step is the sanctioned successor to the 190-S operator-approved
  deviation.

Tests, written first: the section exists; the safe-close and cascade hand-offs
point to it; the halt string, the report field, the three outcomes, and
`retained_shared_reference` are present; there is no `cascade` flag on the
archive call; template/mirror parity.

Size M. Complexity medium. Depends on U4.

### U6 — Ship agent CASCADE bullet (template and mirror)

Files:

* `templates/agents/_ship.agent.md.tmpl`
* `.github/agents/_ship.agent.md`
* `.autoharness/harness-manifest.yaml` (the checksum and note of the Ship agent
  entry)
* `tests/test_ship_safe_close_pointer.py`, or the Ship pointer test that pins
  L826-830

Changes:

* Replace "never `validated_linked_deliberations(S)`, which the engine reaches … and
  may be live/required for `CASCADE` to archive" with flat wording.
* Add: "CASCADE also requires the skill's engine-semantics gate to return
  `VERIFIED`".
* Add: "both paths end with the skill's Linked-Deliberation Disposition step".

Tests, written first: the new phrases are present and the old phrase is absent,
in both the template and the mirror.

Size S. Complexity low. Depends on U5.

### U7 — Docs: compound learning and supersession

Files:

* `docs/compound/2026-09-29-backlogit-1-11-flat-cascade-leaves-linked-deliberations.md`
  (new)
* `docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
  (append a supersession note only)

Changes:

* The learning uses frontmatter `problem_type: tool_version_behavior_drift`.
* It lists the four drift occurrences.
* It records the rule: every engine-behavior assumption carries a verified
  version line, and CASCADE fails closed to SAFE_CLOSE outside that line.
* It points to the deferred registry stash entry (D7).

No code. Size XS. Complexity trivial. Depends on U5.

## Dependency Graph

```text
U1 ──► U2 ──► U3 ──► U4 ──► U5 ──► U6
                                 └──► U7
```

The graph has no cycles. U3-U5 edit the same template and mirror in sequence, so
serial order avoids conflicting edits. U6 and U7 are independent of each other.

**Sequencing guard vs. 198-S (fail-closed).** Before U1 starts, Ship checks
whether `192-F` / `198-S` (the cascade-close evidence command) has merged to the
default branch.

* **198-S has merged.** Its A3b postcondition evaluator and fixtures encode the
  pre-1.11 `allowed_ids` / `required_ids`, and no unit in this plan updates that
  code. Ship halts with `SCOPE_GAP — 198-S evaluator requires realignment` and
  returns the shipment to Stage for a re-plan, which adds a unit for the
  evaluator. Ship must not realign the evaluator ad hoc inside U2-U5 (P-021).
* **198-S has not merged.** This plan proceeds as written. The operator decides
  whether 198-S is blocked on this shipment (OQ1, recommended).

## Decisions and Rationale

* **The gate is a separate function; the classifier is unchanged.** 198-S's A2/A3
  and the existing 750-line classifier tests stay stable. Composition happens at
  Step 0(c), where the skill already composes the classifier with the snapshot.
* **The gate verifies at minor-line granularity, not a semver range.** A range
  upper bound admits `1.12.0-rc1` (semver pre-release precedence). The engine
  change that caused this defect landed in a minor release.
* **Fail closed to SAFE_CLOSE, not HALT.** SAFE_CLOSE never depends on cascade
  semantics, so an unverified engine costs only the cascade convenience.
* **Disposition is path-independent.** SAFE_CLOSE stranded linked deliberations
  under both engine lines. The operator's goal ("don't recreate this scenario")
  covers both paths.
* **Shared-reference guard.** Under 1.11.x semantics, a deliberation's lifetime is
  the lifetime of its referrers. Retention is the non-mutating fail-safe outcome.
* **Parity bundles.** See the convention above. Checksums are refreshed in the
  same unit that edits the mirror, so the suite is never red between tasks.

## Risks and Caveats

| Risk | Likelihood | Mitigation |
|---|---|---|
| Queued `198-S` implements the stale sets in code | High if 198-S lands first | Operator decision OQ1: block 198-S on this shipment. 198-S computes the sets by reference to the skill |
| Merge overlap with `169-S` / `171-S` on skill Step 0 | Medium | Text-only rebase by whichever lands second. Each unit's parity tests catch mismatches |
| Version probe output shape changes | Low | The MCP `version` field and CLI `--format json` are both structured. Anything unparseable is `UNVERIFIED` |
| A 1.11.x patch reintroduces linked archival | Low | U4's byte-identity halt and the unexpected-artifact halt |
| The skill grows further (already about 1,270 lines) | Certain | Net change stays small because U3/U4 *replace* the 155-S text. Compaction is out of scope |
| The dogfood closure of this very shipment exercises the new step | Intended | The feature description links `038-DL`. See Runtime Verification |

## Plan Hardening Signals

* **Public API, schema, or contract change: PRESENT.** P-015 policy, the
  shipment-reconcile skill, the Ship agent contract, and a new public function in
  `autoharness.gates.shipment_closure`.
* **Security, auth, permission, or compliance: ABSENT.** No trust boundary
  changes. The version probe is a local read.
* **Migration, destructive action, or irreversible step: PRESENT.** The new
  disposition step archives backlog artifacts during closure.
* **External integration or dependency: PRESENT.** Behavior is keyed to the
  installed backlogit engine version.
* **High runtime, rollout, or rollback risk: PRESENT (moderate).** Every future
  shipment closure runs through the edited contract.

Requires plan hardening: yes

## Runtime Verification and Closure

* **U1** changes a library surface only, with no CLI. Proof: its unit tests plus
  the full existing suite (`tests/test_shipment_closure_classification.py`
  unchanged and green).
* **U2-U6** change the agent-facing contract. Proof: the pinning tests, parity
  assertions, the refreshed checksums, and `autoharness verify-workspace` clean on
  the dogfood workspace.
* **Operational closure (live proof).** This shipment's own post-merge closure is
  the first live run of the realigned contract on backlogit 1.11.0. The covering
  feature's description links `038-DL`. The expected run is:
  * the engine-semantics gate reports `VERIFIED (1, 11)`;
  * the classifier returns CASCADE, assuming a flat manifest;
  * the cascade leaves `038-DL` byte-identical;
  * the disposition step archives `038-DL` with `archived_status` equal to its
    pre-close status.

  Any other outcome is a halt for operator review. It is never an ad hoc
  deviation.
* **Rollback trigger.** A disposition halt or drift halt on any closure. Recovery:
  revert the merged PR and use SAFE_CLOSE plus a manual archive under an explicit
  operator deviation, as in 190-S. **Owner:** Ship, for closure. Stage, for
  contract follow-ups.

## Plan Hardening

Hardening pass 1 (2026-09-29, Stage, `plan-harden` applied inline).

Trigger: `Requires plan hardening: yes`. Four signals are present: contract,
destructive, external dependency, and rollout. Context pulled:

* backlogit v1.11.0 `ShipShipment`, `collectArchiveCandidateIDs`, `archiveItems`,
  and `ArchiveItem` (non-cascade path);
* `doctor.go` `strandedArchiveCandidates`;
* skill post-mode steps 1-3 and safe-close steps 8-10;
* compound learnings 2026-08-20, 2026-08-23, and 2026-08-21;
* the 198-S plan, sections A2 and A3b.

| # | Hardening | Applied to |
|---|---|---|
| H1 | **The disposition set is defined from explicit feature members of `items(S)`, not from "qualifying" features.** SAFE_CLOSE has no qualifying set. A feature that is *not* a manifest member (a task-only shipment) is not archived by either path, so its deliberation must stay live | U2, U3, U5 |
| H2 | **Pre-archive re-verification of the snapshot hash** in U5 step 3 closes the TOCTOU window between the snapshot and the disposition. A mismatch halts with no mutation | U5 |
| H3 | **`already-archived` is decided from the declared frontmatter `status == "archived"` (exact parsed scalar, the same predicate as INV-6), never from location.** A deliberation in `archive/` declaring `done` is not already archived. It goes through the guard and the archive path | U2, U3, U5 |
| H4 | **The disposition failure mode is explicit: the closure is complete, the disposition is not.** The report records `recommendation: HALT — linked-deliberation disposition failed {id}`. The committed state must not include a partially verified disposition: follow the 2026-08-15 torn-archive learning and do not commit a torn archive. Operator clearance is required | U5 |
| H5 | **The guard's scan is bounded and read-only.** It covers queue root plus archive root frontmatter only, using the same parser as the classifier (`autoharness.gates.topology._frontmatter` in self-hosting). Any id resolving to more than one record fails closed to *retain*, the non-mutating outcome, rather than halting | U5 |
| H6 | **The engine-version re-probe in pre-invocation revalidation compares the raw version string, not only the verdict.** A binary swapped between Step 0(c) and invocation is drift | U3 |
| H7 | **Actions are classified with ProposedAction / ActionRisk** (for strict-safety consumers). `archive_item` on a linked deliberation: ActionRisk *medium*, because it is reversible with `backlogit restore`. It is gated by guard, hash re-check, and verify-after-each. The version probe: ActionRisk *none*, read-only. There are no other new mutations | U5, U3 |
| H8 | **Verified-line text parity is test-enforced against the constant** in the policy (U2), the skill (U3), and the Ship agent (U6, where it references rather than restates the line). This prevents a template edit from drifting away from the code constant | U2, U3, U6 |
| H9 | **The 198-S interaction is surfaced as an operator decision, never actioned by Stage.** 198-S is an operator-declared dag-root | Shipment assembly |
| H10 | **The disposition set excludes `closure_scope(S)`.** backlogit 1.11.0 `collectArchiveCandidateIDs` still archives a linked deliberation whose own ID is an explicit, terminal manifest member (release-scope path, L719-730; comment L734-735 "unless their own IDs are explicit members"). Such a deliberation is an ordinary member of `allowed_ids(S)` / `required_ids(S)`. It is outside the disposition set, the U4 byte-identity check, and the "linked deliberation in `archived_ids` is engine drift" halt. Without this, a legitimate explicit-member deliberation would trip a false drift halt after mutation (added by plan-review pass 2) | U2, U3, U4, U5 |

Hardening result: the hardening signals are addressed. No unit needed splitting,
because H1-H8 fit inside the existing units' scope. The plan is ready for review.

## Plan Review

dispatch_mode: single-agent-declared-degradation
decision: PASS

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
No subagent dispatch surface is exposed in this Stage session. Every selected
persona rubric was applied inline, with one finding list per persona.
`TOOL_DEGRADED: model-specific-review-routing`: the anchor route is not
dispatchable, so the Architecture Strategist ran same-model inline.
agent-intercom is unavailable (`INTERCOM_DEGRADED`), so no broadcasts were sent.

Plan hardening was required, and pass 1 (H1-H9) satisfies it. The strict-safety
ProposedAction / ActionRisk classification is present (H7).

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Constitution Reviewer | inline | 0 P0/P1; 1 P3 |
| Python Reviewer | inline | 0 P0/P1; 1 P2 (resolved in plan); 1 P3 |
| Scope Boundary Auditor | inline | 0 P0/P1; 1 P2 (resolved in plan) |
| Learnings Researcher | inline | 0 P0/P1; 1 P3 |
| Architecture Strategist | inline, same-model (anchor degraded) | 0 P0/P1; 1 P2 (resolved in plan, with an operator recommendation) |
| Agent-Native Parity Reviewer | inline (triggered: agent-facing skill and agent contract) | 0 P0/P1 |
| Security Lens Reviewer | not triggered (no auth, secret, or trust-boundary surface; the version probe is local and read-only) | — |

### Findings

* **P2-1 (Python Reviewer), resolved in plan.** The first draft accepted
  whitespace-padded version strings. U1 now matches without `.strip()`, and a
  test case pins `" 1.11.0"` as `UNVERIFIED`. This is consistent with the INV-6
  no-normalization discipline.
* **P2-2 (Scope Boundary Auditor), resolved in plan.** The first draft put the
  workspace-wide engine-behavior registry into U1. It was removed and captured as
  deferred D7, a separate stash entry. U1 exposes only the single-line constant.
* **P2-3 (Architecture Strategist), resolved in plan, with an operator
  recommendation.** Queued dag-root `198-S` computes the sets by reference to
  this skill. If it lands first, the stale sets are frozen into its A3b evaluator
  and fixtures, which no unit here updates.
  * Resolution: a fail-closed sequencing guard was added under the Dependency
    Graph. If 198-S has merged before U1, Ship halts with `SCOPE_GAP` and returns
    the shipment to Stage for a re-plan. It does not expand scope ad hoc.
  * Recommendation (OQ1, operator): block `198-S` on this shipment so the guard
    never fires.
* **P3-1 (Constitution Reviewer).** U3-U5 edit one very large skill in sequence.
  Keep each task's diff scoped to its named region to ease review. Advisory.
* **P3-2 (Python Reviewer).** Consider exporting the new names from
  `autoharness.gates.__init__` only if the classifier is exported there.
  Otherwise keep them module-local. Advisory.
* **P3-3 (Learnings Researcher).** Cite
  `2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md` in
  U7 as the precedent where "the autoharness expectation was wrong, not the
  engine". Advisory. It is already in the decision record.

No plan unit contradicts a prior resolution. The 2026-08-20 learning's
halt/revert instruction was already superseded (2026-08-24) by the allowance this
plan now withdraws for 1.11.x. U7 records that supersession. Runtime verification
and operational closure are present.

**Gate: PASS.** There are no P0 or P1 findings. All three P2 findings were
resolved by revising the plan before the gate. The open items are P3 advisories
plus the operator recommendation OQ1, which the sequencing guard makes safe
either way. The plan is harvest-ready.

Reviewer independence caveat: the plan author (Stage) also ran this review
inline, with the same model and no subagent dispatch. The operator may request a
multi-agent or anchor re-review before Ship claims the shipment. This does not
block harvest.

### Plan Review — pass 2 (2026-09-29, resumed Stage session)

dispatch_mode: single-agent-declared-degradation (no subagent dispatch surface in
the resumed session; `TOOL_DEGRADED: reviewer-subagent-dispatch`). Personas
re-applied inline: Constitution, Python, Scope Boundary, Learnings, Architecture
Strategist, Agent-Native Parity. Factual claims were re-verified against sources:

* backlogit `5a4b70dd` exists; `collectArchiveCandidateIDs` at
  `internal/core/shipment_lifecycle.go` L716 with the "remain independent unless
  their own IDs are explicit members" comment; engine test
  `TestUArchiveCandidateFlat_UnlistedLinkedDeliberationIsUntouched` present;
  installed engine `backlogit version --no-update-check --format json` →
  `1.11.0`; MCP `get_version` accepts `no_update_check` (`internal/mcp/tools.go`
  L565).
* Skill anchors (L444, L503, L824, L881, L916, L1163, L1197, L1204), the
  `{{OP_ARCHIVE_ITEM_MCP}}` placeholder (L599), `INVARIANT_TOKENS` (range 1..11,
  `tests/test_flat_manifest_closure_docs.py` L38),
  `tests/test_ship_safe_close_pointer.py`, and `topology._frontmatter` all exist.
  `classify_shipment_close_path` is not exported from `autoharness.gates`, so
  P3-2 resolves to "keep new names module-local".

Findings:

* **P2-4 (Architecture Strategist / Scope Boundary), resolved in plan.** The
  disposition set did not exclude deliberations that are themselves explicit
  manifest members, which the 1.11.0 engine still archives on the release-scope
  path. U4's byte-identity check and drift halt would then fire falsely after a
  legitimate mutation. Resolution: hardening H10 and the U2 admission paragraph
  now exclude `closure_scope(S)`; tasks 195.002-T through 195.005-T carry the
  exclusion as an acceptance criterion.
* **P3-4 (Python Reviewer).** `CascadeCloseLinkedDeliberationAllowanceTests`
  spans L403-647 (not only ~L407-480). U3 replaces the whole class; keep valid
  assertions per the U3 list. Advisory; the M size stands.

**Gate (pass 2): PASS.** No P0/P1. P2-4 resolved before the gate. Harvest stands,
with the task updates above.
