---
title: "Remove the agent-intercom capability pack (full product removal plus dogfood removal)"
description: "Implementation plan for retiring the agent-intercom capability pack from the autoharness product (templates, registry, schemas, verify/tune/install logic, tests, docs) and from this repository's own installed harness, with graceful legacy-profile tolerance. Stash 0FD06900. Chained after 215-S."
date: 2026-10-14
status: reviewed
deliberation: "none - the only open question (dogfood-only disable vs full product removal) was resolved by the operator via the Orchestrator on 2026-10-13/14 (UTC): full removal. Decisions are recorded in this plan (see Decisions and Rationale)."
stash_entries: [0FD06900]
requires_plan_hardening: "yes"
plan_hardening_status: "hardened"
plan_review_verdict: "PASS"
plan_review_cycles: 2
tags: [plan, capability-pack-removal, agent-intercom, schema-versioning, legacy-tolerance, dogfood-parity, manifest-checksums]
---

## Problem Frame

The operator no longer uses the `agent-intercom` capability pack ("too cumbersome ... I have better
options now"). Resolved scope (operator decision relayed by the Orchestrator): **full removal of the
pack from the autoharness PRODUCT and from the dogfood harness's installed mirrors** - not a
dogfood-only disable. The pack is not replaced; backlogit, agent-engram, graphtor-docs and the base
primitives must keep working with no dangling references.

Footprint (re-surveyed 2026-10-14 with `git grep -i intercom`, excluding `references/` and
historical record directories): ~210 tracked files outside `references/`/`docs/archive`/
`.backlogit/archive`/`docs/memory`/`docs/reviews`/`docs/research`/`docs/spikes`, of which roughly
95 are LIVE/NORMATIVE surfaces that must change; the rest are historical records that must NOT be
rewritten (`.backlogit/**` operational state, `docs/decisions/**`, `docs/plans/**`, `docs/closure/**`,
`docs/exec-plans/**`, `docs/bugs/**`, `docs/audits/**`, `docs/compound/**`, dated memory, CHANGELOG
historical entries).

Live surfaces by family (template file + installed mirror counted together because the repo carries
template-vs-dogfood parity tests):

| Family | Template side | Installed / live side |
|---|---|---|
| Pack definition | `templates/packs/capability-pack-registry.yaml` (6 lines), `templates/instructions/agent-intercom.instructions.md.tmpl` | `.github/instructions/agent-intercom.instructions.md`, `schemas/capability-pack-registry.schema.json` |
| Schemas (enum + profile block) | - | `schemas/workspace-profile{,/1.0.0}.schema.json`, `schemas/harness-manifest{,/1.0.0,/0.9.0}.schema.json`, `schemas/harness-config{,/0.9.0,/1.0.0,/1.1.0}.schema.json`, `schemas/workspace-profile/0.9.0.schema.json` |
| Verify / contracts | - | `src/autoharness/verify_workspace.py` (11), `src/autoharness/schema_contracts.py` |
| Agents | `_orchestrator` (12), `_ship` (30), `_stage` (13) `.agent.md.tmpl` | `.github/agents/_orchestrator|_ship|_stage.agent.md`, `auto-mergeinstall.agent.md` |
| Foundation | `AGENTS.md.tmpl`, `copilot-instructions.md.tmpl`, `constitution.instructions.md.tmpl` | root `AGENTS.md`, `.github/instructions/constitution.instructions.md`, `harness-architecture.instructions.md`, `.github/copilot-review-instructions.md` |
| Instructions | `backlogit`, `circuit-breaker`, `concurrency`, `role-enforcement`, `strict-safety` `.instructions.md.tmpl` | matching `.github/instructions/*.md` mirrors |
| Policies | `templates/policies/workflow-policies.md.tmpl` | `.github/policies/workflow-policies.md` |
| Skills | 17 skill templates (brainstorm, build-feature, compact-context, deliberate, doc-review, fix-ci, harness-architect, harvest, impl-plan, operational-closure, plan-harden, plan-review, pr-lifecycle, review, runtime-verification, safety-modes, shipment-reconcile) | 13 installed mirrors plus global-only skills `install-harness` (36), `workspace-discovery` (11), `tune-harness` (4), `verify-harness` (2), prompt `install-harness.prompt.md` |
| Dogfood install state | - | `.autoharness/config.yaml`, `.autoharness/workspace-profile.yaml`, `.autoharness/harness-manifest.yaml` (pack list, overlay record, artifact record, checksums) |
| Docs | - | `README.md`, `docs/capability-packs.md`, `getting-started.md`, `tuning-guide.md`, `primitives.md`, `docs/telemetry/{backlogit-evidence-map,backlogit-sensitivity-guardrails,cross-pack-adapter-gap-report}.md`, `docs/deferred/agent-intercom-opt-in-nonmcp.{md,patch}`, `CHANGELOG.md` (new entry only) |
| Tests | - | `test_capability_pack_registry`, `test_deploy_harness_scripts`, `test_graphtor_docs_full_suite`, `test_verify_workspace` (4 files name the pack) |
| Telemetry vocabulary | - | `route_kind: "intercom"` in `schemas/execution-epoch*`, `schemas/tool-telemetry-event*`, `src/autoharness/telemetry/tool_event.py` (retained, see D-6) |

Important structural facts established during planning:

* `install`, `discover`, `tune`, `verify-harness` are **skills** (markdown) - only `verify_workspace.py`
  and `schema_contracts.py` carry executable pack logic (`SUPPORTED_CAPABILITY_PACKS`,
  `PACK_ASSERTIONS["agent-intercom"]`, the `dark_factory_intercom_contract` check, the
  `copilot_remote_operator_guidance` check).
* The agent-intercom overlay instruction is currently the **only home** of the Dark Factory
  Visibility Protocol event table (`DARK_MODE_START` ... `DARK_MODE_COMPLETE`) and the "Combined Rule
  for backlogit-enabled staging". Those are normative operator-visible behaviors that must survive
  removal (relocated, not deleted).
* The repo already has a legacy-pack degradation mechanism
  (`LEGACY_UNSUPPORTED_PACKS = {"circuit-breaker", "concurrency"}` -> warning
  `legacy-{kind}-capability-pack` + migration proposals) which this plan extends instead of
  inventing a second one.
* `verify_workspace(_REPO_ROOT, _REPO_ROOT)` runs against the live dogfood tree inside the unit
  suite (`test_dogfood_ship_route_pin`, `test_template_variable_derivation_contract`, ...), and
  several tests assert template-vs-installed byte parity. Template and mirror therefore change in
  the **same task** (width exception to "single layer" recorded in D-12).

## Requirements Trace

| # | Requirement (operator + Stage constraints) | Unit(s) |
|---|---|---|
| R1 | Remove the pack from templates, registry, install/discover/tune/verify logic, schemas, tests, docs | U2-U4, U6-U7, U9-U22 |
| R2 | Remove the pack from the dogfood installed mirrors, manifest and workspace profile | U8, U9-U22 |
| R3 | Other packs and base primitives keep working; no dangling references | U1 (guard), U23 (final proof) |
| R4 | Historical records are NOT rewritten (archive, memory, reviews, dated plans/decisions, research, spikes, CHANGELOG history) | U1 allowlist, U19 (CHANGELOG new entry only), U23 |
| R5 | Legacy profile/manifest/config listing `agent-intercom` must not crash verify/tune; explicit deprecation path; schema no longer lists it for new documents | U2-U4, U6, U18, U21 (D-2, D-3) |
| R6 | P-005/P-010 violation text, output-timestamps, circuit-breaker stall rule, dark-factory visibility events, Combined Rule remain coherent | U5, U9, U11-U13 (D-4) |
| R7 | Manifest/checksum refresh and removal of the installed instruction file | U8, U9-U22, U23 (D-14) |
| R8 | Deferred doc disposition decided | U20 (D-5) |
| R9 | Tests: remove/update pack-exists tests; add no-live-reference guard; add legacy-tolerance tests | U1, U6, U7, U21, U22, U23 |
| R10 | 2-hour rule, tests-first, repo green after each task, explicit dependencies | Dependency Graph |

## Decisions and Rationale

**D-1 Scope = full product removal + dogfood removal; no deliberation artifact.** The only open
design question (dogfood-only vs full) was decided by the operator. Every other question is
answered below with repo evidence, so `deliberate` is not invoked (Stage Step 2 allows recording
decisions in the plan when no genuinely open question remains).

**D-2 Schema versioning: bump, never mutate a published mirror.** Removing an enum value is a
restrictive contract change. `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`
and `2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md` record three prior
incidents of in-place mutation of published mirrors; `schema_contracts.py` documents mirrors as
"pinned, immutable snapshots". Therefore:
* `workspace-profile` 1.0.0 -> **1.1.0**: new `schemas/workspace-profile/1.1.0.schema.json`; root
  schema tracks it; `agent-intercom` removed from both pack enums and the `agent_intercom` property
  removed. `harness-manifest` 1.0.0 -> **1.1.0** (both pack enums). `harness-config`
  -> **next version after the then-current one** (see below), `agent-intercom` removed from the enum.
* `0.9.0` / `1.0.0` / `1.1.0` published mirrors stay **byte-identical** (byte-pin tests, mirroring
  the existing 1.0.0 restore pattern). A legacy document pinned to a frozen version keeps validating
  against the contract it was written against - this is the primary backward-compatibility path and
  needs no code.
* `harness-config` version collision: shipment 215-S (feature 208-F, queued) already claims config
  **1.2.0** (208.005-T mirror, 208.006-T atomic cut-over). This shipment therefore MUST ship after
  215-S and mint `current_version + 1` (expected **1.3.0**), read from
  `SCHEMA_CONTRACTS["config"]` at claim time rather than hard-coded. Recorded as a shipment-level
  `blocks` edge (D-11).
* `schemas/capability-pack-registry.schema.json` has no versioned mirror set (it describes the
  autoharness-home registry, not an installed document) and is edited in place.

**D-3 Legacy tolerance (profile/config/manifest listing `agent-intercom`).** Extend, do not fork,
the existing mechanism:
1. `schema_contracts.py` gains `REMOVED_CAPABILITY_PACKS = {"agent-intercom": {...removal metadata...}}`
   and `agent-intercom` joins the set consulted by `classify_schema_error`, so a document that
   claims a CURRENT schema version yet lists the pack degrades to a warning, not a strict blocker.
2. A new collector in `collect_contract_state_warnings` emits one warning kind
   `removed-capability-pack` (fields: `field`, `legacy_value`, `message`, `suggested_action`) for a
   pack listed in `capability_packs`, in `capability_pack_overlays[*].pack`, in
   `harness_recommendations.capability_packs`/`recommendation_reasons[*].item`, and for a leftover
   profile `agent_intercom` block - **independent of the document's pinned version** (a 1.0.0
   document validates cleanly, so schema errors alone would never flag it). Warnings are deduped by
   (path, field, value) against the schema-error path.
