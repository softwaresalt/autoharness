---
title: "Plan review attempt 11 - SHIP-HARNESS-LIFECYCLE-FOUNDATION (187-S)"
description: "Immutable per-attempt artifact for the ELEVENTH independent review of the Ship harness lifecycle plan and the FIRST review of revision 12. FAIL/BLOCK: P0 0, P1 8, P2 4, P3 1. Revision 12 closes most attempt-10 structural findings, but the task-scoped RED evidence shape is incompatible with the live P-004 and harness-architect actor contract, the harness-surface registry is undefined, the reader file-slot budget cannot service the resolver's own declared membership bound, Ship consumes resolver verdicts by process exit status alone, and the per-task harness invariant contradicts its own placement anchors."
doc_type: review
source: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-11.md
date: 2026-09-21
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 11
attempt_range: "11"
attempt_conformance: conforming
review_terminal: true
terminal_designation: terminal-fail-recording-only-no-follow-on-authorized
terminal_disposition: FAIL-BLOCKING-P1
terminal_note: "Attempt 11 consumes attempt number 11. This directive authorizes only this immutable artifact and the mutable lifecycle verdict manifest update. No remediation, plan edit, decision edit, backlog mutation, attempt 12, claim, push or GitHub action is authorized."
verdict_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
verdict_manifest_mutated_by_this_attempt: true
predecessor_artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-10.md
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_id: ship-harness-lifecycle-foundation
reviewed_revision: 12
plan_revision_commit: 0806b601
reviewed_content_head: 0806b601
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
plan_mutated_by_this_attempt: false
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 9
feature_id: 181-F
shipment_id: 187-S
declared_surface_count: 1
review_cycle: 11
dispatch_mode: same-model-declared-degradation
subagent_dispatch_state: TOOL_OK
anchor_review_route_state: TOOL_DEGRADED
security_lens_triggered: true
agent_native_parity_triggered: true
indexed_knowledge_retrieval_state: TOOL_UNAVAILABLE
intercom_state: TOOL_UNAVAILABLE
graphtor_docs_state: TOOL_UNAVAILABLE
gate_result: FAIL
decision: BLOCK
verdict_is_pass: false
verdict_at_entry: FAIL
verdict_at_entry_disposition: FAIL-BLOCKING-P1
verdict_at_entry_plan_revision: 12
verdict_at_entry_manifest_revision: 20
verdict_at_entry_publication_eligible: false
remediation_authorization: not-authorized
remediation_performed: false
remediation_cycle_proposed: false
disposition: FAIL-BLOCKING-P1
p0_findings: 0
p1_findings: 8
p2_findings: 4
p3_findings: 1
merged_findings_count: 13
blocking_findings_count: 8
publication_gate: portfolio-strict-zero-p0-p1-p2
findings_raised_at_this_attempt: [S69, S70, S71, S72, S73, S74, S75, S76]
nonblocking_findings_raised_at_this_attempt: [S77, S78, S79, S80, S81]
predecessor_findings_closed_at_this_attempt: [S53, S54, S55, S56, S59, S61, S62, S63, S64, S65, S66, S67, S68]
predecessor_findings_partially_closed: [S57, S58, S60]
previously_closed_findings_unchanged:
  - finding: S14
    state: CLOSED
    closed_at_attempt: 8
    reaffirmed_at_this_attempt: true
    note: "S14 remains closed on the external Ship evidence recorded at attempt 08 and reconfirmed by commit 1cb0dc81. This attempt does not reopen it."
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_note: "Revision 12 is a genuine coherent-contract rewrite and closes most attempt-10 structural findings. It remains insufficient because the plan's RED evidence shape is rejected by the live P-004 precondition and the installed harness-architect actor, the surface registry that the resolver's whole classification pipeline consumes is never defined, and the reader budget contradicts the resolver's own membership bound."
personas_applied:
  - constitution
  - python
  - scope-boundary
  - learnings
  - architecture
  - agent-native-parity
  - security-lens
personas_not_applied: []
tags:
  - "plan-review"
  - "attempt"
  - "fail"
  - "revision-12"
  - "secure-read-contract"
  - "p-004-compatibility"
  - "portfolio-2026-09-18"
---

# Plan review attempt 11 — Ship pre-task harness-generation lifecycle

## Reviewed subject

`docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` at **revision 12**, committed by `0806b601` and reviewed at that content HEAD on branch `chore/stage-176-s-workflow-defects`, together with live carriers `181-F`, `181.002-T`–`181.017-T`, archived `181.001-T`, shipment `187-S`, governing decision revision 9, and mutable verdict manifest revision 20.

