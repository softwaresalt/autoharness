---
title: "Plan review — Closure-evidence naming contract reconciliation"
description: "Consolidated multi-persona plan review of docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md, gating harvest. This record presents one current, authoritative review of the plan as it now stands (revision 5, a full canonical rewrite), followed by a clearly-segregated and deliberately bounded audit trail of superseded findings from earlier cycles. The audit trail is historical and non-binding; the Final Reviewed Contract section is the only statement of what was reviewed and verified. Gate decision: PASS, 0 P0 / 0 P1 open."
doc_type: review
source: docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md
date: 2026-09-17
plan_path: docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md
plan_revision: 5
source_decision: docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md
decision_revision: 4
source_stash_id: FD0CCB42
deferred_scope_expansions:
  - AE612665
review_cycle: 4
review_cycles_remaining: 0
review_cycle_authorization: "Cycles 1-3 consumed the standard three-cycle budget. Cycle 4 is a single bounded correction cycle explicitly authorized by the operator, together with the directive that the plan be maintained as one canonical document rather than an append-only correction log."
dispatch_mode: declared-degradation
decision: PASS
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "closure"
  - "contract-drift"
  - "fail-closed-design"
---

# Plan Review — Closure-Evidence Naming Contract

> **How to read this document.** Everything above the `Audit Trail` divider is
> **current and authoritative**: it describes the plan as it stands at revision
> 5 and the verification actually performed against it. Everything below the
> divider is **historical, superseded, and non-binding** — it exists only so the
> provenance of the current design is traceable, and no sentence in it may be
> read as a requirement.

## Verdict

**Gate decision: PASS** over plan **revision 5**. 0 × P0 open, 0 × P1 open.
**0 review cycles remaining.**

Plan revision 5 is a full canonical rewrite. The plan body no longer carries
revision deltas, superseded requirement variants, resolved-finding tables, or
reviewer chronology; it reads as a single coherent specification. This review
was therefore run against the rewritten document **as a fresh canonical
artifact**, not as a diff against its predecessor.

**Dispatch mode**: declared degradation. Cross-model reviewer persona dispatch
is unavailable in this session (no `agent-engram` search surface, no cross-model
subagent transport). Always-on personas were applied directly against the plan
text, the decision artifact, the harvested backlog, and the live codebase. This
degradation is declared rather than silent; persona independence is weaker than
a dispatched review, and that limitation is a known property of this verdict.

## Inputs

| Artifact | Path | State reviewed |
|---|---|---|
| Plan | `docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md` | revision 5 (canonical rewrite) |
| Decision | `docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md` | revision 4 |
| Session memory | `docs/memory/2026-09-17-stage-closure-evidence-naming-contract.md` | revision 4 |
| Source bug evidence | `docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md` | read-only |
| Prior learning | `docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md` | read-only |
| Stash entry | `FD0CCB42` | consumed/archived |
| Deferred capture | `AE612665` | untouched, unconsumed |
| Harvested backlog | `167-F`, `167.001-T` … `167.012-T`, shipment `175-S` | live |
| Live consumer source | `src/autoharness/gates/topology.py` | read-only |
| Live producer source | `templates/skills/operational-closure/SKILL.md.tmpl`, `.github/skills/operational-closure/SKILL.md` | read-only |
| Publication branch | `chore/stage-175-S` (unpushed) | working tree |

Severity scale: **P0** blocks the gate outright; **P1** must be resolved before
harvest; **P2** should be resolved or explicitly accepted; **P3** is recorded
for follow-up.

## Final Reviewed Contract

This section states what the plan specifies and what this review verified. It is
written in the present tense because it describes the current design, not a
history of arriving at it.

### 1. Path construction is anchored to the resolved workspace root

`build_closure_path` takes a required, keyword-only `workspace_root`, resolves
it **first**, and anchors a relative `closure_dir` as `workspace_root /
closure_dir`. A relative `closure_dir` is never resolved against the process
CWD. The resolved closure directory, the resolved output path, and the output's
parent are each asserted against the resolved root, so an absolute out-of-root
directory, a traversal escape, and a symlink or Windows junction whose target
leaves the tree are all rejected. The same containment logic is extracted as
`assert_path_within_workspace` and reused, by import, for the CLI's
caller-supplied `--path` candidate against `--workspace` — a canonical-looking
file reached from outside the workspace root, directly or through an escaping
symlink/junction, is rejected before the filename, predicate, or
discoverability checks run, rather than being checked by a second,
independently-written containment rule.