3. `SUPPORTED_CAPABILITY_PACKS` drops the pack; `installed_packs` therefore ignores it; no pack
   assertion runs for it; verify never crashes and never blocks on it.
4. A migration proposal `remove-retired-capability-pack` (per contract kind) tells the operator to
   remove the entry and, when `.github/instructions/agent-intercom.instructions.md` exists, to delete
   it only if its checksum still matches the manifest record (a modified file is `manual_review: true`
   - never auto-deleted).
5. Skills: `tune-harness` reports the retired pack as a drift category ("retired capability pack"),
   offers cleanup (remove list entry, overlay record, orphan instruction file under the checksum
   rule, stale woven sections), and never re-weaves it; `install-harness`/`workspace-discovery`
   stop detecting/recommending it and, when an operator passes `capability_packs=agent-intercom`,
   warn `RETIRED_PACK: agent-intercom ignored` and continue. `scripts/deploy-harness.{sh,ps1}`
   (and their templates) behave the same way instead of the current hard `Unknown pack` failure.
6. Already-installed workspaces keep their old rendered text mentioning intercom until the operator
   runs tune; that text is inert prose, so no behavior breaks.

**D-4 Coherence of the surfaces the operator named.**
* *P-005/P-010 violation broadcast text and "broadcast" phrasing generally.* Rule used by every
  sweep: a sentence "When the `agent-intercom` capability pack is installed, broadcast X" is
  (a) **deleted** when X is progress chatter or a pure intercom protocol step (heartbeat, ping,
  `[SHIP] Starting execution workflow`, auto-check, transmit/standby waits); (b) **kept but made
  unconditional and re-targeted to session output** ("report X in the session output / PR or
  closure summary") when X is a normative operator-visible event: policy-violation events
  (P-005/P-010/P-016/P-017 etc., the Step 3.0 gate-bypass halt), `DARK_MODE_*` events, gate
  verdicts the operator must act on, and operator-choice presentations. P-005 telemetry recording
  is unchanged.
* *Output timestamps.* `.github/instructions/output-timestamps.instructions.md` is already universal
  (it does not mention intercom) and is unchanged; only its reference from the overlay disappears.
  The `test_verify_workspace` phrase test drops its two overlay entries.
* *Circuit-breaker stall rule.* Item 4 ("An agent-intercom heartbeat ping fails (when the pack is
  enabled)") is deleted with no replacement; the remaining three stall triggers and the stall
  limit are unchanged (the heartbeat concept no longer exists).
* *Dark-factory visibility.* The events `DARK_MODE_START`, `DARK_MODE_SCOPE`,
  `BRAINSTORM_HANDOFF_READY`, `LOCAL_REVIEW_READY`, `DARK_MODE_MERGE_AUTHORIZED`,
  `ADMIN_FALLBACK_ATTEMPTED`, `DARK_MODE_HALTED`, `DARK_MODE_COMPLETE` and their required-content
  table are relocated verbatim into the P-017 section of `workflow-policies.md(.tmpl)` as the
  "Dark Factory Visibility Protocol", expressed as operator-visible session-output summaries with
  zero intercom dependency. The `degraded-visibility` token and rule are retained, re-worded for a
  generic reporting surface (if the required reporting surface is unavailable: record a
  degraded-visibility warning in the local session/PR summary and continue only with safe,
  non-destructive work; destructive actions, scope expansion, admin fallback, failed local
  readiness, secrets-exposure risk and ambiguous branch-protection state halt). The orchestrator
  `visibility_mode` field keeps its meaning minus the intercom wording. The verify check
  `dark_factory_intercom_contract` is replaced by `dark_factory_visibility_contract` targeting
  `.github/policies/workflow-policies.md` (U5 adds it; U7 retires the old one).
* *Combined Rule for backlogit-enabled staging.* Preserved as an **Operator Choice Presentation Rule**
  in `backlogit.instructions.md(.tmpl)` (replacing "Intercom Coherence Rule") and in the Stage
  agent: when presenting stash/queue/backlog choices, make the session-output message
  self-contained - item ID, priority, kind/type, one-line summary, recommended ordering, explicit
  "operator selection/confirmation awaited" - because the operator may read asynchronously.
* *Clarification / wait flow (review finding F9).* The intercom transmit/standby steps are replaced
  by a channel-neutral rule: when blocked on operator intent, approval or a handoff decision,
  state the question, the options and the decision required in the session output and STOP
  (halt/wait) until the operator replies; never proceed on an assumed answer. Ship's `[WAIT]
  Awaiting user merge approval` notice and Stage's operator-selection prompts use this rule.
* *Destructive-operation approval.* The intercom auto-check/approval step disappears. Destructive
  actions follow the workspace's native approval path (`strict-safety` classification when that pack
  is installed, otherwise local confirmation per AGENTS.md safe-operations). No replacement remote
  channel is introduced.

**D-5 `docs/deferred/agent-intercom-opt-in-nonmcp.{md,patch}`: DELETE both files.** The md already
states `Status: shipped` (PR #253, shipment 101-S / 096-F) and says it is "retained for historical
reference"; the patch targets files this removal deletes or rewrites, so it can no longer be
applied and would only mislead; git history and PR #253 preserve the record, and a `Superseded`
banner would leave a live-looking operational recipe (apply this patch / refresh these checksums)
in `docs/deferred/`. `docs/audits/2026-08-15-...inventory.md` (dated audit) keeps its historical
mention. A one-line tombstone goes in the CHANGELOG entry.

**D-6 Telemetry `route_kind: "intercom"` is retained.** It is a vocabulary value of two **versioned
published contracts** (`execution-epoch` 1.1.0, `tool-telemetry-event` 1.0.0/1.1.0) and of
`tool_event.py`'s well-known set; removing it would make already-recorded journals invalid or
force a contract bump with no operator benefit (the `x-*` extension escape hatch already exists for
any future route). It is a historical-event vocabulary, not a pack reference, and is allowlisted
(with rationale) in the guard test. Revisit only if those contracts are bumped for another reason.

**D-7 Deploy wrapper opt-in mechanism stays.** The `default_in_preset` omitted-vs-explicit-`all`
precedence is generic and has other users; only the real-registry assertions that name
`agent-intercom` change (after removal every remaining pack defaults into `full`). The wrappers'
hard `Unknown pack` failure becomes warn-and-skip for retired IDs (D-3.5).

**D-8 `## Remote Operator Integration` heading in `copilot-instructions.md.tmpl` is retained** (its
remaining content is the agent-engram subsection). Renaming it would make already-installed
workspaces (which carry the old heading) fail `copilot_remote_operator_guidance` - contradicting
the legacy-tolerance requirement. The verify check keeps requiring
`## Remote Operator Integration`, `### agent-engram`, `sync_workspace` and simply stops requiring
`### agent-intercom`; a rename is a future, separately-migrated change (P3 note).

