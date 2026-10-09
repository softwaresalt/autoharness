---
title: "R1 — claim-marker consumption contract (P-002.8, marker_contract_version: 1)"
date: 2026-10-08
created_at: 2026-10-08T21:45:00Z
status: reviewed
source_stash: [21F8C04A]
paired_stash: F2D11D61
source_doc: docs/design-docs/2026-10-07-autoharness-requirements-carryover.md
deliberation: docs/decisions/2026-10-08-r1-claim-marker-consumption-deliberation.md
predecessor_shipment: 211-S
---

# R1: claim-marker consumption contract (P-002.8, `marker_contract_version: 1`)

## Problem Frame

backlogit's `ClaimShipment` (154-S/173-F, producer contract `scheduler-baseline-marker/v1`)
stamps `custom_fields.scheduler_baseline_claim = <S>` on every member it activates. autoharness
has no consumer of that marker.

* `templates/agents/_ship.agent.md.tmpl` Step 3 item 1 keeps every `queued` and `active`
  manifest task in the executable set.
* P-002.7 (`templates/policies/workflow-policies.md.tmpl`) defines the three post-claim rows,
  T1 to T3.
* No Ship step writes a start record.

So autoharness cannot tell a claim-activated member from an organically active residual. It
cannot publish the single versioned consumer contract that backlogit Ship Step 4.0 is meant
to cite either.

Deliberation (D1–D8) corrected two premises from the stash entry:

* autoharness has no P-002.6 wave scheduler. That scheduler is a drift-ignored backlogit
  customization.
* R1 no longer gates `153-S`. Condition (b) on `154-S` was satisfied by an operator
  substitution attestation at `2026-10-07T06:31:36Z`.

The chosen scope (Option B) is:

1. Publish the consumer contract as a new policy block, P-002.8.
2. Apply it in Ship Step 3 and Step 4.1.
3. Gate both behind a new opt-in registry capability, `features.scheduler_baseline_claim`.
4. Back acceptance (1) and (2) with a test-side fixture proof.

## Requirements Trace

| Requirement (21F8C04A / carryover R1) | Unit(s) |
|---|---|
| Read active shipment, ordered `custom_fields.items`, member status, marker, `logs/<id>.jsonl` | U3 (rule M2), U4 |
| Claim-assigned iff active ∧ marker = S ∧ in live manifest ∧ no valid start record in current epoch | U3 (M3), U5 (epoch and start record), U6 |
| Every other active member is an active residual (`WAVE_NO_PROGRESS`, detail `active residual`) | U3 (M4), U4, U6 |
| Admit claim-assigned members to wave 1 without treating them as residual | U3 (M6), U4, U6 |
| `WAVE_CLAIM_STATE_INDETERMINATE` on active-shipment count ≠ 1, manifest drift, stale or errored read, marker = S with missing, unparseable, or claim-event-less log; indeterminate takes precedence | U3 (M5), U4, U6 |
| Single versioned contract (`marker_contract_version: 1`) cited by both consumers | U3 (canonical), U4 and U5 cite, D8 (backlogit cross-workspace follow-up) |
| Acceptance (1): dependency-ready member admitted in wave 1, rest claim-assigned waiting, zero residuals | U6 scenario F1 |
| Acceptance (2): missing or non-S marker → residual; marker = S but no claim event → indeterminate | U6 scenarios F2–F4 |
| Acceptance (3): operator-only `CONDITION_B_ATTESTED` on 154-S after release and install | U7 (release note and operator procedure). No task originates the attestation. |
| Optional `src/autoharness/gates/topology.py` `pre_claim` marker check (L3) | **Deferred** (D3). A new stash entry is captured. |

## Contract Shape (normative content U3 must publish)

P-002.8 lives in its own `<!-- P-002.8:BEGIN canonical claim-marker consumption contract -->`
… `<!-- P-002.8:END -->` block, placed immediately after the `P-002.7:END` marker. It declares
`marker_contract_version: 1` and `producer_contract: scheduler-baseline-marker/v1`.

