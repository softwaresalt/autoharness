---
title: "Canonical post-claim member-status contract (P-002.7) with RED-first cross-surface evidence"
description: "Reduced current-state contract for the post-claim member-status defect, stash 3EF5AAF2. Keeps one contract — a canonical member-status vocabulary asserted identically across exactly four enumerated surfaces — and closes the attempt-08 finding that its evidence was GREEN-only by giving every assertion, including mirror-divergence, version-attribution and the negative state-machine rows, its own RED task that records the assertion failing individually and discriminatingly before any production text exists. Activation is one task and one commit across all four surfaces, because a template and its installed mirror joined by a dependency edge admit a reachable state in which they disagree; if that one task cannot fit inside two hours the unit halts and returns to Stage for explicit scope redesign rather than splitting the commit or authoring assertions mid-activation. The gate speaks one three-token vocabulary — STATUS_CONTRACT_HELD, STATUS_CONTRACT_DIVERGENT, STATUS_CONTRACT_NOT_OBSERVED — emitted by a single task under objective conditions that evaluate the not-observed state first, so an unrun or unimportable suite can never be read as a pass. Carries no dependency on the operation substrate: this unit changes declarations and their conformance test, not execution boundaries, and is the only defect unit that is a DAG root."
doc_type: plan
source: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
date: 2026-09-18
plan_id: post-claim-member-status-contract-v2
plan_path: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_role: active
revision: 3
verdict: null
disposition: REMEDIATED-PENDING-REVIEW
verdict_note: "verdict is null because no independent reviewer has judged revision 3. REMEDIATED-PENDING-REVIEW is recorded under disposition, where it belongs: it states what Stage produced, never what a reviewer found. Revision 3 is the product of one authorized Stage remediation cycle against attempt 02, which returned FAIL/BLOCKED on revision 2 with one P1 (G1, the plan and the sole verdict-emitting task declaring incompatible composed-state vocabularies), two P2s (G2, stale item_deps edges from the retired activation chain; G3, the R5 narrowing rule authoring assertions inside ACTIVATE) and two P3s (G4, retired phase vocabulary; G5, under-declared hardening flag). Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 3
review_manifest: docs/reviews/2026-09-18-post-claim-member-status-contract-v2-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 3EF5AAF2
feature_id: 169-F
shipment_id: 177-S
unit_role: reduced-defect-unit
supersedes_plan: docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
depends_on_shipments: []
dag_role: root
declared_surface_count: 4
requires_plan_hardening: true
hardening_rationale: "The unit's four declared surfaces span two template families, templates/policies/ and templates/agents/, plus their two installed mirrors. Stage's planning gate names multiple template families an elevated blast-radius signal, so the flag is declared true rather than argued down: the hardening content below is a gate, not a completeness note. It adds no new executable surface, runs no command and migrates no existing mutable record, which bounds the blast radius but does not remove the signal. The section carries H1-H11, including the structural coverage questions whose absence let a plan invariant and its own manifest disagree, and the composed-state vocabulary question whose absence let the plan and its only verdict-emitting task declare different tokens."
tags:
  - defect-unit
  - p002-7
  - member-status
  - reduced-scope
  - dag-root
---

# Canonical post-claim member-status contract (P-002.7)

## Why this unit is a root

Every other unit in this portfolio waits on a foundation because it needs an
executable boundary that does not yet exist. This one does not. It changes
**declarations** — a status vocabulary and the surfaces that state it — and
asserts their agreement with a conformance test.

Attempt 08, against the superseded revision-7 plan, recorded two P1 findings
and one P2. `B1` was a provenance defect: every executable record in the unit
cited source stash `3EF5AAF9`, an ID present in no stash file live or archived.
It is **closed** by the governing decision's F10 correction — `169-F`, `177-S`
and every `169.x` task record now cite `3EF5AAF2`, which is the real ID and the
one this plan carries throughout. `B2` was the evidence defect, and it is the
open finding this unit exists to close.

Making this unit a root matters: the architecture decision forbids false serial
dependencies among independent successors, and serializing it behind
`182-S` → `184-S` → `185-S` would be exactly that. `177-S` carries no
shipment-level dependency edge in either direction, which is the executable
form of that claim.

## The defect