**D-9 Historical allowlist (guard test).** Excluded from the "no live reference" scan:
`references/**`, `.backlogit/**` (archive, checkpoints, logs, stash, memories - operational/historical
state; the new stash entry text legitimately names the pack), `docs/archive/**`, `docs/memory/**`,
`docs/reviews/**`, `docs/research/**`, `docs/spikes/**`, `docs/decisions/**`, `docs/plans/**`,
`docs/closure/**`, `docs/exec-plans/**`, `docs/bugs/**`, `docs/audits/**`, `docs/compound/**`,
`docs/design-docs/**` (dated), and `CHANGELOG.md`. `tests/**` is NOT blanket-excluded (that would
hide stale or newly introduced live test assumptions about the removed pack): U1 enumerates the
test files/cases that reference the retired value today and the guard allowlists ONLY those exact
`tests/<file>` paths, each with a required rationale (tolerance/migration proof, retired-value
wrapper test, or the guard's own fixtures; the existing tests that merely ASSUME the pack exists
are rewritten by U2/U6/U7/U21/U22 and drop off the list). Unrelated test references therefore
fail the guard as intended. FROZEN published mirrors (`schemas/harness-config/{0.9.0,1.0.0,1.1.0}`,
`schemas/harness-manifest/{0.9.0,1.0.0}`, `schemas/workspace-profile/{0.9.0,1.0.0}`) and the
telemetry vocabulary files (D-6) are allowlisted by exact path. A small TOMBSTONE allowlist (exact
path + required rationale string) covers the files that must name the retired value to handle it:
`src/autoharness/schema_contracts.py`, `src/autoharness/verify_workspace.py` (retired-pack constant),
`.github/skills/tune-harness/SKILL.md`, `.github/skills/install-harness/SKILL.md`,
`.github/skills/workspace-discovery/SKILL.md`, `scripts/deploy-harness.{sh,ps1}` and
`templates/scripts/deploy-harness.{sh,ps1}.tmpl`, `docs/capability-packs.md` (a "Retired packs"
section), `docs/tuning-guide.md`, and the `docs/telemetry/*` deferral-closure note. Every tombstone
entry must name its reason; the guard fails on an allowlist entry that no longer matches anything
(prevents silent growth).

**D-10 Operator-owned config.** `.autoharness/config.yaml` is operator-owned; the operator has
explicitly directed this removal, so U8 edits ONLY the `capability_packs` list entry. It does NOT
bump the file's `schema_version` (a frozen-version config keeps validating, and the 215-S cut-over
carries its own operator-confirmed marker for config version moves - this shipment must not
pre-empt or disturb it); adopting the new config version stays a tune/operator action. U8 refreshes
the manifest `config_hash` + checksum for the one-key diff. Ship re-confirms the operator
authorization at claim time (quoted in the U8 task description) and halts if it cannot.

**D-11 Shipment sequencing.** One shipment; feature first, tasks in the linear dependency order
below; shipment status `queued`; a single `blocks` edge **215-S -> this shipment** (this shipment
waits for 215-S). Reasons (real conflicts, not preference): (a) `harness-config` contract version
slot 1.2.0 is claimed by 208.005/208.006 (D-2); (b) `verify_workspace.py` and `schema_contracts.py`
are rewritten by 207-F/208-F (resolver delegation, catalog/binding checks, 1.2.0 cut-over);
(c) the same shipment edits `tune-harness`, `install-harness`, `workspace-discovery` skills and
`workflow-policies` that 208.010-T/011-T/012-T/014-T also edit. 211-S..215-S themselves are NOT
modified and do not depend on this shipment. Ship must re-read the post-215-S baseline for the
shared files at claim time (line numbers in this plan are advisory).

**D-12 Sweep by FILE FAMILY, not by layer.** Template, installed mirror and the mirror's manifest
checksum change in one task, because parity tests (`test_template_and_dogfood_are_parity_drift_free`,
circuit-breaker contract byte-identity, copilot-code-review parity, capability-pack-enforcement
parity) and the in-suite dogfood `verify_workspace` run would otherwise go red between tasks.
Mirrors are edited in place (NOT re-rendered): several mirrors intentionally retain pre-existing
drift from their templates (see manifest notes), and a re-render would also change unrelated text.

**D-13 Green-after-each-task ordering.** (1) U1 lands a guard whose PENDING ledger lists every
not-yet-swept surface; each later task removes exactly its own surfaces from the ledger; U23 asserts
the ledger is empty. (2) Verify-side assertion retirement (U7) and dogfood pack disable (U8) land
BEFORE content sweeps so content removal never trips a pack assertion; the overlay instruction file
and its registry/manifest-artifact records are deleted LAST (U22) so no earlier sweep leaves a
manifest entry pointing at a missing template.

**D-14 Manifest checksum procedure.** Per `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`:
compute SHA-256 over LF git-blob bytes via a direct subprocess capture
(for a file edited in the current task run `git add --renormalize <path>` and read the INDEX blob
`git cat-file blob :<path>`; `HEAD:<path>` is the pre-task blob for such a file and would write the
OLD checksum, so reserve `HEAD:<path>` for unchanged baseline evidence only), read as bytes, never
via a PowerShell redirect or working-tree read. Refresh only checksums of files THIS task edited; never refresh a pre-existing
stale entry to quiet a warning (`docs/compound/2026-08-15-checksum-drift-fix-...`). Keep manifest
`note:` additions to one short clause.

**D-15 Size/complexity** are assigned per unit below as two independent axes (size = effort/volume,
complexity = difficulty/uncertainty); no unit is `complexity: high`.

## Implementation Units

Unit labels `U1..U23` map to backlog tasks at harvest. Each unit: single concern, verifiable exit,
full suite green (`PYTHONPATH=src python -m unittest discover -s tests`) before the task closes.
File counts exceed the "<3 files" guideline only for mechanical sweeps, split by family so each
stays within 2 hours (Requirement R10, shaping rule noted in the harvest brief).

