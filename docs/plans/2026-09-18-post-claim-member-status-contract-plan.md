---
title: "Canonical post-claim member-status contract (P-002.7) with RED-first cross-surface evidence and a pre-activation readiness gate"
description: "Reduced current-state contract for the post-claim member-status defect, stash 3EF5AAF2. Keeps one contract — a canonical member-status vocabulary asserted identically across exactly four enumerated surfaces — and closes the attempt-08 finding that its evidence was GREEN-only by giving every assertion, including mirror-divergence, version-attribution and the negative state-machine rows, its own RED task that records the assertion failing individually and discriminatingly before any production text exists. The rollout is PREPARE, RED, VERIFY, ACTIVATE, CONFIRM, DOCS and conforms to the binding rollout invariant of decision D2, PREPARE then VERIFY then ACTIVATE: this plan's PREPARE and RED together are D2's PREPARE, whose own rule is that tests go RED first then GREEN entirely within the inert surface; 169.017-T is D2's VERIFY, producing the complete evidence set before any activation; 169.015-T is D2's ACTIVATE. 169.017-T is the pre-activation readiness gate: it evaluates absence RED, discriminating RED and INERT GREEN for all five assertion families against the inert candidate, requires the inert precondition resolved_surface_count=0, and emits PREACTIVATION_READY, PREACTIVATION_BLOCKED or PREACTIVATION_NOT_OBSERVED to .autoharness/gates/p002-7-preactivation-readiness.txt. Activation is authorized by that verdict and not by a dependency edge: 169.015-T reads the artifact as its first action and fails closed, and PREACTIVATION_READY is the only token that opens the gate. Activation remains one task and one commit across all four surfaces, because a template and its installed mirror joined by a dependency edge admit a reachable state in which they disagree; it transcribes only, authors nothing, narrows nothing and reinterprets no evidence, and if it cannot fit inside two hours the unit halts and returns to Stage. 169.016-T is the distinct post-activation confirmation, retained and retitled rather than archived: it confirms installed/template parity and active-consumer behaviour, adds no assertion, and emits STATUS_CONTRACT_HELD, STATUS_CONTRACT_DIVERGENT or STATUS_CONTRACT_NOT_OBSERVED to .autoharness/gates/p002-7-status-contract-verdict.txt. It is explicitly not the evidence gate that authorized activation, and its failure has an explicit path: halt, do not proceed to DOCS, revert the single activation commit as a unit, return to Stage. Both artifacts are gitignored, single-writer, atomically written, whole-file-replaced, hold exactly one verdict line, evaluate absence fail-closed, and exit zero only on their single authorizing or passing token; their paths, line prefixes and token vocabularies are disjoint and are never conflated. Neither is a declared surface, so declared_surface_count stays fixed at 4. No CI workflow is read as a verdict consumer or modified. Carries no dependency on the operation substrate: this unit changes declarations and their conformance test, not execution boundaries, and is the only defect unit that is a DAG root."
doc_type: plan
source: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
date: 2026-09-18
plan_id: post-claim-member-status-contract-v2
plan_path: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_role: active
revision: 5
verdict: null
disposition: REMEDIATED-PENDING-REVIEW
verdict_note: "verdict is null because no independent reviewer has judged revision 5. REMEDIATED-PENDING-REVIEW is recorded under disposition, where it belongs: it states what Stage produced, never what a reviewer found. Revision 5 is the product of one operator-authorized exceptional bounded remediation cycle against attempt 04, which returned FAIL/BLOCKED on revision 4 with one P1 (M1, the plan's rollout phase order PREPARE-RED-ACTIVATE-VERIFY-DOCS contradicting binding decision D2's rollout invariant PREPARE-VERIFY-ACTIVATE, unreconciled and unrecorded, placing the unit's sole gate emitter after the single irreversible commit that mutates all four declared surfaces) and three P3 (M2, the Tasks table omitting 169.016-T's verdict-emitting role; M3, the marker-provenance sentence overstating where P-002.7 appears; M4, the tool-derived size_composition rollup counting archived absorbed tasks). Revision 5 reorders the rollout to PREPARE-RED-VERIFY-ACTIVATE-CONFIRM-DOCS, records the mapping onto D2 explicitly, adds 169.017-T as the pre-activation readiness gate with its own artifact, format, ownership, atomicity, absence semantics and exit-code contract, makes activation depend on that gate's verdict predicate rather than on task completion, and retains 169.016-T retitled as the distinct post-activation confirmation with an explicit rollback and halt path. M2 and M3 are corrected because the rollout rewrite necessarily touches their surfaces and both fixes are mechanical. M4 is a tool-derived archived-child rollup observation, is out of scope for this cycle, and the item hierarchy was not changed to silence it. Stage asserts no PASS, has performed no self-review, and has decremented no finding count."
awaiting_attempt: 5
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
hardening_rationale: "The unit's four declared surfaces span two template families, templates/policies/ and templates/agents/, plus their two installed mirrors. Stage's planning gate names multiple template families an elevated blast-radius signal, so the flag is declared true rather than argued down: the hardening content below is a gate, not a completeness note. It adds no new executable surface, runs no command and migrates no existing mutable record, which bounds the blast radius but does not remove the signal. The section carries H1-H11, H15-H16 and H17-H20, including the structural coverage questions whose absence let a plan invariant and its own manifest disagree, the composed-state vocabulary question whose absence let the plan and its only verdict-emitting task declare different tokens, and — added at revision 5 — the conformance question whose absence let this plan's rollout ordering contradict the binding decision that governs it without either document being wrong on its face."
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
to a RED task that records that failure individually.** No task after the RED
phase — not VERIFY, not ACTIVATE, not CONFIRM — introduces an assertion. The
three assertion families attempt 08 named are not exceptions to this rule; they
are the reason for it, and each has its own RED task below.

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
and which is a generated verify-workspace artifact rather than a mirror, and
`.autoharness/gates/`, which `.gitignore:7` excludes and which holds this
unit's two generated verdict artifacts. A verdict artifact is a *generated
observation about* the declared surfaces, never a declaring surface, so neither
gate artifact can ever be counted as a fifth surface. `docs/` is also outside
the scope: it narrates the contract and does not declare it.