*Verified*: plan `C4`, `RQ-15`, `U4`, and `U10`; tasks `167.004-T` and
`167.010-T`. The containment scenario is required to run with the process CWD
set to a temporary directory **outside** the workspace root, and to assert the
built path lies under `workspace_root` and **not** under the CWD — without that
condition the anchoring rule would be untestable by construction. `U4` test 5
extends the same assertion to the `--path` input, parametrized over an
absolute out-of-root path, a traversal escape, and a symlink/junction that
resolves outside the root.

### 2. There is exactly one canonical identifier domain

The write grammars (`CLOSURE_SHIPMENT_ID_PATTERN`, `CLOSURE_FEATURE_ID_PATTERN`)
are uppercase-only and case-sensitive. The canonical read pattern `R1` is
composed from them and is likewise uppercase-only, so R1's accepted domain and
the builder's accepted output domain are the same set **in both directions**,
with exact identifier equality on the R1 match rule. Lowercase tolerance exists
**only** in the legacy read pattern `R2` and its case-folded comparison, which
is the closed, immutable, already-committed corpus that requires it.

The plan makes **no** bidirectional domain-coincidence claim about R2. The only
cross-pattern property asserted for R2 is one-directional and structurally
provable: no builder output can ever match R2, because R2's second
hyphen-delimited token must satisfy `\d{2}` and a builder name's second token is
the literal kind letter.

*Verified*: plan `C1`, `C2`, `RQ-17`, `R14`, `H1.7`; decision `D3`; tasks
`167.001-T` and `167.010-T`. `U10` test 1 asserts coincidence in both directions
with exact equality; `U10` test 3 rejects a lowercase kind letter on the write
path; `U1` test 1 asserts a lowercase-kind canonical-shaped name is **not** R1.

### 3. Attribution parses a designated filename position; it never searches

`attribute_closure_candidate` parses the shipment identifier from the position
the anchored grammar reserves for it — immediately after the date prefix for
R2, leading for R1 — and compares the **single parsed group** to the requested
identifier. A requested shipment token is never looked for anywhere else in a
filename, and specifically never inside an R2 free-form suffix.

*Verified*: plan `C3`, `RQ-18`, `R15`; tasks `167.001-T`, `167.003-T`,
`167.008-T`. `U1` test 2 is required to cover `16-S` versus `162-S` in the
**designated primary position** of both grammars in both directions, **and** the
foreign free-form suffix case (`2026-09-11-16-S-supersedes-162-S-closure.md`
requested as `162-S`, plus the R1-shaped equivalent), which must **not** be
attributed. Zero attributed candidates yields `absent` with an empty candidate
list even in a directory holding 54 foreign records.

### 4. The frontmatter diagnostic is generic because the predicate is boolean

`topology._closure_artifact_complete` returns a boolean and is reused unmodified
by import. The plan therefore does not ask any caller to explain *why* a
frontmatter rejection occurred. The CLI emits a **generic authoritative-predicate
rejection** naming the artifact path, naming the deciding predicate, and quoting
a single contract-owned requirement summary. Field- and reason-specific
diagnostics are emitted only for the checks the CLI itself owns: filename
pattern, discoverability/shipment mismatch, and an absent or unreadable path.

This is the minimal-scope resolution: it needs no new structured validator and
no duplication of validity logic. `U11` test 2 asserts the **negative** form —
no field-level or reason-level cause appears in the message or the JSON payload
— and `U11` test 4 asserts by source inspection that `cli.py` contains no
independent membership test over `closure_status` or `compaction_status`.

*Verified*: plan `C5`, `P-D9`, `RQ-20`, `R18`, `H1.8`, `U4`, `U11`; decision
`D6`; tasks `167.004-T`, `167.011-T`.

### 5. Durable tests use temporary fixtures, with one explicit legacy exception