### U1 - Guard test with shrinking pending ledger (tests-first)
* Posture: test-first. Size S / complexity low.
* Files: new `tests/test_removed_pack_surface_guard.py` (1).
* Content: `HISTORICAL_ALLOWLIST` (D-9), `FROZEN_MIRRORS`, `TELEMETRY_VOCAB`, `TOMBSTONES` (path ->
  rationale), and `PENDING_SURFACES` (path prefixes still containing the pack, initial = all live
  surfaces from the footprint table). The scan reads bytes and decodes with `errors="ignore"`,
  skipping binary files, so CRLF/encoding differences never create false matches. `tests/**` is not
  blanket-excluded: the guard allowlists only the exact test files that intentionally name the
  retired value (enumerated here by grep at U1 time), each with a rationale. Tests: (a) every live file containing `intercom` (case-insens.)
  not covered by an allowlist is listed in `PENDING_SURFACES`; (b) every `PENDING_SURFACES` entry still
  matches something (stale entries fail, forcing removal as work lands); (c) allowlist/tombstone
  entries must exist and carry rationale; (d) the empty-ledger assertion is guarded by a module
  constant `LEDGER_ENFORCED = False` that U23 flips to `True`. Scan via `git ls-files` so untracked scratch never counts.
* Verify: suite green; deliberately adding the word in a new live file fails (a).

### U2 - workspace-profile schema 1.1.0
* Posture: migration-first. Size M / complexity medium.
* Files: `schemas/workspace-profile.schema.json`, new `schemas/workspace-profile/1.1.0.schema.json`,
  `src/autoharness/schema_contracts.py`, tests (`tests/test_schema_contract_removed_pack_profile.py`
  new; adjust any hard-coded profile `1.0.0` assertions).
* Remove `agent-intercom` from both pack enums and delete the `agent_intercom` property in
  root + 1.1.0; leave `0.9.0`/`1.0.0` byte-identical (byte-pin test via `git show` of the pre-change
  blob hash recorded in the test). `SCHEMA_CONTRACTS["profile"]`: `current_version "1.1.0"`,
  `known_versions ("0.9.0","1.0.0","1.1.0")`; add `1.0.0 -> 1.1.0` `CONTRACT_MIGRATIONS` entry.
* The profile schema root has no top-level `additionalProperties: false`, so after the property is
  deleted a profile carrying an `agent_intercom` block still VALIDATES (the key is simply an
  unknown, ignored property). Decision: do NOT close the root (that would reject every unknown
  top-level key and needs a separate compatibility audit); the legacy block is detected and warned
  on directly by the U6 collector, not through a schema error.
* Verify: legacy 1.0.0 profile with the pack still validates; a 1.1.0 profile listing the pack in
  `harness_recommendations.capability_packs` fails the enum (classified as a warning in U6); a
  1.1.0 profile carrying only an `agent_intercom` block still validates (test pins this open-root
  behavior).
* Retarget the "current-version" proposals: changing `current_version` to `1.1.0` leaves the
  rules that hard-code the old current target stale (`backfill-profile-schema-version` and
  `review-unknown-profile-contract` in `schema_contracts.py` still point `to_version`/`action` text
  at `1.0.0`; the `normalize-legacy-profile-*` rules likewise). U2 retargets every profile rule
  whose purpose is "move to the current contract" to `1.1.0` (including the action text), keeps the
  `0.9.0 -> 1.0.0` upgrade entry as a historical step, and adds tests asserting the proposal
  payloads (`to_version` and action text) for the missing-version and unknown-version cases.

### U3 - harness-manifest schema 1.1.0
* Posture: migration-first. Size S / complexity medium. Depends on U2 (shared `schema_contracts.py`).
* Files: `schemas/harness-manifest.schema.json`, new `schemas/harness-manifest/1.1.0.schema.json`,
  `schema_contracts.py`, test (extend/duplicate U2's pattern; `tests/test_manifest_capability_pack_enum.py` adjust).
* Same pattern: both enums (top-level `capability_packs`, `capability_pack_overlays[*].pack`).
* Retarget the manifest's current-version proposals (missing-version backfill, unknown-version
  review, and any other rule whose `to_version`/action text names the old current contract) to
  `1.1.0`, with proposal-payload tests, exactly as in U2.

### U4 - harness-config next-version schema (after 215-S)
* Posture: migration-first. Size M / complexity medium. Depends on U3; shipment blocked-by 215-S.
* Files: `schemas/harness-config.schema.json`, new `schemas/harness-config/<N+1>.schema.json`
  (expected 1.3.0), `schema_contracts.py`, `templates/harness-config.yaml.tmpl` (schema_version pin),
  tests.
* `<N+1>` is derived at claim time from `SCHEMA_CONTRACTS["config"]["current_version"]`; the
  published `0.9.0/1.0.0/1.1.0` (+ `1.2.0` if 215-S has landed) mirrors stay byte-identical with
  byte pins; add `N -> N+1` migration entry. Tests that hard-code mirror paths were made
  version-agnostic by 208.003/208.004 - if not, fix them here, never by editing a frozen mirror.
* Verify: a config pinned to the previous version listing the pack still validates.
* Retarget the config's current-version proposals (missing-version backfill, unknown-version
  review, and any rule whose `to_version`/action text names the previous current version) to
  `<N+1>`, with proposal-payload tests, exactly as in U2.

### U5 - Relocate Dark Factory Visibility Protocol and violation-report text into the policy
* Posture: test-first (new verify check + test, then text). Size M / complexity medium.
* Files: `templates/policies/workflow-policies.md.tmpl`, `.github/policies/workflow-policies.md`,
  `src/autoharness/verify_workspace.py` (ADD `dark_factory_visibility_contract` targeting the policy
  mirror with `must_contain` = `Dark Factory Visibility Protocol`, `BRAINSTORM_HANDOFF_READY`,
  `DARK_MODE_COMPLETE`, `degraded-visibility`; keep the old check for now), test additions.