This is the **first** independent review of revision 12 and the **eleventh** attempt overall. Every finding below was verified against repository state at the reviewed HEAD, not inferred from the plan's own claims.

## Capability declarations (P-012)

| Capability | State | Effect on this review |
|---|---|---|
| Reviewer subagent dispatch | `TOOL_OK` | All seven personas dispatched as leaf executors. |
| Model-specific / anchor-review routing | `TOOL_DEGRADED` | `.autoharness/config.yaml:57-79` declares `tier1`/`tier2`/`tier3`/`orchestrator`/`stage`/`ship`/`escalation` but **no** `model_routing.anchor_review` key. The anchor route is not dispatchable, so Architecture Strategist ran the identical rubric same-model. Declared fallback: same-model rubric pass. No persona was skipped. |
| Indexed knowledge retrieval (engram) | `TOOL_UNAVAILABLE` | Circuit-open for this session; not retried. Learnings Researcher used bounded direct reads of the exact `docs/compound/` entries already referenced by the plan and its carriers, not broad search. |
| Intercom visibility | `TOOL_UNAVAILABLE` | Operator visibility degraded; no phase broadcasts. Recorded as a session condition, **not** as a plan defect. |
| Graphtor-docs | `TOOL_UNAVAILABLE` | Documentation questions resolved by direct reads under `docs/` and `.github/`. |

`dispatch_mode: same-model-declared-degradation` is recorded per the plan-review skill's clause 3: subagent dispatch was available, model-specific dispatch was not. This is a declared degradation, never a silent fallback.

## Gate result

**FAIL / BLOCK**.

This portfolio's publication gate is stricter than the skill default: any `P0` or `P1` is `FAIL`; any `P2` is `ADVISORY` and not publication-eligible; only `P3`-or-none is `PASS` and publication-eligible.

* `P0`: 0.
* `P1`: 8, all blocking.
* `P2`: 4.
* `P3`: 1.

Merged set: **13 findings**, 8 blocking. The plan remains not publication-eligible and `187-S` is not authorized for execution.

## Predecessor finding disposition

Revision 12 is a substantive rewrite, and most of the attempt-10 set is genuinely closed:

| Finding | State at attempt 11 | Evidence |
|---|---|---|
| `S53` root/component handle traversal | **CLOSED** | Plan lines 118-133 define a filesystem-anchor POSIX walk with mandatory `O_NOFOLLOW`/`O_DIRECTORY`/`O_CLOEXEC`/`dir_fd`, and a Windows verified-root handle with per-component `NtCreateFile` `RootDirectory` descent. |
| `S54` during-read byte cap | **CLOSED** | Plan lines 101-107: exact advertised-size reservation before read, never refunded, chunks bounded to 64 KiB, no retention beyond advertised size, one-byte EOF probe. |
| `S55` Windows same-size mutation | **CLOSED** | Plan line 129: version is `(size, last_write_time, change_time)`; same-size in-place mutation is explicitly observable. |
| `S56` public `harness_read` contract | **CLOSED in part** | Plan lines 74-84 now name the modules, enums, frozen types, keyword-only factory and close semantics. The residual `TraversalAdapter` gap is carried forward as new finding `S75`, not as `S56`. |
| `S57` import laundering / characterization mixing | **PARTIALLY CLOSED** | Laundering is prohibited (plan lines 62-63) and `181.001-T` is archived. The characterization carve-out is now itself a conflict with live P-004; see `S69`. |
| `S58` checkpoint restore replacement | **PARTIALLY CLOSED** | Plan lines 229-230 require replacement and absence proof. Placement is contradicted by `S73`. |
| `S59` asymmetric Ship placement | **CLOSED** | Verified factually correct: the template carries `### Step 2: Harness Generation (P-002 / P-004)` at `templates/agents/_ship.agent.md.tmpl:326`; the mirror has no harness step and carries `### Step 2: Task Execution Loop` at `.github/agents/_ship.agent.md:336`. Per-file anchors with semantic body parity is the right model. |
| `S60` CLI invalid-usage envelope | **PARTIALLY CLOSED** | Plan lines 217-219 totalize the post-parse envelope. The exit-status collision survives as `S72`. |
| `S61` membership totalization | **CLOSED** | Plan lines 144-153 enumerate eleven closed member reason codes covering empty, duplicate, unsupported, ambiguous and mismatch cases. |
| `S62` digest coverage | **CLOSED** | Plan lines 176-186 bind `shipment_id`, both candidates for shipment and every member including stable absence, raw selected records, manifest/template/installed observations, declarations and the final projection. |
| `S63` duplicate manifest classification | **CLOSED in part** | One `ManifestSnapshot` loader is now the sole authority (plan line 159). The unenumerated global reason set is carried forward as `S76`. |
| `S64` canonical `PYTHONPATH=src` | **CLOSED** | Present on every command in the plan's CLI example, verification matrix and PowerShell equivalents, and consistent with `.autoharness/harness-manifest.yaml:472` `TEST_COMMAND`. |
| `S65` fourth-file rollback record | **CLOSED** | Plan line 281 requires fresh live non-repository approval bound to the exact SHA and explicitly forbids a fourth repository file or task-record mutation. |
| `S66` tasks exceed the 2-hour rule | **CLOSED for the named tasks** | `181.001-T` archived; the work is split into sixteen live tasks of 60-110 minutes, all `size: S`/`XS` and `complexity: medium`/`low`, verified in the carrier frontmatter. Residual sizing concern is narrowed to the two Windows tasks under `S80`. |
| `S67` mutable manifest stale | **CLOSED** | Manifest is at revision 20, selects attempt 10, and correctly reports revision 12 awaiting attempt 11. No lifecycle-manifest lock exists; the only lock under `docs/reviews/` is the unrelated `.2026-09-18-p004-observation-gate-plan-review.md.lock`, which was left untouched. |
| `S68` decision three/four-unit count | **CLOSED** | Decision revision 9 no longer states a count; it reads "`185-S` genuinely needs `184-S`'s registry ... `186-S`, `178-S` and `180-S` inherit that transitively" with no numeral to contradict the list. |

