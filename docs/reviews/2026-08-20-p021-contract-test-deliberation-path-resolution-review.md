# Plan Review — P-021 contract-test deliberation-path resolution (multi-persona adversarial)

Date: 2026-08-20
Agent: Stage (plan-review gate)
Plan: `docs/plans/2026-08-20-p021-contract-test-deliberation-path-resolution-plan.md`
Deliberation: `021-DL` (archived 2026-08-20 to `.backlogit/archive/021-DL.md`)
Hardening: none — plan declares `requires_plan_hardening: no`; P-006 triggers evaluated and not met
Stash: `7852CE0D`
Review rounds: 1 (six personas)

## Summary

A three-file test-harness repair: two P-021 contract modules hard-load a
deliberation artifact at a `queue/` path that no longer exists, collapsing both
modules' `setUpClass` and reddening the baseline before shipment 144-S starts.
The plan replaces both loads with a shared resolver hosted in the module both
siblings already import from, and adds a behavioural plus a structural
regression guard.

**Verdict: PASS — 0 unresolved P0, 0 unresolved P1.**
Six findings raised (2×P1, 3×P2, 1×P3). Both P1s resolved in plan amendments
A1 and A2 before this verdict. Of the P2s, one resolved (A3), two accepted with
explicit verification obligations on Ship. P3 accepted as-is.

---

## Persona 1 — Gate-correctness adversary

*"Show me where this still leaves the suite red."*

The two `setUpClass` reads are demonstrably a cause of red: both target a path
absent from `origin/main` and from the worktree, both sit in `setUpClass`, and
`setUpClass` failure collapses an entire class rather than one test. Repointing
them at a path verified present, with content verified to retain the swept
`C4 AMENDMENT` and `C5 AMENDMENT` markers, removes that cause.

But the plan's acceptance criterion said "the full configured pytest suite is
green," and Stage ran no tests — a role-boundary constraint, correctly observed.
Stage therefore cannot prove these two loads are the ONLY cause. The operator's
own report says "broad setup failures," which is consistent with two collapsed
classes but does not exclude a third, unrelated failure.

Shipping a task whose gate is "whole suite green" when the agent cannot bound
what else is red is a genuine hazard: Ship would either widen scope to chase
unrelated failures (a P-021 C1 violation) or stall.

**Finding 1 (P1): unbounded green criterion.** **RESOLVED** by amendment A1.
The criterion is now scoped to this task's own change, with an explicit
instruction that further pre-existing failures are captured as deferred entries
under C1 and escalated as a shipment-level blocker — never absorbed.

## Persona 2 — Determinism adversary

*"Make this fail on a machine that is not yours."*

The plan delegates root resolution to
`autoharness.backlog_root.resolve_backlog_root`. Reading that function: it
consults `BACKLOGIT_WORKSPACE_DIR` FIRST, and if the override names a directory
that does not exist it raises `BacklogUnavailableError` rather than falling back.

So any developer or CI runner with `BACKLOGIT_WORKSPACE_DIR` set — plausible in
a repo that ships a backlog tool and whose own tests set that variable — makes
these contract tests fail for a reason with no relationship to the code under
test. That is the same nondeterministic-red class this task exists to remove,
reintroduced through the fix.

**Finding 2 (P1): ambient environment leaks into contract-test resolution.**
**RESOLVED** by amendment A2: the helper must pass `env={}` explicitly, matching
the isolation pattern `tests/test_backlog_root.py` already uses. Resolution
becomes a pure function of the committed repository state.

## Persona 3 — Guard-integrity adversary

*"Your regression guard is the deliverable. Show me it guards."*

Two objections.

First, the structural guard scans for lifecycle-volatile `queue/`-anchored path
construction — and the resolver itself necessarily contains exactly that. An
unexamined guard would either fail immediately on its own resolver or be quietly
written with a broad exclusion that also swallows real future violations.

**Finding 3 (P2): guard must exempt its own resolver, narrowly and visibly.**
**RESOLVED** by amendment A3: the exemption must name the resolver definition
explicitly so it cannot silently widen.

Second, is the behavioural assertion actually load-bearing, or does it merely
restate what `setUpClass` already does? It is load-bearing on two counts
`setUpClass` does not cover: the uniqueness check catches a half-completed
archival where the artifact exists in BOTH locations (which `setUpClass` would
happily resolve past), and the marker check proves content equivalence, so a
future artifact that is present but gutted fails loudly instead of passing every
sweep vacuously. Both are real, distinct failure modes. Accepted.

## Persona 4 — Scope adversary

*"You are touching a third file and six comments to fix two lines."*

