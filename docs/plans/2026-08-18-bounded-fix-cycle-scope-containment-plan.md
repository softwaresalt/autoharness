---
title: P-021 bounded fix-cycle scope containment implementation plan
description: Plan to add P-021 bounded fix-cycle scope containment and deferred expansion capture across agent templates, shared instructions, skill templates, the policy registry and the dogfood/manifest checksum set
doc_type: plan
source: docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-plan.md
status: hardened
date: 2026-08-18
stash_source: B48A482A
deliberation: 019-DL
hardening: docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-hardening.md
feature: 134-F
shipment: 143-S
route: claude-opus-5/anthropic/high
requires_plan_hardening: yes
---

<!-- markdownlint-disable-next-line MD025 -->
# Implementation Plan — P-021 Bounded Fix-Cycle Scope Containment & Deferred Expansion Capture

| Field | Value |
|---|---|
| Date | 2026-08-18 |
| Source stash | `B48A482A` |
| Deliberation | `019-DL` |
| Stage route | `claude-opus-5` / `anthropic` / `high` |
| Requires plan hardening | **yes** |
| Blast radius | Elevated — 3 agent templates, 4 shared instructions, 2 skill templates, 1 prompt, the policy registry, 8 dogfood artifacts, and the manifest checksum set |

## 1. Problem

Operator direction `B48A482A`: when fixing a bug or resolving a Copilot review
comment would expand work beyond the currently approved feature/task scope, the
expansion MUST NOT be implemented in that fix cycle. It must be captured as a
separate stash entry for later Stage triage plus **mandatory deliberation /
research** before planning or implementation. The active feature/task stays
bounded. Review pressure, severity, dark mode, and convenience do not authorize
silent scope expansion. The original in-scope defect/comment is still resolved
as far as possible without the expansion, and the deferred expansion ID is
referenced in the review reply and residual-risk record.

No named policy encodes this today. The nearest artifact is an advisory
compound learning
(`docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`)
with no policy ID and no violation action. The circuit breaker bounds the
*number* of review-fix cycles (3) but says nothing about the *scope* of a fix
within a cycle, so an agent can stay under the breaker while silently expanding.

## 2. Solution

Author **P-021: Bounded Fix-Cycle Scope Containment & Deferred Expansion
Capture** in the workflow policy registry (Amendment Log `1.20.0`), then carry
it across every coherent surface, keeping source templates and dogfood-generated
surfaces byte-consistent with refreshed manifest checksums.

### 2.1 Normative clauses (authored once in S1, quoted by carriers)