**Result — exactly four surfaces, two authoritative/mirror pairs:**

```text
templates/policies/workflow-policies.md.tmpl   (authoritative)
.github/policies/workflow-policies.md          (installed mirror)
templates/agents/_ship.agent.md.tmpl           (authoritative)
.github/agents/_ship.agent.md                  (installed mirror)
```

**Current marker count: 0.** `P-002.7` appears in no file in the **search
scope** today. It does appear outside that scope — in this plan, its review
artifacts, the deliberation record, and the `169-F`, `177-S` and `169.x`
backlog records that govern the work — and none of those is a declaring
surface, because the search scope is `templates/policies/`,
`.github/policies/`, `templates/agents/` and `.github/agents/` and nothing
else. The load-bearing claim is the scoped one: **count 0 inside the search
scope.**

That zero does two things. It is what makes the absence RED observations real.
And it is the **inert precondition** the pre-activation gate re-checks: while
`resolved_surface_count` is 0, no declared surface has been mutated and the
candidate is still inert, so evidence gathered against it describes a state
that still exists. The count assertion is directional: the conformance test
asserts the marker resolves in **exactly these four paths and no others**, so
both a missed surface and an unlisted fifth surface fail the test rather than
being exempted.

## Gates and verdicts

This unit emits **two verdicts, in two phases, to two artifacts**, and they are
never conflated.

| | Pre-activation readiness | Post-activation confirmation |
|---|---|---|
| Owning task | `169.017-T` (VERIFY) | `169.016-T` (CONFIRM) |
| Runs | **before** the ACTIVATE commit | **after** the ACTIVATE commit |
| Observes | the **inert candidate** as test-owned data, with every declared surface unmutated | the **shipped text** on the installed surfaces |
| Artifact | `.autoharness/gates/p002-7-preactivation-readiness.txt` | `.autoharness/gates/p002-7-status-contract-verdict.txt` |
| Line prefix | `PREACTIVATION_STATE: ` | `COMPOSED_STATE: ` |
| Tokens | `PREACTIVATION_READY` / `PREACTIVATION_BLOCKED` / `PREACTIVATION_NOT_OBSERVED` | `STATUS_CONTRACT_HELD` / `STATUS_CONTRACT_DIVERGENT` / `STATUS_CONTRACT_NOT_OBSERVED` |
| Authorizes activation | **yes** — `PREACTIVATION_READY` only | **no, never** |
| On failure | activation does not begin; no surface is touched | halt, skip DOCS, revert the activation commit as a unit |

**The two vocabularies are disjoint and the two paths are distinct.** Neither
emitter reads, writes, amends or deletes the other's artifact, and a token from
one vocabulary is never valid in the other's file. `resolved_surface_count` is
`0` in the readiness line and `4` in the confirmation line because the two
steps observe two different phases; that is a property of the ordering, not a
discrepancy.

**Neither artifact is a declared surface.** Both live under
`.autoharness/gates/`, which is outside the surface-enumeration rule's search
scope and is gitignored at `.gitignore:7`, so `declared_surface_count` stays
fixed at **4** and no verdict is ever committed or left in a dirty tree.

### Pre-activation readiness gate

`169.017-T` is the sole emitter of the readiness verdict. It runs while every
declared surface is still unmutated, and it is the step decision `D2` calls
VERIFY: *"produce the complete evidence set before any activation … VERIFY
produces an evidence record; it changes no behaviour."*

| Field | Value |
|---|---|
| Ready state | `PREACTIVATION_READY` — all five families carry an absence RED, a discriminating RED and a **passing inert GREEN**; the enumeration rule resolves `declared_surface_count=4` with `resolved_surface_count=0`; no assertion exists that was not observed red first. **The only token that authorizes activation** |
| Blocked state | `PREACTIVATION_BLOCKED` — the evidence set is complete in shape but at least one inert GREEN assertion **failed** against the candidate definition. The line names the family and the gap |
| Not-observed state | `PREACTIVATION_NOT_OBSERVED` — evaluated **first**; absorbs import failure, `loader.errors`, `_FailedTest` placeholders, zero executed assertions, any family missing any of its three observations, and a violated or unresolvable inert precondition. Never ready |
| Producer (observations) | `tests/test_p002_7_member_status_contract.py`, authored by the RED tasks against `169.011-T`'s inert candidate. The module produces the **observations**; `169.017-T` reads them and emits the **verdict line** — the module must not be able to declare its own gate result |
| Producer (verdict) | `169.017-T` — sole writer of the readiness artifact, sole emitter of the readiness line |
| Consumer (authoritative) | **`169.015-T`.** It reads the artifact as its **first action** and fails closed. See *The activation authorization predicate* below |
| Exit code | `169.017-T` exits **zero only** on `PREACTIVATION_READY`; non-zero on `PREACTIVATION_BLOCKED` and `PREACTIVATION_NOT_OBSERVED` |
| **Not** a consumer | `.github/workflows/ci.yml`, for the same directional reason as the confirmation verdict below |

**The evidence set, and why it is complete before activation.** For each of the
five assertion families, `169.017-T` resolves three **per-assertion**
observations — never an aggregate:

1. **Absence RED** — the assertion observed failing individually against the
   current unmutated surfaces, with its own declared marker in its own failure
   text.
2. **Discriminating RED** — the same assertion observed failing against its
   named near-miss fixture, which is what proves it tests the *contract*
   rather than a file's existence.
3. **Inert GREEN** — the same assertion executed against `169.011-T`'s
   canonical candidate definition **as test-owned data** and observed
   **passing**. This is `D2`'s *"tests go RED first, then GREEN, entirely
   within the inert surface"*, and it is observable before any declared
   surface changes.

**`D2`'s compatibility limb is inapplicable, and that is recorded rather than
skipped.** `D2`'s third evidence category is *"compatibility evidence (every
pinned fixture from `D3` processed without error)"*. `D3`'s pinned corpus is
the manifest/normalizer corpus; this unit introduces **no normalizer** and
reads **no historical record corpus**, so the limb has no subject here. The
complete evidence set for this unit is therefore absence RED, discriminating
RED and inert GREEN, for all five families.