## Findings and actionable recommendations

### `S69` — the plan's RED evidence shape is rejected by the live P-004 and harness-architect contract (P1, BLOCKING)

The plan asserts the actor is "already installed and behaviorally conformant" and places harness-architect changes out of scope (plan lines 44, 55). Two independent incompatibilities falsify that assertion.

**(a) Marker exception type.** Every task declares its expected RED as a *marker-bearing assertion failure* — plan line 61 ("The expected-RED roster contains only marker-bearing assertion failures for the current task") and all fifteen markers in the table at plan lines 240-257, e.g. `AH181002_READ_CONTRACT_LEXICAL`. The installed actor at `.github/skills/harness-architect/SKILL.md:124-131` requires every generated harness test to "fail with its own expected failure marker (raise NotImplementedError("..."))", and `.autoharness/harness-manifest.yaml:473` binds `UNIMPLEMENTED_MARKER: 'raise NotImplementedError("...")'`. The actor's own rejected-outcome list at `SKILL.md:136-139` classifies "a test fails for a reason other than the expected failure marker (**a different exception type** or message)" as a harness defect. An `AssertionError` carrying `AH181002_READ_CONTRACT_LEXICAL` is a different exception type, so the installed actor would refuse `harness-ready` for all fifteen markers and the P-002/P-004 gate would never open.

**(b) Characterization-pass carve-out.** Plan line 64 states "Characterization assertions may pass, but they are recorded separately and excluded from the expected-RED roster", repeated verbatim in `181.002-T`, `181.008-T`, `181.010-T` and `181.003-T`. `.github/policies/workflow-policies.md:92` requires that "**Every** generated harness test for the current task is discovered by that run AND fails with its own expected failure marker", and `:98` lists "Pass, skip, `expectedFailure`, or `unexpectedSuccess`" as never-valid evidence. Live P-004 has no exclusion category; the carve-out is exactly the characterization contamination the policy forbids.

**Recommendation:** choose one and make it explicit. Either (i) restate every task marker as a `raise NotImplementedError("<marker>")` failure so the evidence shape matches the installed actor and `UNIMPLEMENTED_MARKER`, and place characterization assertions in a *separate, non-generated* module so P-004's total quantifier is satisfied; or (ii) acknowledge that the plan requires an amendment to `.github/policies/workflow-policies.md` P-004 and `.github/skills/harness-architect/SKILL.md` Step 5.2, add those files to the declared scope with their own reviewed task, and remove the "no corrective work is part of this plan" claim at plan line 44. Do not proceed on the current assertion that the live contract already accepts this evidence shape.

### `S70` — the `harness-surface` registry that the entire classification pipeline consumes is never defined (P1, BLOCKING)

Plan line 155 requires each task to declare "exactly one **supported** `harness-surface:<surface-id>` label", and the classification order at plan lines 163-166 is expressed entirely in terms of "manifest path matches" and "template mismatch". Nothing in the plan defines the mapping from a surface ID to the manifest artifact path and expected template that those predicates compare against, nor enumerates the supported surface-ID set. The only registry the plan creates is the *reason-code* registry (`181.006-T`, plan line 254). No task in the DAG owns a surface registry.