| Clause | Statement |
|---|---|
| C1 Scope test | A finding is in scope only if fixing it requires **only completing the exact change already authorized** (the same contract surface). "Same file", "same function", "same PR", "same subsystem", or "related" is **not** sufficient. Work requiring original design/decision effort or an unrelated code path is out of scope. Genuine ambiguity resolves **out of scope**. |
| C2 Mandatory capture | An out-of-scope expansion MUST be captured as a stash entry carrying a `DEFERRED SCOPE EXPANSION` marker, source refs (PR number *when applicable*, review-thread ID *when applicable*, task/feature ID, shipment ID — availability judged independently per field, never fused into a single `PR/thread` ref), and a `requires deliberation` flag. Capture is a precondition for closing the finding, and is never conditional on a PR or thread existing. |
| C3 Bounded resolution | Resolve the in-scope defect/comment as far as possible **without** the expansion. The reference obligation is **conditional on actual thread availability**: where a review thread exists, reference the deferred entry ID in the review-thread reply (posted before the thread is resolved) and in the PR/closure residual-risk record; where no thread exists (pre-PR local review, build/CI), the obligation is discharged **in full** by citing the deferred entry ID in the task/run/closure residual-risk record, and the absent reply is not a shortfall. |
| C4 Non-bypass | Review pressure, severity, dark factory mode (P-017), circuit-breaker exhaustion, and convenience never authorize expansion — and neither does any authorization, explicit operator authorization included. Nothing expands the fix cycle that discovered the expansion. Operator authorization can create or approve a **separate** work unit via C2 capture → mandatory C6 deliberation → new approved scope; it is a forward act that opens new work, never a retroactive in-cycle override. |
| C5 Ship capture-only carve-out | Ship MAY create stash entries **for capture only**. Ship MUST NOT triage, prioritize, re-classify, edit, harvest, deliberate on, **discretionarily remove**, or **discretionarily archive** them. Manifest-derived retirement of the source stash entry that fed the shipped scope, after a successful merge (Ship's existing post-merge Step 7), remains **Allowed** — the distinction is provenance, not verb (hardening H2). |
| C6 Stage intake obligation | A stash entry marked `DEFERRED SCOPE EXPANSION` is a distinct triage classification that MUST route to the `deliberate` skill before any planning, regardless of shape or apparent triviality. |
| C7 Violation action | Implementing an out-of-scope expansion inside a fix cycle, or closing an out-of-scope finding with no captured deferred entry, records a P-021 violation via P-005 telemetry and halts. |

### 2.2 Latent contradiction repaired by this plan

`templates/agents/_ship.agent.md.tmpl` line 38 lists **"stash operations"** in
Ship's **Forbidden** column, while Ship pre-merge Step 9 (lines 527–530) and
post-merge Step 6 (lines 763–766) **already require** Ship to create stash
entries. `role-enforcement.instructions.md` mandates a fail-closed halt plus a
P-010 violation for any forbidden-column operation. Mandating a mid-cycle
capture without repairing this would make the required behavior a policy
violation by construction. Tasks 002 and 003 repair it as a narrow
capture-only carve-out — they are **load-bearing, not optional**.

## 3. Surface map

Verified facts that constrain the map:

* `.github/policies/` does not exist — `workflow-policies.md.tmpl` is
  **template-only**, no dogfood pair, no checksum.
* `.github/skills/` holds only `install-harness`, `tune-harness`,
  `verify-harness`, `workspace-discovery` — `pr-lifecycle` and `fix-ci` skill
  templates are **template-only**.
* `.autoharness/harness-manifest.yaml` records SHA256 checksums for 39 managed
  artifacts. `tests/test_circuit_breaker_policy_contract.py` asserts the
  LF-normalized rendered template is **byte-identical** to the dogfood output
  and that the manifest checksum matches.

| ID | Source template | Dogfood pair | Checksum refresh |
|---|---|---|---|
| S1 | `templates/policies/workflow-policies.md.tmpl` | — | no |
| S2 | `templates/agents/_ship.agent.md.tmpl` (Role Boundary) | `.github/agents/_ship.agent.md` | yes |
| S3 | `templates/instructions/role-enforcement.instructions.md.tmpl` | `.github/instructions/role-enforcement.instructions.md` | yes |
| S4 | `templates/agents/_ship.agent.md.tmpl` (fix-cycle procedure + Stop Conditions) | `.github/agents/_ship.agent.md` | yes |
| S5 | `templates/instructions/circuit-breaker.instructions.md.tmpl` | `.github/instructions/circuit-breaker.instructions.md` | yes |
| S6 | `templates/instructions/github-pr-automation.instructions.md.tmpl` | `.github/instructions/github-pr-automation.instructions.md` | yes |
| S7 | `templates/skills/pr-lifecycle/SKILL.md.tmpl`, `templates/skills/fix-ci/SKILL.md.tmpl` | — | no |
| S8 | `templates/agents/_stage.agent.md.tmpl` | `.github/agents/_stage.agent.md` | yes |
| S9 | `templates/agents/_orchestrator.agent.md.tmpl`, `templates/prompts/feature-flow-dark.prompt.md.tmpl` | `.github/agents/_orchestrator.agent.md`, `.github/prompts/feature-flow-dark.prompt.md` | yes (2) |
| S10 | `.autoharness/harness-manifest.yaml` (`HARNESS_ENFORCED_SUMMARY`) | `.github/instructions/copilot-code-review.instructions.md` | yes |
| S11 | `tests/test_scope_containment_policy_contract.py` (new, structural — 011), `tests/test_scope_containment_semantics_contract.py` (new, capture-and-discharge semantics + allocation guards — 012), `tests/test_scope_containment_boundary_contract.py` (new, clause-boundary semantics — 013) | — | no |

## 4. Task decomposition (2-hour rule, width-isolated)

| # | Task | Surfaces | Depends on | Size | Complexity |
|---|---|---|---|---|---|
| 001 | Author P-021 + Amendment Log `1.20.0` | S1 | — | M | medium |
| 002 | Ship Role Boundary capture-only carve-out | S2 | 001 | S | medium |
| 003 | role-enforcement fail-closed protocol recognizes the carve-out | S3 | 001, 002 | S | medium |
| 004 | Ship review-fix / build-fix defer-capture procedure + Stop Conditions rows | S4 | 002 | M | medium |
| 005 | circuit-breaker Review-Fix Cycle Definition gains the C1 scope test | S5 | 001 | M | medium |
| 006 | github-pr-automation autonomous comment loop: classify / capture / reply citing deferred ID / resolve / residual-risk reference | S6 | 001, 005 | M | medium |
| 007 | `pr-lifecycle` + `fix-ci` skill templates carry C1–C3 (`fix-ci` dual-path) | S7 | 001, 005 | M | medium |
| 008 | Stage Step 1 classification + mandatory `deliberate` routing (C6) + late-identifier reconciliation | S8 | 001, 004, 007 | L | medium |
| 009 | Dark-mode non-bypass (C4) in Orchestrator + `feature-flow-dark` prompt | S9 | 001 | M | medium |
| 010 | `HARNESS_ENFORCED_SUMMARY` policy-range coherence + `copilot-code-review` re-render | S10 | 001 | S | low |
| 011 | Contract test: byte identity, checksums, and the exhaustive clause-to-carrier presence matrix | S11 | 002, 003, 004, 005, 006, 007, 008, 009, 010 (enumerated discretely in the backlog, **review finding R3**) | M | medium |
| 012 | Contract test: behaviour-map allocation guards + C2/C3 capture-and-discharge semantics | S11 | 011, 013 | M | medium |
| 013 | Contract test: P-021 clause-boundary semantics (C1 gate, C4 non-bypass, C5 boundary/reference-role, Stage-only reprioritization, reconciliation consumer) | S11 | 011 | M | medium |

Width isolation holds: no task combines a policy-registry edit with a CLI or
schema edit; no task edits both an agent template family and a skill template
family. Task 001 is the single upstream dependency for every carrier surface so
the normative text exists before any surface quotes it. Tasks 011 and 012 are
last because they assert clauses that must already exist.

**Contract replanning (2026-08-19).** Task 008 gained the Stage-owned
late-identifier reconciliation workflow and a new `004` dependency; task 011's
carrier matrix was corrected to be exhaustive; and task 012 was added to carry
the semantic regression suite that 011's presence-only assertions cannot cover.

**Test-suite split (PR #372 review-fix cycle 1, 2026-08-19).** Task 012's
pre-declared split was taken rather than deferred to implementation: the
CLAUSE-BOUNDARY behaviours (B1, B10, B11, B12, B14, B18) moved to a new sibling
task 013 in its own test file, leaving 012 with the behaviour-map allocation
guards and the CAPTURE-AND-DISCHARGE behaviours (B3–B9, B16, B17). Both tasks
are M. Derived behaviours stayed with their parents and split behaviours stayed
with their siblings, so the allocation remains lineage-coherent and the
behaviour map is still declared only in task 011.

See §5 for the per-task criteria and §7 for the risk these close.

## 5. Per-task acceptance criteria

**001** — `templates/policies/workflow-policies.md.tmpl` contains a `## P-021:`
section with the standard field table (Policy ID / Applies To / Gate Point),
**Statement**, clauses C1–C7, **Precondition**, **Postcondition**,
**Relationship to P-017**, **Relationship to P-018**, **Relationship to P-010**,
and **Violation Action**. The Amendment Log gains a `1.20.0` row. Markdown
lint passes. No unresolved `{{...}}` beyond the file's existing variable set.
`CHANGELOG.md` gains a `## Unreleased` entry describing P-021, matching the
format of the existing F02FD596 entry at the head of the file (**review finding
R2**).

**002** — Ship's Role Boundary Backlog row no longer forbids stash creation
outright; it names the capture-only carve-out in **Allowed** and keeps triage /
prioritization / re-classification / harvest / deliberation / removal in
**Forbidden**. Rendered dogfood is byte-identical; manifest checksum refreshed
from the LF-normalized committed blob.

**003** — `role-enforcement.instructions.md.tmpl` states that a capture-only
stash write performed under P-021 matches the Allowed column and does not
trigger the fail-closed unclassified-mutation halt, while any other stash
operation by Ship remains a P-010 violation. Dogfood + checksum refreshed.

**004** — Ship's review-fix and build/CI-fix loops carry C1–C3: evaluate every
finding against the C1 test, capture out-of-scope findings per C2, resolve the
original per C3, and reference the deferred ID in the review-thread reply where
a thread exists, or in the task/run/closure residual-risk record where none
does. The Stop Conditions table's review-fix row notes that
cycle exhaustion does not authorize expansion (C4). Dogfood + checksum refreshed.

**005** — The `### Review-Fix Cycle Definition` section states the C1 test
verbatim in normative form and requires C2 capture for out-of-scope findings.
Existing 3-cycle semantics unchanged. Dogfood + checksum refreshed.
`tests/test_circuit_breaker_policy_contract.py` still passes.

**006** — The autonomous comment-handling loop requires each comment to be
classified in-scope / out-of-scope by the C1 test; out-of-scope comments follow
the REQUIRED ORDERED capture-first sequence — capture the deferred entry per C2,
then a substantive thread reply citing the deferred entry ID and the scope
boundary, then thread resolution, then the PR/closure residual-risk record naming
the same ID. Replying to or resolving the thread before the capture exists is
prohibited, since the reply cannot cite an entry ID that has not been generated
yet. Dogfood + checksum refreshed.

**007** — Both skill templates carry C1–C3 in their review-fix / fix iteration
steps and their residual-risk or follow-up reporting. `fix-ci` is a **dual-path**
carrier: CI check failures take the threadless discharge, while review comments
take the thread-present reply ordering, since the skill maintains a review-thread
inventory, replies per template, resolves Copilot threads via GraphQL, and
enforces a non-negotiable reply gate. It also carries the existing-entry reuse
rule, because a dual-path surface can meet the same finding through two intake
paths in one run. No dogfood pair exists, so no checksum changes.

**008** — Stage Step 1 gains a `Deferred-scope-expansion` classification with a
mandatory route to Step 2 `deliberate`, explicitly overriding the shape-based
routing so such an entry never goes straight to planning. Stage also gains the
STAGE INTAKE obligations, two independently triggered: (A) UNCONDITIONAL
DUPLICATE DETECTION over every deferred entry Stage triages, regardless of field
population — a duplicate comes from a discovery failure, not a missing
identifier, so gating it on `N/A` would leave every fully-populated duplicate
unexamined — and (B) LATE-IDENTIFIER RECONCILIATION, triggered during
deliberation/triage of an entry carrying any `N/A` source ref, where Stage
retrieves the late PR number or
review-thread ID from the Ship-owned residual-risk records that cite the
deferred entry ID — including `fix-ci` run/closure records, where a CI finding
captured with an `N/A` thread ID can gain a thread inside the same dual-path run
— and reconciles the entry in place under its own stash
authority — no Ship write, no duplicate entry, idempotent, and non-blocking when
no late identifier ever surfaces. (A) is what 004's discovery fail-safe depends
on when it captures rather than dropping a finding, so the two tasks are coupled
in both directions. This is the designated consumer of the duty
that 004's late-surfacing-thread criterion delegates to "Stage's C6 intake
responsibility"; without it, every `N/A` recorded under the single-write
invariant would be permanent. Dogfood + checksum refreshed.

**009** — Orchestrator and `feature-flow-dark.prompt` state that a
`DARK_MODE_ACTIVE` record never authorizes scope expansion and that P-021
capture is preserved in full under dark mode. Both dogfood pairs + both
checksums refreshed.

**010** — `HARNESS_ENFORCED_SUMMARY` in `.autoharness/harness-manifest.yaml`
covers the policy range through P-021 (correcting the existing stale
`P-001 through P-019`). `.github/instructions/copilot-code-review.instructions.md`
re-rendered; checksum refreshed. `tests/test_copilot_code_review.py` passes.

**011** — A new contract test asserts, for each dogfooded pair in the surface
map, that the LF-normalized rendered template is byte-identical to the dogfood
output, that the manifest checksum matches, that clauses C1–C7 appear on their
designated carriers per an EXHAUSTIVE matrix — asserting the marker appropriate
to each carrier's declared ROLE (authoritative / normative restatement /
reference-only / procedural / guard-only) rather than one identical string per row — and that the
Ship Role Boundary no longer contains a blanket stash prohibition. A
carrier-completeness guard spanning ALL seven clause rows, derived by inverting a
declared authoring set for tasks 001–009, keeps the matrix from silently
under-listing a carrier. Full `unittest` suite passes.

**012** — A second contract test asserts the C2/C3 CAPTURE-AND-DISCHARGE
SEMANTIC invariants, so a clause that is present but self-contradictory fails a
distinct, diagnosable test: conditional C3, threadless discharge, the
task/run/closure three-record citation, per-field source-ID availability, the
single-write capture invariant, capture-first ordering, thread-present reply
ordering, the six-field payload, the C3 symmetric guard, and dual C3 disposition
carriage with carrier-specific selectors plus existing-entry reuse. It also owns
the behaviour-map ALLOCATION guards that police all three test files.
Each assertion resolves its carrier subset from the
behaviour mapping (B1–B18) in 011 rather than hardcoding a list, and a
subset-fidelity guard fails if a behaviour is asserted against a carrier the
mapping excludes — the mechanism that keeps the suite from demanding
threadless discharge from `github-pr-automation`, or thread-reply ordering from
`circuit-breaker`, which performs no thread operation at all. It also carries a
root-cause guard asserting no C2
carrier makes a PR or a review thread a precondition for capture. Every prior
fix-cycle defect maps to a named failing test here. Full `unittest` suite passes.

**013** — A third contract test asserts the CLAUSE-BOUNDARY semantics, split out
of 012 when its pre-declared split line was reached: the C1 classification gate,
the C4 active-cycle non-bypass (with a universal negative guard against any
wording that names an authorization sufficient to expand the cycle in flight),
the C5 carve-out boundary and its provenance exception, the C5 reference-only
carrier role, Stage-only reprioritization, and the Stage-side reconciliation
consumer asserting all eight of 008's reconciliation obligations. It declares its
own `OWNED_BEHAVIOURS` constant, which 012's allocation guard imports; the import
direction is one-way, so the three-way completeness check stays acyclic. Full
`unittest` suite passes.

## 6. Verification

1. Canonical source gate (**review finding R1**,
   `docs/compound/097-S-canonical-unittest-gate.md`) — full suite green:

   ```powershell
   $env:PYTHONPATH = 'src'
   python -m unittest discover -s tests
   ```

   A repository-root `python -m pytest` invocation is **not** canonical here; it
   wanders into vendored `references/*` and fails on unrelated collection errors.
2. `autoharness verify` / `verify-harness` — no unresolved placeholders, no
   checksum drift, no broken cross-references.
3. Markdown lint over every touched Markdown surface (P-008).
4. Manual coherence read: every clause C1–C7 appears on at least one carrier and
   no carrier contradicts the registry text.
5. `CHANGELOG.md` carries a `## Unreleased` entry for P-021 (**R2**).

## 7. Out of scope (disclosed, deliberately deferred)

* A deterministic `autoharness gate scope-containment` CLI gate — no reliable
  machine signal for scope expansion; heuristics would produce false BLOCKs.
* A structured backlogit `custom_fields.deferred_scope_expansion` schema field —
  belongs to the `backlogit` product; would violate width isolation.
* Broader Orchestrator fix-cycle routing semantics beyond the dark-mode
  non-bypass clause.
* The pre-existing backlogit doctor legacy orphan / self-reference findings.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Dropping task 002/003 would make the mandated capture a P-010 violation | Encoded as an explicit backlog dependency; 011 asserts the carve-out text |
| Manifest checksum conflicts with any concurrent branch | Single serial shipment, one worktree, checksums recomputed from the merged blob per the 115-S procedure |
| Byte-identity drift between template and dogfood | 011 asserts byte identity for every touched pair |
| P-021 could be read as licence to *never* fix anything found in review | C1 explicitly keeps same-contract-surface completions in scope; C3 requires the original to be resolved as far as possible |
| A clause is present and byte-identical on every carrier but semantically self-contradictory across them | Presence-only assertions cannot see this — it is how all three prior fix-cycle defects survived review. Tasks 012 and 013 assert the C2/C3 and clause-boundary semantic invariants directly, with a named regression test per historical defect and per PR review finding |
| A duty is delegated from one carrier to another agent's clause that no task actually defines | The late-identifier reconciliation duty was dangling exactly this way (004 → "Stage's C6 intake responsibility", undefined in 008). Closed by 008's reconciliation workflow; 013's reconciliation-consumer test fails if any such delegation loses its receiving carrier |
| The clause-to-carrier matrix silently under-lists a carrier, so a clause regresses while the test stays green | The matrix in 011 is now exhaustive and carries a carrier-completeness guard tying it to the tasks that author each clause |
| Contract text assumes every finding arrives on a PR review thread | The root cause behind all three prior fix cycles. Guarded directly by 012's NO-PR/NO-THREAD-ASSUMPTION test rather than only via its known symptoms |