The producer is cited by contract ID plus an absolute URL, namely
`https://github.com/softwaresalt/backlogit/blob/main/docs/design-docs/scheduler-baseline-marker-contract.md`.
It is **never** cited by a workspace-relative path. Installed workspaces do not contain that
file, and a relative path would fail the template cross-reference-integrity gate. The same rule
applies to every backlogit reference in U3, U4, U5, and U7.

The rules are numbered so consumers cite IDs rather than restating text:

* **M1 Capability gate.** The contract applies only in shipment mode, only when the backlog
  registry declares `features.scheduler_baseline_claim: true`. When the flag is false or
  absent, nothing changes and P-002.7 alone governs.
* **M2 Reads.**
  * Use the producer read recipe: active-shipment list, `custom_fields.items` read twice, and
    each member's `status` and `custom_fields.scheduler_baseline_claim`.
  * Read the member's item log `logs/<id>.jsonl` through a configured tool when one exposes
    the event stream.
  * Otherwise, read it raw only under an explicit, session-recorded, scoped P-012 declaration
    naming the path.
* **M3 Claim-assigned.** A member is claim-assigned iff all of these hold:
  * its status is `active`;
  * its marker equals the live shipment `S`;
  * it is listed in `S`'s live `custom_fields.items`;
  * its current start epoch has no valid start record.

  Start epoch definition: the log suffix beginning at the latest `status_changed` event with
  `delta.to: active` and `delta.reason: shipment claimed`, or the whole log if no such event
  exists.

  Valid start record definition: a `comment` event in the epoch whose actor is `ship` and whose
  first line exactly equals `WORK_STARTED: <S>`. The first line is the comment split at `\n`,
  with one trailing `\r` stripped.
* **M4 Active residual.** Every other `active` member is an active residual
  (`WAVE_NO_PROGRESS`, detail `active residual`). This includes:
  * a missing or non-`S` marker;
  * absence from the live manifest;
  * a valid start record in the current epoch.
* **M5 Indeterminate (precedence).** Halt `WAVE_CLAIM_STATE_INDETERMINATE` and report each
  member's reason, together with the residuals, when any of these hold:
  * the active-shipment count is not exactly 1, or the sole active shipment is not `S`;
  * the two manifest reads differ (manifest drift);
  * an item read errors, or its status disagrees with the snapshot (stale read);
  * the producer contract's R3 consumer rule holds when its read recipe is applied. This is a
    CLI/MCP read divergence after a partial compensation, detected as a mismatch between two
    transports or a re-read. It is cited by contract ID and residual ID, not restated;
  * the marker equals `S` but the member log is missing, is unparseable, or lacks the
    `shipment claimed` claim event.

  Indeterminate outranks residual.
* **M6 Admission.**
  * `ready_1 = { t ∈ queued ∪ claim-assigned : every dependency of t is terminal_success }`
    (`done` or `archived`).
  * A claim-assigned member with unfinished dependencies is reported `claim-assigned waiting`.
    It is never a residual.
  * When the shipment is admitted, `active_ids` lists only residuals.
* **M7 Relationship to P-002.7.** P-002.8 is the marker-evidenced discriminator at P-002.7's
  claim boundary. A claim-cascade-activated member (marker = `S`, in the manifest, no start
  record) is never a residual, which is consistent with row T1. P-002.8 adds no row to the
  P-002.7 table.
* **M8 Shared tokens.** These tokens are used verbatim and shared with backlogit Ship Step 4.0:
  * `claim-assigned`
  * `claim-assigned waiting`
  * `active residual`
  * `WAVE_NO_PROGRESS`
  * `WAVE_CLAIM_STATE_INDETERMINATE`
  * `WORK_STARTED: <S>`
  * `marker_contract_version: 1`

  Any change to M1–M8 bumps `marker_contract_version`.

## Implementation Units