Stash `3EF5AAF2`: when Ship claims a shipment, the member items' post-claim
status is stated differently on different surfaces. There is no canonical
vocabulary, so each surface asserts its own and the divergence is invisible
until a reconcile step reports an integrity error.

## The evidence defect (attempt-08 `B2`)

The superseded revision's assertions were **GREEN-only**: each was written to
observe the intended end state, and none was observed failing first. Attempt 08
named the specific assertions that entered that way — mirror-divergence
detection, attribution-paragraph presence, and the negative rows of the state
machine.

A GREEN-only assertion cannot distinguish "the contract holds" from "the
assertion does not test the contract". A test that passes before the change and
after it has measured nothing. That is not a stylistic preference about TDD —
it is the same `NO_OBSERVATION`-is-not-`PASS` rule the rest of this portfolio
enforces, applied to this unit's own evidence.

**Every assertion in this unit is observed failing against the current
divergent surfaces before it is observed passing, and every assertion belongs
to a RED task that records that failure individually.** No task in the VERIFY
phase introduces an assertion. The three assertion families attempt 08 named
are not exceptions to this rule; they are the reason for it, and each has its
own RED task below.

### The discriminating RED rule

An assertion that fails only because the clause text does not exist yet is weak
evidence: absence of a file fails everything, including an assertion that tests
nothing. Each RED task therefore records **two** observations per assertion:

1. **Absence RED** — the assertion executed against the current surfaces,
   failing individually, with its own declared marker in its own failure text.
   An aggregate non-zero suite exit is explicitly insufficient.
2. **Discriminating RED** — the same assertion executed against a synthetic
   near-miss fixture: a copy of the canonical definition mutated in exactly the
   way that assertion exists to catch — a mirror diverged by one word, an
   attribution paragraph removed, a fourth transition row added, a
   cross-reference made one-directional, a fifth surface introduced — and
   observed failing there too.

Observation 2 is what proves the assertion tests the contract rather than the
file's existence. An assertion with only observation 1 recorded has not
satisfied this unit's RED requirement.

**Import safety is binding** for every test module in this unit: it must import
cleanly under `unittest.defaultTestLoader` with zero `loader.errors` and zero
`_FailedTest` placeholders, asserted directly. Not-yet-existing text is read
**inside** the test body through a helper, never at module import time. A
module that raises on import produces a missing observation, not a red one.

## Contract

1. A canonical post-claim member-status vocabulary is defined **once**.
2. Every declared surface states it identically.
3. A conformance test enumerates the surfaces by rule and asserts agreement —
   so a surface added later fails the test rather than silently diverging.
4. The declared surface list is derived by the rule below, is enumerated in
   full, and its count is fixed at **4**.

## Declared surfaces

The rule, its scope, its exclusions and its result, in the shape the governing
decision's F7 uses for the review-verdict consumer inventory.

**Marker set.** A surface is a declaring surface if it carries, or must carry,
the clause anchor `P-002.7` together with either the canonical
post-claim member-status vocabulary block (its three claim-to-admission
transition rows and its observed-version attribution paragraph) or the
bidirectional cross-reference sentence that names the clause.

**Search scope.** Tracked files under `templates/policies/`,
`.github/policies/`, `templates/agents/`, `.github/agents/`.

**Exclusion rule.** Generated and untracked paths are excluded by rule, not by
oversight — specifically `.autoharness/staging/`, which `.gitignore:6` excludes
and which is a generated verify-workspace artifact rather than a mirror. `docs/`
is also outside the scope: it narrates the contract and does not declare it.

**Result — exactly four surfaces, two authoritative/mirror pairs:**

```text
templates/policies/workflow-policies.md.tmpl   (authoritative)
.github/policies/workflow-policies.md          (installed mirror)
templates/agents/_ship.agent.md.tmpl           (authoritative)
.github/agents/_ship.agent.md                  (installed mirror)
```

**Current marker count: 0.** `P-002.7` appears in no file in the search scope
today; it appears only in this plan, its review artifacts and the deliberation
record. That zero is what makes the absence RED observations real, and the
count assertion is directional: the conformance test asserts the marker
resolves in **exactly these four paths and no others**, so both a missed
surface and an unlisted fifth surface fail the test rather than being exempted.

## Composed-state check

The unit resolves to exactly one of three states. `169.016-T` is the sole
emitter of the verdict line, and the vocabulary below is the only vocabulary it
may emit.