**The inert precondition.** `169.017-T` also resolves the surface-enumeration
rule and requires `resolved_surface_count = 0`. A non-zero count means a
declared surface has already been mutated, the candidate is no longer inert,
and the evidence set would describe a state that no longer exists; that
resolves to `PREACTIVATION_NOT_OBSERVED` with `reason=surface_not_inert`.

#### Readiness artifact and line format

**Destination — exactly one path.**
`.autoharness/gates/p002-7-preactivation-readiness.txt`

**Format — exactly one line, one of exactly three literal forms.**

```text
PREACTIVATION_STATE: PREACTIVATION_READY | families=5 | absence_red=5 | discriminating_red=5 | inert_green=5 | declared_surface_count=4 | resolved_surface_count=0 | checked=YYYY-MM-DD
PREACTIVATION_STATE: PREACTIVATION_BLOCKED | families=5 | failed=<n> | family=<A|B|C|D|E> | gap=<short-name> | checked=YYYY-MM-DD
PREACTIVATION_STATE: PREACTIVATION_NOT_OBSERVED | reason=<import_error|loader_errors|failed_test_placeholder|zero_assertions|absence_red_unrecorded|discriminating_red_unrecorded|inert_green_unrecorded|family_unrecorded|surface_not_inert> | checked=YYYY-MM-DD
```

The line begins with the literal prefix `PREACTIVATION_STATE: `, carries the
token as its first field, and separates fields with ` | `. `<n>` is a decimal
integer; `<short-name>` and the `reason=` values are from the closed
vocabularies shown. A `PREACTIVATION_BLOCKED` line naming more than one family
repeats the `family=` field once per family, still on the one line.

**Ownership and write behaviour — single writer, atomic, whole-file replace.**
`169.017-T` is the **sole writer**. No other task, and not the test module,
writes this path. The write is **atomic**: the line goes to a temporary file in
the same directory and is renamed over the destination, so a reader sees either
the previous verdict or the new one and never a partial line. Each run
**replaces the whole file** — never appended to, holding exactly one
`PREACTIVATION_STATE:` line at all times.

**Absence evaluation — fail closed, and absence is a *reading*, not an error.**
A consumer resolves the artifact to `PREACTIVATION_NOT_OBSERVED` if **any** of
the following holds: the file does not exist; it exists but is unreadable; it
is empty; it contains no line beginning `PREACTIVATION_STATE: `; it contains
**more than one** such line; or the token in the first field is not one of the
three declared.

**Exit code.** `169.017-T` exits **zero only** when the token it wrote is
`PREACTIVATION_READY`. The exit code and the artifact carry the same verdict by
construction, because one step produces both.

#### Readiness emission conditions

Evaluated in order; exactly one token is emitted. Each is decidable from the
suite's own output without judgement.

1. **`PREACTIVATION_NOT_OBSERVED`** — emitted if *any* of the following holds:
   the test module raised on import under `unittest.defaultTestLoader`;
   `loader.errors` is non-empty; any `_FailedTest` placeholder is present; zero
   assertions executed; any family has no per-assertion **absence RED** record;
   any family has no per-assertion **discriminating RED** record; any family
   has no per-assertion **inert GREEN** record; or the inert precondition is
   violated or unresolvable. Checked **first**, because a suite that did not
   run cannot be distinguished from a suite that passed by its exit code.
2. **`PREACTIVATION_BLOCKED`** — emitted if the module imported cleanly, all
   five families recorded both RED observations, and **at least one inert GREEN
   assertion failed** against the candidate definition.
3. **`PREACTIVATION_READY`** — emitted **only** if the module imported cleanly;
   all five families recorded an absence RED, a discriminating RED and a
   passing inert GREEN per assertion; the enumeration rule resolves
   `declared_surface_count=4` with `resolved_surface_count=0`; and no assertion
   exists in the suite that was not observed red first.

**Fail-closed.** Any state not affirmatively established by conditions 2 or 3
is `PREACTIVATION_NOT_OBSERVED`. No-observation is never ready.

#### The activation authorization predicate

**Activation depends on the verdict, not on task completion.** This is the
distinction attempt 03's `K1` forced on `177-F`'s `I1` gate, applied here.

A dependency edge clears on **predecessor completion**, and `169.017-T`
*completes* on all three of its tokens — two of which leave the unit unready.
So the edge from `169.015-T` to `169.017-T` supplies **ordering only**: it
guarantees the readiness artifact exists before it is read. The **token** is
the authorization.

`169.015-T`'s **first action**, before any declared surface is opened for
writing, is to read the readiness artifact and fail closed:

* **OPEN** — the file exists, is readable, is not empty, carries **exactly
  one** line beginning `PREACTIVATION_STATE: `, and that line's first field is
  `PREACTIVATION_READY`.
* **CLOSED** — everything else: missing, unreadable, empty, no such line, more
  than one such line, an unrecognised token, `PREACTIVATION_BLOCKED`, or
  `PREACTIVATION_NOT_OBSERVED`.

**On a CLOSED gate, `169.015-T` touches no declared surface at all.** It makes
no commit, writes no clause text, halts, and the unit returns to Stage.
`169.015-T` never re-runs the suite, never re-derives or reinterprets the
evidence set, and never writes to either gate artifact.

### Post-activation confirmation

`169.016-T` runs **after** the single ACTIVATE commit. It resolves the unit to
exactly one of three states, and it is the sole emitter of that verdict line.

**It is not the evidence gate that authorized activation, and must never be
described as one.** That gate is `169.017-T`. What `169.016-T` adds is the one
thing no inert observation can supply: confirmation that the contract holds on
the **installed** surfaces, as **active** declarations.