Every template unit mirrors its `templates/` edit into the installed `.github/` copy and
refreshes that mirror's checksum in `.autoharness/harness-manifest.yaml` (dogfood parity). It
anchors by heading or marker block, never by line number. Canonical test gate:
`PYTHONPATH=src python -m unittest discover -s tests`. Generated text uses UTC `Z` timestamps
only, because 211-S C4 lints templates and mirrors for offset date-times.

### U1: Registry schema capability flag
**Size:** XS. **Complexity:** low. **Domain:** schema. **Posture:** test-first.

* **Files:**
  * `schemas/backlog-tool-registry.schema.json`
  * new `tests/test_registry_scheduler_baseline_claim_flag.py`. No existing test validates
    this schema directly. Use `jsonschema`, which is already a runtime dependency in
    `pyproject.toml`.
* **Change:** add `"scheduler_baseline_claim": { "type": "boolean", "default": false,
  "description": "True when the backend stamps custom_fields.scheduler_baseline_claim on
  claim-activated shipment members (producer contract scheduler-baseline-marker/v1) and the
  workspace opts in to P-002.8 consumption" }` under `features.properties`. Leave the
  `required` sets unchanged.
* **Tests (≤3):**
  * a schema with the flag `true` validates;
  * a schema with the flag set to a string fails;
  * the flag is absent from the `required` sets.

### U2: Registry template and dogfood registry opt-in default
**Size:** XS. **Complexity:** trivial. **Domain:** config. **Depends on:** U1.

* **Files:**
  * `templates/backlog/registries/backlogit.registry.yaml`
  * `.autoharness/backlog-registry.yaml`
  * `.autoharness/harness-manifest.yaml`. The dogfood registry is a manifest entry
    (`path: ".autoharness/backlog-registry.yaml"`, `template:
    "backlog/registries/backlogit.registry.yaml"`), so refresh its checksum over the LF bytes.
* **Change:** add `scheduler_baseline_claim: false` under `features`, with a one-line comment.
  The comment says to opt in only when the installed backlogit stamps the marker (`154-S`
  producer, `scheduler-baseline-marker/v1`) and cites P-002.8. Do not touch
  `backlog-md.registry.yaml`: the schema default `false` covers it.
* **Tests:** add one assertion to U1's module. It validates both registry files against the
  schema and asserts that `features.scheduler_baseline_claim` is boolean `false`. Existing
  registry tests (`tests/test_stash_archive_registry_and_policy_migration.py`) must stay green.

### U3: P-002.8 policy contract block
**Size:** M. **Complexity:** medium. **Domain:** template (policy). **Depends on:** U1.
**Posture:** test-first.

* **Files:**
  * `templates/policies/workflow-policies.md.tmpl`
  * `.github/policies/workflow-policies.md`
  * `.autoharness/harness-manifest.yaml`
  * new `tests/test_p002_8_marker_consumption_contract.py`
* **Change:** insert the P-002.8 block (Contract Shape above, M1–M8) immediately after
  `<!-- P-002.7:END -->`, and add one Amendment Log row with the next minor version after the
  merged predecessors.
  * Do not edit bytes inside the P-002.7 BEGIN/END block.
  * Do not add rows to its table.
  * Do not alter its Amendment Log row.
  * Do not copy P-002.7's clause anchor or its "Canonical post-claim member-status vocabulary"
    heading text into P-002.8 or any other file. `tests/p002_7_candidate_definition.py`
    `is_declaring_surface` would then count a fifth declaring surface, and
    `check_e_exactly_four_surfaces` would fail. Refer to P-002.7 by ID only.
* **Tests (≤4 scenarios):**
  1. The template and mirror contain an identical P-002.8 block declaring
     `marker_contract_version: 1` and `scheduler-baseline-marker/v1`.
  2. Rule IDs M1–M8 are present, and every M8 token appears.
  3. The P-002.7 block is byte-identical before and after. The existing
     `tests/test_p002_7_member_status_contract.py` stays green.
  4. The P-002.8 block sits outside the P-002.7 block, and the Amendment Log row names P-002.8.

### U4: Ship Step 3 marker-consumption admission
**Size:** M. **Complexity:** medium. **Domain:** template (agent). **Depends on:** U3.