Two consequences follow. First, "zero manifest path matches", "more than one path match" and "template mismatch" have no defined predicate, so `181.014-T` is not implementable as specified. Second, declaration validation at plan lines 155-157 rejects only "missing, duplicate, malformed or mixed" declarations — an unknown-but-well-formed surface ID such as `harness-surface:bogus` passes validation, then falls through classification step 1 to `MISSING`/`MANIFEST_ENTRY_NOT_FOUND` and reducer class 7, yielding `NO_HARNESS / 1`. Ship would halt reporting that a harness is missing when the real fault is an unsupported declaration, which belongs in `UNRESOLVED / 2`.

For reference, the one surface this portfolio actually uses does resolve: all sixteen live tasks declare `harness-surface:harness-architect`, and `.autoharness/harness-manifest.yaml:237-240` tracks `.github/skills/harness-architect/SKILL.md` with `template: "skills/harness-architect/SKILL.md.tmpl"`, which exists. The defect is that the plan never states how that resolution happens.

**Recommendation:** specify the surface registry as a first-class artifact — supported surface ID, manifest artifact path, expected template value, and the exact match predicate — and assign it to a task at or before `181.006-T`. Add a closed `SURFACE_UNSUPPORTED` declaration reason mapping to `UNRESOLVED / 2`, so an unknown surface ID can never be reported as `NO_HARNESS`.

### `S71` — the reader file-slot budget cannot service the resolver's own declared membership bound (P1, BLOCKING)

Plan line 101: "Each lexically valid request claims one file slot before root/adapter work. The claim is never refunded." Plan line 78 fixes `max_files=256`. Plan line 144 permits `custom_fields.items` to be "a list of 1..512 unique strings". Plan lines 148-151 require both queue **and** archive candidates to be consulted for the shipment and every member, with stable absence still entering the ledger. Plan line 141 binds all of this to one `SecureReader` and one aggregate budget. Plan line 172 then re-observes the whole ledger through the same session.

The arithmetic does not close. First-pass candidate reads are `(1 + N) x 2`; the recheck repeats them. At `N = 512` that is roughly 2,052 slot claims against a 256 limit. The contract breaks at approximately `N = 63` members — comfortably inside the declared legal range — at which point a structurally valid shipment returns `FILE_COUNT_LIMIT` purely because of budget arithmetic. `187-S` itself (17 items, ~77 claims) happens to fit, so this defect would not surface during dogfood execution and would first appear on a larger shipment.

Compounding this, the reducer at plan lines 190-197 has no class for reader budget exhaustion. `FILE_COUNT_LIMIT` and `TOTAL_SIZE_LIMIT` arising during member, manifest or template reads map to no stated reducer class or top-level reason code.

**Recommendation:** reconcile the two bounds explicitly. Either raise `max_files` to at least `2 x (max_members + 1) x 2` plus manifest and per-surface reads, or lower the membership bound, or exempt ledger re-observation from slot claiming by caching the first-pass handle set. Then add an explicit reducer class and closed reason code for budget exhaustion so it cannot be silently absorbed into class 2.

### `S72` — Ship consumes the resolver verdict by process exit status alone, which collides with non-resolver exit 1 and 2 (P1, BLOCKING)

Plan line 228 defines Ship's consumption rule purely in terms of process status: "Exit 0 invokes harness-architect ... Exit 1 halts as `NO_HARNESS`; exit 2 halts as `UNRESOLVED`; they remain distinct." Nothing requires Ship to validate that a resolver document was emitted at all before mapping the status.

At the reviewed HEAD, exit 1 and exit 2 are produced on paths that never ran the resolver. `src/autoharness/cli.py:2930-2932` prints `Unknown command: {command}` and calls `sys.exit(1)` for any unrecognized top-level command, so a stale install or a typo in `harness` yields exit 1, which Ship would read as an authoritative `NO_HARNESS`. More seriously, the canonical invocation is `PYTHONPATH=src python -m autoharness.cli harness resolve ...` (plan line 210); if `PYTHONPATH` is unset, the interpreter itself exits 1 before any autoharness code runs. `sys.exit(2)` already appears 35 times across `cli.py` on unrelated usage paths. In every one of these cases "the resolver never ran" is indistinguishable from a definitive harness verdict, and Ship halts with a false, specific diagnosis.

**Recommendation:** make the emitted document, not the exit status, the verdict carrier. Require Ship to parse exactly one JSON document, confirm `schema_version == "1.0.0"` and a recognized `state`, and only then honor `exit_code` — with the additional invariant that `exit_code` must equal the code implied by `state`. Define a distinct halt for "no valid resolver document emitted" that is neither `NO_HARNESS` nor `UNRESOLVED`, and assert it in `181.003-T`'s structural tests.