| Field | Value |
|---|---|
| Pass state | `STATUS_CONTRACT_HELD` — the `P-002.7` block resolves in exactly the four enumerated paths, byte-identically within each authoritative/mirror pair; the attribution paragraph is present in both policy copies; the cross-reference resolves bidirectionally in both agent copies |
| Fail state | `STATUS_CONTRACT_DIVERGENT` — emitted with the offending surface path and the specific divergence named |
| Not-observed state | `STATUS_CONTRACT_NOT_OBSERVED` — the test module failed to import, or no assertion executed. Distinct from `STATUS_CONTRACT_DIVERGENT` and never a pass |
| Producer | `tests/test_p002_7_member_status_contract.py` — created in `177-S` by `169.009-T` and extended by `169.010-T`, `169.012-T`, `169.013-T` and `169.014-T`. The module produces the **observations**; `169.016-T` reads them and emits the single **verdict line**. Those are two artifacts with two roles, and the split is deliberate: the module must not be able to declare its own gate result |
| Consumer | `.github/workflows/ci.yml` (the stdlib `unittest` suite, which reads the verdict line as a gate) and Ship's claim sequence at `.github/agents/_ship.agent.md` item 4, "Claim the shipment via `backlogit_claim_shipment`", with its authoritative template `templates/agents/_ship.agent.md.tmpl`. Both consumers treat `STATUS_CONTRACT_HELD` as the only pass token |
| Activation commit | `169.015-T` — one task, one commit, all four enumerated surfaces |

### Emission conditions

`169.016-T` evaluates these in order and emits exactly one token. They are
objective: each is decidable from the suite's own output without judgement.

1. **`STATUS_CONTRACT_NOT_OBSERVED`** — emitted if *any* of the following
   holds: the test module raised on import under
   `unittest.defaultTestLoader`; `loader.errors` is non-empty; any
   `_FailedTest` placeholder is present; zero assertions executed; or any one
   of the five RED-proven assertion families has no per-assertion executed
   result recorded. This is checked **first**, because a suite that did not
   run cannot be distinguished from a suite that passed by looking at its exit
   code.
2. **`STATUS_CONTRACT_DIVERGENT`** — emitted if the module imported cleanly,
   every family executed, and **at least one executed assertion failed**. The
   line names the offending surface path and the specific divergence.
3. **`STATUS_CONTRACT_HELD`** — emitted only if the module imported cleanly,
   all five families executed with a per-assertion passing result recorded,
   the surface-enumeration rule resolves to exactly `declared_surface_count`,
   and no assertion exists in the suite that was not observed red first.

**No-observation cannot be mistaken for a pass, and the mistake is blocked in
three places.** The not-observed condition is evaluated before the other two,
so it cannot be reached past them. A green aggregate exit code with no
per-assertion record is `STATUS_CONTRACT_NOT_OBSERVED`, not
`STATUS_CONTRACT_HELD` — the aggregate demonstrates that nothing failed, which
is a weaker claim than that each assertion passed. And an **absent** verdict
line is itself `STATUS_CONTRACT_NOT_OBSERVED`: a consumer that finds no token
has observed nothing and must treat it as such, never as a default pass.

**Fail-closed.** Any state not affirmatively established by conditions 2 or 3
is `STATUS_CONTRACT_NOT_OBSERVED`. This is the portfolio-wide
`NO_OBSERVATION`-is-not-`PASS` rule (decision D6), applied to this unit's own
gate output.

`STATUS_CONTRACT_HELD` is reachable once the single ACTIVATE commit lands.
`STATUS_CONTRACT_DIVERGENT` is reachable **today**, at marker count 0, which is
what makes the absence RED observations possible and the assertions meaningful.

## Rollout

**PREPARE (inert).** The canonical vocabulary definition and the conformance
test are authored as test-owned data and test code. No declared surface
changes, no policy clause references the definition, and the workspace's live
behaviour is byte-identical before and after. This is the only phase in which
the clause text is authored; ACTIVATE transcribes it and writes none.

**RED.** Every assertion is observed failing individually against the current
surfaces, and discriminatingly against a near-miss fixture, before any
production text exists. Five RED tasks, one per assertion family.

**ACTIVATE.** One task, one commit updating every declared surface — both
authoritative templates and both installed mirrors, together. Splitting them
produces a reachable state in which a mirror states a vocabulary its template
does not, which is the divergence this unit exists to remove. A dependency edge
between two activation tasks does not prevent that state; it permits it, which
is why there is one task and not two joined by an edge.