* P-017 section gains the relocated events table (D-4); policy lines that say "when `agent-intercom`
  is installed ... / intercom degraded or unreachable" (templates ~L205-209 G1/G3 channel text,
  ~L380, ~L666-668) are re-worded to channel-neutral language (G3 "no independent approval channel
  available" semantics unchanged); P-005/P-010 violation wording says "report in the session output
  and record via P-005 telemetry". Refresh the mirror's manifest checksum.

### U6 - verify_workspace: legacy tolerance for the retired pack
* Posture: test-first (new `tests/test_removed_pack_legacy_tolerance.py`). Size M / complexity medium.
* Files: `src/autoharness/schema_contracts.py` (collector + `REMOVED_CAPABILITY_PACKS` + migration
  rule + `classify_schema_error` extension), `src/autoharness/verify_workspace.py` (installed-pack
  filter message), new test file.
* Tests: (a) manifest/config/profile at frozen versions listing the pack -> no crash, no blocker,
  warning `removed-capability-pack`; (b) same at the CURRENT version -> schema error classified as
  warning (not `strict_schema_blocker`); (c) legacy `agent_intercom` profile block and overlay record
  tolerated; (d) proposal `remove-retired-capability-pack` present, `manual_review` true when the
  overlay file checksum differs; (e) mixed legacy+supported packs: supported packs still verified.
* Note: at this point the pack is still in `SUPPORTED_CAPABILITY_PACKS` (retired in U7), so (e) is
  written against the final behavior with the constant monkeypatched until U7.
* Regex coverage: `LEGACY_CAPABILITY_PACK_ERROR_RE` today matches `capability_packs.N` /
  `capability_pack_overlays.N.pack` only; U6 extends it (or adds a sibling pattern) for
  `recommendation_reasons.capability_packs.N.item`, tested. The root-level `agent_intercom`
  property needs no matcher: the profile root is open (see U2), so no schema error exists for it;
  instead the U6 collector detects a legacy `agent_intercom` profile block directly (by key
  presence) and emits the `removed-capability-pack` warning, tested per case (c).

### U7 - verify_workspace: retire the pack assertions and fixtures
* Posture: characterization-first. Size M / complexity medium.
* Files: `src/autoharness/verify_workspace.py`, `tests/test_verify_workspace.py` (+ guard ledger).
* Remove `agent-intercom` from `SUPPORTED_CAPABILITY_PACKS`, delete `PACK_ASSERTIONS["agent-intercom"]`
  (incl. `review_intercom_workflow`), delete `dark_factory_intercom_contract`, drop `### agent-intercom`
  from `copilot_remote_operator_guidance` (D-8). In `test_verify_workspace.py` remove the
  overlay-template/mirror phrase entries (L897-905), rewrite fixtures that used `agent-intercom` as
  the only enum member (L948, L1105, L1510-1517, L2027-2054, L2116) to use another real pack or the
  retired value as an explicit legacy case, and fix the message string at L7000.
* Verify: dogfood `verify_workspace` shows only the expected `removed-capability-pack` warnings (the
  dogfood install still lists the pack until U8) and 0 blockers.

### U8 - Dogfood install state: disable the pack
* Posture: migration-first. Size S / complexity medium. Operator-owned file (D-10).
* Files: `.autoharness/config.yaml` (remove the list entry ONLY; no schema_version bump - D-10),
  `.autoharness/workspace-profile.yaml`
  (remove from `harness_recommendations.capability_packs`/reason/`agent_intercom` block; bump
  `schema_version` to 1.1.0), `.autoharness/harness-manifest.yaml` (remove from `capability_packs`,
  `capability_pack_overlays`, bump `schema_version` to 1.1.0, refresh `config_hash` + config checksum).
  The overlay ARTIFACT record and the file itself stay until U22 (D-13).
* Verify: dogfood verify has 0 blockers and no `removed-capability-pack` warning for these three
  documents; `git diff .autoharness/config.yaml` is exactly one removed line (route/`context_tier`
  markers untouched).

### U9 - Instruction family sweep
* Posture: characterization-first. Size M / complexity low.
* Files: templates + mirrors for `circuit-breaker` (delete stall rule item 4), `concurrency`
  (L19), `role-enforcement` (L74 - violation report text per D-4), `strict-safety` (L60),
  `backlogit` (Intercom Coherence Rule -> Operator Choice Presentation Rule). 10 files, ~1-5 line
  edits each. Refresh the 5 mirror checksums.

### U10 - Foundation family sweep
* Size M / complexity low.
* Constitution amendment compliance (found in plan review, finding F1): the constitution's
  Governance section requires "a version bump, rationale, and sync impact report" for any
  amendment, and removing the `agent-intercom` bullet from `## Capability Overlays` is an
  amendment. U10 therefore also bumps `**Version**: 1.0.0` -> `1.1.0` in BOTH the template and the
  installed mirror and adds a new dated sync-impact report
  `docs/design-docs/2026-10-14-constitution-1-1-0-agent-intercom-removal-sync-impact.md` (rationale =
  stash 0FD06900 operator decision; impacted surfaces = this plan's family table; no principle I-XI
  changes - Principle VII destructive-command approval is intercom-independent and unchanged). The
  P-005 "MUST broadcast a P-005 event and halt" sentence becomes "report a P-005 event in the
  session output and halt" (D-4).
* Files: `templates/foundation/{AGENTS,copilot-instructions,constitution.instructions}.md.tmpl`,
  root `AGENTS.md` (pack table row), `.github/instructions/constitution.instructions.md`,
  `.github/instructions/harness-architecture.instructions.md`, `.github/copilot-review-instructions.md`
  (+ `.github/copilot-instructions.md` if it carries the sections). Remove the "Capability Overlay -
  agent-intercom" sections and the intercom rows/clauses (AGENTS.md.tmpl L78-88, L197, L200, L313;
  constitution L104-112; copilot-instructions L100-109, L197-204 -> D-8). Refresh checksums.

### U11 - Orchestrator agent
* Size M / complexity medium (dark-mode visibility semantics).
* Files: `templates/agents/_orchestrator.agent.md.tmpl`, `.github/agents/_orchestrator.agent.md`.
  Delete per-step broadcast sentences (L281, L299, L328, L374, L394, L404, L412), the
  `## Remote Operator Integration (agent-intercom)` section, re-word `visibility_mode` and the
  DARK_MODE_START/SCOPE activation paragraph to session-output summaries (D-4). Refresh checksum.

### U12 - Ship agent
* Size M / complexity low (30 + 10 hits, repetitive).
* Files: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`. Apply the D-4
  rule (a)/(b): the Step 0 startup protocol (L138-142), per-step broadcasts, `[WAIT] Awaiting user
  merge approval` becomes an unconditional operator-visible wait notice, claim-verify sentence
  (L274), closure/index-sync warnings (`CLOSURE_INDEX_SYNC_WARN` stays as a logged token), the
  `## Remote Operator Integration (agent-intercom)` section, and the concurrency note (L64).

### U13 - Stage agent
* Size M / complexity medium.
* Files: `templates/agents/_stage.agent.md.tmpl`, `.github/agents/_stage.agent.md`. Remove Step 0.1c
  (Intercom Startup Ping) and its "before presenting choices / before destructive operations"
  paragraphs (replace with the Operator Choice Presentation Rule and native-approval sentence),
  L94 concurrency note, L212-214 startup protocol, L272 combined rule, L397 grouping broadcast,
  L677-730 broadcasts, `## Remote Operator Integration (agent-intercom)` section, L812-814 combined
  rule tail; the Step 3.0 gate-bypass halt becomes "report a P-005 violation in the session output".
  Keep the step-sequence checklist intact (renumber nothing other than dropping the 0.1c line).

### U14 - Planning-phase skills
* Size M / complexity low.
* Files: skill templates + mirrors for `brainstorm`, `deliberate`, `doc-review`, `harvest`,
  `impl-plan`, `plan-harden`, `plan-review` (7 templates + 5 mirrors; brainstorm/doc-review mirrors
  may not exist). Remove the "Agent-Intercom Communication" tables and "Required Protocol" intercom
  paragraphs; the P-012 capability list in plan-review ("intercom visibility") drops that item.
  Refresh mirror checksums.

### U15 - Execution-phase skills A
* Size M / complexity low.
* Files: `build-feature`, `fix-ci`, `compact-context`, `pr-lifecycle`, `review` templates + mirrors.
  The `review` skill's "Agent-Intercom Communication (NON-NEGOTIABLE)" section is removed together
  with its (already retired in U7) ordering assertion; `fix-ci` granular intercom event table and
  `compact-context` phase broadcasts are removed.

### U16 - Execution-phase skills B
* Size M / complexity low.
* Files: `runtime-verification`, `operational-closure`, `shipment-reconcile`, `harness-architect`,
  `safety-modes` templates + mirrors (safety-modes has no mirror). Same rule.

### U17 - install-harness skill, prompt and auto-mergeinstall agent
* Posture: characterization-first. Size M / complexity medium (36 hits in one skill).
* Files: `.github/skills/install-harness/SKILL.md`, `.github/prompts/install-harness.prompt.md`,
  `.github/agents/auto-mergeinstall.agent.md`. Remove the pack from preset tables, overlay-contract,
  explicit-selection examples, heartbeat/broadcast guidance; add a short "Retired capability packs"
  note (explicit `capability_packs=agent-intercom` -> `RETIRED_PACK` warning, ignored). Refresh
  checksums of manifest-tracked skills.
* Install-manifest version pin: Step 3.3 of the install-harness skill hard-codes the manifest skeleton
  `schema_version: "1.0.0"` and no existing install-harness test asserts it. U17 pins it to the
  current manifest contract `1.1.0` (equal to `SCHEMA_CONTRACTS["manifest"]["current_version"]`) and
  adds a regression test that renders the Step 3.3 skeleton and validates it against the current
  manifest schema, so a fresh install never emits a known-legacy manifest. (New installs also write
  profile `1.1.0`; config follows U4.)