### `S73` — the per-task harness invariant contradicts its own placement anchors (P1, BLOCKING)

Plan line 60 states the invariant: "**Before each implementation task**, Ship invokes harness-architect for that task's declared acceptance scenario and unique marker", and plan line 68 adds "After the task, the same marker must be green." This is a per-task, in-loop contract.

The declared placement is pre-loop in both files. Plan lines 224-226 update the template's existing `### Step 2: Harness Generation (P-002 / P-004)` and insert `### Step 1.5` into the mirror "immediately before its existing `### Step 2: Task Execution Loop`". At the reviewed HEAD the template section it targets states, at `templates/agents/_ship.agent.md.tmpl:328`, "This step runs once, up front — **not in a loop**", and partitions the whole task list by the `harness-ready` label. The mirror's `### Step 2: Task Execution Loop` (`.github/agents/_ship.agent.md:336-372`) contains no harness hook, and `### Step 1.5` would sit entirely outside it.

Plan line 228's phrase "requires the current task's valid marker-bearing RED evidence before partition" makes the contradiction explicit: at a once-up-front step that runs before partitioning, there is no current task. Neither plan line 222-226 nor `181.005-T`'s three-file budget requires editing the template's Step 4 execute-task loop or the mirror's Step 2 loop, and neither requires removing or amending the retained "runs once, up front — not in a loop" sentence. Both loops live inside the two files already in scope, so the file budget is not the obstacle — the declared anchors are simply in the wrong place for the invariant.

**Recommendation:** decide which contract is intended and make the anchors match it. If the invariant is genuinely per-task, add explicit anchors inside `templates/agents/_ship.agent.md.tmpl` Step 4 and `.github/agents/_ship.agent.md` Step 2, require the "runs once, up front — not in a loop" sentence and the `harness-ready` batch partition to be replaced rather than retained, and restate line 228 in per-task terms. If a single up-front pass is intended, rewrite plan lines 60-68 to drop "before each implementation task" and define how one pass produces per-task marker evidence for sixteen distinct markers.

### `S74` — the manifest checksum obligation contradicts a documented prior solution (P1, BLOCKING)

Plan line 231 instructs: "Refresh only the existing manifest entry for `.github/agents/_ship.agent.md`; preserve its template sentinel and update checksum/note for **the exact installed bytes**." `181.005-T` repeats this.

`docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md` §1 records the resolution of exactly this failure, naming the failing gate: `tests/test_telemetry_ship_lifecycle.py::test_manifest_tracks_dogfood_ship_agent_checksum`. The documented root cause is that on Windows, PowerShell's pipe/redirect machinery and direct console capture re-mangle line endings to CRLF, and "a checksum computed by reading the working-tree file directly ... will not match". The established procedure — recorded verbatim in the notes of `.autoharness/harness-manifest.yaml:121` and `:126` — is to compute the digest from the LF-normalized committed git blob via `git cat-file -p :<path>`, "never a raw Windows working-tree read". The gate is real: `tests/test_telemetry_ship_lifecycle.py:46-53` compares the manifest checksum against `sha256` of the file bytes.

Precisely stated, the defect is the **absence of any stated computation procedure**, not a claim that a working-tree read is always wrong here. `.gitattributes` does pin `.github/agents/_ship.agent.md text eol=lf`, so on a correctly configured checkout the working-tree bytes are already LF. That pin is exactly why the residual hazard the learning documents is the *computation method* rather than the source: the recorded failure occurred "even when the underlying git blob is LF", because PowerShell re-mangles line endings during capture. Plan line 231 says only "the exact installed bytes" and names no method, so it neither inherits the `eol=lf` guarantee explicitly nor forbids the capture path that is documented to break it — in the terminal task of the DAG, where a mismatch fails the canonical whole-suite command the same task must prove green.

**Recommendation:** replace "the exact installed bytes" at plan line 231 and in `181.005-T` with the documented procedure — compute the checksum from the LF-normalized committed git blob via `git cat-file -p :<path>` (staged) or `HEAD:<path>` (post-commit), never via PowerShell console capture or redirection — and cite `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md` §1 so the constraint is not lost again.

### `S75` — `TraversalAdapter` is public and injectable but its contract is undefined and unbounded (P1, BLOCKING)

Plan line 80 lists `TraversalAdapter` as part of the public contract; plan line 81 exposes `adapter=None` as a public keyword parameter of `open_secure_reader`. The protocol's method set, parameters, return types, error surface and required capability declarations are never specified anywhere in the plan or in any task carrier.