| Field | Value |
|---|---|
| Pass state | `STATUS_CONTRACT_HELD` — the `P-002.7` block resolves in exactly the four enumerated paths, byte-identically within each authoritative/mirror pair; the attribution paragraph is present in both policy copies; the cross-reference resolves bidirectionally in both agent copies |
| Fail state | `STATUS_CONTRACT_DIVERGENT` — emitted with the offending surface path and the specific divergence named |
| Not-observed state | `STATUS_CONTRACT_NOT_OBSERVED` — the test module failed to import, or no assertion executed. Distinct from `STATUS_CONTRACT_DIVERGENT` and never a pass |
| What it confirms | (1) **installed/template parity** — byte-identical `P-002.7` blocks for both pairs as shipped; (2) **active-consumer behaviour** — Ship's claim sequence at `.github/agents/_ship.agent.md` item 4 resolves the clause as a live declaration rather than inert fixture data, and the cross-reference resolves in both directions from the *installed* copies; (3) the five RED-proven families, per assertion, passing against the shipped text |
| Producer (observations) | `tests/test_p002_7_member_status_contract.py` — created in `177-S` by `169.009-T` and extended by `169.010-T`, `169.012-T`, `169.013-T` and `169.014-T`. The module produces the **observations**; `169.016-T` reads them and emits the single **verdict line**. Those are two artifacts with two roles, and the split is deliberate: the module must not be able to declare its own gate result |
| Producer (verdict) | `169.016-T` — the sole writer of the verdict artifact named below, and the sole emitter of the verdict line |
| Verdict artifact | `.autoharness/gates/p002-7-status-contract-verdict.txt` — exactly one line, written atomically by `169.016-T`. See *Confirmation artifact and line format* below |
| Consumer (authoritative) | **`169.016-T`'s own invocation.** It runs the suite, evaluates the emission conditions, writes the verdict artifact, and **exits non-zero unless the token is `STATUS_CONTRACT_HELD`**. The exit code and the artifact are the gate on *documentation*, not on activation |
| Consumer (contract text, not verdict line) | Ship's claim sequence at `.github/agents/_ship.agent.md` item 4, "Claim the shipment via `backlogit_claim_shipment`", with its authoritative template `templates/agents/_ship.agent.md.tmpl`. Ship reads the **`P-002.7` clause** that `169.015-T` writes into that declared surface. It does not read either verdict line, and it is not a gate consumer |
| **Not** a consumer | `.github/workflows/ci.yml`. Its `test` job runs `PYTHONPATH=src python -m unittest discover -s tests` and consumes an **exit code**; the suite *produces* the observations both verdict lines are derived *from*. The direction is the reverse of a verdict-line consumer. **No task in `177-S` modifies `ci.yml`**, and this unit adds no CI gate |
| Activation commit | `169.015-T` — one task, one commit, all four enumerated surfaces, authorized by `169.017-T`'s verdict |

#### Confirmation artifact and line format

An observation with no destination is not an observation (Principle V). The
destination and the literal line form are therefore declared here rather than
left to the emitting task to invent.

**Destination — exactly one path.**
`.autoharness/gates/p002-7-status-contract-verdict.txt`

`.autoharness/gates/` is **gitignored** (`.gitignore:7`), which is deliberate:
the verdict is a *generated observation about* the tracked surfaces, not a
tracked surface itself. It is never committed, never appears in a diff, and
**cannot leave the working tree dirty** after `169.016-T` runs. `169.007-T`
documents the artifact; it does not commit one. This is the **second** of the
unit's two gate artifacts; the first is the readiness artifact above, and the
two are never conflated.

**Format — exactly one line, one of exactly three literal forms.**

```text
COMPOSED_STATE: STATUS_CONTRACT_HELD | families=5 | assertions_passed=<n> | declared_surface_count=4 | resolved_surface_count=4 | checked=YYYY-MM-DD
COMPOSED_STATE: STATUS_CONTRACT_DIVERGENT | families=5 | failed=<n> | surface=<declared-surface-path> | divergence=<short-name> | checked=YYYY-MM-DD
COMPOSED_STATE: STATUS_CONTRACT_NOT_OBSERVED | reason=<import_error|loader_errors|failed_test_placeholder|zero_assertions|family_unrecorded> | checked=YYYY-MM-DD
```

The line begins with the literal prefix `COMPOSED_STATE: `, carries the token
as its first field, and separates fields with ` | `. `<n>` is a decimal
integer; `<declared-surface-path>` is one of the four enumerated surface paths;
`<short-name>` and the `reason=` values are from the closed vocabularies shown.
A `STATUS_CONTRACT_DIVERGENT` line naming more than one offending surface
repeats the `surface=` field once per surface, still on the one line.

**Ownership and write behaviour — single writer, atomic, whole-file replace.**
`169.016-T` is the **sole writer**. No other task, and not the test module,
writes this path. The write is **atomic**: the line is written to a temporary
file in the same directory and then renamed over the destination, so a reader
sees either the previous verdict or the new one and never a partial line. Each
run **replaces the whole file** — the artifact is never appended to, and it
holds exactly one `COMPOSED_STATE:` line at all times. A pre-existing file from
an earlier run is overwritten, not merged.

**Absence evaluation — fail closed, and absence is a *reading*, not an error.**
A consumer resolves the artifact to `STATUS_CONTRACT_NOT_OBSERVED` if **any**
of the following holds: the file does not exist; it exists but is unreadable;
it is empty; it contains no line beginning `COMPOSED_STATE: `; it contains
**more than one** such line; or the token in the first field is not one of the
three declared above. This is the same fail-closed rule the emission conditions
apply, reapplied at the read boundary, and it is what makes the plan's own
statement — that an **absent** verdict line is itself
`STATUS_CONTRACT_NOT_OBSERVED` (`R8`, `H11`) — decidable rather than
ambiguous. Before this destination was named, a reader could not distinguish
*absent* from *present somewhere else*, and the gate was unevaluable as
written.

**Exit code — the in-unit confirmation gate.** `169.016-T` exits **zero only**
when the token it wrote is `STATUS_CONTRACT_HELD`, and non-zero for
`STATUS_CONTRACT_DIVERGENT` and `STATUS_CONTRACT_NOT_OBSERVED`. The exit code
and the artifact carry the same verdict by construction, because one step
produces both. This is what keeps the unit **self-contained**: both verdicts
are evaluable from their own emitting tasks' invocations alone, with no CI
change, no new workflow and no task outside `177-S`. Note what this exit code
does *not* do — it does not authorize activation, which has already happened by
the time it is computed. It gates **documentation**, and on a non-zero result
it triggers the rollback path below.