Every durable scenario builds fixtures in a temporary scratch workspace, and no
durable test reads, globs, stats, or asserts against `docs/closure/`. Within
that rule the plan states an explicit exception rather than an unsatisfiable
demand: the canonical builder **cannot** emit an R2 name, so R1 fixture names
must come from `build_closure_path(...)` and R2 fixture names come from exactly
one dedicated, test-only helper, `tests/_closure_legacy_names.py::legacy_closure_filename`,
which follows the repository's established `tests/_*.py` shared-helper
convention and is never imported by production code.

Real-corpus verification is one-time publication/runtime evidence recorded in
this work's closure artifact, not a durable assertion. A durable corpus sweep
would be unsatisfiable regardless of coupling concerns:
`docs/closure/138-S-129-F-cancellation-closure.md` matches neither recognized
pattern.

*Verified*: plan `C6`, `P-D6`, `P-D7`, `RQ-10`, `R5`, `R17`, `U7`, `U8`, `U12`;
decision `D7`, `R5`; tasks `167.007-T`, `167.008-T`, `167.012-T`. `167.012-T`'s
scope guard states the temporary-fixture rule with the legacy-helper exception
rather than claiming all fixtures are builder-created, which the builder cannot
satisfy.

### 6. One canonical composed-test path

The composed test is `tests/test_closure_contract_compose.py` in the plan, in
task `167.007-T`, in this review, in the session memory, and in every expected-path
list. The `_compose` suffix follows the repository's existing convention
(`tests/test_telemetry_record_compose.py`,
`tests/test_telemetry_tool_event_compose.py`).

*Verified*: byte-identical path string in plan `U7`, plan `## Runtime
Verification and Closure`, task `167.007-T`, and the session memory's
expected-artifact list.

### 7. Dependency and manifest state matches the plan

Live dependency edges match the plan's declared per-unit dependency sets exactly.
This is **not** a minimal transitive reduction and the plan does not claim one:
several units deliberately declare edges also reachable transitively, because
the plan states them directly as unit preconditions. The shipment manifest is in
topological order and every dependency precedes its dependents.

*Verified*: `backlogit_get_shipment 175-S` manifest order against the plan's
`## Dependency Graph` execution order; `backlogit_get_dependencies` for each
task against its plan unit.

### 8. Eligibility is reported as claimability, not as queue-head position

`175-S` is queued, carries `dag-root`, and its shipment-readiness check passes
at `pre_claim` with `predecessor_ids: []`. It is therefore **eligible and
claimable** under its declared root and scope. The advisory `ready_set` is
`["169-S", "175-S"]`, so `175-S` is **not** the first element of the global
ready set; queue ordering may select a different global head. The session record
states claimability and reproduces the gate's own `next_eligible` output
verbatim without restating the gate's token as a Stage assertion.

*Verified*: `autoharness gate dag-readiness --json`; read-only probe of
`_shipment_readiness_check("pre_claim", ...)`. `169-S` was not altered,
re-labelled, or re-sequenced by this session.

## Persona Verdicts

| Persona | Verdict | Note |
|---|---|---|
| Architecture | PASS | The contract module is the sole definition; `workspace_root` is an explicit dependency rather than ambient state; `CONTRACT_DEFINITION_SITE` keeps the scan surface contract-owned; the reader protocol is unchanged and the hardening table says so. The new `## Contract Specification` section gives every unit one place to consume rather than restate. |
| Scope-boundary | PASS | D8's zero-artifact invariant intact; `3EF5AAF2` and `AE612665` untouched and unconsumed; no source, test, or config file written; unit count held at 12. |
| Standards | PASS | All 12 units remain within the 2-hour rule and width isolation; no unit exceeds 4 named scenarios (U10, U11 and U1 use parametrized rows inside a single named scenario); every task carries both `size` and `complexity`. |
| Fail-closed / safety | PASS | Containment anchors to the resolved workspace root and is proven from an out-of-root CWD, and the same primitive gates the CLI's caller-supplied `--path` before any other write-time check runs; one identifier domain with lowercase tolerance confined to the legacy read path; attribution cannot be defeated by a foreign suffix; write/read parity proven across every consumer branch with no second validity definition anywhere. |
| Test-efficacy | PASS | The durable suite depends on no repository history; the legacy-fixture exception is stated explicitly instead of demanding an impossible builder output; the one real-corpus claim that cannot be simulated is preserved as point-in-time runtime evidence. |
| Dependency / sequencing | PASS | Graph acyclic; manifest topological; live edges match plan-declared sets, including the `167.008-T → 167.007-T` edge the legacy-helper precondition introduces. |
| Implementability | PASS | Every constant, parameter, position-anchored pattern, and assertion named in the plan is constructible as specified, and the two previously impossible demands (a builder-created R2 fixture, a field-specific diagnostic from a boolean predicate) are removed rather than restated. |
| Document-hygiene | PASS (new) | The plan body contains no correction log, revision-delta section, superseded-requirement variant, resolved-finding table, or reviewer chronology. Review history is confined to this document, below the audit-trail divider. |