This is the integration seam between `181.002-T` (defines the protocol), `181.009-T` (POSIX implementation), `181.010-T`/`181.011-T` (Windows implementation) and `181.012-T` (integrates adapters behind `open_secure_reader`) — five serial tasks across four files that must agree on a contract the plan never fixes. Under the plan's own width-isolation rules, none of them may edit another's files to reconcile a mismatch.

There is also a trust-boundary consequence. The plan's entire no-follow guarantee rests on adapter-enforced flags, and plan lines 121-122 and 127 require built-in adapters to fail `PLATFORM_INVARIANT_UNAVAILABLE` when a capability is missing. No equivalent obligation is stated for a caller-supplied adapter, so a public caller can pass an adapter that omits `O_NOFOLLOW` or `OBJ_DONT_REPARSE` and obtain a `SecureReader` that silently provides none of the advertised containment, while every public result type still reports success.

**Recommendation:** specify the `TraversalAdapter` protocol explicitly in `181.002-T` — exact methods, signatures, returned snapshot/identity shapes, and the capability-declaration surface the session validates. Require `open_secure_reader` to validate any supplied adapter's declared capabilities against the same mandatory set as the built-in adapters and to fail `PLATFORM_INVARIANT_UNAVAILABLE` otherwise. If injection exists only for tests, make the seam private and keep the public factory adapter-free.

### `S76` — global manifest-failure reason codes are never enumerated, so `reason_code` is not closed (P1, BLOCKING)

Plan line 159 makes one `ManifestSnapshot` loader the sole authority and plan line 160 states "A global manifest failure produces diagnostics but no synthetic per-surface rows". Reducer class 5 at plan line 194 is "global manifest error -> `UNRESOLVED / 2`" with no reason code named. The three manifest reason codes the plan does define (`MANIFEST_ENTRY_NOT_FOUND`, `MANIFEST_ENTRY_AMBIGUOUS`, `MANIFEST_TEMPLATE_MISMATCH`, plan lines 163-165) are explicitly per-surface and are precisely the rows a global failure must not produce. The global cases attempt 10's `S63` enumerated — missing manifest, unreadable manifest, invalid YAML, invalid top-level shape, duplicate top-level entries — therefore have no reason code at all.

Membership got this treatment in full (eleven closed codes, plan lines 152-153); the manifest did not. Two things depend on it. `HarnessResolution.reason_code` is a required ordered field (plan line 137), and `181.017-T` must ship schemas with "closed enums and `oneOf` branches for state/reason/exit consistency" (plan line 205). An unenumerated reason set makes that `oneOf` unbuildable. Separately, the top-level `reason_code` selection rule when reducer class 6 or 7 fires across multiple surfaces with differing per-surface reasons is also unstated.

**Recommendation:** enumerate closed global manifest reason codes with a fixed precedence order covering missing, unreadable, invalid-YAML, invalid-top-level-shape and duplicate-entry cases, in the same style as the membership list. Additionally state the deterministic rule that selects the single top-level `reason_code` when several surfaces fail, so the runtime value and the schema `oneOf` cannot diverge.

### `S77` — hardlink aliasing is the one containment vector the specified traversal does not close, and `OUTSIDE_TRUST_ROOT` has no producing rule (P2)

Symlink and reparse escape are genuinely closed: lexical rejection removes `..`, absolute and prefix forms (plan lines 88-96), and handle-relative descent with `O_NOFOLLOW` / `OBJ_DONT_REPARSE` makes escape structurally impossible. Hardlinks are not covered by either mechanism. A hardlink created inside a trust root that aliases content outside it is a regular file, passes the `NOT_REGULAR_FILE` check, is reached entirely through in-root parent handles, and its bytes are returned as in-root content.

Symptomatically, `ReadErrorCode.OUTSIDE_TRUST_ROOT` is declared at plan line 77 but no rule anywhere in the plan produces it. The Windows carrier `181.010-T` mentions "final-path containment", which hints at a check the plan text never specifies, and the POSIX adapter has no containment predicate at all because it relies on structural containment that hardlinks defeat.

**Recommendation:** either add an explicit final-file containment check that produces `OUTSIDE_TRUST_ROOT` — a link-count assertion (`st_nlink == 1` on POSIX, `NumberOfLinks == 1` on Windows) is the cheapest total form — or state explicitly that hardlink aliasing is an accepted residual risk of the trust model and remove `OUTSIDE_TRUST_ROOT` from the enum so no declared outcome is unreachable.

### `S78` — the RED observation command is not pinned to P-004's mandated canonical whole-suite command (P2)