The third file (`test_scope_containment_policy_contract.py`) is not scope creep;
it is the only correct host. Both siblings already import from it, so the
resolver rides the existing one-way allocation edge (011 → 013 → 012). Placing
it in either sibling would create a new import edge and risk the cycle those
modules were deliberately arranged to avoid. The module's `OWNED_BEHAVIOURS` set
is untouched, so the three-way allocation guards (RANGE-COMPLETENESS,
pairwise-disjointness, expected-allocation) are unaffected.

The six prose corrections are defensible but are the weakest element: they cite a
path that no longer exists, so leaving them would preserve the exact misdirection
that authored the bug. They are also the only part of this task that increases
textual overlap with `137.003-T`.

**Finding 4 (P3): prose corrections are optional to the green gate.** Accepted
as-is. They are cheap, they remove active misdirection, and the plan already
pins their line numbers so the overlap is auditable. If a rebase conflict does
materialise, they are the safe part to drop.

## Persona 5 — Sequencing adversary

*"Prove the ordering is enforced, not merely intended."*

The direction is stated unambiguously in both deliberation and plan:
`dep add <item-id> <depends-on>` means item-id depends on depends-on, so the
required new edge is `144-S depends on PREREQ`. Combined with the pre-existing
`145-S depends on 144-S`, the graph is a three-node chain — acyclic by
inspection, with the new node a source having no outbound dependency.

The residual risk is mechanical, not logical: the edge is added to a shipment
that already exists and is already queued, and Stage cannot execute Ship's
gate-DAG readiness check to confirm the added edge is honoured at claim time.

**Finding 5 (P2): ordering must be verified after wiring, not assumed.**
ACCEPTED with obligation — Stage must re-read `backlogit dep list` for all three
shipments after wiring and report the observed edges verbatim. Ship must treat a
missing edge as a blocker rather than proceeding on the narrative order.

## Persona 6 — Rebase-collision adversary

*"Two shipments edit one file. Which one loses?"*

`137.003-T` in 145-S also edits `tests/test_scope_containment_boundary_contract.py`,
correcting false `stash remove` / `archive` CLI-alias comments. This shipment
merges first, so `137.003-T` rebases onto the repaired file.

The line ranges are disjoint — this task touches the `setUpClass` load, the
resolver import, and the six 019-DL path citations; `137.003-T` touches
CLI-alias comments elsewhere in the file. No semantic conflict exists in either
direction, and neither change alters an assertion the other depends on.

**Finding 6 (P2): 145-S carries a stale premise risk.** ACCEPTED with obligation
— the coordination note is recorded in the stash entry, the deliberation, the
plan risk table, and the handoff memory, so Ship encounters it before claiming
145-S. No re-plan of 145-S is warranted; a textual rebase is not a scope change.

---

## Findings ledger

| # | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| 1 | P1 | Acceptance criterion assumed whole-suite green without bounding other causes of red | RESOLVED — plan amendment A1 |
| 2 | P1 | `BACKLOGIT_WORKSPACE_DIR` could make contract tests fail nondeterministically | RESOLVED — plan amendment A2 |
| 3 | P2 | Structural guard would trip on its own resolver | RESOLVED — plan amendment A3 |
| 4 | P3 | Six prose corrections are optional to the green gate | ACCEPTED as-is |
| 5 | P2 | Shipment ordering must be verified after wiring | ACCEPTED with verification obligation on Stage and Ship |
| 6 | P2 | File-level overlap with `137.003-T` | ACCEPTED with coordination obligation, recorded in four artifacts |

## Sizing re-check

Size `S`, complexity `low` — reaffirmed after the amendments. A1 adds no work
(it narrows a criterion), A2 adds one keyword argument, A3 adds one narrow
exemption. Neither the effort axis (well under the 2-hour rule) nor the
complexity axis (no elevated uncertainty) forces a split, and the atomicity
argument stands: any split leaves an intermediate state where one module is
repaired and its sibling still collapses in `setUpClass`, failing Ship's
per-task green gate.

## Hardening re-check (P-006)

Confirmed **not required**. Blast radius after amendments is unchanged: three
test modules, no schema change, no CLI distribution change, no template family,
no multi-family fan-out, no public interface change. The single new coupling is
an import of an already-shipped helper that carries its own contract tests.

## Verdict

**PASS.** Proceed to harvest. Zero unresolved P0 or P1 findings. Three accepted
findings carry explicit obligations recorded in the plan, the shipment wiring
step, and the handoff memory.
---

## Addendum - scope-expansion re-gate (round 2, 2026-08-20)

**Trigger.** Stage found a **circular mandatory-gate dependency** between
`146-S` and `144-S` after this review's round-1 PASS. Task 1 of the reviewed
plan was expanded to absorb the malformed-frontmatter repair formerly held by
`136.001-T`. A gate re-run on the delta follows. See plan Amendment A4.