* **Files:**
  * `templates/agents/_ship.agent.md.tmpl`
  * `.github/agents/_ship.agent.md`
  * `.autoharness/harness-manifest.yaml`
  * extend `tests/test_p002_8_marker_consumption_contract.py`
* **Change:** add Step 3 item 1b, "Claim-marker consumption (P-002.8, `marker_contract_version:
  1`)", after the executable-set derivation (item 1) and before the ready-queue listing
  (item 2). It cites M1–M8 by ID. When M1 is satisfied it:
  * classifies every `active` member of the derived set per M3–M5, with indeterminate first;
  * halts `WAVE_CLAIM_STATE_INDETERMINATE` per M5;
  * halts `WAVE_NO_PROGRESS` (detail `active residual`) on any residual, except one case.
    Under the Crash-Resumption Protocol, when the operator has explicitly confirmed restore of
    a `ship`-owned checkpoint, the single residual whose ID equals that checkpoint's recorded
    current task ID is reported as `active residual (operator-resumed)` and admitted
    (deliberation D5);
  * otherwise feeds item 2 with `queued ∪ claim-assigned`, ordered per M6, and reports
    claim-assigned members with unfinished dependencies as `claim-assigned waiting`.

  When M1 is not satisfied, the text states that Step 3 is unchanged. Further constraints:
  * Use only existing placeholders, for example `{{OP_LIST_SHIPMENTS_MCP}}`,
    `{{OP_GET_SHIPMENT_MCP}}`, `{{OP_GET_MCP}}`, `{{STATUS_ACTIVE}}`. Introduce no new
    `{{VARIABLE}}`.
  * Leave item 1a (`SHIPMENT_STATE_INCONSISTENT`) and the Step 0.5 P-002.7 cross-reference
    block unchanged and ahead of this item.
* **Tests (≤4 scenarios):**
  1. The template and mirror carry item 1b citing P-002.8 and `marker_contract_version: 1`.
  2. Both halt tokens and the `claim-assigned waiting` report are present.
  3. The flag-false path states no behavior change.
  4. The operator-resumed carve-out is restricted to a confirmed `ship`-owned checkpoint's
     single recorded task.

### U5: Ship Step 4.1 start-record append
**Size:** S. **Complexity:** medium. **Domain:** template (agent). **Depends on:** U4 (same file,
serialize).

* **Files:**
  * `templates/agents/_ship.agent.md.tmpl`
  * `.github/agents/_ship.agent.md`
  * `.autoharness/harness-manifest.yaml`
  * extend `tests/test_p002_8_marker_consumption_contract.py`
* **Change:** under M1, after moving the task to `{{STATUS_ACTIVE}}`, Step 4.1 must:
  * not move a claim-assigned task again;
  * read the member log and append the comment `WORK_STARTED: <S>` with actor `ship`, through
    the registry's `append_comment` operation, only when no valid start record exists in the
    current epoch (M3);
  * on an append error, re-read before any retry or CLI fallback so the record is never
    duplicated;
  * halt `WAVE_CLAIM_STATE_INDETERMINATE` on an unreadable log.

  When the flag is false, Step 4.1 is unchanged.
* **Tests (≤3):**
  1. Step 4.1 cites M3 and contains `WORK_STARTED: <S>`.
  2. The idempotent re-read-before-append rule is present.
  3. The flag-false no-change statement is present.

### U6: Fixture proof for acceptance (1)/(2)
**Size:** M. **Complexity:** medium. **Domain:** tests. **Depends on:** U3.
**Posture:** test-first (`harness-surface: none`, no `src/` module).

* **Files:**
  * new `tests/fixtures/marker_contract_v1/scenarios.json`
  * new `tests/test_marker_contract_v1_fixtures.py`
* **Change:** a test-local reference evaluator encoding M3–M6. It takes the active-shipment
  list, two manifest reads, member records (status, marker, deps), and member logs (event
  lists using UTC `Z` timestamps). It returns `admitted`, `claim_assigned_waiting`,
  `active_residuals`, `indeterminate`, and a halt token. The test also asserts that the
  fixture's `marker_contract_version` equals the value parsed from the P-002.8 block, so the
  fixture cannot drift from the contract.
* **Scenarios:**
  * **F1 (acceptance 1):** claimed `S`; three active, marker-stamped members with claim events;
    member B depends on A and C depends on B. Result: A is admitted, B and C are
    `claim-assigned waiting`, and there are 0 residuals.
  * **F2 (acceptance 2a):** missing marker → active residual, never claim-assigned.
  * **F3 (acceptance 2a):** marker set to another shipment → active residual.
  * **F4 (acceptance 2b):** marker = `S` but the log lacks the `shipment claimed` event →
    `WAVE_CLAIM_STATE_INDETERMINATE`, which wins over a co-present residual.
  * **F5–F7 (indeterminate):** two active shipments; manifest drift between the reads; a valid
    `WORK_STARTED: S` in the current epoch, which is a residual.

  F5–F7 can be table-driven inside one test method with subtests, keeping the unit to four or
  fewer test methods.

### U7: Release note and operator follow-up procedure
**Size:** XS. **Complexity:** trivial. **Domain:** docs. **Depends on:** U2, U4, U5, U6.

* **Files:**
  * `CHANGELOG.md` (Unreleased)
  * new `docs/claim-marker-consumption.md`. No registry-features guide exists today. This is an
    operator guide that points to P-002.8 and must not restate rules M1–M8.
* **Change:**
  * Add a changelog entry for P-002.8, `marker_contract_version: 1`, and the opt-in flag.
  * Document the flag next to the registry feature list. Cover the opt-in and fail-closed
    behavior, and say that the flag requires the producer `scheduler-baseline-marker/v1`.
  * Add a short operator follow-up that matches carryover-doc §"backlogit follow-up". After
    installing the release, run `autoharness verify-workspace` and set
    `features.scheduler_baseline_claim: true` in backlogit. Then the **operator alone** may post
    `CONDITION_B_ATTESTED` on `154-S`, citing the release and the
    `tests/test_marker_contract_v1_fixtures.py` proof, to replace the 2026-10-07 substitution.
    No agent originates it.
* **Tests:** none. This unit is docs only.

## Dependency Graph

```text
211-S ──blocks──▶ this shipment
U1 → U2
U1 → U3 → U4 → U5
         U3 → U6
{U2, U4, U5, U6} → U7
```

U4 and U5 share the Ship template, so they are serialized. U3 and U4 also share
`.autoharness/harness-manifest.yaml`.

## Decisions and Rationale

See the deliberation. Summary:

* **D1:** Option B. Publish the consumer contract only, not a full P-002.6 port.
* **D2:** priority high, not critical. R1 no longer gates 153-S.
* **D3:** L3 topology `pre_claim` check deferred. The marker does not exist pre-claim, L3 owns
  attestation predicate (C), and that work is contingent on A592FC1C. A new stash entry is
  captured.
* **D4:** start-record write in Step 4.1.
* **D5:** a residual halts, with the operator-resumed carve-out.
* **D6:** opt-in capability flag, default `false`.
* **D7:** test-side fixture proof.
* **D8:** backlogit citation and attestation are out-of-workspace follow-ups (P-017).

## Risks and Caveats

* **Shared files with predecessors.**
  * `templates/agents/_ship.agent.md.tmpl` and its mirror are shared with 208-S (Step 5 item
    7c) and 210-S (B6, Step 0.5 carry-forward).
  * `templates/policies/workflow-policies.md.tmpl` and its mirror are shared with 208-S (P-018)
    and 210-S (B5, P-011). The Amendment Log version is shared with all of them.
  * `.autoharness/harness-manifest.yaml` is shared with 208-S, 209-S, 210-S, and 211-S.
  * Ship **must rebase onto merged 211-S** (and thus all predecessors) before U3. It
    recomputes mirror checksums after rebase and takes the next free Amendment Log minor
    version at execution time, not a pre-chosen number.
* **P-002.7 byte-stability.** Any byte change inside the P-002.7 block fails
  `tests/test_p002_7_member_status_contract.py`. U3 inserts only after `P-002.7:END`.
* **UTC lint (211-S C4).** No offset date-times in templates or mirrors. Fixture timestamps use
  `Z`.
* **Fixture proof is a model, not an execution trace.** The fixture proves that the decision
  table yields the acceptance outcomes. The contract-text tests prove the policy and Ship carry
  that table. A live-claim runtime proof happens in backlogit after install (operator
  procedure, U7).
* **Opt-in misconfiguration.** Enabling the flag against a non-stamping backend halts every
  claimed shipment as residual. This is fail-closed, and U7 documents it.

## Plan Hardening Signals

* **Public API, schema, or contract change: present.** This plan adds a registry schema
  property (U1), a new cross-workspace consumer contract (U3), and new Ship halt tokens (U4).
* **Security, auth, permission, or compliance: absent.** Item-log reads stay under P-012
  scoped declarations, and no credentials are involved.
* **Migration, destructive, or irreversible step: absent.** The change is additive and
  default-off.
* **External integration or operator checkpoint: present.** The plan depends on the backlogit
  producer contract, and acceptance (3) is an operator-only attestation.
* **High runtime, rollout, or rollback risk: present (moderate).** Ship admission behavior
  changes when the flag is on. Rollback is setting the flag to `false`.

Requires plan hardening: yes

## Runtime Verification and Closure

| Unit | Runtime surface | Verification | Closure artifact |
|---|---|---|---|
| U1/U2 | registry load in `install`/`verify-workspace` | schema tests; `verify-workspace` on this repo still passes, with the flag `false` | none beyond tests |
| U3–U5 | Ship agent behavior (prompt contract) | contract-text tests plus the unchanged P-002.7 suite | release note (U7) |
| U6 | none (tests) | fixture suite green | fixture path cited by the operator attestation |
| U7 | docs | link and path integrity | operator follow-up procedure |

Closure: the shipment closes `READY_WITH_CONDITIONS`, with condition "backlogit install and
operator attestation" owned by the operator. That is out-of-workspace and does not gate any
autoharness successor.

## Plan Hardening

**Hardening required:** yes. The plan changes a schema and a cross-workspace contract, has an
operator checkpoint, and changes Ship admission when the flag is on. P-006 applies.

**Consulted:**

* `docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`, the P-002.7
  basis.
* `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`, on mirror and manifest
  checksums.
* `docs/compound/106-S-claim-integrity-guards.md`.
* `tests/test_p002_7_member_status_contract.py` with its candidate and near-miss fixtures.
* backlogit `docs/design-docs/scheduler-baseline-marker-contract.md` (producer v1).
* backlogit `.github/agents/_ship.agent.md` Step 4.0 and the start-record procedure (~L509–585,
  ~L745–770).
* `.github/instructions/backlogit.instructions.md`, on the backlog-root contract.

### Protected invariants

1. **P-002.7 block is byte-stable.** U3 inserts strictly after `<!-- P-002.7:END -->`. Its
   test asserts the extracted P-002.7 block is byte-identical before and after the edit.
2. **Flag off means zero behavior change.** U4 and U5 text opens with the M1 guard. Tests
   assert the "unchanged when `features.scheduler_baseline_claim` is false or absent" sentence
   appears in both Step 3 item 1b and Step 4.1.
3. **Integrity guards keep their order.** Step 0.5 item 1a (`SHIPMENT_STATE_INCONSISTENT`) and
   the `shipment-reconcile` pre-mode check run before item 1b. P-002.8 never suppresses or
   pre-empts them.
4. **Non-shipment mode is excluded.** M1 requires a session shipment `S`. Ship without a
   shipment never classifies.
5. **No new template placeholders.** Item reads use `{{OP_GET_MCP}}`. Shipment reads use
   `{{OP_LIST_SHIPMENTS_MCP}}` and `{{OP_GET_SHIPMENT_MCP}}`. Comments use the registry
   `append_comment` operation, named in prose. `verify_workspace.py` OP maps are not touched,
   which preserves width isolation.

### Tightened rules (fold into the U3/U4/U5 text)

* **H1: the operator-resumed carve-out is narrow.** It applies only when every one of these
  holds:
  1. the operator confirmed restore of a `ship`-owned checkpoint in this session;
  2. the residual's ID equals that checkpoint's recorded current task ID;
  3. the member's marker equals `S`, and it is in the live manifest.

  Any second residual, or a mismatch on any condition, halts `WAVE_NO_PROGRESS`. The carve-out
  never applies to an indeterminate member.
* **H2: raw-log path safety.** A raw `logs/<id>.jsonl` read must:
  * resolve inside the detected backlog root (`.backlog/` or legacy `.backlogit/`);
  * fail closed with `WAVE_CLAIM_STATE_INDETERMINATE` when both roots exist, when the root is
    unknown, or when the resolved path escapes the root via symlink or `..`;
  * be preceded by a P-012 scoped declaration naming the path.
* **H3: start-record idempotence.** Step 4.1 re-reads the log immediately before appending. A
  failed append is followed by a re-read before any retry. Ship never appends a second
  `WORK_STARTED: <S>` in the same epoch.
* **H4: session re-entry without a checkpoint is fail-closed.** If Ship re-enters Step 3 after
  some tasks already carry `WORK_STARTED: <S>` and no operator-confirmed resume exists, those
  tasks are residuals and Ship halts `WAVE_NO_PROGRESS`. This is intended: the operator
  disposes. The rule is stated in item 1b.
* **H5: contract versioning.** M8 states that any change to M1–M8 bumps
  `marker_contract_version`, and that a change to the producer `scheduler-baseline-marker/vN`
  requires a P-002.8 amendment before the flag is honored. U6 parses the version from the
  P-002.8 block, so a bump without a fixture update fails the suite.

### ProposedAction / ActionRisk

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| PA1: add `features.scheduler_baseline_claim` (default `false`) to the registry schema and registries (U1/U2) | low (additive, default-off) | normal PR review | revert the commit |
| PA2: publish the P-002.8 contract and new Ship halt tokens (U3/U4/U5) | medium (contract surface consumed cross-workspace) | plan-review + PR review (P-014) | revert; consumers stay on flag `false` |
| PA3: at runtime with the flag on, Ship appends a `WORK_STARTED: <S>` comment per started task | medium (backlog mutation, append-only, idempotent) | the workspace opt-in is the approval | set the flag to `false`; existing comments are inert when the flag is off |
| PA4: post `CONDITION_B_ATTESTED` on backlogit `154-S` | high (cross-workspace gate input) | **operator-only human checkpoint**, out of workspace | operator revocation per the 154-S closure revocation procedure |

No agent performs PA4. U7 documents it only.

### Verification and closure additions

* **Environment precheck (Ship, before U3):**
  * rebase onto merged `211-S`;
  * confirm the P-002.7 suite is green on the rebased base;
  * re-locate the anchors by heading or marker.
* **Gate per unit:** `PYTHONPATH=src python -m unittest discover -s tests` runs on the whole
  suite. U3 additionally runs `tests/test_p002_7_member_status_contract.py` explicitly before
  and after.
* **Blocked path:** if the mirror diverges from the template after rebase (dogfood parity
  failure), halt and re-mirror. Never hand-edit the checksum without re-hashing.
* **Monitoring signal:** in opted-in workspaces, `WAVE_NO_PROGRESS` or
  `WAVE_CLAIM_STATE_INDETERMINATE` halts at Step 3. Repeated halts on fresh claims mean the
  producer is absent or older, so roll back to `false`.
* **Owner:** the operator owns the opt-in and the attestation. Ship owns the template changes.
* **Validation window:** the first backlogit shipment claimed after install.

### Review-gate capability risk

Reviewer subagent dispatch is not available in this Stage session. plan-review must record
`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`. It
must also emit the literal markers `dispatch_mode: single-agent-declared-degradation` and
`decision: PASS|ADVISORY|FAIL`, so harvest can fail closed.

**Unresolved operator decisions blocking execution:** none. D2 (priority high) and D3 (L3
deferral) are reported to the operator and can be revisited without changing this plan.

## Plan Review

### Review attempt 1 (2026-10-08T21:55Z)

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
No subagent or model-routing dispatch surface is exposed to this Stage session. All seven
personas were applied inline, with one finding list per persona.

dispatch_mode: single-agent-declared-degradation
decision: FAIL

The attempt failed on one P1 finding:

* **P1-1 (Architecture Strategist and Constitution Reviewer).** The P-002.8 producer citation
  used a workspace-relative backlogit path (`docs/design-docs/scheduler-baseline-marker-contract.md`).
  That path does not exist in installed workspaces, so it would fail the template
  cross-reference-integrity quality gate.

P2 findings from attempt 1:

* **P2-1:** U2 omitted the manifest checksum refresh for `.autoharness/backlog-registry.yaml`,
  which is a manifest entry.
* **P2-2:** nothing guarded against P-002.8 or U7 copying P-002.7 clause-anchor or vocabulary
  text. That would create a fifth declaring surface and fail
  `check_e_exactly_four_surfaces`.
* **P2-3:** the M5 "producer R3 condition" wording was not operational.

All four were remediated in-plan: Contract Shape (URL plus contract-ID citation rule, R3
operationalized), U2 (manifest entry), and U3 (no P-002.7 anchor or heading copies).

### Review attempt 2 (2026-10-08T22:00Z)

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`