**VERIFY.** The same assertions, unchanged and unextended, observed passing.
A new assertion appearing here is a defect rather than an improvement, and is
returned to a RED task.

### The 2-hour check on ACTIVATE

ACTIVATE is the widest task in the unit by construction, so the check is
recorded rather than assumed.

Its content is **transcription, not authoring**: the exact clause block, the
attribution paragraph and the cross-reference sentence are frozen in PREPARE
and are inserted verbatim into four files across two document pairs. No design
decision is taken during ACTIVATE. Sized `M` (several files) at complexity
`low` (mechanical), it fits inside two hours.

**If it does not, the unit halts and returns to Stage. Ship neither narrows nor
splits.** This is the contingency, stated in advance so it is not invented
under pressure:

1. `169.015-T` **stops**. It does not split the commit — splitting is
   prohibited under every circumstance, because a commit boundary mid-migration
   is a reachable state in which a mirror states a vocabulary its template does
   not.
2. It also does not narrow in place. Narrowing the declared surface list
   changes which assertions the contract needs, and **re-deriving an assertion
   is authoring one** — which ACTIVATE's own `TRANSCRIPTION ONLY - NO
   AUTHORING` invariant forbids, and which would put a never-red assertion into
   the suite after the production text exists. That is precisely the
   attempt-08 `B2` shape this unit was re-authored to eliminate.
3. The shipment returns to **Stage** for explicit scope redesign. Stage decides
   whether to reduce `declared_surface_count`, and if it does, it re-plans the
   consequences as ordinary work: retiring `169.010-T`'s bidirectional family
   and its fixture outright (dropping the Ship-agent pair removes the reverse
   half of the cross-reference from every declared surface, so that family does
   not narrow — it disappears), and re-observing `169.014-T`'s closure
   assertion **red** against the new expectation before any activation resumes.
4. Only then does a revised ACTIVATE execute, against a contract whose every
   assertion has again been proven red first.

This is the governing decision's `R5` applied to its purpose rather than to its
letter: a contract touching too many surfaces to activate in one task is too
large a contract, and resizing a contract is a **planning** act, not something
Ship performs mid-task. The machinery already exists in the unit — `169.016-T`
establishes that a gap discovered late "returns to a RED task rather than being
closed in place", and this rule points `R5` at that same machinery.

## Tasks

| ID | Task | Phase | Size | Complexity |
|---|---|---|---|---|
| `169.011-T` | Author the canonical vocabulary definition, the attribution paragraph, the cross-reference sentence and the surface-enumeration rule as inert test-owned data | PREPARE | S | medium |
| `169.009-T` | Three claim-to-admission transition-state assertions, each observed failing individually and discriminatingly | RED | S | low |
| `169.010-T` | Bidirectional wiring and cross-reference assertions, each observed failing individually and discriminatingly in both copies | RED | S | low |
| `169.012-T` | Mirror-divergence assertions for both authoritative/mirror pairs, each observed failing individually and discriminatingly | RED | S | low |
| `169.013-T` | Observed-version attribution-paragraph assertions, each observed failing individually and discriminatingly | RED | XS | low |
| `169.014-T` | Negative-row and exactly-four-surface closure assertions, each observed failing individually and discriminatingly | RED | S | medium |
| `169.015-T` | One commit across all four enumerated surfaces: clause, attribution paragraph and bidirectional cross-reference | ACTIVATE | M | low |
| `169.016-T` | Observe every RED assertion passing against the shipped text; add no assertion | VERIFY | S | low |
| `169.007-T` | Document the contract, the distinction it preserves, and the explicitly-undelivered downstream detection | DOCS | S | low |

**Sequence.** `169.011-T` → all five RED tasks (independent of one another, any
order) → `169.015-T` → `169.016-T` → `169.007-T`.

Nine tasks, none exceeding two hours on either axis. The widest is `M`/`low`,
justified above; the most uncertain is `S`/`medium` twice, at the two points
where judgement is genuinely required — choosing the canonical wording, and
choosing which states the clause must refuse.

## Assertion-to-task map

Every assertion in this unit has exactly one RED task. A family absent from
this table has no assertion; an assertion absent from a RED task is a defect.

| Assertion family | RED task | Near-miss fixture that discriminates it |
|---|---|---|
| The three claim-to-admission transition rows | `169.009-T` | A definition with one row's target status altered |
| Bidirectional cross-reference resolves in both copies | `169.010-T` | A definition whose cross-reference names only one direction |
| Template and installed mirror are identical in the `P-002.7` block | `169.012-T` | A mirror diverged from its template by one word |
| Observed-version attribution paragraph is present | `169.013-T` | A definition with the attribution paragraph removed |
| The clause admits exactly three rows and no others; the marker resolves in exactly four surfaces | `169.014-T` | A definition with a fourth transition row added, and a fifth declaring surface introduced |

`169.016-T` observes all five families passing and introduces nothing. The
GREEN phase implements only behaviour that was proven red.

## Out of scope

* Any change to the claim mechanism itself.
* Shipment reconcile classification logic.
* The status-transition table. This unit canonicalizes what member status *is*
  after a claim, not which transitions are legal.
* The verify-workspace token implementation and its negative-case suite, which
  belong to the deferred typed-policy-representation entry `E770139B`. The
  documentation task states this plainly rather than implying the detection
  exists.

## Note on an adjacent observation

During this portfolio's research, `backlogit` was observed to reject
`queued → abandoned` and `blocked → abandoned` via its
`validate_status_transition` pre-hook, leaving `abandoned` apparently reachable
only through `active`. That is a transition-table observation about the backlog
tool, **not** a post-claim member-status defect, and it is recorded here only
so it is not lost. It is explicitly **not** in this unit's scope.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | The surface list is incomplete | It is derived by the stated rule, enumerated in full above, and asserted at a fixed count of **4** by `169.014-T`, so an unlisted surface fails the test rather than being exempted. |
| R2 | RED observation is claimed rather than recorded | Each assertion's failing observation is recorded individually; an aggregate suite exit code is explicitly insufficient evidence, and every RED task names the assertions it covers. |
| R3 | An assertion fails only because the clause is absent, and would pass against a wrong clause | The discriminating RED rule requires each assertion to be observed failing against a near-miss fixture as well as against absence. The Assertion-to-task map names the fixture for each family. |
| R4 | An assertion enters during VERIFY and is never observed red | `169.016-T` is specified to add none, and every assertion family has a named RED owner. A family with no RED owner has no assertion. |
| R5 | ACTIVATE exceeds two hours and is split across commits, or is narrowed mid-flight | Neither is permitted. `169.015-T` halts and the unit returns to **Stage** for explicit scope redesign, per the 2-hour check above. The commit never splits, and no assertion is authored or re-derived inside ACTIVATE; any reduced contract has its assertions retired or re-observed red in the RED phase before activation resumes. |
| R6 | The unit is serialized behind a foundation it does not need | `depends_on_shipments` is empty and `177-S` carries no shipment-level edge in either direction. The root claim is checkable against the executable records, not only against this plan. |
| R7 | The gate token the plan declares is not the token the emitting task produces | The Composed-state check names the three-token vocabulary, the Emission conditions state when each is emitted, and `169.016-T` — the sole emitter — reproduces both verbatim. A task record emitting any other token is a defect, not a variant. |
| R8 | A green aggregate suite exit is read as the contract holding | `STATUS_CONTRACT_NOT_OBSERVED` is evaluated first and absorbs every unrun, unimportable and unrecorded case, including a green exit with no per-assertion record. An absent verdict line is also `STATUS_CONTRACT_NOT_OBSERVED`. No path reaches `STATUS_CONTRACT_HELD` without a per-assertion passing record for all five families. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.
`requires_plan_hardening` is **`true`**: the four declared surfaces span two
template families — `templates/policies/` and `templates/agents/` — plus their
installed mirrors, and Stage's planning gate names multiple template families
an elevated blast-radius signal. The signal is declared rather than argued
down, so this section is a **gate**. That the unit adds no executable surface,
runs no command and migrates no record bounds the blast radius; it does not
remove the signal.

The structural questions below exist because a plan invariant and its own
manifest were previously able to contradict each other without either document
being wrong on its face, and because the plan and its only verdict-emitting
task were able to declare different gate vocabularies for the same gate.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Why is this unit not gated behind the substrate foundations? | Because it needs none of them. It changes declarations and asserts their agreement. Serializing it behind `182-S` → `184-S` → `185-S` would be a false dependency, which the architecture decision forbids, and `177-S` carries no such edge. |
| H2 | Is a passing conformance test evidence the contract holds? | Only if it was first observed failing, and failing for the right reason. The attempt-08 defect was GREEN-only assertions; the discriminating RED rule closes the weaker version of the same gap, where an assertion fails merely because nothing exists yet. |
| H3 | Is an aggregate non-zero suite exit sufficient RED evidence? | No. It does not prove that *this* assertion failed. Each assertion's failing observation is recorded individually, with its own declared marker in its own failure text. |
| H4 | What if a surface is added after the contract lands? | The surface list is derived by rule and the count is asserted at 4, so a new surface fails the conformance test rather than diverging silently. |
| H5 | Is the `abandoned`-transition observation in scope? | No. It is a backlog-tool transition-table observation recorded so it is not lost, explicitly outside this unit's contract, which concerns what member status *is* after a claim. |
| H6 | Why one commit across all surfaces? | A commit boundary mid-migration is a reachable state in which a mirror states a vocabulary its template does not — the divergence the unit exists to remove. A dependency edge between two activation tasks does not close that window; it opens it, because an edge permits a commit between its endpoints. |
| H7 | Does every assertion in this unit have a RED task that records it failing? | Yes, and it is checkable rather than asserted: the Assertion-to-task map lists every family with its owning RED task and its discriminating fixture, and the Tasks table lists every task with its phase. A family in neither table has no assertion. This question exists because the previous hardening pass answered H6 correctly in principle without ever checking whether the manifest did it. |
| H8 | Does the plan's task table match the shipment manifest? | It must, and the correspondence is the check: nine tasks, in the phases and sizes stated, are the `177-S` manifest members alongside `169-F`. A plan that cannot be checked against the work it governs is the precondition for exactly the contradiction attempt 01 found. |
| H9 | Is the ACTIVATE task within the 2-hour rule? | Yes on both axes, for the reason recorded under the 2-hour check. If it ever is not, the unit **halts and returns to Stage** for explicit scope redesign. It never splits the commit, and it never narrows or re-derives an assertion inside ACTIVATE — a reduced contract has its affected families retired or re-observed red in the RED phase first. |
| H10 | Does the token this plan declares match the token the emitting task produces? | Yes, and the correspondence is the check. `169.016-T` is the sole emitter; the Composed-state check declares `STATUS_CONTRACT_HELD` / `STATUS_CONTRACT_DIVERGENT` / `STATUS_CONTRACT_NOT_OBSERVED`; the Emission conditions state objectively when each fires; and `169.016-T`'s record reproduces both. This question exists because the previous revision declared a three-token vocabulary in the plan while the only record that produced a verdict emitted an unrelated two-token pair — deleting the not-observed state that decision D6 requires. A consumer reading the plan's token would have found a token no task emits. |
| H11 | Can an unrun or unimportable suite be scored as the contract holding? | No, and the ordering is what prevents it. `STATUS_CONTRACT_NOT_OBSERVED` is evaluated **before** the other two states and absorbs import failure, `loader.errors`, `_FailedTest` placeholders, zero executed assertions, a family with no per-assertion record, and an absent verdict line. `STATUS_CONTRACT_HELD` requires an affirmative per-assertion passing record for all five families; a green aggregate exit cannot produce it. This is the unit's most specific safety property, and it is the one the RED phase's binding import-safety rule exists to detect — so it has a token of its own. |

### Blast radius

Four declaration surfaces — two authoritative templates and their two installed
mirrors — plus one conformance test module and one documentation page. No
executable boundary, no command execution, no migration of existing mutable
records, and no change to any backlog record's schema. The surface count is
fixed and enumerated, which is what makes the blast radius statable rather than
estimated.

### Rollback

PREPARE and RED are inert: they add test code and test data, and change no
declared surface. The single ACTIVATE commit reverts as a unit, returning all
four surfaces to their current divergent state simultaneously. That guarantee
holds because activation is one commit; it would not hold across two commits
joined by a dependency edge, where reverting the second leaves the first in
place and returns the workspace to the split state rather than the original
one.

### Verification floor

Every assertion recorded failing before it is recorded passing, individually,
and failing against a near-miss fixture as well as against absence. No
assertion enters after the production text exists.