## Harvest Conformance Check

| Check | Result |
|---|---|
| 1:1 unit-to-task mapping | **PASS** — 12 plan units, 12 tasks, no orphan and no extra. |
| Named scenarios per task ≤ 4 | **PASS** — U1, U4, U7, U8, U9, U10, U11 at 4; U2, U3, U12 at 3; U5 and U6 are documentation units whose verification is U9's non-drift guard. Parametrized rows count as rows of one named scenario. |
| `size` and `complexity` present on every task | **PASS** — zero unsized, zero missing complexity. |
| Task text matches the canonical plan | **PASS** — every affected task body rewritten in place through official backlogit operations to match plan revision 5. |
| Manifest membership | **PASS** — exactly the 13 harvested IDs; no pre-existing queue item pulled in. |
| Manifest order | **PASS** — topological; every dependency precedes its dependents. |
| Dependencies match plan-declared sets | **PASS** — including the added `167.008-T → 167.007-T` legacy-helper precondition. |
| DAG acyclic | **PASS** — `cycle_detected: false`, `cycle_nodes: []`. |
| `175-S` queued and `dag-root` | **PASS**. |
| `163-S` depends on `175-S` | **PASS** — `163-S` remains `queued`; no unsupported `blocked` shipment status was invented. |
| Stash traceability | **PASS** — `FD0CCB42` carried into decision, plan, review, memory, feature, and checkpoint; `AE612665` recorded as the deferred capture in all of them. |
| Checkpoint traceability | **PASS** — `checkpoint-20260917-221316.json` (final) carries all domain and progress state under `context`, with **no** top-level `progress` key, verified by reading the persisted JSON back through `backlogit_get_checkpoint`. It supersedes `checkpoint-20260917-213419.json` by reference; no prior record was hand-edited or deleted. Two malformed records in this session's own checkpoint chain hoisted `progress` to the top level and are retained byte-intact as an **accepted, bounded residual risk** rather than repaired in place: `checkpoint-20260917-200735.json` (earliest, superseded by the compliant `checkpoint-20260917-204433.json`) and `checkpoint-20260917-213419.json` (intermediate — its own review-cycle-progression supersession reason did not flag the re-introduced shape defect, which the final record's supersession reason does name explicitly). Both malformed records are `status: resolved`, are not active recovery candidates, and are never hand-edited, unarchived, or deleted; the compliant superseding record in each case is the authoritative one. |

## Unsatisfiable-Gate Check

Every gate outcome the plan introduces or modifies has a concrete legitimate
passing state and a concrete legitimate failing state:

| Outcome | Reachable by | Escapable by |
|---|---|---|
| `recognized` + acceptable | `161-S-153-F-post-merge-closure.md`; `2026-09-11-162-s-154-f-closure.md` | — (this is the pass state) |
| `recognized` + unacceptable | a recognized name with `closure_status: BLOCKED` | author valid frontmatter |
| `unrecognized` | `162-S-notes.md`, which attribution parses to `162-S` at the canonical position | rename to the canonical pattern |
| `absent` | any shipment with no attributed candidate, including in a directory full of foreign records | author a closure artifact |
| `BACKLOG_UNAVAILABLE` | a recognized name with malformed frontmatter | repair the frontmatter |