`.github/policies/workflow-policies.md:91` requires `PYTHONPATH=src python -m unittest discover -s tests` — "the canonical whole-suite test command, invoked exactly as resolved with no runner substitution and **no scoped/targeted subset**" — to be the command that exits non-zero for red-phase evidence. `.github/skills/harness-architect/SKILL.md:124-126` repeats the constraint.

Plan line 67 requires only that "the observed marker, command, failing assertion and task ID are retained as evidence" without pinning which command. The verification matrix at plan lines 265-271 leads with four targeted `python -m unittest tests.<module>` invocations, and plan line 279 states "Before `181.005-T`, its scoped structural marker must be valid RED" immediately after them. Only `181.004-T` mentions a whole-suite baseline, and only for the single pre-activation point; the other fifteen tasks have no such requirement. Evidence gathered from a targeted subset is not valid P-004 evidence under the policy as currently worded.

**Recommendation:** state in the task-scoped harness invariant that the RED observation of record for every task is the canonical whole-suite command, with targeted commands retained only as supplementary diagnostics, and reflect that in each task carrier.

### `S79` — Windows reparse flag precedence and the final-path check are unspecified (P2)

Plan line 127 requires opening each component "through `NtCreateFile` `RootDirectory` with `OBJ_DONT_REPARSE` **and** `FILE_OPEN_REPARSE_POINT`". These flags encode opposite intents: `OBJ_DONT_REPARSE` causes the parse to fail when a reparse point is encountered, while `FILE_OPEN_REPARSE_POINT` opens the reparse point itself instead of its target. Asserting both without stating which governs, and without naming the expected `NTSTATUS` (`STATUS_REPARSE_POINT_ENCOUNTERED`) and its mapping to `REPARSE_POINT`, leaves the adapter's central security behavior ambiguous for `181.011-T`.

