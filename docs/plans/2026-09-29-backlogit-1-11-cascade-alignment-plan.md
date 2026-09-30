---
title: "Align P-015 / shipment-reconcile with backlogit >=1.11.0 flat cascade semantics"
description: "Realign the CASCADE postcondition sets to backlogit 1.11.x, which leaves linked deliberations independent. Add a sanctioned, path-independent linked-deliberation disposition step, and gate CASCADE on a fresh backlogit version probe inside a verified engine-semantics line, so the next engine drift is detected before mutation instead of at closure."
doc_type: plan
status: reviewed
review_record: "inline — see sections Plan Review and Independent review amendments (2026-09-29)"
independent_review: "2026-09-29 independent 4-reviewer plan review (Architecture, Correctness, Scope, Schema-CLI-Docs Coupling): PASS_WITH_CHANGES x4, 0 P0, 7 P1 — all resolved in plan; see section Independent review amendments (2026-09-29)"
created: 2026-09-29
amended: 2026-09-29
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
  snapshot extension, the Step 0(c) routing bullets, the Cascade Close
  "transition log" preamble, pre-invocation re-collection, Cascade Close step 3
  `allowed_ids` / `required_ids`, the step 6 report, the safe-close/Cascade
  hand-offs to post-mode, Quality Criteria, and the vocabulary summary.
* P-015 in `templates/policies/workflow-policies.md.tmpl` and its mirror
  `.github/policies/workflow-policies.md`: Statement, Required Check,
  Postcondition, Violation Action, Relationship to P-007, Evidence-class note,
  D1a table, admission paragraph, INV-1, INV-6, INV-7, INV-10, and item 7.
* The Ship agent in `templates/agents/_ship.agent.md.tmpl` and its mirror
  `.github/agents/_ship.agent.md`: the SAFE_CLOSE and CASCADE close-path
  bullets, the step 1.e commit gate, and the Role Boundary deliberation row.
* The generic Ship agent's post-merge Step 7 "Source artifact cleanup"
  (`templates/agents/_ship.agent.md.tmpl` L889-893) and the `operational-closure`
  skill's closure-checklist "Source artifact cleanup" bullet (template and mirror,
  L84). See the corrected problem statement below.
* The docstring of `src/autoharness/gates/shipment_closure.py` (L9-21).
* The 155-S-era contract tests in `tests/test_cascade_close_archived_ids_postcondition.py`
  (`CascadeCloseLinkedDeliberationAllowanceTests`, the item-7 policy tests, and
  `CascadeCloseTwoSetGateScenarioTests` scenario 2) and
  `tests/test_flat_manifest_closure_docs.py` (`INVARIANT_TOKENS`).

As a result (corrected 2026-09-29, independent review P1-1):

* Every CASCADE close whose explicit feature member links a live deliberation
  halts after mutation (190-S / `034-DL`, which `184-F` linked by description
  only).
* SAFE_CLOSE does not halt. It leaves a deliberation that is linked only by
  description or `references` text live (stranded).
* A deliberation linked through `custom_fields.source_deliberation_id` is a
  different case. The generic Ship agent's post-merge Step 7 already archives it
  with `backlogit_archive_item`, with **no shared-reference guard**, after
  reconcile has finished. The dogfood mirror `.github/agents/_ship.agent.md` has
  no such step (it retires only the source stash entry). The `operational-closure`
  skill records the outcome either way. An unguarded Step 7 would silently defeat
  any retention rule this plan adds, so Step 7 is realigned (U6b). `195-F` itself
  carries `source_deliberation_id: 038-DL`, so its live closure exercises both
  mechanisms.
* Nothing detects an engine-semantics change before the destructive call.

## Requirements Trace

| # | Requirement (decision D*) | Unit(s) |
|---|---|---|
| R1 | Engine-semantics gate: pure function, single-source verified-line constant, released builds only, same-surface probe; `select_close_path` composition function; unverified → SAFE_CLOSE (D4, D4a) | U1a |
| R1b | Pure, read-only `compute_linked_deliberation_disposition` planner with fixture tests written first (D3a) | U1b |
| R2 | Gate docstring realigned to the flat `allowed_ids` / `required_ids` (D2) | U1a |
| R3 | P-015 D1a, admission (disposition set), INV-1, INV-6, CASCADE engine-semantics precondition, INV-12, supersession note, history row (D1-D4, D3a, D4a) | U2a |
| R3b | P-015 close-path gate vs. INV-12 split: Statement, Required Check, Postcondition, Violation Action, P-007 relationship, INV-7, INV-10, item 7, Evidence-class note; P-010 clarification (D3a) | U2b |
| R4 | Skill Step 0(b) all-member snapshot; Step 0(c) engine-semantics gate, `select_close_path`, routing; pre-invocation re-probe (D2, D4a) | U3a |
| R4b | Skill disposition snapshot, INV-6 scoping, transition-log preamble, re-collection (D2, D3a) | U3b |
| R5 | Skill Cascade Close steps 3, 5, 6, 7, Quality Criteria, vocabulary: flat sets over every manifest item; linked deliberation in `archived_ids` or modified = engine drift (D2) | U4 |
| R6 | Skill: Linked-Deliberation Disposition section (D3, D3a) | U5a |
| R6b | Skill: hand-offs, Behavioral Constraints, safe-close steps 1/8, post-mode, scenario matrix, Quality Criteria, closing negative grep over all contract files (D3a) | U5b |
| R7 | Ship agent close-path bullets, step 1.e gate, Role Boundary (D2, D4a, D3a) | U6 |
| R7b | Ship Step 7 and `operational-closure` consume the disposition report; never archive a retained deliberation (D3a) | U6b |
| R8 | Rendered-region parity between each template and its mirror; tracked checksums refreshed in the same unit that edits the mirror (D9, D9a) | U2a-U6b |
| R9 | Compound learning, supersession notes, re-verification runbook for a new backlogit minor line (D1, D7) | U7 |
| R10 | Deferred items captured as stash entries, not implemented (D7, D8a) | Stage (stash), not a unit |

## Implementation Units

Harness-surface labels:

* U1a and U1b are code-bearing and carry `harness-surface:harness-architect`.
  The P-004 per-task harness applies: tests first (red, then green).
* U2a-U7 are contract prose plus their pinning tests. They carry
  `harness-surface:none` and use a **test-first contract posture**: update or add
  the pinning assertions first (red against the old text), then edit the template
  and mirror (green), then refresh the checksum.

**Parity-bundle convention (applies to U2a-U6b).** The 2-hour granularity rule
suggests fewer than 3 files per unit. Each prose unit instead edits a *parity
bundle* of up to four files:

* the template;
* its dogfood mirror;
* the one-line `.autoharness/harness-manifest.yaml` checksum and note for that
  mirror;
* the contract-test file that pins the text.

Splitting the bundle would leave intermediate commits with a red suite or a stale
checksum. This is the established repository convention (see the manifest notes
for 166.004-T through 166.007-T). The *intellectual* scope of each unit is still a
single contract region.

**Parity method (amended 2026-09-29, independent review P1-4).** The template and
mirror legitimately differ (`{{FEATURE_SHIPMENTS}}`, `{{BACKLOG_DIRECTORY}}`,
`{{DATE}}`, and the mirror's concrete `7F9CB5E9` references in INV-4 / INV-11,
which `test_contract_files_define_flat_scope_and_split_delivery_limit` pins).
Whole-section byte parity is therefore not a valid test. Instead:

* **Policy and skill pairs: rendered-region parity.** Render the template with
  `tests/_assertion_render.py::render_source` (which wraps
  `autoharness.verify_workspace._render_template` +
  `_derive_template_variables`, the pattern used in
  `tests/test_template_variable_derivation_contract.py`). Compare **only the
  paragraphs the unit edited**, located by stable anchors, against the mirror.
  An explicit per-test allowlist names every tolerated divergence.
* **Ship agent pair: phrase-level semantic parity.** The mirror is structurally
  divergent: lettered sub-steps a-d at L700-734, the CASCADE bullet at L716-730,
  and no post-merge Step 7. Tests assert that the same required phrases are
  present, and the same withdrawn phrases are absent, in both files. Never byte
  parity.
* **Machine-readable verified-line token.** The policy and the skill each state
  exactly ``Verified engine-semantics lines: `1.11` ``. Tests parse the token and
  assert that it equals `VERIFIED_CASCADE_ENGINE_MINOR_LINES`. The Ship agent
  references the gate by name and never restates the line (H8).

**Multi-shipment delivery (amended 2026-09-29, PR #466 cycle 8; supersedes the
original "Single PR" rule).** The 2-hour re-split turned the twelve unit tasks
into 58 tasks, delivered as six chained shipments (see Resulting units and order
and Shipment partition below). Intermediate commits may still forward-reference a
heading that a later task creates (for example, U3a names the
"Linked-Deliberation Disposition" step that U5a adds). Because each shipment now
closes on main before the next one is claimed, the operator-approved amendment
("A + amendment", 2026-09-29) adds these multi-PR closure rules:

* **T1 — one PR per shipment.** Each shipment is one Ship PR. The DAG chain
  `202-S ◀── 203-S ◀── 204-S ◀── 205-S ◀── 206-S ◀── 201-S` forces each merge
  and closure to finish before the next claim.
* **T2 — deliberation-clean slices.** Features `196-F`..`200-F`, shipments
  `202-S`..`206-S`, and their tasks carry no deliberation linkage: no
  `source_deliberation_id`, no deliberation-ID token in the title, description,
  labels, or custom fields, and no link whose target is a deliberation. Task
  bodies cite the decision document path instead. This keeps the pre-195
  linked-deliberation expansion empty, so the old and the flat
  `allowed_ids` / `required_ids` coincide for the early slices.