#### Confirmation emission conditions

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
   installed/template parity holds for **both** pairs, the surface-enumeration
   rule resolves to exactly `declared_surface_count`, and no assertion exists
   in the suite that was not observed red first.

**No-observation cannot be mistaken for a pass, and the mistake is blocked in
three places.** The not-observed condition is evaluated before the other two,
so it cannot be reached past them. A green aggregate exit code with no
per-assertion record is `STATUS_CONTRACT_NOT_OBSERVED`, not
`STATUS_CONTRACT_HELD` — the aggregate demonstrates that nothing failed, which
is a weaker claim than that each assertion passed. And an **absent** verdict
line is itself `STATUS_CONTRACT_NOT_OBSERVED`: a consumer that finds no token
at `.autoharness/gates/p002-7-status-contract-verdict.txt` has observed nothing
and must treat it as such, never as a default pass. *Confirmation artifact and
line format* above states exactly which read outcomes count as absent.

**Fail-closed.** Any state not affirmatively established by conditions 2 or 3
is `STATUS_CONTRACT_NOT_OBSERVED`. This is the portfolio-wide
`NO_OBSERVATION`-is-not-`PASS` rule (decision D6), applied to this unit's own
gate output.

`STATUS_CONTRACT_HELD` is reachable once the single ACTIVATE commit lands, and
not before — it is a statement about the *activated* surfaces.
`STATUS_CONTRACT_DIVERGENT` is reachable **today**, at marker count 0, which is
what makes the absence RED observations possible and the assertions meaningful.

#### Failure path — rollback and halt

**A non-pass confirmation is not a finding to be argued down; it has one path,
stated in advance.** On `STATUS_CONTRACT_DIVERGENT` or
`STATUS_CONTRACT_NOT_OBSERVED`:

1. `169.016-T` **exits non-zero** and the unit **halts**.
2. **`169.007-T` DOCS does not proceed.** Documentation follows *confirmed*
   behaviour, never asserted behaviour.
3. The single `169.015-T` activation commit is **reverted as a unit** with
   `git revert`, returning all four declared surfaces to their pre-activation
   divergent state **simultaneously**. That guarantee holds *only* because
   activation is one commit; across two commits joined by an edge, reverting
   the second would leave the workspace in the split state rather than the
   original one.
4. The unit **returns to Stage**.

`169.016-T` never repairs a declared surface in place, never amends or re-runs
the activation commit, and never adds, weakens or re-scopes an assertion to
reach `STATUS_CONTRACT_HELD`. A divergence discovered here returns to a **RED
task** for re-observation, and the unit **re-runs `169.017-T`** for a fresh
`PREACTIVATION_READY` verdict before any re-activation. A stale readiness
verdict never authorizes a second activation.

## Rollout

**The order is PREPARE → RED → VERIFY → ACTIVATE → CONFIRM → DOCS, and it
conforms to the binding rollout invariant.** Decision `D2` states that every
contract in this portfolio rolls out `PREPARE → VERIFY → ACTIVATE`, with the
complete evidence set produced **before any activation**. This unit's phases
map onto that invariant as follows, and the mapping is recorded here rather
than left implicit:

| This plan's phase | `D2` phase | Why |
|---|---|---|
| PREPARE | `D2` PREPARE | Authors the candidate inert; live behaviour byte-identical before and after |
| RED | `D2` PREPARE | `D2`'s PREPARE is explicit that *"tests go RED first, then GREEN, entirely within the inert surface"*, so RED sits inside PREPARE rather than beside it |
| VERIFY | `D2` VERIFY | Produces the complete evidence set before any activation and changes no behaviour — `169.017-T` |
| ACTIVATE | `D2` ACTIVATE | One task, one commit, every surface flipped together — `169.015-T` |
| CONFIRM | *(post-activation)* | `D2` defines three phases up to activation and neither names nor forbids what follows. Confirmation observes the activated state; it cannot precede activation |
| DOCS | *(post-activation)* | Documentation follows confirmed behaviour |

**`D2`'s compatibility limb is inapplicable here, and that is recorded, not
skipped.** `D2` names three evidence categories for VERIFY: RED, GREEN, and
compatibility against the `D3` pinned-fixture corpus. `D3`'s corpus is the
manifest/normalizer corpus; this unit introduces no normalizer and reads no
historical record corpus, so the third limb has no subject. This unit's
complete evidence set is absence RED, discriminating RED and inert GREEN.

**PREPARE (inert).** The canonical vocabulary definition and the conformance
test are authored as test-owned data and test code. No declared surface
changes, no policy clause references the definition, and the workspace's live
behaviour is byte-identical before and after. This is the only phase in which
the clause text is authored; ACTIVATE transcribes it and writes none.

**RED.** Every assertion is observed failing individually against the current
surfaces, and discriminatingly against a near-miss fixture, before any
production text exists. Five RED tasks, one per assertion family.

**VERIFY (inert, pre-activation).** `169.017-T` evaluates the complete evidence
set — absence RED, discriminating RED and **inert GREEN** — for all five
families against `169.011-T`'s candidate definition, while every declared
surface is still unmutated, and re-checks the inert precondition
(`resolved_surface_count = 0`). It adds no assertion and changes no behaviour.
It emits the **pre-activation readiness verdict**, and `PREACTIVATION_READY` is
the only token that authorizes the next phase.

**ACTIVATE.** One task, one commit updating every declared surface — both
authoritative templates and both installed mirrors, together. Splitting them
produces a reachable state in which a mirror states a vocabulary its template
does not, which is the divergence this unit exists to remove. A dependency edge
between two activation tasks does not prevent that state; it permits it, which
is why there is one task and not two joined by an edge.

**Its first action is to read the readiness verdict and fail closed.** The edge
supplies ordering; the token supplies authorization. On a CLOSED gate no
declared surface is touched at all. ACTIVATE transcribes only: it adds no
assertion, narrows no scope, and **reinterprets no evidence** — it never
re-runs the suite, re-derives the evidence set, or re-reads a CLOSED gate as
open.