### U18 - workspace-discovery, tune-harness, verify-harness skills (retired-pack handling)
* Size M / complexity medium.
* Files: `.github/skills/workspace-discovery/SKILL.md` (stop Step 1.5c detection of
  `.intercom/settings.json`/markers and the `agent_intercom` recorded block; ALSO update the
  generated-profile example/pin `schema_version: "1.0.0"` (around L559) to the new current profile
  contract `1.1.0`, so a fresh discovery no longer emits a known-legacy profile; add a
  generated-profile validation test that renders the skill's profile skeleton and validates it
  against the current profile schema, with `schema_version` equal to
  `SCHEMA_CONTRACTS["profile"]["current_version"]`),
  `.github/skills/tune-harness/SKILL.md` (remove L20/L264/L521/L913 weaving rows; add the "retired
  capability pack" drift category with the cleanup offer and checksum rule from D-3.4/5),
  `.github/skills/verify-harness/SKILL.md` (L124 event-contract wording -> policy P-017
  visibility protocol). Refresh checksums.

### U19 - Docs: guides, README, primitives, CHANGELOG
* Size S / complexity low.
* Files: `README.md`, `docs/capability-packs.md` ("Retired packs" tombstone), `docs/getting-started.md`,
  `docs/tuning-guide.md`, `docs/primitives.md`, `CHANGELOG.md` (NEW entry only; historical lines
  untouched). The CHANGELOG entry states the removal, the schema version bumps, the legacy
  tolerance behavior and the deferred-doc deletion.

### U20 - Telemetry docs and deferred-doc deletion
* Size S / complexity low.
* Files: `docs/telemetry/cross-pack-adapter-gap-report.md` (close the "Explicit agent-intercom
  deferral note": pack retired, deferral closed, no mapping will be authored),
  `docs/telemetry/backlogit-evidence-map.md`, `docs/telemetry/backlogit-sensitivity-guardrails.md`
  (drop intercom from the "remaining portions" lists), DELETE `docs/deferred/agent-intercom-opt-in-nonmcp.md`
  and `.patch` (D-5).

### U21 - Deploy wrappers: retired-pack tolerance
* Posture: test-first. Size M / complexity medium.
* Files: `scripts/deploy-harness.{ps1,sh}`, `templates/scripts/deploy-harness.{ps1,sh}.tmpl`
  (4 files, identical logic mirrored), `tests/test_deploy_harness_scripts.py`.
* The wrappers also scaffold a config with a hard-coded `schema_version: "1.0.0"`
  (`scripts/deploy-harness.sh` ~L388, `scripts/deploy-harness.ps1` ~L424, plus their templates);
  all four copies must emit U4's new current config version so a fresh one-command deployment does
  not create a known-legacy config, and the execution tests assert and validate the generated
  config against the current config schema.
* Behavior: an explicit pack list containing `agent-intercom` prints a `RETIRED_PACK` warning and
  skips it (exit 0) instead of `Unknown pack`. The test's `_OPT_IN` assumptions are rewritten
  (omitted `full`/`standard` == preset defaults == all remaining registry packs; explicit `all`
  == every registry pack; `starter` empty; explicit-subset tests use real packs; one new test for
  the retired value on both interpreters). Update parity tests between `scripts/` and `templates/scripts/`.

### U22 - Pack definition removal (registry, schema enum, overlay instruction)
* Size M / complexity medium. Final structural step (D-13).
* Files: `templates/packs/capability-pack-registry.yaml` (remove the pack and its comment block),
  `schemas/capability-pack-registry.schema.json` (enum), DELETE
  `templates/instructions/agent-intercom.instructions.md.tmpl` and
  `.github/instructions/agent-intercom.instructions.md`, remove the manifest `artifacts[]` record for
  the overlay file, adjust `tests/test_capability_pack_registry.py` (drop `agent-intercom` from the
  expected id list L24 and delete `test_agent_intercom_is_opt_in_add_on`),
  `tests/test_graphtor_docs_full_suite.py` (`_OPT_IN_ADD_ONS` becomes empty; docstring), and any
  pack-count/enumeration assertions elsewhere (grep for `len(packs)` style tests).
* Verify: registry validates against the edited schema; dogfood verify has 0 blockers and no
  "template missing" finding.

### U23 - Final enforcement and checksum reconciliation
* Posture: verification. Size S / complexity low.
* Files: `tests/test_removed_pack_surface_guard.py` (empty the `PENDING_SURFACES` ledger and enable
  the empty-ledger assertion), manifest reconciliation pass.
* Verify: `git grep -il intercom` over live surfaces returns only allowlist/tombstone entries; full
  suite green; `autoharness verify-workspace` on the dogfood tree: 0 blockers, no
  `removed-capability-pack` warnings, and no NEW checksum drift versus the pre-change run (pre-existing
  drift is reported, not "fixed", per D-14); a legacy-profile smoke run (frozen-version fixtures from
  U6) still warns without crashing.

## Dependency Graph

Linear chain (each task blocked by its predecessor; Ship executes serially, the chain gives a
deterministic order and keeps the guard ledger edit-conflict-free):

`U1 -> U2 -> U3 -> U4 -> U5 -> U6 -> U7 -> U8 -> U9 -> U10 -> U11 -> U12 -> U13 -> U14 -> U15 -> U16 -> U17 -> U18 -> U19 -> U20 -> U21 -> U22 -> U23`

Hard (non-ordering) reasons: U1 precedes everything (ledger); U2-U4 share `schema_contracts.py`;
U5 precedes U7 (replacement check before retirement); U4+U6 precede U7/U8 (version slots and
tolerance exist before the dogfood docs migrate); U7+U8 precede U9-U22 (assertions retired and pack
disabled before content is removed); U21 precedes U22 (wrappers tolerate the retired id before the
registry stops listing it); U22 precedes U23. No cycles. Shipment-level: `215-S blocks <this shipment>`.

## Sequencing and shared files (conflict register)

| Shared file | Other queued work | Resolution |
|---|---|---|
| `schemas/harness-config*`, `schema_contracts.py` | 208.005/208.006 (config 1.2.0 cut-over) | this shipment after 215-S; version derived at claim time |
| `src/autoharness/verify_workspace.py` | 207.003, 208.008, 208.009 | after 215-S; re-baseline line refs |
| `tune-harness`, `install-harness`, `workspace-discovery` skills | 208.010, 208.011, 208.014 | after 215-S |
| `workflow-policies(.tmpl)` | 208.012 (P-013.5) | after 215-S |
| `_orchestrator` template/mirror | 207.005 | after 215-S |
| `harness-manifest.yaml` checksums | every shipment | serial execution; refresh only own edits |
| `.autoharness/config.yaml` | 208.006 operator-confirmed marker | U8 touches only the pack entry + version |
| 211-S (UTC lint), 212-S, 213-S, 214-S | unrelated scopes | not modified; this shipment is not their predecessor |

## Non-Goals

* No replacement remote-visibility/approval pack and no new intercom-like mechanism.
* No rewrite of historical records (D-9) and no edit of any published schema mirror.
* No rename of `## Remote Operator Integration` (D-8) and no change to the telemetry `route_kind`
  vocabulary (D-6).
* No re-render of installed mirrors from templates (D-12); no cleanup of pre-existing manifest drift.
* No changes to Ship/Stage role boundaries, dark-mode authority semantics, or P-xxx policy
  semantics - only the intercom transport wording is removed.

## Plan Hardening Signals

* public API, schema, or contract change: **present** - three versioned contracts bump; registry
  schema enum; verify warning/proposal vocabulary.
* security/auth/permission/compliance: **absent** - no credential or trust-boundary change; the
  removal of the remote approval channel is a reduction of an optional transport, not of a safety
  rule (native approval path remains, D-4).
* migration, backfill, destructive/irreversible step: **present** - legacy-document migration
  path, deletion of the overlay template/mirror and the deferred docs, dogfood config/manifest
  edits (operator-owned config).
* external integration / operator checkpoint / external dependency: **present** - blocked-by 215-S,
  operator authorization for the config edit, manifest checksum procedure.
* high runtime / rollout / rollback risk: **present (moderate)** - ~95 live files across the
  pipeline agents that govern Stage/Ship themselves.

Requires plan hardening: yes

## Plan Hardening (2026-10-14)

Hardening was required (P-006): schema/contract change, migration of installed documents,
irreversible deletions, an operator-owned file edit, and a dependency on a queued shipment.

**Learnings and instructions consulted** (`docs/compound/` + live instructions):
* `2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md` and
  `2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md` -> D-2 (bump, byte-pin the
  frozen mirrors, the 7-step fix procedure is the template for U2-U4).
* `115-S-109-F-checksum-and-branch-ownership-patterns.md` -> D-14 (LF git-blob checksums by direct
  subprocess capture; never PowerShell redirect).
* `2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md` ->
  U23 (report, do not "fix", pre-existing drift; only refresh files this shipment edited).
* `2026-05-06-harness-manifest-artifacts-vs-entries-added.md` -> U8/U22 edit the manifest
  `artifacts[]` list and `capability_pack_overlays[]`, not `entries_added`.
* `docs/archive/memory/2026-07-12-ping-loop-removal-acp-consolidation.md` (precedent: a prior
  intercom-adjacent removal needed the manifest artifact record removed together with the file and a
  test pinning the absence).
* Instructions re-read: `.github/instructions/backlogit.instructions.md` (checkpoint/sizing seams),
  `circuit-breaker.instructions.md` (stall rule), `role-enforcement.instructions.md`.

**Protected invariants** (must hold after every task):
1. Published schema mirrors are byte-identical to their pre-change blobs (byte-pin tests, U2-U4).
2. `verify_workspace` never crashes and never reports a strict-schema blocker for a document that
   merely lists the retired pack (U6 tests are the contract).
3. Normative operator-visible events (policy-violation reports, `DARK_MODE_*`, operator-choice
   presentation, `degraded-visibility` halt rules) keep existing, expressed as session output.
4. Template/mirror parity tests and the in-suite dogfood `verify_workspace` stay green after each task.
5. No historical record (D-9) is modified; `git diff --stat` per task shows no path under the
   historical allowlist except `CHANGELOG.md` (additions only).
6. Stage/Ship/Orchestrator role boundaries, dark-mode authority fields and P-0xx semantics are
   unchanged - only intercom transport wording is removed.

**Risky actions** (`ProposedAction` / `ActionRisk` / `ActionResult` vocabulary; strict-safety is not
installed in this workspace, so this classification is carried as plan discipline):

| ProposedAction | ActionRisk | Approval | Expected ActionResult / rollback |
|---|---|---|---|
| PA-1 mint profile/manifest 1.1.0 and config N+1 mirrors, bump `SCHEMA_CONTRACTS` (U2-U4) | high (contract) | plan-review PASS (done); no separate operator approval | new mirror files + registry edit; rollback = `git revert` of the task commit (frozen mirrors untouched, so nothing legacy is affected) |
| PA-2 edit operator-owned `.autoharness/config.yaml` (remove ONE `capability_packs` entry; no version bump) (U8) | high (operator-owned, drives routing) | operator directive recorded in stash 0FD06900 / Orchestrator relay; Ship re-confirms at claim, halts if absent | one-line diff; rollback = revert; MUST NOT touch route/`context_tier` markers |
| PA-3 delete `templates/instructions/agent-intercom.instructions.md.tmpl`, `.github/instructions/agent-intercom.instructions.md` (U22) | medium (irreversible only via git history) | covered by operator scope decision | recoverable from git history; legacy installs unaffected (their own copy stays until tune offers cleanup) |
| PA-4 delete `docs/deferred/agent-intercom-opt-in-nonmcp.{md,patch}` (U20) | low | D-5 | recoverable from git history / PR #253 |
| PA-5 rewrite normative operator-visible text in agent/policy/skill mirrors (U5, U9-U18) | medium (behavioral prose) | plan-review PASS | per-family tasks give per-commit rollback granularity |
| PA-6 refresh manifest checksums (every sweep task) | medium (integrity record) | none; procedure D-14 | rollback = revert; verify-workspace re-run after each task |

**Added verification** (beyond each unit's own tests):
* Every task closes with the full suite (`PYTHONPATH=src python -m unittest discover -s tests`) and
  a `verify_workspace` run on the dogfood tree whose blocker count is compared with the pre-task
  baseline (0 expected throughout).
* U1's guard doubles as a progress meter: `PENDING_SURFACES` shrinks monotonically; a task that
  forgets one of its surfaces fails rule (b) (stale entry) or leaves the next task's ledger dirty.
* U6/U23 legacy smoke: frozen-version fixtures (manifest 1.0.0, profile 1.0.0, config 1.1.0) listing
  the retired pack plus the dogfood-style `agent_intercom` block run through `verify_workspace`
  and the tune-harness proposal planner; assert exit without exception, 0 blockers, warning
  `removed-capability-pack`, and a `remove-retired-capability-pack` proposal.
* U21 runs both wrapper interpreters when available (the tests already skip when pwsh/bash is
  absent); record the skip in the closure note rather than treating a skip as a pass.
* Claim-time baseline check (Ship): confirm 215-S is `shipped`, re-read `SCHEMA_CONTRACTS["config"]`
  and re-derive U4's `<N+1>`; if 215-S has not shipped the pre-claim gate already blocks (the
  `blocks` edge), so no manual override is expected.

**Operational closure / monitoring / rollback**
* Owner: Ship executes; operator reviews the PR. Validation window: one full `verify-workspace`
  on the dogfood tree and one tune dry-run against a legacy-profile fixture before closure.
* Monitoring signals: guard test failures, `removed-capability-pack` warnings on the dogfood tree
  after U8 (must be zero), manifest checksum drift list vs baseline.
* Rollback triggers: any red full-suite that cannot be fixed within the task, any strict-schema
  blocker on the dogfood tree, any modified historical-allowlist path. Rollback procedure: revert the
  offending task commit(s) in reverse dependency order; because the chain is linear and each task
  leaves the tree green, a partial rollout (stop after any task) is a supported state - the only
  user-visible partial state is "pack still listed but tolerated" (before U22), which is explicitly
  handled by U6/U7.
* Partial-rollout constraint: U22 (definition removal) must not ship before U21 (wrapper
  tolerance) or before U18 (tune/install tolerance guidance) - the dependency chain enforces it.

**Review-gate capability risks carried forward.** Reviewer subagent dispatch is not exposed in this
Stage environment (no task/agent-dispatch tool). Plan review therefore runs as a declared
single-agent persona pass: the review section must carry literal
`dispatch_mode: single-agent-declared-degradation` and `decision:` markers and cover every selected
persona (P-012). Anchor/cross-model routing is likewise unavailable and is declared.

**Unresolved operator decisions that still block safe execution:** none for staging. Execution-time
checkpoints: (1) Ship confirms the operator authorization for U8's config edit; (2) the shipment
waits for 215-S by dependency edge.

`plan_hardening_status: hardened`

## Plan Review (cycle 1 and cycle 2, 2026-10-14)

dispatch_mode: single-agent-declared-degradation
decision: PASS

**Capability declaration (P-012).** `TOOL_DEGRADED: reviewer-subagent-dispatch - declared fallback:
single-agent persona pass` (this Stage session exposes no subagent/agent-dispatch tool; the persona
identity files under `.github/agents/subagents/` were used as the rubric source and each persona's
focus from the Persona Rubric Adapter was applied inline, one finding list per persona).
`TOOL_DEGRADED: model-specific-review-routing - declared fallback: same-model rubric pass`
(no `model_routing.anchor_review` dispatch available; Architecture Strategist ran same-model).
Every selected persona was covered; findings are normalized to P0-P3. Plan hardening was required
(`Requires plan hardening: yes`) and was satisfied by the `## Plan Hardening` section above.

**Persona coverage**

| Persona | Mode | Findings |
|---|---|---|
| Constitution Reviewer | inline pass (always-on) | F1 (P1, fixed), P3 note |
| Python Reviewer | inline pass (always-on) | F2 (P2, fixed), F3 (P3), F4 (P2, fixed) |
| Scope Boundary Auditor | inline pass (always-on) | F5 (P3), F6 (P3, re-triaged from P2) |
| Learnings Researcher | inline pass (always-on; searched `docs/compound/`) | none contradicting; F12 (P3) |
| Architecture Strategist | inline pass, same-model (anchor route unavailable) | F7 (P3, re-triaged from P2), F8 (P3) |
| Agent-Native Parity Reviewer | inline pass (triggered: agent-facing instructions and operator-visible events change) | F9 (P2, fixed) |
| Security Lens Reviewer | inline pass (triggered: removal of an optional approval-routing transport) | F10 (P3) |
| Schema-CLI-Docs Coupling Reviewer (repo-specific, extra pass) | inline pass | F11 (P2, fixed) |

**Cycle 1 initial gate: FAIL (1 P1).** Plan revised in place; cycle 2 re-verified every revised
section and found no residual P0/P1.

**Findings**

* **F1 - P1 (Constitution Reviewer) - RESOLVED.** The constitution's Governance section requires "a
  version bump, rationale, and sync impact report" for any amendment; the draft removed the
  `agent-intercom` Capability Overlays bullet without that process. Fix: U10 now bumps the
  constitution to 1.1.0 (template + mirror) and adds a dated sync-impact report under
  `docs/design-docs/`; Principle VII (destructive-command approval) confirmed intercom-independent.
  P3 note: Principle II (tests first) is honored by U1/U5/U6/U21 test-first posture.
* **F2 - P2 (Python Reviewer) - RESOLVED.** `LEGACY_CAPABILITY_PACK_ERROR_RE` does not match
  `recommendation_reasons.capability_packs.N.item`; U6 now requires extending the matcher with a
  test. (A first draft also planned a matcher for a root `additionalProperties` error on
  `agent_intercom`; hosted review of PR 518 showed the profile root is open so no such error
  exists, and U2/U6 now detect the legacy block directly in the collector instead.)
* **F3 - P3 (Python Reviewer) - advisory.** Type `REMOVED_CAPABILITY_PACKS` as an immutable
  `Mapping[str, RemovedPackInfo]` (frozen dataclass or `MappingProxyType`) so the retired-pack
  metadata is not a mutable module global.
* **F4 - P2 (Python Reviewer) - RESOLVED.** The guard test's file scan must be encoding/CRLF-robust;
  U1 now specifies byte reads with `errors="ignore"` and binary skipping, using `git ls-files`.
* **F5 - P3 (Scope Boundary Auditor) - advisory.** 23 tasks is large for a "removal", but each is a
  family-scoped mechanical unit under the 2-hour rule; no replacement mechanism, no rename of
  `Remote Operator Integration`, no telemetry vocabulary change (D-6/D-8) keeps scope minimal.
* **F6 - P3 (Scope Boundary Auditor) - advisory (re-triaged from P2).** U21 (wrapper retired-pack
  tolerance) goes slightly beyond pure deletion, but is required by requirement R5 (existing
  automation passing `-Packs agent-intercom` must not hard-fail), so it is requirement-driven, not
  scope growth; kept as its own small task so it can be dropped independently if the operator
  disagrees.
* **F7 - P3 (Architecture Strategist) - advisory (re-triaged from P2).** `verify_workspace.py` is
  edited by three sequential tasks (U5-U7); the chain is linear and each step is independently
  green, so there is no concurrent-edit risk; the alternative (one large verify task) would exceed
  the complexity budget.
* **F8 - P3 (Architecture Strategist) - advisory.** The `215-S blocks` edge places this shipment at
  the tail of the 211-S..215-S chain; only U4 (config version slot) and the shared files truly
  force this, and it is recorded with reasons (D-11). Re-evaluate only if 215-S is abandoned.
* **F9 - P2 (Agent-Native Parity) - RESOLVED.** Removing transmit/standby left the "blocked on
  operator" behavior undefined; D-4 now defines the channel-neutral clarification/wait rule
  (state question + options, STOP until reply) and names the Ship `[WAIT]` notice and Stage
  selection prompts as its consumers.
* **F10 - P3 (Security Lens) - advisory.** No secret/auth surface changes. When reviewing U10/U12,
  confirm no rewritten sentence implies destructive approval may be skipped when no remote channel
  exists; policy G3 ("no independent approval channel means halt, do not restore") must remain.
* **F11 - P2 (Schema-CLI-Docs Coupling) - RESOLVED.** Registration touchpoints cross-checked against
  `docs/compound/015-s-graphtor-docs-pack-registration.md` (10 locations): all 10 are covered by
  U2-U4, U6-U7, U13, U12, U17-U19, U22; the config template schema pin is covered by U4.
* **F12 - P3 (Learnings Researcher) - advisory.** The plan reuses the established 7-step
  schema-mirror-versioning procedure and LF-blob checksum procedure; nothing contradicts a known
  past resolution.

**Runtime verification and operational closure gaps:** none open - runtime surface is the
`autoharness verify-workspace` CLI and the install/tune skills; each unit lists its verification and
U23 plus the Plan Hardening closure section cover monitoring, rollback and validation window.

**Gate decision: PASS** (no open P0/P1; every P2 is resolved in the plan; F6/F7 were re-triaged to
P3 advisory, so no accepted-P2 `ADVISORY` authorization is required). The plan is harvest-ready.

## Harvest Record (2026-10-14, Stage)

Feature `209-F`; shipment `216-S` (queued, `blocks` edge: blocked by `215-S`). Every task carries
`size` and `complexity` as structured fields (`size_source: agent`,
`size_ruleset_version: ah-stage-sizing-v1`; written in separate update calls per the registry's
mutually exclusive seams) and a `harness-surface` label per P-002. Each task is blocked by its
predecessor (linear chain). No subtasks were created: the mechanical sweeps carry per-file
checklists in their descriptions and acceptance criteria, and splitting by file would create
sub-30-minute items below the useful granularity.

| Unit | Task | Size | Complexity | harness-surface |
|---|---|---|---|---|
| U1 guard test | 209.001-T | S | low | none |
| U2 profile schema 1.1.0 | 209.002-T | M | medium | harness-architect |
| U3 manifest schema 1.1.0 | 209.003-T | S | medium | harness-architect |
| U4 config next-version schema | 209.004-T | M | medium | harness-architect |
| U5 visibility protocol relocation | 209.005-T | M | medium | harness-architect |
| U6 verify legacy tolerance | 209.006-T | M | medium | harness-architect |
| U7 verify retire assertions | 209.007-T | M | medium | harness-architect |
| U8 dogfood disable | 209.008-T | S | medium | none |
| U9 instruction family | 209.009-T | M | low | none |
| U10 foundation family | 209.010-T | M | low | none |
| U11 Orchestrator | 209.011-T | M | medium | none |
| U12 Ship | 209.012-T | M | low | none |
| U13 Stage | 209.013-T | M | medium | none |
| U14 planning skills | 209.014-T | M | low | none |
| U15 execution skills A | 209.015-T | M | low | none |
| U16 execution skills B | 209.016-T | M | low | none |
| U17 install-harness | 209.017-T | M | medium | none |
| U18 discovery/tune/verify-harness | 209.018-T | M | medium | none |
| U19 docs and CHANGELOG | 209.019-T | S | low | none |
| U20 telemetry docs and deferred deletion | 209.020-T | S | low | none |
| U21 deploy wrappers | 209.021-T | M | medium | none |
| U22 pack definition removal | 209.022-T | M | medium | none |
| U23 final enforcement | 209.023-T | S | low | none |