* **T3 — `203-S` closure (slice 2).** The P-015 flat sets and the engine-semantics
  precondition are on main, but the skill has no Step 0(c) gate yet. The
  precondition cannot be recorded, so Ship closes `203-S` through SAFE_CLOSE with
  `ENGINE_SEMANTICS_UNVERIFIED` (the policy's own fail-closed branch).
* **T4 — `204-S` and `205-S` closures (slices 3 and 4).** The U3a routing
  forward-references the disposition step, which lands only in `206-S`. Ship
  performs no deliberation mutation and records
  `linked_deliberation_disposition: step-not-yet-on-main (transition window); all retained`.
  These closures must not touch any deliberation.
* **T5 — first INV-12 closures.** `206-S` (slice 5) is the first closure with
  INV-12 on main. `201-S` (slice 6, terminal) is the first closure with the full
  realigned contract and carries the `038-DL` live proof (see Runtime
  Verification and Closure).

The three-point SCOPE_GAP sequencing guard (see Dependency Graph) runs at every
shipment's claim, P-014 PR-ready gate, and pre-merge, not once. No dogfood run of
the edited contract happens on an intermediate commit inside a shipment's PR.

### U1a — Engine-semantics gate, close-path composition, gate docstring (code) — 196.001-T..196.003-T (202-S)

Amended 2026-09-29 (independent review P1-3, P2 probe surface, P2 pseudo-versions,
P2 regex, P2 runtime caller, P3 pre-step grep).

* **Pre-step (read-only).** Run
  `git grep -n -E "validated_linked_deliberations|linkedDeliberationIDs|linked deliberation|source_deliberation_id"`
  and record each hit as in scope (owning unit) or out of scope (reason) in the
  task completion note. Baseline at amendment time:
  * the policy, shipment-reconcile, Ship agent, and `operational-closure` pairs;
  * `shipment_closure.py`;
  * `verify_workspace.py`, whose `ship_source_artifact_cleanup` /
    `closure_source_artifact_cleanup` `must_contain` checks are out of scope, but
    U6b must keep those tokens present;
  * the tests `test_cascade_close_archived_ids_postcondition.py`,
    `test_flat_manifest_closure_docs.py`, `test_verify_workspace.py`,
    `test_assertion_render_harness.py`, `test_rendered_assertion_sweep.py`, and
    `test_shipment_mixed_role_detection_compound_doc.py`.
* **Changes** in `src/autoharness/gates/shipment_closure.py`, all additive. The
  new names stay module-local and are not exported from `autoharness.gates`
  (P3-2). A separate `engine_semantics.py` module is not created here; any move
  belongs to the deferred registry `8928EC67` (D7).
  * `VERIFIED_CASCADE_ENGINE_MINOR_LINES: Final[frozenset[tuple[int, int]]] = frozenset({(1, 11)})`.
    This is the single source of truth for the backlogit minor lines whose P-015
    closure engine semantics this contract has verified. It covers **both**
    engine propositions:
    1. flat `shipment ship` archive-candidate selection leaves linked
       deliberations and unlisted descendants independent;
    2. non-cascading `archive_item` changes exactly the named artifact. At
       `v1.11.0`, `internal/core/archive.go` `ArchiveItem` (L103) rewrites only the
       `status`, `archived_status`, and `archived_from` frontmatter keys
       (L234-255), plus the gitignored item event log and index.

    The name is kept for traceability to `038-DL` and `8928EC67`. The docstring
    states the two-proposition scope.
  * `class EngineSemanticsVerdict(str, Enum)` with the values `VERIFIED` and
    `UNVERIFIED`.
  * A frozen dataclass `EngineSemanticsDecision` with fields `verdict`,
    `reason: str`, `probed_version: str | None`,
    `minor_line: tuple[int, int] | None`, `probe_surface: str | None`, and
    `probed_commit: str | None`.
  * `assess_cascade_engine_semantics(probed_version: object, *, probe_surface: object, invocation_surface: object, probed_commit: object = None) -> EngineSemanticsDecision`:
    * **Type.** Only an exact `str` is accepted (`type(x) is str`). A `str`
      subclass, `bytes`, `float`, or `None` is `non-string`.
    * **Parse.** Use
      `re.fullmatch(r"v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?", s, flags=re.ASCII)`.
      This is `fullmatch`, never `match` with `$` (which accepts a trailing `\n`),
      with an ASCII-only `[0-9]` digit class. No `.strip()` and no coercion.
      Anything else is `unparseable`.
    * **Released builds only (amends D4, see D4a).** Any pre-release or
      build-metadata component is `UNVERIFIED` with the reason
      `unreleased build`. This includes Go pseudo-versions
      (`-0.<14 digits>-<12 hex>`), `+dirty`, and `-rc1`.
    * **Same surface.** `probe_surface` and `invocation_surface` must each be
      exactly `"mcp"` or `"cli"`, and they must be equal. Otherwise the result is
      `UNVERIFIED` with `unknown probe surface` or `probe surface mismatch`. The
      MCP server and the CLI binary can be different builds.
    * `(major, minor)` in the constant is `VERIFIED`. Otherwise it is
      `UNVERIFIED` with `minor line X.Y not verified`.
    * Every `UNVERIFIED` reason starts with `ENGINE_SEMANTICS_UNVERIFIED:`. The
      function never raises. `probed_commit` is recorded verbatim when it is an
      exact `str`, otherwise `None`. It is not interpreted here. The skill's
      re-probe compares it raw.
  * `select_close_path(classifier: ClosePathDecision, engine: EngineSemanticsDecision) -> tuple[ClosePath, str]`.
    This is **the single executable composition point** (P1-3).
    * It returns `CASCADE` iff
      `classifier.close_path is ClosePath.CASCADE and engine.verdict is EngineSemanticsVerdict.VERIFIED`.
    * Otherwise it returns `SAFE_CLOSE`, with the classifier's reason when the
      classifier said SAFE_CLOSE, or the engine's reason when the classifier said
      CASCADE and the engine is UNVERIFIED.
    * Wrong-typed inputs return `SAFE_CLOSE` with
      `CLOSE_PATH_SELECTION_INVALID_INPUT`. It never raises.
    * The skill cites this function and also states its 2×2 truth table for
      workspaces without the Python implementation.
  * `classify_shipment_close_path` keeps its signature and behavior
    **unchanged**.
  * Rewrite the module docstring (L9-21):
    * `allowed_ids(S) = closure_scope(S)`;
    * `required_ids(S) = {S} ∪ qualifying feature members ∪ {x ∈ items(S): x not truly archived pre-close}`,
      over every manifest item regardless of `artifact_type`;
    * validated linked deliberations are outside both sets under 1.11.x and are
      handled by the INV-12 disposition step;
    * pointers to `assess_cascade_engine_semantics`, `select_close_path`, and
      `compute_linked_deliberation_disposition` (U1b).
* **Runtime callers (P2).** The self-hosting skill's Step 0(c) (U3a) and the
  disposition step (U5a) cite these functions. Ship evaluates them during dogfood
  closure. They are also the named caller surface for 198-S's A2/A3 evaluator,
  which the 198-S re-plan must adopt (see the P1-3 follow-up stash entry).
* **Tests** (new) in `tests/test_cascade_engine_semantics_gate.py`, written first:
  1. `VERIFIED` with the surfaces `mcp`/`mcp` and `cli`/`cli`: `1.11.0`,
     `v1.11.0`, and `1.11.7`, with `minor_line == (1, 11)`.
  2. `UNVERIFIED` with `unreleased build`:
     * `1.11.1-0.20261001000000-abcdef123456`
     * `1.11.0+dirty`
     * `1.11.1-0.20261001000000-abcdef123456+dirty`
     * `1.11.1-rc1`
  3. `UNVERIFIED`: `1.10.0`, `1.10.1`, `1.12.0`, `2.11.0` (these name the minor
     line), and `1.12.0-rc1` (prefix asserted).
  4. `UNVERIFIED` as `non-string` or `unparseable`:
     * `None`, `""`, `" 1.11.0"`, `"1.11.0 "`, `"1.11.0\n"`, `"1.11"`, `"dev"`,
       `"(devel)"`;
     * full-width and Arabic-Indic digit forms;
     * `1.11` (a float) and `b"1.11.0"`;
     * a `str` subclass instance whose value is `"1.11.0"`.
  5. Surface: `mcp`/`cli`, `None`, and `"MCP"` are `UNVERIFIED`.
  6. `select_close_path`: the full 2×2 truth table plus the invalid-input row.
  7. Prose/regex parity: every example version string that the U2a/U3a text
     quotes is asserted against the function.
  8. The docstring contains the flat definition and not
     `∪ validated_linked_deliberations(S)`. The constant equals
     `frozenset({(1, 11)})`.
* **Exit:** the new tests are green, `tests/test_shipment_closure_classification.py`
  is unchanged and green, and the full suite is green.
* **Size:** M (was S; select_close_path and hardened parsing added).
  **Complexity:** low.

### U1b — Pure read-only linked-deliberation disposition planner (code) — 196.004-T..196.008-T (202-S), 197.001-T..197.006-T (203-S)

Added 2026-09-29 (independent review P2 "pure read-only planner", P1-6, P1-7, P2
self/cycle, P2 torn, P2 every-member-type).

Add `compute_linked_deliberation_disposition(manifest_items, shipment_id, workspace_backlog_dir, *, engine: EngineSemanticsDecision, stash_path=None) -> LinkedDeliberationDispositionPlan`
to `shipment_closure.py`. It is read-only, uses `autoharness.gates.topology._frontmatter`
(the classifier's parser, H5), and never raises. Any read error fails closed to the
`retained_read_error` outcome (see **Outcome enum and reason codes**).

* **Stash path default** (PR #466 review, cycle 4). `stash_path=None` is not "do
  not scan stashes". It resolves to `<workspace_backlog_dir>/stash.jsonl`, the
  active stash file at the root of the resolved backlog directory (for this
  repository, `.backlogit/stash.jsonl`). An explicit `stash_path` overrides the
  default. The default and an explicit path pass the same containment checks
  (see Input safety). A missing stash file means no active stash entries. Any
  other read error on it (unreadable, malformed line, or a containment failure)
  fails closed to `retained_read_error` (with a read-error `reason_code` and the
  stash path as `path`) for every disposition-set deliberation, as the first
  rule of the outcome precedence. The U5a call site passes no `stash_path`, so
  the default is the production path.

* **Description source** (PR #466 review). `_frontmatter` returns only the YAML
  mapping, but a backlogit artifact's description is the Markdown body after the
  closing frontmatter delimiter. The planner therefore reads the body text after
  that delimiter from the same record read, and uses it wherever this unit says
  "description" (member links and live referrers). A record whose body cannot be
  separated from its frontmatter is a read error: `retained_read_error` with
  `reason_code` `body_unseparable`.

* **Disposition set** (amends H1).
  * **Links collected.** The union, over **every explicit manifest member
    regardless of `artifact_type`**, of:
    * the literal `custom_fields.source_deliberation_id`;
    * matches of the matcher `\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b` in the
      description and in each entry of the frontmatter `references` list.
  * **Excluded:**
    * the member's own ID (self-reference);
    * every ID in `closure_scope(S)` (H10).
  * **Validation.** Existence is validated **before** location. The ID must
    resolve to at least one record whose `artifact_type` is `deliberation`. An
    unresolved ID is recorded under `unresolved_references` and is never a halt.
  * **Recorded per deliberation:** link kinds (`source_deliberation_id`,
    `description`, `references`), linking member IDs, every record path, the
    declared status, and the SHA-256 of each record path.
* **Planned outcome per deliberation.** Apply the first rule that matches:
  1. `retained_read_error` (PR #466 review, cycle 5): a read or containment
     failure on the deliberation's own record or records, or on an input of the
     live-referrer scan (the resolved stash file, or any record the scan reads).
     The record carries a read-error `reason_code` and the offending `path` (see
     **Outcome enum and reason codes** below). This rule is evaluated first, so a
     record that cannot be read never reaches later classification.
  2. `retained_ambiguous`: the ID resolves to more than one record (torn or
     duplicated).
  3. `already-archived`: the declared `status` is exactly `"archived"` (H3).
  4. `retained_engine_unverified`: the engine verdict is UNVERIFIED (P1-7). This
     applies on every path.
  5. `retained_live_status`: the deliberation's own status is `active`,
     `blocked`, or `review` (P1-6; PR #466 review, cycle 4). These are the live
     statuses in the deliberation status vocabulary of
     `.backlogit/header-def.yaml` (`queued`, `active`, `blocked`, `review`,
     `done`, `accepted`, `rejected`, `archived`). Deliberations have no
     `in-progress` status. A deliberation under `review` is never archived.
     `queued`, `done`, `accepted`, and `rejected` are not live under this rule;
     `archived` is handled by rule 3.
  6. `retained_shared_reference: [referrer IDs]`: a live referrer exists (see
     below).
  7. `retained_description_mention`: no explicit member links the deliberation
     through `source_deliberation_id`. It is linked only through description or
     `references` text. The outcome is report-only (P1-6, reviewer-recommended
     option).
  8. `archive`: otherwise.
* **Outcome enum and reason codes** (PR #466 review, cycle 5; operator design,
  2026-09-29).
  * INV-12 is the invariant: the rule that gives each disposition-set member
    exactly one outcome and permits mutation only when its conditions hold.
    `LinkedDeliberationOutcome` is the **closed enum** of the values INV-12
    assigns. It has exactly eight members: `archived`, `already-archived`,
    `retained_read_error`, `retained_ambiguous`, `retained_engine_unverified`,
    `retained_live_status`, `retained_shared_reference`, and
    `retained_description_mention`. The planner's planned `archive` is the
    pre-mutation form of `archived`, which U5a assigns only after
    verify-after-each.
  * Every outcome record carries a non-empty `reason_code`. For every outcome
    except `retained_read_error`, it defaults to the outcome value.
  * A `retained_read_error` record also carries `path`: the offending path,
    workspace-relative with `/` separators. A path that resolves outside the
    workspace is recorded as supplied.
  * The initial read-error reason codes are:
    * `path_escape`: a record path or the `stash_path` does not canonicalize
      inside the workspace backlog tree;
    * `symlink_or_reparse_point`: the path is, or sits under, a symlink,
      junction, or reparse point;
    * `unreadable_file`: an OS error on open or read, or content that is not
      decodable as UTF-8;
    * `malformed_frontmatter`: the frontmatter is missing, is not valid YAML, or
      is not a mapping;
    * `body_unseparable`: there is no closing frontmatter delimiter, so the
      Markdown description body cannot be separated;
    * `malformed_stash_entry`: a `stash.jsonl` line is not a JSON object.
  * `unresolved_references` entries are `{id, reason_code}`, with `invalid_id`
    (the ID fails `_ARTIFACT_ID_PATTERN`) or `not_found` (no deliberation record).
    Neither is a read error.
  * The enum is closed: adding a value is a contract change. The reason-code
    vocabulary is extensible. Report consumers (the U5a report, U6b's Ship
    Step 7, and `operational-closure`) accept any `reason_code`, including an
    unknown one, and copy it verbatim. They never re-derive it.
* **Live referrers** (bounded, read-only; P1-6).
  * **Counted:**
    * work items (`feature`, `task`, `subtask`, `bug`, `chore`) outside
      `closure_scope(S)` that are not truly archived and link the deliberation
      through any of the three link sources;
    * shipments other than `S` that are not truly archived, whose
      `custom_fields.items` lists the deliberation, or whose description or
      `custom_fields.source_deliberation_id` names it (the engine's `doctor.go`
      treats shipment descriptions as links);
    * active stash entries (the resolved `stash_path`, by default
      `<workspace_backlog_dir>/stash.jsonl`) whose `deliberation_id` equals the
      deliberation, or whose text matches it.
  * **Never counted:**
    * the deliberation itself;
    * any other deliberation, so A↔B cycles and historical cross-mentions never
      count;
    * docs and plan files;
    * truly archived items and shipments;
    * archived stash entries (`archive/stash.jsonl`).
  * A referrer ID that resolves to more than one record counts as live, which
    fails closed to retain.
  * H3 applies to referrers too. An `archive/` record declaring `done` is live. A
    `queue/` record declaring `archived` is not.
* **Input safety** (Constitution III; PR #466 review). The planner applies the
  same ID and path-containment checks as `classify_shipment_close_path`, and
  reuses its helpers (`_ARTIFACT_ID_PATTERN`, `_read_artifact_record`,
  `_scan_backlog`, `_is_symlink_or_reparse_point`) instead of new path logic.
  * Every candidate ID, including a literal `source_deliberation_id`, must match
    `_ARTIFACT_ID_PATTERN` before it is used to build a path. A non-matching ID
    goes to `unresolved_references` with `reason_code` `invalid_id` and is never
    resolved, so it never becomes a disposition-set member or a
    `retained_read_error`.
  * Every record path and the supplied `stash_path` must canonicalize inside the
    workspace backlog tree, and must not be (or sit under) a symlink or
    reparse point.
  * A containment failure is a read error. It yields `retained_read_error` with
    `reason_code` `path_escape` or `symlink_or_reparse_point`, never `archive`,
    and the planner still never raises.
* **Tests** (fixture-first; `tests/test_linked_deliberation_disposition_planner.py`):
  * multi-feature manifest;
  * self-reference;
  * an A↔B deliberation cycle;
  * a stash-only referrer (field form and text form);
  * a referrer that is another shipment's member, and one that is named in
    another shipment's description;
  * an archived referrer, which is not counted;
  * an `archive/` record with `status: done`, which is counted;
  * a `queue/` record with `status: archived`, which is not counted;
  * a torn deliberation, which yields `retained_ambiguous`;
  * an explicit-member deliberation, which is excluded (H10);
  * `status: active`, `status: blocked`, and `status: review`, each of which
    yields `retained_live_status` (the `review` fixture has no other referrer,
    proving a deliberation under review is never archived);
  * `status: queued` with no referrer, which yields `archive` (not live);
  * the default call with no `stash_path` argument: a `source_deliberation_id`
    deliberation (the `038-DL` shape) cited only by an entry in
    `<workspace_backlog_dir>/stash.jsonl` yields `retained_shared_reference`
    naming that stash entry, and the same fixture without the entry yields
    `archive`;
  * the default call when `<workspace_backlog_dir>/stash.jsonl` is absent, which
    counts no stash referrer and does not raise;
  * a description-only link, which yields `retained_description_mention`;
  * engine UNVERIFIED, which yields `retained_engine_unverified` for every
    non-archived deliberation;
  * an unresolved ID, which goes to `unresolved_references` with `reason_code`
    `not_found`;
  * a non-deliberation `artifact_type`, which is excluded;
  * links from `task`, `bug`, and `chore` members;
  * a deliberation ID that appears only in a member's Markdown body (not in
    frontmatter), which is found as a description link, and one that appears
    only in another shipment's body, which counts as a live referrer;
  * negative input-safety and read-failure cases. Each asserts the **exact**
    outcome, `reason_code`, and `path`, never merely "no archive":
    * a traversal-shaped `source_deliberation_id` (for example `../x-DL`) goes to
      `unresolved_references` with `reason_code` `invalid_id`, and has no
      disposition record;
    * a `stash_path` outside the backlog tree yields `retained_read_error`,
      `path_escape`, and the supplied stash path, for every disposition-set
      deliberation;
    * a symlink or junction deliberation record yields `retained_read_error`,
      `symlink_or_reparse_point`, and that record's path;
    * a symlink or junction `stash_path` yields `retained_read_error`,
      `symlink_or_reparse_point`, and the stash path;
    * a deliberation record that is not decodable as UTF-8 yields
      `retained_read_error`, `unreadable_file`, and the record path;
    * a deliberation record with invalid-YAML frontmatter yields
      `retained_read_error`, `malformed_frontmatter`, and the record path;
    * a deliberation record with no closing frontmatter delimiter yields
      `retained_read_error`, `body_unseparable`, and the record path;
    * a default `<workspace_backlog_dir>/stash.jsonl` containing a non-JSON line
      yields `retained_read_error`, `malformed_stash_entry`, and the
      workspace-relative stash path;
    * another shipment's record, read by the live-referrer scan, with
      invalid-YAML frontmatter yields `retained_read_error`,
      `malformed_frontmatter`, and that record's path;
  * precedence: a torn deliberation with one unreadable record yields
    `retained_read_error`, not `retained_ambiguous`; an unreadable deliberation
    under engine UNVERIFIED yields `retained_read_error`;
  * every other outcome fixture also asserts that `reason_code` equals the
    outcome value, and `LinkedDeliberationOutcome` has exactly the eight members.
* **Size:** M. **Complexity:** medium. Depends on U1a.

### U2a — P-015 sets, disposition set, engine precondition, INV-12 (policy) — 197.007-T, 197.008-T (203-S), 198.001-T, 198.002-T (204-S)

Files:

* `templates/policies/workflow-policies.md.tmpl`
* `.github/policies/workflow-policies.md`
* `.autoharness/harness-manifest.yaml` (the checksum and note of the
  workflow-policies entry)
* `tests/test_flat_manifest_closure_docs.py`

Changes (amended 2026-09-29, independent review P1-5, P1-6, P1-7, P2 every-member-type,
P3 source relabel):

* **D1a.** `allowed_ids(S)` becomes `closure_scope(S)`. `required_ids(S)` becomes
  `{S} ∪ {qualifying feature members} ∪ {x ∈ items(S) : x not truly archived pre-close}`
  over every manifest item regardless of `artifact_type`.
* **Admission paragraph.** Redefine `validated_linked_deliberations(S)` as the
  **disposition set**, exactly as U1b defines it:
  * every explicit member regardless of type;
  * self and `closure_scope(S)` excluded (H10);
  * existence validated before location;
  * unresolved IDs never halt.

  The link sources are relabelled "the three autoharness-defined link sources
  (frozen from backlogit 1.10.x `linkedDeliberationIDs`; the 1.11.x engine no
  longer uses them for archival)". "References" is defined precisely: each entry
  of the artifact's frontmatter `references` list, scanned as text with the
  matcher. The set enters neither `allowed_ids(S)` nor `required_ids(S)`.
* **INV-1.** Linked deliberations are accounted for only by INV-12.
* **INV-6.** The engine leaves a linked deliberation independent under the
  verified engine line. Its disposition is INV-12.
* **New CASCADE precondition.**
  * `select_close_path` must return CASCADE. The self-hosting implementation calls
    `assess_cascade_engine_semantics`. Other workspaces use an equivalent check:
    a **fresh** probe of the installed backlogit version on **the same surface
    (MCP or CLI) that the close path will invoke**, released builds only.
  * The skill records `probe_surface`, `version`, and `commit`.
  * The policy carries the token ``Verified engine-semantics lines: `1.11` ``.
  * Otherwise select SAFE_CLOSE with `ENGINE_SEMANTICS_UNVERIFIED`.
* **SAFE_CLOSE reliance, reworded (P1-7).** SAFE_CLOSE does not depend on cascade
  semantics, fails closed, and never invokes the cascade. It depends on
  `archive_item` semantics. That is the second verified proposition, and its
  general registry is `8928EC67`. The plan never states that SAFE_CLOSE is
  "always valid".
* **New INV-12 (Linked-deliberation disposition)** is the authoritative text.
  INV-12 is the invariant, meaning the rule. `LinkedDeliberationOutcome` is the
  closed enum of the values the rule assigns (PR #466 review, cycle 5). After the
  **selected** close path's gate passes, the Linked-Deliberation Disposition step
  assigns each disposition-set member exactly one `LinkedDeliberationOutcome`:
  * `archived`
  * `already-archived`
  * `retained_read_error`
  * `retained_engine_unverified`
  * `retained_ambiguous`
  * `retained_live_status`
  * `retained_shared_reference`
  * `retained_description_mention`

  Each outcome carries a `reason_code`, which defaults to the outcome value.
  `retained_read_error` also carries the workspace-relative `path` and a
  read-error reason code from U1b's extensible vocabulary (`path_escape`,
  `symlink_or_reparse_point`, `unreadable_file`, `malformed_frontmatter`,
  `body_unseparable`, `malformed_stash_entry`). A read or containment failure
  yields `retained_read_error` before any later classification. The enum is
  closed; consumers accept unknown reason codes.

  Mutation is a single-artifact, non-cascading archive, and it happens only when
  all of these hold:
  * the engine verdict is VERIFIED;
  * the deliberation is linked from an explicit member's `source_deliberation_id`;
  * the deliberation's own status is not live;
  * it resolves to exactly one record;
  * it has no live referrer.

  Rules around each archive:
  * a hash re-check and a guard re-check come immediately before the archive;
  * verify-after-each comes immediately after it.

  The step as a whole:
  * never widens `closure_scope(S)`;
  * is independent of the close path;
  * reports retained outcomes, which never halt.

  If a verification fails, the step halts with P-005 and never advances to
  post-mode.
* **Supersession note (2026-09-29).** The 155-S linked-deliberation allowance was
  correct for backlogit 1.10.x and is superseded for 1.11.x. Cite `5a4b70dd`, the
  v1.11.0 engine test, and 190-S.
* **History row** `1.28.0 | {{DATE}} | Corrected P-015 | …`. The mirror uses the
  concrete date.

Tests, written first:

* A **policy-only** INV-12 assertion: a new test iterating only the two policy
  files (P1-5). `INVARIANT_TOKENS` stays `INV-1`..`INV-11` until U4, because the
  shared test iterates the skill pair too.
* The flat `allowed_ids(S)` row.
* The absence of `closure_scope(S) ∪ validated_linked_deliberations(S)`.
* `ENGINE_SEMANTICS_UNVERIFIED` and `select_close_path`.
* The verified-line token, parsed, equals the constant.
* The H10 exclusion sentence, the eight-outcome `LinkedDeliberationOutcome`
  vocabulary (including `retained_read_error`), and the `reason_code` sentence.
* The absence of "always valid" for SAFE_CLOSE.
* Rendered-region parity for the edited paragraphs, with an allowlist.

Size M. Complexity medium. Depends on U1a.

### U2b — P-015 close-path gate vs. INV-12 split, P-010 clarification (policy) — 198.003-T..198.006-T; policy parity 198.007-T (204-S)

Added 2026-09-29 (independent review P1-2, P2 P-010, P3 1.10-era scoping). Same
bundle as U2a, plus `tests/test_cascade_close_archived_ids_postcondition.py` for the
policy assertions.

Changes. The design splits the old closure postconditions into two layers:

* the **close-path gate**, evaluated before disposition (INV-10);
* the separately sanctioned **INV-12 post-gate mutation**, with its own
  invariance check.

The paragraph edits:

* **Statement.** Add one sentence. After the selected close path completes, the
  separately sanctioned INV-12 step may archive validated linked deliberations
  individually. This is not closure scope.
* **Required Check.**
  * Delete the clause "a required transition of a
    `validated_linked_deliberations(S)` member … is an expected, in-scope cascade
    mutation".
  * On the CASCADE path the check covers every observed artifact outside
    `allowed_ids(S)` **and** every disposition-set record path. A disposition-set
    member that changes during the cascade is engine drift.
* **Postcondition.** Split into two parts:
  * (a) the close-path gate postcondition, which is the current text with the
    flat sets and is evaluated before disposition;
  * (b) the INV-12 postcondition: only deliberations with the outcome `archived`
    may change after the gate, and each one is verified.
* **Violation Action.** Add `HALT — linked-deliberation disposition failed {id}`
  under the same D6 sequence. There is no automatic rollback of the completed
  closure.
* **Relationship to P-007.** The post-mode deleted-file guard treats verified
  `archived` disposition moves as expected.
* **INV-7.** Add temporal scope. Baseline invariance is evaluated at the
  close-path gate. INV-12 then applies its own check against the disposition
  baseline.
* **INV-10.** Label it "close-path gate postconditions (evaluated before INV-12
  disposition)". Add: INV-12's `archived` deliberations are the only artifacts
  outside `allowed_ids(S)` that may change after the gate, and only through INV-12.
* **Item 7.**
  * The "correctly absent" sentence covers non-feature manifest members only.
    Remove "or a qualifying feature member's validated linked deliberation" and
    "unlike a manifest task item or a qualifying feature's linked deliberation".
  * Correct the `collectArchiveCandidateIDs` description: under 1.11.x there is
    no linked-deliberation append.
* **Evidence-class note.** Two engine propositions hold under the verified line:
  * (1) inert archived descendants, proven by the existing path-scoped
    comparison;
  * (2) 1.11.x leaves linked deliberations independent, proven by the engine
    source at `v1.11.0` L716-751,
    `TestUArchiveCandidateFlat_UnlistedLinkedDeliberationIsUntouched`, and the
    190-S observation.

  `archive_item` single-artifact semantics is a verified-line **assumption** that
  `8928EC67` generalizes.
* **1.10-era scoping (P3).** The engine-rationale rows and INV-11's "under
  backlogit 1.10.1" stay as the observed line, with the note "not re-verified for
  1.11; re-verification is owned by `8928EC67`".
* **P-010 clarification (P2).**
  * Under **Ship MAY**, add: "archive a validated linked deliberation only
    through the P-015 INV-12 Linked-Deliberation Disposition step (and the
    post-merge source-artifact retirement that consumes its report). This is a
    closure lifecycle transition, not creation or modification of deliberation
    content."
  * Qualify **Ship MUST NOT** "Create or modify deliberation … artifacts" with
    "(P-015 INV-12 archival transitions excepted)".

Tests, written first. These are policy assertions in
`CascadeCloseTwoSetGatePolicyTests`. The item-7 tests move out of
`CascadeCloseLinkedDeliberationAllowanceTests`, which U3b replaces.

* Invert `test_item_7_omission_sentence_scoped_to_task_and_linked_deliberation` →
  `test_item_7_omission_sentence_scoped_to_non_feature_members`.
* The Required Check no longer contains "expected, in-scope cascade mutation".
* The two-part Postcondition is present.
* The INV-10 label is present.
* The Evidence-class note names two propositions.
* The P-010 clarification is present.
* Rendered-region parity.

Size M. Complexity medium. Depends on U2a.

### U3a — Skill Step 0(b)/(c): all-member snapshot, engine-semantics gate, close-path selection, re-probe — 198.008-T, 198.009-T (204-S), 199.001-T; engine-line consistency 199.002-T (205-S)

Files: the skill template, the skill mirror, the manifest checksum and note for
the skill mirror, and `tests/test_cascade_close_archived_ids_postcondition.py`.

Changes (amended 2026-09-29, independent review P1-2, P1-3, P2 probe surface, P2
every-member-type, P3 registry, P3 re-probe):

* **Step 0(b).** Snapshot `parent_id` and declared `status` for **every explicit
  manifest member regardless of `artifact_type`**, not only task items. The flat
  `required_ids` needs this.
* **New Step 0(c) sub-step "Engine-semantics gate"**, before the classifier
  result is acted on:
  * **Probe on the same surface the close path will use.** Use MCP
    `backlogit_get_version` with `no_update_check: true`, or the CLI
    `backlogit version --no-update-check --format json`.
  * **Literal wording.** Use literal tool/CLI wording. Do not add an
    `{{OP_…}}` placeholder: the registry's `get_version` entry has no
    `params`/`cli_command` (P3 disposition: literal bypass, no registry change).
  * Record `probe_surface`, `version`, and `commit`.
  * Apply `assess_cascade_engine_semantics` (self-hosting), or the equivalent
    rules: released `X.Y.Z` only, minor line in the token, surface match.
  * A probe failure is `UNVERIFIED`.
* **Close-path selection.** Use `select_close_path(classifier_decision, engine_decision)`,
  or its stated 2×2 table.
  * **SAFE_CLOSE selected** now explicitly includes `ENGINE_SEMANTICS_UNVERIFIED`.
  * **CASCADE selected** ends with "then continue to the Linked-Deliberation
    Disposition step", replacing "then proceed to post-mode" (L555-559, P1-2).
* **Pre-invocation revalidation.**
  * Run a fresh re-probe on the same surface.
  * Compare the raw `version`, `commit`, and `probe_surface`, and the verdict.
  * Any difference, **or a re-probe failure**, yields
    `HALT — cascade pre-invocation revalidation drift detected` and P-005.
  * A re-probe failure halts rather than falling back to SAFE_CLOSE (P3
    disposition). Falling back after a CASCADE verdict would be the prohibited
    CASCADE→SAFE_CLOSE substitution. The halt is non-mutating and
    operator-recoverable.

Tests, written first. Add a new class `CascadeCloseEngineSemanticsGateTests`
asserting:

* `Engine-semantics gate`, `ENGINE_SEMANTICS_UNVERIFIED`, `no_update_check`,
  `probe_surface`, and `select_close_path`;
* the verified-line token equals the constant;
* the re-probe compares version, commit, and surface;
* a re-probe failure halts;
* Step 0(b) says "every explicit manifest member";
* the CASCADE routing names the disposition step;
* rendered-region parity.

`CascadeCloseLinkedDeliberationAllowanceTests` stays untouched here; U3b replaces
it.

Size M. Complexity medium. Depends on U2b.

### U3b — Skill disposition snapshot, INV-6 scoping, transition-log preamble, re-collection — 199.003-T..199.006-T (205-S)

Split from U3 on 2026-09-29 (independent review P2 sizing, P2 torn, P1-2). Same
bundle as U3a.

* **Replace "Linked-deliberation snapshot extension (155-S)"** with
  "Linked-deliberation disposition snapshot". It is computed on every run, on both
  paths, using U1b's set definition. It records, per deliberation:
  * link kinds and linking members;
  * every record path;
  * the declared status;
  * the SHA-256 per record path.

  Handling rules:
  * Existence is validated before location.
  * A torn or duplicate deliberation becomes `retained_ambiguous`, with no halt.
    Every record path is still fingerprinted for U4's byte-identity check.
  * An unresolved ID goes to `unresolved_references`, with no halt.
  * `RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS` / `RECONCILE_FAIL_SNAPSHOT_MISSING` apply
    to manifest members only.
  * The text states that the engine does not archive these under the verified
    line (`5a4b70dd` / v1.11.0). `linkedDeliberationIDs` may appear only inside an
    explicit superseded-provenance sentence.
* **INV-6 scoping sentence (L444-449).** The engine leaves linked deliberations
  independent. Their disposition is INV-12.
* **Transition-log preamble (L737-760, P1-2).**
  * Drop "or a qualifying feature member's validated linked deliberation" from
    the correctly-absent sentence.
  * Change "a task item or linked deliberation can" to "a non-feature manifest
    member can".
* **Pre-invocation re-collection (L822-843).** Keep it. It compares link kinds,
  record paths, declared statuses, and SHA-256.

Tests, written first. Replace `CascadeCloseLinkedDeliberationAllowanceTests`
(minus the item-7 tests that U2b moved) with
`CascadeCloseLinkedDeliberationFlatSemanticsTests`, asserting:

* the exact link sources;
* existence validated before location;
* a torn deliberation yields `retained_ambiguous`, not a halt;
* `unresolved_references`;
* SHA-256;
* no blanket allowance;
* `linkedDeliberationIDs` appears only in a superseded sentence;
* the H10 exclusion;
* the scoped transition-log sentence;
* rendered-region parity.

**Retain unchanged**:

* `test_allowed_ids_bullet_includes_linked_deliberations`;
* `test_required_ids_bullet_extended_for_linked_deliberations`;
* the Quality Criteria "never a blanket allowance" assertion.

U4 inverts all three.

Size M. Complexity medium. Depends on U3a.

### U4 — Skill Cascade Close: flat postcondition sets and linked-deliberation byte-identity — 199.007-T..199.010-T; skill parity I 199.011-T (205-S)

Files: the same bundle as U3a.

Changes (amended 2026-09-29, independent review P1-5, P2 every-member-type, P2
test ownership):

* **Step 3.**
  * `allowed_ids` becomes `closure_scope(S)`: **every manifest item regardless of
    `artifact_type`**, plus the shipment record.
  * `required_ids` is the shipment record and the qualifying features
    (unconditionally), plus every other manifest item that was not truly
    archived in the Step 0(b) all-member snapshot.
  * Remove the linked-deliberation clauses and the `027-DL` tolerance example.
    Keep the non-feature tolerance and the feature/shipment non-tolerance
    paragraphs.
  * Add: "a disposition-set deliberation in `archived_ids` fails the
    unexpected-artifact check — engine drift". The H10 carve-out applies: an
    explicit-member deliberation is an ordinary `allowed_ids` member.
* **Step 5.** Every disposition-snapshot record path must be byte-identical
  (location plus SHA-256) after the cascade. Otherwise halt with
  `HALT — cascade modified linked deliberation {id} — engine semantics drift` and
  P-005.
* **Steps 6 and 7.** The report and the gate cover the engine-semantics decision
  (with `probe_surface`, `version`, and `commit`), the disposition snapshot, and
  the byte-identity outcome. `CLOSED` hands off to the Linked-Deliberation
  Disposition step.
* **Quality Criteria (L1204)** and **Vocabulary summary (L1163-1177)** are
  rewritten to match, and they add `INV-12`.
* **`INVARIANT_TOKENS` becomes `range(1, 13)`** in
  `tests/test_flat_manifest_closure_docs.py`, now that both skill files contain
  INV-12 (P1-5).

Tests, written first:

* Invert the two step-3 tests retained by U3b, and the QC blanket-allowance
  assertion.
* Rewrite `CascadeCloseTwoSetGateScenarioTests.test_scenario_2_omitted_truly_pre_archived_tasks_gate_passes`:
  drop the linked-deliberation/`027-DL` example and scope it to non-feature
  manifest members.
* Assert the drift halt string and the H10 carve-out.
* Assert INV-12 in the summary.
* Rendered-region parity.

Size M. Complexity medium. Depends on U3b.

### U5a — Skill Linked-Deliberation Disposition section — 200.001-T..200.006-T (206-S)

Files: the same bundle as U3a, plus the new
`tests/test_shipment_reconcile_linked_deliberation_disposition.py`.

Changes (amended 2026-09-29, independent review P1-6, P1-7, P2 baseline, P2 planner,
P3 TOCTOU, P3 forever-live, P2 advisories). Add a new
`### Linked-Deliberation Disposition (P-015 INV-12)` subsection:

0. **Inputs.**
   * the selected close path and its reason;
   * the Step 0(c) engine-semantics decision;
   * the disposition snapshot;
   * the path-specific baseline.
1. **Plan.** `compute_linked_deliberation_disposition` (U1b) produces the planned
   outcome per deliberation. Other workspaces apply the same stated rules and
   precedence. The guard references "the Step 0(c) matcher" by name and never
   restates the regex, so the matcher literal count in the skill stays 2 (P2).
   When the engine is UNVERIFIED, every non-archived deliberation is
   `retained_engine_unverified` and nothing is mutated, on any path (P1-7).
2. **Disposition baseline (P2).**
   * **Components.**
     * (i) The path-specific set: the safe-close observation-set fingerprints,
       or the CASCADE out-of-manifest descendant fingerprints.
     * (ii) The disposition snapshot.
     * (iii) A pre-disposition
       `git status --porcelain -- "{{BACKLOG_DIRECTORY}}/"` capture.
     * The `closure_scope(S)` IDs already archived by this run are subtracted.
   * **Allowed `ArchiveItem` side effects** (verified at `v1.11.0`
     `internal/core/archive.go`):
     * the target's own queue→archive move;
     * the frontmatter keys `status`, `archived_status`, and `archived_from`;
     * the gitignored item event log (`{{BACKLOG_DIRECTORY}}/logs/`) and index
       (`{{BACKLOG_DIRECTORY}}/*.db*`);
     * lock and hook-queue files.
   * `ArchiveItem` does not write `stash.jsonl` or `archive/stash.jsonl`. Any
     change there, or to any other path, violates the baseline.
3. **Archive.** Work through each planned `archive` in ascending ID order.
   * Immediately before each call, re-run the hash check **and** the
     shared-reference guard for that ID (P3 TOCTOU).
   * A hash mismatch halts with no mutation. A new referrer becomes
     `retained_shared_reference` with no mutation.
   * Archive through `{{OP_ARCHIVE_ITEM_MCP}}` (CLI `backlogit archive {id}`). No
     cascade flag. Use the probed surface.
4. **Verify-after-each.** All of the following must hold:
   * the queue copy is absent, and the archive copy is present exactly once;
   * `status: archived`;
   * `archived_status` equals the snapshotted declared status;
   * frontmatter compared **semantically** (parsed YAML, because `ArchiveItem`
     re-serializes) is equal except for the three engine keys;
   * the body is **byte-exact**;
   * disposition-baseline invariance holds.

   Any failure yields `HALT — linked-deliberation disposition failed {id}`, P-005,
   and the D6 sequence. There is no retry and no rollback of the completed
   closure. The run does not advance to post-mode, and a torn disposition is
   never committed (H4).
5. **Report.** Record:
   * `linked_deliberation_disposition: [{id, link_kinds, linking_members, outcome, reason_code, path, referrers, pre_sha256, post_sha256, archived_status}]`,
     where `outcome` is a `LinkedDeliberationOutcome` value, `reason_code` is
     always present and copied verbatim from the planner, and `path` is present
     for `retained_read_error`;
   * `unresolved_references` (`{id, reason_code}`);
   * the durable advisories `ENGINE_SEMANTICS_UNVERIFIED` /
     `ENGINE_LINE_UNVERIFIED_ADVISORY`, carried into the closure summary (P2);
   * a `stranded_linked_deliberation` advisory listing every `retained_*`
     outcome, so a deliberation that stays live for a long time is visible to
     the operator (P3).
6. **Gate.** When every deliberation has exactly one outcome and every
   `archived` outcome is verified, the result is
   `recommendation: DISPOSITION_COMPLETE`. Continue to post-mode.

Also:

* the H7 action-risk statement;
* the statement that this step is the sanctioned successor to the 190-S
  operator-approved deviation.

Tests, written first, assert:

* the section exists;
* the eight `LinkedDeliberationOutcome` values, including `retained_read_error`,
  and the `reason_code` and `path` report fields;
* the halt string and the report field;
* the baseline definition, including `git status --porcelain`;
* semantic frontmatter comparison with a byte-exact body;
* the allowed side-effect paths, with the stash files excluded;
* engine UNVERIFIED means no mutation;
* the guard re-runs before each archive;
* no cascade flag;
* `compute_linked_deliberation_disposition` is cited;
* the matcher literal count is 2;
* rendered-region parity.

Size M. Complexity medium. Depends on U4 and U1b.

### U5b — Skill hand-offs, post-mode, safe-close wording, scenario matrix, closing negative grep — 200.007-T..200.012-T (206-S); skill parity II + closing grep 195.017-T (201-S)

Split from U5 on 2026-09-29 (independent review P1-2, P1-7, P2 sizing). Same bundle
as U5a.

* **Hand-offs.**
  * Safe-close step 10 `recommendation: CLOSED` continues to the
    Linked-Deliberation Disposition step. The actual token is `CLOSED`, not
    `PROCEED`.
  * Check that the Step 0(c) CASCADE routing (U3a) and Cascade step 7 (U4) are
    consistent.
* **Behavioral Constraints "Manifest-scoped mutation only" (L229)** and **safe-close
  step 1 "only artifacts"**: these are the only artifacts that safe-close steps
  1–10 may move or archive. The INV-12 disposition step is separately sanctioned.
* **Safe-close step 8 and the INV-11 summary (P1-7).** Change to "while Step 0(c)'s
  **selected** close path is not `CASCADE`".
* **Post-mode.**
  * Step 2's per-item check covers disposition `archived` outcomes.
  * Step 3's deleted-file guard treats their moves as expected.
  * Retained outcomes never change the step 5 gate.
* **Scenario-matrix rows:**
  * (a) classifier CASCADE + `ENGINE_SEMANTICS_UNVERIFIED` → SAFE_CLOSE →
    disposition `retained_engine_unverified`;
  * (b) shared reference retained;
  * (c) engine drift (a linked deliberation archived or modified by the cascade)
    → halt;
  * (d) description-only mention → `retained_description_mention`;
  * (e) torn deliberation → `retained_ambiguous`;
  * (f) an unreadable, malformed, or containment-failing deliberation record or
    stash input → `retained_read_error` with its `reason_code` and `path`
    (never archived, never a halt).
* **Quality Criteria** bullets.
* **Closing negative grep (P1-2).** Add
  `test_no_stale_linked_deliberation_cascade_wording` over the policy, skill,
  Ship agent, and `operational-closure` pairs. It asserts these are absent:
  * "expected, in-scope cascade mutation";
  * "may be live/required";
  * "`CASCADE` archiving it is expected";
  * "appends, for every explicit qualifying feature member";
  * a "correctly absent" sentence naming a linked deliberation;
  * "always valid" applied to SAFE_CLOSE;
  * any "Proceed to post-mode" directly after a close-path `CLOSED`.

Tests, written first: the items above, plus rendered-region parity.

Size M. Complexity medium. Depends on U5a.

### U6 — Ship agent close-path bullets, step 1.e gate, Role Boundary — 195.006-T, 195.013-T (201-S)

Files:

* `templates/agents/_ship.agent.md.tmpl`
* `.github/agents/_ship.agent.md`
* `.autoharness/harness-manifest.yaml` (the checksum and note of the Ship agent
  entry)
* `tests/test_ship_safe_close_pointer.py` / `tests/test_flat_manifest_closure_docs.py`
  (`SHIP_AGENT_CONTRACT_FILES`)

Changes (amended 2026-09-29, independent review P1-2, P1-4, P2 P-010):

* **CASCADE bullet** (template L825-837, mirror L716-730):
  * Replace the "never `validated_linked_deliberations(S)`, which the engine
    reaches … may be live/required for `CASCADE` to archive" clause with flat
    wording.
  * Add "CASCADE also requires the skill's engine-semantics gate to return
    `VERIFIED` (via `select_close_path`)".
* **SAFE_CLOSE bullet** (template L816-824, mirror L706-715). Add "then the
  skill's Linked-Deliberation Disposition step".
* **Step 1.e commit gate** (template L867-871; the mirror's equivalent commit
  gate). Commit only after the close path returned `CLOSED`, the disposition step
  returned `DISPOSITION_COMPLETE` (never after a disposition `HALT`), and
  post-mode returned `PROCEED`.
* **Role Boundary Planning row** (template L43, mirror L52). Add "(P-015 INV-12
  archival transitions of validated linked deliberations excepted)".
* The mirror keeps its workspace-specific structure. The edits are phrase-level.

Tests, written first: phrase-level semantic parity. The required phrases are
present, and the withdrawn phrase is absent, in both files.

Size S. Complexity low. Depends on U5b.

### U6b — Ship post-merge Step 7 and operational-closure consume the disposition report — 195.012-T, 195.014-T..195.016-T (201-S)

Added 2026-09-29 (independent review P1-1).

Files:

* `templates/agents/_ship.agent.md.tmpl` (Step 7, L889-893)
* `templates/skills/operational-closure/SKILL.md.tmpl` and
  `.github/skills/operational-closure/SKILL.md` (Step 2 checklist, L84)
* `.autoharness/harness-manifest.yaml` (the checksum and note of the
  `operational-closure` mirror, and of the Ship agent mirror if it is touched)
* one pinning test file

Changes:

* **Ship Step 7 (template).**
  * The `source_deliberation_id` bullet no longer calls `backlogit_archive_item`
    independently. It reads the shipment's `linked_deliberation_disposition`
    report.
    * If the outcome is `archived` or `already-archived`, record it and skip.
    * If the outcome is any `retained_*`, including `retained_read_error`,
      **never archive**. Record the outcome verbatim with its `reason_code`
      (and `path`, when present). An unknown `reason_code` is accepted and
      recorded verbatim.
  * A deliberation that is absent from the report falls into one of two cases.
    Either the report predates this contract, or the link was out of the
    disposition set. In both cases, record `skipped_not_in_disposition_report`
    and never archive.
  * The `backlogit_archive_item` and `source_deliberation_id` tokens stay present,
    as `verify_workspace.py`'s `ship_source_artifact_cleanup` check requires.
* **Dogfood Ship mirror.** It has no Step 7 deliberation retirement. There is
  nothing to realign beyond U6's Role Boundary edit. A test asserts that the
  mirror still does not archive deliberations outside INV-12.
* **`operational-closure` Step 2 "Source artifact cleanup" outcomes list.**
  * Existing outcomes: archived; skipped because already archived; skipped
    because not found; `none`.
  * Add every `retained_*` outcome (including `retained_read_error`), plus
    `skipped_not_in_disposition_report`.
  * The `source_deliberation_id` outcome and its `reason_code` (and `path`, when
    present) are copied from the disposition report, never re-derived. The
    `Source artifact cleanup`, `source_stash_id`, and
    `source_deliberation_id` tokens stay present (the
    `closure_source_artifact_cleanup` check).

Tests, written first:

* Step 7 names `linked_deliberation_disposition`, "never archive" for
  `retained_*`, and records the `reason_code`.
* `operational-closure` lists `retained_shared_reference` and
  `retained_read_error`.
* The verify-workspace tokens are still present.
* Rendered-region parity for `operational-closure`; phrase-level parity for the
  Ship agent.

Size S. Complexity medium. Depends on U6.

### U7 — Docs: compound learning, supersession notes, re-verification runbook — 195.007-T, 195.018-T, 195.019-T (201-S)

Files:

* `docs/compound/2026-09-29-backlogit-1-11-flat-cascade-leaves-linked-deliberations.md`
  (new)
* Supersession notes appended only, with every test-pinned sentence kept
  byte-identical, to:
  * `docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
  * `docs/compound/2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md`
  * `docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md`
  * `docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md`
* Check `docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md`.
  Append a note only if it asserts linked-deliberation cascade archival.

Changes (amended 2026-09-29, independent review P2 U7, P2 runbook):

* The learning's frontmatter uses `problem_type: tool_version_behavior_drift`,
  and `source:` is the file's own path.
* The learning lists the four drift occurrences.
* The rule: every engine-behavior assumption carries a verified version line, and
  CASCADE and disposition mutation fail closed outside that line.
* **Re-verification runbook for a new backlogit minor line.**
  * **Engine functions to re-read at the new tag:**
    * `collectArchiveCandidateIDs` and `archiveItems` in
      `internal/core/shipment_lifecycle.go`;
    * `ArchiveItem` in `internal/core/archive.go`, including its frontmatter-key
      set.
  * **Engine tests to confirm:** `TestUArchiveCandidateFlat_*`.
  * **Surfaces to bump together:**
    * the constant;
    * the policy and skill tokens;
    * this learning.
  * The runbook requires the `8928EC67` deliberation first.
* The learning points to `8928EC67` and `62C1E11E`.

Exit:

* `markdownlint` is clean.
* There are no broken relative links.
* `tests/test_docs_compound_frontmatter_contract.py` and
  `tests/test_docs_frontmatter_decodes.py` are green.

Size S (was XS). Complexity low. Depends on U5b.

## Dependency Graph

```text
U1a(001) ──► U1b(008) ─────────────────────────────┐
   └──► U2a(002) ──► U2b(009) ──► U3a(003) ──► U3b(010) ──► U4(004) ──► U5a(005) ──► U5b(011) ──► U6(006) ──► U6b(012)
                                                                                  └──► U7(007)
```

The graph has no cycles. U5a depends on both U4 and U1b. U2a-U6b edit the same
policy, skill, and Ship files in sequence, so serial order avoids conflicting
edits. The unit-level graph above is the logical order; the task-level edges
(58 tasks) are in Resulting units and order, and the units are delivered as six
chained shipments, one PR each (see Multi-shipment delivery above):

```text
190-S (shipped)
  ◀── 202-S  [slice 1, 196-F]   8 tasks
        ◀── 203-S  [slice 2, 197-F]   8 tasks
              ◀── 204-S  [slice 3, 198-F]   9 tasks
                    ◀── 205-S  [slice 4, 199-F]  11 tasks
                          ◀── 206-S  [slice 5, 200-F]  12 tasks
                                ◀── 201-S  [slice 6, 195-F, terminal]  10 tasks (also keeps the satisfied 190-S edge)
                                      ◀── 198-S (unchanged edge)
```

`X ◀── Y` means Y blocks on X. The chain is the transitive reduction; no
redundant direct edges are needed.

**Sequencing vs. 198-S (amended 2026-09-29; operator decision 2, 2026-09-29T12:54;
guard frequency amended in PR #466 cycle 8).**
The DAG carries `198-S blocks-on 201-S` (`backlogit dep add 198-S 201-S --type blocks`),
and `198-S` is not in the `dag-readiness` ready set. `201-S` is the terminal
shipment of the chain, so condition 1 below is unchanged by the re-split. The
fail-closed guard stays as defense in depth. Ship runs it at three points of
**every** shipment of the chain (`202-S`..`206-S`, `201-S`): at claim (before the
first task), before the P-014 PR-ready gate, and immediately before merge. It is a
concrete check with three conditions:

1. `backlogit dep list 198-S` still lists `198-S → 201-S (blocks)`.
2. `198-S` is still `queued`.
3. `git --no-pager log --oneline origin/main --grep 192-F --grep 198-S --since 2026-09-29`
   shows no 192-F/198-S implementation merge.

If any condition fails, halt with `SCOPE_GAP — 198-S evaluator requires realignment`
and return to Stage (P-021). Never realign the 198-S evaluator ad hoc. The 198-S
re-plan is captured as a P-021 C2 stash entry (see the Independent review
amendments).

## Decisions and Rationale

* **The gate is a separate function, the classifier is unchanged, and composition
  is executable.** 198-S's A2/A3 and the existing classifier tests stay stable.
  `select_close_path` (U1a) is the single composition point, and the skill cites
  it (P1-3).
* **The gate verifies at minor-line granularity, released builds only, on the
  invoking surface.** A semver range admits `1.12.0-rc1`. Pseudo-versions and
  `+dirty` builds may carry unreleased engine changes. The MCP server and the CLI
  may be different builds (D4a).
* **Fail closed to SAFE_CLOSE, not HALT.** SAFE_CLOSE does not depend on cascade
  semantics and never invokes the cascade. It still depends on `archive_item`
  semantics. That dependency is covered by the same verified line, and its
  generalization is `8928EC67` (P1-7).
* **Disposition is path-independent but engine-gated.** It runs after either
  path, and it mutates only under a VERIFIED engine line (P1-7).
* **Auto-archive only `source_deliberation_id` links; retain on any live
  reference.** A description or `references` mention is weak provenance (195-F
  mentions `034-DL` incidentally), so it is report-only. Referrers include work
  items, other unshipped shipments, and active stash entries. Retention is the
  non-mutating fail-safe (P1-6).
* **Step 7 consumes the disposition report.** One archiver, one guard (P1-1).
* **Parity bundles with rendered-region parity** (P1-4). Checksums are refreshed
  in the same unit that edits the mirror, so the suite is never red between
  tasks.

## Risks and Caveats

| Risk | Likelihood | Mitigation |
|---|---|---|
| Queued `198-S` implements the stale sets in code | Low (was high) | DAG edge `198-S blocks-on 201-S` (operator decision 2); a three-point sequencing guard; the re-plan stash entry |
| Merge overlap with `169-S` / `171-S` on skill Step 0 | Medium | Text-only rebase by whichever lands second. Each unit's parity tests catch mismatches |
| Version probe output shape changes | Low | The MCP `version` field and the CLI `--format json` are both structured. Anything unparseable is `UNVERIFIED` |
| A 1.11.x patch reintroduces linked archival | Low | U4's byte-identity halt and the unexpected-artifact halt |
| Retained deliberations stay live indefinitely | Medium | A `stranded_linked_deliberation` advisory in every closure summary. The operator or Stage decides |
| An explicit non-task, non-feature member (for example a deliberation) that is not terminal at close trips the missing-required halt | Low | Fail-closed, and correct. Option E (deliberations as members) was rejected in 038-DL |
| The skill grows further (already about 1,270 lines) | Certain | U3b/U4 *replace* the 155-S text. Compaction is out of scope |
| The dogfood closure of this very shipment exercises the new step | Intended | See Runtime Verification |

## Plan Hardening Signals

* **Public API, schema, or contract change: PRESENT.** P-015 policy, the
  shipment-reconcile and `operational-closure` skills, the Ship agent contract, and
  new public functions in `autoharness.gates.shipment_closure`.
* **Security, auth, permission, or compliance: ABSENT.** No trust boundary
  changes. The version probe is a local read.
* **Migration, destructive action, or irreversible step: PRESENT.** The
  disposition step archives backlog artifacts during closure.
* **External integration or dependency: PRESENT.** Behavior is keyed to the
  installed backlogit engine version and surface.
* **High runtime, rollout, or rollback risk: PRESENT (moderate).** Every future
  shipment closure runs through the edited contract.

Requires plan hardening: yes

## Runtime Verification and Closure

* **U1a/U1b** change a library surface only, with no CLI. Proof: their unit tests
  plus the full existing suite (`tests/test_shipment_closure_classification.py`
  unchanged and green).
* **U2a-U6b** change the agent-facing contract. Proof: the pinning tests, the
  rendered-region and phrase-level parity assertions, the refreshed checksums, and
  `autoharness verify-workspace` clean on the dogfood workspace.
* **Transition-window closures (PR #466 cycle 8; rules T1–T5 in Multi-shipment
  delivery).** `202-S` closes under the pre-195 contract, which is safe because
  its slice is inert code with no runtime caller and, under T2, carries no
  deliberation linkage. `203-S` closes through SAFE_CLOSE with
  `ENGINE_SEMANTICS_UNVERIFIED` (T3). `204-S` and `205-S` close with no
  deliberation mutation and record the transition-window `all retained`
  disposition (T4). `206-S` is the first closure with INV-12; under T2 its
  disposition set is empty (T5).
* **Operational closure of `201-S` (live proof; exhaustive expectations, amended
  2026-09-29; moved to the terminal shipment in PR #466 cycle 8).** The
  post-merge closure of `201-S` (slice 6, terminal) is the first live run of the
  full realigned contract. Its members are `195-F` and the ten slice-6 tasks
  (`195.006-T`, `195.013-T`, `195.012-T`, `195.014-T`..`195.017-T`, `195.007-T`,
  `195.018-T`, `195.019-T`), whose bodies carry no deliberation IDs, so the
  disposition set comes from `195-F` alone. On backlogit 1.11.0 (released
  build), the expected run is:
  * the engine-semantics gate reports `VERIFIED (1, 11)`, with `probe_surface`
    equal to the invocation surface;
  * the classifier returns CASCADE for the flat manifest, and `select_close_path`
    returns CASCADE;
  * the cascade leaves every disposition-set record byte-identical;
  * the disposition outcomes are:
    * `034-DL` (mentioned in the `195-F` description; already `archived`) →
      `already-archived`;
    * `038-DL` (`195-F` `source_deliberation_id`) → `retained_shared_reference`
      while active stash entries that cite it (`8928EC67` and the 2026-09-29
      follow-up entries) remain active, found through the default `stash_path`
      (U1b), otherwise `archived`, with
      `archived_status: queued`;
    * `019-DL` and `027-DL` are no longer mentioned in any `201-S` member's
      description after the re-split, so they are expected outside the
      disposition set; `already-archived` for either is also a pass;
    * any other mention-only deliberation → `retained_description_mention`;
  * `operational-closure` "Source artifact cleanup" copies the `038-DL` outcome
    from the report. The dogfood Ship mirror has no second archiver.

  Any correctly reported outcome from the list above is a pass. Any halt goes to
  operator review, never to an ad hoc deviation.
* **Rollback trigger.** A disposition halt or a drift halt on any closure.
  Recovery: revert the offending shipment's merged PR, then use SAFE_CLOSE plus a
  manual archive under an explicit operator deviation, as in 190-S. Later
  shipments of the chain are blocked on it, so none of them has merged at that
  point. **Owner:** Ship, for closure. Stage, for contract follow-ups.

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

## Independent review amendments (2026-09-29)

An independent, multi-reviewer plan review ran on 2026-09-29, after harvest and
before any Ship claim (operator decision: independent plan review before Ship).
Each reviewer ran in a separate context, and none authored the plan. This section
records the verdicts, how each finding was resolved in this plan, and what the
plan still does not cover. The unit text above is the authoritative resolution;
this section only indexes it.

### Reviewer verdicts

| Reviewer | Verdict | P0 | P1 raised (consolidated IDs) |
|---|---|---|---|
| Architecture Strategist | PASS_WITH_CHANGES | 0 | P1-2, P1-3, P1-4 |
| Correctness Reviewer | PASS_WITH_CHANGES | 0 | P1-6 |
| Scope Boundary Auditor | PASS_WITH_CHANGES | 0 | P1-7 |
| Schema-CLI-Docs Coupling Reviewer | PASS_WITH_CHANGES | 0 | P1-1, P1-2, P1-4, P1-5 |

Consolidated result: 0 P0, 7 P1, 17 P2, 11 P3. All seven P1 findings are resolved
in this plan. No finding required a change to the chosen option (038-DL Option B).

### P1 findings and resolutions

| ID | Finding (short) | Resolution | Re-check (plan section) |
|---|---|---|---|
| P1-1 | Ship post-merge Step 7 and `operational-closure` "Source artifact cleanup" already archive `source_deliberation_id` deliberations with no shared-reference guard, which would defeat INV-12 retention | New unit U6b (195.012-T): Step 7 and `operational-closure` consume the `linked_deliberation_disposition` report and never archive a `retained_*` deliberation. The problem statement is corrected | Problem Frame (corrected bullets); U6b; Runtime Verification (`038-DL` expectation) |
| P1-2 | Stale P-015, skill, and Ship regions contradict the new drift halt (Required Check, Postcondition, INV-7, INV-10, item 7, transition-log preamble, Step 0(c) routing, `CLOSED` hand-off, step 1.e) | U2b (195.009-T) splits the close-path gate from the INV-12 post-gate mutation. U3a routes CASCADE to disposition. U3b fixes the transition-log preamble. U5b fixes the hand-offs and adds the closing negative grep. U6 adds the SAFE_CLOSE bullet and the step 1.e disposition gate | U2b; U3a (Close-path selection); U3b; U5b (Hand-offs, Closing negative grep); U6 |
| P1-3 | No executable composition point for classifier plus engine gate; queued 198-S A1 validator conflicts | `select_close_path` in U1a is the single composition point, and the skill cites it. 198-S now blocks on 201-S, and its re-plan is stash entry `1263B218` | U1a (`select_close_path`, Runtime callers); Dependency Graph (Sequencing vs. 198-S) |
| P1-4 | Byte-parity tests between template and mirror are unimplementable (placeholders, `7F9CB5E9`, structural Ship divergence) | Rendered-region parity for the policy and skill pairs; phrase-level parity for the Ship pair; machine-readable token ``Verified engine-semantics lines: `1.11` `` parsed against the constant | Implementation Units (Parity method); U2a and U3a tests |
| P1-5 | Extending `INVARIANT_TOKENS` to INV-12 in U2 turns the suite red, because the shared test also iterates the skill pair | U2a adds a policy-only INV-12 test. `INVARIANT_TOKENS` becomes `range(1, 13)` in U4, after both skill files gain INV-12 | U2a (Tests); U4 (`INVARIANT_TOKENS`) |
| P1-6 | The shared-reference guard misses live referrers (active stash entries, other unshipped shipments, shipment descriptions) and over-matches incidental mentions | U1b counts work items, other shipments, and active stash entries; retains on a live deliberation status; auto-archives only `source_deliberation_id` links; description-only mentions become `retained_description_mention` (report-only) | U1b (Live referrers, Planned outcome); U2a (INV-12) |
| P1-7 | Disposition can recreate the 190-S scenario on an unverified engine; "SAFE_CLOSE always valid" is wrong | Disposition reads the Step 0(c) engine verdict; UNVERIFIED means `retained_engine_unverified` and no mutation on any path. The wording is corrected, and safe-close step 8 / INV-11 refer to the *selected* path. The scenario row is added | U1b (outcome 4); U2a (SAFE_CLOSE reliance, reworded); U5a step 1; U5b (Safe-close step 8, Scenario-matrix row a); Decisions and Rationale |

### P2 dispositions

All 17 P2 findings are applied in the plan.

| P2 finding | Disposition | Where |
|---|---|---|
| Probe on the same surface as the invocation; record the commit | Applied | U1a (Same surface); U3a (probe, re-probe compares commit) |
| Pseudo-versions and `+dirty` builds | Applied: released builds only | U1a (Released builds only; tests 2) |
| Regex hardening (`fullmatch`, ASCII digits, trailing newline, subclass) | Applied | U1a (Type, Parse; tests 4) |
| Undefined disposition baseline | Applied | U5a step 2 |
| Self-reference, A↔B cycles, historical mentions | Applied | U1b (Excluded, Never counted; tests) |
| Torn or ambiguous out-of-scope deliberation | Applied: `retained_ambiguous`, existence before location | U1b; U3b |
| Sets over every manifest item regardless of `artifact_type` | Applied | U1a docstring; U2a D1a; U3a Step 0(b); U4 step 3 |
| H1 disposition set over every explicit member type | Applied (amends H1); `stranded_linked_deliberation` kept as an advisory, not as a scope-out | U1b; U5a step 5 |
| Pure read-only planner with fixture tests first | Applied: new unit U1b (195.008-T) | U1b |
| Test ownership (item-7 tests, scenario 2, matcher count) | Applied | U2b; U4; U5a |
| 198-S sequencing guard at PR-ready and pre-merge | Applied, plus DAG edge `198-S blocks-on 201-S` | Dependency Graph |
| P-010 versus INV-12 archiving | Applied | U2b (P-010 clarification); U6 (Role Boundary) |
| U7 supersession set, frontmatter `source:`, exit tests | Applied | U7 |
| Re-verification runbook; durable unverified advisories | Applied | U7; U5a step 5 |
| Operator-goal coverage and `8928EC67` hard trigger | Applied | Operator goal coverage (below); stash `8928EC67` |
| Sizing: U3 and U5 exceed the 2-hour rule | Applied: split into U3a/U3b and U5a/U5b | U3a, U3b, U5a, U5b |
| U1 function has no runtime caller | Applied: callers named; prose/regex parity test | U1a (Runtime callers; tests 7) |

### P3 dispositions

| P3 finding | Disposition |
|---|---|
| Re-probe failure should fall back to SAFE_CLOSE | Declined with rationale: after a CASCADE verdict, falling back is the prohibited CASCADE→SAFE_CLOSE substitution. The halt is non-mutating and operator-recoverable (U3a) |
| Relabel the three link sources as autoharness-defined; define "references" | Applied (U2a admission paragraph) |
| Exhaustive live-proof expectations | Applied (Runtime Verification and Closure) |
| Guard TOCTOU | Applied: guard and hash re-check before each archive (U5a step 3) |
| One PR, no closure on intermediate commits | Applied (Implementation Units, Single PR); superseded in PR #466 cycle 8 by Multi-shipment delivery (T1–T5) |
| Retained deliberations may stay live forever | Applied: `stranded_linked_deliberation` advisory (U5a step 5; Risks) |
| Separate `engine_semantics.py` module | Deferred to `8928EC67` (D7); U1a keeps the names module-local |
| Registry `get_version` lacks params / `cli_command` | Applied as literal bypass, no registry change (U3a) |
| Scope 1.10-era rationale rows and INV-11 claims | Applied (U2b, 1.10-era scoping) |
| U1 pre-step repository grep | Applied (U1a Pre-step) |
| 195-F description says H1-H9 | Applied: 195-F description updated (H1-H10, amendments, corrected problem statement, unit list) |

### Superseded statements

* The Plan Hardening result sentence "No unit needed splitting, because H1-H8 fit
  inside the existing units' scope" is superseded. U1, U2, U3, and U5 were split,
  and U6b was added.
* H1 ("explicit feature members of `items(S)`") is amended by U1b to every
  explicit member regardless of `artifact_type`.
* In 038-DL, D3, D4, D8, and D9 are amended by D3a, D4a, D8a, and D9a (see the
  decision record).
* PR #466 cycle 8 (operator decision "A + amendment", 2026-09-29): the "Single
  PR" rule is superseded by Multi-shipment delivery (T1–T5). The per-unit
  "Size … Complexity … Depends on …" lines at the end of each unit and the
  original twelve-row task table are superseded by the 58-task table below. The
  unit headings name the real task IDs. `038-DL`'s historical text is left
  unchanged by operator decision; this plan's task table is the authoritative
  ID map for any retired `195.00x-T` ID that 038-DL still names.

### Resulting units and order

Amended in PR #466 cycle 8: the 2-hour re-split (operator decision 2026-09-29,
binding A). Every task is size `S` (`size_source: agent`,
`size_ruleset_version: ah-stage-sizing-v1`). "Origin" names the original task a
narrowed task was adopted from (`backlogit adopt` regenerates the ID and records
`custom_fields.origin_feature: 195-F`) or narrowed in place; "new" tasks were
created directly under their slice feature. `195.013-T`..`195.019-T` are real
slice-6 IDs, not design labels. A **triple** edits only the template, its
mirror, and the manifest checksum; its assertions follow in the next tasks.

| Order | Task | Unit | Origin | Shipment | Complexity | Depends on |
|---|---|---|---|---|---|---|
| 1 | 196.001-T | U1a-1 | adopted, was 195.001-T | 202-S | low | — |
| 2 | 196.002-T | U1a-2 | new | 202-S | low | 196.001-T |
| 3 | 196.003-T | U1a-3 | new | 202-S | low | 196.002-T |
| 4 | 196.004-T | U1b-1 | adopted, was 195.008-T | 202-S | medium | 196.003-T |
| 5 | 196.005-T | U1b-2 | new | 202-S | medium | 196.004-T |
| 6 | 196.006-T | U1b-3 | new | 202-S | medium | 196.005-T |
| 7 | 196.007-T | U1b-4 | new | 202-S | medium | 196.006-T |
| 8 | 196.008-T | U1b-5 | new | 202-S | medium | 196.007-T |
| 9 | 197.001-T | U1b-6 | new | 203-S | medium | 196.008-T |
| 10 | 197.002-T | U1b-7 | new | 203-S | medium | 197.001-T |
| 11 | 197.003-T | U1b-8 | new | 203-S | medium | 197.002-T |
| 12 | 197.004-T | U1b-9 | new | 203-S | medium | 197.003-T |
| 13 | 197.005-T | U1b-10 | new | 203-S | medium | 197.004-T |
| 14 | 197.006-T | U1b-11 | new | 203-S | medium | 197.005-T |
| 15 | 197.007-T | U2a-1 (triple) | adopted, was 195.002-T | 203-S | low | 196.003-T |
| 16 | 197.008-T | U2a-2 | new | 203-S | low | 197.007-T |
| 17 | 198.001-T | U2a-3 (triple) | new | 204-S | medium | 197.006-T, 197.008-T |
| 18 | 198.002-T | U2a-4 (+ relax for U2b) | new | 204-S | low | 198.001-T |
| 19 | 198.003-T | U2b-1 (triple) | adopted, was 195.009-T | 204-S | low | 198.002-T |
| 20 | 198.004-T | U2b-2 | new | 204-S | low | 198.003-T |
| 21 | 198.005-T | U2b-3 (triple) | new | 204-S | low | 198.004-T |
| 22 | 198.006-T | U2b-4 | new | 204-S | low | 198.005-T |
| 23 | 198.007-T | U2-PAR (policy parity) | new | 204-S | low | 198.006-T |
| 24 | 198.008-T | U3a-1 (triple) | adopted, was 195.003-T | 204-S | low | 198.005-T, 196.003-T |
| 25 | 198.009-T | U3a-2 | new | 204-S | low | 198.008-T, 198.006-T |
| 26 | 199.001-T | U3a-3 (+ relax for U3b) | new | 205-S | low | 198.009-T |
| 27 | 199.002-T | ENG-L (engine-line consistency) | new | 205-S | low | 198.008-T, 197.007-T, 196.003-T |
| 28 | 199.003-T | U3b-1 (triple) | adopted, was 195.010-T | 205-S | low | 199.001-T |
| 29 | 199.004-T | U3b-2 | new | 205-S | low | 199.003-T |
| 30 | 199.005-T | U3b-3 | new | 205-S | low | 199.004-T |
| 31 | 199.006-T | U3b-4 (+ relax for U4) | new | 205-S | low | 199.005-T |
| 32 | 199.007-T | U4-1 (triple) | adopted, was 195.004-T | 205-S | low | 199.006-T |
| 33 | 199.008-T | U4-2 | new | 205-S | low | 199.007-T |
| 34 | 199.009-T | U4-3 (triple) | new | 205-S | low | 199.008-T |
| 35 | 199.010-T | U4-4 | new | 205-S | low | 199.009-T, 198.007-T |
| 36 | 199.011-T | SK-PAR1 (skill parity I) | new | 205-S | low | 199.010-T |
| 37 | 200.001-T | U5a-1 (triple) | adopted, was 195.005-T | 206-S | medium | 199.009-T, 197.006-T |
| 38 | 200.002-T | U5a-2 | new | 206-S | low | 200.001-T |
| 39 | 200.003-T | U5a-3 | new | 206-S | low | 200.002-T |
| 40 | 200.004-T | U5a-4 (triple) | new | 206-S | medium | 200.003-T |
| 41 | 200.005-T | U5a-5 | new | 206-S | low | 200.004-T |
| 42 | 200.006-T | U5a-6 | new | 206-S | low | 200.005-T |
| 43 | 200.007-T | U5b-1 (triple) | adopted, was 195.011-T | 206-S | low | 200.006-T |
| 44 | 200.008-T | U5b-2 | new | 206-S | low | 200.007-T, 200.006-T |
| 45 | 200.009-T | U5b-3 (triple) | new | 206-S | low | 200.008-T |
| 46 | 200.010-T | U5b-4 | new | 206-S | low | 200.009-T |
| 47 | 200.011-T | U5b-5 | new | 206-S | low | 200.010-T |
| 48 | 200.012-T | U5b-6 | new | 206-S | low | 200.011-T |
| 49 | 195.006-T | U6-1 (triple) | narrowed in place | 201-S | low | 200.009-T |
| 50 | 195.013-T | U6-2 | new | 201-S | low | 195.006-T |
| 51 | 195.012-T | U6b-1 | narrowed in place | 201-S | low | 195.006-T |
| 52 | 195.014-T | U6b-2 | new | 201-S | low | 195.013-T, 195.012-T |
| 53 | 195.015-T | U6b-3 (triple) | new | 201-S | low | 195.012-T, 200.009-T |
| 54 | 195.016-T | U6b-4 | new | 201-S | low | 195.015-T |
| 55 | 195.017-T | SK-PAR2 (skill parity II + closing negative grep) | new | 201-S | low | 200.012-T, 195.014-T, 195.016-T, 198.007-T, 199.011-T |
| 56 | 195.007-T | U7-1 | narrowed in place | 201-S | low | 200.009-T |
| 57 | 195.018-T | U7-2 | new | 201-S | low | 195.007-T |
| 58 | 195.019-T | U7-3 | new | 201-S | low | 195.018-T |

The retired IDs `195.001-T`..`195.005-T` and `195.008-T`..`195.011-T` no longer
exist; no backlog frontmatter dependency or link targets them.

### Shipment partition

Every manifest lists its covering feature first, then its tasks in the dependency
order above. No feature spans two shipments, and every cross-shipment task edge
points to an earlier shipment of the chain.

| Slice | Shipment | Feature | Tasks | # | Blocks on | Closure rule |
|---|---|---|---|---|---|---|
| 1 | 202-S | 196-F — engine-semantics gate, close-path composition, disposition-planner core | 196.001-T..196.008-T | 8 | 190-S (shipped) | pre-195 contract; inert slice (T1, T2) |
| 2 | 203-S | 197-F — planner fail-closed hardening, P-015 flat sets and engine-gate precondition | 197.001-T..197.008-T | 8 | 202-S | SAFE_CLOSE with `ENGINE_SEMANTICS_UNVERIFIED` (T3) |
| 3 | 204-S | 198-F — P-015 INV-12, close-path gate vs. INV-12 split, skill engine-semantics gate | 198.001-T..198.009-T | 9 | 203-S | no deliberation mutation, all retained (T4) |
| 4 | 205-S | 199-F — skill disposition snapshot, Cascade Close flat sets | 199.001-T..199.011-T | 11 | 204-S | no deliberation mutation, all retained (T4) |
| 5 | 206-S | 200-F — Linked-Deliberation Disposition step, hand-offs, post-mode, scenario matrix | 200.001-T..200.012-T | 12 | 205-S | first closure with INV-12 (T5) |
| 6 (terminal) | 201-S | 195-F (umbrella) — Ship and operational-closure consumers, closing grep and parity, compound learnings | 195.006-T, 195.013-T, 195.012-T, 195.014-T..195.017-T, 195.007-T, 195.018-T, 195.019-T | 10 | 206-S (and the satisfied 190-S edge) | full contract; `038-DL` live proof (T5) |

In total: six shipments, six features, 58 tasks. `196-F`..`200-F` have no
`parent_id`; each links to the umbrella `195-F` with `related_to`, which keeps
them out of `195-F`'s INV-6 descendant walk. They carry no deliberation linkage
(T2). `195-F` keeps `source_deliberation_id: 038-DL` for the live proof.
`198-S` still blocks on `201-S`. Only `202-S` of the chain is in the
`dag-readiness` ready set.

### Operator goal coverage: partial

Operator goal (verbatim): "make sure autoharness is aligned in workflow with how
backlogit operates such that we don't recreate this scenario."

Covered by the six-shipment chain (`202-S`..`206-S`, `201-S`):

* the P-015 CASCADE and SAFE_CLOSE close paths realigned to backlogit 1.11.x flat
  semantics;
* pre-mutation detection of an engine-semantics change for P-015 CASCADE and for
  INV-12 disposition mutation (fail closed to SAFE_CLOSE and
  `retained_engine_unverified`);
* the sanctioned, guarded linked-deliberation disposition that replaces the 190-S
  operator deviation;
* Ship post-merge Step 7 and `operational-closure` aligned to the same guard;
* a re-verification runbook for the next backlogit minor line.

Deferred (captured, not dropped):

* the P-002.7 shipment-claim cascade version gate (`62C1E11E`, absorbed by
  `8928EC67`);
* the generalization of `archive_item` single-artifact semantics and every other
  engine-behavior assumption into a registry with a verify-workspace probe
  (`8928EC67`; priority high; hard trigger: it must be deliberated before
  changing the verified engine-semantics lines or adopting backlogit 1.12);
* the re-plan of `198-S` / `192-F` onto this contract (`1263B218`);
* relaxing INV-6's descendant gate under 1.11.x (038-DL OQ3; not captured, since
  it stays fail-closed).

### Stash entries

| Stash ID | Action | Purpose |
|---|---|---|
| `1263B218` | Created (P-021 C2 `DEFERRED SCOPE EXPANSION`; task / high) | Re-plan 198-S / 192-F: `engine_semantics` evidence field, `select_close_path` / `assess_cascade_engine_semantics` use, flat sets, disposition outcome, stale `dag-root` label |
| `8928EC67` | Edited (priority medium → high; hard trigger added) | Engine-behavior registry and verify-workspace probe; absorbs `62C1E11E` and `archive_item` semantics |
| `62C1E11E` | Unchanged (referenced) | P-002.7 claim-cascade gate; to be deliberated with `8928EC67` |

## PR #466 review amendments (staging PR, 2026-09-29)

Copilot review of the staging PR (#466) raised in-scope plan findings over eight
review-fix cycles. The unit text above is the authoritative resolution; this
section only indexes it.

**Ship readiness.** `201-S` has been re-split into six chained shipments of 58
tasks (cycle 8 below; Resulting units and order; Shipment partition). No
Stage-owned planning task remains in any shipment. Ship starts with `202-S`, the
only ready shipment of the chain; `201-S` is blocked on `206-S`.

* **Cycles 1–3** (P-005 limit of 3 review-fix cycles per plan): the `201-S`
  manifest dependency order; the U1b input-safety contract (ID pattern, path
  containment, symlink/reparse rejection); and the U1b description source (the
  Markdown body). Out-of-scope findings were reconciled into `8928EC67` items
  (4) and (5).
* **Cycle 4 — operator-authorized extension.** Operator decision
  (2026-09-29T16:47 local): "extend cycle limit for #466". It authorizes exactly
  one additional (fourth) review-fix cycle, limited to the two open in-scope P1
  Copilot threads on U1b / `195.008-T`. It does not authorize a fifth cycle.
  * `retained_live_status` now covers the actual deliberation live statuses
    `active|blocked|review` (from `.backlogit/header-def.yaml`; deliberations
    have no `in-progress`), with `blocked` and `review` fixtures and a `queued`
    not-live fixture (U1b rule 5 and Tests).
  * `stash_path=None` now resolves to `<workspace_backlog_dir>/stash.jsonl`,
    with default-call tests proving that an active-stash referrer (the `038-DL`
    shape) is detected and the deliberation retained (U1b Stash path default and
    Tests; Runtime Verification `038-DL` expectation).
* **Cycle 5 — operator-authorized extension.** Operator decision (2026-09-29):
  "authorize the fifth review cycle" for PR #466, limited to the single open
  Copilot thread on the U1b / `195.008-T` fail-closed return contract.
  * The new eighth outcome `retained_read_error` is first in the U1b precedence.
    INV-12 stays the name of the invariant (the rule). The outcome set is the
    closed enum `LinkedDeliberationOutcome`. Every outcome carries a
    `reason_code`. `retained_read_error` adds a `path` and an extensible
    read-error vocabulary. The tests assert the exact outcome, `reason_code`,
    and `path` for each read-failure class (U1b Outcome enum and reason codes,
    Input safety, and Tests; U2a INV-12; U5a Report; U5b scenario row (f); U6b;
    038-DL D3a).
* **Cycle 6 — operator-authorized extension.** Operator decision (2026-09-29),
  limited to the stale session-memory thread and the task-granularity thread.
  * The stale final entry of the session memory was corrected (memory fix).
  * The task-granularity finding on `201-S` (thread `PRRT_kwDORzpWpM6nWmsD`:
    tasks exceed the 2-hour rule) was accepted as residual risk and deferred as
    stash `5CA04218` (P-021 C2 `DEFERRED SCOPE EXPANSION`), with a prose-only
    hard trigger in the `195-F` body.
* **Cycle 7 — operator-authorized extension.** Operator decision (2026-09-29,
  option "a"), limited to threads `PRRT_kwDORzpWpM6nXCrq` (prose-only trigger
  is not claim-enforced) and `PRRT_kwDORzpWpM6nXCr8` (this index was stale).
  * The prose trigger is now machine-enforced. Stash `5CA04218` was harvested
    into task `196.001-T` under feature `196-F`, carried by gate shipment
    `202-S` (`202-S` blocks on shipped `190-S`, so it is sequenced and
    immediately eligible). `201-S` now blocks on `202-S` in addition to `190-S`;
    `198-S` still blocks on `201-S`.
  * The re-split itself is Stage work in a follow-up staging PR. After that PR
    merges, `202-S` is closed through the normal Ship closure path (safe-close
    per shipment-reconcile / P-015 classifier), which un-gates `201-S`.
  * This index now records cycles 6 and 7.
  * *Superseded by cycle 8:* the claim-gate items (feature `196-F`, task
    `196.001-T`, shipment `202-S` as described here) were deleted before merge,
    and the re-split was done in this PR instead of a follow-up staging PR.
* **Cycle 8 — operator-authorized extension.** Operator decision (2026-09-29,
  option 1: re-split in-PR; partition approved as "A + amendment"), limited to
  thread `PRRT_kwDORzpWpM6nXl13` (gate shipment `202-S` was immediately
  claimable while its only task was a Stage-owned planning task waiting on a
  follow-up staging PR).
  * The old gate is removed: the cycle-7 claim-gate items were deleted before
    merge, together with the `201-S → 202-S` edge. backlogit later **reused**
    their IDs for new slice-1 items: `196-F` is now the slice-1 feature,
    `196.001-T` is task U1a-1 (adopted from `195.001-T`), and `202-S` is the
    slice-1 shipment. Any reference to those IDs before cycle 8 means the
    deleted gate items. No Stage-owned planning task remains in any shipment;
    every task of the chain is Ship-executable.
  * `201-S` was re-split under the 2-hour rule into 58 tasks (12 narrowed, 46
    new) and partitioned into six chained shipments (binding A: `201-S` keeps
    `195-F` and becomes the terminal slice): `190-S ◀── 202-S (196-F) ◀── 203-S (197-F) ◀── 204-S (198-F) ◀── 205-S (199-F) ◀── 206-S (200-F) ◀── 201-S (195-F) ◀── 198-S`.
    See Resulting units and order and Shipment partition.
  * The amendment adds the multi-PR closure rules T1–T5 (Multi-shipment
    delivery), moves the live proof to `201-S`'s terminal closure (Runtime
    Verification and Closure), and runs the SCOPE_GAP guard at every
    shipment's claim, PR-ready gate, and pre-merge.
  * The operator also approved the design's split decisions and overrode the
    20-task session limit (the apply stayed batched: four backlog batches plus
    this documentation batch). `038-DL`'s historical text is unchanged by
    operator decision.
  * Stash `5CA04218` (the cycle-6 deferral) was already archived as harvested
    into the deleted gate task `196.001-T`. Its delivery is this re-split:
    features `196-F`..`200-F` plus the narrowed `195-F` slice, shipments
    `202-S`..`206-S` and `201-S`, in PR #466. This paragraph is the
    provenance correction: `backlogit stash correct` requires the canonical
    delivery artifact to carry `source_stash_id: 5CA04218`, and no re-split
    artifact does, so no correction record was written.
  * This index now records cycles 1–8.