**CONFIRM (post-activation).** `169.016-T` observes the same assertions,
unchanged and unextended, passing against the **shipped** text, and confirms
the two things no inert observation can establish: installed/template parity
across both pairs, and active-consumer behaviour at Ship's claim sequence. A
new assertion appearing here is a defect rather than an improvement, and is
returned to a RED task. **This step is not the evidence gate that authorized
activation**; its failure path is halt, skip DOCS, and revert the single
activation commit as a unit.

**DOCS.** Documents the contract, both verdicts and their non-conflation, and
the explicitly-undelivered downstream detection.

### The 2-hour check on ACTIVATE

ACTIVATE is the widest task in the unit by construction, so the check is
recorded rather than assumed.

Its content is **transcription, not authoring**: the exact clause block, the
attribution paragraph and the cross-reference sentence are frozen in PREPARE
and are inserted verbatim into four files across two document pairs. No design
decision is taken during ACTIVATE, and no evidence is re-derived — the gate
read that opens the task is a single token comparison. Sized `M` (several
files) at complexity `low` (mechanical), it fits inside two hours.

**`169.015-T` has exactly two independent halt triggers, and both end with zero
declared surfaces touched.** The first is a CLOSED readiness gate — any token
other than `PREACTIVATION_READY`, or an absent or malformed readiness artifact,
halts the task before its first write. The second is the two-hour overrun
below. Neither is reducible to the other: a gate can be OPEN on a task that
still overruns, and a task well inside two hours still cannot proceed on a
CLOSED gate.

**If it does not fit, the unit halts and returns to Stage. Ship neither narrows
nor splits.** This is the contingency, stated in advance so it is not invented
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
4. `169.017-T` is **re-run** against the redesigned contract, and only a fresh
   `PREACTIVATION_READY` verdict authorizes a revised ACTIVATE — against a
   contract whose every assertion has again been proven red first. The stale
   readiness verdict from before the redesign never carries over.

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
| `169.017-T` | Evaluate the complete inert evidence set for all five families and emit the pre-activation readiness verdict that authorizes activation | VERIFY | S | low |
| `169.015-T` | One commit across all four enumerated surfaces: clause, attribution paragraph and bidirectional cross-reference, opened by a fail-closed read of the readiness verdict | ACTIVATE | M | low |
| `169.016-T` | Confirm installed/template parity and active-consumer behaviour against the shipped text and emit the post-activation status-contract verdict; add no assertion | CONFIRM | S | low |
| `169.007-T` | Document the contract, both verdicts and their non-conflation, and the explicitly-undelivered downstream detection | DOCS | S | low |

**Sequence.** `169.011-T` → all five RED tasks (independent of one another, any
order) → `169.017-T` → `169.015-T` → `169.016-T` → `169.007-T`.

`169.017-T` is the **sole immediate predecessor** of `169.015-T`. The five RED
tasks reach activation only through it, so there is no path by which activation
becomes ready without the readiness verdict having been computed.

Ten tasks, none exceeding two hours on either axis. The widest is `M`/`low`,
justified above; the most uncertain is `S`/`medium` twice, at the two points
where judgement is genuinely required — choosing the canonical wording, and
choosing which states the clause must refuse.

**Sizing re-assessment on the two changed records, stated rather than
assumed.** `169.017-T` is new: it evaluates a fully-declared predicate over
evidence that already exists and writes one line, which is mechanical work
across a small surface — `S`/`low`. `169.016-T` kept `S`/`low` through its
repurposing: it **lost** the activation-authorization role and **gained** an
explicit rollback/halt path, and those offset rather than compound. Its
observation work — five families, two parity pairs, one active consumer — is
unchanged in volume, and a `git revert` of a single commit adds no uncertainty.
No other task's sizing changed, because no other task's responsibilities did.

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