No row is unreachable and no row is a trap state. The same check applied to the
CLI: each `failed_check` discriminator (`filename`, `frontmatter_predicate`,
`discoverability`, `input`) is reachable and escapable, and the generic
`frontmatter_predicate` message quotes the requirement summary the author needs
in order to escape it.

## Verification of the Plan's Central Claim

The plan's central claim is that recognition alone — with zero closure-artifact
changes — unblocks `163-S`. Verified read-only against the committed tree during
this cycle:

```text
FilesystemTopologyReaders(Path(".")).closure_complete("162-S") -> None
FilesystemTopologyReaders(Path(".")).closure_complete("174-S") -> None
FilesystemTopologyReaders(Path(".")).closure_complete("173-S") -> True

_shipment_readiness_check("pre_claim", "163-S", ...)
  -> blocked, PREDECESSOR_CLOSURE_INCOMPLETE
     "predecessor 162-S is terminal but missing required closure evidence"
```

`docs/closure/2026-09-11-162-s-154-f-closure.md` exists, carries
`closure_status: READY` and `compaction_status: done`, and would satisfy the
unchanged validity predicate if it were ever opened. The failure is purely
discovery. The claim holds.

---

## Audit Trail (HISTORICAL — SUPERSEDED, NON-BINDING)

The entries below record the provenance of the current design. **They are not
requirements.** Each was resolved before this verdict; the finding text is
deliberately reduced to one line so that no superseded wording can be mistaken
for a live specification. The authoritative statement of every item is the
`Final Reviewed Contract` section above and the plan body it describes.

### Cycle 1 — plan revision 1 → 2 (`PASS_WITH_CONDITIONS`, resolved)

| ID | Sev | One-line finding | Disposition |
|---|---|---|---|
| F-1 | P1 | A protocol change was proposed without accounting for the in-repo test doubles. | Superseded by F-9; the protocol is not changed at all. |
| F-2 | P1 | Predicate byte-identity was prose-only. | Hardening item H1.1. |
| F-3 | P2 | "Closed enumeration" was unenforced. | Hardening item H1.4; U1 test 4. |
| F-4 | P2 | The new gate token could be silently swallowed downstream. | Hardening item H6. |
| F-5 | P2 | One unit exceeded the 4-scenario ceiling. | Split into U8. |
| F-6 | P3 | No canonical closure *writer* is delivered. | Out of scope (OQ-1); captured as stash `AE612665`. |
| F-7 | P3 | Closure frontmatter schema not promoted into `schemas/`. | Out of scope (OQ-2). |

### Cycle 2 — plan revision 2 → 3 (entered `BLOCKED`, resolved)

| ID | Sev | One-line finding | Disposition |
|---|---|---|---|
| F-8 | **P0** | A module-level regex tuple could not interpolate a call-time ID, and the builder had no validation or containment. | Generic captured-ID patterns; builder split into U10. |
| F-9 | P1 | A protocol member contradicted the compatibility claim. | Protocol unchanged; optional duck-typed capability accessor. |
| F-10 | P1 | Write-time validation defined validity a second time. | Predicate reused by import; semantic battery split into U11. |
| F-11 | P1 | A harvested task dropped required historical regressions. | U8 shapes restored and marked non-substitutable; U12 created. |
| F-12 | P1 | The non-drift scan was unsatisfiable and spawned a second inventory. | Scan scoped to `RUNTIME_SCAN_ROOTS`; pattern doc derived. |
| F-13 | P1 | An acknowledged scope reduction carried no deferred capture. | Stash `AE612665` captured under P-021 C1. |

### Cycle 3 — plan revision 3 → 4 (entered `BLOCKED`, resolved)