Plan line 128 additionally requires that "Every handle is queried for reparse state and final path before use" without stating what the final path is compared against, or the normalization rules that comparison needs (`\\?\` prefixes, 8.3 short names, volume GUID paths). As written the check has no pass/fail criterion.

**Recommendation:** name the governing flag and the expected status-to-reason mapping, and define the final-path check concretely: the comparison target (the verified root handle's own final path), the required relationship (proper-descendant prefix match), and the normalization applied to both sides before comparison.

### `S80` — the two Windows NT-API tasks are the plan's real sizing risk, and their declared complexity is not derived from the work (P2)

`181.010-T` (100m) and `181.011-T` (110m) are both declared `size: S` / `complexity: medium` in their carrier frontmatter. Between them they must bind `NtCreateFile`, marshal `OBJECT_ATTRIBUTES`, `UNICODE_STRING` and `IO_STATUS_BLOCK` through `ctypes`, implement `RootDirectory` chaining, per-handle reparse and final-path validation, identity via volume serial plus file index, version via size/last-write/change time, bounded reads, and a full injected-API test suite proving flag traces and same-size mutation detection.

There is no precedent for this anywhere in the codebase: `src/` contains exactly two files referencing `ctypes` (`gates/bootstrap_grant.py`, `telemetry/_jsonl_segments.py`), neither of which performs NT API structure marshalling. The plan's own risk table at plan line 299 lists the mitigation as "serial split, explicit estimates, **no high-complexity live task**" — which describes a constraint that complexity assignments were made to satisfy, rather than a judgement derived from the work. Under the plan's own two-axis rule, `complexity: high` would force a further split or a de-risking spike; declaring `medium` avoids that outcome by assertion.

This is raised as `P2`, not `P1`: the other fourteen tasks are credibly under two hours, and the splitting in revision 12 is a real improvement over revision 11.

**Recommendation:** either split `181.010-T`/`181.011-T` further — bindings and struct marshalling separate from traversal, and traversal separate from snapshot/read — or insert a short de-risking spike that proves `NtCreateFile` `RootDirectory` descent through `ctypes` on this host before the implementation tasks are estimated. Re-derive complexity from the work rather than from the mitigation constraint.

### `S81` — `read_bytes` argument-passing convention is inconsistent with the rest of the public contract (P3)

Plan line 81 defines `open_secure_reader` as explicitly keyword-only, and plan line 138 defines the resolver as keyword-only, but plan line 82 writes `SecureReader.read_bytes(root, relative_path)` positionally. For a security primitive where transposing the two arguments silently selects the wrong trust root, the inconsistency is worth removing.

**Recommendation:** make `read_bytes` keyword-only for symmetry with the rest of the public surface.

## Recommended remediation order

1. Resolve `S69` first — it determines whether this plan needs P-004/actor amendments in scope, which changes the file budget and the shape of every task marker.
2. Define the surface registry (`S70`) and the global manifest reason codes (`S76`); both are prerequisites for `181.014-T`, `181.016-T` and `181.017-T`.
3. Reconcile the reader budget against the membership bound (`S71`) and add the missing reducer class.
4. Specify the `TraversalAdapter` protocol and bound adapter injection (`S75`) before any of the five tasks that depend on it.
5. Correct the Ship consumption rule (`S72`) and the harness invariant placement anchors (`S73`) together, since both change the same two files.
6. Apply the documented checksum procedure (`S74`).
7. Address `S77`-`S81` as part of the same revision rather than deferring them; this portfolio's gate does not permit publication with open `P2` findings.

## Runtime verification and closure assessment

No runtime verification was executed by this review. Stage is not authorized to run build systems, test suites or linters, and did not. The planned modules `src/autoharness/harness_read.py`, `src/autoharness/harness_surfaces.py`, `_harness_read_posix.py`, `_harness_read_windows.py` and their tests do not exist at the reviewed HEAD, which was confirmed by directory inspection only.

The review assessed whether the *planned* runtime proof would be sufficient. The verification matrix (plan lines 265-274), the rollback contract (plan line 281) and the operational closure list (plan line 285) are structurally complete and correctly place all execution with Ship. The two substantive gaps in this area are `S74` (checksum procedure) and `S78` (RED observation command), both recorded above.

Cross-artifact consistency was checked and is sound: plan revision 12, manifest revision 20, decision revision 9, `181-F`, `187-S` and all sixteen live task carriers agree on the serial order, the archived status of `181.001-T`, the attempt-10 FAIL at `e363aebb`, and the statement that revision 12 is not publication-eligible pending attempt 11. The dependency DAG recorded in the carriers' structured `dependencies` fields matches plan lines 236-241 exactly, including `181.007-T`'s dual edge on `181.016-T` and `181.017-T`, and is acyclic. `187-S`'s `custom_fields.items` matches the plan's live membership exactly, with `181.001-T` correctly absent. No stale authority was found.

P-004 attempt 03 was **not reviewed**. `docs/plans/2026-09-18-p004-observation-gate-plan.md` and `docs/reviews/2026-09-18-p004-observation-gate-plan-review.md` remain blocked, and the current live P-004 contract was consulted only as a prerequisite compatibility input for `S69` and `S78`. Nothing in this attempt changes that state or authorizes P-004 attempt 03.

## Persona coverage

| Persona | Applied | Route | Principal findings |
|---|---|---|---|
| Constitution | yes | same-model subagent | `S69`, `S73` |
| Python | yes | same-model subagent | `S71`, `S75`, `S76`, `S81` |
| Scope boundary | yes | same-model subagent | `S69`, `S74` |
| Learnings | yes | same-model subagent, bounded direct `docs/compound/` reads | `S74` |
| Architecture | yes | anchor route unavailable — same-model declared degradation | `S70`, `S71`, `S76`, `S80` |
| Agent-Native Parity | yes | same-model subagent (triggered: agent-facing CLI and Ship behavior) | `S72`, `S73` |
| Security Lens | yes | same-model subagent (triggered: trust-boundary filesystem handling) | `S75`, `S77`, `S79` |

`dispatch_mode: same-model-declared-degradation`. All seven personas were covered; none was skipped. Findings were merged conservatively, taking the more conservative severity where personas disagreed, and duplicate observations of the same root cause were collapsed into a single finding.

## Authorization boundary

This attempt **consumed attempt number 11** and is terminal for the present authorization. Only this immutable history artifact and the mutable lifecycle verdict manifest were written. No remediation, plan edit, decision edit, task/shipment/P-004 artifact mutation, attempt 12, backlog mutation, checkpoint action, stash action, shipment claim, source/template/test change, GitHub action or push was performed. Untracked checkpoints and memory files were preserved untouched.

Individual file locks with captured tokens were used for review-artifact mutation. No lock was force-released. The unrelated pre-existing `docs/reviews/.2026-09-18-p004-observation-gate-plan-review.md.lock` was observed and left untouched.

## Scope statement

Reviewed: plan revision 12 at `0806b601`; `181-F`, live `181.002-T`-`181.017-T`, archived `181.001-T`, `187-S`; governing decision revision 9; mutable lifecycle manifest revision 20; the live P-004 policy and harness-architect actor contract from `d8b04112`, `1cb0dc81` and `b8ac632a` as a prerequisite compatibility input; and the exact referenced Ship template/mirror, manifest, CLI, schema and test surfaces needed to validate feasibility and file ownership.

Not reviewed: the blocked P-004 plan and review; P-004 attempt 03; runtime implementation of the planned modules; and any source, test, template, installed-agent, backlog, checkpoint, stash, shipment or GitHub mutation.