Neither `169.017-T` nor `169.016-T` introduces an assertion. `169.017-T`
**evaluates** the five families' existing evidence inertly and writes a
verdict; `169.016-T` **observes** the same five families passing against the
shipped text and writes a verdict. Both are prohibited from adding, widening or
re-scoping an assertion, and so is `169.015-T`. The GREEN phase implements only
behaviour that was proven red.

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
| R4 | An assertion enters after the RED phase and is never observed red | Neither `169.017-T`, `169.015-T` nor `169.016-T` may add one, every assertion family has a named RED owner, and a family with no RED owner has no assertion. `169.017-T` evaluates only families that already carry recorded RED evidence, so an assertion invented later has no evidence to evaluate and blocks the readiness verdict rather than riding through it. |
| R5 | ACTIVATE exceeds two hours and is split across commits, or is narrowed mid-flight | Neither is permitted. `169.015-T` halts and the unit returns to **Stage** for explicit scope redesign, per the 2-hour check above. The commit never splits, and no assertion is authored or re-derived inside ACTIVATE; any reduced contract has its assertions retired or re-observed red in the RED phase, and `169.017-T` re-run for a fresh readiness verdict, before activation resumes. |
| R6 | The unit is serialized behind a foundation it does not need | `depends_on_shipments` is empty and `177-S` carries no shipment-level edge in either direction. The root claim is checkable against the executable records, not only against this plan. |
| R7 | The gate token the plan declares is not the token the emitting task produces | *Gates and verdicts* names both vocabularies, each gate's emission conditions state when each token fires, and each gate has exactly one emitter — `169.017-T` for readiness, `169.016-T` for the status contract — whose record reproduces its own vocabulary verbatim. A task record emitting any other token is a defect, not a variant. |
| R8 | A green aggregate suite exit is read as the contract holding | `STATUS_CONTRACT_NOT_OBSERVED` is evaluated first and absorbs every unrun, unimportable and unrecorded case, including a green exit with no per-assertion record. An absent verdict line is also `STATUS_CONTRACT_NOT_OBSERVED`, and *Confirmation artifact and line format* names the one path a reader checks and the closed list of read outcomes that count as absent, so absence is decidable rather than ambiguous. No path reaches `STATUS_CONTRACT_HELD` without a per-assertion passing record for all five families. The same fail-closed construction is applied independently to `PREACTIVATION_NOT_OBSERVED`. |
| R9 | The unit's only gate is emitted after the irreversible activation commit, so activation is authorized by nothing | `169.017-T` emits a **pre-activation** readiness verdict from the complete inert evidence set, and is the sole immediate predecessor of `169.015-T`. `169.015-T`'s first action is a fail-closed read of that verdict, and on any token other than `PREACTIVATION_READY` it touches no declared surface. The post-activation confirmation is retained but no longer carries the authorizing role, which is what `D2` requires. |
| R10 | The two verdicts are conflated, and a post-activation confirmation is read as pre-activation authorization | The two use **disjoint vocabularies** (`PREACTIVATION_*` versus `STATUS_CONTRACT_*`), **distinct paths**, and distinct line prefixes (`PREACTIVATION_STATE: ` versus `COMPOSED_STATE: `), and neither emitter writes the other's file. A `STATUS_CONTRACT_HELD` token can never satisfy `169.015-T`'s predicate, because that predicate matches only the literal `PREACTIVATION_READY`. |
| R11 | Post-activation confirmation fails and the workspace is left mid-migration with no defined path | *Failure path — rollback and halt* states the path in advance: non-zero exit, halt, DOCS does not proceed, `git revert` of the single activation commit as a unit, return to Stage. Reverting is well-defined precisely because activation is one commit. |
| R12 | A stale readiness verdict authorizes a second activation after a redesign | The readiness artifact is whole-file replaced by its sole writer on every run, and any redesign of scope or assertions requires `169.017-T` to be **re-run** before re-activation. The `checked=` field makes the verdict's vintage visible on the single line a consumer reads. |

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
being wrong on its face, because the plan and its only verdict-emitting task
were able to declare different gate vocabularies for the same gate, and because
the unit's only gate emitter was previously scheduled **after** the single
irreversible activation commit — so the plan's own rollout contradicted the
portfolio's binding rollout invariant while every individual task read as
correct.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Why is this unit not gated behind the substrate foundations? | Because it needs none of them. It changes declarations and asserts their agreement. Serializing it behind `182-S` → `184-S` → `185-S` would be a false dependency, which the architecture decision forbids, and `177-S` carries no such edge. |
| H2 | Is a passing conformance test evidence the contract holds? | Only if it was first observed failing, and failing for the right reason. The attempt-08 defect was GREEN-only assertions; the discriminating RED rule closes the weaker version of the same gap, where an assertion fails merely because nothing exists yet. |
| H3 | Is an aggregate non-zero suite exit sufficient RED evidence? | No. It does not prove that *this* assertion failed. Each assertion's failing observation is recorded individually, with its own declared marker in its own failure text. |
| H4 | What if a surface is added after the contract lands? | The surface list is derived by rule and the count is asserted at 4, so a new surface fails the conformance test rather than diverging silently. |
| H5 | Is the `abandoned`-transition observation in scope? | No. It is a backlog-tool transition-table observation recorded so it is not lost, explicitly outside this unit's contract, which concerns what member status *is* after a claim. |
| H6 | Why one commit across all surfaces? | A commit boundary mid-migration is a reachable state in which a mirror states a vocabulary its template does not — the divergence the unit exists to remove. A dependency edge between two activation tasks does not close that window; it opens it, because an edge permits a commit between its endpoints. Adding a pre-activation gate does not weaken this: `169.017-T` is a predecessor of the single activation task, not a second activation task. |
| H7 | Does every assertion in this unit have a RED task that records it failing? | Yes, and it is checkable rather than asserted: the Assertion-to-task map lists every family with its owning RED task and its discriminating fixture, and the Tasks table lists every task with its phase. A family in neither table has no assertion. This question exists because the previous hardening pass answered H6 correctly in principle without ever checking whether the manifest did it. |
| H8 | Does the plan's task table match the shipment manifest? | It must, and the correspondence is the check: **ten** tasks, in the phases and sizes stated, are the `177-S` manifest members alongside `169-F`, and the manifest is ordered in the same phase sequence. A plan that cannot be checked against the work it governs is the precondition for exactly the contradiction attempt 01 found. |
| H9 | Is the ACTIVATE task within the 2-hour rule? | Yes on both axes, for the reason recorded under the 2-hour check, and the added gate read is a single token comparison that does not move it. If it ever is not, the unit **halts and returns to Stage** for explicit scope redesign. It never splits the commit, and it never narrows or re-derives an assertion inside ACTIVATE — a reduced contract has its affected families retired or re-observed red in the RED phase first, and `169.017-T` re-run. |
| H10 | Does the token this plan declares match the token the emitting task produces? | Yes for both gates, and the correspondence is the check. Each gate has exactly one emitter: `169.017-T` for `PREACTIVATION_READY` / `PREACTIVATION_BLOCKED` / `PREACTIVATION_NOT_OBSERVED`, and `169.016-T` for `STATUS_CONTRACT_HELD` / `STATUS_CONTRACT_DIVERGENT` / `STATUS_CONTRACT_NOT_OBSERVED`. *Gates and verdicts* declares both vocabularies, each gate's emission conditions state objectively when each token fires, and each emitter's record reproduces its own. This question exists because an earlier revision declared a three-token vocabulary in the plan while the only record that produced a verdict emitted an unrelated two-token pair — deleting the not-observed state that decision D6 requires. |
| H11 | Can an unrun or unimportable suite be scored as the contract holding? | No, and the ordering is what prevents it. `STATUS_CONTRACT_NOT_OBSERVED` is evaluated **before** the other two states and absorbs import failure, `loader.errors`, `_FailedTest` placeholders, zero executed assertions, a family with no per-assertion record, and an absent verdict line. `STATUS_CONTRACT_HELD` requires an affirmative per-assertion passing record for all five families; a green aggregate exit cannot produce it. This is the unit's most specific safety property, and it is the one the RED phase's binding import-safety rule exists to detect — so it has a token of its own. |
| H15 | Where does each verdict line go, and can a reader tell absence from presence-elsewhere? | Each goes to exactly one declared path — `.autoharness/gates/p002-7-preactivation-readiness.txt` and `.autoharness/gates/p002-7-status-contract-verdict.txt` — in one of three literal line forms, written atomically by a single declared writer with whole-file replacement. *Readiness artifact and line format* and *Confirmation artifact and line format* each state the destination, the three forms, the single-writer and atomicity rule, and the closed list of read outcomes that resolve to the not-observed token — missing, unreadable, empty, no prefixed line, more than one, or an unrecognised token. This question exists because an earlier revision declared that an *absent* verdict line is itself not-observed while naming no destination, which made absence and presence-elsewhere indistinguishable and the gate unevaluable as written. |
| H16 | Does this unit need a CI change to be evaluable? | No, and it does not make one. Each gate's own emitting task is its authoritative evaluator: it runs or evaluates, writes its verdict artifact, and exits zero **only** on its pass token. `.github/workflows/ci.yml` is a **producer** of the observations — its `test` job runs the stdlib unittest suite and consumes an exit code — not a consumer of either verdict line; an earlier revision had that direction inverted. No task in `177-S` modifies `ci.yml`, no workflow is added, and both gates are self-contained. `.autoharness/gates/` is gitignored, so neither verdict is committed and neither leaves the tree dirty. |
| H17 | Does this unit's rollout conform to `D2`'s `PREPARE → VERIFY → ACTIVATE` invariant? | Yes, and the mapping is recorded in *Rollout* rather than left to inference. PREPARE and RED are both `D2` PREPARE, because `D2`'s PREPARE is explicit that tests go red then green *entirely within the inert surface*. `169.017-T` is `D2` VERIFY: it produces the complete evidence verdict with every declared surface still unmutated. `169.015-T` is `D2` ACTIVATE. CONFIRM and DOCS are post-activation steps `D2` neither names nor forbids. `D2`'s third evidence limb — compatibility against `D3`'s pinned corpus — is recorded **inapplicable** (no normalizer, no historical corpus) rather than silently dropped, because a deviation that is not recorded is indistinguishable from one that was not noticed. |
| H18 | What actually authorizes activation — the dependency edge, or the verdict? | The **verdict**. The edge `169.015-T ← 169.017-T` supplies ordering only; a completed predecessor task proves the task ran, not that it concluded favourably. `169.015-T`'s first action is to read the readiness artifact and compare the token against the literal `PREACTIVATION_READY`, halting before any write on `PREACTIVATION_BLOCKED`, `PREACTIVATION_NOT_OBSERVED`, or any absent-or-malformed read. This distinction is the portfolio's own precedent, recorded against `177-F`'s gate in attempt 03. |
| H19 | Can the post-activation confirmation be mistaken for the authorizing gate? | No, and the separation is structural rather than editorial. Two artifacts at two paths, two disjoint token vocabularies, two distinct line prefixes, two sole writers neither of which writes the other's file, and an authorization predicate that matches one literal token only. A `STATUS_CONTRACT_HELD` line cannot satisfy `169.015-T`'s predicate under any reading, and `169.016-T`'s exit code gates **documentation and rollback**, not activation. The readiness line carries `resolved_surface_count=0` and the confirmation line carries `resolved_surface_count=4`; that difference is a phase property of the two gates, not a discrepancy between them. |
| H20 | If confirmation fails after activation, what happens? | *Failure path — rollback and halt*: `169.016-T` exits non-zero, the unit halts, `169.007-T` DOCS does not proceed, and the single `169.015-T` commit is reverted as a unit so all four surfaces return to their pre-activation state simultaneously. The unit returns to Stage; the divergence goes back to a RED task for re-observation, and `169.017-T` is re-run for a fresh readiness verdict before any re-activation. `169.016-T` never repairs a surface in place and never weakens an assertion to reach its pass token. |