**Verdict: PASS (unchanged) - 0 unresolved P0, 0 unresolved P1.**

### What changed

| Aspect | Round 1 | Round 2 |
| --- | --- | --- |
| Task 1 scope | three `tests/` modules | three `tests/` modules **+ one line** of `docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md` |
| Acceptance criterion 7 | "no file outside `tests/`" | superseded by an enumerated **four-file budget** |
| Acceptance criterion 1 | suite-scoped (per A1) | **all** mandatory gates green (Gate 1-4 + pytest), A1 escape hatch retained |
| Size / complexity | `S` / `low` | `S` / `low` (unchanged) |
| Hardening | `no` | `no` (unchanged) |

### Re-gate findings

**F1 (P1) - does the expansion actually dissolve the cycle? RESOLVED.**
It does, and it is the *only* structure that does. Before: `146-S` repaired the
pytest blocker but left Gate 1 red, so its own first task could not complete;
`144-S` held the Gate 1 repair but was blocked by `146-S`. Neither shipment
could produce a gate-green first task. After: `138.001-T` clears both blockers
in one commit, so it is a genuine first task that can leave every mandatory
gate green - and every downstream task inherits a green baseline. Verified by
inspection of the gate list in `.github/agents/_ship.agent.md` (Gate 1 = YAML
frontmatter validity) and of line 12 of the 2026-08-02 plan, which is still
unquoted at the time of this re-gate.

**F2 (P1) - is any previously authorized scope silently dropped? RESOLVED.**
No. Both authorized scopes survive intact:
* the known scalar fix is reproduced **verbatim** as Scope A of `138.001-T`,
  including its "exactly ONE changed line" constraint and its
  `backlogit docs lint --path` criterion;
* the test-path fix is Scope B, unchanged from round 1 including amendments
  A1/A2/A3.
`136.001-T` is stamped, archived rather than deleted, and carries an explicit
superseded-by pointer, so the original wording remains auditable. `136-F`
retains the sweep and the regression guard.

**F3 (P2) - width isolation. ACCEPTED with a recorded exception.**
The task now crosses two families (tests + docs). Normally a P-003 concern.
Accepted because gate-atomicity *requires* it: splitting the two repairs is what
created the deadlock. The exception is bounded by an explicitly enumerated
four-file budget, the docs side is a single quoting change with a byte-identical
value, and the repo-wide `docs/` sweep is explicitly excluded and left in
`136.002-T`. Recorded at staging time rather than discovered at execution time.

**F4 (P2) - does the 2-hour rule still hold? ACCEPTED.**
Scope A was independently sized `XS` / `trivial`. `XS` + `S` on the effort axis
stays well inside 2 hours, and a mechanical quoting edit adds no uncertainty on
the complexity axis. Neither axis forces a split. `S` / `low` retained.

**F5 (P2) - orphan and dangling-reference risk from the restructure.
RESOLVED.** The two inbound edges to `136.001-T` were removed before archival,
`136.001-T` was removed from the `144-S` manifest, and **no** cross-shipment
task edge was introduced - ordering rides the pre-existing shipment edge
`144-S depends on 146-S (blocks)`. So no edge can dangle when `146-S`'s items
are archived. `136.002-T` is dependency-free (first task of `144-S`);
`136.003-T` depends on `136.002-T` alone.

**F6 (P3) - is the docline regression guard still falsifiable? ACCEPTED.**
Yes. `136.003-T`'s negative test now reverts the `138.001-T` Scope A quoting -
same file, same line, same observable failure. Cross-shipment, but the guard
lands after the fix, so the revert-and-observe procedure is unaffected.

### Hardening re-check (P-006)

`requires_plan_hardening: no` **stands**. The delta is one quoted line in one
Markdown documentation file. No schema change, no CLI distribution change, no
template family touched, no multi-family fan-out, no public interface change.
None of the elevated-blast-radius triggers is met.

### Deliberation-lifecycle note

`021-DL` was archived by Stage on 2026-08-20 (to `.backlogit/archive/021-DL.md`)
because the installed dogfood `.github/agents/_ship.agent.md` lacks the
`source_deliberation_id` cleanup step that exists in
`templates/agents/_ship.agent.md.tmpl`, and `146-S` executes before the `145-S`
migration that would add it. Provenance is preserved unmodified;
`138-F.custom_fields.source_deliberation_id` is retained and the Ship cleanup
step is a documented **no-op** under the established idempotent convention.
This is a backlog-lifecycle action, not a change to the reviewed plan's
execution scope, and does not alter the verdict.