dispatch_mode: single-agent-declared-degradation
decision: PASS

**Gate rationale:** no P0, P1, or P2 findings remain. Hardening was required (P-006) and is
satisfied: the `## Plan Hardening` section is present, with protected invariants,
ProposedAction/ActionRisk entries, rollback, and an operator checkpoint. `strict-safety` is not
installed, so the classification is advisory. Runtime verification and closure are covered per
unit, and the operator-only attestation (PA4) is fenced out of agent scope.

| Persona | Mode | Result |
|---|---|---|
| Constitution Reviewer | inline (declared degradation) | Remediated P1-1. Stage boundary respected. Dogfood parity and the canonical test gate are cited per unit. |
| Python Reviewer | inline | P3-1 |
| Scope Boundary Auditor | inline | P3-2. Option A and L3 correctly excluded. U5 justified as required for M3 decidability. |
| Learnings Researcher | inline | Claim-cascade (P-002.7 basis) and checksum learnings applied. No contradiction with past resolutions. |
| Architecture Strategist | inline (anchor route unavailable, same-model) | Remediated P1-1 and P2-3. Single sourcing via rule IDs and a version bump is sound. |
| Agent-Native Parity Reviewer | inline (triggered: Ship agent behavior) | P3-3 |
| Security Lens Reviewer | inline (triggered: cross-workspace contract, raw log reads) | H2 path containment and the P-012 declaration are adequate. No secrets surface. |

**P3 (advisory):**

* **P3-1:** the U6 evaluator should treat both `done` and `archived` as `terminal_success`.
  Break ties among ready members by manifest order for determinism. Use type-hinted pure
  functions in the test module.
* **P3-2:** U3, U4, and U5 each touch four files (template, mirror, manifest, test), which
  exceeds the literal "fewer than 3 files" heuristic. This is the accepted repository precedent
  for one logical template change with dogfood parity. Each unit remains under two hours.
* **P3-3:** no backlog-tool operation returns an item's event stream, so the P-012-declared raw
  log read is the only path. If backlogit adds an event-stream read, a later contract revision
  can drop the raw read without a version bump to M3 semantics.

**Harvest readiness:** PASS. Harvest one feature and seven tasks (U1–U7). Chain the shipment
after `211-S` with a `blocks` edge.