### Blast radius

Four declaration surfaces — two authoritative templates and their two installed
mirrors — plus one conformance test module and one documentation page. No
executable boundary, no command execution, no migration of existing mutable
records, and no change to any backlog record's schema. The surface count is
fixed and enumerated, which is what makes the blast radius statable rather than
estimated.

Two generated verdict artifacts sit **outside** that radius by construction:
`.autoharness/gates/p002-7-preactivation-readiness.txt` and
`.autoharness/gates/p002-7-status-contract-verdict.txt`. `.autoharness/gates/`
is gitignored, so neither is a declared surface, neither is committed, neither
appears in a diff, and neither can leave the working tree dirty. They are
observations *about* the radius, not part of it.

### Rollback

PREPARE, RED and VERIFY are inert: they add test code and test data and write
verdict artifacts to an ignored path, and change no declared surface. Anything
abandoned before activation rolls back by discarding untracked test material;
no declared surface has moved.

The single ACTIVATE commit reverts as a unit, returning all four surfaces to
their current divergent state simultaneously. That guarantee holds because
activation is one commit; it would not hold across two commits joined by a
dependency edge, where reverting the second leaves the first in place and
returns the workspace to the split state rather than the original one.

A **post-activation confirmation failure uses exactly that revert**, and it is
the reason the one-commit rule is load-bearing rather than stylistic: on
`STATUS_CONTRACT_DIVERGENT` or `STATUS_CONTRACT_NOT_OBSERVED`, `169.016-T`
exits non-zero, DOCS does not proceed, the activation commit is reverted as a
unit, and the unit returns to Stage. Re-activation requires a fresh
`PREACTIVATION_READY` verdict from a re-run `169.017-T`; the pre-failure
verdict is stale and never carries over.

### Verification floor

Every assertion recorded failing before it is recorded passing, individually,
and failing against a near-miss fixture as well as against absence. No
assertion enters after the production text exists.

**The complete evidence set is adjudicated before activation, not after.**
`169.017-T` reads the recorded absence RED, discriminating RED and inert GREEN
observations for all five families, confirms the inert precondition still holds
(`resolved_surface_count = 0`), and emits `PREACTIVATION_READY` only if every
family is affirmatively covered. Anything unestablished is
`PREACTIVATION_NOT_OBSERVED`, not a pass. `169.015-T` may not proceed without
that token, so the floor is enforced by a read at the activation boundary
rather than by a report written after it.