| ID | Sev | One-line finding | Disposition |
|---|---|---|---|
| F-14 | P1 | Containment was verified only beneath the caller-supplied directory. | Workspace-root containment introduced. |
| F-15 | P1 | The ID grammar did not round-trip between builder and classifier. | Field-aware grammars introduced. |
| F-16 | P1 | The authoritative module failed its own non-drift scan. | `CONTRACT_DEFINITION_SITE` self-registration. |
| F-17 | P1 | `unrecognized_candidates` had no shipment-attribution rule. | Attribution rule introduced. |
| F-18 | P1 | One rejected case could not prove write/read parity. | Consumer-branch parity matrix. |
| F-19 | P1 | Durable tests were coupled to the committed closure corpus. | Temporary fixtures; corpus proof moved to runtime evidence. |
| F-20 | P1 | Binding decision D6 still specified scalar-only validation. | D6 revised to the complete predicate. |
| F-21 | P1 | Session memory cited stale revisions and a non-existent checkpoint field. | Memory corrected. |
| F-22 | P2 | The hardening table still described a protocol member. | Justification corrected. |
| F-23 | P2 | The shipment manifest was not topological. | Manifest reordered through official operations. |
| F-24 | P2 | A redundant direct dependency contradicted the plan. | `167.008-T → 167.001-T` removed. |

### Cycle 4 — plan revision 4 → 5 (entered `BLOCKED`, resolved; operator-authorized bounded cycle)

Cycle 4 was authorized by the operator beyond the standard three-cycle budget,
together with the directive that the plan be rewritten as one canonical document
rather than extended with a correction log. Findings F-25 … F-34 are stated in
one line each for the same reason as above.

| ID | Sev | One-line finding | Disposition |
|---|---|---|---|
| F-25 | P1 | A relative `closure_dir` would have resolved against the process CWD before containment was measured. | Root resolves first; relative `closure_dir` anchored under it; out-of-root, absolute-escape, and symlink/junction cases rejected; containment scenario runs from an out-of-root CWD. |
| F-26 | P1 | The ID domain was ambiguous — the read pattern tolerated lowercase the write grammar forbade, and the plan claimed a bidirectional coincidence that did not hold in both directions. | One uppercase-only canonical domain for R1 and the builder; lowercase tolerance confined to legacy R2 reads; the false bidirectional claim removed and replaced with the provable one-directional R2 property. |
| F-27 | P1 | Attribution searched for the requested shipment token as a contiguous token subsequence anywhere in the filename, so a foreign record whose free-form suffix contained the token was attributed to the wrong shipment. | Attribution parses the identifier at its designated grammar position and compares the parsed group; suffix search removed; primary-position and foreign-suffix `16-S`/`162-S` cases both required as tests. |
| F-28 | P1 | The CLI was required to name the offending frontmatter field while directly reusing a boolean-only predicate — an impossible demand that invited a second validity implementation. | Frontmatter rejection narrowed to a generic authoritative-predicate rejection (minimal scope); CLI-owned checks keep specific diagnostics; negative assertions added. |
| F-29 | P1 | A test unit demanded builder-created fixtures for a legacy shape the builder cannot emit. | Explicit durable-test exception: all fixtures temporary, R1 from the builder, R2 from one dedicated test-only legacy filename helper. |
| F-30 | P1 | The composed test's filename differed between the plan and its harvested task. | Single canonical path `tests/test_closure_contract_compose.py`, matching repository convention, propagated to every artifact. |
| F-31 | P1 | Checkpoints were persisted with a top-level `progress` block despite the payload contract requiring domain data under `context`. | A superseding checkpoint was created through the official operation with all domain and progress state under `context`, and the persisted JSON was read back and verified. |
| F-32 | P2 | The session record claimed a transitive reduction that had not been performed. | Corrected to state that live edges match plan-declared dependency sets and that only the undeclared redundant edge was removed. |
| F-33 | P2 | Decision risk R5 and the baseline producer table lagged the live contract. | R5 rewritten to the temporary-fixture design; the producer table now names the template placeholder and the installed literal explicitly and covers both producer surfaces. |
| F-34 | P2 | `175-S` was described as `ready_set_head` although `169-S` precedes it in the global ready set. | Reported as eligible/claimable under its declared root and scope, with the gate's own output quoted verbatim; `169-S` untouched. |

## Gate Outcome

The plan is cleared for harvest at **revision 5** with **0 × P0 and 0 × P1
open**. The review-cycle budget — three standard cycles plus the one
operator-authorized bounded correction cycle — is now **exhausted**. Any further
same-contract-surface finding must halt and escalate rather than open a fifth
cycle.
